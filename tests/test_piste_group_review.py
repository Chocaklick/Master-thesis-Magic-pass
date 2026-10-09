import json
from pathlib import Path

import pandas as pd
import pytest

from src.descriptive.prepare_piste_group_review import build_review, normalized, relation_inventory, sha

ROOT = Path(__file__).resolve().parents[1]


def relation(identifier, members, name=None):
    tags = {'site': 'piste', 'name': name} if name else {'piste:type': 'downhill'}
    return dict(type='relation', id=identifier, members=members, tags=tags, version=1, timestamp='2026-10-09T00:00:00Z')


def member(kind, identifier):
    return dict(type=kind, ref=identifier)


def test_membership_recursion_deduplicates_flags_shared_unknown_and_cycles():
    payload = {'elements': [dict(type='way', id=1, tags={'piste:type': 'downhill'}),
        relation(20, [member('way', 1), member('way', 1), member('relation', 10)]),
        relation(10, [member('relation', 20), member('way', 99), member('node', 9)], 'Area'),
        relation(11, [member('way', 1), member('relation', 88)], 'Other')]}
    _, sites = relation_inventory(payload)
    first, second = sites
    assert first['selected_downhill_way_ids'] == [1]
    assert first['cycle_relation_ids'] == [10]
    assert first['downhill_way_ids_also_in_other_sites'] == [1]
    assert {'type': 'way', 'id': 99} in first['member_references_outside_query']
    assert second['member_references_outside_query'] == [{'type': 'relation', 'id': 88}]


def test_review_retains_all_pairs_ties_and_empty_geometries_without_accepting():
    groups = pd.DataFrame([dict(station_group_id='g', station_group_name='École-Ski', source_entry_labels='', component_resort_ids='')])
    points = pd.DataFrame([dict(station_group_id='g', access_point_id='a', reference_longitude=7.0, reference_latitude=46.0)])
    resorts = pd.DataFrame(columns=['resort_id', 'resort_name_canonical', 'resort_name_original'])
    payload = {'elements': [dict(type='way', id=1, tags={'piste:type': 'downhill'}, geometry=[dict(lon=7.0, lat=46.0), dict(lon=7.01, lat=46.0)]),
        relation(10, [member('way', 1)], 'Ecole Ski'), relation(11, [member('way', 1)], 'Ecole Ski annexe'),
        relation(12, [member('way', 99)], 'Far unknown')]}
    frame, detail = build_review(groups, points, resorts, payload)
    assert len(detail['all_group_site_pairs']) == 3
    assert frame.loc[0, 'exact_name_site_relation_ids'] == '10'
    assert frame.loc[0, 'nearest_referenced_geometry_site_relation_ids'] == '10|11'
    assert detail['all_group_site_pairs'][2]['reference_to_referenced_geometry_metres'] is None
    assert not any(p['assignment_verified'] for p in detail['all_group_site_pairs'])
    assert not frame.current_site_assignment_verified.any()
    assert normalized('École-Ski') == 'ecole ski'
    with pytest.raises(ValueError):
        build_review(groups, pd.concat([points, points]), resorts, payload)


def test_saved_review_and_provenance_are_complete_without_exclusions():
    summary = json.loads((ROOT / 'reports/piste_group_review_summary.json').read_text())
    frame = pd.read_csv(ROOT / 'data_processed/winter_profile_piste_group_review.csv', dtype=str, keep_default_na=False)
    retained = pd.read_csv(ROOT / 'data_processed/accessibility_station_groups.csv')
    assert set(frame.station_group_id) == set(retained.station_group_id)
    assert (summary['group_count'], summary['site_count'], summary['pair_count']) == (71, 238, 16898)
    assert summary['groups_with_exact_name_suggestions'] == 33
    assert summary['groups_with_exact_name_also_nearest'] == 32
    assert summary['accepted_group_assignment_count'] == 0
    assert not summary['automatic_exclusion_applied']
    for hashes in ['input_sha256', 'output_sha256', 'protected_legacy_sha256']:
        for path, expected in summary[hashes].items():
            assert sha(path) == expected, path
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    known = set(sources.source_id)
    assert set(frame.source_id) <= known
    assert {x for cell in frame.parent_source_ids for x in cell.split('|')} <= known
    fields = dictionary[dictionary.table.eq('winter_profile_piste_group_review')]
    assert len(fields) == 14 and set(fields.variable) == set(frame.columns)
