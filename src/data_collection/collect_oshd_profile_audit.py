"""Approved OSHD first batch; source terms/links from archived public HTML.

Respect robots.txt, never request the prohibited record API. Immutable ZIPs
are promoted only after provider MD5 and exact size validation. Interrupted
parts stay in interim, and a failed request is not automatically repeated.
No snow extraction, source splicing, piste assignment or effect estimation.
"""
import argparse
import hashlib
import json
import re
import sys
import time
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_evidence import append_log
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

CONFIG = 'config/winter_profile_aggregation_decisions_stage45.json'
MANIFEST = 'reports/oshd_profile_audit_collection_summary.json'
AGENT = 'ThesisSkiResearch/0.1 (academic snow source audit; resumable collection)'


@contextmanager
def single_collector_lock(folder):
    """OS-released file lock: no stale PID claims or simultaneous appenders."""
    path = folder / 'collector.lock'
    with path.open('a+b') as stream:
        if path.stat().st_size == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        if sys.platform == 'win32':
            import msvcrt
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise RuntimeError('An OSHD collector already holds the lock; do not start another') from exc
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == 'win32':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class PublicRecordParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.records = []; self.links = set(); self.download_anchors = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('data-record'):
            self.records.append(json.loads(values['data-record']))
        if tag == 'link' and values.get('rel') in ['alternate', 'item']:
            self.links.add(values.get('href', ''))
        if tag == 'a' and values.get('href'):
            self.download_anchors.add(urljoin('https://zenodo.org/records/17313889', values['href']))


def official_download_anchor(text, canonical_url):
    """Only use an actual public-page anchor, not invented query parameters."""
    parser = PublicRecordParser(); parser.feed(text)
    alternative = canonical_url + '?download=1'
    if alternative not in parser.download_anchors:
        raise ValueError('Alternate download URL not present in archived public HTML')
    return alternative


def parse_record(text, years):
    parser = PublicRecordParser(); parser.feed(text)
    records = [r for r in parser.records if str(r.get('id')) == '17313889']
    if not records or any(r != records[0] for r in records):
        raise ValueError('Missing or inconsistent public record metadata')
    record = records[0]
    if record['access']['files'] != 'public' or not any(r.get('id') == 'cc-by-4.0' for r in record['metadata'].get('rights', [])):
        raise ValueError('Public data access/CC-BY4.0 not verified')
    files = []
    for year in years:
        key = f'OSHD_DATA_WY{year}.zip'
        item = record['files']['entries'][key]
        url = f'https://zenodo.org/records/17313889/files/{key}'
        if url not in parser.links or item['key'] != key or not item['checksum'].startswith('md5:'):
            raise ValueError('Download URL/key/checksum not grounded in public page')
        files.append(dict(water_year=year, key=key, url=url, expected_bytes=int(item['size']), expected_md5=item['checksum'][4:]))
    return record, files


def evidence(source_id):
    files = sorted((ROOT / 'data_external/source_evidence').glob(source_id + '_*.metadata.json'))
    if len(files) != 1:
        raise ValueError('Exactly one archived source required: ' + source_id)
    meta = json.loads(files[0].read_text(encoding='utf-8'))
    if digest(ROOT / meta['raw_file'])[1] != meta['sha256']:
        raise ValueError('Archived evidence integrity failure: ' + source_id)
    return meta


def digest(path):
    md5 = hashlib.md5(); sha = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            md5.update(block); sha.update(block)
    return md5.hexdigest(), sha.hexdigest()


def validate_download_response(response, start, total, end=None):
    status = response.status
    if end is not None:
        if status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{end}/{total}':
            raise ValueError('Server did not confirm exact bounded range; no append')
        expected_size = end-start+1
    elif start:
        if status != 206 or response.headers.get('Content-Range') != f'bytes {start}-{total-1}/{total}':
            raise ValueError('Server did not confirm exact suffix range; partial retained without append')
        expected_size = total-start
    elif status != 200:
        raise ValueError('Unexpected initial download status')
    else:
        expected_size = total
    if response.headers.get('Content-Length') and int(response.headers['Content-Length']) != expected_size:
        raise ValueError('Unexpected response byte count')


def publish_sources(state, html, paper):
    path = ROOT / 'metadata/data_sources_master.csv'
    master = pd.read_csv(path, dtype=str, keep_default_na=False)
    sources = []
    for meta in [html, paper]:
        sources.append(dict(source_id=meta['source_id'], variable_name='oshd_source_terms_and_file_manifest',
            variable_description='Original public source HTML, file URLs/checksums and explicit dataset license',
            source_organisation=meta['organisation'], source_dataset_name='OSHD source terms and record evidence',
            source_page_url=meta['url'], retrieval_date=meta['retrieval_date'], retrieval_method=meta['retrieval_method'] if 'retrieval_method' in meta else 'urllib GET with robots policy',
            local_raw_file=meta['raw_file'], license='Archived record explicitly CC-BY4.0; paper confirms dataset license',
            quality_notes='Public HTML rights separate from copyright: explicit cc-by-4.0 verified. General record API prohibited by robots and not called.',
            notes='sha256=' + meta['sha256']))
    sources.append(dict(source_id='SLF_OSHD_RECORD_API_METADATA_2026_10_09',
        variable_name='denied_record_api_method', variable_description='Record API collection stopped by robots policy, not a downloaded source',
        source_organisation='Zenodo', source_page_url='https://developers.zenodo.org/',
        api_endpoint='https://zenodo.org/api/records/17313889', retrieval_date='2026-10-09',
        retrieval_method='robots check denied endpoint before request', access_conditions='Disallow:/api; explicit file endpoints exception not used for general record API',
        quality_notes='No API original archived or fabricated; use authorized public record page, no robots bypass'))
    for file in state['files']:
        sources.append(dict(source_id=file['source_id'], variable_name='modelled_daily_snow_grid_candidate',
            variable_description=f"Original OSHD particle-filter daily model grid WY{file['water_year']}, source-audit candidate only",
            source_organisation='WSL SLF / Zenodo', source_dataset_name='OSHD250m2016-2025 version1.0 first useful audit batch',
            source_page_url=html['url'], direct_download_url=file['url'], retrieval_date=file.get('retrieval_date', ''),
            retrieval_method='Bounded exact206 byte ranges with robots crawl delay; no failed-request retry within execution; provider MD5/size/SHA256 validation',
            original_file_name=file['key'], local_raw_file=file.get('raw_file', ''),
            temporal_start=f"{file['water_year']-1}-09-01", temporal_end=f"{file['water_year']}-08-31",
            geographic_level='Swiss OSHD250m domain and hydrologically connected border regions', temporal_resolution='daily/monthly NetCDF archives',
            license='CC-BY4.0 explicit archived record rights; credit Oberrauch et al. dataset DOI10.5281/zenodo.17313889',
            transformation_applied='None: original ZIP bytes; no snow extraction, source mixing or profile mean',
            quality_notes='Collection status=' + file['status'] + '; different model from SPASS; current source audit not final feature choice',
            notes='expected_md5=' + file['expected_md5'] + '; validated_sha256=' + file.get('sha256', '') + '; last_request_url=' + file.get('last_request_url', file['url'])))
    ids = [s['source_id'] for s in sources]
    write_csv(pd.concat([master[~master.source_id.isin(ids)], pd.DataFrame(sources).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), path)


def run_collection():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume-failed', action='store_true', help='Explicit later retry of non-permission interruption; never HTTP401/403')
    parser.add_argument('--max-seconds', type=float, default=300, help='Session duration before retaining a resumable part; no source deletion')
    parser.add_argument('--chunk-bytes', type=int, default=8*1024*1024, help='Bounded byte-range request, never a whole unbounded suffix')
    parser.add_argument('--official-download-anchor', action='store_true', help='Use the archived public download=1 anchor after canonical-link HTTP504; identical archive checks remain')
    args = parser.parse_args()
    if args.max_seconds <= 0 or args.chunk_bytes <= 0:
        raise ValueError('Positive collection time budget required')
    deadline = time.monotonic() + args.max_seconds
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    if not config['oshd_candidate_audit_and_useful_collection_approved'] or config['snow_splicing_or_calibration_approved']:
        raise ValueError('Require source audit approval without automatic splicing')
    html = evidence('SLF_OSHD_RECORD_PUBLIC_HTML_2026_10_09'); paper = evidence('SLF_OSHD_PAPER_TERMS_HTML_2026_10_09')
    robots = sorted((ROOT / 'data_external/source_evidence').glob('zenodo.org_robots_20261009*.txt'))
    if not robots:
        raise ValueError('Archived robots policy required')
    policy = RobotFileParser(); policy.parse(robots[-1].read_text(encoding='utf-8').splitlines())
    years = sorted(config['collection_first_batch_water_years'], key=lambda y: (y == 2023, y))
    record, files = parse_record((ROOT / html['raw_file']).read_text(encoding='utf-8'), years)
    if any(not policy.can_fetch(AGENT, f['url']) for f in files):
        raise ValueError('robots policy does not allow file URLs')
    inputs = {CONFIG: digest(ROOT / CONFIG)[1], html['raw_file']: html['sha256'], paper['raw_file']: paper['sha256'], robots[-1].relative_to(ROOT).as_posix(): digest(robots[-1])[1]}
    manifest = ROOT / MANIFEST
    if manifest.exists():
        state = json.loads(manifest.read_text(encoding='utf-8'))
        if state['input_sha256'] != inputs:
            raise ValueError('Changed protocol/record: preserve existing download manifest and review')
    else:
        state = dict(date='2026-10-09', input_sha256=inputs, record_id=record['id'],
            dataset_license='cc-by-4.0', record_copyright=record['metadata'].get('copyright', ''),
            general_record_api_request_made=False, files=[dict(f, source_id=f"SLF_OSHD_PF_WY{f['water_year']}_PROFILE_AUDIT", status='pending') for f in files],
            snow_extracted=False, source_spliced=False, group_piste_assignment_applied=False, features_computed=False)
    def save():
        manifest.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        publish_sources(state, html, paper)
    save()
    if any(f.get('status') == 'failed' and not f.get('resume_allowed', False) for f in state['files']):
        print('Prior permission denial retained: no provider requests until access is reviewed.', flush=True)
        return
    folder = ROOT / 'data_interim/oshd_profile_downloads'; folder.mkdir(parents=True, exist_ok=True)
    last_request = None
    for file in state['files']:
        if time.monotonic() >= deadline:
            break
        if file['status'] == 'complete':
            raw = ROOT / file['raw_file']
            if raw.stat().st_size != file['expected_bytes'] or digest(raw) != (file['expected_md5'], file['sha256']):
                raise ValueError('Completed source integrity failure; do not overwrite')
            print(file['key'], 'cached, no request', flush=True)
            continue
        if file['status'] == 'failed' and (not args.resume_failed or not file.get('resume_allowed', False)):
            print(file['key'], 'failure retained, no new request', flush=True)
            continue
        part = folder / (file['key'] + '.part')
        start = part.stat().st_size if part.exists() else 0
        if start > file['expected_bytes']:
            raise ValueError('Partial exceeds provider size; preserve and investigate')
        timestamp = datetime.now(timezone.utc).isoformat()
        request_url = official_download_anchor((ROOT / html['raw_file']).read_text(encoding='utf-8'), file['url']) if args.official_download_anchor else file['url']
        if not policy.can_fetch(AGENT, request_url):
            raise PermissionError('robots policy does not allow requested download anchor')
        file.update(retrieval_date=timestamp, status='collecting', partial_file=part.relative_to(ROOT).as_posix(), downloaded_bytes=start)
        file['last_request_url'] = request_url
        save()
        try:
            while start < file['expected_bytes']:
                if time.monotonic() >= deadline:
                    file.update(status='paused', downloaded_bytes=start, pause_reason='session_time_budget_reached')
                    save()
                    return
                if last_request is not None:
                    time.sleep(max(0, (policy.crawl_delay(AGENT) or 10) - (time.monotonic() - last_request)))
                end = min(start + args.chunk_bytes, file['expected_bytes']) - 1
                headers = {'User-Agent': AGENT, 'Range': f'bytes={start}-{end}'}
                if file.get('etag'):
                    headers['If-Range'] = file['etag']
                last_request = time.monotonic()
                with urlopen(Request(request_url, headers=headers), timeout=60) as response:
                    if urlparse(response.geturl()).hostname != 'zenodo.org' or not policy.can_fetch(AGENT, response.geturl()):
                        raise PermissionError('Unapproved redirect destination')
                    validate_download_response(response, start, file['expected_bytes'], end)
                    file.update(http_status=response.status, etag=response.headers.get('ETag', ''), final_url=response.geturl())
                    next_report = start + 64 * 1024 * 1024
                    with part.open('ab' if start else 'xb') as stream:
                        while True:
                            block = response.read(min(1024 * 1024, end - start + 2))
                            if not block:
                                break
                            if start + len(block) > end+1:
                                raise ValueError('Response exceeds pinned size')
                            stream.write(block); start += len(block)
                            if start >= next_report:
                                stream.flush(); file['downloaded_bytes'] = start; save()
                                print(file['key'], f"{start}/{file['expected_bytes']} bytes", flush=True)
                                next_report = start + 64 * 1024 * 1024
                            if start < file['expected_bytes'] and time.monotonic() >= deadline:
                                stream.flush()
                                file.update(status='paused', downloaded_bytes=start, pause_reason='session_time_budget_reached')
                                save()
                                print(file['key'], f'paused at {start} bytes; ordinary invocation resumes next bounded range', flush=True)
                                return
                    if start != end+1:
                        raise ValueError('Incomplete range, validated prefix retained')
                    file['downloaded_bytes'] = start
                    save()
                    print(file['key'], f"{start}/{file['expected_bytes']} bytes, exact206 range", flush=True)
            if not part.exists() or part.stat().st_size != file['expected_bytes']:
                raise ValueError('Incomplete source stream, part retained')
            observed_md5, observed_sha = digest(part)
            if observed_md5 != file['expected_md5']:
                raise ValueError('Provider MD5 mismatch; part retained and not promoted')
            with zipfile.ZipFile(part) as archive:
                members = [dict(name=m.filename, uncompressed_bytes=m.file_size, compressed_bytes=m.compress_size) for m in archive.infolist()]
                if not any(m['name'].endswith('.nc') for m in members):
                    raise ValueError('No NetCDF members in source ZIP')
            raw = ROOT / 'data_external/source_evidence' / (file['source_id'] + '_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '.zip')
            if raw.exists():
                raise ValueError('Immutable output already exists')
            part.rename(raw)
            file.update(status='complete', raw_file=raw.relative_to(ROOT).as_posix(), sha256=observed_sha,
                downloaded_bytes=file['expected_bytes'], zip_members=members, provider_md5_verified=True, size_verified=True)
            with raw.with_suffix('.metadata.json').open('x', encoding='utf-8') as stream:
                json.dump(file, stream, ensure_ascii=False, indent=2)
            append_log(dict(timestamp=timestamp, task='stage45_approved_oshd_source_audit', source_id=file['source_id'],
                source='WSL SLF / Zenodo', source_url=file['url'], **{'URL/API': request_url}, request='GET validated bounded Range',
                retrieval_method='resumable streamed original ZIP; exact size and provider MD5/SHA256', HTTP_status=file.get('http_status', ''),
                status='downloaded', raw_file=file['raw_file'], output_file=file['raw_file'], checksum=observed_sha, success='True'))
            print(file['key'], 'complete, provider MD5 verified', flush=True)
        except Exception as exc:
            denied = isinstance(exc, PermissionError) or isinstance(exc, HTTPError) and exc.code in [401, 403]
            file.update(status='failed', error=f'{type(exc).__name__}: {exc}',
                resume_allowed=not denied, downloaded_bytes=part.stat().st_size if part.exists() else 0,
                http_status=getattr(exc, 'code', file.get('http_status', '')))
            append_log(dict(timestamp=timestamp, task='stage45_approved_oshd_source_audit', source_id=file['source_id'],
                source='WSL SLF / Zenodo', source_url=file['url'], **{'URL/API': request_url}, request='GET validated bounded Range',
                retrieval_method='no automatic retry; partial retained', HTTP_status=file.get('http_status', ''),
                status='failed', success='False', error=file['error']))
            print(file['key'], file['error'], flush=True)
            save()
            if denied or isinstance(exc, HTTPError) and 500 <= exc.code <= 599:
                break
        save()
    state['complete_file_count'] = sum(f['status'] == 'complete' for f in state['files'])
    save()
    print('OSHD audit files complete:', state['complete_file_count'], '/ 3; no features or splicing', flush=True)


def main():
    folder = ROOT / 'data_interim/oshd_profile_downloads'
    folder.mkdir(parents=True, exist_ok=True)
    with single_collector_lock(folder):
        run_collection()


if __name__ == '__main__':
    main()
