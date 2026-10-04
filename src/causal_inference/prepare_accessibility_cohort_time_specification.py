"""Document orientation A and audit proposed inputs; never fit a treatment effect."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.causal_inference.audit_accessibility_all_cohort_comparability import trend

CONFIG = ROOT / "config/accessibility_cohort_time_estimator.json"
OUTPUT = ROOT / "reports/accessibility_cohort_time_specification_support.json"
REPORT = ROOT / "reports/81_CADRAGE_ESTIMATION_COHORTES_MOIS_FR.md"


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not config["estimator_orientation_selected"] or config["researcher_approved_orientation"] != "A":
        raise ValueError("This preparation requires explicit approval of orientation A")
    if config["estimation_executed"]:
        raise ValueError("Preparation cannot certify an estimation it does not execute")
    input_config_path = ROOT / config["territorial_input_config"]
    inputs = json.loads(input_config_path.read_text(encoding="utf-8"))
    panel_path, universe_path = ROOT / inputs["analytical_panel"], ROOT / inputs["comparison_universe"]
    panel = pd.read_csv(panel_path, low_memory=False)
    panel["date"] = pd.to_datetime(panel.date)
    universe = pd.read_csv(universe_path)
    by_unit = {int(bfs): rows.set_index("date") for bfs, rows in panel.groupby("municipality_bfs_id")}
    rows, missing = [], []
    potential_post = 0
    all_post = 0
    for cohort, roles in universe.groupby("focal_cohort_month", sort=True):
        anchor = pd.Timestamp(cohort)
        months = int(config["proposed_parameters_not_approved"]["pre_diagnostic_and_seasonality_window_months"])
        dates = pd.date_range(anchor-pd.DateOffset(months=months), anchor-pd.DateOffset(months=1), freq="MS")
        row = {"focal_cohort_month": cohort}
        for label, flag in [("treated", "treated_in_focal_cohort"), ("primary_donors", "primary_donor_candidate_at_anchor")]:
            selected = roles.loc[roles[flag].astype(str).str.lower().eq("true")]
            baseline, seasonal, joint = [], [], []
            for unit in selected.itertuples():
                local = by_unit[int(unit.municipality_bfs_id)]
                reference = local.reindex([anchor-pd.DateOffset(months=1)]).log_overnights.iloc[0]
                fit = trend(local.reindex(dates).log_overnights.to_numpy(float), dates)[0]
                baseline.append(pd.notna(reference))
                seasonal.append(np.isfinite(fit))
                jointly_available = pd.notna(reference) and np.isfinite(fit)
                joint.append(jointly_available)
                if label == "treated":
                    count = int(local.loc[local.index >= anchor].hotel_overnights.notna().sum())
                    all_post += count
                    potential_post += count if jointly_available else 0
                    if not jointly_available:
                        missing.append({"municipality_bfs_id": int(unit.municipality_bfs_id), "municipality_name": unit.municipality_name, "focal_cohort_month": cohort, "observed_post_months_retained_in_inventory": count})
            row.update({f"{label}_candidates": len(selected), f"{label}_observed_reference_minus1": int(sum(baseline)), f"{label}_pre36_full_rank_seasonal_fit": int(sum(seasonal)), f"{label}_joint_reference_and_seasonal_fit": int(sum(joint))})
        rows.append(row)
    summary = {
        "specification_version": config["specification_version"],
        "orientation_A_approved": True,
        "parameter_bundle_approved": config["parameter_bundle_approved"],
        "counterfactual_support_only_not_sample_selection": True,
        "cohort_reference_support": rows,
        "exposed_territories_retained_in_inventory": int(sum(row["treated_candidates"] for row in rows)),
        "territories_with_proposed_reference_and_seasonal_fit": int(sum(row["treated_joint_reference_and_seasonal_fit"] for row in rows)),
        "all_observed_exposed_post_rows_retained_in_inventory": all_post,
        "observed_exposed_post_rows_with_proposed_reference_and_fit": potential_post,
        "missing_proposed_reference_or_fit": missing,
        "analysis_sample_selected": False, "estimation_executed": False, "causal_estimation_approved": False,
        "input_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in [CONFIG, input_config_path, panel_path, universe_path]},
    }
    OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    all_post_display = f"{all_post:,}".replace(",", " ")
    potential_post_display = f"{potential_post:,}".replace(",", " ")
    REPORT.write_text("\n".join([
        "# Cadrage de l'estimation par cohorte et mois", "",
        "## Décision validée le 5 octobre 2026", "",
        "L'orientation A est retenue : comparer les changements de nuitées par cohorte et mois avec les témoins autorisés. La tendance linéaire reste une sensibilité, pas le contrefactuel imposé au modèle principal. Le panel territorial, les groupes existants, le suivi non équilibré, les entrées successives et les sensibilités déjà validées restent inchangés.", "",
        "Le choix de l'orientation ne valide pas automatiquement les paramètres ci-dessous. Aucun effet n'est encore calculé et aucune commune n'est retirée.", "",
        "## Proposition à valider ensemble", "",
        "| Point | Proposition | Conséquence / alternative |", "|---|---|---|",
        "| Référence | Dernier mois avant la première exposition, soit mois relatif -1, et diagnostics sur les 36 mois précédents. | Suppose l'absence d'anticipation à la référence. Une référence plus ancienne ou une période moyenne prétraitement reste possible, mais changerait le contraste. |",
        "| Saisonnalité | Estimer les effets des douze mois séparément pour chaque territoire à partir de ses seules observations prétraitement, sur 36 mois. Une pente accompagne la calibration pour ne pas l'assimiler à la saisonnalité ; elle n'est pas soustraite en principal. | Permet de distinguer saisonnalité locale et chocs de calendrier communs. Suppose un profil saisonnier stable ; une comparaison annuelle ou une variante non corrigée est une autre possibilité. |",
        "| Poids | Même poids à chaque commune observable, dans la cohorte et parmi les témoins autorisés ; agrégation dynamique avec effectifs publiés. Aucun appariement ni seuil de qualité. | Cible une commune moyenne, pas une moyenne pondérée par la taille hôtelière. Aucun coefficient global mélangeant silencieusement les durées de suivi n'est choisi. |",
        "| Données manquantes | Conserver les 79 communes dans l'inventaire. Marquer les trois historiques prétraitement incomplets comme non calculables dans cette spécification, sans imputation. Pour chaque contraste, exiger les deux valeurs originales observées. | Alternative : différer l'estimation et rechercher les historiques complets des trois fusions. Les dates et raisons de non-calcul resteraient publiées. |",
        "| Incertitude | Bootstrap par territoire : tous ses mois et ses réutilisations comme témoin restent ensemble. Intervalles/bandes simultanés à 95 % ; signaler les petites cohortes. | Ne pas traiter les mois comme des communes indépendantes. Les quelques communes de certaines cohortes limitent la précision et la fiabilité de l'inférence. |", "",
        "La nouvelle typologie OFS, la construction et les séries agrégées du rapport 80 restent du contexte. Elles ne deviennent pas automatiquement des variables d'ajustement. Les capacités hôtelières après entrée ne sont pas introduites comme contrôles, car elles peuvent être modifiées par le traitement.", "",
        "## Disponibilité vérifiée, sans appliquer de sélection", "",
        f"Les {summary['exposed_territories_retained_in_inventory']} communes et {all_post_display} observations postérieures restent dans le panel. {summary['territories_with_proposed_reference_and_seasonal_fit']} communes disposent à la fois de la référence -1 et d'une calibration saisonnière algébriquement calculable. Elles représentent {potential_post_display} observations postérieures, avant de vérifier pour chaque date les résultats disponibles chez les témoins. Ces comptes sont une conséquence potentielle de la proposition, pas un échantillon adopté.", "",
        "| Cohorte | Exposées : référence et calibration / inventaire | Témoins : référence et calibration / candidats |", "|---|---:|---:|"] + [
        f"| {row['focal_cohort_month'][:7]} | {row['treated_joint_reference_and_seasonal_fit']}/{row['treated_candidates']} | {row['primary_donors_joint_reference_and_seasonal_fit']}/{row['primary_donors_candidates']} |" for row in rows
    ] + ["", "Les trois cas sont Blonay–Saint-Légier, Val de Bagnes et Laténa. Aucune reconstruction partielle ou exclusion arbitraire n'est appliquée. La disponibilité d'un témoin ici ne garantit pas son observation pour chaque mois postérieur, sa comparabilité, ni l'absence de chocs ou de retombées indirectes.", "",
        "## Sources et reprise", "",
        "Les entrées sont les fichiers territoriaux du rapport 78 et les règles approuvées des rapports 74–79. La vérification réutilise le diagnostic de rang du rapport 79 ; elle ne soustrait aucune saisonnalité et n'estime aucun effet. Empreintes SHA-256 et comptes : `accessibility_cohort_time_specification_support.json`.", "",
        "Cadre méthodologique déjà enregistré : `CALLAWAY_SANTANNA_2021_DID` ([article, version auteur](https://arxiv.org/abs/1803.09015v4)). La correction saisonnière préestimée décrite ici est une proposition spécifique au projet, non une implémentation automatiquement certifiée par cet article. Les hypothèses de tendances parallèles après correction, de non-anticipation et de comparaison valide restent à évaluer.", "",
        "Décision durable : `config/accessibility_cohort_time_estimator.json`. Seule l'orientation A est approuvée ; `parameter_bundle_approved` reste faux. Avant le calcul, recueillir l'accord explicite pour cette proposition ou ses modifications. L'effet propre d'une entrée additionnelle reste une analyse distincte, et aucun résultat n'est déclaré causal.", "",
    ]), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"input_sha256", "cohort_reference_support"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
