from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_pilot_stack_is_balanced_and_weights_each_treated_equally() -> None:
    stack = read("data_processed/accessibility_pilot_stacked_panel.csv")
    primary = stack[stack.analysis_tier.eq("primary")].copy()
    relaxed = stack[stack.analysis_tier.eq("relaxed")].copy()
    assert len(primary) == (6 + 11) * 48
    assert len(relaxed) == (6 + 15) * 48
    assert primary.stack_treated_municipality_bfs_id.nunique() == 6
    assert primary.municipality_bfs_id.nunique() == 16
    assert primary.groupby("stack_unit_id").event_month.nunique().eq(48).all()
    assert set(primary.event_month) == set(range(-24, 24))

    weight_check = (
        primary.groupby(["stack_treated_municipality_bfs_id", "date", "is_treated_municipality"])
        .stack_unit_weight.sum()
        .unstack()
    )
    assert np.allclose(weight_check[False], 1.0)
    assert np.allclose(weight_check[True], 1.0)


def test_primary_pilot_matches_direct_equal_stack_gap_and_is_noncausal() -> None:
    stack = read("data_processed/accessibility_pilot_stacked_panel.csv")
    primary = stack[stack.analysis_tier.eq("primary")].copy()
    estimates = read("reports/accessibility_pilot_did_estimates.csv")
    reported = estimates[estimates.scenario_id.eq("primary_full_24m_post")].iloc[0]
    stack_dids = []
    for _, group in primary.groupby("stack_treated_municipality_bfs_id"):
        treated = group[as_bool(group.is_treated_municipality)].set_index("event_month").log_overnights
        controls = (
            group[~as_bool(group.is_treated_municipality)]
            .pivot(index="event_month", columns="municipality_bfs_id", values="log_overnights")
            .mean(axis=1)
        )
        gap = treated - controls
        stack_dids.append(gap[gap.index >= 0].mean() - gap[gap.index < 0].mean())
    assert np.isclose(reported.estimate_log_points, np.mean(stack_dids), atol=1e-12)
    assert np.isclose(reported.estimate_log_points, -0.07057086705997487, atol=1e-12)
    assert reported.municipality_cluster_count == 16
    assert not bool(reported.causal_estimation_approved)
    assert reported.interpretation == "non_causal_pilot_estimate"


def test_pilot_sensitivities_and_event_study_preserve_guardrails() -> None:
    estimates = read("reports/accessibility_pilot_did_estimates.csv")
    events = read("reports/accessibility_pilot_event_study.csv")
    influence = read("reports/accessibility_pilot_influence_sensitivity.csv")
    decomposition = read("reports/accessibility_pilot_treated_decomposition.csv")
    summary = json.loads((
        ROOT / "reports" / "accessibility_pilot_estimation_summary.json"
    ).read_text(encoding="utf-8"))
    assert len(estimates) == 4
    assert len(events) == 16
    assert len(influence) == 17
    assert len(decomposition) == 6
    assert decomposition.treated_municipality_bfs_id.is_unique
    assert not as_bool(decomposition.causal_effect_approved).any()
    assert np.isclose(
        decomposition.post_minus_pre_log_gap.mean(),
        estimates.loc[
            estimates.scenario_id.eq("primary_full_24m_post"), "estimate_log_points"
        ].iloc[0],
        atol=1e-12,
    )
    assert not as_bool(estimates.causal_estimation_approved).any()
    assert not as_bool(events.causal_effect_approved).any()
    assert not summary["causal_estimation_approved"]
    assert not summary["causal_effect_claim_allowed"]
    assert summary["primary_pair_count"] == 11
    assert summary["relaxed_pair_count"] == 15
    assert summary["primary_treated_municipalities"] == 6
    assert summary["primary_municipality_clusters"] == 16
    assert summary["primary_treated_retained_under_strict_published_2018_transfers"] == 0
    assert summary["primary_treated_retained_under_250m_proximity_transfer_sensitivity"] == 6

    conservative = estimates[
        estimates.scenario_id.eq("primary_excluding_targeted_sensitivity_controls")
    ].iloc[0]
    assert conservative.pair_count == 5
    assert conservative.stack_count == 4
    assert conservative.ci95_normal_lower_log_points < 0 < conservative.ci95_normal_upper_log_points
    pair_loo = influence[influence.diagnostic_type.eq("leave_one_pair_out")]
    treated_loo = influence[influence.diagnostic_type.eq("leave_one_treated_municipality_out")]
    assert len(pair_loo) == 11
    assert len(treated_loo) == 6


def test_stage24_provenance_is_registered() -> None:
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    assert "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION" in set(sources.source_id)
    assert {
        "accessibility_pilot_stacked_panel",
        "accessibility_pilot_did_estimates",
        "accessibility_pilot_event_study",
        "accessibility_pilot_influence_sensitivity",
        "accessibility_pilot_treated_decomposition",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
