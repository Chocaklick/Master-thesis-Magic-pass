from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_high_leverage_control_review_is_traceable_and_non_causal() -> None:
    audit = read("reports/accessibility_high_leverage_control_external_shock_evidence.csv")
    assert len(audit) == 7
    assert audit.municipality_bfs_id.is_unique
    assert set(audit.municipality_bfs_id) == {1024, 1068, 1103, 3216, 3298, 3953, 4201}
    assert audit.strict_pair_count.sum() == 15
    assert as_bool(audit.high_leverage_control_review_completed).all()
    assert as_bool(audit.all_cited_sources_integrity_verified).all()
    assert audit.review_source_ids.fillna("").ne("").all()
    assert not as_bool(audit.spillover_review_completed).any()
    assert not as_bool(audit.causal_control_approved).any()

    excluded = set(audit.loc[
        as_bool(audit.excluded_from_strict_candidate_by_review), "municipality_bfs_id"
    ])
    assert excluded == {1103, 3953}
    sursee = audit[audit.municipality_bfs_id.eq(1103)].iloc[0]
    assert sursee.largest_absolute_yoy_bed_change_date == "2019-06-01"
    assert sursee.largest_yoy_bed_change_pct > 0.9

    for path_list in audit.review_local_files:
        for relative in path_list.split("|"):
            assert (ROOT / relative).exists()


def test_stage20_pair_screen_removes_four_pairs_and_keeps_gates_closed() -> None:
    pairs = read(
        "data_processed/accessibility_comparison_high_leverage_control_external_risk_screen.csv"
    )
    summary = json.loads((
        ROOT / "reports" / "accessibility_comparison_high_leverage_control_review_summary.json"
    ).read_text(encoding="utf-8"))
    assert len(pairs) == 70
    assert not pairs.duplicated([
        "treated_municipality_bfs_id", "control_municipality_bfs_id"
    ]).any()
    before = as_bool(pairs.strict_candidate_before_high_leverage_control_review)
    reviewed = before & as_bool(pairs.high_leverage_control_review_completed)
    excluded = as_bool(pairs.strict_candidate_excluded_by_high_leverage_control_review)
    retained = as_bool(pairs.retained_in_strict_candidate_after_high_leverage_control_review)
    pending = as_bool(pairs.strict_candidate_control_external_review_pending)
    reviewed_retained = as_bool(
        pairs.strict_candidate_control_external_reviewed_and_retained
    )
    assert before.sum() == 32
    assert reviewed.sum() == 15
    assert excluded.sum() == 4
    assert reviewed_retained.sum() == 11
    assert retained.sum() == 28
    assert pending.sum() == 17
    assert pairs.loc[retained, "treated_municipality_bfs_id"].nunique() == 7
    assert set(pairs.loc[excluded, "control_municipality_bfs_id"]) == {1103, 3953}
    assert not as_bool(pairs.causal_control_approved_after_stage20).any()
    assert not as_bool(pairs.causal_pair_approved_after_stage20).any()

    assert summary["strict_candidate_pairs_after_high_leverage_control_review"] == 28
    assert summary["remaining_control_reviews"] == 17
    assert summary["causal_pairs_approved"] == 0


def test_remaining_worklist_and_stage20_provenance_are_complete() -> None:
    worklist = read("reports/accessibility_remaining_control_external_review_worklist.csv")
    assert len(worklist) == 17
    assert worklist.control_municipality_bfs_id.is_unique
    assert worklist.strict_candidate_pair_count.sum() == 17
    assert not as_bool(worklist.causal_control_approved).any()

    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    required_sources = {
        "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW",
        "EMMEN_ANNUAL_REPORT_2019",
        "VITZNAU_TOURISM_PROJECTS_RETROSPECTIVE_2021",
        "SURSEE_FOCUS_HOTEL_HISTORY",
        "LENZBURG_BARRACUDA_OPENING_2017",
        "LENZBURG_BARRACUDA_OPERATOR_CURRENT",
        "MAIENFELD_HEIDIDORF_GRANT_2017",
        "WALENSTADT_HOTEL_LOEWEN_RENOVATION_2018",
        "RORSCHACHERBERG_ANNUAL_REPORT_2019",
    }
    assert required_sources <= set(sources.source_id)
    assert {
        "accessibility_high_leverage_control_external_shock_evidence",
        "accessibility_comparison_high_leverage_control_external_risk_screen",
        "accessibility_remaining_control_external_review_worklist",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
