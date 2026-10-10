"""Current mapped-candidate terrain pilot, not final preentry station profiles.

Approved unique geometry/native2m cell lengths/Horn/no interpolation. Both
observed editions retained. Every original tile checked against providerSHA.
"""
import json,math,sys
from pathlib import Path
from contextlib import ExitStack
import numpy as np
import pandas as pd
import rasterio
from rasterio.merge import merge
from shapely import wkt
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.audit_exact_piste_overlap_stage58 import build as exact_build,DEFS as NETWORK_DEFS
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths,horn
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_NATIVE2M_TERRAIN_PILOT_STAGE63'
TABLES=['winter_profile_exact_piste_overlap_stage63','terrain_native2m_pilot_cells_stage63','terrain_native2m_pilot_summary_stage63']
OUTPUTS=[f'data_processed/{t}.csv' for t in TABLES]
NETWORK='data_interim/winter_profile_exact_network_stage63.json'
SUMMARY='reports/native2m_terrain_pilot_stage63_summary.json'

CELL_DEFS={
 'source_id':('Registered derived diagnostic source','identifier'),
 'station_group_id':('Pilot derived group ID; not municipality','identifier'),
 'edition_reference_datetime':('Literal pilot DEM reference date, not assumed acquisition date','timestamp'),
 'cell_row':('Native mosaic cell row, zero based from north','index'),
 'cell_col':('Native mosaic cell column, zero based from west','index'),
 'cell_centre_east_2056':('Native cell centre easting, EPSG2056','metres'),
 'cell_centre_north_2056':('Native cell centre northing, EPSG2056','metres'),
 'unique_axis_length_m':('Exact unique mapped-axis length in this cell','metres'),
 'altitude_m':('Observed native DEM altitude; no nodata interpolation','metres'),
 'terrain_slope_degrees':('Strict observed3x3 Horn terrain slope','degrees'),
 'terrain_aspect_degrees':('Downslope azimuth N0/E90/S180/W270; missing forflat or unobservedgradient','degrees'),
 'altitude_observed':('Central raster cell has finite non-nodata observed elevation','boolean'),
 'gradient_observed':('All9neighbourhood cells observed; no missing interpolation','boolean'),
 'flat_terrain':('Exactlyzero slope when observed; missing ifgradient unavailable','boolean'),
 'centre_tile_source_id':('Original raster source atnativecentre, withneighbours from sameedition','identifier')}
STAT_DEFS={
 'source_id':('Registered derived diagnostic source','identifier'),
 'station_group_id':('Pilot derived group, not final acceptedcausalprofile','identifier'),
 'edition_reference_datetime':('Provider edition referencedatetime, not acquisitiondate','timestamp'),
 'unique_mapped_axis_length_m':('Current mappedcandidate-networklength, not exhaustiverealpistes','metres'),
 'axis_cell_count':('Native2m cells containing axislength, not independentstations','count'),
 'observed_altitude_length_m':('Unique axislength with observednativealtitude','metres'),
 'observed_gradient_length_m':('Unique axislength with fullyobservedHorn3x3gradient','metres'),
 'observed_orientation_length_m':('Unique axislength with nonflatobserveddirection','metres'),
 'flat_observed_length_m':('Observedgradient with exactlyzeroslope; retainedaltitude/length','metres'),
 'missing_altitude_length_m':('Retaineduniqueaxislength without observedaltitude','metres'),
 'missing_gradient_length_m':('Retaineduniqueaxislength without fullyobserved3x3','metres'),
 'minimum_observed_altitude_m':('Minimumobservedcentral-cellaltitude, no interpolation','metres'),
 'maximum_observed_altitude_m':('Maximumobservedcentral-cellaltitude','metres'),
 'length_weighted_observed_altitude_m':('Sum observed altitude×uniqueaxislength dividedby observedlength','metres'),
 'length_weighted_observed_slope_degrees':('Sum observedHornslope×uniqueaxislength dividedby observedgradientlength','degrees'),
 'current_candidate_proxy_not_verified_preentry':('True, no preentry or exhaustivedomaincertification','boolean')}


def main():
    paths=['src/descriptive/extract_terrain_pilot_stage63.py','src/descriptive/audit_exact_piste_overlap_stage58.py',
       'src/data_processing/terrain_cell_weights_stage61.py','config/terrain_vintage_decisions_stage62.json',
       'config/terrain_tile_sources_stage62.json','config/terrain_extraction_decisions_stage61.json',
       'data_processed/winter_profile_verified_piste_member_qa_stage60.csv','data_processed/winter_profile_verified_piste_group_qa_stage60.csv',
       'data_processed/accessibility_station_groups_stage55.csv','reports/piste_terrain_sources_stage60_summary.json',
       'reports/terrain_catalogue_stage61_summary.json','data_interim/terrain_tile_events_stage62.json']
    inputs={p:sha(p) for p in paths}
    for p in paths[9:11]:
        parent=json.loads((ROOT/p).read_text(encoding='utf8'))
        for f,h in {**parent['input_sha256'],**parent['output_sha256']}.items():
            if sha(f)!=h:raise ValueError('Prior checkpoint changed: '+f)
    queue=json.loads((ROOT/paths[4]).read_text(encoding='utf8'))
    metadata=[]
    for s in queue:
        files=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if len(files)!=1:raise ValueError('Requirecomplete84tilepilot before extraction: '+s['source_id'])
        m=json.loads(files[0].read_text(encoding='utf8'))
        if m['url']!=s['url'] or sha(m['raw_file'])!=s['expected_sha256'] or m['sha256']!=s['expected_sha256']:raise ValueError('Raster original/provider checksum mismatch')
        inputs[m['raw_file']]=m['sha256'];metadata.append(m)
    members=pd.read_csv(ROOT/paths[6],dtype=str,keep_default_na=False)
    groups=pd.read_csv(ROOT/paths[7],dtype=str,keep_default_na=False)
    lineage=pd.read_csv(ROOT/paths[8],dtype=str,keep_default_na=False).set_index('station_group_id').parent_station_group_ids.to_dict()
    index,_,_=originals();network_frame,networks=exact_build(groups,members,lineage,index)
    network_frame['source_id']=SOURCE
    network_frame['parent_source_ids']=network_frame.parent_source_ids.str.replace('DERIVED_VERIFIED_PISTE_MEMBER_QA_STAGE56','DERIVED_PISTE_ASSIGNMENT_MEMBER_QA_STAGE60',regex=False)
    gid='MP_GROUP_RESORT__st_luc_chandolin'
    geometry=wkt.loads(next(g['exact_unique_axis_wkt'] for g in networks if g['station_group_id']==gid))
    cell_rows=[];stats=[];header_checks=[]
    for edition in sorted({m['item_reference_datetime'] for m in metadata}):
        metas=[m for m in metadata if m['item_reference_datetime']==edition]
        with ExitStack() as stack:
            datasets=[stack.enter_context(rasterio.open(ROOT/m['raw_file'])) for m in metas]
            for m,d in zip(metas,datasets):
                if d.crs.to_epsg()!=2056 or d.res!=(2.0,2.0) or d.transform.b!=0 or d.transform.d!=0 or d.units!=('metre',) or d.count!=1:
                    raise ValueError('Require native northup2mEPSG2056 observedmetreDEM; no resampling/unitguess')
                header_checks.append(dict(source_id=m['source_id'],reference_datetime=edition,transform=list(d.transform),shape=list(d.shape),units=list(d.units),nodata=d.nodata,crs=str(d.crs)))
            array,transform=merge(datasets,nodata=-9999,dtype='float64')
            z=array[0];z[z==-9999]=np.nan
            weights=cell_lengths(geometry,transform.c,transform.f,2,2)
            tile_sources={tuple(d.bounds):m['source_id'] for m,d in zip(metas,datasets)}
            if len(tile_sources)!=len(datasets):raise ValueError('Duplicate edition tile bounds; no arbitrary mosaic precedence')
            for (row,col),length in weights.items():
                east,north=transform*(col+0.5,row+0.5)
                observed=0<=row<z.shape[0] and 0<=col<z.shape[1] and np.isfinite(z[row,col])
                altitude=float(z[row,col]) if observed else None
                slope,aspect=horn(z[row-1:row+2,col-1:col+2]) if 0<row<z.shape[0]-1 and 0<col<z.shape[1]-1 else (None,None)
                sid=next((sid for (left,bottom,right,top),sid in tile_sources.items() if left<=east<right and bottom<north<=top),'')
                cell_rows.append(dict(source_id=SOURCE,station_group_id=gid,edition_reference_datetime=edition,cell_row=row,cell_col=col,cell_centre_east_2056=east,cell_centre_north_2056=north,unique_axis_length_m=length,altitude_m=altitude,terrain_slope_degrees=slope,terrain_aspect_degrees=aspect,altitude_observed=bool(observed),gradient_observed=slope is not None,flat_terrain=(slope==0) if slope is not None else None,centre_tile_source_id=sid))
        cells=pd.DataFrame([r for r in cell_rows if r['edition_reference_datetime']==edition])
        total=math.fsum(cells.unique_axis_length_m)
        length=lambda mask:math.fsum(cells.loc[mask,'unique_axis_length_m'])
        mean=lambda col:float(np.average(cells.loc[cells[col].notna(),col],weights=cells.loc[cells[col].notna(),'unique_axis_length_m'])) if cells[col].notna().any() else None
        stats.append(dict(source_id=SOURCE,station_group_id=gid,edition_reference_datetime=edition,unique_mapped_axis_length_m=total,axis_cell_count=len(cells),observed_altitude_length_m=length(cells.altitude_observed),observed_gradient_length_m=length(cells.gradient_observed),observed_orientation_length_m=length(cells.terrain_aspect_degrees.notna()),flat_observed_length_m=length(cells.flat_terrain.eq(True)),missing_altitude_length_m=length(~cells.altitude_observed),missing_gradient_length_m=length(~cells.gradient_observed),minimum_observed_altitude_m=cells.altitude_m.min(),maximum_observed_altitude_m=cells.altitude_m.max(),length_weighted_observed_altitude_m=mean('altitude_m'),length_weighted_observed_slope_degrees=mean('terrain_slope_degrees'),current_candidate_proxy_not_verified_preentry=True))
    frames=[network_frame,pd.DataFrame(cell_rows),pd.DataFrame(stats)]
    state=dict(date='2026-10-10',input_sha256=inputs,original_tile_count=len(metadata),total_bytes=sum(m['size_bytes'] for m in metadata),group_count_retained=70,original_piste_objects_retained=len(members),current_mapped_axis_group_count=int(network_frame.exact_unique_mapped_axis_length_m.notna().sum()),pilot_edition_statistics=stats,header_checks=header_checks,reference_rule='Latestpertile2024 in thispilot;2019comparison retained',source_attribution='Office fédéral de topographie swisstopo',no_missing_interpolation_or_flat_threshold=True,no_individual_metric_or_preentry_certification=True,no_snow_splice_classes_or_effect_fit=True)
    target=ROOT/SUMMARY
    if target.exists():
        old=json.loads(target.read_text(encoding='utf8'))
        if old['input_sha256']!=inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):raise ValueError('Frozen pilot differs')
    else:
        for f,p in zip(frames,OUTPUTS):write_csv(f,ROOT/p)
        (ROOT/NETWORK).write_text(json.dumps(networks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        state['output_sha256']={p:sha(p) for p in [*OUTPUTS,NETWORK]}
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    records=[dict(source_id=m['source_id'],variable_name='native2m_dem_elevation',variable_description='OriginalswissALTI3D2mmetreGeoTIFF; referenceedition or comparisonpilot, notpreentryverified',source_organisation=m['organisation'],source_page_url=m['url'],retrieval_date=m['retrieval_date'],original_file_name=Path(m['raw_file']).name,local_raw_file=m['raw_file'],processed_file='|'.join(OUTPUTS[1:]),geographic_level='NativetileEPSG2056',temporal_resolution='Providerreferenceedition '+m['item_reference_datetime'],units='metres elevation;2mgrid',license='OfficialswisstopoOGDterms withmandatoryattribution; collectionproprietarymarker separatelyretained',retrieval_method='Serialrobots/TLS/immutableGeoTIFF withofficialSHA256verified',transformation_applied='Originaluntouched;nativeobservedcellvalues andstrict3x3Horn diagnostic',quality_notes='Notactualacquisitiondate/preentrygeometry; no nodatainterpolation',notes='Parent SWISSTOPO_ALTI3D_STLUC_ITEMS_STAGE61; SHA256='+m['sha256']) for m in metadata]
    records.append(dict(source_id=SOURCE,variable_name='approved_native2m_terrain_pilot_and_current_unique_network',variable_description='Updated854objectmappednetwork and StLuc2019/2024cell-length/Horn terrain diagnostics',source_organisation='Thesis audit of OSM/swisstopo',retrieval_date='2026-10-10',processed_file='|'.join(OUTPUTS),geographic_level='70retainedgroups, oneboundedpilot, notmunicipaloutcomes',temporal_resolution='Currentqualifiedgeometry;literal2019/2024DEMreferenceeditions',license='OSMODbL;swisstopoOGDterms andattribution',retrieval_method='Approveduniquegeometry/native2mcells/Horn/nointerpolation;originalSHAandheaders',transformation_applied='Lengthweightobservedaltitude/slope;orientationcellazimuthretainedwithoutunapprovedaggregation/categories',quality_notes='No exhaustive/preentry/memberacceptance, sourceimputation, exclusions or causalfeatures',notes='FullSHAandcoverage in '+SUMMARY))
    records=[r for r in records if r['source_id'] not in set(master.source_id)]
    if records:write_csv(pd.concat([master,pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);records=[]
    for table,f,defs in zip(TABLES,frames,[NETWORK_DEFS,CELL_DEFS,STAT_DEFS]):
        if set(f)!=set(defs):raise ValueError('Every field defined')
        for col,(description,unit) in defs.items():
            if ((dictionary.table==table)&(dictionary.variable==col)).any():continue
            records.append(dict(variable=col,table=table,description=description,unit=unit,data_type=str(f[col].dtype),source_id=SOURCE,geographic_level='mappedcandidate group/nativepilotcell',temporal_level='currentgeometry/DEMreferenceedition',raw_or_derived='diagnostic only, not finalpreentryfeature',formula='Exactuniqueaxis length percell;strictHorn3x3;observedlength weightedmeans,missingnotzero',causal_role='qualifiedsource/coverage diagnostic, no causalprofilecertification',missing_share=f'{f[col].isna().mean():.6f}',notes='Allgroups/originalsretained; no interpolation/aspectclass/exclusions'))
    if records:write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','header_checks']},ensure_ascii=False))


if __name__=='__main__':main()
