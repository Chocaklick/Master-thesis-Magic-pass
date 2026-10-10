"""Observed latest-per-tile native terrain and edition-boundary audit.

No gradient is computed across a mixed-edition Horn neighbourhood until the
researcher chooses its treatment. This is a temporary methodological gate,
not an exclusion, imputation or a silently adopted seam filter. All groups,
central elevations, exact lengths, source dates and observed coverage remain.
Dense native-cell details stay in resumable local interim CSVs, not in Git.
"""
import hashlib
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from shapely import wkt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.terrain_cell_weights_stage61 import cell_lengths, horn
from src.descriptive.summarise_terrain_orientation_stage64 import summarise_cells
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_NATIVE2M_REFERENCE_AUDIT_STAGE66'
TABLE = 'terrain_native2m_reference_audit_stage66'
CELL_TABLE = 'terrain_native2m_reference_cells_stage66'
OUTPUT = 'data_processed/' + TABLE + '.csv'
SUMMARY = 'reports/native2m_reference_stage66_summary.json'
DIR = 'data_interim/terrain_native2m_reference_cells_stage66'
QUEUE = 'config/terrain_reference_tile_sources_stage66.json'

CELL_DEFS = {
    'source_id': ('Registered reference/coverage audit source', 'identifier'),
    'station_group_id': ('Preserved station group, not municipality or independent cell unit', 'identifier'),
    'cell_centre_east_2056': ('Exact observed native2m cell centre on verified aligned grid', 'metres'),
    'cell_centre_north_2056': ('Exact observed native2m cell centre on verified aligned grid', 'metres'),
    'unique_axis_length_m': ('Exact unique mapped candidate-axis length in this native cell', 'metres'),
    'altitude_m': ('Original central native altitude; missing stays missing', 'metres'),
    'altitude_observed': ('Finite central native elevation observed without interpolation', 'boolean'),
    'centre_tile_source_id': ('Original central native raster source, or missing if absent', 'identifier'),
    'centre_reference_datetime': ('Literal central DEM edition, not assumed acquisition date', 'timestamp'),
    'horn_neighbour_source_ids': ('Distinct original sources of nine native centres, north-west to south-east window', 'identifier list'),
    'horn_neighbour_reference_dates': ('Distinct known source editions in strict3x3window', 'timestamp list'),
    'native_neighbour_values_observed_count': ('Finite original native values among nine; zero is observed coverage count', 'count'),
    'horn_complete_native_neighbourhood': ('All9native elevations observed, even when edition treatment remains pending', 'boolean'),
    'mixed_reference_neighbourhood': ('More than one literal source edition in strict3x3 neighbourhood', 'boolean'),
    'horn_calculation_status': ('Computed same-edition, missing native neighbours or awaiting mixed-edition rule', 'text'),
    'terrain_slope_degrees': ('StrictHorn3x3 only if complete observed same-edition neighbourhood; mixed-edition calculation deferred', 'degrees'),
    'terrain_aspect_degrees': ('Observed downslopeN0/E90/S180/W270; missing forflat/unobserved/unapproved seam', 'degrees'),
    'gradient_observed': ('StrictHorn gradient actually calculated; availability and pending decisions separately flagged', 'boolean'),
    'flat_terrain': ('Exactlyzero calculated slope only; missing when no approved gradient calculation', 'boolean'),
}
GROUP_DEFS = {
    'source_id': ('Registered reference/coverage audit source', 'identifier'),
    'station_group_id': ('Preserved group identifier, no municipality duplication', 'identifier'),
    'station_group_name': ('Preserved group name', 'text'),
    'group_retained': ('True for all70groups; no automatic exclusion', 'boolean'),
    'terrain_status': ('Extracted reference, pending seam rule, missing axes or unresolved scope', 'text'),
    'cell_detail_file': ('Resumable local interim native-cell CSV, original angles/provenance retained', 'relative file path'),
    'unique_mapped_axis_length_m': ('Previously approved unique candidate-axis length', 'metres'),
    'native_axis_cell_count': ('Native cells carrying exact axislength, not independent stations', 'count'),
    'reference_datetimes_on_axis': ('Literal editions under observed central cells; not acquisition dates', 'timestamp list'),
    'observed_altitude_length_m': ('Unique axislength with finite central native altitude', 'metres'),
    'missing_altitude_length_m': ('Retained axislength with unobserved central elevation', 'metres'),
    'complete_native_neighbourhood_length_m': ('Unique length with all9finite original neighbour values', 'metres'),
    'missing_native_neighbourhood_length_m': ('Retained length without9finite native neighbours', 'metres'),
    'mixed_edition_complete_neighbourhood_length_m': ('Length with9observed native values from different editions; pending method, not missing data', 'metres'),
    'mixed_edition_axis_share': ('Pending complete mixed-edition length divided by all unique mappedaxislength', 'fraction'),
    'minimum_observed_altitude_m': ('Minimum observed native altitude along candidateaxes', 'metres'),
    'maximum_observed_altitude_m': ('Maximum observed native altitude along candidateaxes, not necessarily summit', 'metres'),
    'length_weighted_observed_altitude_m': ('Sum observed centrealtitude timeslength divided by observedaltitudelength', 'metres'),
    'length_weighted_observed_slope_degrees': ('Approved observed-length slope mean only for groups without pending editionseam rule', 'degrees'),
    'orientation_coverage_share': ('Observed nonflat orientation length / all axislength, missing while a seam rule is pending', 'fraction'),
    'terrain_northness': ('Length-weighted cos(angle), approved continuous candidate, missing while seam rule pending', 'dimensionless [-1,1]'),
    'terrain_eastness': ('Length-weighted sin(angle), approved continuous candidate, missing while seam rule pending', 'dimensionless [-1,1]'),
    'orientation_resultant_concentration': ('Hypot(northness,eastness), descriptive only, missing while seam rule pending', 'dimensionless [0,1]'),
    'north_length_share': ('Observed-orientation length in approved northsector, descriptive only', 'fraction'),
    'east_length_share': ('Observed-orientation length in approved eastsector, descriptive only', 'fraction'),
    'south_length_share': ('Observed-orientation length in approved southsector, descriptive only', 'fraction'),
    'west_length_share': ('Observed-orientation length in approved westsector, descriptive only', 'fraction'),
    'current_proxy_not_verified_preentry': ('Current geometry/model remain qualified proxies, not verified preentry features', 'boolean'),
}


def neighbourhood(east, north, lookup, value):
    """Native centre lookup only, no interpolation or coordinate snapping."""
    window, sources, dates = [], set(), set()
    for dy in (2, 0, -2):
        row = []
        for dx in (-2, 0, 2):
            x, y = east + dx, north + dy
            key = (math.floor(x / 1000) * 1000, math.floor(y / 1000) * 1000)
            tile = lookup.get(key)
            if tile is None:
                row.append(np.nan)
            else:
                sources.add(tile['source_id'])
                dates.add(tile['item_reference_datetime'])
                r = int((tile['top'] - y) // 2)
                c = int((x - tile['left']) // 2)
                row.append(value(tile['source_id'], r, c))
        window.append(row)
    z = np.asarray(window, dtype=float)
    complete, mixed = bool(np.isfinite(z).all()), len(dates) > 1
    status = 'missing_native_neighbours' if not complete else 'awaiting_mixed_edition_rule' if mixed else 'computed_same_edition'
    slope, aspect = horn(z) if status == 'computed_same_edition' else (None, None)
    return z, sorted(sources), sorted(dates), mixed, status, slope, aspect


def main():
    paths = ['src/descriptive/audit_native2m_reference_stage66.py', QUEUE,
             'src/data_processing/terrain_cell_weights_stage61.py', 'src/descriptive/summarise_terrain_orientation_stage64.py',
             'data_processed/winter_profile_exact_piste_overlap_stage63.csv',
             'data_interim/winter_profile_exact_network_stage63.json',
             'reports/terrain_catalogue_extension_stage65_summary.json',
             'config/terrain_extraction_decisions_stage61.json', 'config/terrain_vintage_decisions_stage62.json',
             'config/terrain_orientation_decisions_stage64.json', 'data_interim/terrain_reference_events_stage66.json',
             'config/terrain_catalogue_dictionary_corrections_stage65.json']
    inputs = {p: sha(p) for p in paths}
    for summary in ['reports/terrain_catalogue_extension_stage65_summary.json', 'reports/native2m_terrain_pilot_stage63_summary.json']:
        old = json.loads((ROOT / summary).read_text(encoding='utf8'))
        for p, h in {**old['input_sha256'], **old['output_sha256']}.items():
            if sha(p) != h:
                raise ValueError('Frozen prior input/output changed: ' + p)
    queue = json.loads((ROOT / QUEUE).read_text(encoding='utf8'))
    lookup, by_source, headers = {}, {}, []
    for source in queue:
        metas = list((ROOT / 'data_external/source_evidence').glob(source['source_id'] + '_*.metadata.json'))
        if len(metas) != 1:
            raise ValueError('Complete finite499tile reference required before audit: ' + source['source_id'])
        meta = json.loads(metas[0].read_text(encoding='utf8'))
        if meta['url'] != source['url'] or meta['sha256'] != source['expected_sha256'] or sha(meta['raw_file']) != source['expected_sha256']:
            raise ValueError('Original/provider checksum mismatch')
        inputs[meta['raw_file']] = meta['sha256']
        with rasterio.open(ROOT / meta['raw_file']) as d:
            if d.crs.to_epsg() != 2056 or d.res != (2., 2.) or d.transform.b != 0 or d.transform.d != 0 or d.units != ('metre',) or d.count != 1:
                raise ValueError('Native2m northupEPSG2056metre headers required; no resampling/units guess')
            xkm, ykm = map(int, source['native_tile_key'].split('-'))
            if d.shape != (500, 500) or tuple(d.bounds) != (xkm * 1000, ykm * 1000, (xkm + 1) * 1000, (ykm + 1) * 1000):
                raise ValueError('Actual native tile grid differs; do not assume pilot grid')
            tile = {**source, 'raw_file': meta['raw_file'], 'left': d.bounds.left, 'top': d.bounds.top, 'nodata': d.nodata}
            key = (d.bounds.left, d.bounds.bottom)
            if key in lookup:
                raise ValueError('Duplicate latest native footprint, no mosaic precedence')
            lookup[key] = tile
            by_source[source['source_id']] = tile
            headers.append(dict(source_id=source['source_id'], shape=list(d.shape), bounds=list(d.bounds),
                                crs=str(d.crs), resolution=list(d.res), units=list(d.units), nodata=d.nodata,
                                reference_datetime=source['item_reference_datetime'], bytes=meta['size_bytes']))
    # Each original is checksum/header checked once. Cache <=48 native arrays,
    # <=96MB float64, instead of making a country-wide gigapixel mosaic.
    @lru_cache(maxsize=48)
    def array(sid):
        with rasterio.open(ROOT / by_source[sid]['raw_file']) as d:
            values = d.read(1).astype(float)
        nodata = by_source[sid]['nodata']
        if nodata is not None:
            values[values == nodata] = np.nan
        return values

    def value(sid, row, col):
        return float(array(sid)[row, col])

    groups = pd.read_csv(ROOT / paths[4])
    networks = {n['station_group_id']: n for n in json.loads((ROOT / paths[5]).read_text(encoding='utf8'))}
    (ROOT / DIR).mkdir(parents=True, exist_ok=True)
    recipe = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    records, outputs = [], {}
    for g in groups.itertuples():
        base = dict(source_id=SOURCE, station_group_id=g.station_group_id, station_group_name=g.station_group_name,
                    group_retained=True, current_proxy_not_verified_preentry=True,
                    unique_mapped_axis_length_m=g.exact_unique_mapped_axis_length_m)
        if pd.isna(g.exact_unique_mapped_axis_length_m):
            records.append({**base, 'terrain_status': 'piste_scope_unresolved' if not g.current_site_correspondence_verified else 'referenced_axes_missing'})
            continue
        token = hashlib.sha256(g.station_group_id.encode()).hexdigest()[:12]
        cell_file, checkpoint = f'{DIR}/{token}.csv', ROOT / DIR / (token + '.json')
        if checkpoint.exists():
            previous = json.loads(checkpoint.read_text(encoding='utf8'))
            if previous['recipe_sha256'] != recipe or sha(cell_file) != previous['cell_sha256']:
                raise ValueError('Per-group cache changed; use new stage rather than overwrite')
            record = previous['group_record']
        else:
            geometry = wkt.loads(networks[g.station_group_id]['exact_unique_axis_wkt'])
            weights = cell_lengths(geometry, 0, 0, 2, 2)
            rows = []
            for (r, c), length in weights.items():
                east, north = 2 * c + 1, -2 * r - 1
                z, sids, dates, mixed, status, slope, aspect = neighbourhood(east, north, lookup, value)
                tile = lookup.get((math.floor(east / 1000) * 1000, math.floor(north / 1000) * 1000))
                altitude = float(z[1, 1]) if np.isfinite(z[1, 1]) else None
                rows.append(dict(source_id=SOURCE, station_group_id=g.station_group_id,
                    cell_centre_east_2056=east, cell_centre_north_2056=north, unique_axis_length_m=length,
                    altitude_m=altitude, altitude_observed=altitude is not None,
                    centre_tile_source_id=tile['source_id'] if tile else None,
                    centre_reference_datetime=tile['item_reference_datetime'] if tile else None,
                    horn_neighbour_source_ids='|'.join(sids), horn_neighbour_reference_dates='|'.join(dates),
                    native_neighbour_values_observed_count=int(np.isfinite(z).sum()),
                    horn_complete_native_neighbourhood=bool(np.isfinite(z).all()), mixed_reference_neighbourhood=mixed,
                    horn_calculation_status=status, terrain_slope_degrees=slope, terrain_aspect_degrees=aspect,
                    gradient_observed=slope is not None, flat_terrain=(slope == 0) if slope is not None else None))
            cells = pd.DataFrame(rows).reindex(columns=CELL_DEFS)
            total = math.fsum(cells.unique_axis_length_m)
            if not math.isclose(total, g.exact_unique_mapped_axis_length_m, rel_tol=1e-12):
                raise ValueError('Native-cell weights changed preserved unique length')
            length = lambda mask: math.fsum(cells.loc[mask, 'unique_axis_length_m'])
            observed = cells.altitude_observed
            complete = cells.horn_complete_native_neighbourhood
            seam_length = length(complete & cells.mixed_reference_neighbourhood)
            record = {**base, 'terrain_status': 'awaiting_mixed_edition_rule' if seam_length else 'native2m_reference_extracted',
                'cell_detail_file': cell_file, 'native_axis_cell_count': len(cells),
                'reference_datetimes_on_axis': '|'.join(sorted(cells.centre_reference_datetime.dropna().unique())),
                'observed_altitude_length_m': length(observed), 'missing_altitude_length_m': length(~observed),
                'complete_native_neighbourhood_length_m': length(complete), 'missing_native_neighbourhood_length_m': length(~complete),
                'mixed_edition_complete_neighbourhood_length_m': seam_length, 'mixed_edition_axis_share': seam_length / total,
                'minimum_observed_altitude_m': float(cells.loc[observed, 'altitude_m'].min()) if observed.any() else None,
                'maximum_observed_altitude_m': float(cells.loc[observed, 'altitude_m'].max()) if observed.any() else None,
                'length_weighted_observed_altitude_m': float(np.average(cells.loc[observed, 'altitude_m'], weights=cells.loc[observed, 'unique_axis_length_m'])) if observed.any() else None}
            if seam_length == 0:
                orientation = summarise_cells(cells)
                record.update({k: orientation[k] for k in ('orientation_coverage_share', 'terrain_northness', 'terrain_eastness',
                    'orientation_resultant_concentration', 'north_length_share', 'east_length_share', 'south_length_share', 'west_length_share')})
                mask = cells.gradient_observed
                record['length_weighted_observed_slope_degrees'] = float(np.average(cells.loc[mask, 'terrain_slope_degrees'], weights=cells.loc[mask, 'unique_axis_length_m'])) if mask.any() else None
            write_csv(cells, ROOT / cell_file)
            checkpoint.write_text(json.dumps(dict(recipe_sha256=recipe, cell_sha256=sha(cell_file), group_record=record), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        records.append(record)
        outputs[cell_file] = sha(cell_file)
        outputs[checkpoint.relative_to(ROOT).as_posix()] = sha(checkpoint.relative_to(ROOT).as_posix())
        print(g.station_group_name, record['terrain_status'], f"mixed-edition length {record['mixed_edition_complete_neighbourhood_length_m']:.6f}m", flush=True)
    frame = pd.DataFrame(records).reindex(columns=GROUP_DEFS)
    pending = frame[frame.terrain_status.eq('awaiting_mixed_edition_rule')]
    state = dict(date='2026-10-10', input_sha256=inputs, header_checks=headers,
                 all_groups_retained=len(frame), original_latest_tiles_verified=len(queue),
                 latest_tile_total_bytes=sum(h['bytes'] for h in headers), native_axis_cell_rows=int(frame.native_axis_cell_count.sum()),
                 terrain_status_counts=frame.terrain_status.value_counts().to_dict(),
                 pending_seam_groups=pending[['station_group_id', 'station_group_name', 'mixed_edition_complete_neighbourhood_length_m', 'mixed_edition_axis_share']].to_dict('records'),
                 all_missing_lengths_retained=True, no_mixed_edition_gradient_rule_silently_selected=True,
                 no_interpolation_group_exclusion_or_model_fit=True, source_attribution='Office fédéral de topographie swisstopo')
    target = ROOT / SUMMARY
    if target.exists():
        old = json.loads(target.read_text(encoding='utf8'))
        if old['input_sha256'] != inputs or any(sha(p) != h for p, h in old['output_sha256'].items()):
            raise ValueError('Frozen reference audit differs; use new stage')
    else:
        write_csv(frame, ROOT / OUTPUT)
        state['output_sha256'] = {**outputs, OUTPUT: sha(OUTPUT)}
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    records = []
    for s in queue:
        if s['source_id'] in set(master.source_id):
            continue
        meta_file = list((ROOT / 'data_external/source_evidence').glob(s['source_id'] + '_*.metadata.json'))[0]
        m = json.loads(meta_file.read_text(encoding='utf8'))
        records.append(dict(source_id=m['source_id'], variable_name='native2m_observed_reference_elevation',
            variable_description='Original latest-per-native-tile2mmetre reference; actual header/grid/SHA verified',
            source_organisation=m['organisation'], source_page_url=m['url'], retrieval_date=m['retrieval_date'],
            original_file_name=Path(m['raw_file']).name, local_raw_file=m['raw_file'], processed_file=OUTPUT,
            geographic_level='Verified nativeEPSG2056tile, retained station-group axes', temporal_resolution='Literal reference ' + m['item_reference_datetime'],
            license='Official swisstopo OGD terms; mandatory source attribution; literal catalogue marker preserved',
            retrieval_method='Finite serial public robots/TLS GET; official SHA and native headers checked',
            transformation_applied='Original intact; observed centres/strictHorn onlysameedition, exactcelllengths, seamcoverage deferred',
            quality_notes='Not actual acquisition/preentry date or exhaustive skiing; no nodata interpolation or editionseam adjustment',
            notes='SHA256=' + m['sha256'] + '; Office fédéral de topographie swisstopo'))
    if SOURCE not in set(master.source_id):
        records.append(dict(source_id=SOURCE, variable_name='native2m_reference_profiles_and_observed_seam_coverage',
            variable_description='All70groups retained, nativecentral altitudes and same-editionHorn summaries; exactmixededition neighbourhood coverage for validation',
            source_organisation='Thesis nativecell audit of swisstopo/OSM', retrieval_date='2026-10-10', processed_file=OUTPUT + '|' + DIR,
            geographic_level='Retained station groups/native cells, not municipality effects', temporal_resolution='Latestperverifiednative tile, all literal dates retained',
            license='swisstopo OGD attribution; OSM ODbL', retrieval_method='Immutable sourceSHA/headers; approvedexact2mcellweights/Horn',
            transformation_applied='Observed-length altitude and approvedorientation summaries when no pendingedition seam; no rule selected for mixedneighbourhoods',
            quality_notes='Unknowns/pendingmethod never zero/exclusion; not verified preentry, finalmetric certification or fitted clustering/effects', notes=SUMMARY))
    if records:
        write_csv(pd.concat([master, pd.DataFrame(records).reindex(columns=SOURCE_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    records = []
    for table, defs, observed_frame in [(TABLE, GROUP_DEFS, frame), (CELL_TABLE, CELL_DEFS, None)]:
        for col, (description, unit) in defs.items():
            if ((dictionary.table == table) & (dictionary.variable == col)).any():
                continue
            declared_type = ('boolean (nullable)' if col == 'flat_terrain' else 'bool' if unit == 'boolean' else
                             'int64' if unit == 'count' else 'float64' if unit in ('metres', 'degrees') else 'object')
            role = ('Approved continuous candidate; temporal/seam validity still required' if col in ('terrain_northness', 'terrain_eastness') else
                    'Descriptive only; not automatically included in models' if col in ('orientation_resultant_concentration', 'north_length_share', 'east_length_share', 'south_length_share', 'west_length_share') else
                    'Qualified source/coverage/current terrain diagnostic; no fitted causal model')
            records.append(dict(variable=col, table=table, description=description, unit=unit,
                data_type=str(observed_frame[col].dtype) if observed_frame is not None else declared_type,
                geographic_level='station group/nativecell, not independent resort observations', temporal_level='Currentqualifiedgeometry/literalDEMreference',
                source_id=SOURCE, raw_or_derived='Derived observed/provenance audit', formula=description,
                causal_role=role,
                missing_share=f'{observed_frame[col].isna().mean():.6f}' if observed_frame is not None else '',
                notes='DataInterim cellCSV files preserved/hashes; unknown/pendingnotzero; no automaticexclusion/newfittedmodel'))
    if records:
        write_csv(pd.concat([dictionary, pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_dictionary.csv')
    print(json.dumps({k: v for k, v in state.items() if k not in ('input_sha256', 'output_sha256', 'header_checks')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
