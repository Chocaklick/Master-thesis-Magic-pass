"""Apply approved edition-seam missingness in a new, resumable group summary.

Original Stage66 cells remain intact: their temporarily deferred seam gradients
are now the researcher-approved missing gradients, not missing source altitudes.
All groups and lengths remain; no additional geographic or coverage cutoff.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.audit_native2m_reference_stage66 import GROUP_DEFS
from src.descriptive.summarise_terrain_orientation_stage64 import summarise_cells, FORMULAS
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_TERRAIN_REFERENCE_STAGE67'
TABLE = 'terrain_reference_profiles_stage67'
OUTPUT = 'data_processed/' + TABLE + '.csv'
SUMMARY = 'reports/terrain_reference_profiles_stage67_summary.json'
DECISION = 'config/terrain_seam_decision_stage67.json'
AUDIT = 'reports/native2m_reference_stage66_summary.json'
PRESERVATION = 'reports/piste_preservation_stage66_summary.json'
PARENT = 'data_processed/terrain_native2m_reference_audit_stage66.csv'
NETWORK = 'data_processed/winter_profile_exact_piste_overlap_stage63.csv'
DEFS = dict(GROUP_DEFS)
DEFS.update({
    'terrain_status': ('Extracted full/partial gradient reference, unresolved scope or missing referenced axes; no pending seam rule', 'text'),
    'mixed_edition_complete_neighbourhood_length_m': ('Length with nine observed elevations from different editions; gradient deliberately missing by approved rule, altitude retained', 'metres'),
    'mixed_edition_axis_share': ('Approved missing-seam gradient length divided by all unique mapped axislength', 'fraction'),
    'length_weighted_observed_slope_degrees': ('Sum observed slope times celllength divided by observed gradient length; no seam adjustment', 'degrees'),
    'orientation_coverage_share': ('Observed nonflat orientation length divided by all unique mapped axislength', 'fraction'),
    'terrain_northness': ('Length-weighted cos(azimuth) over observed nonflat lengths; positive north', 'dimensionless [-1,1]'),
    'terrain_eastness': ('Length-weighted sin(azimuth) over observed nonflat lengths; positive east', 'dimensionless [-1,1]'),
    'orientation_resultant_concentration': ('Hypot(northness,eastness), descriptive only; cannot diagnose multimodality', 'dimensionless [0,1]'),
    'parent_station_group_ids': ('Preserved premerge group identifiers, not duplicated analysis units', 'identifier list'),
    'observed_gradient_length_m': ('Unique length with actually observed approved Horn gradient, including exactly flat terrain', 'metres'),
    'missing_gradient_length_m': ('Unobserved gradient length: approved mixed-edition seams plus incomplete native neighbourhoods', 'metres'),
    'observed_orientation_length_m': ('Observed nonflat length; denominator of northness/eastness and cardinal shares', 'metres'),
    'flat_observed_length_m': ('Length with exactly zero observed slope; altitude retained, orientation undefined', 'metres'),
    'gradient_coverage_share': ('Observed gradient length divided by all unique mapped axislength', 'fraction'),
    'seam_policy': ('Approved local missing-gradient policy; Stage66 audit cell status remains historical', 'text'),
})


def row_digest(frame):
    """Canonical string-field row hash, independent of Windows/Git line endings."""
    return hashlib.sha256(json.dumps(frame.to_dict('records'), ensure_ascii=False, separators=(',', ':')).encode('utf8')).hexdigest()


def main():
    decision = json.loads((ROOT / DECISION).read_text(encoding='utf8'))
    if decision['mixed_edition_complete_neighbourhood'] != 'retain_altitude_and_length_leave_gradient_missing' or decision['exclude_groups'] or decision['interpolate_or_adjust_seams']:
        raise ValueError('Only the explicit approved missing-gradient seam policy is implemented')
    paths = [Path(__file__).resolve().relative_to(ROOT).as_posix(), DECISION, AUDIT, PRESERVATION, PARENT, NETWORK,
             'src/descriptive/summarise_terrain_orientation_stage64.py', 'src/descriptive/audit_native2m_reference_stage66.py']
    inputs = {p: sha(p) for p in paths}
    frozen = json.loads((ROOT / AUDIT).read_text(encoding='utf8'))
    for p, h in {**frozen['input_sha256'], **frozen['output_sha256']}.items():
        if sha(p) != h:
            raise ValueError('Frozen Stage66 input/output changed: ' + p)
    groups = pd.read_csv(ROOT / PARENT, float_precision='round_trip')
    network = pd.read_csv(ROOT / NETWORK, float_precision='round_trip')
    if len(groups) != 70 or groups.station_group_id.duplicated().any() or not groups.group_retained.all():
        raise ValueError('Retain all 70 groups exactly once')
    if not groups.station_group_id.equals(network.station_group_id):
        raise ValueError('Preserved group universe/order changed')
    lineage = network.set_index('station_group_id').parent_station_group_ids.to_dict()
    rows = []
    for _, g in groups.iterrows():
        row = g.to_dict()
        row.update(source_id=SOURCE, parent_station_group_ids=lineage[g.station_group_id],
                   seam_policy='missing_gradient_at_mixed_edition_only')
        if pd.notna(g.cell_detail_file):
            inputs[g.cell_detail_file] = sha(g.cell_detail_file)
            f = pd.read_csv(ROOT / g.cell_detail_file, low_memory=False, float_precision='round_trip')
            mixed = f.horn_complete_native_neighbourhood & f.mixed_reference_neighbourhood
            if f.loc[mixed, 'gradient_observed'].any() or f.loc[mixed, ['terrain_slope_degrees', 'terrain_aspect_degrees']].notna().any().any():
                raise ValueError('Do not compute/adjust gradients across mixed-edition seams')
            stats = summarise_cells(f)
            total = stats.pop('unique_mapped_axis_length_m')
            if not math.isclose(total, g.unique_mapped_axis_length_m, rel_tol=1e-12):
                raise ValueError('Unique axislength changed')
            row.update(stats)
            mask = f.gradient_observed
            observed = math.fsum(f.loc[mask, 'unique_axis_length_m'])
            row.update(observed_gradient_length_m=observed, gradient_coverage_share=observed / total,
                       length_weighted_observed_slope_degrees=float(np.average(f.loc[mask, 'terrain_slope_degrees'], weights=f.loc[mask, 'unique_axis_length_m'])) if mask.any() else None,
                       terrain_status='native2m_reference_extracted_partial_gradient' if (~mask).any() else 'native2m_reference_extracted')
            if not math.isclose(row['missing_gradient_length_m'], g.mixed_edition_complete_neighbourhood_length_m + g.missing_native_neighbourhood_length_m, abs_tol=1e-9):
                raise ValueError('Missing gradient causes do not reconcile')
        rows.append(row)
    frame = pd.DataFrame(rows).reindex(columns=DEFS)
    target = ROOT / SUMMARY
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    if master.source_id.duplicated().any() or dictionary.duplicated(['table', 'variable']).any():
        raise ValueError('Duplicate registry keys')
    if target.exists():
        state = json.loads(target.read_text(encoding='utf8'))
        if state['input_sha256'] != inputs or sha(OUTPUT) != state['output_sha256'][OUTPUT]:
            raise ValueError('Frozen Stage67 differs; use a new namespace')
    else:
        if len(master) != 1195 or len(dictionary) != 8049 or SOURCE in set(master.source_id):
            raise ValueError('Unexpected preappend registry; reconcile before writing')
        write_csv(frame, ROOT / OUTPUT)
        state = dict(date='2026-10-10', input_sha256=inputs, output_sha256={OUTPUT: sha(OUTPUT)},
                     prior_registry_rows_and_digest={p: dict(rows=len(f), sha256=row_digest(f)) for p, f in [('metadata/data_sources_master.csv', master), ('metadata/data_dictionary.csv', dictionary)]},
                     retained_groups=len(frame), extracted_groups=int(frame.observed_gradient_length_m.notna().sum()),
                     terrain_status_counts=frame.terrain_status.value_counts().to_dict(),
                     mixed_edition_missing_gradient_length_m=float(frame.mixed_edition_complete_neighbourhood_length_m.sum()),
                     missing_native_elevation_length_m=float(frame.missing_altitude_length_m.sum()),
                     current_proxy_not_verified_preentry=True, no_model_fit_imputation_or_group_exclusion=True,
                     decision=decision, source_attribution='Office fédéral de topographie swisstopo; OpenStreetMap contributors')
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    for path, f in [('metadata/data_sources_master.csv', master), ('metadata/data_dictionary.csv', dictionary)]:
        baseline = state['prior_registry_rows_and_digest'][path]
        if row_digest(f.iloc[:baseline['rows']]) != baseline['sha256']:
            raise ValueError('Prior registry rows changed')
    if SOURCE not in set(master.source_id):
        record = dict(source_id=SOURCE, variable_name='approved_native2m_group_terrain_reference',
                      variable_description='70 retained groups;40 extracted altitude/terrain references; only mixed-edition Horn gradients locally missing',
                      source_organisation='Thesis derived analysis of swisstopo/OpenStreetMap', retrieval_date='2026-10-10', processed_file=OUTPUT,
                      geographic_level='Station group, not municipality or independent cells', temporal_resolution='Current qualified mapped axes/latest native tile editions; not preentry certified',
                      units='Metres, degrees, dimensionless components/fractions', license='swisstopo OGD attribution; OSM ODbL',
                      retrieval_method='Frozen Stage66 observed cells only; no external request',
                      transformation_applied='Explicitly approved local seam gradient missingness; observed-length slope and nonflat-angle weighted summaries',
                      quality_notes='All70groups retained;29 unresolved scopes and one referenced-axis absence remain; no automatic filtering/clustering/causal fit',
                      notes=DECISION + '; ' + AUDIT + '; original attribution Office fédéral de topographie swisstopo')
        write_csv(pd.concat([master, pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_sources_master.csv')
    records = []
    for col, (description, unit) in DEFS.items():
        if ((dictionary.table == TABLE) & (dictionary.variable == col)).any():
            continue
        role = ('Approved continuous candidate; temporal/profile validity still required before fit' if col in ('terrain_northness', 'terrain_eastness') else
                'Descriptive only; no automatic model inclusion' if col in ('orientation_resultant_concentration', 'north_length_share', 'east_length_share', 'south_length_share', 'west_length_share') else 'Qualified terrain/provenance/coverage')
        records.append(dict(variable=col, table=TABLE, description=description, unit=unit, data_type=str(frame[col].dtype),
                            geographic_level='Station group, not municipality/independent cells', temporal_level='Current qualified proxy/literal DEM editions',
                            source_id=SOURCE, raw_or_derived='derived', formula=FORMULAS.get(col, description), causal_role=role,
                            missing_share=f'{frame[col].isna().mean():.6f}', notes='Approved seam-local missingness; retained altitude/length; no interpolation, dominant direction, group exclusion or fitted model'))
    if records:
        write_csv(pd.concat([dictionary, pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')], ignore_index=True), ROOT / 'metadata/data_dictionary.csv')
    print(json.dumps({k: v for k, v in state.items() if k not in ('input_sha256', 'output_sha256', 'prior_registry_rows_and_digest')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
