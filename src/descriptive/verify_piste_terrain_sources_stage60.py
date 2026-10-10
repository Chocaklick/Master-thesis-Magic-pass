"""One independently documented current-site overlay; old universe unchanged."""
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit
import pandas as pd
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha,validate_case
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.audit_verified_piste_members_stage56 import build,MEMBER_DEFS,GROUP_DEFS
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_PISTE_ASSIGNMENT_MEMBER_QA_STAGE60'
SUMMARY='reports/piste_terrain_sources_stage60_summary.json'
TABLES=['winter_profile_piste_assignment_stage60','winter_profile_verified_piste_member_qa_stage60','winter_profile_verified_piste_group_qa_stage60']
OUTPUTS=[f'data_processed/{t}.csv' for t in TABLES]


def main():
    fixed=['src/descriptive/verify_piste_terrain_sources_stage60.py','src/data_collection/collect_piste_terrain_stage60.py',
        'config/piste_terrain_sources_stage60.json','config/piste_assignment_case_stage60.json','reports/piste_terrain_discovery_stage60.json',
        'config/piste_assignment_protocol_decisions_stage51.json','data_processed/winter_profile_piste_assignment_stage55.csv',
        'data_processed/winter_profile_piste_geometry_roles.csv','src/descriptive/audit_verified_piste_members_stage56.py',
        'src/descriptive/verify_piste_assignments_stage51.py','src/descriptive/review_piste_candidates_stage53.py',
        'reports/verified_piste_member_qa_stage56_summary.json','data_processed/winter_profile_verified_piste_member_qa_stage56.csv',
        'data_processed/winter_profile_verified_piste_group_qa_stage56.csv','reports/piste_official_page_collection_stage49_summary.json',
        'data_interim/piste_terrain_events_stage60.json','reports/figures/piste_candidates_stage53_6.png']
    inputs={p:sha(p) for p in fixed}
    parent=json.loads((ROOT/fixed[11]).read_text(encoding='utf-8'))
    for p,h in {**parent['input_sha256'],**parent['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Frozen parent changed: '+p)
    protocol=json.loads((ROOT/fixed[5]).read_text(encoding='utf-8'))
    if protocol['automatic_name_or_distance_acceptance']:raise ValueError('Require approved individual protocol')
    configs=json.loads((ROOT/fixed[2]).read_text(encoding='utf-8'))
    docs={};source_records=[]
    for s in configs:
        metas=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if len(metas)!=1:raise ValueError('Require single successful archived original')
        meta=json.loads(metas[0].read_text(encoding='utf-8'))
        if meta['url']!=s['url'] or sha(meta['raw_file'])!=meta['sha256']:raise ValueError('Original page identity/hash changed')
        inputs[meta['raw_file']]=meta['sha256']
        soup=BeautifulSoup((ROOT/meta['raw_file']).read_bytes(),'html.parser')
        for hidden in soup(['script','style']):hidden.decompose()
        docs[s['source_id']]=dict(metadata=meta,text=' '.join(soup.get_text(' ',strip=True).split()))
        source_records.append(dict(source_id=s['source_id'],variable_name='current_station_or_terrain_method_evidence',variable_description=s['purpose'],source_organisation=s['organisation'],source_page_url=s['url'],retrieval_date=meta['retrieval_date'],original_file_name=Path(meta['raw_file']).name,local_raw_file=meta['raw_file'],processed_file=SUMMARY,retrieval_method='Observed URL, robots/TLS, archived original SHA; no snippet used as evidence',geographic_level='Current station identity or algorithm documentation',temporal_resolution='Current source, not preentry geometry',license='Provider terms; no open licence inferred',transformation_applied='Individual source/marker review; no geometry edits or terrain extraction',quality_notes='Archive primary prevails over search; documentation is not method approval',notes='SHA256='+meta['sha256']))
    case=json.loads((ROOT/fixed[3]).read_text(encoding='utf-8'))
    discovery=json.loads((ROOT/fixed[4]).read_text(encoding='utf-8'))
    observed={r['url'] for q in discovery['searches'] for r in q['results']}
    scope=docs[case['scope_source_id']]
    if scope['metadata']['url'] not in observed:raise ValueError('Discovery URL missing')
    old_sources=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    operator=old_sources[old_sources.source_id.eq(case['operator_source_id'])].iloc[0]
    operator_path=operator.local_raw_file
    expected=operator.notes.split('sha256=')[-1]
    if sha(operator_path)!=expected:raise ValueError('Old operator original changed')
    inputs[operator_path]=expected
    if urlsplit(operator.source_page_url).hostname!=urlsplit(scope['metadata']['url']).hostname:raise ValueError('Different official host needs explicit review')
    op_text=BeautifulSoup((ROOT/operator_path).read_bytes(),'html.parser').get_text(' ',strip=True)
    if 'Remontées mécaniques de St-Luc/Chandolin' not in op_text:raise ValueError('Official operator identity absent')
    links=json.loads((ROOT/fixed[14]).read_text(encoding='utf-8'))['group_links']
    # Preserve the existing Magic stable-ID official-link chain; no name join.
    scope_config=json.loads((ROOT/'config/piste_operator_scope_evidence_stage53.json').read_text(encoding='utf-8'))
    parent_id=next(s['parent_source_id'] for s in scope_config if s['source_id']==case['operator_source_id'])
    parent_config=json.loads((ROOT/'config/piste_operator_evidence_stage53.json').read_text(encoding='utf-8'))
    magic_id=next(s['parent_source_id'] for s in parent_config if s['source_id']==parent_id)
    if not any(l['station_group_id']==case['station_group_id'] and l.get('source_id')==magic_id for l in links):raise ValueError('Stable official group chain missing')
    for p in ['config/piste_operator_scope_evidence_stage53.json','config/piste_operator_evidence_stage53.json']:inputs[p]=sha(p)
    index,counts,sites=originals();site=sites[case['osm_site_relation_id']]
    lifts={m['id'] for m in site['member_references_outside_query'] if (m['type'],m['id']) in index and index[(m['type'],m['id'])].get('tags',{}).get('aerialway')}
    prior=pd.read_csv(ROOT/fixed[6],dtype=str,keep_default_na=False)
    validate_case(case,set(prior.station_group_id),site,scope['text'],lifts)
    target_rows=prior.station_group_id.eq(case['station_group_id'])
    if target_rows.sum()!=1 or prior.loc[target_rows,'current_site_correspondence_verified'].iloc[0]!='False':raise ValueError('Require one original pending row')
    frame=prior.copy();stats=counts[counts.osm_site_relation_id.eq(case['osm_site_relation_id'])].iloc[0]
    changes=dict(current_site_correspondence_verified='True',osm_site_relation_id=str(case['osm_site_relation_id']),operator_source_id=case['operator_source_id'],scope_source_id=case['scope_source_id'],downhill_member_object_count=str(len(site['selected_downhill_way_ids'])),known_lift_member_count=str(len(lifts)),known_nordic_member_count=str(stats.known_nordic_way_member_count),unresolved_way_relation_count=str(stats.remaining_unresolved_way_relation_count),remaining_node_reference_count=str(stats.remaining_node_reference_count),review_status='current_site_correspondence_verified_members_require_geometry_qa',review_note=case['review_note'],source_id=SOURCE)
    for k,v in changes.items():frame.loc[target_rows,k]=v
    pd.testing.assert_frame_equal(prior[~target_rows].reset_index(drop=True),frame[~target_rows].reset_index(drop=True),check_exact=True)
    roles=pd.read_csv(ROOT/fixed[7],dtype=str,keep_default_na=False)
    member,groups=build(frame,roles,index,sites)
    for new,p in [(member,fixed[12]),(groups,fixed[13])]:
        old=pd.read_csv(ROOT/p,dtype=str,keep_default_na=False)
        cols=[c for c in old if c!='source_id']
        old=old[old.station_group_id.ne(case['station_group_id'])][cols].reset_index(drop=True)
        unchanged=new[new.station_group_id.ne(case['station_group_id'])][cols].fillna('').astype(str).reset_index(drop=True)
        pd.testing.assert_frame_equal(old,unchanged,check_exact=True)
    member['source_id']=SOURCE;groups['source_id']=SOURCE
    for checkpoint in ['data_interim/current_piste_geometry_collection_checkpoint.json','reports/piste_missing_member_collection_summary.json']:
        meta=json.loads((ROOT/checkpoint).read_text(encoding='utf-8'));inputs[checkpoint]=sha(checkpoint);inputs[meta['raw_file']]=meta['sha256']
    frames=[frame,member,groups]
    state=dict(date='2026-10-10',input_sha256=inputs,group_count=70,verified_correspondence_count=int(frame.current_site_correspondence_verified.eq('True').sum()),unresolved_group_count=int(frame.current_site_correspondence_verified.eq('False').sum()),newly_verified_group=case['station_group_id'],new_downhill_object_count=len(site['selected_downhill_way_ids']),total_member_count=len(member),candidate_role_counts=member.candidate_role.value_counts().to_dict(),geometry_status_counts=member.geometry_status.value_counts().to_dict(),all_other_assignment_and_qa_rows_preserved=True,no_terrain_extraction_or_effects=True,no_automatic_exclusion_or_historical_certification=True,source_metadata=[d['metadata'] for d in docs.values()],algorithm_proposal_documented_not_automatically_selected=True)
    path=ROOT/SUMMARY
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old['input_sha256']!=inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):raise ValueError('Frozen own checkpoint changed')
    else:
        for f,p in zip(frames,OUTPUTS):write_csv(f,ROOT/p)
        state['output_sha256']={p:sha(p) for p in OUTPUTS}
        path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    source_records.extend([dict(source_id='DISCOVERY_PISTE_TERRAIN_STAGE60',variable_name='bounded_station_and_algorithm_url_discovery',variable_description='Four bounded search queries/request IDs/result URLs; discovery only',source_organisation='Tavily connector fallback',retrieval_date='2026-10-10',processed_file=fixed[4],retrieval_method='CLI unavailable; existing connector; no account/install',quality_notes='Search snippets not primary identity/price/algorithm evidence'),dict(source_id=SOURCE,variable_name='current_site_assignment_and_nonexcluding_member_qa',variable_description='One new StLucChandolin current correspondence using approved individual protocol, all other rows preserved',source_organisation='Thesis audit of official operator and OSM contributors',retrieval_date='2026-10-10',processed_file='|'.join(OUTPUTS),geographic_level='70 derived station groups; no commune exposure change',temporal_resolution='Current qualified mapped proxy',license='OSM ODbL and separate website terms',retrieval_method='Archived exact winter installation routes, stable operator chain, original lift IDs and visually reviewed existing map',transformation_applied='Single pending-row overlay; unchanged Stage56 member QA function, no geometry/route edits',quality_notes='No exhaustive/preentry/individual metric acceptance, effects or exclusions',notes='Parents DERIVED_CONNECTED_GROUP_OVERLAY_STAGE55|DERIVED_VERIFIED_PISTE_MEMBER_QA_STAGE56; SHA in '+SUMMARY)])
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    records=[r for r in source_records if r['source_id'] not in set(master.source_id)]
    if records:write_csv(pd.concat([master,pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);rows=[]
    assignment_defs={r.variable:(r.description,r.unit) for r in dictionary[dictionary.table.eq('winter_profile_piste_assignment_stage55')].itertuples()}
    for table,f,defs in zip(TABLES,frames,[assignment_defs,MEMBER_DEFS,GROUP_DEFS]):
        if set(f)!=set(defs):raise ValueError('Every field must be defined')
        for col,(description,unit) in defs.items():
            if ((dictionary.table==table)&(dictionary.variable==col)).any():continue
            rows.append(dict(variable=col,table=table,description=description,unit=unit,data_type=str(f[col].dtype),source_id=SOURCE,geographic_level='retained group or original member',temporal_level='current mapped proxy',raw_or_derived='retained or documented diagnostic',formula='Approved single-row correspondence overlay then original Stage56 build; no geometry repair/exclusions',causal_role='coverage/quality diagnostic, not final preentry feature',missing_share=f'{(f[col].isna()|f[col].eq("")).mean():.6f}',notes='All other rows preserved; current OSM does not prove historical exhaustivity'))
    if rows:write_csv(pd.concat([dictionary,pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','source_metadata']},ensure_ascii=False))


if __name__=='__main__':main()
