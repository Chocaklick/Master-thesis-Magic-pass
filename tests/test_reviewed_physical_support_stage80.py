"""Native support is not a winter mean; groups/old caches remain present."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from shapely import wkt
from shapely.geometry import box
from shapely.ops import unary_union
from netCDF4 import Dataset
from src.data_processing.prepare_reviewed_spass_weights_stage80 import ROOT,OUTPUTS,DAY
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link


def read(path):return pd.read_csv(ROOT/path,float_precision='round_trip')


def test_all_groups_and_missing_geometry_not_zero():
    c=read(OUTPUTS[1]); assert len(c)==69 and c.station_group_id.is_unique and c.group_retained.all()
    assert c.not_preentry_profile.all() and set(c.diagnostic_civil_date)=={DAY}
    missing=c[~c.geometry_available]; assert len(missing)==2
    assert missing.diagnostic_observed_length_m.isna().all()
    assert missing.status.eq('missing_geometry_not_zero').all()
    assert c.geometry_available.sum()==67


def test_exact_native_snow_weights_for_all_measured_networks():
    parent=json.loads((ROOT/'reports/native_snow_weights_stage69_summary.json').read_text())
    grid=parent['original_grid_axes']['spass']; weights=read(OUTPUTS[0]); assert len(weights)==639
    networks=json.loads((ROOT/'data_interim/winter_profile_metric_network_stage80.json').read_text())
    assert not weights.duplicated(['station_group_id','spass_e_index','spass_n_index']).any()
    for n in networks:
        if n['measured_unique_proxy_axis_wkt'] is None:continue
        g=wkt.loads(n['measured_unique_proxy_axis_wkt']); part=weights[weights.station_group_id.eq(n['station_group_id'])]
        expected=cell_lengths(g,grid['left'],grid['top'],grid['step'],grid['step'])
        actual={(grid['north_count']-1-int(r.spass_n_index),int(r.spass_e_index)):r.unique_proxy_axis_length_m for r in part.itertuples()}
        assert actual.keys()==expected.keys()
        assert sum(actual.values())==pytest.approx(g.length,abs=1e-7)
        assert all(actual[k]==expected[k] for k in actual)


def test_saved_original_source_values_masks_and_zeros():
    p=json.loads((ROOT/'reports/snow_grid_metadata_compatibility_stage47.json').read_text())
    f=read(OUTPUTS[2]); assert len(f)==639 and f.not_preentry_profile.all() and f.original_variable_unit.eq('UNKNOWN').all()
    with ascii_link(ROOT/p['spass_raw_file']) as link,Dataset(link) as ds:
        assert f.original_time_index.nunique()==1
        ti=int(f.original_time_index.iloc[0]); field=np.asarray(np.ma.filled(ds.variables['HSCLQMD'][ti,:,:],np.nan))
        for r in f.itertuples():
            value=field[int(r.spass_n_index),int(r.spass_e_index)]
            if np.isfinite(value):assert r.original_value_observed and r.original_height_value==value
            else:assert not r.original_value_observed and pd.isna(r.original_height_value)
    assert f.original_height_value.eq(0).any(), 'Real zero must remain observed'


def test_known_partial_mask_does_not_certify_calendar_coverage():
    f=read(OUTPUTS[1]); parts=f[f.status.eq('partial_source_mask_on_diagnostic_day')]
    assert set(parts.station_group_id)=={'MP_GROUP_RESORT__la_dole_jura_sur_leman','MP_GROUP_RESORT__melchsee_frutt','MP_GROUP_RESORT__vallee_de_joux'}
    dole=parts.set_index('station_group_id').loc['MP_GROUP_RESORT__la_dole_jura_sur_leman']
    assert dole.diagnostic_observed_proxy_length_share==pytest.approx(0.658248069972649)
    assert dole.native_grid_axis_share==pytest.approx(1)
    s=json.loads((ROOT/'reports/reviewed_spass_support_stage80_summary.json').read_text())
    assert s['no_preentry_or_winter_profile_computed'] and s['no_original_unit_change']


def test_terrain_catalogue_all_groups_native2m_and_no_raster_claim():
    c=read('data_processed/terrain_reviewed_catalogue_coverage_stage80.csv')
    a=read('data_processed/terrain_reviewed_asset_inventory_stage80.csv')
    assert len(c)==69 and c.station_group_id.is_unique and c.group_retained.all()
    assert not c.actual_raster_coverage_verified.any() and not c.actual_nodata_or_neighbourhood_coverage_known.any()
    assert a.asset_grid_resolution_m.eq(2).all() and a.asset_horizontal_epsg.eq(2056).all()
    chosen=a[a.latest_reference_for_native_tile]
    assert not chosen.duplicated(['station_group_id','native_tile_key']).any()
    assert chosen.asset_url.nunique()==1274
    assert c.catalogue_status.eq('complete_new_original_pages').sum()==27
    assert c.catalogue_status.eq('complete_archived_catalogue_reused').sum()==40
    nets=json.loads((ROOT/'data_interim/winter_profile_metric_network_stage80.json').read_text())
    for n in nets:
        if n['measured_unique_proxy_axis_wkt'] is None:continue
        keys=chosen[chosen.station_group_id.eq(n['station_group_id'])].native_tile_key
        tiles=[]
        for key in keys:
            e,nn=(int(x)*1000 for x in key.split('-'));tiles.append(box(e,nn,e+1000,nn+1000))
        geom=wkt.loads(n['measured_unique_proxy_axis_wkt'])
        length=geom.intersection(unary_union(tiles)).length
        row=c[c.station_group_id.eq(n['station_group_id'])].iloc[0]
        assert row.catalogue_tile_footprint_axis_length_m==length
    assert c.set_index('station_group_id').loc['MP_GROUP_RESORT__la_dole_jura_sur_leman','catalogue_tile_footprint_axis_share']==pytest.approx(0.6582480699726465)


def test_actual_metadata_events_logged_once():
    es=json.loads((ROOT/'data_interim/terrain_catalogue_events_stage80.json').read_text())
    log=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    good=[e for e in es if e['status']=='downloaded']; assert len(good)==35
    assert len({e['source_id'] for e in good})==35
    for e in good:
        matched=log[log.timestamp.eq(e['timestamp'])&log.source_id.eq(e['source_id'])]
        assert len(matched)==1 and matched.checksum.iloc[0]==e['checksum']
        assert sha(e['raw_file'])==e['checksum']


def test_cancelled_ign_and_current_cache_not_recollected():
    d=json.loads((ROOT/'config/terrain_french_complement_decision_stage80.json').read_text())
    assert d['french_terrain_research_stopped'] and d['french_source_complement']=='none'
    assert d['original_transborder_axes_and_previous_results_retained']
    s=json.loads((ROOT/'reports/reviewed_geometry_followup_stage80_summary.json').read_text())
    assert s['french_complement_cancelled'] and s['no_new_raster_download']
    assert s['current_verified_cached_asset_count']+s['current_missing_latest_asset_count']==1274
    assert s['current_verified_cached_asset_count']>s.get('already_cached_latest_asset_count',45)
    assert not any(x['source_id'].startswith('IGN') for x in s['cached_assets'])
    sources=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False).set_index('source_id')
    assert len(s['stopped_ign_source_outcomes'])==11
    for o in s['stopped_ign_source_outcomes']:assert o['source_id'] in sources.index
    for sid in ['IGN_LIDAR_CONTENT_202503_STAGE80','IGN_LIDAR_DELIVERY_202409_STAGE80']:
        assert 'NOT a consulted PDF' in sources.loc[sid,'notes']


def test_registered_support_fields_and_exact_missing_shares():
    d=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    for p in [*OUTPUTS,'data_processed/terrain_reviewed_asset_inventory_stage80.csv','data_processed/terrain_reviewed_catalogue_coverage_stage80.csv']:
        f=pd.read_csv(ROOT/p,dtype=str,keep_default_na=False); part=d[d.table.eq(Path(p).stem)]
        assert part.variable.is_unique and set(part.variable)==set(f)
        for r in part.itertuples():assert abs(float(r.missing_share)-f[r.variable].eq('').mean())<=0.00000051
