"""Approved local seam missingness: whole groups and source cells preserved."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from src.descriptive.summarise_terrain_orientation_stage64 import summarise_cells
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

ROOT = Path(__file__).resolve().parents[1]
TABLE = 'data_processed/terrain_reference_profiles_stage67.csv'


def test_decision_and_all70_groups_one_row_each():
    state = json.loads((ROOT / 'reports/terrain_reference_profiles_stage67_summary.json').read_text(encoding='utf8'))
    decision = state['decision']
    assert decision['researcher_reply'].startswith('Laisser pente et orientation manquantes')
    assert not decision['exclude_groups'] and not decision['interpolate_or_adjust_seams']
    f = pd.read_csv(ROOT / TABLE)
    old = pd.read_csv(ROOT / 'data_processed/terrain_native2m_reference_audit_stage66.csv')
    assert len(f) == 70 and f.group_retained.all() and not f.station_group_id.duplicated().any()
    pd.testing.assert_series_equal(f.station_group_id, old.station_group_id)
    assert f.observed_gradient_length_m.notna().sum() == 40
    assert f.terrain_northness.notna().sum() == 40 and f.terrain_eastness.notna().sum() == 40
    assert f.terrain_status.eq('native2m_reference_extracted_partial_gradient').sum() == 6
    assert f.terrain_status.eq('piste_scope_unresolved').sum() == 29
    assert f.terrain_status.eq('referenced_axes_missing').sum() == 1


def test_altitudes_lengths_and_previously_calculated_metrics_unchanged():
    f = pd.read_csv(ROOT / TABLE, float_precision='round_trip')
    old = pd.read_csv(ROOT / 'data_processed/terrain_native2m_reference_audit_stage66.csv', float_precision='round_trip')
    unchanged = ['station_group_id', 'unique_mapped_axis_length_m', 'native_axis_cell_count', 'reference_datetimes_on_axis',
                 'observed_altitude_length_m', 'missing_altitude_length_m', 'complete_native_neighbourhood_length_m',
                 'missing_native_neighbourhood_length_m', 'mixed_edition_complete_neighbourhood_length_m', 'mixed_edition_axis_share',
                 'minimum_observed_altitude_m', 'maximum_observed_altitude_m', 'length_weighted_observed_altitude_m',
                 'current_proxy_not_verified_preentry', 'cell_detail_file']
    pd.testing.assert_frame_equal(f[unchanged], old[unchanged], check_exact=True)
    ready = old.terrain_status.eq('native2m_reference_extracted')
    metrics = ['length_weighted_observed_slope_degrees', 'orientation_coverage_share', 'terrain_northness', 'terrain_eastness',
               'orientation_resultant_concentration', 'north_length_share', 'east_length_share', 'south_length_share', 'west_length_share']
    pd.testing.assert_frame_equal(f.loc[ready, metrics], old.loc[ready, metrics], check_exact=True)


def test_all40_summaries_recomputed_without_seam_imputation():
    f = pd.read_csv(ROOT / TABLE, float_precision='round_trip')
    for g in f[f.cell_detail_file.notna()].itertuples():
        c = pd.read_csv(ROOT / g.cell_detail_file, float_precision='round_trip', low_memory=False)
        seam = c.horn_complete_native_neighbourhood & c.mixed_reference_neighbourhood
        assert c.loc[seam, ['terrain_slope_degrees', 'terrain_aspect_degrees']].isna().all().all()
        assert not c.loc[seam, 'gradient_observed'].any()
        stats = summarise_cells(c)
        for col, value in stats.items():
            np.testing.assert_allclose(getattr(g, col), value, rtol=1e-12, atol=1e-10)
        observed = math.fsum(c.loc[c.gradient_observed, 'unique_axis_length_m'])
        np.testing.assert_allclose(observed, g.observed_gradient_length_m, rtol=1e-12)
        np.testing.assert_allclose(g.gradient_coverage_share, observed / g.unique_mapped_axis_length_m, rtol=1e-12)
        slope = np.average(c.loc[c.gradient_observed, 'terrain_slope_degrees'], weights=c.loc[c.gradient_observed, 'unique_axis_length_m'])
        np.testing.assert_allclose(slope, g.length_weighted_observed_slope_degrees, rtol=1e-12)
        np.testing.assert_allclose(g.missing_gradient_length_m, g.mixed_edition_complete_neighbourhood_length_m + g.missing_native_neighbourhood_length_m, atol=1e-10)


def test_registry_prefixes_and_descriptive_feature_roles():
    state = json.loads((ROOT / 'reports/terrain_reference_profiles_stage67_summary.json').read_text(encoding='utf8'))
    for path, baseline in state['prior_registry_rows_and_digest'].items():
        f = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
        assert row_digest(f.iloc[:baseline['rows']]) == baseline['sha256']
    d = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    d = d[d.table.eq('terrain_reference_profiles_stage67')].set_index('variable')
    assert len(d) == 35
    for col in ['orientation_resultant_concentration', 'north_length_share', 'east_length_share', 'south_length_share', 'west_length_share']:
        assert d.loc[col, 'causal_role'].startswith('Descriptive only')
    for col in ['terrain_northness', 'terrain_eastness']:
        assert d.loc[col, 'causal_role'].startswith('Approved continuous candidate')
