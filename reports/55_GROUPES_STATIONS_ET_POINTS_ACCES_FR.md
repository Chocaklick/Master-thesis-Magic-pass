# Groupes-stations et points d'accès — étapes 2 à 4

## Résultat

Les **78 entrées suisses ou à composante suisse** sont maintenant reliées à **71 groupes-stations**. La réduction par rapport aux 78 événements vient des composantes publiées ensemble, pas des anciens `cluster_id`. Les dix destinations entièrement étrangères restent hors périmètre.

| Élément | Nombre |
|---|---:|
| Groupes-stations | 71 |
| Groupes avec au moins une fiche structurelle | 67 |
| Groupes sans fiche dans le répertoire fourni | 4 |
| Groupes avec structure complète | 66 |
| Groupes avec structure de fiche incomplète | 1 |
| Fiches structurelles uniques utilisées | 67 |
| Points d'accès station | 75 |
| Groupes avec plusieurs points d'accès | 4 |

## Règles retenues

Un groupe est créé à partir d'une fiche stable ou d'une relation documentée. Le simple partage d'un ancien cluster de remontées ne suffit jamais : ces clusters peuvent contenir plusieurs domaines indépendants. Les kilomètres de pistes et remontées sont additionnés une seule fois par fiche unique. Les quatre destinations sans fiche — Château-d'Oex/La Braye, Mayens de Conthey, Grenchenberg et Wilerallmi — gardent donc leurs variables structurelles manquantes. La fiche de La Forclaz existe mais ne publie pas de kilométrage de pistes; elle reste explicitement incomplète.

Les cas composites ne sont pas artificiellement transformés en identités parfaites. Beatenberg-Hohwald/Niederhorn et la Vallée de Joux restent des groupes conjoints parce que la fiche structurelle ne permet pas de décomposer les totaux; cette convention ne prouve pas que toutes les composantes sont reliées par remontées. Villars-Gryon-Les Diablerets est le cas explicitement documenté comme domaine relié; Glacier 3000 reste séparé.

## Accès

Chaque coordonnée actuelle de la carte officielle Magic Pass est conservée quand elle existe. Crans-Montana et Lauchernalp utilisent faute de correspondance actuelle leur point du répertoire. Château-d'Oex utilise le point d'exploitation OFT/BAV `8530674`, nommé *Château-d'Oex (téléphérique)*, comme référence historique de la base; la télécabine elle-même n'est jamais utilisée comme mode de trajet.

Le nœud de calcul est l'arrêt de bus ou de train desservi le plus proche de chaque point. Qualités obtenues : `{"near_access_point": 51, "local_access_proxy": 21, "distant_proxy_review_required": 3}`. Cas à revoir car l'arrêt est à plus de 2,5 km : Jura-sur-Léman (Transfrontalier) → La Givrine (2.63 km); Rathvel → Les Paccots, Les Rosalys (3.11 km); Les Rochers - de - Naye → Jor (2.59 km). Ces nœuds sont utilisables pour un premier calcul descriptif seulement; l'accès piéton exact et la stabilité historique ne sont pas validés.

## Fichiers

- `data_processed/accessibility_station_groups.csv` : un groupe, ses événements, sa structure cumulée sans doublon et ses limites;
- `data_processed/accessibility_station_group_events.csv` : les 78 événements et leur mois d'ancrage;
- `data_processed/accessibility_station_access_points.csv` : les coordonnées sources;
- `reports/accessibility_station_access_nodes.csv` : les arrêts de transport retenus et leurs distances;
- `reports/accessibility_station_group_summary.json` : comptes, sources et empreintes des entrées.

Les groupes autorisent la suite du calcul d'exposition, mais **zéro groupe n'est encore approuvé comme traitement causal**.
