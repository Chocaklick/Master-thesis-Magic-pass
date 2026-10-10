"""Descriptive Spearman handles ties, missing pairs and fixed source alignment."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.descriptive.diagnose_native_snow_ranks_stage71 import rank_correlation,validate_dates
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

ROOT=Path(__file__).resolve().parents[1]


def average_ranks_independent(values):
    # Direct definition counts: no pandas/scipy rank implementation shared.
    return np.array([1+sum(other<value for other in values)+(sum(other==value for other in values)-1)/2 for value in values])


def test_ties_zero_missing_and_positive_unit_invariance():
    a=np.array([0.,0.,1.,2.,3.,np.nan]);b=np.array([0.,1.,1.,2.,3.,7.])
    result=rank_correlation(a,b)
    assert result['finite_paired_days']==5 and result['spass_tied_paired_days']==2 and result['oshd_tied_paired_days']==2
    assert result['spass_zero_paired_days']==2 and result['oshd_zero_paired_days']==1
    ra=np.array([1.5,1.5,3,4,5]);rb=np.array([1,2.5,2.5,4,5])
    expected=np.corrcoef(ra,rb)[0,1]
    assert result['spearman_rho']==pytest.approx(expected,abs=1e-15)
    assert rank_correlation(a*100,b)['spearman_rho']==result['spearman_rho']
    assert rank_correlation([1,2,3],[9,6,3])['spearman_rho']==-1
    assert rank_correlation([1,2,3],[2,4,6])['spearman_rho']==1


def test_constant_and_insufficient_pairs_remain_missing_not_zero():
    for a,b,status in [([0,0],[1,2],'spass_series_constant'),([1,2],[0,0],'oshd_series_constant'),
                       ([0,0],[0,0],'both_series_constant'),([np.nan,1],[2,3],'fewer_than_two_finite_pairs')]:
        result=rank_correlation(a,b)
        assert result['diagnostic_status']==status and result['spearman_rho'] is None
    with pytest.raises(ValueError,match='Aligned'):
        rank_correlation([1,2],[1])


def test_all_group_lag_rows_and_source_coverages_retained():
    r=pd.read_csv(ROOT/'data_processed/native_snow_rank_diagnostic_stage71.csv',float_precision='round_trip')
    c=pd.read_csv(ROOT/'data_processed/native_snow_value_coverage_stage70.csv',float_precision='round_trip')
    assert len(r)==210 and r.station_group_id.nunique()==70 and r.group_retained.all()
    assert not r.duplicated(['station_group_id','oshd_date_offset_days']).any()
    for col in ['station_group_id','station_group_name','oshd_date_offset_days','group_retained',
                'days_with_full_common_length','min_common_observed_length_share','mean_common_observed_length_share','unique_mapped_axis_length_m']:
        pd.testing.assert_series_equal(r[col],c[col])
    assert r.spearman_rho.notna().sum()==120
    assert r.loc[r.spearman_rho.notna(),'finite_paired_days'].eq(151).all()
    assert r.loc[r.spearman_rho.isna(),'finite_paired_days'].isna().all()
    assert not r.physical_unit_comparison_available.any() and not r.p_value_or_ci_computed.any()
    assert r.spass_source_unit.eq('UNKNOWN').all()


def test_all_actual_coefficients_match_independent_rank_definition():
    r=pd.read_csv(ROOT/'data_processed/native_snow_rank_diagnostic_stage71.csv',float_precision='round_trip')
    d=pd.read_csv(ROOT/'data_processed/native_snow_daily_common_support_stage70.csv',float_precision='round_trip')
    for row in r[r.spearman_rho.notna()].itertuples():
        f=d[d.station_group_id.eq(row.station_group_id)&d.oshd_date_offset_days.eq(row.oshd_date_offset_days)]
        a=f.spass_mean_common_raw.to_numpy();b=f.oshd_mean_common_m.to_numpy()
        ra=average_ranks_independent(a);rb=average_ranks_independent(b)
        expected=np.corrcoef(ra,rb)[0,1]
        assert row.spearman_rho==pytest.approx(expected,abs=1e-15)
        reference=r[r.station_group_id.eq(row.station_group_id)&r.reference_offset].spearman_rho.iloc[0]
        assert row.rho_difference_from_offset_zero==row.spearman_rho-reference


def test_calendar_and_duplicate_guards():
    d=pd.read_csv(ROOT/'data_processed/native_snow_daily_common_support_stage70.csv')
    decision=json.loads((ROOT/'config/snow_rank_diagnostic_decisions_stage71.json').read_text(encoding='utf8'))
    validate_dates(d,decision)
    with pytest.raises(ValueError,match='Duplicate'):
        validate_dates(pd.concat([d,d.iloc[:1]],ignore_index=True),decision)
    with pytest.raises(ValueError,match='Missing/extra'):
        validate_dates(d.iloc[1:],decision)
    broken=d.copy();broken.loc[0,'oshd_civil_date']='2020-01-01'
    with pytest.raises(ValueError,match='date offset differs'):
        validate_dates(broken,decision)


def test_registry_prefix_and_approved_no_selection_no_conversion():
    s=json.loads((ROOT/'reports/native_snow_rank_diagnostic_stage71_summary.json').read_text(encoding='utf8'))
    for path,b in s['prior_registry_rows_and_digest'].items():
        f=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        assert row_digest(f.iloc[:b['rows']])==b['sha256']
    assert not s['physical_difference_or_conversion'] and not s['source_splicing_or_calibration']
    assert not s['choose_best_lag'] and not s['p_values_or_ci_computed']
    assert s['five_own_preentry_winters_unchanged'] and not s['new_clustering_or_effect_fit']
