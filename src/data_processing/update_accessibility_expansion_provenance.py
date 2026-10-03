"""Register accessibility-expansion sources and analytical variables."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "metadata" / "data_sources_master.csv"
DICTIONARY_PATH = ROOT / "metadata" / "data_dictionary.csv"
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
    "mapping_method": "Exact stable stop identifier or reviewed historical stop-equivalence rule",
    "historical_node_usable": "Whether the historical endpoint is active on both sampled service days",
}


def source_row(source_id: str, **kwargs) -> dict:
    row = {column: "" for column in SOURCE_COLUMNS}
    row["source_id"] = source_id
    row.update(kwargs)
    return row


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
