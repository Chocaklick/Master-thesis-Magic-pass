"""Historical preservation plus prospective clustering coverage, no fitted groups."""
import json
import subprocess
import sys
from datetime import datetime,timezone
from io import StringIO
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.descriptive.build_remaining_piste_assignments_stage78 import read,digest,REGISTRY


def main():
    parent_path='reports/preservation_stage80_summary.json';parent=json.loads((ROOT/parent_path).read_text())
    hashes={r['path']:r['sha256'] for r in parent['checks']}
    manifests=['reports/reviewed_terrain_queue_stage81_summary.json','reports/terrain_reviewed_profiles_stage82_summary.json',
        'reports/spass_reviewed_profiles_stage83_summary.json','reports/reviewed_profile_registry_stage83_summary.json']
    for p in manifests:
        m=json.loads((ROOT/p).read_text())
        candidates=m.get('input_sha256',{})|m.get('output_sha256',{})|{p:sha(p)}
        for checkpoint in m.get('daily_checkpoints',{}).values():
            candidates[checkpoint['path']]=checkpoint['sha256'];candidates[checkpoint['metadata']]=checkpoint['metadata_sha256']
        for path,h in candidates.items():
            if path in hashes and hashes[path]!=h:raise ValueError('Conflicting original/frozen proof '+path)
            hashes[path]=h
    hashes[parent_path]=sha(parent_path)
    for p,h in hashes.items():
        if sha(p)!=h:raise ValueError('Original or frozen result changed '+p)
    prefixes={}
    for p in REGISTRY:
        old=pd.read_csv(StringIO(subprocess.check_output(['git','show','23d505f:'+p],cwd=ROOT).decode('utf-8-sig')),dtype=str,keep_default_na=False)
        actual=read(p)
        if not actual.iloc[:len(old)].reset_index(drop=True).equals(old):raise ValueError('Historical registry prefix changed '+p)
        prefixes[p]=dict(previous_rows_exact=len(old),previous_row_digest=digest(old),current_rows=len(actual),appended_rows=len(actual)-len(old))
    t=pd.read_csv(ROOT/'data_processed/terrain_reviewed_profiles_stage82.csv')
    s=pd.read_csv(ROOT/'data_processed/spass_reviewed_profiles_stage83.csv')
    route_path='data_processed/accessibility_road_group_reference_stage79.csv';city_path='data_processed/winter_profile_urban_city_detail_stage57.csv'
    route=pd.read_csv(ROOT/route_path);cities=pd.read_csv(ROOT/city_path)[['municipality_bfs_id','city_name']].drop_duplicates()
    if len(cities)!=6 or not cities.municipality_bfs_id.is_unique:raise ValueError('Six approved cities required')
    selected=route[route.municipality_bfs_id.isin(cities.municipality_bfs_id)]
    if selected.duplicated(['station_group_id','municipality_bfs_id']).any():raise ValueError('City route duplication')
    accessible=set(selected.loc[selected.road_reference_minutes.notna(),'station_group_id'])
    geom=set(t.loc[t[['unique_mapped_axis_length_m','length_weighted_observed_altitude_m','terrain_northness','terrain_eastness']].notna().all(axis=1),'station_group_id'])
    snow=set(s.loc[s.spass_five_preentry_winters_mean_m.notna(),'station_group_id'])
    readiness=dict(checked_at=datetime.now(timezone.utc).isoformat(),input_sha256={p:sha(p) for p in [
        'src/descriptive/check_reviewed_profiles_stage83.py','data_processed/terrain_reviewed_profiles_stage82.csv',
        'data_processed/spass_reviewed_profiles_stage83.csv',route_path,city_path]},
        all_groups_retained=len(t),approved_city_count=len(cities),group_city_rows=len(selected),
        all_six_road_times_available_groups=int(selected.groupby('station_group_id').road_reference_minutes.count().eq(6).sum()),
        proposed_without_snow_fields_available=len(geom&accessible),proposed_with_snow_fields_available=len(geom&accessible&snow),
        current_geometry_road_proxy_not_verified_preentry=True,hotel_capacity_not_arbitrarily_assigned=True,
        no_cluster_count_or_model_fitted=True,no_group_exclusion_or_new_did=True,
        prospective_coverage_only_not_validated_model_sample=True)
    rpath=ROOT/'reports/reviewed_profiles_readiness_stage83_summary.json'
    if rpath.exists():
        old=json.loads(rpath.read_text())
        if old['input_sha256']!=readiness['input_sha256']:raise ValueError('Frozen coverage audit differs')
    else:rpath.write_text(json.dumps(readiness,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    hashes[rpath.relative_to(ROOT).as_posix()]=sha(rpath.relative_to(ROOT))
    state=dict(checked_at=datetime.now(timezone.utc).isoformat(),baseline_commit='23d505f',historical_unique_files=len(parent['checks']),
        checked_unique_files=len(hashes),old_results_originals_and_caches_unchanged=True,all_original71_ids_and185_territories_retained=True,
        french_complement_still_cancelled=True,no_new_did_or_clustering=True,registry_prefixes_exact=prefixes,
        checks=[dict(path=p,sha256=h) for p,h in hashes.items()])
    (ROOT/'reports/preservation_stage83_summary.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in state.items() if k!='checks'},ensure_ascii=False));print(json.dumps(readiness,ensure_ascii=False))


if __name__=='__main__':main()
