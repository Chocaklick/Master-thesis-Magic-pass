"""Register exact current official evidence for two flagged scope checks.

No quantities imported as station features, no historical scope certification.
"""
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

CONFIG = 'config/piste_scope_case_evidence_stage46.json'
OUTPUT = 'reports/piste_scope_case_evidence_summary.json'


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(); self.fragments = []; self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ['script', 'style']:
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ['script', 'style']:
            self.hidden -= 1
    def handle_data(self, data):
        if not self.hidden:
            self.fragments.append(data)


def visible_text(content):
    parser = VisibleText(); parser.feed(content)
    return ' '.join(' '.join(parser.fragments).split())


def main():
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    cases, records, inputs = [], [], {CONFIG:hashlib.sha256((ROOT / CONFIG).read_bytes()).hexdigest()}
    for source in config:
        paths = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
        if len(paths) != 1:
            raise ValueError('Require exactly one archived official page')
        meta = json.loads(paths[0].read_text(encoding='utf-8'))
        raw = ROOT / meta['raw_file']
        if hashlib.sha256(raw.read_bytes()).hexdigest() != meta['sha256'] or meta['url'] != source['url']:
            raise ValueError('Source identity/hash mismatch')
        inputs[meta['raw_file']] = meta['sha256']
        text = visible_text(raw.read_text(encoding='utf-8'))
        if 'SAINTE_CROIX' in source['source_id']:
            required = ['Chasseron', 'ski de fond', 'domaine skiable']
            group = 'MP_GROUP_RESORT__sainte_croix_les_rasses'
            finding = 'Official alpine domain exists; OSM relation2899124 has22nordic ways and7lift ways but0referenced downhill ways. Missing alpine membership, not absence of skiing.'
        else:
            required = ['Abbaye', 'Orient', 'Brassus']
            group = 'MP_GROUP_RESORT__vallee_de_joux'
            finding = 'Official page names three components; relation9374152 L Abbaye cannot alone represent whole retained Vallee de Joux group.'
        if not all(word in text for word in required):
            raise ValueError('Required official scope evidence missing; no inferred claim')
        cases.append(dict(station_group_id=group, source_id=source['source_id'], required_visible_markers=required,
            finding=finding, current_official_description_verified=True, historical_scope_verified=False,
            osm_group_assignment_accepted=False, source_url=source['url']))
        records.append(dict(source_id=source['source_id'], variable_name='official_current_piste_scope_evidence',
            variable_description=source['purpose'], source_organisation=source['organisation'],
            source_dataset_name='Current official Magic Pass destination page', source_page_url=source['url'],
            retrieval_method='Archived official HTML; robots checked, exact SHA256, visible scope markers verified',
            retrieval_date=meta['retrieval_date'], local_raw_file=meta['raw_file'], processed_file=OUTPUT,
            geographic_level='Current named destination components; not accepted GIS assignment',
            temporal_resolution='Current description, not verified preentry footprint', license='Provider website terms; no open data licence inferred',
            transformation_applied='Visible text marker verification only; no feature values or geometry assignment',
            quality_notes=finding, manual_verification='Current descriptions checked against referenced OSM membership audit',
            notes='sha256=' + meta['sha256']))
    state = dict(date='2026-10-09', input_sha256=inputs, cases=cases, station_features_computed=False,
        accepted_assignments=0, additional_groups_or_exclusions=0)
    if (ROOT / OUTPUT).exists():
        if json.loads((ROOT / OUTPUT).read_text(encoding='utf-8')) != state:
            raise ValueError('Changed own evidence; keep prior checkpoint')
    else:
        (ROOT / OUTPUT).write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    ids = {r['source_id'] for r in records}
    write_csv(pd.concat([master[~master.source_id.isin(ids)], pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    print('Two immutable official scope pages verified/registered; no features or accepted assignments.')


if __name__ == '__main__':
    main()
