"""Finite official-link batch, cache-preserving; stops after any failed request."""
import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scope', action='store_true')
    parser.add_argument('--source-id', action='append')
    args = parser.parse_args()
    events = ROOT / 'data_interim/piste_operator_events_stage51.json'
    previous = json.loads(events.read_text(encoding='utf-8')) if events.exists() else []
    if any(r.get('status') == 'failed' and (not args.source_id or r['source_id'] in args.source_id) for r in previous):
        raise RuntimeError('Prior failure requires review; do not retry automatically')
    def log(row):
        row['task'] = 'stage51_official_operator_verification'
        previous.append(row)
        events.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        collect_evidence_log(row)
        if row.get('status') == 'failed':
            raise RuntimeError('Request failed and retained; stop batch without bypass')
    collect_evidence_log = collect_evidence.append_log
    collect_evidence.append_log = log
    config = 'config/piste_operator_scope_evidence_stage51.json' if args.scope else 'config/piste_operator_evidence_stage51.json'
    sys.argv = ['collect_evidence', '--config', config]
    for source_id in args.source_id or []:
        sys.argv.extend(['--source-id', source_id])
    collect_evidence.main()


if __name__ == '__main__':
    main()
