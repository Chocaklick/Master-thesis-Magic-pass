"""Six individual dossiers and literal grooming audit, all200 candidates preserved."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from bs4 import BeautifulSoup
from src.descriptive.audit_completed_piste_membership import audit
from src.descriptive.audit_piste_geometry_roles import role
from src.descriptive.check_national_preparation_stage87 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_collection.collect_braunwald_urban_road_stage90 import register
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

SOURCE = 'DERIVED_NATIONAL_PISTE_DOCUMENTARY_REVIEW_STAGE91'
OUTPUTS = {name: 'data_processed/' + name + '.csv' for name in [
    'national_preparation_work_queue_stage91', 'national_piste_review_members_stage91', 'national_grooming_literal_audit_stage91']}
SUMMARY = 'reports/national_piste_documentary_review_stage91_summary.json'
DEFS = {
    'prior_queue_source_id': ('Preserved Stage88 queue source before this additive derived version', 'identifier'),
    'reviewed_osm_site_relation_id': ('Individually examined original site ID, not a name-only match or a new independent domain', 'identifier'),
    'current_geographic_review_status': ('Individual current geographic/identity coherence review; full real or historical coverage remains uncertified', 'category'),
    'current_review_note': ('Manual original map and primary document findings and their explicit limits', 'text'),
    'verified_common_decade_winter': ('Actual ski activity verified in a primary report for this winter; missing when not yet certified, not no ski activity', 'winter label'),
    'activity_evidence_source_id': ('Registered primary ski activity evidence, not filename-based dating', 'identifier'),
    'activity_evidence_page': ('Printed source report page actually read and visually reviewed', 'page number'),
    'braunwald_approved_car_reference_complete': ('True for Braunwald six-city valley car leg only; false for candidates not yet collected, never full city-to-piste time', 'boolean'),
    'osm_site_relation_id': ('Original cached site relation identity, verified separately from listing ID', 'identifier'),
    'osm_way_id': ('Original unique OSM way ID retained without generated substitute', 'identifier'),
    'osm_version': ('Literal source OSM object version, not construction date', 'version'),
    'osm_edit_timestamp': ('Literal edit timestamp, never operational or construction date', 'UTC timestamp'),
    'original_name': ('Literal original object name; blank means not supplied, not a missing way', 'text'),
    'candidate_role': ('Prior axis/surface role convention; explicit surfaces not converted into axes', 'category'),
    'geometry_available': ('Source way contains at least two geometry vertices; does not certify full domain or accept length for models', 'boolean'),
    'original_geometry_sha256': ('SHA256 of canonical JSON of exact original WGS84 source geometry, no moved or created coordinates', 'SHA256'),
    'grooming_literal': ('Original piste:grooming tag verbatim; absent tag remains blank, not ungroomed', 'text'),
    'original_tags_json': ('Full original OSM tags retained verbatim as JSON', 'JSON'),
    'historical_grooming_verified': ('False: present tags do not establish common-decade grooming status', 'boolean'),
    'new_metric_profile_computed': ('False: no new terrain/snow/axis-length profile computed by this dossier audit', 'boolean'),
    'evidence_source_ids': ('Registered individual source IDs used for this documentary review', 'identifiers'),
    'unit_name': ('Original readable group/listing name, not join key', 'text'),
    'scope_layer': ('Existing approved connected group versus provisional national listing dossier', 'category'),
    'member_object_count': ('Unique mapped member way IDs in unit; not piste kilometres or independent resorts', 'count'),
    'grooming_tag_observed_objects': ('Member IDs with a literal nonempty grooming tag; no status inferred when absent', 'count'),
    'grooming_tag_absent_objects': ('Member IDs without literal tag, not presumed ungroomed', 'count'),
    'explicit_backcountry_objects': ('Member IDs literally tagged backcountry/no, not a historical preparation classification', 'count'),
    'grooming_literal_counts_json': ('Counts of exact observed tag strings; diagnostic only, no model-feature or exclusion rule', 'JSON'),
    'additional_grooming_scope_validation_pending': ('True: researcher asked to choose profile scope; no automatic grooming-based mask applied', 'boolean'),
    'historical_scope_verified': ('False: current geometry is only a reviewed proxy, not common-decade geometry certification', 'boolean'),
    'automatic_exclusion': ('Always false: missing history, grooming or geometry never removes a group/candidate', 'boolean'),
}


def main():
    paths = ['src/descriptive/publish_national_piste_review_stage91.py', 'src/descriptive/review_national_piste_dossiers_stage91.py',
             'src/data_collection/collect_national_scope_evidence_stage91.py', 'config/national_scope_sources_stage91.json',
             'config/national_piste_review_cases_stage91.json', 'data_processed/national_preparation_work_queue_stage88.csv',
             'data_processed/winter_profile_piste_members_stage79.csv', 'data_processed/accessibility_station_groups_stage79.csv',
             'data_interim/national_scope_stage91/evidence_events.json', 'data_interim/national_scope_stage91/visual_review_aids.json',
             'reports/braunwald_urban_road_reference_stage90_summary.json']
    inputs = {p: sha(p) for p in paths}
    configured = json.loads((ROOT / paths[3]).read_text(encoding='utf-8'))
    cases = json.loads((ROOT / paths[4]).read_text(encoding='utf-8'))
    events = json.loads((ROOT / paths[8]).read_text(encoding='utf-8'))
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    documents = {}
    source_rows = []
    wanted = {s['source_id'] for s in configured} | {sid for c in cases for sid in c['documentary_source_ids']}
    for sid in sorted(wanted):
        files = list((ROOT / 'data_external/source_evidence').glob(sid + '_*.metadata.json'))
        if len(files) != 1:
            raise ValueError('One real archive required ' + sid)
        m = json.loads(files[0].read_text(encoding='utf-8'))
        if m['source_id'] != sid or m['http_status'] != 200 or sha(m['raw_file']) != m['sha256']:
            raise ValueError('Source identity/outcome/hash changed ' + sid)
        inputs[m['raw_file']] = m['sha256']; inputs[files[0].relative_to(ROOT).as_posix()] = sha(files[0].relative_to(ROOT))
        if m['suffix'] == 'pdf':
            with (ROOT / m['raw_file']).open('rb') as stream:
                if stream.read(5) != b'%PDF-':
                    raise ValueError('PDF signature absent ' + sid)
        documents[sid] = m
    for s in configured:
        m = documents[s['source_id']]
        if s.get('parent_source_id'):
            parent = documents[s['parent_source_id']]
            soup = BeautifulSoup((ROOT / parent['raw_file']).read_text(encoding='utf-8'), 'html.parser')
            links = {urljoin(parent['final_url'], a['href']) for a in soup.find_all('a', href=True)}
            if s['url'] not in links:
                raise ValueError('Actual parent link missing ' + s['source_id'])
        if s['source_id'] not in set(master.source_id):
            source_rows.append(dict(source_id=s['source_id'], variable_name='national_current_scope_or_historical_ski_activity_proof',
                variable_description=s['purpose'], source_organisation=s['organisation'], source_page_url=s['url'],
                retrieval_date=m['retrieval_date'], retrieval_method='Actual checkpointed primary GET, literal parent links or individually verified official search source',
                local_raw_file=m['raw_file'], geographic_level='Operator/domain documentary evidence, not communal outcomes',
                temporal_resolution='Actual stated winter or current document edition; no filename/publication inference',
                license='Publisher rights, no open licence inferred', confidence_level='Actual original SHA/HTTP/signature and individual reading',
                manual_verification='Local plan PDF rendering and original OSM maps individually reviewed; Elm p5/Feldis p10 for actual ski activity; no complete historical footprint certification',
                quality_notes='Evidence only; grooming status and missing features do not automatically exclude stations', notes=SUMMARY))
    if source_rows:
        write_csv(pd.concat([master, pd.DataFrame(source_rows).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    maps = json.loads((ROOT / paths[9]).read_text(encoding='utf-8'))
    for c in cases:
        path = next(m['map_path'] for m in maps if m['resort_id'] == c['resort_id'])
        inputs[path] = sha(path)
    for name in ['avers_official_plan', 'bivio_official_plan', 'flumserberg_official_plan', 'elm_report_page5', 'feldis_report_page10']:
        path = 'data_interim/national_scope_stage91/' + name + '.png'; inputs[path] = sha(path)
    payloads = []
    for path in ['data_interim/current_piste_geometry_collection_checkpoint.json', 'reports/piste_missing_member_collection_summary.json']:
        inputs[path] = sha(path); m = json.loads((ROOT / path).read_text(encoding='utf-8'))
        if sha(m['raw_file']) != m['sha256']:
            raise ValueError('Original OSM source edited')
        inputs[m['raw_file']] = m['sha256']; payloads.append(json.loads((ROOT / m['raw_file']).read_text(encoding='utf-8')))
    _, sites = audit(*payloads)
    sites = {s['osm_relation_id']: s for s in sites}
    index = {(e['type'], e['id']): e for p in payloads for e in p['elements']}
    queue = pd.read_csv(ROOT / paths[5], dtype=str, keep_default_na=False)
    queue['prior_queue_source_id'] = queue.source_id; queue['source_id'] = SOURCE
    for c in ['reviewed_osm_site_relation_id', 'current_geographic_review_status', 'current_review_note',
              'verified_common_decade_winter', 'activity_evidence_source_id', 'activity_evidence_page']:
        queue[c] = ''
    queue['braunwald_approved_car_reference_complete'] = False
    rows = []; units = []
    for c in cases:
        rid = c['resort_id']; site = sites[c['osm_site_relation_id']]
        mask = queue.resort_id.eq(rid)
        if mask.sum() != 1 or str(c['osm_site_relation_id']) not in queue.loc[mask, 'cached_osm_site_name_hint_ids'].iloc[0].split('|'):
            raise ValueError('Exact existing candidate and cached site needed')
        uid = queue.loc[mask, 'preparation_unit_id'].iloc[0]
        queue.loc[mask, ['reviewed_osm_site_relation_id', 'current_geographic_review_status', 'current_review_note']] = [str(c['osm_site_relation_id']), c['current_geographic_review_status'], c['review_note']]
        for name, value in [('verified_common_decade_winter', c['activity_verified_common_winter']),
                            ('activity_evidence_source_id', c['activity_evidence_source_id']), ('activity_evidence_page', c['activity_evidence_page'])]:
            queue.loc[mask, name] = '' if value is None else str(value)
        queue.loc[mask, 'braunwald_approved_car_reference_complete'] = rid == 'braunwald'
        if c['activity_verified_common_winter']:
            queue.loc[mask, 'common_decade_activity_review_status'] = 'primary_ski_activity_verified_population_eligible_full_historical_scope_pending'
        combined = sorted(set(queue.loc[mask, 'documentary_source_ids'].iloc[0].split('|')) | set(c['documentary_source_ids']))
        queue.loc[mask, 'documentary_source_ids'] = '|'.join(i for i in combined if i)
        queue.loc[mask, 'archived_documentary_source_count'] = str(sum(s in documents for s in combined))
        queue.loc[mask, 'next_review_action'] = 'Await grooming profile-scope decision; retain uncertain historical/full-domain coverage, then extend approved spatial methods. No new independent-domain assignment or automatic filter.'
        units.append((uid, queue.loc[mask, 'unit_name'].iloc[0], 'provisional_national_listing_review', site['selected_downhill_way_ids']))
        for wid in site['selected_downhill_way_ids']:
            e = index[('way', wid)]; tags = e.get('tags', {}); geometry = e.get('geometry', [])
            import hashlib
            rows.append(dict(source_id=SOURCE, resort_id=rid, preparation_unit_id=uid, osm_site_relation_id=c['osm_site_relation_id'],
                osm_way_id=wid, osm_version=e['version'], osm_edit_timestamp=e['timestamp'], original_name=tags.get('name', ''),
                candidate_role=role(e), geometry_available=len(geometry) >= 2,
                original_geometry_sha256=hashlib.sha256(json.dumps(geometry, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                grooming_literal=tags.get('piste:grooming', ''), original_tags_json=json.dumps(tags, ensure_ascii=False, sort_keys=True),
                historical_grooming_verified=False, new_metric_profile_computed=False, automatic_exclusion=False,
                evidence_source_ids='|'.join(c['documentary_source_ids'])))
    old_members = pd.read_csv(ROOT / paths[6]); groups = pd.read_csv(ROOT / paths[7])
    for g in groups.itertuples():
        units.append((g.station_group_id, g.station_group_name, 'existing_approved_connected_group', sorted(set(old_members.loc[old_members.station_group_id.eq(g.station_group_id), 'osm_id'].astype(int)))))
    grooming = []
    for uid, name, layer, ids in units:
        literals = [index[('way', i)].get('tags', {}).get('piste:grooming', '') for i in ids]
        counts = pd.Series([s for s in literals if s], dtype=str).value_counts().to_dict()
        grooming.append(dict(source_id=SOURCE, preparation_unit_id=uid, unit_name=name, scope_layer=layer,
            member_object_count=len(ids), grooming_tag_observed_objects=sum(bool(s) for s in literals),
            grooming_tag_absent_objects=literals.count(''), explicit_backcountry_objects=sum(s in ['backcountry', 'no'] for s in literals),
            grooming_literal_counts_json=json.dumps(counts, sort_keys=True), historical_grooming_verified=False,
            historical_scope_verified=False, additional_grooming_scope_validation_pending=True, automatic_exclusion=False))
    frames = dict(zip(OUTPUTS, [queue, pd.DataFrame(rows), pd.DataFrame(grooming)]))
    target = ROOT / SUMMARY
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf-8'))
        if previous['input_sha256'] != inputs or any(sha(p) != h for p, h in previous['output_sha256'].items()):
            raise ValueError('Completed dossier version changed; preserve results')
        print('Six dossier review and literal grooming audit already frozen; no rewriting')
        return
    for table, frame in frames.items():
        write_csv(frame, ROOT / OUTPUTS[table])
    # Reuse registration mechanics, with explicit Stage91 temporal/analytical roles.
    register(SOURCE, dict(variable_name='national_individual_scope_activity_and_grooming_review',
        variable_description='Six individually reviewed current candidate sites, three primary common-decade ski-activity proofs, all200 candidates retained; literal grooming audit of69old+6provisional scopes',
        source_organisation='Thesis from retained OSM/BAV and actual operator/official documents', retrieval_date=datetime.now(timezone.utc).isoformat(),
        processed_file='|'.join(OUTPUTS.values()), geographic_level='Original member way, existing connected group or provisional catalogue listing; never municipality-night duplication',
        temporal_resolution='Current OSM versus separately certified stated winter activity, no inferred past grooming',
        license='OSM ODbL / inherited publisher rights', transformation_applied='Original stable keys and individual source geography review; retain literal tags, no metric mask or independent domain acceptance',
        quality_notes='No clustering, terrain/snow profile, automatic exclusion, current-to-historical grooming inference or old result replacement', notes=SUMMARY),
        frames, ['national_preparation_work_queue_stage88', 'national_similarity_inventory_stage86'], DEFS)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    mask = dictionary.table.isin(OUTPUTS)
    dictionary.loc[mask, 'geographic_level'] = 'National documentary listing/site/member audit, with69existing groups separately retained'
    dictionary.loc[mask, 'temporal_level'] = 'Current tags/geometry versus explicit common-decade winter activity; no historical tag inference'
    dictionary.loc[mask, 'causal_role'] = 'Descriptive preparation and diagnostic only, no model assignment, exclusion or communal exposure'
    dictionary.loc[mask, 'notes'] = 'All200 candidates retained. Grooming absent is not ungroomed; current backcountry not past status. No profiles or domain merges fitted.'
    write_csv(dictionary, ROOT / 'metadata/data_dictionary.csv')
    old = frames['national_grooming_literal_audit_stage91'].query("scope_layer == 'existing_approved_connected_group'")
    state = dict(completed_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
        output_sha256={p: sha(p) for p in OUTPUTS.values()}, candidate_count=200, reviewed_current_site_dossiers=6,
        reviewed_member_objects=len(rows), primary_common_decade_ski_activity_dossiers=3, new_independent_domains_or_physical_profiles_accepted=0,
        actual_new_sources=len(configured), actual_new_collection_events=len(events),
        existing_groups_with_backcountry_objects=int(old.explicit_backcountry_objects.gt(0).sum()), existing_backcountry_member_objects=int(old.explicit_backcountry_objects.sum()),
        grooming_scope_choice_pending=True, no_automatic_exclusion_old_value_replacement_fit_or_group_merge=True)
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in state.items() if k not in ['input_sha256', 'output_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
