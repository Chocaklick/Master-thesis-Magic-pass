"""Document stopped IGN research and actual old raster cache, without new collection."""
import json
import sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS


def main():
    inputs={p:sha(p) for p in ['src/descriptive/close_reviewed_geometry_stage80.py',
        'config/terrain_french_complement_decision_stage80.json','config/ign_terrain_audit_sources_stage80.json',
        'config/ign_terrain_followup_sources_stage80.json','data_processed/terrain_reviewed_asset_inventory_stage80.csv']}
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    events=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    evidence={};byurl={}
    for p in (ROOT/'data_external/source_evidence').glob('*.metadata.json'):
        m=json.loads(p.read_text(encoding='utf-8'))
        if 'url' in m and 'raw_file' in m and (ROOT/m['raw_file']).exists():byurl.setdefault(m['url'],[]).append((p,m))
        if m.get('source_id','').startswith('IGN_') and m.get('source_id','').endswith('STAGE80'):evidence[m['source_id']]=(p,m)
    records=[];outcomes=[]
    for path in ['config/ign_terrain_audit_sources_stage80.json','config/ign_terrain_followup_sources_stage80.json']:
        for s in json.loads((ROOT/path).read_text(encoding='utf-8')):
            sid=s['source_id'];ev=events[events.source_id.eq(sid)]
            rec=dict(source_id=sid,variable_name='official_documentation_or_catalogue_attempt',
                variable_description=s['purpose'],source_organisation=s['organisation'],source_page_url=s['url'],
                geographic_level='Document or local Dôle–Tuffes catalogue metadata, not communal data',
                temporal_resolution='Observed HTTP response; not historical terrain acquisition certificate',
                processed_file='reports/126_GEOMETRIES_REVUES_ET_COUVERTURES_FR.md',
                retrieval_method='Public configured GET with robots/TLS and immutable actual response; research stopped by researcher',
                license='No terrain reuse performed; licence metadata archived, attribution needed for any later authorised reuse',
                quality_notes='IGN audit interrupted at researcher request; no French raster, no blending or boundary cut')
            outcome=dict(source_id=sid,actual_events=len(ev),no_raster_or_profile_use=True)
            if sid in evidence:
                p,m=evidence[sid];raw=ROOT/m['raw_file'];h=sha(m['raw_file'])
                if h!=m['sha256']:raise ValueError('Original evidence changed')
                inputs[m['raw_file']]=h;inputs[p.relative_to(ROOT).as_posix()]=sha(p.relative_to(ROOT).as_posix())
                head=raw.read_bytes()[:32]
                pdf_ok=s['suffix']!='pdf' or head.startswith(b'%PDF-')
                rec.update(retrieval_date=m['retrieval_date'],local_raw_file=m['raw_file'],
                    notes='SHA='+h+'; actual final URL='+m['final_url']+'; '+('expected container signature' if pdf_ok else 'HTTP200 HTML redirect, NOT a consulted PDF'))
                outcome.update(raw_file=m['raw_file'],sha256=h,expected_pdf_signature_valid=pdf_ok)
                if not pdf_ok:rec['quality_notes']+='; expected PDF is an HTML redirection, content not used as documentation'
            else:
                if ev.empty:raise ValueError('Configured source never actually attempted')
                last=ev.iloc[-1];rec.update(retrieval_date=last.timestamp,notes='Actual failure '+last.status+'; '+last.error)
                outcome.update(status=last.status,HTTP_status=last.HTTP_status)
            records.append(rec);outcomes.append(outcome)
    fresh=[r for r in records if r['source_id'] not in set(master.source_id)]
    if fresh:write_csv(pd.concat([master,pd.DataFrame(fresh).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    assets=pd.read_csv(ROOT/'data_processed/terrain_reviewed_asset_inventory_stage80.csv',dtype=str,keep_default_na=False)
    wanted=assets[assets.latest_reference_for_native_tile.eq('True')].drop_duplicates('asset_url')
    cached=[];pending=[]
    for r in wanted.itertuples():
        candidates=[(p,m) for p,m in byurl.get(r.asset_url,[]) if m.get('sha256')==r.asset_sha256]
        if not candidates:pending.append(r.asset_url);continue
        p,m=candidates[-1]
        if sha(m['raw_file'])!=r.asset_sha256:raise ValueError('Actual original raster differs from official asset checksum')
        inputs[m['raw_file']]=r.asset_sha256;inputs[p.relative_to(ROOT).as_posix()]=sha(p.relative_to(ROOT).as_posix())
        cached.append(dict(asset_url=r.asset_url,raw_file=m['raw_file'],source_id=m['source_id'],sha256=r.asset_sha256))
    state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,
        stopped_ign_source_outcomes=outcomes,french_complement_cancelled=True,no_new_raster_download=True,
        old_cached_count_field_is_historical_not_current=True,latest_distinct_assets=len(wanted),
        current_verified_cached_asset_count=len(cached),current_missing_latest_asset_count=len(pending),
        cached_assets=cached,uncollected_asset_urls=pending)
    target=ROOT/'reports/reviewed_geometry_followup_stage80_summary.json'
    if target.exists():
        old=json.loads(target.read_text(encoding='utf-8'))
        if old['input_sha256']!=inputs:raise ValueError('Frozen closing audit differs')
    else:target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','stopped_ign_source_outcomes','cached_assets','uncollected_asset_urls']},ensure_ascii=False))


if __name__=='__main__':main()
