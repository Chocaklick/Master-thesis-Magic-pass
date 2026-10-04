"""Build the researcher-approved stage-28 cohort comparison candidate universes.

Option C uses not-yet-exposed and never-exposed municipalities as the primary
donor set and never-exposed municipalities alone as a sensitivity. Future-treated
donors can contribute outcomes only before their own first exposure month. This
stage does not choose an outcome window, comparability screen, estimator or final
analysis sample.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_cohort_comparison.json"
INPUT_PATH = ROOT / "reports" / "accessibility_covid_foreign_share_selected.csv"
UNIVERSE_PATH = ROOT / "reports" / "accessibility_cohort_comparison_universe.csv"
COHORT_PATH = ROOT / "reports" / "accessibility_cohort_comparison_by_cohort.csv"
SUMMARY_PATH = ROOT / "reports" / "accessibility_cohort_comparison_summary.json"
REPORT_PATH = ROOT / "reports" / "75_COMPARAISON_COHORTES_OPTION_C_FR.md"
SOURCE_ID = "DERIVED_ACCESSIBILITY_COHORT_COMPARISON_RULE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_universe(config: dict, selected: pd.DataFrame) -> pd.DataFrame:
    result = selected[
        [
            "focal_cohort_month",
            "municipality_bfs_id",
            "municipality_name",
            "municipality_first_exposure_month_120min",
            "exposure_status_at_focal_cohort",
            "selected_foreign_share_available",
            "foreign_share_interaction_sensitivity_complete_case_candidate",
        ]
    ].copy()
    status = result.exposure_status_at_focal_cohort
    treated = status.eq("first_exposed_in_focal_cohort")
    never = status.eq("never_exposed_in_current_120min_matrix")
    not_yet = status.eq("not_yet_exposed_at_focal_cohort")
    previously = status.eq("previously_exposed_before_focal_cohort")
    if not (treated | never | not_yet | previously).all():
        unknown = sorted(status[~(treated | never | not_yet | previously)].unique())
        raise ValueError(f"Unexpected exposure status values: {unknown}")

    result["treated_in_focal_cohort"] = treated
    result["primary_donor_candidate_at_anchor"] = never | not_yet
    result["sensitivity_never_exposed_donor_candidate"] = never
    result["primary_comparison_universe_candidate"] = treated | never | not_yet
    result["sensitivity_comparison_universe_candidate"] = treated | never
    result["primary_comparison_role"] = np.select(
        [treated, never, not_yet, previously],
        [
            "treated_in_focal_cohort",
            "donor_never_exposed",
            "donor_not_yet_exposed",
            "excluded_already_exposed",
        ],
        default="unexpected",
    )
    result["sensitivity_comparison_role"] = np.select(
        [treated, never, not_yet, previously],
        [
            "treated_in_focal_cohort",
            "donor_never_exposed",
            "excluded_not_yet_exposed",
            "excluded_already_exposed",
        ],
        default="unexpected",
    )
    result["primary_donor_use_end_exclusive"] = np.where(
        not_yet,
        result.municipality_first_exposure_month_120min.fillna(""),
        "",
    )
    result["primary_donor_month_rule"] = np.select(
        [not_yet, never],
        [
            config["not_yet_exposed_donor_censoring_rule"],
            "eligible_through_selected_window_subject_to_future_methodological_gates",
        ],
        default="",
    )
    result["comparison_group_rule_selected"] = True
    result["outcome_window_selected"] = bool(config["outcome_window_selected"])
    result["comparability_screen_selected"] = bool(
        config["comparability_screen_selected"]
    )
    result["analysis_sample_selected"] = bool(config["analysis_sample_selected"])
    result["estimator_selected"] = bool(config["estimator_selected"])
    result["causal_estimation_approved"] = bool(
        config["causal_estimation_approved"]
    )
    result["source_id"] = SOURCE_ID
    return result.sort_values(
        ["focal_cohort_month", "municipality_bfs_id"], kind="stable"
    ).reset_index(drop=True)


def build_cohort_summary(universe: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for cohort, group in universe.groupby("focal_cohort_month", sort=True):
        roles = group.primary_comparison_role.value_counts()
        treated = group.treated_in_focal_cohort.astype(bool)
        primary = group.primary_donor_candidate_at_anchor.astype(bool)
        sensitivity = group.sensitivity_never_exposed_donor_candidate.astype(bool)
        share = group.selected_foreign_share_available.astype(bool)
        rows.append(
            {
                "focal_cohort_month": cohort,
                "municipality_rows": int(len(group)),
                "treated_municipalities": int(treated.sum()),
                "primary_donor_municipalities": int(primary.sum()),
                "primary_not_yet_exposed_donors": int(
                    roles.get("donor_not_yet_exposed", 0)
                ),
                "primary_never_exposed_donors": int(
                    roles.get("donor_never_exposed", 0)
                ),
                "sensitivity_never_exposed_donors": int(sensitivity.sum()),
                "excluded_already_exposed_municipalities": int(
                    roles.get("excluded_already_exposed", 0)
                ),
                "treated_with_foreign_share": int((treated & share).sum()),
                "primary_donors_with_foreign_share": int((primary & share).sum()),
                "sensitivity_donors_with_foreign_share": int(
                    (sensitivity & share).sum()
                ),
                "comparison_group_rule_selected": True,
                "outcome_window_selected": False,
                "comparability_screen_selected": False,
                "analysis_sample_selected": False,
                "estimator_selected": False,
                "causal_estimation_approved": False,
                "source_id": SOURCE_ID,
            }
        )
    return pd.DataFrame(rows)


def build_summary(config: dict, universe: pd.DataFrame, cohorts: pd.DataFrame) -> dict:
    return {
        "specification_version": config["specification_version"],
        "researcher_approved_option": config["researcher_approved_option"],
        "accessibility_threshold_minutes": config[
            "accessibility_threshold_minutes"
        ],
        "primary_donor_rule": config["primary_donor_rule"],
        "not_yet_exposed_donor_censoring_rule": config[
            "not_yet_exposed_donor_censoring_rule"
        ],
        "sensitivity_donor_rule": config["sensitivity_donor_rule"],
        "municipality_cohort_rows": int(len(universe)),
        "municipalities_per_cohort": int(
            universe.groupby("focal_cohort_month").municipality_bfs_id.nunique().min()
        ),
        "first_exposure_cohorts": int(universe.focal_cohort_month.nunique()),
        "unique_first_exposed_municipalities": int(
            universe.loc[
                universe.treated_in_focal_cohort, "municipality_bfs_id"
            ].nunique()
        ),
        "unique_never_exposed_municipalities": int(
            universe.loc[
                universe.exposure_status_at_focal_cohort.eq(
                    "never_exposed_in_current_120min_matrix"
                ),
                "municipality_bfs_id",
            ].nunique()
        ),
        "cohort_counts": cohorts[
            [
                "focal_cohort_month",
                "treated_municipalities",
                "primary_donor_municipalities",
                "primary_not_yet_exposed_donors",
                "primary_never_exposed_donors",
                "sensitivity_never_exposed_donors",
                "excluded_already_exposed_municipalities",
            ]
        ].to_dict(orient="records"),
        "comparison_group_rule_selected": True,
        "outcome_window_selected": False,
        "comparability_screen_selected": False,
        "analysis_sample_selected": False,
        "estimator_selected": False,
        "causal_estimation_approved": False,
        "input_sha256": {
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            INPUT_PATH.relative_to(ROOT).as_posix(): sha256(INPUT_PATH),
        },
        "source_id": SOURCE_ID,
    }


def write_report(summary: dict) -> None:
    lines = [
        "# Comparaison des cohortes - étape 28",
        "",
        "**Statut : option C appliquée aux univers candidats. Aucun estimateur n'est encore choisi.**",
        "",
        "## Règle validée",
        "",
        "- Analyse principale : communes jamais exposées ou pas encore exposées à la date de la cohorte.",
        "- Une commune pas encore exposée cesse d'être témoin au mois de sa propre première exposition; seuls les mois strictement antérieurs peuvent être utilisés.",
        "- Sensibilité : communes jamais exposées dans la matrice actuelle à 120 minutes uniquement.",
        "- Les communes déjà exposées avant la cohorte ne servent jamais de témoins; les communes de la cohorte sont marquées comme traitées.",
        "",
        "## Effectifs mécaniques par cohorte",
        "",
        "| Cohorte | Traitées | Témoins principaux | Dont pas encore exposées | Dont jamais exposées | Témoins de sensibilité | Déjà exposées exclues des témoins |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary["cohort_counts"]:
        lines.append(
            f"| {row['focal_cohort_month']} | {row['treated_municipalities']} | "
            f"{row['primary_donor_municipalities']} | "
            f"{row['primary_not_yet_exposed_donors']} | "
            f"{row['primary_never_exposed_donors']} | "
            f"{row['sensitivity_never_exposed_donors']} | "
            f"{row['excluded_already_exposed_municipalities']} |"
        )
    lines.extend(
        [
            "",
            f"L'audit conserve {summary['municipality_cohort_rows']} lignes commune-cohorte, "
            f"{summary['unique_first_exposed_municipalities']} communes exposées une première fois et "
            f"{summary['unique_never_exposed_municipalities']} communes jamais exposées dans la matrice actuelle.",
            "",
            "## Limites et prochaine décision",
            "",
            "Ces effectifs décrivent une disponibilité mécanique. Ils ne valident ni comparabilité, ni tendances parallèles, ni absence de choc local. La matrice d'accessibilité actuelle reste projetée sur les cohortes historiques.",
            "",
            "Ce fichier décrit la décision sur les témoins. La décision temporelle ultérieure retient tous les mois postérieurs observés dans un dessin dynamique non équilibré, avec horizons 6/12/24 mois en sensibilité : voir le rapport 76. Le filtre de comparabilité, l'échantillon final et l'estimateur restent à définir.",
            "",
            "## Sources internes",
            "",
            "- Première exposition communale et statut par cohorte : `reports/accessibility_covid_foreign_share_selected.csv`.",
            "- Règle approuvée : `config/accessibility_cohort_comparison.json`.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["researcher_approved_option"] != "C":
        raise ValueError("Stage 28 requires the researcher-approved option C")
    selected = pd.read_csv(INPUT_PATH, dtype={"municipality_bfs_id": int})
    universe = build_universe(config, selected)
    cohorts = build_cohort_summary(universe)
    summary = build_summary(config, universe, cohorts)

    if len(universe) != 186 * 7:
        raise ValueError(f"Expected 1,302 rows, found {len(universe)}")
    if not universe.groupby("focal_cohort_month").municipality_bfs_id.nunique().eq(186).all():
        raise ValueError("Every cohort must retain all 186 municipality rows")
    if int(universe.treated_in_focal_cohort.sum()) != 80:
        raise ValueError("Expected 80 first-exposed municipality-cohort rows")
    if not cohorts.primary_never_exposed_donors.eq(106).all():
        raise ValueError("Expected 106 never-exposed donors in every cohort")
    if not cohorts.sensitivity_never_exposed_donors.eq(106).all():
        raise ValueError("Sensitivity donors must be the 106 never-exposed municipalities")
    if universe.analysis_sample_selected.any() or universe.estimator_selected.any():
        raise ValueError("Stage 28 donor audit cannot select an estimation sample")
    if universe.causal_estimation_approved.any():
        raise ValueError("Stage 28 donor audit cannot approve causal estimation")

    universe.to_csv(UNIVERSE_PATH, index=False, lineterminator="\n")
    cohorts.to_csv(COHORT_PATH, index=False, lineterminator="\n")
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
