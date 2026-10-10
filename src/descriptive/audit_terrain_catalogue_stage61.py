"""Native2m pilot metadata inventory and approved terrain kernel checkpoint.

Retain all editions and catalogue entries. No raster download or vintage
selection, missing interpolation, profile fit or causal feature certification.
"""
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import rasterio
from shapely.geometry import LineString,shape
from shapely.ops import unary_union
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_TERRAIN_CATALOGUE_PILOT_STAGE61'
TABLE='terrain_stluc_native2m_asset_inventory_stage61'
OUTPUT=f'data_processed/{TABLE}.csv'
SUMMARY='reports/terrain_catalogue_stage61_summary.json'
DEFS={
 'source_id':('Registered derived inventory source','identifier'),
 'station_group_id':('Pilot group ID, no removal or prioritisation of other groups','identifier'),
 'item_id':('Literal provider STAC item ID; not piste identifier','identifier'),
 'item_reference_datetime':('Provider reference datetime; not independently verified acquisition date','timestamp'),
 'item_created_datetime':('Provider catalogue item created time','timestamp'),
 'item_updated_datetime':('Provider catalogue item updated time, not acquisition time','timestamp'),
 'asset_id':('Literal asset key, retained unchanged','identifier'),
 'asset_url':('Literal official asset href, not guessed download address','URL'),
 'asset_created_datetime':('Provider asset creation time','timestamp'),
 'asset_updated_datetime':('Provider asset update time','timestamp'),
 'asset_grid_resolution_m':('Explicit provider gsd, approved2m candidates only','metres'),
 'asset_horizontal_epsg':('Explicit provider projected EPSG,2056','EPSG code'),
 'asset_checksum_multihash':('Literal provider multihash, required for future file verification','checksum'),
 'asset_sha256':('Decoded SHA256 from supported multihash1220, not observed downloaded checksum','checksum'),
 'intersects_current_axis_footprint':('Current original lonlat axes intersect literal catalogue footprint, metadata pilot only','boolean'),
 'tile_vintage_selection_applied':('False: all observed editions retained, reference selection pending approval','boolean')}


def original(sid,inputs):
    metas=list((ROOT/'data_external/source_evidence').glob(sid+'_*.metadata.json'))
    if len(metas)!=1:raise ValueError('Require single archived original: '+sid)
    meta=json.loads(metas[0].read_text(encoding='utf8'))
    if sha(meta['raw_file'])!=meta['sha256']:raise ValueError('Original changed: '+sid)
    inputs[meta['raw_file']]=meta['sha256'];inputs[metas[0].relative_to(ROOT).as_posix()]=sha(metas[0].relative_to(ROOT).as_posix())
    return meta


def main():
    paths=['src/descriptive/audit_terrain_catalogue_stage61.py','src/data_processing/terrain_cell_weights_stage61.py',
       'config/terrain_extraction_decisions_stage61.json','config/terrain_catalogue_sources_stage61.json',
       'config/terrain_pilot_query_stage61.json','config/terrain_terms_sources_stage61.json',
       'config/terrain_runtime_requirements_stage61.txt','src/data_collection/prepare_terrain_pilot_query_stage61.py',
       'src/data_collection/collect_terrain_catalogue_stage61.py','tests/test_terrain_cells_stage61.py',
       'data_processed/winter_profile_piste_assignment_stage60.csv','reports/piste_terrain_sources_stage60_summary.json',
       'data_interim/terrain_catalogue_events_stage61.json']
    inputs={p:sha(p) for p in paths}
    parent=json.loads((ROOT/paths[11]).read_text(encoding='utf8'))
    for p,h in {**parent['input_sha256'],**parent['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Prior checkpoint changed: '+p)
    ids=['SWISSTOPO_ALTI3D_COLLECTION_STAGE61','SWISSTOPO_ALTI3D_STLUC_ITEMS_STAGE61','SWISSTOPO_FREE_GEODATA_TERMS_STAGE61']
    metas=[original(sid,inputs) for sid in ids]
    collection=json.loads((ROOT/metas[0]['raw_file']).read_bytes())
    payload=json.loads((ROOT/metas[1]['raw_file']).read_bytes())
    if any(l['rel']=='next' for l in payload.get('links',[])):raise ValueError('Incomplete pilot pagination; archive exact next links before inventory')
    soup=BeautifulSoup((ROOT/metas[2]['raw_file']).read_bytes(),'html.parser')
    for e in soup(['script','style']):e.decompose()
    text=' '.join(soup.get_text(' ',strip=True).split())
    if not all(s in text for s in ['A reference to the source is mandatory','may be enriched and processed','also used commercially']):raise ValueError('Terms content requires individual review')
    decision=json.loads((ROOT/paths[2]).read_text(encoding='utf8'))
    if decision['resolution_m']!=2 or decision['interpolate_missing_values']:raise ValueError('Require approved2m/nointerpolation')
    index,_,sites=originals()
    geometry=unary_union([LineString([(p['lon'],p['lat']) for p in index[('way',i)]['geometry']]) for i in sites[5976698]['selected_downhill_way_ids']])
    rows=[]
    for f in payload['features']:
        if f['collection']!='ch.swisstopo.swissalti3d':raise ValueError('Wrong collection')
        for aid,a in f['assets'].items():
            if not a.get('type','').startswith('image/tiff') or a.get('gsd')!=2.0 or a.get('proj:epsg')!=2056:continue
            checksum=a.get('file:checksum','')
            if not checksum.lower().startswith('1220') or len(checksum)!=68:raise ValueError('Require supported provider SHA256 multihash')
            rows.append(dict(source_id=SOURCE,station_group_id='MP_GROUP_RESORT__st_luc_chandolin',item_id=f['id'],
                item_reference_datetime=f['properties'].get('datetime'),item_created_datetime=f['properties'].get('created'),item_updated_datetime=f['properties'].get('updated'),asset_id=aid,asset_url=a['href'],asset_created_datetime=a.get('created'),asset_updated_datetime=a.get('updated'),asset_grid_resolution_m=a['gsd'],asset_horizontal_epsg=a['proj:epsg'],asset_checksum_multihash=checksum,asset_sha256=checksum[4:].lower(),intersects_current_axis_footprint=shape(f['geometry']).intersects(geometry),tile_vintage_selection_applied=False))
    frame=pd.DataFrame(rows)
    if len(frame)!=len(payload['features']) or frame.asset_url.duplicated().any():raise ValueError('Require one distinct native2m TIFF per observed item')
    state=dict(date='2026-10-10',input_sha256=inputs,pilot_group_id='MP_GROUP_RESORT__st_luc_chandolin',all_group_count_retained=70,
       catalogue_item_count=len(payload['features']),native2m_asset_count=len(frame),reference_datetimes=sorted(frame.item_reference_datetime.unique()),
       footprint_intersection_asset_count=int(frame.intersects_current_axis_footprint.sum()),
       catalogue_license_literal=collection['license'],terms_individually_verified=True,required_attribution='Office fédéral de topographie swisstopo',
       catalogue_license_not_relabelled=True,all_editions_retained=True,no_raster_download_or_vintage_selection=True,
       no_terrain_or_snow_feature_or_effect_fit=True,approved_horn_native_cell_kernel_prepared=True,
       runtime_versions=dict(python=sys.version.split()[0],numpy=np.__version__,rasterio=rasterio.__version__,gdal=rasterio.__gdal_version__),
       source_metadata=metas,metadata_datetime_not_assumed_actual_acquisition=True)
    target=ROOT/SUMMARY
    if target.exists():
        old=json.loads(target.read_text(encoding='utf8'))
        if old['input_sha256']!=inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):raise ValueError('Frozen own inventory changed')
    else:
        write_csv(frame,ROOT/OUTPUT);state['output_sha256']={OUTPUT:sha(OUTPUT)}
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    records=[]
    for meta in metas:
        records.append(dict(source_id=meta['source_id'],variable_name='terrain_catalogue_or_terms_evidence',variable_description=meta['purpose'],source_organisation=meta['organisation'],source_page_url=meta['url'],retrieval_date=meta['retrieval_date'],original_file_name=Path(meta['raw_file']).name,local_raw_file=meta['raw_file'],processed_file=SUMMARY,retrieval_method='Finite public GET, official items/terms links, robots/TLS/SHA verified',geographic_level='Official DEM metadata or OGD conditions',temporal_resolution='Current catalogue and terms; not terrain acquisition date',license='Literal collection proprietary retained; official OGD terms separately verified; source attribution mandatory',transformation_applied='Native2m asset metadata retained; no raster values/download or vintage choice',quality_notes='Catalogue/creation/update dates not substituted for actual acquisition; pilot not group exclusion',notes='SHA256='+meta['sha256']))
    records.append(dict(source_id=SOURCE,variable_name='native2m_terrain_asset_pilot_inventory',variable_description='All84native2m current footprint-box metadata assets, both observed editions retained, no vintage selection',source_organisation='Thesis audit of swisstopo metadata',retrieval_date='2026-10-10',processed_file=OUTPUT,geographic_level='Bounded StLuc metadata pilot; all70groups retained',temporal_resolution='Literal edition reference and asset update dates',license='Official OGD conditions/attribution; literal proprietary catalogue marker retained',retrieval_method='Offline original catalogue and items/terms with SHA',transformation_applied='Filter asset format/resolution/CRS only per approved2m terrain; footprint intersection diagnostic and exact checksums retained',quality_notes='No raster/profile/causal feature inferred; reference vintage awaits researcher choice',notes='Original/source lineage and approved kernel versions in '+SUMMARY))
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    records=[r for r in records if r['source_id'] not in set(master.source_id)]
    if records:write_csv(pd.concat([master,pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);records=[]
    if set(frame)!=set(DEFS):raise ValueError('Every field defined')
    for col,(description,unit) in DEFS.items():
        if ((dictionary.table==TABLE)&(dictionary.variable==col)).any():continue
        records.append(dict(variable=col,table=TABLE,description=description,unit=unit,data_type=str(frame[col].dtype),source_id=SOURCE,geographic_level='pilot candidate asset',temporal_level='literal provider metadata',raw_or_derived='retained metadata/availability diagnostic',formula='Official native2m TIFF metadata; no terrain feature extraction',causal_role='source audit only; not preentry feature',missing_share=f'{frame[col].isna().mean():.6f}',notes='No vintage choice, interpolation or group exclusion; all observed editions retained'))
    if records:write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','source_metadata']},ensure_ascii=False))


if __name__=='__main__':main()
