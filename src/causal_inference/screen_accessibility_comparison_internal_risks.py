"""Screen the 70 historical-access comparison pairs with existing project evidence.

The screen combines network proximity, current scheduled-time context, hotel
capacity discontinuities, documented competing-pass links and already-reviewed
external shocks.  It prioritises the remaining manual review and never clears a
spillover, shock, treatment, control or causal pair.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SHORTLIST_PATH = ROOT / "reports" / "accessibility_historically_screened_pretrend_shortlist.csv"
GEOMETRY_PATH = ROOT / "data_processed" / "municipality_population_geometry_2026.csv"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
GROUPS_PATH = ROOT / "data_processed" / "accessibility_station_groups.csv"
ACCESS_POINTS_PATH = ROOT / "data_processed" / "accessibility_station_access_points.csv"
JOURNEYS_PATH = ROOT / "data_processed" / "accessibility_station_group_journey_context.csv"
CAPACITY_PATH = ROOT / "data_processed" / "hotel_capacity_municipality_month.csv"
RESORT_POINTS_PATH = ROOT / "data_processed" / "resort_point_municipality.csv"
PASS_HISTORY_PATH = ROOT / "data_processed" / "resort_competing_pass_history.csv"
EXISTING_SHOCK_PATH = ROOT / "reports" / "donor_external_shock_evidence.csv"

PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_comparison_internal_risk_screen.csv"
CONTROL_OUTPUT = ROOT / "reports" / "accessibility_comparison_control_internal_diagnostics.csv"
WORKLIST_OUTPUT = ROOT / "reports" / "accessibility_comparison_external_review_worklist.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_comparison_internal_risk_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "65_SCREENING_INTERNE_RISQUES_COMPARAISONS_FR.md"

ANCHOR = pd.Timestamp("2017-11-01")
PRE_START = pd.Timestamp("2015-11-01")
PRE_END = pd.Timestamp("2017-10-01")
POST_START = ANCHOR
POST_END = pd.Timestamp("2019-10-01")
PASS_SEASONS = {"2017/2018", "2018/2019"}
MEAN_CAPACITY_WARNING = 0.20
YOY_CAPACITY_WARNING = 0.50


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.strip().str.lower().eq("true")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2.astype(float))
    lon2_rad = np.radians(lon2.astype(float))
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad
    value = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
    )
    return 6371.0088 * 2 * np.arcsin(np.sqrt(value))


def distance_band(distance: float) -> str:
    if distance <= 20:
        return "within_20km"
    if distance <= 30:
        return "20_to_30km"
    if distance <= 50:
        return "30_to_50km"
    return "beyond_50km"


def percent_change(before: float, after: float) -> float:
    if not np.isfinite(before) or not np.isfinite(after) or before <= 0:
        return np.nan
    return float(after / before - 1)


def capacity_diagnostics(capacity: pd.DataFrame, municipality_id: int) -> dict:
    subset = capacity[
        capacity.municipality_bfs_id.eq(municipality_id)
        & capacity.date.between(PRE_START, POST_END)
    ].sort_values("date").copy()
    pre = subset[subset.date.between(PRE_START, PRE_END)]
    post = subset[subset.date.between(POST_START, POST_END)]
    pre_beds = float(pre.hotel_beds_available.mean())
    post_beds = float(post.hotel_beds_available.mean())
    pre_establishments = float(pre.hotel_establishments_open.mean())
    post_establishments = float(post.hotel_establishments_open.mean())
    bed_change = percent_change(pre_beds, post_beds)
    establishment_change = percent_change(pre_establishments, post_establishments)
    log_beds = np.log1p(subset.set_index("date").hotel_beds_available)
    yoy = log_beds - log_beds.shift(12, freq="MS")
    max_yoy = float(yoy.abs().max()) if yoy.notna().any() else np.nan
    warning_reasons = []
    if np.isfinite(bed_change) and abs(bed_change) >= MEAN_CAPACITY_WARNING:
        warning_reasons.append("mean_available_beds_change_at_least_20pct")
    if np.isfinite(establishment_change) and abs(establishment_change) >= MEAN_CAPACITY_WARNING:
        warning_reasons.append("mean_open_establishments_change_at_least_20pct")
    if np.isfinite(max_yoy) and max_yoy >= np.log1p(YOY_CAPACITY_WARNING):
        warning_reasons.append("maximum_year_on_year_bed_change_at_least_50pct")
    return {
        "capacity_pre_observed_months": int(pre.hotel_beds_available.notna().sum()),
        "capacity_post_observed_months": int(post.hotel_beds_available.notna().sum()),
        "pre_mean_hotel_beds_available": pre_beds,
        "post_mean_hotel_beds_available": post_beds,
        "hotel_beds_mean_change_post_vs_pre_pct": bed_change,
        "pre_mean_hotel_establishments_open": pre_establishments,
        "post_mean_hotel_establishments_open": post_establishments,
        "hotel_establishments_mean_change_post_vs_pre_pct": establishment_change,
        "maximum_absolute_year_on_year_log_bed_change": max_yoy,
        "large_hotel_capacity_shift_warning": bool(warning_reasons),
        "hotel_capacity_warning_reasons": "|".join(warning_reasons),
    }


def build_pass_lookup(
    municipality_ids: set[int], resort_points: pd.DataFrame, pass_history: pd.DataFrame
) -> dict[int, dict]:
    points = resort_points.copy()
    points["point_municipality_bfs_id"] = pd.to_numeric(
        points.point_municipality_bfs_id, errors="coerce"
    ).astype("Int64")
    points = points[points.point_municipality_bfs_id.isin(municipality_ids)]
    linked = pass_history[
        pass_history.season.isin(PASS_SEASONS)
        & as_bool(pass_history.historical_competing_pass_link_documented)
    ].copy()
    positive = points[["point_municipality_bfs_id", "resort_id"]].merge(
        linked[
            [
                "resort_id",
                "resort_name_canonical",
                "season",
                "competing_pass_name",
                "official_area_label",
                "source_ids",
            ]
        ],
        on="resort_id",
        how="inner",
        validate="many_to_many",
    )
    result: dict[int, dict] = {}
    for municipality_id in sorted(municipality_ids):
        local_points = points[points.point_municipality_bfs_id.eq(municipality_id)]
        local_positive = positive[
            positive.point_municipality_bfs_id.eq(municipality_id)
        ]
        result[municipality_id] = {
            "supplied_resort_points_in_municipality": int(local_points.resort_id.nunique()),
            "documented_competing_pass_link_in_window": not local_positive.empty,
            "documented_competing_pass_names": "|".join(
                sorted(set(local_positive.competing_pass_name.dropna().astype(str)))
            ),
            "documented_competing_pass_seasons": "|".join(
                sorted(set(local_positive.season.dropna().astype(str)))
            ),
            "documented_competing_pass_resort_ids": "|".join(
                sorted(set(local_positive.resort_id.dropna().astype(str)))
            ),
            "documented_competing_pass_source_ids": "|".join(
                sorted(
                    {
                        source
                        for values in local_positive.source_ids.dropna().astype(str)
                        for source in values.split("|")
                        if source
                    }
                )
            ),
            "competing_pass_internal_evidence_status": (
                "positive_link_for_supplied_resort_point_in_municipality"
                if not local_positive.empty
                else "no_positive_link_in_reviewed_products_not_verified_absence"
                if not local_points.empty
                else "no_supplied_resort_point_in_municipality_not_applicable_as_absence"
            ),
        }
    return result


def build_existing_shock_lookup(shocks: pd.DataFrame) -> tuple[dict[int, dict], set[int]]:
    shocks = shocks.copy()
    shocks["analysis_anchor"] = pd.to_datetime(shocks.analysis_anchor, errors="raise")
    shocks["donor_municipality_bfs_id"] = pd.to_numeric(
        shocks.donor_municipality_bfs_id, errors="raise"
    ).astype(int)
    exact = shocks[shocks.analysis_anchor.eq(ANCHOR)]
    exact_lookup: dict[int, dict] = {}
    for municipality_id, group in exact.groupby("donor_municipality_bfs_id"):
        exact_lookup[int(municipality_id)] = {
            "existing_external_shock_exact_anchor": True,
            "existing_external_shock_status": "|".join(
                sorted(set(group.local_tourism_shock_status.astype(str)))
            ),
            "existing_external_shock_source_ids": "|".join(
                sorted(
                    {
                        source
                        for values in group.review_source_ids.dropna().astype(str)
                        for source in values.split("|")
                        if source
                    }
                )
            ),
            "existing_external_shock_evidence_note": " || ".join(
                sorted(set(group.review_evidence_note.astype(str)))
            ),
        }
    return exact_lookup, set(shocks.donor_municipality_bfs_id.astype(int))


def build_municipality_diagnostics(
    municipality_ids: set[int], names: dict[int, str], geometry: pd.DataFrame,
    groups: pd.DataFrame, access_points: pd.DataFrame, journeys: pd.DataFrame,
    capacity: pd.DataFrame, pass_lookup: dict[int, dict],
    shock_lookup: dict[int, dict], any_shock_ids: set[int],
) -> pd.DataFrame:
    group_dates = groups.assign(
        first_effective_month=pd.to_datetime(groups.first_effective_month, errors="raise")
    )[["station_group_id", "station_group_name", "first_effective_month"]]
    anchor_groups = group_dates[group_dates.first_effective_month.le(ANCHOR)]
    window_groups = group_dates[group_dates.first_effective_month.le(POST_END)]
    window_ids = set(window_groups.station_group_id)
    window_points = access_points[access_points.station_group_id.isin(window_ids)].merge(
        window_groups[["station_group_id", "station_group_name"]],
        on="station_group_id",
        how="left",
        validate="many_to_one",
    )
    if window_points.empty:
        raise ValueError("No station access point is active in the treatment window")
    location = geometry.set_index("boundary_bfs_id_2026")
    usable_journeys = journeys[
        journeys.station_group_id.isin(window_ids)
        & as_bool(journeys.descriptive_accessibility_usable)
    ].copy()
    rows = []
    for municipality_id in sorted(municipality_ids):
        if municipality_id not in location.index:
            raise ValueError(f"Missing current municipality geometry for {municipality_id}")
        place = location.loc[municipality_id]
        distances = haversine_km(
            float(place.municipality_representative_latitude),
            float(place.municipality_representative_longitude),
            window_points.reference_latitude.to_numpy(float),
            window_points.reference_longitude.to_numpy(float),
        )
        nearest_point = window_points.iloc[int(np.argmin(distances))]
        local_journeys = usable_journeys[
            usable_journeys.municipality_bfs_id.eq(municipality_id)
        ].sort_values("mean_one_way_generalized_minutes", kind="stable")
        nearest_time = local_journeys.iloc[0] if not local_journeys.empty else None
        anchor_journeys = local_journeys[
            local_journeys.station_group_id.isin(set(anchor_groups.station_group_id))
        ]
        pass_data = pass_lookup[municipality_id]
        shock_data = shock_lookup.get(
            municipality_id,
            {
                "existing_external_shock_exact_anchor": False,
                "existing_external_shock_status": "",
                "existing_external_shock_source_ids": "",
                "existing_external_shock_evidence_note": "",
            },
        )
        row = {
            "municipality_bfs_id": municipality_id,
            "municipality_name": names[municipality_id],
            "municipality_representative_longitude": float(
                place.municipality_representative_longitude
            ),
            "municipality_representative_latitude": float(
                place.municipality_representative_latitude
            ),
            "minimum_representative_distance_to_window_magic_access_point_km": float(
                distances.min()
            ),
            "nearest_window_magic_station_group_id": nearest_point.station_group_id,
            "nearest_window_magic_station_group_name": nearest_point.station_group_name,
            "network_proximity_band": distance_band(float(distances.min())),
            "current_scheduled_nearest_window_magic_group_minutes": (
                float(nearest_time.mean_one_way_generalized_minutes)
                if nearest_time is not None else np.nan
            ),
            "current_scheduled_nearest_window_magic_group_name": (
                nearest_time.station_group_name if nearest_time is not None else ""
            ),
            "current_scheduled_window_magic_groups_within_120min": int(
                as_bool(local_journeys.within_120_minutes).sum()
            ),
            "current_scheduled_anchor_magic_groups_within_120min": int(
                as_bool(anchor_journeys.within_120_minutes).sum()
            ),
            **capacity_diagnostics(capacity, municipality_id),
            **pass_data,
            **shock_data,
            "existing_external_shock_evidence_other_anchor": bool(
                municipality_id in any_shock_ids
                and municipality_id not in shock_lookup
            ),
            "network_distance_is_spillover_clearance": False,
            "causal_municipality_approved": False,
        }
        rows.append(row)
    return pd.DataFrame(rows).sort_values("municipality_bfs_id", kind="stable")


def triage_pair(row: pd.Series) -> tuple[str, bool, str]:
    flags = []
    if row.control_existing_external_shock_exact_anchor:
        flags.append("documented_control_shock_exact_anchor")
    if row.control_documented_competing_pass_link_in_window:
        flags.append("documented_control_competing_pass_link")
    if row.control_minimum_representative_distance_to_window_magic_access_point_km <= 30:
        flags.append("control_within_30km_of_window_magic_access_point")
    elif row.control_minimum_representative_distance_to_window_magic_access_point_km <= 50:
        flags.append("control_30_to_50km_from_window_magic_access_point")
    if row.treated_control_representative_distance_km <= 30:
        flags.append("treated_control_representatives_within_30km")
    elif row.treated_control_representative_distance_km <= 50:
        flags.append("treated_control_representatives_30_to_50km")
    if row.control_large_hotel_capacity_shift_warning:
        flags.append("control_large_hotel_capacity_shift_warning")
    if row.treated_large_hotel_capacity_shift_warning:
        flags.append("treated_large_hotel_capacity_shift_warning")

    if row.control_existing_external_shock_exact_anchor:
        decision = "exclude_from_priority_existing_documented_control_shock"
        retained = False
    elif row.control_documented_competing_pass_link_in_window:
        decision = "deprioritise_documented_control_competing_pass_link"
        retained = False
    elif row.control_minimum_representative_distance_to_window_magic_access_point_km <= 30:
        decision = "deprioritise_control_network_proximity_within_30km"
        retained = False
    elif row.treated_control_representative_distance_km <= 30:
        decision = "deprioritise_bilateral_proximity_within_30km"
        retained = False
    elif row.control_large_hotel_capacity_shift_warning:
        decision = "retain_for_external_review_with_capacity_warning"
        retained = True
    elif (
        row.control_minimum_representative_distance_to_window_magic_access_point_km <= 50
        or row.treated_control_representative_distance_km <= 50
    ):
        decision = "retain_for_external_review_with_intermediate_proximity_warning"
        retained = True
    else:
        decision = "retain_for_external_review_lower_internal_risk"
        retained = True
    return decision, retained, "|".join(flags)


def main() -> None:
    shortlist = pd.read_csv(SHORTLIST_PATH)
    geometry = pd.read_csv(GEOMETRY_PATH)
    panel = pd.read_csv(PANEL_PATH)
    groups = pd.read_csv(GROUPS_PATH)
    access_points = pd.read_csv(ACCESS_POINTS_PATH)
    journeys = pd.read_csv(JOURNEYS_PATH)
    capacity = pd.read_csv(CAPACITY_PATH)
    capacity["date"] = pd.to_datetime(capacity.date, errors="raise")
    resort_points = pd.read_csv(RESORT_POINTS_PATH)
    pass_history = pd.read_csv(PASS_HISTORY_PATH)
    existing_shocks = pd.read_csv(EXISTING_SHOCK_PATH)

    if len(shortlist) != 70 or shortlist.treated_municipality_bfs_id.nunique() != 14:
        raise ValueError("Expected the 14 x 5 historically screened shortlist")
    treated_ids = set(shortlist.treated_municipality_bfs_id.astype(int))
    control_ids = set(shortlist.control_municipality_bfs_id.astype(int))
    all_ids = treated_ids | control_ids
    names = {
        **dict(
            shortlist[["treated_municipality_bfs_id", "treated_municipality_name"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        ),
        **dict(
            shortlist[["control_municipality_bfs_id", "control_municipality_name"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        ),
    }
    names = {int(key): str(value) for key, value in names.items()}
    panel_ids = set(panel.municipality_bfs_id.astype(int))
    if not all_ids <= panel_ids:
        raise ValueError("A shortlisted municipality is absent from the accessibility panel")

    pass_lookup = build_pass_lookup(all_ids, resort_points, pass_history)
    shock_lookup, any_shock_ids = build_existing_shock_lookup(existing_shocks)
    diagnostics = build_municipality_diagnostics(
        all_ids, names, geometry, groups, access_points, journeys, capacity,
        pass_lookup, shock_lookup, any_shock_ids,
    )
    controls = diagnostics[diagnostics.municipality_bfs_id.isin(control_ids)].copy()
    controls = controls.merge(
        shortlist[
            ["control_municipality_bfs_id", "comparison_candidate_type"]
        ].drop_duplicates(),
        left_on="municipality_bfs_id",
        right_on="control_municipality_bfs_id",
        how="left",
        validate="one_to_one",
    ).drop(columns="control_municipality_bfs_id")
    controls["later_magic_exposure_after_review_window"] = controls[
        "comparison_candidate_type"
    ].eq("not_yet_exposed_during_2015_11_to_2019_10")
    controls["spillover_internal_screen_status"] = (
        "distance_and_current_schedule_screen_completed_not_cleared"
    )
    controls["external_local_shock_review_status"] = np.where(
        controls.existing_external_shock_exact_anchor,
        "completed_existing_exact_anchor_evidence_control_excluded",
        "pending_municipality_specific_external_source_review",
    )
    controls["causal_control_approved"] = False
    controls.to_csv(CONTROL_OUTPUT, index=False, lineterminator="\n")

    treated = diagnostics[diagnostics.municipality_bfs_id.isin(treated_ids)].copy()
    treated_prefix = treated.add_prefix("treated_").rename(
        columns={
            "treated_municipality_bfs_id": "treated_municipality_bfs_id",
            "treated_municipality_name": "treated_diagnostic_municipality_name",
        }
    )
    control_prefix = controls.add_prefix("control_").rename(
        columns={
            "control_municipality_bfs_id": "control_municipality_bfs_id",
            "control_municipality_name": "control_diagnostic_municipality_name",
            "control_comparison_candidate_type": "control_diagnostic_candidate_type",
            "control_causal_control_approved": "control_diagnostic_causal_control_approved",
        }
    )
    pairs = shortlist.merge(
        treated_prefix,
        on="treated_municipality_bfs_id",
        how="left",
        validate="many_to_one",
    ).merge(
        control_prefix,
        on="control_municipality_bfs_id",
        how="left",
        validate="many_to_one",
    )
    pair_distances = []
    for row in pairs.itertuples(index=False):
        pair_distances.append(
            float(
                haversine_km(
                    row.treated_municipality_representative_latitude,
                    row.treated_municipality_representative_longitude,
                    np.array([row.control_municipality_representative_latitude]),
                    np.array([row.control_municipality_representative_longitude]),
                )[0]
            )
        )
    pairs["treated_control_representative_distance_km"] = pair_distances
    triage = pairs.apply(triage_pair, axis=1, result_type="expand")
    triage.columns = [
        "internal_pair_triage_decision",
        "retained_for_external_review",
        "internal_risk_flags",
    ]
    pairs = pd.concat([pairs, triage], axis=1)
    pairs["spillover_review_status"] = (
        "internal_distance_screen_completed_external_market_review_pending"
    )
    pairs["control_external_shock_review_status"] = np.where(
        pairs.control_existing_external_shock_exact_anchor,
        "completed_existing_exact_anchor_evidence_control_excluded",
        "internal_proxy_screen_completed_external_source_review_pending",
    )
    pairs["treated_local_shock_review_status"] = (
        "internal_capacity_proxy_completed_external_source_review_pending"
    )
    pairs["spillover_review_completed"] = False
    pairs["parallel_trends_approved"] = False
    pairs["causal_treatment_approved"] = False
    pairs["causal_control_approved"] = False
    pairs["causal_pair_approved"] = False
    pairs["internal_screen_source_id"] = (
        "DERIVED_ACCESSIBILITY_COMPARISON_INTERNAL_RISK_SCREEN"
    )
    pairs = pairs.sort_values(
        ["treated_municipality_bfs_id", "comparability_rank"], kind="stable"
    )
    if pairs[
        ["causal_treatment_approved", "causal_control_approved", "causal_pair_approved"]
    ].any().any():
        raise ValueError("Internal risk screening must not approve causal rows")
    pairs.to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")

    retained = pairs[as_bool(pairs.retained_for_external_review)].copy()
    control_work = controls.copy()
    pair_stats = pairs.groupby("control_municipality_bfs_id").agg(
        comparison_pair_count=("treated_municipality_bfs_id", "size"),
        retained_pair_count=("retained_for_external_review", lambda value: int(as_bool(value).sum())),
        best_comparability_rank=("comparability_rank", "min"),
        linked_treated_municipalities=(
            "treated_municipality_name", lambda value: "|".join(sorted(set(value.astype(str))))
        ),
    ).reset_index()
    control_work = control_work.merge(
        pair_stats,
        left_on="municipality_bfs_id",
        right_on="control_municipality_bfs_id",
        how="left",
        validate="one_to_one",
    ).drop(columns="control_municipality_bfs_id")
    control_work["entity_role"] = "provisional_control_municipality"
    control_work["external_review_priority"] = np.where(
        control_work.retained_pair_count.gt(0), 1, 3
    )
    control_work["external_review_topics"] = (
        "local_tourism_and_infrastructure_shocks|competing_passes_beyond_reviewed_products|"
        "visitor_market_overlap_and_spillovers|hotel_outcome_scope"
    )

    treated_stats = pairs.groupby("treated_municipality_bfs_id").agg(
        comparison_pair_count=("control_municipality_bfs_id", "size"),
        retained_pair_count=("retained_for_external_review", lambda value: int(as_bool(value).sum())),
        best_comparability_rank=("comparability_rank", "min"),
        linked_treated_municipalities=("treated_municipality_name", "first"),
    ).reset_index()
    treated_work = treated.merge(
        treated_stats,
        left_on="municipality_bfs_id",
        right_on="treated_municipality_bfs_id",
        how="left",
        validate="one_to_one",
    ).drop(columns="treated_municipality_bfs_id")
    treated_work["entity_role"] = "historically_retained_treated_municipality"
    treated_work["external_review_priority"] = np.where(
        treated_work.retained_pair_count.gt(0), 1, 2
    )
    treated_work["external_review_topics"] = (
        "local_tourism_and_infrastructure_shocks|other_pass_or_operator_changes|"
        "hotel_outcome_scope_and_possible_mediators"
    )
    work_columns = [
        "entity_role", "external_review_priority", "municipality_bfs_id",
        "municipality_name", "comparison_pair_count", "retained_pair_count",
        "best_comparability_rank", "linked_treated_municipalities",
        "minimum_representative_distance_to_window_magic_access_point_km",
        "network_proximity_band", "large_hotel_capacity_shift_warning",
        "hotel_capacity_warning_reasons", "documented_competing_pass_link_in_window",
        "documented_competing_pass_names", "existing_external_shock_exact_anchor",
        "existing_external_shock_evidence_other_anchor", "external_review_topics",
    ]
    worklist = pd.concat(
        [treated_work[work_columns], control_work[work_columns]], ignore_index=True
    ).sort_values(
        ["external_review_priority", "entity_role", "retained_pair_count", "municipality_bfs_id"],
        ascending=[True, True, False, True],
        kind="stable",
    )
    worklist["external_review_status"] = np.select(
        [
            worklist.existing_external_shock_exact_anchor,
            worklist.entity_role.eq("provisional_control_municipality")
            & worklist.retained_pair_count.eq(0),
        ],
        [
            "completed_existing_exact_anchor_evidence_control_excluded",
            "deferred_after_internal_deprioritisation",
        ],
        default="pending_external_source_review",
    )
    worklist["causal_entity_approved"] = False
    worklist.to_csv(WORKLIST_OUTPUT, index=False, lineterminator="\n")

    decision_counts = pairs.internal_pair_triage_decision.value_counts().to_dict()
    summary = {
        "analysis_date": "2026-10-03",
        "analysis_anchor": ANCHOR.date().isoformat(),
        "review_window": {
            "pre_start": PRE_START.date().isoformat(),
            "pre_end": PRE_END.date().isoformat(),
            "post_start": POST_START.date().isoformat(),
            "post_end": POST_END.date().isoformat(),
        },
        "historically_screened_pairs": len(pairs),
        "treated_municipalities": len(treated_ids),
        "distinct_control_municipalities": len(control_ids),
        "control_municipalities_with_documented_competing_pass_link_in_window": int(
            controls.documented_competing_pass_link_in_window.sum()
        ),
        "control_municipalities_with_existing_exact_anchor_shock_evidence": int(
            controls.existing_external_shock_exact_anchor.sum()
        ),
        "control_municipalities_with_large_capacity_shift_warning": int(
            controls.large_hotel_capacity_shift_warning.sum()
        ),
        "control_municipalities_within_30km_window_magic_network": int(
            controls.minimum_representative_distance_to_window_magic_access_point_km.le(30).sum()
        ),
        "control_municipalities_within_50km_window_magic_network": int(
            controls.minimum_representative_distance_to_window_magic_access_point_km.le(50).sum()
        ),
        "pair_triage_decision_counts": decision_counts,
        "pairs_retained_for_external_review": len(retained),
        "treated_municipalities_with_at_least_one_retained_pair": int(
            retained.treated_municipality_bfs_id.nunique()
        ),
        "distinct_controls_in_retained_pairs": int(
            retained.control_municipality_bfs_id.nunique()
        ),
        "spillover_reviews_completed": 0,
        "priority_entities_with_external_source_review_pending": int(
            worklist.external_review_status.eq("pending_external_source_review").sum()
        ),
        "entities_deferred_after_internal_deprioritisation": int(
            worklist.external_review_status.eq(
                "deferred_after_internal_deprioritisation"
            ).sum()
        ),
        "entities_with_existing_exact_anchor_review_completed": int(
            worklist.external_review_status.eq(
                "completed_existing_exact_anchor_evidence_control_excluded"
            ).sum()
        ),
        "parallel_trends_approved": False,
        "causal_pairs_approved": 0,
        "thresholds_are_sensitivity_rules": {
            "network_proximity_deprioritisation_km": 30,
            "intermediate_proximity_warning_km": 50,
            "mean_capacity_change_warning_abs_share": MEAN_CAPACITY_WARNING,
            "maximum_year_on_year_capacity_change_warning_abs_share": YOY_CAPACITY_WARNING,
        },
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in [
                SHORTLIST_PATH, GEOMETRY_PATH, PANEL_PATH, GROUPS_PATH, ACCESS_POINTS_PATH,
                JOURNEYS_PATH, CAPACITY_PATH, RESORT_POINTS_PATH,
                PASS_HISTORY_PATH, EXISTING_SHOCK_PATH,
            ]
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# Screening interne des risques des comparaisons — étape 18

## Résultat

Les **{len(pairs)} couples** issus du filtre historique ont été examinés avec les données déjà présentes dans le projet. Le screening combine : distance du point représentatif communal au réseau Magic Pass actif pendant la fenêtre 2017–2019, temps de transport public actuel comme contexte, variation de la capacité hôtelière, liens positifs déjà documentés avec d'autres forfaits multi-stations et preuves de chocs locaux déjà examinées.

| Indicateur interne | Communes de comparaison |
|---|---:|
| À 30 km ou moins d'un point d'accès Magic actif dans la fenêtre | {summary['control_municipalities_within_30km_window_magic_network']} / {len(control_ids)} |
| À 50 km ou moins | {summary['control_municipalities_within_50km_window_magic_network']} / {len(control_ids)} |
| Lien positif documenté avec un forfait concurrent en 2017/18 ou 2018/19 | {summary['control_municipalities_with_documented_competing_pass_link_in_window']} / {len(control_ids)} |
| Choc local déjà sourcé au même ancrage | {summary['control_municipalities_with_existing_exact_anchor_shock_evidence']} / {len(control_ids)} |
| Avertissement de rupture de capacité hôtelière | {summary['control_municipalities_with_large_capacity_shift_warning']} / {len(control_ids)} |

Après cette priorisation, **{len(retained)} couples**, couvrant **{summary['treated_municipalities_with_at_least_one_retained_pair']} communes traitées** et **{summary['distinct_controls_in_retained_pairs']} contrôles distincts**, restent à examiner dans les sources externes. Les autres ne sont pas déclarés impossibles : ils sont dépriorisés lorsqu'une proximité à 30 km ou moins, un forfait concurrent documenté ou un choc déjà sourcé crée un risque plus fort.

## Règles et limites

- Les seuils de 30 et 50 km sont des bandes de sensibilité, pas des frontières causales. Le point représentatif communal et les points d'accès aux stations ne décrivent pas les bassins touristiques complets.
- Les temps programmés utilisent toujours l'horaire 2026; ils servent seulement de contexte secondaire. Ils ne remplacent pas la validation historique réalisée pour les communes traitées.
- Un lien de forfait concurrent est retenu uniquement lorsqu'il est positivement documenté pour un point de station situé dans la commune. L'absence de lien dans les produits déjà étudiés ne prouve pas l'absence de concurrence.
- L'avertissement de capacité correspond à une variation moyenne absolue d'au moins 20 %, ou à un écart annuel ponctuel d'au moins 50 %. Il peut refléter un choc, une ouverture/fermeture saisonnière ou un mécanisme post-traitement; il déclenche une revue, jamais une exclusion automatique.
- Le dessin d'issue reste celui proposé par le chercheur : les nuitées de la commune de référence sont reliées aux stations par le temps d'accès, sans exiger que la station se trouve dans cette commune.

**Aucun spillover n'est déclaré absent, aucune tendance parallèle n'est approuvée et aucun couple causal n'est validé.** La prochaine étape est la revue externe ciblée du fichier `reports/accessibility_comparison_external_review_worklist.csv`.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
