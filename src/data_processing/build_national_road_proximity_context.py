"""Build qualified proximity context to official Swiss national-road axes.

The FEDRO/ASTRA source distinguishes main, feeder, connection and ramp axes,
but it does not publish a motorway-class field in these layers. Consequently,
this module reports distance to the main national-road axis and to any
published national-road axis. It never labels either measure as motorway
distance, route distance, driving time or historical accessibility.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

import numpy as np
import pandas as pd
import pyogrio
from pyogrio import raw
from pyproj import Transformer
from shapely import from_wkb
from shapely.geometry import Point
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
POINT_MUNICIPALITY_PATH = ROOT / "data_processed" / "resort_point_municipality.csv"
FEATURE_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
LISTING_OUTPUT = ROOT / "data_processed" / "resort_national_road_proximity_context.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_national_road_proximity_context.csv"
CANDIDATE_OUTPUT = ROOT / "reports" / "national_road_proximity_candidate_summary.csv"
DECISION_OUTPUT = ROOT / "data_processed" / "magic_pass_decision_support.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "national_road_proximity_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md"

SOURCE_ID = "ASTRA_NATIONAL_ROAD_AXES_2026"
STAC_SOURCE_ID = "ASTRA_NATIONAL_ROAD_AXES_2026_STAC"
COLLECTION_SOURCE_ID = "ASTRA_NATIONAL_ROAD_AXES_COLLECTION"
SOURCE_REFERENCE_DATETIME = "2026-08-01T00:00:00Z"
ASSET_UPDATED_DATETIME = "2026-09-01T03:32:13.046159Z"
MAIN_LAYER = "Stammachsen"
NETWORK_LAYERS = ["Anschlussachse", "Rampenachsen", "Stammachsen", "Zubringerachsen"]
EXPECTED_FEATURE_COUNTS = {
    "Anschlussachse": 596,
    "Rampenachsen": 2_292,
    "Stammachsen": 166,
    "Zubringerachsen": 30,
    "Bezugspunkte": 15_176,
    "Data_status": 1,
}
REQUIRED_FIELDS = {
    "ID",
    "Eigentuemer",
    "Segmentname",
    "Strassennummer",
    "Bezeichnung",
    "Positionscode",
    "SHAPE_Length",
}
INTERPRETATION = (
    "official_current_swiss_national_road_axis_straight_line_context_not_"
    "motorway_classification_route_or_historical_accessibility"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


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


def checked_source(config: dict) -> tuple[Path, dict, dict]:
    settings = config["national_road_proximity_context"]
    expected = {
        "source_id": SOURCE_ID,
        "source_reference_datetime": SOURCE_REFERENCE_DATETIME,
        "asset_updated_datetime": ASSET_UPDATED_DATETIME,
        "distance_crs": "EPSG:2056",
        "main_axis_layer": MAIN_LAYER,
        "network_axis_layers": NETWORK_LAYERS,
        "point_eligibility": (
            "supplied_listing_coordinate_inside_unique_current_swiss_municipality"
        ),
        "cluster_aggregation": (
            "minimum_median_maximum_across_eligible_supplied_listing_points"
        ),
        "interpretation": INTERPRETATION,
    }
    if settings != expected:
        raise ValueError("Unexpected national-road proximity configuration")

    data_metadata = exact_metadata(SOURCE_ID)
    stac_metadata = exact_metadata(STAC_SOURCE_ID)
    collection_metadata = exact_metadata(COLLECTION_SOURCE_ID)
    stac = json.loads((ROOT / stac_metadata["raw_file"]).read_text(encoding="utf-8"))
    collection = json.loads(
        (ROOT / collection_metadata["raw_file"]).read_text(encoding="utf-8")
    )
    properties = stac.get("properties", {})
    if (
        stac.get("id") != "nationalstrassenachsen"
        or stac.get("collection") != "ch.astra.nationalstrassenachsen"
        or properties.get("datetime") != SOURCE_REFERENCE_DATETIME
        or properties.get("updated") != ASSET_UPDATED_DATETIME
    ):
        raise ValueError("Unexpected ASTRA STAC item identity or dates")
    asset = stac.get("assets", {}).get("nationalstrassenachsen_2056.gdb.zip", {})
    if (
        asset.get("href") != data_metadata["url"]
        or asset.get("proj:epsg") != 2056
        or asset.get("file:checksum") != "1220" + data_metadata["sha256"]
    ):
        raise ValueError("ASTRA STAC asset URL, CRS or checksum mismatch")
    if (
        collection.get("id") != "ch.astra.nationalstrassenachsen"
        or collection.get("summaries", {}).get("proj:epsg") != [2056]
        or collection.get("extent", {}).get("temporal", {}).get("interval")
        != [[SOURCE_REFERENCE_DATETIME, SOURCE_REFERENCE_DATETIME]]
        or "Federal Roads Office" not in collection.get("description", "")
    ):
        raise ValueError("Unexpected ASTRA STAC collection definition")
    return ROOT / data_metadata["raw_file"], stac, collection


def safe_extract_gdb(archive_path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("ASTRA national-road archive integrity failure")
        for name in archive.namelist():
            member = PurePosixPath(name)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"Unsafe archive member: {name}")
        archive.extractall(destination)
    geodatabases = list(destination.glob("*.gdb"))
    if len(geodatabases) != 1:
        raise ValueError(f"Expected one File Geodatabase, found {len(geodatabases)}")
    return geodatabases[0]


def load_line_layer(gdb_path: Path, layer: str) -> tuple[list[dict], dict]:
    info = pyogrio.read_info(gdb_path, layer=layer)
    if info["features"] != EXPECTED_FEATURE_COUNTS[layer]:
        raise ValueError(f"Unexpected ASTRA feature count for {layer}")
    if set(info["fields"]) != REQUIRED_FIELDS:
        raise ValueError(f"Unexpected ASTRA schema for {layer}: {info['fields']}")
    if info["geometry_type"] != "MultiLineString Z":
        raise ValueError(f"Unexpected ASTRA geometry type for {layer}")
    metadata, _, geometry_wkb, arrays = raw.read(gdb_path, layer=layer)
    if metadata.get("geometry_type") != "MultiLineString Z":
        raise ValueError(f"Raw ASTRA geometry metadata changed for {layer}")
    fields = {name: array for name, array in zip(info["fields"], arrays, strict=True)}
    geometries = list(from_wkb(geometry_wkb))
    if len(geometries) != EXPECTED_FEATURE_COUNTS[layer]:
        raise ValueError(f"ASTRA geometry array length changed for {layer}")
    if any(geometry is None or geometry.is_empty or not geometry.is_valid for geometry in geometries):
        raise ValueError(f"Invalid or empty ASTRA geometry in {layer}")
    if set(fields["Eigentuemer"]) != {"CH"}:
        raise ValueError(f"Unexpected ASTRA owner code in {layer}")
    length_difference = np.abs(
        np.array([geometry.length for geometry in geometries], dtype=float)
        - fields["SHAPE_Length"].astype(float)
    )
    if float(length_difference.max()) > 1e-6:
        raise ValueError(f"ASTRA geometry and published lengths differ for {layer}")

    records = []
    for index, geometry in enumerate(geometries):
        records.append(
            {
                "axis_layer": layer,
                "axis_id": str(fields["ID"][index]),
                "road_number": str(fields["Strassennummer"][index]),
                "segment_name": str(fields["Segmentname"][index]),
                "designation": str(fields["Bezeichnung"][index]),
                "position_code": str(fields["Positionscode"][index]),
                "geometry": geometry,
            }
        )
    records.sort(key=lambda row: (row["axis_layer"], row["axis_id"]))
    return records, {
        "features": len(records),
        "published_feature_length_km": float(fields["SHAPE_Length"].sum() / 1000),
    }


def load_axes(archive_path: Path) -> tuple[list[dict], list[dict], dict]:
    with tempfile.TemporaryDirectory(prefix="astra-national-roads-") as temporary:
        gdb_path = safe_extract_gdb(archive_path, Path(temporary))
        layers = {name: geometry for name, geometry in pyogrio.list_layers(gdb_path)}
        if set(layers) != set(EXPECTED_FEATURE_COUNTS):
            raise ValueError(f"Unexpected ASTRA File Geodatabase layers: {sorted(layers)}")
        for layer, expected in EXPECTED_FEATURE_COUNTS.items():
            if pyogrio.read_info(gdb_path, layer=layer)["features"] != expected:
                raise ValueError(f"Unexpected ASTRA feature count for {layer}")
        metadata, _, _, arrays = raw.read(gdb_path, layer="Data_status")
        if list(metadata.get("fields", [])) != ["DATASTATUS"]:
            raise ValueError("Unexpected ASTRA data-status schema")
        data_status = pd.Timestamp(arrays[0][0]).strftime("%Y-%m-%d")
        if data_status != "2026-09-01":
            raise ValueError("Unexpected ASTRA embedded data-status date")

        by_layer = {}
        layer_summary = {}
        for layer in NETWORK_LAYERS:
            by_layer[layer], layer_summary[layer] = load_line_layer(gdb_path, layer)
        main = by_layer[MAIN_LAYER]
        network = [record for layer in NETWORK_LAYERS for record in by_layer[layer]]
    return main, network, {
        "embedded_data_status_date": data_status,
        "layers": layer_summary,
        "network_axis_features": len(network),
        "network_published_feature_length_km": float(
            sum(value["published_feature_length_km"] for value in layer_summary.values())
        ),
    }


def nearest_axis(point: Point, tree: STRtree, records: list[dict], prefix: str) -> dict:
    matches, distances = tree.query_nearest(point, return_distance=True, all_matches=True)
    minimum_distance = float(np.min(distances))
    tied = sorted(
        int(index)
        for index, distance in zip(matches, distances, strict=True)
        if abs(float(distance) - minimum_distance) <= 1e-9
    )
    chosen = records[tied[0]]
    return {
        f"nearest_{prefix}_axis_layer": chosen["axis_layer"],
        f"nearest_{prefix}_axis_id": chosen["axis_id"],
        f"nearest_{prefix}_road_number": chosen["road_number"],
        f"nearest_{prefix}_segment_name": chosen["segment_name"],
        f"nearest_{prefix}_designation": chosen["designation"],
        f"nearest_{prefix}_position_code": chosen["position_code"],
        f"distance_to_nearest_{prefix}_km": minimum_distance / 1000,
    }


def build_listing_context(
    main: list[dict], network: list[dict], config: dict
) -> pd.DataFrame:
    resorts = pd.read_csv(RESORT_PATH)
    crosswalk = pd.read_csv(POINT_MUNICIPALITY_PATH)
    if len(resorts) != 271 or not resorts["resort_id"].is_unique:
        raise ValueError("Unexpected resort listing grain")
    if len(crosswalk) != 271 or not crosswalk["resort_id"].is_unique:
        raise ValueError("Unexpected point-municipality crosswalk grain")
    context = resorts[
        ["resort_id", "resort_name_canonical", "cluster_id", "latitude", "longitude"]
    ].merge(
        crosswalk[
            [
                "resort_id",
                "point_municipality_bfs_id",
                "point_municipality_name",
                "selection_status",
            ]
        ],
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    point_x, point_y = transformer.transform(
        context["longitude"].to_numpy(), context["latitude"].to_numpy()
    )
    context["point_x_2056"] = point_x
    context["point_y_2056"] = point_y
    eligible = context["selection_status"].eq("unique_current_polygon")
    if int(eligible.sum()) != 268:
        raise ValueError("Unexpected Swiss point-eligibility count")

    main_tree = STRtree([row["geometry"] for row in main])
    network_tree = STRtree([row["geometry"] for row in network])
    nearest_rows = []
    for row in context.loc[eligible].itertuples(index=False):
        point = Point(row.point_x_2056, row.point_y_2056)
        nearest_rows.append(
            {
                "resort_id": row.resort_id,
                **nearest_axis(point, main_tree, main, "national_road_main"),
                **nearest_axis(point, network_tree, network, "national_road_network"),
            }
        )
    context = context.merge(
        pd.DataFrame(nearest_rows), on="resort_id", how="left", validate="one_to_one"
    )
    context["national_road_proximity_context_status"] = np.where(
        eligible,
        "assigned_official_swiss_national_road_scope",
        "outside_official_swiss_national_road_scope",
    )
    context["national_road_proximity_values_complete"] = eligible
    settings = config["national_road_proximity_context"]
    context["national_road_source_reference_datetime"] = settings[
        "source_reference_datetime"
    ]
    context["national_road_asset_updated_datetime"] = settings[
        "asset_updated_datetime"
    ]
    context["national_road_distance_crs"] = settings["distance_crs"]
    context["national_road_point_eligibility"] = settings["point_eligibility"]
    context["national_road_main_axis_scope"] = "official_Stammachsen_layer"
    context["national_road_network_axis_scope"] = (
        "official_Anschlussachse_Rampenachsen_Stammachsen_Zubringerachsen_layers"
    )
    context["national_road_distance_method"] = (
        "euclidean_straight_line_from_supplied_listing_coordinate_to_published_axis"
    )
    context["national_road_motorway_classification_available"] = False
    context["national_road_proximity_interpretation"] = INTERPRETATION
    context["national_road_proximity_feature_approved"] = False
    context["national_road_source_ids"] = (
        f"{SOURCE_ID}|{STAC_SOURCE_ID}|{COLLECTION_SOURCE_ID}"
    )
    distances = [
        "distance_to_nearest_national_road_main_km",
        "distance_to_nearest_national_road_network_km",
    ]
    if context.loc[eligible, distances].isna().any().any():
        raise ValueError("Eligible listing lacks a national-road-axis distance")
    if context.loc[~eligible, distances].notna().any().any():
        raise ValueError("Outside-scope listing received a national-road-axis distance")
    if (context.loc[eligible, distances] < 0).any().any():
        raise ValueError("Negative national-road-axis distance")
    if not (
        context.loc[eligible, "distance_to_nearest_national_road_network_km"]
        <= context.loc[eligible, "distance_to_nearest_national_road_main_km"] + 1e-12
    ).all():
        raise ValueError("All-axis network distance exceeds main-axis distance")
    return context


def pipe_unique(series: pd.Series) -> str:
    return "|".join(sorted({str(value) for value in series.dropna() if str(value)}))


def build_cluster_context(listings: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = pd.read_csv(FEATURE_PATH)
    if len(features) != 162 or not features["cluster_id"].is_unique:
        raise ValueError("Unexpected Path C feature grain")
    if set(features["cluster_id"]) != set(listings["cluster_id"]):
        raise ValueError("Listing and Path C cluster universes differ")
    rows = []
    for feature in features.itertuples(index=False):
        group = listings[listings["cluster_id"].eq(feature.cluster_id)].copy()
        usable = group[as_bool(group["national_road_proximity_values_complete"])]
        if len(usable) == len(group):
            status = "complete_all_listing_points_inside_swiss_scope"
        elif len(usable):
            status = "partial_listing_points_outside_swiss_scope"
        else:
            status = "unavailable_no_listing_point_inside_swiss_scope"
        row = {
            "cluster_id": feature.cluster_id,
            "cluster_display_name": feature.cluster_display_name,
            "candidate_for_path_c": str(feature.candidate_for_path_c).lower() == "true",
            "cluster_listing_count": int(len(group)),
            "cluster_listings_with_national_road_context": int(len(usable)),
            "cluster_listing_national_road_context_share": len(usable) / len(group),
            "cluster_national_road_proximity_context_status": status,
            "cluster_unassigned_national_road_resort_ids": pipe_unique(
                group.loc[
                    ~as_bool(group["national_road_proximity_values_complete"]), "resort_id"
                ]
            ),
        }
        for prefix in ["national_road_main", "national_road_network"]:
            distance = f"distance_to_nearest_{prefix}_km"
            values = usable[distance].astype(float)
            for statistic, calculation in {
                "minimum": values.min,
                "median": values.median,
                "maximum": values.max,
            }.items():
                row[f"cluster_distance_to_nearest_{prefix}_{statistic}_km"] = (
                    float(calculation()) if len(values) else np.nan
                )
            row[f"cluster_distance_to_nearest_{prefix}_range_km"] = (
                float(values.max() - values.min()) if len(values) else np.nan
            )
            row[f"cluster_nearest_{prefix}_road_numbers"] = pipe_unique(
                usable[f"nearest_{prefix}_road_number"]
            )
            row[f"cluster_nearest_{prefix}_axis_layers"] = pipe_unique(
                usable[f"nearest_{prefix}_axis_layer"]
            )
        settings = config["national_road_proximity_context"]
        row.update(
            {
                "national_road_source_reference_datetime": settings[
                    "source_reference_datetime"
                ],
                "national_road_asset_updated_datetime": settings[
                    "asset_updated_datetime"
                ],
                "national_road_distance_crs": settings["distance_crs"],
                "national_road_point_eligibility": settings["point_eligibility"],
                "national_road_main_axis_scope": "official_Stammachsen_layer",
                "national_road_network_axis_scope": (
                    "official_Anschlussachse_Rampenachsen_Stammachsen_Zubringerachsen_layers"
                ),
                "national_road_cluster_aggregation": settings["cluster_aggregation"],
                "national_road_motorway_classification_available": False,
                "national_road_proximity_interpretation": INTERPRETATION,
                "national_road_proximity_feature_approved": False,
                "national_road_source_ids": (
                    f"{SOURCE_ID}|{STAC_SOURCE_ID}|{COLLECTION_SOURCE_ID}"
                ),
            }
        )
        rows.append(row)
    context = pd.DataFrame(rows)
    if len(context) != 162 or not context["cluster_id"].is_unique:
        raise ValueError("Cluster road context must preserve one row per lift cluster")
    if int(context["cluster_listing_count"].sum()) != len(listings):
        raise ValueError("Cluster road aggregation lost resort listings")
    for prefix in ["national_road_main", "national_road_network"]:
        stem = f"cluster_distance_to_nearest_{prefix}"
        complete = context[f"{stem}_median_km"].notna()
        if not (
            context.loc[complete, f"{stem}_minimum_km"]
            <= context.loc[complete, f"{stem}_median_km"]
        ).all() or not (
            context.loc[complete, f"{stem}_median_km"]
            <= context.loc[complete, f"{stem}_maximum_km"]
        ).all():
            raise ValueError(f"Invalid cluster distance summary for {prefix}")
    usable = context["cluster_distance_to_nearest_national_road_network_median_km"].notna()
    if not (
        context.loc[
            usable, "cluster_distance_to_nearest_national_road_network_median_km"
        ]
        <= context.loc[
            usable, "cluster_distance_to_nearest_national_road_main_median_km"
        ]
        + 1e-12
    ).all():
        raise ValueError("Cluster all-axis median exceeds main-axis median")
    return context


def enrich_decision_support(context: pd.DataFrame) -> None:
    decision = pd.read_csv(DECISION_OUTPUT)
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
    nonblank = [
        column for column in guarded if column in decision and decision[column].notna().any()
    ]
    if nonblank:
        raise ValueError(f"Unapproved decision fields became populated: {nonblank}")
    if as_bool(decision["national_road_proximity_feature_approved"]).any():
        raise ValueError("National-road proximity was unexpectedly approved")
    DECISION_OUTPUT.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    archive_path, _, collection = checked_source(config)
    main_axes, network_axes, source_summary = load_axes(archive_path)
    listings = build_listing_context(main_axes, network_axes, config)
    listings.to_csv(LISTING_OUTPUT, index=False, lineterminator="\n")
    clusters = build_cluster_context(listings, config)
    clusters.to_csv(CLUSTER_OUTPUT, index=False, lineterminator="\n")
    enrich_decision_support(clusters)

    usable = as_bool(listings["national_road_proximity_values_complete"])
    candidates = clusters[as_bool(clusters["candidate_for_path_c"])].copy()
    candidates[
        [
            "cluster_id",
            "cluster_display_name",
            "cluster_national_road_proximity_context_status",
            "cluster_distance_to_nearest_national_road_main_median_km",
            "cluster_distance_to_nearest_national_road_network_median_km",
            "cluster_nearest_national_road_main_road_numbers",
            "cluster_nearest_national_road_network_road_numbers",
        ]
    ].sort_values(
        "cluster_distance_to_nearest_national_road_main_median_km"
    ).to_csv(CANDIDATE_OUTPUT, index=False, lineterminator="\n")
    summary = {
        "analysis_version": config["analysis_version"],
        "source_reference_datetime": SOURCE_REFERENCE_DATETIME,
        "asset_updated_datetime": ASSET_UPDATED_DATETIME,
        "collection_provider": collection["providers"][0]["name"],
        **source_summary,
        "resort_listings": len(listings),
        "resort_listings_inside_official_swiss_scope": int(usable.sum()),
        "resort_listings_outside_official_swiss_scope": int((~usable).sum()),
        "outside_scope_resort_ids": listings.loc[~usable, "resort_id"].tolist(),
        "path_c_clusters": len(clusters),
        "path_c_clusters_complete": int(
            clusters["cluster_national_road_proximity_context_status"]
            .eq("complete_all_listing_points_inside_swiss_scope")
            .sum()
        ),
        "path_c_clusters_partial": int(
            clusters["cluster_national_road_proximity_context_status"]
            .eq("partial_listing_points_outside_swiss_scope")
            .sum()
        ),
        "path_c_candidates": len(candidates),
        "path_c_candidates_complete": int(
            candidates["cluster_national_road_proximity_context_status"]
            .eq("complete_all_listing_points_inside_swiss_scope")
            .sum()
        ),
        "median_cluster_median_distance_to_main_axis_km": float(
            clusters[
                "cluster_distance_to_nearest_national_road_main_median_km"
            ].median()
        ),
        "median_cluster_median_distance_to_any_network_axis_km": float(
            clusters[
                "cluster_distance_to_nearest_national_road_network_median_km"
            ].median()
        ),
        "maximum_listing_distance_to_main_axis_km": float(
            listings.loc[usable, "distance_to_nearest_national_road_main_km"].max()
        ),
        "maximum_listing_distance_to_any_network_axis_km": float(
            listings.loc[usable, "distance_to_nearest_national_road_network_km"].max()
        ),
        "nearest_network_axis_layer_counts_for_eligible_listings": {
            str(key): int(value)
            for key, value in listings.loc[
                usable, "nearest_national_road_network_axis_layer"
            ]
            .value_counts()
            .sort_index()
            .items()
        },
        "motorway_classification_available": False,
        "approved_features": int(
            as_bool(clusters["national_road_proximity_feature_approved"]).sum()
        ),
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    outside = ", ".join(
        f"{row.resort_name_canonical} (`{row.resort_id}`)"
        for row in listings.loc[~usable].itertuples(index=False)
    )
    layer_counts = ", ".join(
        f"{layer}: {count}"
        for layer, count in summary[
            "nearest_network_axis_layer_counts_for_eligible_listings"
        ].items()
    )
    report = f"""# Qualified proximity to official Swiss national-road axes

## Scope and definitions

The checksum-verified FEDRO/ASTRA File Geodatabase has STAC reference datetime **{SOURCE_REFERENCE_DATETIME}**, asset update timestamp **{ASSET_UPDATED_DATETIME}**, embedded data-status date **{summary['embedded_data_status_date']}**, and official coordinate reference **EPSG:2056**. It publishes **{summary['layers']['Stammachsen']['features']:,} main-axis features**, **{summary['layers']['Anschlussachse']['features']:,} connection-axis features**, **{summary['layers']['Rampenachsen']['features']:,} ramp-axis features**, and **{summary['layers']['Zubringerachsen']['features']:,} feeder-axis features**. Geometry lengths reproduce every published `SHAPE_Length` value within numerical tolerance.

Two straight-line measures are retained from each eligible supplied listing coordinate:

- distance to the nearest official `Stammachsen` main axis;
- distance to the nearest line in any of the four official national-road axis layers.

The source fields identify a national-route number, segment and axis family, but do **not** provide a motorway-versus-non-motorway classification. The analysis therefore never renames these measures as motorway distance. Cluster summaries preserve the minimum, median and maximum across eligible supplied listing points.

## Coverage and descriptive reference

- eligible Swiss resort listings with both distances: **{summary['resort_listings_inside_official_swiss_scope']:,} / {summary['resort_listings']:,}**
- listings outside the complete Swiss source scope and left missing: **{summary['resort_listings_outside_official_swiss_scope']:,}**
- clusters complete for every supplied listing point: **{summary['path_c_clusters_complete']:,} / {summary['path_c_clusters']:,}**
- partially covered clusters: **{summary['path_c_clusters_partial']:,}**
- apparent Path C candidates with complete context: **{summary['path_c_candidates_complete']:,} / {summary['path_c_candidates']:,}**
- median of cluster-median distance to a national-road main axis: **{summary['median_cluster_median_distance_to_main_axis_km']:.2f} km**
- median of cluster-median distance to any national-road axis: **{summary['median_cluster_median_distance_to_any_network_axis_km']:.2f} km**
- maximum eligible listing distance to a main axis: **{summary['maximum_listing_distance_to_main_axis_km']:.2f} km**
- maximum eligible listing distance to any published axis: **{summary['maximum_listing_distance_to_any_network_axis_km']:.2f} km**
- nearest any-axis layer across eligible listings: {layer_counts}
- approved generic accessibility features or scores: **0**

The outside-scope listings are {outside}. They are French points in the shared Portes du Soleil cluster. A distance from those points to the nearest Swiss axis would be computable geometrically but would compare against a truncated road universe, so it remains missing and the cluster is marked partial.

## Interpretation limit

These are current Euclidean point-to-line distances, not road-network routes, distance to a usable motorway entrance, travel times, winter-reliable access, congestion, parking capacity or historical pre-treatment infrastructure. The closest line may be a main axis, ramp, connection or feeder, and physical proximity does not establish legal access. The official source is current rather than season-specific. `national_road_proximity_feature_approved` therefore remains false, `accessibility_score` remains blank, and no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/resort_national_road_proximity_context.csv`
- `data_processed/path_c_cluster_national_road_proximity_context.csv`
- `reports/national_road_proximity_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified road-axis context appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
