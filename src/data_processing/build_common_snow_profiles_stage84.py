"""Ten common observed winters, same native piste weights, preentry profiles intact."""
import json
import math
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
from src.data_processing import build_reviewed_spass_profiles_stage83 as reader
from src.data_processing.build_spass_preentry_profiles_stage77 import daily_metric,winter_metric,DEFS as PARENT_DEFS
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_COMMON_SNOW_DESCRIPTIVE_STAGE84'
CONFIG='config/descriptive_similarity_scope_stage84.json'
OUTPUTS=['data_processed/common_snow_winter_stage84.csv','data_processed/common_snow_profiles_stage84.csv',
    'data_processed/common_snow_reassessment_stage84.csv']
SUMMARY='reports/common_snow_profiles_stage84_summary.json'
CACHE=ROOT/'data_interim/common_snow_stage84'
DEFS=dict(PARENT_DEFS)|reader.EXTRA|{
    'winter_label':('Civil winter December start year to following April','text'),
    'not_preentry_feature':('True: common descriptive period may contain postentry years; never substituted into causal/predictive preentry profiles','boolean'),
    'membership_independent_window':('True: all retained groups use same ten civil winters independent of adhesion','boolean'),
    'requested_winter_count':('Exactly ten common winters 2013/14 to2022/23, not own preentry windows','count'),
    'observed_winter_count':('Common winter means actually observed, not independent station observations','count'),
    'common_ten_winter_mean_m':('Arithmetic mean of all ten observed winter means, NA if any whole winter absent','metres, assumed'),
    'common_period_start_date':('Fixed2013-12-01 for every group','date'),
    'common_period_end_date':('Fixed2023-04-30 for every group','date'),
    'expected_total_days':('1512 actual December-April calendar days across ten winters, leap days retained','days'),
    'missing_winter_start_years':('Common winter years whose entire mean remains missing, no fallback','years'),
    'previous_preentry_status':('Frozen Stage83 profile availability, not a restriction of the common period','category'),
    'previous_observed_winter_count':('Original own five-winter count, preserved not overwritten','count'),
    'common_observed_winter_count':('Actually observed common winter count','count'),
    'common_period_snow_mean_available':('Finite ten-common-winter mean, not automatic clustering acceptance','boolean'),
    'reassessment_status':('Recomputed coverage reason; no automatic sample filter','category'),
}


def register(frames):
    m=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    if SOURCE not in set(m.source_id):
        r=dict(source_id=SOURCE,variable_name='common_ten_winter_descriptive_snow_profiles',
            variable_description='All retained groups use winters2013/14–2022/23; same native piste weights, equal winters, no preentry substitution',
            source_organisation='Thesis derived from original WSL SLF SPASS and reviewed current OSM geometries',
            retrieval_date='2026-10-12',processed_file='|'.join(OUTPUTS),geographic_level='Retained connected station group, not communal nights or independent days',
            temporal_start='2013-12-01',temporal_end='2023-04-30',temporal_resolution='Ten common December-April winters',
            unit='m under approved assumption, original UNKNOWN unchanged',license='Parent WSL Data Policy; OSM ODbL',
            transformation_applied='Original selected cells/caches reused; daily exact spatial lengths, observed-day winter mean then equal ten winter means',
            quality_notes='Descriptive climate similarity, may include postentry observations; no missing fill, OSHD, causal fit or automatic exclusion',
            notes=SUMMARY+'; preserve Stage77 andStage83 own-preentry profiles')
        write_csv(pd.concat([m,pd.DataFrame([r]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    d=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);add=[]
    for path,f in zip(OUTPUTS,frames):
        for c in f:
            if ((d.table==Path(path).stem)&d.variable.eq(c)).any():continue
            desc,unit=DEFS[c]
            add.append(dict(variable=c,table=Path(path).stem,description=desc,unit=unit,data_type=str(f[c].dtype),
                geographic_level='Connected station group, not independent grid/date observations',temporal_level='Common descriptive decade, not own preentry period',
                source_id=SOURCE,raw_or_derived='derived',formula=desc,causal_role='Descriptive similarity only; not a preentry covariate or predicted effect',
                missing_share=f'{f[c].isna().mean():.6f}',notes=CONFIG+'; unitsUNKNOWN preserved/no imputation/no membership selection'))
    if add:write_csv(pd.concat([d,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    CACHE.mkdir(parents=True,exist_ok=True)
    paths=[CONFIG,'src/data_processing/build_common_snow_profiles_stage84.py',
        'data_processed/spass_native_weights_stage80.csv','data_processed/winter_profile_metric_network_stage80.csv',
        'data_processed/spass_reviewed_profiles_stage83.csv','reports/spass_reviewed_profiles_stage83_summary.json',
        'reports/snow_grid_metadata_compatibility_stage47.json','reports/native_snow_weights_stage69_summary.json',
        'src/data_processing/build_reviewed_spass_profiles_stage83.py','src/data_processing/build_spass_preentry_profiles_stage77.py']
    contract={p:sha(p) for p in paths};inputs=dict(contract)
    decision=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'));years=decision['common_winter_start_years']
    if years!=list(range(2013,2023)) or decision['winter_months']!=[12,1,2,3,4]:raise ValueError('Exact common decade required')
    spass=json.loads((ROOT/paths[6]).read_text(encoding='utf-8'))
    if sha(spass['spass_raw_file'])!=spass['spass_netcdf_sha256']:raise ValueError('Original snow changed')
    inputs[spass['spass_raw_file']]=spass['spass_netcdf_sha256']
    grid=json.loads((ROOT/paths[7]).read_text(encoding='utf-8'))['original_grid_axes']['spass']
    groups=pd.read_csv(ROOT/paths[3],float_precision='round_trip').set_index('station_group_id')
    weights=pd.read_csv(ROOT/paths[2],float_precision='round_trip')
    if not weights.spass_cell_in_grid.all():raise ValueError('Outside-grid handling needs review')
    indices=weights[['spass_e_index','spass_n_index']].drop_duplicates().sort_values(['spass_e_index','spass_n_index']).to_numpy(dtype=int)
    locs={tuple(v):i for i,v in enumerate(indices)};gw={}
    for gid,p in weights.groupby('station_group_id'):
        gw[gid]=(np.array([locs[t] for t in p[['spass_e_index','spass_n_index']].itertuples(index=False,name=None)]),p.unique_proxy_axis_length_m.to_numpy())
    flags=dict(source_id=SOURCE,parent_source_id=spass['spass_source_id'],group_retained=True,
        spass_original_unit='UNKNOWN',spass_metres_assumed=True,source_spliced_or_calibrated=False,
        current_proxy_not_verified_preentry=True,not_preentry_feature=True,membership_independent_window=True)
    records=[];dailyproof={}
    for year in years:
        dates=[str(t.date()) for t in pd.date_range(f'{year}-12-01',f'{year+1}-04-30')]
        path=CACHE/f'daily_{year}.csv';sidecar=path.with_suffix('.json');yc=dict(inputs=contract,groups=sorted(gw),dates=dates)
        if sidecar.exists():
            m=json.loads(sidecar.read_text(encoding='utf-8'))
            if m['contract']!=yc or sha(path.relative_to(ROOT))!=m['sha256']:raise ValueError('Frozen common cache differs')
            daily=pd.read_csv(path,float_precision='round_trip');source_inputs=m['source_input_sha256']
            for p,h in source_inputs.items():
                if sha(p)!=h:raise ValueError('Original reused value cache differs')
        else:
            if path.exists():raise ValueError('Uncheckpointed common cache retained')
            values={};source_inputs={}
            for month in sorted({d[:7] for d in dates}):
                extra=reader.CACHE/'values'/('spass_extra_'+month+'.json')
                if not extra.exists():raise ValueError('Existing Stage83 month must be reused, not rebuilt')
                value,_=reader.month_values(month,[d for d in dates if d.startswith(month)],indices,spass,grid,source_inputs)
                values.update(value)
            rows=[]
            for gid in sorted(gw):
                loc,length=gw[gid]
                for day in dates:rows.append(dict(station_group_id=gid,civil_date=day,**daily_metric(values[day][loc],length)))
            daily=pd.DataFrame(rows);write_csv(daily,path)
            m=dict(contract=yc,sha256=sha(path.relative_to(ROOT)),source_input_sha256=source_inputs)
            sidecar.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        inputs.update(source_inputs);dailyproof[str(year)]=dict(path=path.relative_to(ROOT).as_posix(),sha256=m['sha256'],
            metadata=sidecar.relative_to(ROOT).as_posix(),metadata_sha256=sha(sidecar.relative_to(ROOT)))
        for gid,g in groups.iterrows():
            r=flags|dict(station_group_id=gid,station_group_name=g.display_scope_name,geometry_available=gid in gw,geometry_status=g.metric_status,
                mapped_candidate_axis_length_m=g.full_unique_candidate_axis_length_m,measured_proxy_axis_length_m=g.measured_unique_proxy_axis_length_m,
                measured_share_of_mapped_candidate_length=g.measured_share_of_mapped_candidate_length,
                winter_start_year=year,winter_label=f'{year}/{year+1}',winter_start_date=dates[0],winter_end_date=dates[-1],expected_days=len(dates),
                observed_days=np.nan,missing_days=np.nan,spass_winter_mean_m=np.nan,min_observed_length_share=np.nan,mean_observed_length_share=np.nan,
                negative_value_days=np.nan,all_requested_days_observed=False,all_axis_length_observed=False)
            if gid not in gw:r['status']='missing_geometry'
            else:
                r.update(winter_metric(daily[daily.station_group_id.eq(gid)],len(dates)))
                r['status']='winter_observed_full_coverage' if r['all_axis_length_observed'] and r['all_requested_days_observed'] else 'winter_observed_partial_coverage' if r['observed_days'] else 'no_observed_spass_length'
            records.append(r)
        (CACHE/'progress.json').write_text(json.dumps(dict(completed_winter_start_years=list(dailyproof),input_sha256=contract),indent=2)+'\n',encoding='utf-8')
        print('Common winter',year,len(daily),'group-day rows',flush=True)
    winter=pd.DataFrame(records);profiles=[]
    for gid,w in winter.groupby('station_group_id',sort=False):
        g=groups.loc[gid];means=w.spass_winter_mean_m.to_numpy(dtype=float);good=np.isfinite(means)
        if len(w)!=10 or not w.winter_start_year.sort_values().tolist()==years:raise ValueError('All ten winters required')
        r=flags|dict(station_group_id=gid,station_group_name=g.display_scope_name,geometry_available=gid in gw,geometry_status=g.metric_status,
            mapped_candidate_axis_length_m=g.full_unique_candidate_axis_length_m,measured_proxy_axis_length_m=g.measured_unique_proxy_axis_length_m,
            measured_share_of_mapped_candidate_length=g.measured_share_of_mapped_candidate_length,
            requested_winter_count=10,observed_winter_count=int(good.sum()),common_ten_winter_mean_m=math.fsum(means)/10 if good.all() else np.nan,
            missing_winter_start_years='|'.join(str(y) for y,v in zip(w.winter_start_year,good) if not v),
            common_period_start_date='2013-12-01',common_period_end_date='2023-04-30',expected_total_days=int(w.expected_days.sum()),
            all_requested_days_observed=bool(w.all_requested_days_observed.all()),all_axis_length_observed=bool(w.all_axis_length_observed.all()),
            min_observed_length_share=float(w.min_observed_length_share.min()))
        r['status']='missing_geometry' if gid not in gw else 'common_ten_winters_incomplete' if not good.all() else 'common_ten_winters_full_coverage' if r['all_axis_length_observed'] and r['all_requested_days_observed'] else 'common_ten_winters_partial_coverage'
        profiles.append(r)
    profile=pd.DataFrame(profiles);old=pd.read_csv(ROOT/paths[4])
    previous=old[old.status.eq('incomplete_five_winters')][['station_group_id','station_group_name','status','observed_winter_count']].rename(
        columns={'status':'previous_preentry_status','observed_winter_count':'previous_observed_winter_count'})
    assessment=previous.merge(profile[['station_group_id','observed_winter_count','common_ten_winter_mean_m','min_observed_length_share',
        'all_requested_days_observed','all_axis_length_observed']],on='station_group_id',validate='one_to_one').rename(columns={'observed_winter_count':'common_observed_winter_count'})
    if len(assessment)!=13:raise ValueError('All thirteen previous incomplete groups must be reassessed')
    assessment['source_id']=SOURCE;assessment['common_period_snow_mean_available']=assessment.common_ten_winter_mean_m.notna()
    assessment['reassessment_status']=np.where(assessment.common_period_snow_mean_available,'common_decade_mean_available_no_automatic_exclusion','common_decade_still_missing_explicit_reason')
    frames=[winter,profile,assessment];target=ROOT/SUMMARY
    if target.exists():
        m=json.loads(target.read_text(encoding='utf-8'))
        if m['input_sha256']!=inputs or any(sha(p)!=h for p,h in m['output_sha256'].items()):raise ValueError('Frozen common profiles differ')
    else:
        for p,f in zip(OUTPUTS,frames):write_csv(f,ROOT/p)
        m=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,output_sha256={p:sha(p) for p in OUTPUTS},
            daily_checkpoints=dailyproof,retained_groups=len(groups),common_winter_rows=len(winter),
            available_ten_winter_profiles=int(profile.common_ten_winter_mean_m.notna().sum()),profile_status_counts=profile.status.value_counts().to_dict(),
            all_previous13_reassessed=True,previous13_mean_available_count=int(assessment.common_period_snow_mean_available.sum()),
            no_external_request_or_new_original_values_read=True,no_imputation_OSHD_prediction_or_causal_fit=True,old_preentry_profiles_not_overwritten=True)
        target.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    register(frames)
    print(json.dumps({k:v for k,v in m.items() if k not in ['input_sha256','output_sha256','daily_checkpoints']},ensure_ascii=False))


if __name__=='__main__':main()
