"""Generate the treatment, panel, causal, and model feasibility gate report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESORTS = ROOT / "data_processed" / "resort_master.csv"
POINTS = ROOT / "data_processed" / "resort_point_municipality.csv"
HOTEL = ROOT / "data_processed" / "hotel_municipality_month.csv"
HISTORY = ROOT / "data_processed" / "magic_pass_membership_history.csv"
CURRENT = ROOT / "data_processed" / "magic_pass_current_destinations.csv"
REVIEWED_UNITS = ROOT / "data_processed" / "treatment_destination_units.csv"
REVIEWED_PANEL = ROOT / "data_processed" / "destination_month_panel.csv"
CONTINUITY_AUDIT = ROOT / "reports" / "membership_continuity_audit.csv"
MEMBERSHIP_STATUS = ROOT / "data_processed" / "magic_pass_membership_status_by_season.csv"
CONTROL_SUMMARY = ROOT / "reports" / "control_audit_summary.json"
DONOR_PRETREND_SUMMARY = ROOT / "reports" / "donor_pretrend_summary.json"
DONOR_NETWORK_SUMMARY = ROOT / "reports" / "donor_network_spillover_summary.json"
DONOR_EXTERNAL_SHOCK_SUMMARY = ROOT / "reports" / "donor_external_shock_summary.json"
DISTANCE_GRADIENT_SUMMARY = ROOT / "reports" / "treatment_distance_gradient_summary.json"
TRANSPORT_ZONE_PROXY_AUDIT_SUMMARY = (
    ROOT / "reports" / "transport_zone_proxy_audit_summary.json"
)
PUBLIC_TRANSPORT_JOURNEY_SUMMARY = (
    ROOT / "reports" / "public_transport_journey_context_summary.json"
)
PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW_SUMMARY = (
    ROOT / "reports" / "public_transport_arrival_node_review_summary.json"
)
PUBLIC_TRANSPORT_HISTORICAL_SUMMARY = (
    ROOT / "reports" / "public_transport_historical_audit_summary.json"
)
CAPACITY_SUMMARY = ROOT / "reports" / "hotel_capacity_summary.json"
SNOW_SUMMARY = ROOT / "reports" / "snow_proxy_summary.json"
SNOW_SENSITIVITY_SUMMARY = ROOT / "reports" / "snow_station_sensitivity_summary.json"
WEATHER_SUMMARY = ROOT / "reports" / "weather_proxy_summary.json"
TEMPORAL_SUMMARY = ROOT / "reports" / "temporal_controls_summary.json"
CLUSTERS = ROOT / "data_raw" / "stations_ski_clusters_resume_gps_bergfex.csv"
WINDOW_OUTPUT = ROOT / "reports" / "provisional_treatment_window_coverage.csv"
COUNT_OUTPUT = ROOT / "reports" / "feasibility_counts.csv"
REPORT_OUTPUT = ROOT / "reports" / "model_feasibility_report.md"
CAPACITY_DIAGNOSTIC_OUTPUT = ROOT / "reports" / "hotel_capacity_treatment_diagnostics.csv"


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def diagnostic_anchor(season: str) -> pd.Timestamp:
    first_year = int(str(season).split("/")[0])
    # The first official pass was winter-only from November 2017.  Later press
    # packs describe annual summer/winter passes; 1 May is used only to count
    # potentially available outcome months, never as an accepted treatment date.
    month = 11 if first_year == 2017 else 5
    return pd.Timestamp(year=first_year, month=month, day=1)


def main() -> None:
    resorts = pd.read_csv(RESORTS, dtype="string")
    points = pd.read_csv(POINTS, dtype="string")
    hotel = pd.read_csv(HOTEL)
    history = pd.read_csv(HISTORY, dtype="string")
    current = pd.read_csv(CURRENT, dtype="string")
    reviewed_units = pd.read_csv(REVIEWED_UNITS, dtype="string")
    reviewed_panel = pd.read_csv(REVIEWED_PANEL)
    continuity = pd.read_csv(CONTINUITY_AUDIT, dtype="string")
    membership_status = pd.read_csv(MEMBERSHIP_STATUS, dtype="string")
    control_summary = json.loads(CONTROL_SUMMARY.read_text(encoding="utf-8"))
    donor_pretrend_summary = json.loads(
        DONOR_PRETREND_SUMMARY.read_text(encoding="utf-8")
    )
    donor_network_summary = json.loads(
        DONOR_NETWORK_SUMMARY.read_text(encoding="utf-8")
    )
    donor_external_shock_summary = json.loads(
        DONOR_EXTERNAL_SHOCK_SUMMARY.read_text(encoding="utf-8")
    )
    distance_gradient_summary = json.loads(
        DISTANCE_GRADIENT_SUMMARY.read_text(encoding="utf-8")
    )
    transport_zone_proxy_audit_summary = json.loads(
        TRANSPORT_ZONE_PROXY_AUDIT_SUMMARY.read_text(encoding="utf-8")
    )
    public_transport_journey_summary = json.loads(
        PUBLIC_TRANSPORT_JOURNEY_SUMMARY.read_text(encoding="utf-8")
    )
    public_transport_arrival_node_review_summary = json.loads(
        PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW_SUMMARY.read_text(encoding="utf-8")
    )
    public_transport_historical_summary = json.loads(
        PUBLIC_TRANSPORT_HISTORICAL_SUMMARY.read_text(encoding="utf-8")
    )
    capacity_summary = json.loads(CAPACITY_SUMMARY.read_text(encoding="utf-8"))
    snow_summary = json.loads(SNOW_SUMMARY.read_text(encoding="utf-8"))
    snow_sensitivity_summary = json.loads(
        SNOW_SENSITIVITY_SUMMARY.read_text(encoding="utf-8")
    )
    weather_summary = json.loads(WEATHER_SUMMARY.read_text(encoding="utf-8"))
    temporal_summary = json.loads(TEMPORAL_SUMMARY.read_text(encoding="utf-8"))
    clusters = pd.read_csv(CLUSTERS, sep=";", dtype="string")
    hotel["date"] = pd.to_datetime(hotel["date"], errors="raise")

    observed = hotel[hotel["hotel_overnights"].notna()].copy()
    observed_start = observed["date"].min()
    observed_end = observed["date"].max()
    municipality_months = {
        name: set(group["date"])
        for name, group in observed.groupby("municipality_name_source", observed=True)
    }

    base = history[
        history["event_type"].eq("base_pass_entry")
        & history["candidate_resort_id"].notna()
        & as_bool(history["bfs_hotel_universe"])
    ].copy()
    window_rows: list[dict] = []
    for row in base.itertuples(index=False):
        anchor = diagnostic_anchor(row.entry_season)
        months = municipality_months.get(row.bfs_hotel_municipality_name, set())
        pre = sum(month < anchor for month in months)
        potential_post = sum(month >= anchor for month in months)
        if pd.notna(row.exit_date) and str(row.exit_date).strip():
            exit_month = pd.Timestamp(row.exit_date).to_period("M").to_timestamp()
            active_post = sum(anchor <= month <= exit_month for month in months)
            active_post_status = "bounded_by_documented_exit"
        else:
            active_post = potential_post
            active_post_status = "continuity_not_verified"
        window_rows.append(
            {
                "event_id": row.event_id,
                "candidate_resort_id": row.candidate_resort_id,
                "source_resort_name": row.source_resort_name,
                "cluster_id": row.cluster_id,
                "municipality_bfs_id": row.point_municipality_bfs_id,
                "municipality_name": row.bfs_hotel_municipality_name,
                "entry_season": row.entry_season,
                "diagnostic_anchor": anchor.date().isoformat(),
                "anchor_status": "provisional_for_coverage_count_only",
                "observed_pre_months": pre,
                "observed_post_months_potential": potential_post,
                "observed_post_months_with_known_exit_bound": active_post,
                "post_continuity_status": active_post_status,
                "has_24_months_pre": pre >= 24,
                "has_36_months_pre": pre >= 36,
                "has_24_months_post_potential": active_post >= 24,
                "has_36_months_post_potential": active_post >= 36,
                "treatment_ready": False,
            }
        )
    windows = pd.DataFrame(window_rows)
    WINDOW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    windows.to_csv(WINDOW_OUTPUT, index=False)

    reviewed_panel["date"] = pd.to_datetime(reviewed_panel["date"], errors="raise")
    reviewed_panel["first_analysis_anchor"] = pd.to_datetime(
        reviewed_panel["first_analysis_anchor"], errors="raise"
    )
    capacity_diagnostics: list[dict] = []
    for destination_unit_id, group in reviewed_panel.groupby(
        "destination_unit_id", observed=True
    ):
        group = group.sort_values("date")
        complete = group.dropna(
            subset=[
                "hotel_overnights_capacity_table",
                "hotel_beds_available",
                "hotel_overnights_per_available_bed_month",
            ]
        )
        anchor = group["first_analysis_anchor"].iloc[0]
        pre = complete.loc[complete["date"].lt(anchor)].tail(24)
        post = complete.loc[
            complete["date"].ge(anchor) & complete["assumed_base_member"]
        ].head(24)

        def mean(frame: pd.DataFrame, column: str) -> float:
            return float(frame[column].mean()) if len(frame) else float("nan")

        def percent_change(before: float, after: float) -> float:
            if pd.isna(before) or pd.isna(after) or before == 0:
                return float("nan")
            return 100 * (after / before - 1)

        pre_beds = mean(pre, "hotel_beds_available")
        post_beds = mean(post, "hotel_beds_available")
        pre_nights = mean(pre, "hotel_overnights_capacity_table")
        post_nights = mean(post, "hotel_overnights_capacity_table")
        pre_intensity = mean(pre, "hotel_overnights_per_available_bed_month")
        post_intensity = mean(post, "hotel_overnights_per_available_bed_month")
        capacity_diagnostics.append(
            {
                "destination_unit_id": destination_unit_id,
                "destination_name": group["destination_name"].iloc[0],
                "first_analysis_anchor": anchor.date().isoformat(),
                "pre_window_observed_months": len(pre),
                "active_post_window_observed_months_assumption": len(post),
                "complete_24_pre_and_24_post_capacity_window": len(pre) == 24
                and len(post) == 24,
                "mean_available_beds_pre24": pre_beds,
                "mean_available_beds_post24": post_beds,
                "available_beds_change_pct": percent_change(pre_beds, post_beds),
                "mean_hotel_overnights_pre24": pre_nights,
                "mean_hotel_overnights_post24": post_nights,
                "hotel_overnights_change_pct": percent_change(pre_nights, post_nights),
                "mean_overnights_per_bed_pre24": pre_intensity,
                "mean_overnights_per_bed_post24": post_intensity,
                "overnights_per_bed_change_pct": percent_change(
                    pre_intensity, post_intensity
                ),
                "membership_continuity_assumed": True,
                "causal_interpretation_approved": False,
                "diagnostic_note": (
                    "Descriptive adjacent-window comparison; no seasonality, COVID, "
                    "selection, trends, weather, or donor adjustment."
                ),
            }
        )
    capacity_diagnostic = pd.DataFrame(capacity_diagnostics)
    capacity_diagnostic.to_csv(CAPACITY_DIAGNOSTIC_OUTPUT, index=False)

    reached_hotel_municipalities = set(
        points.loc[as_bool(points["bfs_hotel_universe"]), "point_municipality_bfs_id"].dropna()
    )
    provisional_treated_municipalities = set(base["point_municipality_bfs_id"].dropna())
    naive_control_upper_bound = len(reached_hotel_municipalities - provisional_treated_municipalities)

    metrics = {
        "resort_listings_total": len(resorts),
        "lift_clusters_total": clusters["cluster_id"].nunique(),
        "lift_clusters_linked_to_resort_listings": resorts["cluster_id"].nunique(),
        "independent_resort_domains_validated": 0,
        "official_current_magic_destinations_snapshot": current["official_destination_id"].nunique(),
        "official_current_destinations_candidate_linked": current["candidate_resort_id"].nunique(),
        "documented_base_entry_events": int(history["event_type"].eq("base_pass_entry").sum()),
        "candidate_linked_base_entry_events": int(
            (history["event_type"].eq("base_pass_entry") & history["candidate_resort_id"].notna()).sum()
        ),
        "candidate_linked_base_entries_with_hotel_outcome": len(base),
        "provisional_treated_clusters_with_hotel_outcome": base["cluster_id"].nunique(),
        "provisional_treated_municipalities_with_hotel_outcome": base[
            "point_municipality_bfs_id"
        ].nunique(),
        "treated_with_exact_entry_date": 0,
        "treated_with_season_only_and_24_months_pre": int(windows["has_24_months_pre"].sum()),
        "treated_with_season_only_and_36_months_pre": int(windows["has_36_months_pre"].sum()),
        "treated_with_season_only_and_24_months_post_potential": int(
            windows["has_24_months_post_potential"].sum()
        ),
        "treated_with_season_only_and_36_months_post_potential": int(
            windows["has_36_months_post_potential"].sum()
        ),
        "unique_provisional_treatment_anchors": windows["diagnostic_anchor"].nunique(),
        "hotel_municipalities_total": hotel["municipality_name_source"].nunique(),
        "hotel_municipalities_reached_by_resort_point": len(reached_hotel_municipalities),
        "naive_non_treated_control_municipalities_upper_bound": naive_control_upper_bound,
        "approved_usable_controls": 0,
        "hotel_observed_start": observed_start.date().isoformat(),
        "hotel_observed_end": observed_end.date().isoformat(),
        "hotel_observed_month_rows": int(observed["hotel_overnights"].notna().sum()),
        "causal_treatment_units_approved": 0,
        "reviewed_destination_units": len(reviewed_units),
        "reviewed_destination_units_in_outcome_panel": int(
            as_bool(reviewed_units["eligible_for_reviewed_outcome_panel"]).sum()
        ),
        "reviewed_destination_units_excluded_incomplete_scope": int(
            (~as_bool(reviewed_units["eligible_for_reviewed_outcome_panel"])).sum()
        ),
        "reviewed_destination_month_rows": len(reviewed_panel),
        "reviewed_observed_destination_months": int(
            reviewed_panel["hotel_overnights"].notna().sum()
        ),
        "hotel_capacity_municipality_month_rows": int(
            capacity_summary["municipality_month_rows"]
        ),
        "hotel_capacity_complete_supply_rows": int(
            capacity_summary["complete_capacity_supply_rows"]
        ),
        "reviewed_destination_months_complete_capacity": int(
            reviewed_panel["complete_capacity_scope"].sum()
        ),
        "reviewed_units_with_complete_24pre_24post_capacity_window": int(
            capacity_diagnostic["complete_24_pre_and_24_post_capacity_window"].sum()
        ),
        "slf_snow_stations_with_daily_data": int(
            snow_summary["snow_stations_with_daily_data"]
        ),
        "slf_snow_stations_passing_longitudinal_gate": int(
            snow_summary["stations_passing_80pct_winter_coverage_gate"]
        ),
        "resorts_with_snow_climate_feature_ready": int(
            snow_summary["resorts_with_snow_climate_feature_ready"]
        ),
        "reviewed_resort_components_with_alternative_snow_station_test": int(
            snow_sensitivity_summary["reviewed_resort_components"]
        ),
        "alternative_snow_station_high_or_moderate_agreement": int(
            snow_sensitivity_summary["agreement_counts"].get("high", 0)
            + snow_sensitivity_summary["agreement_counts"].get("moderate", 0)
        ),
        "alternative_snow_station_low_agreement": int(
            snow_sensitivity_summary["agreement_counts"].get("low", 0)
        ),
        "alternative_snow_station_median_depth_correlation": float(
            snow_sensitivity_summary["median_winter_mean_depth_correlation"]
        ),
        "alternative_snow_station_median_relative_depth_difference": float(
            snow_sensitivity_summary[
                "median_relative_mean_absolute_depth_difference"
            ]
        ),
        "reviewed_destination_months_complete_snow_proxy": int(
            reviewed_panel["complete_snow_proxy"].sum()
        ),
        "observed_outcome_rows_with_complete_snow_proxy": int(
            (
                reviewed_panel["hotel_overnights"].notna()
                & reviewed_panel["complete_snow_proxy"]
            ).sum()
        ),
        "meteoswiss_candidate_stations_with_core_parameters_since_2013": int(
            weather_summary[
                "eligible_candidate_stations_with_core_parameters_since_2013"
            ]
        ),
        "meteoswiss_selected_weather_stations": int(
            weather_summary["selected_station_count"]
        ),
        "reviewed_destination_months_complete_weather_proxy": int(
            reviewed_panel["complete_weather_proxy"].sum()
        ),
        "observed_outcome_rows_with_complete_weather_proxy": int(
            (
                reviewed_panel["hotel_overnights"].notna()
                & reviewed_panel["complete_weather_proxy"]
            ).sum()
        ),
        "temporal_control_month_rows": int(temporal_summary["month_rows"]),
        "reviewed_destination_months_with_temporal_controls": int(
            reviewed_panel["temporal_control_source_id"].notna().sum()
        ),
        "reviewed_destination_months_in_covid_sensitivity_interval": int(
            as_bool(reviewed_panel["covid_sensitivity_month"]).sum()
        ),
        "reviewed_units_with_24_pre_and_post_months_assumption": int(
            (
                as_bool(reviewed_units["eligible_for_reviewed_outcome_panel"])
                & as_bool(reviewed_units["has_24_observed_pre_months"])
                & as_bool(reviewed_units["has_24_active_post_months_assumption"])
            ).sum()
        ),
        "reviewed_units_with_36_pre_and_post_months_assumption": int(
            (
                as_bool(reviewed_units["eligible_for_reviewed_outcome_panel"])
                & as_bool(reviewed_units["has_36_observed_pre_months"])
                & as_bool(reviewed_units["has_36_active_post_months_assumption"])
            ).sum()
        ),
        "reviewed_units_with_fully_documented_membership_continuity": int(
            as_bool(continuity["continuity_fully_documented"]).sum()
        ),
        "panel_units_with_fully_documented_membership_continuity": int(
            (
                as_bool(continuity["outcome_panel_eligible"])
                & as_bool(continuity["continuity_fully_documented"])
            ).sum()
        ),
        "fully_documented_panel_units_with_24_pre_and_post_months": int(
            (
                as_bool(reviewed_units["eligible_for_reviewed_outcome_panel"])
                & as_bool(reviewed_units["has_24_observed_pre_months"])
                & as_bool(reviewed_units["has_24_active_post_months_assumption"])
                & reviewed_units["destination_unit_id"].isin(
                    continuity.loc[
                        as_bool(continuity["continuity_fully_documented"]),
                        "destination_unit_id",
                    ]
                )
            ).sum()
        ),
        "active_unit_seasons_with_individual_winter_summer_evidence": int(
            membership_status["offering_source_id"].fillna("").ne("").sum()
        ),
        "active_unit_seasons_with_documented_summer_access": int(
            as_bool(membership_status["summer_access_documented"]).sum()
        ),
        "annual_seasons_with_individual_winter_summer_evidence": int(
            membership_status.loc[
                membership_status["offering_source_id"].fillna("").ne(""),
                "season",
            ].nunique()
        ),
        "control_municipalities_upper_bound_after_resolved_magic_links": int(
            control_summary["hotel_municipalities_reached_by_resort_points"]
            - control_summary["municipalities_with_known_magic_exposure_from_resolved_links"]
        ),
        "control_municipalities_upper_bound_after_scope_screen": int(control_summary["candidate_control_municipalities_upper_bound"]),
        "additional_scope_risk_municipalities_excluded": int(control_summary["additional_municipalities_excluded_by_scope_review"]),
        "treatment_donor_pairs_screened": int(
            control_summary["treatment_donor_pairs_screened"]
        ),
        "provisional_donor_pairs_30km_36pre": int(
            control_summary["provisional_donor_pairs_30km_36pre"]
        ),
        "provisional_donor_pairs_50km_36pre": int(
            control_summary["provisional_donor_pairs_50km_36pre"]
        ),
        "donor_pretrend_treatments_screened": int(
            donor_pretrend_summary["treatments_screened"]
        ),
        "donor_pretrend_pairs_screened": int(
            donor_pretrend_summary["provisional_pairs_screened"]
        ),
        "donor_pretrend_shortlisted_pairs": int(
            donor_pretrend_summary["shortlisted_pairs_for_manual_review"]
        ),
        "shortlisted_pairs_within_30km_any_resolved_magic": int(
            donor_network_summary[
                "shortlisted_pairs_within_30km_resolved_magic"
            ]
        ),
        "shortlisted_pairs_beyond_50km_any_resolved_magic": int(
            donor_network_summary["shortlisted_pairs"]
            - donor_network_summary[
                "shortlisted_pairs_within_50km_resolved_magic"
            ]
        ),
        "beyond_50km_pairs_excluded_for_local_tourism_shocks": int(
            donor_external_shock_summary[
                "excluded_contemporaneous_local_tourism_shock"
            ]
        ),
        "beyond_50km_pairs_with_magic_roster_absence": int(
            donor_external_shock_summary[
                "historical_magic_roster_absence_documented"
            ]
        ),
        "donor_pairs_remaining_deep_manual_audit": int(
            donor_external_shock_summary["remaining_deep_audit_pairs"]
        ),
        "same_destination_distance_crosswalk_rows": int(
            distance_gradient_summary["distance_crosswalk_rows"]
        ),
        "same_destination_distance_gradient_usable_rows": int(
            distance_gradient_summary["distance_gradient_usable_rows"]
        ),
        "positive_descriptive_near_far_contrasts": int(
            distance_gradient_summary[
                "destinations_with_positive_descriptive_near_far_contrast"
            ]
        ),
        "npvm_proxy_listing_points_geometrically_reconstructed": int(
            transport_zone_proxy_audit_summary["proxy_geometry_validation_passed"]
        ),
        "npvm_proxy_clusters": int(
            transport_zone_proxy_audit_summary["proxy_clusters"]
        ),
        "npvm_proxy_only_clusters": int(
            transport_zone_proxy_audit_summary["proxy_only_clusters"]
        ),
        "npvm_proxy_only_candidate_clusters": int(
            transport_zone_proxy_audit_summary["candidate_clusters_proxy_only"]
        ),
        "public_transport_journey_pairs": int(
            public_transport_journey_summary["destination_municipality_pairs"]
        ),
        "public_transport_journey_samples": int(
            public_transport_journey_summary["journey_samples"]
        ),
        "public_transport_journey_feasible_samples": int(
            public_transport_journey_summary["feasible_journey_samples"]
        ),
        "public_transport_journey_pairs_complete_all_samples": int(
            public_transport_journey_summary["pairs_complete_all_samples"]
        ),
        "public_transport_arrival_nodes_reviewed": int(
            public_transport_arrival_node_review_summary["reviewed_component_nodes"]
        ),
        "public_transport_arrival_nodes_descriptively_accepted": int(
            public_transport_arrival_node_review_summary[
                "accepted_for_descriptive_routing"
            ]
        ),
        "public_transport_arrival_village_or_local_centre_proxies": int(
            public_transport_arrival_node_review_summary[
                "village_or_local_centre_proxies"
            ]
        ),
        "public_transport_arrival_nodes_with_reference_day_warning": int(
            public_transport_arrival_node_review_summary[
                "nodes_with_reference_day_availability_warning"
            ]
        ),
        "public_transport_historical_anchor_years": len(
            public_transport_historical_summary["historical_anchor_years"]
        ),
        "public_transport_historical_components_service_compared": int(
            public_transport_historical_summary[
                "historical_components_service_compared"
            ]
        ),
        "unresolved_official_base_entry_labels": int(
            control_summary["unresolved_official_base_entry_labels"]
        ),
    }
    pd.DataFrame([{"metric": key, "value": value} for key, value in metrics.items()]).to_csv(
        COUNT_OUTPUT, index=False
    )

    model_rows = [
        ("Municipality fixed-effects panel", "Diagnostic-ready only", "Eleven reviewed outcome units, documented seasonal membership, monthly hotel capacity, deterministic calendar/COVID sensitivity flags, SLF snow proxies, and MeteoSwiss temperature/precipitation proxies can be represented, but treatment intensity, remaining confounding, spillovers, and controls remain unresolved."),
        ("Staggered Difference-in-Differences", "Not credible yet", "Reviewed-unit membership continuity is documented, but treatment intensity, pre-trends, spillovers and untreated-control status are not validated."),
        ("Matching", "Causal use rejected", "The 35-pair donor shortlist is exhausted by network proximity or overlapping donor-specific shocks; zero controls are approved."),
        ("Synthetic control / synthetic DiD", "Not credible under present donor design", "Every shortlisted pair is deprioritised or excluded; a future attempt requires a redesigned and broader donor search."),
        ("Causal forest", "Not supported", "At most 14 provisional treated municipalities is far below a defensible heterogeneous-effect sample."),
        ("X-Learner", "Not supported", "The effective treated-unit count is too small and treatment labels are not final."),
        ("DR-Learner", "Not supported", "The effective treated-unit count is too small and nuisance models would be unstable."),
        ("Gradient boosting", "Not run", "No defensible cluster-level supervised target exists; an unadjusted post-entry change is not a membership-uplift label."),
        ("Random forest", "Not run", "No defensible cluster-level supervised target exists and current lift clusters are not certified independent destinations."),
        ("Neural network", "Rejected", "Monthly rows do not create independent resorts; the effective cross-sectional sample is far too small."),
        ("K-means plus nearest analogues", "Selected for exploratory Path C", "Uses current undated structural features only, keeps snow vulnerability separate, reports stability/OOD support, and never labels analogue changes as causal uplift."),
    ]
    model_table = "\n".join(
        f"| {name} | {verdict} | {reason} |" for name, verdict, reason in model_rows
    )
    report = f"""# Model feasibility report

Generated reproducibly by `src/data_processing/build_feasibility_report.py`.

## Executive verdict

**Checkpoints 4 and 5 fail under the present design.** The project therefore follows **Path C (weak treatment sample / exploratory decision support)**. Destination scope, reviewed-unit season-by-season membership, monthly hotel capacity, and qualified snow/weather proxies are integrated, but the current donor shortlist is exhausted and the effective treated sample is too small for heterogeneous-effect ML.

No causal model, treatment-effect learner, predicted uplift, composite opportunity score, or neural network is authorised. A separate Path C module now builds current structural segments and descriptive analogues, with out-of-distribution flags and no causal interpretation.

## Effective sample

- The supplied Bergfex layer contains **{metrics['resort_listings_total']} resort listings**. The preserved lift layer has **{metrics['lift_clusters_total']} clusters**, of which **{metrics['lift_clusters_linked_to_resort_listings']}** are linked to at least one listing. Neither number is yet an approved count of independent ski destinations.
- The official current-map snapshot contains **{metrics['official_current_magic_destinations_snapshot']} embedded destinations**; **{metrics['official_current_destinations_candidate_linked']}** have a candidate link to a supplied resort listing. The page headline and press archive refer to more than 100 destinations, so the embedded-list discrepancy must be reviewed rather than silently reconciled.
- Official evidence records **{metrics['documented_base_entry_events']} base-pass entry events**. **{metrics['candidate_linked_base_entry_events']}** have a candidate resort-listing link, but only **{metrics['candidate_linked_base_entries_with_hotel_outcome']}** also point to an OFS hotel municipality.
- Those {metrics['candidate_linked_base_entries_with_hotel_outcome']} events reduce to **{metrics['provisional_treated_municipalities_with_hotel_outcome']} municipalities**. This municipality count, not the {metrics['hotel_observed_month_rows']:,} observed monthly rows, is the more relevant upper bound for treatment heterogeneity.
- The 18 candidate links collapse to **{metrics['reviewed_destination_units']} reviewed destination units**. **{metrics['reviewed_destination_units_in_outcome_panel']}** enter a diagnostic outcome panel; **{metrics['reviewed_destination_units_excluded_incomplete_scope']}** composite destinations are excluded because the supplied hotel panel does not cover their full reviewed scope.
- The reviewed panel has **{metrics['reviewed_destination_month_rows']:,} destination-month rows**, of which **{metrics['reviewed_observed_destination_months']:,}** have a complete aggregated hotel-night outcome.
- **Zero** treatment units are approved for causal estimation. The reviewed geography and annual membership are evidence inputs, while treatment intensity, confounding, spillovers, and control status remain unresolved.

## Outcome coverage

- The cleaned OFS-derived panel has **{metrics['hotel_municipalities_total']} municipalities**.
- Observed hotel-night values run from **{metrics['hotel_observed_start']}** through **{metrics['hotel_observed_end']}**; later 2026 grid rows are missing and are not counted as observed.
- Resort points reach **{metrics['hotel_municipalities_reached_by_resort_point']}** hotel municipalities.
- Resolved historical/current Magic links reduce the 74-municipality resort-point universe to an upper bound of **{metrics['control_municipalities_upper_bound_after_resolved_magic_links']}** apparent controls. The **{metrics['unresolved_official_base_entry_labels']}** base-entry labels without one-to-one supplied-directory links have all received conservative scope classifications; the remaining problem is not an unreviewed label backlog but the absence of identity-equivalent mappings and a valid donor pool. **Zero controls are approved.**

## Provisional pre/post windows

For coverage diagnostics only, the script anchors the founding 2017/18 season at 2017-11-01 and later annual seasons at 1 May of their first year. These are not accepted treatment dates. A documented exit bounds Crans-Montana's active post period. The separate reviewed-unit continuity audit now documents all active seasons for the 14 reviewed units, without converting annual membership into an exact treatment date or intensity.

- Season-only candidate events with at least 24 observed pre months: **{metrics['treated_with_season_only_and_24_months_pre']}**
- With at least 36 observed pre months: **{metrics['treated_with_season_only_and_36_months_pre']}**
- With at least 24 potentially post-entry months: **{metrics['treated_with_season_only_and_24_months_post_potential']}**
- With at least 36 potentially post-entry months: **{metrics['treated_with_season_only_and_36_months_post_potential']}**
- Distinct provisional anchors: **{metrics['unique_provisional_treatment_anchors']}**
- Treated units with an exact entry date: **0**

The provisional event-level audit is in `reports/provisional_treatment_window_coverage.csv`. The stricter destination-unit review superseding raw event counts is in `reports/destination_unit_review.csv`:

- Reviewed units with at least 24 observed pre months and 24 active post months under the explicit continuity assumption: **{metrics['reviewed_units_with_24_pre_and_post_months_assumption']}**
- Reviewed units with at least 36 observed pre months and 36 active post months under that assumption: **{metrics['reviewed_units_with_36_pre_and_post_months_assumption']}**

These are coverage counts, not an identification claim.

## Hotel-capacity diagnostic

The official HESTA supply table contributes **{metrics['hotel_capacity_municipality_month_rows']:,} municipality-month rows**; **{metrics['hotel_capacity_complete_supply_rows']:,}** have establishments, rooms, and beds observed. After reviewed destination aggregation, **{metrics['reviewed_destination_months_complete_capacity']:,} of {metrics['reviewed_destination_month_rows']:,}** destination-month rows have complete capacity scope.

For each destination, `reports/hotel_capacity_treatment_diagnostics.csv` compares the last 24 observed pre-anchor months with the first 24 observed active-post months under the explicit continuity assumption. It reports separate changes in live-table overnight stays, available beds, and overnight stays per bed. **{metrics['reviewed_units_with_complete_24pre_24post_capacity_window']} units** have both complete 24-month capacity windows.

This is a descriptive diagnostic only. The adjacent windows are not seasonally or trend adjusted, early post-periods can overlap COVID, and annual membership does not establish constant treatment intensity. Capacity integration therefore helps distinguish demand changes from contemporaneous supply changes but does not identify a Magic Pass effect.

## Snow proxy coverage

The official SLF historical archive contains daily observations for **{metrics['slf_snow_stations_with_daily_data']} snow stations**. The project predeclares an 80% November–April coverage gate over 2013/14–2025/26; **{metrics['slf_snow_stations_passing_longitudinal_gate']} stations** pass. Every resort listing is mapped to the geographically nearest passing station, while distance and the elevation gap to the published resort top remain visible. **{metrics['resorts_with_snow_climate_feature_ready']} of {metrics['resort_listings_total']} listings** have high/moderate proxy comparability and at least ten usable winters.

The reviewed panel contains **{metrics['reviewed_destination_months_complete_snow_proxy']:,} complete station-proxy months**; **{metrics['observed_outcome_rows_with_complete_snow_proxy']:,} rows** also have an observed hotel-night outcome. These fields support descriptive climate adjustment and future robustness checks only. IMIS stations serve avalanche monitoring and can differ materially from pistes in terrain, aspect, wind, elevation, grooming, and snowmaking. No snow field is yet an approved causal covariate.

A next-nearest-station sensitivity covers all **{metrics['reviewed_resort_components_with_alternative_snow_station_test']} reviewed resort components** using the same station coverage gate. **{metrics['alternative_snow_station_high_or_moderate_agreement']} components** receive a high or moderate descriptive agreement grade and **{metrics['alternative_snow_station_low_agreement']}** receive a low grade. The median winter-depth correlation is **{metrics['alternative_snow_station_median_depth_correlation']:.3f}**, but the median relative mean absolute depth difference is **{metrics['alternative_snow_station_median_relative_depth_difference']:.1%}**; absolute snow levels are therefore materially station-dependent even when seasonal variation co-moves. See `reports/13_SNOW_PROXY_SENSITIVITY.md`. This test does not approve the snow covariate, and an independent gridded-source sensitivity remains pending.

## Temperature and precipitation proxy coverage

Official MeteoSwiss inventory metadata identifies **{metrics['meteoswiss_candidate_stations_with_core_parameters_since_2013']} current SwissMetNet stations** whose daily mean/minimum/maximum temperature and 06:00-to-06:00 UTC precipitation series start by the analysis date and have no recorded end. Nearest-station assignment for the reviewed resort components requires **{metrics['meteoswiss_selected_weather_stations']} stations**.

The reviewed panel contains **{metrics['reviewed_destination_months_complete_weather_proxy']:,} complete weather-proxy months**; **{metrics['observed_outcome_rows_with_complete_weather_proxy']:,} rows** also have an observed hotel-night outcome. Station-specific calendar-month anomalies use 2013–2025 usable observations. Two station-months fail the 80% precipitation coverage gate and remain missing. These are regional station proxies, not piste microclimate or snowfall-phase measures, and no weather field is yet approved as a causal covariate.

## Temporal controls

A deterministic calendar table covers **{metrics['temporal_control_month_rows']} months** from January 2013 through December 2026 and joins to **{metrics['reviewed_destination_months_with_temporal_controls']:,} of {metrics['reviewed_destination_month_rows']:,} reviewed destination-month rows**. It records calendar month/quarter, winter and summer indicators, the December/January holiday peak, and the Gregorian Easter month.

The table also flags March 2020 through April 2022 as a deliberately broad COVID sensitivity interval. This marks **{metrics['reviewed_destination_months_in_covid_sensitivity_interval']:,} reviewed destination-month rows**. It is not a legal chronology of canton-specific restrictions or travel rules. Any later event-study diagnostic must therefore report at least a full-sample specification, exclusion of this broad interval, and documented alternative period definitions; the flag does not by itself remove COVID confounding.

## Same-destination distance gradient

Following the researcher's proposed comparison, the pipeline now measures each of 186 hotel municipality series against the component resort points of each reviewed treated destination while keeping that destination fixed. The resulting **{metrics['same_destination_distance_crosswalk_rows']:,} destination–municipality rows** retain both representative-point and minimum-polygon distance. For the seven continuity-plus-24/24 destinations, **{metrics['same_destination_distance_gradient_usable_rows']:,} municipality rows** have at least 18 observed months in both adjacent 24-month windows.

**{metrics['positive_descriptive_near_far_contrasts']} of seven** treatment-specific near-versus-far contrasts are descriptively positive when municipalities at most 30 km away are compared with municipalities beyond 50 km and the 30–50 km band is omitted. Moléson is the exception. This pattern is exploratory only: current 2026 boundaries are applied to historical outcomes, hotel locations and validated historical origin-to-destination travel times are unavailable, and the adjacent windows do not remove common shocks, COVID, competing passes or investment. See `reports/15_TREATMENT_DISTANCE_GRADIENT.md`; all effect and exposure approval flags remain false.

## NPVM zone-proxy audit

All **{metrics['npvm_proxy_listing_points_geometrically_reconstructed']}** municipality-constrained NPVM listing-point assignments are exactly reconstructed against the checksum-verified zone and current municipality geometries. They affect **{metrics['npvm_proxy_clusters']} clusters**; **{metrics['npvm_proxy_only_clusters']}** have no exact listing-point assignment for an internal comparison, including **{metrics['npvm_proxy_only_candidate_clusters']}** apparent Path C candidates. The geometry and deterministic choice are validated, but proxy-only travel times are not independently validated observed routes. Historical zone lineage and causal approval remain false. See `reports/27_TRANSPORT_ZONE_PROXY_AUDIT.md`.

## Scheduled public-transport journey context

The official winter-2026 Swiss GTFS timetable now supplies **{metrics['public_transport_journey_samples']:,} scheduled routing requests** across **{metrics['public_transport_journey_pairs']:,} destination–municipality pairs**. Morning departures are sampled from 08:00 to 10:00 and return departures from 15:00 to 18:00 on one winter weekday and one winter Saturday. **{metrics['public_transport_journey_feasible_samples']:,} samples** meet the six-vehicle and eight-hour limits; **{metrics['public_transport_journey_pairs_complete_all_samples']:,} pairs** are feasible at every sampled time. Municipality origins use the most frequently served train stop inside the municipality where possible, with a terrestrial-stop fallback. All **{metrics['public_transport_arrival_nodes_reviewed']}** component arrival nodes have passed the versioned current name/mode/municipality/distance review for descriptive routing; **{metrics['public_transport_arrival_village_or_local_centre_proxies']}** are transparently retained as village/local-centre proxies under the researcher's fallback rule, and **{metrics['public_transport_arrival_nodes_with_reference_day_warning']}** has a reference-day availability warning. This is not historical or causal approval. See `reports/24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md` and `reports/26_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW.md`.

The official archive index exposes snapshots for **{metrics['public_transport_historical_anchor_years']} relevant timetable years**, but **{metrics['public_transport_historical_components_service_compared']} historical component nodes** have yet undergone actual stop/service comparison. The 2026 journey measure is therefore useful descriptive context, not a historically stable pre-treatment or causal covariate. See `reports/25_PUBLIC_TRANSPORT_HISTORICAL_AUDIT.md`.

## Membership-continuity audit

Entry events, full official rosters, named continuation statements, and the documented Crans-Montana exit were checked season by season. Missing annual evidence remains unverified rather than being filled as active or inactive.

- Reviewed units with every active season explicitly documented: **{metrics['reviewed_units_with_fully_documented_membership_continuity']}**
- Such units that also enter the outcome panel: **{metrics['panel_units_with_fully_documented_membership_continuity']}**
- Such panel units with both 24 observed pre months and 24 observed active-post months: **{metrics['fully_documented_panel_units_with_24_pre_and_post_months']}**

The detailed audit is in `reports/membership_continuity_audit.csv`. The final count is an evidence/coverage screen, not a count of identified effects. Seasonal documentation does not establish identical summer access, precise treatment intensity, absence of confounding, or a valid counterfactual. Zero controls and zero treatment units are approved for causal estimation. The additional dated rosters and operator/tourism documents are reviewed in `reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md`.

Annual launch lists and map symbols now classify winter versus summer-winter access for **{metrics['active_unit_seasons_with_individual_winter_summer_evidence']} active destination-unit seasons across {metrics['annual_seasons_with_individual_winter_summer_evidence']} annual publications**. **{metrics['active_unit_seasons_with_documented_summer_access']}** of those unit-seasons have documented summer access for at least one published component label. Composite destinations retain mixed-component labels rather than being flattened. See `reports/10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md`; summer inclusion is not evidence of daily operation or causal tourism exposure.

## Donor/control contamination screen

The pipeline screened **{metrics['treatment_donor_pairs_screened']}** treatment-municipality pairs. A deliberately provisional flag removes known resolved Magic exposure, precautionary composite/overlapping scope risks, the treated municipality scope, donors within 30 km, donors with fewer than 36 observed pre months, and donors with fewer than 24 post months. Resolving the current Sattel-Hochstuckli label exposes one additional Magic-linked municipality. The scope review excludes **{metrics['additional_scope_risk_municipalities_excluded']} additional municipalities**, leaving **{metrics['control_municipalities_upper_bound_after_scope_screen']}** apparent controls and **{metrics['provisional_donor_pairs_30km_36pre']}** pairs passing the 30 km screen; **{metrics['provisional_donor_pairs_50km_36pre']}** survive a 50 km sensitivity screen.

For the seven continuity-plus-coverage treatments, the pre-trend screen ranks **{metrics['donor_pretrend_pairs_screened']}** provisional pairs from the 36 pre-anchor months and retains **{metrics['donor_pretrend_shortlisted_pairs']}** top-five pairs for manual review. The heuristic combines outcome level, deseasonalized trend, seasonality, standardized shape, bed capacity, distance and current resort-directory structure. **Zero are approved causal controls** because network spillovers, accessibility, time-varying confounders and formal balance are not jointly cleared. See `reports/11_DONOR_PRETREND_SCREEN.md`.

The first screen measured distance only to the treatment being evaluated. A network-wide audit now shows that **{metrics['shortlisted_pairs_within_30km_any_resolved_magic']} of the 35 shortlisted pairs** use a donor municipality within 30 km of some historically or currently resolved Magic Pass resort point; only **{metrics['shortlisted_pairs_beyond_50km_any_resolved_magic']} pairs** lie beyond 50 km from every resolved point. This remains a lower-bound proximity screen because scope-classified labels without one-to-one directory links cannot all be represented as points, and distance cannot prove spillovers or their absence. See `reports/14_DONOR_NETWORK_SPILLOVER_AUDIT.md`.

The official-source review uses complete annual Magic Pass rosters to document station-label absence for all **{metrics['beyond_50km_pairs_with_magic_roster_absence']}** geographically remote pairs. Operator and government evidence then excludes **all {metrics['beyond_50km_pairs_excluded_for_local_tourism_shocks']} pairs** because a donor-specific tourism, pricing, access or infrastructure shock overlaps the relevant post window. **{metrics['donor_pairs_remaining_deep_manual_audit']} pairs remain for deep manual audit.** Exact regional-pass operator terms are still qualified, but no exclusion depends on resolving them. See `reports/16_DONOR_EXTERNAL_SHOCK_AUDIT.md`; approved controls remain zero.

See `reports/control_contamination_audit.csv`, `reports/control_candidates_by_treatment.csv`, and `reports/donor_pretrend_shortlist.csv`.

## Model-family decisions

| Model family | Current decision | Evidence-based reason |
|---|---|---|
{model_table}

## Main identification risks

1. Selection into Magic Pass and pre-existing trends are unmeasured.
2. Resort listings, lift clusters, official pass destinations, and tourism municipalities are different units.
3. Several resorts share the same municipality; some destinations span several municipalities.
4. Crans-Montana proves that treatment is not universally absorbing.
5. COVID overlaps the post-period of early entrants and the entry period of later ones.
6. Spillovers may contaminate nearby nominal controls.
7. Hotel capacity, mountain-station snow, regional temperature/precipitation, qualified Swiss straight-line population, NPVM 2025 context, current OFT/BAV stop proximity and winter-2026 scheduled journey context are integrated. Historical timetable stability, snowmaking, cross-border population, investment, local economic conditions, and competing-network changes remain unmeasured.

## Next evidence gate

For Path C, compare the identified historical GTFS anchor feeds with the same routing rules; add motorway and relevant cross-border population context; validate destination catchments for tourism dependence; add competing-pass variables; and obtain dated infrastructure features. The NPVM proxy geometry audit is complete, but 50 proxy-only clusters still lack an internal exact-zone sensitivity reference. If door-to-lift precision becomes necessary, supplement the completed current arrival-node review with walking/access evidence. Keep the completed min/median/max aggregation sensitivity and preserve separate opportunity, vulnerability, comparability and data-quality dimensions. Complete regional-weather and independent gridded-snow sensitivities before elevating climate fields. Any return to Path B requires a redesigned broader donor search, validated treatment intensity/exposure and stronger time-varying confounders. Complex heterogeneous-effect ML remains unjustified unless the effective treated-destination count increases substantially.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
