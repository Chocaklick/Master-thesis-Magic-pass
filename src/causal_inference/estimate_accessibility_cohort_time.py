"""Approved exploratory cohort-month contrasts; no automatic causal certification.

Run from the project root. Original proposal/support remain historical snapshots.
CSV outputs have one typed observation per row; raw and territorial inputs immutable.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
CONFIG = ROOT / "config/accessibility_cohort_time_execution.json"
PREFIX = "accessibility_cohort_time_estimation"
SOURCE = "DERIVED_ACCESSIBILITY_COHORT_TIME_ESTIMATION"


def truth(values: pd.Series) -> np.ndarray:
    return values.astype(str).str.lower().eq("true").to_numpy()


def month_number(dates: pd.DatetimeIndex) -> np.ndarray:
    return np.asarray(dates.year * 12 + dates.month, dtype=float)


def seasonal_fit(y: np.ndarray, dates: pd.DatetimeIndex) -> dict:
    """Pre-only local fit; missing dates never compress elapsed calendar time."""
    valid = np.isfinite(y)
    time = month_number(dates)
    center = float(time.mean())
    x = np.column_stack([np.ones(len(dates)), time-center] +
                        [(dates.month == m).astype(float) for m in range(2, 13)])
    rank = int(np.linalg.matrix_rank(x[valid])) if valid.any() else 0
    n = int(valid.sum())
    if rank != 13 or n <= rank:
        return {"n": n, "rank": rank, "status": "missing_or_rank_deficient_pre36",
                "season": np.full(12, np.nan), "slope": np.nan, "intercept": np.nan}
    coef = np.linalg.lstsq(x[valid], y[valid], rcond=None)[0]
    return {"n": n, "rank": rank, "status": "calculable",
            "season": np.r_[0., coef[2:]], "slope": float(coef[1]),
            "intercept": float(coef[0])}


def contrast(delta: np.ndarray, treated: np.ndarray, donor: np.ndarray) -> tuple:
    """Difference of endpoint changes and clustered empirical influence vector."""
    treated = treated & np.isfinite(delta)
    donor = donor & np.isfinite(delta)
    nt, nd = int(treated.sum()), int(donor.sum())
    influence = np.zeros(len(delta))
    if not nt or not nd:
        return np.nan, influence, treated, donor
    mt, md = float(delta[treated].mean()), float(delta[donor].mean())
    influence[treated] = (delta[treated]-mt)/nt
    influence[donor] = -(delta[donor]-md)/nd
    return mt-md, influence, treated, donor


def aggregate(cells: list[dict], size: int) -> tuple:
    """Equal treated-unit weights, including changing cohort-share uncertainty."""
    cells = [cell for cell in cells if np.isfinite(cell["estimate"])]
    if not cells:
        return np.nan, np.zeros(size), 0
    total = sum(int(cell["treated_mask"].sum()) for cell in cells)
    point = sum(cell["estimate"]*cell["treated_mask"].sum() for cell in cells)/total
    influence = np.zeros(size)
    for cell in cells:
        nt = int(cell["treated_mask"].sum())
        influence += nt/total * cell["influence"]
        influence[cell["treated_mask"]] += (cell["estimate"]-point)/total
    return float(point), influence, total


def intervals(frame: pd.DataFrame, influence: np.ndarray, draws: np.ndarray,
              simultaneous: bool) -> pd.DataFrame:
    """One shared BFS multiplier draw across all time cells; no row bootstrap."""
    frame = frame.copy()
    errors = draws @ influence.T
    se = np.sqrt(np.sum(influence**2, axis=1))
    quantiles = np.quantile(errors, [.025, .975], axis=0)
    frame["cluster_standard_error"] = se
    frame["pointwise_lower_95"] = frame.estimate_log_points.to_numpy()-quantiles[1]
    frame["pointwise_upper_95"] = frame.estimate_log_points.to_numpy()-quantiles[0]
    frame["simultaneous_critical_95"] = np.nan
    frame["simultaneous_lower_95"] = np.nan
    frame["simultaneous_upper_95"] = np.nan
    if simultaneous:
        for _, indexes in frame.groupby("variant", sort=False).groups.items():
            idx = np.asarray(list(indexes), dtype=int)
            valid = idx[np.isfinite(frame.loc[idx, "estimate_log_points"]) & (se[idx] > 1e-12)]
            if len(valid):
                critical = float(np.quantile(np.max(np.abs(errors[:, valid]/se[valid]), axis=1), .95))
                frame.loc[idx, "simultaneous_critical_95"] = critical
                frame.loc[idx, "simultaneous_lower_95"] = frame.loc[idx, "estimate_log_points"]-critical*se[idx]
                frame.loc[idx, "simultaneous_upper_95"] = frame.loc[idx, "estimate_log_points"]+critical*se[idx]
    missing = ~np.isfinite(frame.estimate_log_points)
    frame.loc[missing, ["cluster_standard_error", "pointwise_lower_95", "pointwise_upper_95"]] = np.nan
    return frame


def calculate(panel: pd.DataFrame, universe: pd.DataFrame, execution: dict,
              parameters: dict) -> tuple:
    panel = panel.copy()
    panel["date"] = pd.to_datetime(panel.date)
    if panel.duplicated(["municipality_bfs_id", "date"]).any():
        raise ValueError("Duplicate territorial outcome key")
    observed = panel.hotel_overnights.notna()
    if not np.allclose(panel.loc[observed, "log_overnights"], np.log1p(panel.loc[observed, "hotel_overnights"])):
        raise ValueError("Outcome differs from registered log1p source")
    dates = pd.date_range(panel.date.min(), panel.loc[observed, "date"].max(), freq="MS")
    ids = np.sort(panel.municipality_bfs_id.unique()).astype(int)
    y = panel.pivot(index="municipality_bfs_id", columns="date", values="log_overnights").reindex(index=ids, columns=dates).to_numpy(float)
    grid_month = np.asarray(dates.month)-1
    num = month_number(dates)
    pre = int(parameters["pre_diagnostic_and_seasonality_window_months"])
    support, calibrations, cohort_cells = [], [], []
    for anchor_string, roles in universe.groupby("focal_cohort_month", sort=True):
        anchor = pd.Timestamp(anchor_string)
        roles = roles.set_index("municipality_bfs_id").reindex(ids)
        tmask = truth(roles.treated_in_focal_cohort)
        dmask = truth(roles.primary_donor_candidate_at_anchor)
        never = truth(roles.sensitivity_never_exposed_donor_candidate)
        if np.any(tmask & dmask):
            raise ValueError("Treated territory incorrectly classified as donor")
        event = (num - (anchor.year*12+anchor.month)).astype(int)
        pre_mask = (event >= -pre) & (event < 0)
        reference_index = int(np.flatnonzero(event == -1)[0])
        fits = [seasonal_fit(row[pre_mask], dates[pre_mask]) for row in y]
        season = np.array([fit["season"] for fit in fits])
        slope = np.array([fit["slope"] for fit in fits])
        baseline = np.isfinite(y[:, reference_index])
        good = baseline & np.isfinite(slope)
        corrected = y - season[:, grid_month]
        delta = corrected - corrected[:, [reference_index]]
        linear_delta = delta - slope[:, None]*(event[None, :]+1)
        exits = pd.to_datetime(roles.primary_donor_use_end_exclusive, errors="coerce")
        exit_months = np.array([np.inf if pd.isna(value) else value.year*12+value.month for value in exits])
        horizon_masks = {}
        for h in [6, 12, 24]:
            required = (event >= -h) & (event < h)
            horizon_masks[h] = tmask & good & np.isfinite(y[:, required]).all(axis=1) if required.sum() == 2*h else np.zeros(len(ids), bool)
        intersection = horizon_masks[6] & horizon_masks[12] & horizon_masks[24]
        for i, bfs in enumerate(ids):
            fit = fits[i]
            row = {"focal_cohort_month": anchor_string, "municipality_bfs_id": int(bfs),
                   "municipality_name": str(roles.iloc[i].municipality_name),
                   "treated_in_focal_cohort": bool(tmask[i]), "primary_donor_candidate": bool(dmask[i]),
                   "pre_observed_months": fit["n"], "pre_design_rank": fit["rank"],
                   "fit_status": fit["status"], "reference_observed": bool(baseline[i]),
                   "reference_log_overnights": y[i, reference_index],
                   "reference_and_calibration_available": bool(good[i]),
                   "pre_slope_log_points_per_month": fit["slope"],
                   "pre_intercept_log_points": fit["intercept"], "source_id": SOURCE}
            row.update({f"seasonal_offset_month_{m:02d}": fit["season"][m-1] for m in range(1, 13)})
            calibrations.append(row)
            if tmask[i]:
                count = int(np.isfinite(y[i, event >= 0]).sum())
                support.append({"municipality_bfs_id": int(bfs), "municipality_name": str(roles.iloc[i].municipality_name),
                                "focal_cohort_month": anchor_string, "calculable": bool(good[i]),
                                "reason": "observed_reference_and_full_rank_pre36" if good[i] else "missing_reference_or_pre36_calibration",
                                "inventory_observed_post_months": count,
                                "calculable_observed_post_months": count if good[i] else 0,
                                "common_6_months": bool(horizon_masks[6][i]),
                                "common_12_months": bool(horizon_masks[12][i]),
                                "common_24_months": bool(horizon_masks[24][i]),
                                "same_territories_6_12_24": bool(intersection[i]), "source_id": SOURCE})
        variants = [("primary", tmask, dmask, delta, None),
                    ("never_exposed_donors", tmask, never, delta, None),
                    ("linear_pretrend_sensitivity", tmask, dmask, linear_delta, None),
                    ("covid_contrast_months_omitted", tmask, dmask, delta, None)]
        for h in [6, 12, 24]:
            variants.extend([(f"common_{h}_months", horizon_masks[h], dmask, delta, h),
                             (f"same_territories_common_{h}_months", intersection, dmask, delta, h)])
        for variant, treated, donor, changes, horizon in variants:
            for j, date in enumerate(dates):
                k = int(event[j])
                if k < -pre or (horizon is not None and not -horizon <= k < horizon):
                    continue
                if variant == "covid_contrast_months_omitted" and pd.Timestamp("2020-03-01") <= date <= pd.Timestamp("2022-03-01"):
                    continue
                eligible_donors = donor & good & (num[j] < exit_months)
                estimate, influence, tm, dm = contrast(changes[:, j], treated & good, eligible_donors)
                if np.isfinite(estimate) and k == -1:
                    estimate = 0.
                    influence[:] = 0.
                cell = {"variant": variant, "focal_cohort_month": anchor_string,
                        "calendar_month": date.strftime("%Y-%m-%d"), "event_month": k,
                        "estimate": estimate, "influence": influence, "treated_mask": tm, "donor_mask": dm,
                        "treated_candidates": int(treated.sum()), "donor_candidates_before_outcome_check": int(eligible_donors.sum()),
                        "treated_ids": "|".join(map(str, ids[tm])), "donor_ids": "|".join(map(str, ids[dm]))}
                cohort_cells.append(cell)
    rows = []
    for cell in cohort_cells:
        rows.append({"variant": cell["variant"], "focal_cohort_month": cell["focal_cohort_month"],
                     "calendar_month": cell["calendar_month"], "event_month": cell["event_month"],
                     "estimate_log_points": cell["estimate"], "treated_candidates": cell["treated_candidates"],
                     "treated_observed_count": int(cell["treated_mask"].sum()),
                     "donor_observed_count": int(cell["donor_mask"].sum()),
                     "donor_candidates_before_outcome_check": cell["donor_candidates_before_outcome_check"],
                     "treated_bfs_ids": cell["treated_ids"], "donor_bfs_ids": cell["donor_ids"],
                     "status": "calculable" if np.isfinite(cell["estimate"]) else "no_observed_treated_or_donor_pair",
                     "source_id": SOURCE, "causal_estimation_approved": False})
    cohort = pd.DataFrame(rows)
    groups = {}
    for cell in cohort_cells:
        groups.setdefault((cell["variant"], cell["event_month"]), []).append(cell)
    dynamic_rows, dynamic_influence = [], []
    for (variant, event), cells in sorted(groups.items()):
        estimate, influence, total = aggregate(cells, len(ids))
        estimable = [cell for cell in cells if np.isfinite(cell["estimate"])]
        contributing = np.logical_or.reduce([cell["treated_mask"] | cell["donor_mask"] for cell in estimable]) if estimable else np.zeros(len(ids), bool)
        dynamic_rows.append({"variant": variant, "event_month": event, "estimate_log_points": estimate,
                             "treated_observed_count": total, "cohorts_contributing_count": len(estimable),
                             "unique_territories_contributing_count": int(contributing.sum()),
                             "treated_bfs_ids": "|".join(map(str, ids[np.logical_or.reduce([cell["treated_mask"] for cell in estimable])])) if estimable else "",
                             "smallest_cohort_treated_count": min([int(cell["treated_mask"].sum()) for cell in estimable], default=0),
                             "source_id": SOURCE, "causal_estimation_approved": False})
        dynamic_influence.append(influence)
    draws = np.random.default_rng(execution["bootstrap_seed"]).normal(size=(execution["bootstrap_repetitions"], len(ids)))
    cohort = intervals(cohort, np.array([cell["influence"] for cell in cohort_cells]), draws, False)
    dynamic = intervals(pd.DataFrame(dynamic_rows), np.array(dynamic_influence), draws, True)
    return cohort, dynamic, pd.DataFrame(calibrations), pd.DataFrame(support)


def report_text(summary: dict, dynamic: pd.DataFrame, support: pd.DataFrame) -> str:
    text = ["# Premiers contrastes par cohorte et mois — option A", "",
            "## Résultat et couverture", "",
            f"Calcul exploratoire approuvé le 5 octobre 2026. **{summary['calculable_exposed_territories']}/79 communes** contribuent au calcul principal, soit **{summary['primary_observed_post_pairs']} observations postérieures**. Les 79 communes et 5 580 observations restent dans le panel source. Aucun filtrage de qualité, appariement, imputation ou contrôle OFS nouveau.", "",
            "Blonay–Saint-Légier, Val de Bagnes et Laténa gardent leurs 51, 63 et 15 mois postérieurs, mais n'ont pas la référence/calibration requise. Moutier constitue une seule commune, avec ses deux identifiants sources préservés.", "",
            "Les chiffres ci-dessous sont des différences de changements de **log(1 + nuitées)**, en points logarithmiques. Ce ne sont ni des nuitées supplémentaires, ni directement des pourcentages de nuitées, ni des effets causaux établis. Chaque ligne peut représenter une composition différente de communes/cohortes.", "",
            "| Mois relatif | Communes | Cohortes | Contraste principal | IC ponctuel 95 % | Bande simultanée 95 % |", "|---:|---:|---:|---:|---:|---:|"]
    for k in [-24, -12, 0, 5, 11, 23, 35, 59, 100]:
        selected = dynamic.loc[dynamic.variant.eq("primary") & dynamic.event_month.eq(k)]
        if len(selected):
            r = selected.iloc[0]
            text.append(f"| {k} | {r.treated_observed_count} | {r.cohorts_contributing_count} | {r.estimate_log_points:.3f} | [{r.pointwise_lower_95:.3f} ; {r.pointwise_upper_95:.3f}] | [{r.simultaneous_lower_95:.3f} ; {r.simultaneous_upper_95:.3f}] |")
    primary = dynamic.loc[dynamic.variant.eq("primary") & dynamic.event_month.ge(0)]
    zero_outside = int(((primary.simultaneous_lower_95 > 0) | (primary.simultaneous_upper_95 < 0)).sum())
    text += ["", f"Sur les {len(primary)} mois relatifs postérieurs, {zero_outside} bandes simultanées excluent zéro. Cela ne prouve pas un effet nul : l'incertitude et les limites d'identification restent importantes.", "", "## Méthode et vérifications", "",
             "Pour chaque cohorte g, une régression locale sur les seuls 36 mois avant g estime intercept, pente calendaire et onze indicatrices de mois. Un rang complet et des degrés de liberté positifs rendent le calcul possible, sans seuil de qualité. On soustrait seulement les effets saisonniers à l'issue. La pente n'est soustraite que dans la sensibilité linéaire. Les trous restent des trous et le temps reste calendaire.", "",
             "Le contraste à la date t est : changement moyen depuis g−1 chez les exposées, moins le même changement chez les témoins observés. Les témoins sont ceux approuvés à g, jamais ou pas encore exposés, et sortent strictement avant leur propre entrée. Chaque commune a le même poids dans sa cohorte ou chez les témoins. À mois relatif égal, les cohortes sont pondérées par leur nombre de communes effectivement observées : chaque commune traitée garde le même poids.", "",
             "Bootstrap multiplicateur gaussien, 4 999 tirages, graine 20261005 : un même multiplicateur par territoire dans tous les mois, cohortes et rôles. Les contributions centrées des moyennes et des poids de cohortes donnent les erreurs simulées. IC ponctuels dans la table cohorte/mois ; bandes simultanées sur tous les mois calculables de chaque courbe dynamique, hors référence normalisée −1. Les bandes ne couvrent pas conjointement toutes les variantes. La calibration est une fonction du dossier prétraitement de chaque territoire, conservé entier. Cette approximation asymptotique reste fragile pour les cohortes de trois communes et ne corrige pas une dépendance géographique entre communes.", "",
             "La saisonnalité étant ajustée dans la fenêtre diagnostique elle-même, les écarts prétraitement sont des diagnostics **en échantillon**, pas une validation indépendante des tendances parallèles. La référence −1 suppose l'absence d'anticipation. L'audit 79 relevait déjà des écarts de tendance, surtout pour les cohortes récentes. Un intervalle étroit ne corrige pas ces problèmes d'identification.", "",
             "## Sensibilités disponibles", "",
             "| Variante | Ce qui change |", "|---|---|",
             "| Témoins jamais exposés | Retire les futurs exposés du groupe de comparaison, sans changer les communes traitées. |",
             "| Tendance linéaire prétraitement | Soustrait également la pente pré36 propre à chaque territoire, extrapolée après entrée. Hypothèse forte, pas modèle principal. |",
             "| Mois de contraste COVID omis | Omet mars 2020–mars 2022 des comparaisons. La calibration pré36 reste identique : ce n'est pas une estimation entièrement sans COVID. |",
             "| Horizons communs 6/12/24 mois | Respectivement 76/73/65 communes avec toutes les issues pré/post observées. Variante complémentaire avec les mêmes 65 communes aux trois horizons. |", "",
             "Comparaison compacte à mois relatif 23, qui représente 66 communes en principal :", "",
             "| Variante | Communes | Contraste | IC ponctuel 95 % |", "|---|---:|---:|---:|"]
    for variant, label in [("primary", "Principal"), ("never_exposed_donors", "Jamais exposés"),
                           ("linear_pretrend_sensitivity", "Pente prétraitement"),
                           ("covid_contrast_months_omitted", "Mois COVID omis"),
                           ("same_territories_common_24_months", "Même support 65 communes")]:
        r = dynamic.loc[dynamic.variant.eq(variant) & dynamic.event_month.eq(23)].iloc[0]
        text.append(f"| {label} | {r.treated_observed_count} | {r.estimate_log_points:.3f} | [{r.pointwise_lower_95:.3f} ; {r.pointwise_upper_95:.3f}] |")
    text += ["",
             "Les CSV donnent tous les mois et variantes, sans sélectionner les résultats favorables. Aucun coefficient post global/saut permanent n'est calculé : son agrégation n'était pas choisie dans le cadrage approuvé. Les plages 0–5, 6–11, 12–23 et 24+ restent examinables mois par mois ; une baisse entre plages ne démontrerait pas un rendement décroissant, car composition et contexte changent. L'effet propre des entrées additionnelles n'est pas identifié par ce modèle, qui conserve toute la trajectoire du réseau.", "",
             "## Limites, sources et reprise", "",
             "L'accessibilité actuelle est tenue fixe historiquement, les retombées indirectes restent possibles et seuls 18/79 territoires disposent d'une revue de chocs antérieure. La pandémie touche certaines calibrations et suivis. Ces contrastes ne débloquent donc pas une interprétation causale, une prédiction d'effet individuel de station ou un score d'opportunité.", "",
             "Entrées : panel HESTA territorial et univers de comparaison du rapport 78, décisions des rapports 74–79, proposition historique 81. Approbation d'exécution : `config/accessibility_cohort_time_execution.json`. Le rapport 81 et sa configuration sont conservés comme instantané de la proposition avant accord, pas comme état courant.", "",
             "Cadre : `CALLAWAY_SANTANNA_2021_DID` et documentation officielle [`att_gt`](https://bcallaway11.github.io/did/reference/att_gt.html), consultée le 5 octobre 2026 (`DID_ATT_GT_OFFICIAL_DOCUMENTATION`). Cette dernière documente le principe de comparaisons par cohorte, la référence universelle et le bootstrap multiplicateur. Le script Python applique un contraste et une saisonnalité propres au projet : ce n'est pas l'exécution du package R ni une certification automatique de sa théorie pour ce panel.", "",
             "Résultats : `accessibility_cohort_time_estimation_cohort_month.csv`, `_dynamic.csv`, `_calibration.csv`, `_territory_support.csv`. Empreintes des entrées/sorties, versions et comptes : `accessibility_cohort_time_estimation_summary.json`. Les variables et sources sont enregistrées dans les deux catalogues metadata.", "",
             "Reprise : `.venv/Scripts/python.exe src/causal_inference/estimate_accessibility_cohort_time.py`, puis mise à jour de la provenance et tests. Le calcul est déterministe, local et ne relance aucune collecte. Prochaine discussion : confronter les sensibilités et diagnostics, puis valider tout changement de référence, calibration, témoins ou agrégation avant de le mettre en œuvre.", ""]
    return "\n".join(text)


def main() -> None:
    execution = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not execution["parameter_bundle_approved"] or not execution["estimator_selected"]:
        raise ValueError("Explicit approval required before estimation")
    proposal_path = ROOT / execution["approved_proposal_config"]
    proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
    inputs_path = ROOT / proposal["territorial_input_config"]
    inputs = json.loads(inputs_path.read_text(encoding="utf-8"))
    panel_path, universe_path = ROOT / inputs["analytical_panel"], ROOT / inputs["comparison_universe"]
    input_paths = [CONFIG, proposal_path, inputs_path, panel_path, universe_path,
                   ROOT / proposal["comparison_rule_config"], ROOT / proposal["temporal_design_config"],
                   ROOT / proposal["network_trajectory_config"], Path(__file__)]
    checksums = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}
    cohort, dynamic, calibration, support = calculate(pd.read_csv(panel_path, low_memory=False), pd.read_csv(universe_path), execution, proposal["proposed_parameters_not_approved"])
    paths = []
    for label, frame in [("cohort_month", cohort), ("dynamic", dynamic), ("calibration", calibration), ("territory_support", support)]:
        path = ROOT / f"reports/{PREFIX}_{label}.csv"
        frame.to_csv(path, index=False, lineterminator="\n")
        paths.append(path)
    summary = {"specification_version": execution["specification_version"], "parameter_bundle_approved": True,
               "estimator_selected": True, "estimation_executed": True, "causal_estimation_approved": False,
               "final_causal_sample_selected": False, "additional_effect_estimator_selected": False,
               "exposed_territories_retained_in_inventory": len(support),
               "calculable_exposed_territories": int(support.calculable.sum()),
               "inventory_observed_post_months": int(support.inventory_observed_post_months.sum()),
               "primary_observed_post_pairs": int(cohort.loc[cohort.variant.eq("primary") & cohort.event_month.ge(0) & cohort.status.eq("calculable"), "treated_observed_count"].sum()),
               "common_horizon_territories": {str(h): int(support[f"common_{h}_months"].sum()) for h in [6, 12, 24]},
               "same_territories_all_horizons": int(support.same_territories_6_12_24.sum()),
               "missing_histories": support.loc[~support.calculable].to_dict(orient="records"),
               "bootstrap_repetitions": execution["bootstrap_repetitions"], "bootstrap_seed": execution["bootstrap_seed"],
               "bootstrap_kind": "gaussian_territory_multiplier_centered_influence",
               "dynamic_simultaneous_band_family": execution["simultaneous_family"],
               "global_post_coefficient_selected": False,
               "cohort_month_rows": len(cohort), "dynamic_rows": len(dynamic), "calibration_rows": len(calibration),
               "input_sha256": checksums,
               "output_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
               "runtime_versions": {"numpy": np.__version__, "pandas": pd.__version__, "python": sys.version.split()[0]}}
    if checksums != {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in input_paths}:
        raise ValueError("Input changed during estimation")
    (ROOT / f"reports/{PREFIX}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (ROOT / "reports/82_ESTIMATION_COHORTES_MOIS_OPTION_A_FR.md").write_text(report_text(summary, dynamic, support), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"input_sha256", "output_sha256", "runtime_versions", "missing_histories"}}, indent=2))


if __name__ == "__main__":
    main()
