import pytest
from shapely.geometry import LineString,Polygon

from src.descriptive.audit_piste_geometry_roles import mapped_area,role,geometry_diagnostic


def test_surface_union_removes_overlap_and_preserves_holes():
    first=Polygon([(0,0),(100,0),(100,100),(0,100)])
    second=Polygon([(50,0),(150,0),(150,100),(50,100)])
    assert mapped_area([first,second])=={'mapped_piste_area_ha':1.5,'mapped_piste_area_km2':0.015}
    hole=Polygon([(0,0),(100,0),(100,100),(0,100)],holes=[[(20,20),(80,20),(80,80),(20,80)]])
    assert mapped_area([hole])['mapped_piste_area_ha']==0.64


def test_lines_invalid_surfaces_and_missing_coverage_never_become_area():
    assert mapped_area([]) is None
    with pytest.raises(ValueError):
        mapped_area([LineString([(0,0),(100,0)])])
    with pytest.raises(ValueError):
        mapped_area([Polygon([(0,0),(100,100),(100,0),(0,100)])])


def test_role_does_not_turn_surface_boundary_into_piste_length():
    surface=dict(type='way',nodes=[1,2,3,1],tags={'area':'yes'})
    ambiguous=dict(type='way',nodes=[1,2,3,1],tags={})
    assert role(surface)=='explicit_surface_way_candidate'
    assert role(ambiguous)=='closed_way_role_unresolved'
    assert role(dict(type='relation',tags={'type':'route'}))=='route_wrapper_not_independent_axis'
    surface['geometry']=[{'lon':7,'lat':46},{'lon':7.001,'lat':46},{'lon':7,'lat':46.001},{'lon':7,'lat':46}]
    status,length,area=geometry_diagnostic(surface,role(surface),set())
    assert length is None and area>0
    axis=dict(type='way',nodes=[1,2],tags={},geometry=surface['geometry'][:2])
    status,length,area=geometry_diagnostic(axis,role(axis),{123})
    assert status=='surface_boundary_dual_role_pending' and length is None and area is None


def test_declared_surface_is_not_closed_or_repaired_artificially():
    surface=dict(type='way',nodes=[1,2,3],tags={'area':'yes'},geometry=[{'lon':7,'lat':46},{'lon':7.001,'lat':46},{'lon':7,'lat':46.001}])
    assert geometry_diagnostic(surface,role(surface),set())==('declared_surface_not_closed_no_repair',None,None)
