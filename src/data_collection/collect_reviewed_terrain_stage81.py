"""Serial exact-queue Swiss raster collection; no repeat of original caches."""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.data_collection import collect_evidence
from src.data_collection.collect_reviewed_terrain_catalogue_stage80 import atomic_log
from src.data_collection.collect_piste_operator_evidence_stage53 import local_network_block,local_url_encoding_error,request_url
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha

CONFIG='config/terrain_reviewed_tile_sources_stage81.json'
EVENTS='data_interim/terrain_reviewed_events_stage81.json'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=10000);args=parser.parse_args()
    sources=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    if len({s['source_id'] for s in sources})!=len(sources) or len({s['url'] for s in sources})!=len(sources):raise ValueError('Duplicate request')
    proof=json.loads((ROOT/'reports/reviewed_terrain_queue_stage81_summary.json').read_text(encoding='utf-8'))
    if sha(CONFIG)!=proof['output_sha256'][CONFIG]:raise ValueError('Frozen queue changed')
    path=ROOT/EVENTS;events=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    log=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    keys=set(zip(log.timestamp,log.source_id))
    for event in events:
        if (event['timestamp'],event['source_id']) not in keys:
            if event['status']=='downloaded' and sha(event['raw_file'])!=event['checksum']:raise ValueError('Unlogged original changed')
            atomic_log(event)
    failed=log[log.status.eq('failed')&~log.error.map(local_network_block)&~log.error.map(local_url_encoding_error)]
    failed_urls=set(failed.source_url);failed_hosts={urlsplit(r.source_url).hostname for r in failed.itertuples() if r.source_url and r.HTTP_status!='404'}
    fetch=collect_evidence.fetch;collect_evidence.fetch=lambda url:fetch(request_url(url))
    def append(row):
        row['task']='stage81_reviewed_native2m_collection';events.append(row)
        path.write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');atomic_log(row)
    collect_evidence.append_log=append
    requests=0;cached=0
    for s in sources:
        old=s.get('cached_raw_file')
        if old:
            if sha(old)!=s['expected_sha256']:raise ValueError('Original cached raster changed')
            cached+=1;continue
        found=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if not found and (s['url'] in failed_urls or urlsplit(s['url']).hostname in failed_hosts):
            print('Prior actual failed source retained, no retry:',s['source_id'],flush=True);return
        if not found and requests>=args.limit:break
        before=len(events);sys.argv=['collect_evidence','--config',CONFIG,'--source-id',s['source_id']];collect_evidence.main()
        if len(events)>before:
            requests+=1
            if events[-1]['status']!='downloaded':
                print('Stopped after actual failure; checkpoint and original retained',flush=True);return
        else:cached+=1
        print('Swiss native tile checkpoint',cached+requests,'/',len(sources),flush=True)
    print('Run finished:',requests,'new requests;',cached,'cached originals reused',flush=True)


if __name__=='__main__':main()
