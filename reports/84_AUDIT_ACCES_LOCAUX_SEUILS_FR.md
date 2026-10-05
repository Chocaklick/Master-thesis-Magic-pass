# Audit des accès locaux et des seuils — 5 octobre 2026

## Résultat

Le problème ne vient pas uniquement des 120 minutes. La règle actuelle mélange accessibilité en transports publics et bassin d'hébergement, omet certains accès locaux et impose une réussite sur **24 départs sur 24**. L'audit et les comparaisons ont été autorisés ; **aucun nouveau seuil, temps de marche, traitement ou témoin n'a été adopté**. Les estimations et graphiques 82–83 sont conservés, mais leurs dates d'exposition doivent être réexaminées avant interprétation.

## Comparaison demandée

Même définition actuelle du trajet, même exigence 24/24, mêmes groupes et calendrier. Moutier est compté une seule fois.

| Seuil | Communes exposées selon les routes actuelles | Groupes accessibles | Communes perdues par rapport à 120 min | Dates de première exposition modifiées* | Pré36 entièrement observé** |
|---|---:|---:|---:|---:|---:|
| 30 min | 5 | 5 | 74 | 0 | 5 |
| 45 min | 10 | 12 | 69 | 1 | 9 |
| 60 min | 30 | 28 | 49 | 8 | 26 |
| 120 min, référence | 79 | 45 | 0 | 0 | 70 |

*Parmi les communes encore exposées. À 45 minutes, la date de Visp change. À 60 minutes, huit dates changent : Blonay-Saint-Légier, Spiez, Brig-Glis, Kandersteg, Langnau im Emmental, Visp, Sigriswil et Meiringen.

**Compteur descriptif de 36 valeurs mensuelles publiées, sans imputation. Ce n'est pas le nombre de communes calculables : le modèle antérieur acceptait certains historiques partiellement observés lorsque la régression restait calculable. Aucune nouvelle exclusion n'est appliquée ici.

Les dix communes à 45 minutes sont Beatenberg, Unterseen, Schangnau, Gruyères, Plaffeien, Leysin, Ollon, Le Chenit, Anniviers et Visp. Ce sont des **candidats issus des routes**, pas dix bassins touristiques validés. Les 30/45/60 minutes laissent respectivement 3/2/2 communes avec un arrêt local identique sans exposition par la règle de transport. Elles ne peuvent pas être considérées automatiquement comme témoins non affectés.

## Accès locaux : ce qui manque

L'audit couvre les **75 points d'accès des 71 groupes**, avec rapprochement vers la commune contenant leur arrêt de bus/train. Cette commune n'est pas nécessairement celle de la remontée ni le lieu d'hébergement pertinent.

| Cas | Constat | Conséquence actuelle |
|---|---|---|
| Leukerbad, BFS 6111 | Origine et arrivée au Busterminal. 24 requêtes rejetées car sans véhicule. Point de référence à 175 m à vol d'oiseau de l'arrêt. | Groupe local entré en mai 2019, mais exposition communale datée de mai 2023 via Eischoll, à 114 min. |
| Hasliberg, BFS 783 | Même arrêt Wasserwendi, Twing. 24 requêtes rejetées. Point à 43 m. | Groupe Meiringen-Hasliberg entré en mai 2025 ; commune classée « jamais exposée » et témoin dans les sept cohortes. |
| Beatenberg, BFS 571 | Même arrêt Waldegg pour un point à 655 m. Une autre arrivée donne une route complète. | Date de mai 2022 inchangée, mais l'option locale est omise. |
| Château-d'Œx / La Braye | Dix allers rejetés pour trajet sans véhicule **entre deux arrêts différents** ; quatorze retours disponibles. | Accès local incomplet ; il faut distinguer marche codée dans le réseau et simple identité d'arrêt. |

Les distances ci-dessus proviennent des références déjà collectées. Elles ne sont **ni des distances piétonnes ni des minutes de marche**. Le fichier de requêtes conserve la meilleure option par horaire : à Beatenberg, un autre accès utilisable masque les rejets du point Waldegg dans les résultats agrégés. Un zéro dans le compteur de rejets ne prouve donc pas que chaque point d'accès est traité correctement.

Deux autres limites sont maintenant explicites :

- Sur 30 points d'accès dont la commune d'arrêt figure dans le panel, six relations locales, en dehors des cas d'arrêt identique, échouent à la règle 24/24 : Château-d'Œx, Grenchenberg–Grenchen, Axalp–Brienz, Crans-Montana, Gstaad–Saanen et Saas-Fee. Par exemple, Saas-Fee a **22/24 requêtes disponibles**, avec moyenne de 7,7 minutes sur les trajets disponibles, mais ne passe pas cette règle. Cette moyenne incomplète n'a pas été utilisée pour créer une nouvelle exposition.
- **45 points**, dans **40 communes d'arrêt**, ne correspondent à aucune commune du panel hôtelier actuel. **43 groupes** n'ont aucun point d'accès dont la commune d'arrêt figure dans ce panel. Cela ne prouve pas l'absence de données OFS ailleurs ni l'absence d'un bassin voisin : la couverture des nuitées et l'association géographique restent à vérifier.

## Ce que mesure réellement le temps

Le temps est la moyenne aller/retour des trajets horaires, **attente initiale comprise**, sur un mercredi et un samedi de février 2026. L'origine est l'arrêt ferroviaire le plus desservi de la commune, sinon un arrêt terrestre très desservi ; ce n'est pas systématiquement le centre communal. L'arrivée est un arrêt proche d'un point de référence, pas un départ de remontée entièrement vérifié. La marche finale non codée n'est pas ajoutée. Plusieurs arrêts sont à plus de deux kilomètres de leur référence.

Exemple : Evolène est à 51 minutes selon cette métrique, dont environ **42 minutes d'attente initiale moyenne aller/retour**. Un seuil de 45 minutes l'écarterait encore. Il faut donc choisir la métrique avant d'interpréter son seuil.

Un bassin touristique désigne les communes où les clients des stations peuvent plausiblement loger. L'accessibilité est un indice de cette relation, pas sa preuve. Une ville accessible pour une excursion à la journée ne constitue pas automatiquement un bassin de nuitées de la station.

## Choix à valider avant de modifier l'analyse

1. **Accès locaux et marche :** soit conserver les TP et vérifier les parcours piétons/derniers kilomètres vers les véritables départs, soit utiliser une relation locale documentée séparée du temps de transport. Ne pas transformer tous les trajets sans véhicule en temps nul.
2. **Fiabilité horaire :** conserver 24/24, ou comparer une couverture partielle explicitement mesurée. Aucun taux minimal alternatif n'est fixé ici. La moyenne des trajets réussis seule pourrait sous-estimer les accès difficiles.
3. **Origine et mode :** maintenir l'arrêt communal actuel corrigé, ou recalculer depuis un centre communal défini vers le départ des remontées, en TP et/ou par la route. Le temps routier nécessite une source et une méthode nouvelles, pas une conversion des temps GTFS.
4. **Seuil et bassin :** comparer de nouveau 30/45/60 après clarification des points précédents, puis vérifier les liens d'hébergement. Ne pas choisir le seuil pour atteindre un nombre souhaité de communes.

Je recommande de clarifier d'abord **origine, départ et marche locale**, puis de comparer les couvertures horaires avant de choisir le seuil principal. Les communes restent dans l'inventaire ; « pas de route admissible » ne devient pas automatiquement « témoin non affecté ».

## Sources, méthode et reprise

Sources déjà enregistrées : horaires `SKI_GTFS_TIMETABLE_2026_WINTER_20260207`, points `MAGIC_CURRENT_MAP` et `BAV_PUBLIC_TRANSPORT_STOPS_2026`, groupes et événements `DERIVED_ACCESSIBILITY_STATION_GROUPS` / `DERIVED_ACCESSIBILITY_STATION_GROUP_EVENTS`, nuitées `BFS_HOTEL_DATA` et raccordement exact de Moutier. Les identifiants de référence sont conservés par point d'accès ; aucun téléchargement ni nouveau routage.

Méthode : audit par identifiants stables, contrôle d'égalité des routes BFS 700/6831 avant dédoublonnage, seuils appliqués aux temps existants, première entrée parmi les groupes actifs avec conservation de la sortie documentée, comptage des seules nuitées observées. Les scénarios 30/60/120 reproduisent exactement les dates du panel existant. Les 45 minutes sont un diagnostic ajouté, sans modification des données canoniques. L'accès 2026 reste fixe historiquement : cette limite n'est pas résolue.

- [Audit détaillé des 75 points](accessibility_local_node_audit.csv).
- [Rejets sans véhicule](accessibility_zero_vehicle_rejections.csv) : 58 requêtes, dont 48 à arrêt identique et 10 entre arrêts différents.
- [Comparaison commune par commune](accessibility_threshold_territories.csv) : 740 lignes, soit 185 communes × quatre seuils, avec dates et couverture des nuitées.
- [Résumé des quatre seuils](accessibility_threshold_summary.csv).
- Configuration : `config/accessibility_local_threshold_audit.json`. Script : `src/data_processing/audit_accessibility_local_thresholds.py`. Manifest : `accessibility_local_threshold_audit_summary.json`, avec empreintes des sources et résultats canoniques protégés.

Reprise : exécuter `.venv/Scripts/python.exe src/data_processing/audit_accessibility_local_thresholds.py` depuis la racine. Les quatre CSV et leur provenance sont reproductibles à partir des fichiers présents. Lire ce rapport et obtenir les choix méthodologiques ci-dessus **avant tout remplacement des expositions, témoins, estimations ou graphiques**.
