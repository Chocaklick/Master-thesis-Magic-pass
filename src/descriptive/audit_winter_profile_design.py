"""Coverage-only audit for proposed winter/profile analysis; never estimates effects.

Run from project root. Existing classes/groups and outcome values are immutable.
Both winter definitions are diagnostics, not approved analysis specifications.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_WINTER_PROFILE_DESIGN_AUDIT_2026_10_08'
INPUTS = {
    'groups': 'data_processed/accessibility_station_groups.csv',
    'resorts': 'data_processed/resort_master.csv',
    'segments': 'data_processed/path_c_cluster_segments.csv',
    'reference': 'data_processed/accessibility_road_did_group_reference.csv',
    'panel': 'data_processed/accessibility_municipality_month_exposure_territorial.csv',
    'history': 'data_processed/magic_pass_membership_history.csv',
    'offering': 'data_processed/magic_pass_membership_status_by_season.csv',
}
EXTRA_INPUTS = ['config/temporal_controls.json', 'config/accessibility_station_groups.json',
    'config/accessibility_road_did_final_execution.json',
    'metadata/magic_pass_season_offering_evidence.json',
    'reports/path_c_feature_readiness_audit.csv',
    'reports/accessibility_road_did_summary.json']
OUTPUTS = {
    'winter_profile_group_audit': 'reports/winter_profile_group_audit.csv',
    'winter_profile_municipality_support_audit': 'reports/winter_profile_municipality_support_audit.csv',
}
SUMMARY = 'reports/winter_profile_design_audit_summary.json'
FIELDS = {
    'matched_cluster_ids': ('Existing cluster IDs joined through exact component resort IDs; not a new group definition', 'identifiers'),
    'existing_segment_ids': ('Distinct nonmissing existing segment IDs across the matched clusters; no segment assigned by this audit', 'identifiers'),
    'existing_segment_link_status': ('Single existing cluster class, mixed classes, incomplete class coverage, or no linked class; all remain descriptive/undated', 'category'),
    'component_feature_dates': ('Original component feature-observation dates; UNKNOWN is preserved', 'source dates'),
    'preentry_structure_verified': ('False: no exact dated preentry structure verified in the audited current directory', 'boolean'),
    'winter_definition': ('Diagnostic broad Nov-Apr or core Dec-Mar, neither approved for estimation', 'category'),
    'first_base_exposure_month': ('Earliest historical base-pass entry of a road-accessible existing group, before the proposed winter anchor', 'calendar month'),
    'first_winter_exposure_month': ('Earliest existing November winter anchor among accessible groups; not a measured opening date', 'calendar month'),
    'first_winter_trigger_group_ids': ('All accessible group IDs with the same earliest winter anchor, never only the nearest group', 'identifiers'),
    'first_winter_trigger_group_count': ('Count of distinct existing groups entering at the first winter anchor', 'count'),
    'ever_accessible_group_count': ('Distinct historically entered groups inside inclusive road threshold over observed horizon', 'count'),
    'later_group_entry_count': ('Distinct accessible groups with a winter anchor later than the first one, without censoring observations', 'count'),
    'ever_multiple_active_groups': ('Whether any observed winter month has at least two active accessible groups under documented exit convention', 'boolean'),
    'complete_pre_winter_count': ('Complete proposed winters ending strictly before first base-pass exposure; zero is observed lack of complete windows, not imputed nights', 'count'),
    'complete_post_winter_count': ('Complete proposed winters starting in/after first winter exposure; later entries and exits do not censor outcome follow-up', 'count'),
    'first_post_winter_complete': ('All required original monthly nights observed in the first proposed post winter', 'boolean'),
    'first_two_post_winters_complete': ('All required nights observed in both first and second proposed post winters', 'boolean'),
    'pre24_nights_observed_months': ('Observed original hotel-night months in the 24 calendar months strictly before first base exposure', 'count'),
    'pre24_beds_observed_months': ('Observed original available-bed months in the same pre-base-exposure 24-month window', 'count'),
    'pre24_foreign_observed_months': ('Observed foreign and total hotel nights in the same pre-base-exposure window', 'count'),
    'observed_end': ('Last observed original overnight month, not the end of future calendar rows', 'calendar month'),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def split_ids(value):
    return str(value).split('|') if pd.notna(value) and str(value) else []


def audit_groups(groups, resorts, segments):
    master = resorts.set_index('resort_id')
    classes = segments.set_index('cluster_id').segment_id
    rows = []
    for row in groups.to_dict('records'):
        ids = split_ids(row['component_resort_ids'])
        if any(r not in master.index for r in ids):
            raise ValueError('Unknown exact component resort ID')
        subset = master.loc[ids] if ids else master.iloc[:0]
        clusters = sorted(subset.cluster_id.dropna().unique())
        linked = classes.reindex(clusters)
        labels = sorted(linked.dropna().unique())
        status = ('no_linked_class' if not len(labels) else
                  'incomplete_class_coverage' if linked.isna().any() else
                  'mixed_existing_classes' if len(labels) > 1 else 'single_existing_class')
        dates = sorted(subset.feature_observation_date.dropna().unique())
        # Preentry dating is absent in these input records. Fail rather than
        # silently invent approval if a new historical source is introduced.
        if any(d != 'UNKNOWN' for d in dates):
            raise ValueError('New feature dates require renewed temporal audit')
        row.update(matched_cluster_ids='|'.join(clusters), existing_segment_ids='|'.join(labels),
                   existing_segment_link_status=status, component_feature_dates='|'.join(dates),
                   preentry_structure_verified=False)
        rows.append(row)
    return pd.DataFrame(rows)


def winter_dates(year, definition):
    start, count = (11, 6) if definition == 'nov_apr' else (12, 4)
    return pd.date_range(pd.Timestamp(year, start, 1), periods=count, freq='MS')


def complete_windows(unit, years, definition):
    nights = unit.set_index('date').hotel_overnights
    return {year: bool(nights.reindex(winter_dates(year, definition)).notna().all()) for year in years}


def overlap_components(links):
    """Conservative overlap diagnostic, not an automatically selected bootstrap."""
    parents = {}
    def find(x):
        parents.setdefault(x, x)
        while parents[x] != x:
            parents[x] = parents[parents[x]]
            x = parents[x]
        return x
    for row in links.itertuples():
        a, b = find(('m', row.municipality_bfs_id)), find(('g', row.station_group_id))
        parents[a] = b
    sizes = {}
    for node in list(parents):
        if node[0] == 'm':
            key = find(node)
            sizes[key] = sizes.get(key, 0) + 1
    return sorted(sizes.values(), reverse=True)


def audit_municipalities(reference, groups, panel, history):
    observed_end = panel.loc[panel.hotel_overnights.notna(), 'date'].max()
    exits = {'MP_GROUP_RESORT__' + r.candidate_resort_id: pd.Timestamp(r.exit_date).to_period('M').to_timestamp()
             for r in history[history.event_type.eq('base_pass_exit')].itertuples()}
    ref = reference.merge(groups[['station_group_id', 'first_winter_effective_month']],
                          on='station_group_id', validate='many_to_one')
    ref['base'] = pd.to_datetime(ref.first_effective_month)
    ref['winter'] = pd.to_datetime(ref.first_winter_effective_month)
    ref['last'] = ref.station_group_id.map(exits).fillna(observed_end)
    rows, summaries = [], {}
    for threshold in [15, 30, 45]:
        links = ref[ref.road_reference_minutes.le(threshold) & ref.winter.le(observed_end)
                    & ref.winter.le(ref['last'])].copy()
        by_unit = {bfs: part for bfs, part in links.groupby('municipality_bfs_id')}
        for bfs, unit in panel.groupby('municipality_bfs_id', sort=True):
            nearby = by_unit.get(bfs, links.iloc[:0])
            first = nearby.winter.min()
            base = nearby.base.min()
            trigger = nearby[nearby.winter.eq(first)]
            before = unit[unit.date.ge(base - pd.DateOffset(months=24)) & unit.date.lt(base)] if pd.notna(base) else unit.iloc[:0]
            multiple = False
            active = pd.Series(0, index=unit.index)
            for link in nearby.itertuples():
                active += (unit.date.ge(link.winter) & unit.date.le(link.last)).astype(int)
            multiple = bool((active[unit.date.dt.month.isin([11, 12, 1, 2, 3, 4])] >= 2).any())
            for definition in ['nov_apr', 'dec_mar']:
                complete = complete_windows(unit, range(panel.date.min().year - 1, observed_end.year + 1), definition)
                pre = [y for y, ok in complete.items() if ok and pd.notna(base) and winter_dates(y, definition)[-1] < base]
                post = [y for y, ok in complete.items() if ok and pd.notna(first) and winter_dates(y, definition)[0] >= first]
                first_year = first.year if pd.notna(first) else None
                rows.append(dict(threshold_minutes=threshold, winter_definition=definition,
                    municipality_bfs_id=int(bfs), municipality_name_source=unit.municipality_name_source.iloc[-1],
                    first_base_exposure_month=base, first_winter_exposure_month=first,
                    first_winter_trigger_group_ids='|'.join(sorted(trigger.station_group_id)),
                    first_winter_trigger_group_count=len(trigger), ever_accessible_group_count=len(nearby),
                    later_group_entry_count=int(nearby.winter.gt(first).sum()), ever_multiple_active_groups=multiple,
                    complete_pre_winter_count=len(pre), complete_post_winter_count=len(post),
                    first_post_winter_complete=complete.get(first_year, False),
                    first_two_post_winters_complete=complete.get(first_year, False) and complete.get(first_year + 1, False) if first_year else False,
                    pre24_nights_observed_months=int(before.hotel_overnights.notna().sum()),
                    pre24_beds_observed_months=int(before.hotel_beds_available.notna().sum()),
                    pre24_foreign_observed_months=int(before[['foreign_overnights', 'hotel_overnights']].notna().all(axis=1).sum()),
                    observed_end=observed_end, source_id=SOURCE))
        components = overlap_components(links)
        summaries[str(threshold)] = dict(accessible_group_count=int(links.station_group_id.nunique()),
            overlap_component_count=len(components), overlap_component_municipality_sizes=components)
    frame = pd.DataFrame(rows)
    for threshold in [15, 30, 45]:
        summaries[str(threshold)]['winter_windows'] = {}
        for definition in ['nov_apr', 'dec_mar']:
            sub = frame[frame.threshold_minutes.eq(threshold) & frame.winter_definition.eq(definition)]
            exposed = sub[sub.first_winter_exposure_month.notna()]
            pre_post = exposed.complete_pre_winter_count.ge(1) & exposed.complete_post_winter_count.ge(1)
            summaries[str(threshold)]['winter_windows'][definition] = dict(
                exposed_territories=len(exposed), at_least_one_complete_pre_and_post_winter=int(pre_post.sum()),
                first_post_winter_complete=int(exposed.first_post_winter_complete.sum()),
                first_two_post_winters_complete=int(exposed.first_two_post_winters_complete.sum()),
                three_complete_pre_winters=int(exposed.complete_pre_winter_count.ge(3).sum()),
                multiple_first_winter_groups=int(exposed.first_winter_trigger_group_count.gt(1).sum()),
                ever_multiple_active_groups=int(exposed.ever_multiple_active_groups.sum()),
                later_group_entries_territories=int(exposed.later_group_entry_count.gt(0).sum()),
                complete_pre24_nights=int(exposed.pre24_nights_observed_months.eq(24).sum()),
                complete_pre24_beds=int(exposed.pre24_beds_observed_months.eq(24).sum()),
                complete_pre24_foreign=int(exposed.pre24_foreign_observed_months.eq(24).sum()))
    return frame, summaries


def register(frames):
    source_path = ROOT / 'metadata/data_sources_master.csv'
    dictionary_path = ROOT / 'metadata/data_dictionary.csv'
    master = pd.read_csv(source_path, dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(dictionary_path, dtype=str, keep_default_na=False)
    record = dict(source_id=SOURCE, variable_name='winter_profile_design_feasibility',
        variable_description='Coverage, exact ID concordance and overlaps only; winter/profile/multi-exposure choices pending',
        source_organisation='Thesis audit from previously archived official HESTA, Magic Pass and directory/road evidence',
        source_dataset_name='Winter and heterogeneous-profile design audit', retrieval_date='2026-10-08',
        retrieval_method='Local SHA-checked prior outputs, no download or effect estimation',
        local_raw_file='|'.join(INPUTS.values()), processed_file='|'.join(OUTPUTS.values()),
        transformation_applied='Complete candidate season counts, exact resort-cluster IDs and bipartite overlap diagnostic',
        quality_notes='Two winter windows proposed, not approved; current undated segments not preentry covariates; no automatic exclusion, category assignment or summer status transfer',
        geographic_level='existing station group and harmonised municipality territory', temporal_resolution='candidate winter/entry',
        license='Inherits original sources; model and measurement limitations retained', confidence_level='coverage audit only')
    parents = ['accessibility_station_groups', 'accessibility_road_did_inventory',
               'accessibility_municipality_month_exposure_territorial']
    definitions = []
    for table, frame in frames.items():
        for variable in frame:
            prior = dictionary[dictionary.table.isin(parents) & dictionary.variable.eq(variable)]
            if variable in FIELDS:
                description, unit = FIELDS[variable]
                row = dict(variable=variable, table=table, description=description, unit=unit)
            elif len(prior):
                row = prior.iloc[0].to_dict()
            else:
                raise ValueError('Missing definition: ' + variable)
            row.update(variable=variable, table=table, source_id=SOURCE, raw_or_derived='derived',
                       data_type=str(frame[variable].dtype), missing_share=f'{frame[variable].isna().mean():.6f}',
                       causal_role='design/coverage audit, no estimated effect or approved profile', notes=record['quality_notes'])
            definitions.append(row)
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), source_path)
    write_csv(pd.concat([dictionary[~dictionary.table.isin(frames)], pd.DataFrame(definitions).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), dictionary_path)


def main():
    inputs = {k: pd.read_csv(ROOT / p, low_memory=False) for k, p in INPUTS.items()}
    inputs['panel']['date'] = pd.to_datetime(inputs['panel'].date)
    old = json.loads((ROOT / 'reports/accessibility_road_did_summary.json').read_text(encoding='utf-8'))
    protected = {**old['output_sha256'], **old['input_sha256'], **old['protected_legacy_sha256']}
    checks = {p: sha(p) for p in [*INPUTS.values(), *EXTRA_INPUTS, 'src/descriptive/audit_winter_profile_design.py']}
    if (ROOT / SUMMARY).exists():
        previous = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        if previous['input_sha256'] != checks:
            raise ValueError('Audit inputs changed; explicit new version required')
        for p, value in previous['output_sha256'].items():
            if sha(p) != value:
                raise ValueError('Audit output edited: ' + p)
        print('Exact audit checkpoint reused; no output rewrite, network call or estimation.')
        return
    for p, value in protected.items():
        if sha(p) != value:
            raise ValueError('Legacy input/output changed: ' + p)
    group = audit_groups(inputs['groups'], inputs['resorts'], inputs['segments'])
    units, counts = audit_municipalities(inputs['reference'], inputs['groups'], inputs['panel'], inputs['history'])
    frames = dict(zip(OUTPUTS, [group, units]))
    for table, frame in frames.items():
        write_csv(frame, ROOT / OUTPUTS[table])
    register(frames)
    offering = inputs['offering']
    summary = dict(status='audit_complete_all_new_method_choices_pending', effect_estimation_run=False,
        automatic_exclusion_applied=False, classifications_changed=False, summer_status_transferred=False,
        audit_date='2026-10-08', group_count=len(group), structural_status_counts=group.structural_data_status.value_counts().to_dict(),
        existing_segment_link_status_counts=group.existing_segment_link_status.value_counts().to_dict(),
        single_existing_class_counts=group[group.existing_segment_link_status.eq('single_existing_class')].existing_segment_ids.value_counts().to_dict(),
        verified_preentry_structural_groups=int(group.preentry_structure_verified.sum()), thresholds=counts,
        offering_review_destination_units=int(offering.destination_unit_id.nunique()),
        documented_summer_unit_seasons=int(offering.summer_access_documented.sum()),
        unknown_summer_unit_seasons=int(offering.summer_access_status.eq('unknown_not_individually_documented').sum()),
        input_sha256=checks, output_sha256={p: sha(p) for p in OUTPUTS.values()}, protected_legacy_sha256=protected)
    for p, value in protected.items():
        if sha(p) != value:
            raise ValueError('Protected prior result changed during audit: ' + p)
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith('sha256')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
