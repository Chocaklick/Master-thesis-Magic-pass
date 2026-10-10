"""Independent numeric checks, assumption provenance and no silent exclusions."""
import io
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.descriptive.diagnose_native_snow_metrics_stage75 import paired_metrics, OUTPUT, SUMMARY, DAILY, COVERAGE, DEFS
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.data_processing.prepare_native_snow_weights_stage69 import digest

ROOT = Path(__file__).resolve().parents[1]


def test_pairwise_missingness_sign_scale_and_true_zeros():
    r = paired_metrics([0., 1., np.nan, 9., np.inf], [0., 3., 4., np.inf, 2.])
    assert r['finite_paired_days'] == 2
    assert r['spass_paired_mean_m'] == .5
    assert r['oshd_paired_mean_m'] == 1.5
    assert r['mean_oshd_minus_spass_m'] == r['median_oshd_minus_spass_m'] == 1.
    assert r['mean_absolute_difference_m'] == 1.
    assert r['root_mean_square_difference_m'] == pytest.approx(np.sqrt(2))
    assert paired_metrics([np.nan], [0.]) == {'finite_paired_days': 0}
    assert paired_metrics([0.], [0.])['mean_absolute_difference_m'] == 0.
    assert paired_metrics([3.], [1.])['mean_oshd_minus_spass_m'] == -2.
    for a, b in [([[1]], [[2]]), ([1, 2], [3])]:
        with pytest.raises(ValueError):
            paired_metrics(a, b)


def test_every_computed_row_independently_recomputed_from_frozen_daily_means():
    daily = pd.read_csv(ROOT/DAILY, float_precision='round_trip')
    output = pd.read_csv(ROOT/OUTPUT, float_precision='round_trip')
    calculated = output[output.mean_oshd_minus_spass_m.notna()]
    assert len(calculated) == 120
    for r in calculated.itertuples():
        f = daily[daily.station_group_id.eq(r.station_group_id) & daily.oshd_date_offset_days.eq(r.oshd_date_offset_days)]
        a, b = f.spass_mean_common_raw.to_numpy(), f.oshd_mean_common_m.to_numpy()
        mask = np.isfinite(a) & np.isfinite(b)
        a, b = a[mask], b[mask]
        d = b-a
        assert len(d) == r.finite_paired_days == 151
        expected = [np.mean(a), np.mean(b), np.mean(d), np.median(d), np.mean(np.abs(d)), np.sqrt(np.mean(d**2))]
        actual = [r.spass_paired_mean_m, r.oshd_paired_mean_m, r.mean_oshd_minus_spass_m,
                  r.median_oshd_minus_spass_m, r.mean_absolute_difference_m, r.root_mean_square_difference_m]
        np.testing.assert_allclose(actual, expected, rtol=1e-13, atol=1e-14)
        assert abs(r.mean_oshd_minus_spass_m) <= r.mean_absolute_difference_m + 1e-14
        assert r.mean_absolute_difference_m <= r.root_mean_square_difference_m + 1e-14


def test_entire_universe_coverage_and_unchanged_rank_references():
    out = pd.read_csv(ROOT/OUTPUT).set_index(['station_group_id', 'oshd_date_offset_days'])
    cov = pd.read_csv(ROOT/COVERAGE).set_index(out.index.names)
    assert len(out) == 210 and out.index.equals(cov.index) and out.index.is_unique
    assert out.group_retained.all() and out.spass_unit_assumption_approved.all()
    assert out.spass_analytical_unit.eq('m').all() and out.spass_original_source_unit.eq('UNKNOWN').all()
    assert out.spass_raw_to_m_factor.eq(1).all()
    assert not out.source_spliced_or_calibrated.any() and not out.p_value_or_ci_computed.any()
    for lag in [-1, 0, 1]:
        f = out.xs(lag, level='oshd_date_offset_days')
        assert len(f) == 70 and f.mean_oshd_minus_spass_m.isna().sum() == 30
        missing = f[f.mean_oshd_minus_spass_m.isna()]
        assert missing.available_daily_rows.eq(0).all()
        assert missing.finite_paired_days.isna().all() and missing.diagnostic_status.str.startswith('no_usable_geometry__').all()
    for field in ['min_common_observed_length_share', 'mean_common_observed_length_share', 'unique_mapped_axis_length_m']:
        np.testing.assert_allclose(out[field], cov[field], equal_nan=True)
    for path, original, current in [('native_snow_rank_diagnostic_stage71.csv', 'spearman_rho', 'spearman_daily_levels_stage71'),
                                    ('native_snow_change_rank_diagnostic_stage72.csv', 'spearman_change_rho', 'spearman_daily_changes_stage72')]:
        old = pd.read_csv(ROOT/'data_processed'/path).set_index(out.index.names)
        np.testing.assert_allclose(out[current], old.loc[out.index, original], equal_nan=True)


def test_frozen_inputs_registry_prefixes_and_untouched_collection():
    summary = json.loads((ROOT/SUMMARY).read_text(encoding='utf8'))
    for path, sha in {**summary['input_sha256'], **summary['output_sha256']}.items():
        assert digest(path) == sha
    for path, added in [('metadata/data_sources_master.csv', 1), ('metadata/data_dictionary.csv', len(DEFS))]:
        current = pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)
        old = pd.read_csv(io.BytesIO(subprocess.check_output(['git', 'show', 'a6dc92a:'+path], cwd=ROOT)), dtype=str, keep_default_na=False)
        assert len(current) >= len(old)+added and old.equals(current.iloc[:len(old)].reset_index(drop=True))
        assert row_digest(old) == summary['prior_registry_rows_and_digest'][path]['sha256']
    path = 'logs/data_collection_log.csv'
    # Git stores LF while this Windows checkout has CRLF; compare exact cells.
    old = pd.read_csv(io.BytesIO(subprocess.check_output(['git', 'show', 'a6dc92a:'+path], cwd=ROOT)), dtype=str, keep_default_na=False)
    current = pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)
    assert len(current) >= 1585 and old.equals(current.iloc[:len(old)].reset_index(drop=True))
