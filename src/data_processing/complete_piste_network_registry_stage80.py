"""Registration-only repair; preserve frozen numerical producer and outputs.

The first Stage80 run wrote/checkpointed valid outputs, then stopped because one
definition was absent. Supply that understood definition without rerunning the
geometry or silently changing its frozen code/input SHA.
"""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.data_processing import build_reviewed_piste_network_stage80 as producer
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def main():
    state=json.loads((ROOT/producer.SUMMARY).read_text(encoding='utf-8'))
    for p,h in {**state['input_sha256'],**state['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Frozen Stage80 changed: '+p)
    producer.EXTRA_DEFS['current_proxy_not_verified_preentry']=(
        'True: current mapped geometry remains a qualified proxy, not a verified preentry operating footprint','boolean')
    frames=[pd.read_csv(ROOT/p,float_precision='round_trip') for p in producer.OUTPUTS]
    docs=[]
    for s in json.loads((ROOT/'config/piste_metric_sources_stage80.json').read_text(encoding='utf-8')):
        metas=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if len(metas)!=1:raise ValueError('Require original semantic evidence')
        docs.append(json.loads(metas[0].read_text(encoding='utf-8')))
    producer.register(frames,docs)
    proof=dict(completed_at=producer.datetime.now(producer.timezone.utc).isoformat(),
        producer_summary=producer.SUMMARY,producer_summary_sha256=sha(producer.SUMMARY),
        registration_script_sha256=sha('src/data_processing/complete_piste_network_registry_stage80.py'),
        output_sha256=state['output_sha256'], numerical_producer_and_results_unchanged=True,
        missing_definition_supplied='current_proxy_not_verified_preentry',
        no_geometry_recomputation_or_source_request=True)
    (ROOT/'reports/piste_network_registry_stage80_summary.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','groups_with_unmeasured_portions']},ensure_ascii=False))


if __name__=='__main__':main()
