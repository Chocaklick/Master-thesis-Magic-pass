"""New resumable evidence queue; preserve frozen Stage78 and provider refusals."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence
from src.data_collection.collect_piste_operator_evidence_stage53 import request_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-id', action='append')
    args = parser.parse_args()
    config = 'config/piste_remaining_sources_stage79.json'
    sources = json.loads((ROOT / config).read_text(encoding='utf-8'))
    path = ROOT / 'data_interim/piste_remaining_stage79/evidence_events.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    events = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    requested = set(args.source_id or [s['source_id'] for s in sources])
    blocked = {e['source_id'] for e in events if e.get('status') == 'failed'
               and 'WinError 10013' not in e.get('error', '')}
    requested -= blocked
    if not requested:
        print('No unblocked source to request')
        return
    old_append, old_fetch = collect_evidence.append_log, collect_evidence.fetch
    collect_evidence.fetch = lambda url: old_fetch(request_url(url))

    def record(row):
        row['task'] = 'stage79_remaining_piste_evidence'
        events.append(row)
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        old_append(row)

    collect_evidence.append_log = record
    sys.argv = ['collect_evidence', '--config', config]
    for sid in sorted(requested):
        sys.argv.extend(['--source-id', sid])
    collect_evidence.main()


if __name__ == '__main__':
    main()
