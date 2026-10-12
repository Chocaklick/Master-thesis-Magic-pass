"""Approved four original access stops; secure isolated six-city ORS collection."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
for variable in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[variable] = '1'
import pandas as pd
from bs4 import BeautifulSoup
from pyproj import Transformer
from src.data_collection import collect_accessibility_road_matrix as engine
from src.data_collection.collect_braunwald_urban_road_stage90 import register
from src.data_processing.build_public_transport_stop_context import checked_source, load_stops
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.check_national_preparation_stage87 import sha
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

DECISION = 'config/national_multiple_road_access_decision_stage94.json'
PREPARATION = 'reports/flumserberg_urban_road_preparation_stage94.json'
COLLECTION = 'reports/flumserberg_urban_road_collection_stage94.json'
INVENTORY_SOURCE = 'DERIVED_FLUMSERBERG_URBAN_ENDPOINTS_STAGE94'
ROUTE_SOURCE = 'ORS_FLUMSERBERG_URBAN_MATRIX_STAGE94'
OUTPUTS = {'flumserberg_urban_origins_stage94': 'data_interim/flumserberg_urban_origins_stage94.csv',
           'flumserberg_urban_arrivals_stage94': 'data_interim/flumserberg_urban_arrivals_stage94.csv'}
TABLES = {'flumserberg_urban_road_directional_stage94': 'data_processed/flumserberg_urban_road_directional_stage94.csv',
          'flumserberg_urban_road_pairs_stage94': 'data_processed/flumserberg_urban_road_pairs_stage94.csv'}
POINTS = {'8509450': ('Unterterzen (Talstation)', 'valley_feeder'),
          '8509451': ('Oberterzen (Mittelstation)', 'valley_feeder'),
          '8530493': ('Flumserberg Tannenboden', 'higher_ski_departure'),
          '8530496': ('Flumserberg Tannenheim', 'higher_ski_departure')}


def prepare():
    paths = [DECISION, 'src/data_collection/collect_flumserberg_urban_road_stage94.py',
             'data_interim/braunwald_urban_origins_stage90.csv', 'reports/braunwald_urban_road_preparation_stage90.json',
             'config/national_road_arrival_sources_stage94.json', 'config/path_c_analysis.json',
             'config/accessibility_road_routing.json']
    inputs = {p: sha(p) for p in paths}
    decision = json.loads((ROOT / DECISION).read_text(encoding='utf-8'))
    if decision['status'] != 'researcher_validated' or not decision['valley_and_higher_departures_distinguished']:
        raise ValueError('Approved multiple-arrival rule needed')
    meta_path = list((ROOT / 'data_external/source_evidence').glob('NATIONAL_FLUMSERBERG_ARRIVAL_STAGE94_*.metadata.json'))
    if len(meta_path) != 1:
        raise ValueError('Exactly one actual official car-access source required')
    m = json.loads(meta_path[0].read_text(encoding='utf-8'))
    if sha(m['raw_file']) != m['sha256'] or m['http_status'] != 200:
        raise ValueError('Actual official access archive differs')
    text = BeautifulSoup((ROOT / m['raw_file']).read_text(encoding='utf-8'), 'html.parser').get_text(' ', strip=True)
    if not all(name in text for name in ['Unterterzen', 'Oberterzen', 'Tannenheim', 'Tannenboden']):
        raise ValueError('Do not substitute an unverified catalogue/nearest point')
    inputs[m['raw_file']] = m['sha256']; inputs[meta_path[0].relative_to(ROOT).as_posix()] = sha(meta_path[0].relative_to(ROOT))
    archive = checked_source(json.loads((ROOT / paths[5]).read_text(encoding='utf-8')))
    inputs[archive] = sha(archive)
    stops, _, _ = load_stops(archive)
    origins = pd.read_csv(ROOT / paths[2], dtype={'selected_stop_id': str}, float_precision='round_trip')
    if len(origins) != 6:
        raise ValueError('Same six exact approved origins required')
    convert = Transformer.from_crs(2056, 4326, always_xy=True)
    arrivals = []
    for sid, (name, access_class) in POINTS.items():
        part = stops[stops.Numero.eq(sid)]
        if len(part) != 1 or part.iloc[0].Nom != name:
            raise ValueError('Original BAV ID/name differs ' + sid)
        p = part.iloc[0]; lon, lat = convert.transform(float(p.E), float(p.N))
        arrivals.append(dict(access_point_id='ACCESS_DESC__flumserberg__' + sid, access_point_name=name,
            station_group_id='DESC_LISTING_PENDING__flumserberg', station_group_name='Flumserberg (périmètre provisoire revu)',
            selected_stop_id=sid, selected_stop_name=name, bav_xtf_id=p.xtf_id,
            bav_easting_2056=float(p.E), bav_northing_2056=float(p.N), coordinate_state_date='2026-09-20',
            road_arrival_longitude=lon, road_arrival_latitude=lat, road_arrival_status='verified_existing_tp_stop_coordinate',
            road_arrival_source_id='NATIONAL_FLUMSERBERG_ARRIVAL_STAGE94', road_arrival_coordinate_source_id='BAV_PUBLIC_TRANSPORT_STOPS_2026',
            winter_access_status='operator_official_car_access_documented_route_winter_unverified',
            final_walk_minutes=None, road_arrival_access_class=access_class, source_id=INVENTORY_SOURCE))
    arrivals = pd.DataFrame(arrivals)
    old = json.loads((ROOT / paths[3]).read_text(encoding='utf-8'))
    protected = old['protected_old_numerical_sha256'] | old['output_sha256']
    for p in ['reports/braunwald_urban_road_collection_stage90.json', 'reports/braunwald_urban_road_reference_stage90_summary.json',
              'reports/national_proxy_support_stage92_summary.json', 'reports/national_common_snow_stage93_summary.json']:
        previous = json.loads((ROOT / p).read_text(encoding='utf-8'))
        protected[p] = sha(p); protected.update(previous['output_sha256'])
    target = ROOT / PREPARATION
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf-8'))
        if previous['input_sha256'] != inputs or previous['protected_old_numerical_sha256'] != protected:
            raise ValueError('Frozen four-arrival preparation differs')
        for p, value in previous['output_sha256'].items():
            if sha(p) != value:
                raise ValueError('Keep edited endpoints rather than overwrite')
        print('Four approved arrivals and unchanged six origins already intact')
        return
    for p, value in protected.items():
        if sha(p) != value:
            raise ValueError('Old numerical output changed ' + p)
    for path, frame in zip(OUTPUTS.values(), [origins, arrivals]):
        write_csv(frame, ROOT / path)
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    sid = m['source_id']
    if sid not in set(master.source_id):
        record = dict(source_id=sid, variable_name='Flumserberg_official_four_car_accesses', variable_description=m['purpose'],
            source_organisation=m['organisation'], source_page_url=m['url'], retrieval_date=m['retrieval_date'],
            local_raw_file=m['raw_file'], retrieval_method='Actual primary GET with archived source and SHA',
            geographic_level='Literal operator arrivals, not visitor origins', temporal_resolution='Current operator information',
            license='Publisher rights, no open licence inferred', quality_notes='Documents access locations, not all winter/legal route geometry or actual travel times')
        write_csv(pd.concat([master, pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    register(INVENTORY_SOURCE, dict(variable_name='Flumserberg_verified_multiple_stop_endpoints', variable_description='Same six city stops and four operator-corroborated original BAV stop coordinates',
        source_organisation='BAV/OFT and Bergbahnen Flumserberg, researcher multiple-access approval', retrieval_date=datetime.now(timezone.utc).isoformat(),
        local_raw_file=m['raw_file'], processed_file='|'.join(OUTPUTS.values()), geographic_level='Six urban origins/four named verified candidate arrivals',
        temporal_resolution='Current coordinates, not historical road access', license='Inherited BAV OGD / publisher attribution',
        transformation_applied='Original BAV coordinates transformed2056to4326; no nearest lift/catalogue/mairie substitution',
        quality_notes='Valley/higher branches distinguished, onward transfers unmeasured, no new independent domain or canonical commune assignment', notes=PREPARATION),
        dict(zip(OUTPUTS, [origins, arrivals])), ['braunwald_urban_origins_stage90', 'braunwald_urban_arrival_stage90'],
        {'road_arrival_access_class': ('Individually documented valley feeder versus higher ski departure, not an arbitrary elevation threshold', 'category')})
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    mask = dictionary.table.isin(OUTPUTS)
    dictionary.loc[mask, 'geographic_level'] = 'Six old urban stop origins and four verified Flumserberg arrival stops'
    dictionary.loc[mask, 'notes'] = 'Car-only stop reference, valley/higher classes separate; upward lifts and final walking missing not zero; no new independent domain acceptance'
    write_csv(dictionary, ROOT / 'metadata/data_dictionary.csv')
    state = dict(prepared_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
        output_sha256={p: sha(p) for p in OUTPUTS.values()}, protected_old_numerical_sha256=protected,
        approved_multiple_access_rule=True, original_stop_ids=list(POINTS), existing_urban_origins=6, ready_arrivals=4)
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Four individually sourced BAV arrivals prepared, six exact origins preserved')


def configure():
    state = json.loads((ROOT / PREPARATION).read_text(encoding='utf-8'))
    for p, value in (state['input_sha256'] | state['output_sha256']).items():
        if sha(p) != value:
            raise ValueError('Frozen endpoints/input changed ' + p)
    engine.OUTPUTS, engine.TABLES = OUTPUTS, TABLES
    engine.SOURCE, engine.INVENTORY_SOURCE = ROUTE_SOURCE, INVENTORY_SOURCE
    engine.ORIGIN_READY = engine.ARRIVAL_READY = 'verified_existing_tp_stop_coordinate'
    engine.PROTECTED = list(state['protected_old_numerical_sha256'])
    engine.SUMMARY = COLLECTION
    engine.CACHE_DIRECTORY = 'data_interim/flumserberg_urban_ors_stage94'
    engine.RAW_DIRECTORY = 'data_external/flumserberg_urban_ors_stage94'
    engine.MEASUREMENT_LABEL = 'six arrêts urbains → quatre accès Flumserberg, voiture seule, vallée/altitude distinguées'
    engine.EXTRA_INPUTS = [DECISION, PREPARATION]
    engine.ENTRY_POINT = 'src/data_collection/collect_flumserberg_urban_road_stage94.py'
    engine.RESUME_COMMAND = '.venv/Scripts/python.exe -X utf8 ' + engine.ENTRY_POINT + ' --execute --max-new-batches 2'
    engine.APPROVED_ZERO_PAIRS = set(); engine.sha = sha


if __name__ == '__main__':
    if sys.argv[1:] == ['--prepare']:
        prepare()
    else:
        configure()
        if '--execute' in sys.argv and (ROOT / COLLECTION).exists():
            p = json.loads((ROOT / COLLECTION).read_text(encoding='utf-8'))
            if any(m.get('http_status') in [401, 403, 429] for m in p['failures']):
                raise ValueError('Retain refusal/quota stop, never automatically retry')
        engine.main()
