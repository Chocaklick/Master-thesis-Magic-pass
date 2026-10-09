"""Offline member QA, not station lengths, terrain/snow features or exclusions.

Current site correspondence does not individually certify its members. Exact
geometry/edge repetitions and lifecycle tags are flags only, without tolerance,
automatic repair, deduplication across different IDs or operating-status inference.
"""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter,defaultdict
from pathlib import Path
import pandas as pd
from shapely.geometry import LineString
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_VERIFIED_PISTE_MEMBER_QA_STAGE54'
MEMBER_TABLE='winter_profile_verified_piste_member_qa_stage54'
GROUP_TABLE='winter_profile_verified_piste_group_qa_stage54'
OUTPUTS=[f'data_processed/{MEMBER_TABLE}.csv',f'data_processed/{GROUP_TABLE}.csv']
SUMMARY='reports/verified_piste_member_qa_stage54_summary.json'


def exact_signature(element):
    """Exact stored coordinate sequence, invariant to reversal, no rounding."""
    geom=element.get('geometry',[])
    if len(geom)<2:return None
    if not all('lon' in p and 'lat' in p and math.isfinite(p['lon']) and math.isfinite(p['lat']) for p in geom):return None
    points=tuple((p['lon'],p['lat']) for p in geom)
    return min(points,tuple(reversed(points)))


def lifecycle_tags(tags):
    stems=('abandoned','disused','proposed','construction','demolished','removed','was')
    # Retain the literal value, including 'no'; a tag is not a removal rule.
    return {k:v for k,v in tags.items() if k in stems or k.startswith(tuple(s+':' for s in stems)) or k=='piste:status'}


def edges(element):
    nodes=element.get('nodes',[])
    return {tuple(sorted((a,b))) for a,b in zip(nodes,nodes[1:]) if a!=b}


def build(assignments,roles,index,sites):
    if len(assignments)!=71 or not assignments.station_group_id.is_unique:raise ValueError('Preserve all71 groups')
    assigned=assignments[assignments.current_site_correspondence_verified.eq('True')]
    role_index={(r.osm_type,int(r.osm_id)):r._asdict() for r in roles.itertuples(index=False)}
    if len(role_index)!=len(roles):raise ValueError('Duplicate role versions require explicit reconciliation')
    members={int(g.osm_site_relation_id):sites[int(g.osm_site_relation_id)]['selected_downhill_way_ids'] for g in assigned.itertuples()}
    way_ids=sorted({i for ids in members.values() for i in ids})
    duplicates=defaultdict(set); edge_owners=defaultdict(set); source_sites=defaultdict(set)
    for sid,site in sites.items():
        for i in site['selected_downhill_way_ids']:source_sites[i].add(sid)
    for i in way_ids:
        element=index[('way',i)]
        signature=exact_signature(element)
        if signature is not None:duplicates[signature].add(i)
        for edge in edges(element):edge_owners[edge].add(i)
    rows=[]
    for g in assigned.itertuples():
        sid=int(g.osm_site_relation_id)
        for i in members[sid]:
            element=index[('way',i)]; tags=element.get('tags',{}); old=role_index[('way',i)]
            if int(old['osm_version'])!=element['version']:raise ValueError('Source version changed')
            signature=exact_signature(element)
            exact_ids=duplicates.get(signature,set())-{i} if signature is not None else set()
            edge_ids={j for edge in edges(element) for j in edge_owners[edge] if j!=i}
            is_simple=None
            if old['candidate_role']=='way_axis_candidate' and signature is not None:
                is_simple=bool(LineString(signature).is_simple)
            life=lifecycle_tags(tags)
            flags=[]
            if old['geometry_status'] not in ['valid_axis_candidate','valid_standalone_surface_candidate']:flags.append('upstream_geometry_pending')
            if exact_ids:flags.append('exact_reversed_geometry_also_in_other_ids')
            if edge_ids:flags.append('exact_node_edge_also_in_other_ids')
            if is_simple is False:flags.append('self_intersection_or_retracing_requires_review')
            if life:flags.append('literal_lifecycle_or_status_tag_requires_review')
            if old['candidate_role']!='way_axis_candidate':flags.append('surface_or_other_role_not_axis')
            other_sites=source_sites[i]-{sid}
            if other_sites:flags.append('also_referenced_by_other_source_sites')
            rows.append(dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.station_group_name,
                osm_site_relation_id=sid,parent_source_id=old['parent_source_id'],osm_snapshot=old['osm_snapshot'],
                osm_type='way',osm_id=i,osm_version=element['version'],osm_edit_timestamp=element['timestamp'],
                original_name=tags.get('name',''),candidate_role=old['candidate_role'],geometry_status=old['geometry_status'],
                candidate_axis_length_m=old['candidate_axis_length_m'],candidate_standalone_polygon_area_m2=old['candidate_standalone_polygon_area_m2'],
                exact_duplicate_geometry_way_ids='|'.join(map(str,sorted(exact_ids))),
                exact_shared_node_edge_way_ids='|'.join(map(str,sorted(edge_ids))),
                line_is_simple=is_simple,other_source_site_relation_ids='|'.join(map(str,sorted(other_sites))),
                original_lifecycle_tags=json.dumps(life,ensure_ascii=False,sort_keys=True),
                original_review_tags=json.dumps({k:v for k,v in tags.items() if k in ['fixme','note','opening_hours']},ensure_ascii=False,sort_keys=True),
                diagnostic_flags='|'.join(flags),current_site_correspondence_verified=True,
                individual_piste_metric_use_verified=False,historical_scope_verified=False,object_retained=True))
    frame=pd.DataFrame(rows)
    if frame.duplicated(['station_group_id','osm_type','osm_id','osm_version']).any():raise ValueError('Duplicate group member row')
    groups=[]
    for g in assignments.itertuples():
        part=frame[frame.station_group_id.eq(g.station_group_id)]
        verified=g.current_site_correspondence_verified=='True'
        count=lambda mask:int(mask.sum()) if verified else None
        groups.append(dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.station_group_name,
            current_site_correspondence_verified=verified,osm_site_relation_id=g.osm_site_relation_id,
            inspected_downhill_member_count=len(part) if verified else None,
            candidate_axis_count=count(part.candidate_role.eq('way_axis_candidate')),
            explicit_surface_member_count=count(part.candidate_role.eq('explicit_surface_way_candidate')),
            exact_geometry_duplicate_member_count=count(part.exact_duplicate_geometry_way_ids.ne('')),
            exact_edge_shared_member_count=count(part.exact_shared_node_edge_way_ids.ne('')),
            nonsimple_axis_member_count=count(part.line_is_simple.eq(False)),
            literal_lifecycle_tag_member_count=count(part.original_lifecycle_tags.ne('{}')),
            other_source_site_member_count=count(part.other_source_site_relation_ids.ne('')),
            geometry_or_role_pending_member_count=count(~part.geometry_status.isin(['valid_axis_candidate','valid_standalone_surface_candidate'])),
            member_metric_use_verified=False,historical_scope_verified=False,group_retained=True,
            review_status='current_member_diagnostics_only' if verified else g.review_status,
            review_note=('Zero referenced objects is incomplete source coverage, not absence of alpine activity.' if verified and part.empty else 'No full-domain or preentry certification; flags do not automatically remove members.' if verified else g.review_note)))
    return frame,pd.DataFrame(groups)


MEMBER_DEFS={
    'source_id':('Registered derived diagnostic source','identifier'),
    'station_group_id':('Retained group identifier; not commune or lift cluster','identifier'),
    'station_group_name':('Retained name, not sole join key','name'),
    'osm_site_relation_id':('Individually verified current site correspondence','identifier'),
    'parent_source_id':('Original OSM snapshot containing this object version','identifier'),
    'osm_snapshot':('Original current snapshot, not construction date','timestamp'),
    'osm_type':('Original object type','category'),
    'osm_id':('Original type-specific upstream identifier','identifier'),
    'osm_version':('Original version; no silent reconciliation','integer'),
    'osm_edit_timestamp':('Edit time, not proof of creation or preentry scope','timestamp'),
    'original_name':('Literal source name','name'),
    'candidate_role':('Stage49 separate axis/surface review role','category'),
    'geometry_status':('Retained Stage49 geometric diagnostic','category'),
    'candidate_axis_length_m':('Copied object diagnostic, not accepted station kilometres','metres'),
    'candidate_standalone_polygon_area_m2':('Copied explicit standalone surface diagnostic, not full domain area','square metres'),
    'exact_duplicate_geometry_way_ids':('Other IDs with exact forward/reverse coordinate sequence, no tolerance; flag only','identifiers'),
    'exact_shared_node_edge_way_ids':('Other reviewed IDs reusing an exact unordered consecutive node pair; flag only','identifiers'),
    'line_is_simple':('Shapely line simplicity for candidate axes; missing for other roles or missing geometry','boolean'),
    'other_source_site_relation_ids':('Other original site relations referencing same object, not extra independent piste observations','identifiers'),
    'original_lifecycle_tags':('Literal abandonment/disuse/proposal/construction/removal/status tags, not interpreted operating status','JSON'),
    'original_review_tags':('Literal fixme/note/opening_hours for further individual review','JSON'),
    'diagnostic_flags':('Quality flags, not automatic rejection rules','categories'),
    'current_site_correspondence_verified':('True for the parent site; does not certify each member','boolean'),
    'individual_piste_metric_use_verified':('False: no individual final metric acceptance performed','boolean'),
    'historical_scope_verified':('False: no preentry geometry certification','boolean'),
    'object_retained':('True: every referenced downhill object retained','boolean')}
GROUP_DEFS={k:MEMBER_DEFS[k] for k in ['source_id','station_group_id','station_group_name','current_site_correspondence_verified','osm_site_relation_id','historical_scope_verified']}
GROUP_DEFS.update({
    'inspected_downhill_member_count':('Objects inspected; missing for unresolved sites, zero may mean missing membership','count'),
    'candidate_axis_count':('Literal axis candidates, not accepted unique pistes','count'),
    'explicit_surface_member_count':('Explicit surface way members, not axes or total hectares','count'),
    'exact_geometry_duplicate_member_count':('Members with exact coordinate-sequence repetition under distinct IDs','count'),
    'exact_edge_shared_member_count':('Members sharing exact node edges under distinct IDs','count'),
    'nonsimple_axis_member_count':('Candidate axes with self-intersection/retracing requiring individual review','count'),
    'literal_lifecycle_tag_member_count':('Members with literal lifecycle/status tags requiring review','count'),
    'other_source_site_member_count':('Members also referenced by another source site','count'),
    'geometry_or_role_pending_member_count':('Members whose previous geometry/role diagnostic is pending','count'),
    'member_metric_use_verified':('False: object diagnostic is not final profile acceptance','boolean'),
    'group_retained':('True: all71 groups retained','boolean'),
    'review_status':('Diagnostic stage or retained unresolved status','category'),
    'review_note':('Coverage caveat and continuation guidance','text')})


def register(frames):
    path=ROOT/'metadata/data_sources_master.csv'; master=pd.read_csv(path,dtype=str,keep_default_na=False)
    record=dict(source_id=SOURCE,variable_name='verified_site_member_geometry_diagnostics',variable_description='Current verified site members linked to original geometry roles with non-excluding quality flags',source_organisation='Thesis audit of OSM contributors',retrieval_date='2026-10-10',retrieval_method='Offline original keys/versions/SHA; exact geometry/node-edge and literal lifecycle checks',processed_file='|'.join(OUTPUTS),geographic_level='retained station groups and original downhill objects, not municipal outcomes',temporal_resolution='Current original snapshots; not verified before entry',license='Parent OSM ODbL',transformation_applied='Copy prior object diagnostics; no station lengths/area union/repair/automatic deduplication',quality_notes='Site correspondence not member metric acceptance; all groups and objects retained; no assumed active status',notes='Parents DERIVED_PISTE_ASSIGNMENTS_STAGE53|DERIVED_PISTE_GEOMETRY_ROLES_STAGE49; hash lineage in '+SUMMARY)
    if SOURCE not in set(master.source_id):write_csv(pd.concat([master,pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),path)
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False); records=[]
    for table,frame,defs in zip([MEMBER_TABLE,GROUP_TABLE],frames,[MEMBER_DEFS,GROUP_DEFS]):
        if set(frame)!=set(defs):raise ValueError('Every understood diagnostic field requires a definition')
        for column in frame:
            if ((dictionary.table==table)&(dictionary.variable==column)).any():continue
            description,unit=defs[column]
            records.append(dict(variable=column,table=table,description=description,unit=unit,data_type=str(frame[column].dtype),geographic_level='retained group/member diagnostic',temporal_level='current source snapshot',source_id=SOURCE,raw_or_derived='retained source or diagnostic, not final analysis feature',formula='src/descriptive/audit_verified_piste_members_stage54.py; flags only',causal_role='quality audit; never selection on outcomes',missing_share=f'{frame[column].isna().mean():.6f}',notes='Missing unresolved scope is not zero; no exclusion or preentry certification'))
    if records:write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-register',action='store_true');args=parser.parse_args()
    fixed=['src/descriptive/audit_verified_piste_members_stage54.py','data_processed/winter_profile_piste_assignment_stage53.csv','data_processed/winter_profile_piste_geometry_roles.csv','reports/piste_geometry_roles_stage49_summary.json','reports/piste_assignment_stage53_summary.json','src/descriptive/review_piste_candidates_stage53.py','src/descriptive/audit_completed_piste_membership.py','src/descriptive/prepare_piste_group_review.py','config/winter_profile_geometry_roles_decisions_stage49.json']
    parent=json.loads((ROOT/'reports/piste_assignment_stage53_summary.json').read_text(encoding='utf-8'))
    for p,h in {**parent['input_sha256'],**parent['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Prior checkpoint changed: '+p)
    inputs={p:sha(p) for p in fixed}
    index,counts,sites=originals()
    assignments=pd.read_csv(ROOT/fixed[1],dtype=str,keep_default_na=False)
    roles=pd.read_csv(ROOT/fixed[2],dtype=str,keep_default_na=False)
    frames=build(assignments,roles,index,sites)
    member,groups=frames
    state=dict(date='2026-10-10',input_sha256=inputs,retained_group_count=len(groups),verified_site_group_count=int(groups.current_site_correspondence_verified.sum()),member_row_count=len(member),unique_member_object_count=member.osm_id.nunique(),candidate_role_counts=dict(Counter(member.candidate_role)),flag_counts=dict(Counter(flag for cell in member.diagnostic_flags for flag in cell.split('|') if flag)),individual_piste_metric_use_verified=False,group_profile_features_computed=False,automatic_exclusion_applied=False,historical_scope_certified=False)
    target=ROOT/SUMMARY
    if target.exists():
        prior=json.loads(target.read_text(encoding='utf-8'))
        if prior['input_sha256']!=inputs or any(sha(p)!=h for p,h in prior['output_sha256'].items()):raise ValueError('Own checkpoint changed; use a new stage')
    else:
        for path,frame in zip(OUTPUTS,frames):write_csv(frame,ROOT/path)
        state['output_sha256']={p:sha(p) for p in OUTPUTS}
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not args.no_register:register(frames)
    print(json.dumps({k:v for k,v in state.items() if not k.endswith('sha256')},ensure_ascii=False))


if __name__=='__main__':main()
