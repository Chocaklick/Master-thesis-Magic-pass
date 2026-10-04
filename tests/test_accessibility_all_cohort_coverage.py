from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_all_cohort_inventory_keeps_every_exposed_municipality_at_every_threshold() -> None:
    coverage = read("reports/accessibility_all_cohort_municipality_coverage.csv")
    counts = coverage.groupby("accessibility_threshold_minutes").municipality_bfs_id.nunique()
    assert counts.to_dict() == {30: 5, 60: 30, 90: 55, 120: 80}
    assert not as_bool(coverage.analysis_sample_selected).any()
    assert not as_bool(coverage.causal_treatment_approved).any()


def test_coverage_horizons_are_nested_without_using_covid_as_exclusion() -> None:
    coverage = read("reports/accessibility_all_cohort_municipality_coverage.csv")
    for _, row in coverage.iterrows():
        if bool(row.complete_observed_24_pre_24_post):
            assert bool(row.complete_observed_12_pre_12_post)
        if bool(row.complete_observed_12_pre_12_post):
            assert bool(row.complete_observed_6_pre_6_post)
    main = coverage[coverage.accessibility_threshold_minutes.eq(120)]
    assert as_bool(main.window_24_overlaps_existing_covid_sensitivity).any()
    assert (
        as_bool(main.window_24_overlaps_existing_covid_sensitivity)
        & as_bool(main.complete_observed_24_pre_24_post)
    ).any()


def test_all_group_and_cohort_outputs_are_complete_and_noncausal() -> None:
    groups = read("reports/accessibility_all_cohort_station_group_coverage.csv")
    cohorts = read("reports/accessibility_all_cohort_coverage_by_cohort.csv")
    assert len(groups) == 71 * 4
    assert groups.groupby("accessibility_threshold_minutes").station_group_id.nunique().eq(71).all()
    assert set(cohorts.accessibility_threshold_minutes) == {30, 60, 90, 120}
    assert not as_bool(groups.analysis_sample_selected).any()
    assert not as_bool(groups.causal_treatment_approved).any()
    assert not as_bool(cohorts.analysis_sample_selected).any()
    assert not as_bool(cohorts.causal_treatment_approved).any()


def test_stage26_summary_and_provenance_are_registered() -> None:
    summary = json.loads((
        ROOT / "reports" / "accessibility_all_cohort_coverage_summary.json"
    ).read_text(encoding="utf-8"))
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    assert summary["threshold_overview"]["120"]["municipalities_ever_exposed"] == 80
    assert summary["stage24_primary_treated_municipalities"] == 6
    assert summary["stage24_primary_first_exposure_groups_at_120min"] == 6
    assert (
        summary["threshold_overview"]["120"]["mechanical_coverage_by_horizon"]["6"]
        ["mechanically_additional_complete_municipalities_vs_stage24_primary"]
        == 70
    )
    assert not summary["analysis_sample_selected"]
    assert not summary["causal_estimation_approved"]
    assert "DERIVED_ACCESSIBILITY_ALL_COHORT_COVERAGE" in set(sources.source_id)
    assert {
        "accessibility_all_cohort_municipality_coverage",
        "accessibility_all_cohort_coverage_by_cohort",
        "accessibility_all_cohort_station_group_coverage",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
