"""Documented activity != current operation != approved geometry/road arrivals."""
import json
from pathlib import Path
import pandas as pd
from src.descriptive.prepare_national_documentary_queue_stage88 import ROOT, OUTPUT, CASES
from src.descriptive.check_national_preparation_stage87 import sha


def test_all200_candidates35cached_hints_six_documentary_starters_no_exclusion():
    f = pd.read_csv(ROOT / OUTPUT)
    inv = pd.read_csv(ROOT / 'data_processed/national_similarity_inventory_stage86.csv')
    expected = inv[inv.within_swiss_preparation_scope & inv.identity_level.ne('existing_approved_group')].component_resort_ids
    assert len(f) == 200 and f.resort_id.is_unique and set(f.resort_id) == set(expected)
    assert f.cached_site_hint_count.gt(0).sum() == 35
    assert set(f.loc[f.archived_documentary_source_count.gt(0), 'resort_id']) == set(CASES)
    assert f.archived_documentary_source_count.sum() == 8
    assert not f.accepted_independent_domain_assignment.any()
    assert not f.new_physical_profile_computed.any() and not f.automatic_clustering_exclusion.any()


def test_closure_does_not_exclude_historical_activity_or_infer_other_false_statuses():
    f = pd.read_csv(ROOT / OUTPUT, dtype=str, keep_default_na=False).set_index('resort_id')
    b = f.loc['braunwald']
    assert b.explicit_operator_ski_cessation_observed == 'True'
    assert b.common_decade_activity_review_status == 'primary_activity_verified_2019_20_population_eligible_geometry_pending'
    assert f.drop('braunwald').explicit_operator_ski_cessation_observed.eq('UNKNOWN').all()
    period = json.loads((ROOT / 'config/national_activity_period_decision_stage88.json').read_text())
    cross = json.loads((ROOT / 'config/national_transboundary_scope_decision_stage88.json').read_text())
    urban = json.loads((ROOT / 'config/national_urban_reference_decision_stage89.json').read_text())
    assert period['status'] == 'researcher_validated' and period['unknown_activity_kept_pending_not_automatically_excluded']
    assert cross['status'].startswith('researcher_validated') and cross['new_domains_not_merged_or_cut_by_this_file']
    assert urban['status'] == 'researcher_validated' and urban['no_ARE_OR_catalogue_point_substitution']


def test_all_actual_outcomes_logged_once_and_archived_sources_checksum_verified():
    events = json.loads((ROOT / 'data_interim/national_preparation_stage88/evidence_events.json').read_text())
    log = pd.read_csv(ROOT / 'logs/data_collection_log.csv', dtype=str, keep_default_na=False)
    assert len(events) == 17 and sum(e['status'] == 'downloaded' for e in events) == 8
    local = [e for e in events if 'WinError 10013' in e.get('error', '')]
    assert len(local) == 8
    refused = [e for e in events if e['status'] == 'failed' and 'WinError 10013' not in e.get('error', '')]
    assert len(refused) == 1 and str(refused[0]['HTTP_status']) == '403'
    for e in events:
        assert len(log[log.timestamp.eq(e['timestamp']) & log.source_id.eq(e['source_id'])]) == 1
        if e['status'] == 'downloaded':
            assert sha(e['raw_file']) == e['checksum']
            if e['source_id'] == 'NATIONAL_BRAUNWALD_REPORT_2019_20_STAGE88':
                with (ROOT / e['raw_file']).open('rb') as stream:
                    assert stream.read(5) == b'%PDF-'


def test_queue_schema_literal_sources_and_serialized_missingness_registered():
    f = pd.read_csv(ROOT / OUTPUT, dtype=str, keep_default_na=False)
    d = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    s = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    part = d[d.table.eq(Path(OUTPUT).stem)]
    assert part.variable.is_unique and set(part.variable) == set(f)
    for r in part.itertuples():
        assert r.source_id in set(s.source_id)
        assert abs(float(r.missing_share) - f[r.variable].eq('').mean()) <= .00000051
    for ids in f.documentary_source_ids:
        assert set(ids.split('|')) - {''} <= set(s.source_id)
    row = s.set_index('source_id').loc['NATIONAL_BRAUNWALD_FUTURE_NOTICE_STAGE88']
    assert row.local_raw_file == '' and '403' in row.quality_notes


def test_braunwald_valley_proposal_is_source_stop_not_nearest_chairlift_or_used_route():
    p = json.loads((ROOT / 'reports/braunwald_road_arrival_proposal_stage89.json').read_text())
    assert p['status'] == 'exact_arrival_point_validation_pending_no_route_requested'
    assert p['proposed_stop_id'] == '8503260' and p['proposed_stop_name'] == 'Linthal Braunwaldbahn (Talst.)'
    assert p['bav_easting_2056'] == 2719079 and p['bav_northing_2056'] == 1198680
    assert p['nearest_listing_stop_not_selected']['stop_id'] == '8530956'
    assert p['proposed_measure_not_complete_city_to_piste_travel_time']
    assert p['no_new_ORS_call_domain_exclusion_or_old_endpoint_overwrite']
    assert p['coordinate_state_date'] == '2026-09-20'
    for path, checksum in p['input_sha256'].items():
        assert sha(path) == checksum


def test_completed_additive_audit_retains_parent_and_qualifies_unfinished_work():
    m = json.loads((ROOT / 'reports/preservation_national_stage89_summary.json').read_text())
    assert m['historical_unique_files'] == 3127 and m['checked_unique_files'] > 3127
    assert m['all_old_sources_preentry_profiles_caches_exposures_and_DiD_unchanged']
    assert m['no_new_domain_group_merge_ORS_route_prediction_causal_fit_or_clustering']
    assert m['registry_prefixes_exact']['metadata/data_sources_master.csv']['current_rows'] == 1648
    assert m['registry_prefixes_exact']['metadata/data_dictionary.csv']['current_rows'] == 9113
    assert m['registry_prefixes_exact']['logs/data_collection_log.csv']['current_rows'] == 2488
