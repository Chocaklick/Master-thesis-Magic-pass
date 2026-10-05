from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.causal_inference.estimate_accessibility_cohort_time import (
    aggregate, calculate, contrast, intervals, month_number, seasonal_fit,
)

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "accessibility_cohort_time_estimation"


def synthetic_inputs(extra_treated_slope=0.):
    dates = pd.date_range("2016-01-01", "2021-04-01", freq="MS")
    anchor = pd.Timestamp("2019-05-01")
    ids = [11, 12, 13, 14, 15, 16]
    records, roles = [], []
    for i, bfs in enumerate(ids):
        treated = i < 3
        y = (4+i*.2 + (i+1)*.15*np.cos(dates.month*np.pi/6) +
             (.01+(extra_treated_slope if treated else 0))*np.arange(len(dates)) +
             (.4 if treated else 0)*np.asarray(dates >= anchor) +
             (2. if bfs == 15 else 0)*np.asarray(dates >= pd.Timestamp("2020-05-01")))
        for date, value in zip(dates, y):
            records.append({"municipality_bfs_id": bfs, "date": date,
                            "hotel_overnights": np.expm1(value), "log_overnights": value})
        roles.append({"focal_cohort_month": "2019-05-01", "municipality_bfs_id": bfs,
                      "municipality_name": f"synthetic_{bfs}", "treated_in_focal_cohort": treated,
                      "primary_donor_candidate_at_anchor": not treated,
                      "sensitivity_never_exposed_donor_candidate": not treated and bfs != 15,
                      "primary_donor_use_end_exclusive": "2020-05-01" if bfs == 15 else ""})
    return pd.DataFrame(records), pd.DataFrame(roles)


def run_synthetic(panel=None, extra_slope=0.):
    original, universe = synthetic_inputs(extra_slope)
    config = {"bootstrap_seed": 10, "bootstrap_repetitions": 199}
    return calculate(original if panel is None else panel, universe, config,
                     {"pre_diagnostic_and_seasonality_window_months": 36})


def test_pre_calendar_fit_keeps_gaps_and_separates_season_from_slope():
    dates = pd.date_range("2016-05-01", periods=36, freq="MS")
    y = .03*month_number(dates)+np.asarray(dates.month)*.1
    y[[3, 9, 18]] = np.nan
    fit = seasonal_fit(y, dates)
    assert fit["n"] == 33 and fit["rank"] == 13
    assert abs(fit["slope"]-.03) < 1e-10
    assert np.allclose(fit["season"], np.arange(12)*.1)
    deficient = seasonal_fit(y[:12], dates[:12])
    assert not np.isfinite(deficient["slope"])


def test_synthetic_jump_recovered_and_future_donor_exits_before_own_entry():
    cohort, _, _, _ = run_synthetic()
    post = cohort[cohort.variant.eq("primary") & cohort.event_month.ge(0)]
    assert np.allclose(post.estimate_log_points, .4)
    before = post[post.event_month.eq(11)].iloc[0]
    at = post[post.event_month.eq(12)].iloc[0]
    assert before.donor_observed_count == 3 and at.donor_observed_count == 2
    assert "15" in before.donor_bfs_ids.split("|")
    assert "15" not in at.donor_bfs_ids.split("|")
    never = cohort[cohort.variant.eq("never_exposed_donors") & cohort.event_month.ge(0)]
    assert (never.donor_observed_count == 2).all()
    assert np.allclose(never.estimate_log_points, .4)


def test_primary_does_not_subtract_pretrend_linear_variant_does():
    cohort, _, _, _ = run_synthetic(extra_slope=.002)
    primary = cohort[cohort.variant.eq("primary") & cohort.event_month.ge(0)]
    linear = cohort[cohort.variant.eq("linear_pretrend_sensitivity") & cohort.event_month.ge(0)]
    assert np.allclose(primary.estimate_log_points, .4+.002*(primary.event_month+1))
    assert np.allclose(linear.estimate_log_points, .4)


def test_post_values_cannot_change_seasonal_calibration():
    original, _ = synthetic_inputs()
    _, _, calibration, _ = run_synthetic(original)
    changed = original.copy()
    mask = changed.date.ge(pd.Timestamp("2019-05-01")) & changed.municipality_bfs_id.eq(11)
    changed.loc[mask, "log_overnights"] += 5
    changed.loc[mask, "hotel_overnights"] = np.expm1(changed.loc[mask, "log_overnights"])
    _, _, after, _ = run_synthetic(changed)
    pd.testing.assert_frame_equal(calibration, after)


def test_missing_endpoint_not_imputed_but_zero_is_valid():
    original, _ = synthetic_inputs()
    missing = original.date.eq(pd.Timestamp("2019-04-01")) & original.municipality_bfs_id.eq(11)
    original.loc[missing, ["hotel_overnights", "log_overnights"]] = np.nan
    zero = original.date.eq(pd.Timestamp("2019-05-01")) & original.municipality_bfs_id.eq(12)
    original.loc[zero, ["hotel_overnights", "log_overnights"]] = 0.
    cohort, _, _, support = run_synthetic(original)
    assert not support.loc[support.municipality_bfs_id.eq(11), "calculable"].iloc[0]
    at = cohort[cohort.variant.eq("primary") & cohort.event_month.eq(0)].iloc[0]
    assert at.treated_observed_count == 2
    assert "12" in at.treated_bfs_ids.split("|")
    assert np.isfinite(at.estimate_log_points)


def test_shared_cluster_multiplier_preserves_repeated_cell_dependence():
    delta = np.array([1., 3., .5, 1.5])
    effect, influence, _, _ = contrast(delta, np.array([1, 1, 0, 0], bool), np.array([0, 0, 1, 1], bool))
    assert effect == 1.
    assert np.isclose(influence.sum(), 0)
    frame = pd.DataFrame({"variant": ["a", "a"], "event_month": [0, 1], "estimate_log_points": [effect, effect]})
    draws = np.random.default_rng(5).normal(size=(999, 4))
    out = intervals(frame, np.array([influence, influence]), draws, True)
    assert out.loc[0, "pointwise_lower_95"] == out.loc[1, "pointwise_lower_95"]
    assert out.loc[0, "simultaneous_lower_95"] == out.loc[1, "simultaneous_lower_95"]
    assert out.loc[0, "simultaneous_lower_95"] <= out.loc[0, "estimate_log_points"]


def test_dynamic_influence_includes_cohort_share_uncertainty():
    cells = []
    for mask, delta in [(np.array([1, 1, 0, 0, 0, 0], bool), np.array([1., 2., 0, 0, .5, 1.])),
                        (np.array([0, 0, 1, 1, 0, 0], bool), np.array([0, 0, 3., 5., .5, 1.]))]:
        donor = np.array([0, 0, 0, 0, 1, 1], bool)
        point, infl, tm, _ = contrast(delta, mask, donor)
        cells.append({"estimate": point, "influence": infl, "treated_mask": tm, "delta": delta, "donor": donor})
    point, infl, n = aggregate(cells, 6)
    assert n == 4 and np.isclose(infl.sum(), 0)
    for i in range(6):
        weights = np.ones(6)
        weights[i] += 1e-6
        numerator, denominator = 0., 0.
        for cell in cells:
            tm, dm = cell["treated_mask"], cell["donor"]
            count = weights[tm].sum()
            estimate = np.average(cell["delta"][tm], weights=weights[tm])-np.average(cell["delta"][dm], weights=weights[dm])
            numerator += count*estimate
            denominator += count
        assert np.isclose((numerator/denominator-point)/1e-6, infl[i], atol=2e-7)


def test_approved_execution_preserves_inventory_and_historical_proposal():
    current = json.loads((ROOT / "config/accessibility_cohort_time_execution.json").read_text(encoding="utf-8"))
    old = json.loads((ROOT / current["approved_proposal_config"]).read_text(encoding="utf-8"))
    summary = json.loads((ROOT / f"reports/{PREFIX}_summary.json").read_text(encoding="utf-8"))
    assert current["parameter_bundle_approved"] and current["estimator_selected"]
    assert not old["parameter_bundle_approved"]  # intentionally immutable pre-approval snapshot
    assert summary["estimation_executed"] and not summary["causal_estimation_approved"]
    assert summary["calculable_exposed_territories"] == 76
    assert summary["exposed_territories_retained_in_inventory"] == 79
    assert summary["primary_observed_post_pairs"] == 5451
    assert summary["inventory_observed_post_months"] == 5580
    assert sum(row["inventory_observed_post_months"] for row in summary["missing_histories"]) == 129
    assert summary["common_horizon_territories"] == {"6": 76, "12": 73, "24": 65}
    for relative, checksum in {**summary["input_sha256"], **summary["output_sha256"]}.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == checksum


def test_exported_endpoint_contrasts_reconcile_independently_to_source():
    panel = pd.read_csv(ROOT / "data_processed/accessibility_municipality_month_exposure_territorial.csv", low_memory=False).set_index(["municipality_bfs_id", "date"])
    fits = pd.read_csv(ROOT / f"reports/{PREFIX}_calibration.csv").set_index(["municipality_bfs_id", "focal_cohort_month"])
    cohort = pd.read_csv(ROOT / f"reports/{PREFIX}_cohort_month.csv")
    for row in cohort[cohort.variant.eq("primary") & cohort.event_month.isin([0, 5, 23, 59])].itertuples():
        anchor = pd.Timestamp(row.focal_cohort_month)
        reference = anchor-pd.DateOffset(months=1)
        date = pd.Timestamp(row.calendar_month)
        means = []
        for ids in [row.treated_bfs_ids, row.donor_bfs_ids]:
            changes = []
            for bfs in str(ids).split("|"):
                fit = fits.loc[(int(bfs), row.focal_cohort_month)]
                zt = panel.loc[(int(bfs), row.calendar_month), "log_overnights"]-fit[f"seasonal_offset_month_{date.month:02d}"]
                zr = panel.loc[(int(bfs), reference.strftime("%Y-%m-%d")), "log_overnights"]-fit[f"seasonal_offset_month_{reference.month:02d}"]
                changes.append(zt-zr)
            means.append(np.mean(changes))
        assert np.isclose(row.estimate_log_points, means[0]-means[1], atol=1e-12)


def test_exported_roles_never_use_treated_donors_and_dynamic_equal_weight():
    universe = pd.read_csv(ROOT / "reports/accessibility_cohort_comparison_universe_territorial.csv")
    exit_dates = universe.set_index(["focal_cohort_month", "municipality_bfs_id"]).primary_donor_use_end_exclusive.to_dict()
    cohort = pd.read_csv(ROOT / f"reports/{PREFIX}_cohort_month.csv")
    dynamic = pd.read_csv(ROOT / f"reports/{PREFIX}_dynamic.csv")
    for row in cohort[cohort.variant.eq("primary")].itertuples():
        treated = set(str(row.treated_bfs_ids).split("|"))
        donors = set(str(row.donor_bfs_ids).split("|"))
        assert not treated & donors
        for bfs in donors:
            exit_date = exit_dates[(row.focal_cohort_month, int(bfs))]
            assert pd.isna(exit_date) or row.calendar_month < exit_date
        if row.event_month == -1:
            assert row.estimate_log_points == row.cluster_standard_error == 0
    for row in dynamic[dynamic.variant.eq("primary")].itertuples():
        cells = cohort[cohort.variant.eq("primary") & cohort.event_month.eq(row.event_month)]
        assert row.treated_observed_count == cells.treated_observed_count.sum()
        assert np.isclose(row.estimate_log_points, np.average(cells.estimate_log_points, weights=cells.treated_observed_count))
    assert 700 not in set(int(bfs) for ids in cohort.treated_bfs_ids.dropna() for bfs in str(ids).split("|"))


def test_common_horizons_and_covid_variant_have_explicit_support():
    cohort = pd.read_csv(ROOT / f"reports/{PREFIX}_cohort_month.csv")
    dynamic = pd.read_csv(ROOT / f"reports/{PREFIX}_dynamic.csv")
    covid = cohort[cohort.variant.eq("covid_contrast_months_omitted")]
    assert not covid.calendar_month.between("2020-03-01", "2022-03-01").any()
    same = dynamic[dynamic.variant.str.startswith("same_territories_")]
    assert same.treated_observed_count.eq(65).all()
    assert same.treated_bfs_ids.nunique() == 1
    for h in [6, 12, 24]:
        rows = dynamic[dynamic.variant.eq(f"same_territories_common_{h}_months")]
        assert rows.event_month.min() == -h and rows.event_month.max() == h-1
        assert not rows.causal_estimation_approved.any()


def test_estimation_sources_and_every_output_variable_registered():
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    assert {"DERIVED_ACCESSIBILITY_COHORT_TIME_ESTIMATION", "DID_ATT_GT_OFFICIAL_DOCUMENTATION", "DID_BASICS_OFFICIAL_DOCUMENTATION"} <= set(sources.source_id)
    for label in ["cohort_month", "dynamic", "calibration", "territory_support"]:
        frame = pd.read_csv(ROOT / f"reports/{PREFIX}_{label}.csv")
        registered = dictionary[dictionary.table.eq(f"{PREFIX}_{label}")]
        assert set(frame.columns) == set(registered.variable)
        assert registered.description.notna().all()
        if "estimate_log_points" in frame:
            assert registered.loc[registered.variable.eq("estimate_log_points"), "unit"].iloc[0] == "log(1+overnight stays) points"
