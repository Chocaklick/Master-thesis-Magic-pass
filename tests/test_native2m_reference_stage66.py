"""Real native source checks; incomplete/unapproved cells never fabricated."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
TABLE = 'data_processed/terrain_native2m_reference_audit_stage66.csv'


def test_all499actual_native_headers_and_all70groups_retained():
    state = json.loads((ROOT / 'reports/native2m_reference_stage66_summary.json').read_text(encoding='utf8'))
    assert state['original_latest_tiles_verified'] == 499 and len(state['header_checks']) == 499
    assert all(h['shape'] == [500, 500] and h['resolution'] == [2., 2.] and h['units'] == ['metre'] and h['crs'] == 'EPSG:2056' for h in state['header_checks'])
    groups = pd.read_csv(ROOT / TABLE)
    old = pd.read_csv(ROOT / 'data_processed/winter_profile_exact_piste_overlap_stage63.csv')
    assert len(groups) == 70 and groups.group_retained.all() and not groups.station_group_id.duplicated().any()
    pd.testing.assert_series_equal(groups.station_group_id, old.station_group_id, check_names=False)
    pd.testing.assert_series_equal(groups.unique_mapped_axis_length_m, old.exact_unique_mapped_axis_length_m, check_names=False)
    assert groups.observed_altitude_length_m.notna().sum() == 40


def test_all_cell_weights_coverage_and_pending_methods_reconcile():
    groups = pd.read_csv(ROOT / TABLE)
    for g in groups[groups.cell_detail_file.notna()].itertuples():
        f = pd.read_csv(ROOT / g.cell_detail_file, low_memory=False, float_precision='round_trip')
        assert not f.duplicated(['cell_centre_east_2056', 'cell_centre_north_2056']).any()
        assert f.station_group_id.eq(g.station_group_id).all() and (f.unique_axis_length_m > 0).all()
        np.testing.assert_allclose(math.fsum(f.unique_axis_length_m), g.unique_mapped_axis_length_m, rtol=1e-12)
        np.testing.assert_allclose(g.observed_altitude_length_m + g.missing_altitude_length_m, g.unique_mapped_axis_length_m, rtol=1e-12)
        np.testing.assert_allclose(g.complete_native_neighbourhood_length_m + g.missing_native_neighbourhood_length_m, g.unique_mapped_axis_length_m, rtol=1e-12)
        pending = f.horn_complete_native_neighbourhood & f.mixed_reference_neighbourhood
        assert f.loc[pending, 'horn_calculation_status'].eq('awaiting_mixed_edition_rule').all()
        assert f.loc[pending, 'terrain_slope_degrees'].isna().all() and f.loc[pending, 'terrain_aspect_degrees'].isna().all()
        assert not f.loc[pending, 'gradient_observed'].any()
        np.testing.assert_allclose(math.fsum(f.loc[pending, 'unique_axis_length_m']), g.mixed_edition_complete_neighbourhood_length_m, atol=1e-10)
        if pending.any():
            assert g.terrain_status == 'awaiting_mixed_edition_rule' and pd.isna(g.terrain_northness) and pd.isna(g.terrain_eastness)
        assert f.loc[~f.horn_complete_native_neighbourhood, 'terrain_slope_degrees'].isna().all()
        assert f.loc[f.terrain_slope_degrees.eq(0), 'terrain_aspect_degrees'].isna().all()


def test_direct_original_centre_values_from_each_extracted_group():
    groups = pd.read_csv(ROOT / TABLE)
    for g in groups[groups.cell_detail_file.notna()].itertuples():
        # Preserve the serialized IEEE value exactly; the default decimal parser
        # can introduce one-ULP differences although the original CSV is exact.
        f = pd.read_csv(ROOT / g.cell_detail_file, low_memory=False, float_precision='round_trip')
        observed = f[f.altitude_observed]
        if observed.empty:
            continue
        row = observed.iloc[len(observed) // 2]
        metas = list((ROOT / 'data_external/source_evidence').glob(row.centre_tile_source_id + '_*.metadata.json'))
        assert len(metas) == 1
        m = json.loads(metas[0].read_text(encoding='utf8'))
        with rasterio.open(ROOT / m['raw_file']) as d:
            altitude = next(d.sample([(row.cell_centre_east_2056, row.cell_centre_north_2056)]))[0]
        assert float(altitude) == row.altitude_m


def test_original_stluc_pilot_cell_centres_weights_values_and_components_preserved():
    old = pd.read_csv(ROOT / 'data_processed/terrain_native2m_pilot_cells_stage63.csv', float_precision='round_trip')
    old = old[old.edition_reference_datetime.eq('2024-01-01T00:00:00Z')]
    groups = pd.read_csv(ROOT / TABLE)
    g = groups[groups.station_group_id.eq('MP_GROUP_RESORT__st_luc_chandolin')].iloc[0]
    current = pd.read_csv(ROOT / g.cell_detail_file, low_memory=False, float_precision='round_trip')
    keys = ['cell_centre_east_2056', 'cell_centre_north_2056']
    compare = ['unique_axis_length_m', 'altitude_m', 'terrain_slope_degrees', 'terrain_aspect_degrees']
    assert len(old) == len(current) == 31806
    old, current = [f.sort_values(keys).reset_index(drop=True) for f in (old, current)]
    pd.testing.assert_frame_equal(old[keys], current[keys], check_dtype=False, check_exact=True)
    np.testing.assert_allclose(old[compare], current[compare], rtol=1e-12, atol=1e-10)
    reference = pd.read_csv(ROOT / 'data_processed/terrain_orientation_reference_stage64.csv')
    before = reference[reference.station_group_id.eq(g.station_group_id)].iloc[0]
    for col in ['terrain_northness', 'terrain_eastness', 'orientation_resultant_concentration']:
        np.testing.assert_allclose(g[col], before[col], rtol=1e-12, atol=1e-12)
