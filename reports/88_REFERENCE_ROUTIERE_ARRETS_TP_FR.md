# Référence routière « arrêt communal → arrêt de station »

7 octobre 2026. **Collecte nationale terminée**, selon la nouvelle consigne du chercheur : reprendre les points TP existants et reporter les précisions mairie/parking. Les résultats ne remplacent ni les anciens temps TP, ni les expositions ou estimations du mémoire.

## Résultat

| Élément | Couverture |
|---|---:|
| Territoires communaux conservés | 185, représentant 186 historiques sources |
| Arrêts d’accès aux stations conservés | 75, dans les 71 groupes existants |
| Directions demandées et réponses archivées | 27 750 cellules, en 48 requêtes HTTP 200 |
| Directions avec durée strictement positive | 27 592 |
| Directions sans trajet retourné | 150 |
| Zéros du modèle | 8 : 6 validés au même arrêt, 2 restant à vérifier |
| Couples avec moyenne aller–retour utilisable | **13 799 / 13 875**, dont trois à 0 minute validés |
| Communes automatiquement exclues | **0** |

Les 76 couples sans moyenne utilisable restent dans les tableaux. « Collecte terminée » signifie que toutes les cellules ont été interrogées, pas que chaque itinéraire existe ou soit certifié accessible en voiture privée.

## Points et calcul

Origines : `selected_stop_id` des arrêts communaux déjà retenus dans `public_transport_journey_nodes.csv`. Arrivées : `selected_stop_id` déjà retenus dans `accessibility_station_access_nodes.csv`. **Ni l'ancien point de référence géographique de la station, ni une mairie ou un parking nouvellement choisi.**

Chaque identifiant est raccordé exactement à `Numero` dans le fichier officiel OFT `PointExploitation.csv` déjà archivé. Ses coordonnées originales E/N en LV95 sont conservées et transformées en WGS84 (`EPSG:2056 → EPSG:4326`, ordre longitude/latitude explicite). Les 185 origines et 75 arrivées ont toutes une correspondance unique. Le raccordement Moutier 700/6831 reste une seule unité, avec le même arrêt 8500105 pour les deux historiques. Aucun arrêt, groupe ou territoire n'est resélectionné.

Il s'agit des **points officiels des arrêts utilisés dans la sélection TP**, pas d'un relevé de quai ou d'entrée de voirie : le calcul horaire GTFS normalise les identifiants de quai, sans modéliser une géométrie routière. État des coordonnées OFT : 20 septembre 2026 ; version GTFS comparée : 7 février 2026. Cette différence est conservée, sans prétendre mesurer l'accessibilité historique exacte.

API : `https://api.heigit.org/openrouteservice/v2/matrix/driving-car`. Profil voiture, durée et distance, sans heure de départ, trafic réel, supplément neige, parking ou marche inventé. Pour chaque couple : deux calculs indépendants, puis **(minutes aller + minutes retour) / 2** si les deux sont utilisables. Un sens absent ne devient ni zéro, ni une valeur imputée. Un zéro réseau ne prouve pas la coïncidence réelle de l'arrêt communal et du départ des remontées.

## Raccordements et anomalies

Les tableaux conservent les distances `snapped_distance` renvoyées par ORS et les coordonnées routières résolues, dans les deux sens. Un audit séparé calcule aussi leur déplacement géodésique WGS84 : c'est une distance à vol d'oiseau, **pas un temps ou une distance de marche**. Les 260 points ont une observation de raccordement. Sur le maximum observé par point : médiane **15,1 m**, 95e percentile **65,7 m**, maximum **680,27 m**. Aucun seuil d'acceptation ou rejet n'est appliqué.

- **Lauterbrunnen → Grütschalp** : l'ancien arrêt communal est Grütschalp ; ORS raccorde ce point à 257,01 m, mais ne retourne de trajet vers aucun des 75 accès, ni au retour. Les 150 directions restent manquantes ; la commune n'est pas supprimée et son origine n'est pas déplacée arbitrairement au village.
- **Beatenberg (accès Hohwald1799), Hasliberg, Leukerbad** : trois couples utilisent exactement le même identifiant et les mêmes coordonnées OFT à l'origine et à l'arrivée, avec six durées réseau nulles. **Le chercheur a validé leurs moyennes à 0 minute** pour cette mesure arrêt→même arrêt. Cela ne certifie pas un accès nul depuis la mairie jusqu'aux remontées.
- **Saas-Fee** : les coordonnées du Busterminal et d'AlpinExpress sont différentes, mais ORS les raccorde au même point routier, produisant deux zéros. Le raccordement AlpinExpress atteint **680,27 m**, contre **300,78 m** pour le Busterminal. Aucun zéro réel ou temps de marche n'est déduit. La [source officielle d'arrivée](https://www.saas-fee.ch/en/arrival/car-park-saas-fee) indique de laisser la voiture au parking d'entrée du village : le raccordement ne certifie donc pas un accès automobile jusqu'à AlpinExpress.
- **Zermatt** : raccordement de **397,26 m**, avec des durées positives. La [source officielle](https://zermatt.swiss/en/plan-book/arrival) décrit l'arrivée automobile à Täsch, puis le transfert vers Zermatt sans voitures. Une durée renvoyée par le modèle ne suffit pas à certifier l'accès légal en voiture privée. Le territoire et les mesures restent conservés avec cette réserve.

Ces contrôles ne constituent pas un audit exhaustif de toutes les interdictions et routes hivernales. Les raccordements les plus grands sont listés pour inspection ; leur classement n'est pas un filtre. Le modèle ne fournit pas de tracé dans ces matrices pour vérifier les cols, fermetures ou autorisations. Les éventuels changements de point, seuil, marche ou traitement de ces cas seront proposés au chercheur avant application.

**Validation obtenue et appliquée** le 7 octobre : « Oui, valider les trois vrais trajets arrêt → même arrêt à 0 minute. » La configuration conserve les trois couples et identifiants approuvés ; le code contrôle encore l'identifiant et l'égalité des coordonnées avant validation. Saas-Fee reste en attente, sans temps nul réel inventé. Cette modification réutilise les 48 réponses et ne fait aucun nouvel appel.

## Fichiers, sources et reprise

- [Moyennes par couple commune–accès](../data_processed/accessibility_road_stop_pairs.csv) et [mesures directionnelles](../data_processed/accessibility_road_stop_directional.csv).
- [Points communaux](accessibility_road_stop_origins.csv) et [points de station](accessibility_road_stop_arrivals.csv), avec identifiants TP et coordonnées originales.
- [Raccordements des 260 points](accessibility_road_stop_snapping_endpoints.csv), [observations détaillées](accessibility_road_stop_snapping_observations.csv), [152 directions à vérifier](accessibility_road_stop_route_anomalies.csv).
- Manifests : `accessibility_road_stop_preparation_summary.json`, `accessibility_road_stop_collection_summary.json`, `accessibility_road_stop_snapping_summary.json`. Sources et chaque variable enregistrées dans les deux métadonnées centrales. Source des points : `BAV_PUBLIC_TRANSPORT_STOPS_2026`, original déjà vérifié avec SHA-256 et STAC ; pas de téléchargement répété. Documentation primaire : [Matrix](https://giscience.github.io/openrouteservice/api-reference/endpoints/matrix/), [restrictions](https://openrouteservice.org/restrictions/), migration HeiGIT déjà documentée au rapport87.

Les 48 réponses originales sont immuables sous `data_external/accessibility_road_stop_ors/`, avec requêtes sans clé, dates, versions, SHA-256 et en-têtes de quota autorisés. Checkpoints dans `data_interim/accessibility_road_stop_ors/`. Graphe : **21 septembre 2026**, moteur **9.10.0**, identiques entre lots. Dernier quota observé : limite500/restant450, simple constat de ces réponses. Reprise vérifiée : **48 réponses réutilisées, zéro nouvel appel**.

L'export a rencontré une erreur locale intermittente `OSError22` sur le dictionnaire CSV après archivage complet. Reprise validée contre les réponses originales, sans nouvelle requête ; écriture CSV temporaire complète puis remplacement pour éviter une publication partielle. L'option de récupération refuse un tableau qui ne se reconstruit pas exactement depuis les caches vérifiés. Ce problème ne constitue pas un échec de collecte API.

Avant le changement de consigne, le raffinement avait atteint **38/185 centres administratifs**, contre3 auparavant : 29 nouvelles adresses Bern/Grisons géocodées exactement et six points principaux officiels fribourgeois. Sept autres adresses restent en attente ; les coordonnées postales discordantes et points dupliqués ne sont pas devinés. Un seul parking était vérifié. Inventaires, originaux, trois moyennes mairie–Twing et rapport87 sont conservés séparément. La recherche supplémentaire de ces points est **reportée**, sans bloquer cette nouvelle matrice. Les pages d'accès Moléson, Charmey et La Berra déjà récupérées restent documentées ; la tentative Niederhorn HTTP500 et la liste bernoise bloquée par robots restent des échecs explicites.

Commandes depuis la racine, seulement si nécessaire :

```text
.venv/Scripts/python.exe src/data_collection/collect_accessibility_road_stop_matrix.py --execute --max-new-batches 48
.venv/Scripts/python.exe src/data_processing/audit_accessibility_road_stop_snapping.py
```

Il n'y a plus de lot routier TP à télécharger. Prochaine étape éventuelle : inspection/comparaison descriptive aux temps TP corrigés, avant toute nouvelle définition de bassin, correction des cas locaux ou modification de l'analyse. **Aucun seuil, commune supprimée ou exposition/estimation remplacée.** Les treize résultats historiques protégés et six fichiers du premier raffinement routier gardent leurs empreintes.
