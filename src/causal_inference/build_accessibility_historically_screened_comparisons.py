"""Apply the historical-access screen to the 95 pretrend comparison pairs.

This stage only narrows the manual review worklist. It does not validate the
projected transfer topology, local-shock exclusion, spillovers, parallel
trends, a comparison municipality or a causal treatment.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SHORTLIST_PATH = ROOT / "reports" / "accessibility_first_exposure_pretrend_shortlist.csv"
HISTORICAL_PATH = ROOT / "reports" / "accessibility_historical_gtfs_2018_current_transfer_municipality_validation.csv"
FIRST_EXPOSURE_PATH = ROOT / "reports" / "accessibility_first_exposure_audit.csv"
OUTPUT = ROOT / "reports" / "accessibility_historically_screened_pretrend_shortlist.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_historically_screened_pretrend_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "64_REVUE_COMPARAISONS_APRES_ACCES_HISTORIQUE_FR.md"


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    shortlist = pd.read_csv(SHORTLIST_PATH)
    historical = pd.read_csv(HISTORICAL_PATH)
    first = pd.read_csv(FIRST_EXPOSURE_PATH)
    retained = historical[as_bool(historical.historical_first_exposure_retained)].copy()
    if len(shortlist) != 95 or shortlist.treated_municipality_bfs_id.nunique() != 19:
        raise ValueError("Expected the 19 x 5 pretrend shortlist")
    if len(retained) != 14:
        raise ValueError("Expected 14 historically retained treated municipalities")

    historical_fields = retained[[
        "municipality_bfs_id", "current_founding_groups_within_120_minutes",
        "historical_founding_groups_with_complete_routes",
        "historical_founding_groups_within_120_minutes",
        "historical_validated_group_ids", "historical_validated_group_names",
        "historical_first_exposure_retained",
        "all_current_founding_groups_historically_within_120_minutes",
        "historical_first_exposure_design_review_status",
    ]].rename(columns={"municipality_bfs_id": "treated_municipality_bfs_id"})
    result = shortlist[
        shortlist.treated_municipality_bfs_id.isin(retained.municipality_bfs_id)
    ].copy().merge(
        historical_fields,
        on="treated_municipality_bfs_id",
        how="left",
        validate="many_to_one",
    )
    control_fields = first[[
        "municipality_bfs_id", "ever_accessible_120min", "first_exposure_month",
        "shared_current_territory",
    ]].rename(columns={
        "municipality_bfs_id": "control_municipality_bfs_id",
        "ever_accessible_120min": "control_ever_accessible_current_120min",
        "first_exposure_month": "control_first_exposure_month_audit",
        "shared_current_territory": "control_shared_current_territory",
    })
    result = result.merge(
        control_fields,
        on="control_municipality_bfs_id",
        how="left",
        validate="many_to_one",
    )
    if len(result) != 70 or not result.groupby(
        "treated_municipality_bfs_id"
    ).size().eq(5).all():
        raise ValueError("Expected five comparison rows for each of 14 treatments")

    result["historical_access_scenario_used"] = (
        "official_2026_transfer_topology_projected_to_active_2018_stop_ids_sensitivity"
    )
    result["historical_access_scenario_is_published_2018_fact"] = False
    result["historical_access_screen_passed"] = True
    result["treated_pair_retained_for_manual_review"] = True
    result["treated_local_shock_review_status"] = "pending_manual_evidence_review"
    result["control_external_shock_review_status"] = "pending_manual_evidence_review"
    result["spillover_review_status"] = "pending_bilateral_and_network_review"
    result["outcome_scope_review_status"] = "official_hotel_series_available_scope_not_tourist_catchment"
    result["parallel_trends_approved"] = False
    result["causal_treatment_approved"] = False
    result["causal_control_approved"] = False
    result["causal_pair_approved"] = False
    result["source_id"] = "DERIVED_ACCESSIBILITY_HISTORICAL_GTFS_2018_VALIDATION"
    result = result.sort_values(
        ["treated_municipality_bfs_id", "comparability_rank"], kind="stable"
    )
    result.to_csv(OUTPUT, index=False, lineterminator="\n")

    removed = historical[~as_bool(historical.historical_first_exposure_retained)]
    complete_mix = as_bool(
        retained.all_current_founding_groups_historically_within_120_minutes
    )
    summary = {
        "analysis_date": "2026-10-03",
        "original_treated_municipalities": 19,
        "original_shortlisted_pairs": 95,
        "historically_retained_treated_municipalities": len(retained),
        "historically_removed_treated_municipalities": len(removed),
        "historically_screened_pairs_for_manual_review": len(result),
        "distinct_comparison_municipalities": int(
            result.control_municipality_bfs_id.nunique()
        ),
        "retained_treatments_with_all_current_founding_groups": int(
            complete_mix.sum()
        ),
        "retained_treatments_with_revised_founding_group_mix": int(
            (~complete_mix).sum()
        ),
        "removed_treated_municipalities": removed[
            ["municipality_bfs_id", "municipality_name"]
        ].to_dict("records"),
        "historical_access_scenario": (
            "official_2026_transfer_topology_projected_to_active_2018_stop_ids_sensitivity"
        ),
        "historical_access_scenario_is_published_2018_fact": False,
        "local_shock_reviews_completed": 0,
        "spillover_reviews_completed": 0,
        "parallel_trends_approved": False,
        "causal_pairs_approved": 0,
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): digest(path)
            for path in [SHORTLIST_PATH, HISTORICAL_PATH, FIRST_EXPOSURE_PATH]
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    removed_names = ", ".join(removed.municipality_name.astype(str))
    report = f"""# Comparaisons après validation historique de l'accès — étape 17

## Réduction de la revue

La sensibilité fondée sur la topologie officielle actuelle des transferts, projetée uniquement sur les identifiants actifs en 2018, conserve **{len(retained)} des 19 communes traitées**. Le travail manuel passe donc de **95 à {len(result)} couples**, soit cinq comparaisons pré-période pour chacune des 14 communes retenues. Les {summary['distinct_comparison_municipalities']} communes de comparaison distinctes restent seulement des candidates mécaniques.

| Statut des communes traitées | Nombre |
|---|---:|
| Tous les groupes fondateurs actuels restent à 120 min ou moins | {int(complete_mix.sum())} |
| Au moins un groupe reste, mais la composition fondatrice est révisée | {int((~complete_mix).sum())} |
| Aucune exposition fondatrice maintenue à 120 min ou moins | {len(removed)} |

Les cinq communes retirées sont : **{removed_names}**. Elles ne doivent pas entrer dans un premier test à seuil de 120 minutes sous cette sensibilité, sauf justification explicite d'une autre règle d'accès.

## Ce qui reste à vérifier

Le filtre historique ne valide pas un contrôle causal. Pour les 70 couples restants, trois examens sont encore `pending` : chocs locaux de la commune traitée et de la commune de comparaison, spillovers bilatéraux ou du réseau Magic Pass, et validité du périmètre communal comme issue touristique. Les tendances parallèles restent non approuvées et tous les drapeaux causaux restent `false`.

## Fichier de revue

`reports/accessibility_historically_screened_pretrend_shortlist.csv` contient les 70 couples, leurs métriques pré-période, la composition fondatrice historiquement retenue et les champs de revue encore ouverts.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
