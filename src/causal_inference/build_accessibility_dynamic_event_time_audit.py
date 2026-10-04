"""Audit the approved unbalanced dynamic event-time structure.

The researcher approved keeping every observed post-treatment month, reporting
composition at each relative month, comparing four post-treatment time bins,
and retaining constant-step and common 6/12/24-month windows as sensitivities.
This script audits support only. It does not choose an estimator, a lead window,
a comparability screen, a successive-entry treatment rule or a final sample.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_dynamic_event_time.json"
UNIVERSE_PATH = ROOT / "reports" / "accessibility_cohort_comparison_universe.csv"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
COHORT_MONTH_PATH = (
    ROOT / "reports" / "accessibility_dynamic_event_time_support_by_cohort_month.csv"
)
EVENT_MONTH_PATH = (
    ROOT / "reports" / "accessibility_dynamic_event_time_support_by_event_month.csv"
)
SUMMARY_PATH = ROOT / "reports" / "accessibility_dynamic_event_time_summary.json"
REPORT_PATH = ROOT / "reports" / "76_DYNAMIQUE_TEMPORELLE_NON_EQUILIBREE_FR.md"
SOURCE_ID = "DERIVED_ACCESSIBILITY_DYNAMIC_EVENT_TIME_SUPPORT"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def event_month(date: pd.Series, anchor: pd.Series) -> pd.Series:
    return (
        (date.dt.year - anchor.dt.year) * 12 + (date.dt.month - anchor.dt.month)
    ).astype(int)


def post_bin(values: pd.Series, config: dict) -> pd.Series:
    labels: list[str] = []
    conditions: list[pd.Series] = []
    for item in config["post_effect_bins"]:
        condition = values.ge(int(item["start_inclusive"]))
        if item["end_inclusive"] is not None:
            condition &= values.le(int(item["end_inclusive"]))
        conditions.append(condition)
        labels.append(str(item["label"]))
    return pd.Series(
        np.select(conditions, labels, default="pre_treatment"), index=values.index
    )


def build_month_frame(
    config: dict, universe: pd.DataFrame, panel: pd.DataFrame
) -> pd.DataFrame:
    universe = universe.copy()
    panel = panel.copy()
    universe["focal_cohort_month"] = pd.to_datetime(
        universe["focal_cohort_month"], errors="raise"
    )
    universe["municipality_first_exposure_month_120min"] = pd.to_datetime(
        universe["municipality_first_exposure_month_120min"], errors="coerce"
    )
    for column in [
        "treated_in_focal_cohort",
        "primary_donor_candidate_at_anchor",
        "sensitivity_never_exposed_donor_candidate",
    ]:
        universe[column] = bool_series(universe[column])
    panel["date"] = pd.to_datetime(panel["date"], errors="raise")
    if panel.duplicated(["municipality_bfs_id", "date"]).any():
        raise ValueError("Outcome panel has duplicate municipality-month keys")
    if universe.duplicated(["focal_cohort_month", "municipality_bfs_id"]).any():
        raise ValueError("Comparison universe has duplicate municipality-cohort keys")
    latest_observed = panel.loc[panel.hotel_overnights.notna(), "date"].max()
    panel = panel.loc[panel.date.le(latest_observed)].copy()
    keep = [
        "municipality_bfs_id",
        "date",
        "hotel_overnights",
        "new_station_group_entry_count_120min",
        "active_station_group_count_120min",
    ]
    frame = universe.merge(
        panel[keep], on="municipality_bfs_id", how="left", validate="many_to_many"
    )
    if frame["date"].isna().any():
        missing_ids = sorted(
            frame.loc[frame.date.isna(), "municipality_bfs_id"].unique().tolist()
        )
        raise ValueError(f"Municipalities absent from outcome panel: {missing_ids}")
    frame["event_month"] = event_month(
        frame["date"], frame["focal_cohort_month"]
    )
    frame["event_period"] = np.where(
        frame.event_month.lt(0), "pre_treatment", "post_treatment"
    )
    frame["post_effect_bin"] = post_bin(frame.event_month, config)
    frame["outcome_observed"] = frame.hotel_overnights.notna()
    never = frame.primary_comparison_role.eq("donor_never_exposed")
    not_yet = frame.primary_comparison_role.eq("donor_not_yet_exposed")
    frame["primary_donor_month_eligible"] = (
        frame.primary_donor_candidate_at_anchor
        & (
            never
            | (
                not_yet
                & frame.date.lt(frame.municipality_first_exposure_month_120min)
            )
        )
    )
    frame["sensitivity_donor_month_eligible"] = (
        frame.sensitivity_never_exposed_donor_candidate
    )
    frame["treated_outcome_observed"] = (
        frame.treated_in_focal_cohort & frame.outcome_observed
    )
    frame["primary_donor_outcome_observed"] = (
        frame.primary_donor_month_eligible & frame.outcome_observed
    )
    frame["sensitivity_donor_outcome_observed"] = (
        frame.sensitivity_donor_month_eligible & frame.outcome_observed
    )
    frame["treated_additional_entry_this_month"] = (
        frame.treated_in_focal_cohort
        & frame.date.gt(frame.focal_cohort_month)
        & frame.new_station_group_entry_count_120min.fillna(0).gt(0)
    )
    frame = frame.sort_values(
        ["focal_cohort_month", "municipality_bfs_id", "date"], kind="stable"
    ).reset_index(drop=True)
    frame["treated_additional_entry_reached"] = frame.groupby(
        ["focal_cohort_month", "municipality_bfs_id"], sort=False
    ).treated_additional_entry_this_month.cummax()
    frame["treated_observed_after_additional_entry"] = (
        frame.treated_outcome_observed & frame.treated_additional_entry_reached
    )
    covid_start = pd.Timestamp(config["covid_exclusion_sensitivity_start_month"])
    covid_end = pd.Timestamp(config["covid_exclusion_sensitivity_end_month"])
    frame["covid_exclusion_sensitivity_month"] = frame.date.between(
        covid_start, covid_end
    )
    return frame


def build_cohort_month_support(config: dict, frame: pd.DataFrame) -> pd.DataFrame:
    support = (
        frame.groupby(
            [
                "focal_cohort_month",
                "date",
                "event_month",
                "event_period",
                "post_effect_bin",
                "covid_exclusion_sensitivity_month",
            ],
            sort=True,
            observed=True,
        )
        .agg(
            treated_candidate_municipalities=("treated_in_focal_cohort", "sum"),
            treated_observed_outcome_municipalities=(
                "treated_outcome_observed",
                "sum",
            ),
            primary_donor_eligible_municipalities=(
                "primary_donor_month_eligible",
                "sum",
            ),
            primary_donor_observed_outcome_municipalities=(
                "primary_donor_outcome_observed",
                "sum",
            ),
            sensitivity_donor_eligible_municipalities=(
                "sensitivity_donor_month_eligible",
                "sum",
            ),
            sensitivity_donor_observed_outcome_municipalities=(
                "sensitivity_donor_outcome_observed",
                "sum",
            ),
            treated_with_additional_entry_this_month=(
                "treated_additional_entry_this_month",
                "sum",
            ),
            treated_with_additional_entry_reached=(
                "treated_additional_entry_reached",
                "sum",
            ),
            treated_observed_after_additional_entry=(
                "treated_observed_after_additional_entry",
                "sum",
            ),
        )
        .reset_index()
    )
    support = support.rename(columns={"date": "calendar_month"})
    support["treated_missing_outcome_municipalities"] = (
        support.treated_candidate_municipalities
        - support.treated_observed_outcome_municipalities
    )
    support["primary_donor_missing_outcome_municipalities"] = (
        support.primary_donor_eligible_municipalities
        - support.primary_donor_observed_outcome_municipalities
    )
    support["sensitivity_donor_missing_outcome_municipalities"] = (
        support.sensitivity_donor_eligible_municipalities
        - support.sensitivity_donor_observed_outcome_municipalities
    )
    support["primary_comparison_support_available"] = (
        support.treated_observed_outcome_municipalities.gt(0)
        & support.primary_donor_observed_outcome_municipalities.gt(0)
    )
    support["sensitivity_comparison_support_available"] = (
        support.treated_observed_outcome_municipalities.gt(0)
        & support.sensitivity_donor_observed_outcome_municipalities.gt(0)
    )
    support["primary_temporal_design_selected"] = bool(
        config["primary_temporal_design_selected"]
    )
    support["fixed_symmetric_primary_horizon_selected"] = bool(
        config["fixed_symmetric_primary_horizon_selected"]
    )
    support["successive_entry_handling_selected"] = bool(
        config["successive_entry_handling_selected"]
    )
    support["analysis_sample_selected"] = bool(config["analysis_sample_selected"])
    support["estimator_selected"] = bool(config["estimator_selected"])
    support["causal_estimation_approved"] = bool(
        config["causal_estimation_approved"]
    )
    support["source_id"] = SOURCE_ID
    support["focal_cohort_month"] = support.focal_cohort_month.dt.strftime(
        "%Y-%m-%d"
    )
    support["calendar_month"] = support.calendar_month.dt.strftime("%Y-%m-%d")
    return support


def build_event_month_support(
    config: dict, cohort_month: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for event_time, group in cohort_month.groupby("event_month", sort=True):
        active = group.loc[group.treated_observed_outcome_municipalities.gt(0)]
        contributing = group.loc[
            group.treated_observed_outcome_municipalities.gt(0),
            "focal_cohort_month",
        ].tolist()
        rows.append(
            {
                "event_month": int(event_time),
                "event_period": str(group.event_period.iloc[0]),
                "post_effect_bin": str(group.post_effect_bin.iloc[0]),
                "calendar_months_represented": int(group.calendar_month.nunique()),
                "calendar_month_range": (
                    f"{group.calendar_month.min()}|{group.calendar_month.max()}"
                ),
                "treated_cohorts_contributing": int(len(set(contributing))),
                "treated_cohort_months_contributing": "|".join(
                    sorted(set(contributing))
                ),
                "treated_observed_outcome_municipalities": int(
                    group.treated_observed_outcome_municipalities.sum()
                ),
                "primary_donor_municipality_cohort_observations": int(
                    active.primary_donor_observed_outcome_municipalities.sum()
                ),
                "sensitivity_donor_municipality_cohort_observations": int(
                    active.sensitivity_donor_observed_outcome_municipalities.sum()
                ),
                "treated_observed_after_additional_entry": int(
                    group.treated_observed_after_additional_entry.sum()
                ),
                "cohorts_with_primary_comparison_support": int(
                    group.primary_comparison_support_available.sum()
                ),
                "cohorts_with_sensitivity_comparison_support": int(
                    group.sensitivity_comparison_support_available.sum()
                ),
                "primary_temporal_design_selected": True,
                "fixed_symmetric_primary_horizon_selected": False,
                "successive_entry_handling_selected": bool(
                    config["successive_entry_handling_selected"]
                ),
                "analysis_sample_selected": False,
                "estimator_selected": False,
                "causal_estimation_approved": False,
                "source_id": SOURCE_ID,
            }
        )
    return pd.DataFrame(rows)


def common_horizon_summary(config: dict, frame: pd.DataFrame) -> list[dict]:
    treated = frame.loc[frame.treated_in_focal_cohort].copy()
    rows: list[dict[str, object]] = []
    for (cohort, bfs_id), group in treated.groupby(
        ["focal_cohort_month", "municipality_bfs_id"], sort=True
    ):
        observed = set(group.loc[group.outcome_observed, "event_month"].astype(int))
        later = set(
            group.loc[
                group.treated_additional_entry_this_month, "event_month"
            ].astype(int)
        )
        row: dict[str, object] = {
            "focal_cohort_month": cohort,
            "municipality_bfs_id": int(bfs_id),
        }
        for horizon in config["common_support_sensitivity_horizons_months"]:
            horizon = int(horizon)
            pre = set(range(-horizon, 0))
            post = set(range(0, horizon))
            row[f"complete_{horizon}"] = pre.issubset(observed) and post.issubset(
                observed
            )
            row[f"later_entry_in_post_{horizon}"] = bool(later & post)
        rows.append(row)
    units = pd.DataFrame(rows)
    complete_all = units[
        [f"complete_{int(h)}" for h in config["common_support_sensitivity_horizons_months"]]
    ].all(axis=1)
    result: list[dict] = []
    for horizon in config["common_support_sensitivity_horizons_months"]:
        horizon = int(horizon)
        complete = units[f"complete_{horizon}"].astype(bool)
        result.append(
            {
                "horizon_months_each_side": horizon,
                "treated_municipalities_complete": int(complete.sum()),
                "treated_municipalities_complete_at_all_three_horizons": int(
                    complete_all.sum()
                ),
                "treated_cohorts_with_at_least_one_complete_municipality": int(
                    units.loc[complete, "focal_cohort_month"].nunique()
                ),
                "complete_treated_municipalities_with_later_entry_in_post_window": int(
                    (
                        complete
                        & units[f"later_entry_in_post_{horizon}"].astype(bool)
                    ).sum()
                ),
            }
        )
    return result


def post_bin_summary(config: dict, frame: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for item in config["post_effect_bins"]:
        mask = frame.event_month.ge(int(item["start_inclusive"]))
        if item["end_inclusive"] is not None:
            mask &= frame.event_month.le(int(item["end_inclusive"]))
        local = frame.loc[mask]
        contributing_keys = local.loc[
            local.treated_outcome_observed, ["focal_cohort_month", "date"]
        ].drop_duplicates()
        comparison_rows = local.merge(
            contributing_keys, on=["focal_cohort_month", "date"], how="inner",
            validate="many_to_one",
        )
        treated_observed = local.treated_outcome_observed
        after_additional = local.treated_observed_after_additional_entry
        rows.append(
            {
                "post_effect_bin": item["label"],
                "event_month_start": int(item["start_inclusive"]),
                "event_month_end": (
                    int(item["end_inclusive"])
                    if item["end_inclusive"] is not None
                    else None
                ),
                "treated_cohorts_contributing": int(
                    local.loc[
                        treated_observed, "focal_cohort_month"
                    ].nunique()
                ),
                "treated_municipalities_contributing": int(
                    local.loc[
                        treated_observed, "municipality_bfs_id"
                    ].nunique()
                ),
                "treated_observation_rows": int(treated_observed.sum()),
                "primary_donor_municipality_cohort_observations": int(
                    comparison_rows.primary_donor_outcome_observed.sum()
                ),
                "sensitivity_donor_municipality_cohort_observations": int(
                    comparison_rows.sensitivity_donor_outcome_observed.sum()
                ),
                "treated_observation_rows_after_additional_entry": int(
                    after_additional.sum()
                ),
                "share_treated_observations_after_additional_entry": (
                    float(after_additional.sum() / treated_observed.sum())
                    if treated_observed.sum()
                    else None
                ),
            }
        )
    return rows


def build_summary(
    config: dict,
    universe: pd.DataFrame,
    panel: pd.DataFrame,
    frame: pd.DataFrame,
    cohort_month: pd.DataFrame,
    event_support: pd.DataFrame,
) -> dict:
    treated = frame.loc[frame.treated_in_focal_cohort].copy()
    post_observed = treated.event_month.ge(0) & treated.outcome_observed
    treated_units_post = treated.loc[
        post_observed, ["focal_cohort_month", "municipality_bfs_id"]
    ].drop_duplicates()
    before_next_entry = treated.loc[
        post_observed & ~treated.treated_additional_entry_reached
    ]
    later_by_unit = treated.groupby(
        ["focal_cohort_month", "municipality_bfs_id"]
    ).treated_additional_entry_this_month.any()
    pre_units = treated.loc[
        treated.event_month.lt(0) & treated.outcome_observed,
        "municipality_bfs_id",
    ].unique()
    without_pre = universe.loc[
        bool_series(universe.treated_in_focal_cohort)
        & ~universe.municipality_bfs_id.isin(pre_units),
        ["municipality_bfs_id", "municipality_name", "focal_cohort_month"],
    ].to_dict(orient="records")
    cohort_post = []
    for cohort, group in cohort_month.groupby("focal_cohort_month", sort=True):
        post = group.loc[
            group.event_month.ge(0)
            & group.treated_observed_outcome_municipalities.gt(0)
        ]
        cohort_post.append(
            {
                "focal_cohort_month": cohort,
                "treated_municipalities": int(
                    group.treated_candidate_municipalities.max()
                ),
                "last_event_month_with_treated_outcome": int(post.event_month.max()),
                "calendar_months_with_treated_outcome": int(len(post)),
            }
        )
    observed_panel = panel.loc[panel.hotel_overnights.notna()].copy()
    observed_panel["date"] = pd.to_datetime(observed_panel["date"], errors="raise")
    supported_post = event_support.loc[
        event_support.event_month.ge(0)
        & event_support.treated_observed_outcome_municipalities.gt(0)
        & event_support.cohorts_with_primary_comparison_support.gt(0)
    ]
    return {
        "specification_version": config["specification_version"],
        "primary_temporal_design": config["primary_temporal_design"],
        "primary_temporal_design_selected": True,
        "fixed_symmetric_primary_horizon_selected": False,
        "observed_outcome_calendar_start": observed_panel.date.min().strftime(
            "%Y-%m-%d"
        ),
        "observed_outcome_calendar_end": observed_panel.date.max().strftime(
            "%Y-%m-%d"
        ),
        "calendar_months_with_any_observed_outcome": int(
            observed_panel.date.nunique()
        ),
        "treated_municipalities": int(
            universe.loc[
                bool_series(universe.treated_in_focal_cohort), "municipality_bfs_id"
            ].nunique()
        ),
        "treated_municipalities_with_at_least_one_observed_post_month": int(
            len(treated_units_post)
        ),
        "first_exposure_cohorts": int(universe.focal_cohort_month.nunique()),
        "treated_municipalities_with_observed_pre_and_post_support": int(len(pre_units)),
        "treated_municipalities_without_observed_pre_support": without_pre,
        "supported_post_event_month_start": int(supported_post.event_month.min()),
        "supported_post_event_month_end": int(supported_post.event_month.max()),
        "cohort_post_support": cohort_post,
        "post_effect_bin_support": post_bin_summary(config, frame),
        "constant_step_sensitivity_support": {
            "treated_municipalities_contributing": int(
                treated_units_post.municipality_bfs_id.nunique()
            ),
            "treated_cohorts_contributing": int(
                treated_units_post.focal_cohort_month.nunique()
            ),
            "treated_observation_rows": int(post_observed.sum()),
        },
        "common_support_sensitivities": common_horizon_summary(config, frame),
        "treated_municipalities_with_any_later_accessible_entry": int(
            later_by_unit.sum()
        ),
        "treated_post_observation_rows_after_later_accessible_entry": int(
            treated.loc[post_observed, "treated_additional_entry_reached"].sum()
        ),
        "next_entry_censoring_counterfactual_support_only": {
            "observed_post_rows_before_next_entry": int(len(before_next_entry)),
            "municipalities_with_any_observed_post_row_before_next_entry": int(
                before_next_entry.municipality_bfs_id.nunique()
            ),
            "rule_applied_to_analytical_sample": False,
        },
        "successive_entry_handling_selected": False,
        "linear_counterfactual_status": config["linear_counterfactual_status"],
        "comparability_screen_selected": False,
        "analysis_sample_selected": False,
        "estimator_selected": False,
        "causal_estimation_approved": False,
        "input_sha256": {
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            UNIVERSE_PATH.relative_to(ROOT).as_posix(): sha256(UNIVERSE_PATH),
            PANEL_PATH.relative_to(ROOT).as_posix(): sha256(PANEL_PATH),
        },
        "source_id": SOURCE_ID,
    }


def write_report(summary: dict) -> None:
    lines = [
        "# Dynamique temporelle non équilibrée - étape 28b",
        "",
        "**Statut : règle temporelle validée et support audité. Aucun effet n'est encore estimé.**",
        "",
        "## Règle appliquée",
        "",
        "- L'analyse principale pourra utiliser tous les mois postérieurs observés pour chaque commune, même si leur nombre diffère entre cohortes.",
        "- Les effets seront distingués par mois relatif à l'entrée. La composition des cohortes et des témoins est donc publiée pour chaque mois relatif.",
        "- Les périodes 0-5, 6-11, 12-23 et 24 mois ou plus serviront à vérifier une éventuelle atténuation, sans imposer une forme décroissante.",
        "- Un saut postérieur permanent et les fenêtres communes 6/12/24 mois restent des sensibilités.",
        "- Les mois prétraitement sont inventoriés. La période utilisée pour tester les tendances avant entrée et le mois de référence restent à définir avec l'estimateur.",
        "",
        "## Support obtenu",
        "",
        f"Les nuitées observées couvrent {summary['calendar_months_with_any_observed_outcome']} mois, de {summary['observed_outcome_calendar_start']} à {summary['observed_outcome_calendar_end']}. Les {summary['treated_municipalities_with_at_least_one_observed_post_month']} communes traitées sur {summary['treated_municipalities']} ont au moins un mois postérieur observé. Avec au moins une cohorte traitée et ses témoins principaux, le support va du mois relatif {summary['supported_post_event_month_start']} au mois {summary['supported_post_event_month_end']}.",
        "",
        "| Cohorte | Communes traitées | Dernier mois relatif observé | Mois postérieurs avec au moins une issue observée |",
        "|---|---:|---:|---:|",
    ]
    for row in summary["cohort_post_support"]:
        lines.append(
            f"| {row['focal_cohort_month']} | {row['treated_municipalities']} | "
            f"{row['last_event_month_with_treated_outcome']} | "
            f"{row['calendar_months_with_treated_outcome']} |"
        )
    lines.extend(
        [
            "",
            "## Composition des quatre périodes postérieures",
            "",
            "| Période relative | Cohortes contributrices | Communes contributrices | Observations commune-mois traitées | Part après une entrée accessible supplémentaire |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in summary["post_effect_bin_support"]:
        period_label = {
            "0_5_months": "0-5 mois", "6_11_months": "6-11 mois",
            "12_23_months": "12-23 mois", "24_plus_months": "24 mois ou plus",
        }[row["post_effect_bin"]]
        share = row["share_treated_observations_after_additional_entry"]
        share_text = "NA" if share is None else f"{100 * share:.1f} %"
        lines.append(
            f"| {period_label} | {row['treated_cohorts_contributing']} | "
            f"{row['treated_municipalities_contributing']} | "
            f"{row['treated_observation_rows']} | {share_text} |"
        )
    lines.extend(
        [
            "",
            "## Couverture des fenêtres de sensibilité",
            "",
            "| Fenêtre avant + après | Communes traitées complètes | Cohortes représentées | Dont entrée supplémentaire dans la fenêtre postérieure |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in summary["common_support_sensitivities"]:
        horizon = row["horizon_months_each_side"]
        lines.append(
            f"| {horizon}+{horizon} mois | "
            f"{row['treated_municipalities_complete']} | "
            f"{row['treated_cohorts_with_at_least_one_complete_municipality']} | "
            f"{row['complete_treated_municipalities_with_later_entry_in_post_window']} |"
        )
    lines.extend(
        [
            "",
            "Les trois fenêtres peuvent être comparées sur les mêmes 65 communes disposant de toutes les observations requises à 24+24 mois. Les effectifs 76/73/65 ci-dessus décrivent leur couverture respective, pas une composition identique. Aucune estimation ni sélection définitive n'est effectuée ici.",
            "",
            "## Limites avant estimation",
            "",
            f"{summary['treated_municipalities_with_observed_pre_and_post_support']} communes disposent d'au moins une nuitée observée avant et après. Les quatre autres restent dans l'inventaire mais leur historique de résultat avant exposition manque sous l'identifiant courant : Blonay - Saint-Légier, Val de Bagnes, Laténa et Moutier (JU). La reconstruction déjà effectuée pour la part étrangère de Moutier n'a pas encore été appliquée au panel de résultats. Avoir un mois postérieur ne suffit donc pas à rendre les 80 communes estimables.",
            "",
            f"{summary['treated_municipalities_with_any_later_accessible_entry']} communes traitées connaissent au moins une entrée accessible supplémentaire. Ces observations restent visibles mais ne sont ni censurées ni attribuées à une station : leur traitement méthodologique doit être validé séparément.",
            "",
            "Une tendance contrefactuelle linéaire reste une hypothèse à diagnostiquer. Le présent audit ne valide ni tendances parallèles, ni forme linéaire, ni saut permanent. Aucun filtre de comparabilité, échantillon final ou estimateur n'est choisi.",
            "",
            "## Prochaine décision : les entrées successives",
            "",
            f"Trois possibilités restent à choisir. Garder la trajectoire du réseau après la première exposition conserve les {summary['constant_step_sensitivity_support']['treated_observation_rows']} observations postérieures et décrit une exposition qui peut ensuite s'élargir. Arrêter le suivi dès la prochaine entrée accessible laisserait {summary['next_entry_censoring_counterfactual_support_only']['observed_post_rows_before_next_entry']} observations et {summary['next_entry_censoring_counterfactual_support_only']['municipalities_with_any_observed_post_row_before_next_entry']} communes avec au moins une observation postérieure ; cette comparaison d'effectifs est calculée sans appliquer la règle. Enfin, modéliser les ajouts séparément exigerait d'auditer leurs dates, leurs bassins et leur variation indépendante ; des entrées simultanées ne garantissent pas des effets distincts. Aucun de ces choix n'est appliqué ici.",
            "",
            "## Fichiers de contrôle",
            "",
            "- Support par cohorte et mois relatif : `reports/accessibility_dynamic_event_time_support_by_cohort_month.csv`.",
            "- Support agrégé par mois relatif : `reports/accessibility_dynamic_event_time_support_by_event_month.csv`.",
            "- Spécification approuvée : `config/accessibility_dynamic_event_time.json`.",
            "- Sources internes : `reports/accessibility_cohort_comparison_universe.csv` pour les rôles et dates d'exposition ; `data_processed/accessibility_municipality_month_exposure.csv` pour les nuitées HESTA et entrées accessibles. Leurs empreintes SHA-256 figurent dans le résumé JSON. Aucun téléchargement supplémentaire.",
            "",
            "Les témoins agrégés sont comptés seulement pour les cohortes-mois ayant au moins une issue traitée observée. Une commune témoin réutilisée dans plusieurs cohortes produit plusieurs observations commune-cohorte, sans devenir plusieurs communes indépendantes. Les tableaux décrivent la disponibilité mensuelle ; ils ne fixent aucune pondération d'estimation.",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not config["primary_temporal_design_selected"]:
        raise ValueError("The approved dynamic temporal design must be selected")
    if config["fixed_symmetric_primary_horizon_selected"]:
        raise ValueError("The primary design cannot impose a fixed symmetric horizon")
    universe = pd.read_csv(UNIVERSE_PATH, dtype={"municipality_bfs_id": int})
    panel = pd.read_csv(PANEL_PATH, dtype={"municipality_bfs_id": int})
    if set(universe.municipality_bfs_id) != set(panel.municipality_bfs_id):
        raise ValueError("Cohort universe and outcome panel municipality IDs differ")
    frame = build_month_frame(config, universe, panel)
    cohort_month = build_cohort_month_support(config, frame)
    event_support = build_event_month_support(config, cohort_month)
    summary = build_summary(
        config, universe, panel, frame, cohort_month, event_support
    )

    expected_horizons = {6: 76, 12: 73, 24: 65}
    actual_horizons = {
        row["horizon_months_each_side"]: row["treated_municipalities_complete"]
        for row in summary["common_support_sensitivities"]
    }
    if actual_horizons != expected_horizons:
        raise ValueError(
            f"Common-horizon support no longer reconciles to stage 26: {actual_horizons}"
        )
    if summary["treated_municipalities_with_at_least_one_observed_post_month"] != 80:
        raise ValueError("All 80 treated municipalities must retain observed post support")
    if summary["treated_municipalities_with_any_later_accessible_entry"] != 46:
        raise ValueError("Expected 46 treated municipalities with later accessible entries")
    if cohort_month.analysis_sample_selected.any() or event_support.estimator_selected.any():
        raise ValueError("Support audit cannot select a sample or estimator")
    if cohort_month.causal_estimation_approved.any():
        raise ValueError("Support audit cannot approve causal estimation")

    cohort_month.to_csv(COHORT_MONTH_PATH, index=False, lineterminator="\n")
    event_support.to_csv(EVENT_MONTH_PATH, index=False, lineterminator="\n")
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
