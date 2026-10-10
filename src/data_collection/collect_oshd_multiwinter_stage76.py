"""New approved seven-archive batch; old collector and checkpoints immutable.

Public-page links only, pinned sizes/MD5, exact bounded HTTP206 ranges. Prefixes
survive interruption, provider denials stop, no automatic failed-request retry.
"""
import argparse
import json
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_oshd_profile_audit import (
    evidence, digest, parse_record, official_download_anchor, validate_download_response,
    single_collector_lock, AGENT, SOURCE_COLUMNS)
from src.data_collection.collect_evidence import append_log
from src.data_processing.atomic_csv_output import write_csv

CONFIG = 'config/snow_multiwinter_decisions_stage76.json'
SUMMARY = 'reports/oshd_multiwinter_collection_stage76_summary.json'
FOLDER = ROOT/'data_interim/oshd_multiwinter_stage76_downloads'


def current_robot_policy(original):
    """Refresh the public policy after 24h; retain every immutable snapshot.

    The pinned initial evidence stays unchanged. Current permission, not a
    stale snapshot, governs resumed requests. Failure stops collection.
    """
    candidates = []
    for path in (ROOT/'data_external/source_evidence').glob('ZENODO_ROBOTS_REFRESH_STAGE76_*.metadata.json'):
        m = json.loads(path.read_text(encoding='utf8'))
        if digest(ROOT/m['raw_file'])[1] != m['sha256']:
            raise ValueError('Refreshed robots evidence changed')
        candidates.append(m)
    initial = dict(raw_file=original.relative_to(ROOT).as_posix(),
        sha256=digest(original)[1], retrieval_date='2026-10-09T16:39:57+00:00')
    m = max(candidates+[initial], key=lambda r:r['retrieval_date'])
    now = datetime.now(timezone.utc)
    if (now-datetime.fromisoformat(m['retrieval_date'])).total_seconds() < 86400:
        return (ROOT/m['raw_file']).read_text(encoding='utf8'), m
    url = 'https://zenodo.org/robots.txt'
    stamp = now.isoformat()
    sid = 'ZENODO_ROBOTS_REFRESH_STAGE76_'+now.strftime('%Y%m%dT%H%M%SZ')
    event = dict(timestamp=stamp, task='stage76_approved_eight_winter_snow_comparison',
        source_id=sid, source='Zenodo', source_url=url, **{'URL/API':url}, request='GET',
        retrieval_method='Public robots policy refresh after 24h; no dataset request', success='False')
    try:
        with urlopen(Request(url,headers={'User-Agent':AGENT}),timeout=60) as response:
            event['HTTP_status']=response.status
            if response.status!=200 or response.geturl()!=url:
                raise PermissionError('Unexpected robots response; stop, no stale-policy fallback')
            content=response.read()
        text=content.decode('utf8')
        # Check understood group/rule syntax before any dataset request.
        zenodo_can_fetch(text,'https://zenodo.org/records/17313889')
        raw=ROOT/'data_external/source_evidence'/(sid+'.txt')
        with raw.open('xb') as stream:
            stream.write(content)
        m=dict(source_id=sid,retrieval_date=stamp,raw_file=raw.relative_to(ROOT).as_posix(),
            sha256=digest(raw)[1],size_bytes=len(content),url=url,http_status=200)
        with raw.with_suffix('.metadata.json').open('x',encoding='utf8') as stream:
            json.dump(m,stream,ensure_ascii=False,indent=2)
        path=ROOT/'metadata/data_sources_master.csv'
        master=pd.read_csv(path,dtype=str,keep_default_na=False)
        row=dict(source_id=sid,variable_name='collection_robots_policy',
            variable_description='Current public robots permission for resumed Stage76 archive requests',
            source_organisation='Zenodo',source_dataset_name='Public robots.txt',source_page_url=url,
            direct_download_url=url,retrieval_date=stamp,original_file_name='robots.txt',
            local_raw_file=m['raw_file'],retrieval_method=event['retrieval_method'],
            transformation_applied='None; immutable original text',quality_notes='Collection policy only, not an analytical feature',
            notes='sha256='+m['sha256'])
        write_csv(pd.concat([master,pd.DataFrame([row]).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),path)
        event.update(success='True',status='downloaded',raw_file=m['raw_file'],checksum=m['sha256'])
        append_log(event)
        print('Current robots policy archived:',m['raw_file'],flush=True)
        return text,m
    except Exception as exc:
        event.update(status='failed',error=f'{type(exc).__name__}: {exc}',HTTP_status=getattr(exc,'code',event.get('HTTP_status','')))
        append_log(event)
        raise


def zenodo_can_fetch(text, url):
    """RFC9309 longest matching rule for this single wildcard/ASCII snapshot.

    urllib.robotparser uses first match and does not implement wildcard paths.
    Reject changed user-agent structure or encoded paths rather than guess.
    RFC9309 sections2.2.2/2.2.3: specific rule first, Allow wins equal length.
    """
    parsed=urlparse(url)
    path=parsed.path+('?' + parsed.query if parsed.query else '')
    if parsed.scheme!='https' or parsed.hostname!='zenodo.org' or not path.isascii() or '%' in path:
        return False
    lines=[line.split('#',1)[0].strip() for line in text.splitlines()]
    agents=[line.split(':',1)[1].strip() for line in lines if line.lower().startswith('user-agent:')]
    if agents!=['*']:
        raise ValueError('Changed robot groups require complete policy review')
    matches=[]
    for line in lines:
        if ':' not in line:
            continue
        kind,pattern=[s.strip() for s in line.split(':',1)]
        kind=kind.lower()
        if kind not in ['allow','disallow'] or not pattern:
            continue
        if not pattern.isascii() or '%' in pattern:
            raise ValueError('Non-ASCII/encoded rules require full RFC parser')
        terminal=pattern.endswith('$')
        literal=pattern[:-1] if terminal else pattern
        expression='^'+re.escape(literal).replace(r'\*','.*')+('$' if terminal else '')
        if re.match(expression,path):
            matches.append((len(literal.replace('*','').encode('ascii')),kind=='allow'))
    return max(matches)[1] if matches else True


def publish_sources(state):
    path = ROOT/'metadata/data_sources_master.csv'
    master = pd.read_csv(path, dtype=str, keep_default_na=False)
    additions = []
    for f in state['files']:
        row = dict(source_id=f['source_id'], variable_name='modelled_daily_snow_grid_multiwinter_diagnostic',
                   variable_description=f"Original OSHD WY{f['water_year']} archive for approved eight-winter comparison, not a substituted SPASS feature",
                   source_organisation='WSL SLF / Zenodo', source_dataset_name='OSHD250m2016-2025 version1.0',
                   source_page_url='https://zenodo.org/records/17313889', direct_download_url=f['url'],
                   retrieval_date=f.get('retrieval_date', ''), original_file_name=f['key'], local_raw_file=f.get('raw_file', ''),
                   retrieval_method='Archived public anchor; exact HTTP206 ranges, size/provider MD5/SHA256; interruption checkpoint, no automatic failed-request retry',
                   temporal_start=f"{f['water_year']-1}-09-01", temporal_end=f"{f['water_year']}-08-31",
                   geographic_level='OSHD native250m Switzerland and connected border regions', temporal_resolution='daily, monthly NetCDF in annual ZIP',
                   license='CC-BY4.0; Oberrauch et al., DOI10.5281/zenodo.17313889', transformation_applied='None: original archive bytes',
                   quality_notes='Collection status='+f['status']+'; no calibration/splice, exclusion or preentry substitution',
                   notes='expected_md5='+f['expected_md5']+'; sha256='+f.get('sha256', '')+'; last_request_url='+f.get('last_request_url', '')+'; '+SUMMARY)
        mask = master.source_id.eq(f['source_id'])
        if mask.sum() > 1:
            raise ValueError('Duplicate new source ID')
        if mask.any():
            for col in SOURCE_COLUMNS:
                master.loc[mask, col] = row.get(col, '')
        else:
            additions.append(row)
    write_csv(pd.concat([master, pd.DataFrame(additions).reindex(columns=SOURCE_COLUMNS).fillna('')], ignore_index=True), path)


def save(state):
    state['complete_file_count'] = sum(f['status']=='complete' for f in state['files'])
    state['downloaded_bytes'] = sum(f.get('downloaded_bytes', 0) for f in state['files'])
    (ROOT/SUMMARY).write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    publish_sources(state)


def log_request(f, request_url, start, end, stamp, success, error=''):
    append_log(dict(timestamp=stamp, task='stage76_approved_eight_winter_snow_comparison',
                    source_id=f['source_id'], source='WSL SLF / Zenodo', source_url=f['url'],
                    **{'URL/API': request_url}, request=f'GET Range bytes={start}-{end}',
                    retrieval_method='public file anchor, robots delay and exact range validation',
                    HTTP_status=f.get('http_status', ''), status='range_received' if success else 'failed',
                    success=str(success), error=error, notes=f"Prefix bytes={f.get('downloaded_bytes', 0)}; archive not approved for use until MD5/size verified"))


def run(args):
    decisions = json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['collection_water_years'] != list(range(2016, 2023)) or decisions['source_splicing_or_calibration']:
        raise ValueError('Require approved extension without splicing')
    html = evidence('SLF_OSHD_RECORD_PUBLIC_HTML_2026_10_09')
    text = (ROOT/html['raw_file']).read_text(encoding='utf8')
    robots = ROOT/'data_external/source_evidence/zenodo.org_robots_20261009T163957Z.txt'
    robot_text=robots.read_text(encoding='utf8')
    record, files = parse_record(text, decisions['collection_water_years'])
    inputs = {CONFIG:digest(ROOT/CONFIG)[1], html['raw_file']:html['sha256'],
              robots.relative_to(ROOT).as_posix():digest(robots)[1],
              'src/data_collection/collect_oshd_profile_audit.py':digest(ROOT/'src/data_collection/collect_oshd_profile_audit.py')[1]}
    target = ROOT/SUMMARY
    if target.exists():
        state = json.loads(target.read_text(encoding='utf8'))
        if state['input_sha256'] != inputs:
            raise ValueError('Frozen approved protocol/source changed; new namespace required')
    else:
        state = dict(date='2026-10-10', input_sha256=inputs, dataset_license='cc-by-4.0', record_id='17313889',
                     files=[dict(f, source_id=f"SLF_OSHD_PF_WY{f['water_year']}_MULTIWINTER_STAGE76", status='pending') for f in files],
                     expected_bytes=sum(f['expected_bytes'] for f in files), general_record_api_request_made=False,
                     source_spliced_or_calibrated=False, snow_extracted=False)
    state.setdefault('collector_runs', []).append(dict(started_at=datetime.now(timezone.utc).isoformat(),
        producer_sha256=digest(Path(__file__))[1], chunk_bytes=args.chunk_bytes,
        canonical_download_link=args.canonical_download_link, published_file_content=args.published_file_content,
        resume_failed=args.resume_failed, checkpoint_only=args.checkpoint_only,
        only_water_year=args.only_water_year, continue_pending=args.continue_pending))
    save(state)
    if args.checkpoint_only:
        print(json.dumps({k:v for k,v in state.items() if k!='files'}), flush=True); return
    robot_text, current_policy = current_robot_policy(robots)
    state['collector_runs'][-1]['current_robots_policy'] = current_policy
    save(state)
    policy = RobotFileParser(); policy.parse(robot_text.splitlines())
    deadline = time.monotonic()+args.max_seconds
    # Include the preceding policy request in the minimum crawl interval.
    last_request = time.monotonic()
    for f in state['files']:
        if args.only_water_year is not None and f['water_year']!=args.only_water_year:
            continue
        if f['status']=='complete':
            raw = ROOT/f['raw_file']
            if raw.stat().st_size != f['expected_bytes'] or digest(raw) != (f['expected_md5'], f['sha256']):
                raise ValueError('Completed immutable archive changed')
            continue
        if f['status']=='failed' and (not f.get('resume_allowed') or not args.resume_failed):
            print(f['key'], 'failure retained, no retry', flush=True)
            if args.continue_pending and f.get('resume_allowed'):
                continue
            return
        part = FOLDER/(f['key']+'.part')
        start = part.stat().st_size if part.exists() else 0
        if start > f['expected_bytes']:
            raise ValueError('Oversize partial retained for investigation')
        # Both alternatives are literal published links checked by parse_record.
        url = f['url'] if args.canonical_download_link else official_download_anchor(text, f['url'])
        if args.published_file_content:
            url = record['files']['entries'][f['key']]['links']['content']
            # The archived robots explicit file exception is not the forbidden
            # general record metadata API; no fabricated URL or access bypass.
            parsed = urlparse(url)
            if parsed.scheme!='https' or parsed.hostname!='zenodo.org' or not parsed.path.startswith('/api/records/17313889/files/') or not parsed.path.endswith('/content'):
                raise ValueError('Unexpected published file-content link')
            state['published_file_content_api_used'] = True
        if not zenodo_can_fetch(robot_text, url):
            raise PermissionError('robots denies archived file anchor')
        f.update(status='collecting', downloaded_bytes=start, partial_file=part.relative_to(ROOT).as_posix(), last_request_url=url)
        save(state)
        try:
            while start < f['expected_bytes']:
                if time.monotonic() >= deadline:
                    f.update(status='paused', pause_reason='execution_budget_checkpoint'); save(state); return
                if last_request is not None:
                    time.sleep(max(0, (policy.crawl_delay(AGENT) or 10)-(time.monotonic()-last_request)))
                end = min(start+args.chunk_bytes, f['expected_bytes'])-1
                stamp = datetime.now(timezone.utc).isoformat()
                f.update(retrieval_date=stamp, last_range_start=start, last_range_end=end, http_status='')
                headers = {'User-Agent':AGENT, 'Range':f'bytes={start}-{end}'}
                if f.get('etag'):
                    headers['If-Range'] = f['etag']
                last_request = time.monotonic(); request_start = start
                with urlopen(Request(url, headers=headers), timeout=60) as response:
                    f['http_status'] = response.status
                    if not zenodo_can_fetch(robot_text, response.geturl()):
                        raise PermissionError('Unapproved redirect')
                    validate_download_response(response, start, f['expected_bytes'], end)
                    f.update(etag=response.headers.get('ETag', ''), final_url=response.geturl())
                    with part.open('ab' if start else 'xb') as stream:
                        while start <= end:
                            block = response.read(min(1024*1024, end-start+1))
                            if not block:
                                raise ValueError('Incomplete range; received prefix retained')
                            stream.write(block); start += len(block)
                        if response.read(1):
                            raise ValueError('Oversize response; archive retained, not promoted')
                f['downloaded_bytes'] = start
                log_request(f, url, request_start, end, stamp, True)
                save(state)
                print(f['key'], f"{start}/{f['expected_bytes']} bytes, exact206", flush=True)
            observed_md5, sha = digest(part)
            if observed_md5 != f['expected_md5'] or part.stat().st_size != f['expected_bytes']:
                raise ValueError('Archive MD5/size mismatch; not promoted')
            with zipfile.ZipFile(part) as archive:
                members = [dict(name=m.filename, uncompressed_bytes=m.file_size, compressed_bytes=m.compress_size) for m in archive.infolist()]
                if not any(m['name'].endswith('.nc') for m in members):
                    raise ValueError('No NetCDF members')
            raw = ROOT/'data_external/source_evidence'/(f['source_id']+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.zip')
            if raw.exists():
                raise ValueError('Refuse overwrite of original')
            part.rename(raw)
            f.update(status='complete', raw_file=raw.relative_to(ROOT).as_posix(), sha256=sha,
                     downloaded_bytes=f['expected_bytes'], zip_members=members, provider_md5_verified=True, size_verified=True)
            with raw.with_suffix('.metadata.json').open('x', encoding='utf8') as stream:
                json.dump(f, stream, ensure_ascii=False, indent=2)
            save(state); print(f['key'], 'COMPLETE provider MD5/size verified', flush=True)
        except Exception as exc:
            denied = isinstance(exc, PermissionError) or isinstance(exc, HTTPError) and exc.code in [401, 403]
            f.update(status='failed', error=f'{type(exc).__name__}: {exc}', resume_allowed=not denied,
                     downloaded_bytes=part.stat().st_size if part.exists() else 0,
                     http_status=getattr(exc, 'code', f.get('http_status', '')))
            log_request(f, url, f.get('last_range_start', start), f.get('last_range_end', start),
                        f.get('retrieval_date', datetime.now(timezone.utc).isoformat()), False, f['error'])
            save(state); print(f['key'], f['error'], flush=True)
            if args.continue_pending and not denied:
                continue
            return
    print('Additional OSHD archives complete:', state['complete_file_count'], '/ 7; no splicing', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume-failed', action='store_true')
    parser.add_argument('--max-seconds', type=float, default=3600)
    parser.add_argument('--chunk-bytes', type=int, default=32*1024*1024)
    parser.add_argument('--checkpoint-only', action='store_true')
    parser.add_argument('--canonical-download-link', action='store_true', help='Published rel=item URL without download query; same robots/range/MD5 rules')
    parser.add_argument('--published-file-content', action='store_true', help='Literal file content link from archived metadata, explicit robots Allow:/api/records/*/files; never general record API')
    parser.add_argument('--continue-pending', action='store_true', help='Do not retry failed files; try other independent pending archives, stop entire batch on access denial')
    parser.add_argument('--only-water-year', type=int, choices=list(range(2016,2023)), help='Single approved archive, other checkpoints unchanged')
    args = parser.parse_args()
    if args.max_seconds <= 0 or args.chunk_bytes <= 0:
        raise ValueError('Positive duration/chunk size required')
    FOLDER.mkdir(exist_ok=True)
    with single_collector_lock(FOLDER):
        run(args)


if __name__ == '__main__':
    main()
