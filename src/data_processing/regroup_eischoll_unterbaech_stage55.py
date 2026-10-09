"""Approved connected-domain overlay; no source replacement or effect fitting.

Reuse existing minimum usable road access and original treatment dates. Both
original group IDs and event/access IDs survive in explicit lineage. Municipal
outcomes remain single territory-month rows, repeated only across sensitivity
specifications as before, never across station components.
"""
import json
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.causal_inference.estimate_accessibility_road_did import group_reference,build_exposure
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.descriptive.review_piste_candidates_stage53 import originals
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

CONFIG='config/eischoll_unterbaech_regrouping_stage55.json'
SOURCE='DERIVED_CONNECTED_GROUP_OVERLAY_STAGE55'
SUMMARY='reports/eischoll_unterbaech_regrouping_stage55_summary.json'
PATHS={
    'mapping':'data_processed/station_group_lineage_stage55.csv',
    'groups':'data_processed/accessibility_station_groups_stage55.csv',
    'access':'data_processed/accessibility_station_access_points_stage55.csv',
    'pairs':'data_processed/accessibility_road_pairs_stage55.csv',
    'reference':'data_processed/accessibility_road_group_reference_stage55.csv',
    'monthly':'data_processed/accessibility_road_monthly_exposure_stage55.csv',
    'inventory':'reports/accessibility_road_inventory_stage55.csv',
    'pistes':'data_processed/winter_profile_piste_assignment_stage55.csv'}
PARENTS={
    'groups':'accessibility_station_groups',
    'access':'accessibility_station_access_points',
    'pairs':'accessibility_road_final_pairs',
    'reference':'accessibility_road_did_group_reference',
    'monthly':'accessibility_road_did_monthly_exposure',
    'inventory':'accessibility_road_did_inventory',
    'pistes':'winter_profile_piste_assignment_stage53'}


def joined(cells):
    return '|'.join(sorted({p for cell in cells for p in str(cell).split('|') if p}))


def regroup(groups,decision):
    originals=decision['parent_group_ids'];new=decision['new_derived_group_id']
    if len(groups)!=71 or not groups.station_group_id.is_unique or new in set(groups.station_group_id):raise ValueError('Require original71-group universe')
    parent=groups[groups.station_group_id.isin(originals)]
    if len(parent)!=2 or not parent.first_effective_month.eq('2023-05-01').all():raise ValueError('Preserve exact common first entry')
    for column in ['first_entry_season','first_effective_month','first_winter_effective_month','membership_continuity_status']:
        if parent[column].nunique()!=1:raise ValueError('Different histories require a separately approved calendar')
    components=[v for cell in parent.component_resort_ids for v in cell.split('|') if v]
    if len(components)!=len(set(components)):raise ValueError('Never sum repeated component listings')
    row=parent.iloc[0].to_dict()
    for column in ['component_resort_ids','source_entry_event_ids','source_entry_labels','cluster_ids_lineage_only','source_ids']:
        row[column]=joined(parent[column])
    row.update(station_group_id=new,station_group_name=decision['new_group_name'],group_origin='researcher_approved_connected_overlay',
        scope_status='connected_ski_domain_historical_account_corrob_not_certified_map',grouping_basis='Approved current official ski connection + authored2022 account; retain historical caveat and separate source IDs',
        component_listing_count=len(components),entry_event_count=len(row['source_entry_event_ids'].split('|')),
        structural_data_status='unique_listing_sums_only_physical_overlap_and_preentry_unverified')
    for column in ['ski_area_km_unique_listing_sum','number_lifts_unique_listing_sum']:
        values=pd.to_numeric(parent[column],errors='coerce')
        row[column]=values.sum(min_count=len(parent))
    for column,method in [('altitude_top_m_min','min'),('altitude_top_m_max','max')]:
        values=pd.to_numeric(parent[column],errors='coerce')
        row[column]=getattr(values,method)() if values.notna().all() else np.nan
    result=pd.concat([groups[~groups.station_group_id.isin(originals)],pd.DataFrame([row])],ignore_index=True)
    result['parent_station_group_ids']=result.station_group_id.map(lambda x:joined(originals) if x==new else x)
    result['aggregation_source_id']=SOURCE
    result['historical_connection_quality']=result.station_group_id.map(lambda x:decision['historical_connection_quality'] if x==new else 'No change to original grouping evidence')
    mapping=pd.DataFrame(dict(original_station_group_id=g.station_group_id,station_group_id=new if g.station_group_id in originals else g.station_group_id,
        original_station_group_name=g.station_group_name,group_changed=g.station_group_id in originals,source_id=SOURCE) for g in groups.itertuples())
    if len(result)!=70 or len(mapping)!=71 or mapping.original_station_group_id.nunique()!=71:raise ValueError('Grouping must retain all original identities')
    other=groups[~groups.station_group_id.isin(originals)].reset_index(drop=True)
    if not other.equals(result.loc[result.station_group_id.ne(new),groups.columns].reset_index(drop=True)):raise ValueError('Unrelated group attributes changed')
    return result,mapping


def map_ids(frame,mapping):
    result=frame.copy()
    result['original_station_group_id']=result.station_group_id
    bridge=mapping.set_index('original_station_group_id').station_group_id.to_dict()
    result['station_group_id']=result.station_group_id.map(bridge)
    if result.station_group_id.isna().any():raise ValueError('Unmapped original identity')
    return result


def compare_exposure(before,after):
    keys=['municipality_bfs_id','date','threshold_minutes']
    if before.duplicated(keys).any() or after.duplicated(keys).any():raise ValueError('No duplicate territory-month observations within a threshold')
    fields=['hotel_overnights','log_overnights','first_exposure_month','nearest_active_group_minutes','active_station_group_count','new_station_group_entry_count','exposure_assignment_status']
    merged=before[keys+fields].merge(after[keys+fields],on=keys,validate='one_to_one',how='outer',indicator=True,suffixes=('_old','_new'))
    if not merged._merge.eq('both').all():raise ValueError('Territory/month universe changed')
    equal=lambda c:(merged[c+'_old'].eq(merged[c+'_new']) | (merged[c+'_old'].isna()&merged[c+'_new'].isna()))
    for c in ['hotel_overnights','log_overnights','first_exposure_month']:
        if not equal(c).all():raise ValueError('Outcome or first actual exposure changed: '+c)
    if not np.allclose(merged.nearest_active_group_minutes_old,merged.nearest_active_group_minutes_new,equal_nan=True):raise ValueError('Nearest active access changed')
    for c in ['active_station_group_count','new_station_group_entry_count']:
        delta=merged[c+'_new']-merged[c+'_old']
        if not delta.isin([0,-1]).all():raise ValueError('Unexpected group-count change')
    return [dict(threshold_minutes=int(t),territory_count=p.municipality_bfs_id.nunique(),observation_count=len(p),
        rows_with_active_count_reduced=int((p.active_station_group_count_new<p.active_station_group_count_old).sum()),
        territories_with_active_count_reduced=p.loc[p.active_station_group_count_new.lt(p.active_station_group_count_old),'municipality_bfs_id'].nunique(),
        rows_with_entry_count_reduced=int((p.new_station_group_entry_count_new<p.new_station_group_entry_count_old).sum()),
        exposure_status_changed_rows=int((p.exposure_assignment_status_old!=p.exposure_assignment_status_new).sum()),
        outcomes_and_first_exposure_preserved=True) for t,p in merged.groupby('threshold_minutes')]


def register(frames):
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    if SOURCE not in set(master.source_id):
        record=dict(source_id=SOURCE,variable_name='connected_station_group_overlay',variable_description='Researcher-approved Eischoll/Unterbaech group with original IDs and unique municipal outcomes',source_organisation='Thesis derived overlay',retrieval_date='2026-10-10',retrieval_method='Validated lineage + cached existing road minima + unchanged historical entry dates',processed_file='|'.join(PATHS.values()),geographic_level='70derivedgroups, all71originalidentities and185municipalterritories',temporal_resolution='Historical treatment calendars/current static road reference',transformation_applied='Two approved groups toone; minimum usable old access times; original road source values/outcomes unchanged',quality_notes='Selfdated2022authored historical connection, not official old map; catalogue lift sums not verified physical or preentry features',notes='Approval in '+CONFIG+'; frozeninputs/outputSHA in '+SUMMARY+'; no effects estimated')
        write_csv(pd.concat([master,pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);records=[]
    explicit={'parent_station_group_ids':('All original group IDs retained behind a derived group','identifiers'),
        'aggregation_source_id':('Approved regrouping derivation source','identifier'),
        'historical_connection_quality':('Historical connection evidence and limitations, not geometry certification','text'),
        'original_station_group_id':('Unchanged original group key before overlay','identifier'),
        'original_station_group_name':('Unchanged original group name before overlay','name'),
        'group_changed':('True only for thetwoapprovedparents','boolean')}
    for key,frame in frames.items():
        table=Path(PATHS[key]).stem;parent_table=PARENTS.get(key)
        parent=dictionary[dictionary.table.eq(parent_table)] if parent_table else dictionary.iloc[:0]
        for col in frame:
            if ((dictionary.table==table)&(dictionary.variable==col)).any():continue
            previous=parent[parent.variable.eq(col)]
            if len(previous)==1:
                record=previous.iloc[0].to_dict();record.update(table=table,source_id=SOURCE,formula='Retain parentfield semantics; approved lineage/roadminimum transformation only; see '+SUMMARY,notes='Original definition/source remains in '+parent_table+'; common group catalogue counts not physical/historical metric certification')
            else:
                description,unit=explicit.get(col,('Retained attribute '+col+' from '+str(parent_table)+'; original source semantics unchanged exceptapprovedgroup overlay','original source unit'))
                record=dict(variable=col,table=table,description=description,unit=unit,source_id=SOURCE,geographic_level='Group lineage or unchanged municipal territory-month',temporal_level='Retained historical dates/current road reference',raw_or_derived='retained or approved regrouping diagnostic',formula='src/data_processing/regroup_eischoll_unterbaech_stage55.py',causal_role='accessibility/group inventory, not new effect estimate',notes='No outcome duplication, excluded commune, imputation or summer-offer inference')
            record.update(data_type=str(frame[col].dtype),missing_share=f'{frame[col].isna().mean():.6f}')
            records.append(record)
    if records:write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    decision=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    if not decision['preserve_original_group_ids_and_outputs'] or decision['new_effect_estimation_authorised'] or decision['automatic_exclusion_authorised']:raise ValueError('Require exact approved limited scope')
    fixed=[CONFIG,'src/data_processing/regroup_eischoll_unterbaech_stage55.py','data_processed/accessibility_station_groups.csv','data_processed/accessibility_station_access_points.csv',
        'data_processed/accessibility_road_final_pairs.csv','data_processed/accessibility_road_did_monthly_exposure.csv','data_processed/accessibility_municipality_month_exposure_territorial.csv',
        'data_processed/magic_pass_membership_history.csv','data_processed/winter_profile_piste_assignment_stage53.csv','reports/piste_history_stage54_summary.json',
        'reports/verified_piste_member_qa_stage54_summary.json','src/causal_inference/estimate_accessibility_road_did.py','config/accessibility_road_did_final_execution.json']
    parent=json.loads((ROOT/'reports/piste_assignment_stage53_summary.json').read_text(encoding='utf-8'))
    for p,h in {**parent['input_sha256'],**parent['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Previous checkpoint changed: '+p)
    inputs={p:sha(p) for p in fixed}
    groups=pd.read_csv(ROOT/fixed[2],dtype=str,keep_default_na=False)
    new_groups,mapping=regroup(groups,decision)
    access=map_ids(pd.read_csv(ROOT/fixed[3],dtype=str,keep_default_na=False),mapping)
    old_pairs=pd.read_csv(ROOT/fixed[4]);pairs=map_ids(old_pairs,mapping)
    reference=group_reference(pairs,new_groups);reference['source_id']=SOURCE
    panel=pd.read_csv(ROOT/fixed[6]);history=pd.read_csv(ROOT/fixed[7])
    monthly,inventory=build_exposure(reference,panel,history,[15,30,45]);monthly['accessibility_source_id']=SOURCE;inventory['source_id']=SOURCE
    before=pd.read_csv(ROOT/fixed[5]);before['date']=pd.to_datetime(before.date);before['first_exposure_month']=pd.to_datetime(before.first_exposure_month)
    changes=compare_exposure(before,monthly)
    index,counts,sites=originals();site=sites[decision['piste_site_relation_id']]
    if len(site['selected_downhill_way_ids'])!=63 or site['cycle_relation_ids']:raise ValueError('Unexpected current source membership')
    old_pistes=pd.read_csv(ROOT/fixed[8],dtype=str,keep_default_na=False)
    parent_pistes=old_pistes[old_pistes.station_group_id.isin(decision['parent_group_ids'])]
    if parent_pistes.current_site_correspondence_verified.ne('False').any():raise ValueError('Unexpected existing accepted parent assignment')
    common=parent_pistes.iloc[0].to_dict(); stats=counts[counts.osm_site_relation_id.eq(decision['piste_site_relation_id'])].iloc[0]
    common.update(station_group_id=decision['new_derived_group_id'],station_group_name=decision['new_group_name'],component_resort_ids=joined(parent_pistes.component_resort_ids),current_site_correspondence_verified='True',osm_site_relation_id=decision['piste_site_relation_id'],operator_source_id='OPERATOR_DEEP_06_STAGE53',scope_source_id='UNTERBAECH_EISCHOLL_FIRSTHAND_ENVIADI_STAGE54',downhill_member_object_count=63,known_lift_member_count=int(stats.known_aerialway_member_count),known_nordic_member_count=int(stats.known_nordic_way_member_count),unresolved_way_relation_count=int(stats.remaining_unresolved_way_relation_count),remaining_node_reference_count=int(stats.remaining_node_reference_count),review_status='verified_current_connected_site_correspondence',review_note='Researcher-approved common domain; official current connection + selfdated2022authoredaccount + individually inspected original sharedsite map.63downhillmembers/6knownaerialways not exhaustive; officialcurrent7installations versusdirectorysum10 requires component/lift-type review. No membermetrics or preentrygeometry certification.',source_id=SOURCE)
    pistes=pd.concat([old_pistes[~old_pistes.station_group_id.isin(decision['parent_group_ids'])],pd.DataFrame([common])],ignore_index=True)
    if len(pistes)!=70 or pistes.current_site_correspondence_verified.eq('True').sum()!=40:raise ValueError('Unexpected derived correspondence universe')
    frames=dict(mapping=mapping,groups=new_groups,access=access,pairs=pairs,reference=reference,monthly=monthly,inventory=inventory,pistes=pistes)
    state=dict(date='2026-10-10',input_sha256=inputs,original_group_identity_count=71,new_group_count=70,access_point_count=len(access),original_road_pair_count=len(old_pairs),derived_road_pair_count=len(pairs),retained_territory_count=panel.municipality_bfs_id.nunique(),current_site_verified_group_count=40,pending_group_count=30,new_common_site_downhill_members=63,cumulative_downhill_member_objects=773,exposure_comparison=changes,no_original_output_overwritten=True,no_new_routing_or_point_changes=True,no_effects_estimated=True,no_automatic_exclusions=True,historic_official_domain_geometry_certified=False,summer_component_offering_not_inferred=True,catalogue_lift_sum_not_verified_physical_count=True)
    target=ROOT/SUMMARY
    if target.exists():
        prior=json.loads(target.read_text(encoding='utf-8'))
        if prior['input_sha256']!=inputs or any(sha(p)!=h for p,h in prior['output_sha256'].items()):raise ValueError('Own frozen overlay changed')
    else:
        for key,frame in frames.items():write_csv(frame,ROOT/PATHS[key])
        state['output_sha256']={p:sha(p) for p in PATHS.values()};target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    register(frames)
    print(json.dumps({k:v for k,v in state.items() if not k.endswith('sha256')},ensure_ascii=False))


if __name__=='__main__':main()
