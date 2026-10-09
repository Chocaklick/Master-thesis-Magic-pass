"""Stage44: source/calendar inventory, not station features or new assignments."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_current_piste_geometry import validate_response
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

CONFIG = 'config/winter_profile_terrain_snow_source_review_stage44.json'
CHECKPOINT = 'data_interim/current_piste_geometry_collection_checkpoint.json'
OUTPUT = 'data_processed/winter_profile_terrain_snow_source_feasibility.csv'
SUMMARY = 'reports/terrain_snow_source_feasibility_summary.json'
SOURCE = 'DERIVED_TERRAIN_SNOW_FEASIBILITY_2026_10_09'
INPUTS = [CONFIG, CHECKPOINT, 'data_processed/winter_profile_five_dimension_groups.csv',
    'data_processed/winter_profile_approved_snow_windows.csv',
    'config/winter_profile_historical_source_review.json',
    'reports/approved_profile_context_summary.json',
    'src/descriptive/audit_terrain_snow_source_feasibility.py',
    'src/data_collection/collect_current_piste_geometry.py']
DEFS = {
    'station_group_id': ('Unchanged connected station group ID', 'identifier'),
    'station_group_name': ('Retained group name', 'name'),
    'first_base_entry_month': ('Retained group base entry; not a new component or summer date', 'month'),
    'requested_winter_count': ('Approved five own December-April preentry winter calendars', 'count'),
    'spass_calendar_winter_count': ('Whole requested winters within original SPASS calendar; not valid-cell coverage', 'count'),
    'spass_calendar_missing_winter_count': ('Requested whole winters beyond SPASS archive, not filled', 'count'),
    'spass_missing_winter_start_years': ('December years of requested winters beyond SPASS', 'years'),
    'oshd_candidate_calendar_winter_count': ('Whole requested winters within candidate OSHD2016-2025 calendar; no grid downloaded or value validated', 'count'),
    'overlap_calendar_winter_count': ('Requested whole winters within both products calendars, not observed comparable cells', 'count'),
    'recent_missing_spass_within_oshd_calendar_count': ('SPASS missing calendars potentially covered by candidate; not substituted', 'count'),
    'oshd_candidate_covers_all_five_calendars': ('Calendar availability only; not a new source reference choice', 'boolean'),
    'existing_targeted_history_source_ids': ('Exact already registered source IDs retained in group parents and previous targeted review; not a complete historical audit', 'identifiers'),
    'piste_history_audit_status': ('Targeted prior evidence only or group history review pending; neither certifies unchanged pistes', 'status'),
    'current_piste_inventory_status': ('Global archived query success, not coverage or assignment for this group', 'status'),
    'group_piste_assignment_verified': ('False: no OSM-to-group assignment applied', 'boolean'),
    'snow_feature_computed': ('False: source compatibility and aggregation require validation', 'boolean'),
    'source_id': ('Registered derived source inventory', 'identifier'),
    'parent_source_ids': ('Registered parent datasets; candidate model remains unselected', 'identifiers'),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def build_inventory(groups, windows, history, config, collection_status):
    if not groups.station_group_id.is_unique or windows.duplicated(['station_group_id', 'winter_start_year']).any():
        raise ValueError('Duplicate group or winter key')
    if set(windows.station_group_id) != set(groups.station_group_id):
        raise ValueError('Group/calendar key mismatch')
    rows = []
    reviewed = {r['source_id'] for r in history['records']}
    for g in groups.itertuples():
        w = windows[windows.station_group_id.eq(g.station_group_id)]
        if len(w) != 5 or w.winter_start_year.max() - w.winter_start_year.min() != 4:
            raise ValueError('Exactly five consecutive approved winters required')
        start = pd.to_datetime(w.winter_start_date); end = pd.to_datetime(w.winter_end_date)
        if not end.lt(pd.Timestamp(g.first_base_entry_month)).all():
            raise ValueError('Preentry window leakage')
        if not pd.to_datetime(w.first_base_entry_month).eq(pd.Timestamp(g.first_base_entry_month)).all():
            raise ValueError('Group entry mismatch')
        spass = w.spass_calendar_within_archive
        if not pd.api.types.is_bool_dtype(spass):
            raise ValueError('Explicit boolean archive flag required')
        new = start.ge(pd.Timestamp(config['snow_candidate_calendar_start'])) & end.le(pd.Timestamp(config['snow_candidate_calendar_end']))
        references = sorted(set(str(g.parent_source_ids).split('|')) & reviewed)
        rows.append(dict(station_group_id=g.station_group_id, station_group_name=g.station_group_name,
            first_base_entry_month=g.first_base_entry_month, requested_winter_count=5,
            spass_calendar_winter_count=int(spass.sum()), spass_calendar_missing_winter_count=int((~spass).sum()),
            spass_missing_winter_start_years='|'.join(map(str, w.loc[~spass, 'winter_start_year'].tolist())),
            oshd_candidate_calendar_winter_count=int(new.sum()), overlap_calendar_winter_count=int((spass & new).sum()),
            recent_missing_spass_within_oshd_calendar_count=int((~spass & new).sum()),
            oshd_candidate_covers_all_five_calendars=bool(new.all()),
            existing_targeted_history_source_ids='|'.join(references),
            piste_history_audit_status='partial_existing_component_evidence_not_piste_verification' if references else 'group_history_review_pending',
            current_piste_inventory_status=collection_status, group_piste_assignment_verified=False,
            snow_feature_computed=False, source_id=SOURCE,
            parent_source_ids='DERIVED_APPROVED_PROFILE_CONTEXT_2026_10_09|DERIVED_FIVE_DIMENSION_AVAILABILITY_2026_10_09|SLF_SPASS_HSCLQMD_GRID_1962_2023|'
                + config['snow_candidate_source_id'] + '|' + config['piste_source_id']))
    return pd.DataFrame(rows)


def geometry_inventory(payload):
    count = validate_response(payload)
    elements = payload['elements']; ways = [e for e in elements if e['type'] == 'way']
    return dict(element_count=count, way_count=len(ways), relation_count=count-len(ways),
        downhill_way_count=sum(e['tags'].get('piste:type') == 'downhill' for e in ways),
        downhill_relation_count=sum(e['type'] == 'relation' and e['tags'].get('piste:type') == 'downhill' for e in elements),
        site_relation_count=sum(e['tags'].get('site') == 'piste' for e in elements),
        closed_way_count=sum(len(e.get('nodes', [])) > 1 and e['nodes'][0] == e['nodes'][-1] for e in ways),
        ways_without_two_geometry_points=sum(len(e.get('geometry', [])) < 2 for e in ways),
        osm_snapshot=payload['osm3s']['timestamp_osm_base'],
        element_count_is_not_piste_count=True, country_query_is_not_verified_group_scope=True,
        site_relations_may_include_non_downhill=True, timestamp_is_edit_not_construction_date=True)


def register(frame, config, collection):
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    # Web consultation records have no invented local original/HTTP checksum.
    consultations = [
        ('SLF_OSHD_PF_250M_WY2016_2025_CANDIDATE', 'WSL SLF / Zenodo', 'OSHD particle-filter daily snow 250m WY2016-2025', config['snow_candidate_url'], 'Calendar2015-09-01..2025-08-31. Different physical model/assimilation from SPASS; candidate only; no ZIP downloaded. Paper explicitly states data CC-BY4.0, repository displays copyright notice: inspect packaged terms before bulk reuse.'),
        ('SLF_OSHD_PF_DATASET_PAPER_2026', 'WSL SLF / The Cryosphere', 'Peer-reviewed OSHD2016-2025 model and validation paper', config['snow_candidate_paper_url'], '15June2026; snow-model variables and limits, not prepared piste/snowmaking measurements. Assimilation shares in-situ observation lineage; not independent IMIS validation.'),
        ('SLF_SPASS_CATALOGUE_REVIEW_2026_10_09', 'WSL SLF / EnviDat', 'SPASS catalogue recent-extension check', 'https://www.envidat.ch/metadata/spass---new-gridded-snow-datasets-for-switzerland', 'Consulted catalogue lists retained HSCLQMD hydrological archive1962-2023; no identical recent extension verified, not proof none exists elsewhere.'),
        ('SLF_SEASONAL_OSHD_CATALOGUE_REVIEW_2026_10_09', 'WSL SLF / EnviDat', 'Seasonal snow WY2016-2022 catalogue', 'https://www.envidat.ch/metadata/seasonal-snow-data-wy-2016-2022', 'Alternative catalogue consulted; access links do not certify a2024/25 extension.'),
        ('SLF_CLIMATOLOGICAL_OSHD_CATALOGUE_REVIEW_2026_10_09', 'WSL SLF / EnviDat', 'Climatological snow1998-2022 catalogue', 'https://www.envidat.ch/metadata/climatological-snow-data-1998-2022-oshd', 'Alternative catalogue only, no files collected or source promoted.'),
        ('OPENSKIDATA_SOURCE_REVIEW_2026_10_09', 'OpenSkiData', 'Current ski data origin, identifiers and licensing', 'https://www.openskidata.org/', 'OSM/Skimap upstream, processed content IDs unstable. ODbL attribution obligations; third-party clustering not our71groups. Website and independent metadata endpoint returned HTTP403 in terminal; no bypass, files not downloaded.'),
        ('OPENSKIDATA_FORMAT_REVIEW_2026_10_09', 'OpenSkiData / GitHub', 'Public data format and upstream identifiers', 'https://github.com/russellporter/openskidata-format', 'Software license is not data license. Retain upstream keys/date instead of assuming content-derived IDs stable.'),
        ('SWISSTOPO_APP_PISTE_ORIGIN_REVIEW_2026_10_09', 'swisstopo', 'App terms: piste data origin', 'https://www.swisstopo.admin.ch/fr/conditions-utilisation-app-swisstopo', 'Downhill pistes in app attributed to OSM, not a second independent official geometry dataset.'),
        ('OSM_DOWNHILL_TAG_REVIEW_2026_10_09', 'OpenStreetMap contributors / Wiki', 'Downhill ways, areas and relations', config['piste_documentation'], 'Deduplicate shared ways/relation membership before length calculations; site=piste may be mixed. Mapping/edit time not construction or unchanged history.'),
        ('OSM_OVERPASS_USAGE_REVIEW_2026_10_09', 'Overpass public service operator', 'Public Overpass API usage policy', config['service_usage_policy'], 'One bounded cached national query; no parallel crawl, tile harvesting or automatic retry.'),
        ('OPENSNOWMAP_DATA_REVIEW_2026_10_09', 'OpenSnowMap / OSM contributors', 'OSM piste/lift source export option', 'https://www.opensnowmap.org/iframes/data.html', 'ODbL OSM upstream; entire planet export not collected, not an independent measurement.'),
    ]
    records = [dict(source_id=sid, variable_name='source_feasibility_reference', variable_description=title,
        source_organisation=org, source_dataset_name=title, source_page_url=url, retrieval_date='2026-10-09',
        retrieval_method='Primary webpage consultation; no original data files downloaded', quality_notes=note,
        confidence_level='documented candidate or provenance, not analytical station observation',
        license='See primary provider terms; not automatically interchangeable') for sid, org, title, url, note in consultations]
    records += [dict(source_id=config['piste_source_id'], variable_name='current_osm_piste_geometry',
        variable_description='Current Swiss-area downhill ways/relations and piste sites, unassigned to retained groups',
        source_organisation='OpenStreetMap contributors via Overpass', source_dataset_name='Bounded current OSM piste inventory',
        source_page_url=config['piste_documentation'], api_endpoint=config['piste_endpoint'], api_parameters=config['piste_query'],
        retrieval_date=collection['retrieval_date'], retrieval_method='One read-only POST; immutable response/version/date and SHA256 retained',
        local_raw_file=collection.get('raw_file', ''), geographic_level='Swiss country-query elements, cross-border full geometries possible',
        temporal_resolution='Current frozen OSM snapshot; not historical verified pistes', license='ODbL; credit OpenStreetMap contributors',
        quality_notes='Ways/relations overlap; closed ways may be areas; site relations may be Nordic/mixed; no rebuild or group assignment',
        confidence_level='archived map elements, not complete official ski-domain inventory', notes='sha256=' + collection.get('sha256', '')),
        dict(source_id=SOURCE, variable_name='terrain_snow_source_feasibility',
        variable_description='Unchanged group-level calendar availability and pending piste source/history audit',
        source_organisation='Thesis derived source audit', source_dataset_name='Stage44 source feasibility',
        retrieval_date='2026-10-09', retrieval_method='Local exact calendar/key audit; no snow values or feature estimates',
        local_raw_file='|'.join(INPUTS), processed_file=OUTPUT, geographic_level='71 unchanged connected station groups',
        temporal_resolution='Five own preentry Dec-Apr calendar windows; current geometry availability',
        license='Inherits parent terms', quality_notes='Candidate calendars are not valid-cell coverage. No splicing, classification, exclusion or effect estimate.')]
    ids = [r['source_id'] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate new source ID')
    write_csv(pd.concat([master[~master.source_id.isin(ids)], pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    definitions = []
    for col in frame:
        description, unit = DEFS[col]
        definitions.append(dict(variable=col, table=Path(OUTPUT).stem, description=description, unit=unit,
            data_type=str(frame[col].dtype), geographic_level='unchanged station group', temporal_level='source/calendar audit only',
            source_id=SOURCE, raw_or_derived='derived feasibility audit', formula='src/descriptive/audit_terrain_snow_source_feasibility.py',
            causal_role='feature source feasibility; not treatment or effect', missing_share=f'{frame[col].isna().mean():.6f}',
            notes='No source mixing, piste-to-group assignment, feature aggregation or automatic exclusion.'))
    write_csv(pd.concat([dictionary[dictionary.table.ne(Path(OUTPUT).stem)], pd.DataFrame(definitions).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')


def main():
    parent = json.loads((ROOT / 'reports/approved_profile_context_summary.json').read_text(encoding='utf-8'))
    protected = {**parent['input_sha256'], **parent['output_sha256'], **parent['protected_legacy_sha256']}
    for p, expected in protected.items():
        if sha(p) != expected:
            raise ValueError('Protected earlier output changed: ' + p)
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    collection = json.loads((ROOT / CHECKPOINT).read_text(encoding='utf-8'))
    inputs = {p: sha(p) for p in INPUTS}
    if collection.get('raw_file'):
        inputs[collection['raw_file']] = sha(collection['raw_file'])
        if inputs[collection['raw_file']] != collection['sha256']:
            raise ValueError('Source archive integrity failure')
    if (ROOT / SUMMARY).exists():
        prior = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        if prior['input_sha256'] != inputs or sha(OUTPUT) != prior['output_sha256'][OUTPUT]:
            raise ValueError('Changed stage44 inputs/outputs: preserve and review, no overwrite')
        print('Exact stage44 checkpoint reused; no requests, features, groups or estimates changed.')
        return
    history = json.loads((ROOT / INPUTS[4]).read_text(encoding='utf-8'))
    groups = pd.read_csv(ROOT / INPUTS[2]); windows = pd.read_csv(ROOT / INPUTS[3])
    frame = build_inventory(groups, windows, history, config, collection['status'])
    geometry = geometry_inventory(json.loads((ROOT / collection['raw_file']).read_bytes())) if collection['status'] == 'complete' else dict(status=collection['status'])
    write_csv(frame, ROOT / OUTPUT)
    register(frame, config, collection)
    summary = dict(date='2026-10-09', status='source_inventory_complete_features_pending_validation',
        group_count=len(frame), requested_group_winters=int(frame.requested_winter_count.sum()),
        spass_missing_group_winters=int(frame.spass_calendar_missing_winter_count.sum()),
        spass_missing_groups=int(frame.spass_calendar_missing_winter_count.gt(0).sum()),
        oshd_candidate_available_calendar_counts={str(k): int(v) for k, v in frame.oshd_candidate_calendar_winter_count.value_counts().sort_index().items()},
        requested_overlap_calendar_group_winters=int(frame.overlap_calendar_winter_count.sum()),
        recent_spass_missing_potentially_covered=int(frame.recent_missing_spass_within_oshd_calendar_count.sum()),
        geometry_inventory=geometry, targeted_prior_history_group_count=int(frame.existing_targeted_history_source_ids.ne('').sum()),
        group_piste_assignment_applied=False, snow_values_downloaded=False, feature_means_computed=False,
        snow_source_substituted=False, clustering_fitted=False, effect_estimation_run=False, automatic_exclusion_applied=False,
        input_sha256=inputs, output_sha256={OUTPUT: sha(OUTPUT)}, protected_legacy_sha256=protected)
    for p, expected in protected.items():
        if sha(p) != expected:
            raise ValueError('Protected earlier output modified: ' + p)
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith('sha256')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
