"""Register current operator page/PDF scope evidence, not georeferenced pistes."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.register_piste_scope_case_evidence import visible_text
from src.descriptive.register_piste_operator_evidence_stage47 import navigation
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

CONFIG='config/piste_plan_evidence_stage49.json'
OUTPUT='reports/piste_plan_evidence_stage49_summary.json'


def main():
    inputs={CONFIG:hashlib.sha256((ROOT/CONFIG).read_bytes()).hexdigest()}
    cases=[]; rows=[]
    for source in json.loads((ROOT/CONFIG).read_text(encoding='utf-8')):
        found=list((ROOT/'data_external/source_evidence').glob(source['source_id']+'_*.metadata.json'))
        if len(found)!=1:
            raise ValueError('Require one exact archived source')
        meta=json.loads(found[0].read_text(encoding='utf-8')); raw=ROOT/meta['raw_file']
        if meta['url']!=source['url'] or hashlib.sha256(raw.read_bytes()).hexdigest()!=meta['sha256']:
            raise ValueError('Source identity/hash changed')
        inputs[meta['raw_file']]=meta['sha256']
        if source['suffix']=='pdf':
            from pypdf import PdfReader
            reader=PdfReader(raw)
            if len(reader.pages)!=1:
                raise ValueError('Plan page count changed; re-review visually')
            text=reader.pages[0].extract_text()
            required=['Abbaye','Orient','Brassus','Vaulion']
            if not all(word in text for word in required):
                raise ValueError('Required plan scope labels missing')
            detail=dict(page_count=1, original_pdf_metadata={str(k):str(v) for k,v in reader.metadata.items()},
                required_markers=required, text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                rendered_page='data_interim/piste_plan_review_stage49/vallee_joux_page1.png',
                visual_review_note='Rendered page reviewed: separate panels for the three retained components and Dent de Vaulion; Magic Pass logos on the three retained panels, not the Vaulion panel. No extra group component accepted.',
                geometry_conversion_applied=False,
                rights_note='Plan credits underlying Google/DigitalGlobe imagery; no open geospatial or digitisation licence inferred')
            finding='Regional plan is broader than retained Magic Pass group; three named components confirmed, Vaulion not added. PDF creation metadata 2023 is not preentry scope certification.'
        else:
            text=visible_text(raw.read_text(encoding='utf-8'))
            required=['Rasses I','Rasses II','Rasses III','Avattes I','Cochet']
            if not all(word in text for word in required):
                raise ValueError('Required operator installation labels missing')
            detail=dict(required_markers=required, navigation_links=navigation(raw.read_text(encoding='utf-8'),meta['final_url']),
                geometry_conversion_applied=False)
            finding='Operator page names alpine installations; installation counts/opening status are not piste lengths, piste counts or historical station characteristics.'
        cases.append(dict(source_id=source['source_id'], source_url=source['url'], raw_file=meta['raw_file'], finding=finding,
            historical_scope_verified=False, gis_assignment_accepted=False, **detail))
        rows.append(dict(source_id=source['source_id'], variable_name='current_operator_piste_plan_scope_evidence',
            variable_description=source['purpose'],source_organisation=source['organisation'],source_dataset_name='Current operator page or regional piste plan',
            source_page_url=source['url'],retrieval_date=meta['retrieval_date'],retrieval_method='Archived original; robots and SHA256; page/text scope inspection; PDF rendered and visually reviewed',
            original_file_name=Path(meta['raw_file']).name,local_raw_file=meta['raw_file'],processed_file=OUTPUT,
            geographic_level='Current named regional panels/installations, not verified GIS footprint',temporal_resolution='Current document, not verified preentry geometry',
            license='Provider/underlying imagery terms; no open GIS licence inferred',transformation_applied='Scope marker and metadata inspection only; no georeferencing or feature transcription',
            quality_notes=finding,notes='sha256='+meta['sha256']))
    state=dict(date='2026-10-09',input_sha256=inputs,cases=cases,groups_changed=False,
        accepted_gis_assignments=0,station_features_computed=False)
    output=ROOT/OUTPUT
    if output.exists():
        if json.loads(output.read_text(encoding='utf-8'))!=state:
            raise ValueError('Changed plan checkpoint; retain prior output and review')
    else:
        output.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    ids={s['source_id'] for s in rows}
    write_csv(pd.concat([master[~master.source_id.isin(ids)],pd.DataFrame(rows).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    print('Two current plan/operator sources verified and registered; no historical or GIS assignment.')


if __name__=='__main__':
    main()
