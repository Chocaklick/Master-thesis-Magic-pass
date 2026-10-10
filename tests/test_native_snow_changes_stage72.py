"""Consecutive changes complement levels, without bridging gaps or changing support."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.descriptive.diagnose_native_snow_changes_stage72 import consecutive_changes, support_stability, audit_support, DEFS
from src.descriptive.diagnose_native_snow_ranks_stage71 import rank_correlation
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.data_processing.prepare_native_snow_weights_stage69 import digest

ROOT = Path(__file__).resolve().parents[1]


def direct_ranks(a):
    return np.array([1+np.sum(a<v)+(np.sum(a==v)-1)/2 for v in a])


def test_actual_consecutive_dates_not_sorted_row_gaps_or_missing_endpoints():
    f = pd.DataFrame(dict(spass_civil_date=['2023-01-05','2023-01-01','2023-01-02','2023-01-04','2023-01-06'],
                          spass_mean_common_raw=[9.,1.,3.,5.,np.nan],oshd_mean_common_m=[30.,10.,14.,20.,40.]))
    a,b,n = consecutive_changes(f)
    assert n==3
    assert np.array_equal(a,[2.,np.nan,4.,np.nan],equal_nan=True)
    assert np.array_equal(b,[4.,np.nan,10.,np.nan],equal_nan=True)
    assert rank_correlation(a,b)['finite_paired_days']==2
    with pytest.raises(ValueError,match='Duplicate daily'):
        consecutive_changes(pd.concat([f,f.iloc[:1]]))
    empty = f.iloc[:0]
    a,b,n = consecutive_changes(empty)
    assert len(a)==len(b)==n==0


def test_calendar_uses_explicit_days_without_deprecation_warning():
    import warnings
    f = pd.DataFrame(dict(spass_civil_date=['2023-01-01','2023-01-02'],
                          spass_mean_common_raw=[1.,2.],oshd_mean_common_m=[3.,4.]))
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        a,b,n = consecutive_changes(f)
    assert n==1 and a[0]==b[0]==1


def test_constant_changes_and_zero_changes_are_not_zero_snow():
    f = pd.DataFrame(dict(spass_civil_date=pd.date_range('2023-01-01',periods=4).strftime('%Y-%m-%d'),
                          spass_mean_common_raw=[8.,8.,8.,8.],oshd_mean_common_m=[3.,4.,6.,9.]))
    a,b,n = consecutive_changes(f)
    r = rank_correlation(a,b)
    assert n==3 and r['spass_zero_paired_days']==3
    assert r['spearman_rho'] is None and r['diagnostic_status']=='spass_series_constant'
    assert rank_correlation([0,1,1,2],[0,1,2,2])['spearman_rho']==pytest.approx(np.corrcoef([1,2.5,2.5,4],[1,2,3.5,3.5])[0,1])


def test_equal_coverage_does_not_imply_same_observed_footprints():
    r = support_stability([[True,False],[False,True],[False,True]],[5.,5.])
    assert r['support_adjacent_pairs_checked']==2 and r['support_changed_pairs']==1
    assert r['max_changed_support_length_m']==10.
    s = support_stability([[True,False],[True,False]],[5.,5.])
    assert s['support_changed_pairs']==0 and s['max_changed_support_length_m']==0
    with pytest.raises(ValueError,match='Aligned footprint'):
        support_stability([[True,False]],[1.])


def test_all_actual_change_coefficients_independently_recomputed():
    r = pd.read_csv(ROOT/'data_processed/native_snow_change_rank_diagnostic_stage72.csv',float_precision='round_trip')
    daily = pd.read_csv(ROOT/'data_processed/native_snow_daily_common_support_stage70.csv',float_precision='round_trip')
    for row in r[r.spearman_change_rho.notna()].itertuples():
        f = daily[daily.station_group_id.eq(row.station_group_id)&daily.oshd_date_offset_days.eq(row.oshd_date_offset_days)].sort_values('spass_civil_date')
        dates = np.array(f.spass_civil_date,dtype='datetime64[D]')
        assert (np.diff(dates)==np.timedelta64(1,'D')).all()
        a,b = np.diff(f.spass_mean_common_raw.to_numpy()),np.diff(f.oshd_mean_common_m.to_numpy())
        assert len(a)==len(b)==150 and np.isfinite(a).all() and np.isfinite(b).all()
        expected = np.corrcoef(direct_ranks(a),direct_ranks(b))[0,1]
        assert row.spearman_change_rho==pytest.approx(expected,abs=1e-15)
        reference = r[r.station_group_id.eq(row.station_group_id)&r.reference_offset].spearman_change_rho.iloc[0]
        assert row.rho_difference_from_offset_zero==row.spearman_change_rho-reference
        assert row.spass_zero_changes==int((a==0).sum()) and row.oshd_zero_changes==int((b==0).sum())


def test_actual_native_support_including_all_month_boundaries_is_stable():
    parent = json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
    audit,inputs = audit_support(parent)
    assert len(audit)==120 and len(inputs)==16
    assert sum(v['support_adjacent_pairs_checked'] for v in audit.values())==18000
    assert sum(v['support_changed_pairs'] for v in audit.values())==0
    assert all(v['max_changed_support_length_m']==0 for v in audit.values())


def test_all_groups_levels_and_original_coverage_preserved():
    r = pd.read_csv(ROOT/'data_processed/native_snow_change_rank_diagnostic_stage72.csv',float_precision='round_trip')
    old = pd.read_csv(ROOT/'data_processed/native_snow_rank_diagnostic_stage71.csv',float_precision='round_trip')
    assert len(r)==210 and r.station_group_id.nunique()==70 and r.group_retained.all()
    assert not r.duplicated(['station_group_id','oshd_date_offset_days']).any()
    for col in ['station_group_id','station_group_name','oshd_date_offset_days','group_retained',
                'min_common_observed_length_share','mean_common_observed_length_share','unique_mapped_axis_length_m']:
        pd.testing.assert_series_equal(r[col],old[col])
    np.testing.assert_equal(r.spearman_daily_level_rho_stage71.to_numpy(),old.spearman_rho.to_numpy())
    assert r.spearman_change_rho.notna().sum()==120
    available = r.spearman_change_rho.notna()
    assert r.loc[available,'finite_paired_changes'].eq(150).all()
    assert r.loc[~available,'finite_paired_changes'].isna().all()
    assert r.loc[~available,'support_changed_pairs'].isna().all()
    assert not r.physical_unit_comparison_available.any() and not r.p_value_or_ci_computed.any()
    assert r.spass_source_unit.eq('UNKNOWN').all() and r.oshd_source_unit.eq('m').all()
    assert len(DEFS)==31


def test_registry_prefix_and_complementary_scope_preserved():
    summary = json.loads((ROOT/'reports/native_snow_change_rank_diagnostic_stage72_summary.json').read_text(encoding='utf8'))
    for path,b in summary['prior_registry_rows_and_digest'].items():
        f = pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        assert row_digest(f.iloc[:b['rows']])==b['sha256']
    assert summary['daily_level_reference_preserved'] and summary['five_own_preentry_winters_unchanged']
    assert not summary['source_splicing_or_calibration'] and not summary['choose_best_lag']
    assert not summary['physical_between_model_difference_or_conversion'] and not summary['p_values_or_ci_computed']
    assert not summary['new_clustering_or_effect_fit']


def test_technical_calendar_repair_keeps_first_version_and_all_results():
    repair = json.loads((ROOT/'config/native_snow_calendar_repair_stage72.json').read_text(encoding='utf8'))
    for path,h in repair['archived_first_version_sha256'].items():
        assert digest(path)==h
    assert digest('src/descriptive/diagnose_native_snow_changes_stage72.py')==repair['repaired_producer_sha256']
    old = json.loads((ROOT/'data_interim/native_snow_changes_stage72_before_calendar_fix/native_snow_change_rank_diagnostic_stage72_summary.json').read_text(encoding='utf8'))
    new = json.loads((ROOT/'reports/native_snow_change_rank_diagnostic_stage72_summary.json').read_text(encoding='utf8'))
    old['input_sha256']['src/descriptive/diagnose_native_snow_changes_stage72.py']=repair['repaired_producer_sha256']
    assert old==new
    for path,h in new['output_sha256'].items():
        assert digest(path)==h
