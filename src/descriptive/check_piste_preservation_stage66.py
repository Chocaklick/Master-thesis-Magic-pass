"""Extended raster audit preservation; append-only original data and registries."""
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

    previous = json.loads((ROOT / 'reports/piste_preservation_stage64_summary.json').read_text(encoding='utf8'))
    for row in previous['checks']:
        check(row['path'], row['sha256'], row['summary'])
    for name in ['terrain_catalogue_extension_stage65_summary.json', 'native2m_reference_stage66_summary.json']:
        current = json.loads((ROOT / 'reports' / name).read_text(encoding='utf8'))
        for p, h in {**current['input_sha256'], **current['output_sha256']}.items():
            check(p, h, name)
    # Also freeze the literal provenance sidecars, including reused pilot files.
    # No mutation of originals or inferred source/acquisition dates is allowed.
    queue = json.loads((ROOT / 'config/terrain_reference_tile_sources_stage66.json').read_text(encoding='utf8'))
    for source in queue:
        candidates = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
        if len(candidates) != 1:
            raise ValueError('Missing/ambiguous original source sidecar')
        p = candidates[0]
        meta = json.loads(p.read_text(encoding='utf8'))
        for key in ('source_id', 'url', 'item_reference_datetime', 'native_tile_key'):
            if meta.get(key) != source[key]:
                raise ValueError('Literal source provenance mismatch: ' + key)
        if meta['sha256'] != source['expected_sha256']:
            raise ValueError('Provider/source sidecar checksum mismatch')
        rel = p.relative_to(ROOT).as_posix()
        check(rel, hashlib.sha256(p.read_bytes()).hexdigest(), 'Original native reference provenance sidecar')
    registries = []
    for path, keys in [('metadata/data_sources_master.csv', ['source_id']), ('metadata/data_dictionary.csv', ['table', 'variable'])]:
        original = subprocess.check_output(['git', 'show', '973f501:' + path], cwd=ROOT).decode('utf8')
        old = pd.read_csv(io.StringIO(original), dtype=str, keep_default_na=False)
        new = pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)
        if new.duplicated(keys).any() or not old.equals(new.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Prior registry changed or duplicate keys: ' + path)
        registries.append(dict(path=path, baseline_commit='973f501', prior_rows=len(old), current_rows=len(new), prior_rows_exact=True))
    original_log = subprocess.check_output(['git', 'show', '973f501:logs/data_collection_log.csv'], cwd=ROOT)
    old = pd.read_csv(io.BytesIO(original_log), dtype=str, keep_default_na=False)
    current_log = pd.read_csv(ROOT / 'logs/data_collection_log.csv', dtype=str, keep_default_na=False)
    if not old.equals(current_log.iloc[:len(old)].reset_index(drop=True)):
        raise ValueError('Old collection rows changed')
    events = []
    for path in ['data_interim/terrain_catalogue_events_stage65.json', 'data_interim/terrain_reference_events_stage66.json']:
        events.extend(json.loads((ROOT / path).read_text(encoding='utf8')))
    delta = current_log.iloc[len(old):]
    if len(events) != 497 or len(delta) != 497 or delta.source_id.duplicated().any() or set(delta.source_id) != {e['source_id'] for e in events}:
        raise ValueError('Unexpected collection counts or duplicated source IDs')
    for event in events:
        row = delta[delta.source_id.eq(event['source_id'])].iloc[0]
        for col in ('source_url', 'checksum', 'timestamp', 'status', 'raw_file'):
            if row[col] != str(event.get(col, '')):
                raise ValueError('Original event/log mismatch')
        if row.status != 'downloaded' or row.HTTP_status != '200':
            raise ValueError('Incomplete collection; do not declare successful reference')
    state = dict(date='2026-10-10', protected_reference_count=len(checked), protected_unique_file_count=len(cache),
                 registry_reconciliation=registries, old_collection_rows_exact=len(old), new_collection_events_exact=len(delta), checks=checked)
    target = ROOT / 'reports/piste_preservation_stage66_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8')) != state:
            raise ValueError('Frozen preservation snapshot differs; use new stage')
    else:
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in state.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
