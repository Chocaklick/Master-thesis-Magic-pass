import hashlib
import json
from pathlib import Path

import pandas as pd

from src.descriptive.audit_winter_profile_design import winter_dates, complete_windows, overlap_components

ROOT = Path(__file__).resolve().parents[1]


def test_winter_calendar_and_missing_april_not_zero():
    broad = winter_dates(2025, 'nov_apr')
    assert list(broad.month) == [11, 12, 1, 2, 3, 4]
    assert broad[-1] == pd.Timestamp('2026-04-01')
    unit = pd.DataFrame({'date': broad[:-1], 'hotel_overnights': [0., 1., 2., 3., 4.]})
    assert not complete_windows(unit, [2025], 'nov_apr')[2025]
    assert complete_windows(unit, [2025], 'dec_mar')[2025]


def test_shared_group_overlap_keeps_distinct_municipalities():
    links = pd.DataFrame({'municipality_bfs_id': [1, 2, 2, 3, 4], 'station_group_id': ['a', 'a', 'b', 'b', 'c']})
    assert overlap_components(links) == [3, 1]


def test_group_profile_audit_has_no_preentry_or_new_category_approval():
    group = pd.read_csv(ROOT / 'reports/winter_profile_group_audit.csv')
    original = pd.read_csv(ROOT / 'data_processed/accessibility_station_groups.csv')
    pd.testing.assert_frame_equal(group[original.columns], original)
    assert len(group) == 71
    assert not group.preentry_structure_verified.any()
    assert group.existing_segment_link_status.eq('single_existing_class').sum() == 66
    assert group.existing_segment_link_status.eq('no_linked_class').sum() == 5


def test_all_territories_and_windows_remain_with_missing_support_visible():
    unit = pd.read_csv(ROOT / 'reports/winter_profile_municipality_support_audit.csv')
    assert len(unit) == 185 * 3 * 2
    assert not unit.duplicated(['threshold_minutes', 'winter_definition', 'municipality_bfs_id']).any()
    assert unit.groupby(['threshold_minutes', 'winter_definition']).municipality_bfs_id.nunique().eq(185).all()
    sub = unit[unit.threshold_minutes.eq(30) & unit.winter_definition.eq('nov_apr')]
    exposed = sub[sub.first_winter_exposure_month.notna()]
    assert len(exposed) == 58
    assert exposed.first_winter_trigger_group_count.gt(1).sum() == 33
    assert exposed.ever_multiple_active_groups.sum() == 45
    assert (exposed.complete_pre_winter_count.ge(1) & exposed.complete_post_winter_count.ge(1)).sum() == 49
    recent = exposed[exposed.first_winter_exposure_month.eq('2025-11-01')]
    assert len(recent) == 6 and not recent.first_post_winter_complete.any()


def test_audit_manifests_and_prior_results_are_intact():
    meta = json.loads((ROOT / 'reports/winter_profile_design_audit_summary.json').read_text(encoding='utf-8'))
    assert not meta['effect_estimation_run']
    assert not meta['automatic_exclusion_applied']
    assert not meta['classifications_changed']
    assert not meta['summer_status_transferred']
    for path, expected in {**meta['input_sha256'], **meta['output_sha256'], **meta['protected_legacy_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    source = pd.read_csv(ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv')
    assert not source.source_id.duplicated().any()
    assert not dictionary.duplicated(['table', 'variable']).any()
    for name in ['winter_profile_group_audit', 'winter_profile_municipality_support_audit']:
        assert set(dictionary.loc[dictionary.table.eq(name), 'variable']) == set(pd.read_csv(ROOT / f'reports/{name}.csv').columns)
