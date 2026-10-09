import json
from pathlib import Path


def test_authorised_axes_and_surfaces_have_disjoint_roles():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root/'config/winter_profile_geometry_roles_decisions_stage49.json').read_text(encoding='utf-8'))
    assert config['both_axes_and_surfaces_retained']
    assert config['axes']['dem_grid_resolution_m'] == 2
    assert config['axes']['altitude_mean_weight'] == 'line_length'
    assert config['surfaces']['metrics'] == ['mapped_piste_area_ha','mapped_piste_area_km2']
    assert config['surfaces']['overlapping_footprints_union_required']
    assert not config['line_and_surface_weights_may_be_mixed']
    assert not config['artificial_centerline_from_polygon_allowed']
    assert not config['surfaces']['used_for_altitude_slope_aspect_or_snow_weights']
    assert config['ambiguous_closed_way_interpretation'] is None
    assert config['terrain_flat_aspect_threshold_degrees'] is None
    assert not config['automatic_group_or_municipality_exclusion_approved']
    assert not config['snow_model_splicing_or_calibration_approved']
    assert not config['clustering_fit_approved']
    assert all((root/path).is_file() for path in config['parent_decisions'])


def test_seven_ambiguous_ways_retained_until_review_without_group_removal():
    root=Path(__file__).resolve().parents[1]
    decision=json.loads((root/'config/piste_ambiguous_geometry_decisions_stage49.json').read_text(encoding='utf-8'))
    assert len(set(decision['osm_way_ids']))==7
    assert decision['retain_ambiguous_objects'] and decision['individual_verification_before_measure_required']
    assert not decision['count_as_axis_length_before_verification']
    assert not decision['count_as_mapped_area_before_verification']
    assert not decision['drop_their_station_groups']
    assert decision['geometry_interpretation'] is None
