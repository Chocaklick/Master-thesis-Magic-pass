"""Approved arrival correction, exact reuse, and threshold-specific DiD outputs."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from src.data_processing.prepare_accessibility_road_reference import sha

ROOT=Path(__file__).resolve().parents[1]


def test_only_approved_saasfee_arrival_changed():
    old=pd.read_csv(ROOT/'reports/accessibility_road_stop_arrivals.csv',dtype={'selected_stop_id':str})
    new=pd.read_csv(ROOT/'reports/accessibility_road_final_arrivals.csv',dtype={'selected_stop_id':str})
    access='ACCESS_MAGIC_CURRENT__600'
    pd.testing.assert_frame_equal(old[old.access_point_id.ne(access)].reset_index(drop=True),new[new.access_point_id.ne(access)].reset_index(drop=True))
    row=new[new.access_point_id.eq(access)].iloc[0]
    assert row.selected_stop_id=='8511180' and row.selected_stop_name=='Saas-Fee, Parkplatz Nord'
    origins=pd.read_csv(ROOT/'reports/accessibility_road_stop_corrected_origins.csv',dtype={'selected_stop_id':str})
    assert origins[origins.municipality_bfs_id.eq(6290)].iloc[0].selected_stop_id=='8501782'
    assert origins[origins.municipality_bfs_id.eq(584)].iloc[0].selected_stop_id=='8507384'


def test_final_reference_and_exact_local_probe_reuse():
    m=json.loads((ROOT/'reports/accessibility_road_final_collection_summary.json').read_text(encoding='utf-8'))
    assert m['usable_pairs']==13875 and m['exact_probe_cells_reused']==2
    for p,value in {**m['input_sha256'],**m['output_sha256'],**m['protected_legacy_sha256']}.items():
        assert sha(p)==value
    old=pd.read_csv(ROOT/'data_processed/accessibility_road_stop_corrected_directional.csv')
    new=pd.read_csv(ROOT/'data_processed/accessibility_road_final_directional.csv')
    keys=['municipality_bfs_id','access_point_id','direction']
    keep=lambda f:f[f.access_point_id.ne('ACCESS_MAGIC_CURRENT__600')].sort_values(keys).reset_index(drop=True)
    pd.testing.assert_frame_equal(keep(old),keep(new))
    local=new[new.municipality_bfs_id.eq(6290)&new.access_point_id.eq('ACCESS_MAGIC_CURRENT__600')]
    probe=json.loads((ROOT/'reports/saas_fee_road_candidate_probe_summary.json').read_text(encoding='utf-8'))
    assert len(local)==2 and local.request_id.eq(probe['request_id']).all()
    np.testing.assert_allclose(local.model_duration_seconds,[94.14,94.14])
    p=pd.read_csv(ROOT/'data_processed/accessibility_road_final_pairs.csv')
    assert p.road_reference_minutes.notna().all()
    np.testing.assert_allclose(p.road_reference_minutes,(p.outbound_minutes+p.return_minutes)/2)


def test_road_did_preserves_all_territories_and_rebuilds_saasfee_timing():
    inventory=pd.read_csv(ROOT/'reports/accessibility_road_did_inventory.csv',parse_dates=['first_exposure_month'])
    assert len(inventory)==185*3
    assert set(inventory.threshold_minutes)=={15,30,45}
    assert not inventory.exposure_assignment_status.eq('indeterminate_access_or_earlier_entry').any()
    saas=inventory[inventory.municipality_bfs_id.eq(6290)]
    assert saas.first_exposure_month.eq(pd.Timestamp('2019-05-01')).all()
    universe=pd.read_csv(ROOT/'reports/accessibility_road_did_comparison_universe.csv')
    assert not (universe.treated_in_focal_cohort & universe.primary_donor_candidate_at_anchor).any()
    assert universe.groupby(['threshold_minutes','focal_cohort_month']).municipality_bfs_id.nunique().eq(185).all()
    roles=universe[universe.municipality_bfs_id.eq(6290)&universe.focal_cohort_month.eq('2019-05-01')]
    assert len(roles)==3 and roles.treated_in_focal_cohort.all()


def test_three_estimation_manifests_and_normalized_reference():
    m=json.loads((ROOT/'reports/accessibility_road_did_summary.json').read_text(encoding='utf-8'))
    assert m['principal_threshold_minutes']==30 and m['sensitivity_thresholds_minutes']==[15,45]
    assert m['bootstrap_repetitions']==4999 and m['bootstrap_seed']==20261005
    assert m['causal_certification'] is False and m['canonical_tp_exposure_changed'] is False
    for p,value in {**m['input_sha256'],**m['output_sha256'],**m['protected_legacy_sha256']}.items():
        assert sha(p)==value
    for threshold in [15,30,45]:
        d=pd.read_csv(ROOT/f'reports/accessibility_road_did_{threshold}min_dynamic.csv')
        assert set(d.threshold_minutes)=={threshold}
        ref=d[d.event_month.eq(-1)&d.estimate_log_points.notna()]
        assert len(ref)>0
        np.testing.assert_allclose(ref.estimate_log_points,0,atol=1e-12)
        s=pd.read_csv(ROOT/f'reports/accessibility_road_did_{threshold}min_territory_support.csv')
        assert len(s)==m['thresholds'][str(threshold)]['exposed_territories']
        assert int(s.calculable.sum())==m['thresholds'][str(threshold)]['calculable_exposed_territories']
