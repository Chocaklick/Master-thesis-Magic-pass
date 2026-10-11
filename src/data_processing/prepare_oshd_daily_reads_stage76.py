"""Exact old cell reader, one civil day at a time, then monthly cache assembly.

No aggregation, interpolation, changed precision, masks or scientific producer.
Daily checkpoints survive interruption; old monthly caches are only verified.
"""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[name]='1'
import argparse
import copy
import json
import sys
import zipfile
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd
netCDF4.set_chunk_cache(1048576,101,0.75)
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import src.data_processing.compare_snow_multiwinter_stage76 as worker
from src.data_collection.collect_oshd_multiwinter_stage76 import single_collector_lock
from src.descriptive.inspect_oshd_netcdf_metadata import extract_member
from src.data_processing.prepare_native_snow_weights_stage69 import digest


def monthly_from_daily(source,sha,indices,dates,variable,dims,names,grid,key):
    folder=worker.CACHE/'values'
    sidecar=folder/(key+'.json'); npz=folder/(key+'.npz')
    args=(source,sha,indices,dates,variable,dims,names,grid,key)
    if sidecar.exists():
        return worker.read_selected(*args)
    if npz.exists():
        raise ValueError('Uncheckpointed monthly cache retained for review')
    observed=[]; values=[]; coordinates={}; daily_proofs=[]; first=None
    for day in dates:
        day_key=key+'_bounded_'+day
        selected,m=worker.read_selected(source,sha,indices,[day],variable,dims,names,grid,day_key)
        if first is None:
            first=copy.deepcopy(m)
        for field in ['source_unit','original_time_units','calendar']:
            if m[field]!=first[field]:
                raise ValueError('Changed source declaration between exact daily reads')
        if day in selected:
            observed.append(day); values.append(selected[day])
            coordinates[day]=m['original_date_coordinates'][day]
        daily_proofs.append(dict(key=day_key,sha256=m['sha256']))
    if first is None:
        raise ValueError('At least one requested date required')
    first['contract']['requested_dates']=dates
    first.update(observed_dates=observed,missing_dates=[d for d in dates if d not in observed],
        original_date_coordinates=coordinates,
        exact_daily_assembly=dict(producer='src/data_processing/prepare_oshd_daily_reads_stage76.py',
            producer_sha256=digest('src/data_processing/prepare_oshd_daily_reads_stage76.py'),
            unchanged_reader_sha256=digest('src/data_processing/compare_snow_multiwinter_stage76.py'),
            daily_checkpoints=daily_proofs,interpolation_or_precision_change=False))
    array=np.stack(values) if values else np.empty((0,len(indices)))
    np.savez_compressed(npz,values=array)
    first['sha256']=digest(npz.relative_to(ROOT))
    with sidecar.open('x',encoding='utf8') as stream:
        json.dump(first,stream,ensure_ascii=False,indent=2)
    print('Exact daily-assembled month',key,len(observed),'observed days',flush=True)
    return worker.read_selected(*args)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only-water-year',type=int,choices=list(range(2016,2023)))
    args=parser.parse_args()
    parent=json.loads((ROOT/'reports/native_snow_weights_stage69_summary.json').read_text(encoding='utf8'))
    path='data_processed/native_snow_cell_pairs_stage69.csv'
    if digest(path)!=parent['output_sha256'][path]:
        raise ValueError('Approved piste support changed')
    pairs=pd.read_csv(ROOT/path,float_precision='round_trip')
    indices=pairs[['oshd_e_index','oshd_n_index']].drop_duplicates().sort_values(['oshd_e_index','oshd_n_index']).to_numpy(dtype=int)
    collection=json.loads((ROOT/worker.COLLECTION).read_text(encoding='utf8'))
    folder=worker.CACHE/'calculation_lock'; folder.mkdir(parents=True,exist_ok=True)
    with single_collector_lock(folder):
        for archive in collection['files']:
            year=archive['water_year']
            if archive['status']!='complete' or args.only_water_year is not None and args.only_water_year!=year:
                continue
            if (worker.CACHE/f'daily_WY{year}.json').exists():
                continue
            if digest(archive['raw_file'])!=archive['sha256']:
                raise ValueError('Original annual archive changed')
            dates=worker.winter_dates(year)
            requested=[str(d.date()) for d in pd.date_range(dates[0]-pd.Timedelta(days=1),dates[-1]+pd.Timedelta(days=1))]
            members=worker.CACHE/'members'/f'WY{year}'; members.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(ROOT/archive['raw_file']) as z:
                if len(z.namelist())!=len(set(z.namelist())):
                    raise ValueError('Duplicate ZIP names')
                for month in sorted({d[:7] for d in requested}):
                    name=f'OSHD_DATA_{month}.nc'
                    if name not in z.namelist():
                        continue  # Worker records absence, never invent a file.
                    target,record=extract_member(z,z.getinfo(name),members)
                    monthly_from_daily(target.relative_to(ROOT).as_posix(),record['sha256'],indices,
                        [d for d in requested if d.startswith(month)],'hs',('easting','northing','time'),
                        ('easting','northing'),parent['original_grid_axes']['oshd'],'oshd_'+month)


if __name__=='__main__':
    main()
