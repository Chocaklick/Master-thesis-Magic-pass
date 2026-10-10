"""Winter calendar, observed-day weighting, native paired indexing and checkpoints."""
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from netCDF4 import Dataset

import src.data_processing.compare_snow_multiwinter_stage76 as worker
import src.data_collection.collect_oshd_multiwinter_stage76 as collector
from src.data_collection.collect_oshd_profile_audit import parse_record, official_download_anchor, validate_download_response
from src.data_collection.collect_oshd_multiwinter_stage76 import zenodo_can_fetch
from src.data_processing.prepare_native_snow_weights_stage69 import digest, native_grid

ROOT=Path(__file__).resolve().parents[1]


def test_current_robot_refresh_reuses_recent_policy_and_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setattr(collector,'ROOT',tmp_path)
    folder=tmp_path/'data_external/source_evidence'
    folder.mkdir(parents=True)
    original=folder/'old.txt'
    original.write_text('User-agent: *\nDisallow: /api\n',encoding='utf8')
    raw=folder/'ZENODO_ROBOTS_REFRESH_STAGE76_test.txt'
    raw.write_text('User-agent: *\nAllow: /api/records/*/files\n',encoding='utf8')
    sidecar=raw.with_suffix('.metadata.json')
    m=dict(raw_file=raw.relative_to(tmp_path).as_posix(),sha256=collector.digest(raw)[1],
           retrieval_date=datetime.now(timezone.utc).isoformat())
    sidecar.write_text(json.dumps(m),encoding='utf8')
    calls=[]
    def denied(request,timeout):
        calls.append(request.full_url)
        raise PermissionError('synthetic unavailable policy')
    monkeypatch.setattr(collector,'urlopen',denied)
    events=[]
    monkeypatch.setattr(collector,'append_log',events.append)
    text,meta=collector.current_robot_policy(original)
    assert meta==m and 'Allow:' in text and not calls
    m['retrieval_date']='2026-10-01T00:00:00+00:00'
    sidecar.write_text(json.dumps(m),encoding='utf8')
    with pytest.raises(PermissionError,match='synthetic unavailable'):
        collector.current_robot_policy(original)
    assert calls==['https://zenodo.org/robots.txt']
    assert events[0]['success']=='False' and events[0]['status']=='failed'


def test_actual_completed_winter_metrics_recomputed_independently():
    summary=json.loads((ROOT/worker.SUMMARY).read_text(encoding='utf8'))
    out=pd.read_csv(ROOT/worker.OUTPUT)
    for year in summary['completed_water_years']:
        daily=pd.read_csv(worker.CACHE/f'daily_WY{year}.csv')
        for (group,lag),f in daily.groupby(['station_group_id','oshd_date_offset_days']):
            row=out.loc[out.water_year.eq(year)&out.station_group_id.eq(group)&out.oshd_date_offset_days.eq(lag)].iloc[0]
            x=f.spass_mean_common_raw.to_numpy(float);y=f.oshd_mean_common_m.to_numpy(float)
            valid=np.isfinite(x)&np.isfinite(y)
            assert row.finite_paired_days==valid.sum()
            assert row.requested_days==len(worker.winter_dates(year))
            if valid.any():
                d=y[valid]-x[valid]
                np.testing.assert_allclose([row.spass_winter_mean_m,row.oshd_winter_mean_m,row.mean_oshd_minus_spass_m,
                    row.daily_mean_absolute_difference_m,row.daily_root_mean_square_difference_m],
                    [x[valid].mean(),y[valid].mean(),d.mean(),np.abs(d).mean(),np.sqrt(np.mean(d*d))],rtol=1e-12,atol=1e-12)


def test_robot_file_exception_longest_match_not_general_api_bypass():
    text=(ROOT/'data_external/source_evidence/zenodo.org_robots_20261009T163957Z.txt').read_text(encoding='utf8')
    assert zenodo_can_fetch(text,'https://zenodo.org/api/records/17313889/files/OSHD_DATA_WY2016.zip/content')
    for path in ['/api/records/17313889','/api/records/17313889/files-archive','/records/17313889/preview','/login']:
        assert not zenodo_can_fetch(text,'https://zenodo.org'+path)
    assert not zenodo_can_fetch(text,'https://example.org/api/records/17313889/files/foo/content')
    assert not zenodo_can_fetch(text,'https://zenodo.org/api/%72ecords/17313889/files/foo/content')
    tie='User-agent: *\nDisallow: /same\nAllow: /same\n'
    assert zenodo_can_fetch(tie,'https://zenodo.org/same')
    with pytest.raises(ValueError,match='Changed robot groups'):
        zenodo_can_fetch(text+'\nUser-agent: OtherBot\nDisallow: /\n','https://zenodo.org/')


def test_all_eight_calendars_include_actual_leap_days_and_five_months():
    for year in range(2016,2024):
        d=worker.winter_dates(year)
        assert set(d.month)=={12,1,2,3,4}
        assert len(d)==(152 if year in [2016,2020] else 151)
        assert str(d[0].date())==f'{year-1}-12-01' and str(d[-1].date())==f'{year}-04-30'


def test_all_prepared_spass_months_source_units_and_source_indices():
    p=json.loads((ROOT/'reports/spass_multiwinter_cache_preparation_stage76_summary.json').read_text(encoding='utf8'))
    assert p['complete_months']==35 and p['observed_day_count']==1059
    assert p['all35_months_prepared'] and not p['group_profiles_computed']
    for month,r in p['months'].items():
        folder=worker.CACHE/'values'
        m=json.loads((folder/f'spass_{month}.json').read_text(encoding='utf8'))
        assert m['source_unit']==r['source_unit']=='UNKNOWN' and not m['missing_dates']
        assert len(m['contract']['indices'])==325
        assert digest((folder/f'spass_{month}.npz').relative_to(ROOT))==r['cache_sha256']
        with np.load(folder/f'spass_{month}.npz',allow_pickle=False) as data:
            assert data['values'].shape==(r['observed_days'],325)


def test_observed_paired_days_equal_weight_zero_missing_and_duplicate_dates():
    f=pd.DataFrame(dict(spass_civil_date=['2023-01-01','2023-01-02','2023-01-03'],
                        spass_mean_common_raw=[0.,2.,np.nan],oshd_mean_common_m=[0.,4.,9.],
                        common_observed_length_share=[1.,.5,0.],spass_negative_common_length_m=[0,0,0],oshd_negative_common_length_m=[0,0,0]))
    r=worker.aggregate_daily(f,3)
    assert r['finite_paired_days']==2 and r['missing_pair_days']==1
    assert r['spass_winter_mean_m']==1. and r['oshd_winter_mean_m']==2.
    assert r['mean_common_observed_length_share']==.5 and r['min_common_observed_length_share']==0.
    assert r['status']=='computed_partial_pairs'
    f.loc[:,'spass_mean_common_raw']=np.nan
    r=worker.aggregate_daily(f,3)
    assert r['status']=='no_finite_pairs' and r['spass_winter_mean_m'] is None
    with pytest.raises(ValueError,match='Duplicated'):
        worker.aggregate_daily(pd.concat([f,f.iloc[:1]]),4)


def test_real_public_inventory_and_previous_pilot_identity():
    text=(ROOT/'data_external/source_evidence/SLF_OSHD_RECORD_PUBLIC_HTML_2026_10_09_20261009T163957Z.html').read_text(encoding='utf8')
    _,files=parse_record(text,range(2016,2023))
    assert sum(f['expected_bytes'] for f in files)==4507509648
    assert all(official_download_anchor(text,f['url']).endswith('?download=1') for f in files)
    checkpoint=json.loads((worker.CACHE/'daily_WY2023.json').read_text(encoding='utf8'))
    assert checkpoint['source_checkpoints']['reused_stage70_file']=='data_processed/native_snow_daily_common_support_stage70.csv'
    out=pd.read_csv(ROOT/worker.OUTPUT)
    old=pd.read_csv(ROOT/'data_processed/native_snow_metric_diagnostic_stage75.csv').set_index(['station_group_id','oshd_date_offset_days'])
    current=out[out.water_year.eq(2023)].set_index(old.index.names)
    assert len(out)==1680 and out.station_group_id.nunique()==70 and out.group_retained.all()
    np.testing.assert_allclose(current.mean_oshd_minus_spass_m,old.loc[current.index,'mean_oshd_minus_spass_m'],equal_nan=True)
    assert not out.source_spliced_or_calibrated.any()


def test_original_native_order_paired_indices_masks_and_cache_are_not_cartesian(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'CACHE',tmp_path/'cache')
    (tmp_path/'cache').mkdir()
    # Pair two diagonal cells, both axis directions, including true zero/masked fill.
    origin=tmp_path/'source.nc'
    with Dataset(origin,'w') as d:
        for name,size in [('easting',3),('northing',2),('time',2)]:
            d.createDimension(name,size)
        d.createVariable('easting','f8',('easting',))[:]=[100,350,600]
        d.createVariable('northing','f8',('northing',))[:]=[750,500]
        t=d.createVariable('time','f8',('time',));t.units='days since 2023-01-01T06:00:00 UTC+01:00';t[:]=[0,1]
        h=d.createVariable('hs','f8',('easting','northing','time'),fill_value=-999);h.unit='m'
        h[:]=np.arange(12).reshape(3,2,2);h[0,0,0]=0.;h[2,1,1]=-999
    # ROOT/path accepts an absolute temporary input; cache sidecar digest uses patched root helper.
    original_digest=worker.digest
    monkeypatch.setattr(worker,'digest',lambda p: original_digest(p) if not Path(p).is_absolute() else __import__('hashlib').sha256(Path(p).read_bytes()).hexdigest())
    # read_selected uses relative_to(ROOT) for cache; put synthetic ROOT around tmp.
    monkeypatch.setattr(worker,'ROOT',tmp_path)
    # Producer SHA lookup must refer to the real protected script.
    def test_digest(p):
        path=Path(p)
        if str(p)=='src/data_processing/compare_snow_multiwinter_stage76.py':
            return original_digest(str(p))
        return __import__('hashlib').sha256((path if path.is_absolute() else tmp_path/path).read_bytes()).hexdigest()
    monkeypatch.setattr(worker,'digest',test_digest)
    grid=native_grid(np.array([100,350,600]),np.array([750,500]))
    args=(str(origin),test_digest(origin),np.array([[0,0],[2,1]]),['2023-01-01','2023-01-02','2023-01-03'],
          'hs',('easting','northing','time'),('easting','northing'),grid,'test')
    values,meta=worker.read_selected(*args)
    np.testing.assert_array_equal(values['2023-01-01'],[0.,10.])
    np.testing.assert_allclose(values['2023-01-02'],[1.,np.nan],equal_nan=True)
    assert meta['missing_dates']==['2023-01-03'] and meta['source_unit']=='m'
    cached,_=worker.read_selected(*args)
    np.testing.assert_allclose(cached['2023-01-02'],values['2023-01-02'],equal_nan=True)
    changed=list(args);changed[2]=np.array([[0,1],[2,0]])
    with pytest.raises(ValueError,match='Frozen value checkpoint'):
        worker.read_selected(*changed)
