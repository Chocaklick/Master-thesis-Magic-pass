"""Separate late primary evidence and literal QA; no frozen-stage edits or filters."""
import json
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from pypdf import PdfReader
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_PISTE_HISTORICAL_QA_STAGE79'
CONFIG = 'config/piste_historical_followup_stage79.json'
CLAIMS = 'config/piste_historical_claims_stage79.json'
OUTPUTS = ['data_processed/piste_historical_claims_stage79.csv',
           'data_processed/piste_flagged_objects_stage79.csv']
SUMMARY = 'reports/piste_historical_qa_stage79_summary.json'


def read(path):
    return pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)


def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC', text).split()).casefold()


DEFS = {
    'claim_id': ('Stable derived identifier of a manually reviewed primary-document claim', 'identifier'),
    'source_id': ('Registered documentary source, or derivation source for the QA table', 'identifier'),
    'pdf_page': ('One-based physical PDF page checked in text and rendered view, not an inferred publication date', 'page'),
    'finding': ('Paraphrased observed statement, without extending its source scope', 'text'),
    'scope_limit': ('What this documentary finding does not establish', 'text'),
    'operating_calendar_or_geometry_changed': ('Always false: these claims do not alter treatment calendars or geometry assignments', 'boolean'),
    'source_url': ('Actual archived requested URL of the primary document', 'URL'),
    'raw_file': ('Immutable project-relative original documentary file', 'path'),
    'raw_sha256': ('Streaming SHA256 of the archived original', 'SHA256'),
    'station_group_id': ('Approved derived group ID, original IDs retained in the separate lineage', 'identifier'),
    'station_group_name': ('Retained descriptive name, never the sole join key', 'text'),
    'osm_id': ('Original OSM way identifier, not invented or geocoded from a name', 'identifier'),
    'osm_version': ('Original archived OSM object version', 'count'),
    'original_name': ('Literal original OSM name, historical hints not treated as dated closure proof', 'text'),
    'candidate_role': ('Original axis/surface candidate role; surfaces never become axes', 'category'),
    'geometry_status': ('Existing original geometry validity diagnosis, not an operating certificate', 'category'),
    'original_lifecycle_tags': ('Literal preserved lifecycle/status tags as JSON; not automatic exclusions', 'JSON'),
    'original_review_tags': ('Literal preserved note/fixme/opening_hours tags as JSON', 'JSON'),
    'literal_name_history_hint': ('Existing derived flag for an old/abandoned name, not verified temporal history', 'boolean'),
    'diagnostic_flags': ('Previously derived QA alerts preserved verbatim; no filter applied', 'categories'),
    'stage79_exact_duplicate_geometry_way_ids': ('Other exactly identical original coordinate sequences; no tolerance', 'identifiers'),
    'stage79_exact_shared_node_edge_way_ids': ('Other original objects with exactly shared node edges; surfaces may share boundaries', 'identifiers'),
    'historical_or_status_alert': ('Literal lifecycle tag or old-name hint; requires documentary individual review', 'boolean'),
    'original_note_alert': ('At least one original note/fixme/opening_hours tag', 'boolean'),
    'geometry_or_topology_alert': ('Existing invalid/uncertain geometry, non-simple axis, exact duplicate or shared-node alert', 'boolean'),
    'itinerary_or_park_name_alert': ('Literal itinerary/park/cross name alert already recorded in member flags', 'boolean'),
    'review_status': ('Individual review queue only, no metric decision or automatic exclusion', 'category'),
    'object_retained': ('Original member remains present; no flagged object removed', 'boolean'),
}


def register(frames, sources, manifests):
    master = read('metadata/data_sources_master.csv')
    records = []
    for s in sources:
        m = manifests[s['source_id']]
        records.append(dict(source_id=s['source_id'], variable_name='primary_historical_operating_evidence',
            variable_description=s['purpose'], source_organisation=s['organisation'], source_page_url=m['url'],
            direct_download_url=m.get('final_url', ''), retrieval_date=m['retrieval_date'][:10],
            retrieval_method='Resumable source collector; archived actual HTTP200/SHA; primary PDF text and page rendering reviewed',
            local_raw_file=m['raw_file'], geographic_level='Source-specific La Braye/other named facilities; never communal observations',
            temporal_resolution='Source-stated2017/18 ski activity and2018 municipal account; no fabricated publication/closure date',
            license='Publisher rights unchanged; no licence inferred',
            processed_file=OUTPUTS[0], quality_notes='Activity, financing, facility removal and authorisation distinguished; no treatment/geometry change',
            notes='Separate late follow-up, not mutation of frozen Stage79 producer; '+SUMMARY))
    records.append(dict(source_id=SOURCE, variable_name='historical_claims_and_literal_object_qa',
        variable_description='Five bounded primary claims and all flagged retained original member objects',
        source_organisation='Thesis documentary/geometry audit', retrieval_date=datetime.now(timezone.utc).date().isoformat(),
        retrieval_method='Manually pinned primary page markers; existing literal QA flags, no operating classification inferred',
        processed_file='|'.join(OUTPUTS), geographic_level='Documentary claims and retained OSM objects in approved69-group universe',
        temporal_resolution='Historical source statements/current source geometry proxy distinguished',
        transformation_applied='Expose review queue and bounded claims only; no axis/surface/calendar/value replacement',
        quality_notes='No automatic object or group exclusion and no new physical profile or DiD estimate', notes=SUMMARY))
    fresh = [r for r in records if r['source_id'] not in set(master.source_id)]
    if fresh:
        write_csv(pd.concat([master, pd.DataFrame(fresh).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT/'metadata/data_sources_master.csv')
    dictionary = read('metadata/data_dictionary.csv'); add = []
    for path, frame in zip(OUTPUTS, frames):
        table = Path(path).stem
        for col in frame:
            if ((dictionary.table == table) & dictionary.variable.eq(col)).any():
                continue
            description, unit = DEFS[col]
            add.append(dict(variable=col, table=table, description=description, unit=unit,
                data_type=str(frame[col].dtype), geographic_level='Documentary claim or original OSM object',
                temporal_level='Exact stated source period/current mapped proxy', source_id=SOURCE,
                raw_or_derived='bounded documentary claim or retained literal QA',
                formula='src/descriptive/audit_piste_followup_stage79.py; no imputation/filter',
                causal_role='Quality and scope audit; no causal estimate or final clustering variable',
                missing_share=f"{(frame[col].isna() | frame[col].astype(str).eq('')).mean():.6f}",
                notes='All objects/groups and source calendar remain unchanged; '+SUMMARY))
    if add:
        write_csv(pd.concat([dictionary, pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT/'metadata/data_dictionary.csv')


def main():
    sources = json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    decisions = json.loads((ROOT/CLAIMS).read_text(encoding='utf-8'))
    assert decisions['no_calendar_change'] and decisions['no_geometry_assignment'] and decisions['no_source_data_modified']
    manifests = {}; docs = {}; inputs = {p:sha(p) for p in [CONFIG, CLAIMS, 'src/descriptive/audit_piste_followup_stage79.py',
        'data_processed/winter_profile_piste_members_stage79.csv', 'reports/remaining_piste_assignments_stage79_summary.json']}
    for s in sources:
        found = list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if len(found) != 1:
            raise ValueError('Exactly one archived primary document required')
        m = json.loads(found[0].read_text(encoding='utf-8'))
        if sha(m['raw_file']) != m['sha256'] or m['http_status'] != 200:
            raise ValueError('Original source changed or response not successful')
        manifests[s['source_id']] = m; docs[s['source_id']] = PdfReader(ROOT/m['raw_file'])
        inputs[m['raw_file']] = m['sha256']; inputs[found[0].relative_to(ROOT).as_posix()] = sha(found[0].relative_to(ROOT).as_posix())
    claims = []
    for c in decisions['claims']:
        page = normalized(docs[c['source_id']].pages[c['pdf_page']-1].extract_text())
        if not all(normalized(marker) in page for marker in c['required_markers']):
            raise ValueError('Primary page markers differ: '+c['claim_id'])
        m = manifests[c['source_id']]
        claims.append({k:v for k,v in c.items() if k != 'required_markers'} | dict(source_url=m['url'], raw_file=m['raw_file'], raw_sha256=m['sha256']))
    claim_frame = pd.DataFrame(claims)
    members = read('data_processed/winter_profile_piste_members_stage79.csv')
    fields = ['station_group_id','station_group_name','osm_id','osm_version','original_name','candidate_role','geometry_status',
        'original_lifecycle_tags','original_review_tags','literal_name_history_hint','diagnostic_flags',
        'stage79_exact_duplicate_geometry_way_ids','stage79_exact_shared_node_edge_way_ids']
    qa = members[fields].copy()
    qa['historical_or_status_alert'] = members.original_lifecycle_tags.ne('{}') | members.literal_name_history_hint.eq('True')
    qa['original_note_alert'] = members.original_review_tags.ne('{}')
    qa['geometry_or_topology_alert'] = (members.geometry_status.isin(['valid_axis_candidate','valid_standalone_surface_candidate']).eq(False)
        | members.line_is_simple.eq('False') | members.stage79_exact_duplicate_geometry_way_ids.ne('') | members.stage79_exact_shared_node_edge_way_ids.ne(''))
    qa['itinerary_or_park_name_alert'] = members.diagnostic_flags.str.contains('literal_itinerary_or_park_name', regex=False)
    mask = qa[['historical_or_status_alert','original_note_alert','geometry_or_topology_alert','itinerary_or_park_name_alert']].any(axis=1)
    qa = qa[mask].copy(); qa['source_id'] = SOURCE
    qa['review_status'] = 'individual_review_pending_no_metric_rule_applied'; qa['object_retained'] = True
    frames = [claim_frame, qa]
    target = ROOT/SUMMARY
    if target.exists():
        state = json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256'] != inputs or any(sha(p) != h for p,h in state['output_sha256'].items()):
            raise ValueError('Frozen follow-up changed: use a new stage')
    else:
        for path, frame in zip(OUTPUTS, frames):
            write_csv(frame, ROOT/path)
        state = dict(completed_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
            output_sha256={p:sha(p) for p in OUTPUTS}, primary_claim_count=len(claim_frame),
            flagged_object_count=len(qa), flagged_group_count=qa.station_group_id.nunique(),
            historical_or_status_alert_count=int(qa.historical_or_status_alert.sum()),
            original_note_alert_count=int(qa.original_note_alert.sum()),
            geometry_or_topology_alert_count=int(qa.geometry_or_topology_alert.sum()),
            itinerary_or_park_name_alert_count=int(qa.itinerary_or_park_name_alert.sum()),
            source_manifests=manifests, no_calendar_geometry_or_metric_change=True, no_automatic_exclusion=True)
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    register(frames, sources, manifests)
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','source_manifests']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
