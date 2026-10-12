"""Additive archival follow-up, keep the completed Stage87 audit frozen."""
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


def main():
    parent_path = 'reports/preservation_national_stage87_summary.json'
    parent = json.loads((ROOT / parent_path).read_text(encoding='utf-8'))
    hashes = {r['path']: r['sha256'] for r in parent['checks']}
    paths = ['reports/national_preparation_work_queue_stage88_summary.json', 'reports/braunwald_road_arrival_proposal_stage89.json']
    for p in paths:
        m = json.loads((ROOT / p).read_text(encoding='utf-8'))
        for path, h in (m['input_sha256'] | m.get('output_sha256', {}) | {p: sha(p)}).items():
            if path in hashes and hashes[path] != h:
                raise ValueError('Frozen proof conflict ' + path)
            hashes[path] = h
    hashes[parent_path] = sha(parent_path)
    own = 'src/descriptive/check_national_preservation_stage89.py'
    hashes[own] = sha(own)
    ep = 'data_interim/national_arrival_stage89/evidence_events.json'
    hashes[ep] = sha(ep)
    for i, (p, h) in enumerate(hashes.items(), 1):
        if sha(p) != h:
            raise ValueError('Original/frozen source or old result changed ' + p)
        if i % 700 == 0:
            print('Verified', i, 'files', flush=True)
    prefixes = {}
    for path in REGISTRY:
        old = pd.read_csv(StringIO(subprocess.check_output(['git', 'show', 'b639eea:' + path], cwd=ROOT).decode('utf-8-sig')),
                          dtype=str, keep_default_na=False)
        actual = read(path)
        if not actual.iloc[:len(old)].reset_index(drop=True).equals(old):
            raise ValueError('Historical registry prefix changed ' + path)
        prefixes[path] = dict(previous_rows_exact=len(old), previous_row_digest=digest(old), current_rows=len(actual), appended_rows=len(actual) - len(old))
    state = dict(checked_at=datetime.now(timezone.utc).isoformat(), baseline_commit='b639eea',
                 historical_unique_files=len(parent['checks']), checked_unique_files=len(hashes),
                 all_old_sources_preentry_profiles_caches_exposures_and_DiD_unchanged=True,
                 no_new_domain_group_merge_ORS_route_prediction_causal_fit_or_clustering=True,
                 three_additional_scope_population_and_urban_reference_choices_validated=True,
                 exact_braunwald_valley_stop_proposed_not_yet_used=True,
                 registry_prefixes_exact=prefixes, checks=[dict(path=p, sha256=h) for p, h in hashes.items()])
    target = ROOT / 'reports/preservation_national_stage89_summary.json'
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf-8'))
        if previous['checks'] != state['checks'] or previous['registry_prefixes_exact'] != prefixes:
            raise ValueError('Completed preservation audit differs')
    else:
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in state.items() if k != 'checks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
