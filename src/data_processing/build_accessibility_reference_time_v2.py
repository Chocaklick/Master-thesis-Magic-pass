"""Versioned, resumable access-time revision; never overwrite legacy outputs.

Run from project root. All access points are queried separately: a legacy
winner under waiting-inclusive time is not a safe winner under duration alone.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src/data_processing"))
import build_accessibility_station_group_journeys as legacy
from build_public_transport_journey_context import sample_row as legacy_sample
from gtfs_static_router import format_gtfs_time

CONFIG = "config/accessibility_reference_time_v2.json"
SOURCE = "DERIVED_ACCESSIBILITY_REFERENCE_TIME_V2"
MANIFEST = "reports/accessibility_reference_time_v2_summary.json"
CACHE = ROOT / "data_interim/accessibility_reference_time_v2"
OUTPUTS = {
    "accessibility_reference_time_v2_samples": "data_processed/accessibility_reference_time_v2_samples.csv",
    "accessibility_reference_time_v2_daily": "data_processed/accessibility_reference_time_v2_daily.csv",
    "accessibility_reference_time_v2_pairs": "data_processed/accessibility_reference_time_v2_pairs.csv",
    "accessibility_reference_time_v2_local_review": "reports/accessibility_reference_time_v2_local_review.csv",
    "accessibility_mobility_literature": "reports/accessibility_mobility_literature.csv",
    "accessibility_reference_time_v2_query_status": "reports/accessibility_reference_time_v2_query_status.csv",
}
PROTECTED = [
    "data_processed/accessibility_station_group_journey_samples.csv",
    "data_processed/accessibility_station_group_journey_context.csv",
    "data_processed/accessibility_municipality_month_exposure_territorial.csv",
    "reports/accessibility_cohort_comparison_universe_territorial.csv",
    "reports/accessibility_local_threshold_audit_summary.json",
    "reports/accessibility_cohort_time_estimation_summary.json",
    "reports/accessibility_cohort_time_estimation_cohort_month.csv",
    "reports/accessibility_cohort_time_estimation_dynamic.csv",
    "config/accessibility_commune_trend_plots.json",
    "data_processed/accessibility_commune_trend_plot_points.json",
    *[f"figures/accessibility_15_communes_trends_{i}.png" for i in (1, 2, 3)],
]
LOCAL_EVIDENCE: dict = {}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def truth(series):
    return series.astype(str).str.lower().eq("true")


def validate_local_evidence(items):
    result = {}
    for item in items:
        key = (int(item["municipality_bfs_id"]), item["access_point_id"])
        if key in result:
            raise ValueError("Duplicate local evidence key")
        if not item.get("actual_endpoints_verified") or not item.get("source_id") or not item.get("evidence_locator"):
            raise ValueError("Local duration requires documented actual endpoints and source")
        out, ret = float(item["outbound_walk_minutes"]), float(item["return_walk_minutes"])
        if min(out, ret) < 0 or not np.isfinite([out, ret]).all():
            raise ValueError("Invalid documented walking duration")
        if min(out, ret) == 0 and not item.get("actual_origin_departure_coincidence_verified"):
            raise ValueError("Same GTFS stop is not proof of actual station coincidence")
        result[key] = item
    return result


def revised_sample(pair, direction, day_label, date, requested, origin,
                   destination, journey, maximum_legs, maximum_minutes):
    row = legacy_sample(pair, direction, day_label, date, requested, origin,
                        destination, journey, maximum_legs, maximum_minutes)
    access_id = (destination.get("component_resort_id", "")
                 if direction.startswith("outbound") else origin.get("component_resort_id", ""))
    row.update(access_point_id=access_id, initial_coded_walk_minutes=np.nan,
               available_duration_minutes=np.nan, local_access_pending=False,
               local_access_status="not_a_zero_vehicle_candidate",
               local_duration_source_id="", initial_wait_excluded=True,
               method_version="stage33_v2_2026_10_06")
    if journey is not None:
        walking = float(journey.initial_walk_seconds) / 60
        row["initial_coded_walk_minutes"] = walking
        if row["journey_feasible"]:
            # first_departure - requested may contain an initial coded walk;
            # subtract only waiting, not that movement.
            row["available_duration_minutes"] = row["scheduled_journey_minutes"] + walking
            row["initial_wait_minutes"] -= walking
            if row["initial_wait_minutes"] < -1e-9:
                raise ValueError("Initial walking exceeds readiness-to-boarding interval")
        if journey.legs == 0:
            row["local_access_pending"] = True
            row["local_access_status"] = (
                "same_transport_node_actual_departure_unverified"
                if str(origin.selected_stop_id) == str(destination.selected_stop_id)
                else "coded_transfer_between_nodes_actual_departure_unverified")
            # Diagnostic node interval, NOT assigned as actual station access.
            row["scheduled_first_boarding_time"] = ""
            row["scheduled_arrival_time"] = format_gtfs_time(journey.arrival_seconds)
            row["generalized_elapsed_minutes"] = (journey.arrival_seconds - requested) / 60
            row["vehicle_legs"] = 0
            row["transfers"] = 0
            row["journey_exclusion_reason"] = "local_access_documentation_pending_not_missing_transport"
    evidence = LOCAL_EVIDENCE.get((int(pair["municipality_bfs_id"]), access_id))
    if evidence is not None:
        minutes = float(evidence["outbound_walk_minutes" if direction.startswith("outbound") else "return_walk_minutes"])
        row.update(journey_feasible=True, journey_exclusion_reason="",
                   available_duration_minutes=minutes, local_access_pending=False,
                   local_access_status="documented_actual_local_access",
                   local_duration_source_id=evidence["source_id"],
                   initial_wait_minutes=0., initial_coded_walk_minutes=minutes,
                   scheduled_journey_minutes=minutes, generalized_elapsed_minutes=minutes,
                   vehicle_legs=0, transfers=0, transport_modes="documented_local_walking",
                   scheduled_first_boarding_time="", scheduled_arrival_time="")
    row["interpretation"] = "winter_2026_transport_node_proxy_not_verified_door_to_lift_or_historical_access"
    return row


def direction_status(subset):
    if subset.available_duration_minutes.notna().any():
        return "available_with_local_candidate_pending" if truth(subset.local_access_pending).any() else "available"
    if truth(subset.local_access_pending).any():
        return "local_access_documentation_pending"
    return "no_usable_itinerary_within_existing_query_bounds"


def aggregate(samples, dates):
    keys = ["station_group_id", "station_group_name", "municipality_bfs_id", "municipality_name"]
    daily_rows = []
    for values, part in samples.groupby(keys + ["reference_date"], sort=True, dropna=False):
        row = dict(zip(keys + ["reference_date"], values))
        for direction, prefix in [("outbound_municipality_to_destination", "outbound"),
                                  ("return_destination_to_municipality", "return")]:
            sub = part[part.direction.eq(direction)]
            valid = sub[sub.available_duration_minutes.notna()]
            row[prefix + "_requested_departures"] = sub.requested_departure_time.nunique()
            row[prefix + "_available_departures"] = valid.requested_departure_time.nunique()
            row[prefix + "_status"] = direction_status(sub)
            row[prefix + "_min_minutes"] = valid.available_duration_minutes.min()
            # Dispersion across best available access point per requested time,
            # not an empirical traveller distribution or unequal point weights.
            by_request = valid.groupby("requested_departure_time").available_duration_minutes.min()
            row[prefix + "_range_minutes"] = by_request.max() - by_request.min()
            if len(valid):
                winner = valid.sort_values(["available_duration_minutes", "access_point_id", "requested_departure_time"], kind="stable").iloc[0]
                row[prefix + "_winning_access_point_id"] = winner.access_point_id
                row[prefix + "_winning_requested_time"] = winner.requested_departure_time
            else:
                row[prefix + "_winning_access_point_id"] = ""
                row[prefix + "_winning_requested_time"] = ""
        row["daily_reference_minutes"] = (row["outbound_min_minutes"] + row["return_min_minutes"]) / 2
        row["local_access_pending"] = bool(truth(part.local_access_pending).any())
        row["time_scope"] = "selected_transport_nodes_with_unverified_last_mile"
        row["source_id"] = SOURCE
        daily_rows.append(row)
    daily = pd.DataFrame(daily_rows)
    pairs = []
    for values, part in daily.groupby(keys, sort=True, dropna=False):
        row = dict(zip(keys, values))
        if set(part.reference_date.astype(str)) != set(dates):
            raise ValueError("Reference-day grain changed")
        row["days_with_both_directions"] = int(part.daily_reference_minutes.notna().sum())
        # No silent skipna mean representing two days when just one exists.
        row["reference_time_minutes"] = (part.daily_reference_minutes.mean()
            if row["days_with_both_directions"] == len(dates) else np.nan)
        row["two_day_status"] = "available" if pd.notna(row["reference_time_minutes"]) else "incomplete_reference_days"
        row["local_access_pending"] = bool(truth(part.local_access_pending).any())
        row["actual_station_access_verified"] = False
        row["time_scope"] = "selected_transport_nodes_with_unverified_last_mile"
        row["source_id"] = SOURCE
        pairs.append(row)
    return daily, pd.DataFrame(pairs)


def register(frames):
    from src.data_processing.update_accessibility_expansion_provenance import source_row, DICTIONARY_COLUMNS
    path = ROOT / "metadata/data_sources_master.csv"
    old = pd.read_csv(path, dtype=str, keep_default_na=False)
    source_items = json.loads((ROOT / "config/accessibility_mobility_evidence_sources.json").read_text(encoding="utf-8"))
    incoming = [source_row(SOURCE, variable_name="access_duration|direction_coverage|local_missingness",
        variable_description="Approved daily minimum morning/return durations and mean across two reference days; node proxy, local verification pending",
        source_organisation="Master thesis analytical pipeline", source_dataset_name="Versioned access reference time revision",
        retrieval_method="Per-access-point rerouting with existing official winter 2026 GTFS; independent resumable caches",
        retrieval_date="2026-10-06", local_raw_file="config/accessibility_reference_time_v2.json|reports/accessibility_station_access_nodes.csv|reports/public_transport_journey_nodes.csv",
        processed_file="|".join(OUTPUTS.values()), geographic_level="71 unchanged groups, 75 unchanged access points, 186 source municipal series (185 territories)",
        temporal_resolution="Two sampled winter 2026 days", unit="minutes, counts, flags",
        transformation_applied="Minima by direction/day over all access points and returned queries; exclude initial wait, preserve coded initial walk and transfers. No 24/24 gate. Both days explicitly represented, missing direction never imputed.",
        quality_notes="Current bus/train nodes, not all actual lift departures; initial zero-vehicle access requires endpoint evidence. Existing six-leg/480-minute router bounds and earliest-arrival query search retained. No main mode, threshold, historical validation, causal or exposure replacement approval.")]
    for source in source_items:
        metas = list((ROOT / "data_external/source_evidence").glob(source["source_id"] + "_*.metadata.json"))
        meta = json.loads(metas[0].read_text(encoding="utf-8")) if metas else {}
        incoming.append(source_row(source["source_id"], variable_name="published_visitor_modal_shares_or_arrival_evidence",
            variable_description=source["description"], source_organisation=source["organisation"],
            source_dataset_name=source["description"], source_page_url=source["url"], direct_download_url=source["url"],
            retrieval_method="Web primary-source inspection; " + ("immutable archived response and SHA256" if meta else "local archive unavailable; see collection log"),
            retrieval_date=meta.get("retrieval_date", "2026-10-06"), local_raw_file=meta.get("raw_file", ""),
            processed_file="reports/accessibility_mobility_literature.csv|reports/85_REVISION_TEMPS_ACCES_ET_MODES_FR.md",
            unit="published modal percentage or documented walking minutes", license="Upstream publication terms; not an open microdata dataset",
            quality_notes="Reported aggregate survey results, not new individual observations or a representative sample of all Magic Pass stations. See row-level population, locator, formula and limitations.",
            notes="Original numeric summaries are never merged into HESTA or used as universal modal weights."))
    identifiers = {r["source_id"] for r in incoming}
    pd.concat([old[~old.source_id.isin(identifiers)], pd.DataFrame(incoming).reindex(columns=old.columns)], ignore_index=True).fillna("").sort_values("source_id").to_csv(path, index=False, lineterminator="\n")
    path = ROOT / "metadata/data_dictionary.csv"
    old_dictionary = pd.read_csv(path, dtype=str, keep_default_na=False)
    old_definitions = old_dictionary.drop_duplicates("variable").set_index("variable")
    definitions = {
        "access_point_id": ("Stable existing access-point identifier; never names as sole key", "identifier"),
        "initial_coded_walk_minutes": ("Initial walk encoded by router cross-transfer; preserved separately from waiting, not assumed actual lift access", "minutes"),
        "available_duration_minutes": ("Available node itinerary duration excluding only initial waiting, plus coded initial walking; verified local walk can replace it", "minutes"),
        "local_access_pending": ("At least one local no-vehicle candidate requires actual endpoint/walking documentation; not no transport", "boolean"),
        "local_access_status": ("Explicit same-node, coded transfer, verified local or non-local candidate classification", "category"),
        "local_duration_source_id": ("Source identifier of documented actual local duration; empty if unverified", "identifier"),
        "initial_wait_excluded": ("Initial waiting is excluded from revised duration; transfers remain", "boolean"),
        "method_version": ("Version of approved revised method", "version"),
        "daily_reference_minutes": ("(minimum available outbound duration + minimum available return duration)/2 for one day; missing if either direction missing", "minutes"),
        "reference_time_minutes": ("Mean of both reference-day durations; missing when a reference day cannot be computed", "minutes"),
        "days_with_both_directions": ("Reference days with at least one usable returned itinerary in each direction", "days"),
        "two_day_status": ("Explicit availability of the approved two-day mean, without imputing incomplete days", "category"),
        "actual_station_access_verified": ("Whether actual municipal origin to lift-departure access is verified; remains false in node-proxy output", "boolean"),
        "time_scope": ("Geographic endpoint scope of the time; unverified last mile remains explicit", "category"),
        "old_mean_including_wait_minutes": ("Unchanged legacy mean one-way generalized elapsed time, including initial waiting", "minutes"),
        "old_24_of_24_complete": ("Unchanged legacy complete-query eligibility", "boolean"),
        "difference_from_old_minutes": ("New reference duration minus old mean, comparing different descriptive metrics, not a travel-speed change", "minutes"),
        "query_count": ("Number of access-point/departure queries in the recorded status category", "queries"),
        "actual_local_duration_minutes": ("Documented actual local walking access if verified; missing is not an absence of transport", "minutes"),
        "endpoint_evidence_status": ("Verification state of actual municipality-origin/lift-departure correspondence", "category"),
        "publication": ("Primary study citation or official source title", "text"),
        "population": ("Exact survey or documented journey population; no national extrapolation", "text"),
        "collection_period": ("Reported observation period, separate from publication date", "period"),
        "sample_people": ("Number of people/questionnaires when explicitly known for stated population, not station response count", "people"),
        "sample_records": ("Station-specific records when applicable; not necessarily independent people", "records"),
        "indicator": ("Exact modal share, composition or official arrival indicator", "text"),
        "value": ("Published aggregate value or explicitly identified arithmetic derivation", "see value_unit"),
        "value_unit": ("Unit of literature indicator; percentages not probabilities or minutes", "unit"),
        "locator": ("Page, figure, table or HTML section supporting the claim", "text"),
        "limitations": ("Population/period/design limits and prohibited extrapolations", "text"),
        "formula": ("Arithmetic transformation, or reported when directly published", "text"),
        "source_url": ("Direct primary-source URL", "URL"),
    }
    for prefix in ("outbound", "return"):
        for suffix, desc, unit in [
            ("requested_departures", "Distinct requested departures, irrespective of number of access points", "queries"),
            ("available_departures", "Distinct departures with at least one usable itinerary; no percentage gate", "queries"),
            ("status", "Direction availability, with local documentation pending distinguished from no usable itinerary", "category"),
            ("min_minutes", "Minimum duration among available returned itineraries on this day", "minutes"),
            ("range_minutes", "Max minus min duration across best-point itineraries per requested departure; complementary dispersion", "minutes"),
            ("winning_access_point_id", "Stable access point of duration minimum; deterministic ID tie-break only", "identifier"),
            ("winning_requested_time", "Requested departure associated with minimum, not first boarding time", "time")]:
            definitions[prefix + "_" + suffix] = (prefix + ": " + desc, unit)
    entries = []
    for table, frame in frames.items():
        for field in frame.columns:
            if field in definitions:
                description, unit = definitions[field]
            elif field in old_definitions.index:
                description, unit = old_definitions.loc[field, ["description", "unit"]]
            else:
                raise ValueError(f"Undocumented variable: {table}.{field}")
            entries.append(dict(variable=field, table=table, description=description, unit=unit,
                data_type=str(frame[field].dtype), geographic_level="Existing access points/groups and municipal series, or explicit literature population",
                temporal_level="Sampled winter-2026 day/request or original study period", source_id=SOURCE,
                raw_or_derived="derived or retained source field", formula="See versioned builder, config and report 85",
                causal_role="descriptive proxy/review only, no exposure replacement", missing_share=f"{frame[field].isna().mean():.6f}",
                notes="No imputation, no walking speed/coincidence tolerance, no threshold or mode selected. Literature rows retain original source identifiers."))
    pd.concat([old_dictionary[~old_dictionary.table.isin(frames)], pd.DataFrame(entries).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna("").sort_values(["table", "variable"]).to_csv(path, index=False, lineterminator="\n")


def main():
    global LOCAL_EVIDENCE
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate-only", action="store_true", help="Require all valid versioned caches; do not reroute")
    parser.add_argument("--max-new-caches", type=int, help="Stop safely after this many new access-point/day checkpoints")
    args = parser.parse_args()
    config = json.loads((ROOT / CONFIG).read_text(encoding="utf-8"))
    LOCAL_EVIDENCE = validate_local_evidence(config["local_evidence"])
    protected = {p: sha(p) for p in PROTECTED}
    inputs = [CONFIG, "config/path_c_analysis.json", "reports/accessibility_station_access_nodes.csv", "reports/public_transport_journey_nodes.csv"]
    metadata = legacy.exact_metadata(legacy.SOURCE_ID)
    nodes = pd.read_csv(legacy.NODE_PATH, dtype={"selected_stop_id": str})
    municipal_nodes = pd.read_csv(legacy.OLD_NODE_PATH, dtype={"selected_stop_id": str})
    municipal_nodes = municipal_nodes[municipal_nodes.node_role.eq("municipality_origin")].copy()
    if len(nodes) != 75 or len(municipal_nodes) != 186:
        raise ValueError("Approved universe changed")
    settings = json.loads(legacy.CONFIG_PATH.read_text(encoding="utf-8"))["public_transport_journey_context"]
    fingerprint = hashlib.sha256(json.dumps({
        "inputs": {p: sha(p) for p in inputs}, "gtfs": metadata["sha256"],
        "code": {p: sha(p) for p in ["src/data_processing/build_accessibility_reference_time_v2.py",
            "src/data_processing/gtfs_static_router.py", "src/data_processing/build_accessibility_station_group_journeys.py",
            "src/data_processing/build_public_transport_journey_context.py"]}}, sort_keys=True).encode()).hexdigest()
    legacy.sample_row = revised_sample  # process-local adapter; old files/code unchanged
    archive = ROOT / metadata["raw_file"]
    reference = trips = None
    all_rows = []
    new_caches = 0
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = dict(specification_version=config["specification_version"], fingerprint=fingerprint,
        protected_legacy_sha256=protected, canonical_outputs_changed=False,
        expected_access_day_caches=150, output_paths=OUTPUTS, status="routing_in_progress")
    for day_label, date in settings["reference_dates"].items():
        network = connections = None
        for number, node in enumerate(nodes.itertuples(index=False), 1):
            code = hashlib.sha256(node.access_point_id.encode()).hexdigest()[:20]
            path = CACHE / date / (code + ".csv")
            meta_path = path.with_suffix(".metadata.json")
            valid = False
            if path.exists() and meta_path.exists():
                checkpoint = json.loads(meta_path.read_text(encoding="utf-8"))
                valid = checkpoint.get("fingerprint") == fingerprint and checkpoint.get("sha256") == hashlib.sha256(path.read_bytes()).hexdigest()
            if valid:
                frame = pd.read_csv(path, dtype={"reference_date": str, "origin_stop_id": str, "destination_stop_id": str})
                if len(frame) != 2232:
                    raise ValueError("Checkpoint grain mismatch")
                all_rows.extend(frame.to_dict("records"))
                print(f"{date} {number}/75 cached {node.access_point_name}", flush=True)
                continue
            if args.aggregate_only:
                raise ValueError(f"Missing or invalid checkpoint {date} {node.access_point_id}; resume routing first")
            if args.max_new_caches is not None and new_caches >= args.max_new_caches:
                manifest.update(status="checkpointed_partial_routing", completed_in_this_run=new_caches)
                (ROOT / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                return
            if network is None:
                if reference is None:
                    print("Load immutable GTFS reference and active trips", flush=True)
                    reference = legacy.load_feed_reference_tables(archive)
                    legacy.validate_settings({"public_transport_journey_context": settings}, reference)
                    trips = legacy.load_active_trip_info(archive, reference, list(settings["reference_dates"].values()))
                print(f"Build network {date}", flush=True)
                network = legacy.build_day_network(archive, reference, trips, date, int(settings["default_transfer_seconds"]))
                connections = legacy.flatten_connections(network)
            print(f"{date} {number}/75 route {node.access_point_name}", flush=True)
            rows = legacy.route_group(network, connections, nodes[nodes.access_point_id.eq(node.access_point_id)], municipal_nodes, settings, date, day_label)
            frame = pd.DataFrame(rows)
            path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(path, index=False, lineterminator="\n")
            checkpoint = dict(fingerprint=fingerprint, rows=len(rows), access_point_id=node.access_point_id,
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            meta_path.write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
            all_rows.extend(rows)
            new_caches += 1
            manifest.update(last_completed_date=date, last_completed_access_point=node.access_point_id,
                            completed_in_this_run=new_caches)
            (ROOT / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        del network, connections
        gc.collect()
    samples = pd.DataFrame(all_rows)
    if len(samples) != 334800 or samples.duplicated(["access_point_id", "municipality_bfs_id", "reference_date", "direction", "requested_departure_time"]).any():
        raise ValueError("Access-point query grain mismatch")
    daily, pairs = aggregate(samples, list(settings["reference_dates"].values()))
    old = pd.read_csv(legacy.PAIR_OUTPUT)[["station_group_id", "municipality_bfs_id", "mean_one_way_generalized_minutes", "routing_pair_complete"]].rename(columns={
        "mean_one_way_generalized_minutes": "old_mean_including_wait_minutes", "routing_pair_complete": "old_24_of_24_complete"})
    pairs = pairs.merge(old, on=["station_group_id", "municipality_bfs_id"], validate="one_to_one")
    pairs["difference_from_old_minutes"] = pairs.reference_time_minutes - pairs.old_mean_including_wait_minutes
    local = pd.read_csv(ROOT / "reports/accessibility_local_node_audit.csv")
    local["actual_local_duration_minutes"] = np.nan
    local["endpoint_evidence_status"] = "actual_origin_departure_and_walking_duration_to_document"
    literature = pd.DataFrame(json.loads((ROOT / "config/accessibility_mobility_literature_review.json").read_text(encoding="utf-8")))
    statuses = samples.groupby(["reference_date", "direction", "journey_feasible", "journey_exclusion_reason", "local_access_status"], dropna=False).size().reset_index(name="query_count")
    frames = dict(zip(OUTPUTS, [samples, daily, pairs, local, literature, statuses]))
    for table, frame in frames.items():
        frame.to_csv(ROOT / OUTPUTS[table], index=False, lineterminator="\n")
    if protected != {p: sha(p) for p in PROTECTED}:
        raise RuntimeError("Protected legacy outputs changed")
    register(frames)
    manifest.update(status="completed_node_proxy_local_documentation_pending",
        output_row_counts={k: len(v) for k, v in frames.items()}, output_sha256={p: sha(p) for p in OUTPUTS.values()},
        pairs_with_two_day_time=int(pairs.reference_time_minutes.notna().sum()),
        newly_available_pairs=int((pairs.reference_time_minutes.notna() & ~truth(pairs.old_24_of_24_complete)).sum()),
        local_pending_pairs=int(truth(pairs.local_access_pending).sum()),
        actual_station_access_verified_pairs=0, main_threshold_selected=False, reference_mode_selected=False)
    (ROOT / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: manifest[k] for k in ["status", "output_row_counts", "pairs_with_two_day_time", "newly_available_pairs", "local_pending_pairs"]}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
