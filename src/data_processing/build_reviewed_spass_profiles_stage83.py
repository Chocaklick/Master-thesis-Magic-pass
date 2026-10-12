"""Extend approved SPASS profiles to reviewed networks; old caches stay frozen."""
import os
for variable in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[variable]='1'
import argparse
import json
import math
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import netCDF4
netCDF4.set_chunk_cache(1048576,101,0.75)
import numpy as np
import pandas as pd
from src.data_processing import build_spass_preentry_profiles_stage77 as previous
from src.data_processing import compare_snow_multiwinter_stage76 as reader
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_collection.collect_oshd_multiwinter_stage76 import single_collector_lock
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_REVIEWED_SPASS_PREENTRY_STAGE83'
CACHE=ROOT/'data_interim/spass_reviewed_stage83'
OUTPUTS=['data_processed/spass_reviewed_windows_stage83.csv','data_processed/spass_reviewed_winter_stage83.csv',
    'data_processed/spass_reviewed_profiles_stage83.csv']
SUMMARY='reports/spass_reviewed_profiles_stage83_summary.json'
EXTRA={
    'parent_station_group_ids':('Stage79 parent identities retained without duplicating group winter means','identifiers'),
    'mapped_candidate_axis_length_m':('Full mapped candidate unique length, not official complete ski area','metres'),
    'measured_proxy_axis_length_m':('Individually reviewed eligible unique proxy length used for native SPASS weights','metres'),
    'measured_share_of_mapped_candidate_length':('Measured length/full mapped candidate length, ambiguous portions still recorded','fraction'),
}


def approved_windows():
    original=pd.read_csv(ROOT/'data_processed/winter_profile_approved_snow_windows_stage57.csv')
    bridge=pd.read_csv(ROOT/'data_processed/station_group_parent_bridge_stage79.csv')
    fields=['first_base_entry_month','winter_start_year','winter_start_date','winter_end_date','expected_days','spass_calendar_within_archive']
    linked=original.rename(columns={'station_group_id':'parent_station_group_id'}).merge(
        bridge[['parent_station_group_id','station_group_id']],on='parent_station_group_id',how='left',validate='many_to_one')
    if linked.station_group_id.isna().any():raise ValueError('Original calendar identity unmapped')
    rows=[]
    for (gid,year),part in linked.groupby(['station_group_id','winter_start_year'],sort=False):
        if any(part[c].nunique(dropna=False)!=1 for c in fields):raise ValueError('Connected parents have different own winter calendars')
        rows.append(dict(source_id=SOURCE,station_group_id=gid,parent_station_group_ids='|'.join(sorted(part.parent_station_group_id.unique())),
            **{c:part[c].iloc[0] for c in fields}))
    frame=pd.DataFrame(rows)
    if len(frame)!=345 or not frame.groupby('station_group_id').size().eq(5).all():raise ValueError('Five original windows per approved69groups required')
    return frame


def old_month(month,spass,inputs):
    for base in ['data_interim/snow_multiwinter_stage76/values','data_interim/spass_preentry_stage77/values']:
        path=ROOT/base/('spass_'+month+'.json')
        if not path.exists():continue
        m=json.loads(path.read_text(encoding='utf-8'));contract=m['contract'];npz=path.with_suffix('.npz')
        if contract['source_file']!=spass['spass_raw_file'] or contract['source_sha256']!=spass['spass_netcdf_sha256'] or m['source_unit']!='UNKNOWN':raise ValueError('Not unchanged original SPASS cache')
        if contract['variable']!='HSCLQMD' or contract['dimensions']!=['time','N','E'] or contract['producer_sha256']!=sha('src/data_processing/compare_snow_multiwinter_stage76.py'):raise ValueError('Original reader differs')
        if sha(npz.relative_to(ROOT))!=m['sha256']:raise ValueError('Old selected cells changed')
        inputs[path.relative_to(ROOT).as_posix()]=sha(path.relative_to(ROOT));inputs[npz.relative_to(ROOT).as_posix()]=m['sha256']
        with np.load(npz,allow_pickle=False) as z:values=z['values']
        return np.asarray(contract['indices'],dtype=int),dict(zip(m['observed_dates'],values))
    if month[:4] not in ['2022','2023']:raise ValueError('Previously available own-winter cache absent '+month)
    path=ROOT/'data_interim/native_snow_values_stage70/spass_pilot.json';npz=path.with_suffix('.npz')
    m=json.loads(path.read_text(encoding='utf-8'));contract=m['contract']
    if contract['source_file']!=spass['spass_raw_file'] or contract['source_sha256']!=spass['spass_netcdf_sha256'] or m['unit']!='UNKNOWN':raise ValueError('Original pilot source differs')
    if contract['producer_sha256']!=sha('src/data_processing/extract_native_snow_values_stage70.py') or sha(npz.relative_to(ROOT))!=m['cache_sha256']:raise ValueError('Frozen pilot cache differs')
    dates_path='data_processed/native_snow_date_pairs_stage69.csv';dates=pd.read_csv(ROOT/dates_path)
    dates=dates[dates.oshd_date_offset_days.eq(0)].sort_values('spass_time_index')
    if dates.spass_time_index.tolist()!=contract['times']:raise ValueError('Original pilot time coordinates misaligned')
    inputs[dates_path]=sha(dates_path);inputs[path.relative_to(ROOT).as_posix()]=sha(path.relative_to(ROOT));inputs[npz.relative_to(ROOT).as_posix()]=m['cache_sha256']
    with np.load(npz,allow_pickle=False) as z:values=z['values']
    return np.asarray(contract['indices'],dtype=int),{d:v for d,v in zip(dates.spass_civil_date,values) if d.startswith(month)}


def month_values(month,days,indices,spass,grid,inputs):
    old_indices,old_values=old_month(month,spass,inputs)
    oldloc={tuple(v):i for i,v in enumerate(old_indices)}
    reuse=[i for i,v in enumerate(indices) if tuple(v) in oldloc]
    missing=[i for i,v in enumerate(indices) if tuple(v) not in oldloc]
    if set(old_values)!=set(days):raise ValueError('Original whole-month source calendar differs, no fabricated missing dates')
    fresh={};sidecar=None
    if missing:
        oldcache=reader.CACHE
        try:
            reader.CACHE=CACHE
            fresh,meta=reader.read_selected(spass['spass_raw_file'],spass['spass_netcdf_sha256'],indices[missing],days,
                'HSCLQMD',('time','N','E'),('E','N'),grid,'spass_extra_'+month)
        finally:reader.CACHE=oldcache
        if set(fresh)!=set(days):raise ValueError('Requested in-archive source days differ')
        p=(CACHE/'values'/('spass_extra_'+month+'.npz')).relative_to(ROOT).as_posix()
        sidecar=Path(p).with_suffix('.json').as_posix();inputs[p]=meta['sha256'];inputs[sidecar]=sha(sidecar)
    values={}
    cols=[oldloc[tuple(indices[i])] for i in reuse]
    for d in days:
        v=np.empty(len(indices),dtype=float)
        v[reuse]=old_values[d][cols]
        if missing:v[missing]=fresh[d]
        values[d]=v
    return values,dict(month=month,reused_original_cell_count=len(reuse),new_original_cell_count=len(missing),extra_checkpoint=sidecar)


def register(frames):
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    if SOURCE not in set(master.source_id):
        r=dict(source_id=SOURCE,variable_name='reviewed_spass_five_own_preentry_winter_profile',
            variable_description='69retainedgroups, reviewed native unique piste weights, same five own strictly preentry winters, no missing fill',
            source_organisation='Thesis derived from WSL SLF SPASS and current reviewed OSM proxies',retrieval_date='2026-10-12',
            processed_file='|'.join(OUTPUTS),geographic_level='Station group, not municipality outcomes or independent daily units',
            temporal_resolution='Own December-April windows, equal observed days within winter and equal five winters',
            unit='metres under researcher-approved assumption; original UNKNOWN unchanged',license='Parent WSL Data Policy; OSM ODbL',
            transformation_applied='Reuse original selected-cell caches; read only added cells; no OSHD/calibration/imputation',
            quality_notes='Ambiguous axes unmeasured; incomplete calendars/geometry/source masks retained, all69groups kept',notes=SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([r]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    d=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);add=[];defs=previous.DEFS|EXTRA
    for path,f in zip(OUTPUTS,frames):
        for c in f:
            if ((d.table==Path(path).stem)&d.variable.eq(c)).any():continue
            desc,unit=defs[c]
            add.append(dict(variable=c,table=Path(path).stem,description=desc,unit=unit,data_type=str(f[c].dtype),
                geographic_level='Approved retained group, not a communal outcome',temporal_level='Five own strictly preentry winters/current geometry caveat',
                source_id=SOURCE,raw_or_derived='derived',formula=desc,causal_role='Qualified snow profile, not a fitted effect or automatic inclusion rule',
                missing_share=f'{f[c].isna().mean():.6f}',notes='Original SPASS metre assumption/UNKNOWN/no missing or OSHD fill'))
    if add:write_csv(pd.concat([d,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def run(no_register):
    paths=['src/data_processing/build_reviewed_spass_profiles_stage83.py','config/spass_preentry_decisions_stage77.json',
        'config/winter_profile_aggregation_decisions_stage45.json','data_processed/winter_profile_approved_snow_windows_stage57.csv',
        'data_processed/station_group_parent_bridge_stage79.csv','data_processed/winter_profile_metric_network_stage80.csv',
        'data_processed/spass_native_weights_stage80.csv','reports/snow_grid_metadata_compatibility_stage47.json',
        'reports/native_snow_weights_stage69_summary.json','src/data_processing/build_spass_preentry_profiles_stage77.py',
        'src/data_processing/compare_snow_multiwinter_stage76.py']
    contract={p:sha(p) for p in paths};inputs=dict(contract)
    decision=json.loads((ROOT/paths[1]).read_text(encoding='utf-8'))
    if decision['researcher_reply']!='A' or decision['missing_imputation'] or decision['source_spliced_or_calibrated']:raise ValueError('Approved unchanged SPASS-only policy required')
    spass=json.loads((ROOT/paths[7]).read_text(encoding='utf-8'))
    if sha(spass['spass_raw_file'])!=spass['spass_netcdf_sha256']:raise ValueError('Original snow source changed')
    inputs[spass['spass_raw_file']]=spass['spass_netcdf_sha256']
    grid=json.loads((ROOT/paths[8]).read_text(encoding='utf-8'))['original_grid_axes']['spass']
    windows=approved_windows();groups=pd.read_csv(ROOT/paths[5],float_precision='round_trip').set_index('station_group_id')
    weights=pd.read_csv(ROOT/paths[6],float_precision='round_trip')
    if not weights.spass_cell_in_grid.all():raise ValueError('New outside-array handling requires review')
    indices=weights[['spass_e_index','spass_n_index']].drop_duplicates().sort_values(['spass_e_index','spass_n_index']).to_numpy(dtype=int)
    locs={tuple(v):i for i,v in enumerate(indices)};gw={}
    for gid,p in weights.groupby('station_group_id'):
        gw[gid]=(np.array([locs[t] for t in p[['spass_e_index','spass_n_index']].itertuples(index=False,name=None)]),p.unique_proxy_axis_length_m.to_numpy())
    annual={};dailyproof={};monthproof=[]
    eligible=windows[windows.spass_calendar_within_archive&windows.station_group_id.isin(gw)]
    for year,target in eligible.groupby('winter_start_year',sort=True):
        year=int(year);days=[str(x.date()) for x in pd.date_range(f'{year}-12-01',f'{year+1}-04-30')]
        path=CACHE/f'daily_{year}.csv';side=path.with_suffix('.json');yearcontract=dict(inputs=contract,groups=sorted(target.station_group_id),days=days)
        if side.exists():
            m=json.loads(side.read_text(encoding='utf-8'))
            if m['contract']!=yearcontract or sha(path.relative_to(ROOT))!=m['sha256']:raise ValueError('Frozen annual profile cache differs')
            daily=pd.read_csv(path,float_precision='round_trip');inputs.update(m['source_input_sha256']);monthproof.extend(m['month_reuse'])
            for p,h in m['source_input_sha256'].items():
                if sha(p)!=h:raise ValueError('Reused annual cache source differs')
        else:
            if path.exists():raise ValueError('Uncheckpointed annual output retained')
            values={};checkpoints=[];source_inputs={}
            for month in sorted({d[:7] for d in days}):
                v,proof=month_values(month,[d for d in days if d.startswith(month)],indices,spass,grid,source_inputs)
                values.update(v);checkpoints.append(proof)
            rows=[]
            for gid in sorted(target.station_group_id):
                loc,lengths=gw[gid]
                for day in days:rows.append(dict(station_group_id=gid,civil_date=day,**previous.daily_metric(values[day][loc],lengths)))
            daily=pd.DataFrame(rows);write_csv(daily,path)
            m=dict(contract=yearcontract,sha256=sha(path.relative_to(ROOT)),source_input_sha256=source_inputs,month_reuse=checkpoints)
            side.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');inputs.update(source_inputs);monthproof.extend(checkpoints)
        annual[year]=daily;dailyproof[str(year)]=dict(path=path.relative_to(ROOT).as_posix(),sha256=m['sha256'],metadata=side.relative_to(ROOT).as_posix(),metadata_sha256=sha(side.relative_to(ROOT)))
        (CACHE/'progress.json').write_text(json.dumps(dict(completed_winter_start_years=sorted(annual),input_sha256=contract),indent=2)+'\n',encoding='utf-8')
        print('Reviewed SPASS winter',year,len(daily),'group-day rows',flush=True)
    flags=dict(source_id=SOURCE,parent_source_id=decision['source_id'],group_retained=True,spass_original_unit='UNKNOWN',spass_metres_assumed=True,
        source_spliced_or_calibrated=False,current_proxy_not_verified_preentry=True)
    records=[]
    for win in windows.to_dict('records'):
        gid=win['station_group_id'];g=groups.loc[gid]
        r=win|flags|dict(station_group_name=g.display_scope_name,geometry_available=gid in gw,geometry_status=g.metric_status,
            mapped_candidate_axis_length_m=g.full_unique_candidate_axis_length_m,measured_proxy_axis_length_m=g.measured_unique_proxy_axis_length_m,
            measured_share_of_mapped_candidate_length=g.measured_share_of_mapped_candidate_length,
            observed_days=np.nan,missing_days=np.nan,spass_winter_mean_m=np.nan,min_observed_length_share=np.nan,mean_observed_length_share=np.nan,
            negative_value_days=np.nan,all_requested_days_observed=False,all_axis_length_observed=False)
        if gid not in gw:r['status']='missing_geometry'
        elif not win['spass_calendar_within_archive']:r.update(status='outside_spass_calendar',observed_days=0,missing_days=win['expected_days'])
        else:
            r.update(previous.winter_metric(annual[win['winter_start_year']].loc[lambda d:d.station_group_id.eq(gid)],win['expected_days']))
            r['status']='winter_observed_full_coverage' if r['all_axis_length_observed'] and r['all_requested_days_observed'] else 'winter_observed_partial_coverage' if r['observed_days'] else 'no_observed_spass_length'
        records.append(r)
    winter=pd.DataFrame(records);profiles=[]
    for gid,w in winter.groupby('station_group_id',sort=False):
        g=groups.loc[gid];r=flags|dict(station_group_id=gid,station_group_name=g.display_scope_name,parent_station_group_ids=w.parent_station_group_ids.iloc[0],
            first_base_entry_month=w.first_base_entry_month.iloc[0],geometry_available=gid in gw,geometry_status=g.metric_status,
            mapped_candidate_axis_length_m=g.full_unique_candidate_axis_length_m,measured_proxy_axis_length_m=g.measured_unique_proxy_axis_length_m,
            measured_share_of_mapped_candidate_length=g.measured_share_of_mapped_candidate_length,**previous.five_metric(w),
            all_requested_days_observed=bool(w.all_requested_days_observed.all()),all_axis_length_observed=bool(w.all_axis_length_observed.all()),
            min_observed_length_share=float(w.min_observed_length_share.min()))
        r['status']='missing_geometry' if gid not in gw else 'incomplete_five_winters' if r['observed_winter_count']<5 else 'five_winters_full_coverage' if r['all_requested_days_observed'] and r['all_axis_length_observed'] else 'five_winters_partial_coverage'
        profiles.append(r)
    frames=[windows,winter,pd.DataFrame(profiles)]
    state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,daily_checkpoints=dailyproof,month_cache_reuse=monthproof,
        retained_groups=len(groups),winter_rows=len(winter),observed_winter_means=int(winter.spass_winter_mean_m.notna().sum()),
        computable_five_winter_profiles=int(frames[2].spass_five_preentry_winters_mean_m.notna().sum()),profile_status_counts=frames[2].status.value_counts().to_dict(),
        no_external_request=True,no_osdh_or_missing_fill=True,no_old_output_change=True,no_clustering_or_did=True)
    path=ROOT/SUMMARY
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old['input_sha256']!=inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):raise ValueError('Frozen final profiles differ')
    else:
        for p,f in zip(OUTPUTS,frames):write_csv(f,ROOT/p)
        state['output_sha256']={p:sha(p) for p in OUTPUTS};path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not no_register:register(frames)
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','daily_checkpoints','month_cache_reuse']},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--no-register',action='store_true');args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True)
    with single_collector_lock(CACHE):run(args.no_register)
