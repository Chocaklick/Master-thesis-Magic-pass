"""Document stop-to-road raccordements without acceptance cutoffs/exclusions.

Service-reported snap distances and independent WGS84 geodesic displacements
are separate observations, not walking durations or proof of legal car access.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_accessibility_road_reference import sha
from src.data_processing.prepare_accessibility_road_stop_reference import OUTPUTS as ENDPOINTS
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.atomic_csv_output import write_csv

SOURCE = "DERIVED_ACCESSIBILITY_ROAD_STOP_SNAPPING_AUDIT_2026"
INPUT = "data_processed/accessibility_road_stop_directional.csv"
COLLECTION = "reports/accessibility_road_stop_collection_summary.json"
OUTPUTS = {
    "accessibility_road_stop_snapping_observations": "reports/accessibility_road_stop_snapping_observations.csv",
    "accessibility_road_stop_snapping_endpoints": "reports/accessibility_road_stop_snapping_endpoints.csv",
    "accessibility_road_stop_route_anomalies": "reports/accessibility_road_stop_route_anomalies.csv",
}
SUMMARY = "reports/accessibility_road_stop_snapping_summary.json"


def displacement(input_lon, input_lat, resolved):
    if pd.isna(resolved):
        return np.nan
    value = json.loads(resolved)
    if value is None or len(value) != 2 or not all(v is not None and np.isfinite(v) for v in value):
        return np.nan
    return Geod(ellps="WGS84").inv(input_lon, input_lat, value[0], value[1])[2]


def audit(directional, origins, arrivals):
    rows = []
    for role, endpoints, key, coordinate_prefix in [
        ("communal_stop", origins, "municipality_bfs_id", "road_origin"),
        ("station_stop", arrivals, "access_point_id", "road_arrival")]:
        for endpoint in endpoints.to_dict("records"):
            cells = directional[directional[key].eq(endpoint[key])]
            # An endpoint occurs once per partner; collapse only identical
            # observations within a request/role, never average different snaps.
            for direction in ("outbound", "return"):
                position = "origin" if (role == "communal_stop") == (direction == "outbound") else "destination"
                subset = cells[cells.direction.eq(direction) & cells.request_id.notna()]
                fields = ["request_id", position + "_snap_distance_metres", "resolved_" + position + "_location", "graph_date", "engine_version"]
                subset = subset[fields].drop_duplicates()
                for record in subset.to_dict("records"):
                    snap = record[position + "_snap_distance_metres"]
                    resolved = record["resolved_" + position + "_location"]
                    distance = displacement(endpoint[coordinate_prefix + "_longitude"], endpoint[coordinate_prefix + "_latitude"], resolved)
                    rows.append(dict(endpoint_role=role, endpoint_id=str(endpoint[key]),
                        endpoint_name=endpoint.get("municipality_names_source", endpoint.get("access_point_name")),
                        selected_stop_id=endpoint["selected_stop_id"], selected_stop_name=endpoint["selected_stop_name"],
                        direction=direction, request_id=record["request_id"],
                        input_longitude=endpoint[coordinate_prefix + "_longitude"], input_latitude=endpoint[coordinate_prefix + "_latitude"],
                        resolved_location=resolved, reported_snap_distance_metres=snap,
                        geodesic_displacement_metres=distance, missing_snap_distance=pd.isna(snap),
                        missing_resolved_coordinate=pd.isna(distance), graph_date=record["graph_date"], engine_version=record["engine_version"], source_id=SOURCE))
    fields = ["endpoint_role", "endpoint_id", "endpoint_name", "selected_stop_id", "selected_stop_name", "direction", "request_id",
        "input_longitude", "input_latitude", "resolved_location", "reported_snap_distance_metres", "geodesic_displacement_metres",
        "missing_snap_distance", "missing_resolved_coordinate", "graph_date", "engine_version", "source_id"]
    observations = pd.DataFrame(rows, columns=fields)
    endpoint_rows = []
    for role, endpoints, key in [("communal_stop", origins, "municipality_bfs_id"), ("station_stop", arrivals, "access_point_id")]:
        for endpoint in endpoints.to_dict("records"):
            observed = observations[observations.endpoint_role.eq(role) & observations.endpoint_id.eq(str(endpoint[key]))]
            snaps = pd.to_numeric(observed.reported_snap_distance_metres)
            locations = observed.resolved_location.dropna()
            endpoint_rows.append(dict(endpoint_role=role, endpoint_id=str(endpoint[key]),
                endpoint_name=endpoint.get("municipality_names_source", endpoint.get("access_point_name")),
                selected_stop_id=endpoint["selected_stop_id"], selected_stop_name=endpoint["selected_stop_name"],
                observations=len(observed), min_reported_snap_metres=snaps.min(), max_reported_snap_metres=snaps.max(),
                max_geodesic_displacement_metres=pd.to_numeric(observed.geodesic_displacement_metres).max(),
                distinct_snapped_locations=locations.nunique(), snapping_varies=locations.nunique() > 1,
                snapping_not_observed=observed.empty, missing_reported_snaps=int(observed.missing_snap_distance.sum()),
                missing_resolved_coordinates=int(observed.missing_resolved_coordinate.sum()), automatic_exclusion=False, source_id=SOURCE))
    anomalies = directional.copy()
    anomalies["distinct_points_collapsed_to_same_resolved_coordinate"] = (
        anomalies.resolved_origin_location.notna() & anomalies.resolved_origin_location.eq(anomalies.resolved_destination_location)
        & anomalies.input_points_identical.eq(False))
    anomalies["identical_points_positive_model_duration"] = anomalies.input_points_identical.eq(True) & anomalies.model_duration_seconds.gt(0)
    anomalies["missing_route_or_local_zero_review"] = ~anomalies.route_status.isin(["route_available", "verified_same_tp_stop_zero"])
    anomalies = anomalies[anomalies[["distinct_points_collapsed_to_same_resolved_coordinate", "identical_points_positive_model_duration", "missing_route_or_local_zero_review"]].any(axis=1)].copy()
    anomalies["automatic_exclusion"] = False
    anomalies["audit_source_id"] = SOURCE
    return dict(zip(OUTPUTS, [observations, pd.DataFrame(endpoint_rows), anomalies]))


def register(frames):
    path = ROOT / "metadata/data_sources_master.csv"
    master = pd.read_csv(path, dtype=str, keep_default_na=False)
    row = dict(source_id=SOURCE, variable_name="stop_to_road_snapping_diagnostics",
        variable_description="Endpoint raccordement distances, independently computed geodesic displacement and structural route anomalies without cutoff/exclusion",
        source_organisation="Thesis project from OFT and HeiGIT/openrouteservice observations",
        source_dataset_name="Stop-to-stop road matrix snapping audit", retrieval_method="Reproducible Python audit of SHA-verified retained matrix responses",
        retrieval_date="2026-10-07", processed_file="|".join(OUTPUTS.values()), geographic_level="185 communal stops /75 station-access IDs /directional pairs",
        temporal_resolution="Current coordinate/network snapshots", unit="metres and factual flags",
        license="Inherited OFT /ORS /OpenStreetMap terms", access_conditions="Local derived data; no external request",
        transformation_applied="Distinct endpoint/request/direction snap observations; WGS84 ellipsoidal distance; min/max, not average coordinate or travel-time correction",
        quality_notes="No cutoff: large displacements listed as magnitudes, not invalidity or commune exclusions. No walking duration inferred. Matrix does not prove winter/legal access.",
        confidence_level="factual model diagnostics, not observed mobility", manual_verification="Explicit user request2026-10-07",
        notes="Parents DERIVED_ACCESSIBILITY_ROAD_STOP_ENDPOINTS_2026|ORS_DRIVING_CAR_TP_STOP_MATRIX_2026; versions and SHA in " + SUMMARY)
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([row]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(""), path)
    path = ROOT / "metadata/data_dictionary.csv"
    dictionary = pd.read_csv(path, dtype=str, keep_default_na=False)
    descriptions = {
        "endpoint_role": "Communal selected TP stop or station-access selected TP stop",
        "endpoint_id": "Stable territorial BFS or access-point ID, no name-based matching",
        "endpoint_name": "Original commune/access label",
        "input_longitude": "Original unchanged selected stop longitude WGS84, before road snapping",
        "input_latitude": "Original unchanged selected stop latitude WGS84, before road snapping",
        "resolved_location": "Exact service-resolved [longitude,latitude], not substituted original stop",
        "reported_snap_distance_metres": "Service-reported distance from requested point to road graph, metres",
        "geodesic_displacement_metres": "Independent WGS84 ellipsoidal straight-line separation from requested to reported resolved coordinate, metres; not road or walking distance",
        "missing_snap_distance": "No numeric service snap distance observed, never assumed zero",
        "missing_resolved_coordinate": "No resolved coordinate for independent displacement computation",
        "observations": "Distinct snap observations by request and direction, not independent communes",
        "min_reported_snap_metres": "Minimum observed service-reported snap distance for this endpoint",
        "max_reported_snap_metres": "Maximum observed service-reported snap distance for this endpoint",
        "max_geodesic_displacement_metres": "Maximum independent straight-line displacement for this endpoint",
        "distinct_snapped_locations": "Distinct reported resolved coordinate pairs, not resort count",
        "snapping_varies": "More than one reported resolved location; direction-sensitive graph placement, not automatically an error",
        "snapping_not_observed": "No returned snap observation, not exclusion or impossibility assertion",
        "missing_reported_snaps": "Count of snap observations without reported distance",
        "missing_resolved_coordinates": "Count of snap observations without usable resolved coordinate",
        "automatic_exclusion": "Always false: diagnostic never automatically excludes any commune or pair",
        "distinct_points_collapsed_to_same_resolved_coordinate": "Different requested coordinates resolved to an identical network coordinate; needs local review, not actual coincidence",
        "identical_points_positive_model_duration": "Identical requested coordinates with positive model duration, structural diagnostic",
        "missing_route_or_local_zero_review": "Nonavailable route or model zero requiring explicit local review; not automatically excluded",
        "audit_source_id": "Independent snapping audit provenance identifier",
    }
    rows = []
    for table, frame in frames.items():
        for field in frame:
            matches = dictionary[dictionary.variable.eq(field)]
            description = descriptions.get(field, matches.description.iloc[0] if not matches.empty else None)
            if description is None:
                raise ValueError("Undocumented audit field: " + field)
            unit = "metres" if any(t in field for t in ["metres", "_metres"]) else "decimal degrees WGS84" if field in ["input_longitude", "input_latitude"] else "count" if field in ["observations", "distinct_snapped_locations", "missing_reported_snaps", "missing_resolved_coordinates"] else "text/flag/identifier"
            rows.append(dict(variable=field, table=table, description=description, unit=unit, data_type=str(frame[field].dtype),
                geographic_level="endpoint/request/direction or directional pair", temporal_level="current static graph snapshot", source_id=SOURCE,
                raw_or_derived="derived diagnostic", formula="Service values, WGS84 Geod.inv displacement and deterministic structural flags, no cutoff",
                causal_role="diagnostic only, no exclusion", missing_share=f"{frame[field].isna().mean():.6f}" if len(frame) else "not_applicable_empty_anomaly_table",
                notes="No threshold, imputation, walk-time or historical causal interpretation."))
    write_csv(pd.concat([dictionary[~dictionary.table.isin(OUTPUTS)], pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(""), path)


def main():
    collection = json.loads((ROOT / COLLECTION).read_text(encoding="utf-8"))
    if sha(INPUT) != collection["output_sha256"][INPUT]:
        raise ValueError("Matrix output checksum differs from collection manifest")
    if (ROOT / SUMMARY).exists():
        previous = json.loads((ROOT / SUMMARY).read_text(encoding="utf-8"))
        for p, value in previous["output_sha256"].items():
            if sha(p) != value:
                raise ValueError("Preserve edited audit before regeneration")
    origins, arrivals = [pd.read_csv(ROOT / p, dtype={"selected_stop_id": str}) for p in ENDPOINTS.values()]
    directional = pd.read_csv(ROOT / INPUT)
    frames = audit(directional, origins, arrivals)
    for table, frame in frames.items():
        frame.to_csv(ROOT / OUTPUTS[table], index=False, lineterminator="\n")
    register(frames)
    observations, endpoints, anomalies = frames.values()
    summary = dict(measurement_label="arrêt communal → arrêt de station", endpoint_count=len(endpoints),
        returned_snap_observations=len(observations), endpoints_without_snap=int(endpoints.snapping_not_observed.sum()),
        maximum_service_reported_snap_metres=float(endpoints.max_reported_snap_metres.max()),
        structural_anomaly_directional_rows=len(anomalies), route_status_counts=directional.route_status.value_counts().to_dict(),
        endpoint_snap_quantiles_metres=endpoints.max_reported_snap_metres.quantile([0, .5, .9, .95, .99, 1]).to_dict(),
        largest_raccordements=endpoints.sort_values("max_reported_snap_metres", ascending=False).head(12).to_dict("records"),
        acceptance_threshold=None, automatically_excluded_communes=0, canonical_outputs_changed=False,
        input_sha256={p: sha(p) for p in [INPUT, COLLECTION, *ENDPOINTS.values()]}, output_sha256={p: sha(p) for p in OUTPUTS.values()},
        builder_sha256=sha("src/data_processing/audit_accessibility_road_stop_snapping.py"))
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["endpoint_count", "returned_snap_observations", "endpoints_without_snap", "maximum_service_reported_snap_metres", "structural_anomaly_directional_rows", "route_status_counts"]}))


if __name__ == "__main__":
    main()
