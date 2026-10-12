"""New bounded official evidence queue; preserve originals and actual refusals."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence
from src.data_collection.collect_piste_operator_evidence_stage53 import request_url


def main():
    config = 'config/national_operator_sources_stage88.json'
    sources = json.loads((ROOT / config).read_text(encoding='utf-8'))
    path = ROOT / 'data_interim/national_preparation_stage88/evidence_events.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    events = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    blocked = {e['source_id'] for e in events if e.get('status') == 'failed' and 'WinError 10013' not in e.get('error', '')}
    requested = {s['source_id'] for s in sources} - blocked
    if not requested:
        print('All unsuccessful sources retain provider refusal; no retry')
        return
    old_append, old_fetch = collect_evidence.append_log, collect_evidence.fetch
    collect_evidence.fetch = lambda url: old_fetch(request_url(url))

    def record(row):
        row['task'] = 'stage88_national_domain_evidence_preparation'
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
