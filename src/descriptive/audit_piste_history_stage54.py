"""Dated original evidence: corroboration, not an official historic-map claim."""
import json
import re
import sys
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS
SUMMARY='reports/piste_history_stage54_summary.json'
CONFIGS=['config/piste_historical_sources_stage54.json','config/piste_historical_scope_sources_stage54.json','config/piste_historical_observation_sources_stage54.json']


def article_dates(soup):
    text=str(soup)
    dates={}
    for field in ['datePublished','dateModified']:
        values=set(re.findall(r'"'+field+r'"\s*:\s*"([^"]+)"',text))
        if len(values)>1:raise ValueError('Conflicting original article dates')
        dates[field]=next(iter(values)) if values else None
    return dates


def main():
    inputs={p:sha(p) for p in CONFIGS+['config/piste_historical_connection_decisions_stage54.json','reports/piste_history_discovery_stage54.json','reports/piste_history_discovery_complement_stage54.json','src/descriptive/audit_piste_history_stage54.py','src/data_collection/collect_piste_history_stage54.py','data_processed/accessibility_station_groups.csv']}
    configs=[s for p in CONFIGS for s in json.loads((ROOT/p).read_text(encoding='utf-8'))]
    documents=[]
    for source in configs:
        paths=list((ROOT/'data_external/source_evidence').glob(source['source_id']+'_*.metadata.json'))
        if len(paths)!=1:raise ValueError('Require exactly one archived original per new source')
        metadata=json.loads(paths[0].read_text(encoding='utf-8'))
        if metadata['url']!=source['url'] or sha(metadata['raw_file'])!=metadata['sha256']:raise ValueError('Changed original evidence')
        inputs[paths[0].relative_to(ROOT).as_posix()]=sha(paths[0].relative_to(ROOT))
        inputs[metadata['raw_file']]=metadata['sha256']
        document=dict(source_id=source['source_id'],url=source['url'],raw_file=metadata['raw_file'],sha256=metadata['sha256'],publication_before_entry=None,physical_ski_connection_documented=False)
        if source['suffix']=='pdf':
            reader=PdfReader(ROOT/metadata['raw_file'])
            pages=[p.extract_text() or '' for p in reader.pages]
            document.update(page_count=len(pages),eischoll_mentioned_pages=[i+1 for i,t in enumerate(pages) if 'eischoll' in t.lower()],historical_official_map_found=False)
            if '2019_20' in source['source_id']:
                if '2019/2020' not in pages[0] or '28. Mai 2021' not in pages[0]:raise ValueError('Unexpected report dating')
                document.update(document_reference='FY2019/20, assembly28May2021',publication_before_entry=True,interpretation='Official report inspected: no Eischoll mention; not a physical connection proof.')
            elif '2020_21' in source['source_id']:
                if '2020/2021' not in pages[0] or '23. Oktober 2021' not in pages[0]:raise ValueError('Unexpected report dating')
                document.update(document_reference='FY2020/21, assembly23October2021',publication_before_entry=True,interpretation='Official report inspected: no Eischoll mention; not a physical connection proof.')
            elif '2021_22' in source['source_id']:
                if '2021/2022' not in pages[0] or '22. Oktober 2022' not in pages[0]:raise ValueError('Unexpected report dating')
                document.update(document_reference='FY2021/22, assembly22October2022',publication_before_entry=True,interpretation='Official report inspected: no Eischoll mention; not a physical connection proof.')
            else:
                if '2022/2023' not in pages[0] or 'Eischoll' not in pages[13]:raise ValueError('Unexpected later report')
                document.update(document_reference='FY2022/23, publishedSeptember2023; page14',publication_before_entry=False,interpretation='Retrospective/postentry: shared regional ticket cooperation ended2023/24; discussions with Eischoll continued. Ticket cooperation is not physical slope connection.')
        else:
            soup=BeautifulSoup((ROOT/metadata['raw_file']).read_bytes(),'html.parser')
            dates=article_dates(soup); document.update(dates)
            text=soup.get_text(' ',strip=True)
            if 'ENVIADI' in source['source_id']:
                if dates!={'datePublished':'2022-03-10T14:11:44+00:00','dateModified':'2022-07-07T15:25:58+00:00'}:raise ValueError('Article dating changed')
                if 'Kuriose Verbindungswege im Wald' not in text or 'entgegengesetzten Richtung' not in text:raise ValueError('Specific two-direction ski connection text absent')
                document.update(author='Felix Gross',publication_before_entry=True,physical_ski_connection_documented=True,interpretation='Authored direct ski-visit account describes both connecting forest paths; published and last-modified dates precedeMay2023. Self-declared dates, not an independently archived2022version or official plan.')
            elif 'FIRSTHAND_FEB2021' in source['source_id']:
                if dates['datePublished']!='2021-08-28T15:31:00+02:00' or 'Unterbäch Februar 2021' not in text or 'Der Verbindungsweg von Eischoll' not in text:raise ValueError('Visit/account dates or connection changed')
                document.update(publication_before_entry=True,physical_ski_connection_documented=True,interpretation='Visit is reported asFebruary2021 and publicationAugust2021, but lastmodifiedMay2025: corroborating account only, not frozen preentry content.')
            else:document['interpretation']='Current official archive navigation, no historical physical connection claim.'
        documents.append(document)
    # Existing official current source is preserved, not newly registered.
    matches=list((ROOT/'data_external/source_evidence').glob('OPERATOR_DEEP_06_STAGE53_*.metadata.json'))
    if len(matches)!=1:raise ValueError('Require archived current official source')
    current=json.loads(matches[0].read_text(encoding='utf-8'))
    if sha(current['raw_file'])!=current['sha256']:raise ValueError('Changed current official source')
    text=BeautifulSoup((ROOT/current['raw_file']).read_bytes(),'html.parser').get_text(' ',strip=True)
    if 'Strygge-Erez' not in text or 'Verbindungspisten nach Unterbäch' not in text:raise ValueError('Official current connection statement absent')
    inputs[current['raw_file']]=current['sha256']
    decision=json.loads((ROOT/'config/piste_historical_connection_decisions_stage54.json').read_text(encoding='utf-8'))
    groups=pd.read_csv(ROOT/'data_processed/accessibility_station_groups.csv',dtype=str,keep_default_na=False)
    part=groups[groups.station_group_id.isin(decision['station_group_ids'])]
    if len(part)!=2 or not part.first_effective_month.eq('2023-05-01').all():raise ValueError('Historical entry mismatch')
    state=dict(date='2026-10-10',input_sha256=inputs,documents=documents,current_official_source_id=current['source_id'],retained_original_group_ids=decision['station_group_ids'],first_effective_month='2023-05-01',connection_assessment='corroborated_preentry_authored_account_plus_current_official_confirmation',historic_official_plan_found=False,independently_frozen_preentry_article_found=False,full_historical_domain_geometry_certified=False,fusion_applied=False,additional_regrouping_validation_required=True)
    target=ROOT/SUMMARY
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8'))!=state:raise ValueError('Frozen historical audit changed')
    else:target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False);records=[]
    for source,document in zip(configs,documents):
        if source['source_id'] in set(master.source_id):continue
        metadata=json.loads(next((ROOT/'data_external/source_evidence').glob(source['source_id']+'_*.metadata.json')).read_text(encoding='utf-8'))
        records.append(dict(source_id=source['source_id'],variable_name='historical_ski_connection_evidence',variable_description=source['purpose'],source_organisation=source['organisation'],source_page_url=source['url'],retrieval_date=metadata['retrieval_date'],retrieval_method='Public original GET/robots/TLS, exact discovered or literal archived link; SHA verified',original_file_name=Path(document['raw_file']).name,local_raw_file=document['raw_file'],processed_file=SUMMARY,geographic_level='Eischoll/Unterbaech station connection, not municipal outcomes',temporal_resolution=document.get('document_reference',document.get('datePublished') or 'current navigation'),license='Public consultation; no open redistribution licence asserted',transformation_applied='Read-only text/date/manual PDF review; originals retained',quality_notes=document['interpretation'],notes='sha256='+document['sha256']+'; no group fusion or historic map certification in this audit'))
    for sid,path in [('PISTE_HISTORY_DISCOVERY_STAGE54','reports/piste_history_discovery_stage54.json'),('DERIVED_PISTE_HISTORY_AUDIT_STAGE54',SUMMARY)]:
        if sid not in set(master.source_id):records.append(dict(source_id=sid,variable_name='historical_connection_source_audit',variable_description='Discovery metadata only' if 'DISCOVERY' in sid else 'Dated original evidence assessment, not certified historical map',source_organisation='Thesis source audit',processed_file=path,retrieval_date='2026-10-10',retrieval_method='Recorded queries/request IDs/URLs and archived primary documents',geographic_level='Eischoll/Unterbaech groups',quality_notes='No inference from publication year in a filename, search snippet, shared ticket or current geometry alone',notes='Complement '+ 'reports/piste_history_discovery_complement_stage54.json' if 'DISCOVERY' in sid else 'Original SHA and dates in summary'))
    if records:write_csv(pd.concat([master,pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    print('Seven originals and current official evidence checked; preentry authored corroboration, no official historical-map certification or fusion.')


if __name__=='__main__':main()
