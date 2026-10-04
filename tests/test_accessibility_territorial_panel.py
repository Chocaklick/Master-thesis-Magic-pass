from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.data_processing.build_accessibility_territorial_panel import bridge_panel

ROOT = Path(__file__).resolve().parents[1]


def config() -> dict:
    return json.loads((ROOT / "config/accessibility_outcome_territorial_harmonisation.json").read_text(encoding="utf-8"))


def test_bridge_keeps_every_original_value_and_monthly_source_id() -> None:
    original = pd.read_csv(ROOT / "data_processed/accessibility_municipality_month_exposure.csv")
    panel = pd.read_csv(ROOT / config()["analytical_panel"], low_memory=False)
    assert len(panel) == 31080 and panel.municipality_bfs_id.nunique() == 185
    assert not panel.duplicated(["municipality_bfs_id", "date"]).any()
    assert not panel.municipality_bfs_id.eq(700).any()
    keys = ["municipality_bfs_id", "date"]
    lineage = panel.assign(municipality_bfs_id=panel.source_municipality_bfs_id)
    observed = original.set_index(keys).loc[pd.MultiIndex.from_frame(lineage[keys])].reset_index()
    pd.testing.assert_frame_equal(lineage[original.columns].reset_index(drop=True), observed[original.columns], check_exact=False, rtol=1e-14, atol=1e-12)
    assert panel.hotel_overnights.notna().sum() == original.hotel_overnights.notna().sum() == 28455
    assert panel.hotel_overnights.sum() == original.hotel_overnights.sum()
    moutier = panel.loc[panel.municipality_bfs_id.eq(6831)]
    assert moutier.hotel_overnights.notna().sum() == 157
    assert moutier.loc[moutier.date.lt("2026-01-01")].source_municipality_bfs_id.eq(700).all()
    assert moutier.loc[moutier.date.ge("2026-01-01")].source_municipality_bfs_id.eq(6831).all()
    assert moutier.territorial_source_bfs_ids.eq("700|6831").all()
    assert moutier.territorial_mutation_source_id.eq("BFS_MUNICIPAL_MUTATION_3999").all()


def test_bridge_refuses_imputation_or_discarding_an_observed_parallel_value() -> None:
    original = pd.read_csv(ROOT / "data_processed/accessibility_municipality_month_exposure.csv")
    unapproved = config() | {"researcher_approved": False}
    with pytest.raises(ValueError, match="approved"):
        bridge_panel(unapproved, original)
    conflicting = original.copy()
    conflicting.loc[conflicting.municipality_bfs_id.eq(700) & conflicting.date.eq("2026-01-01"), "hotel_overnights"] = 1
    with pytest.raises(ValueError, match="source value"):
        bridge_panel(config(), conflicting)


def test_cohort_roles_baseline_and_territorial_support_reconcile() -> None:
    settings = config()
    universe = pd.read_csv(ROOT / settings["comparison_universe"])
    baseline = pd.read_csv(ROOT / settings["selected_foreign_share"])
    assert len(universe) == len(baseline) == 1295
    assert not universe.duplicated(["municipality_bfs_id", "focal_cohort_month"]).any()
    assert universe.treated_in_focal_cohort.sum() == 79
    assert (universe.treated_in_focal_cohort & universe.selected_foreign_share_available).sum() == 76
    assert universe.groupby("focal_cohort_month").primary_donor_candidate_at_anchor.sum().tolist() == [145, 142, 139, 123, 114, 109, 106]
    assert universe.groupby("focal_cohort_month").sensitivity_never_exposed_donor_candidate.sum().eq(106).all()
    original = pd.read_csv(ROOT / "reports/accessibility_covid_foreign_share_selected.csv")
    pd.testing.assert_frame_equal(baseline[original.columns], original.loc[~original.municipality_bfs_id.eq(700)].reset_index(drop=True))
    summary = json.loads((ROOT / "reports/accessibility_territorial_harmonisation_summary.json").read_text(encoding="utf-8"))
    temporal = summary["temporal_support"]
    assert temporal["treated_municipalities"] == temporal["treated_current_territories"] == 79
    assert temporal["treated_municipalities_with_observed_pre_and_post_support"] == 76
    assert {r["municipality_bfs_id"] for r in temporal["treated_municipalities_without_observed_pre_support"]} == {5892, 6037, 6513}
    assert temporal["constant_step_sensitivity_support"]["treated_observation_rows"] == 5580
    assert [r["treated_municipalities_complete"] for r in temporal["common_support_sensitivities"]] == [76, 73, 65]
    assert summary["additional_entry_months"] == 96 and summary["territories_with_additional_entries"] == 45
    assert summary["distinct_territorial_entry_months"] == 175
    assert summary["station_groups_retained"] == 71
    assert summary["observed_design"]["two_way_fixed_effect_rank"] == 41
    assert len(summary["observed_design"]["exact_identical_observed_exposure_pairs"]) == 4
    assert not summary["analysis_sample_selected"] and not summary["estimator_selected"]
    assert not summary["causal_estimation_approved"] and not summary["imputation_applied"]


def test_every_territorial_variable_and_source_is_registered() -> None:
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    assert {"DERIVED_ACCESSIBILITY_TERRITORIAL_MOUTIER_BRIDGE", "BFS_MUNICIPAL_MUTATION_3999"}.issubset(set(sources.source_id))
    for key in ["analytical_panel", "comparison_universe", "selected_foreign_share"]:
        path = ROOT / config()[key]
        columns = set(pd.read_csv(path, nrows=0).columns)
        definitions = dictionary.loc[dictionary.table.eq(path.stem)]
        assert columns == set(definitions.variable)
        assert definitions.source_id.eq("DERIVED_ACCESSIBILITY_TERRITORIAL_MOUTIER_BRIDGE").all()
