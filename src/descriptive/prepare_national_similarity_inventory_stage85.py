"""National preparation, no listing/legacy lift cluster silently made a ski domain."""
import json
import re
import sys
import unicodedata
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_NATIONAL_SIMILARITY_PREPARATION_STAGE85'
OUTPUTS=['data_processed/national_similarity_inventory_stage85.csv',
    'data_processed/national_similarity_listing_lineage_stage85.csv',
    'data_processed/national_similarity_piste_site_inventory_stage85.csv']
SUMMARY='reports/national_similarity_inventory_stage85_summary.json'
DEFS={
    'source_id':('Registered preparation source, not official certification of national ski domains','identifier'),
    'preparation_unit_id':('Existing validated station_group_id or explicitly provisional listing ID; never silently a verified new domain','identifier'),
    'unit_name':('Existing readable source name, not a join key','text'),
    'identity_level':('Approved existing group versus unresolved provisional catalogue listing','category'),
    'unit_scope_verified':('True only for retained approved group layer, not new independent-domain certification','boolean'),
    'swiss_scope_status':('Prior approved Swiss group or source point inside/outside Swiss municipal polygons; not a new domain boundary','category'),
    'within_swiss_preparation_scope':('Swiss existing scope or Swiss source-point listing included for preparation, not filtering fitted clusters','boolean'),
    'component_resort_ids':('All original listing IDs, retained under approved grouping or pending candidate','identifiers'),
    'cluster_ids_lineage_only':('Old supplied lift cluster identifiers retained only as lineage, not physical domain equivalence','identifiers'),
    'historical_magic_group':('Existing approved historical Magic group, not automatically currently operational/current membership','boolean'),
    'current_magic_candidate_destination_ids':('Literal archived catalogue candidate IDs; scope pending, not negative/positive membership certificate','identifiers'),
    'membership_verification_status':('No unresolved or absent join interpreted as verified nonmembership; membership not a clustering input','category'),
    'metric_piste_geometry_available':('Reviewed exact eligible network exists in current profile layer','boolean'),
    'terrain_profile_available':('Observed terrain profile exists, not complete domain or historical certification','boolean'),
    'common_decade_snow_profile_available':('Common2013/14–2022/23 mean exists, not independent-domain/clustering approval','boolean'),
    'provided_structural_context_available':('Original listing top elevation/piste km/lift count present; definitions differ from measured axes','boolean'),
    'npvm_road_context_available':('Existing ARE zonal road context available, not interchangeable with six-city ORS stop routing','boolean'),
    'ors_six_city_reference_available':('Existing approved-group six-city ORS stop reference available, no new point substitution','boolean'),
    'nearest_tp_context_available':('Nearest official stop already available; not verified road arrival at ski departure','boolean'),
    'pending_connection_review':('Several listings share a legacy lift cluster or an existing group cluster: hint only, no merge','boolean'),
    'possible_existing_group_ids_legacy_cluster_hint':('Existing groups sharing supplied lift cluster; not a proven piste connection','identifiers'),
    'legacy_same_cluster_listing_count':('Count of original catalogue listings sharing existing lift cluster; not domain size','count'),
    'next_preparation_action':('Specific unresolved preparation needs; no sample exclusion','text'),
    'source_ids':('Literal parent source IDs and derived table parents','identifiers'),
    'resort_id':('Original catalogue listing ID, stable and retained','identifier'),
    'resort_name_canonical':('Original canonical listing name','text'),
    'original_cluster_id':('Preserved legacy lift cluster, never rebuilt','identifier'),
    'point_municipality_bfs_id':('Existing official coordinate-container BFS, not tourism catchment','identifier'),
    'point_selection_status':('Original geolocation interpretation retained','category'),
    'original_identity_status':('Original listing versus domain identity warning retained','category'),
    'original_feature_observation_date':('Original UNKNOWN retained when snapshot date uncertified','text'),
    'osm_site_relation_id':('Original OSM relation identifier, not a newly assigned national unit','identifier'),
    'osm_site_name':('Original OSM site name, never sufficient for assignment','text'),
    'cached_downhill_way_count':('Existing completed selected downhill members, not certified complete real domain','count'),
    'cached_nordic_way_count':('Existing distinct nordic member count, not downhill axes','count'),
    'unresolved_way_relation_count':('Existing unresolved referenced members retained','count'),
    'related_approved_group_ids':('Existing explicit site relation references in approved group table','identifiers'),
    'new_national_assignment_accepted':('False: inventory is preparation only, not automatic site/name/distance acceptance','boolean'),
    'exact_name_listing_hint_ids':('Normalised exact name search hint only, not accepted entity resolution or a sole-key merge','identifiers'),
}


def name_hint(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',str(text)) if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',text.casefold()).strip()


def main():
    paths=['src/descriptive/prepare_national_similarity_inventory_stage85.py','config/descriptive_similarity_scope_stage84.json',
        'data_processed/resort_master.csv','data_processed/resort_point_municipality.csv',
        'data_processed/accessibility_station_groups_stage79.csv','data_processed/winter_profile_metric_network_stage80.csv',
        'data_processed/terrain_reviewed_profiles_stage82.csv','data_processed/common_snow_profiles_stage84.csv',
        'data_processed/resort_transport_accessibility_context.csv','data_processed/resort_public_transport_stop_context.csv',
        'data_processed/magic_pass_current_destinations.csv','data_processed/winter_profile_piste_assignment_stage79.csv',
        'data_processed/winter_profile_piste_site_membership_audit.csv','data_processed/accessibility_road_group_reference_stage79.csv']
    inputs={p:sha(p) for p in paths};master=pd.read_csv(ROOT/paths[2],dtype=str,keep_default_na=False)
    geo=pd.read_csv(ROOT/paths[3],dtype=str,keep_default_na=False).set_index('resort_id')
    groups=pd.read_csv(ROOT/paths[4],dtype=str,keep_default_na=False)
    terrain=pd.read_csv(ROOT/paths[6]).set_index('station_group_id');snow=pd.read_csv(ROOT/paths[7]).set_index('station_group_id')
    are=pd.read_csv(ROOT/paths[8]).set_index('resort_id');tp=pd.read_csv(ROOT/paths[9]).set_index('resort_id')
    current=pd.read_csv(ROOT/paths[10],dtype=str,keep_default_na=False)
    road=pd.read_csv(ROOT/paths[13]);city_ids={261,351,2701,5192,5586,6621}
    road_count=road[road.municipality_bfs_id.isin(city_ids)].groupby('station_group_id').road_reference_minutes.count()
    if not master.resort_id.is_unique or not groups.station_group_id.is_unique:raise ValueError('Original stable IDs must be unique')
    listing=master.set_index('resort_id');covered={};cluster_groups={}
    for g in groups.itertuples():
        for rid in g.component_resort_ids.split('|') if g.component_resort_ids else []:
            if rid in covered or rid not in listing.index:raise ValueError('Ambiguous original listing linkage')
            covered[rid]=g.station_group_id
            cid=listing.loc[rid,'cluster_id']
            if cid:cluster_groups.setdefault(cid,set()).add(g.station_group_id)
    counts=master[master.cluster_id.ne('')].groupby('cluster_id').size().to_dict()
    rows=[];lineage=[]
    for g in groups.itertuples():
        ids=g.component_resort_ids.split('|') if g.component_resort_ids else []
        parents='|'.join(sorted(set(g.source_ids.split('|'))|{'DERIVED_CONNECTED_GROUP_OVERLAY_STAGE79','DERIVED_REVIEWED_NATIVE2M_PROFILES_STAGE82','DERIVED_COMMON_SNOW_DESCRIPTIVE_STAGE84'}))
        rows.append(dict(source_id=SOURCE,preparation_unit_id=g.station_group_id,unit_name=g.station_group_name,identity_level='existing_approved_group',
            unit_scope_verified=True,swiss_scope_status='prior_approved_swiss_group_scope',within_swiss_preparation_scope=True,
            component_resort_ids=g.component_resort_ids,cluster_ids_lineage_only='|'.join(sorted({listing.loc[r,'cluster_id'] for r in ids if listing.loc[r,'cluster_id']})),
            historical_magic_group=True,current_magic_candidate_destination_ids='|'.join(sorted(set(current.loc[current.candidate_resort_id.isin(ids),'official_destination_id']))),
            membership_verification_status='historical_magic_link_current_catalogue_scope_separate',
            metric_piste_geometry_available=pd.notna(terrain.loc[g.station_group_id,'unique_mapped_axis_length_m']),
            terrain_profile_available=pd.notna(terrain.loc[g.station_group_id,'length_weighted_observed_altitude_m']),
            common_decade_snow_profile_available=pd.notna(snow.loc[g.station_group_id,'common_ten_winter_mean_m']),
            provided_structural_context_available=bool(ids) and all(all(listing.loc[r,c] not in ['', 'UNKNOWN'] for c in ['altitude_top_m','ski_area_km','number_lifts']) for r in ids),
            npvm_road_context_available=bool(ids) and all(bool(are.loc[r,'travel_time_values_complete']) for r in ids),
            ors_six_city_reference_available=road_count.get(g.station_group_id,0)==6,
            nearest_tp_context_available=bool(ids) and all(bool(tp.loc[r,'public_transport_stop_values_complete']) for r in ids),
            pending_connection_review=False,possible_existing_group_ids_legacy_cluster_hint='',
            next_preparation_action='Common descriptive profiles ready; no prediction or automatic clustering acceptance' if pd.notna(snow.loc[g.station_group_id,'common_ten_winter_mean_m']) else 'Original geometry gap retained for documentary review',
            source_ids=parents))
    for r in master.itertuples():
        country=geo.loc[r.resort_id];rid=r.resort_id;inside=country.selection_status=='unique_current_polygon'
        unit=covered.get(rid,'DESC_LISTING_PENDING__'+rid)
        lineage.append(dict(source_id=SOURCE,resort_id=rid,resort_name_canonical=r.resort_name_canonical,preparation_unit_id=unit,
            original_cluster_id=r.cluster_id,point_municipality_bfs_id=country.point_municipality_bfs_id,
            point_selection_status=country.selection_status,original_identity_status=r.identity_status,
            original_feature_observation_date=r.feature_observation_date,
            source_ids=r.source_ids+'|'+country.source_id+'|'+country.query_source_id))
        if rid in covered:continue
        possible=sorted(cluster_groups.get(r.cluster_id,set()))
        matches=current[current.candidate_resort_id.eq(rid)]
        rows.append(dict(source_id=SOURCE,preparation_unit_id=unit,unit_name=r.resort_name_canonical,identity_level='provisional_listing_not_verified_independent_domain',
            unit_scope_verified=False,swiss_scope_status=country.selection_status,within_swiss_preparation_scope=inside,component_resort_ids=rid,
            cluster_ids_lineage_only=r.cluster_id,historical_magic_group=False,
            current_magic_candidate_destination_ids='|'.join(sorted(set(matches.official_destination_id))),
            membership_verification_status='current_catalogue_candidate_scope_pending' if len(matches) else 'absence_of_resolved_link_is_not_verified_nonmembership',
            metric_piste_geometry_available=False,terrain_profile_available=False,common_decade_snow_profile_available=False,
            provided_structural_context_available=all(getattr(r,c) not in ['', 'UNKNOWN'] for c in ['altitude_top_m','ski_area_km','number_lifts']),
            npvm_road_context_available=bool(are.loc[rid,'travel_time_values_complete']),
            ors_six_city_reference_available=False,nearest_tp_context_available=bool(tp.loc[rid,'public_transport_stop_values_complete']),
            pending_connection_review=counts.get(r.cluster_id,0)>1 or bool(possible),
            possible_existing_group_ids_legacy_cluster_hint='|'.join(possible),legacy_same_cluster_listing_count=counts.get(r.cluster_id,0),
            next_preparation_action='Verify domain identity, connected scope, cached pistes and actual arrival before comparable physical/road profiles' if inside else 'Foreign standalone listing retained in audit, outside requested Swiss candidate preparation',
            source_ids=r.source_ids+'|'+country.source_id+'|'+country.query_source_id+'|ARE_NPVM_TRAVEL_TIME_2025|BAV_PUBLIC_TRANSPORT_STOPS_2026'))
    assignment=pd.read_csv(ROOT/paths[11],dtype=str,keep_default_na=False);relations={}
    for a in assignment.itertuples():
        if a.osm_site_relation_id:
            sid=int(float(a.osm_site_relation_id));relations.setdefault(sid,[]).append(a.station_group_id)
    site_source=pd.read_csv(ROOT/paths[12]);hints={}
    for r in master.itertuples():hints.setdefault(name_hint(r.resort_name_canonical),[]).append(r.resort_id)
    sites=[]
    for s in site_source.itertuples():
        sites.append(dict(source_id=SOURCE,osm_site_relation_id=int(s.osm_site_relation_id),osm_site_name=s.osm_site_name,
            cached_downhill_way_count=int(s.completed_selected_downhill_way_count),cached_nordic_way_count=int(s.known_nordic_way_member_count),
            unresolved_way_relation_count=int(s.remaining_unresolved_way_relation_count),
            related_approved_group_ids='|'.join(sorted(relations.get(int(s.osm_site_relation_id),[]))),new_national_assignment_accepted=False,
            exact_name_listing_hint_ids='|'.join(sorted(hints.get(name_hint(s.osm_site_name),[]))),
            source_ids=str(s.source_id)+'|'+str(s.parent_source_ids)))
    frames=[pd.DataFrame(rows),pd.DataFrame(lineage),pd.DataFrame(sites)]
    if len(frames[0])!=len(groups)+len(master)-len(covered) or len(lineage)!=271:raise ValueError('All original listings and approved groups must remain')
    target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256']!=inputs or any(sha(p)!=h for p,h in state['output_sha256'].items()):raise ValueError('Frozen national inventory differs')
    else:
        for p,f in zip(OUTPUTS,frames):write_csv(f,ROOT/p)
        unreviewed=frames[0][frames[0].identity_level.ne('existing_approved_group')&frames[0].within_swiss_preparation_scope]
        state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,output_sha256={p:sha(p) for p in OUTPUTS},
            all_original_listing_count=len(master),original_swiss_point_listings=int((geo.selection_status=='unique_current_polygon').sum()),
            preserved_approved_group_count=len(groups),listing_ids_in_approved_groups=len(covered),
            swiss_provisional_listing_count=len(unreviewed),foreign_standalone_listing_count=int((~frames[0].within_swiss_preparation_scope).sum()),
            provisional_swiss_rows_with_legacy_cluster_connection_hint=int(unreviewed.pending_connection_review.sum()),
            provisional_swiss_rows_sharing_legacy_cluster_with_approved_group=int(unreviewed.possible_existing_group_ids_legacy_cluster_hint.ne('').sum()),
            cached_osm_sites_available_for_review=len(sites),not_a_verified_national_domain_count=True,
            no_automatic_nonmembership_merge_piste_assignment_exclusion_or_model_fit=True)
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    source_table=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    if SOURCE not in set(source_table.source_id):
        record=dict(source_id=SOURCE,variable_name='national_descriptive_domain_preparation_and_lineage',
            variable_description='Original271listings and existing69groups retained; Swiss-point candidates and cached238OSMsites separated from verified physical domains',
            source_organisation='Thesis audit of existing Bergfex/geo.admin/OSM/ARE/BAV/Magic sources',retrieval_date='2026-10-12',
            processed_file='|'.join(OUTPUTS),geographic_level='Approved groups and provisional listings/site references, not a finished independent-domain universe',
            temporal_resolution='Existing undated listings/current-source snapshots; common2013/14–2022/23 snow where verified axes exist',
            license='Inherited parent sources; OSM ODbL/Swiss OGD attribution; no external recollection',
            transformation_applied='StableID joins only; original group and cluster lineage kept, exact-name hints not accepted as assignments',
            quality_notes='Missing joins not verified nonmembership; old lift clusters not automatic connected domains; nearest TP/ARE not automatically ORS arrival or comparable route',
            notes=SUMMARY+'; prediction later, no fitted clustering')
        write_csv(pd.concat([source_table,pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);add=[]
    for path,f in zip(OUTPUTS,frames):
        for c in f:
            if ((dictionary.table==Path(path).stem)&dictionary.variable.eq(c)).any():continue
            desc,unit=DEFS[c]
            add.append(dict(variable=c,table=Path(path).stem,description=desc,unit=unit,data_type=str(f[c].dtype),
                geographic_level='Provisional listing/approved group/original OSMsite, not independent domains yet',temporal_level='Existing qualified source snapshots/common descriptive decade',
                source_id=SOURCE,raw_or_derived='audit only',formula=desc,causal_role='Descriptive preparation and ambiguity, not fitted classes/treatment/prediction',
                missing_share=f'{f[c].isna().mean():.6f}',notes='No automatic membership, geometric proximity, domain merging or sample exclusion'))
    if add:write_csv(pd.concat([dictionary,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256']},ensure_ascii=False))


if __name__=='__main__':main()
