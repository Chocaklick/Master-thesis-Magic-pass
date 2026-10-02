"""Build the focused manual 2018 GTFS validation worklist.

The archive host disallows automated collection in robots.txt.  This script
therefore never downloads the feed; it records the exact official snapshot and
the route endpoints required for the 19 first-exposure design candidates.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_historical_gtfs_2018.json"
FIRST_EXPOSURE_PATH = ROOT / "reports" / "accessibility_first_exposure_audit.csv"
GROUPS_PATH = ROOT / "data_processed" / "accessibility_station_groups.csv"
JOURNEYS_PATH = ROOT / "data_processed" / "accessibility_station_group_journey_context.csv"

WORKLIST_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_manual_worklist.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_historical_gtfs_2018_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "60_AUDIT_HISTORIQUE_ACCES_PRIORITAIRE_FR.md"


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    first = pd.read_csv(FIRST_EXPOSURE_PATH)
    groups = pd.read_csv(GROUPS_PATH)
    journeys = pd.read_csv(JOURNEYS_PATH)
    candidates = first[
        as_bool(first.first_exposure_candidate_for_manual_design_review)
    ].copy()
    if len(candidates) != 19:
        raise ValueError("Expected 19 first-exposure candidates")
    candidate_ids = set(candidates.municipality_bfs_id.astype(int))
    founding_ids = set(
        groups.loc[
            groups.first_effective_month.astype(str).eq("2017-11-01"),
            "station_group_id",
        ]
    )
    worklist = journeys[
        journeys.municipality_bfs_id.astype(int).isin(candidate_ids)
        & journeys.station_group_id.isin(founding_ids)
        & as_bool(journeys.descriptive_accessibility_usable)
        & as_bool(journeys.within_120_minutes)
    ].copy()
    expected_pairs = int(candidates.groups_entering_at_first_exposure.sum())
    if len(worklist) != expected_pairs:
        raise ValueError(
            f"Expected {expected_pairs} founding group-municipality endpoints; found {len(worklist)}"
        )
    keep = [
        "municipality_bfs_id",
        "municipality_name",
        "municipality_main_stop_id",
        "municipality_main_stop_name",
        "station_group_id",
        "station_group_name",
        "outbound_access_point_ids_used",
        "outbound_access_point_names_used",
        "return_access_point_ids_used",
        "return_access_point_names_used",
        "mean_one_way_generalized_minutes",
    ]
    worklist = worklist[keep].copy()
    worklist["historical_timetable_year"] = int(config["timetable_year"])
    worklist["historical_snapshot_build"] = config["snapshot_build"]
    worklist["historical_archive_url"] = config["archive_url"]
    worklist["expected_manual_local_path"] = config["expected_manual_local_path"]
    worklist["manual_download_required_due_to_robots"] = True
    worklist["historical_origin_stop_found"] = False
    worklist["historical_destination_stop_found"] = False
    worklist["historical_route_computed"] = False
    worklist["historical_mean_one_way_generalized_minutes"] = pd.NA
    worklist["absolute_2018_to_2026_time_change_minutes"] = pd.NA
    worklist["historical_access_plausibility_status"] = "pending_manual_feed_download"
    worklist["historical_access_validated"] = False
    worklist["causal_accessibility_feature_approved"] = False
    worklist["source_id"] = config["source_id"]
    worklist = worklist.sort_values(
        ["municipality_bfs_id", "station_group_name"], kind="stable"
    )
    worklist.to_csv(WORKLIST_OUTPUT, index=False, lineterminator="\n")

    summary = {
        "analysis_date": "2026-10-02",
        "source_id": config["source_id"],
        "archive_url": config["archive_url"],
        "head_http_status": config["head_http_status"],
        "content_length_bytes": config["content_length_bytes"],
        "robots_policy_observed": config["robots_policy_observed"],
        "automated_download_allowed": False,
        "manual_download_required": True,
        "historical_feed_downloaded": bool(config["historical_feed_downloaded"]),
        "first_exposure_candidate_municipalities": len(candidates),
        "priority_group_municipality_routes": len(worklist),
        "unique_founding_station_groups": int(worklist.station_group_id.nunique()),
        "unique_origin_stops": int(worklist.municipality_main_stop_id.nunique()),
        "unique_current_destination_access_references": int(
            pd.concat(
                [
                    worklist.outbound_access_point_ids_used,
                    worklist.return_access_point_ids_used,
                ]
            ).nunique()
        ),
        "historical_routes_computed": 0,
        "historical_access_validated_routes": 0,
        "causal_accessibility_features_approved": 0,
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in [CONFIG_PATH, FIRST_EXPOSURE_PATH, GROUPS_PATH, JOURNEYS_PATH]
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Audit historique ciblé des accès — étape 13

## Périmètre utile

Le screening du rapport 59 réduit l'audit historique à **{len(candidates)} communes** et **{len(worklist)} couples commune–groupe fondateur**, couvrant {summary['unique_founding_station_groups']} groupes et {summary['unique_origin_stops']} arrêts d'origine. Il n'est donc pas nécessaire de recalculer immédiatement les 13 206 couples de la matrice complète.

## Source 2018 identifiée

- source officielle : `{config['source_id']}`;
- construction GTFS : `{config['snapshot_build']}`;
- URL : {config['archive_url']};
- taille annoncée par le serveur : **{config['content_length_bytes']:,} octets**;
- réponse HEAD vérifiée : HTTP {config['head_http_status']} le {config['head_check_date']}.

Le fichier n'a pas été téléchargé automatiquement. Le `robots.txt` du serveur d'archive indique `Disallow: /`; cette restriction est respectée. Le téléchargement doit donc être effectué manuellement depuis l'URL officielle, puis le ZIP doit être placé sans modification à l'emplacement suivant :

`{config['expected_manual_local_path']}`

Après dépôt, le projet devra calculer SHA-256, vérifier l'intégrité du ZIP, retrouver les arrêts historiques et exécuter exactement les mêmes horaires-types que pour 2026. Les champs de résultat restent actuellement faux ou manquants; **aucun accès historique ni usage causal n'est approuvé**.

## Fichier de travail

`reports/accessibility_historical_gtfs_2018_manual_worklist.csv` contient chaque origine communale, chaque groupe fondateur accessible, les identifiants d'arrêts actuels, les références d'accès utilisées en 2026 et les champs qui seront complétés après validation du flux 2018.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
