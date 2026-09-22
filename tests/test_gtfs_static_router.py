from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "data_processing"))

from gtfs_static_router import (  # noqa: E402
    DayNetwork,
    MODE_BITS,
    Pattern,
    build_destination_profile,
    flatten_connections,
    forward_raptor,
    format_gtfs_time,
    mode_mask_label,
    normalize_stop_id,
    parse_gtfs_time,
)


def synthetic_network() -> DayNetwork:
    first = Pattern(
        route_id="rail",
        mode="train",
        stops=(0, 1),
        pickup=(0, 0),
        dropoff=(0, 0),
        arrivals=np.asarray([[28_800, 30_600]], dtype=np.int32),
        departures=np.asarray([[28_800, 30_600]], dtype=np.int32),
        trip_ids=("rail-1",),
        trip_numbers=np.asarray([0], dtype=np.int32),
    )
    second = Pattern(
        route_id="bus",
        mode="bus",
        stops=(1, 2),
        pickup=(0, 0),
        dropoff=(0, 0),
        arrivals=np.asarray([[30_900, 32_400]], dtype=np.int32),
        departures=np.asarray([[30_900, 32_400]], dtype=np.int32),
        trip_ids=("bus-1",),
        trip_numbers=np.asarray([1], dtype=np.int32),
    )
    return DayNetwork(
        date="20260204",
        stop_ids=("A", "B", "C"),
        stop_index={"A": 0, "B": 1, "C": 2},
        patterns=[first, second],
        stop_patterns=[[(0, 0)], [(0, 1), (1, 0)], [(1, 1)]],
        self_transfer_seconds=np.asarray([120, 120, 120], dtype=np.int32),
        cross_transfers=[[], [], []],
        pattern_summary={},
    )


def test_time_and_stop_helpers_are_deterministic() -> None:
    assert normalize_stop_id("8503000:0:7") == "8503000"
    assert normalize_stop_id("custom:platform") == "custom:platform"
    assert parse_gtfs_time("25:10:05") == 90_605
    assert format_gtfs_time(90_605) == "25:10:05"
    mask = MODE_BITS["train"] | MODE_BITS["bus"]
    assert mode_mask_label(mask) == "train|bus"


def test_backward_profile_and_forward_router_agree_on_transfer_journey() -> None:
    network = synthetic_network()
    profile = build_destination_profile(
        network,
        flatten_connections(network),
        destination_stop_id="C",
        max_legs=2,
        earliest_departure_seconds=28_200,
        latest_arrival_seconds=36_000,
    )
    outbound = profile.query("A", 28_200)
    assert outbound is not None
    assert outbound.first_departure_seconds == 28_800
    assert outbound.arrival_seconds == 32_400
    assert outbound.legs == 2
    assert outbound.transfers == 1
    assert mode_mask_label(outbound.mode_mask) == "train|bus"

    forward = forward_raptor(network, "A", 28_200, max_legs=2)
    assert forward["C"] == outbound
    assert "C" not in forward_raptor(network, "A", 28_200, max_legs=1)
