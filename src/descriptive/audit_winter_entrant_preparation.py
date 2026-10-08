"""Road/Dec-Apr entrant variation and preentry feature preparation, not effects.

All station groups remain intact. Event rows are diagnostic records, not a
duplicated outcome panel. Exact checkpoint reuse makes no network requests.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.causal_inference.audit_accessibility_successive_entries import residualize
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_WINTER_ENTRANT_PREPARATION_2026_10_08'
INPUTS = {
    'groups': 'data_processed/accessibility_station_groups.csv',
    'reference': 'data_processed/accessibility_road_did_group_reference.csv',
    'panel': 'data_processed/accessibility_municipality_month_exposure_territorial.csv',
    'history': 'data_processed/magic_pass_membership_history.csv',
    'features': 'reports/winter_profile_group_audit.csv',
}
CONFIG = 'config/winter_profile_preparation_approved.json'
REVIEW = 'config/winter_profile_historical_source_review.json'
SUMMARY = 'reports/winter_entrant_preparation_summary.json'
OUTPUTS = {
    'winter_entrant_group_audit': 'reports/winter_entrant_group_audit.csv',
    'winter_entrant_event_support': 'reports/winter_entrant_event_support.csv',
    'winter_clustering_feature_readiness': 'reports/winter_clustering_feature_readiness.csv',
}
DEFINITIONS = {
    'threshold_minutes': ('Inclusive approved road reference maximum; scenarios are not independent samples', 'minutes'),
    'station_group_id': ('Unchanged existing station group stable identifier', 'identifier'),
    'station_group_name': ('Original existing station group name', 'name'),
    'municipality_bfs_id': ('Harmonised municipality territory BFS ID, including exact Moutier bridge', 'identifier'),
    'municipality_name_source': ('Original municipality name in the preserved panel', 'name'),
    'entry_winter_anchor': ('Existing November entry anchor, not measured opening date', 'month'),
    'entering_group_ids': ('All groups newly accessible in this municipality at the same anchor', 'identifiers'),
    'entering_group_count': ('Count of simultaneous entering distinct groups', 'count'),
    'prior_active_group_ids': ('All accessible groups still active in October immediately before this entry anchor', 'identifiers'),
    'prior_active_group_count': ('Count of October active groups; not cumulative entry count', 'count'),
    'is_later_network_entry': ('Entry anchor later than the municipality earliest network winter entry, even if old membership ended', 'boolean'),
    'previous_and_first_winter_complete': ('Original nights observed for all five months of both immediately previous and entry winter; prior winter may already be treated', 'boolean'),
    'candidate_same_portfolio_complete_controls': ('Diagnostic count of other territories with identical October active group IDs, no winter entry/exit and complete adjacent winters; not approved donors', 'count'),
    'candidate_same_portfolio_history_complete_controls': ('Above diagnostic plus same first network winter anchor (or both never exposed by October); histories otherwise not proven comparable', 'count'),
    'candidate_same_portfolio_control_bfs_ids': ('Exact territory IDs behind the stable same-portfolio diagnostic count; not approved donors', 'identifiers'),
    'candidate_same_portfolio_history_control_bfs_ids': ('Exact territory IDs also sharing the first-network anchor; not approved donors', 'identifiers'),
    'accessible_territories': ('Territories with inclusive road access and historical winter entry before the last observed month', 'count'),
    'observed_winter_exposure_rows': ('Observed Dec-Apr commune-month rows exposed to this group; not independent station observations', 'count'),
    'first_entry_territories': ('Territories where this group enters at earliest network winter entry, possibly jointly', 'count'),
    'later_entry_territories': ('Territories where this group enters after earliest network winter entry', 'count'),
    'later_entry_complete_territories': ('Later-entry territories with complete immediately previous and first post winter', 'count'),
    'later_entry_alone_complete_territories': ('Above, with this group as sole new entrant at the anchor; does not guarantee isolation from other shocks', 'count'),
    'later_entry_supported_same_portfolio_territories': ('Complete later-entry territories with at least one diagnostic stable same-portfolio candidate, not causally approved', 'count'),
    'later_entry_alone_supported_same_portfolio_territories': ('Complete sole-entrant later-entry territories with such a candidate', 'count'),
    'later_entry_supported_history_territories': ('Complete later-entry territories with at least one candidate also sharing the first network winter anchor', 'count'),
    'identical_observed_exposure_group_ids': ('Other positive columns exactly identical over observed winter commune-months; their independent contributions cannot be separated in this design', 'identifiers'),
    'in_fixed_effect_linear_dependency': ('Numerically nonzero nullspace loading after municipality/calendar-month projection; algebraic diagnostic, not causal test', 'boolean'),
    'variation_status': ('no observed exposure, exact joint-only column, further FE linear dependency, or distinct algebraic variation requiring identification', 'category'),
    'source_id': ('Registered derived audit source ID', 'identifier'),
    'first_base_entry_month': ('Existing first base-pass entry; predictors must predate this, not just the November winter anchor', 'month'),
    'structural_data_status': ('Unchanged completeness of current unique-listing structure, not historical validity', 'category'),
    'component_feature_dates': ('Unchanged component observation dates, UNKNOWN preserved', 'dates'),
    'verified_preentry_structure': ('Existing audited full group preentry structural verification; no historical value inferred from investment proposals', 'boolean'),
    'existing_descriptive_segment_ids': ('Exact existing lift-cluster class links retained for comparison, not preentry profile assignment', 'identifiers'),
    'historical_candidate_source_ids': ('Targeted reviewed existing archive sources for this group, not exhaustive source availability', 'identifiers'),
    'historical_candidate_status': ('Targeted historical source limitations; unreviewed groups remain not reviewed rather than no source exists', 'category'),
    'clustering_fit_ready': ('False unless full required dated historical structure and exact feature/preprocessing protocol approved', 'boolean'),
}


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def pipe(values):
    return '|'.join(sorted(set(map(str, values))))


def winter_dates(year):
    return pd.date_range(pd.Timestamp(year, 12, 1), periods=5, freq='MS')


def complete_winter(unit, year):
    return bool(unit.set_index('date').hotel_overnights.reindex(winter_dates(year)).notna().all())


def active_ids(links, date):
    return frozenset(links.loc[links.winter.le(date) & links['last'].ge(date), 'station_group_id'])


def matrix_diagnostics(matrix, unit, month, numerical):
    positive = np.flatnonzero(matrix.any(axis=0))
    identical = {i: [] for i in range(matrix.shape[1])}
    for n, left in enumerate(positive):
        for right in positive[n + 1:]:
            if np.array_equal(matrix[:, left], matrix[:, right]):
                identical[left].append(int(right))
                identical[right].append(int(left))
    dependent = set()
    if not len(positive):
        return identical, dependent, dict(positive_group_columns=0, fixed_effect_rank=0, rank_deficiency=0)
    residual, iterations = residualize(matrix[:, positive], unit, month,
        numerical['projection_tolerance'], numerical['projection_maximum_iterations'])
    _, singular, vt = np.linalg.svd(residual, full_matrices=False)
    tolerance = float(singular[0] * max(residual.shape) * np.finfo(float).eps)
    rank = int((singular > tolerance).sum())
    if rank < len(positive):
        loading = np.linalg.norm(vt[rank:], axis=0)
        dependent = set(map(int, positive[loading > numerical['nullspace_loading_tolerance']]))
    return identical, dependent, dict(positive_group_columns=len(positive), fixed_effect_rank=rank,
        rank_deficiency=len(positive) - rank, rank_tolerance=tolerance, projection_iterations=iterations)


def audit_threshold(threshold, groups, reference, panel, history, numerical):
    end = panel.loc[panel.hotel_overnights.notna(), 'date'].max()
    exits = {'MP_GROUP_RESORT__' + r.candidate_resort_id: pd.Timestamp(r.exit_date).to_period('M').to_timestamp()
             for r in history[history.event_type.eq('base_pass_exit')].itertuples()}
    links = reference.merge(groups[['station_group_id', 'first_winter_effective_month']],
                            on='station_group_id', validate='many_to_one')
    links['winter'] = pd.to_datetime(links.first_winter_effective_month)
    links['last'] = links.station_group_id.map(exits).fillna(end)
    links = links[links.road_reference_minutes.le(threshold) & links.winter.le(end)
                  & links.winter.le(links['last'])].copy()
    ids = groups.station_group_id.tolist()
    units = {int(bfs): part for bfs, part in panel.groupby('municipality_bfs_id')}
    nearby = {bfs: links[links.municipality_bfs_id.eq(bfs)] for bfs in units}
    first = {bfs: part.winter.min() for bfs, part in nearby.items()}
    observed = panel[panel.date.dt.month.isin([12, 1, 2, 3, 4]) & panel.hotel_overnights.notna()].copy()
    matrix = np.zeros((len(observed), len(ids)), dtype=bool)
    for i, gid in enumerate(ids):
        loc = links[links.station_group_id.eq(gid)]
        if len(loc):
            matrix[:, i] = (observed.municipality_bfs_id.isin(loc.municipality_bfs_id)
                & observed.date.ge(loc.winter.iloc[0]) & observed.date.le(loc['last'].iloc[0]))
    identical, dependent, design = matrix_diagnostics(matrix, observed.municipality_bfs_id.to_numpy(),
                                                     observed.date.to_numpy(), numerical)
    events = []
    for anchor in sorted(links.winter.unique()):
        anchor = pd.Timestamp(anchor)
        before = anchor - pd.DateOffset(months=1)
        dates = winter_dates(anchor.year)
        portfolios = {bfs: active_ids(part, before) for bfs, part in nearby.items()}
        complete = {bfs: complete_winter(unit, anchor.year - 1) and complete_winter(unit, anchor.year)
                    for bfs, unit in units.items()}
        # Diagnostic stable candidates: no other entry from anchor through April,
        # no documented membership loss during those months (exit month included).
        stable = {bfs: not (part.winter.ge(anchor) & part.winter.le(dates[-1])).any()
                       and not (part['last'].ge(before) & part['last'].lt(dates[-1])).any()
                  for bfs, part in nearby.items()}
        for bfs, part in links[links.winter.eq(anchor)].groupby('municipality_bfs_id'):
            bfs = int(bfs)
            candidates = [other for other in units if other != bfs and stable[other] and complete[other]
                          and portfolios[other] == portfolios[bfs]]
            first_before = first[bfs] if pd.notna(first[bfs]) and first[bfs] <= before else pd.NaT
            history_candidates = [other for other in candidates if
                (pd.isna(first_before) and (pd.isna(first[other]) or first[other] > before))
                or (pd.notna(first_before) and first[other] == first_before)]
            events.append(dict(threshold_minutes=threshold, municipality_bfs_id=bfs,
                municipality_name_source=units[bfs].municipality_name_source.iloc[-1],
                entry_winter_anchor=anchor, entering_group_ids=pipe(part.station_group_id),
                entering_group_count=len(part), prior_active_group_ids=pipe(portfolios[bfs]),
                prior_active_group_count=len(portfolios[bfs]), is_later_network_entry=anchor > first[bfs],
                previous_and_first_winter_complete=complete[bfs],
                candidate_same_portfolio_complete_controls=len(candidates),
                candidate_same_portfolio_history_complete_controls=len(history_candidates),
                candidate_same_portfolio_control_bfs_ids=pipe(candidates),
                candidate_same_portfolio_history_control_bfs_ids=pipe(history_candidates), source_id=SOURCE))
    events = pd.DataFrame(events)
    records = []
    for i, row in enumerate(groups.itertuples()):
        relevant = events[events.entering_group_ids.map(lambda s: row.station_group_id in s.split('|'))]
        later = relevant[relevant.is_later_network_entry]
        full = later[later.previous_and_first_winter_complete]
        supported = full.candidate_same_portfolio_complete_controls.gt(0)
        same = identical[i]
        status = ('no_observed_winter_exposure' if not matrix[:, i].any() else
                  'joint_only_exact_identical_column' if same else
                  'further_fixed_effect_linear_dependency' if i in dependent else
                  'distinct_variation_identification_pending')
        records.append(dict(threshold_minutes=threshold, station_group_id=row.station_group_id,
            station_group_name=row.station_group_name, accessible_territories=len(relevant),
            observed_winter_exposure_rows=int(matrix[:, i].sum()), first_entry_territories=len(relevant) - len(later),
            later_entry_territories=len(later), later_entry_complete_territories=len(full),
            later_entry_alone_complete_territories=int(full.entering_group_count.eq(1).sum()),
            later_entry_supported_same_portfolio_territories=int(supported.sum()),
            later_entry_alone_supported_same_portfolio_territories=int((supported & full.entering_group_count.eq(1)).sum()),
            later_entry_supported_history_territories=int(full.candidate_same_portfolio_history_complete_controls.gt(0).sum()),
            identical_observed_exposure_group_ids=pipe(ids[j] for j in same),
            in_fixed_effect_linear_dependency=i in dependent, variation_status=status, source_id=SOURCE))
    records = pd.DataFrame(records)
    design.update(observed_winter_rows=len(observed), exposed_territories=int(links.municipality_bfs_id.nunique()),
        distinct_territory_entry_events=len(events), later_territory_entry_events=int(events.is_later_network_entry.sum()),
        later_entry_territories=int(events.loc[events.is_later_network_entry, 'municipality_bfs_id'].nunique()),
        variation_status_counts=records.variation_status.value_counts().to_dict(),
        groups_with_later_entry=int(records.later_entry_territories.gt(0).sum()),
        groups_with_complete_later_entry=int(records.later_entry_complete_territories.gt(0).sum()),
        groups_with_complete_sole_later_entry=int(records.later_entry_alone_complete_territories.gt(0).sum()),
        groups_with_same_portfolio_candidates=int(records.later_entry_supported_same_portfolio_territories.gt(0).sum()),
        groups_with_sole_entry_same_portfolio_candidates=int(records.later_entry_alone_supported_same_portfolio_territories.gt(0).sum()),
        groups_with_same_history_candidates=int(records.later_entry_supported_history_territories.gt(0).sum()))
    return records, events, design


def feature_readiness(features, review):
    records = []
    for r in features.itertuples():
        candidates = [s for s in review['records'] if s['station_group_name_contains'].casefold() in r.station_group_name.casefold()]
        records.append(dict(station_group_id=r.station_group_id, station_group_name=r.station_group_name,
            first_base_entry_month=r.first_effective_month, structural_data_status=r.structural_data_status,
            component_feature_dates=r.component_feature_dates, verified_preentry_structure=r.preentry_structure_verified,
            existing_descriptive_segment_ids=r.existing_segment_ids,
            historical_candidate_source_ids=pipe(s['source_id'] for s in candidates),
            historical_candidate_status=pipe(s['group_feature_status'] for s in candidates) or 'not_reviewed_no_absence_claim',
            clustering_fit_ready=False, source_id=SOURCE))
    return pd.DataFrame(records)


def register(frames):
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    record = dict(source_id=SOURCE, variable_name='winter_entrant_variation_and_feature_readiness',
        variable_description='Road Dec-Apr entrant variation, stable-portfolio candidate support and dated trait readiness only',
        source_organisation='Thesis audit of already registered HESTA, Magic Pass, road and official archives',
        source_dataset_name='Winter entrant and supplementary clustering preparation', retrieval_date='2026-10-08',
        retrieval_method='Local inputs and targeted archived PDF inspection; no external request',
        local_raw_file='|'.join(INPUTS.values()), processed_file='|'.join(OUTPUTS.values()),
        geographic_level='existing station group and harmonised municipality territory', temporal_resolution='Dec-Apr winter and entry',
        transformation_applied='Exact observed columns; inherited two-way projection; complete adjacent winters and diagnostic exact previous portfolios',
        quality_notes='Algebraic and candidate support only; no causal donors approved, clustering fitted, imputation, exclusions or effect estimated',
        confidence_level='reproducible variation/coverage diagnostic', license='Inherits registered original source terms')
    definitions = []
    for table, frame in frames.items():
        for col in frame:
            description, unit = DEFINITIONS[col]
            definitions.append(dict(variable=col, table=table, description=description, unit=unit,
                data_type=str(frame[col].dtype), geographic_level=record['geographic_level'], temporal_level=record['temporal_resolution'],
                source_id=SOURCE, raw_or_derived='derived or preserved source identity',
                formula='See src/descriptive/audit_winter_entrant_preparation.py and report94',
                causal_role='preparation diagnostic, no causal effect or approved class',
                missing_share=f'{frame[col].isna().mean():.6f}', notes=record['quality_notes']))
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    write_csv(pd.concat([dictionary[~dictionary.table.isin(frames)], pd.DataFrame(definitions).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh-preparation', action='store_true',
        help='Explicitly rebuild only this derived preparation audit after a reviewed script/input revision; never modify legacy outputs')
    args = parser.parse_args()
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    if not config['additional_entry_identification_audit_approved'] or config['new_effect_estimation_approved']:
        raise ValueError('This script is preparation only under its explicit approval')
    review = json.loads((ROOT / REVIEW).read_text(encoding='utf-8'))
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv').set_index('source_id')
    archives = [sources.loc[s['source_id'], 'local_raw_file'] for s in review['records']]
    dependencies = [*INPUTS.values(), CONFIG, REVIEW, *archives, 'src/descriptive/audit_winter_entrant_preparation.py',
        'src/causal_inference/audit_accessibility_successive_entries.py', 'config/accessibility_successive_entries.json',
        'reports/winter_profile_design_audit_summary.json', 'reports/accessibility_road_did_summary.json']
    checks = {p: sha(p) for p in dependencies}
    old = json.loads((ROOT / 'reports/winter_profile_design_audit_summary.json').read_text(encoding='utf-8'))
    protected = {**old['input_sha256'], **old['output_sha256'], **old['protected_legacy_sha256']}
    for p, value in protected.items():
        if sha(p) != value:
            raise ValueError('Protected old input/output changed: ' + p)
    if (ROOT / SUMMARY).exists():
        previous = json.loads((ROOT / SUMMARY).read_text(encoding='utf-8'))
        for p, value in previous['output_sha256'].items():
            if sha(p) != value:
                raise ValueError('Audit output edited: ' + p)
        if not args.refresh_preparation:
            if previous['input_sha256'] != checks:
                raise ValueError('Inputs changed; explicitly review/version next audit')
            print('Exact stage41 checkpoint reused; no rewriting, network, clustering fit or effect estimation.')
            return
    inputs = {k: pd.read_csv(ROOT / p, low_memory=False) for k, p in INPUTS.items()}
    inputs['panel']['date'] = pd.to_datetime(inputs['panel'].date)
    group_frames, event_frames, counts = [], [], {}
    for threshold in config['road_thresholds_minutes']:
        group, events, diagnostic = audit_threshold(threshold, inputs['groups'], inputs['reference'],
            inputs['panel'], inputs['history'], config['numerical_diagnostics'])
        group_frames.append(group); event_frames.append(events); counts[str(threshold)] = diagnostic
    frames = dict(zip(OUTPUTS, [pd.concat(group_frames, ignore_index=True), pd.concat(event_frames, ignore_index=True),
                               feature_readiness(inputs['features'], review)]))
    for table, frame in frames.items():
        write_csv(frame, ROOT / OUTPUTS[table])
    register(frames)
    for p, value in protected.items():
        if sha(p) != value:
            raise ValueError('Protected prior output changed during audit: ' + p)
    summary = dict(status='preparation_and_variation_audit_complete_method_choices_pending', date='2026-10-08',
        group_count=len(inputs['groups']), territory_count=int(inputs['panel'].municipality_bfs_id.nunique()),
        effect_estimation_run=False, clustering_fitted=False, automatic_exclusion_applied=False,
        verified_preentry_structural_groups=int(frames['winter_clustering_feature_readiness'].verified_preentry_structure.sum()),
        thresholds=counts, input_sha256=checks, output_sha256={p: sha(p) for p in OUTPUTS.values()},
        protected_legacy_sha256=protected)
    (ROOT / SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if not k.endswith('sha256')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
