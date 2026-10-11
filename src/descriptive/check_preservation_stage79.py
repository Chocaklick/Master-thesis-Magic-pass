"""Streaming historical SHA and exact append-only registries; no analytical changes."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.descriptive.build_remaining_piste_assignments_stage78 import read, digest, REGISTRY


def main():
    parent_path = 'reports/preservation_stage78_summary.json'
    parent = json.loads((ROOT/parent_path).read_text(encoding='utf-8'))
    hashes = {c['path']:c['sha256'] for c in parent['checks']}
    manifests = ['reports/remaining_piste_assignments_stage79_summary.json',
        'reports/wilerallmi_schwanden_regrouping_stage79_summary.json',
        'reports/piste_historical_qa_stage79_summary.json']
    for p in manifests:
        state = json.loads((ROOT/p).read_text(encoding='utf-8'))
        for path,h in {**state['input_sha256'], **state['output_sha256'], p:sha(p)}.items():
            if path in hashes and hashes[path] != h:
                raise ValueError('Conflicting historical SHA: '+path)
            hashes[path] = h
    hashes[parent_path] = sha(parent_path)
    for p,h in hashes.items():
        if sha(p) != h:
            raise ValueError('Protected file changed: '+p)
    counts = {}
    for p in REGISTRY:
        raw = subprocess.check_output(['git','show','b1226de:'+p], cwd=ROOT)
        prior = pd.read_csv(StringIO(raw.decode('utf-8-sig')), dtype=str, keep_default_na=False)
        actual = read(p)
        if not actual.iloc[:len(prior)].reset_index(drop=True).equals(prior):
            raise ValueError('Registry prefix changed: '+p)
        counts[p] = dict(previous_rows_exact=len(prior), previous_row_digest=digest(prior),
                        current_rows=len(actual), appended_rows=len(actual)-len(prior))
    state = dict(checked_at=datetime.now(timezone.utc).isoformat(), baseline_commit='b1226de',
        historical_unique_files=len(parent['checks']), checked_unique_files=len(hashes),
        old_results_and_originals_unchanged=True, all_original71_group_ids_and185_territories_retained=True,
        no_new_did_clustering_or_physical_profile=True, registry_prefixes_exact=counts,
        checks=[dict(path=p, sha256=h) for p,h in hashes.items()])
    (ROOT/'reports/preservation_stage79_summary.json').write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if k != 'checks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
