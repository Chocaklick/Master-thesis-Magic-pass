"""New preservation snapshot after approved exact geometry/context extension."""
import hashlib
import io
import json
import subprocess
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]


def main():
    checked=[];cache={}
    def check(path,expected,summary):
        if path not in cache:
            digest=hashlib.sha256()
            with (ROOT/path).open('rb') as stream:
                for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
            cache[path]=digest.hexdigest()
        if cache[path]!=expected:raise ValueError('Protected file changed: '+path)
        checked.append(dict(path=path,sha256=expected,summary=summary))
    prior=json.loads((ROOT/'reports/piste_preservation_stage56_summary.json').read_text(encoding='utf-8'))
    for row in prior['checks']:check(row['path'],row['sha256'],row['summary'])
    summaries=['connected_profile_context_stage57_summary.json','exact_piste_overlap_stage58_summary.json','exact_overlap_geometry_stage59_summary.json']
    for name in summaries:
        data=json.loads((ROOT/'reports'/name).read_text(encoding='utf-8'))
        for key in ['input_sha256','output_sha256']:
            for path,h in data.get(key,{}).items():check(path,h,name)
    registries=[]
    for path,keys in [('metadata/data_sources_master.csv',['source_id']),('metadata/data_dictionary.csv',['table','variable'])]:
        original=subprocess.check_output(['git','show','b7ab9de:'+path],cwd=ROOT).decode('utf-8')
        old=pd.read_csv(io.StringIO(original),dtype=str,keep_default_na=False)
        new=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        if new.duplicated(keys).any() or not old.equals(new.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Prior registry changed or duplicate keys')
        registries.append(dict(path=path,baseline_commit='b7ab9de',prior_rows=len(old),current_rows=len(new),prior_rows_exact=True))
    state=dict(date='2026-10-10',protected_reference_count=len(checked),protected_unique_file_count=len(cache),registry_reconciliation=registries,checks=checked)
    target=ROOT/'reports/piste_preservation_stage59_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8'))!=state:raise ValueError('Frozen audit snapshot changed; use a new stage')
    else:target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(len(checked),'SHA references;',len(cache),'unique files; all old registry rows exact.')


if __name__=='__main__':main()
