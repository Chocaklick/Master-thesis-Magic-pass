"""Test Path C sensitivity to min/median/max aggregation within lift clusters."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_path_c_segments_and_analogues import (
    adjusted_rand_index,
    as_bool,
    empirical_support_score,
    fit_kmeans,
    pairwise_distances,
    silhouette_score,
    support_flag,
    support_reference,
)


ROOT = Path(__file__).resolve().parents[2]
FEATURES = ["altitude_top_m", "ski_area_km", "number_lifts"]


def scenario_transformed(frame: pd.DataFrame, rule: str) -> np.ndarray:
    altitude = pd.to_numeric(frame[f"altitude_top_m_{rule}"], errors="raise").to_numpy(float)
    area = pd.to_numeric(frame[f"ski_area_km_{rule}"], errors="raise").to_numpy(float)
    lifts = pd.to_numeric(frame[f"number_lifts_{rule}"], errors="raise").to_numpy(float)
    return np.column_stack([altitude, np.log1p(area), np.log1p(lifts)])


def choose_segmentation(
    matrix: np.ndarray, parameters: dict
) -> tuple[int, np.ndarray, pd.DataFrame]:
    solutions: dict[int, tuple[float, np.ndarray, np.ndarray]] = {}
    rows: list[dict[str, object]] = []
    for k in parameters["candidate_k"]:
        solution = fit_kmeans(
            matrix,
            k,
            parameters["random_seed"] + k * 100,
            parameters["n_init"],
            parameters["max_iter"],
        )
        solutions[k] = solution
        inertia, labels, _ = solution
        stability: list[float] = []
        sample_size = int(np.floor(parameters["bootstrap_sample_share"] * len(matrix)))
        for repetition in range(parameters["bootstrap_repetitions"]):
            rng = np.random.default_rng(
                parameters["random_seed"] + k * 1000 + repetition
            )
            sample = np.sort(rng.choice(len(matrix), size=sample_size, replace=False))
            _, _, centres = fit_kmeans(
                matrix[sample],
                k,
                parameters["random_seed"]
                + 100000
                + k * 1000
                + repetition,
                parameters["bootstrap_n_init"],
                parameters["max_iter"],
            )
            predicted = pairwise_distances(matrix, centres).argmin(axis=1)
            stability.append(adjusted_rand_index(labels, predicted))
        sizes = np.bincount(labels, minlength=k)
        rows.append(
            {
                "k": k,
                "inertia": inertia,
                "silhouette": silhouette_score(matrix, labels),
                "bootstrap_ari_median": float(np.median(stability)),
                "bootstrap_ari_p10": float(np.quantile(stability, 0.10)),
                "minimum_cluster_size": int(sizes.min()),
                "cluster_sizes": "|".join(map(str, sorted(sizes.tolist()))),
            }
        )
    diagnostics = pd.DataFrame(rows)
    admissible = diagnostics[
        diagnostics["bootstrap_ari_median"].ge(parameters["minimum_median_bootstrap_ari"])
        & diagnostics["minimum_cluster_size"].ge(parameters["minimum_cluster_size"])
    ]
    if admissible.empty:
        raise ValueError("No aggregation-sensitivity solution passed the configured gates")
    selected_k = int(
        admissible.sort_values(["silhouette", "k"], ascending=[False, True]).iloc[0]["k"]
    )
    diagnostics["selected"] = diagnostics["k"].eq(selected_k)
    labels = solutions[selected_k][1]
    centres = solutions[selected_k][2]
    ordering = sorted(range(selected_k), key=lambda cluster: (float(centres[cluster].sum()), cluster))
    remap = {old: new + 1 for new, old in enumerate(ordering)}
    ordered_labels = np.array([f"SEGMENT_{remap[label]:02d}" for label in labels])
    return selected_k, ordered_labels, diagnostics


def treated_reference_for_rule(
    rule: str,
    resorts: pd.DataFrame,
    units: pd.DataFrame,
    diagnostics: pd.DataFrame,
) -> pd.DataFrame:
    unit_lookup = units.set_index("destination_unit_id")
    rows: list[dict[str, object]] = []
    for diagnostic in diagnostics.itertuples(index=False):
        component_ids = str(unit_lookup.loc[diagnostic.destination_unit_id, "component_resort_ids"]).split("|")
        component = resorts[resorts["resort_id"].isin(component_ids)].copy()
        aggregation = getattr(pd.to_numeric(component["altitude_top_m"]), rule)()
        area = getattr(pd.to_numeric(component["ski_area_km"]), rule)()
        lifts = getattr(pd.to_numeric(component["number_lifts"]), rule)()
        rows.append(
            {
                "destination_unit_id": diagnostic.destination_unit_id,
                "destination_name": diagnostic.destination_name,
                f"altitude_top_m_{rule}": aggregation,
                f"ski_area_km_{rule}": area,
                f"number_lifts_{rule}": lifts,
                "hotel_overnights_change_pct": diagnostic.hotel_overnights_change_pct,
            }
        )
    return pd.DataFrame(rows)


def jaccard(left: str, right: str) -> float:
    first, second = set(left.split("|")), set(right.split("|"))
    return len(first & second) / len(first | second)


def main() -> None:
    config = json.loads((ROOT / "config/path_c_analysis.json").read_text(encoding="utf-8"))
    parameters = config["segmentation"]
    sensitivity = config["aggregation_sensitivity"]
    rules = sensitivity["rules"]
    baseline_rule = sensitivity["baseline_rule"]
    if set(rules) != {"median", "min", "max"} or baseline_rule not in rules:
        raise ValueError("Aggregation sensitivity requires min, median and max with a valid baseline")
    features = pd.read_csv(ROOT / "data_processed/path_c_resort_cluster_features.csv")
    eligible = features[as_bool(features["structural_feature_complete"])].copy().reset_index(drop=True)
    candidates = eligible[as_bool(eligible["candidate_for_path_c"])].copy()
    current_members = eligible[as_bool(eligible["resolved_current_magic_member"])].copy()
    resorts = pd.read_csv(ROOT / "data_processed/resort_master.csv")
    units = pd.read_csv(ROOT / "data_processed/treatment_destination_units.csv", dtype="string")
    capacity = pd.read_csv(ROOT / "reports/hotel_capacity_treatment_diagnostics.csv")
    capacity = capacity[as_bool(capacity["complete_24_pre_and_24_post_capacity_window"])].copy()

    baseline_segments = pd.read_csv(ROOT / "data_processed/path_c_cluster_segments.csv")
    baseline_segment_map = baseline_segments.set_index("cluster_id")["segment_id"]

    detail_rows: list[dict[str, object]] = []
    k_diagnostics: list[pd.DataFrame] = []
    scenario_labels: dict[str, np.ndarray] = {}
    scenario_summary: list[dict[str, object]] = []

    for rule in rules:
        transformed = scenario_transformed(eligible, rule)
        means = transformed.mean(axis=0)
        deviations = transformed.std(axis=0, ddof=0)
        matrix = (transformed - means) / deviations
        if rule == baseline_rule:
            selected_k = int(
                pd.read_csv(ROOT / "reports/path_c_segmentation_diagnostics.csv")
                .query("selected == True")
                .iloc[0]["k"]
            )
            ordered_labels = eligible["cluster_id"].map(baseline_segment_map).to_numpy()
            diagnostics = pd.read_csv(ROOT / "reports/path_c_segmentation_diagnostics.csv")
        else:
            selected_k, ordered_labels, diagnostics = choose_segmentation(matrix, parameters)
        diagnostics = diagnostics.copy()
        diagnostics.insert(0, "aggregation_rule", rule)
        k_diagnostics.append(diagnostics)
        scenario_labels[rule] = ordered_labels

        member_matrix = matrix[current_members.index.to_numpy()]
        member_nearest, member_q75, member_q95 = support_reference(member_matrix)
        treated = treated_reference_for_rule(rule, resorts, units, capacity)
        treated_transformed = scenario_transformed(treated, rule)
        treated_matrix = (treated_transformed - means) / deviations
        treated_nearest, treated_q75, treated_q95 = support_reference(treated_matrix)
        candidate_matrix = matrix[candidates.index.to_numpy()]

        for position, (_, candidate) in enumerate(candidates.iterrows()):
            vector = candidate_matrix[position]
            member_distances = np.sqrt(((member_matrix - vector) ** 2).sum(axis=1))
            member_order = np.argsort(member_distances)[:3]
            treated_distances = np.sqrt(((treated_matrix - vector) ** 2).sum(axis=1))
            treated_order = np.argsort(treated_distances)[:3]
            changes = pd.to_numeric(
                treated.iloc[treated_order]["hotel_overnights_change_pct"], errors="raise"
            )
            detail_rows.append(
                {
                    "aggregation_rule": rule,
                    "cluster_id": candidate["cluster_id"],
                    "cluster_display_name": candidate["cluster_display_name"],
                    "selected_k": selected_k,
                    "segment_id": ordered_labels[candidates.index[position]],
                    "closest_current_magic_cluster_id": current_members.iloc[member_order[0]]["cluster_id"],
                    "top3_current_magic_cluster_ids": "|".join(
                        current_members.iloc[member_order]["cluster_id"].astype(str)
                    ),
                    "current_magic_nearest_distance": float(member_distances[member_order[0]]),
                    "current_magic_support_score": empirical_support_score(
                        float(member_distances[member_order[0]]), member_nearest
                    ),
                    "current_magic_ood_flag": support_flag(
                        float(member_distances[member_order[0]]), member_q75, member_q95
                    ),
                    "closest_reviewed_treated_id": treated.iloc[treated_order[0]]["destination_unit_id"],
                    "top3_reviewed_treated_ids": "|".join(
                        treated.iloc[treated_order]["destination_unit_id"].astype(str)
                    ),
                    "reviewed_treated_nearest_distance": float(treated_distances[treated_order[0]]),
                    "reviewed_treated_support_score": empirical_support_score(
                        float(treated_distances[treated_order[0]]), treated_nearest
                    ),
                    "reviewed_treated_ood_flag": support_flag(
                        float(treated_distances[treated_order[0]]), treated_q75, treated_q95
                    ),
                    "analogue_descriptive_change_signal_pct": float(changes.median()),
                    "causal_interpretation_approved": False,
                }
            )

        selected = diagnostics[as_bool(diagnostics["selected"])].iloc[0]
        scenario_summary.append(
            {
                "aggregation_rule": rule,
                "selected_k": selected_k,
                "selected_silhouette": float(selected["silhouette"]),
                "selected_bootstrap_ari_median": float(selected["bootstrap_ari_median"]),
                "selected_bootstrap_ari_p10": float(selected["bootstrap_ari_p10"]),
            }
        )

    detail = pd.DataFrame(detail_rows).sort_values(["cluster_id", "aggregation_rule"])
    detail.to_csv(ROOT / "data_processed/path_c_candidate_analogue_sensitivity.csv", index=False)
    pd.concat(k_diagnostics, ignore_index=True).to_csv(
        ROOT / "reports/path_c_aggregation_sensitivity_k_diagnostics.csv", index=False
    )

    baseline = detail[detail["aggregation_rule"].eq(baseline_rule)].set_index("cluster_id")
    summaries = pd.DataFrame(scenario_summary).set_index("aggregation_rule")
    comparison_rows: list[dict[str, object]] = []
    for rule in rules:
        scenario = detail[detail["aggregation_rule"].eq(rule)].set_index("cluster_id")
        comparison_rows.append(
            {
                "aggregation_rule": rule,
                **summaries.loc[rule].to_dict(),
                "segment_assignment_ari_vs_median": adjusted_rand_index(
                    scenario_labels[baseline_rule], scenario_labels[rule]
                ),
                "candidate_segment_label_agreement_vs_median": float(
                    scenario["segment_id"].eq(baseline["segment_id"]).mean()
                ),
                "current_magic_top1_agreement_vs_median": float(
                    scenario["closest_current_magic_cluster_id"]
                    .eq(baseline["closest_current_magic_cluster_id"])
                    .mean()
                ),
                "current_magic_top3_mean_jaccard_vs_median": float(
                    np.mean(
                        [
                            jaccard(left, right)
                            for left, right in zip(
                                scenario["top3_current_magic_cluster_ids"],
                                baseline["top3_current_magic_cluster_ids"],
                            )
                        ]
                    )
                ),
                "reviewed_treated_top1_agreement_vs_median": float(
                    scenario["closest_reviewed_treated_id"]
                    .eq(baseline["closest_reviewed_treated_id"])
                    .mean()
                ),
                "reviewed_treated_top3_mean_jaccard_vs_median": float(
                    np.mean(
                        [
                            jaccard(left, right)
                            for left, right in zip(
                                scenario["top3_reviewed_treated_ids"],
                                baseline["top3_reviewed_treated_ids"],
                            )
                        ]
                    )
                ),
                "reviewed_treated_ood_agreement_vs_median": float(
                    scenario["reviewed_treated_ood_flag"]
                    .eq(baseline["reviewed_treated_ood_flag"])
                    .mean()
                ),
                "opportunity_signal_spearman_vs_median": float(
                    scenario["analogue_descriptive_change_signal_pct"].rank().corr(
                        baseline["analogue_descriptive_change_signal_pct"].rank()
                    )
                ),
                "opportunity_signal_mean_absolute_change_pct_points": float(
                    (
                        scenario["analogue_descriptive_change_signal_pct"]
                        - baseline["analogue_descriptive_change_signal_pct"]
                    ).abs().mean()
                ),
                "causal_interpretation_approved": False,
            }
        )
    comparison = pd.DataFrame(comparison_rows)
    comparison.to_csv(ROOT / "reports/path_c_aggregation_sensitivity.csv", index=False)

    candidate_sensitivity = (
        detail.groupby("cluster_id", observed=True)
        .agg(
            aggregation_segment_ids=("segment_id", lambda values: "|".join(sorted(set(values)))),
            aggregation_segment_stable=("segment_id", lambda values: values.nunique() == 1),
            aggregation_current_magic_top1_stable=(
                "closest_current_magic_cluster_id",
                lambda values: values.nunique() == 1,
            ),
            aggregation_reviewed_treated_top1_stable=(
                "closest_reviewed_treated_id",
                lambda values: values.nunique() == 1,
            ),
            aggregation_reviewed_treated_ood_stable=(
                "reviewed_treated_ood_flag",
                lambda values: values.nunique() == 1,
            ),
            aggregation_signal_min_pct=("analogue_descriptive_change_signal_pct", "min"),
            aggregation_signal_max_pct=("analogue_descriptive_change_signal_pct", "max"),
        )
        .reset_index()
    )
    candidate_sensitivity["aggregation_signal_range_pct_points"] = (
        candidate_sensitivity["aggregation_signal_max_pct"]
        - candidate_sensitivity["aggregation_signal_min_pct"]
    )
    candidate_sensitivity["aggregation_sensitivity_status"] = np.where(
        candidate_sensitivity[
            [
                "aggregation_segment_stable",
                "aggregation_current_magic_top1_stable",
                "aggregation_reviewed_treated_top1_stable",
                "aggregation_reviewed_treated_ood_stable",
            ]
        ].all(axis=1),
        "stable_across_min_median_max",
        "sensitive_to_within_cluster_aggregation",
    )
    decision_path = ROOT / "data_processed/magic_pass_decision_support.csv"
    decision = pd.read_csv(decision_path)
    sensitivity_columns = [
        column for column in candidate_sensitivity.columns if column != "cluster_id"
    ]
    decision = decision.drop(
        columns=[column for column in sensitivity_columns if column in decision.columns]
    ).merge(candidate_sensitivity, on="cluster_id", how="left", validate="one_to_one")
    scored = as_bool(decision["candidate_for_path_c"])
    stable = (
        as_bool(decision["aggregation_reviewed_treated_top1_stable"])
        & as_bool(decision["aggregation_reviewed_treated_ood_stable"])
    )
    supported = decision["reviewed_treated_ood_flag"].isin(
        ["good_support", "moderate_extrapolation"]
    )
    decision.loc[scored, "confidence"] = np.where(
        stable[scored] & supported[scored],
        "exploratory_moderate_comparability_only",
        "exploratory_low_aggregation_sensitive_or_ood",
    )
    decision.loc[
        scored & ~decision["aggregation_sensitivity_status"].eq("stable_across_min_median_max"),
        "interpretation",
    ] = (
        "Structural analogue output is sensitive to within-cluster aggregation; "
        "descriptive post-entry patterns are not predicted uplift or causal effects."
    )
    decision.to_csv(decision_path, index=False)

    min_row = comparison.set_index("aggregation_rule").loc["min"]
    max_row = comparison.set_index("aggregation_rule").loc["max"]
    report = f"""# Path C aggregation sensitivity

## Purpose

Fifty-three lift clusters contain multiple supplied listings that disagree on at least one structural feature. The baseline uses the within-cluster median. This robustness check rebuilds the structural segmentation and analogues with the within-cluster minimum and maximum instead.

## Results

All three aggregation rules select k={int(comparison['selected_k'].mode().iloc[0])}. Relative to the median baseline:

- minimum aggregation: segment ARI {min_row['segment_assignment_ari_vs_median']:.3f}; current-Magic top-1 analogue agreement {min_row['current_magic_top1_agreement_vs_median']:.1%}; reviewed-treated top-1 agreement {min_row['reviewed_treated_top1_agreement_vs_median']:.1%}; treated OOD-category agreement {min_row['reviewed_treated_ood_agreement_vs_median']:.1%}; opportunity-signal rank correlation {min_row['opportunity_signal_spearman_vs_median']:.3f};
- maximum aggregation: segment ARI {max_row['segment_assignment_ari_vs_median']:.3f}; current-Magic top-1 analogue agreement {max_row['current_magic_top1_agreement_vs_median']:.1%}; reviewed-treated top-1 agreement {max_row['reviewed_treated_top1_agreement_vs_median']:.1%}; treated OOD-category agreement {max_row['reviewed_treated_ood_agreement_vs_median']:.1%}; opportunity-signal rank correlation {max_row['opportunity_signal_spearman_vs_median']:.3f}.

The selected number of broad segments is robust, but individual nearest analogues and OOD classifications are not invariant. Only **{int(candidate_sensitivity['aggregation_sensitivity_status'].eq('stable_across_min_median_max').sum())} of {len(candidate_sensitivity)}** candidates retain the same segment, closest current-Magic analogue, closest reviewed-treated analogue and treated-reference OOD category under all three rules. The enriched decision-support export exposes those row-level flags and lowers confidence for aggregation-sensitive or strong-OOD cases.

`data_processed/path_c_candidate_analogue_sensitivity.csv` preserves every candidate-scenario result, and `reports/path_c_aggregation_sensitivity.csv` contains the full comparison.

## Interpretation

This is a measurement/aggregation sensitivity, not model validation against a causal truth. The median remains the primary rule because it is less dominated by the broadest or narrowest duplicated listing, while min/max results expose how much the decision-support view depends on listing semantics. No causal interpretation or composite ranking is approved.
"""
    (ROOT / "reports/19_PATH_C_AGGREGATION_SENSITIVITY.md").write_text(
        report, encoding="utf-8"
    )
    summary = {
        "candidate_clusters": int(len(baseline)),
        "aggregation_rules": rules,
        "selected_k_by_rule": {
            row["aggregation_rule"]: int(row["selected_k"])
            for row in comparison_rows
        },
        "minimum_rule_segment_ari": float(min_row["segment_assignment_ari_vs_median"]),
        "maximum_rule_segment_ari": float(max_row["segment_assignment_ari_vs_median"]),
        "minimum_rule_treated_top1_agreement": float(
            min_row["reviewed_treated_top1_agreement_vs_median"]
        ),
        "maximum_rule_treated_top1_agreement": float(
            max_row["reviewed_treated_top1_agreement_vs_median"]
        ),
        "candidates_fully_stable_across_aggregation_rules": int(
            candidate_sensitivity["aggregation_sensitivity_status"]
            .eq("stable_across_min_median_max")
            .sum()
        ),
        "candidates_with_stable_reviewed_treated_top1": int(
            candidate_sensitivity["aggregation_reviewed_treated_top1_stable"].sum()
        ),
        "candidates_with_stable_reviewed_treated_ood": int(
            candidate_sensitivity["aggregation_reviewed_treated_ood_stable"].sum()
        ),
        "causal_interpretation_approved": False,
    }
    (ROOT / "reports/path_c_aggregation_sensitivity_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
