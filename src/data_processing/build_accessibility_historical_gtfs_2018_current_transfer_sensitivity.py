"""Project the official 2026 transfer topology onto active 2018 stop IDs.

This is a conservative bridge for the large schema gap between 184 published
cross-stop transfers in the 2018 feed and 7,369 in the 2026 feed. It adds only
official 2026 links whose two normalized stop IDs are already active in 2018;
it does not infer links by distance and remains a non-historical sensitivity.
"""

from __future__ import annotations

import gc
import hashlib
import json
import sys
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
from build_public_transport_journey_context import exact_metadata  # noqa: E402
from gtfs_static_router import (  # noqa: E402
    build_transfer_rules,
    flatten_connections,
    load_feed_reference_tables,
)


SAMPLE_OUTPUT = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_current_transfer_journey_samples.csv"
CONTEXT_OUTPUT = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_current_transfer_journey_context.csv"
MUNICIPALITY_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_current_transfer_municipality_validation.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_current_transfer_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "63_SENSIBILITE_TOPOLOGIE_TRANSFERTS_ACTUELS_GTFS_2018_FR.md"
STRICT_CONTEXT_PATH = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_journey_context.csv"
PROXIMITY_CONTEXT_PATH = ROOT / "data_processed" / "accessibility_historical_gtfs_2018_proximity_journey_context.csv"
CACHE_DIR = ROOT / "data_interim" / "accessibility_historical_gtfs_2018_current_transfer_routes"


def add_current_transfer_topology(network, current_cross: dict[str, list[tuple[str, int]]]) -> dict:
    active = {
        stop_id for stop_id, index in network.stop_index.items()
        if network.stop_patterns[index]
    }
    existing = {
        (from_index, to_index)
        for from_index, links in enumerate(network.cross_transfers)
        for to_index, _ in links
    }
    eligible = 0
    added = 0
    for from_stop, links in current_cross.items():
        if from_stop not in active:
            continue
        from_index = network.stop_index[from_stop]
        for to_stop, duration in links:
            if to_stop not in active:
                continue
            eligible += 1
            to_index = network.stop_index[to_stop]
            if (from_index, to_index) in existing:
                continue
            network.cross_transfers[from_index].append((to_index, int(duration)))
            existing.add((from_index, to_index))
            added += 1
    for links in network.cross_transfers:
        links.sort(key=lambda value: (value[0], value[1]))
    return {
        "active_2018_stops": len(active),
        "eligible_2026_published_cross_stop_links": eligible,
        "new_projected_cross_stop_links_added": added,
    }


def cache_paths(date: str, group_id: str) -> tuple[Path, Path]:
    safe = hashlib.sha1(group_id.encode("utf-8")).hexdigest()[:16]
    base = CACHE_DIR / date / safe
    return base.with_suffix(".csv"), base.with_suffix(".metadata.json")


def route_fingerprint(
    config: dict, archive_sha: str, current_sha: str, date: str,
    group_pairs: pd.DataFrame, group_nodes: pd.DataFrame, origin_nodes: pd.DataFrame,
) -> str:
    digest = hashlib.sha256()
    digest.update(archive_sha.encode("ascii"))
    digest.update(current_sha.encode("ascii"))
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


def update_worklist(worklist: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "station_group_id", "municipality_bfs_id",
        "historical_routing_pair_complete", "historical_mean_one_way_generalized_minutes",
        "historical_within_120_minutes", "historical_access_plausibility_status",
        "historical_access_validated", "signed_2018_to_2026_time_change_minutes",
        "absolute_2018_to_2026_time_change_minutes",
    ]
    sensitivity = context[fields].rename(columns={
        column: f"current_transfer_topology_{column}" for column in fields
        if column not in {"station_group_id", "municipality_bfs_id"}
    })
    generated = [
        column for column in sensitivity if column.startswith("current_transfer_topology_")
    ]
    result = worklist.drop(
        columns=[column for column in generated if column in worklist], errors="ignore"
    ).merge(
        sensitivity, on=["station_group_id", "municipality_bfs_id"],
        how="left", validate="one_to_one",
    )
    result["current_transfer_topology_assumption"] = (
        "official_2026_cross_stop_links_projected_only_when_both_stop_ids_are_active_in_2018"
    )
    result["current_transfer_topology_causal_accessibility_feature_approved"] = False
    return result


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    settings = config["current_transfer_topology_sensitivity"]
    archive_path, archive_metadata = validate_archive(config)
    current_path = ROOT / settings["source_local_path"]
    current_metadata = exact_metadata(settings["source_id"])
    if current_path != ROOT / current_metadata["raw_file"]:
        raise ValueError("Configured current GTFS path differs from registered source metadata")
    current_sha = sha256(current_path)
    if current_sha.lower() != str(current_metadata["sha256"]).lower():
        raise ValueError("Current GTFS SHA-256 differs from registered source metadata")

    worklist = pd.read_csv(WORKLIST_PATH, dtype={"municipality_main_stop_id": str})
    access_nodes = pd.read_csv(ACCESS_NODES_PATH, dtype={"selected_stop_id": str})
    first = pd.read_csv(FIRST_EXPOSURE_PATH)
    strict = pd.read_csv(STRICT_CONTEXT_PATH)
    proximity = pd.read_csv(PROXIMITY_CONTEXT_PATH)
    _, historical_stop_lookup = load_stop_lookup(archive_path)
    origin_nodes, destination_nodes, _ = prepare_nodes(
        worklist, access_nodes, historical_stop_lookup, config
    )
    current_reference = load_feed_reference_tables(current_path)
    _, current_cross, current_transfer_summary = build_transfer_rules(
        current_reference["transfers"], int(config["default_transfer_seconds"])
    )
    if current_transfer_summary["normalized_cross_stop_transfer_links"] != 7369:
        raise ValueError("Current GTFS transfer topology changed")

    all_rows = []
    topology_summaries = []
    group_ids = sorted(worklist.station_group_id.unique())
    for day_label, date in config["reference_dates"].items():
        network_digest = network_cache_fingerprint(config, archive_metadata["sha256"], date)
        network = load_network_cache(date, network_digest)
        if network is None:
            raise FileNotFoundError(
                f"Strict day-network cache missing for {date}; run the strict historical builder first"
            )
        topology = add_current_transfer_topology(network, current_cross)
        topology["service_date"] = date
        topology_summaries.append(topology)
        connections = flatten_connections(network)
        for number, group_id in enumerate(group_ids, start=1):
            pairs = worklist[worklist.station_group_id.eq(group_id)].copy()
            nodes = destination_nodes[destination_nodes.station_group_id.eq(group_id)].copy()
            origins = origin_nodes[
                origin_nodes.municipality_bfs_id.isin(pairs.municipality_bfs_id)
            ].copy()
            digest = route_fingerprint(
                config, archive_metadata["sha256"], current_sha, date,
                pairs, nodes, origins,
            )
            expected = len(pairs) * (
                len(config["outbound_sample_times"]) + len(config["return_sample_times"])
            )
            rows = load_cache(date, group_id, digest, expected)
            if rows is None:
                name = pairs.station_group_name.iloc[0]
                print(f"{date} {number}/{len(group_ids)} current-topology route {name}", flush=True)
                rows = route_group_day(
                    network, connections, pairs, nodes, origins, config, day_label, date
                )
                for row in rows:
                    row["routing_transfer_variant"] = "current_2026_transfer_topology_on_2018_ids"
                    row["interpretation"] = settings["interpretation"]
                write_cache(date, group_id, digest, rows)
            else:
                print(f"{date} {number}/{len(group_ids)} current-topology cache", flush=True)
            all_rows.extend(rows)
        del connections, network
        gc.collect()

    samples = pd.DataFrame(all_rows).sort_values([
        "station_group_id", "municipality_bfs_id", "direction",
        "reference_date", "requested_departure_time",
    ], kind="stable")
    if len(samples) != 936:
        raise ValueError(f"Unexpected current-topology sample count: {len(samples)}")
    samples.to_csv(SAMPLE_OUTPUT, index=False, lineterminator="\n")
    context = aggregate_context(samples, worklist, origin_nodes, destination_nodes, config)
    context["routing_transfer_variant"] = "current_2026_transfer_topology_on_2018_ids"
    context["interpretation"] = settings["interpretation"]
    context["causal_accessibility_feature_approved"] = False
    context.to_csv(CONTEXT_OUTPUT, index=False, lineterminator="\n")
    municipality = municipality_validation(context, first)
    municipality["routing_transfer_variant"] = "current_2026_transfer_topology_on_2018_ids"
    municipality.to_csv(MUNICIPALITY_OUTPUT, index=False, lineterminator="\n")
    update_worklist(worklist, context).to_csv(
        WORKLIST_PATH, index=False, lineterminator="\n"
    )

    counts = {
        "strict_complete_routes": int(as_bool(strict.historical_routing_pair_complete).sum()),
        "strict_routes_within_120_minutes": int(as_bool(strict.historical_within_120_minutes).sum()),
        "proximity_250m_complete_routes": int(as_bool(proximity.historical_routing_pair_complete).sum()),
        "proximity_250m_routes_within_120_minutes": int(as_bool(proximity.historical_within_120_minutes).sum()),
        "current_topology_complete_routes": int(as_bool(context.historical_routing_pair_complete).sum()),
        "current_topology_routes_within_120_minutes": int(as_bool(context.historical_within_120_minutes).sum()),
    }
    municipalities_retained = int(as_bool(
        municipality.historical_first_exposure_retained
    ).sum())
    all_groups_retained = int(as_bool(
        municipality.all_current_founding_groups_historically_within_120_minutes
    ).sum())
    summary = {
        "analysis_date": "2026-10-03",
        "historical_source_id": config["source_id"],
        "current_transfer_source_id": settings["source_id"],
        "historical_gtfs_sha256": archive_metadata["sha256"],
        "current_gtfs_sha256": current_sha,
        "routing_variant": "current_2026_transfer_topology_on_2018_ids",
        "assumption": settings,
        "current_transfer_source_summary": current_transfer_summary,
        "topology_projection_summaries": topology_summaries,
        "journey_samples": len(samples),
        "feasible_journey_samples": int(as_bool(samples.journey_feasible).sum()),
        **counts,
        "municipalities_retaining_at_least_one_founding_group_within_120_minutes": municipalities_retained,
        "municipalities_retaining_all_current_founding_groups_within_120_minutes": all_groups_retained,
        "median_signed_2018_to_2026_time_change_minutes": float(
            context.signed_2018_to_2026_time_change_minutes.median()
        ),
        "median_absolute_2018_to_2026_time_change_minutes": float(
            context.absolute_2018_to_2026_time_change_minutes.median()
        ),
        "causal_accessibility_features_approved": 0,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Sensibilité : topologie actuelle des transferts sur le GTFS 2018 — étape 16

## Principe

Cette variante ajoute au réseau 2018 uniquement les transferts entre arrêts publiés dans le GTFS officiel 2026 lorsque **les deux identifiants normalisés sont déjà actifs en 2018**. Elle ne crée aucun lien par simple distance et conserve tous les transferts 2018. Elle teste donc l'effet d'un changement de codage de la topologie des correspondances, mais ne prouve pas que chaque lien existait en 2018.

| Variante | Couples complets | Couples à 120 min ou moins |
|---|---:|---:|
| Transferts strictement publiés en 2018 | {counts['strict_complete_routes']} / 39 | {counts['strict_routes_within_120_minutes']} / 39 |
| Marche inférée à 250 m | {counts['proximity_250m_complete_routes']} / 39 | {counts['proximity_250m_routes_within_120_minutes']} / 39 |
| Topologie officielle 2026 projetée sur les arrêts 2018 | {counts['current_topology_complete_routes']} / 39 | {counts['current_topology_routes_within_120_minutes']} / 39 |

Avec la topologie actuelle projetée, **{municipalities_retained} / 19 communes** gardent au moins un groupe fondateur à 120 minutes ou moins et **{all_groups_retained} / 19** gardent tous les groupes actuellement attribués. La différence médiane signée, calculée comme temps 2026 moins temps 2018, vaut {summary['median_signed_2018_to_2026_time_change_minutes']:.1f} minutes.

## Décision méthodologique

Le scénario strict est une borne basse sous-connectée; la marche à 250 m est une borne plus permissive; la projection de la topologie officielle actuelle est la sensibilité structurelle la plus directement documentée. Les trois doivent rester visibles. Aucun drapeau causal n'est activé tant que le choix du scénario principal et les autres hypothèses d'identification ne sont pas validés.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
