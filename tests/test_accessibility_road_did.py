"""Regression checks for scoped endpoint correction and approved road design."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from src.causal_inference.estimate_accessibility_road_did import group_reference, build_exposure, comparison_universe
from src.data_collection.collect_accessibility_road_lauterbrunnen import sha, BASE, PREP, DELTA_SUMMARY, SUMMARY

ROOT = Path(__file__).resolve().parents[1]


def test_approved_thresholds_and_exact_lauterbrunnen_override():
    c = json.loads((ROOT/'config/accessibility_road_did_execution.json').read_text(encoding='utf-8'))
    assert c['principal_threshold_minutes'] == 30
    assert c['sensitivity_thresholds_minutes'] == [15, 45]
    assert c['communal_stop_override']['new_selected_stop_id'] == '8507384'
    old = pd.read_csv(ROOT/BASE[0], dtype={'selected_stop_id': str})
    new = pd.read_csv(ROOT/'reports/accessibility_road_stop_corrected_origins.csv', dtype={'selected_stop_id': str})
    pd.testing.assert_frame_equal(old[old.municipality_bfs_id.ne(584)].reset_index(drop=True), new[new.municipality_bfs_id.ne(584)].reset_index(drop=True))
    row = new[new.municipality_bfs_id.eq(584)].iloc[0]
    assert row.selected_stop_id == '8507384' and row.selected_stop_name == 'Lauterbrunnen'
    assert '8507378' in row.legacy_tp_origin_records


def test_six_delta_requests_no_other_commune_rerouted():
    m = json.loads((ROOT/DELTA_SUMMARY).read_text(encoding='utf-8'))
    assert m['actual_directional_cells_returned'] == 150
    assert len(m['successful_requests']) == 6
    for request in m['successful_requests']:
        assert request['batch']['municipality_bfs_ids'] == [584]
        assert sha(request['raw_file']) == request['raw_sha256']
    assert m['pairs_with_both_directions'] == 75


def test_corrected_matrix_preserves_other_rows_and_old_results():
    for kind in ['directional', 'pairs']:
        old = pd.read_csv(ROOT/f'data_processed/accessibility_road_stop_{kind}.csv')
        new = pd.read_csv(ROOT/f'data_processed/accessibility_road_stop_corrected_{kind}.csv')
        keys = ['municipality_bfs_id','access_point_id']+(['direction'] if kind == 'directional' else [])
        assert len(old) == len(new) and not new.duplicated(keys).any()
        unchanged = lambda frame: frame[frame.municipality_bfs_id.ne(584)].sort_values(keys).reset_index(drop=True)
        pd.testing.assert_frame_equal(unchanged(old), unchanged(new))
    m = json.loads((ROOT/PREP).read_text(encoding='utf-8'))
    assert all(sha(p) == value for p,value in m['protected_legacy_sha256'].items())
    corrected = json.loads((ROOT/SUMMARY).read_text(encoding='utf-8'))
    assert corrected['usable_pairs'] == 13874
    p = pd.read_csv(ROOT/'data_processed/accessibility_road_stop_corrected_pairs.csv')
    np.testing.assert_allclose(p.road_reference_minutes, (p.outbound_minutes+p.return_minutes)/2, equal_nan=True)
    missing = p[p.road_reference_minutes.isna()]
    assert list(missing.municipality_bfs_id) == [6290]


def test_group_minimum_uses_one_real_access_mean_and_stable_tie():
    p = pd.DataFrame(dict(municipality_bfs_id=[1,1,1],station_group_id=['G','G','G'],access_point_id=['Z','B','A'],road_reference_minutes=[np.nan,12.,12.]))
    g = pd.DataFrame(dict(station_group_id=['G'],station_group_name=['Group'],first_effective_month=['2019-05-01']))
    r = group_reference(p,g)
    assert len(r) == 1 and r.iloc[0].access_point_id == 'A'
    assert r.iloc[0].road_reference_minutes == 12 and r.iloc[0].unusable_access_count == 1


def test_unknown_saas_fee_entry_cannot_be_used_as_never_or_later_exposed():
    p = pd.read_csv(ROOT/'data_processed/accessibility_road_stop_corrected_pairs.csv')
    g = pd.read_csv(ROOT/'data_processed/accessibility_station_groups.csv')
    h = pd.read_csv(ROOT/'data_processed/magic_pass_membership_history.csv')
    u = pd.read_csv(ROOT/'data_processed/accessibility_municipality_month_exposure_territorial.csv',low_memory=False)
    monthly, inventory = build_exposure(group_reference(p,g),u,h,[15,30,45])
    assert len(inventory) == 3*185 and len(monthly) == 3*len(u)
    saas = inventory[inventory.municipality_bfs_id.eq(6290)]
    assert saas.exposure_assignment_status.eq('indeterminate_access_or_earlier_entry').all()
    assert saas.earliest_unknown_group_entry_month.eq(pd.Timestamp('2019-05-01')).all()
    with pytest.raises(ValueError,match='requires researcher validation'):
        comparison_universe(inventory,pd.Timestamp('2026-03-01'))
    laut = inventory[inventory.municipality_bfs_id.eq(584)].set_index('threshold_minutes')
    assert pd.isna(laut.loc[15,'first_exposure_month'])
    assert laut.loc[30,'first_exposure_month'] == pd.Timestamp('2022-05-01')
    assert laut.loc[45,'first_exposure_month'] == pd.Timestamp('2022-05-01')


def test_parking_candidate_probe_is_not_an_endpoint_approval():
    c = json.loads((ROOT/'config/accessibility_saas_fee_road_endpoint_proposal.json').read_text(encoding='utf-8'))
    assert c['endpoint_approved'] is False and c['analytical_endpoints_changed'] is False
    p = pd.read_csv(ROOT/'reports/saas_fee_road_candidate_probe.csv',dtype={'origin_stop_id':str,'destination_stop_id':str})
    assert len(p) == 9
    local = p[p.origin_stop_id.eq('8501782') & p.destination_stop_id.eq('8511180')].iloc[0]
    assert local.model_duration_seconds == pytest.approx(94.14)
    assert local.destination_snap_distance_metres == pytest.approx(62.29)
    current = pd.read_csv(ROOT/'reports/accessibility_road_stop_arrivals.csv',dtype={'selected_stop_id':str})
    assert current[current.access_point_id.eq('ACCESS_MAGIC_CURRENT__600')].iloc[0].selected_stop_id == '8594574'
