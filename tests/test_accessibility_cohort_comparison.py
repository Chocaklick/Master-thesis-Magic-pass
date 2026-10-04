from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_option_c_comparison_rules_are_versioned_without_an_estimator() -> None:
    config = json.loads(
        (ROOT / "config" / "accessibility_cohort_comparison.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["researcher_approved_option"] == "C"
    assert config["accessibility_threshold_minutes"] == 120
    assert config["primary_donor_rule"] == (
        "not_yet_exposed_at_focal_cohort_or_never_exposed_in_current_120min_matrix"
    )
    assert config["not_yet_exposed_donor_censoring_rule"] == (
        "use_outcomes_strictly_before_own_first_exposure_month_only"
    )
    assert config["sensitivity_donor_rule"] == (
        "never_exposed_in_current_120min_matrix_only"
    )
    assert not config["outcome_window_selected"]
    assert not config["estimator_selected"]


def test_universe_is_exhaustive_and_roles_follow_exposure_timing() -> None:
    universe = read("reports/accessibility_cohort_comparison_universe.csv")
    assert len(universe) == 186 * 7
    assert universe.focal_cohort_month.nunique() == 7
    assert (
        universe.groupby("focal_cohort_month").municipality_bfs_id.nunique().eq(186).all()
    )
    roles = universe.primary_comparison_role.value_counts().to_dict()
    assert roles == {
        "donor_never_exposed": 742,
        "excluded_already_exposed": 344,
        "donor_not_yet_exposed": 136,
        "treated_in_focal_cohort": 80,
    }
    assert as_bool(universe.treated_in_focal_cohort).sum() == 80
    assert as_bool(universe.primary_donor_candidate_at_anchor).sum() == 878
    assert as_bool(universe.sensitivity_never_exposed_donor_candidate).sum() == 742
    not_yet = universe.primary_comparison_role.eq("donor_not_yet_exposed")
    assert universe.loc[not_yet, "primary_donor_use_end_exclusive"].eq(
        universe.loc[not_yet, "municipality_first_exposure_month_120min"]
    ).all()
    assert as_bool(universe.comparison_group_rule_selected).all()
    assert not as_bool(universe.outcome_window_selected).any()
    assert not as_bool(universe.comparability_screen_selected).any()
    assert not as_bool(universe.analysis_sample_selected).any()
    assert not as_bool(universe.estimator_selected).any()
    assert not as_bool(universe.causal_estimation_approved).any()


def test_cohort_counts_match_approved_primary_and_sensitivity_sets() -> None:
    cohorts = read("reports/accessibility_cohort_comparison_by_cohort.csv")
    assert cohorts.treated_municipalities.tolist() == [41, 3, 3, 16, 9, 5, 3]
    assert cohorts.primary_donor_municipalities.tolist() == [
        145,
        142,
        139,
        123,
        114,
        109,
        106,
    ]
    assert cohorts.primary_not_yet_exposed_donors.tolist() == [39, 36, 33, 17, 8, 3, 0]
    assert cohorts.primary_never_exposed_donors.eq(106).all()
    assert cohorts.sensitivity_never_exposed_donors.eq(106).all()
    assert cohorts.excluded_already_exposed_municipalities.tolist() == [
        0,
        41,
        44,
        47,
        63,
        72,
        77,
    ]
    assert not as_bool(cohorts.analysis_sample_selected).any()
    assert not as_bool(cohorts.estimator_selected).any()


def test_summary_and_provenance_keep_stage_28_noncausal() -> None:
    summary = json.loads(
        (ROOT / "reports" / "accessibility_cohort_comparison_summary.json").read_text(
            encoding="utf-8"
        )
    )
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    assert summary["municipality_cohort_rows"] == 1302
    assert summary["unique_first_exposed_municipalities"] == 80
    assert summary["unique_never_exposed_municipalities"] == 106
    assert summary["comparison_group_rule_selected"]
    assert not summary["outcome_window_selected"]
    assert not summary["comparability_screen_selected"]
    assert not summary["analysis_sample_selected"]
    assert not summary["estimator_selected"]
    assert not summary["causal_estimation_approved"]
    assert "DERIVED_ACCESSIBILITY_COHORT_COMPARISON_RULE" in set(sources.source_id)
    assert {
        "accessibility_cohort_comparison_universe",
        "accessibility_cohort_comparison_by_cohort",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
