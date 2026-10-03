from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_remaining_control_review_is_complete_traceable_and_non_causal() -> None:
    audit = read("reports/accessibility_remaining_control_external_shock_evidence.csv")
    assert len(audit) == 17
    assert audit.municipality_bfs_id.is_unique
    assert audit.strict_pair_count.sum() == 17
    assert as_bool(audit.remaining_control_review_completed).all()
    assert as_bool(audit.all_cited_sources_integrity_verified).all()
    assert audit.review_source_ids.fillna("").ne("").all()
    assert not as_bool(audit.spillover_review_completed).any()
    assert not as_bool(audit.causal_control_approved).any()

    excluded = set(audit.loc[
        as_bool(audit.excluded_from_strict_candidate_by_review), "municipality_bfs_id"
    ])
    assert excluded == {191, 230, 938, 1301, 3022, 3101, 4401}
    assert as_bool(audit.retained_in_strict_candidate_after_review).sum() == 10
    arbon = audit[audit.municipality_bfs_id.eq(4401)].iloc[0]
    assert arbon.hotel_beds_mean_change_post_vs_pre_pct < -0.2

    for path_list in audit.review_local_files:
        for relative in path_list.split("|"):
            assert (ROOT / relative).exists()


def test_stage21_pair_screen_retains_21_candidates_and_keeps_gates_closed() -> None:
    pairs = read("data_processed/accessibility_comparison_full_control_external_risk_screen.csv")
    summary = json.loads((
        ROOT / "reports" / "accessibility_comparison_full_control_review_summary.json"
    ).read_text(encoding="utf-8"))
    assert len(pairs) == 70
    assert not pairs.duplicated([
        "treated_municipality_bfs_id", "control_municipality_bfs_id"
    ]).any()
    before = as_bool(pairs.strict_candidate_before_remaining_control_review)
    excluded = as_bool(pairs.strict_candidate_excluded_by_remaining_control_review)
    retained = as_bool(pairs.retained_in_strict_candidate_after_full_control_review)
    completed = as_bool(pairs.strict_candidate_all_local_control_reviews_complete)
    assert before.sum() == 28
    assert excluded.sum() == 7
    assert retained.sum() == 21
    assert completed.sum() == 21
    assert pairs.loc[retained, "treated_municipality_bfs_id"].nunique() == 7
    assert pairs.loc[retained, "control_municipality_bfs_id"].nunique() == 15
    assert not as_bool(pairs.visitor_market_spillover_review_completed_after_stage21).any()
    assert not as_bool(pairs.causal_control_approved_after_stage21).any()
    assert not as_bool(pairs.causal_pair_approved_after_stage21).any()

    assert summary["remaining_controls_reviewed"] == 17
    assert summary["strict_candidate_pairs_after_full_local_control_review"] == 21
    assert summary["spillover_pairs_pending"] == 21
    assert summary["causal_pairs_approved"] == 0


def test_spillover_worklist_and_stage21_provenance_are_complete() -> None:
    worklist = read("reports/accessibility_spillover_review_worklist.csv")
    assert len(worklist) == 21
    assert not worklist.duplicated([
        "treated_municipality_bfs_id", "control_municipality_bfs_id"
    ]).any()
    assert as_bool(worklist.strict_candidate_all_local_control_reviews_complete).all()
    assert set(worklist.visitor_market_spillover_review_status) == {"pending"}
    assert not as_bool(worklist.causal_pair_approved).any()

    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    config = json.loads((
        ROOT / "config" / "accessibility_remaining_control_external_shock_review.json"
    ).read_text(encoding="utf-8"))
    required_sources = {
        "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW",
        *(source_id for row in config for source_id in row["source_ids"]),
    }
    assert required_sources <= set(sources.source_id)
    assert {
        "accessibility_remaining_control_external_shock_evidence",
        "accessibility_comparison_full_control_external_risk_screen",
        "accessibility_spillover_review_worklist",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
