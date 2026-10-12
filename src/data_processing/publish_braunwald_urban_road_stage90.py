"""Six city road means and source snapping; no funicular-time invention."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.data_collection.collect_braunwald_urban_road_stage90 import (
    DECISION, PREPARATION, COLLECTION, OUTPUTS, TABLES, ROUTE_SOURCE, register)
from src.data_processing import audit_accessibility_road_stop_snapping as audit
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.check_national_preparation_stage87 import sha

SOURCE = 'DERIVED_BRAUNWALD_URBAN_REFERENCE_STAGE90'
RESULTS = {'braunwald_urban_road_city_reference_stage90': 'data_processed/braunwald_urban_road_city_reference_stage90.csv',
           'braunwald_urban_road_snapping_stage90': 'data_processed/braunwald_urban_road_snapping_stage90.csv'}
SUMMARY = 'reports/braunwald_urban_road_reference_stage90_summary.json'
CITY_DEFS = {
    'resort_id': ('Original catalogue ID retained, not a newly accepted independent domain', 'identifier'),
    'preparation_unit_id': ('Stable provisional national preparation key, physical perimeter still under review', 'identifier'),
    'city_name': ('Original six-city label from Stage57, joined by BFS not names', 'text'),
    'urban_stop_id': ('Exact existing approved BAV urban origin stop', 'identifier'),
    'urban_stop_name': ('Published original urban origin stop name', 'text'),
    'arrival_stop_id': ('Approved BAV8503260funicular valley stop; not mountain chairlift nearest to listing', 'identifier'),
    'arrival_stop_name': ('Published Linthal Braunwaldbahn (Talst.) name', 'text'),
    'outbound_distance_km': ('Original outward model distance divided by1000, not a crow-flight distance', 'kilometres'),
    'return_distance_km': ('Original independent return model distance divided by1000', 'kilometres'),
    'both_directions_available': ('Both driving durations actually usable; not route winter certification or inclusion filter', 'boolean'),
    'urban_max_reported_snap_m': ('Largest service-reported snap observed for this exact city stop in the two directions', 'metres'),
    'arrival_max_reported_snap_m': ('Largest observed service-reported snap for approved valley arrival; no acceptance cutoff', 'metres'),
    'urban_max_geodesic_displacement_m': ('Largest independently computed WGS84 input-to-resolved displacement for urban stop', 'metres'),
    'arrival_max_geodesic_displacement_m': ('Largest independently computed WGS84 input-to-resolved displacement for valley stop', 'metres'),
    'onward_transfer_minutes': ('Unmeasured funicular and onward ski access: missing, never zero or added to car time', 'minutes'),
    'complete_city_to_piste_time': ('Always false: car time ends at valley access, not at actual piste departure', 'boolean'),
    'winter_route_verified': ('False: provider matrix has no geometry to certify all winter/legal route restrictions', 'boolean'),
    'automatic_exclusion': ('Always false: no city, candidate domain or municipality excluded by diagnostic', 'boolean'),
    'graph_dates': ('Literal graph dates actually returned by the independent source matrices', 'dates as supplied'),
    'engine_versions': ('Literal provider engine versions from archived source responses', 'text'),
}


def log_actual_requests():
    path = ROOT / 'logs/data_collection_log.csv'
    log = pd.read_csv(path, dtype=str, keep_default_na=False)
    additions = []
    for p in sorted((ROOT / 'data_external/braunwald_urban_ors_stage90').glob('*.metadata.json')):
        m = json.loads(p.read_text(encoding='utf-8'))
        if sha(m['raw_file']) != m['raw_sha256']:
            raise ValueError('Original response changed before logging')
        if ((log.timestamp == m['retrieval_date']) & log.source_id.eq(ROUTE_SOURCE)).any():
            continue
        success = m['status'] == 'success'
        rows = len(m['payload']['sources']) * len(m['payload']['destinations']) if success else 0
        additions.append(dict(timestamp=m['retrieval_date'], task='stage90_Braunwald_six_city_road_reference',
                              source_id=ROUTE_SOURCE, source='HeiGIT / openrouteservice', source_url=m['endpoint'],
                              **{'URL/API': m['endpoint']}, request='POST matrix request_id=' + m['request_id'],
                              retrieval_method='Secure bounded POST; Authorization never archived; exact payload in safe metadata',
                              HTTP_status='' if m['http_status'] is None else str(m['http_status']),
                              status='downloaded' if success else 'failed', raw_file=m['raw_file'], output_file=m['raw_file'],
                              checksum=m['raw_sha256'], records=str(rows), rows_collected=str(rows), success=str(success),
                              error=m.get('network_error_type') or ('' if success else m['status']),
                              notes='Actual response and safe allowance headers retained; no key, live traffic or invented transfer'))
    if additions:
        write_csv(pd.concat([log, pd.DataFrame(additions).reindex(columns=log.columns)], ignore_index=True).fillna(''), path)


def main():
    collection = json.loads((ROOT / COLLECTION).read_text(encoding='utf-8'))
    log_actual_requests()
    for p, h in collection['output_sha256'].items():
        if sha(p) != h:
            raise ValueError('Collected road output changed ' + p)
    origins, arrivals = [pd.read_csv(ROOT / p, dtype={'selected_stop_id': str}, float_precision='round_trip') for p in OUTPUTS.values()]
    directional, pairs = [pd.read_csv(ROOT / p, float_precision='round_trip') for p in TABLES.values()]
    cities = pd.read_csv(ROOT / 'data_processed/winter_profile_urban_city_detail_stage57.csv')[['municipality_bfs_id', 'city_name']].drop_duplicates()
    decision = json.loads((ROOT / DECISION).read_text(encoding='utf-8'))
    audit.SOURCE = SOURCE
    snaps = list(audit.audit(directional, origins, arrivals).values())[0]
    rows = []
    for p in pairs.merge(cities, validate='one_to_one').itertuples():
        original = origins[origins.municipality_bfs_id.eq(p.municipality_bfs_id)].iloc[0]
        out = directional[directional.municipality_bfs_id.eq(p.municipality_bfs_id) & directional.direction.eq('outbound')].iloc[0]
        back = directional[directional.municipality_bfs_id.eq(p.municipality_bfs_id) & directional.direction.eq('return')].iloc[0]
        urban = snaps[snaps.endpoint_role.eq('communal_stop') & snaps.endpoint_id.eq(str(p.municipality_bfs_id))]
        arrival = snaps[snaps.endpoint_role.eq('station_stop')]
        rows.append(dict(source_id=SOURCE, resort_id='braunwald', preparation_unit_id=decision['preparation_unit_id'],
                         municipality_bfs_id=p.municipality_bfs_id, city_name=p.city_name,
                         urban_stop_id=original.selected_stop_id, urban_stop_name=original.selected_stop_name,
                         arrival_stop_id=decision['selected_stop_id'], arrival_stop_name=decision['selected_stop_name'],
                         outbound_minutes=p.outbound_minutes, return_minutes=p.return_minutes, road_reference_minutes=p.road_reference_minutes,
                         outbound_distance_km=out.model_distance_metres / 1000, return_distance_km=back.model_distance_metres / 1000,
                         both_directions_available=pd.notna(p.road_reference_minutes),
                         urban_max_reported_snap_m=urban.reported_snap_distance_metres.max(),
                         arrival_max_reported_snap_m=arrival.reported_snap_distance_metres.max(),
                         urban_max_geodesic_displacement_m=urban.geodesic_displacement_metres.max(),
                         arrival_max_geodesic_displacement_m=arrival.geodesic_displacement_metres.max(),
                         onward_transfer_minutes=None, complete_city_to_piste_time=False,
                         winter_route_verified=False, automatic_exclusion=False,
                         graph_dates='|'.join(sorted({str(v) for v in [out.graph_date, back.graph_date] if pd.notna(v)})),
                         engine_versions='|'.join(sorted({str(v) for v in [out.engine_version, back.engine_version] if pd.notna(v)}))))
    city = pd.DataFrame(rows)
    inputs = {p: sha(p) for p in [DECISION, PREPARATION, COLLECTION, *OUTPUTS.values(), *TABLES.values(),
              'src/data_processing/publish_braunwald_urban_road_stage90.py', 'data_processed/winter_profile_urban_city_detail_stage57.csv',
              'reports/accessibility_road_stop_corrected_collection_summary.json']}
    target = ROOT / SUMMARY
    complete = len(city) == 6 and city.both_directions_available.all()
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf-8'))
        for p, h in previous['output_sha256'].items():
            if sha(p) != h:
                raise ValueError('Published urban reference edited; preserve user changes')
        if previous['complete_six_city_reference'] and previous['input_sha256'] != inputs:
            raise ValueError('Completed publication is frozen; create a new version')
    else:
        previous = None
    if previous and previous['input_sha256'] == inputs:
        print('Published reference intact; no output recomputation or network request')
        return
    frames = dict(zip(RESULTS, [city, snaps]))
    for table, f in frames.items():
        write_csv(f, ROOT / RESULTS[table])
    register(SOURCE, dict(variable_name='Braunwald_six_city_static_car_reference',
             variable_description='Six existing city stops to validated lower funicular station, directional mean and exact observed snapping; upward leg absent, not zero',
             source_organisation='Thesis derived from BAV and archived HeiGIT / openrouteservice responses',
             retrieval_date=datetime.now(timezone.utc).isoformat(), processed_file='|'.join(RESULTS.values()),
             local_raw_file='|'.join(m['raw_file'] for m in collection['successful_requests']),
             geographic_level='Six urban origins and one validated provisional-domain access stop',
             temporal_resolution='Current static road graph; not historical or real visitor travel times',
             license='Inherited BAV OGD / ORS terms / OpenStreetMap attribution',
             transformation_applied='Separate outbound/return minutes, arithmetic mean if both observed; minimum only identified for all six if all observed; original resolved points not substituted',
             quality_notes='Car leg to Linthal only. Funicular and onward walking/transit missing, no traffic/winter supplement, no automatic exclusion or clustering/canonical exposure change',
             notes=SUMMARY), frames,
             ['braunwald_urban_road_pairs_stage90', 'accessibility_road_stop_snapping_observations'], CITY_DEFS)
    # Registration-only serialized missingness refresh for a resumable partial table;
    # never alter historical dictionary rows or frozen numerical producers/results.
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    changed = False
    for table, f in frames.items():
        for c in f:
            mask = dictionary.table.eq(table) & dictionary.variable.eq(c)
            value = f'{(f[c].isna() | f[c].astype(str).eq("")).mean():.6f}'
            if dictionary.loc[mask, 'missing_share'].iloc[0] != value:
                dictionary.loc[mask, 'missing_share'] = value
                changed = True
    if changed:
        write_csv(dictionary, ROOT / 'metadata/data_dictionary.csv')
    old = json.loads((ROOT / 'reports/accessibility_road_stop_corrected_collection_summary.json').read_text(encoding='utf-8'))
    old_versions = old.get('graph_versions', [])
    observed = city[city.road_reference_minutes.notna()]
    closest = observed.loc[observed.road_reference_minutes.idxmin()] if len(observed) else None
    summary = dict(completed_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
                   output_sha256={p: sha(p) for p in RESULTS.values()}, city_count=6,
                   observed_directional_routes=int(directional.usable_duration_minutes.notna().sum()),
                   complete_six_city_reference=bool(complete), available_city_means=len(observed),
                   minimum_six_city_reference_minutes=float(closest.road_reference_minutes) if complete else None,
                   minimum_available_city_reference_minutes=float(closest.road_reference_minutes) if closest is not None else None,
                   closest_available_city_name=closest.city_name if closest is not None else None,
                   arrival_reported_snap_metres=snaps[snaps.endpoint_role.eq('station_stop')].reported_snap_distance_metres.tolist(),
                   actual_graph_versions=collection['graph_versions'], previous_corrected_road_graph_versions=old_versions,
                   prior_graph_exactly_same=set(tuple(v) for v in collection['graph_versions']) == set((v['graph_date'], v['engine_version']) for v in old_versions),
                   upward_and_piste_transfer_unmeasured_not_zero=True, no_clustering_prediction_or_old_matrix_replacement=True,
                   canonical_69groups_and185territories_unchanged=True)
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k not in ['input_sha256', 'output_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
