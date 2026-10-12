# Données de référence

Les tables ne sont jamais écrasées : quand une étape modifie une table, elle crée une nouvelle version suffixée `_stageNN`. Ce document indique **quelle version utiliser** pour chaque thème. Les anciennes versions restent dans le dépôt pour la traçabilité et les tests ; ne pas les supprimer ni les renommer.

Sauf mention contraire, les chemins sont relatifs à la racine du dépôt. Le sens de chaque colonne est documenté dans `metadata/data_dictionary.csv` (colonnes `table` et `variable`) ; les sources dans `metadata/data_sources_master.csv`.

## 1. Résultat : nuitées hôtelières communales

| À utiliser | Contenu |
|---|---|
| `data_processed/accessibility_municipality_month_exposure_territorial.csv` | Panel commune × mois, **185 territoires** (Moutier 700/6831 réunis), 2013-01 à 2026-12 (nuitées observées jusqu'en 2026-03). Panel d'entrée du DiD de référence. |
| `data_processed/hotel_municipality_month.csv`, `hotel_municipality_month_enriched.csv` | Les 186 séries HESTA d'origine : nuitées, arrivées, clientèle suisse et étrangère. |
| `data_processed/hotel_capacity_municipality_month.csv` | Capacité hôtelière (établissements, chambres, lits) par commune et mois. |

Versions antérieures : `accessibility_municipality_month_exposure.csv` (186 séries administratives, sans le pont de Moutier) ; `destination_month_panel.csv` (phase A, 11 destinations).

## 2. Magic Pass : adhésions

| À utiliser | Contenu |
|---|---|
| `data_processed/magic_pass_membership_history.csv` | 93 événements officiels (entrées, sorties), dates et sources. |
| `data_processed/magic_pass_membership_status_by_season.csv` | Statut par saison et droits hiver/été. |
| `data_processed/magic_pass_scope_relations.csv`, `magic_pass_current_destinations.csv` | Correspondances entre libellés Magic Pass et fiches de stations. |

## 3. Groupes de stations Magic Pass

| À utiliser | Contenu |
|---|---|
| `data_processed/accessibility_station_groups_stage79.csv` | **69 groupes** actuels (après Eischoll–Unterbäch et Wilerallmi–Schwanden), date de première entrée, composantes. |
| `data_processed/accessibility_station_access_points_stage79.csv` | Points d'accès (arrêts) des groupes. |
| `data_processed/station_group_lineage_stage79.csv`, `station_group_parent_bridge_stage79.csv` | Lien entre les 71 identifiants d'origine et les 69 groupes actuels. |

Versions antérieures : `accessibility_station_groups.csv` (71 groupes d'origine), `accessibility_station_groups_stage55.csv` (70 groupes).

## 4. Accès routier commune → groupe de stations

| À utiliser | Contenu |
|---|---|
| `data_processed/accessibility_road_group_reference_stage79.csv` | Temps routier de référence entre chaque territoire et chaque groupe (185 × 69). |
| `data_processed/accessibility_road_pairs_stage79.csv`, `accessibility_road_monthly_exposure_stage79.csv` | Couples commune–groupe et exposition mensuelle aux seuils 15/30/45 min, pour les 69 groupes. |
| `data_processed/accessibility_road_final_pairs.csv`, `accessibility_road_final_directional.csv` | Mesures routières de base (75 accès, corrections Lauterbrunnen et Saas-Fee), utilisées par le DiD du rapport 91. |

Versions antérieures (ne pas utiliser sauf comparaison) : `accessibility_road_reference_*` (mairies et parkings), `accessibility_road_stop_*` et `accessibility_road_stop_corrected_*` (avant les corrections finales), `*_stage55` (70 groupes). Transports publics : `accessibility_reference_time_v2_*` (temps TP révisés) et `accessibility_station_group_journey_*` (GTFS 2026 initial) ; les deux plus gros fichiers d'échantillons ne sont pas versionnés.

## 5. Résultats DiD (effet communal)

| À utiliser | Contenu |
|---|---|
| `reports/accessibility_road_did_30min_*.csv` (+ `_15min_*`, `_45min_*`) | **DiD de référence** (rapport 91) : contrastes par cohorte et mois, dynamique, calibration saisonnière, support par territoire. |
| `reports/accessibility_road_did_summary.json`, `reports/accessibility_road_did_dynamic.png` | Résumé et figure de la dynamique. |
| `reports/accessibility_road_did_inventory.csv`, `accessibility_road_did_comparison_universe.csv` | Communes exposées et univers de témoins. |

Attention : le DiD de référence a été calculé avec les **71 groupes d'origine**, avant les regroupements des étapes 55 et 79. Les expositions recalculées pour 69 groupes existent (`accessibility_road_monthly_exposure_stage79.csv`), mais le DiD n'a pas été relancé dessus.

Versions antérieures : `reports/accessibility_cohort_time_estimation_*` (transports publics, 120 min, rapport 82) ; `reports/accessibility_pilot_*` (pilote apparié, rapports 71–72).

## 6. Profils des stations membres (69 groupes)

| Dimension | À utiliser | Contenu |
|---|---|---|
| **Table consolidée** | `data_processed/national_similarity_feature_context_stage86.csv` | Les six variables comparables (km de pistes mesurés, altitude pondérée, nord/sud, est/ouest, neige décennale, minimum des six villes) et leurs couvertures, pour les 69 groupes et les fiches nationales. **Point de départ du futur clustering.** |
| Pistes | `data_processed/winter_profile_metric_network_stage80.csv` | Réseau mesurable par groupe (longueurs, couverture, portions ambiguës). |
| Pistes (objets) | `data_processed/winter_profile_piste_members_stage79.csv`, `winter_profile_piste_groups_stage79.csv` | Objets OpenStreetMap rattachés à chaque groupe. |
| Relief | `data_processed/terrain_reviewed_profiles_stage82.csv` | Altitude, pente et orientation pondérées par la longueur (67 profils sur 69). |
| Neige avant l'entrée | `data_processed/spass_reviewed_profiles_stage83.csv` (+ `spass_reviewed_winter_stage83.csv`, `spass_reviewed_windows_stage83.csv`) | Moyenne des cinq hivers avant l'entrée de chaque groupe (54 profils sur 69). |
| Neige décennie commune | `data_processed/common_snow_profiles_stage84.csv` (+ `common_snow_winter_stage84.csv`) | Moyenne 2013/14–2022/23, décembre–avril (67 profils sur 69). Descriptive, pas préentrée. |
| Accès urbain | `data_processed/winter_profile_urban_minimum_stage57.csv`, `winter_profile_urban_city_detail_stage57.csv` | Temps routier minimal depuis Bâle, Berne, Genève, Lausanne, Lugano, Zurich (version à 70 groupes ; la valeur pour les 69 groupes actuels est dans la table consolidée). |

Versions antérieures : affectations de pistes `winter_profile_piste_assignment_stage51` à `_stage79` ; relief `terrain_reference_profiles_stage67.csv` (40 groupes) et pilotes `_stage63`/`_stage64` ; neige `spass_preentry_profiles_stage77.csv` (34 profils) ; `winter_profile_urban_minimum.csv` et `winter_profile_urban_city_detail.csv` (71 groupes).

## 7. Base nationale (phase D, en cours)

| À utiliser | Contenu |
|---|---|
| `data_processed/national_similarity_inventory_stage86.csv` | 272 unités de préparation (69 groupes, 200 fiches suisses, 3 fiches étrangères) et disponibilité de chaque mesure. |
| `data_processed/national_similarity_listing_lineage_stage86.csv` | Les 271 fiches d'origine et leurs caractéristiques publiées. |
| `data_processed/national_preparation_work_queue_stage91.csv` | File de vérification des 200 fiches et statut de chaque dossier. |
| `data_processed/national_piste_review_members_stage91.csv`, `national_proxy_networks_stage92.csv`, `national_proxy_spass_weights_stage92.csv` | Pistes examinées et réseaux provisoires des six dossiers ouverts. |
| `data_processed/national_common_snow_profiles_stage93.csv` | Neige décennale des six réseaux provisoires. |
| `data_processed/braunwald_urban_road_*_stage90.csv` | Accès routier validé de Braunwald. |

Versions antérieures : `national_similarity_*_stage85.csv`, `national_preparation_work_queue_stage88.csv`.

## 8. Phase A : voie C et couches de contexte

| Thème | Tables |
|---|---|
| Stations | `resort_master.csv` (271 fiches), `resort_point_municipality.csv`, `resort_municipality_crosswalk.csv`, `resort_data_quality.csv` |
| Voie C | `path_c_resort_cluster_features.csv`, `path_c_cluster_segments.csv`, `path_c_candidate_analogues.csv`, `path_c_candidate_analogue_sensitivity.csv`, `path_c_candidate_evidence_dashboard.csv`, `magic_pass_decision_support.csv` |
| Contexte (population, transport, routes, forfaits, réseau) | `path_c_cluster_*_context.csv`, `resort_*_context.csv`, `competing_pass_historical_area_seasons.csv`, `resort_competing_pass_history.csv` |
| Neige et météo (proxies de stations de mesure) | `resort_snow_station_crosswalk.csv`, `resort_snow_vulnerability.csv`, `slf_snow_station_*.csv`, `destination_snow_*.csv`, `meteoswiss_*.csv`, `destination_weather_*.csv` |
| Contexte communal OFS (rapport 80) | `municipality_typology_2020_snapshot_2026.csv`, `municipality_new_residential_buildings_year.csv`, `bfs_residential_property_price_index_quarter.csv`, `bfs_tourism_investments_*_year.csv`, `bfs_tourism_satellite_national_context_year.csv` |
| Contexte touristique et population | `municipality_tourism_context_2025.csv`, `municipality_population_geometry_2026.csv`, `eurostat_population_grid_2021_swiss_region.csv` |

Tous ces fichiers se trouvent dans `data_processed/`.

## 9. Registres

| Fichier | Rôle |
|---|---|
| `metadata/data_sources_master.csv` | Une ligne par source (URL, date, méthode, licence, fichier local). |
| `metadata/data_dictionary.csv` | Une ligne par couple table–variable (définition, unité, rôle, part manquante). |
| `metadata/entity_resolution_log.csv` | Correspondances de noms et décisions d'identité. |
| `metadata/variable_causal_role.csv` | Rôle causal des variables (pré-traitement, médiateur, résultat…) ; ne contient pour l'instant que l'en-tête. |
| `logs/data_collection_log.csv` | Chaque requête de collecte, réussie ou non. |
