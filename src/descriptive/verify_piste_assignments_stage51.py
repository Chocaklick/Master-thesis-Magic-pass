"""Curated current site correspondences, not automatic piste metrics/coverage.

--review-only renders original piste/lift/reference geometries for individual
inspection. Acceptance requires the separately recorded manual geographic
finding AND exact official-link/content and original membership checks.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit

os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[2] / 'data_interim/matplotlib_stage51'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from bs4 import BeautifulSoup
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.audit_completed_piste_membership import audit
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

CONFIG = 'config/piste_assignment_cases_stage51.json'
PROTOCOL = 'config/piste_assignment_protocol_decisions_stage51.json'
TABLE = 'winter_profile_piste_assignment_stage51'
OUTPUT = f'data_processed/{TABLE}.csv'
SUMMARY = 'reports/piste_assignment_stage51_summary.json'
SOURCE = 'DERIVED_PISTE_ASSIGNMENTS_STAGE51'
MAP = 'reports/figures/piste_assignment_geographic_review_stage51.png'


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def host(url):
    return urlsplit(url).hostname.removeprefix('www.')


def validate_case(case, group_ids, site, scope_text, known_lift_ids):
    if case['station_group_id'] not in group_ids or case['osm_site_relation_id'] != site['osm_relation_id']:
        raise ValueError('Unknown or changed stable key')
    if not all(marker in scope_text for marker in case['required_operator_markers']):
        raise ValueError('Missing exact independently reviewed official content')
    if not set(case['verified_lift_way_ids']).issubset(known_lift_ids):
        raise ValueError('Corroborated lift is not a retained member')
    if case['geographic_review_status'] != 'reviewed_current_scope_coherent':
        raise ValueError('Require individual geographic review, never name/radius alone')
    if site['cycle_relation_ids']:
        raise ValueError('Recursive cycle requires separate review')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--review-only', action='store_true'); args = parser.parse_args()
    fixed = [CONFIG, PROTOCOL, 'config/piste_operator_evidence_stage51.json', 'config/piste_operator_scope_evidence_stage51.json',
        'config/winter_profile_geometry_roles_decisions_stage49.json', 'data_processed/accessibility_station_groups.csv',
        'data_processed/accessibility_station_access_points.csv', 'reports/piste_official_page_audit_stage49_summary.json',
        'reports/piste_official_page_collection_stage49_summary.json', 'src/descriptive/verify_piste_assignments_stage51.py',
        'reports/piste_site_membership_audit_summary.json']
    inputs = {p:sha(p) for p in fixed}
    protocol = json.loads((ROOT / PROTOCOL).read_text(encoding='utf-8'))
    if protocol['automatic_name_or_distance_acceptance'] or not protocol['all_71_groups_retained']:
        raise ValueError('Require approved retention and no automatic match')
    configs = json.loads((ROOT / fixed[2]).read_text()) + json.loads((ROOT / fixed[3]).read_text())
    documents = {}; records = []
    for source in configs:
        metadata = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
        if not metadata:
            continue  # failed original is retained in canonical log, never invented
        if len(metadata) != 1:
            raise ValueError('Require one original page')
        meta = json.loads(metadata[0].read_text(encoding='utf-8'))
        if meta['url'] != source['url'] or sha(meta['raw_file']) != meta['sha256']:
            raise ValueError('Operator evidence identity/hash changed')
        inputs[meta['raw_file']] = meta['sha256']
        soup = BeautifulSoup((ROOT / meta['raw_file']).read_bytes(), 'html.parser')
        for hidden in soup(['script', 'style']): hidden.decompose()
        documents[source['source_id']] = dict(source_id=source['source_id'], url=source['url'],
            final_url=meta['final_url'], raw_file=meta['raw_file'], sha256=meta['sha256'],
            text=' '.join(soup.get_text(' ', strip=True).split()),
            links=[urljoin(meta['final_url'], a['href']) for a in soup.find_all('a', href=True)])
        records.append(dict(source_id=source['source_id'], variable_name='official_current_piste_operator_evidence',
            variable_description='Official operator identity/components and installations used for individual current OSM site verification',
            source_organisation=source['organisation'], source_page_url=source['url'], retrieval_date=meta['retrieval_date'],
            original_file_name=Path(meta['raw_file']).name, local_raw_file=meta['raw_file'], processed_file=SUMMARY,
            retrieval_method='Exact observed official link; robots checked, archived public HTML and full SHA256',
            geographic_level='Station operator/current installation description', temporal_resolution='Current website, not certified preentry scope',
            license='Provider website terms, no open data licence inferred; no bulk republication of content',
            transformation_applied='Short marker/content and original-link review, no source geometry changes',
            quality_notes='Real full piste coverage/historical scope not assumed; current site corroboration only',
            notes='Parent ' + source['parent_source_id'] + '; sha256=' + meta['sha256']))
    for source in configs:
        if source['source_id'] in documents and source['parent_source_id'] in documents:
            if source['url'] not in documents[source['parent_source_id']]['links']:
                raise ValueError('Scope page not present as literal archived parent link')
    initial = json.loads((ROOT / 'data_interim/current_piste_geometry_collection_checkpoint.json').read_text())
    extra = json.loads((ROOT / 'reports/piste_missing_member_collection_summary.json').read_text())
    for meta in [initial, extra]:
        if sha(meta['raw_file']) != meta['sha256']: raise ValueError('Original OSM hash changed')
        inputs[meta['raw_file']] = meta['sha256']
    first = json.loads((ROOT / initial['raw_file']).read_bytes()); second = json.loads((ROOT / extra['raw_file']).read_bytes())
    frame, inventory = audit(first, second)
    sites = {s['osm_relation_id']:s for s in inventory}
    index = {(e['type'], e['id']):e for e in first['elements'] + second['elements']}
    groups = pd.read_csv(ROOT / fixed[5], keep_default_na=False)
    points = pd.read_csv(ROOT / fixed[6], keep_default_na=False)
    cases = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    if len(groups) != 71 or not groups.station_group_id.is_unique or len({c['station_group_id'] for c in cases}) != len(cases):
        raise ValueError('Group retention/unique case key failure')
    pages = {c['source_id']:c for c in json.loads((ROOT / fixed[7]).read_text(encoding='utf-8'))['cases']}
    official_links = json.loads((ROOT / fixed[8]).read_text(encoding='utf-8'))['group_links']
    transform = Transformer.from_crs(4326, 2056, always_xy=True)
    fig, axes = plt.subplots(2, 3, figsize=(15, 9)); details = []
    for ax, case in zip(axes.flat, cases):
        site = sites[case['osm_site_relation_id']]
        lifts = [index[(m['type'], m['id'])] for m in site['member_references_outside_query']
            if (m['type'], m['id']) in index and index[(m['type'], m['id'])].get('tags', {}).get('aerialway')]
        for ids, color, label in [(site['selected_downhill_way_ids'], '#aaaaaa', 'Objets descente OSM'),
            ([e['id'] for e in lifts], '#1565c0', 'Remontées membres')]:
            for n, identifier in enumerate(ids):
                geom = index[('way', identifier)].get('geometry', [])
                if len(geom) < 2: continue
                x,y = transform.transform([p['lon'] for p in geom], [p['lat'] for p in geom])
                ax.plot([v/1000 for v in x], [v/1000 for v in y], color=color, lw=1, label=label if n == 0 else None)
        selected = points[points.station_group_id.eq(case['station_group_id'])]
        for n,r in enumerate(selected.itertuples()):
            x,y = transform.transform(r.reference_longitude, r.reference_latitude)
            ax.scatter(x/1000,y/1000,color='#d84315',s=30,marker='x',label='Référence conservée' if n == 0 else None)
        ax.set_title(site['name']); ax.set_aspect('equal', adjustable='datalim'); ax.set_xlabel('Est LV95 (km)'); ax.set_ylabel('Nord LV95 (km)')
        ax.ticklabel_format(useOffset=False, style='plain')
        op = documents[case['operator_source_id']]
        config = next(s for s in configs if s['source_id'] == case['operator_source_id'])
        magic = pages[config['parent_source_id']]
        inputs[magic['raw_file']] = sha(magic['raw_file'])
        if not any(l['station_group_id'] == case['station_group_id'] and l['source_id'] == config['parent_source_id'] for l in official_links):
            raise ValueError('Official page/group stable join missing')
        if not any(l.get('url') == op['url'] and l.get('label') == 'Site web' for l in magic['navigation_links']):
            raise ValueError('Operator not the literal official Site web link')
        if host(site['tags']['website']) != host(op['url']): raise ValueError('Original operator host mismatch')
        if not args.review_only:
            validate_case(case, set(groups.station_group_id), site, documents[case['scope_source_id']]['text'], {e['id'] for e in lifts})
        stats = frame[frame.osm_site_relation_id.eq(site['osm_relation_id'])].iloc[0].to_dict()
        details.append(dict(**case, original_site_tags=site['tags'], original_site_version=site['version'],
            original_site_edit_timestamp=site['last_edit_timestamp'], selected_downhill_way_ids=site['selected_downhill_way_ids'],
            lift_way_ids=[e['id'] for e in lifts], source_membership_diagnostics=stats,
            source_geometry_quality_flags=[dict(osm_way_id=e['id'], tags=e['tags']) for e in lifts if any(k in e['tags'] for k in ['fixme','construction_date','year_of_construction'])]))
    axes.flat[-1].axis('off')
    handles, labels = axes.flat[0].get_legend_handles_labels()
    axes.flat[-1].legend(handles,labels,loc='center',fontsize=11)
    fig.suptitle('Contrôle individuel : membres originaux, sans rayon de sélection ni clipping',fontsize=12)
    fig.tight_layout(); (ROOT / MAP).parent.mkdir(parents=True, exist_ok=True)
    if args.review_only or not (ROOT / SUMMARY).exists(): fig.savefig(ROOT / MAP, dpi=140)
    plt.close(fig)
    if args.review_only:
        print('Review map ready; no acceptance/registry written: ' + MAP); return
    rows=[]; reviewed={d['station_group_id']:d for d in details}
    for group in groups.itertuples():
        d=reviewed.get(group.station_group_id); stats=d['source_membership_diagnostics'] if d else {}
        rows.append(dict(station_group_id=group.station_group_id, station_group_name=group.station_group_name,
            component_resort_ids=group.component_resort_ids, current_site_correspondence_verified=bool(d),
            osm_site_relation_id=d['osm_site_relation_id'] if d else '', operator_source_id=d['operator_source_id'] if d else '',
            scope_source_id=d['scope_source_id'] if d else '', downhill_member_object_count=len(d['selected_downhill_way_ids']) if d else '',
            known_lift_member_count=len(d['lift_way_ids']) if d else '', known_nordic_member_count=stats.get('known_nordic_way_member_count',''),
            unresolved_way_relation_count=stats.get('remaining_unresolved_way_relation_count',''), remaining_node_reference_count=stats.get('remaining_node_reference_count',''),
            full_actual_domain_coverage_verified=False, historical_scope_verified=False, individual_piste_metrics_ready=False,
            group_retained=True, review_status='current_site_correspondence_verified_members_require_geometry_qa' if d else 'retained_pending_individual_verification',
            review_note=d['review_note'] if d else 'Not individually reviewed in this first batch; no missing count replaced with zero.', source_id=SOURCE))
    out=pd.DataFrame(rows)
    old=json.loads((ROOT / SUMMARY).read_text()) if (ROOT / SUMMARY).exists() else None
    if old:
        if old['input_sha256'] != inputs or any(sha(p) != h for p,h in old['output_sha256'].items()): raise ValueError('Changed checkpoint; preserve and investigate')
    else:
        write_csv(out, ROOT / OUTPUT)
        state=dict(date='2026-10-09', input_sha256=inputs, output_sha256={p:sha(p) for p in [OUTPUT,MAP]},
            cases=details, archived_operator_sources=[{k:v for k,v in doc.items() if k not in ['text','links']} for doc in documents.values()],
            group_count_retained=71, verified_current_site_correspondences=len(details), final_piste_metrics_computed=False,
            historical_scope_certifications=0, full_actual_domain_coverage_certifications=0, exclusions_applied=False,
            note='Acceptance concerns current site identity/scope correspondence only, not every member geometry, completeness or preentry domain.')
        (ROOT / SUMMARY).write_text(json.dumps(state,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n',encoding='utf-8')
    records.append(dict(source_id=SOURCE, variable_name='current_station_group_osm_site_correspondence',
        variable_description='All71groups with individually documented current identity/operator/geographic review', source_organisation='Thesis reproducible individual review',
        processed_file=OUTPUT, retrieval_date='2026-10-09', retrieval_method='Approved protocol, literal official links/content, original recursive member IDs and manual geographic map review',
        geographic_level='Retained station group, not municipality', temporal_resolution='Current qualified proxy; historical audit pending',
        license='OSM contributors ODbL; official website content terms separate', transformation_applied='No name/radius-only matching, clipping, geometry repair, metrics or group removal', notes='Exact source and output hashes: '+SUMMARY))
    path=ROOT/'metadata/data_sources_master.csv'; master=pd.read_csv(path,dtype=str,keep_default_na=False)
    new=[r for r in records if r['source_id'] not in set(master.source_id)]
    write_csv(pd.concat([master,pd.DataFrame(new).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),path)
    desc=['Stable retained group ID','Original group name','Unchanged components','Verified current site correspondence only',
        'Original OSM site relation ID; blank if unresolved','Official operator source','Official component/installation source',
        'Unique downhill member object count, not distinct pistes/km/full coverage','Known lift members; not altitude/aspect proxy','Known Nordic members, not added to alpine pistes',
        'Unresolved ways/relations diagnostic','Node refs not fetched, not zero unknown nodes',
        'False: full real domain not certified','False: preentry geography not certified','False: member-level axis/surface/topology QA pending',
        'True: every existing group retained','Individual review state','Evidence limitations and remaining work','Derived source key']
    fields=[dict(variable=c,table=TABLE,description=t,unit='diagnostic/identifier/text/count',data_type=str(out[c].dtype),geographic_level='station group',
        temporal_level='current qualified proxy',source_id=SOURCE,raw_or_derived='retained identifier or verification diagnostic',formula='Individual curated case checks; no metric aggregation',
        causal_role='source quality only; not treatment/outcome/profile',missing_share=f'{out[c].eq("").mean():.6f}',notes='All71retained; unknown counts blank, historical/full coverage false') for c,t in zip(out.columns,desc)]
    path=ROOT/'metadata/data_dictionary.csv'; dictionary=pd.read_csv(path,dtype=str,keep_default_na=False)
    if not dictionary.table.eq(TABLE).any(): write_csv(pd.concat([dictionary,pd.DataFrame(fields).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),path)
    print(f'{len(details)} current site correspondences verified / {len(out)} retained groups; no piste metrics, exclusions or historical certification.')


if __name__ == '__main__': main()
