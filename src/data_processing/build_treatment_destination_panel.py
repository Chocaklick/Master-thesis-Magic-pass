"""Build reviewed destination units and a diagnostic municipality outcome panel.

The script keeps three concepts separate:

* a resort point's containing municipality (geographic fact);
* a reviewed destination-to-municipality outcome scope (analytical choice); and
* a causal treatment (not approved at this checkpoint).

No row produced here is promoted to causal-ready.  The treatment indicator in
the monthly panel explicitly assumes continuity after a documented entry unless
an exit is documented.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "treatment_destination_review.json"
RESORTS = ROOT / "data_processed" / "resort_master.csv"
POINTS = ROOT / "data_processed" / "resort_point_municipality.csv"
HISTORY = ROOT / "data_processed" / "magic_pass_membership_history.csv"
HOTEL = ROOT / "data_processed" / "hotel_municipality_month_enriched.csv"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"

RESORT_CROSSWALK_OUT = ROOT / "data_processed" / "resort_municipality_crosswalk.csv"
UNIT_OUT = ROOT / "data_processed" / "treatment_destination_units.csv"
UNIT_MUNICIPALITY_OUT = ROOT / "data_processed" / "treatment_destination_municipality.csv"
EVENT_OUT = ROOT / "data_processed" / "municipality_treatment_events.csv"
PANEL_OUT = ROOT / "data_processed" / "destination_month_panel.csv"
REVIEW_OUT = ROOT / "reports" / "destination_unit_review.csv"
SUMMARY_OUT = ROOT / "reports" / "treatment_panel_summary.json"
REVIEW_MD_OUT = ROOT / "reports" / "04_DESTINATION_UNIT_REVIEW.md"


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def load_bfs_hotel_universe() -> dict[int, str]:
    paths = [
        path
        for path in sorted(EVIDENCE_DIR.glob("BFS_HOTEL_METADATA_*.json"))
        if not path.name.endswith(".metadata.json")
    ]
    if not paths:
        raise FileNotFoundError("No cached BFS hotel metadata response was found")
    payload = json.loads(paths[-1].read_text(encoding="utf-8"))
    dimension = next(item for item in payload["variables"] if item["code"] == "Gemeinde")
    return {
        int(code): label
        for code, label in zip(dimension["values"], dimension["valueTexts"])
    }


def analytical_anchor(entry_season: str) -> pd.Timestamp:
    first_year = int(str(entry_season).split("/")[0])
    month = 11 if first_year == 2017 else 5
    return pd.Timestamp(first_year, month, 1)


def event_anchor_precision(entry_season: str) -> str:
    first_year = int(str(entry_season).split("/")[0])
    if first_year == 2017:
        return "exact_product_validity_date"
    if first_year == 2019:
        return "official_validity_month"
    if first_year == 2025:
        return "exact_operator_membership_date"
    return "analytical_month_anchor"


def complete_weighted_sum(group: pd.DataFrame, column: str, expected: int) -> float:
    values = group[column]
    if values.notna().sum() != expected:
        return np.nan
    return float((values * group["municipality_weight"]).sum())


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    units = config["units"]
    resorts = pd.read_csv(RESORTS, dtype="string")
    points = pd.read_csv(POINTS, dtype="string")
    history = pd.read_csv(HISTORY, dtype="string", keep_default_na=False)
    hotel = pd.read_csv(HOTEL)
    hotel["date"] = pd.to_datetime(hotel["date"], errors="raise")
    bfs_hotels = load_bfs_hotel_universe()

    unit_ids = [unit["destination_unit_id"] for unit in units]
    if len(unit_ids) != len(set(unit_ids)):
        raise ValueError("destination_unit_id values must be unique")

    resort_ids = set(resorts["resort_id"].dropna())
    reviewed_resort_ids: list[str] = []
    for unit in units:
        reviewed_resort_ids.extend(unit["component_resort_ids"])
    unknown_resorts = sorted(set(reviewed_resort_ids) - resort_ids)
    if unknown_resorts:
        raise ValueError(f"Unknown component resort IDs: {unknown_resorts}")
    if len(reviewed_resort_ids) != len(set(reviewed_resort_ids)):
        raise ValueError("A resort listing is assigned to more than one destination unit")

    hotel_names = set(hotel["municipality_name_source"].dropna())
    municipality_rows: list[dict] = []
    resort_review: dict[str, dict] = {}
    for unit in units:
        municipalities = unit["municipalities"]
        if len({item["bfs_id"] for item in municipalities}) != len(municipalities):
            raise ValueError(f"Duplicate municipality in {unit['destination_unit_id']}")
        for item in municipalities:
            if item["weight"] != 1.0:
                raise ValueError("Count outcomes require additive weight 1.0")
            if bfs_hotels.get(item["bfs_id"]) != item["name"]:
                raise ValueError(
                    f"BFS municipality mismatch for {unit['destination_unit_id']}: {item}"
                )
            if item["name"] not in hotel_names:
                raise ValueError(f"Hotel municipality missing from panel: {item['name']}")
            municipality_rows.append(
                {
                    "destination_unit_id": unit["destination_unit_id"],
                    "destination_name": unit["destination_name"],
                    "municipality_bfs_id": item["bfs_id"],
                    "municipality_name": item["name"],
                    "municipality_weight": item["weight"],
                    "weighting_scheme": "additive_municipality_total",
                    "scope_review_status": unit["scope_review_status"],
                    "eligible_for_reviewed_outcome_panel": unit[
                        "eligible_for_reviewed_outcome_panel"
                    ],
                    "causal_exposure_approved": False,
                    "source_ids": "|".join(unit["scope_source_ids"]),
                }
            )
        for resort_id in unit["component_resort_ids"]:
            resort_review[resort_id] = unit

    unit_municipalities = pd.DataFrame(municipality_rows)
    unit_municipalities["municipality_bfs_id"] = unit_municipalities[
        "municipality_bfs_id"
    ].astype("Int64")
    unit_municipalities.to_csv(UNIT_MUNICIPALITY_OUT, index=False)

    point_columns = [
        "resort_id",
        "point_longitude",
        "point_latitude",
        "point_municipality_bfs_id",
        "point_municipality_name",
        "point_municipality_canton",
        "boundary_reference_year",
        "selection_status",
        "relationship_type",
        "assignment_method",
        "assignment_confidence",
        "bfs_hotel_universe",
        "bfs_hotel_municipality_name",
        "source_id",
        "query_source_id",
        "source_sha256",
    ]
    crosswalk = resorts[
        ["resort_id", "resort_name_canonical", "cluster_id", "identity_status"]
    ].merge(points[point_columns], on="resort_id", validate="one_to_one")
    crosswalk["reviewed_destination_unit_id"] = crosswalk["resort_id"].map(
        lambda resort_id: (
            resort_review[resort_id]["destination_unit_id"]
            if resort_id in resort_review
            else ""
        )
    )
    crosswalk["outcome_scope_review_status"] = crosswalk["resort_id"].map(
        lambda resort_id: (
            resort_review[resort_id]["scope_review_status"]
            if resort_id in resort_review
            else "not_reviewed"
        )
    )
    crosswalk["eligible_for_reviewed_outcome_panel"] = crosswalk["resort_id"].map(
        lambda resort_id: bool(
            resort_id in resort_review
            and resort_review[resort_id]["eligible_for_reviewed_outcome_panel"]
        )
    )
    crosswalk["outcome_allocation_weight"] = np.nan
    crosswalk["causal_exposure_approved"] = False
    crosswalk["causal_exposure_note"] = (
        "Point containment alone is not a tourism catchment; use the reviewed "
        "destination-municipality table for outcome aggregation."
    )
    crosswalk.sort_values("resort_id").to_csv(RESORT_CROSSWALK_OUT, index=False)

    entry_history = history[history["event_type"].eq("base_pass_entry")].copy()
    event_rows: list[dict] = []
    unit_rows: list[dict] = []
    unit_by_id = {unit["destination_unit_id"]: unit for unit in units}
    for unit in units:
        matched_events: list[pd.Series] = []
        for resort_id, label in zip(
            unit["component_resort_ids"], unit["entry_labels"], strict=True
        ):
            matches = entry_history[
                entry_history["candidate_resort_id"].eq(resort_id)
                & entry_history["source_resort_name"].eq(label)
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one base entry for {unit['destination_unit_id']} / "
                    f"{resort_id} / {label}; found {len(matches)}"
                )
            row = matches.iloc[0]
            matched_events.append(row)
            anchor = analytical_anchor(row["entry_season"])
            event_rows.append(
                {
                    "destination_unit_id": unit["destination_unit_id"],
                    "destination_name": unit["destination_name"],
                    "event_id": row["event_id"],
                    "event_type": "base_pass_entry",
                    "source_resort_name": row["source_resort_name"],
                    "candidate_resort_id": row["candidate_resort_id"],
                    "entry_season": row["entry_season"],
                    "effective_month": anchor.date().isoformat(),
                    "effective_month_precision": event_anchor_precision(row["entry_season"]),
                    "component_count_change": 1,
                    "source_id": row["source_id"],
                    "source_date": row["source_date"],
                    "scope_review_status": unit["scope_review_status"],
                    "eligible_for_reviewed_outcome_panel": unit[
                        "eligible_for_reviewed_outcome_panel"
                    ],
                    "treatment_ready": False,
                }
            )
        if unit["exit_date"]:
            component_ids = set(unit["component_resort_ids"])
            exits = history[
                history["event_type"].eq("base_pass_exit")
                & history["candidate_resort_id"].isin(component_ids)
                & history["exit_date"].eq(unit["exit_date"])
            ]
            if len(exits) != 1:
                raise ValueError(
                    f"Expected one reviewed exit for {unit['destination_unit_id']}"
                )
            row = exits.iloc[0]
            event_rows.append(
                {
                    "destination_unit_id": unit["destination_unit_id"],
                    "destination_name": unit["destination_name"],
                    "event_id": row["event_id"],
                    "event_type": "base_pass_exit",
                    "source_resort_name": row["source_resort_name"],
                    "candidate_resort_id": row["candidate_resort_id"],
                    "entry_season": "",
                    "effective_month": pd.Timestamp(unit["exit_date"])
                    .to_period("M")
                    .to_timestamp()
                    .date()
                    .isoformat(),
                    "effective_month_precision": "documented_last_active_month",
                    "component_count_change": -len(matched_events),
                    "source_id": row["source_id"],
                    "source_date": row["source_date"],
                    "scope_review_status": unit["scope_review_status"],
                    "eligible_for_reviewed_outcome_panel": unit[
                        "eligible_for_reviewed_outcome_panel"
                    ],
                    "treatment_ready": False,
                }
            )
        anchors = [analytical_anchor(row["entry_season"]) for row in matched_events]
        unit_rows.append(
            {
                "destination_unit_id": unit["destination_unit_id"],
                "destination_name": unit["destination_name"],
                "component_resort_ids": "|".join(unit["component_resort_ids"]),
                "entry_labels": "|".join(unit["entry_labels"]),
                "component_resort_count": len(unit["component_resort_ids"]),
                "entry_event_count": len(matched_events),
                "municipality_count": len(unit["municipalities"]),
                "municipality_bfs_ids": "|".join(
                    str(item["bfs_id"]) for item in unit["municipalities"]
                ),
                "municipality_names": "|".join(
                    item["name"] for item in unit["municipalities"]
                ),
                "first_entry_season": min(row["entry_season"] for row in matched_events),
                "first_analysis_anchor": min(anchors).date().isoformat(),
                "anchor_precision": unit["anchor_precision"],
                "documented_exit_date": unit["exit_date"] or "",
                "scope_review_status": unit["scope_review_status"],
                "eligible_for_reviewed_outcome_panel": unit[
                    "eligible_for_reviewed_outcome_panel"
                ],
                "required_scope": unit["required_scope"],
                "missing_outcome_scope": unit["missing_outcome_scope"],
                "weighting_scheme": "additive_municipality_total",
                "scope_source_ids": "|".join(unit["scope_source_ids"]),
                "membership_continuity_status": "not_fully_audited",
                "causal_treatment_unit_approved": False,
                "causal_blocker": (
                    "Historical continuity, untreated-control status, confounding, and "
                    "spillovers are not all approved."
                ),
                "review_note": unit["review_note"],
            }
        )

    events = pd.DataFrame(event_rows).sort_values(
        ["destination_unit_id", "effective_month", "event_type", "source_resort_name"]
    )
    events.to_csv(EVENT_OUT, index=False)
    unit_frame = pd.DataFrame(unit_rows).sort_values("destination_unit_id")

    panel_rows: list[dict] = []
    approved = unit_municipalities[
        as_bool(unit_municipalities["eligible_for_reviewed_outcome_panel"])
    ]
    outcome_columns = [
        "hotel_overnights",
        "hotel_arrivals",
        "domestic_overnights",
        "foreign_overnights",
    ]
    capacity_sum_columns = [
        "hotel_establishments_open",
        "hotel_rooms_available",
        "hotel_beds_available",
        "hotel_overnights_capacity_table",
    ]
    for destination_unit_id, mappings in approved.groupby(
        "destination_unit_id", observed=True
    ):
        unit = unit_by_id[destination_unit_id]
        expected = len(mappings)
        scoped = hotel.merge(
            mappings[["municipality_name", "municipality_weight"]],
            left_on="municipality_name_source",
            right_on="municipality_name",
            validate="many_to_one",
        )
        for date, group in scoped.groupby("date", observed=True):
            row = {
                "destination_unit_id": destination_unit_id,
                "destination_name": unit["destination_name"],
                "date": date,
                "year": date.year,
                "month": date.month,
                "municipality_count_expected": expected,
                "municipalities_observed_hotel_overnights": int(
                    group["hotel_overnights"].notna().sum()
                ),
                "complete_outcome_scope": bool(
                    group["hotel_overnights"].notna().sum() == expected
                ),
                "municipalities_observed_hotel_beds_available": int(
                    group["hotel_beds_available"].notna().sum()
                ),
                "complete_capacity_scope": bool(
                    group[
                        [
                            "hotel_establishments_open",
                            "hotel_rooms_available",
                            "hotel_beds_available",
                        ]
                    ]
                    .notna()
                    .all(axis=1)
                    .sum()
                    == expected
                ),
                "first_analysis_anchor": pd.Timestamp(unit["analysis_anchor"]),
                "anchor_precision": unit["anchor_precision"],
                "membership_continuity_assumed": True,
                "causal_ready": False,
            }
            for column in outcome_columns:
                row[column] = complete_weighted_sum(group, column, expected)
            for column in capacity_sum_columns:
                row[column] = complete_weighted_sum(group, column, expected)
            if expected == 1:
                row["hotel_room_occupancy_rate_pct"] = complete_weighted_sum(
                    group, "hotel_room_occupancy_rate_pct", expected
                )
                row["hotel_bed_occupancy_rate_pct"] = complete_weighted_sum(
                    group, "hotel_bed_occupancy_rate_pct", expected
                )
                row["occupancy_rate_aggregation_status"] = (
                    "official_source_value_single_municipality"
                )
            else:
                row["hotel_room_occupancy_rate_pct"] = np.nan
                row["hotel_bed_occupancy_rate_pct"] = np.nan
                row["occupancy_rate_aggregation_status"] = (
                    "not_aggregated_across_multiple_municipalities"
                )
            panel_rows.append(row)

    panel = pd.DataFrame(panel_rows)
    event_months = events.copy()
    event_months["effective_month"] = pd.to_datetime(event_months["effective_month"])
    panel["assumed_active_component_count"] = 0
    for destination_unit_id, destination_events in event_months.groupby(
        "destination_unit_id", observed=True
    ):
        if destination_unit_id not in set(panel["destination_unit_id"]):
            continue
        selector = panel["destination_unit_id"].eq(destination_unit_id)
        dates = panel.loc[selector, "date"]
        counts = pd.Series(0, index=dates.index, dtype="int64")
        for event in destination_events.itertuples(index=False):
            if event.event_type == "base_pass_entry":
                counts.loc[dates >= event.effective_month] += int(event.component_count_change)
            else:
                exit_month = event.effective_month
                counts.loc[dates > exit_month] += int(event.component_count_change)
        if (counts < 0).any():
            raise ValueError(f"Negative assumed component count for {destination_unit_id}")
        panel.loc[selector, "assumed_active_component_count"] = counts

    panel["assumed_base_member"] = panel["assumed_active_component_count"].gt(0)
    panel["post_first_entry"] = panel["date"].ge(panel["first_analysis_anchor"])
    panel["event_time_months"] = (
        (panel["date"].dt.year - panel["first_analysis_anchor"].dt.year) * 12
        + panel["date"].dt.month
        - panel["first_analysis_anchor"].dt.month
    )
    panel["log_overnights"] = np.log1p(panel["hotel_overnights"])
    panel["hotel_overnights_per_available_bed_month"] = (
        panel["hotel_overnights_capacity_table"]
        / panel["hotel_beds_available"].where(panel["hotel_beds_available"].gt(0))
    )
    panel["treatment_status_basis"] = (
        "entry_plus_no_exit_continuity_assumption; documented exits override after last active month"
    )
    panel["outcome_scope_status"] = panel["destination_unit_id"].map(
        {unit["destination_unit_id"]: unit["scope_review_status"] for unit in units}
    )
    panel["source_id"] = "DERIVED_REVIEWED_DESTINATION_PANEL"
    panel["capacity_source_id"] = "BFS_HOTEL_CAPACITY_DATA"
    panel = panel.sort_values(["destination_unit_id", "date"]).reset_index(drop=True)
    panel["date"] = panel["date"].dt.date.astype(str)
    panel["first_analysis_anchor"] = panel["first_analysis_anchor"].dt.date.astype(str)
    panel.to_csv(PANEL_OUT, index=False)

    panel_dates = pd.to_datetime(panel["date"])
    panel_anchors = pd.to_datetime(panel["first_analysis_anchor"])
    observed = panel["hotel_overnights"].notna()
    active = panel["assumed_base_member"]
    coverage_rows: list[dict] = []
    for destination_unit_id, group in panel.assign(
        _date=panel_dates, _anchor=panel_anchors, _observed=observed, _active=active
    ).groupby("destination_unit_id", observed=True):
        pre = int((group["_observed"] & (group["_date"] < group["_anchor"])).sum())
        active_post = int(
            (
                group["_observed"]
                & (group["_date"] >= group["_anchor"])
                & group["_active"]
            ).sum()
        )
        coverage_rows.append(
            {
                "destination_unit_id": destination_unit_id,
                "observed_pre_months": pre,
                "observed_active_post_months_assumption": active_post,
                "has_24_observed_pre_months": pre >= 24,
                "has_36_observed_pre_months": pre >= 36,
                "has_24_active_post_months_assumption": active_post >= 24,
                "has_36_active_post_months_assumption": active_post >= 36,
            }
        )
    coverage = pd.DataFrame(coverage_rows)
    unit_frame = unit_frame.merge(coverage, on="destination_unit_id", how="left", validate="one_to_one")
    for column in [
        "observed_pre_months",
        "observed_active_post_months_assumption",
    ]:
        unit_frame[column] = unit_frame[column].astype("Int64")
    for column in [
        "has_24_observed_pre_months",
        "has_36_observed_pre_months",
        "has_24_active_post_months_assumption",
        "has_36_active_post_months_assumption",
    ]:
        unit_frame[column] = unit_frame[column].eq(True)
    unit_frame.to_csv(UNIT_OUT, index=False)
    unit_frame.to_csv(REVIEW_OUT, index=False)

    usable_24 = (
        as_bool(unit_frame["eligible_for_reviewed_outcome_panel"])
        & as_bool(unit_frame["has_24_observed_pre_months"])
        & as_bool(unit_frame["has_24_active_post_months_assumption"])
    )
    usable_36 = (
        as_bool(unit_frame["eligible_for_reviewed_outcome_panel"])
        & as_bool(unit_frame["has_36_observed_pre_months"])
        & as_bool(unit_frame["has_36_active_post_months_assumption"])
    )
    summary = {
        "reviewed_destination_units": int(len(unit_frame)),
        "reviewed_component_entry_events": int(
            events["event_type"].eq("base_pass_entry").sum()
        ),
        "destination_units_in_outcome_panel": int(
            as_bool(unit_frame["eligible_for_reviewed_outcome_panel"]).sum()
        ),
        "destination_units_excluded_for_incomplete_scope": int(
            (~as_bool(unit_frame["eligible_for_reviewed_outcome_panel"])).sum()
        ),
        "destination_month_rows": int(len(panel)),
        "observed_destination_month_outcomes": int(panel["hotel_overnights"].notna().sum()),
        "complete_destination_month_capacity_rows": int(
            panel["complete_capacity_scope"].sum()
        ),
        "destination_month_rows_with_observed_bed_capacity": int(
            panel["hotel_beds_available"].notna().sum()
        ),
        "units_with_24_pre_and_24_active_post_months_assumption": int(usable_24.sum()),
        "units_with_36_pre_and_36_active_post_months_assumption": int(usable_36.sum()),
        "causal_treatment_units_approved": 0,
        "causal_ready_panel_rows": 0,
        "continuity_assumption": (
            "Entry is carried forward until a documented exit. This is a diagnostic "
            "coding assumption and has not been accepted for causal estimation."
        ),
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    table_rows = []
    for row in unit_frame.itertuples(index=False):
        pre = "—" if pd.isna(row.observed_pre_months) else str(int(row.observed_pre_months))
        post = (
            "—"
            if pd.isna(row.observed_active_post_months_assumption)
            else str(int(row.observed_active_post_months_assumption))
        )
        table_rows.append(
            "| "
            + " | ".join(
                [
                    row.destination_name,
                    str(row.entry_event_count),
                    row.municipality_names.replace("|", "<br>"),
                    row.scope_review_status,
                    pre,
                    post,
                ]
            )
            + " |"
        )
    report = f"""# Destination-unit and municipality outcome review

Generated reproducibly by `src/data_processing/build_treatment_destination_panel.py` from the versioned review configuration and cached official evidence.

## Decision

The 18 candidate Magic Pass entry/outcome links represent **{summary['reviewed_destination_units']} reviewed destination units**, not 18 independent treatments. **{summary['destination_units_in_outcome_panel']} units** have an explicit municipality outcome scope and enter the diagnostic panel. **{summary['destination_units_excluded_for_incomplete_scope']} composite units** are excluded because the supplied OFS hotel panel does not cover their complete reviewed geography.

This review approves an outcome aggregation, not a causal exposure. Every destination and month remains `causal_ready = false` until membership continuity, confounding, spillovers, and untreated controls are audited.

## Unit decisions

| Destination unit | Entry events | Outcome municipalities | Review status | Observed pre months | Active post months under assumption |
|---|---:|---|---|---:|---:|
{chr(10).join(table_rows)}

## Aggregation rules

- Resort point containment remains a geographic fact only. It is copied to `data_processed/resort_municipality_crosswalk.csv` with causal exposure set to false.
- Municipality hotel-night counts are additive. Each included municipality has weight 1.0; weights are not normalised into shares.
- A destination-month aggregate is missing unless every municipality in its approved scope has an observed value.
- Establishments, rooms and beds are summed across the reviewed municipal scope only when every municipality is observed. `hotel_overnights_per_available_bed_month` uses the contemporaneous demand and bed capacity from the same live HESTA table.
- Official occupancy percentages are retained for single-municipality destinations only. They are not averaged across multi-municipality destinations because the required open-bed-day denominator is unavailable.
- Anniviers and Espace Dent Blanche collapse multiple same-season resort labels to one municipal outcome. Reichenbach im Kandertal has one municipal outcome with a later treatment-intensity increment when Kiental enters.
- Meiringen-Hasliberg sums Hasliberg and Meiringen. Villars-Gryon-Les Diablerets, Sainte-Croix / Les Rasses, and Bergbahnen Destination Gstaad are excluded because the hotel panel only observes part of their reviewed composite scope.

## Timing and remaining gate

The 2017-11 anchor is the documented first-pass validity date. Later 1 May values are monthly analytical anchors unless the operator documents the exact date. The diagnostic panel carries entry forward until a documented exit; Crans-Montana is switched off after 2020-04. This continuity convention is an assumption, not evidence.

Under that assumption, **{summary['units_with_24_pre_and_24_active_post_months_assumption']} units** have at least 24 observed pre and active-post months and **{summary['units_with_36_pre_and_36_active_post_months_assumption']}** have at least 36. These are coverage counts only. The causal-treatment count remains **zero**.
"""
    REVIEW_MD_OUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
