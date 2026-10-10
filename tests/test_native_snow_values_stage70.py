"""Common observed support is neither imputation nor source unit certification."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from netCDF4 import Dataset

from src.data_processing.extract_native_snow_values_stage70 import finite_values, support_metrics
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

ROOT=Path(__file__).resolve().parents[1]


def test_mask_zero_negative_and_exact_same_weight_denominator():
    masked=np.ma.array([0.,-2.,-9999.,np.inf],mask=[False,False,True,False])
    a=finite_values(masked)
    assert a[0]==0 and a[1]==-2 and np.isnan(a[2]) and np.isinf(a[3])
    a=np.array([0.,-2.,np.nan,10.])
    b=np.array([0.,4.,6.,np.nan]);w=np.array([1.,2.,3.,4.])
    m=support_metrics(a,b,w)
    assert m['common_observed_length_m']==3
    assert m['spass_mean_common_raw']==pytest.approx(-4/3)
    assert m['oshd_mean_common_m']==pytest.approx(8/3)
    assert m['spass_only_observed_length_m']==4 and m['oshd_only_observed_length_m']==3
    assert m['spass_zero_common_length_m']==1 and m['spass_negative_common_length_m']==2
    m=support_metrics(np.array([np.nan]),np.array([0.]),np.array([2.]))
    assert m['common_observed_length_share']==0 and m['spass_mean_common_raw'] is None and m['oshd_mean_common_m'] is None
    with pytest.raises(ValueError,match='positive exact'):
        support_metrics(np.array([0.]),np.array([0.]),np.array([0.]))


def test_native_series_all_fixed_dates_and_missing_groups_retained():
    f=pd.read_csv(ROOT/'data_processed/native_snow_daily_common_support_stage70.csv',float_precision='round_trip')
    c=pd.read_csv(ROOT/'data_processed/native_snow_value_coverage_stage70.csv')
    groups=pd.read_csv(ROOT/'data_processed/terrain_reference_profiles_stage67.csv')
    assert len(f)==40*151*3 and len(c)==70*3 and c.group_retained.all()
    assert set(c.station_group_id)==set(groups.station_group_id)
    assert (f.groupby(['station_group_id','oshd_date_offset_days']).size()==151).all()
    assert not f.duplicated(['station_group_id','spass_civil_date','oshd_date_offset_days']).any()
    assert f.spass_unit.eq('UNKNOWN').all() and f.oshd_unit.eq('m').all()
    assert not f.physical_unit_comparison_available.any() and not c.physical_unit_comparison_available.any()
    missing=c.days_with_common_observed_length.isna()
    assert missing.sum()==30*3
    assert c.loc[missing,'min_common_observed_length_share'].isna().all()
    total=f.common_observed_length_m+f.spass_only_observed_length_m+f.oshd_only_observed_length_m+f.neither_observed_length_m
    np.testing.assert_allclose(total,f.unique_mapped_axis_length_m,rtol=1e-12,atol=1e-10)
    assert f.common_observed_length_share.between(0,1).all()


def test_actual_source_samples_match_checkpoint_no_cartesian_misindex():
    s=json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
    for model in ['spass','oshd']:
        key=next(k for k in s['source_value_checkpoints'] if k.startswith(model))
        m=s['source_value_checkpoints'][key];contract=m['contract']
        with np.load(ROOT/'data_interim/native_snow_values_stage70'/f'{key}.npz') as cache:
            values=cache['values']
        indices=contract['indices'];times=contract['times']
        with ascii_link(ROOT/contract['source_file']) as link,Dataset(link) as d:
            v=d.variables[contract['variable']]
            for ti,ci in [(0,0),(len(times)//2,len(indices)//2),(len(times)-1,len(indices)-1)]:
                e,n=indices[ci];t=times[ti]
                value=finite_values(v[t,n,e] if model=='spass' else v[e,n,t])
                np.testing.assert_equal(values[ti,ci],value)


def test_recompute_actual_group_day_from_native_cache():
    s=json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
    f=pd.read_csv(ROOT/'data_processed/native_snow_daily_common_support_stage70.csv',float_precision='round_trip')
    weights=pd.read_csv(ROOT/'data_processed/native_snow_cell_pairs_stage69.csv',float_precision='round_trip')
    dates=pd.read_csv(ROOT/'data_processed/native_snow_date_pairs_stage69.csv')
    sm=s['source_value_checkpoints']['spass_pilot']['contract']
    sloc={tuple(v):i for i,v in enumerate(sm['indices'])}
    with np.load(ROOT/'data_interim/native_snow_values_stage70/spass_pilot.npz') as cache:
        sv=cache['values']
    # Three geographically distinct groups, all three offsets; not independent causal samples.
    for gid in list(f.station_group_id.unique())[::15]:
        part=weights[weights.station_group_id.eq(gid)]
        for lag in [-1,0,1]:
            row=f[f.station_group_id.eq(gid)&f.oshd_date_offset_days.eq(lag)].iloc[70]
            date=dates[dates.spass_civil_date.eq(row.spass_civil_date)&dates.oshd_date_offset_days.eq(lag)].iloc[0]
            key=next(k for k,m in s['source_value_checkpoints'].items() if m['contract']['source_file']==date.oshd_member_file)
            om=s['source_value_checkpoints'][key]['contract'];oloc={tuple(v):i for i,v in enumerate(om['indices'])}
            with np.load(ROOT/'data_interim/native_snow_values_stage70'/f'{key}.npz') as cache:
                ov=cache['values']
            ai=[sloc[t] for t in part[['spass_e_index','spass_n_index']].itertuples(index=False,name=None)]
            bi=[oloc[t] for t in part[['oshd_e_index','oshd_n_index']].itertuples(index=False,name=None)]
            a=sv[sm['times'].index(int(date.spass_time_index)),ai]
            b=ov[om['times'].index(int(date.oshd_time_index)),bi]
            observed=np.isfinite(a)&np.isfinite(b)
            w=part.unique_axis_length_m.to_numpy()[observed]
            assert row.common_observed_length_m==math.fsum(w)
            if len(w):
                assert row.spass_mean_common_raw==math.fsum(w*a[observed])/math.fsum(w)
                assert row.oshd_mean_common_m==math.fsum(w*b[observed])/math.fsum(w)
            else:
                assert pd.isna(row.spass_mean_common_raw) and pd.isna(row.oshd_mean_common_m)


def test_old_registry_rows_exact_and_no_conversion_or_splice():
    s=json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
    for path,b in s['prior_registry_rows_and_digest'].items():
        f=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        assert row_digest(f.iloc[:b['rows']])==b['sha256']
    assert not s['new_unit_conversion'] and not s['physical_difference_computed']
    assert not s['source_splicing_or_calibration'] and not s['new_clustering_or_effect_fit']


def test_documentary_source_urls_and_terms_repaired_only_on_new_rows():
    config=json.loads((ROOT/'config/native_snow_provenance_corrections_stage70.json').read_text(encoding='utf8'))
    sources=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    for c in config['corrections']:
        index=sources.index[sources.source_id.eq(c['source_id'])]
        assert len(index)==1 and index[0]>=config['prior_source_rows_protected']
        assert sources.at[index[0],c['field']]==c['new']
