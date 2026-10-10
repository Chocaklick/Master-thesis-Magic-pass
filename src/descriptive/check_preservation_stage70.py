"""Protect native weights/source values and all prior evidence/registry prefixes."""
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


def main():
    prior=json.loads((ROOT/'reports/preservation_stage68_summary.json').read_text(encoding='utf8'))
    manifests=[json.loads((ROOT/p).read_text(encoding='utf8')) for p in [
        'reports/native_snow_weights_stage69_summary.json','reports/native_snow_values_stage70_summary.json']]
    checks=list(prior['checks'])
    for stage,s in zip([69,70],manifests):
        checks.extend(dict(path=p,sha256=h,summary=f'Stage{stage} approved native snow audit') for p,h in {**s['input_sha256'],**s['output_sha256']}.items())
    for key,m in manifests[1]['source_value_checkpoints'].items():
        path=f'data_interim/native_snow_values_stage70/{key}.npz'
        checks.append(dict(path=path,sha256=m['cache_sha256'],summary='Resumable original-unit values/masks'))
        path=f'data_interim/native_snow_values_stage70/{key}.json'
        saved=json.loads((ROOT/path).read_text(encoding='utf8'))
        if saved!=m:
            raise ValueError('Source-value checkpoint manifest differs: '+key)
        checks.append(dict(path=path,sha256=digest(path),summary='Source-value checkpoint contract'))
    cache={}
    for r in checks:
        if r['path'] not in cache:
            cache[r['path']]=digest(r['path'])
        if cache[r['path']]!=r['sha256']:
            raise ValueError('Protected original/derived file changed: '+r['path'])
    registry=[]
    for path,keys,count in [('metadata/data_sources_master.csv',['source_id'],1201),('metadata/data_dictionary.csv',['table','variable'],8188)]:
        f=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        if len(f)!=count or f.duplicated(keys).any():
            raise ValueError('Unexpected registry counts or duplicates')
        for s in manifests:
            b=s['prior_registry_rows_and_digest'][path]
            if row_digest(f.iloc[:b['rows']])!=b['sha256']:
                raise ValueError('Prior registry rows changed')
        old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','49185e0:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
        if not old.equals(f.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Committed Stage68 registry prefix changed')
        registry.append(dict(path=path,committed_prior_rows_exact=len(old),current_rows=len(f),appended_rows=len(f)-len(old)))
    old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','49185e0:logs/data_collection_log.csv'],cwd=ROOT)),dtype=str,keep_default_na=False)
    current=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    if not old.equals(current):
        raise ValueError('Collection log changed without collection')
    state=dict(date='2026-10-10',protected_reference_count=len(checks),protected_unique_file_count=len(cache),registry_reconciliation=registry,
        collection_rows_unchanged=len(current),no_new_downloads=True,checks=checks)
    target=ROOT/'reports/preservation_stage70_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8'))!=state:
            raise ValueError('Frozen preservation audit differs; use new stage')
    else:
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in state.items() if k!='checks'}))


if __name__=='__main__':
    main()
