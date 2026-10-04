"""Audit small-cluster inference for the non-causal accessibility pilot."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_small_cluster_inference.json"
STACK_PATH = ROOT / "data_processed" / "accessibility_pilot_stacked_panel.csv"
ESTIMATE_PATH = ROOT / "reports" / "accessibility_pilot_did_estimates.csv"

INFERENCE_OUTPUT = ROOT / "reports" / "accessibility_pilot_small_cluster_inference.csv"
COMPONENT_OUTPUT = ROOT / "reports" / "accessibility_pilot_inference_components.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_pilot_small_cluster_inference_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "72_INFERENCE_PETIT_NOMBRE_COMMUNES_FR.md"

SOURCE_ID = "DERIVED_ACCESSIBILITY_SMALL_CLUSTER_INFERENCE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def student_t_cdf(value: float, degrees_of_freedom: int) -> float:
    """Numerically integrate the Student t density without an optional SciPy dependency."""
    if degrees_of_freedom <= 0:
        raise ValueError("Student t degrees of freedom must be positive")
    if value == 0:
        return 0.5
    upper = abs(float(value))
    intervals = max(4_000, int(math.ceil(upper * 4_000)))
    if intervals % 2:
        intervals += 1
    grid = np.linspace(0.0, upper, intervals + 1)
    constant = math.exp(
        math.lgamma((degrees_of_freedom + 1) / 2)
        - math.lgamma(degrees_of_freedom / 2)
    ) / math.sqrt(degrees_of_freedom * math.pi)
    density = constant * (1 + grid**2 / degrees_of_freedom) ** (
        -(degrees_of_freedom + 1) / 2
    )
    step = upper / intervals
    integral = step / 3 * (
        density[0]
        + density[-1]
        + 4 * density[1:-1:2].sum()
        + 2 * density[2:-1:2].sum()
    )
    cdf = 0.5 + integral
    return float(cdf if value > 0 else 1 - cdf)


def student_t_critical(probability: float, degrees_of_freedom: int) -> float:
    lower, upper = 0.0, 20.0
    for _ in range(60):
        midpoint = (lower + upper) / 2
        if student_t_cdf(midpoint, degrees_of_freedom) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return float((lower + upper) / 2)


def stack_effects(primary_stack: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for stack_id, group in primary_stack.groupby(
        "stack_treated_municipality_bfs_id", sort=True
    ):
        treated = group[as_bool(group.is_treated_municipality)].set_index(
            "event_month"
        ).log_overnights
        controls = group[~as_bool(group.is_treated_municipality)].copy()
        controls["weighted_log_overnights"] = (
            controls.log_overnights * controls.stack_unit_weight
        )
        control_mean = controls.groupby("event_month").weighted_log_overnights.sum()
        gap = treated - control_mean
        effect = float(gap[gap.index >= 0].mean() - gap[gap.index < 0].mean())
        unit_rows = (
            group[["municipality_bfs_id", "municipality_name"]]
            .drop_duplicates()
            .sort_values("municipality_bfs_id", kind="stable")
        )
        rows.append({
            "stack_treated_municipality_bfs_id": int(stack_id),
            "stack_treated_municipality_name": str(
                group.stack_treated_municipality_name.iloc[0]
            ),
            "municipality_bfs_ids": "|".join(
                unit_rows.municipality_bfs_id.astype(int).astype(str)
            ),
            "municipality_names": "|".join(unit_rows.municipality_name.astype(str)),
            "stack_post_minus_pre_log_gap": effect,
        })
    return pd.DataFrame(rows)


def connected_components(effects: pd.DataFrame) -> list[list[int]]:
    stack_ids = effects.stack_treated_municipality_bfs_id.astype(int).tolist()
    unit_sets = {
        int(row.stack_treated_municipality_bfs_id): {
            int(value) for value in str(row.municipality_bfs_ids).split("|")
        }
        for row in effects.itertuples(index=False)
    }
    parent = {stack_id: stack_id for stack_id in stack_ids}

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    for left_position, left in enumerate(stack_ids):
        for right in stack_ids[left_position + 1:]:
            if unit_sets[left] & unit_sets[right]:
                union(left, right)
    grouped: dict[int, list[int]] = {}
    for stack_id in stack_ids:
        grouped.setdefault(find(stack_id), []).append(stack_id)
    return [sorted(values) for _, values in sorted(grouped.items())]


def build_component_audit(effects: pd.DataFrame) -> pd.DataFrame:
    effect_lookup = effects.set_index("stack_treated_municipality_bfs_id")
    unit_lookup = {
        int(row.stack_treated_municipality_bfs_id): {
            int(value) for value in str(row.municipality_bfs_ids).split("|")
        }
        for row in effects.itertuples(index=False)
    }
    rows = []
    total_stacks = len(effects)
    for position, stack_ids in enumerate(connected_components(effects), start=1):
        municipality_counts: dict[int, int] = {}
        for stack_id in stack_ids:
            for municipality_id in unit_lookup[stack_id]:
                municipality_counts[municipality_id] = municipality_counts.get(municipality_id, 0) + 1
        reused = sorted(
            municipality_id
            for municipality_id, count in municipality_counts.items()
            if count > 1
        )
        component_sum = float(
            effect_lookup.loc[stack_ids, "stack_post_minus_pre_log_gap"].sum()
        )
        rows.append({
            "component_id": f"component_{position:02d}",
            "treated_stack_bfs_ids": "|".join(str(value) for value in stack_ids),
            "treated_stack_names": "|".join(
                effect_lookup.loc[stack_ids, "stack_treated_municipality_name"].tolist()
            ),
            "treated_stack_count": len(stack_ids),
            "unique_municipality_count": len(municipality_counts),
            "reused_municipality_bfs_ids_linking_stacks": "|".join(
                str(value) for value in reused
            ),
            "sum_stack_log_gaps": component_sum,
            "contribution_to_equal_stack_mean_log_points": component_sum / total_stacks,
            "source_id": SOURCE_ID,
        })
    return pd.DataFrame(rows)


def exact_component_sign_flip(component_audit: pd.DataFrame) -> dict:
    contributions = component_audit.contribution_to_equal_stack_mean_log_points.to_numpy(float)
    observed = float(contributions.sum())
    randomized = np.array([
        float(np.dot(np.asarray(signs, dtype=float), contributions))
        for signs in itertools.product((-1, 1), repeat=len(contributions))
    ])
    tolerance = 1e-14
    exceedances = int((np.abs(randomized) >= abs(observed) - tolerance).sum())
    return {
        "observed_log_points": observed,
        "sign_pattern_count": int(len(randomized)),
        "absolute_exceedance_count": exceedances,
        "two_sided_p_value": float(exceedances / len(randomized)),
        "minimum_attainable_two_sided_p_value": float(2 / len(randomized)),
        "randomized_absolute_statistic_min": float(np.abs(randomized).min()),
        "randomized_absolute_statistic_median": float(np.median(np.abs(randomized))),
        "randomized_absolute_statistic_max": float(np.abs(randomized).max()),
    }


def build_outputs(config: dict, stack: pd.DataFrame, estimates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    primary = stack[stack.analysis_tier.eq("primary")].copy()
    effects = stack_effects(primary)
    reported = estimates[
        estimates.scenario_id.eq(config["target_scenario_id"])
    ].iloc[0]
    effect_mean = float(effects.stack_post_minus_pre_log_gap.mean())
    if not np.isclose(effect_mean, float(reported.estimate_log_points), atol=1e-12):
        raise ValueError("Treated-stack mean does not reproduce the stage-24 estimate")

    stack_count = len(effects)
    degrees_of_freedom = stack_count - 1
    t_standard_error = float(
        effects.stack_post_minus_pre_log_gap.std(ddof=1) / math.sqrt(stack_count)
    )
    t_statistic = effect_mean / t_standard_error
    t_p_value = float(2 * (1 - student_t_cdf(abs(t_statistic), degrees_of_freedom)))
    t_critical = student_t_critical(0.975, degrees_of_freedom)
    t_lower = effect_mean - t_critical * t_standard_error
    t_upper = effect_mean + t_critical * t_standard_error

    normal_standard_error = float(reported.cluster_robust_standard_error)
    normal_statistic = effect_mean / normal_standard_error
    normal_p_value = float(2 * (1 - NormalDist().cdf(abs(normal_statistic))))

    components = build_component_audit(effects)
    sign_flip = exact_component_sign_flip(components)
    if not np.isclose(sign_flip["observed_log_points"], effect_mean, atol=1e-12):
        raise ValueError("Component contributions do not reproduce the target estimate")

    inference = pd.DataFrame([{
        "scenario_id": config["target_scenario_id"],
        "estimate_log_points": effect_mean,
        "estimate_percent_change": float(np.expm1(effect_mean)),
        "municipality_cluster_count": int(reported.municipality_cluster_count),
        "treated_stack_count": stack_count,
        "connected_component_count": len(components),
        "normal_cluster_robust_standard_error": normal_standard_error,
        "normal_reference_statistic": normal_statistic,
        "normal_reference_two_sided_p_value": normal_p_value,
        "normal_ci95_lower_log_points": float(reported.ci95_normal_lower_log_points),
        "normal_ci95_upper_log_points": float(reported.ci95_normal_upper_log_points),
        "treated_stack_t_standard_error": t_standard_error,
        "treated_stack_t_degrees_of_freedom": degrees_of_freedom,
        "treated_stack_t_statistic": t_statistic,
        "treated_stack_t_two_sided_p_value": t_p_value,
        "treated_stack_t_ci95_lower_log_points": t_lower,
        "treated_stack_t_ci95_upper_log_points": t_upper,
        "treated_stack_t_ci95_lower_percent_change": float(np.expm1(t_lower)),
        "treated_stack_t_ci95_upper_percent_change": float(np.expm1(t_upper)),
        "component_sign_pattern_count": sign_flip["sign_pattern_count"],
        "component_sign_flip_exceedance_count": sign_flip["absolute_exceedance_count"],
        "component_sign_flip_two_sided_p_value": sign_flip["two_sided_p_value"],
        "component_sign_flip_minimum_two_sided_p_value": sign_flip[
            "minimum_attainable_two_sided_p_value"
        ],
        "causal_estimation_approved": False,
        "causal_effect_claim_allowed": False,
        "sign_flip_is_random_assignment_test": False,
        "interpretation": "small_cluster_inference_sensitivity_for_non_causal_pilot",
        "source_id": SOURCE_ID,
    }])
    summary = {
        "specification_version": config["specification_version"],
        "scenario_id": config["target_scenario_id"],
        "estimate_log_points": effect_mean,
        "estimate_percent_change": float(np.expm1(effect_mean)),
        "treated_stack_count": stack_count,
        "municipality_cluster_count": int(reported.municipality_cluster_count),
        "connected_component_count": len(components),
        "reused_linking_municipality_bfs_ids": sorted({
            int(value)
            for text in components.reused_municipality_bfs_ids_linking_stacks
            if str(text).strip()
            for value in str(text).split("|")
        }),
        "normal_reference_two_sided_p_value": normal_p_value,
        "treated_stack_t_two_sided_p_value": t_p_value,
        "treated_stack_t_ci95_percent_change": [
            float(np.expm1(t_lower)), float(np.expm1(t_upper))
        ],
        "component_sign_flip_two_sided_p_value": sign_flip["two_sided_p_value"],
        "component_sign_flip_sign_patterns": sign_flip["sign_pattern_count"],
        "component_sign_flip_minimum_two_sided_p_value": sign_flip[
            "minimum_attainable_two_sided_p_value"
        ],
        "causal_estimation_approved": False,
        "causal_effect_claim_allowed": False,
        "sign_flip_is_random_assignment_test": False,
        "conclusion": (
            "The negative pilot mean is not robustly distinguishable from zero under the "
            "small-effective-sample reference checks and remains non-causal exploratory evidence."
        ),
        "input_sha256": {
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            STACK_PATH.relative_to(ROOT).as_posix(): sha256(STACK_PATH),
            ESTIMATE_PATH.relative_to(ROOT).as_posix(): sha256(ESTIMATE_PATH),
        },
        "methodological_sources": config["methodological_sources"],
        "source_id": SOURCE_ID,
    }
    return inference, components, summary


def write_report(inference: pd.DataFrame, components: pd.DataFrame, summary: dict) -> None:
    row = inference.iloc[0]
    lines = [
        "# Inférence avec peu de communes - étape 25",
        "",
        "**Statut : sensibilité du pilote non causal; aucune estimation causale approuvée.**",
        "",
        "## Pourquoi ce contrôle",
        "",
        f"L'intervalle initial regroupe {int(row.municipality_cluster_count)} communes, mais l'effet moyen "
        f"repose en réalité sur seulement **{int(row.treated_stack_count)} communes traitées**. Avec si peu "
        "d'unités effectivement traitées, les approximations normales peuvent donner une impression de "
        "précision excessive. La littérature recommande donc d'exposer explicitement cette fragilité.",
        "",
        "## Deux sensibilités préenregistrées",
        "",
        "1. La référence *t* traite les six variations propres aux communes traitées comme les six "
        "observations effectives. Elle est facile à lire, mais reste approximative car Emmen sert de témoin "
        "à Bulle et à Gruyères.",
        "2. Le test de changement de signe relie d'abord les ensembles partageant une commune, puis énumère "
        "exactement tous les signes possibles des composantes disjointes du graphe. Sa lecture suppose "
        "l'indépendance de ces composantes et une symétrie sous l'hypothèse nulle; **ce n'est pas un test "
        "fondé sur une assignation aléatoire du Magic Pass**.",
        "",
        "## Résultat",
        "",
        "| Référence | Unités effectives | Valeur p bilatérale | Intervalle 95% |",
        "|---|---:|---:|---:|",
        f"| Normale, regroupée par commune | {int(row.municipality_cluster_count)} | "
        f"{row.normal_reference_two_sided_p_value:.3f} | "
        f"[{100 * np.expm1(row.normal_ci95_lower_log_points):.1f}%; "
        f"{100 * np.expm1(row.normal_ci95_upper_log_points):.1f}%] |",
        f"| *t* sur variations des communes traitées | {int(row.treated_stack_count)} | "
        f"{row.treated_stack_t_two_sided_p_value:.3f} | "
        f"[{100 * row.treated_stack_t_ci95_lower_percent_change:.1f}%; "
        f"{100 * row.treated_stack_t_ci95_upper_percent_change:.1f}%] |",
        f"| Signes exacts sur composantes connectées | {int(row.connected_component_count)} | "
        f"{row.component_sign_flip_two_sided_p_value:.3f} | non construit |",
        "",
        f"La moyenne reste **{100 * row.estimate_percent_change:.1f}%**, mais elle n'est plus distinguable de "
        "zéro avec les deux références adaptées au faible nombre d'unités effectives. Le test exact ne "
        f"dispose que de {int(row.component_sign_pattern_count)} configurations et sa valeur p minimale possible "
        f"est {row.component_sign_flip_minimum_two_sided_p_value:.4f}.",
        "",
        "## Structure de dépendance",
        "",
        "| Composante | Communes traitées | Lien partagé | Contribution au coefficient |",
        "|---|---|---|---:|",
    ]
    for component in components.itertuples(index=False):
        shared = component.reused_municipality_bfs_ids_linking_stacks or "aucun"
        lines.append(
            f"| {component.component_id} | {str(component.treated_stack_names).replace('|', ', ')} | "
            f"{shared} | {component.contribution_to_equal_stack_mean_log_points:.4f} |"
        )
    lines += [
        "",
        "## Conclusion pour le mémoire",
        "",
        "Le signe négatif constitue un **résultat exploratoire**, pas une preuve statistique robuste et "
        "encore moins un effet causal. La formulation défendable est : les comparaisons retenues suggèrent "
        "une baisse moyenne, mais cette conclusion dépend fortement de l'approximation d'inférence et de la "
        "composition des témoins. La sensibilité conservatrice de l'étape 24 (-2,0%, intervalle incluant "
        "zéro) reste l'autre résultat central à présenter.",
        "",
        "## Sources méthodologiques",
        "",
        "- Canay, Romano et Shaikh (2017), [tests par changements de signe sous symétrie approximative]"
        "(https://doi.org/10.3982/ECTA13081).",
        "- MacKinnon et Webb (2018), [limites de l'inférence avec peu de grappes traitées]"
        "(https://doi.org/10.1111/ectj.12107).",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_pilot_small_cluster_inference.csv` : résultat comparé ;",
        "- `reports/accessibility_pilot_inference_components.csv` : composantes et dépendances ;",
        "- `reports/accessibility_pilot_small_cluster_inference_summary.json` : résumé et empreintes ;",
        "- `config/accessibility_small_cluster_inference.json` : règles préenregistrées.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    stack = pd.read_csv(STACK_PATH)
    estimates = pd.read_csv(ESTIMATE_PATH)
    inference, components, summary = build_outputs(config, stack, estimates)
    row = inference.iloc[0]
    if int(row.treated_stack_count) != 6 or int(row.connected_component_count) != 5:
        raise ValueError("Expected six treated stacks and five connected components")
    if bool(row.causal_estimation_approved) or bool(row.causal_effect_claim_allowed):
        raise ValueError("Small-cluster sensitivity cannot grant causal approval")
    inference.to_csv(INFERENCE_OUTPUT, index=False, lineterminator="\n")
    components.to_csv(COMPONENT_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(inference, components, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
