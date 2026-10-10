"""Finite latest-reference rasters, immutable original SHA and cached reuse."""
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=499)
    args = parser.parse_args()
    config = 'config/terrain_reference_tile_sources_stage66.json'
    sources = json.loads((ROOT / config).read_text(encoding='utf8'))
    if len({s['source_id'] for s in sources}) != len(sources) or len({s['url'] for s in sources}) != len(sources):
        raise ValueError('Duplicate source ID or literal asset URL')
    path = ROOT / 'data_interim/terrain_reference_events_stage66.json'
    events = json.loads(path.read_text(encoding='utf8')) if path.exists() else []
    log = pd.read_csv(ROOT / 'logs/data_collection_log.csv', dtype=str, keep_default_na=False)
    failures = log[log.status.eq('failed') & ~log.error.map(local_network_block) & ~log.error.map(local_url_encoding_error)]
    failed_urls = set(failures.source_url)
    failed_hosts = {urlsplit(r.source_url).hostname for r in failures.itertuples() if r.source_url and r.HTTP_status != '404'}
    original_log, original_fetch = collect_evidence.append_log, collect_evidence.fetch
    collect_evidence.fetch = lambda url: original_fetch(request_url(url))

    def append(row):
        row['task'] = 'stage66_native2m_reference_collection'
        events.append(row)
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        original_log(row)

    collect_evidence.append_log = append
    for source in sources[:args.limit]:
        cached = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
        if not cached and (source['url'] in failed_urls or urlsplit(source['url']).hostname in failed_hosts):
            print('Prior failed URL/host retained; no retry', source['source_id'], flush=True)
            return
        before = len(events)
        sys.argv = ['collect_evidence', '--config', config, '--source-id', source['source_id']]
        collect_evidence.main()
        if len(events) > before and events[-1].get('status') != 'downloaded':
            print('Collection stopped on recorded failure; originals/checkpoints preserved', flush=True)
            return
        print(source['source_id'], 'checkpoint saved', flush=True)
    print('Finite reference queue complete; no terrain gradient or feature inferred.', flush=True)


if __name__ == '__main__':
    main()
