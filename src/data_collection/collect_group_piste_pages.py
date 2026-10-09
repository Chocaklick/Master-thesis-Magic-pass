"""Finite official page queue by retained access/map IDs; isolated event log.

No group assignment, new source URL guessing or source-registry write. Reuse
the project's evidence collector, redirecting only its log in this process so
snow collection cannot race on the canonical CSV. Merge events after it stops.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_collection import collect_evidence

QUEUE='data_interim/piste_official_page_queue_stage49.json'
EVENTS='data_interim/piste_official_page_events_stage49.json'
SUMMARY='reports/piste_official_page_collection_stage49_summary.json'


def make_queue(points,destinations,cached_by_url):
    if not destinations.official_destination_id.is_unique:
        raise ValueError('Duplicate original official map ID')
    index=destinations.set_index('official_destination_id')
    sources={}; group_links=[]
    for point in points.itertuples():
        if not point.access_point_id.startswith('ACCESS_MAGIC_CURRENT__'):
            group_links.append(dict(station_group_id=point.station_group_id,access_point_id=point.access_point_id,
                source_id=None,scope_status='retained_fallback_reference_official_page_not_resolved'))
            continue
        identifier=point.access_point_id.split('__',1)[1]
        if identifier not in index.index:
            raise ValueError('Retained official access ID absent from original map')
        row=index.loc[identifier]
        path=row.official_destination_path
        if not path.startswith('/fr/stations/'):
            raise ValueError('Unexpected original official path, never guessed')
        url='https://www.magicpass.ch'+path
        sid=cached_by_url.get(url,'MAGIC_PISTE_SCOPE_DEST_'+identifier+'_STAGE49')
        sources.setdefault(sid,dict(source_id=sid,url=url,organisation='Magic Mountains Cooperation',suffix='html',
            official_destination_id=identifier,original_destination_name=row.official_destination_name,
            purpose='Current official destination scope/operator navigation; stable map ID, no automatic GIS or historical assignment'))
        group_links.append(dict(station_group_id=point.station_group_id,access_point_id=point.access_point_id,
            source_id=sid,scope_status='current_official_page_review_candidate'))
    return list(sources.values()),group_links


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--collect',action='store_true')
    parser.add_argument('--limit',type=int,default=12,help='First N sources in stable map-ID order, including cached sources')
    args=parser.parse_args()
    files=['data_processed/accessibility_station_access_points.csv','data_processed/magic_pass_current_destinations.csv']
    inputs={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    manifest=ROOT/SUMMARY
    if manifest.exists():
        state=json.loads(manifest.read_text(encoding='utf-8'))
        if state['input_sha256']!=inputs or hashlib.sha256((ROOT/QUEUE).read_bytes()).hexdigest()!=state['queue_sha256']:
            raise ValueError('Changed original queue inputs; preserve prior checkpoint')
    else:
        points=pd.read_csv(ROOT/files[0],dtype=str,keep_default_na=False)
        destinations=pd.read_csv(ROOT/files[1],dtype=str,keep_default_na=False)
        cached={}
        for metadata_file in sorted((ROOT/'data_external/source_evidence').glob('*.metadata.json')):
            meta=json.loads(metadata_file.read_text(encoding='utf-8'))
            if meta.get('url','').startswith('https://www.magicpass.ch/fr/stations/') and meta.get('raw_file','').endswith('.html'):
                cached[meta['url']]=meta['source_id']
        sources,links=make_queue(points,destinations,cached)
        sources.sort(key=lambda s:int(s['official_destination_id']))
        (ROOT/QUEUE).write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        state=dict(date='2026-10-09',input_sha256=inputs,queue_sha256=hashlib.sha256((ROOT/QUEUE).read_bytes()).hexdigest(),
            group_count=points.station_group_id.nunique(),access_point_count=len(points),page_count=len(sources),group_links=links,
            group_assignments_accepted=0,station_features_computed=False,canonical_log_merged=False,provider_collection_halted=False)
    def save():
        sources=json.loads((ROOT/QUEUE).read_text(encoding='utf-8'))
        # One directory scan, not 72 repeated scans after every downloaded page.
        metadata_index={}
        for candidate in (ROOT/'data_external/source_evidence').glob('*.metadata.json'):
            match=re.fullmatch(r'(.*)_\d{8}T\d{6}Z\.metadata\.json',candidate.name)
            if match:
                metadata_index.setdefault(match.group(1),[]).append(candidate)
        cached=[]
        for source in sources:
            matches=metadata_index.get(source['source_id'],[])
            if len(matches)>1:
                raise ValueError('More than one source original; review before reuse')
            if matches:
                meta=json.loads(matches[0].read_text(encoding='utf-8'))
                if meta.get('url')!=source['url'] or not meta.get('raw_file'):
                    raise ValueError('Cached official page identity changed')
                cached.append(dict(source_id=source['source_id'],raw_file=meta['raw_file'],sha256=meta['sha256'],retrieval_date=meta['retrieval_date']))
        state['archived_pages']=cached; state['archived_page_count']=len(cached)
        manifest.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    if not args.collect or state['provider_collection_halted']:
        print('Official page queue:',state['page_count'],'pages,',state['group_count'],'groups retained; no requests.')
        return
    def isolated_log(row):
        path=ROOT/EVENTS
        events=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        row['task']='stage49_current_official_piste_page_review'
        state['canonical_log_merged']=False
        events.append(row); path.write_text(json.dumps(events,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        save()
        status=str(row.get('HTTP_status',''))
        if status in ['401','403','429'] or status.startswith('5'):
            state['provider_collection_halted']=True; save()
            raise RuntimeError('Provider denial/rate/server error retained; batch stops, no bypass/retry')
    collect_evidence.append_log=isolated_log
    sys.argv=['collect_evidence','--config',QUEUE,'--limit',str(args.limit)]
    try:
        collect_evidence.main()
    finally:
        save()
    print('Official page collection:',state['archived_page_count'],'/',state['page_count'],'archived; isolated events not yet merged.')


if __name__=='__main__':
    main()
