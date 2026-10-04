from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.causal_inference.build_accessibility_dynamic_event_time_audit import (
    build_month_frame,
)


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def test_dynamic_time_rule_is_versioned_without_selecting_an_estimator() -> None:
    config = json.loads(
        (ROOT / "config" / "accessibility_dynamic_event_time.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["primary_temporal_design_selected"]
    assert not config["fixed_symmetric_primary_horizon_selected"]
    assert [item["label"] for item in config["post_effect_bins"]] == [
        "0_5_months",
        "6_11_months",
        "12_23_months",
        "24_plus_months",
    ]
    assert config["common_support_sensitivity_horizons_months"] == [6, 12, 24]
    assert not config["successive_entry_handling_selected"]
    assert not config["estimator_selected"]
    assert not config["causal_estimation_approved"]


def test_cohort_month_support_reports_changing_composition() -> None:
    support = read("reports/accessibility_dynamic_event_time_support_by_cohort_month.csv")
    assert support.focal_cohort_month.nunique() == 7
    assert support.calendar_month.nunique() == 159
    assert support.event_month.min() < 0
    assert support.event_month.max() >= 100
    assert set(support.post_effect_bin) == {
        "pre_treatment",
        "0_5_months",
        "6_11_months",
        "12_23_months",
        "24_plus_months",
    }
    at_anchor = support.loc[support.event_month.eq(0)].sort_values(
        "focal_cohort_month"
    )
    assert at_anchor.primary_donor_eligible_municipalities.tolist() == [
        145,
        142,
        139,
        123,
        114,
        109,
        106,
    ]
    assert as_bool(support.primary_temporal_design_selected).all()
    assert not as_bool(support.fixed_symmetric_primary_horizon_selected).any()
    assert not as_bool(support.analysis_sample_selected).any()
    assert not as_bool(support.estimator_selected).any()
    assert not as_bool(support.causal_estimation_approved).any()


def test_summary_reconciles_common_horizons_and_successive_entries() -> None:
    summary = json.loads(
        (ROOT / "reports" / "accessibility_dynamic_event_time_summary.json").read_text(
            encoding="utf-8"
        )
    )
    counts = {
        row["horizon_months_each_side"]: row["treated_municipalities_complete"]
        for row in summary["common_support_sensitivities"]
    }
    assert counts == {6: 76, 12: 73, 24: 65}
    assert all(
        row["treated_municipalities_complete_at_all_three_horizons"] == 65
        for row in summary["common_support_sensitivities"]
    )
    assert summary["treated_municipalities"] == 80
    assert summary["treated_municipalities_with_at_least_one_observed_post_month"] == 80
    assert summary["treated_municipalities_with_observed_pre_and_post_support"] == 76
    assert summary["treated_municipalities_with_any_later_accessible_entry"] == 46
    censoring = summary["next_entry_censoring_counterfactual_support_only"]
    assert censoring["observed_post_rows_before_next_entry"] == 3118
    assert censoring["municipalities_with_any_observed_post_row_before_next_entry"] == 77
    assert not censoring["rule_applied_to_analytical_sample"]
    assert summary["supported_post_event_month_start"] == 0
    assert summary["supported_post_event_month_end"] >= 100
    assert not summary["successive_entry_handling_selected"]
    assert not summary["analysis_sample_selected"]
    assert not summary["estimator_selected"]
    assert not summary["causal_estimation_approved"]


def test_dynamic_support_provenance_is_registered() -> None:
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    assert "DERIVED_ACCESSIBILITY_DYNAMIC_EVENT_TIME_SUPPORT" in set(
        sources.source_id
    )
    assert {
        "accessibility_dynamic_event_time_support_by_cohort_month",
        "accessibility_dynamic_event_time_support_by_event_month",
    } <= set(dictionary.table)
    assert set(dictionary.source_id) <= set(sources.source_id)


def test_future_donor_exits_at_own_exposure_and_later_entry_flag_starts_on_entry() -> None:
    config = json.loads(
        (ROOT / "config" / "accessibility_dynamic_event_time.json").read_text(
            encoding="utf-8"
        )
    )
    universe = pd.DataFrame({
        "municipality_bfs_id": [1, 2, 3, 4],
        "focal_cohort_month": ["2022-05-01"] * 4,
        "municipality_first_exposure_month_120min": [
            "2022-05-01", "2022-07-01", None, "2022-04-01"
        ],
        "treated_in_focal_cohort": [True, False, False, False],
        "primary_donor_candidate_at_anchor": [False, True, True, False],
        "sensitivity_never_exposed_donor_candidate": [False, False, True, False],
        "primary_comparison_role": [
            "treated_in_focal_cohort", "donor_not_yet_exposed",
            "donor_never_exposed", "excluded_already_exposed"
        ],
    })
    panel = pd.DataFrame([
        {
            "municipality_bfs_id": bfs_id, "date": date,
            "hotel_overnights": None if bfs_id == 3 and date == "2022-06-01" else 10,
            "new_station_group_entry_count_120min": int(
                bfs_id == 1 and date in {"2022-05-01", "2022-07-01"}
            ),
            "active_station_group_count_120min": 0,
        }
        for bfs_id in [1, 2, 3, 4]
        for date in ["2022-04-01", "2022-05-01", "2022-06-01", "2022-07-01"]
    ])
    frame = build_month_frame(config, universe, panel)
    future = frame.loc[frame.municipality_bfs_id.eq(2)]
    assert future.primary_donor_month_eligible.tolist() == [True, True, True, False]
    assert not frame.loc[
        frame.municipality_bfs_id.eq(4), "primary_donor_month_eligible"
    ].any()
    treated = frame.loc[frame.municipality_bfs_id.eq(1)]
    assert treated.event_month.tolist() == [-1, 0, 1, 2]
    assert treated.treated_additional_entry_reached.tolist() == [False, False, False, True]
    missing = frame.loc[
        frame.municipality_bfs_id.eq(3) & frame.date.eq(pd.Timestamp("2022-06-01"))
    ].iloc[0]
    assert missing.primary_donor_month_eligible
    assert not missing.primary_donor_outcome_observed
