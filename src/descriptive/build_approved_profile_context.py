"""Apply stage43 approved urban minimum and five preentry winter calendars.

No snow extraction/aggregation, geometry inference, sample filter or class fit.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.descriptive.audit_five_dimension_profile_availability import last_preentry_winter, expected_days

CONFIG = 'config/winter_profile_operational_decisions_stage43.json'
SUMMARY = 'reports/approved_profile_context_summary.json'
SOURCE = 'DERIVED_APPROVED_PROFILE_CONTEXT_2026_10_09'
INPUTS = [CONFIG, 'data_processed/winter_profile_five_dimension_groups.csv',
    'data_processed/accessibility_road_did_group_reference.csv',
    'reports/accessibility_road_stop_origins.csv',
    'reports/accessibility_road_final_snapping_endpoints.csv',
    'reports/five_dimension_profile_availability_summary.json',
    'reports/snow_gridded_sensitivity_summary.json',
    'src/descriptive/build_approved_profile_context.py']
OUTPUTS = {name: f'data_processed/{name}.csv' for name in [
    'winter_profile_urban_city_detail', 'winter_profile_urban_minimum',
    'winter_profile_approved_snow_windows']}
DEFS = {
    'station_group_id': ('Unchanged connected station group ID', 'identifier'),
    'station_group_name': ('Unchanged station group name', 'name'),
    'first_base_entry_month': ('Group base entry from the preceding audited group table', 'month'),
    'municipality_bfs_id': ('Approved city BFS ID, not a new hotel outcome unit', 'identifier'),
    'city_name': ('Original city name from retained road origin inventory', 'name'),
    'selected_stop_id': ('Original city communal-stop ID, not mairie coordinates', 'identifier'),
    'selected_stop_name': ('Original city stop name', 'name'),
    'access_point_id': ('Existing selected group access node for this city-group reference', 'identifier'),
    'road_reference_minutes': ('Existing mean of separately calculated outbound and return driving times; group access selection unchanged', 'minutes'),
    'origin_max_snap_metres': ('Largest observed geodesic displacement of city origin in archived matrix snapping audit; not walking time', 'metres'),
    'arrival_max_snap_metres': ('Largest observed geodesic displacement of selected station arrival in archived snapping audit; not walking time', 'metres'),
    'unusable_access_count': ('Original group reference count of unusable access alternatives', 'count'),
    'is_city_minimum': ('City reference equals group minimum exactly; all tied minima retained', 'boolean'),
    'urban_min_road_minutes': ('Minimum of all six approved city-group driving references, without truncation by municipal treatment threshold', 'minutes'),
    'minimum_city_bfs_ids': ('All city IDs attaining minimum, no arbitrary tie breaking', 'identifiers'),
    'minimum_city_names': ('Names of all city minima', 'names'),
    'available_city_count': ('Finite nonnegative observed city references; completeness recorded, not a sample filter', 'count'),
    'all_six_cities_available': ('Whether all six approved city references exist', 'boolean'),
    'current_graph_historical_caveat': ('True: current static road graph is not verified as preentry network', 'boolean'),
    'winter_start_year': ('December year of requested complete preentry winter', 'year'),
    'winter_start_date': ('December1 of requested winter', 'date'),
    'winter_end_date': ('April30 of requested winter, strictly preceding entry', 'date'),
    'expected_days': ('All December-April calendar days, including leap day', 'days'),
    'spass_calendar_within_archive': ('Requested whole winter is within pinned SPASS hydrological archive 1961-09-01 to 2023-08-31; not a valid-cell coverage claim', 'boolean'),
    'snow_mean_computed': ('False: piste spatial scope and aggregation still require definition', 'boolean'),
    'source_id': ('Registered derived context source', 'identifier'),
    'parent_source_ids': ('Registered parents; no new API calls', 'identifiers'),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build_context(groups, road, origins, snaps, city_ids, archive_start, archive_end):
    if not groups.station_group_id.is_unique or len(city_ids) != len(set(city_ids)):
        raise ValueError('Nonunique group or city key')
    road = road[road.municipality_bfs_id.isin(city_ids)].copy()
    if road.duplicated(['municipality_bfs_id', 'station_group_id']).any():
        raise ValueError('Duplicate city-group reference')
    if set(road.station_group_id) - set(groups.station_group_id):
        raise ValueError('Unexpected road group')
    origins = origins[origins.municipality_bfs_id.isin(city_ids)].set_index('municipality_bfs_id')
    if not origins.index.is_unique or set(origins.index) != set(city_ids):
        raise ValueError('Six exact original city origins required')
    snap_keys = snaps.endpoint_role.astype(str) + '|' + snaps.endpoint_id.astype(str)
    if snap_keys.duplicated().any():
        raise ValueError('Ambiguous snapping endpoint')
    snap_map = dict(zip(snap_keys, snaps.max_geodesic_displacement_metres))
    def displacement(role, identifier):
        return snap_map.get(role + '|' + str(identifier), np.nan)
    details, minima, winters = [], [], []
    for g in groups.itertuples():
        selected = road[road.station_group_id.eq(g.station_group_id)].set_index('municipality_bfs_id')
        values = pd.to_numeric(selected.road_reference_minutes, errors='coerce')
        if (values.dropna() < 0).any() or np.isinf(values.dropna()).any():
            raise ValueError('Invalid road time; no invented replacement')
        minimum = values.min()
        tied = sorted(values[values.eq(minimum)].index.tolist())
        minima.append(dict(station_group_id=g.station_group_id, station_group_name=g.station_group_name,
            first_base_entry_month=g.first_base_entry_month, urban_min_road_minutes=minimum,
            minimum_city_bfs_ids='|'.join(map(str, tied)),
            minimum_city_names='|'.join(origins.loc[i, 'municipality_names_source'] for i in tied),
            available_city_count=int(values.notna().sum()), all_six_cities_available=values.notna().sum() == len(city_ids),
            current_graph_historical_caveat=True, source_id=SOURCE,
            parent_source_ids='DERIVED_ACCESSIBILITY_ROAD_DID_2026'))
        for city in sorted(city_ids):
            r = selected.loc[city] if city in selected.index else pd.Series(dtype=object)
            time = values.get(city, np.nan); access = r.get('access_point_id', '')
            details.append(dict(station_group_id=g.station_group_id, municipality_bfs_id=city,
                city_name=origins.loc[city, 'municipality_names_source'],
                selected_stop_id=origins.loc[city, 'selected_stop_id'], selected_stop_name=origins.loc[city, 'selected_stop_name'],
                access_point_id=access, road_reference_minutes=time,
                origin_max_snap_metres=displacement('communal_stop', city),
                arrival_max_snap_metres=displacement('station_stop', access),
                unusable_access_count=r.get('unusable_access_count', np.nan),
                is_city_minimum=bool(pd.notna(time) and time == minimum),
                source_id=SOURCE, parent_source_ids='DERIVED_ACCESSIBILITY_ROAD_DID_2026|DERIVED_ACCESSIBILITY_ROAD_FINAL_SNAPPING'))
        entry = pd.Timestamp(g.first_base_entry_month); last = last_preentry_winter(entry)
        for year in range(last - 4, last + 1):
            start, end = pd.Timestamp(year, 12, 1), pd.Timestamp(year + 1, 4, 30)
            winters.append(dict(station_group_id=g.station_group_id, first_base_entry_month=g.first_base_entry_month,
                winter_start_year=year, winter_start_date=start.date().isoformat(), winter_end_date=end.date().isoformat(),
                expected_days=expected_days(year), spass_calendar_within_archive=start >= archive_start and end <= archive_end,
                snow_mean_computed=False, source_id=SOURCE, parent_source_ids='SLF_SPASS_HSCLQMD_GRID_1962_2023'))
    return dict(zip(OUTPUTS, [pd.DataFrame(details), pd.DataFrame(minima), pd.DataFrame(winters)]))


def register(frames):
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    record = dict(source_id=SOURCE, variable_name='approved_urban_minimum_and_snow_windows',
        variable_description='Approved six-city road minimum and five fully preentry December-April winter calendars',
        source_organisation='Thesis derived context using archived ORS BAV and SLF inputs',
        source_dataset_name='Stage43 approved profile context', retrieval_date='2026-10-09',
        retrieval_method='Local deterministic joins only; no routing or grid extraction', local_raw_file='|'.join(INPUTS),
        processed_file='|'.join(OUTPUTS.values()), geographic_level='unchanged station group; city stop and group access stop',
        temporal_resolution='current static road context; group-specific fully preentry winter calendars',
        transformation_applied='Minimum of six bidirectional means with all ties; five complete winter dates; archived endpoint snap displacement',
        quality_notes='Current road network not verified preentry; no snow means, geometry, imputation, exclusion or clustering; 2023 archive end not filled',
        confidence_level='exact retained route transformation and calendars, not causal certification', license='Inherits parent source terms')
    definitions = []
    for table, frame in frames.items():
        for col in frame:
            description, unit = DEFS[col]
            definitions.append(dict(variable=col, table=table, description=description, unit=unit,
                data_type=str(frame[col].dtype), geographic_level=record['geographic_level'], temporal_level=record['temporal_resolution'],
                source_id=SOURCE, raw_or_derived='derived context or retained source value',
                formula='src/descriptive/build_approved_profile_context.py; approved minimum or exact calendar',
                causal_role='candidate profile context; no final clustering or effect specification',
                missing_share=f'{frame[col].isna().mean():.6f}', notes=record['quality_notes']))
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    write_csv(pd.concat([dictionary[~dictionary.table.isin(frames)], pd.DataFrame(definitions).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh-context', action='store_true', help='Reviewed revision of own derived context only; refuses edited outputs')
    args = parser.parse_args()
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    if not config['urban_six_city_summary_choice_received'] or not config['snow_source_and_baseline_choice_received']:
        raise ValueError('Researcher decisions required')
    previous_audit = json.loads((ROOT / INPUTS[5]).read_text(encoding='utf-8'))
    protected = {**previous_audit['input_sha256'], **previous_audit['output_sha256'], **previous_audit['protected_legacy_sha256']}
    for path, expected in protected.items():
        if sha(path) != expected:
            raise ValueError('Protected historical file changed: ' + path)
    inputs = {p: sha(p) for p in INPUTS}
    if (ROOT / SUMMARY).exists():
        prior = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        if any(sha(p) != v for p, v in prior['output_sha256'].items()):
            raise ValueError('Edited stage43 outputs; preserve and investigate')
        if not args.refresh_context:
            if prior['input_sha256'] != inputs:
                raise ValueError('Changed stage43 inputs require reviewed refresh or new namespace')
            print('Exact stage43 checkpoint reused; no requests, rewrite or snow/class/effect estimation.')
            return
    grid_summary = json.loads((ROOT / INPUTS[6]).read_text(encoding='utf-8'))
    assert grid_summary['source_hydrological_years'] == [1962, 2023]
    frames = build_context(*[pd.read_csv(ROOT / p) for p in INPUTS[1:5]], config['urban_city_bfs_ids'],
        pd.Timestamp('1961-09-01'), pd.Timestamp('2023-08-31'))
    for table, frame in frames.items():
        write_csv(frame, ROOT / OUTPUTS[table])
    register(frames)
    g = frames['winter_profile_urban_minimum']; w = frames['winter_profile_approved_snow_windows']
    summary = dict(status='approved_urban_context_complete_snow_windows_prepared', date='2026-10-09',
        group_count=len(g), city_detail_count=len(frames['winter_profile_urban_city_detail']),
        all_six_city_group_count=int(g.all_six_cities_available.sum()), urban_min_range_minutes=[float(g.urban_min_road_minutes.min()), float(g.urban_min_road_minutes.max())],
        snow_window_count=len(w), spass_archive_end='2023-08-31',
        snow_winters_outside_spass=int((~w.spass_calendar_within_archive).sum()),
        groups_with_requested_snow_winters_outside_spass=sorted(w.loc[~w.spass_calendar_within_archive, 'station_group_id'].unique().tolist()),
        snow_mean_computed=False, clustering_fitted=False, effect_estimation_run=False, automatic_exclusion_applied=False,
        input_sha256=inputs, output_sha256={p: sha(p) for p in OUTPUTS.values()}, protected_legacy_sha256=protected)
    for path, expected in protected.items():
        if sha(path) != expected:
            raise ValueError('Protected file modified during operation: ' + path)
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith('sha256')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
