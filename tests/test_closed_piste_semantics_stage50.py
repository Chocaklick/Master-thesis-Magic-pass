import pytest
from src.descriptive.audit_closed_piste_semantics_stage50 import semantic_review


def way(tags, nodes=None):
    return dict(type='way', nodes=nodes or [1,2,3,1], tags=dict({'piste:type':'downhill'}, **tags))


def test_landuse_supports_area_semantics_without_inventing_original_area_tag():
    original = way({'landuse':'piste'})
    assert semantic_review(original)[0] == 'implicit_piste_surface_semantics_supported'
    assert 'area' not in original['tags']


def test_bridge_outline_not_assumed_to_equal_piste_footprint():
    assert semantic_review(way({'man_made':'bridge','bridge':'yes'}))[0] == 'bridge_outline_supported_piste_footprint_unverified'


def test_school_and_tunnel_remain_unresolved_not_axes_from_closure():
    assert semantic_review(way({'amenity':'ski_school'}))[0] == 'school_extent_role_unresolved'
    assert semantic_review(way({'tunnel':'yes'}))[0] == 'tunnel_closed_role_unresolved'


def test_no_nonclosed_or_explicit_geometry_silently_reclassified():
    with pytest.raises(ValueError):
        semantic_review(way({'landuse':'piste'}, [1,2,3]))
    with pytest.raises(ValueError):
        semantic_review(way({'landuse':'piste','area':'no'}))
