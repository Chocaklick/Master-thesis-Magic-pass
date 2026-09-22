"""Build the explicit historical GTFS comparison plan without overstating evidence.

The official archive index was inspected to identify a winter snapshot for every
first Magic Pass exposure year represented in the scheduled-journey context.
Historical feeds are deliberately not treated as compared until their stop and
service content has actually been downloaded and audited.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "public_transport_historical_audit.json"
UNITS = ROOT / "data_processed" / "treatment_destination_units.csv"
NODES = ROOT / "reports" / "public_transport_journey_nodes.csv"
OUTPUT = ROOT / "reports" / "public_transport_historical_audit_plan.csv"
SUMMARY = ROOT / "reports" / "public_transport_historical_audit_summary.json"
REPORT = ROOT / "reports" / "25_PUBLIC_TRANSPORT_HISTORICAL_AUDIT.md"


def exposure_year(season: str) -> int:
    parts = str(season).split("/")
    if len(parts) != 2 or len(parts[1]) != 4:
        raise ValueError(f"Unexpected Magic Pass season: {season}")
    return int(parts[1])


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    anchors = pd.DataFrame(config["anchors"])
    if anchors["timetable_year"].duplicated().any():
        raise ValueError("Historical timetable anchors must be unique by year")

    units = pd.read_csv(UNITS, dtype="string")
    nodes = pd.read_csv(NODES, dtype="string")
    nodes = nodes[nodes["node_role"].eq("destination_component_arrival")].copy()
    units = units[["destination_unit_id", "first_entry_season"]].copy()
    units["first_exposure_winter_timetable_year"] = units["first_entry_season"].map(
        exposure_year
    )
    rows = nodes.merge(units, on="destination_unit_id", how="left", validate="many_to_one")
    if rows["first_entry_season"].isna().any():
        raise ValueError("Every selected destination component must have an entry season")
    rows = rows.merge(
        anchors,
        left_on="first_exposure_winter_timetable_year",
        right_on="timetable_year",
        how="left",
        validate="many_to_one",
    )
    if rows["archive_url"].isna().any():
        missing = sorted(rows.loc[rows["archive_url"].isna(), "timetable_year"].unique())
        raise ValueError(f"Missing historical GTFS anchors: {missing}")

    rows["archive_index_availability_status"] = (
        "official_snapshot_url_identified_in_archive_index"
    )
    rows["historical_feed_downloaded"] = rows["timetable_year"].eq(2026)
    rows["historical_destination_stop_service_compared"] = False
    rows["historical_line_stability_status"] = (
        "not_yet_verified_against_anchor_year_timetables"
    )
    rows["causal_accessibility_feature_approved"] = False
    keep = [
        "destination_unit_id",
        "destination_name",
        "component_resort_id",
        "component_resort_name",
        "selected_stop_id",
        "selected_stop_name",
        "selected_stop_mode_code",
        "selected_stop_mode",
        "first_entry_season",
        "first_exposure_winter_timetable_year",
        "snapshot_build",
        "archive_url",
        "archive_index_availability_status",
        "historical_feed_downloaded",
        "historical_destination_stop_service_compared",
        "historical_line_stability_status",
        "causal_accessibility_feature_approved",
    ]
    rows = rows[keep].sort_values(
        ["first_exposure_winter_timetable_year", "destination_unit_id", "component_resort_id"]
    )
    rows.to_csv(OUTPUT, index=False, lineterminator="\n")

    summary = {
        "archive_index_url": config["archive_index_url"],
        "archive_index_review_date": config["archive_index_review_date"],
        "archive_index_collection_status": config["archive_index_collection_status"],
        "selection_rule": config["selection_rule"],
        "historical_anchor_years": sorted(int(value) for value in anchors["timetable_year"]),
        "destination_units": int(rows["destination_unit_id"].nunique()),
        "destination_component_nodes": int(len(rows)),
        "components_with_official_anchor_url": int(rows["archive_url"].notna().sum()),
        "historical_components_service_compared": int(
            rows["historical_destination_stop_service_compared"].sum()
        ),
        "historical_service_comparison_status": config[
            "historical_service_comparison_status"
        ],
        "causal_accessibility_features_approved": 0,
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    anchor_lines = "\n".join(
        f"- **{int(row.timetable_year)}**: `{row.snapshot_build}` — {row.archive_url}"
        for row in anchors.sort_values("timetable_year").itertuples(index=False)
    )
    report = f"""# Historical public-transport timetable audit

## What has been verified

The official SKI/Open Data Mobility Switzerland archive index was inspected on **{config['archive_index_review_date']}**. A winter GTFS snapshot was found for every first-exposure timetable year represented by the 11 destination units and 15 component arrival nodes in the scheduled-journey context. The deterministic selection rule is: **{config['selection_rule']}**.

{anchor_lines}

Automated caching of the dynamic archive index was attempted but stopped because its `robots.txt` policy disallows the project collector. The reviewed URLs and the failed collection attempt are retained transparently; the restriction was not bypassed.

## What has not been verified

The historical ZIP files for 2018–2025 have not yet been downloaded and routed. Consequently, stop continuity, departure frequency, mode sequence and journey-time changes around each destination's first Magic Pass winter have **not** been measured. Identifying an official archive file is not evidence that a line remained stable.

The winter-2026 scheduled journey measures therefore remain descriptive current context. They are not approved as pre-treatment or causal covariates until the anchor-year feeds are checksum-cached and compared with the same node and routing rules.

## Reproducible audit table

See `reports/public_transport_historical_audit_plan.csv`. It links each selected current component node to its first-exposure winter archive URL and keeps `historical_destination_stop_service_compared` and `causal_accessibility_feature_approved` false.
"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
