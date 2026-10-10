"""Complete catalogue and latest-per-tile availability audit, not DEM features."""
import json
import re
import sys
from pathlib import Path

import pandas as pd
from shapely.geometry import LineString, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_terrain_extension_stage65 import literal_next
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.audit_terrain_catalogue_stage61 import DEFS as PILOT_DEFS
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_TERRAIN_CATALOGUE_EXTENSION_STAGE65'
TABLES = ['terrain_group_native2m_asset_inventory_stage65', 'terrain_group_catalogue_coverage_stage65']
OUTPUTS = ['data_processed/' + t + '.csv' for t in TABLES]
SUMMARY = 'reports/terrain_catalogue_extension_stage65_summary.json'
ASSET_DEFS = {**PILOT_DEFS,
    'native_tile_key': ('Literal native tile key from provider asset ID, not geographic assignment', 'identifier'),
    'catalogue_page_source_id': ('Registered archived original page containing this asset', 'identifier'),
    'latest_reference_for_native_tile': ('Latest provider reference date for this group/native tile; all older editions retained', 'boolean'),
    'cached_original_tile_source_id': ('Previously downloaded original matching literal URL and official SHA, if available', 'identifier'),
}
GROUP_DEFS = {
    'source_id': ('Registered catalogue extension diagnostic source', 'identifier'),
    'station_group_id': ('Preserved station-group identifier, not municipality', 'identifier'),
    'station_group_name': ('Preserved group name', 'text'),
    'group_retained': ('True for all70groups, missing catalogue is not exclusion', 'boolean'),
    'catalogue_status': ('Complete catalogue, unresolved piste scope or missing referenced axes', 'text'),
    'unique_mapped_axis_length_m': ('Previously computed exact candidate-axis length, unchanged', 'metres'),
    'archived_page_count': ('Original complete pages; StLuc archive reused', 'count'),
    'catalogue_page_source_ids': ('Archived original source IDs in literal pagination chain', 'identifier list'),
    'all_native2m_asset_count': ('All native2m approved-CRS assets across editions, not downloaded raster count', 'count'),
    'latest_native_tile_count': ('Metadata assets selected by approved latest-per-native-tile rule', 'count'),
    'latest_axis_intersecting_tile_count': ('Selected catalogue footprints intersecting original axes; not exact native cell coverage', 'count'),
    'latest_axis_reference_dates': ('Distinct literal reference dates on selected axis-intersecting footprints', 'timestamp list'),
    'latest_axis_mixed_reference_dates': ('Axis-intersecting selected tiles have several reference dates; no gradient seam convention yet', 'boolean'),
    'actual_raster_coverage_verified': ('False: metadata not observed native raster coverage', 'boolean'),
}


def archive(sid, inputs):
    paths = list((ROOT / 'data_external/source_evidence').glob(sid + '_*.metadata.json'))
    if len(paths) != 1:
        raise ValueError('Require one completed archived page: ' + sid)
    meta = json.loads(paths[0].read_text(encoding='utf8'))
    if meta['source_id'] != sid or sha(meta['raw_file']) != meta['sha256']:
        raise ValueError('Source ID/SHA mismatch: ' + sid)
    inputs[meta['raw_file']] = meta['sha256']
    relative = paths[0].relative_to(ROOT).as_posix()
    inputs[relative] = sha(relative)
    return meta, json.loads((ROOT / meta['raw_file']).read_bytes())


def parse_assets(payload, gid, geometry, sid, cache):
    rows = []
    for item in payload['features']:
        if item['collection'] != 'ch.swisstopo.swissalti3d':
            raise ValueError('Wrong DEM collection')
        for aid, asset in item['assets'].items():
            if not asset.get('type', '').startswith('image/tiff') or asset.get('gsd') != 2.0 or asset.get('proj:epsg') != 2056:
                continue
            checksum = asset.get('file:checksum', '')
            match = re.fullmatch(r'swissalti3d_\d{4}_(\d+-\d+)_2_2056_5728\.tif', aid)
            if not re.fullmatch(r'1220[0-9a-fA-F]{64}', checksum) or match is None:
                raise ValueError('Unknown official checksum or native tile identifier; review, do not guess')
            url, digest = asset['href'], checksum[4:].lower()
            known = cache.get(url)
            if known and known['expected_sha256'] != digest:
                raise ValueError('Previously collected literal asset has a different official SHA')
            date = item['properties'].get('datetime')
            if date is None:
                raise ValueError('Unknown reference date: latest edition cannot be inferred')
            rows.append(dict(source_id=SOURCE, station_group_id=gid, item_id=item['id'],
                item_reference_datetime=date, item_created_datetime=item['properties'].get('created'), item_updated_datetime=item['properties'].get('updated'),
                asset_id=aid, asset_url=url, asset_created_datetime=asset.get('created'), asset_updated_datetime=asset.get('updated'),
                asset_grid_resolution_m=asset['gsd'], asset_horizontal_epsg=asset['proj:epsg'], asset_checksum_multihash=checksum,
                asset_sha256=digest, intersects_current_axis_footprint=shape(item['geometry']).intersects(geometry),
                tile_vintage_selection_applied=True, native_tile_key=match.group(1), catalogue_page_source_id=sid,
                latest_reference_for_native_tile=False, cached_original_tile_source_id=known['source_id'] if known else None))
    return rows


def main():
    paths = ['src/descriptive/audit_terrain_extension_stage65.py', 'src/data_collection/prepare_terrain_extension_stage65.py',
             'src/data_collection/collect_terrain_extension_stage65.py', 'config/terrain_group_catalogue_sources_stage65.json',
             'data_interim/terrain_extension_plan_stage65.json', 'data_interim/terrain_catalogue_queue_stage65.json',
             'data_interim/terrain_catalogue_events_stage65.json', 'config/terrain_tile_sources_stage62.json',
             'data_processed/winter_profile_exact_piste_overlap_stage63.csv',
             'data_processed/winter_profile_verified_piste_member_qa_stage60.csv',
             'config/terrain_vintage_decisions_stage62.json', 'reports/terrain_orientation_stage64_summary.json']
    inputs = {p: sha(p) for p in paths}
    plan = json.loads((ROOT / paths[4]).read_text(encoding='utf8'))
    previous = json.loads((ROOT / paths[-1]).read_text(encoding='utf8'))
    for p, h in {**plan['input_sha256'], **previous['input_sha256'], **previous['output_sha256']}.items():
        if sha(p) != h:
            raise ValueError('Frozen previous data/plan changed: ' + p)
    roots = json.loads((ROOT / paths[3]).read_text(encoding='utf8'))
    roots_by_group = {s['station_group_id']: s for s in roots}
    cache = {s['url']: s for s in json.loads((ROOT / paths[7]).read_text(encoding='utf8'))}
    groups = pd.read_csv(ROOT / paths[8])
    members = pd.read_csv(ROOT / paths[9], dtype=str, keep_default_na=False)
    index, _, _ = originals()
    all_rows, coverage, metadata = [], [], {}
    for g in groups.itertuples():
        base = dict(source_id=SOURCE, station_group_id=g.station_group_id, station_group_name=g.station_group_name,
                    group_retained=True, unique_mapped_axis_length_m=g.exact_unique_mapped_axis_length_m,
                    actual_raster_coverage_verified=False)
        if pd.isna(g.exact_unique_mapped_axis_length_m):
            coverage.append({**base, 'catalogue_status': 'piste_scope_unresolved' if not g.current_site_correspondence_verified else 'referenced_axes_missing'})
            continue
        selected = members[members.station_group_id.eq(g.station_group_id) & members.candidate_role.eq('way_axis_candidate')]
        geometry = unary_union([LineString([(p['lon'], p['lat']) for p in index[(r.osm_type, int(r.osm_id))]['geometry']]) for r in selected.itertuples()])
        if g.station_group_id == 'MP_GROUP_RESORT__st_luc_chandolin':
            sid = 'SWISSTOPO_ALTI3D_STLUC_ITEMS_STAGE61'
            meta, payload = archive(sid, inputs)
            if literal_next(payload) is not None:
                raise ValueError('Completed pilot unexpectedly has pagination')
            payloads = [(sid, payload)]
            metadata[sid] = meta
        else:
            root = roots_by_group[g.station_group_id]
            source, payloads, seen_urls = root, [], set()
            for page in range(1, 31):
                meta, payload = archive(source['source_id'], inputs)
                if meta['url'] != source['url'] or source['url'] in seen_urls:
                    raise ValueError('Broken or cyclic literal pagination chain')
                seen_urls.add(source['url'])
                metadata[meta['source_id']] = meta
                payloads.append((meta['source_id'], payload))
                next_url = literal_next(payload)
                if next_url is None:
                    break
                source = {**root, 'source_id': root['source_id'].removesuffix('P001') + f'P{page + 1:03}', 'url': next_url}
            else:
                raise ValueError('Unfinished pagination; never infer missing terrain')
        rows = [r for sid, payload in payloads for r in parse_assets(payload, g.station_group_id, geometry, sid, cache)]
        frame = pd.DataFrame(rows)
        if frame.empty or frame.asset_id.duplicated().any() or frame.asset_url.duplicated().any():
            raise ValueError('Empty or duplicated group catalogue needs review')
        latest = frame.groupby('native_tile_key').item_reference_datetime.max()
        frame['latest_reference_for_native_tile'] = frame.item_reference_datetime.eq(frame.native_tile_key.map(latest))
        latest_rows = frame[frame.latest_reference_for_native_tile]
        if latest_rows.native_tile_key.duplicated().any():
            raise ValueError('Latest edition tie; no arbitrary asset selection')
        dates = sorted(latest_rows.loc[latest_rows.intersects_current_axis_footprint, 'item_reference_datetime'].unique())
        coverage.append({**base, 'catalogue_status': 'complete_original_pages', 'archived_page_count': len(payloads),
                         'catalogue_page_source_ids': '|'.join(sid for sid, _ in payloads), 'all_native2m_asset_count': len(frame),
                         'latest_native_tile_count': len(latest_rows), 'latest_axis_intersecting_tile_count': int(latest_rows.intersects_current_axis_footprint.sum()),
                         'latest_axis_reference_dates': '|'.join(dates), 'latest_axis_mixed_reference_dates': len(dates) > 1})
        all_rows.extend(frame.to_dict('records'))
    assets = pd.DataFrame(all_rows).reindex(columns=ASSET_DEFS)
    group_frame = pd.DataFrame(coverage).reindex(columns=GROUP_DEFS)
    for url, part in assets.groupby('asset_url'):
        for col in ('asset_sha256', 'native_tile_key', 'item_reference_datetime', 'asset_grid_resolution_m', 'asset_horizontal_epsg'):
            if part[col].nunique() != 1:
                raise ValueError('Conflicting current catalogue records for shared literal asset: ' + url)
    selected_assets = assets[assets.latest_reference_for_native_tile]
    mixed = group_frame[group_frame.latest_axis_mixed_reference_dates.eq(True)]
    state = dict(date='2026-10-10', input_sha256=inputs, all_groups_retained=len(group_frame),
                 complete_catalogue_group_count=int(group_frame.catalogue_status.eq('complete_original_pages').sum()),
                 new_archived_page_count=len(metadata) - 1, all_group_asset_rows=len(assets),
                 distinct_all_edition_assets=assets.asset_url.nunique(), distinct_latest_assets=selected_assets.asset_url.nunique(),
                 already_cached_latest_assets=selected_assets.loc[selected_assets.cached_original_tile_source_id.notna(), 'asset_url'].nunique(),
                 mixed_latest_axis_edition_groups=mixed[['station_group_id', 'station_group_name', 'latest_axis_reference_dates']].to_dict('records'),
                 latest_reference_dates=sorted(selected_assets.item_reference_datetime.unique()),
                 no_new_raster_values_or_profile_fit=True, metadata_not_raster_coverage=True,
                 source_attribution='Office fédéral de topographie swisstopo', no_group_exclusion=True)
    target = ROOT / SUMMARY
    if target.exists():
        old = json.loads(target.read_text(encoding='utf8'))
        if old['input_sha256'] != inputs or any(sha(p) != h for p, h in old['output_sha256'].items()):
            raise ValueError('Frozen extension differs; use new stage')
    else:
        for frame, path in zip((assets, group_frame), OUTPUTS):
            write_csv(frame, ROOT / path)
        state['output_sha256'] = {p: sha(p) for p in OUTPUTS}
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    records = [dict(source_id=sid, variable_name='official_native2m_catalogue_metadata', variable_description=m['purpose'],
                    source_organisation=m['organisation'], source_page_url=m['url'], retrieval_date=m['retrieval_date'],
                    original_file_name=Path(m['raw_file']).name, local_raw_file=m['raw_file'], processed_file='|'.join(OUTPUTS),
                    geographic_level='Literal query bounding box of preserved candidate axes, not municipal basin',
                    temporal_resolution='Current catalogue, all provider reference/creation/update dates retained',
                    license='Official swisstopo OGD conditions and attribution; literal proprietary collection marker preserved separately',
                    retrieval_method='Finite public robots/TLS GET, literal pagination, original SHA/checkpoint',
                    transformation_applied='Metadata native2m approvedCRS assets retained across editions; latestpernative tile selected',
                    quality_notes='Not actual acquisition date, observed raster coverage, exhaustive domain or verified preentry',
                    notes='SHA256=' + m['sha256'] + '; stable group=' + m.get('station_group_id', 'MP_GROUP_RESORT__st_luc_chandolin'))
               for sid, m in metadata.items() if sid not in set(master.source_id)]
    if SOURCE not in set(master.source_id):
        records.append(dict(source_id=SOURCE, variable_name='terrain_catalogue_extension_latest_tile_availability',
                            variable_description='All70retainedgroups; complete dated catalogues for40mapped-axis groups and latestpernative tile audit',
                            source_organisation='Thesis derived audit of official swisstopo metadata', retrieval_date='2026-10-10',
                            processed_file='|'.join(OUTPUTS), geographic_level='Preserved station groups and literal native tiles',
                            temporal_resolution='Current catalogue; edition dates retained, not actual acquisition/preentry',
                            license='Official swisstopo OGD attribution; OSM ODbL', retrieval_method='Offline archived JSON/sourceSHA/literalpagination',
                            transformation_applied='Approved latestpernative tile metadata selection; axisintersection and mixededition diagnostic',
                            quality_notes='No raster elevation/Horn/feature values or interpolation/group exclusion', notes=SUMMARY))
    if records:
        write_csv(pd.concat([master, pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    records = []
    for table, frame, defs in zip(TABLES, (assets, group_frame), (ASSET_DEFS, GROUP_DEFS)):
        for col, (description, unit) in defs.items():
            if ((dictionary.table == table) & (dictionary.variable == col)).any():
                continue
            records.append(dict(variable=col, table=table, description=description, unit=unit, data_type=str(frame[col].dtype),
                                geographic_level='Station group/native metadata asset', temporal_level='Literal provider reference/current metadata', source_id=SOURCE,
                                raw_or_derived='Metadata/availability diagnostic, not observed terrain', formula=description,
                                causal_role='Source/coverage audit, not final causal profile', missing_share=f'{frame[col].isna().mean():.6f}',
                                notes='All70groups retained; no raster data fabrication or profile/effect fit; official page lineage'))
    if records:
        write_csv(pd.concat([dictionary, pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_dictionary.csv')
    print(json.dumps({k: v for k, v in state.items() if k not in ('input_sha256', 'output_sha256')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
