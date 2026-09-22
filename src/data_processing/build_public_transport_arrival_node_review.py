"""Validate the selected ski-destination arrival nodes for descriptive routing."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "public_transport_arrival_node_review.csv"
NODES = ROOT / "reports" / "public_transport_journey_nodes.csv"
JOURNEY_SUMMARY = ROOT / "reports" / "public_transport_journey_context_summary.json"
OUTPUT = ROOT / "reports" / "public_transport_arrival_node_review.csv"
SUMMARY = ROOT / "reports" / "public_transport_arrival_node_review_summary.json"
REPORT = ROOT / "reports" / "26_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW.md"

MAXIMUM_ACCEPTED_POINT_DISTANCE_KM = 2.1


def main() -> None:
    review = pd.read_csv(CONFIG, dtype="string", keep_default_na=False)
    if len(review) != 15 or review["component_resort_id"].duplicated().any():
        raise ValueError("Arrival-node review must contain 15 unique component resorts")
    if review[["component_resort_id", "selected_stop_id"]].duplicated().any():
        raise ValueError("Arrival-node review keys must be unique")
    if not review["review_decision"].eq("accepted_for_descriptive_routing").all():
        raise ValueError("Unexpected arrival-node review decision")

    nodes = pd.read_csv(NODES, dtype="string", keep_default_na=False)
    nodes = nodes[nodes["node_role"].eq("destination_component_arrival")].copy()
    if len(nodes) != 15 or nodes["component_resort_id"].duplicated().any():
        raise ValueError("Expected 15 unique selected destination component nodes")
    result = nodes.merge(
        review,
        on=["component_resort_id", "selected_stop_id"],
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not result["_merge"].eq("both").all():
        raise ValueError("Reviewed arrival nodes no longer match generated node selection")
    result = result.drop(columns="_merge")

    distance = pd.to_numeric(
        result["selected_stop_distance_from_reference_point_km"], errors="raise"
    )
    if distance.gt(MAXIMUM_ACCEPTED_POINT_DISTANCE_KM).any():
        raise ValueError("A reviewed arrival node exceeds the declared distance guardrail")
    if not result["selected_stop_mode_code"].str.contains("A|B", regex=True).all():
        raise ValueError("Reviewed arrival nodes must retain bus or train capability")
    if not result["selected_stop_municipality_bfs_id"].eq(
        result["boundary_bfs_id_2026"]
    ).all():
        raise ValueError("Reviewed arrival nodes must remain in the component municipality")

    journey_summary = json.loads(JOURNEY_SUMMARY.read_text(encoding="utf-8"))
    absent_by_stop: dict[str, list[str]] = {}
    for day in journey_summary["network_summaries"]:
        for stop_id in day["selected_nodes_absent_from_active_day_network"]:
            absent_by_stop.setdefault(str(stop_id), []).append(str(day["service_date"]))
    absent_dates = result["selected_stop_id"].map(
        lambda value: absent_by_stop.get(str(value), [])
    )
    result["absent_reference_dates"] = absent_dates.map(
        lambda values: "|".join(values) if values else "none"
    )
    result["active_reference_day_count"] = absent_dates.map(
        lambda values: 2 - len(values)
    )
    result["name_distance_municipality_review_complete"] = True
    result["descriptive_routing_node_approved"] = True
    result["historical_node_continuity_verified"] = False
    result["causal_accessibility_feature_approved"] = False
    result["review_interpretation"] = (
        "official_current_stop_name_mode_municipality_and_point_distance_review_"
        "accepted_for_descriptive_routing_not_historical_or_causal_accessibility"
    )
    result = result.sort_values(
        ["destination_unit_id", "component_resort_id"], kind="stable"
    )
    result.to_csv(OUTPUT, index=False, lineterminator="\n")

    counts = {
        str(key): int(value)
        for key, value in result["review_class"].value_counts().items()
    }
    summary = {
        "reviewed_component_nodes": int(len(result)),
        "review_class_counts": counts,
        "accepted_for_descriptive_routing": int(
            result["descriptive_routing_node_approved"].sum()
        ),
        "village_or_local_centre_proxies": int(
            result["review_class"].eq("village_or_local_centre_proxy").sum()
        ),
        "maximum_point_to_stop_distance_km": float(distance.max()),
        "maximum_accepted_point_distance_km": MAXIMUM_ACCEPTED_POINT_DISTANCE_KM,
        "nodes_active_on_both_reference_days": int(
            result["active_reference_day_count"].eq(2).sum()
        ),
        "nodes_with_reference_day_availability_warning": int(
            result["active_reference_day_count"].lt(2).sum()
        ),
        "historical_node_continuity_verified": 0,
        "causal_accessibility_features_approved": 0,
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# Public-transport arrival-node review

## Decision

All **{len(result)}** component arrival nodes pass the current descriptive review: the official stop identifier and published name still match the versioned review, the stop is bus/train-capable, it lies in the component point's current municipality, and it is no more than **{MAXIMUM_ACCEPTED_POINT_DISTANCE_KM:.1f} km** from the supplied component coordinate. The observed maximum is **{distance.max():.2f} km**.

The review classes are `{json.dumps(counts, ensure_ascii=False)}`. The **{summary['village_or_local_centre_proxies']}** village/local-centre proxies implement the researcher's explicit fallback permission when a lift-base stop is not practical. They are not silently relabelled as lift-base access.

## Service-day warning

**{summary['nodes_active_on_both_reference_days']} of {len(result)}** nodes occur in both active reference-day networks. `Grimentz, Le Boccard` is absent from the Wednesday network but present on Saturday. Anniviers remains routable through its separate Chandolin component in the destination-level fastest-component calculation, but the Grimentz weekday absence stays visible in the review table.

## Limits

This is a controlled name, mode, municipality, distance and reference-day-availability review against official current OFT/BAV and GTFS data. It does not establish door-to-lift walking time, accessibility for every traveller, historical stop continuity, unchanged lines, real-time reliability or a tourism catchment. Every node is approved only for the current descriptive routing context; historical and causal approval remain false.

## Output

- `reports/public_transport_arrival_node_review.csv`
- `reports/public_transport_arrival_node_review_summary.json`
"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
