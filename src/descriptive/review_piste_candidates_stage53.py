"""Offline original-member candidate maps. No correspondence inferred."""
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'data_interim/matplotlib_stage53'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from pyproj import Transformer
import pandas as pd
from src.descriptive.audit_completed_piste_membership import audit
from src.descriptive.verify_piste_assignments_stage51 import sha


def originals():
    index={}; payloads=[]
    for path in ['data_interim/current_piste_geometry_collection_checkpoint.json','reports/piste_missing_member_collection_summary.json']:
        meta=json.loads((ROOT/path).read_text(encoding='utf-8'))
        if sha(meta['raw_file'])!=meta['sha256']:raise ValueError('Original geometry changed')
        payload=json.loads((ROOT/meta['raw_file']).read_bytes());payloads.append(payload)
        for e in payload['elements']:
            key=(e['type'],e['id'])
            if key in index:raise ValueError('Duplicate original object')
            index[key]=e
    counts,sites=audit(*payloads)
    return index,counts,{s['osm_relation_id']:s for s in sites}


def main():
    candidates=json.loads((ROOT/'config/piste_assignment_candidates_stage53.json').read_text(encoding='utf-8'))
    index,counts,sites=originals()
    points=pd.read_csv(ROOT/'data_processed/accessibility_station_access_points.csv',keep_default_na=False)
    transform=Transformer.from_crs(4326,2056,always_xy=True)
    details=[]
    for batch in range((len(candidates)+5)//6):
        fig,axes=plt.subplots(2,3,figsize=(15,9))
        subset=candidates[batch*6:batch*6+6]
        for ax,case in zip(axes.flat,subset):
            site=sites[case['osm_site_relation_id']]
            lifts=[index[(m['type'],m['id'])] for m in site['member_references_outside_query'] if (m['type'],m['id']) in index and index[(m['type'],m['id'])].get('tags',{}).get('aerialway')]
            for elements,color in [([index[('way',i)] for i in site['selected_downhill_way_ids']],'#999999'),(lifts,'#1565c0')]:
                for e in elements:
                    geom=e.get('geometry',[])
                    if len(geom)<2:continue
                    x,y=transform.transform([p['lon'] for p in geom],[p['lat'] for p in geom])
                    ax.plot([v/1000 for v in x],[v/1000 for v in y],color=color,lw=1)
            for r in points[points.station_group_id.eq(case['station_group_id'])].itertuples():
                x,y=transform.transform(r.reference_longitude,r.reference_latitude)
                ax.scatter(x/1000,y/1000,color='#d84315',marker='x',s=30)
            ax.set_title(str(site['osm_relation_id'])+' '+site['name']);ax.set_aspect('equal',adjustable='datalim')
            ax.ticklabel_format(useOffset=False,style='plain');ax.xaxis.set_major_locator(MaxNLocator(4));ax.yaxis.set_major_locator(MaxNLocator(4))
            ax.set_xlabel('Est LV95 (km)');ax.set_ylabel('Nord LV95 (km)')
            details.append(dict(**case,site=site,lifts=[dict(id=e['id'],tags=e.get('tags',{})) for e in lifts],
                membership=counts[counts.osm_site_relation_id.eq(site['osm_relation_id'])].iloc[0].to_dict(),
                map=f'reports/figures/piste_candidates_stage53_{batch+1}.png'))
        for ax in list(axes.flat)[len(subset):]:ax.set_visible(False)
        fig.suptitle('Candidats non acceptés : descentes grises, remontées bleues, références orange. Aucun rayon.',fontsize=12)
        fig.tight_layout();fig.savefig(ROOT/f'reports/figures/piste_candidates_stage53_{batch+1}.png',dpi=140);plt.close(fig)
    (ROOT/'data_interim/piste_candidate_review_stage53.json').write_text(json.dumps(details,ensure_ascii=False,indent=2,default=lambda x:x.item())+'\n',encoding='utf-8')
    print(len(details),'candidate views. No registry or assignment written.')


if __name__=='__main__':main()
