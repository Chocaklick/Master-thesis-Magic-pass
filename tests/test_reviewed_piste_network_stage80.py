"""Unresolved portions missing, not group exclusions or loss of original IDs."""
import json
from pathlib import Path
import pandas as pd
import pytest
from shapely import wkt
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from src.data_processing.build_reviewed_piste_network_stage80 import ROOT, CONFIG, OUTPUTS, NETWORK, SUMMARY, projected
from src.descriptive.review_piste_candidates_stage53 import originals
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def read(p):return pd.read_csv(ROOT/p,dtype=str,keep_default_na=False)


@pytest.fixture(scope='module')
def original_index():return originals()[0]


def test_approved_rule_and_all_originals_retained():
    d=json.loads((ROOT/'config/piste_metric_decisions_stage80.json').read_text(encoding='utf-8'))
    assert d['unresolved_portions']=='retain_original_objects_do_not_measure_publish_coverage'
    assert not d['remove_group_or_commune'] and not d['change_historical_calendar']
    f=read(OUTPUTS[1]); net=json.loads((ROOT/NETWORK).read_text(encoding='utf-8'))
    assert len(f)==69 and f.station_group_id.is_unique and f.group_retained.eq('True').all()
    assert len(net)==69
    originals_retained=[m['osm_id'] for n in net for m in n['original_members_retained']]
    assert len(originals_retained)==2001 and len(set(originals_retained))==2001
    assert set(originals_retained)==set(read('data_processed/winter_profile_piste_members_stage79.csv').osm_id.astype(int))
    assert sum(not m['measurement_permitted_as_current_proxy'] for n in net for m in n['original_members_retained'])==28


def test_37_individual_reviews_28_ambiguous_axes_not_measured():
    f=read(OUTPUTS[0]); c=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    wanted={w for case in c['unresolved_cases'] for w in case['way_ids']}
    assert len(f)==37 and f.osm_id.is_unique
    unmeasured=f[f.measurement_permitted_as_current_proxy.eq('False')]
    assert len(unmeasured)==28 and set(unmeasured.osm_id.astype(int))==wanted
    assert unmeasured.candidate_role.eq('way_axis_candidate').all()
    assert f.original_object_retained.eq('True').all()
    assert f.historical_or_operating_status_certified.eq('False').all()


def test_six_renamings_and_two_non_geometry_notes_not_excluded():
    f=read(OUTPUTS[0]); renamed=f[f.review_status.eq('former_name_only_not_former_geometry')]
    assert len(renamed)==6 and renamed.measurement_permitted_as_current_proxy.eq('True').all()
    assert all(set(json.loads(x))=={'was:name'} for x in renamed.original_lifecycle_tags)
    notes=f[f.review_status.eq('non_geometry_note_retained')]
    assert set(notes.osm_id)=={'154193971','29279508'}
    assert notes.measurement_permitted_as_current_proxy.eq('True').all()


def test_original_multipolygon_hole_not_invented_or_made_axis(original_index):
    f=read(OUTPUTS[0]); surface=f[f.osm_id.eq('225673460')].iloc[0]
    assert surface.candidate_role=='explicit_surface_way_candidate'
    assert surface.canonical_surface_relation_id=='2998700.0'
    n=json.loads((ROOT/NETWORK).read_text(encoding='utf-8'))
    m=next(m for g in n for m in g['original_members_retained'] if m['osm_id']==225673460)
    canonical=m['canonical_surface']; assert canonical['osm_type']=='relation' and canonical['osm_id']==2998700
    assert canonical['inner_member_id']==225673482 and canonical['inner_member_version'] is None
    e=original_index[('relation',2998700)]; rings={m['role']:projected(m) for m in e['members']}
    expected=Polygon(rings['outer'],[rings['inner']])
    actual=wkt.loads(canonical['geometry_wkt'])
    assert actual.equals_exact(expected,0) and len(actual.interiors)==1 and actual.area<Polygon(rings['outer']).area


def test_exact_networks_recomputed_from_original_eligible_axes(original_index):
    c=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    missing={w for case in c['unresolved_cases'] for w in case['way_ids']}
    f=pd.read_csv(ROOT/OUTPUTS[1],float_precision='round_trip').set_index('station_group_id')
    m=read('data_processed/winter_profile_piste_members_stage79.csv')
    network=json.loads((ROOT/NETWORK).read_text(encoding='utf-8'))
    for n in network:
        gid=n['station_group_id']; p=m[m.station_group_id.eq(gid)&m.candidate_role.eq('way_axis_candidate')]
        if p.empty:
            assert n['measured_unique_proxy_axis_wkt'] is None and pd.isna(f.loc[gid,'measured_unique_proxy_axis_length_m'])
            continue
        full=unary_union([LineString(projected(original_index[('way',int(w))])) for w in p.osm_id])
        usable=unary_union([LineString(projected(original_index[('way',int(w))])) for w in p.osm_id if int(w) not in missing])
        assert wkt.loads(n['full_unique_candidate_axis_wkt']).equals_exact(full,0)
        assert wkt.loads(n['measured_unique_proxy_axis_wkt']).equals_exact(usable,0)
        assert f.loc[gid,'full_unique_candidate_axis_length_m']==full.length
        assert f.loc[gid,'measured_unique_proxy_axis_length_m']==usable.length
        assert f.loc[gid,'unmeasured_unique_ambiguous_axis_length_m']==full.length-usable.length


def test_old_40_full_candidate_network_lengths_unchanged():
    old=pd.read_csv(ROOT/'data_processed/winter_profile_exact_piste_overlap_stage63.csv',float_precision='round_trip')
    old=old[old.exact_unique_mapped_axis_length_m.notna()]
    new=pd.read_csv(ROOT/OUTPUTS[1],float_precision='round_trip')
    joined=old.merge(new,on='station_group_id',validate='one_to_one')
    assert len(joined)==40
    pd.testing.assert_series_equal(joined.exact_unique_mapped_axis_length_m,joined.full_unique_candidate_axis_length_m,check_names=False)
    # Only the new approved mask, not the frozen old profiles, changes Moosalp.
    assert joined.loc[joined.station_group_id.eq('MP_GROUP_RESORT__moosalpregion'),'measured_share_of_mapped_candidate_length'].lt(1).all()


def test_coverage_missing_not_zero_and_no_arbitrary_cutoff():
    f=pd.read_csv(ROOT/OUTPUTS[1])
    assert f.measured_unique_proxy_axis_length_m.notna().sum()==67
    assert f.measured_share_of_mapped_candidate_length.lt(1).sum()==5
    missing=f[f.measured_unique_proxy_axis_length_m.isna()]
    assert len(missing)==2 and missing.metric_status.eq('missing_geometry_not_zero').all()
    assert missing.full_unique_candidate_axis_length_m.isna().all()
    assert f.full_real_domain_coverage_certified.eq(False).all()
    dole=f[f.station_group_id.eq('MP_GROUP_RESORT__la_dole_jura_sur_leman')].iloc[0]
    assert 'transfrontalier' in dole.display_scope_name and dole.original_axis_object_count==99


def test_sources_fields_missing_shares_and_registry_repair():
    d=read('metadata/data_dictionary.csv'); s=read('metadata/data_sources_master.csv')
    for path in OUTPUTS:
        f=read(path); defs=d[d.table.eq(Path(path).stem)]
        assert defs.variable.is_unique and set(defs.variable)==set(f)
        assert set(defs.source_id)<=set(s.source_id)
        for r in defs.itertuples():assert abs(float(r.missing_share)-f[r.variable].eq('').mean())<=.00000051
    p=json.loads((ROOT/'reports/piste_network_registry_stage80_summary.json').read_text(encoding='utf-8'))
    assert p['numerical_producer_and_results_unchanged'] and p['no_geometry_recomputation_or_source_request']
    assert p['registration_script_sha256']==sha('src/data_processing/complete_piste_network_registry_stage80.py')


def test_originals_producer_and_outputs_frozen():
    s=json.loads((ROOT/SUMMARY).read_text(encoding='utf-8'))
    for p,h in {**s['input_sha256'],**s['output_sha256']}.items():assert sha(p)==h,p
    assert s['no_group_exclusion_or_original_rewrite'] and s['new_snow_or_terrain_values_read'] is False
