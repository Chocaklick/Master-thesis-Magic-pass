"""Bounded metadata pilot, not tile-vintage selection or domain exclusion."""
import json
import sys
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha


def main():
    metas=list((ROOT/'data_external/source_evidence').glob('SWISSTOPO_ALTI3D_COLLECTION_STAGE61_*.metadata.json'))
    if len(metas)!=1:raise ValueError('Require single archived collection')
    meta=json.loads(metas[0].read_text(encoding='utf8'))
    if sha(meta['raw_file'])!=meta['sha256']:raise ValueError('Collection original changed')
    collection=json.loads((ROOT/meta['raw_file']).read_bytes())
    if collection['id']!='ch.swisstopo.swissalti3d' or 2.0 not in collection['summaries']['gsd']:raise ValueError('Wrong model or absent approved resolution')
    links=[l['href'] for l in collection['links'] if l['rel']=='items']
    if len(links)!=1:raise ValueError('Require explicit provider items link')
    index,_,sites=originals()
    coords=[p for i in sites[5976698]['selected_downhill_way_ids'] for p in index[('way',i)]['geometry']]
    bbox=[min(p['lon'] for p in coords),min(p['lat'] for p in coords),max(p['lon'] for p in coords),max(p['lat'] for p in coords)]
    query=links[0]+'?'+urlencode({'bbox':','.join(map(str,bbox)),'limit':100})
    config=[dict(source_id='SWISSTOPO_ALTI3D_STLUC_ITEMS_STAGE61',url=query,organisation='Official swisstopo geo.admin.ch STAC',suffix='json',purpose='Bounded StLuc current candidate-footprint metadata pilot; all editions/asset dates retained for audit; no selection or exclusion',parent_source_id=meta['source_id'])]
    target=ROOT/'config/terrain_pilot_query_stage61.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8'))!=config:raise ValueError('Existing pilot query differs')
    else:target.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(bbox=bbox,query_url=query,collection_license=collection['license'],no_tile_selection=True)))


if __name__=='__main__':main()
