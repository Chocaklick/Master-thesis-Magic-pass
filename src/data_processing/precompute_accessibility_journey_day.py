"""Precompute one reference day of station-group journeys into resumable caches."""

from __future__ import annotations

import argparse
import gc
import json

import pandas as pd

from build_accessibility_station_group_journeys import (
    CONFIG_PATH, GROUP_PATH, NODE_PATH, OLD_NODE_PATH, SOURCE_ID,
    exact_metadata, group_fingerprint, load_feed_reference_tables,
    load_active_trip_info, validate_settings, build_day_network,
    flatten_connections, load_group_cache, route_group, write_group_cache,
    ROOT,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_date", choices=["20260204", "20260207"])
    args = parser.parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    metadata = exact_metadata(SOURCE_ID)
    archive_path = ROOT / metadata["raw_file"]
    reference = load_feed_reference_tables(archive_path)
    settings = validate_settings(config, reference)
    labels = {value: key for key, value in settings["reference_dates"].items()}
    trip_reference = load_active_trip_info(
        archive_path, reference, list(settings["reference_dates"].values()))
    groups = pd.read_csv(GROUP_PATH)
    group_nodes = pd.read_csv(NODE_PATH, dtype={"selected_stop_id": str})
    old_nodes = pd.read_csv(OLD_NODE_PATH, dtype={"selected_stop_id": str})
    municipality_nodes = old_nodes[old_nodes.node_role.eq("municipality_origin")].copy()
    network = build_day_network(
        archive_path, reference, trip_reference, args.reference_date,
        int(settings["default_transfer_seconds"]))
    connections = flatten_connections(network)
    expected = len(municipality_nodes) * (
        len(settings["outbound_sample_times"]) + len(settings["return_sample_times"]))
    for number, group in enumerate(groups.itertuples(index=False), start=1):
        nodes = group_nodes[group_nodes.station_group_id.eq(group.station_group_id)].copy()
        fingerprint = group_fingerprint(metadata["sha256"], settings,
                                        args.reference_date, municipality_nodes, nodes)
        cached = load_group_cache(args.reference_date, group.station_group_id,
                                  fingerprint, expected)
        if cached is not None:
            print(f"{args.reference_date} {number}/71 cache {group.station_group_name}",
                  flush=True)
            continue
        print(f"{args.reference_date} {number}/71 route {group.station_group_name}",
              flush=True)
        rows = route_group(network, connections, nodes, municipality_nodes,
                           settings, args.reference_date,
                           labels[args.reference_date])
        write_group_cache(args.reference_date, group.station_group_id, fingerprint, rows)
        gc.collect()


if __name__ == "__main__":
    main()
