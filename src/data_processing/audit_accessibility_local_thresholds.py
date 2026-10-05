"""Stage 32 diagnostic: reuse collected routes, never replace exposure or donors.

Python/flat CSV follows project and scientific research instructions. Same-stop
identity is not a measured zero-minute access or an approved lodging catchment.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
SOURCE_ID = "DERIVED_ACCESSIBILITY_LOCAL_THRESHOLD_AUDIT"
CONFIG = "config/accessibility_local_threshold_audit.json"
ROUTES = "data_processed/accessibility_station_group_journey_context.csv"
NODES = "reports/accessibility_station_access_nodes.csv"
GROUPS = "data_processed/accessibility_station_groups.csv"
EVENTS = "data_processed/accessibility_station_group_events.csv"
HISTORY = "data_processed/magic_pass_membership_history.csv"
SAMPLES = "data_processed/accessibility_station_group_journey_samples.csv"
OUTPUTS = {
    "accessibility_local_node_audit": "reports/accessibility_local_node_audit.csv",
    "accessibility_zero_vehicle_rejections": "reports/accessibility_zero_vehicle_rejections.csv",
    "accessibility_threshold_territories": "reports/accessibility_threshold_territories.csv",
    "accessibility_threshold_summary": "reports/accessibility_threshold_summary.csv",
}
MANIFEST = "reports/accessibility_local_threshold_audit_summary.json"
REPORT = "reports/84_AUDIT_ACCES_LOCAUX_SEUILS_FR.md"
FIELDS = {
    "source_id": ("Registered derived audit source; upstream sources retained in input manifest", "source identifier"),
    "municipality_bfs_id": ("Analytical BFS territory identifier; Moutier represented once as 6831", "BFS identifier"),
    "municipality_name": ("Municipality source name, not a key or evidence of lodging dependence", "text"),
    "station_group_id": ("Existing stable station group identifier; no regrouping", "identifier"),
    "station_group_name": ("Existing station group display name", "text"),
    "access_point_id": ("Stable reference access point identifier", "identifier"),
    "access_point_name": ("Original reference access point name", "text"),
    "selected_stop_id": ("Station reference selected bus/train stop ID; not necessarily actual lift departure", "GTFS identifier"),
    "selected_stop_name": ("Original station-side selected bus/train stop name", "text"),
    "selected_stop_municipality_bfs_id": ("Current BFS commune containing selected station stop; not a station footprint assignment", "BFS identifier"),
    "selected_stop_municipality_name": ("Source name of commune containing station-side stop", "text"),
    "reference_source_id": ("Upstream provenance ID for station reference point", "source identifier"),
    "reference_method": ("Existing method for station reference coordinates", "text"),
    "selected_stop_distance_from_access_point_km": ("Existing straight-line stop-to-reference distance; not walking duration or path length", "kilometres"),
    "access_node_quality": ("Existing node quality label, not a newly imposed filter", "category"),
    "municipality_main_stop_id": ("Existing municipal origin GTFS stop ID", "GTFS identifier"),
    "municipality_main_stop_name": ("Existing municipal origin stop name", "text"),
    "municipality_main_stop_selection_method": ("Existing origin selection rule; busiest train or terrestrial stop, not necessarily commune centre", "text"),
    "municipality_main_stop_distance_from_representative_point_km": ("Original municipal origin to representative point straight-line distance", "kilometres"),
    "hotel_territory_in_panel": ("Whether the station stop commune is in the 185-territory HESTA panel", "boolean flag"),
    "same_stop_local_candidate": ("Exact municipal origin and station stop ID equality; pending local-access review, no assumed travel duration", "boolean flag"),
    "routing_pair_complete": ("Existing success for all 24 departure requests (10 outward, 14 return), possibly via alternative access nodes; not simply one itinerary each way", "boolean flag"),
    "outbound_feasible_samples": ("Original feasible outward request count out of ten sampled departures", "count"),
    "return_feasible_samples": ("Original feasible return request count out of fourteen sampled departures", "count"),
    "descriptive_accessibility_usable": ("Existing complete and reviewed group routing eligibility; no new scientific validation", "boolean flag"),
    "mean_one_way_generalized_minutes": ("Existing mean of sampled outbound/return elapsed times including initial waiting; missing retained", "minutes"),
    "outbound_mean_initial_wait_minutes": ("Existing mean outward initial wait over feasible departure requests", "minutes"),
    "return_mean_initial_wait_minutes": ("Existing mean return initial wait over feasible departure requests", "minutes"),
    "first_effective_month": ("Existing earliest official base-entry effective month for this group", "calendar month"),
    "first_exposure_month_120min": ("Canonical first 120-minute network exposure month, retained without correction", "calendar month"),
    "local_entry_precedes_canonical_exposure": ("Same-stop local candidate enters before canonical exposure, or canonical exposure is missing", "boolean flag"),
    "canonical_never_exposed_donor_cohorts": ("Number of approved cohort universes assigning this territory donor_never_exposed under unchanged 120-minute rule", "count"),
    "same_stop_zero_vehicle_rejected_requests": ("Cached best-per-request zero-leg rejections with identical stop IDs, summed by group and territory; alternative feasible nodes can mask rejected node options", "count"),
    "walk_only_zero_vehicle_rejected_requests": ("Cached zero-leg rejections with different stop IDs, indicating router walking transfers; no duration inferred", "count"),
    "local_review_status": ("Diagnostic reason for review, preserving missing local routes and absent hotel communes", "category"),
    "same_stop": ("Whether rejected sampled request origin and destination IDs are identical", "boolean flag"),
    "rejected_requests": ("Number of original sampled requests rejected for zero vehicle legs in this group/territory/identity category", "count"),
    "threshold_minutes": ("Diagnostic bound on existing generalized route metric; no primary threshold selection", "minutes"),
    "route_exposure_candidate": ("At least one currently usable group route within scenario threshold and active during the source panel calendar", "boolean flag"),
    "scenario_first_exposure_month": ("Earliest eligible active-group month within scenario bound; route-only scenario, not replacement treatment", "calendar month"),
    "scenario_first_group_ids": ("All eligible groups jointly defining scenario first exposure, pipe-delimited stable IDs", "identifier list"),
    "scenario_first_group_names": ("Original names of groups jointly defining scenario first exposure", "text"),
    "qualifying_group_count": ("Distinct eligible groups having any active month in panel within threshold, respecting documented exit", "count"),
    "first_group_has_stop_in_commune": ("Any first-exposure group has a selected access stop inside this commune; proximity clue only, not lodging validation", "boolean flag"),
    "pre36_observed_months": ("Nonmissing original hotel outcomes in 36 calendar months before scenario entry; no regression or new fit gate", "count"),
    "reference_observed": ("Original hotel outcome observed one calendar month before scenario entry", "boolean flag"),
    "post_observed_months": ("Nonmissing original hotel outcomes on/after scenario first entry; full network trajectory retained", "count"),
    "complete_pre36": ("All 36 pre-calendar outcomes observed; descriptive coverage only, not model eligibility", "boolean flag"),
    "complete_pre12_post12": ("All original outcomes observed in symmetric 12-month calendar windows around scenario entry", "boolean flag"),
    "lost_relative_to_120min": ("Canonical 120-minute exposed territory lacks any route candidate at this diagnostic bound", "boolean flag"),
    "date_changed_relative_to_120min": ("Route-candidate first entry differs from canonical first entry; compares only territories exposed in both", "boolean flag"),
    "same_stop_candidate_group_ids": ("Groups with an exactly shared local stop, irrespective of route threshold; candidates only", "identifier list"),
    "same_stop_candidate_first_entry": ("Earliest group entry among shared-stop local candidates, not an approved exposure month", "calendar month"),
    "unexposed_with_same_stop_candidate": ("No threshold route exposure despite an exact shared-stop group candidate; cannot certify unaffected control", "boolean flag"),
    "earlier_same_stop_candidate": ("Shared-stop candidate entry precedes route-only scenario entry, or scenario entry missing", "boolean flag"),
    "primary_replacement_approved": ("Whether these diagnostic records replace canonical treatment or donor roles; always false", "boolean flag"),
    "territories_in_panel": ("Distinct HESTA analytical territories, with approved Moutier bridge", "count"),
    "route_exposed_territories": ("Distinct territories with route-only candidate exposure at this threshold", "count"),
    "territories_without_route_exposure": ("Territories lacking route exposure; not certified unaffected controls", "count"),
    "groups_with_route_exposure": ("Distinct station groups linked by eligible routes at threshold across panel", "count"),
    "territories_lost_vs_120min": ("Number of canonical exposed territories without route exposure at scenario threshold", "count"),
    "territories_with_changed_first_date": ("Route-exposed territories whose first date changes from canonical 120-minute date", "count"),
    "exposed_complete_pre36": ("Route-exposed territories with every pre36 original outcome observed", "count"),
    "exposed_complete_pre12_post12": ("Route-exposed territories with complete original symmetric 12-month windows", "count"),
    "exposed_observed_post_months": ("Total original nonmissing post outcomes across scenario-exposed territories", "count"),
    "unexposed_shared_stop_candidates": ("Route-unexposed territories with exact same-stop local candidate awaiting review", "count"),
    "earlier_shared_stop_candidates": ("Territories with earlier shared-stop candidate entry than route-only scenario, including missing route entry", "count"),
}


def sha(path: str) -> str:
    digest = hashlib.sha256()
    with (ROOT / path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_routes(routes: pd.DataFrame) -> pd.DataFrame:
    """Only the already approved exact Moutier identity bridge is allowed."""
    old = routes[routes.municipality_bfs_id.eq(700)].set_index("station_group_id")
    new = routes[routes.municipality_bfs_id.eq(6831)].set_index("station_group_id")
    columns = [c for c in routes if c not in {"municipality_bfs_id", "municipality_name", "station_group_id"}]
    pd.testing.assert_frame_equal(old[columns].sort_index(), new[columns].sort_index())
    result = routes[~routes.municipality_bfs_id.eq(700)].copy()
    if result.duplicated(["station_group_id", "municipality_bfs_id"]).any():
        raise ValueError("Duplicate group/territory routes")
    return result


def zero_leg_inventory() -> pd.DataFrame:
    """Read cached request results only; never reroute or redownload."""
    pieces = []
    columns = ["station_group_id", "municipality_bfs_id", "origin_stop_id", "destination_stop_id", "journey_exclusion_reason"]
    for chunk in pd.read_csv(ROOT / SAMPLES, usecols=columns, dtype={"origin_stop_id": str, "destination_stop_id": str}, chunksize=50000):
        local = chunk[chunk.journey_exclusion_reason.eq("no_vehicle_leg_same_stop_or_walk_only")].copy()
        local["municipality_bfs_id"] = local.municipality_bfs_id.replace({700: 6831})
        # Moutier duplicated routing requests describe one territory, not two trips.
        local = local[~chunk.loc[local.index, "municipality_bfs_id"].eq(700)]
        local["same_stop"] = local.origin_stop_id.eq(local.destination_stop_id)
        pieces.append(local.groupby(["station_group_id", "municipality_bfs_id", "same_stop"]).size().rename("rejected_requests").reset_index())
    result = pd.concat(pieces).groupby(["station_group_id", "municipality_bfs_id", "same_stop"], as_index=False).rejected_requests.sum()
    result["source_id"] = SOURCE_ID
    return result


def local_node_audit(routes, nodes, groups, canonical_first, universe, rejected):
    origins = routes.drop_duplicates("municipality_bfs_id")[["municipality_bfs_id", "municipality_name", "municipality_main_stop_id", "municipality_main_stop_name", "municipality_main_stop_selection_method", "municipality_main_stop_distance_from_representative_point_km"]]
    keep = ["station_group_id", "access_point_id", "access_point_name", "selected_stop_id", "selected_stop_name", "selected_stop_municipality_bfs_id", "selected_stop_municipality_name", "reference_source_id", "reference_method", "selected_stop_distance_from_access_point_km", "access_node_quality"]
    local = nodes[keep].merge(groups[["station_group_id", "station_group_name", "first_effective_month"]], validate="many_to_one")
    local = local.merge(origins, how="left", left_on="selected_stop_municipality_bfs_id", right_on="municipality_bfs_id", validate="many_to_one")
    local["hotel_territory_in_panel"] = local.municipality_bfs_id.notna()
    local["same_stop_local_candidate"] = local.hotel_territory_in_panel & local.selected_stop_id.eq(local.municipality_main_stop_id)
    route_cols = ["station_group_id", "municipality_bfs_id", "routing_pair_complete", "descriptive_accessibility_usable", "mean_one_way_generalized_minutes", "outbound_mean_initial_wait_minutes", "return_mean_initial_wait_minutes", "outbound_feasible_samples", "return_feasible_samples"]
    local = local.merge(routes[route_cols], how="left", validate="many_to_one")
    local["first_exposure_month_120min"] = local.municipality_bfs_id.map(canonical_first)
    donor_counts = universe[universe.primary_comparison_role.eq("donor_never_exposed")].groupby("municipality_bfs_id").size()
    local["canonical_never_exposed_donor_cohorts"] = local.municipality_bfs_id.map(donor_counts)
    local.loc[local.hotel_territory_in_panel & local.canonical_never_exposed_donor_cohorts.isna(), "canonical_never_exposed_donor_cohorts"] = 0
    local["local_entry_precedes_canonical_exposure"] = local.same_stop_local_candidate & (local.first_exposure_month_120min.isna() | pd.to_datetime(local.first_effective_month).lt(pd.to_datetime(local.first_exposure_month_120min)))
    for same, column in [(True, "same_stop_zero_vehicle_rejected_requests"), (False, "walk_only_zero_vehicle_rejected_requests")]:
        counts = rejected[rejected.same_stop.eq(same)].set_index(["station_group_id", "municipality_bfs_id"]).rejected_requests
        keys = pd.MultiIndex.from_frame(local[["station_group_id", "municipality_bfs_id"]])
        local[column] = counts.reindex(keys).to_numpy()
        local.loc[local.hotel_territory_in_panel & local[column].isna(), column] = 0
    local["local_review_status"] = np.select([
        ~local.hotel_territory_in_panel,
        local.same_stop_local_candidate & ~local.routing_pair_complete.eq(True),
        local.same_stop_local_candidate,
        local.hotel_territory_in_panel & ~local.routing_pair_complete.eq(True),
    ], ["station_stop_commune_absent_from_hotel_panel", "same_stop_local_option_rejected_group_route_missing", "same_stop_option_omitted_alternative_group_route_exists", "local_group_route_incomplete"], default="local_group_route_exists_lodging_basin_unvalidated")
    local["primary_replacement_approved"] = False
    local["source_id"] = SOURCE_ID
    return local.sort_values(["station_group_id", "access_point_id"])


def threshold_inventory(routes, groups, panel, local, thresholds, history):
    entries = groups.set_index("station_group_id").first_effective_month.map(pd.Timestamp)
    # Respect the same documented exit used by the canonical exposure builder.
    exits = history[history.event_type.eq("base_pass_exit")].copy()
    exit_dates = {"MP_GROUP_RESORT__" + row.candidate_resort_id: pd.Timestamp(str(row.exit_date)[:7] + "-01") for row in exits.itertuples()}
    pairs = routes.copy()
    pairs["entry"] = pairs.station_group_id.map(entries)
    pairs["start"] = pairs.entry.clip(lower=panel.date.min())
    pairs["last"] = pairs.station_group_id.map(exit_dates).fillna(panel.date.max())
    pairs["calendar_active"] = pairs.start.le(pairs["last"]) & pairs.start.le(panel.date.max())
    eligible = pairs.routing_pair_complete & pairs.descriptive_accessibility_usable & pairs.calendar_active
    canonical_first = panel[panel.active_station_group_count_120min.gt(0)].groupby("municipality_bfs_id").date.min()
    shared = local[local.same_stop_local_candidate].drop_duplicates(["station_group_id", "municipality_bfs_id"])
    local_groups = shared.groupby("municipality_bfs_id").station_group_id.agg(lambda x: "|".join(sorted(x))).to_dict()
    local_first = pd.to_datetime(shared.first_effective_month).groupby(shared.municipality_bfs_id).min().to_dict()
    inside = set(zip(local.station_group_id, local.selected_stop_municipality_bfs_id))
    details, summaries = [], []
    for threshold in thresholds:
        selected = pairs[eligible & pairs.mean_one_way_generalized_minutes.le(threshold)]
        by_unit = {key: frame for key, frame in selected.groupby("municipality_bfs_id")}
        rows = []
        for bfs, unit in panel.groupby("municipality_bfs_id", sort=True):
            links = by_unit.get(bfs, selected.iloc[:0])
            first = links.start.min() if len(links) else pd.NaT
            initial = links[links.start.eq(first)]
            observations = unit.set_index("date").hotel_overnights
            has_exposure = pd.notna(first)
            pre36 = pd.date_range(first - pd.DateOffset(months=36), periods=36, freq="MS") if has_exposure else []
            both12 = pd.date_range(first - pd.DateOffset(months=12), periods=24, freq="MS") if has_exposure else []
            baseline = observations.get(first - pd.DateOffset(months=1)) if has_exposure else np.nan
            old = canonical_first.get(bfs, pd.NaT)
            candidate = local_first.get(bfs, pd.NaT)
            row = {
                "threshold_minutes": threshold, "municipality_bfs_id": int(bfs), "municipality_name": unit.municipality_name_source.iloc[-1],
                "route_exposure_candidate": has_exposure, "scenario_first_exposure_month": first,
                "scenario_first_group_ids": "|".join(sorted(initial.station_group_id)), "scenario_first_group_names": "|".join(initial.sort_values("station_group_id").station_group_name),
                "qualifying_group_count": len(links), "first_group_has_stop_in_commune": any((gid, bfs) in inside for gid in initial.station_group_id),
                "first_exposure_month_120min": old,
                "pre36_observed_months": int(observations.reindex(pre36).notna().sum()) if has_exposure else np.nan,
                "reference_observed": pd.notna(baseline),
                "post_observed_months": int(observations[observations.index >= first].notna().sum()) if has_exposure else np.nan,
                "complete_pre36": has_exposure and observations.reindex(pre36).notna().all(),
                "complete_pre12_post12": has_exposure and observations.reindex(both12).notna().all(),
                "lost_relative_to_120min": pd.notna(old) and not has_exposure,
                "date_changed_relative_to_120min": has_exposure and pd.notna(old) and first != old,
                "same_stop_candidate_group_ids": local_groups.get(bfs, ""), "same_stop_candidate_first_entry": candidate,
                "unexposed_with_same_stop_candidate": not has_exposure and pd.notna(candidate),
                "earlier_same_stop_candidate": pd.notna(candidate) and (not has_exposure or candidate < first),
                "primary_replacement_approved": False, "source_id": SOURCE_ID,
            }
            rows.append(row)
        frame = pd.DataFrame(rows)
        for column in ["scenario_first_exposure_month", "first_exposure_month_120min", "same_stop_candidate_first_entry"]:
            frame[column] = pd.to_datetime(frame[column])
        details.extend(rows)
        exposed = frame[frame.route_exposure_candidate]
        summaries.append({
            "threshold_minutes": threshold, "territories_in_panel": len(frame), "route_exposed_territories": len(exposed),
            "territories_without_route_exposure": len(frame) - len(exposed), "groups_with_route_exposure": selected.station_group_id.nunique(),
            "territories_lost_vs_120min": int(frame.lost_relative_to_120min.sum()), "territories_with_changed_first_date": int(frame.date_changed_relative_to_120min.sum()),
            "exposed_complete_pre36": int(exposed.complete_pre36.sum()), "exposed_complete_pre12_post12": int(exposed.complete_pre12_post12.sum()),
            "exposed_observed_post_months": int(exposed.post_observed_months.sum()),
            "unexposed_shared_stop_candidates": int(frame.unexposed_with_same_stop_candidate.sum()), "earlier_shared_stop_candidates": int(frame.earlier_same_stop_candidate.sum()),
            "primary_replacement_approved": False, "source_id": SOURCE_ID,
        })
    detail_frame = pd.DataFrame(details)
    for column in ["scenario_first_exposure_month", "first_exposure_month_120min", "same_stop_candidate_first_entry"]:
        detail_frame[column] = pd.to_datetime(detail_frame[column])
    return detail_frame, pd.DataFrame(summaries)


def register_outputs(frames):
    """Use existing catalog schemas; preserve every unrelated row."""
    from src.data_processing.update_accessibility_expansion_provenance import source_row, DICTIONARY_COLUMNS
    source_path = ROOT / "metadata/data_sources_master.csv"
    dictionary_path = ROOT / "metadata/data_dictionary.csv"
    sources = pd.read_csv(source_path, dtype=str, keep_default_na=False)
    incoming = source_row(SOURCE_ID,
        variable_name="local_route_omissions|route_only_threshold_scenarios|uncertain_control_classifications",
        variable_description="Approved diagnostic audit of local same-stop/walk-only route omissions and 30/45/60/120 minute candidate exposure coverage",
        source_organisation="Master thesis analytical pipeline", source_dataset_name="Local access and threshold diagnostic, no exposure replacement",
        retrieval_method="Reuse existing local route, node, request, membership and HESTA files; no collection or rerouting", retrieval_date="2026-10-05",
        local_raw_file="|".join([CONFIG, ROUTES, NODES, GROUPS, EVENTS, HISTORY, SAMPLES]),
        processed_file="|".join([*OUTPUTS.values(), MANIFEST, REPORT]),
        geographic_level="71 existing station groups, 75 access nodes, 185 analytical hotel territories",
        temporal_resolution="Static winter 2026 routes; historical entry dates and original monthly outcome coverage", temporal_start="2013-01", temporal_end="2026-12",
        unit="minutes, kilometres, counts, stable identifiers and flags", license="Derived diagnostics; upstream source terms apply", access_conditions="Local reproducible output",
        transformation_applied="Verify exact Moutier route equality and deduplicate 700. Match station-stop commune to existing municipal origin, inspect exact stop equality and cached zero-vehicle failures. Reuse generalized means including waiting at four thresholds, earliest active group date and existing documented exit. Count nonmissing HESTA windows without imputation",
        quality_notes="Same-stop candidates have no assigned duration. Station reference points/stop communes do not validate lift departures or lodging dependence. Best-per-request routing can mask rejected options at other access nodes. Route-unexposed is not certified unaffected. No threshold or walking rule chosen; no canonical exposure, control, estimate or plot replaced",
        confidence_level="Exact reproducible diagnostics, lodging and historical transport assumptions unresolved",
        manual_verification="Canonical threshold/date reconciliation, source hash preservation, known local cases and missing outcome checks",
        notes="Researcher approved audit and narrower comparisons, not a replacement exposure rule. Flat CSV scientific guidance and project Python conventions followed.")
    sources = pd.concat([sources[~sources.source_id.eq(SOURCE_ID)], pd.DataFrame([incoming])], ignore_index=True).fillna("")
    sources.sort_values("source_id").to_csv(source_path, index=False, lineterminator="\n")
    existing = pd.read_csv(dictionary_path, dtype=str, keep_default_na=False)
    rows = []
    for table, frame in frames.items():
        for variable in frame:
            description, unit = FIELDS[variable]
            rows.append(dict(variable=variable, table=table, description=description, unit=unit, data_type=str(frame[variable].dtype),
                geographic_level="existing groups/access nodes or analytical BFS territories", temporal_level="diagnostic threshold and existing entry/outcome calendar",
                source_id=SOURCE_ID, raw_or_derived="derived or retained source field", formula="See src/data_processing/audit_accessibility_local_thresholds.py and report 84",
                causal_role="diagnostic only, no treatment replacement", missing_share=f"{frame[variable].isna().mean():.6f}",
                notes="No walking time imputation, canonical exposure change, threshold choice or causal approval."))
    result = pd.concat([existing[~existing.table.isin(frames)], pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna("")
    result.sort_values(["table", "variable"]).to_csv(dictionary_path, index=False, lineterminator="\n")


def main():
    config = json.loads((ROOT / CONFIG).read_text(encoding="utf-8"))
    protected = [config["outcome_panel"], config["comparison_universe"], ROUTES, NODES, GROUPS, EVENTS, HISTORY, SAMPLES,
        "config/accessibility_cohort_time_execution.json", "reports/accessibility_cohort_time_estimation_summary.json",
        "reports/accessibility_cohort_time_estimation_cohort_month.csv", "reports/accessibility_cohort_time_estimation_dynamic.csv",
        "config/accessibility_commune_trend_plots.json", "data_processed/accessibility_commune_trend_plot_points.json",
        *[f"figures/accessibility_15_communes_trends_{i}.png" for i in [1, 2, 3]]]
    # Existing schema names remain authoritative; abort on missing source inputs.
    hashes = {path: sha(path) for path in protected}
    routes = canonical_routes(pd.read_csv(ROOT / ROUTES, dtype={"municipality_main_stop_id": str}))
    nodes = pd.read_csv(ROOT / NODES, dtype={"selected_stop_id": str})
    groups = pd.read_csv(ROOT / GROUPS)
    events = pd.read_csv(ROOT / EVENTS)
    event_first = events.groupby("station_group_id").effective_month.min().sort_index()
    pd.testing.assert_series_equal(groups.set_index("station_group_id").first_effective_month.sort_index(), event_first, check_names=False)
    panel = pd.read_csv(ROOT / config["outcome_panel"], parse_dates=["date"], low_memory=False)
    universe = pd.read_csv(ROOT / config["comparison_universe"])
    first = panel[panel.active_station_group_count_120min.gt(0)].groupby("municipality_bfs_id").date.min()
    rejected = zero_leg_inventory()
    local = local_node_audit(routes, nodes, groups, first, universe, rejected)
    detail, summary = threshold_inventory(routes, groups, panel, local, config["thresholds_minutes"], pd.read_csv(ROOT / HISTORY))
    for threshold in [30, 60, 120]:
        expected = panel[panel[f"active_station_group_count_{threshold}min"].gt(0)].groupby("municipality_bfs_id").date.min().sort_index()
        actual = detail[detail.threshold_minutes.eq(threshold) & detail.route_exposure_candidate].set_index("municipality_bfs_id").scenario_first_exposure_month.sort_index()
        pd.testing.assert_series_equal(expected, actual, check_names=False)
    frames = dict(zip(OUTPUTS, [local, rejected, detail, summary]))
    for table, frame in frames.items():
        if set(frame) - set(FIELDS):
            raise ValueError(f"Undocumented variables in {table}: {set(frame) - set(FIELDS)}")
        frame.to_csv(ROOT / OUTPUTS[table], index=False, lineterminator="\n", date_format="%Y-%m-%d")
    after = {path: sha(path) for path in protected}
    if hashes != after:
        raise ValueError("Canonical input changed during audit")
    manifest = dict(specification_version=config["specification_version"], source_id=SOURCE_ID,
        config_sha256=sha(CONFIG), builder_sha256=sha("src/data_processing/audit_accessibility_local_thresholds.py"),
        canonical_outputs_changed=False, primary_replacement_approved=False, causal_estimation_approved=False,
        input_sha256=hashes, output_sha256={path: sha(path) for path in OUTPUTS.values()},
        output_row_counts={key: len(value) for key, value in frames.items()},
        same_stop_cases=local[local.same_stop_local_candidate][["station_group_name", "municipality_name", "selected_stop_name", "selected_stop_distance_from_access_point_km", "routing_pair_complete", "first_effective_month", "first_exposure_month_120min"]].astype(str).to_dict("records"),
        zero_vehicle_rejected_requests=int(rejected.rejected_requests.sum()),
        caveat="Local stop identity is a candidate relationship, not measured walking access or lodging catchment. No main threshold chosen.")
    (ROOT / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    register_outputs(frames)
    print(summary.to_string(index=False))
    print(json.dumps({"same_stop_cases": manifest["same_stop_cases"], "output_rows": manifest["output_row_counts"], "canonical_outputs_changed": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
