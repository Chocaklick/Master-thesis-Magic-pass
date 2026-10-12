"""Single documented arrival source, new namespace, no ORS call or stop choice."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence
from src.data_collection.collect_piste_operator_evidence_stage53 import request_url


def main():
    path = ROOT / 'data_interim/national_arrival_stage89/evidence_events.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    events = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    if any(e['status'] == 'failed' and 'WinError 10013' not in e.get('error', '') for e in events):
        print('Preserve actual provider refusal; no retry')
        return
    old_append, old_fetch = collect_evidence.append_log, collect_evidence.fetch
    collect_evidence.fetch = lambda url: old_fetch(request_url(url))
    def record(row):
        row['task'] = 'stage89_national_arrival_evidence'
        events.append(row)
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        old_append(row)
    collect_evidence.append_log = record
    sys.argv = ['collect_evidence', '--config', 'config/national_arrival_sources_stage89.json']
    collect_evidence.main()


if __name__ == '__main__':
    main()
