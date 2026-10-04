"""Version approved COVID option A and pre-treatment foreign-share baseline.

The researcher selected a 24-month ratio-of-sums baseline.  This stage keeps all
cohorts and months, records the official core sensitivity interval, and exports
the selected characteristic without choosing how to handle unavailable values,
a comparison group, or an estimator.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_covid_specification.json"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
COVERAGE_PATH = ROOT / "reports" / "accessibility_all_cohort_municipality_coverage.csv"
TEMPORAL_CONFIG_PATH = ROOT / "config" / "temporal_controls.json"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
OUTPUT_PATH = ROOT / "reports" / "accessibility_covid_foreign_share_baseline_audit.csv"
SELECTED_OUTPUT_PATH = (
    ROOT / "reports" / "accessibility_covid_foreign_share_selected.csv"
)
SUMMARY_PATH = ROOT / "reports" / "accessibility_covid_specification_summary.json"
REPORT_PATH = ROOT / "reports" / "74_SPECIFICATION_COVID_ET_BASELINE_CLIENTELE_FR.md"
SOURCE_ID = "DERIVED_ACCESSIBILITY_COVID_SPECIFICATION"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def successful_evidence_metadata(source_id: str) -> dict:
    candidates: list[tuple[str, dict]] = []
    for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json")):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata.get("source_id") == source_id and metadata.get("http_status") == 200:
            candidates.append((str(metadata.get("retrieval_date", "")), metadata))
    if not candidates:
        raise FileNotFoundError(f"No successful cached evidence for {source_id}")
    metadata = max(candidates, key=lambda item: item[0])[1]
    raw_path = ROOT / metadata["raw_file"]
    if not raw_path.exists() or sha256(raw_path) != metadata["sha256"]:
        raise ValueError(f"Evidence integrity failure for {source_id}")
    return metadata


def exposure_status(first_exposure: pd.Timestamp | pd.NaT, cohort: pd.Timestamp) -> str:
    if pd.isna(first_exposure):
        return "never_exposed_in_current_120min_matrix"
    if first_exposure == cohort:
        return "first_exposed_in_focal_cohort"
    if first_exposure < cohort:
        return "previously_exposed_before_focal_cohort"
    return "not_yet_exposed_at_focal_cohort"


def cutoff_and_reason(
    cohort: pd.Timestamp,
    first_exposure: pd.Timestamp | pd.NaT,
    pandemic_start: pd.Timestamp,
) -> tuple[pd.Timestamp, str]:
    candidates = {
        "focal_cohort": cohort,
        "pandemic_start": pandemic_start,
    }
    if pd.notna(first_exposure):
        candidates["municipality_first_exposure"] = first_exposure
    cutoff = min(candidates.values())
    reasons = sorted(key for key, value in candidates.items() if value == cutoff)
    return cutoff, "|".join(reasons)


def share_metrics(window: pd.DataFrame, horizon: int) -> dict[str, object]:
    valid = window[
        window.domestic_overnights.notna() & window.foreign_overnights.notna()
    ].copy()
    valid["origin_total"] = valid.domestic_overnights + valid.foreign_overnights
    positive = valid[valid.origin_total.gt(0)].copy()
    foreign_sum = float(positive.foreign_overnights.sum()) if len(positive) else np.nan
    total_sum = float(positive.origin_total.sum()) if len(positive) else np.nan
    ratio = foreign_sum / total_sum if total_sum and total_sum > 0 else np.nan
    monthly_mean = (
        float((positive.foreign_overnights / positive.origin_total).mean())
        if len(positive)
        else np.nan
    )
    prefix = f"baseline_{horizon}m"
    return {
        f"{prefix}_calendar_months": int(len(window)),
        f"{prefix}_observed_origin_months": int(len(valid)),
        f"{prefix}_positive_total_months": int(len(positive)),
        f"{prefix}_complete": bool(len(window) == horizon and len(valid) == horizon),
        f"{prefix}_foreign_overnights_sum": foreign_sum,
        f"{prefix}_total_overnights_sum": total_sum,
        f"{prefix}_foreign_share_ratio_of_sums": ratio,
        f"{prefix}_foreign_share_mean_monthly": monthly_mean,
        f"{prefix}_aggregation_abs_difference": (
            abs(ratio - monthly_mean)
            if pd.notna(ratio) and pd.notna(monthly_mean)
            else np.nan
        ),
    }


def build_audit(config: dict, panel: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    exposed = coverage[coverage.accessibility_threshold_minutes.eq(120)].copy()
    exposed = exposed[["municipality_bfs_id", "first_exposure_month"]].drop_duplicates()
    first_exposure = dict(
        zip(exposed.municipality_bfs_id.astype(int), exposed.first_exposure_month)
    )
    cohorts = sorted(exposed.first_exposure_month.dropna().unique())
    pandemic_start = pd.Timestamp(config["official_core_disruption_start"])
    horizons = [int(value) for value in config["foreign_share_baseline_window_candidates_months"]]
    municipality_names = (
        panel[["municipality_bfs_id", "municipality_name_source"]]
        .drop_duplicates()
        .set_index("municipality_bfs_id")
        .municipality_name_source
        .to_dict()
    )
    rows: list[dict[str, object]] = []
    for cohort_value in cohorts:
        cohort = pd.Timestamp(cohort_value)
        for municipality_bfs_id, local in panel.groupby("municipality_bfs_id", sort=True):
            municipality_bfs_id = int(municipality_bfs_id)
            first = first_exposure.get(municipality_bfs_id, pd.NaT)
            cutoff, cutoff_reason = cutoff_and_reason(cohort, first, pandemic_start)
            row: dict[str, object] = {
                "focal_cohort_month": cohort.date().isoformat(),
                "municipality_bfs_id": municipality_bfs_id,
                "municipality_name": municipality_names[municipality_bfs_id],
                "municipality_first_exposure_month_120min": (
                    first.date().isoformat() if pd.notna(first) else ""
                ),
                "exposure_status_at_focal_cohort": exposure_status(first, cohort),
                "baseline_cutoff_month_exclusive": cutoff.date().isoformat(),
                "baseline_cutoff_reason": cutoff_reason,
                "baseline_ends_before_pandemic": bool(cutoff <= pandemic_start),
                "baseline_ends_before_first_exposure": bool(
                    pd.isna(first) or cutoff <= first
                ),
                "primary_sample_month_policy": config["primary_sample_month_policy"],
                "common_shock_adjustment": config["common_shock_adjustment"],
                "analysis_sample_selected": False,
                "cohort_comparison_rule_selected": False,
                "causal_estimation_approved": False,
                "source_id": SOURCE_ID,
            }
            for horizon in horizons:
                start = cutoff - pd.DateOffset(months=horizon)
                end = cutoff - pd.DateOffset(months=1)
                window = local[local.date.between(start, end)].copy()
                row[f"baseline_{horizon}m_start"] = start.date().isoformat()
                row[f"baseline_{horizon}m_end"] = end.date().isoformat()
                row.update(share_metrics(window, horizon))
            rows.append(row)
    result = pd.DataFrame(rows).sort_values(
        ["focal_cohort_month", "municipality_bfs_id"], kind="stable"
    )
    return result.reset_index(drop=True)


def build_summary(config: dict, audit: pd.DataFrame, evidence: dict[str, dict]) -> dict:
    horizons = [int(value) for value in config["foreign_share_baseline_window_candidates_months"]]
    first = audit[
        audit.exposure_status_at_focal_cohort.eq("first_exposed_in_focal_cohort")
    ]
    first_missing_24 = first[
        first.baseline_24m_foreign_share_ratio_of_sums.isna()
    ][["municipality_bfs_id", "municipality_name", "focal_cohort_month"]]
    window_summary: dict[str, dict] = {}
    for horizon in horizons:
        prefix = f"baseline_{horizon}m"
        available = audit[f"{prefix}_foreign_share_ratio_of_sums"].notna()
        complete = audit[f"{prefix}_complete"].astype(bool)
        first_available = first[f"{prefix}_foreign_share_ratio_of_sums"].notna()
        first_complete = first[f"{prefix}_complete"].astype(bool)
        differences = audit.loc[available, f"{prefix}_aggregation_abs_difference"]
        window_summary[str(horizon)] = {
            "municipality_cohort_rows": int(len(audit)),
            "rows_with_complete_baseline": int(complete.sum()),
            "rows_with_any_foreign_share": int(available.sum()),
            "first_exposed_municipalities": int(len(first)),
            "first_exposed_with_complete_baseline": int(first_complete.sum()),
            "first_exposed_with_any_foreign_share": int(first_available.sum()),
            "aggregation_methods_correlation": float(
                audit.loc[available, f"{prefix}_foreign_share_ratio_of_sums"].corr(
                    audit.loc[available, f"{prefix}_foreign_share_mean_monthly"]
                )
            ),
            "aggregation_abs_difference_median": float(differences.median()),
            "aggregation_abs_difference_p95": float(differences.quantile(0.95)),
            "aggregation_abs_difference_max": float(differences.max()),
        }
    selected_horizon = int(config["foreign_share_baseline_window_selected_months"])
    selected_prefix = f"baseline_{selected_horizon}m"
    selected_available = audit[
        f"{selected_prefix}_foreign_share_ratio_of_sums"
    ].notna()
    first_selected_available = first[
        f"{selected_prefix}_foreign_share_ratio_of_sums"
    ].notna()
    return {
        "specification_version": config["specification_version"],
        "researcher_approved_option": config["researcher_approved_option"],
        "primary_sample_month_policy": config["primary_sample_month_policy"],
        "common_shock_adjustment": config["common_shock_adjustment"],
        "standalone_national_covid_dummy_in_primary_model": config[
            "standalone_national_covid_dummy_in_primary_model"
        ],
        "official_core_disruption_start": config["official_core_disruption_start"],
        "official_core_disruption_end": config["official_core_disruption_end"],
        "core_period_exclusion_sensitivity": config["core_period_exclusion_sensitivity"],
        "legacy_broad_interval_secondary_sensitivity": config[
            "legacy_broad_interval_secondary_sensitivity"
        ],
        "panel_municipalities": int(audit.municipality_bfs_id.nunique()),
        "first_exposure_cohorts": int(audit.focal_cohort_month.nunique()),
        "municipality_cohort_rows": int(len(audit)),
        "unique_first_exposed_municipalities": int(first.municipality_bfs_id.nunique()),
        "first_exposed_without_any_24m_foreign_share": first_missing_24.to_dict(
            orient="records"
        ),
        "baseline_window_audit": window_summary,
        "foreign_share_baseline_window_selected_months": config[
            "foreign_share_baseline_window_selected_months"
        ],
        "foreign_share_aggregation_selected": config[
            "foreign_share_aggregation_selected"
        ],
        "selected_foreign_share_rows_available": int(selected_available.sum()),
        "selected_foreign_share_rows_missing": int((~selected_available).sum()),
        "first_exposed_with_selected_foreign_share": int(
            first_selected_available.sum()
        ),
        "first_exposed_without_selected_foreign_share": int(
            (~first_selected_available).sum()
        ),
        "foreign_share_missing_handling_selected": False,
        "analysis_sample_selected": False,
        "cohort_comparison_rule_selected": False,
        "causal_estimation_approved": False,
        "official_evidence": {
            source_id: {
                "raw_file": metadata["raw_file"],
                "sha256": metadata["sha256"],
                "retrieval_date": metadata["retrieval_date"],
                "final_url": metadata.get("final_url", metadata.get("url", "")),
            }
            for source_id, metadata in evidence.items()
        },
        "input_sha256": {
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            PANEL_PATH.relative_to(ROOT).as_posix(): sha256(PANEL_PATH),
            COVERAGE_PATH.relative_to(ROOT).as_posix(): sha256(COVERAGE_PATH),
            TEMPORAL_CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(TEMPORAL_CONFIG_PATH),
        },
        "source_id": SOURCE_ID,
    }


def build_selected_baseline(config: dict, audit: pd.DataFrame) -> pd.DataFrame:
    """Export the approved characteristic without silently resolving missing data."""
    horizon = int(config["foreign_share_baseline_window_selected_months"])
    if horizon != 24:
        raise ValueError(f"Stage 27 expects the approved 24-month window, found {horizon}")
    aggregation = config["foreign_share_aggregation_selected"]
    if aggregation != "ratio_of_summed_foreign_to_summed_total_overnights":
        raise ValueError(f"Unexpected approved aggregation: {aggregation}")
    prefix = f"baseline_{horizon}m"
    selected = audit[
        [
            "focal_cohort_month",
            "municipality_bfs_id",
            "municipality_name",
            "municipality_first_exposure_month_120min",
            "exposure_status_at_focal_cohort",
            "baseline_cutoff_month_exclusive",
            "baseline_cutoff_reason",
            "baseline_ends_before_pandemic",
            "baseline_ends_before_first_exposure",
            "primary_sample_month_policy",
            "common_shock_adjustment",
            f"{prefix}_start",
            f"{prefix}_end",
            f"{prefix}_observed_origin_months",
            f"{prefix}_complete",
            f"{prefix}_foreign_overnights_sum",
            f"{prefix}_total_overnights_sum",
            f"{prefix}_foreign_share_ratio_of_sums",
            "analysis_sample_selected",
            "cohort_comparison_rule_selected",
            "causal_estimation_approved",
            "source_id",
        ]
    ].copy()
    selected = selected.rename(
        columns={
            f"{prefix}_start": "selected_baseline_start",
            f"{prefix}_end": "selected_baseline_end",
            f"{prefix}_observed_origin_months": "selected_baseline_observed_origin_months",
            f"{prefix}_complete": "selected_baseline_complete",
            f"{prefix}_foreign_overnights_sum": "selected_foreign_overnights_sum",
            f"{prefix}_total_overnights_sum": "selected_total_overnights_sum",
            f"{prefix}_foreign_share_ratio_of_sums": "selected_foreign_share",
        }
    )
    selected.insert(11, "selected_baseline_window_months", horizon)
    selected.insert(12, "selected_foreign_share_aggregation", aggregation)
    selected["selected_foreign_share_available"] = selected[
        "selected_foreign_share"
    ].notna()
    selected["foreign_share_missing_handling_selected"] = False
    return selected


def write_report(summary: dict) -> None:
    w12 = summary["baseline_window_audit"]["12"]
    w24 = summary["baseline_window_audit"]["24"]
    w36 = summary["baseline_window_audit"]["36"]
    missing_names = ", ".join(
        item["municipality_name"]
        for item in summary["first_exposed_without_any_24m_foreign_share"]
    )
    lines = [
        "# Spécification COVID et baseline de clientèle - étape 27",
        "",
        "**Statut : option A, baseline de 24 mois et ratio des sommes approuvés. Le traitement des valeurs manquantes reste à valider avant estimation.**",
        "",
        "## Règles déjà validées",
        "",
        "- Tous les mois disponibles et toutes les cohortes restent dans l'analyse principale.",
        "- Les effets fixes de mois calendaires absorbent les chocs nationaux communs. Une indicatrice COVID nationale seule n'est donc pas ajoutée séparément.",
        "- La sensibilité principale retirera mars 2020 à mars 2022 inclus. L'ancien intervalle large jusqu'à avril 2022 est conservé seulement pour comparer avec les résultats antérieurs.",
        "- L'interaction COVID utilisera une part de clientèle étrangère calculée avant la pandémie, avant la première exposition propre de la commune et avant la cohorte examinée.",
        "- La caractéristique approuvée couvre 24 mois et correspond au ratio entre la somme des nuitées étrangères et la somme des nuitées domestiques plus étrangères.",
        "",
        "## Disponibilité des baselines candidates",
        "",
        "L'audit couvre 186 communes × 7 cohortes, soit 1 302 lignes. Il ne sélectionne aucun témoin ni traitement.",
        "",
        "| Baseline | Lignes complètes sur 1 302 | Premières expositions complètes sur 80 | Premières expositions avec une part calculable | Principal compromis |",
        "|---:|---:|---:|---:|---|",
        f"| 12 mois | {w12['rows_with_complete_baseline']} | {w12['first_exposed_with_complete_baseline']} | {w12['first_exposed_with_any_foreign_share']} | Couverture maximale, mais mesure plus volatile |",
        f"| 24 mois | {w24['rows_with_complete_baseline']} | {w24['first_exposed_with_complete_baseline']} | {w24['first_exposed_with_any_foreign_share']} | Deux cycles saisonniers, sans perdre de commune exposée observable |",
        f"| 36 mois | {w36['rows_with_complete_baseline']} | {w36['first_exposed_with_complete_baseline']} | {w36['first_exposed_with_any_foreign_share']} | Plus stable, mais une commune exposée complète en moins |",
        "",
        f"Quatre des 80 communes exposées n'ont aucune part calculable avant leur exposition sous leur identifiant communal actuel : {missing_names}. Elles ne sont pas exclues par ce rapport.",
        "",
        "## Agrégation validée",
        "",
        "Le **ratio des sommes** est retenu : somme des nuitées étrangères divisée par la somme des nuitées totales. Les mois de forte fréquentation pèsent donc davantage.",
        "",
        f"Sur la baseline de 24 mois, les deux mesures sont fortement corrélées. Leur corrélation est {w24['aggregation_methods_correlation']:.3f}; l'écart absolu médian est {100*w24['aggregation_abs_difference_median']:.1f} point de pourcentage et le 95e percentile {100*w24['aggregation_abs_difference_p95']:.1f} points.",
        "",
        "## Décision enregistrée",
        "",
        "La **baseline de 24 mois avec ratio des sommes** est maintenant verrouillée. Le fichier sélectionné conserve les 1 302 lignes commune-cohorte; il ne retire ni n'impute les valeurs manquantes.",
        "",
        "## Nouvelle décision méthodologique requise : quatre historiques manquants",
        "",
        f"La part approuvée est disponible pour {summary['first_exposed_with_selected_foreign_share']} des 80 premières expositions. Elle manque pour : {missing_names}.",
        "",
        "- **A — reconstruire les historiques (recommandé pour maximiser l'inclusion)** : Moutier peut être relié à sa série BFS 700 grâce au pont officiel déjà documenté. Pour les trois autres cas, il faut collecter les séries HESTA des entités antérieures et leurs mutations officielles, puis agréger seulement sur un périmètre territorial justifié.",
        "- **B — interaction sur cas complets** : garder les 80 communes dans le modèle principal sans interaction, mais estimer l'hétérogénéité selon la clientèle étrangère sur les 76 cas disponibles.",
        "- **C — indicatrice de valeur manquante** : conserver les 80 cas dans l'interaction en centrant conventionnellement la part manquante et en ajoutant un terme spécifique. Cette solution préserve la taille, mais repose sur une convention de modélisation plus forte.",
        "",
        "Aucune de ces trois solutions n'est appliquée sans validation. Aucune comparaison de cohorte, aucun échantillon et aucun estimateur n'est choisi ici.",
        "",
        "## Sources",
        "",
        "- Chronologie officielle des décisions COVID du Conseil fédéral : `SWISS_FEDERAL_COUNCIL_COVID_DECISION_CHRONOLOGY`.",
        "- Effondrement de la demande hôtelière 2020 et exposition particulière de la clientèle étrangère : `BFS_HOTEL_DEMAND_COVID_2020`.",
        "- Nuitées domestiques et étrangères mensuelles : panel HESTA déjà enregistré dans le projet.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    panel = pd.read_csv(PANEL_PATH, parse_dates=["date"])
    coverage = pd.read_csv(COVERAGE_PATH, parse_dates=["first_exposure_month"])
    evidence = {
        source_id: successful_evidence_metadata(source_id)
        for source_id in config["official_source_ids"]
    }
    audit = build_audit(config, panel, coverage)
    selected = build_selected_baseline(config, audit)
    summary = build_summary(config, audit, evidence)

    if len(audit) != 186 * 7:
        raise ValueError(f"Expected 1,302 municipality-cohort rows, found {len(audit)}")
    if not audit.baseline_ends_before_pandemic.all():
        raise ValueError("Every baseline must end before the pandemic")
    if not audit.baseline_ends_before_first_exposure.all():
        raise ValueError("Every baseline must end before own first exposure")
    if audit.analysis_sample_selected.any() or audit.causal_estimation_approved.any():
        raise ValueError("Stage 27 availability audit cannot select a sample or approve causality")
    if len(selected) != len(audit):
        raise ValueError("The selected characteristic export must preserve every audit row")
    if selected.foreign_share_missing_handling_selected.any():
        raise ValueError("Missing-characteristic handling requires a separate approval")

    audit.to_csv(OUTPUT_PATH, index=False, lineterminator="\n")
    selected.to_csv(SELECTED_OUTPUT_PATH, index=False, lineterminator="\n")
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
