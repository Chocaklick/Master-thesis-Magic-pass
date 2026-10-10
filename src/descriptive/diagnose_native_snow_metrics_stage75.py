"""Paired level discrepancies under the explicitly approved SPASS metre assumption.

Source metadata stay UNKNOWN. Native support, zeros, dates and groups stay
those of Stage70; metrics are discrepancies between models, not ground truth.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest, SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.descriptive.diagnose_native_snow_ranks_stage71 import validate_dates, DAILY, COVERAGE

SOURCE='DERIVED_NATIVE_SNOW_METRIC_DIAGNOSTIC_STAGE75'
CONFIG='config/snow_metric_decisions_stage75.json'
OUTPUT='data_processed/native_snow_metric_diagnostic_stage75.csv'
SUMMARY='reports/native_snow_metric_diagnostic_stage75_summary.json'
TABLE='native_snow_metric_diagnostic_stage75'
DEFS={
    'source_id':('Derived paired metric provenance ID','identifier'),
    'station_group_id':('Preserved group ID, not an independent commune/day/cell','identifier'),
    'station_group_name':('Preserved group name','text'),
    'group_retained':('True for all 70 groups, including missing geometry','boolean'),
    'oshd_date_offset_days':('Fixed OSHD date minus SPASS date: -1/0/+1; no optimised lag','days'),
    'reference_offset':('True for approved same civil date zero','boolean'),
    'diagnostic_status':('Computed paired metrics or explicit missing geometry/no finite pair','text'),
    'requested_spass_days':('151 fixed pilot reference dates','count'),
    'available_daily_rows':('Actual daily source rows; zero is not zero snow','count'),
    'finite_paired_days':('Days with both finite source means, missing for absent geometry','count'),
    'missing_pair_days':('151 minus finite paired days, missing for absent geometry','count'),
    'spass_original_source_unit':('UNKNOWN in the immutable original metadata','text'),
    'spass_analytical_unit':('m under exact latest researcher approval','metres, assumed'),
    'spass_unit_assumption_approved':('Explicitly true; approval is not producer certification','boolean'),
    'spass_raw_to_m_factor':('1.0: raw numbers interpreted as metres, no x100 in metric computation','factor'),
    'oshd_source_unit':('Documented original hs.unit=m','metres'),
    'spass_paired_mean_m':('Arithmetic mean of finite paired daily SPASS means under approved metre assumption','metres, assumed'),
    'oshd_paired_mean_m':('Arithmetic mean of finite paired daily OSHD means','metres'),
    'mean_oshd_minus_spass_m':('Mean(OSHD-SPASS) on finite paired days; sign is model difference, not error vs truth','metres, assumption-dependent'),
    'median_oshd_minus_spass_m':('Median(OSHD-SPASS) on finite paired days','metres, assumption-dependent'),
    'mean_absolute_difference_m':('Mean(abs(OSHD-SPASS)); no observed truth asserted','metres, assumption-dependent'),
    'root_mean_square_difference_m':('sqrt(mean((OSHD-SPASS)^2)); model discrepancy, not accuracy score','metres, assumption-dependent'),
    'min_common_observed_length_share':('Preserved Stage70 minimum common observed length share','fraction'),
    'mean_common_observed_length_share':('Preserved Stage70 mean common observed length share','fraction'),
    'unique_mapped_axis_length_m':('Preserved candidate unique mapped axis length','metres'),
    'spearman_daily_levels_stage71':('Unchanged daily rank reference, not re-estimated or unit-certified','dimensionless'),
    'spearman_daily_changes_stage72':('Unchanged daily change rank diagnostic','dimensionless'),
    'p_value_or_ci_computed':('False: temporal dependence and single pilot preserved','boolean'),
    'source_spliced_or_calibrated':('False: no substitute snow series or adjustment fitted','boolean'),
    'current_proxy_not_verified_preentry':('Current piste geometry retains historical uncertainty','boolean'),
}


def paired_metrics(a,b):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    if a.ndim!=1 or a.shape!=b.shape:
        raise ValueError('Aligned one-dimensional arrays required')
    good=np.isfinite(a)&np.isfinite(b)
    a,b=a[good],b[good]
    n=len(a)
    out=dict(finite_paired_days=n)
    if not n:
        return out
    d=b-a
    out.update(spass_paired_mean_m=math.fsum(a)/n,oshd_paired_mean_m=math.fsum(b)/n,
        mean_oshd_minus_spass_m=math.fsum(d)/n,median_oshd_minus_spass_m=float(np.median(d)),
        mean_absolute_difference_m=math.fsum(abs(d))/n,root_mean_square_difference_m=math.sqrt(math.fsum(d*d)/n))
    return out


def main():
    paths=[CONFIG,DAILY,COVERAGE,'data_processed/native_snow_rank_diagnostic_stage71.csv',
        'data_processed/native_snow_change_rank_diagnostic_stage72.csv',
        'reports/native_snow_values_stage70_summary.json','reports/native_snow_rank_diagnostic_stage71_summary.json',
        'reports/native_snow_change_rank_diagnostic_stage72_summary.json',
        'reports/spass_unit_investigation_stage74.json','src/descriptive/diagnose_native_snow_metrics_stage75.py']
    inputs={p:digest(p) for p in paths}
    for path in paths[5:8]:
        frozen=json.loads((ROOT/path).read_text(encoding='utf8'))
        for p,h in frozen['output_sha256'].items():
            if digest(p)!=h:
                raise ValueError('Frozen input changed: '+p)
    decisions=json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['spass_analytical_unit']!='m' or decisions['spass_original_declared_unit']!='UNKNOWN' or decisions['spass_raw_to_m_factor']!=1 or decisions['date_offsets_days']!=[-1,0,1] or decisions['reference_date_offset_days']!=0 or decisions['choose_best_lag']:
        raise ValueError('Explicit metre assumption and existing fixed date protocol required')
    daily=pd.read_csv(ROOT/DAILY,float_precision='round_trip')
    coverage=pd.read_csv(ROOT/COVERAGE,float_precision='round_trip')
    validate_dates(daily,decisions)
    if len(coverage)!=210 or coverage.duplicated(['station_group_id','oshd_date_offset_days']).any() or not daily.spass_unit.eq('UNKNOWN').all() or not daily.oshd_unit.eq('m').all():
        raise ValueError('Source universe/units changed')
    levels=pd.read_csv(ROOT/paths[3]).set_index(['station_group_id','oshd_date_offset_days'])
    changes=pd.read_csv(ROOT/paths[4]).set_index(['station_group_id','oshd_date_offset_days'])
    records=[]
    for c in coverage.itertuples():
        f=daily[daily.station_group_id.eq(c.station_group_id)&daily.oshd_date_offset_days.eq(c.oshd_date_offset_days)]
        key=(c.station_group_id,c.oshd_date_offset_days)
        r=dict(source_id=SOURCE,station_group_id=c.station_group_id,station_group_name=c.station_group_name,
            group_retained=c.group_retained,oshd_date_offset_days=c.oshd_date_offset_days,reference_offset=c.oshd_date_offset_days==0,
            requested_spass_days=c.requested_days,available_daily_rows=len(f),spass_original_source_unit='UNKNOWN',
            spass_analytical_unit='m',spass_unit_assumption_approved=True,spass_raw_to_m_factor=1.,oshd_source_unit='m',
            spearman_daily_levels_stage71=levels.loc[key,'spearman_rho'],spearman_daily_changes_stage72=changes.loc[key,'spearman_change_rho'],
            p_value_or_ci_computed=False,source_spliced_or_calibrated=False,current_proxy_not_verified_preentry=c.current_proxy_not_verified_preentry,
            **{k:getattr(c,k) for k in ['min_common_observed_length_share','mean_common_observed_length_share','unique_mapped_axis_length_m']})
        if len(f):
            r.update(paired_metrics(f.spass_mean_common_raw.to_numpy(),f.oshd_mean_common_m.to_numpy()))
            r['missing_pair_days']=c.requested_days-r['finite_paired_days']
            r['diagnostic_status']='computed_complete_pairs' if r['finite_paired_days']==c.requested_days else 'computed_partial_pairs' if r['finite_paired_days'] else 'no_finite_pairs'
        else:
            r['diagnostic_status']='no_usable_geometry__'+c.value_status
        records.append(r)
    result=pd.DataFrame(records).reindex(columns=DEFS)
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    target=ROOT/SUMMARY
    if target.exists():
        summary=json.loads(target.read_text(encoding='utf8'))
        if summary['input_sha256']!=inputs or summary['output_sha256'][OUTPUT]!=digest(OUTPUT):
            raise ValueError('Frozen metric diagnostic differs; create a new stage')
    else:
        if len(master)!=1217 or len(dictionary)!=8261:
            raise ValueError('Unexpected registry baseline')
        write_csv(result,ROOT/OUTPUT)
        by_lag={}
        for lag,g in result.groupby('oshd_date_offset_days'):
            valid=g[g.mean_oshd_minus_spass_m.notna()]
            by_lag[str(lag)]=dict(retained_groups=len(g),computed_groups=len(valid),missing_groups=len(g)-len(valid),
                bias_median_m=float(valid.mean_oshd_minus_spass_m.median()),bias_min_m=float(valid.mean_oshd_minus_spass_m.min()),bias_max_m=float(valid.mean_oshd_minus_spass_m.max()),
                mean_abs_difference_median_m=float(valid.mean_absolute_difference_m.median()),rms_difference_median_m=float(valid.root_mean_square_difference_m.median()),
                oshd_lower_groups=int(valid.mean_oshd_minus_spass_m.lt(0).sum()),oshd_higher_groups=int(valid.mean_oshd_minus_spass_m.gt(0).sum()),
                equal_mean_groups=int(valid.mean_oshd_minus_spass_m.eq(0).sum()),min_paired_days=int(valid.finite_paired_days.min()),max_paired_days=int(valid.finite_paired_days.max()))
        summary=dict(date='2026-10-10',input_sha256=inputs,output_sha256={OUTPUT:digest(OUTPUT)},
            prior_registry_rows_and_digest={p:dict(rows=len(f),sha256=row_digest(f)) for p,f in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]},
            rows=len(result),retained_groups=result.station_group_id.nunique(),lag_summary=by_lag,
            spass_unit_status='researcher-approved metre assumption, original declaration unknown',decisions=decisions,
            original_values_and_metadata_unchanged=True,physical_model_discrepancies_computed=True,
            source_spliced_or_calibrated=False,choose_best_lag=False,final_profiles_or_new_effect_fit=False)
        target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if SOURCE not in set(master.source_id):
        new=dict(source_id=SOURCE,variable_name='native_snow_paired_level_discrepancies_under_approved_metre_assumption',
            variable_description='Within-group model discrepancies, all groups retained, fixed native common support/date offsets; SPASS metre assumption explicitly approved',
            source_organisation='Thesis derived SPASS/OSHD diagnostic',source_dataset_name='Frozen Stage70 means with Stage71/72 rank references',
            source_page_url='reports/120_COMPARAISON_NEIGE_METRES_FR.md',retrieval_method='Local hash-verified outputs; no network or original field reread',
            retrieval_date='2026-10-10',processed_file=OUTPUT,geographic_level='Station group; not municipality or independent daily units',
            temporal_resolution='Fixed daily pilot December2022April2023',temporal_start='2022-12-01',temporal_end='2023-04-30',
            unit='m, SPASS researcher-approved assumption; OSHD documented m',license='Parents SPASS WSL Data Policy, OSHD CC-BY4.0, OSM ODbL; no new redistribution licence',
            transformation_applied='Factor1 SPASS raw-to-m; paired equal-day model means, signed/absolute/quadratic differences; rank references retained',
            quality_notes='No ground truth accuracy, unit certification, CI/pvalue, calibration/splice, optimised lag or sample filter; one pilot winter only',notes=CONFIG+'; '+SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([new]).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
    additions=[]
    for col,(description,unit) in DEFS.items():
        if ((dictionary.table==TABLE)&(dictionary.variable==col)).any():
            continue
        additions.append(dict(variable=col,table=TABLE,description=description,unit=unit,data_type=str(result[col].dtype),
            geographic_level='Retained station group',temporal_level='Fixed pilot/date offset, not five-own-winter feature',source_id=SOURCE,
            raw_or_derived='derived',formula=description,causal_role='Model discrepancy diagnostic only',missing_share=f'{result[col].isna().mean():.6f}',
            notes='SPASS analytical unit m is researcher-approved assumption; original unit remains UNKNOWN; missing geometry retained'))
    if additions:
        write_csv(pd.concat([dictionary,pd.DataFrame(additions).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['input_sha256','output_sha256','prior_registry_rows_and_digest','decisions']},ensure_ascii=False))


if __name__=='__main__':
    main()
