"""Version approved COVID option A and pre-treatment foreign-share baseline.

The researcher selected a 24-month ratio-of-sums baseline.  This stage keeps all
cohorts and months, records the official core sensitivity interval, and exports
the selected characteristic without choosing how to handle unavailable values,
a comparison group, or an estimator.
"""

from __future__ import annotations

import hashlib
import json
from html import unescape
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_covid_specification.json"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
COVERAGE_PATH = ROOT / "reports" / "accessibility_all_cohort_municipality_coverage.csv"
TEMPORAL_CONFIG_PATH = ROOT / "config" / "temporal_controls.json"
RECONSTRUCTION_PATH = (
    ROOT / "config" / "accessibility_covid_foreign_share_reconstruction.csv"
)
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


def checked_reconstruction_evidence(
    reconstruction: pd.DataFrame,
) -> dict[str, dict]:
    source_ids = set(reconstruction.mutation_source_id)
    source_ids.add("BFS_HESTA_ARCHIVE_2020_METADATA")
    evidence = {
        source_id: successful_evidence_metadata(source_id)
        for source_id in sorted(source_ids)
    }
    archive_path = ROOT / evidence["BFS_HESTA_ARCHIVE_2020_METADATA"]["raw_file"]
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    municipality = next(
        variable for variable in archive["variables"] if variable["code"] == "Gemeinde"
    )
    archive_ids = {int(value) for value in municipality["values"]}
    archive_names = set(municipality["valueTexts"])
    for row in reconstruction.itertuples(index=False):
        mutation_path = ROOT / evidence[row.mutation_source_id]["raw_file"]
        mutation_text = unescape(
            mutation_path.read_text(encoding="utf-8", errors="replace")
        )
        target_name_token = (
            "Moutier" if row.target_name.startswith("Moutier") else row.target_name
        )
        predecessor_name_token = (
            "Moutier"
            if row.predecessor_name.startswith("Moutier")
            else row.predecessor_name
        )
        required_tokens = [
            str(row.target_bfs_id),
            target_name_token,
            str(row.predecessor_bfs_id),
            predecessor_name_token,
            pd.Timestamp(row.mutation_effective_date).strftime("%d.%m.%Y"),
        ]
        missing = [token for token in required_tokens if token not in mutation_text]
        if missing:
            raise ValueError(
                f"Mutation evidence {row.mutation_source_id} lacks tokens {missing}"
            )
        present = (
            int(row.predecessor_bfs_id) in archive_ids
            and row.predecessor_name in archive_names
        )
        expected_present = row.hesta_archive_status.startswith("present_in_checked")
        if present != expected_present and row.hesta_archive_status != "present_in_project_hesta_series":
            raise ValueError(
                f"Archived HESTA presence mismatch for {row.predecessor_name}"
            )
    return evidence


def build_summary(
    config: dict,
    audit: pd.DataFrame,
    selected: pd.DataFrame,
    reconstruction: pd.DataFrame,
    evidence: dict[str, dict],
) -> dict:
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
    selected_available = selected.selected_foreign_share.notna()
    first_selected = selected[
        selected.exposure_status_at_focal_cohort.eq("first_exposed_in_focal_cohort")
    ]
    first_selected_available = first_selected.selected_foreign_share.notna()
    first_selected_missing = first_selected.loc[
        ~first_selected_available,
        ["municipality_bfs_id", "municipality_name", "focal_cohort_month"],
    ]
    reconstructed_targets = reconstruction.loc[
        reconstruction.reconstruction_approved.astype(bool), "target_bfs_id"
    ].nunique()
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
        "first_exposed_without_selected_foreign_share_details": (
            first_selected_missing.to_dict(orient="records")
        ),
        "foreign_share_missing_handling_selected": config[
            "foreign_share_missing_handling_selected"
        ],
        "historical_reconstruction": {
            "targets_reviewed": int(reconstruction.target_bfs_id.nunique()),
            "targets_reconstructed": int(reconstructed_targets),
            "targets_unresolved": int(
                reconstruction.target_bfs_id.nunique() - reconstructed_targets
            ),
            "predecessor_components_reviewed": int(len(reconstruction)),
            "selected_rows_reconstructed": int(
                selected.foreign_share_reconstruction_applied.astype(bool).sum()
            ),
            "method": config["foreign_share_missing_handling_selected"],
        },
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
            RECONSTRUCTION_PATH.relative_to(ROOT).as_posix(): sha256(RECONSTRUCTION_PATH),
        },
        "source_id": SOURCE_ID,
    }


def build_selected_baseline(
    config: dict,
    audit: pd.DataFrame,
    panel: pd.DataFrame,
    reconstruction: pd.DataFrame,
) -> pd.DataFrame:
    """Export the approved characteristic and exact approved history bridges."""
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
    selected["foreign_share_reconstruction_applied"] = False
    selected["foreign_share_reconstruction_status"] = np.where(
        selected.selected_foreign_share_available,
        "not_required_observed_current_identifier",
        "unavailable_not_in_approved_reconstruction_targets",
    )
    selected["foreign_share_reconstruction_source_bfs_ids"] = ""
    selected["foreign_share_reconstruction_source_names"] = ""
    selected["foreign_share_reconstruction_source_ids"] = ""
    selected["foreign_share_reconstruction_component_coverage"] = ""

    for target_bfs_id, components in reconstruction.groupby("target_bfs_id", sort=True):
        target_mask = selected.municipality_bfs_id.eq(int(target_bfs_id))
        source_ids = sorted(components.predecessor_bfs_id.astype(int).tolist())
        source_names = sorted(components.predecessor_name.tolist())
        mutation_ids = sorted(set(components.mutation_source_id))
        approved = components.reconstruction_approved.astype(bool).all()
        available_components = int(
            components.hesta_archive_status.str.startswith("present_").sum()
        )
        coverage = f"{available_components}/{len(components)}"
        selected.loc[target_mask, "foreign_share_reconstruction_source_bfs_ids"] = (
            "|".join(str(value) for value in source_ids)
        )
        selected.loc[target_mask, "foreign_share_reconstruction_source_names"] = (
            "|".join(source_names)
        )
        selected.loc[target_mask, "foreign_share_reconstruction_source_ids"] = (
            "|".join(["BFS_HOTEL_DATA", *mutation_ids])
        )
        selected.loc[
            target_mask, "foreign_share_reconstruction_component_coverage"
        ] = coverage
        if not approved:
            selected.loc[target_mask, "foreign_share_reconstruction_status"] = (
                "blocked_incomplete_public_predecessor_coverage"
            )
            continue

        source_panel = panel[panel.municipality_bfs_id.isin(source_ids)].copy()
        if source_panel.municipality_bfs_id.nunique() != len(source_ids):
            raise ValueError(f"Approved source series missing for target {target_bfs_id}")
        for index in selected.index[target_mask]:
            start = pd.Timestamp(selected.at[index, "selected_baseline_start"])
            end = pd.Timestamp(selected.at[index, "selected_baseline_end"])
            window = source_panel[source_panel.date.between(start, end)].copy()
            monthly = (
                window.groupby("date", as_index=False)[
                    ["domestic_overnights", "foreign_overnights"]
                ]
                .sum(min_count=len(source_ids))
            )
            metrics = share_metrics(monthly, horizon)
            if not metrics[f"{prefix}_complete"]:
                raise ValueError(
                    f"Approved reconstruction is incomplete for target {target_bfs_id}"
                )
            selected.at[index, "selected_baseline_observed_origin_months"] = metrics[
                f"{prefix}_observed_origin_months"
            ]
            selected.at[index, "selected_baseline_complete"] = True
            selected.at[index, "selected_foreign_overnights_sum"] = metrics[
                f"{prefix}_foreign_overnights_sum"
            ]
            selected.at[index, "selected_total_overnights_sum"] = metrics[
                f"{prefix}_total_overnights_sum"
            ]
            selected.at[index, "selected_foreign_share"] = metrics[
                f"{prefix}_foreign_share_ratio_of_sums"
            ]
            selected.at[index, "selected_foreign_share_available"] = True
            selected.at[index, "foreign_share_reconstruction_applied"] = True
            selected.at[index, "foreign_share_reconstruction_status"] = (
                "reconstructed_official_same_territory_identifier_continuity"
            )

    selected["foreign_share_missing_handling_selected"] = True
    return selected


def write_report(summary: dict) -> None:
    w12 = summary["baseline_window_audit"]["12"]
    w24 = summary["baseline_window_audit"]["24"]
    w36 = summary["baseline_window_audit"]["36"]
    missing_names = ", ".join(
        item["municipality_name"]
        for item in summary["first_exposed_without_any_24m_foreign_share"]
    )
    unresolved_names = ", ".join(
        item["municipality_name"]
        for item in summary["first_exposed_without_selected_foreign_share_details"]
    )
    lines = [
        "# Spécification COVID et baseline de clientèle - étape 27",
        "",
        "**Statut : option A appliquée. Moutier est reconstruit exactement; trois historiques restent indisponibles sans approximation.**",
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
        "## Reconstruction officielle des historiques",
        "",
        "L'option A a été appliquée en exigeant l'identifiant BFS, la mutation officielle et toutes les composantes territoriales d'une fusion. Une composante absente de la publication contrôlée n'est jamais remplacée par zéro.",
        "",
        "| Commune actuelle | Couverture des composantes historiques | Résultat |",
        "|---|---:|---|",
        "| Moutier (JU) | 1/1 | Série BFS 700 reliée au BFS 6831 par la mutation officielle 3999; part reconstruite |",
        "| Val de Bagnes | 1/2 | Bagnes est dans l'archive HESTA contrôlée, Vollèges ne l'est pas; aucune agrégation partielle |",
        "| Blonay - Saint-Légier | 0/2 | Les deux anciennes communes sont absentes de l'archive HESTA contrôlée |",
        "| Laténa | 0/4 | Les quatre anciennes communes sont absentes de l'archive HESTA contrôlée |",
        "",
        f"Après reconstruction, la part est disponible pour {summary['first_exposed_with_selected_foreign_share']} des 80 premières expositions. Elle reste manquante pour : {unresolved_names}. Les 1 302 lignes sont conservées et aucune valeur n'est imputée.",
        "",
        "Aucune comparaison de cohorte, aucun échantillon et aucun estimateur n'est choisi ici. Le traitement analytique des trois valeurs toujours manquantes devra rester explicite dans la prochaine spécification.",
        "",
        "## Sources",
        "",
        "- Chronologie officielle des décisions COVID du Conseil fédéral : `SWISS_FEDERAL_COUNCIL_COVID_DECISION_CHRONOLOGY`.",
        "- Effondrement de la demande hôtelière 2020 et exposition particulière de la clientèle étrangère : `BFS_HOTEL_DEMAND_COVID_2020`.",
        "- Nuitées domestiques et étrangères mensuelles : panel HESTA déjà enregistré dans le projet.",
        "- Mutations communales officielles : `BFS_MUNICIPAL_MUTATION_3944`, `BFS_MUNICIPAL_MUTATION_3961`, `BFS_MUNICIPAL_MUTATION_3994` et `BFS_MUNICIPAL_MUTATION_3999`.",
        "- Univers communal de l'ancienne publication HESTA contrôlée : `BFS_HESTA_ARCHIVE_2020_METADATA`.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    panel = pd.read_csv(PANEL_PATH, parse_dates=["date"])
    coverage = pd.read_csv(COVERAGE_PATH, parse_dates=["first_exposure_month"])
    reconstruction = pd.read_csv(
        RECONSTRUCTION_PATH,
        dtype={"target_bfs_id": int, "predecessor_bfs_id": int},
    )
    reconstruction["reconstruction_approved"] = (
        reconstruction.reconstruction_approved.astype("string").str.lower().eq("true")
    )
    evidence = {
        source_id: successful_evidence_metadata(source_id)
        for source_id in config["official_source_ids"]
    }
    evidence.update(checked_reconstruction_evidence(reconstruction))
    audit = build_audit(config, panel, coverage)
    selected = build_selected_baseline(config, audit, panel, reconstruction)
    summary = build_summary(config, audit, selected, reconstruction, evidence)

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
    if not selected.foreign_share_missing_handling_selected.all():
        raise ValueError("The approved option-A handling must be recorded on every row")
    if int(selected.foreign_share_reconstruction_applied.sum()) != 7:
        raise ValueError("Expected the Moutier bridge to reconstruct seven cohort rows")

    audit.to_csv(OUTPUT_PATH, index=False, lineterminator="\n")
    selected.to_csv(SELECTED_OUTPUT_PATH, index=False, lineterminator="\n")
    SUMMARY_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
