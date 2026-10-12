"""Exact native cells and nine Horn neighbours; immutable caches reused."""
import json
import math
import sys
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from shapely import wkt
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def required_keys(geometry):
    """Exact source ownership grid already header-verified, no geometric buffer."""
    weights=cell_lengths(geometry,0,0,2,2)
    central=set();neighbours=set()
    for r,c in weights:
        e,n=2*c+1,-2*r-1
        central.add(f'{math.floor(e/1000)}-{math.floor(n/1000)}')
        for dx in (-2,0,2):
            for dy in (-2,0,2):neighbours.add(f'{math.floor((e+dx)/1000)}-{math.floor((n+dy)/1000)}')
    return central,neighbours,len(weights)


def main():
    paths=['src/data_collection/prepare_reviewed_terrain_queue_stage81.py',
        'data_interim/winter_profile_metric_network_stage80.json',
        'data_processed/terrain_reviewed_asset_inventory_stage80.csv',
        'reports/reviewed_geometry_followup_stage80_summary.json',
        'config/terrain_french_complement_decision_stage80.json',
        'src/data_processing/terrain_cell_weights_stage61.py']
    inputs={p:sha(p) for p in paths}
    decision=json.loads((ROOT/paths[4]).read_text(encoding='utf-8'))
    if decision['french_source_complement']!='none':raise ValueError('No French complement authorised')
    nets=json.loads((ROOT/paths[1]).read_text(encoding='utf-8'))
    inventory=pd.read_csv(ROOT/paths[2],dtype=str,keep_default_na=False)
    latest=inventory[inventory.latest_reference_for_native_tile.eq('True')]
    bykey={}
    for key,part in latest.groupby('native_tile_key'):
        if part.asset_url.nunique()!=1 or part.asset_sha256.nunique()!=1 or part.item_reference_datetime.nunique()!=1:
            raise ValueError('Conflicting literal latest-per-tile selection '+key)
        bykey[key]=part.iloc[0].to_dict()
    cached=json.loads((ROOT/paths[3]).read_text(encoding='utf-8'))['cached_assets']
    byurl={r['asset_url']:r for r in cached}
    groups=[];needs=defaultdict(set);centres=defaultdict(set)
    for n in nets:
        gid=n['station_group_id'];geometry=n['measured_unique_proxy_axis_wkt']
        if geometry is None:
            groups.append(dict(station_group_id=gid,status='missing_geometry_not_zero',group_retained=True));continue
        mainkeys,keys,count=required_keys(wkt.loads(geometry))
        for key in keys:needs[key].add(gid)
        for key in mainkeys:centres[key].add(gid)
        groups.append(dict(station_group_id=gid,status='exact_native_keys_planned',group_retained=True,
            native_axis_cell_count=count,axis_native_tile_keys=sorted(mainkeys),horn_native_tile_keys=sorted(keys),
            catalogue_absent_native_tile_keys=sorted(keys-set(bykey))))
    queue=[]
    for key in sorted(set(needs)&set(bykey)):
        r=bykey[key];cache=byurl.get(r['asset_url'])
        sid=cache['source_id'] if cache else 'SWISSTOPO_ALTI3D_TILE_STAGE81_'+r['asset_id'].removesuffix('.tif').upper()
        queue.append(dict(source_id=sid,url=r['asset_url'],organisation='Office fédéral de topographie swisstopo',suffix='tif',
            expected_sha256=r['asset_sha256'],native_tile_key=key,asset_id=r['asset_id'],
            item_reference_datetime=r['item_reference_datetime'],
            asset_created_datetime=r['asset_created_datetime'] or None,asset_updated_datetime=r['asset_updated_datetime'] or None,
            station_group_ids=sorted(needs[key]),central_axis_group_ids=sorted(centres[key]),
            parent_source_ids=sorted(latest[latest.native_tile_key.eq(key)].catalogue_page_source_id.unique()),
            cached_raw_file=cache['raw_file'] if cache else None,
            purpose='Approved latest native Swiss2m; exact axis cells and nine Horn neighbours only; no French raster/resampling/preentry certification'))
    qpath='config/terrain_reviewed_tile_sources_stage81.json'
    target=ROOT/qpath
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8'))!=queue:raise ValueError('Frozen exact queue differs')
    else:target.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,output_sha256={qpath:sha(qpath)},
        group_count=len(groups),groups_with_geometry=sum(g['status']=='exact_native_keys_planned' for g in groups),
        required_available_native_tile_count=len(queue),cached_required_tile_count=sum(bool(r['cached_raw_file']) for r in queue),
        new_required_tile_count=sum(not r['cached_raw_file'] for r in queue),
        unavailable_catalogue_key_count=len(set(needs)-set(bykey)),groups=groups,
        no_french_raster_or_geometry_cut=True,no_original_or_old_profile_change=True)
    path=ROOT/'reports/reviewed_terrain_queue_stage81_summary.json'
    if path.exists():
        old=json.loads(path.read_text(encoding='utf-8'))
        if old['input_sha256']!=inputs or old['output_sha256']!=state['output_sha256']:raise ValueError('Frozen exact queue proof differs')
    else:path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','groups']},ensure_ascii=False))


if __name__=='__main__':main()
