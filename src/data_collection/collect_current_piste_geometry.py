"""One bounded, read-only OSM piste query; immutable evidence and no assignments.

A successful checkpoint is reused without a network call. Failures remain
recorded and are not automatically retried. Existing groups are never rebuilt.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_evidence import append_log

CONFIG = 'config/winter_profile_terrain_snow_source_review_stage44.json'
CHECKPOINT = 'data_interim/current_piste_geometry_collection_checkpoint.json'
AGENT = 'ThesisSkiResearch/0.1 (academic piste source inventory; one cached query)'


def validate_response(payload):
    if payload.get('remark'):
        raise ValueError('Overpass remark signals incomplete/error response: ' + payload['remark'])
    if not payload.get('osm3s', {}).get('timestamp_osm_base'):
        raise ValueError('Missing OSM snapshot timestamp')
    elements = payload.get('elements')
    if not isinstance(elements, list) or not elements:
        raise ValueError('Empty or missing inventory, not absence of pistes')
    keys = [(e['type'], e['id']) for e in elements]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate upstream keys')
    for e in elements:
        if e['type'] not in ['way', 'relation'] or not e.get('version') or not e.get('timestamp'):
            raise ValueError('Missing upstream version/date or unexpected element kind')
        tags = e.get('tags', {})
        if tags.get('piste:type') != 'downhill' and tags.get('site') != 'piste':
            raise ValueError('Unexpected element selection')
    return len(elements)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--retry-failed', action='store_true', help='Explicitly reviewed later retry; no automatic loop')
    args = parser.parse_args()
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    config_sha = hashlib.sha256((ROOT / CONFIG).read_bytes()).hexdigest()
    checkpoint = ROOT / CHECKPOINT
    if checkpoint.exists():
        prior = json.loads(checkpoint.read_text(encoding='utf-8'))
        if prior['config_sha256'] != config_sha:
            raise ValueError('Changed collection protocol requires separate checkpoint')
        if prior['status'] == 'complete':
            raw = ROOT / prior['raw_file']
            if hashlib.sha256(raw.read_bytes()).hexdigest() != prior['sha256']:
                raise ValueError('Cached source integrity failure')
            validate_response(json.loads(raw.read_bytes()))
            print('Exact piste source checkpoint reused; no new request or assignment.')
            return
        if not args.retry_failed:
            print('Previous piste collection failure retained; no new request. See checkpoint.')
            return
    stamp = datetime.now(timezone.utc); token = stamp.strftime('%Y%m%dT%H%M%SZ')
    sid = config['piste_source_id']; folder = ROOT / 'data_external/source_evidence'
    folder.mkdir(parents=True, exist_ok=True)
    row = dict(timestamp=stamp.isoformat(), task='stage44_current_piste_inventory', source_id=sid,
        source='OpenStreetMap contributors via Overpass API', source_url=config['piste_endpoint'],
        **{'URL/API': config['piste_endpoint']}, request=config['piste_query'],
        retrieval_method='one bounded read-only Overpass POST, no automatic retries', success='False')
    metadata = dict(source_id=sid, retrieval_date=stamp.isoformat(), endpoint=config['piste_endpoint'],
        query=config['piste_query'], config_sha256=config_sha, status='failed', group_assignment_applied=False)
    try:
        request = Request(config['piste_endpoint'], data=urlencode({'data': config['piste_query']}).encode(),
            headers={'User-Agent': AGENT, 'Content-Type': 'application/x-www-form-urlencoded'})
        with urlopen(request, timeout=75) as response:
            content = response.read(config['piste_max_response_bytes'] + 1)
            metadata['http_status'] = response.status
            metadata['final_url'] = response.geturl()
        if len(content) > config['piste_max_response_bytes']:
            raise ValueError('Response exceeds bounded collection limit; not archived as complete')
        # Preserve original response even when incomplete; validation precedes promotion.
        raw = folder / f'{sid}_{token}.json'
        with raw.open('xb') as stream:
            stream.write(content)
        metadata.update(raw_file=raw.relative_to(ROOT).as_posix(), size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest())
        payload = json.loads(content); count = validate_response(payload)
        metadata.update(status='complete', element_count=count, osm_snapshot=payload['osm3s']['timestamp_osm_base'])
        row.update(success='True', HTTP_status=metadata['http_status'], status='downloaded',
            raw_file=metadata['raw_file'], output_file=metadata['raw_file'], checksum=metadata['sha256'], rows_collected=count)
    except Exception as exc:
        metadata.update(error=f'{type(exc).__name__}: {exc}', http_status=getattr(exc, 'code', metadata.get('http_status')))
        row.update(status='failed', HTTP_status=metadata.get('http_status'), error=metadata['error'])
        if isinstance(exc, HTTPError):
            # Archive the denial/error as such, never disguise it as a geometry response.
            denied = folder / f'{sid}_{token}.error.txt'
            with denied.open('xb') as stream:
                stream.write(exc.read())
            metadata['error_response_file'] = denied.relative_to(ROOT).as_posix()
    evidence_meta = folder / f'{sid}_{token}.metadata.json'
    with evidence_meta.open('x', encoding='utf-8') as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2)
    append_log(row)
    checkpoint.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metadata, ensure_ascii=True))


if __name__ == '__main__':
    main()
