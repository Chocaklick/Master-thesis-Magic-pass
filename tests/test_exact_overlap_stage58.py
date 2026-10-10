"""Exact geometry weighting, preserved lineage and calendar context."""
import json
from pathlib import Path
import pandas as pd
import pytest
from shapely.geometry import LineString
from src.descriptive.audit_exact_piste_overlap_stage58 import exact_network
from src.descriptive.verify_exact_overlap_geometry_stage59 import shared_geometry

ROOT=Path(__file__).resolve().parents[1]


def test_reverse_duplicate_is_once_but_id_sum_remains():
    a=LineString([(0,0),(10,0)])
    b=LineString([(10,0),(0,0)])
    r=exact_network([a,b])
    assert r['distinct_id_sum_m']==20
    assert r['exact_unique_network_m']==10
    assert r['overlap_repeated_weight_m']==10


def test_partial_overlap_not_only_complete_duplicate():
    r=exact_network([LineString([(0,0),(10,0)]),LineString([(5,0),(15,0)])])
    assert r['distinct_id_sum_m']==20 and r['exact_unique_network_m']==15


def test_crossing_and_nearby_lines_do_not_deduplicate_length():
    crossing=exact_network([LineString([(0,0),(10,0)]),LineString([(5,-5),(5,5)])])
    nearby=exact_network([LineString([(0,0),(10,0)]),LineString([(0,1e-9),(10,1e-9)])])
    assert crossing['exact_unique_network_m']==20
    assert nearby['exact_unique_network_m']==20


def test_no_input_is_missing_not_zero():
    assert exact_network([]) is None
    with pytest.raises(ValueError):
        exact_network([LineString()])


def test_approval_retains_ids_surfaces_and_no_tolerance():
    d=json.loads((ROOT/'config/piste_exact_overlap_decisions_stage58.json').read_text(encoding='utf-8'))
    assert d['within_group_exact_overlap_counted_once'] and d['distinct_identifier_length_sum_preserved']
    assert d['surfaces_separate_from_axes'] and not d['automatic_member_or_group_exclusion_allowed']
    assert not d['proximity_tolerance_or_coordinate_snapping_allowed']


def test_all_groups_and_773_member_versions_retained():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_exact_piste_overlap_stage58.csv')
    net=json.loads((ROOT/'data_interim/winter_profile_exact_network_stage58.json').read_text(encoding='utf-8'))
    assert len(f)==len(net)==70 and f.group_retained.all()
    assert f.candidate_axis_count.sum()==765 and f.explicit_surface_count.sum()==8
    assert len([r for g in net for r in g['retained_original_members']])==773
    assert f.individual_metric_use_verified.eq(False).all()
    assert f.loc[f.metric_status.eq('site_correspondence_unresolved'),'exact_unique_mapped_axis_length_m'].isna().all()
    assert f.loc[f.metric_status.eq('verified_site_missing_mapped_axes'),'exact_unique_mapped_axis_length_m'].isna().all()
    assert f.literal_lifecycle_flag_member_count.sum()==2


def test_urban_context_70_groups_and_each_has_five_own_winters():
    minimum=pd.read_csv(ROOT/'data_processed/winter_profile_urban_minimum_stage57.csv')
    windows=pd.read_csv(ROOT/'data_processed/winter_profile_approved_snow_windows_stage57.csv')
    detail=pd.read_csv(ROOT/'data_processed/winter_profile_urban_city_detail_stage57.csv')
    assert len(minimum)==70 and minimum.all_six_cities_available.all()
    assert len(detail)==420 and len(windows)==350
    assert windows.groupby('station_group_id').size().eq(5).all()
    assert pd.to_datetime(windows.winter_end_date).lt(pd.to_datetime(windows.first_base_entry_month)).all()
    assert not windows.snow_mean_computed.any()


def test_original_members_equal_retained_network_provenance():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_verified_piste_member_qa_stage56.csv',dtype=str,keep_default_na=False)
    net=json.loads((ROOT/'data_interim/winter_profile_exact_network_stage58.json').read_text(encoding='utf-8'))
    old={(r.station_group_id,r.parent_source_id,r.osm_type,int(r.osm_id),int(r.osm_version)) for r in f.itertuples()}
    new={(g['station_group_id'],r['parent_source_id'],r['osm_type'],r['osm_id'],r['osm_version']) for g in net for r in g['retained_original_members']}
    assert old==new


def test_pair_geometry_excludes_crossing_points_without_any_tolerance():
    assert shared_geometry([]) is None
    r=shared_geometry([LineString([(0,0),(10,0)]),LineString([(5,-5),(5,5)])])
    assert r=={'exact_overlap_pair_count':0,'exact_shared_portion_m':0}
    r=shared_geometry([LineString([(0,0),(10,0)]),LineString([(5,0),(15,0)])])
    assert r=={'exact_overlap_pair_count':1,'exact_shared_portion_m':5}


def test_shared_physical_length_not_same_as_excess_weight_when_three_ids():
    a=LineString([(0,0),(10,0)])
    assert shared_geometry([a,a,a])['exact_shared_portion_m']==10
    assert exact_network([a,a,a])['overlap_repeated_weight_m']==20


def test_only_seven_groups_have_directly_verified_shared_line_geometry():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_overlap_geometry_stage59.csv')
    assert len(f)==70 and f.group_retained.all()
    assert f.has_exact_shared_line_geometry.eq(True).sum()==7
    assert f.loc[f.has_exact_shared_line_geometry.eq(False),'exact_shared_portion_m'].eq(0).all()
    assert f.has_exact_shared_line_geometry.isna().sum()==31
