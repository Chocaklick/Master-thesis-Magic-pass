"""Apply predeclared pair-level pretrend diagnostics after the spillover screen."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RULE_PATH = ROOT / "config" / "accessibility_parallel_trend_rules.json"
PAIR_INPUT = ROOT / "data_processed" / "accessibility_comparison_spillover_screen.csv"
PANEL_INPUT = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"

AUDIT_OUTPUT = ROOT / "reports" / "accessibility_parallel_trend_diagnostics.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_comparison_parallel_trend_screen.csv"
CORE_OUTPUT = ROOT / "reports" / "accessibility_estimation_candidate_pairs.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_parallel_trend_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "70_DIAGNOSTIC_PRETENDANCES_COMPARAISONS_FR.md"

EXPECTED_ALL_PAIRS = 70
EXPECTED_WORKLIST_PAIRS = 21


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hac_trend(values: np.ndarray, months: np.ndarray, max_lag: int) -> dict[str, float | bool]:
    """OLS trend with month-of-year fixed effects and Newey-West covariance."""
    n = len(values)
    time = np.arange(n, dtype=float)
    time -= time.mean()
    month_dummies = np.column_stack([(months == month).astype(float) for month in range(2, 13)])
    x = np.column_stack([np.ones(n), time, month_dummies])
    beta, _, rank, _ = np.linalg.lstsq(x, values, rcond=None)
    if rank < x.shape[1]:
        raise ValueError("Pretrend regression is rank deficient")
    residuals = values - x @ beta
    xtx_inv = np.linalg.inv(x.T @ x)
    score = x * residuals[:, None]
    meat = score.T @ score
    lag_limit = min(max_lag, n - 1)
    for lag in range(1, lag_limit + 1):
        weight = 1.0 - lag / (lag_limit + 1.0)
        gamma = score[lag:].T @ score[:-lag]
        meat += weight * (gamma + gamma.T)
    covariance = xtx_inv @ meat @ xtx_inv
    slope = float(beta[1])
    standard_error = float(np.sqrt(max(covariance[1, 1], 0.0)))
    lower = slope - 1.96 * standard_error
    upper = slope + 1.96 * standard_error
    return {
        "seasonally_adjusted_monthly_difference_trend": slope,
        "absolute_seasonally_adjusted_monthly_difference_trend": abs(slope),
        "hac_trend_standard_error": standard_error,
        "hac_trend_ci95_lower": lower,
        "hac_trend_ci95_upper": upper,
        "hac_trend_ci95_contains_zero": bool(lower <= 0 <= upper),
        "annualised_differential_trend_pct": float(np.expm1(12 * slope)),
    }


def pair_preperiod(row: pd.Series, panel: pd.DataFrame, required_months: int, hac_lag: int) -> dict:
    anchor = pd.Timestamp(row.first_exposure_month)
    start = anchor - pd.DateOffset(months=required_months)
    end = anchor - pd.DateOffset(months=1)
    treated = panel[
        panel.municipality_bfs_id.eq(int(row.treated_municipality_bfs_id))
        & panel.date.between(start, end)
    ][["date", "log_overnights"]].rename(columns={"log_overnights": "treated_log"})
    control = panel[
        panel.municipality_bfs_id.eq(int(row.control_municipality_bfs_id))
        & panel.date.between(start, end)
    ][["date", "log_overnights"]].rename(columns={"log_overnights": "control_log"})
    joined = treated.merge(control, on="date", how="inner", validate="one_to_one").dropna()
    if len(joined) != required_months:
        return {
            "diagnostic_pre_months": int(len(joined)),
            "pre_period_start": start.date().isoformat(),
            "pre_period_end": end.date().isoformat(),
            "seasonally_adjusted_monthly_difference_trend": np.nan,
            "absolute_seasonally_adjusted_monthly_difference_trend": np.nan,
            "hac_trend_standard_error": np.nan,
            "hac_trend_ci95_lower": np.nan,
            "hac_trend_ci95_upper": np.nan,
            "hac_trend_ci95_contains_zero": False,
            "annualised_differential_trend_pct": np.nan,
        }
    difference = (joined.treated_log - joined.control_log).to_numpy(float)
    diagnostics = hac_trend(
        difference, joined.date.dt.month.to_numpy(int), max_lag=hac_lag
    )
    return {
        "diagnostic_pre_months": int(len(joined)),
        "pre_period_start": start.date().isoformat(),
        "pre_period_end": end.date().isoformat(),
        **diagnostics,
    }


def passes_rule(frame: pd.DataFrame, rule: dict, required_months: int) -> pd.Series:
    return (
        frame.diagnostic_pre_months.ge(required_months)
        & frame.pre_log_outcome_correlation.ge(rule["minimum_log_outcome_correlation"])
        & frame.pre_standardised_outcome_rmse.le(rule["maximum_standardised_outcome_rmse"])
        & frame.pre_seasonal_profile_rmse.le(rule["maximum_seasonal_profile_rmse"])
        & frame.absolute_seasonally_adjusted_monthly_difference_trend.le(
            rule["maximum_absolute_seasonally_adjusted_monthly_difference_trend"]
        )
    )


def build_audit(pairs: pd.DataFrame, panel: pd.DataFrame, rules: dict) -> pd.DataFrame:
    worklist = pairs[
        as_bool(pairs.retained_for_parallel_trend_diagnostic_after_spillover_screen)
    ].copy()
    if len(worklist) != EXPECTED_WORKLIST_PAIRS:
        raise ValueError(f"Expected {EXPECTED_WORKLIST_PAIRS} pretrend worklist pairs")
    required = int(rules["pre_period_months_required"])
    hac_lag = int(rules["hac_lag_months"])
    computed = pd.DataFrame([
        pair_preperiod(row, panel, required, hac_lag) for _, row in worklist.iterrows()
    ], index=worklist.index)
    columns = [
        "treated_municipality_bfs_id", "treated_municipality_name", "first_exposure_month",
        "first_exposure_group_names", "control_municipality_bfs_id", "control_municipality_name",
        "comparability_rank", "pre_log_outcome_correlation",
        "pre_standardised_outcome_rmse", "pre_seasonal_profile_rmse",
        "pre_monthly_log_trend_gap_abs", "pre_log_bed_capacity_gap_abs",
        "pre_domestic_share_gap_abs", "direct_local_spillover_review_status",
        "broad_visitor_market_substitution_status",
    ]
    audit = pd.concat([worklist[columns], computed], axis=1)
    audit["primary_pretrend_rule_passed"] = passes_rule(audit, rules["primary"], required)
    audit["sensitivity_pretrend_rule_passed"] = passes_rule(
        audit, rules["sensitivity"], required
    )
    if (audit.primary_pretrend_rule_passed & ~audit.sensitivity_pretrend_rule_passed).any():
        raise ValueError("Primary rule must be nested inside sensitivity rule")
    audit["pretrend_diagnostic_class"] = np.select(
        [
            audit.primary_pretrend_rule_passed,
            audit.sensitivity_pretrend_rule_passed,
        ],
        [
            "primary_compatible_not_proof",
            "sensitivity_only_not_primary",
        ],
        default="fails_predeclared_pretrend_magnitude_rule",
    )
    failure_columns = {
        "insufficient_pre_months": audit.diagnostic_pre_months.lt(required),
        "correlation_below_primary_minimum": audit.pre_log_outcome_correlation.lt(
            rules["primary"]["minimum_log_outcome_correlation"]
        ),
        "standardised_rmse_above_primary_maximum": audit.pre_standardised_outcome_rmse.gt(
            rules["primary"]["maximum_standardised_outcome_rmse"]
        ),
        "seasonal_rmse_above_primary_maximum": audit.pre_seasonal_profile_rmse.gt(
            rules["primary"]["maximum_seasonal_profile_rmse"]
        ),
        "differential_trend_above_primary_maximum": (
            audit.absolute_seasonally_adjusted_monthly_difference_trend.gt(
                rules["primary"]["maximum_absolute_seasonally_adjusted_monthly_difference_trend"]
            )
        ),
    }
    audit["primary_rule_failure_reasons"] = [
        "|".join(name for name, flags in failure_columns.items() if bool(flags.loc[index]))
        for index in audit.index
    ]
    audit["eligible_for_primary_estimation_sensitivity"] = audit.primary_pretrend_rule_passed
    audit["eligible_for_relaxed_estimation_sensitivity"] = audit.sensitivity_pretrend_rule_passed
    audit["parallel_trends_approved"] = False
    audit["causal_pair_approved"] = False
    audit["rule_version"] = rules["rule_version"]
    audit["source_id"] = "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC"
    return audit.sort_values(
        ["treated_municipality_name", "comparability_rank", "control_municipality_name"],
        kind="stable",
    )


def build_pair_screen(pairs: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "treated_municipality_bfs_id", "control_municipality_bfs_id",
        "diagnostic_pre_months", "seasonally_adjusted_monthly_difference_trend",
        "absolute_seasonally_adjusted_monthly_difference_trend",
        "hac_trend_standard_error", "hac_trend_ci95_lower", "hac_trend_ci95_upper",
        "hac_trend_ci95_contains_zero", "annualised_differential_trend_pct",
        "primary_pretrend_rule_passed", "sensitivity_pretrend_rule_passed",
        "pretrend_diagnostic_class", "primary_rule_failure_reasons",
        "eligible_for_primary_estimation_sensitivity",
        "eligible_for_relaxed_estimation_sensitivity", "rule_version",
    ]
    out = pairs.merge(
        audit[fields],
        on=["treated_municipality_bfs_id", "control_municipality_bfs_id"],
        how="left", validate="one_to_one",
    )
    for column in [
        "primary_pretrend_rule_passed", "sensitivity_pretrend_rule_passed",
        "eligible_for_primary_estimation_sensitivity",
        "eligible_for_relaxed_estimation_sensitivity",
    ]:
        out[column] = as_bool(out[column])
    worklist = as_bool(out.retained_for_parallel_trend_diagnostic_after_spillover_screen)
    out["stage23_pair_decision"] = np.select(
        [
            ~worklist,
            out.primary_pretrend_rule_passed,
            ~out.primary_pretrend_rule_passed & out.sensitivity_pretrend_rule_passed,
            worklist,
        ],
        [
            "outside_stage22_pretrend_worklist",
            "retain_primary_estimation_sensitivity_candidate",
            "retain_relaxed_sensitivity_only",
            "exclude_from_estimation_sensitivity_due_pretrend_rule",
        ],
        default="unexpected",
    )
    out["parallel_trends_approved_after_stage23"] = False
    out["causal_pair_approved_after_stage23"] = False
    out["parallel_trend_diagnostic_source_id"] = (
        "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC"
    )
    return out


def build_core(audit: pd.DataFrame) -> pd.DataFrame:
    core = audit[audit.sensitivity_pretrend_rule_passed].copy()
    core["estimation_candidate_tier"] = np.where(
        core.primary_pretrend_rule_passed, "primary", "relaxed_sensitivity_only"
    )
    core["historical_access_status"] = (
        "retained_under_2018_feed_with_projected_2026_transfer_topology_sensitivity"
    )
    core["broad_market_substitution_cleared"] = False
    core["causal_estimation_approved"] = False
    return core


def make_summary(audit: pd.DataFrame, pair_screen: pd.DataFrame, core: pd.DataFrame, rules: dict) -> dict:
    primary = as_bool(audit.primary_pretrend_rule_passed)
    sensitivity = as_bool(audit.sensitivity_pretrend_rule_passed)
    return {
        "rule_version": rules["rule_version"],
        "pre_period_months_required": rules["pre_period_months_required"],
        "hac_lag_months": rules["hac_lag_months"],
        "primary_rule": rules["primary"],
        "sensitivity_rule": rules["sensitivity"],
        "all_input_pairs": int(len(pair_screen)),
        "pairs_diagnosed": int(len(audit)),
        "primary_compatible_pairs": int(primary.sum()),
        "primary_compatible_treated_municipalities": int(
            audit.loc[primary, "treated_municipality_bfs_id"].nunique()
        ),
        "sensitivity_compatible_pairs_including_primary": int(sensitivity.sum()),
        "sensitivity_only_pairs": int((sensitivity & ~primary).sum()),
        "pairs_failing_sensitivity_rule": int((~sensitivity).sum()),
        "treated_municipalities_without_primary_pair": int(
            len(set(audit.treated_municipality_bfs_id) - set(audit.loc[primary, "treated_municipality_bfs_id"]))
        ),
        "hac_intervals_containing_zero": int(as_bool(audit.hac_trend_ci95_contains_zero).sum()),
        "estimation_candidate_rows": int(len(core)),
        "parallel_trends_approved": 0,
        "causal_pairs_approved": 0,
        "input_sha256": {
            RULE_PATH.relative_to(ROOT).as_posix(): sha256(RULE_PATH),
            PAIR_INPUT.relative_to(ROOT).as_posix(): sha256(PAIR_INPUT),
            PANEL_INPUT.relative_to(ROOT).as_posix(): sha256(PANEL_INPUT),
        },
        "source_id": "DERIVED_ACCESSIBILITY_PARALLEL_TREND_DIAGNOSTIC",
        "interpretation": rules["interpretation"],
    }


def write_report(audit: pd.DataFrame, summary: dict) -> None:
    lines = [
        "# Diagnostic des pré-tendances - étape 23",
        "",
        "**Statut : compatibilité pré-traitement, pas preuve de tendances parallèles.**",
        "",
        "## Règle fixée avant le calcul",
        "",
        "La règle principale exige 36 mois communs, une corrélation des log-nuitées d'au moins 0,70, "
        "un RMSE standardisé au plus égal à 0,80, un RMSE saisonnier au plus égal à 0,25 et une "
        "pente différentielle mensuelle désaisonnalisée d'au plus 0,005 en valeur absolue. Une règle "
        "secondaire plus souple (0,60; 0,90; 0,30; 0,0075) sert uniquement de sensibilité.",
        "",
        "L'incertitude de la pente est calculée avec une covariance Newey-West à 12 retards. L'inclusion "
        "de zéro dans l'intervalle à 95% est rapportée, mais ne suffit jamais à accepter une paire.",
        "",
        "## Résultat",
        "",
        f"Sur {summary['pairs_diagnosed']} paires, **{summary['primary_compatible_pairs']}** passent la règle "
        f"principale et couvrent **{summary['primary_compatible_treated_municipalities']} communes traitées**. "
        f"{summary['sensitivity_only_pairs']} paires supplémentaires passent seulement la sensibilité relâchée, pour un total de "
        f"**{summary['sensitivity_compatible_pairs_including_primary']}**. "
        f"**{summary['pairs_failing_sensitivity_rule']}** échouent même à la règle souple.",
        "",
        "| Commune traitée | Témoins règle principale | Témoins sensibilité seulement | Échecs |",
        "|---|---|---|---|",
    ]
    for treated, group in audit.groupby("treated_municipality_name", sort=True):
        primary_names = ", ".join(group.loc[group.primary_pretrend_rule_passed, "control_municipality_name"])
        sensitivity_names = ", ".join(group.loc[
            group.sensitivity_pretrend_rule_passed & ~group.primary_pretrend_rule_passed,
            "control_municipality_name",
        ])
        failed_names = ", ".join(group.loc[~group.sensitivity_pretrend_rule_passed, "control_municipality_name"])
        lines.append(
            f"| {treated} | {primary_names or 'aucun'} | {sensitivity_names or 'aucun'} | {failed_names or 'aucun'} |"
        )
    lines += [
        "",
        "## Interprétation",
        "",
        "Ces règles réduisent le noyau sans sélectionner sur les résultats postérieurs. Elles montrent surtout "
        "qu'aucune paire de Haut-Intyamon ne présente une pré-tendance assez proche, ce qui empêche de retenir "
        "cette commune dans le noyau principal actuel. Les paires retenues restent des candidats de sensibilité : "
        "l'accès historique repose sur une topologie de transfert projetée et la substitution touristique large "
        "n'est pas éliminée. Les drapeaux `parallel_trends_approved` et `causal_pair_approved` restent donc faux.",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_parallel_trend_diagnostics.csv` : 21 diagnostics et motifs d'échec ;",
        "- `data_processed/accessibility_comparison_parallel_trend_screen.csv` : statut étape 23 des 70 paires ;",
        "- `reports/accessibility_estimation_candidate_pairs.csv` : noyau principal et sensibilité relâchée ;",
        "- `reports/accessibility_parallel_trend_summary.json` : règles, compteurs et empreintes.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rules = json.loads(RULE_PATH.read_text(encoding="utf-8"))
    pairs = pd.read_csv(PAIR_INPUT)
    panel = pd.read_csv(PANEL_INPUT)
    panel["date"] = pd.to_datetime(panel.date, errors="raise")
    if len(pairs) != EXPECTED_ALL_PAIRS:
        raise ValueError(f"Expected {EXPECTED_ALL_PAIRS} input pairs")
    audit = build_audit(pairs, panel, rules)
    pair_screen = build_pair_screen(pairs, audit)
    core = build_core(audit)
    summary = make_summary(audit, pair_screen, core, rules)

    AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PAIR_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT_OUTPUT, index=False, lineterminator="\n")
    pair_screen.to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")
    core.to_csv(CORE_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(audit, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
