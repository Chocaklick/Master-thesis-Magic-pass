"""Register accessibility-expansion sources and analytical variables."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "metadata" / "data_sources_master.csv"
DICTIONARY_PATH = ROOT / "metadata" / "data_dictionary.csv"
EVIDENCE_CONFIG_PATH = ROOT / "config" / "evidence_sources.json"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
NEW_TREATED_REVIEW_SOURCE_IDS = {
    "ANNIVIERS_TOURISM_TAX_FLYER_2019",
    "BULLE_TOURISM_POSTULATE_2019",
    "FRIBOURG_PREALPS_2030_REPORT_2019",
    "FRIBOURG_YOUTH_HOSTEL_REPORT_2019",
    "LA_CHAUX_DE_FONDS_MANAGEMENT_REPORT_2019",
    "LEYSIN_CHAIRLIFT_PREAVIS_2017",
    "LEYSIN_SNOWMAKING_PREAVIS_2018",
    "OLLON_VILLARS_BATHS_PREAVIS_2017",
    "ORMONT_DESSUS_MEILLERET_PREAVIS_2018",
    "ORMONT_DESSUS_TVGD_LOAN_PREAVIS_2017",
    "PLAFFEIEN_TOURISM_AG_MINUTES_2019",
    "SAIGNELEGIER_INFO_JUNE_2019",
}
NEW_CONTROL_REVIEW_SOURCE_IDS = {
    "EMMEN_ANNUAL_REPORT_2019",
    "LENZBURG_BARRACUDA_OPENING_2017",
    "LENZBURG_BARRACUDA_OPERATOR_CURRENT",
    "MAIENFELD_HEIDIDORF_GRANT_2017",
    "RORSCHACHERBERG_ANNUAL_REPORT_2019",
    "SURSEE_FOCUS_HOTEL_HISTORY",
    "VITZNAU_TOURISM_PROJECTS_RETROSPECTIVE_2021",
    "WALENSTADT_HOTEL_LOEWEN_RENOVATION_2018",
}
NEW_REMAINING_CONTROL_REVIEW_SOURCE_IDS = {
    "AARAU_HOTELLERIE_RESPONSE_2022",
    "AMDEN_ACCOUNTS_2019",
    "APPENZELL_TOURISM_QUALITY_OFFENSIVE_2017",
    "ARBON_METROPOL_CLOSURE_2017",
    "DUEBENDORF_ANNUAL_REPORT_2016",
    "EINSIEDELN_DESTINATION_DECISION_2017",
    "EMMETTEN_ACCOUNTS_2019",
    "FRAUENFELD_CITY_CENTRE_PROGRAMME_2019",
    "FREIENBACH_ACCOUNTS_2019",
    "GAIS_CANTONAL_TOURISM_PROGRAMME_2020_2023",
    "KREUZLINGEN_KULT_X_RETROSPECTIVE",
    "LIESTAL_ANNUAL_REPORT_2018",
    "PRATTELN_ANNUAL_REPORT_2019",
    "SARNEN_HOTEL_KRONE_RENOVATION_2019",
    "SCHAFFHAUSEN_HOTEL_TANNE_REOPENING_2019",
    "SIGRISWIL_TOURIST_TAX_2019",
    "THUN_TOURIST_TAX_CONTEXT_2017",
    "WINTERTHUR_HOUSE_OF_WINTERTHUR_2017",
}
SOURCE_COLUMNS = [
    "source_id", "variable_name", "variable_description", "source_organisation",
    "source_dataset_name", "source_page_url", "direct_download_url", "api_endpoint",
    "api_parameters", "wms_layer", "geocat_metadata_url", "retrieval_method",
    "retrieval_date", "original_file_name", "local_raw_file", "processed_file",
    "geographic_level", "temporal_resolution", "temporal_start", "temporal_end",
    "unit", "license", "access_conditions", "transformation_applied", "quality_notes",
    "confidence_level", "manual_verification", "notes",
]
DICTIONARY_COLUMNS = [
    "variable", "table", "description", "unit", "data_type", "geographic_level",
    "temporal_level", "source_id", "raw_or_derived", "formula", "causal_role",
    "missing_share", "notes",
]


TABLES = {
    "accessibility_station_groups": (
        ROOT / "data_processed" / "accessibility_station_groups.csv",
        "DERIVED_ACCESSIBILITY_STATION_GROUPS", "station group", "review snapshot"),
    "accessibility_station_group_events": (
        ROOT / "data_processed" / "accessibility_station_group_events.csv",
        "DERIVED_ACCESSIBILITY_STATION_GROUP_EVENTS", "station group entry event", "event month"),
    "accessibility_station_access_points": (
        ROOT / "data_processed" / "accessibility_station_access_points.csv",
        "DERIVED_ACCESSIBILITY_STATION_GROUPS", "station access point", "current/historical reference snapshot"),
    "accessibility_station_access_nodes": (
        ROOT / "reports" / "accessibility_station_access_nodes.csv",
        "DERIVED_ACCESSIBILITY_STATION_GROUPS", "station access point", "winter-2026 reference"),
    "accessibility_station_group_journey_samples": (
        ROOT / "data_processed" / "accessibility_station_group_journey_samples.csv",
        "DERIVED_ACCESSIBILITY_STATION_GROUP_JOURNEYS", "station group by municipality request", "sampled winter-2026 time"),
    "accessibility_station_group_journey_context": (
        ROOT / "data_processed" / "accessibility_station_group_journey_context.csv",
        "DERIVED_ACCESSIBILITY_STATION_GROUP_JOURNEYS", "station group by hotel municipality", "winter-2026 reference"),
    "accessibility_municipality_month_exposure": (
        ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv",
        "DERIVED_ACCESSIBILITY_MUNICIPALITY_EXPOSURE", "hotel municipality series", "monthly"),
    "accessibility_station_group_event_window": (
        ROOT / "data_processed" / "accessibility_station_group_event_window.csv",
        "DERIVED_ACCESSIBILITY_MUNICIPALITY_EXPOSURE", "station group by hotel municipality", "event month -36 to +36"),
    "accessibility_station_group_pair_diagnostic": (
        ROOT / "data_processed" / "accessibility_station_group_pair_diagnostic.csv",
        "DERIVED_ACCESSIBILITY_MUNICIPALITY_EXPOSURE", "station group by hotel municipality", "adjacent 24-month windows"),
    "accessibility_station_group_feasibility": (
        ROOT / "reports" / "accessibility_station_group_feasibility.csv",
        "DERIVED_ACCESSIBILITY_MUNICIPALITY_EXPOSURE", "station group", "review snapshot"),
    "accessibility_identification_pair_audit": (
        ROOT / "data_processed" / "accessibility_identification_pair_audit.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "station group by hotel municipality", "identification review snapshot"),
    "accessibility_identification_group_audit": (
        ROOT / "reports" / "accessibility_identification_group_audit.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "station group", "identification review snapshot"),
    "accessibility_identification_municipality_audit": (
        ROOT / "reports" / "accessibility_identification_municipality_audit.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "hotel municipality series", "identification review snapshot"),
    "accessibility_identification_cohort_audit": (
        ROOT / "reports" / "accessibility_identification_cohort_audit.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "station-group entry cohort", "entry cohort and adjacent 24-month window"),
    "accessibility_identification_overlap_audit": (
        ROOT / "reports" / "accessibility_identification_overlap_audit.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "pair of station groups", "common entry month"),
    "accessibility_first_exposure_audit": (
        ROOT / "reports" / "accessibility_first_exposure_audit.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "hotel municipality series", "first accessible entry and adjacent 24-month window"),
    "accessibility_first_exposure_pretrend_pairs": (
        ROOT / "data_processed" / "accessibility_first_exposure_pretrend_pairs.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "treated municipality by provisional comparison municipality", "36 pre-anchor months"),
    "accessibility_first_exposure_pretrend_shortlist": (
        ROOT / "reports" / "accessibility_first_exposure_pretrend_shortlist.csv",
        "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", "treated municipality by provisional comparison municipality", "36 pre-anchor months"),
    "accessibility_historical_gtfs_2018_manual_worklist": (
        ROOT / "reports" / "accessibility_historical_gtfs_2018_manual_worklist.csv",
        "SKI_GTFS_TIMETABLE_2018_WINTER_20180207", "priority municipality by founding station group", "first Magic Pass winter 2017/2018"),
    "accessibility_historical_gtfs_2018_stop_audit": (
        ROOT / "reports" / "accessibility_historical_gtfs_2018_stop_audit.csv",
        "SKI_GTFS_TIMETABLE_2018_WINTER_20180207", "historical route endpoint", "winter-2018 timetable snapshot"),
    "accessibility_historical_gtfs_2018_journey_samples": (
        ROOT / "data_processed" / "accessibility_historical_gtfs_2018_journey_samples.csv",
        "SKI_GTFS_TIMETABLE_2018_WINTER_20180207", "priority municipality by founding station-group request", "sampled winter-2018 time"),
    "accessibility_historical_gtfs_2018_journey_context": (
        ROOT / "data_processed" / "accessibility_historical_gtfs_2018_journey_context.csv",
        "SKI_GTFS_TIMETABLE_2018_WINTER_20180207", "priority municipality by founding station group", "winter-2018 strict transfer scenario"),
    "accessibility_historical_gtfs_2018_municipality_validation": (
        ROOT / "reports" / "accessibility_historical_gtfs_2018_municipality_validation.csv",
        "SKI_GTFS_TIMETABLE_2018_WINTER_20180207", "first-exposure hotel municipality", "winter-2018 strict transfer scenario"),
    "accessibility_historical_gtfs_2018_proximity_journey_samples": (
        ROOT / "data_processed" / "accessibility_historical_gtfs_2018_proximity_journey_samples.csv",
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION", "priority municipality by founding station-group request", "sampled winter-2018 proximity-transfer sensitivity"),
    "accessibility_historical_gtfs_2018_proximity_journey_context": (
        ROOT / "data_processed" / "accessibility_historical_gtfs_2018_proximity_journey_context.csv",
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION", "priority municipality by founding station group", "winter-2018 proximity-transfer sensitivity"),
    "accessibility_historical_gtfs_2018_proximity_municipality_validation": (
        ROOT / "reports" / "accessibility_historical_gtfs_2018_proximity_municipality_validation.csv",
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION", "first-exposure hotel municipality", "winter-2018 proximity-transfer sensitivity"),
    "accessibility_historical_gtfs_2018_current_transfer_journey_samples": (
        ROOT / "data_processed" / "accessibility_historical_gtfs_2018_current_transfer_journey_samples.csv",
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION", "priority municipality by founding station-group request", "sampled winter-2018 current-transfer-topology sensitivity"),
    "accessibility_historical_gtfs_2018_current_transfer_journey_context": (
        ROOT / "data_processed" / "accessibility_historical_gtfs_2018_current_transfer_journey_context.csv",
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION", "priority municipality by founding station group", "winter-2018 current-transfer-topology sensitivity"),
    "accessibility_historical_gtfs_2018_current_transfer_municipality_validation": (
        ROOT / "reports" / "accessibility_historical_gtfs_2018_current_transfer_municipality_validation.csv",
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION", "first-exposure hotel municipality", "winter-2018 current-transfer-topology sensitivity"),
    "accessibility_historically_screened_pretrend_shortlist": (
        ROOT / "reports" / "accessibility_historically_screened_pretrend_shortlist.csv",
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION", "historically retained treated municipality by provisional comparison municipality", "36 pre-anchor months and winter-2018 access screen"),
    "accessibility_comparison_internal_risk_screen": (
        ROOT / "data_processed" / "accessibility_comparison_internal_risk_screen.csv",
        "DERIVED_ACCESSIBILITY_COMPARISON_INTERNAL_RISK_SCREEN", "historically retained treated municipality by provisional comparison municipality", "2015-11 to 2019-10 review window"),
    "accessibility_comparison_control_internal_diagnostics": (
        ROOT / "reports" / "accessibility_comparison_control_internal_diagnostics.csv",
        "DERIVED_ACCESSIBILITY_COMPARISON_INTERNAL_RISK_SCREEN", "provisional comparison municipality", "2015-11 to 2019-10 review window"),
    "accessibility_comparison_external_review_worklist": (
        ROOT / "reports" / "accessibility_comparison_external_review_worklist.csv",
        "DERIVED_ACCESSIBILITY_COMPARISON_INTERNAL_RISK_SCREEN", "treated or provisional comparison municipality", "external-review checkpoint"),
    "accessibility_treated_external_shock_evidence": (
        ROOT / "reports" / "accessibility_treated_external_shock_evidence.csv",
        "DERIVED_ACCESSIBILITY_TREATED_EXTERNAL_SHOCK_REVIEW", "treated hotel municipality", "2015-11 to 2019-10 external-review window"),
    "accessibility_comparison_treated_external_risk_screen": (
        ROOT / "data_processed" / "accessibility_comparison_treated_external_risk_screen.csv",
        "DERIVED_ACCESSIBILITY_TREATED_EXTERNAL_SHOCK_REVIEW", "treated municipality by provisional comparison municipality", "November 2017 anchor and adjacent 24-month windows"),
    "accessibility_high_leverage_control_external_shock_evidence": (
        ROOT / "reports" / "accessibility_high_leverage_control_external_shock_evidence.csv",
        "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW", "high-leverage provisional comparison municipality", "2015-11 to 2019-10 external-review window"),
    "accessibility_comparison_high_leverage_control_external_risk_screen": (
        ROOT / "data_processed" / "accessibility_comparison_high_leverage_control_external_risk_screen.csv",
        "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW", "treated municipality by provisional comparison municipality", "November 2017 anchor and adjacent 24-month windows"),
    "accessibility_remaining_control_external_review_worklist": (
        ROOT / "reports" / "accessibility_remaining_control_external_review_worklist.csv",
        "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW", "provisional comparison municipality", "stage-20 review checkpoint"),
    "accessibility_remaining_control_external_shock_evidence": (
        ROOT / "reports" / "accessibility_remaining_control_external_shock_evidence.csv",
        "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW", "remaining provisional comparison municipality", "2015-11 to 2019-10 external-review window"),
    "accessibility_comparison_full_control_external_risk_screen": (
        ROOT / "data_processed" / "accessibility_comparison_full_control_external_risk_screen.csv",
        "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW", "treated municipality by provisional comparison municipality", "November 2017 anchor and adjacent 24-month windows"),
    "accessibility_spillover_review_worklist": (
        ROOT / "reports" / "accessibility_spillover_review_worklist.csv",
        "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW", "surviving treated-control comparison pair", "stage-21 review checkpoint"),
    "accessibility_pair_spillover_evidence": (
        ROOT / "reports" / "accessibility_pair_spillover_evidence.csv",
        "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN", "surviving treated-control comparison pair", "November 2017 anchor and current scheduled-access sensitivity"),
    "accessibility_comparison_spillover_screen": (
        ROOT / "data_processed" / "accessibility_comparison_spillover_screen.csv",
        "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN", "treated municipality by provisional comparison municipality", "stage-22 spillover-screen checkpoint"),
    "accessibility_parallel_trend_worklist": (
        ROOT / "reports" / "accessibility_parallel_trend_worklist.csv",
        "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN", "surviving treated-control comparison pair", "36-month pre-anchor worklist"),
    "accessibility_parallel_trend_diagnostics": (
        ROOT / "reports" / "accessibility_parallel_trend_diagnostics.csv",
        "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC", "surviving treated-control comparison pair", "36-month pre-anchor diagnostic"),
    "accessibility_comparison_parallel_trend_screen": (
        ROOT / "data_processed" / "accessibility_comparison_parallel_trend_screen.csv",
        "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC", "treated municipality by provisional comparison municipality", "stage-23 pretrend checkpoint"),
    "accessibility_estimation_candidate_pairs": (
        ROOT / "reports" / "accessibility_estimation_candidate_pairs.csv",
        "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC", "pretrend-compatible treated-control comparison pair", "36-month pre-anchor diagnostic"),
    "accessibility_pilot_stacked_panel": (
        ROOT / "data_processed" / "accessibility_pilot_stacked_panel.csv",
        "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION", "matched stack by municipality and month", "event months -24 to +23"),
    "accessibility_pilot_did_estimates": (
        ROOT / "reports" / "accessibility_pilot_did_estimates.csv",
        "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION", "pilot specification", "24-month pre/post and sensitivity windows"),
    "accessibility_pilot_event_study": (
        ROOT / "reports" / "accessibility_pilot_event_study.csv",
        "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION", "candidate tier by six-month event-time bin", "event months -24 to +23"),
    "accessibility_pilot_influence_sensitivity": (
        ROOT / "reports" / "accessibility_pilot_influence_sensitivity.csv",
        "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION", "leave-one-treated or leave-one-pair pilot specification", "event months -24 to +23"),
    "accessibility_pilot_treated_decomposition": (
        ROOT / "reports" / "accessibility_pilot_treated_decomposition.csv",
        "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION", "treated municipality and weighted retained controls", "24-month pre/post and truncated-post windows"),
    "accessibility_pilot_small_cluster_inference": (
        ROOT / "reports" / "accessibility_pilot_small_cluster_inference.csv",
        "DERIVED_ACCESSIBILITY_SMALL_CLUSTER_INFERENCE", "primary non-causal pilot specification", "24-month pre/post window"),
    "accessibility_pilot_inference_components": (
        ROOT / "reports" / "accessibility_pilot_inference_components.csv",
        "DERIVED_ACCESSIBILITY_SMALL_CLUSTER_INFERENCE", "connected treated-stack component", "24-month pre/post window"),
}


DESCRIPTIONS = {
    "station_group_id": "Stable analytical group identifier kept separate from lift cluster and municipality IDs",
    "station_group_name": "Reviewed human-readable station-group label",
    "group_origin": "Whether the group comes from a direct listing link, a reviewed pending relation, or both",
    "scope_status": "Qualified relation between official destination labels and the retained analytical group",
    "grouping_basis": "Evidence-based reason for retaining components together",
    "component_resort_ids": "Pipe-delimited stable supplied resort listing IDs used for structure",
    "component_listing_count": "Number of unique supplied listings whose structural values enter the group",
    "source_entry_event_ids": "Pipe-delimited stable official base-entry event IDs",
    "source_entry_labels": "Original official station labels represented by the group",
    "entry_event_count": "Number of original in-scope base-entry labels mapped to the group",
    "first_entry_season": "Earliest documented Magic Pass base-entry season in the group",
    "first_effective_month": "Analytical first month of base-pass exposure",
    "first_winter_effective_month": "November anchor of the station group's first Magic Pass winter season",
    "ski_area_km_unique_listing_sum": "Published piste kilometres summed once per unique component listing",
    "number_lifts_unique_listing_sum": "Published lift counts summed once per unique component listing",
    "altitude_top_m_min": "Minimum published top altitude across unique component listings",
    "altitude_top_m_max": "Maximum published top altitude across unique component listings",
    "structural_data_status": "Completeness status of the deduplicated resort-directory structure",
    "cluster_ids_lineage_only": "Preserved lift cluster IDs for lineage; never used as the grouping rule",
    "current_access_assumption": "Statement that current access is held fixed for the first descriptive screen",
    "membership_continuity_status": "Whether membership is carried forward by assumption or bounded by a documented exit",
    "descriptive_exposure_approved": "Whether this row has passed the current descriptive exposure gate",
    "causal_treatment_approved": "Whether the station group is approved as a causal treatment",
    "review_status": "Documented external-shock review classification for the treated municipality",
    "shock_severity": "Qualitative directness and severity class of the reviewed concurrent intervention",
    "shock_timing": "Documented timing of the reviewed external intervention relative to the treatment anchor",
    "design_decision": "Rule assigning the treated municipality to descriptive, broad-reviewed or strict Magic-only candidate sets",
    "recommended_sensitivity": "Targeted robustness check recommended from the municipality-specific document review",
    "review_source_ids": "Pipe-delimited official source identifiers supporting the positive evidence classification",
    "eligible_broad_reviewed_set": "Whether the treated municipality avoids a high direct concurrent shock in the reviewed evidence",
    "eligible_strict_magic_only_candidate_set": "Whether the row remains in the stricter candidate set after high and moderate direct interventions are removed",
    "largest_absolute_yoy_bed_change_date": "Month of the largest absolute year-on-year change in available hotel beds during the review window",
    "largest_absolute_yoy_bed_change_phase": "Whether the largest year-on-year hotel-bed change occurs before or after the November 2017 anchor",
    "stage19_pair_decision": "Pair status after combining the stage-18 internal screen with treated-municipality external evidence",
    "strict_pair_count": "Number of stage-19 strict comparison pairs reusing the reviewed control municipality",
    "strict_treated_municipality_count": "Number of distinct treated municipalities paired with the reviewed control in the stage-19 strict set",
    "strict_treated_municipality_names": "Pipe-delimited treated municipalities paired with the reviewed control in the stage-19 strict set",
    "high_leverage_control_review_completed": "Whether this control belongs to and completed the stage-20 review of controls reused in at least two strict pairs",
    "retained_in_strict_candidate_after_review": "Whether the reviewed control remains usable in the strict candidate set subject to its named sensitivity",
    "excluded_from_strict_candidate_by_review": "Whether positive external-shock evidence removes the reviewed control from the strict candidate set",
    "strict_candidate_before_high_leverage_control_review": "Whether the pair belonged to the 32-pair stage-19 strict candidate set",
    "strict_candidate_excluded_by_high_leverage_control_review": "Whether stage-20 positive evidence removes the pair because its control has a major competing shock",
    "retained_in_strict_candidate_after_high_leverage_control_review": "Whether the pair remains among the 28 strict candidates after stage-20 control review",
    "strict_candidate_control_external_reviewed_and_retained": "Whether the pair's high-leverage control was reviewed and retained with a documented sensitivity",
    "strict_candidate_control_external_review_pending": "Whether the pair remains a strict candidate but its control-specific external review is pending",
    "control_external_review_completed_after_stage20": "Whether any completed control external review is available after stage 20",
    "stage20_pair_decision": "Pair status after the high-leverage control external-shock review",
    "remaining_control_review_completed": "Whether the stage-20 pending control completed its local external-shock review in stage 21",
    "strict_candidate_before_remaining_control_review": "Whether the pair belonged to the 28-pair stage-20 strict candidate set",
    "strict_candidate_excluded_by_remaining_control_review": "Whether stage-21 positive evidence removes the pair because its control has a major competing shock",
    "retained_in_strict_candidate_after_full_control_review": "Whether the pair remains in the strict candidate set after every local control review",
    "control_external_review_completed_after_stage21": "Whether the pair's control has a completed local external review after stage 21",
    "strict_candidate_all_local_control_reviews_complete": "Whether a surviving strict candidate has completed treated-side and control-side local reviews",
    "visitor_market_spillover_review_completed_after_stage21": "Whether shared tourist-basin and visitor-market spillovers have been reviewed after stage 21",
    "stage21_pair_decision": "Pair status after all local control external-shock reviews",
    "spillover_review_questions": "Pipe-delimited visitor-market, destination, transport and substitution questions for the pair review",
    "parallel_trends_review_status": "Checkpoint status of the pair-specific parallel-trends assessment",
    "operational_tourist_basin_definition": "Operational reference catchment based on scheduled travel from the municipality reference origin to station-group access points",
    "direct_local_spillover_low_risk_by_declared_proxies": "Whether pair distance, station-network distance, window exposure and current scheduled access jointly indicate low direct local interference",
    "broad_visitor_market_substitution_status": "Status of wider national or interregional substitution that cannot be cleared by local distance and scheduled-time proxies",
    "eligible_for_parallel_trend_diagnostic": "Whether the pair passes the disclosed direct-local-spillover proxy screen and may enter pretrend diagnostics",
    "seasonally_adjusted_monthly_difference_trend": "Monthly trend in treated-minus-control log hotel nights after calendar-month fixed effects",
    "hac_trend_standard_error": "Newey-West heteroskedasticity/autocorrelation-consistent standard error for the differential monthly trend",
    "hac_trend_ci95_contains_zero": "Whether the approximate 95 percent HAC interval for the differential trend includes zero; not an acceptance rule alone",
    "primary_pretrend_rule_passed": "Whether all predeclared primary coverage, correlation, RMSE, seasonality and differential-trend magnitude thresholds pass",
    "sensitivity_pretrend_rule_passed": "Whether all predeclared relaxed sensitivity thresholds pass",
    "pretrend_diagnostic_class": "Primary-compatible, sensitivity-only or failed predeclared pretrend magnitude classification",
    "eligible_for_primary_estimation_sensitivity": "Whether the pair may enter a primary non-causal estimation sensitivity after passing the primary diagnostic rule",
    "eligible_for_relaxed_estimation_sensitivity": "Whether the pair may enter the broader non-causal estimation sensitivity",
    "stack_unit_weight": "Within-stack analytical weight: one for the treated municipality and reciprocal control count for each comparison municipality",
    "treated_post": "Indicator equal to one for the treated municipality in event months zero and later",
    "estimate_log_points": "Weighted stacked pilot coefficient in log hotel overnight units",
    "estimate_percent_change": "Exponentiated pilot coefficient minus one; descriptive conversion, not a causal effect",
    "municipality_cluster_count": "Number of stable municipality identifiers used for clustered sandwich uncertainty",
    "estimation_candidate_tier": "Primary or relaxed-sensitivity-only pretrend compatibility tier",
    "event_mapping_status": "Direct listing link or reviewed scope relation used to map the event",
    "effective_month": "Analytical month when the base-entry event begins",
    "effective_month_precision": "Exact-validity or analytical-anchor status of the effective month",
    "winter_effective_month": "November anchor of the documented first entry season",
    "winter_effective_month_precision": "Exact founding validity or analytical winter-anchor status",
    "component_count_change": "Original destination-label entry count; group exposure itself changes once",
    "identity_equivalence_approved": "Whether event label and group are approved as strictly identical entities",
    "access_point_id": "Stable current-map, resort-listing, or BAV access reference identifier",
    "access_point_name": "Source label of the station access point",
    "reference_latitude": "Latitude of the station access reference point",
    "reference_longitude": "Longitude of the station access reference point",
    "reference_source_id": "Source identifier for the access coordinate",
    "reference_method": "Rule used to select the station access reference point",
    "selected_stop_distance_from_access_point_km": "Straight-line distance from station access point to selected served ground stop",
    "access_node_quality": "Distance-based current access-node review class",
    "descriptive_routing_node_approved": "Whether node distance is acceptable for initial descriptive routing",
    "historical_access_validated": "Whether the station access node is verified for the historical entry period",
    "mean_one_way_generalized_minutes": "Mean of outbound and return generalized scheduled travel time",
    "mean_round_trip_generalized_minutes": "Sum of mean outbound and return generalized scheduled travel time",
    "routing_pair_complete": "Whether all 24 sampled weekday/Saturday requests have feasible itineraries",
    "descriptive_accessibility_usable": "Complete routing pair with at least one reviewed current group access node",
    "station_group_has_reviewed_current_access_node": "Whether the group has at least one access node within 2.5 km",
    "current_access_fixed": "Whether current 2026 access is held fixed across historical months",
    "multiple_active_groups_120min": "Whether more than one assumed-active group is accessible within 120 minutes",
    "any_new_group_entry_120min": "Whether at least one accessible station group enters in the month",
    "public_transport_exposure_source_id": "Derived journey source used by monthly exposure variables",
    "membership_exposure_source_id": "Derived membership-event source used by monthly exposure variables",
    "causal_exposure_approved": "Whether monthly exposure is approved for causal interpretation",
    "event_time_months": "Calendar months relative to the station group's first effective month",
    "group_assumed_active": "Whether group membership is carried as active in the event-window month",
    "other_active_group_count_120min": "Other assumed-active station groups accessible within 120 minutes",
    "other_group_entry_same_month_count_120min": "Other accessible groups entering in the same municipality-month",
    "nearest_other_entry_gap_months_120min": "Absolute month gap to the nearest other accessible group entry",
    "other_entry_within_12_months_120min": "Whether another accessible group enters within plus or minus 12 months",
    "post_entry": "Whether event time is zero or positive",
    "causal_interpretation_approved": "Whether the event-window row is approved for causal interpretation",
    "observed_hotel_overnights": "Whether the official hotel-night outcome is observed in this window row",
    "pre_24_mean_hotel_overnights": "Mean observed hotel nights in event months -24 through -1",
    "post_24_mean_hotel_overnights": "Mean observed hotel nights in event months 0 through 23",
    "descriptive_log_change_post24_minus_pre24": "Post-24 minus pre-24 mean log hotel nights",
    "descriptive_mean_nights_pct_change": "Percentage change in mean hotel nights from the adjacent pre-24 to post-24 window",
    "entry_window_overlaps_covid_sensitivity": "Whether the adjacent 48-month window intersects March 2020 through April 2022",
    "descriptive_diagnostic_available": "Whether the group has at least one complete adjacent 24/24 municipality pair",
    "municipality_pairs_total": "All hotel-municipality routing pairs for the station group",
    "municipality_pairs_complete": "Pairs complete for every scheduled request",
    "municipality_pairs_descriptive_usable": "Pairs passing the current descriptive routing-node gate",
    "municipality_pairs_120min": "Usable municipality pairs within 120 mean one-way minutes",
    "pairs_complete_24_pre_24_post": "Accessible pairs with 24 observed outcome months before and after entry",
    "pairs_with_other_entry_within_12_months": "Accessible pairs with another group entry within plus or minus 12 months",
    "pairs_without_other_entry_within_12_months": "Accessible pairs without another group entry within plus or minus 12 months",
    "descriptive_event_window_ready": "Whether at least one accessible municipality supplies a complete 24/24 window",
    "entry_separation_possible_somewhere": "Whether any accessible municipality avoids another entry within plus or minus 12 months",
    "mechanically_isolated_non_covid_window": "Complete 24/24 window with no other accessible entry within twelve months and no COVID-sensitivity overlap",
    "manual_identification_review_priority": "Mechanical priority for manual identification review; never a causal approval",
    "identification_blocking_reasons": "Pipe-delimited reasons preventing causal interpretation of the group-municipality pair",
    "catchment_signature_sha256": "SHA-256 of the sorted municipality identifiers in the current 120-minute group catchment",
    "exact_same_anchor_catchment_collision": "Whether another reviewed group has the same entry anchor and identical current municipality catchment",
    "mechanically_distinct_design_column": "Whether the current group exposure column is not an exact date-and-catchment duplicate",
    "identification_status": "Conservative station-group identification classification after timing, overlap and support checks",
    "sequential_complete_window_candidate": "Whether a municipality has complete 24/24 windows for at least two distinct accessible entry months",
    "sequential_non_covid_isolated_candidate": "Whether a municipality has at least two complete, isolated and non-COVID accessible entry windows",
    "first_exposure_month": "First month when any station group is descriptively accessible and enters Magic Pass",
    "groups_entering_at_first_exposure": "Number of accessible station groups entering in the municipality's first exposure month",
    "first_exposure_group_names": "Pipe-delimited station groups entering at first municipal exposure",
    "first_exposure_candidate_for_manual_design_review": "Complete non-COVID first-exposure window with no later entry during the post 24 months",
    "comparison_candidate_type": "Never-exposed or not-yet-exposed status under the current 120-minute matrix",
    "descriptive_pretrend_comparability_score": "Within-treated-municipality percentile summary of pre-period comparability metrics",
    "comparability_rank": "Relative rank of a provisional comparison within one treated municipality",
    "pretrend_screen_usable": "Whether outcome coverage and metric availability allow descriptive ranking",
    "parallel_trends_approved": "Whether the parallel-trends assumption has been approved",
    "historical_origin_stop_found": "Whether the current municipality origin stop or a reviewed historical equivalent is present in the 2018 feed",
    "historical_destination_stop_found": "Whether the current destination access stop or a reviewed historical equivalent is present in the 2018 feed",
    "historical_route_computed": "Whether the priority route was computed from the 2018 timetable",
    "historical_access_plausibility_status": "Status of the targeted 2018 access validation",
    "historical_routing_pair_complete": "Whether all 24 historical weekday and Saturday requests have feasible itineraries",
    "historical_mean_one_way_generalized_minutes": "Mean historical generalized time across outbound and return directions",
    "signed_2018_to_2026_time_change_minutes": "Current 2026 mean time minus historical 2018 mean time",
    "absolute_2018_to_2026_time_change_minutes": "Absolute magnitude of the 2018-to-2026 mean-time change",
    "relative_2018_to_2026_time_change_percent": "Signed 2018-to-2026 time change divided by the historical mean",
    "historical_first_exposure_retained": "Whether at least one founding station group remains within 120 minutes under the historical routing variant",
    "all_current_founding_groups_historically_within_120_minutes": "Whether every currently assigned founding group remains within 120 minutes under the historical routing variant",
    "routing_transfer_variant": "Strict or sensitivity transfer topology used for historical routing",
    "minimum_representative_distance_to_window_magic_access_point_km": "Minimum straight-line distance from the municipality representative point to a station-group access point active by the end of the 24-month post window",
    "network_proximity_band": "Sensitivity band for municipality representative-point proximity to the 2017-2019 Magic Pass network",
    "documented_competing_pass_link_in_window": "Whether a supplied resort point in the municipality has a positive documented link to a reviewed competing pass in 2017/18 or 2018/19",
    "large_hotel_capacity_shift_warning": "Whether hotel beds, establishments or year-on-year available-bed changes exceed a predeclared descriptive warning threshold",
    "existing_external_shock_exact_anchor": "Whether an earlier source-backed donor review documents a local shock for the same November 2017 anchor",
    "treated_control_representative_distance_km": "Great-circle distance between treated and comparison municipality representative points",
    "internal_pair_triage_decision": "Non-causal priority decision combining documented risks and descriptive proxy warnings",
    "retained_for_external_review": "Whether the pair remains prioritised for municipality-specific external source review",
    "internal_risk_flags": "Pipe-delimited documented risks and descriptive proxy warnings raised by the internal screen",
    "external_review_topics": "Evidence domains still requiring municipality-specific external source review",
    "external_review_status": "Checkpoint status of the municipality-specific external source review",
    "mapping_method": "Exact stable stop identifier or reviewed historical stop-equivalence rule",
    "historical_node_usable": "Whether the historical endpoint is active on both sampled service days",
}


def source_row(source_id: str, **kwargs) -> dict:
    row = {column: "" for column in SOURCE_COLUMNS}
    row["source_id"] = source_id
    row.update(kwargs)
    return row


def treated_review_external_sources() -> list[dict]:
    """Register newly collected official documents without weakening old entries."""
    catalog = {
        row["source_id"]: row
        for row in json.loads(EVIDENCE_CONFIG_PATH.read_text(encoding="utf-8"))
    }
    rows = []
    for source_id in sorted(NEW_TREATED_REVIEW_SOURCE_IDS):
        if source_id not in catalog:
            raise KeyError(f"Missing treated-review evidence config: {source_id}")
        candidates = []
        for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json")):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata.get("source_id") == source_id and metadata.get("http_status") == 200:
                candidates.append((metadata.get("retrieval_date", ""), metadata))
        if not candidates:
            raise FileNotFoundError(f"No successful cached retrieval for {source_id}")
        _, metadata = max(candidates, key=lambda item: item[0])
        source = catalog[source_id]
        raw_file = metadata["raw_file"].replace("\\", "/")
        rows.append(source_row(
            source_id,
            variable_name="treated_municipality_external_shock_evidence",
            variable_description=source["description"],
            source_organisation=source["organisation"],
            source_dataset_name=source["description"],
            source_page_url=source["url"],
            direct_download_url=metadata.get("final_url", source["url"]),
            retrieval_method="HTTP GET with immutable local response, metadata sidecar and SHA-256",
            retrieval_date=metadata["retrieval_date"],
            original_file_name=Path(raw_file).name,
            local_raw_file=raw_file,
            processed_file="reports/accessibility_treated_external_shock_evidence.csv|data_processed/accessibility_comparison_treated_external_risk_screen.csv|reports/66_AUDIT_EXTERNE_COMMUNES_TRAITEES_FR.md",
            geographic_level="official municipality, destination or regional tourism evidence",
            temporal_resolution="document-specific event or policy period",
            temporal_start="2016", temporal_end="2019",
            unit="documented event, investment, governance or accommodation evidence",
            license="UNKNOWN; preserve official citation, original URL and immutable checksum",
            access_conditions="Public official source; automated retrieval respects robots.txt",
            transformation_applied="Manual document-level review encoded in config/accessibility_treated_external_shock_review.json; positive evidence only",
            quality_notes="A source can document a concurrent intervention but cannot by itself identify its effect on hotel overnight stays",
            confidence_level="high for the cited official statement; analytical severity remains a documented review judgement",
            manual_verification="Relevant page or section inspected; cached file and SHA-256 verified by the stage-19 builder",
            notes="Missing evidence is never interpreted as proof that no shock occurred",
        ))
    return rows


def control_review_external_sources() -> list[dict]:
    """Register the stage-20 control evidence with immutable local lineage."""
    catalog = {
        row["source_id"]: row
        for row in json.loads(EVIDENCE_CONFIG_PATH.read_text(encoding="utf-8"))
    }
    rows = []
    for source_id in sorted(NEW_CONTROL_REVIEW_SOURCE_IDS):
        if source_id not in catalog:
            raise KeyError(f"Missing control-review evidence config: {source_id}")
        candidates = []
        for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json")):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata.get("source_id") == source_id and metadata.get("http_status") == 200:
                candidates.append((metadata.get("retrieval_date", ""), metadata))
        if not candidates:
            raise FileNotFoundError(f"No successful cached retrieval for {source_id}")
        _, metadata = max(candidates, key=lambda item: item[0])
        source = catalog[source_id]
        raw_file = metadata["raw_file"].replace("\\", "/")
        rows.append(source_row(
            source_id,
            variable_name="control_municipality_external_shock_evidence",
            variable_description=source["description"],
            source_organisation=source["organisation"],
            source_dataset_name=source["description"],
            source_page_url=source["url"],
            direct_download_url=metadata.get("final_url", source["url"]),
            retrieval_method="HTTP GET with immutable local response, metadata sidecar and SHA-256",
            retrieval_date=metadata["retrieval_date"],
            original_file_name=Path(raw_file).name,
            local_raw_file=raw_file,
            processed_file="reports/accessibility_high_leverage_control_external_shock_evidence.csv|data_processed/accessibility_comparison_high_leverage_control_external_risk_screen.csv|reports/67_AUDIT_EXTERNE_CONTROLES_PRIORITAIRES_FR.md",
            geographic_level="official municipality, accommodation operator or regional-tourism evidence",
            temporal_resolution="document-specific opening, project or policy period",
            temporal_start="2017", temporal_end="2021",
            unit="documented hotel, tourism project, renovation or municipal-budget evidence",
            license="UNKNOWN; preserve source citation, original URL and immutable checksum",
            access_conditions="Public source; automated retrieval respects robots.txt",
            transformation_applied="Manual document-level review encoded in config/accessibility_high_leverage_control_external_shock_review.json; positive evidence only",
            quality_notes="A source can document a control-side competing shock but cannot by itself identify its effect on hotel overnight stays",
            confidence_level="high for the cited statement where official or operator-owned; medium for the hosted Lenzburg press clipping; analytical severity remains a documented review judgement",
            manual_verification="Relevant page or HTML section inspected; cached file and SHA-256 verified by the stage-20 builder",
            notes="Missing evidence is never interpreted as proof that no shock occurred; visitor-market spillovers remain pending",
        ))
    return rows


def remaining_control_review_external_sources() -> list[dict]:
    """Register the stage-21 control evidence with immutable local lineage."""
    catalog = {
        row["source_id"]: row
        for row in json.loads(EVIDENCE_CONFIG_PATH.read_text(encoding="utf-8"))
    }
    rows = []
    for source_id in sorted(NEW_REMAINING_CONTROL_REVIEW_SOURCE_IDS):
        if source_id not in catalog:
            raise KeyError(f"Missing remaining-control evidence config: {source_id}")
        candidates = []
        for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json")):
            metadata = json.loads(path.read_text(encoding="utf-8"))
            if metadata.get("source_id") == source_id and metadata.get("http_status") == 200:
                candidates.append((metadata.get("retrieval_date", ""), metadata))
        if not candidates:
            raise FileNotFoundError(f"No successful cached retrieval for {source_id}")
        _, metadata = max(candidates, key=lambda item: item[0])
        source = catalog[source_id]
        raw_file = metadata["raw_file"].replace("\\", "/")
        rows.append(source_row(
            source_id,
            variable_name="control_municipality_external_shock_evidence",
            variable_description=source["description"],
            source_organisation=source["organisation"],
            source_dataset_name=source["description"],
            source_page_url=source["url"],
            direct_download_url=metadata.get("final_url", source["url"]),
            retrieval_method="HTTP GET with immutable local response, metadata sidecar and SHA-256",
            retrieval_date=metadata["retrieval_date"],
            original_file_name=Path(raw_file).name,
            local_raw_file=raw_file,
            processed_file="reports/accessibility_remaining_control_external_shock_evidence.csv|data_processed/accessibility_comparison_full_control_external_risk_screen.csv|reports/68_AUDIT_EXTERNE_CONTROLES_RESTANTS_FR.md",
            geographic_level="official municipality, destination, canton or accommodation-market evidence",
            temporal_resolution="document-specific opening, closure, project, policy or review period",
            temporal_start="2016", temporal_end="2022",
            unit="documented hotel, event, tourism-policy, governance or municipal-budget evidence",
            license="UNKNOWN; preserve source citation, original URL and immutable checksum",
            access_conditions="Public source; automated retrieval respects robots.txt",
            transformation_applied="Manual document-level review encoded in config/accessibility_remaining_control_external_shock_review.json; positive evidence only",
            quality_notes="A source can document a control-side competing shock but cannot by itself identify its effect on hotel overnight stays",
            confidence_level="high for the cited official statement; medium for the Arbon municipal notice reproduced in a local publication; analytical severity remains a documented review judgement",
            manual_verification="Relevant page or HTML section inspected; cached file and SHA-256 verified by the stage-21 builder",
            notes="Missing evidence is never interpreted as proof that no shock occurred; visitor-market spillovers remain pending",
        ))
    return rows


def derived_sources() -> list[dict]:
    common = {
        "source_organisation": "Master thesis analytical pipeline",
        "retrieval_method": "Deterministic offline Python transformation of checksum-registered project inputs",
        "retrieval_date": "2026-10-02",
        "license": "Derived analytical data; upstream source terms continue to apply",
        "access_conditions": "Local reproducible project output",
        "confidence_level": "high for reproducibility; descriptive only",
    }
    rows = [
        source_row(
            "DERIVED_ACCESSIBILITY_STATION_GROUPS", **common,
            variable_name="station_group|component_resort_ids|deduplicated_structure|access_points|access_nodes",
            variable_description="Reviewed Swiss Magic Pass station groups, unique-listing structural aggregation and current access references",
            source_dataset_name="Accessibility expansion station-group registry",
            local_raw_file="config/accessibility_station_groups.json",
            processed_file="data_processed/accessibility_station_groups.csv|data_processed/accessibility_station_access_points.csv|reports/accessibility_station_access_nodes.csv|reports/55_GROUPES_STATIONS_ET_POINTS_ACCES_FR.md",
            geographic_level="Swiss station group and access point",
            temporal_resolution="entry history plus current access snapshot",
            temporal_start="2017-11", temporal_end="2026-10",
            unit="group, listing, kilometre, lift, metre, coordinate and stop",
            transformation_applied="Map 78 in-scope base entries to 71 groups; never group from lift cluster alone; sum each structural listing once; select official current access coordinates and nearest served ground stop",
            quality_notes="Four groups lack resort-directory structure; current access is not historical access; composite relation does not always prove lift connectivity",
            manual_verification="All 16 pending events mapped from versioned scope review; exact source labels and four directory gaps retained",
        ),
        source_row(
            "DERIVED_ACCESSIBILITY_STATION_GROUP_EVENTS", **common,
            variable_name="station_group_entry_event|effective_month|documented_exit|membership_continuity_status",
            variable_description="Event-to-group mapping and monthly base-membership anchors for all in-scope Swiss destinations",
            source_dataset_name="Accessibility expansion station-group events",
            local_raw_file="config/accessibility_station_groups.json|data_processed/magic_pass_membership_history.csv",
            processed_file="data_processed/accessibility_station_group_events.csv|data_processed/accessibility_municipality_month_exposure.csv",
            geographic_level="official destination event and station group",
            temporal_resolution="event month",
            temporal_start="2017-11", temporal_end="2025-05",
            unit="event, season and month",
            transformation_applied="Retain every official base-entry event; collapse group exposure only at the group level; apply exact founding validity and May analytical anchors; stop Crans-Montana after documented exit",
            quality_notes="Annual continuity is assumed after first entry except the one documented exit; 78 events are not 78 independent treatments",
            manual_verification="Event partition fixed at 88 base entries: 78 in scope and ten foreign exclusions",
        ),
        source_row(
            "DERIVED_ACCESSIBILITY_STATION_GROUP_JOURNEYS", **common,
            variable_name="generalized_elapsed_minutes|sample_coverage|mean_one_way_generalized_minutes|time_thresholds",
            variable_description="Winter-2026 scheduled public-transport context for every station group and hotel municipality",
            source_dataset_name="Expanded station-group public-transport journeys",
            local_raw_file="config/path_c_analysis.json|reports/accessibility_station_access_nodes.csv",
            processed_file="data_processed/accessibility_station_group_journey_samples.csv|data_processed/accessibility_station_group_journey_context.csv|reports/56_TEMPS_TRAJET_GROUPES_STATIONS_COMMUNES_FR.md",
            geographic_level="station group by hotel municipality",
            temporal_resolution="Wednesday and Saturday winter-2026 timetable samples",
            temporal_start="2026-02-04", temporal_end="2026-02-07",
            unit="minutes, trips, transfers and coverage share",
            transformation_applied="Route 24 published departure requests per pair; retain fastest access point separately per request; aggregate outbound, return and threshold variants",
            quality_notes="Current static schedule only; no car routing, delays, crowding, fares, unlisted walking or historical stability",
            manual_verification="71 groups, 186 origins and 75 access nodes guarded by exact row-count checks and resumable caches",
        ),
        source_row(
            "DERIVED_ACCESSIBILITY_MUNICIPALITY_EXPOSURE", **common,
            variable_name="active_station_group_count|new_station_group_entry_count|known_ski_area_sum|known_lift_sum|event_time|concurrent_exposure|feasibility",
            variable_description="Municipality-month and station-group event-window exposure using multiple scheduled-time thresholds",
            source_dataset_name="Expanded Magic Pass municipality accessibility exposure",
            local_raw_file="data_processed/accessibility_station_group_events.csv|data_processed/accessibility_station_group_journey_context.csv|data_processed/hotel_municipality_month_enriched.csv",
            processed_file="data_processed/accessibility_municipality_month_exposure.csv|data_processed/accessibility_station_group_event_window.csv|data_processed/accessibility_station_group_pair_diagnostic.csv|reports/accessibility_station_group_feasibility.csv|reports/57_EXPOSITIONS_ET_FAISABILITE_ELARGIES_FR.md",
            geographic_level="hotel municipality series and station-group/municipality pair",
            temporal_resolution="monthly and event month -36 to +36",
            temporal_start="2013-01", temporal_end="2026-03",
            unit="counts, minutes, kilometres, lifts and official hotel outcomes",
            transformation_applied="Hold current access fixed; cross documented entry anchors with 30/60/90/120-minute pairs; preserve simultaneous groups and build 24-month before/after feasibility diagnostics",
            quality_notes="Exposure is descriptive; membership continuity, road travel, confounding, COVID and interference remain unresolved; zero causal approvals",
            manual_verification="Stable group, municipality and event grains plus protected false causal flags checked",
        ),
        source_row(
            "DERIVED_ACCESSIBILITY_IDENTIFICATION_AUDIT", **common,
            variable_name="entry_separation|covid_overlap|exposure_collinearity|first_exposure|pretrend_comparability",
            variable_description="Identification audit and pre-period comparison screening for expanded municipality accessibility exposure",
            source_dataset_name="Accessibility first-exposure identification audit",
            local_raw_file="data_processed/accessibility_station_group_pair_diagnostic.csv|data_processed/accessibility_municipality_month_exposure.csv",
            processed_file="data_processed/accessibility_identification_pair_audit.csv|reports/accessibility_identification_group_audit.csv|reports/accessibility_identification_municipality_audit.csv|reports/accessibility_first_exposure_audit.csv|data_processed/accessibility_first_exposure_pretrend_pairs.csv|reports/accessibility_first_exposure_pretrend_shortlist.csv|reports/58_AUDIT_IDENTIFICATION_EXPOSITION_COMMUNALE_FR.md|reports/59_SCREENING_COMPARAISONS_PRE_EXPOSITION_FR.md",
            geographic_level="hotel municipality, station group, entry cohort and provisional municipality pair",
            temporal_resolution="entry cohort, adjacent 24-month window and 36-month pre-period",
            temporal_start="2014-11", temporal_end="2026-03",
            unit="groups, municipalities, months, correlations, gaps and ranks",
            transformation_applied="Audit concurrent entries, COVID overlap, exact exposure collinearity and two-way fixed-effect rank; define municipality first exposure; rank provisional comparisons from pre-anchor outcomes and capacity only",
            quality_notes="Current 2026 access is projected historically; comparison ranking is relative and does not validate parallel trends, external shocks, spillovers or causal controls",
            manual_verification="Protected false causal flags, exact row counts and design-rank results checked by automated tests",
        ),
    ]
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION",
        variable_name="historical_route_samples|historical_route_context|stop_crosswalk|transfer_sensitivity|historical_first_exposure_retention",
        variable_description="Targeted 2018 accessibility validation for the 39 founding group-municipality routes under strict and two documented transfer scenarios",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Historical Magic Pass first-exposure accessibility validation",
        retrieval_method="Deterministic offline routing of checksum-pinned 2018 and 2026 GTFS inputs",
        retrieval_date="2026-10-03",
        local_raw_file="data_external/source_evidence/SKI_GTFS_TIMETABLE_2018_WINTER_20180207.zip|data_external/source_evidence/SKI_GTFS_TIMETABLE_2026_WINTER_20260207_20260922T125552Z.zip",
        processed_file="data_processed/accessibility_historical_gtfs_2018_journey_context.csv|data_processed/accessibility_historical_gtfs_2018_proximity_journey_context.csv|data_processed/accessibility_historical_gtfs_2018_current_transfer_journey_context.csv|reports/accessibility_historical_gtfs_2018_stop_audit.csv|reports/accessibility_historical_gtfs_2018_current_transfer_municipality_validation.csv|reports/accessibility_historically_screened_pretrend_shortlist.csv|reports/61_COMPARAISON_ACCES_HISTORIQUE_2018_2026_FR.md|reports/62_SENSIBILITE_TRANSFERTS_PROXIMITE_GTFS_2018_FR.md|reports/63_SENSIBILITE_TOPOLOGIE_TRANSFERTS_ACTUELS_GTFS_2018_FR.md|reports/64_REVUE_COMPARAISONS_APRES_ACCES_HISTORIQUE_FR.md",
        geographic_level="priority hotel municipality by founding station group",
        temporal_resolution="Wednesday and Saturday winter timetable samples",
        temporal_start="2018-02-07", temporal_end="2026-02-07",
        unit="minutes, trips, transfers, routes and municipality validation flags",
        license="Derived analytical data; Open Data Mobility Switzerland terms continue to apply",
        access_conditions="Local reproducible output from manually supplied historical archive and registered current archive",
        transformation_applied="Verify ZIP and SHA-256; audit 31 endpoints; route 936 requests per scenario; preserve strict published transfers; separately test 250-metre walking links and official 2026 transfer topology on active 2018 IDs",
        quality_notes="The strict 2018 transfer graph is structurally sparse; both augmented scenarios are sensitivities rather than historically published transfer evidence. Two invalid timetable trips per two sampled days are excluded without imputation. Zero causal approvals.",
        confidence_level="high for source integrity and computational reproducibility; medium-to-low for historical transfer topology",
        manual_verification="Two changed destination stops reviewed; all 19 origin stops exact; strict and sensitivity results kept separate",
        notes="Current-topology projection is the most directly documented sensitivity but remains non-historical and non-causal",
    ))
    rows.append(source_row(
        "SKI_GTFS_TIMETABLE_2018_WINTER_20180207",
        variable_name="historical_scheduled_stop_times|trips|routes|service_calendar|transfers|stop_coordinates",
        variable_description="Official timetable-year 2018 GTFS snapshot selected for targeted first-winter access validation",
        source_organisation="Business office SKI on behalf of the Swiss Federal Office of Transport (BAV/OFT)",
        source_dataset_name="Timetable 2018 GTFS, build 2018-02-07",
        source_page_url="https://archive.opentransportdata.swiss/timetable_gtfs_archive.htm",
        direct_download_url="https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2018-gtfs/GTFS_FP2018_2018-02-07.zip",
        retrieval_method="Manual user download from the exact official archive URL because robots.txt disallows automated collection; local ZIP integrity, size and SHA-256 verified",
        retrieval_date="2026-10-03",
        original_file_name="GTFS_FP2018_2018-02-07.zip",
        local_raw_file="data_external/source_evidence/SKI_GTFS_TIMETABLE_2018_WINTER_20180207.zip",
        processed_file="reports/accessibility_historical_gtfs_2018_manual_worklist.csv|reports/accessibility_historical_gtfs_2018_stop_audit.csv|data_processed/accessibility_historical_gtfs_2018_journey_samples.csv|data_processed/accessibility_historical_gtfs_2018_journey_context.csv|reports/60_AUDIT_HISTORIQUE_ACCES_PRIORITAIRE_FR.md|reports/61_COMPARAISON_ACCES_HISTORIQUE_2018_2026_FR.md",
        geographic_level="Swiss national public-transport timetable; targeted municipality-to-station routes",
        temporal_resolution="published static winter timetable snapshot",
        temporal_start="2017-12", temporal_end="2018-12",
        unit="scheduled service and time",
        license="Open Data Mobility Switzerland terms of use",
        access_conditions="Public archive; robots.txt disallows automated collection, so manual download is required",
        transformation_applied="Preserve archive unchanged; normalize Swiss platform suffixes; exclude one temporally invalid trip on each sampled day; route 39 priority pairs under published 2018 transfers",
        quality_notes="Exact 50,151,599-byte archive and SHA-256 655bf97a42b88da347cbe938e392351768766fddb2c76fc4ed111400104b7234 verified. The 2018 feed publishes only 184 normalized cross-stop transfer links, so strict routes form a documented under-connected lower bound.",
        confidence_level="high for source identity and strict published schedule; limited for practical interchange completeness",
        manual_verification="All 19 origins retain exact stop IDs; ten of twelve destination references are exact and two reviewed equivalents are documented",
        notes="Selected snapshot closest to 7 February of the first Magic Pass exposure winter; manual collection respected the archive robots policy",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_COMPARISON_INTERNAL_RISK_SCREEN",
        variable_name="network_proximity|bilateral_distance|hotel_capacity_shift|documented_competing_pass_link|existing_external_shock|pair_triage",
        variable_description="Internal evidence and proxy-risk screen for the 70 historically retained first-exposure comparison pairs",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility comparison internal risk screen",
        retrieval_method="Deterministic offline Python transformation of registered project data and previously reviewed evidence",
        retrieval_date="2026-10-03",
        local_raw_file="data_processed/municipality_population_geometry_2026.csv|data_processed/accessibility_station_group_journey_context.csv|data_processed/hotel_capacity_municipality_month.csv|data_processed/resort_point_municipality.csv|data_processed/resort_competing_pass_history.csv|reports/donor_external_shock_evidence.csv",
        processed_file="data_processed/accessibility_comparison_internal_risk_screen.csv|reports/accessibility_comparison_control_internal_diagnostics.csv|reports/accessibility_comparison_external_review_worklist.csv|reports/65_SCREENING_INTERNE_RISQUES_COMPARAISONS_FR.md",
        geographic_level="treated municipality by provisional comparison municipality; municipality review worklist",
        temporal_resolution="November 2017 anchor with adjacent 24-month windows",
        temporal_start="2015-11", temporal_end="2019-10",
        unit="kilometres, minutes, capacity changes, evidence flags and review priorities",
        license="Derived analytical data; upstream source terms continue to apply",
        access_conditions="Local reproducible output",
        transformation_applied="Measure representative-point proximity to station access points active by October 2019; retain current scheduled-time context; compare balanced 24-month capacity windows; link only positive documented competing-pass evidence and exact-anchor reviewed shocks; apply disclosed non-causal priority rules",
        quality_notes="Representative points are not tourism catchments; current scheduled times are not historical; capacity shifts can be shocks, seasonality or mediators; missing pass links never establish absence; no spillover or causal pair is cleared",
        confidence_level="high for deterministic joins and positive documented links; medium-to-low for proxy-risk interpretation",
        manual_verification="Thresholds, positive-evidence semantics, exact-anchor reuse and protected false causal flags are checked by automated tests",
        notes="The screen reduces external review effort; it does not estimate an effect or validate parallel trends",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_TREATED_EXTERNAL_SHOCK_REVIEW",
        variable_name="treated_external_shock_evidence|review_source_integrity|capacity_peak_timing|broad_reviewed_set|strict_magic_only_candidate_set|stage19_pair_decision",
        variable_description="Official-source external-shock review for the 14 historically retained treated municipalities and nested comparison sets",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility treated-municipality external shock review",
        retrieval_method="Deterministic Python join of manually reviewed official evidence, checksum sidecars, stage-18 pairs and official hotel capacity",
        retrieval_date="2026-10-03",
        local_raw_file="config/accessibility_treated_external_shock_review.json|config/evidence_sources.json|data_external/source_evidence|data_processed/accessibility_comparison_internal_risk_screen.csv|data_processed/hotel_capacity_municipality_month.csv",
        processed_file="reports/accessibility_treated_external_shock_evidence.csv|data_processed/accessibility_comparison_treated_external_risk_screen.csv|reports/accessibility_comparison_treated_external_review_summary.json|reports/66_AUDIT_EXTERNE_COMMUNES_TRAITEES_FR.md",
        geographic_level="treated hotel municipality and treated-control comparison pair",
        temporal_resolution="November 2017 anchor with November 2015 to October 2019 review window",
        temporal_start="2015-11", temporal_end="2019-10",
        unit="documents, evidence classes, months, hotel beds and nested candidate flags",
        license="Derived analytical data; upstream official-source terms continue to apply",
        access_conditions="Local reproducible output from immutable cached official evidence",
        transformation_applied="Verify every cited file against its SHA-256 sidecar; classify high direct, moderate direct and targeted/indirect risks; retain all treatments descriptively; build broad and strict nested comparison sets",
        quality_notes="Document review cannot prove shock absence or identify an effect. Control-side external review, visitor-market spillovers and parallel trends remain pending; zero causal approvals.",
        confidence_level="high for source integrity and deterministic set construction; medium for qualitative severity classification",
        manual_verification="Fourteen treated municipalities reviewed; key municipal PDFs visually inspected; all positive evidence linked to registered official sources",
        notes="The 38-pair broad set and 32-pair strict set are review candidates, not causal samples",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW",
        variable_name="control_external_shock_evidence|source_integrity|capacity_peak_timing|strict_candidate_after_control_review|remaining_control_worklist|stage20_pair_decision",
        variable_description="External-shock review of the seven control municipalities reused in at least two stage-19 strict comparison pairs",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility high-leverage control external-shock review",
        retrieval_method="Deterministic Python join of manually reviewed evidence, checksum sidecars, stage-19 pairs and official hotel capacity",
        retrieval_date="2026-10-03",
        local_raw_file="config/accessibility_high_leverage_control_external_shock_review.json|config/evidence_sources.json|data_external/source_evidence|data_processed/accessibility_comparison_treated_external_risk_screen.csv|data_processed/hotel_capacity_municipality_month.csv",
        processed_file="reports/accessibility_high_leverage_control_external_shock_evidence.csv|data_processed/accessibility_comparison_high_leverage_control_external_risk_screen.csv|reports/accessibility_remaining_control_external_review_worklist.csv|reports/accessibility_comparison_high_leverage_control_review_summary.json|reports/67_AUDIT_EXTERNE_CONTROLES_PRIORITAIRES_FR.md",
        geographic_level="provisional comparison municipality and treated-control comparison pair",
        temporal_resolution="November 2017 anchor with November 2015 to October 2019 review window",
        temporal_start="2015-11", temporal_end="2019-10",
        unit="documents, evidence classes, months, hotel beds, controls and pair flags",
        license="Derived analytical data; upstream source terms continue to apply",
        access_conditions="Local reproducible output from immutable cached evidence",
        transformation_applied="Review controls used in at least two strict pairs first; verify every cited file against its SHA-256 sidecar; remove pairs only for major positive competing-shock evidence; retain smaller changes with explicit sensitivity; generate the remaining-control worklist",
        quality_notes="Document review cannot prove shock absence or identify an effect. Seventeen controls, visitor-market spillovers and parallel trends remain pending; zero causal approvals.",
        confidence_level="high for source integrity and deterministic set construction; medium for qualitative severity classification",
        manual_verification="Seven controls and fifteen strict pairs reviewed; key PDFs visually inspected and HTML claims checked against cached source text",
        notes="The 28-pair post-screen set remains a candidate pool, not a causal sample",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW",
        variable_name="remaining_control_external_shock_evidence|source_integrity|capacity_peak_timing|strict_candidate_after_full_control_review|spillover_worklist|stage21_pair_decision",
        variable_description="External-shock review of the 17 controls still pending after stage 20 and construction of the complete local-control-reviewed candidate set",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility remaining-control external-shock review",
        retrieval_method="Deterministic Python join of manually reviewed evidence, checksum sidecars, stage-20 pairs and official hotel capacity",
        retrieval_date="2026-10-03",
        local_raw_file="config/accessibility_remaining_control_external_shock_review.json|config/evidence_sources.json|data_external/source_evidence|data_processed/accessibility_comparison_high_leverage_control_external_risk_screen.csv|data_processed/hotel_capacity_municipality_month.csv",
        processed_file="reports/accessibility_remaining_control_external_shock_evidence.csv|data_processed/accessibility_comparison_full_control_external_risk_screen.csv|reports/accessibility_spillover_review_worklist.csv|reports/accessibility_comparison_full_control_review_summary.json|reports/68_AUDIT_EXTERNE_CONTROLES_RESTANTS_FR.md",
        geographic_level="provisional comparison municipality and treated-control comparison pair",
        temporal_resolution="November 2017 anchor with November 2015 to October 2019 review window",
        temporal_start="2015-11", temporal_end="2019-10",
        unit="documents, evidence classes, months, hotel beds, controls and pair flags",
        license="Derived analytical data; upstream source terms continue to apply",
        access_conditions="Local reproducible output from immutable cached evidence",
        transformation_applied="Review all 17 controls pending after stage 20; verify every cited file against its SHA-256 sidecar; remove pairs only for major positive competing-shock evidence; retain smaller, late or out-of-window changes with explicit sensitivity; generate the pair-level spillover worklist",
        quality_notes="All surviving strict controls have a local review, but document review cannot prove shock absence or identify an effect. Visitor-market spillovers and parallel trends remain pending; zero causal approvals.",
        confidence_level="high for source integrity and deterministic set construction; medium for qualitative severity classification",
        manual_verification="Seventeen controls and seventeen strict pairs reviewed; official PDFs and HTML claims inspected; all positive evidence linked to registered sources",
        notes="The 21-pair post-screen set remains a candidate pool, not a causal sample",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN",
        variable_name="operational_tourist_basin|control_to_treated_entry_group_time|pair_distance|window_network_distance|direct_local_spillover_screen|parallel_trend_worklist",
        variable_description="Pair-level direct-local-spillover screen using the municipality-centre-to-station scheduled-time basin proposed for the accessibility extension",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility comparison operational-basin and spillover screen",
        retrieval_method="Deterministic Python transformation of stage-21 pairs and checksum-registered current scheduled journeys",
        retrieval_date="2026-10-03",
        local_raw_file="data_processed/accessibility_comparison_full_control_external_risk_screen.csv|data_processed/accessibility_station_group_journey_context.csv",
        processed_file="reports/accessibility_pair_spillover_evidence.csv|data_processed/accessibility_comparison_spillover_screen.csv|reports/accessibility_parallel_trend_worklist.csv|reports/accessibility_pair_spillover_summary.json|reports/69_SCREENING_BASSINS_TOURISTIQUES_SPILLOVERS_FR.md",
        geographic_level="treated hotel municipality by comparison hotel municipality and station-group access point",
        temporal_resolution="November 2017 anchor, November 2015 to October 2019 exposure window and winter-2026 scheduled-time sensitivity",
        temporal_start="2015-11", temporal_end="2026-02",
        unit="kilometres, scheduled minutes, exposure classifications and pair flags",
        license="Derived analytical data; upstream source terms continue to apply",
        access_conditions="Local reproducible output",
        transformation_applied="Require control non-exposure during the review window, more than 50 km between municipality reference points, more than 50 km from a window-active Magic access point, no shared current territory and specific-group scheduled time above 120 minutes or complete-matrix non-exposure",
        quality_notes="Current scheduled times and reference-point distances screen direct local interference only. They do not prove absence of historical, national or interregional visitor substitution; official destination boundaries are not treated as hard catchments.",
        confidence_level="high for deterministic joins; medium-to-low for historical and behavioural spillover interpretation",
        manual_verification="All 21 surviving pairs checked; 20 have complete current routes to entry groups and one retains complete-matrix non-exposure despite no specific complete route",
        notes="All 21 advance to pretrend diagnostics with broad-market substitution explicitly unresolved; zero causal spillover clearances",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC",
        variable_name="pretrend_rule|paired_pre_months|outcome_correlation|standardised_rmse|seasonal_rmse|seasonally_adjusted_difference_trend|hac_uncertainty|estimation_candidate_tier",
        variable_description="Predeclared primary and relaxed pair-level pretrend diagnostics for the 21 post-spillover comparison candidates",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility comparison parallel-trend compatibility diagnostic",
        retrieval_method="Deterministic Python calculation from the predeclared JSON rule, stage-22 pairs and official monthly hotel outcomes",
        retrieval_date="2026-10-03",
        local_raw_file="config/accessibility_parallel_trend_rules.json|data_processed/accessibility_comparison_spillover_screen.csv|data_processed/accessibility_municipality_month_exposure.csv",
        processed_file="reports/accessibility_parallel_trend_diagnostics.csv|data_processed/accessibility_comparison_parallel_trend_screen.csv|reports/accessibility_estimation_candidate_pairs.csv|reports/accessibility_parallel_trend_summary.json|reports/70_DIAGNOSTIC_PRETENDANCES_COMPARAISONS_FR.md",
        geographic_level="treated hotel municipality by comparison hotel municipality",
        temporal_resolution="36 monthly observations before the pair's first exposure month",
        temporal_start="2014-11", temporal_end="2017-10",
        unit="months, correlations, standardised errors, log-point trends and pair flags",
        license="Derived analytical data; upstream source terms continue to apply",
        access_conditions="Local reproducible output",
        transformation_applied="Apply predeclared coverage, correlation, standardized-RMSE, seasonal-RMSE and seasonally adjusted differential-trend magnitude gates; report Newey-West uncertainty at 12 lags without using non-rejection alone as acceptance",
        quality_notes="Pre-treatment compatibility cannot prove the parallel-trends counterfactual. Historical transfer topology and broad visitor substitution remain sensitivity limitations; zero causal approvals.",
        confidence_level="high for reproducibility and rule application; limited for causal identification",
        manual_verification="Rule file is checksum-recorded; primary rule is nested inside relaxed sensitivity; protected causal flags remain false",
        notes="Eleven primary-compatible pairs cover six treated municipalities; fifteen pairs including sensitivity-only cases remain available for non-causal estimation sensitivity",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION",
        variable_name="weighted_stacked_panel|matched_difference_in_differences_pilot|binned_event_study|municipality_clustered_uncertainty|leave_one_out_sensitivity",
        variable_description="Predeclared non-causal pilot estimates for the primary and relaxed pretrend-compatible municipality pairs",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility first-exposure non-causal pilot estimation",
        retrieval_method="Deterministic weighted two-way within transformation and municipality-clustered sandwich covariance implemented in Python",
        retrieval_date="2026-10-03",
        local_raw_file="config/accessibility_pilot_estimation.json|reports/accessibility_estimation_candidate_pairs.csv|data_processed/accessibility_municipality_month_exposure.csv|reports/accessibility_historical_gtfs_2018_municipality_validation.csv|reports/accessibility_historical_gtfs_2018_proximity_municipality_validation.csv",
        processed_file="data_processed/accessibility_pilot_stacked_panel.csv|reports/accessibility_pilot_did_estimates.csv|reports/accessibility_pilot_event_study.csv|reports/accessibility_pilot_influence_sensitivity.csv|reports/accessibility_pilot_treated_decomposition.csv|reports/accessibility_pilot_estimation_summary.json|reports/71_ESTIMATION_PILOTE_NON_CAUSALE_FR.md",
        geographic_level="matched stack of one treated hotel municipality and its retained comparison municipalities",
        temporal_resolution="monthly event time from -24 to +23 with a November 2017 common anchor",
        temporal_start="2015-11", temporal_end="2019-10",
        unit="log hotel overnight coefficient, descriptive percent conversion and uncertainty interval",
        license="Derived analytical data; upstream source terms continue to apply",
        access_conditions="Local reproducible output",
        transformation_applied="Give each treated municipality weight one and divide total control weight one within its stack; remove stack-by-municipality and stack-by-calendar-month means; estimate treated-post and binned event-time terms; cluster sandwich scores by stable municipality across reused controls; run uniform truncation, conservative-control exclusion and leave-one-out sensitivities",
        quality_notes="Only 16 municipality clusters enter the primary pilot. Historical access relies on a transfer-topology sensitivity, broad visitor substitution remains unresolved and sample selection is substantial. Normal cluster-robust intervals are descriptive; no causal estimate is approved.",
        confidence_level="high for deterministic arithmetic and internal replication; low for causal identification",
        manual_verification="Primary coefficient independently reproduced as the equal mean of six stack-specific post-minus-pre log gaps; weights sum to one for treated and one for controls in every stack-month",
        notes="Primary pilot is -6.8 percent, but the conservative control-exclusion sensitivity is -2.0 percent with an interval spanning zero; neither is a causal Magic Pass effect",
    ))
    rows.append(source_row(
        "CANAY_ROMANO_SHAIKH_APPROXIMATE_SYMMETRY_2017",
        variable_name="approximate_randomization_test|sign_change_symmetry|fixed_number_of_clusters",
        variable_description="Methodological basis for sign-change tests with a fixed small number of large clusters under an explicit approximate-symmetry condition",
        source_organisation="Econometrica / The Econometric Society",
        source_dataset_name="Canay, Romano and Shaikh (2017), Randomization Tests Under an Approximate Symmetry Assumption",
        source_page_url="https://doi.org/10.3982/ECTA13081",
        retrieval_method="Methodological publication consulted through DOI metadata and the authors' public paper page",
        retrieval_date="2026-10-04",
        geographic_level="methodological reference",
        temporal_resolution="not applicable",
        unit="statistical inference method",
        license="Publisher terms apply",
        access_conditions="Public bibliographic page; article access depends on publisher terms",
        transformation_applied="Used to motivate, not validate, the exact connected-component sign-change sensitivity",
        quality_notes="The project test still requires component independence and sign symmetry; it is not a random treatment-assignment test",
        confidence_level="peer-reviewed methodological source",
        manual_verification="Title, authors, journal, volume, pages and DOI checked",
        notes="Econometrica 85(3), 1013-1030",
    ))
    rows.append(source_row(
        "MACKINNON_WEBB_WILD_BOOTSTRAP_FEW_CLUSTERS_2018",
        variable_name="few_treated_clusters|cluster_robust_inference_limit|wild_bootstrap_limit",
        variable_description="Methodological warning that conventional clustered inference and wild-cluster procedures can be unreliable with very few treated clusters",
        source_organisation="The Econometrics Journal / Royal Economic Society",
        source_dataset_name="MacKinnon and Webb (2018), The wild bootstrap for few (treated) clusters",
        source_page_url="https://doi.org/10.1111/ectj.12107",
        retrieval_method="Methodological publication consulted through publisher and author working-paper pages",
        retrieval_date="2026-10-04",
        geographic_level="methodological reference",
        temporal_resolution="not applicable",
        unit="statistical inference method",
        license="Publisher terms apply",
        access_conditions="Public bibliographic and author working-paper pages",
        transformation_applied="Used to justify reporting effective treated-unit counts and avoiding a stronger causal or significance claim",
        quality_notes="The article does not certify any one procedure for the project's selected and partially dependent matched stacks",
        confidence_level="peer-reviewed methodological source",
        manual_verification="Title, authors, journal, volume, pages and DOI checked",
        notes="The Econometrics Journal 21(2), 114-135",
    ))
    rows.append(source_row(
        "DERIVED_ACCESSIBILITY_SMALL_CLUSTER_INFERENCE",
        variable_name="treated_stack_t_reference|connected_component_sign_flip|effective_treated_stack_count|component_dependence",
        variable_description="Predeclared small-effective-sample inference sensitivity for the primary non-causal accessibility pilot",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Accessibility pilot small-cluster inference audit",
        retrieval_method="Deterministic Python reconstruction of treated-stack contrasts and exhaustive component sign enumeration",
        retrieval_date="2026-10-04",
        local_raw_file="config/accessibility_small_cluster_inference.json|data_processed/accessibility_pilot_stacked_panel.csv|reports/accessibility_pilot_did_estimates.csv",
        processed_file="reports/accessibility_pilot_small_cluster_inference.csv|reports/accessibility_pilot_inference_components.csv|reports/accessibility_pilot_small_cluster_inference_summary.json|reports/72_INFERENCE_PETIT_NOMBRE_COMMUNES_FR.md",
        geographic_level="treated municipality stack and connected stack-municipality component",
        temporal_resolution="monthly event time from -24 to +23 summarized as stack-level pre/post contrasts",
        temporal_start="2015-11", temporal_end="2019-10",
        unit="log hotel overnight contrast, descriptive percent conversion, p-value and component",
        license="Derived analytical data; upstream source terms continue to apply",
        access_conditions="Local reproducible output",
        transformation_applied="Reproduce six equal-weight treated-stack DiD gaps; compute a Student-t reference with five degrees of freedom; link stacks sharing any municipality; enumerate every joint component sign pattern",
        quality_notes="Only five disconnected components remain after respecting the reused Emmen control. The t reference approximates stack independence; the sign test assumes independence and sign symmetry across graph components and is not random-assignment inference. No causal approval.",
        confidence_level="high for deterministic arithmetic; low for causal identification and limited for inferential power",
        manual_verification="Stage-24 coefficient reproduced exactly; Bulle and Gruyères linked through BFS 1024; all 32 component sign patterns enumerated",
        notes="The normal clustered result is not robust to effective-sample inference: treated-stack t and connected-component sign sensitivities both include or fail to reject zero",
    ))
    rows.extend(treated_review_external_sources())
    rows.extend(control_review_external_sources())
    rows.extend(remaining_control_review_external_sources())
    return rows


def description(variable: str, existing_lookup: dict[str, str]) -> str:
    if variable in DESCRIPTIONS:
        return DESCRIPTIONS[variable]
    if variable in existing_lookup and existing_lookup[variable]:
        return existing_lookup[variable]
    if variable.startswith("within_") and variable.endswith("_minutes"):
        threshold = variable.split("_")[1]
        return f"Whether mean one-way generalized scheduled time is at most {threshold} minutes"
    if variable.startswith("municipalities_within_"):
        threshold = variable.split("_")[2].replace("min", "")
        return f"Usable hotel municipalities within {threshold} mean one-way minutes"
    if variable.startswith("active_station_group_count_"):
        threshold = variable.rsplit("_", 1)[1].replace("min", "")
        return f"Assumed-active station groups accessible within {threshold} mean one-way minutes"
    if variable.startswith("new_station_group_entry_count_"):
        threshold = variable.rsplit("_", 1)[1].replace("min", "")
        return f"Station groups entering Magic Pass this month within {threshold} mean one-way minutes"
    if variable.startswith("active_winter_station_group_count_"):
        return "Assumed-active groups within the time threshold during November-April only"
    if variable.startswith("new_winter_station_group_entry_count_"):
        return "Groups reaching their first November winter anchor within the time threshold"
    if variable.startswith("active_groups_with_structure_count_"):
        return "Accessible active station groups with complete resort-directory structural values"
    if variable.startswith("active_groups_missing_structure_count_"):
        return "Accessible active station groups missing resort-directory structural values"
    if variable.startswith("active_ski_area_km_known_sum_"):
        return "Known published piste kilometres summed across accessible active groups without duplicate listings"
    if variable.startswith("active_lifts_known_sum_"):
        return "Known published lift counts summed across accessible active groups without duplicate listings"
    if variable.startswith("nearest_active_group_minutes_"):
        return "Minimum mean one-way scheduled time among accessible active groups under the stated threshold"
    if variable.startswith("outbound_") or variable.startswith("return_"):
        direction = "outbound municipality-to-station" if variable.startswith("outbound_") else "return station-to-municipality"
        return f"{direction.capitalize()} routing metric: {variable.split('_', 1)[1].replace('_', ' ')}"
    if variable.startswith("selected_stop_"):
        return f"Selected served ground-stop attribute: {variable.replace('selected_stop_', '').replace('_', ' ')}"
    if variable.startswith("municipality_main_stop_"):
        return f"Municipality origin-stop attribute: {variable.replace('municipality_main_stop_', '').replace('_', ' ')}"
    if variable.endswith("_approved"):
        return f"Protected approval flag for {variable.replace('_approved', '').replace('_', ' ')}"
    if variable.endswith("_source_id") or variable == "source_id" or variable == "source_ids":
        return "Stable provenance source identifier or pipe-delimited identifiers"
    return f"Recorded analytical field: {variable.replace('_', ' ')}"


def unit(variable: str) -> str:
    if "minutes" in variable or variable.endswith("_month") or variable == "event_time_months":
        return "minutes" if "minutes" in variable else "month"
    if variable.endswith("_km") or "ski_area_km" in variable:
        return "kilometres"
    if "share" in variable:
        return "share"
    if "latitude" in variable or "longitude" in variable:
        return "decimal degrees"
    if "altitude" in variable:
        return "metres"
    if "count" in variable or variable.startswith("number_") or variable.startswith("pairs_") or variable.startswith("municipalities_"):
        return "count"
    return "identifier, category, flag or source unit"


def main() -> None:
    missing = [str(path) for path, *_ in TABLES.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Accessibility outputs missing: {missing}")
    sources = pd.read_csv(SOURCE_PATH, dtype=str, keep_default_na=False)
    incoming_sources = pd.DataFrame(derived_sources()).reindex(columns=SOURCE_COLUMNS,
                                                               fill_value="")
    sources = sources[~sources.source_id.isin(incoming_sources.source_id)]
    sources = pd.concat([sources, incoming_sources], ignore_index=True).fillna("")
    sources.sort_values("source_id").to_csv(SOURCE_PATH, index=False, lineterminator="\n")

    existing = pd.read_csv(DICTIONARY_PATH, dtype=str, keep_default_na=False)
    existing_lookup = (existing[existing.description.ne("")]
                       .drop_duplicates("variable").set_index("variable").description.to_dict())
    rows = []
    for table, (path, source_id, geo, temporal) in TABLES.items():
        frame = pd.read_csv(path)
        missing_shares = frame.isna().mean()
        for variable in frame.columns:
            role = ("quality gate" if "approved" in variable or "usable" in variable
                    else "descriptive exposure candidate" if any(
                        token in variable for token in ["active_", "entry", "within_", "generalized_minutes"])
                    else "outcome" if variable in {"hotel_overnights", "log_overnights"}
                    else "lineage or descriptive context")
            rows.append({
                "variable": variable,
                "table": table,
                "description": description(variable, existing_lookup),
                "unit": unit(variable),
                "data_type": str(frame[variable].dtype),
                "geographic_level": geo,
                "temporal_level": temporal,
                "source_id": source_id,
                "raw_or_derived": "derived or retained source field",
                "formula": "See the deterministic builder and linked methodology report for this table",
                "causal_role": role,
                "missing_share": f"{missing_shares[variable]:.6f}",
                "notes": ("Current access is fixed for initial descriptive tests; zero causal approvals. "
                          "Original source values remain un-imputed."),
            })
        del frame
    incoming = pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS, fill_value="")
    keys = set(zip(incoming.table, incoming.variable))
    keep = ~existing.apply(lambda row: (row.table, row.variable) in keys, axis=1)
    dictionary = pd.concat([existing[keep], incoming], ignore_index=True).fillna("")
    dictionary.sort_values(["table", "variable"]).to_csv(
        DICTIONARY_PATH, index=False, lineterminator="\n")
    print(json.dumps({
        "source_records_added_or_updated": len(incoming_sources),
        "dictionary_rows_added_or_updated": len(incoming),
        "total_source_records": len(sources),
        "total_dictionary_rows": len(dictionary),
    }, indent=2))


if __name__ == "__main__":
    main()
