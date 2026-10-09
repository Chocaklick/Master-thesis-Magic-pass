"""All remaining groups reviewed without auto matching, exclusion or metrics.

Only separately curated/manual cases can advance a current-site assignment.
Previous fifteen accepted rows and all frozen checkpoints are preserved.
"""
import json
import sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha, validate_case
from src.descriptive.verify_piste_assignments_stage52 import available_document, preserve_previous
from src.descriptive.review_piste_candidates_stage53 import originals
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

TABLE='winter_profile_piste_assignment_stage53'
OUTPUT=f'data_processed/{TABLE}.csv'
SUMMARY='reports/piste_assignment_stage53_summary.json'
SOURCE='DERIVED_PISTE_ASSIGNMENTS_STAGE53'


def validate_official_links(sources,documents,pages,group_links,discovery_urls=()):
    for source in sources:
        parents=source.get('official_group_links',[dict(parent_source_id=source['parent_source_id'],station_group_id=source['station_group_id'])])
        for parent in parents:
            sid=parent['parent_source_id']
            if sid=='DISCOVERY_PISTE_SOURCE_STAGE53':
                identity=source.get('identity_parent_source_id')
                if source['url'] not in discovery_urls:raise ValueError('Unarchived alternative discovery')
                if source.get('fallback_group_join') is True:
                    if not any(l['station_group_id']==source['station_group_id'] and l.get('source_id') is None for l in group_links):raise ValueError('Fallback stable group join missing')
                elif identity not in pages or not any(l['station_group_id']==source['station_group_id'] and l.get('source_id')==identity for l in group_links):
                    raise ValueError('Alternative stable identity join missing')
            elif sid in pages:
                if not any(n.get('label')=='Site web' and n.get('url')==source['url'] for n in pages[sid]['navigation_links']):
                    raise ValueError('Not exact official URL')
                if not any(l['station_group_id']==parent['station_group_id'] and l.get('source_id')==sid for l in group_links):
                    raise ValueError('Official stable group join missing')
            else:
                doc=documents.get(sid)
                if not doc or not any(l['url']==source['url'] for l in doc['observed_links']):raise ValueError('Not literal archived scope link')


def overlay(prior,cases,sites,documents,candidate_details):
    frame=prior.copy();unresolved=[];accepted=[]
    if len({c['station_group_id'] for c in cases})!=len(cases):raise ValueError('Duplicate curated group')
    by_group={c['station_group_id']:c for c in cases}
    remaining=set(prior.loc[prior.current_site_correspondence_verified.ne('True'),'station_group_id'])
    if set(by_group)!=remaining:raise ValueError('Review universe must equal remaining56groups')
    for row in prior[prior.current_site_correspondence_verified.ne('True')].itertuples():
        case=by_group.get(row.station_group_id)
        if not case:raise ValueError('Every remaining group needs explicit recorded review')
        key=frame.station_group_id.eq(row.station_group_id)
        if case['geographic_review_status']=='reviewed_current_scope_coherent':
            site=sites[case['osm_site_relation_id']]
            detail=next(d for d in candidate_details if d['station_group_id']==row.station_group_id and d['osm_site_relation_id']==case['osm_site_relation_id'])
            op=documents.get(case['operator_source_id']);scope=documents.get(case['scope_source_id'])
            if not op or not scope or len(case['required_operator_markers'])<2 or not case.get('geographic_review_note'):
                raise ValueError('No independent content/manual review')
            if not case['verified_lift_way_ids']:raise ValueError('Need corroborated original installation')
            validate_case(case,set(prior.station_group_id),site,scope['visible_text'],{l['id'] for l in detail['lifts']})
            # A different OSM URL is a documented contradiction, not an automatic
            # exclusion: acceptance requires explicit independently sourced note.
            if (site['tags'].get('website') or site['tags'].get('url')) and not case.get('original_site_url_review_note'):
                raise ValueError('Original site URL needs explicit review')
            stats=detail['membership']
            updates=dict(current_site_correspondence_verified='True',osm_site_relation_id=str(site['osm_relation_id']),
                operator_source_id=case['operator_source_id'],scope_source_id=case['scope_source_id'],
                downhill_member_object_count=str(len(site['selected_downhill_way_ids'])),known_lift_member_count=str(len(detail['lifts'])),
                known_nordic_member_count=str(stats['known_nordic_way_member_count']),
                unresolved_way_relation_count=str(stats['remaining_unresolved_way_relation_count']),
                remaining_node_reference_count=str(stats['remaining_node_reference_count']),
                review_status='current_site_correspondence_verified_members_require_geometry_qa')
            for col,value in updates.items():frame.loc[key,col]=value
            accepted.append(dict(**case,original_site=site,lifts=detail['lifts'],membership=stats,map=detail['map']))
        else:
            if case['geographic_review_status']=='pending':raise ValueError('Explicit unresolved status required')
            frame.loc[key,'review_status']=case['geographic_review_status'];unresolved.append(case)
        frame.loc[key,'review_note']=case['review_note'];frame.loc[key,'source_id']=SOURCE
    preserve_previous(prior,frame)
    for c in ['historical_scope_verified','full_actual_domain_coverage_verified','individual_piste_metrics_ready']:
        if frame[c].ne('False').any():raise ValueError('Unapproved certification/metrics/exclusion')
    if frame.group_retained.ne('True').any():raise ValueError('Group removal')
    return frame,accepted,unresolved


def main():
    fixed=['config/piste_operator_evidence_stage53.json','config/piste_operator_scope_evidence_stage53.json',
        'config/piste_assignment_candidates_stage53.json','config/piste_assignment_cases_stage53.json',
        'src/descriptive/verify_piste_assignments_stage53.py','src/descriptive/review_piste_candidates_stage53.py',
        'src/data_collection/collect_piste_operator_evidence_stage53.py',
        'data_interim/piste_candidate_review_stage53.json','reports/piste_assignment_stage52_summary.json',
        'data_processed/winter_profile_piste_assignment_stage52.csv','config/piste_assignment_protocol_decisions_stage51.json',
        'reports/piste_official_page_audit_stage49_summary.json','reports/piste_official_page_collection_stage49_summary.json']
    deep='config/piste_operator_deep_scope_evidence_stage53.json'
    alternative='config/piste_operator_alternative_evidence_stage53.json'
    discovery='reports/piste_source_discovery_stage53.json'
    inputs={p:sha(p) for p in fixed+[deep,alternative,discovery,'src/data_collection/prepare_piste_scope_queue_stage53.py',
        'src/descriptive/prepare_piste_reviews_stage53.py','config/piste_assignment_verified_cases_stage53.json',
        'src/descriptive/verify_piste_assignments_stage51.py','src/descriptive/verify_piste_assignments_stage52.py',
        'src/descriptive/audit_completed_piste_membership.py','data_processed/accessibility_station_groups.csv',
        'data_processed/accessibility_station_access_points.csv']}
    protected=json.loads((ROOT/fixed[8]).read_text(encoding='utf-8'))
    for path,h in {**protected['input_sha256'],**protected['output_sha256']}.items():
        if sha(path)!=h:raise ValueError('Protected prior checkpoint changed: '+path)
    protocol=json.loads((ROOT/fixed[10]).read_text(encoding='utf-8'))
    if protocol['automatic_name_or_distance_acceptance'] or not protocol['all_71_groups_retained']:raise ValueError('Unapproved protocol')
    sources=sum([json.loads((ROOT/p).read_text(encoding='utf-8')) for p in [fixed[0],fixed[1],deep,alternative]],[])
    documents={s['source_id']:available_document(s) for s in sources}
    pages={p['source_id']:p for p in json.loads((ROOT/fixed[11]).read_text(encoding='utf-8'))['cases']}
    group_links=json.loads((ROOT/fixed[12]).read_text(encoding='utf-8'))['group_links']
    discovered=json.loads((ROOT/discovery).read_text(encoding='utf-8'))
    discovery_urls={r['url'] for q in discovered['records'] for r in q['results']}
    validate_official_links(sources,documents,pages,group_links,discovery_urls)
    for source in sources:
        for parent in source.get('official_group_links',[dict(parent_source_id=source['parent_source_id'])]):
            if parent['parent_source_id'] in pages:
                raw=pages[parent['parent_source_id']]['raw_file'];inputs[raw]=sha(raw)
        if source.get('identity_parent_source_id'):
            raw=pages[source['identity_parent_source_id']]['raw_file'];inputs[raw]=sha(raw)
    for d in documents.values():
        if d:inputs[d['raw_file']]=d['sha256']
    for path in ['data_interim/current_piste_geometry_collection_checkpoint.json','reports/piste_missing_member_collection_summary.json']:
        meta=json.loads((ROOT/path).read_text(encoding='utf-8'));inputs[meta['raw_file']]=meta['sha256']
    index,counts,sites=originals()
    prior=pd.read_csv(ROOT/fixed[9],dtype=str,keep_default_na=False)
    cases=json.loads((ROOT/fixed[3]).read_text(encoding='utf-8'))
    details=json.loads((ROOT/fixed[7]).read_text(encoding='utf-8'))
    frame,accepted,unresolved=overlay(prior,cases,sites,documents,details)
    maps=sorted({d['map'] for d in details})
    events=json.loads((ROOT/'data_interim/piste_operator_events_stage53.json').read_text(encoding='utf-8'))
    old=json.loads((ROOT/SUMMARY).read_text(encoding='utf-8')) if (ROOT/SUMMARY).exists() else None
    if old:
        if old['input_sha256']!=inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):raise ValueError('Own frozen checkpoint changed')
    else:
        write_csv(frame,ROOT/OUTPUT)
        state=dict(date='2026-10-10',input_sha256=inputs,output_sha256={p:sha(p) for p in [OUTPUT,*maps]},
            cases=accepted,unresolved_cases=unresolved,retained_group_count=71,prior_verified_count=15,
            new_verified_count=len(accepted),total_verified_count=15+len(accepted),remaining_group_count=len(unresolved),
            exclusions_applied=False,piste_metrics_computed=False,historical_or_full_domain_certification=False,
            source_documents=[{k:v for k,v in d.items() if k not in ['visible_text','observed_links']} for d in documents.values() if d],
            collection_events=events)
        (ROOT/SUMMARY).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    records=[]
    records.append(dict(source_id='DISCOVERY_PISTE_SOURCE_STAGE53',variable_name='official_source_url_discovery',
        variable_description='Six archived official-domain search queries, result URLs and request IDs; discovery only',
        source_organisation='Tavily search; official primary pages collected separately',retrieval_date='2026-10-10',
        processed_file=discovery,retrieval_method='Advanced search via available connector; CLI unavailable and linked setup skill missing',
        geographic_level='Station source discovery',temporal_resolution='2026-10-10 search index',
        transformation_applied='Keep query, request ID, exact URL and title; no search snippet used as assignment evidence',
        quality_notes='Index not authoritative; each accepted correspondence requires archived exact primary content',
        license='Search/provider terms; no inferred open-data licence'))
    for s in sources:
        d=documents[s['source_id']];ev=[e for e in events if e['source_id']==s['source_id']]
        e=ev[-1] if ev else None
        if not d and not e:raise ValueError('Source not attempted/diagnosed')
        records.append(dict(source_id=s['source_id'],variable_name='official_current_piste_operator_evidence',
            variable_description='Current station operator identity or documented source access failure',source_organisation=s['organisation'],
            source_page_url=s['url'],retrieval_date=d['retrieval_date'] if d else e['timestamp'],
            original_file_name=Path(d['raw_file']).name if d else '',local_raw_file=d['raw_file'] if d else '',processed_file=SUMMARY,
            retrieval_method='Exact archived official link; robots/TLS and original SHA verified' if d else 'Failed or unrequested prior failed host documented',
            geographic_level='Station identity, not municipality',temporal_resolution='Current; preentry scope not certified',
            license='Provider terms; no open licence inferred',transformation_applied='Individual review; no source geometry changes or metrics',
            quality_notes='Incomplete OSM and historical uncertainty retained' if d else e.get('error','unavailable'),
            notes='Parent '+s['parent_source_id']+('; sha256='+d['sha256'] if d else '; events retained')))
    records.append(dict(source_id=SOURCE,variable_name='cumulative_current_station_group_piste_site_correspondence',
        variable_description='All71groups retained, prior15accepted rows unchanged, remaining56documented individually',
        source_organisation='Thesis documented individual review',retrieval_date='2026-10-10',processed_file=OUTPUT,
        geographic_level='Station group; no municipality exposure change',temporal_resolution='Current qualified proxy',
        retrieval_method='Approved option1; official source chain, original membership and individual geometry review',
        license='OSM contributors ODbL; website terms separately',transformation_applied='Stable-ID overlay; no automatic name/distance/radius assignment, exclusion or metrics',
        notes='Parents data_processed/winter_profile_piste_assignment_stage52.csv; hashes '+SUMMARY))
    path=ROOT/'metadata/data_sources_master.csv';master=pd.read_csv(path,dtype=str,keep_default_na=False)
    new=[r for r in records if r['source_id'] not in set(master.source_id)]
    if new:write_csv(pd.concat([master,pd.DataFrame(new).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),path)
    path=ROOT/'metadata/data_dictionary.csv';dictionary=pd.read_csv(path,dtype=str,keep_default_na=False)
    if not dictionary.table.eq(TABLE).any():
        definitions=dictionary[dictionary.table.eq('winter_profile_piste_assignment_stage52')].copy()
        if set(definitions.variable)!=set(frame.columns):raise ValueError('Schema mismatch')
        definitions['table']=TABLE;definitions['source_id']=SOURCE
        definitions['formula']='Prior71row table; preserve15accepted rows exactly, explicit manual56case overlay; unavailable values remain blank'
        definitions['missing_share']=[f'{frame[c].eq("").mean():.6f}' for c in definitions.variable]
        write_csv(pd.concat([dictionary,definitions.reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True),path)
    print(f'New{len(accepted)}; total{15+len(accepted)}/71; unresolved{len(unresolved)}, no exclusion/metrics.')


if __name__=='__main__':main()
