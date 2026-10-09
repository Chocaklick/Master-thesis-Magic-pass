"""Keep original OSM versions; distinguish candidate axes/surfaces, not groups.

Object geometry diagnostics are not verified station characteristics. No
polygon repair, centerline construction, multipolygon stitching or assignment.
"""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS

CONFIG='config/winter_profile_geometry_roles_decisions_stage49.json'
TABLE='winter_profile_piste_geometry_roles'
OUTPUT='data_processed/'+TABLE+'.csv'
SUMMARY='reports/piste_geometry_roles_stage49_summary.json'
SOURCE='DERIVED_PISTE_GEOMETRY_ROLES_STAGE49'
SCRIPT='src/descriptive/audit_piste_geometry_roles.py'
TRANSFORM=Transformer.from_crs(4326,2056,always_xy=True)
DEFS={
    'source_id':('Registered derived diagnostic source','identifier'),
    'parent_source_id':('Original OSM snapshot source, retained separately','identifier'),
    'osm_snapshot':('Original OSM snapshot date, not construction date','timestamp'),
    'osm_type':('Original upstream object type','category'),
    'osm_id':('Original stable upstream identifier within object type','identifier'),
    'osm_version':('Original upstream version, never silently merged','integer'),
    'osm_edit_timestamp':('Original editing timestamp, not piste construction date','timestamp'),
    'original_name':('Original OSM name; not used as sole join key','name'),
    'original_area_tag':('Original area tag; missing means unspecified','category'),
    'original_relation_type':('Original relation type; not a station grouping','category'),
    'candidate_role':('Literal geometry/tag-based review role, not accepted group assignment','category'),
    'closed_way':('Upstream first and last node IDs coincide; unspecified if unavailable','boolean'),
    'coordinate_count':('Coordinates directly present in way geometry; not sampled terrain points','count'),
    'surface_boundary_relation_ids':('Same-snapshot multipolygon relations referencing this way; dual-role caution','identifiers'),
    'geometry_status':('Geometry diagnostic without automatic repair or dropped object','category'),
    'candidate_axis_length_m':('EPSG2056 length of valid candidate way axis, not station length; surface boundaries never measured as axes','metres'),
    'candidate_standalone_polygon_area_m2':('EPSG2056 area of a valid explicitly declared standalone surface way; not fused station area or real total area','square metres'),
    'group_assignment_verified':('False: object inventory does not assign any station group','boolean'),
    'historical_scope_verified':('False: current geometry not certified preentry','boolean')
}


def mapped_area(polygons):
    """Fuse ONLY verified projected surface geometries, preserving holes.

    No inputs means missing coverage, not a claim of zero real piste area.
    Caller must verify group membership/CRS; this audit does not call it on groups.
    """
    if not polygons:
        return None
    if any(p.geom_type not in ['Polygon','MultiPolygon'] or not p.is_valid or p.is_empty for p in polygons):
        raise ValueError('Require valid projected surfaces; never repair or use axis buffers')
    union=unary_union(polygons)
    return dict(mapped_piste_area_ha=union.area/10000,mapped_piste_area_km2=union.area/1000000)


def role(element):
    tags=element.get('tags',{})
    if element['type']=='relation':
        return 'surface_multipolygon_candidate' if tags.get('type')=='multipolygon' else 'route_wrapper_not_independent_axis' if tags.get('type')=='route' else 'relation_scope_unresolved'
    nodes=element.get('nodes',[])
    closed=bool(nodes and nodes[0]==nodes[-1])
    if tags.get('area')=='yes':
        return 'explicit_surface_way_candidate'
    if closed and tags.get('area')!='no':
        return 'closed_way_role_unresolved'
    return 'way_axis_candidate'


def geometry_diagnostic(element,candidate,boundaries):
    coordinates=element.get('geometry',[])
    if element['type']=='relation':
        return 'relation_geometry_requires_scope_and_topology_verification',None,None
    if len(coordinates)<2 or not all('lon' in p and 'lat' in p for p in coordinates):
        return 'missing_coordinates',None,None
    if not all(math.isfinite(p['lon']) and math.isfinite(p['lat']) and -180<=p['lon']<=180 and -90<=p['lat']<=90 for p in coordinates):
        return 'invalid_coordinates',None,None
    x,y=TRANSFORM.transform([p['lon'] for p in coordinates],[p['lat'] for p in coordinates])
    points=list(zip(x,y))
    if candidate=='closed_way_role_unresolved':
        return 'role_pending_no_measure',None,None
    if candidate=='explicit_surface_way_candidate':
        if len(points)<4 or points[0]!=points[-1]:
            return 'declared_surface_not_closed_no_repair',None,None
        polygon=Polygon(points)
        if not polygon.is_valid or polygon.is_empty:
            return 'invalid_polygon_no_repair',None,None
        if boundaries:
            return 'surface_member_topology_pending',None,None
        return 'valid_standalone_surface_candidate',None,polygon.area
    line=LineString(points)
    if not line.is_valid or line.is_empty:
        return 'invalid_line',None,None
    if boundaries:
        return 'surface_boundary_dual_role_pending',None,None
    return 'valid_axis_candidate',line.length,None


def build_rows(payload,parent):
    elements=payload['elements']
    keys=[(e['type'],e['id']) for e in elements]
    if len(keys)!=len(set(keys)):
        raise ValueError('Duplicate original upstream keys within source')
    boundaries={}
    for e in elements:
        if e.get('tags',{}).get('type')=='multipolygon' and e.get('tags',{}).get('piste:type')=='downhill':
            for m in e.get('members',[]):
                if m['type']=='way':
                    boundaries.setdefault(m['ref'],set()).add(e['id'])
    rows=[]
    for e in elements:
        if e.get('tags',{}).get('piste:type')!='downhill':
            continue
        candidate=role(e); member_of=boundaries.get(e['id'],set()) if e['type']=='way' else set()
        status,length,area=geometry_diagnostic(e,candidate,member_of)
        nodes=e.get('nodes',[])
        rows.append(dict(source_id=SOURCE,parent_source_id=parent,osm_snapshot=payload['osm3s']['timestamp_osm_base'],
            osm_type=e['type'],osm_id=e['id'],osm_version=e['version'],osm_edit_timestamp=e['timestamp'],
            original_name=e.get('tags',{}).get('name',''),original_area_tag=e.get('tags',{}).get('area',''),
            original_relation_type=e.get('tags',{}).get('type',''),candidate_role=candidate,
            closed_way=(nodes[0]==nodes[-1]) if nodes else None,coordinate_count=len(e.get('geometry',[])),
            surface_boundary_relation_ids='|'.join(map(str,sorted(member_of))),geometry_status=status,
            candidate_axis_length_m=length,candidate_standalone_polygon_area_m2=area,
            group_assignment_verified=False,historical_scope_verified=False))
    return rows


def register(frame):
    path=ROOT/'metadata/data_sources_master.csv'
    master=pd.read_csv(path,dtype=str,keep_default_na=False)
    record=dict(source_id=SOURCE,variable_name='piste_geometry_role_diagnostics',
        variable_description='Separate literal OSM candidate axes and surfaces; no station characteristics or accepted group membership',
        source_organisation='Thesis audit of OpenStreetMap contributors',source_page_url='https://wiki.openstreetmap.org/wiki/Tag:piste:type=downhill',
        retrieval_date='2026-10-09',retrieval_method='Cached original snapshots/SHA; original keys and versions retained; EPSG2056 object geometry diagnostics',
        processed_file=OUTPUT,geographic_level='Original selected OSM objects, including border features; not station groups',
        temporal_resolution='Current snapshots, not preentry certified',license='Parent OSM ODbL',
        transformation_applied='Separate line/area diagnostics; no surface-to-line conversion, buffer, repair or group assignment',
        quality_notes='Closed unspecified roles, invalid shapes and multipolygon topology remain flagged; areas are not full real piste area',
        notes='Parent sources OSM_DOWNHILL_SWISS_CURRENT_2026_10_09|OSM_PISTE_REFERENCED_MEMBER_TAGS_2026_10_09; source/checkpoint hashes in summary')
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)],pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),path)
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False)
    fields=[dict(variable=column,table=TABLE,description=description,unit=unit,data_type=str(frame[column].dtype),
        geographic_level='original OSM object by snapshot',temporal_level='current source snapshot',source_id=SOURCE,
        raw_or_derived='retained source attribute or object diagnostic',formula='See role/geometry_diagnostic; no station profile aggregation',
        causal_role='geometry availability/quality audit only',missing_share=f'{frame[column].isna().mean():.6f}',
        notes='All original versions retained; no missing-to-zero or group exclusion') for column,(description,unit) in DEFS.items()]
    write_csv(pd.concat([dictionary[dictionary.table.ne(TABLE)],pd.DataFrame(fields).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--no-register',action='store_true'); args=parser.parse_args()
    decision=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    if not decision['both_axes_and_surfaces_retained'] or decision['line_and_surface_weights_may_be_mixed'] or decision['artificial_centerline_from_polygon_allowed']:
        raise ValueError('Require approved disjoint geometry roles')
    inputs={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [CONFIG,SCRIPT,'data_processed/accessibility_station_groups.csv']}
    rows=[]
    for file in ['data_interim/current_piste_geometry_collection_checkpoint.json','reports/piste_missing_member_collection_summary.json']:
        meta=json.loads((ROOT/file).read_text(encoding='utf-8'))
        if meta['status']!='complete':
            raise ValueError('Require original complete geometry snapshots')
        inputs[file]=hashlib.sha256((ROOT/file).read_bytes()).hexdigest()
        raw=ROOT/meta['raw_file']; observed=hashlib.sha256(raw.read_bytes()).hexdigest()
        if observed!=meta['sha256']:
            raise ValueError('Original snapshot hash changed')
        inputs[meta['raw_file']]=observed
        rows.extend(build_rows(json.loads(raw.read_bytes()),meta['source_id']))
    frame=pd.DataFrame(rows)
    if frame.duplicated(['parent_source_id','osm_type','osm_id','osm_version']).any():
        raise ValueError('Duplicate snapshot-object key')
    groups=pd.read_csv(ROOT/'data_processed/accessibility_station_groups.csv')
    if len(groups)!=71 or not groups.station_group_id.is_unique:
        raise ValueError('Retain the existing group universe')
    output=ROOT/OUTPUT; summary=ROOT/SUMMARY
    state=dict(date='2026-10-09',input_sha256=inputs,group_count=71,object_snapshot_rows=len(frame),
        unique_upstream_object_count=len(frame[['osm_type','osm_id']].drop_duplicates()),
        candidate_role_counts=dict(Counter(frame.candidate_role)),geometry_status_counts=dict(Counter(frame.geometry_status)),
        metrics_are_object_diagnostics_not_group_profiles=True,group_assignments_accepted=0,
        group_profiles_computed=False,group_surface_union_computed=False,automatic_exclusion_applied=False,
        historical_scope_certified=False,notes='Surface-only objects retained; no invented axes. Original source versions not reconciled silently. Relations/topology and unknown closed roles require review.')
    if summary.exists():
        previous=json.loads(summary.read_text(encoding='utf-8'))
        if previous['input_sha256']!=inputs or hashlib.sha256(output.read_bytes()).hexdigest()!=previous['output_sha256']:
            raise ValueError('Changed own checkpoint; preserve and review')
    else:
        write_csv(frame,output)
        state['output_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
        summary.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if not args.no_register:
        register(frame)
    print('Separate object geometry-role audit:',len(frame),'rows; no station features or exclusions.')


if __name__=='__main__':
    main()
