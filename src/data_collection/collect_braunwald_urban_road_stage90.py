"""Approved single arrival, six existing cities, isolated resumable ORS engine."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.data_collection import collect_accessibility_road_matrix as engine
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.build_public_transport_stop_context import checked_source, load_stops, exact_metadata
from src.descriptive.check_national_preparation_stage87 import sha

DECISION = 'config/braunwald_urban_arrival_decision_stage90.json'
PREPARATION = 'reports/braunwald_urban_road_preparation_stage90.json'
COLLECTION = 'reports/braunwald_urban_road_collection_stage90.json'
INVENTORY_SOURCE = 'DERIVED_BRAUNWALD_URBAN_ENDPOINTS_STAGE90'
ROUTE_SOURCE = 'ORS_BRAUNWALD_URBAN_MATRIX_STAGE90'
OUTPUTS = {'braunwald_urban_origins_stage90': 'data_interim/braunwald_urban_origins_stage90.csv',
           'braunwald_urban_arrival_stage90': 'data_interim/braunwald_urban_arrival_stage90.csv'}
TABLES = {'braunwald_urban_road_directional_stage90': 'data_processed/braunwald_urban_road_directional_stage90.csv',
          'braunwald_urban_road_pairs_stage90': 'data_processed/braunwald_urban_road_pairs_stage90.csv'}


def register(source, record, frames, parent_tables=(), definitions=None):
    definitions = definitions or {}
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    entries = []
    for table, frame in frames.items():
        if (dictionary.table.eq(table)).any():
            continue
        for column in frame:
            inherited = dictionary[dictionary.table.isin(parent_tables) & dictionary.variable.eq(column)]
            if column in definitions:
                description, unit = definitions[column]
            elif len(inherited):
                description, unit = inherited.iloc[0][['description', 'unit']]
            else:
                raise ValueError('New variable definition required: ' + table + '.' + column)
            entries.append(dict(table=table, variable=column, description=description, unit=unit,
                                data_type=str(frame[column].dtype), geographic_level='Six approved urban stops to one reviewed candidate station access',
                                temporal_level='Current static model, not historical travel time', source_id=source, raw_or_derived='derived',
                                formula=description, causal_role='Descriptive urban access only, no canonical exposure, prediction or clustering assignment',
                                missing_share=f'{(frame[column].isna() | frame[column].astype(str).eq("")).mean():.6f}',
                                notes='Approved car reference ends at Linthal valley station; funicular/foot transfer separate and not invented'))
    if source not in set(master.source_id):
        row = dict(record, source_id=source)
        write_csv(pd.concat([master, pd.DataFrame([row]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    if entries:
        write_csv(pd.concat([dictionary, pd.DataFrame(entries).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')


def prepare():
    inputs = [DECISION, 'src/data_collection/collect_braunwald_urban_road_stage90.py',
              'reports/braunwald_road_arrival_proposal_stage89.json', 'config/path_c_analysis.json',
              'reports/accessibility_road_stop_corrected_origins.csv', 'data_processed/winter_profile_urban_city_detail_stage57.csv',
              'config/accessibility_road_routing.json', 'reports/preservation_national_stage89_summary.json']
    decision = json.loads((ROOT / DECISION).read_text(encoding='utf-8'))
    proposal = json.loads((ROOT / inputs[2]).read_text(encoding='utf-8'))
    if decision['status'] != 'researcher_validated' or decision['selected_stop_id'] != proposal['proposed_stop_id']:
        raise ValueError('Exact lower stop must be approved, not inferred')
    for p, h in proposal['input_sha256'].items():
        if sha(p) != h:
            raise ValueError('Previously sourced proposal changed ' + p)
    cities = pd.read_csv(ROOT / inputs[5])[['municipality_bfs_id', 'city_name']].drop_duplicates()
    origins = pd.read_csv(ROOT / inputs[4], dtype={'selected_stop_id': str}, float_precision='round_trip')
    origins = origins[origins.municipality_bfs_id.isin(cities.municipality_bfs_id)].sort_values('municipality_bfs_id').copy()
    if len(origins) != 6 or not cities.municipality_bfs_id.is_unique or origins.road_origin_status.ne('verified_existing_tp_stop_coordinate').any():
        raise ValueError('Same six verified urban stop coordinates required')
    bav = exact_metadata('BAV_PUBLIC_TRANSPORT_STOPS_2026')
    archive = checked_source(json.loads((ROOT / 'config/path_c_analysis.json').read_text(encoding='utf-8')))
    stops, _, _ = load_stops(archive)
    point = stops[stops.Numero.eq(decision['selected_stop_id'])]
    if len(point) != 1 or point.iloc[0].Nom != decision['selected_stop_name']:
        raise ValueError('Original BAV identity differs')
    point = point.iloc[0]
    if float(point.E) != proposal['bav_easting_2056'] or float(point.N) != proposal['bav_northing_2056']:
        raise ValueError('Exact published lower-station coordinates differ')
    arrivals = pd.DataFrame([dict(access_point_id=decision['access_point_id'], access_point_name='Braunwald — accès inférieur Linthal',
                                 station_group_id=decision['preparation_unit_id'], station_group_name='Braunwald (périmètre en cours de vérification)',
                                 selected_stop_id=point.Numero, selected_stop_name=point.Nom, bav_xtf_id=point.xtf_id,
                                 bav_easting_2056=float(point.E), bav_northing_2056=float(point.N), coordinate_state_date='2026-09-20',
                                 road_arrival_longitude=proposal['proposed_longitude_wgs84'], road_arrival_latitude=proposal['proposed_latitude_wgs84'],
                                 road_arrival_status='verified_existing_tp_stop_coordinate', road_arrival_source_id='NATIONAL_BRAUNWALD_ARRIVAL_STAGE89',
                                 road_arrival_coordinate_source_id='BAV_PUBLIC_TRANSPORT_STOPS_2026',
                                 winter_access_status='operator_public_car_access_to_Linthal_documented_route_winter_unverified',
                                 final_walk_minutes=None, source_id=INVENTORY_SOURCE)])
    parent = json.loads((ROOT / inputs[-1]).read_text(encoding='utf-8'))
    protected = {r['path']: r['sha256'] for r in parent['checks'] if r['path'].startswith(('data_processed/', 'config/', 'src/'))}
    inputs.append(bav['raw_file'])
    contract = {p: sha(p) for p in inputs}
    target = ROOT / PREPARATION
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf-8'))
        if previous['input_sha256'] != contract or previous['protected_old_numerical_sha256'] != protected:
            raise ValueError('Frozen endpoint preparation differs')
        for p, h in previous['output_sha256'].items():
            if sha(p) != h:
                raise ValueError('Prepared endpoint edited; preserve user changes')
        print('Approved endpoint preparation already intact; no file rewritten')
        return
    for p, h in protected.items():
        if sha(p) != h:
            raise ValueError('Old numerical result/producer changed ' + p)
    for p, frame in zip(OUTPUTS.values(), [origins, arrivals]):
        write_csv(frame, ROOT / p)
    register(INVENTORY_SOURCE, dict(variable_name='approved_Braunwald_urban_stop_endpoints',
             variable_description='Six existing urban stops to approved Linthal funicular base BAV8503260; candidate domain identity still provisional',
             source_organisation='BAV/OFT; documented Sportbahnen Braunwald access; researcher approval', retrieval_date=datetime.now(timezone.utc).isoformat(),
             local_raw_file=bav['raw_file'], processed_file='|'.join(OUTPUTS.values()), geographic_level='Urban stop and approved candidate station access point',
             license='Inherited BAV OGD and operator attribution', transformation_applied='Reuse exact six old origins and exact approved BAV station coordinate; no new origin selection',
             quality_notes='Car leg only; upward funicular and onward ski access unmeasured; no new independent domain/municipality assignment', notes=PREPARATION),
             dict(zip(OUTPUTS, [origins, arrivals])), ['accessibility_road_stop_origins', 'accessibility_road_stop_arrivals'],
             {'station_group_id': ('Engine-compatible field contains stable provisional preparation_unit_id, not an approved new connected station group', 'identifier'),
              'station_group_name': ('Readable candidate domain name with identity/perimeter still under review', 'text')})
    state = dict(prepared_at=datetime.now(timezone.utc).isoformat(), input_sha256=contract,
                 output_sha256={p: sha(p) for p in OUTPUTS.values()}, protected_old_numerical_sha256=protected,
                 approved_arrival_stop_id=point.Numero, existing_urban_origin_count=6, no_old_result_or_origin_changed=True)
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Six unchanged city stops and approved lower funicular arrival prepared')


def configure():
    state = json.loads((ROOT / PREPARATION).read_text(encoding='utf-8'))
    for p, h in state['input_sha256'].items() | state['output_sha256'].items():
        if sha(p) != h:
            raise ValueError('Prepared inputs/results differ ' + p)
    engine.OUTPUTS, engine.TABLES = OUTPUTS, TABLES
    engine.SOURCE, engine.INVENTORY_SOURCE = ROUTE_SOURCE, INVENTORY_SOURCE
    engine.ORIGIN_READY = engine.ARRIVAL_READY = 'verified_existing_tp_stop_coordinate'
    engine.PROTECTED = list(state['protected_old_numerical_sha256'])
    engine.SUMMARY = COLLECTION
    engine.CACHE_DIRECTORY = 'data_interim/braunwald_urban_ors_stage90'
    engine.RAW_DIRECTORY = 'data_external/braunwald_urban_ors_stage90'
    engine.MEASUREMENT_LABEL = 'six arrêts urbains → Linthal Braunwaldbahn (Talst.), étape automobile seule'
    engine.EXTRA_INPUTS = [DECISION, PREPARATION]
    engine.ENTRY_POINT = 'src/data_collection/collect_braunwald_urban_road_stage90.py'
    engine.RESUME_COMMAND = '.venv/Scripts/python.exe -X utf8 ' + engine.ENTRY_POINT + ' --execute --max-new-batches 2'
    engine.APPROVED_ZERO_PAIRS = set()
    engine.sha = sha  # Existing algorithm, bounded streaming hashes rather than whole-file reads.


if __name__ == '__main__':
    if sys.argv[1:] == ['--prepare']:
        prepare()
    else:
        configure()
        if '--execute' in sys.argv and (ROOT / COLLECTION).exists():
            previous = json.loads((ROOT / COLLECTION).read_text(encoding='utf-8'))
            if any(f.get('http_status') in [401, 403, 429] for f in previous['failures']):
                raise ValueError('Retain provider refusal/quota stop; no automatic retry')
        engine.main()
