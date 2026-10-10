"""Approved exact overlap diagnostic; original objects and old outputs retained.

Union valid candidate axes within each derived group in the existing EPSG2056
coordinate system, with no precision grid, tolerance, repair, buffer or snapping.
This is mapped candidate coverage, not an exhaustive or preentry resort feature.
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd
import shapely
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.audit_piste_geometry_roles import TRANSFORM, mapped_area
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_EXACT_PISTE_OVERLAP_STAGE58'
CONFIG = 'config/piste_exact_overlap_decisions_stage58.json'
TABLE = 'winter_profile_exact_piste_overlap_stage58'
OUTPUT = f'data_processed/{TABLE}.csv'
NETWORK = 'data_interim/winter_profile_exact_network_stage58.json'
SUMMARY = 'reports/exact_piste_overlap_stage58_summary.json'
MEMBERS = 'data_processed/winter_profile_verified_piste_member_qa_stage56.csv'
GROUPS = 'data_processed/winter_profile_verified_piste_group_qa_stage56.csv'


def exact_network(lines):
    """No inputs means absent mapped coverage, never zero real piste length."""
    if not lines:
        return None
    if any(x.geom_type != 'LineString' or not x.is_valid or x.is_empty for x in lines):
        raise ValueError('Require valid axes; no repair or implicit exclusion')
    network = unary_union(lines)
    total = math.fsum(x.length for x in lines)
    if network.length > total + 1e-8:
        raise ValueError('Union length cannot exceed original length sum')
    return dict(distinct_id_sum_m=total, exact_unique_network_m=network.length,
                overlap_repeated_weight_m=total-network.length, geometry=network)


DEFS = {
    'source_id': ('Registered derived diagnostic source', 'identifier'),
    'station_group_id': ('Derived group ID; neither municipality nor lift cluster', 'identifier'),
    'station_group_name': ('Retained group name; not a sole join key', 'name'),
    'parent_station_group_ids': ('Preserved original group identities', 'identifiers'),
    'current_site_correspondence_verified': ('Existing current site correspondence; not exhaustive coverage', 'boolean'),
    'retained_member_count': ('Retained original site member objects; missing for unresolved sites', 'count'),
    'candidate_axis_count': ('Axis candidate objects, not named piste count', 'count'),
    'distinct_id_axis_length_sum_m': ('Sum of current candidate-axis lengths once per original ID', 'metres'),
    'exact_unique_mapped_axis_length_m': ('Length of candidate geometric union within group, no tolerance or snapping', 'metres'),
    'repeated_overlap_weight_m': ('ID length sum minus unique geometric length; not separately surveyed track length', 'metres'),
    'repeated_overlap_weight_share': ('Repeated overlap weight divided by ID length sum', 'proportion'),
    'explicit_surface_count': ('Separate explicit standalone surface candidates, not axes', 'count'),
    'mapped_surface_union_area_ha': ('Union of current mapped explicit valid surfaces only; not exhaustive piste area', 'hectares'),
    'literal_lifecycle_flag_member_count': ('Literal lifecycle/status tags retained for review, not an automatic exclusion', 'count'),
    'individual_metric_use_verified': ('False: geometric validity does not close individual lifecycle/scope review', 'boolean'),
    'historical_scope_verified': ('False: no preentry geometry certification', 'boolean'),
    'group_retained': ('True: every derived group remains in the output', 'boolean'),
    'metric_status': ('Mapped candidate coverage or missing source coverage; no real-zero inference', 'category'),
    'parent_source_ids': ('Existing derived member and group lineage', 'identifiers')
}


def build(groups, members, lineage, index):
    if len(groups) != 70 or not groups.station_group_id.is_unique:
        raise ValueError('Preserve all 70 derived groups')
    if members.duplicated(['station_group_id', 'osm_type', 'osm_id', 'osm_version']).any():
        raise ValueError('Original member keys must remain unique within group')
    rows, networks = [], []
    seen = set()
    for g in groups.itertuples():
        part = members[members.station_group_id.eq(g.station_group_id)]
        verified = g.current_site_correspondence_verified == 'True'
        lines, polygons, retained = [], [], []
        if not verified and not part.empty:
            raise ValueError('Do not infer unresolved site membership')
        for r in part.itertuples():
            element = index[(r.osm_type, int(r.osm_id))]
            if element['version'] != int(r.osm_version):
                raise ValueError('Original version changed')
            geom = element.get('geometry', [])
            x, y = TRANSFORM.transform([p['lon'] for p in geom], [p['lat'] for p in geom])
            points = list(zip(x, y))
            if r.candidate_role == 'way_axis_candidate' and r.geometry_status == 'valid_axis_candidate':
                line = LineString(points)
                if not math.isclose(line.length, float(r.candidate_axis_length_m), rel_tol=1e-12, abs_tol=1e-8):
                    raise ValueError('Original axis diagnostic differs')
                lines.append(line)
            elif r.candidate_role == 'explicit_surface_way_candidate' and r.geometry_status == 'valid_standalone_surface_candidate':
                polygon = Polygon(points)
                if not math.isclose(polygon.area, float(r.candidate_standalone_polygon_area_m2), rel_tol=1e-12, abs_tol=1e-8):
                    raise ValueError('Original surface diagnostic differs')
                polygons.append(polygon)
            else:
                raise ValueError('Unresolved member geometry requires review, not silent exclusion')
            key = (r.station_group_id, r.osm_type, r.osm_id, r.osm_version)
            seen.add(key)
            retained.append(dict(parent_source_id=r.parent_source_id, osm_type=r.osm_type,
                                 osm_id=int(r.osm_id), osm_version=int(r.osm_version),
                                 candidate_role=r.candidate_role, diagnostic_flags=r.diagnostic_flags,
                                 original_lifecycle_tags=json.loads(r.original_lifecycle_tags)))
        metric = exact_network(lines)
        area = mapped_area(polygons)
        rows.append(dict(source_id=SOURCE, station_group_id=g.station_group_id,
            station_group_name=g.station_group_name, parent_station_group_ids=lineage[g.station_group_id],
            current_site_correspondence_verified=verified,
            retained_member_count=len(part) if verified else None,
            candidate_axis_count=len(lines) if verified else None,
            distinct_id_axis_length_sum_m=metric['distinct_id_sum_m'] if metric else None,
            exact_unique_mapped_axis_length_m=metric['exact_unique_network_m'] if metric else None,
            repeated_overlap_weight_m=metric['overlap_repeated_weight_m'] if metric else None,
            repeated_overlap_weight_share=metric['overlap_repeated_weight_m']/metric['distinct_id_sum_m'] if metric and metric['distinct_id_sum_m'] else None,
            explicit_surface_count=len(polygons) if verified else None,
            mapped_surface_union_area_ha=area['mapped_piste_area_ha'] if area else None,
            literal_lifecycle_flag_member_count=int(part.original_lifecycle_tags.ne('{}').sum()) if verified else None,
            individual_metric_use_verified=False, historical_scope_verified=False, group_retained=True,
            metric_status='mapped_candidate_network_only' if metric else 'verified_site_missing_mapped_axes' if verified else 'site_correspondence_unresolved',
            parent_source_ids='DERIVED_VERIFIED_PISTE_MEMBER_QA_STAGE56|DERIVED_CONNECTED_GROUP_OVERLAY_STAGE55'))
        networks.append(dict(station_group_id=g.station_group_id, crs='EPSG:2056',
            exact_unique_axis_wkt=metric['geometry'].wkt if metric else None,
            retained_original_members=retained, individual_metric_use_verified=False))
    if len(seen) != len(members):
        raise ValueError('Every original member must remain represented')
    return pd.DataFrame(rows), networks


def register(frame):
    master = pd.read_csv(ROOT/'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    if SOURCE not in set(master.source_id):
        row = dict(source_id=SOURCE, variable_name='exact_overlap_mapped_candidate_piste_network',
            variable_description='Approved exact unique geometric network compared with original-ID length sum; surfaces separate',
            source_organisation='Thesis deterministic audit of OSM contributors', retrieval_date='2026-10-10',
            retrieval_method='Offline preserved original snapshots and Stage56 keys/versions; no requests',
            processed_file=OUTPUT+'|'+NETWORK, geographic_level='70 derived station groups; not municipality outcomes',
            temporal_resolution='Current mapped geometry, not preentry certified', license='Parent OSM ODbL',
            transformation_applied='EPSG2056 unary union, no grid size/snap/tolerance/repair; ID sum retained; separate surface union',
            quality_notes='No exhaustive domain, lifecycle acceptance, final features or exclusions; missing coverage not zero',
            notes='Approval and SHA lineage in '+SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([row]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT/'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    if set(frame) != set(DEFS):
        raise ValueError('Every analytical field must be defined')
    rows = []
    for col, (description, unit) in DEFS.items():
        if ((dictionary.table == TABLE) & (dictionary.variable == col)).any():
            continue
        rows.append(dict(variable=col, table=TABLE, description=description, unit=unit,
            data_type=str(frame[col].dtype), source_id=SOURCE, geographic_level='retained derived group',
            temporal_level='current original geometry', raw_or_derived='derived mapped candidate diagnostic',
            formula='audit_exact_piste_overlap_stage58.py; geometric union within group, ID sum retained',
            causal_role='quality/coverage diagnostic; not final preentry clustering feature',
            missing_share=f'{frame[col].isna().mean():.6f}', notes='No tolerance, lifecycle exclusion, real-zero inference or preentry certification'))
    if rows:
        write_csv(pd.concat([dictionary,pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    decision = json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    if not decision['within_group_exact_overlap_counted_once'] or decision['proximity_tolerance_or_coordinate_snapping_allowed']:
        raise ValueError('Require exact overlap approval, no proximity rule')
    paths = [CONFIG, 'src/descriptive/audit_exact_piste_overlap_stage58.py', MEMBERS, GROUPS,
        'data_processed/accessibility_station_groups_stage55.csv', 'src/descriptive/audit_piste_geometry_roles.py',
        'src/descriptive/review_piste_candidates_stage53.py', 'src/descriptive/audit_completed_piste_membership.py',
        'data_interim/current_piste_geometry_collection_checkpoint.json', 'reports/piste_missing_member_collection_summary.json',
        'reports/verified_piste_member_qa_stage56_summary.json']
    parent = json.loads((ROOT/paths[-1]).read_text(encoding='utf-8'))
    for p, h in {**parent['input_sha256'], **parent['output_sha256']}.items():
        if sha(p) != h:
            raise ValueError('Prior frozen checkpoint changed: '+p)
    inputs = {p:sha(p) for p in paths}
    for checkpoint in paths[8:10]:
        original = json.loads((ROOT/checkpoint).read_text(encoding='utf-8'))
        inputs[original['raw_file']] = sha(original['raw_file'])
    index, _, _ = originals()
    groups = pd.read_csv(ROOT/GROUPS,dtype=str,keep_default_na=False)
    members = pd.read_csv(ROOT/MEMBERS,dtype=str,keep_default_na=False)
    lineage = pd.read_csv(ROOT/paths[4],dtype=str,keep_default_na=False).set_index('station_group_id').parent_station_group_ids.to_dict()
    frame, networks = build(groups,members,lineage,index)
    affected = frame[frame.repeated_overlap_weight_m.gt(0)]
    state = dict(date='2026-10-10',input_sha256=inputs,shapely_version=shapely.__version__,geos_version=shapely.geos_version_string,
        group_count=len(frame),original_member_count=len(members),candidate_axis_count=int(frame.candidate_axis_count.sum()),
        explicit_surface_count=int(frame.explicit_surface_count.sum()),groups_with_mapped_axes=int(frame.exact_unique_mapped_axis_length_m.notna().sum()),
        verified_sites_without_mapped_axes=frame.loc[frame.metric_status.eq('verified_site_missing_mapped_axes'),'station_group_id'].tolist(),
        unresolved_group_count=int(frame.metric_status.eq('site_correspondence_unresolved').sum()),
        groups_with_repeated_overlap=affected[['station_group_id','repeated_overlap_weight_m']].to_dict('records'),
        repeated_weight_total_m=float(frame.repeated_overlap_weight_m.sum()),
        all_original_members_and_groups_retained=True,old_outputs_preserved=True,
        historical_geometry_certified=False,individual_metric_acceptance=False,profile_fit_or_effect_estimation=False,
        no_tolerance_snap_repair_or_exclusion=True)
    target = ROOT/SUMMARY
    if target.exists():
        old = json.loads(target.read_text(encoding='utf-8'))
        if old['input_sha256'] != inputs or any(sha(p)!=h for p,h in old['output_sha256'].items()):
            raise ValueError('Frozen own checkpoint changed; use a new stage')
    else:
        write_csv(frame,ROOT/OUTPUT)
        (ROOT/NETWORK).write_text(json.dumps(networks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        state['output_sha256']={p:sha(p) for p in [OUTPUT,NETWORK]}
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    register(frame)
    print(json.dumps({k:v for k,v in state.items() if not k.endswith('sha256')},ensure_ascii=False))


if __name__ == '__main__':
    main()
