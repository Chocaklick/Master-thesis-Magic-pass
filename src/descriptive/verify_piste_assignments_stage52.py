"""Second individually reviewed lot; cumulative table preserves Stage51.

Correspondences concern current site identity, not full domain, every object,
historical coverage, feature extraction or municipality exposure.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data_interim/matplotlib_stage52'))
sys.path.insert(0,str(ROOT))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pandas as pd
from bs4 import BeautifulSoup
from pyproj import Transformer
from src.descriptive.verify_piste_assignments_stage51 import validate_case, sha, host
from src.descriptive.audit_completed_piste_membership import audit
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

CONFIG='config/piste_assignment_cases_stage52.json'
TABLE='winter_profile_piste_assignment_stage52'
OUTPUT=f'data_processed/{TABLE}.csv'
SUMMARY='reports/piste_assignment_stage52_summary.json'
SOURCE='DERIVED_PISTE_ASSIGNMENTS_STAGE52'
PRIOR='reports/piste_assignment_stage51_summary.json'
PRIOR_TABLE='data_processed/winter_profile_piste_assignment_stage51.csv'
MAPS=[f'reports/figures/piste_assignment_geographic_review_stage52_{i}.png' for i in [1,2]]


def available_document(source):
    matches=list((ROOT/'data_external/source_evidence').glob(source['source_id']+'_*.metadata.json'))
    if not matches:return None
    if len(matches)!=1:raise ValueError('Multiple original source versions require review')
    meta=json.loads(matches[0].read_text(encoding='utf-8'))
    if source['url']!=meta['url'] or sha(meta['raw_file'])!=meta['sha256']:raise ValueError('Source identity/hash changed')
    soup=BeautifulSoup((ROOT/meta['raw_file']).read_bytes(),'html.parser')
    base=soup.find('base',href=True); base_url=urljoin(meta['final_url'],base['href']) if base else meta['final_url']
    for hidden in soup(['script','style']):hidden.decompose()
    return dict(**meta,visible_text=' '.join(soup.get_text(' ',strip=True).split()),
        observed_links=[dict(label=' '.join(a.get_text(' ',strip=True).split()),url=urljoin(base_url,a['href'])) for a in soup.find_all('a',href=True)],
        link_resolution_base=base_url)


def preserve_previous(prior, frame):
    if len(frame)!=71 or not frame.station_group_id.is_unique:raise ValueError('Retain all71unique group IDs')
    if set(prior.station_group_id)!=set(frame.station_group_id):raise ValueError('Group universe changed')
    accepted=prior[prior.current_site_correspondence_verified.eq('True')].set_index('station_group_id')
    current=frame.set_index('station_group_id')
    for key,row in accepted.iterrows():
        if not row.equals(current.loc[key]):raise ValueError('Previously accepted correspondence changed')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review-only',action='store_true');args=parser.parse_args()
    fixed=[CONFIG,'config/piste_operator_evidence_stage52.json','config/piste_operator_scope_evidence_stage52.json',
        'config/piste_assignment_protocol_decisions_stage51.json',PRIOR,PRIOR_TABLE,
        'data_processed/accessibility_station_groups.csv','data_processed/accessibility_station_access_points.csv',
        'reports/piste_official_page_audit_stage49_summary.json','reports/piste_official_page_collection_stage49_summary.json',
        'src/descriptive/verify_piste_assignments_stage52.py','src/descriptive/verify_piste_assignments_stage51.py',
        'src/descriptive/audit_completed_piste_membership.py','reports/piste_site_membership_audit_summary.json',
        'config/winter_profile_geometry_roles_decisions_stage49.json']
    inputs={p:sha(p) for p in fixed}
    old_state=json.loads((ROOT/PRIOR).read_text(encoding='utf-8'))
    for p,h in {**old_state['input_sha256'],**old_state['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Protected Stage51 changed: '+p)
    protocol=json.loads((ROOT/fixed[3]).read_text(encoding='utf-8'))
    if protocol['automatic_name_or_distance_acceptance'] or not protocol['all_71_groups_retained']:raise ValueError('Unapproved protocol')
    sources=json.loads((ROOT/fixed[1]).read_text())+json.loads((ROOT/fixed[2]).read_text())
    cases=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    if len({c['station_group_id'] for c in cases})!=len(cases):raise ValueError('Duplicate reviewed group')
    documents={s['source_id']:available_document(s) for s in sources}
    for doc in documents.values():
        if doc:inputs[doc['raw_file']]=doc['sha256']
    pages={p['source_id']:p for p in json.loads((ROOT/fixed[8]).read_text())['cases']}
    group_links=json.loads((ROOT/fixed[9]).read_text())['group_links']
    for source in sources:
        doc=documents[source['source_id']]
        if not doc:continue
        parent=source['parent_source_id']
        if parent in pages:
            page=pages[parent];inputs[page['raw_file']]=sha(page['raw_file'])
            if not any(x.get('label')=='Site web' and x.get('url')==source['url'] for x in page['navigation_links']):raise ValueError('Not exact official operator link')
            if not any(x['station_group_id']==source['station_group_id'] and x.get('source_id')==parent for x in group_links):raise ValueError('Stable official group join missing')
        else:
            parent_doc=documents.get(parent)
            if not parent_doc or not any(x['url']==source['url'] for x in parent_doc['observed_links']):raise ValueError('Scope URL not a literal parent link including HTML base')
    initial=json.loads((ROOT/'data_interim/current_piste_geometry_collection_checkpoint.json').read_text())
    extra=json.loads((ROOT/'reports/piste_missing_member_collection_summary.json').read_text())
    for meta in [initial,extra]:
        if sha(meta['raw_file'])!=meta['sha256']:raise ValueError('Original geometry changed')
        inputs[meta['raw_file']]=meta['sha256']
    first=json.loads((ROOT/initial['raw_file']).read_bytes());second=json.loads((ROOT/extra['raw_file']).read_bytes())
    counts,inventory=audit(first,second);sites={s['osm_relation_id']:s for s in inventory}
    index={(e['type'],e['id']):e for e in first['elements']+second['elements']}
    prior=pd.read_csv(ROOT/PRIOR_TABLE,dtype=str,keep_default_na=False);frame=prior.copy()
    points=pd.read_csv(ROOT/fixed[7],keep_default_na=False);transform=Transformer.from_crs(4326,2056,always_xy=True)
    details=[]
    for batch,map_path in enumerate(MAPS):
        fig,axes=plt.subplots(2,3,figsize=(15,9))
        for ax,case in zip(axes.flat,cases[batch*6:(batch+1)*6]):
            site=sites[case['osm_site_relation_id']]
            lifts=[index[(m['type'],m['id'])] for m in site['member_references_outside_query'] if (m['type'],m['id']) in index and index[(m['type'],m['id'])].get('tags',{}).get('aerialway')]
            for ids,color in [(site['selected_downhill_way_ids'],'#aaaaaa'),([e['id'] for e in lifts],'#1565c0')]:
                for identifier in ids:
                    geom=index[('way',identifier)].get('geometry',[])
                    if len(geom)<2:continue
                    x,y=transform.transform([p['lon'] for p in geom],[p['lat'] for p in geom])
                    ax.plot([v/1000 for v in x],[v/1000 for v in y],color=color,lw=1)
            for r in points[points.station_group_id.eq(case['station_group_id'])].itertuples():
                x,y=transform.transform(r.reference_longitude,r.reference_latitude)
                ax.scatter(x/1000,y/1000,color='#d84315',marker='x',s=30)
            ax.set_title(site['name']);ax.set_aspect('equal',adjustable='datalim');ax.ticklabel_format(useOffset=False,style='plain')
            ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))
            ax.set_xlabel('Est LV95 (km)');ax.set_ylabel('Nord LV95 (km)')
            op=documents[case['operator_source_id']];scope=documents.get(case['scope_source_id'])
            accepted=case['geographic_review_status']=='reviewed_current_scope_coherent'
            if accepted and not args.review_only:
                if not op or not scope or not case.get('geographic_review_note') or len(case['required_operator_markers'])<2:raise ValueError('Evidence/manual note missing')
                validate_case(case,set(prior.station_group_id),site,scope['visible_text'],{e['id'] for e in lifts})
                url=site['tags'].get('website') or site['tags'].get('url')
                if url and host(url)!=host(op['url']):raise ValueError('Original site operator contradicts evidence')
            stats=counts[counts.osm_site_relation_id.eq(site['osm_relation_id'])].iloc[0].to_dict()
            details.append(dict(**case,current_site_correspondence_verified=accepted,original_site_tags=site['tags'],
                original_site_version=site['version'],original_site_edit_timestamp=site['last_edit_timestamp'],
                selected_downhill_way_ids=site['selected_downhill_way_ids'],lift_way_ids=[e['id'] for e in lifts],
                membership_diagnostics=stats,shared_downhill_way_ids=site['downhill_way_ids_also_in_other_sites'],
                upstream_quality_tags=[dict(osm_way_id=e['id'],tags=e['tags']) for e in lifts if 'fixme' in e.get('tags',{})]))
            key=frame.station_group_id.eq(case['station_group_id'])
            if not args.review_only:
                if accepted:
                    replacements=dict(current_site_correspondence_verified='True',osm_site_relation_id=str(site['osm_relation_id']),
                        operator_source_id=case['operator_source_id'],scope_source_id=case['scope_source_id'],
                        downhill_member_object_count=str(len(site['selected_downhill_way_ids'])),known_lift_member_count=str(len(lifts)),
                        known_nordic_member_count=str(stats['known_nordic_way_member_count']),unresolved_way_relation_count=str(stats['remaining_unresolved_way_relation_count']),
                        remaining_node_reference_count=str(stats['remaining_node_reference_count']),review_status='current_site_correspondence_verified_members_require_geometry_qa')
                    for col,value in replacements.items():frame.loc[key,col]=value
                elif case['geographic_review_status']=='pending':raise ValueError('Unfinished case review; not final checkpoint')
                else:frame.loc[key,'review_status']=case['geographic_review_status']
                frame.loc[key,'review_note']=case['review_note'];frame.loc[key,'source_id']=SOURCE
        fig.suptitle('Contrôle individuel : descentes gris, remontées bleu, références orange. Aucun rayon/clipping.',fontsize=12)
        fig.tight_layout()
        if args.review_only or not (ROOT/SUMMARY).exists():fig.savefig(ROOT/map_path,dpi=140)
        plt.close(fig)
    if args.review_only:print('Two candidate maps rendered; no assignment/registry written.');return
    preserve_previous(prior,frame)
    if frame.group_retained.ne('True').any() or frame.historical_scope_verified.ne('False').any() or frame.full_actual_domain_coverage_verified.ne('False').any() or frame.individual_piste_metrics_ready.ne('False').any():raise ValueError('Unapproved exclusion/certification/metrics')
    old=json.loads((ROOT/SUMMARY).read_text()) if (ROOT/SUMMARY).exists() else None
    if old:
        if old['input_sha256']!=inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):raise ValueError('Changed own checkpoint, preserve/review')
    else:
        write_csv(frame,ROOT/OUTPUT)
        state=dict(date='2026-10-09',input_sha256=inputs,output_sha256={p:sha(p) for p in [OUTPUT,*MAPS]},cases=details,
            retained_group_count=len(frame),prior_verified_count=5,new_verified_count=sum(d['current_site_correspondence_verified'] for d in details),
            total_verified_count=int(frame.current_site_correspondence_verified.eq('True').sum()),
            remaining_group_count=int(frame.current_site_correspondence_verified.ne('True').sum()),
            piste_metrics_computed=False,exclusions_applied=False,historical_or_full_domain_certification=False,
            archived_operator_sources=[{k:v for k,v in doc.items() if k not in ['visible_text','observed_links']} for doc in documents.values() if doc])
        (ROOT/SUMMARY).write_text(json.dumps(state,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n',encoding='utf-8')
    events=json.loads((ROOT/'data_interim/piste_operator_events_stage52.json').read_text(encoding='utf-8'))
    records=[]
    for s in sources:
        doc=documents[s['source_id']];event=next((e for e in reversed(events) if e['source_id']==s['source_id']),None)
        if not doc and not event:continue
        records.append(dict(source_id=s['source_id'],variable_name='official_current_piste_operator_evidence',
            variable_description='Official operator/current installation content or failed source attempt retained',source_organisation=s['organisation'],
            source_page_url=s['url'],retrieval_date=doc['retrieval_date'] if doc else event['timestamp'],
            original_file_name=Path(doc['raw_file']).name if doc else '',local_raw_file=doc['raw_file'] if doc else '',processed_file=SUMMARY,
            retrieval_method='Exact archived official link, robots/TLS checked; raw HTML SHA' if doc else 'Failed public request retained without retry; no content fabricated',
            geographic_level='Station current identity, not municipality',temporal_resolution='Current website; historical scope unverified',
            license='Provider terms, no open data licence inferred',transformation_applied='Individual identity/installation review; no metric extraction',
            quality_notes='Incomplete OSM and historical uncertainty retained' if doc else event.get('error','unavailable'),
            notes='Parent '+s['parent_source_id']+('; sha256='+doc['sha256'] if doc else '; failure in canonical collection log')))
    records.append(dict(source_id=SOURCE,variable_name='cumulative_current_station_group_piste_site_correspondence',
        variable_description='All71retainedgroups, prior5correspondences preserved and second individually verified lot',source_organisation='Thesis individual documented review',
        retrieval_date='2026-10-09',processed_file=OUTPUT,geographic_level='Station group, not municipality',temporal_resolution='Current qualified proxy',
        retrieval_method='Approved protocol; literal official source links/content and manual original geometry review',
        license='OSM contributors ODbL; official website content terms separate',transformation_applied='Stable-ID cumulative overlay; no radius/clipping/exclusion/metrics',notes='Parents '+PRIOR_TABLE+'; exact hashes '+SUMMARY))
    path=ROOT/'metadata/data_sources_master.csv';master=pd.read_csv(path,dtype=str,keep_default_na=False)
    new=[r for r in records if r['source_id'] not in set(master.source_id)]
    write_csv(pd.concat([master,pd.DataFrame(new).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),path)
    path=ROOT/'metadata/data_dictionary.csv';dictionary=pd.read_csv(path,dtype=str,keep_default_na=False)
    if not dictionary.table.eq(TABLE).any():
        definitions=dictionary[dictionary.table.eq('winter_profile_piste_assignment_stage51')].copy()
        if set(definitions.variable)!=set(frame.columns):raise ValueError('Schema/dictionary mismatch')
        definitions['table']=TABLE;definitions['source_id']=SOURCE
        definitions['formula']='Prior71row table overlaid by separately documented Stage52 stable-ID cases; old accepted rows unchanged'
        definitions['missing_share']=[f'{frame[c].eq("").mean():.6f}' for c in definitions.variable]
        write_csv(pd.concat([dictionary,definitions.reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True),path)
    print(f"New {sum(d['current_site_correspondence_verified'] for d in details)}; total {frame.current_site_correspondence_verified.eq('True').sum()}/71; all groups retained, no metrics.")


if __name__=='__main__':main()
