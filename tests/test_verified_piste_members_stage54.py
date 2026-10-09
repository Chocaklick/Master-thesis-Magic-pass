"""Non-excluding diagnostics and frozen universe; no network or profile fit."""
import json
from pathlib import Path
import pandas as pd
from src.descriptive.audit_verified_piste_members_stage54 import exact_signature,lifecycle_tags,edges
ROOT=Path(__file__).resolve().parents[1]


def test_exact_reversed_sequence_no_rounding():
    a={'geometry':[{'lon':7.0,'lat':46.0},{'lon':7.1,'lat':46.1}]}
    b={'geometry':list(reversed(a['geometry']))}
    c={'geometry':[{'lon':7.0,'lat':46.0},{'lon':7.100000001,'lat':46.1}]}
    assert exact_signature(a)==exact_signature(b)
    assert exact_signature(a)!=exact_signature(c)


def test_missing_geometry_is_not_duplicate():
    assert exact_signature({}) is None
    assert exact_signature({'geometry':[{'lon':7,'lat':float('nan')},{'lon':8,'lat':46}]}) is None


def test_literal_lifecycle_tags_not_active_status():
    assert lifecycle_tags({'disused':'no','abandoned:piste:type':'downhill','name':'x'})=={'disused':'no','abandoned:piste:type':'downhill'}
    assert lifecycle_tags({'opening_hours':'Mo-Fr'})=={}


def test_shared_vertex_is_not_shared_edge():
    assert edges({'nodes':[1,2,3]}) & edges({'nodes':[3,4,5]})==set()
    assert edges({'nodes':[1,2,3]}) & edges({'nodes':[3,2,8]})=={(2,3)}


def test_all_groups_retained_unresolved_not_zero():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_verified_piste_group_qa_stage54.csv',dtype=str,keep_default_na=False)
    assert len(f)==71 and f.station_group_id.is_unique and f.group_retained.eq('True').all()
    assert f.loc[f.current_site_correspondence_verified.eq('False'),'inspected_downhill_member_count'].eq('').all()
    assert f.loc[f.station_group_name.str.contains('Sainte-Croix'),'inspected_downhill_member_count'].astype(float).eq(0).all()


def test_diagnostics_do_not_accept_metrics_or_exclude():
    f=pd.read_csv(ROOT/'data_processed/winter_profile_verified_piste_member_qa_stage54.csv',dtype=str,keep_default_na=False)
    assert len(f)==710 and f.osm_id.nunique()==710
    assert f.object_retained.eq('True').all()
    assert f.individual_piste_metric_use_verified.eq('False').all()
    assert f.historical_scope_verified.eq('False').all()
    assert f.original_lifecycle_tags.ne('{}').sum()==2


def test_historical_approval_does_not_authorise_fusion():
    d=json.loads((ROOT/'config/piste_historical_connection_decisions_stage54.json').read_text(encoding='utf-8'))
    assert d['verify_connection_before_entry'] and d['propose_common_group_if_confirmed']
    assert not d['fusion_authorised'] and not d['current_connection_alone_sufficient']
