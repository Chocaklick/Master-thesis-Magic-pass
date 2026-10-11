"""Approved SPASS-only own five-winter profiles, with exact native lengths.

Reuse old selected-cell caches, including the 2022/23 pilot. New older-month
reads use the unchanged frozen reader in a separate cache namespace. No OSHD
values, source mixing, missing imputation, group removal or new model fit.
"""
import os
for name in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[name] = '1'
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys

import netCDF4
import numpy as np
import pandas as pd
netCDF4.set_chunk_cache(1048576, 101, 0.75)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import src.data_processing.compare_snow_multiwinter_stage76 as reader
from src.data_collection.collect_oshd_multiwinter_stage76 import single_collector_lock
from src.data_processing.prepare_native_snow_weights_stage69 import digest
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

SOURCE = 'DERIVED_SPASS_PREENTRY_PROFILES_STAGE77'
CONFIG = 'config/spass_preentry_decisions_stage77.json'
PRODUCER = 'src/data_processing/build_spass_preentry_profiles_stage77.py'
WINDOWS = 'data_processed/winter_profile_approved_snow_windows_stage57.csv'
WEIGHTS = 'data_processed/native_snow_cell_pairs_stage69.csv'
GROUPS = 'data_processed/native_snow_weight_coverage_stage69.csv'
CACHE = ROOT/'data_interim/spass_preentry_stage77'
SUMMARY = 'reports/spass_preentry_profiles_stage77_summary.json'
OUTPUTS = {
    'spass_preentry_winter_stage77': 'data_processed/spass_preentry_winter_stage77.csv',
    'spass_preentry_profiles_stage77': 'data_processed/spass_preentry_profiles_stage77.csv',
}
DEFS = {
    'source_id': ('Derived SPASS-only profile source', 'identifier'),
    'parent_source_id': ('Original SPASS source, no OSHD snow values', 'identifier'),
    'station_group_id': ('Unchanged retained group ID, not municipality', 'identifier'),
    'station_group_name': ('Preserved group name, not sole key', 'text'),
    'group_retained': ('True even when snow or geometry is missing', 'boolean'),
    'first_base_entry_month': ('Original group entry, never moved to obtain coverage', 'month'),
    'winter_start_year': ('December year of own strictly preentry winter', 'year'),
    'winter_start_date': ('Original requested December1 date', 'date'),
    'winter_end_date': ('Original requested April30 date', 'date'),
    'expected_days': ('All requested December-April days, leap day included', 'days'),
    'spass_calendar_within_archive': ('Whole requested winter within archive; not cell availability', 'boolean'),
    'geometry_available': ('Verified mapped axes available, not exhaustive domain certification', 'boolean'),
    'geometry_status': ('Preserved native-weight geometry status', 'text'),
    'status': ('Complete/partial observed result or explicit missing reason, never a sample filter', 'text'),
    'observed_days': ('Days with positive finite SPASS piste length', 'days'),
    'missing_days': ('Requested minus observed days; unknown if geometry is absent', 'days'),
    'spass_winter_mean_m': ('Mean of observed finite daily piste means; no missing-day imputation', 'metres, assumed'),
    'min_observed_length_share': ('Minimum SPASS observed length share over requested days; not OSHD common support', 'fraction'),
    'mean_observed_length_share': ('Mean SPASS observed length share over requested days', 'fraction'),
    'negative_value_days': ('Days containing negative SPASS values; retained and flagged', 'days'),
    'all_requested_days_observed': ('All calendar days have a finite daily mean', 'boolean'),
    'all_axis_length_observed': ('All source values on the mapped axes observed on every requested day', 'boolean'),
    'spass_original_unit': ('Original UNKNOWN declaration preserved', 'text'),
    'spass_metres_assumed': ('User-approved metre interpretation, not producer certification', 'boolean'),
    'source_spliced_or_calibrated': ('False: SPASS-only, no OSHD fill or calibration', 'boolean'),
    'current_proxy_not_verified_preentry': ('Current pistes retain historical uncertainty', 'boolean'),
    'requested_winter_count': ('Five own preentry winters, never reduced for missing data', 'count'),
    'calendar_winter_count': ('Own winters entirely inside SPASS archive, independently of geometry', 'count'),
    'observed_winter_count': ('Own winter means actually available; not independent resorts', 'count'),
    'spass_five_preentry_winters_mean_m': ('Arithmetic mean of exactly five observed winter means; NA if any is absent', 'metres, assumed'),
    'missing_winter_start_years': ('Own winters without finite mean, all reasons retained', 'years'),
    'first_preentry_winter_start_date': ('Earliest original own winter date', 'date'),
    'last_preentry_winter_end_date': ('Latest original own winter end, strictly before entry', 'date'),
}


def collapse_weights(pairs):
    """Collapse subdivisions only; retain the exact sum of unique axis lengths."""
    if not pairs.spass_cell_in_grid.all():
        raise ValueError('Outside SPASS grid needs explicit spatial handling')
    if not np.isfinite(pairs.unique_axis_length_m).all() or not pairs.unique_axis_length_m.gt(0).all():
        raise ValueError('Require finite positive unique lengths')
    cols = ['station_group_id', 'spass_e_index', 'spass_n_index']
    return pairs.groupby(cols, sort=True).unique_axis_length_m.agg(lambda x: math.fsum(x)).reset_index()


def daily_metric(values, lengths):
    values, lengths = np.asarray(values, dtype=float), np.asarray(lengths, dtype=float)
    if values.shape != lengths.shape or not np.isfinite(lengths).all() or not (lengths > 0).all():
        raise ValueError('Aligned values and positive finite piste lengths required')
    finite = np.isfinite(values)
    observed = math.fsum(lengths[finite])
    return dict(spass_daily_mean_m=math.fsum(values[finite]*lengths[finite])/observed if observed else None,
                observed_length_share=observed/math.fsum(lengths),
                all_axis_length_observed=bool(finite.all()),
                negative_length_m=math.fsum(lengths[finite & (values < 0)]))


def winter_metric(daily, expected_days):
    if daily.civil_date.duplicated().any() or len(daily) != expected_days:
        raise ValueError('One record per requested calendar day required')
    means = daily.spass_daily_mean_m.to_numpy(dtype=float)
    finite = means[np.isfinite(means)]
    return dict(observed_days=len(finite), missing_days=expected_days-len(finite),
                spass_winter_mean_m=math.fsum(finite)/len(finite) if len(finite) else None,
                min_observed_length_share=float(daily.observed_length_share.min()),
                mean_observed_length_share=math.fsum(daily.observed_length_share)/expected_days,
                negative_value_days=int(daily.negative_length_m.gt(0).sum()),
                all_requested_days_observed=len(finite) == expected_days,
                all_axis_length_observed=bool(daily.all_axis_length_observed.all()))


def five_metric(winters):
    if len(winters) != 5 or winters.winter_start_year.duplicated().any():
        raise ValueError('Exactly five distinct own winter records required')
    ordered = winters.sort_values('winter_start_year')
    years = ordered.winter_start_year.to_numpy(dtype=int)
    if not np.all(np.diff(years) == 1) or not (pd.to_datetime(ordered.winter_end_date) < pd.to_datetime(ordered.first_base_entry_month)).all():
        raise ValueError('Five consecutive strictly preentry windows required')
    values = ordered.spass_winter_mean_m.to_numpy(dtype=float)
    good = np.isfinite(values)
    return dict(requested_winter_count=5, calendar_winter_count=int(ordered.spass_calendar_within_archive.sum()),
                observed_winter_count=int(good.sum()),
                spass_five_preentry_winters_mean_m=math.fsum(values)/5 if good.all() else None,
                missing_winter_start_years='|'.join(str(y) for y in years[~good]),
                first_preentry_winter_start_date=ordered.winter_start_date.iloc[0],
                last_preentry_winter_end_date=ordered.winter_end_date.iloc[-1])


def cached_pilot(indices, spass):
    """Reuse SPASS cells alone; do not reuse a mean conditioned on OSHD masks."""
    parent = json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
    meta_path = 'data_interim/native_snow_values_stage70/spass_pilot.json'
    path = 'data_interim/native_snow_values_stage70/spass_pilot.npz'
    meta = json.loads((ROOT/meta_path).read_text(encoding='utf8'))
    expected = parent['source_value_checkpoints']['spass_pilot']
    if meta != expected or digest(path) != meta['cache_sha256']:
        raise ValueError('Frozen pilot source-cell cache changed')
    contract = meta['contract']
    if (contract['indices'] != indices.tolist() or contract['source_file'] != spass['spass_raw_file']
            or contract['source_sha256'] != spass['spass_netcdf_sha256'] or meta['unit'] != 'UNKNOWN'
            or contract['producer_sha256'] != digest('src/data_processing/extract_native_snow_values_stage70.py')):
        raise ValueError('Frozen pilot SPASS contract changed')
    dates_path = 'data_processed/native_snow_date_pairs_stage69.csv'
    if digest(dates_path) != parent['input_sha256'][dates_path]:
        raise ValueError('Frozen pilot calendar changed')
    dates = pd.read_csv(ROOT/dates_path)
    dates = dates[dates.oshd_date_offset_days.eq(0)].sort_values('spass_time_index')
    if dates.spass_time_index.tolist() != contract['times'] or dates.spass_civil_date.duplicated().any():
        raise ValueError('Pilot dates and original selected cells misaligned')
    with np.load(ROOT/path, allow_pickle=False) as cache:
        values = cache['values']
    return dict(zip(dates.spass_civil_date, values)), dict(kind='reuse_original_spass_pilot_cells',
        npz=path, npz_sha256=meta['cache_sha256'], metadata=meta_path, metadata_sha256=digest(meta_path),
        calendar=dates_path, calendar_sha256=digest(dates_path))


def source_month(month, dates, indices, spass, grid):
    old = reader.CACHE
    existing = old/'values'/('spass_'+month+'.json')
    folder = old if existing.exists() else CACHE
    try:
        reader.CACHE = folder
        values, meta = reader.read_selected(spass['spass_raw_file'], spass['spass_netcdf_sha256'], indices,
            dates, 'HSCLQMD', ('time', 'N', 'E'), ('E', 'N'), grid, 'spass_'+month)
    finally:
        reader.CACHE = old
    path = (folder/'values'/('spass_'+month+'.npz')).relative_to(ROOT).as_posix()
    sidecar = Path(path).with_suffix('.json').as_posix()
    return values, dict(kind='reuse_stage76_month' if folder == old else 'stage77_older_month',
                        npz=path, npz_sha256=meta['sha256'], metadata=sidecar, metadata_sha256=digest(sidecar))


def validate_prefixes(snapshot):
    for path, record in snapshot.items():
        frame = pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)
        if row_digest(frame.iloc[:record['rows']]) != record['row_digest']:
            raise ValueError('Historical registry/log prefix changed: '+path)


def register(frames):
    path = ROOT/'metadata/data_sources_master.csv'
    master = pd.read_csv(path, dtype=str, keep_default_na=False)
    if SOURCE not in set(master.source_id):
        record = dict(source_id=SOURCE, variable_name='spass_five_own_preentry_winter_profiles',
            variable_description='Approved SPASS-only exact piste-weighted five preentry winters; absent winter means retained missing',
            source_organisation='Thesis derived from WSL SLF SPASS and verified OSM axes',
            source_dataset_name='Stage77 SPASS-only profiles',
            source_page_url='reports/123_PROFILS_NEIGE_SPASS_PREENTREE_FR.md',
            retrieval_method='Offline verified original selected-cell caches; unchanged reader for older dates',
            retrieval_date='2026-10-11', processed_file='|'.join(OUTPUTS.values()),
            geographic_level='Retained station groups, not overnight-stay municipalities',
            temporal_resolution='Winter and equal-weight own five-preentry-winters',
            temporal_start='2012-12-01', temporal_end='2023-04-30',
            unit='m, researcher-approved SPASS assumption; original UNKNOWN',
            license='SPASS parent WSL Data Policy; geometry OSM ODbL',
            transformation_applied='SPASS native unique piste lengths; observed-day winter mean, equal five winter means only if all exist',
            quality_notes='All70groups retained; current geometry proxy; missing calendar/geometry/values distinct; no OSHD fill',
            notes=SUMMARY+'; requested calendars extend to April2025 but snow values stop at April2023; parent_source_id=SLF_SPASS_HSCLQMD_GRID_1962_2023')
        write_csv(pd.concat([master, pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS).fillna('')], ignore_index=True), path)
    path = ROOT/'metadata/data_dictionary.csv'
    dictionary = pd.read_csv(path, dtype=str, keep_default_na=False)
    additions = []
    for table, frame in frames.items():
        for col in frame:
            if ((dictionary.table == table) & dictionary.variable.eq(col)).any():
                continue
            description, unit = DEFS[col]
            additions.append(dict(variable=col, table=table, description=description, unit=unit,
                data_type=str(frame[col].dtype), geographic_level='Retained station group',
                temporal_level='Own preentry winter' if 'winter_stage' in table else 'Own five preentry winters',
                source_id=SOURCE, raw_or_derived='derived', formula=description,
                causal_role='Candidate preentry snow profile, not estimated causal effect',
                missing_share=f'{frame[col].isna().mean():.6f}', notes=CONFIG+'; current geometry historical caveat'))
    if additions:
        write_csv(pd.concat([dictionary, pd.DataFrame(additions).reindex(columns=DICTIONARY_COLUMNS).fillna('')], ignore_index=True), path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-register', action='store_true')
    args = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    lock_folder = CACHE/'calculation_lock'
    lock_folder.mkdir(exist_ok=True)
    with single_collector_lock(lock_folder):
        run(args)


def run(args):
    decision = json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decision['researcher_reply'] != 'A' or decision['source_spliced_or_calibrated'] or decision['missing_imputation']:
        raise ValueError('Require approved SPASS-only A, without imputation')
    aggregation = json.loads((ROOT/decision['parent_aggregation_decisions']).read_text(encoding='utf8'))
    if not aggregation['snow_daily_observed_mean_per_winter_then_equal_five_winter_mean_approved']:
        raise ValueError('Original aggregation must remain approved')
    parent = json.loads((ROOT/'reports/native_snow_weights_stage69_summary.json').read_text(encoding='utf8'))
    for path in [WEIGHTS, GROUPS]:
        if digest(path) != parent['output_sha256'][path]:
            raise ValueError('Frozen piste lengths or universe changed')
    context = json.loads((ROOT/'reports/connected_profile_context_stage57_summary.json').read_text(encoding='utf8'))
    if digest(WINDOWS) != context['output_sha256'][WINDOWS]:
        raise ValueError('Approved own calendars changed')
    spass = json.loads((ROOT/'reports/snow_grid_metadata_compatibility_stage47.json').read_text(encoding='utf8'))
    inputs_list = [CONFIG, PRODUCER, WINDOWS, WEIGHTS, GROUPS, decision['parent_aggregation_decisions'],
        'reports/preservation_stage76_summary.json', 'reports/connected_profile_context_stage57_summary.json',
        'reports/native_snow_weights_stage69_summary.json', 'reports/snow_grid_metadata_compatibility_stage47.json',
        'reports/native_snow_values_stage70_summary.json', 'src/data_processing/compare_snow_multiwinter_stage76.py']
    contract = {p: digest(p) for p in inputs_list}
    # Original verified once per invocation; no field read/download when cache is reused.
    if digest(spass['spass_raw_file']) != spass['spass_netcdf_sha256']:
        raise ValueError('SPASS original changed')
    contract[spass['spass_raw_file']] = spass['spass_netcdf_sha256']
    snapshot_path = CACHE/'prior_registry.json'
    if snapshot_path.exists():
        snapshot = json.loads(snapshot_path.read_text(encoding='utf8'))
        validate_prefixes(snapshot)
    else:
        snapshot = {}
        for path in ['metadata/data_sources_master.csv', 'metadata/data_dictionary.csv', 'logs/data_collection_log.csv']:
            f = pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)
            snapshot[path] = dict(rows=len(f), row_digest=row_digest(f))
        snapshot_path.write_text(json.dumps(snapshot, indent=2)+'\n', encoding='utf8')
    groups = pd.read_csv(ROOT/GROUPS, float_precision='round_trip')
    windows = pd.read_csv(ROOT/WINDOWS)
    if not groups.station_group_id.is_unique or set(groups.station_group_id) != set(windows.station_group_id):
        raise ValueError('Preserve all exact group IDs')
    if windows.duplicated(['station_group_id', 'winter_start_year']).any() or not windows.groupby('station_group_id').size().eq(5).all():
        raise ValueError('Exactly five unchanged windows per group required')
    weights = collapse_weights(pd.read_csv(ROOT/WEIGHTS, float_precision='round_trip'))
    indices = weights[['spass_e_index', 'spass_n_index']].drop_duplicates().sort_values(['spass_e_index', 'spass_n_index']).to_numpy(dtype=int)
    locations = {tuple(v): i for i, v in enumerate(indices)}
    groupweights = {}
    for gid, f in weights.groupby('station_group_id', sort=False):
        loc = np.array([locations[t] for t in f[['spass_e_index', 'spass_n_index']].itertuples(index=False, name=None)])
        groupweights[gid] = (loc, f.unique_axis_length_m.to_numpy())
    annual = {}; dailyfiles = {}
    eligible = windows[windows.spass_calendar_within_archive & windows.station_group_id.isin(groupweights)]
    for year, target in eligible.groupby('winter_start_year', sort=True):
        year = int(year)
        requested = [str(d.date()) for d in pd.date_range(f'{year}-12-01', f'{year+1}-04-30')]
        path = CACHE/f'daily_{year}.csv'; sidecar = path.with_suffix('.json')
        yearcontract = dict(inputs=contract, station_group_ids=sorted(target.station_group_id.tolist()), requested_dates=requested)
        if sidecar.exists():
            m = json.loads(sidecar.read_text(encoding='utf8'))
            if m['contract'] != yearcontract or digest(path.relative_to(ROOT)) != m['sha256']:
                raise ValueError('Frozen annual SPASS profile cache changed')
            daily = pd.read_csv(path, float_precision='round_trip')
        else:
            if path.exists():
                raise ValueError('Uncheckpointed annual cache retained for review')
            values = {}; checkpoints = []
            if year == 2022:
                values, checkpoint = cached_pilot(indices, spass); checkpoints.append(checkpoint)
            else:
                for month in sorted({d[:7] for d in requested}):
                    selected, checkpoint = source_month(month, [d for d in requested if d.startswith(month)], indices, spass, parent['original_grid_axes']['spass'])
                    values.update(selected); checkpoints.append(checkpoint)
            rows = []
            for gid in sorted(target.station_group_id):
                loc, lengths = groupweights[gid]
                for day in requested:
                    a = values.get(day, np.full(len(indices), np.nan))[loc]
                    rows.append(dict(station_group_id=gid, civil_date=day, **daily_metric(a, lengths)))
            daily = pd.DataFrame(rows)
            write_csv(daily, path)
            m = dict(contract=yearcontract, sha256=digest(path.relative_to(ROOT)), source_checkpoints=checkpoints)
            sidecar.write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        annual[year] = daily
        dailyfiles[str(year)] = dict(path=path.relative_to(ROOT).as_posix(), sha256=m['sha256'],
            metadata=sidecar.relative_to(ROOT).as_posix(), metadata_sha256=digest(sidecar.relative_to(ROOT)),
            source_checkpoints=m['source_checkpoints'])
        (CACHE/'progress.json').write_text(json.dumps(dict(completed_winter_start_years=sorted(annual), input_sha256=contract), indent=2)+'\n', encoding='utf8')
        print('SPASS own-winter cache', year, len(daily), 'group-day rows; resume-safe', flush=True)
    groupmap = groups.set_index('station_group_id')
    records = []
    baseflags = dict(source_id=SOURCE, parent_source_id=decision['source_id'], group_retained=True,
        spass_original_unit='UNKNOWN', spass_metres_assumed=True, source_spliced_or_calibrated=False,
        current_proxy_not_verified_preentry=True)
    for w in windows.itertuples():
        g = groupmap.loc[w.station_group_id]
        available = w.station_group_id in groupweights
        record = {k: getattr(w, k) for k in ['station_group_id', 'first_base_entry_month', 'winter_start_year', 'winter_start_date', 'winter_end_date', 'expected_days', 'spass_calendar_within_archive']}
        record.update(baseflags, station_group_name=g.station_group_name, geometry_available=available,
            geometry_status=g.weight_status, observed_days=np.nan, missing_days=np.nan, spass_winter_mean_m=np.nan,
            min_observed_length_share=np.nan, mean_observed_length_share=np.nan, negative_value_days=np.nan,
            all_requested_days_observed=False, all_axis_length_observed=False)
        if not available:
            record['status'] = 'missing_geometry__'+g.weight_status
        elif not w.spass_calendar_within_archive:
            record.update(status='outside_spass_calendar', observed_days=0, missing_days=w.expected_days)
        else:
            daily = annual[w.winter_start_year]
            daily = daily[daily.station_group_id.eq(w.station_group_id)]
            record.update(winter_metric(daily, w.expected_days))
            record['status'] = ('winter_observed_full_coverage' if record['all_axis_length_observed'] and record['all_requested_days_observed'] else
                'winter_observed_partial_coverage' if record['observed_days'] else 'no_observed_spass_length')
        records.append(record)
    winter = pd.DataFrame(records)
    profiles = []
    for gid, w in winter.groupby('station_group_id', sort=False):
        g = groupmap.loc[gid]
        r = dict(baseflags, station_group_id=gid, station_group_name=g.station_group_name,
            first_base_entry_month=w.first_base_entry_month.iloc[0], geometry_available=gid in groupweights,
            geometry_status=g.weight_status, **five_metric(w))
        r['all_requested_days_observed'] = bool(w.all_requested_days_observed.all())
        r['all_axis_length_observed'] = bool(w.all_axis_length_observed.all())
        r['min_observed_length_share'] = float(w.min_observed_length_share.min())
        r['status'] = ('missing_geometry__'+g.weight_status if gid not in groupweights else
            'incomplete_five_winters' if r['observed_winter_count'] < 5 else
            'five_winters_full_coverage' if r['all_requested_days_observed'] and r['all_axis_length_observed'] else 'five_winters_partial_coverage')
        profiles.append(r)
    frames = dict(zip(OUTPUTS, [winter, pd.DataFrame(profiles)]))
    summary_path = ROOT/SUMMARY
    if summary_path.exists():
        old = json.loads(summary_path.read_text(encoding='utf8'))
        if old['input_sha256'] != contract or any(digest(p) != sha for p, sha in old['output_sha256'].items()):
            raise ValueError('Frozen final SPASS profiles changed; use new version')
    else:
        for table, frame in frames.items():
            write_csv(frame, ROOT/OUTPUTS[table])
        state = dict(date='2026-10-11', completed_at=datetime.now(timezone.utc).isoformat(),
            decisions=decision, input_sha256=contract, output_sha256={p: digest(p) for p in OUTPUTS.values()},
            prior_registry=snapshot, daily_checkpoints=dailyfiles, retained_groups=len(groups),
            winter_rows=len(winter), computable_five_winter_profiles=int(frames['spass_preentry_profiles_stage77'].spass_five_preentry_winters_mean_m.notna().sum()),
            profile_status_counts=frames['spass_preentry_profiles_stage77'].status.value_counts().to_dict(),
            winter_status_counts=winter.status.value_counts().to_dict(), new_external_requests=0,
            source_spliced_or_calibrated=False, clustering_or_new_effect_estimation=False)
        summary_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    if not args.no_register:
        with single_collector_lock(ROOT/'data_interim/oshd_multiwinter_stage76_downloads'):
            register(frames)
    validate_prefixes(snapshot)
    print(json.dumps(dict(retained_groups=len(groups), winter_rows=len(winter),
        computable_five_winter_profiles=int(frames['spass_preentry_profiles_stage77'].spass_five_preentry_winters_mean_m.notna().sum()),
        source_spliced_or_calibrated=False, new_external_requests=0)), flush=True)


if __name__ == '__main__':
    main()
