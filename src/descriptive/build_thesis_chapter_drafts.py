"""Generate methods, results, and discussion chapter drafts from validated outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_VERSION = "path_c_v0_31"


def load_json(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def main() -> None:
    feasibility = pd.read_csv(ROOT / "reports/feasibility_counts.csv").set_index(
        "metric"
    )["value"]
    path_c = load_json("reports/path_c_summary.json")
    aggregation = load_json("reports/path_c_aggregation_sensitivity_summary.json")
    panel = load_json("reports/treatment_panel_summary.json")
    continuity = load_json("reports/membership_continuity_summary.json")
    donor_pretrend = load_json("reports/donor_pretrend_summary.json")
    donor_network = load_json("reports/donor_network_spillover_summary.json")
    donor_shocks = load_json("reports/donor_external_shock_summary.json")
    decision = load_json("reports/path_c_decision_framework_summary.json")
    readiness = load_json("reports/path_c_feature_readiness_summary.json")
    scope = load_json("reports/candidate_scope_radius_sensitivity_summary.json")
    concordance = load_json("reports/destination_scope_concordance_audit_summary.json")
    snow_station = load_json("reports/snow_station_sensitivity_summary.json")
    snow_grid = load_json("reports/snow_gridded_sensitivity_summary.json")
    weather_station = load_json("reports/weather_station_sensitivity_summary.json")
    weather_grid = load_json("reports/weather_gridded_sensitivity_summary.json")
    public_transport = load_json("reports/public_transport_journey_context_summary.json")
    distance_transport = load_json("reports/distance_transport_comparison_summary.json")
    historical_pass = load_json("reports/historical_competing_pass_context_summary.json")

    versioned = [
        path_c,
        decision,
        readiness,
        scope,
        snow_grid,
        weather_station,
        weather_grid,
        public_transport,
        distance_transport,
        historical_pass,
    ]
    for summary in versioned:
        if summary.get("analysis_version") != ANALYSIS_VERSION:
            raise ValueError("Chapter inputs do not share Path C v0.31")
    if int(panel["causal_treatment_units_approved"]) != 0:
        raise ValueError("Methods draft guard failed: a causal treatment is approved")
    if int(donor_shocks["causal_controls_approved"]) != 0:
        raise ValueError("Methods draft guard failed: a causal control is approved")
    if int(decision["recommendations_issued"]) != 0:
        raise ValueError("Results draft guard failed: recommendations are present")

    methods = f"""# Thesis chapter draft — Methods

> Draft generated from the validated Path C v0.31 outputs. Adapt numbering and citation style to the final thesis template. Counts are pipeline-derived and must remain linked to the cited repository outputs.

## 1. Research design

The study followed a sequential, feasibility-gated Business Analytics design. The initial objective was to estimate whether Magic Pass participation affected hotel overnight stays and, if identification proved credible, to study heterogeneous effects and transfer the resulting evidence to non-member ski destinations. The design did not assume that a particular causal or machine-learning method would be suitable. Instead, six checkpoints progressively assessed the existing data, treatment definition, panel coverage, causal identification, machine-learning feasibility and final decision-support architecture.

Checkpoints 1–3 constructed and audited the empirical foundation. Checkpoints 4–5 treated causal inference and heterogeneous-effect modelling as hypotheses to be accepted only if treatment, outcome, donor and temporal-support conditions were met. Because those gates failed, Checkpoint 6 selected Path C: an exploratory structural-analogue dashboard in which descriptive opportunity, vulnerability, tourism context, accessibility, competition and uncertainty remain separate. This fallback was precluded from producing treatment-effect predictions, a composite score or a candidate ranking.

## 2. Units of analysis and entity resolution

The supplied directory contained **{feasibility['resort_listings_total']} resort listings**. These listings were not assumed to represent independent ski destinations because several names can refer to components of one domain and one preserved lift cluster can contain multiple directory rows. The existing geographic clustering was therefore audited rather than rebuilt. It contains **{feasibility['lift_clusters_total']} lift clusters**, of which **{feasibility['lift_clusters_linked_to_resort_listings']}** link to at least one supplied listing. Stable `resort_id`, `cluster_id`, `destination_unit_id` and BFS municipality identifiers were retained throughout.

Magic Pass evidence was resolved from official dated publications. Candidate links were reviewed conservatively and ambiguous labels were not forced into one-to-one matches. Eighteen candidate-linked entry components were collapsed into **{panel['reviewed_destination_units']} reviewed destination units**. **{panel['destination_units_in_outcome_panel']}** had an explicit hotel-outcome scope; three composite destinations were excluded because the available municipality panel covered only part of their geography. Membership continuity and winter/summer modality were stored separately. All {continuity['reviewed_destination_units']} reviewed units have documented active seasons, while modality evidence exists for {continuity['active_unit_seasons_with_individual_modality_evidence']} active unit-seasons.

## 3. Hotel outcome and capacity panel

The main outcome was monthly hotel overnight stays at municipality level. The processed panel contains **{feasibility['hotel_capacity_municipality_month_rows']} municipality-month rows** for **{feasibility['hotel_municipalities_total']} municipalities**, with **{feasibility['hotel_observed_month_rows']} observed overnight-stay cells** between January 2013 and March 2026. Suppressed source values remained missing and were not imputed. Establishments, rooms and beds were retained as supply-side context. For multi-municipality destination units, count variables were summed only when every municipality in the reviewed scope was observed; published occupancy rates were not averaged across municipalities.

The reviewed destination panel contains **{panel['destination_month_rows']} destination-month rows**, including **{panel['observed_destination_month_outcomes']} observed outcomes** and **{panel['complete_destination_month_capacity_rows']} complete capacity rows**. Entry seasons provided diagnostic anchors rather than exact treatment dates. The carry-forward membership rule was explicitly treated as a diagnostic coding assumption, not causal exposure validation.

## 4. Climate, snow and temporal context

Snow conditions were represented first through the nearest eligible long-running SLF station, retaining distance, elevation difference, winter coverage and proxy quality. A next-nearest-station sensitivity test was run for all **{snow_station['reviewed_resort_components']} reviewed components**. It yielded {snow_station['agreement_counts']['high']} high, {snow_station['agreement_counts']['moderate']} moderate and {snow_station['agreement_counts']['low']} low comparisons, with a median winter-depth correlation of **{float(snow_station['median_winter_mean_depth_correlation']):.3f}**. A second sensitivity used the SPASS 1 km modelled snow product at resort and station locations. All **{snow_grid['component_winter_rows']} component-winter rows** were complete, but resort-centred disagreement remained material.

Regional temperature and precipitation context used eligible SwissMetNet stations and calendar-month anomalies. The next-nearest-station comparison produced median component correlations of **{float(weather_station['median_component_temperature_anomaly_correlation']):.3f}** for temperature and **{float(weather_station['median_component_precipitation_anomaly_correlation']):.3f}** for precipitation. Official 1 km TabsM/RhiresM grids supplied an additional spatial sensitivity. These products were treated as regional proxies, not direct piste measurements or automatically valid causal covariates. Deterministic month, winter/summer, peak-season, Easter and broad COVID-sensitivity indicators were generated for the full panel.

## 5. Accessibility, tourism and competitive context

Accessibility was deliberately measured in several non-equivalent ways: straight-line population context, cross-border population grids, modelled NPVM travel time, distance to official passenger stops and national-road axes, and scheduled public-transport journeys. The GTFS calculation sampled five outbound departure times from 08:00–10:00 and seven return times from 15:00–18:00 on one winter weekday and one Saturday. It produced **{public_transport['journey_samples']} journey samples** for **{public_transport['destination_municipality_pairs']} destination–municipality pairs**. The measure is a winter-2026 timetable snapshot; historical stability was not assumed.

Tourism dependence was reported for the reviewed outcome scopes and, separately, for municipalities containing candidate component points. Candidate rules based on 0, 5 and 10 km municipality buffers were evaluated against the independently reviewed complete destination scopes. These rules were sensitivity analyses rather than definitions of a visitor catchment.

Competitive context combined three current multi-area-pass rosters with dated positive-presence evidence for Top4, Meilenweiss, Schneepass Zentralschweiz, TopCard and SnowPass Graubünden. The historical table contains **{historical_pass['area_season_rows']} area-season rows** and **{historical_pass['documented_listing_season_links']} positive listing-season links**. A missing link means only that no reviewed positive evidence was found; it does not establish historical absence.

## 6. Causal feasibility assessment

The causal screen required an explicit destination scope, documented membership continuity, sufficient pre/post outcomes, historically credible non-treated donors, limited spillover risk and no major contemporaneous donor-specific shock. This is stricter than selecting an available estimator: staggered Difference-in-Differences still requires a credible parallel-trends comparison and careful treatment of heterogeneous timing and effects (Callaway and Sant'Anna, 2021; Sun and Abraham, 2021), while connected ski markets make interference a substantive threat rather than a technical footnote (Hudgens and Halloran, 2008). Seven treatments supported a 36-month descriptive pre-period screen. Among **{donor_pretrend['provisional_pairs_screened']} provisional pairs**, {donor_pretrend['shortlisted_pairs_for_manual_review']} top-five pairs were shortlisted for manual review. Network proximity deprioritised **{donor_shocks['deprioritised_within_30km']} pairs within 30 km** and **{donor_shocks['deprioritised_30_to_50km']} pairs between 30 and 50 km**. The seven pairs beyond 50 km were all excluded because official evidence documented a contemporaneous donor-specific tourism, pricing, access or infrastructure shock. Consequently, zero treatments and zero controls were approved for causal estimation.

## 7. Path C structural segmentation and analogues

Path C used only three structural directory fields: median published top altitude, median published ski-area kilometres and median published lift count. Ski area and lift count were log-transformed before standardisation. Geography, membership, hotel outcomes, tourism dependence and snow vulnerability were excluded from the similarity model so that labels, outcomes and strategic dimensions did not define structural resemblance.

Deterministic k-means solutions from k=2 to k=8 were compared using average silhouette width (Rousseeuw, 1987), minimum segment size and 80% subsample adjusted Rand stability, whose chance-corrected partition-comparison foundation follows Hubert and Arabie (1985). The selected **k={path_c['selected_k']}** solution had silhouette **{float(path_c['selected_silhouette']):.3f}**, median bootstrap ARI **{float(path_c['selected_bootstrap_ari_median']):.3f}** and 10th-percentile ARI **{float(path_c['selected_bootstrap_ari_p10']):.3f}**. Apparent non-member candidates were compared with structurally complete current Magic Pass clusters and with eight reviewed treated reference units. The resulting analogue signal is the median unadjusted post-versus-pre diagnostic of the three nearest reviewed treated references; it is not predicted uplift.

Within-cluster minimum, median and maximum aggregation rules were then compared. All selected k=2, but assignment and nearest-analogue stability varied. Candidate-level stability flags were retained rather than selecting the most favourable aggregation.

## 8. Decision framework and reproducibility

The final dashboard assigns **{readiness['feature_groups']} feature groups** exactly once across seven decision dimensions. Candidate coverage and permitted use are separate fields. Only structural similarity is authorised for exploratory matching. Zero groups are approved as pre-treatment predictors, causal covariates, recommendation inputs or composite-score inputs. Candidate rows remain sorted by stable cluster ID.

All source files are checksum-audited, external evidence is registered in the provenance table, and analytical variables are described in the data dictionary. The offline pipeline regenerates processed tables, diagnostics, reports, figures and automated tests from the project root. Raw inputs are never overwritten.
"""

    results = f"""# Thesis chapter draft — Results

> Draft generated from the validated Path C v0.31 outputs. This chapter reports feasibility and descriptive evidence; it does not report a Magic Pass treatment effect.

## 1. Data foundation and treatment panel

The audit retained **{feasibility['resort_listings_total']} directory listings**, **{feasibility['lift_clusters_total']} preserved lift clusters** and **{feasibility['hotel_municipalities_total']} hotel municipalities**. Of the lift clusters, {feasibility['lift_clusters_linked_to_resort_listings']} were linked to at least one directory listing and {path_c['segmentation_eligible_clusters']} had complete structural fields for segmentation. The hotel panel covered January 2013 to March 2026 and contained {feasibility['hotel_observed_month_rows']} observed monthly overnight-stay values.

Official Magic Pass material yielded **{feasibility['documented_base_entry_events']} documented base-entry events**. After conservative entity resolution and destination-scope review, {panel['reviewed_destination_units']} destination units were retained and {panel['destination_units_in_outcome_panel']} entered the hotel panel. All reviewed units had documented active-season continuity, but only {continuity['fully_documented_panel_units_with_24_pre_and_post_months']} panel units combined that evidence with at least 24 observed pre and 24 active-post months. No destination was approved as a causal treatment unit.

## 2. Causal and machine-learning feasibility

The donor screen initially considered {feasibility['treatment_donor_pairs_screened']} treatment–municipality combinations. Mechanical distance and coverage rules retained {feasibility['provisional_donor_pairs_30km_36pre']} pairs under the 30 km screen and {feasibility['provisional_donor_pairs_50km_36pre']} under the 50 km sensitivity. The descriptive pre-trend stage ranked {donor_pretrend['provisional_pairs_screened']} pairs and retained {donor_pretrend['shortlisted_pairs_for_manual_review']} for manual review.

The network audit showed that {donor_network['shortlisted_pairs_within_50km_resolved_magic']} of the 35 shortlisted pairs lay within 50 km of another resolved Magic Pass point. Of the seven remote pairs, every donor had an independently documented contemporaneous local shock. No shortlisted donor survived the combined proximity and external-shock review, leaving **{donor_shocks['remaining_deep_audit_pairs']} deep-audit pairs, {donor_shocks['causal_controls_approved']} approved controls and {panel['causal_treatment_units_approved']} approved causal treatments**.

Checkpoint 4 therefore rejected causal estimation. Checkpoint 5 also rejected causal forests, meta-learners and neural networks because there was no defensible causal target and the effective treated sample was at most 14 reviewed units, only seven with the required 24/24 continuity and outcome coverage. No CATE, uplift or treatment-effect prediction was produced.

## 3. Structural segmentation and support

The selected two-segment structural solution achieved silhouette **{float(path_c['selected_silhouette']):.3f}** and high subsample stability (median ARI **{float(path_c['selected_bootstrap_ari_median']):.3f}**, 10th percentile **{float(path_c['selected_bootstrap_ari_p10']):.3f}**). Among **{path_c['apparent_nonmember_candidates_scored']} apparent candidates**, {path_c['candidate_good_treated_support']} had good support relative to the reviewed treated references, {path_c['candidate_moderate_treated_extrapolation']} were moderate extrapolations and {path_c['candidate_strong_treated_extrapolation']} were strong extrapolations.

Sensitivity to within-cluster aggregation was substantial. Although minimum, median and maximum rules all selected k=2, segment ARI relative to the median solution fell to **{float(aggregation['minimum_rule_segment_ari']):.3f}** under minimum aggregation and **{float(aggregation['maximum_rule_segment_ari']):.3f}** under maximum aggregation. Only **{aggregation['candidates_fully_stable_across_aggregation_rules']} of 104 candidates** preserved every recorded segment, nearest-analogue and treated-support criterion. Seventy-one retained the same closest reviewed treated analogue and 60 retained the same treated-reference support category. These results justify reporting candidate-specific stability rather than a single league table.

## 4. Tourism-scope evidence

Component-point municipalities exactly reproduced 10 of 11 reviewed outcome municipality sets, but seven of those matches were core-municipality proxies defined from the same component logic. Among the four independently reviewed complete municipal scopes, only three matched exactly and component points recovered four of five municipalities. Meiringen-Hasliberg supplied the principal mismatch because the resort point lies in Hasliberg while the reviewed outcome scope also includes Meiringen.

The radius sensitivity confirmed a precision–recall trade-off. Point containment recovered four of five links with no extras. A 5 km rule recovered all five but added **{scope['complete_observed_scope_validation_by_radius_km']['5']['extra_municipality_links']} municipalities**, and a 10 km rule added **{scope['complete_observed_scope_validation_by_radius_km']['10']['extra_municipality_links']}**. Although {scope['candidates_with_any_observed_hesta_ratio']} candidates obtained an observed HESTA ratio under at least one rule, only {scope['candidates_with_complete_hotel_context_for_any_rule']} had complete hotel context under any rule and zero catchments were validated.

## 5. Climate and snow robustness

The alternative SLF-station test classified 11 of 15 component comparisons as high or moderate and four as low. Median winter-depth correlation was **{float(snow_station['median_winter_mean_depth_correlation']):.3f}**, while the median relative absolute depth difference was **{100 * float(snow_station['median_relative_mean_absolute_depth_difference']):.1f}%**. SPASS comparison at station locations was uniformly high or moderate, but resort-centred comparison was low for {snow_grid['component_local_3x3_agreement_counts']['low']} of 15 components. This pattern identifies station-to-resort location and elevation mismatch as the principal limitation of the snow proxy.

Weather anomalies were more robust to station choice. All 15 alternative-station comparisons were high or moderate; median temperature- and precipitation-anomaly correlations were **{float(weather_station['median_component_temperature_anomaly_correlation']):.3f}** and **{float(weather_station['median_component_precipitation_anomaly_correlation']):.3f}**. The official 1 km grids produced median correlations of **{float(weather_grid['median_component_temperature_anomaly_correlation']):.3f}** and **{float(weather_grid['median_component_precipitation_anomaly_correlation']):.3f}**, although two component comparisons were low. None of these sensitivities converted a climate field into an approved causal covariate.

## 6. Accessibility and transport

The scheduled GTFS analysis produced **{public_transport['journey_samples']} samples**, of which {public_transport['feasible_journey_samples']} were feasible under the six-vehicle and eight-hour limits. Across {public_transport['destination_municipality_pairs']} destination–municipality pairs, {public_transport['pairs_complete_all_samples']} were feasible at every sampled time. Median outbound and return generalized times were **{float(public_transport['median_pair_outbound_mean_generalized_minutes']):.1f}** and **{float(public_transport['median_pair_return_mean_generalized_minutes']):.1f} minutes**.

Ten destinations supported a bidirectional distance/time rank correlation. The median correlation was **{float(distance_transport['median_destination_distance_round_trip_rank_correlation_available_pairs']):.3f}**, ranging from {float(distance_transport['minimum_destination_distance_round_trip_rank_correlation_available_pairs']):.3f} to {float(distance_transport['maximum_destination_distance_round_trip_rank_correlation_available_pairs']):.3f}. At the 0.25 rank-gap threshold, {distance_transport['materially_worse_transit_than_distance_rank_pairs']} pairs had worse transit access than straight-line distance suggested and {distance_transport['materially_better_transit_than_distance_rank_pairs']} had better access. Distance is therefore informative but not interchangeable with scheduled travel time.

## 7. Competition and network context

The historical multi-area-pass register covered five products over 21 product-seasons. It contained **{historical_pass['area_season_rows']} area-season rows** and **{historical_pass['documented_listing_season_links']} positive listing-season links**, reaching {historical_pass['unique_supplied_listings_with_documented_link']} listings and {historical_pass['clusters_with_documented_link']} lift clusters. Thirty candidates had at least one documented historical link; 19 had every cluster listing linked in at least one reviewed product-season and 11 were partial mixed-listing clusters. SnowPass remained winter-only, and product-level summer statements were not widened to individual areas.

This reconstruction improved positive-presence coverage but did not produce a full historical market panel. Zero non-links were verified as market absence, so historical competition remained descriptive context rather than a treatment, predictor or ranking feature.

## 8. Final decision framework

Checkpoint 6 assigned {readiness['feature_groups']} evidence groups to seven dimensions. Thirteen groups had complete candidate coverage, two were partial and four had no candidate feature. Only structural similarity was approved for exploratory use. **Zero groups** were approved as pre-treatment predictors, causal covariates, recommendation inputs or composite-score inputs.

The final dashboard contains {decision['candidate_clusters']} candidate clusters. It produces **{decision['predicted_uplift_values']} predicted-uplift values, {decision['recommendations_issued']} recommendations, {decision['composite_scores']} composite scores and {decision['causal_interpretation_approvals']} causal approvals**. No candidate meets the complete Opportunity × Strategic Need gate. The empirical result is therefore a qualified multidimensional evidence system, not a ranked expansion recommendation.
"""

    discussion = f"""# Thesis chapter draft — Discussion and limitations

> Draft generated from the validated Path C v0.31 outputs. It interprets the research design and findings without converting descriptive evidence into causal or managerial certainty.

## 1. Main interpretation

The project demonstrates that the available Swiss ski-destination data are rich enough to support a reproducible, multidimensional descriptive decision system, but not a credible estimate of the causal effect of Magic Pass participation. This distinction is the central finding. The absence of a causal estimate is not a computational failure: it follows from explicit evidence gates that exposed unresolved treatment intensity, destination scope, donor contamination, local shocks, spillovers and insufficient effective sample size.

Path C preserves analytical usefulness after that rejection. Structural segmentation, analogue distance, snow vulnerability, tourism context, accessibility and competition can inform structured investigation when kept separate. The architecture is particularly useful for identifying where evidence is strong, where a candidate is an extrapolation and which additional information would be required before a strategic decision. It is not suitable for estimating expected overnight-stay gains or ranking destinations for admission.

## 2. Implications for causal inference and machine learning

The donor audit illustrates why a superficially adequate panel can still be unsuitable for causal inference. Seven treatments had sufficient continuity and 24/24 outcome coverage, and 315 pairs passed the descriptive pre-trend data screen. Yet 28 of the 35 shortlisted pairs were within 50 km of another resolved Magic Pass point, and all seven remote pairs had contemporaneous donor-specific shocks. Promoting one of these pairs would have replaced an explicit identification failure with an untestable assumption.

The same logic applies to causal machine learning. Causal forests are developed under explicit causal assumptions including unconfoundedness (Wager and Athey, 2018), while meta-learners organise flexible supervised models around a conditional treatment-effect target rather than identifying that target automatically (Künzel et al., 2019). Neither can compensate for an invalid treatment/control design, and 14 reviewed destinations are not an adequate effective sample for stable heterogeneous-effect estimation. Rejecting complex models therefore improves scientific credibility. The contribution shifts from algorithmic novelty to disciplined integration, scope control and uncertainty communication.

## 3. Managerial usefulness of Path C

The dashboard can support a staged managerial conversation. Structural comparability identifies whether a candidate resembles existing Magic Pass clusters. The treated-reference support flag shows whether analogue interpretation is interpolation or extrapolation. Snow, access, tourism and competition layers identify distinct strategic considerations. The evidence-gap dimension prevents an attractive structural profile from being mistaken for a complete business case.

However, candidate rows must remain examples for due diligence rather than recommendations. Only {aggregation['candidates_fully_stable_across_aggregation_rules']} of 104 candidates were stable across every aggregation check, {path_c['candidate_strong_treated_extrapolation']} were strong extrapolations and only {scope['candidates_with_complete_hotel_context_for_any_rule']} had complete hotel context under any tested scope rule. A single weighted score would conceal these non-equivalent uncertainties and imply value judgements not established by the data.

## 4. Measurement and scope limitations

### 4.1 Resort and destination entities

The supplied directory is a listing system rather than a certified inventory of independent commercial ski domains. The preserved lift clusters reduce duplication but do not solve ownership, joint-ticketing or destination-boundary questions. Fifty-three linked clusters contain multiple listings, and within-cluster structural aggregation changes many analogue results. Destination-level conclusions should therefore be phrased in terms of the reviewed units or preserved clusters used by the analysis.

### 4.2 Hotel-outcome geography

Municipality hotel data do not automatically represent a ski destination's visitor catchment. Seven reviewed outcome scopes are core-municipality proxies, and the radius experiment shows that improving recall rapidly adds unrelated municipalities. Five kilometres recovered the one omitted reviewed link but added {scope['complete_observed_scope_validation_by_radius_km']['5']['extra_municipality_links']} others. Candidate tourism dependence must remain qualified point-container or radius-sensitivity context until external destination scopes are available.

### 4.3 Treatment definition and intensity

Official publications support membership timing and continuity for the reviewed units, but treatment is not homogeneous. Winter-only and winter-plus-summer access differ, as do prices, supplements, product rules, local marketing and capacity responses. Entry is known mainly by season rather than exact activation date. The design therefore cannot assume a single binary treatment with constant intensity.

### 4.4 Donors, interference and common shocks

Ski destinations operate in connected regional markets. Nearby resorts may experience diversion, complementarity or shared marketing effects, violating no-interference assumptions. Remote destinations are not automatically credible controls: every remote shortlisted donor had a documented concurrent shock. The COVID sensitivity interval, weather, capacity changes, infrastructure investment and flexible pricing further complicate parallel-trend claims.

### 4.5 Climate and snow proxies

SLF stations are external point measurements and can differ materially from resort elevations. The resort-centred SPASS comparison was low for {snow_grid['component_local_3x3_agreement_counts']['low']} of 15 components, even though station-location agreement was much stronger. SPASS and SLF are also not independent because the gridded product is modelled and quantile-mapped to an SLF snow target. SwissMetNet and official weather grids describe regional conditions rather than piste microclimates, snowmaking or operational decisions. Climate fields are appropriate for qualified vulnerability context, not causal adjustment without further design work.

### 4.6 Accessibility

The GTFS analysis improves on straight-line distance by using departure-time-specific scheduled journeys, but it represents one weekday and one Saturday in winter 2026. It does not measure historical service at treatment entry, real-time reliability, fares, crowding, car access, hotel location or final walking time. Six destination nodes are village/local-centre proxies. The median distance/time rank correlation of {float(distance_transport['median_destination_distance_round_trip_rank_correlation_available_pairs']):.3f} confirms that distance is informative, while the {distance_transport['materially_worse_transit_than_distance_rank_pairs']} materially worse-transit pairs show why it is insufficient.

### 4.7 Competing passes

The historical register records positive presence, not a complete market census. Evidence scope varies by product and season, benefit tiers are not equivalent, and detailed small-lift boundaries remain incomplete. A candidate without a documented link cannot be called historically unserved by multi-area passes. Competition variables therefore remain contextual and cannot establish treatment contrast or market whitespace.

### 4.8 Temporal leakage and transportability

Most candidate-side structural, accessibility, tourism and network layers are current or undated snapshots. They may encode post-treatment investment or market evolution and are not approved as pre-treatment predictors. The eight reviewed treated analogue references are too few to establish that structural proximity transports hotel-demand responses. The analogue signal must remain an unadjusted descriptive comparison.

## 5. Strengths

The study nevertheless has several strengths. It preserves raw sources and stable identifiers, separates resort assignment from municipality exposure mapping, uses explicit positive-evidence rules, records source checksums and provenance, and encodes analytical permissions as executable flags. Sensitivity tests expose dependence on station choice, grid location, within-cluster aggregation, geographic distance rule and candidate municipality scope. Negative results and failed collection attempts remain documented rather than silently removed.

The seven-dimension architecture is also a substantive Business Analytics contribution. It prevents structural attractiveness, vulnerability, accessibility and data quality from collapsing into one opaque score. The resulting system is auditable and communicates why a candidate cannot yet receive a defensible recommendation.

## 6. Prioritised future research

Future work should follow the identification bottlenecks rather than add marginal variables indiscriminately:

1. define destination exposure using externally validated tourism scopes and treatment intensity;
2. redesign the donor strategy, potentially expanding beyond the supplied ski-resort municipality universe while retaining interference and shock audits;
3. obtain historical transport and infrastructure measures only if they are needed as pre-treatment variables;
4. collect operational snowmaking, investment and lift-capacity histories if climate adaptation is part of the causal question;
5. expand the number of credibly treated destination units before reconsidering heterogeneous-effect models;
6. validate decision weights with Magic Pass stakeholders before any composite business score is introduced.

Detailed historical SnowPass schedules, additional regional-pass rosters and walking-access refinements are secondary unless a specific claim depends on them. They should not displace the higher-priority treatment, scope and donor problems.

## 7. Conclusion

Under the available design, the project should be described as **exploratory and decision-support oriented**, not causal or predictive. The evidence supports structured comparison of 104 apparent candidates and transparent reporting of opportunity, vulnerability and uncertainty. It does not support expected-uplift estimates, a causal interpretation, or a ranked recommendation list. That boundary is a core result of the thesis rather than a caveat appended after modelling.
"""

    outputs = {
        "reports/43_THESIS_METHODS_DRAFT.md": methods,
        "reports/44_THESIS_RESULTS_DRAFT.md": results,
        "reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md": discussion,
    }
    for relative_path, content in outputs.items():
        (ROOT / relative_path).write_text(content, encoding="utf-8")

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "chapter_drafts": list(outputs),
        "approved_causal_treatments": int(panel["causal_treatment_units_approved"]),
        "approved_causal_controls": int(donor_shocks["causal_controls_approved"]),
        "predicted_uplift_values": int(decision["predicted_uplift_values"]),
        "recommendations_issued": int(decision["recommendations_issued"]),
        "composite_scores": int(decision["composite_scores"]),
        "causal_interpretation_approvals": int(
            decision["causal_interpretation_approvals"]
        ),
        "interpretation": "thesis_ready_drafts_from_validated_path_c_outputs_not_final_citations_or_causal_claims",
    }
    (ROOT / "reports/thesis_chapter_drafts_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
