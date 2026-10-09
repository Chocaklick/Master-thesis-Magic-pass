"""Complete the tags of ALL referenced ways/relations absent from initial query.

One finite request, no spatial cutoff or accepted station assignment. Separate
immutable response: never merge versions silently into the original snapshot.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_evidence import append_log
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS

INPUT = 'data_interim/winter_profile_piste_all_site_group_pairs.json'
CHECKPOINT = 'reports/piste_missing_member_collection_summary.json'
SOURCE = 'OSM_PISTE_REFERENCED_MEMBER_TAGS_2026_10_09'
ENDPOINT = 'https://overpass-api.de/api/interpreter'


def requested_members(detail):
    return sorted({(m['type'], m['id']) for s in detail['sites'] for m in s['member_references_outside_query'] if m['type'] in ['way', 'relation']})


def validate(payload, requested):
    if payload.get('remark') or not payload.get('osm3s', {}).get('timestamp_osm_base'):
        raise ValueError('Incomplete response or missing snapshot')
    observed = [(e['type'], e['id']) for e in payload.get('elements', [])]
    if len(observed) != len(set(observed)) or not set(observed) <= set(requested):
        raise ValueError('Duplicate or unsolicited identifiers')
    if any(not e.get('version') or not e.get('timestamp') for e in payload['elements']):
        raise ValueError('Missing original version or edit date')
    return sorted(set(requested) - set(observed))


def register(state):
    path = ROOT / 'metadata/data_sources_master.csv'
    master = pd.read_csv(path, dtype=str, keep_default_na=False)
    record = dict(source_id=SOURCE, variable_name='referenced_piste_member_original_tags',
        variable_description='Original tags for all ways and relations outside initial piste selection; no geographic assignment',
        source_organisation='OpenStreetMap contributors via Overpass API', source_dataset_name='Stage46 referenced member completion',
        source_page_url='https://wiki.openstreetmap.org/wiki/Tag:site=piste', api_endpoint=ENDPOINT,
        api_parameters=state['query'], retrieval_method='One bounded finite ID query, no retries; separate immutable snapshot',
        retrieval_date=state['retrieval_date'], local_raw_file=state.get('raw_file', ''),
        geographic_level='All referenced ways/relations absent from the original 238 site inventory', temporal_resolution='current OSM snapshot',
        license='OpenStreetMap contributors ODbL', transformation_applied='None: original JSON bytes; unreturned IDs retained as unresolved',
        quality_notes='Status=' + state['status'] + '; current metadata not historical construction evidence; nodes not needed for downhill line tagging',
        notes='Parent source OSM_DOWNHILL_SWISS_CURRENT_2026_10_09; sha256=' + state.get('sha256', ''))
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), path)


def main():
    detail = json.loads((ROOT / INPUT).read_text(encoding='utf-8'))
    requested = requested_members(detail)
    input_sha = hashlib.sha256((ROOT / INPUT).read_bytes()).hexdigest()
    checkpoint = ROOT / CHECKPOINT
    if checkpoint.exists():
        prior = json.loads(checkpoint.read_text(encoding='utf-8'))
        if prior['input_sha256'] != input_sha:
            raise ValueError('Changed inputs: keep existing checkpoint')
        if prior['status'] == 'complete':
            content = (ROOT / prior['raw_file']).read_bytes()
            if hashlib.sha256(content).hexdigest() != prior['sha256']:
                raise ValueError('Source hash changed')
            validate(json.loads(content), requested)
        print('Existing member collection checkpoint retained; no requests or retries.')
        return
    selections = ''.join(kind + '(id:' + ','.join(str(i) for k, i in requested if k == kind) + ');' for kind in ['way', 'relation'] if any(k == kind for k, _ in requested))
    query = '[out:json][timeout:60][maxsize:134217728];(' + selections + ');out meta geom;'
    stamp = datetime.now(timezone.utc)
    state = dict(source_id=SOURCE, retrieval_date=stamp.isoformat(), input_sha256=input_sha, query=query,
        requested_way_count=sum(k == 'way' for k, _ in requested), requested_relation_count=sum(k == 'relation' for k, _ in requested),
        status='failed', assignment_applied=False, features_computed=False)
    folder = ROOT / 'data_external/source_evidence'
    token = stamp.strftime('%Y%m%dT%H%M%SZ')
    try:
        req = Request(ENDPOINT, data=urlencode({'data': query}).encode(), headers={'User-Agent': 'ThesisSkiResearch/0.1 (finite piste member audit)', 'Content-Type': 'application/x-www-form-urlencoded'})
        with urlopen(req, timeout=75) as response:
            content = response.read(100000001)
            state.update(http_status=response.status, final_url=response.geturl())
        if len(content) > 100000000:
            raise ValueError('Bounded response limit exceeded')
        raw = folder / f'{SOURCE}_{token}.json'
        with raw.open('xb') as stream:
            stream.write(content)
        state.update(raw_file=raw.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content))
        payload = json.loads(content)
        missing = validate(payload, requested)
        state.update(status='complete', osm_snapshot=payload['osm3s']['timestamp_osm_base'], element_count=len(payload['elements']),
            unreturned_member_ids=[dict(type=k, id=i) for k, i in missing])
    except Exception as exc:
        state.update(error=f'{type(exc).__name__}: {exc}', http_status=getattr(exc, 'code', state.get('http_status')))
        if isinstance(exc, HTTPError):
            path = folder / f'{SOURCE}_{token}.error.txt'
            with path.open('xb') as stream:
                stream.write(exc.read())
            state['error_response_file'] = path.relative_to(ROOT).as_posix()
    with (folder / f'{SOURCE}_{token}.metadata.json').open('x', encoding='utf-8') as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
    checkpoint.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    register(state)
    append_log(dict(timestamp=stamp.isoformat(), task='stage46_piste_member_tag_completion', source_id=SOURCE,
        source='OpenStreetMap contributors via Overpass API', source_url=ENDPOINT, **{'URL/API': ENDPOINT}, request=query,
        retrieval_method='one finite bounded ID query; no retry', HTTP_status=state.get('http_status', ''),
        status=state['status'], raw_file=state.get('raw_file', ''), checksum=state.get('sha256', ''), success=str(state['status'] == 'complete'), error=state.get('error', '')))
    print(json.dumps({k:v for k,v in state.items() if k != 'query'}, ensure_ascii=True))


if __name__ == '__main__':
    main()
