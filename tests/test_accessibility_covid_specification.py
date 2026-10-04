from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_option_a_and_official_core_sensitivity_are_versioned() -> None:
    config = json.loads(
        (ROOT / "config" / "accessibility_covid_specification.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["researcher_approved_option"] == "A"
    assert config["primary_sample_month_policy"] == "retain_all_available_months_and_cohorts"
    assert config["common_shock_adjustment"] == "calendar_month_fixed_effects"
    assert not config["standalone_national_covid_dummy_in_primary_model"]
    assert config["core_period_exclusion_sensitivity"] == {
        "enabled": True,
        "start": "2020-03-01",
        "end": "2022-03-01",
    }
    assert config["foreign_share_baseline_window_selected_months"] is None
    assert config["foreign_share_aggregation_selected"] is None


def test_baseline_audit_is_exhaustive_nonselective_and_preperiod_only() -> None:
    audit = read(
        "reports/accessibility_covid_foreign_share_baseline_audit.csv",
        parse_dates=[
            "focal_cohort_month",
            "municipality_first_exposure_month_120min",
            "baseline_cutoff_month_exclusive",
        ],
    )
    assert len(audit) == 186 * 7
    assert audit.focal_cohort_month.nunique() == 7
    assert audit.groupby("focal_cohort_month").municipality_bfs_id.nunique().eq(186).all()
    assert as_bool(audit.baseline_ends_before_pandemic).all()
    assert as_bool(audit.baseline_ends_before_first_exposure).all()
    assert not as_bool(audit.analysis_sample_selected).any()
    assert not as_bool(audit.cohort_comparison_rule_selected).any()
    assert not as_bool(audit.causal_estimation_approved).any()


def test_candidate_window_counts_reconcile_without_choosing_one() -> None:
    summary = json.loads(
        (ROOT / "reports" / "accessibility_covid_specification_summary.json").read_text(
            encoding="utf-8"
        )
    )
    assert summary["municipality_cohort_rows"] == 1302
    assert summary["unique_first_exposed_municipalities"] == 80
    assert {
        horizon: values["rows_with_complete_baseline"]
        for horizon, values in summary["baseline_window_audit"].items()
    } == {"12": 1255, "24": 1242, "36": 1227}
    assert {
        horizon: values["first_exposed_with_complete_baseline"]
        for horizon, values in summary["baseline_window_audit"].items()
    } == {"12": 76, "24": 76, "36": 75}
    assert summary["foreign_share_baseline_window_selected_months"] is None
    assert summary["foreign_share_aggregation_selected"] is None
    assert not summary["analysis_sample_selected"]


def test_official_evidence_checksums_and_provenance_are_registered() -> None:
    summary = json.loads(
        (ROOT / "reports" / "accessibility_covid_specification_summary.json").read_text(
            encoding="utf-8"
        )
    )
    for metadata in summary["official_evidence"].values():
        path = ROOT / metadata["raw_file"]
        assert path.exists()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == metadata["sha256"]
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    required_sources = {
        "BFS_HOTEL_DEMAND_COVID_2020",
        "SWISS_FEDERAL_COUNCIL_COVID_DECISION_CHRONOLOGY",
        "DERIVED_ACCESSIBILITY_COVID_SPECIFICATION",
    }
    assert required_sources <= set(sources.source_id)
    assert "accessibility_covid_foreign_share_baseline_audit" in set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
