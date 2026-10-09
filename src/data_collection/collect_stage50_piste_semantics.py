"""Small public documentation batch, isolated log while snow collects.

No canonical CSV registry/log writes. Reuses source SHA/robots checks and stops
after an access/rate/server failure; no automatic denied-source retry.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence


def main():
    events = ROOT / 'data_interim/piste_semantics_events_stage50.json'
    def isolated_log(row):
        previous = json.loads(events.read_text(encoding='utf-8')) if events.exists() else []
        if any(str(r.get('HTTP_status', '')) in ['401','403','429'] or str(r.get('HTTP_status', '')).startswith('5') for r in previous):
            raise RuntimeError('Prior provider denial/rate/server failure requires review before retry')
        row['task'] = 'stage50_piste_semantics_documentation'
        previous.append(row)
        events.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if str(row.get('HTTP_status', '')) in ['401','403','429'] or str(row.get('HTTP_status', '')).startswith('5') or str(row.get('error','')).startswith('PermissionError'):
            raise RuntimeError('Failed provider/robots request retained; collection stops')
    if events.exists():
        previous = json.loads(events.read_text(encoding='utf-8'))
        if any(r.get('status') == 'failed' for r in previous):
            raise RuntimeError('Review prior source failure before any new request')
    collect_evidence.append_log = isolated_log
    sys.argv = ['collect_evidence', '--config', 'config/piste_semantics_evidence_stage50.json']
    collect_evidence.main()


if __name__ == '__main__':
    main()
