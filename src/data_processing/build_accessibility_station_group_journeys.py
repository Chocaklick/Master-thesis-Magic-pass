"""Route every station group to every hotel municipality on winter-2026 GTFS.

The calculation is descriptive and current. Results are cached independently
for each station group and reference day so an interrupted run resumes without
recomputing completed groups.
"""

from __future__ import annotations

import gc
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "data_processing"))

from build_public_transport_journey_context import (  # noqa: E402
    SOURCE_ID,
    aggregate_samples as old_aggregate_samples,
    better_sample,
    exact_metadata,
    sample_row,
    validate_settings,
)
from gtfs_static_router import (  # noqa: E402
    build_day_network,
    build_destination_profile,
    flatten_connections,
    forward_raptor,
    load_active_trip_info,
    load_feed_reference_tables,
    parse_gtfs_time,
)


CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
GROUP_PATH = ROOT / "data_processed" / "accessibility_station_groups.csv"
NODE_PATH = ROOT / "reports" / "accessibility_station_access_nodes.csv"
OLD_NODE_PATH = ROOT / "reports" / "public_transport_journey_nodes.csv"
SAMPLE_OUTPUT = ROOT / "data_processed" / "accessibility_station_group_journey_samples.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_station_group_journey_context.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_station_group_journey_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "56_TEMPS_TRAJET_GROUPES_STATIONS_COMMUNES_FR.md"
CACHE_DIR = ROOT / "data_interim" / "accessibility_station_group_journeys"
INTERPRETATION = (
    "official_winter_2026_gtfs_static_current_descriptive_station_group_access_"
    "not_historical_or_causal_accessibility"
)


def hash_frame(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, lineterminator="\n").encode("utf-8")


def group_fingerprint(gtfs_sha256: str, settings: dict, date: str,
                      municipality_nodes: pd.DataFrame,
                      group_nodes: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(gtfs_sha256.encode("ascii"))
    digest.update(json.dumps(settings, sort_keys=True).encode("utf-8"))
    digest.update(date.encode("ascii"))
    digest.update(hash_frame(municipality_nodes))
    digest.update(hash_frame(group_nodes))
    for path in [Path(__file__), ROOT / "src" / "data_processing" /
                 "build_public_transport_journey_context.py",
                 ROOT / "src" / "data_processing" / "gtfs_static_router.py"]:
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def cache_paths(date: str, group_id: str) -> tuple[Path, Path]:
    safe = hashlib.sha1(group_id.encode("utf-8")).hexdigest()[:16]
    base = CACHE_DIR / date / f"{safe}_{group_id[:36]}"
    return base.with_suffix(".csv"), base.with_suffix(".metadata.json")


def load_group_cache(date: str, group_id: str, fingerprint: str,
                     expected_rows: int):
    rows_path, meta_path = cache_paths(date, group_id)
    if not rows_path.exists() or not meta_path.exists():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("fingerprint") != fingerprint or meta.get("rows") != expected_rows:
        return None
    rows = pd.read_csv(rows_path, dtype={"origin_stop_id": str,
                                        "destination_stop_id": str}).to_dict("records")
    return rows if len(rows) == expected_rows else None


def write_group_cache(date: str, group_id: str, fingerprint: str,
                      rows: list[dict]) -> None:
    rows_path, meta_path = cache_paths(date, group_id)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(rows_path, index=False, lineterminator="\n")
    meta_path.write_text(json.dumps({
        "station_group_id": group_id,
        "reference_date": date,
        "fingerprint": fingerprint,
        "rows": len(rows),
    }, indent=2) + "\n", encoding="utf-8")


def route_group(network, connections, group_nodes: pd.DataFrame,
                municipality_nodes: pd.DataFrame, settings: dict,
                date: str, day_label: str) -> list[dict]:
    outbound_times = [parse_gtfs_time(v) for v in settings["outbound_sample_times"]]
    return_times = [parse_gtfs_time(v) for v in settings["return_sample_times"]]
    maximum_legs = int(settings["maximum_vehicle_legs"])
    maximum_minutes = int(settings["maximum_generalized_elapsed_minutes"])
    group_id = group_nodes.station_group_id.iloc[0]
    group_name = group_nodes.station_group_name.iloc[0]
    samples: dict[tuple, dict] = {}

    for access in group_nodes.itertuples(index=False):
        access_dict = access._asdict()
        access_dict["component_resort_id"] = access.access_point_id
        access_dict["component_resort_name"] = access.access_point_name
        access_series = pd.Series(access_dict)
        stop_id = str(access.selected_stop_id)
        profile = (build_destination_profile(
            network, connections, stop_id, maximum_legs, min(outbound_times),
            max(outbound_times) + maximum_minutes * 60,
        ) if stop_id in network.stop_index else None)
        for municipality in municipality_nodes.itertuples(index=False):
            municipality_series = pd.Series(municipality._asdict())
            pair = {
                "station_group_id": group_id,
                "station_group_name": group_name,
                "municipality_bfs_id": int(municipality.municipality_bfs_id),
                "boundary_bfs_id_2026": int(municipality.boundary_bfs_id_2026),
                "municipality_name": municipality.municipality_name,
            }
            for requested in outbound_times:
                journey = profile.query(str(municipality.selected_stop_id), requested) \
                    if profile is not None else None
                row = sample_row(
                    pair, "outbound_municipality_to_destination", day_label, date,
                    requested, municipality_series, access_series, journey,
                    maximum_legs, maximum_minutes,
                )
                row["interpretation"] = INTERPRETATION
                key = (group_id, int(municipality.municipality_bfs_id),
                       "outbound_municipality_to_destination", date, requested)
                samples[key] = better_sample(samples.get(key), row)
        del profile
        gc.collect()

        for requested in return_times:
            routes = forward_raptor(network, stop_id, requested, maximum_legs) \
                if stop_id in network.stop_index else {}
            for municipality in municipality_nodes.itertuples(index=False):
                municipality_series = pd.Series(municipality._asdict())
                pair = {
                    "station_group_id": group_id,
                    "station_group_name": group_name,
                    "municipality_bfs_id": int(municipality.municipality_bfs_id),
                    "boundary_bfs_id_2026": int(municipality.boundary_bfs_id_2026),
                    "municipality_name": municipality.municipality_name,
                }
                row = sample_row(
                    pair, "return_destination_to_municipality", day_label, date,
                    requested, access_series, municipality_series,
                    routes.get(str(municipality.selected_stop_id)), maximum_legs,
                    maximum_minutes,
                )
                row["destination_component_resort_id"] = access.access_point_id
                row["destination_component_resort_name"] = access.access_point_name
                row["interpretation"] = INTERPRETATION
                key = (group_id, int(municipality.municipality_bfs_id),
                       "return_destination_to_municipality", date, requested)
                samples[key] = better_sample(samples.get(key), row)
        gc.collect()

    expected = len(municipality_nodes) * (len(outbound_times) + len(return_times))
    if len(samples) != expected:
        raise ValueError(f"Unexpected group-day grain for {group_id}: {len(samples)}")
    return list(samples.values())


def pipe_unique(values: pd.Series) -> str:
    return "|".join(sorted({str(v) for v in values.dropna() if str(v)}))


def aggregate(samples: pd.DataFrame, municipality_nodes: pd.DataFrame,
              group_nodes: pd.DataFrame, settings: dict) -> pd.DataFrame:
    rows = []
    keys = ["station_group_id", "station_group_name", "municipality_bfs_id",
            "boundary_bfs_id_2026", "municipality_name"]
    expected_out = len(settings["reference_dates"]) * len(settings["outbound_sample_times"])
    expected_return = len(settings["reference_dates"]) * len(settings["return_sample_times"])
    origin_lookup = municipality_nodes.set_index("municipality_bfs_id")
    usable_group = group_nodes.groupby("station_group_id").descriptive_routing_node_approved.any()
    for values, group in samples.groupby(keys, sort=False, dropna=False):
        row = dict(zip(keys, values))
        origin = origin_lookup.loc[int(row["municipality_bfs_id"])]
        row.update({
            "municipality_main_stop_id": origin.selected_stop_id,
            "municipality_main_stop_name": origin.selected_stop_name,
            "municipality_main_stop_selection_method": origin.selection_method,
            "municipality_main_stop_distance_from_representative_point_km":
                float(origin.selected_stop_distance_from_reference_point_km),
        })
        for direction, prefix, expected in [
            ("outbound_municipality_to_destination", "outbound", expected_out),
            ("return_destination_to_municipality", "return", expected_return),
        ]:
            subset = group[group.direction.eq(direction)]
            feasible = subset[subset.journey_feasible.astype(str).str.lower().eq("true")]
            row[f"{prefix}_scheduled_samples"] = len(subset)
            row[f"{prefix}_feasible_samples"] = len(feasible)
            row[f"{prefix}_sample_coverage_share"] = len(feasible) / expected
            for metric in ["initial_wait_minutes", "scheduled_journey_minutes",
                           "generalized_elapsed_minutes"]:
                values_numeric = pd.to_numeric(feasible[metric], errors="coerce")
                row[f"{prefix}_mean_{metric}"] = (float(values_numeric.mean())
                                                     if len(feasible) else np.nan)
                row[f"{prefix}_maximum_{metric}"] = (float(values_numeric.max())
                                                        if len(feasible) else np.nan)
            transfers = pd.to_numeric(feasible.transfers, errors="coerce")
            row[f"{prefix}_maximum_transfers"] = (int(transfers.max())
                                                     if transfers.notna().any() else pd.NA)
            row[f"{prefix}_transport_modes"] = pipe_unique(feasible.transport_modes)
            row[f"{prefix}_access_point_ids_used"] = pipe_unique(
                feasible.destination_component_resort_id)
            row[f"{prefix}_access_point_names_used"] = pipe_unique(
                feasible.destination_component_resort_name)
        out = row["outbound_mean_generalized_elapsed_minutes"]
        ret = row["return_mean_generalized_elapsed_minutes"]
        row["mean_round_trip_generalized_minutes"] = out + ret if pd.notna(out) and pd.notna(ret) else np.nan
        row["mean_one_way_generalized_minutes"] = (out + ret) / 2 if pd.notna(out) and pd.notna(ret) else np.nan
        row["routing_pair_complete"] = (
            row["outbound_sample_coverage_share"] == 1 and
            row["return_sample_coverage_share"] == 1)
        row["within_30_minutes"] = bool(pd.notna(row["mean_one_way_generalized_minutes"]) and row["mean_one_way_generalized_minutes"] <= 30)
        row["within_60_minutes"] = bool(pd.notna(row["mean_one_way_generalized_minutes"]) and row["mean_one_way_generalized_minutes"] <= 60)
        row["within_90_minutes"] = bool(pd.notna(row["mean_one_way_generalized_minutes"]) and row["mean_one_way_generalized_minutes"] <= 90)
        row["within_120_minutes"] = bool(pd.notna(row["mean_one_way_generalized_minutes"]) and row["mean_one_way_generalized_minutes"] <= 120)
        row["station_group_has_reviewed_current_access_node"] = bool(usable_group.loc[row["station_group_id"]])
        row["descriptive_accessibility_usable"] = bool(
            row["routing_pair_complete"] and row["station_group_has_reviewed_current_access_node"])
        row.update({
            "gtfs_feed_version": settings["feed_version"],
            "reference_dates": "|".join(settings["reference_dates"].values()),
            "outbound_sampling_window": "08:00-10:00_every_30_minutes_inclusive",
            "return_sampling_window": "15:00-18:00_every_30_minutes_inclusive",
            "current_access_assumption": "fixed_current_access_for_initial_descriptive_screen",
            "historical_stability_status": settings["historical_stability_status"],
            "interpretation": INTERPRETATION,
            "source_id": SOURCE_ID,
            "causal_accessibility_feature_approved": False,
        })
        rows.append(row)
    result = pd.DataFrame(rows)
    expected = 71 * 186
    if len(result) != expected or result.duplicated(
            ["station_group_id", "municipality_bfs_id"]).any():
        raise ValueError(f"Expected {expected} unique station-group/municipality pairs")
    return result


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    metadata = exact_metadata(SOURCE_ID)
    archive_path = ROOT / metadata["raw_file"]
    reference = load_feed_reference_tables(archive_path)
    settings = validate_settings(config, reference)
    dates = list(settings["reference_dates"].values())
    trip_reference = load_active_trip_info(archive_path, reference, dates)
    groups = pd.read_csv(GROUP_PATH)
    group_nodes = pd.read_csv(NODE_PATH, dtype={"selected_stop_id": str})
    old_nodes = pd.read_csv(OLD_NODE_PATH, dtype={"selected_stop_id": str})
    municipality_nodes = old_nodes[old_nodes.node_role.eq("municipality_origin")].copy()
    if len(groups) != 71 or len(municipality_nodes) != 186 or len(group_nodes) != 75:
        raise ValueError("Unexpected group, municipality or access-node universe")
    if set(group_nodes.station_group_id) != set(groups.station_group_id):
        raise ValueError("Journey nodes do not cover every station group")

    all_rows = []
    network_summaries = []
    expected_group_day_rows = len(municipality_nodes) * (
        len(settings["outbound_sample_times"]) + len(settings["return_sample_times"]))
    for day_label, date in settings["reference_dates"].items():
        network = build_day_network(
            archive_path, reference, trip_reference, date,
            int(settings["default_transfer_seconds"]))
        connections = flatten_connections(network)
        network_summaries.append(network.pattern_summary)
        for number, group in enumerate(groups.itertuples(index=False), start=1):
            nodes = group_nodes[group_nodes.station_group_id.eq(group.station_group_id)].copy()
            fingerprint = group_fingerprint(metadata["sha256"], settings, date,
                                            municipality_nodes, nodes)
            rows = load_group_cache(date, group.station_group_id, fingerprint,
                                    expected_group_day_rows)
            if rows is None:
                print(f"{date} {number}/71 route {group.station_group_name}", flush=True)
                rows = route_group(network, connections, nodes, municipality_nodes,
                                   settings, date, day_label)
                write_group_cache(date, group.station_group_id, fingerprint, rows)
            else:
                print(f"{date} {number}/71 cache {group.station_group_name}", flush=True)
            all_rows.extend(rows)
        del connections, network
        gc.collect()

    samples = pd.DataFrame(all_rows)
    expected_samples = 71 * 186 * 2 * 12
    if len(samples) != expected_samples:
        raise ValueError(f"Unexpected journey sample count {len(samples)} != {expected_samples}")
    samples = samples.sort_values([
        "station_group_id", "municipality_bfs_id", "direction",
        "reference_date", "requested_departure_time"], kind="stable")
    samples.to_csv(SAMPLE_OUTPUT, index=False, lineterminator="\n")
    pairs = aggregate(samples, municipality_nodes, group_nodes, settings)
    pairs.to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")

    complete = pairs.routing_pair_complete.sum()
    usable = pairs.descriptive_accessibility_usable.sum()
    metrics = {
        "analysis_date": "2026-10-02",
        "source_id": SOURCE_ID,
        "gtfs_sha256": metadata["sha256"],
        "feed_version": settings["feed_version"],
        "reference_dates": settings["reference_dates"],
        "station_groups": 71,
        "station_access_nodes": len(group_nodes),
        "municipality_origins": 186,
        "station_group_municipality_pairs": len(pairs),
        "journey_samples": len(samples),
        "feasible_journey_samples": int(samples.journey_feasible.astype(str).str.lower().eq("true").sum()),
        "complete_pairs": int(complete),
        "descriptive_usable_pairs": int(usable),
        "pairs_within_30_minutes": int(pairs.within_30_minutes.sum()),
        "pairs_within_60_minutes": int(pairs.within_60_minutes.sum()),
        "pairs_within_90_minutes": int(pairs.within_90_minutes.sum()),
        "pairs_within_120_minutes": int(pairs.within_120_minutes.sum()),
        "municipalities_with_at_least_one_group_within_120_minutes": int(
            pairs[pairs.within_120_minutes].municipality_bfs_id.nunique()),
        "groups_with_at_least_one_municipality_within_120_minutes": int(
            pairs[pairs.within_120_minutes].station_group_id.nunique()),
        "median_one_way_generalized_minutes": float(pairs.mean_one_way_generalized_minutes.median()),
        "historical_stability_status": settings["historical_stability_status"],
        "fixed_current_access_assumption": True,
        "causal_accessibility_features_approved": 0,
        "network_summaries": network_summaries,
        "cache_directory": str(CACHE_DIR.relative_to(ROOT)).replace("\\", "/"),
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [CONFIG_PATH, GROUP_PATH, NODE_PATH, OLD_NODE_PATH]
        },
    }
    SUMMARY_OUTPUT.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    report = f"""# Temps de trajet entre groupes-stations et communes — étape 6

## Résultat

Le réseau horaire officiel GTFS hiver 2026 relie maintenant les **71 groupes-stations** aux **186 séries communales hôtelières**, soit **{len(pairs):,} couples** et **{len(samples):,} requêtes horaires**. Le meilleur point d'accès du groupe est retenu séparément pour chaque horaire.

| Indicateur | Nombre |
|---|---:|
| Couples complets sur les 24 horaires | {int(complete):,} |
| Couples utilisables descriptivement après contrôle du nœud | {int(usable):,} |
| Temps moyen aller simple ≤ 30 min | {metrics['pairs_within_30_minutes']:,} |
| ≤ 60 min | {metrics['pairs_within_60_minutes']:,} |
| ≤ 90 min | {metrics['pairs_within_90_minutes']:,} |
| ≤ 120 min | {metrics['pairs_within_120_minutes']:,} |
| Communes avec au moins un groupe à ≤ 120 min | {metrics['municipalities_with_at_least_one_group_within_120_minutes']} / 186 |
| Groupes avec au moins une commune à ≤ 120 min | {metrics['groups_with_at_least_one_municipality_within_120_minutes']} / 71 |

Le temps généralisé inclut l'attente jusqu'au premier départ. Cinq départs aller entre 08:00 et 10:00 et sept retours entre 15:00 et 18:00 sont testés le mercredi 4 et le samedi 7 février 2026. Les seuils 30/60/90/120 minutes sont des variantes descriptives, pas une définition imposée du bassin touristique.

## Limites

Il s'agit d'horaires publiés actuels : ni retards, ni voiture, ni marche non codée, ni tarifs. Conformément à la décision du chercheur, l'accès actuel est maintenu fixe pour le premier test; la stabilité historique reste `{settings['historical_stability_status']}`. Les résultats sont donc adaptés à la construction d'expositions descriptives, pas à une interprétation causale.

## Reprise et fichiers

Le cache est enregistré **par groupe et par jour** dans `{metrics['cache_directory']}`. Une interruption reprend aux groupes non calculés.

- `data_processed/accessibility_station_group_journey_context.csv` : un couple groupe–commune;
- `data_processed/accessibility_station_group_journey_samples.csv` : les requêtes horaires;
- `reports/accessibility_station_group_journey_summary.json` : comptes et empreintes.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
