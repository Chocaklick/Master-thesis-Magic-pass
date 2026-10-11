"""Native SPASS support for all69groups, one fixed diagnostic day, no profiles.

This uses April1 2023 within the previously approved pilot only to inspect
observed source coverage. It is not a preentry feature, winter mean or evidence
that the same masks hold on every day of the own five preentry winters.
"""
import json
import math
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from netCDF4 import Dataset,num2date
from shapely import wkt
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link
from src.data_processing.prepare_native_snow_weights_stage69 import native_grid,digest as sha
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_REVIEWED_SPASS_SUPPORT_STAGE80'
DAY='2023-04-01'
OUTPUTS=['data_processed/spass_native_weights_stage80.csv','data_processed/spass_coverage_check_stage80.csv',
         'data_processed/spass_coverage_source_cells_stage80.csv']
SUMMARY='reports/reviewed_spass_support_stage80_summary.json'
DEFS={
    'source_id':('Registered source of support or original selected cells','identifier'),
    'parent_source_id':('Original SPASS source, no OSHD values','identifier'),
    'station_group_id':('Approved derived group, original lineage retained','identifier'),
    'spass_e_index':('Literal zero-based original east-axis index; outside indices flagged','index'),
    'spass_n_index':('Literal zero-based original ascending north-axis index; no resampling','index'),
    'spass_cell_in_grid':('Index inside original array; not finite snow value proof','boolean'),
    'spass_cell_centre_east_2056':('Original native coordinate when inside source grid','metres'),
    'spass_cell_centre_north_2056':('Original native coordinate when inside source grid','metres'),
    'unique_proxy_axis_length_m':('Exact measured unique proxy length crossing the native SPASS cell, excluding unresolved axes only from measurement','metres'),
    'station_group_name':('Derived readable current scope; original names preserved in Stage79','text'),
    'group_retained':('True for all69groups, including missing geometry or source coverage','boolean'),
    'geometry_available':('Measured qualified current axes available, not full real-domain completeness','boolean'),
    'full_candidate_axis_length_m':('Full original mapped candidate union as coverage reference, not official piste length','metres'),
    'measured_proxy_axis_length_m':('Measured current proxy union after individual ambiguity handling','metres'),
    'native_grid_axis_length_m':('Measured length inside original array extent; finite masks still separate','metres'),
    'native_grid_axis_share':('Inside-array length/measured proxy length; not actual valid weather values','fraction'),
    'diagnostic_civil_date':('Fixed2023-04-01 within approved pilot, not a preentry-profile choice','date'),
    'diagnostic_observed_length_m':('Measured length with finite original values on this date only','metres'),
    'diagnostic_observed_proxy_length_share':('One-day finite length/measured proxy length, not guaranteed five-winter coverage','fraction'),
    'diagnostic_observed_candidate_length_share':('One-day finite length/full mapped candidate length, ambiguity and source gaps retained','fraction'),
    'status':('Missing geometry, partial one-day coverage or all observed on diagnostic day; no group selection','category'),
    'not_preentry_profile':('True: one-day coverage audit is never used as a preentry snow predictor','boolean'),
    'original_time_index':('Literal SPASS time-axis index on fixed diagnostic date','index'),
    'original_timestamp':('Original decoded source time, no time convention invented','timestamp'),
    'original_time_coordinate_value':('Original numeric source time coordinate','source time units'),
    'original_time_units':('Literal time.units string from original source','text'),
    'original_variable_unit':('Original variable units declaration, UNKNOWN preserved','text'),
    'original_height_value':('Selected original source value, unconverted; NaN remains missing and zero stays observed','original source unit; metres only under approved assumption'),
    'original_value_observed':('Finite original masked value, including real zero','boolean'),
}


def register(frames):
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    if SOURCE not in set(master.source_id):
        record=dict(source_id=SOURCE,variable_name='reviewed_native_spass_support_and_one_day_coverage',
            variable_description='69retainedgroups and native exact measured-network weights; April1 2023 raw-mask diagnostic only',
            source_organisation='Thesis derived from original SLF SPASS and documented OSM proxies',retrieval_date='2026-10-12',
            processed_file='|'.join(OUTPUTS),geographic_level='Group/native source cell, not communal observations',
            temporal_resolution='Current proxy support; fixed diagnostic date within approved pilot, not preentry profile',
            unit='Original UNKNOWN; researcher-approved metre assumption not a certified provider declaration',
            license='Parent WSL Data Policy; geometry OSM ODbL',
            transformation_applied='Exact native-cell length allocation, source mask preserved, no snow interpolation/unit change or OSHD use',
            quality_notes='All69groups retained; one day does not certify five-winter coverage; no new winter/profile means',notes=SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);add=[]
    for path,frame in zip(OUTPUTS,frames):
        for c in frame:
            if ((dictionary.table==Path(path).stem)&dictionary.variable.eq(c)).any():continue
            description,unit=DEFS[c]
            add.append(dict(variable=c,table=Path(path).stem,description=description,unit=unit,data_type=str(frame[c].dtype),
                geographic_level='Retained group or original native cell',temporal_level='Current support/fixed one-day mask diagnostic',source_id=SOURCE,
                raw_or_derived='exact support or selected original raw value',formula='prepare_reviewed_spass_weights_stage80.py; exact lengths and original masks',
                causal_role='Coverage only; not a preentry feature, final snow profile or causal estimate',
                missing_share=f'{frame[c].isna().mean():.6f}',notes='Five own preentry winters and original units remain unchanged'))
    if add:write_csv(pd.concat([dictionary,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    paths=['src/data_processing/prepare_reviewed_spass_weights_stage80.py',
        'data_interim/winter_profile_metric_network_stage80.json','data_processed/winter_profile_metric_network_stage80.csv',
        'reports/snow_grid_metadata_compatibility_stage47.json','reports/native_snow_weights_stage69_summary.json',
        'src/data_processing/terrain_cell_weights_stage61.py']
    inputs={p:sha(p) for p in paths};sp=json.loads((ROOT/paths[3]).read_text(encoding='utf-8'))
    if sha(sp['spass_raw_file'])!=sp['spass_netcdf_sha256']:raise ValueError('Original SPASS changed')
    inputs[sp['spass_raw_file']]=sp['spass_netcdf_sha256']
    nets=json.loads((ROOT/paths[1]).read_text(encoding='utf-8'));groups=pd.read_csv(ROOT/paths[2],float_precision='round_trip').set_index('station_group_id')
    parent=json.loads((ROOT/paths[4]).read_text(encoding='utf-8'))
    with ascii_link(ROOT/sp['spass_raw_file']) as link,Dataset(link) as ds:
        east,north=np.asarray(ds.variables['E'][:],dtype=float),np.asarray(ds.variables['N'][:],dtype=float)
        grid=native_grid(east,north)
        if grid!=parent['original_grid_axes']['spass']:raise ValueError('Native original grid differs')
        time=ds.variables['time'];raw=np.asarray(time[:],dtype=float);decoded=num2date(raw,time.units,calendar=getattr(time,'calendar','standard'))
        found=[i for i,t in enumerate(decoded) if str(t)[:10]==DAY]
        if len(found)!=1:raise ValueError('Require exactly one original diagnostic date')
        ti=found[0];v=ds.variables['HSCLQMD'];unit=getattr(v,'units',getattr(v,'unit','UNKNOWN'))
        if unit!='UNKNOWN' or v.dimensions!=('time','N','E'):raise ValueError('Source units/dimensions need review')
        field=np.asarray(np.ma.filled(v[ti,:,:],np.nan),dtype=float)
        time_record=dict(original_time_index=ti,original_timestamp=str(decoded[ti]),
            original_time_coordinate_value=float(raw[ti]),original_time_units=time.units,original_variable_unit=unit)
    weights=[];coverage=[];selected={}
    for n in nets:
        gid=n['station_group_id'];g=groups.loc[gid];available=n['measured_unique_proxy_axis_wkt'] is not None
        base=dict(source_id=SOURCE,station_group_id=gid,station_group_name=g.display_scope_name,group_retained=True,
            geometry_available=available,full_candidate_axis_length_m=g.full_unique_candidate_axis_length_m,
            measured_proxy_axis_length_m=g.measured_unique_proxy_axis_length_m,diagnostic_civil_date=DAY,not_preentry_profile=True)
        if not available:
            coverage.append(base|dict(status='missing_geometry_not_zero'));continue
        geometry=wkt.loads(n['measured_unique_proxy_axis_wkt'])
        lengths=cell_lengths(geometry,grid['left'],grid['top'],grid['step'],grid['step']);inside=[];observed=[]
        for (row,col),length in lengths.items():
            ni=grid['north_count']-1-row if grid['north_ascending'] else row
            valid=0<=col<grid['east_count'] and 0<=ni<grid['north_count']
            value=float(field[ni,col]) if valid else np.nan
            weights.append(dict(source_id=SOURCE,station_group_id=gid,spass_e_index=col,spass_n_index=ni,
                spass_cell_in_grid=valid,spass_cell_centre_east_2056=float(east[col]) if valid else np.nan,
                spass_cell_centre_north_2056=float(north[ni]) if valid else np.nan,unique_proxy_axis_length_m=length))
            if valid:
                inside.append(length)
                selected[(col,ni)]=dict(source_id=sp['spass_source_id'],parent_source_id=sp['spass_source_id'],
                    spass_e_index=col,spass_n_index=ni,diagnostic_civil_date=DAY,**time_record,
                    original_height_value=value,original_value_observed=bool(np.isfinite(value)),not_preentry_profile=True)
            if np.isfinite(value):observed.append(length)
        obs=math.fsum(observed);extent=math.fsum(inside)
        coverage.append(base|dict(native_grid_axis_length_m=extent,native_grid_axis_share=extent/geometry.length,
            diagnostic_observed_length_m=obs,diagnostic_observed_proxy_length_share=obs/geometry.length,
            diagnostic_observed_candidate_length_share=obs/g.full_unique_candidate_axis_length_m,
            status='all_source_values_observed_on_diagnostic_day' if len(observed)==len(lengths) else 'partial_source_mask_on_diagnostic_day'))
    frames=[pd.DataFrame(weights),pd.DataFrame(coverage),pd.DataFrame(selected.values())]
    target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256']!=inputs or any(sha(p)!=h for p,h in state['output_sha256'].items()):raise ValueError('Frozen SPASS support differs')
    else:
        for p,f in zip(OUTPUTS,frames):write_csv(f,ROOT/p)
        state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,output_sha256={p:sha(p) for p in OUTPUTS},
            all_group_count=len(frames[1]),native_weight_row_count=len(frames[0]),original_source_cell_count=len(frames[2]),
            diagnostic_date=DAY,groups_with_one_day_partial_mask=frames[1].loc[frames[1].status.eq('partial_source_mask_on_diagnostic_day'),
                ['station_group_id','diagnostic_observed_proxy_length_share']].to_dict('records'),
            no_preentry_or_winter_profile_computed=True,no_interpolation_or_osdh_values=True,no_original_unit_change=True)
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    register(frames)
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256']},ensure_ascii=False))


if __name__=='__main__':main()
