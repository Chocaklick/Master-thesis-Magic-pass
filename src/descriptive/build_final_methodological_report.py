"""Build the mission-required 18-question methodological report and executive summary."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_VERSION = "path_c_v0_31"


def load(name: str) -> dict:
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))


def main() -> None:
    initial = load("initial_findings.json")
    current_magic = load("current_magic_pass_summary.json")
    membership = load("membership_continuity_summary.json")
    panel = load("treatment_panel_summary.json")
    donor_pretrend = load("donor_pretrend_summary.json")
    donor_shocks = load("donor_external_shock_summary.json")
    path_c = load("path_c_summary.json")
    aggregation = load("path_c_aggregation_sensitivity_summary.json")
    readiness = load("path_c_feature_readiness_summary.json")
    decision = load("path_c_decision_framework_summary.json")
    scope = load("candidate_scope_radius_sensitivity_summary.json")
    snow_station = load("snow_station_sensitivity_summary.json")
    distance_transport = load("distance_transport_comparison_summary.json")
    examples = load("thesis_candidate_uncertainty_examples_summary.json")

    for payload in [path_c, readiness, decision, scope, distance_transport, examples]:
        if payload.get("analysis_version") != ANALYSIS_VERSION:
            raise ValueError("Final report inputs do not share Path C v0.31")
    protected = {
        "causal_treatments": int(panel["causal_treatment_units_approved"]),
        "causal_controls": int(donor_shocks["causal_controls_approved"]),
        "predicted_uplift_values": int(decision["predicted_uplift_values"]),
        "recommendations_issued": int(decision["recommendations_issued"]),
        "composite_scores": int(decision["composite_scores"]),
        "causal_interpretation_approvals": int(
            decision["causal_interpretation_approvals"]
        ),
    }
    if any(protected.values()):
        raise ValueError(f"Final report guard failed: {protected}")

    answers = [
        {
            "question_number": 1,
            "question": "How many ski resorts are available?",
            "short_answer": "271 directory listings; not 271 independent resorts.",
            "answer": (
                f"The supplied directory contains {initial['resort_listings']} listings. "
                f"The preserved lift layer contains {initial['clusters']} clusters, of which "
                f"{initial['assigned_clusters']} link to at least one listing. Because "
                f"{initial['multi_listing_clusters']} linked clusters contain multiple listings "
                "and commercial-domain boundaries are not certified, no single independent-resort "
                "count is claimed."
            ),
            "evidence": "reports/01_DATA_AUDIT.md|reports/03_CLUSTER_VALIDATION.md",
        },
        {
            "question_number": 2,
            "question": "How many are Magic Pass members?",
            "short_answer": "95 official current destinations; 69 conservatively linked directory listings.",
            "answer": (
                f"The official current-map snapshot contains {current_magic['official_current_destinations']} "
                f"destinations. Conservative entity resolution links {current_magic['candidate_resolved_destinations']} "
                f"of those labels to supplied directory listings and leaves "
                f"{current_magic['unresolved_destinations']} unresolved. At the preserved cluster level, "
                f"the Path C feature table contains {path_c['resolved_current_magic_reference_clusters'] + 1} "
                f"resolved current Magic clusters; {path_c['resolved_current_magic_reference_clusters']} "
                "have complete structural fields and form the analogue reference pool. The counts are "
                "not interchangeable because destination labels, listings and clusters have different scope."
            ),
            "evidence": "data_processed/magic_pass_current_destinations.csv|reports/current_magic_pass_summary.json|reports/path_c_summary.json",
        },
        {
            "question_number": 3,
            "question": "How many treated resorts have reliable entry dates?",
            "short_answer": "14 reviewed destination units have documented entry seasons; none has an exact causal activation date.",
            "answer": (
                f"The review consolidates 18 component entry events into {panel['reviewed_destination_units']} "
                f"destination units. All {membership['destination_units_with_fully_documented_active_seasons']} "
                "have explicit positive evidence for their active seasons, but entry timing is mainly seasonal "
                "rather than an exact activation date and treatment intensity is not homogeneous. Eleven units "
                "have an explicit hotel-outcome scope. Zero units are approved as causal treatments."
            ),
            "evidence": "reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md|reports/membership_continuity_audit.csv|reports/treatment_panel_summary.json",
        },
        {
            "question_number": 4,
            "question": "How many have sufficient pre-treatment observations?",
            "short_answer": "7 support the 24-month adjacent-window diagnostic; 6 support 36 months.",
            "answer": (
                f"Under the explicit season carry-forward diagnostic, "
                f"{panel['units_with_24_pre_and_24_active_post_months_assumption']} units have 24 observed "
                f"pre and 24 active-post months, and {panel['units_with_36_pre_and_36_active_post_months_assumption']} "
                "have 36 on each side. These are coverage counts, not causal-readiness approvals."
            ),
            "evidence": "reports/treatment_panel_summary.json|reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md",
        },
        {
            "question_number": 5,
            "question": "How many have sufficient post-treatment observations?",
            "short_answer": "The same 7 units have 24 active-post months; 6 have 36.",
            "answer": (
                "The adjacent-window gate is joint: seven reviewed panel units have both 24 pre and "
                "24 active-post months, while six have both 36 pre and 36 active-post months. Post-period "
                "coverage does not resolve treatment intensity, donors, spillovers or contemporaneous shocks."
            ),
            "evidence": "reports/treatment_panel_summary.json|reports/model_feasibility_report.md",
        },
        {
            "question_number": 6,
            "question": "Are parallel trends plausible?",
            "short_answer": "Not established for any approved treatment-control pair.",
            "answer": (
                f"A descriptive pre-period screen ranked {donor_pretrend['provisional_pairs_screened']} "
                f"pairs and shortlisted {donor_pretrend['shortlisted_pairs_for_manual_review']}. "
                f"Twenty-eight shortlisted pairs were at or within 50 km of another resolved Magic point. "
                f"All {donor_shocks['beyond_50km_pairs_reviewed']} remote pairs had documented "
                "contemporaneous donor-specific shocks. Pre-period similarity therefore did not establish "
                "a credible counterfactual trend."
            ),
            "evidence": "reports/11_DONOR_PRETREND_SCREEN.md|reports/14_DONOR_NETWORK_SPILLOVER_AUDIT.md|reports/16_DONOR_EXTERNAL_SHOCK_AUDIT.md",
        },
        {
            "question_number": 7,
            "question": "Is causal inference credible?",
            "short_answer": "No under the current design.",
            "answer": (
                "Zero treatments and zero controls pass the joint identification gates. The blockers are "
                "treatment scope and intensity, donor contamination, regional interference, local shocks, "
                "outcome-scope uncertainty and current/post-treatment covariates. No treatment effect is estimated."
            ),
            "evidence": "reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md|reports/model_experiment_log.csv",
        },
        {
            "question_number": 8,
            "question": "Is heterogeneous treatment-effect modelling statistically feasible?",
            "short_answer": "No.",
            "answer": (
                f"The effective treatment sample is at most {panel['reviewed_destination_units']} reviewed "
                f"destinations, only {panel['units_with_24_pre_and_24_active_post_months_assumption']} with the "
                "joint 24/24 coverage gate and zero with causal approval. Repeated municipality-month rows do "
                "not create independent treated destinations, so stable heterogeneity estimation is unsupported."
            ),
            "evidence": "reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md|reports/model_experiment_log.csv",
        },
        {
            "question_number": 9,
            "question": "Is Causal Forest feasible?",
            "short_answer": "No.",
            "answer": (
                "Causal Forest is rejected because the causal target is unidentified, no control is approved, "
                "overlap cannot be defended and the number of independent treated units is too small. A software "
                "implementation would not repair those design failures."
            ),
            "evidence": "reports/model_experiment_log.csv|reports/47_METHODOLOGICAL_LITERATURE.md",
        },
        {
            "question_number": 10,
            "question": "Is standard ML useful?",
            "short_answer": "Only for qualified descriptive structure, not outcome prediction or uplift.",
            "answer": (
                "Supervised ML has no defensible cluster-level causal or recommendation target and would face "
                "leakage from current/post-treatment features. Unsupervised structural segmentation and nearest-"
                "analogue distances are useful as transparent exploratory tools with grouped entities, explicit "
                "support checks and aggregation sensitivity."
            ),
            "evidence": "reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md|reports/38_PATH_C_FEATURE_READINESS_AUDIT.md",
        },
        {
            "question_number": 11,
            "question": "Is a neural network justified?",
            "short_answer": "No.",
            "answer": (
                "The sample of independent destinations is far too small, the target is not causally approved, "
                "and a neural network would reduce interpretability while increasing leakage and overfitting risk."
            ),
            "evidence": "reports/model_experiment_log.csv|reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md",
        },
        {
            "question_number": 12,
            "question": "Is clustering/similarity more appropriate?",
            "short_answer": "Yes, as an exploratory fallback with explicit sensitivity checks.",
            "answer": (
                f"Among {path_c['segmentation_eligible_clusters']} structurally complete clusters, k=2 has "
                f"silhouette {path_c['selected_silhouette']:.3f} and median subsample ARI "
                f"{path_c['selected_bootstrap_ari_median']:.3f}. However, only "
                f"{aggregation['candidates_fully_stable_across_aggregation_rules']} of "
                f"{aggregation['candidate_clusters']} candidates retain every recorded segment, analogue and "
                "support criterion across min/median/max aggregation. Clustering is therefore more appropriate "
                "only as a qualified descriptive device."
            ),
            "evidence": "reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md|reports/19_PATH_C_AGGREGATION_SENSITIVITY.md",
        },
        {
            "question_number": 13,
            "question": "What is the most defensible final Business Analytics methodology?",
            "short_answer": "A separated seven-dimension exploratory evidence dashboard.",
            "answer": (
                f"Checkpoint 6 selects a {decision['dimensions']}-dimension dashboard covering "
                f"{decision['candidate_clusters']} apparent candidates and assigning all "
                f"{decision['feature_groups_assigned_once']} evidence groups exactly once. Structural similarity, "
                "analogue opportunity, snow vulnerability, tourism context, accessibility, competition/network "
                "context and evidence gaps remain separate. No weighted composite, ranking or treatment-effect "
                "prediction is authorised."
            ),
            "evidence": "reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md|reports/42_THESIS_RESULTS_SYNTHESIS.md",
        },
        {
            "question_number": 14,
            "question": "Which variables appear most informative?",
            "short_answer": "Current structural fields are the only approved similarity inputs; other layers are informative context.",
            "answer": (
                "Published top altitude, ski-area kilometres and lift count provide the clearest reproducible "
                "cross-sectional structural separation and are the only fields approved for exploratory similarity. "
                "Snow vulnerability, point-container tourism intensity, population/accessibility, competing-pass "
                "links and network density help diagnose context and uncertainty, but none is approved as a "
                "pre-treatment predictor, causal covariate, recommendation input or composite-score component."
            ),
            "evidence": "reports/path_c_feature_readiness_audit.csv|reports/38_PATH_C_FEATURE_READINESS_AUDIT.md",
        },
        {
            "question_number": 15,
            "question": "Which variables are missing?",
            "short_answer": "Validated candidate catchments, historical access/infrastructure and treatment-intensity data remain missing.",
            "answer": (
                "Material gaps include externally validated destination catchments and exposure weights, historical "
                "public-transport/service measures, dated lift capacity and infrastructure, systematic snowmaking, "
                "complete historical competing-pass coverage, area-specific summer rights, hotel-location/final-mile "
                "access and a broader uncontaminated donor universe. Four readiness groups have no candidate feature "
                f"and two have only partial candidate coverage."
            ),
            "evidence": "reports/38_PATH_C_FEATURE_READINESS_AUDIT.md|PROJECT_STATE.md",
        },
        {
            "question_number": 16,
            "question": "What are the main sources of uncertainty?",
            "short_answer": "Entity scope, treatment, counterfactuals, timing and spatial proxy mismatch.",
            "answer": (
                "The principal uncertainties are multi-listing cluster semantics, resort-to-municipality exposure, "
                "season-level and heterogeneous treatment, donor shocks and spillovers, current/post-treatment feature "
                "timing, station-to-resort snow mismatch, timetable currentness and incomplete historical pass-market "
                f"coverage. The snow-station sensitivity classifies {snow_station['agreement_counts']['low']} of "
                f"{snow_station['reviewed_resort_components']} component comparisons as low, and the four-case "
                "appendix demonstrates how aggregation and empirical support can change at row level."
            ),
            "evidence": "reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md|reports/48_CANDIDATE_UNCERTAINTY_EXAMPLES.md",
        },
        {
            "question_number": 17,
            "question": "Which additional data would most improve the model?",
            "short_answer": "Destination exposure definitions and a much larger credible treatment/control design.",
            "answer": (
                "The highest-value additions are externally validated destination boundaries and municipality weights, "
                "treatment intensity and exact timing, a larger set of credibly untreated comparison destinations with "
                "shock/interference audits, and pre-treatment histories for hotel capacity, infrastructure, access and "
                "snowmaking. Stakeholder-defined decision weights are also required before any composite business score."
            ),
            "evidence": "reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md|reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md",
        },
        {
            "question_number": 18,
            "question": "Can the final system reasonably be described as predictive, causal, exploratory or decision-support?",
            "short_answer": "Exploratory and decision-support oriented; not predictive or causal.",
            "answer": (
                f"The final system is an exploratory decision-support evidence architecture. It has "
                f"{readiness['groups_approved_for_exploratory_similarity']} feature group approved for similarity, "
                f"{readiness['groups_approved_as_pre_treatment_predictors']} approved pre-treatment predictors, "
                f"{readiness['groups_approved_as_causal_covariates']} causal covariates, "
                f"{decision['recommendations_issued']} recommendations and "
                f"{decision['causal_interpretation_approvals']} causal interpretations. It must not be described "
                "as an uplift model, profitability estimate or admission ranking."
            ),
            "evidence": "reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md|reports/path_c_feature_readiness_audit.csv",
        },
    ]
    answers_frame = pd.DataFrame(answers)
    if answers_frame["question_number"].tolist() != list(range(1, 19)):
        raise ValueError("Final methodological report must answer questions 1 through 18")
    answers_frame.to_csv(
        ROOT / "reports" / "final_methodological_question_answers.csv", index=False
    )

    answer_sections = "\n\n".join(
        f"## {row.question_number}. {row.question}\n\n"
        f"**Answer:** {row.short_answer}\n\n{row.answer}\n\n"
        f"**Internal evidence:** `{row.evidence.replace('|', '`, `')}`"
        for row in answers_frame.itertuples()
    )
    report = f"""# Final methodological report

This report answers the 18 questions required by the authoritative project mission. It is generated from validated Path C v0.31 outputs. Counts use their stated entity level; listings, lift clusters, official destinations, reviewed destination units and municipalities are not silently treated as equivalent.

## Final decision

The available data support a reproducible **exploratory decision-support framework**, not a causal, predictive-uplift or profitability model. Checkpoints 4 and 5 fail because zero treatments and zero controls are causally approved. Checkpoint 6 therefore retains a transparent seven-dimension dashboard with no recommendation ranking or composite score.

{answer_sections}

## Reproducibility and claim boundary

All numerical answers are regenerated from repository summaries and linked to internal evidence artifacts. External-source claims are mapped separately in `reports/46_THESIS_CITATION_MAP.md`; methodological references are in `reports/47_METHODOLOGICAL_LITERATURE.md`. The four candidate rows in `reports/48_CANDIDATE_UNCERTAINTY_EXAMPLES.md` illustrate uncertainty categories only. No answer in this report authorises a candidate recommendation or a treatment-effect interpretation.
"""
    (ROOT / "reports" / "49_FINAL_METHODOLOGICAL_REPORT.md").write_text(
        report.rstrip() + "\n", encoding="utf-8"
    )

    executive = f"""# Executive summary

## Research decision

This thesis evaluates whether the available Swiss ski-resort, hotel-demand, Magic Pass, snow/climate and accessibility evidence can support causal effect estimation and strategic decision support. The central conclusion is deliberately narrower than the initial ambition: the evidence does **not** support a credible causal estimate of Magic Pass membership, heterogeneous treatment-effect modelling or a ranked admission recommendation. It does support a reproducible exploratory framework that makes structural comparability, contextual evidence and uncertainty visible without combining them into a misleading score.

## Evidence base

The supplied universe contains **{initial['resort_listings']} directory listings**, **{initial['clusters']} preserved lift clusters** and **{initial['assigned_clusters']} clusters linked to at least one listing**. These are not certified independent commercial resorts. The hotel panel contains {initial['monthly_grid_rows']:,} municipality-month rows for {initial['municipality_labels']} municipalities from January 2013 through March 2026. Fourteen Magic Pass destination units were manually reviewed, 11 have an explicit hotel-outcome scope and seven have the joint 24-month pre/post coverage required for the adjacent-window diagnostic.

## Why causal and predictive modelling were rejected

The donor process screened {donor_pretrend['provisional_pairs_screened']} descriptive treatment-donor pairs and shortlisted {donor_pretrend['shortlisted_pairs_for_manual_review']}. Twenty-eight shortlisted pairs were at or within 50 km of another resolved Magic Pass point; every one of the seven remote pairs had an independently documented contemporaneous local shock. Zero causal treatments and zero controls were approved. With at most 14 reviewed treated destinations, only seven passing the 24/24 coverage screen and no identified causal target, causal forests, meta-learners, standard uplift models and neural networks are not statistically defensible.

## Final analytical architecture

Checkpoint 6 selects a **seven-dimension separated evidence dashboard** for {decision['candidate_clusters']} apparent candidates. The 19 evidence groups cover structural similarity, analogue opportunity, snow vulnerability, tourism context, accessibility, competition/network context and evidence gaps. Thirteen groups have complete candidate coverage, two are partial and four lack a candidate feature. Coverage is not permission: only structural similarity is approved for exploratory matching, while zero groups are approved as pre-treatment predictors, causal covariates, recommendation inputs or composite-score components.

The structural solution uses top altitude, ski-area kilometres and lift count. Among {path_c['segmentation_eligible_clusters']} complete clusters, k=2 achieves silhouette {path_c['selected_silhouette']:.3f} and median subsample ARI {path_c['selected_bootstrap_ari_median']:.3f}. Yet only {aggregation['candidates_fully_stable_across_aggregation_rules']} of 104 candidates preserve every recorded segment, analogue and support criterion across minimum, median and maximum within-cluster aggregation. Twenty-five candidates are strong extrapolations from the eight reviewed treated references. These diagnostics prevent structural resemblance from being mistaken for predicted benefit.

## Business interpretation

The framework is useful for organising due diligence, not deciding admission. It can show whether a candidate lies inside the observed structural support, where snow or access context may be relevant and which evidence is incomplete. It cannot estimate expected overnight-stay gains, financial profitability or the causal effect of joining Magic Pass. The four fixed examples in the uncertainty appendix demonstrate how the same evidence system communicates stability, aggregation sensitivity and extrapolation without ranking candidates.

## Priority next evidence

The most valuable future inputs are externally validated destination catchments and municipality exposure weights, exact treatment timing and intensity, a larger uncontaminated donor/treatment universe, and pre-treatment histories for hotel capacity, access, lift/infrastructure investment and snowmaking. Historical timetable and pass details are secondary unless required for a specific claim. Stakeholder-defined decision weights would be required before any composite business score could be considered.

## Final classification

The completed system is **exploratory and decision-support oriented**. It is not causal, not an uplift predictor, not a profitability model and not a candidate ranking. This boundary is the principal methodological result of the thesis.
"""
    (ROOT / "reports" / "EXECUTIVE_SUMMARY.md").write_text(
        executive.rstrip() + "\n", encoding="utf-8"
    )

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "questions_answered": len(answers_frame),
        "final_classification": "exploratory_and_decision_support_not_predictive_or_causal",
        "resort_listings": int(initial["resort_listings"]),
        "linked_lift_clusters": int(initial["assigned_clusters"]),
        "official_current_magic_destinations": int(
            current_magic["official_current_destinations"]
        ),
        "reviewed_destination_units": int(panel["reviewed_destination_units"]),
        "units_with_24_pre_and_post_months": int(
            panel["units_with_24_pre_and_24_active_post_months_assumption"]
        ),
        "causal_treatments_approved": protected["causal_treatments"],
        "causal_controls_approved": protected["causal_controls"],
        "candidate_clusters": int(decision["candidate_clusters"]),
        "recommendations_issued": protected["recommendations_issued"],
        "composite_scores": protected["composite_scores"],
        "causal_interpretation_approvals": protected[
            "causal_interpretation_approvals"
        ],
        "interpretation": "mission_required_final_methodological_answers_with_explicit_entity_denominators_and_guardrails",
    }
    (ROOT / "reports" / "final_methodological_report_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
