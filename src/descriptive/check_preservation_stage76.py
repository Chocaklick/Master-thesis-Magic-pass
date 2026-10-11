"""Checkpoint proof of protected earlier research and append-only Stage76 rows."""
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest
from src.data_collection.collect_oshd_multiwinter_stage76 import digest as archive_digest


def main():
    p='reports/preservation_stage75_summary.json'
    parent=json.loads((ROOT/p).read_text(encoding='utf8'))
    if digest(parent['parent_manifest'])!=parent['parent_manifest_sha256']:
        raise ValueError('Protected parent manifest changed')
    older=json.loads((ROOT/parent['parent_manifest']).read_text(encoding='utf8'))
    checks=older['checks']+[{ 'path':path,'sha256':sha } for path,sha in parent['additional_checks'].items()]
    hashes={}
    for r in checks:
        path=r['path']
        if path not in hashes:
            hashes[path]=digest(path)
        if hashes[path]!=r['sha256']:
            raise ValueError('Protected earlier file changed: '+path)
    prefix={}
    for path in ['metadata/data_sources_master.csv','metadata/data_dictionary.csv','logs/data_collection_log.csv']:
        old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','5ced79e:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
        new=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        if not old.equals(new.iloc[:len(old)].reset_index(drop=True)):
            raise ValueError('Earlier exact table prefix changed: '+path)
        if path.endswith('data_collection_log.csv'):
            appended=new.iloc[len(old):]
            allowed=appended.task.eq('stage76_approved_eight_winter_snow_comparison') | (
                appended.task.eq('initial_source_verification') & appended.source_id.eq('IETF_ROBOTS_LONGEST_RULE_RFC9309_STAGE76'))
            if not allowed.all():
                raise ValueError('Unexpected collection scope')
        prefix[path]=dict(prior_rows_exact=len(old),current_rows=len(new))
    current=json.loads((ROOT/'reports/snow_multiwinter_comparison_stage76_summary.json').read_text(encoding='utf8'))
    for path,sha in {**current['input_sha256'],**current['output_sha256']}.items():
        if digest(path)!=sha:
            raise ValueError('Current extraction checkpoint changed: '+path)
    daily_assembly_checks=0
    for year,m in current['year_checkpoints'].items():
        path=f'data_interim/snow_multiwinter_stage76/daily_WY{year}.csv'
        if digest(path)!=m['sha256']:
            raise ValueError('Annual cache changed')
        for key,c in m['source_checkpoints'].items():
            if 'contract' not in c or 'sha256' not in c:
                continue
            month_path=f'data_interim/snow_multiwinter_stage76/values/{key}.npz'
            if digest(month_path)!=c['sha256']:
                raise ValueError('Monthly selected-value cache changed')
            assembly=c.get('exact_daily_assembly')
            if not assembly:
                continue
            if assembly['producer_sha256']!=digest(assembly['producer']) or assembly['interpolation_or_precision_change']:
                raise ValueError('Daily assembly producer changed')
            with np.load(ROOT/month_path,allow_pickle=False) as cache:
                month_values=cache['values']
            lookup={date:i for i,date in enumerate(c['observed_dates'])}
            for day in assembly['daily_checkpoints']:
                day_path=f"data_interim/snow_multiwinter_stage76/values/{day['key']}.npz"
                if digest(day_path)!=day['sha256']:
                    raise ValueError('Daily selected-value cache changed')
                date=day['key'][-10:]
                with np.load(ROOT/day_path,allow_pickle=False) as cache:
                    day_values=cache['values']
                if date in lookup:
                    np.testing.assert_allclose(month_values[lookup[date]],day_values[0],rtol=0,atol=0,equal_nan=True)
                elif len(day_values)!=0:
                    raise ValueError('Observed daily row incorrectly absent from monthly cache')
                daily_assembly_checks+=1
    collection=json.loads((ROOT/'reports/oshd_multiwinter_collection_stage76_summary.json').read_text(encoding='utf8'))
    archives={}
    for r in collection['files']:
        if r['status']!='complete':
            continue
        path=ROOT/r['raw_file']
        observed_md5,observed_sha=archive_digest(path)
        if path.stat().st_size!=r['expected_bytes'] or observed_md5!=r['expected_md5'] or observed_sha!=r['sha256']:
            raise ValueError('Completed new original archive changed')
        archives[str(r['water_year'])]=dict(raw_file=r['raw_file'],sha256=observed_sha,provider_md5_verified=True)
    policies=[]
    for path in (ROOT/'data_external/source_evidence').glob('ZENODO_ROBOTS_REFRESH_STAGE76_*.metadata.json'):
        m=json.loads(path.read_text(encoding='utf8'))
        if digest(m['raw_file'])!=m['sha256']:
            raise ValueError('Original refreshed robots policy changed')
        policies.append(m)
    preparation=json.loads((ROOT/'reports/spass_multiwinter_cache_preparation_stage76_summary.json').read_text(encoding='utf8'))
    for month,m in preparation['months'].items():
        path=f'data_interim/snow_multiwinter_stage76/values/spass_{month}.npz'
        if digest(path)!=m['cache_sha256']:
            raise ValueError('Prepared SPASS cache changed')
    if not preparation['all35_months_prepared'] or preparation['observed_day_count']!=1059:
        raise ValueError('Incomplete approved SPASS preparation')
    proof_file=next((ROOT/'data_external/source_evidence').glob('IETF_ROBOTS_LONGEST_RULE_RFC9309_STAGE76_*.metadata.json'))
    proof=json.loads(proof_file.read_text(encoding='utf8'))
    if digest(proof['raw_file'])!=proof['sha256']:
        raise ValueError('Original protocol evidence changed')
    runtime_path=ROOT/'reports/snow_multiwinter_runtime_stage76_summary.json'
    runtime=json.loads(runtime_path.read_text(encoding='utf8')) if runtime_path.exists() else {'runs':[]}
    if runtime['runs'] and runtime['runs'][-1]['status']!='completed':
        raise ValueError('Wait for low-memory worker to complete')
    for r in runtime['runs']:
        if r['worker_sha256']!=digest('src/data_processing/compare_snow_multiwinter_stage76.py'):
            raise ValueError('Runtime used a different numerical producer')
    state=dict(checked_at=datetime.now(timezone.utc).isoformat(),parent_manifest=p,parent_sha256=digest(p),
               protected_reference_count=len(checks),protected_unique_file_count=len(hashes),registry_and_log_prefixes=prefix,
               old_results_and_originals_unchanged=True,completed_water_years=current['completed_water_years'],
               all_eight_winters_complete=current['all_eight_winters_complete'],current_comparison_sha256=current['output_sha256'],
               spass_prepared_months=35,spass_observed_prepared_days=1059,
               protocol_evidence_sha256=proof['sha256'],
               new_original_archives_verified=archives,current_robots_snapshots_verified=policies,
               low_memory_runs_verified=len(runtime['runs']),
               exact_daily_to_monthly_value_checks=daily_assembly_checks,
               current_producers={p:digest(p) for p in ['src/data_collection/collect_oshd_multiwinter_stage76.py',
               'src/data_processing/compare_snow_multiwinter_stage76.py','config/snow_multiwinter_decisions_stage76.json',
               'src/data_processing/run_snow_multiwinter_low_memory_stage76.py',
               'src/data_processing/sync_snow_multiwinter_dictionary_stage76.py',
               'src/data_processing/prepare_oshd_daily_reads_stage76.py']},
               checkpoint_not_final_until_all_eight=True)
    (ROOT/'reports/preservation_stage76_summary.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(state,ensure_ascii=False))


if __name__=='__main__':
    main()
