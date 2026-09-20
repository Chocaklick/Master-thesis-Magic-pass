"""Prepare point-location queries, not overnight-stay exposure assignments."""
import csv
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]


def main():
    queries = []
    with (ROOT / "data_processed/resort_master.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            params = {"geometryType": "esriGeometryPoint", "geometry": f"{row['longitude']},{row['latitude']}",
                "layers": "all:ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill", "returnGeometry": "false",
                "sr": "4326", "tolerance": "0", "mapExtent": "0,0,0,0", "imageDisplay": "0,0,0", "lang": "fr"}
            url = "https://api3.geo.admin.ch/rest/services/ech/MapServer/identify?" + urlencode(params)
            queries.append({"source_id": "GEO_POINT_" + hashlib.sha256(url.encode()).hexdigest()[:12],
                "url": url, "suffix": "json", "organisation": "swisstopo / geo.admin.ch",
                "description": "Current municipality containing supplied resort coordinate; not tourism exposure",
                "resort_id": row["resort_id"], "api_parameters": params})
    (ROOT / "config/municipality_queries.json").write_text(json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
