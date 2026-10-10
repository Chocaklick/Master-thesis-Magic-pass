"""Finite dated-source queue; preserve originals, failures and prior checkpoints."""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_collection import collect_evidence
from src.data_collection.collect_piste_operator_evidence_stage53 import local_network_block,local_url_encoding_error,request_url


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--limit',type=int,default=12)
    parser.add_argument('--config',default='config/terrain_tile_sources_stage62.json')
    args=parser.parse_args()
    sources=json.loads((ROOT/args.config).read_text(encoding='utf-8'))
    if len({s['source_id'] for s in sources})!=len(sources):raise ValueError('Duplicate source ID')
    path=ROOT/'data_interim/terrain_tile_events_stage62.json'
    events=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    log=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    failures=log[log.status.eq('failed') & ~log.error.map(local_network_block) & ~log.error.map(local_url_encoding_error)]
    failed_urls=set(failures.source_url)
    failed_hosts={urlsplit(r.source_url).hostname for r in failures.itertuples() if r.source_url and r.HTTP_status!='404'}
    original_log=collect_evidence.append_log
    original_fetch=collect_evidence.fetch
    collect_evidence.fetch=lambda url:original_fetch(request_url(url))
    def append(row):
        row['task']='stage62_piste_terrain_source_verification'
        events.append(row)
        path.write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        original_log(row)
    collect_evidence.append_log=append
    for s in sources[:args.limit]:
        cached=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        hostname=urlsplit(s['url']).hostname
        if not cached and (s['url'] in failed_urls or hostname in failed_hosts):
            if not any(e['source_id']==s['source_id'] for e in events):
                append(dict(timestamp=collect_evidence.datetime.now(collect_evidence.timezone.utc).isoformat(),source_id=s['source_id'],source_url=s['url'],status='not_requested_prior_failed_host',success='False',error='Prior remote failure retained; no retry'))
            print(s['source_id'],'prior failure retained',flush=True)
            continue
        before=len(events)
        sys.argv=['collect_evidence','--config',args.config,'--source-id',s['source_id']]
        collect_evidence.main()
        if len(events)>before and events[-1].get('status')=='failed':
            if local_network_block(events[-1].get('error')):
                print('Local socket restriction: collection paused, not provider absence',flush=True)
                break
            failed_urls.add(s['url'])
            if str(events[-1].get('HTTP_status'))!='404':failed_hosts.add(hostname)
        print(s['source_id'],'checkpoint saved',flush=True)


if __name__=='__main__':main()
