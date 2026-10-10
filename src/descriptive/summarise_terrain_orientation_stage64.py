"""Approved terrain orientation summaries; no fitted classes or causal effects.

One row per retained group for the latest pilot reference. Separate edition
comparison, without treating two editions as independent groups. No source
angles, historical results, municipal outcomes or lift clusters are rewritten.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_TERRAIN_ORIENTATION_STAGE64'
TABLES = ['terrain_orientation_reference_stage64', 'terrain_orientation_edition_comparison_stage64']
OUTPUTS = [f'data_processed/{table}.csv' for table in TABLES]
SUMMARY = 'reports/terrain_orientation_stage64_summary.json'
DECISION = 'config/terrain_orientation_decisions_stage64.json'
PILOT = 'reports/native2m_terrain_pilot_stage63_summary.json'
CELLS = 'data_processed/terrain_native2m_pilot_cells_stage63.csv'
GROUPS = 'data_processed/winter_profile_exact_piste_overlap_stage63.csv'

DEFS = {
    'source_id': ('Registered derived source identifier', 'identifier'),
    'station_group_id': ('Preserved station-group identifier, not municipality', 'identifier'),
    'station_group_name': ('Preserved group name', 'text'),
    'parent_station_group_ids': ('Preserved original group lineage', 'identifier list'),
    'terrain_summary_status': ('Extracted reference or explicit missing-scope/extraction status', 'text'),
    'edition_reference_datetime': ('Literal DEM reference edition; not actual acquisition or preentry date', 'timestamp'),
    'edition_role': ('Latest reference or separate comparison; never independent groups for modelling', 'text'),
    'unique_mapped_axis_length_m': ('Unique mapped candidate-axis length, not official exhaustive piste kilometres', 'metres'),
    'observed_orientation_length_m': ('Unique length with observed nonflat terrain angle; denominator of orientation summaries', 'metres'),
    'flat_observed_length_m': ('Observed gradient with exactly zero slope; no directional assignment', 'metres'),
    'missing_gradient_length_m': ('Retained length without complete observed Horn neighbourhood', 'metres'),
    'orientation_coverage_share': ('Observed nonflat angle length divided by all mapped unique-axis length', 'fraction'),
    'terrain_northness': ('Length-weighted cos(downslope azimuth): positive north, negative south', 'dimensionless [-1,1]'),
    'terrain_eastness': ('Length-weighted sin(downslope azimuth): positive east, negative west', 'dimensionless [-1,1]'),
    'orientation_resultant_concentration': ('Hypot of northness and eastness; descriptive only, cannot diagnose multimodality', 'dimensionless [0,1]'),
    'north_length_share': ('Observed angle length in [315,360) or [0,45), divided by observed orientation length; descriptive only', 'fraction'),
    'east_length_share': ('Observed angle length in [45,135), divided by observed orientation length; descriptive only', 'fraction'),
    'south_length_share': ('Observed angle length in [135,225), divided by observed orientation length; descriptive only', 'fraction'),
    'west_length_share': ('Observed angle length in [225,315), divided by observed orientation length; descriptive only', 'fraction'),
    'group_retained': ('True for all 70 groups; missing profile never an automatic exclusion', 'boolean'),
    'current_proxy_not_verified_preentry': ('Current mapped geometry/DEM are qualified proxies, not verified preentry measurements', 'boolean'),
}
FORMULAS = {
    'terrain_northness': 'sum(length_i*cos(angle_i*pi/180))/sum(observed_nonflat_length_i)',
    'terrain_eastness': 'sum(length_i*sin(angle_i*pi/180))/sum(observed_nonflat_length_i)',
    'orientation_resultant_concentration': 'hypot(terrain_northness,terrain_eastness)',
    'orientation_coverage_share': 'observed_orientation_length_m/unique_mapped_axis_length_m',
}


def summarise_cells(cells):
    """Finite positive exact weights; no invented direction for flat/missing cells."""
    lengths = cells.unique_axis_length_m.to_numpy(dtype=float)
    angles = cells.terrain_aspect_degrees.to_numpy(dtype=float)
    slopes = cells.terrain_slope_degrees.to_numpy(dtype=float)
    if not np.isfinite(lengths).all() or (lengths <= 0).any():
        raise ValueError('Require finite positive unique cell lengths')
    observed = cells.gradient_observed.to_numpy(dtype=bool)
    if not np.array_equal(observed, np.isfinite(slopes)) or (slopes[observed] < 0).any() or (slopes[observed] > 90).any():
        raise ValueError('Invalid gradient availability or slope')
    known = np.isfinite(angles)
    flat = observed & (slopes == 0)
    if not np.array_equal(known, observed & ~flat) or (angles[known] < 0).any() or (angles[known] >= 360).any():
        raise ValueError('Observed nonflat angles required; do not invent missing/flat orientation')
    if not np.array_equal(cells.flat_terrain.eq(True).to_numpy(), flat) or cells.loc[~observed, 'flat_terrain'].notna().any():
        raise ValueError('Flat-status source inconsistent')
    total = math.fsum(lengths)
    denominator = math.fsum(lengths[known])
    result = dict(unique_mapped_axis_length_m=total, observed_orientation_length_m=denominator,
                  flat_observed_length_m=math.fsum(lengths[flat]), missing_gradient_length_m=math.fsum(lengths[~observed]),
                  orientation_coverage_share=denominator / total if total else None)
    metrics = ['terrain_northness', 'terrain_eastness', 'orientation_resultant_concentration',
               'north_length_share', 'east_length_share', 'south_length_share', 'west_length_share']
    result.update({name: None for name in metrics})
    if denominator:
        north = math.fsum(w * math.cos(math.radians(a)) for w, a in zip(lengths[known], angles[known])) / denominator
        east = math.fsum(w * math.sin(math.radians(a)) for w, a in zip(lengths[known], angles[known])) / denominator
        result.update(terrain_northness=north, terrain_eastness=east, orientation_resultant_concentration=math.hypot(north, east))
        # Approved half-open sectors; angular boundaries belong to exactly one sector.
        sectors = ((angles >= 315) | (angles < 45), (angles >= 45) & (angles < 135),
                   (angles >= 135) & (angles < 225), (angles >= 225) & (angles < 315))
        for direction, mask in zip(('north', 'east', 'south', 'west'), sectors):
            result[direction + '_length_share'] = math.fsum(lengths[known & mask]) / denominator
        if not math.isclose(sum(result[d + '_length_share'] for d in ('north', 'east', 'south', 'west')), 1, abs_tol=1e-12):
            raise ValueError('Cardinal partition does not reconcile')
        if math.hypot(north, east) > 1 + 1e-12:
            raise ValueError('Invalid resultant; no clipping or fabricated correction')
    if not math.isclose(denominator + result['flat_observed_length_m'] + result['missing_gradient_length_m'], total, rel_tol=1e-12):
        raise ValueError('Coverage lengths do not reconcile')
    return result


def main():
    paths = [DECISION, PILOT, CELLS, GROUPS, 'src/descriptive/summarise_terrain_orientation_stage64.py']
    inputs = {p: sha(p) for p in paths}
    pilot = json.loads((ROOT / PILOT).read_text(encoding='utf8'))
    for p, h in {**pilot['input_sha256'], **pilot['output_sha256']}.items():
        if sha(p) != h:
            raise ValueError('Frozen pilot changed: ' + p)
    decision = json.loads((ROOT / DECISION).read_text(encoding='utf8'))
    if decision['continuous_model_feature_candidates'] != ['terrain_northness', 'terrain_eastness'] or decision['dominant_direction_imposed']:
        raise ValueError('Unexpected authorised orientation policy')
    groups = pd.read_csv(ROOT / GROUPS)
    cells = pd.read_csv(ROOT / CELLS)
    if len(groups) != 70 or groups.station_group_id.duplicated().any() or not groups.group_retained.all():
        raise ValueError('Retain all 70 groups')
    if cells.duplicated(['station_group_id', 'edition_reference_datetime', 'cell_row', 'cell_col']).any():
        raise ValueError('Duplicated cell weights')
    if not set(cells.station_group_id).issubset(set(groups.station_group_id)):
        raise ValueError('Cell group missing from preserved universe')
    latest = cells.groupby('station_group_id').edition_reference_datetime.max().to_dict()
    reference, comparison = [], []
    for g in groups.itertuples():
        base = dict(source_id=SOURCE, station_group_id=g.station_group_id, station_group_name=g.station_group_name,
                    parent_station_group_ids=g.parent_station_group_ids, group_retained=True,
                    current_proxy_not_verified_preentry=True)
        parts = cells[cells.station_group_id.eq(g.station_group_id)]
        if len(parts):
            for edition, part in parts.groupby('edition_reference_datetime', sort=True):
                row = {**base, **summarise_cells(part), 'edition_reference_datetime': edition,
                       'edition_role': 'latest_reference' if edition == latest[g.station_group_id] else 'comparison_only',
                       'terrain_summary_status': 'native2m_pilot_extracted'}
                if not math.isclose(row['unique_mapped_axis_length_m'], g.exact_unique_mapped_axis_length_m, rel_tol=1e-12):
                    raise ValueError('Cell weights differ from unique preserved network')
                comparison.append(row)
                if row['edition_role'] == 'latest_reference':
                    reference.append(row)
        else:
            status = ('piste_scope_unresolved' if not g.current_site_correspondence_verified else
                      'referenced_axes_missing' if pd.isna(g.exact_unique_mapped_axis_length_m) else 'terrain_not_yet_extracted')
            reference.append({**base, 'terrain_summary_status': status, 'unique_mapped_axis_length_m': g.exact_unique_mapped_axis_length_m})
    frames = [pd.DataFrame(rows).reindex(columns=DEFS) for rows in (reference, comparison)]
    state = dict(date='2026-10-10', input_sha256=inputs, all_groups_retained=len(reference),
                 extracted_reference_group_count=len(latest), comparison_rows=len(comparison),
                 reference_status_counts=frames[0].terrain_summary_status.value_counts().to_dict(),
                 continuous_model_feature_candidates=decision['continuous_model_feature_candidates'],
                 descriptive_only_features=decision['descriptive_only_not_automatic_model_features'],
                 no_imputation_exclusion_dominant_direction_or_model_fit=True, reference_and_comparison=comparison)
    target = ROOT / SUMMARY
    if target.exists():
        previous = json.loads(target.read_text(encoding='utf8'))
        if previous['input_sha256'] != inputs or any(sha(p) != h for p, h in previous['output_sha256'].items()):
            raise ValueError('Frozen orientation stage changed; use new namespace')
    else:
        for frame, path in zip(frames, OUTPUTS):
            write_csv(frame, ROOT / path)
        state['output_sha256'] = {p: sha(p) for p in OUTPUTS}
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    if master.source_id.duplicated().any():
        raise ValueError('Duplicate source keys')
    if SOURCE not in set(master.source_id):
        source = dict(source_id=SOURCE, variable_name='approved_group_terrain_orientation',
                      variable_description='Length-weighted northness/eastness plus strictly descriptive concentration/cardinal shares',
                      source_organisation='Thesis derived analysis of swisstopo and OpenStreetMap', retrieval_date='2026-10-10',
                      processed_file='|'.join(OUTPUTS), geographic_level='70 retained station groups; one extracted pilot',
                      temporal_resolution='Current mapped axes; literal 2019/2024 DEM editions; latest pilot reference 2024',
                      units='Dimensionless components and fractions; metres for coverage', license='OSM ODbL; swisstopo OGD attribution retained',
                      retrieval_method='Existing frozen Stage63 cells only; no new request or source rewrite',
                      transformation_applied='Exact cell-length weighted cos/sin; resultant concentration; approved half-open cardinal sectors',
                      quality_notes='Not verified preentry or exhaustive pistes; missing profiles retained; concentration not independent feature',
                      notes='Parent DERIVED_NATIVE2M_TERRAIN_PILOT_STAGE63; researcher replies in ' + DECISION + '; original attribution Office fédéral de topographie swisstopo')
        write_csv(pd.concat([master, pd.DataFrame([source]).reindex(columns=SOURCE_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    if dictionary.duplicated(['table', 'variable']).any():
        raise ValueError('Duplicate dictionary keys')
    records = []
    for table, frame in zip(TABLES, frames):
        for col, (description, unit) in DEFS.items():
            if ((dictionary.table == table) & (dictionary.variable == col)).any():
                continue
            role = ('Approved continuous candidate; historical/coverage validity still required before fitting' if col in decision['continuous_model_feature_candidates'] else
                    'Descriptive only; not automatically included in models' if col in decision['descriptive_only_not_automatic_model_features'] else 'Provenance or coverage')
            records.append(dict(variable=col, table=table, description=description, unit=unit, data_type=str(frame[col].dtype),
                                geographic_level='station group, not municipality or independent raster cells', temporal_level='DEM reference edition/current mapped proxy',
                                source_id=SOURCE, raw_or_derived='derived', formula=FORMULAS.get(col, description), causal_role=role,
                                missing_share=f'{frame[col].isna().mean():.6f}', notes='Missing is not zero; angles/flat/missing length preserved; no fitted clustering or effect model'))
    if records:
        write_csv(pd.concat([dictionary, pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_dictionary.csv')
    print(json.dumps({k: v for k, v in state.items() if k not in ('input_sha256', 'output_sha256')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
