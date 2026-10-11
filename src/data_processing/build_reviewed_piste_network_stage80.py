"""Individually reviewed metric mask, exact unique axes and separate surfaces.

Unresolved original objects stay present. Coverage is relative to the full mapped
candidate network, not a certificate of the real operating/preentry domain.
"""
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.audit_piste_geometry_roles import TRANSFORM
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_REVIEWED_PISTE_NETWORK_STAGE80'
CONFIG = 'config/piste_individual_review_stage80.json'
DECISION = 'config/piste_metric_decisions_stage80.json'
OUTPUTS = ['data_processed/piste_individual_review_stage80.csv', 'data_processed/winter_profile_metric_network_stage80.csv']
NETWORK = 'data_interim/winter_profile_metric_network_stage80.json'
SUMMARY = 'reports/reviewed_piste_network_stage80_summary.json'


def read(path):
    return pd.read_csv(ROOT/path, dtype=str, keep_default_na=False)


def projected(e):
    cs = e['geometry']; x,y = TRANSFORM.transform([p['lon'] for p in cs], [p['lat'] for p in cs])
    return list(zip(x,y))


def union(lines):
    return unary_union(lines) if lines else None


def build(config, groups, members, index):
    unresolved = {}
    for c in config['unresolved_cases']:
        for wid in c['way_ids']:
            if wid in unresolved:
                raise ValueError('Repeated individually reviewed ID')
            unresolved[wid] = c
    rename = set(config['former_name_only_way_ids']); notes = {c['way_id']:c for c in config['non_geometry_notes']}
    sr = config['original_surface_relation']; special = sr['outer_way_id']
    review_ids = set(unresolved) | rename | set(notes) | {special}
    if len(unresolved) != 28 or len(review_ids) != 37 or not review_ids <= set(members.osm_id.astype(int)):
        raise ValueError('Exact reviewed original-object scope required')
    reviewed = []; network_rows = []; networks = []
    for g in groups.itertuples():
        part = members[members.station_group_id.eq(g.station_group_id)]
        all_lines = []; usable_lines = []; surfaces = []; member_provenance = []
        for r in part.itertuples():
            wid = int(r.osm_id); e = index[('way',wid)]
            if int(r.osm_version) != e['version'] or r.original_name != e.get('tags',{}).get('name',''):
                raise ValueError('Original identity/version/name differs')
            tags = e.get('tags',{}); pts = projected(e)
            status = 'candidate_proxy_no_individual_alert'; reason = ''; evidence = r.membership_evidence_source_ids
            measure = True; canonical = None
            if wid in unresolved:
                if not (r.literal_name_history_hint == 'True' or tags.get('abandoned') == 'yes' or wid == 672823371):
                    raise ValueError('Unresolved rationale not observed in original')
                status = 'unresolved_portion_not_measured'; reason = unresolved[wid]['reason']; measure = False
                evidence = '|'.join(unresolved[wid]['evidence_source_ids'])
            elif wid in rename:
                if set(json.loads(r.original_lifecycle_tags)) != {'was:name'} or r.literal_name_history_hint == 'True':
                    raise ValueError('Renaming is not the only literal history flag')
                status = 'former_name_only_not_former_geometry'; reason = config['former_name_reason']
                evidence += '|OSM_FORMER_NAME_SEMANTICS_STAGE80'
            elif wid in notes:
                status = 'non_geometry_note_retained'; reason = notes[wid]['reason']
            if r.candidate_role == 'way_axis_candidate':
                line = LineString(pts)
                if r.geometry_status != 'valid_axis_candidate' or not line.is_valid or not line.is_simple or line.is_empty:
                    raise ValueError('Unexpected axis needs individual review, not an automatic filter')
                all_lines.append(line)
                if measure:
                    usable_lines.append(line)
            elif r.candidate_role == 'explicit_surface_way_candidate':
                if wid == special:
                    relation = index[('relation', sr['relation_id'])]
                    if relation['tags'].get('type') != 'multipolygon' or relation['tags'].get('area') != 'yes':
                        raise ValueError('Original explicit surface relation required')
                    ms = relation['members']
                    if {(m['ref'],m['role']) for m in ms} != {(special,'outer'),(sr['inner_way_id'],'inner')}:
                        raise ValueError('Unknown extra polygon rings require review')
                    rings = {m['role']:projected(m) for m in ms}
                    if any(cs[0] != cs[-1] for cs in rings.values()):
                        raise ValueError('Cannot close an unclosed original ring')
                    polygon = Polygon(rings['outer'], [rings['inner']])
                    if not polygon.is_valid or polygon.is_empty:
                        raise ValueError('No topology repair allowed')
                    if rings['outer'] != pts:
                        raise ValueError('Relation outer geometry differs from original way')
                    status = 'surface_resolved_original_multipolygon_with_hole'; reason = sr['reason']
                    canonical = dict(osm_type='relation', osm_id=sr['relation_id'], osm_version=relation['version'],
                        inner_member_id=sr['inner_way_id'], inner_member_version=None, geometry_wkt=polygon.wkt)
                else:
                    if r.geometry_status != 'valid_standalone_surface_candidate':
                        raise ValueError('Unexpected surface needs individual review')
                    polygon = Polygon(pts)
                    if not polygon.is_valid or polygon.is_empty:
                        raise ValueError('No surface repair allowed')
                if measure:
                    surfaces.append(polygon)
            else:
                raise ValueError('Unknown role cannot be converted into axis')
            if wid in review_ids:
                reviewed.append(dict(source_id=SOURCE, station_group_id=r.station_group_id, osm_id=wid,
                    osm_version=r.osm_version, original_name=r.original_name, candidate_role=r.candidate_role,
                    original_lifecycle_tags=r.original_lifecycle_tags, original_review_tags=r.original_review_tags,
                    review_status=status, measurement_permitted_as_current_proxy=measure,
                    review_reason=reason, evidence_source_ids=evidence, original_object_retained=True,
                    historical_or_operating_status_certified=False,
                    canonical_surface_relation_id=sr['relation_id'] if wid == special else None))
            member_provenance.append(dict(osm_id=wid, osm_version=e['version'], candidate_role=r.candidate_role,
                measurement_permitted_as_current_proxy=measure, review_status=status, original_object_retained=True,
                canonical_surface=canonical))
        full = union(all_lines); usable = union(usable_lines); area = union(surfaces)
        full_len = full.length if full is not None else None; usable_len = usable.length if usable is not None else None
        # Subset identity is established BEFORE noding: usable_lines are the
        # identical retained original LineStrings from all_lines, with no move.
        # A second GEOS intersection of separately noded unions can miss common
        # subsegments at floating precision (observed ~3.876m at Arolla). Do not
        # snap/repair them or use that intersection as a missingness mask.
        ambiguous_len = full_len-usable_len if full_len is not None and usable_len is not None else full_len
        if ambiguous_len is not None and ambiguous_len < 0:
            raise ValueError('Unexpected nonmonotonic union length; no clipping or tolerance filter')
        network_rows.append(dict(source_id=SOURCE, station_group_id=g.station_group_id, station_group_name=g.station_group_name,
            group_retained=True, geometry_correspondence_verified=g.geometry_correspondence_verified,
            retained_original_object_count=len(part) if len(part) else None,
            original_axis_object_count=len(all_lines) if len(part) else None,
            measured_proxy_axis_object_count=len(usable_lines) if len(part) else None,
            unmeasured_ambiguous_axis_object_count=sum(int(w) in unresolved for w in part.osm_id) if len(part) else None,
            full_candidate_axis_id_sum_m=math.fsum(x.length for x in all_lines) if all_lines else None,
            full_unique_candidate_axis_length_m=full_len,
            measured_unique_proxy_axis_length_m=usable_len,
            unmeasured_unique_ambiguous_axis_length_m=ambiguous_len,
            measured_share_of_mapped_candidate_length=usable_len/full_len if full_len and usable_len is not None else None,
            mapped_surface_count=len(surfaces) if len(part) else None,
            mapped_surface_union_area_ha=area.area/10000 if area is not None else None,
            current_proxy_not_verified_preentry=True, full_real_domain_coverage_certified=False,
            metric_status='observed_candidate_subset_with_ambiguous_portions_missing' if ambiguous_len and ambiguous_len>0 else 'mapped_current_proxy' if usable is not None else 'missing_geometry_not_zero',
            display_scope_name='La Dôle–Tuffes (domaine transfrontalier)' if g.station_group_id == 'MP_GROUP_RESORT__la_dole_jura_sur_leman' else g.station_group_name))
        networks.append(dict(station_group_id=g.station_group_id, crs='EPSG:2056',
            full_unique_candidate_axis_wkt=full.wkt if full is not None else None,
            measured_unique_proxy_axis_wkt=usable.wkt if usable is not None else None,
            unmeasured_original_axis_wkts=[dict(osm_id=int(w),geometry_wkt=LineString(projected(index[('way',int(w))])).wkt)
                for w in part.osm_id if int(w) in unresolved],
            separate_mapped_surface_union_wkt=area.wkt if area is not None else None,
            original_members_retained=member_provenance))
    frame = pd.DataFrame(network_rows)
    if len(frame) != 69 or not frame.station_group_id.is_unique or len(reviewed) != 37:
        raise ValueError('All groups and individually reviewed objects must survive')
    return [pd.DataFrame(reviewed), frame], networks


EXTRA_DEFS = {
    'measurement_permitted_as_current_proxy':('Use for current qualified proxy only; not a preentry/active-status certificate','boolean'),
    'review_reason':('Individual documented reasoning distinguishing naming, difficulty, topology and abandonment','text'),
    'evidence_source_ids':('Existing primary proof or refused-source IDs and observed original-tag semantic documentation','identifiers'),
    'original_object_retained':('True even when the future metric for this portion is not measured','boolean'),
    'historical_or_operating_status_certified':('False: neither literal tags nor current operator identity certify historical operation','boolean'),
    'canonical_surface_relation_id':('Original multipolygon relation providing complete outer/inner geometry; not an invented axis','identifier'),
    'retained_original_object_count':('All retained assigned objects, NA for unresolved correspondence','count'),
    'original_axis_object_count':('Original mapped axes, not official piste count','count'),
    'measured_proxy_axis_object_count':('Mapped axes after approved individual unresolved-portion rule','count'),
    'unmeasured_ambiguous_axis_object_count':('Individually reviewed unresolved axes kept but not measured','count'),
    'full_candidate_axis_id_sum_m':('All mapped axis lengths counted once per original ID, including unresolved portion candidates','metres'),
    'full_unique_candidate_axis_length_m':('Exact within-group union of all candidate axes; reference denominator is not exhaustive real operating network','metres'),
    'measured_unique_proxy_axis_length_m':('Exact union of current proxy axes after individual review; shared portions counted once','metres'),
    'unmeasured_unique_ambiguous_axis_length_m':('Full unique length minus measured subset unique length, not a second floating-point GEOS difference; shared portions not double removed','metres'),
    'measured_share_of_mapped_candidate_length':('Measured unique length/full mapped candidate unique length; not real-domain completeness','fraction'),
    'mapped_surface_count':('Separate valid surfaces including original multipolygon with hole, not axes','count'),
    'mapped_surface_union_area_ha':('Separate exact union of original mapped polygons; not exhaustive surveyed piste area','hectares'),
    'full_real_domain_coverage_certified':('Always false: OSM source extent is not full operating-domain or preentry proof','boolean'),
    'display_scope_name':('Derived readable scope name; historical original name preserved separately','text'),
    'metric_status':('Current proxy, unresolved portions not measured, or missing correspondence; never automatic group exclusion','category'),
}


def register(frames, source_docs):
    master=read('metadata/data_sources_master.csv'); records=[]
    for m in source_docs:
        records.append(dict(source_id=m['source_id'], variable_name='original_tag_semantics', variable_description=m['purpose'],
            source_organisation=m['organisation'], source_page_url=m['url'], retrieval_date=m['retrieval_date'][:10],
            local_raw_file=m['raw_file'], retrieval_method='Archived actual HTTP200/SHA, no provider refusals bypassed',
            geographic_level='OSM key semantics, not station observations', license='Publisher terms; archived source retained',
            quality_notes='Tag semantics not independently dated operating history', notes='SHA='+m['sha256']+'; '+SUMMARY))
    records.append(dict(source_id=SOURCE, variable_name='individually_reviewed_exact_metric_network',
        variable_description='Approved unresolved-portion missingness, all objects/groups retained; exact qualified current proxy axes and separate surfaces',
        source_organisation='Thesis derived from archived OSM and documented primary proofs', retrieval_date='2026-10-12',
        processed_file='|'.join(OUTPUTS+[NETWORK]), geographic_level='69 groups, not municipal outcomes',
        temporal_resolution='Current geometry proxy; historical/operating completeness not certified', license='OSM ODbL; primary sources unchanged',
        transformation_applied='37 explicit individual reviews, unresolved28axes not measured, exact union/no tolerance, original hole retained for surface',
        quality_notes='No group exclusion, repaired geometry, automatic tag filter or old-profile rewrite', notes=SUMMARY))
    fresh=[r for r in records if r['source_id'] not in set(master.source_id)]
    if fresh:write_csv(pd.concat([master,pd.DataFrame(fresh).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=read('metadata/data_dictionary.csv'); add=[]
    inherited=dictionary[dictionary.table.isin(['piste_flagged_objects_stage79','winter_profile_piste_groups_stage79','winter_profile_exact_piste_overlap_stage63'])]
    for path, frame in zip(OUTPUTS,frames):
        table=Path(path).stem
        for c in frame:
            if ((dictionary.table==table)&dictionary.variable.eq(c)).any():continue
            if c in EXTRA_DEFS:description,unit=EXTRA_DEFS[c]
            else:
                previous=inherited[inherited.variable.eq(c)]
                if previous.empty:raise ValueError('No understood definition '+c)
                description,unit=previous.iloc[0][['description','unit']]
                if c=='group_retained':description='True for all69approved derived groups, no automatic group exclusion'
                if c=='review_status':description='Individual naming/status/topology finding; not blanket lifecycle exclusion'
            add.append(dict(variable=c,table=table,description=description,unit=unit,data_type=str(frame[c].dtype),
                geographic_level='Retained group or original object', temporal_level='Current qualified mapped proxy', source_id=SOURCE,
                raw_or_derived='individual review/exact geometry derivation', formula='build_reviewed_piste_network_stage80.py; explicit original IDs; no proximity tolerance',
                causal_role='Coverage and profile-support geometry; not estimated effects or fitted classes',
                missing_share=f"{(frame[c].isna() | frame[c].astype(str).eq('')).mean():.6f}", notes=DECISION+'; historical/current distinction retained'))
    if add:write_csv(pd.concat([dictionary,pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')


def main():
    decision=json.loads((ROOT/DECISION).read_text(encoding='utf-8'))
    if decision['unresolved_portions']!='retain_original_objects_do_not_measure_publish_coverage' or decision['remove_group_or_commune']:
        raise ValueError('Only approved individual missingness rule')
    config=json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    paths=[CONFIG,DECISION,'src/data_processing/build_reviewed_piste_network_stage80.py',
        'data_processed/winter_profile_piste_members_stage79.csv','data_processed/winter_profile_piste_groups_stage79.csv',
        'reports/remaining_piste_assignments_stage79_summary.json','config/piste_metric_sources_stage80.json']
    inputs={p:sha(p) for p in paths}; source_docs=[]
    for s in json.loads((ROOT/paths[-1]).read_text(encoding='utf-8')):
        metas=list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
        if len(metas)!=1:raise ValueError('Require archived semantic source')
        m=json.loads(metas[0].read_text(encoding='utf-8'))
        if sha(m['raw_file'])!=m['sha256']:raise ValueError('Original changed')
        inputs[m['raw_file']]=m['sha256']; inputs[metas[0].relative_to(ROOT).as_posix()]=sha(metas[0].relative_to(ROOT).as_posix()); source_docs.append(m)
    index,_,_=originals()
    frames,networks=build(config,read(paths[4]),read(paths[3]),index)
    for sid in set(frames[0].evidence_source_ids.str.split('|').explode()):
        if sid not in set(read('metadata/data_sources_master.csv').source_id) and sid not in {m['source_id'] for m in source_docs}:
            raise ValueError('Unregistered proof '+sid)
        for meta in (ROOT/'data_external/source_evidence').glob(sid+'_*.metadata.json'):
            m=json.loads(meta.read_text(encoding='utf-8')); inputs[m['raw_file']]=m['sha256'];inputs[meta.relative_to(ROOT).as_posix()]=sha(meta.relative_to(ROOT).as_posix())
    target=ROOT/SUMMARY
    if target.exists():
        state=json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256']!=inputs or any(sha(p)!=h for p,h in state['output_sha256'].items()):raise ValueError('Frozen reviewed network differs')
    else:
        for path,frame in zip(OUTPUTS,frames):write_csv(frame,ROOT/path)
        (ROOT/NETWORK).write_text(json.dumps(networks,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        g=frames[1]
        state=dict(completed_at=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,
            output_sha256={p:sha(p) for p in OUTPUTS+[NETWORK]}, retained_group_count=69, retained_original_object_count=2001,
            individual_review_count=37, unresolved_unmeasured_axis_count=28, former_name_only_count=6,
            non_geometry_note_count=2, original_surface_with_hole_resolved_count=1,
            measured_proxy_axis_group_count=int(g.measured_unique_proxy_axis_length_m.notna().sum()),
            groups_with_unmeasured_portions=g.loc[g.unmeasured_unique_ambiguous_axis_length_m.gt(0),['station_group_id','full_unique_candidate_axis_length_m','measured_unique_proxy_axis_length_m','unmeasured_unique_ambiguous_axis_length_m','measured_share_of_mapped_candidate_length']].to_dict('records'),
            no_group_exclusion_or_original_rewrite=True,no_historical_calendar_change=True,new_snow_or_terrain_values_read=False)
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    register(frames,source_docs)
    print(json.dumps({k:v for k,v in state.items() if k not in ['input_sha256','output_sha256','groups_with_unmeasured_portions']},ensure_ascii=False))


if __name__=='__main__':main()
