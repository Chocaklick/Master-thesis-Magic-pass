"""Retain official operator navigation and scope evidence, not GIS assignments."""
import hashlib
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.register_piste_scope_case_evidence import visible_text
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

CONFIG = 'config/piste_operator_evidence_stage47.json'
OUTPUT = 'reports/piste_operator_evidence_stage47_summary.json'
SCRIPT = 'src/descriptive/register_piste_operator_evidence_stage47.py'


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.href=None; self.fragments=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href=dict(attrs).get('href'); self.fragments=[]
    def handle_data(self, text):
        if self.href is not None:
            self.fragments.append(text)
    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((self.href, ' '.join(' '.join(self.fragments).split())))
            self.href=None


def navigation(content, url):
    parser = Links(); parser.feed(content)
    result=[]; seen=set()
    for href, label in parser.links:
        absolute=urljoin(url, href)
        if urlsplit(absolute).scheme not in ['http','https'] or (absolute,label) in seen:
            continue
        seen.add((absolute,label))
        result.append(dict(url=absolute, label=label, original_href=href))
    return result


def main():
    config=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    inputs={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [CONFIG,SCRIPT,'src/descriptive/register_piste_scope_case_evidence.py']}
    cases=[]; rows=[]
    markers={
        'SKI_VAUD_OPERATOR_LINK_STAGE47':(['Ste-Croix / Les Rasses','2025/2026'],'MP_GROUP_RESORT__sainte_croix_les_rasses'),
        'MYVALLEE_JOUX_ALPINE_SCOPE_STAGE47':(['trois stations','Mollards','Esserts','Abbaye'],'MP_GROUP_RESORT__vallee_de_joux'),
        'SWISSTOPO_ALTI3D_RESOLUTION_STAGE47':(['0.5 m','2 m','updated every six years','LV95 LN02'],None)
    }
    for source in config:
        found=list((ROOT/'data_external/source_evidence').glob(source['source_id']+'_*.metadata.json'))
        if len(found)!=1:
            raise ValueError('Require one exact archived public page; no inferred content')
        meta=json.loads(found[0].read_text(encoding='utf-8')); raw=ROOT/meta['raw_file']
        if meta['url']!=source['url'] or hashlib.sha256(raw.read_bytes()).hexdigest()!=meta['sha256']:
            raise ValueError('Official source identity/hash changed')
        text=raw.read_text(encoding='utf-8'); visible=visible_text(text)
        required, group=markers[source['source_id']]
        if not all(marker in visible for marker in required):
            raise ValueError('Required visible source evidence missing')
        inputs[meta['raw_file']]=meta['sha256']
        links=navigation(text, meta['final_url'])
        cases.append(dict(source_id=source['source_id'], station_group_id=group, source_url=source['url'],
            raw_file=meta['raw_file'], required_visible_markers=required, current_scope_note=source['scope_note'],
            navigation_links=links, historical_scope_certified=False, gis_assignment_accepted=False))
        rows.append(dict(source_id=source['source_id'], variable_name='current_operator_scope_or_dem_documentation',
            variable_description=source['scope_note'], source_organisation=source['organisation'],
            source_dataset_name='Official current web documentation', source_page_url=source['url'],
            retrieval_date=meta['retrieval_date'], retrieval_method='Archived HTML, robots check, full SHA256 and visible markers; observed hrefs only',
            local_raw_file=meta['raw_file'], processed_file=OUTPUT, geographic_level='current named scope or DEM product documentation',
            temporal_resolution='current page; not preentry certified', license='Provider website terms; no open geometry licence inferred',
            transformation_applied='Extract exact observed navigation links; no geometry, quantities or station features',
            quality_notes=source['scope_note'], notes='sha256='+meta['sha256']))
    state=dict(date='2026-10-09', input_sha256=inputs, cases=cases, accepted_assignments=0,
        station_features_computed=False, groups_changed=False, dem_resolution_selected=False)
    path=ROOT/OUTPUT
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8'))!=state:
            raise ValueError('Changed own evidence; preserve prior checkpoint and review')
    else:
        path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    ids={row['source_id'] for row in rows}
    write_csv(pd.concat([master[~master.source_id.isin(ids)],pd.DataFrame(rows).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    print('Three official pages verified; exact navigation retained, no geometry/feature/group choice applied.')


if __name__=='__main__':
    main()
