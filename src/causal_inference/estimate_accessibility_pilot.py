"""Run a predeclared, explicitly non-causal pilot on screened municipality pairs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_pilot_estimation.json"
CANDIDATE_PATH = ROOT / "reports" / "accessibility_estimation_candidate_pairs.csv"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
HISTORICAL_STRICT_PATH = ROOT / "reports" / "accessibility_historical_gtfs_2018_municipality_validation.csv"
HISTORICAL_PROXIMITY_PATH = ROOT / "reports" / "accessibility_historical_gtfs_2018_proximity_municipality_validation.csv"

STACK_OUTPUT = ROOT / "data_processed" / "accessibility_pilot_stacked_panel.csv"
ESTIMATE_OUTPUT = ROOT / "reports" / "accessibility_pilot_did_estimates.csv"
EVENT_OUTPUT = ROOT / "reports" / "accessibility_pilot_event_study.csv"
INFLUENCE_OUTPUT = ROOT / "reports" / "accessibility_pilot_influence_sensitivity.csv"
DECOMPOSITION_OUTPUT = ROOT / "reports" / "accessibility_pilot_treated_decomposition.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_pilot_estimation_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "71_ESTIMATION_PILOTE_NON_CAUSALE_FR.md"

EXPECTED_PRIMARY_PAIRS = 11
EXPECTED_RELAXED_PAIRS = 15
Z_975 = NormalDist().inv_cdf(0.975)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pipe(values: list[str]) -> str:
    return "|".join(str(value) for value in values)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def candidate_pairs(candidates: pd.DataFrame, tier: str) -> pd.DataFrame:
    if tier == "primary":
        return candidates[candidates.estimation_candidate_tier.eq("primary")].copy()
    if tier == "relaxed":
        return candidates.copy()
    raise ValueError(f"Unknown candidate tier: {tier}")


def build_stack(
    pairs: pd.DataFrame,
    panel: pd.DataFrame,
    event_start: int,
    event_end: int,
    tier_label: str,
) -> pd.DataFrame:
    rows: list[dict] = []
    for treated_id, group in pairs.groupby("treated_municipality_bfs_id", sort=True):
        treated_id = int(treated_id)
        treated_name = str(group.treated_municipality_name.iloc[0])
        anchor = pd.Timestamp(group.first_exposure_month.iloc[0])
        controls = (
            group[["control_municipality_bfs_id", "control_municipality_name"]]
            .drop_duplicates()
            .sort_values("control_municipality_bfs_id", kind="stable")
        )
        if controls.empty:
            continue
        units = [(treated_id, treated_name, True, 1.0)] + [
            (
                int(control.control_municipality_bfs_id),
                str(control.control_municipality_name),
                False,
                1.0 / len(controls),
            )
            for control in controls.itertuples(index=False)
        ]
        for municipality_id, municipality_name, is_treated, weight in units:
            local = panel[panel.municipality_bfs_id.eq(municipality_id)].copy()
            local["event_month"] = (
                (local.date.dt.year - anchor.year) * 12
                + local.date.dt.month - anchor.month
            )
            local = local[local.event_month.between(event_start, event_end)].sort_values("date")
            local = local.dropna(subset=["log_overnights"])
            expected_months = event_end - event_start + 1
            if len(local) != expected_months or local.event_month.nunique() != expected_months:
                raise ValueError(
                    f"Incomplete pilot window for stack {treated_id}, municipality {municipality_id}"
                )
            for observation in local.itertuples(index=False):
                rows.append({
                    "analysis_tier": tier_label,
                    "stack_treated_municipality_bfs_id": treated_id,
                    "stack_treated_municipality_name": treated_name,
                    "municipality_bfs_id": municipality_id,
                    "municipality_name": municipality_name,
                    "is_treated_municipality": is_treated,
                    "control_count_in_stack": int(len(controls)),
                    "stack_control_bfs_ids": pipe(
                        controls.control_municipality_bfs_id.astype(int).tolist()
                    ),
                    "first_exposure_month": anchor.date().isoformat(),
                    "date": observation.date.date().isoformat(),
                    "event_month": int(observation.event_month),
                    "post_exposure": int(observation.event_month >= 0),
                    "treated_post": int(is_treated and observation.event_month >= 0),
                    "log_overnights": float(observation.log_overnights),
                    "stack_unit_weight": float(weight),
                    "stack_unit_id": f"{treated_id}:{municipality_id}",
                    "stack_date_id": f"{treated_id}:{observation.date.date().isoformat()}",
                    "source_id": "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION",
                })
    stack = pd.DataFrame(rows)
    if stack.empty:
        raise ValueError("Pilot stack is empty")
    return stack.sort_values(
        ["stack_treated_municipality_bfs_id", "municipality_bfs_id", "date"],
        kind="stable",
    )


def residualise_two_way_by_stack(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    """Weighted two-way demeaning for a balanced stack with unit-constant weights."""
    results = np.zeros((len(frame), len(columns)), dtype=float)
    for _, indices in frame.groupby("stack_treated_municipality_bfs_id", sort=False).groups.items():
        local = frame.loc[indices]
        weights = local.stack_unit_weight.to_numpy(float)
        for position, column in enumerate(columns):
            values = local[column].to_numpy(float)
            unit_mean = pd.Series(values, index=local.index).groupby(
                local.stack_unit_id
            ).transform("mean").to_numpy(float)
            date_mean = (
                pd.DataFrame({"value": values, "weight": weights, "date": local.stack_date_id.to_numpy()})
                .groupby("date", sort=False)
                .apply(lambda part: np.average(part.value, weights=part.weight), include_groups=False)
            )
            date_values = local.stack_date_id.map(date_mean).to_numpy(float)
            stack_mean = float(np.average(values, weights=weights))
            results[frame.index.get_indexer(local.index), position] = (
                values - unit_mean - date_values + stack_mean
            )
    return results


def fit_effects(frame: pd.DataFrame, effect_columns: list[str]) -> pd.DataFrame:
    if frame.index.tolist() != list(range(len(frame))):
        frame = frame.reset_index(drop=True)
    residualised = residualise_two_way_by_stack(
        frame, ["log_overnights", *effect_columns]
    )
    y = residualised[:, 0]
    x = residualised[:, 1:]
    weights = frame.stack_unit_weight.to_numpy(float)
    sqrt_weights = np.sqrt(weights)
    yw = y * sqrt_weights
    xw = x * sqrt_weights[:, None]
    beta, _, rank, _ = np.linalg.lstsq(xw, yw, rcond=None)
    if rank != len(effect_columns):
        raise ValueError("Pilot effect design is rank deficient")
    residuals = yw - xw @ beta
    bread = np.linalg.pinv(xw.T @ xw)
    meat = np.zeros((len(effect_columns), len(effect_columns)), dtype=float)
    clusters = frame.municipality_bfs_id.astype(int)
    cluster_count = int(clusters.nunique())
    for _, positions in clusters.groupby(clusters).groups.items():
        locations = frame.index.get_indexer(positions)
        score = xw[locations].T @ residuals[locations]
        meat += np.outer(score, score)
    covariance = bread @ meat @ bread
    if cluster_count > 1:
        covariance *= cluster_count / (cluster_count - 1)
    standard_errors = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    rows = []
    for index, column in enumerate(effect_columns):
        lower = float(beta[index] - Z_975 * standard_errors[index])
        upper = float(beta[index] + Z_975 * standard_errors[index])
        rows.append({
            "effect_term": column,
            "estimate_log_points": float(beta[index]),
            "cluster_robust_standard_error": float(standard_errors[index]),
            "ci95_normal_lower_log_points": lower,
            "ci95_normal_upper_log_points": upper,
            "estimate_percent_change": float(np.expm1(beta[index])),
            "ci95_normal_lower_percent_change": float(np.expm1(lower)),
            "ci95_normal_upper_percent_change": float(np.expm1(upper)),
            "municipality_cluster_count": cluster_count,
            "stack_count": int(frame.stack_treated_municipality_bfs_id.nunique()),
            "unique_municipality_count": int(frame.municipality_bfs_id.nunique()),
            "observation_count": int(len(frame)),
        })
    return pd.DataFrame(rows)


def static_estimate(stack: pd.DataFrame, scenario_id: str, candidate_tier: str) -> dict:
    result = fit_effects(stack.reset_index(drop=True), ["treated_post"]).iloc[0].to_dict()
    return {
        "scenario_id": scenario_id,
        "candidate_tier": candidate_tier,
        "event_window_start": int(stack.event_month.min()),
        "event_window_end": int(stack.event_month.max()),
        "pair_count": int(
            stack[["stack_treated_municipality_bfs_id", "municipality_bfs_id"]]
            .drop_duplicates()
            .loc[lambda data: data.municipality_bfs_id.ne(data.stack_treated_municipality_bfs_id)]
            .shape[0]
        ),
        **result,
        "causal_estimation_approved": False,
        "interpretation": "non_causal_pilot_estimate",
        "source_id": "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION",
    }


def add_event_bins(stack: pd.DataFrame, bins: list[dict]) -> tuple[pd.DataFrame, list[str]]:
    frame = stack.copy()
    columns = []
    for item in bins:
        column = f"event_bin_{item['label']}"
        frame[column] = (
            frame.is_treated_municipality.astype(bool)
            & frame.event_month.between(int(item["start"]), int(item["end"]))
        ).astype(int)
        columns.append(column)
    return frame, columns


def event_study(stack: pd.DataFrame, bins: list[dict], tier: str) -> pd.DataFrame:
    frame, columns = add_event_bins(stack, bins)
    result = fit_effects(frame.reset_index(drop=True), columns)
    lookup = {f"event_bin_{item['label']}": item for item in bins}
    result["candidate_tier"] = tier
    result["event_bin"] = result.effect_term.map(lambda value: lookup[value]["label"])
    result["event_month_start"] = result.effect_term.map(lambda value: lookup[value]["start"])
    result["event_month_end"] = result.effect_term.map(lambda value: lookup[value]["end"])
    result["reference_event_month"] = -1
    result["causal_effect_approved"] = False
    result["interpretation"] = "non_causal_binned_event_study_pilot"
    result["source_id"] = "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION"
    return result


def influence_sensitivities(
    primary_pairs: pd.DataFrame, panel: pd.DataFrame, config: dict
) -> pd.DataFrame:
    window = config["event_window"]
    rows = []
    treated_records = (
        primary_pairs[["treated_municipality_bfs_id", "treated_municipality_name"]]
        .drop_duplicates()
        .sort_values("treated_municipality_bfs_id")
    )
    for treated in treated_records.itertuples(index=False):
        subset = primary_pairs[
            ~primary_pairs.treated_municipality_bfs_id.eq(treated.treated_municipality_bfs_id)
        ]
        stack = build_stack(
            subset, panel, int(window["start_month"]), int(window["end_month"]), "primary"
        )
        estimate = static_estimate(
            stack, f"leave_treated_out_{int(treated.treated_municipality_bfs_id)}", "primary"
        )
        rows.append({
            "diagnostic_type": "leave_one_treated_municipality_out",
            "omitted_bfs_ids": str(int(treated.treated_municipality_bfs_id)),
            "omitted_names": treated.treated_municipality_name,
            **estimate,
        })
    for pair in primary_pairs.sort_values(
        ["treated_municipality_bfs_id", "control_municipality_bfs_id"]
    ).itertuples(index=False):
        mask = (
            primary_pairs.treated_municipality_bfs_id.eq(pair.treated_municipality_bfs_id)
            & primary_pairs.control_municipality_bfs_id.eq(pair.control_municipality_bfs_id)
        )
        subset = primary_pairs[~mask]
        stack = build_stack(
            subset, panel, int(window["start_month"]), int(window["end_month"]), "primary"
        )
        estimate = static_estimate(
            stack,
            f"leave_pair_out_{int(pair.treated_municipality_bfs_id)}_{int(pair.control_municipality_bfs_id)}",
            "primary",
        )
        rows.append({
            "diagnostic_type": "leave_one_pair_out",
            "omitted_bfs_ids": (
                f"{int(pair.treated_municipality_bfs_id)}:{int(pair.control_municipality_bfs_id)}"
            ),
            "omitted_names": (
                f"{pair.treated_municipality_name} - {pair.control_municipality_name}"
            ),
            **estimate,
        })
    return pd.DataFrame(rows)


def treated_decomposition(primary_stack: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for treated_id, group in primary_stack.groupby(
        "stack_treated_municipality_bfs_id", sort=True
    ):
        treated = group[group.is_treated_municipality.astype(bool)].set_index(
            "event_month"
        ).log_overnights
        controls = group[~group.is_treated_municipality.astype(bool)].copy()
        controls["weighted_log_overnights"] = (
            controls.log_overnights * controls.stack_unit_weight
        )
        control_mean = controls.groupby("event_month").weighted_log_overnights.sum()
        gap = treated - control_mean
        full_change = float(gap[gap.index >= 0].mean() - gap[gap.index < 0].mean())
        truncated_change = float(
            gap[(gap.index >= 0) & (gap.index <= 13)].mean()
            - gap[gap.index < 0].mean()
        )
        control_names = (
            controls[["municipality_bfs_id", "municipality_name"]]
            .drop_duplicates()
            .sort_values("municipality_bfs_id", kind="stable")
        )
        rows.append({
            "treated_municipality_bfs_id": int(treated_id),
            "treated_municipality_name": group.stack_treated_municipality_name.iloc[0],
            "control_count": int(len(control_names)),
            "control_municipality_bfs_ids": pipe(
                control_names.municipality_bfs_id.astype(int).tolist()
            ),
            "control_municipality_names": pipe(control_names.municipality_name.tolist()),
            "pre_mean_treated_minus_weighted_control_log_gap": float(
                gap[gap.index < 0].mean()
            ),
            "post_mean_treated_minus_weighted_control_log_gap": float(
                gap[gap.index >= 0].mean()
            ),
            "post_minus_pre_log_gap": full_change,
            "post_minus_pre_percent_change": float(np.expm1(full_change)),
            "truncated_post_minus_pre_log_gap": truncated_change,
            "truncated_post_minus_pre_percent_change": float(np.expm1(truncated_change)),
            "causal_effect_approved": False,
            "interpretation": "treated_stack_descriptive_decomposition",
            "source_id": "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION",
        })
    return pd.DataFrame(rows)


def build_summary(
    estimates: pd.DataFrame,
    events: pd.DataFrame,
    influence: pd.DataFrame,
    decomposition: pd.DataFrame,
    strict_historical_retained: int,
    proximity_historical_retained: int,
    config: dict,
) -> dict:
    primary = estimates[estimates.scenario_id.eq("primary_full_24m_post")].iloc[0]
    truncated = estimates[estimates.scenario_id.eq("primary_post_truncated_at_month_13")].iloc[0]
    relaxed = estimates[estimates.scenario_id.eq("relaxed_full_24m_post")].iloc[0]
    pair_loo = influence[influence.diagnostic_type.eq("leave_one_pair_out")]
    treated_loo = influence[influence.diagnostic_type.eq("leave_one_treated_municipality_out")]
    primary_events = events[events.candidate_tier.eq("primary")]
    pre_events = primary_events[primary_events.event_month_end.lt(0)]
    post_events = primary_events[primary_events.event_month_start.ge(0)]
    return {
        "specification_version": config["specification_version"],
        "primary_pair_count": EXPECTED_PRIMARY_PAIRS,
        "relaxed_pair_count": EXPECTED_RELAXED_PAIRS,
        "primary_treated_municipalities": int(primary.stack_count),
        "primary_unique_municipalities": int(primary.unique_municipality_count),
        "primary_municipality_clusters": int(primary.municipality_cluster_count),
        "primary_treated_retained_under_strict_published_2018_transfers": int(
            strict_historical_retained
        ),
        "primary_treated_retained_under_250m_proximity_transfer_sensitivity": int(
            proximity_historical_retained
        ),
        "primary_estimate_log_points": float(primary.estimate_log_points),
        "primary_estimate_percent_change": float(primary.estimate_percent_change),
        "primary_ci95_percent_change": [
            float(primary.ci95_normal_lower_percent_change),
            float(primary.ci95_normal_upper_percent_change),
        ],
        "truncated_post_estimate_percent_change": float(truncated.estimate_percent_change),
        "relaxed_estimate_percent_change": float(relaxed.estimate_percent_change),
        "leave_one_pair_out_percent_change_range": [
            float(pair_loo.estimate_percent_change.min()),
            float(pair_loo.estimate_percent_change.max()),
        ],
        "leave_one_treated_out_percent_change_range": [
            float(treated_loo.estimate_percent_change.min()),
            float(treated_loo.estimate_percent_change.max()),
        ],
        "treated_stack_percent_change_range": [
            float(decomposition.post_minus_pre_percent_change.min()),
            float(decomposition.post_minus_pre_percent_change.max()),
        ],
        "primary_pre_event_bins_with_ci_excluding_zero": int(
            ((pre_events.ci95_normal_lower_log_points > 0)
             | (pre_events.ci95_normal_upper_log_points < 0)).sum()
        ),
        "primary_post_event_bins_with_ci_excluding_zero": int(
            ((post_events.ci95_normal_lower_log_points > 0)
             | (post_events.ci95_normal_upper_log_points < 0)).sum()
        ),
        "causal_estimation_approved": False,
        "causal_effect_claim_allowed": False,
        "input_sha256": {
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            CANDIDATE_PATH.relative_to(ROOT).as_posix(): sha256(CANDIDATE_PATH),
            PANEL_PATH.relative_to(ROOT).as_posix(): sha256(PANEL_PATH),
            HISTORICAL_STRICT_PATH.relative_to(ROOT).as_posix(): sha256(HISTORICAL_STRICT_PATH),
            HISTORICAL_PROXIMITY_PATH.relative_to(ROOT).as_posix(): sha256(HISTORICAL_PROXIMITY_PATH),
        },
        "source_id": "DERIVED_ACCESSIBILITY_NONCAUSAL_PILOT_ESTIMATION",
        "interpretation": (
            "Non-causal pilot only. Small cluster count, projected historical transfer topology, "
            "broad visitor substitution and residual selection prevent causal interpretation."
        ),
    }


def write_report(
    estimates: pd.DataFrame,
    events: pd.DataFrame,
    decomposition: pd.DataFrame,
    summary: dict,
) -> None:
    primary = estimates[estimates.scenario_id.eq("primary_full_24m_post")].iloc[0]
    truncated = estimates[estimates.scenario_id.eq("primary_post_truncated_at_month_13")].iloc[0]
    relaxed = estimates[estimates.scenario_id.eq("relaxed_full_24m_post")].iloc[0]
    conservative = estimates[
        estimates.scenario_id.eq("primary_excluding_targeted_sensitivity_controls")
    ].iloc[0]
    lines = [
        "# Estimation pilote non causale - étape 24",
        "",
        "**Statut : test quantitatif exploratoire; aucune estimation causale approuvée.**",
        "",
        "## Modèle préenregistré",
        "",
        "Chaque commune traitée forme un ensemble avec ses témoins retenus. La commune traitée reçoit un "
        "poids de 1 et les témoins se partagent ensemble un poids de 1, ce qui évite de favoriser Bulle parce "
        "qu'elle possède davantage de témoins. Le modèle retire les effets fixes commune × ensemble et mois × "
        "ensemble. L'incertitude est regroupée par commune BFS, y compris lorsqu'un témoin est réutilisé.",
        "",
        "La fenêtre principale contient 24 mois avant et 24 mois après novembre 2017. Le coefficient compare "
        "le changement moyen des log-nuitées des communes traitées à celui de leurs témoins. Il est converti "
        "en pourcentage uniquement pour faciliter la lecture.",
        "",
        "## Résultat principal",
        "",
        f"Avec les 11 paires principales et {int(primary.stack_count)} communes traitées, le pilote donne "
        f"**{100 * primary.estimate_percent_change:.1f}%**. L'intervalle normal regroupé à 95% va de "
        f"**{100 * primary.ci95_normal_lower_percent_change:.1f}% à "
        f"{100 * primary.ci95_normal_upper_percent_change:.1f}%**.",
        "",
        "Ce nombre ne doit pas être lu comme l'effet du Magic Pass : le nombre de grappes est faible, "
        "l'accès historique dépend encore d'une sensibilité de transferts et une substitution touristique "
        "large peut subsister.",
        "",
        f"Les {summary['primary_treated_retained_under_250m_proximity_transfer_sensitivity']} communes "
        "traitées sont également retenues sous la sensibilité historique ajoutant des correspondances à 250 m. "
        f"En revanche, {summary['primary_treated_retained_under_strict_published_2018_transfers']} sont retenues "
        "avec la seule table de transferts publiée en 2018, connue pour être fortement sous-connectée. Cette "
        "concordance entre les deux scénarios augmentés améliore la plausibilité, sans rendre les transferts historiques certains.",
        "",
        "## Sensibilités",
        "",
        "| Variante | Paires | Communes traitées | Variation pilote | Intervalle 95% |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in [primary, truncated, relaxed, conservative]:
        lines.append(
            f"| {row.scenario_id} | {int(row.pair_count)} | {int(row.stack_count)} | "
            f"{100 * row.estimate_percent_change:.1f}% | "
            f"[{100 * row.ci95_normal_lower_percent_change:.1f}%; "
            f"{100 * row.ci95_normal_upper_percent_change:.1f}%] |"
        )
    lines += [
        "",
        f"En retirant une paire à la fois, le point estimé varie de "
        f"**{100 * summary['leave_one_pair_out_percent_change_range'][0]:.1f}% à "
        f"{100 * summary['leave_one_pair_out_percent_change_range'][1]:.1f}%**. En retirant une commune "
        f"traitée à la fois, il varie de **{100 * summary['leave_one_treated_out_percent_change_range'][0]:.1f}% "
        f"à {100 * summary['leave_one_treated_out_percent_change_range'][1]:.1f}%**.",
        "",
        "## Décomposition par commune traitée",
        "",
        "Cette décomposition est descriptive et explique l'hétérogénéité derrière la moyenne pondérée.",
        "",
        "| Commune traitée | Témoins | Variation pilote 24 mois | Variation post tronquée |",
        "|---|---|---:|---:|",
    ]
    for row in decomposition.itertuples(index=False):
        lines.append(
            f"| {row.treated_municipality_name} | {str(row.control_municipality_names).replace('|', ', ')} | "
            f"{100 * row.post_minus_pre_percent_change:.1f}% | "
            f"{100 * row.truncated_post_minus_pre_percent_change:.1f}% |"
        )
    lines += [
        "",
        "## Profil temporel",
        "",
        "Les coefficients semestriels sont exprimés relativement au mois -1. Ils servent à repérer une "
        "rupture ou une dérive, pas à dater un mécanisme causal.",
        "",
        "| Fenêtre | Variation pilote | Intervalle 95% |",
        "|---|---:|---:|",
    ]
    for row in events[events.candidate_tier.eq("primary")].itertuples(index=False):
        lines.append(
            f"| {row.event_bin} | {100 * row.estimate_percent_change:.1f}% | "
            f"[{100 * row.ci95_normal_lower_percent_change:.1f}%; "
            f"{100 * row.ci95_normal_upper_percent_change:.1f}%] |"
        )
    lines += [
        "",
        "## Conclusion utilisable",
        "",
        "Le pilote indique la direction et l'instabilité possibles des résultats, mais il ne franchit pas le "
        "seuil de preuve causale. Il peut être présenté comme analyse exploratoire ou test de robustesse. Pour "
        "une affirmation causale, il faudrait notamment une reconstruction historique de l'accessibilité plus "
        "forte, davantage de grappes indépendantes et une stratégie crédible contre la substitution entre régions.",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_pilot_did_estimates.csv` : estimations principale et sensibilités ;",
        "- `reports/accessibility_pilot_event_study.csv` : profil semestriel ;",
        "- `reports/accessibility_pilot_influence_sensitivity.csv` : retraits successifs ;",
        "- `reports/accessibility_pilot_treated_decomposition.csv` : décomposition descriptive par commune traitée ;",
        "- `data_processed/accessibility_pilot_stacked_panel.csv` : panel empilé reproductible ;",
        "- `reports/accessibility_pilot_estimation_summary.json` : résumé et empreintes.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    candidates = pd.read_csv(CANDIDATE_PATH)
    panel = pd.read_csv(PANEL_PATH)
    panel["date"] = pd.to_datetime(panel.date, errors="raise")
    strict_historical = pd.read_csv(HISTORICAL_STRICT_PATH)
    proximity_historical = pd.read_csv(HISTORICAL_PROXIMITY_PATH)
    primary_pairs = candidate_pairs(candidates, "primary")
    relaxed_pairs = candidate_pairs(candidates, "relaxed")
    if len(primary_pairs) != EXPECTED_PRIMARY_PAIRS or len(relaxed_pairs) != EXPECTED_RELAXED_PAIRS:
        raise ValueError("Unexpected stage-23 candidate counts")
    primary_treated_ids = set(primary_pairs.treated_municipality_bfs_id.astype(int))
    strict_historical_retained = int((
        as_bool(strict_historical.historical_first_exposure_retained)
        & strict_historical.municipality_bfs_id.astype(int).isin(primary_treated_ids)
    ).sum())
    proximity_historical_retained = int((
        as_bool(proximity_historical.historical_first_exposure_retained)
        & proximity_historical.municipality_bfs_id.astype(int).isin(primary_treated_ids)
    ).sum())
    window = config["event_window"]
    primary_stack = build_stack(
        primary_pairs, panel, int(window["start_month"]), int(window["end_month"]), "primary"
    )
    relaxed_stack = build_stack(
        relaxed_pairs, panel, int(window["start_month"]), int(window["end_month"]), "relaxed"
    )
    truncated_stack = primary_stack[
        primary_stack.event_month.le(int(window["uniform_truncated_post_end_month"]))
    ].copy()
    targeted_ids = set(int(value) for value in config["targeted_sensitivity_control_bfs_ids"])
    conservative_pairs = primary_pairs[
        ~primary_pairs.control_municipality_bfs_id.astype(int).isin(targeted_ids)
    ].copy()
    conservative_stack = build_stack(
        conservative_pairs, panel, int(window["start_month"]), int(window["end_month"]),
        "primary_conservative_control_exclusion",
    )

    estimates = pd.DataFrame([
        static_estimate(primary_stack, "primary_full_24m_post", "primary"),
        static_estimate(
            truncated_stack, "primary_post_truncated_at_month_13", "primary"
        ),
        static_estimate(relaxed_stack, "relaxed_full_24m_post", "relaxed"),
        static_estimate(
            conservative_stack,
            "primary_excluding_targeted_sensitivity_controls",
            "primary_conservative_control_exclusion",
        ),
    ])
    events = pd.concat([
        event_study(primary_stack, config["event_study_bins"], "primary"),
        event_study(relaxed_stack, config["event_study_bins"], "relaxed"),
    ], ignore_index=True)
    influence = influence_sensitivities(primary_pairs, panel, config)
    decomposition = treated_decomposition(primary_stack)
    summary = build_summary(
        estimates,
        events,
        influence,
        decomposition,
        strict_historical_retained,
        proximity_historical_retained,
        config,
    )

    if summary["primary_treated_municipalities"] != 6:
        raise ValueError("Expected six primary treated municipalities")
    if summary["primary_treated_retained_under_250m_proximity_transfer_sensitivity"] != 6:
        raise ValueError("Expected all six primary treatments under the 250 m historical sensitivity")
    if summary["causal_estimation_approved"] or summary["causal_effect_claim_allowed"]:
        raise ValueError("Pilot must not grant causal approval")

    STACK_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    combined_stack = pd.concat([primary_stack, relaxed_stack], ignore_index=True)
    combined_stack.to_csv(STACK_OUTPUT, index=False, lineterminator="\n")
    estimates.to_csv(ESTIMATE_OUTPUT, index=False, lineterminator="\n")
    events.to_csv(EVENT_OUTPUT, index=False, lineterminator="\n")
    influence.to_csv(INFLUENCE_OUTPUT, index=False, lineterminator="\n")
    decomposition.to_csv(DECOMPOSITION_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(estimates, events, decomposition, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
