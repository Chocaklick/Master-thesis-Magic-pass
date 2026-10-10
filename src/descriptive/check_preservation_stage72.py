"""Verify prior sources/results and both snow diagnostics with append-only registries."""
import io
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.descriptive.diagnose_native_snow_changes_stage72 import DEFS


def main():
    prior=json.loads((ROOT/'reports/preservation_stage71_summary.json').read_text(encoding='utf8'))
    current=json.loads((ROOT/'reports/native_snow_change_rank_diagnostic_stage72_summary.json').read_text(encoding='utf8'))
    checks=list(prior['checks'])
    checks.extend(dict(path=p,sha256=h,summary='Stage72 approved complementary changes') for p,h in {**current['input_sha256'],**current['output_sha256']}.items())
    cache={}
    for r in checks:
        if r['path'] not in cache:
            cache[r['path']]=digest(r['path'])
        if cache[r['path']]!=r['sha256']:
            raise ValueError('Protected file changed: '+r['path'])
    registry=[]
    for path,keys,append in [('metadata/data_sources_master.csv',['source_id'],1),('metadata/data_dictionary.csv',['table','variable'],len(DEFS))]:
        f=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        b=current['prior_registry_rows_and_digest'][path]
        if len(f)!=b['rows']+append or f.duplicated(keys).any() or row_digest(f.iloc[:b['rows']])!=b['sha256']:
            raise ValueError('Registry baseline or append changed')
        old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','0473b28:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
        if not old.equals(f.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Committed Stage71 registry rows changed')
        registry.append(dict(path=path,prior_rows_exact=len(old),current_rows=len(f),appended_rows=len(f)-len(old)))
    old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','0473b28:logs/data_collection_log.csv'],cwd=ROOT)),dtype=str,keep_default_na=False)
    new=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    if not old.equals(new):
        raise ValueError('No new collection permitted in daily-change diagnostic')
    state=dict(date='2026-10-10',protected_reference_count=len(checks),protected_unique_file_count=len(cache),registry_reconciliation=registry,
        collection_rows_unchanged=len(new),no_new_downloads=True,checks=checks)
    target=ROOT/'reports/preservation_stage72_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8'))!=state:
            raise ValueError('Frozen preservation changed; use new stage')
    else:
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in state.items() if k!='checks'}))


if __name__=='__main__':
    main()
