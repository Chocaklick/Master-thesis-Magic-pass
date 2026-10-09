"""Read-only integrity and exact registry-prefix reconciliation to milestone."""
import io
import json
import subprocess
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha


def main():
    reports=['piste_assignment_stage51_summary.json','piste_assignment_stage52_summary.json',
        'piste_geometry_roles_stage49_summary.json','piste_closed_semantics_stage50_summary.json',
        'piste_site_membership_audit_summary.json','piste_missing_member_collection_summary.json',
        'piste_official_page_audit_stage49_summary.json','piste_official_page_collection_stage49_summary.json',
        'piste_operator_evidence_stage47_summary.json','piste_scope_case_evidence_summary.json',
        'piste_plan_evidence_stage49_summary.json','piste_group_review_summary.json',
        'oshd_profile_audit_collection_summary.json','oshd_netcdf_metadata_inventory.json',
        'accessibility_road_did_15min_summary.json','accessibility_road_did_30min_summary.json',
        'accessibility_road_did_45min_summary.json','accessibility_road_final_collection_summary.json']
    checked=[]
    # Older consumers record a single digest; these paths are taken from their
    # original script constants, not inferred from a name or hash match.
    single_paths={
        ('piste_geometry_roles_stage49_summary.json','output_sha256'):'data_processed/winter_profile_piste_geometry_roles.csv',
        ('piste_closed_semantics_stage50_summary.json','output_sha256'):'data_processed/winter_profile_closed_piste_review_stage50.csv',
        ('piste_official_page_audit_stage49_summary.json','output_sha256'):'data_processed/winter_profile_official_page_coverage_stage49.csv',
        ('piste_missing_member_collection_summary.json','input_sha256'):'data_interim/winter_profile_piste_all_site_group_pairs.json',
        ('oshd_netcdf_metadata_inventory.json','inspector_sha256'):'src/descriptive/inspect_oshd_netcdf_metadata.py'}
    for name in reports:
        d=json.loads((ROOT/'reports'/name).read_text(encoding='utf-8'))
        for key in ['input_sha256','output_sha256','protected_legacy_sha256','inspector_sha256']:
            hashes=d.get(key,{})
            if isinstance(hashes,str):
                if (name,key) not in single_paths:raise ValueError('Unmapped single hash: '+name+' '+key)
                hashes={single_paths[(name,key)]:hashes}
            if not isinstance(hashes,dict):raise ValueError('Unsupported hash schema: '+name+' '+key)
            for path,h in hashes.items():
                if sha(path)!=h:raise ValueError('Protected prior changed: '+path)
                checked.append(dict(summary=name,path=path,sha256=h))
        if d.get('raw_file') and d.get('sha256'):
            if sha(d['raw_file'])!=d['sha256']:raise ValueError('Original source changed: '+d['raw_file'])
            checked.append(dict(summary=name,path=d['raw_file'],sha256=d['sha256']))
    registries=[]
    for name,keys in [('metadata/data_sources_master.csv',['source_id']),('metadata/data_dictionary.csv',['table','variable'])]:
        old_text=subprocess.check_output(['git','show','221d48a:'+name],cwd=ROOT).decode('utf-8')
        before=pd.read_csv(io.StringIO(old_text),dtype=str,keep_default_na=False)
        current=pd.read_csv(ROOT/name,dtype=str,keep_default_na=False)
        if current.duplicated(keys).any():raise ValueError('Duplicate provenance key')
        if not before.equals(current.iloc[:len(before)].reset_index(drop=True)):raise ValueError('Prior registry rows modified')
        registries.append(dict(path=name,prior_rows=len(before),current_rows=len(current),prior_rows_exact=True))
    d=json.loads((ROOT/'reports/piste_assignment_stage53_summary.json').read_text(encoding='utf-8'))
    for path,h in {**d['input_sha256'],**d['output_sha256']}.items():
        if sha(path)!=h:raise ValueError('Current checkpoint changed: '+path)
    state=dict(date='2026-10-10',protected_reference_count=len(checked),protected_unique_path_count=len({c['path'] for c in checked}),
        own_reference_count=len(d['input_sha256'])+len(d['output_sha256']),registry_reconciliation=registries,checks=checked)
    path=ROOT/'reports/piste_preservation_stage53_summary.json'
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=state:raise ValueError('Preservation audit changed')
    else:path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(len(checked),'protected SHAchecks;',len({c['path'] for c in checked}),'unique files; own hashes and exact old registries passed.')


if __name__=='__main__':main()
