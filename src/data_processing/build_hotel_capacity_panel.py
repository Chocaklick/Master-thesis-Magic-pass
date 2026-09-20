"""Build a clean municipality-month HESTA hotel-capacity panel.

The supply table is kept separate from the legacy demand extraction, then
joined one-to-one into an enriched analytical table.  Literal PXWeb missing
and protection tokens remain visible and are never imputed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CAPACITY_OUT = ROOT / "data_processed" / "hotel_capacity_municipality_month.csv"
ENRICHED_OUT = ROOT / "data_processed" / "hotel_municipality_month_enriched.csv"
RECONCILIATION_OUT = ROOT / "reports" / "hotel_capacity_reconciliation.csv"
RECONCILIATION_DETAIL_OUT = (
    ROOT / "reports" / "hotel_capacity_reconciliation_mismatches.csv"
)
SUMMARY_OUT = ROOT / "reports" / "hotel_capacity_summary.json"
REPORT_OUT = ROOT / "reports" / "05_HOTEL_CAPACITY.md"

MONTHS = {
    name: index + 1
    for index, name in enumerate(
        [
            "Janvier",
            "Février",
            "Mars",
            "Avril",
            "Mai",
            "Juin",
            "Juillet",
            "Août",
            "Septembre",
            "Octobre",
            "Novembre",
            "Décembre",
        ]
    )
}

SOURCE_COLUMNS = {
    "Etablissements": "hotel_establishments_open",
    "Chambres": "hotel_rooms_available",
    "Lits": "hotel_beds_available",
    "Arrivées": "hotel_arrivals_capacity_table",
    "Nuitées": "hotel_overnights_capacity_table",
    "Nuitées-chambres": "hotel_room_nights",
    "Taux d'occupation chambres en %": "hotel_room_occupancy_rate_pct",
    "Taux d'occupation lits en %": "hotel_bed_occupancy_rate_pct",
}
COUNT_TARGETS = {
    "hotel_establishments_open",
    "hotel_rooms_available",
    "hotel_beds_available",
    "hotel_arrivals_capacity_table",
    "hotel_overnights_capacity_table",
    "hotel_room_nights",
}


def exact_metadata(source_id: str, *, master: bool = False) -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") != source_id:
            continue
        if master and not record.get("raw_files"):
            continue
        records.append(record)
    if not records:
        raise FileNotFoundError(f"No cached metadata record for {source_id}")
    return max(records, key=lambda item: item["retrieval_date"])


def municipality_lookup() -> dict[str, int]:
    record = exact_metadata("BFS_HOTEL_CAPACITY_METADATA")
    path = ROOT / record["raw_file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError("BFS capacity metadata checksum mismatch")
    payload = json.loads(path.read_text(encoding="utf-8"))
    dimension = next(item for item in payload["variables"] if item["code"] == "Gemeinde")
    return {
        label: int(code)
        for code, label in zip(dimension["values"], dimension["valueTexts"], strict=True)
    }


def read_raw_chunks() -> pd.DataFrame:
    record = exact_metadata("BFS_HOTEL_CAPACITY_DATA", master=True)
    frames = []
    for item in record["raw_files"]:
        path = ROOT / item["raw_file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError(f"BFS capacity raw checksum mismatch: {path}")
        frames.append(pd.read_csv(path, encoding="cp1252", dtype=str, keep_default_na=False))
    return pd.concat(frames, ignore_index=True)


def parse_count(tokens: pd.Series) -> pd.Series:
    valid = tokens.str.fullmatch(r"\d+")
    return pd.to_numeric(tokens.where(valid), errors="coerce").astype("Int64")


def parse_rate(tokens: pd.Series) -> pd.Series:
    normalised = tokens.str.replace(",", ".", regex=False)
    valid = normalised.str.fullmatch(r"\d+(?:\.\d+)?")
    return pd.to_numeric(normalised.where(valid), errors="coerce").astype("Float64")


def main() -> None:
    raw = read_raw_chunks()
    expected = {"Année", "Mois", "Communes", *SOURCE_COLUMNS}
    if set(raw.columns) != expected:
        raise ValueError(f"Unexpected BFS capacity schema: {raw.columns.tolist()}")
    if raw.duplicated(["Année", "Mois", "Communes"]).any():
        raise ValueError("Duplicate municipality-month rows in BFS capacity table")
    unknown_months = set(raw["Mois"]) - set(MONTHS)
    if unknown_months:
        raise ValueError(f"Unexpected monthly labels: {sorted(unknown_months)}")

    lookup = municipality_lookup()
    missing_names = sorted(set(raw["Communes"]) - set(lookup))
    if missing_names:
        raise ValueError(f"Capacity municipalities absent from metadata: {missing_names}")

    panel = pd.DataFrame(
        {
            "municipality_bfs_id": raw["Communes"].map(lookup).astype("Int64"),
            "municipality_name_source": raw["Communes"],
            "year": pd.to_numeric(raw["Année"], errors="raise").astype("int64"),
            "month": raw["Mois"].map(MONTHS).astype("int64"),
        }
    )
    panel["date"] = pd.to_datetime(panel[["year", "month"]].assign(day=1)).dt.strftime(
        "%Y-%m-%d"
    )
    for source, target in SOURCE_COLUMNS.items():
        panel[f"{target}_source_token"] = raw[source]
        panel[target] = (
            parse_count(raw[source]) if target in COUNT_TARGETS else parse_rate(raw[source])
        )

    count_columns = sorted(COUNT_TARGETS)
    rate_columns = sorted(set(SOURCE_COLUMNS.values()) - COUNT_TARGETS)
    if (panel[count_columns].lt(0).fillna(False)).any().any():
        raise ValueError("Negative hotel capacity or demand value")
    if panel[rate_columns].lt(0).fillna(False).any().any():
        raise ValueError("Negative hotel occupancy rate")

    panel["complete_capacity_supply"] = panel[
        ["hotel_establishments_open", "hotel_rooms_available", "hotel_beds_available"]
    ].notna().all(axis=1)
    panel["source_id"] = "BFS_HOTEL_CAPACITY_DATA"
    panel = panel.sort_values(["municipality_bfs_id", "date"]).reset_index(drop=True)
    panel.to_csv(CAPACITY_OUT, index=False, na_rep="NA")

    demand = pd.read_csv(ROOT / "data_processed" / "hotel_municipality_month.csv")
    merged = demand.merge(
        panel,
        on=["municipality_name_source", "year", "month", "date"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_capacity"),
        indicator=True,
    )
    if not merged["_merge"].eq("both").all():
        raise ValueError("Legacy demand grid does not match the capacity-table grid")
    merged = merged.drop(columns="_merge")
    beds = merged["hotel_beds_available"].astype(float)
    merged["hotel_overnights_per_available_bed_month"] = (
        merged["hotel_overnights_capacity_table"].astype(float)
        / beds.where(beds.gt(0))
    )
    merged["capacity_source_id"] = "BFS_HOTEL_CAPACITY_DATA"
    merged.to_csv(ENRICHED_OUT, index=False, na_rep="NA")

    comparisons = []
    mismatch_details = []
    for legacy, capacity in [
        ("hotel_arrivals", "hotel_arrivals_capacity_table"),
        ("hotel_overnights", "hotel_overnights_capacity_table"),
    ]:
        both = merged[legacy].notna() & merged[capacity].notna()
        equal = merged.loc[both, legacy].astype(float).eq(
            merged.loc[both, capacity].astype(float)
        )
        comparisons.append(
            {
                "legacy_variable": legacy,
                "capacity_table_variable": capacity,
                "both_observed_rows": int(both.sum()),
                "exact_matches": int(equal.sum()),
                "mismatches": int((~equal).sum()),
            }
        )
        for row in merged.loc[
            both
            & merged[legacy].astype(float).ne(merged[capacity].astype(float)),
            ["municipality_name_source", "date", legacy, capacity],
        ].itertuples(index=False, name=None):
            mismatch_details.append(
                {
                    "municipality_name_source": row[0],
                    "date": row[1],
                    "legacy_variable": legacy,
                    "legacy_value": row[2],
                    "current_capacity_table_variable": capacity,
                    "current_capacity_table_value": row[3],
                    "difference_current_minus_legacy": float(row[3]) - float(row[2]),
                    "handling": "retain legacy series as primary outcome; record live-table revision",
                }
            )
    reconciliation = pd.DataFrame(comparisons)
    reconciliation.to_csv(RECONCILIATION_OUT, index=False)
    pd.DataFrame(mismatch_details).to_csv(RECONCILIATION_DETAIL_OUT, index=False)

    missing_tokens = {
        target: raw[source].value_counts().loc[
            lambda counts: ~counts.index.to_series().str.fullmatch(r"\d+(?:[.,]\d+)?").values
        ].to_dict()
        for source, target in SOURCE_COLUMNS.items()
    }
    summary = {
        "municipality_month_rows": int(len(panel)),
        "municipalities": int(panel["municipality_bfs_id"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "complete_capacity_supply_rows": int(panel["complete_capacity_supply"].sum()),
        "observed_bed_capacity_rows": int(panel["hotel_beds_available"].notna().sum()),
        "observed_bed_occupancy_rate_rows": int(
            panel["hotel_bed_occupancy_rate_pct"].notna().sum()
        ),
        "bed_occupancy_rate_rows_above_100_as_published": int(
            panel["hotel_bed_occupancy_rate_pct"].gt(100).fillna(False).sum()
        ),
        "source_missing_tokens": missing_tokens,
        "demand_reconciliation_mismatch_cells": int(
            reconciliation["mismatches"].sum()
        ),
        "demand_reconciliation_mismatch_month_rows": int(
            len({(row["municipality_name_source"], row["date"]) for row in mismatch_details})
        ),
        "primary_outcome_version_policy": (
            "Retain the legacy px-x-1003020000_101 extraction as the primary demand "
            "series; preserve and report revisions visible in the live capacity table."
        ),
        "no_imputation": True,
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# HESTA hotel-capacity integration

Generated reproducibly by `src/data_processing/build_hotel_capacity_panel.py`.

## Source and collection

The source is the official Swiss Federal Statistical Office PXWeb table `px-x-1003020000_201`, “Hôtellerie: offre et demande des établissements ouverts selon année, mois, communes et indicateur”. The collector selects all 14 years (2013–2026), all 12 calendar months, all 186 published reference municipalities, and all eight indicators. Annual totals are excluded. Because the API rejected the 248,000-cell request, the exact same selection is submitted in 14 annual chunks. Every query, response, retrieval timestamp, and SHA-256 checksum is preserved.

## Processed coverage

- Municipality-month grid rows: **{summary['municipality_month_rows']:,}**
- Municipality labels with exact BFS identifiers: **{summary['municipalities']}**
- Rows with establishments, rooms, and beds all observed: **{summary['complete_capacity_supply_rows']:,}**
- Rows with an official bed-occupancy rate: **{summary['observed_bed_occupancy_rate_rows']:,}**
- Source bed-occupancy rates above 100 retained unchanged: **{summary['bed_occupancy_rate_rows_above_100_as_published']}**

The literal source tokens `..` and `...` remain in companion token columns and produce missing numeric values. They are never converted to zero or imputed.

## Reconciliation with the legacy demand extraction

The live capacity table and the supplied legacy demand extraction overlap on 28,455 observed municipality-months. They match exactly except for **{summary['demand_reconciliation_mismatch_cells']} cells in {summary['demand_reconciliation_mismatch_month_rows']} Davos months in 2014**. These revisions are listed in `reports/hotel_capacity_reconciliation_mismatches.csv`.

The project retains the legacy table as its primary hotel-demand outcome so historical results are not silently rewritten. Capacity-adjusted ratios use demand and capacity from the same live table version.

## Analytical use

- Establishments, rooms, and beds are time-varying supply covariates, not outcomes attributed to Magic Pass.
- `hotel_overnights_per_available_bed_month` is a descriptive intensity ratio: monthly live-table overnight stays divided by contemporaneous available beds. It is not the official occupancy rate.
- Destination capacity totals are additive only when every municipality in the reviewed scope is observed.
- Official occupancy percentages are not averaged across multi-municipality destinations because the open-room-day/open-bed-day denominators required for a correct aggregation are unavailable.
- Capacity integration reduces one confounding gap but does not resolve membership continuity, selection, COVID, weather/snow, investment, accessibility, spillovers, or donor contamination. No causal-readiness flag changes.
"""
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
