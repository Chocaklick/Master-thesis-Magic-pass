"""Approved communal-stop correction: six delta matrices, legacy files immutable.

Run --prepare once, then --execute --max-new-batches 6. Resume cached deltas;
never repeat the other184 communes' completed requests.
"""
import json
import sys
from pathlib import Path
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_accessibility_road_matrix as engine
from src.data_processing.prepare_accessibility_road_stop_reference import REFINEMENT, sha
from src.data_processing.build_public_transport_stop_context import checked_source, load_stops, exact_metadata
from src.data_processing.register_road_did_outputs import register
from src.data_processing.atomic_csv_output import write_csv

CONFIG = 'config/accessibility_road_did_execution.json'
ORIGIN = 'reports/accessibility_road_lauterbrunnen_origin.csv'
ARRIVALS = 'reports/accessibility_road_stop_arrivals.csv'
PREP = 'reports/accessibility_road_lauterbrunnen_preparation_summary.json'
DELTA_SUMMARY = 'reports/accessibility_road_lauterbrunnen_collection_summary.json'
SUMMARY = 'reports/accessibility_road_stop_corrected_collection_summary.json'
DELTA_TABLES = {f'accessibility_road_lauterbrunnen_{kind}': f'data_processed/accessibility_road_lauterbrunnen_{kind}.csv' for kind in ['directional', 'pairs']}
TABLES = {f'accessibility_road_stop_corrected_{kind}': f'data_processed/accessibility_road_stop_corrected_{kind}.csv' for kind in ['directional', 'pairs']}
CORRECTED_ORIGINS = 'reports/accessibility_road_stop_corrected_origins.csv'
BASE = ['reports/accessibility_road_stop_origins.csv', ARRIVALS,
    'data_processed/accessibility_road_stop_directional.csv', 'data_processed/accessibility_road_stop_pairs.csv',
    'reports/accessibility_road_stop_collection_summary.json', 'reports/accessibility_road_stop_preparation_summary.json',
    'reports/accessibility_road_stop_snapping_summary.json']


def prepare():
    method = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))['communal_stop_override']
    stops, _, _ = load_stops(checked_source(json.loads((ROOT / 'config/path_c_analysis.json').read_text(encoding='utf-8'))))
    match = stops[stops.Numero.eq(method['new_selected_stop_id'])]
    if len(match) != 1 or match.iloc[0].Nom != method['new_selected_stop_name'] or str(match.iloc[0].Commune_Numero) != str(method['municipality_bfs_id']):
        raise ValueError('Exact approved official stop identity not verified')
    origins = pd.read_csv(ROOT / BASE[0], dtype={'selected_stop_id': str})
    row = origins[origins.municipality_bfs_id.eq(method['municipality_bfs_id'])].copy()
    if len(row) != 1 or row.iloc[0].selected_stop_id != method['old_selected_stop_id']:
        raise ValueError('Unexpected baseline communal stop')
    point = match.iloc[0]
    lon, lat = Transformer.from_crs(2056, 4326, always_xy=True).transform(float(point.E), float(point.N))
    replacement = dict(selected_stop_id=point.Numero, selected_stop_name=point.Nom,
        bav_easting_2056=float(point.E), bav_northing_2056=float(point.N), bav_xtf_id=point.xtf_id,
        road_origin_longitude=lon, road_origin_latitude=lat,
        source_id='DERIVED_ACCESSIBILITY_ROAD_LAUTERBRUNNEN_ENDPOINT')
    for key, value in replacement.items():
        row[key] = value
        origins.loc[origins.municipality_bfs_id.eq(method['municipality_bfs_id']), key] = value
    inputs = [CONFIG, *BASE]
    if (ROOT / PREP).exists():
        validate_preparation()
        print('Prepared correction already verified; no file changed.')
        return
    write_csv(row, ROOT / ORIGIN)
    write_csv(origins, ROOT / CORRECTED_ORIGINS)
    source = exact_metadata('BAV_PUBLIC_TRANSPORT_STOPS_2026')
    frames = {'accessibility_road_lauterbrunnen_origin': row, 'accessibility_road_stop_corrected_origins': origins}
    register(replacement['source_id'], dict(variable_name='approved_communal_stop_correction',
        variable_description='BFS584 Grütschalp8507378 replaced by Lauterbrunnen8507384, both driving directions',
        source_organisation='BAV/OFT; researcher-approved correction', source_dataset_name='Official operating-point coordinate reuse',
        source_page_url=source['url'], local_raw_file=source['raw_file'], processed_file=ORIGIN+'|'+CORRECTED_ORIGINS,
        retrieval_method='Existing SHA-verified BAV source, exact Numero/name/commune identity; no download',
        transformation_applied='EPSG2056 to4326 always_xy; only BFS584 coordinates changed; original TP records retained',
        quality_notes='Explicit endpoint exception; TP/car common endpoint comparison no longer exact for BFS584. No other point changed, no winter or legal car certification.'),
        frames, {table: ['accessibility_road_stop_origins'] for table in frames})
    manifest = dict(input_sha256={p: sha(p) for p in inputs}, output_sha256={p: sha(p) for p in [ORIGIN, CORRECTED_ORIGINS]},
        protected_legacy_sha256={p: sha(p) for p in engine.PROTECTED + REFINEMENT + BASE}, approved_override=method,
        coordinate_source_sha256=source['sha256'])
    (ROOT / PREP).write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Verified official Lauterbrunnen8507384; one communal point changed, original endpoints retained.')


def validate_preparation():
    manifest = json.loads((ROOT / PREP).read_text(encoding='utf-8'))
    for p, value in {**manifest['input_sha256'], **manifest['output_sha256'], **manifest['protected_legacy_sha256']}.items():
        if sha(p) != value:
            raise ValueError('Correction preparation/protected file changed: ' + p)


def configure():
    engine.OUTPUTS = {'accessibility_road_lauterbrunnen_origin': ORIGIN, 'accessibility_road_stop_arrivals': ARRIVALS}
    engine.TABLES = DELTA_TABLES
    engine.SOURCE = 'ORS_DRIVING_CAR_LAUTERBRUNNEN_CORRECTION_2026'
    engine.INVENTORY_SOURCE = 'DERIVED_ACCESSIBILITY_ROAD_LAUTERBRUNNEN_ENDPOINT'
    engine.ORIGIN_READY = engine.ARRIVAL_READY = 'verified_existing_tp_stop_coordinate'
    engine.PROTECTED = list(dict.fromkeys(engine.PROTECTED + REFINEMENT + BASE))
    engine.SUMMARY = DELTA_SUMMARY
    engine.CACHE_DIRECTORY = 'data_interim/accessibility_road_lauterbrunnen_ors'
    engine.RAW_DIRECTORY = 'data_external/accessibility_road_lauterbrunnen_ors'
    engine.MEASUREMENT_LABEL = 'arrêt Lauterbrunnen8507384 → arrêts de station, correction communale validée'
    engine.EXTRA_INPUTS = [CONFIG, PREP]
    engine.ENTRY_POINT = 'src/data_collection/collect_accessibility_road_lauterbrunnen.py'
    engine.RESUME_COMMAND = '.venv/Scripts/python.exe '+engine.ENTRY_POINT+' --execute --max-new-batches 6'
    engine.APPROVED_ZERO_PAIRS = set()


def publish():
    validate_preparation()
    delta = json.loads((ROOT / DELTA_SUMMARY).read_text(encoding='utf-8'))
    if delta['actual_directional_cells_returned'] != 150:
        print('Correction not complete; resume delta collector, no corrected full matrix published.')
        return
    for p, value in delta['output_sha256'].items():
        if sha(p) != value:
            raise ValueError('Delta output changed: '+p)
    prior = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8')) if (ROOT / SUMMARY).exists() else None
    if prior:
        for p, value in prior['output_sha256'].items():
            if sha(p) != value:
                raise ValueError('Preserve edited corrected output: '+p)
    frames = {}
    for kind, baseline in [('directional', BASE[2]), ('pairs', BASE[3])]:
        old = pd.read_csv(ROOT / baseline)
        changed = pd.read_csv(ROOT / DELTA_TABLES['accessibility_road_lauterbrunnen_'+kind])
        frame = pd.concat([old[old.municipality_bfs_id.ne(584)], changed], ignore_index=True)
        keys = ['municipality_bfs_id', 'access_point_id'] + (['direction'] if kind == 'directional' else [])
        if frame.duplicated(keys).any() or len(frame) != len(old):
            raise ValueError('Corrected full matrix key/universe differs')
        frame = frame.sort_values(keys).reset_index(drop=True)
        table = 'accessibility_road_stop_corrected_'+kind
        frames[table] = frame
        write_csv(frame, ROOT / TABLES[table])
    register('DERIVED_ACCESSIBILITY_ROAD_STOP_CORRECTED_MATRIX', dict(variable_name='road_stop_reference_with_approved_endpoint_exception',
        variable_description='Full original road matrix with only BFS584 rows replaced by independent corrected measurements',
        source_organisation='Thesis project from archived HeiGIT/OpenStreetMap and BAV observations',
        source_dataset_name='Stop-to-stop road reference, approved Lauterbrunnen endpoint correction',
        retrieval_method='Reuse unchanged184 communes; merge150 newly measured corrected directions',
        local_raw_file=BASE[2]+'|'+BASE[3]+'|'+DELTA_SUMMARY, processed_file='|'.join(TABLES.values()),
        transformation_applied='Replace only BFS584; preserve stable IDs, row source IDs and request/SHA lineage; missing direction remains missing',
        quality_notes='Static graph, car-free/winter/snapping warnings persist. No invented walk, traffic or model zero. Original full matrix preserved.'),
        frames, {table: [table.replace('_corrected_', '_')] for table in frames})
    directional, pairs = frames.values()
    summary = dict(status='corrected_full_reference_published', measurement_label=engine.MEASUREMENT_LABEL,
        corrected_territory_id=584, input_sha256={p: sha(p) for p in [CONFIG, PREP, DELTA_SUMMARY, *BASE]},
        output_sha256={p: sha(p) for p in TABLES.values()}, protected_legacy_sha256=delta['protected_legacy_sha256'],
        directional_rows=len(directional), pairs=len(pairs), usable_pairs=int(pairs.road_reference_minutes.notna().sum()),
        graph_versions=directional[['graph_date', 'engine_version']].drop_duplicates().to_dict('records'),
        route_status_counts=directional.route_status.value_counts().to_dict(), delta_new_requests=delta['new_requests'],
        original_tp_endpoint_changed=False, approved_road_endpoint_exception=True)
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ['status', 'directional_rows', 'pairs', 'usable_pairs', 'route_status_counts']}))
    from src.data_processing import audit_accessibility_road_stop_snapping as audit
    audit.INPUT, audit.COLLECTION = TABLES['accessibility_road_stop_corrected_directional'], SUMMARY
    audit.ENDPOINTS = {'accessibility_road_stop_corrected_origins': CORRECTED_ORIGINS, 'accessibility_road_stop_arrivals': ARRIVALS}
    audit.SOURCE = 'DERIVED_ACCESSIBILITY_ROAD_STOP_CORRECTED_SNAPPING'
    audit.OUTPUTS = {table.replace('_stop_', '_stop_corrected_'): path.replace('_stop_', '_stop_corrected_') for table, path in audit.OUTPUTS.items()}
    audit.SUMMARY = 'reports/accessibility_road_stop_corrected_snapping_summary.json'
    audit.main()


if __name__ == '__main__':
    if sys.argv[1:] == ['--prepare']:
        prepare()
    else:
        validate_preparation()
        configure()
        engine.main()
        publish()
