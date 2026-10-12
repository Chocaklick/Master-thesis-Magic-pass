"""All200 candidates retained; source preparation is not domain/metric acceptance."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from bs4 import BeautifulSoup
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_NATIONAL_DOCUMENTARY_QUEUE_STAGE88'
OUTPUT = 'data_processed/national_preparation_work_queue_stage88.csv'
SUMMARY = 'reports/national_preparation_work_queue_stage88_summary.json'
CASES = {'avers': [8956633, ['NATIONAL_AVERS_REGION_STAGE88']],
         'bivio': [8956662, ['NATIONAL_BIVIO_OPERATOR_STAGE88']],
         'braunwald': [9051525, ['NATIONAL_BRAUNWALD_WINTER_STAGE88', 'NATIONAL_BRAUNWALD_REPORT_2019_20_STAGE88', 'NATIONAL_BRAUNWALD_FUTURE_NOTICE_STAGE88']],
         'elm': [9051526, ['NATIONAL_ELM_PLAN_STAGE88', 'NATIONAL_ELM_CHANGE_STAGE88']],
         'feldis': [9053171, ['NATIONAL_FELDIS_ASSOCIATION_STAGE88']],
         'flumserberg': [9053173, ['NATIONAL_FLUMSERBERG_PLAN_STAGE88']]}
DEFS = {
    'source_id': ('Registered documentary preparation source', 'identifier'),
    'resort_id': ('Preserved original Swiss catalogue ID, not a new certified independent domain', 'identifier'),
    'preparation_unit_id': ('Unchanged provisional preparation ID from Stage86', 'identifier'),
    'unit_name': ('Original readable label; never sole assignment key', 'text'),
    'legacy_cluster_id': ('Supplied old lift cluster only as lineage, no automatic domain grouping', 'identifier'),
    'possible_existing_group_ids_legacy_hint': ('Existing clusters shared with groups, hint only', 'identifiers'),
    'cached_osm_site_name_hint_ids': ('Already archived exact-name site search hints, not accepted assignments', 'identifiers'),
    'cached_site_hint_count': ('Count of original sites available for documentary review; not physical-domain count', 'count'),
    'documentary_source_ids': ('Literal configured official evidence source IDs including actual failed attempts', 'identifiers'),
    'archived_documentary_source_count': ('Count of actual original archives available for this dossier', 'count'),
    'explicit_operator_ski_cessation_observed': ('True only for verified explicit operator cessation notice; UNKNOWN otherwise, never inferred from daily closed', 'boolean or UNKNOWN'),
    'common_decade_activity_review_status': ('Primary documented2019/20activity for Braunwald, or historical audit still pending', 'category'),
    'current_operation_review_status': ('Explicit cessation notice versus current operational status not yet certified', 'category'),
    'accepted_independent_domain_assignment': ('Always false in this queue; operator/site identity not yet full perimeter/connection review', 'boolean'),
    'new_physical_profile_computed': ('Always false: original candidate data not turned into new altitude/snow profiles by this queue', 'boolean'),
    'automatic_clustering_exclusion': ('Always false: unresolved documents/cells/periods not an automatic sample filter', 'boolean'),
    'next_review_action': ('Unfinished bounded documentary/perimeter/change review to resume without repeating source collection', 'text'),
    'parent_source_ids': ('Registered parent inventory/site sources, not new external acquisitions', 'identifiers'),
}


def main():
    paths = ['src/descriptive/prepare_national_documentary_queue_stage88.py',
             'src/data_collection/collect_national_operator_evidence_stage88.py',
             'config/national_operator_sources_stage88.json',
             'config/national_transboundary_scope_decision_stage88.json',
             'config/national_activity_period_decision_stage88.json',
             'data_processed/national_similarity_inventory_stage86.csv',
             'data_processed/national_similarity_piste_site_inventory_stage85.csv',
             'data_interim/national_preparation_stage88/evidence_events.json']
    inputs = {p: sha(p) for p in paths}
    configured = json.loads((ROOT / paths[2]).read_text(encoding='utf-8'))
    events = json.loads((ROOT / paths[7]).read_text(encoding='utf-8'))
    metadata = {}
    for s in configured:
        files = []
        for p in (ROOT / 'data_external/source_evidence').glob(s['source_id'] + '_*.metadata.json'):
            m = json.loads(p.read_text(encoding='utf-8'))
            if m['source_id'] == s['source_id']:
                files.append((p, m))
        if files:
            if len(files) != 1:
                raise ValueError('Do not silently choose another original source version')
            p, m = files[0]
            if sha(m['raw_file']) != m['sha256'] or m['http_status'] != 200:
                raise ValueError('Original source or HTTP outcome differs')
            with (ROOT / m['raw_file']).open('rb') as stream:
                signature = stream.read(8)
            if s['suffix'] == 'pdf' and not signature.startswith(b'%PDF-'):
                raise ValueError('Not a PDF; do not certify annual-report content')
            metadata[s['source_id']] = m
            inputs[p.relative_to(ROOT).as_posix()] = sha(p.relative_to(ROOT))
            inputs[m['raw_file']] = m['sha256']
    notice = metadata['NATIONAL_BRAUNWALD_WINTER_STAGE88']
    soup = BeautifulSoup((ROOT / notice['raw_file']).read_text(encoding='utf-8'), 'html.parser')
    if 'Eingestellter Skibetrieb' not in soup.get_text(' ', strip=True):
        raise ValueError('No explicit ski cessation evidence; do not infer from daily closed')
    # Historical activity manually checked in the primary annual report, page4,
    # section Winter2019/2020, not inferred from the filename or OSM edit date.
    if 'NATIONAL_BRAUNWALD_REPORT_2019_20_STAGE88' not in metadata:
        raise ValueError('Primary historical activity dossier must remain available')
    inventory = pd.read_csv(ROOT / paths[5], keep_default_na=False)
    candidates = inventory[inventory.within_swiss_preparation_scope & inventory.identity_level.ne('existing_approved_group')]
    sites = pd.read_csv(ROOT / paths[6], dtype=str, keep_default_na=False)
    rows = []
    for r in candidates.itertuples():
        rid = r.component_resort_ids
        if '|' in rid:
            raise ValueError('Queue expects an original provisional listing, not merged domains')
        hints = sorted({int(s.osm_site_relation_id) for s in sites.itertuples() if rid in s.exact_name_listing_hint_ids.split('|')})
        configured_ids = CASES.get(rid, [None, []])[1]
        if rid in CASES and CASES[rid][0] not in hints:
            raise ValueError('Dossier site must be an already archived name-search hint, not invented geometry')
        closed = rid == 'braunwald'
        rows.append(dict(source_id=SOURCE, resort_id=rid, preparation_unit_id=r.preparation_unit_id, unit_name=r.unit_name,
                         legacy_cluster_id=r.cluster_ids_lineage_only,
                         possible_existing_group_ids_legacy_hint=r.possible_existing_group_ids_legacy_cluster_hint,
                         cached_osm_site_name_hint_ids='|'.join(map(str, hints)), cached_site_hint_count=len(hints),
                         documentary_source_ids='|'.join(configured_ids),
                         archived_documentary_source_count=sum(s in metadata for s in configured_ids),
                         explicit_operator_ski_cessation_observed='True' if closed else 'UNKNOWN',
                         common_decade_activity_review_status='primary_activity_verified_2019_20_population_eligible_geometry_pending' if closed else 'historical_ski_activity_not_yet_audited_keep_pending',
                         current_operation_review_status='explicit_current_operator_ski_cessation_notice_exact_timing_detail_refused' if closed else 'not_yet_certified_not_inferred_from_daily_closed',
                         accepted_independent_domain_assignment=False, new_physical_profile_computed=False, automatic_clustering_exclusion=False,
                         next_review_action='Review actual piste/lift scope, links, current-versus-historical changes and ambiguous members before measurements' if configured_ids else 'Find independent primary operator/historical activity proof; examine available cached sites without automatic name/distance assignment',
                         parent_source_ids='DERIVED_NATIONAL_COMPARABLE_CONTEXT_STAGE86|DERIVED_NATIONAL_SIMILARITY_PREPARATION_STAGE85'))
    frame = pd.DataFrame(rows)
    if len(frame) != 200 or not frame.resort_id.is_unique:
        raise ValueError('All200 Swiss candidates must remain in preparation')
    summary = dict(completed_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
                   candidate_count=200, candidate_dossiers_with_archives=int(frame.archived_documentary_source_count.gt(0).sum()),
                   actual_configured_source_count=len(configured), actual_original_archives=len(metadata),
                   actual_collection_event_count=len(events), failed_collection_events=sum(e['status'] == 'failed' for e in events),
                   candidates_with_existing_site_name_hints=int(frame.cached_site_hint_count.gt(0).sum()),
                   no_new_domain_merge_profile_fit_or_automatic_exclusion=True,
                   primary_braunwald_historical_activity_proof=dict(source_id='NATIONAL_BRAUNWALD_REPORT_2019_20_STAGE88',
                                                                  source_report_period='2019-05-01/2020-04-30',
                                                                  page=4, section='Winter2019/2020',
                                                                  finding='Operator reports ski operation in winter2019/2020, including December and January; not an exhaustive ten-winter operations audit'),
                   transboundary_and_population_period_validated=True)
    target = ROOT / SUMMARY
    if target.exists():
        existing = json.loads(target.read_text(encoding='utf-8'))
        if existing['input_sha256'] != inputs or sha(OUTPUT) != existing['output_sha256'][OUTPUT]:
            raise ValueError('Frozen documentary queue differs')
        summary = existing
    else:
        write_csv(frame, ROOT / OUTPUT)
        summary['output_sha256'] = {OUTPUT: sha(OUTPUT)}
        target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    add = []
    for s in configured:
        if s['source_id'] in set(sources.source_id):
            continue
        m = metadata.get(s['source_id']); part = [e for e in events if e['source_id'] == s['source_id']]
        if not part:
            raise ValueError('Every attempted source needs actual provenance')
        last = part[-1]
        record = dict(source_id=s['source_id'], variable_name='national_operator_scope_or_activity_evidence',
                      variable_description=s['purpose'], source_organisation=s['organisation'], source_page_url=s['url'],
                      retrieval_method='Checkpointed official GET; source robots policy respected; no provider-refusal bypass',
                      retrieval_date=m['retrieval_date'] if m else last['timestamp'], local_raw_file=m['raw_file'] if m else '',
                      geographic_level='Literal operator/domain documentation, not commune-night observations',
                      temporal_resolution='Stated current snapshot or annual-report period, not inferred publication date',
                      license='Publisher rights; no licence inferred', confidence_level='Original HTTP archive verified' if m else 'Unavailable: actual provider refusal retained',
                      quality_notes='Evidence only; not complete/historical piste geometry or nonmembership certificate' if m else last['error'],
                      manual_verification='Original SHA/HTTP/signature and primary report page4 checked; no filename-date inference' if m and s['suffix'] == 'pdf' else 'Original SHA/HTTP verified; operative/perimeter statements individually qualified' if m else 'No content read from refused detailed notice',
                      notes='Purpose and actual success/failure in ' + SUMMARY + '; parent=' + s.get('parent_source_id', ''))
        add.append(record)
    if SOURCE not in set(sources.source_id):
        add.append(dict(source_id=SOURCE, variable_name='national_documentary_preparation_queue',
                        variable_description='All200 Swiss provisional listings retained; six dossier starters, source outcomes and original OSM hints distinguished from accepted domains',
                        source_organisation='Thesis preparation from original national inventory and actual operator evidence',
                        retrieval_date='2026-10-12', processed_file=OUTPUT,
                        geographic_level='Provisional catalogue listing, not a fitted independent-domain sample',
                        temporal_resolution='Common2013/14–2022/23activity eligibility/current status kept separate',
                        transformation_applied='StableID queue joins; no automatic name/distance linkage, domain merging, measurement or exclusion',
                        quality_notes='Braunwald eligible on verified2019/20activity, current cessation separated; all unknown historical cases remain pending', notes=SUMMARY))
    if add:
        write_csv(pd.concat([sources, pd.DataFrame(add).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    additions = []
    for c in frame:
        if ((dictionary.table == Path(OUTPUT).stem) & dictionary.variable.eq(c)).any():
            continue
        desc, unit = DEFS[c]
        additions.append(dict(variable=c, table=Path(OUTPUT).stem, description=desc, unit=unit, data_type=str(frame[c].dtype),
                              geographic_level='Provisional source listing not verified independent domain', temporal_level='Common decade and current operational status separately',
                              source_id=SOURCE, raw_or_derived='documentary preparation audit', formula=desc,
                              causal_role='Descriptive preparation only; no predicted membership/effect, causal sample or exclusion',
                              missing_share=f'{frame[c].replace("", float("nan")).isna().mean():.6f}',
                              notes='UNKNOWN means unaudited, not false or no activity; no profile or assignment accepted by this queue'))
    if additions:
        write_csv(pd.concat([dictionary, pd.DataFrame(additions).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')
    print(json.dumps({k: v for k, v in summary.items() if k not in ['input_sha256', 'output_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
