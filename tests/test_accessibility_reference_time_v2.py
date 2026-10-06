from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/data_processing"))
import build_accessibility_reference_time_v2 as v2
from gtfs_static_router import Journey, DestinationProfile, MODE_BITS


def node(stop, access="point"):
    return pd.Series(dict(selected_stop_id=stop, selected_stop_name=stop,
                          component_resort_id=access, component_resort_name=access))


def query(journey, origin="A", destination="B"):
    return v2.revised_sample(dict(station_group_id="group", station_group_name="group",
        municipality_bfs_id=1, municipality_name="town"), "outbound_municipality_to_destination",
        "winter_weekday", "20260204", 28800, node(origin), node(destination), journey, 6, 480)


def test_initial_wait_removed_but_transfer_interval_retained():
    # 08:30 first boarding; arrive 09:30 with two vehicle legs.
    row = query(Journey(34200, 30600, MODE_BITS["bus"], 2))
    assert row["initial_wait_minutes"] == 30
    assert row["available_duration_minutes"] == 60
    assert row["generalized_elapsed_minutes"] == 90
    assert row["transfers"] == 1


def test_initial_coded_walking_is_not_removed_as_wait():
    row = query(Journey(34200, 30600, MODE_BITS["bus"], 1, 300))
    assert row["available_duration_minutes"] == 65
    assert row["initial_wait_minutes"] == 25
    assert row["initial_coded_walk_minutes"] == 5


def test_no_vehicle_local_access_is_pending_not_zero_or_missing_transport():
    row = query(Journey(28800, 28800, 0, 0), origin="A", destination="A")
    assert row["local_access_pending"]
    assert np.isnan(row["available_duration_minutes"])
    assert "pending_not_missing_transport" in row["journey_exclusion_reason"]
    row = query(Journey(28980, 28800, 0, 0))
    assert row["generalized_elapsed_minutes"] == 3
    assert np.isnan(row["available_duration_minutes"])
    assert row["local_access_status"].startswith("coded_transfer")


def evidence(minutes=5):
    return dict(municipality_bfs_id=1, access_point_id="point", actual_endpoints_verified=True,
        source_id="official", evidence_locator="page 2 exact endpoints",
        outbound_walk_minutes=minutes, return_walk_minutes=minutes)


def test_zero_requires_actual_endpoint_coincidence_not_stop_identity():
    with pytest.raises(ValueError, match="not proof"):
        v2.validate_local_evidence([evidence(0)])
    item = evidence(0)
    item["actual_origin_departure_coincidence_verified"] = True
    assert len(v2.validate_local_evidence([item])) == 1
    item = evidence()
    item["actual_endpoints_verified"] = False
    with pytest.raises(ValueError, match="documented actual endpoints"):
        v2.validate_local_evidence([item])


def test_documented_local_walk_can_exist_without_transport_itinerary(monkeypatch):
    monkeypatch.setattr(v2, "LOCAL_EVIDENCE", v2.validate_local_evidence([evidence(5)]))
    row = query(None)
    assert row["journey_feasible"]
    assert row["available_duration_minutes"] == 5
    assert row["local_duration_source_id"] == "official"
    assert not row["local_access_pending"]


def samples():
    rows = []
    for date, outbound, returning in [("20260204", [10., 80., np.nan], [30., np.nan]),
                                      ("20260207", [40., 70.], [60., 90.])]:
        for direction, values in [("outbound_municipality_to_destination", outbound),
                                  ("return_destination_to_municipality", returning)]:
            for i, value in enumerate(values):
                rows.append(dict(station_group_id="group", station_group_name="group",
                    municipality_bfs_id=1, municipality_name="town", reference_date=date,
                    direction=direction, requested_departure_time=str(i), access_point_id="point",
                    available_duration_minutes=value, local_access_pending=False))
    return pd.DataFrame(rows)


def test_daily_minima_then_two_day_mean_not_pooled_or_all_success_filter():
    daily, pairs = v2.aggregate(samples(), ["20260204", "20260207"])
    assert daily.daily_reference_minutes.tolist() == [20, 50]
    assert pairs.reference_time_minutes.iloc[0] == 35
    assert daily.outbound_available_departures.tolist() == [2, 2]
    assert daily.outbound_requested_departures.tolist() == [3, 2]
    assert daily.outbound_range_minutes.tolist() == [70, 30]


def test_missing_direction_and_day_are_not_imputed_or_silently_skipna():
    frame = samples()
    frame.loc[frame.reference_date.eq("20260207") & frame.direction.str.startswith("return"), "available_duration_minutes"] = np.nan
    daily, pairs = v2.aggregate(frame, ["20260204", "20260207"])
    assert daily.daily_reference_minutes.iloc[0] == 20
    assert pd.isna(daily.daily_reference_minutes.iloc[1])
    assert pairs.days_with_both_directions.iloc[0] == 1
    assert pd.isna(pairs.reference_time_minutes.iloc[0])
    assert daily.return_status.iloc[1].startswith("no_usable_itinerary")


def test_multiple_access_points_are_reselected_on_duration():
    frame = samples()
    additional = frame.iloc[[0]].copy()
    additional["access_point_id"] = "another"
    additional["available_duration_minutes"] = 5
    daily, pairs = v2.aggregate(pd.concat([frame, additional]), ["20260204", "20260207"])
    assert daily.outbound_min_minutes.iloc[0] == 5
    assert daily.outbound_winning_access_point_id.iloc[0] == "another"
    assert daily.outbound_available_departures.iloc[0] == 2
    assert pairs.reference_time_minutes.iloc[0] == 33.75


def test_local_pending_survives_another_usable_access_point():
    frame = samples()
    frame.loc[0, "local_access_pending"] = True
    frame.loc[0, "available_duration_minutes"] = np.nan
    daily, pairs = v2.aggregate(frame, ["20260204", "20260207"])
    assert daily.outbound_status.iloc[0] == "available_with_local_candidate_pending"
    assert pairs.local_access_pending.iloc[0]


def test_profile_initial_walk_metadata_leaves_legacy_schedule_unchanged():
    from test_gtfs_static_router import synthetic_network
    network = synthetic_network()
    network.cross_transfers[0] = [(1, 300)]
    profile = DestinationProfile(network, "C")
    profile.add(1, 30900, Journey(32400, 30900, MODE_BITS["bus"], 1))
    journey = profile.query("A", 28800)
    assert journey.first_departure_seconds == 30900
    assert journey.arrival_seconds == 32400
    assert journey.initial_walk_seconds == 300


def test_literature_does_not_confuse_modes_populations_or_record_counts():
    frame = pd.DataFrame(json.loads((ROOT / "config/accessibility_mobility_literature_review.json").read_text(encoding="utf-8")))
    ski = frame[frame.indicator.eq("Car arrival share, derived complement")].iloc[0]
    assert ski.value == pytest.approx(100 - 5.7)
    assert pd.isna(ski.sample_people)
    sb = frame[frame.source_id.eq("SAINT_BERNARD_SKI_MOBILITY_SURVEY_2008_WP2010")]
    assert sb[sb.indicator.eq("Car arrival share")].sample_records.sum() == 256
    assert sb.sample_people.isna().all()
    assert sb[sb.indicator.str.startswith("Excursionist")].sample_records.iloc[0] == 263
    app = frame[frame.source_id.eq("APPENZELL_OVERNIGHT_MOBILITY_STUDY_2024")]
    assert app.sample_people.sum() == 654


def test_additional_methodological_gates_remain_unapproved():
    config = json.loads((ROOT / v2.CONFIG).read_text(encoding="utf-8"))
    assert "two" in config["approved_day_rule"]
    assert not any(config[k] for k in ["threshold_selected", "reference_mode_selected", "origin_rule_changed",
                                       "station_nodes_changed", "canonical_exposure_changed", "historical_access_validated"])


def test_published_review_has_complete_dictionary_and_partial_walking_evidence():
    local = pd.read_csv(ROOT / "reports/accessibility_reference_time_v2_local_review.csv")
    literature = pd.read_csv(ROOT / "reports/accessibility_mobility_literature.csv")
    assert len(local) == 75 and len(literature) == 13
    shared = local[local.same_stop_local_candidate].set_index("municipality_bfs_id")
    assert shared.loc[6111, "documented_outbound_walk_minutes"] == 5
    assert shared.loc[783, "documented_outbound_walk_minutes"] == 0.5
    assert shared.documented_return_walk_minutes.isna().all()
    assert local.actual_local_duration_minutes.isna().all()
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    for table, frame in [("accessibility_reference_time_v2_local_review", local), ("accessibility_mobility_literature", literature)]:
        assert set(dictionary.loc[dictionary.table.eq(table), "variable"]) == set(frame.columns)
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv", keep_default_na=False).set_index("source_id")
    assert set(literature.source_id) <= set(sources.index)
    assert "Client Challenge" in sources.loc["TOGGENBURG_VISITOR_MOBILITY_SURVEY_2025", "quality_notes"]
    assert not sources.loc["SAINT_BERNARD_SKI_MOBILITY_SURVEY_2008_WP2010", "local_raw_file"]
    assert not sources.loc["ATE_RIDE_GLIDE_LAST_MILE_2010_2011", "local_raw_file"]


def test_legacy_files_preserved_and_first_checkpoint_integrity():
    import hashlib
    manifest = json.loads((ROOT / v2.MANIFEST).read_text(encoding="utf-8"))
    assert not manifest["canonical_outputs_changed"]
    assert all(v2.sha(path) == digest for path, digest in manifest["protected_legacy_sha256"].items())
    # This first point is already complete, so the test cannot race the active
    # writer of a later checkpoint. Never infer full routing from this test.
    code = hashlib.sha256("ACCESS_BAV__8530674".encode()).hexdigest()[:20]
    path = ROOT / "data_interim/accessibility_reference_time_v2/20260204" / (code + ".csv")
    meta = json.loads(path.with_suffix(".metadata.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == meta["sha256"]
    assert meta["rows"] == 2232 == len(pd.read_csv(path))
