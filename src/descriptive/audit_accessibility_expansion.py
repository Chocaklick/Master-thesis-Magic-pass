"""Offline stage-1 inventory; does not alter the established analytical panel."""

from pathlib import Path
import hashlib
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "reports"
INPUT_HASHES = {}


def read(relative):
    path = ROOT / relative
    INPUT_HASHES[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def split_ids(series):
    return {part for value in series for part in value.split("|") if part}


def main():
    history = read("data_processed/magic_pass_membership_history.csv")
    units = read("data_processed/treatment_destination_units.csv")
    links = read("data_processed/treatment_destination_municipality.csv")
    review = read("reports/unmatched_magic_entry_review.csv")
    points = read("data_processed/resort_point_municipality.csv")
    hotel = read("data_processed/hotel_municipality_month_enriched.csv")
    distance = read("data_processed/treatment_municipality_distance_exposure.csv")
    nodes = read("reports/public_transport_journey_nodes.csv")
    base = history.loc[history.event_type.eq("base_pass_entry")].copy()
    linked = base.loc[base.candidate_resort_id.ne("")].copy()
    eligible = units.eligible_for_reviewed_outcome_panel.str.lower().eq("true")
    old_stations = split_ids(units.loc[eligible, "component_resort_ids"])
    old_municipalities = set(links.loc[
        links.eligible_for_reviewed_outcome_panel.str.lower().eq("true"),
        "municipality_bfs_id",
    ])
    assert linked.candidate_resort_id.is_unique
    assert old_stations <= set(linked.candidate_resort_id)
    linked = linked.merge(points[["resort_id", "selection_status"]],
                          left_on="candidate_resort_id", right_on="resort_id",
                          validate="one_to_one")
    assert linked.selection_status.str.startswith("unique_current_").all()
    linked["inventory_status"] = "reopened_incomplete_destination_scope"
    linked.loc[linked.bfs_hotel_universe.str.lower().eq("false"), "inventory_status"] = (
        "added_without_point_municipality_hotel_requirement")
    linked.loc[linked.candidate_resort_id.isin(old_stations), "inventory_status"] = (
        "already_in_reviewed_panel")
    linked["additional_to_old_panel"] = ~linked.candidate_resort_id.isin(old_stations)
    arrival_ids = set(nodes.loc[nodes.node_role.eq("destination_component_arrival"),
                               "component_resort_id"])
    linked["existing_journey_arrival_node"] = linked.candidate_resort_id.isin(arrival_ids)
    linked["new_accessibility_exposure_validated"] = False
    station_columns = ["event_id", "source_id", "source_resort_name", "entry_season",
                       "candidate_resort_id", "resort_name_canonical", "cluster_id",
                       "entity_resolution_method", "point_municipality_bfs_id",
                       "point_municipality_name", "bfs_hotel_universe", "inventory_status",
                       "additional_to_old_panel", "existing_journey_arrival_node",
                       "new_accessibility_exposure_validated"]
    linked[station_columns].sort_values("candidate_resort_id").to_csv(
        REPORTS / "accessibility_expansion_station_inventory.csv", index=False)

    excluded = review.review_class.eq("foreign_outside_swiss_listing_universe")
    pending = review.loc[~excluded].copy()
    pending["inventory_status"] = "pending_identity_or_scope_review"
    pending["scope_rule"] = "Swiss destination or Swiss component only"
    pending["integrated_as_station"] = False
    pending.sort_values("event_id").to_csv(
        REPORTS / "accessibility_expansion_pending_events.csv", index=False)
    assert set(base.loc[base.candidate_resort_id.eq(""), "event_id"]) == set(review.event_id)

    hotel["nights_numeric"] = pd.to_numeric(hotel.hotel_overnights, errors="coerce")
    hotel["observed_date"] = hotel.date.where(hotel.nights_numeric.notna(), "")
    municipalities = hotel.groupby(["municipality_bfs_id", "municipality_name_source"]).agg(
        observed_hotel_months=("nights_numeric", "count"),
        first_observed_month=("observed_date", lambda s: min(x for x in s if x)),
        last_observed_month=("observed_date", "max"),
    ).reset_index()
    assert municipalities.municipality_bfs_id.is_unique
    bridge = distance[["municipality_bfs_id", "boundary_bfs_id_2026"]].drop_duplicates()
    assert bridge.municipality_bfs_id.is_unique
    municipalities = municipalities.merge(bridge, validate="one_to_one", how="left")
    assert municipalities.boundary_bfs_id_2026.notna().all()
    municipalities["already_in_reviewed_outcome_scope"] = (
        municipalities.municipality_bfs_id.isin(old_municipalities))
    municipalities["additional_to_reviewed_outcome_scope"] = (
        ~municipalities.already_in_reviewed_outcome_scope)
    municipalities["existing_journey_origin"] = municipalities.municipality_bfs_id.isin(
        nodes.loc[nodes.node_role.eq("municipality_origin"), "municipality_bfs_id"])
    municipalities["shared_current_territory"] = municipalities.boundary_bfs_id_2026.duplicated(False)
    municipalities["inventory_status"] = "existing_hotel_series_for_accessibility_screen"
    municipalities.sort_values("municipality_bfs_id").to_csv(
        REPORTS / "accessibility_expansion_municipality_inventory.csv", index=False)
    old_territories = set(municipalities.loc[
        municipalities.already_in_reviewed_outcome_scope, "boundary_bfs_id_2026"])
    related = split_ids(pending.related_resort_ids)
    counts = {
        "base_entry_events": len(base),
        "foreign_events_excluded": int(excluded.sum()),
        "events_retained_for_review": len(linked) + len(pending),
        "old_destination_units": int(eligible.sum()),
        "old_component_listings": len(old_stations),
        "linked_station_listings_in_inventory": len(linked),
        "additional_station_listings": int(linked.additional_to_old_panel.sum()),
        "added_without_point_hotel_requirement": int(linked.inventory_status.eq(
            "added_without_point_municipality_hotel_requirement").sum()),
        "reopened_incomplete_destination_scope": int(linked.inventory_status.eq(
            "reopened_incomplete_destination_scope").sum()),
        "pending_swiss_or_swiss_component_events": len(pending),
        "pending_directory_gap_events": int(pending.review_class.str.contains(
            "missing_from_directory").sum()),
        "pending_additional_related_listings_not_identity_matches": len(
            related - set(linked.candidate_resort_id)),
        "old_outcome_municipality_series": len(old_municipalities),
        "available_municipality_series": len(municipalities),
        "additional_series_vs_old_outcome_scope": int(
            municipalities.additional_to_reviewed_outcome_scope.sum()),
        "current_territories": municipalities.boundary_bfs_id_2026.nunique(),
        "additional_current_territories_vs_old_outcome_scope": len(
            set(municipalities.boundary_bfs_id_2026) - old_territories),
        "newly_collected_hotel_series": 0,
        "additional_origins_vs_existing_journey_universe": int(
            (~municipalities.existing_journey_origin).sum()),
        "newly_validated_accessibility_pairs": 0,
        "newly_approved_causal_units": 0,
    }
    assert len(base) == len(linked) + len(pending) + int(excluded.sum())
    assert counts["additional_station_listings"] == (
        counts["added_without_point_hotel_requirement"] + counts["reopened_incomplete_destination_scope"])
    # The prose below is a dated checkpoint. Require review if its baseline changes.
    expected = {
        "base_entry_events": 88, "foreign_events_excluded": 10,
        "old_destination_units": 11, "old_component_listings": 15,
        "linked_station_listings_in_inventory": 62, "additional_station_listings": 47,
        "added_without_point_hotel_requirement": 44, "reopened_incomplete_destination_scope": 3,
        "pending_swiss_or_swiss_component_events": 16, "pending_directory_gap_events": 4,
        "pending_additional_related_listings_not_identity_matches": 6,
        "old_outcome_municipality_series": 12, "available_municipality_series": 186,
        "current_territories": 185, "additional_origins_vs_existing_journey_universe": 0,
    }
    for name, value in expected.items():
        assert counts[name] == value, f"Review dated inventory: {name} changed"
    summary = {"audit_date": "2026-10-02", "stage": "1_inventory_only",
               "counts": counts, "input_sha256": INPUT_HASHES,
               "next_step_requires_report_to_user_first": True}
    (REPORTS / "accessibility_expansion_inventory_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    short = municipalities.loc[municipalities.observed_hotel_months.lt(24)]
    short_text = "; ".join(f"{r.municipality_name_source} ({r.municipality_bfs_id}) : "
                           f"{r.observed_hotel_months} mois" for r in short.itertuples())
    text = f"""# Bilan de la première étape d'élargissement

Inventaire local du 2 octobre 2026, conformément au [plan](53_PLAN_ELARGISSEMENT_COMMUNES_STATIONS_FR.md). Aucun nouveau trajet, regroupement de stations ou modèle n'a été calculé.

## Comptage comparable

| Unité comptée | Ancien périmètre | Inventaire élargi | Ajout |
|---|---:|---:|---:|
| Fiches de stations ayant une entrée Magic Pass directement identifiée | {counts['old_component_listings']} composantes des {counts['old_destination_units']} destinations du panel | {counts['linked_station_listings_in_inventory']} | +{counts['additional_station_listings']} |
| Séries communales hôtelières, comparées au périmètre des résultats des 11 destinations | {counts['old_outcome_municipality_series']} | {counts['available_municipality_series']} | +{counts['additional_series_vs_old_outcome_scope']} |
| Territoires communaux distincts selon les limites 2026 | {len(old_territories)} | {counts['current_territories']} | +{counts['additional_current_territories_vs_old_outcome_scope']} |
| Communes supplémentaires par rapport aux calculs de trajets déjà existants | {counts['available_municipality_series']} origines déjà présentes | {counts['available_municipality_series']} | 0 |

Les **47 fiches ajoutées au registre de préparation** se décomposent en 44 dont la commune du point n'appartient pas au panel hôtelier, et trois domaines précédemment exclus pour périmètre composite incomplet : Gstaad, Sainte-Croix / Les Rasses et Villars-Gryon-Les Diablerets. Leurs 62 points de fiches sont résolus dans une commune suisse. La réduction par futurs regroupements n'est pas encore connue : 62 fiches ne signifient pas 62 domaines indépendants.

Les **174 séries communales supplémentaires** sont déjà stockées dans le projet ; aucun nouveau téléchargement n'a eu lieu. Elles deviennent disponibles pour examiner l'exposition aux nouvelles stations. Toutes les 186 séries ont au moins une valeur mensuelle de nuitées observée et une origine de transport existante. Moutier BE (BFS 700) et Moutier JU (BFS 6831) représentent deux séries administratives pour un seul territoire actuel ; elles ne doivent pas devenir deux communes indépendantes. Séries de moins de 24 mois observés : {short_text}. Le nombre avec des fenêtres avant/après suffisantes dépendra des adhésions examinées.

## Cas restant à résoudre

Sur 88 entrées de base, 10 destinations entièrement étrangères sont écartées du périmètre. Restent **78 événements**, soit 62 correspondances directes et **16 événements suisses ou à composante suisse en attente**. Parmi ces 16, quatre concernent une destination sans fiche propre : Château-d'Oex / La Braye, Grenchenberg, Mayens de Conthey et Wilerallmi. Les douze autres concernent des composantes ou périmètres chevauchants. Six fiches supplémentaires apparaissent dans les relations documentées, mais ces relations ne sont pas des identités validées et ne sont pas ajoutées aux 62. Le cas Jura sur Léman est limité à sa composante suisse à clarifier.

## Ce qui est effectivement intégré

Les cas figurent désormais dans les trois registres ci-dessous. **L'intégration porte sur le périmètre de préparation**, pas sur un panel final d'effets. Zéro nouveau couple station–commune a encore été validé par temps de trajet, et zéro nouvelle unité causale est approuvée. Le nombre finalement analysable ne peut être annoncé avant les contrôles d'identité, d'accès et de couverture temporelle. Arrêt à cette étape pour présentation au chercheur.

## Registres et reproduction

- [Stations identifiées](accessibility_expansion_station_inventory.csv) : une ligne par entrée liée à une fiche, avec identifiants d'origine, saison, méthode de lien, commune du point et motif d'ajout.
- [Événements en attente](accessibility_expansion_pending_events.csv) : les 16 cas, leurs preuves existantes et relations possibles. `integrated_as_station` reste faux.
- [Séries communales](accessibility_expansion_municipality_inventory.csv) : code BFS, observations disponibles, première/dernière observation, origine existante et doublons territoriaux.
- [Comptes et empreintes des entrées](accessibility_expansion_inventory_summary.json).

Reproduction depuis la racine : `python src/descriptive/audit_accessibility_expansion.py`. Les fichiers CSV sont des registres d'audit ; aucun nouvel indicateur analytique ou source externe n'est introduit. Les sources et variables d'origine restent référencées dans `metadata/data_sources_master.csv` et `metadata/data_dictionary.csv`.
"""
    (REPORTS / "54_BILAN_ELARGISSEMENT_ETAPE_1_FR.md").write_text(text, encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
