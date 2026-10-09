import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.data_collection.collect_oshd_profile_audit import parse_record, validate_download_response, single_collector_lock, official_download_anchor, reconcile_checkpoint_counts

ROOT = Path(__file__).resolve().parents[1]


def record_html(rights='cc-by-4.0', public='public', linked=True):
    data = dict(id='17313889', access=dict(files=public), metadata=dict(rights=[dict(id=rights)]),
        files=dict(entries={'OSHD_DATA_WY2024.zip': dict(key='OSHD_DATA_WY2024.zip', size=50, checksum='md5:abc')}))
    link = '<link rel="item" href="https://zenodo.org/records/17313889/files/OSHD_DATA_WY2024.zip">' if linked else ''
    return "<div data-record='" + json.dumps(data) + "'></div>" + link


def test_public_html_explicit_license_links_and_archive_size():
    record, files = parse_record(record_html(), [2024])
    assert record['id'] == '17313889'
    assert files[0]['expected_bytes'] == 50 and files[0]['expected_md5'] == 'abc'
    assert '/api/' not in files[0]['url']


def test_deadline_checkpoint_total_counts_completed_not_partial_archives():
    state=dict(complete_file_count=0, files=[dict(status='complete'),dict(status='paused'),dict(status='failed')])
    reconcile_checkpoint_counts(state)
    assert state['complete_file_count']==1
    assert [f['status'] for f in state['files']]==['complete','paused','failed']


def test_download_anchor_must_be_present_in_public_html():
    url = 'https://zenodo.org/records/17313889/files/OSHD_DATA_WY2024.zip'
    text = record_html() + '<a href="/records/17313889/files/OSHD_DATA_WY2024.zip?download=1">Download</a>'
    assert official_download_anchor(text, url) == url + '?download=1'
    with pytest.raises(ValueError):
        official_download_anchor(record_html(), url)


@pytest.mark.parametrize('kwargs', [dict(rights='copyright'), dict(public='restricted'), dict(linked=False)])
def test_uncertified_license_access_or_unlinked_download_rejected(kwargs):
    with pytest.raises(ValueError):
        parse_record(record_html(**kwargs), [2024])


def test_resume_requires_exact_partial_range_and_initial_size():
    validate_download_response(SimpleNamespace(status=200, headers={'Content-Length': '100'}), 0, 100)
    validate_download_response(SimpleNamespace(status=206, headers={'Content-Range': 'bytes 50-99/100', 'Content-Length': '50'}), 50, 100)
    for status, headers, start in [(200, {'Content-Length': '100'}, 50),
        (206, {'Content-Range': 'bytes 0-49/100'}, 50), (200, {'Content-Length': '5'}, 0)]:
        with pytest.raises(ValueError):
            validate_download_response(SimpleNamespace(status=status, headers=headers), start, 100)


def test_bounded_range_requires_exact_response_even_for_first_chunk():
    validate_download_response(SimpleNamespace(status=206, headers={'Content-Range': 'bytes 0-9/100', 'Content-Length': '10'}), 0, 100, 9)
    validate_download_response(SimpleNamespace(status=206, headers={'Content-Range': 'bytes 50-59/100', 'Content-Length': '10'}), 50, 100, 59)
    with pytest.raises(ValueError):
        validate_download_response(SimpleNamespace(status=200, headers={'Content-Length': '100'}), 0, 100, 9)


def test_approved_rules_and_no_silent_splicing_or_exclusion():
    config = json.loads((ROOT / 'config/winter_profile_aggregation_decisions_stage45.json').read_text())
    assert config['oshd_candidate_audit_and_useful_collection_approved']
    assert config['unique_verified_piste_length_weighting_approved']
    assert config['terrain_not_travel_bearing_aspect_approved']
    assert config['snow_daily_observed_mean_per_winter_then_equal_five_winter_mean_approved']
    assert config['fully_absent_winter_leaves_five_winter_mean_missing']
    assert not config['snow_splicing_or_calibration_approved']
    assert not config['automatic_coverage_threshold_or_exclusion_approved']


def test_concurrent_collectors_refused_and_lock_released(tmp_path):
    with single_collector_lock(tmp_path):
        with pytest.raises((RuntimeError, BlockingIOError)):
            with single_collector_lock(tmp_path):
                raise AssertionError('Second collector obtained lock')
    with single_collector_lock(tmp_path):
        pass
