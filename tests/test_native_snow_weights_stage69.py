"""Native footprints preserve axes, actual source indexing and calendars."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from shapely import wkt
from shapely.geometry import LineString

from src.data_processing.prepare_native_snow_weights_stage69 import native_grid, ensure_nested, index_at
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

ROOT = Path(__file__).resolve().parents[1]


def test_native_grid_orders_and_refinement_boundary_ownership():
    coarse = native_grid(np.array([500,1500]),np.array([500,1500]))
    fine = native_grid(np.arange(125,2000,250),np.arange(1875,0,-250))
    ensure_nested(coarse,fine)
    assert index_at(125,1875,coarse) == (0,1,True)
    assert index_at(125,1875,fine) == (0,0,True)
    assert type(coarse['north_ascending']) is bool
    line = LineString([(1000,100),(1000,1900)])
    weights = cell_lengths(line,fine['left'],fine['top'],250,250)
    assert math.fsum(weights.values()) == pytest.approx(line.length)
    assert {c for r,c in weights} == {4}
    broken = {**fine,'left':fine['left']+1}
    with pytest.raises(ValueError,match='not nested'):
        ensure_nested(coarse,broken)


def test_actual_weights_equal_independent_coarse_partition():
    s=json.loads((ROOT/'reports/native_snow_weights_stage69_summary.json').read_text(encoding='utf8'))
    f=pd.read_csv(ROOT/'data_processed/native_snow_cell_pairs_stage69.csv',float_precision='round_trip')
    network=json.loads((ROOT/'data_interim/winter_profile_exact_network_stage63.json').read_text(encoding='utf8'))
    g=s['original_grid_axes']['spass']
    for r in network:
        if not r['exact_unique_axis_wkt']:
            continue
        geometry=wkt.loads(r['exact_unique_axis_wkt'])
        direct=cell_lengths(geometry,g['left'],g['top'],1000,1000)
        direct={(c,g['north_count']-1-row):length for (row,c),length in direct.items()}
        grouped=f[f.station_group_id.eq(r['station_group_id'])].groupby(['spass_e_index','spass_n_index']).unique_axis_length_m.sum().to_dict()
        assert grouped.keys()==direct.keys()
        for k in direct:
            assert grouped[k]==pytest.approx(direct[k],rel=1e-12,abs=1e-10)
    assert len(f)==1852 and f.spass_cell_in_grid.all() and f.oshd_cell_in_grid.all()
    assert f.unique_axis_length_m.gt(0).all()
    assert f.spass_cell_centre_east_2056.eq(2474500+1000*f.spass_e_index).all()
    assert f.spass_cell_centre_north_2056.eq(1059500+1000*f.spass_n_index).all()
    assert f.oshd_cell_centre_east_2056.eq(2478125+250*f.oshd_e_index).all()
    assert f.oshd_cell_centre_north_2056.eq(1319375-250*f.oshd_n_index).all()


def test_all_groups_and_dates_preserved_not_snow_coverage():
    f=pd.read_csv(ROOT/'data_processed/native_snow_weight_coverage_stage69.csv',float_precision='round_trip')
    prior=pd.read_csv(ROOT/'data_processed/terrain_reference_profiles_stage67.csv',float_precision='round_trip')
    pd.testing.assert_series_equal(f.station_group_id,prior.station_group_id)
    pd.testing.assert_series_equal(f.unique_mapped_axis_length_m,prior.unique_mapped_axis_length_m)
    assert len(f)==70 and f.group_retained.all() and not f.snow_values_read.any()
    assert f.cell_pair_count.notna().sum()==40
    assert f.loc[f.cell_pair_count.isna(),'both_native_grid_length_share'].isna().all()
    dates=pd.read_csv(ROOT/'data_processed/native_snow_date_pairs_stage69.csv')
    assert len(dates)==453 and dates.both_calendar_dates_available.all()
    assert dates.groupby('oshd_date_offset_days').size().to_dict()=={-1:151,0:151,1:151}
    diff=(pd.to_datetime(dates.oshd_civil_date)-pd.to_datetime(dates.spass_civil_date)).dt.days
    assert diff.eq(dates.oshd_date_offset_days).all()
    assert pd.to_datetime(dates.spass_original_timestamp).dt.hour.eq(0).all()
    assert pd.to_datetime(dates.oshd_original_timestamp).dt.hour.eq(6).all()
    assert dates.oshd_time_units.str.contains('UTC\\+01:00').all()


def test_registry_prior_rows_exact_and_no_analytical_unit_conversion():
    s=json.loads((ROOT/'reports/native_snow_weights_stage69_summary.json').read_text(encoding='utf8'))
    for path,b in s['prior_registry_rows_and_digest'].items():
        f=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        assert row_digest(f.iloc[:b['rows']])==b['sha256']
    assert not s['snow_values_read'] and not s['new_unit_conversion_or_splice']
    assert s['decisions']['five_own_preentry_winters_unchanged']
