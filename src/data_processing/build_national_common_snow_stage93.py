"""Common ten winters on six provisional supports; added source cells only."""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from src.data_processing import build_reviewed_spass_profiles_stage83 as reader
from src.data_processing.build_spass_preentry_profiles_stage77 import daily_metric, winter_metric
from src.data_processing.build_common_snow_profiles_stage84 import DEFS as COMMON_DEFS
from src.descriptive.check_national_preparation_stage87 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_collection.collect_braunwald_urban_road_stage90 import register

SOURCE = 'DERIVED_NATIONAL_PROVISIONAL_COMMON_SNOW_STAGE93'
CACHE = ROOT / 'data_interim/national_common_snow_stage93'
OUTPUTS = {t: 'data_processed/' + t + '.csv' for t in ['national_common_snow_winter_stage93', 'national_common_snow_profiles_stage93']}
SUMMARY = 'reports/national_common_snow_stage93_summary.json'
EXTRA = {
    'station_group_id': ('Engine-compatible provisional preparation_unit_id, not an accepted new independent domain', 'identifier'),
    'station_group_name': ('Original provisional candidate label', 'text'),
    'independent_domain_assignment_accepted': ('False: provisional snow metric does not certify independent physical domain or full historical scope', 'boolean'),
    'common_decade_ski_activity_verified': ('Separately documented actual skiing for at least one common winter; not a calculation filter', 'boolean'),
}


def main():
    paths = ['src/data_processing/build_national_common_snow_stage93.py', 'config/descriptive_similarity_scope_stage84.json',
             'config/national_grooming_scope_decision_stage92.json', 'reports/national_proxy_support_stage92_summary.json',
             'data_processed/national_proxy_networks_stage92.csv', 'data_processed/national_proxy_spass_weights_stage92.csv',
             'reports/snow_grid_metadata_compatibility_stage47.json', 'reports/native_snow_weights_stage69_summary.json',
             'src/data_processing/build_reviewed_spass_profiles_stage83.py', 'src/data_processing/build_spass_preentry_profiles_stage77.py']
    contract = {p: sha(p) for p in paths}; inputs = dict(contract)
    settings = json.loads((ROOT / paths[1]).read_text(encoding='utf-8'))
    years = settings['common_winter_start_years']
    if years != list(range(2013, 2023)) or settings['winter_months'] != [12, 1, 2, 3, 4]:
        raise ValueError('Same approved common decade required')
    support = json.loads((ROOT / paths[3]).read_text(encoding='utf-8'))
    for p, value in support['output_sha256'].items():
        if sha(p) != value:
            raise ValueError('Provisional original support edited')
    sp = json.loads((ROOT / paths[6]).read_text(encoding='utf-8'))
    # This exact immutable source was fully SHA-verified in the immediately prior
    # Stage92 support. Avoid a second9GB read; no download or source mutation here.
    if support['input_sha256'].get(sp['spass_raw_file']) != sp['spass_netcdf_sha256']:
        raise ValueError('Prior original source verification absent')
    inputs[sp['spass_raw_file']] = sp['spass_netcdf_sha256']
    grid = json.loads((ROOT / paths[7]).read_text(encoding='utf-8'))['original_grid_axes']['spass']
    groups = pd.read_csv(ROOT / paths[4], float_precision='round_trip').set_index('station_group_id')
    weights = pd.read_csv(ROOT / paths[5], float_precision='round_trip')
    if not weights.spass_cell_in_grid.all():
        raise ValueError('Outside-grid source support needs explicit review')
    indices = weights[['spass_e_index', 'spass_n_index']].drop_duplicates().sort_values(['spass_e_index', 'spass_n_index']).to_numpy(dtype=int)
    positions = {tuple(v): i for i, v in enumerate(indices)}
    group_weights = {gid: (np.array([positions[t] for t in p[['spass_e_index', 'spass_n_index']].itertuples(index=False, name=None)]), p.unique_proxy_axis_length_m.to_numpy()) for gid, p in weights.groupby('station_group_id')}
    CACHE.mkdir(parents=True, exist_ok=True)
    flags = dict(source_id=SOURCE, parent_source_id=sp['spass_source_id'], group_retained=True,
                 spass_original_unit='UNKNOWN', spass_metres_assumed=True, source_spliced_or_calibrated=False,
                 current_proxy_not_verified_preentry=True, not_preentry_feature=True, membership_independent_window=True,
                 independent_domain_assignment_accepted=False)
    records = []; dailyproof = {}; provenance = []
    oldcache = reader.CACHE
    try:
        reader.CACHE = CACHE
        for year in years:
            dates = [str(t.date()) for t in pd.date_range(f'{year}-12-01', f'{year+1}-04-30')]
            path = CACHE / f'daily_{year}.csv'; sidecar = path.with_suffix('.json')
            annual_contract = dict(inputs=contract, groups=sorted(group_weights), dates=dates)
            if sidecar.exists():
                m = json.loads(sidecar.read_text(encoding='utf-8'))
                if m['contract'] != annual_contract or sha(path.relative_to(ROOT)) != m['sha256']:
                    raise ValueError('Frozen yearly provisional cache changed')
                daily = pd.read_csv(path, float_precision='round_trip')
                for p, value in m['source_input_sha256'].items():
                    if sha(p) != value:
                        raise ValueError('Original selected-cell cache edited')
                source_inputs = m['source_input_sha256']; year_provenance = m['monthly_source_reuse']
            else:
                if path.exists():
                    raise ValueError('Retain uncheckpointed output, inspect before any overwrite')
                values = {}; source_inputs = {}; year_provenance = []
                for month in sorted({d[:7] for d in dates}):
                    value, reuse = reader.month_values(month, [d for d in dates if d.startswith(month)], indices, sp, grid, source_inputs)
                    values.update(value); year_provenance.append(reuse)
                rows = []
                for gid, (loc, length) in sorted(group_weights.items()):
                    for day in dates:
                        rows.append(dict(station_group_id=gid, civil_date=day, **daily_metric(values[day][loc], length)))
                daily = pd.DataFrame(rows); write_csv(daily, path)
                m = dict(contract=annual_contract, sha256=sha(path.relative_to(ROOT)), source_input_sha256=source_inputs,
                         monthly_source_reuse=year_provenance)
                sidecar.write_text(json.dumps(m, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            inputs.update(source_inputs); provenance.extend(year_provenance)
            dailyproof[str(year)] = dict(path=path.relative_to(ROOT).as_posix(), sha256=m['sha256'],
                metadata=sidecar.relative_to(ROOT).as_posix(), metadata_sha256=sha(sidecar.relative_to(ROOT)))
            for gid, g in groups.iterrows():
                r = flags | dict(station_group_id=gid, station_group_name=g.station_group_name,
                    common_decade_ski_activity_verified=bool(g.common_decade_ski_activity_verified),
                    geometry_available=gid in group_weights,
                    mapped_candidate_axis_length_m=g.full_unique_candidate_axis_length_m,
                    measured_proxy_axis_length_m=g.measured_unique_proxy_axis_length_m,
                    measured_share_of_mapped_candidate_length=g.measured_share_of_mapped_candidate_length,
                    winter_start_year=year, winter_label=f'{year}/{year+1}', winter_start_date=dates[0], winter_end_date=dates[-1], expected_days=len(dates))
                r.update(winter_metric(daily[daily.station_group_id.eq(gid)], len(dates)))
                r['status'] = 'winter_observed_full_coverage' if r['all_axis_length_observed'] and r['all_requested_days_observed'] else 'winter_observed_partial_coverage' if r['observed_days'] else 'no_observed_spass_length'
                records.append(r)
            print('Provisional common winter', year, len(daily), 'actual group-day rows', flush=True)
    finally:
        reader.CACHE = oldcache
    winter = pd.DataFrame(records); profiles = []
    for gid, w in winter.groupby('station_group_id', sort=False):
        g = groups.loc[gid]; means = w.spass_winter_mean_m.to_numpy(dtype=float); good = np.isfinite(means)
        if len(w) != 10 or w.winter_start_year.sort_values().tolist() != years:
            raise ValueError('Exactly ten unchanged winter records needed')
        profiles.append(flags | dict(station_group_id=gid, station_group_name=g.station_group_name,
            common_decade_ski_activity_verified=bool(g.common_decade_ski_activity_verified), geometry_available=gid in group_weights,
            mapped_candidate_axis_length_m=g.full_unique_candidate_axis_length_m, measured_proxy_axis_length_m=g.measured_unique_proxy_axis_length_m,
            measured_share_of_mapped_candidate_length=g.measured_share_of_mapped_candidate_length,
            requested_winter_count=10, observed_winter_count=int(good.sum()), common_ten_winter_mean_m=math.fsum(means)/10 if good.all() else None,
            missing_winter_start_years='|'.join(str(y) for y, v in zip(w.winter_start_year, good) if not v),
            common_period_start_date='2013-12-01', common_period_end_date='2023-04-30', expected_total_days=int(w.expected_days.sum()),
            all_requested_days_observed=bool(w.all_requested_days_observed.all()), all_axis_length_observed=bool(w.all_axis_length_observed.all()),
            min_observed_length_share=float(w.min_observed_length_share.min()),
            status='common_ten_winters_incomplete' if not good.all() else 'common_ten_winters_full_coverage' if w.all_axis_length_observed.all() and w.all_requested_days_observed.all() else 'common_ten_winters_partial_coverage'))
    frames = dict(zip(OUTPUTS, [winter, pd.DataFrame(profiles)])); target = ROOT / SUMMARY
    if target.exists():
        prior = json.loads(target.read_text(encoding='utf-8'))
        if prior['input_sha256'] != inputs or any(sha(p) != h for p, h in prior['output_sha256'].items()):
            raise ValueError('Completed provisional snow results frozen, use another version')
        print('Six provisional common snow profiles already intact, no old cache overwritten')
        return
    for table, frame in frames.items():
        write_csv(frame, ROOT / OUTPUTS[table])
    register(SOURCE, dict(variable_name='six_provisional_national_common_snow_profiles',
        variable_description='Common2013/14–2022/23DecemberApril native piste-weighted SPASS means, exactly ten equally weighted observed winters, six provisional domains not automatically admitted to clustering',
        source_organisation='Thesis from original SLF SPASS and individually reviewed current OSM geometry', retrieval_date=datetime.now(timezone.utc).isoformat(),
        processed_file='|'.join(OUTPUTS.values()), geographic_level='Provisional candidate by common winter, not communal nights or independent daily resorts',
        temporal_resolution='Fixed common decade, never own preentry predictor replacement', unit='Metres under approved assumption, literal sourceUNKNOWNretained',
        license='Inherited WSL Data Policy and OSM ODbL', transformation_applied='Exact unchanged spatial lengths; observed days within winter then equal1/10winter means; original selected-cell cache reuse and only added source cells',
        quality_notes='No OSHD/splicing/imputation, missing/zero kept distinct, unknown ski history and full real-domain coverage still pending; old69profiles immutable', notes=SUMMARY), frames, (), COMMON_DEFS | EXTRA)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False); mask = dictionary.table.isin(OUTPUTS)
    dictionary.loc[mask, 'geographic_level'] = 'Six provisional candidate proxies, not independently accepted new groups or municipal data'
    dictionary.loc[mask, 'temporal_level'] = 'Common2013/14–2022/23DecemberApril, same decade for every candidate'
    dictionary.loc[mask, 'causal_role'] = 'Descriptive common climate proxy only; not preentry/predictive/causal outcome or automatic clustering acceptance'
    dictionary.loc[mask, 'notes'] = 'Native exact spatial weights, equal ten winters, no imputation/OSHD; sourceUNKNOWNmetre assumption retained; partial proxy/historical coverage separated'
    write_csv(dictionary, ROOT / 'metadata/data_dictionary.csv')
    state = dict(completed_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
        output_sha256={p: sha(p) for p in OUTPUTS.values()}, daily_checkpoints=dailyproof, monthly_source_reuse=provenance,
        provisional_candidates=6, common_winter_rows=len(winter), observed_winter_means=int(winter.spass_winter_mean_m.notna().sum()),
        complete_ten_winter_means=int(frames['national_common_snow_profiles_stage93'].common_ten_winter_mean_m.notna().sum()),
        actual_group_date_rows=6*1512, source_unit='UNKNOWN', researcher_metres_assumed=True,
        no_new_external_collection_old_cache_overwrite_or_independent_domain_clustering_acceptance=True)
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in state.items() if k not in ['input_sha256', 'output_sha256', 'daily_checkpoints', 'monthly_source_reuse']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
