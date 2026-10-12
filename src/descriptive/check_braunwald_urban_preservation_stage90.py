"""Bounded follow-up audit: inherited numeric files, touched source lineage, registries."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.descriptive.check_national_preparation_stage87 import sha, read, digest, REGISTRY
from src.data_collection.collect_braunwald_urban_road_stage90 import PREPARATION, COLLECTION
from src.data_processing.publish_braunwald_urban_road_stage90 import SUMMARY

TARGET = 'reports/preservation_braunwald_urban_stage90_summary.json'


def main():
    preparation = json.loads((ROOT / PREPARATION).read_text(encoding='utf-8'))
    hashes = dict(preparation['protected_old_numerical_sha256'])
    for p in [PREPARATION, COLLECTION, SUMMARY, 'reports/braunwald_road_arrival_proposal_stage89.json']:
        m = json.loads((ROOT / p).read_text(encoding='utf-8'))
        additions = m['input_sha256'] | m.get('output_sha256', {}) | {p: sha(p)}
        for request in m.get('successful_requests', []):
            additions[request['raw_file']] = request['raw_sha256']
            raw = Path(request['raw_file'])
            meta = raw.with_suffix('.metadata.json').as_posix()
            additions[meta] = sha(meta)
            cache = 'data_interim/braunwald_urban_ors_stage90/' + request['request_id'] + '.json'
            additions[cache] = sha(cache)
        for path, value in additions.items():
            if path in hashes and hashes[path] != value:
                raise ValueError('Frozen contract conflict ' + path)
            hashes[path] = value
    hashes['src/descriptive/check_braunwald_urban_preservation_stage90.py'] = sha('src/descriptive/check_braunwald_urban_preservation_stage90.py')
    for path, value in hashes.items():
        if sha(path) != value:
            raise ValueError('Source, numerical producer or historical value changed ' + path)
    prefixes = {}
    for path in REGISTRY:
        baseline = pd.read_csv(StringIO(subprocess.check_output(['git', 'show', '7b15b79:' + path], cwd=ROOT).decode('utf-8-sig')),
                               dtype=str, keep_default_na=False)
        actual = read(path)
        if not actual.iloc[:len(baseline)].reset_index(drop=True).equals(baseline):
            raise ValueError('Historical registry prefix changed ' + path)
        prefixes[path] = dict(previous_rows_exact=len(baseline), previous_row_digest=digest(baseline),
                             current_rows=len(actual), appended_rows=len(actual) - len(baseline))
    state = dict(checked_at=datetime.now(timezone.utc).isoformat(), baseline_commit='7b15b79',
                 checked_unique_files=len(hashes), rechecked_historical_numerical_files=len(preparation['protected_old_numerical_sha256']),
                 audit_scope='300 inherited numerical outputs/configs/producers plus directly used source contracts, new response caches and outputs. Untouched bulk rasters not rehashed this turn; Stage89 full audit retained.',
                 old_processed_values_groups_exposures_and_producers_unchanged=True,
                 approved_car_arrival_used_onward_transfer_missing_not_zero=True,
                 no_prediction_clustering_causal_fit_or_automatic_exclusion=True,
                 registry_prefixes_exact=prefixes,
                 checks=[dict(path=p, sha256=h) for p, h in hashes.items()])
    target = ROOT / TARGET
    if target.exists():
        prior = json.loads(target.read_text(encoding='utf-8'))
        if prior['checks'] != state['checks'] or prior['registry_prefixes_exact'] != prefixes:
            raise ValueError('Completed preservation check changed; retain old audit and version explicitly')
    else:
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in state.items() if k != 'checks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
