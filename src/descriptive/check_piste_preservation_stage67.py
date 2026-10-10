"""Protect old science, immutable native terrain and approved seam summaries."""
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.summarise_terrain_reference_stage67 import row_digest


def main():
    old = json.loads((ROOT / 'reports/piste_preservation_stage66_summary.json').read_text(encoding='utf8'))
    current = json.loads((ROOT / 'reports/terrain_reference_profiles_stage67_summary.json').read_text(encoding='utf8'))
    checks, cache = [], {}
    for row in old['checks'] + [dict(path=p, sha256=h, summary='Approved Stage67') for p, h in {**current['input_sha256'], **current['output_sha256']}.items()]:
        p = row['path']
        if p not in cache:
            digest = hashlib.sha256()
            with (ROOT / p).open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            cache[p] = digest.hexdigest()
        if cache[p] != row['sha256']:
            raise ValueError('Protected file changed: ' + p)
        checks.append(row)
    registries = []
    for path, keys in [('metadata/data_sources_master.csv', ['source_id']), ('metadata/data_dictionary.csv', ['table', 'variable'])]:
        f = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
        baseline = current['prior_registry_rows_and_digest'][path]
        if f.duplicated(keys).any() or row_digest(f.iloc[:baseline['rows']]) != baseline['sha256']:
            raise ValueError('Prior Stage66 registry changed or duplicate keys')
        git_old = pd.read_csv(io.BytesIO(subprocess.check_output(['git', 'show', '973f501:' + path], cwd=ROOT)), dtype=str, keep_default_na=False)
        if not git_old.equals(f.iloc[:len(git_old)].reset_index(drop=True)):
            raise ValueError('Prior Stage64 registry changed')
        expected = baseline['rows'] + (1 if keys == ['source_id'] else 35)
        if len(f) != expected:
            raise ValueError('Unexpected registry delta')
        registries.append(dict(path=path, prior_rows_exact=baseline['rows'], current_rows=len(f)))
    old_log = pd.read_csv(io.BytesIO(subprocess.check_output(['git', 'show', '973f501:logs/data_collection_log.csv'], cwd=ROOT)), dtype=str, keep_default_na=False)
    log = pd.read_csv(ROOT / 'logs/data_collection_log.csv', dtype=str, keep_default_na=False)
    if not old_log.equals(log.iloc[:len(old_log)].reset_index(drop=True)):
        raise ValueError('Old collection rows changed')
    events = sum([json.loads((ROOT / p).read_text(encoding='utf8')) for p in ['data_interim/terrain_catalogue_events_stage65.json', 'data_interim/terrain_reference_events_stage66.json']], [])
    delta = log.iloc[len(old_log):]
    if len(events) != 497 or len(delta) != 497 or delta.source_id.duplicated().any():
        raise ValueError('Unexpected request/duplicate source after collection complete')
    if set(delta.source_id) != {e['source_id'] for e in events}:
        raise ValueError('Event/source mismatch')
    for e in events:
        row = delta[delta.source_id.eq(e['source_id'])].iloc[0]
        if row.status != 'downloaded' or row.HTTP_status != '200' or any(row[c] != str(e.get(c, '')) for c in ('source_url', 'checksum', 'timestamp', 'status', 'raw_file')):
            raise ValueError('Literal original event/log mismatch')
    state = dict(date='2026-10-10', protected_reference_count=len(checks), protected_unique_file_count=len(cache),
                 registry_reconciliation=registries, old_collection_rows_exact=len(old_log), new_collection_events_exact=len(delta),
                 no_new_stage67_requests=True, checks=checks)
    target = ROOT / 'reports/piste_preservation_stage67_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8')) != state:
            raise ValueError('Frozen preservation differs; use new stage')
    else:
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in state.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
