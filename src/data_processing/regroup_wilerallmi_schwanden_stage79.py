"""Approved 70 -> 69 overlay; keep every old group identity and municipal outcome."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import pandas as pd
from src.causal_inference.estimate_accessibility_road_did import group_reference, build_exposure
from src.data_processing.regroup_eischoll_unterbaech_stage55 import joined, compare_exposure
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

CONFIG = 'config/piste_scope_decisions_stage79.json'
SOURCE = 'DERIVED_CONNECTED_GROUP_OVERLAY_STAGE79'
SUMMARY = 'reports/wilerallmi_schwanden_regrouping_stage79_summary.json'
PARENTS = {
    'lineage': 'station_group_lineage_stage55',
    'groups': 'accessibility_station_groups_stage55',
    'access': 'accessibility_station_access_points_stage55',
    'pairs': 'accessibility_road_pairs_stage55',
    'reference': 'accessibility_road_group_reference_stage55',
    'monthly': 'accessibility_road_monthly_exposure_stage55',
    'inventory': 'accessibility_road_inventory_stage55',
}
OUTPUTS = {key: ('reports/' if key == 'inventory' else 'data_processed/') +
           name.replace('stage55', 'stage79') + '.csv' for key, name in PARENTS.items()}
BRIDGE = 'data_processed/station_group_parent_bridge_stage79.csv'


def read(path):
    return pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)


def regroup(groups, decision):
    parents, new = decision['parent_group_ids'], decision['new_derived_group_id']
    if len(groups) != 70 or not groups.station_group_id.is_unique:
        raise ValueError('Require retained70-group input')
    part = groups[groups.station_group_id.isin(parents)]
    if len(part) != 2 or not part.first_effective_month.eq(decision['common_entry_month']).all():
        raise ValueError('Different or missing parent entry calendars')
    for col in ['first_entry_season', 'first_winter_effective_month', 'membership_continuity_status']:
        if part[col].nunique() != 1:
            raise ValueError('Different histories require validation: ' + col)
    row = part.iloc[0].to_dict()
    for col in ['component_resort_ids', 'source_entry_event_ids', 'source_entry_labels',
                'cluster_ids_lineage_only', 'source_ids', 'parent_station_group_ids']:
        row[col] = joined(part[col])
    # Wilerallmi has no directory listing: do not turn partial catalogue sums
    # or altitude bounds into complete combined-domain characteristics.
    for col in ['ski_area_km_unique_listing_sum', 'number_lifts_unique_listing_sum',
                'altitude_top_m_min', 'altitude_top_m_max']:
        row[col] = ''
    row.update(station_group_id=new, station_group_name=decision['new_group_name'],
               group_origin='researcher_approved_connected_overlay',
               scope_status='approved_connected_domain_internal_pdf_dates_not_publication_proof',
               grouping_basis='Official connected plan + joint2024/25 entry + user approval; retain historical caveat',
               component_listing_count=len([x for x in row['component_resort_ids'].split('|') if x]),
               entry_event_count=len(row['source_entry_event_ids'].split('|')),
               structural_data_status='combined_catalogue_incomplete_no_imputation',
               aggregation_source_id=SOURCE,
               historical_connection_quality=decision['historical_connection_quality'])
    other = groups[~groups.station_group_id.isin(parents)].reset_index(drop=True)
    result = pd.concat([other, pd.DataFrame([row])], ignore_index=True)
    result['stage79_parent_station_group_ids'] = result.station_group_id.map(
        lambda gid: joined(parents) if gid == new else gid)
    result['stage79_overlay_source_id'] = SOURCE
    bridge = pd.DataFrame(dict(parent_station_group_id=r.station_group_id,
        station_group_id=new if r.station_group_id in parents else r.station_group_id,
        parent_station_group_name=r.station_group_name,
        group_changed=r.station_group_id in parents, source_id=SOURCE) for r in groups.itertuples())
    if len(result) != 69 or not result.station_group_id.is_unique or len(bridge) != 70:
        raise ValueError('Retain all identities, merge only two approved parents')
    pd.testing.assert_frame_equal(result.iloc[:len(other)][groups.columns], other)
    return result, bridge


def map_ids(frame, bridge):
    mapped = frame.copy()
    mapped['stage79_parent_station_group_id'] = frame.station_group_id
    mapped['station_group_id'] = frame.station_group_id.map(
        bridge.set_index('parent_station_group_id').station_group_id)
    if mapped.station_group_id.isna().any():
        raise ValueError('Unmapped original group')
    # Existing original_station_group_id fields from Stage55 remain unchanged.
    return mapped


def register(frames):
    master = read('metadata/data_sources_master.csv')
    if SOURCE not in set(master.source_id):
        record = dict(source_id=SOURCE, variable_name='approved_connected_group_overlay',
            variable_description='Wilerallmi-Sch wanden single derived group, original IDs and unique municipal outcomes',
            source_organisation='Thesis approved derivation', retrieval_date='2026-10-11',
            retrieval_method='User-approved connected plan and retained road minima; no new routing or estimator',
            processed_file='|'.join([*OUTPUTS.values(), BRIDGE]),
            geographic_level='69 derived groups; all71 original group identities and185 municipal territories retained',
            temporal_resolution='Historical entry calendars; current static road reference',
            transformation_applied='Two2024/25 groups toone; original road values and source municipal observations unchanged',
            quality_notes='Internal plan dates2019 not publication proof; combined catalogue fields incomplete and left missing',
            notes='Decision '+CONFIG+'; immutable old outputs; SHA '+SUMMARY)
        write_csv(pd.concat([master, pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],
                  ignore_index=True).fillna(''), ROOT/'metadata/data_sources_master.csv')
    dictionary = read('metadata/data_dictionary.csv'); records = []
    defs = {
        'stage79_parent_station_group_ids': ('All parent Stage55 IDs retained behind each derived group', 'identifiers'),
        'stage79_overlay_source_id': ('Registered source of this approved overlay', 'identifier'),
        'stage79_parent_station_group_id': ('Unchanged Stage55 group ID, not original71-group key', 'identifier'),
        'parent_station_group_id': ('One Stage55 parent group ID, preserved exactly', 'identifier'),
        'parent_station_group_name': ('Unchanged Stage55 parent name, not a join key', 'name'),
    }
    for key, frame in frames.items():
        path = BRIDGE if key == 'bridge' else OUTPUTS[key]
        parent_name = 'station_group_lineage_stage55' if key == 'bridge' else PARENTS[key]
        parent = dictionary[dictionary.table.eq(parent_name)]
        for col in frame:
            table = Path(path).stem
            if ((dictionary.table == table) & dictionary.variable.eq(col)).any(): continue
            oldcol = {'parent_station_group_id':'original_station_group_id',
                      'parent_station_group_name':'original_station_group_name'}.get(col, col)
            previous = parent[parent.variable.eq(oldcol)]
            if col in defs:
                desc, unit = defs[col]
                rec = dict(variable=col, description=desc, unit=unit,
                    geographic_level='Retained group lineage or municipal exposure',
                    temporal_level='Retained source calendars/current road proxy', raw_or_derived='approved overlay',
                    causal_role='Group/access inventory; not an effect estimate')
            elif len(previous) == 1:
                rec = previous.iloc[0].to_dict()
            else:
                raise ValueError('No verified parent definition: ' + parent_name + ':' + col)
            rec.update(variable=col, table=table, source_id=SOURCE, data_type=str(frame[col].dtype),
                missing_share=f"{(frame[col].isna() | frame[col].astype(str).eq('')).mean():.6f}",
                formula='src/data_processing/regroup_wilerallmi_schwanden_stage79.py; retained minimum access and unchanged outcomes',
                notes='Parent '+parent_name+' definitions preserved; combined structural catalogue missing, no imputation; '+CONFIG)
            records.append(rec)
    if records:
        write_csv(pd.concat([dictionary, pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS)],
                  ignore_index=True).fillna(''), ROOT/'metadata/data_dictionary.csv')


def main():
    d = json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))['connected_group']
    if not d['preserve_original_group_ids_and_outputs'] or d['automatic_exclusion_authorised']:
        raise ValueError('Approved scope changed')
    paths = {k: ('reports/' if k == 'inventory' else 'data_processed/') + name + '.csv'
             for k, name in PARENTS.items()}
    fixed = [CONFIG, 'src/data_processing/regroup_wilerallmi_schwanden_stage79.py', *paths.values(),
        'data_processed/accessibility_municipality_month_exposure_territorial.csv',
        'data_processed/magic_pass_membership_history.csv']
    inputs = {p: sha(p) for p in fixed}
    groups, bridge = regroup(read(paths['groups']), d)
    access = map_ids(read(paths['access']), bridge)
    pairs = map_ids(pd.read_csv(ROOT/paths['pairs']), bridge)
    reference = group_reference(pairs, groups); reference['source_id'] = SOURCE
    panel = pd.read_csv(ROOT/fixed[-2]); history = pd.read_csv(ROOT/fixed[-1])
    monthly, inventory = build_exposure(reference, panel, history, [15,30,45])
    monthly['accessibility_source_id'] = SOURCE; inventory['source_id'] = SOURCE
    before = pd.read_csv(ROOT/paths['monthly'])
    before['date'] = pd.to_datetime(before.date)
    before['first_exposure_month'] = pd.to_datetime(before.first_exposure_month)
    changes = compare_exposure(before, monthly)
    lineage = read(paths['lineage'])
    lineage['stage79_parent_station_group_id'] = lineage.station_group_id
    lineage['station_group_id'] = lineage.station_group_id.map(
        bridge.set_index('parent_station_group_id').station_group_id)
    if len(lineage) != 71 or lineage.original_station_group_id.nunique() != 71 or lineage.station_group_id.isna().any():
        raise ValueError('Original71 identities must survive both overlays')
    frames = dict(lineage=lineage, groups=groups, access=access, pairs=pairs,
                  reference=reference, monthly=monthly, inventory=inventory, bridge=bridge)
    target = ROOT/SUMMARY
    if target.exists():
        state = json.loads(target.read_text(encoding='utf-8'))
        if state['input_sha256'] != inputs or any(sha(p) != h for p,h in state['output_sha256'].items()):
            raise ValueError('Frozen overlay changed: use a new stage')
    else:
        for key, frame in frames.items(): write_csv(frame, ROOT/(BRIDGE if key == 'bridge' else OUTPUTS[key]))
        state = dict(date='2026-10-11', completed_at=datetime.now(timezone.utc).isoformat(),
            input_sha256=inputs, output_sha256={p:sha(p) for p in [*OUTPUTS.values(),BRIDGE]},
            parent_group_count=70, derived_group_count=69, retained_original_group_identity_count=71,
            retained_territory_count=panel.municipality_bfs_id.nunique(),
            road_pair_count=len(pairs), access_point_count=len(access), exposure_comparison=changes,
            outcomes_not_duplicated=True, first_exposure_and_nearest_access_unchanged=True,
            no_effect_estimated=True, no_exclusion=True, combined_catalogue_imputed=False,
            historical_connection_quality=d['historical_connection_quality'])
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    register(frames)
    print(json.dumps({k:v for k,v in state.items() if not k.endswith('sha256')}, ensure_ascii=False))


if __name__ == '__main__': main()
