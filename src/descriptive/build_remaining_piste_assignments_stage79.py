"""Seven explicit correspondences after approved overlay; no metric acceptance."""
import hashlib
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data_interim/matplotlib_stage79'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.audit_verified_piste_members_stage56 import exact_signature,edges,lifecycle_tags
from src.descriptive.build_remaining_piste_assignments_stage78 import evidence
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_REMAINING_PISTE_ASSIGNMENTS_STAGE79'
CONFIG='config/piste_remaining_assignments_stage79.json'
SUMMARY='reports/remaining_piste_assignments_stage79_summary.json'
BASE=['data_processed/winter_profile_piste_assignment_stage78.csv',
      'data_processed/winter_profile_piste_members_stage78.csv',
      'data_processed/winter_profile_piste_groups_stage78.csv']
OUTPUTS=['data_processed/winter_profile_piste_assignment_stage79.csv',
         'data_processed/winter_profile_piste_members_stage79.csv',
         'data_processed/winter_profile_piste_groups_stage79.csv',
         'data_processed/piste_remaining_review_stage79.csv']


def read(path):return pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)


def build(config,index,sites,roles,old_assignment,old_members,group_master,bridge):
    approved=json.loads((ROOT/'config/piste_scope_decisions_stage79.json').read_text(encoding='utf-8'))
    decision=approved['connected_group'];parents=set(decision['parent_group_ids']);new=decision['new_derived_group_id']
    accepted={c['station_group_id']:c for c in config['groups']}
    pending={c['station_group_id']:c for c in config['pending']}
    if config['automatic_assignment'] or config['individual_metric_use_authorized']:
        raise ValueError('No automatic assignment/metric use')
    old_pending=set(old_assignment.loc[old_assignment.stage78_geometry_correspondence_verified.eq('False'),'station_group_id'])
    expected=(old_pending-parents)|{new}
    if set(accepted)&set(pending) or set(accepted)|set(pending)!=expected:
        raise ValueError('All nine remaining derived dossiers must survive')
    if len(group_master)!=69 or not group_master.station_group_id.is_unique or len(bridge)!=70:
        raise ValueError('Require approved69-group universe')
    if old_members.station_group_id.isin(parents).any():raise ValueError('Unexpected existing parent members')
    role_index={(r.osm_type,int(r.osm_id)):r._asdict() for r in roles.itertuples(index=False)}
    rows=[]
    for gid,c in accepted.items():
        if gid not in set(group_master.station_group_id) or len(set(c['way_ids']))!=len(c['way_ids']):
            raise ValueError('Unknown identity or repeated curated ID')
        if old_members.station_group_id.eq(gid).any():raise ValueError('Earlier accepted members cannot be replaced')
        sid=c.get('accepted_site_relation_id')
        if sid is not None and not set(c['way_ids']).issubset(sites[sid]['selected_downhill_way_ids']):
            raise ValueError('Fabricated original relation membership')
        for wid in c['way_ids']:
            e=index[('way',wid)];tags=e.get('tags',{});role=role_index[('way',wid)]
            if tags.get('piste:type')!='downhill' or str(e['version'])!=role['osm_version']:
                raise ValueError('Wrong original object/version')
            signature=exact_signature(e)
            simple=bool(LineString(signature).is_simple) if signature is not None and role['candidate_role']=='way_axis_candidate' else ''
            life=lifecycle_tags(tags)
            hint=any(w in tags.get('name','').lower() for w in ['ancienne','abandonn','disused','ehemalig','stillgelegt'])
            flags=[]
            if role['geometry_status'] not in ['valid_axis_candidate','valid_standalone_surface_candidate']:flags.append('upstream_geometry_pending')
            if simple is False:flags.append('self_intersection_or_retracing_requires_review')
            if role['candidate_role']!='way_axis_candidate':flags.append('surface_or_other_role_not_axis')
            if life:flags.append('literal_lifecycle_or_status_tag_requires_review')
            if hint:flags.append('literal_name_history_hint_requires_review')
            if any(w in tags.get('name','').lower() for w in ['itineraire','itinéraire','cross','park']):flags.append('literal_itinerary_or_park_name_not_operating_piste_certificate')
            if any(k in tags for k in ['fixme','note']):flags.append('original_review_note_requires_review')
            row=dict(source_id=SOURCE,station_group_id=gid,station_group_name=group_master.set_index('station_group_id').loc[gid,'station_group_name'],
                osm_site_relation_id='' if sid is None else sid,parent_source_id=role['parent_source_id'],osm_snapshot=role['osm_snapshot'],
                osm_type='way',osm_id=wid,osm_version=e['version'],osm_edit_timestamp=e['timestamp'],original_name=tags.get('name',''),
                candidate_role=role['candidate_role'],geometry_status=role['geometry_status'],candidate_axis_length_m=role['candidate_axis_length_m'],
                candidate_standalone_polygon_area_m2=role['candidate_standalone_polygon_area_m2'],
                exact_duplicate_geometry_way_ids='',exact_shared_node_edge_way_ids='',line_is_simple=simple,
                other_source_site_relation_ids='|'.join(map(str,[s for s,site in sites.items() if wid in site['selected_downhill_way_ids'] and s!=sid])),
                original_lifecycle_tags=json.dumps(life,ensure_ascii=False,sort_keys=True),
                original_review_tags=json.dumps({k:v for k,v in tags.items() if k in ['fixme','note','opening_hours']},ensure_ascii=False,sort_keys=True),
                diagnostic_flags='|'.join(flags),current_site_correspondence_verified=sid is not None,individual_piste_metric_use_verified=False,
                historical_scope_verified=False,object_retained=True,membership_basis='explicit_reviewed_way_ids_stage79',
                membership_evidence_source_ids='|'.join(c['evidence_source_ids']),current_geometry_correspondence_verified=True,
                additional_exact_duplicate_geometry_way_ids='',additional_exact_shared_node_edge_way_ids='',literal_name_history_hint=hint)
            rows.append(row)
    addition=pd.DataFrame(rows).reindex(columns=old_members.columns).fillna('').astype(str)
    members=pd.concat([old_members,addition],ignore_index=True)
    if members.duplicated(['station_group_id','osm_type','osm_id','osm_version']).any():raise ValueError('Duplicate membership')
    if members.osm_id.duplicated().any():raise ValueError('Cross-group original object needs individual validation')
    signatures=defaultdict(set);owners=defaultdict(set)
    for wid in members.osm_id.astype(int):
        e=index[('way',wid)];sig=exact_signature(e)
        if sig is not None:signatures[sig].add(wid)
        for edge in edges(e):owners[edge].add(wid)
    members['stage79_exact_duplicate_geometry_way_ids']=[
        '|'.join(map(str,sorted(signatures.get(exact_signature(index[('way',int(w))]),set())-{int(w)}))) for w in members.osm_id]
    members['stage79_exact_shared_node_edge_way_ids']=[
        '|'.join(map(str,sorted({j for e in edges(index[('way',int(w))]) for j in owners[e] if j!=int(w)}))) for w in members.osm_id]
    members['stage79_scope_note']=members.station_group_id.map({g:c['scope_note'] for g,c in accepted.items()}).fillna('Retained earlier member cells unchanged; see Stage78 evidence and QA')
    pd.testing.assert_frame_equal(members.iloc[:len(old_members)][old_members.columns],old_members)
    assignment=old_assignment[~old_assignment.station_group_id.isin(parents)].copy().reset_index(drop=True)
    combined=old_assignment[old_assignment.station_group_id.eq(decision['parent_group_ids'][0])].iloc[0].to_dict()
    parent_part=old_assignment[old_assignment.station_group_id.isin(parents)]
    for col in ['component_resort_ids']:
        combined[col]='|'.join(sorted({s for cell in parent_part[col] for s in str(cell).split('|') if s}))
    combined.update(station_group_id=new,station_group_name=decision['new_group_name'],
        current_site_correspondence_verified='True',osm_site_relation_id=9196556,
        operator_source_id='WILERALLMI_SCHWANDEN_PLAN_STAGE78',scope_source_id='WILERALLMI_ANNUAL_2023_24',
        downhill_member_object_count=len(accepted[new]['way_ids']),review_status='approved_current_connected_site_correspondence',
        review_note=accepted[new]['scope_note'],source_id=SOURCE)
    assignment=pd.concat([assignment,pd.DataFrame([combined])],ignore_index=True).fillna('')
    summaries=[]
    for g in group_master.itertuples():
        part=members[members.station_group_id.eq(g.station_group_id)];verified=bool(len(part));c=accepted.get(g.station_group_id)
        summaries.append(dict(source_id=SOURCE,station_group_id=g.station_group_id,station_group_name=g.station_group_name,
            geometry_correspondence_verified=verified,new_correspondence_stage79=c is not None,
            parent_station_group_ids=g.stage79_parent_station_group_ids,
            member_object_count=len(part) if verified else '',candidate_axis_count=int(part.candidate_role.eq('way_axis_candidate').sum()) if verified else '',
            explicit_surface_count=int(part.candidate_role.eq('explicit_surface_way_candidate').sum()) if verified else '',
            lifecycle_or_history_hint_count=int((part.original_lifecycle_tags.ne('{}')|part.literal_name_history_hint.eq('True')).sum()) if verified else '',
            original_review_note_count=int(part.original_review_tags.ne('{}').sum()) if verified else '',
            membership_evidence_source_ids='|'.join(c['evidence_source_ids']) if c else '|'.join(sorted(set(part.membership_evidence_source_ids))) if verified else '',
            full_domain_coverage_verified=False,historical_geometry_verified=False,new_metric_use_verified=False,group_retained=True,
            review_status='explicit_current_network_correspondence' if c else 'retained_stage78_correspondence' if verified else pending[g.station_group_id]['review_status'],
            review_note=c['scope_note'] if c else 'Previous60 mapped groups and their original member cells retained; no new metric acceptance.' if verified else pending[g.station_group_id]['review_note']))
    groups=pd.DataFrame(summaries);groupidx=groups.set_index('station_group_id')
    fields=['geometry_correspondence_verified','new_correspondence_stage79','parent_station_group_ids',
            'membership_evidence_source_ids','full_domain_coverage_verified','historical_geometry_verified','new_metric_use_verified','review_status','review_note']
    for col in fields:assignment['stage79_'+col]=assignment.station_group_id.map(groupidx[col])
    assignment['stage79_explicit_way_ids']=assignment.station_group_id.map({g:'|'.join(map(str,c['way_ids'])) for g,c in accepted.items()}).fillna('')
    pd.testing.assert_frame_equal(assignment.iloc[:len(assignment)-1][old_assignment.columns],old_assignment[~old_assignment.station_group_id.isin(parents)].reset_index(drop=True))
    review=groups[groups.station_group_id.isin(expected)].copy()
    if len(review)!=9 or len(groups)!=69:raise ValueError('No dossier or group may disappear')
    return [assignment,members,groups,review]


def render(config,index):
    t=Transformer.from_crs(4326,2056,always_xy=True)
    context=json.loads((ROOT/'data_interim/piste_remaining_stage78/lift_context.json').read_text(encoding='utf-8'))
    lifts={r['fid']:r for c in context['cases'] for r in c['legacy_lifts']}
    for n,c in enumerate(config['groups'],1):
        fig,ax=plt.subplots(figsize=(12,9));allcs=[]
        for wid in c['way_ids']:
            e=index[('way',wid)];cs=[t.transform(p['lon'],p['lat']) for p in e['geometry']];allcs+=cs
            color='#8139aa' if e.get('tags',{}).get('area')=='yes' else '#333333'
            ax.plot([p[0]/1000 for p in cs],[p[1]/1000 for p in cs],color=color,lw=.8)
            mid=cs[len(cs)//2];ax.text(mid[0]/1000,mid[1]/1000,str(wid)+' '+e.get('tags',{}).get('name',''),fontsize=5)
        x0,x1=min(p[0] for p in allcs)-300,max(p[0] for p in allcs)+300
        y0,y1=min(p[1] for p in allcs)-300,max(p[1] for p in allcs)+300
        for lift in lifts.values():
            for cs in lift['coordinates_lv95']:
                if not any(x0<=p[0]<=x1 and y0<=p[1]<=y1 for p in cs):continue
                ax.plot([p[0]/1000 for p in cs],[p[1]/1000 for p in cs],color='#007b37',lw=1.5)
                mid=cs[len(cs)//2];ax.text(mid[0]/1000,mid[1]/1000,str(lift['name']),fontsize=6,color='#007b37')
        ax.set_xlim(x0/1000,x1/1000);ax.set_ylim(y0/1000,y1/1000);ax.set_aspect('equal')
        ax.ticklabel_format(useOffset=False,style='plain');ax.set_title(c['station_group_name']+' — objets revus, métriques non validées',fontsize=11)
        fig.tight_layout();fig.savefig(ROOT/f'reports/figures/piste_curated_stage79_{n:02d}.png',dpi=170);plt.close(fig)


def register(frames,manifest):
    master=read('metadata/data_sources_master.csv');records=[]
    records.append(dict(source_id=SOURCE,variable_name='explicit_piste_correspondence_after_approved_overlay',
        variable_description='Seven explicit original-object mappings;69 retained groups; no metric acceptance',
        source_organisation='Thesis documented audit',retrieval_date='2026-10-11',
        retrieval_method='Pinned original IDs, archived primary operator identity and geographic/visual review',processed_file='|'.join(OUTPUTS),
        geographic_level='69 approved derived groups; original OSM objects, not municipal observations',
        temporal_resolution='Current2026 OSM proxy; Grimentz titled22-23 plan; internal2019 plan dates not publication proof',
        license='Original OSM ODbL; independent documentary publisher rights unchanged',
        transformation_applied='Retain1323 old member cells; append7 explicit networks and separate globalQA; approved70to69group overlay',
        quality_notes='Foreign Dole-Tuffes portions not clipped; uncovered snow/terrain missing. Plans403/robots/404 not bypassed. No historical footprint, complete domain or active status certification',
        notes='Decision config/piste_scope_decisions_stage79.json; sources/checksums '+SUMMARY))
    events=json.loads((ROOT/'data_interim/piste_remaining_stage79/evidence_events.json').read_text(encoding='utf-8'))
    for source in json.loads((ROOT/'config/piste_remaining_sources_stage79.json').read_text(encoding='utf-8')):
        docs=[m for m in manifest if m['source_id']==source['source_id']]
        ev=[r for r in events if r['source_id']==source['source_id']]
        errors=[r.get('error','') for r in ev if r.get('status')=='failed']
        records.append(dict(source_id=source['source_id'],variable_name='official_piste_scope_evidence',
            variable_description=source['purpose'],source_organisation=source['organisation'],source_page_url=source['url'],
            retrieval_method='Versioned resumable collector; actual robots/TLS; no bypass; cached originals SHA verified',
            retrieval_date=docs[0]['retrieval_date'][:10] if docs else ev[-1]['timestamp'][:10] if ev else '',
            local_raw_file='|'.join(m['raw_file'] for m in docs),geographic_level='Exact documented operator/domain; no municipality-level observations',
            temporal_resolution='Source-stated current/historical scope; no inferred publication date',
            license='Publisher rights; no licence inferred',access_conditions='Actual refusals retained without alternate-channel retries',
            quality_notes='; '.join(errors) if errors else 'Original HTTP response archived; not exhaustive/preentry footprint certificate',
            confidence_level='Archived independent primary evidence' if docs else 'Collection failed; no absence claim',
            notes='Parent '+source['parent_source_id']+'; '+('|'.join(m['metadata_path'] for m in docs))))
    fresh=[r for r in records if r['source_id'] not in set(master.source_id)]
    if fresh:write_csv(pd.concat([master,pd.DataFrame(fresh).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=read('metadata/data_dictionary.csv');add=[]
    explicit={
        'stage79_exact_duplicate_geometry_way_ids':('Exact coordinate duplicates across retained original objects; oldStage78QA not overwritten','identifiers'),
        'stage79_exact_shared_node_edge_way_ids':('Exact shared original node edges across all current retained objects; no tolerance or automatic removal','identifiers'),
        'stage79_scope_note':('Individual documented correspondence scope; metric use and operating/historical coverage still pending','text'),
        'new_correspondence_stage79':('New explicit current correspondence inStage79, not new completed snow/terrain profile','boolean'),
        'parent_station_group_ids':('All preserved Stage55 parent IDs; Wilerallmi andSchwanden combined after user approval','identifiers'),
        'lifecycle_or_history_hint_count':('Objects with literal lifecycle tags or historical names; flags not automatic exclusions','count'),
        'original_review_note_count':('Objects with original note/fixme/opening_hours tags requiring individual QA; not automatic removal','count'),
        'explicit_way_ids':('Manually pinned original OSM way IDs; no fabricated site relation or proximity assignment','identifiers'),
    }
    parent_tables=[Path(p).stem for p in BASE]+[Path(BASE[2]).stem]
    group_defs=dictionary[dictionary.table.eq(Path(BASE[2]).stem)]
    for path,frame,parent_table in zip(OUTPUTS,frames,parent_tables):
        for col in frame:
            table=Path(path).stem
            if ((dictionary.table==table)&dictionary.variable.eq(col)).any():continue
            key=col[len('stage79_'):] if col.startswith('stage79_') and path==OUTPUTS[0] else col
            if col in explicit or key in explicit:
                desc,unit=explicit.get(col,explicit.get(key));rec=dict(description=desc,unit=unit,
                    geographic_level='Group or original-object audit',temporal_level='Frozen current source proxy',raw_or_derived='documented correspondence/QA',
                    causal_role='Geometry quality/coverage; not post-outcome-selected predictor or causal estimate')
            else:
                parent=group_defs if col.startswith('stage79_') and path==OUTPUTS[0] else dictionary[dictionary.table.eq(parent_table)]
                old=parent[parent.variable.eq(key)]
                if len(old)!=1:raise ValueError('Missing verified dictionary definition: '+table+':'+col)
                rec=old.iloc[0].to_dict()
            rec.update(variable=col,table=table,source_id=SOURCE,data_type=str(frame[col].dtype),
                missing_share=f"{(frame[col].isna()|frame[col].astype(str).eq('')).mean():.6f}",
                formula='src/descriptive/build_remaining_piste_assignments_stage79.py; explicit reviewed IDs, no automatic filter',
                notes='Parent '+parent_table+'; all69groups retained; current membership not final metric/historical acceptance; '+SUMMARY)
            add.append(rec)
    if add:write_csv(pd.concat([dictionary,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    config=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'));index,_,sites=originals()
    fixed=[CONFIG,'config/piste_scope_decisions_stage79.json','config/piste_remaining_sources_stage79.json',
        'src/descriptive/build_remaining_piste_assignments_stage79.py','src/descriptive/prepare_remaining_review_maps_stage79.py',
        'src/data_collection/collect_remaining_piste_evidence_stage79.py',*BASE,
        'data_processed/winter_profile_piste_geometry_roles.csv','data_processed/accessibility_station_groups_stage79.csv',
        'data_processed/station_group_parent_bridge_stage79.csv','reports/wilerallmi_schwanden_regrouping_stage79_summary.json']
    frames=build(config,index,sites,read(fixed[9]),read(BASE[0]),read(BASE[1]),read(fixed[10]),read(fixed[11]))
    source_ids={sid for c in config['groups'] for sid in c['evidence_source_ids']}
    source_ids|={s['source_id'] for s in json.loads((ROOT/fixed[2]).read_text(encoding='utf-8')) if list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))}
    manifest=evidence(sorted(source_ids));inputs={p:sha(p) for p in fixed}
    for m in manifest:inputs[m['raw_file']]=m['raw_sha256'];inputs[m['metadata_path']]=sha(m['metadata_path'])
    target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256']!=inputs or any(sha(p)!=h for p,h in state['output_sha256'].items()):raise ValueError('FrozenStage79 changed: use new stage')
    else:
        for path,frame in zip(OUTPUTS,frames):write_csv(frame,ROOT/path)
        state=dict(date='2026-10-11',completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,
            output_sha256={p:sha(p) for p in OUTPUTS},retained_group_count=len(frames[2]),groups_with_geometry=int(frames[2].geometry_correspondence_verified.sum()),
            new_correspondence_count=len(config['groups']),pending_group_count=len(config['pending']),old_member_rows_retained=len(read(BASE[1])),
            additional_member_rows=len(frames[1])-len(read(BASE[1])),total_member_rows=len(frames[1]),
            new_group_counts=frames[2][frames[2].new_correspondence_stage79][['station_group_id','member_object_count','candidate_axis_count','explicit_surface_count','lifecycle_or_history_hint_count','original_review_note_count']].to_dict('records'),
            official_evidence_manifest=manifest,automatic_assignment=False,automatic_group_exclusion=False,full_domain_coverage_certified=False,
            new_snow_terrain_profiles_or_effects_computed=False,
            next_action='AuditLaBrayehistoricalfootprint andRiffenmattgeoreferencedpistes; approve metric-use rule for ambiguous lifecycle/itinerary axes before new physical profiles')
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    register(frames,manifest);render(config,index)
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','official_evidence_manifest','new_group_counts']},ensure_ascii=False))


if __name__=='__main__':main()
