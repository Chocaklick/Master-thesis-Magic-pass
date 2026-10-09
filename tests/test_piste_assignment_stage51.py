import pytest
from src.descriptive.verify_piste_assignments_stage51 import validate_case, host


def example():
    case = dict(station_group_id='G', osm_site_relation_id=1, required_operator_markers=['Operator', 'Lift'],
        verified_lift_way_ids=[10], geographic_review_status='reviewed_current_scope_coherent')
    site = dict(osm_relation_id=1, cycle_relation_ids=[])
    return case, site


def test_independent_markers_and_manual_review_required():
    case, site = example()
    validate_case(case, {'G'}, site, 'Operator Lift', {10})
    with pytest.raises(ValueError): validate_case(case, {'G'}, site, 'Operator', {10})
    case['geographic_review_status'] = 'nearest_name_match'
    with pytest.raises(ValueError): validate_case(case, {'G'}, site, 'Operator Lift', {10})


def test_missing_stable_key_or_lift_and_cycles_fail():
    case, site = example()
    with pytest.raises(ValueError): validate_case(case, {'H'}, site, 'Operator Lift', {10})
    with pytest.raises(ValueError): validate_case(case, {'G'}, site, 'Operator Lift', {11})
    site['cycle_relation_ids'] = [1]
    with pytest.raises(ValueError): validate_case(case, {'G'}, site, 'Operator Lift', {10})


def test_www_host_is_not_name_or_radius_rule():
    assert host('https://www.operator.ch/fr/') == host('https://operator.ch/')
    assert host('https://other.ch/operator.ch') != host('https://operator.ch/')
