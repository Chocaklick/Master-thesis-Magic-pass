"""Approved exact native snow weights and civil-date pairing; no snow values.

The actual native grids are nested/aligned. Split the unchanged unique axes
once on their common refinement; never upsample/interpolate snow. Retain
native source indices and distinct northing orders. No group is excluded.
"""
import hashlib
from datetime import timedelta
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date
from shapely import wkt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_NATIVE_SNOW_WEIGHTS_STAGE69'
SUMMARY = 'reports/native_snow_weights_stage69_summary.json'
CONFIG = 'config/snow_comparison_decisions_stage69.json'
OSHD = 'reports/oshd_netcdf_metadata_inventory.json'
SPASS = 'reports/snow_grid_metadata_compatibility_stage47.json'
GROUPS = 'data_processed/terrain_reference_profiles_stage67.csv'
NETWORK = 'data_interim/winter_profile_exact_network_stage63.json'
TABLES = ['native_snow_cell_pairs_stage69', 'native_snow_weight_coverage_stage69', 'native_snow_date_pairs_stage69']
OUTPUTS = ['data_processed/'+x+'.csv' for x in TABLES]
DEFS = [
    {
        'source_id': ('Derived geometric weights/date pairing source', 'identifier'),
        'station_group_id': ('Preserved group identifier, not municipality or independent snow cell', 'identifier'),
        'spass_e_index': ('Original east-axis index in SPASS; outside indices kept with flag', 'index'),
        'spass_n_index': ('Original ascending north-axis index in SPASS', 'index'),
        'oshd_e_index': ('Original east-axis index in OSHD', 'index'),
        'oshd_n_index': ('Original descending north-axis index in OSHD', 'index'),
        'spass_cell_in_grid': ('Both source indices inside original SPASS array, not snow value availability', 'boolean'),
        'oshd_cell_in_grid': ('Both source indices inside original OSHD array, not snow value availability', 'boolean'),
        'spass_cell_centre_east_2056': ('Original native SPASS east-coordinate when inside grid', 'metres'),
        'spass_cell_centre_north_2056': ('Original native SPASS north-coordinate when inside grid', 'metres'),
        'oshd_cell_centre_east_2056': ('Original native OSHD east-coordinate when inside grid', 'metres'),
        'oshd_cell_centre_north_2056': ('Original native OSHD north-coordinate when inside grid', 'metres'),
        'unique_axis_length_m': ('Exact unchanged axislength in shared SPASS/OSHD native cell footprint, counted once per group', 'metres'),
    },
    {
        'source_id': ('Derived geometric weights/date pairing source', 'identifier'),
        'station_group_id': ('Retained station-group ID, one row each', 'identifier'),
        'station_group_name': ('Preserved group name', 'text'),
        'group_retained': ('True for all70groups', 'boolean'),
        'weight_status': ('Prepared native footprints or retained missing axes/scope', 'text'),
        'unique_mapped_axis_length_m': ('Unchanged original unique candidate-axis length', 'metres'),
        'cell_pair_count': ('Number of native shared footprints with positive axislength', 'count'),
        'spass_native_cell_count': ('Distinct SPASS indices carrying axes, not independent resorts', 'count'),
        'oshd_native_cell_count': ('Distinct OSHD indices carrying axes, not independent resorts', 'count'),
        'both_native_grid_length_m': ('Length inside both native array extents, not valid snow-value coverage', 'metres'),
        'outside_either_native_grid_length_m': ('Retained axislength outside at least one source array', 'metres'),
        'both_native_grid_length_share': ('Inside-both-grid length divided by all unique candidate-axis length', 'fraction'),
        'snow_values_read': ('False: this preparation reads coordinate/time axes only', 'boolean'),
        'current_proxy_not_verified_preentry': ('Current candidate geometry is not an exhaustive/preentry-certified piste domain', 'boolean'),
    },
    {
        'source_id': ('Derived geometric weights/date pairing source', 'identifier'),
        'spass_civil_date': ('Reference SPASS calendar date within fixed pilotDecemberApril', 'date'),
        'spass_original_timestamp': ('Original decoded timestamp, no timezone conversion invented', 'timestamp'),
        'spass_time_index': ('Original index in SPASS time coordinate', 'index'),
        'spass_time_coordinate_value': ('Original numeric source time-coordinate value', 'source time units'),
        'spass_time_units': ('Literal original source time units', 'text'),
        'oshd_date_offset_days': ('OSHD civil date minus SPASS civil date; zero reference, plus/minusone sensitivity', 'days'),
        'oshd_civil_date': ('Original OSHD date corresponding to approved offset', 'date'),
        'oshd_original_timestamp': ('Original decoded OSHD timestamp and raw units retained, not claimed simultaneous', 'timestamp'),
        'oshd_source_id': ('Registered original OSHD annual archive', 'identifier'),
        'oshd_member_file': ('Checksum-verified extracted original monthly member in interim', 'relative file path'),
        'oshd_time_index': ('Original monthly time-axis index', 'index'),
        'oshd_time_coordinate_value': ('Original numeric monthly time coordinate', 'source time units'),
        'oshd_time_units': ('Literal original OSHD monthly units including stated time offset', 'text'),
        'both_calendar_dates_available': ('Both date coordinates found, not finite snowfield values', 'boolean'),
    },
]


def digest(path):
    h = hashlib.sha256()
    with (ROOT/path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def coordinates(path, xname, yname):
    with ascii_link(ROOT/path) as link, Dataset(link) as d:
        return np.asarray(d.variables[xname][:],dtype=float),np.asarray(d.variables[yname][:],dtype=float)


def native_grid(east,north):
    if len(east)<2 or len(north)<2 or not np.isfinite(east).all() or not np.isfinite(north).all():
        raise ValueError('Complete finite native coordinate axes required')
    dx,dy=np.diff(east),np.diff(north)
    if not (dx==dx[0]).all() or not (dy==dy[0]).all() or dx[0]<=0 or dy[0]==0 or abs(dx[0])!=abs(dy[0]):
        raise ValueError('Nonregular native grids require a new explicit footprint rule')
    step=float(dx[0])
    return dict(left=float(east[0]-step/2),top=float(max(north)+step/2),step=step,
                east_count=len(east),north_count=len(north),north_ascending=bool(dy[0]>0))


def index_at(east,north,grid):
    col=math.floor((east-grid['left'])/grid['step'])
    row=math.floor((grid['top']-north)/grid['step'])
    n=grid['north_count']-1-row if grid['north_ascending'] else row
    inside=0<=col<grid['east_count'] and 0<=n<grid['north_count']
    return col,n,inside


def ensure_nested(coarse,fine):
    ratio=coarse['step']/fine['step']
    if ratio!=int(ratio) or ratio<1 or (coarse['left']-fine['left'])%fine['step'] or (coarse['top']-fine['top'])%fine['step']:
        raise ValueError('Native grid boundaries not nested; do not snap/interpolate')


def main():
    paths=[CONFIG,OSHD,SPASS,GROUPS,NETWORK,'src/data_processing/prepare_native_snow_weights_stage69.py',
           'src/data_processing/terrain_cell_weights_stage61.py','src/descriptive/inspect_oshd_netcdf_metadata.py',
           'reports/snow_comparison_readiness_stage68_summary.json']
    inputs={p:digest(p) for p in paths}
    decisions=json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    if decisions['spatial_rule']!='exact_unique_axis_length_native_grids_common_observed_support' or decisions['interpolation'] or decisions['new_unit_conversion']:
        raise ValueError('Only explicitly approved native/common-support policy')
    prior=json.loads((ROOT/'reports/snow_comparison_readiness_stage68_summary.json').read_text(encoding='utf8'))
    for p,h in {**prior['input_sha256'],**prior['output_sha256']}.items():
        if digest(p)!=h:
            raise ValueError('Frozen input changed: '+p)
    spass=json.loads((ROOT/SPASS).read_text(encoding='utf8'))
    spath=spass['spass_raw_file']
    if digest(spath)!=spass['spass_netcdf_sha256']:
        raise ValueError('Original SPASS bytes changed')
    inputs[spath]=spass['spass_netcdf_sha256']
    inventory=json.loads((ROOT/OSHD).read_text(encoding='utf8'))
    se,sn=coordinates(spath,'E','N')
    monthly_dates={}
    oe,on=None,None
    for sid,archive in inventory['archives'].items():
        if archive['water_year']!=2023:
            continue
        for m in archive['members']:
            p=m['extracted_file']
            if digest(p)!=m['sha256']:
                raise ValueError('Original extracted monthly member changed: '+p)
            inputs[p]=m['sha256']
            xe,yn=coordinates(p,'easting','northing')
            if oe is None:
                oe,on=xe,yn
            if not np.array_equal(xe,oe) or not np.array_equal(yn,on):
                raise ValueError('Original monthly native coordinate axes differ')
            with ascii_link(ROOT/p) as link,Dataset(link) as d:
                var=d.variables['time']; raw=np.asarray(var[:],dtype=float);units=var.units
                decoded=num2date(raw,units,calendar=getattr(var,'calendar','standard'))
                for i,(t,num) in enumerate(zip(decoded,raw)):
                    date=pd.Timestamp(str(t)).normalize()
                    if date in monthly_dates:
                        raise ValueError('Duplicated original OSHD date')
                    monthly_dates[date]=dict(oshd_original_timestamp=str(t),oshd_source_id=sid,oshd_member_file=p,
                        oshd_time_index=i,oshd_time_coordinate_value=float(num),oshd_time_units=units)
    sg,og=native_grid(se,sn),native_grid(oe,on)
    ensure_nested(sg,og)
    if sg['step']!=1000 or og['step']!=250:
        raise ValueError('Unexpected observed source resolutions')
    groups=pd.read_csv(ROOT/GROUPS,float_precision='round_trip')
    networks={r['station_group_id']:r for r in json.loads((ROOT/NETWORK).read_text(encoding='utf8'))}
    pairs,coverage=[],[]
    for g in groups.itertuples():
        base=dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.station_group_name,group_retained=True,
                  unique_mapped_axis_length_m=g.unique_mapped_axis_length_m,snow_values_read=False,current_proxy_not_verified_preentry=True)
        text=networks[g.station_group_id]['exact_unique_axis_wkt']
        if not text:
            coverage.append({**base,'weight_status':g.terrain_status})
            continue
        geometry=wkt.loads(text)
        weights=cell_lengths(geometry,og['left'],og['top'],og['step'],og['step'])
        part=[]
        for (r,c),length in sorted(weights.items()):
            x,y=og['left']+(c+.5)*og['step'],og['top']-(r+.5)*og['step']
            ec,nc,si=index_at(x,y,sg)
            ei,ni,oi=index_at(x,y,og)
            part.append(dict(source_id=SOURCE,station_group_id=g.station_group_id,spass_e_index=ec,spass_n_index=nc,oshd_e_index=ei,oshd_n_index=ni,
                spass_cell_in_grid=si,oshd_cell_in_grid=oi,spass_cell_centre_east_2056=float(se[ec]) if si else None,
                spass_cell_centre_north_2056=float(sn[nc]) if si else None,oshd_cell_centre_east_2056=float(oe[ei]) if oi else None,
                oshd_cell_centre_north_2056=float(on[ni]) if oi else None,unique_axis_length_m=length))
        total=math.fsum(r['unique_axis_length_m'] for r in part)
        if not math.isclose(total,g.unique_mapped_axis_length_m,rel_tol=1e-12):
            raise ValueError('Exact geometry length changed')
        observed=math.fsum(r['unique_axis_length_m'] for r in part if r['spass_cell_in_grid'] and r['oshd_cell_in_grid'])
        outside=math.fsum(r['unique_axis_length_m'] for r in part if not(r['spass_cell_in_grid'] and r['oshd_cell_in_grid']))
        coverage.append({**base,'weight_status':'native_weights_prepared_not_snow_coverage','cell_pair_count':len(part),
            'spass_native_cell_count':len({(r['spass_e_index'],r['spass_n_index']) for r in part}),
            'oshd_native_cell_count':len({(r['oshd_e_index'],r['oshd_n_index']) for r in part}),
            'both_native_grid_length_m':observed,'outside_either_native_grid_length_m':outside,'both_native_grid_length_share':observed/total})
        pairs.extend(part)
    with ascii_link(ROOT/spath) as link,Dataset(link) as d:
        var=d.variables['time'];raw=np.asarray(var[:],dtype=float);units=var.units
        decoded=num2date(raw,units,calendar=getattr(var,'calendar','standard'))
        spdates={pd.Timestamp(str(t)).normalize():(i,str(t),float(num)) for i,(t,num) in enumerate(zip(decoded,raw))}
        if len(spdates)!=len(raw):
            raise ValueError('Duplicated SPASS date')
    dates=[]
    for date in pd.date_range(decisions['pilot_start'],decisions['pilot_end']):
        i,t,num=spdates[date]
        for offset in decisions['sensitivity_oshd_date_offsets_days']:
            od=date+timedelta(days=int(offset))
            record=dict(source_id=SOURCE,spass_civil_date=str(date.date()),spass_original_timestamp=t,spass_time_index=i,
                spass_time_coordinate_value=num,spass_time_units=units,oshd_date_offset_days=offset,oshd_civil_date=str(od.date()),
                both_calendar_dates_available=od in monthly_dates)
            record.update(monthly_dates.get(od,{}))
            dates.append(record)
    frames=[pd.DataFrame(rows).reindex(columns=defs) for rows,defs in zip((pairs,coverage,dates),DEFS)]
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf8'))
        if state['input_sha256']!=inputs or any(digest(p)!=h for p,h in state['output_sha256'].items()):
            raise ValueError('Frozen native weights differ; use a new stage')
    else:
        if len(master)!=1198 or len(dictionary)!=8104:
            raise ValueError('Unexpected registry baseline before append')
        for f,p in zip(frames,OUTPUTS):
            write_csv(f,ROOT/p)
        state=dict(date='2026-10-10',input_sha256=inputs,output_sha256={p:digest(p) for p in OUTPUTS},
            prior_registry_rows_and_digest={p:dict(rows=len(f),sha256=row_digest(f)) for p,f in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]},
            retained_groups=len(groups),mapped_axis_groups=int(frames[1].cell_pair_count.notna().sum()),cell_pair_rows=len(frames[0]),date_pair_rows=len(frames[2]),
            exact_axis_length_m=float(frames[1].unique_mapped_axis_length_m.sum()),outside_native_grid_length_m=float(frames[1].outside_either_native_grid_length_m.sum()),
            original_grid_axes=dict(spass=sg,oshd=og),native_boundaries_verified_nested=True,snow_values_read=False,
            new_unit_conversion_or_splice=False,decisions=decisions)
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    if SOURCE not in set(master.source_id):
        record=dict(source_id=SOURCE,variable_name='exact_native_snow_weights_and_date_pairs',variable_description='Native1km/250m shared piste footprints and approvedcivil dates plus/minusoneday; no dependent snow values',
            source_organisation='Thesis derived analysis of SLF/OSM',retrieval_date='2026-10-10',processed_file='|'.join(OUTPUTS),geographic_level='Retained stationgroups/nativefootprints, not municipality',
            temporal_resolution='Currentqualifiedaxes;December2022April2023civilcalendar with originaltimes preserved',license='ParentSPASS/OSHDterms;OSM ODbL',
            retrieval_method='FrozenoriginalSHA,actualcoordinate/timeaxes;no request',transformation_applied='Exactsharednativegrid refinement length;sourceindices/nativeaxisorders;datepairing approvedin'+CONFIG,
            quality_notes='Geometry/calendaravailability is not observed snowcoverage;unitSPASSUNKNOWN;no interpolation/groupfilter/calibration/splice orfit',notes=SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
    records=[]
    for table,f,defs in zip(TABLES,frames,DEFS):
        for col,(description,unit) in defs.items():
            if ((dictionary.table==table)&(dictionary.variable==col)).any():
                continue
            records.append(dict(variable=col,table=table,description=description,unit=unit,data_type=str(f[col].dtype),geographic_level='Stationgroup/nativefootprint orcalendar, not independentcells',
                temporal_level='Qualifiedcurrentgeometry/pilotcivil dates, notfiveownpreentrymean',source_id=SOURCE,raw_or_derived='derived',formula=description,
                causal_role='Approvedgeometricweight/timepairingprovenance;notcausal snowfeature',missing_share=f'{f[col].isna().mean():.6f}',notes='No snowvalues read;originalunits retained;no missing-to-zero/exclusion/interpolation'))
    if records:
        write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ('input_sha256','output_sha256','prior_registry_rows_and_digest')},ensure_ascii=False))


if __name__=='__main__':
    main()
