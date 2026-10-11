"""Versioned explicit original-way correspondence, never proximity assignment.

All 70 groups, old assignment columns and all 854 member rows are retained.
New membership QA is not final metric acceptance or preentry certification.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'data_interim/matplotlib_stage78'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from shapely.geometry import LineString
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.descriptive.audit_verified_piste_members_stage56 import exact_signature, edges, lifecycle_tags, MEMBER_DEFS
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_REMAINING_PISTE_ASSIGNMENTS_STAGE78'
REVIEW_SOURCE = 'DERIVED_REMAINING_PISTE_REVIEW_STAGE78'
SUMMARY = 'reports/remaining_piste_assignments_stage78_summary.json'
OUTPUTS = [
    'data_processed/piste_remaining_review_stage78.csv',
    'data_processed/winter_profile_piste_assignment_stage78.csv',
    'data_processed/winter_profile_piste_members_stage78.csv',
    'data_processed/winter_profile_piste_groups_stage78.csv']
BASE = ['data_processed/winter_profile_piste_assignment_stage60.csv',
        'data_processed/winter_profile_verified_piste_member_qa_stage60.csv']
REGISTRY = ['metadata/data_sources_master.csv','metadata/data_dictionary.csv','logs/data_collection_log.csv']


def read(path):
    return pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)


def digest(frame):
    return hashlib.sha256(frame.to_csv(index=False,lineterminator='\n').encode('utf-8')).hexdigest()


def baseline_registry():
    result = {}
    for path in REGISTRY:
        raw = subprocess.check_output(['git','show','e2a8c4a:'+path],cwd=ROOT)
        from io import StringIO
        prior = pd.read_csv(StringIO(raw.decode('utf-8-sig')),dtype=str,keep_default_na=False)
        actual = read(path)
        if list(actual)!=list(prior) or not actual.iloc[:len(prior)].reset_index(drop=True).equals(prior):
            raise ValueError('Historical registry prefix changed: '+path)
        result[path] = dict(rows=len(prior),row_digest=digest(prior))
    return result


def evidence(ids):
    manifests = []
    for sid in ids:
        found = list((ROOT/'data_external/source_evidence').glob(sid+'_*.metadata.json'))
        if not found:
            raise ValueError('Missing archived independent evidence: '+sid)
        for path in sorted(found):
            meta = json.loads(path.read_text(encoding='utf-8'))
            raw = meta['raw_file']
            if sha(raw)!=meta['sha256']:
                raise ValueError('Original evidence changed: '+raw)
            manifests.append(dict(source_id=sid,metadata_path=path.relative_to(ROOT).as_posix(),
                raw_file=raw,raw_sha256=meta['sha256'],url=meta['url'],retrieval_date=meta['retrieval_date']))
    return manifests


def build(config, inventory, index, sites, roles, old_assignment, old_members):
    scope = {c['station_group_id']:c for c in inventory['cases']}
    accepted = {c['station_group_id']:c for c in config['groups']}
    pending = {c['station_group_id']:c for c in config['pending']}
    if len(scope)!=30 or set(accepted)&set(pending) or set(accepted)|set(pending)!=set(scope):
        raise ValueError('Exactly 30 separate dossiers must be retained')
    if not old_assignment.station_group_id.is_unique or len(old_assignment)!=70:
        raise ValueError('Retain 70 group units')
    if old_members.duplicated(['station_group_id','osm_type','osm_id','osm_version']).any():
        raise ValueError('Prior membership duplicates')
    role_index = {(r.osm_type,int(r.osm_id)):r._asdict() for r in roles.itertuples(index=False)}
    new_rows = []
    for gid, c in accepted.items():
        if len(c['way_ids'])!=len(set(c['way_ids'])):
            raise ValueError('Duplicate curated IDs: '+gid)
        if gid not in set(old_assignment.station_group_id) or not c['scope_note'] or not c['evidence_source_ids']:
            raise ValueError('Identity and independent evidence required')
        if old_members.station_group_id.eq(gid).any():
            raise ValueError('Do not replace previous member rows in this stage')
        case = scope[gid]
        candidates = {r['osm_way_id'] for r in case['candidate_objects']}
        sid = c.get('accepted_site_relation_id')
        if sid is not None and not set(c['way_ids']).issubset(sites[sid]['selected_downhill_way_ids']):
            raise ValueError('Claimed original site does not reference curated ways')
        for way_id in c['way_ids']:
            if way_id not in candidates:
                raise ValueError('Uninspected original object: '+str(way_id))
            element = index[('way',way_id)]
            tags = element.get('tags',{})
            role = role_index[('way',way_id)]
            if tags.get('piste:type')!='downhill' or int(role['osm_version'])!=element['version']:
                raise ValueError('Wrong object identity/version')
            signature = exact_signature(element)
            simple = bool(LineString(signature).is_simple) if signature is not None and role['candidate_role']=='way_axis_candidate' else ''
            life = lifecycle_tags(tags)
            flags = []
            if role['geometry_status'] not in ['valid_axis_candidate','valid_standalone_surface_candidate']:
                flags.append('upstream_geometry_pending')
            if simple is False:flags.append('self_intersection_or_retracing_requires_review')
            if role['candidate_role']!='way_axis_candidate':flags.append('surface_or_other_role_not_axis')
            if life:flags.append('literal_lifecycle_or_status_tag_requires_review')
            history_hint = any(w in tags.get('name','').lower() for w in ['ancienne','abandonn','disused'])
            if history_hint:flags.append('literal_name_history_hint_requires_review')
            if 'itinéraire' in tags.get('name','').lower():flags.append('literal_itinerary_name_not_operating_piste_certificate')
            other_sites = [s for s,site in sites.items() if way_id in site['selected_downhill_way_ids'] and s!=sid]
            new_rows.append(dict(source_id=SOURCE,station_group_id=gid,station_group_name=case['station_group_name'],
                osm_site_relation_id='' if sid is None else sid,parent_source_id=role['parent_source_id'],
                osm_snapshot=role['osm_snapshot'],osm_type='way',osm_id=way_id,osm_version=element['version'],
                osm_edit_timestamp=element['timestamp'],original_name=tags.get('name',''),
                candidate_role=role['candidate_role'],geometry_status=role['geometry_status'],
                candidate_axis_length_m=role['candidate_axis_length_m'],candidate_standalone_polygon_area_m2=role['candidate_standalone_polygon_area_m2'],
                exact_duplicate_geometry_way_ids='',exact_shared_node_edge_way_ids='',line_is_simple=simple,
                other_source_site_relation_ids='|'.join(map(str,other_sites)),original_lifecycle_tags=json.dumps(life,ensure_ascii=False,sort_keys=True),
                original_review_tags=json.dumps({k:v for k,v in tags.items() if k in ['fixme','note','opening_hours']},ensure_ascii=False,sort_keys=True),
                diagnostic_flags='|'.join(flags),current_site_correspondence_verified=sid is not None,
                individual_piste_metric_use_verified=False,historical_scope_verified=False,object_retained=True))
    new_frame = pd.DataFrame(new_rows).reindex(columns=old_members.columns).fillna('').astype(str)
    members = pd.concat([old_members,new_frame],ignore_index=True)
    if members.duplicated(['station_group_id','osm_type','osm_id','osm_version']).any():
        raise ValueError('Duplicate membership rows')
    signatures = defaultdict(set); edge_owners = defaultdict(set)
    for wid in sorted(set(members.osm_id.astype(int))):
        item=index[('way',wid)]; sig=exact_signature(item)
        if sig is not None:signatures[sig].add(wid)
        for edge in edges(item):edge_owners[edge].add(wid)
    # New global QA columns: never rewrite the old diagnostic columns/854 rows.
    memberships=[]; proofs=[]; repetitions=[]; shared=[]; history=[]
    for row in members.itertuples():
        wid=int(row.osm_id); item=index[('way',wid)]; sig=exact_signature(item)
        c=accepted.get(row.station_group_id)
        memberships.append('explicit_reviewed_way_ids' if c else 'retained_stage60_site_members')
        proofs.append('|'.join(c['evidence_source_ids']) if c else row.source_id)
        repetitions.append('|'.join(map(str,sorted(signatures.get(sig,set())-{wid}))))
        shared.append('|'.join(map(str,sorted({j for e in edges(item) for j in edge_owners[e] if j!=wid}))))
        history.append(any(w in item.get('tags',{}).get('name','').lower() for w in ['ancienne','abandonn','disused']))
    members['membership_basis']=memberships
    members['membership_evidence_source_ids']=proofs
    members['current_geometry_correspondence_verified']=True
    members['additional_exact_duplicate_geometry_way_ids']=repetitions
    members['additional_exact_shared_node_edge_way_ids']=shared
    members['literal_name_history_hint']=history
    if not members.iloc[:len(old_members)][old_members.columns].equals(old_members):
        raise ValueError('Old member cells modified')
    assignment=old_assignment.copy(); summaries=[]
    for row in assignment.itertuples():
        gid=row.station_group_id; c=accepted.get(gid); part=members[members.station_group_id.eq(gid)]
        verified=bool(len(part))
        summaries.append(dict(source_id=SOURCE,station_group_id=gid,station_group_name=row.station_group_name,
            geometry_correspondence_verified=verified,new_correspondence_stage78=c is not None,
            member_object_count=len(part) if verified else '',candidate_axis_count=int(part.candidate_role.eq('way_axis_candidate').sum()) if verified else '',
            explicit_surface_count=int(part.candidate_role.eq('explicit_surface_way_candidate').sum()) if verified else '',
            upstream_geometry_pending_count=int((~part.geometry_status.isin(['valid_axis_candidate','valid_standalone_surface_candidate'])).sum()) if verified else '',
            literal_lifecycle_or_name_history_count=int((part.original_lifecycle_tags.ne('{}')|part.literal_name_history_hint.eq(True)).sum()) if verified else '',
            nonsimple_axis_count=int(part.line_is_simple.eq('False').sum()) if verified else '',
            membership_evidence_source_ids='|'.join(c['evidence_source_ids']) if c else '|'.join(sorted(set(part.source_id))) if verified else '',
            full_domain_coverage_verified=False,historical_geometry_verified=False,new_metric_use_verified=False,
            group_retained=True,review_status='explicit_current_network_correspondence' if c else 'retained_previous_current_correspondence' if verified else pending[gid]['review_status'],
            review_note=c['scope_note'] if c else 'Earlier correspondence and metric products unchanged; current proxy not exhaustive or preentry certificate.' if verified else pending[gid]['review_note']))
    groups=pd.DataFrame(summaries)
    extra=groups.set_index('station_group_id')
    for column in ['geometry_correspondence_verified','new_correspondence_stage78','membership_evidence_source_ids','full_domain_coverage_verified','historical_geometry_verified','new_metric_use_verified']:
        assignment['stage78_'+column]=assignment.station_group_id.map(extra[column])
    assignment['stage78_explicit_way_ids']=assignment.station_group_id.map({gid:'|'.join(map(str,c['way_ids'])) for gid,c in accepted.items()}).fillna('')
    assignment['stage78_review_status']=assignment.station_group_id.map(extra.review_status)
    assignment['stage78_review_note']=assignment.station_group_id.map(extra.review_note)
    if not assignment[old_assignment.columns].equals(old_assignment):raise ValueError('Old assignments changed')
    review=[]
    for gid,case in scope.items():
        down=[r for r in case['candidate_objects'] if r['original_tags'].get('piste:type')=='downhill']
        g=extra.loc[gid]
        review.append(dict(station_group_id=gid,station_group_name=case['station_group_name'],
            previous_review_status=case['original_pending_status'],previous_review_note=case['original_note'],
            candidate_downhill_objects_display_window=len(down),candidate_objects_without_site_relation=sum(not r['site_relation_ids'] for r in down),
            minimum_downhill_review_distance_m=min((r['review_distance_m'] for r in down),default=None),
            archived_official_document_count=sum(d['archived'] for d in case['official_documents']),
            geometry_assignment_accepted=gid in accepted,review_status=g.review_status,review_note=g.review_note,source_id=REVIEW_SOURCE))
    return [pd.DataFrame(review),assignment,members,groups]


def render_curated(config, inventory, context):
    cases={c['station_group_id']:c for c in inventory['cases']}
    lifts={c['station_group_id']:c for c in context['cases']}
    outputs=[]
    for n,c in enumerate(config['groups'],1):
        case=cases[c['station_group_id']]; selected={r['osm_way_id']:r for r in case['candidate_objects']}
        fig,ax=plt.subplots(figsize=(11,8)); coords=[]
        for wid in c['way_ids']:
            r=selected[wid]; cs=r['geometry_lv95'];coords.extend(cs)
            ax.plot([p[0]/1000 for p in cs],[p[1]/1000 for p in cs],color='#6a329f' if r['original_tags'].get('area')=='yes' else '#333333',lw=.8)
            mid=cs[len(cs)//2];ax.text(mid[0]/1000,mid[1]/1000,str(wid)+' '+r['original_tags'].get('name',''),fontsize=5)
        x0,x1=min(p[0] for p in coords)-400,max(p[0] for p in coords)+400
        y0,y1=min(p[1] for p in coords)-400,max(p[1] for p in coords)+400
        for lift in lifts[c['station_group_id']]['legacy_lifts']:
            cs_all=[p for line in lift['coordinates_lv95'] for p in line]
            if not any(x0<=p[0]<=x1 and y0<=p[1]<=y1 for p in cs_all):continue
            for cs in lift['coordinates_lv95']:
                ax.plot([p[0]/1000 for p in cs],[p[1]/1000 for p in cs],color='#078445',lw=1.7)
                mid=cs[len(cs)//2];ax.text(mid[0]/1000,mid[1]/1000,'L'+str(lift['fid'])+' '+str(lift['name']),fontsize=7,color='#006b34')
        ax.set_xlim(x0/1000,x1/1000);ax.set_ylim(y0/1000,y1/1000)
        ax.set_aspect('equal');ax.ticklabel_format(useOffset=False,style='plain')
        ax.set_xlabel('Est LV95 (km)');ax.set_ylabel('Nord LV95 (km)')
        ax.set_title(case['station_group_name']+' — identifiants explicitement revus, couverture non exhaustive',fontsize=10)
        path=f'reports/figures/piste_curated_stage78_{n:02d}.png'
        fig.tight_layout();fig.savefig(ROOT/path,dpi=160);plt.close(fig);outputs.append(path)
    return outputs


def register(frames, config, manifest):
    master=read(REGISTRY[0]); rows=[]
    discovery=dict(source_id='DISCOVERY_REMAINING_PISTES_STAGE78',variable_name='official_evidence_discovery',variable_description='Web discovery of literal independent primary official URLs; discovery is not assignment evidence',source_organisation='Thesis research',retrieval_date='2026-10-11',retrieval_method='Tavily unavailable/auth failed; fallback web search; raw pages fetched with robots/TLS controls',processed_file='reports/piste_remaining_discovery_stage78.json',geographic_level='30 remaining station group dossiers',temporal_resolution='Current discovery, not historical footprint',quality_notes='Tavily CLI/reference unavailable; connector attempts failed; search snippets not used as acceptance evidence')
    derived=dict(source_id=SOURCE,variable_name='explicit_current_piste_correspondence',variable_description='Individual original-way correspondence and non-excluding QA, not final terrain/snow features',source_organisation='Thesis audit of OSM and official operators',retrieval_date='2026-10-11',retrieval_method='Explicit pinned way IDs plus independent official operator and geographic review; no name/distance auto matching',processed_file='|'.join(OUTPUTS[1:]),geographic_level='70 retained groups and original OSM objects',temporal_resolution='Current 2026 OSM proxies; not preentry geometry verified',license='Parent OSM ODbL; official evidence rights unchanged',transformation_applied='Copy old19 assignment fields and old854 member rows exactly; add explicit reviewed objects and separate global flags',quality_notes='No groups/communes removed; no fake site IDs, no axes digitised from surfaces; all new metric use pending; no clustering or DiD',notes='Source and output SHA manifest '+SUMMARY)
    review=dict(source_id=REVIEW_SOURCE,variable_name='remaining_piste_review_queue',variable_description='All30 remaining dossiers, candidate diagnostics and explicit review outcome',source_organisation='Thesis audit',retrieval_date='2026-10-11',retrieval_method='Offline original OSM and read-only legacy lift context; individually reviewed official evidence',processed_file=OUTPUTS[0],geographic_level='30 retained group dossiers',temporal_resolution='Current candidate audit',transformation_applied='10km diagnostic window only; no analytical cutoff or absence claim',quality_notes='Legacy1805 lifts kept as context with original fids/UUIDs and unknown upstream date; existing clusters never rebuilt',notes='LOCAL_0f53d91bbb86|OSM_DOWNHILL_SWISS_CURRENT_2026_10_09; '+SUMMARY)
    rows.extend([discovery,derived,review])
    events=json.loads((ROOT/'data_interim/piste_remaining_stage78/evidence_events.json').read_text(encoding='utf-8'))
    for s in json.loads((ROOT/'config/piste_remaining_sources_stage78.json').read_text(encoding='utf-8')):
        docs=[m for m in manifest if m['source_id']==s['source_id']]
        metas=[json.loads((ROOT/m['metadata_path']).read_text(encoding='utf-8')) for m in docs]
        ev=[e for e in events if e['source_id']==s['source_id']]
        errors=[e.get('error','') for e in ev if e.get('status')=='failed']
        row=dict(source_id=s['source_id'],variable_name='official_piste_scope_evidence',variable_description=s['purpose'],source_organisation=s['organisation'],source_page_url=s['url'],retrieval_method='collect_remaining_piste_evidence_stage78.py; actual robots/TLS checks; no bypass',retrieval_date=metas[0]['retrieval_date'][:10] if metas else '2026-10-11' if ev else '',local_raw_file='|'.join(m['raw_file'] for m in metas),geographic_level=s['station_group_id'],temporal_resolution='Current official page/plan; publication dates only where documented',license='Publisher rights; evidence copy, no licence invented',access_conditions='Actual failures retained; no repeat of provider policy refusals',quality_notes='; '.join(errors) or 'HTTP200 original archived with SHA; no complete/preentry geometry certification',confidence_level='official documentary evidence' if metas else 'collection failed, not absence evidence',manual_verification='Individual visual/text review; raw response preserved' if metas else 'No downloaded page',notes='Parent '+s['parent_source_id']+'; metadata/SHA '+('|'.join(m['metadata_path'] for m in docs)))
        rows.append(row)
    fresh=[r for r in rows if r['source_id'] not in set(master.source_id)]
    if fresh:write_csv(pd.concat([master,pd.DataFrame(fresh).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/REGISTRY[0])
    dictionary=read(REGISTRY[1]); additions=[]
    common={'station_group_id':('Stable retained station group, never commune or lift cluster','identifier'),
        'station_group_name':('Original retained name; not sole join key','name'),
        'source_id':('Registered review/derived source identifier','identifier'),
        'review_status':('Explicit correspondence or unresolved review stage, not an exclusion','category'),
        'review_note':('Individual scope proof and remaining uncertainty','text')}
    review_defs={**common,'previous_review_status':('Copied earlier unresolved site status','category'),'previous_review_note':('Earlier site-only reason, retained for comparison','text'),
        'candidate_downhill_objects_display_window':('Original downhill objects within diagnostic10km window; not station pistes','count'),
        'candidate_objects_without_site_relation':('Diagnostic objects not referenced by any site; not automatically accepted','count'),
        'minimum_downhill_review_distance_m':('Nearest candidate diagnostic distance, not assignment rule or access time','metres'),
        'archived_official_document_count':('Earlier source documents present, not evidence completeness score','count'),
        'geometry_assignment_accepted':('Explicit current network correspondence accepted; not final metric use','boolean')}
    extras={'membership_basis':('Explicit reviewed original IDs or untouched earlier site membership; absent site ID not fabricated','category'),
        'membership_evidence_source_ids':('Independent archived official proof IDs or previous-source lineage','identifiers'),
        'current_geometry_correspondence_verified':('Current network identity verified; not every member metric or historical status','boolean'),
        'additional_exact_duplicate_geometry_way_ids':('Global Stage78 exact coordinate duplicates under other IDs; old QA columns unchanged','identifiers'),
        'additional_exact_shared_node_edge_way_ids':('Global Stage78 exact node-edge repetitions; no tolerance, displacement or automatic removal','identifiers'),
        'literal_name_history_hint':('Literal ancienne/abandon/disused substring, flag not operating-status decision','boolean')}
    group_defs={**common,'geometry_correspondence_verified':('At least one currently associated original object, not full coverage','boolean'),
        'new_correspondence_stage78':('New individual network correspondence in Stage78','boolean'),
        'member_object_count':('Associated objects, not independent real pistes; blank unresolved, not zero','count'),
        'candidate_axis_count':('Original axis-role objects, not accepted unique station kilometres','count'),
        'explicit_surface_count':('Original area-role objects, never counted as axes','count'),
        'upstream_geometry_pending_count':('Objects whose old geometric diagnostic remains unresolved','count'),
        'literal_lifecycle_or_name_history_count':('Objects with literal historical/lifecycle flags, not automatically excluded','count'),
        'nonsimple_axis_count':('Original axes with self-intersection/retracing flag','count'),
        'membership_evidence_source_ids':extras['membership_evidence_source_ids'],
        'full_domain_coverage_verified':('False: no complete real-domain inventory certification','boolean'),
        'historical_geometry_verified':('False: current OSM not verified before entry','boolean'),
        'new_metric_use_verified':('False: new membership QA not final terrain/snow metric acceptance','boolean'),
        'group_retained':('True: all70 groups retained without analytic exclusion','boolean')}
    # Old assignment columns inherit actual earlier dictionary definitions.
    assignment_defs={}
    for col in frames[1]:
        if col.startswith('stage78_'):
            key=col[len('stage78_'):]
            assignment_defs[col]=('Explicit original reviewed way IDs, no fabricated relation' ,'identifiers') if key=='explicit_way_ids' else group_defs[key]
        else:
            old=dictionary[(dictionary.table=='winter_profile_piste_assignment_stage60')&dictionary.variable.eq(col)]
            if len(old)!=1:raise ValueError('Need exact prior definition for '+col)
            assignment_defs[col]=(old.iloc[0].description,old.iloc[0].unit)
    member_defs={**MEMBER_DEFS,**extras}
    member_defs['osm_site_relation_id']=('Original verified site identifier only; blank for explicit way mapping without accepted site, never fake','identifier')
    member_defs['current_site_correspondence_verified']=('Previous literal flag retained; newFalse absent accepted site is not missing geometry','boolean')
    for path,frame,defs in zip(OUTPUTS,frames,[review_defs,assignment_defs,member_defs,group_defs]):
        if set(frame)!=set(defs):raise ValueError('Definitions must cover every column: '+path+' '+str(set(frame)^set(defs)))
        table=Path(path).stem
        for col in frame:
            if ((dictionary.table==table)&dictionary.variable.eq(col)).any():continue
            desc,unit=defs[col]
            missing=frame[col].isna()|frame[col].astype(str).eq('')
            additions.append(dict(variable=col,table=table,description=desc,unit=unit,data_type=str(frame[col].dtype),geographic_level='retained group/original object review, not municipal outcome',temporal_level='current source proxy, dates frozen',source_id=REVIEW_SOURCE if path==OUTPUTS[0] else SOURCE,raw_or_derived='retained original or explicit review flag',formula='src/descriptive/build_remaining_piste_assignments_stage78.py; no automatic exclusion',causal_role='coverage/quality audit; not outcome-selected classes or causal predictor certified',missing_share=f'{missing.mean():.6f}',notes='All70 groups kept; axes/surfaces separate; old products unchanged, no new terrain/snow/DiD'))
    if additions:write_csv(pd.concat([dictionary,pd.DataFrame(additions).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/REGISTRY[1])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render-only',action='store_true');parser.add_argument('--no-register',action='store_true');args=parser.parse_args()
    fixed=['config/piste_remaining_assignments_stage78.json','config/piste_remaining_sources_stage78.json',
        'src/descriptive/build_remaining_piste_assignments_stage78.py','src/descriptive/review_remaining_piste_geometry_stage78.py',
        'src/descriptive/review_remaining_lifts_stage78.py','src/data_collection/collect_remaining_piste_evidence_stage78.py',
        'data_interim/piste_remaining_stage78/candidate_inventory.json','data_interim/piste_remaining_stage78/lift_context.json',
        'data_processed/winter_profile_piste_geometry_roles.csv',*BASE,'reports/spass_preentry_profiles_stage77_summary.json']
    config=json.loads((ROOT/fixed[0]).read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/fixed[6]).read_text(encoding='utf-8'));context=json.loads((ROOT/fixed[7]).read_text(encoding='utf-8'))
    if args.render_only:
        render_curated(config,inventory,context);print('20 explicit-ID review maps; no table, registry or assignment changed');return
    prior=baseline_registry()
    index,_,sites=originals()
    frames=build(config,inventory,index,sites,read(fixed[8]),read(BASE[0]),read(BASE[1]))
    all_sources={sid for c in config['groups']+config['pending'] for sid in c.get('evidence_source_ids',[])}
    all_sources|={s['source_id'] for s in json.loads((ROOT/fixed[1]).read_text(encoding='utf-8')) if list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))}
    manifest=evidence(sorted(all_sources))
    inputs={p:sha(p) for p in fixed}
    inputs.update({m['raw_file']:m['raw_sha256'] for m in manifest})
    inputs.update({m['metadata_path']:sha(m['metadata_path']) for m in manifest})
    inputs['data_raw/bahnen-winter_2056.gpkg']=context['source_sha256']
    if sha('data_raw/bahnen-winter_2056.gpkg')!=context['source_sha256']:raise ValueError('Legacy context original changed')
    target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256']!=inputs or any(sha(p)!=h for p,h in state['output_sha256'].items()):raise ValueError('Frozen Stage78 changed: use a new stage')
    else:
        for path,frame in zip(OUTPUTS,frames):write_csv(frame,ROOT/path)
        groups=frames[3]
        state=dict(date='2026-10-11',completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,
            output_sha256={p:sha(p) for p in OUTPUTS},baseline_commit='e2a8c4a',prior_registry=prior,
            retained_group_count=len(groups),review_dossier_count=len(frames[0]),new_correspondence_count=int(groups.new_correspondence_stage78.sum()),
            groups_with_current_correspondence=int(groups.geometry_correspondence_verified.sum()),
            still_unresolved_group_count=int((~groups.geometry_correspondence_verified).sum()),
            retained_prior_member_rows=len(read(BASE[1])),additional_member_rows=len(frames[2])-len(read(BASE[1])),
            unique_added_objects=frames[2].iloc[len(read(BASE[1])):].osm_id.nunique(),
            new_qa_flags=frames[3][frames[3].new_correspondence_stage78.eq(True)][['station_group_id','candidate_axis_count','explicit_surface_count','upstream_geometry_pending_count','literal_lifecycle_or_name_history_count','nonsimple_axis_count']].to_dict('records'),
            official_evidence_manifest=manifest,automatic_assignment=False,group_exclusion=False,
            full_domain_or_preentry_geometry_certified=False,new_terrain_snow_or_clustering_computed=False,
            next_action='Complete10 unresolved dossiers; resolve LaDole boundary choice, historical Wilerallmi-Schwanden connection and lifecycle/metric QA before new geometry/terrain/snow versions')
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not args.no_register:register(frames,config,manifest)
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','prior_registry','official_evidence_manifest','new_qa_flags']},ensure_ascii=False))


if __name__=='__main__':main()
