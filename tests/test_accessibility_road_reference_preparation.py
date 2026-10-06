from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_processing import prepare_accessibility_road_reference as road


def test_approved_moutier_bridge_preserves_both_original_tp_records():
    nodes = pd.read_csv(ROOT / road.INPUTS[2], dtype=str, keep_default_na=False)
    mapping = pd.read_csv(ROOT / road.INPUTS[4], usecols=["source_municipality_bfs_id", "municipality_bfs_id"])
    result = road.prepare_origins(nodes, mapping)
    assert len(result) == result.municipality_bfs_id.nunique() == 185
    moutier = result[result.municipality_bfs_id.eq(6831)].iloc[0]
    assert set(moutier.source_municipality_bfs_ids.split("|")) == {"700", "6831"}
    records = json.loads(moutier.legacy_tp_origin_records)
    assert {r["source_municipality_bfs_id"] for r in records} == {700, 6831}
    assert all(r["selected_stop_id"] == "8500105" for r in records)
    assert result[["road_origin_latitude", "road_origin_longitude"]].isna().all().all()


def test_incomplete_territorial_mapping_does_not_silently_drop_origins():
    nodes = pd.read_csv(ROOT / road.INPUTS[2], dtype=str, keep_default_na=False)
    mapping = pd.read_csv(ROOT / road.INPUTS[4], usecols=["source_municipality_bfs_id", "municipality_bfs_id"])
    with pytest.raises(ValueError, match="no implicit discard"):
        road.prepare_origins(nodes, mapping[mapping.source_municipality_bfs_id.ne(700)])


def test_actual_arrivals_are_not_inferred_from_existing_coordinates():
    nodes = pd.read_csv(ROOT / road.INPUTS[3], dtype={"selected_stop_id": str}, keep_default_na=False)
    result = road.prepare_arrivals(nodes)
    assert len(result) == result.access_point_id.nunique() == 75
    assert result.station_group_id.nunique() == 71
    assert set(result.access_point_id) == set(nodes.access_point_id)
    assert not result.existing_reference_verified_as_road_arrival.any()
    assert result[["road_arrival_latitude", "road_arrival_longitude", "final_walk_minutes"]].isna().all().all()
    assert result.winter_access_status.eq("not_yet_verified").all()


def test_road_gates_and_published_provenance_are_consistent():
    config = json.loads((ROOT / road.CONFIG).read_text(encoding="utf-8"))
    assert config["road_primary_approved"] and config["public_transport_comparison_retained"]
    assert config["origin_definition_approved"] and config["station_arrival_definition_approved"]
    assert config["traffic_assumptions_approved"]
    assert "replacement" in config["traffic_approval_status"]
    assert config["routing_source_selected"] and config["routing_execution_authorized"]
    assert config["routing_provider"] == "openrouteservice"
    assert not config["threshold_selected"] and not config["canonical_exposure_replacement_approved"]
    summary = json.loads((ROOT / road.SUMMARY).read_text(encoding="utf-8"))
    assert summary["potential_territory_access_pairs"] == 13875
    assert summary["potential_directional_routes"] == 27750
    assert summary["actual_road_routes_computed"] == 0
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv", dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv", dtype=str, keep_default_na=False)
    assert not sources.source_id.duplicated().any()
    for table, path in road.OUTPUTS.items():
        frame = pd.read_csv(ROOT / path)
        assert set(dictionary[dictionary.table.eq(table)].variable) == set(frame.columns)
        assert road.sha(path) == summary["output_sha256"][path]
    assert all(road.sha(path) == value for path, value in summary["protected_legacy_sha256"].items())


def test_moutier_coordinate_is_exact_reviewed_original_not_fuzzy_geocoding():
    frame = pd.read_csv(ROOT / road.OUTPUTS["accessibility_road_origin_review"])
    result = frame[frame.municipality_bfs_id.eq(6831)].iloc[0]
    metadata = road.archived_metadata("MOUTIER_ADMINISTRATIVE_CENTRE_GEOADMIN_2026")
    response = json.loads((ROOT / metadata["raw_file"]).read_text(encoding="utf-8"))
    exact = [r["attrs"] for r in response["results"] if r["attrs"].get("featureId") == "1376503_0"]
    assert len(exact) == 1
    assert exact[0]["num"] == 1
    assert "2740 moutier 6831" in exact[0]["detail"]
    assert result.road_origin_latitude == pytest.approx(exact[0]["lat"], abs=1e-12)
    assert result.road_origin_longitude == pytest.approx(exact[0]["lon"], abs=1e-12)
    assert frame.road_origin_latitude.notna().sum() == 1
    arrivals = pd.read_csv(ROOT / road.OUTPUTS["accessibility_road_station_arrival_review"])
    leukerbad = arrivals[arrivals.access_point_id.eq("ACCESS_MAGIC_CURRENT__602")].iloc[0]
    assert "parking" in leukerbad.road_arrival_evidence_note
    assert pd.isna(leukerbad.road_arrival_latitude) and pd.isna(leukerbad.final_walk_minutes)


def test_batch_plan_preserves_every_direction_and_does_not_query_pending_points():
    from src.data_processing.plan_accessibility_road_matrix import plan_batches, PLAN
    batches = plan_batches(list(range(185)), [f"fixture_{i}" for i in range(75)], 25)
    assert len(batches) == 48
    assert sum(b["requested_cells"] for b in batches) == 27750
    pairs = [(b["direction"], m, a) for b in batches for m in b["municipality_bfs_ids"] for a in b["access_point_ids"]]
    assert len(pairs) == len(set(pairs)) == 27750
    assert all(b["requested_cells"] <= 625 for b in batches)
    with pytest.raises(ValueError, match="Duplicate"):
        plan_batches([1, 1], ["a"], 25)
    plan = json.loads((ROOT / PLAN).read_text(encoding="utf-8"))
    assert plan["status"] == "planning_only_no_api_request"
    assert plan["ready_origin_count"] == 1 and plan["ready_arrival_count"] == 0
    assert plan["ready_batches"] == 0


def test_modified_review_output_is_not_overwritten(tmp_path, monkeypatch):
    # Synthetic isolated fixture: simulate a user's edit, never alter the project.
    file = tmp_path / "review.csv"
    file.write_text("user evidence\n", encoding="utf-8")
    (tmp_path / "summary.json").write_text(json.dumps({"output_sha256": {"review.csv": "previous_checksum"}}), encoding="utf-8")
    monkeypatch.setattr(road, "ROOT", tmp_path)
    monkeypatch.setattr(road, "SUMMARY", "summary.json")
    monkeypatch.setattr(road, "PROTECTED", [])
    with pytest.raises(ValueError, match="preserve and integrate"):
        road.main()
    assert file.read_text(encoding="utf-8") == "user evidence\n"
