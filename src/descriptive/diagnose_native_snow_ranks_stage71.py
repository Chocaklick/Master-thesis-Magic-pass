"""Approved descriptive within-group Spearman, fixed three civil-date offsets.

Compute Pearson of average ranks directly; scipy is unnecessary and no iid
p-value is produced for temporally dependent days. Preserve the frozen daily
values, paired support, all groups and explicit unavailable/constant statuses.
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

SOURCE='DERIVED_NATIVE_SNOW_RANK_DIAGNOSTIC_STAGE71'
CONFIG='config/snow_rank_diagnostic_decisions_stage71.json'
DAILY='data_processed/native_snow_daily_common_support_stage70.csv'
COVERAGE='data_processed/native_snow_value_coverage_stage70.csv'
OUTPUT='data_processed/native_snow_rank_diagnostic_stage71.csv'
SUMMARY='reports/native_snow_rank_diagnostic_stage71_summary.json'
TABLE='native_snow_rank_diagnostic_stage71'
DEFS={
    'source_id':('Derived rank-diagnostic provenance identifier','identifier'),
    'station_group_id':('Preserved group ID, not independent municipality/day/cell','identifier'),
    'station_group_name':('Preserved group name','text'),
    'group_retained':('True for all70groups, including missing geometry','boolean'),
    'oshd_date_offset_days':('OSHD date minus SPASS date: fixed -1/0/+1; no best lag selection','days'),
    'reference_offset':('True only at validated same-civil-date offset0','boolean'),
    'diagnostic_status':('Computed on complete/incomplete daily pairs or explicit no-geometry/constant/insufficient status','text'),
    'requested_spass_days':('151 fixed SPASS dates in pilot December2022April2023','count'),
    'available_daily_rows':('Actual group-lag daily rows;0 means no row extracted, not zero snow','count'),
    'finite_paired_days':('Days with both finite daily common-support means; missing when no geometry','count'),
    'missing_pair_days':('Requested151 minus finite pairs; missing when no geometry','count'),
    'spass_unique_paired_values':('Number of distinct original-unit SPASS daily means among paired days','count'),
    'oshd_unique_paired_values':('Number of distinct original OSHD daily means among paired days','count'),
    'spass_tied_paired_days':('Paired days whose SPASS value occurs more than once; no rounding tolerance','count'),
    'oshd_tied_paired_days':('Paired days whose OSHD value occurs more than once; average ranks used','count'),
    'spass_zero_paired_days':('Paired days with genuine exactly-zero SPASS common-support mean','count'),
    'oshd_zero_paired_days':('Paired days with genuine exactly-zero OSHD common-support mean','count'),
    'spearman_rho':('Pearson correlation of within-group average ranks on finite paired days; undefined for constant series or fewer than2pairs','dimensionless [-1,1]'),
    'rho_difference_from_offset_zero':('Same-group lagrho minus reference0rho; descriptive sensitivity not chosen lag','dimensionless'),
    'days_with_full_common_length':('Unchanged native-value coverage count from Stage70','count'),
    'min_common_observed_length_share':('Unchanged minimum observed length coverage, not correlation confidence','fraction'),
    'mean_common_observed_length_share':('Unchanged equal-day average coverage for this fixed lag','fraction'),
    'unique_mapped_axis_length_m':('Preserved candidate unique axis length; missing geometry is not zero','metres'),
    'spass_source_unit':('UNKNOWN; rank calculation does not certify physical numeric scale','text'),
    'oshd_source_unit':('Original documented OSHD hs unit m','text'),
    'physical_unit_comparison_available':('False; no undocumented level conversion/bias/MAE/RMSE','boolean'),
    'p_value_or_ci_computed':('False; no assumption of151 independent days','boolean'),
    'current_proxy_not_verified_preentry':('Current candidate piste support retains historical qualification','boolean'),
}


def rank_correlation(a,b):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    if a.ndim!=1 or a.shape!=b.shape:
        raise ValueError('Aligned one-dimensional daily pairs required')
    finite=np.isfinite(a)&np.isfinite(b)
    a,b=a[finite],b[finite]
    n=len(a)
    out=dict(finite_paired_days=n,spass_unique_paired_values=len(np.unique(a)),oshd_unique_paired_values=len(np.unique(b)),
        spass_tied_paired_days=int(pd.Series(a).duplicated(keep=False).sum()),oshd_tied_paired_days=int(pd.Series(b).duplicated(keep=False).sum()),
        spass_zero_paired_days=int((a==0).sum()),oshd_zero_paired_days=int((b==0).sum()),spearman_rho=None)
    if n<2:
        return {**out,'diagnostic_status':'fewer_than_two_finite_pairs'}
    constant_a=out['spass_unique_paired_values']==1;constant_b=out['oshd_unique_paired_values']==1
    if constant_a or constant_b:
        return {**out,'diagnostic_status':'both_series_constant' if constant_a and constant_b else 'spass_series_constant' if constant_a else 'oshd_series_constant'}
    ra=pd.Series(a).rank(method='average').to_numpy();rb=pd.Series(b).rank(method='average').to_numpy()
    ra-=ra.mean();rb-=rb.mean()
    numerator=math.fsum(ra*rb);denominator=math.sqrt(math.fsum(ra*ra)*math.fsum(rb*rb))
    rho=numerator/denominator
    # Clamp only floating representation at the mathematical coefficient limits.
    if not -1-1e-15<=rho<=1+1e-15:
        raise ValueError('Invalid rank correlation')
    return {**out,'spearman_rho':min(1.,max(-1.,rho)),'diagnostic_status':'computed'}


def validate_dates(frame,decisions):
    keys=['station_group_id','spass_civil_date','oshd_date_offset_days']
    if frame.duplicated(keys).any():
        raise ValueError('Duplicate group/date/lag observations')
    expected=set(pd.date_range(decisions['pilot_start'],decisions['pilot_end']).strftime('%Y-%m-%d'))
    for (gid,lag),rows in frame.groupby(['station_group_id','oshd_date_offset_days']):
        if lag not in decisions['date_offsets_days'] or set(rows.spass_civil_date)!=expected:
            raise ValueError('Missing/extra reference dates or unapproved lag: '+gid)
        offsets=(pd.to_datetime(rows.oshd_civil_date)-pd.to_datetime(rows.spass_civil_date)).dt.days
        if not offsets.eq(lag).all():
            raise ValueError('Actual source date offset differs')


def main():
    paths=[CONFIG,DAILY,COVERAGE,'reports/native_snow_values_stage70_summary.json',
        'config/native_snow_provenance_corrections_stage70.json','reports/preservation_stage70_summary.json',
        'src/descriptive/diagnose_native_snow_ranks_stage71.py']
    inputs={p:digest(p) for p in paths}
    parent=json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
    for p,h in parent['output_sha256'].items():
        if digest(p)!=h:
            raise ValueError('Frozen source daily values/coverage changed')
    decisions=json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['date_offsets_days']!=[-1,0,1] or decisions['reference_date_offset_days']!=0 or decisions['new_unit_conversion'] or decisions['choose_best_lag']:
        raise ValueError('Only approved fixed-lag raw-unit ranks allowed')
    daily=pd.read_csv(ROOT/DAILY,float_precision='round_trip')
    coverage=pd.read_csv(ROOT/COVERAGE,float_precision='round_trip')
    validate_dates(daily,decisions)
    if coverage.duplicated(['station_group_id','oshd_date_offset_days']).any() or len(coverage)!=210:
        raise ValueError('Retained universe/coverage keys changed')
    if not daily.spass_unit.eq('UNKNOWN').all() or not daily.oshd_unit.eq('m').all() or daily.physical_unit_comparison_available.any():
        raise ValueError('Parent source units altered')
    rows=[]
    for c in coverage.itertuples():
        f=daily[daily.station_group_id.eq(c.station_group_id)&daily.oshd_date_offset_days.eq(c.oshd_date_offset_days)].sort_values('spass_civil_date')
        record=dict(source_id=SOURCE,station_group_id=c.station_group_id,station_group_name=c.station_group_name,group_retained=c.group_retained,
            oshd_date_offset_days=c.oshd_date_offset_days,reference_offset=c.oshd_date_offset_days==0,requested_spass_days=c.requested_days,
            available_daily_rows=len(f),spass_source_unit='UNKNOWN',oshd_source_unit='m',physical_unit_comparison_available=False,
            p_value_or_ci_computed=False,current_proxy_not_verified_preentry=c.current_proxy_not_verified_preentry,
            **{key:getattr(c,key) for key in ['days_with_full_common_length','min_common_observed_length_share','mean_common_observed_length_share','unique_mapped_axis_length_m']})
        if not len(f):
            record['diagnostic_status']='no_usable_geometry__'+c.value_status
        else:
            metrics=rank_correlation(f.spass_mean_common_raw.to_numpy(),f.oshd_mean_common_m.to_numpy())
            record.update(metrics);record['missing_pair_days']=c.requested_days-metrics['finite_paired_days']
            if metrics['diagnostic_status']=='computed':
                record['diagnostic_status']='computed_complete_daily_pairs' if not record['missing_pair_days'] else 'computed_incomplete_daily_pairs'
        rows.append(record)
    result=pd.DataFrame(rows).reindex(columns=DEFS)
    zero=result[result.reference_offset].set_index('station_group_id').spearman_rho
    result['rho_difference_from_offset_zero']=result.spearman_rho-result.station_group_id.map(zero)
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    target=ROOT/SUMMARY
    if target.exists():
        summary=json.loads(target.read_text(encoding='utf8'))
        if summary['input_sha256']!=inputs or digest(OUTPUT)!=summary['output_sha256'][OUTPUT]:
            raise ValueError('Frozen rank diagnostic changed; create new stage')
    else:
        if len(master)!=1201 or len(dictionary)!=8188:
            raise ValueError('Unexpected registry baseline')
        write_csv(result,ROOT/OUTPUT)
        summaries={}
        for lag,part in result.groupby('oshd_date_offset_days'):
            rho=part.spearman_rho.dropna();delta=part.rho_difference_from_offset_zero.dropna()
            summaries[str(lag)]=dict(retained_groups=len(part),rho_available_groups=len(rho),unavailable_groups=int(part.spearman_rho.isna().sum()),
                rho_min=float(rho.min()),rho_q25=float(rho.quantile(.25)),rho_median=float(rho.median()),rho_q75=float(rho.quantile(.75)),rho_max=float(rho.max()),
                delta_from_zero_min=float(delta.min()),delta_from_zero_median=float(delta.median()),delta_from_zero_max=float(delta.max()),
                min_finite_paired_days=int(part.finite_paired_days.min()),max_finite_paired_days=int(part.finite_paired_days.max()))
        summary=dict(date='2026-10-10',input_sha256=inputs,output_sha256={OUTPUT:digest(OUTPUT)},
            prior_registry_rows_and_digest={p:dict(rows=len(f),sha256=row_digest(f)) for p,f in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]},
            rows=len(result),retained_groups=result.station_group_id.nunique(),lag_summary=summaries,
            status_counts=result.diagnostic_status.value_counts().to_dict(),rank_ties='average',p_values_or_ci_computed=False,
            physical_difference_or_conversion=False,source_splicing_or_calibration=False,choose_best_lag=False,
            five_own_preentry_winters_unchanged=True,new_clustering_or_effect_fit=False,
            software_versions=dict(python=sys.version.split()[0],pandas=pd.__version__,numpy=np.__version__),decisions=decisions)
        target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if SOURCE not in set(master.source_id):
        r=dict(source_id=SOURCE,variable_name='native_snow_within_group_spearman_fixed_lags',
            variable_description='Descriptive rank concordance per retained group and fixed -1/0/+1 civil-day lag, no absolute-level agreement',
            source_organisation='Thesis derived analysis of preserved SLF SPASS/OSHD means',source_dataset_name='Frozen Stage70 observed common piste support',
            retrieval_method='Local checksum-verified outputs only; no external request',retrieval_date='2026-10-10',processed_file=OUTPUT,
            geographic_level='Station group, not municipality or independent days/cells',temporal_resolution='One December2022April2023 pilot,151 reference dates per lag',
            temporal_start='2022-12-01',temporal_end='2023-04-30',unit='Dimensionless Spearman ranks; SPASS unit remains UNKNOWN',
            license='Parent SPASS WSL Data Policy; OSHD CC-BY4.0; OSM ODbL; no new licence assigned',
            transformation_applied='Pearson of average ranks, finite daily pairs, constant/insufficient statuses retained,0fixedreference and lag deltas',
            quality_notes='No iid p-value/CI, best-lag selection, detrending, source conversion/calibration/splice/group exclusion or effectfit; shared seasonality and single-winter limits',
            notes=CONFIG+'; '+SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([r]).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
    records=[]
    for col,(description,unit) in DEFS.items():
        if ((dictionary.table==TABLE)&(dictionary.variable==col)).any():
            continue
        records.append(dict(variable=col,table=TABLE,description=description,unit=unit,data_type=str(result[col].dtype),
            geographic_level='Retained stationgroup, not independent daily observations',temporal_level='Single pilot winter and fixed lag, not ownfivewinter feature',source_id=SOURCE,
            raw_or_derived='derived',formula=description,causal_role='Descriptive snow model rank diagnostic only; no causal effect or preentry profile',
            missing_share=f'{result[col].isna().mean():.6f}',notes='Average tied ranks; fixed0reference; unit uncertainty/missing geometry retained; no p-value,CI,scale certification or splice'))
    if records:
        write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['input_sha256','output_sha256','prior_registry_rows_and_digest','decisions']},ensure_ascii=False))


if __name__=='__main__':
    main()
