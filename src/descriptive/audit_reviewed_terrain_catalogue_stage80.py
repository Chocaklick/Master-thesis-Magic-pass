"""Reuse40 old catalogues and audit27new ones; metadata is not raster coverage."""
import json
import math
import sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from shapely import wkt
from shapely.geometry import box
from shapely.ops import unary_union
from pyproj import Transformer
from src.descriptive.audit_terrain_extension_stage65 import archive,parse_assets,ASSET_DEFS,GROUP_DEFS
from src.data_collection.collect_terrain_extension_stage65 import literal_next
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_REVIEWED_TERRAIN_CATALOGUE_STAGE80'
OUTPUTS=['data_processed/terrain_reviewed_asset_inventory_stage80.csv','data_processed/terrain_reviewed_catalogue_coverage_stage80.csv']
SUMMARY='reports/reviewed_terrain_catalogue_stage80_summary.json'


def main():
    paths=['config/terrain_group_catalogue_sources_stage80.json','data_interim/terrain_catalogue_events_stage80.json',
        'data_interim/terrain_catalogue_queue_stage80.json','data_interim/winter_profile_metric_network_stage80.json',
        'data_processed/winter_profile_metric_network_stage80.csv','data_processed/terrain_group_native2m_asset_inventory_stage65.csv',
        'data_processed/terrain_group_catalogue_coverage_stage65.csv','config/terrain_reference_tile_sources_stage66.json',
        'src/descriptive/audit_reviewed_terrain_catalogue_stage80.py','src/descriptive/audit_terrain_extension_stage65.py',
        'src/data_collection/collect_reviewed_terrain_catalogue_stage80.py','src/data_collection/collect_terrain_extension_stage65.py']
    inputs={p:sha(p) for p in paths}
    roots={s['station_group_id']:s for s in json.loads((ROOT/paths[0]).read_text(encoding='utf-8'))}
    networks={n['station_group_id']:n for n in json.loads((ROOT/paths[3]).read_text(encoding='utf-8'))}
    groups=pd.read_csv(ROOT/paths[4],float_precision='round_trip')
    old_assets=pd.read_csv(ROOT/paths[5],float_precision='round_trip');old_cov=pd.read_csv(ROOT/paths[6])
    cache={s['url']:s for s in json.loads((ROOT/paths[7]).read_text(encoding='utf-8'))}
    assets=[];coverage=[];metadata={};to_wgs=Transformer.from_crs(2056,4326,always_xy=True)
    from shapely.ops import transform
    for g in groups.itertuples():
        geomwkt=networks[g.station_group_id]['measured_unique_proxy_axis_wkt']
        base=dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.display_scope_name,
            group_retained=True,unique_mapped_axis_length_m=g.measured_unique_proxy_axis_length_m,
            actual_raster_coverage_verified=False)
        if geomwkt is None:
            coverage.append(base|dict(catalogue_status='missing_geometry_not_zero'));continue
        geometry=wkt.loads(geomwkt)
        if g.station_group_id not in roots:
            part=old_assets[old_assets.station_group_id.eq(g.station_group_id)].copy()
            previous=old_cov[old_cov.station_group_id.eq(g.station_group_id)]
            if len(previous)!=1 or part.empty:raise ValueError('Completed old catalogue absent')
            row=previous.iloc[0].to_dict()|base|dict(catalogue_status='complete_archived_catalogue_reused')
        else:
            root=roots[g.station_group_id];sid=root['source_id'];url=root['url'];pages=[];visited=set()
            for page in range(1,31):
                if url in visited:raise ValueError('Pagination loop')
                visited.add(url);meta,payload=archive(sid,inputs)
                if meta['url']!=url:raise ValueError('Archived literal URL differs')
                metadata[sid]=meta;pages.append((sid,payload));next_url=literal_next(payload)
                if next_url is None:break
                sid=root['source_id'].removesuffix('P001')+f'P{page+1:03}';url=next_url
            else:raise ValueError('Incomplete catalogue pagination')
            rawrows=[r for sid,payload in pages for r in parse_assets(payload,g.station_group_id,transform(to_wgs.transform,geometry),sid,cache)]
            part=pd.DataFrame(rawrows)
            if part.empty:raise ValueError('No2m assets for mapped group; needs explicit missing handling')
            if part.asset_id.duplicated().any():raise ValueError('Duplicate native asset')
            latest=part.groupby('native_tile_key').item_reference_datetime.max()
            part['latest_reference_for_native_tile']=part.item_reference_datetime.eq(part.native_tile_key.map(latest))
            if part[part.latest_reference_for_native_tile].native_tile_key.duplicated().any():raise ValueError('Latest tie needs review')
            chosen=part[part.latest_reference_for_native_tile];dates=sorted(chosen.loc[chosen.intersects_current_axis_footprint,'item_reference_datetime'].unique())
            row=base|dict(catalogue_status='complete_new_original_pages',archived_page_count=len(pages),
                catalogue_page_source_ids='|'.join(s for s,_ in pages),all_native2m_asset_count=len(part),
                latest_native_tile_count=len(chosen),latest_axis_intersecting_tile_count=int(chosen.intersects_current_axis_footprint.sum()),
                latest_axis_reference_dates='|'.join(dates),latest_axis_mixed_reference_dates=len(dates)>1)
        part['source_id']=SOURCE
        chosen=part[part.latest_reference_for_native_tile]
        footprints=[]
        for key in chosen.native_tile_key:
            east,north=(int(x)*1000 for x in key.split('-'));footprints.append(box(east,north,east+1000,north+1000))
        # Exact native catalogue tile squares, not rounded WGS84 page envelopes.
        observed=geometry.intersection(unary_union(footprints)).length
        row.update(catalogue_tile_footprint_axis_length_m=observed,
            catalogue_tile_footprint_axis_share=observed/geometry.length,
            catalogue_snapshot_reused=g.station_group_id not in roots,
            actual_nodata_or_neighbourhood_coverage_known=False)
        coverage.append(row);assets.extend(part.to_dict('records'))
    af=pd.DataFrame(assets).reindex(columns=ASSET_DEFS);gf=pd.DataFrame(coverage)
    if len(gf)!=69 or not gf.station_group_id.is_unique:raise ValueError('All groups retained')
    for url,p in af.groupby('asset_url'):
        if p.asset_sha256.nunique()!=1:raise ValueError('Conflicting official original checksum')
    frames=[af,gf];target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256']!=inputs or any(sha(p)!=h for p,h in state['output_sha256'].items()):raise ValueError('Frozen reviewed catalogue differs')
    else:
        for p,f in zip(OUTPUTS,frames):write_csv(f,ROOT/p)
        sel=af[af.latest_reference_for_native_tile]
        state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,
            output_sha256={p:sha(p) for p in OUTPUTS},all_group_count=69,new_catalogue_group_count=27,reused_catalogue_group_count=40,
            new_archived_page_count=len(metadata),latest_distinct_asset_count=sel.asset_url.nunique(),
            already_cached_latest_asset_count=sel.loc[sel.cached_original_tile_source_id.notna(),'asset_url'].nunique(),
            groups_with_incomplete_catalogue_footprint=gf.loc[gf.catalogue_tile_footprint_axis_share.lt(1-1e-12),['station_group_id','station_group_name','catalogue_tile_footprint_axis_share']].to_dict('records'),
            no_new_raster_values_or_profiles=True,source_attribution='Office fédéral de topographie swisstopo')
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False);records=[]
    for sid,m in metadata.items():
        records.append(dict(source_id=sid,variable_name='official_native2m_catalogue_metadata',variable_description=m['purpose'],
            source_organisation=m['organisation'],source_page_url=m['url'],retrieval_date=m['retrieval_date'],local_raw_file=m['raw_file'],
            processed_file='|'.join(OUTPUTS),geographic_level='Full original domain bbox, not municipal basin',
            temporal_resolution='Observed catalogue snapshot; all literal edition/creation/update dates retained',
            license='Official swisstopo OGD conditions/mandatory attribution',retrieval_method='Unchanged serial collector, actual HTTP/SHA/literal pagination',
            quality_notes='Metadata footprints not finite raster elevations; French gaps retained',notes='SHA='+m['sha256']))
    records.append(dict(source_id=SOURCE,variable_name='reviewed_geometry_terrain_catalogue_coverage',
        variable_description='69groups retained,40completed catalogues reused27new, native2m latest-per-tile availability and explicit footprint gaps',
        source_organisation='Thesis derived audit of swisstopo',retrieval_date='2026-10-12',processed_file='|'.join(OUTPUTS),
        geographic_level='Group and native metadata asset',temporal_resolution='Current qualified proxy; editions not preentry/acquisition certificate',
        license='Swisstopo OGD attribution; OSM ODbL',quality_notes='No raster/profile fit or group exclusion',notes=SUMMARY))
    fresh=[r for r in records if r['source_id'] not in set(master.source_id)]
    if fresh:write_csv(pd.concat([master,pd.DataFrame(fresh).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);add=[]
    defs=dict(GROUP_DEFS)|{
        'catalogue_tile_footprint_axis_length_m':('Measured proxy axislength inside native catalogue tile squares; not finite raster coverage','metres'),
        'catalogue_tile_footprint_axis_share':('Native tile footprint length/measured proxy network length; no selection threshold','fraction'),
        'catalogue_snapshot_reused':('True when completed old catalogue reused without new query','boolean'),
        'actual_nodata_or_neighbourhood_coverage_known':('False: native finite raster and nine-cell neighbourhood not read here','boolean')}
    defs['group_retained']=('True for all69approved derived groups','boolean')
    defs['unique_mapped_axis_length_m']=('Current measured proxy unique length after individually unresolved portions omitted from measurement, not original candidate length','metres')
    for path,frame,definitions in zip(OUTPUTS,frames,[ASSET_DEFS,defs]):
        for c in frame:
            if ((dictionary.table==Path(path).stem)&dictionary.variable.eq(c)).any():continue
            description,unit=definitions[c]
            add.append(dict(variable=c,table=Path(path).stem,description=description,unit=unit,data_type=str(frame[c].dtype),
                geographic_level='Group or native metadata asset',temporal_level='Literal catalogue snapshots and reference editions',source_id=SOURCE,
                raw_or_derived='metadata availability only',formula='audit_reviewed_terrain_catalogue_stage80.py; exact native tile footprint/no interpolation',
                causal_role='Source coverage, not final terrain profile or causal estimate',missing_share=f'{frame[c].isna().mean():.6f}',notes=SUMMARY))
    if add:write_csv(pd.concat([dictionary,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256']},ensure_ascii=False))


if __name__=='__main__':main()
