"""Resumable static ORS matrices at verified endpoints; pending is not exclusion.

Run from root, --execute to make requests. Credentials never enter artifacts.
Original response bytes and safe request/response metadata are immutable.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.road_reference_credentials import load_credential
from src.data_processing.prepare_accessibility_road_reference import OUTPUTS, PROTECTED, sha
from src.data_processing.plan_accessibility_road_matrix import plan_batches
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

CONFIG = "config/accessibility_road_routing.json"
ENDPOINT = "https://api.heigit.org/openrouteservice/v2/matrix/driving-car"
SOURCE = "ORS_DRIVING_CAR_STATIC_MATRIX_2026"
TABLES = {"accessibility_road_reference_directional": "data_processed/accessibility_road_reference_directional.csv",
          "accessibility_road_reference_pairs": "data_processed/accessibility_road_reference_pairs.csv"}
SUMMARY = "reports/accessibility_road_reference_collection_summary.json"
SAFE_HEADERS = {"content-type", "x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset", "retry-after"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def make_payload(batch, origins, arrivals, config):
    m = origins.set_index("municipality_bfs_id").loc[batch["municipality_bfs_ids"]]
    a = arrivals.set_index("access_point_id").loc[batch["access_point_ids"]]
    mc = m[["road_origin_longitude", "road_origin_latitude"]].astype(float).values.tolist()
    ac = a[["road_arrival_longitude", "road_arrival_latitude"]].astype(float).values.tolist()
    if batch["direction"] == "outbound":
        locations, ns, nd = mc + ac, len(mc), len(ac)
    else:
        locations, ns, nd = ac + mc, len(ac), len(mc)
    if not all(math.isfinite(v) for point in locations for v in point):
        raise ValueError("Unverified/missing endpoint cannot be requested")
    return dict(locations=locations, sources=[str(i) for i in range(ns)],
                destinations=[str(i) for i in range(ns, ns + nd)],
                metrics=config["metrics"], units=config["units"],
                resolve_locations=config["resolve_locations"])


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_matrix(payload, credential, endpoint):
    if endpoint != ENDPOINT:
        raise ValueError("Authenticated requests require the approved HeiGIT endpoint")
    request = Request(endpoint, data=json.dumps(payload).encode(), method="POST",
                      headers={"Authorization": credential, "Content-Type": "application/json",
                               "User-Agent": "ThesisSkiResearch/0.1"})
    try:
        response = build_opener(NoRedirect).open(request, timeout=60)
    except HTTPError as exc:
        response = exc
    except (URLError, TimeoutError, OSError) as exc:
        # Do not interpolate request, exception text or headers: credentials could leak.
        return None, {}, b"", type(exc).__name__
    with response:
        body = response.read()
        headers = {k.lower(): v for k, v in response.headers.items() if k.lower() in SAFE_HEADERS}
        return response.code, headers, body, None


def validate_response(response, payload):
    ns, nd = len(payload["sources"]), len(payload["destinations"])
    for metric in ("durations", "distances"):
        matrix = response.get(metric)
        if not isinstance(matrix, list) or len(matrix) != ns or any(len(row) != nd for row in matrix):
            raise ValueError("Matrix dimensions differ from the exact request")
        for row in matrix:
            if any(v is not None and (not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0) for v in row):
                raise ValueError("Invalid matrix value")
    for field, count in (("sources", ns), ("destinations", nd)):
        if len(response.get(field, [])) != count:
            raise ValueError("Resolved endpoint count differs")


def load_cache(path, request_id, payload):
    metadata = json.loads(path.read_text(encoding="utf-8"))
    if metadata["request_id"] != request_id or metadata["payload"] != payload or metadata["endpoint"] != ENDPOINT:
        raise ValueError("Checkpoint request identity differs")
    raw = ROOT / metadata["raw_file"]
    if sha(metadata["raw_file"]) != metadata["raw_sha256"]:
        raise ValueError("Immutable response checksum mismatch")
    if metadata["status"] != "success":
        raise ValueError("Failed response is not a reusable successful checkpoint")
    response = json.loads(raw.read_bytes())
    validate_response(response, payload)
    return response, metadata


def cell_records(batch, payload, response, metadata):
    validate_response(response, payload)
    records = []
    for mi, bfs in enumerate(batch["municipality_bfs_ids"]):
        for ai, access in enumerate(batch["access_point_ids"]):
            si, di = (mi, ai) if batch["direction"] == "outbound" else (ai, mi)
            duration, distance = response["durations"][si][di], response["distances"][si][di]
            original_s = payload["locations"][int(payload["sources"][si])]
            original_d = payload["locations"][int(payload["destinations"][di])]
            status = "route_available" if duration is not None else "no_route_returned"
            usable = duration
            if duration == 0:
                # Road snapping can collapse distinct geographical points. Do not
                # promote a model zero into a documented real local coincidence.
                status = "zero_model_duration_requires_local_review"
                usable = None
            engine = response.get("metadata", {}).get("engine", {})
            records.append(dict(municipality_bfs_id=bfs, access_point_id=access,
                direction=batch["direction"], route_status=status,
                model_duration_seconds=duration, usable_duration_minutes=None if usable is None else usable / 60,
                model_distance_metres=distance,
                origin_snap_distance_metres=response["sources"][si].get("snapped_distance"),
                destination_snap_distance_metres=response["destinations"][di].get("snapped_distance"),
                resolved_origin_location=json.dumps(response["sources"][si].get("location")),
                resolved_destination_location=json.dumps(response["destinations"][di].get("location")),
                input_points_identical=original_s == original_d,
                request_id=metadata["request_id"], raw_file=metadata["raw_file"], raw_sha256=metadata["raw_sha256"],
                retrieval_date=metadata["retrieval_date"], engine_version=engine.get("version", ""),
                graph_date=engine.get("graph_date", ""), engine_build_date=engine.get("build_date", ""), source_id=SOURCE))
    return records


def build_outputs(origins, arrivals, records):
    universe = pd.MultiIndex.from_product([origins.municipality_bfs_id, arrivals.access_point_id,
                                          ["outbound", "return"]],
                names=["municipality_bfs_id", "access_point_id", "direction"]).to_frame(index=False)
    if records:
        observed = pd.DataFrame(records)
        if observed.duplicated(["municipality_bfs_id", "access_point_id", "direction"]).any():
            raise ValueError("Duplicate directional observation")
        frame = universe.merge(observed, how="left", validate="one_to_one")
    else:
        frame = universe.copy()
        for field in ["route_status", "model_duration_seconds", "usable_duration_minutes", "model_distance_metres",
                      "origin_snap_distance_metres", "destination_snap_distance_metres", "resolved_origin_location",
                      "resolved_destination_location", "input_points_identical", "request_id", "raw_file", "raw_sha256",
                      "retrieval_date", "engine_version", "graph_date", "engine_build_date", "source_id"]:
            frame[field] = None
    origin_fields = ["municipality_bfs_id", "road_origin_status", "road_origin_source_id", "road_origin_coordinate_source_id"]
    arrival_fields = ["access_point_id", "station_group_id", "road_arrival_status", "road_arrival_source_id",
                      "road_arrival_coordinate_source_id", "winter_access_status", "final_walk_minutes"]
    frame = frame.merge(origins[origin_fields], validate="many_to_one").merge(arrivals[arrival_fields], validate="many_to_one")
    ready = frame.road_origin_status.eq("verified_documented_administrative_centre") & frame.road_arrival_status.eq("verified_documented_road_arrival")
    frame["route_status"] = frame.route_status.fillna(ready.map({True: "verified_endpoints_not_yet_queried", False: "endpoint_evidence_pending"}))
    frame["source_id"] = frame.source_id.fillna("DERIVED_ACCESSIBILITY_ROAD_REFERENCE_PREPARATION")
    keys = ["municipality_bfs_id", "access_point_id", "station_group_id"]
    pairs = frame[keys].drop_duplicates().copy()
    for direction in ("outbound", "return"):
        subset = frame[frame.direction.eq(direction)][keys + ["usable_duration_minutes", "route_status"]]
        pairs = pairs.merge(subset.rename(columns={"usable_duration_minutes": direction + "_minutes", "route_status": direction + "_status"}), validate="one_to_one")
    # Missing in either direction propagates; final walk is never silently zero.
    pairs["road_reference_minutes"] = (pairs.outbound_minutes + pairs.return_minutes) / 2
    pairs = pairs.merge(arrivals[["access_point_id", "winter_access_status", "final_walk_minutes"]], validate="many_to_one")
    pairs["source_id"] = pairs.road_reference_minutes.notna().map({True: SOURCE, False: "DERIVED_ACCESSIBILITY_ROAD_REFERENCE_PREPARATION"})
    return dict(zip(TABLES, [frame, pairs]))


def recover_completed(cache_folder, origins, arrivals, config):
    """Reuse prior cells even after adding endpoints: do not route them again."""
    records, successes = [], []
    ready_m = set(origins.loc[origins.road_origin_status.eq("verified_documented_administrative_centre"), "municipality_bfs_id"])
    ready_a = set(arrivals.loc[arrivals.road_arrival_status.eq("verified_documented_road_arrival"), "access_point_id"])
    for path in sorted(cache_folder.glob("*.json")):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        batch = metadata["batch"]
        if not set(batch["municipality_bfs_ids"]).issubset(ready_m) or not set(batch["access_point_ids"]).issubset(ready_a):
            continue
        current_payload = make_payload(batch, origins, arrivals, config)
        if current_payload != metadata["payload"]:
            # Reviewed endpoint changed; old original retained, not reused as new coordinate.
            continue
        rid = digest(dict(endpoint=ENDPOINT, batch=batch, payload=current_payload))
        response, metadata = load_cache(path, rid, current_payload)
        records.extend(cell_records(batch, current_payload, response, metadata))
        successes.append(metadata)
    if len({(r["municipality_bfs_id"], r["access_point_id"], r["direction"]) for r in records}) != len(records):
        raise ValueError("Overlapping successful checkpoints require explicit review")
    return records, successes


def missing_batches(municipality_ids, access_ids, completed, size):
    """Group identical still-missing destinations into rectangles, without repeats."""
    batches = []
    for direction in ("outbound", "return"):
        groups = {}
        for bfs in municipality_ids:
            missing = tuple(a for a in access_ids if (bfs, a, direction) not in completed)
            if missing:
                groups.setdefault(missing, []).append(bfs)
        for destinations, ids in groups.items():
            for batch in plan_batches(ids, list(destinations), size):
                if batch["direction"] == direction:
                    batches.append(batch)
    return batches


def register(frames, manifest):
    source_path = ROOT / "metadata/data_sources_master.csv"
    sources = pd.read_csv(source_path, dtype=str, keep_default_na=False)
    row = dict(source_id=SOURCE, variable_name="static_directional_road_access",
        variable_description="Fastest modelled driving-car matrix at independently documented endpoints, directions separate and averaged only if both usable",
        source_organisation="HeiGIT / openrouteservice; OpenStreetMap contributors",
        source_dataset_name="ORS driving-car Matrix API, current graph snapshot",
        source_page_url="https://openrouteservice.org/dev/", api_endpoint=ENDPOINT,
        api_parameters="See immutable per-request metadata; duration+distance, units m, no departure/traffic/fallback parameters",
        retrieval_method="Authenticated POST, redirects disabled; key in Authorization only, never archived",
        retrieval_date="|".join(sorted({r["retrieval_date"] for r in manifest["successful_requests"]})),
        local_raw_file="|".join(r["raw_file"] for r in manifest["successful_requests"]),
        processed_file="|".join(TABLES.values()), geographic_level="municipality administrative centre to lift-serving parking/drop-off",
        temporal_resolution="current static graph snapshot, not historical travel time", unit="seconds, minutes and metres",
        license="ORS terms and OpenStreetMap attribution; no account credentials redistributed",
        access_conditions="User-configured API credential; actual response quotas retained; no account/payment changes",
        transformation_applied="Seconds/60; (outbound+return)/2 only when both usable; no imputation or threshold/exposure change",
        quality_notes="No congestion; winter restrictions and final walk separately unresolved; snapped coordinates retained. Distinct-point model zeros require review, not real zero access. Pending endpoints retained. Current graph cannot establish past access.",
        confidence_level="modelled service result, not observed individual travel time",
        manual_verification="Approved endpoints and static metric; reviewed endpoint evidence configuration",
        notes="Request IDs, engine/graph versions, safe quota headers and response SHA-256: " + SUMMARY)
    if manifest["successful_requests"]:
        sources = sources[sources.source_id.ne(SOURCE)]
        pd.concat([sources, pd.DataFrame([row]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna("").to_csv(source_path, index=False, lineterminator="\n")
    path = ROOT / "metadata/data_dictionary.csv"
    dictionary = pd.read_csv(path, dtype=str, keep_default_na=False)
    descriptions = {
        "model_duration_seconds": "Original modelled driving duration; null if no route, zero retained only as model output",
        "usable_duration_minutes": "Model seconds / 60; zero requires local review; missing stays missing",
        "model_distance_metres": "Original driving distance returned by service",
        "origin_snap_distance_metres": "Service-reported distance from requested start to model road network",
        "destination_snap_distance_metres": "Service-reported distance from requested end to model road network",
        "resolved_origin_location": "Service-snapped start [longitude, latitude], JSON; not a substituted official endpoint",
        "resolved_destination_location": "Service-snapped end [longitude, latitude], JSON; not a substituted official endpoint",
        "input_points_identical": "Exact equality of requested coordinates, not independent proof of real local coincidence",
        "route_status": "Available, no route, zero needing local review, verified not queried or endpoint evidence pending",
        "road_reference_minutes": "Arithmetic mean of separately routed outward/return minutes; missing if either unusable, final walk excluded and separately documented",
        "outbound_minutes": "Usable administrative-centre to station-parking driving time in minutes",
        "return_minutes": "Usable station-parking to administrative-centre driving time in minutes",
        "outbound_status": "Outward route status; pending is not an analytical exclusion",
        "return_status": "Return route status; missing is never zero",
        "request_id": "SHA-256 identity of endpoint, exact payload, direction and stable endpoint IDs",
        "raw_file": "Project-relative immutable original API response path",
        "raw_sha256": "SHA-256 of original response bytes",
        "retrieval_date": "Actual request timestamp in UTC, no historical-date assumption",
        "engine_version": "Original API routing-engine version if provided",
        "graph_date": "Original API routing-graph date if provided; differences flagged in manifest",
        "engine_build_date": "Original API engine build date if provided",
        "direction": "Outward administrative-centre to parking, or independent return",
        "source_id": "Provenance: model API result or unqueried endpoint inventory",
    }
    prior = dictionary[dictionary.table.isin(OUTPUTS)]
    rows = []
    for table, frame in frames.items():
        for field in frame:
            if field not in descriptions:
                matches = prior[prior.variable.eq(field)]
                if matches.empty:
                    raise ValueError("Unregistered analytical field: " + field)
                description, unit = matches.iloc[0][["description", "unit"]]
            else:
                description = descriptions[field]
                unit = "minutes" if "minutes" in field else "seconds" if field.endswith("seconds") else "metres" if field.endswith("metres") else "text/identifier/status"
            missing = frame[field].isna() | frame[field].astype(str).eq("")
            rows.append(dict(variable=field, table=table, description=description, unit=unit,
                data_type=str(frame[field].dtype), geographic_level="territory–access-point, direction where applicable",
                temporal_level="current static graph snapshot", source_id=SOURCE if manifest["successful_requests"] else "DERIVED_ACCESSIBILITY_ROAD_REFERENCE_PREPARATION",
                raw_or_derived="derived", formula="Exact service observation and endpoint lineage; mean only if both directions usable",
                causal_role="access measurement under construction, not canonical exposure",
                missing_share=f"{missing.mean():.6f}", notes="No municipality removed; unresolved winter/walk retained; no time imputation or live congestion."))
    dictionary = dictionary[~dictionary.table.isin(TABLES)]
    pd.concat([dictionary, pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna("").to_csv(path, index=False, lineterminator="\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-new-batches", type=int, default=2)
    args = parser.parse_args()
    if args.max_new_batches < 1:
        parser.error("max-new-batches must be positive")
    config = json.loads((ROOT / CONFIG).read_text(encoding="utf-8"))
    if config["api_endpoint"] != ENDPOINT:
        raise ValueError("Deprecated/unapproved endpoint; no request sent")
    protected = {p: sha(p) for p in PROTECTED}
    if (ROOT / SUMMARY).exists():
        previous = json.loads((ROOT / SUMMARY).read_text(encoding="utf-8"))
        for path, value in previous.get("output_sha256", {}).items():
            if sha(path) != value:
                raise ValueError("Derived output edited; preserve before regeneration: " + path)
    origins = pd.read_csv(ROOT / OUTPUTS["accessibility_road_origin_review"])
    arrivals = pd.read_csv(ROOT / OUTPUTS["accessibility_road_station_arrival_review"])
    m = sorted(origins.loc[origins.road_origin_status.eq("verified_documented_administrative_centre"), "municipality_bfs_id"].astype(int))
    a = sorted(arrivals.loc[arrivals.road_arrival_status.eq("verified_documented_road_arrival"), "access_point_id"])
    credential, credential_location = load_credential(config)
    if args.execute and not credential:
        raise ValueError("Credential absent; no request sent")
    cache_folder = ROOT / "data_interim/accessibility_road_ors"
    raw_folder = ROOT / "data_external/accessibility_road_ors"
    cache_folder.mkdir(parents=True, exist_ok=True)
    raw_folder.mkdir(parents=True, exist_ok=True)
    # Exclusive lock prevents competing writers; unknown old lock is not removed.
    lock = cache_folder / "collector.lock"
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(datetime.now(timezone.utc).isoformat())
    try:
        records, successes = recover_completed(cache_folder, origins, arrivals, config)
        failures = []
        new_requests, reused = 0, len(successes)
        status = "dry_run" if not args.execute else "available_verified_endpoints_completed"
        completed = {(r["municipality_bfs_id"], r["access_point_id"], r["direction"]) for r in records}
        if args.execute and successes:
            latest = max(successes, key=lambda r: r["retrieval_date"])["safe_response_headers"]
            if latest.get("x-ratelimit-remaining") == "0":
                reset = latest.get("x-ratelimit-reset")
                if not reset or not reset.isdigit() or int(reset) > time.time():
                    status = "stopped_reported_quota_exhausted"
        for batch in missing_batches(m, a, completed, config["block_size"]):
            if status == "stopped_reported_quota_exhausted":
                break
            payload = make_payload(batch, origins, arrivals, config)
            rid = digest(dict(endpoint=ENDPOINT, batch=batch, payload=payload))
            checkpoint = cache_folder / (rid + ".json")
            if checkpoint.exists():
                response, metadata = load_cache(checkpoint, rid, payload)
                reused += 1
            elif not args.execute or new_requests >= args.max_new_batches:
                status = "dry_run" if not args.execute else "batch_budget_reached_resume_pending"
                continue
            else:
                code, headers, body, error = request_matrix(payload, credential, ENDPOINT)
                new_requests += 1
                if credential.encode() in body:
                    raise ValueError("Response contains credential; original not persisted")
                stamp = datetime.now(timezone.utc)
                raw = raw_folder / f"{rid}_{stamp.strftime('%Y%m%dT%H%M%S%fZ')}.json"
                metadata = dict(request_id=rid, endpoint=ENDPOINT, batch=batch, payload=payload,
                    retrieval_date=stamp.isoformat(), http_status=code, safe_response_headers=headers,
                    network_error_type=error, raw_file=raw.relative_to(ROOT).as_posix(),
                    raw_sha256=hashlib.sha256(body).hexdigest(), status="http_or_network_failure")
                with raw.open("xb") as stream:
                    stream.write(body)
                if code == 200:
                    try:
                        response = json.loads(body)
                        validate_response(response, payload)
                        metadata["status"] = "success"
                    except (ValueError, TypeError, KeyError):
                        metadata["status"] = "invalid_response"
                with raw.with_suffix(".metadata.json").open("x", encoding="utf-8") as stream:
                    json.dump(metadata, stream, ensure_ascii=False, indent=2)
                if metadata["status"] != "success":
                    failures.append(metadata)
                    status = f"stopped_http_{code}" if code else "stopped_network_failure"
                    break
                with checkpoint.open("x", encoding="utf-8") as stream:
                    json.dump(metadata, stream, ensure_ascii=False, indent=2)
            records.extend(cell_records(batch, payload, response, metadata))
            successes.append(metadata)
            if metadata["safe_response_headers"].get("x-ratelimit-remaining") == "0":
                status = "stopped_reported_quota_exhausted"
                break
            if args.execute:
                time.sleep(1.5)  # Operational pacing, not a travel-time assumption.
        frames = build_outputs(origins, arrivals, records)
        manifest = dict(status=status, endpoint=ENDPOINT, provider="openrouteservice", credential_present=bool(credential),
            credential_location=credential_location, new_requests=new_requests, reused_successful_requests=reused,
            ready_origins=len(m), ready_arrivals=len(a), municipality_territories=len(origins), access_points=len(arrivals),
            directional_universe=2 * len(origins) * len(arrivals), successful_requests=successes, failures=failures,
            actual_directional_cells_returned=len(records), usable_directional_routes=int(frames[next(iter(TABLES))].usable_duration_minutes.notna().sum()),
            pairs_with_both_directions=int(frames["accessibility_road_reference_pairs"].road_reference_minutes.notna().sum()),
            graph_versions=sorted({(r.get("graph_date", ""), r.get("engine_version", "")) for r in records}),
            full_endpoint_universe_complete=len(m) == len(origins) and len(a) == len(arrivals),
            endpoints_remaining={"origins": len(origins) - len(m), "arrivals": len(arrivals) - len(a)},
            canonical_outputs_changed=False, protected_legacy_sha256=protected,
            input_sha256={p: sha(p) for p in [CONFIG, *OUTPUTS.values()]},
            collector_sha256=sha("src/data_collection/collect_accessibility_road_matrix.py"),
            quota_note="No separate account quota endpoint used; first response reveals allowance headers, later requests check retained remaining quota. Missing headers mean unknown, not unlimited. 401/403/429 stop without retry.",
            resume_command=".venv/Scripts/python.exe src/data_collection/collect_accessibility_road_matrix.py --execute --max-new-batches 2")
        manifest["graph_version_difference_flag"] = len(manifest["graph_versions"]) > 1
        for table, frame in frames.items():
            frame.to_csv(ROOT / TABLES[table], index=False, lineterminator="\n")
        register(frames, manifest)
        if protected != {p: sha(p) for p in PROTECTED}:
            raise ValueError("Protected legacy changed")
        manifest["output_sha256"] = {p: sha(p) for p in TABLES.values()}
        (ROOT / SUMMARY).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: manifest[k] for k in ["status", "credential_present", "ready_origins", "ready_arrivals", "new_requests", "reused_successful_requests", "actual_directional_cells_returned", "pairs_with_both_directions"]}))
    finally:
        lock.unlink()


if __name__ == "__main__":
    main()
