import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.descriptive.build_approved_profile_context import build_context, OUTPUTS

ROOT = Path(__file__).resolve().parents[1]


def small_context(times):
    groups = pd.DataFrame([dict(station_group_id='g', station_group_name='G', first_base_entry_month='2025-05-01')])
    road = pd.DataFrame([dict(station_group_id='g', municipality_bfs_id=i, access_point_id='a',
        road_reference_minutes=t, unusable_access_count=0) for i, t in enumerate(times, 1)])
    origins = pd.DataFrame([dict(municipality_bfs_id=i, municipality_names_source=str(i),
        selected_stop_id=str(i), selected_stop_name=str(i)) for i in range(1, 7)])
    snaps = pd.DataFrame([dict(endpoint_role='station_stop', endpoint_id='a', max_geodesic_displacement_metres=123)])
    return build_context(groups, road, origins, snaps, list(range(1, 7)), pd.Timestamp('1961-09-01'), pd.Timestamp('2023-08-31'))


def test_minimum_keeps_ties_missing_and_original_minutes():
    frames = small_context([10, 10, 20, np.nan, 30, 40])
    g = frames['winter_profile_urban_minimum'].iloc[0]
    assert g.urban_min_road_minutes == 10
    assert g.minimum_city_bfs_ids == '1|2'
    assert g.available_city_count == 5 and not g.all_six_cities_available
    d = frames['winter_profile_urban_city_detail']
    assert len(d) == 6 and d.is_city_minimum.sum() == 2
    assert d.road_reference_minutes.isna().sum() == 1
    assert d.arrival_max_snap_metres.eq(123).all()


def test_missing_all_cities_is_not_zero_and_negative_rejected():
    assert pd.isna(small_context([np.nan] * 6)['winter_profile_urban_minimum'].iloc[0].urban_min_road_minutes)
    with pytest.raises(ValueError, match='Invalid road time'):
        small_context([-1, 10, 20, 30, 40, 50])


def test_five_own_preentry_winters_without_archive_truncation():
    w = small_context([1] * 6)['winter_profile_approved_snow_windows']
    assert set(w.winter_start_year) == {2020, 2021, 2022, 2023, 2024}
    # 2025-05 entry has last completed winter 2024/25, not 2023/24.
    assert w.winter_start_year.max() == 2024


def test_outputs_exact_parent_values_all_groups_snapshots_and_registry():
    d, g, w = [pd.read_csv(ROOT / p) for p in OUTPUTS.values()]
    road = pd.read_csv(ROOT / 'data_processed/accessibility_road_did_group_reference.csv')
    expected = road[road.municipality_bfs_id.isin([261, 351, 2701, 5192, 5586, 6621])]
    assert len(d) == 426 and len(g) == 71 and len(w) == 355
    assert g.all_six_cities_available.all()
    assert not d[['origin_max_snap_metres', 'arrival_max_snap_metres']].isna().any().any()
    assert not d.duplicated(['municipality_bfs_id', 'station_group_id']).any()
    pd.testing.assert_series_equal(d.set_index(['municipality_bfs_id', 'station_group_id']).road_reference_minutes.sort_index(),
        expected.set_index(['municipality_bfs_id', 'station_group_id']).road_reference_minutes.sort_index(), check_dtype=False)
    assert g.set_index('station_group_id').urban_min_road_minutes.sort_index().equals(expected.groupby('station_group_id').road_reference_minutes.min().sort_index().rename('urban_min_road_minutes'))
    assert w.groupby('station_group_id').size().eq(5).all()
    assert (pd.to_datetime(w.winter_end_date) < pd.to_datetime(w.first_base_entry_month)).all()
    assert (~w.spass_calendar_within_archive).sum() == 23
    assert w.loc[~w.spass_calendar_within_archive].station_group_id.nunique() == 14
    assert not w.snow_mean_computed.any()
    meta = json.loads((ROOT / 'reports/approved_profile_context_summary.json').read_text(encoding='utf-8'))
    for path, value in {**meta['input_sha256'], **meta['output_sha256'], **meta['protected_legacy_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == value, path
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv')
    assert not sources.source_id.duplicated().any()
    assert not dictionary.duplicated(['table', 'variable']).any()
    for table in OUTPUTS:
        assert set(dictionary[dictionary.table.eq(table)].variable) == set(pd.read_csv(ROOT / OUTPUTS[table]).columns)
