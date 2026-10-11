"""Own-window chronology, missing-versus-zero and independent numerical QA."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data_processing.build_spass_preentry_profiles_stage77 import (
    ROOT, OUTPUTS, WINDOWS, SUMMARY, collapse_weights, daily_metric, winter_metric, five_metric)


def winters(values, day_counts=None):
    years = range(2012, 2017)
    return pd.DataFrame(dict(winter_start_year=list(years), spass_winter_mean_m=values,
        winter_start_date=[f'{y}-12-01' for y in years], winter_end_date=[f'{y+1}-04-30' for y in years],
        first_base_entry_month=['2017-05-01']*5, spass_calendar_within_archive=[True]*5,
        observed_days=day_counts or [151]*5))


def test_zero_and_negative_not_missing_and_no_oshd_mask():
    r = daily_metric([0, 2, np.nan], [1, 3, 6])
    assert r['spass_daily_mean_m'] == 1.5
    assert r['observed_length_share'] == .4
    assert not r['all_axis_length_observed']
    assert daily_metric([-2, 0], [1, 1])['spass_daily_mean_m'] == -1
    assert daily_metric([-2, 0], [1, 1])['negative_length_m'] == 1
    assert daily_metric([np.nan, np.inf], [1, 1])['spass_daily_mean_m'] is None
    assert daily_metric([0, 0], [1, 1])['spass_daily_mean_m'] == 0
    with pytest.raises(ValueError):
        daily_metric([1, 2], [0, 1])


def test_partial_daily_means_not_imputed_and_duplicates_rejected():
    f = pd.DataFrame(dict(civil_date=['2016-02-28', '2016-02-29', '2016-03-01'],
        spass_daily_mean_m=[0., np.nan, 2.], observed_length_share=[1., 0., .5],
        all_axis_length_observed=[True, False, False], negative_length_m=[0., 0., 0.]))
    r = winter_metric(f, 3)
    assert r['spass_winter_mean_m'] == 1
    assert r['observed_days'] == 2 and r['missing_days'] == 1
    assert r['mean_observed_length_share'] == .5
    assert not r['all_requested_days_observed']
    with pytest.raises(ValueError):
        winter_metric(pd.concat([f.iloc[:1], f.iloc[:1], f.iloc[2:]]), 3)


def test_exactly_five_equal_weight_winters_and_no_partial_fallback():
    f = winters([0., 1., 2., 3., 9.], [151, 151, 151, 152, 151])
    assert five_metric(f)['spass_five_preentry_winters_mean_m'] == 3
    f.loc[4, 'spass_winter_mean_m'] = np.nan
    r = five_metric(f)
    assert r['spass_five_preentry_winters_mean_m'] is None
    assert r['observed_winter_count'] == 4
    assert r['missing_winter_start_years'] == '2016'
    with pytest.raises(ValueError):
        five_metric(f.iloc[:4])
    f.loc[4, 'winter_end_date'] = '2017-05-01'
    with pytest.raises(ValueError):
        five_metric(f)


def test_native_subdivision_collapse_keeps_length_and_not_polygons():
    f = pd.DataFrame(dict(station_group_id=['x']*3, spass_e_index=[0, 0, 1],
        spass_n_index=[1, 1, 1], spass_cell_in_grid=[True]*3,
        unique_axis_length_m=[1., 2., 3.]))
    c = collapse_weights(f)
    assert c.unique_axis_length_m.tolist() == [3., 3.]
    assert daily_metric([1., 3.], c.unique_axis_length_m)['spass_daily_mean_m'] == 2
    f.loc[0, 'spass_cell_in_grid'] = False
    with pytest.raises(ValueError):
        collapse_weights(f)


def test_real_outputs_retain_all_own_windows_and_no_snow_splice():
    requested = pd.read_csv(ROOT/WINDOWS)
    winter = pd.read_csv(ROOT/OUTPUTS['spass_preentry_winter_stage77'], float_precision='round_trip')
    profile = pd.read_csv(ROOT/OUTPUTS['spass_preentry_profiles_stage77'], float_precision='round_trip')
    assert len(winter) == 350 and len(profile) == 70
    assert profile.station_group_id.is_unique and profile.group_retained.all()
    assert set(profile.station_group_id) == set(requested.station_group_id)
    cols = ['station_group_id', 'first_base_entry_month', 'winter_start_year', 'winter_start_date',
            'winter_end_date', 'expected_days', 'spass_calendar_within_archive']
    pd.testing.assert_frame_equal(requested[cols].reset_index(drop=True), winter[cols].reset_index(drop=True))
    assert not winter.source_spliced_or_calibrated.any()
    assert winter.spass_original_unit.eq('UNKNOWN').all() and winter.spass_metres_assumed.all()
    assert profile.spass_five_preentry_winters_mean_m.notna().sum() == 34
    missing = profile[profile.observed_winter_count.lt(5)]
    assert missing.spass_five_preentry_winters_mean_m.isna().all()
    for g in profile.itertuples():
        w = winter[winter.station_group_id.eq(g.station_group_id)]
        a = w.spass_winter_mean_m.to_numpy()
        if np.isfinite(a).all():
            np.testing.assert_allclose(g.spass_five_preentry_winters_mean_m, np.mean(a), rtol=1e-14, atol=1e-14)
        else:
            assert np.isnan(g.spass_five_preentry_winters_mean_m)


def test_independent_daily_to_winter_and_registry_definitions():
    summary = json.loads((ROOT/SUMMARY).read_text(encoding='utf8'))
    winter = pd.read_csv(ROOT/OUTPUTS['spass_preentry_winter_stage77'], float_precision='round_trip')
    checks = 0
    for year, checkpoint in summary['daily_checkpoints'].items():
        f = pd.read_csv(ROOT/checkpoint['path'], float_precision='round_trip')
        assert not f.duplicated(['station_group_id', 'civil_date']).any()
        for gid, rows in f.groupby('station_group_id'):
            target = winter[winter.station_group_id.eq(gid) & winter.winter_start_year.eq(int(year))].iloc[0]
            means = rows.spass_daily_mean_m.to_numpy()
            finite = means[np.isfinite(means)]
            assert len(rows) == target.expected_days
            assert len(finite) == target.observed_days
            np.testing.assert_allclose(target.spass_winter_mean_m, np.mean(finite), rtol=1e-14, atol=1e-14)
            checks += 1
    assert checks == 188
    dictionary = pd.read_csv(ROOT/'metadata/data_dictionary.csv')
    sources = pd.read_csv(ROOT/'metadata/data_sources_master.csv')
    for table, path in OUTPUTS.items():
        f = pd.read_csv(ROOT/path)
        d = dictionary[dictionary.table.eq(table)]
        assert not d.variable.duplicated().any()
        assert set(f) == set(d.variable)
        assert set(d.source_id) <= set(sources.source_id)
        for r in d.itertuples():
            # An empty list means no missing winter, not an unknown list.
            expected = 0. if r.variable == 'missing_winter_start_years' else f[r.variable].isna().mean()
            assert abs(float(r.missing_share) - expected) <= .00000051


def test_all_real_daily_means_against_original_split_native_lengths():
    weights = pd.read_csv(ROOT/'data_processed/native_snow_cell_pairs_stage69.csv', float_precision='round_trip')
    indices = weights[['spass_e_index', 'spass_n_index']].drop_duplicates().sort_values(['spass_e_index', 'spass_n_index'])
    lookup = {tuple(v): i for i, v in enumerate(indices.to_numpy())}
    summary = json.loads((ROOT/SUMMARY).read_text(encoding='utf8'))
    checked = 0
    for checkpoint in summary['daily_checkpoints'].values():
        values = {}
        for c in checkpoint['source_checkpoints']:
            with np.load(ROOT/c['npz'], allow_pickle=False) as cache:
                a = cache['values']
            if c['kind'] == 'reuse_original_spass_pilot_cells':
                dates = pd.read_csv(ROOT/c['calendar'])
                days = dates[dates.oshd_date_offset_days.eq(0)].sort_values('spass_time_index').spass_civil_date.tolist()
            else:
                meta = json.loads((ROOT/c['metadata']).read_text(encoding='utf8'))
                days = meta['observed_dates']
            assert len(days) == len(a)
            values.update(zip(days, a))
        daily = pd.read_csv(ROOT/checkpoint['path'], float_precision='round_trip')
        for gid, rows in daily.groupby('station_group_id'):
            w = weights[weights.station_group_id.eq(gid)]
            loc = [lookup[t] for t in w[['spass_e_index', 'spass_n_index']].itertuples(index=False, name=None)]
            lengths = w.unique_axis_length_m.to_numpy()
            for row in rows.itertuples():
                a = values[row.civil_date][loc]
                finite = np.isfinite(a)
                expected = np.dot(a[finite], lengths[finite])/np.sum(lengths[finite]) if finite.any() else np.nan
                np.testing.assert_allclose(row.spass_daily_mean_m, expected, rtol=1e-12, atol=1e-14, equal_nan=True)
                np.testing.assert_allclose(row.observed_length_share, np.sum(lengths[finite])/np.sum(lengths), rtol=1e-12, atol=1e-14)
                checked += 1
    assert checked == sum(len(pd.read_csv(ROOT/c['path'])) for c in summary['daily_checkpoints'].values())
