"""Audit successive accessible entries while retaining the approved network path.

Reuse station groups, current access and the existing first-entry/documented-exit
timeline. Rank calculations diagnose linear dependence only; no treatment effect
or causal estimator is fitted and no municipalities or station groups are removed.
"""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.build_accessibility_municipality_exposure import (  # noqa: E402
    build_group_timeline,
)

CONFIG = ROOT / "config/accessibility_successive_entries.json"
INPUTS = {
    "groups": ROOT / "data_processed/accessibility_station_groups.csv",
    "events": ROOT / "data_processed/accessibility_station_group_events.csv",
    "journeys": ROOT / "data_processed/accessibility_station_group_journey_context.csv",
    "history": ROOT / "data_processed/magic_pass_membership_history.csv",
    "panel": ROOT / "data_processed/accessibility_municipality_month_exposure.csv",
}
EVENT_OUTPUT = ROOT / "reports/accessibility_successive_entry_events.csv"
GROUP_OUTPUT = ROOT / "reports/accessibility_successive_entry_group_separability.csv"
SUMMARY_OUTPUT = ROOT / "reports/accessibility_successive_entry_summary.json"
REPORT_OUTPUT = ROOT / "reports/77_ENTREES_SUCCESSIVES_TRAJECTOIRE_RESEAU_FR.md"
SOURCE_ID = "DERIVED_ACCESSIBILITY_SUCCESSIVE_ENTRY_AUDIT"


def as_bool(values: pd.Series) -> pd.Series:
    return values.astype(str).str.lower().eq("true")


def pipe(values) -> str:
    return "|".join(sorted(set(str(v) for v in values)))


def month_gap(later: pd.Timestamp, earlier: pd.Timestamp) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month


def residualize(matrix: np.ndarray, unit: np.ndarray, month: np.ndarray,
                tolerance: float, maximum: int) -> tuple[np.ndarray, int]:
    """Exact two-way projection to numerical tolerance on an unbalanced grid."""
    result = pd.DataFrame(matrix, dtype=float)
    for iteration in range(1, maximum + 1):
        previous = result.to_numpy(copy=True)
        result -= result.groupby(unit).transform("mean")
        result -= result.groupby(month).transform("mean")
        if np.max(np.abs(result.to_numpy() - previous)) < tolerance:
            return result.to_numpy(), iteration
    raise ValueError("Two-way projection did not converge; no rank reported")


def audit_design(config: dict, groups: pd.DataFrame, qualified: pd.DataFrame,
                 timeline: pd.DataFrame, panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    catchments = {
        gid: set(rows.municipality_bfs_id.astype(int))
        for gid, rows in qualified.groupby("station_group_id")
    }
    ids = sorted(catchments)
    all_rows = panel.sort_values(["municipality_bfs_id", "date"]).reset_index(drop=True)
    membership = timeline.pivot(
        index="date", columns="station_group_id", values="assumed_active_base_membership"
    )
    exposure = np.column_stack([
        np.isin(all_rows.municipality_bfs_id, list(catchments[gid]))
        & all_rows.date.map(membership[gid]).to_numpy(dtype=bool)
        for gid in ids
    ])
    if not np.array_equal(
        exposure.sum(axis=1), all_rows.active_station_group_count_120min.to_numpy()
    ):
        raise ValueError("Reconstructed group exposure does not match the existing panel")
    observed = all_rows.hotel_overnights.notna()
    matrix = exposure[observed].astype(float)
    observed_panel = all_rows.loc[observed]
    residual, iterations = residualize(
        matrix, observed_panel.municipality_bfs_id.to_numpy(),
        observed_panel.date.to_numpy(), config["projection_numerical_tolerance"],
        config["projection_maximum_iterations"],
    )
    singular = np.linalg.svd(residual, compute_uv=False)
    rank_tolerance = float(singular[0] * max(residual.shape) * np.finfo(float).eps)
    rank = int((singular > rank_tolerance).sum())
    identical = {gid: [] for gid in ids}
    exact_pairs = []
    names = groups.set_index("station_group_id").station_group_name.to_dict()
    for left, right in combinations(range(len(ids)), 2):
        if np.array_equal(matrix[:, left], matrix[:, right]):
            identical[ids[left]].append(ids[right])
            identical[ids[right]].append(ids[left])
            exact_pairs.append({
                "station_group_id_left": ids[left],
                "station_group_id_right": ids[right],
                "station_group_name_left": names[ids[left]],
                "station_group_name_right": names[ids[right]],
            })
    first_by_municipality = qualified.groupby(
        "municipality_bfs_id"
    ).first_effective_month.min()
    rows = []
    for group in groups.itertuples(index=False):
        gid = group.station_group_id
        local = qualified.loc[qualified.station_group_id.eq(gid)]
        first = local.municipality_bfs_id.map(first_by_municipality)
        rows.append({
            "station_group_id": gid,
            "station_group_name": group.station_group_name,
            "first_effective_month": group.first_effective_month.strftime("%Y-%m-%d"),
            "accessible_municipalities_120min": len(local),
            "accessible_current_territories_120min": int(local.boundary_bfs_id_2026.nunique()),
            "first_exposure_municipalities": int(first.eq(group.first_effective_month).sum()),
            "additional_entry_municipalities": int(first.lt(group.first_effective_month).sum()),
            "observed_exposure_rows": int(matrix[:, ids.index(gid)].sum()) if gid in ids else 0,
            "identical_observed_exposure_group_ids": pipe(identical.get(gid, [])),
            "has_identical_observed_exposure_column": bool(identical.get(gid, [])),
            "primary_network_trajectory_rule_selected": True,
            "additional_effect_estimator_selected": False,
            "causal_estimation_approved": False,
            "source_id": SOURCE_ID,
        })
    return pd.DataFrame(rows), {
        "observed_outcome_rows": int(observed.sum()),
        "group_columns_with_current_access": len(ids),
        "two_way_fixed_effect_rank": rank,
        "rank_deficiency": len(ids) - rank,
        "rank_numerical_tolerance": rank_tolerance,
        "projection_iterations": iterations,
        "projection_numerical_tolerance": config["projection_numerical_tolerance"],
        "condition_number_nonzero_space": float(singular[0] / singular[rank-1]),
        "exact_identical_observed_exposure_pairs": exact_pairs,
        "documented_exits_preserved": timeline.loc[
            timeline.last_active_month.notna(),
            ["station_group_id", "last_active_month"],
        ].drop_duplicates().assign(
            last_active_month=lambda x: x.last_active_month.dt.strftime("%Y-%m-%d")
        ).to_dict(orient="records"),
        "interpretation": "Linear rank support only; not a causal-identification test or an estimator selection",
    }


def audit_events(qualified: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    entries = qualified.groupby(
        ["municipality_bfs_id", "first_effective_month"], as_index=False
    ).agg(
        municipality_name=("municipality_name", "first"),
        boundary_bfs_id_2026=("boundary_bfs_id_2026", "first"),
        entering_station_group_ids=("station_group_id", pipe),
        entering_station_group_names=("station_group_name", pipe),
        entering_station_group_count=("station_group_id", "nunique"),
    )
    rows = []
    for bfs_id, events in entries.groupby("municipality_bfs_id", sort=True):
        events = events.sort_values("first_effective_month").reset_index(drop=True)
        local = panel.loc[panel.municipality_bfs_id.eq(bfs_id)].sort_values("date")
        for index, event in events.iterrows():
            anchor = event.first_effective_month
            previous = events.iloc[index-1].first_effective_month if index else pd.NaT
            following = events.iloc[index+1].first_effective_month if index+1 < len(events) else pd.NaT
            at_entry = local.loc[local.date.eq(anchor)]
            if len(at_entry) != 1:
                raise ValueError("Expected one panel row at each accessible entry month")
            current = at_entry.iloc[0]
            if int(current.new_station_group_entry_count_120min) != event.entering_station_group_count:
                raise ValueError("Entry group count differs from existing municipality exposure")
            post = local.date.ge(anchor) & local.hotel_overnights.notna()
            next_segment = post & (local.date.lt(following) if pd.notna(following) else True)
            pre = local.date.lt(anchor) & local.hotel_overnights.notna()
            previous_segment = pre & (local.date.ge(previous) if pd.notna(previous) else True)
            rows.append({
                "municipality_entry_id": f"ACCESS_ENTRY__{int(bfs_id)}__{anchor.strftime('%Y%m')}",
                "municipality_bfs_id": int(bfs_id),
                "municipality_name": event.municipality_name,
                "boundary_bfs_id_2026": int(event.boundary_bfs_id_2026),
                "entry_month": anchor.strftime("%Y-%m-%d"),
                "entry_order": index+1,
                "entry_type": "first_exposure" if index == 0 else "additional_entry",
                "entering_station_group_ids": event.entering_station_group_ids,
                "entering_station_group_names": event.entering_station_group_names,
                "entering_station_group_count": int(event.entering_station_group_count),
                "multiple_groups_entering_same_month": event.entering_station_group_count > 1,
                "previous_entry_month": previous.strftime("%Y-%m-%d") if pd.notna(previous) else "",
                "next_entry_month": following.strftime("%Y-%m-%d") if pd.notna(following) else "",
                "months_since_previous_entry": month_gap(anchor, previous) if pd.notna(previous) else None,
                "months_until_next_entry": month_gap(following, anchor) if pd.notna(following) else None,
                "observed_pre_months_since_previous_entry": int(previous_segment.sum()),
                "observed_post_months_before_next_entry": int(next_segment.sum()),
                "observed_post_months_all_available": int(post.sum()),
                "hotel_overnights_at_entry": current.hotel_overnights,
                "active_station_group_count_120min": int(current.active_station_group_count_120min),
                "active_ski_area_km_known_sum_120min": current.active_ski_area_km_known_sum_120min,
                "active_lifts_known_sum_120min": current.active_lifts_known_sum_120min,
                "active_groups_missing_structure_count_120min": int(current.active_groups_missing_structure_count_120min),
                "primary_network_trajectory_rule_selected": True,
                "additional_effect_estimator_selected": False,
                "analysis_sample_selected": False,
                "causal_estimation_approved": False,
                "source_id": SOURCE_ID,
            })
    return pd.DataFrame(rows)


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not config["primary_successive_entry_rule_selected"]:
        raise ValueError("Researcher approval for the network trajectory is required")
    data = {name: pd.read_csv(path) for name, path in INPUTS.items()}
    panel = data["panel"]
    panel["date"] = pd.to_datetime(panel.date)
    latest = panel.loc[panel.hotel_overnights.notna(), "date"].max()
    panel = panel.loc[panel.date.le(latest)].copy()
    groups = data["groups"]
    groups["first_effective_month"] = pd.to_datetime(groups.first_effective_month)
    timeline = build_group_timeline(groups, data["events"], data["history"], panel.date)
    journeys = data["journeys"]
    qualified = journeys.loc[
        as_bool(journeys.descriptive_accessibility_usable)
        & as_bool(journeys.within_120_minutes)
    ].merge(groups[["station_group_id", "first_effective_month"]],
            on="station_group_id", validate="many_to_one")
    events = audit_events(qualified, panel)
    group_audit, design = audit_design(config, groups, qualified, timeline, panel)
    first = events.entry_type.eq("first_exposure")
    summary = {
        "specification_version": config["specification_version"],
        "primary_target": config["researcher_approved_primary_target"],
        "municipality_entry_months": len(events),
        "first_exposure_entry_months": int(first.sum()),
        "additional_entry_months": int((~first).sum()),
        "municipalities_with_additional_entries": int(events.loc[~first].municipality_bfs_id.nunique()),
        "current_territories_exposed": int(events.boundary_bfs_id_2026.nunique()),
        "current_territories_with_additional_entries": int(events.loc[~first].boundary_bfs_id_2026.nunique()),
        "distinct_current_territory_entry_months": int(len(events[["boundary_bfs_id_2026", "entry_month"]].drop_duplicates())),
        "administrative_id_harmonisation_applied": False,
        "additional_entries_with_multiple_groups": int(events.loc[~first].multiple_groups_entering_same_month.sum()),
        "additional_entries_with_observed_pre_and_post_segment": int((
            ~first & events.observed_pre_months_since_previous_entry.gt(0)
            & events.observed_post_months_before_next_entry.gt(0)
        ).sum()),
        "entry_month_group_count_distribution": {str(k): int(v) for k, v in events.entering_station_group_count.value_counts().sort_index().items()},
        "station_groups_retained": len(group_audit),
        "station_groups_without_current_120min_pair": int(group_audit.accessible_municipalities_120min.eq(0).sum()),
        "observed_design": design,
        "primary_network_trajectory_rule_selected": True,
        "additional_effect_estimator_selected": False,
        "analysis_sample_selected": False,
        "causal_estimation_approved": False,
        "input_sha256": {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in [CONFIG, *INPUTS.values()]},
        "source_id": SOURCE_ID,
    }
    if len(events) != 177 or int(first.sum()) != 80:
        raise ValueError("Entry sequence must reconcile to 177 months and 80 first exposures")
    events.to_csv(EVENT_OUTPUT, index=False, lineterminator="\n")
    group_audit.to_csv(GROUP_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    pairs = design["exact_identical_observed_exposure_pairs"]
    pair_labels = "; ".join(f"{p['station_group_name_left']} / {p['station_group_name_right']}" for p in pairs)
    REPORT_OUTPUT.write_text("\n".join([
        "# Entrées successives et trajectoire du réseau - étape 29", "",
        "Cet audit conserve les identifiants administratifs sources. Le raccordement territorial de Moutier, validé ensuite, est appliqué dans un panel séparé au [rapport 78](78_RACCORDEMENT_TERRITORIAL_MOUTIER_FR.md) : ses comptes territoriaux et son diagnostic recalculé sont à utiliser avant estimation.", "",
        "## Décision appliquée", "",
        "L'analyse principale conserve tous les mois observés après la première exposition, y compris après une nouvelle entrée accessible. Elle cible la trajectoire d'exposition au réseau depuis cette première entrée. L'effet propre de chaque ajout fait l'objet d'un diagnostic séparé avant de choisir une estimation.", "",
        "## Ce que les données permettent d'examiner", "",
        f"Les 80 séries communales exposées représentent {summary['current_territories_exposed']} territoires actuels : les identifiants Moutier BE (700) et Moutier JU (6831) correspondent au même territoire. Les séries recensent {len(events)} événements commune-mois : 80 premières expositions et {summary['additional_entry_months']} ajouts dans {summary['municipalities_with_additional_entries']} séries, soit {summary['current_territories_with_additional_entries']} territoires. En dédupliquant uniquement pour compter les territoires, on obtient {summary['distinct_current_territory_entry_months']} dates territoire-mois, dont 96 ajouts. Aucun raccordement analytique n'est encore appliqué.", "",
        f"Parmi les 97 ajouts recensés par identifiant, {summary['additional_entries_with_multiple_groups']} font entrer plusieurs groupes simultanément. {summary['additional_entries_with_observed_pre_and_post_segment']} disposent d'au moins une nuitée observée entre l'entrée précédente et cet ajout, puis entre cet ajout et l'entrée suivante. Cette disponibilité ne garantit pas la comparabilité.", "",
        "Le tableau des événements conserve les groupes entrant ensemble, les délais entre entrées et les données cumulées déjà présentes : nombre de groupes actifs, kilomètres de pistes et remontées connus. Les structures manquantes restent signalées. Les sommes connues peuvent être partielles.", "",
        "## Peut-on séparer les groupes ?", "",
        f"Les 71 groupes restent recensés. {design['group_columns_with_current_access']} ont au moins une commune accessible à 120 minutes ; {summary['station_groups_without_current_120min_pair']} n'en ont aucune dans cette matrice. Sur les {design['observed_outcome_rows']} lignes où les nuitées sont observées, les {design['group_columns_with_current_access']} colonnes d'exposition ont un rang de {design['two_way_fixed_effect_rank']} après retrait des effets fixes commune et mois. Le déficit est de {design['rank_deficiency']} dimensions.", "",
        f"Colonnes d'exposition exactement identiques sur les observations disponibles : {pair_labels or 'aucune'}. Ces contributions ne peuvent pas être estimées séparément dans cette définition. Les identifiants originaux restent distincts et aucun regroupement supplémentaire n'est appliqué.", "",
        "Une colonne distincte ou un rang suffisant indique seulement une variation algébrique. Cela ne valide ni les tendances avant entrée, ni l'absence de choc concomitant, ni l'interprétation causale d'un effet additionnel. La projection du calendrier de transport actuel sur le passé et les changements de territoire restent des limites.", "",
        "Le rang de cet audit décrit le panel par identifiants sources. Moutier ne constitue pas deux communes indépendantes : l'ancien identifiant contient 154 mois observés jusqu'en décembre 2025 et le nouveau trois mois de janvier à mars 2026. Le raccordement exact validé et le diagnostic territorial recalculé figurent au rapport 78 ; les données sources de cet audit restent intactes.", "",
        "## Méthode et reprise", "",
        "Le calendrier de groupe réutilise la première entrée et la sortie documentée de Crans-Montana. L'hypothèse de continuité des autres adhésions reste celle du projet. Les changements internes de composantes d'un groupe ne deviennent pas automatiquement de nouvelles entrées de groupe.", "",
        "Le rang est calculé sur toutes les lignes de nuitées observées disponibles, sans seuil de durée avant/après et sans exclusion COVID. Une projection alternée retire exactement, à la tolérance numérique de 1e-12, les moyennes par commune et mois dans le panel non équilibré. Le seuil de rang est celui de NumPy : valeur singulière maximale × plus grande dimension × précision machine. Ce calcul est un diagnostic de dépendance, pas une régression estimant un effet.", "",
        "Prochaine décision : choisir les diagnostics de comparabilité et l'estimateur pour la trajectoire principale ; définir ensuite la spécification des effets additionnels en tenant compte des groupes indissociables. Après le raccordement de Moutier au rapport 78, trois historiques préexposition restent incomplets. Aucun échantillon final ou effet causal n'est validé à ce stade.", "",
        "## Sources et fichiers", "",
        "- `data_processed/accessibility_station_groups.csv`, `accessibility_station_group_events.csv` et `magic_pass_membership_history.csv` : identifiants, entrées, regroupements existants et sortie documentée.",
        "- `data_processed/accessibility_station_group_journey_context.csv` : accès actuel et règle descriptive de qualité déjà appliquée.",
        "- `data_processed/accessibility_municipality_month_exposure.csv` : nuitées HESTA, expositions et structures cumulées ; reconciliation intégrale des comptes de groupes.",
        "- `reports/accessibility_successive_entry_events.csv` : un événement commune-mois par ligne.",
        "- `reports/accessibility_successive_entry_group_separability.csv` : les 71 groupes et les dépendances exactes observées.",
        "- `reports/accessibility_successive_entry_summary.json` : effectifs, paramètres numériques, sortie documentée et empreintes SHA-256 des entrées. Aucun téléchargement supplémentaire.", "",
    ]), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
