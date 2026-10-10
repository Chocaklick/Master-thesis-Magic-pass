"""Prepare approved SPASS cell values while OSHD transfer is incomplete.

No group mean, feature, imputation, model substitution or source conversion.
Use exactly the future comparison worker's cache contracts, no duplicate reads.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.compare_snow_multiwinter_stage76 import read_selected, winter_dates, CONFIG
from src.data_processing.prepare_native_snow_weights_stage69 import digest


def main():
    decisions=json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['collection_water_years']!=list(range(2016,2023)):
        raise ValueError('Approved seven additional winters required')
    spass=json.loads((ROOT/'reports/snow_grid_metadata_compatibility_stage47.json').read_text(encoding='utf8'))
    parent=json.loads((ROOT/'reports/native_snow_weights_stage69_summary.json').read_text(encoding='utf8'))
    path='data_processed/native_snow_cell_pairs_stage69.csv'
    if digest(path)!=parent['output_sha256'][path] or digest(spass['spass_raw_file'])!=spass['spass_netcdf_sha256']:
        raise ValueError('Original source or approved grid support changed')
    f=pd.read_csv(ROOT/path,float_precision='round_trip')
    indices=f[['spass_e_index','spass_n_index']].drop_duplicates().sort_values(['spass_e_index','spass_n_index']).to_numpy(dtype=int)
    output=ROOT/'reports/spass_multiwinter_cache_preparation_stage76_summary.json'
    state=dict(date='2026-10-10',source_sha256=spass['spass_netcdf_sha256'],native_indices=325,
               approved_paired_weight_file_sha256=parent['output_sha256'][path],
               source_unit_unchanged='UNKNOWN',group_profiles_computed=False,source_spliced_or_calibrated=False,months={})
    for year in decisions['collection_water_years']:
        dates=[str(d.date()) for d in winter_dates(year)]
        for month in sorted({d[:7] for d in dates}):
            _,meta=read_selected(spass['spass_raw_file'],spass['spass_netcdf_sha256'],indices,
                                [d for d in dates if d.startswith(month)],'HSCLQMD',('time','N','E'),('E','N'),
                                parent['original_grid_axes']['spass'],'spass_'+month)
            state['months'][month]=dict(observed_days=len(meta['observed_dates']),missing_days=len(meta['missing_dates']),
                                       cache_sha256=meta['sha256'],source_unit=meta['source_unit'])
            output.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    state.update(complete_months=len(state['months']),all35_months_prepared=len(state['months'])==35,
                 observed_day_count=sum(m['observed_days'] for m in state['months'].values()))
    output.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in state.items() if k!='months'}),flush=True)


if __name__=='__main__':
    main()
