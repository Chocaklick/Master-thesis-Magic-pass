"""Select deterministic Path C examples that illustrate uncertainty, never merit."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_VERSION = "path_c_v0_31"
INPUT_PATH = ROOT / "data_processed" / "magic_pass_decision_support.csv"


def first_unused(
    candidates: pd.DataFrame,
    mask: pd.Series,
    used_ids: set[str],
) -> pd.Series:
    eligible = candidates[mask & ~candidates["cluster_id"].isin(used_ids)].sort_values(
        "cluster_id"
    )
    if eligible.empty:
        raise ValueError("An uncertainty-example selection rule has no eligible candidate")
    return eligible.iloc[0]


def display(value: object, digits: int = 2) -> str:
    if pd.isna(value) or value == "":
        return "not available"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def main() -> None:
    dashboard = pd.read_csv(INPUT_PATH)
    candidates = dashboard[dashboard["candidate_for_path_c"].eq(True)].copy()
    if len(candidates) != 104 or not candidates["cluster_id"].is_unique:
        raise ValueError("Expected 104 unique Path C candidate clusters")
    if set(candidates["analysis_version"].dropna()) != {ANALYSIS_VERSION}:
        raise ValueError("Candidate dashboard does not use Path C v0.31")
    protected_numeric = [
        "predicted_uplift_pct",
        "uplift_lower_pct",
        "uplift_upper_pct",
        "composite_opportunity_need_score",
    ]
    if candidates[protected_numeric].notna().any().any():
        raise ValueError("Protected uplift or composite fields must remain blank")
    if candidates["causal_interpretation_approved"].eq(True).any():
        raise ValueError("No candidate may have causal interpretation approval")

    rules = [
        {
            "case_id": "stable_complete_context",
            "case_label": "Stable structural comparison with point-container context",
            "selection_rule": (
                "First cluster_id with stable min/median/max segment, analogue and support "
                "criteria; good treated-reference support; and complete point-container "
                "population/hotel context."
            ),
            "mask": (
                candidates["aggregation_sensitivity_status"].eq(
                    "stable_across_min_median_max"
                )
                & candidates["reviewed_treated_ood_flag"].eq("good_support")
                & candidates["tourism_context_status"].eq(
                    "complete_point_container_population_and_hotel_context"
                )
            ),
        },
        {
            "case_id": "segment_assignment_sensitive",
            "case_label": "Segment assignment changes under aggregation",
            "selection_rule": (
                "First cluster_id with good treated-reference support whose recorded "
                "min/median/max solutions span more than one segment."
            ),
            "mask": (
                candidates["reviewed_treated_ood_flag"].eq("good_support")
                & candidates["aggregation_segment_ids"]
                .fillna("")
                .str.contains("|", regex=False)
            ),
        },
        {
            "case_id": "support_category_sensitive",
            "case_label": "Treated-reference support changes under aggregation",
            "selection_rule": (
                "First cluster_id with good median-rule support, stable segment assignment "
                "and a non-stable treated-reference support category across aggregation rules."
            ),
            "mask": (
                candidates["reviewed_treated_ood_flag"].eq("good_support")
                & candidates["aggregation_segment_stable"].eq(True)
                & candidates["aggregation_reviewed_treated_ood_stable"].eq(False)
            ),
        },
        {
            "case_id": "strong_treated_reference_extrapolation",
            "case_label": "Strong treated-reference extrapolation",
            "selection_rule": (
                "First cluster_id classified as a strong extrapolation from the eight "
                "reviewed treated reference units under the median rule."
            ),
            "mask": candidates["reviewed_treated_ood_flag"].eq(
                "strong_extrapolation"
            ),
        },
    ]

    used_ids: set[str] = set()
    selected_records = []
    selected_fields = [
        "cluster_id",
        "cluster_display_name",
        "member_resort_ids",
        "listing_count",
        "altitude_top_m_median",
        "ski_area_km_median",
        "number_lifts_median",
        "segment_id",
        "reviewed_treated_ood_flag",
        "reviewed_treated_nearest_distance",
        "aggregation_segment_ids",
        "aggregation_segment_stable",
        "aggregation_current_magic_top1_stable",
        "aggregation_reviewed_treated_top1_stable",
        "aggregation_reviewed_treated_ood_stable",
        "aggregation_signal_range_pct_points",
        "aggregation_sensitivity_status",
        "closest_magic_analogue_1_cluster_id",
        "closest_magic_analogue_1_name",
        "closest_reviewed_treated_analogue_1_id",
        "closest_reviewed_treated_analogue_1_name",
        "tourism_context_status",
        "candidate_scope_radius_sensitivity_status",
        "tourism_catchment_validated",
        "cluster_transport_context_status",
        "cluster_listing_exact_transport_assignment_share",
        "cluster_public_transport_stop_context_status",
        "cluster_national_road_proximity_context_status",
        "snow_proxy_quality_worst",
        "cluster_competing_pass_scope_status",
        "historical_competing_pass_scope_status",
        "historical_competing_pass_market_absence_verified",
        "pre_treatment_feature_approved",
        "causal_covariate_approved",
        "causal_interpretation_approved",
    ]
    for order, rule in enumerate(rules, start=1):
        row = first_unused(candidates, rule["mask"], used_ids)
        used_ids.add(str(row["cluster_id"]))
        record = {
            "selection_order": order,
            "case_id": rule["case_id"],
            "case_label": rule["case_label"],
            "selection_rule": rule["selection_rule"],
        }
        record.update({field: row[field] for field in selected_fields})
        selected_records.append(record)

    examples = pd.DataFrame(selected_records)
    if len(examples) != 4 or not examples["cluster_id"].is_unique:
        raise ValueError("Expected four unique uncertainty examples")
    examples.to_csv(
        ROOT / "reports" / "thesis_candidate_uncertainty_examples.csv", index=False
    )

    table_rows = "\n".join(
        "| {order} | `{case}` | `{cluster}` | {name} | {support} | {sensitivity} |".format(
            order=row.selection_order,
            case=row.case_id,
            cluster=row.cluster_id,
            name=row.cluster_display_name,
            support=row.reviewed_treated_ood_flag,
            sensitivity=row.aggregation_sensitivity_status,
        )
        for row in examples.itertuples()
    )
    sections = []
    for row in examples.itertuples():
        sections.extend(
            [
                f"## {row.selection_order}. {row.case_label}: `{row.cluster_id}`",
                "",
                f"**Directory label:** {row.cluster_display_name}",
                "",
                f"**Selection rule:** {row.selection_rule}",
                "",
                "**Structural reading.** "
                f"The median directory profile is {display(row.altitude_top_m_median, 0)} m "
                f"top altitude, {display(row.ski_area_km_median, 1)} km of published ski area "
                f"and {display(row.number_lifts_median, 1)} lifts. The median-rule segment is "
                f"`{row.segment_id}` and the treated-reference support flag is "
                f"`{row.reviewed_treated_ood_flag}`. The aggregation rules record segment set "
                f"`{row.aggregation_segment_ids}` and an analogue-signal range of "
                f"{display(row.aggregation_signal_range_pct_points, 1)} percentage points.",
                "",
                "**Analogue reading.** "
                f"The closest current Magic cluster is `{display(row.closest_magic_analogue_1_cluster_id)}` "
                f"({display(row.closest_magic_analogue_1_name)}), while the closest reviewed treated "
                f"reference is `{display(row.closest_reviewed_treated_analogue_1_id)}` "
                f"({display(row.closest_reviewed_treated_analogue_1_name)}). These are geometric "
                "neighbours in the three-field structural feature space, not counterfactual controls.",
                "",
                "**Evidence limits.** "
                f"Tourism context is `{row.tourism_context_status}` and no tourism catchment is "
                f"validated. NPVM assignment is `{row.cluster_transport_context_status}`; current "
                f"stop context is `{row.cluster_public_transport_stop_context_status}` and road-axis "
                f"context is `{row.cluster_national_road_proximity_context_status}`. Current pass "
                f"scope is `{row.cluster_competing_pass_scope_status}` and historical positive-presence "
                f"scope is `{row.historical_competing_pass_scope_status}`; historical market absence "
                "is not verified.",
                "",
                "**Permitted conclusion.** This row illustrates how evidence strength and uncertainty "
                "can be narrated for one stable identifier. It is not an admission recommendation, "
                "a causal estimate, an expected-uplift value or a statement of relative merit.",
                "",
            ]
        )

    report = f"""# Illustrative Path C candidate uncertainty cases

These four rows are selected by predeclared, deterministic uncertainty rules and then by ascending stable `cluster_id`. They are **not** the best, worst or most representative candidates. The ordering below is the rule order, not a ranking. No candidate is assigned an expected treatment effect, recommendation, confidence interval or composite score.

## Selection overview

| Rule order | Case | Stable cluster ID | Directory label | Median-rule treated support | Aggregation status |
|---:|---|---|---|---|---|
{table_rows}

The first rule illustrates stability with available point-container context. The next two isolate distinct aggregation problems: segment movement and support-category movement. The final rule illustrates extrapolation beyond the empirical treated-reference support. The exact selection fields are preserved in `reports/thesis_candidate_uncertainty_examples.csv`.

{'\n'.join(sections)}
## Use in the thesis

Use at most these examples as a short boxed illustration or appendix. Keep the stable IDs, selection rules and limitation paragraphs together. Do not reorder them by an opportunity signal, add a recommendation label, or interpret the closest analogue as a causal control. Any managerial assessment would still require validated destination scope, stakeholder-defined decision weights and decision-specific evidence that the present project does not contain.
"""
    (ROOT / "reports" / "48_CANDIDATE_UNCERTAINTY_EXAMPLES.md").write_text(
        report.rstrip() + "\n", encoding="utf-8"
    )

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "candidate_universe": len(candidates),
        "selected_examples": len(examples),
        "selection_method": "predeclared_uncertainty_categories_then_ascending_stable_cluster_id",
        "selected_cluster_ids": examples["cluster_id"].tolist(),
        "selected_case_ids": examples["case_id"].tolist(),
        "predicted_uplift_values": 0,
        "recommendations_issued": 0,
        "composite_scores": 0,
        "causal_interpretation_approvals": 0,
        "interpretation": "illustrative_uncertainty_cases_not_ranking_recommendation_or_treatment_effect",
    }
    (ROOT / "reports" / "thesis_candidate_uncertainty_examples_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
