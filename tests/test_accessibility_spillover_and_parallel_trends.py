from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_operational_basin_screen_is_complete_but_not_global_clearance() -> None:
    audit = read("reports/accessibility_pair_spillover_evidence.csv")
    pairs = read("data_processed/accessibility_comparison_spillover_screen.csv")
    summary = json.loads((
        ROOT / "reports" / "accessibility_pair_spillover_summary.json"
    ).read_text(encoding="utf-8"))
    assert len(audit) == 21
    assert not audit.duplicated([
        "treated_municipality_bfs_id", "control_municipality_bfs_id"
    ]).any()
    assert as_bool(audit.pair_spillover_review_completed).all()
    assert as_bool(audit.direct_local_spillover_low_risk_by_declared_proxies).all()
    assert as_bool(audit.eligible_for_parallel_trend_diagnostic).all()
    assert not as_bool(audit.official_destination_boundary_used_as_hard_gate).any()
    assert not as_bool(audit.causal_spillover_clearance_approved).any()
    assert set(audit.broad_visitor_market_substitution_status) == {
        "unresolved_national_or_interregional_substitution_not_testable_from_distance"
    }
    assert audit.treated_control_representative_distance_km.min() > 50
    observed = audit.control_current_scheduled_nearest_treated_entry_group_minutes.dropna()
    assert len(observed) == 20
    assert observed.min() > 120

    advanced = as_bool(pairs.retained_for_parallel_trend_diagnostic_after_spillover_screen)
    assert advanced.sum() == 21
    assert not as_bool(pairs.parallel_trends_approved_after_stage22).any()
    assert not as_bool(pairs.causal_pair_approved_after_stage22).any()
    assert summary["broad_market_substitution_cleared_pairs"] == 0


def test_predeclared_parallel_trend_rules_are_nested_and_non_causal() -> None:
    rules = json.loads((
        ROOT / "config" / "accessibility_parallel_trend_rules.json"
    ).read_text(encoding="utf-8"))
    audit = read("reports/accessibility_parallel_trend_diagnostics.csv")
    pairs = read("data_processed/accessibility_comparison_parallel_trend_screen.csv")
    core = read("reports/accessibility_estimation_candidate_pairs.csv")
    summary = json.loads((
        ROOT / "reports" / "accessibility_parallel_trend_summary.json"
    ).read_text(encoding="utf-8"))

    assert rules["protected_flags"] == {
        "parallel_trends_approved": False,
        "causal_pair_approved": False,
    }
    assert len(audit) == 21
    primary = as_bool(audit.primary_pretrend_rule_passed)
    sensitivity = as_bool(audit.sensitivity_pretrend_rule_passed)
    assert primary.sum() == 11
    assert sensitivity.sum() == 15
    assert not (primary & ~sensitivity).any()
    assert audit.loc[primary, "treated_municipality_bfs_id"].nunique() == 6
    assert set(audit.loc[
        audit.treated_municipality_name.eq("Haut-Intyamon"), "pretrend_diagnostic_class"
    ]) == {"fails_predeclared_pretrend_magnitude_rule"}
    assert len(core) == 15
    assert set(core.estimation_candidate_tier) == {"primary", "relaxed_sensitivity_only"}
    assert not as_bool(core.causal_estimation_approved).any()
    assert not as_bool(audit.parallel_trends_approved).any()
    assert not as_bool(audit.causal_pair_approved).any()
    assert not as_bool(pairs.parallel_trends_approved_after_stage23).any()
    assert not as_bool(pairs.causal_pair_approved_after_stage23).any()
    assert summary["primary_compatible_pairs"] == 11
    assert summary["sensitivity_only_pairs"] == 4
    assert summary["pairs_failing_sensitivity_rule"] == 6


def test_stage22_stage23_provenance_is_registered() -> None:
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    assert {
        "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN",
        "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC",
    } <= set(sources.source_id)
    assert {
        "accessibility_pair_spillover_evidence",
        "accessibility_comparison_spillover_screen",
        "accessibility_parallel_trend_worklist",
        "accessibility_parallel_trend_diagnostics",
        "accessibility_comparison_parallel_trend_screen",
        "accessibility_estimation_candidate_pairs",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
