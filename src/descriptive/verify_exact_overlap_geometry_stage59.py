"""Separate exact shared geometry from floating length subtraction residuals.

Stage58 is preserved, including its raw differences. Positive subtraction alone
does not prove overlap. Pair intersections test positive shared LINE length, not
nearby geometry or a numerical distance tolerance. Point crossings are ignored.
"""
import json
import sys
from itertools import combinations
from pathlib import Path
import pandas as pd
from shapely.geometry import LineString
from shapely.ops import unary_union
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.audit_piste_geometry_roles import TRANSFORM
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

SOURCE='DERIVED_EXACT_OVERLAP_GEOMETRY_STAGE59'
TABLE='winter_profile_overlap_geometry_stage59'
OUTPUT=f'data_processed/{TABLE}.csv'
SUMMARY='reports/exact_overlap_geometry_stage59_summary.json'


def shared_geometry(lines):
    if not lines:return None
    intersections=[a.intersection(b) for a,b in combinations(lines,2) if a.intersects(b)]
    positive=[g for g in intersections if g.length>0]
    return dict(exact_overlap_pair_count=len(positive),exact_shared_portion_m=unary_union(positive).length if positive else 0.0)


DEFS={
    'source_id':('Registered derived verification source','identifier'),
    'station_group_id':('Retained current derived group ID','identifier'),
    'exact_overlap_pair_count':('Pairs sharing exact positive line length; point crossings excluded; missing without mapped axes','count'),
    'exact_shared_portion_m':('Union length of portions shared by at least two axes; multiplicity counted once, distinct from excess ID weight','metres'),
    'has_exact_shared_line_geometry':('Positive exact shared line geometry, never inferred from rounded length difference','boolean'),
    'raw_id_sum_minus_union_m':('Unchanged Stage58 subtraction; tiny floating residuals retained','metres'),
    'subtraction_residual_without_shared_geometry_m':('Raw difference when pair intersections prove no shared line; not genuine repeated piste length','metres'),
    'group_retained':('All derived groups retained, missing source coverage not zero','boolean')}


def main():
    parent=json.loads((ROOT/'reports/exact_piste_overlap_stage58_summary.json').read_text(encoding='utf-8'))
    for p,h in {**parent['input_sha256'],**parent['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Frozen parent changed: '+p)
    paths=['src/descriptive/verify_exact_overlap_geometry_stage59.py','reports/exact_piste_overlap_stage58_summary.json',
           'data_processed/winter_profile_exact_piste_overlap_stage58.csv','data_interim/winter_profile_exact_network_stage58.json']
    inputs={p:sha(p) for p in paths}
    index,_,_=originals()
    groups=pd.read_csv(ROOT/paths[2])
    net=json.loads((ROOT/paths[3]).read_text(encoding='utf-8'))
    rows=[]
    for g in net:
        lines=[]
        for r in g['retained_original_members']:
            if r['candidate_role']!='way_axis_candidate':continue
            e=index[(r['osm_type'],r['osm_id'])]
            if e['version']!=r['osm_version']:raise ValueError('Original version changed')
            x,y=TRANSFORM.transform([p['lon'] for p in e['geometry']],[p['lat'] for p in e['geometry']])
            lines.append(LineString(zip(x,y)))
        metric=shared_geometry(lines)
        difference=groups.loc[groups.station_group_id.eq(g['station_group_id']),'repeated_overlap_weight_m'].iloc[0]
        rows.append(dict(source_id=SOURCE,station_group_id=g['station_group_id'],
            exact_overlap_pair_count=metric['exact_overlap_pair_count'] if metric else None,
            exact_shared_portion_m=metric['exact_shared_portion_m'] if metric else None,
            has_exact_shared_line_geometry=metric['exact_shared_portion_m']>0 if metric else None,
            raw_id_sum_minus_union_m=difference,
            subtraction_residual_without_shared_geometry_m=difference if metric and metric['exact_shared_portion_m']==0 else None,
            group_retained=True))
    frame=pd.DataFrame(rows)
    actual=frame[frame.has_exact_shared_line_geometry.eq(True)]
    state=dict(date='2026-10-10',input_sha256=inputs,group_count=len(frame),
        groups_with_exact_shared_line_count=len(actual),groups_with_exact_shared_line=actual.station_group_id.tolist(),
        shared_physical_portion_total_m=float(actual.exact_shared_portion_m.sum()),
        excess_identifier_weight_total_m=float(actual.raw_id_sum_minus_union_m.sum()),
        maximum_absolute_nonoverlap_subtraction_residual_m=float(frame.subtraction_residual_without_shared_geometry_m.abs().max()),
        no_geometric_tolerance_or_exclusion=True,stage58_original_subtractions_preserved=True,
        note='Stage58 positive raw subtraction list includes floating residuals; only direct positive pair line intersection proves geometric overlap.')
    target=ROOT/SUMMARY
    if target.exists():
        old=json.loads(target.read_text(encoding='utf-8'))
        if old['input_sha256']!=inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):raise ValueError('Frozen verification changed')
    else:
        write_csv(frame,ROOT/OUTPUT)
        state['output_sha256']={OUTPUT:sha(OUTPUT)}
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    if SOURCE not in set(master.source_id):
        record=dict(source_id=SOURCE,variable_name='exact_shared_line_geometry_verification',variable_description='Direct intersections distinguish exact shared portions from floating subtraction residuals',source_organisation='Thesis deterministic OSM geometry audit',retrieval_date='2026-10-10',retrieval_method='Offline exact pair intersections; no queries/tolerance/snap',processed_file=OUTPUT,geographic_level='70 retained derived station groups',temporal_resolution='Current source geometry, not preentry certified',license='Parent OSM ODbL',transformation_applied='Positive line intersections then union of shared portions; point crossings not overlaps; raw differences preserved',quality_notes='Diagnostic only, no final profiles or individual lifecycle acceptance',notes='Parent DERIVED_EXACT_PISTE_OVERLAP_STAGE58; SHA lineage in '+SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    records=[]
    for col,(description,unit) in DEFS.items():
        if ((dictionary.table==TABLE)&(dictionary.variable==col)).any():continue
        records.append(dict(variable=col,table=TABLE,description=description,unit=unit,data_type=str(frame[col].dtype),source_id=SOURCE,geographic_level='retained derived group',temporal_level='current original geometry',raw_or_derived='exact geometry verification',formula='Pair intersection positive length; union shared pieces; preserve Stage58 subtraction',causal_role='quality diagnostic, not final causal feature',missing_share=f'{frame[col].isna().mean():.6f}',notes='No proximity tolerance or group/member exclusion'))
    if records:write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if not k.endswith('sha256')},ensure_ascii=False))


if __name__=='__main__':main()
