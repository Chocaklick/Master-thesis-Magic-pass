"""Build an explicit use/readiness registry for Path C feature groups."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "path_c_feature_readiness.json"
DECISION = ROOT / "data_processed" / "magic_pass_decision_support.csv"
OUTPUT = ROOT / "reports" / "path_c_feature_readiness_audit.csv"
SUMMARY = ROOT / "reports" / "path_c_feature_readiness_summary.json"
REPORT = ROOT / "reports" / "38_PATH_C_FEATURE_READINESS_AUDIT.md"


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def build_audit(config: dict[str, object], decision: pd.DataFrame) -> pd.DataFrame:
    candidates = decision[as_bool(decision["candidate_for_path_c"])].copy()
    if len(candidates) != 104 or not candidates["cluster_id"].is_unique:
        raise ValueError("Expected 104 unique Path C candidate clusters")
    if not decision["analysis_version"].eq(config["analysis_version"]).all():
        raise ValueError("Feature-readiness and decision-support versions differ")

    global_approvals = config["global_approvals"]
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for group in config["feature_groups"]:
        group_id = group["feature_group_id"]
        if group_id in seen:
            raise ValueError(f"Duplicate feature group: {group_id}")
        seen.add(group_id)
        required = list(group["candidate_required_fields"])
        missing_fields = sorted(set(required) - set(candidates.columns))
        if missing_fields:
            raise ValueError(f"Unknown candidate fields for {group_id}: {missing_fields}")
        if required:
            available = candidates[required].notna().all(axis=1)
            coverage = int(available.sum())
        else:
            coverage = 0
        if coverage == len(candidates):
            coverage_status = "complete_candidate_coverage"
        elif coverage == 0:
            coverage_status = "no_candidate_feature"
        else:
            coverage_status = "partial_candidate_coverage"

        rows.append(
            {
                "analysis_version": config["analysis_version"],
                "feature_group_id": group_id,
                "feature_group_name": group["feature_group_name"],
                "candidate_required_fields": "|".join(required),
                "candidate_pool_count": len(candidates),
                "candidate_rows_with_complete_required_fields": coverage,
                "candidate_coverage_share": coverage / len(candidates),
                "candidate_coverage_status": coverage_status,
                "evidence_scope": group["evidence_scope"],
                "temporal_status": group["temporal_status"],
                "scope_comparability_status": group["scope_comparability_status"],
                "leakage_risk": group["leakage_risk"],
                "approved_usage": group["approved_usage"],
                "exploratory_similarity_use_approved": bool(
                    group["exploratory_similarity_use_approved"]
                ),
                "descriptive_context_use_approved": bool(
                    group["descriptive_context_use_approved"]
                ),
                "pre_treatment_predictor_approved": bool(
                    global_approvals["pre_treatment_predictor_approved"]
                ),
                "causal_covariate_approved": bool(
                    global_approvals["causal_covariate_approved"]
                ),
                "recommendation_feature_approved": bool(
                    global_approvals["recommendation_feature_approved"]
                ),
                "composite_score_approved": bool(
                    global_approvals["composite_score_approved"]
                ),
                "source_ids": group["source_ids"],
            }
        )
    audit = pd.DataFrame(rows)
    if audit["exploratory_similarity_use_approved"].sum() != 1:
        raise ValueError("Exactly one feature group must be approved for similarity")
    protected = [
        "pre_treatment_predictor_approved",
        "causal_covariate_approved",
        "recommendation_feature_approved",
        "composite_score_approved",
    ]
    if audit[protected].any().any():
        raise ValueError("A protected Path C feature approval became true")
    return audit


def build_summary(audit: pd.DataFrame) -> dict[str, object]:
    return {
        "analysis_version": audit["analysis_version"].iloc[0],
        "feature_groups": int(len(audit)),
        "groups_with_complete_candidate_coverage": int(
            audit["candidate_coverage_status"].eq("complete_candidate_coverage").sum()
        ),
        "groups_with_partial_candidate_coverage": int(
            audit["candidate_coverage_status"].eq("partial_candidate_coverage").sum()
        ),
        "groups_without_candidate_feature": int(
            audit["candidate_coverage_status"].eq("no_candidate_feature").sum()
        ),
        "groups_approved_for_exploratory_similarity": int(
            audit["exploratory_similarity_use_approved"].sum()
        ),
        "groups_approved_for_descriptive_context": int(
            audit["descriptive_context_use_approved"].sum()
        ),
        "groups_approved_as_pre_treatment_predictors": int(
            audit["pre_treatment_predictor_approved"].sum()
        ),
        "groups_approved_as_causal_covariates": int(
            audit["causal_covariate_approved"].sum()
        ),
        "groups_approved_for_recommendations": int(
            audit["recommendation_feature_approved"].sum()
        ),
        "groups_approved_for_composite_score": int(
            audit["composite_score_approved"].sum()
        ),
        "structural_similarity_temporal_status": audit.set_index(
            "feature_group_id"
        ).loc["structural_similarity", "temporal_status"],
        "interpretation": (
            "explicit_feature_use_registry_prevents_current_or_post_treatment_"
            "context_from_becoming_predictive_causal_or_recommendation_input"
        ),
    }


def write_report(audit: pd.DataFrame, summary: dict[str, object]) -> None:
    table_rows = []
    for row in audit.itertuples(index=False):
        table_rows.append(
            f"| {row.feature_group_name} | "
            f"{row.candidate_rows_with_complete_required_fields}/{row.candidate_pool_count} | "
            f"{row.temporal_status} | {row.approved_usage} |"
        )
    report = f"""# Path C feature-readiness audit

## Decision

The registry covers **{summary['feature_groups']} feature groups**. Only **{summary['groups_approved_for_exploratory_similarity']}** group—the three current structural fields—is approved for the existing exploratory similarity calculation. **{summary['groups_approved_as_pre_treatment_predictors']}** groups are approved as pre-treatment predictors, **{summary['groups_approved_as_causal_covariates']}** as causal covariates, **{summary['groups_approved_for_recommendations']}** for recommendations and **{summary['groups_approved_for_composite_score']}** for a composite score.

Complete candidate coverage is available for **{summary['groups_with_complete_candidate_coverage']}** groups, partial coverage for **{summary['groups_with_partial_candidate_coverage']}**, and no candidate-level feature exists for **{summary['groups_without_candidate_feature']}**. Coverage is not approval: most complete layers are current or post-treatment descriptive context.

## Registry

| Feature group | Complete candidate rows | Temporal status | Approved usage |
|---|---:|---|---|
{chr(10).join(table_rows)}

## Guardrail

The current structural fields remain undated and may themselves postdate treatment. Their sole approval is the already declared exploratory segmentation and analogue distance; it is not predictive or causal approval. Opportunity uses post-treatment reference outcomes and remains a separate descriptive dimension. Snow, tourism, population, transport, road, stop, competition and network layers remain outside the similarity calculation. Historical public transport, historical competing-pass status and dated infrastructure remain absent.

The registry is executable: every declared decision-support field must exist, candidate coverage is recomputed from the 104-candidate table, exactly one group may enter exploratory similarity, and all pre-treatment, causal, recommendation and composite approvals must remain false.

## Outputs

- `config/path_c_feature_readiness.json`
- `reports/path_c_feature_readiness_audit.csv`
- `reports/path_c_feature_readiness_summary.json`
- `reports/38_PATH_C_FEATURE_READINESS_AUDIT.md`
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    decision = pd.read_csv(DECISION)
    audit = build_audit(config, decision)
    summary = build_summary(audit)
    audit.to_csv(OUTPUT, index=False)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_report(audit, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
