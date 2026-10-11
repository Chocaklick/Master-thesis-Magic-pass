"""Approved scope, exact historical preservation and truthful documentary claims."""
import json
import subprocess
from io import StringIO
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.descriptive.build_remaining_piste_assignments_stage79 import ROOT, BASE, OUTPUTS, SUMMARY, read
from src.descriptive.review_piste_candidates_stage53 import originals
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.regroup_eischoll_unterbaech_stage55 import compare_exposure
from src.data_processing.regroup_wilerallmi_schwanden_stage79 import OUTPUTS as ROAD_OUTPUTS, BRIDGE
from src.descriptive.audit_piste_followup_stage79 import OUTPUTS as FOLLOWUP_OUTPUTS

CONFIG = json.loads((ROOT/'config/piste_remaining_assignments_stage79.json').read_text(encoding='utf-8'))
SCOPE = json.loads((ROOT/'config/piste_scope_decisions_stage79.json').read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def original_index():
    return originals()


def test_explicit_two_approvals_and_no_new_estimator():
    assert SCOPE['la_dole']['full_domain_cross_border_authorized']
    assert not SCOPE['la_dole']['clip_to_swiss_boundary']
    d = SCOPE['connected_group']
    assert d['preserve_original_group_ids_and_outputs']
    assert not d['historical_geometry_certified'] and not d['new_effect_estimation_authorised']
    assert 'no independent proof of publication' in d['historical_connection_quality']


def test_69_groups_all_71_original_identities_and_70_parents():
    old = read('data_processed/accessibility_station_groups_stage55.csv')
    new = read(ROAD_OUTPUTS['groups']); bridge = read(BRIDGE)
    lineage = read(ROAD_OUTPUTS['lineage'])
    assert len(old) == 70 and len(new) == 69 and new.station_group_id.is_unique
    assert len(bridge) == 70 and set(bridge.parent_station_group_id) == set(old.station_group_id)
    assert bridge.group_changed.eq('True').sum() == 2
    assert len(lineage) == 71 and lineage.original_station_group_id.nunique() == 71
    assert set(lineage.original_station_group_id) == set(read('data_processed/station_group_lineage_stage55.csv').original_station_group_id)
    assert set(lineage.station_group_id) == set(new.station_group_id)
    parents = set(SCOPE['connected_group']['parent_group_ids'])
    pd.testing.assert_frame_equal(new[~new.station_group_id.eq(SCOPE['connected_group']['new_derived_group_id'])][old.columns].reset_index(drop=True),
                                  old[~old.station_group_id.isin(parents)].reset_index(drop=True))
    joint = new[new.station_group_id.eq(SCOPE['connected_group']['new_derived_group_id'])]
    assert joint.first_effective_month.eq('2024-05-01').all()
    assert joint[['ski_area_km_unique_listing_sum','number_lifts_unique_listing_sum','altitude_top_m_min','altitude_top_m_max']].eq('').all().all()


def test_old_access_coordinates_and_road_values_unchanged():
    for key in ['access','pairs']:
        old_path = ROAD_OUTPUTS[key].replace('stage79','stage55')
        if key == 'access':
            old, new = read(old_path), read(ROAD_OUTPUTS[key])
        else:
            old, new = pd.read_csv(ROOT/old_path), pd.read_csv(ROOT/ROAD_OUTPUTS[key])
        cols = [c for c in old if c != 'station_group_id']
        pd.testing.assert_frame_equal(old[cols], new[cols])
        assert old.station_group_id.equals(new.stage79_parent_station_group_id)
    assert len(read(ROAD_OUTPUTS['access'])) == 75
    assert len(read(ROAD_OUTPUTS['pairs'])) == 13875


def test_minimum_reference_across_approved_departures():
    old = pd.read_csv(ROOT/'data_processed/accessibility_road_group_reference_stage55.csv')
    new = pd.read_csv(ROOT/ROAD_OUTPUTS['reference'])
    gid = SCOPE['connected_group']['new_derived_group_id']
    candidates = old[old.station_group_id.isin(SCOPE['connected_group']['parent_group_ids'])]
    expected = candidates.groupby('municipality_bfs_id').road_reference_minutes.min()
    actual = new[new.station_group_id.eq(gid)].set_index('municipality_bfs_id').road_reference_minutes
    assert len(new) == 69*185 and new[['municipality_bfs_id','station_group_id']].duplicated().sum() == 0
    pd.testing.assert_series_equal(actual.sort_index(), expected.sort_index(), check_names=False)


def test_unique_outcomes_and_exposure_calendar_preserved_at_all_thresholds():
    before = pd.read_csv(ROOT/'data_processed/accessibility_road_monthly_exposure_stage55.csv')
    after = pd.read_csv(ROOT/ROAD_OUTPUTS['monthly'])
    comparison = compare_exposure(before, after)
    assert [c['threshold_minutes'] for c in comparison] == [15,30,45]
    assert [c['territories_with_active_count_reduced'] for c in comparison] == [1,2,9]
    assert [c['rows_with_active_count_reduced'] for c in comparison] == [32,64,288]
    assert all(c['exposure_status_changed_rows'] == 0 and c['territory_count'] == 185 for c in comparison)
    assert len(after) == 93240 and not after.duplicated(['municipality_bfs_id','date','threshold_minutes']).any()
    # Retained source territory columns are not recreated from group names.
    for c in ['source_id','source_municipality_bfs_id','territorial_source_bfs_ids']:
        assert before[c].equals(after[c])


def test_all_old_assignment_and_member_cells_exact():
    old, new = read(BASE[0]), read(OUTPUTS[0])
    parents = SCOPE['connected_group']['parent_group_ids']
    keep = old[~old.station_group_id.isin(parents)].reset_index(drop=True)
    pd.testing.assert_frame_equal(new.iloc[:len(keep)][old.columns], keep)
    oldm, newm = read(BASE[1]), read(OUTPUTS[1])
    pd.testing.assert_frame_equal(newm.iloc[:len(oldm)][oldm.columns], oldm)
    assert len(oldm) == 1323 and len(newm) == 2001 and newm.osm_id.nunique() == 2001
    addition = newm.iloc[len(oldm):]
    assert len(addition) == 678 and addition.object_retained.eq('True').all()
    assert addition.individual_piste_metric_use_verified.eq('False').all()
    assert addition.historical_scope_verified.eq('False').all()


@pytest.mark.parametrize('case', CONFIG['groups'], ids=lambda c:c['station_group_id'])
def test_every_added_original_id_version_role_and_literal_tag(case, original_index):
    index, _, sites = original_index
    part = read(OUTPUTS[1]); part = part[part.station_group_id.eq(case['station_group_id'])]
    assert set(part.osm_id.astype(int)) == set(case['way_ids'])
    for r in part.itertuples():
        e = index[('way', int(r.osm_id))]
        assert e['tags']['piste:type'] == 'downhill' and int(r.osm_version) == e['version']
        assert r.original_name == e['tags'].get('name','') and r.osm_edit_timestamp == e['timestamp']
        assert set(r.membership_evidence_source_ids.split('|')) == set(case['evidence_source_ids'])
        assert r.current_geometry_correspondence_verified == 'True'
        if r.osm_site_relation_id:
            assert int(r.osm_id) in sites[int(r.osm_site_relation_id)]['selected_downhill_way_ids']
        else:
            assert r.current_site_correspondence_verified == 'False'


def test_dole_full_crossborder_pinned_objects_and_surfaces_not_axes(original_index):
    index, _, _ = original_index
    f = read(OUTPUTS[1]); d = f[f.station_group_id.eq(SCOPE['la_dole']['station_group_id'])]
    assert len(d) == 104 and d.candidate_role.eq('explicit_surface_way_candidate').sum() == 5
    # Original geometry is referenced by stable ID; no cut or coordinate replacement is made.
    assert all(index[('way', int(w))].get('geometry') for w in d.osm_id)
    surfaces = f[f.candidate_role.eq('explicit_surface_way_candidate')]
    assert surfaces.candidate_axis_length_m.eq('').all()
    assert len(surfaces) >= 26
    assert d[d.osm_id.eq('672823371')].original_review_tags.str.contains('approximatif').all()


def test_67_correspondences_and_two_missing_not_zero():
    f = read(OUTPUTS[2]); q = read(OUTPUTS[3])
    assert len(f) == 69 and f.station_group_id.is_unique and len(q) == 9
    assert f.geometry_correspondence_verified.eq('True').sum() == 67
    assert f.new_correspondence_stage79.eq('True').sum() == 7
    missing = f[f.geometry_correspondence_verified.eq('False')]
    assert set(missing.station_group_id) == {c['station_group_id'] for c in CONFIG['pending']}
    assert missing.member_object_count.eq('').all() and missing.candidate_axis_count.eq('').all()
    assert f.group_retained.eq('True').all()
    assert f.full_domain_coverage_verified.eq('False').all() and f.new_metric_use_verified.eq('False').all()


def test_late_primary_claims_do_not_infer_calendar_or_aggregate_to_station():
    claims = read(FOLLOWUP_OUTPUTS[0])
    assert len(claims) == 5 and claims.claim_id.is_unique
    assert claims.operating_calendar_or_geometry_changed.eq('False').all()
    ski = claims[claims.claim_id.eq('LABRAYE_ACTUAL_SKI_2017_18')].iloc[0]
    assert 'plusieurs stations' in ski.scope_limit and ski.pdf_page == '7'
    assert 'ne prouve' in claims[claims.claim_id.eq('LABRAYE_SUBSIDY_STOP_2018')].scope_limit.iloc[0]
    assert 'ne prouvent' in claims[claims.claim_id.eq('LABRAYE_OPERATING_CONVENTION')].scope_limit.iloc[0]


def test_all_literal_qa_alerts_retained_without_metric_filter():
    f = read(OUTPUTS[1]); q = read(FOLLOWUP_OUTPUTS[1])
    assert len(q) == 144 and q.osm_id.is_unique and q.object_retained.eq('True').all()
    assert q.historical_or_status_alert.eq('True').sum() == 33
    assert q.geometry_or_topology_alert.eq('True').sum() == 101
    assert set(q.osm_id) <= set(f.osm_id)
    assert q.review_status.eq('individual_review_pending_no_metric_rule_applied').all()
    for c in ['original_name','original_lifecycle_tags','original_review_tags','diagnostic_flags']:
        assert q[c].tolist() == f.set_index('osm_id').loc[q.osm_id,c].tolist()


def test_append_only_registry_prefix_against_stage78_commit():
    for p in ['metadata/data_sources_master.csv','metadata/data_dictionary.csv','logs/data_collection_log.csv']:
        raw = subprocess.check_output(['git','show','b1226de:'+p], cwd=ROOT)
        before = pd.read_csv(StringIO(raw.decode('utf-8-sig')), dtype=str, keep_default_na=False)
        actual = read(p)
        pd.testing.assert_frame_equal(actual.iloc[:len(before)].reset_index(drop=True), before)


def test_every_new_table_field_defined_and_sources_truthful():
    master, dictionary = read('metadata/data_sources_master.csv'), read('metadata/data_dictionary.csv')
    assert master.source_id.is_unique
    for p in [*OUTPUTS, *ROAD_OUTPUTS.values(), BRIDGE, *FOLLOWUP_OUTPUTS]:
        f = read(p); defs = dictionary[dictionary.table.eq(Path(p).stem)]
        assert defs.variable.is_unique and set(defs.variable) == set(f)
        assert set(defs.source_id) <= set(master.source_id)
        for d in defs.itertuples():
            assert abs(float(d.missing_share)-f[d.variable].eq('').mean()) <= .00000051
    queue = json.loads((ROOT/'config/piste_remaining_sources_stage79.json').read_text(encoding='utf-8'))
    follow = json.loads((ROOT/'config/piste_historical_followup_stage79.json').read_text(encoding='utf-8'))
    assert {s['source_id'] for s in queue+follow} <= set(master.source_id)
    failed = master[master.source_id.isin(['GSTAAD_PLAN_STAGE79','TLML_PLAN_STAGE79','TVGD_PLAN_STAGE79','JURA_PLAN_2021_STAGE79','RIFFENMATT_OPERATOR_STAGE79'])]
    assert len(failed) == 5 and failed.local_raw_file.eq('').all()
    assert failed.quality_notes.str.contains('robots|403|404').all()


@pytest.mark.parametrize('manifest', [SUMMARY, 'reports/wilerallmi_schwanden_regrouping_stage79_summary.json', 'reports/piste_historical_qa_stage79_summary.json'])
def test_frozen_producers_originals_and_results(manifest):
    state = json.loads((ROOT/manifest).read_text(encoding='utf-8'))
    for p,h in {**state['input_sha256'], **state['output_sha256']}.items():
        assert sha(p) == h, p


def test_collection_successes_not_repeated():
    events = json.loads((ROOT/'data_interim/piste_remaining_stage79/evidence_events.json').read_text(encoding='utf-8'))
    success = [e['source_id'] for e in events if e['status'] == 'downloaded']
    assert len(events) == 31 and len(success) == 17 and len(success) == len(set(success))
    assert sum('10013' in str(e.get('error','')) for e in events) == 9
