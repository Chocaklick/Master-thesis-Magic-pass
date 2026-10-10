"""Bounded resumable official STAC metadata, literal pagination only.

No original overwrite, completed-query repeat or host failure retry. Archives
every fetched page and every request outcome in a new checkpoint namespace.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence
from src.data_collection.collect_piste_operator_evidence_stage53 import local_network_block, local_url_encoding_error, request_url
from src.descriptive.verify_piste_assignments_stage51 import sha

CONFIG = 'config/terrain_group_catalogue_sources_stage65.json'
QUEUE = 'data_interim/terrain_catalogue_queue_stage65.json'
EVENTS = 'data_interim/terrain_catalogue_events_stage65.json'


def literal_next(payload):
    links = [l for l in payload.get('links', []) if l.get('rel') == 'next']
    if not links:
        return None
    if len(links) != 1 or links[0].get('method', 'GET') != 'GET':
        raise ValueError('Ambiguous/non-GET pagination needs review')
    url = links[0]['href']
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.netloc != 'data.geo.admin.ch' or parts.path != '/api/stac/v1/collections/ch.swisstopo.swissalti3d/items':
        raise ValueError('Unexpected pagination origin/path; no invented URL')
    return url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=120, help='Maximum new metadata-page requests this run')
    args = parser.parse_args()
    initial = json.loads((ROOT / CONFIG).read_text(encoding='utf8'))
    queue = json.loads((ROOT / QUEUE).read_text(encoding='utf8')) if (ROOT / QUEUE).exists() else initial.copy()
    if queue[:len(initial)] != initial or len({s['source_id'] for s in queue}) != len(queue):
        raise ValueError('Initial queue changed or duplicate source IDs')
    events = json.loads((ROOT / EVENTS).read_text(encoding='utf8')) if (ROOT / EVENTS).exists() else []
    log = pd.read_csv(ROOT / 'logs/data_collection_log.csv', dtype=str, keep_default_na=False)
    failures = log[log.status.eq('failed') & ~log.error.map(local_network_block) & ~log.error.map(local_url_encoding_error)]
    failed_urls = set(failures.source_url)
    failed_hosts = {urlsplit(r.source_url).hostname for r in failures.itertuples() if r.source_url and r.HTTP_status != '404'}
    original_log, original_fetch = collect_evidence.append_log, collect_evidence.fetch
    collect_evidence.fetch = lambda url: original_fetch(request_url(url))

    def append(row):
        row['task'] = 'stage65_terrain_catalogue_extension'
        events.append(row)
        (ROOT / EVENTS).write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        original_log(row)

    collect_evidence.append_log = append
    requests, complete = 0, []
    for root in initial:
        source = root
        visited = set()
        for page in range(1, 31):
            if source['url'] in visited:
                raise ValueError('Pagination loop; preserve incomplete group')
            visited.add(source['url'])
            metas = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
            if not metas:
                if requests >= args.limit:
                    print('Bounded request limit reached; resumable queue preserved', flush=True)
                    return
                if source['url'] in failed_urls or urlsplit(source['url']).hostname in failed_hosts:
                    print('Prior failed official URL/host retained; no retry', source['source_id'], flush=True)
                    return
                if source not in queue:
                    queue.append(source)
                (ROOT / QUEUE).write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
                before = len(events)
                sys.argv = ['collect_evidence', '--config', QUEUE, '--source-id', source['source_id']]
                collect_evidence.main()
                requests += 1
                if len(events) == before or events[-1].get('status') != 'downloaded':
                    print('Collection stopped on recorded failure; no automatic retry', flush=True)
                    return
                metas = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
            if len(metas) != 1:
                raise ValueError('Require a single original per page')
            meta = json.loads(metas[0].read_text(encoding='utf8'))
            if meta['url'] != source['url'] or sha(meta['raw_file']) != meta['sha256']:
                raise ValueError('Cached original/url integrity failure')
            payload = json.loads((ROOT / meta['raw_file']).read_bytes())
            if payload.get('type') != 'FeatureCollection' or 'features' not in payload:
                raise ValueError('Unexpected catalogue page; no inferred absence')
            next_url = literal_next(payload)
            if next_url is None:
                complete.append(root['station_group_id'])
                print(root['station_group_name'], 'complete metadata pages:', page, flush=True)
                break
            source = {**root, 'source_id': root['source_id'].removesuffix('P001') + f'P{page + 1:03}',
                      'url': next_url, 'page_number': page + 1, 'parent_source_id': root['source_id']}
        else:
            raise ValueError('Pagination safety bound reached; group not declared complete')
    print(json.dumps(dict(groups_complete=len(complete), new_requests=requests, completed_pilot_not_requested=True)), flush=True)


if __name__ == '__main__':
    main()
