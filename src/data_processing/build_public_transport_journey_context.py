"""Build municipality-to-ski-destination scheduled public-transport context.

The analysis uses one official winter 2026 GTFS Static snapshot.  Municipality
origins are principal train stops (or principal terrestrial stops when no train
stop exists).  Ski-destination arrivals are served bus/train stops nearest to
the supplied component point inside its current municipality.  Cableways and
chairlifts are never selected as access nodes.
"""

from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer

from gtfs_static_router import (
    Journey,
    build_day_network,
    build_destination_profile,
    count_active_departures,
    flatten_connections,
    format_gtfs_time,
    forward_raptor,
    load_active_trip_info,
    load_feed_reference_tables,
    mode_mask_label,
    parse_gtfs_time,
)
from build_public_transport_stop_context import checked_source, load_stops


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
DISTANCE_PATH = ROOT / "data_processed" / "treatment_municipality_distance_exposure.csv"
UNIT_PATH = ROOT / "data_processed" / "treatment_destination_units.csv"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
POINT_MUNICIPALITY_PATH = ROOT / "data_processed" / "resort_point_municipality.csv"
SAMPLE_OUTPUT = ROOT / "data_processed" / "treatment_municipality_public_transport_journey_samples.csv"
SUMMARY_OUTPUT = ROOT / "data_processed" / "treatment_municipality_public_transport_journey_context.csv"
NODE_OUTPUT = ROOT / "reports" / "public_transport_journey_nodes.csv"
METRICS_OUTPUT = ROOT / "reports" / "public_transport_journey_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md"
CACHE_DIR = ROOT / "data_interim" / "public_transport_journey_context"

SOURCE_ID = "SKI_GTFS_TIMETABLE_2026_WINTER_20260207"
INTERPRETATION = (
    "official_2026_winter_gtfs_static_scheduled_journey_context_with_algorithmic_"
    "ground_stop_nodes_not_real_time_or_historically_stable_causal_accessibility"
)
GROUND_MODE_CODES = ("A", "B")


def exact_metadata(source_id: str) -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if len(records) != 1:
        raise ValueError(f"Expected one cached {source_id} record, found {len(records)}")
    record = records[0]
    raw_path = ROOT / record["raw_file"]
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Cached source checksum failure: {source_id}")
    return record


def validate_settings(config: dict, reference: dict) -> dict:
    settings = config["public_transport_journey_context"]
    required = {
        "source_id": SOURCE_ID,
        "feed_version": "20260207",
        "feed_start_date": "20251214",
        "feed_end_date": "20261212",
        "reference_dates": {
            "winter_weekday": "20260204",
            "winter_saturday": "20260207",
        },
        "outbound_sample_times": [
            "08:00:00", "08:30:00", "09:00:00", "09:30:00", "10:00:00"
        ],
        "return_sample_times": [
            "15:00:00", "15:30:00", "16:00:00", "16:30:00",
            "17:00:00", "17:30:00", "18:00:00"
        ],
        "municipality_origin_rule": (
            "highest_reference_day_departure_count_train_stop_inside_current_"
            "municipality_else_highest_count_ground_stop_inside_current_"
            "municipality_else_nearest_served_ground_stop"
        ),
        "resort_arrival_rule": (
            "nearest_reference_day_served_bus_or_train_stop_in_the_current_"
            "municipality_of_each_supplied_destination_component_point"
        ),
        "platform_normalization": "numeric_gtfs_stop_id_prefix_before_first_colon",
        "default_transfer_seconds": 120,
        "maximum_vehicle_legs": 6,
        "maximum_generalized_elapsed_minutes": 480,
        "historical_stability_status": "not_yet_verified_against_anchor_year_timetables",
        "interpretation": INTERPRETATION,
    }
    if settings != required:
        raise ValueError("Unexpected public-transport journey configuration")
    feed = reference["feed"]
    checks = {
        "feed_version": feed.get("feed_version"),
        "feed_start_date": feed.get("feed_start_date"),
        "feed_end_date": feed.get("feed_end_date"),
    }
    for key, actual in checks.items():
        if str(actual) != str(settings[key]):
            raise ValueError(f"GTFS {key} changed: {actual}")
    return settings


def mode_is_ground(code: str) -> bool:
    text = str(code) if pd.notna(code) else ""
    return any(code in text for code in GROUND_MODE_CODES)


def mode_has_train(code: str) -> bool:
    return "B" in (str(code) if pd.notna(code) else "")


def total_departures(stop_id: str, departure_counts: dict[str, dict[str, int]]) -> int:
    return sum(values.get(str(stop_id), 0) for values in departure_counts.values())


def point_distance_km(x1, y1, x2, y2) -> float:
    return float(np.hypot(float(x1) - float(x2), float(y1) - float(y2)) / 1000)


def select_municipality_nodes(
    passenger: pd.DataFrame,
    distance: pd.DataFrame,
    departure_counts: dict[str, dict[str, int]],
    settings: dict,
) -> pd.DataFrame:
    municipalities = distance[
        [
            "municipality_bfs_id",
            "boundary_bfs_id_2026",
            "boundary_bfs_bridge_status",
            "municipality_name",
            "municipality_boundary_name_2026",
            "municipality_representative_longitude",
            "municipality_representative_latitude",
        ]
    ].drop_duplicates()
    if len(municipalities) != 186 or not municipalities["municipality_bfs_id"].is_unique:
        raise ValueError("Unexpected hotel-municipality universe")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    x, y = transformer.transform(
        municipalities["municipality_representative_longitude"].to_numpy(),
        municipalities["municipality_representative_latitude"].to_numpy(),
    )
    municipalities = municipalities.assign(origin_x_2056=x, origin_y_2056=y)
    ground = passenger[passenger["MoyenTransport_Code"].map(mode_is_ground)].copy()
    ground["stop_id"] = ground["Numero"].astype(str)
    ground["reference_departures"] = ground["stop_id"].map(
        lambda value: total_departures(value, departure_counts)
    )
    ground = ground[ground["reference_departures"].gt(0)].copy()
    ground["is_train_stop"] = ground["MoyenTransport_Code"].map(mode_has_train)

    rows = []
    for municipality in municipalities.itertuples(index=False):
        inside = ground[
            pd.to_numeric(ground["Commune_Numero"], errors="coerce").eq(
                int(municipality.boundary_bfs_id_2026)
            )
        ].copy()
        train = inside[inside["is_train_stop"]]
        if len(train):
            candidates = train.copy()
            method = "highest_departure_count_train_stop_inside_current_municipality"
        elif len(inside):
            candidates = inside.copy()
            method = "highest_departure_count_ground_stop_inside_current_municipality"
        else:
            candidates = ground.copy()
            method = "nearest_served_ground_stop_outside_current_municipality_fallback"
        candidates["representative_distance_km"] = candidates.apply(
            lambda row: point_distance_km(
                municipality.origin_x_2056,
                municipality.origin_y_2056,
                row["E"],
                row["N"],
            ),
            axis=1,
        )
        candidates["numeric_stop_id"] = pd.to_numeric(
            candidates["stop_id"], errors="coerce"
        )
        chosen = candidates.sort_values(
            ["reference_departures", "representative_distance_km", "numeric_stop_id"],
            ascending=[False, True, True],
            kind="stable",
        ).iloc[0]
        rows.append(
            {
                "node_role": "municipality_origin",
                "municipality_bfs_id": int(municipality.municipality_bfs_id),
                "boundary_bfs_id_2026": int(municipality.boundary_bfs_id_2026),
                "boundary_bfs_bridge_status": municipality.boundary_bfs_bridge_status,
                "municipality_name": municipality.municipality_name,
                "municipality_boundary_name_2026": municipality.municipality_boundary_name_2026,
                "component_resort_id": "",
                "component_resort_name": "",
                "selected_stop_id": str(chosen["stop_id"]),
                "selected_stop_name": str(chosen["Nom"]),
                "selected_stop_mode_code": str(chosen["MoyenTransport_Code"]),
                "selected_stop_mode": str(chosen["MoyenTransport_Designation"]),
                "selected_stop_municipality_bfs_id": int(chosen["Commune_Numero"]),
                "selected_stop_municipality_name": str(chosen["Commune_Nom"]),
                "selected_stop_reference_departures": int(chosen["reference_departures"]),
                "selected_stop_distance_from_reference_point_km": float(
                    chosen["representative_distance_km"]
                ),
                "selection_method": method,
                "selection_rule": settings["municipality_origin_rule"],
            }
        )
    return pd.DataFrame(rows)


def select_destination_nodes(
    passenger: pd.DataFrame,
    units: pd.DataFrame,
    distance: pd.DataFrame,
    resorts: pd.DataFrame,
    point_municipalities: pd.DataFrame,
    departure_counts: dict[str, dict[str, int]],
    settings: dict,
) -> pd.DataFrame:
    destination_ids = sorted(distance["destination_unit_id"].unique())
    units = units[units["destination_unit_id"].isin(destination_ids)].copy()
    if len(units) != len(destination_ids):
        raise ValueError("Distance-diagnostic destination units do not resolve uniquely")
    component_rows = []
    for unit in units.itertuples(index=False):
        for resort_id in str(unit.component_resort_ids).split("|"):
            component_rows.append(
                {
                    "destination_unit_id": unit.destination_unit_id,
                    "destination_name": unit.destination_name,
                    "component_resort_id": resort_id,
                }
            )
    components = pd.DataFrame(component_rows).merge(
        resorts[
            ["resort_id", "resort_name_canonical", "longitude", "latitude"]
        ],
        left_on="component_resort_id",
        right_on="resort_id",
        how="left",
        validate="many_to_one",
    ).merge(
        point_municipalities[
            ["resort_id", "point_municipality_bfs_id", "point_municipality_name", "selection_status"]
        ],
        on="resort_id",
        how="left",
        validate="many_to_one",
    )
    if components["resort_name_canonical"].isna().any():
        raise ValueError("Destination component missing from resort master")
    if not components["selection_status"].eq("unique_current_polygon").all():
        raise ValueError("A reviewed destination component lacks a unique Swiss municipality")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    x, y = transformer.transform(
        components["longitude"].to_numpy(), components["latitude"].to_numpy()
    )
    components = components.assign(component_x_2056=x, component_y_2056=y)

    ground = passenger[passenger["MoyenTransport_Code"].map(mode_is_ground)].copy()
    ground["stop_id"] = ground["Numero"].astype(str)
    ground["reference_departures"] = ground["stop_id"].map(
        lambda value: total_departures(value, departure_counts)
    )
    ground = ground[ground["reference_departures"].gt(0)].copy()
    rows = []
    for component in components.itertuples(index=False):
        candidates = ground[
            pd.to_numeric(ground["Commune_Numero"], errors="coerce").eq(
                int(component.point_municipality_bfs_id)
            )
        ].copy()
        method = "nearest_served_ground_stop_inside_component_current_municipality"
        if candidates.empty:
            candidates = ground.copy()
            method = "nearest_served_ground_stop_outside_component_municipality_fallback"
        candidates["component_distance_km"] = candidates.apply(
            lambda row: point_distance_km(
                component.component_x_2056,
                component.component_y_2056,
                row["E"],
                row["N"],
            ),
            axis=1,
        )
        candidates["numeric_stop_id"] = pd.to_numeric(
            candidates["stop_id"], errors="coerce"
        )
        chosen = candidates.sort_values(
            ["component_distance_km", "reference_departures", "numeric_stop_id"],
            ascending=[True, False, True],
            kind="stable",
        ).iloc[0]
        rows.append(
            {
                "node_role": "destination_component_arrival",
                "municipality_bfs_id": pd.NA,
                "boundary_bfs_id_2026": int(component.point_municipality_bfs_id),
                "boundary_bfs_bridge_status": "not_applicable",
                "municipality_name": "",
                "municipality_boundary_name_2026": component.point_municipality_name,
                "destination_unit_id": component.destination_unit_id,
                "destination_name": component.destination_name,
                "component_resort_id": component.component_resort_id,
                "component_resort_name": component.resort_name_canonical,
                "selected_stop_id": str(chosen["stop_id"]),
                "selected_stop_name": str(chosen["Nom"]),
                "selected_stop_mode_code": str(chosen["MoyenTransport_Code"]),
                "selected_stop_mode": str(chosen["MoyenTransport_Designation"]),
                "selected_stop_municipality_bfs_id": int(chosen["Commune_Numero"]),
                "selected_stop_municipality_name": str(chosen["Commune_Nom"]),
                "selected_stop_reference_departures": int(chosen["reference_departures"]),
                "selected_stop_distance_from_reference_point_km": float(
                    chosen["component_distance_km"]
                ),
                "selection_method": method,
                "selection_rule": settings["resort_arrival_rule"],
            }
        )
    return pd.DataFrame(rows)


def sample_row(
    pair: dict,
    direction: str,
    day_label: str,
    date: str,
    requested: int,
    origin: pd.Series,
    destination: pd.Series,
    journey: Journey | None,
    maximum_vehicle_legs: int,
    maximum_generalized_elapsed_minutes: int,
) -> dict:
    raw_elapsed_minutes = (
        (journey.arrival_seconds - requested) / 60 if journey is not None else np.nan
    )
    feasible = bool(
        journey is not None
        and 0 < journey.legs <= maximum_vehicle_legs
        and 0 <= raw_elapsed_minutes <= maximum_generalized_elapsed_minutes
    )
    if journey is None:
        exclusion_reason = "no_scheduled_itinerary_found"
    elif journey.legs == 0:
        exclusion_reason = "no_vehicle_leg_same_stop_or_walk_only"
    elif journey.legs > maximum_vehicle_legs:
        exclusion_reason = "vehicle_leg_limit_exceeded"
    elif raw_elapsed_minutes > maximum_generalized_elapsed_minutes:
        exclusion_reason = "elapsed_time_limit_exceeded_probable_overnight_wait"
    elif raw_elapsed_minutes < 0:
        exclusion_reason = "invalid_negative_elapsed_time"
    else:
        exclusion_reason = ""
    row = {
        **pair,
        "direction": direction,
        "reference_day_type": day_label,
        "reference_date": date,
        "requested_departure_time": format_gtfs_time(requested),
        "origin_stop_id": origin["selected_stop_id"],
        "origin_stop_name": origin["selected_stop_name"],
        "destination_stop_id": destination["selected_stop_id"],
        "destination_stop_name": destination["selected_stop_name"],
        "destination_component_resort_id": destination.get("component_resort_id", ""),
        "destination_component_resort_name": destination.get("component_resort_name", ""),
        "journey_feasible": feasible,
        "journey_exclusion_reason": exclusion_reason,
        "scheduled_first_boarding_time": "",
        "scheduled_arrival_time": "",
        "initial_wait_minutes": np.nan,
        "scheduled_journey_minutes": np.nan,
        "generalized_elapsed_minutes": np.nan,
        "vehicle_legs": pd.NA,
        "transfers": pd.NA,
        "transport_modes": "",
        "source_id": SOURCE_ID,
        "interpretation": INTERPRETATION,
        "causal_accessibility_feature_approved": False,
    }
    if feasible:
        row.update(
            {
                "scheduled_first_boarding_time": format_gtfs_time(
                    journey.first_departure_seconds
                ),
                "scheduled_arrival_time": format_gtfs_time(journey.arrival_seconds),
                "initial_wait_minutes": (
                    journey.first_departure_seconds - requested
                ) / 60,
                "scheduled_journey_minutes": (
                    journey.arrival_seconds - journey.first_departure_seconds
                ) / 60,
                "generalized_elapsed_minutes": (
                    journey.arrival_seconds - requested
                ) / 60,
                "vehicle_legs": int(journey.legs),
                "transfers": int(journey.transfers),
                "transport_modes": mode_mask_label(journey.mode_mask),
            }
        )
    return row


def better_sample(left: dict | None, right: dict) -> dict:
    if left is None:
        return right
    left_value = left["generalized_elapsed_minutes"]
    right_value = right["generalized_elapsed_minutes"]
    if pd.isna(left_value):
        return right
    if pd.isna(right_value):
        return left
    left_key = (left_value, left["vehicle_legs"], left["destination_stop_id"])
    right_key = (right_value, right["vehicle_legs"], right["destination_stop_id"])
    return right if right_key < left_key else left


def route_samples_for_day(
    archive_path: Path,
    reference: dict,
    trip_reference: dict,
    settings: dict,
    date: str,
    day_label: str,
    municipality_nodes: pd.DataFrame,
    destination_nodes: pd.DataFrame,
) -> tuple[list[dict], dict]:
    network = build_day_network(
        archive_path,
        reference,
        trip_reference,
        date,
        int(settings["default_transfer_seconds"]),
    )
    missing_nodes = sorted(
        (
            set(municipality_nodes["selected_stop_id"])
            | set(destination_nodes["selected_stop_id"])
        )
        - set(network.stop_index)
    )
    outbound_times = [parse_gtfs_time(value) for value in settings["outbound_sample_times"]]
    return_times = [parse_gtfs_time(value) for value in settings["return_sample_times"]]
    components_by_unit = {
        unit: group.copy()
        for unit, group in destination_nodes.groupby("destination_unit_id", sort=False)
    }
    samples: dict[tuple, dict] = {}
    connections = flatten_connections(network)
    connection_count = len(connections.departure)

    for destination_number, destination in enumerate(
        destination_nodes.itertuples(index=False), start=1
    ):
        print(
            f"{date} outbound profile {destination_number}/{len(destination_nodes)} "
            f"{destination.component_resort_id} -> {destination.selected_stop_name}",
            flush=True,
        )
        profile = (
            build_destination_profile(
                network,
                connections,
                str(destination.selected_stop_id),
                int(settings["maximum_vehicle_legs"]),
                min(outbound_times),
                max(outbound_times)
                + int(settings["maximum_generalized_elapsed_minutes"]) * 60,
            )
            if str(destination.selected_stop_id) in network.stop_index
            else None
        )
        destination_series = pd.Series(destination._asdict())
        for municipality in municipality_nodes.itertuples(index=False):
            municipality_series = pd.Series(municipality._asdict())
            pair = {
                "destination_unit_id": destination.destination_unit_id,
                "destination_name": destination.destination_name,
                "municipality_bfs_id": int(municipality.municipality_bfs_id),
                "boundary_bfs_id_2026": int(municipality.boundary_bfs_id_2026),
                "municipality_name": municipality.municipality_name,
            }
            for requested in outbound_times:
                journey = (
                    profile.query(str(municipality.selected_stop_id), requested)
                    if profile is not None
                    else None
                )
                row = sample_row(
                    pair,
                    "outbound_municipality_to_destination",
                    day_label,
                    date,
                    requested,
                    municipality_series,
                    destination_series,
                    journey,
                    int(settings["maximum_vehicle_legs"]),
                    int(settings["maximum_generalized_elapsed_minutes"]),
                )
                key = (
                    destination.destination_unit_id,
                    int(municipality.municipality_bfs_id),
                    "outbound_municipality_to_destination",
                    date,
                    requested,
                )
                samples[key] = better_sample(samples.get(key), row)
        del profile
        gc.collect()

    del connections
    gc.collect()

    for destination_number, destination in enumerate(
        destination_nodes.itertuples(index=False), start=1
    ):
        print(
            f"{date} return routes {destination_number}/{len(destination_nodes)} "
            f"{destination.component_resort_id} <- {destination.selected_stop_name}",
            flush=True,
        )
        destination_series = pd.Series(destination._asdict())
        for requested in return_times:
            routes = forward_raptor(
                network,
                str(destination.selected_stop_id),
                requested,
                int(settings["maximum_vehicle_legs"]),
            )
            for municipality in municipality_nodes.itertuples(index=False):
                municipality_series = pd.Series(municipality._asdict())
                pair = {
                    "destination_unit_id": destination.destination_unit_id,
                    "destination_name": destination.destination_name,
                    "municipality_bfs_id": int(municipality.municipality_bfs_id),
                    "boundary_bfs_id_2026": int(municipality.boundary_bfs_id_2026),
                    "municipality_name": municipality.municipality_name,
                }
                journey = routes.get(str(municipality.selected_stop_id))
                row = sample_row(
                    pair,
                    "return_destination_to_municipality",
                    day_label,
                    date,
                    requested,
                    destination_series,
                    municipality_series,
                    journey,
                    int(settings["maximum_vehicle_legs"]),
                    int(settings["maximum_generalized_elapsed_minutes"]),
                )
                # Preserve the ski component used as the origin of the return.
                row["destination_component_resort_id"] = destination.component_resort_id
                row["destination_component_resort_name"] = destination.component_resort_name
                key = (
                    destination.destination_unit_id,
                    int(municipality.municipality_bfs_id),
                    "return_destination_to_municipality",
                    date,
                    requested,
                )
                samples[key] = better_sample(samples.get(key), row)

    expected = len(components_by_unit) * len(municipality_nodes) * (
        len(outbound_times) + len(return_times)
    )
    if len(samples) != expected:
        raise ValueError(f"Unexpected daily sample grain: {len(samples)} != {expected}")
    summary = {
        **network.pattern_summary,
        "connections": int(connection_count),
        "destination_component_nodes": int(len(destination_nodes)),
        "destination_units": int(len(components_by_unit)),
        "municipality_origin_nodes": int(len(municipality_nodes)),
        "selected_nodes_absent_from_active_day_network": missing_nodes,
        "daily_route_samples": int(len(samples)),
    }
    return list(samples.values()), summary


def pipe_unique(values: pd.Series) -> str:
    return "|".join(sorted({str(value) for value in values.dropna() if str(value)}))


def aggregate_samples(
    samples: pd.DataFrame,
    municipality_nodes: pd.DataFrame,
    settings: dict,
) -> pd.DataFrame:
    rows = []
    group_columns = [
        "destination_unit_id",
        "destination_name",
        "municipality_bfs_id",
        "boundary_bfs_id_2026",
        "municipality_name",
    ]
    expected_outbound = len(settings["reference_dates"]) * len(
        settings["outbound_sample_times"]
    )
    expected_return = len(settings["reference_dates"]) * len(
        settings["return_sample_times"]
    )
    node_lookup = municipality_nodes.set_index("municipality_bfs_id")
    for keys, group in samples.groupby(group_columns, sort=False, dropna=False):
        row = dict(zip(group_columns, keys))
        origin = node_lookup.loc[int(row["municipality_bfs_id"])]
        row.update(
            {
                "municipality_main_stop_id": origin["selected_stop_id"],
                "municipality_main_stop_name": origin["selected_stop_name"],
                "municipality_main_stop_mode_code": origin["selected_stop_mode_code"],
                "municipality_main_stop_mode": origin["selected_stop_mode"],
                "municipality_main_stop_selection_method": origin["selection_method"],
                "municipality_main_stop_distance_from_representative_point_km": origin[
                    "selected_stop_distance_from_reference_point_km"
                ],
            }
        )
        for direction, prefix, expected in [
            ("outbound_municipality_to_destination", "outbound", expected_outbound),
            ("return_destination_to_municipality", "return", expected_return),
        ]:
            subset = group[group["direction"].eq(direction)]
            feasible = subset[subset["journey_feasible"]]
            row[f"{prefix}_scheduled_samples"] = int(len(subset))
            row[f"{prefix}_feasible_samples"] = int(len(feasible))
            row[f"{prefix}_sample_coverage_share"] = len(feasible) / expected
            for metric in [
                "initial_wait_minutes",
                "scheduled_journey_minutes",
                "generalized_elapsed_minutes",
            ]:
                row[f"{prefix}_mean_{metric}"] = (
                    float(feasible[metric].mean()) if len(feasible) else np.nan
                )
                row[f"{prefix}_maximum_{metric}"] = (
                    float(feasible[metric].max()) if len(feasible) else np.nan
                )
            row[f"{prefix}_maximum_transfers"] = (
                int(feasible["transfers"].max()) if len(feasible) else pd.NA
            )
            row[f"{prefix}_transport_modes"] = pipe_unique(
                feasible["transport_modes"]
            )
            row[f"{prefix}_destination_stop_ids"] = pipe_unique(
                feasible["destination_stop_id"]
                if prefix == "outbound"
                else feasible["origin_stop_id"]
            )
            row[f"{prefix}_destination_stop_names"] = pipe_unique(
                feasible["destination_stop_name"]
                if prefix == "outbound"
                else feasible["origin_stop_name"]
            )
            row[f"{prefix}_destination_component_resort_ids"] = pipe_unique(
                feasible["destination_component_resort_id"]
            )
        if (
            pd.notna(row["outbound_mean_generalized_elapsed_minutes"])
            and pd.notna(row["return_mean_generalized_elapsed_minutes"])
        ):
            row["mean_round_trip_generalized_minutes"] = (
                row["outbound_mean_generalized_elapsed_minutes"]
                + row["return_mean_generalized_elapsed_minutes"]
            )
        else:
            row["mean_round_trip_generalized_minutes"] = np.nan
        row.update(
            {
                "gtfs_feed_version": settings["feed_version"],
                "gtfs_feed_start_date": settings["feed_start_date"],
                "gtfs_feed_end_date": settings["feed_end_date"],
                "reference_dates": "|".join(settings["reference_dates"].values()),
                "outbound_sampling_window": "08:00-10:00_every_30_minutes_inclusive",
                "return_sampling_window": "15:00-18:00_every_30_minutes_inclusive",
                "municipality_origin_rule": settings["municipality_origin_rule"],
                "resort_arrival_rule": settings["resort_arrival_rule"],
                "historical_stability_status": settings["historical_stability_status"],
                "public_transport_journey_interpretation": INTERPRETATION,
                "public_transport_journey_feature_approved": False,
                "public_transport_journey_source_id": SOURCE_ID,
            }
        )
        rows.append(row)
    result = pd.DataFrame(rows)
    if len(result) != 2_046 or result.duplicated(
        ["destination_unit_id", "municipality_bfs_id"]
    ).any():
        raise ValueError("Journey context must preserve 11 x 186 destination-municipality rows")
    return result


def cache_fingerprint(
    gtfs_sha256: str,
    settings: dict,
    municipality_nodes: pd.DataFrame,
    destination_nodes: pd.DataFrame,
) -> str:
    digest = hashlib.sha256()
    digest.update(gtfs_sha256.encode("ascii"))
    digest.update(json.dumps(settings, sort_keys=True).encode("utf-8"))
    for implementation_path in [Path(__file__), Path(__file__).with_name("gtfs_static_router.py")]:
        digest.update(hashlib.sha256(implementation_path.read_bytes()).digest())
    for frame in [municipality_nodes, destination_nodes]:
        digest.update(frame.to_csv(index=False, lineterminator="\n").encode("utf-8"))
    return digest.hexdigest()


def load_day_cache(
    date: str, fingerprint: str, expected_rows: int
) -> tuple[list[dict], dict] | None:
    rows_path = CACHE_DIR / f"journey_samples_{date}.csv"
    metadata_path = CACHE_DIR / f"journey_samples_{date}.metadata.json"
    if not rows_path.exists() or not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if (
        metadata.get("fingerprint") != fingerprint
        or int(metadata.get("rows", -1)) != expected_rows
    ):
        return None
    rows = pd.read_csv(rows_path).to_dict("records")
    if len(rows) != expected_rows:
        return None
    print(f"{date} cached journey samples reused", flush=True)
    return rows, metadata["network_summary"]


def write_day_cache(
    date: str, fingerprint: str, rows: list[dict], network_summary: dict
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    rows_path = CACHE_DIR / f"journey_samples_{date}.csv"
    metadata_path = CACHE_DIR / f"journey_samples_{date}.metadata.json"
    pd.DataFrame(rows).to_csv(rows_path, index=False, lineterminator="\n")
    metadata_path.write_text(
        json.dumps(
            {
                "fingerprint": fingerprint,
                "rows": len(rows),
                "network_summary": network_summary,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    gtfs_metadata = exact_metadata(SOURCE_ID)
    archive_path = ROOT / gtfs_metadata["raw_file"]
    reference = load_feed_reference_tables(archive_path)
    settings = validate_settings(config, reference)
    dates = list(settings["reference_dates"].values())
    trip_reference = load_active_trip_info(archive_path, reference, dates)
    departure_counts, feed_counts = count_active_departures(
        archive_path, trip_reference
    )

    passenger, _, bav_summary = load_stops(checked_source(config))
    distance = pd.read_csv(DISTANCE_PATH)
    units = pd.read_csv(UNIT_PATH)
    resorts = pd.read_csv(RESORT_PATH)
    point_municipalities = pd.read_csv(POINT_MUNICIPALITY_PATH)
    municipality_nodes = select_municipality_nodes(
        passenger, distance, departure_counts, settings
    )
    destination_nodes = select_destination_nodes(
        passenger,
        units,
        distance,
        resorts,
        point_municipalities,
        departure_counts,
        settings,
    )
    nodes = pd.concat([municipality_nodes, destination_nodes], ignore_index=True)
    nodes.to_csv(NODE_OUTPUT, index=False, lineterminator="\n")

    sample_rows = []
    network_summaries = []
    fingerprint = cache_fingerprint(
        gtfs_metadata["sha256"], settings, municipality_nodes, destination_nodes
    )
    expected_daily_rows = int(distance["destination_unit_id"].nunique()) * len(
        municipality_nodes
    ) * (
        len(settings["outbound_sample_times"])
        + len(settings["return_sample_times"])
    )
    for day_label, date in settings["reference_dates"].items():
        cached = load_day_cache(date, fingerprint, expected_daily_rows)
        if cached is None:
            rows, summary = route_samples_for_day(
                archive_path,
                reference,
                trip_reference,
                settings,
                date,
                day_label,
                municipality_nodes,
                destination_nodes,
            )
            write_day_cache(date, fingerprint, rows, summary)
        else:
            rows, summary = cached
        sample_rows.extend(rows)
        network_summaries.append(summary)
        gc.collect()
    samples = pd.DataFrame(sample_rows).sort_values(
        [
            "destination_unit_id",
            "municipality_bfs_id",
            "direction",
            "reference_date",
            "requested_departure_time",
        ],
        kind="stable",
    )
    expected_samples = 2_046 * (
        len(settings["reference_dates"])
        * (
            len(settings["outbound_sample_times"])
            + len(settings["return_sample_times"])
        )
    )
    if len(samples) != expected_samples:
        raise ValueError(f"Unexpected final sample count: {len(samples)} != {expected_samples}")
    samples.to_csv(SAMPLE_OUTPUT, index=False, lineterminator="\n")
    summary_context = aggregate_samples(samples, municipality_nodes, settings)
    summary_context.to_csv(SUMMARY_OUTPUT, index=False, lineterminator="\n")

    complete = summary_context[
        summary_context["outbound_sample_coverage_share"].eq(1)
        & summary_context["return_sample_coverage_share"].eq(1)
    ]
    node_method_counts = {
        str(key): int(value)
        for key, value in municipality_nodes["selection_method"].value_counts().items()
    }
    destination_method_counts = {
        str(key): int(value)
        for key, value in destination_nodes["selection_method"].value_counts().items()
    }
    metrics = {
        "analysis_version": config["analysis_version"],
        "source_id": SOURCE_ID,
        "gtfs_sha256": gtfs_metadata["sha256"],
        "gtfs_size_bytes": int(gtfs_metadata["size_bytes"]),
        "feed_version": settings["feed_version"],
        "feed_start_date": settings["feed_start_date"],
        "feed_end_date": settings["feed_end_date"],
        "reference_dates": settings["reference_dates"],
        **feed_counts,
        "network_summaries": network_summaries,
        "official_bav_passenger_stops_available_for_node_selection": int(
            bav_summary["passenger_stops"]
        ),
        "municipality_origin_nodes": int(len(municipality_nodes)),
        "municipality_origin_selection_methods": node_method_counts,
        "destination_units": int(distance["destination_unit_id"].nunique()),
        "destination_component_nodes": int(len(destination_nodes)),
        "destination_node_selection_methods": destination_method_counts,
        "destination_component_node_names": sorted(
            destination_nodes["selected_stop_name"].unique().tolist()
        ),
        "destination_municipality_pairs": int(len(summary_context)),
        "journey_samples": int(len(samples)),
        "feasible_journey_samples": int(samples["journey_feasible"].sum()),
        "pairs_complete_all_samples": int(len(complete)),
        "median_pair_outbound_mean_generalized_minutes": float(
            summary_context["outbound_mean_generalized_elapsed_minutes"].median()
        ),
        "median_pair_return_mean_generalized_minutes": float(
            summary_context["return_mean_generalized_elapsed_minutes"].median()
        ),
        "median_pair_round_trip_generalized_minutes": float(
            summary_context["mean_round_trip_generalized_minutes"].median()
        ),
        "historical_stability_status": settings["historical_stability_status"],
        "approved_causal_accessibility_features": 0,
        "interpretation": INTERPRETATION,
    }
    METRICS_OUTPUT.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# Scheduled public-transport journey context

## Definition

This qualified context uses the checksum-verified official Swiss GTFS Static feed version **{settings['feed_version']}**, valid from **{settings['feed_start_date']}** through **{settings['feed_end_date']}**. The reference dates are Wednesday **{settings['reference_dates']['winter_weekday']}** and Saturday **{settings['reference_dates']['winter_saturday']}**, both inside the winter timetable. Outbound requests are sampled every 30 minutes from 08:00 through 10:00; return requests are sampled every 30 minutes from 15:00 through 18:00. The fastest scheduled itinerary at or after each requested time is retained. `generalized_elapsed_minutes` includes initial waiting; `scheduled_journey_minutes` starts at the first vehicle boarding.

The origin for each of the **{len(municipality_nodes)}** hotel municipalities is the train stop inside its current municipality with the highest combined reference-day departure count. If no served train stop exists, the most frequently served terrestrial stop is used. The arrival node for each reviewed destination component is the nearest served bus/train stop inside the component point's current municipality. Cableways, chairlifts and funiculars are excluded from node selection. Multi-component destinations use the fastest component for each sampled request.

## Coverage

- reviewed destination units: **{metrics['destination_units']}**
- component arrival nodes: **{metrics['destination_component_nodes']}**
- destination × municipality pairs: **{metrics['destination_municipality_pairs']:,}**
- scheduled samples: **{metrics['journey_samples']:,}**
- feasible samples: **{metrics['feasible_journey_samples']:,}**
- pairs complete on every outbound and return sample: **{metrics['pairs_complete_all_samples']:,} / {metrics['destination_municipality_pairs']:,}**
- median pair mean outbound generalized time: **{metrics['median_pair_outbound_mean_generalized_minutes']:.1f} minutes**
- median pair mean return generalized time: **{metrics['median_pair_return_mean_generalized_minutes']:.1f} minutes**
- median pair mean round-trip generalized time: **{metrics['median_pair_round_trip_generalized_minutes']:.1f} minutes**

Municipality-node methods: `{json.dumps(node_method_counts, ensure_ascii=False)}`. Destination-node methods: `{json.dumps(destination_method_counts, ensure_ascii=False)}`.

## Limits

GTFS Static represents the published schedule, not delays, cancellations, crowding, fares, snow-road disruptions or guaranteed connections. Platform identifiers are collapsed to their Swiss base stop; generic published transfers are modelled, while route/trip-specific transfer rules are reported but not separately modelled. Walking is limited to transfers present in the feed. The destination nodes are reproducible algorithmic proxies for village/valley access and still require manual face validation.

Most importantly, this is a winter-2026 reference measure. The selected Magic Pass entry seasons range across earlier years, and the historical line-stability comparison has status **`{settings['historical_stability_status']}`**. It is therefore a useful descriptive transport-access variable but not yet an approved pre-treatment or causal covariate. The generic `accessibility_score` and all causal effect fields remain untouched.

## Outputs

- `reports/public_transport_journey_nodes.csv`
- `data_processed/treatment_municipality_public_transport_journey_samples.csv`
- `data_processed/treatment_municipality_public_transport_journey_context.csv`
- `reports/public_transport_journey_context_summary.json`
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
