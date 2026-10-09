"""Audit a separate member snapshot without accepting any group assignments."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.prepare_piste_group_review import relation_inventory
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

TABLE = 'winter_profile_piste_site_membership_audit'
SOURCE = 'DERIVED_PISTE_SITE_MEMBERSHIP_AUDIT_2026_10_09'
OUTPUT = f'data_processed/{TABLE}.csv'
SUMMARY = 'reports/piste_site_membership_audit_summary.json'
DEFS = {
    'osm_site_relation_id': ('Original site relation identifier; not canonical station group', 'identifier'),
    'osm_site_name': ('Original site name; may cover only one component or nordic scope', 'name'),
    'initial_selected_downhill_way_count': ('Unique downhill ways tagged in initial country query', 'count'),
    'completed_selected_downhill_way_count': ('Unique downhill ways after explicit referenced-member tag completion; not accepted group pistes', 'count'),
    'added_downhill_way_ids': ('Referenced downhill identifiers absent from initial country selection; not automatically geographically clipped or assigned', 'identifiers'),
    'known_nordic_way_member_count': ('Unique recursively referenced known ways tagged nordic, including compound nordic tags', 'count'),
    'known_aerialway_member_count': ('Unique known referenced lift ways; neither altitude nor aspect proxy', 'count'),
    'remaining_unresolved_way_relation_count': ('Recursive member references still not in either snapshot; not an absence claim', 'count'),
    'remaining_node_reference_count': ('Nodes not requested because downhill line tags sought; retained separately', 'count'),
    'group_assignment_accepted': ('False: no group/site assignment accepted by this inventory', 'boolean'),
    'historical_scope_verified': ('False: both snapshots current, edits are not construction dates', 'boolean'),
    'source_id': ('Derived source registry key', 'identifier'),
    'parent_source_ids': ('Immutable original OSM and referenced member sources', 'identifiers'),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def audit(initial, extra):
    old_keys = {(e['type'], e['id']) for e in initial['elements']}
    new_keys = {(e['type'], e['id']) for e in extra['elements']}
    if old_keys & new_keys or len(new_keys) != len(extra['elements']):
        raise ValueError('Never silently resolve duplicate versions across snapshots')
    combined = {'elements': initial['elements'] + extra['elements']}
    _, first_sites = relation_inventory(initial)
    _, sites = relation_inventory(combined)
    if {s['osm_relation_id'] for s in sites} != {s['osm_relation_id'] for s in first_sites}:
        raise ValueError('Member completion unexpectedly changed site universe')
    index = {(e['type'], e['id']):e for e in combined['elements']}
    first_index = {s['osm_relation_id']:s for s in first_sites}
    rows = []
    for site in sites:
        # relation_inventory removes downhill ways from its outside-selection list.
        known = [index[(m['type'], m['id'])] for m in site['member_references_outside_query'] if (m['type'], m['id']) in index]
        unresolved = [m for m in site['member_references_outside_query'] if (m['type'], m['id']) not in index]
        previous = set(first_index[site['osm_relation_id']]['selected_downhill_way_ids'])
        rows.append(dict(osm_site_relation_id=site['osm_relation_id'], osm_site_name=site['name'],
            initial_selected_downhill_way_count=len(previous), completed_selected_downhill_way_count=len(site['selected_downhill_way_ids']),
            added_downhill_way_ids='|'.join(map(str, sorted(set(site['selected_downhill_way_ids'])-previous))),
            known_nordic_way_member_count=sum(e['type'] == 'way' and 'nordic' in e.get('tags', {}).get('piste:type', '').split(';') for e in known),
            known_aerialway_member_count=sum(e['type'] == 'way' and bool(e.get('tags', {}).get('aerialway')) for e in known),
            remaining_unresolved_way_relation_count=sum(m['type'] in ['way', 'relation'] for m in unresolved),
            remaining_node_reference_count=sum(m['type'] == 'node' for m in unresolved), group_assignment_accepted=False,
            historical_scope_verified=False, source_id=SOURCE,
            parent_source_ids='OSM_DOWNHILL_SWISS_CURRENT_2026_10_09|OSM_PISTE_REFERENCED_MEMBER_TAGS_2026_10_09'))
    return pd.DataFrame(rows), sites


def main():
    parent = json.loads((ROOT / 'reports/piste_group_review_summary.json').read_text(encoding='utf-8'))
    protected = {**parent['input_sha256'], **parent['output_sha256'], **parent['protected_legacy_sha256']}
    for p, expected in protected.items():
        if sha(p) != expected:
            raise ValueError('Protected original changed: ' + p)
    original = json.loads((ROOT / 'data_interim/current_piste_geometry_collection_checkpoint.json').read_text())
    extra = json.loads((ROOT / 'reports/piste_missing_member_collection_summary.json').read_text())
    if extra['status'] != 'complete' or sha(extra['raw_file']) != extra['sha256']:
        raise ValueError('Complete member source required')
    paths = ['src/descriptive/audit_completed_piste_membership.py', 'reports/piste_missing_member_collection_summary.json', original['raw_file'], extra['raw_file']]
    inputs = {p:sha(p) for p in paths}
    if (ROOT / SUMMARY).exists():
        prior = json.loads((ROOT / SUMMARY).read_text())
        if prior['input_sha256'] != inputs or sha(OUTPUT) != prior['output_sha256'][OUTPUT]:
            raise ValueError('Own checkpoint changed; preserve and investigate')
        print('Exact completed membership audit reused, no requests or assignment.')
        return
    frame, sites = audit(json.loads((ROOT / original['raw_file']).read_bytes()), json.loads((ROOT / extra['raw_file']).read_bytes()))
    write_csv(frame, ROOT / OUTPUT)
    source = dict(source_id=SOURCE, variable_name='current_piste_site_membership_audit',
        variable_description='Separate tag completion audit retaining all 238 sites and unreturned recursively referenced IDs',
        source_organisation='Thesis reproducible audit of two immutable OSM responses', retrieval_date='2026-10-09',
        retrieval_method='Original site memberships, added member tags; no geographic acceptance rule',
        local_raw_file='|'.join(paths), processed_file=OUTPUT, geographic_level='OSM piste site, not station/municipality',
        license='OpenStreetMap contributors ODbL', transformation_applied='Unique original way IDs, no duplicated members or silent version overwrite',
        quality_notes='Two current snapshots; source completeness not verified group coverage or preentry geography; no features or exclusions')
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([source]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    fields = [dict(variable=c, table=TABLE, description=DEFS[c][0], unit=DEFS[c][1], data_type=str(frame[c].dtype),
        geographic_level='OSM site, not accepted station group', temporal_level='current membership inventory', source_id=SOURCE,
        raw_or_derived='derived source diagnostic', formula='src/descriptive/audit_completed_piste_membership.py',
        causal_role='source coverage diagnostic, not analytical feature', missing_share=f'{frame[c].isna().mean():.6f}', notes=source['quality_notes']) for c in frame]
    write_csv(pd.concat([dictionary[dictionary.table.ne(TABLE)], pd.DataFrame(fields).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')
    state = dict(date='2026-10-09', site_count=len(frame), original_snapshot=original['osm_snapshot'], member_snapshot=extra['osm_snapshot'],
        unique_referenced_downhill_way_count=len({i for s in sites for i in s['selected_downhill_way_ids']}),
        sites_with_added_downhill_members=int(frame.added_downhill_way_ids.ne('').sum()),
        sites_without_referenced_downhill_members=int(frame.completed_selected_downhill_way_count.eq(0).sum()),
        sites_with_remaining_unresolved_way_relations=int(frame.remaining_unresolved_way_relation_count.gt(0).sum()),
        accepted_assignments=0, features_computed=False, exclusions_applied=False,
        input_sha256=inputs, output_sha256={OUTPUT:sha(OUTPUT)}, protected_legacy_sha256=protected)
    (ROOT / SUMMARY).write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if not k.endswith('sha256')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
