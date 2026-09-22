"""Small deterministic GTFS Static router used by the thesis pipeline.

The module deliberately implements only the parts needed by the project:

* one GTFS feed and one service date at a time;
* stop/platform identifiers collapsed to their numeric Swiss DIDOK base;
* published generic transfers, with a conservative default interchange time;
* a backward profile connection scan for many origins to one destination;
* a round-based forward router for one origin to many destinations.

It is not intended to replace a production journey planner.  In particular,
real-time disruptions, fares, accessibility constraints and street walking
outside the published transfer table are out of scope.
"""

from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import gc
import zipfile

import numpy as np
import pandas as pd


INF = np.int32(2_000_000_000)

MODE_BITS = {
    "train": 1,
    "bus": 2,
    "tram_metro": 4,
    "ferry": 8,
    "aerial": 16,
    "funicular": 32,
    "taxi_other": 64,
}


def normalize_stop_id(value: str) -> str:
    """Collapse Swiss platform IDs such as 8503000:0:7 to 8503000."""

    value = str(value)
    head = value.split(":", 1)[0]
    return head if head.isdigit() else value


def parse_gtfs_time(value: str) -> int:
    hours, minutes, seconds = (int(part) for part in str(value).split(":"))
    return hours * 3600 + minutes * 60 + seconds


def format_gtfs_time(seconds: int | float | None) -> str:
    if seconds is None or pd.isna(seconds):
        return ""
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"


def route_type_mode(route_type: int | str) -> str:
    value = int(route_type)
    if 100 <= value < 200:
        return "train"
    if value == 202 or 700 <= value < 800:
        return "bus"
    if 400 <= value < 500 or 900 <= value < 1000:
        return "tram_metro"
    if 1000 <= value < 1100:
        return "ferry"
    if 1300 <= value < 1400:
        return "aerial"
    if 1400 <= value < 1500:
        return "funicular"
    return "taxi_other"


def mode_mask_label(mask: int) -> str:
    names = [name for name, bit in MODE_BITS.items() if int(mask) & bit]
    return "|".join(names)


def active_service_ids(
    calendar: pd.DataFrame, calendar_dates: pd.DataFrame, date: str
) -> set[str]:
    day = datetime.strptime(date, "%Y%m%d").strftime("%A").lower()
    active = calendar[
        calendar["start_date"].le(date)
        & calendar["end_date"].ge(date)
        & calendar[day].eq("1")
    ]
    result = set(active["service_id"])
    exceptions = calendar_dates[calendar_dates["date"].eq(date)]
    result.update(exceptions.loc[exceptions["exception_type"].eq("1"), "service_id"])
    result.difference_update(
        exceptions.loc[exceptions["exception_type"].eq("2"), "service_id"]
    )
    return result


def load_feed_reference_tables(archive_path) -> dict:
    with zipfile.ZipFile(archive_path) as archive:
        feed = pd.read_csv(archive.open("feed_info.txt"), dtype="string")
        calendar = pd.read_csv(archive.open("calendar.txt"), dtype="string")
        calendar_dates = pd.read_csv(
            archive.open("calendar_dates.txt"), dtype="string"
        )
        routes = pd.read_csv(
            archive.open("routes.txt"),
            dtype="string",
            usecols=["route_id", "route_type", "route_short_name", "route_desc"],
        )
        transfers = pd.read_csv(archive.open("transfers.txt"), dtype="string")

    if len(feed) != 1:
        raise ValueError("Expected one GTFS feed_info row")
    route_modes = {
        str(row.route_id): route_type_mode(row.route_type)
        for row in routes.itertuples(index=False)
    }
    return {
        "feed": feed.iloc[0].to_dict(),
        "calendar": calendar,
        "calendar_dates": calendar_dates,
        "routes": routes,
        "route_modes": route_modes,
        "transfers": transfers,
    }


def load_active_trip_info(archive_path, reference: dict, dates: list[str]) -> dict:
    active_services = {
        date: active_service_ids(
            reference["calendar"], reference["calendar_dates"], date
        )
        for date in dates
    }
    service_mask: dict[str, int] = {}
    for index, date in enumerate(dates):
        bit = 1 << index
        for service_id in active_services[date]:
            service_mask[service_id] = service_mask.get(service_id, 0) | bit

    trip_info: dict[str, tuple[str, str, int]] = {}
    with zipfile.ZipFile(archive_path) as archive:
        for chunk in pd.read_csv(
            archive.open("trips.txt"),
            dtype="string",
            usecols=["trip_id", "service_id", "route_id"],
            chunksize=250_000,
        ):
            chunk["day_mask"] = chunk["service_id"].map(service_mask).fillna(0).astype(int)
            for row in chunk[chunk["day_mask"].gt(0)].itertuples(index=False):
                mode = reference["route_modes"].get(str(row.route_id), "taxi_other")
                trip_info[str(row.trip_id)] = (
                    str(row.route_id),
                    mode,
                    int(row.day_mask),
                )
    return {
        "dates": dates,
        "active_services": active_services,
        "trip_info": trip_info,
    }


def _seconds_series(series: pd.Series) -> pd.Series:
    return (
        pd.to_numeric(series.str.slice(0, 2), errors="raise") * 3600
        + pd.to_numeric(series.str.slice(3, 5), errors="raise") * 60
        + pd.to_numeric(series.str.slice(6, 8), errors="raise")
    ).astype("int32")


def count_active_departures(
    archive_path, trip_reference: dict
) -> tuple[dict[str, dict[str, int]], dict]:
    """Count boardable scheduled departures at normalized stops for each date."""

    dates = trip_reference["dates"]
    trip_info = trip_reference["trip_info"]
    trip_masks = {trip_id: value[2] for trip_id, value in trip_info.items()}
    counts: dict[str, defaultdict[str, int]] = {
        date: defaultdict(int) for date in dates
    }
    active_stop_time_rows = {date: 0 for date in dates}
    total_rows = 0
    with zipfile.ZipFile(archive_path) as archive:
        for chunk in pd.read_csv(
            archive.open("stop_times.txt"),
            dtype="string",
            usecols=["trip_id", "stop_id", "pickup_type"],
            chunksize=750_000,
        ):
            total_rows += len(chunk)
            chunk["day_mask"] = chunk["trip_id"].map(trip_masks).fillna(0).astype(int)
            chunk = chunk[chunk["day_mask"].gt(0)].copy()
            chunk["base_stop_id"] = chunk["stop_id"].map(normalize_stop_id)
            boardable = ~chunk["pickup_type"].fillna("0").eq("1")
            for index, date in enumerate(dates):
                bit = 1 << index
                active = chunk[chunk["day_mask"].map(lambda value: bool(value & bit))]
                active_stop_time_rows[date] += len(active)
                values = active.loc[boardable.reindex(active.index, fill_value=False)]
                for stop_id, count in values["base_stop_id"].value_counts().items():
                    counts[date][str(stop_id)] += int(count)
    return (
        {date: dict(value) for date, value in counts.items()},
        {
            "total_stop_time_rows": int(total_rows),
            "active_stop_time_rows": active_stop_time_rows,
            "active_trip_counts": {
                date: sum(
                    1
                    for value in trip_info.values()
                    if value[2] & (1 << index)
                )
                for index, date in enumerate(dates)
            },
            "active_service_counts": {
                date: len(trip_reference["active_services"][date]) for date in dates
            },
        },
    )


def build_transfer_rules(
    transfers: pd.DataFrame, default_transfer_seconds: int
) -> tuple[dict[str, int], dict[str, list[tuple[str, int]]], dict]:
    route_specific = transfers[
        transfers[
            ["from_route_id", "to_route_id", "from_trip_id", "to_trip_id"]
        ]
        .notna()
        .any(axis=1)
    ]
    generic = transfers.drop(index=route_specific.index).copy()
    generic = generic[~generic["transfer_type"].eq("3")]
    generic["from_base"] = generic["from_stop_id"].map(normalize_stop_id)
    generic["to_base"] = generic["to_stop_id"].map(normalize_stop_id)
    generic["seconds"] = pd.to_numeric(
        generic["min_transfer_time"], errors="coerce"
    ).fillna(default_transfer_seconds)
    generic["seconds"] = generic["seconds"].clip(lower=0).astype(int)

    self_min: dict[str, int] = {}
    cross_min: dict[tuple[str, str], int] = {}
    for row in generic.itertuples(index=False):
        if row.from_base == row.to_base:
            current = self_min.get(row.from_base, default_transfer_seconds)
            self_min[row.from_base] = min(current, int(row.seconds))
        else:
            key = (row.from_base, row.to_base)
            cross_min[key] = min(cross_min.get(key, int(row.seconds)), int(row.seconds))
    cross: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for (from_stop, to_stop), seconds in sorted(cross_min.items()):
        cross[from_stop].append((to_stop, seconds))
    return (
        self_min,
        dict(cross),
        {
            "generic_transfer_rows": int(len(generic)),
            "route_or_trip_specific_transfer_rows_not_modelled": int(
                len(route_specific)
            ),
            "normalized_self_transfer_stops": int(len(self_min)),
            "normalized_cross_stop_transfer_links": int(len(cross_min)),
            "default_transfer_seconds": int(default_transfer_seconds),
        },
    )


@dataclass
class Pattern:
    route_id: str
    mode: str
    stops: tuple[int, ...]
    pickup: tuple[int, ...]
    dropoff: tuple[int, ...]
    arrivals: np.ndarray
    departures: np.ndarray
    trip_ids: tuple[str, ...]
    trip_numbers: np.ndarray


@dataclass
class DayNetwork:
    date: str
    stop_ids: tuple[str, ...]
    stop_index: dict[str, int]
    patterns: list[Pattern]
    stop_patterns: list[list[tuple[int, int]]]
    self_transfer_seconds: np.ndarray
    cross_transfers: list[list[tuple[int, int]]]
    pattern_summary: dict


def _non_overtaking_groups(arrivals: np.ndarray, departures: np.ndarray) -> list[np.ndarray]:
    order = np.argsort(departures[:, 0], kind="stable")
    groups: list[list[int]] = []
    last_times: list[np.ndarray] = []
    for trip in order:
        times = np.maximum(arrivals[trip], departures[trip])
        placed = False
        for group_index, last in enumerate(last_times):
            if np.all(times >= last):
                groups[group_index].append(int(trip))
                last_times[group_index] = times
                placed = True
                break
        if not placed:
            groups.append([int(trip)])
            last_times.append(times)
    return [np.asarray(group, dtype=np.int32) for group in groups]


def build_day_network(
    archive_path,
    reference: dict,
    trip_reference: dict,
    date: str,
    default_transfer_seconds: int,
) -> DayNetwork:
    date_index = trip_reference["dates"].index(date)
    date_bit = 1 << date_index
    active_trip_info = {
        trip_id: value
        for trip_id, value in trip_reference["trip_info"].items()
        if value[2] & date_bit
    }

    stop_ids: list[str] = []
    stop_index: dict[str, int] = {}

    def stop_number(stop_id: str) -> int:
        base = normalize_stop_id(stop_id)
        if base not in stop_index:
            stop_index[base] = len(stop_ids)
            stop_ids.append(base)
        return stop_index[base]

    grouped: dict[
        tuple[str, str, tuple[int, ...], tuple[int, ...], tuple[int, ...]],
        list[tuple[str, np.ndarray, np.ndarray]],
    ] = defaultdict(list)
    pending = pd.DataFrame()
    with zipfile.ZipFile(archive_path) as archive:
        for chunk in pd.read_csv(
            archive.open("stop_times.txt"),
            dtype="string",
            usecols=[
                "trip_id",
                "arrival_time",
                "departure_time",
                "stop_id",
                "stop_sequence",
                "pickup_type",
                "drop_off_type",
            ],
            chunksize=500_000,
        ):
            chunk = chunk[chunk["trip_id"].isin(active_trip_info)].copy()
            if not pending.empty:
                chunk = pd.concat([pending, chunk], ignore_index=True)
                pending = pd.DataFrame()
            if chunk.empty:
                continue
            last_trip = str(chunk.iloc[-1]["trip_id"])
            pending = chunk[chunk["trip_id"].eq(last_trip)].copy()
            complete = chunk[~chunk["trip_id"].eq(last_trip)].copy()
            if complete.empty:
                continue
            complete["arrival_seconds"] = _seconds_series(complete["arrival_time"])
            complete["departure_seconds"] = _seconds_series(
                complete["departure_time"]
            )
            complete["pickup"] = pd.to_numeric(
                complete["pickup_type"].fillna("0"), errors="raise"
            ).astype("int8")
            complete["dropoff"] = pd.to_numeric(
                complete["drop_off_type"].fillna("0"), errors="raise"
            ).astype("int8")
            complete["stop_sequence_number"] = pd.to_numeric(
                complete["stop_sequence"], errors="raise"
            ).astype("int32")
            complete["stop_number"] = complete["stop_id"].map(stop_number)
            for trip_id, rows in complete.groupby("trip_id", sort=False):
                rows = rows.sort_values("stop_sequence_number", kind="stable")
                if len(rows) < 2:
                    continue
                route_id, mode, _ = active_trip_info[str(trip_id)]
                stops = tuple(int(value) for value in rows["stop_number"])
                pickup = tuple(int(value) for value in rows["pickup"])
                dropoff = tuple(int(value) for value in rows["dropoff"])
                key = (route_id, mode, stops, pickup, dropoff)
                grouped[key].append(
                    (
                        str(trip_id),
                        rows["arrival_seconds"].to_numpy(dtype=np.int32),
                        rows["departure_seconds"].to_numpy(dtype=np.int32),
                    )
                )

    if not pending.empty:
        pending["arrival_seconds"] = _seconds_series(pending["arrival_time"])
        pending["departure_seconds"] = _seconds_series(pending["departure_time"])
        pending["pickup"] = pd.to_numeric(
            pending["pickup_type"].fillna("0"), errors="raise"
        ).astype("int8")
        pending["dropoff"] = pd.to_numeric(
            pending["drop_off_type"].fillna("0"), errors="raise"
        ).astype("int8")
        pending["stop_sequence_number"] = pd.to_numeric(
            pending["stop_sequence"], errors="raise"
        ).astype("int32")
        pending["stop_number"] = pending["stop_id"].map(stop_number)
        for trip_id, rows in pending.groupby("trip_id", sort=False):
            rows = rows.sort_values("stop_sequence_number", kind="stable")
            if len(rows) >= 2:
                route_id, mode, _ = active_trip_info[str(trip_id)]
                stops = tuple(int(value) for value in rows["stop_number"])
                pickup = tuple(int(value) for value in rows["pickup"])
                dropoff = tuple(int(value) for value in rows["dropoff"])
                grouped[(route_id, mode, stops, pickup, dropoff)].append(
                    (
                        str(trip_id),
                        rows["arrival_seconds"].to_numpy(dtype=np.int32),
                        rows["departure_seconds"].to_numpy(dtype=np.int32),
                    )
                )

    patterns: list[Pattern] = []
    trip_number = 0
    overtaking_source_patterns = 0
    for (route_id, mode, stops, pickup, dropoff), trips in grouped.items():
        arrivals = np.vstack([trip[1] for trip in trips]).astype(np.int32)
        departures = np.vstack([trip[2] for trip in trips]).astype(np.int32)
        groups = _non_overtaking_groups(arrivals, departures)
        if len(groups) > 1:
            overtaking_source_patterns += 1
        for indices in groups:
            subset_arrivals = arrivals[indices]
            subset_departures = departures[indices]
            order = np.argsort(subset_departures[:, 0], kind="stable")
            subset_arrivals = subset_arrivals[order]
            subset_departures = subset_departures[order]
            if len(subset_departures) > 1 and np.any(
                np.diff(subset_departures, axis=0) < 0
            ):
                raise ValueError("Overtaking split left an unsorted departure column")
            if np.any(subset_arrivals[:, 1:] < subset_departures[:, :-1]):
                raise ValueError("GTFS trip contains a backward in-vehicle time step")
            subset_ids = tuple(trips[int(indices[int(i)])][0] for i in order)
            numbers = np.arange(
                trip_number, trip_number + len(subset_ids), dtype=np.int32
            )
            trip_number += len(subset_ids)
            patterns.append(
                Pattern(
                    route_id=route_id,
                    mode=mode,
                    stops=stops,
                    pickup=pickup,
                    dropoff=dropoff,
                    arrivals=subset_arrivals,
                    departures=subset_departures,
                    trip_ids=subset_ids,
                    trip_numbers=numbers,
                )
            )

    self_rules, cross_rules, transfer_summary = build_transfer_rules(
        reference["transfers"], default_transfer_seconds
    )
    for stop_id in sorted(
        set(self_rules) | set(cross_rules) | {x for v in cross_rules.values() for x, _ in v}
    ):
        stop_number(stop_id)
    self_transfer = np.full(len(stop_ids), default_transfer_seconds, dtype=np.int32)
    for stop_id, seconds in self_rules.items():
        self_transfer[stop_index[stop_id]] = int(seconds)
    cross: list[list[tuple[int, int]]] = [[] for _ in stop_ids]
    for from_stop, links in cross_rules.items():
        from_number = stop_index[from_stop]
        cross[from_number] = [
            (stop_index[to_stop], int(seconds)) for to_stop, seconds in links
        ]

    stop_patterns: list[list[tuple[int, int]]] = [[] for _ in stop_ids]
    for pattern_id, pattern in enumerate(patterns):
        for position, stop in enumerate(pattern.stops):
            stop_patterns[stop].append((pattern_id, position))

    summary = {
        "service_date": date,
        "active_trips": int(len(active_trip_info)),
        "normalized_stops_in_network": int(len(stop_ids)),
        "route_patterns_before_overtaking_split": int(len(grouped)),
        "route_patterns_after_overtaking_split": int(len(patterns)),
        "source_patterns_requiring_overtaking_split": int(overtaking_source_patterns),
        "active_trip_rows_in_patterns": int(sum(len(p.trip_ids) for p in patterns)),
        **transfer_summary,
    }
    del grouped
    gc.collect()
    return DayNetwork(
        date=date,
        stop_ids=tuple(stop_ids),
        stop_index=stop_index,
        patterns=patterns,
        stop_patterns=stop_patterns,
        self_transfer_seconds=self_transfer,
        cross_transfers=cross,
        pattern_summary=summary,
    )


@dataclass(frozen=True)
class Journey:
    arrival_seconds: int
    first_departure_seconds: int
    mode_mask: int
    legs: int

    @property
    def transfers(self) -> int:
        return max(0, self.legs - 1)


@dataclass
class Connections:
    departure: np.ndarray
    arrival: np.ndarray
    from_stop: np.ndarray
    to_stop: np.ndarray
    trip_number: np.ndarray
    sequence: np.ndarray
    boardable: np.ndarray
    alightable: np.ndarray
    mode_bit: np.ndarray
    trip_count: int


def flatten_connections(network: DayNetwork) -> Connections:
    parts = {name: [] for name in [
        "departure", "arrival", "from_stop", "to_stop", "trip_number",
        "sequence", "boardable", "alightable", "mode_bit"
    ]}
    trip_count = 0
    for pattern in network.patterns:
        n_trips, n_stops = pattern.departures.shape
        if n_stops < 2:
            continue
        width = n_stops - 1
        parts["departure"].append(pattern.departures[:, :-1].reshape(-1))
        parts["arrival"].append(pattern.arrivals[:, 1:].reshape(-1))
        parts["from_stop"].append(
            np.tile(np.asarray(pattern.stops[:-1], dtype=np.int32), n_trips)
        )
        parts["to_stop"].append(
            np.tile(np.asarray(pattern.stops[1:], dtype=np.int32), n_trips)
        )
        parts["trip_number"].append(np.repeat(pattern.trip_numbers, width))
        parts["sequence"].append(
            np.tile(np.arange(width, dtype=np.int16), n_trips)
        )
        parts["boardable"].append(
            np.tile(np.asarray(pattern.pickup[:-1], dtype=np.int8) != 1, n_trips)
        )
        parts["alightable"].append(
            np.tile(np.asarray(pattern.dropoff[1:], dtype=np.int8) != 1, n_trips)
        )
        bit = MODE_BITS[pattern.mode]
        parts["mode_bit"].append(np.full(n_trips * width, bit, dtype=np.uint8))
        trip_count = max(trip_count, int(pattern.trip_numbers.max()) + 1)
    arrays = {name: np.concatenate(values) for name, values in parts.items()}
    order = np.lexsort((-arrays["sequence"], -arrays["departure"]))
    return Connections(
        **{name: values[order] for name, values in arrays.items()},
        trip_count=trip_count,
    )


class DestinationProfile:
    def __init__(self, network: DayNetwork, destination_stop_id: str):
        self.network = network
        if destination_stop_id not in network.stop_index:
            raise KeyError(f"Destination stop absent from active network: {destination_stop_id}")
        self.destination = network.stop_index[destination_stop_id]
        n_stops = len(network.stop_ids)
        self.negative_departures: list[list[int]] = [[] for _ in range(n_stops)]
        self.arrivals: list[list[int]] = [[] for _ in range(n_stops)]
        self.first_departures: list[list[int]] = [[] for _ in range(n_stops)]
        self.mode_masks: list[list[int]] = [[] for _ in range(n_stops)]
        self.legs: list[list[int]] = [[] for _ in range(n_stops)]

    def query_number(self, stop: int, ready_seconds: int) -> Journey | None:
        if stop == self.destination:
            return Journey(int(ready_seconds), int(ready_seconds), 0, 0)
        times = self.negative_departures[stop]
        index = bisect_right(times, -int(ready_seconds)) - 1
        if index < 0:
            return None
        return Journey(
            self.arrivals[stop][index],
            self.first_departures[stop][index],
            self.mode_masks[stop][index],
            self.legs[stop][index],
        )

    def query(self, stop_id: str, ready_seconds: int) -> Journey | None:
        stop = self.network.stop_index.get(str(stop_id))
        if stop is None:
            return None
        candidates = [self.query_number(stop, ready_seconds)]
        for other, duration in self.network.cross_transfers[stop]:
            if other == self.destination:
                candidates.append(
                    Journey(
                        int(ready_seconds + duration),
                        int(ready_seconds),
                        0,
                        0,
                    )
                )
            else:
                candidate = self.query_number(other, ready_seconds + duration)
                if candidate is not None:
                    candidates.append(candidate)
        return _best_journey(candidates)

    def add(self, stop: int, departure: int, journey: Journey) -> None:
        arrivals = self.arrivals[stop]
        if arrivals and not _journey_better(journey, Journey(
            arrivals[-1], self.first_departures[stop][-1],
            self.mode_masks[stop][-1], self.legs[stop][-1]
        )):
            return
        self.negative_departures[stop].append(-int(departure))
        arrivals.append(int(journey.arrival_seconds))
        self.first_departures[stop].append(int(journey.first_departure_seconds))
        self.mode_masks[stop].append(int(journey.mode_mask))
        self.legs[stop].append(int(journey.legs))


def _journey_better(left: Journey, right: Journey | None) -> bool:
    if right is None:
        return True
    return (
        left.arrival_seconds,
        left.legs,
        left.first_departure_seconds,
        left.mode_mask,
    ) < (
        right.arrival_seconds,
        right.legs,
        right.first_departure_seconds,
        right.mode_mask,
    )


def _best_journey(values) -> Journey | None:
    best = None
    for value in values:
        if value is not None and _journey_better(value, best):
            best = value
    return best


def build_destination_profile(
    network: DayNetwork,
    connections: Connections,
    destination_stop_id: str,
    max_legs: int,
    earliest_departure_seconds: int,
    latest_arrival_seconds: int,
) -> DestinationProfile:
    profile = DestinationProfile(network, destination_stop_id)
    target = profile.destination
    trip_state: list[Journey | None] = [None] * connections.trip_count

    for index in range(len(connections.departure)):
        departure = int(connections.departure[index])
        if departure > latest_arrival_seconds:
            continue
        if departure < earliest_departure_seconds:
            break
        arrival = int(connections.arrival[index])
        from_stop = int(connections.from_stop[index])
        to_stop = int(connections.to_stop[index])
        trip = int(connections.trip_number[index])
        mode_bit = int(connections.mode_bit[index])

        candidates: list[Journey | None] = [trip_state[trip]]
        if bool(connections.alightable[index]):
            if to_stop == target and arrival <= latest_arrival_seconds:
                candidates.append(Journey(arrival, departure, mode_bit, 1))
            ready = arrival + int(network.self_transfer_seconds[to_stop])
            onward = profile.query_number(to_stop, ready)
            if onward is not None and onward.legs and 1 + onward.legs <= max_legs:
                candidates.append(
                    Journey(
                        onward.arrival_seconds,
                        departure,
                        mode_bit | onward.mode_mask,
                        1 + onward.legs,
                    )
                )
            for other, duration in network.cross_transfers[to_stop]:
                if other == target:
                    candidates.append(
                        Journey(arrival + duration, departure, mode_bit, 1)
                    )
                else:
                    onward = profile.query_number(other, arrival + duration)
                    if onward is not None and onward.legs and 1 + onward.legs <= max_legs:
                        candidates.append(
                            Journey(
                                onward.arrival_seconds,
                                departure,
                                mode_bit | onward.mode_mask,
                                1 + onward.legs,
                            )
                        )
        best = _best_journey(candidates)
        if best is None:
            continue
        extended = Journey(
            best.arrival_seconds, departure, best.mode_mask | mode_bit, best.legs
        )
        if (
            extended.legs > max_legs
            or extended.arrival_seconds > latest_arrival_seconds
        ):
            continue
        trip_state[trip] = extended
        if bool(connections.boardable[index]):
            profile.add(from_stop, departure, extended)
    return profile


def forward_raptor(
    network: DayNetwork,
    origin_stop_id: str,
    start_seconds: int,
    max_legs: int,
) -> dict[str, Journey]:
    origin = network.stop_index.get(str(origin_stop_id))
    if origin is None:
        return {}
    n_stops = len(network.stop_ids)
    best_arrival = np.full(n_stops, INF, dtype=np.int32)
    best_first = np.full(n_stops, -1, dtype=np.int32)
    best_mask = np.zeros(n_stops, dtype=np.uint8)
    best_legs = np.zeros(n_stops, dtype=np.int8)
    best_arrival[origin] = int(start_seconds)
    best_first[origin] = int(start_seconds)
    marked = {origin}

    for round_number in range(max_legs):
        route_starts: dict[int, int] = {}
        for stop in marked:
            for pattern_id, position in network.stop_patterns[stop]:
                route_starts[pattern_id] = min(
                    position, route_starts.get(pattern_id, position)
                )
        new_arrival = best_arrival.copy()
        new_first = best_first.copy()
        new_mask = best_mask.copy()
        new_legs = best_legs.copy()
        improved: set[int] = set()

        for pattern_id, start_position in route_starts.items():
            pattern = network.patterns[pattern_id]
            boarded_trip = None
            boarded_first = -1
            boarded_mask = 0
            boarded_legs = 0
            for position in range(start_position, len(pattern.stops)):
                stop = pattern.stops[position]
                if boarded_trip is not None and pattern.dropoff[position] != 1:
                    arrival = int(pattern.arrivals[boarded_trip, position])
                    if arrival < boarded_first or arrival < int(start_seconds):
                        raise RuntimeError(
                            "Forward router produced backward time: "
                            f"route={pattern.route_id} trip={pattern.trip_ids[boarded_trip]} "
                            f"position={position} arrival={arrival} "
                            f"first_departure={boarded_first} start={start_seconds}"
                        )
                    if arrival < int(new_arrival[stop]):
                        new_arrival[stop] = arrival
                        new_first[stop] = boarded_first
                        new_mask[stop] = boarded_mask
                        new_legs[stop] = boarded_legs
                        improved.add(stop)

                if pattern.pickup[position] == 1 or int(best_arrival[stop]) >= int(INF):
                    continue
                transfer = 0 if round_number == 0 and stop == origin else int(
                    network.self_transfer_seconds[stop]
                )
                ready = int(best_arrival[stop]) + transfer
                candidate = int(
                    np.searchsorted(pattern.departures[:, position], ready, side="left")
                )
                if candidate >= len(pattern.trip_ids):
                    continue
                if boarded_trip is None or candidate < boarded_trip:
                    if int(pattern.departures[candidate, position]) < ready:
                        raise RuntimeError("Binary search selected a departure before readiness")
                    boarded_trip = candidate
                    boarded_first = (
                        int(pattern.departures[candidate, position])
                        if int(best_legs[stop]) == 0
                        else int(best_first[stop])
                    )
                    boarded_mask = int(best_mask[stop]) | MODE_BITS[pattern.mode]
                    boarded_legs = int(best_legs[stop]) + 1

        queue = list(improved)
        queue_position = 0
        while queue_position < len(queue):
            stop = queue[queue_position]
            queue_position += 1
            for other, duration in network.cross_transfers[stop]:
                arrival = int(new_arrival[stop]) + duration
                if arrival < int(new_arrival[other]):
                    new_arrival[other] = arrival
                    new_first[other] = new_first[stop]
                    new_mask[other] = new_mask[stop]
                    new_legs[other] = new_legs[stop]
                    if other not in improved:
                        improved.add(other)
                        queue.append(other)

        changed = {
            stop for stop in improved if int(new_arrival[stop]) < int(best_arrival[stop])
        }
        best_arrival, best_first, best_mask, best_legs = (
            new_arrival,
            new_first,
            new_mask,
            new_legs,
        )
        marked = changed
        if not marked:
            break

    result = {}
    for stop, arrival in enumerate(best_arrival):
        if int(arrival) >= int(INF):
            continue
        result[network.stop_ids[stop]] = Journey(
            int(arrival),
            int(best_first[stop]),
            int(best_mask[stop]),
            int(best_legs[stop]),
        )
    return result
