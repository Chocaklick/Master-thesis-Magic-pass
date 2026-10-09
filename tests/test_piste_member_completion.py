import json
from pathlib import Path

import pytest

from src.data_collection.collect_piste_member_tags import requested_members, validate
from src.descriptive.audit_completed_piste_membership import audit, sha
from src.descriptive.register_piste_scope_case_evidence import visible_text

ROOT = Path(__file__).resolve().parents[1]


def test_scope_check_uses_visible_html_not_scripts_or_unverified_history():
    assert visible_text('<script>L Abbaye</script><style>Le Brassus</style><p>L’Orient &amp; pistes</p>') == 'L’Orient & pistes'


def test_completion_is_finite_deduplicated_and_missing_not_absent():
    detail = dict(sites=[dict(member_references_outside_query=[dict(type='way', id=1), dict(type='node', id=2)]),
        dict(member_references_outside_query=[dict(type='way', id=1), dict(type='relation', id=3)])])
    requested = requested_members(detail)
    assert requested == [('relation', 3), ('way', 1)]
    element = dict(type='way', id=1, version=1, timestamp='2026-10-09')
    payload = dict(osm3s={'timestamp_osm_base':'2026-10-09'}, elements=[element])
    assert validate(payload, requested) == [('relation', 3)]
    with pytest.raises(ValueError):
        validate(dict(payload, elements=[element, element]), requested)
    with pytest.raises(ValueError):
        validate(dict(payload, remark='timeout'), requested)


def test_completion_audit_adds_downhill_without_accepting_lifts_as_pistes():
    site = dict(type='relation', id=10, version=1, timestamp='2026-10-09', tags={'site':'piste', 'name':'Example'},
        members=[dict(type='way', ref=1), dict(type='way', ref=2), dict(type='way', ref=3), dict(type='way', ref=4)])
    initial = {'elements':[site]}
    extra = {'elements':[dict(type='way', id=1, tags={'piste:type':'downhill'}),
        dict(type='way', id=2, tags={'piste:type':'nordic'}), dict(type='way', id=3, tags={'aerialway':'t-bar'})]}
    frame, _ = audit(initial, extra)
    row = frame.iloc[0]
    assert row.completed_selected_downhill_way_count == row.known_nordic_way_member_count == row.known_aerialway_member_count == 1
    assert row.remaining_unresolved_way_relation_count == 1
    assert row.added_downhill_way_ids == '1'
    assert not row.group_assignment_accepted and not row.historical_scope_verified
    with pytest.raises(ValueError):
        audit(initial, {'elements':[site]})


def test_saved_membership_source_and_old_hashes_retained():
    state = json.loads((ROOT / 'reports/piste_site_membership_audit_summary.json').read_text())
    assert state['site_count'] == 238
    assert state['accepted_assignments'] == 0 and not state['features_computed'] and not state['exclusions_applied']
    for key in ['input_sha256', 'output_sha256', 'protected_legacy_sha256']:
        for path, expected in state[key].items():
            assert sha(path) == expected, path
