import json

import pandas as pd
import pytest

from src.data_processing import prepare_accessibility_road_stop_reference as preparation
from src.data_processing import audit_accessibility_road_stop_snapping as audit
from src.data_collection import collect_accessibility_road_matrix as engine
from src.data_collection.collect_accessibility_road_stop_matrix import configure


@pytest.fixture
def stop_engine(monkeypatch):
    # Production configure runs once in its separate CLI process. Undo every
    # namespace field after each isolated test, keeping old endpoint tests exact.
    names = ["OUTPUTS", "PROTECTED", "ORIGIN_READY", "ARRIVAL_READY", "INVENTORY_SOURCE", "SOURCE", "TABLES", "SUMMARY",
        "CACHE_DIRECTORY", "RAW_DIRECTORY", "MEASUREMENT_LABEL", "RESUME_COMMAND", "EXTRA_INPUTS", "ENTRY_POINT", "APPROVED_ZERO_PAIRS"]
    for name in names:
        monkeypatch.setattr(engine, name, getattr(engine, name))
    configure()
    return engine


def test_all_stops_use_exact_original_ids_and_not_station_reference_coordinates():
    origins, arrivals = [pd.read_csv(preparation.ROOT / p, dtype={"selected_stop_id": str}) for p in preparation.OUTPUTS.values()]
    original = pd.read_csv(preparation.ROOT / preparation.INPUTS[3], dtype={"selected_stop_id": str}).set_index("access_point_id")
    assert len(origins) == origins.municipality_bfs_id.nunique() == 185
    assert len(arrivals) == arrivals.access_point_id.nunique() == 75
    assert arrivals.station_group_id.nunique() == 71
    assert arrivals.set_index("access_point_id").selected_stop_id.to_dict() == original.selected_stop_id.to_dict()
    moutier = origins[origins.municipality_bfs_id.eq(6831)].iloc[0]
    assert set(moutier.source_municipality_bfs_ids.split("|")) == {"700", "6831"}
    assert {r["selected_stop_id"] for r in json.loads(moutier.legacy_tp_origin_records)} == {"8500105"}
    assert origins.road_origin_latitude.notna().all() and arrivals.road_arrival_latitude.notna().all()
    assert arrivals.final_walk_minutes.isna().all()
    # Source-original LV95 exact values, no town hall or arbitrary centroid.
    assert moutier.bav_easting_2056 == 2595643 and moutier.bav_northing_2056 == 1236644


def test_bridge_with_different_selected_stops_requires_review():
    nodes = pd.read_csv(preparation.ROOT / preparation.INPUTS[2], dtype={"selected_stop_id": str})
    mapping = pd.read_csv(preparation.ROOT / preparation.INPUTS[4], usecols=["source_municipality_bfs_id", "municipality_bfs_id"])
    nodes.loc[nodes.municipality_bfs_id.eq(700), "selected_stop_id"] = "synthetic_different_stop"
    access = pd.read_csv(preparation.ROOT / preparation.INPUTS[3], dtype={"selected_stop_id": str})
    stops = pd.DataFrame({"Numero": []})
    # A first untouched commune is missing from this tiny fixture; test bridge
    # directly with only its approved two-history territory.
    nodes = nodes[nodes.municipality_bfs_id.isin([700, 6831])]
    mapping = mapping[mapping.source_municipality_bfs_id.isin([700, 6831])]
    with pytest.raises(ValueError, match="different TP origins"):
        preparation.endpoint_frames(nodes, mapping, access, stops)


def test_complete_matrix_resumes_without_any_new_cell(stop_engine):
    origins, arrivals = [pd.read_csv(preparation.ROOT / p) for p in preparation.OUTPUTS.values()]
    config = json.loads((engine.ROOT / engine.CONFIG).read_text(encoding="utf-8"))
    records, successes = engine.recover_completed(engine.ROOT / engine.CACHE_DIRECTORY, origins, arrivals, config)
    assert len(records) == 27750 and len(successes) == 48
    complete = {(r["municipality_bfs_id"], r["access_point_id"], r["direction"]) for r in records}
    assert not engine.missing_batches(sorted(origins.municipality_bfs_id), sorted(arrivals.access_point_id), complete, 25)
    frames = engine.build_outputs(origins, arrivals, records)
    directional, pairs = frames.values()
    assert len(directional) == 27750 and len(pairs) == 13875
    assert directional.route_status.value_counts().to_dict() == {"route_available": 27592, "no_route_returned": 150, "verified_same_tp_stop_zero": 6, "zero_model_duration_requires_local_review": 2}
    assert pairs.road_reference_minutes.notna().sum() == 13799
    assert pairs.road_reference_minutes.eq(0).sum() == 3
    saas = pairs[pairs.municipality_bfs_id.eq(6290) & pairs.access_point_id.eq("ACCESS_MAGIC_CURRENT__600")].iloc[0]
    assert pd.isna(saas.road_reference_minutes)
    assert set(directional.source_id) == {"ORS_DRIVING_CAR_TP_STOP_MATRIX_2026"}
    assert pairs.winter_access_status.eq("not_yet_verified").all()


def test_snap_displacements_are_not_walk_times_or_thresholds():
    assert audit.displacement(7, 46, "[7,46]") == pytest.approx(0)
    assert 70 < audit.displacement(7, 46, "[7.001,46]") < 90
    assert pd.isna(audit.displacement(7, 46, "null"))
    summary = json.loads((audit.ROOT / audit.SUMMARY).read_text(encoding="utf-8"))
    assert summary["acceptance_threshold"] is None and summary["automatically_excluded_communes"] == 0
    endpoints = pd.read_csv(audit.ROOT / audit.OUTPUTS["accessibility_road_stop_snapping_endpoints"])
    assert len(endpoints) == 260 and not endpoints.automatic_exclusion.any()
    assert not endpoints.snapping_not_observed.any()
    assert endpoints.max_reported_snap_metres.max() == pytest.approx(680.27)


def test_stop_and_old_result_sources_dictionary_and_hashes_remain_separate():
    summary = json.loads((preparation.ROOT / preparation.SUMMARY).read_text(encoding="utf-8"))
    assert all(preparation.sha(p) == value for p, value in summary["protected_legacy_and_refinement_sha256"].items())
    dictionary = pd.read_csv(preparation.ROOT / "metadata/data_dictionary.csv")
    for table, p in {**preparation.OUTPUTS, **audit.OUTPUTS}.items():
        assert set(dictionary[dictionary.table.eq(table)].variable) == set(pd.read_csv(preparation.ROOT / p).columns)
    assert not dictionary.duplicated(["table", "variable"]).any()
    sources = pd.read_csv(preparation.ROOT / "metadata/data_sources_master.csv")
    assert not sources.source_id.duplicated().any()
    assert {"ORS_DRIVING_CAR_STATIC_MATRIX_2026", "ORS_DRIVING_CAR_TP_STOP_MATRIX_2026", preparation.SOURCE, audit.SOURCE}.issubset(set(sources.source_id))


def test_exact_geocoding_rejects_postal_mismatch_and_duplicates():
    from src.data_processing.extend_accessibility_road_endpoint_evidence import exact_candidates
    candidate = dict(street="Mühlegasse 1", postcode=3000, municipality_bfs_id=351)
    attrs = dict(origin="address", detail="muehlegasse 1 3000 bern 351 bern ch be", featureId="synthetic")
    assert len(exact_candidates({"results": [{"attrs": attrs}]}, candidate)) == 1
    assert len(exact_candidates({"results": [{"attrs": attrs}, {"attrs": attrs}]}, candidate)) == 2
    attrs["detail"] = "muehlegasse 1 3011 bern 351 bern ch be"
    assert not exact_candidates({"results": [{"attrs": attrs}]}, candidate)
