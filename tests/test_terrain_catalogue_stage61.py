"""Frozen source metadata is not silently converted to terrain observations."""
import json
from pathlib import Path
import pandas as pd
from src.descriptive.verify_piste_assignments_stage51 import sha
ROOT=Path(__file__).resolve().parents[1]


def test_all_native2m_editions_retained_and_no_reference_selection():
    f=pd.read_csv(ROOT/'data_processed/terrain_stluc_native2m_asset_inventory_stage61.csv')
    assert len(f)==84 and f.asset_url.is_unique
    assert f.asset_grid_resolution_m.eq(2).all() and f.asset_horizontal_epsg.eq(2056).all()
    assert f.intersects_current_axis_footprint.sum()==50
    assert set(f.item_reference_datetime.str[:4])=={'2019','2024'}
    assert not f.tile_vintage_selection_applied.any()
    assert f.asset_sha256.str.len().eq(64).all()


def test_literal_proprietary_marker_and_distinct_terms_remain_visible():
    s=json.loads((ROOT/'reports/terrain_catalogue_stage61_summary.json').read_text(encoding='utf8'))
    assert s['catalogue_license_literal']=='proprietary'
    assert s['terms_individually_verified'] and s['catalogue_license_not_relabelled']
    assert s['metadata_datetime_not_assumed_actual_acquisition']
    assert s['no_raster_download_or_vintage_selection'] and s['all_group_count_retained']==70


def test_every_frozen_pilot_input_and_output_unchanged():
    s=json.loads((ROOT/'reports/terrain_catalogue_stage61_summary.json').read_text(encoding='utf8'))
    assert all(sha(p)==h for p,h in {**s['input_sha256'],**s['output_sha256']}.items())
