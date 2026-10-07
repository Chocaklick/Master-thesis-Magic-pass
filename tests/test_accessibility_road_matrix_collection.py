import json
from copy import deepcopy

import pandas as pd
import pytest

from src.data_collection import collect_accessibility_road_matrix as road
from src.data_collection.road_reference_credentials import load_credential
from src.data_processing.prepare_accessibility_road_reference import OUTPUTS


def fixture():
    config = json.loads((road.ROOT / road.CONFIG).read_text())
    origins = pd.read_csv(road.ROOT / OUTPUTS["accessibility_road_origin_review"])
    arrivals = pd.read_csv(road.ROOT / OUTPUTS["accessibility_road_station_arrival_review"])
    batch = dict(batch_id="fixture", direction="outbound", municipality_bfs_ids=[783],
                 access_point_ids=["ACCESS_MAGIC_CURRENT__4451"], requested_cells=1)
    payload = road.make_payload(batch, origins, arrivals, config)
    response = dict(durations=[[120]], distances=[[1000]],
                    sources=[dict(location=payload["locations"][0], snapped_distance=2)],
                    destinations=[dict(location=payload["locations"][1], snapped_distance=3)])
    metadata = dict(request_id="fixture_not_real_source", raw_file="fixture_not_real_data.json",
                    raw_sha256="fixture", retrieval_date="synthetic fixture")
    return origins, arrivals, batch, payload, response, metadata


def test_new_host_and_secret_never_enter_payload():
    origins, arrivals, batch, payload, _, _ = fixture()
    assert road.ENDPOINT == "https://api.heigit.org/openrouteservice/v2/matrix/driving-car"
    assert payload["metrics"] == ["duration", "distance"]
    assert payload["sources"] == ["0"] and payload["destinations"] == ["1"]
    assert not any(k in payload for k in ("Authorization", "api_key", "departure", "fallback_speed"))
    with pytest.raises(ValueError, match="HeiGIT"):
        road.request_matrix(payload, "synthetic-not-a-credential", "https://api.openrouteservice.org/v2/matrix/driving-car")


def test_real_zero_not_inferred_from_network_snapping():
    origins, arrivals, batch, payload, response, metadata = fixture()
    response["durations"] = [[0]]
    response["distances"] = [[0]]
    record = road.cell_records(batch, payload, response, metadata)[0]
    assert record["model_duration_seconds"] == 0
    assert record["usable_duration_minutes"] is None
    assert record["route_status"] == "zero_model_duration_requires_local_review"


def test_missing_route_and_single_direction_not_averaged():
    origins, arrivals, batch, payload, response, metadata = fixture()
    records = road.cell_records(batch, payload, response, metadata)
    frames = road.build_outputs(origins, arrivals, records)
    assert len(frames["accessibility_road_reference_directional"]) == 27750
    pairs = frames["accessibility_road_reference_pairs"]
    target = pairs[pairs.municipality_bfs_id.eq(783) & pairs.access_point_id.eq(batch["access_point_ids"][0])].iloc[0]
    assert target.outbound_minutes == 2
    assert pd.isna(target.road_reference_minutes)
    assert target.return_status == "verified_endpoints_not_yet_queried"
    response["durations"] = [[None]]
    response["distances"] = [[None]]
    assert road.cell_records(batch, payload, response, metadata)[0]["route_status"] == "no_route_returned"


def test_incremental_extension_does_not_repeat_completed_pairs():
    complete = {(1, "a", "outbound"), (1, "a", "return")}
    jobs = road.missing_batches([1, 2], ["a", "b"], complete, 25)
    generated = {(bfs, access, job["direction"]) for job in jobs
                 for bfs in job["municipality_bfs_ids"] for access in job["access_point_ids"]}
    assert len(generated) == 6
    assert not generated & complete
    assert len(generated | complete) == 8


def test_response_shape_and_negative_values_rejected():
    _, _, _, payload, response, _ = fixture()
    broken = deepcopy(response)
    broken["durations"] = [[-1]]
    with pytest.raises(ValueError, match="Invalid"):
        road.validate_response(broken, payload)
    broken["durations"] = []
    with pytest.raises(ValueError, match="dimensions"):
        road.validate_response(broken, payload)


def test_real_archived_responses_resume_and_all_pending_ids_preserved():
    origins, arrivals, _, _, _, _ = fixture()
    config = json.loads((road.ROOT / road.CONFIG).read_text())
    records, successes = road.recover_completed(road.ROOT / "data_interim/accessibility_road_ors", origins, arrivals, config)
    assert len(records) == 6 and len(successes) == 2
    frames = road.build_outputs(origins, arrivals, records)
    directional, pairs = frames.values()
    assert len(directional) == 27750 and len(pairs) == 13875
    assert directional.municipality_bfs_id.nunique() == 185
    assert directional.access_point_id.nunique() == 75
    assert pairs.road_reference_minutes.notna().sum() == 3
    assert directional.route_status.eq("endpoint_evidence_pending").sum() == 27744
    assert pairs.winter_access_status.eq("not_yet_verified").all()
    assert pairs.final_walk_minutes.isna().all()
    dictionary = pd.read_csv(road.ROOT / "metadata/data_dictionary.csv")
    for table, frame in frames.items():
        assert set(dictionary[dictionary.table.eq(table)].variable) == set(frame)


def test_navigation_place_coordinate_not_viewport():
    arrivals = pd.read_csv(road.ROOT / OUTPUTS["accessibility_road_station_arrival_review"])
    twing = arrivals[arrivals.access_point_id.eq("ACCESS_MAGIC_CURRENT__4451")].iloc[0]
    assert twing.road_arrival_latitude == pytest.approx(46.7450222)
    assert twing.road_arrival_longitude == pytest.approx(8.1952418)
    assert twing.road_arrival_latitude != 46.7451822
    assert pd.isna(twing.final_walk_minutes)


def test_process_credential_fallback_is_not_logged(monkeypatch):
    import src.data_collection.road_reference_credentials as credentials
    monkeypatch.setattr(credentials.os, "name", "posix")
    monkeypatch.setenv("ORS_API_KEY", "synthetic-fixture-value")
    value, location = load_credential({"credential_environment_variable": "ORS_API_KEY",
                                      "alternative_credential_environment_variable": "OPENROUTESERVICE_API_KEY"})
    assert value == "synthetic-fixture-value"
    assert location == "process environment"
