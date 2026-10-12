"""Approved car endpoint, exact source cells and no fictitious onward access."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Geod

from src.data_collection.collect_braunwald_urban_road_stage90 import (
    ROOT, DECISION, PREPARATION, COLLECTION, OUTPUTS, TABLES, ROUTE_SOURCE)
from src.data_processing.publish_braunwald_urban_road_stage90 import RESULTS, SUMMARY, SOURCE
from src.descriptive.check_national_preparation_stage87 import sha


def js(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def csv(path, **kwargs):
    return pd.read_csv(ROOT / path, float_precision='round_trip', **kwargs)


def test_exact_approved_valley_stop_preserves_historical_pending_proposal():
    d, p = js(DECISION), js('reports/braunwald_road_arrival_proposal_stage89.json')
    a = csv(OUTPUTS['braunwald_urban_arrival_stage90'], dtype={'selected_stop_id': str}).iloc[0]
    assert d['status'] == 'researcher_validated'
    assert d['approval_user_text'] == "oui je valide l'arret inférieur"
    assert d['selected_stop_id'] == p['proposed_stop_id'] == a.selected_stop_id == '8503260'
    assert a.selected_stop_name == 'Linthal Braunwaldbahn (Talst.)'
    assert a.bav_easting_2056 == 2719079 and a.bav_northing_2056 == 1198680
    assert a.road_arrival_longitude == p['proposed_longitude_wgs84']
    assert a.road_arrival_latitude == p['proposed_latitude_wgs84']
    assert a.selected_stop_id != p['nearest_listing_stop_not_selected']['stop_id']
    assert p['status'] == 'exact_arrival_point_validation_pending_no_route_requested'


def test_six_origin_rows_identical_to_existing_reference_not_catalogue_points():
    # The full parent includes composite lineage IDs; inference on six simple IDs
    # alone can turn the identical CSV text into integers. Compare serialized data.
    old = csv('reports/accessibility_road_stop_corrected_origins.csv', dtype=str, keep_default_na=False)
    new = csv(OUTPUTS['braunwald_urban_origins_stage90'], dtype=str, keep_default_na=False)
    assert set(new.municipality_bfs_id) == {'261', '351', '2701', '5192', '5586', '6621'}
    expected = old.set_index('municipality_bfs_id', drop=False).loc[new.municipality_bfs_id].reset_index(drop=True)
    pd.testing.assert_frame_equal(new, expected)


def test_twelve_cells_match_two_archived_directional_responses_exactly():
    m = js(COLLECTION)
    f = csv(TABLES['braunwald_urban_road_directional_stage90'])
    assert m['new_requests'] == 2 and len(m['successful_requests']) == 2 and not m['failures']
    assert m['endpoint'] == 'https://api.heigit.org/openrouteservice/v2/matrix/driving-car'
    assert len(f) == 12 and f.route_status.eq('route_available').all()
    for request in m['successful_requests']:
        assert sha(request['raw_file']) == request['raw_sha256']
        raw = js(request['raw_file'])
        assert request['http_status'] == 200
        assert set(request['safe_response_headers']) <= {'content-type', 'x-ratelimit-limit', 'x-ratelimit-remaining', 'x-ratelimit-reset', 'retry-after'}
        for i, bfs in enumerate(request['batch']['municipality_bfs_ids']):
            row = f[f.request_id.eq(request['request_id']) & f.municipality_bfs_id.eq(bfs)].iloc[0]
            x, y = (i, 0) if row.direction == 'outbound' else (0, i)
            assert row.model_duration_seconds == raw['durations'][x][y]
            assert row.model_distance_metres == raw['distances'][x][y]
            assert row.usable_duration_minutes == raw['durations'][x][y] / 60
            assert json.loads(row.resolved_origin_location) == raw['sources'][x]['location']
            assert json.loads(row.resolved_destination_location) == raw['destinations'][y]['location']
            assert row.origin_snap_distance_metres == raw['sources'][x]['snapped_distance']
            assert row.destination_snap_distance_metres == raw['destinations'][y]['snapped_distance']


def test_mean_minimum_and_no_upward_transfer_or_automatic_exclusion():
    f = csv(RESULTS['braunwald_urban_road_city_reference_stage90'])
    m = js(SUMMARY)
    assert len(f) == 6 and f.municipality_bfs_id.is_unique and f.both_directions_available.all()
    np.testing.assert_array_equal(f.road_reference_minutes, (f.outbound_minutes + f.return_minutes) / 2)
    assert f.onward_transfer_minutes.isna().all()
    assert not f.complete_city_to_piste_time.any() and not f.winter_route_verified.any()
    assert not f.automatic_exclusion.any()
    assert f.preparation_unit_id.eq('DESC_LISTING_PENDING__braunwald').all()
    assert m['complete_six_city_reference'] and m['closest_available_city_name'] == 'Zürich'
    assert m['minimum_six_city_reference_minutes'] == f.road_reference_minutes.min()
    assert m['prior_graph_exactly_same']


def test_snapping_fourteen_observations_independent_distance_without_walk_conversion():
    f = csv(RESULTS['braunwald_urban_road_snapping_stage90'])
    assert len(f) == 14
    assert not f.duplicated(['endpoint_role', 'endpoint_id', 'request_id', 'direction']).any()
    assert not f.missing_snap_distance.any() and not f.missing_resolved_coordinate.any()
    for r in f.itertuples():
        lon, lat = json.loads(r.resolved_location)
        distance = Geod(ellps='WGS84').inv(r.input_longitude, r.input_latitude, lon, lat)[2]
        assert r.geodesic_displacement_metres == distance
    a = f[f.endpoint_role.eq('station_stop')]
    assert len(a) == 2 and a.reported_snap_distance_metres.eq(22.93).all()


def test_six_csv_schemas_sources_and_serialized_missingness():
    d = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    s = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    for table, path in (OUTPUTS | TABLES | RESULTS).items():
        f = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
        part = d[d.table.eq(table)]
        assert part.variable.is_unique and set(part.variable) == set(f)
        for r in part.itertuples():
            assert r.source_id in set(s.source_id)
            assert abs(float(r.missing_share) - f[r.variable].eq('').mean()) <= .00000051
            assert r.causal_role.startswith('Descriptive urban access only') or r.causal_role == 'access measurement under construction, not canonical exposure'


def test_real_api_requests_logged_once_no_duplicate_or_fictitious_request():
    f = pd.read_csv(ROOT / 'logs/data_collection_log.csv', dtype=str, keep_default_na=False)
    part = f[f.source_id.eq(ROUTE_SOURCE)]
    assert len(part) == 2 and part.HTTP_status.eq('200').all() and part.rows_collected.eq('6').all()
    for r in js(COLLECTION)['successful_requests']:
        match = part[part.timestamp.eq(r['retrieval_date'])]
        assert len(match) == 1 and match.iloc[0].checksum == r['raw_sha256']


def test_frozen_contracts_and_all_three_hundred_historical_numeric_files():
    for p in [PREPARATION, COLLECTION, SUMMARY]:
        m = js(p)
        for path, checksum in (m['input_sha256'] | m['output_sha256']).items():
            assert sha(path) == checksum
    p = js(PREPARATION)['protected_old_numerical_sha256']
    assert len(p) == 300
    for path, checksum in p.items():
        assert sha(path) == checksum
    assert len(csv('data_processed/accessibility_station_groups_stage79.csv')) == 69
