"""Build municipality-month Magic Pass accessibility exposure and feasibility.

Current winter-2026 scheduled travel times are held fixed as explicitly agreed.
Multiple station groups may affect the same municipality-month; event-specific
windows retain concurrent exposures instead of assigning one municipality to
one resort.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
GROUP_PATH = ROOT / "data_processed" / "accessibility_station_groups.csv"
EVENT_PATH = ROOT / "data_processed" / "accessibility_station_group_events.csv"
JOURNEY_PATH = ROOT / "data_processed" / "accessibility_station_group_journey_context.csv"
HISTORY_PATH = ROOT / "data_processed" / "magic_pass_membership_history.csv"
HOTEL_PATH = ROOT / "data_processed" / "hotel_municipality_month_enriched.csv"
MUNICIPALITY_PATH = ROOT / "reports" / "accessibility_expansion_municipality_inventory.csv"
MONTH_OUTPUT = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
WINDOW_OUTPUT = ROOT / "data_processed" / "accessibility_station_group_event_window.csv"
PAIR_DIAGNOSTIC_OUTPUT = ROOT / "data_processed" / "accessibility_station_group_pair_diagnostic.csv"
FEASIBILITY_OUTPUT = ROOT / "reports" / "accessibility_station_group_feasibility.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_expansion_feasibility_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "57_EXPOSITIONS_ET_FAISABILITE_ELARGIES_FR.md"
THRESHOLDS = [30, 60, 90, 120]


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().eq("true")


def month_index(series: pd.Series) -> pd.Series:
    dates = pd.to_datetime(series)
    return dates.dt.year * 12 + dates.dt.month


def pipe(values) -> str:
    return "|".join(sorted({str(v) for v in values if str(v)}))


def build_group_timeline(groups: pd.DataFrame, events: pd.DataFrame,
                         history: pd.DataFrame, dates: pd.Series) -> pd.DataFrame:
    first = events.groupby("station_group_id", as_index=False).agg(
        first_effective_month=("effective_month", "min"),
        first_winter_effective_month=("winter_effective_month", "min"),
        first_entry_season=("entry_season", "min"),
        source_entry_event_ids=("event_id", pipe),
        source_entry_labels=("source_resort_name", pipe),
    )
    first = first.merge(groups[["station_group_id", "station_group_name",
                                "component_resort_ids"]], validate="one_to_one")
    exits = history[history.event_type.eq("base_pass_exit")].copy()
    exit_rows = []
    for row in exits.itertuples(index=False):
        gid = f"MP_GROUP_RESORT__{row.candidate_resort_id}"
        if gid in set(groups.station_group_id):
            exit_rows.append({
                "station_group_id": gid,
                "last_active_month": str(row.exit_date)[:7] + "-01",
                "exit_event_id": row.event_id,
                "exit_source_id": row.source_id,
            })
    exit_frame = pd.DataFrame(exit_rows)
    if len(exit_frame) != 1 or exit_frame.station_group_id.iloc[0] != \
            "MP_GROUP_RESORT__crans_montana_crans_montana":
        raise ValueError("Expected the single documented Crans-Montana base exit")
    first = first.merge(exit_frame, on="station_group_id", how="left",
                        validate="one_to_one")
    date_frame = pd.DataFrame({"date": sorted(pd.to_datetime(dates).unique())})
    timeline = first.merge(date_frame, how="cross")
    timeline["first_effective_month"] = pd.to_datetime(timeline.first_effective_month)
    timeline["first_winter_effective_month"] = pd.to_datetime(
        timeline.first_winter_effective_month)
    timeline["last_active_month"] = pd.to_datetime(timeline.last_active_month)
    timeline["assumed_active_base_membership"] = (
        timeline.date.ge(timeline.first_effective_month) &
        (timeline.last_active_month.isna() | timeline.date.le(timeline.last_active_month)))
    timeline["new_station_group_entry"] = timeline.date.eq(timeline.first_effective_month)
    timeline["winter_month"] = timeline.date.dt.month.isin([11, 12, 1, 2, 3, 4])
    timeline["assumed_active_winter_access"] = (
        timeline.assumed_active_base_membership & timeline.winter_month &
        timeline.date.ge(timeline.first_winter_effective_month))
    timeline["new_winter_station_group_entry"] = timeline.date.eq(
        timeline.first_winter_effective_month)
    timeline["membership_continuity_status"] = np.where(
        timeline.last_active_month.notna(),
        "carried_forward_until_documented_exit",
        "assumed_from_first_base_entry_without_complete_annual_continuity_audit")
    timeline["historical_access_status"] = "fixed_current_access_assumption"
    timeline["causal_treatment_approved"] = False
    return timeline


def build_month_panel(groups: pd.DataFrame, journeys: pd.DataFrame,
                      timeline: pd.DataFrame, hotel: pd.DataFrame,
                      municipalities: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pairs = journeys[[
        "station_group_id", "municipality_bfs_id", "boundary_bfs_id_2026",
        "municipality_name", "mean_one_way_generalized_minutes",
        "routing_pair_complete", "descriptive_accessibility_usable",
        *[f"within_{t}_minutes" for t in THRESHOLDS],
    ]].copy()
    pairs["municipality_bfs_id"] = pairs.municipality_bfs_id.astype(int)
    for column in ["routing_pair_complete", "descriptive_accessibility_usable",
                   *[f"within_{t}_minutes" for t in THRESHOLDS]]:
        pairs[column] = as_bool(pairs[column])
    structural = groups[["station_group_id", "ski_area_km_unique_listing_sum",
                         "number_lifts_unique_listing_sum", "structural_data_status"]].copy()
    structural["ski_area_km_unique_listing_sum"] = pd.to_numeric(
        structural.ski_area_km_unique_listing_sum, errors="coerce")
    structural["number_lifts_unique_listing_sum"] = pd.to_numeric(
        structural.number_lifts_unique_listing_sum, errors="coerce")
    long = pairs.merge(timeline[[
        "station_group_id", "date", "first_effective_month",
        "first_winter_effective_month", "last_active_month",
        "assumed_active_base_membership", "new_station_group_entry",
        "winter_month", "assumed_active_winter_access",
        "new_winter_station_group_entry"]],
        on="station_group_id", validate="many_to_many").merge(
            structural, on="station_group_id", validate="many_to_one")
    if len(long) != len(pairs) * hotel.date.nunique():
        raise ValueError("Unexpected station-group/municipality/month expansion")
    long["eligible_pair"] = long.descriptive_accessibility_usable

    base = hotel.copy()
    base["municipality_bfs_id"] = base.municipality_bfs_id.astype(int)
    base["date"] = pd.to_datetime(base.date)
    municipality_flags = municipalities[["municipality_bfs_id", "boundary_bfs_id_2026",
                                         "shared_current_territory"]].copy()
    municipality_flags["municipality_bfs_id"] = municipality_flags.municipality_bfs_id.astype(int)
    municipality_flags["shared_current_territory"] = as_bool(
        municipality_flags.shared_current_territory)
    base = base.merge(municipality_flags, on="municipality_bfs_id", how="left",
                      validate="many_to_one", suffixes=("", "_inventory"))
    result = base.copy()

    for threshold in THRESHOLDS:
        within = long[f"within_{threshold}_minutes"] & long.eligible_pair
        active = within & long.assumed_active_base_membership
        entering = within & long.new_station_group_entry
        winter_active = within & long.assumed_active_winter_access
        winter_entering = within & long.new_winter_station_group_entry
        known_structure = long.structural_data_status.eq(
            "complete_unique_listing_aggregation")
        work = long[["municipality_bfs_id", "date"]].copy()
        work[f"active_station_group_count_{threshold}min"] = active.astype(int)
        work[f"new_station_group_entry_count_{threshold}min"] = entering.astype(int)
        work[f"active_winter_station_group_count_{threshold}min"] = winter_active.astype(int)
        work[f"new_winter_station_group_entry_count_{threshold}min"] = winter_entering.astype(int)
        work[f"active_groups_with_structure_count_{threshold}min"] = (
            active & known_structure).astype(int)
        work[f"active_groups_missing_structure_count_{threshold}min"] = (
            active & ~known_structure).astype(int)
        work[f"active_ski_area_km_known_sum_{threshold}min"] = np.where(
            active & known_structure, long.ski_area_km_unique_listing_sum, 0.0)
        work[f"active_lifts_known_sum_{threshold}min"] = np.where(
            active & known_structure, long.number_lifts_unique_listing_sum, 0.0)
        work[f"nearest_active_group_minutes_{threshold}min"] = np.where(
            active, long.mean_one_way_generalized_minutes, np.nan)
        aggregated = work.groupby(["municipality_bfs_id", "date"], as_index=False).agg({
            f"active_station_group_count_{threshold}min": "sum",
            f"new_station_group_entry_count_{threshold}min": "sum",
            f"active_winter_station_group_count_{threshold}min": "sum",
            f"new_winter_station_group_entry_count_{threshold}min": "sum",
            f"active_groups_with_structure_count_{threshold}min": "sum",
            f"active_groups_missing_structure_count_{threshold}min": "sum",
            f"active_ski_area_km_known_sum_{threshold}min": "sum",
            f"active_lifts_known_sum_{threshold}min": "sum",
            f"nearest_active_group_minutes_{threshold}min": "min",
        })
        result = result.merge(aggregated, on=["municipality_bfs_id", "date"],
                              how="left", validate="one_to_one")

    result["multiple_active_groups_120min"] = result.active_station_group_count_120min.gt(1)
    result["any_new_group_entry_120min"] = result.new_station_group_entry_count_120min.gt(0)
    result["winter_month"] = result.date.dt.month.isin([11, 12, 1, 2, 3, 4])
    result["current_access_fixed"] = True
    result["public_transport_exposure_source_id"] = (
        "DERIVED_ACCESSIBILITY_STATION_GROUP_JOURNEYS")
    result["membership_exposure_source_id"] = (
        "DERIVED_ACCESSIBILITY_STATION_GROUP_EVENTS")
    result["causal_exposure_approved"] = False
    if len(result) != len(hotel) or result.duplicated(
            ["municipality_bfs_id", "date"]).any():
        raise ValueError("Municipality-month output lost its 31,248-row grain")
    return result, pairs


def other_entry_gap_table(qualified: pd.DataFrame,
                          timeline: pd.DataFrame) -> pd.DataFrame:
    anchors = timeline[["station_group_id", "first_effective_month"]].drop_duplicates()
    pairs = qualified[["station_group_id", "municipality_bfs_id"]].merge(
        anchors, on="station_group_id", validate="many_to_one")
    rows = []
    for municipality, group in pairs.groupby("municipality_bfs_id"):
        values = group[["station_group_id", "first_effective_month"]].to_records(index=False)
        for gid, anchor in values:
            gaps = [abs((pd.Timestamp(anchor).year - pd.Timestamp(other_anchor).year) * 12 +
                        pd.Timestamp(anchor).month - pd.Timestamp(other_anchor).month)
                    for other_gid, other_anchor in values if other_gid != gid]
            rows.append({
                "station_group_id": gid,
                "municipality_bfs_id": int(municipality),
                "nearest_other_entry_gap_months_120min": min(gaps) if gaps else pd.NA,
                "other_entry_within_12_months_120min": bool(gaps and min(gaps) <= 12),
            })
    return pd.DataFrame(rows)


def build_event_window(groups: pd.DataFrame, journeys: pd.DataFrame,
                       timeline: pd.DataFrame, month_panel: pd.DataFrame,
                       hotel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    journeys = journeys.copy()
    for column in ["descriptive_accessibility_usable", "within_30_minutes",
                   "within_60_minutes", "within_90_minutes", "within_120_minutes",
                   "routing_pair_complete"]:
        journeys[column] = as_bool(journeys[column])
    qualified = journeys[
        journeys.descriptive_accessibility_usable & journeys.within_120_minutes
    ].copy()
    anchors = timeline[["station_group_id", "station_group_name",
                        "first_effective_month", "last_active_month",
                        "membership_continuity_status"]].drop_duplicates()
    qualified = qualified.merge(anchors, on=["station_group_id", "station_group_name"],
                                validate="many_to_one")
    dates = pd.DataFrame({"event_time_months": range(-36, 37)})
    window = qualified.merge(dates, how="cross")
    anchor_period = pd.PeriodIndex(pd.to_datetime(window.first_effective_month), freq="M")
    window["date"] = [
        (period + int(offset)).to_timestamp()
        for period, offset in zip(anchor_period, window.event_time_months)
    ]
    hotel_copy = hotel.copy()
    hotel_copy["municipality_bfs_id"] = hotel_copy.municipality_bfs_id.astype(int)
    hotel_copy["date"] = pd.to_datetime(hotel_copy.date)
    keep_hotel = [
        "municipality_bfs_id", "date", "hotel_overnights", "hotel_arrivals",
        "domestic_overnights", "foreign_overnights", "log_overnights",
        "hotel_establishments_open", "hotel_rooms_available",
        "hotel_beds_available", "hotel_overnights_per_available_bed_month",
    ]
    window = window.merge(hotel_copy[keep_hotel], on=["municipality_bfs_id", "date"],
                          how="left", validate="many_to_one")
    exposure_cols = ["municipality_bfs_id", "date",
                     "active_station_group_count_120min",
                     "new_station_group_entry_count_120min"]
    window = window.merge(month_panel[exposure_cols],
                          on=["municipality_bfs_id", "date"], how="left",
                          validate="many_to_one")
    window["group_assumed_active"] = (
        window.date.ge(pd.to_datetime(window.first_effective_month)) &
        (window.last_active_month.isna() |
         window.date.le(pd.to_datetime(window.last_active_month))))
    window["other_active_group_count_120min"] = np.where(
        window.active_station_group_count_120min.notna(),
        (window.active_station_group_count_120min -
         window.group_assumed_active.astype(int)).clip(lower=0),
        np.nan)
    window["other_group_entry_same_month_count_120min"] = np.where(
        window.new_station_group_entry_count_120min.notna(),
        (window.new_station_group_entry_count_120min -
         window.event_time_months.eq(0).astype(int)).clip(lower=0),
        np.nan)
    gaps = other_entry_gap_table(qualified, timeline)
    window = window.merge(gaps, on=["station_group_id", "municipality_bfs_id"],
                          validate="many_to_one")
    window = window.merge(groups[[
        "station_group_id", "scope_status", "component_resort_ids",
        "ski_area_km_unique_listing_sum", "number_lifts_unique_listing_sum",
        "structural_data_status"]], on="station_group_id", validate="many_to_one")
    window["post_entry"] = window.event_time_months.ge(0)
    window["current_access_fixed"] = True
    window["causal_interpretation_approved"] = False
    window = window.sort_values(["station_group_id", "municipality_bfs_id",
                                 "event_time_months"], kind="stable")

    observed = pd.to_numeric(window.hotel_overnights, errors="coerce").notna()
    window["observed_hotel_overnights"] = observed
    diagnostic_rows = []
    for (gid, bfs_id), pair in window.groupby(
            ["station_group_id", "municipality_bfs_id"], sort=False):
        pre = pair[pair.event_time_months.between(-24, -1)]
        post = pair[pair.event_time_months.between(0, 23)]
        pre_log = pd.to_numeric(pre.log_overnights, errors="coerce")
        post_log = pd.to_numeric(post.log_overnights, errors="coerce")
        pre_nights = pd.to_numeric(pre.hotel_overnights, errors="coerce")
        post_nights = pd.to_numeric(post.hotel_overnights, errors="coerce")
        pre_count = int(pre_nights.notna().sum())
        post_count = int(post_nights.notna().sum())
        complete = pre_count == 24 and post_count == 24
        first = pair.iloc[0]
        window_start = pd.Timestamp(first.first_effective_month) - pd.DateOffset(months=24)
        window_end = pd.Timestamp(first.first_effective_month) + pd.DateOffset(months=23)
        overlaps_covid = (window_start <= pd.Timestamp("2022-04-01") and
                          window_end >= pd.Timestamp("2020-03-01"))
        pre_mean_nights = float(pre_nights.mean()) if pre_count else np.nan
        post_mean_nights = float(post_nights.mean()) if post_count else np.nan
        diagnostic_rows.append({
            "station_group_id": gid,
            "station_group_name": first.station_group_name,
            "municipality_bfs_id": int(bfs_id),
            "municipality_name": first.municipality_name,
            "first_effective_month": first.first_effective_month,
            "mean_one_way_generalized_minutes": first.mean_one_way_generalized_minutes,
            **{f"within_{threshold}_minutes": bool(first[f"within_{threshold}_minutes"])
               for threshold in THRESHOLDS},
            "observed_pre_24_months": pre_count,
            "observed_post_24_months": post_count,
            "complete_24_pre_24_post": complete,
            "pre_24_mean_hotel_overnights": pre_mean_nights,
            "post_24_mean_hotel_overnights": post_mean_nights,
            "descriptive_log_change_post24_minus_pre24": (
                float(post_log.mean() - pre_log.mean()) if complete else np.nan),
            "descriptive_mean_nights_pct_change": (
                float((post_mean_nights / pre_mean_nights - 1) * 100)
                if complete and pre_mean_nights > 0 else np.nan),
            "other_entry_within_12_months_120min": bool(
                first.other_entry_within_12_months_120min),
            "entry_window_overlaps_covid_sensitivity": overlaps_covid,
            "current_access_fixed": True,
            "causal_interpretation_approved": False,
        })
    pair_coverage = pd.DataFrame(diagnostic_rows)

    feasibility = groups[["station_group_id", "station_group_name",
                          "first_entry_season", "first_effective_month",
                          "scope_status", "structural_data_status"]].copy()
    pair_counts = []
    for gid, group in journeys.groupby("station_group_id"):
        row = {"station_group_id": gid,
               "municipality_pairs_total": len(group),
               "municipality_pairs_complete": int(group.routing_pair_complete.sum()),
               "municipality_pairs_descriptive_usable": int(
                   group.descriptive_accessibility_usable.sum())}
        for threshold in THRESHOLDS:
            row[f"municipalities_within_{threshold}min"] = int(
                (group.descriptive_accessibility_usable &
                 group[f"within_{threshold}_minutes"]).sum())
        pair_counts.append(row)
    feasibility = feasibility.merge(pd.DataFrame(pair_counts),
                                    on="station_group_id", validate="one_to_one")
    coverage_group = pair_coverage.groupby("station_group_id", as_index=False).agg(
        municipality_pairs_120min=("municipality_bfs_id", "size"),
        pairs_complete_24_pre_24_post=("complete_24_pre_24_post", "sum"),
        pairs_with_other_entry_within_12_months=(
            "other_entry_within_12_months_120min", "sum"),
    )
    feasibility = feasibility.merge(coverage_group, on="station_group_id", how="left",
                                    validate="one_to_one").fillna({
        "municipality_pairs_120min": 0,
        "pairs_complete_24_pre_24_post": 0,
        "pairs_with_other_entry_within_12_months": 0,
    })
    feasibility["pairs_without_other_entry_within_12_months"] = (
        feasibility.municipality_pairs_120min -
        feasibility.pairs_with_other_entry_within_12_months)
    feasibility["descriptive_event_window_ready"] = \
        feasibility.pairs_complete_24_pre_24_post.gt(0)
    feasibility["entry_separation_possible_somewhere"] = \
        feasibility.pairs_without_other_entry_within_12_months.gt(0)
    feasibility["causal_treatment_approved"] = False
    for threshold in THRESHOLDS:
        usable = pair_coverage[
            pair_coverage.complete_24_pre_24_post &
            pair_coverage[f"within_{threshold}_minutes"]]
        diagnostic = usable.groupby("station_group_id", as_index=False).agg(
            **{
                f"diagnostic_pairs_{threshold}min": ("municipality_bfs_id", "size"),
                f"median_descriptive_log_change_{threshold}min": (
                    "descriptive_log_change_post24_minus_pre24", "median"),
                f"median_descriptive_nights_pct_change_{threshold}min": (
                    "descriptive_mean_nights_pct_change", "median"),
            })
        feasibility = feasibility.merge(diagnostic, on="station_group_id", how="left",
                                        validate="one_to_one")
        feasibility[f"diagnostic_pairs_{threshold}min"] = feasibility[
            f"diagnostic_pairs_{threshold}min"].fillna(0).astype(int)
    feasibility["descriptive_diagnostic_available"] = \
        feasibility.diagnostic_pairs_120min.gt(0)
    return window, pair_coverage, feasibility


def main() -> None:
    groups = pd.read_csv(GROUP_PATH)
    events = pd.read_csv(EVENT_PATH)
    journeys = pd.read_csv(JOURNEY_PATH)
    history = pd.read_csv(HISTORY_PATH)
    hotel = pd.read_csv(HOTEL_PATH)
    municipalities = pd.read_csv(MUNICIPALITY_PATH)
    if len(groups) != 71 or len(events) != 78 or len(journeys) != 71 * 186:
        raise ValueError("Unexpected expanded station/event/journey universe")
    if len(hotel) != 31_248 or hotel.municipality_bfs_id.nunique() != 186:
        raise ValueError("Unexpected hotel municipality-month universe")
    timeline = build_group_timeline(groups, events, history, hotel.date)
    month_panel, pairs = build_month_panel(groups, journeys, timeline, hotel,
                                           municipalities)
    window, pair_diagnostic, feasibility = build_event_window(
        groups, journeys, timeline, month_panel, hotel)
    month_panel.to_csv(MONTH_OUTPUT, index=False, lineterminator="\n",
                       date_format="%Y-%m-%d")
    window.to_csv(WINDOW_OUTPUT, index=False, lineterminator="\n",
                  date_format="%Y-%m-%d")
    pair_diagnostic.to_csv(PAIR_DIAGNOSTIC_OUTPUT, index=False, lineterminator="\n",
                           date_format="%Y-%m-%d")
    feasibility.to_csv(FEASIBILITY_OUTPUT, index=False, lineterminator="\n")

    entry_months = (events[["station_group_id", "effective_month"]].drop_duplicates()
                    .effective_month.value_counts())
    observed_overnights = month_panel.loc[month_panel.hotel_overnights.notna(), "date"]
    raw_within_120 = as_bool(journeys.within_120_minutes)
    usable_within_120 = raw_within_120 & as_bool(
        journeys.descriptive_accessibility_usable)
    summary = {
        "analysis_date": "2026-10-02",
        "station_groups": 71,
        "municipality_series": 186,
        "municipality_month_rows": len(month_panel),
        "panel_grid_start_month": str(pd.to_datetime(month_panel.date).min().date()),
        "panel_grid_end_month": str(pd.to_datetime(month_panel.date).max().date()),
        "hotel_overnights_last_observed_month": str(
            pd.to_datetime(observed_overnights).max().date()),
        "station_group_municipality_pairs": len(journeys),
        "raw_pairs_within_120min": int(raw_within_120.sum()),
        "raw_groups_with_at_least_one_120min_municipality": int(
            journeys.loc[raw_within_120, "station_group_id"].nunique()),
        "descriptive_usable_pairs_within_120min": int(usable_within_120.sum()),
        "event_window_pairs_within_120min": int(
            window[["station_group_id", "municipality_bfs_id"]].drop_duplicates().shape[0]),
        "event_window_rows": len(window),
        "groups_with_at_least_one_120min_municipality": int(
            feasibility.municipalities_within_120min.gt(0).sum()),
        "groups_with_at_least_one_complete_24_pre_24_post_pair": int(
            feasibility.descriptive_event_window_ready.sum()),
        "groups_with_descriptive_adjacent_24_month_diagnostic": int(
            feasibility.descriptive_diagnostic_available.sum()),
        "groups_with_positive_median_descriptive_log_change_120min": int(
            feasibility.median_descriptive_log_change_120min.gt(0).sum()),
        "groups_with_some_entry_separation_over_12_months": int(
            feasibility.entry_separation_possible_somewhere.sum()),
        "groups_with_missing_directory_listing": int(
            feasibility.structural_data_status.eq("missing_directory_listing").sum()),
        "groups_with_incomplete_directory_structure": int(
            feasibility.structural_data_status.eq("incomplete_unique_listing_aggregation").sum()),
        "municipality_months_with_multiple_active_groups_120min": int(
            month_panel.multiple_active_groups_120min.sum()),
        "municipalities_ever_with_multiple_active_groups_120min": int(
            month_panel.loc[month_panel.multiple_active_groups_120min,
                            "municipality_bfs_id"].nunique()),
        "maximum_simultaneous_active_groups_120min": int(
            month_panel.active_station_group_count_120min.max()),
        "documented_group_exits": 1,
        "entry_group_counts_by_effective_month": {
            str(k): int(v) for k, v in entry_months.sort_index().items()},
        "current_access_fixed": True,
        "road_travel_time_status": "not_built_no_validated_station_pair_road_routing_source",
        "historical_access_audit_status": "deferred_after_initial_tests_by_researcher_decision",
        "causal_treatments_approved": 0,
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [GROUP_PATH, EVENT_PATH, JOURNEY_PATH, HISTORY_PATH,
                         HOTEL_PATH, MUNICIPALITY_PATH]
        },
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")

    ready = feasibility[feasibility.descriptive_event_window_ready]
    unready = feasibility[~feasibility.descriptive_event_window_ready]
    report = f"""# Expositions communales et faisabilité élargie — étapes 7 à 10

## Panel obtenu

Le panel final garde **une ligne par série communale et par mois** : **{len(month_panel):,} lignes**, 186 séries et une grille de 2013-01 à 2026-12. Les nuitées sont observées jusqu'en 2026-03; les mois ultérieurs restent dans la grille avec une issue manquante et ne sont pas traités comme des zéros. Une commune n'est plus assignée à une station unique. Elle peut être exposée simultanément à plusieurs groupes Magic Pass accessibles.

Les origines communales existantes sont réutilisées : gare ferroviaire desservie ayant le plus de départs dans la commune actuelle; à défaut, arrêt terrestre le plus desservi, puis arrêt desservi le plus proche. Il s'agit d'un point de référence de transport du centre communal, et non d'une affirmation que tous les hôtels se situent à cet arrêt. Moutier BE et Moutier JU gardent leurs deux séries sources mais partagent explicitement le même territoire communal actuel.

Pour chaque mois, quatre variantes sont conservées : temps moyen aller simple ≤ 30, 60, 90 et 120 minutes. Chacune contient le nombre de groupes actifs, les nouvelles entrées, les pistes/remontées connues cumulées sans doublon et le temps du groupe actif le plus proche. Le seuil n'est donc pas choisi à l'avance; il pourra être testé en sensibilité.

La matrice brute compte **{summary['raw_pairs_within_120min']:,} couples** et **{summary['raw_groups_with_at_least_one_120min_municipality']} groupes** avec au moins une commune à 120 minutes. Après la règle de qualité des nœuds et des trajets, **{summary['descriptive_usable_pairs_within_120min']:,} couples** et **{summary['groups_with_at_least_one_120min_municipality']} groupes** alimentent les fenêtres descriptives. Cette différence est conservée plutôt que masquée.

Deux temporalités sont distinguées. L'ancrage principal reprend la convention du projet : novembre 2017 pour le pass fondateur, puis mai de la saison d'entrée comme début commercial analytique. Une variante hivernale commence en novembre de chaque première saison et ne compte que novembre–avril. Elle évite d'interpréter automatiquement une adhésion au réseau comme une ouverture estivale de toutes les remontées.

## Entrées multiples

- couples groupe–commune à ≤ 120 minutes utilisables dans une fenêtre d'événement : **{summary['event_window_pairs_within_120min']:,}**;
- lignes de fenêtre -36 à +36 mois : **{len(window):,}**;
- communes connaissant au moins une fois plusieurs groupes actifs à ≤ 120 minutes : **{summary['municipalities_ever_with_multiple_active_groups_120min']}**;
- maximum simultané : **{summary['maximum_simultaneous_active_groups_120min']} groupes**.

La table événementielle contient, pour chaque entrée de groupe et chaque commune accessible, le nombre d'autres groupes déjà actifs, les autres entrées le même mois et l'écart à l'entrée voisine. On peut donc estimer séparément une entrée seulement lorsque son calendrier apporte de la variation; les entrées simultanées restent un effet conjoint.

Un premier diagnostic adjacent compare aussi, pour chaque couple complet, la moyenne des 24 mois après à celle des 24 mois avant. **{summary['groups_with_descriptive_adjacent_24_month_diagnostic']} groupes** ont au moins un tel couple à 120 minutes. Cette variation brute équilibre les saisons sur deux années mais ne corrige ni les tendances, ni le COVID, ni les entrées concurrentes : elle n'est pas un effet Magic Pass.

## Faisabilité

| Contrôle | Groupes |
|---|---:|
| Au moins une commune hôtelière à ≤ 120 min avec accès descriptivement utilisable | {summary['groups_with_at_least_one_120min_municipality']} / 71 |
| Au moins un couple avec 24 mois observés avant et 24 après | {summary['groups_with_at_least_one_complete_24_pre_24_post_pair']} / 71 |
| Au moins une commune sans autre entrée à ±12 mois | {summary['groups_with_some_entry_separation_over_12_months']} / 71 |
| Fiche structurelle absente | {summary['groups_with_missing_directory_listing']} / 71 |
| Fiche structurelle incomplète | {summary['groups_with_incomplete_directory_structure']} / 71 |
| Traitements causaux approuvés | 0 |

Les groupes sans fenêtre 24/24 sont principalement les entrées récentes : {', '.join(unready.station_group_name.head(12))}{'...' if len(unready) > 12 else ''}. Le fichier de faisabilité donne le diagnostic complet groupe par groupe.

Cette extension augmente fortement la couverture descriptive, mais ne crée pas automatiquement un contrefactuel. Les adhésions fondatrices simultanées, le COVID, les autres changements touristiques et les expositions croisées restent à traiter avant toute estimation causale.

## Hypothèses et travail différé

L'accessibilité de 2026 est tenue fixe pour ces premiers tests, comme convenu. Une seule sortie documentée, Crans-Montana après avril 2020, interrompt le report de l'exposition. Pour les autres groupes, la continuité depuis la première entrée est une hypothèse explicite, pas un fait annuel complètement audité. L'audit historique détaillé reste dans la liste de finition.

Le temps routier automobile n'est pas fabriqué à partir de distance à vol d'oiseau : le projet ne contient pas encore de moteur routier ou de matrice station–commune validée. Le panel actuel repose donc sur le transport public horaire; l'ajout routier est un chantier séparé documenté.

## Fichiers

- `data_processed/accessibility_municipality_month_exposure.csv` : panel commune–mois;
- `data_processed/accessibility_station_group_event_window.csv` : fenêtres groupe–commune -36/+36 mois;
- `data_processed/accessibility_station_group_pair_diagnostic.csv` : premier avant/après descriptif par couple;
- `reports/accessibility_station_group_feasibility.csv` : faisabilité par groupe;
- `reports/accessibility_expansion_feasibility_summary.json` : comptes et empreintes.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
