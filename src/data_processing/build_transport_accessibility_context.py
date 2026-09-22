"""Build qualified NPVM road and public-transport context for Path C.

The official ARE GeoPackage supplies modelled travel times for 7,978 NPVM
traffic zones. Each supplied resort listing coordinate is assigned only when it
falls inside exactly one zone. Cluster summaries use the minimum, median and
maximum across assigned listing points, preserving multi-listing dispersion and
leaving foreign or otherwise uncovered points explicit. These values are not
live routing, seasonal access, visitor catchments, or approved causal features.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import from_wkb, make_valid
from shapely.geometry import Point
from shapely.strtree import STRtree


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
POINT_MUNICIPALITY_PATH = ROOT / "data_processed" / "resort_point_municipality.csv"
FEATURE_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
BOUNDARY_INTERIM_DIR = ROOT / "data_interim" / "swissboundaries3d_2026"
LISTING_OUTPUT = ROOT / "data_processed" / "resort_transport_accessibility_context.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_transport_accessibility_context.csv"
DECISION_OUTPUT = ROOT / "data_processed" / "magic_pass_decision_support.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "transport_accessibility_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "22_TRANSPORT_ACCESSIBILITY_CONTEXT.md"

SOURCE_ID = "ARE_NPVM_TRAVEL_TIME_2025"
STAC_SOURCE_ID = "ARE_NPVM_TRAVEL_TIME_2025_STAC"
METHOD_SOURCE_ID = "ARE_TRANSPORT_ACCESSIBILITY_METHOD"
BOUNDARY_SOURCE_ID = "SWISSTOPO_BOUNDARIES_2026"
INTERPRETATION = (
    "npvm_2025_modelled_traffic_zone_context_not_live_routing_or_destination_catchment"
)
REFERENCE_DATE = "2025-06-30"

MEASURES = {
    "road_major_center_travel_time_minutes": "Strasse_Reisezeit_Z",
    "public_transport_major_center_travel_time_minutes": "OeV_Reisezeit_Z",
    "road_agglomeration_travel_time_minutes": "Strasse_Reisezeit_Agglo",
    "public_transport_agglomeration_travel_time_minutes": "OeV_Reisezeit_Agglo",
}
TARGETS = {
    "road_major_center": "Strasse_No_Z",
    "public_transport_major_center": "OeV_No_Z",
    "road_agglomeration": "Strasse_No_Agglo",
    "public_transport_agglomeration": "OeV_No_Agglo",
}


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


def checked_source(config: dict) -> Path:
    settings = config["transport_accessibility_context"]
    if settings != {
        "source_id": SOURCE_ID,
        "model_reference_date": REFERENCE_DATE,
        "distance_crs": "EPSG:2056",
        "point_assignment": "exact_zone_or_nearest_zone_intersecting_current_point_municipality_with_distance_diagnostic",
        "cluster_aggregation": "minimum_median_maximum_across_usable_supplied_listing_point_zone_assignments",
        "interpretation": INTERPRETATION,
    }:
        raise ValueError("Unexpected transport-accessibility configuration")

    data_metadata = exact_metadata(SOURCE_ID)
    stac_metadata = exact_metadata(STAC_SOURCE_ID)
    exact_metadata(METHOD_SOURCE_ID)
    data_path = ROOT / data_metadata["raw_file"]
    stac = json.loads((ROOT / stac_metadata["raw_file"]).read_text(encoding="utf-8"))
    if stac.get("properties", {}).get("datetime") != f"{REFERENCE_DATE}T00:00:00Z":
        raise ValueError("Unexpected ARE STAC reference date")
    asset = stac.get("assets", {}).get("reisezeit-miv_2056.gpkg", {})
    if asset.get("href") != data_metadata["url"] or asset.get("proj:epsg") != 2056:
        raise ValueError("ARE STAC asset URL or CRS does not match the cached source")
    expected_multihash = "1220" + data_metadata["sha256"]
    if asset.get("file:checksum") != expected_multihash:
        raise ValueError("ARE STAC multihash does not match the cached GeoPackage")
    return data_path


def checked_boundary_source() -> Path:
    metadata = exact_metadata(BOUNDARY_SOURCE_ID)
    archive = ROOT / metadata["raw_file"]
    BOUNDARY_INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        members = [item for item in bundle.infolist() if item.filename.lower().endswith(".gpkg")]
        if len(members) != 1:
            raise ValueError(f"Expected one boundary GeoPackage, found {len(members)}")
        output = BOUNDARY_INTERIM_DIR / Path(members[0].filename).name
        if not output.exists() or output.stat().st_size != members[0].file_size:
            bundle.extract(members[0], BOUNDARY_INTERIM_DIR)
        if bundle.testzip() is not None:
            raise RuntimeError("swissBOUNDARIES3D archive integrity failure")
    return output


def load_current_municipalities(gpkg: Path) -> dict[int, object]:
    query = (
        "SELECT bfs_nummer,geom FROM tlm_hoheitsgebiet "
        "WHERE objektart='Gemeindegebiet' AND icc='CH'"
    )
    with sqlite3.connect(gpkg.resolve().as_uri() + "?mode=ro", uri=True) as database:
        rows = database.execute(query).fetchall()
    if len(rows) != 2_110 or len({int(row[0]) for row in rows}) != 2_110:
        raise ValueError("Unexpected current Swiss municipality boundary grain")
    return {int(bfs_id): gpkg_geometry(blob) for bfs_id, blob in rows}


def load_source(gpkg: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    zone_columns = [
        "Verkehrszone_ID",
        "Strasse_No_Z",
        "Strasse_Reisezeit_Z",
        "Strasse_No_Agglo",
        "Strasse_Reisezeit_Agglo",
        "OeV_No_Z",
        "OeV_Reisezeit_Z",
        "OeV_No_Agglo",
        "OeV_Reisezeit_Agglo",
        "Strasse_Erreichb_EWAP",
        "Strasse_Erreichb_EW",
        "OeV_Erreichb_EWAP",
        "OeV_Erreichb_EW",
        "geom",
    ]
    target_columns = [
        "Agglo_No",
        "Agglo_Name",
        "Agglo_Groesse",
        "Zentren_6",
        "Verkehrszone_ID",
    ]
    with sqlite3.connect(gpkg.resolve().as_uri() + "?mode=ro", uri=True) as database:
        zones = pd.DataFrame(
            database.execute(
                "SELECT " + ",".join(zone_columns) + " FROM Reisezeit_Erreichbarkeit"
            ).fetchall(),
            columns=zone_columns,
        )
        targets = pd.DataFrame(
            database.execute(
                "SELECT " + ",".join(target_columns) + " FROM Agglomerationen_Punkte"
            ).fetchall(),
            columns=target_columns,
        )

    if len(zones) != 7_978 or zones["Verkehrszone_ID"].duplicated().any():
        raise ValueError("Unexpected ARE NPVM traffic-zone grain")
    if len(targets) != 84 or targets["Verkehrszone_ID"].duplicated().any():
        raise ValueError("Unexpected ARE centre/agglomeration lookup grain")
    source_value_columns = [*MEASURES.values(), *TARGETS.values()]
    if zones[source_value_columns].isna().any().any():
        raise ValueError("Official travel-time or target fields contain missing values")
    index_columns = [
        "Strasse_Erreichb_EWAP",
        "Strasse_Erreichb_EW",
        "OeV_Erreichb_EWAP",
        "OeV_Erreichb_EW",
    ]
    if zones[index_columns].notna().any().any():
        raise ValueError("Unexpected nonblank accessibility-index columns in travel-time source")
    zones["geometry"] = zones.pop("geom").map(gpkg_geometry)
    if zones["geometry"].map(lambda geometry: geometry.is_empty).any():
        raise ValueError("Empty ARE NPVM traffic-zone geometry")
    for column in ["Verkehrszone_ID", *TARGETS.values()]:
        zones[column] = zones[column].astype("int64")
    targets["Verkehrszone_ID"] = targets["Verkehrszone_ID"].astype("int64")
    targets["Agglo_No"] = targets["Agglo_No"].astype("int64")
    targets["Agglo_Groesse"] = targets["Agglo_Groesse"].astype("int64")
    targets["Zentren_6"] = targets["Zentren_6"].astype("int64")

    target_ids = set(targets["Verkehrszone_ID"])
    referenced_ids = set()
    for column in TARGETS.values():
        referenced_ids.update(zones[column])
    if not referenced_ids.issubset(target_ids):
        raise ValueError("Travel-time target has no centre/agglomeration lookup row")
    if int(targets["Zentren_6"].sum()) != 6:
        raise ValueError("Official lookup does not contain exactly six major centres")
    return zones, targets


def target_details(targets: pd.DataFrame) -> dict[int, dict]:
    return {
        int(row.Verkehrszone_ID): {
            "name": row.Agglo_Name,
            "published_size_class": int(row.Agglo_Groesse),
            "six_major_centres_flag": bool(row.Zentren_6),
        }
        for row in targets.itertuples(index=False)
    }


def build_listing_context(
    zones: pd.DataFrame,
    targets: pd.DataFrame,
    municipalities: dict[int, object],
    config: dict,
) -> pd.DataFrame:
    resorts = pd.read_csv(RESORT_PATH)
    point_municipality = pd.read_csv(
        POINT_MUNICIPALITY_PATH,
        usecols=["resort_id", "point_municipality_bfs_id", "selection_status"],
    )
    if len(resorts) != 271 or not resorts["resort_id"].is_unique:
        raise ValueError("Unexpected resort-master grain")
    if resorts[["latitude", "longitude", "cluster_id"]].isna().any().any():
        raise ValueError("Every resort listing must have a coordinate and cluster ID")
    if len(point_municipality) != 271 or not point_municipality["resort_id"].is_unique:
        raise ValueError("Unexpected resort point-municipality crosswalk grain")
    resorts = resorts.merge(point_municipality, on="resort_id", how="left", validate="one_to_one")
    if int(resorts["point_municipality_bfs_id"].notna().sum()) != 268:
        raise ValueError("Expected 268 supplied coordinates in a current Swiss municipality")

    geometries = zones["geometry"].tolist()
    tree = STRtree(geometries)
    coordinate_transform = Transformer.from_crs(4326, 2056, always_xy=True)
    target_lookup = target_details(targets)
    source_ids = (
        f"{SOURCE_ID}|{STAC_SOURCE_ID}|{METHOD_SOURCE_ID}|"
        f"GEOADMIN_MUNICIPALITY_IDENTIFY|{BOUNDARY_SOURCE_ID}"
    )
    settings = config["transport_accessibility_context"]
    rows = []

    for resort in resorts.itertuples(index=False):
        x, y = coordinate_transform.transform(resort.longitude, resort.latitude)
        point = Point(x, y)
        candidates = [
            int(index)
            for index in tree.query(point)
            if geometries[int(index)].covers(point)
        ]
        if len(candidates) > 1:
            strict = [index for index in candidates if point.within(geometries[index])]
            candidates = strict if len(strict) == 1 else candidates
        nearest_index = int(tree.nearest(point))
        nearest_distance_km = float(geometries[nearest_index].distance(point) / 1000)
        if len(candidates) == 1:
            zone = zones.iloc[candidates[0]]
            assignment_status = "exact_point_in_npvm_traffic_zone"
            zone_id: int | pd._libs.missing.NAType = int(zone["Verkehrszone_ID"])
            assignment_distance_km = 0.0
        elif not candidates and pd.notna(resort.point_municipality_bfs_id):
            municipality_id = int(resort.point_municipality_bfs_id)
            municipality = municipalities.get(municipality_id)
            if municipality is None:
                raise ValueError(f"Missing current municipality geometry {municipality_id}")
            municipality_zone_indices = [
                int(index)
                for index in tree.query(municipality)
                if geometries[int(index)].intersects(municipality)
                and geometries[int(index)].intersection(municipality).area > 0
            ]
            if municipality_zone_indices:
                nearest_same_municipality_index = min(
                    municipality_zone_indices,
                    key=lambda index: (
                        geometries[index].distance(point),
                        int(zones.iloc[index]["Verkehrszone_ID"]),
                    ),
                )
                zone = zones.iloc[nearest_same_municipality_index]
                assignment_status = (
                    "nearest_npvm_zone_intersecting_current_point_municipality"
                )
                zone_id = int(zone["Verkehrszone_ID"])
                assignment_distance_km = float(
                    geometries[nearest_same_municipality_index].distance(point) / 1000
                )
            else:
                zone = None
                assignment_status = (
                    "swiss_point_no_npvm_zone_intersecting_current_municipality"
                )
                zone_id = pd.NA
                assignment_distance_km = nearest_distance_km
        elif not candidates:
            zone = None
            assignment_status = "outside_swiss_current_municipality_and_npvm_coverage"
            zone_id = pd.NA
            assignment_distance_km = nearest_distance_km
        else:
            zone = None
            assignment_status = "ambiguous_multiple_covering_npvm_zones"
            zone_id = pd.NA
            assignment_distance_km = nearest_distance_km

        row = {
            "resort_id": resort.resort_id,
            "resort_name_canonical": resort.resort_name_canonical,
            "cluster_id": resort.cluster_id,
            "listing_longitude": float(resort.longitude),
            "listing_latitude": float(resort.latitude),
            "npvm_traffic_zone_id": zone_id,
            "npvm_zone_assignment_status": assignment_status,
            "distance_to_nearest_npvm_zone_km": nearest_distance_km,
            "npvm_zone_assignment_distance_km": assignment_distance_km,
            "point_municipality_bfs_id_2026": (
                int(resort.point_municipality_bfs_id)
                if pd.notna(resort.point_municipality_bfs_id)
                else pd.NA
            ),
        }
        if zone is not None:
            for output_name, source_name in MEASURES.items():
                row[output_name] = int(zone[source_name])
            for prefix, source_name in TARGETS.items():
                target_id = int(zone[source_name])
                details = target_lookup[target_id]
                row[f"{prefix}_target_zone_id"] = target_id
                row[f"{prefix}_target_name"] = details["name"]
                row[f"{prefix}_target_published_size_class"] = details[
                    "published_size_class"
                ]
                row[f"{prefix}_target_six_major_centres_flag"] = details[
                    "six_major_centres_flag"
                ]
            row["public_transport_minus_road_major_center_minutes"] = (
                row["public_transport_major_center_travel_time_minutes"]
                - row["road_major_center_travel_time_minutes"]
            )
            row["public_transport_minus_road_agglomeration_minutes"] = (
                row["public_transport_agglomeration_travel_time_minutes"]
                - row["road_agglomeration_travel_time_minutes"]
            )
            row["travel_time_values_complete"] = True
        else:
            for output_name in MEASURES:
                row[output_name] = np.nan
            for prefix in TARGETS:
                row[f"{prefix}_target_zone_id"] = pd.NA
                row[f"{prefix}_target_name"] = ""
                row[f"{prefix}_target_published_size_class"] = pd.NA
                row[f"{prefix}_target_six_major_centres_flag"] = pd.NA
            row["public_transport_minus_road_major_center_minutes"] = np.nan
            row["public_transport_minus_road_agglomeration_minutes"] = np.nan
            row["travel_time_values_complete"] = False
        row.update(
            {
                "npvm_model_reference_date": settings["model_reference_date"],
                "npvm_distance_crs": settings["distance_crs"],
                "transport_point_assignment_method": settings["point_assignment"],
                "transport_accessibility_interpretation": INTERPRETATION,
                "transport_accessibility_feature_approved": False,
                "transport_source_ids": source_ids,
            }
        )
        rows.append(row)

    context = pd.DataFrame(rows)
    if len(context) != len(resorts) or not context["resort_id"].is_unique:
        raise ValueError("Listing transport output must preserve one row per resort listing")
    usable = as_bool(context["travel_time_values_complete"])
    if not context.loc[usable, list(MEASURES)].notna().all().all():
        raise ValueError("Usable listing is missing official travel times")
    if context.loc[~usable, list(MEASURES)].notna().any().any():
        raise ValueError("Unassigned listing received travel-time values")
    return context


def pipe_unique(series: pd.Series) -> str:
    values = sorted({str(value) for value in series.dropna() if str(value)})
    return "|".join(values)


def build_cluster_context(listings: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = pd.read_csv(FEATURE_PATH)
    if len(features) != 162 or not features["cluster_id"].is_unique:
        raise ValueError("Unexpected Path C feature grain")
    if set(listings["cluster_id"]) != set(features["cluster_id"]):
        raise ValueError("Listing and Path C cluster universes differ")
    settings = config["transport_accessibility_context"]
    exact_status = "exact_point_in_npvm_traffic_zone"
    proxy_status = "nearest_npvm_zone_intersecting_current_point_municipality"
    rows = []
    for feature in features.itertuples(index=False):
        group = listings[listings["cluster_id"].eq(feature.cluster_id)].copy()
        assigned = group[as_bool(group["travel_time_values_complete"])]
        exact = group[group["npvm_zone_assignment_status"].eq(exact_status)]
        proxied = group[group["npvm_zone_assignment_status"].eq(proxy_status)]
        listing_count = int(len(group))
        assigned_count = int(len(assigned))
        if assigned_count == listing_count and len(proxied) == 0:
            status = "complete_all_listing_points_exact"
        elif assigned_count == listing_count:
            status = "complete_with_nearest_same_municipality_zone_proxy"
        elif assigned_count:
            status = "partial_foreign_or_unresolved_listing_points"
        else:
            status = "unavailable_no_listing_point_assigned"
        row = {
            "cluster_id": feature.cluster_id,
            "cluster_display_name": feature.cluster_display_name,
            "candidate_for_path_c": str(feature.candidate_for_path_c).lower() == "true",
            "cluster_listing_count": listing_count,
            "cluster_listings_assigned_to_npvm_zone": assigned_count,
            "cluster_listings_exactly_assigned_to_npvm_zone": int(len(exact)),
            "cluster_listings_assigned_by_current_municipality_zone_proxy": int(
                len(proxied)
            ),
            "cluster_listings_outside_swiss_npvm_scope": int(
                group["npvm_zone_assignment_status"]
                .eq("outside_swiss_current_municipality_and_npvm_coverage")
                .sum()
            ),
            "cluster_listings_with_ambiguous_npvm_zone": int(
                group["npvm_zone_assignment_status"].eq(
                    "ambiguous_multiple_covering_npvm_zones"
                ).sum()
            ),
            "cluster_listing_transport_assignment_share": assigned_count / listing_count,
            "cluster_listing_exact_transport_assignment_share": len(exact) / listing_count,
            "cluster_maximum_zone_proxy_distance_km": (
                float(proxied["npvm_zone_assignment_distance_km"].max())
                if len(proxied)
                else 0.0
            ),
            "cluster_npvm_traffic_zone_ids": pipe_unique(
                assigned["npvm_traffic_zone_id"].astype("Int64").astype("string")
            ),
            "unassigned_resort_ids": pipe_unique(
                group.loc[
                    ~as_bool(group["travel_time_values_complete"]), "resort_id"
                ]
            ),
            "cluster_transport_context_status": status,
        }
        for measure in MEASURES:
            values = assigned[measure].dropna().astype(float)
            row[f"{measure.removesuffix('_minutes')}_minimum_minutes"] = (
                float(values.min()) if len(values) else np.nan
            )
            row[f"{measure.removesuffix('_minutes')}_median_minutes"] = (
                float(values.median()) if len(values) else np.nan
            )
            row[f"{measure.removesuffix('_minutes')}_maximum_minutes"] = (
                float(values.max()) if len(values) else np.nan
            )
            row[f"{measure.removesuffix('_minutes')}_range_minutes"] = (
                float(values.max() - values.min()) if len(values) else np.nan
            )
            exact_values = exact[measure].dropna().astype(float)
            row[f"{measure.removesuffix('_minutes')}_exact_only_median_minutes"] = (
                float(exact_values.median()) if len(exact_values) else np.nan
            )
        for prefix in TARGETS:
            row[f"{prefix}_target_names"] = pipe_unique(
                assigned[f"{prefix}_target_name"]
            )
        for gap in [
            "public_transport_minus_road_major_center_minutes",
            "public_transport_minus_road_agglomeration_minutes",
        ]:
            row[f"{gap.removesuffix('_minutes')}_median_minutes"] = (
                float(assigned[gap].median()) if len(assigned) else np.nan
            )
        row.update(
            {
                "npvm_model_reference_date": settings["model_reference_date"],
                "npvm_distance_crs": settings["distance_crs"],
                "transport_point_assignment_method": settings["point_assignment"],
                "transport_cluster_aggregation_method": settings["cluster_aggregation"],
                "transport_accessibility_interpretation": INTERPRETATION,
                "transport_accessibility_feature_approved": False,
                "transport_source_ids": (
                    f"{SOURCE_ID}|{STAC_SOURCE_ID}|{METHOD_SOURCE_ID}|"
                    f"GEOADMIN_MUNICIPALITY_IDENTIFY|{BOUNDARY_SOURCE_ID}"
                ),
            }
        )
        rows.append(row)

    context = pd.DataFrame(rows)
    if len(context) != len(features) or not context["cluster_id"].is_unique:
        raise ValueError("Cluster transport output must preserve one row per Path C cluster")
    if int(context["cluster_listing_count"].sum()) != len(listings):
        raise ValueError("Cluster transport aggregation lost resort listings")
    for measure in MEASURES:
        stem = measure.removesuffix("_minutes")
        complete = context[f"{stem}_median_minutes"].notna()
        if not (
            context.loc[complete, f"{stem}_minimum_minutes"]
            <= context.loc[complete, f"{stem}_median_minutes"]
        ).all() or not (
            context.loc[complete, f"{stem}_median_minutes"]
            <= context.loc[complete, f"{stem}_maximum_minutes"]
        ).all():
            raise ValueError(f"Invalid min/median/max order for {measure}")
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
    if as_bool(decision["transport_accessibility_feature_approved"]).any():
        raise ValueError("Transport accessibility was unexpectedly approved")
    DECISION_OUTPUT.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    gpkg = checked_source(config)
    municipality_gpkg = checked_boundary_source()
    zones, targets = load_source(gpkg)
    listings = build_listing_context(
        zones,
        targets,
        load_current_municipalities(municipality_gpkg),
        config,
    )
    listings.to_csv(LISTING_OUTPUT, index=False, lineterminator="\n")
    clusters = build_cluster_context(listings, config)
    clusters.to_csv(CLUSTER_OUTPUT, index=False, lineterminator="\n")
    enrich_decision_support(clusters)

    exact = listings["npvm_zone_assignment_status"].eq("exact_point_in_npvm_traffic_zone")
    proxied = listings["npvm_zone_assignment_status"].eq(
        "nearest_npvm_zone_intersecting_current_point_municipality"
    )
    usable = as_bool(listings["travel_time_values_complete"])
    candidates = clusters[as_bool(clusters["candidate_for_path_c"])]
    complete_clusters = clusters["cluster_transport_context_status"].eq(
        "complete_all_listing_points_assigned"
    )
    summary = {
        "analysis_version": config["analysis_version"],
        "npvm_model_reference_date": REFERENCE_DATE,
        "npvm_traffic_zones": int(len(zones)),
        "centre_and_agglomeration_targets": int(len(targets)),
        "six_major_centres": int(targets["Zentren_6"].sum()),
        "resort_listings": int(len(listings)),
        "resort_listings_exactly_assigned": int(exact.sum()),
        "resort_listings_assigned_by_current_municipality_zone_proxy": int(
            proxied.sum()
        ),
        "resort_listings_with_usable_travel_time": int(usable.sum()),
        "resort_listings_outside_swiss_npvm_scope": int((~usable).sum()),
        "resort_listings_ambiguous": int(
            listings["npvm_zone_assignment_status"]
            .eq("ambiguous_multiple_covering_npvm_zones")
            .sum()
        ),
        "unassigned_resort_ids": listings.loc[~usable, "resort_id"].tolist(),
        "path_c_clusters": int(len(clusters)),
        "path_c_clusters_complete_all_listing_points_exact": int(
            clusters["cluster_transport_context_status"]
            .eq("complete_all_listing_points_exact")
            .sum()
        ),
        "path_c_clusters_complete_with_zone_proxy": int(
            clusters["cluster_transport_context_status"]
            .eq("complete_with_nearest_same_municipality_zone_proxy")
            .sum()
        ),
        "path_c_clusters_partial": int(
            clusters["cluster_transport_context_status"]
            .eq("partial_foreign_or_unresolved_listing_points")
            .sum()
        ),
        "path_c_clusters_unavailable": int(
            clusters["cluster_transport_context_status"]
            .eq("unavailable_no_listing_point_assigned")
            .sum()
        ),
        "path_c_candidates": int(len(candidates)),
        "path_c_candidates_with_usable_travel_time": int(
            candidates["cluster_transport_context_status"]
            .ne("unavailable_no_listing_point_assigned")
            .sum()
        ),
        "maximum_current_municipality_zone_proxy_distance_km": float(
            listings.loc[proxied, "npvm_zone_assignment_distance_km"].max()
        ),
        "median_cluster_median_road_major_center_minutes": float(
            clusters["road_major_center_travel_time_median_minutes"].median()
        ),
        "median_cluster_median_public_transport_major_center_minutes": float(
            clusters["public_transport_major_center_travel_time_median_minutes"].median()
        ),
        "median_cluster_median_road_agglomeration_minutes": float(
            clusters["road_agglomeration_travel_time_median_minutes"].median()
        ),
        "median_cluster_median_public_transport_agglomeration_minutes": float(
            clusters["public_transport_agglomeration_travel_time_median_minutes"].median()
        ),
        "transport_accessibility_features_approved": int(
            as_bool(clusters["transport_accessibility_feature_approved"]).sum()
        ),
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    unassigned = listings.loc[
        ~usable, ["resort_name_canonical", "resort_id", "cluster_id"]
    ]
    unassigned_text = ", ".join(
        f"{row.resort_name_canonical} (`{row.resort_id}`)"
        for row in unassigned.itertuples(index=False)
    ) or "none"
    report = f"""# Qualified NPVM transport accessibility context

## Scope

The official ARE GeoPackage contains **{summary['npvm_traffic_zones']:,}** National Passenger Traffic Model (NPVM) traffic zones and **{summary['centre_and_agglomeration_targets']:,}** named centre/agglomeration targets. Its STAC item dates the model output to **{REFERENCE_DATE}**. For every zone, the source provides modelled travel time by road and public transport to the fastest of the six major centres (Basel, Bern, Geneva, Lausanne, Lugano and Zurich) and to the fastest agglomeration or core municipality.

Each of the 271 supplied resort-listing coordinates is projected to EPSG:2056. Exact point-in-zone containment is used where available. Because NPVM zone polygons do not continuously cover high-alpine terrain, a Swiss point outside every zone is linked to the nearest zone that spatially intersects its independently resolved current municipality; the assignment distance remains explicit. No global nearest-zone assignment is used. Cluster values are minimum, median and maximum across usable listing-point assignments; this preserves multi-listing dispersion instead of assigning the artificial cluster-median coordinate to one zone. Exact-only medians are retained as a sensitivity reference where available.

## Coverage

- resort listings exactly assigned to one NPVM zone: **{summary['resort_listings_exactly_assigned']:,} / {summary['resort_listings']:,}**
- Swiss resort listings assigned to the nearest zone intersecting their current municipality: **{summary['resort_listings_assigned_by_current_municipality_zone_proxy']:,}**
- resort listings with a usable travel-time value: **{summary['resort_listings_with_usable_travel_time']:,} / {summary['resort_listings']:,}**
- listings outside the Swiss municipality/NPVM scope: **{summary['resort_listings_outside_swiss_npvm_scope']:,}**
- ambiguous multi-zone listing assignments: **{summary['resort_listings_ambiguous']:,}**
- linked Path C clusters with every listing point assigned exactly: **{summary['path_c_clusters_complete_all_listing_points_exact']:,} / {summary['path_c_clusters']:,}**
- linked clusters complete after the within-municipality zone proxy: **{summary['path_c_clusters_complete_with_zone_proxy']:,}**
- partially covered clusters: **{summary['path_c_clusters_partial']:,}**
- apparent Path C candidates with usable travel-time context: **{summary['path_c_candidates_with_usable_travel_time']:,} / {summary['path_c_candidates']:,}**
- maximum reported within-municipality proxy distance: **{summary['maximum_current_municipality_zone_proxy_distance_km']:.2f} km**
- approved generic transport-accessibility features or scores: **0**

The uncovered directory listings are {unassigned_text}. They are retained without imputation. Their shared cluster can still have Swiss listing points with valid values, so its coverage status remains partial rather than silently complete.

## Descriptive reference values

Across the 162 cluster summaries, the median of the cluster-level median travel times is **{summary['median_cluster_median_road_major_center_minutes']:.1f} minutes by road** and **{summary['median_cluster_median_public_transport_major_center_minutes']:.1f} minutes by public transport** to a major centre. The analogous values to the fastest agglomeration/core municipality are **{summary['median_cluster_median_road_agglomeration_minutes']:.1f}** and **{summary['median_cluster_median_public_transport_agglomeration_minutes']:.1f} minutes**.

## Interpretation limit

These are NPVM traffic-zone model outputs, not live door-to-door routes, rail-only times, timetables, waiting-time guarantees, access from a particular valley station, or winter road-closure measures. For 98 Swiss high-alpine points, the nearest zone intersecting the same current municipality is a transparent spatial proxy; it is not an observed route origin, and municipality boundary changes can differ from the NPVM zone lineage. A supplied resort coordinate may represent a listing or ski area rather than the actual visitor arrival node. Cluster aggregation describes the supplied directory points and does not establish a destination catchment. Therefore `transport_accessibility_feature_approved` remains false, the generic `accessibility_score` remains blank, and no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/resort_transport_accessibility_context.csv`
- `data_processed/path_c_cluster_transport_accessibility_context.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified transport columns appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
