from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.strip().str.lower().eq("true")


def test_treated_external_review_is_complete_traceable_and_non_causal() -> None:
    audit = read("reports/accessibility_treated_external_shock_evidence.csv")
    assert len(audit) == 14
    assert audit.municipality_bfs_id.is_unique
    assert as_bool(audit.external_treatment_review_completed).all()
    assert as_bool(audit.all_cited_sources_integrity_verified).all()
    source_ids = audit.review_source_ids.fillna("")
    assert source_ids.ne("").sum() == 13
    assert source_ids.eq("").sum() == 1
    assert audit.loc[
        source_ids.eq(""), "municipality_name"
    ].tolist() == ["Köniz"]
    assert not as_bool(audit.causal_treatment_approved).any()

    high = set(audit.loc[
        ~as_bool(audit.eligible_broad_reviewed_set), "municipality_bfs_id"
    ])
    moderate = set(audit.loc[
        as_bool(audit.eligible_broad_reviewed_set)
        & ~as_bool(audit.eligible_strict_magic_only_candidate_set),
        "municipality_bfs_id",
    ])
    assert high == {843, 5407, 5409, 5411, 5841}
    assert moderate == {2299, 6252}
    assert audit.loc[
        audit.municipality_bfs_id.eq(355),
        "largest_absolute_yoy_bed_change_phase",
    ].item() == "pre_anchor"


def test_pair_sets_are_nested_and_keep_all_causal_gates_closed() -> None:
    pairs = read("data_processed/accessibility_comparison_treated_external_risk_screen.csv")
    summary = json.loads((
        ROOT / "reports" / "accessibility_comparison_treated_external_review_summary.json"
    ).read_text(encoding="utf-8"))
    assert len(pairs) == 70
    assert not pairs.duplicated([
        "treated_municipality_bfs_id", "control_municipality_bfs_id"
    ]).any()
    stage18 = as_bool(pairs.retained_for_external_review)
    broad = as_bool(pairs.eligible_broad_reviewed_comparison_set)
    strict = as_bool(pairs.eligible_strict_magic_only_candidate_set)
    assert stage18.sum() == 50
    assert broad.sum() == 38
    assert strict.sum() == 32
    assert not (broad & ~stage18).any()
    assert not (strict & ~broad).any()
    assert pairs.loc[broad, "treated_municipality_bfs_id"].nunique() == 9
    assert pairs.loc[strict, "treated_municipality_bfs_id"].nunique() == 7
    assert summary["broad_reviewed_set_pairs"] == 38
    assert summary["strict_magic_only_candidate_pairs"] == 32
    assert summary["control_external_reviews_still_pending_for_retained_pairs"] == 50
    for column in [
        "parallel_trends_approved", "causal_treatment_approved",
        "causal_control_approved", "causal_pair_approved",
    ]:
        assert not as_bool(pairs[column]).any()


def test_stage19_sources_and_variables_are_registered() -> None:
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    required_sources = {
        "DERIVED_ACCESSIBILITY_TREATED_EXTERNAL_SHOCK_REVIEW",
        "ANNIVIERS_TOURISM_TAX_FLYER_2019",
        "BULLE_TOURISM_POSTULATE_2019",
        "FRIBOURG_PREALPS_2030_REPORT_2019",
        "FRIBOURG_YOUTH_HOSTEL_REPORT_2019",
        "LA_CHAUX_DE_FONDS_MANAGEMENT_REPORT_2019",
        "LEYSIN_CHAIRLIFT_PREAVIS_2017",
        "LEYSIN_SNOWMAKING_PREAVIS_2018",
        "OLLON_VILLARS_BATHS_PREAVIS_2017",
        "ORMONT_DESSUS_MEILLERET_PREAVIS_2018",
        "ORMONT_DESSUS_TVGD_LOAN_PREAVIS_2017",
        "PLAFFEIEN_TOURISM_AG_MINUTES_2019",
        "SAIGNELEGIER_INFO_JUNE_2019",
    }
    assert required_sources <= set(sources.source_id)
    assert {
        "accessibility_treated_external_shock_evidence",
        "accessibility_comparison_treated_external_risk_screen",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)
