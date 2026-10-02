"""Build the reviewed Magic Pass station-group and access-point layers.

This layer is deliberately separate from the preserved lift clusters and from
municipality outcome scopes. It maps all in-scope base-entry events to a stable
station group, aggregates each unique supplied listing once, and selects a
served ground public-transport node near every retained station access point.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "data_processing"))

from build_public_transport_journey_context import (  # noqa: E402
    SOURCE_ID as GTFS_SOURCE_ID,
    count_active_departures,
    exact_metadata,
    load_active_trip_info,
    load_feed_reference_tables,
    mode_is_ground,
    point_distance_km,
    total_departures,
    validate_settings,
)
from build_public_transport_stop_context import checked_source, load_stops  # noqa: E402


CONFIG_PATH = ROOT / "config" / "accessibility_station_groups.json"
PATH_C_CONFIG = ROOT / "config" / "path_c_analysis.json"
HISTORY_PATH = ROOT / "data_processed" / "magic_pass_membership_history.csv"
DIRECT_PATH = ROOT / "reports" / "accessibility_expansion_station_inventory.csv"
PENDING_PATH = ROOT / "reports" / "accessibility_expansion_pending_events.csv"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
CURRENT_PATH = ROOT / "data_processed" / "magic_pass_current_destinations.csv"
GROUP_OUTPUT = ROOT / "data_processed" / "accessibility_station_groups.csv"
EVENT_OUTPUT = ROOT / "data_processed" / "accessibility_station_group_events.csv"
POINT_OUTPUT = ROOT / "data_processed" / "accessibility_station_access_points.csv"
NODE_OUTPUT = ROOT / "reports" / "accessibility_station_access_nodes.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_station_group_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "55_GROUPES_STATIONS_ET_POINTS_ACCES_FR.md"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def unique_pipe(values) -> str:
    return "|".join(sorted({str(v) for v in values if str(v)}))


def direct_group_id(resort_id: str) -> str:
    return f"MP_GROUP_RESORT__{resort_id}"


def season_anchor(season: str) -> tuple[str, str]:
    start = int(str(season).split("/")[0])
    if season == "2017/2018":
        return "2017-11-01", "exact_product_validity_date"
    return f"{start}-05-01", "analytical_may_anchor_from_entry_season"


def structural_number(row: pd.Series, column: str) -> float:
    return float(pd.to_numeric(pd.Series([row[column]]), errors="coerce").iloc[0])


def build_groups(config: dict, history: pd.DataFrame, direct: pd.DataFrame,
                 pending: pd.DataFrame, resorts: pd.DataFrame):
    base = history.loc[history.event_type.eq("base_pass_entry")].copy()
    foreign_ids = set(base.event_id) - set(direct.event_id) - set(pending.event_id)
    if len(base) != 88 or len(foreign_ids) != 10:
        raise ValueError("Stage-1 event partition changed")
    if direct.candidate_resort_id.duplicated().any() or direct.event_id.duplicated().any():
        raise ValueError("Direct station inventory must remain one event per listing")

    event_rows = []
    group_meta = {}
    for row in direct.itertuples(index=False):
        gid = direct_group_id(row.candidate_resort_id)
        group_meta[gid] = {
            "station_group_id": gid,
            "station_group_name": row.source_resort_name,
            "component_resort_ids": [row.candidate_resort_id],
            "grouping_basis": "one directly linked supplied resort listing; lift cluster is retained only as lineage",
            "scope_status": "direct_listing_relation",
            "source_ids": [row.source_id, "BERGFEX_RESORT_DIRECTORY"],
            "origin": "direct_link",
        }
        event_rows.append({
            "event_id": row.event_id,
            "station_group_id": gid,
            "event_mapping_status": "direct_candidate_resort_link",
        })

    pending_seen = set()
    for item in config["pending_groups"]:
        gid = item["station_group_id"]
        existing = group_meta.get(gid)
        if existing:
            expected_components = set(existing["component_resort_ids"])
            if set(item["component_resort_ids"]) != expected_components:
                raise ValueError(f"Pending relation changes direct components for {gid}")
            existing.update({
                "station_group_name": item["station_group_name"],
                "grouping_basis": item["grouping_basis"],
                "scope_status": item["scope_status"],
                "source_ids": sorted(set(existing["source_ids"]) | set(item["source_ids"])),
                "origin": "direct_link_plus_reviewed_pending_relation",
            })
        else:
            group_meta[gid] = {
                "station_group_id": gid,
                "station_group_name": item["station_group_name"],
                "component_resort_ids": item["component_resort_ids"],
                "grouping_basis": item["grouping_basis"],
                "scope_status": item["scope_status"],
                "source_ids": item["source_ids"],
                "origin": "reviewed_pending_relation",
            }
        for event_id in item["event_ids"]:
            if event_id in pending_seen:
                raise ValueError(f"Pending event mapped twice: {event_id}")
            pending_seen.add(event_id)
            event_rows.append({
                "event_id": event_id,
                "station_group_id": gid,
                "event_mapping_status": "reviewed_scope_relation_not_identity_equivalence",
            })
    if pending_seen != set(pending.event_id):
        raise ValueError(f"Pending event mapping mismatch: {pending_seen ^ set(pending.event_id)}")

    events = pd.DataFrame(event_rows).merge(
        base[["event_id", "source_id", "source_resort_name", "entry_season",
              "source_date", "source_page", "date_precision", "candidate_resort_id"]],
        on="event_id", how="left", validate="one_to_one",
    )
    if events.source_id.isna().any() or len(events) != 78:
        raise ValueError("Every in-scope base entry must map to one station group")
    anchors = events.entry_season.map(season_anchor)
    events["effective_month"] = [x[0] for x in anchors]
    events["effective_month_precision"] = [x[1] for x in anchors]
    events["winter_effective_month"] = events.entry_season.map(
        lambda value: f"{int(str(value).split('/')[0])}-11-01")
    events["winter_effective_month_precision"] = np.where(
        events.entry_season.eq("2017/2018"),
        "exact_product_validity_date", "analytical_november_winter_anchor")
    events["component_count_change"] = 1
    # A sufficiently clear analytical link is still not promoted to strict
    # identity equivalence between an official label and a directory entity.
    events["identity_equivalence_approved"] = False
    events["causal_treatment_approved"] = False

    resort_lookup = resorts.set_index("resort_id")
    groups = []
    for gid, item in sorted(group_meta.items()):
        component_ids = list(dict.fromkeys(item["component_resort_ids"]))
        missing = set(component_ids) - set(resort_lookup.index)
        if missing:
            raise ValueError(f"Unknown resort listing(s) in {gid}: {missing}")
        subset = resorts[resorts.resort_id.isin(component_ids)].copy()
        if len(subset) != len(component_ids):
            raise ValueError(f"Duplicate/missing structural components in {gid}")
        group_events = events[events.station_group_id.eq(gid)]
        first_month = group_events.effective_month.min()
        first_winter_month = group_events.winter_effective_month.min()
        ski = pd.to_numeric(subset.ski_area_km, errors="coerce")
        lifts = pd.to_numeric(subset.number_lifts, errors="coerce")
        altitude = pd.to_numeric(subset.altitude_top_m, errors="coerce")
        groups.append({
            "station_group_id": gid,
            "station_group_name": item["station_group_name"],
            "group_origin": item["origin"],
            "scope_status": item["scope_status"],
            "grouping_basis": item["grouping_basis"],
            "component_resort_ids": "|".join(component_ids),
            "component_listing_count": len(component_ids),
            "source_entry_event_ids": unique_pipe(group_events.event_id),
            "source_entry_labels": unique_pipe(group_events.source_resort_name),
            "entry_event_count": len(group_events),
            "first_entry_season": min(group_events.entry_season),
            "first_effective_month": first_month,
            "first_winter_effective_month": first_winter_month,
            "ski_area_km_unique_listing_sum": float(ski.sum(min_count=1)) if len(subset) and ski.notna().all() else np.nan,
            "number_lifts_unique_listing_sum": int(lifts.sum()) if len(subset) and lifts.notna().all() else pd.NA,
            "altitude_top_m_min": float(altitude.min()) if altitude.notna().any() else np.nan,
            "altitude_top_m_max": float(altitude.max()) if altitude.notna().any() else np.nan,
            "structural_data_status": (
                "missing_directory_listing" if not len(subset)
                else "complete_unique_listing_aggregation"
                if ski.notna().all() and lifts.notna().all() and altitude.notna().all()
                else "incomplete_unique_listing_aggregation"
            ),
            "cluster_ids_lineage_only": unique_pipe(subset.cluster_id),
            "source_ids": unique_pipe(item["source_ids"]),
            "current_access_assumption": "fixed_current_access_for_initial_descriptive_screen",
            "membership_continuity_status": "assumed_from_first_base_entry_unless_documented_exit",
            "descriptive_exposure_approved": False,
            "causal_treatment_approved": False,
        })
    groups = pd.DataFrame(groups)
    if len(groups) != 71 or groups.station_group_id.duplicated().any():
        raise ValueError(f"Expected 71 stable station groups, found {len(groups)}")
    if groups.component_listing_count.astype(int).sum() != 67:
        raise ValueError("Expected 67 unique structural listings across 71 groups")
    return groups, events, group_meta


def build_access_points(config: dict, groups: pd.DataFrame, group_meta: dict,
                        current: pd.DataFrame, resorts: pd.DataFrame,
                        passenger: pd.DataFrame) -> pd.DataFrame:
    current = current.copy()
    current["official_latitude_first"] = pd.to_numeric(current.official_latitude_first)
    current["official_longitude_first"] = pd.to_numeric(current.official_longitude_first)
    current_by_candidate = current[current.candidate_resort_id.ne("")].set_index("candidate_resort_id")
    current_by_name = current.set_index("official_destination_name")
    resort_lookup = resorts.set_index("resort_id")
    pending_by_group = {x["station_group_id"]: x for x in config["pending_groups"]}
    rows = []

    for group in groups.itertuples(index=False):
        review = pending_by_group.get(group.station_group_id, {})
        reviewed_current_labels = review.get("official_current_access_labels", [])
        used_names = set()
        for resort_id in str(group.component_resort_ids).split("|") if group.component_resort_ids else []:
            if resort_id in current_by_candidate.index:
                item = current_by_candidate.loc[resort_id]
                if isinstance(item, pd.DataFrame):
                    raise ValueError(f"Multiple current map matches for {resort_id}")
                used_names.add(item.official_destination_name)
                rows.append({
                    "station_group_id": group.station_group_id,
                    "access_point_id": f"ACCESS_MAGIC_CURRENT__{item.official_destination_id}",
                    "access_point_name": item.official_destination_name,
                    "reference_latitude": item.official_latitude_first,
                    "reference_longitude": item.official_longitude_first,
                    "reference_source_id": "MAGIC_CURRENT_MAP",
                    "reference_method": "current_official_magic_map_point",
                    "component_resort_id": resort_id,
                })
            elif not reviewed_current_labels:
                item = resort_lookup.loc[resort_id]
                rows.append({
                    "station_group_id": group.station_group_id,
                    "access_point_id": f"ACCESS_RESORT__{resort_id}",
                    "access_point_name": item.resort_name_canonical,
                    "reference_latitude": float(item.latitude),
                    "reference_longitude": float(item.longitude),
                    "reference_source_id": "BERGFEX_RESORT_DIRECTORY",
                    "reference_method": "supplied_resort_point_fallback_no_current_map_match",
                    "component_resort_id": resort_id,
                })

        for label in reviewed_current_labels:
            if label in used_names:
                continue
            if label not in current_by_name.index:
                raise ValueError(f"Current official access label not found: {label}")
            item = current_by_name.loc[label]
            if isinstance(item, pd.DataFrame):
                raise ValueError(f"Current official access label not unique: {label}")
            rows.append({
                "station_group_id": group.station_group_id,
                "access_point_id": f"ACCESS_MAGIC_CURRENT__{item.official_destination_id}",
                "access_point_name": label,
                "reference_latitude": item.official_latitude_first,
                "reference_longitude": item.official_longitude_first,
                "reference_source_id": "MAGIC_CURRENT_MAP",
                "reference_method": "reviewed_current_official_magic_map_point",
                "component_resort_id": "",
            })
            used_names.add(label)

        special = review.get("special_access")
        if special:
            matches = passenger[passenger.Numero.astype(str).eq(special["stop_id"])]
            if len(matches) != 1:
                raise ValueError(f"BAV special access point not unique: {special['stop_id']}")
            item = matches.iloc[0]
            # The historical base is represented by the official cableway point,
            # but cableways remain ineligible as journey nodes.
            if special["expected_name"].lower().replace("é", "e")[:10] not in str(item.Nom).lower().replace("�", "e"):
                print(f"Warning: decoded BAV name differs for {special['stop_id']}: {item.Nom}")
            to_wgs84 = Transformer.from_crs("EPSG:2056", "EPSG:4326", always_xy=True)
            lon, lat = to_wgs84.transform(float(item.E), float(item.N))
            rows.append({
                "station_group_id": group.station_group_id,
                "access_point_id": f"ACCESS_BAV__{special['stop_id']}",
                "access_point_name": "Château-d'Oex (téléphérique / La Braye)",
                "reference_latitude": lat,
                "reference_longitude": lon,
                "reference_source_id": "BAV_PUBLIC_TRANSPORT_STOPS_2026",
                "reference_method": "official_bav_cableway_operating_point_as_historical_base_reference",
                "component_resort_id": "",
            })
    points = pd.DataFrame(rows).merge(
        groups[["station_group_id", "station_group_name"]], on="station_group_id",
        validate="many_to_one",
    )
    if points.access_point_id.duplicated().any():
        dup = points.loc[points.access_point_id.duplicated(False), "access_point_id"].tolist()
        raise ValueError(f"Access point assigned to multiple groups: {dup}")
    if set(points.station_group_id) != set(groups.station_group_id):
        raise ValueError("Every group needs at least one access point")
    return points.sort_values(["station_group_id", "access_point_id"])


def select_access_nodes(points: pd.DataFrame, passenger: pd.DataFrame,
                        departure_counts: dict[str, dict[str, int]]) -> pd.DataFrame:
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    px, py = transformer.transform(points.reference_longitude.to_numpy(),
                                   points.reference_latitude.to_numpy())
    points = points.assign(reference_x_2056=px, reference_y_2056=py)
    ground = passenger[passenger.MoyenTransport_Code.map(mode_is_ground)].copy()
    ground["selected_stop_id"] = ground.Numero.astype(str)
    for label, counts in departure_counts.items():
        ground[f"departures_{label}"] = ground.selected_stop_id.map(counts).fillna(0).astype(int)
    ground["selected_stop_reference_departures"] = ground.selected_stop_id.map(
        lambda x: total_departures(x, departure_counts))
    ground = ground[ground.selected_stop_reference_departures.gt(0)].copy()
    rows = []
    for point in points.itertuples(index=False):
        candidates = ground.copy()
        candidates["distance_km"] = np.hypot(
            candidates.E.astype(float) - point.reference_x_2056,
            candidates.N.astype(float) - point.reference_y_2056,
        ) / 1000
        candidates["numeric_stop_id"] = pd.to_numeric(candidates.selected_stop_id,
                                                        errors="coerce")
        chosen = candidates.sort_values(
            ["distance_km", "selected_stop_reference_departures", "numeric_stop_id"],
            ascending=[True, False, True], kind="stable").iloc[0]
        distance = float(chosen.distance_km)
        quality = ("near_access_point" if distance <= 0.5 else
                   "local_access_proxy" if distance <= 2.5 else
                   "distant_proxy_review_required")
        rows.append({
            **point._asdict(),
            "selected_stop_id": str(chosen.selected_stop_id),
            "selected_stop_name": str(chosen.Nom),
            "selected_stop_mode_code": str(chosen.MoyenTransport_Code),
            "selected_stop_mode": str(chosen.MoyenTransport_Designation),
            "selected_stop_municipality_bfs_id": str(chosen.Commune_Numero),
            "selected_stop_municipality_name": str(chosen.Commune_Nom),
            "selected_stop_reference_departures": int(chosen.selected_stop_reference_departures),
            "selected_stop_weekday_departures": int(chosen.departures_20260204),
            "selected_stop_saturday_departures": int(chosen.departures_20260207),
            "selected_stop_distance_from_access_point_km": distance,
            "access_node_quality": quality,
            "selection_method": "nearest_reference_day_served_bus_or_train_stop_to_access_point",
            "descriptive_routing_node_approved": quality != "distant_proxy_review_required",
            "historical_access_validated": False,
            "causal_accessibility_feature_approved": False,
        })
    nodes = pd.DataFrame(rows)
    if len(nodes) != len(points) or nodes.selected_stop_reference_departures.le(0).any():
        raise ValueError("Access-node selection is incomplete")
    return nodes.sort_values(["station_group_id", "access_point_id"])


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    path_c = json.loads(PATH_C_CONFIG.read_text(encoding="utf-8"))
    history = read_csv(HISTORY_PATH)
    direct = read_csv(DIRECT_PATH)
    pending = read_csv(PENDING_PATH)
    resorts = read_csv(RESORT_PATH)
    current = read_csv(CURRENT_PATH)
    groups, events, group_meta = build_groups(config, history, direct, pending, resorts)

    gtfs_metadata = exact_metadata(GTFS_SOURCE_ID)
    archive_path = ROOT / gtfs_metadata["raw_file"]
    reference = load_feed_reference_tables(archive_path)
    settings = validate_settings(path_c, reference)
    dates = list(settings["reference_dates"].values())
    trip_reference = load_active_trip_info(archive_path, reference, dates)
    departure_counts, _ = count_active_departures(archive_path, trip_reference)
    passenger, _, _ = load_stops(checked_source(path_c))
    points = build_access_points(config, groups, group_meta, current, resorts, passenger)
    nodes = select_access_nodes(points, passenger, departure_counts)

    points_out = points.drop(columns=["station_group_name"], errors="ignore")
    groups.to_csv(GROUP_OUTPUT, index=False, lineterminator="\n")
    events.sort_values(["effective_month", "station_group_id", "event_id"]).to_csv(
        EVENT_OUTPUT, index=False, lineterminator="\n")
    points_out.to_csv(POINT_OUTPUT, index=False, lineterminator="\n")
    nodes.to_csv(NODE_OUTPUT, index=False, lineterminator="\n")

    quality_counts = nodes.access_node_quality.value_counts().to_dict()
    source_counts = points.reference_method.value_counts().to_dict()
    summary = {
        "analysis_date": config["review_date"],
        "station_groups": len(groups),
        "in_scope_base_entry_events": len(events),
        "foreign_base_entry_events_excluded": 10,
        "groups_with_structural_listing_data": int(groups.component_listing_count.astype(int).gt(0).sum()),
        "groups_without_structural_listing_data": int(groups.component_listing_count.astype(int).eq(0).sum()),
        "groups_with_complete_structural_data": int(groups.structural_data_status.eq("complete_unique_listing_aggregation").sum()),
        "groups_with_incomplete_structural_data": int(groups.structural_data_status.eq("incomplete_unique_listing_aggregation").sum()),
        "unique_component_resort_listings": int(groups.component_listing_count.astype(int).sum()),
        "access_points": len(points),
        "access_point_reference_methods": {str(k): int(v) for k, v in source_counts.items()},
        "access_node_quality": {str(k): int(v) for k, v in quality_counts.items()},
        "groups_with_multiple_access_points": int(points.groupby("station_group_id").size().gt(1).sum()),
        "maximum_access_point_to_ground_stop_km": float(nodes.selected_stop_distance_from_access_point_km.max()),
        "descriptive_routing_nodes_approved": int(nodes.descriptive_routing_node_approved.sum()),
        "historical_access_validated": 0,
        "causal_treatments_approved": 0,
        "input_sha256": {
            str(p.relative_to(ROOT)).replace("\\", "/"): file_hash(p)
            for p in [CONFIG_PATH, HISTORY_PATH, DIRECT_PATH, PENDING_PATH, RESORT_PATH,
                      CURRENT_PATH, PATH_C_CONFIG]
        },
        "source_ids": unique_pipe(points.reference_source_id.tolist() + [GTFS_SOURCE_ID]),
        "grouping_guardrail": config["grouping_guardrail"],
    }
    SUMMARY_OUTPUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")

    distant = nodes[nodes.access_node_quality.eq("distant_proxy_review_required")]
    distant_text = ("aucun" if distant.empty else "; ".join(
        f"{r.access_point_name} → {r.selected_stop_name} ({r.selected_stop_distance_from_access_point_km:.2f} km)"
        for r in distant.itertuples()))
    report = f"""# Groupes-stations et points d'accès — étapes 2 à 4

## Résultat

Les **78 entrées suisses ou à composante suisse** sont maintenant reliées à **{len(groups)} groupes-stations**. La réduction par rapport aux 78 événements vient des composantes publiées ensemble, pas des anciens `cluster_id`. Les dix destinations entièrement étrangères restent hors périmètre.

| Élément | Nombre |
|---|---:|
| Groupes-stations | {len(groups)} |
| Groupes avec au moins une fiche structurelle | {summary['groups_with_structural_listing_data']} |
| Groupes sans fiche dans le répertoire fourni | {summary['groups_without_structural_listing_data']} |
| Groupes avec structure complète | {summary['groups_with_complete_structural_data']} |
| Groupes avec structure de fiche incomplète | {summary['groups_with_incomplete_structural_data']} |
| Fiches structurelles uniques utilisées | {summary['unique_component_resort_listings']} |
| Points d'accès station | {len(points)} |
| Groupes avec plusieurs points d'accès | {summary['groups_with_multiple_access_points']} |

## Règles retenues

Un groupe est créé à partir d'une fiche stable ou d'une relation documentée. Le simple partage d'un ancien cluster de remontées ne suffit jamais : ces clusters peuvent contenir plusieurs domaines indépendants. Les kilomètres de pistes et remontées sont additionnés une seule fois par fiche unique. Les quatre destinations sans fiche — Château-d'Oex/La Braye, Mayens de Conthey, Grenchenberg et Wilerallmi — gardent donc leurs variables structurelles manquantes. La fiche de La Forclaz existe mais ne publie pas de kilométrage de pistes; elle reste explicitement incomplète.

Les cas composites ne sont pas artificiellement transformés en identités parfaites. Beatenberg-Hohwald/Niederhorn et la Vallée de Joux restent des groupes conjoints parce que la fiche structurelle ne permet pas de décomposer les totaux; cette convention ne prouve pas que toutes les composantes sont reliées par remontées. Villars-Gryon-Les Diablerets est le cas explicitement documenté comme domaine relié; Glacier 3000 reste séparé.

## Accès

Chaque coordonnée actuelle de la carte officielle Magic Pass est conservée quand elle existe. Crans-Montana et Lauchernalp utilisent faute de correspondance actuelle leur point du répertoire. Château-d'Oex utilise le point d'exploitation OFT/BAV `8530674`, nommé *Château-d'Oex (téléphérique)*, comme référence historique de la base; la télécabine elle-même n'est jamais utilisée comme mode de trajet.

Le nœud de calcul est l'arrêt de bus ou de train desservi le plus proche de chaque point. Qualités obtenues : `{json.dumps(summary['access_node_quality'], ensure_ascii=False)}`. Cas à revoir car l'arrêt est à plus de 2,5 km : {distant_text}. Ces nœuds sont utilisables pour un premier calcul descriptif seulement; l'accès piéton exact et la stabilité historique ne sont pas validés.

## Fichiers

- `data_processed/accessibility_station_groups.csv` : un groupe, ses événements, sa structure cumulée sans doublon et ses limites;
- `data_processed/accessibility_station_group_events.csv` : les 78 événements et leur mois d'ancrage;
- `data_processed/accessibility_station_access_points.csv` : les coordonnées sources;
- `reports/accessibility_station_access_nodes.csv` : les arrêts de transport retenus et leurs distances;
- `reports/accessibility_station_group_summary.json` : comptes, sources et empreintes des entrées.

Les groupes autorisent la suite du calcul d'exposition, mais **zéro groupe n'est encore approuvé comme traitement causal**.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
