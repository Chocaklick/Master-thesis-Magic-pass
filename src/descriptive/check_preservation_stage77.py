"""Check historical files, Stage76, new SPASS caches and exact old registries."""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest
from src.data_processing.build_spass_preentry_profiles_stage77 import SUMMARY, SOURCE, validate_prefixes


def main():
    current = json.loads((ROOT/SUMMARY).read_text(encoding='utf8'))
    parent_path = 'reports/preservation_stage76_summary.json'
    if digest(parent_path) != current['input_sha256'][parent_path]:
        raise ValueError('Stage76 final preservation manifest changed')
    parent = json.loads((ROOT/parent_path).read_text(encoding='utf8'))
    prior = json.loads((ROOT/parent['parent_manifest']).read_text(encoding='utf8'))
    if digest(prior['parent_manifest']) != prior['parent_manifest_sha256']:
        raise ValueError('Historical preservation manifest changed')
    older = json.loads((ROOT/prior['parent_manifest']).read_text(encoding='utf8'))
    checks = older['checks'] + [dict(path=p, sha256=h) for p, h in prior['additional_checks'].items()]
    hashes = {}
    for r in checks:
        path = r['path']
        hashes.setdefault(path, r['sha256'])
        if hashes[path] != r['sha256']:
            raise ValueError('Conflicting historical source hash')
    for path, sha in {**parent['current_comparison_sha256'], **parent['current_producers']}.items():
        hashes[path] = sha
    for r in parent['new_original_archives_verified'].values():
        hashes[r['raw_file']] = r['sha256']
    # Preserve all previously committed Stage76 reports and configuration too.
    previous_paths = ['reports/121_EXTENSION_COMPARAISON_NEIGE_HUIT_HIVERS_FR.md',
        'reports/122_BILAN_NEIGE_HUIT_HIVERS_ET_CHOIX_PROFILS_FR.md',
        'reports/oshd_multiwinter_collection_stage76_summary.json',
        'reports/snow_multiwinter_comparison_stage76_summary.json',
        'reports/snow_multiwinter_runtime_stage76_summary.json', parent_path]
    import hashlib
    for path in previous_paths:
        original = subprocess.check_output(['git', 'show', 'b96fd90:'+path], cwd=ROOT)
        # Git LF vs working tree CRLF is not a scientific-data change.
        actual = (ROOT/path).read_bytes()
        if actual.replace(b'\r\n', b'\n') != original.replace(b'\r\n', b'\n'):
            raise ValueError('Previous Stage76 report changed: '+path)
        hashes[path] = hashlib.sha256(actual).hexdigest()
    for path, sha in {**current['input_sha256'], **current['output_sha256']}.items():
        hashes[path] = sha
    cache_count = 0
    for c in current['daily_checkpoints'].values():
        hashes[c['path']] = c['sha256']
        hashes[c['metadata']] = c['metadata_sha256']
        for m in c['source_checkpoints']:
            hashes[m['npz']] = m['npz_sha256']
            hashes[m['metadata']] = m['metadata_sha256']
            if 'calendar' in m:
                hashes[m['calendar']] = m['calendar_sha256']
            cache_count += 1
    for path, sha in hashes.items():
        if digest(path) != sha:
            raise ValueError('Original, earlier result or new checkpoint changed: '+path)
    validate_prefixes(current['prior_registry'])
    counts = {}
    for path, r in current['prior_registry'].items():
        f = pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)
        old = pd.read_csv(io.BytesIO(subprocess.check_output(['git', 'show', 'b96fd90:'+path], cwd=ROOT)), dtype=str, keep_default_na=False)
        if not old.equals(f.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Exact committed old table cells changed: '+path)
        appended = f.iloc[r['rows']:]
        if path.endswith('data_collection_log.csv'):
            if len(appended):
                raise ValueError('No new external collection was authorised or needed')
        elif not appended.source_id.eq(SOURCE).all():
            raise ValueError('Unexpected registry namespace')
        counts[path] = dict(prior_rows_exact=r['rows'], current_rows=len(f))
    state = dict(checked_at=datetime.now(timezone.utc).isoformat(), parent_manifest=parent_path,
        parent_sha256=digest(parent_path), historical_reference_count=len(checks),
        historical_unique_file_count=len({r['path'] for r in checks}), checked_unique_files=len(hashes),
        old_results_and_originals_unchanged=True, prior_tables_exact=counts,
        source_month_or_pilot_references_verified=cache_count, annual_daily_checkpoints_verified=len(current['daily_checkpoints']),
        new_external_requests=0, source_spliced_or_calibrated=False,
        checks=[dict(path=p, sha256=h) for p, h in hashes.items()])
    output = ROOT/'reports/preservation_stage77_summary.json'
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k: v for k, v in state.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
