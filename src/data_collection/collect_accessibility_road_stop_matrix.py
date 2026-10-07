"""Run the secure matrix engine in an isolated stop-to-stop dataset namespace.

No historical matrix/raw/checkpoint or administrative/parking result is replaced.
Separate process entry point, never configure another dataset during collection.
"""
import sys
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_accessibility_road_matrix as engine
from src.data_processing.prepare_accessibility_road_stop_reference import OUTPUTS, REFINEMENT, SOURCE
from src.data_processing.prepare_accessibility_road_stop_reference import CONFIG, SUMMARY, sha


def configure():
    engine.OUTPUTS = OUTPUTS
    engine.PROTECTED = engine.PROTECTED + REFINEMENT
    engine.ORIGIN_READY = engine.ARRIVAL_READY = "verified_existing_tp_stop_coordinate"
    engine.INVENTORY_SOURCE = SOURCE
    engine.SOURCE = "ORS_DRIVING_CAR_TP_STOP_MATRIX_2026"
    engine.TABLES = {
        "accessibility_road_stop_directional": "data_processed/accessibility_road_stop_directional.csv",
        "accessibility_road_stop_pairs": "data_processed/accessibility_road_stop_pairs.csv",
    }
    engine.SUMMARY = "reports/accessibility_road_stop_collection_summary.json"
    engine.CACHE_DIRECTORY = "data_interim/accessibility_road_stop_ors"
    engine.RAW_DIRECTORY = "data_external/accessibility_road_stop_ors"
    engine.MEASUREMENT_LABEL = "arrêt communal → arrêt de station"
    engine.RESUME_COMMAND = ".venv/Scripts/python.exe src/data_collection/collect_accessibility_road_stop_matrix.py --execute --max-new-batches 48"
    engine.EXTRA_INPUTS = [CONFIG, SUMMARY]
    engine.ENTRY_POINT = "src/data_collection/collect_accessibility_road_stop_matrix.py"
    method = json.loads((ROOT / CONFIG).read_text(encoding="utf-8"))
    origins, arrivals = [pd.read_csv(ROOT / p, dtype={"selected_stop_id": str}) for p in OUTPUTS.values()]
    origins = origins.set_index("municipality_bfs_id")
    arrivals = arrivals.set_index("access_point_id")
    approved = set()
    for pair in method.get("approved_identical_stop_zero_pairs", []):
        origin = origins.loc[pair["municipality_bfs_id"]]
        arrival = arrivals.loc[pair["access_point_id"]]
        if origin.selected_stop_id != pair["selected_stop_id"] or arrival.selected_stop_id != pair["selected_stop_id"]:
            raise ValueError("Approved zero pair no longer uses the same exact TP stop ID")
        if (origin.road_origin_longitude, origin.road_origin_latitude) != (arrival.road_arrival_longitude, arrival.road_arrival_latitude):
            raise ValueError("Approved same-stop coordinates do not actually coincide")
        approved.add((pair["municipality_bfs_id"], pair["access_point_id"]))
    engine.APPROVED_ZERO_PAIRS = approved


def validate_preparation():
    summary = json.loads((ROOT / SUMMARY).read_text(encoding="utf-8"))
    for p, value in {**summary["input_sha256"], **summary["output_sha256"]}.items():
        if sha(p) != value:
            raise ValueError("Stop-coordinate preparation changed; verify/rebuild before collection: " + p)


if __name__ == "__main__":
    validate_preparation()
    configure()
    engine.main()
