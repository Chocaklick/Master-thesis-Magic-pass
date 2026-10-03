"""Test a documented proximity-transfer sensitivity on the 2018 GTFS.

The strict 2018 feed exposes far fewer cross-stop transfers than the 2026
feed. This script preserves that strict result and separately adds inferred
bidirectional walking links between active GTFS stops no more than 250 metres
apart. The sensitivity is descriptive and never treated as a published GTFS
transfer or a causal feature.
"""

from __future__ import annotations

import gc
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "data_processing"))

from build_accessibility_historical_gtfs_2018_routes import (  # noqa: E402
    ACCESS_NODES_PATH,
    CONFIG_PATH,
    FIRST_EXPOSURE_PATH,
    WORKLIST_PATH,
    aggregate_context,
    as_bool,
    load_network_cache,
    load_stop_lookup,
    municipality_validation,
    network_cache_fingerprint,
    prepare_nodes,
    route_group_day,
    sha256,
    validate_archive,
)
from gtfs_static_router import (  # noqa: E402
    flatten_connections,
    load_active_trip_info,
    load_feed_reference_tables,
)


SAMPLE_OUTPUT = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_proximity_journey_samples.csv"
CONTEXT_OUTPUT = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_proximity_journey_context.csv"
MUNICIPALITY_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_proximity_municipality_validation.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_proximity_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "62_SENSIBILITE_TRANSFERTS_PROXIMITE_GTFS_2018_FR.md"
STRICT_CONTEXT_PATH = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_journey_context.csv"
CACHE_DIR = ROOT / "data_interim" / "accessibility_historical_gtfs_2018_proximity_routes"


def haversine_metres(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_008.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = phi2 - phi1
    dlambda = math.radians(lon2 - lon1)
    value = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * radius * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def add_proximity_transfers(network, stop_lookup: dict[str, dict], settings: dict) -> dict:
    maximum = float(settings["maximum_walk_distance_metres"])
    speed = float(settings["walking_speed_metres_per_second"])
    minimum = int(settings["minimum_interchange_seconds"])
    rounding = int(settings["duration_rounding_seconds"])
    lat_cell = maximum / 111_000
    lon_cell = maximum / 74_000
    active = []
    for stop_id, index in network.stop_index.items():
        coordinates = stop_lookup.get(stop_id)
        if not coordinates or not network.stop_patterns[index]:
            continue
        latitude = coordinates["historical_stop_latitude"]
        longitude = coordinates["historical_stop_longitude"]
        if pd.isna(latitude) or pd.isna(longitude):
            continue
        active.append((stop_id, index, float(latitude), float(longitude)))

    grid: dict[tuple[int, int], list[tuple[str, int, float, float]]] = defaultdict(list)
    for item in active:
        grid[(math.floor(item[2] / lat_cell), math.floor(item[3] / lon_cell))].append(item)

    existing = {
        (from_index, to_index)
        for from_index, links in enumerate(network.cross_transfers)
        for to_index, _ in links
    }
    inferred = 0
    examined_pairs = 0
    for stop_id, index, latitude, longitude in active:
        cell = (math.floor(latitude / lat_cell), math.floor(longitude / lon_cell))
        for delta_lat in [-1, 0, 1]:
            for delta_lon in [-1, 0, 1]:
                for other_id, other_index, other_lat, other_lon in grid.get(
                    (cell[0] + delta_lat, cell[1] + delta_lon), []
                ):
                    if other_index <= index:
                        continue
                    examined_pairs += 1
                    distance = haversine_metres(
                        latitude, longitude, other_lat, other_lon
                    )
                    if distance > maximum:
                        continue
                    walk = math.ceil((distance / speed) / rounding) * rounding
                    duration = minimum + int(walk)
                    if (index, other_index) not in existing:
                        network.cross_transfers[index].append((other_index, duration))
                        existing.add((index, other_index))
                        inferred += 1
                    if (other_index, index) not in existing:
                        network.cross_transfers[other_index].append((index, duration))
                        existing.add((other_index, index))
                        inferred += 1
    for links in network.cross_transfers:
        links.sort(key=lambda value: (value[0], value[1]))
    return {
        "active_stops_with_coordinates": len(active),
        "candidate_pairs_examined": examined_pairs,
        "inferred_directed_proximity_transfer_links": inferred,
        "maximum_walk_distance_metres": maximum,
        "walking_speed_metres_per_second": speed,
        "minimum_interchange_seconds": minimum,
        "duration_rounding_seconds": rounding,
    }


def cache_paths(date: str, group_id: str) -> tuple[Path, Path]:
    safe = hashlib.sha1(group_id.encode("utf-8")).hexdigest()[:16]
    base = CACHE_DIR / date / safe
    return base.with_suffix(".csv"), base.with_suffix(".metadata.json")


def route_fingerprint(
    config: dict, archive_sha: str, date: str, group_pairs: pd.DataFrame,
    group_nodes: pd.DataFrame, origin_nodes: pd.DataFrame,
) -> str:
    digest = hashlib.sha256()
    digest.update(archive_sha.encode("ascii"))
    digest.update(date.encode("ascii"))
    digest.update(json.dumps(config, sort_keys=True).encode("utf-8"))
    for frame in [group_pairs, group_nodes, origin_nodes]:
        digest.update(frame.to_csv(index=False, lineterminator="\n").encode("utf-8"))
    for path in [Path(__file__), ROOT / "src/data_processing/gtfs_static_router.py",
                 ROOT / "src/data_processing/build_accessibility_historical_gtfs_2018_routes.py"]:
        digest.update(sha256(path).encode("ascii"))
    return digest.hexdigest()


def load_cache(date: str, group_id: str, digest: str, expected: int):
    data_path, metadata_path = cache_paths(date, group_id)
    if not data_path.exists() or not metadata_path.exists():
        return None
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("fingerprint") != digest or metadata.get("rows") != expected:
        return None
    frame = pd.read_csv(
        data_path, dtype={"origin_stop_id": str, "destination_stop_id": str}
    )
    return frame.to_dict("records") if len(frame) == expected else None


def write_cache(date: str, group_id: str, digest: str, rows: list[dict]) -> None:
    data_path, metadata_path = cache_paths(date, group_id)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(data_path, index=False, lineterminator="\n")
    metadata_path.write_text(json.dumps({
        "reference_date": date,
        "station_group_id": group_id,
        "fingerprint": digest,
        "rows": len(rows),
    }, indent=2) + "\n", encoding="utf-8")


def add_worklist_sensitivity(worklist: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "station_group_id", "municipality_bfs_id",
        "historical_routing_pair_complete", "historical_mean_one_way_generalized_minutes",
        "historical_within_120_minutes", "historical_access_plausibility_status",
        "historical_access_validated", "signed_2018_to_2026_time_change_minutes",
        "absolute_2018_to_2026_time_change_minutes",
    ]
    sensitivity = context[fields].rename(columns={
        column: f"proximity_250m_{column}" for column in fields
        if column not in {"station_group_id", "municipality_bfs_id"}
    })
    old = [column for column in sensitivity if column.startswith("proximity_250m_")]
    result = worklist.drop(columns=[column for column in old if column in worklist], errors="ignore")
    result = result.merge(
        sensitivity, on=["station_group_id", "municipality_bfs_id"],
        how="left", validate="one_to_one",
    )
    result["proximity_250m_transfer_assumption"] = (
        "inferred_bidirectional_walk_between_active_2018_gtfs_stops_at_most_250m"
    )
    result["proximity_250m_causal_accessibility_feature_approved"] = False
    return result


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    settings = config["proximity_transfer_sensitivity"]
    archive_path, archive_metadata = validate_archive(config)
    worklist = pd.read_csv(WORKLIST_PATH, dtype={"municipality_main_stop_id": str})
    access_nodes = pd.read_csv(ACCESS_NODES_PATH, dtype={"selected_stop_id": str})
    first = pd.read_csv(FIRST_EXPOSURE_PATH)
    strict = pd.read_csv(STRICT_CONTEXT_PATH)
    _, stop_lookup = load_stop_lookup(archive_path)
    origin_nodes, destination_nodes, _ = prepare_nodes(
        worklist, access_nodes, stop_lookup, config
    )
    reference = load_feed_reference_tables(archive_path)
    dates = list(config["reference_dates"].values())
    trip_reference = load_active_trip_info(archive_path, reference, dates)
    group_ids = sorted(worklist.station_group_id.unique())

    all_rows = []
    transfer_summaries = []
    for day_label, date in config["reference_dates"].items():
        network_digest = network_cache_fingerprint(config, archive_metadata["sha256"], date)
        network = load_network_cache(date, network_digest)
        if network is None:
            raise FileNotFoundError(
                f"Strict day-network cache missing for {date}; run the strict historical builder first"
            )
        transfer_summary = add_proximity_transfers(network, stop_lookup, settings)
        transfer_summary["service_date"] = date
        transfer_summaries.append(transfer_summary)
        connections = flatten_connections(network)
        for number, group_id in enumerate(group_ids, start=1):
            pairs = worklist[worklist.station_group_id.eq(group_id)].copy()
            nodes = destination_nodes[destination_nodes.station_group_id.eq(group_id)].copy()
            origins = origin_nodes[
                origin_nodes.municipality_bfs_id.isin(pairs.municipality_bfs_id)
            ].copy()
            digest = route_fingerprint(
                config, archive_metadata["sha256"], date, pairs, nodes, origins
            )
            expected = len(pairs) * (
                len(config["outbound_sample_times"]) + len(config["return_sample_times"])
            )
            rows = load_cache(date, group_id, digest, expected)
            if rows is None:
                name = pairs.station_group_name.iloc[0]
                print(f"{date} {number}/{len(group_ids)} proximity route {name}", flush=True)
                rows = route_group_day(
                    network, connections, pairs, nodes, origins, config, day_label, date
                )
                for row in rows:
                    row["routing_transfer_variant"] = "inferred_proximity_transfers_250m"
                    row["interpretation"] = settings["interpretation"]
                write_cache(date, group_id, digest, rows)
            else:
                print(f"{date} {number}/{len(group_ids)} proximity cache", flush=True)
            all_rows.extend(rows)
        del connections, network
        gc.collect()

    samples = pd.DataFrame(all_rows).sort_values([
        "station_group_id", "municipality_bfs_id", "direction",
        "reference_date", "requested_departure_time",
    ], kind="stable")
    if len(samples) != 936:
        raise ValueError(f"Unexpected proximity-sensitivity sample count: {len(samples)}")
    samples.to_csv(SAMPLE_OUTPUT, index=False, lineterminator="\n")
    context = aggregate_context(samples, worklist, origin_nodes, destination_nodes, config)
    context["routing_transfer_variant"] = "inferred_proximity_transfers_250m"
    context["interpretation"] = settings["interpretation"]
    context["causal_accessibility_feature_approved"] = False
    context.to_csv(CONTEXT_OUTPUT, index=False, lineterminator="\n")
    municipality = municipality_validation(context, first)
    municipality["routing_transfer_variant"] = "inferred_proximity_transfers_250m"
    municipality.to_csv(MUNICIPALITY_OUTPUT, index=False, lineterminator="\n")
    add_worklist_sensitivity(worklist, context).to_csv(
        WORKLIST_PATH, index=False, lineterminator="\n"
    )

    strict_complete = int(as_bool(strict.historical_routing_pair_complete).sum())
    strict_within = int(as_bool(strict.historical_within_120_minutes).sum())
    proximity_complete = int(as_bool(context.historical_routing_pair_complete).sum())
    proximity_within = int(as_bool(context.historical_within_120_minutes).sum())
    municipalities_retained = int(as_bool(
        municipality.historical_first_exposure_retained
    ).sum())
    all_groups_retained = int(as_bool(
        municipality.all_current_founding_groups_historically_within_120_minutes
    ).sum())
    summary = {
        "analysis_date": "2026-10-03",
        "source_id": config["source_id"],
        "gtfs_sha256": archive_metadata["sha256"],
        "routing_variant": "inferred_proximity_transfers_250m",
        "assumption": settings,
        "strict_published_transfer_cross_stop_links_per_day": 184,
        "winter_2026_published_transfer_cross_stop_links_per_day": 7369,
        "transfer_summaries": transfer_summaries,
        "journey_samples": len(samples),
        "feasible_journey_samples": int(as_bool(samples.journey_feasible).sum()),
        "strict_complete_routes": strict_complete,
        "proximity_complete_routes": proximity_complete,
        "strict_routes_within_120_minutes": strict_within,
        "proximity_routes_within_120_minutes": proximity_within,
        "municipalities_retaining_at_least_one_founding_group_within_120_minutes": municipalities_retained,
        "municipalities_retaining_all_current_founding_groups_within_120_minutes": all_groups_retained,
        "median_signed_2018_to_2026_time_change_minutes": float(
            context.signed_2018_to_2026_time_change_minutes.median()
        ),
        "median_absolute_2018_to_2026_time_change_minutes": float(
            context.absolute_2018_to_2026_time_change_minutes.median()
        ),
        "causal_accessibility_features_approved": 0,
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
            for path in [CONFIG_PATH, STRICT_CONTEXT_PATH, ACCESS_NODES_PATH, FIRST_EXPOSURE_PATH]
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Sensibilité des transferts de proximité dans le GTFS 2018 — étape 15

## Pourquoi une sensibilité est nécessaire

Le flux 2018 ne publie que **184 transferts entre identifiants d'arrêts normalisés**, contre **7 369** dans le flux 2026. Le scénario strict reste conservé, mais il ne permet que {strict_complete} / 39 couples complets et {strict_within} / 39 couples à 120 minutes ou moins. Plusieurs gares bus–train proches ne sont donc pas reliées dans l'ancien schéma.

La sensibilité ajoute uniquement des liens de marche bidirectionnels entre arrêts GTFS 2018 actifs situés à **250 m ou moins**. Le temps vaut 120 secondes d'interchange plus la marche à 1,2 m/s, arrondie aux 30 secondes supérieures. Les transferts publiés sont conservés et jamais remplacés.

| Résultat | Strict publié | Sensibilité 250 m |
|---|---:|---:|
| Couples complets sur 24 horaires | {strict_complete} / 39 | {proximity_complete} / 39 |
| Couples complets à 120 minutes ou moins | {strict_within} / 39 | {proximity_within} / 39 |
| Communes gardant au moins un groupe fondateur à 120 minutes ou moins | 2 / 19 | {municipalities_retained} / 19 |
| Communes gardant tous leurs groupes fondateurs actuels | 2 / 19 | {all_groups_retained} / 19 |

La variante 250 m est une **sensibilité modélisée**, pas une propriété publiée par le GTFS 2018. Elle sert à mesurer l'effet du changement de codage des correspondances. Le scénario strict et la variante doivent être rapportés ensemble; aucun des deux n'autorise à lui seul une interprétation causale.

## Fichiers

- `data_processed/accessibility_historical_gtfs_2018_proximity_journey_context.csv` : 39 couples;
- `data_processed/accessibility_historical_gtfs_2018_proximity_journey_samples.csv` : 936 horaires;
- `reports/accessibility_historical_gtfs_2018_proximity_municipality_validation.csv` : 19 communes;
- `reports/accessibility_historical_gtfs_2018_proximity_summary.json` : paramètres, liens inférés et comptes.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
