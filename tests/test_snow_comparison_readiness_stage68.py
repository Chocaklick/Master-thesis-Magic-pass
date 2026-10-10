"""No calendar audit silently becomes a snow measurement or exclusion."""
import json
from pathlib import Path

import pandas as pd

from src.descriptive.audit_snow_comparison_readiness_stage68 import metadata_dates
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

ROOT = Path(__file__).resolve().parents[1]


def test_retained_universe_windows_and_potential_missing_calendar_coverage():
    f = pd.read_csv(ROOT / 'data_processed/snow_comparison_readiness_stage68.csv')
    groups = pd.read_csv(ROOT / 'data_processed/terrain_reference_profiles_stage67.csv')
    pd.testing.assert_series_equal(f.station_group_id, groups.station_group_id)
    assert len(f) == 70 and f.group_retained.all() and not f.snow_feature_computed.any()
    assert f.requested_own_preentry_winters.eq(5).all()
    assert f.spass_calendar_available_winters.sum() == 327 and f.spass_calendar_missing_winters.sum() == 23
    assert f.missing_spass_with_downloaded_oshd_calendar_winters.sum() == 23
    assert f.mapped_axis_geometry_available.sum() == 40
    assert f.within_spass_centre_envelope.eq(True).sum() == 40
    assert f.within_oshd_centre_envelope.eq(True).sum() == 40
    assert f.loc[~f.mapped_axis_geometry_available, 'axis_min_east_2056'].isna().all()
    assert f.loc[~f.mapped_axis_geometry_available, 'within_spass_centre_envelope'].isna().all()


def test_common_calendar_not_new_fivewinter_baseline_or_unit_conversion():
    s = json.loads((ROOT / 'reports/snow_comparison_readiness_stage68_summary.json').read_text(encoding='utf8'))
    assert s['complete_downloaded_month_count'] == 36 and s['downloaded_oshd_days'] == 1096
    assert s['downloaded_model_common_days'] == 365 and s['candidate_winter_days'] == 151 and s['candidate_winter_calendar_complete']
    assert not s['snow_values_read'] and not s['snow_features_computed'] and not s['spatial_mapping_applied'] and not s['model_splicing_or_unit_conversion_applied']
    assert s['unit_review']['raw_HSCLQMD_unit_attribute'] == 'UNKNOWN'
    assert s['unit_review']['paper_analytical_HS_unit'] == 'centimetres'
    assert not s['unit_review']['paper_unit_proves_distributed_numeric_scale']
    assert not s['unit_review']['new_conversion_applied']


def test_daily_metadata_gaps_rejected_not_interpolated():
    import pytest
    a = dict(axis=dict(missing_count=0,strictly_increasing=True,difference_min=1,difference_max=1,
                       decoded_first='2022-12-01 06:00:00',decoded_last='2022-12-03 06:00:00',observed_count=3))
    assert len(metadata_dates(a)) == 3
    a['axis']['observed_count'] = 2
    with pytest.raises(ValueError,match='count differs'):
        metadata_dates(a)
    a['axis']['difference_max'] = 2
    with pytest.raises(ValueError,match='complete daily'):
        metadata_dates(a)


def test_registry_prefixes_and_readiness_roles_preserved():
    s = json.loads((ROOT / 'reports/snow_comparison_readiness_stage68_summary.json').read_text(encoding='utf8'))
    for path,b in s['prior_registry_rows_and_digest'].items():
        f = pd.read_csv(ROOT / path,dtype=str,keep_default_na=False)
        assert row_digest(f.iloc[:b['rows']]) == b['sha256']
    d = pd.read_csv(ROOT / 'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    rows = d[d.table.eq('snow_comparison_readiness_stage68')]
    assert len(rows) == 20 and rows.causal_role.str.contains('not analytical snowfeature').all()
