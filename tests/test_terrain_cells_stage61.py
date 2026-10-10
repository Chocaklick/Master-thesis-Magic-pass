"""Approved terrain kernel verified on explicit artificial geometric fixtures."""
import json
from pathlib import Path
import math
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import LineString,Polygon
from shapely.ops import unary_union
from src.data_processing.terrain_cell_weights_stage61 import horn,cell_lengths
ROOT=Path(__file__).resolve().parents[1]


def test_horn_cardinal_directions_are_terrain_not_line_bearing():
    east=np.tile(np.array([-2,0,2]),(3,1))
    north=np.tile(np.array([2,0,-2])[:,None],(1,3))
    assert horn(east)==(45.0,270.0)
    assert horn(-east)==(45.0,90.0)
    assert horn(north)==(45.0,180.0)
    assert horn(-north)==(45.0,0.0)


def test_flat_missing_and_tiny_nonzero_slope_have_distinct_roles():
    assert horn(np.ones((3,3)))==(0.0,None)
    incomplete=np.ones((3,3));incomplete[0,0]=np.nan
    assert horn(incomplete)==(None,None)
    tiny=np.tile(np.array([-1e-9,0,1e-9]),(3,1))
    assert 0<horn(tiny)[0]<1 and horn(tiny)[1]==270


def test_axis_lengths_in_native_cells_not_point_counts():
    f=cell_lengths(LineString([(0.5,1),(5.5,1)]),0,2)
    assert f==pytest.approx({(0,0):1.5,(0,1):2.0,(0,2):1.5},rel=1e-12,abs=1e-12)


def test_boundary_piece_single_native_cell_owner():
    f=cell_lengths(LineString([(2,2),(2,-2)]),0,2)
    assert f=={(0,1):2.0,(1,1):2.0}


def test_exact_union_cells_preserve_length_and_reverse_geometry():
    a=LineString([(0.5,1.5),(7.5,-3.5)])
    b=LineString(list(a.coords)[::-1])
    geometry=unary_union([a,b])
    weights=cell_lengths(geometry,0,2)
    assert math.isclose(sum(weights.values()),a.length,rel_tol=1e-12)
    assert weights==pytest.approx(cell_lengths(b,0,2),rel=1e-12,abs=1e-12)


def test_outside_cells_retained_no_implicit_exclusion():
    f=cell_lengths(LineString([(-3,1),(1,1)]),0,2)
    assert any(col<0 for row,col in f) and sum(f.values())==4
    with pytest.raises(ValueError):cell_lengths(Polygon([(0,0),(1,0),(0,1)]),0,2)


def test_explicit_terrain_approval_no_additional_flat_cutoff():
    d=json.loads((ROOT/'config/terrain_extraction_decisions_stage61.json').read_text(encoding='utf8'))
    assert d['resolution_m']==2 and d['terrain_gradient']=='Horn 3x3'
    assert not d['interpolate_missing_values'] and not d['automatic_group_or_member_exclusion']
    assert d['flat_parts_retained_for_altitude_and_length']


def test_stluc_overlay_preserves_all_other_assignments():
    old=pd.read_csv(ROOT/'data_processed/winter_profile_piste_assignment_stage55.csv',dtype=str,keep_default_na=False)
    new=pd.read_csv(ROOT/'data_processed/winter_profile_piste_assignment_stage60.csv',dtype=str,keep_default_na=False)
    mask=old.station_group_id.ne('MP_GROUP_RESORT__st_luc_chandolin')
    pd.testing.assert_frame_equal(old[mask],new[mask],check_exact=True)
    assert len(new)==70 and new.current_site_correspondence_verified.eq('True').sum()==41
    members=pd.read_csv(ROOT/'data_processed/winter_profile_verified_piste_member_qa_stage60.csv',dtype=str,keep_default_na=False)
    assert len(members)==854 and members.osm_id.nunique()==854
    assert members.object_retained.eq('True').all()


def test_primary_docs_originals_sha_and_no_collection_repetition():
    from src.descriptive.verify_piste_assignments_stage51 import sha
    s=json.loads((ROOT/'reports/piste_terrain_sources_stage60_summary.json').read_text(encoding='utf8'))
    assert len(s['source_metadata'])==3 and s['new_downhill_object_count']==81
    assert all(sha(m['raw_file'])==m['sha256'] for m in s['source_metadata'])
