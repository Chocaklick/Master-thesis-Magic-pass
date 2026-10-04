"""Descriptive audit of every approved territorial candidate; never a sample filter."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config/accessibility_all_cohort_comparability_audit.json"
BRIDGE_CONFIG = ROOT / "config/accessibility_outcome_territorial_harmonisation.json"
SOURCE_ID = "DERIVED_ACCESSIBILITY_ALL_COHORT_COMPARABILITY_AUDIT"
REVIEW_PATHS = [ROOT / f"reports/{name}.csv" for name in [
    "accessibility_treated_external_shock_evidence",
    "accessibility_high_leverage_control_external_shock_evidence",
    "accessibility_remaining_control_external_shock_evidence",
]]


def truth(values: pd.Series) -> pd.Series:
    return values.astype(str).str.lower().eq("true")


def trend(values: np.ndarray, dates: pd.DatetimeIndex) -> tuple[float, str]:
    valid = np.isfinite(values)
    dates = dates[valid]
    values = values[valid]
    if not len(values):
        return np.nan, "no_observed_pre_values"
    time = (dates.year * 12 + dates.month).to_numpy(dtype=float)
    time -= time.mean()
    months = dates.month.to_numpy()
    matrix = np.column_stack([np.ones(len(values)), time, *[(months == m).astype(float) for m in range(2, 13)]])
    beta, _, rank, _ = np.linalg.lstsq(matrix, values, rcond=None)
    if rank != matrix.shape[1] or len(values) <= rank:
        return np.nan, "insufficient_calendar_rank_or_residual_degrees_of_freedom"
    return float(beta[1]), "descriptive_full_rank_not_parallel_trends_approval"


def paired_metrics(left: np.ndarray, right: np.ndarray, dates: pd.DatetimeIndex) -> dict:
    valid = np.isfinite(left) & np.isfinite(right)
    a, b, paired_dates = left[valid], right[valid], dates[valid]
    if len(a) >= 2 and np.std(a) > 0 and np.std(b) > 0:
        correlation = float(np.corrcoef(a, b)[0, 1])
        standardised_rmse = float(np.sqrt(np.mean(((a-a.mean())/a.std() - (b-b.mean())/b.std())**2)))
    else:
        correlation = standardised_rmse = np.nan
    profile = pd.DataFrame({"month": paired_dates.month, "left": a, "right": b}).groupby("month").mean()
    seasonal_rmse = float(np.sqrt(np.mean(((profile.left-profile.left.mean()) - (profile.right-profile.right.mean()))**2))) if len(profile) == 12 else np.nan
    slope, status = trend(left-right, dates)
    return {
        "paired_pre_observed_months": int(valid.sum()),
        "paired_pre_complete": bool(valid.all()),
        "pre_log_outcome_correlation": correlation,
        "pre_standardised_outcome_rmse": standardised_rmse,
        "pre_seasonal_profile_rmse": seasonal_rmse,
        "seasonal_profile_calendar_months": len(profile),
        "seasonally_adjusted_monthly_difference_trend": slope,
        "trend_diagnostic_status": status,
    }


def review_context(reviews: pd.DataFrame, bfs_id: int) -> dict:
    local = reviews.loc[reviews.municipality_bfs_id.eq(bfs_id)]
    def joined(column: str) -> str:
        return " | ".join(local[column].dropna().astype(str).drop_duplicates()) if column in local else ""
    return {
        "existing_shock_review_available": not local.empty,
        "existing_shock_review_rows": len(local),
        "existing_shock_review_status": joined("review_status"),
        "existing_shock_review_severity": joined("shock_severity"),
        "existing_shock_review_timing": joined("shock_timing"),
        "existing_shock_review_source_ids": joined("review_source_ids"),
        "existing_shock_review_evidence": joined("evidence_note"),
        "existing_shock_review_limits": joined("review_limits") if not local.empty else "No existing review; absence of a documented shock is not established",
        "existing_shock_review_origin_tables": joined("review_origin_table"),
        "existing_shock_review_applicable_to_focal_window_validated": False,
        "former_pilot_design_decisions_applied": False,
    }


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not config["researcher_approved_descriptive_audit"] or config["automatic_exclusion_applied"]:
        raise ValueError("Only the approved non-selective audit is permitted")
    bridge = json.loads(BRIDGE_CONFIG.read_text(encoding="utf-8"))
    panel_path, universe_path = ROOT / bridge["analytical_panel"], ROOT / bridge["comparison_universe"]
    panel = pd.read_csv(panel_path, low_memory=False)
    panel["date"] = pd.to_datetime(panel.date)
    universe = pd.read_csv(universe_path)
    reviews = pd.concat([pd.read_csv(path).assign(review_origin_table=path.stem) for path in REVIEW_PATHS], ignore_index=True)
    reviews["municipality_bfs_id"] = reviews.municipality_bfs_id.replace({700: 6831})
    by_unit = {int(bfs): rows.set_index("date").sort_index() for bfs, rows in panel.groupby("municipality_bfs_id")}
    contexts = {bfs: review_context(reviews, bfs) for bfs in by_unit}
    coverage_rows, pair_rows = [], []
    for cohort, local in universe.groupby("focal_cohort_month", sort=True):
        anchor = pd.Timestamp(cohort)
        treated = local.loc[truth(local.treated_in_focal_cohort)].sort_values("municipality_bfs_id")
        donors = local.loc[truth(local.primary_donor_candidate_at_anchor)].sort_values("municipality_bfs_id")
        dates = pd.date_range(anchor-pd.DateOffset(months=config["pair_diagnostic_window_months"]), anchor-pd.DateOffset(months=1), freq="MS")
        donor_logs = {int(row.municipality_bfs_id): by_unit[int(row.municipality_bfs_id)].reindex(dates).log_overnights.to_numpy(dtype=float) for row in donors.itertuples()}
        donor_beds = {int(row.municipality_bfs_id): by_unit[int(row.municipality_bfs_id)].reindex(dates).hotel_beds_available for row in donors.itertuples()}
        for unit in treated.itertuples():
            bfs = int(unit.municipality_bfs_id)
            source = by_unit[bfs]
            context = contexts[bfs]
            for horizon in config["diagnostic_pre_windows_months"]:
                window_dates = pd.date_range(anchor-pd.DateOffset(months=horizon), anchor-pd.DateOffset(months=1), freq="MS")
                pre = source.reindex(window_dates)
                slope, status = trend(pre.log_overnights.to_numpy(dtype=float), window_dates)
                beds = pre.hotel_beds_available
                yoy = beds / beds.shift(12).replace(0, np.nan) - 1
                observed = pre.hotel_overnights.notna()
                coverage_rows.append({
                    "municipality_bfs_id": bfs, "municipality_name": unit.municipality_name,
                    "focal_cohort_month": cohort, "diagnostic_pre_window_months": horizon,
                    "diagnostic_pre_start": window_dates.min().strftime("%Y-%m-%d"),
                    "diagnostic_pre_end": window_dates.max().strftime("%Y-%m-%d"),
                    "observed_pre_outcome_months": int(observed.sum()),
                    "complete_pre_outcome_window": bool(observed.all()),
                    "observed_pre_seasonal_calendar_months": int(window_dates[observed].month.nunique()),
                    "pre_mean_hotel_overnights": pre.hotel_overnights.mean(),
                    "pre_median_hotel_overnights": pre.hotel_overnights.median() if observed.any() else np.nan,
                    "pre_seasonally_adjusted_log_trend_monthly": slope,
                    "pre_trend_diagnostic_status": status,
                    "pre_observed_hotel_capacity_months": int(beds.notna().sum()),
                    "pre_median_hotel_beds_available": beds.median() if beds.notna().any() else np.nan,
                    "pre_median_hotel_establishments_open": pre.hotel_establishments_open.median() if pre.hotel_establishments_open.notna().any() else np.nan,
                    "pre_largest_absolute_yoy_bed_change": yoy.abs().max(),
                    "pre_bed_yoy_comparisons": int(yoy.notna().sum()),
                    "pre_covid_overlap_calendar_months": int(window_dates.to_series().between("2020-03-01", "2022-03-01").sum()),
                    "primary_donor_candidate_count": len(donors),
                    **context,
                    "automatic_exclusion_applied": False, "analysis_sample_selected": False,
                    "estimator_selected": False, "causal_estimation_approved": False,
                    "source_id": SOURCE_ID,
                })
            treated_log = source.reindex(dates).log_overnights.to_numpy(dtype=float)
            treated_beds = source.reindex(dates).hotel_beds_available
            for donor in donors.itertuples():
                control = int(donor.municipality_bfs_id)
                control_beds = donor_beds[control]
                capacity_overlap = treated_beds.notna() & control_beds.notna()
                a = treated_beds.loc[capacity_overlap].median() if capacity_overlap.any() else np.nan
                b = control_beds.loc[capacity_overlap].median() if capacity_overlap.any() else np.nan
                control_context = contexts[control]
                pair_rows.append({
                    "focal_cohort_month": cohort, "treated_municipality_bfs_id": bfs,
                    "treated_municipality_name": unit.municipality_name,
                    "control_municipality_bfs_id": control, "control_municipality_name": donor.municipality_name,
                    "primary_donor_role": donor.primary_comparison_role,
                    "primary_donor_use_end_exclusive": donor.primary_donor_use_end_exclusive,
                    "diagnostic_pre_window_months": len(dates),
                    "diagnostic_pre_start": dates.min().strftime("%Y-%m-%d"), "diagnostic_pre_end": dates.max().strftime("%Y-%m-%d"),
                    **paired_metrics(treated_log, donor_logs[control], dates),
                    "paired_pre_capacity_observed_months": int(capacity_overlap.sum()),
                    "paired_pre_median_treated_beds": a, "paired_pre_median_control_beds": b,
                    "paired_pre_median_bed_ratio_treated_to_control": a/b if pd.notna(b) and b > 0 else np.nan,
                    "treated_existing_shock_review_available": context["existing_shock_review_available"],
                    "control_existing_shock_review_available": control_context["existing_shock_review_available"],
                    "control_existing_shock_review_status": control_context["existing_shock_review_status"],
                    "control_existing_shock_review_source_ids": control_context["existing_shock_review_source_ids"],
                    "shock_review_applicable_to_focal_window_validated": False,
                    "former_pilot_design_decisions_applied": False,
                    "automatic_exclusion_applied": False, "analysis_sample_selected": False,
                    "estimator_selected": False, "causal_estimation_approved": False, "source_id": SOURCE_ID,
                })
    coverage = pd.DataFrame(coverage_rows)
    pairs = pd.DataFrame(pair_rows)
    cohorts = []
    for cohort, local in pairs.groupby("focal_cohort_month", sort=True):
        cov = coverage.loc[coverage.focal_cohort_month.eq(cohort) & coverage.diagnostic_pre_window_months.eq(36)]
        cohorts.append({
            "focal_cohort_month": cohort, "exposed_territories": int(cov.municipality_bfs_id.nunique()),
            "candidate_pairs_audited": len(local), "pairs_with_any_observed_pre_overlap": int(local.paired_pre_observed_months.gt(0).sum()),
            "pairs_with_complete_36_month_pre_overlap": int(local.paired_pre_complete.sum()),
            "pairs_with_full_rank_differential_trend": int(local.seasonally_adjusted_monthly_difference_trend.notna().sum()),
            "median_pair_log_correlation": float(local.pre_log_outcome_correlation.median()),
            "median_absolute_monthly_differential_log_trend": float(local.seasonally_adjusted_monthly_difference_trend.abs().median()),
            "pre_36_covid_overlap_calendar_months": int(cov.pre_covid_overlap_calendar_months.max()),
            "treated_with_existing_shock_review": int(cov.existing_shock_review_available.sum()),
            "donors_with_existing_shock_review": int(local.loc[local.control_existing_shock_review_available].control_municipality_bfs_id.nunique()),
        })
    summary = {
        "specification_version": config["specification_version"], "source_id": SOURCE_ID,
        "analytical_grain": "approved_territorial_panel_one_moutier_unit",
        "exposed_territories_retained": int(coverage.municipality_bfs_id.nunique()),
        "coverage_rows": len(coverage), "candidate_pairs_audited": len(pairs),
        "diagnostic_windows": [{"pre_months": int(h), "territories_with_complete_pre_window": int(g.complete_pre_outcome_window.sum()), "territories_with_full_rank_trend": int(g.pre_seasonally_adjusted_log_trend_monthly.notna().sum()), "territories_with_any_capacity": int(g.pre_observed_hotel_capacity_months.gt(0).sum())} for h, g in coverage.groupby("diagnostic_pre_window_months")],
        "cohort_diagnostics": cohorts,
        "existing_shock_reviews_in_exposed_territories": int(coverage.loc[coverage.diagnostic_pre_window_months.eq(36)].existing_shock_review_available.sum()),
        "paired_pre_capacity_ratio_distribution": {
            "observed_candidate_pairs": int(pairs.paired_pre_median_bed_ratio_treated_to_control.notna().sum()),
            "q25": float(pairs.paired_pre_median_bed_ratio_treated_to_control.quantile(0.25)),
            "median": float(pairs.paired_pre_median_bed_ratio_treated_to_control.median()),
            "q75": float(pairs.paired_pre_median_bed_ratio_treated_to_control.quantile(0.75)),
        },
        "shock_scope_warning": "Existing reviews concern the former founding-cohort pilot around 2017; no new window-specific validation or negative proof is inferred",
        "automatic_exclusion_applied": False, "matching_rule_selected": False,
        "analysis_sample_selected": False, "estimator_selected": False, "causal_estimation_approved": False,
        "input_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in [CONFIG, BRIDGE_CONFIG, panel_path, universe_path, *REVIEW_PATHS]},
    }
    if summary["exposed_territories_retained"] != 79 or len(coverage) != 316:
        raise ValueError("All 79 territorial candidates must remain in all four diagnostic windows")
    coverage.to_csv(ROOT / "reports/accessibility_all_cohort_comparability_municipalities.csv", index=False, lineterminator="\n")
    pairs.to_csv(ROOT / "reports/accessibility_all_cohort_comparability_pairs.csv", index=False, lineterminator="\n")
    (ROOT / "reports/accessibility_all_cohort_comparability_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = ["# Comparabilité descriptive de toutes les cohortes — étape 29c", "",
        "Audit approuvé, sans filtre automatique ni choix d'estimateur. Les 79 territoires exposés restent recensés ; Moutier est une seule unité. Aucune commune n'est déclarée comparable ou exclue par un seuil.", "",
        "## Disponibilité avant entrée", "", "| Fenêtre diagnostique | Nuitées complètes | Tendance estimable algébriquement | Capacité disponible au moins un mois |", "|---|---:|---:|---:|"]
    for item in summary["diagnostic_windows"]:
        lines.append(f"| {item['pre_months']} mois | {item['territories_with_complete_pre_window']}/79 | {item['territories_with_full_rank_trend']}/79 | {item['territories_with_any_capacity']}/79 |")
    lines += ["", "Les historiques préexposition de Blonay–Saint-Légier, Val de Bagnes et Laténa restent manquants. Les fenêtres servent à diagnostiquer la couverture, pas à fixer la fenêtre d'estimation. Une seule année ou moins ne permet pas de séparer une tendance linéaire des effets propres aux douze mois.", "",
        "## Comparaison avec tous les témoins autorisés", "", f"Les {len(pairs):,} couples candidats sont audités, sans classement ni top-5. Les témoins suivent l'option C : jamais ou pas encore exposés à l'entrée de la cohorte ; leur date de sortie est conservée. Les statistiques ci-dessous portent sur les 36 mois avant entrée et ne sont pas des estimations de l'effet du Magic Pass.".replace(",", " "), "",
        "| Cohorte | Communes | Couples complets sur 36 mois | Corrélation médiane | Écart de tendance absolu médian (log/mois) | Mois COVID dans le prétraitement |", "|---|---:|---:|---:|---:|---:|"]
    for row in cohorts:
        lines.append(f"| {row['focal_cohort_month'][:7]} | {row['exposed_territories']} | {row['pairs_with_complete_36_month_pre_overlap']}/{row['candidate_pairs_audited']} | {row['median_pair_log_correlation']:.3f} | {row['median_absolute_monthly_differential_log_trend']:.4f} | {row['pre_36_covid_overlap_calendar_months']} |")
    lines += ["", "Une forte corrélation peut simplement refléter une saisonnalité commune. Le CSV conserve aussi l'écart entre profils saisonniers centrés, l'erreur standardisée, le nombre réel de mois appariés, le rang de la tendance et le ratio de capacités sur les mêmes mois observés. Des tailles hôtelières différentes ou une pente différente sont des diagnostics, pas des motifs automatiques d'exclusion. Les médianes portent sur les couples calculables et peuvent masquer des cas individuels.", "",
        "## Chocs déjà documentés", "", f"{summary['existing_shock_reviews_in_exposed_territories']}/79 communes exposées disposent d'une revue externe déjà réalisée. Les autres restent non revues : cela ne signifie pas absence de choc. Les preuves et limites des anciennes revues sont reprises, mais leur période se rattache au pilote autour de 2017. Leur validité pour chaque nouvelle fenêtre n'est pas automatiquement acquise, et les anciennes décisions d'exclusion ne sont pas réappliquées.", "",
        "Les fenêtres prétraitement récentes peuvent traverser la pandémie : cette présence est comptée, sans exclusion. Une tendance prétraitement linéaire ajustée de la saisonnalité ne prouve pas que le contrefactuel restera linéaire après l'entrée.", "",
        f"La capacité varie fortement entre candidats : parmi {summary['paired_pre_capacity_ratio_distribution']['observed_candidate_pairs']} couples calculables, le ratio des lits exposé/témoin a une médiane de {summary['paired_pre_capacity_ratio_distribution']['median']:.2f}, avec un intervalle interquartile de {summary['paired_pre_capacity_ratio_distribution']['q25']:.2f} à {summary['paired_pre_capacity_ratio_distribution']['q75']:.2f}. Ce constat ne définit aucun filtre.", "",
        "## Méthode, sources et reprise", "",
        "Issue : champ existant `log_overnights = log(1 + nuitées)`, sans imputation. Corrélation et erreur standardisée utilisent les mois où les deux issues sont observées. Le profil saisonnier exige les douze mois calendaires représentés ; les années manquantes ne sont pas remplacées. La pente est une régression descriptive avec intercept, temps calendaire réel et onze indicatrices de mois, calculée seulement si le rang est complet et s'il reste des degrés de liberté. Les mois manquants ne compriment pas le temps. Aucun test de significativité ou seuil de succès n'est employé.", "",
        "La capacité provient des séries HESTA déjà intégrées : médianes prétraitement, ratio des médianes sur mois communs, variation annuelle maximale absolue des lits observés. Les changements après entrée ne sont pas utilisés pour décider de la comparabilité prétraitement. Les sommes de groupes ou pistes ne sont pas assimilées à une capacité hôtelière.", "",
        "- [Audit des communes](accessibility_all_cohort_comparability_municipalities.csv) : quatre fenêtres par commune, disponibilité, pente, capacité et preuves de chocs.",
        "- [Audit de tous les couples](accessibility_all_cohort_comparability_pairs.csv) : métriques prétraitement, identifiants, rôles et sortie des témoins.",
        "- `accessibility_all_cohort_comparability_summary.json` et `config/accessibility_all_cohort_comparability_audit.json` : résumé, règles, garde-fous et empreintes des entrées.",
        "- Sources : panel territorial HESTA et univers de comparaison approuvés au rapport 78 ; revues de chocs traités et témoins des étapes 19–21 avec leurs sources originales. Aucun téléchargement supplémentaire.", "",
        "Reproduction : `.venv/Scripts/python.exe src/causal_inference/audit_accessibility_all_cohort_comparability.py` depuis la racine. Prochaine décision : définir avec le chercheur l'estimateur par cohorte et mois, son mois de référence et les hypothèses de tendance ; un éventuel appariement ou filtre exige également un accord séparé. Aucun effet ou échantillon final n'est produit par cet audit.", "",
        "Deux orientations à discuter : comparaison des changements par cohorte et mois avec les témoins autorisés, en gardant une variante de tendance linéaire comme sensibilité ; ou tendance linéaire préestimée et saut/dynamique comme modèle principal, sous une hypothèse d'extrapolation plus forte. Dans les deux cas, il reste à valider l'ajustement de saisonnalité, la référence, la pondération, l'incertitude et le traitement des trois historiques manquants avant calcul des effets.", "",
        "Référence méthodologique déjà enregistrée : [Callaway et Sant'Anna, Difference-in-Differences with Multiple Time Periods](https://arxiv.org/abs/1803.09015v4), `CALLAWAY_SANTANNA_2021_DID`. Ce cadre traite des dates d'entrée échelonnées et d'effets hétérogènes, mais requiert toujours des hypothèses de tendances parallèles, éventuellement conditionnelles. Il ne résout pas automatiquement les écarts diagnostiqués ici. L'abstract de la version auteur a été consulté ; aucune implémentation spécifique n'est validée par cet audit.", ""]
    (ROOT / "reports/79_AUDIT_COMPARABILITE_TOUTES_COHORTES_FR.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "input_sha256"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
