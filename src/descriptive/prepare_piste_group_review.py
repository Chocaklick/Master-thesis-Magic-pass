"""Exhaustive OSM site/group review queue: no accepted geographic assignment.

All groups and all collected piste-site relations remain in the JSON matrix.
Exact names and closest geometries are review aids, never acceptance rules.
"""
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

TABLE = 'winter_profile_piste_group_review'
SOURCE = 'DERIVED_PISTE_GROUP_REVIEW_2026_10_09'
OUTPUT = f'data_processed/{TABLE}.csv'
DETAIL = 'data_interim/winter_profile_piste_all_site_group_pairs.json'
SUMMARY = 'reports/piste_group_review_summary.json'
INPUTS = ['data_interim/current_piste_geometry_collection_checkpoint.json',
    'data_processed/accessibility_station_groups.csv', 'data_processed/accessibility_station_access_points.csv',
    'data_processed/resort_master.csv', 'reports/terrain_snow_source_feasibility_summary.json',
    'src/descriptive/prepare_piste_group_review.py']
DEFS = {
    'station_group_id': ('Unchanged connected group ID', 'identifier'),
    'station_group_name': ('Original connected group name', 'name'),
    'reference_point_count': ('Existing group reference points, not new road endpoints or piste footprint', 'count'),
    'exact_name_site_relation_ids': ('All OSM site relations matching normalized full original group/component/entry names; review only', 'identifiers'),
    'exact_name_site_count': ('Count of exact-name site suggestions; not verified matches', 'count'),
    'nearest_referenced_geometry_site_relation_ids': ('All tied site relations closest to existing group reference points among sites with collected downhill member geometry; not accepted assignments', 'identifiers'),
    'minimum_reference_to_site_geometry_metres': ('EPSG2056 straight-line minimum from retained station reference points to referenced downhill geometries; not road/walk time or analytical cutoff', 'metres'),
    'exact_name_and_nearest_site_relation_ids': ('Overlap of two review aids; still not accepted or coverage certified', 'identifiers'),
    'current_site_assignment_verified': ('False: neither exact names nor proximity alone verify site scope', 'boolean'),
    'historical_piste_scope_verified': ('False: current site membership/edit timestamps do not prove preentry scope', 'boolean'),
    'piste_feature_computed': ('False: no slope length, altitude, aspect or snow group feature computed', 'boolean'),
    'review_status': ('All groups require independent operator/scope validation; none removed', 'status'),
    'source_id': ('Registered derived review source', 'identifier'),
    'parent_source_ids': ('Registered retained geometry and reference point parents', 'identifiers'),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def normalized(text):
    decomposed = unicodedata.normalize('NFKD', str(text))
    return ' '.join(''.join(c.lower() if c.isalnum() else ' ' for c in decomposed if not unicodedata.combining(c)).split())


def relation_inventory(payload):
    ways = {e['id']: e for e in payload['elements'] if e['type'] == 'way' and e.get('tags', {}).get('piste:type') == 'downhill'}
    relations = {e['id']: e for e in payload['elements'] if e['type'] == 'relation'}
    sites = []
    for identifier, relation in sorted(relations.items()):
        if relation.get('tags', {}).get('site') != 'piste':
            continue
        selected, outside, cycles, visited = set(), set(), set(), set()
        def walk(current, stack):
            if current in stack:
                cycles.add(current); return
            if current in visited:
                return
            if current not in relations:
                outside.add(('relation', current)); return
            visited.add(current)
            for member in relations[current].get('members', []):
                key = (member['type'], member['ref'])
                if member['type'] == 'way' and member['ref'] in ways:
                    selected.add(member['ref'])
                elif member['type'] == 'relation':
                    walk(member['ref'], stack | {current})
                else:
                    outside.add(key)
        walk(identifier, set())
        sites.append(dict(osm_relation_id=identifier, name=relation['tags'].get('name', ''), tags=relation['tags'],
            version=relation['version'], last_edit_timestamp=relation['timestamp'],
            selected_downhill_way_ids=sorted(selected), recursively_visited_relation_ids=sorted(visited),
            member_references_outside_query=[dict(type=t, id=i) for t, i in sorted(outside)],
            cycle_relation_ids=sorted(cycles), direct_member_count=len(relation.get('members', []))))
    membership = Counter(w for site in sites for w in site['selected_downhill_way_ids'])
    for site in sites:
        site['downhill_way_ids_also_in_other_sites'] = [w for w in site['selected_downhill_way_ids'] if membership[w] > 1]
    return ways, sites


def build_review(groups, points, resorts, payload):
    if not groups.station_group_id.is_unique or points.duplicated(['station_group_id', 'access_point_id']).any() or not resorts.resort_id.is_unique:
        raise ValueError('Duplicate stable key')
    if set(points.station_group_id) != set(groups.station_group_id):
        raise ValueError('Reference/group universe mismatch')
    ways, sites = relation_inventory(payload)
    transform = Transformer.from_crs(4326, 2056, always_xy=True)
    geometries = {}
    for identifier, way in ways.items():
        coordinates = way.get('geometry', [])
        if len(coordinates) >= 2 and all('lon' in p and 'lat' in p for p in coordinates):
            x, y = transform.transform([p['lon'] for p in coordinates], [p['lat'] for p in coordinates])
            geometries[identifier] = LineString(zip(x, y))
    site_geometry = {s['osm_relation_id']: unary_union([geometries[i] for i in s['selected_downhill_way_ids'] if i in geometries]) for s in sites}
    listings = resorts.set_index('resort_id')
    rows, pairs = [], []
    for group in groups.itertuples():
        aliases = {group.station_group_name, *str(group.source_entry_labels).split('|')}
        for identifier in str(group.component_resort_ids).split('|'):
            if identifier and identifier in listings.index:
                aliases.update([listings.loc[identifier, 'resort_name_canonical'], listings.loc[identifier, 'resort_name_original']])
            elif identifier:
                raise ValueError('Unresolved retained component ID: ' + identifier)
        alias_keys = {normalized(a) for a in aliases if a and pd.notna(a)}
        selected_points = points[points.station_group_id.eq(group.station_group_id)]
        group_points = [(r.access_point_id, Point(*transform.transform(r.reference_longitude, r.reference_latitude))) for r in selected_points.itertuples()]
        if not all(p.is_valid and not p.is_empty for _, p in group_points):
            raise ValueError('Invalid reference geometry')
        group_pairs = []
        for site in sites:
            geometry = site_geometry[site['osm_relation_id']]
            distances = {identifier: float(point.distance(geometry)) for identifier, point in group_points} if not geometry.is_empty else {}
            minimum = min(distances.values()) if distances else None
            group_pairs.append(dict(station_group_id=group.station_group_id, osm_site_relation_id=site['osm_relation_id'],
                normalized_full_name_match=bool(site['name'] and normalized(site['name']) in alias_keys),
                reference_to_referenced_geometry_metres=minimum,
                minimum_reference_access_point_ids=sorted(k for k, v in distances.items() if v == minimum),
                retained_original_name_aliases=sorted(a for a in aliases if a and pd.notna(a)), assignment_verified=False))
        exact = {p['osm_site_relation_id'] for p in group_pairs if p['normalized_full_name_match']}
        measured = [p['reference_to_referenced_geometry_metres'] for p in group_pairs if p['reference_to_referenced_geometry_metres'] is not None]
        minimum = min(measured) if measured else None
        nearest = {p['osm_site_relation_id'] for p in group_pairs if minimum is not None and p['reference_to_referenced_geometry_metres'] == minimum}
        join = lambda values: '|'.join(map(str, sorted(values)))
        rows.append(dict(station_group_id=group.station_group_id, station_group_name=group.station_group_name,
            reference_point_count=len(group_points), exact_name_site_relation_ids=join(exact), exact_name_site_count=len(exact),
            nearest_referenced_geometry_site_relation_ids=join(nearest), minimum_reference_to_site_geometry_metres=minimum,
            exact_name_and_nearest_site_relation_ids=join(exact & nearest), current_site_assignment_verified=False,
            historical_piste_scope_verified=False, piste_feature_computed=False, review_status='operator_and_scope_review_required_no_exclusion',
            source_id=SOURCE, parent_source_ids='OSM_DOWNHILL_SWISS_CURRENT_2026_10_09|DERIVED_ACCESSIBILITY_STATION_GROUPS'))
        pairs.extend(group_pairs)
    return pd.DataFrame(rows), dict(sites=sites, all_group_site_pairs=pairs,
        site_relation_is_not_canonical_group=True, all_pairs_retained_without_radius_filter=True,
        member_outside_query_is_not_absent_in_osm=True, current_geometry_not_verified_preentry=True,
        geometry_distances_are_review_aids_not_road_times_or_sample_filters=True)


def register(frame):
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    record = dict(source_id=SOURCE, variable_name='piste_group_correspondence_review_queue',
        variable_description='Exhaustive group/site relation review, exact name aids and uncapped geometry distances; not approved assignment',
        source_organisation='Thesis deterministic inventory from archived OSM and retained group reference points',
        source_dataset_name='Stage46 current piste correspondence review', retrieval_date='2026-10-09',
        retrieval_method='Local OSM membership recursion and EPSG2056 geometry distances; no new requests',
        local_raw_file='|'.join(INPUTS), processed_file=OUTPUT+'|'+DETAIL,
        geographic_level='unchanged station groups versus archived OSM piste-site relations',
        temporal_resolution='current geometry proxy, preentry scope unverified',
        transformation_applied='Exact normalized original names only; all71x238pairs retained, all ties, no radius threshold/acceptance',
        quality_notes='Names and proximity not sufficient to accept scopes. Shared/unknown relation membership and cycles retained; no features/clustering/exclusions.',
        license='OSM ODbL attribution and original parent terms')
    definitions = [dict(variable=c, table=TABLE, description=DEFS[c][0], unit=DEFS[c][1], data_type=str(frame[c].dtype),
        geographic_level='unchanged station group', temporal_level='current geometry review only', source_id=SOURCE,
        raw_or_derived='derived review aid, not accepted station feature', formula='src/descriptive/prepare_piste_group_review.py',
        causal_role='source correspondence diagnostic; not treatment/exposure/effect', missing_share=f'{frame[c].isna().mean():.6f}',
        notes=record['quality_notes']) for c in frame]
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    write_csv(pd.concat([dictionary[dictionary.table.ne(TABLE)], pd.DataFrame(definitions).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')


def main():
    parent = json.loads((ROOT / INPUTS[4]).read_text(encoding='utf-8'))
    protected = {**parent['input_sha256'], **parent['output_sha256'], **parent['protected_legacy_sha256']}
    for path, expected in protected.items():
        if sha(path) != expected:
            raise ValueError('Protected source/result changed: ' + path)
    checkpoint = json.loads((ROOT / INPUTS[0]).read_text(encoding='utf-8'))
    if checkpoint['status'] != 'complete' or sha(checkpoint['raw_file']) != checkpoint['sha256']:
        raise ValueError('Complete integrity-checked current piste source required')
    inputs = {p: sha(p) for p in INPUTS}; inputs[checkpoint['raw_file']] = checkpoint['sha256']
    if (ROOT / SUMMARY).exists():
        prior = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        if prior['input_sha256'] != inputs or any(sha(p) != v for p, v in prior['output_sha256'].items()):
            raise ValueError('Changed own review output/input: preserve and investigate')
        print('Exact piste review checkpoint reused; no requests or accepted assignments.')
        return
    groups, points, resorts = [pd.read_csv(ROOT / p, keep_default_na=False) for p in INPUTS[1:4]]
    frame, details = build_review(groups, points, resorts, json.loads((ROOT / checkpoint['raw_file']).read_bytes()))
    write_csv(frame, ROOT / OUTPUT)
    (ROOT / DETAIL).write_text(json.dumps(details, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    register(frame)
    summary = dict(date='2026-10-09', group_count=len(frame), site_count=len(details['sites']), pair_count=len(details['all_group_site_pairs']),
        groups_with_exact_name_suggestions=int(frame.exact_name_site_count.gt(0).sum()),
        groups_with_exact_name_also_nearest=int(frame.exact_name_and_nearest_site_relation_ids.ne('').sum()),
        sites_with_selected_downhill_way_refs=sum(bool(s['selected_downhill_way_ids']) for s in details['sites']),
        unique_selected_downhill_ways_in_sites=len({i for s in details['sites'] for i in s['selected_downhill_way_ids']}),
        selected_ways_shared_between_sites=len({i for s in details['sites'] for i in s['downhill_way_ids_also_in_other_sites']}),
        sites_with_members_outside_query=sum(bool(s['member_references_outside_query']) for s in details['sites']),
        sites_with_relation_cycles=sum(bool(s['cycle_relation_ids']) for s in details['sites']),
        accepted_group_assignment_count=0, profile_features_computed=False, automatic_exclusion_applied=False,
        input_sha256=inputs, output_sha256={p: sha(p) for p in [OUTPUT, DETAIL]}, protected_legacy_sha256=protected)
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if not k.endswith('sha256')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
