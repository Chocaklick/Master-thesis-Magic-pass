"""Approved exact native2m terrain for reviewed69groups, preserving old cells."""
import argparse
from datetime import datetime,timezone
from functools import lru_cache
import json
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import numpy as np
import pandas as pd
import rasterio
from shapely import wkt
from src.descriptive.audit_native2m_reference_stage66 import CELL_DEFS as PREVIOUS_CELL_DEFS,neighbourhood
from src.descriptive.summarise_terrain_reference_stage67 import DEFS as OLD_DEFS
from src.descriptive.summarise_terrain_orientation_stage64 import summarise_cells
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS
from src.data_collection.collect_oshd_multiwinter_stage76 import single_collector_lock

SOURCE='DERIVED_REVIEWED_NATIVE2M_PROFILES_STAGE82'
OUTPUT='data_processed/terrain_reviewed_profiles_stage82.csv'
SUMMARY='reports/terrain_reviewed_profiles_stage82_summary.json'
CACHE=ROOT/'data_interim/terrain_reviewed_cells_stage82'
QUEUE='config/terrain_reviewed_tile_sources_stage81.json'
CELL_DEFS=dict(PREVIOUS_CELL_DEFS)|{
    'horn_calculation_status':('Computed same-edition or missing native neighbours/mixed-edition gradient under the approved rule','category'),
    'terrain_slope_degrees':('Strict Horn on nine finite same-edition cells only; mixed-edition neighbourhood remains missing','degrees'),
    'terrain_aspect_degrees':('Observed downslope angle; undefined on exactly flat, unobserved or mixed-edition terrain','degrees'),
    'gradient_observed':('Finite approved Horn gradient, not a pending method decision','boolean'),
}
DEFS=dict(OLD_DEFS)|{
    'group_retained':('True for all69approvedgroups, no missing-data exclusion','boolean'),
    'unique_mapped_axis_length_m':('Measured reviewed unique proxy length; not full mapped candidate or complete real domain','metres'),
    'full_candidate_axis_length_m':('All original candidate unique mapped length, not certified official piste kilometres','metres'),
    'measured_share_of_mapped_candidate_length':('Reviewed measurable length/full mapped candidate length, ambiguous portions kept','fraction'),
    'altitude_coverage_of_full_candidate_share':('Finite altitude length/full mapped candidate length, geometry ambiguity and DEM gaps both visible','fraction'),
    'gradient_coverage_of_full_candidate_share':('Observed Horn gradient length/full mapped candidate length','fraction'),
    'cache_mode':('New exact extraction or reuse of geometrically identical original source-cell cache','category'),
    'terrain_status':('Observed qualified current profile with full/partial coverage or explicit missing geometry','category'),
    'mixed_edition_complete_neighbourhood_length_m':('Nine finite source values of different editions: altitude retained, slope/aspect missing by approved rule','metres'),
}


def make_record(base,cells):
    f=cells;observed=f.altitude_observed;complete=f.horn_complete_native_neighbourhood;grad=f.gradient_observed
    length=lambda mask:math.fsum(f.loc[mask,'unique_axis_length_m'])
    total=math.fsum(f.unique_axis_length_m)
    if not math.isclose(total,base['unique_mapped_axis_length_m'],rel_tol=1e-12):raise ValueError('Preserved measured proxy length differs')
    mixed=complete&f.mixed_reference_neighbourhood
    if f.loc[mixed,'gradient_observed'].any():raise ValueError('No approved mixed-edition gradient')
    stats=summarise_cells(f);stats.pop('unique_mapped_axis_length_m')
    dates=sorted(f.centre_reference_datetime.dropna().unique())
    r=base|stats|dict(native_axis_cell_count=len(f),reference_datetimes_on_axis='|'.join(dates),
        observed_altitude_length_m=length(observed),missing_altitude_length_m=length(~observed),
        complete_native_neighbourhood_length_m=length(complete),missing_native_neighbourhood_length_m=length(~complete),
        mixed_edition_complete_neighbourhood_length_m=length(mixed),mixed_edition_axis_share=length(mixed)/total,
        minimum_observed_altitude_m=float(f.loc[observed,'altitude_m'].min()) if observed.any() else None,
        maximum_observed_altitude_m=float(f.loc[observed,'altitude_m'].max()) if observed.any() else None,
        length_weighted_observed_altitude_m=float(np.average(f.loc[observed,'altitude_m'],weights=f.loc[observed,'unique_axis_length_m'])) if observed.any() else None,
        observed_gradient_length_m=length(grad),gradient_coverage_share=length(grad)/total,
        length_weighted_observed_slope_degrees=float(np.average(f.loc[grad,'terrain_slope_degrees'],weights=f.loc[grad,'unique_axis_length_m'])) if grad.any() else None,
        altitude_coverage_of_full_candidate_share=length(observed)/base['full_candidate_axis_length_m'],
        gradient_coverage_of_full_candidate_share=length(grad)/base['full_candidate_axis_length_m'],
        terrain_status='observed_partial_source_or_gradient_coverage' if (~observed).any() or (~grad).any() else 'observed_current_proxy')
    if not math.isclose(r['missing_gradient_length_m'],r['missing_native_neighbourhood_length_m']+r['mixed_edition_complete_neighbourhood_length_m'],abs_tol=1e-8):raise ValueError('Gradient missing causes do not reconcile')
    return r


def register(frame,metadata):
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False);records=[]
    for sid,m in metadata.items():
        if sid in set(master.source_id):continue
        records.append(dict(source_id=sid,variable_name='native_swiss2m_terrain',variable_description=m['purpose'],
            source_organisation=m['organisation'],source_page_url=m['url'],direct_download_url=m['url'],
            retrieval_date=m['retrieval_date'],local_raw_file=m['raw_file'],processed_file=OUTPUT+'|data_interim/terrain_reviewed_cells_stage82',
            geographic_level='Verified Swiss native1km tile',temporal_resolution='Literal source edition; not assumed acquisition or preentry date',
            temporal_start=m['item_reference_datetime'],unit='native2m raster; altitude metre; EPSG2056/verticalEPSG5728',
            license='swisstopo OGD with attribution Office fédéral de topographie swisstopo',
            retrieval_method='Serial actual GET, archived response/SHA matched to official STAC, exact header validation',
            transformation_applied='Original preserved; exact native-cell lengths/Horn, no interpolation/resampling/source combination',
            quality_notes='Current qualified terrain, not certified historical operating piste; French complement cancelled',notes='SHA='+m['sha256']))
    if SOURCE not in set(master.source_id):
        records.append(dict(source_id=SOURCE,variable_name='reviewed_native2m_group_profiles',variable_description='69retainedgroups,67measurable networks, exact native source profiles with missingness/ambiguity published',
            source_organisation='Thesis from swisstopo and reviewed current OSM axes',retrieval_date='2026-10-12',processed_file=OUTPUT,
            geographic_level='Station group, not overnight municipality',temporal_resolution='Current proxy, literal editions, not verified preentry terrain',
            license='swisstopo OGD attribution; OSM ODbL',
            transformation_applied='Exact source-cell lengths, strict Horn on9finite same-edition cells; mixed-edition gradients missing; observed-length summaries',
            quality_notes='No group exclusion/model fit/dominant orientation; unresolved axes unmeasured; Swiss-only partial Dôle',notes=SUMMARY))
    if records:write_csv(pd.concat([master,pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);add=[]
    for table,f,defs in [(Path(OUTPUT).stem,frame,DEFS),('terrain_reviewed_cells_stage82',None,CELL_DEFS)]:
        for c,(desc,unit) in defs.items():
            if ((dictionary.table==table)&dictionary.variable.eq(c)).any():continue
            role='Continuous candidate, current proxy historical caveat' if c in ['terrain_northness','terrain_eastness'] else 'Description only, not automatically fitted' if c in ['orientation_resultant_concentration','north_length_share','east_length_share','south_length_share','west_length_share'] else 'Qualified profile/provenance/coverage, not an estimated effect'
            add.append(dict(variable=c,table=table,description=desc,unit=unit,data_type=str(f[c].dtype) if f is not None else 'nullable original or derived native-cell field',
                geographic_level='Retained group/native source cell, not independent resort observation',temporal_level='Current reviewed geometry and literal DEM editions',
                source_id=SOURCE,raw_or_derived='derived',formula=desc,causal_role=role,
                missing_share=f'{f[c].isna().mean():.6f}' if f is not None else '',notes='Approved Horn/no missing interpolation/no French complement; current proxy caveat'))
    if add:write_csv(pd.concat([dictionary,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def run(no_register):
    paths=['src/data_processing/build_reviewed_terrain_profiles_stage82.py',QUEUE,'reports/reviewed_terrain_queue_stage81_summary.json',
        'data_interim/winter_profile_metric_network_stage80.json','data_processed/winter_profile_metric_network_stage80.csv',
        'config/terrain_seam_decision_stage67.json','config/terrain_extraction_decisions_stage61.json',
        'config/terrain_orientation_decisions_stage64.json','config/terrain_french_complement_decision_stage80.json',
        'src/data_processing/terrain_cell_weights_stage61.py','src/descriptive/audit_native2m_reference_stage66.py',
        'src/descriptive/summarise_terrain_orientation_stage64.py','data_interim/winter_profile_exact_network_stage63.json',
        'data_processed/terrain_native2m_reference_audit_stage66.csv','reports/native2m_reference_stage66_summary.json',
        'data_processed/station_group_parent_bridge_stage79.csv']
    inputs={p:sha(p) for p in paths}
    if json.loads((ROOT/paths[5]).read_text())['mixed_edition_complete_neighbourhood']!='retain_altitude_and_length_leave_gradient_missing':raise ValueError('Approved seam convention required')
    queue=json.loads((ROOT/QUEUE).read_text());by_source={};lookup={};metadata={};headers=[]
    for s in queue:
        paths_meta=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if len(paths_meta)!=1:raise ValueError('Finish exact finite raster collection first '+s['source_id'])
        p=paths_meta[0];m=json.loads(p.read_text());metadata[s['source_id']]=m
        if m['url']!=s['url'] or m['sha256']!=s['expected_sha256'] or sha(m['raw_file'])!=m['sha256']:raise ValueError('Original/official SHA differs')
        inputs[m['raw_file']]=m['sha256'];inputs[p.relative_to(ROOT).as_posix()]=sha(p.relative_to(ROOT))
        with rasterio.open(ROOT/m['raw_file']) as d:
            e,n=(int(x)*1000 for x in s['native_tile_key'].split('-'))
            if d.crs.to_epsg()!=2056 or d.res!=(2.,2.) or d.transform.b!=0 or d.transform.d!=0 or d.count!=1 or d.units!=('metre',) or d.shape!=(500,500) or tuple(d.bounds)!=(e,n,e+1000,n+1000):raise ValueError('Require literal aligned northupnative2mmetre headers')
            tile=s|dict(raw_file=m['raw_file'],left=d.bounds.left,top=d.bounds.top,nodata=d.nodata)
            lookup[(e,n)]=tile;by_source[s['source_id']]=tile
            headers.append(dict(source_id=s['source_id'],raw_file=m['raw_file'],shape=list(d.shape),bounds=list(d.bounds),resolution=list(d.res),units=list(d.units),crs=str(d.crs),nodata=d.nodata,reference_datetime=s['item_reference_datetime'],size_bytes=m['size_bytes']))
    @lru_cache(maxsize=48)
    def array(sid):
        with rasterio.open(ROOT/by_source[sid]['raw_file']) as d:a=d.read(1).astype(float)
        nodata=by_source[sid]['nodata']
        if nodata is not None:a[a==nodata]=np.nan
        return a
    def value(sid,r,c):return float(array(sid)[r,c])
    groups=pd.read_csv(ROOT/paths[4],float_precision='round_trip')
    networks={n['station_group_id']:n for n in json.loads((ROOT/paths[3]).read_text())}
    oldnet={n['station_group_id']:n for n in json.loads((ROOT/paths[12]).read_text())}
    oldgroups=pd.read_csv(ROOT/paths[13],float_precision='round_trip').set_index('station_group_id')
    parent=json.loads((ROOT/paths[14]).read_text())
    recipe=__import__('hashlib').sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()
    bridge=pd.read_csv(ROOT/paths[15]);rows=[];outputs={};reused=[]
    for g in groups.itertuples():
        base=dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.display_scope_name,group_retained=True,
            current_proxy_not_verified_preentry=True,unique_mapped_axis_length_m=g.measured_unique_proxy_axis_length_m,
            full_candidate_axis_length_m=g.full_unique_candidate_axis_length_m,measured_share_of_mapped_candidate_length=g.measured_share_of_mapped_candidate_length,
            parent_station_group_ids='|'.join(sorted(bridge.loc[bridge.station_group_id.eq(g.station_group_id),'parent_station_group_id'])),
            seam_policy='missing_gradient_at_mixed_edition_only')
        geomtext=networks[g.station_group_id]['measured_unique_proxy_axis_wkt']
        if geomtext is None:rows.append(base|dict(terrain_status='missing_geometry_not_zero'));continue
        geometry=wkt.loads(geomtext);token=__import__('hashlib').sha256(g.station_group_id.encode()).hexdigest()[:12]
        cell_file=CACHE/(token+'.csv');checkpoint=cell_file.with_suffix('.json')
        ccontract=dict(recipe_sha256=recipe,network_sha256=sha(paths[3]),queue_sha256=sha(QUEUE))
        if checkpoint.exists():
            previous=json.loads(checkpoint.read_text())
            if previous['contract']!=ccontract or sha(cell_file.relative_to(ROOT))!=previous['sha256']:raise ValueError('Frozen group-cell cache differs')
            cells=pd.read_csv(cell_file,float_precision='round_trip',low_memory=False);mode=previous['cache_mode']
            inputs.update(previous['parent_cell_inputs'])
            for p,h in previous['parent_cell_inputs'].items():
                if sha(p)!=h:raise ValueError('Reused parent cells changed')
        else:
            if cell_file.exists():raise ValueError('Uncheckpointed cell file retained')
            old=oldnet.get(g.station_group_id,{}).get('exact_unique_axis_wkt');parent_inputs={}
            if old and geometry.equals_exact(wkt.loads(old),0) and g.station_group_id in oldgroups.index and pd.notna(oldgroups.loc[g.station_group_id,'cell_detail_file']):
                oldfile=oldgroups.loc[g.station_group_id,'cell_detail_file'];h=sha(oldfile)
                if h!=parent['output_sha256'][oldfile]:raise ValueError('Frozen original cells changed')
                cells=pd.read_csv(ROOT/oldfile,float_precision='round_trip',low_memory=False)
                used={s for text in cells.horn_neighbour_source_ids.dropna() for s in text.split('|') if s}
                if not used<=set(by_source):raise ValueError('Old identical network has different literal native sources')
                parent_inputs[oldfile]=h;inputs[oldfile]=h;mode='reuse_exact_original_network_source_cells';reused.append(g.station_group_id)
                cells['source_id']=SOURCE
                cells.loc[cells.horn_calculation_status.eq('awaiting_mixed_edition_rule'),'horn_calculation_status']='missing_mixed_edition_approved'
            else:
                weights=cell_lengths(geometry,0,0,2,2);records=[];mode='new_exact_native_extraction'
                for (r,c),length in weights.items():
                    east,north=2*c+1,-2*r-1
                    z,sids,dates,mixed,status,slope,aspect=neighbourhood(east,north,lookup,value)
                    if status=='awaiting_mixed_edition_rule':status='missing_mixed_edition_approved'
                    tile=lookup.get((math.floor(east/1000)*1000,math.floor(north/1000)*1000));altitude=float(z[1,1]) if np.isfinite(z[1,1]) else None
                    records.append(dict(source_id=SOURCE,station_group_id=g.station_group_id,cell_centre_east_2056=east,cell_centre_north_2056=north,
                        unique_axis_length_m=length,altitude_m=altitude,altitude_observed=altitude is not None,
                        centre_tile_source_id=tile['source_id'] if tile else None,centre_reference_datetime=tile['item_reference_datetime'] if tile else None,
                        horn_neighbour_source_ids='|'.join(sids),horn_neighbour_reference_dates='|'.join(dates),native_neighbour_values_observed_count=int(np.isfinite(z).sum()),
                        horn_complete_native_neighbourhood=bool(np.isfinite(z).all()),mixed_reference_neighbourhood=mixed,horn_calculation_status=status,
                        terrain_slope_degrees=slope,terrain_aspect_degrees=aspect,gradient_observed=slope is not None,flat_terrain=slope==0 if slope is not None else None))
                cells=pd.DataFrame(records).reindex(columns=CELL_DEFS)
            write_csv(cells,cell_file)
            checkpoint.write_text(json.dumps(dict(contract=ccontract,sha256=sha(cell_file.relative_to(ROOT)),cache_mode=mode,parent_cell_inputs=parent_inputs),indent=2)+'\n',encoding='utf-8')
        if mode.startswith('reuse') and g.station_group_id not in reused:reused.append(g.station_group_id)
        rows.append(make_record(base|dict(cell_detail_file=cell_file.relative_to(ROOT).as_posix(),cache_mode=mode),cells))
        outputs[cell_file.relative_to(ROOT).as_posix()]=sha(cell_file.relative_to(ROOT));outputs[checkpoint.relative_to(ROOT).as_posix()]=sha(checkpoint.relative_to(ROOT))
        (CACHE/'progress.json').write_text(json.dumps(dict(completed_groups=[r['station_group_id'] for r in rows],total_groups=len(groups)),indent=2)+'\n',encoding='utf-8')
        print(g.display_scope_name,mode,rows[-1]['terrain_status'],flush=True)
    inputs['data_processed/station_group_parent_bridge_stage79.csv']=sha('data_processed/station_group_parent_bridge_stage79.csv')
    frame=pd.DataFrame(rows).reindex(columns=DEFS)
    if len(frame)!=69 or not frame.station_group_id.is_unique:raise ValueError('All69groups retained once')
    state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,header_checks=headers,
        group_count=len(frame),groups_with_observed_altitudes=int(frame.observed_altitude_length_m.gt(0).sum()),
        reused_exact_original_cell_groups=reused,new_extraction_group_count=int(frame.cache_mode.eq('new_exact_native_extraction').sum()),
        terrain_status_counts=frame.terrain_status.value_counts().to_dict(),original_native_tiles_verified=len(queue),
        no_french_raster_or_missing_interpolation=True,no_group_exclusion_or_model_fit=True,
        partial_source_groups=frame.loc[frame.missing_altitude_length_m.gt(0),['station_group_id','station_group_name','observed_altitude_length_m','missing_altitude_length_m']].to_dict('records'))
    target=ROOT/SUMMARY
    if target.exists():
        previous=json.loads(target.read_text())
        if previous['input_sha256']!=inputs or any(sha(p)!=h for p,h in previous['output_sha256'].items()):raise ValueError('Frozen terrain extension differs')
    else:
        write_csv(frame,ROOT/OUTPUT);state['output_sha256']=outputs|{OUTPUT:sha(OUTPUT)}
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not no_register:register(frame,metadata)
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','header_checks','reused_exact_original_cell_groups']},ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--no-register',action='store_true');args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True)
    with single_collector_lock(CACHE):run(args.no_register)
