"""Catalogue provenance/latest-tile selection and no unapproved seam method."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data_collection.collect_terrain_extension_stage65 import literal_next
from src.descriptive.audit_native2m_reference_stage66 import neighbourhood
from src.descriptive.verify_piste_assignments_stage51 import sha

ROOT = Path(__file__).resolve().parents[1]


def test_all39new_catalogues_and_original_stluc_reused():
    queue = json.loads((ROOT / 'config/terrain_group_catalogue_sources_stage65.json').read_text(encoding='utf8'))
    assert len(queue) == 39 and len({s['station_group_id'] for s in queue}) == 39
    assert not any(s['station_group_id'] == 'MP_GROUP_RESORT__st_luc_chandolin' for s in queue)
    events = json.loads((ROOT / 'data_interim/terrain_catalogue_events_stage65.json').read_text(encoding='utf8'))
    assert len(events) == 40 and all(e['status'] == 'downloaded' and int(e['HTTP_status']) == 200 for e in events)
    assert len({e['source_id'] for e in events}) == 40


def test_native2m_catalogue_all70groups_and_latestpernative_tile():
    assets = pd.read_csv(ROOT / 'data_processed/terrain_group_native2m_asset_inventory_stage65.csv')
    groups = pd.read_csv(ROOT / 'data_processed/terrain_group_catalogue_coverage_stage65.csv')
    assert len(groups) == 70 and groups.group_retained.all() and not groups.station_group_id.duplicated().any()
    assert groups.catalogue_status.eq('complete_original_pages').sum() == 40
    assert len(assets) == 1053 and assets.asset_url.nunique() == 1036
    assert assets.asset_grid_resolution_m.eq(2).all() and assets.asset_horizontal_epsg.eq(2056).all()
    latest = assets.groupby(['station_group_id', 'native_tile_key']).item_reference_datetime.transform('max')
    assert assets.latest_reference_for_native_tile.equals(assets.item_reference_datetime.eq(latest))
    assert assets.tile_vintage_selection_applied.all()
    assert not assets.duplicated(['station_group_id', 'asset_id']).any()
    assert not assets[assets.latest_reference_for_native_tile].duplicated(['station_group_id', 'native_tile_key']).any()
    assert groups.latest_axis_mixed_reference_dates.eq(True).sum() == 6


def test_global_reference_queue_deduplicates_and_reuses42originals():
    queue = json.loads((ROOT / 'config/terrain_reference_tile_sources_stage66.json').read_text(encoding='utf8'))
    assert len(queue) == 499 and len({s['url'] for s in queue}) == 499 and len({s['native_tile_key'] for s in queue}) == 499
    assert sum(s['source_id'].startswith('SWISSTOPO_ALTI3D_TILE_STAGE62_') for s in queue) == 42
    assert all(len(s['expected_sha256']) == 64 for s in queue)


@pytest.mark.parametrize('url', ['https://example.org/items', 'http://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.swissalti3d/items'])
def test_no_untrusted_or_guessed_pagination(url):
    with pytest.raises(ValueError):
        literal_next({'links': [{'rel': 'next', 'href': url}]})
    assert literal_next({'links': []}) is None


def test_singleedition_native_neighbours_horn_and_orientation():
    tile = dict(source_id='fixture', item_reference_datetime='fixture2024', left=0., top=1000.)
    z, _, dates, mixed, status, slope, angle = neighbourhood(501., 501., {(0, 0): tile}, lambda sid, r, c: float(c * 2))
    assert np.isfinite(z).all() and dates == ['fixture2024'] and not mixed and status == 'computed_same_edition'
    assert slope == pytest.approx(45) and angle == pytest.approx(270)


def test_mixededition_complete_native_values_are_not_missing_but_gradient_is_deferred():
    lookup = {(0, 0): dict(source_id='fixtureWest', item_reference_datetime='fixture2024', left=0., top=1000.),
              (1000, 0): dict(source_id='fixtureEast', item_reference_datetime='fixture2025', left=1000., top=1000.)}
    z, sources, dates, mixed, status, slope, angle = neighbourhood(999., 501., lookup, lambda sid, r, c: 100.)
    assert np.isfinite(z).all() and len(sources) == 2 and len(dates) == 2 and mixed
    assert status == 'awaiting_mixed_edition_rule' and slope is None and angle is None


def test_missing_neighbours_no_edge_interpolation_or_fabricated_flat():
    tile = dict(source_id='fixture', item_reference_datetime='fixture2024', left=0., top=1000.)
    z, _, _, mixed, status, slope, angle = neighbourhood(999., 501., {(0, 0): tile}, lambda sid, r, c: 100.)
    assert np.isfinite(z).sum() == 6 and not mixed and status == 'missing_native_neighbours'
    assert slope is None and angle is None


def test_flat_sameedition_no_extra_threshold():
    tile = dict(source_id='fixture', item_reference_datetime='fixture2024', left=0., top=1000.)
    _, _, _, _, status, slope, angle = neighbourhood(501., 501., {(0, 0): tile}, lambda sid, r, c: 100.)
    assert status == 'computed_same_edition' and slope == 0 and angle is None


def test_immutable_catalogue_outputs_and_documentary_corrections():
    state = json.loads((ROOT / 'reports/terrain_catalogue_extension_stage65_summary.json').read_text(encoding='utf8'))
    assert all(sha(p) == h for p, h in {**state['input_sha256'], **state['output_sha256']}.items())
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    corrections = json.loads((ROOT / 'config/terrain_catalogue_dictionary_corrections_stage65.json').read_text(encoding='utf8'))
    for c in corrections['corrections']:
        row = dictionary[dictionary.table.eq(c['table']) & dictionary.variable.eq(c['variable'])]
        assert len(row) == 1 and row.iloc[0].description == c['new_description_and_formula']
        assert row.iloc[0].formula == c['new_description_and_formula']
