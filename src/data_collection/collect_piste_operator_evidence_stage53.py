"""Finite remaining official-link queue. Cache and failures survive interruption.

Preparation follows exact existing stable-ID official joins only. It is NOT
OSM assignment. Every other URL must be a literal link in an archived parent.
"""
import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, quote
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_evidence

CONFIG = 'config/piste_operator_evidence_stage53.json'
EVENTS = 'data_interim/piste_operator_events_stage53.json'


def local_network_block(error):
    return '[WinError 10013]' in str(error)


def local_url_encoding_error(error):
    return 'UnicodeEncodeError' in str(error) and "'ascii' codec" in str(error)


def request_url(url):
    """Percent-encode literal Unicode URL, preserving existing URI escapes."""
    p=urlsplit(url)
    return urlunsplit((p.scheme,p.netloc,quote(p.path,safe='/%:@!$&\'()*+,;=-._~'),
        quote(p.query,safe='=&%/?@:!$\'()*+,;~-._'),quote(p.fragment,safe='%')))


def prepare():
    prior = pd.read_csv(ROOT/'data_processed/winter_profile_piste_assignment_stage52.csv', dtype=str, keep_default_na=False)
    remaining = set(prior.loc[prior.current_site_correspondence_verified.ne('True'), 'station_group_id'])
    pages = {p['source_id']: p for p in json.loads((ROOT/'reports/piste_official_page_audit_stage49_summary.json').read_text(encoding='utf-8'))['cases']}
    links = json.loads((ROOT/'reports/piste_official_page_collection_stage49_summary.json').read_text(encoding='utf-8'))['group_links']
    cache = {}
    for path in (ROOT/'data_external/source_evidence').glob('*.metadata.json'):
        meta = json.loads(path.read_text(encoding='utf-8'))
        cache.setdefault(meta.get('url'), meta)
    sources = []
    for link in links:
        if link['station_group_id'] not in remaining or not link.get('source_id'): continue
        page = pages[link['source_id']]
        for nav in page['navigation_links']:
            if nav.get('label') != 'Site web': continue
            existing = next((s for s in sources if s['url'] == nav['url']), None)
            if existing:
                existing['official_group_links'].append(dict(station_group_id=link['station_group_id'], parent_source_id=link['source_id']))
                continue
            meta = cache.get(nav['url'])
            sources.append(dict(source_id=meta['source_id'] if meta else 'OPERATOR_REMAINING_'+str(len(sources)+1).zfill(2)+'_STAGE53',
                url=nav['url'], organisation=page['original_destination_name'], suffix='html',
                station_group_id=link['station_group_id'], parent_source_id=link['source_id'],
                official_group_links=[dict(station_group_id=link['station_group_id'], parent_source_id=link['source_id'])]))
    path = ROOT/CONFIG
    if path.exists():
        if json.loads(path.read_text(encoding='utf-8')) != sources: raise ValueError('Existing queue changed; do not overwrite')
    else: path.write_text(json.dumps(sources, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Remaining', len(remaining), 'groups;', len(sources), 'distinct exact operator URLs. No assignment.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--config', default=CONFIG)
    args = parser.parse_args()
    if args.prepare: prepare(); return
    sources = json.loads((ROOT/args.config).read_text(encoding='utf-8'))
    path = ROOT/EVENTS
    events = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    canonical = pd.read_csv(ROOT/'logs/data_collection_log.csv', dtype=str, keep_default_na=False)
    # Do not repeat a known failed host, including earlier evidence batches.
    failures = canonical[canonical.status.eq('failed') & ~canonical.error.map(local_network_block) & ~canonical.error.map(local_url_encoding_error)]
    # A404 identifies a missing URL, not a forbidden host. A separately
    # discovered, exact new official URL can be collected; the broken URL is
    # never retried. All other remote failures block their host conservatively.
    failed_urls=set(failures.source_url)
    failed_hosts = {urlsplit(r.source_url).hostname for r in failures.itertuples() if r.source_url and r.HTTP_status!='404'}
    original_log = collect_evidence.append_log
    original_fetch = collect_evidence.fetch
    collect_evidence.fetch = lambda url: original_fetch(request_url(url))
    def append(row):
        row['task'] = 'stage53_remaining_official_operator_verification'
        events.append(row)
        path.write_text(json.dumps(events, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        original_log(row)
    collect_evidence.append_log = append
    for source in sources:
        hostname = urlsplit(source['url']).hostname
        cached = list((ROOT/'data_external/source_evidence').glob(source['source_id']+'_*.metadata.json'))
        if (hostname in failed_hosts or source['url'] in failed_urls) and not cached:
            if not any(e['source_id'] == source['source_id'] for e in events):
                append(dict(timestamp=collect_evidence.datetime.now(collect_evidence.timezone.utc).isoformat(),
                    source_id=source['source_id'], source_url=source['url'], status='not_requested_prior_failed_host',
                    error='Prior failed host retained; no retry', success='False'))
            print(source['source_id'], 'prior failed host retained, no request', flush=True)
            continue
        sys.argv = ['collect_evidence', '--config', args.config, '--source-id', source['source_id']]
        before = len(events)
        collect_evidence.main()
        if len(events) > before and events[-1].get('status') == 'failed':
            if local_network_block(events[-1].get('error')):
                print('Local socket permission block: queue paused, provider not classified unavailable', flush=True)
                break
            failed_urls.add(source['url'])
            if str(events[-1].get('HTTP_status'))!='404':failed_hosts.add(hostname)
        print(source['source_id'], 'checkpoint saved', flush=True)


if __name__ == '__main__': main()
