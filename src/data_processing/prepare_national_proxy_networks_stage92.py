"""Six provisional current proxies, exact native lengths; old69groups untouched."""
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from netCDF4 import Dataset
from pyproj import Transformer
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from src.descriptive.audit_completed_piste_membership import audit
from src.descriptive.audit_piste_geometry_roles import role
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link
from src.descriptive.check_national_preparation_stage87 import sha
from src.data_processing.prepare_native_snow_weights_stage69 import native_grid
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths
from src.data_processing.atomic_csv_output import write_csv
from src.data_collection.collect_braunwald_urban_road_stage90 import register

SOURCE = 'DERIVED_NATIONAL_CURRENT_PROXY_SUPPORT_STAGE92'
OUTPUTS = {t: 'data_processed/' + t + '.csv' for t in [
    'national_proxy_networks_stage92', 'national_proxy_object_review_stage92', 'national_proxy_spass_weights_stage92']}
NETWORK = 'data_interim/national_proxy_networks_stage92.json'
SUMMARY = 'reports/national_proxy_support_stage92_summary.json'
DEFS = {
    'source_id': ('Registered current provisional proxy support provenance', 'identifier'),
    'station_group_id': ('Engine-compatible key equal to provisional preparation_unit_id, not a new accepted independent domain', 'identifier'),
    'station_group_name': ('Original candidate label, not a matching key', 'text'),
    'preparation_unit_id': ('Preserved national provisional listing key, original resort_id kept separately', 'identifier'),
    'resort_id': ('Original stable catalogue listing ID, not a fabricated source identity', 'identifier'),
    'osm_site_relation_id': ('Individually reviewed cached relation, not radius/name matching', 'identifier'),
    'mapped_axis_objects': ('Unique original objects with axis role, not official piste count', 'count'),
    'measured_axis_objects': ('Reviewed original axis objects usable in this provisional proxy', 'count'),
    'unmeasured_axis_objects': ('Ambiguous original axis objects retained but not measured', 'count'),
    'explicit_surface_objects': ('Original declared surface objects kept apart from linear axes', 'count'),
    'full_unique_candidate_axis_length_m': ('Exact union length of all source candidate axes; mapped proxy coverage reference only', 'metres'),
    'measured_unique_proxy_axis_length_m': ('Exact union of usable original axes, counting exactly coincident portions once; no snapping/tolerance', 'metres'),
    'mapped_axis_length_sum_by_id_m': ('Sum of original axis lengths by unique OSM ID kept for comparison, may double count coincident portions', 'metres'),
    'measured_share_of_mapped_candidate_length': ('Usable exact union length divided by full mapped candidate union, not real domain coverage', 'fraction'),
    'mapped_surface_union_area_ha': ('Separate exact union of declared source polygons; no axes invented from surfaces and no total real area claim', 'hectares'),
    'independent_domain_assignment_accepted': ('Always false in provisional support; identity/connection/period acceptance for final national sample remains separate', 'boolean'),
    'common_decade_ski_activity_verified': ('Primary actual skiing proof available for at least one approved common winter, not inferred from present skiing or a lift construction date', 'boolean'),
    'grooming_scope_validation_applied': ('Approved keep corroborated descents, grooming literal descriptive only, no present-to-past inference', 'boolean'),
    'automatic_exclusion': ('Always false, unresolved or missing features do not exclude candidates/groups', 'boolean'),
    'osm_way_id': ('Exact original unique OSM member ID', 'identifier'),
    'candidate_role': ('Original axis/surface role under unchanged prior conventions', 'category'),
    'geometry_review_status': ('Literal geometry validity/individual ambiguity, not a grooming-based filter', 'category'),
    'measured_in_proxy': ('Eligible original geometry used in exact axis/surface union, not a fitted clustering acceptance', 'boolean'),
    'grooming_literal': ('Original tag or missing; absence not ungroomed and present tag not historical', 'text'),
    'measured_source_axis_length_m': ('Original planar EPSG2056 axis length when measured, surfaces/unresolved remain missing', 'metres'),
    'spass_e_index': ('Original east coordinate array index, no snow interpolation', 'index'),
    'spass_n_index': ('Original ascending north coordinate array index', 'index'),
    'spass_cell_in_grid': ('Coordinate indices in array bounds, not proof of finite snow value', 'boolean'),
    'spass_cell_centre_east_2056': ('Original source cell east-coordinate when in grid', 'metres'),
    'spass_cell_centre_north_2056': ('Original source cell north-coordinate when in grid', 'metres'),
    'unique_proxy_axis_length_m': ('Exact usable unique axis length intersecting the native SPASS cell, no artificial raster resampling', 'metres'),
}


def main():
    paths = ['src/data_processing/prepare_national_proxy_networks_stage92.py', 'config/national_grooming_scope_decision_stage92.json',
             'config/national_piste_review_cases_stage91.json', 'reports/national_piste_documentary_review_stage91_summary.json',
             'data_processed/national_preparation_work_queue_stage91.csv', 'reports/snow_grid_metadata_compatibility_stage47.json']
    inputs = {p: sha(p) for p in paths}
    decision = json.loads((ROOT / paths[1]).read_text(encoding='utf-8'))
    if decision['status'] != 'researcher_validated' or decision['grooming_use'] != 'literal_descriptive_context_only_not_automatic_model_input_or_metric_exclusion':
        raise ValueError('New explicit researcher approval required')
    cases = json.loads((ROOT / paths[2]).read_text(encoding='utf-8'))
    queue = pd.read_csv(ROOT / paths[4], dtype=str, keep_default_na=False).set_index('resort_id')
    payloads = []
    for path in ['data_interim/current_piste_geometry_collection_checkpoint.json', 'reports/piste_missing_member_collection_summary.json']:
        m = json.loads((ROOT / path).read_text(encoding='utf-8')); inputs[path] = sha(path)
        if sha(m['raw_file']) != m['sha256']:
            raise ValueError('Original geometry changed')
        inputs[m['raw_file']] = m['sha256']; payloads.append(json.loads((ROOT / m['raw_file']).read_text(encoding='utf-8')))
    _, sites = audit(*payloads); sites = {s['osm_relation_id']: s for s in sites}
    index = {(e['type'], e['id']): e for p in payloads for e in p['elements']}
    sp = json.loads((ROOT / paths[5]).read_text(encoding='utf-8'))
    if sha(sp['spass_raw_file']) != sp['spass_netcdf_sha256']:
        raise ValueError('Original SPASS changed')
    inputs[sp['spass_raw_file']] = sp['spass_netcdf_sha256']
    with ascii_link(ROOT / sp['spass_raw_file']) as link, Dataset(link) as d:
        east = np.asarray(d.variables['E'][:], dtype=float); north = np.asarray(d.variables['N'][:], dtype=float)
    grid = native_grid(east, north)
    transform = Transformer.from_crs(4326, 2056, always_xy=True)
    rows = []; objects = []; networks = []; weights = []
    for c in cases:
        rid = c['resort_id']; q = queue.loc[rid]; uid = q.preparation_unit_id
        if q.current_geographic_review_status != 'individually_reviewed_current_identity_coherent_full_coverage_uncertified':
            raise ValueError('Individual source review missing, never automatic proximity')
        all_lines = []; lines = []; surfaces = []
        part = []
        for wid in sites[c['osm_site_relation_id']]['selected_downhill_way_ids']:
            e = index[('way', wid)]; tags = e.get('tags', {}); kind = role(e); geometry = e.get('geometry', [])
            state = 'missing_or_ambiguous_geometry_retained'; measured = False; length = None
            points = []
            if len(geometry) >= 2 and all('lon' in p and 'lat' in p for p in geometry):
                x, y = transform.transform([p['lon'] for p in geometry], [p['lat'] for p in geometry]); points = list(zip(x, y))
                ambiguous = tags.get('abandoned') == 'yes' or tags.get('disused') == 'yes' or any('fixme' in k for k in tags)
                if kind == 'way_axis_candidate':
                    line = LineString(points); all_lines.append(line)
                    if line.is_valid and line.is_simple and not line.is_empty and not ambiguous:
                        state = 'valid_original_axis_no_individual_ambiguity'; measured = True; length = line.length; lines.append(line)
                elif kind == 'explicit_surface_way_candidate' and len(points) >= 4 and points[0] == points[-1]:
                    poly = Polygon(points)
                    if poly.is_valid and not poly.is_empty and not ambiguous:
                        state = 'valid_original_surface_kept_separate'; measured = True; surfaces.append(poly)
            part.append(dict(source_id=SOURCE, preparation_unit_id=uid, resort_id=rid, osm_way_id=wid, candidate_role=kind,
                geometry_review_status=state, measured_in_proxy=measured, grooming_literal=tags.get('piste:grooming', ''),
                measured_source_axis_length_m=length, automatic_exclusion=False))
        full = unary_union(all_lines) if all_lines else None
        useful = unary_union(lines) if lines else None
        area = unary_union(surfaces) if surfaces else None
        row = dict(source_id=SOURCE, station_group_id=uid, station_group_name=q.unit_name, preparation_unit_id=uid, resort_id=rid,
            osm_site_relation_id=c['osm_site_relation_id'], mapped_axis_objects=len(all_lines), measured_axis_objects=len(lines),
            unmeasured_axis_objects=len(all_lines)-len(lines), explicit_surface_objects=sum(p['candidate_role']=='explicit_surface_way_candidate' for p in part),
            full_unique_candidate_axis_length_m=full.length if full is not None else None,
            measured_unique_proxy_axis_length_m=useful.length if useful is not None else None,
            mapped_axis_length_sum_by_id_m=math.fsum(line.length for line in all_lines) if all_lines else None,
            measured_share_of_mapped_candidate_length=useful.length/full.length if useful is not None and full is not None and full.length else None,
            mapped_surface_union_area_ha=area.area/10000 if area is not None else None, independent_domain_assignment_accepted=False,
            common_decade_ski_activity_verified=bool(q.verified_common_decade_winter), grooming_scope_validation_applied=True, automatic_exclusion=False)
        rows.append(row); objects.extend(part)
        networks.append(row | dict(measured_unique_proxy_axis_wkt=useful.wkt if useful is not None else None,
                                   full_unique_candidate_axis_wkt=full.wkt if full is not None else None,
                                   separate_mapped_surface_union_wkt=area.wkt if area is not None else None))
        if useful is not None:
            for (r, col), length in sorted(cell_lengths(useful, grid['left'], grid['top'], grid['step'], grid['step']).items()):
                n = grid['north_count'] - 1 - r if grid['north_ascending'] else r
                inside = 0 <= col < len(east) and 0 <= n < len(north)
                weights.append(dict(source_id=SOURCE, station_group_id=uid, spass_e_index=col, spass_n_index=n,
                    spass_cell_in_grid=inside, spass_cell_centre_east_2056=float(east[col]) if inside else None,
                    spass_cell_centre_north_2056=float(north[n]) if inside else None, unique_proxy_axis_length_m=length))
    frames = dict(zip(OUTPUTS, [pd.DataFrame(rows), pd.DataFrame(objects), pd.DataFrame(weights)]))
    target = ROOT / SUMMARY
    if target.exists():
        prior = json.loads(target.read_text(encoding='utf-8'))
        if prior['input_sha256'] != inputs or any(sha(p) != h for p, h in prior['output_sha256'].items()):
            raise ValueError('Provisional support frozen, use new version')
        print('Exact provisional support and original cells reused, no recomputation')
        return
    for table, frame in frames.items():
        write_csv(frame, ROOT / OUTPUTS[table])
    (ROOT / NETWORK).write_text(json.dumps(networks, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    register(SOURCE, dict(variable_name='six_national_provisional_exact_proxy_networks_and_spass_weights',
        variable_description='Six individually reviewed current candidate site proxies; approved corroborated descents with grooming descriptive only; exact unique union and native SPASS length weights',
        source_organisation='Thesis from original OSM and SLF SPASS, with manual primary-source dossiers', retrieval_date=datetime.now(timezone.utc).isoformat(),
        processed_file='|'.join(OUTPUTS.values()), geographic_level='Provisional site/candidate and original/native cell; not certified new domains',
        temporal_resolution='Current geometry; common-decade activity proof separate; no historical-grooming inference',
        license='OSM ODbL / inherited SPASS WSL Data Policy', transformation_applied='Same exact unique length/native grid allocation; no invented GIS connector, surface-derived axes, tolerance or interpolation',
        quality_notes='Six provisional supports, not six completed terrain/snow profiles or new independent groups; all200candidates and old69groups kept', notes=SUMMARY), frames, (), DEFS)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    mask = dictionary.table.isin(OUTPUTS)
    dictionary.loc[mask, 'geographic_level'] = 'Provisional national candidate/source object/native cell; original69groups separate'
    dictionary.loc[mask, 'temporal_level'] = 'Current geometry and native grid support; no snow values read'
    dictionary.loc[mask, 'causal_role'] = 'Descriptive provisional proxy or coverage; not a causal/predictive feature or clustering acceptance'
    dictionary.loc[mask, 'notes'] = 'Approved descents retained regardless of grooming; ambiguous geometry unmeasured; current history/full-domain coverage uncertified'
    write_csv(dictionary, ROOT / 'metadata/data_dictionary.csv')
    state = dict(completed_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
        output_sha256={p: sha(p) for p in [*OUTPUTS.values(), NETWORK]}, provisional_candidates=6,
        original_member_objects=len(objects), native_spass_weight_rows=len(weights),
        unmeasured_original_objects=sum(not p['measured_in_proxy'] for p in objects),
        ski_activity_verified_candidates=sum(r['common_decade_ski_activity_verified'] for r in rows),
        grooming_choice_validated=True, grooming_scope_choice_pending=False, no_new_snow_or_terrain_values=True,
        no_old_group_or_profile_replacement_independent_domain_acceptance_or_automatic_exclusion=True)
    target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in state.items() if k not in ['input_sha256', 'output_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
