"""Rank comparison municipalities for the first-accessible-exposure design.

The ranking uses only 36 pre-anchor months.  It prioritises manual control review
and never approves a causal control or estimates a Magic Pass effect.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
FIRST_EXPOSURE_PATH = ROOT / "reports" / "accessibility_first_exposure_audit.csv"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_first_exposure_pretrend_pairs.csv"
SHORTLIST_OUTPUT = ROOT / "reports" / "accessibility_first_exposure_pretrend_shortlist.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_first_exposure_pretrend_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "59_SCREENING_COMPARAISONS_PRE_EXPOSITION_FR.md"

ANCHOR = pd.Timestamp("2017-11-01")
PRE_MONTHS = 36
MIN_PAIRED_OUTCOME_MONTHS = 30
MIN_METRICS = 5
SHORTLIST_SIZE = 5


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def deseasonalized_trend(log_values: pd.Series, dates: pd.Series) -> float:
    valid = log_values.notna() & dates.notna()
    if int(valid.sum()) < 24:
        return np.nan
    y = log_values.loc[valid].to_numpy(dtype=float)
    date = pd.to_datetime(dates.loc[valid])
    time = (
        (date.dt.year - date.dt.year.min()) * 12
        + date.dt.month
        - date.dt.month.min()
    ).to_numpy(dtype=float)
    month_dummies = pd.get_dummies(date.dt.month, drop_first=True, dtype=float)
    matrix = np.column_stack([np.ones(len(y)), time, month_dummies.to_numpy()])
    coefficients, *_ = np.linalg.lstsq(matrix, y, rcond=None)
    return float(coefficients[1])


def standardised_rmse(left: pd.Series, right: pd.Series) -> float:
    valid = left.notna() & right.notna()
    left_values = left.loc[valid].to_numpy(dtype=float)
    right_values = right.loc[valid].to_numpy(dtype=float)
    if len(left_values) < 24 or np.std(left_values) == 0 or np.std(right_values) == 0:
        return np.nan
    left_z = (left_values - np.mean(left_values)) / np.std(left_values)
    right_z = (right_values - np.mean(right_values)) / np.std(right_values)
    return float(np.sqrt(np.mean((left_z - right_z) ** 2)))


def seasonal_profile_rmse(
    left: pd.Series, right: pd.Series, month: pd.Series
) -> float:
    frame = pd.DataFrame({"left": left, "right": right, "month": month}).dropna()
    profile = frame.groupby("month")[["left", "right"]].mean()
    if len(profile) != 12:
        return np.nan
    profile = profile - profile.mean(axis=0)
    return float(np.sqrt(np.mean((profile.left - profile.right) ** 2)))


def comparison_candidates(
    first_exposure: pd.DataFrame, panel: pd.DataFrame
) -> pd.DataFrame:
    dates = pd.date_range(
        ANCHOR - pd.DateOffset(months=24),
        ANCHOR + pd.DateOffset(months=23),
        freq="MS",
    )
    window = panel[panel.date.isin(dates)]
    support = (
        window.groupby(["municipality_bfs_id", "municipality_name_source"])
        .agg(
            rows=("date", "size"),
            observed_hotel_months=("hotel_overnights", lambda values: int(values.notna().sum())),
            accessible_entries_in_window=("new_station_group_entry_count_120min", "sum"),
        )
        .reset_index()
    )
    support = support[
        support.rows.eq(48)
        & support.observed_hotel_months.eq(48)
        & support.accessible_entries_in_window.eq(0)
    ].copy()
    support = support.merge(
        first_exposure[
            [
                "municipality_bfs_id",
                "ever_accessible_120min",
                "first_exposure_month",
            ]
        ],
        on="municipality_bfs_id",
        how="left",
        validate="one_to_one",
    )
    support["comparison_candidate_type"] = np.where(
        as_bool(support.ever_accessible_120min),
        "not_yet_exposed_during_2015_11_to_2019_10",
        "never_exposed_in_current_120min_matrix",
    )
    support["causal_control_approved"] = False
    return support.sort_values("municipality_bfs_id", kind="stable")


def build_pair_metrics(
    treated: pd.DataFrame, controls: pd.DataFrame, panel: pd.DataFrame
) -> pd.DataFrame:
    start = ANCHOR - pd.DateOffset(months=PRE_MONTHS)
    end = ANCHOR - pd.DateOffset(months=1)
    pre = panel[panel.date.between(start, end)].copy()
    rows = []
    for treatment in treated.itertuples(index=False):
        treatment_month = pre[
            pre.municipality_bfs_id.eq(int(treatment.municipality_bfs_id))
        ][
            [
                "date",
                "hotel_overnights",
                "hotel_beds_available",
                "domestic_overnights",
                "foreign_overnights",
            ]
        ]
        for control in controls.itertuples(index=False):
            control_month = pre[
                pre.municipality_bfs_id.eq(int(control.municipality_bfs_id))
            ][
                [
                    "date",
                    "hotel_overnights",
                    "hotel_beds_available",
                    "domestic_overnights",
                    "foreign_overnights",
                ]
            ]
            paired = treatment_month.merge(
                control_month,
                on="date",
                how="outer",
                suffixes=("_treated", "_control"),
                validate="one_to_one",
            ).sort_values("date")
            outcomes = paired[
                paired.hotel_overnights_treated.notna()
                & paired.hotel_overnights_control.notna()
            ].copy()
            treated_log = np.log1p(outcomes.hotel_overnights_treated)
            control_log = np.log1p(outcomes.hotel_overnights_control)
            beds = paired[
                paired.hotel_beds_available_treated.notna()
                & paired.hotel_beds_available_control.notna()
            ]
            treated_trend = deseasonalized_trend(treated_log, outcomes.date)
            control_trend = deseasonalized_trend(control_log, outcomes.date)
            treated_origin = paired[
                paired.domestic_overnights_treated.notna()
                & paired.foreign_overnights_treated.notna()
            ]
            control_origin = paired[
                paired.domestic_overnights_control.notna()
                & paired.foreign_overnights_control.notna()
            ]
            treated_domestic_share = (
                treated_origin.domestic_overnights_treated.sum()
                / (
                    treated_origin.domestic_overnights_treated.sum()
                    + treated_origin.foreign_overnights_treated.sum()
                )
                if len(treated_origin)
                and (
                    treated_origin.domestic_overnights_treated.sum()
                    + treated_origin.foreign_overnights_treated.sum()
                )
                > 0
                else np.nan
            )
            control_domestic_share = (
                control_origin.domestic_overnights_control.sum()
                / (
                    control_origin.domestic_overnights_control.sum()
                    + control_origin.foreign_overnights_control.sum()
                )
                if len(control_origin)
                and (
                    control_origin.domestic_overnights_control.sum()
                    + control_origin.foreign_overnights_control.sum()
                )
                > 0
                else np.nan
            )
            rows.append(
                {
                    "treated_municipality_bfs_id": int(treatment.municipality_bfs_id),
                    "treated_municipality_name": treatment.municipality_name,
                    "first_exposure_month": treatment.first_exposure_month,
                    "groups_entering_at_first_exposure": int(
                        treatment.groups_entering_at_first_exposure
                    ),
                    "first_exposure_group_names": treatment.first_exposure_group_names,
                    "control_municipality_bfs_id": int(control.municipality_bfs_id),
                    "control_municipality_name": control.municipality_name_source,
                    "comparison_candidate_type": control.comparison_candidate_type,
                    "control_first_exposure_month": control.first_exposure_month,
                    "pre_window_start": start.date().isoformat(),
                    "pre_window_end": end.date().isoformat(),
                    "paired_pre_outcome_months": int(len(outcomes)),
                    "paired_pre_capacity_months": int(len(beds)),
                    "pre_log_outcome_correlation": (
                        float(treated_log.corr(control_log))
                        if len(outcomes) >= 24
                        else np.nan
                    ),
                    "pre_log_outcome_level_gap_abs": (
                        float(abs(treated_log.mean() - control_log.mean()))
                        if len(outcomes)
                        else np.nan
                    ),
                    "pre_standardised_outcome_rmse": standardised_rmse(
                        treated_log, control_log
                    ),
                    "pre_seasonal_profile_rmse": seasonal_profile_rmse(
                        treated_log, control_log, outcomes.date.dt.month
                    ),
                    "treated_monthly_log_trend": treated_trend,
                    "control_monthly_log_trend": control_trend,
                    "pre_monthly_log_trend_gap_abs": (
                        abs(treated_trend - control_trend)
                        if np.isfinite(treated_trend) and np.isfinite(control_trend)
                        else np.nan
                    ),
                    "pre_log_bed_capacity_gap_abs": (
                        float(
                            abs(
                                np.log1p(beds.hotel_beds_available_treated).mean()
                                - np.log1p(beds.hotel_beds_available_control).mean()
                            )
                        )
                        if len(beds) >= 24
                        else np.nan
                    ),
                    "pre_domestic_share_gap_abs": (
                        abs(treated_domestic_share - control_domestic_share)
                        if np.isfinite(treated_domestic_share)
                        and np.isfinite(control_domestic_share)
                        else np.nan
                    ),
                    "historical_access_validation_status": "pending_for_treated_municipality",
                    "control_external_shock_review_status": "pending",
                    "spillover_review_status": "current_120min_non_exposure_only",
                    "causal_control_approved": False,
                }
            )
    return pd.DataFrame(rows)


def rank_pairs(pairs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    ranking_features = [
        "pre_correlation_loss",
        "pre_log_outcome_level_gap_abs",
        "pre_standardised_outcome_rmse",
        "pre_seasonal_profile_rmse",
        "pre_monthly_log_trend_gap_abs",
        "pre_log_bed_capacity_gap_abs",
        "pre_domestic_share_gap_abs",
    ]
    pairs = pairs.copy()
    pairs["pre_correlation_loss"] = 1 - pairs.pre_log_outcome_correlation
    parts = []
    for _, group in pairs.groupby("treated_municipality_bfs_id", sort=False):
        group = group.copy()
        ranks = group[ranking_features].rank(method="average", pct=True, ascending=True)
        group["comparability_components_available"] = ranks.notna().sum(axis=1)
        group["descriptive_pretrend_comparability_score"] = (
            100 * (1 - ranks.mean(axis=1, skipna=True))
        ).round(2)
        usable = (
            group.paired_pre_outcome_months.ge(MIN_PAIRED_OUTCOME_MONTHS)
            & group.comparability_components_available.ge(MIN_METRICS)
        )
        group["pretrend_screen_usable"] = usable
        group["comparability_rank"] = pd.NA
        group.loc[usable, "comparability_rank"] = (
            group.loc[usable, "descriptive_pretrend_comparability_score"]
            .rank(method="first", ascending=False)
            .astype(int)
        )
        parts.append(group)
    ranked = pd.concat(parts, ignore_index=True).sort_values(
        ["treated_municipality_bfs_id", "comparability_rank", "control_municipality_bfs_id"],
        na_position="last",
        kind="stable",
    )
    shortlist = ranked[
        ranked.pretrend_screen_usable
        & pd.to_numeric(ranked.comparability_rank, errors="coerce").le(SHORTLIST_SIZE)
    ].copy()
    shortlist["manual_comparison_review_priority"] = True
    shortlist["causal_control_approved"] = False
    return ranked, shortlist


def main() -> None:
    first_exposure = pd.read_csv(FIRST_EXPOSURE_PATH)
    panel = pd.read_csv(PANEL_PATH)
    panel["date"] = pd.to_datetime(panel.date, errors="raise")
    treated = first_exposure[
        as_bool(first_exposure.first_exposure_candidate_for_manual_design_review)
    ].copy()
    controls = comparison_candidates(first_exposure, panel)
    if len(treated) != 19 or len(controls) != 132:
        raise ValueError("Unexpected first-exposure treatment/comparison screen")
    pairs = build_pair_metrics(treated, controls, panel)
    ranked, shortlist = rank_pairs(pairs)
    if len(ranked) != 19 * 132:
        raise ValueError("Pair grid is incomplete")
    if shortlist.groupby("treated_municipality_bfs_id").size().ne(SHORTLIST_SIZE).any():
        raise ValueError("Every treated municipality must receive five provisional comparisons")
    if ranked.causal_control_approved.any() or shortlist.causal_control_approved.any():
        raise ValueError("Pretrend ranking must not approve causal controls")

    PAIR_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ranked.to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")
    shortlist.to_csv(SHORTLIST_OUTPUT, index=False, lineterminator="\n")
    unique_shortlist = shortlist.control_municipality_bfs_id.nunique()
    never_shortlist = shortlist.comparison_candidate_type.eq(
        "never_exposed_in_current_120min_matrix"
    ).sum()
    summary = {
        "analysis_date": "2026-10-02",
        "analysis_anchor": ANCHOR.date().isoformat(),
        "pre_window_months": PRE_MONTHS,
        "first_exposure_treated_municipalities_screened": len(treated),
        "mechanical_comparison_municipalities": len(controls),
        "never_exposed_comparison_municipalities": int(
            controls.comparison_candidate_type.eq(
                "never_exposed_in_current_120min_matrix"
            ).sum()
        ),
        "not_yet_exposed_comparison_municipalities": int(
            controls.comparison_candidate_type.ne(
                "never_exposed_in_current_120min_matrix"
            ).sum()
        ),
        "treatment_comparison_pairs_screened": len(ranked),
        "pairs_usable_for_descriptive_pretrend_ranking": int(
            ranked.pretrend_screen_usable.sum()
        ),
        "shortlisted_pairs_for_manual_review": len(shortlist),
        "unique_shortlisted_comparison_municipalities": int(unique_shortlist),
        "shortlisted_pairs_with_never_exposed_control": int(never_shortlist),
        "median_shortlist_pre_log_outcome_correlation": float(
            shortlist.pre_log_outcome_correlation.median()
        ),
        "median_shortlist_pre_monthly_log_trend_gap_abs": float(
            shortlist.pre_monthly_log_trend_gap_abs.median()
        ),
        "historical_access_validated_treated_municipalities": 0,
        "manual_control_external_shock_reviews_complete": 0,
        "parallel_trends_approved": False,
        "causal_controls_approved": 0,
        "causal_treatments_approved": 0,
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in [FIRST_EXPOSURE_PATH, PANEL_PATH]
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    preview_rows = []
    for row in shortlist[shortlist.comparability_rank.eq(1)].sort_values(
        "treated_municipality_name"
    ).itertuples(index=False):
        preview_rows.append(
            f"| {row.treated_municipality_name} | {row.groups_entering_at_first_exposure} | "
            f"{row.control_municipality_name} | {row.comparison_candidate_type.replace('_', ' ')} | "
            f"{row.descriptive_pretrend_comparability_score:.1f} | "
            f"{row.pre_log_outcome_correlation:.3f} | "
            f"{row.pre_monthly_log_trend_gap_abs:.4f} |"
        )
    report = f"""# Screening des comparaisons avant première exposition — étape 12

## Résultat

Le dessin communal proposé dans le rapport 58 retient **{len(treated)} communes** dont la première exposition accessible se situe au lancement de novembre 2017, avec 24 mois observés avant et après, aucun COVID dans la fenêtre et aucune nouvelle entrée accessible pendant les 24 mois postérieurs. **{len(controls)} communes** ont une issue complète et aucune entrée accessible dans la même fenêtre : {summary['never_exposed_comparison_municipalities']} ne sont jamais exposées dans la matrice actuelle et {summary['not_yet_exposed_comparison_municipalities']} ne le deviennent que plus tard.

Les **{len(ranked):,} couples** sont comparés uniquement sur les 36 mois antérieurs : niveau et forme des nuitées, saisonnalité, tendance désaisonnalisée, lits disponibles et part domestique. Les cinq meilleures comparaisons relatives par commune produisent **{len(shortlist)} couples**, impliquant {unique_shortlist} communes de comparaison distinctes. Le score sert uniquement à prioriser une revue manuelle.

## Meilleure comparaison mécanique par commune traitée

| Commune exposée | Groupes à la première exposition | Comparaison provisoire | Statut | Score relatif | Corrélation pré | Écart de tendance mensuelle |
|---|---:|---|---|---:|---:|---:|
{chr(10).join(preview_rows)}

## Ce que ce screening permet — et ne permet pas

Le résultat montre qu'un groupe de comparaison communal plus large existe mécaniquement; il ne valide pas les tendances parallèles. Le score est relatif à chaque commune traitée et ne doit pas être comparé entre lignes. Il ne vérifie encore ni les chocs touristiques locaux, ni les autres forfaits, ni les investissements hôteliers ou de remontées, ni les débordements au-delà du seuil de 120 minutes.

L'accès de 2026 est toujours projeté sur 2017. Il faut donc d'abord auditer l'existence et la plausibilité des liaisons historiques pour les 19 communes traitées, puis examiner les 95 couples présélectionnés. **Zéro contrôle, zéro traitement et aucune hypothèse de tendances parallèles ne sont approuvés.**

## Fichiers

- `data_processed/accessibility_first_exposure_pretrend_pairs.csv` : les 2 508 couples et leurs mesures pré-traitement;
- `reports/accessibility_first_exposure_pretrend_shortlist.csv` : cinq comparaisons provisoires par commune exposée;
- `reports/accessibility_first_exposure_pretrend_summary.json` : comptes, décisions et empreintes.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
