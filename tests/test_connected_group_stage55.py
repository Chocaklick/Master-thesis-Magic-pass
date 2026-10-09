"""Approved overlay preserves upstream identities and municipal observations."""
import json
from pathlib import Path
import pandas as pd
import numpy as np
from src.data_processing.regroup_eischoll_unterbaech_stage55 import compare_exposure
from src.descriptive.audit_piste_history_stage54 import article_dates
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]


def test_explicit_fusion_approval_with_historical_caveat():
    d=json.loads((ROOT/'config/eischoll_unterbaech_regrouping_stage55.json').read_text(encoding='utf-8'))
    assert d['preserve_original_group_ids_and_outputs']
    assert not d['historical_geometry_certified'] and not d['new_effect_estimation_authorised']


def test_all_original_ids_retained_in_70_group_overlay():
    old=pd.read_csv(ROOT/'data_processed/accessibility_station_groups.csv',dtype=str,keep_default_na=False)
    groups=pd.read_csv(ROOT/'data_processed/accessibility_station_groups_stage55.csv',dtype=str,keep_default_na=False)
    bridge=pd.read_csv(ROOT/'data_processed/station_group_lineage_stage55.csv',dtype=str,keep_default_na=False)
    assert len(old)==71 and len(groups)==70 and len(bridge)==71
    assert set(old.station_group_id)==set(bridge.original_station_group_id)
    assert set(groups.station_group_id)==set(bridge.station_group_id)
    assert bridge.group_changed.eq('True').sum()==2


def test_roads_have_no_new_coordinates_or_source_values():
    old=pd.read_csv(ROOT/'data_processed/accessibility_road_final_pairs.csv')
    new=pd.read_csv(ROOT/'data_processed/accessibility_road_pairs_stage55.csv')
    cols=[c for c in old if c!='station_group_id']
    assert old[cols].equals(new[cols])
    assert old.station_group_id.equals(new.original_station_group_id)
    points=pd.read_csv(ROOT/'data_processed/accessibility_station_access_points_stage55.csv')
    assert len(points)==75 and points.access_point_id.is_unique


def test_exposure_outcomes_first_date_and_keys_preserved():
    before=pd.read_csv(ROOT/'data_processed/accessibility_road_did_monthly_exposure.csv')
    after=pd.read_csv(ROOT/'data_processed/accessibility_road_monthly_exposure_stage55.csv')
    result=compare_exposure(before,after)
    assert [r['territories_with_active_count_reduced'] for r in result]==[1,2,3]
    assert all(r['territory_count']==185 and r['exposure_status_changed_rows']==0 for r in result)
    assert len(after)==3*185*168


def test_shared_piste_site_counted_in_one_current_group():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_piste_assignment_stage55.csv',dtype=str,keep_default_na=False)
    assert len(f)==70 and f.group_retained.eq('True').all()
    assert f.current_site_correspondence_verified.eq('True').sum()==40
    joint=f[f.station_group_id.eq('MP_GROUP_CONNECTED__eischoll_unterbaech')]
    assert len(joint)==1 and int(joint.osm_site_relation_id.iloc[0])==9142700
    assert f.individual_piste_metrics_ready.eq('False').all()


def test_article_dates_are_not_taken_from_url_or_search():
    s=BeautifulSoup('<script type="application/ld+json">{"datePublished":"2022-03-10","dateModified":"2025-01-01"}</script>','html.parser')
    assert article_dates(s)=={'datePublished':'2022-03-10','dateModified':'2025-01-01'}
    assert article_dates(BeautifulSoup('<h1>2021</h1>','html.parser'))=={'datePublished':None,'dateModified':None}


def test_new_member_audit_retains_773_unique_objects():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_verified_piste_member_qa_stage56.csv',dtype=str,keep_default_na=False)
    assert len(f)==773 and f.osm_id.nunique()==773
    assert f.candidate_role.eq('way_axis_candidate').sum()==765
    assert f.candidate_role.eq('explicit_surface_way_candidate').sum()==8
    assert f.object_retained.eq('True').all() and f.individual_piste_metric_use_verified.eq('False').all()
    assert len(f[f.station_group_id.eq('MP_GROUP_CONNECTED__eischoll_unterbaech')])==63


def test_new_group_audit_does_not_remove_unresolved_groups():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_verified_piste_group_qa_stage56.csv',dtype=str,keep_default_na=False)
    assert len(f)==70 and f.group_retained.eq('True').all()
    assert f.current_site_correspondence_verified.eq('True').sum()==40
    assert f.loc[f.current_site_correspondence_verified.eq('False'),'inspected_downhill_member_count'].eq('').all()
