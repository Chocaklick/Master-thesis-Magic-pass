from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data_processing.audit_accessibility_local_thresholds import (
    FIELDS, OUTPUTS, SOURCE_ID, canonical_routes, threshold_inventory,
)

ROOT = Path(__file__).resolve().parents[1]


def outputs():
    return {key: pd.read_csv(ROOT / path) for key, path in OUTPUTS.items()}


def test_current_thresholds_reproduce_source_dates_and_moutier_once():
    detail = outputs()["accessibility_threshold_territories"]
    panel = pd.read_csv(ROOT / "data_processed/accessibility_municipality_month_exposure_territorial.csv", parse_dates=["date"], low_memory=False)
    assert len(detail) == 740
    for threshold in [30, 45, 60, 120]:
        scenario = detail[detail.threshold_minutes.eq(threshold)]
        assert len(scenario) == 185 and scenario.municipality_bfs_id.is_unique
        assert scenario.municipality_bfs_id.eq(6831).sum() == 1
        assert not scenario.municipality_bfs_id.eq(700).any()
        if threshold != 45:
            expected = panel[panel[f"active_station_group_count_{threshold}min"].gt(0)].groupby("municipality_bfs_id").date.min()
            actual = scenario[scenario.route_exposure_candidate].set_index("municipality_bfs_id").scenario_first_exposure_month.map(pd.Timestamp)
            pd.testing.assert_series_equal(expected.sort_index(), actual.sort_index(), check_names=False)


def test_monotone_route_counts_are_diagnostics_not_sample_selection():
    summary = outputs()["accessibility_threshold_summary"]
    assert summary.route_exposed_territories.tolist() == [5, 10, 30, 79]
    assert summary.territories_with_changed_first_date.tolist() == [0, 1, 8, 0]
    assert not summary.primary_replacement_approved.any()
    detail = outputs()["accessibility_threshold_territories"]
    previous = set()
    for threshold in [30, 45, 60, 120]:
        current = set(detail.loc[detail.threshold_minutes.eq(threshold) & detail.route_exposure_candidate, "municipality_bfs_id"])
        assert previous <= current
        previous = current
    config = json.loads((ROOT / "config/accessibility_local_threshold_audit.json").read_text(encoding="utf-8"))
    assert config["audit_scope_approved"]
    assert not any(config[key] for key in ["main_threshold_selected", "local_walking_rule_approved", "exposure_replacement_approved", "canonical_outputs_changed"])


def test_same_node_candidates_have_no_fabricated_zero_time_or_control_correction():
    local = outputs()["accessibility_local_node_audit"]
    shared = local[local.same_stop_local_candidate].set_index("municipality_bfs_id")
    assert set(shared.index) == {571, 783, 6111}
    assert shared.loc[783, "canonical_never_exposed_donor_cohorts"] == 7
    assert pd.isna(shared.loc[783, "first_exposure_month_120min"])
    assert shared.loc[6111, "first_effective_month"] == "2019-05-01"
    assert shared.loc[6111, "first_exposure_month_120min"] == "2023-05-01"
    assert shared.loc[[783, 6111], "mean_one_way_generalized_minutes"].isna().all()
    assert not shared.routing_pair_complete.loc[[783, 6111]].any()
    assert shared.loc[571, "same_stop_zero_vehicle_rejected_requests"] == 0
    assert shared.loc[571, "routing_pair_complete"]
    assert not local.primary_replacement_approved.any()


def test_complete_means_24_of_24_not_merely_one_trip_both_directions():
    local = outputs()["accessibility_local_node_audit"]
    known = local[local.hotel_territory_in_panel]
    complete = known.outbound_feasible_samples.eq(10) & known.return_feasible_samples.eq(14)
    assert np.array_equal(complete.to_numpy(), known.routing_pair_complete.to_numpy(bool))
    saas = known[known.station_group_name.eq("Saas-Fee")].iloc[0]
    assert saas.outbound_feasible_samples + saas.return_feasible_samples == 22
    assert saas.mean_one_way_generalized_minutes == pytest.approx(7.7)
    assert not saas.routing_pair_complete
    assert local.loc[~local.hotel_territory_in_panel, "mean_one_way_generalized_minutes"].isna().all()
    assert (~local.hotel_territory_in_panel).sum() == 45
    assert local.loc[~local.hotel_territory_in_panel, "selected_stop_municipality_bfs_id"].nunique() == 40


def test_zero_leg_rejections_keep_walk_only_separate_and_do_not_infer_duration():
    rejected = outputs()["accessibility_zero_vehicle_rejections"]
    assert rejected.loc[rejected.same_stop, "rejected_requests"].sum() == 48
    assert rejected.loc[~rejected.same_stop, "rejected_requests"].sum() == 10
    assert set(rejected.columns) == {"station_group_id", "municipality_bfs_id", "same_stop", "rejected_requests", "source_id"}
    assert rejected.municipality_bfs_id.isin([6111, 783, 5841]).all()


def test_moutier_route_bridge_rejects_inconsistent_values():
    routes = pd.DataFrame({"station_group_id": ["a", "a", "a"], "municipality_bfs_id": [700, 6831, 42], "municipality_name": ["old", "new", "other"], "mean_one_way_generalized_minutes": [40., 40., 70.]})
    assert canonical_routes(routes).municipality_bfs_id.tolist() == [6831, 42]
    routes.loc[1, "mean_one_way_generalized_minutes"] = 39.
    with pytest.raises(AssertionError):
        canonical_routes(routes)


def test_synthetic_thresholds_keep_calendar_gaps_zero_outcomes_and_documented_exit():
    dates = pd.date_range("2013-01-01", "2020-12-01", freq="MS")
    panel = pd.DataFrame({"date": dates, "municipality_bfs_id": 1, "municipality_name_source": "unit", "hotel_overnights": 0., "active_station_group_count_120min": (dates >= "2017-01-01").astype(int)})
    panel.loc[panel.date.eq("2017-02-01"), "hotel_overnights"] = np.nan
    groups = pd.DataFrame({"station_group_id": ["a", "b", "MP_GROUP_RESORT__expired"], "first_effective_month": ["2017-01-01", "2019-01-01", "2010-01-01"]})
    routes = pd.DataFrame({"station_group_id": groups.station_group_id, "station_group_name": ["a", "b", "expired"], "municipality_bfs_id": 1, "routing_pair_complete": True, "descriptive_accessibility_usable": True, "mean_one_way_generalized_minutes": [50., 40., 10.]})
    history = pd.DataFrame({"event_type": ["base_pass_exit"], "candidate_resort_id": ["expired"], "exit_date": ["2012-12-01"]})
    local = pd.DataFrame(columns=["same_stop_local_candidate", "station_group_id", "municipality_bfs_id", "first_effective_month", "selected_stop_municipality_bfs_id"]).astype({"same_stop_local_candidate": bool})
    detail, summary = threshold_inventory(routes, groups, panel, local, [40, 50], history)
    assert detail.scenario_first_exposure_month.tolist() == [pd.Timestamp("2019-01-01"), pd.Timestamp("2017-01-01")]
    assert detail.post_observed_months.tolist() == [24, 47]
    assert detail.qualifying_group_count.tolist() == [1, 2]
    assert summary.groups_with_route_exposure.tolist() == [1, 2]
    assert detail.reference_observed.all()  # Real zero is observed, not missing.
    assert detail.iloc[0].complete_pre36 == False
    assert detail.iloc[1].complete_pre36 == True


def test_provenance_and_checksums_cover_outputs_and_unchanged_canonical_files():
    manifest = json.loads((ROOT / "reports/accessibility_local_threshold_audit_summary.json").read_text(encoding="utf-8"))
    assert not manifest["canonical_outputs_changed"]
    assert not manifest["primary_replacement_approved"]
    for path, expected in {**manifest["input_sha256"], **manifest["output_sha256"]}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    assert hashlib.sha256((ROOT / "src/data_processing/audit_accessibility_local_thresholds.py").read_bytes()).hexdigest() == manifest["builder_sha256"]
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    assert sources.source_id.eq(SOURCE_ID).sum() == 1
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    for table, frame in outputs().items():
        registered = dictionary[dictionary.table.eq(table)].set_index("variable")
        assert set(registered.index) == set(frame.columns)
        assert set(frame) <= set(FIELDS)
        assert registered.source_id.eq(SOURCE_ID).all()
        assert registered.description.notna().all()
