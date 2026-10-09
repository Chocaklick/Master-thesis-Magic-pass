import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from src.data_collection.collect_current_piste_geometry import validate_response
import src.data_collection.collect_current_piste_geometry as collector
from src.descriptive.audit_terrain_snow_source_feasibility import build_inventory, geometry_inventory, CONFIG, OUTPUT, SUMMARY

ROOT = Path(__file__).resolve().parents[1]


def fixture_payload():
    return {'osm3s': {'timestamp_osm_base': '2026-10-09T00:00:00Z'}, 'elements': [
        {'type': 'way', 'id': 1, 'version': 2, 'timestamp': '2026-09-01', 'tags': {'piste:type': 'downhill'},
         'nodes': [1, 2], 'geometry': [{'lat': 46, 'lon': 7}, {'lat': 46.1, 'lon': 7.1}]},
        {'type': 'relation', 'id': 1, 'version': 1, 'timestamp': '2026-09-01', 'tags': {'site': 'piste'}}]}


def test_geometry_keys_types_and_limits_not_piste_or_group_counts():
    p = fixture_payload()
    assert validate_response(p) == 2  # Same numeric ID in different OSM namespaces is legitimate.
    counts = geometry_inventory(p)
    assert counts['downhill_way_count'] == 1 and counts['site_relation_count'] == 1
    assert counts['element_count_is_not_piste_count'] and counts['timestamp_is_edit_not_construction_date']


def test_partial_response_empty_duplicate_and_version_rejected():
    for change in ['remark', 'empty', 'duplicate', 'version']:
        p = fixture_payload()
        if change == 'remark':
            p['remark'] = 'runtime timeout'
        elif change == 'empty':
            p['elements'] = []
        elif change == 'duplicate':
            p['elements'].append(p['elements'][0])
        else:
            del p['elements'][0]['version']
        with pytest.raises(ValueError):
            validate_response(p)


def test_source_calendars_not_snow_values_and_unchanged_group_universe():
    frame = pd.read_csv(ROOT / OUTPUT, keep_default_na=False)
    groups = pd.read_csv(ROOT / 'data_processed/winter_profile_five_dimension_groups.csv')
    assert len(frame) == 71 and frame.station_group_id.is_unique
    assert set(frame.station_group_id) == set(groups.station_group_id)
    assert frame.requested_winter_count.eq(5).all()
    assert frame.spass_calendar_missing_winter_count.sum() == 23
    assert frame.spass_calendar_missing_winter_count.gt(0).sum() == 14
    assert frame.oshd_candidate_calendar_winter_count.value_counts().to_dict() == {5: 40, 2: 22, 3: 6, 4: 3}
    assert frame.overlap_calendar_winter_count.sum() == 251
    assert frame.recent_missing_spass_within_oshd_calendar_count.sum() == 23
    assert not frame.snow_feature_computed.any() and not frame.group_piste_assignment_verified.any()


def test_duplicate_calendars_not_averaged():
    groups = pd.read_csv(ROOT / 'data_processed/winter_profile_five_dimension_groups.csv')
    windows = pd.read_csv(ROOT / 'data_processed/winter_profile_approved_snow_windows.csv')
    config = json.loads((ROOT / CONFIG).read_text())
    with pytest.raises(ValueError, match='Duplicate'):
        build_inventory(groups, pd.concat([windows, windows.iloc[:1]]), {'records': []}, config, 'complete')


def test_saved_integrity_dictionary_sources_and_candidates():
    summary = json.loads((ROOT / SUMMARY).read_text())
    for path, value in {**summary['input_sha256'], **summary['output_sha256'], **summary['protected_legacy_sha256']}.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == value, path
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv')
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv')
    assert not sources.source_id.duplicated().any()
    assert not dictionary.duplicated(['table', 'variable']).any()
    assert set(dictionary[dictionary.table.eq(Path(OUTPUT).stem)].variable) == set(pd.read_csv(ROOT / OUTPUT).columns)
    parents = set('|'.join(pd.read_csv(ROOT / OUTPUT).parent_source_ids).split('|'))
    assert parents <= set(sources.source_id)
    config = json.loads((ROOT / CONFIG).read_text())
    assert not config['snow_candidate_selected_as_reference']
    assert not config['snow_cross_product_splicing_or_calibration_approved']


@pytest.mark.parametrize('status', ['complete', 'failed'])
def test_collector_resume_has_no_request_or_source_rewrite(tmp_path, monkeypatch, capsys, status):
    config_file = tmp_path / collector.CONFIG
    config_file.parent.mkdir(parents=True)
    config_file.write_text('{}', encoding='utf-8')
    checkpoint_file = tmp_path / collector.CHECKPOINT
    checkpoint_file.parent.mkdir(parents=True)
    prior = dict(status=status, config_sha256=hashlib.sha256(config_file.read_bytes()).hexdigest())
    if status == 'complete':
        raw = tmp_path / 'original.json'
        raw.write_text(json.dumps(fixture_payload()), encoding='utf-8')
        prior.update(raw_file='original.json', sha256=hashlib.sha256(raw.read_bytes()).hexdigest())
    checkpoint_file.write_text(json.dumps(prior), encoding='utf-8')
    before = checkpoint_file.read_bytes()
    monkeypatch.setattr(collector, 'ROOT', tmp_path)
    monkeypatch.setattr(collector.sys, 'argv', ['collector'])
    def refuse_network(*args, **kwargs):
        raise AssertionError('Resume must not request external data')
    monkeypatch.setattr(collector, 'urlopen', refuse_network)
    collector.main()
    assert checkpoint_file.read_bytes() == before
    assert 'no new request' in capsys.readouterr().out
