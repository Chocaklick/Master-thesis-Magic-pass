# Comparaison des accès historiques 2018–2026 — étape 14

## Résultat ciblé

L'archive GTFS 2018 fournie manuellement a été vérifiée puis appliquée aux **39 couples commune–groupe fondateur** du screening précédent. Ils représentent **19 communes**, **10 groupes-stations** et **12 points d'accès**. Le calcul reproduit les mêmes 24 horaires-types qu'en 2026 : mercredi et samedi, cinq départs aller et sept retours par jour.

| Contrôle ou résultat | Nombre |
|---|---:|
| Arrêts d'origine communaux retrouvés | 19 / 19 |
| Points d'accès avec identifiant stable | 10 / 12 |
| Points d'accès avec équivalent historique revu | 2 / 12 |
| Couples dont les 24 horaires sont réalisables | 9 / 39 |
| Couples complets et à 120 minutes ou moins en 2018 | 3 / 39 |
| Communes gardant au moins un groupe fondateur à 120 minutes ou moins | 2 / 19 |
| Communes gardant tous leurs groupes fondateurs actuels à 120 minutes ou moins | 2 / 19 |

## Correspondances modifiées

Deux arrêts actuels n'existaient pas sous le même identifiant dans le flux 2018. La règle est la même que pour la sélection 2026 : arrêt actif de train ou de bus le plus proche du point d'accès officiel, avec revue du nom et de la distance.

- Les Diablerets : `8584841` devient `8501479` (Les Diablerets, train), à 0,578 km du point d'accès;
- Villars-Gryon : `8510070` devient `8579126` (Villars-sur-Ollon, temple, bus), à 0,451 km.

Les 29 autres nœuds nécessaires — 19 origines et 10 accès — conservent leur identifiant normalisé. Le détail se trouve dans `reports/accessibility_historical_gtfs_2018_stop_audit.csv`.

## Interprétation

`historical_access_validated` signifie uniquement qu'un couple dispose des 24 itinéraires planifiés et reste à 120 minutes ou moins dans le GTFS 2018. Cela renforce ou révise la plausibilité de l'exposition au moment de la première saison, mais ne prouve ni l'absence de changements intermédiaires, ni les tendances parallèles, ni un effet causal. Tous les drapeaux causaux restent donc à `false`.

Le changement signé est calculé comme **temps 2026 moins temps 2018**; sa médiane est de -147.1 minutes pour les couples comparables. La médiane de la variation en valeur absolue est de 147.1 minutes.

## Fichiers produits

- `data_processed/accessibility_historical_gtfs_2018_journey_samples.csv` : 936 requêtes horaires;
- `data_processed/accessibility_historical_gtfs_2018_journey_context.csv` : un résultat par couple;
- `reports/accessibility_historical_gtfs_2018_municipality_validation.csv` : synthèse des 19 communes;
- `reports/accessibility_historical_gtfs_2018_summary.json` : paramètres, empreintes et comptes;
- `data_interim/accessibility_historical_gtfs_2018_routes/` : cache de reprise par groupe et par jour.
