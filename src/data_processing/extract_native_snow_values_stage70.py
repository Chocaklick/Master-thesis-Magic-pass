"""Native observed common support, original units, fixed civil-date offsets.

Only geometry has a common refinement: source snow fields are never resampled.
Monthly/151-day NumPy reads are bounded and source indices paired after reading,
avoiding netCDF4 orthogonal-fancy-index Cartesian selection. Cache checkpoints
hold unchanged original decoded values/masks and are verified before reuse.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest, SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

SOURCE='DERIVED_NATIVE_SNOW_VALUES_STAGE70'
CONFIG='config/snow_value_audit_stage70.json'
SUMMARY='reports/native_snow_values_stage70_summary.json'
PARENT='reports/native_snow_weights_stage69_summary.json'
DAILY='data_processed/native_snow_daily_common_support_stage70.csv'
COVERAGE='data_processed/native_snow_value_coverage_stage70.csv'
CACHE=ROOT/'data_interim/native_snow_values_stage70'
DAILY_DEFS={
    'source_id':('Derived native value audit source','identifier'),
    'station_group_id':('Retained station-group identifier, not municipality','identifier'),
    'spass_civil_date':('Reference date in fixed December2022April2023 diagnostic','date'),
    'oshd_date_offset_days':('OSHD date minus SPASS date: fixed -1/0/+1; zero reference','days'),
    'oshd_civil_date':('Actually observed source coordinate date','date'),
    'spass_original_timestamp':('Literal decoded original SPASS timestamp; raw units retained in parent date pairs','timestamp'),
    'oshd_original_timestamp':('Literal decoded original OSHD timestamp; no simultaneous-time claim','timestamp'),
    'oshd_source_id':('Original annual OSHD archive identifier','identifier'),
    'oshd_member_file':('Actual original monthly member; protected SHA in parent manifest','relative file path'),
    'unique_mapped_axis_length_m':('Preserved total unique candidate axis length, not exhaustive certified domaine','metres'),
    'spass_observed_length_m':('Length with finite unmasked SPASS value, including true zeros','metres'),
    'oshd_observed_length_m':('Length with finite unmasked OSHD value, including true zeros','metres'),
    'common_observed_length_m':('Length with both values finite and unmasked on identical footprints','metres'),
    'common_observed_length_share':('Common observed length divided by total unique axis length','fraction'),
    'spass_only_observed_length_m':('Finite SPASS but missing OSHD, retained not compared','metres'),
    'oshd_only_observed_length_m':('Finite OSHD but missing SPASS, retained not compared','metres'),
    'neither_observed_length_m':('Both fields missing, retained not zero-filled','metres'),
    'spass_mean_common_raw':('SUM(length*original SPASS value) / common observed length; missing if no support','UNKNOWN source unit'),
    'oshd_mean_common_m':('SUM(length*original OSHD value) / exact same common length; missing if no support','metres'),
    'spass_unit':('UNKNOWN until actual distributed numeric scale proven; old metre inference not certification','text'),
    'oshd_unit':('Literal original hs unit attribute, verified m','text'),
    'spass_zero_common_length_m':('Common observed length with exactly zero original SPASS value','metres'),
    'oshd_zero_common_length_m':('Common observed length with exactly zero original OSHD value','metres'),
    'spass_negative_common_length_m':('Common observed length with negative original SPASS value; flagged not removed','metres'),
    'oshd_negative_common_length_m':('Common observed length with negative original OSHD value; flagged not removed','metres'),
    'physical_unit_comparison_available':('False: no undocumented raw-unit conversion or physical difference','boolean'),
}
COVERAGE_DEFS={
    'source_id':('Derived native snow value audit source','identifier'),
    'station_group_id':('All70group IDs retained, one row per fixed lag','identifier'),
    'station_group_name':('Preserved group name','text'),
    'group_retained':('True for all groups; missing geometry is not exclusion','boolean'),
    'oshd_date_offset_days':('Fixed date offset: zero reference, plus/minusone sensitivity','days'),
    'value_status':('Native values read or preserved unresolved geometry status','text'),
    'requested_days':('151 reference SPASS civil dates, not independent stations','count'),
    'days_with_common_observed_length':('Days with strictly positive pairwise observed support; missing if no geometry','count'),
    'days_with_full_common_length':('Days with all positive footprints observed in both models; missing if no geometry','count'),
    'min_common_observed_length_share':('Minimum per-day common length share for this fixed lag','fraction'),
    'mean_common_observed_length_share':('Equal-day mean of geometric coverage only, not a fivewinter snow mean','fraction'),
    'unique_mapped_axis_length_m':('Unchanged candidate network length; missing if absent, not zero','metres'),
    'spass_negative_value_days':('Days with any negative SPASS common-support values; retained and flagged','count'),
    'oshd_negative_value_days':('Days with any negative OSHD common-support values; retained and flagged','count'),
    'physical_unit_comparison_available':('False until distributed SPASS unit justified; not missing data exclusion','boolean'),
    'current_proxy_not_verified_preentry':('True: current piste geometry with historical uncertainty, no entry-date certification','boolean'),
}


def finite_values(values):
    """Preserve the netCDF missing mask; zero and negative are not missing."""
    return np.asarray(np.ma.asarray(values,dtype=float).filled(np.nan),dtype=float)


def support_metrics(spass,oshd,lengths):
    a,b,w=np.asarray(spass),np.asarray(oshd),np.asarray(lengths,dtype=float)
    if a.shape!=b.shape or a.shape!=w.shape or not np.isfinite(w).all() or not (w>0).all():
        raise ValueError('Aligned original values and positive exact lengths required')
    sa,ob=np.isfinite(a),np.isfinite(b)
    common=sa&ob
    length=lambda mask:math.fsum(w[mask])
    total=math.fsum(w); c=length(common)
    result=dict(unique_mapped_axis_length_m=total,spass_observed_length_m=length(sa),oshd_observed_length_m=length(ob),
        common_observed_length_m=c,common_observed_length_share=c/total,
        spass_only_observed_length_m=length(sa&~ob),oshd_only_observed_length_m=length(ob&~sa),neither_observed_length_m=length(~sa&~ob),
        spass_mean_common_raw=math.fsum(w[common]*a[common])/c if c else None,
        oshd_mean_common_m=math.fsum(w[common]*b[common])/c if c else None,
        spass_zero_common_length_m=length(common&(a==0)),oshd_zero_common_length_m=length(common&(b==0)),
        spass_negative_common_length_m=length(common&(a<0)),oshd_negative_common_length_m=length(common&(b<0)))
    return result


def read_cache(key,source,source_sha,indices,times,variable,dimensions):
    """Bounded one original source per checkpoint; freeze code and index lists."""
    CACHE.mkdir(exist_ok=True)
    npz=CACHE/(key+'.npz'); manifest=CACHE/(key+'.json')
    contract=dict(source_file=source,source_sha256=source_sha,indices=indices.tolist(),times=times.tolist(),
                  variable=variable,dimensions=list(dimensions),producer_sha256=digest('src/data_processing/extract_native_snow_values_stage70.py'))
    if manifest.exists():
        m=json.loads(manifest.read_text(encoding='utf8'))
        if m['contract']!=contract or digest(npz.relative_to(ROOT))!=m['cache_sha256']:
            raise ValueError('Frozen source-value checkpoint changed: '+key)
        with np.load(npz,allow_pickle=False) as data:
            return data['values'],m
    with ascii_link(ROOT/source) as link,Dataset(link) as d:
        v=d.variables[variable]
        if v.dimensions!=dimensions:
            raise ValueError('Unexpected original snowfield dimension order')
        unit=getattr(v,'units',getattr(v,'unit','UNKNOWN'))
        x0,n0=indices.min(axis=0);x1,n1=indices.max(axis=0)
        t0,t1=int(times.min()),int(times.max())
        if dimensions==('time','N','E'):
            block=finite_values(v[t0:t1+1,n0:n1+1,x0:x1+1])
            values=block[:,indices[:,1]-n0,indices[:,0]-x0][times-t0,:]
        else:
            block=finite_values(v[x0:x1+1,n0:n1+1,t0:t1+1])
            values=block[indices[:,0]-x0,indices[:,1]-n0,:][:,times-t0].T
        del block
        m=dict(contract=contract,unit=unit,original_mask_applied=True,
               original_fill_value=str(getattr(v,'_FillValue','ABSENT')),shape=list(values.shape))
    if npz.exists():
        with np.load(npz,allow_pickle=False) as existing:
            if not np.array_equal(existing['values'],values,equal_nan=True):
                raise ValueError('Unfinished checkpoint differs; preserve for review')
    else:
        np.savez_compressed(npz,values=values)
    m['cache_sha256']=digest(npz.relative_to(ROOT))
    manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(checkpoint=key,shape=m['shape'],unit=unit)),flush=True)
    return values,m


def main():
    parent=json.loads((ROOT/PARENT).read_text(encoding='utf8'))
    inputs={**parent['input_sha256'],**parent['output_sha256'],PARENT:digest(PARENT),CONFIG:digest(CONFIG),
            'src/data_processing/extract_native_snow_values_stage70.py':digest('src/data_processing/extract_native_snow_values_stage70.py')}
    for p,h in inputs.items():
        if digest(p)!=h:
            raise ValueError('Protected source/preparation changed: '+p)
    config=json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if config['new_unit_conversion'] or config['automatic_group_exclusion']:
        raise ValueError('No conversion/exclusion authorised')
    f=pd.read_csv(ROOT/'data_processed/native_snow_cell_pairs_stage69.csv',float_precision='round_trip')
    if not (f.spass_cell_in_grid & f.oshd_cell_in_grid).all():
        raise ValueError('Outside-native cells need explicit missing reader, never negative indices')
    dates=pd.read_csv(ROOT/'data_processed/native_snow_date_pairs_stage69.csv')
    se=f[['spass_e_index','spass_n_index']].drop_duplicates().sort_values(['spass_e_index','spass_n_index']).to_numpy(dtype=int)
    oe=f[['oshd_e_index','oshd_n_index']].drop_duplicates().sort_values(['oshd_e_index','oshd_n_index']).to_numpy(dtype=int)
    spath=json.loads((ROOT/'reports/snow_grid_metadata_compatibility_stage47.json').read_text(encoding='utf8'))['spass_raw_file']
    stimes=np.array(sorted(dates.spass_time_index.unique()),dtype=int)
    svalues,smeta=read_cache('spass_pilot',spath,inputs[spath],se,stimes,'HSCLQMD',('time','N','E'))
    if smeta['unit']!='UNKNOWN':
        raise ValueError('New SPASS unit evidence differs from approved raw-unit audit; review it')
    sloc={tuple(v):i for i,v in enumerate(se)};sdate={t:i for i,t in enumerate(stimes)}
    oloc={tuple(v):i for i,v in enumerate(oe)}
    ovalues={};metas={'spass_pilot':smeta}
    for p,rows in dates.groupby('oshd_member_file',sort=True):
        times=np.array(sorted(rows.oshd_time_index.unique()),dtype=int)
        key='oshd_'+Path(p).stem
        values,meta=read_cache(key,p,inputs[p],oe,times,'hs',('easting','northing','time'))
        if meta['unit']!='m':
            raise ValueError('Original OSHD unit is not documented metres')
        metas[key]=meta
        for i,t in enumerate(times):
            ovalues[(p,t)]=values[i]
    daily=[]
    grouped=dict(tuple(f.groupby('station_group_id',sort=False)))
    for gid,weights in grouped.items():
        si=np.array([sloc[t] for t in weights[['spass_e_index','spass_n_index']].itertuples(index=False,name=None)])
        oi=np.array([oloc[t] for t in weights[['oshd_e_index','oshd_n_index']].itertuples(index=False,name=None)])
        w=weights.unique_axis_length_m.to_numpy()
        for r in dates.itertuples():
            a=svalues[sdate[r.spass_time_index],si];b=ovalues[(r.oshd_member_file,r.oshd_time_index)][oi]
            base={k:getattr(r,k) for k in ['spass_civil_date','oshd_date_offset_days','oshd_civil_date','spass_original_timestamp','oshd_original_timestamp','oshd_source_id','oshd_member_file']}
            daily.append(dict(source_id=SOURCE,station_group_id=gid,**base,**support_metrics(a,b,w),spass_unit='UNKNOWN',oshd_unit='m',physical_unit_comparison_available=False))
    daily=pd.DataFrame(daily).reindex(columns=DAILY_DEFS)
    retained=pd.read_csv(ROOT/'data_processed/native_snow_weight_coverage_stage69.csv',float_precision='round_trip')
    coverage=[]
    for g in retained.itertuples():
        for lag in [-1,0,1]:
            rows=daily[daily.station_group_id.eq(g.station_group_id)&daily.oshd_date_offset_days.eq(lag)]
            record=dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.station_group_name,group_retained=True,
                oshd_date_offset_days=lag,requested_days=151,unique_mapped_axis_length_m=g.unique_mapped_axis_length_m,
                value_status='native_raw_values_extracted_unit_comparison_pending' if len(rows) else g.weight_status,
                physical_unit_comparison_available=False,current_proxy_not_verified_preentry=True)
            if len(rows):
                if len(rows)!=151:
                    raise ValueError('Reference dates lost')
                # Full means exact observed mask completeness, not a numeric coverage tolerance.
                record.update(days_with_common_observed_length=int(rows.common_observed_length_m.gt(0).sum()),
                    days_with_full_common_length=int((rows.spass_only_observed_length_m.eq(0)&rows.oshd_only_observed_length_m.eq(0)&rows.neither_observed_length_m.eq(0)).sum()),
                    min_common_observed_length_share=float(rows.common_observed_length_share.min()),mean_common_observed_length_share=float(rows.common_observed_length_share.mean()),
                    spass_negative_value_days=int(rows.spass_negative_common_length_m.gt(0).sum()),oshd_negative_value_days=int(rows.oshd_negative_common_length_m.gt(0).sum()))
            coverage.append(record)
    coverage=pd.DataFrame(coverage).reindex(columns=COVERAGE_DEFS)
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf8'))
        if state['input_sha256']!=inputs or any(digest(p)!=h for p,h in state['output_sha256'].items()):
            raise ValueError('Frozen raw snow audit changed; use new stage')
    else:
        if len(master)!=1199 or len(dictionary)!=8146:
            raise ValueError('Unexpected registry baseline')
        write_csv(daily,ROOT/DAILY);write_csv(coverage,ROOT/COVERAGE)
        state=dict(date='2026-10-10',input_sha256=inputs,output_sha256={p:digest(p) for p in [DAILY,COVERAGE]},
            prior_registry_rows_and_digest={p:dict(rows=len(frame),sha256=row_digest(frame)) for p,frame in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]},
            retained_groups=70,mapped_groups=len(grouped),daily_group_date_lag_rows=len(daily),coverage_rows=len(coverage),
            distinct_spass_native_cells=len(se),distinct_oshd_native_cells=len(oe),source_value_checkpoints=metas,
            lag_coverage={str(lag):dict(mapped_groups=len(rows),fully_observed_groups=int(rows.days_with_full_common_length.eq(151).sum()),
                groups_with_any_common_days=int(rows.days_with_common_observed_length.gt(0).sum()),min_length_share=float(rows.min_common_observed_length_share.min()))
                for lag,rows in coverage[coverage.days_with_common_observed_length.notna()].groupby('oshd_date_offset_days')},
            raw_spass_unit='UNKNOWN',original_oshd_unit='m',new_unit_conversion=False,physical_difference_computed=False,
            source_splicing_or_calibration=False,new_clustering_or_effect_fit=False)
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    review=config['unit_review_source_id']
    additions=[]
    if review not in set(master.source_id):
        additions.append(dict(source_id=review,variable_name='distributed_HSCLQMD_unit_evidence',variable_description=config['unit_review_findings'],
            source_organisation='WSL/SLF SWE2HS documentation and EnviDat',source_url='|'.join(config['unit_review_urls']),retrieval_date='2026-10-10',
            retrieval_method=config['unit_review_method'],quality_notes='Configurable example is not product-generation setting; unit remains UNKNOWN; no archived HTML/HTTP/checksum claimed',notes=CONFIG))
    if SOURCE not in set(master.source_id):
        additions.append(dict(source_id=SOURCE,variable_name='native_daily_snow_common_support',variable_description='Original-unit daily length-weighted snow fields on identical observed piste portions, fixed lag reference/sensitivities',
            source_organisation='Thesis derived SLF SPASS/OSHD audit',retrieval_date='2026-10-10',processed_file=DAILY+'|'+COVERAGE,
            geographic_level='Stationgroup current candidate axes, not municipal outcomes',temporal_resolution='151 daily pilot dates times3 fixed offsets; not five own preentry winters',
            retrieval_method='Protected original local NetCDF checksums; bounded source-value reads; resumable exact cache',
            transformation_applied='Native paired indices, original missing mask, exact common finite length denominator; no interpolation/missing zero-fill/unit conversion',
            quality_notes='SPASS UNKNOWN raw unit, OSHD m; no physical difference/calibration/splice/causal or clustering fit;70 groups retained',notes=SUMMARY))
    if additions:
        write_csv(pd.concat([master,pd.DataFrame(additions).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
    records=[]
    for table,frame,defs in [('native_snow_daily_common_support_stage70',daily,DAILY_DEFS),('native_snow_value_coverage_stage70',coverage,COVERAGE_DEFS)]:
        for col,(description,unit) in defs.items():
            if ((dictionary.table==table)&(dictionary.variable==col)).any():
                continue
            records.append(dict(table=table,variable=col,description=description,unit=unit,data_type=str(frame[col].dtype),
                geographic_level='Retained stationgroup/current candidate axes',temporal_level='Fixed civil-date pilot/lag, not own fivewinter feature',source_id=SOURCE,
                raw_or_derived='derived',formula=description,causal_role='Snow model compatibility preparation; not a causal/preentry feature or independent cell sample',
                missing_share=f'{frame[col].isna().mean():.6f}',notes='Original masks/zero distinction; exact common length denominator; no physical conversion or group exclusion'))
    if records:
        write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','source_value_checkpoints','prior_registry_rows_and_digest']},ensure_ascii=False))


if __name__=='__main__':
    main()
