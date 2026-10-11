"""New metadata only for27newly mapped groups; completed40catalogues reused."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.descriptive.review_piste_candidates_stage53 import originals
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def main():
    paths=['data_processed/winter_profile_metric_network_stage80.csv',
        'data_processed/winter_profile_piste_members_stage79.csv',
        'data_processed/terrain_reference_profiles_stage67.csv',
        'src/data_collection/prepare_reviewed_terrain_catalogue_stage80.py',
        'reports/reviewed_piste_network_stage80_summary.json']
    inputs={p:sha(p) for p in paths}
    groups=pd.read_csv(ROOT/paths[0]); members=pd.read_csv(ROOT/paths[1])
    old=pd.read_csv(ROOT/paths[2]); completed=set(old.loc[old.unique_mapped_axis_length_m.notna(),'station_group_id'])
    pending=groups[groups.measured_unique_proxy_axis_length_m.notna() & ~groups.station_group_id.isin(completed)]
    if len(pending)!=27:raise ValueError('Require all27newmapped groups, not a pilot selected by outcome')
    metas=list((ROOT/'data_external/source_evidence').glob('SWISSTOPO_ALTI3D_COLLECTION_STAGE61_*.metadata.json'))
    if len(metas)!=1:raise ValueError('Require observed official collection')
    m=json.loads(metas[0].read_text(encoding='utf-8'))
    if sha(m['raw_file'])!=m['sha256']:raise ValueError('Official collection changed')
    inputs[m['raw_file']]=m['sha256']; inputs[metas[0].relative_to(ROOT).as_posix()]=sha(metas[0].relative_to(ROOT).as_posix())
    collection=json.loads((ROOT/m['raw_file']).read_bytes())
    links=[x['href'] for x in collection['links'] if x['rel']=='items']
    if len(links)!=1:raise ValueError('Literal items link required')
    index,_,_=originals(); queue=[]
    for g in pending.itertuples():
        p=members[members.station_group_id.eq(g.station_group_id) & members.candidate_role.eq('way_axis_candidate')]
        cs=[v for r in p.itertuples() for v in index[('way',int(r.osm_id))]['geometry']]
        bbox=[min(c['lon'] for c in cs),min(c['lat'] for c in cs),max(c['lon'] for c in cs),max(c['lat'] for c in cs)]
        token=hashlib.sha256(g.station_group_id.encode()).hexdigest()[:12].upper()
        queue.append(dict(source_id='SWISSTOPO_ALTI3D_GROUP_ITEMS_STAGE80_'+token+'_P001',
            url=links[0]+'?'+urlencode({'bbox':','.join(map(str,bbox)),'limit':100}),
            station_group_id=g.station_group_id,station_group_name=g.display_scope_name,bbox_wgs84=bbox,
            original_axis_ids=sorted(int(x) for x in p.osm_id),organisation='Office fédéral de topographie swisstopo',
            suffix='json',purpose='All27newmapped groups, full geographic bbox including FrenchDole-Tuffes; native2m latest-per-tile rule unchanged, no profile/value inferred',
            parent_source_id='SWISSTOPO_ALTI3D_COLLECTION_STAGE61',page_number=1))
    target=ROOT/'config/terrain_group_catalogue_sources_stage80.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf-8'))!=queue:raise ValueError('Frozen catalogue plan differs')
    else:target.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    state=dict(completed_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        input_sha256=inputs,output_sha256={target.relative_to(ROOT).as_posix():sha(target.relative_to(ROOT).as_posix())},
        new_catalogue_group_count=27,completed_catalogue_group_count_reused=40,
        no_profile_raster_download_or_outcome_selection=True)
    proof=ROOT/'reports/reviewed_terrain_catalogue_plan_stage80_summary.json'
    if not proof.exists():proof.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('27 new official metadata queries prepared; completed40not repeated')


if __name__=='__main__':main()
