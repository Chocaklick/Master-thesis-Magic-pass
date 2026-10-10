"""Append-only readiness audit; no alteration of completed terrain/snow sources."""
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
    prior = json.loads((ROOT / 'reports/piste_preservation_stage67_summary.json').read_text(encoding='utf8'))
    s = json.loads((ROOT / 'reports/snow_comparison_readiness_stage68_summary.json').read_text(encoding='utf8'))
    checks,cache = [],{}
    for row in prior['checks'] + [dict(path=p,sha256=h,summary='Stage68 readiness') for p,h in {**s['input_sha256'],**s['output_sha256']}.items()]:
        p=row['path']
        if p not in cache:
            digest=hashlib.sha256()
            with (ROOT/p).open('rb') as f:
                for block in iter(lambda:f.read(1024*1024),b''):
                    digest.update(block)
            cache[p]=digest.hexdigest()
        if cache[p] != row['sha256']:
            raise ValueError('Protected file changed: '+p)
        checks.append(row)
    registry=[]
    for path,keys,extra in [('metadata/data_sources_master.csv',['source_id'],2),('metadata/data_dictionary.csv',['table','variable'],20)]:
        f=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        b=s['prior_registry_rows_and_digest'][path]
        if len(f) != b['rows']+extra or f.duplicated(keys).any() or row_digest(f.iloc[:b['rows']]) != b['sha256']:
            raise ValueError('Unexpected registry delta or changed prior rows')
        old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','ad80e4c:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
        if not old.equals(f.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Committed terrain registry prefix changed')
        registry.append(dict(path=path,prior_rows_exact=b['rows'],current_rows=len(f)))
    old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','ad80e4c:logs/data_collection_log.csv'],cwd=ROOT)),dtype=str,keep_default_na=False)
    new=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    if not old.equals(new):
        raise ValueError('Readiness stage must not alter collection log')
    state=dict(date='2026-10-10',protected_reference_count=len(checks),protected_unique_file_count=len(cache),
               registry_reconciliation=registry,collection_rows_unchanged=len(new),no_new_downloads=True,checks=checks)
    target=ROOT/'reports/preservation_stage68_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8')) != state:
            raise ValueError('Frozen preservation changed; use a new stage')
    else:
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in state.items() if k != 'checks'}))


if __name__ == '__main__':
    main()
