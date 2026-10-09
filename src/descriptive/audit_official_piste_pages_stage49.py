"""Hash-verified current official page coverage; no inferred GIS assignments.

Run only after page and snow collectors stop (shared registry/log writers).
The group universe and links use retained IDs, never fuzzy names or proximity.
"""
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.register_piste_operator_evidence_stage47 import navigation
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

OUTPUT = 'data_processed/winter_profile_official_page_coverage_stage49.csv'
SUMMARY = 'reports/piste_official_page_audit_stage49_summary.json'
TABLE = 'winter_profile_official_page_coverage_stage49'
SOURCE = 'DERIVED_OFFICIAL_PISTE_PAGE_AUDIT_STAGE49'


class Headings(HTMLParser):
    def __init__(self):
        super().__init__(); self.active = False; self.fragments = []; self.headings = []
    def handle_starttag(self, tag, attrs):
        if tag == 'h1':
            self.active = True; self.fragments = []
    def handle_data(self, data):
        if self.active:
            self.fragments.append(data)
    def handle_endtag(self, tag):
        if tag == 'h1' and self.active:
            self.headings.append(' '.join(' '.join(self.fragments).split())); self.active = False


def coverage(groups, links, verified):
    if not groups.station_group_id.is_unique:
        raise ValueError('Duplicate stable group ID')
    allowed = set(groups.station_group_id)
    if {link['station_group_id'] for link in links} != allowed:
        raise ValueError('Coverage links must retain exactly the original group universe')
    rows = []
    for group in groups.itertuples():
        selected = [link for link in links if link['station_group_id'] == group.station_group_id]
        planned = sorted({link['source_id'] for link in selected if link['source_id']})
        archived = sorted(set(planned) & verified)
        fallback = sum(link['source_id'] is None for link in selected)
        rows.append(dict(station_group_id=group.station_group_id, station_group_name=group.station_group_name,
            access_point_count=len(selected), planned_official_page_count=len(planned),
            verified_archived_page_count=len(archived), fallback_reference_count=fallback,
            verified_source_ids='|'.join(archived), gis_assignment_verified=False,
            historical_scope_verified=False, automatic_exclusion_applied=False))
    return pd.DataFrame(rows)


def main():
    collection_path = 'reports/piste_official_page_collection_stage49_summary.json'
    queue_path = 'data_interim/piste_official_page_queue_stage49.json'
    collection = json.loads((ROOT / collection_path).read_text(encoding='utf-8'))
    queue = json.loads((ROOT / queue_path).read_text(encoding='utf-8'))
    digest = lambda path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
    if digest(queue_path) != collection['queue_sha256']:
        raise ValueError('Frozen source queue changed')
    inputs = {p: digest(p) for p in [queue_path, 'data_processed/accessibility_station_groups.csv',
        'src/descriptive/audit_official_piste_pages_stage49.py']}
    inputs.update(collection['input_sha256'])
    if any(digest(p) != sha for p, sha in inputs.items()):
        raise ValueError('Original retained linkage inputs changed')
    sources = {s['source_id']: s for s in queue}; cases = []; records = []
    for archived in collection['archived_pages']:
        source = sources[archived['source_id']]
        matches = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
        if len(matches) != 1:
            raise ValueError('Require one exact archived original')
        meta = json.loads(matches[0].read_text(encoding='utf-8'))
        if meta['source_id'] != source['source_id'] or meta['url'] != source['url'] or meta['raw_file'] != archived['raw_file'] or digest(meta['raw_file']) != meta['sha256'] or meta['sha256'] != archived['sha256']:
            raise ValueError('Original source identity or SHA changed')
        inputs[meta['raw_file']] = meta['sha256']
        content = (ROOT / meta['raw_file']).read_text(encoding='utf-8'); parser = Headings(); parser.feed(content)
        cases.append(dict(source_id=source['source_id'], official_destination_id=source['official_destination_id'],
            original_destination_name=source['original_destination_name'], source_url=source['url'], raw_file=meta['raw_file'],
            observed_h1=parser.headings, navigation_links=navigation(content, meta['final_url']),
            gis_assignment_accepted=False, historical_scope_certified=False))
        records.append(dict(source_id=source['source_id'], variable_name='current_official_destination_scope_navigation',
            variable_description=source['purpose'], source_organisation=source['organisation'],
            source_dataset_name='Current official Magic Pass destination page', source_page_url=source['url'],
            retrieval_date=meta['retrieval_date'], retrieval_method='Archived original, stable map/access IDs, SHA256 and observed h1/href extraction',
            original_file_name=Path(meta['raw_file']).name, local_raw_file=meta['raw_file'], processed_file=SUMMARY,
            geographic_level='Current official destination page, not verified GIS domain', temporal_resolution='Current document, not preentry certified',
            license='Provider website terms; no open geometry licence inferred', transformation_applied='Retain literal headings/navigation only',
            quality_notes='No fuzzy-name/proximity matching, domain assignment, quantity transcription or historical certification', notes='sha256=' + meta['sha256']))
    groups = pd.read_csv(ROOT / 'data_processed/accessibility_station_groups.csv', dtype=str, keep_default_na=False)
    frame = coverage(groups, collection['group_links'], set(c['source_id'] for c in cases))
    state = dict(date='2026-10-09', input_sha256=inputs, cases=cases, group_count=len(frame),
        planned_page_count=len(queue), verified_archived_page_count=len(cases), fallback_reference_count=int(frame.fallback_reference_count.sum()),
        accepted_gis_assignments=0, station_features_computed=False, automatic_exclusion_applied=False)
    if (ROOT / SUMMARY).exists():
        prior = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        if prior['input_sha256'] != inputs or digest(OUTPUT) != prior['output_sha256']:
            raise ValueError('Changed audit checkpoint; retain previous output and review')
    else:
        write_csv(frame, ROOT / OUTPUT); state['output_sha256'] = digest(OUTPUT)
        (ROOT / SUMMARY).write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    master_path = ROOT / 'metadata/data_sources_master.csv'
    master = pd.read_csv(master_path, dtype=str, keep_default_na=False)
    # Earlier reused sources remain byte-for-byte unchanged as records.
    records = [r for r in records if r['source_id'] not in set(master.source_id)]
    derived = dict(source_id=SOURCE, variable_name='official_page_coverage_audit', variable_description='Retained group page availability, not verified piste coverage',
        source_organisation='Thesis provenance audit', processed_file=OUTPUT, retrieval_date='2026-10-09',
        retrieval_method='Cached source hashes and stable retained IDs', geographic_level='Retained station group', temporal_resolution='Current page audit',
        transformation_applied='Coverage counts only, no accepted GIS or historical assignment',
        notes='Parent sources and original URLs/hash lineage in ' + SUMMARY)
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame(records + [derived]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), master_path)
    dictionary_path = ROOT / 'metadata/data_dictionary.csv'
    dictionary = pd.read_csv(dictionary_path, dtype=str, keep_default_na=False)
    definitions = dict(station_group_id=('Unchanged stable group identifier', 'ID'), station_group_name=('Unchanged original group label', 'text'),
        access_point_count=('Number of retained access points linked by stable IDs', 'count'), planned_official_page_count=('Number of distinct official pages in frozen queue', 'count'),
        verified_archived_page_count=('Number of archived original pages verified by SHA256', 'count'), fallback_reference_count=('Retained access points without current map-linked official page', 'count'),
        verified_source_ids=('Parent source identifiers, not accepted GIS memberships', 'IDs'), gis_assignment_verified=('False: no domain assignment accepted by this page audit', 'boolean'),
        historical_scope_verified=('False: current pages do not certify preentry piste geography', 'boolean'), automatic_exclusion_applied=('False: all groups retained regardless of evidence availability', 'boolean'))
    fields = [dict(variable=k, table=TABLE, description=description, unit=unit, data_type=str(frame[k].dtype), geographic_level='station group', temporal_level='current page audit',
        source_id=SOURCE, raw_or_derived='retained identifier or audit diagnostic', formula='Stable-ID linkage and SHA-verified archive counts; see script', causal_role='provenance audit only', missing_share='0.000000',
        notes='No missing-to-zero station characteristics, domain acceptance or group exclusion') for k, (description, unit) in definitions.items()]
    write_csv(pd.concat([dictionary[dictionary.table.ne(TABLE)], pd.DataFrame(fields).reindex(columns=dictionary.columns)], ignore_index=True).fillna(''), dictionary_path)
    events = pd.DataFrame(json.loads((ROOT / 'data_interim/piste_official_page_events_stage49.json').read_text(encoding='utf-8'))).fillna('').astype(str)
    log_path = ROOT / 'logs/data_collection_log.csv'; log = pd.read_csv(log_path, dtype=str, keep_default_na=False)
    events = events.reindex(columns=log.columns, fill_value='')
    combined = pd.concat([log, events], ignore_index=True).drop_duplicates()
    write_csv(combined, log_path)
    collection['canonical_log_merged'] = True
    (ROOT / collection_path).write_text(json.dumps(collection, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Hash-verified {len(cases)}/{len(queue)} official pages; all {len(frame)} groups retained, no GIS acceptance.')


if __name__ == '__main__':
    main()
