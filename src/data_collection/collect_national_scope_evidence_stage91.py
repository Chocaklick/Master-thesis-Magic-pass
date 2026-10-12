"""Bounded independent primary plan/report queue; no failed provider-page retry."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence
from src.data_collection.collect_piste_operator_evidence_stage53 import request_url


def main():
    config = 'config/national_scope_sources_stage91.json'
    sources = json.loads((ROOT / config).read_text(encoding='utf-8'))
    path = ROOT / 'data_interim/national_scope_stage91/evidence_events.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    events = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    blocked = {e['source_id'] for e in events if e.get('status') == 'failed' and 'WinError 10013' not in e.get('error', '')}
    requested = {s['source_id'] for s in sources} - blocked
    if not requested:
        print('Retain source refusals without retry')
        return
    old_append, old_fetch = collect_evidence.append_log, collect_evidence.fetch
    collect_evidence.fetch = lambda url: old_fetch(request_url(url))

    def record(row):
        row['task'] = 'stage91_national_scope_and_common_decade_evidence'
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
