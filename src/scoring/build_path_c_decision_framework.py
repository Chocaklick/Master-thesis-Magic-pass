"""Formalise Checkpoint 6 as a guarded, non-recommendation Path C dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "path_c_decision_framework.json"
DECISION = ROOT / "data_processed" / "magic_pass_decision_support.csv"
READINESS = ROOT / "reports" / "path_c_feature_readiness_audit.csv"
DASHBOARD = ROOT / "data_processed" / "path_c_candidate_evidence_dashboard.csv"
DIMENSIONS = ROOT / "reports" / "path_c_decision_framework_dimensions.csv"
SUMMARY = ROOT / "reports" / "path_c_decision_framework_summary.json"
REPORT = ROOT / "reports" / "39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md"


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def build_dimensions(config: dict[str, object], readiness: pd.DataFrame) -> pd.DataFrame:
    declared = [
        feature_group_id
        for dimension in config["dimensions"]
        for feature_group_id in dimension["feature_group_ids"]
    ]
    if len(declared) != len(set(declared)):
        raise ValueError("Decision-framework feature groups must be assigned once")
    if set(declared) != set(readiness["feature_group_id"]):
        missing = sorted(set(readiness["feature_group_id"]) - set(declared))
        extra = sorted(set(declared) - set(readiness["feature_group_id"]))
        raise ValueError(f"Decision-framework feature-group mismatch: {missing=}, {extra=}")

    indexed = readiness.set_index("feature_group_id")
    rows: list[dict[str, object]] = []
    for order, dimension in enumerate(config["dimensions"], start=1):
        groups = indexed.loc[dimension["feature_group_ids"]]
        rows.append(
            {
                "analysis_version": config["analysis_version"],
                "checkpoint": config["checkpoint"],
                "dimension_order": order,
                "dimension_id": dimension["dimension_id"],
                "dimension_name": dimension["dimension_name"],
                "feature_group_ids": "|".join(dimension["feature_group_ids"]),
                "feature_group_count": len(groups),
                "complete_candidate_coverage_groups": int(
                    groups["candidate_coverage_status"]
                    .eq("complete_candidate_coverage")
                    .sum()
                ),
                "partial_candidate_coverage_groups": int(
                    groups["candidate_coverage_status"]
                    .eq("partial_candidate_coverage")
                    .sum()
                ),
                "no_candidate_feature_groups": int(
                    groups["candidate_coverage_status"].eq("no_candidate_feature").sum()
                ),
                "exploratory_similarity_approved_groups": int(
                    as_bool(groups["exploratory_similarity_use_approved"]).sum()
                ),
                "pre_treatment_predictor_approved_groups": int(
                    as_bool(groups["pre_treatment_predictor_approved"]).sum()
                ),
                "causal_covariate_approved_groups": int(
                    as_bool(groups["causal_covariate_approved"]).sum()
                ),
                "recommendation_feature_approved_groups": int(
                    as_bool(groups["recommendation_feature_approved"]).sum()
                ),
                "composite_score_approved_groups": int(
                    as_bool(groups["composite_score_approved"]).sum()
                ),
                "framework_status": dimension["framework_status"],
                "permitted_use": dimension["permitted_use"],
            }
        )
    dimensions = pd.DataFrame(rows)
    protected = [
        "pre_treatment_predictor_approved_groups",
        "causal_covariate_approved_groups",
        "recommendation_feature_approved_groups",
        "composite_score_approved_groups",
    ]
    if dimensions[protected].any().any():
        raise ValueError("A protected decision-framework approval became true")
    return dimensions


def build_dashboard(config: dict[str, object], decision: pd.DataFrame) -> pd.DataFrame:
    candidates = decision[as_bool(decision["candidate_for_path_c"])].copy()
    if len(candidates) != 104 or not candidates["cluster_id"].is_unique:
        raise ValueError("Expected 104 unique Path C candidate clusters")
    missing = sorted(set(config["dashboard_fields"]) - set(candidates.columns))
    if missing:
        raise ValueError(f"Unknown decision-framework dashboard fields: {missing}")
    dashboard = candidates[config["dashboard_fields"]].copy()
    dashboard.insert(0, "analysis_version", config["analysis_version"])
    dashboard.insert(1, "checkpoint", config["checkpoint"])
    dashboard.insert(2, "framework_id", config["framework_id"])
    dashboard["opportunity_dimension_status"] = (
        "descriptive_analogue_signal_not_treatment_effect"
    )
    dashboard["strategic_need_dimension_status"] = dashboard[
        "tourism_context_status"
    ].map(
        {
            "complete_point_container_population_and_hotel_context": (
                "snow_plus_point_container_tourism_context_not_comparable_catchment"
            ),
            "population_only_no_complete_hotel_context": (
                "snow_only_candidate_tourism_dependence_incomplete"
            ),
        }
    )
    if dashboard["strategic_need_dimension_status"].isna().any():
        raise ValueError("Unexpected candidate tourism-context status")
    dashboard["accessibility_dimension_status"] = (
        "qualified_current_context_not_historical_access_or_visitor_catchment"
    )
    dashboard["competition_network_dimension_status"] = (
        "qualified_current_context_not_historical_market_structure"
    )
    dashboard["framework_status"] = (
        "exploratory_evidence_dashboard_no_business_recommendation"
    )
    dashboard["recommendation_status"] = "not_issued_evidence_gates_not_passed"
    dashboard["recommendation_confidence"] = pd.NA
    for field, value in config["protected_outputs"].items():
        dashboard[field] = bool(value)
    if dashboard["predicted_uplift_pct"].notna().any():
        raise ValueError("Predicted uplift must remain blank")
    if dashboard["composite_opportunity_need_score"].notna().any():
        raise ValueError("Composite opportunity/need score must remain blank")
    if dashboard[list(config["protected_outputs"])].any().any():
        raise ValueError("A protected dashboard output became true")
    return dashboard.sort_values("cluster_id").reset_index(drop=True)


def build_summary(
    config: dict[str, object], dimensions: pd.DataFrame, dashboard: pd.DataFrame
) -> dict[str, object]:
    return {
        "analysis_version": config["analysis_version"],
        "checkpoint": config["checkpoint"],
        "framework_id": config["framework_id"],
        "final_architecture": config["final_architecture"],
        "dimensions": int(len(dimensions)),
        "feature_groups_assigned_once": int(dimensions["feature_group_count"].sum()),
        "candidate_clusters": int(len(dashboard)),
        "candidate_good_treated_support": int(
            dashboard["reviewed_treated_ood_flag"].eq("good_support").sum()
        ),
        "candidate_moderate_treated_extrapolation": int(
            dashboard["reviewed_treated_ood_flag"].eq("moderate_extrapolation").sum()
        ),
        "candidate_strong_treated_extrapolation": int(
            dashboard["reviewed_treated_ood_flag"].eq("strong_extrapolation").sum()
        ),
        "candidates_stable_across_structural_aggregation": int(
            dashboard["aggregation_sensitivity_status"]
            .eq("stable_across_min_median_max")
            .sum()
        ),
        "candidates_with_point_container_tourism_context": int(
            dashboard["tourism_context_status"]
            .eq("complete_point_container_population_and_hotel_context")
            .sum()
        ),
        "two_dimension_matrix_ready_candidates": int(
            as_bool(dashboard["two_dimension_matrix_ready"]).sum()
        ),
        "predicted_uplift_values": int(dashboard["predicted_uplift_pct"].notna().sum()),
        "recommendations_issued": int(
            (
                ~dashboard["recommendation_status"].eq(
                    "not_issued_evidence_gates_not_passed"
                )
            ).sum()
        ),
        "composite_scores": int(
            dashboard["composite_opportunity_need_score"].notna().sum()
        ),
        "causal_interpretation_approvals": int(
            as_bool(dashboard["causal_interpretation_approved"]).sum()
        ),
        "interpretation": (
            "checkpoint_6_selects_separated_exploratory_dashboard_with_no_"
            "causal_prediction_recommendation_or_composite_score"
        ),
    }


def write_report(
    config: dict[str, object], dimensions: pd.DataFrame, summary: dict[str, object]
) -> None:
    rows = [
        "| Dimension | Feature groups | Coverage pattern | Status | Permitted use |",
        "|---|---:|---|---|---|",
    ]
    for row in dimensions.itertuples(index=False):
        coverage = (
            f"{row.complete_candidate_coverage_groups} complete / "
            f"{row.partial_candidate_coverage_groups} partial / "
            f"{row.no_candidate_feature_groups} absent"
        )
        rows.append(
            f"| {row.dimension_name} | {row.feature_group_count} | {coverage} | "
            f"{row.framework_status} | {row.permitted_use} |"
        )
    REPORT.write_text(
        f"""# Checkpoint 6 — Business decision framework

## Decision

Checkpoint 6 selects a **separated exploratory evidence dashboard** for the **{summary['candidate_clusters']} Path C candidates**. It does not select an uplift model, causal ranking, recommendation engine or composite score. The architecture keeps structural comparability, descriptive analogue opportunity, snow vulnerability, tourism dependence, accessibility, competition/network context and evidence gaps separate across **{summary['dimensions']} dimensions**.

The dashboard is deliberately incomplete as a business recommendation. Only **{summary['candidates_with_point_container_tourism_context']}** candidates have complete point-container hotel context, and those municipalities are not validated or comparable destination catchments. Historical public transport, competition and dated infrastructure remain missing. A full Opportunity × Strategic Need matrix is therefore ready for **{summary['two_dimension_matrix_ready_candidates']} candidates**.

## Dimension register

{chr(10).join(rows)}

## Candidate uncertainty

Among the 104 candidates, **{summary['candidate_good_treated_support']}** have good structural support against the reviewed treated references, **{summary['candidate_moderate_treated_extrapolation']}** are moderate extrapolations and **{summary['candidate_strong_treated_extrapolation']}** are strong extrapolations. Only **{summary['candidates_stable_across_structural_aggregation']}** remain stable on every recorded min/median/max aggregation criterion. These diagnostics qualify interpretation; they do not produce recommendation confidence or treatment-effect uncertainty.

## Protected outputs

Predicted-uplift values: **{summary['predicted_uplift_values']}**. Recommendations issued: **{summary['recommendations_issued']}**. Composite scores: **{summary['composite_scores']}**. Causal approvals: **{summary['causal_interpretation_approvals']}**. Candidate rows are sorted by stable `cluster_id`, never by opportunity signal.

## Outputs

- `config/path_c_decision_framework.json`
- `data_processed/path_c_candidate_evidence_dashboard.csv`
- `reports/path_c_decision_framework_dimensions.csv`
- `reports/path_c_decision_framework_summary.json`
- `reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md`
""",
        encoding="utf-8",
    )


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    decision = pd.read_csv(DECISION)
    readiness = pd.read_csv(READINESS)
    if not decision["analysis_version"].eq(config["analysis_version"]).all():
        raise ValueError("Decision-support and framework versions differ")
    if not readiness["analysis_version"].eq(config["analysis_version"]).all():
        raise ValueError("Feature-readiness and framework versions differ")
    dimensions = build_dimensions(config, readiness)
    dashboard = build_dashboard(config, decision)
    summary = build_summary(config, dimensions, dashboard)
    dimensions.to_csv(DIMENSIONS, index=False)
    dashboard.to_csv(DASHBOARD, index=False)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_report(config, dimensions, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
