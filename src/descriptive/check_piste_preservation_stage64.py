"""Append-only orientation milestone; preserve all prior pilot/source results."""
import hashlib
import io
import json
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main():
    checked, cache = [], {}

    def check(path, expected, summary):
        if path not in cache:
            digest = hashlib.sha256()
            with (ROOT / path).open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(block)
            cache[path] = digest.hexdigest()
        if cache[path] != expected:
            raise ValueError('Protected file changed: ' + path)
        checked.append(dict(path=path, sha256=expected, summary=summary))

    prior = json.loads((ROOT / 'reports/piste_preservation_stage63_summary.json').read_text(encoding='utf8'))
    for row in prior['checks']:
        check(row['path'], row['sha256'], row['summary'])
    current = json.loads((ROOT / 'reports/terrain_orientation_stage64_summary.json').read_text(encoding='utf8'))
    for path, h in {**current['input_sha256'], **current['output_sha256']}.items():
        check(path, h, 'terrain_orientation_stage64_summary.json')
    registries = []
    for path, keys in [('metadata/data_sources_master.csv', ['source_id']), ('metadata/data_dictionary.csv', ['table', 'variable'])]:
        original = subprocess.check_output(['git', 'show', '43443c8:' + path], cwd=ROOT).decode('utf8')
        old = pd.read_csv(io.StringIO(original), dtype=str, keep_default_na=False)
        new = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
        if new.duplicated(keys).any() or not old.equals(new.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Old registry changed or duplicate keys: ' + path)
        registries.append(dict(path=path, baseline_commit='43443c8', prior_rows=len(old), current_rows=len(new), prior_rows_exact=True))
    original_log = subprocess.check_output(['git', 'show', '43443c8:logs/data_collection_log.csv'], cwd=ROOT)
    working_log = (ROOT / 'logs/data_collection_log.csv').read_bytes()
    log_rows = pd.read_csv(io.BytesIO(working_log), dtype=str, keep_default_na=False)
    original_rows = pd.read_csv(io.BytesIO(original_log), dtype=str, keep_default_na=False)
    if working_log.replace(b'\r\n', b'\n') != original_log.replace(b'\r\n', b'\n') or not log_rows.equals(original_rows):
        raise ValueError('No new external collection was expected; original log changed')
    state = dict(date='2026-10-10', protected_reference_count=len(checked), protected_unique_file_count=len(cache),
                 registry_reconciliation=registries, collection_log_rows_exact=True,
                 collection_log_git_windows_line_endings_only=(working_log != original_log),
                 collection_log_working_sha256=hashlib.sha256(working_log).hexdigest(), checks=checked)
    target = ROOT / 'reports/piste_preservation_stage64_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8')) != state:
            raise ValueError('Frozen snapshot changed; use a new stage')
    else:
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in state.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
