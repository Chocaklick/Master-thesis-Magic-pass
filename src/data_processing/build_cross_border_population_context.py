"""Build qualified 2021 cross-border population context for Path C.

The official Eurostat census grid provides one internally consistent reference
year on both sides of Switzerland's borders.  Population is assigned to the
centre of each 1 km cell and summed inside the same predeclared straight-line
radii as the existing Swiss municipality-point diagnostic.  The two products
remain separate because their reference years and spatial allocation differ.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
SOURCE_CONFIG_PATH = ROOT / "config" / "eurostat_census_grid_2021.json"
CLUSTER_FEATURES_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
REGIONAL_GRID_OUTPUT = ROOT / "data_processed" / "eurostat_population_grid_2021_swiss_region.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_cross_border_population_context.csv"
CANDIDATE_AUDIT_OUTPUT = ROOT / "reports" / "cross_border_population_candidate_summary.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "cross_border_population_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "29_CROSS_BORDER_POPULATION_CONTEXT.md"
SOURCE_ID = "EUROSTAT_CENSUS_GRID_2021_V3"
DOCUMENTATION_SOURCE_ID = "EUROSTAT_CENSUS_GRID_2021_V3_README"
INTERPRETATION = (
    "eurostat_2021_one_km_population_context_not_travel_time_or_destination_catchment"
)
GRID_ID_PATTERN = re.compile(r"^CRS3035RES1000mN(?P<y>\d+)E(?P<x>\d+)$")
CHUNK_SIZE = 250_000


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact_metadata(source_id: str) -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if len(records) != 1:
        raise ValueError(f"Expected one cached {source_id} record, found {len(records)}")
    record = records[0]
    raw = ROOT / record["raw_file"]
    if not raw.exists() or sha256_file(raw) != record["sha256"]:
        raise RuntimeError(f"Cached source checksum failure: {source_id}")
    return record


def load_cluster_coordinates() -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    clusters = pd.read_csv(CLUSTER_FEATURES_PATH)
    required = {
        "cluster_id",
        "cluster_display_name",
        "candidate_for_path_c",
        "longitude_median",
        "latitude_median",
    }
    if not required.issubset(clusters.columns):
        raise ValueError(f"Missing cluster columns: {sorted(required - set(clusters.columns))}")
    if len(clusters) != 162 or not clusters["cluster_id"].is_unique:
        raise ValueError("Expected 162 unique linked Path C clusters")
    if clusters[["longitude_median", "latitude_median"]].isna().any().any():
        raise ValueError("Every linked cluster must have a median coordinate")
    transformer = Transformer.from_crs(4326, 3035, always_xy=True)
    coordinates = [
        transformer.transform(longitude, latitude)
        for longitude, latitude in zip(
            clusters["longitude_median"], clusters["latitude_median"], strict=True
        )
    ]
    cluster_x = np.array([value[0] for value in coordinates], dtype=float)
    cluster_y = np.array([value[1] for value in coordinates], dtype=float)
    return clusters, cluster_x, cluster_y


def minimum_distance_squared(
    cell_x: np.ndarray,
    cell_y: np.ndarray,
    cluster_x: np.ndarray,
    cluster_y: np.ndarray,
) -> np.ndarray:
    minimum = np.full(len(cell_x), np.inf)
    for x, y in zip(cluster_x, cluster_y, strict=True):
        minimum = np.minimum(minimum, np.square(cell_x - x) + np.square(cell_y - y))
    return minimum


def load_relevant_grid(
    raw_path: Path,
    cluster_x: np.ndarray,
    cluster_y: np.ndarray,
    maximum_radius_km: float,
    unavailable_codes: set[int],
) -> tuple[pd.DataFrame, dict]:
    tolerance_m = 1000 / math.sqrt(2)
    search_m = maximum_radius_km * 1000 + tolerance_m
    bounds = (
        float(cluster_x.min() - search_m),
        float(cluster_x.max() + search_m),
        float(cluster_y.min() - search_m),
        float(cluster_y.max() + search_m),
    )
    selected = []
    source_rows = 0
    allocated_rows = 0
    unallocated_rows = 0
    unallocated_population = 0
    unavailable_total_rows = 0
    invalid_negative_values: set[int] = set()
    for chunk in pd.read_csv(
        raw_path,
        usecols=["GRD_ID", "T", "POPULATED", "CNTR_ID"],
        dtype={"GRD_ID": "string", "T": "int64", "POPULATED": "int64", "CNTR_ID": "string"},
        chunksize=CHUNK_SIZE,
    ):
        source_rows += len(chunk)
        unavailable_total_rows += int(chunk["T"].isin(unavailable_codes).sum())
        invalid_negative_values.update(
            int(value)
            for value in chunk.loc[chunk["T"].lt(0), "T"].unique()
            if int(value) not in unavailable_codes
        )
        coordinates = chunk["GRD_ID"].str.extract(GRID_ID_PATTERN)
        allocated = coordinates.notna().all(axis=1)
        allocated_rows += int(allocated.sum())
        unallocated_rows += int((~allocated).sum())
        unallocated_population += int(chunk.loc[~allocated & chunk["T"].ge(0), "T"].sum())
        if not allocated.any():
            continue
        allocated_chunk = chunk.loc[allocated].copy()
        allocated_coordinates = coordinates.loc[allocated].astype("int64")
        allocated_chunk["cell_lower_left_x_3035"] = allocated_coordinates["x"].to_numpy()
        allocated_chunk["cell_lower_left_y_3035"] = allocated_coordinates["y"].to_numpy()
        allocated_chunk["cell_centroid_x_3035"] = (
            allocated_chunk["cell_lower_left_x_3035"] + 500
        )
        allocated_chunk["cell_centroid_y_3035"] = (
            allocated_chunk["cell_lower_left_y_3035"] + 500
        )
        in_bounds = (
            allocated_chunk["cell_centroid_x_3035"].between(bounds[0], bounds[1])
            & allocated_chunk["cell_centroid_y_3035"].between(bounds[2], bounds[3])
        )
        allocated_chunk = allocated_chunk.loc[in_bounds].copy()
        if allocated_chunk.empty:
            continue
        distance_squared = minimum_distance_squared(
            allocated_chunk["cell_centroid_x_3035"].to_numpy(dtype=float),
            allocated_chunk["cell_centroid_y_3035"].to_numpy(dtype=float),
            cluster_x,
            cluster_y,
        )
        close = distance_squared <= search_m**2
        allocated_chunk = allocated_chunk.loc[close].copy()
        allocated_chunk["minimum_distance_to_path_c_cluster_km"] = (
            np.sqrt(distance_squared[close]) / 1000
        )
        selected.append(allocated_chunk)
    if invalid_negative_values:
        raise ValueError(f"Unexpected negative total-population codes: {sorted(invalid_negative_values)}")
    grid = pd.concat(selected, ignore_index=True)
    if not grid["GRD_ID"].is_unique:
        duplicates = grid.loc[grid["GRD_ID"].duplicated(False), "GRD_ID"].tolist()[:10]
        raise ValueError(f"Duplicate grid identifiers in regional extract: {duplicates}")
    grid = grid.rename(
        columns={
            "GRD_ID": "grid_cell_id",
            "T": "total_population_2021",
            "POPULATED": "populated_flag",
            "CNTR_ID": "reporting_country_codes",
        }
    )
    contains_ch = grid["reporting_country_codes"].str.split("-").map(lambda x: "CH" in x)
    grid["country_scope_category"] = np.select(
        [grid["reporting_country_codes"].eq("CH"), contains_ch],
        ["switzerland_only", "switzerland_foreign_mixed"],
        default="foreign_only",
    )
    grid["total_population_observation_status"] = np.where(
        grid["total_population_2021"].ge(0),
        "observed",
        np.where(
            grid["total_population_2021"].eq(-8888),
            "unavailable_confidentiality",
            "unavailable_other_reason",
        ),
    )
    grid["population_reference_year"] = 2021
    grid["grid_crs"] = "EPSG:3035"
    grid["grid_resolution_m"] = 1000
    grid["population_source_id"] = SOURCE_ID
    grid = grid.sort_values("grid_cell_id").reset_index(drop=True)
    summary = {
        "source_rows": int(source_rows),
        "spatially_allocated_rows": int(allocated_rows),
        "unallocated_rows_excluded": int(unallocated_rows),
        "observed_unallocated_population_excluded": int(unallocated_population),
        "source_rows_with_unavailable_total_population": int(unavailable_total_rows),
        "regional_cells_within_maximum_radius_plus_centroid_tolerance": int(len(grid)),
        "regional_cells_with_observed_total_population": int(
            grid["total_population_2021"].ge(0).sum()
        ),
        "regional_cells_with_unavailable_total_population": int(
            grid["total_population_2021"].lt(0).sum()
        ),
    }
    return grid, summary


def country_codes(series: pd.Series) -> str:
    codes = {
        code
        for value in series.dropna().astype(str)
        for code in value.split("-")
        if code
    }
    return "|".join(sorted(codes))


def build_cluster_context(
    clusters: pd.DataFrame,
    cluster_x: np.ndarray,
    cluster_y: np.ndarray,
    grid: pd.DataFrame,
    radii: list[int],
) -> pd.DataFrame:
    cell_x = grid["cell_centroid_x_3035"].to_numpy(dtype=float)
    cell_y = grid["cell_centroid_y_3035"].to_numpy(dtype=float)
    population = grid["total_population_2021"].to_numpy(dtype=np.int64)
    observed = population >= 0
    scope = grid["country_scope_category"].to_numpy(dtype=str)
    rows = []
    for cluster, x, y in zip(clusters.itertuples(index=False), cluster_x, cluster_y, strict=True):
        distances_km = np.hypot(cell_x - x, cell_y - y) / 1000
        row = {
            "cluster_id": cluster.cluster_id,
            "cluster_display_name": cluster.cluster_display_name,
            "candidate_for_path_c": str(cluster.candidate_for_path_c).lower() == "true",
            "cluster_location_longitude": float(cluster.longitude_median),
            "cluster_location_latitude": float(cluster.latitude_median),
            "cluster_location_x_3035": float(x),
            "cluster_location_y_3035": float(y),
        }
        for radius in radii:
            within = distances_km <= radius
            usable = within & observed
            positive = usable & (population > 0)
            total = int(population[usable].sum())
            parts = {}
            for category in [
                "switzerland_only",
                "foreign_only",
                "switzerland_foreign_mixed",
            ]:
                parts[category] = int(population[usable & (scope == category)].sum())
            if total != sum(parts.values()):
                raise ValueError(f"Country-scope partition failed for {cluster.cluster_id}, {radius} km")
            prefix = f"within_{radius}km"
            row[f"eurostat_population_2021_{prefix}_cell_centroid"] = total
            row[f"eurostat_switzerland_only_population_2021_{prefix}_cell_centroid"] = parts[
                "switzerland_only"
            ]
            row[f"eurostat_foreign_only_population_2021_{prefix}_cell_centroid"] = parts[
                "foreign_only"
            ]
            row[f"eurostat_ch_foreign_mixed_population_2021_{prefix}_cell_centroid"] = parts[
                "switzerland_foreign_mixed"
            ]
            row[f"eurostat_foreign_only_share_of_observed_population_{prefix}"] = (
                parts["foreign_only"] / total if total > 0 else np.nan
            )
            row[f"eurostat_population_grid_cells_{prefix}"] = int(within.sum())
            row[f"eurostat_total_population_unavailable_cells_{prefix}"] = int(
                (within & ~observed).sum()
            )
            row[f"eurostat_populated_cells_with_unavailable_total_{prefix}"] = int(
                (within & ~observed & grid["populated_flag"].eq(1).to_numpy()).sum()
            )
            row[f"eurostat_positive_population_country_codes_{prefix}"] = country_codes(
                grid.loc[positive, "reporting_country_codes"]
            )
        maximum_missing = row[
            f"eurostat_total_population_unavailable_cells_within_{max(radii)}km"
        ]
        row.update(
            {
                "cross_border_population_context_status": (
                    "complete_observed_total_population_grid_cells"
                    if maximum_missing == 0
                    else "one_or_more_total_population_grid_cells_unavailable"
                ),
                "population_reference_year": 2021,
                "population_grid_release_date": "2026-05-30",
                "population_grid_crs": "EPSG:3035",
                "population_grid_resolution_m": 1000,
                "population_grid_cell_location_method": "grid_cell_centroid",
                "grid_cell_centroid_maximum_location_error_km": 1 / math.sqrt(2),
                "unallocated_population_records_excluded": True,
                "cross_border_population_interpretation": INTERPRETATION,
                "cross_border_population_feature_approved": False,
                "cross_border_population_source_ids": f"{SOURCE_ID}|{DOCUMENTATION_SOURCE_ID}",
            }
        )
        rows.append(row)
    context = pd.DataFrame(rows)
    if len(context) != len(clusters) or not context["cluster_id"].is_unique:
        raise ValueError("Cross-border context must preserve one row per linked cluster")
    for category in ["", "switzerland_only_", "foreign_only_", "ch_foreign_mixed_"]:
        columns = [
            f"eurostat_{category}population_2021_within_{radius}km_cell_centroid"
            for radius in radii
        ]
        if (context[columns].diff(axis=1).iloc[:, 1:] < 0).any().any():
            raise ValueError(f"Population is not monotonic across radii for {category or 'total'}")
    return context


def enrich_decision_support(context: pd.DataFrame) -> None:
    path = ROOT / "data_processed" / "magic_pass_decision_support.csv"
    decision = pd.read_csv(path)
    identifiers = {"cluster_id", "cluster_display_name", "candidate_for_path_c"}
    context_columns = [column for column in context.columns if column not in identifiers]
    stale = [column for column in context_columns if column in decision.columns]
    decision = decision.drop(columns=stale).merge(
        context[["cluster_id", *context_columns]],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    guarded = [
        "accessibility_score",
        "predicted_uplift_pct",
        "uplift_lower_pct",
        "uplift_upper_pct",
        "composite_opportunity_need_score",
    ]
    nonblank = [column for column in guarded if column in decision and decision[column].notna().any()]
    if nonblank:
        raise ValueError(f"Unapproved decision fields became populated: {nonblank}")
    decision.to_csv(path, index=False)


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    source_config = json.loads(SOURCE_CONFIG_PATH.read_text(encoding="utf-8"))
    settings = config["cross_border_population_context"]
    if settings["source_id"] != SOURCE_ID or settings["interpretation"] != INTERPRETATION:
        raise ValueError("Cross-border population configuration is not the approved version")
    if source_config["source_id"] != SOURCE_ID:
        raise ValueError("Eurostat collection configuration source ID mismatch")
    radii = [int(value) for value in settings["straight_line_radii_km"]]
    if radii != sorted(set(radii)) or radii != [30, 60, 90, 120]:
        raise ValueError("Expected predeclared 30/60/90/120 km radii")
    unavailable_codes = {int(value) for value in settings["unavailable_total_population_codes"]}
    if unavailable_codes != {-8888, -9999}:
        raise ValueError("Unexpected unavailable-value codes")

    data_metadata = exact_metadata(SOURCE_ID)
    documentation_metadata = exact_metadata(DOCUMENTATION_SOURCE_ID)
    documentation = (ROOT / documentation_metadata["raw_file"]).read_text(
        encoding="utf-8", errors="replace"
    )
    for required_text in [
        "T: Total population",
        "value -8888",
        "value -9999",
        'cell code is "CC_unallocated"',
        "ETRS89-LAEA (EPSG:3035)",
    ]:
        if required_text not in documentation:
            raise ValueError(f"Official Eurostat documentation token missing: {required_text}")

    clusters, cluster_x, cluster_y = load_cluster_coordinates()
    grid, source_summary = load_relevant_grid(
        ROOT / data_metadata["raw_file"],
        cluster_x,
        cluster_y,
        max(radii),
        unavailable_codes,
    )
    grid.to_csv(REGIONAL_GRID_OUTPUT, index=False)
    context = build_cluster_context(clusters, cluster_x, cluster_y, grid, radii)
    context.to_csv(CLUSTER_OUTPUT, index=False)
    enrich_decision_support(context)

    candidates = context[as_bool(context["candidate_for_path_c"])].copy()
    audit_columns = ["cluster_id", "cluster_display_name"]
    for radius in [60, 120]:
        audit_columns.extend(
            [
                f"eurostat_population_2021_within_{radius}km_cell_centroid",
                f"eurostat_foreign_only_population_2021_within_{radius}km_cell_centroid",
                f"eurostat_ch_foreign_mixed_population_2021_within_{radius}km_cell_centroid",
                f"eurostat_foreign_only_share_of_observed_population_within_{radius}km",
                f"eurostat_positive_population_country_codes_within_{radius}km",
            ]
        )
    candidates[audit_columns].sort_values(
        "eurostat_foreign_only_share_of_observed_population_within_120km",
        ascending=False,
    ).to_csv(CANDIDATE_AUDIT_OUTPUT, index=False)

    radius_summary = {}
    for radius in radii:
        foreign_column = (
            f"eurostat_foreign_only_population_2021_within_{radius}km_cell_centroid"
        )
        mixed_column = (
            f"eurostat_ch_foreign_mixed_population_2021_within_{radius}km_cell_centroid"
        )
        share_column = f"eurostat_foreign_only_share_of_observed_population_within_{radius}km"
        missing_column = f"eurostat_total_population_unavailable_cells_within_{radius}km"
        radius_summary[str(radius)] = {
            "clusters_with_foreign_only_population": int(context[foreign_column].gt(0).sum()),
            "candidates_with_foreign_only_population": int(candidates[foreign_column].gt(0).sum()),
            "clusters_with_mixed_border_cell_population": int(context[mixed_column].gt(0).sum()),
            "clusters_with_unavailable_total_population_cells": int(
                context[missing_column].gt(0).sum()
            ),
            "median_foreign_only_population_all_clusters": float(context[foreign_column].median()),
            "median_foreign_only_population_candidates": float(candidates[foreign_column].median()),
            "median_foreign_only_share_all_clusters": float(context[share_column].median()),
            "median_foreign_only_share_candidates": float(candidates[share_column].median()),
            "maximum_foreign_only_share_candidate": float(candidates[share_column].max()),
        }
    summary = {
        "analysis_version": config["analysis_version"],
        "source_id": SOURCE_ID,
        "source_sha256": data_metadata["sha256"],
        "population_reference_year": 2021,
        "grid_release_date": settings["release_date"],
        **source_summary,
        "path_c_clusters_with_context": int(len(context)),
        "path_c_candidates_with_context": int(len(candidates)),
        "cluster_context_status_counts": context[
            "cross_border_population_context_status"
        ].value_counts().to_dict(),
        "radii_km": radius_summary,
        "cross_border_population_features_approved": int(
            as_bool(context["cross_border_population_feature_approved"]).sum()
        ),
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    table_rows = []
    for radius in radii:
        values = radius_summary[str(radius)]
        table_rows.append(
            "| {radius} | {clusters} | {candidates} | {mixed} | {share:.1%} | {missing} |".format(
                radius=radius,
                clusters=values["clusters_with_foreign_only_population"],
                candidates=values["candidates_with_foreign_only_population"],
                mixed=values["clusters_with_mixed_border_cell_population"],
                share=values["median_foreign_only_share_all_clusters"],
                missing=values["clusters_with_unavailable_total_population_cells"],
            )
        )
    report = f"""# Qualified cross-border population context

## Scope

The official Eurostat GISCO Census Grid 2021 version 3 supplies total population on a harmonised **1 km grid** in **EPSG:3035**. The checksum-verified raw CSV member contains **{summary['source_rows']:,} rows**. Of these, **{summary['spatially_allocated_rows']:,}** have a grid location; **{summary['unallocated_rows_excluded']:,}** country-level `CC_unallocated` records cannot be placed spatially and are excluded rather than assigned arbitrarily. Their observed population totals **{summary['observed_unallocated_population_excluded']:,}** people across the full source universe.

For every linked Path C lift cluster, a cell contributes when its centroid falls inside the predeclared 30, 60, 90 or 120 km straight-line radius. A 1 km square's centroid can differ from a point elsewhere in the cell by at most **0.707 km**. Cells are partitioned into Switzerland-only, foreign-only, and mixed Swiss/foreign border cells using the official reporting-country list. Mixed cells remain separate because the CSV does not allocate their population by country.

## Coverage

| Radius | Clusters with foreign-only population | Candidates with foreign-only population | Clusters with mixed-cell population | Median foreign-only share | Clusters with unavailable-total cells |
|---:|---:|---:|---:|---:|---:|
{chr(10).join(table_rows)}

- linked clusters with context: **{summary['path_c_clusters_with_context']}**
- apparent Path C candidates with context: **{summary['path_c_candidates_with_context']}**
- regional source cells retained: **{summary['regional_cells_within_maximum_radius_plus_centroid_tolerance']:,}**
- regional cells whose total population is unavailable: **{summary['regional_cells_with_unavailable_total_population']:,}**
- approved generic accessibility or causal population features: **0**

## Interpretation limit

This module closes the known *geographic truncation* of the Swiss-only population-radius diagnostic, but it does not create a visitor catchment. Census population is not skier demand; straight-line distance ignores mountains, roads, borders and travel behaviour. The 2021 grid is not merged numerically with STATPOP 2025 municipality totals because the reference year and allocation method differ. Confidential or otherwise unavailable totals (`-8888` and `-9999`) remain missing, while national unallocated records cannot be assigned to a radius. Population in mixed Swiss/foreign cells is reported separately rather than guessed. `cross_border_population_feature_approved` therefore remains false, `accessibility_score` remains blank, and no causal or composite ranking is produced.

## Outputs

- `data_processed/eurostat_population_grid_2021_swiss_region.csv`
- `data_processed/path_c_cluster_cross_border_population_context.csv`
- `reports/cross_border_population_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified context appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
