"""Registration only after workers finish; scientific producers remain frozen."""
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.data_processing import build_reviewed_terrain_profiles_stage82 as terrain
from src.data_processing import build_reviewed_spass_profiles_stage83 as snow
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def main():
    hashes={}
    for p in [terrain.SUMMARY,snow.SUMMARY]:
        m=json.loads((ROOT/p).read_text(encoding='utf-8'))
        for path,h in m['input_sha256'].items()|m['output_sha256'].items():
            if path in hashes and hashes[path]!=h:raise ValueError('Conflicting frozen input '+path)
            hashes[path]=h
        for v in m.get('daily_checkpoints',{}).values():hashes[v['path']]=v['sha256'];hashes[v['metadata']]=v['metadata_sha256']
    for path,h in hashes.items():
        if sha(path)!=h:raise ValueError('Frozen producer/input/result changed '+path)
    metadata={}
    for s in json.loads((ROOT/terrain.QUEUE).read_text(encoding='utf-8')):
        paths=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if len(paths)!=1:raise ValueError('One actual original sidecar required')
        metadata[s['source_id']]=json.loads(paths[0].read_text(encoding='utf-8'))
    terrain.register(pd.read_csv(ROOT/terrain.OUTPUT,float_precision='round_trip'),metadata)
    snow.register([pd.read_csv(ROOT/p,float_precision='round_trip') for p in snow.OUTPUTS])
    state=dict(completed_at=datetime.now(timezone.utc).isoformat(),verified_unique_files=len(hashes),
        registration_script_sha256=sha('src/data_processing/register_reviewed_profiles_stage83.py'),
        numerical_producers_and_results_unchanged=True,no_new_request_or_recomputation=True,
        registry_rows={p:len(pd.read_csv(ROOT/p)) for p in ['metadata/data_sources_master.csv','metadata/data_dictionary.csv','logs/data_collection_log.csv']})
    path=ROOT/'reports/reviewed_profile_registry_stage83_summary.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old['registration_script_sha256']!=state['registration_script_sha256']:raise ValueError('Registration helper changed')
    else:path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state,ensure_ascii=False))


if __name__=='__main__':main()
