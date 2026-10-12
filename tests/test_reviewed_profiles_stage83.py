"""Reviewed terrain/snow coverage, old-source reuse and original calendars."""
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from netCDF4 import Dataset,num2date
from shapely import wkt
from src.data_processing.build_reviewed_terrain_profiles_stage82 import ROOT,OUTPUT as TERRAIN,make_record
from src.data_processing.build_reviewed_spass_profiles_stage83 import OUTPUTS as SNOW,approved_windows
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def read(p):return pd.read_csv(ROOT/p,float_precision='round_trip',low_memory=False)


def test_all69groups_original_dates_and345windows_retained():
    t=read(TERRAIN);s=read(SNOW[2]);w=read(SNOW[0]);annual=read(SNOW[1]);g=read('data_processed/winter_profile_metric_network_stage80.csv')
    assert len(t)==len(s)==69 and t.station_group_id.is_unique and s.station_group_id.is_unique
    assert set(t.station_group_id)==set(s.station_group_id)==set(g.station_group_id)
    assert t.group_retained.all() and s.group_retained.all()
    assert len(w)==len(annual)==345 and not w.duplicated(['station_group_id','winter_start_year']).any()
    pd.testing.assert_frame_equal(w,approved_windows(),check_exact=True)
    assert w.groupby('station_group_id').size().eq(5).all()
    assert (pd.to_datetime(w.winter_end_date)<pd.to_datetime(w.first_base_entry_month)).all()
    assert (pd.to_datetime(w.winter_start_date).dt.month==12).all()
    assert (pd.to_datetime(w.winter_end_date).dt.month==4).all()
    assert t.current_proxy_not_verified_preentry.all() and s.current_proxy_not_verified_preentry.all()


def test_exact_635tile_plan_and309real_successes_not_repeated():
    q=json.loads((ROOT/'config/terrain_reviewed_tile_sources_stage81.json').read_text())
    m=json.loads((ROOT/'reports/reviewed_terrain_queue_stage81_summary.json').read_text())
    assert len(q)==len({r['url'] for r in q})==len({r['source_id'] for r in q})==635
    assert sum(bool(r['cached_raw_file']) for r in q)==326 and m['new_required_tile_count']==309
    absent=[g for g in m['groups'] if g.get('catalogue_absent_native_tile_keys')]
    assert len(absent)==1 and absent[0]['station_group_id']=='MP_GROUP_RESORT__la_dole_jura_sur_leman'
    events=json.loads((ROOT/'data_interim/terrain_reviewed_events_stage81.json').read_text())
    log=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    assert len(events)==309 and len({r['source_id'] for r in events})==309
    for e in events:
        assert e['status']=='downloaded' and str(e['HTTP_status'])=='200' and e['source_id'].startswith('SWISSTOPO_ALTI3D_TILE_STAGE81_')
        part=log[log.timestamp.eq(e['timestamp'])&log.source_id.eq(e['source_id'])]
        assert len(part)==1 and part.checksum.iloc[0]==e['checksum'] and sha(e['raw_file'])==e['checksum']


def test_67terrain_profiles_two_gaps_and_approved_seams():
    f=read(TERRAIN);assert f.observed_altitude_length_m.gt(0).sum()==67
    missing=f[f.terrain_status.eq('missing_geometry_not_zero')];assert len(missing)==2
    assert missing.minimum_observed_altitude_m.isna().all() and missing.unique_mapped_axis_length_m.isna().all()
    assert f.terrain_northness.notna().sum()==67 and f.terrain_eastness.notna().sum()==67
    assert np.hypot(f.terrain_northness.dropna(),f.terrain_eastness.dropna()).le(1+1e-12).all()
    for col in ['orientation_coverage_share','gradient_coverage_share','altitude_coverage_of_full_candidate_share','gradient_coverage_of_full_candidate_share']:
        assert f[col].dropna().between(0,1+1e-12).all()
    assert f.length_weighted_observed_slope_degrees.dropna().between(0,90).all()
    assert f.mixed_edition_complete_neighbourhood_length_m.gt(0).sum()==7
    d=f.set_index('station_group_id').loc['MP_GROUP_RESORT__la_dole_jura_sur_leman']
    assert d.observed_altitude_length_m/d.unique_mapped_axis_length_m==pytest.approx(.6582480699726465)
    assert d.altitude_coverage_of_full_candidate_share<.6582480699726465


def test_all67_native_cell_summaries_and_exact_original39reuse():
    f=read(TERRAIN);old=read('data_processed/terrain_reference_profiles_stage67.csv').set_index('station_group_id')
    m=json.loads((ROOT/'reports/terrain_reviewed_profiles_stage82_summary.json').read_text())
    assert len(m['reused_exact_original_cell_groups'])==39 and m['new_extraction_group_count']==28
    for g in f[f.cell_detail_file.notna()].itertuples():
        cells=read(g.cell_detail_file)
        base={c:getattr(g,c) for c in ['source_id','station_group_id','station_group_name','group_retained','current_proxy_not_verified_preentry',
            'unique_mapped_axis_length_m','full_candidate_axis_length_m','measured_share_of_mapped_candidate_length','parent_station_group_ids','seam_policy']}
        r=make_record(base,cells)
        for c,v in r.items():
            if isinstance(v,(float,np.floating)):assert getattr(g,c)==pytest.approx(v,rel=1e-12,abs=1e-10)
        seam=cells.horn_complete_native_neighbourhood&cells.mixed_reference_neighbourhood
        assert cells.loc[seam,['terrain_slope_degrees','terrain_aspect_degrees']].isna().all().all()
        assert not cells.loc[seam,'gradient_observed'].any()
        assert cells.loc[cells.gradient_observed&cells.terrain_slope_degrees.eq(0),'terrain_aspect_degrees'].isna().all()
        if g.cache_mode.startswith('reuse'):
            o=read(old.loc[g.station_group_id,'cell_detail_file'])
            columns=[c for c in o if c not in ['source_id','horn_calculation_status']]
            pd.testing.assert_frame_equal(cells[columns],o[columns],check_exact=True)
            for c in ['length_weighted_observed_altitude_m','length_weighted_observed_slope_degrees','terrain_northness','terrain_eastness']:
                assert getattr(g,c)==old.loc[g.station_group_id,c]


def test_54_five_winter_means_equal_weights_no_missing_fallback():
    s=read(SNOW[2]);w=read(SNOW[1]);assert s.spass_five_preentry_winters_mean_m.notna().sum()==54
    assert s.status.value_counts().to_dict()=={'five_winters_full_coverage':53,'incomplete_five_winters':13,'missing_geometry':2,'five_winters_partial_coverage':1}
    assert not s.source_spliced_or_calibrated.any() and s.spass_original_unit.eq('UNKNOWN').all() and s.spass_metres_assumed.all()
    for g in s.itertuples():
        part=w[w.station_group_id.eq(g.station_group_id)];values=part.spass_winter_mean_m.to_numpy()
        assert len(part)==5 and g.observed_winter_count==np.isfinite(values).sum()
        if np.isfinite(values).all():assert g.spass_five_preentry_winters_mean_m==math.fsum(values)/5
        else:assert pd.isna(g.spass_five_preentry_winters_mean_m)
    assert s.loc[s.status.eq('five_winters_partial_coverage'),'station_group_id'].tolist()==['MP_GROUP_RESORT__vallee_de_joux']


def test_all313_winter_means_rebuilt_from_observed_days_only():
    s=json.loads((ROOT/'reports/spass_reviewed_profiles_stage83_summary.json').read_text())
    w=read(SNOW[1]);count=0
    assert w.spass_winter_mean_m.notna().sum()==313
    for year,p in s['daily_checkpoints'].items():
        f=read(p['path']);assert not f.duplicated(['station_group_id','civil_date']).any()
        for gid,d in f.groupby('station_group_id'):
            row=w[w.station_group_id.eq(gid)&w.winter_start_year.eq(int(year))].iloc[0]
            assert len(d)==row.expected_days
            observed=d.spass_daily_mean_m.dropna()
            assert row.observed_days==len(observed) and row.missing_days==len(d)-len(observed)
            assert row.spass_winter_mean_m==math.fsum(observed)/len(observed)
            count+=1
    assert count==313


def test_original39_geometry_snow_means_numerically_unchanged():
    m=json.loads((ROOT/'reports/terrain_reviewed_profiles_stage82_summary.json').read_text())
    ids=m['reused_exact_original_cell_groups'];old=read('data_processed/spass_preentry_profiles_stage77.csv').set_index('station_group_id')
    new=read(SNOW[2]).set_index('station_group_id')
    np.testing.assert_allclose(new.loc[ids,'spass_five_preentry_winters_mean_m'],old.loc[ids,'spass_five_preentry_winters_mean_m'],rtol=1e-12,atol=1e-12,equal_nan=True)


def test_new315_original_snow_cells_against_direct_raw_reads():
    s=json.loads((ROOT/'reports/snow_grid_metadata_compatibility_stage47.json').read_text())
    for month in ['2012-12','2023-04']:
        path=ROOT/f'data_interim/spass_reviewed_stage83/values/spass_extra_{month}.json'
        m=json.loads(path.read_text());ids=np.asarray(m['contract']['indices'],dtype=int)
        assert len(ids)==315 and m['source_unit']=='UNKNOWN' and m['source_masks_applied']
        with np.load(path.with_suffix('.npz'),allow_pickle=False) as z:values=z['values']
        with ascii_link(ROOT/s['spass_raw_file']) as link,Dataset(link) as ds:
            day=m['observed_dates'][0];t=int(m['original_date_coordinates'][day][0])
            raw=np.asarray(np.ma.filled(ds.variables['HSCLQMD'][t,:,:],np.nan))
            np.testing.assert_equal(values[0],raw[ids[:,1],ids[:,0]])


def test_native_headers_registration_and_unchanged_producers():
    m=json.loads((ROOT/'reports/terrain_reviewed_profiles_stage82_summary.json').read_text())
    assert len(m['header_checks'])==635
    for h in m['header_checks']:
        assert h['shape']==[500,500] and h['resolution']==[2.,2.] and h['units']==['metre'] and h['crs']=='EPSG:2056'
    r=json.loads((ROOT/'reports/reviewed_profile_registry_stage83_summary.json').read_text())
    assert r['numerical_producers_and_results_unchanged'] and r['no_new_request_or_recomputation']
    d=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    sources=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    for path in [TERRAIN,*SNOW]:
        f=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False);part=d[d.table.eq(Path(path).stem)]
        assert part.variable.is_unique and set(part.variable)==set(f)
        assert set(part.source_id)<=set(sources.source_id)
        for v in part.itertuples():assert abs(float(v.missing_share)-f[v.variable].eq('').mean())<=.00000051
    assert 'IGN_' not in '|'.join(h['source_id'] for h in m['header_checks'])
