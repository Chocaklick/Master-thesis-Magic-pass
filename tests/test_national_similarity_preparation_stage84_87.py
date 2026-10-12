"""Independent fixed calendar and national-unit checks, without fitting classes."""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.data_processing.build_common_snow_profiles_stage84 import ROOT, OUTPUTS as SNOW
from src.descriptive.consolidate_national_preparation_stage86 import OUTPUTS as NATIONAL, RID, GID, numeric
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def read(path):
    return pd.read_csv(ROOT / path, float_precision='round_trip', low_memory=False)


def test_fixed_common_decade_all69groups_and_690winter_rows():
    w, p = read(SNOW[0]), read(SNOW[1])
    old = read('data_processed/spass_reviewed_profiles_stage83.csv')
    assert len(w) == 690 and len(p) == 69 and p.station_group_id.is_unique
    assert set(p.station_group_id) == set(old.station_group_id)
    assert not w.duplicated(['station_group_id', 'winter_start_year']).any()
    assert w.groupby('station_group_id').winter_start_year.apply(list).apply(lambda x: x == list(range(2013, 2023))).all()
    assert p.expected_total_days.eq(1512).all()
    assert p.common_period_start_date.eq('2013-12-01').all() and p.common_period_end_date.eq('2023-04-30').all()
    for r in w.itertuples():
        assert r.winter_start_date == f'{r.winter_start_year}-12-01'
        assert r.winter_end_date == f'{r.winter_start_year + 1}-04-30'
        assert r.expected_days == (152 if r.winter_start_year in [2015, 2019] else 151)
    assert p.membership_independent_window.all() and p.not_preentry_feature.all()


def test_all13_previous_incomplete_groups_recovered_not_removed():
    p, a = read(SNOW[1]), read(SNOW[2])
    old = read('data_processed/spass_reviewed_profiles_stage83.csv')
    assert len(a) == 13 and a.station_group_id.is_unique
    assert set(a.station_group_id) == set(old.loc[old.status.eq('incomplete_five_winters'), 'station_group_id'])
    assert a.previous_observed_winter_count.isin([3, 4]).all()
    assert a.common_observed_winter_count.eq(10).all() and a.common_period_snow_mean_available.all()
    assert p.status.value_counts().to_dict() == {
        'common_ten_winters_full_coverage': 64, 'common_ten_winters_partial_coverage': 3, 'missing_geometry': 2}
    assert p.common_ten_winter_mean_m.notna().sum() == 67
    assert not p.source_spliced_or_calibrated.any() and p.spass_metres_assumed.all() and p.spass_original_unit.eq('UNKNOWN').all()


def test_spatial_partial_coverages_explicit_not_zero_or_full():
    p = read(SNOW[1]).set_index('station_group_id')
    expected = {'MP_GROUP_RESORT__la_dole_jura_sur_leman': .6582480699726491,
                'MP_GROUP_RESORT__melchsee_frutt': .863519071185632,
                'MP_GROUP_RESORT__vallee_de_joux': .942674513583907}
    assert set(p[p.status.eq('common_ten_winters_partial_coverage')].index) == set(expected)
    for gid, share in expected.items():
        assert p.loc[gid, 'min_observed_length_share'] == pytest.approx(share)
        assert p.loc[gid, 'all_requested_days_observed'] and not p.loc[gid, 'all_axis_length_observed']
    absent = p[p.status.eq('missing_geometry')]
    assert absent.observed_winter_count.eq(0).all() and absent.common_ten_winter_mean_m.isna().all()
    assert absent.min_observed_length_share.isna().all()


def test_equal_weight_to_ten_winter_means_no_missing_fallback():
    w, p = read(SNOW[0]), read(SNOW[1])
    for r in p.itertuples():
        part = w[w.station_group_id.eq(r.station_group_id)]
        v = part.spass_winter_mean_m.to_numpy()
        assert r.observed_winter_count == np.isfinite(v).sum()
        if np.isfinite(v).all():
            assert r.common_ten_winter_mean_m == math.fsum(v) / 10
        else:
            assert pd.isna(r.common_ten_winter_mean_m)


def test_670_observed_winter_means_rebuilt_from_101304_daily_rows():
    summary = json.loads((ROOT / 'reports/common_snow_profiles_stage84_summary.json').read_text())
    w = read(SNOW[0]).set_index(['station_group_id', 'winter_start_year'])
    rebuilt = rows = 0
    assert set(summary['daily_checkpoints']) == {str(y) for y in range(2013, 2023)}
    for year, checkpoint in summary['daily_checkpoints'].items():
        f = read(checkpoint['path'])
        assert not f.duplicated(['station_group_id', 'civil_date']).any()
        assert sha(checkpoint['path']) == checkpoint['sha256']
        assert sha(checkpoint['metadata']) == checkpoint['metadata_sha256']
        for gid, daily in f.groupby('station_group_id'):
            r = w.loc[(gid, int(year))]
            assert len(daily) == r.expected_days == r.observed_days and r.missing_days == 0
            observed = daily.spass_daily_mean_m.dropna()
            assert r.spass_winter_mean_m == math.fsum(observed) / len(observed)
            rebuilt += 1
        rows += len(f)
    assert rebuilt == 670 and rows == 101304


def test_archived_stage85_inventory_is_preparation_not_domains_or_nonmembership():
    f = read('data_processed/national_similarity_inventory_stage85.csv')
    l = read('data_processed/national_similarity_listing_lineage_stage85.csv')
    sites = read('data_processed/national_similarity_piste_site_inventory_stage85.csv')
    assert len(f) == 273 and f.within_swiss_preparation_scope.sum() == 270
    assert f.identity_level.eq('existing_approved_group').sum() == 69
    assert len(l) == 271 and l.resort_id.is_unique
    assert len(sites) == 238 and not sites.new_national_assignment_accepted.any()
    candidates = f[f.identity_level.ne('existing_approved_group') & f.within_swiss_preparation_scope]
    assert len(candidates) == 201 and not candidates.unit_scope_verified.any()
    assert candidates.membership_verification_status.value_counts().to_dict() == {
        'absence_of_resolved_link_is_not_verified_nonmembership': 193, 'current_catalogue_candidate_scope_pending': 8}
    assert candidates.pending_connection_review.sum() == 120
    assert candidates.possible_existing_group_ids_legacy_cluster_hint.notna().sum() == 14


def test_alias_is_previously_measured_scope_not_new_group_or_exposure():
    f, l = read(NATIONAL[0]), read(NATIONAL[1])
    original = read('data_processed/national_similarity_listing_lineage_stage85.csv').set_index('resort_id')
    assert len(f) == 272 and f.within_swiss_preparation_scope.sum() == 269
    assert f.identity_level.eq('existing_approved_group').sum() == 69
    assert not f.preparation_unit_id.eq('DESC_LISTING_PENDING__' + RID).any()
    assert len(l) == 271 and set(l.resort_id) == set(original.index)
    changed = l.set_index('resort_id').preparation_unit_id.ne(original.preparation_unit_id)
    assert changed[changed].index.tolist() == [RID]
    r = l.set_index('resort_id').loc[RID]
    assert r.preparation_unit_id == GID and r.listing_link_status == 'documented_alias_inside_previously_retained_perimeter'
    assert RID in f.set_index('preparation_unit_id').loc[GID, 'component_resort_ids'].split('|')
    candidates = f[f.identity_level.ne('existing_approved_group') & f.within_swiss_preparation_scope]
    assert len(candidates) == 200 and candidates.pending_connection_review.sum() == 119
    assert candidates.possible_existing_group_ids_legacy_cluster_hint.notna().sum() == 13
    assert candidates.membership_verification_status.value_counts().to_dict() == {
        'absence_of_resolved_link_is_not_verified_nonmembership': 192, 'current_catalogue_candidate_scope_pending': 8}


def test_literal_original_listing_features_not_summed_or_substituted():
    l = read(NATIONAL[1]).set_index('resort_id')
    master = pd.read_csv(ROOT / 'data_processed/resort_master.csv', dtype=str, keep_default_na=False).set_index('resort_id')
    mapping = {'listing_top_altitude_source_m': 'altitude_top_m', 'listing_piste_length_source_km': 'ski_area_km',
               'listing_lift_count_source': 'number_lifts'}
    for c, raw in mapping.items():
        expected = master.loc[l.index, raw].apply(numeric)
        np.testing.assert_equal(l[c].to_numpy(), expected.to_numpy())
    assert l.not_automatically_approved_clustering_feature.all()
    assert pd.isna(l.loc[RID, 'listing_piste_length_source_km'])
    assert not read(NATIONAL[0]).set_index('preparation_unit_id').loc[GID, 'provided_structural_context_available']
    assert l.original_feature_observation_date.eq('UNKNOWN').all()


def test_existing_lift_cluster_lineage_unchanged_not_domain_assignment():
    l = read(NATIONAL[1]).set_index('resort_id')
    master = read('data_processed/resort_master.csv').set_index('resort_id')
    pd.testing.assert_series_equal(l.original_cluster_id, master.loc[l.index, 'cluster_id'], check_names=False)
    assert l.original_cluster_id.nunique() == 162
    grouped_ids = read('data_processed/accessibility_station_groups_stage79.csv').station_group_id
    assert set(read(NATIONAL[0]).query("identity_level == 'existing_approved_group'").preparation_unit_id) == set(grouped_ids)


def test_comparable_field_layer_leaves_new_domains_missing_no_ARE_ORSimputation():
    f = read(NATIONAL[2]).set_index('preparation_unit_id')
    terrain = read('data_processed/terrain_reviewed_profiles_stage82.csv').set_index('station_group_id')
    snow = read(SNOW[1]).set_index('station_group_id')
    assert f.comparable_six_fields_available.sum() == 67 and not f.automatic_clustering_inclusion.any()
    unreviewed = f[f.identity_level.ne('existing_approved_group')]
    fields = ['measured_unique_piste_axes_m', 'length_weighted_piste_altitude_m', 'terrain_northness', 'terrain_eastness',
              'common_ten_winter_mean_m', 'minimum_six_city_road_minutes']
    assert unreviewed[fields].isna().all().all() and unreviewed.road_city_count_observed.eq(0).all()
    np.testing.assert_equal(f.loc[terrain.index, 'length_weighted_piste_altitude_m'].to_numpy(), terrain.length_weighted_observed_altitude_m.to_numpy())
    np.testing.assert_equal(f.loc[snow.index, 'common_ten_winter_mean_m'].to_numpy(), snow.common_ten_winter_mean_m.to_numpy())
    road = read('data_processed/accessibility_road_group_reference_stage79.csv')
    cities = read('data_processed/winter_profile_urban_city_detail_stage57.csv').municipality_bfs_id.unique()
    expected = road[road.municipality_bfs_id.isin(cities)].groupby('station_group_id').road_reference_minutes.min()
    np.testing.assert_equal(f.loc[expected.index, 'minimum_six_city_road_minutes'].to_numpy(), expected.to_numpy())
    assert f.loc[terrain.index, 'road_city_count_observed'].eq(6).all()


def test_frozen_producers_config_and_data_hashes_not_rewritten():
    for p in ['reports/common_snow_profiles_stage84_summary.json',
              'reports/national_similarity_inventory_stage85_summary.json', 'reports/national_similarity_context_stage86_summary.json']:
        m = json.loads((ROOT / p).read_text())
        for path, expected in (m['input_sha256'] | m['output_sha256']).items():
            if path.endswith('.nc'):  # 8GB original checked once by separate streaming preservation audit.
                continue
            assert sha(path) == expected
    config = json.loads((ROOT / 'config/descriptive_similarity_scope_stage84.json').read_text())
    assert config['old_54_vs_67_clustering_scope_question'].startswith('superseded')
    assert config['clustering_features_transforms_and_algorithms'].startswith('not_yet_validated')
    assert config['no_membership_or_hotel_outcome_used_as_clustering_feature']


def test_nine_new_csv_schemas_sources_and_serialized_missingness_registered():
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    paths = [*SNOW, 'data_processed/national_similarity_inventory_stage85.csv',
             'data_processed/national_similarity_listing_lineage_stage85.csv',
             'data_processed/national_similarity_piste_site_inventory_stage85.csv', *NATIONAL]
    for path in paths:
        f = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
        part = dictionary[dictionary.table.eq(Path(path).stem)]
        assert part.variable.is_unique and set(part.variable) == set(f)
        assert set(part.source_id) <= set(sources.source_id)
        for r in part.itertuples():
            assert abs(float(r.missing_share) - f[r.variable].eq('').mean()) <= .00000051


def test_completed_preservation_retains_old_sources_panels_and_registry_prefixes():
    m = json.loads((ROOT / 'reports/preservation_national_stage87_summary.json').read_text())
    assert m['historical_unique_files'] == 3087 and m['checked_unique_files'] > 3087
    assert m['original_sources_old_preentry_results_caches_and_exposures_unchanged']
    assert m['no_prediction_causal_fit_clustering_or_automatic_sample_filter']
    prefixes = m['registry_prefixes_exact']
    assert prefixes['metadata/data_sources_master.csv']['previous_rows_exact'] == 1634
    assert prefixes['metadata/data_sources_master.csv']['appended_rows'] == 3
    assert prefixes['metadata/data_dictionary.csv']['previous_rows_exact'] == 8924
    assert prefixes['logs/data_collection_log.csv']['appended_rows'] == 0
