"""Route the 39 priority municipality--station-group pairs on the 2018 GTFS.

The archive is supplied manually because the official archive host disallows
automated collection.  This builder verifies the immutable ZIP before use,
audits current-to-historical stop continuity, applies only the two reviewed
stop crosswalks recorded in configuration, and reproduces the 2026 sampling
windows on a Wednesday and Saturday in February 2018.
"""

from __future__ import annotations

import gc
import hashlib
import json
import pickle
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "data_processing"))

from build_public_transport_journey_context import better_sample, sample_row  # noqa: E402
from gtfs_static_router import (  # noqa: E402
    build_day_network,
    build_destination_profile,
    flatten_connections,
    forward_raptor,
    load_active_trip_info,
    load_feed_reference_tables,
    normalize_stop_id,
    parse_gtfs_time,
)


CONFIG_PATH = ROOT / "config" / "accessibility_historical_gtfs_2018.json"
WORKLIST_PATH = ROOT / "reports" / "accessibility_historical_gtfs_2018_manual_worklist.csv"
ACCESS_NODES_PATH = ROOT / "reports" / "accessibility_station_access_nodes.csv"
FIRST_EXPOSURE_PATH = ROOT / "reports" / "accessibility_first_exposure_audit.csv"

SAMPLE_OUTPUT = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_journey_samples.csv"
CONTEXT_OUTPUT = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_journey_context.csv"
STOP_AUDIT_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_stop_audit.csv"
MUNICIPALITY_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_municipality_validation.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "61_COMPARAISON_ACCES_HISTORIQUE_2018_2026_FR.md"
CACHE_DIR = ROOT / "data_interim" / "accessibility_historical_gtfs_2018_routes"
NETWORK_CACHE_DIR = CACHE_DIR / "day_networks"

INTERPRETATION = (
    "official_winter_2018_gtfs_static_targeted_historical_access_validation_"
    "using_reviewed_current_access_points_not_real_time_or_causal"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pipe_unique(values: pd.Series) -> str:
    return "|".join(sorted({str(value) for value in values.dropna() if str(value)}))


def validate_archive(config: dict) -> tuple[Path, dict]:
    archive_path = ROOT / config["expected_manual_local_path"]
    if not archive_path.exists():
        raise FileNotFoundError(
            f"Manual historical GTFS missing: {config['expected_manual_local_path']}"
        )
    if archive_path.stat().st_size != int(config["verified_file_size_bytes"]):
        raise ValueError("Historical GTFS file size differs from the recorded source")
    digest = sha256(archive_path)
    if digest.lower() != str(config["sha256"]).lower():
        raise ValueError("Historical GTFS SHA-256 differs from the recorded source")
    with zipfile.ZipFile(archive_path) as archive:
        bad_member = archive.testzip()
        required = {
            "agency.txt", "routes.txt", "trips.txt", "stops.txt",
            "calendar.txt", "calendar_dates.txt", "transfers.txt",
            "feed_info.txt", "stop_times.txt",
        }
        if bad_member is not None:
            raise ValueError(f"Corrupt historical GTFS member: {bad_member}")
        if set(archive.namelist()) != required:
            raise ValueError("Historical GTFS member inventory changed")
    return archive_path, {"sha256": digest, "size_bytes": archive_path.stat().st_size}


def load_stop_lookup(archive_path: Path) -> tuple[pd.DataFrame, dict[str, dict]]:
    with zipfile.ZipFile(archive_path) as archive:
        stops = pd.read_csv(archive.open("stops.txt"), dtype="string")
    stops["base_stop_id"] = stops.stop_id.map(normalize_stop_id)
    stops["stop_lat"] = pd.to_numeric(stops.stop_lat, errors="coerce")
    stops["stop_lon"] = pd.to_numeric(stops.stop_lon, errors="coerce")
    lookup = {}
    for stop_id, group in stops.groupby("base_stop_id", sort=False):
        named = group[group.stop_name.notna()]
        row = (named if len(named) else group).iloc[0]
        lookup[str(stop_id)] = {
            "historical_stop_name": str(row.stop_name),
            "historical_stop_latitude": float(row.stop_lat),
            "historical_stop_longitude": float(row.stop_lon),
        }
    return stops, lookup


def map_stop(current_stop_id: str, lookup: dict[str, dict], config: dict) -> dict:
    current_stop_id = normalize_stop_id(str(current_stop_id))
    if current_stop_id in lookup:
        return {
            "historical_stop_id": current_stop_id,
            **lookup[current_stop_id],
            "mapping_method": "exact_normalized_stop_id",
            "mapping_distance_from_access_point_km": 0.0,
            "mapping_review_note": "Stable normalized stop identifier in the 2018 feed.",
        }
    override = config.get("historical_stop_overrides", {}).get(current_stop_id)
    if not override:
        return {
            "historical_stop_id": "",
            "historical_stop_name": "",
            "historical_stop_latitude": np.nan,
            "historical_stop_longitude": np.nan,
            "mapping_method": "unresolved_current_stop_absent_from_2018_feed",
            "mapping_distance_from_access_point_km": np.nan,
            "mapping_review_note": "No reviewed historical equivalent is recorded.",
        }
    historical_id = normalize_stop_id(str(override["historical_stop_id"]))
    if historical_id not in lookup:
        raise ValueError(f"Reviewed historical stop is absent: {historical_id}")
    if str(override["historical_stop_name"]) != lookup[historical_id]["historical_stop_name"]:
        raise ValueError(f"Reviewed historical stop name changed: {historical_id}")
    return {
        "historical_stop_id": historical_id,
        **lookup[historical_id],
        "mapping_method": override["mapping_method"],
        "mapping_distance_from_access_point_km": float(
            override["distance_from_access_point_km"]
        ),
        "mapping_review_note": override["review_note"],
    }


def prepare_nodes(
    worklist: pd.DataFrame,
    access_nodes: pd.DataFrame,
    lookup: dict[str, dict],
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    origins = worklist[
        ["municipality_bfs_id", "municipality_name", "municipality_main_stop_id",
         "municipality_main_stop_name"]
    ].drop_duplicates().copy()
    if len(origins) != 19 or not origins.municipality_bfs_id.is_unique:
        raise ValueError("Expected 19 unique municipality origins")
    origin_rows = []
    for row in origins.itertuples(index=False):
        mapped = map_stop(row.municipality_main_stop_id, lookup, config)
        origin_rows.append({
            "node_role": "municipality_origin",
            "municipality_bfs_id": int(row.municipality_bfs_id),
            "station_group_id": "",
            "access_point_id": "",
            "access_point_name": "",
            "current_stop_id": str(row.municipality_main_stop_id),
            "current_stop_name": row.municipality_main_stop_name,
            **mapped,
        })

    group_ids = set(worklist.station_group_id)
    destinations = access_nodes[access_nodes.station_group_id.isin(group_ids)].copy()
    if len(destinations) != 12 or destinations.access_point_id.nunique() != 12:
        raise ValueError("Expected 12 current access points for the ten priority groups")
    destination_rows = []
    for row in destinations.itertuples(index=False):
        mapped = map_stop(row.selected_stop_id, lookup, config)
        destination_rows.append({
            "node_role": "station_group_access",
            "municipality_bfs_id": pd.NA,
            "station_group_id": row.station_group_id,
            "station_group_name": row.station_group_name,
            "access_point_id": row.access_point_id,
            "access_point_name": row.access_point_name,
            "access_point_latitude": float(row.reference_latitude),
            "access_point_longitude": float(row.reference_longitude),
            "current_stop_id": str(row.selected_stop_id),
            "current_stop_name": row.selected_stop_name,
            **mapped,
        })
    origin_nodes = pd.DataFrame(origin_rows)
    destination_nodes = pd.DataFrame(destination_rows)
    audit = pd.concat([origin_nodes, destination_nodes], ignore_index=True, sort=False)
    return origin_nodes, destination_nodes, audit


def add_active_stop_audit(audit: pd.DataFrame, networks: dict[str, object]) -> pd.DataFrame:
    result = audit.copy()
    for day_label, network in networks.items():
        active = {
            stop_id for stop_id, index in network.stop_index.items()
            if network.stop_patterns[index]
        }
        result[f"active_in_{day_label}"] = result.historical_stop_id.astype(str).isin(active)
    active_columns = [column for column in result if column.startswith("active_in_")]
    result["historical_stop_found"] = result.historical_stop_id.astype(str).ne("")
    result["historical_node_usable"] = (
        result.historical_stop_found & result[active_columns].all(axis=1)
    )
    result["historical_source_id"] = "SKI_GTFS_TIMETABLE_2018_WINTER_20180207"
    result["causal_accessibility_feature_approved"] = False
    return result


def fingerprint(
    config: dict, archive_sha: str, date: str, group_pairs: pd.DataFrame,
    group_nodes: pd.DataFrame, origin_nodes: pd.DataFrame,
) -> str:
    digest = hashlib.sha256()
    digest.update(archive_sha.encode("ascii"))
    digest.update(date.encode("ascii"))
    digest.update(json.dumps(config, sort_keys=True).encode("utf-8"))
    for frame in [group_pairs, group_nodes, origin_nodes]:
        digest.update(frame.to_csv(index=False, lineterminator="\n").encode("utf-8"))
    digest.update(sha256(Path(__file__)).encode("ascii"))
    digest.update(sha256(ROOT / "src/data_processing/gtfs_static_router.py").encode("ascii"))
    return digest.hexdigest()


def cache_paths(date: str, group_id: str) -> tuple[Path, Path]:
    safe = hashlib.sha1(group_id.encode("utf-8")).hexdigest()[:16]
    base = CACHE_DIR / date / safe
    return base.with_suffix(".csv"), base.with_suffix(".metadata.json")


def load_cache(date: str, group_id: str, digest: str, rows: int):
    data_path, metadata_path = cache_paths(date, group_id)
    if not data_path.exists() or not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("fingerprint") != digest or metadata.get("rows") != rows:
        return None
    data = pd.read_csv(
        data_path,
        dtype={"origin_stop_id": str, "destination_stop_id": str},
    )
    return data.to_dict("records") if len(data) == rows else None


def write_cache(date: str, group_id: str, digest: str, rows: list[dict]) -> None:
    data_path, metadata_path = cache_paths(date, group_id)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(data_path, index=False, lineterminator="\n")
    metadata_path.write_text(
        json.dumps({
            "station_group_id": group_id,
            "reference_date": date,
            "fingerprint": digest,
            "rows": len(rows),
        }, indent=2) + "\n",
        encoding="utf-8",
    )


def network_cache_fingerprint(config: dict, archive_sha: str, date: str) -> str:
    digest = hashlib.sha256()
    digest.update(archive_sha.encode("ascii"))
    digest.update(date.encode("ascii"))
    digest.update(str(config["default_transfer_seconds"]).encode("ascii"))
    digest.update(sha256(ROOT / "src/data_processing/gtfs_static_router.py").encode("ascii"))
    return digest.hexdigest()


def load_network_cache(date: str, digest: str):
    data_path = NETWORK_CACHE_DIR / f"{date}.pickle"
    metadata_path = NETWORK_CACHE_DIR / f"{date}.metadata.json"
    if not data_path.exists() or not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("fingerprint") != digest:
        return None
    with data_path.open("rb") as handle:
        return pickle.load(handle)


def write_network_cache(date: str, digest: str, network) -> None:
    NETWORK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data_path = NETWORK_CACHE_DIR / f"{date}.pickle"
    metadata_path = NETWORK_CACHE_DIR / f"{date}.metadata.json"
    with data_path.open("wb") as handle:
        pickle.dump(network, handle, protocol=pickle.HIGHEST_PROTOCOL)
    metadata_path.write_text(
        json.dumps({
            "reference_date": date,
            "fingerprint": digest,
            "network_summary": network.pattern_summary,
        }, indent=2) + "\n",
        encoding="utf-8",
    )


def stop_is_active(network, stop_id: str) -> bool:
    index = network.stop_index.get(str(stop_id))
    return index is not None and bool(network.stop_patterns[index])


def route_group_day(
    network,
    connections,
    group_pairs: pd.DataFrame,
    group_nodes: pd.DataFrame,
    origin_nodes: pd.DataFrame,
    config: dict,
    day_label: str,
    date: str,
) -> list[dict]:
    outbound_times = [parse_gtfs_time(value) for value in config["outbound_sample_times"]]
    return_times = [parse_gtfs_time(value) for value in config["return_sample_times"]]
    maximum_legs = int(config["maximum_vehicle_legs"])
    maximum_minutes = int(config["maximum_generalized_elapsed_minutes"])
    origin_lookup = origin_nodes.set_index("municipality_bfs_id")
    samples: dict[tuple, dict] = {}

    for access in group_nodes.itertuples(index=False):
        destination = pd.Series({
            "selected_stop_id": str(access.historical_stop_id),
            "selected_stop_name": access.historical_stop_name,
            "component_resort_id": access.access_point_id,
            "component_resort_name": access.access_point_name,
        })
        stop_id = str(access.historical_stop_id)
        profile = (
            build_destination_profile(
                network, connections, stop_id, maximum_legs,
                min(outbound_times), max(outbound_times) + maximum_minutes * 60,
            )
            if stop_is_active(network, stop_id)
            else None
        )
        for pair_row in group_pairs.itertuples(index=False):
            origin_row = origin_lookup.loc[int(pair_row.municipality_bfs_id)]
            origin = pd.Series({
                "selected_stop_id": str(origin_row.historical_stop_id),
                "selected_stop_name": origin_row.historical_stop_name,
            })
            pair = {
                "station_group_id": pair_row.station_group_id,
                "station_group_name": pair_row.station_group_name,
                "municipality_bfs_id": int(pair_row.municipality_bfs_id),
                "municipality_name": pair_row.municipality_name,
            }
            for requested in outbound_times:
                journey = (
                    profile.query(str(origin_row.historical_stop_id), requested)
                    if profile is not None and stop_is_active(
                        network, str(origin_row.historical_stop_id)
                    )
                    else None
                )
                row = sample_row(
                    pair, "outbound_municipality_to_destination", day_label, date,
                    requested, origin, destination, journey, maximum_legs, maximum_minutes,
                )
                row.update({
                    "current_2026_origin_stop_id": origin_row.current_stop_id,
                    "historical_origin_mapping_method": origin_row.mapping_method,
                    "historical_destination_access_point_id": access.access_point_id,
                    "historical_destination_access_point_name": access.access_point_name,
                    "current_2026_destination_stop_id": access.current_stop_id,
                    "historical_destination_mapping_method": access.mapping_method,
                    "source_id": config["source_id"],
                    "interpretation": INTERPRETATION,
                })
                key = (
                    pair_row.station_group_id, int(pair_row.municipality_bfs_id),
                    "outbound_municipality_to_destination", date, requested,
                )
                samples[key] = better_sample(samples.get(key), row)
        del profile
        gc.collect()

        for requested in return_times:
            routes = (
                forward_raptor(network, stop_id, requested, maximum_legs)
                if stop_is_active(network, stop_id)
                else {}
            )
            for pair_row in group_pairs.itertuples(index=False):
                origin_row = origin_lookup.loc[int(pair_row.municipality_bfs_id)]
                municipality = pd.Series({
                    "selected_stop_id": str(origin_row.historical_stop_id),
                    "selected_stop_name": origin_row.historical_stop_name,
                })
                pair = {
                    "station_group_id": pair_row.station_group_id,
                    "station_group_name": pair_row.station_group_name,
                    "municipality_bfs_id": int(pair_row.municipality_bfs_id),
                    "municipality_name": pair_row.municipality_name,
                }
                journey = routes.get(str(origin_row.historical_stop_id)) \
                    if stop_is_active(network, str(origin_row.historical_stop_id)) else None
                row = sample_row(
                    pair, "return_destination_to_municipality", day_label, date,
                    requested, destination, municipality, journey,
                    maximum_legs, maximum_minutes,
                )
                row.update({
                    "destination_component_resort_id": access.access_point_id,
                    "destination_component_resort_name": access.access_point_name,
                    "current_2026_origin_stop_id": access.current_stop_id,
                    "historical_origin_mapping_method": access.mapping_method,
                    "historical_destination_access_point_id": access.access_point_id,
                    "historical_destination_access_point_name": access.access_point_name,
                    "current_2026_destination_stop_id": origin_row.current_stop_id,
                    "historical_destination_mapping_method": origin_row.mapping_method,
                    "source_id": config["source_id"],
                    "interpretation": INTERPRETATION,
                })
                key = (
                    pair_row.station_group_id, int(pair_row.municipality_bfs_id),
                    "return_destination_to_municipality", date, requested,
                )
                samples[key] = better_sample(samples.get(key), row)
        gc.collect()

    expected = len(group_pairs) * (len(outbound_times) + len(return_times))
    if len(samples) != expected:
        raise ValueError(f"Unexpected historical group-day sample count: {len(samples)}")
    return list(samples.values())


def aggregate_context(
    samples: pd.DataFrame,
    worklist: pd.DataFrame,
    origin_nodes: pd.DataFrame,
    destination_nodes: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    expected_outbound = len(config["reference_dates"]) * len(config["outbound_sample_times"])
    expected_return = len(config["reference_dates"]) * len(config["return_sample_times"])
    origin_lookup = origin_nodes.set_index("municipality_bfs_id")
    rows = []
    keys = ["station_group_id", "station_group_name", "municipality_bfs_id", "municipality_name"]
    for values, group in samples.groupby(keys, sort=False, dropna=False):
        row = dict(zip(keys, values))
        origin = origin_lookup.loc[int(row["municipality_bfs_id"])]
        group_destinations = destination_nodes[
            destination_nodes.station_group_id.eq(row["station_group_id"])
        ]
        row.update({
            "current_2026_municipality_main_stop_id": origin.current_stop_id,
            "historical_municipality_main_stop_id": origin.historical_stop_id,
            "historical_municipality_main_stop_name": origin.historical_stop_name,
            "historical_origin_mapping_method": origin.mapping_method,
            "historical_origin_stop_found": bool(str(origin.historical_stop_id)),
            "historical_destination_stop_found": bool(
                group_destinations.historical_stop_id.astype(str).ne("").any()
            ),
        })
        for direction, prefix, expected in [
            ("outbound_municipality_to_destination", "historical_outbound", expected_outbound),
            ("return_destination_to_municipality", "historical_return", expected_return),
        ]:
            subset = group[group.direction.eq(direction)]
            feasible = subset[as_bool(subset.journey_feasible)]
            row[f"{prefix}_scheduled_samples"] = len(subset)
            row[f"{prefix}_feasible_samples"] = len(feasible)
            row[f"{prefix}_sample_coverage_share"] = len(feasible) / expected
            for metric in ["initial_wait_minutes", "scheduled_journey_minutes",
                           "generalized_elapsed_minutes"]:
                numeric = pd.to_numeric(feasible[metric], errors="coerce")
                row[f"{prefix}_mean_{metric}"] = float(numeric.mean()) if len(feasible) else np.nan
                row[f"{prefix}_maximum_{metric}"] = float(numeric.max()) if len(feasible) else np.nan
            transfers = pd.to_numeric(feasible.transfers, errors="coerce")
            row[f"{prefix}_maximum_transfers"] = (
                int(transfers.max()) if transfers.notna().any() else pd.NA
            )
            row[f"{prefix}_transport_modes"] = pipe_unique(feasible.transport_modes)
            row[f"{prefix}_access_point_ids_used"] = pipe_unique(
                feasible.destination_component_resort_id
            )
            row[f"{prefix}_access_point_names_used"] = pipe_unique(
                feasible.destination_component_resort_name
            )
        outbound = row["historical_outbound_mean_generalized_elapsed_minutes"]
        returned = row["historical_return_mean_generalized_elapsed_minutes"]
        row["historical_mean_one_way_generalized_minutes"] = (
            (outbound + returned) / 2
            if pd.notna(outbound) and pd.notna(returned) else np.nan
        )
        row["historical_routing_pair_complete"] = bool(
            row["historical_outbound_sample_coverage_share"] == 1
            and row["historical_return_sample_coverage_share"] == 1
        )
        row["historical_route_computed"] = bool(
            row["historical_origin_stop_found"]
            and row["historical_destination_stop_found"]
            and row["historical_outbound_scheduled_samples"] == expected_outbound
            and row["historical_return_scheduled_samples"] == expected_return
        )
        value = row["historical_mean_one_way_generalized_minutes"]
        for threshold in [30, 60, 90, 120]:
            row[f"historical_within_{threshold}_minutes"] = bool(
                pd.notna(value) and value <= threshold
            )
        if not row["historical_route_computed"]:
            status = "endpoint_not_found_or_route_not_computed"
        elif not row["historical_routing_pair_complete"]:
            status = "computed_but_incomplete_sample_coverage"
        elif row["historical_within_120_minutes"]:
            status = "validated_complete_within_120_minutes"
        else:
            status = "complete_but_above_120_minutes"
        row["historical_access_plausibility_status"] = status
        row["historical_access_validated"] = status == "validated_complete_within_120_minutes"
        row["reference_dates"] = "|".join(config["reference_dates"].values())
        row["source_id"] = config["source_id"]
        row["interpretation"] = INTERPRETATION
        row["causal_accessibility_feature_approved"] = False
        rows.append(row)

    result = pd.DataFrame(rows)
    if len(result) != 39 or result.duplicated(
        ["station_group_id", "municipality_bfs_id"]
    ).any():
        raise ValueError("Expected 39 unique historical route contexts")
    current = worklist[[
        "station_group_id", "municipality_bfs_id", "mean_one_way_generalized_minutes"
    ]].rename(columns={
        "mean_one_way_generalized_minutes": "current_2026_mean_one_way_generalized_minutes"
    })
    result = result.merge(
        current, on=["station_group_id", "municipality_bfs_id"],
        how="left", validate="one_to_one",
    )
    result["signed_2018_to_2026_time_change_minutes"] = (
        result.current_2026_mean_one_way_generalized_minutes
        - result.historical_mean_one_way_generalized_minutes
    )
    result["absolute_2018_to_2026_time_change_minutes"] = (
        result.signed_2018_to_2026_time_change_minutes.abs()
    )
    result["relative_2018_to_2026_time_change_percent"] = (
        result.signed_2018_to_2026_time_change_minutes
        / result.historical_mean_one_way_generalized_minutes * 100
    )
    return result.sort_values(
        ["municipality_bfs_id", "station_group_name"], kind="stable"
    )


def update_worklist(worklist: pd.DataFrame, context: pd.DataFrame, config: dict) -> pd.DataFrame:
    base_columns = [
        "municipality_bfs_id", "municipality_name", "municipality_main_stop_id",
        "municipality_main_stop_name", "station_group_id", "station_group_name",
        "outbound_access_point_ids_used", "outbound_access_point_names_used",
        "return_access_point_ids_used", "return_access_point_names_used",
        "mean_one_way_generalized_minutes",
    ]
    result = worklist[base_columns].merge(
        context.drop(columns=["station_group_name", "municipality_name"]),
        on=["station_group_id", "municipality_bfs_id"],
        how="left", validate="one_to_one",
    )
    result["historical_timetable_year"] = int(config["timetable_year"])
    result["historical_snapshot_build"] = config["snapshot_build"]
    result["historical_archive_url"] = config["archive_url"]
    result["expected_manual_local_path"] = config["expected_manual_local_path"]
    result["manual_download_required_due_to_robots"] = True
    return result.sort_values(
        ["municipality_bfs_id", "station_group_name"], kind="stable"
    )


def municipality_validation(context: pd.DataFrame, first: pd.DataFrame) -> pd.DataFrame:
    rows = []
    first_lookup = first.set_index("municipality_bfs_id")
    for municipality_id, group in context.groupby("municipality_bfs_id", sort=True):
        original = first_lookup.loc[int(municipality_id)]
        within = as_bool(group.historical_within_120_minutes)
        complete = as_bool(group.historical_routing_pair_complete)
        validated = as_bool(group.historical_access_validated)
        row = {
            "municipality_bfs_id": int(municipality_id),
            "municipality_name": group.municipality_name.iloc[0],
            "first_exposure_month": original.first_exposure_month,
            "current_founding_groups_within_120_minutes": len(group),
            "historical_founding_groups_with_complete_routes": int(complete.sum()),
            "historical_founding_groups_within_120_minutes": int(within.sum()),
            "historical_validated_group_ids": pipe_unique(
                group.loc[validated, "station_group_id"]
            ),
            "historical_validated_group_names": pipe_unique(
                group.loc[validated, "station_group_name"]
            ),
            "historical_first_exposure_retained": bool(within.any()),
            "all_current_founding_groups_historically_within_120_minutes": bool(
                len(group) and within.all()
            ),
            "historical_first_exposure_design_review_status": (
                "retained_all_current_founding_groups"
                if len(group) and within.all()
                else "retained_with_revised_founding_group_mix"
                if within.any()
                else "not_retained_at_120_minutes"
            ),
            "causal_first_exposure_treatment_approved": False,
            "source_id": "SKI_GTFS_TIMETABLE_2018_WINTER_20180207",
        }
        rows.append(row)
    result = pd.DataFrame(rows)
    if len(result) != 19:
        raise ValueError("Expected 19 municipality-level historical validations")
    return result


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    archive_path, archive_metadata = validate_archive(config)
    worklist = pd.read_csv(WORKLIST_PATH, dtype={"municipality_main_stop_id": str})
    access_nodes = pd.read_csv(ACCESS_NODES_PATH, dtype={"selected_stop_id": str})
    first = pd.read_csv(FIRST_EXPOSURE_PATH)
    if len(worklist) != 39:
        raise ValueError("Expected 39 priority historical routes")

    _, stop_lookup = load_stop_lookup(archive_path)
    origin_nodes, destination_nodes, stop_audit = prepare_nodes(
        worklist, access_nodes, stop_lookup, config
    )
    reference = load_feed_reference_tables(archive_path)
    feed = reference["feed"]
    if str(feed.get("feed_version")) != "20180206":
        raise ValueError(f"Unexpected historical GTFS version: {feed.get('feed_version')}")
    dates = list(config["reference_dates"].values())
    trip_reference = load_active_trip_info(archive_path, reference, dates)

    group_ids = sorted(worklist.station_group_id.unique())
    cached: dict[tuple[str, str], list[dict] | None] = {}
    fingerprints = {}
    rows_per_day = {}
    for day_label, date in config["reference_dates"].items():
        for group_id in group_ids:
            pairs = worklist[worklist.station_group_id.eq(group_id)][[
                "station_group_id", "station_group_name", "municipality_bfs_id",
                "municipality_name", "municipality_main_stop_id",
            ]].copy()
            nodes = destination_nodes[destination_nodes.station_group_id.eq(group_id)].copy()
            origins = origin_nodes[
                origin_nodes.municipality_bfs_id.isin(pairs.municipality_bfs_id)
            ].copy()
            digest = fingerprint(
                config, archive_metadata["sha256"], date, pairs, nodes, origins
            )
            expected = len(pairs) * (
                len(config["outbound_sample_times"]) + len(config["return_sample_times"])
            )
            fingerprints[(date, group_id)] = digest
            rows_per_day[(date, group_id)] = expected
            cached[(date, group_id)] = load_cache(date, group_id, digest, expected)

    all_rows = []
    networks = {}
    network_summaries = []
    for day_label, date in config["reference_dates"].items():
        day_missing = any(cached[(date, group_id)] is None for group_id in group_ids)
        network_digest = network_cache_fingerprint(
            config, archive_metadata["sha256"], date
        )
        network = load_network_cache(date, network_digest)
        if network is None:
            network = build_day_network(
                archive_path, reference, trip_reference, date,
                int(config["default_transfer_seconds"]),
                drop_invalid_time_trips=True,
            )
            write_network_cache(date, network_digest, network)
        else:
            print(f"{date} network cache", flush=True)
        networks[day_label] = network
        network_summaries.append(network.pattern_summary)
        connections = flatten_connections(network) if day_missing else None
        for number, group_id in enumerate(group_ids, start=1):
            rows = cached[(date, group_id)]
            if rows is None:
                name = worklist.loc[
                    worklist.station_group_id.eq(group_id), "station_group_name"
                ].iloc[0]
                print(f"{date} {number}/{len(group_ids)} route {name}", flush=True)
                pairs = worklist[worklist.station_group_id.eq(group_id)].copy()
                nodes = destination_nodes[
                    destination_nodes.station_group_id.eq(group_id)
                ].copy()
                origins = origin_nodes[
                    origin_nodes.municipality_bfs_id.isin(pairs.municipality_bfs_id)
                ].copy()
                rows = route_group_day(
                    network, connections, pairs, nodes, origins, config, day_label, date
                )
                write_cache(
                    date, group_id, fingerprints[(date, group_id)], rows
                )
            else:
                print(f"{date} {number}/{len(group_ids)} cache", flush=True)
            all_rows.extend(rows)
        del connections
        gc.collect()

    stop_audit = add_active_stop_audit(stop_audit, networks)
    if not as_bool(stop_audit.historical_node_usable).all():
        missing = stop_audit.loc[
            ~as_bool(stop_audit.historical_node_usable),
            ["node_role", "current_stop_id", "historical_stop_id"],
        ]
        raise ValueError(f"Historical route endpoint unusable:\n{missing}")
    stop_audit.to_csv(STOP_AUDIT_OUTPUT, index=False, lineterminator="\n")

    samples = pd.DataFrame(all_rows).sort_values([
        "station_group_id", "municipality_bfs_id", "direction",
        "reference_date", "requested_departure_time",
    ], kind="stable")
    if len(samples) != 39 * 24:
        raise ValueError(f"Unexpected historical sample count: {len(samples)}")
    samples.to_csv(SAMPLE_OUTPUT, index=False, lineterminator="\n")
    context = aggregate_context(
        samples, worklist, origin_nodes, destination_nodes, config
    )
    context.to_csv(CONTEXT_OUTPUT, index=False, lineterminator="\n")
    updated_worklist = update_worklist(worklist, context, config)
    updated_worklist.to_csv(WORKLIST_PATH, index=False, lineterminator="\n")
    municipality = municipality_validation(context, first)
    municipality.to_csv(MUNICIPALITY_OUTPUT, index=False, lineterminator="\n")

    status_counts = context.historical_access_plausibility_status.value_counts().to_dict()
    complete = int(as_bool(context.historical_routing_pair_complete).sum())
    validated = int(as_bool(context.historical_access_validated).sum())
    municipality_retained = int(as_bool(municipality.historical_first_exposure_retained).sum())
    all_groups_retained = int(as_bool(
        municipality.all_current_founding_groups_historically_within_120_minutes
    ).sum())
    comparable = context[
        context.historical_mean_one_way_generalized_minutes.notna()
    ]
    summary = {
        "analysis_date": "2026-10-03",
        "source_id": config["source_id"],
        "archive_url": config["archive_url"],
        "head_http_status": config["head_http_status"],
        "content_length_bytes": config["content_length_bytes"],
        "verified_file_size_bytes": archive_metadata["size_bytes"],
        "gtfs_sha256": archive_metadata["sha256"],
        "zip_integrity_check": config["zip_integrity_check"],
        "robots_policy_observed": config["robots_policy_observed"],
        "automated_download_allowed": False,
        "manual_download_required": True,
        "historical_feed_downloaded": True,
        "feed_version": str(feed.get("feed_version")),
        "feed_start_date": str(feed.get("feed_start_date")),
        "feed_end_date": str(feed.get("feed_end_date")),
        "reference_dates": config["reference_dates"],
        "first_exposure_candidate_municipalities": 19,
        "priority_group_municipality_routes": 39,
        "unique_founding_station_groups": 10,
        "unique_origin_stops": 19,
        "unique_current_destination_access_references": 12,
        "exact_stop_id_mappings": int(
            stop_audit.mapping_method.eq("exact_normalized_stop_id").sum()
        ),
        "reviewed_stop_overrides": int(
            (~stop_audit.mapping_method.eq("exact_normalized_stop_id")).sum()
        ),
        "historical_journey_samples": len(samples),
        "historical_feasible_journey_samples": int(as_bool(samples.journey_feasible).sum()),
        "historical_routes_computed": int(as_bool(context.historical_route_computed).sum()),
        "historical_complete_routes": complete,
        "historical_access_validated_routes": validated,
        "historical_routes_within_120_minutes": int(
            as_bool(context.historical_within_120_minutes).sum()
        ),
        "historical_access_status_counts": status_counts,
        "municipalities_retaining_at_least_one_founding_group_within_120_minutes": municipality_retained,
        "municipalities_retaining_all_current_founding_groups_within_120_minutes": all_groups_retained,
        "median_signed_2018_to_2026_time_change_minutes": (
            float(comparable.signed_2018_to_2026_time_change_minutes.median())
            if len(comparable) else None
        ),
        "median_absolute_2018_to_2026_time_change_minutes": (
            float(comparable.absolute_2018_to_2026_time_change_minutes.median())
            if len(comparable) else None
        ),
        "causal_accessibility_features_approved": 0,
        "network_summaries": network_summaries,
        "cache_directory": str(CACHE_DIR.relative_to(ROOT)).replace("\\", "/"),
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in [CONFIG_PATH, ACCESS_NODES_PATH, FIRST_EXPOSURE_PATH]
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Comparaison des accès historiques 2018–2026 — étape 14

## Résultat ciblé

L'archive GTFS 2018 fournie manuellement a été vérifiée puis appliquée aux **39 couples commune–groupe fondateur** du screening précédent. Ils représentent **19 communes**, **10 groupes-stations** et **12 points d'accès**. Le calcul reproduit les mêmes 24 horaires-types qu'en 2026 : mercredi et samedi, cinq départs aller et sept retours par jour.

| Contrôle ou résultat | Nombre |
|---|---:|
| Arrêts d'origine communaux retrouvés | 19 / 19 |
| Points d'accès avec identifiant stable | 10 / 12 |
| Points d'accès avec équivalent historique revu | 2 / 12 |
| Couples dont les 24 horaires sont réalisables | {complete} / 39 |
| Couples complets et à 120 minutes ou moins en 2018 | {validated} / 39 |
| Communes gardant au moins un groupe fondateur à 120 minutes ou moins | {municipality_retained} / 19 |
| Communes gardant tous leurs groupes fondateurs actuels à 120 minutes ou moins | {all_groups_retained} / 19 |

## Correspondances modifiées

Deux arrêts actuels n'existaient pas sous le même identifiant dans le flux 2018. La règle est la même que pour la sélection 2026 : arrêt actif de train ou de bus le plus proche du point d'accès officiel, avec revue du nom et de la distance.

- Les Diablerets : `8584841` devient `8501479` (Les Diablerets, train), à 0,578 km du point d'accès;
- Villars-Gryon : `8510070` devient `8579126` (Villars-sur-Ollon, temple, bus), à 0,451 km.

Les 29 autres nœuds nécessaires — 19 origines et 10 accès — conservent leur identifiant normalisé. Le détail se trouve dans `reports/accessibility_historical_gtfs_2018_stop_audit.csv`.

## Interprétation

`historical_access_validated` signifie uniquement qu'un couple dispose des 24 itinéraires planifiés et reste à 120 minutes ou moins dans le GTFS 2018. Cela renforce ou révise la plausibilité de l'exposition au moment de la première saison, mais ne prouve ni l'absence de changements intermédiaires, ni les tendances parallèles, ni un effet causal. Tous les drapeaux causaux restent donc à `false`.

Le changement signé est calculé comme **temps 2026 moins temps 2018**; sa médiane est de {summary['median_signed_2018_to_2026_time_change_minutes']:.1f} minutes pour les couples comparables. La médiane de la variation en valeur absolue est de {summary['median_absolute_2018_to_2026_time_change_minutes']:.1f} minutes.

## Fichiers produits

- `data_processed/accessibility_historical_gtfs_2018_journey_samples.csv` : 936 requêtes horaires;
- `data_processed/accessibility_historical_gtfs_2018_journey_context.csv` : un résultat par couple;
- `reports/accessibility_historical_gtfs_2018_municipality_validation.csv` : synthèse des 19 communes;
- `reports/accessibility_historical_gtfs_2018_summary.json` : paramètres, empreintes et comptes;
- `data_interim/accessibility_historical_gtfs_2018_routes/` : cache de reprise par groupe et par jour.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
