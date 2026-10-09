"""Audit five approved profile dimensions, without fitting or inventing traits.

Daily snow is re-counted in Dec-Apr fully before base entry. Coverage diagnostics
do not choose a snow baseline, certify existing proxy assignments or drop groups.
"""
import argparse
import calendar
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_FIVE_DIMENSION_AVAILABILITY_2026_10_09'
CONFIG = 'config/winter_profile_five_dimension_audit.json'
SUMMARY = 'reports/five_dimension_profile_availability_summary.json'
INPUTS = {
    'groups': 'data_processed/accessibility_station_groups.csv',
    'master': 'data_processed/resort_master.csv',
    'snow': 'data_processed/resort_snow_station_crosswalk.csv',
    'urban': 'data_processed/resort_transport_accessibility_context.csv',
    'grid': 'data_processed/spass_snow_component_winter.csv',
    'readiness': 'reports/winter_clustering_feature_readiness.csv',
    'road': 'data_processed/accessibility_road_did_group_reference.csv',
    'origins': 'reports/accessibility_road_stop_origins.csv',
}
RAW = 'data_external/source_evidence/SLF_IMIS_DAILY_SNOW_20260920T085732Z.csv'
RAW_META = 'data_external/source_evidence/SLF_IMIS_DAILY_SNOW_20260920T085732Z.metadata.json'
OUTPUTS = {
    'winter_profile_five_dimension_groups': 'data_processed/winter_profile_five_dimension_groups.csv',
    'winter_profile_five_dimension_components': 'data_processed/winter_profile_five_dimension_components.csv',
    'winter_profile_preentry_snow_coverage': 'data_processed/winter_profile_preentry_snow_coverage.csv',
}
DEFINITIONS = {
    'station_group_id': ('Existing unchanged station group ID', 'identifier'),
    'station_group_name': ('Original existing group name', 'name'),
    'resort_id': ('Exact directory component ID; blank for groups without a listing, no name-matched substitution', 'identifier'),
    'first_base_entry_month': ('Existing base-pass entry, not the November winter anchor', 'month'),
    'component_listing_count': ('Original count of unique directory listings in group', 'count'),
    'structural_data_status': ('Original completeness of undated group directory structure', 'category'),
    'current_ski_area_km': ('Original undated component piste length, not historical certification', 'km'),
    'current_number_lifts': ('Original undated component lift count', 'count'),
    'current_altitude_top_m': ('Original component summit altitude, not dominant piste or base altitude', 'metres'),
    'feature_observation_date': ('Original component observation date; UNKNOWN retained', 'date or UNKNOWN'),
    'current_size_fields_complete': ('All existing listed component piste/lift fields present; false with no listing', 'boolean'),
    'current_summit_fields_complete': ('All listed component summit fields present; false with no listing', 'boolean'),
    'verified_preentry_structure': ('Prior full group preentry verification retained; no new date inferred', 'boolean'),
    'piste_base_altitude_available': ('False: no verified base-altitude field or domain geometry in audited inputs', 'boolean'),
    'piste_altitude_distribution_available': ('False: no verified historical piste footprint for altitudinal distribution', 'boolean'),
    'domain_orientation_available': ('False: no verified piste footprint/aspect dataset in audited inputs; lift bearing is not slope aspect', 'boolean'),
    'snow_station_code': ('Original IMIS proxy ID from exact resort crosswalk, selected using 2013-2025 coverage', 'identifier'),
    'snow_station_distance_km': ('Original resort-point to observation-station geographic distance, not slope coverage', 'km'),
    'snow_station_elevation_gap_to_resort_top_m': ('Original station elevation minus component summit altitude', 'metres'),
    'snow_proxy_quality': ('Existing qualitative proxy-quality label, not recomputed or promoted', 'category'),
    'snow_proxy_assignment_historically_verified': ('False: existing full-period/current-geography station selection not approved as historical group assignment', 'boolean'),
    'snow_proxy_component_count': ('Count of listed components with an exact retained snow crosswalk', 'count'),
    'snow_existing_proxy_quality_labels': ('Distinct existing quality labels across listed components', 'categories'),
    'winter_start_year': ('December calendar year of audited Dec-Apr winter', 'year'),
    'winter_end_date': ('April30 of next year; entire winter must precede base entry', 'date'),
    'snow_valid_days': ('Count of source days with numeric nonnegative HS; observed zero valid, invalid/absent days not imputed', 'days'),
    'snow_expected_days': ('Calendar days Dec-Apr, including leap day', 'days'),
    'snow_coverage_share': ('Valid source days divided by calendar days, diagnostic only', 'share'),
    'in_common_five_winter_candidate': ('Winter in five-winter candidate before earliest entry; not chosen baseline', 'boolean'),
    'in_entry_specific_five_winter_candidate': ('Winter in five-winter candidate before this group entry; not chosen baseline', 'boolean'),
    'snow_preentry_winters_with_observations': ('Full-calendar preentry winters having at least one valid source day', 'count'),
    'snow_preentry_winters_coverage_ge_80pct': ('Count of full preentry winter calendars with >=80percent valid days; no exclusion applied', 'count'),
    'snow_preentry_winters_complete': ('Count of full preentry winter calendars with every day observed', 'count'),
    'snow_common5_winters_coverage_ge_80pct': ('Count among common five candidate winters with >=80percent valid days', 'count'),
    'snow_common5_winters_complete': ('Count among common five candidate winters with every day observed', 'count'),
    'snow_entry5_winters_coverage_ge_80pct': ('Count among entry-specific five candidate winters with >=80percent valid days', 'count'),
    'snow_entry5_winters_complete': ('Count among entry-specific five candidate winters with every day observed', 'count'),
    'snow_all_components_common5_80pct': ('Each exact listed component has all five common candidate winters >=80percent coverage; only proxy support', 'boolean'),
    'snow_all_components_entry5_80pct': ('Each exact listed component has all five entry-specific candidate winters >=80percent coverage; only proxy support', 'boolean'),
    'snow_all_components_common5_complete': ('Each exact listed component has every day in all five common candidate winters', 'boolean'),
    'snow_all_components_entry5_complete': ('Each exact listed component has every day in all five entry-specific candidate winters', 'boolean'),
    'snow_group_historical_measurement_verified': ('False: proxy geometry and group aggregation unapproved, even when coverage complete', 'boolean'),
    'existing_grid_component_available': ('Exact component appears in the old SPASS sensitivity; no historical-group or Dec-Apr transfer', 'boolean'),
    'npvm_zone_assignment_status': ('Original exact/nearest-within-municipality zone status', 'category'),
    'npvm_zone_assignment_distance_km': ('Original listing-point to assigned zone displacement', 'km'),
    'road_major_center_travel_time_minutes': ('Original NPVM zone time to quickest of six centres, not the existing station arrival or an ORS trip', 'minutes'),
    'road_major_center_target_name': ('Original NPVM selected centre name', 'name'),
    'npvm_model_reference_date': ('Original dated NPVM2025 model reference', 'date'),
    'npvm_reference_precedes_base_entry': ('Whether model date strictly precedes group base entry; not a network-stability assumption', 'boolean'),
    'urban_context_component_count': ('Count of listed components with nonmissing NPVM car time', 'count'),
    'urban_context_all_components_available': ('All listed components have a modelled car time; false with no listing', 'boolean'),
    'urban_context_all_components_exact_zonal': ('All listed components have exact point-in-zone assignment, not nearest-zone proxy', 'boolean'),
    'urban_context_all_components_predate_entry': ('All listed component model reference dates precede entry', 'boolean'),
    'cached_city_road_reference_count': ('Usable existing bidirectional road group references for the six audited NPVM cities; no city chosen as profile reference', 'count'),
    'cached_city_road_context_all_available': ('All six city selected-stop to group references available in existing approved road matrix', 'boolean'),
    'cached_city_road_profile_selected': ('False: city list, minimum versus multi-pole profile and historical use not approved as clustering protocol', 'boolean'),
    'five_dimension_clustering_ready': ('False while dated structure, piste geometry, snow mapping, urban method and final numerical choices remain unapproved', 'boolean'),
    'source_id': ('Registered derived audit source ID', 'identifier'),
    'parent_source_ids': ('Registered original sources supplying the retained evidence/identity', 'identifiers'),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def winter_end(year):
    return pd.Timestamp(year + 1, 4, 30)


def expected_days(year):
    return 31 + 31 + calendar.monthrange(year + 1, 2)[1] + 31 + 30


def last_preentry_winter(entry):
    year = entry.year - 1
    while winter_end(year) >= entry:
        year -= 1
    return year


def snow_counts(raw, codes):
    raw = raw[raw.station_code.isin(codes)].copy()
    raw['date'] = pd.to_datetime(raw.measure_date, utc=True).dt.tz_localize(None).dt.normalize()
    if raw.duplicated(['station_code', 'date']).any():
        raise ValueError('Duplicate source station-day; do not silently average')
    raw['valid'] = pd.to_numeric(raw.HS, errors='coerce').ge(0)
    raw = raw[raw.date.dt.month.isin([12, 1, 2, 3, 4])]
    raw['winter_start_year'] = raw.date.dt.year.where(raw.date.dt.month.eq(12), raw.date.dt.year - 1)
    return raw.groupby(['station_code', 'winter_start_year']).valid.sum().to_dict()


def build_audit(inputs, counts, first_source_year, city_ids):
    groups, master, snow, urban, grid, readiness = [inputs[k] for k in ['groups', 'master', 'snow', 'urban', 'grid', 'readiness']]
    roads = inputs['road'][inputs['road'].municipality_bfs_id.isin(city_ids)]
    if roads.duplicated(['municipality_bfs_id', 'station_group_id']).any():
        raise ValueError('Cached city-group reference key is not unique')
    master = master.set_index('resort_id'); snow = snow.set_index('resort_id')
    urban = urban.set_index('resort_id'); ready = readiness.set_index('station_group_id')
    if not all(frame.index.is_unique for frame in [master, snow, urban, ready]):
        raise ValueError('Exact ID joins must be unique')
    common_last = last_preentry_winter(pd.to_datetime(groups.first_effective_month).min())
    common_years = set(range(common_last - 4, common_last + 1))
    component_rows, winters, group_rows = [], [], []
    grid_ids = set(grid.resort_id)
    for g in groups.itertuples():
        ids = g.component_resort_ids.split('|') if pd.notna(g.component_resort_ids) else []
        if len(set(ids)) != len(ids) or len(ids) != g.component_listing_count:
            raise ValueError('Component count mismatch; no deduplication or regrouping applied')
        entry = pd.Timestamp(g.first_effective_month)
        entry_last = last_preentry_winter(entry)
        entry_years = set(range(entry_last - 4, entry_last + 1))
        local = []
        for rid in ids:
            if rid not in master.index:
                raise ValueError('Unknown component ID')
            m = master.loc[rid]; s = snow.loc[rid] if rid in snow.index else pd.Series(dtype=object)
            u = urban.loc[rid] if rid in urban.index else pd.Series(dtype=object)
            code = s.get('snow_station_code')
            year_rows = []
            if pd.notna(code):
                for year in range(first_source_year, entry_last + 1):
                    valid = int(counts.get((code, year), 0)); expected = expected_days(year)
                    if valid > expected:
                        raise ValueError('Source day count exceeds calendar')
                    year_rows.append(dict(station_group_id=g.station_group_id, resort_id=rid, snow_station_code=code,
                        winter_start_year=year, winter_end_date=winter_end(year), first_base_entry_month=entry,
                        snow_valid_days=valid, snow_expected_days=expected, snow_coverage_share=valid / expected,
                        in_common_five_winter_candidate=year in common_years,
                        in_entry_specific_five_winter_candidate=year in entry_years,
                        source_id=SOURCE, parent_source_ids='SLF_IMIS_DAILY_SNOW|SLF_IMIS_STATIONS'))
            winters.extend(year_rows)
            def number(predicate, years=None):
                return sum(predicate(r) and (years is None or r['winter_start_year'] in years) for r in year_rows)
            reference_date = pd.to_datetime(u.get('npvm_model_reference_date'), errors='coerce')
            row = dict(station_group_id=g.station_group_id, station_group_name=g.station_group_name,
                resort_id=rid, first_base_entry_month=entry, current_ski_area_km=m.ski_area_km,
                current_number_lifts=m.number_lifts, current_altitude_top_m=m.altitude_top_m,
                feature_observation_date=m.feature_observation_date,
                snow_station_code=code, snow_station_distance_km=s.get('snow_station_distance_km'),
                snow_station_elevation_gap_to_resort_top_m=s.get('snow_station_elevation_gap_to_resort_top_m'),
                snow_proxy_quality=s.get('snow_proxy_quality'), snow_proxy_assignment_historically_verified=False,
                snow_preentry_winters_with_observations=number(lambda r: r['snow_valid_days'] > 0),
                snow_preentry_winters_coverage_ge_80pct=number(lambda r: r['snow_coverage_share'] >= .8),
                snow_preentry_winters_complete=number(lambda r: r['snow_coverage_share'] == 1),
                snow_common5_winters_coverage_ge_80pct=number(lambda r: r['snow_coverage_share'] >= .8, common_years),
                snow_common5_winters_complete=number(lambda r: r['snow_coverage_share'] == 1, common_years),
                snow_entry5_winters_coverage_ge_80pct=number(lambda r: r['snow_coverage_share'] >= .8, entry_years),
                snow_entry5_winters_complete=number(lambda r: r['snow_coverage_share'] == 1, entry_years),
                existing_grid_component_available=rid in grid_ids,
                npvm_zone_assignment_status=u.get('npvm_zone_assignment_status'),
                npvm_zone_assignment_distance_km=u.get('npvm_zone_assignment_distance_km'),
                road_major_center_travel_time_minutes=u.get('road_major_center_travel_time_minutes'),
                road_major_center_target_name=u.get('road_major_center_target_name'),
                npvm_model_reference_date=reference_date,
                npvm_reference_precedes_base_entry=bool(pd.notna(reference_date) and reference_date < entry),
                source_id=SOURCE, parent_source_ids='|'.join(str(x) for x in [m.source_ids, s.get('source_ids'), u.get('transport_source_ids')] if pd.notna(x)))
            component_rows.append(row); local.append(row)
        def every(predicate):
            return bool(local) and all(predicate(r) for r in local)
        group_rows.append(dict(station_group_id=g.station_group_id, station_group_name=g.station_group_name,
            first_base_entry_month=entry, component_listing_count=len(ids), structural_data_status=g.structural_data_status,
            current_size_fields_complete=every(lambda r: pd.notna(r['current_ski_area_km']) and pd.notna(r['current_number_lifts'])),
            current_summit_fields_complete=every(lambda r: pd.notna(r['current_altitude_top_m'])),
            verified_preentry_structure=bool(ready.loc[g.station_group_id, 'verified_preentry_structure']),
            piste_base_altitude_available=False, piste_altitude_distribution_available=False,
            domain_orientation_available=False, snow_proxy_component_count=sum(pd.notna(r['snow_station_code']) for r in local),
            snow_existing_proxy_quality_labels='|'.join(sorted({r['snow_proxy_quality'] for r in local if pd.notna(r['snow_proxy_quality'])})),
            snow_all_components_common5_80pct=every(lambda r: r['snow_common5_winters_coverage_ge_80pct'] == 5),
            snow_all_components_entry5_80pct=every(lambda r: r['snow_entry5_winters_coverage_ge_80pct'] == 5),
            snow_all_components_common5_complete=every(lambda r: r['snow_common5_winters_complete'] == 5),
            snow_all_components_entry5_complete=every(lambda r: r['snow_entry5_winters_complete'] == 5),
            snow_group_historical_measurement_verified=False,
            urban_context_component_count=sum(pd.notna(r['road_major_center_travel_time_minutes']) for r in local),
            urban_context_all_components_available=every(lambda r: pd.notna(r['road_major_center_travel_time_minutes'])),
            urban_context_all_components_exact_zonal=every(lambda r: r['npvm_zone_assignment_status'] == 'exact_point_in_npvm_traffic_zone'),
            urban_context_all_components_predate_entry=every(lambda r: r['npvm_reference_precedes_base_entry']),
            cached_city_road_reference_count=int(roads.loc[roads.station_group_id.eq(g.station_group_id) & roads.road_reference_minutes.notna(), 'municipality_bfs_id'].nunique()),
            cached_city_road_context_all_available=int(roads.loc[roads.station_group_id.eq(g.station_group_id) & roads.road_reference_minutes.notna(), 'municipality_bfs_id'].nunique()) == len(city_ids),
            cached_city_road_profile_selected=False,
            five_dimension_clustering_ready=False, source_id=SOURCE, parent_source_ids=g.source_ids))
    return dict(zip(OUTPUTS, [pd.DataFrame(group_rows), pd.DataFrame(component_rows), pd.DataFrame(winters)])), common_years


def register(frames):
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    record = dict(source_id=SOURCE, variable_name='five_dimension_profile_availability',
        variable_description='Exact group/component availability and raw Dec-Apr preentry snow coverage, no chosen traits or clusters',
        source_organisation='Thesis audit of archived directory, SLF and ARE sources', source_dataset_name='Five-dimension profile feasibility',
        retrieval_date='2026-10-09', retrieval_method='Local exact ID joins and SHA-checked daily snow; no network calls',
        local_raw_file='|'.join([RAW, *INPUTS.values()]), processed_file='|'.join(OUTPUTS.values()),
        geographic_level='existing group; component listing and external snow-station proxy', temporal_resolution='fully preentry Dec-Apr winters and current undated/2025 context',
        transformation_applied='Source-valid day counts; common versus entry-specific five-winter candidate coverage only',
        quality_notes='No imputation or exclusions; future-selected snow crosswalk and current urban model remain qualified; no means, orientation, classes or causal effects fabricated',
        confidence_level='availability and source coverage only', license='Inherits original source terms')
    definitions = []
    for table, frame in frames.items():
        for col in frame:
            description, unit = DEFINITIONS[col]
            definitions.append(dict(variable=col, table=table, description=description, unit=unit,
                data_type=str(frame[col].dtype), geographic_level=record['geographic_level'], temporal_level=record['temporal_resolution'],
                source_id=SOURCE, raw_or_derived='derived diagnostic or retained original field',
                formula='See src/descriptive/audit_five_dimension_profile_availability.py; no approved profile estimate',
                causal_role='coverage/context audit, not approved clustering feature',
                missing_share=f'{frame[col].isna().mean():.6f}', notes=record['quality_notes']))
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    write_csv(pd.concat([dictionary[~dictionary.table.isin(frames)], pd.DataFrame(definitions).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh-audit', action='store_true',
        help='Explicit reviewed revision of this derived availability namespace; never changes old outputs and refuses edited audit files')
    args = parser.parse_args()
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    if not config['availability_audit_approved'] or config['clustering_fit_approved']:
        raise ValueError('Availability-only approval required')
    dependencies = [*INPUTS.values(), RAW, RAW_META, CONFIG, 'src/descriptive/audit_five_dimension_profile_availability.py',
        'data_raw/bergfex_stations_ski_suisse_par_region.csv', 'data_raw/bahnen-winter_2056.gpkg',
        'config/path_c_feature_readiness.json', 'config/spass_snow_grid.json', 'reports/winter_entrant_preparation_summary.json']
    checks = {p: sha(p) for p in dependencies}
    raw_meta = json.loads((ROOT / RAW_META).read_text(encoding='utf-8'))
    if raw_meta['sha256'] != checks[RAW]:
        raise ValueError('Original daily snow checksum failure')
    old = json.loads((ROOT / 'reports/winter_entrant_preparation_summary.json').read_text(encoding='utf-8'))
    protected = {**old['input_sha256'], **old['output_sha256'], **old['protected_legacy_sha256']}
    for p, value in protected.items():
        if sha(p) != value:
            raise ValueError('Protected previous file changed: ' + p)
    if (ROOT / SUMMARY).exists():
        previous = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        for p, value in previous['output_sha256'].items():
            if sha(p) != value:
                raise ValueError('Audit output edited: ' + p)
        if not args.refresh_audit:
            if previous['input_sha256'] != checks:
                raise ValueError('Changed inputs require explicitly reviewed/versioned audit')
            print('Exact stage42 checkpoint reused; no rewrite, collection, feature fit or effect estimation.')
            return
    inputs = {k: pd.read_csv(ROOT / p, low_memory=False) for k, p in INPUTS.items()}
    raw = pd.read_csv(ROOT / RAW, usecols=['station_code', 'measure_date', 'HS'])
    first_year = pd.to_datetime(raw.measure_date, utc=True).min().year
    counts = snow_counts(raw, set(inputs['snow'].snow_station_code.dropna()))
    city_ids = config['cached_urban_reference_inventory']['candidate_city_bfs_ids']
    frames, common = build_audit(inputs, counts, first_year, city_ids)
    city_nodes = inputs['origins'][inputs['origins'].municipality_bfs_id.isin(city_ids)]
    if len(city_nodes) != len(city_ids) or not city_nodes.municipality_bfs_id.is_unique:
        raise ValueError('Candidate city origins must resolve uniquely to existing points')
    # Inventory the actual local geospatial source; a lift layer is not piste geometry.
    with sqlite3.connect((ROOT / 'data_raw/bahnen-winter_2056.gpkg').as_uri() + '?mode=ro', uri=True) as connection:
        layers = connection.execute('select table_name,data_type,identifier from gpkg_contents').fetchall()
    for table, frame in frames.items():
        write_csv(frame, ROOT / OUTPUTS[table])
    register(frames)
    g = frames['winter_profile_five_dimension_groups']; c = frames['winter_profile_five_dimension_components']
    summary = dict(status='approved_availability_audit_complete_operational_choices_pending', date='2026-10-09',
        group_count=len(g), component_count=len(c), raw_snow_rows=len(raw), common_candidate_winter_start_years=sorted(common),
        raw_snow_available_start=str(pd.to_datetime(raw.measure_date, utc=True).min()),
        raw_snow_available_end=str(pd.to_datetime(raw.measure_date, utc=True).max()),
        local_geopackage_layers=layers, group_boolean_counts={col: int(g[col].sum()) for col in g if g[col].dtype == bool},
        existing_snow_proxy_quality_counts=c.snow_proxy_quality.value_counts().to_dict(),
        existing_grid_matched_components=int(c.existing_grid_component_available.sum()),
        npvm_reference_dates=sorted(c.npvm_model_reference_date.dropna().astype(str).unique()),
        cached_city_road_candidate_nodes=city_nodes[['municipality_bfs_id', 'municipality_names_source', 'selected_stop_id', 'selected_stop_name', 'coordinate_state_date']].to_dict('records'),
        cached_city_group_reference_count=int(g.cached_city_road_reference_count.sum()),
        clustering_fitted=False, effect_estimation_run=False, automatic_exclusion_applied=False,
        input_sha256=checks, output_sha256={p: sha(p) for p in OUTPUTS.values()}, protected_legacy_sha256=protected)
    for p, value in protected.items():
        if sha(p) != value:
            raise ValueError('Protected result changed during audit: ' + p)
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith('sha256')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
