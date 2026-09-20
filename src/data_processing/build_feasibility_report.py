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
CONTROL_SUMMARY = ROOT / "reports" / "control_audit_summary.json"
CAPACITY_SUMMARY = ROOT / "reports" / "hotel_capacity_summary.json"
SNOW_SUMMARY = ROOT / "reports" / "snow_proxy_summary.json"
WEATHER_SUMMARY = ROOT / "reports" / "weather_proxy_summary.json"
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
    control_summary = json.loads(CONTROL_SUMMARY.read_text(encoding="utf-8"))
    capacity_summary = json.loads(CAPACITY_SUMMARY.read_text(encoding="utf-8"))
    snow_summary = json.loads(SNOW_SUMMARY.read_text(encoding="utf-8"))
    weather_summary = json.loads(WEATHER_SUMMARY.read_text(encoding="utf-8"))
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
        "control_municipalities_upper_bound_after_resolved_magic_links": int(
            control_summary["candidate_control_municipalities_upper_bound"]
        ),
        "treatment_donor_pairs_screened": int(
            control_summary["treatment_donor_pairs_screened"]
        ),
        "provisional_donor_pairs_30km_36pre": int(
            control_summary["provisional_donor_pairs_30km_36pre"]
        ),
        "unresolved_official_base_entry_labels": int(
            control_summary["unresolved_official_base_entry_labels"]
        ),
    }
    pd.DataFrame([{"metric": key, "value": value} for key, value in metrics.items()]).to_csv(
        COUNT_OUTPUT, index=False
    )

    model_rows = [
        ("Municipality fixed-effects panel", "Diagnostic-ready only", "Eleven reviewed outcome units, monthly hotel capacity, SLF snow proxies, and MeteoSwiss temperature/precipitation proxies can be represented, but membership continuity, remaining confounding, spillovers, and controls remain unresolved."),
        ("Staggered Difference-in-Differences", "Not credible yet", "Destination scope is improved, but continuity assumptions and untreated-control status are not validated."),
        ("Matching", "Descriptive only", "May help select analogues after pre-treatment covariates and membership status are completed; it is not yet causal."),
        ("Synthetic control / synthetic DiD", "Case-study candidate", "Could be assessed for a few clearly mapped municipalities with uncontaminated donors; no donor pool is approved yet."),
        ("Causal forest", "Not supported", "At most 14 provisional treated municipalities is far below a defensible heterogeneous-effect sample."),
        ("X-Learner", "Not supported", "The effective treated-unit count is too small and treatment labels are not final."),
        ("DR-Learner", "Not supported", "The effective treated-unit count is too small and nuisance models would be unstable."),
        ("Gradient boosting", "Deferred", "Potentially useful for ordinary prediction after features exist, but not evidence of membership uplift."),
        ("Random forest", "Deferred", "Potentially useful as a grouped predictive benchmark; current independent destination sample is unresolved."),
        ("Neural network", "Rejected", "Monthly rows do not create independent resorts; the effective cross-sectional sample is far too small."),
    ]
    model_table = "\n".join(
        f"| {name} | {verdict} | {reason} |" for name, verdict, reason in model_rows
    )
    report = f"""# Model feasibility report

Generated reproducibly by `src/data_processing/build_feasibility_report.py`.

## Executive verdict

The project currently follows **Path C (weak treatment sample / exploratory decision support)**. This is a checkpoint decision, not a permanent rejection of causal work. Destination scope, monthly hotel capacity, a qualified SLF snow proxy, and qualified MeteoSwiss temperature/precipitation proxies have now been integrated, but a move to Path B still requires complete season-by-season membership and exit histories, the remaining confounders, and an uncontaminated control audit.

No causal model, treatment-effect learner, opportunity score, or neural network should be fitted at this checkpoint.

## Effective sample

- The supplied Bergfex layer contains **{metrics['resort_listings_total']} resort listings**. The preserved lift layer has **{metrics['lift_clusters_total']} clusters**, of which **{metrics['lift_clusters_linked_to_resort_listings']}** are linked to at least one listing. Neither number is yet an approved count of independent ski destinations.
- The official current-map snapshot contains **{metrics['official_current_magic_destinations_snapshot']} embedded destinations**; **{metrics['official_current_destinations_candidate_linked']}** have a candidate link to a supplied resort listing. The page headline and press archive refer to more than 100 destinations, so the embedded-list discrepancy must be reviewed rather than silently reconciled.
- Official evidence records **{metrics['documented_base_entry_events']} base-pass entry events**. **{metrics['candidate_linked_base_entry_events']}** have a candidate resort-listing link, but only **{metrics['candidate_linked_base_entries_with_hotel_outcome']}** also point to an OFS hotel municipality.
- Those {metrics['candidate_linked_base_entries_with_hotel_outcome']} events reduce to **{metrics['provisional_treated_municipalities_with_hotel_outcome']} municipalities**. This municipality count, not the {metrics['hotel_observed_month_rows']:,} observed monthly rows, is the more relevant upper bound for treatment heterogeneity.
- The 18 candidate links collapse to **{metrics['reviewed_destination_units']} reviewed destination units**. **{metrics['reviewed_destination_units_in_outcome_panel']}** enter a diagnostic outcome panel; **{metrics['reviewed_destination_units_excluded_incomplete_scope']}** composite destinations are excluded because the supplied hotel panel does not cover their full reviewed scope.
- The reviewed panel has **{metrics['reviewed_destination_month_rows']:,} destination-month rows**, of which **{metrics['reviewed_observed_destination_months']:,}** have a complete aggregated hotel-night outcome.
- **Zero** treatment units are approved for causal estimation. The reviewed geography is an outcome-scope decision, while membership continuity, confounding, spillovers, and control status remain unresolved.

## Outcome coverage

- The cleaned OFS-derived panel has **{metrics['hotel_municipalities_total']} municipalities**.
- Observed hotel-night values run from **{metrics['hotel_observed_start']}** through **{metrics['hotel_observed_end']}**; later 2026 grid rows are missing and are not counted as observed.
- Resort points reach **{metrics['hotel_municipalities_reached_by_resort_point']}** hotel municipalities.
- Resolved historical/current Magic links reduce the 74-municipality resort-point universe to an upper bound of **{metrics['control_municipalities_upper_bound_after_resolved_magic_links']}** apparent controls. This is not a clean donor pool: **{metrics['unresolved_official_base_entry_labels']}** official base-entry labels remain unresolved, and **zero controls are approved**.

## Provisional pre/post windows

For coverage diagnostics only, the script anchors the founding 2017/18 season at 2017-11-01 and later annual seasons at 1 May of their first year. These are not accepted treatment dates. A documented exit bounds Crans-Montana's active post period; continuity for all other events remains unverified.

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

This is a descriptive diagnostic only. The adjacent windows are not seasonally or trend adjusted, early post-periods can overlap COVID, and membership continuity remains assumed. Capacity integration therefore helps distinguish demand changes from contemporaneous supply changes but does not identify a Magic Pass effect.

## Snow proxy coverage

The official SLF historical archive contains daily observations for **{metrics['slf_snow_stations_with_daily_data']} snow stations**. The project predeclares an 80% November–April coverage gate over 2013/14–2025/26; **{metrics['slf_snow_stations_passing_longitudinal_gate']} stations** pass. Every resort listing is mapped to the geographically nearest passing station, while distance and the elevation gap to the published resort top remain visible. **{metrics['resorts_with_snow_climate_feature_ready']} of {metrics['resort_listings_total']} listings** have high/moderate proxy comparability and at least ten usable winters.

The reviewed panel contains **{metrics['reviewed_destination_months_complete_snow_proxy']:,} complete station-proxy months**; **{metrics['observed_outcome_rows_with_complete_snow_proxy']:,} rows** also have an observed hotel-night outcome. These fields support descriptive climate adjustment and future robustness checks only. IMIS stations serve avalanche monitoring and can differ materially from pistes in terrain, aspect, wind, elevation, grooming, and snowmaking. No snow field is yet an approved causal covariate.

## Temperature and precipitation proxy coverage

Official MeteoSwiss inventory metadata identifies **{metrics['meteoswiss_candidate_stations_with_core_parameters_since_2013']} current SwissMetNet stations** whose daily mean/minimum/maximum temperature and 06:00-to-06:00 UTC precipitation series start by the analysis date and have no recorded end. Nearest-station assignment for the reviewed resort components requires **{metrics['meteoswiss_selected_weather_stations']} stations**.

The reviewed panel contains **{metrics['reviewed_destination_months_complete_weather_proxy']:,} complete weather-proxy months**; **{metrics['observed_outcome_rows_with_complete_weather_proxy']:,} rows** also have an observed hotel-night outcome. Station-specific calendar-month anomalies use 2013–2025 usable observations. Two station-months fail the 80% precipitation coverage gate and remain missing. These are regional station proxies, not piste microclimate or snowfall-phase measures, and no weather field is yet approved as a causal covariate.

## Membership-continuity audit

Entry events, full official rosters, named continuation statements, and the documented Crans-Montana exit were checked season by season. Missing annual evidence remains unverified rather than being filled as active or inactive.

- Reviewed units with every active season explicitly documented: **{metrics['reviewed_units_with_fully_documented_membership_continuity']}**
- Such units that also enter the outcome panel: **{metrics['panel_units_with_fully_documented_membership_continuity']}**
- Such panel units with both 24 observed pre months and 24 observed active-post months: **{metrics['fully_documented_panel_units_with_24_pre_and_post_months']}**

The detailed audit is in `reports/membership_continuity_audit.csv`. Its zero in the final line is the decisive reason not to estimate a multi-unit causal effect yet.

## Donor/control contamination screen

The pipeline screened **{metrics['treatment_donor_pairs_screened']}** treatment-municipality pairs. A deliberately provisional flag removes known resolved Magic exposure, the treated municipality scope, donors within 30 km, donors with fewer than 36 observed pre months, and donors with fewer than 24 post months. **{metrics['provisional_donor_pairs_30km_36pre']}** pairs pass that mechanical screen, but **zero are approved causal controls** because unresolved membership, spillovers beyond an arbitrary distance threshold, and time-varying confounders remain.

See `reports/control_contamination_audit.csv` and `reports/control_candidates_by_treatment.csv`.

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
7. Hotel capacity, mountain-station snow, and regional temperature/precipitation proxies are integrated, but snowmaking, accessibility, investment, local economic conditions, and competing-network changes remain unmeasured.

## Next evidence gate

Fill the remaining unverified unit-seasons, resolve the unmatched official entry labels, add the remaining time-varying confounders, validate weather/snow proxy sensitivity, and replace the mechanical donor screen with a documented membership/spillover audit. Only then reassess fixed-effects/event-study or case-study synthetic-control feasibility. Complex heterogeneous-effect ML remains unjustified unless the effective treated-destination count increases substantially.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
