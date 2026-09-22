"""Build qualified Swiss straight-line population accessibility context for Path C.

The calculation aligns official STATPOP 2025 municipality population with the
official swissBOUNDARIES3D municipality state of 1 January 2026 using a small,
source-backed mutation bridge. Municipality populations are represented at a
point guaranteed to lie within each current polygon. Results are geographic
context only: they are neither travel times nor destination catchments.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import from_wkb, make_valid


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
INTERIM_DIR = ROOT / "data_interim" / "swissboundaries3d_2026"
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
POPULATION_PATH = ROOT / "data_processed" / "municipality_tourism_context_2025.csv"
BRIDGE_PATH = ROOT / "config" / "municipality_boundary_bridge_2025_2026.csv"
MUNICIPALITY_OUTPUT = ROOT / "data_processed" / "municipality_population_geometry_2026.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_accessibility_context.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "21_ACCESSIBILITY_CONTEXT.md"
BOUNDARY_SOURCE_ID = "SWISSTOPO_BOUNDARIES_2026"
POPULATION_SOURCE_ID = "BFS_STATPOP_DATA"
INTERPRETATION = (
    "swiss_straight_line_population_context_not_travel_time_or_destination_catchment"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def gpkg_geometry(blob: bytes):
    if blob[:2] != b"GP":
        raise ValueError("Unexpected GeoPackage geometry header")
    envelope_code = (blob[3] >> 1) & 7
    envelope_bytes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope_code]
    geometry = from_wkb(blob[8 + envelope_bytes :])
    return make_valid(geometry) if not geometry.is_valid else geometry


def exact_metadata(source_id: str) -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if len(records) != 1:
        raise ValueError(f"Expected one cached {source_id} record, found {len(records)}")
    record = records[0]
    raw_path = ROOT / record["raw_file"]
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Cached source checksum failure: {source_id}")
    return record


def checked_gpkg() -> Path:
    metadata = exact_metadata(BOUNDARY_SOURCE_ID)
    archive = ROOT / metadata["raw_file"]
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        members = [item for item in bundle.infolist() if item.filename.lower().endswith(".gpkg")]
        if len(members) != 1:
            raise ValueError(f"Expected one GeoPackage in archive, found {len(members)}")
        output = INTERIM_DIR / Path(members[0].filename).name
        if not output.exists() or output.stat().st_size != members[0].file_size:
            bundle.extract(members[0], INTERIM_DIR)
        if bundle.testzip() is not None:
            raise RuntimeError("swissBOUNDARIES3D archive integrity failure")
    return output


def checked_bridge() -> pd.DataFrame:
    bridge = pd.read_csv(BRIDGE_PATH)
    required = {
        "source_bfs_id_2025",
        "source_name_2025",
        "target_bfs_id_2026",
        "target_name_2026",
        "relationship",
        "source_id",
    }
    if set(bridge.columns) != required:
        raise ValueError(f"Unexpected bridge columns: {bridge.columns.tolist()}")
    if len(bridge) != 7 or not bridge["source_bfs_id_2025"].is_unique:
        raise ValueError("The reviewed 2025-to-2026 bridge must contain seven unique source IDs")
    for source_id, group in bridge.groupby("source_id", observed=True):
        record = exact_metadata(source_id)
        raw_text = html.unescape(
            (ROOT / record["raw_file"]).read_text(encoding="utf-8", errors="replace")
        )
        page_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw_text))
        for row in group.itertuples(index=False):
            expected_tokens = [
                str(row.source_bfs_id_2025),
                row.source_name_2025,
                str(row.target_bfs_id_2026),
                row.target_name_2026,
            ]
            missing = [token for token in expected_tokens if token not in page_text]
            if missing:
                raise ValueError(f"{source_id} does not verify bridge tokens {missing}")
    return bridge


def load_boundaries() -> pd.DataFrame:
    query = (
        "SELECT bfs_nummer,name,gem_flaeche,geom "
        "FROM tlm_hoheitsgebiet WHERE objektart='Gemeindegebiet' AND icc='CH'"
    )
    gpkg = checked_gpkg()
    with sqlite3.connect(gpkg.resolve().as_uri() + "?mode=ro", uri=True) as database:
        rows = database.execute(query).fetchall()
    boundaries = pd.DataFrame(
        rows,
        columns=[
            "boundary_bfs_id_2026",
            "boundary_name_2026",
            "municipality_area_ha_2026",
            "geometry_blob",
        ],
    )
    boundaries["geometry"] = boundaries.pop("geometry_blob").map(gpkg_geometry)
    if len(boundaries) != 2110 or not boundaries["boundary_bfs_id_2026"].is_unique:
        raise ValueError(
            f"Expected 2,110 unique Swiss 2026 municipality polygons, found {len(boundaries)}"
        )
    return boundaries


def align_population(boundaries: pd.DataFrame, bridge: pd.DataFrame) -> pd.DataFrame:
    population = pd.read_csv(
        POPULATION_PATH,
        usecols=[
            "municipality_bfs_id",
            "municipality_name_statpop",
            "population_reference_year",
            "resident_population",
            "population_source_id",
        ],
    )
    if (
        len(population) != 2115
        or not population["municipality_bfs_id"].is_unique
        or not population["population_reference_year"].eq(2025).all()
        or not population["population_source_id"].eq(POPULATION_SOURCE_ID).all()
        or not population["resident_population"].gt(0).all()
    ):
        raise ValueError("Unexpected STATPOP 2025 municipality population input")

    bridge_lookup = bridge.set_index("source_bfs_id_2025")
    population["boundary_bfs_id_2026"] = population["municipality_bfs_id"].map(
        bridge_lookup["target_bfs_id_2026"]
    ).fillna(population["municipality_bfs_id"]).astype(int)
    population["boundary_bridge_relationship"] = population["municipality_bfs_id"].map(
        bridge_lookup["relationship"]
    ).fillna("same_bfs_id")
    population["boundary_bridge_source_id"] = population["municipality_bfs_id"].map(
        bridge_lookup["source_id"]
    ).fillna("")

    aggregated_rows = []
    for boundary_id, group in population.groupby("boundary_bfs_id_2026", sort=True):
        relationships = sorted(set(group["boundary_bridge_relationship"]))
        sources = sorted(set(group["boundary_bridge_source_id"]) - {""})
        aggregated_rows.append(
            {
                "boundary_bfs_id_2026": int(boundary_id),
                "population_reference_year": 2025,
                "resident_population_2025_on_2026_boundary": int(
                    group["resident_population"].sum()
                ),
                "population_constituent_count_2025": int(len(group)),
                "population_constituent_bfs_ids_2025": "|".join(
                    group["municipality_bfs_id"].astype(str)
                ),
                "population_constituent_names_2025": "|".join(
                    group["municipality_name_statpop"].astype(str)
                ),
                "boundary_bridge_status": (
                    "same_bfs_id" if relationships == ["same_bfs_id"] else "|".join(relationships)
                ),
                "boundary_bridge_source_ids": "|".join(sources),
                "population_source_id": POPULATION_SOURCE_ID,
                "boundary_source_id": BOUNDARY_SOURCE_ID,
            }
        )
    aligned = pd.DataFrame(aggregated_rows)
    aligned = boundaries.merge(
        aligned,
        on="boundary_bfs_id_2026",
        how="left",
        validate="one_to_one",
    )
    if aligned["resident_population_2025_on_2026_boundary"].isna().any():
        missing = aligned.loc[
            aligned["resident_population_2025_on_2026_boundary"].isna(),
            ["boundary_bfs_id_2026", "boundary_name_2026"],
        ]
        raise ValueError(f"2026 boundaries without aligned STATPOP: {missing.to_dict('records')}")
    original_total = int(population["resident_population"].sum())
    aligned_total = int(aligned["resident_population_2025_on_2026_boundary"].sum())
    if original_total != aligned_total:
        raise ValueError(f"Population total changed during boundary alignment: {original_total} != {aligned_total}")

    inverse = Transformer.from_crs(2056, 4326, always_xy=True)
    representatives = aligned["geometry"].map(lambda geometry: geometry.representative_point())
    aligned["municipality_representative_x_2056"] = representatives.map(lambda point: point.x)
    aligned["municipality_representative_y_2056"] = representatives.map(lambda point: point.y)
    lon_lat = representatives.map(lambda point: inverse.transform(point.x, point.y))
    aligned["municipality_representative_longitude"] = lon_lat.map(lambda value: value[0])
    aligned["municipality_representative_latitude"] = lon_lat.map(lambda value: value[1])
    aligned["boundary_reference_date"] = "2026-01-01"
    aligned["population_boundary_alignment"] = "STATPOP_2025_aggregated_to_2026_boundaries"
    aligned["accessibility_interpretation"] = INTERPRETATION
    return aligned


def build_cluster_context(municipalities: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = pd.read_csv(ROOT / "data_processed" / "path_c_resort_cluster_features.csv")
    if features[["latitude_median", "longitude_median"]].isna().any().any():
        raise ValueError("Every Path C cluster must have a median coordinate")
    settings = config["accessibility_context"]
    thresholds = [int(value) for value in settings["population_center_thresholds"]]
    radii = [int(value) for value in settings["straight_line_radii_km"]]
    if thresholds != sorted(set(thresholds)) or radii != sorted(set(radii)):
        raise ValueError("Accessibility thresholds and radii must be sorted and unique")

    population = municipalities["resident_population_2025_on_2026_boundary"].to_numpy()
    municipality_x = municipalities["municipality_representative_x_2056"].to_numpy()
    municipality_y = municipalities["municipality_representative_y_2056"].to_numpy()
    coordinate_transform = Transformer.from_crs(4326, 2056, always_xy=True)
    rows = []
    for cluster in features.itertuples(index=False):
        x, y = coordinate_transform.transform(cluster.longitude_median, cluster.latitude_median)
        distances_km = np.hypot(municipality_x - x, municipality_y - y) / 1000
        row = {
            "cluster_id": cluster.cluster_id,
            "cluster_display_name": cluster.cluster_display_name,
            "candidate_for_path_c": str(cluster.candidate_for_path_c).lower() == "true",
            "cluster_location_longitude": float(cluster.longitude_median),
            "cluster_location_latitude": float(cluster.latitude_median),
        }
        for threshold in thresholds:
            eligible = population >= threshold
            if not eligible.any():
                raise ValueError(f"No municipality meets population threshold {threshold}")
            eligible_indices = np.flatnonzero(eligible)
            nearest_index = int(eligible_indices[np.argmin(distances_km[eligible])])
            nearest = municipalities.iloc[nearest_index]
            prefix = f"nearest_municipality_population_ge_{threshold}"
            row[f"{prefix}_bfs_id_2026"] = int(nearest["boundary_bfs_id_2026"])
            row[f"{prefix}_name"] = nearest["boundary_name_2026"]
            row[f"distance_to_{prefix}_km"] = float(distances_km[nearest_index])
        for radius in radii:
            row[f"resident_population_within_{radius}km_straight_line"] = int(
                population[distances_km <= radius].sum()
            )
        row.update(
            {
                "population_reference_year": int(settings["population_reference_year"]),
                "boundary_reference_date": settings["boundary_reference_date"],
                "distance_crs": settings["distance_crs"],
                "municipality_location_method": settings["municipality_location"],
                "accessibility_context_status": "complete_swiss_straight_line_population_context",
                "accessibility_interpretation": INTERPRETATION,
                "accessibility_feature_approved": False,
                "population_source_id": POPULATION_SOURCE_ID,
                "boundary_source_id": BOUNDARY_SOURCE_ID,
                "boundary_bridge_source_ids": "BFS_MUNICIPAL_MUTATION_3999|BFS_MUNICIPAL_MUTATION_4000|BFS_MUNICIPAL_MUTATION_4001|BFS_MUNICIPAL_MUTATION_4002|BFS_MUNICIPAL_MUTATION_4003",
            }
        )
        rows.append(row)
    context = pd.DataFrame(rows)
    if len(context) != len(features) or not context["cluster_id"].is_unique:
        raise ValueError("Accessibility output must preserve one row per Path C cluster")
    radius_columns = [f"resident_population_within_{radius}km_straight_line" for radius in radii]
    if (context[radius_columns].diff(axis=1).iloc[:, 1:] < 0).any().any():
        raise ValueError("Population within increasing straight-line radii is not monotonic")
    return context


def enrich_decision_support(context: pd.DataFrame) -> None:
    path = ROOT / "data_processed" / "magic_pass_decision_support.csv"
    decision = pd.read_csv(path)
    context_columns = [
        column
        for column in context.columns
        if column not in {"cluster_id", "cluster_display_name", "candidate_for_path_c"}
    ]
    decision = decision.drop(
        columns=[column for column in context_columns if column in decision.columns]
    ).merge(
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
    settings = config["accessibility_context"]
    if settings["interpretation"] != INTERPRETATION:
        raise ValueError("Accessibility interpretation in config is not the approved qualified label")
    bridge = checked_bridge()
    municipalities = align_population(load_boundaries(), bridge)
    municipality_export = municipalities.drop(columns="geometry")
    municipality_export.to_csv(MUNICIPALITY_OUTPUT, index=False)
    context = build_cluster_context(municipalities, config)
    context.to_csv(CLUSTER_OUTPUT, index=False)
    enrich_decision_support(context)

    candidates = context[as_bool(context["candidate_for_path_c"])]
    threshold_counts = {
        str(threshold): int(
            municipalities["resident_population_2025_on_2026_boundary"].ge(threshold).sum()
        )
        for threshold in settings["population_center_thresholds"]
    }
    summary = {
        "analysis_version": config["analysis_version"],
        "statpop_2025_source_municipalities": 2115,
        "swissboundaries_2026_municipalities": int(len(municipalities)),
        "bridged_statpop_source_municipalities": int(len(bridge)),
        "aligned_resident_population_total": int(
            municipalities["resident_population_2025_on_2026_boundary"].sum()
        ),
        "population_reference_municipalities_by_threshold": threshold_counts,
        "path_c_clusters_with_context": int(len(context)),
        "path_c_candidates_with_context": int(len(candidates)),
        "accessibility_features_approved": int(
            as_bool(context["accessibility_feature_approved"]).sum()
        ),
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    thresholds_text = ", ".join(
        f"at least {int(threshold):,}: **{threshold_counts[str(threshold)]:,}**"
        for threshold in settings["population_center_thresholds"]
    )
    radii_text = ", ".join(f"{int(radius)} km" for radius in settings["straight_line_radii_km"])
    report = f"""# Qualified straight-line population accessibility context

## Scope

Official STATPOP 2025 permanent-resident population is aligned to the official swissBOUNDARIES3D municipality state of 1 January 2026. The seven 2025 identifiers affected by the five official 2026 OFS mutations are explicitly mapped and aggregated. This preserves all **{summary['aligned_resident_population_total']:,} residents** while reconciling **{summary['statpop_2025_source_municipalities']:,}** STATPOP rows to **{summary['swissboundaries_2026_municipalities']:,}** current polygons.

Each municipality is represented by a point guaranteed to lie within its polygon. Distances from each cluster's median supplied coordinate are Euclidean distances in EPSG:2056. Three transparent population thresholds are reported instead of selecting one untested definition: {thresholds_text}. Population totals are also reported inside {radii_text} straight-line radii. The thresholds and radii are versioned in `config/path_c_analysis.json`.

## Coverage

- linked Path C clusters with complete geographic context: **{summary['path_c_clusters_with_context']:,}**
- apparent Path C candidates with complete geographic context: **{summary['path_c_candidates_with_context']:,}**
- municipality mutation records verified against checksum-protected OFS pages: **5**
- approved generic accessibility features or scores: **0**

## Interpretation limit

These fields are Swiss straight-line population context, not road or public-transport travel time, not a labour or visitor market, and not a destination catchment. Municipality population is collapsed to one representative point, so totals within a radius are discretised approximations. Foreign population is excluded, which especially understates context near national borders. Terrain, network impedance, seasonal closures and travel behaviour are not represented. Consequently `accessibility_feature_approved` remains false and the generic `accessibility_score` remains blank; no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/municipality_population_geometry_2026.csv`
- `data_processed/path_c_cluster_accessibility_context.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified context columns appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
