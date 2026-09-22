"""Audit municipality-constrained NPVM zone proxies and their cluster impact."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point
from shapely.strtree import STRtree

from build_transport_accessibility_context import (
    checked_boundary_source,
    checked_source,
    load_current_municipalities,
    load_source,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "path_c_analysis.json"
LISTINGS = ROOT / "data_processed" / "resort_transport_accessibility_context.csv"
CLUSTERS = ROOT / "data_processed" / "path_c_cluster_transport_accessibility_context.csv"
OUTPUT = ROOT / "reports" / "transport_zone_proxy_audit.csv"
SUMMARY = ROOT / "reports" / "transport_zone_proxy_audit_summary.json"
REPORT = ROOT / "reports" / "27_TRANSPORT_ZONE_PROXY_AUDIT.md"

PROXY_STATUS = "nearest_npvm_zone_intersecting_current_point_municipality"
MEASURES = [
    "road_major_center",
    "public_transport_major_center",
    "road_agglomeration",
    "public_transport_agglomeration",
]


def distance_band(value: float) -> str:
    if value <= 0.5:
        return "gt_0_to_0_5_km"
    if value <= 1.0:
        return "gt_0_5_to_1_km"
    if value <= 2.0:
        return "gt_1_to_2_km"
    return "gt_2_km"


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    zones, _ = load_source(checked_source(config))
    municipalities = load_current_municipalities(checked_boundary_source())
    listings = pd.read_csv(LISTINGS)
    proxies = listings[listings["npvm_zone_assignment_status"].eq(PROXY_STATUS)].copy()
    if len(proxies) != 98 or proxies["resort_id"].duplicated().any():
        raise ValueError("Expected 98 unique municipality-constrained NPVM proxies")

    geometries = zones["geometry"].tolist()
    zone_ids = zones["Verkehrszone_ID"].astype(int).tolist()
    zone_index = {zone_id: index for index, zone_id in enumerate(zone_ids)}
    tree = STRtree(geometries)
    transformer = Transformer.from_crs(4326, 2056, always_xy=True)
    rows = []
    for row in proxies.itertuples(index=False):
        point = Point(*transformer.transform(row.listing_longitude, row.listing_latitude))
        municipality = municipalities[int(row.point_municipality_bfs_id_2026)]
        assigned_index = zone_index[int(row.npvm_traffic_zone_id)]
        assigned_geometry = geometries[assigned_index]
        candidates = [
            int(index)
            for index in tree.query(municipality)
            if geometries[int(index)].intersects(municipality)
            and geometries[int(index)].intersection(municipality).area > 0
        ]
        nearest_same_municipality = min(
            candidates,
            key=lambda index: (
                geometries[index].distance(point),
                zone_ids[index],
            ),
        )
        distance_km = float(assigned_geometry.distance(point) / 1000)
        unrestricted_distance_km = float(geometries[int(tree.nearest(point))].distance(point) / 1000)
        overlap_km2 = float(assigned_geometry.intersection(municipality).area / 1_000_000)
        stored_difference = abs(distance_km - float(row.npvm_zone_assignment_distance_km))
        passed = (
            nearest_same_municipality == assigned_index
            and overlap_km2 > 0
            and stored_difference <= 1e-9
            and distance_km + 1e-9 >= unrestricted_distance_km
        )
        rows.append(
            {
                "resort_id": row.resort_id,
                "resort_name_canonical": row.resort_name_canonical,
                "cluster_id": row.cluster_id,
                "point_municipality_bfs_id_2026": int(row.point_municipality_bfs_id_2026),
                "assigned_npvm_traffic_zone_id": int(row.npvm_traffic_zone_id),
                "recomputed_proxy_distance_km": distance_km,
                "stored_proxy_distance_km": float(row.npvm_zone_assignment_distance_km),
                "stored_recomputed_absolute_difference_km": stored_difference,
                "unrestricted_nearest_zone_distance_km": unrestricted_distance_km,
                "same_municipality_constraint_extra_distance_km": distance_km - unrestricted_distance_km,
                "assigned_zone_municipality_overlap_area_km2": overlap_km2,
                "proxy_distance_band": distance_band(distance_km),
                "nearest_positive_area_intersection_with_current_municipality": nearest_same_municipality == assigned_index,
                "proxy_geometry_validation_passed": passed,
                "historical_npvm_zone_lineage_verified": False,
                "transport_accessibility_feature_approved": False,
            }
        )
    audit = pd.DataFrame(rows).sort_values("resort_id", kind="stable")
    if not audit["proxy_geometry_validation_passed"].all():
        raise ValueError("At least one NPVM proxy failed geometric reconstruction")
    audit.to_csv(OUTPUT, index=False, lineterminator="\n")

    clusters = pd.read_csv(CLUSTERS)
    proxy_clusters = clusters[
        clusters["cluster_listings_assigned_by_current_municipality_zone_proxy"].gt(0)
    ].copy()
    mixed = proxy_clusters[
        proxy_clusters["cluster_listings_exactly_assigned_to_npvm_zone"].gt(0)
    ]
    sensitivity = {}
    for measure in MEASURES:
        full = mixed[f"{measure}_travel_time_median_minutes"]
        exact = mixed[f"{measure}_travel_time_exact_only_median_minutes"]
        difference = (full - exact).abs().dropna()
        sensitivity[measure] = {
            "mixed_clusters_compared": int(len(difference)),
            "median_absolute_difference_minutes": float(difference.median()),
            "p90_absolute_difference_minutes": float(difference.quantile(0.9)),
            "maximum_absolute_difference_minutes": float(difference.max()),
        }
    band_counts = {
        str(key): int(value)
        for key, value in audit["proxy_distance_band"].value_counts().items()
    }
    summary = {
        "analysis_version": config["analysis_version"],
        "proxy_listing_points": int(len(audit)),
        "proxy_geometry_validation_passed": int(audit["proxy_geometry_validation_passed"].sum()),
        "proxy_distance_band_counts": band_counts,
        "median_proxy_distance_km": float(audit["recomputed_proxy_distance_km"].median()),
        "maximum_proxy_distance_km": float(audit["recomputed_proxy_distance_km"].max()),
        "proxy_clusters": int(len(proxy_clusters)),
        "proxy_only_clusters": int(proxy_clusters["cluster_listings_exactly_assigned_to_npvm_zone"].eq(0).sum()),
        "mixed_exact_and_proxy_clusters": int(len(mixed)),
        "candidate_clusters_using_proxy": int(proxy_clusters["candidate_for_path_c"].sum()),
        "candidate_clusters_proxy_only": int((proxy_clusters["candidate_for_path_c"] & proxy_clusters["cluster_listings_exactly_assigned_to_npvm_zone"].eq(0)).sum()),
        "mixed_cluster_exact_only_sensitivity": sensitivity,
        "historical_npvm_zone_lineage_verified": 0,
        "transport_accessibility_features_approved": 0,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    REPORT.write_text(
        f"""# NPVM municipality-constrained zone-proxy audit

## Geometric reconstruction

All **{len(audit)}** proxy assignments are reproduced from the checksum-verified NPVM and current municipality geometries. In every case, the stored zone is the nearest NPVM zone with a positive-area intersection with the point's independently resolved current municipality, the stored distance matches the recomputed distance, and the overlap area is positive.

Proxy distance is at most **{summary['maximum_proxy_distance_km']:.2f} km** and has a median of **{summary['median_proxy_distance_km']:.2f} km**. Distance-band counts are `{json.dumps(band_counts, ensure_ascii=False)}`. These bands are diagnostics, not quality or causal approval classes.

## Dependence and sensitivity

**{summary['proxy_clusters']}** clusters use at least one proxy. **{summary['proxy_only_clusters']}** have no exactly contained listing point, so the NPVM context for those clusters cannot be checked against an internal exact-only value. This includes **{summary['candidate_clusters_proxy_only']}** apparent Path C candidates. The remaining **{summary['mixed_exact_and_proxy_clusters']}** mixed clusters permit a limited aggregation sensitivity comparison.

For public-transport time to a major centre, the absolute difference between the all-usable median and exact-only median is **{sensitivity['public_transport_major_center']['median_absolute_difference_minutes']:.1f} minutes** at the median, **{sensitivity['public_transport_major_center']['p90_absolute_difference_minutes']:.1f} minutes** at p90 and **{sensitivity['public_transport_major_center']['maximum_absolute_difference_minutes']:.1f} minutes** at maximum. This does not validate proxy-only clusters; it only exposes observed sensitivity where exact and proxy listings coexist.

## Decision

The geometry and deterministic selection logic are validated, but the proxy is still not an observed trip origin, live route, winter-service guarantee or historical zone-lineage match. Historical lineage and transport-accessibility approval therefore remain false. No generic accessibility or composite score is populated.

## Outputs

- `reports/transport_zone_proxy_audit.csv`
- `reports/transport_zone_proxy_audit_summary.json`
""",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
