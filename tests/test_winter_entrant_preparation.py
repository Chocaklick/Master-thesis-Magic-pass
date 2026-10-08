import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.descriptive.audit_winter_entrant_preparation import (
    complete_winter, active_ids, matrix_diagnostics, winter_dates,
)

ROOT = Path(__file__).resolve().parents[1]


def test_five_month_winter_preserves_true_zero_and_missing_april():
    dates = winter_dates(2025)
    assert list(dates.month) == [12, 1, 2, 3, 4]
    unit = pd.DataFrame({'date': dates, 'hotel_overnights': [0., 1., 2., 3., 4.]})
    assert complete_winter(unit, 2025)
    assert not complete_winter(unit.iloc[:-1], 2025)


def test_exit_inclusive_and_prior_portfolio_not_cumulative():
    links = pd.DataFrame({'station_group_id': ['a', 'b'],
        'winter': pd.to_datetime(['2017-11-01', '2019-11-01']),
        'last': pd.to_datetime(['2020-04-01', '2026-03-01'])})
    assert active_ids(links, pd.Timestamp('2020-04-01')) == {'a', 'b'}
    assert active_ids(links, pd.Timestamp('2020-10-01')) == {'b'}


def test_identical_positive_columns_joint_only_but_zeros_not_a_bundle():
    unit = np.repeat([1, 2, 3], 3)
    month = np.tile([1, 2, 3], 3)
    a = np.array([0, 0, 1, 0, 1, 1, 0, 0, 0], dtype=bool)
    m = np.column_stack([a, a, np.zeros(9, dtype=bool)])
    numerical = {'projection_tolerance': 1e-12, 'projection_maximum_iterations': 10000,
                 'nullspace_loading_tolerance': 1e-8}
    identical, dependent, result = matrix_diagnostics(m, unit, month, numerical)
    assert identical == {0: [1], 1: [0], 2: []}
    assert result['fixed_effect_rank'] == 1
    assert dependent == {0, 1}


def test_published_inventory_not_selected_estimation_panel():
    groups = pd.read_csv(ROOT / 'reports/winter_entrant_group_audit.csv')
    events = pd.read_csv(ROOT / 'reports/winter_entrant_event_support.csv')
    features = pd.read_csv(ROOT / 'reports/winter_clustering_feature_readiness.csv')
    original = pd.read_csv(ROOT / 'data_processed/accessibility_station_groups.csv')
    assert len(groups) == 71 * 3
    assert not groups.duplicated(['threshold_minutes', 'station_group_id']).any()
    assert not events.duplicated(['threshold_minutes', 'municipality_bfs_id', 'entry_winter_anchor']).any()
    assert set(features.station_group_id) == set(original.station_group_id)
    assert not features.clustering_fit_ready.any()
    assert not features.verified_preentry_structure.any()
    assert (groups.later_entry_alone_supported_same_portfolio_territories <= groups.later_entry_alone_complete_territories).all()
    assert (events.candidate_same_portfolio_history_complete_controls <= events.candidate_same_portfolio_complete_controls).all()
    recent = events[events.entry_winter_anchor.eq('2025-11-01')]
    assert not recent.previous_and_first_winter_complete.any()


def test_preparation_checkpoint_metadata_and_legacy_immutable():
    meta = json.loads((ROOT / 'reports/winter_entrant_preparation_summary.json').read_text(encoding='utf-8'))
    assert meta['territory_count'] == 185 and meta['group_count'] == 71
    assert not meta['effect_estimation_run'] and not meta['clustering_fitted']
    assert not meta['automatic_exclusion_applied']
    assert meta['thresholds']['30']['exposed_territories'] == 58
    assert meta['thresholds']['30']['later_entry_territories'] == 24
    for path, expected in {**meta['input_sha256'], **meta['output_sha256'], **meta['protected_legacy_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv')
    assert not sources.source_id.duplicated().any()
    assert not dictionary.duplicated(['table', 'variable']).any()
    for name in ['winter_entrant_group_audit', 'winter_entrant_event_support', 'winter_clustering_feature_readiness']:
        assert set(dictionary[dictionary.table.eq(name)].variable) == set(pd.read_csv(ROOT / f'reports/{name}.csv').columns)
