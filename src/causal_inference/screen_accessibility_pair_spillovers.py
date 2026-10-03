"""Screen direct local spillovers for the 21 stage-21 comparison candidates.

The operational basin follows the researcher's municipality-centre-to-station
idea: a municipality is locally exposed when its reference origin is within
120 scheduled minutes of a station group. Pair distance and station-network
distance are conservative supporting proxies. The screen does not claim that
broad Swiss visitor-market substitution is absent and grants no causal status.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PAIR_INPUT = ROOT / "data_processed" / "accessibility_comparison_full_control_external_risk_screen.csv"
JOURNEY_INPUT = ROOT / "data_processed" / "accessibility_station_group_journey_context.csv"

AUDIT_OUTPUT = ROOT / "reports" / "accessibility_pair_spillover_evidence.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_comparison_spillover_screen.csv"
WORKLIST_OUTPUT = ROOT / "reports" / "accessibility_parallel_trend_worklist.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_pair_spillover_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "69_SCREENING_BASSINS_TOURISTIQUES_SPILLOVERS_FR.md"

WINDOW_END = pd.Timestamp("2019-10-01")
SCHEDULED_ACCESS_LIMIT_MINUTES = 120.0
PAIR_DISTANCE_LOW_DIRECT_RISK_KM = 50.0
EXPECTED_ALL_PAIRS = 70
EXPECTED_CANDIDATE_PAIRS = 21


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def specific_group_access(row: pd.Series, journeys: pd.DataFrame) -> dict[str, object]:
    group_names = [name for name in str(row.first_exposure_group_names).split("|") if name]
    local = journeys[
        journeys.municipality_bfs_id.eq(int(row.control_municipality_bfs_id))
        & journeys.station_group_name.isin(group_names)
        & as_bool(journeys.descriptive_accessibility_usable)
    ].sort_values("mean_one_way_generalized_minutes", kind="stable")
    if local.empty:
        return {
            "control_to_treated_entry_group_routes_available": 0,
            "control_nearest_treated_entry_group_name": "",
            "control_current_scheduled_nearest_treated_entry_group_minutes": np.nan,
            "specific_treated_group_route_status": (
                "no_complete_current_route_but_window_matrix_classifies_control_outside_120min"
            ),
        }
    nearest = local.iloc[0]
    return {
        "control_to_treated_entry_group_routes_available": int(len(local)),
        "control_nearest_treated_entry_group_name": nearest.station_group_name,
        "control_current_scheduled_nearest_treated_entry_group_minutes": float(
            nearest.mean_one_way_generalized_minutes
        ),
        "specific_treated_group_route_status": (
            "complete_current_route_above_120min"
            if float(nearest.mean_one_way_generalized_minutes) > SCHEDULED_ACCESS_LIMIT_MINUTES
            else "complete_current_route_within_120min"
        ),
    }


def build_audit(pairs: pd.DataFrame, journeys: pd.DataFrame) -> pd.DataFrame:
    candidates = pairs[
        as_bool(pairs.retained_in_strict_candidate_after_full_control_review)
    ].copy()
    if len(candidates) != EXPECTED_CANDIDATE_PAIRS:
        raise ValueError(f"Expected {EXPECTED_CANDIDATE_PAIRS} stage-21 candidate pairs")

    access = pd.DataFrame([
        specific_group_access(row, journeys) for _, row in candidates.iterrows()
    ], index=candidates.index)
    columns = [
        "treated_municipality_bfs_id", "treated_municipality_name", "first_exposure_month",
        "first_exposure_group_names", "control_municipality_bfs_id", "control_municipality_name",
        "comparison_candidate_type", "control_first_exposure_month_audit",
        "control_later_magic_exposure_after_review_window", "control_shared_current_territory",
        "treated_control_representative_distance_km",
        "control_minimum_representative_distance_to_window_magic_access_point_km",
        "control_network_proximity_band",
        "control_current_scheduled_nearest_window_magic_group_minutes",
        "control_current_scheduled_nearest_window_magic_group_name",
        "control_supplied_resort_points_in_municipality",
        "control_documented_competing_pass_link_in_window",
    ]
    audit = pd.concat([candidates[columns], access], axis=1)
    control_exposure = pd.to_datetime(audit.control_first_exposure_month_audit, errors="coerce")
    audit["control_not_exposed_during_review_window"] = (
        control_exposure.isna() | control_exposure.gt(WINDOW_END)
    )
    audit["pair_centres_more_than_50km_apart"] = (
        audit.treated_control_representative_distance_km.gt(PAIR_DISTANCE_LOW_DIRECT_RISK_KM)
    )
    audit["control_more_than_50km_from_window_magic_access_point"] = (
        audit.control_network_proximity_band.eq("beyond_50km")
    )
    audit["control_specific_entry_group_outside_120min_or_unroutable"] = (
        audit.control_current_scheduled_nearest_treated_entry_group_minutes.gt(
            SCHEDULED_ACCESS_LIMIT_MINUTES
        )
        | audit.control_current_scheduled_nearest_treated_entry_group_minutes.isna()
    )
    audit["direct_local_spillover_low_risk_by_declared_proxies"] = (
        audit.control_not_exposed_during_review_window
        & audit.pair_centres_more_than_50km_apart
        & audit.control_more_than_50km_from_window_magic_access_point
        & ~as_bool(audit.control_shared_current_territory)
        & audit.control_specific_entry_group_outside_120min_or_unroutable
    )
    audit["operational_tourist_basin_definition"] = (
        "municipality_reference_origin_within_120_current_scheduled_minutes_of_station_group"
    )
    audit["official_destination_boundary_used_as_hard_gate"] = False
    audit["direct_local_spillover_review_status"] = np.where(
        audit.direct_local_spillover_low_risk_by_declared_proxies,
        "screened_low_direct_local_risk_not_proof_of_absence",
        "direct_local_spillover_risk_requires_exclusion_or_additional_evidence",
    )
    audit["broad_visitor_market_substitution_status"] = (
        "unresolved_national_or_interregional_substitution_not_testable_from_distance"
    )
    audit["pair_spillover_review_completed"] = True
    audit["eligible_for_parallel_trend_diagnostic"] = (
        audit.direct_local_spillover_low_risk_by_declared_proxies
    )
    audit["causal_spillover_clearance_approved"] = False
    audit["source_id"] = "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN"
    return audit.sort_values(
        ["treated_municipality_name", "control_municipality_name"], kind="stable"
    )


def build_pair_screen(pairs: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "treated_municipality_bfs_id", "control_municipality_bfs_id",
        "control_to_treated_entry_group_routes_available",
        "control_nearest_treated_entry_group_name",
        "control_current_scheduled_nearest_treated_entry_group_minutes",
        "specific_treated_group_route_status", "control_not_exposed_during_review_window",
        "pair_centres_more_than_50km_apart",
        "control_more_than_50km_from_window_magic_access_point",
        "control_specific_entry_group_outside_120min_or_unroutable",
        "direct_local_spillover_low_risk_by_declared_proxies",
        "operational_tourist_basin_definition", "official_destination_boundary_used_as_hard_gate",
        "direct_local_spillover_review_status", "broad_visitor_market_substitution_status",
        "pair_spillover_review_completed", "eligible_for_parallel_trend_diagnostic",
        "causal_spillover_clearance_approved",
    ]
    out = pairs.merge(
        audit[fields],
        on=["treated_municipality_bfs_id", "control_municipality_bfs_id"],
        how="left", validate="one_to_one",
    )
    for column in [
        "pair_spillover_review_completed", "eligible_for_parallel_trend_diagnostic",
        "direct_local_spillover_low_risk_by_declared_proxies",
        "causal_spillover_clearance_approved",
    ]:
        out[column] = as_bool(out[column])
    candidates = as_bool(out.retained_in_strict_candidate_after_full_control_review)
    out["retained_for_parallel_trend_diagnostic_after_spillover_screen"] = (
        candidates & out.eligible_for_parallel_trend_diagnostic
    )
    out["stage22_pair_decision"] = np.select(
        [
            ~candidates,
            candidates & ~out.eligible_for_parallel_trend_diagnostic,
            out.retained_for_parallel_trend_diagnostic_after_spillover_screen,
        ],
        [
            "outside_stage21_candidate_set",
            "exclude_or_hold_due_direct_local_spillover_risk",
            "advance_to_pretrend_diagnostic_with_global_substitution_caveat",
        ],
        default="unexpected",
    )
    out["parallel_trends_approved_after_stage22"] = False
    out["causal_pair_approved_after_stage22"] = False
    out["pair_spillover_screen_source_id"] = "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN"
    return out


def build_worklist(pair_screen: pd.DataFrame) -> pd.DataFrame:
    retained = pair_screen[
        as_bool(pair_screen.retained_for_parallel_trend_diagnostic_after_spillover_screen)
    ].copy()
    columns = [
        "treated_municipality_bfs_id", "treated_municipality_name",
        "control_municipality_bfs_id", "control_municipality_name", "first_exposure_month",
        "first_exposure_group_names", "comparability_rank", "paired_pre_outcome_months",
        "pre_log_outcome_correlation", "pre_standardised_outcome_rmse",
        "pre_seasonal_profile_rmse", "pre_monthly_log_trend_gap_abs",
        "pre_log_bed_capacity_gap_abs", "pre_domestic_share_gap_abs",
        "direct_local_spillover_review_status", "broad_visitor_market_substitution_status",
        "control_current_scheduled_nearest_treated_entry_group_minutes",
        "specific_treated_group_route_status",
    ]
    worklist = retained[columns].copy()
    worklist["parallel_trend_diagnostic_status"] = "pending_predeclared_rule"
    worklist["parallel_trends_approved"] = False
    worklist["causal_pair_approved"] = False
    worklist["source_id"] = "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN"
    return worklist.sort_values(
        ["treated_municipality_name", "comparability_rank", "control_municipality_name"],
        kind="stable",
    )


def make_summary(audit: pd.DataFrame, pair_screen: pd.DataFrame, worklist: pd.DataFrame) -> dict:
    candidates = as_bool(pair_screen.retained_in_strict_candidate_after_full_control_review)
    low = as_bool(pair_screen.direct_local_spillover_low_risk_by_declared_proxies)
    advanced = as_bool(pair_screen.retained_for_parallel_trend_diagnostic_after_spillover_screen)
    return {
        "scheduled_access_limit_minutes": SCHEDULED_ACCESS_LIMIT_MINUTES,
        "pair_distance_support_threshold_km": PAIR_DISTANCE_LOW_DIRECT_RISK_KM,
        "all_input_pairs": int(len(pair_screen)),
        "stage21_candidate_pairs": int(candidates.sum()),
        "pairs_reviewed_for_direct_local_spillover": int(len(audit)),
        "pairs_low_direct_local_spillover_risk_by_declared_proxies": int((candidates & low).sum()),
        "pairs_advanced_to_parallel_trend_diagnostic": int(advanced.sum()),
        "pairs_with_specific_current_route_to_entry_group": int(
            audit.control_to_treated_entry_group_routes_available.gt(0).sum()
        ),
        "pairs_with_unroutable_specific_entry_group_but_window_matrix_non_exposure": int(
            audit.control_to_treated_entry_group_routes_available.eq(0).sum()
        ),
        "minimum_pair_centre_distance_km": float(audit.treated_control_representative_distance_km.min()),
        "minimum_observed_control_to_treated_entry_group_minutes": float(
            audit.control_current_scheduled_nearest_treated_entry_group_minutes.min()
        ),
        "broad_market_substitution_cleared_pairs": 0,
        "causal_spillover_clearances_approved": 0,
        "causal_pairs_approved": 0,
        "input_sha256": {
            PAIR_INPUT.relative_to(ROOT).as_posix(): sha256(PAIR_INPUT),
            JOURNEY_INPUT.relative_to(ROOT).as_posix(): sha256(JOURNEY_INPUT),
        },
        "source_id": "DERIVED_ACCESSIBILITY_PAIR_SPILLOVER_SCREEN",
        "interpretation": (
            "The screen supports low direct local interference for pretrend prioritisation only. "
            "It does not establish absence of national or interregional visitor substitution."
        ),
    }


def write_report(summary: dict) -> None:
    lines = [
        "# Bassins touristiques et spillovers - étape 22",
        "",
        "**Statut : screening spatial et de transport terminé; absence globale de spillover non démontrée.**",
        "",
        "## Définition opérationnelle du bassin",
        "",
        "Le bassin n'est pas défini par la commune administrative où se trouve la station. Il est défini, "
        "comme proposé pour cette extension, par le temps de trajet entre l'origine de référence du centre "
        "communal et les points d'accès des groupes de stations. Le seuil principal reste 120 minutes dans "
        "un sens. Les frontières officielles de destination ne sont pas utilisées comme frontière dure, car "
        "elles ne suffisent pas à décrire les visiteurs réels.",
        "",
        "## Résultat",
        "",
        f"Les {summary['pairs_reviewed_for_direct_local_spillover']} paires ont été contrôlées. Toutes sont "
        "à plus de 50 km entre centres communaux, tous les témoins sont à plus de 50 km d'un point Magic actif "
        "dans la fenêtre, et aucun témoin n'est exposé à moins de 120 minutes pendant novembre 2015-octobre 2019.",
        "",
        f"Pour {summary['pairs_with_specific_current_route_to_entry_group']} paires, une route actuelle complète "
        "vers au moins un groupe entrant est disponible; le minimum observé est "
        f"**{summary['minimum_observed_control_to_treated_entry_group_minutes']:.1f} minutes**, donc au-dessus du seuil. "
        f"Une paire n'a pas de route complète vers son groupe précis, mais son témoin reste classé hors du bassin "
        "de 120 minutes dans la matrice complète.",
        "",
        f"Les **{summary['pairs_advanced_to_parallel_trend_diagnostic']} paires** avancent donc au diagnostic "
        "des pré-tendances avec un risque direct local faible selon ces règles.",
        "",
        "## Limite importante",
        "",
        "Cette étape ne prouve pas que les marchés touristiques suisses sont indépendants. Un visiteur peut "
        "substituer un séjour entre régions éloignées, et l'horaire actuel n'est pas une reconstitution parfaite "
        "de 2017. Le statut obtenu autorise seulement le test statistique suivant; il n'accorde ni contrôle causal "
        "ni effet causal. Les sensibilités finales devront retirer tour à tour les témoins et les cas touristiques "
        "les plus exposés à une substitution large.",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_pair_spillover_evidence.csv` : diagnostic des 21 paires ;",
        "- `data_processed/accessibility_comparison_spillover_screen.csv` : statut étape 22 des 70 paires ;",
        "- `reports/accessibility_parallel_trend_worklist.csv` : 21 paires prêtes pour la règle de pré-tendances ;",
        "- `reports/accessibility_pair_spillover_summary.json` : seuils, compteurs et empreintes.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    pairs = pd.read_csv(PAIR_INPUT)
    journeys = pd.read_csv(JOURNEY_INPUT)
    if len(pairs) != EXPECTED_ALL_PAIRS:
        raise ValueError(f"Expected {EXPECTED_ALL_PAIRS} input pairs")
    audit = build_audit(pairs, journeys)
    pair_screen = build_pair_screen(pairs, audit)
    worklist = build_worklist(pair_screen)
    summary = make_summary(audit, pair_screen, worklist)
    expected = {
        "pairs_reviewed_for_direct_local_spillover": EXPECTED_CANDIDATE_PAIRS,
        "pairs_low_direct_local_spillover_risk_by_declared_proxies": EXPECTED_CANDIDATE_PAIRS,
        "pairs_advanced_to_parallel_trend_diagnostic": EXPECTED_CANDIDATE_PAIRS,
        "pairs_with_specific_current_route_to_entry_group": 20,
        "pairs_with_unroutable_specific_entry_group_but_window_matrix_non_exposure": 1,
    }
    for key, value in expected.items():
        if summary[key] != value:
            raise ValueError(f"Expected {key}={value}, got {summary[key]}")
    if summary["minimum_pair_centre_distance_km"] <= PAIR_DISTANCE_LOW_DIRECT_RISK_KM:
        raise ValueError("A candidate pair violates the predeclared 50 km support condition")
    if summary["minimum_observed_control_to_treated_entry_group_minutes"] <= SCHEDULED_ACCESS_LIMIT_MINUTES:
        raise ValueError("A candidate control falls within 120 minutes of a treated entry group")

    AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PAIR_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT_OUTPUT, index=False, lineterminator="\n")
    pair_screen.to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")
    worklist.to_csv(WORKLIST_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
