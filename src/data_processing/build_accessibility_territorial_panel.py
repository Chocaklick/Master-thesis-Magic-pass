"""Apply only the approved, exact Moutier identity bridge; audit at territorial grain."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.causal_inference import build_accessibility_dynamic_event_time_audit as dynamic
from src.causal_inference import audit_accessibility_successive_entries as successive

CONFIG = ROOT / "config/accessibility_outcome_territorial_harmonisation.json"
SOURCE_ID = "DERIVED_ACCESSIBILITY_TERRITORIAL_MOUTIER_BRIDGE"
INPUTS = {
    "panel": ROOT / "data_processed/accessibility_municipality_month_exposure.csv",
    "universe": ROOT / "reports/accessibility_cohort_comparison_universe.csv",
    "foreign_share": ROOT / "reports/accessibility_covid_foreign_share_selected.csv",
    "mutation": ROOT / "config/accessibility_covid_foreign_share_reconstruction.csv",
    **{k: v for k, v in successive.INPUTS.items() if k != "panel"},
}


def identity(config: dict) -> tuple[int, int]:
    if not config["researcher_approved"] or config["imputation_applied"]:
        raise ValueError("Only the approved exact non-imputed bridge is permitted")
    return int(config["predecessor_bfs_id"]), int(config["current_bfs_id"])


def bridge_panel(config: dict, original: pd.DataFrame) -> pd.DataFrame:
    old, new = identity(config)
    frame = original.copy()
    local = frame.loc[frame.municipality_bfs_id.isin([old, new])]
    if local.duplicated(["municipality_bfs_id", "date"]).any():
        raise ValueError("Source municipality-month keys must be unique")
    left = local.loc[local.municipality_bfs_id.eq(old)].set_index("date").sort_index()
    right = local.loc[local.municipality_bfs_id.eq(new)].set_index("date").sort_index()
    exposure_fields = [c for c in frame if c.startswith(("active_", "new_", "nearest_"))]
    pd.testing.assert_frame_equal(left[exposure_fields], right[exposure_fields])
    dates = pd.to_datetime(frame.date)
    before = dates.lt(pd.Timestamp(config["effective_month"]))
    parallel = (frame.municipality_bfs_id.eq(old) & ~before) | (
        frame.municipality_bfs_id.eq(new) & before
    )
    numeric_source_fields = [c for c in frame if (
        c.startswith(("hotel_", "domestic_")) and not c.endswith("_source_token")
    ) or c in {"foreign_overnights", "log_overnights"}]
    if frame.loc[parallel, numeric_source_fields].notna().any().any():
        raise ValueError("A source value exists outside the approved identifier validity dates")
    frame = frame.loc[~parallel].copy()
    frame["source_municipality_bfs_id"] = frame.municipality_bfs_id
    frame["territorial_harmonisation_applied"] = frame.municipality_bfs_id.isin([old, new])
    frame["territorial_source_bfs_ids"] = frame.municipality_bfs_id.astype(str)
    frame.loc[frame.territorial_harmonisation_applied, "territorial_source_bfs_ids"] = f"{old}|{new}"
    frame["territorial_harmonisation_source_id"] = SOURCE_ID
    frame["territorial_mutation_source_id"] = ""
    frame.loc[frame.territorial_harmonisation_applied, "territorial_mutation_source_id"] = config["mutation_source_id"]
    frame.loc[frame.municipality_bfs_id.eq(old), "municipality_bfs_id"] = new
    if frame.duplicated(["municipality_bfs_id", "date"]).any():
        raise ValueError("Harmonised municipality-month keys are not unique")
    if len(frame) != len(original) - len(left):
        raise ValueError("Exactly one parallel empty calendar series must be removed")
    if frame.hotel_overnights.notna().sum() != original.hotel_overnights.notna().sum():
        raise ValueError("Observed overnight count changed")
    return frame.sort_values(["municipality_bfs_id", "date"]).reset_index(drop=True)


def bridge_cohort_table(config: dict, original: pd.DataFrame,
                        agreement_fields: list[str]) -> pd.DataFrame:
    old, new = identity(config)
    left = original.loc[original.municipality_bfs_id.eq(old)].set_index("focal_cohort_month").sort_index()
    right = original.loc[original.municipality_bfs_id.eq(new)].set_index("focal_cohort_month").sort_index()
    pd.testing.assert_frame_equal(left[agreement_fields], right[agreement_fields])
    frame = original.loc[~original.municipality_bfs_id.eq(old)].copy()
    frame["territorial_source_bfs_ids"] = frame.municipality_bfs_id.astype(str)
    frame["territorial_harmonisation_applied"] = frame.municipality_bfs_id.eq(new)
    frame.loc[frame.territorial_harmonisation_applied, "territorial_source_bfs_ids"] = f"{old}|{new}"
    frame["territorial_harmonisation_source_id"] = SOURCE_ID
    frame["territorial_mutation_source_id"] = ""
    frame.loc[frame.territorial_harmonisation_applied, "territorial_mutation_source_id"] = config["mutation_source_id"]
    if frame.duplicated(["municipality_bfs_id", "focal_cohort_month"]).any():
        raise ValueError("Harmonised cohort keys are not unique")
    return frame.sort_values(["focal_cohort_month", "municipality_bfs_id"]).reset_index(drop=True)


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    old, new = identity(config)
    data = {k: pd.read_csv(v) for k, v in INPUTS.items()}
    evidence = data["mutation"].loc[
        data["mutation"].target_bfs_id.eq(new)
        & data["mutation"].predecessor_bfs_id.eq(old)
    ]
    if len(evidence) != 1 or evidence.iloc[0].mutation_source_id != config["mutation_source_id"] or evidence.iloc[0].mutation_effective_date != config["effective_month"]:
        raise ValueError("Configuration must match the already registered official mutation")
    panel = bridge_panel(config, data["panel"])
    role_fields = [c for c in data["universe"] if c not in {"municipality_bfs_id", "municipality_name"}]
    role_fields.remove("focal_cohort_month")
    universe = bridge_cohort_table(config, data["universe"], role_fields)
    foreign_fields = [c for c in data["foreign_share"] if c.startswith("selected_")]
    foreign = bridge_cohort_table(config, data["foreign_share"], foreign_fields)
    temporal_config = json.loads(dynamic.CONFIG_PATH.read_text(encoding="utf-8"))
    frame = dynamic.build_month_frame(temporal_config, universe, panel)
    cohort_support = dynamic.build_cohort_month_support(temporal_config, frame)
    event_support = dynamic.build_event_month_support(temporal_config, cohort_support)
    temporal = dynamic.build_summary(temporal_config, universe, panel, frame, cohort_support, event_support)
    temporal["administrative_id_harmonisation_applied"] = True
    temporal.pop("input_sha256")  # These originals are not the territorial inputs; outer hashes are exact.
    temporal["source_id"] = SOURCE_ID
    groups = data["groups"]
    groups["first_effective_month"] = pd.to_datetime(groups.first_effective_month)
    observed_panel = panel.copy()
    observed_panel["date"] = pd.to_datetime(observed_panel.date)
    observed_panel = observed_panel.loc[observed_panel.date.le(observed_panel.loc[observed_panel.hotel_overnights.notna(), "date"].max())]
    timeline = successive.build_group_timeline(groups, data["events"], data["history"], observed_panel.date)
    journeys = data["journeys"]
    # Keep the current journey row only after checking both source IDs have identical access.
    access_fields = [c for c in journeys if c.endswith("minutes") or c.endswith("usable") or "stop_id" in c]
    left = journeys.loc[journeys.municipality_bfs_id.eq(old)].set_index("station_group_id").sort_index()
    right = journeys.loc[journeys.municipality_bfs_id.eq(new)].set_index("station_group_id").sort_index()
    pd.testing.assert_frame_equal(left[access_fields], right[access_fields])
    qualified = journeys.loc[
        ~journeys.municipality_bfs_id.eq(old)
        & successive.as_bool(journeys.descriptive_accessibility_usable)
        & successive.as_bool(journeys.within_120_minutes)
    ].merge(groups[["station_group_id", "first_effective_month"]], on="station_group_id", validate="many_to_one")
    entries = successive.audit_events(qualified, observed_panel)
    group_audit, design = successive.audit_design(
        json.loads(successive.CONFIG.read_text(encoding="utf-8")), groups, qualified, timeline, observed_panel
    )
    first = entries.entry_type.eq("first_exposure")
    treated = dynamic.bool_series(universe.treated_in_focal_cohort)
    summary = {
        "specification_version": config["specification_version"],
        "source_id": SOURCE_ID,
        "official_mutation_source_id": config["mutation_source_id"],
        "administrative_id_harmonisation_applied": True,
        "original_administrative_series": int(data["panel"].municipality_bfs_id.nunique()),
        "analytical_territories": int(panel.municipality_bfs_id.nunique()),
        "panel_rows": len(panel), "comparison_cohort_rows": len(universe),
        "observed_outcome_rows_before": int(data["panel"].hotel_overnights.notna().sum()),
        "observed_outcome_rows_after": int(panel.hotel_overnights.notna().sum()),
        "moutier_observed_months": int(panel.loc[panel.municipality_bfs_id.eq(new)].hotel_overnights.notna().sum()),
        "exposed_territories_with_foreign_share": int((treated & dynamic.bool_series(universe.selected_foreign_share_available)).sum()),
        "distinct_territorial_entry_months": len(entries),
        "first_exposure_entry_months": int(first.sum()),
        "additional_entry_months": int((~first).sum()),
        "territories_with_additional_entries": int(entries.loc[~first].municipality_bfs_id.nunique()),
        "additional_entries_with_multiple_groups": int(entries.loc[~first].multiple_groups_entering_same_month.sum()),
        "additional_entries_with_observed_pre_and_post_segment": int((~first & entries.observed_pre_months_since_previous_entry.gt(0) & entries.observed_post_months_before_next_entry.gt(0)).sum()),
        "station_groups_retained": len(group_audit),
        "observed_design": design, "temporal_support": temporal,
        "imputation_applied": False, "analysis_sample_selected": False,
        "estimator_selected": False, "causal_estimation_approved": False,
        "input_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in [CONFIG, dynamic.CONFIG_PATH, successive.CONFIG, *INPUTS.values()]},
        "outputs": {k: config[k] for k in ["analytical_panel", "comparison_universe", "selected_foreign_share"]},
    }
    if summary["analytical_territories"] != 185 or temporal["treated_municipalities"] != 79 or temporal["constant_step_sensitivity_support"]["treated_observation_rows"] != 5580:
        raise ValueError("Territorial support does not reconcile with the approved exact bridge")
    for table, key in [(panel, "analytical_panel"), (universe, "comparison_universe"), (foreign, "selected_foreign_share")]:
        table.to_csv(ROOT / config[key], index=False, lineterminator="\n")
    (ROOT / "reports/accessibility_territorial_harmonisation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    missing = ", ".join(row["municipality_name"] for row in temporal["treated_municipalities_without_observed_pre_support"])
    (ROOT / "reports/78_RACCORDEMENT_TERRITORIAL_MOUTIER_FR.md").write_text("\n".join([
        "# Raccordement territorial de Moutier — étape 29b", "",
        "## Décision et méthode", "",
        "Raccordement explicitement validé par le chercheur : BFS 700 avant janvier 2026, BFS 6831 à partir de janvier 2026, pour le même territoire. La mutation officielle déjà archivée est `BFS_MUNICIPAL_MUTATION_3999`. Il ne s'agit ni d'une fusion à reconstituer ni d'une imputation.", "",
        "Le panel dérivé utilise 6831 comme identifiant analytique. `source_municipality_bfs_id` conserve l'identifiant réellement fourni chaque mois ; `municipality_name_source`, les valeurs, jetons et identifiants de sources HESTA restent ceux de la ligne originale. Les lignes parallèles retirées ne contenaient aucune valeur numérique d'issue ou de capacité. Toutes les autres communes restent inchangées.", "",
        "Les calendriers d'exposition et l'accessibilité des deux identifiants sont vérifiés identiques. Les rôles de comparaison et valeurs de clientèle étrangère sont également réconciliés : une seule ligne territoriale est conservée par cohorte. Les sorties administratives antérieures ne sont pas écrasées ; elles documentent la provenance, mais ne constituent plus le grain prévu pour l'estimation élargie.", "",
        "## Bilan après raccordement", "",
        "| Indicateur | Résultat |", "|---|---:|",
        f"| Territoires dans le panel | {summary['analytical_territories']} (au lieu de 186 identifiants) |",
        f"| Communes exposées | {temporal['treated_municipalities']} (au lieu de 80 séries) |",
        f"| Lignes commune-mois | {len(panel):,} |".replace(",", " "),
        f"| Nuitées mensuelles observées | {summary['observed_outcome_rows_after']:,} — aucune perte |".replace(",", " "),
        f"| Mois observés pour Moutier | {summary['moutier_observed_months']} |",
        "| Observations postérieures exposées conservées | 5 580 |",
        f"| Communes avec observations avant et après | {temporal['treated_municipalities_with_observed_pre_and_post_support']}/79 |",
        f"| Communes avec ajouts successifs | {summary['territories_with_additional_entries']} |",
        f"| Entrées territoire-mois | {len(entries)} : 79 premières + {summary['additional_entry_months']} ajouts |",
        f"| Part étrangère disponible pour l'interaction | {summary['exposed_territories_with_foreign_share']}/79 |", "",
        "Les fenêtres complètes de 6+6, 12+12 et 24+24 mois restent disponibles pour 76, 73 et 65 communes. Le raccordement ne crée aucune nouvelle nuitée et ne modifie pas les contrôles jamais exposés ou pas encore exposés. Il corrige uniquement le double identifiant et rend l'historique de Moutier exploitable dans une seule unité.", "",
        f"Les trois historiques préexposition encore incomplets sont : {missing}. Ces communes restent recensées ; aucune exclusion ou approximation supplémentaire n'est décidée.", "",
        f"Le diagnostic territorial est recalculé : {design['group_columns_with_current_access']} colonnes d'exposition accessibles, rang {design['two_way_fixed_effect_rank']}, quatre paires identiques. Les 71 groupes et la sortie documentée de Crans-Montana sont préservés. Le rang reste un diagnostic algébrique, pas une preuve causale.", "",
        "## Fichiers et reprise", "",
        "- [Panel territorial](../data_processed/accessibility_municipality_month_exposure_territorial.csv).",
        "- [Rôles de comparaison territoriaux](accessibility_cohort_comparison_universe_territorial.csv).",
        "- [Baseline de clientèle étrangère territoriale](accessibility_covid_foreign_share_selected_territorial.csv).",
        "- `accessibility_territorial_harmonisation_summary.json` : support temporel, diagnostic des ajouts, rang et empreintes des entrées.",
        "- `config/accessibility_outcome_territorial_harmonisation.json` : décision, dates, sources et chemins canoniques.", "",
        "Reproduction : `.venv/Scripts/python.exe src/data_processing/build_accessibility_territorial_panel.py` depuis la racine. Les rapports 76–77 restent des audits par identifiant source ; ce rapport précise le bilan territorial à utiliser ensuite. Aucun nouvel accès externe n'a été nécessaire.", "",
        "Prochain point à valider avant estimation : diagnostics de comparabilité et spécification de l'estimateur. Aucun filtre de communes, effet additionnel ou effet causal n'est choisi ici.", "",
    ]), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in {"input_sha256", "observed_design", "temporal_support"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
