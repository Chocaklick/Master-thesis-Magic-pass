"""Individual review of seven closed ways, not station GIS acceptance.

Keep Stage49 unchanged. Four landuse objects have documented area semantics;
one bridge outline has uncertain piste-footprint meaning; school/tunnel roles
remain unresolved. No length, area, invented axis or group removal is applied.
Use --no-register while snow collector writes shared CSVs.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.register_piste_scope_case_evidence import visible_text
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

TABLE = 'winter_profile_closed_piste_review_stage50'
OUTPUT = 'data_processed/' + TABLE + '.csv'
SUMMARY = 'reports/piste_closed_semantics_stage50_summary.json'
SOURCE = 'DERIVED_CLOSED_PISTE_SEMANTICS_STAGE50'


def semantic_review(element):
    tags = element.get('tags', {}); nodes = element.get('nodes', [])
    if not nodes or nodes[0] != nodes[-1] or tags.get('piste:type') != 'downhill' or 'area' in tags:
        raise ValueError('Require the exact retained closed unspecified downhill case')
    if tags.get('landuse') == 'piste':
        return 'implicit_piste_surface_semantics_supported', 'OSM_AREA_CONVENTIONS_STAGE50', 'Closed landuse polygon implies area; no area tag added to original source.'
    if tags.get('man_made') == 'bridge':
        return 'bridge_outline_supported_piste_footprint_unverified', 'OSM_BRIDGE_OUTLINE_CONVENTIONS_STAGE50', 'Structure outline is documented; whole structure is not assumed to equal the piste footprint.'
    return 'school_extent_role_unresolved' if tags.get('amenity') == 'ski_school' else 'tunnel_closed_role_unresolved', 'OSM_DOWNHILL_GEOMETRY_CONVENTIONS_STAGE50', 'Closure and downhill tag do not alone establish an axis or piste surface.'


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--no-register', action='store_true'); args = parser.parse_args()
    paths = ['config/piste_ambiguous_geometry_decisions_stage49.json', 'config/piste_semantics_evidence_stage50.json',
        'src/descriptive/audit_closed_piste_semantics_stage50.py', 'data_interim/current_piste_geometry_collection_checkpoint.json']
    digest = lambda p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
    inputs = {p: digest(p) for p in paths}
    decision = json.loads((ROOT / paths[0]).read_text(encoding='utf-8'))
    if not decision['retain_ambiguous_objects'] or not decision['individual_verification_before_measure_required']:
        raise ValueError('Require approved retention and individual review')
    collection = json.loads((ROOT / paths[-1]).read_text(encoding='utf-8'))
    if digest(collection['raw_file']) != collection['sha256']:
        raise ValueError('Original snapshot changed')
    inputs[collection['raw_file']] = collection['sha256']
    elements = json.loads((ROOT / collection['raw_file']).read_bytes())['elements']
    targets = {e['id']: e for e in elements if e['type'] == 'way' and e['id'] in decision['osm_way_ids']}
    if set(targets) != set(decision['osm_way_ids']):
        raise ValueError('All seven original IDs must remain present')
    documents = []; records = []
    markers = {'OSM_AREA_CONVENTIONS_STAGE50':'assumed to be areas', 'OSM_DOWNHILL_GEOMETRY_CONVENTIONS_STAGE50':'The piste as',
               'OSM_BRIDGE_OUTLINE_CONVENTIONS_STAGE50':'outline of the bridge'}
    for source in json.loads((ROOT / paths[1]).read_text(encoding='utf-8')):
        matches = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
        if len(matches) != 1:
            raise ValueError('Require one archived documentation original')
        meta = json.loads(matches[0].read_text(encoding='utf-8'))
        if meta['url'] != source['url'] or digest(meta['raw_file']) != meta['sha256']:
            raise ValueError('Documentation identity/SHA changed')
        text = visible_text((ROOT / meta['raw_file']).read_text(encoding='utf-8'))
        if markers[source['source_id']] not in text or 'Creative Commons Attribution-ShareAlike 2.0' not in text:
            raise ValueError('Required source semantics/licence marker missing')
        inputs[meta['raw_file']] = meta['sha256']
        documents.append(dict(source_id=source['source_id'], url=source['url'], raw_file=meta['raw_file'], sha256=meta['sha256']))
        records.append(dict(source_id=source['source_id'], variable_name='osm_geometry_tag_semantics', variable_description=source['purpose'],
            source_organisation=source['organisation'], source_dataset_name='Original OSM wiki geometry documentation', source_page_url=source['url'],
            retrieval_date=meta['retrieval_date'], retrieval_method='Archived public HTML, robots and full SHA256; literal documentation review',
            original_file_name=Path(meta['raw_file']).name, local_raw_file=meta['raw_file'], processed_file=SUMMARY,
            geographic_level='Tag conventions, not station boundaries', temporal_resolution='Current documentation with original page edit dates retained',
            license='Wiki content CC-BY-SA2.0 unless otherwise noted; OSM data licence remains separate ODbL',
            transformation_applied='Source marker checks; no geometry/feature substitution', quality_notes='Convention-based interpretation is not verified station scope or historical geometry', notes='sha256=' + meta['sha256']))
    rows = []; cases = []
    for identifier in decision['osm_way_ids']:
        element = targets[identifier]; status, doc, note = semantic_review(element)
        geometry = element['geometry']; coords = [(p['lon'], p['lat']) for p in geometry]
        valid = len(coords) >= 4 and coords[0] == coords[-1] and Polygon(coords).is_valid
        row = dict(osm_way_id=identifier, osm_version=element['version'], osm_edit_timestamp=element['timestamp'],
            parent_source_id=collection['source_id'], documentation_source_id=doc, semantic_review_status=status,
            original_tags_json=json.dumps(element.get('tags', {}), ensure_ascii=False, sort_keys=True),
            node_count=len(element['nodes']), coordinate_count=len(coords), closed_polygon_topology_valid=valid,
            station_group_assignment_verified=False, historical_scope_verified=False, axis_length_computed=False,
            mapped_area_computed=False, review_note=note)
        rows.append(row)
        cases.append(dict(**row, original_geometry=geometry, original_node_ids=element['nodes'],
            original_source_relations=[dict(osm_relation_id=r['id'], original_tags=r.get('tags', {}),
                original_roles=[m.get('role','') for m in r.get('members', []) if m.get('type') == 'way' and m.get('ref') == identifier])
                for r in elements if r['type'] == 'relation' and any(m.get('type') == 'way' and m.get('ref') == identifier for m in r.get('members', []))]))
    frame = pd.DataFrame(rows)
    state = dict(date='2026-10-09', input_sha256=inputs, documents=documents, cases=cases,
        group_count_retained=71, prior_stage49_unchanged=True, accepted_group_assignments=0,
        metrics_computed=False, source_geometry_modified=False, exclusions_applied=False,
        note='Individual semantics review only. Four supported implicit area candidates; bridge piste-footprint and school/tunnel cases remain unverified. No preentry or actual domain claim.')
    if (ROOT / SUMMARY).exists():
        previous = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        if previous['input_sha256'] != inputs or digest(OUTPUT) != previous['output_sha256']:
            raise ValueError('Changed own checkpoint; preserve and review')
    else:
        write_csv(frame, ROOT / OUTPUT); state['output_sha256'] = digest(OUTPUT)
        (ROOT / SUMMARY).write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not args.no_register:
        master_path = ROOT / 'metadata/data_sources_master.csv'; master = pd.read_csv(master_path, dtype=str, keep_default_na=False)
        records = [r for r in records if r['source_id'] not in set(master.source_id)]
        records.append(dict(source_id=SOURCE, variable_name='closed_piste_semantics_review', variable_description='Individual tag/documentation diagnostics on seven retained closed OSM ways',
            source_organisation='Thesis source semantics audit', processed_file=OUTPUT, retrieval_date='2026-10-09',
            retrieval_method='Cached original IDs/tags/SHA and documented geometry conventions', geographic_level='Original OSM object', temporal_resolution='Current source snapshot',
            transformation_applied='Diagnostic only; no area/axis measure or group assignment',
            notes='Parents OSM_DOWNHILL_SWISS_CURRENT_2026_10_09 and three wiki sources; exact hashes in ' + SUMMARY))
        write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), master_path)
        descriptions = ['Original stable OSM way ID','Original version','Original edit timestamp, not construction date','Parent original snapshot ID',
            'Supporting documentation ID','Individual semantic finding, not accepted group assignment','Unmodified literal source tags',
            'Original node count','Original coordinate count','Exact closed polygon topology valid without repair, not domain proof',
            'False: no station group assignment accepted','False: current objects not certified preentry','False: no axis length computed',
            'False: no piste area computed','Short source interpretation and remaining uncertainty']
        fields = [dict(variable=column, table=TABLE, description=description, unit='count' if column in ['node_count','coordinate_count'] else 'diagnostic/identifier/text',
            data_type=str(frame[column].dtype), geographic_level='original OSM way', temporal_level='current source snapshot', source_id=SOURCE,
            raw_or_derived='retained original attribute or source diagnostic', formula='See semantic_review; no length/area aggregation', causal_role='provenance/quality only',
            missing_share=f'{frame[column].isna().mean():.6f}', notes='All seven objects retained, no original tags overwritten, no missing values invented')
            for column, description in zip(frame.columns, descriptions)]
        dictionary_path = ROOT / 'metadata/data_dictionary.csv'; dictionary = pd.read_csv(dictionary_path, dtype=str, keep_default_na=False)
        write_csv(pd.concat([dictionary[dictionary.table.ne(TABLE)], pd.DataFrame(fields).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), dictionary_path)
        events = pd.DataFrame(json.loads((ROOT / 'data_interim/piste_semantics_events_stage50.json').read_text(encoding='utf-8'))).fillna('').astype(str)
        log_path = ROOT / 'logs/data_collection_log.csv'; log = pd.read_csv(log_path, dtype=str, keep_default_na=False)
        events = events.reindex(columns=log.columns, fill_value='')
        existing = set(map(tuple, log.values.tolist())); new_events = events[[tuple(row) not in existing for row in events.values.tolist()]]
        write_csv(pd.concat([log, new_events], ignore_index=True), log_path)
    print('Seven cases individually reviewed; four supported area semantics, three footprint/role uncertainties; no measures or group exclusions.')


if __name__ == '__main__':
    main()
