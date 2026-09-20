"""Validate existing memberships against original line geometries; never recluster."""
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MPL_CACHE = ROOT / "data_interim" / "matplotlib"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyproj import Transformer
from shapely import from_wkb
from shapely.geometry import Point
from shapely.ops import unary_union

sys.path.insert(0, str(ROOT / "src/data_processing"))
from audit_existing_data import read_csv


def gpkg_geometry(blob):
    assert blob[:2] == b"GP"
    envelope_code = (blob[3] >> 1) & 7
    envelope_bytes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope_code]
    return from_wkb(blob[8 + envelope_bytes:])


def main():
    p = ROOT / "data_raw/bahnen-winter_2056.gpkg"
    with sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True) as db:
        lifts = {fid: gpkg_geometry(blob) for fid, blob in db.execute("SELECT fid,geom FROM transport_winter_2056")}
        columns = db.execute("PRAGMA table_info(transport_winter_2056)").fetchall()
    features = json.loads((ROOT / "data_raw/stations_ski_clusters_gps_bergfex.geojson").read_text(encoding="utf-8"))["features"]
    cluster_members = {f["properties"]["cluster_id"]: f["properties"]["lift_fids"] for f in features}
    assert set(fid for ids in cluster_members.values() for fid in ids) == set(lifts)
    geometries = {cid: unary_union([lifts[fid] for fid in ids]) for cid, ids in cluster_members.items()}
    assignments = read_csv(ROOT / "data_raw/stations_ski_assignations_clusters_gps_bergfex.csv")
    transform = Transformer.from_crs(4326, 2056, always_xy=True)
    records = []
    for row in assignments.to_dict("records"):
        x, y = transform.transform(float(row["lon"]), float(row["lat"]))
        point = Point(x, y)
        distance = point.distance(geometries[row["cluster_id"]])
        all_distances = {cid: point.distance(geom) for cid, geom in geometries.items()}
        nearest = min(all_distances, key=all_distances.get)
        records.append({"resort_id": row["ski_id"], "resort_name": row["ski_name"], "cluster_id": row["cluster_id"],
            "stored_distance_m": float(row["distance_m"]), "recomputed_distance_m": round(distance, 3),
            "distance_difference_m": round(distance - float(row["distance_m"]), 3),
            "nearest_cluster_recomputed": nearest, "assigned_is_nearest": nearest == row["cluster_id"],
            "assignment_quality": row["assignment_quality"], "latitude": row["lat"], "longitude": row["lon"]})
    frame = pd.DataFrame(records)
    frame.to_csv(ROOT / "reports/cluster_geometry_validation.csv", index=False)
    print(json.dumps({"lift_count": len(lifts), "invalid_lift_geometries": sum(not g.is_valid for g in lifts.values()),
        "distance_max_absolute_difference_m": frame.distance_difference_m.abs().max(),
        "assignments_not_nearest": int((~frame.assigned_is_nearest).sum()),
        "gpkg_schema": columns}, ensure_ascii=False, indent=2))
    fig, ax = plt.subplots(figsize=(10, 6))
    for label, color in [("confident", "#397e8b"), ("warning", "#d59a23"), ("review", "#bd3c34")]:
        subset = frame[frame.assignment_quality == label]
        ax.scatter(subset.longitude.astype(float), subset.latitude.astype(float), s=18, c=color, label=f"{label}: {len(subset)}", alpha=.8)
    ax.set(xlabel="Longitude (WGS84)", ylabel="Latitude (WGS84)",
           title="Existing resort coordinates and source assignment flags\nIncludes border-region listings; flags are not independent validation")
    ax.legend()
    ax.grid(alpha=.2)
    fig.tight_layout()
    fig.savefig(ROOT / "figures/existing_assignment_flags.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
