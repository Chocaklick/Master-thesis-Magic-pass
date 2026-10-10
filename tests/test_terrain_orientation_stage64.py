"""Synthetic mathematical edge cases, and original pilot reconciliation."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.descriptive.summarise_terrain_orientation_stage64 import summarise_cells
from src.descriptive.verify_piste_assignments_stage51 import sha

ROOT = Path(__file__).resolve().parents[1]


def fixture(angles, lengths=None, slopes=None):
    slopes = slopes if slopes is not None else [10. if a is not None else None for a in angles]
    return pd.DataFrame(dict(unique_axis_length_m=lengths if lengths is not None else [1.] * len(angles),
                             terrain_aspect_degrees=angles, terrain_slope_degrees=slopes,
                             gradient_observed=[s is not None for s in slopes],
                             flat_terrain=[s == 0 if s is not None else None for s in slopes]))


def test_exact_north_east_and_unequal_weights():
    r = summarise_cells(fixture([0., 90.], [3., 1.]))
    assert r['terrain_northness'] == pytest.approx(.75)
    assert r['terrain_eastness'] == pytest.approx(.25)
    assert r['orientation_resultant_concentration'] == pytest.approx(math.hypot(.75, .25))
    assert r['north_length_share'] == .75 and r['east_length_share'] == .25


def test_opposed_directions_zero_components_do_not_hide_cardinal_parts():
    r = summarise_cells(fixture([0., 180.]))
    assert r['terrain_northness'] == pytest.approx(0, abs=1e-15)
    assert r['terrain_eastness'] == pytest.approx(0, abs=1e-15)
    assert r['north_length_share'] == .5 and r['south_length_share'] == .5


def test_cardinal_boundaries_partition_once_and_cyclic_north():
    r = summarise_cells(fixture([0., 44.999, 45., 135., 225., 315., 359.999]))
    assert [r[d + '_length_share'] for d in ('north', 'east', 'south', 'west')] == pytest.approx([4/7, 1/7, 1/7, 1/7])


def test_flat_and_missing_gradients_not_assigned_north_or_zero_features():
    r = summarise_cells(fixture([0., None, None], [2., 3., 5.], [10., 0., None]))
    assert r['orientation_coverage_share'] == .2
    assert r['flat_observed_length_m'] == 3 and r['missing_gradient_length_m'] == 5
    assert r['terrain_northness'] == 1 and r['north_length_share'] == 1
    absent = summarise_cells(fixture([None, None], [3., 5.], [0., None]))
    assert absent['terrain_northness'] is None and absent['north_length_share'] is None
    assert absent['orientation_coverage_share'] == 0


@pytest.mark.parametrize('angles,lengths,slopes', [([360.], [1.], [10.]), ([0.], [-1.], [10.]),
                                                 ([None], [1.], [10.]), ([0.], [1.], [0.])])
def test_invalid_observations_fail_without_imputation(angles, lengths, slopes):
    with pytest.raises(ValueError):
        summarise_cells(fixture(angles, lengths, slopes))


def test_real_pilot_weighted_formula_independent_reconciliation():
    cells = pd.read_csv(ROOT / 'data_processed/terrain_native2m_pilot_cells_stage63.csv')
    out = pd.read_csv(ROOT / 'data_processed/terrain_orientation_edition_comparison_stage64.csv')
    for row in out.itertuples():
        p = cells[cells.edition_reference_datetime.eq(row.edition_reference_datetime)]
        a = np.deg2rad(p.terrain_aspect_degrees)
        assert row.terrain_northness == pytest.approx(np.average(np.cos(a), weights=p.unique_axis_length_m), abs=1e-14)
        assert row.terrain_eastness == pytest.approx(np.average(np.sin(a), weights=p.unique_axis_length_m), abs=1e-14)
        assert row.orientation_resultant_concentration == pytest.approx(math.hypot(row.terrain_northness, row.terrain_eastness))
        assert sum(getattr(row, d + '_length_share') for d in ('north', 'east', 'south', 'west')) == pytest.approx(1)


def test_all70groups_retained_and_only_one_latest_reference_per_group():
    groups = pd.read_csv(ROOT / 'data_processed/winter_profile_exact_piste_overlap_stage63.csv')
    out = pd.read_csv(ROOT / 'data_processed/terrain_orientation_reference_stage64.csv')
    assert len(out) == 70 and not out.station_group_id.duplicated().any() and out.group_retained.all()
    assert set(out.station_group_id) == set(groups.station_group_id)
    assert out.terrain_northness.notna().sum() == 1
    assert out.loc[out.terrain_northness.notna(), 'edition_reference_datetime'].tolist() == ['2024-01-01T00:00:00Z']
    assert out.loc[out.terrain_northness.isna(), 'orientation_resultant_concentration'].isna().all()
    pd.testing.assert_series_equal(out.station_group_name, groups.station_group_name, check_names=False)


def test_policy_and_frozen_source_integrity():
    d = json.loads((ROOT / 'config/terrain_orientation_decisions_stage64.json').read_text(encoding='utf8'))
    assert d['continuous_model_feature_candidates'] == ['terrain_northness', 'terrain_eastness']
    assert len(d['descriptive_only_not_automatic_model_features']) == 5
    assert not d['new_clustering_or_effect_fit_approved'] and not d['dominant_direction_imposed']
    s = json.loads((ROOT / 'reports/terrain_orientation_stage64_summary.json').read_text(encoding='utf8'))
    assert all(sha(p) == h for p, h in {**s['input_sha256'], **s['output_sha256']}.items())
