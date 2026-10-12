"""Reuse an already accepted perimeter, not a new connected-domain merge or fit."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from bs4 import BeautifulSoup
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS
from src.descriptive.prepare_national_similarity_inventory_stage85 import DEFS as PARENT_DEFS

SOURCE = 'DERIVED_NATIONAL_COMPARABLE_CONTEXT_STAGE86'
RID = 'rougemont_rougemont_la_videmanette'
GID = 'MP_GROUP_RESORT__gstaad'
OUTPUTS = ['data_processed/national_similarity_inventory_stage86.csv',
           'data_processed/national_similarity_listing_lineage_stage86.csv',
           'data_processed/national_similarity_feature_context_stage86.csv']
SUMMARY = 'reports/national_similarity_context_stage86_summary.json'
DEFS = dict(PARENT_DEFS) | {
    'listing_link_status': ('Original approved component, documented alias inside already retained perimeter, or unresolved listing; no new group merge', 'category'),
    'listing_top_altitude_source_m': ('Original undated listing summit altitude, not length-weighted piste altitude', 'metres'),
    'listing_piste_length_source_km': ('Original catalogue piste length, unknown methodology; never substituted into exact measured axes', 'kilometres'),
    'listing_lift_count_source': ('Original listing lift count, not unique group lifts and never summed across overlapping listings', 'count'),
    'not_automatically_approved_clustering_feature': ('True: raw context remains separate from validated comparable features', 'boolean'),
    'measured_unique_piste_axes_m': ('Existing eligible exact unique piste axes, ambiguous portions omitted and coverage retained', 'metres'),
    'length_weighted_piste_altitude_m': ('Existing observed altitude weighted by exact piste length on native 2m terrain', 'metres'),
    'terrain_northness': ('Existing exact-length-weighted cosine of observed terrain aspect; not piste travel direction', 'dimensionless'),
    'terrain_eastness': ('Existing exact-length-weighted sine of observed terrain aspect; not piste travel direction', 'dimensionless'),
    'common_ten_winter_mean_m': ('Fixed2013/14–2022/23 SPASS mean, equal winters, metres assumed; descriptive not preentry', 'metres, assumed'),
    'minimum_six_city_road_minutes': ('Minimum of all six already approved city road times; no ARE/BAV substitution for new listings', 'minutes'),
    'road_city_count_observed': ('Count of approved city times actually available, not new guessed endpoints', 'count'),
    'geometry_measured_share': ('Eligible length / mapped candidate length; not real-world exhaustive mapping coverage', 'share'),
    'terrain_altitude_coverage_share': ('Observed native2m altitude length / eligible measured piste length', 'share'),
    'terrain_orientation_coverage_share': ('Observed aspect length / eligible measured piste length; flat/missing distinct', 'share'),
    'snow_minimum_observed_length_share': ('Smallest observed native SPASS length share across the common winters', 'share'),
    'comparable_six_fields_available': ('All six comparable values available; readiness only, never automatic clustering inclusion', 'boolean'),
    'automatic_clustering_inclusion': ('Always false: no feature protocol, model sample, classes or missingness rule chosen here', 'boolean'),
}


def numeric(value):
    return pd.to_numeric(pd.Series([value]), errors='coerce').iloc[0]


def main():
    paths = ['src/descriptive/consolidate_national_preparation_stage86.py',
             'data_processed/national_similarity_inventory_stage85.csv',
             'data_processed/national_similarity_listing_lineage_stage85.csv',
             'data_processed/resort_master.csv',
             'config/piste_remaining_assignments_stage79.json',
             'data_external/source_evidence/GSTAAD_EGGLI_STAGE79_20261011T214812Z.html',
             'data_external/source_evidence/GSTAAD_EGGLI_STAGE79_20261011T214812Z.metadata.json',
             'data_processed/terrain_reviewed_profiles_stage82.csv',
             'data_processed/common_snow_profiles_stage84.csv',
             'data_processed/accessibility_road_group_reference_stage79.csv',
             'data_processed/winter_profile_urban_city_detail_stage57.csv',
             'data_processed/winter_profile_piste_members_stage79.csv']
    inputs = {p: sha(p) for p in paths}
    inv = pd.read_csv(ROOT / paths[1], keep_default_na=False)
    lineage = pd.read_csv(ROOT / paths[2], dtype=str, keep_default_na=False)
    master = pd.read_csv(ROOT / paths[3], dtype=str, keep_default_na=False).set_index('resort_id')
    curation = json.loads((ROOT / paths[4]).read_text(encoding='utf-8'))
    approved = next(g for g in curation['groups'] if g['station_group_id'] == GID)
    metadata = json.loads((ROOT / paths[6]).read_text(encoding='utf-8'))
    if inputs[paths[5]] != metadata['sha256'] or metadata['http_status'] != 200:
        raise ValueError('Previously archived official evidence differs')
    title = BeautifulSoup((ROOT / paths[5]).read_text(encoding='utf-8'), 'html.parser').title.get_text()
    if not all(token in title for token in ['Eggli', 'Videmanette', 'Rougemont']):
        raise ValueError('Official identity evidence requires individual review')
    if 'Eggli/Videmanette' not in approved['scope_note'] or 'GSTAAD_EGGLI_STAGE79' not in approved['evidence_source_ids']:
        raise ValueError('Do not expand the previously retained physical perimeter')
    assigned = pd.read_csv(ROOT / paths[11])
    part = assigned[assigned.station_group_id.eq(GID)]
    if len(part) != 132 or set(part.osm_id.astype(int)) != set(approved['way_ids']):
        raise ValueError('Previously retained Gstaad objects differ')
    target_id = 'DESC_LISTING_PENDING__' + RID
    if len(inv[inv.preparation_unit_id.eq(target_id)]) != 1 or len(lineage[lineage.resort_id.eq(RID)]) != 1:
        raise ValueError('Stable original catalogue identity must be unique')
    inv = inv[~inv.preparation_unit_id.eq(target_id)].copy()
    original_components = inv.loc[inv.preparation_unit_id.eq(GID), 'component_resort_ids'].iloc[0]
    inv.loc[inv.preparation_unit_id.eq(GID), 'component_resort_ids'] = original_components + '|' + RID
    evidence_ids = '|GSTAAD_EGGLI_STAGE79|DERIVED_REMAINING_PISTE_ASSIGNMENTS_STAGE79'
    inv.loc[inv.preparation_unit_id.eq(GID), 'source_ids'] += evidence_ids
    lineage['listing_link_status'] = lineage.preparation_unit_id.map(
        lambda x: 'original_approved_component' if not x.startswith('DESC_LISTING_PENDING__') else 'pending_independent_domain_review')
    lineage.loc[lineage.resort_id.eq(RID), 'preparation_unit_id'] = GID
    lineage.loc[lineage.resort_id.eq(RID), 'listing_link_status'] = 'documented_alias_inside_previously_retained_perimeter'
    lineage.loc[lineage.resort_id.eq(RID), 'source_ids'] += evidence_ids
    raw_fields = {'listing_top_altitude_source_m': 'altitude_top_m',
                  'listing_piste_length_source_km': 'ski_area_km', 'listing_lift_count_source': 'number_lifts'}
    for column, original in raw_fields.items():
        lineage[column] = lineage.resort_id.map(lambda r: numeric(master.loc[r, original]))
    lineage['not_automatically_approved_clustering_feature'] = True
    # Fix presence semantics in this new layer only: literal NA is not a measured value.
    for idx, row in inv.iterrows():
        ids = str(row.component_resort_ids).split('|') if row.component_resort_ids else []
        inv.loc[idx, 'provided_structural_context_available'] = bool(ids) and all(
            pd.notna(numeric(master.loc[r, c])) for r in ids for c in raw_fields.values())
    terrain = pd.read_csv(ROOT / paths[7], float_precision='round_trip').set_index('station_group_id')
    snow = pd.read_csv(ROOT / paths[8], float_precision='round_trip').set_index('station_group_id')
    route = pd.read_csv(ROOT / paths[9], float_precision='round_trip')
    cities = pd.read_csv(ROOT / paths[10])[['municipality_bfs_id', 'city_name']].drop_duplicates()
    if len(cities) != 6 or not cities.municipality_bfs_id.is_unique:
        raise ValueError('Same six approved cities required')
    road = route[route.municipality_bfs_id.isin(cities.municipality_bfs_id)]
    features = []
    mapping = {'measured_unique_piste_axes_m': 'unique_mapped_axis_length_m',
               'length_weighted_piste_altitude_m': 'length_weighted_observed_altitude_m',
               'terrain_northness': 'terrain_northness', 'terrain_eastness': 'terrain_eastness',
               'geometry_measured_share': 'measured_share_of_mapped_candidate_length',
               'terrain_orientation_coverage_share': 'orientation_coverage_share'}
    six = ['measured_unique_piste_axes_m', 'length_weighted_piste_altitude_m', 'terrain_northness',
           'terrain_eastness', 'common_ten_winter_mean_m', 'minimum_six_city_road_minutes']
    for row in inv.itertuples():
        gid = row.preparation_unit_id
        rec = dict(source_id=SOURCE, preparation_unit_id=gid, unit_name=row.unit_name, identity_level=row.identity_level,
                   within_swiss_preparation_scope=row.within_swiss_preparation_scope, automatic_clustering_inclusion=False,
                   road_city_count_observed=0, source_ids=str(row.source_ids))
        rec.update({c: float('nan') for c in [*mapping, 'terrain_altitude_coverage_share', 'common_ten_winter_mean_m',
                                            'snow_minimum_observed_length_share', 'minimum_six_city_road_minutes']})
        if row.identity_level == 'existing_approved_group':
            t, s = terrain.loc[gid], snow.loc[gid]
            rec.update({c: t[original] for c, original in mapping.items()})
            rec['terrain_altitude_coverage_share'] = t.observed_altitude_length_m / t.unique_mapped_axis_length_m
            rec['common_ten_winter_mean_m'] = s.common_ten_winter_mean_m
            rec['snow_minimum_observed_length_share'] = s.min_observed_length_share
            routes = road[road.station_group_id.eq(gid)].road_reference_minutes.dropna()
            rec['road_city_count_observed'] = len(routes)
            if len(routes) == 6:
                rec['minimum_six_city_road_minutes'] = routes.min()
                rec['source_ids'] += '|DERIVED_CONNECTED_GROUP_OVERLAY_STAGE79'
        rec['comparable_six_fields_available'] = all(pd.notna(rec[c]) for c in six)
        features.append(rec)
    frames = [inv, lineage, pd.DataFrame(features)]
    for f in frames:
        f['source_id'] = SOURCE
    if len(inv) != 272 or len(lineage) != 271 or not lineage.resort_id.is_unique or not inv.preparation_unit_id.is_unique:
        raise ValueError('Retain all original identities without a duplicated alias-domain')
    target = ROOT / SUMMARY
    if target.exists():
        summary = json.loads(target.read_text(encoding='utf-8'))
        if summary['input_sha256'] != inputs or any(sha(p) != h for p, h in summary['output_sha256'].items()):
            raise ValueError('Frozen context differs; create a new version')
    else:
        for p, f in zip(OUTPUTS, frames):
            write_csv(f, ROOT / p)
        summary = dict(completed_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
                       output_sha256={p: sha(p) for p in OUTPUTS}, approved_groups_unchanged=69,
                       original_listing_ids_retained=271, swiss_point_original_listings=268,
                       original_listing_ids_linked_to_retained_perimeters=68,
                       swiss_provisional_listings_still_needing_domain_review=200,
                       swiss_preparation_records_not_verified_domain_count=269, foreign_standalone_audit_records=3,
                       alias=dict(resort_id=RID, retained_group_id=GID, official_source_id=metadata['source_id'],
                                  official_title=title, official_page_url=metadata['url'],
                                  already_retained_scope=approved['scope_note'], accepted_piste_object_count=len(part)),
                       comparable_six_field_records_available=int(frames[2].comparable_six_fields_available.sum()),
                       no_new_physical_group_geometry_exposure_or_fit=True,
                       original_catalogue_measures_not_substituted_or_summed=True,
                       existing_ORS_not_mixed_with_ARE_or_unverified_nearest_stops=True)
        target.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    if SOURCE not in set(sources.source_id):
        record = dict(source_id=SOURCE, variable_name='national_descriptive_comparable_context_and_alias_lineage',
                      variable_description='69retained scopes plus200Swiss provisional listings;271original IDs, one already-covered Videmanette alias not a second domain',
                      source_organisation='Thesis audit of original catalogue, archived official Gstaad evidence and reviewed OSM/SPASS/Swiss terrain/ORS',
                      retrieval_date='2026-10-12', processed_file='|'.join(OUTPUTS),
                      geographic_level='Prior approved group/provisional listing, not a completed national domain universe',
                      temporal_resolution='Common2013/14–2022/23snow/current qualified geometric and road proxies/undated original catalogue',
                      license='Parent source licences and attribution preserved; no new external collection',
                      transformation_applied='Stable-ID alias bridge to previously retained scope; comparable measures separated from listing context',
                      quality_notes='No automatic nonmembership, grouping, feature aggregation, nearest-stop route, sample exclusion or model fit', notes=SUMMARY)
        write_csv(pd.concat([sources, pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    add = []
    for path, frame in zip(OUTPUTS, frames):
        for column in frame:
            if ((dictionary.table == Path(path).stem) & dictionary.variable.eq(column)).any():
                continue
            description, unit = DEFS[column]
            add.append(dict(variable=column, table=Path(path).stem, description=description, unit=unit,
                            data_type=str(frame[column].dtype), geographic_level='Approved group or provisional source listing',
                            temporal_level='Common descriptive decade and qualified current/undated source context', source_id=SOURCE,
                            raw_or_derived='source context or derived, never imputed', formula=description,
                            causal_role='Descriptive preparation only; no fitted classes or predictive/causal claim',
                            missing_share=f'{frame[column].replace("", float("nan")).isna().mean():.6f}',
                            notes='Original source definitions and stable IDs retained; no automatic clustering inclusion'))
    if add:
        write_csv(pd.concat([dictionary, pd.DataFrame(add).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')
    print(json.dumps({k: v for k, v in summary.items() if k not in ['input_sha256', 'output_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
