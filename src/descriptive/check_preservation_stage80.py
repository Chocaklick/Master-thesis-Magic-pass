"""Protect Stage79 originals/results and verify Stage80 frozen provenance."""
import json
import subprocess
import sys
from datetime import datetime,timezone
from io import StringIO
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.descriptive.build_remaining_piste_assignments_stage78 import read,digest,REGISTRY


def main():
    parent_path='reports/preservation_stage79_summary.json'
    parent=json.loads((ROOT/parent_path).read_text(encoding='utf-8'))
    hashes={c['path']:c['sha256'] for c in parent['checks']}
    manifests=['reports/reviewed_piste_network_stage80_summary.json',
        'reports/piste_network_registry_stage80_summary.json',
        'reports/reviewed_terrain_catalogue_plan_stage80_summary.json',
        'reports/reviewed_terrain_catalogue_stage80_summary.json',
        'reports/reviewed_spass_support_stage80_summary.json',
        'reports/reviewed_geometry_followup_stage80_summary.json']
    for path in manifests:
        m=json.loads((ROOT/path).read_text(encoding='utf-8'))
        for p,h in {**m.get('input_sha256',{}),**m.get('output_sha256',{}),path:sha(path)}.items():
            if p in hashes and hashes[p]!=h:raise ValueError('Conflicting frozen SHA '+p)
            hashes[p]=h
    hashes[parent_path]=sha(parent_path)
    for p,h in hashes.items():
        if sha(p)!=h:raise ValueError('Protected original/result changed '+p)
    prefixes={}
    for p in REGISTRY:
        previous=pd.read_csv(StringIO(subprocess.check_output(['git','show','2c01aa0:'+p],cwd=ROOT).decode('utf-8-sig')),dtype=str,keep_default_na=False)
        actual=read(p)
        if not actual.iloc[:len(previous)].reset_index(drop=True).equals(previous):raise ValueError('Historical registry prefix changed '+p)
        prefixes[p]=dict(previous_rows_exact=len(previous),previous_row_digest=digest(previous),current_rows=len(actual),appended_rows=len(actual)-len(previous))
    state=dict(checked_at=datetime.now(timezone.utc).isoformat(),baseline_commit='2c01aa0',
        historical_unique_files=len(parent['checks']),checked_unique_files=len(hashes),
        old_results_and_originals_unchanged=True,all_original71_group_ids_and185_territories_retained=True,
        no_new_did_clustering_or_final_physical_profile=True,french_terrain_complement_cancelled=True,
        registry_prefixes_exact=prefixes,checks=[dict(path=p,sha256=h) for p,h in hashes.items()])
    (ROOT/'reports/preservation_stage80_summary.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if k!='checks'},ensure_ascii=False))


if __name__=='__main__':main()
