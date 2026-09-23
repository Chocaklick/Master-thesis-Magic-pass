"""Build stability-checked structural segments and descriptive Path C analogues.

No output from this module is a causal effect or predicted uplift.  Similarity
uses only the three structural variables declared in config/path_c_analysis.json.
Snow vulnerability is kept as a separate strategic-need axis, and tourism
dependence/accessibility remain explicitly unavailable.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def transformed_features(frame: pd.DataFrame) -> np.ndarray:
    altitude = pd.to_numeric(frame["altitude_top_m_median"], errors="raise").to_numpy(float)
    ski_area = pd.to_numeric(frame["ski_area_km_median"], errors="raise").to_numpy(float)
    lifts = pd.to_numeric(frame["number_lifts_median"], errors="raise").to_numpy(float)
    if np.any(ski_area < 0) or np.any(lifts < 0):
        raise ValueError("Structural size features must be non-negative")
    return np.column_stack([altitude, np.log1p(ski_area), np.log1p(lifts)])


def fit_kmeans(
    matrix: np.ndarray,
    k: int,
    seed: int,
    n_init: int,
    max_iter: int,
) -> tuple[float, np.ndarray, np.ndarray]:
    best: tuple[float, np.ndarray, np.ndarray] | None = None
    for initialisation in range(n_init):
        rng = np.random.default_rng(seed + initialisation * 1009)
        centres = np.empty((k, matrix.shape[1]), dtype=float)
        centres[0] = matrix[rng.integers(len(matrix))]
        for centre_index in range(1, k):
            squared = ((matrix[:, None, :] - centres[None, :centre_index, :]) ** 2).sum(axis=2)
            nearest = squared.min(axis=1)
            if nearest.sum() == 0:
                centres[centre_index] = matrix[rng.integers(len(matrix))]
            else:
                centres[centre_index] = matrix[rng.choice(len(matrix), p=nearest / nearest.sum())]
        labels = np.full(len(matrix), -1, dtype=int)
        for _ in range(max_iter):
            squared = ((matrix[:, None, :] - centres[None, :, :]) ** 2).sum(axis=2)
            updated_labels = squared.argmin(axis=1)
            updated_centres = np.array(
                [
                    matrix[updated_labels == cluster].mean(axis=0)
                    if np.any(updated_labels == cluster)
                    else matrix[rng.integers(len(matrix))]
                    for cluster in range(k)
                ]
            )
            if np.array_equal(updated_labels, labels) and np.allclose(updated_centres, centres):
                break
            labels, centres = updated_labels, updated_centres
        inertia = float(((matrix - centres[labels]) ** 2).sum())
        if best is None or inertia < best[0]:
            best = (inertia, labels.copy(), centres.copy())
    if best is None:
        raise RuntimeError("K-means did not produce a solution")
    return best


def pairwise_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return np.sqrt(((left[:, None, :] - right[None, :, :]) ** 2).sum(axis=2))


def silhouette_score(matrix: np.ndarray, labels: np.ndarray) -> float:
    distances = pairwise_distances(matrix, matrix)
    values: list[float] = []
    for index in range(len(matrix)):
        same = labels == labels[index]
        if same.sum() <= 1:
            values.append(0.0)
            continue
        within = float(distances[index, same].sum() / (same.sum() - 1))
        nearest_other = min(
            float(distances[index, labels == other].mean())
            for other in np.unique(labels)
            if other != labels[index]
        )
        denominator = max(within, nearest_other)
        values.append((nearest_other - within) / denominator if denominator else 0.0)
    return float(np.mean(values))


def adjusted_rand_index(first: np.ndarray, second: np.ndarray) -> float:
    _, first_codes = np.unique(first, return_inverse=True)
    _, second_codes = np.unique(second, return_inverse=True)
    table = np.zeros((first_codes.max() + 1, second_codes.max() + 1), dtype=int)
    np.add.at(table, (first_codes, second_codes), 1)

    def combinations_of_two(values: np.ndarray) -> float:
        return float((values * (values - 1) // 2).sum())

    joint = combinations_of_two(table)
    first_total = combinations_of_two(table.sum(axis=1))
    second_total = combinations_of_two(table.sum(axis=0))
    n = len(first)
    possible = n * (n - 1) / 2
    expected = first_total * second_total / possible if possible else 0.0
    maximum = (first_total + second_total) / 2
    return (joint - expected) / (maximum - expected) if maximum != expected else 1.0


def support_reference(reference: np.ndarray) -> tuple[np.ndarray, float, float]:
    distances = pairwise_distances(reference, reference)
    np.fill_diagonal(distances, np.inf)
    nearest = distances.min(axis=1)
    return nearest, float(np.quantile(nearest, 0.75)), float(np.quantile(nearest, 0.95))


def support_flag(distance: float, threshold_75: float, threshold_95: float) -> str:
    if distance <= threshold_75:
        return "good_support"
    if distance <= threshold_95:
        return "moderate_extrapolation"
    return "strong_extrapolation"


def empirical_support_score(distance: float, reference_nearest: np.ndarray) -> float:
    return round(100 * float(np.mean(reference_nearest >= distance)), 1)


def haversine_km(lon_a: float, lat_a: float, lon_b: np.ndarray, lat_b: np.ndarray) -> np.ndarray:
    lon_a_rad, lat_a_rad = np.radians(lon_a), np.radians(lat_a)
    lon_b_rad, lat_b_rad = np.radians(lon_b), np.radians(lat_b)
    dlon, dlat = lon_b_rad - lon_a_rad, lat_b_rad - lat_a_rad
    value = np.sin(dlat / 2) ** 2 + np.cos(lat_a_rad) * np.cos(lat_b_rad) * np.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(value))


def markdown_table(frame: pd.DataFrame) -> str:
    columns = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join(["---"] * len(columns)) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = []
        for value in row:
            if pd.isna(value):
                values.append("")
            elif isinstance(value, float):
                values.append(f"{value:.3f}")
            else:
                values.append(str(value).replace("|", "/"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def upsert_experiment_log(rows: list[dict[str, str]]) -> None:
    path = ROOT / "reports/model_experiment_log.csv"
    existing = pd.read_csv(path, dtype="string")
    names = {row["model_or_analysis"] for row in rows}
    existing = existing[~existing["model_or_analysis"].isin(names)]
    output = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    output.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def main() -> None:
    config = json.loads((ROOT / "config/path_c_analysis.json").read_text(encoding="utf-8"))
    parameters = config["segmentation"]
    features = pd.read_csv(ROOT / "data_processed/path_c_resort_cluster_features.csv")
    eligible_mask = as_bool(features["structural_feature_complete"])
    eligible = features.loc[eligible_mask].copy().reset_index(drop=True)
    transformed = transformed_features(eligible)
    means = transformed.mean(axis=0)
    standard_deviations = transformed.std(axis=0, ddof=0)
    if np.any(standard_deviations == 0):
        raise ValueError("A Path C structural feature has zero variance")
    matrix = (transformed - means) / standard_deviations

    solutions: dict[int, tuple[float, np.ndarray, np.ndarray]] = {}
    diagnostic_rows: list[dict[str, object]] = []
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
            rng = np.random.default_rng(parameters["random_seed"] + k * 1000 + repetition)
            sample = np.sort(rng.choice(len(matrix), size=sample_size, replace=False))
            _, _, subsample_centres = fit_kmeans(
                matrix[sample],
                k,
                parameters["random_seed"] + 100000 + k * 1000 + repetition,
                parameters["bootstrap_n_init"],
                parameters["max_iter"],
            )
            predicted = pairwise_distances(matrix, subsample_centres).argmin(axis=1)
            stability.append(adjusted_rand_index(labels, predicted))
        sizes = np.bincount(labels, minlength=k)
        diagnostic_rows.append(
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
    diagnostics = pd.DataFrame(diagnostic_rows)
    admissible = diagnostics[
        diagnostics["bootstrap_ari_median"].ge(parameters["minimum_median_bootstrap_ari"])
        & diagnostics["minimum_cluster_size"].ge(parameters["minimum_cluster_size"])
    ]
    if admissible.empty:
        raise ValueError("No segmentation solution passed the predeclared stability and size gates")
    selected_k = int(admissible.sort_values(["silhouette", "k"], ascending=[False, True]).iloc[0]["k"])
    diagnostics["selected"] = diagnostics["k"].eq(selected_k)
    diagnostics.to_csv(ROOT / "reports/path_c_segmentation_diagnostics.csv", index=False)

    _, labels, centres = solutions[selected_k]
    ordering = sorted(range(selected_k), key=lambda cluster: (float(centres[cluster].sum()), cluster))
    remap = {old: new + 1 for new, old in enumerate(ordering)}
    segment_ids = np.array([f"SEGMENT_{remap[label]:02d}" for label in labels])
    eligible["segment_id"] = segment_ids
    eligible["altitude_top_z"] = matrix[:, 0]
    eligible["log1p_ski_area_z"] = matrix[:, 1]
    eligible["log1p_number_lifts_z"] = matrix[:, 2]
    eligible["distance_to_segment_centroid"] = [
        float(np.linalg.norm(matrix[index] - centres[labels[index]]))
        for index in range(len(matrix))
    ]
    eligible["selected_k"] = selected_k

    segment_profiles = (
        eligible.groupby("segment_id", observed=True)
        .agg(
            entities=("cluster_id", "size"),
            altitude_top_m_median=("altitude_top_m_median", "median"),
            ski_area_km_median=("ski_area_km_median", "median"),
            number_lifts_median=("number_lifts_median", "median"),
            resolved_current_magic_clusters=("resolved_current_magic_member", "sum"),
            apparent_candidate_clusters=("candidate_for_path_c", "sum"),
        )
        .reset_index()
    )
    overall_medians = eligible[
        ["altitude_top_m_median", "ski_area_km_median", "number_lifts_median"]
    ].median()

    def profile_label(row: pd.Series) -> str:
        parts = []
        for column, label in [
            ("altitude_top_m_median", "altitude"),
            ("ski_area_km_median", "ski area"),
            ("number_lifts_median", "lift count"),
        ]:
            parts.append(("higher" if row[column] >= overall_medians[column] else "lower") + " " + label)
        return ", ".join(parts)

    segment_profiles["descriptive_profile"] = segment_profiles.apply(profile_label, axis=1)
    eligible = eligible.merge(
        segment_profiles[["segment_id", "descriptive_profile"]],
        on="segment_id",
        how="left",
        validate="many_to_one",
    )
    segments = features.merge(
        eligible[
            [
                "cluster_id",
                "segment_id",
                "descriptive_profile",
                "altitude_top_z",
                "log1p_ski_area_z",
                "log1p_number_lifts_z",
                "distance_to_segment_centroid",
                "selected_k",
            ]
        ],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    segments["segmentation_eligible"] = segments["segment_id"].notna()
    segments["segmentation_interpretation"] = np.where(
        segments["segmentation_eligible"],
        "current_structural_segment_not_treatment_effect_group",
        "not_segmented_missing_structural_feature",
    )
    segments.to_csv(ROOT / "data_processed/path_c_cluster_segments.csv", index=False)

    eligible_by_id = eligible.set_index("cluster_id", drop=False)
    member_reference = eligible[as_bool(eligible["resolved_current_magic_member"])].copy()
    member_matrix = matrix[as_bool(eligible["resolved_current_magic_member"]).to_numpy()]
    if len(member_reference) < 4:
        raise ValueError("Too few resolved current Magic clusters for analogue support")
    member_nearest, member_q75, member_q95 = support_reference(member_matrix)

    resorts = pd.read_csv(ROOT / "data_processed/resort_master.csv")
    units = pd.read_csv(ROOT / "data_processed/treatment_destination_units.csv", dtype="string")
    diagnostics_24 = pd.read_csv(ROOT / "reports/hotel_capacity_treatment_diagnostics.csv")
    diagnostics_24 = diagnostics_24[
        as_bool(diagnostics_24["complete_24_pre_and_24_post_capacity_window"])
    ].copy()
    unit_lookup = units.set_index("destination_unit_id")
    treated_rows: list[dict[str, object]] = []
    for diagnostic in diagnostics_24.itertuples(index=False):
        unit = unit_lookup.loc[diagnostic.destination_unit_id]
        component_ids = str(unit["component_resort_ids"]).split("|")
        component = resorts[resorts["resort_id"].isin(component_ids)].copy()
        if len(component) != len(component_ids):
            raise ValueError(f"Missing component features for {diagnostic.destination_unit_id}")
        treated_rows.append(
            {
                "destination_unit_id": diagnostic.destination_unit_id,
                "destination_name": diagnostic.destination_name,
                "component_resort_ids": "|".join(component_ids),
                "altitude_top_m_median": pd.to_numeric(component["altitude_top_m"]).median(),
                "ski_area_km_median": pd.to_numeric(component["ski_area_km"]).median(),
                "number_lifts_median": pd.to_numeric(component["number_lifts"]).median(),
                "hotel_overnights_change_pct": diagnostic.hotel_overnights_change_pct,
                "available_beds_change_pct": diagnostic.available_beds_change_pct,
                "overnights_per_bed_change_pct": diagnostic.overnights_per_bed_change_pct,
                "causal_interpretation_approved": False,
                "reference_interpretation": "unadjusted_adjacent_24_month_diagnostic_not_treatment_effect",
            }
        )
    treated_reference = pd.DataFrame(treated_rows)
    treated_transformed = transformed_features(treated_reference)
    treated_matrix = (treated_transformed - means) / standard_deviations
    treated_nearest, treated_q75, treated_q95 = support_reference(treated_matrix)
    treated_reference.to_csv(ROOT / "data_processed/path_c_reviewed_treated_reference.csv", index=False)

    candidate = eligible[as_bool(eligible["candidate_for_path_c"])].copy()
    candidate_indices = candidate.index.to_numpy()
    candidate_matrix = matrix[candidate_indices]
    analogue_rows: list[dict[str, object]] = []
    for candidate_position, (_, candidate_row) in enumerate(candidate.iterrows()):
        candidate_vector = candidate_matrix[candidate_position]
        member_distances = np.sqrt(((member_matrix - candidate_vector) ** 2).sum(axis=1))
        member_order = np.argsort(member_distances)[: config["analogues"]["nearest_magic_members"]]
        treated_distances = np.sqrt(((treated_matrix - candidate_vector) ** 2).sum(axis=1))
        treated_order = np.argsort(treated_distances)[: config["analogues"]["nearest_reviewed_treated_destinations"]]
        nearest_member_distance = float(member_distances[member_order[0]])
        nearest_treated_distance = float(treated_distances[treated_order[0]])
        treated_subset = treated_reference.iloc[treated_order]
        changes = pd.to_numeric(treated_subset["hotel_overnights_change_pct"], errors="raise")
        geographic = haversine_km(
            float(candidate_row["longitude_median"]),
            float(candidate_row["latitude_median"]),
            member_reference["longitude_median"].to_numpy(float),
            member_reference["latitude_median"].to_numpy(float),
        )
        result: dict[str, object] = {
            "cluster_id": candidate_row["cluster_id"],
            "cluster_display_name": candidate_row["cluster_display_name"],
            "segment_id": candidate_row["segment_id"],
            "magic_member_nearest_distance": nearest_member_distance,
            "magic_member_comparability_score": empirical_support_score(nearest_member_distance, member_nearest),
            "magic_member_ood_flag": support_flag(nearest_member_distance, member_q75, member_q95),
            "reviewed_treated_nearest_distance": nearest_treated_distance,
            "reviewed_treated_comparability_score": empirical_support_score(nearest_treated_distance, treated_nearest),
            "reviewed_treated_ood_flag": support_flag(nearest_treated_distance, treated_q75, treated_q95),
            "analogue_descriptive_change_signal_pct": float(changes.median()),
            "analogue_descriptive_change_range_low_pct": float(changes.min()),
            "analogue_descriptive_change_range_high_pct": float(changes.max()),
            "opportunity_signal_interpretation": config["analogues"]["opportunity_signal_interpretation"],
            "nearest_current_magic_cluster_geographic_km": float(geographic.min()),
            "resolved_current_magic_clusters_within_30km": int((geographic <= 30).sum()),
            "resolved_current_magic_clusters_within_50km": int((geographic <= 50).sum()),
            "network_fit_interpretation": "geographic_context_only_not_accessibility_or_membership_fit",
            "snow_vulnerability_proxy": candidate_row["snow_vulnerability_proxy_median"],
            "strategic_need_status": "incomplete_no_approved_tourism_catchment_or_validated_destination_accessibility",
            "predicted_uplift_pct": np.nan,
            "uplift_lower_pct": np.nan,
            "uplift_upper_pct": np.nan,
            "causal_interpretation_approved": False,
        }
        for rank, position in enumerate(member_order, start=1):
            member = member_reference.iloc[position]
            result[f"closest_magic_analogue_{rank}_cluster_id"] = member["cluster_id"]
            result[f"closest_magic_analogue_{rank}_name"] = member["cluster_display_name"]
            result[f"closest_magic_analogue_{rank}_distance"] = float(member_distances[position])
            result[f"closest_magic_analogue_{rank}_same_segment"] = bool(
                member["segment_id"] == candidate_row["segment_id"]
            )
        for rank, position in enumerate(treated_order, start=1):
            treated = treated_reference.iloc[position]
            result[f"closest_reviewed_treated_analogue_{rank}_id"] = treated["destination_unit_id"]
            result[f"closest_reviewed_treated_analogue_{rank}_name"] = treated["destination_name"]
            result[f"closest_reviewed_treated_analogue_{rank}_distance"] = float(treated_distances[position])
            result[f"closest_reviewed_treated_analogue_{rank}_hotel_change_pct"] = float(
                treated["hotel_overnights_change_pct"]
            )
        analogue_rows.append(result)
    analogues = pd.DataFrame(analogue_rows).sort_values("cluster_id").reset_index(drop=True)
    analogues["opportunity_signal_percentile"] = (
        analogues["analogue_descriptive_change_signal_pct"].rank(method="average", pct=True) * 100
    ).round(1)
    analogues["snow_vulnerability_percentile"] = (
        analogues["snow_vulnerability_proxy"].rank(method="average", pct=True, na_option="keep") * 100
    ).round(1)
    analogues["two_dimension_coordinates_available"] = (
        analogues["opportunity_signal_percentile"].notna()
        & analogues["snow_vulnerability_percentile"].notna()
    )
    analogues["composite_opportunity_need_score"] = np.nan
    analogues["composite_score_status"] = "not_produced_dimensions_kept_separate"
    analogues.to_csv(ROOT / "data_processed/path_c_candidate_analogues.csv", index=False)

    decision = segments.merge(analogues, on=["cluster_id", "cluster_display_name", "segment_id"], how="left", validate="one_to_one")
    decision["analysis_version"] = config["analysis_version"]
    decision["current_magic_pass_status"] = decision["magic_status"]
    decision["tourism_dependence"] = np.nan
    decision["accessibility_score"] = np.nan
    decision["hotel_capacity"] = np.nan
    decision["model_used"] = "structural_kmeans_and_nearest_treated_analogue_descriptive"
    decision["confidence"] = np.where(
        decision["candidate_for_path_c"].fillna(False)
        & decision["reviewed_treated_ood_flag"].isin(["good_support", "moderate_extrapolation"]),
        "exploratory_moderate_comparability_only",
        "exploratory_low_or_not_scored",
    )
    decision["interpretation"] = np.where(
        decision["candidate_for_path_c"].fillna(False),
        "Structural analogue output; descriptive post-entry patterns are not predicted uplift or causal effects.",
        "Not in the initial apparent-nonmember candidate pool.",
    )
    decision.to_csv(ROOT / "data_processed/magic_pass_decision_support.csv", index=False)

    selected_diagnostic = diagnostics.loc[diagnostics["selected"]].iloc[0]
    summary = {
        "analysis_version": config["analysis_version"],
        "linked_lift_clusters": int(len(features)),
        "segmentation_eligible_clusters": int(len(eligible)),
        "clusters_with_multi_listing_feature_disagreement": int(
            as_bool(features["multi_listing_feature_disagreement"]).sum()
        ),
        "selected_k": selected_k,
        "selected_silhouette": float(selected_diagnostic["silhouette"]),
        "selected_bootstrap_ari_median": float(selected_diagnostic["bootstrap_ari_median"]),
        "selected_bootstrap_ari_p10": float(selected_diagnostic["bootstrap_ari_p10"]),
        "resolved_current_magic_reference_clusters": int(len(member_reference)),
        "reviewed_treated_reference_units": int(len(treated_reference)),
        "apparent_nonmember_candidates_scored": int(len(analogues)),
        "candidate_good_treated_support": int(analogues["reviewed_treated_ood_flag"].eq("good_support").sum()),
        "candidate_moderate_treated_extrapolation": int(analogues["reviewed_treated_ood_flag"].eq("moderate_extrapolation").sum()),
        "candidate_strong_treated_extrapolation": int(analogues["reviewed_treated_ood_flag"].eq("strong_extrapolation").sum()),
        "candidate_two_dimension_coordinates_available": int(analogues["two_dimension_coordinates_available"].sum()),
        "predicted_uplift_values": int(analogues["predicted_uplift_pct"].notna().sum()),
        "composite_scores": int(analogues["composite_opportunity_need_score"].notna().sum()),
        "causal_interpretation_approved": False,
    }
    (ROOT / "reports/path_c_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    checkpoint_report = f"""# Checkpoints 4–5 and Path C decision

## Decision

Checkpoint 4 fails under the present design: there are **0 approved causal treatment units** and **0 approved controls**. The 35-pair donor shortlist is exhausted after 28 proximity deprioritisations and seven official-source shock exclusions. No DiD, event-study, matching or synthetic-control estimate is authorised.

Checkpoint 5 also fails for heterogeneous-effect ML: the project has 14 reviewed destination units, 11 in the outcome panel, seven with 24 observed pre and active-post months, and still zero causally approved units. Monthly repetition does not increase the number of independent treated destinations. Causal forest, X-Learner, DR-Learner and a neural network remain rejected; supervised gradient boosting/random forest have no defensible cluster-level target.

The selected architecture is therefore **Path C: exploratory structural segmentation and descriptive analogue decision support**. This is a positive architecture choice, not a causal fallback disguised as prediction.

## Leakage and unit controls

- Analysis entity: the **{summary['linked_lift_clusters']} existing lift clusters linked to at least one supplied listing**, rather than 271 repeated directory rows. A cluster is still not a certified independent destination.
- The Bergfex infrastructure snapshot is undated, so it is labelled current/undated and **not pre-treatment**.
- Similarity uses only top altitude, log ski-area kilometres and log lift count.
- Membership, hotel outcomes, post-entry changes and snow vulnerability do not enter the structural clustering.
- Hotel outcomes/capacity are excluded because a resort point's municipality is not an approved tourism catchment.
- Snow vulnerability is retained on a separate strategic-need axis. Qualified point-container tourism, Swiss municipality-point and Eurostat cross-border grid population, NPVM zonal travel-time and official stop-proximity context are appended downstream. A separate winter-2026 GTFS module measures scheduled municipality-to-destination journeys, and all 15 current component arrival nodes pass a versioned name/mode/municipality/distance review for descriptive routing. A same-pair diagnostic confirms that geographic distance is informative but not interchangeable with scheduled transit time. Six arrivals remain explicit village/local-centre proxies; door-to-lift walking and historical continuity are unverified. None is an approved catchment or causal destination-accessibility feature.

## Prohibited interpretations

The analogue signal is not predicted uplift, a counterfactual, a confidence interval or evidence that a resort should join Magic Pass. No composite opportunity/need score is produced. A later causal redesign would require new donor and exposure evidence rather than a more complex algorithm.
"""
    (ROOT / "reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md").write_text(checkpoint_report, encoding="utf-8")

    profile_for_report = segment_profiles[
        [
            "segment_id",
            "entities",
            "altitude_top_m_median",
            "ski_area_km_median",
            "number_lifts_median",
            "resolved_current_magic_clusters",
            "apparent_candidate_clusters",
            "descriptive_profile",
        ]
    ]
    analogue_report = f"""# Path C segmentation and analogue review

## Segmentation result

Of {summary['linked_lift_clusters']} linked lift clusters, **{summary['segmentation_eligible_clusters']}** have all three structural features. The predeclared rule selects **k = {selected_k}**: silhouette **{summary['selected_silhouette']:.3f}**, median 80% subsample ARI **{summary['selected_bootstrap_ari_median']:.3f}**, and 10th-percentile ARI **{summary['selected_bootstrap_ari_p10']:.3f}**. The full k=2–8 comparison is in `reports/path_c_segmentation_diagnostics.csv`.

{markdown_table(profile_for_report)}

These are broad current structural segments, not treatment-effect groups. **{summary['clusters_with_multi_listing_feature_disagreement']}** lift clusters contain supplied listings that disagree on at least one structural feature; the cluster table retains every min/median/max range rather than hiding that ambiguity.

## Analogue system

- **{summary['resolved_current_magic_reference_clusters']}** structurally complete clusters have a resolved link to the current official Magic Pass map and form the current-member reference pool.
- **{summary['reviewed_treated_reference_units']}** reviewed destinations have complete unadjusted 24-month pre/post capacity diagnostics and form the historical-pattern reference pool.
- **{summary['apparent_nonmember_candidates_scored']}** structurally complete clusters with no resolved current, historical or precautionary Magic relation are scored as *apparent* non-member candidates. This is not verified non-membership.
- Against the eight reviewed treated references, {summary['candidate_good_treated_support']} candidates have good support, {summary['candidate_moderate_treated_extrapolation']} moderate extrapolation and {summary['candidate_strong_treated_extrapolation']} strong extrapolation under empirical leave-one-out distance thresholds.

For each candidate, `data_processed/path_c_candidate_analogues.csv` retains three closest current Magic clusters, three closest reviewed treated destinations, their standardised distances, the three unadjusted hotel-change diagnostics, an empirical support flag, network-distance context and snow vulnerability. The analogue signal is the median of those three changes; its low/high fields are an observed range, **not a confidence interval**.

## Two dimensions kept separate

The decision-support export contains an analogue-opportunity percentile and a snow-vulnerability percentile for **{summary['candidate_two_dimension_coordinates_available']}** candidates. The downstream pipeline appends qualified point-container tourism context, Swiss municipality-point population, harmonised Eurostat 2021 cross-border grid population, official NPVM 2025 zonal road/public-transport context and official OFT/BAV straight-line proximity to passenger stops and train stations. The cross-border grid closes the known geographic truncation of the Swiss-only radii but remains residential straight-line context, not a visitor catchment. The NPVM layer covers every candidate but uses a transparent nearest-zone-within-current-municipality proxy for high-alpine listing points outside the zone polygons. Stop proximity also has usable cluster context for every candidate, while the mixed Swiss/French Portes du Soleil cluster is explicitly partial. Neither tourism dependence nor destination-level accessibility is approved. Strategic need is therefore incomplete. Predicted-uplift fields are blank ({summary['predicted_uplift_values']} populated), and no composite score is produced ({summary['composite_scores']} populated).

## Outputs and next evidence needs

- `data_processed/path_c_resort_cluster_features.csv`
- `data_processed/path_c_cluster_segments.csv`
- `data_processed/path_c_reviewed_treated_reference.csv`
- `data_processed/path_c_candidate_analogues.csv`
- `data_processed/path_c_cluster_tourism_context.csv`
- `data_processed/path_c_cluster_accessibility_context.csv`
- `data_processed/path_c_cluster_cross_border_population_context.csv`
- `data_processed/path_c_cluster_transport_accessibility_context.csv`
- `data_processed/path_c_cluster_public_transport_stop_context.csv`
- `data_processed/magic_pass_decision_support.csv`

The min/median/max audit and the qualified contexts are documented in reports 19–29. The cross-border population context is complete. Next, obtain the historical GTFS anchors through a manual or authorised channel, add motorway proximity, define defensible destination catchments, and audit competing-pass status for apparent candidates. The NPVM proxy geometry and same-pair distance/transit audits are complete, but 50 proxy-only clusters still lack an internal exact-zone sensitivity reference. If door-to-lift precision is needed, add explicit walking/access evidence for the six village/local-centre proxies. Until then the export is an exploratory dashboard-ready prototype, not a recommendation ranking.
"""
    (ROOT / "reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md").write_text(analogue_report, encoding="utf-8")

    experiment_rows = [
        {
            "timestamp": "2026-09-22T00:30:00+02:00",
            "model_or_analysis": "checkpoint_4_causal_feasibility",
            "status": "failed_gate",
            "sample_definition": "14 reviewed units; 11 panel units; 35 shortlisted donor pairs",
            "result_or_decision": "0 causal treatments and 0 controls approved; donor shortlist exhausted",
            "reason": "Treatment intensity, confounding, spillovers and a valid donor pool are not jointly resolved",
            "next_condition": "Redesign and broaden donors plus strengthen exposure and time-varying confounder evidence",
        },
        {
            "timestamp": "2026-09-22T00:30:00+02:00",
            "model_or_analysis": "checkpoint_5_heterogeneous_effect_ml",
            "status": "failed_gate",
            "sample_definition": "At most 14 reviewed treatments; 7 with 24/24 coverage; 0 causally approved",
            "result_or_decision": "Causal forest, X-Learner, DR-Learner and neural network remain rejected",
            "reason": "Independent treated sample is too small and no causal outcome target is approved",
            "next_condition": "Substantially larger validated treated sample with overlap and stable nuisance models",
        },
        {
            "timestamp": "2026-09-22T00:30:00+02:00",
            "model_or_analysis": "path_c_structural_kmeans",
            "status": "completed_descriptive",
            "sample_definition": f"{len(eligible)} lift clusters with complete undated structural features",
            "result_or_decision": f"Selected k={selected_k}; silhouette={summary['selected_silhouette']:.3f}; median bootstrap ARI={summary['selected_bootstrap_ari_median']:.3f}",
            "reason": "Stable, interpretable cross-sectional segmentation without using membership or outcomes",
            "next_condition": "Test aggregation sensitivity and add dated authoritative infrastructure features",
        },
        {
            "timestamp": "2026-09-22T00:30:00+02:00",
            "model_or_analysis": "path_c_nearest_treated_analogues",
            "status": "completed_descriptive",
            "sample_definition": f"{len(analogues)} apparent candidates; {len(treated_reference)} reviewed treated references",
            "result_or_decision": "Three nearest analogues and OOD flags produced; predicted uplift left missing",
            "reason": "Unadjusted analogue patterns support exploration but not counterfactual prediction",
            "next_condition": "Add tourism dependence, accessibility, competition and stronger historical feature timing",
        },
    ]
    upsert_experiment_log(experiment_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
