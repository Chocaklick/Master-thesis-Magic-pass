"""Build a thesis-ready synthesis from the validated Path C outputs."""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MPL_CACHE = ROOT / "data_interim" / "matplotlib"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ANALYSIS_VERSION = "path_c_v0_31"


def load_json(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def pct(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.1f}%"


def build_coverage_figure(dimensions: pd.DataFrame) -> None:
    ordered = dimensions.sort_values("dimension_order", ascending=False).copy()
    labels = [textwrap.fill(value, 29) for value in ordered["dimension_name"]]
    complete = ordered["complete_candidate_coverage_groups"].astype(int)
    partial = ordered["partial_candidate_coverage_groups"].astype(int)
    missing = ordered["no_candidate_feature_groups"].astype(int)

    figure, axis = plt.subplots(figsize=(10.8, 6.2))
    axis.barh(labels, complete, color="#2A9D8F", label="Complete candidate coverage")
    axis.barh(
        labels,
        partial,
        left=complete,
        color="#E9C46A",
        label="Partial candidate coverage",
    )
    axis.barh(
        labels,
        missing,
        left=complete + partial,
        color="#E76F51",
        label="No candidate feature",
    )
    for y_position, (_, row) in enumerate(ordered.iterrows()):
        total = int(row["feature_group_count"])
        axis.text(total + 0.08, y_position, f"n={total}", va="center", fontsize=9)
    axis.set_xlim(0, max(ordered["feature_group_count"].astype(int)) + 1.1)
    axis.set_xlabel("Feature groups")
    axis.set_title(
        "Checkpoint 6 evidence coverage by decision dimension\n"
        "coverage is not predictive, causal or recommendation approval"
    )
    axis.grid(axis="x", alpha=0.18)
    axis.legend(frameon=False, loc="lower right")
    figure.text(
        0.01,
        0.01,
        "Path C v0.31. All 19 groups have zero pre-treatment, causal, recommendation and composite-score approvals.",
        fontsize=8,
    )
    figure.tight_layout(rect=(0, 0.045, 1, 1))
    figure.savefig(ROOT / "figures/path_c_evidence_coverage.png", dpi=180)
    plt.close(figure)


def main() -> None:
    feasibility = pd.read_csv(ROOT / "reports/feasibility_counts.csv").set_index(
        "metric"
    )["value"]
    dimensions = pd.read_csv(
        ROOT / "reports/path_c_decision_framework_dimensions.csv"
    )
    dashboard = pd.read_csv(
        ROOT / "data_processed/path_c_candidate_evidence_dashboard.csv"
    )
    decision = load_json("reports/path_c_decision_framework_summary.json")
    readiness = load_json("reports/path_c_feature_readiness_summary.json")
    historical = load_json("reports/historical_competing_pass_context_summary.json")
    transport = load_json("reports/distance_transport_comparison_summary.json")

    if decision["analysis_version"] != ANALYSIS_VERSION:
        raise ValueError("Unexpected Path C decision-framework version")
    if not dimensions["analysis_version"].eq(ANALYSIS_VERSION).all():
        raise ValueError("Mixed analysis versions in the dimension register")
    if not dashboard["analysis_version"].eq(ANALYSIS_VERSION).all():
        raise ValueError("Mixed analysis versions in the candidate dashboard")
    if len(dimensions) != 7 or int(dimensions["feature_group_count"].sum()) != 19:
        raise ValueError("Checkpoint 6 dimension register changed unexpectedly")
    if len(dashboard) != 104 or not dashboard["cluster_id"].is_unique:
        raise ValueError("Candidate dashboard grain changed unexpectedly")
    for column in [
        "two_dimension_matrix_ready",
        "causal_interpretation_approved",
        "recommendation_approved",
        "composite_score_approved",
    ]:
        if as_bool(dashboard[column]).any():
            raise ValueError(f"Protected dashboard guard failed: {column}")
    if dashboard["predicted_uplift_pct"].notna().any():
        raise ValueError("Predicted uplift must remain blank")
    if dashboard["composite_opportunity_need_score"].notna().any():
        raise ValueError("Composite score must remain blank")

    candidates = int(decision["candidate_clusters"])
    good_support = int(decision["candidate_good_treated_support"])
    strong_extrapolation = int(decision["candidate_strong_treated_extrapolation"])
    stable_candidates = int(decision["candidates_stable_across_structural_aggregation"])
    tourism_context = int(decision["candidates_with_point_container_tourism_context"])
    historical_context = int(
        decision["candidates_with_documented_historical_competing_pass_link"]
    )

    dimension_rows = "\n".join(
        "| {name} | {feature_count} | {complete} / {partial} / {missing} | {status} |".format(
            name=row.dimension_name,
            feature_count=int(row.feature_group_count),
            complete=int(row.complete_candidate_coverage_groups),
            partial=int(row.partial_candidate_coverage_groups),
            missing=int(row.no_candidate_feature_groups),
            status=row.framework_status,
        )
        for row in dimensions.sort_values("dimension_order").itertuples()
    )

    report = f"""# Thesis results synthesis — Path C v0.31

## Research conclusion

The validated data support an **exploratory Business Analytics decision-support architecture**, not a causal Magic Pass effect model and not a candidate ranking. Checkpoints 1–3 establish a reproducible data foundation. Checkpoint 4 rejects causal estimation under the present design because there are **{feasibility['causal_treatment_units_approved']} approved treatment units** and **{feasibility['approved_usable_controls']} approved controls**. Checkpoint 5 rejects heterogeneous-effect machine learning because the effective treated-destination sample is too small and no defensible causal target exists. Checkpoint 6 therefore retains a seven-dimension evidence dashboard with protected blank uplift, composite-score and recommendation fields.

This negative feasibility result is substantive: the project prevents a technically elaborate model from being presented as causal when treatment exposure, donor validity, spillovers and pre-treatment comparability are not identified.

## Analytical foundation

| Empirical layer | Validated scope | Thesis interpretation |
|---|---:|---|
| Supplied resort listings | {feasibility['resort_listings_total']} | Directory listings, not independent destinations |
| Existing lift clusters | {feasibility['lift_clusters_total']} | Preserved; {feasibility['lift_clusters_linked_to_resort_listings']} link to at least one listing |
| Hotel municipalities | {feasibility['hotel_municipalities_total']} | {feasibility['hotel_observed_month_rows']} observed monthly overnight-stay cells, 2013-01 to 2026-03 |
| Reviewed destination units | {feasibility['reviewed_destination_units']} | {feasibility['reviewed_destination_units_in_outcome_panel']} enter the outcome panel; three composite scopes are excluded |
| Apparent Path C candidates | {candidates} | Screening universe, not verified non-membership or recommended resorts |
| Historical competing-pass context | {historical['area_season_rows']} area-season rows | {historical['documented_listing_season_links']} conservative positive listing-season links; non-links are not absence |
| Scheduled public-transport comparison | {feasibility['public_transport_journey_pairs']} destination–municipality pairs | Current winter-2026 context, not historical accessibility |

## Feasibility gates

| Gate | Result | Consequence |
|---|---:|---|
| Approved causal treatment units | {feasibility['causal_treatment_units_approved']} | No defensible event-study/DiD treatment sample |
| Approved controls | {feasibility['approved_usable_controls']} | No promoted donor comparison |
| Candidate catchments validated | {feasibility['validated_tourism_catchments']} | Municipal tourism intensity remains qualified context |
| Pre-treatment feature groups approved | {readiness['groups_approved_as_pre_treatment_predictors']} / {readiness['feature_groups']} | No supervised candidate-uplift model |
| Causal covariate groups approved | {readiness['groups_approved_as_causal_covariates']} / {readiness['feature_groups']} | No causal adjustment using current/post-treatment context |
| Candidates ready for full Opportunity × Strategic Need matrix | {decision['two_dimension_matrix_ready_candidates']} / {candidates} | No complete matrix or rank |
| Recommendations issued | {decision['recommendations_issued']} | Recommendation fields remain intentionally blank |

## Selected Path C architecture

The final architecture separates evidence that would otherwise be easy to conflate. The coverage pattern below is reported at feature-group level; **coverage does not imply analytical permission**.

| Dimension | Groups | Complete / partial / unavailable | Status |
|---|---:|---:|---|
{dimension_rows}

Across the 19 groups, **{readiness['groups_with_complete_candidate_coverage']}** have complete candidate coverage, **{readiness['groups_with_partial_candidate_coverage']}** are partial and **{readiness['groups_without_candidate_feature']}** are unavailable at candidate level. Only the undated structural-similarity group is approved for exploratory similarity; zero groups are approved for prediction, causal adjustment, recommendation or composite scoring.

![Checkpoint 6 evidence coverage](../figures/path_c_evidence_coverage.png)

## Candidate-side descriptive findings

- **{good_support} of {candidates} candidates ({pct(good_support, candidates)})** have good structural support relative to the reviewed treated references, while **{strong_extrapolation} ({pct(strong_extrapolation, candidates)})** are strong extrapolations.
- Only **{stable_candidates} candidates ({pct(stable_candidates, candidates)})** preserve every recorded segment, nearest-analogue and support classification under minimum/median/maximum within-cluster aggregation. This is the strongest reason not to turn analogue results into a league table.
- Point-container tourism context is complete for **{tourism_context} candidates ({pct(tourism_context, candidates)})**. Radius rules reach more candidates but fail destination-catchment validation, so they do not repair the strategic-need dimension.
- A documented positive link to at least one of five partially reconstructed historical competing passes exists for **{historical_context} candidates ({pct(historical_context, candidates)})**. The remaining candidates cannot be labelled historically absent from competing passes.

## Accessibility result

Straight-line distance is informative but not interchangeable with scheduled public-transport time. Across the reviewed destinations, **{transport['destination_municipality_pairs']}** destination–municipality pairs are compared; **{transport['bidirectional_mean_pairs']}** have both outbound and return means and **{transport['complete_all_sampled_time_pairs']}** are feasible at every sampled time. The median destination-specific distance/time rank correlation is **{float(transport['median_destination_distance_round_trip_rank_correlation_available_pairs']):.3f}**. At the declared rank-gap threshold, **{transport['materially_worse_transit_than_distance_rank_pairs']}** pairs have worse transit access than distance suggests. These are current scheduled-access diagnostics, not historical exposure measures.

## Defensible contribution

The contribution is the reproducible integration of hotel demand and capacity, reviewed Magic Pass history, preserved lift clusters, snow and weather sensitivities, population, road and public-transport context, competing-pass history and explicit evidence gates. The dashboard makes useful descriptive heterogeneity visible while preserving the distinction between:

1. data availability and permission to model;
2. structural similarity and treatment-effect similarity;
3. current accessibility and historical pre-treatment accessibility;
4. positive competing-pass evidence and verified market absence;
5. a municipality containing a resort point and a validated tourism catchment.

## Claims the thesis must not make

- It must not report the analogue signal as predicted uplift or a Magic Pass treatment effect.
- It must not rank the 104 candidates as recommendations.
- It must not interpret current competing-pass non-links as historical absence.
- It must not present winter-2026 transport time, current infrastructure or current tourism intensity as pre-treatment covariates.
- It must not describe the preserved lift clusters as certified independent ski destinations.

## Writing implication

The results chapter should lead with the causal/ML feasibility decision, then present Path C as the empirically supported fallback architecture. Candidate-level examples may illustrate how the seven dimensions expose evidence and uncertainty, but stable IDs rather than an opportunity score must determine display order. Missing detailed SnowPass small-lift schedules, historical GTFS feeds, candidate catchments, dated infrastructure, walking access and independent climate measurements belong in limitations and future research unless a specific thesis claim makes one indispensable.
"""

    (ROOT / "reports/42_THESIS_RESULTS_SYNTHESIS.md").write_text(
        report, encoding="utf-8"
    )
    build_coverage_figure(dimensions)

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "architecture": decision["final_architecture"],
        "candidate_clusters": candidates,
        "dimensions": len(dimensions),
        "feature_groups": int(readiness["feature_groups"]),
        "complete_candidate_coverage_groups": int(
            readiness["groups_with_complete_candidate_coverage"]
        ),
        "partial_candidate_coverage_groups": int(
            readiness["groups_with_partial_candidate_coverage"]
        ),
        "unavailable_candidate_feature_groups": int(
            readiness["groups_without_candidate_feature"]
        ),
        "approved_causal_treatment_units": int(
            feasibility["causal_treatment_units_approved"]
        ),
        "approved_controls": int(feasibility["approved_usable_controls"]),
        "recommendations_issued": int(decision["recommendations_issued"]),
        "composite_scores": int(decision["composite_scores"]),
        "causal_interpretation_approvals": int(
            decision["causal_interpretation_approvals"]
        ),
        "report": "reports/42_THESIS_RESULTS_SYNTHESIS.md",
        "figure": "figures/path_c_evidence_coverage.png",
    }
    (ROOT / "reports/thesis_results_synthesis_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
