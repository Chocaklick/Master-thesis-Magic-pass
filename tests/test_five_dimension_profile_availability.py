import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from src.descriptive.audit_five_dimension_profile_availability import (
    expected_days, last_preentry_winter, snow_counts, winter_end,
)

ROOT = Path(__file__).resolve().parents[1]


def test_winter_is_december_april_and_ends_strictly_before_entry():
    assert expected_days(2011) == 152
    assert expected_days(2012) == 151
    assert winter_end(2016) == pd.Timestamp('2017-04-30')
    assert last_preentry_winter(pd.Timestamp('2017-11-01')) == 2016
    assert last_preentry_winter(pd.Timestamp('2019-05-01')) == 2018
    assert last_preentry_winter(pd.Timestamp('2019-01-01')) == 2017
    assert last_preentry_winter(pd.Timestamp('2019-04-30')) == 2017


def test_zero_snow_is_observed_negative_and_missing_are_not():
    raw = pd.DataFrame({'station_code': ['a'] * 5,
        'measure_date': ['2016-12-01', '2017-01-01', '2017-02-01', '2017-04-01', '2017-05-01'],
        'HS': ['0', '-1', None, '12', '8']})
    assert snow_counts(raw, {'a'}) == {('a', 2016): 2}


def test_duplicate_station_day_rejected_not_averaged():
    raw = pd.DataFrame({'station_code': ['a', 'a'],
        'measure_date': ['2016-12-01 00:00', '2016-12-01 12:00'], 'HS': [1, 2]})
    with pytest.raises(ValueError, match='Duplicate source station-day'):
        snow_counts(raw, {'a'})


def test_inventory_preserves_all_groups_and_source_component_values():
    groups = pd.read_csv(ROOT / 'data_processed/winter_profile_five_dimension_groups.csv')
    components = pd.read_csv(ROOT / 'data_processed/winter_profile_five_dimension_components.csv')
    original = pd.read_csv(ROOT / 'data_processed/accessibility_station_groups.csv')
    master = pd.read_csv(ROOT / 'data_processed/resort_master.csv').set_index('resort_id')
    assert set(groups.station_group_id) == set(original.station_group_id)
    assert len(groups) == 71 and len(components) == 67
    assert not groups.station_group_id.duplicated().any()
    assert not components.duplicated(['station_group_id', 'resort_id']).any()
    assert groups.component_listing_count.sum() == len(components)
    for field, parent in [('current_ski_area_km', 'ski_area_km'), ('current_number_lifts', 'number_lifts'), ('current_altitude_top_m', 'altitude_top_m')]:
        pd.testing.assert_series_equal(components.set_index('resort_id')[field].sort_index(),
            master.loc[components.resort_id, parent].sort_index(), check_names=False, check_dtype=False)
    assert not groups.verified_preentry_structure.any()
    assert not groups.domain_orientation_available.any()
    assert not groups.five_dimension_clustering_ready.any()
    assert not groups.urban_context_all_components_predate_entry.any()
    assert groups.cached_city_road_reference_count.eq(6).all()
    assert groups.cached_city_road_context_all_available.all()
    assert not groups.cached_city_road_profile_selected.any()
    assert not components.snow_proxy_assignment_historically_verified.any()


def test_snow_coverage_no_postentry_no_imputation_and_common_not_selected():
    snow = pd.read_csv(ROOT / 'data_processed/winter_profile_preentry_snow_coverage.csv')
    assert (pd.to_datetime(snow.winter_end_date) < pd.to_datetime(snow.first_base_entry_month)).all()
    assert (snow.snow_valid_days >= 0).all()
    assert (snow.snow_valid_days <= snow.snow_expected_days).all()
    assert not snow.duplicated(['station_group_id', 'resort_id', 'winter_start_year']).any()
    assert set(snow.loc[snow.in_common_five_winter_candidate, 'winter_start_year']) == set(range(2012, 2017))
    assert snow.groupby(['station_group_id', 'resort_id']).in_entry_specific_five_winter_candidate.sum().eq(5).all()
    assert (snow.snow_coverage_share - snow.snow_valid_days / snow.snow_expected_days).abs().max() < 1e-12


def test_manifest_all_sources_and_old_results_protected():
    meta = json.loads((ROOT / 'reports/five_dimension_profile_availability_summary.json').read_text(encoding='utf-8'))
    assert not meta['clustering_fitted'] and not meta['effect_estimation_run']
    assert not meta['automatic_exclusion_applied']
    for path, expected in {**meta['input_sha256'], **meta['output_sha256'], **meta['protected_legacy_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv')
    assert not sources.source_id.duplicated().any()
    assert not dictionary.duplicated(['table', 'variable']).any()
    for table in ['winter_profile_five_dimension_groups', 'winter_profile_five_dimension_components', 'winter_profile_preentry_snow_coverage']:
        assert set(dictionary[dictionary.table.eq(table)].variable) == set(pd.read_csv(ROOT / f'data_processed/{table}.csv').columns)
