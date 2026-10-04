from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.causal_inference.audit_accessibility_all_cohort_comparability import paired_metrics, trend

ROOT = Path(__file__).resolve().parents[1]


def test_all_territories_and_approved_pairs_are_audited_without_filtering() -> None:
    audit = pd.read_csv(ROOT / "reports/accessibility_all_cohort_comparability_municipalities.csv")
    pairs = pd.read_csv(ROOT / "reports/accessibility_all_cohort_comparability_pairs.csv")
    universe = pd.read_csv(ROOT / "reports/accessibility_cohort_comparison_universe_territorial.csv")
    assert len(audit) == 316 and audit.municipality_bfs_id.nunique() == 79
    assert audit.groupby("municipality_bfs_id").diagnostic_pre_window_months.apply(set).eq({6, 12, 24, 36}).all()
    expected = set()
    for cohort, local in universe.groupby("focal_cohort_month"):
        treated = local.loc[local.treated_in_focal_cohort].municipality_bfs_id
        donors = local.loc[local.primary_donor_candidate_at_anchor].municipality_bfs_id
        expected.update((cohort, int(a), int(b)) for a in treated for b in donors)
    assert set(zip(pairs.focal_cohort_month, pairs.treated_municipality_bfs_id, pairs.control_municipality_bfs_id)) == expected
    assert pairs.diagnostic_pre_end.lt(pairs.focal_cohort_month).all()
    assert not pairs.duplicated(["focal_cohort_month", "treated_municipality_bfs_id", "control_municipality_bfs_id"]).any()
    assert not audit.municipality_bfs_id.eq(700).any()
    missing = audit.loc[audit.observed_pre_outcome_months.eq(0)].municipality_bfs_id.unique()
    assert set(missing) == {5892, 6037, 6513}
    for frame in [audit, pairs]:
        for flag in ["automatic_exclusion_applied", "former_pilot_design_decisions_applied", "analysis_sample_selected", "estimator_selected", "causal_estimation_approved"]:
            assert not frame[flag].any()


def test_actual_calendar_time_is_not_compressed_by_missing_months() -> None:
    dates = pd.date_range("2015-01-01", periods=48, freq="MS")
    values = 0.02*np.arange(48) + np.sin(dates.month.to_numpy())
    values[[2, 10, 19, 26, 37]] = np.nan
    slope, status = trend(values, dates)
    np.testing.assert_allclose(slope, 0.02, atol=1e-12)
    assert status.startswith("descriptive_full_rank")
    short_slope, short_status = trend(values[:12], dates[:12])
    assert np.isnan(short_slope) and short_status.startswith("insufficient")
    empty_slope, _ = trend(np.full(48, np.nan), dates)
    assert np.isnan(empty_slope)


def test_pair_overlap_seasonal_distance_and_missingness() -> None:
    dates = pd.date_range("2015-01-01", periods=36, freq="MS")
    left = np.arange(36, dtype=float)/100 + np.cos(dates.month.to_numpy())
    right = left.copy() + 2
    right[5] = np.nan
    result = paired_metrics(left, right, dates)
    assert result["paired_pre_observed_months"] == 35
    assert not result["paired_pre_complete"]
    assert result["seasonal_profile_calendar_months"] == 12
    np.testing.assert_allclose(result["pre_log_outcome_correlation"], 1)
    np.testing.assert_allclose(result["pre_seasonal_profile_rmse"], 0, atol=1e-12)
    np.testing.assert_allclose(result["seasonally_adjusted_monthly_difference_trend"], 0, atol=1e-12)
    absent = paired_metrics(np.full(36, np.nan), right, dates)
    assert absent["paired_pre_observed_months"] == 0
    assert np.isnan(absent["pre_log_outcome_correlation"])


def test_registered_variables_and_inherited_reviews_are_not_new_approvals() -> None:
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    assert "DERIVED_ACCESSIBILITY_ALL_COHORT_COMPARABILITY_AUDIT" in set(sources.source_id)
    for name in ["municipalities", "pairs"]:
        table = "accessibility_all_cohort_comparability_" + name
        frame = pd.read_csv(ROOT / f"reports/{table}.csv")
        assert set(frame.columns) == set(dictionary.loc[dictionary.table.eq(table)].variable)
    audit = pd.read_csv(ROOT / "reports/accessibility_all_cohort_comparability_municipalities.csv")
    assert not audit.existing_shock_review_applicable_to_focal_window_validated.any()
    assert audit.loc[~audit.existing_shock_review_available].existing_shock_review_limits.str.contains("not established").all()
    summary = json.loads((ROOT / "reports/accessibility_all_cohort_comparability_summary.json").read_text(encoding="utf-8"))
    assert not summary["matching_rule_selected"]
    assert not summary["analysis_sample_selected"]
