"""Finite metadata queue from preserved original candidate-axis coordinates.

Only catalogue metadata: no raster/profile inference, grouping or exclusion.
The completed St-Luc catalogue is reused rather than queried a second time.
"""
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha

CONFIG = 'config/terrain_group_catalogue_sources_stage65.json'
PLAN = 'data_interim/terrain_extension_plan_stage65.json'


def build_queue(groups, members, index, items_url):
    records = []
    for g in groups.itertuples():
        if pd.isna(g.exact_unique_mapped_axis_length_m) or g.station_group_id == 'MP_GROUP_RESORT__st_luc_chandolin':
            continue
        selected = members[members.station_group_id.eq(g.station_group_id) & members.candidate_role.eq('way_axis_candidate')]
        if selected.empty or not selected.geometry_status.eq('valid_axis_candidate').all():
            raise ValueError('Mapped-axis group requires preserved valid original axes')
        coords = [p for r in selected.itertuples() for p in index[(r.osm_type, int(r.osm_id))]['geometry']]
        bbox = [min(p['lon'] for p in coords), min(p['lat'] for p in coords),
                max(p['lon'] for p in coords), max(p['lat'] for p in coords)]
        if not (-180 < bbox[0] < bbox[2] < 180 and -90 < bbox[1] < bbox[3] < 90):
            raise ValueError('Invalid original geographic bounding box')
        token = hashlib.sha256(g.station_group_id.encode()).hexdigest()[:12].upper()
        records.append(dict(source_id='SWISSTOPO_ALTI3D_GROUP_ITEMS_STAGE65_' + token + '_P001',
                            url=items_url + '?' + urlencode({'bbox': ','.join(map(str, bbox)), 'limit': 100}),
                            station_group_id=g.station_group_id, station_group_name=g.station_group_name,
                            bbox_wgs84=bbox, original_axis_ids=sorted(int(v) for v in selected.osm_id),
                            organisation='Office fédéral de topographie swisstopo', suffix='json',
                            purpose='Complete dated native2m catalogue extension from preserved mapped candidate axes; all editions retained; no profile/exclusion',
                            parent_source_id='SWISSTOPO_ALTI3D_COLLECTION_STAGE61', page_number=1))
    if len(records) != 39 or len({r['source_id'] for r in records}) != 39:
        raise ValueError('Expected all39remaining mapped-axis groups, not an arbitrary subset')
    return records


def main():
    paths = ['src/data_collection/prepare_terrain_extension_stage65.py',
             'data_processed/winter_profile_exact_piste_overlap_stage63.csv',
             'data_processed/winter_profile_verified_piste_member_qa_stage60.csv',
             'reports/terrain_orientation_stage64_summary.json', 'reports/terrain_catalogue_stage61_summary.json']
    inputs = {p: sha(p) for p in paths}
    for p in paths[-2:]:
        previous = json.loads((ROOT / p).read_text(encoding='utf8'))
        for f, h in {**previous['input_sha256'], **previous['output_sha256']}.items():
            if sha(f) != h:
                raise ValueError('Frozen previous result changed: ' + f)
    metas = list((ROOT / 'data_external/source_evidence').glob('SWISSTOPO_ALTI3D_COLLECTION_STAGE61_*.metadata.json'))
    if len(metas) != 1:
        raise ValueError('Require one archived official collection')
    meta = json.loads(metas[0].read_text(encoding='utf8'))
    if sha(meta['raw_file']) != meta['sha256']:
        raise ValueError('Collection original changed')
    inputs[meta['raw_file']] = meta['sha256']
    collection = json.loads((ROOT / meta['raw_file']).read_bytes())
    links = [l['href'] for l in collection['links'] if l['rel'] == 'items']
    if collection['id'] != 'ch.swisstopo.swissalti3d' or len(links) != 1:
        raise ValueError('Require literal official items link')
    groups = pd.read_csv(ROOT / paths[1])
    members = pd.read_csv(ROOT / paths[2], dtype=str, keep_default_na=False)
    index, _, _ = originals()
    queue = build_queue(groups, members, index, links[0])
    state = dict(date='2026-10-10', input_sha256=inputs, all_groups_retained=len(groups),
                 new_catalogue_group_count=len(queue), pilot_catalogue_reused='SWISSTOPO_ALTI3D_STLUC_ITEMS_STAGE61',
                 no_raster_collection_or_new_profile_fit=True)
    for target, payload in [(ROOT / CONFIG, queue), (ROOT / PLAN, state)]:
        if target.exists():
            if json.loads(target.read_text(encoding='utf8')) != payload:
                raise ValueError('Frozen extension plan differs: ' + target.name)
        else:
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in state.items() if k != 'input_sha256'}))


if __name__ == '__main__':
    main()
