"""Prepare the approved stop-to-stop car proxy from unchanged TP stop IDs.

No network call, stop reselection, municipal-centroid or parking substitution.
Coordinates come from the same BAV operating points used for TP node selection.
"""
import json
import sys
from pathlib import Path

import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_accessibility_road_reference import prepare_origins, sha, PROTECTED
from src.data_processing.build_public_transport_stop_context import checked_source, load_stops, exact_metadata
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.atomic_csv_output import write_csv

SOURCE = "DERIVED_ACCESSIBILITY_ROAD_STOP_ENDPOINTS_2026"
CONFIG = "config/accessibility_road_stop_reference_method.json"
SUMMARY = "reports/accessibility_road_stop_preparation_summary.json"
OUTPUTS = {
    "accessibility_road_stop_origins": "reports/accessibility_road_stop_origins.csv",
    "accessibility_road_stop_arrivals": "reports/accessibility_road_stop_arrivals.csv",
}
INPUTS = [CONFIG, "config/path_c_analysis.json", "reports/public_transport_journey_nodes.csv",
    "reports/accessibility_station_access_nodes.csv", "data_processed/accessibility_municipality_month_exposure_territorial.csv"]
REFINEMENT = ["reports/accessibility_road_origin_review.csv", "reports/accessibility_road_station_arrival_review.csv",
    "reports/accessibility_road_reference_preparation_summary.json", "data_processed/accessibility_road_reference_directional.csv",
    "data_processed/accessibility_road_reference_pairs.csv", "reports/accessibility_road_reference_collection_summary.json"]


def endpoint_frames(nodes, mapping, access, stops):
    if not stops.Numero.is_unique or access.access_point_id.duplicated().any():
        raise ValueError("Nonunique source stop/access ID; no implicit selection")
    origins = prepare_origins(nodes, mapping)
    pool = stops.set_index("Numero")
    transformer = Transformer.from_crs(2056, 4326, always_xy=True)
    origin_rows = []
    for row in origins.itertuples(index=False):
        records = json.loads(row.legacy_tp_origin_records)
        stop_ids = {r["selected_stop_id"] for r in records}
        if len(stop_ids) != 1:
            raise ValueError("Territorial histories have different TP origins; no arbitrary averaging")
        stop_id = next(iter(stop_ids))
        if stop_id not in pool.index:
            raise ValueError("Existing selected TP stop missing from checked official coordinates")
        point = pool.loc[stop_id]
        lon, lat = transformer.transform(float(point.E), float(point.N))
        origin_rows.append(dict(municipality_bfs_id=row.municipality_bfs_id,
            source_municipality_bfs_ids=row.source_municipality_bfs_ids,
            municipality_names_source=row.municipality_names_source, legacy_tp_origin_records=row.legacy_tp_origin_records,
            selected_stop_id=stop_id, selected_stop_name=point.Nom,
            bav_easting_2056=float(point.E), bav_northing_2056=float(point.N),
            bav_xtf_id=point.xtf_id, coordinate_state_date="2026-09-20",
            road_origin_longitude=lon, road_origin_latitude=lat,
            road_origin_status="verified_existing_tp_stop_coordinate",
            road_origin_source_id="BAV_PUBLIC_TRANSPORT_STOPS_2026",
            road_origin_coordinate_source_id="BAV_PUBLIC_TRANSPORT_STOPS_2026", source_id=SOURCE))
    arrivals = []
    for row in access.itertuples(index=False):
        if row.selected_stop_id not in pool.index:
            raise ValueError("Existing station TP stop missing from checked official coordinates")
        point = pool.loc[row.selected_stop_id]
        lon, lat = transformer.transform(float(point.E), float(point.N))
        arrivals.append(dict(access_point_id=row.access_point_id, access_point_name=row.access_point_name,
            station_group_id=row.station_group_id, station_group_name=row.station_group_name,
            component_resort_id=row.component_resort_id,
            selected_stop_id=row.selected_stop_id, selected_stop_name=point.Nom,
            bav_easting_2056=float(point.E), bav_northing_2056=float(point.N),
            bav_xtf_id=point.xtf_id, coordinate_state_date="2026-09-20",
            road_arrival_longitude=lon, road_arrival_latitude=lat,
            road_arrival_status="verified_existing_tp_stop_coordinate",
            road_arrival_source_id="BAV_PUBLIC_TRANSPORT_STOPS_2026",
            road_arrival_coordinate_source_id="BAV_PUBLIC_TRANSPORT_STOPS_2026",
            winter_access_status="not_yet_verified", final_walk_minutes=None, source_id=SOURCE))
    return dict(zip(OUTPUTS, [pd.DataFrame(origin_rows), pd.DataFrame(arrivals)]))


DESCRIPTIONS = {
    "municipality_bfs_id": ("Approved territorial hotel-panel BFS ID, Moutier bridge retained", "identifier"),
    "source_municipality_bfs_ids": ("Unaltered source historical BFS IDs in this territory, pipe separated", "identifier list"),
    "municipality_names_source": ("Unaltered source municipality names, not a matching key", "text"),
    "legacy_tp_origin_records": ("Original TP stop ID/name and selection rule for every source history", "JSON"),
    "access_point_id": ("Unchanged station access identifier, not a new parking point", "identifier"),
    "access_point_name": ("Original station access label", "text"),
    "station_group_id": ("Unchanged existing station group identifier", "identifier"),
    "station_group_name": ("Original station group label", "text"),
    "component_resort_id": ("Original component resort ID if available", "identifier"),
    "selected_stop_id": ("Exact existing selected TP stop ID, matched to official BAV Numero", "identifier"),
    "selected_stop_name": ("Official operating-point name for the unchanged selected stop ID", "text"),
    "bav_easting_2056": ("Original official stop E, LV95, not municipality or station-reference centroid", "metres EPSG:2056"),
    "bav_northing_2056": ("Original official stop N, LV95", "metres EPSG:2056"),
    "bav_xtf_id": ("Original official operating-point internal ID, retained alongside Numero", "identifier"),
    "coordinate_state_date": ("Official BAV coordinate source-state date, not collection or journey date", "date"),
    "road_origin_latitude": ("WGS84 latitude transformed from official unchanged communal TP stop N,E", "decimal degrees WGS84"),
    "road_origin_longitude": ("WGS84 longitude transformed from official unchanged communal TP stop E,N", "decimal degrees WGS84"),
    "road_arrival_latitude": ("WGS84 latitude of unchanged station TP stop, not resort reference/parking", "decimal degrees WGS84"),
    "road_arrival_longitude": ("WGS84 longitude of unchanged station TP stop, not resort reference/parking", "decimal degrees WGS84"),
    "road_origin_status": ("Existing TP stop coordinate verified; NOT verified town-hall/driveway access", "category"),
    "road_arrival_status": ("Existing TP stop coordinate verified; NOT verified lift parking access", "category"),
    "road_origin_source_id": ("Official original coordinate source ID", "identifier"),
    "road_origin_coordinate_source_id": ("Official original coordinate source ID", "identifier"),
    "road_arrival_source_id": ("Official original coordinate source ID", "identifier"),
    "road_arrival_coordinate_source_id": ("Official original coordinate source ID", "identifier"),
    "winter_access_status": ("Winter road restrictions/legal accessibility not established", "category"),
    "final_walk_minutes": ("Unresearched final walk remains missing, not zero, not included in stop-to-stop driving proxy", "minutes"),
    "source_id": ("Derived stop-endpoint provenance identifier", "identifier"),
}


def register(frames, original):
    path = ROOT / "metadata/data_sources_master.csv"
    master = pd.read_csv(path, dtype=str, keep_default_na=False)
    row = dict(source_id=SOURCE, variable_name="road_stop_endpoint_coordinates",
        variable_description="Approved arrêt communal → arrêt de station road proxy, unchanged selected TP stop IDs",
        source_organisation="Thesis project; BAV/OFT official operating points", source_dataset_name="Derived exact selected TP-stop coordinates",
        source_page_url=original.get("url", original.get("source_url", "")), local_raw_file=original["raw_file"],
        retrieval_method="Reuse SHA-verified official archive without download", retrieval_date="2026-10-07",
        processed_file="|".join(OUTPUTS.values()), geographic_level="185 territories /75 existing access IDs /71 unchanged groups",
        temporal_resolution="BAV state2026-09-20, not historical lift access", unit="EPSG:2056 metres and WGS84 degrees",
        license="Inherited BAV source terms; retain attribution", access_conditions="Local immutable official source",
        transformation_applied="Exact selected_stop_id = Numero; same E,N transformed EPSG:2056→4326 always_xy; no new stop selection",
        quality_notes="TP selected stops, not main municipal centres or station parking. No inferred walk, winter validity or analytical exclusion.",
        confidence_level="exact stop identity and coordinate lineage; car access unresolved until routing",
        manual_verification="Explicit user endpoint relaxation2026-10-07; Moutier stop ID8500105 identical across source histories",
        notes="Parent sources BAV_PUBLIC_TRANSPORT_STOPS_2026|DERIVED_ACCESSIBILITY_STATION_GROUPS|DERIVED_ACCESSIBILITY_TERRITORIAL_MOUTIER_BRIDGE; original SHA256=" + original["sha256"])
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([row]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(""), path)
    path = ROOT / "metadata/data_dictionary.csv"
    dictionary = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = []
    for table, frame in frames.items():
        for field in frame:
            description, unit = DESCRIPTIONS[field]
            rows.append(dict(variable=field, table=table, description=description, unit=unit,
                data_type=str(frame[field].dtype), geographic_level="territorial commune or existing station-access stop",
                temporal_level="official coordinate snapshot2026-09-20", source_id=SOURCE, raw_or_derived="derived",
                formula="Exact unchanged TP stop ID; official BAV E,N transformed to WGS84, no imputation",
                causal_role="descriptive access proxy, not canonical exposure", missing_share=f"{frame[field].isna().mean():.6f}",
                notes="No commune excluded; administrative/parking refinements retained separately and deferred."))
    write_csv(pd.concat([dictionary[~dictionary.table.isin(OUTPUTS)], pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(""), path)


def main():
    config = json.loads((ROOT / CONFIG).read_text(encoding="utf-8"))
    if config["measurement_label"] != "arrêt communal → arrêt de station":
        raise ValueError("Unexpected approved endpoint definition")
    protected = {p: sha(p) for p in PROTECTED + REFINEMENT}
    if (ROOT / SUMMARY).exists():
        old = json.loads((ROOT / SUMMARY).read_text(encoding="utf-8"))
        for p, value in old["output_sha256"].items():
            if sha(p) != value:
                raise ValueError("Preserve manually changed derived endpoint output before regeneration")
    stops, _, _ = load_stops(checked_source(json.loads((ROOT / INPUTS[1]).read_text(encoding="utf-8"))))
    nodes = pd.read_csv(ROOT / INPUTS[2], dtype={"selected_stop_id": str})
    access = pd.read_csv(ROOT / INPUTS[3], dtype={"selected_stop_id": str})
    mapping = pd.read_csv(ROOT / INPUTS[4], usecols=["source_municipality_bfs_id", "municipality_bfs_id"])
    frames = endpoint_frames(nodes, mapping, access, stops)
    origins, arrivals = frames.values()
    if len(origins) != 185 or len(arrivals) != 75 or arrivals.station_group_id.nunique() != 71:
        raise ValueError("Changed study universe; never implicitly exclude communes or access IDs")
    for table, frame in frames.items():
        frame.to_csv(ROOT / OUTPUTS[table], index=False, lineterminator="\n")
    original = exact_metadata("BAV_PUBLIC_TRANSPORT_STOPS_2026")
    register(frames, original)
    summary = dict(status="all_existing_tp_stops_resolved_no_routing_yet", measurement_label=config["measurement_label"],
        municipality_territories=len(origins), source_histories=186, access_points=len(arrivals), station_groups=71,
        missing_origin_coordinates=int(origins.road_origin_latitude.isna().sum()), missing_arrival_coordinates=int(arrivals.road_arrival_latitude.isna().sum()),
        coordinate_source_id="BAV_PUBLIC_TRANSPORT_STOPS_2026", coordinate_original_sha256=original["sha256"],
        input_sha256={p: sha(p) for p in INPUTS}, output_sha256={p: sha(p) for p in OUTPUTS.values()},
        protected_legacy_and_refinement_sha256=protected, canonical_outputs_changed=False,
        builder_sha256=sha("src/data_processing/prepare_accessibility_road_stop_reference.py"))
    if protected != {p: sha(p) for p in protected}:
        raise ValueError("Historical/refinement results changed")
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["status", "municipality_territories", "access_points", "missing_origin_coordinates", "missing_arrival_coordinates"]}))


if __name__ == "__main__":
    main()
