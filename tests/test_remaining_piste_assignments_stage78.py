"""Explicit identity, all units retained, exact old cells and truthful provenance."""
import copy
import json
from pathlib import Path

import pandas as pd
import pytest
from src.descriptive.build_remaining_piste_assignments_stage78 import (
    ROOT, BASE, OUTPUTS, SUMMARY, build, read, baseline_registry)
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha

CONFIG=json.loads((ROOT/'config/piste_remaining_assignments_stage78.json').read_text(encoding='utf-8'))


def test_preserve_all70_groups_and_exact_previous_assignment_cells():
    old=read(BASE[0]);new=read(OUTPUTS[1])
    pd.testing.assert_frame_equal(new[old.columns],old)
    assert len(new)==70 and new.station_group_id.is_unique
    assert new.group_retained.eq('True').all()
    assert new.stage78_new_correspondence_stage78.eq('True').sum()==20
    assert new.stage78_geometry_correspondence_verified.eq('True').sum()==60
    assert new.stage78_full_domain_coverage_verified.eq('False').all()
    assert new.stage78_historical_geometry_verified.eq('False').all()
    assert new.stage78_new_metric_use_verified.eq('False').all()


def test_all854_previous_member_cells_exact_and469_new_original_objects():
    old=read(BASE[1]);new=read(OUTPUTS[2])
    pd.testing.assert_frame_equal(new.iloc[:len(old)][old.columns],old)
    assert len(old)==854 and len(new)==1323
    added=new.iloc[len(old):]
    assert len(added)==469 and added.osm_id.nunique()==469
    assert added.membership_basis.eq('explicit_reviewed_way_ids').all()
    assert added.individual_piste_metric_use_verified.eq('False').all()
    assert not new.duplicated(['station_group_id','osm_type','osm_id','osm_version']).any()
    assert added.object_retained.eq('True').all()


@pytest.mark.parametrize('case',CONFIG['groups'],ids=lambda c:c['station_group_id'])
def test_every_curated_id_original_tags_version_role_and_proof(case):
    index,_,sites=originals()
    frame=read(OUTPUTS[2]);part=frame[frame.station_group_id.eq(case['station_group_id'])]
    assert set(part.osm_id.astype(int))==set(case['way_ids'])
    for r in part.itertuples():
        original=index[('way',int(r.osm_id))]
        assert original['tags']['piste:type']=='downhill'
        assert int(r.osm_version)==original['version']
        assert r.osm_edit_timestamp==original['timestamp']
        assert r.original_name==original['tags'].get('name','')
        assert set(r.membership_evidence_source_ids.split('|'))==set(case['evidence_source_ids'])
        if r.osm_site_relation_id:
            assert int(r.osm_id) in sites[int(r.osm_site_relation_id)]['selected_downhill_way_ids']
        else:
            assert r.current_site_correspondence_verified=='False'
        assert r.current_geometry_correspondence_verified=='True'


def test_surfaces_never_axes_and_historical_flags_not_silently_removed():
    f=read(OUTPUTS[2]);added=f[f.membership_basis.eq('explicit_reviewed_way_ids')]
    surface=added[added.candidate_role.eq('explicit_surface_way_candidate')]
    assert set(surface.osm_id)=={'661760344','661760350'}
    assert surface.candidate_axis_length_m.eq('').all()
    lifecycle=added[added.original_lifecycle_tags.ne('{}')]
    assert len(lifecycle)==19
    assert lifecycle.object_retained.eq('True').all()
    ancient=added[added.osm_id.eq('1375037670')]
    assert ancient.literal_name_history_hint.eq('True').all()
    assert ancient.individual_piste_metric_use_verified.eq('False').all()


def test_review_queue_exact30_with_no_automatic_exclusion_or_missing_zero():
    f=read(OUTPUTS[0]);g=read(OUTPUTS[3])
    assert len(f)==30 and f.station_group_id.is_unique
    assert f.geometry_assignment_accepted.eq('True').sum()==20
    assert set(f.loc[f.geometry_assignment_accepted.eq('False'),'station_group_id'])=={r['station_group_id'] for r in CONFIG['pending']}
    missing=g[g.geometry_correspondence_verified.eq('False')]
    assert len(missing)==10 and missing.member_object_count.eq('').all()
    assert missing.candidate_axis_count.eq('').all()
    assert g.group_retained.eq('True').all()
    assert not f.review_status.str.contains('excluded').any()
    assert '671247731' not in set(read(OUTPUTS[2]).osm_id)


def test_registered_sources_and_every_new_column_defined():
    master=read('metadata/data_sources_master.csv');d=read('metadata/data_dictionary.csv')
    assert master.source_id.is_unique
    for path in OUTPUTS:
        f=read(path);defs=d[d.table.eq(Path(path).stem)]
        assert defs.variable.is_unique and set(defs.variable)==set(f)
        assert set(defs.source_id)<=set(master.source_id)
        for r in defs.itertuples():
            miss=f[r.variable].eq('').mean()
            assert abs(float(r.missing_share)-miss)<=0.00000051
    for case in CONFIG['groups']:
        assert set(case['evidence_source_ids'])<=set(master.source_id)
    failed=master[master.source_id.isin(['AROLLA_PLAN_STAGE78','EVOLENE_PLAN_STAGE78','MARECOTTES_OPERATOR_STAGE78'])]
    assert len(failed)==3 and failed.local_raw_file.eq('').all()
    assert failed.quality_notes.str.contains('robots|CERTIFICATE_VERIFY_FAILED',regex=True).all()


def test_frozen_inputs_outputs_and_raw_evidence_sha():
    state=json.loads((ROOT/SUMMARY).read_text(encoding='utf-8'))
    assert state['new_correspondence_count']==20 and state['still_unresolved_group_count']==10
    assert not state['automatic_assignment'] and not state['group_exclusion']
    assert not state['new_terrain_snow_or_clustering_computed']
    for p,h in {**state['input_sha256'],**state['output_sha256']}.items():
        assert sha(p)==h,p
    assert baseline_registry()==state['prior_registry']


def test_original_identity_or_uninspected_way_rejected():
    config=copy.deepcopy(CONFIG)
    config['groups'][0]['way_ids'].append(999999999999999)
    inv=json.loads((ROOT/'data_interim/piste_remaining_stage78/candidate_inventory.json').read_text(encoding='utf-8'))
    index,_,sites=originals()
    with pytest.raises(ValueError,match='Uninspected original object'):
        build(config,inv,index,sites,read('data_processed/winter_profile_piste_geometry_roles.csv'),read(BASE[0]),read(BASE[1]))


def test_second_run_does_not_repeat_collection_or_rewrite_old_flags():
    events=json.loads((ROOT/'data_interim/piste_remaining_stage78/evidence_events.json').read_text(encoding='utf-8'))
    successful=[r['source_id'] for r in events if r.get('status')=='downloaded']
    assert len(successful)==12
    assert len(successful)==len(set(successful))
    flags=read(OUTPUTS[2]).iloc[:854]
    assert flags.diagnostic_flags.tolist()==read(BASE[1]).diagnostic_flags.tolist()
