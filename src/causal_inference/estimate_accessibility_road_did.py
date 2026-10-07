"""Approved30min road cohort/month contrasts;15/45min sensitivity, no new filters.

Run from root. Reuse original HESTA and approved estimator functions, new output
namespace only. Historical dates stay historical; current road graph stays fixed.
"""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.causal_inference import estimate_accessibility_cohort_time as estimator
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.register_road_did_outputs import register

CONFIG = 'config/accessibility_road_did_execution.json'
SOURCE = 'DERIVED_ACCESSIBILITY_ROAD_DID_2026'
PREFIX = 'accessibility_road_did'
GROUPS = 'data_processed/accessibility_station_groups.csv'
HISTORY = 'data_processed/magic_pass_membership_history.csv'
COLLECTION = 'reports/accessibility_road_stop_corrected_collection_summary.json'
MANIFEST = f'reports/{PREFIX}_summary.json'
REPORT = 'reports/91_DID_ROUTIER_30MIN_SENSIBILITES_FR.md'
FIGURE = f'reports/{PREFIX}_dynamic.png'


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def group_reference(pairs, groups):
    keys = ['municipality_bfs_id', 'station_group_id']
    if pairs.duplicated(['municipality_bfs_id', 'access_point_id']).any():
        raise ValueError('Duplicate access pair')
    ordered = pairs.sort_values(keys+['road_reference_minutes', 'access_point_id'], na_position='last')
    result = ordered.drop_duplicates(keys)[keys+['access_point_id', 'road_reference_minutes']].copy()
    result = result.merge(groups[['station_group_id', 'station_group_name', 'first_effective_month']], validate='many_to_one')
    counts = pairs.groupby(keys).road_reference_minutes.agg(['size', 'count']).reset_index()
    counts['unusable_access_count'] = counts['size']-counts['count']
    result = result.merge(counts[keys+['unusable_access_count']], validate='one_to_one')
    result['source_id'] = SOURCE
    return result


def build_exposure(reference, panel, history, thresholds):
    """Keep every territory/month; local accessibility is not a commune filter."""
    panel = panel.copy()
    panel['date'] = pd.to_datetime(panel.date)
    if panel.duplicated(['municipality_bfs_id', 'date']).any():
        raise ValueError('Duplicate original territory/month')
    exits = {'MP_GROUP_RESORT__'+r.candidate_resort_id: pd.Timestamp(str(r.exit_date)[:7]+'-01')
             for r in history[history.event_type.eq('base_pass_exit')].itertuples()}
    reference = reference.copy()
    reference['start'] = pd.to_datetime(reference.first_effective_month).clip(lower=panel.date.min())
    reference['last'] = reference.station_group_id.map(exits).fillna(panel.date.max())
    eligible = reference.road_reference_minutes.notna() & reference.start.le(reference['last']) & reference.start.le(panel.date.max())
    monthly, inventory = [], []
    for threshold in thresholds:
        links = reference[eligible & reference.road_reference_minutes.le(threshold)]
        by_unit = {bfs: part for bfs, part in links.groupby('municipality_bfs_id')}
        for bfs, unit in panel.groupby('municipality_bfs_id', sort=True):
            nearby = by_unit.get(bfs, links.iloc[:0])
            first = nearby.start.min() if len(nearby) else pd.NaT
            unknown = reference[reference.municipality_bfs_id.eq(bfs) & reference.road_reference_minutes.isna()
                & reference.start.le(reference['last']) & reference.start.le(panel.date.max())]
            unknown_entry = unknown.start.min() if len(unknown) else pd.NaT
            indeterminate = pd.notna(unknown_entry) and (pd.isna(first) or unknown_entry < first)
            status = 'indeterminate_access_or_earlier_entry' if indeterminate else 'known_exposed_candidate' if pd.notna(first) else 'no_known_threshold_exposure'
            out = unit[['municipality_bfs_id', 'municipality_name_source', 'date', 'hotel_overnights',
                'log_overnights', 'source_id', 'source_municipality_bfs_id', 'territorial_source_bfs_ids']].copy()
            out['threshold_minutes'] = threshold
            out['first_exposure_month'] = first
            out['exposure_assignment_status'] = status
            active = np.zeros(len(unit), dtype=int)
            new = np.zeros(len(unit), dtype=int)
            nearest = np.full(len(unit), np.inf)
            for row in nearby.itertuples():
                mask = (unit.date.ge(row.start) & unit.date.le(row.last)).to_numpy()
                active += mask
                new += unit.date.eq(row.start).to_numpy()
                nearest[mask] = np.minimum(nearest[mask], row.road_reference_minutes)
            nearest[np.isinf(nearest)] = np.nan
            out['active_station_group_count'] = active
            out['new_station_group_entry_count'] = new
            out['nearest_active_group_minutes'] = nearest
            out['accessibility_source_id'] = SOURCE
            monthly.append(out)
            inventory.append(dict(threshold_minutes=threshold, municipality_bfs_id=int(bfs),
                municipality_name=unit.municipality_name_source.iloc[-1], first_exposure_month=first,
                qualifying_group_count=len(nearby), observed_post_months=int(unit.loc[unit.date.ge(first), 'hotel_overnights'].notna().sum()) if pd.notna(first) else 0,
                unusable_access_count=int(reference.loc[reference.municipality_bfs_id.eq(bfs), 'unusable_access_count'].sum()),
                earliest_unknown_group_entry_month=unknown_entry, exposure_assignment_status=status,
                source_id=SOURCE))
    return pd.concat(monthly, ignore_index=True), pd.DataFrame(inventory)


def comparison_universe(inventory, observed_end):
    """Same approved never/not-yet donor rule, reconstructed for each road threshold."""
    rows = []
    for threshold, unit in inventory.groupby('threshold_minutes'):
        first = pd.to_datetime(unit.first_exposure_month)
        anchors = sorted(first[first.le(observed_end)].dropna().unique())
        # Missing access is neither evidence for never exposed nor permission
        # to ignore an unknown group entering earlier than a known reachable one.
        unresolved = unit.exposure_assignment_status.eq('indeterminate_access_or_earlier_entry')
        if unresolved.any():
            raise ValueError('Unknown access/earlier exposure requires researcher validation: '+str(unit.loc[unresolved, 'municipality_bfs_id'].tolist()))
        for anchor in anchors:
            anchor = pd.Timestamp(anchor)
            for row in unit.itertuples():
                date = pd.Timestamp(row.first_exposure_month) if pd.notna(row.first_exposure_month) else pd.NaT
                treated = date == anchor
                never = pd.isna(date)
                not_yet = pd.notna(date) and date > anchor
                role = 'treated_in_focal_cohort' if treated else 'donor_never_exposed' if never else 'donor_not_yet_exposed' if not_yet else 'excluded_already_exposed'
                rows.append(dict(threshold_minutes=int(threshold), focal_cohort_month=anchor.strftime('%Y-%m-%d'),
                    municipality_bfs_id=row.municipality_bfs_id, municipality_name=row.municipality_name,
                    first_exposure_month=date, treated_in_focal_cohort=treated,
                    primary_donor_candidate_at_anchor=never or not_yet,
                    sensitivity_never_exposed_donor_candidate=never,
                    primary_donor_use_end_exclusive=date.strftime('%Y-%m-%d') if not_yet else '',
                    primary_comparison_role=role, source_id=SOURCE))
    return pd.DataFrame(rows)


FIELDS = {
    'threshold_minutes': ('Inclusive mean driving-time maximum;30 primary,15/45 sensitivity, approved2026-10-07', 'minutes'),
    'first_exposure_month': ('Earliest active historical Magic Pass group entry reachable under this current road threshold; not a contemporary entry date', 'calendar month'),
    'earliest_unknown_group_entry_month': ('Earliest historical entry of a group whose road access mean is unusable; may predate known first exposure', 'calendar month'),
    'exposure_assignment_status': ('Known exposed candidate, no known threshold exposure, or indeterminate because an unusable access may imply an earlier exposure', 'category'),
    'qualifying_group_count': ('Number of unchanged groups with at least one usable access at or below threshold and active in panel period', 'count'),
    'observed_post_months': ('Nonmissing original HESTA months from first exposure through observed end; no censoring of subsequent group entries', 'count'),
    'unusable_access_count': ('Count of access pairs without usable bidirectional mean; retained as uncertainty, not automatically excluded', 'count'),
    'active_station_group_count': ('Count of threshold-reachable groups active in this calendar month, honoring existing documented exit convention', 'count'),
    'new_station_group_entry_count': ('Count of threshold-reachable groups entering in this month; full successive-entry trajectory retained', 'count'),
    'nearest_active_group_minutes': ('Shortest usable access reference among historically active groups inside the approved threshold; missing if none', 'minutes'),
    'accessibility_source_id': ('Provenance of derived road-threshold exposure, separate from original HESTA outcome source_id', 'identifier'),
}


def plot(dynamic):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
    for ax, threshold in zip(axes, [15, 30, 45]):
        curve = dynamic[(dynamic.threshold_minutes.eq(threshold)) & dynamic.variant.eq('primary')].sort_values('event_month')
        ax.fill_between(curve.event_month.to_numpy(), curve.simultaneous_lower_95.to_numpy(), curve.simultaneous_upper_95.to_numpy(), color='#4477aa', alpha=.18, label='Bande simultanée 95 %')
        ax.plot(curve.event_month, curve.estimate_log_points, color='#225588', lw=1.5, label='Contraste DiD')
        ax.axhline(0, color='black', lw=.7)
        ax.axvline(0, color='#aa4444', ls='--', lw=1)
        ax.set_title(f'{threshold} min'+(' — principal' if threshold == 30 else ' — sensibilité'))
        ax.set_xlabel('Mois depuis la première exposition')
        ax.grid(alpha=.15)
    axes[0].set_ylabel('Différence de changements de log(1 + nuitées)')
    axes[1].legend(fontsize=8, loc='best')
    fig.suptitle('Référence automobile : contrastes exploratoires, non certifiés causaux', fontsize=11)
    fig.tight_layout()
    fig.savefig(ROOT / FIGURE, dpi=160)
    plt.close(fig)


def make_report(summaries, dynamic, inventory, support):
    lines = ['# DiD avec référence automobile', '', '7 octobre 2026. **30 minutes au principal ;15 et45 minutes en sensibilité**, seuils validés. Même estimateur et paramètres que les tests précédents, nouvelles dates d’exposition et nouveaux témoins. Les résultats TP et la première matrice automobile restent intacts.', '',
        '## Couverture et correction', '', 'Le point communal de Lauterbrunnen est désormais l’arrêt officiel **Lauterbrunnen8507384**, et non Grütschalp8507378. Six nouvelles matrices mesurent150 directions/75 couples ; les autres184 communes réutilisent leurs observations. Les trois zéros locaux approuvés restent utilisables ; le zéro distinct-point Saas-Fee reste manquant. Aucun arrêt de station ni groupe n’est modifié.', '',
        '| Seuil | Exposées dans l’inventaire | Calibration/référence disponibles | Mois postérieurs effectivement utilisés |', '|---:|---:|---:|---:|']
    for t in [15, 30, 45]:
        s = summaries[str(t)]
        lines.append(f"| {t} min | {s['exposed_territories']} | {s['calculable_exposed_territories']} | {s['primary_observed_post_pairs']} |")
    laut = inventory[inventory.municipality_bfs_id.eq(584)].sort_values('threshold_minutes')
    lines += ['', 'Lauterbrunnen : '+ '; '.join(f"{int(r.threshold_minutes)}min : "+(f"première exposition {pd.Timestamp(r.first_exposure_month):%Y-%m}" if pd.notna(r.first_exposure_month) else 'aucune exposition calculée au seuil') for r in laut.itertuples())+'.', '',
        'Les185 territoires restent dans l’inventaire. Une exposition au seuil ne garantit pas un historique hôtelier utilisable : les communes sans calibration/référence restent listées dans les tables de support, sans imputation. Les mois après une nouvelle entrée de station restent présents.', '',
        '## Contrastes principaux', '', 'Unités : points logarithmiques sur log(1+nuitées), **pas des nuitées supplémentaires ni directement des pourcentages**. Référence : mois−1. Les compositions peuvent changer avec le mois relatif.', '',
        '| Seuil | Mois relatif | Communes traitées observées | Contraste | IC ponctuel95 % | Bande simultanée95 % |', '|---:|---:|---:|---:|---:|---:|']
    for t in [15, 30, 45]:
        for k in [0, 11, 23]:
            selected = dynamic[dynamic.threshold_minutes.eq(t) & dynamic.variant.eq('primary') & dynamic.event_month.eq(k)]
            if len(selected):
                r = selected.iloc[0]
                lines.append(f'| {t} | {k} | {int(r.treated_observed_count)} | {r.estimate_log_points:.3f} | [{r.pointwise_lower_95:.3f} ; {r.pointwise_upper_95:.3f}] | [{r.simultaneous_lower_95:.3f} ; {r.simultaneous_upper_95:.3f}] |')
    lines += ['', '## Diagnostics et sensibilités', '']
    for t in [15, 30, 45]:
        s = summaries[str(t)]
        lines.append(f"- {t}min : {s['pre_months_simultaneous_excluding_zero']}/{s['pre_months_calculable']} mois prétraitement et {s['post_months_simultaneous_excluding_zero']}/{s['post_months_calculable']} mois postérieurs ont une bande simultanée excluant zéro. Ce décompte n’est pas un test global de tendances parallèles.")
    lines += ['', 'Toutes les variantes précédentes sont recalculées à chaque seuil : témoins jamais exposés seulement, soustraction de pente prétraitement, omission des contrastes COVID de mars2020 à mars2022, horizons communs6/12/24 mois et mêmes territoires à ces trois horizons. Aucun coefficient post global ni effet propre d’une entrée additionnelle n’est ajouté. Les tables publient tous les mois, pas seulement ceux du tableau.', '',
        '## Méthode, sources et limites', '',
        'Accessibilité : moyenne aller/retour automobile statique, puis accès le plus rapide disponible de chaque groupe et seuil inclusif. Exposition : première entrée historique d’un groupe accessible ; réseau complet conservé avec les sorties documentées selon la convention existante. Chaque seuil reconstruit ses cohortes et ses témoins, sans zone tampon ou filtre géographique nouveau.', '',
        'Calcul : changements depuis−1 chez les exposées moins ceux des témoins jamais/pas encore exposés ; ces derniers cessent de contribuer à leur première entrée. Correction saisonnière estimée sur les36 mois précédents, pente soustraite uniquement en sensibilité. Pondérations égales par territoire, pondération dynamique par effectifs traités observés. Bootstrap multiplicateur territorial4 999 tirages, graine20261005, mêmes paramètres qu’avant. Bandes simultanées par courbe/variante, pas conjointement entre seuils.', '',
        'Sources déjà enregistrées : HESTA OFS, historique officiel Magic Pass, BAV/OFT et matrices HeiGIT/OpenStreetMap archivées. Décision et fichiers : `config/accessibility_road_did_execution.json`, `accessibility_road_stop_corrected_collection_summary.json`, sources/dictionnaire metadata. La comparaison avec le point TP d’origine n’est plus à extrémité identique pour Lauterbrunnen, exception explicitement validée. Raccordement au réseau dans les tables `accessibility_road_stop_corrected_snapping_*` ; grand raccordement, lieux sans voitures et restrictions hivernales restent signalés sans exclusion.', '',
        'Le réseau routier2026 est tenu fixe historiquement. Temps modélisés sans congestion, marche finale ou supplément neige/parking. Les communes au-delà du seuil ne sont pas certifiées sans retombées ; déplacer le seuil change à la fois les communes traitées, les dates et les témoins. Tendances préalables, chocs hôteliers/COVID et changements de composition limitent l’interprétation. Ce pipeline est un contraste Python spécifique au projet, pas l’exécution du package R did ni une certification causale.', '',
        'Reprise : `.venv/Scripts/python.exe src/causal_inference/estimate_accessibility_road_did.py`. Résultats séparés par seuil (`accessibility_road_did_15min/30min/45min_*`), exposition mensuelle, inventaire, univers de témoins, figure et empreintes dans `accessibility_road_did_summary.json`. Les étapes achevées sont réutilisées si leurs entrées et sorties sont inchangées ; aucune collecte routière n’est relancée.', '']
    return '\n'.join(lines)


def main():
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf-8'))
    execution = json.loads((ROOT / config['approved_estimator_execution']).read_text(encoding='utf-8'))
    parameters = json.loads((ROOT / config['approved_estimator_parameters']).read_text(encoding='utf-8'))['proposed_parameters_not_approved']
    if not execution['parameter_bundle_approved'] or config['principal_threshold_minutes'] != 30 or config['sensitivity_thresholds_minutes'] != [15, 45]:
        raise ValueError('Approved execution/thresholds differ')
    collection = json.loads((ROOT / COLLECTION).read_text(encoding='utf-8'))
    for p, value in {**collection['output_sha256'], **collection['input_sha256'], **collection['protected_legacy_sha256']}.items():
        if sha(p) != value:
            raise ValueError('Changed correction input/output/protected source: '+p)
    protected = collection['protected_legacy_sha256'].copy()
    # Previous estimates/exposures are protected as well as original road data.
    legacy = list((ROOT / 'reports').glob('accessibility_cohort_time_estimation_*.csv'))
    legacy += [ROOT / 'reports/accessibility_cohort_time_estimation_summary.json', ROOT / 'reports/82_ESTIMATION_COHORTES_MOIS_OPTION_A_FR.md']
    protected.update({p.relative_to(ROOT).as_posix(): sha(p.relative_to(ROOT).as_posix()) for p in legacy})
    inputs = [CONFIG, COLLECTION, config['corrected_road_pairs'], config['outcome_panel'], GROUPS, HISTORY,
        config['approved_estimator_execution'], config['approved_estimator_parameters'], config['approved_comparison_rule'],
        config['historical_network_trajectory'], 'src/causal_inference/estimate_accessibility_cohort_time.py',
        'src/causal_inference/estimate_accessibility_road_did.py']
    checks = {p: sha(p) for p in inputs}
    previous = json.loads((ROOT / MANIFEST).read_text(encoding='utf-8')) if (ROOT / MANIFEST).exists() else None
    if previous:
        for p, value in previous['output_sha256'].items():
            if sha(p) != value:
                raise ValueError('Preserve edited road DiD output: '+p)
    panel = pd.read_csv(ROOT / config['outcome_panel'], low_memory=False)
    panel['date'] = pd.to_datetime(panel.date)
    pairs = pd.read_csv(ROOT / config['corrected_road_pairs'])
    groups = pd.read_csv(ROOT / GROUPS)
    history = pd.read_csv(ROOT / HISTORY)
    reference = group_reference(pairs, groups)
    monthly, inventory = build_exposure(reference, panel, history, [15, 30, 45])
    universe = comparison_universe(inventory, panel.loc[panel.hotel_overnights.notna(), 'date'].max())
    frames = {PREFIX+'_group_reference': reference, PREFIX+'_monthly_exposure': monthly,
        PREFIX+'_inventory': inventory, PREFIX+'_comparison_universe': universe}
    paths = {table: ('data_processed/' if table.endswith(('group_reference', 'monthly_exposure')) else 'reports/')+table+'.csv' for table in frames}
    parents = {PREFIX+'_group_reference': ['accessibility_road_stop_pairs', 'accessibility_station_groups'],
        PREFIX+'_monthly_exposure': ['accessibility_municipality_month_exposure_territorial'],
        PREFIX+'_inventory': ['accessibility_cohort_time_estimation_territory_support'],
        PREFIX+'_comparison_universe': ['accessibility_cohort_comparison_universe_territorial']}
    for table, frame in frames.items():
        write_csv(frame, ROOT / paths[table])
    estimator.SOURCE = SOURCE
    summaries, dynamic_frames, support_frames = {}, [], []
    for threshold in [30, 15, 45]:
        stem = f'{PREFIX}_{threshold}min'
        checkpoint = ROOT / f'reports/{stem}_summary.json'
        old = json.loads(checkpoint.read_text(encoding='utf-8')) if checkpoint.exists() else None
        if old:
            for p, value in old['output_sha256'].items():
                if sha(p) != value:
                    raise ValueError('Preserve edited completed threshold: '+p)
        if old and old['input_sha256'] == checks:
            result = [pd.read_csv(ROOT / f'reports/{stem}_{label}.csv') for label in ['cohort_month', 'dynamic', 'calibration', 'territory_support']]
            print(f'Reused verified {threshold}min estimation.', flush=True)
        else:
            print(f'Calculating {threshold}min with unchanged approved cohort-month estimator...', flush=True)
            result = estimator.calculate(panel, universe[universe.threshold_minutes.eq(threshold)], execution, parameters)
        cohort, dynamic, calibration, support = result
        for label, frame in zip(['cohort_month', 'dynamic', 'calibration', 'territory_support'], result):
            table = stem+'_'+label
            frame['threshold_minutes'] = threshold
            frames[table] = frame
            paths[table] = f'reports/{table}.csv'
            parents[table] = ['accessibility_cohort_time_estimation_'+label]
            write_csv(frame, ROOT / paths[table])
        primary = dynamic[dynamic.variant.eq('primary')]
        def nonzero(part):
            return int((part.simultaneous_lower_95.gt(0) | part.simultaneous_upper_95.lt(0)).sum())
        before = primary[primary.event_month.lt(-1) & primary.estimate_log_points.notna()]
        after = primary[primary.event_month.ge(0) & primary.estimate_log_points.notna()]
        summary = dict(threshold_minutes=threshold, exposed_territories=len(support),
            calculable_exposed_territories=int(support.calculable.sum()),
            inventory_observed_post_months=int(support.inventory_observed_post_months.sum()),
            primary_observed_post_pairs=int(cohort.loc[cohort.variant.eq('primary') & cohort.event_month.ge(0) & cohort.status.eq('calculable'), 'treated_observed_count'].sum()),
            pre_months_calculable=len(before), pre_months_simultaneous_excluding_zero=nonzero(before),
            post_months_calculable=len(after), post_months_simultaneous_excluding_zero=nonzero(after),
            common_horizon_territories={str(h): int(support[f'common_{h}_months'].sum()) for h in [6, 12, 24]},
            same_territories_all_horizons=int(support.same_territories_6_12_24.sum()),
            incomplete_history_ids=support.loc[~support.calculable, 'municipality_bfs_id'].astype(int).tolist(),
            input_sha256=checks, output_sha256={paths[stem+'_'+label]: sha(paths[stem+'_'+label]) for label in ['cohort_month', 'dynamic', 'calibration', 'territory_support']},
            estimation_executed=True, causal_certification=False)
        checkpoint.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        summaries[str(threshold)] = summary
        dynamic_frames.append(dynamic)
        support_frames.append(support)
        print(json.dumps({k: summary[k] for k in ['threshold_minutes', 'exposed_territories', 'calculable_exposed_territories', 'primary_observed_post_pairs', 'pre_months_simultaneous_excluding_zero']}), flush=True)
    dynamic_all = pd.concat(dynamic_frames, ignore_index=True)
    plot(dynamic_all)
    (ROOT / REPORT).write_text(make_report(summaries, dynamic_all, inventory, pd.concat(support_frames)), encoding='utf-8')
    register(SOURCE, dict(variable_name='road_threshold_exposure_and_cohort_month_contrasts',
        variable_description='Approved static car30min primary,15/45min sensitivities, unchanged exploratory DiD estimator',
        source_organisation='Thesis research pipeline from registered HESTA, Magic Pass, BAV and HeiGIT sources',
        source_dataset_name='Road-threshold municipality exposure and exploratory cohort/month contrasts',
        local_raw_file='|'.join(inputs), processed_file='|'.join([*paths.values(), REPORT, FIGURE, MANIFEST]),
        retrieval_method='Local deterministic Python reconstruction; no collection, outcome imputation or automatic geographic filtering',
        transformation_applied='Group closest usable road reference; historical entry/exit; threshold-specific donor reconstruction; approved log1p pre36 seasonal changes,4999 Gaussian territory multiplier draws seed20261005',
        quality_notes='Current stop-to-stop road snapshot fixed historically, approved Lauterbrunnen exception. Missing access/outcomes explicit; no buffer, winter/snap exclusion or causal certification. Donor contamination and calibration/composition limits remain.'), frames, parents, FIELDS)
    if checks != {p: sha(p) for p in inputs} or protected != {p: sha(p) for p in protected}:
        raise ValueError('Inputs or protected outputs changed during calculation')
    manifest = dict(status='completed_approved_exploratory_road_did', principal_threshold_minutes=30,
        sensitivity_thresholds_minutes=[15, 45], municipality_territories=int(panel.municipality_bfs_id.nunique()),
        station_groups=int(reference.station_group_id.nunique()), bootstrap_repetitions=execution['bootstrap_repetitions'],
        bootstrap_seed=execution['bootstrap_seed'], thresholds=summaries, input_sha256=checks,
        output_sha256={p: sha(p) for p in [*paths.values(), REPORT, FIGURE]}, protected_legacy_sha256=protected,
        runtime_versions=dict(python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__),
        causal_certification=False, canonical_tp_exposure_changed=False, global_post_coefficient_selected=False)
    (ROOT / MANIFEST).write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('All approved road thresholds complete; old TP and uncorrected car results unchanged.', flush=True)


if __name__ == '__main__':
    main()
