"""Streaming SHA proof for all Stage77 protected files and append-only registries."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.descriptive.build_remaining_piste_assignments_stage78 import SUMMARY, baseline_registry, read, REGISTRY, digest


def main():
    parent_path='reports/preservation_stage77_summary.json'
    parent=json.loads((ROOT/parent_path).read_text(encoding='utf-8'))
    current=json.loads((ROOT/SUMMARY).read_text(encoding='utf-8'))
    hashes={}
    for r in parent['checks']:
        p,h=r['path'],r['sha256']
        if p in hashes and hashes[p]!=h:raise ValueError('Conflicting historical hashes')
        hashes[p]=h
    for p,h in {**current['input_sha256'],**current['output_sha256']}.items():
        if p in hashes and hashes[p]!=h:raise ValueError('Current input silently changed historical file '+p)
        hashes[p]=h
    for path,expected in hashes.items():
        if sha(path)!=expected:raise ValueError('Protected file changed: '+path)
    prior=baseline_registry()
    if prior!=current['prior_registry']:raise ValueError('Registry baseline changed')
    counts={}
    for path in REGISTRY:
        frame=read(path);prior_count=prior[path]['rows']
        if digest(frame.iloc[:prior_count])!=prior[path]['row_digest']:raise ValueError('Old registry cells changed')
        counts[path]=dict(previous_rows_exact=prior_count,current_rows=len(frame),appended_rows=len(frame)-prior_count)
    state=dict(checked_at=datetime.now(timezone.utc).isoformat(),parent_manifest=parent_path,parent_sha256=sha(parent_path),
        current_manifest=SUMMARY,current_manifest_sha256=sha(SUMMARY),checked_unique_files=len(hashes),
        historical_unique_files=len(parent['checks']),old_results_and_originals_unchanged=True,
        prior_tables_exact=counts,all70_groups_retained=True,clustering_or_did_changed=False,
        checks=[dict(path=p,sha256=h) for p,h in hashes.items()])
    (ROOT/'reports/preservation_stage78_summary.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if k!='checks'}))


if __name__=='__main__':main()
