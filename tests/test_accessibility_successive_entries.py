from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.causal_inference.audit_accessibility_successive_entries import residualize


ROOT = Path(__file__).resolve().parents[1]


def test_primary_network_path_keeps_all_post_rows_and_original_group_ids() -> None:
    config = json.loads((ROOT / "config/accessibility_successive_entries.json").read_text(encoding="utf-8"))
    summary = json.loads((ROOT / "reports/accessibility_successive_entry_summary.json").read_text(encoding="utf-8"))
    events = pd.read_csv(ROOT / "reports/accessibility_successive_entry_events.csv")
    groups = pd.read_csv(ROOT / "reports/accessibility_successive_entry_group_separability.csv")
    original = pd.read_csv(ROOT / "data_processed/accessibility_station_groups.csv")
    first = events.entry_type.eq("first_exposure")
    assert config["primary_successive_entry_rule_selected"]
    assert len(events) == 177 and first.sum() == 80
    assert events.loc[~first].municipality_bfs_id.nunique() == 46
    assert summary["current_territories_exposed"] == 79
    assert summary["current_territories_with_additional_entries"] == 45
    assert summary["distinct_current_territory_entry_months"] == 175
    assert not summary["administrative_id_harmonisation_applied"]
    assert events.loc[~first].multiple_groups_entering_same_month.sum() == 43
    assert events.loc[first].observed_post_months_all_available.sum() == 5580
    assert events.loc[first].observed_post_months_before_next_entry.sum() == 3118
    assert not events.municipality_entry_id.duplicated().any()
    assert (events.entering_station_group_ids.str.split("|").str.len() == events.entering_station_group_count).all()
    assert set(groups.station_group_id) == set(original.station_group_id)
    assert summary["additional_entries_with_observed_pre_and_post_segment"] == 94
    assert not summary["additional_effect_estimator_selected"]
    assert not summary["analysis_sample_selected"]
    assert not summary["causal_estimation_approved"]


def test_group_rank_audit_records_exact_duplicates_and_documented_exit() -> None:
    summary = json.loads((ROOT / "reports/accessibility_successive_entry_summary.json").read_text(encoding="utf-8"))
    design = summary["observed_design"]
    groups = pd.read_csv(ROOT / "reports/accessibility_successive_entry_group_separability.csv")
    assert design["group_columns_with_current_access"] == 45
    assert design["two_way_fixed_effect_rank"] == 41
    assert design["rank_deficiency"] == 4
    assert design["observed_outcome_rows"] == 28455
    assert len(design["exact_identical_observed_exposure_pairs"]) == 4
    assert groups.accessible_municipalities_120min.eq(0).sum() == 26
    assert design["documented_exits_preserved"] == [{
        "station_group_id": "MP_GROUP_RESORT__crans_montana_crans_montana",
        "last_active_month": "2020-04-01",
    }]
    for pair in design["exact_identical_observed_exposure_pairs"]:
        left = groups.set_index("station_group_id").loc[pair["station_group_id_left"]]
        assert pair["station_group_id_right"] in left.identical_observed_exposure_group_ids.split("|")


def test_unbalanced_two_way_projection_matches_direct_dummy_projection() -> None:
    units = np.array([1, 1, 1, 2, 2, 2, 3, 3])
    months = np.array([1, 2, 3, 1, 3, 4, 2, 4])
    matrix = np.array([[0, 1], [0, 0], [1, 0], [0, 1], [1, 1], [1, 0], [0, 1], [1, 1]], dtype=float)
    fixed_effects = np.column_stack([
        pd.get_dummies(units, dtype=float).to_numpy(),
        pd.get_dummies(months, dtype=float).to_numpy(),
    ])
    direct = matrix - fixed_effects @ np.linalg.lstsq(fixed_effects, matrix, rcond=None)[0]
    projected, iterations = residualize(matrix, units, months, 1e-12, 10000)
    assert iterations > 1
    np.testing.assert_allclose(projected, direct, atol=1e-11)
    np.testing.assert_allclose(fixed_effects.T @ projected, 0, atol=1e-11)


def test_successive_entry_sources_and_every_csv_variable_are_registered() -> None:
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    assert "DERIVED_ACCESSIBILITY_SUCCESSIVE_ENTRY_AUDIT" in set(sources.source_id)
    for table in ["accessibility_successive_entry_events", "accessibility_successive_entry_group_separability"]:
        columns = set(pd.read_csv(ROOT / f"reports/{table}.csv").columns)
        definitions = dictionary.loc[dictionary.table.eq(table)]
        assert columns == set(definitions.variable)
        assert definitions.source_id.eq("DERIVED_ACCESSIBILITY_SUCCESSIVE_ENTRY_AUDIT").all()
