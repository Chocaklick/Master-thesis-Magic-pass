"""Finite independent-site batch, original cache and every failure retained.

No failed source or failed host is retried. Other unattempted hosts may continue;
this is operational collection, never automatic geographic assignment.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--config',default='config/piste_operator_evidence_stage52.json')
    args=parser.parse_args()
    sources=json.loads((ROOT/args.config).read_text(encoding='utf-8'))
    events_path=ROOT/'data_interim/piste_operator_events_stage52.json'
    events=json.loads(events_path.read_text(encoding='utf-8')) if events_path.exists() else []
    original_log=collect_evidence.append_log
    def append(row):
        row['task']='stage52_official_operator_verification'
        events.append(row)
        events_path.write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        original_log(row)
    collect_evidence.append_log=append
    for source in sources:
        failed_hosts={urlsplit(r['source_url']).hostname for r in events if r.get('status')=='failed'}
        if urlsplit(source['url']).hostname in failed_hosts:
            print(source['source_id'],'prior failed host retained, no request',flush=True)
            continue
        sys.argv=['collect_evidence','--config',args.config,'--source-id',source['source_id']]
        collect_evidence.main()
        print(source['source_id'],'checkpoint saved',flush=True)


if __name__=='__main__':main()
