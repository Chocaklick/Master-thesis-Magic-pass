"""Approved complementary ranks of actual consecutive-day snow changes.

Audit native footprints across all dates and monthly boundaries first. Never
mistake equal length coverage for identical support, bridge holes, select a lag,
convert unknown units, or replace the preserved daily-level diagnostic.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest, SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.descriptive.diagnose_native_snow_ranks_stage71 import rank_correlation, validate_dates, DAILY, COVERAGE

SOURCE = 'DERIVED_NATIVE_SNOW_CHANGES_STAGE72'
CONFIG = 'config/snow_daily_change_decisions_stage72.json'
OUTPUT = 'data_processed/native_snow_change_rank_diagnostic_stage72.csv'
SUMMARY = 'reports/native_snow_change_rank_diagnostic_stage72_summary.json'
TABLE = 'native_snow_change_rank_diagnostic_stage72'
PARENT = 'reports/native_snow_values_stage70_summary.json'
LEVELS = 'data_processed/native_snow_rank_diagnostic_stage71.csv'
WEIGHTS = 'data_processed/native_snow_cell_pairs_stage69.csv'
DATES = 'data_processed/native_snow_date_pairs_stage69.csv'
DEFS = {
    'source_id': ('Derived change diagnostic provenance ID', 'identifier'),
    'station_group_id': ('Stable retained group ID, not municipality or independent days', 'identifier'),
    'station_group_name': ('Preserved station-group name', 'text'),
    'group_retained': ('True for every group, including missing geometry', 'boolean'),
    'oshd_date_offset_days': ('Fixed OSHD civil date minus SPASS date: -1/0/+1, no selected best lag', 'days'),
    'reference_offset': ('True only for approved same-civil-date reference zero', 'boolean'),
    'diagnostic_status': ('Computed or explicit unavailable geometry/constant/insufficient status', 'text'),
    'requested_consecutive_pairs': ('150 potential consecutive daily changes in fixed 151-day pilot', 'count'),
    'available_consecutive_pairs': ('Number of actual consecutive calendar pairs before finite-value check; zero rows not zero snow', 'count'),
    'finite_paired_changes': ('Changes for which both source models have finite values at both observed endpoints', 'count'),
    'missing_change_pairs': ('Requested150 minus finite change pairs, missing if no geometry', 'count'),
    'spass_unique_changes': ('Distinct SPASS changes in own original unknown unit', 'count'),
    'oshd_unique_changes': ('Distinct OSHD changes in original metre unit', 'count'),
    'spass_tied_changes': ('Paired changes with duplicated SPASS values, no rounding tolerance', 'count'),
    'oshd_tied_changes': ('Paired changes with duplicated OSHD values, average ranks used', 'count'),
    'spass_zero_changes': ('Paired changes exactly zero, not days with zero snow', 'count'),
    'oshd_zero_changes': ('Paired changes exactly zero, not days with zero snow', 'count'),
    'spearman_change_rho': ('Pearson correlation of average ranks of consecutive-day changes, undefined for constant or insufficient series', 'dimensionless [-1,1]'),
    'rho_difference_from_offset_zero': ('Same-group change rho minus fixed reference change rho, no optimized lag', 'dimensionless'),
    'spearman_daily_level_rho_stage71': ('Preserved parent daily-level rho for context, different temporal target', 'dimensionless [-1,1]'),
    'support_adjacent_pairs_checked': ('Native footprint masks checked individually across consecutive dates, including monthly file boundaries', 'count'),
    'support_changed_pairs': ('Pairs whose observed footprint composition changes; zero only when actually verified', 'count'),
    'max_changed_support_length_m': ('Maximum length of symmetric footprint-mask difference across adjacent dates', 'metres'),
    'min_common_observed_length_share': ('Unchanged Stage70 minimum observed common length coverage', 'fraction'),
    'mean_common_observed_length_share': ('Unchanged Stage70 mean observed common length coverage', 'fraction'),
    'unique_mapped_axis_length_m': ('Unchanged unique candidate piste length, missing if no usable geometry', 'metres'),
    'spass_source_unit': ('UNKNOWN; within-source changes and rank calculation do not certify physical scale', 'text'),
    'oshd_source_unit': ('Original documented OSHD hs unit m', 'text'),
    'physical_unit_comparison_available': ('False; no between-model physical subtraction or unit conversion', 'boolean'),
    'p_value_or_ci_computed': ('False; consecutive daily changes not assumed independent', 'boolean'),
    'current_proxy_not_verified_preentry': ('Preserved historical uncertainty of current candidate piste support', 'boolean'),
}


def consecutive_changes(frame):
    """Sort actual dates; a gap invalidates its pair, without bridging it."""
    f = frame.sort_values('spass_civil_date')
    dates = pd.to_datetime(f.spass_civil_date)
    if dates.duplicated().any():
        raise ValueError('Duplicate daily date')
    # Explicit day unit avoids pandas/NumPy generic NaT timedelta deprecation.
    civil_dates = dates.to_numpy(dtype='datetime64[D]')
    consecutive = np.diff(civil_dates) == np.timedelta64(1, 'D')
    a = f.spass_mean_common_raw.to_numpy(dtype=float)
    b = f.oshd_mean_common_m.to_numpy(dtype=float)
    if not len(a):
        return np.array([]), np.array([]), 0
    finite = consecutive & np.isfinite(a[1:]) & np.isfinite(a[:-1]) & np.isfinite(b[1:]) & np.isfinite(b[:-1])
    da, db = np.full(max(0, len(a)-1), np.nan), np.full(max(0, len(b)-1), np.nan)
    da[finite] = a[1:][finite] - a[:-1][finite]
    db[finite] = b[1:][finite] - b[:-1][finite]
    return da, db, int(consecutive.sum())


def support_stability(masks, lengths):
    masks, lengths = np.asarray(masks, dtype=bool), np.asarray(lengths, dtype=float)
    if masks.ndim != 2 or masks.shape[1] != len(lengths) or not np.isfinite(lengths).all() or not (lengths > 0).all():
        raise ValueError('Aligned footprint masks and positive lengths required')
    changed = masks[1:] != masks[:-1]
    lengths_changed = [math.fsum(lengths[row]) for row in changed]
    return dict(support_adjacent_pairs_checked=len(changed), support_changed_pairs=int(changed.any(axis=1).sum()),
                max_changed_support_length_m=max(lengths_changed, default=0.))


def audit_support(parent):
    """Use frozen original-value caches; no NetCDF re-read or new collection."""
    cached = {}
    cache_inputs = {}
    for key, meta in parent['source_value_checkpoints'].items():
        path = 'data_interim/native_snow_values_stage70/' + key + '.npz'
        manifest = 'data_interim/native_snow_values_stage70/' + key + '.json'
        if json.loads((ROOT/manifest).read_text(encoding='utf8')) != meta or digest(path) != meta['cache_sha256']:
            raise ValueError('Protected source-value cache changed: '+key)
        cache_inputs[path] = meta['cache_sha256']
        cache_inputs[manifest] = digest(manifest)
        with np.load(ROOT/path, allow_pickle=False) as data:
            values = data['values']
        contract = meta['contract']
        if list(values.shape) != meta['shape'] or contract['source_sha256'] != parent['input_sha256'][contract['source_file']]:
            raise ValueError('Cache shape or original provenance changed')
        cached[contract['source_file']] = (values, {t: i for i, t in enumerate(contract['times'])},
                                        {tuple(v): i for i, v in enumerate(contract['indices'])})
    weights = pd.read_csv(ROOT/WEIGHTS, float_precision='round_trip')
    dates = pd.read_csv(ROOT/DATES)
    spass_source = parent['source_value_checkpoints']['spass_pilot']['contract']['source_file']
    sv, st, si = cached[spass_source]
    audit = {}
    for gid, group in weights.groupby('station_group_id', sort=False):
        sidx = [si[t] for t in group[['spass_e_index', 'spass_n_index']].itertuples(index=False, name=None)]
        for lag, calendar in dates.groupby('oshd_date_offset_days'):
            masks = []
            for r in calendar.sort_values('spass_civil_date').itertuples():
                ov, ot, oi = cached[r.oshd_member_file]
                oidx = [oi[t] for t in group[['oshd_e_index', 'oshd_n_index']].itertuples(index=False, name=None)]
                masks.append(np.isfinite(sv[st[r.spass_time_index], sidx]) & np.isfinite(ov[ot[r.oshd_time_index], oidx]))
            audit[(gid, int(lag))] = support_stability(masks, group.unique_axis_length_m.to_numpy())
    if any(v['support_changed_pairs'] for v in audit.values()):
        # A changing mean-support target requires an actual new methodological choice.
        raise ValueError('Observed footprint composition changes: present temporal support alternatives for validation before estimation')
    return audit, cache_inputs


def main():
    paths = [CONFIG, DAILY, COVERAGE, WEIGHTS, DATES, LEVELS, PARENT,
             'reports/native_snow_rank_diagnostic_stage71_summary.json', 'reports/preservation_stage71_summary.json',
             'src/descriptive/diagnose_native_snow_changes_stage72.py', 'src/descriptive/diagnose_native_snow_ranks_stage71.py']
    inputs = {p: digest(p) for p in paths}
    parent = json.loads((ROOT/PARENT).read_text(encoding='utf8'))
    prior = json.loads((ROOT/'reports/native_snow_rank_diagnostic_stage71_summary.json').read_text(encoding='utf8'))
    for p, h in {**parent['output_sha256'], **prior['output_sha256']}.items():
        if digest(p) != h:
            raise ValueError('Frozen parent output changed: '+p)
    for p in [WEIGHTS, DATES]:
        if digest(p) != parent['input_sha256'][p]:
            raise ValueError('Frozen native geometry/calendar changed')
    decisions = json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['date_offsets_days'] != [-1,0,1] or decisions['reference_date_offset_days'] != 0 or not decisions['preserve_daily_level_reference'] or decisions['choose_best_lag'] or decisions['new_unit_conversion']:
        raise ValueError('Unapproved diagnostic choice')
    daily = pd.read_csv(ROOT/DAILY, float_precision='round_trip')
    coverage = pd.read_csv(ROOT/COVERAGE, float_precision='round_trip')
    levels = pd.read_csv(ROOT/LEVELS, float_precision='round_trip').set_index(['station_group_id','oshd_date_offset_days'])
    validate_dates(daily, decisions)
    if len(coverage) != 210 or coverage.duplicated(['station_group_id','oshd_date_offset_days']).any():
        raise ValueError('Retained coverage universe changed')
    audit, cache_inputs = audit_support(parent)
    inputs.update(cache_inputs)
    requested = (pd.Timestamp(decisions['pilot_end']) - pd.Timestamp(decisions['pilot_start'])).days
    rows = []
    for c in coverage.itertuples():
        f = daily[daily.station_group_id.eq(c.station_group_id) & daily.oshd_date_offset_days.eq(c.oshd_date_offset_days)]
        key = (c.station_group_id, c.oshd_date_offset_days)
        r = dict(source_id=SOURCE, station_group_id=c.station_group_id, station_group_name=c.station_group_name, group_retained=c.group_retained,
                 oshd_date_offset_days=c.oshd_date_offset_days, reference_offset=c.oshd_date_offset_days==0,
                 requested_consecutive_pairs=requested, available_consecutive_pairs=0, spearman_daily_level_rho_stage71=levels.loc[key,'spearman_rho'],
                 spass_source_unit='UNKNOWN', oshd_source_unit='m', physical_unit_comparison_available=False, p_value_or_ci_computed=False,
                 **{k:getattr(c,k) for k in ['min_common_observed_length_share','mean_common_observed_length_share','unique_mapped_axis_length_m','current_proxy_not_verified_preentry']})
        if not len(f):
            r['diagnostic_status'] = 'no_usable_geometry__'+c.value_status
        else:
            da, db, actual = consecutive_changes(f)
            metrics = rank_correlation(da, db)
            r.update(audit[key]); r['available_consecutive_pairs'] = actual
            r['finite_paired_changes'] = metrics['finite_paired_days']
            r['missing_change_pairs'] = requested-metrics['finite_paired_days']
            r['spearman_change_rho'] = metrics['spearman_rho']
            for source in ['spass','oshd']:
                for out, old in [('unique_changes','unique_paired_values'),('tied_changes','tied_paired_days'),('zero_changes','zero_paired_days')]:
                    r[source+'_'+out] = metrics[source+'_'+old]
            r['diagnostic_status'] = metrics['diagnostic_status']
            if metrics['diagnostic_status']=='computed':
                r['diagnostic_status'] = 'computed_complete_change_pairs' if not r['missing_change_pairs'] else 'computed_incomplete_change_pairs'
        rows.append(r)
    result = pd.DataFrame(rows).reindex(columns=DEFS)
    zero = result[result.reference_offset].set_index('station_group_id').spearman_change_rho
    result['rho_difference_from_offset_zero'] = result.spearman_change_rho - result.station_group_id.map(zero)
    master = pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    dictionary = pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    target = ROOT/SUMMARY
    if target.exists():
        summary = json.loads(target.read_text(encoding='utf8'))
        if summary['input_sha256'] != inputs or digest(OUTPUT) != summary['output_sha256'][OUTPUT]:
            raise ValueError('Frozen complementary diagnostic changed; create new stage')
    else:
        if len(master)!=1202 or len(dictionary)!=8216:
            raise ValueError('Unexpected registry baseline')
        write_csv(result, ROOT/OUTPUT)
        lag_summary = {}
        for lag, part in result.groupby('oshd_date_offset_days'):
            rho = part.spearman_change_rho.dropna()
            lag_summary[str(lag)] = dict(retained_groups=len(part), computed_groups=len(rho), missing_groups=int(part.spearman_change_rho.isna().sum()),
                rho_min=float(rho.min()),rho_q25=float(rho.quantile(.25)),rho_median=float(rho.median()),rho_q75=float(rho.quantile(.75)),rho_max=float(rho.max()),
                min_finite_pairs=int(part.finite_paired_changes.min()),max_finite_pairs=int(part.finite_paired_changes.max()),
                level_rho_median=float(part.spearman_daily_level_rho_stage71.median()),
                changed_support_pairs=int(part.support_changed_pairs.sum()))
        summary = dict(date='2026-10-10', input_sha256=inputs, output_sha256={OUTPUT:digest(OUTPUT)},
            prior_registry_rows_and_digest={p:dict(rows=len(f),sha256=row_digest(f)) for p,f in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]},
            rows=len(result),retained_groups=result.station_group_id.nunique(),lag_summary=lag_summary,
            status_counts=result.diagnostic_status.value_counts().to_dict(),native_adjacent_support_checks=sum(v['support_adjacent_pairs_checked'] for v in audit.values()),
            changed_support_pairs=sum(v['support_changed_pairs'] for v in audit.values()),
            rank_ties='average', p_values_or_ci_computed=False,physical_between_model_difference_or_conversion=False,
            source_splicing_or_calibration=False, choose_best_lag=False, daily_level_reference_preserved=True,
            five_own_preentry_winters_unchanged=True, new_clustering_or_effect_fit=False,
            software_versions=dict(python=sys.version.split()[0],pandas=pd.__version__,numpy=np.__version__),decisions=decisions)
        target.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if SOURCE not in set(master.source_id):
        r = dict(source_id=SOURCE,variable_name='native_snow_spearman_consecutive_changes_fixed_lags',
            variable_description='Complementary daily-change rank concordance; preserved daily-level reference; no physical snow agreement or unit proof',
            source_organisation='Thesis derived SLF SPASS/OSHD analysis',source_dataset_name='Frozen Stage70 native common-support means and source-value caches',
            source_page_url='reports/116_DIAGNOSTIC_NEIGE_SPEARMAN_FR.md',retrieval_method='Local hashed outputs/caches only; no external request',retrieval_date='2026-10-10',processed_file=OUTPUT,
            geographic_level='Retained station groups, not independent days or municipalities',temporal_resolution='Consecutive-day changes in single December2022April2023 pilot',
            temporal_start='2022-12-01',temporal_end='2023-04-30',unit='Dimensionless rank rho; source differences SPASS UNKNOWN/OSHD m',
            license='Parent SPASS WSL Data Policy; OSHD CC-BY4.0; OSM ODbL; no new licence assigned',
            transformation_applied='Within-source consecutive differences; both finite endpoints; verified same native footprints; average tied ranks; fixed -1/0/+1 offsets',
            quality_notes='No p-value/CI, gap filling, best lag, unit proof, between-model metre difference, splice, exclusions or profile/effect fit; differencing amplifies noise',notes=CONFIG+'; '+SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([r]).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
    records = []
    for col,(description,unit) in DEFS.items():
        if ((dictionary.table==TABLE)&(dictionary.variable==col)).any():
            continue
        records.append(dict(variable=col,table=TABLE,description=description,unit=unit,data_type=str(result[col].dtype),
            geographic_level='Retained stationgroup',temporal_level='Single pilot winter/fixedlag, not fivewinter preentry feature',source_id=SOURCE,
            raw_or_derived='derived',formula=description,causal_role='Complementary descriptive snow agreement only, no causal estimate',
            missing_share=f'{result[col].isna().mean():.6f}',notes='No gap filling; original units; stable support audit; average ties; groups retained; no iid inference or splice'))
    if records:
        write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['input_sha256','output_sha256','prior_registry_rows_and_digest','decisions']},ensure_ascii=False))


if __name__ == '__main__':
    main()
