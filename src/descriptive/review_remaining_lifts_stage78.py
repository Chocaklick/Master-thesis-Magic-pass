"""Add immutable legacy lift geometries to individual candidate views, no join.

Source fids and UUIDs are never treated as OSM IDs or accepted station clusters.
The geometry is contextual and has no newly inferred observation date.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'data_interim/matplotlib_stage78'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely import from_wkb
from shapely.geometry import Point
from pyproj import Transformer
from src.descriptive.verify_piste_assignments_stage51 import sha


def main():
    a = json.loads((ROOT/'data_interim/piste_remaining_stage78/candidate_inventory.json').read_text(encoding='utf-8'))
    database = ROOT/'data_raw/bahnen-winter_2056.gpkg'
    c = sqlite3.connect('file:'+database.as_posix()+'?mode=ro', uri=True)
    lifts = []
    for fid, blob, name, uuid, kind in c.execute('SELECT fid,geom,name,tlm_uuid,type FROM transport_winter_2056'):
        if blob[:2] != b'GP': raise ValueError('Require standard GPKG header')
        envelope = (blob[3] >> 1) & 7
        size = {0:0, 1:32, 2:48, 3:48, 4:64}[envelope]
        geometry = from_wkb(blob[8+size:])
        lifts.append(dict(fid=fid, name=name, tlm_uuid=uuid, type=kind, geometry=geometry))
    transform = Transformer.from_crs(4326, 2056, always_xy=True)
    details = []
    for number, case in enumerate(a['cases'], 1):
        points = [Point(*transform.transform(p['reference_longitude'], p['reference_latitude'])) for p in case['reference_points']]
        local = [lift for lift in lifts if min(p.distance(lift['geometry']) for p in points) <= 10000]
        selected = [r for r in case['candidate_objects'] if r['review_distance_m'] <= 6000 and r['original_tags'].get('piste:type') == 'downhill']
        fig, ax = plt.subplots(figsize=(11, 8))
        for r in selected:
            cs=r['geometry_lv95']; tags=r['original_tags']; middle=cs[len(cs)//2]
            ax.plot([v[0]/1000 for v in cs], [v[1]/1000 for v in cs], color='#666666', lw=.7)
            ax.text(middle[0]/1000, middle[1]/1000, str(r['osm_way_id'])+' '+tags.get('name', tags.get('piste:name','')), fontsize=5)
        for lift in local:
            if min(p.distance(lift['geometry']) for p in points) > 6000: continue
            for line in getattr(lift['geometry'], 'geoms', [lift['geometry']]):
                cs=list(line.coords)
                ax.plot([v[0]/1000 for v in cs], [v[1]/1000 for v in cs], color='#078445', lw=2)
                middle=cs[len(cs)//2]
                ax.text(middle[0]/1000, middle[1]/1000, 'L'+str(lift['fid'])+' '+str(lift['name']), fontsize=7, color='#006b34')
        for p in points: ax.scatter(p.x/1000,p.y/1000,color='#d84315',marker='x',s=50)
        ax.set_aspect('equal',adjustable='datalim');ax.ticklabel_format(useOffset=False,style='plain')
        ax.set_xlabel('Est LV95 (km)');ax.set_ylabel('Nord LV95 (km)')
        ax.set_title(case['station_group_name']+' — pistes OSM et remontées originales de contexte',fontsize=11)
        path=f'reports/figures/piste_lift_context_stage78_{number:02d}.png'
        fig.tight_layout();fig.savefig(ROOT/path,dpi=160);plt.close(fig)
        details.append(dict(station_group_id=case['station_group_id'],context_map=path,
            legacy_lifts=[{**{k:v for k,v in x.items() if k!='geometry'},'coordinates_lv95':[list(y.coords) for y in getattr(x['geometry'],'geoms',[x['geometry']])]} for x in local]))
    target=ROOT/'data_interim/piste_remaining_stage78/lift_context.json'
    target.write_text(json.dumps(dict(source_sha256=sha('data_raw/bahnen-winter_2056.gpkg'), observation_date='UNKNOWN',
        manual_context_only=True, automatic_assignments=False,cases=details),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('30 context maps; original lift features',len(lifts),'no assignments')


if __name__=='__main__': main()
