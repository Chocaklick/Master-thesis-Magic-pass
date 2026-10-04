from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def test_orientation_a_does_not_approve_unselected_parameters_or_causality() -> None:
    config = json.loads((ROOT / "config/accessibility_cohort_time_estimator.json").read_text(encoding="utf-8"))
    assert config["researcher_approved_orientation"] == "A"
    assert config["estimator_orientation_selected"]
    assert config["linear_trend_role"] == "sensitivity_not_primary_counterfactual"
    for flag in ["parameter_bundle_approved", "analysis_sample_selected", "matching_rule_selected", "estimator_selected", "estimation_executed", "causal_estimation_approved"]:
        assert not config[flag]


def test_reference_support_is_counterfactual_not_a_reduced_panel() -> None:
    summary = json.loads((ROOT / "reports/accessibility_cohort_time_specification_support.json").read_text(encoding="utf-8"))
    assert summary["orientation_A_approved"]
    assert summary["counterfactual_support_only_not_sample_selection"]
    assert summary["exposed_territories_retained_in_inventory"] == 79
    assert summary["territories_with_proposed_reference_and_seasonal_fit"] == 76
    assert summary["all_observed_exposed_post_rows_retained_in_inventory"] == 5580
    assert {row["municipality_bfs_id"] for row in summary["missing_proposed_reference_or_fit"]} == {5892, 6037, 6513}
    assert summary["observed_exposed_post_rows_with_proposed_reference_and_fit"] + sum(row["observed_post_months_retained_in_inventory"] for row in summary["missing_proposed_reference_or_fit"]) == 5580
    assert not summary["parameter_bundle_approved"]
    assert not summary["estimation_executed"]


def test_support_source_and_json_projection_variables_are_registered() -> None:
    payload = json.loads((ROOT / "reports/accessibility_cohort_time_specification_support.json").read_text(encoding="utf-8"))
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    assert "DERIVED_ACCESSIBILITY_COHORT_TIME_SPECIFICATION" in set(sources.source_id)
    for table, keys in [
        ("accessibility_cohort_time_reference_support", set(payload["cohort_reference_support"][0])),
        ("accessibility_cohort_time_missing_histories", set(payload["missing_proposed_reference_or_fit"][0])),
        ("accessibility_cohort_time_specification_summary", {key for key, value in payload.items() if not isinstance(value, (list, dict))}),
    ]:
        assert keys == set(dictionary.loc[dictionary.table.eq(table)].variable)
    for path, checksum in payload["input_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == checksum
