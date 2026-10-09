import pandas as pd
import pytest

from src.descriptive.audit_official_piste_pages_stage49 import Headings, coverage


def test_coverage_retains_fallback_and_multiple_accesses_without_assignment():
    groups = pd.DataFrame([dict(station_group_id='a', station_group_name='Same name'),
                           dict(station_group_id='b', station_group_name='Same name')])
    links = [dict(station_group_id='a', source_id='s'), dict(station_group_id='a', source_id='s'),
             dict(station_group_id='b', source_id=None)]
    result = coverage(groups, links, {'s'})
    assert result.station_group_id.tolist() == ['a', 'b']
    assert result.access_point_count.tolist() == [2, 1]
    assert result.verified_archived_page_count.tolist() == [1, 0]
    assert result.fallback_reference_count.tolist() == [0, 1]
    assert not result.gis_assignment_verified.any()
    assert not result.historical_scope_verified.any()
    assert not result.automatic_exclusion_applied.any()
    with pytest.raises(ValueError):
        coverage(groups, links[:2], {'s'})


def test_headings_are_literal_not_scope_matching():
    parser = Headings()
    parser.feed('<h1>Station <span>Nord &amp; Sud</span></h1><p>Other station</p>')
    assert parser.headings == ['Station Nord & Sud']
