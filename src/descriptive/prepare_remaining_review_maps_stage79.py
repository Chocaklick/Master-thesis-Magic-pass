"""Offline discovery displays only; rectangles never establish correspondence."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'data_interim/matplotlib_stage79'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pyproj import Transformer
from shapely.geometry import LineString, box
from src.descriptive.review_piste_candidates_stage53 import originals

# Diagnostic windows deliberately contain neighbouring operators for review.
CASES = {
    'grimentz_zinal': (2604,1103,2618,1119),
    'gstaad': (2579,1140,2601,1166),
    'tlml': (2561,1132,2579,1144),
    'tvgd': (2567,1124,2588,1136),
    'torrent': (2611,1128,2619,1139),
}


def main():
    index, _, sites = originals()
    transform = Transformer.from_crs(4326,2056,always_xy=True)
    context = json.loads((ROOT/'data_interim/piste_remaining_stage78/lift_context.json').read_text(encoding='utf-8'))
    lifts = {r['fid']:r for c in context['cases'] for r in c['legacy_lifts']}
    records = {}
    for name,bounds in CASES.items():
        area = box(*(v*1000 for v in bounds)); objects=[]
        fig, ax = plt.subplots(figsize=(14,12))
        for (kind,wid),e in index.items():
            if kind != 'way' or e.get('tags',{}).get('piste:type') != 'downhill':continue
            geom=e.get('geometry',[])
            if len(geom)<2:continue
            cs=[transform.transform(p['lon'],p['lat']) for p in geom]
            if not area.intersects(LineString(cs)):continue
            tags=e.get('tags',{}); site_ids=[s for s,site in sites.items() if wid in site['selected_downhill_way_ids']]
            objects.append(dict(osm_way_id=wid, original_tags=tags, site_relation_ids=site_ids, geometry_lv95=cs))
            ax.plot([p[0]/1000 for p in cs],[p[1]/1000 for p in cs],color='#666666',lw=.75)
            mid=cs[len(cs)//2]
            ax.text(mid[0]/1000,mid[1]/1000,str(wid)+' '+tags.get('name',''),fontsize=5)
        for lift in lifts.values():
            for cs in lift['coordinates_lv95']:
                if not area.intersects(LineString(cs)):continue
                ax.plot([p[0]/1000 for p in cs],[p[1]/1000 for p in cs],color='#007b37',lw=1.7)
                mid=cs[len(cs)//2];ax.text(mid[0]/1000,mid[1]/1000,'L'+str(lift['fid'])+' '+str(lift['name']),fontsize=7,color='#007b37')
        ax.set_xlim(bounds[0],bounds[2]);ax.set_ylim(bounds[1],bounds[3]);ax.set_aspect('equal')
        ax.ticklabel_format(useOffset=False,style='plain');ax.set_title(name+' — candidats, aucune attribution automatique')
        fig.tight_layout();fig.savefig(ROOT/f'reports/figures/piste_candidate_stage79_{name}.png',dpi=180);plt.close(fig)
        records[name]=dict(diagnostic_bounds_km_lv95=bounds,objects=objects)
        print(name,len(objects),'candidate objects, not accepted')
    folder=ROOT/'data_interim/piste_remaining_stage79';folder.mkdir(parents=True,exist_ok=True)
    (folder/'candidate_networks.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
