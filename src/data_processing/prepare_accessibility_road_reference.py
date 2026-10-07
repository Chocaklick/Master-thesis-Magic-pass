"""Prepare endpoint review without choosing coordinates, routing or exclusions.

Run from project root. Existing TP nodes are provenance, NOT road endpoints.
The approved territorial bridge is read from the canonical panel, never rebuilt.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.build_accessibility_reference_time_v2 import PROTECTED

SOURCE = "DERIVED_ACCESSIBILITY_ROAD_REFERENCE_PREPARATION"
CONFIG = "config/accessibility_road_reference_method.json"
INPUTS = [CONFIG, "config/accessibility_road_documentation_sources.json",
          "reports/public_transport_journey_nodes.csv",
          "reports/accessibility_station_access_nodes.csv",
          "data_processed/accessibility_municipality_month_exposure_territorial.csv",
          "config/accessibility_road_endpoint_sources.json",
          "config/accessibility_road_endpoint_evidence_review.json"]
OUTPUTS = {
    "accessibility_road_origin_review": "reports/accessibility_road_origin_review.csv",
    "accessibility_road_station_arrival_review": "reports/accessibility_road_station_arrival_review.csv",
}
SUMMARY = "reports/accessibility_road_reference_preparation_summary.json"


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def pipe(values):
    return "|".join(sorted({str(v) for v in values if str(v)}))


def prepare_origins(nodes, territorial_mapping):
    origins = nodes[nodes.node_role.eq("municipality_origin")].copy()
    origins["source_municipality_bfs_id"] = pd.to_numeric(origins.municipality_bfs_id, errors="raise").astype(int)
    mapping = territorial_mapping[["source_municipality_bfs_id", "municipality_bfs_id"]].drop_duplicates()
    if mapping.source_municipality_bfs_id.duplicated().any():
        raise ValueError("A source history maps to multiple territorial units")
    if set(origins.source_municipality_bfs_id) != set(mapping.source_municipality_bfs_id):
        raise ValueError("Origin/territorial source universe differs; no implicit discard")
    origins = origins.drop(columns="municipality_bfs_id").merge(mapping, validate="one_to_one")
    rows = []
    for bfs, group in origins.groupby("municipality_bfs_id", sort=True):
        records = group[["source_municipality_bfs_id", "municipality_name", "selected_stop_id",
                         "selected_stop_name", "selection_method"]].sort_values("source_municipality_bfs_id").to_dict("records")
        rows.append(dict(municipality_bfs_id=int(bfs), source_municipality_bfs_ids=pipe(group.source_municipality_bfs_id),
            municipality_names_source=pipe(group.municipality_name),
            legacy_tp_origin_records=json.dumps(records, ensure_ascii=False, sort_keys=True),
            road_origin_latitude=np.nan, road_origin_longitude=np.nan,
            road_origin_source_id="", road_origin_evidence_locator="",
            road_origin_address="", road_origin_coordinate_source_id="", road_origin_coordinate_locator="",
            road_origin_status="approved_administrative_centre_coordinates_pending",
            source_id=SOURCE))
    return pd.DataFrame(rows)


def prepare_arrivals(nodes):
    if nodes.access_point_id.duplicated().any():
        raise ValueError("Access identifiers must remain unique")
    columns = ["station_group_id", "station_group_name", "access_point_id", "access_point_name",
               "component_resort_id", "reference_latitude", "reference_longitude",
               "reference_source_id", "reference_method", "selected_stop_id", "selected_stop_name"]
    frame = nodes[columns].copy().sort_values(["station_group_id", "access_point_id"]).reset_index(drop=True)
    frame["existing_reference_verified_as_road_arrival"] = False
    for name in ["road_arrival_latitude", "road_arrival_longitude", "final_walk_minutes"]:
        frame[name] = np.nan
    for name in ["road_arrival_source_id", "road_arrival_evidence_locator", "road_arrival_coordinate_source_id", "road_arrival_coordinate_locator", "winter_access_source_id"]:
        frame[name] = ""
    frame["road_arrival_status"] = "approved_parking_dropoff_definition_actual_endpoint_evidence_pending"
    frame["road_arrival_evidence_note"] = ""
    frame["winter_access_status"] = "not_yet_verified"
    frame["source_id"] = SOURCE
    return frame


DESCRIPTIONS = {
    "municipality_bfs_id": ("Existing canonical territorial hotel-panel BFS identifier; approved Moutier bridge retained", "identifier"),
    "source_municipality_bfs_ids": ("All original hotel/TP-origin BFS identifiers represented by this territory, pipe-separated", "identifier list"),
    "municipality_names_source": ("Unaltered source municipal names, pipe-separated; not a matching key", "text"),
    "legacy_tp_origin_records": ("JSON list retaining each source BFS/name and old TP stop identifier/name/selection rule; not a road origin", "JSON"),
    "road_origin_latitude": ("Independently evidenced administrative-centre origin latitude; missing if not reviewed, never an arbitrary centroid", "decimal degrees WGS84"),
    "road_origin_longitude": ("Independently evidenced administrative-centre origin longitude; missing if not reviewed, never an arbitrary centroid", "decimal degrees WGS84"),
    "road_origin_source_id": ("Primary official administrative-address evidence identifier; blank where not reviewed", "identifier"),
    "road_origin_evidence_locator": ("Precise official address/section supporting actual road origin; blank where not reviewed", "text"),
    "road_origin_status": ("Origin review status; pending is neither exclusion nor absence of road access", "category"),
    "road_origin_address": ("Officially documented administrative-centre street address; blank where not researched", "text"),
    "road_origin_coordinate_source_id": ("Independent primary geocoding source identifier for the documented administrative address", "identifier"),
    "road_origin_coordinate_locator": ("Reviewed exact geocoding feature and municipal/address match; no automatic first-result selection", "text"),
    "station_group_id": ("Unchanged existing station-group identifier; no clustering or membership rebuilt", "identifier"),
    "station_group_name": ("Existing station-group descriptive name, not a matching key", "text"),
    "access_point_id": ("Unchanged existing access-point identifier; later endpoint correction must retain lineage", "identifier"),
    "access_point_name": ("Original access-point name; does not itself prove a lift departure or parking", "text"),
    "component_resort_id": ("Existing component resort identifier where available; missing remains missing", "identifier"),
    "reference_latitude": ("Existing station reference latitude copied for review only, not adopted as a car arrival", "decimal degrees WGS84"),
    "reference_longitude": ("Existing station reference longitude copied for review only, not adopted as a car arrival", "decimal degrees WGS84"),
    "reference_source_id": ("Original evidence identifier for existing reference coordinates", "identifier"),
    "reference_method": ("Original method for station reference coordinates; not a road-endpoint validation", "text"),
    "selected_stop_id": ("Existing TP arrival stop identifier retained for comparison provenance", "identifier"),
    "selected_stop_name": ("Existing TP arrival stop name, not a verified road arrival", "text"),
    "existing_reference_verified_as_road_arrival": ("Whether this preparation establishes the old reference as the actual car arrival; false means unverified, not incorrect", "boolean"),
    "road_arrival_latitude": ("Independently evidenced road arrival latitude; missing if unresolved, not the old proxy", "decimal degrees WGS84"),
    "road_arrival_longitude": ("Independently evidenced road arrival longitude; missing if unresolved, not the old proxy", "decimal degrees WGS84"),
    "final_walk_minutes": ("Future documented parking/drop-off to lift-departure walk; missing is not zero", "minutes"),
    "road_arrival_source_id": ("Primary source for actual or partial road-arrival evidence; not proof of complete endpoint coordinates", "identifier"),
    "road_arrival_evidence_locator": ("Precise evidence locator for actual or partial road-arrival facts", "text"),
    "road_arrival_coordinate_source_id": ("Archived primary-linked navigation evidence identifier; blank if coordinate unverified", "identifier"),
    "road_arrival_coordinate_locator": ("Exact place coordinates in the operator-linked redirect, not map viewport or old station proxy", "text"),
    "winter_access_source_id": ("Future primary evidence for winter availability/restrictions; currently blank", "identifier"),
    "road_arrival_status": ("Arrival review status; unresolved case retained, not routed to arbitrary village/top coordinates", "category"),
    "road_arrival_evidence_note": ("Positive road-arrival source facts and limitations; does not imply verified coordinates/winter access", "text"),
    "winter_access_status": ("Winter availability review status; not verified is not a closure", "category"),
    "source_id": ("Provenance identifier of this preparatory inventory, not a road measurement source", "identifier"),
}


def archived_metadata(source_id):
    records = []
    for path in (ROOT / "data_external/source_evidence").glob(source_id + "_*.metadata.json"):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata.get("source_id") == source_id:
            records.append(metadata)
    if len(records) != 1:
        raise ValueError(f"Expected one immutable original for {source_id}, found {len(records)}")
    metadata = records[0]
    if sha(metadata["raw_file"]) != metadata["sha256"]:
        raise ValueError(f"Source checksum mismatch: {source_id}")
    return metadata


def apply_endpoint_evidence(frames):
    review = json.loads((ROOT / INPUTS[6]).read_text(encoding="utf-8"))
    origins, arrivals = frames.values()
    for evidence in review["origins"]:
        chosen = origins.municipality_bfs_id.eq(evidence["municipality_bfs_id"])
        if chosen.sum() != 1:
            raise ValueError("Origin evidence must match one retained territory")
        archived_metadata(evidence["address_source_id"])
        origins.loc[chosen, "road_origin_address"] = evidence["address"]
        origins.loc[chosen, "road_origin_source_id"] = evidence["address_source_id"]
        origins.loc[chosen, "road_origin_evidence_locator"] = evidence["address_locator"]
        origins.loc[chosen, "road_origin_status"] = "address_verified_coordinates_pending"
        if evidence["coordinates_verified"]:
            metadata = archived_metadata(evidence["coordinate_source_id"])
            response = json.loads((ROOT / metadata["raw_file"]).read_text(encoding="utf-8"))
            matches = [r["attrs"] for r in response["results"]
                       if r["attrs"].get("featureId") == evidence["reviewed_feature_id"]
                       and r["attrs"].get("detail") == evidence["expected_detail"]
                       and r["attrs"].get("origin") == "address"]
            if len(matches) != 1:
                raise ValueError("Reviewed exact official address no longer matches one archived candidate")
            latitude, longitude = matches[0]["lat"], matches[0]["lon"]
            if not np.isfinite([latitude, longitude]).all() or not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Invalid documented WGS84 coordinates")
            origins.loc[chosen, ["road_origin_latitude", "road_origin_longitude"]] = [latitude, longitude]
            origins.loc[chosen, "road_origin_coordinate_source_id"] = evidence["coordinate_source_id"]
            origins.loc[chosen, "road_origin_coordinate_locator"] = evidence["coordinate_locator"]
            origins.loc[chosen, "road_origin_status"] = "verified_documented_administrative_centre"
    for evidence in review["arrivals"]:
        chosen = arrivals.access_point_id.eq(evidence["access_point_id"])
        if chosen.sum() != 1:
            raise ValueError("Arrival evidence must match one retained access point")
        archived_metadata(evidence["source_id"])
        # Positive information is useful even without exact coordinates or a
        # walking duration. Never promote it to verified road/winter access.
        if evidence["winter_access_verified"] or evidence["final_walk_minutes"] is not None:
            raise ValueError("Winter access/walking completion needs additional explicit verified evidence")
        arrivals.loc[chosen, "road_arrival_source_id"] = evidence["source_id"]
        arrivals.loc[chosen, "road_arrival_evidence_locator"] = evidence["locator"]
        arrivals.loc[chosen, "road_arrival_evidence_note"] = evidence["fact"] + " Limits: " + evidence["limits"]
        arrivals.loc[chosen, "road_arrival_status"] = "dropoff_and_garage_documented_coordinates_pending"
        if evidence["coordinates_verified"]:
            parent = archived_metadata(evidence["source_id"])
            navigation = archived_metadata(evidence["coordinate_source_id"])
            if navigation.get("parent_source_id") != evidence["source_id"]:
                raise ValueError("Navigation evidence must identify its official operator parent")
            if evidence["navigation_url"] not in (ROOT / parent["raw_file"]).read_text(encoding="utf-8"):
                raise ValueError("Navigation URL missing from archived official operator page")
            response = json.loads((ROOT / navigation["raw_file"]).read_text(encoding="utf-8"))
            matches = re.findall(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", response["location"])
            if response["url"] != evidence["navigation_url"] or len(matches) != 1:
                raise ValueError("Expected one exact operator-linked place coordinate")
            latitude, longitude = map(float, matches[0])
            if (latitude, longitude) != (evidence["latitude"], evidence["longitude"]):
                raise ValueError("Reviewed navigation destination differs from archived original")
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError("Invalid navigation coordinates")
            arrivals.loc[chosen, ["road_arrival_latitude", "road_arrival_longitude"]] = [latitude, longitude]
            arrivals.loc[chosen, "road_arrival_coordinate_source_id"] = evidence["coordinate_source_id"]
            arrivals.loc[chosen, "road_arrival_coordinate_locator"] = evidence["coordinate_locator"]
            arrivals.loc[chosen, "road_arrival_status"] = "verified_documented_road_arrival"


def register(frames):
    path = ROOT / "metadata/data_sources_master.csv"
    sources = pd.read_csv(path, dtype=str, keep_default_na=False)
    specs = json.loads((ROOT / INPUTS[1]).read_text(encoding="utf-8"))
    rows = []
    for spec in specs:
        rows.append(dict(source_id=spec["source_id"], variable_name="road_reference_method_documentation",
            variable_description=spec["description"], source_organisation=spec["organisation"],
            source_dataset_name="Primary routing/source documentation, not a route dataset",
            source_page_url=spec["url"], retrieval_method="Primary web documentation consulted; no local original archived",
            retrieval_date=spec.get("consultation_date", "2026-10-06"), processed_file="reports/87_COLLECTE_REFERENCE_ROUTIERE_FR.md" if spec.get("consultation_date") else "reports/86_PREPARATION_REFERENCE_ROUTIERE_FR.md",
            geographic_level="routing-service documentation", temporal_resolution="consultation snapshot",
            unit="documentation", license="See source terms; no road extract redistributed",
            access_conditions="Public primary documentation; protected pages not bypassed",
            transformation_applied="Documented service characteristics only; no queries/road durations collected",
            quality_notes=spec["limits"], confidence_level="primary documentation, not empirical travel-time evidence",
            manual_verification=spec["locator"], notes="Primary documentation, not an empirical route observation; collection progress in reports/accessibility_road_reference_collection_summary.json"))
    for spec in json.loads((ROOT / INPUTS[5]).read_text(encoding="utf-8")):
        metadata = archived_metadata(spec["source_id"])
        rows.append(dict(source_id=spec["source_id"], variable_name="road_reference_endpoint_evidence",
            variable_description=spec["description"], source_organisation=spec["organisation"],
            source_dataset_name="Official municipal/operator address and arrival evidence; official exact geocoding candidates",
            source_page_url=spec["url"], direct_download_url=metadata.get("final_url", spec["url"]),
            retrieval_method=metadata.get("retrieval_method", "Existing robots-respecting collector; immutable original and SHA-256 sidecar"),
            retrieval_date=metadata["retrieval_date"], original_file_name=Path(metadata["raw_file"]).name,
            local_raw_file=metadata["raw_file"], processed_file="|".join(OUTPUTS.values()),
            geographic_level="Documented municipality or station-access endpoint", temporal_resolution="retrieval-date source snapshot",
            unit="documented address, coordinates or partial arrival facts",
            license="Preserve primary source URL; inherited official source terms", access_conditions="Public source; robots respected",
            transformation_applied="Official administrative address and exact reviewed geocoding; operator-linked parking place coordinates or explicitly partial arrival facts",
            quality_notes="Current access, not historically certified. Winter proof and final walking duration unresolved; parking navigation point is not a surveyed driveway entrance. No time inferred from address.",
            confidence_level="official positive endpoint fact; uncertainties explicit", manual_verification="config/accessibility_road_endpoint_evidence_review.json",
            notes="Raw SHA-256 " + metadata["sha256"]))
    rows.append(dict(source_id=SOURCE, variable_name="road_reference_endpoint_inventory",
        variable_description="Existing municipality territories and station access identifiers preserved for road endpoint review, no road time calculated",
        source_organisation="Thesis project", source_dataset_name="Stage 34 road reference preparation",
        retrieval_method="Reproducible Python derivation from existing checked inputs",
        retrieval_date=json.loads((ROOT / INPUTS[6]).read_text(encoding="utf-8"))["review_date"], processed_file="|".join(OUTPUTS.values()),
        geographic_level="185 existing hotel territories and 75 existing station access points",
        temporal_resolution="preparatory review snapshot", unit="identifiers and explicit endpoint statuses",
        license="Inherited input licenses", access_conditions="Local project outputs",
        transformation_applied="Approved panel territorial mapping; preserve source BFS/TP origins and station IDs; exact sourced endpoint evidence applied from separate review config",
        quality_notes="Only explicitly evidenced endpoints filled. No road route, threshold, exclusion or canonical exposure replacement.",
        confidence_level="exact lineage; only explicitly evidenced road endpoints verified",
        manual_verification="User approved road-primary/TP-comparison, administrative-centre/actual-parking-dropoff endpoints and static metric through replacement question after withdrawal of accidental initial reply",
        notes="Inputs: reports/public_transport_journey_nodes.csv; reports/accessibility_station_access_nodes.csv; data_processed/accessibility_municipality_month_exposure_territorial.csv; config/accessibility_road_endpoint_evidence_review.json. Parent evidence: DERIVED_ACCESSIBILITY_STATION_GROUP_JOURNEYS|DERIVED_ACCESSIBILITY_STATION_GROUPS|DERIVED_ACCESSIBILITY_TERRITORIAL_MOUTIER_BRIDGE|MOUTIER_ADMINISTRATIVE_CENTRE_OFFICIAL_2026|MOUTIER_ADMINISTRATIVE_CENTRE_GEOADMIN_2026|LEUKERBAD_TORRENT_ROAD_ARRIVAL_OFFICIAL_2026"))
    ids = {row["source_id"] for row in rows}
    sources = sources[~sources.source_id.isin(ids)]
    pd.concat([sources, pd.DataFrame(rows).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna("").to_csv(path, index=False, lineterminator="\n")
    path = ROOT / "metadata/data_dictionary.csv"
    dictionary = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows = []
    for table, frame in frames.items():
        for field in frame:
            description, unit = DESCRIPTIONS[field]
            missing = frame[field].isna() | frame[field].astype(str).eq("")
            rows.append(dict(variable=field, table=table, description=description, unit=unit,
                data_type=str(frame[field].dtype), geographic_level="municipal territory" if table.endswith("origin_review") else "existing station access point",
                temporal_level="preparatory 2026 review", source_id=SOURCE, raw_or_derived="derived inventory",
                formula="Copy existing lineage/canonical bridge; apply independently reviewed endpoint evidence; no missing-value imputation",
                causal_role="preparation only, not exposure or analysis feature", missing_share=f"{missing.mean():.6f}",
                notes="Original references/TP stops are not road coordinates. Endpoint/static metric and ORS provider approved; unresearched coordinates remain pending; no credentials recorded."))
    dictionary = dictionary[~dictionary.table.isin(frames)]
    pd.concat([dictionary, pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna("").to_csv(path, index=False, lineterminator="\n")


def main():
    protected = {p: sha(p) for p in PROTECTED}
    # These are preparatory inventories, not a storage layer for future/manual
    # collected coordinates. Do not erase a user's completed evidence on rerun.
    if (ROOT / SUMMARY).exists():
        previous = json.loads((ROOT / SUMMARY).read_text(encoding="utf-8"))
        for path, expected in previous["output_sha256"].items():
            if not (ROOT / path).exists() or sha(path) != expected:
                raise ValueError(f"Review output changed since preparation; preserve and integrate its evidence before regenerating: {path}")
    config = json.loads((ROOT / CONFIG).read_text(encoding="utf-8"))
    origins = pd.read_csv(ROOT / INPUTS[2], dtype=str, keep_default_na=False)
    mapping = pd.read_csv(ROOT / INPUTS[4], usecols=["source_municipality_bfs_id", "municipality_bfs_id"])
    nodes = pd.read_csv(ROOT / INPUTS[3], dtype={"selected_stop_id": str, "component_resort_id": str}, keep_default_na=False)
    frames = {"accessibility_road_origin_review": prepare_origins(origins, mapping),
              "accessibility_road_station_arrival_review": prepare_arrivals(nodes)}
    apply_endpoint_evidence(frames)
    o, a = frames.values()
    if len(o) != 185 or len(a) != 75 or a.station_group_id.nunique() != 71:
        raise ValueError("Existing universe changed; no automatic expansion/exclusion")
    for table, frame in frames.items():
        frame.to_csv(ROOT / OUTPUTS[table], index=False, lineterminator="\n")
    register(frames)
    after = {p: sha(p) for p in PROTECTED}
    if after != protected:
        raise ValueError("A protected legacy output changed")
    summary = dict(status=config["status"], road_primary_approved=config["road_primary_approved"],
        origin_definition_approved=config["origin_definition_approved"],
        station_arrival_definition_approved=config["station_arrival_definition_approved"],
        traffic_assumptions_approved=config["traffic_assumptions_approved"],
        municipality_territories=len(o), source_municipality_histories=len(origins[origins.node_role.eq("municipality_origin")]),
        access_points=len(a), station_groups=int(a.station_group_id.nunique()),
        potential_territory_access_pairs=len(o) * len(a), potential_directional_routes=2 * len(o) * len(a),
        actual_road_routes_computed=0, verified_road_origins=int(o.road_origin_status.eq("verified_documented_administrative_centre").sum()),
        verified_road_arrivals=int(a.road_arrival_latitude.notna().sum()),
        routing_provider_selected=config["routing_source_selected"], routing_provider=config["routing_provider"], canonical_outputs_changed=False,
        input_sha256={p: sha(p) for p in INPUTS},
        builder_sha256=sha("src/data_processing/prepare_accessibility_road_reference.py"),
        output_sha256={p: sha(p) for p in OUTPUTS.values()}, protected_legacy_sha256=after,
        resume_command=".venv/Scripts/python.exe src/data_processing/prepare_accessibility_road_reference.py",
        next_step="Extend documented administrative-centre/road-arrival evidence, then resume the ORS collector at the new HeiGIT endpoint. Key stays local; quotas and originals in collection manifest. New evidence belongs in authoritative endpoint review input, not hand-edited output CSVs.")
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["status", "municipality_territories", "access_points", "station_groups", "potential_territory_access_pairs", "actual_road_routes_computed"]}))


if __name__ == "__main__":
    main()
