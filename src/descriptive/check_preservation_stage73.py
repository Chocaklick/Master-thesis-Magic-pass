"""Preserve Stage72 and earlier research; append-only documentary collection."""
import io
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.descriptive.audit_snow_compatibility_stage73 import DEFS


def main():
    prior = json.loads((ROOT/'reports/preservation_stage72_summary.json').read_text(encoding='utf8'))
    current = json.loads((ROOT/'reports/snow_compatibility_stage73_summary.json').read_text(encoding='utf8'))
    checks = list(prior['checks'])
    checks.extend(dict(path=p,sha256=h,summary='Stage73 documentary evidence, no analytical change')
        for p,h in {**current['input_sha256'],**current['output_sha256']}.items())
    cache = {}
    for row in checks:
        if row['path'] not in cache:
            cache[row['path']] = digest(row['path'])
        if cache[row['path']] != row['sha256']:
            raise ValueError('Protected file changed: '+row['path'])
    registry = []
    for path, keys, appended in [('metadata/data_sources_master.csv',['source_id'],7),('metadata/data_dictionary.csv',['table','variable'],len(DEFS))]:
        new = pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        baseline = current['prior_registry_rows_and_digest'][path]
        old = pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','86b6e37:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
        if len(new)!=baseline['rows']+appended or new.duplicated(keys).any() or row_digest(new.iloc[:baseline['rows']])!=baseline['sha256'] or not old.equals(new.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Prior registry or expected append changed: '+path)
        registry.append(dict(path=path,prior_rows_exact=len(old),current_rows=len(new),appended_rows=appended))
    path = 'logs/data_collection_log.csv'
    old = pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','86b6e37:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
    new = pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
    appended = new.iloc[len(old):]
    expected_ids = {r['source_id'] for r in json.loads((ROOT/'config/snow_compatibility_evidence_sources_stage73.json').read_text(encoding='utf8'))}
    if not old.equals(new.iloc[:len(old)].reset_index(drop=True)) or len(appended)!=10 or set(appended.source_id)!=expected_ids:
        raise ValueError('Collection history or scoped documentary requests changed')
    if (appended.success=='True').sum()!=6 or (appended.success=='False').sum()!=4:
        raise ValueError('Expected four sandbox failures and six archived successes')
    state = dict(date='2026-10-10',protected_reference_count=len(checks),protected_unique_file_count=len(cache),
        registry_reconciliation=registry,prior_collection_rows_exact=len(old),current_collection_rows=len(new),
        appended_documentary_events=len(appended),analytical_outputs_changed=False,checks=checks)
    target = ROOT/'reports/preservation_stage73_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8'))!=state:
            raise ValueError('Frozen preservation changed; use a new stage')
    else:
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in state.items() if k!='checks'}))


if __name__=='__main__':
    main()
