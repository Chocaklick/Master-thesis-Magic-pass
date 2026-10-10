"""Resumable approved winter comparisons; no source mixing or effect estimate.

Completed annual archives only. Reuse 2022/23 pilot, extract only necessary
monthly members in new interim folders, preserve native axes/date/value masks.
No publication as complete until all eight winters are actually computed.
"""
import argparse
import json
import math
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest, native_grid, SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.data_processing.extract_native_snow_values_stage70 import finite_values, support_metrics
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link, extract_member, metadata
from src.descriptive.diagnose_native_snow_metrics_stage75 import paired_metrics
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

SOURCE = 'DERIVED_SNOW_MULTIWINTER_COMPARISON_STAGE76'
CONFIG = 'config/snow_multiwinter_decisions_stage76.json'
COLLECTION = 'reports/oshd_multiwinter_collection_stage76_summary.json'
CACHE = ROOT/'data_interim/snow_multiwinter_stage76'
OUTPUT = 'data_processed/snow_multiwinter_comparison_stage76.csv'
SUMMARY = 'reports/snow_multiwinter_comparison_stage76_summary.json'
DEFS = {
    'source_id':('Derived eight-winter comparison ID', 'identifier'),
    'station_group_id':('Retained stable group ID, not commune', 'identifier'),
    'station_group_name':('Preserved name, not sole key', 'text'),
    'group_retained':('True for all70groups, even absent geometry or source', 'boolean'),
    'water_year':('OSHD archive year: September previous year to August this year', 'year'),
    'winter':('December previous year through April this year, diagnostic not own-preentry substitution', 'text'),
    'oshd_date_offset_days':('Fixed-1/0/+1 sensitivity, zero reference, no optimised lag', 'days'),
    'reference_offset':('True for fixed same civil date reference', 'boolean'),
    'status':('Computed/missing geometry/archive pending, never an invented zero', 'text'),
    'requested_days':('Actual calendar days December1-April30, including leap day', 'count'),
    'finite_paired_days':('Observed days with finite means on common native support', 'count'),
    'missing_pair_days':('Requested calendar days minus actually paired days, missing if not calculated', 'count'),
    'spass_winter_mean_m':('Equal-day mean of paired daily SPASS length-weighted means, m assumed', 'metres, assumed'),
    'oshd_winter_mean_m':('Same paired days/native support, OSHD documented m', 'metres'),
    'mean_oshd_minus_spass_m':('OSHD winter mean minus SPASS winter mean on same observed days', 'metres, assumption-dependent'),
    'daily_mean_absolute_difference_m':('Within-winter mean abs(OSHD-SPASS), not abs(winter means) or truth error', 'metres, assumption-dependent'),
    'daily_root_mean_square_difference_m':('Within-winter sqrt mean squared daily model differences', 'metres, assumption-dependent'),
    'min_common_observed_length_share':('Minimum observed common length share over requested days', 'fraction'),
    'mean_common_observed_length_share':('Equal-day common length share over requested days', 'fraction'),
    'spass_negative_value_days':('Observed common support containing negative source values, flagged not removed', 'count'),
    'oshd_negative_value_days':('Observed common support containing negative source values, flagged not removed', 'count'),
    'spass_original_unit':('Original declaration remains UNKNOWN, not retroactively certified', 'text'),
    'spass_metres_assumed':('Explicit researcher-approved metre interpretation factor1', 'boolean'),
    'oshd_unit':('Literal original hs.unit=m', 'text'),
    'source_spliced_or_calibrated':('False, diagnostic only', 'boolean'),
    'current_proxy_not_verified_preentry':('True: current piste geometry retains historical uncertainty', 'boolean'),
}


def winter_dates(year):
    return pd.date_range(f'{year-1}-12-01', f'{year}-04-30')


def aggregate_daily(f, requested):
    if f.spass_civil_date.duplicated().any():
        raise ValueError('Duplicated reference date would reweight winter')
    r = paired_metrics(f.spass_mean_common_raw.to_numpy(), f.oshd_mean_common_m.to_numpy())
    n = r['finite_paired_days']
    return dict(finite_paired_days=n, missing_pair_days=requested-n,
                spass_winter_mean_m=r.get('spass_paired_mean_m'), oshd_winter_mean_m=r.get('oshd_paired_mean_m'),
                mean_oshd_minus_spass_m=r.get('mean_oshd_minus_spass_m'),
                daily_mean_absolute_difference_m=r.get('mean_absolute_difference_m'),
                daily_root_mean_square_difference_m=r.get('root_mean_square_difference_m'),
                min_common_observed_length_share=float(f.common_observed_length_share.min()),
                mean_common_observed_length_share=float(f.common_observed_length_share.mean()),
                spass_negative_value_days=int(f.spass_negative_common_length_m.gt(0).sum()),
                oshd_negative_value_days=int(f.oshd_negative_common_length_m.gt(0).sum()),
                status='computed_complete_pairs' if n==requested else 'computed_partial_pairs' if n else 'no_finite_pairs')


def read_selected(source, sha, indices, dates, variable, dims, names, expected_grid, key):
    folder = CACHE/'values'; folder.mkdir(parents=True, exist_ok=True)
    npz, sidecar = folder/(key+'.npz'), folder/(key+'.json')
    contract = dict(source_file=source, source_sha256=sha, indices=indices.tolist(), requested_dates=dates,
                    variable=variable, dimensions=list(dims), producer_sha256=digest('src/data_processing/compare_snow_multiwinter_stage76.py'))
    if sidecar.exists():
        m = json.loads(sidecar.read_text(encoding='utf8'))
        if m['contract'] != contract or digest(npz.relative_to(ROOT)) != m['sha256']:
            raise ValueError('Frozen value checkpoint changed: '+key)
        with np.load(npz, allow_pickle=False) as x:
            return {d:v for d,v in zip(m['observed_dates'], x['values'])}, m
    with ascii_link(ROOT/source) as link, Dataset(link) as ds:
        east, north = [np.asarray(ds.variables[name][:], dtype=float) for name in names]
        if native_grid(east, north) != expected_grid:
            raise ValueError('Changed native grid needs review, no snapping: '+source)
        time = ds.variables['time']; raw = np.asarray(time[:], dtype=float)
        units, calendar = time.units, getattr(time, 'calendar', 'standard')
        decoded = num2date(raw, units, calendar=calendar)
        calendar_map = {str(t)[:10]:(i,str(t),float(value)) for i,(t,value) in enumerate(zip(decoded, raw))}
        if len(calendar_map) != len(raw):
            raise ValueError('Duplicate source civil date')
        observed = [d for d in dates if d in calendar_map]
        v = ds.variables[variable]
        unit = getattr(v, 'units', getattr(v, 'unit', 'UNKNOWN'))
        if v.dimensions != dims or unit != ('UNKNOWN' if variable=='HSCLQMD' else 'm'):
            raise ValueError('Source dimensions/unit changed')
        if not observed:
            values = np.empty((0, len(indices)))
        else:
            # Small date/month blocks; pair after reading, never orthogonal fancy indexing.
            ts = np.array([calendar_map[d][0] for d in observed]); t0,t1=int(ts.min()),int(ts.max())
            x0,n0=indices.min(axis=0); x1,n1=indices.max(axis=0)
            if dims==('time','N','E'):
                block=finite_values(v[t0:t1+1,n0:n1+1,x0:x1+1])
                values=block[:,indices[:,1]-n0,indices[:,0]-x0][ts-t0,:]
            else:
                block=finite_values(v[x0:x1+1,n0:n1+1,t0:t1+1])
                values=block[indices[:,0]-x0,indices[:,1]-n0,:][:,ts-t0].T
            del block
        m=dict(contract=contract, source_unit=unit, original_time_units=units, calendar=calendar,
               observed_dates=observed, missing_dates=[d for d in dates if d not in calendar_map],
               original_date_coordinates={d:calendar_map[d] for d in observed}, source_masks_applied=True)
    if npz.exists():
        raise ValueError('Uncheckpointed value file retained; inspect before retry')
    np.savez_compressed(npz, values=values)
    m['sha256']=digest(npz.relative_to(ROOT))
    sidecar.write_text(json.dumps(m, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print('Value cache', key, len(observed), 'observed days', flush=True)
    return dict(zip(observed, values)), m


def compute_year(year, archive, pairs, spass, grids):
    dates = winter_dates(year)
    source_dates = [str(d.date()) for d in dates]
    target_dates = [str(d.date()) for d in pd.date_range(dates[0]-pd.Timedelta(days=1), dates[-1]+pd.Timedelta(days=1))]
    se=pairs[['spass_e_index','spass_n_index']].drop_duplicates().sort_values(['spass_e_index','spass_n_index']).to_numpy(dtype=int)
    oe=pairs[['oshd_e_index','oshd_n_index']].drop_duplicates().sort_values(['oshd_e_index','oshd_n_index']).to_numpy(dtype=int)
    svalues, ovalues, checkpoints = {}, {}, {}
    # Verify originals once per new winter before making caches, never download them again.
    if digest(spass['spass_raw_file']) != spass['spass_netcdf_sha256'] or digest(archive['raw_file']) != archive['sha256']:
        raise ValueError('Original archive or SPASS changed')
    for month in sorted({d[:7] for d in source_dates}):
        values, meta=read_selected(spass['spass_raw_file'], spass['spass_netcdf_sha256'], se,
                                  [d for d in source_dates if d.startswith(month)], 'HSCLQMD', ('time','N','E'), ('E','N'), grids['spass'], 'spass_'+month)
        svalues.update(values); checkpoints['spass_'+month]=meta
    folder=CACHE/'members'/f'WY{year}'; folder.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ROOT/archive['raw_file']) as z:
        if len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Duplicate original ZIP names')
        for month in sorted({d[:7] for d in target_dates}):
            name=f'OSHD_DATA_{month}.nc'
            if name not in z.namelist():
                checkpoints['missing_member_'+month]=dict(member_name=name, absent=True); continue
            target, record=extract_member(z,z.getinfo(name),folder)
            values, meta=read_selected(target.relative_to(ROOT).as_posix(), record['sha256'], oe,
                                      [d for d in target_dates if d.startswith(month)], 'hs', ('easting','northing','time'),
                                      ('easting','northing'), grids['oshd'], 'oshd_'+month)
            ovalues.update(values); checkpoints['oshd_'+month]=dict(**meta, extraction=record)
    sloc={tuple(v):i for i,v in enumerate(se)}; oloc={tuple(v):i for i,v in enumerate(oe)}
    records=[]
    for gid, f in pairs.groupby('station_group_id', sort=False):
        si=[sloc[t] for t in f[['spass_e_index','spass_n_index']].itertuples(index=False, name=None)]
        oi=[oloc[t] for t in f[['oshd_e_index','oshd_n_index']].itertuples(index=False, name=None)]
        lengths=f.unique_axis_length_m.to_numpy()
        for lag in [-1,0,1]:
            for d in dates:
                sd,od=str(d.date()),str((d+pd.Timedelta(days=lag)).date())
                a=svalues.get(sd, np.full(len(se),np.nan))[si]
                b=ovalues.get(od, np.full(len(oe),np.nan))[oi]
                records.append(dict(station_group_id=gid,spass_civil_date=sd,oshd_civil_date=od,oshd_date_offset_days=lag,
                                    **support_metrics(a,b,lengths)))
    return pd.DataFrame(records), checkpoints


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-register', action='store_true', help='Avoid shared registry writes while collector is active')
    args=parser.parse_args()
    CACHE.mkdir(exist_ok=True)
    decisions=json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['diagnostic_water_years']!=list(range(2016,2024)) or decisions['date_offsets_days']!=[-1,0,1] or decisions['source_splicing_or_calibration']:
        raise ValueError('Approved fixed eight winters required')
    pairs=pd.read_csv(ROOT/'data_processed/native_snow_cell_pairs_stage69.csv', float_precision='round_trip')
    groups=pd.read_csv(ROOT/'data_processed/native_snow_weight_coverage_stage69.csv', float_precision='round_trip')
    frozen=json.loads((ROOT/'reports/native_snow_weights_stage69_summary.json').read_text(encoding='utf8'))
    for path in ['data_processed/native_snow_cell_pairs_stage69.csv','data_processed/native_snow_weight_coverage_stage69.csv']:
        if digest(path)!=frozen['output_sha256'][path]:
            raise ValueError('Approved spatial support changed')
    collection=json.loads((ROOT/COLLECTION).read_text(encoding='utf8'))
    completed={f['water_year']:f for f in collection['files'] if f['status']=='complete'}
    spass=json.loads((ROOT/'reports/snow_grid_metadata_compatibility_stage47.json').read_text(encoding='utf8'))
    contract={p:digest(p) for p in [CONFIG,'data_processed/native_snow_cell_pairs_stage69.csv',
                                  'src/data_processing/compare_snow_multiwinter_stage76.py']}
    output_rows=[]; years_done=[]; year_checkpoints={}
    for year in decisions['diagnostic_water_years']:
        requested=len(winter_dates(year)); path=CACHE/f'daily_WY{year}.csv'; sidecar=path.with_suffix('.json')
        daily=None
        if sidecar.exists():
            m=json.loads(sidecar.read_text(encoding='utf8'))
            if m['contract']!=contract or digest(path.relative_to(ROOT))!=m['sha256']:
                raise ValueError('Frozen annual checkpoint changed')
            daily=pd.read_csv(path,float_precision='round_trip'); year_checkpoints[str(year)]=m
        elif year==2023:
            source='data_processed/native_snow_daily_common_support_stage70.csv'
            parent=json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
            if digest(source)!=parent['output_sha256'][source]:
                raise ValueError('Preserved pilot changed')
            daily=pd.read_csv(ROOT/source,float_precision='round_trip')
            checkpoints=dict(reused_stage70_file=source, sha256=digest(source))
        elif year in completed:
            daily,checkpoints=compute_year(year,completed[year],pairs,spass,frozen['original_grid_axes'])
        if daily is not None and not sidecar.exists():
            write_csv(daily,path)
            m=dict(contract=contract,sha256=digest(path.relative_to(ROOT)),source_checkpoints=checkpoints,
                   archive_identity={k:completed[year][k] for k in ['source_id','raw_file','sha256','expected_md5','expected_bytes']} if year in completed else 'reused frozen Stage70 pilot')
            sidecar.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf8'); year_checkpoints[str(year)]=m
        if daily is not None:
            years_done.append(year)
        for g in groups.itertuples():
            for lag in [-1,0,1]:
                r=dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.station_group_name,
                       group_retained=True,water_year=year,winter=f'{year-1}/{str(year)[-2:]}',oshd_date_offset_days=lag,reference_offset=lag==0,
                       requested_days=requested,spass_original_unit='UNKNOWN',spass_metres_assumed=True,oshd_unit='m',
                       source_spliced_or_calibrated=False,current_proxy_not_verified_preentry=True)
                if pd.isna(g.cell_pair_count):
                    r['status']='no_usable_geometry__'+g.weight_status
                elif daily is None:
                    r['status']='archive_not_yet_complete'
                else:
                    f=daily[daily.station_group_id.eq(g.station_group_id)&daily.oshd_date_offset_days.eq(lag)]
                    if len(f)!=requested or set(f.spass_civil_date)!=set(str(d.date()) for d in winter_dates(year)):
                        raise ValueError('Incomplete/duplicated annual source table')
                    r.update(aggregate_daily(f,requested))
                output_rows.append(r)
    result=pd.DataFrame(output_rows).reindex(columns=DEFS)
    # This table is an explicit evolving checkpoint, not a falsely frozen complete result.
    write_csv(result,ROOT/OUTPUT)
    state=dict(date='2026-10-10',decisions=decisions,input_sha256=contract,output_sha256={OUTPUT:digest(OUTPUT)},
               completed_water_years=years_done,all_eight_winters_complete=len(years_done)==8,
               retained_groups=groups.station_group_id.nunique(),rows=len(result),year_checkpoints=year_checkpoints,
               source_spliced_or_calibrated=False,five_own_preentry_winters_unchanged=True)
    (ROOT/SUMMARY).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if not args.no_register:
        master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
        if SOURCE not in set(master.source_id):
            new=dict(source_id=SOURCE,variable_name='native_piste_weighted_snow_common_winter_comparison',
                     variable_description='Approved eight December-April windows, same common observed support and dates, SPASS assumed m; explicit partial collection statuses',
                     source_organisation='Thesis derived SPASS/OSHD',source_dataset_name='Stage76 eight-winter comparison',
                     source_page_url='reports/121_EXTENSION_COMPARAISON_NEIGE_HUIT_HIVERS_FR.md',processed_file=OUTPUT,
                     retrieval_method='Checksum-verified sources/caches; exact native lengths and paired days',retrieval_date='2026-10-10',
                     temporal_start='2015-12-01',temporal_end='2023-04-30',temporal_resolution='group winter fixedlag',
                     unit='m; SPASS researcher-approved assumption',license='Parent SPASS WSL Data Policy; OSHD CC-BY4; OSM ODbL',
                     transformation_applied='Length-weight daily means on common finite source portions, equal-day winter paired means, no interpolation/splice',
                     quality_notes='Current pistes/historical uncertainty; all70groups retained; archive pending distinct from no snow',notes=SUMMARY)
            write_csv(pd.concat([master,pd.DataFrame([new]).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
        dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
        additions=[]
        for col,(description,unit) in DEFS.items():
            if not ((dictionary.table=='snow_multiwinter_comparison_stage76')&dictionary.variable.eq(col)).any():
                additions.append(dict(variable=col,table='snow_multiwinter_comparison_stage76',description=description,unit=unit,
                                      data_type=str(result[col].dtype),source_id=SOURCE,raw_or_derived='derived',formula=description,
                                      geographic_level='retained station group',temporal_level='diagnostic winter/lag, not final five-preentry feature',
                                      causal_role='model-comparison diagnostic only',missing_share=f'{result[col].isna().mean():.6f}',notes=CONFIG))
        if additions:
            write_csv(pd.concat([dictionary,pd.DataFrame(additions).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ['decisions','input_sha256','output_sha256','year_checkpoints']}),flush=True)


if __name__=='__main__':
    main()
