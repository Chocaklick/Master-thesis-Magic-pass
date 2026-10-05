from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.descriptive.plot_accessibility_commune_trends import fit_line, prepare_unit

ROOT = Path(__file__).resolve().parents[1]


def load_outputs():
    config = json.loads((ROOT / "config/accessibility_commune_trend_plots.json").read_text(encoding="utf-8"))
    payload = json.loads((ROOT / config["output_points"]).read_text(encoding="utf-8"))
    return config, payload, pd.DataFrame(payload["observations"]), pd.DataFrame(payload["communes"])


def test_frozen_random_draw_only_illustrates_15_of_76_without_analytic_selection():
    config, _, _, communes = load_outputs()
    support = pd.read_csv(ROOT / config["support_file"])
    candidates = support.loc[support.calculable, "municipality_bfs_id"].sort_values().to_numpy(int)
    draw = np.random.default_rng(config["selection_seed"]).choice(candidates, 15, replace=False).tolist()
    assert draw == config["selected_bfs_ids_in_draw_order"]
    assert len(candidates) == 76 and communes.municipality_bfs_id.nunique() == 15
    assert set(draw) == set(communes.municipality_bfs_id)
    assert communes.illustration_only.all()
    assert not communes.causal_estimation_approved.any()
    assert not config["analysis_sample_changed"]
    assert support.municipality_bfs_id.nunique() == 79


def test_plotted_observations_are_exact_original_source_not_interpolation():
    config, _, points, _ = load_outputs()
    panel = pd.read_csv(ROOT / config["panel_file"], low_memory=False).set_index(["municipality_bfs_id", "date"])
    for row in points.itertuples():
        original = panel.loc[(row.municipality_bfs_id, row.date)]
        assert row.source_outcome_observed == pd.notna(original.hotel_overnights)
        if row.source_outcome_observed:
            assert row.hotel_overnights == original.hotel_overnights
            assert np.isclose(row.observed_log_overnights, original.log_overnights, atol=1e-14)
        else:
            assert pd.isna(row.hotel_overnights) and pd.isna(row.observed_log_overnights)
            assert pd.isna(row.seasonally_adjusted_log_overnights)
    assert points.source_outcome_observed.sum() == 1358


def test_seasonal_profile_is_exact_pre_only_calibration_for_both_segments():
    config, _, points, communes = load_outputs()
    fits = pd.read_csv(ROOT / config["calibration_file"]).set_index(["focal_cohort_month", "municipality_bfs_id"])
    for unit in communes.itertuples():
        local = points.loc[points.municipality_bfs_id.eq(unit.municipality_bfs_id)]
        fit = fits.loc[(unit.focal_cohort_month, unit.municipality_bfs_id)]
        season = np.array([fit[f"seasonal_offset_month_{m:02d}"] for m in range(1, 13)])
        season -= season.mean()
        months = pd.to_datetime(local.date).dt.month.to_numpy()-1
        assert np.allclose(local.centered_pre_seasonal_offset, season[months])
        assert np.allclose(local.seasonally_adjusted_log_overnights,
                           local.observed_log_overnights-local.centered_pre_seasonal_offset, equal_nan=True)
        assert np.isclose(unit.pre_trend_slope_log1p_per_month, fit.pre_slope_log_points_per_month)


def test_pre_post_trends_back_transform_fits_with_correct_calendar_segments():
    _, _, points, communes = load_outputs()
    for unit in communes.itertuples():
        local = points.loc[points.municipality_bfs_id.eq(unit.municipality_bfs_id)]
        for label, mask in [("pre", local.event_month.lt(0)), ("post", local.event_month.ge(0))]:
            segment = local.loc[mask]
            assert np.isclose(getattr(unit, f"{label}_observed_months"), segment.source_outcome_observed.sum())
            valid = segment.source_outcome_observed
            x = np.column_stack([np.ones(valid.sum()), segment.loc[valid, "event_month"]])
            intercept, slope = np.linalg.lstsq(x, segment.loc[valid, "seasonally_adjusted_log_overnights"], rcond=None)[0]
            assert np.isclose(getattr(unit, f"{label}_trend_intercept_log1p"), intercept)
            assert np.isclose(getattr(unit, f"{label}_trend_slope_log1p_per_month"), slope)
            assert np.allclose(segment[f"{label}_trend_nights"], np.expm1(intercept+slope*segment.event_month))
            assert local.loc[~mask, f"{label}_trend_nights"].isna().all()
        assert local.event_month.min() == -36
        assert local.event_month.lt(0).sum() == 36
        assert local.date.min() == unit.plot_start_month and local.date.max() == unit.plot_end_month
    assert set(communes.loc[communes.post_observed_months.lt(12), "municipality_bfs_id"]) == {784, 1407}


def test_synthetic_fit_uses_actual_calendar_gaps_and_never_future_input():
    dates = pd.date_range("2017-01-01", "2020-11-01", freq="MS")
    anchor = pd.Timestamp("2020-01-01")
    k = np.arange(len(dates))-36
    season = np.arange(12)*.08
    y = np.where(k < 0, 5+.02*k, 5.4+.005*k)+season[np.asarray(dates.month)-1]-season.mean()
    local = pd.DataFrame({"date": dates, "log_overnights": y, "hotel_overnights": np.expm1(y)})
    local.loc[5, ["hotel_overnights", "log_overnights"]] = np.nan
    calibration = pd.Series({f"seasonal_offset_month_{m:02d}": season[m-1] for m in range(1, 13)})
    points, metadata = prepare_unit(local, anchor, calibration, 36)
    assert np.isclose(metadata["pre_trend_slope_log1p_per_month"], .02)
    assert np.isclose(metadata["post_trend_slope_log1p_per_month"], .005)
    assert metadata["pre_observed_months"] == 35 and metadata["post_observed_months"] == 11
    changed = local.copy()
    changed.loc[changed.date.ge(anchor), "log_overnights"] += 2
    changed.loc[changed.date.ge(anchor), "hotel_overnights"] = np.expm1(changed.loc[changed.date.ge(anchor), "log_overnights"])
    after, _ = prepare_unit(changed, anchor, calibration, 36)
    assert np.allclose(points.pre_trend_nights, after.pre_trend_nights, equal_nan=True)
    assert np.allclose(points.centered_pre_seasonal_offset, after.centered_pre_seasonal_offset)
    zero_fit = fit_line(np.array([0., 0., 0., np.nan]), np.array([0, 1, 3, 4]))
    assert zero_fit["n"] == 3 and zero_fit["slope"] == 0


def test_plot_input_output_hashes_and_three_readable_png_pages():
    config, _, _, communes = load_outputs()
    summary = json.loads((ROOT / config["output_summary"]).read_text(encoding="utf-8"))
    assert summary["illustrated_territories"] == 15 and summary["plot_pages"] == 3
    assert not summary["analysis_sample_changed"] and not summary["causal_estimation_approved"]
    assert communes.groupby("plot_page").size().to_dict() == {1: 5, 2: 5, 3: 5}
    for relative, checksum in {**summary["input_sha256"], **summary["output_sha256"]}.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == checksum
    for number in range(1, 4):
        image = (ROOT / f"figures/accessibility_15_communes_trends_{number}.png").read_bytes()
        assert image.startswith(b"\x89PNG\r\n\x1a\n")
        assert (int.from_bytes(image[16:20], "big"), int.from_bytes(image[20:24], "big")) == (1840, 2560)


def test_plot_source_and_all_json_projection_variables_registered():
    _, payload, _, _ = load_outputs()
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    assert "DERIVED_ACCESSIBILITY_COMMUNE_TREND_PLOTS" in set(sources.source_id)
    for table, records in [("accessibility_commune_trend_plot_points", payload["observations"]),
                           ("accessibility_commune_trend_plot_communes", payload["communes"])]:
        registered = dictionary[dictionary.table.eq(table)]
        assert set(records[0]) == set(registered.variable)
        assert registered.description.notna().all()
    unit = dictionary.loc[dictionary.table.eq("accessibility_commune_trend_plot_points") & dictionary.variable.eq("pre_trend_nights"), "unit"].iloc[0]
    assert unit == "overnight stays (observed or descriptive fitted level)"
