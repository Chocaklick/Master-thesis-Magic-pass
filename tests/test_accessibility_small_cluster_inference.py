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


def test_small_cluster_audit_reproduces_primary_pilot() -> None:
    inference = read("reports/accessibility_pilot_small_cluster_inference.csv").iloc[0]
    estimates = read("reports/accessibility_pilot_did_estimates.csv")
    primary = estimates[estimates.scenario_id.eq("primary_full_24m_post")].iloc[0]
    assert np.isclose(inference.estimate_log_points, primary.estimate_log_points, atol=1e-12)
    assert inference.treated_stack_count == 6
    assert inference.municipality_cluster_count == 16


def test_connected_components_preserve_reused_control_dependence() -> None:
    components = read("reports/accessibility_pilot_inference_components.csv", dtype=str).fillna("")
    assert len(components) == 5
    linked = components[components.reused_municipality_bfs_ids_linking_stacks.ne("")]
    assert len(linked) == 1
    assert linked.iloc[0].reused_municipality_bfs_ids_linking_stacks == "1024"
    assert set(linked.iloc[0].treated_stack_names.split("|")) == {"Bulle", "Gruyères"}


def test_small_cluster_references_remove_false_precision_and_keep_guardrails() -> None:
    inference = read("reports/accessibility_pilot_small_cluster_inference.csv").iloc[0]
    assert np.isclose(inference.component_sign_flip_two_sided_p_value, 0.1875)
    assert 0.09 < inference.treated_stack_t_two_sided_p_value < 0.11
    assert inference.treated_stack_t_ci95_lower_log_points < 0
    assert inference.treated_stack_t_ci95_upper_log_points > 0
    assert inference.component_sign_pattern_count == 32
    assert not bool(inference.sign_flip_is_random_assignment_test)
    assert not bool(inference.causal_estimation_approved)
    assert not bool(inference.causal_effect_claim_allowed)


def test_stage25_summary_and_provenance_are_registered() -> None:
    summary = json.loads((
        ROOT / "reports" / "accessibility_pilot_small_cluster_inference_summary.json"
    ).read_text(encoding="utf-8"))
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    assert summary["connected_component_count"] == 5
    assert not summary["causal_effect_claim_allowed"]
    assert {
        "DERIVED_ACCESSIBILITY_SMALL_CLUSTER_INFERENCE",
        "CANAY_ROMANO_SHAIKH_APPROXIMATE_SYMMETRY_2017",
        "MACKINNON_WEBB_WILD_BOOTSTRAP_FEW_CLUSTERS_2018",
    } <= set(sources.source_id)
    assert {
        "accessibility_pilot_small_cluster_inference",
        "accessibility_pilot_inference_components",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
