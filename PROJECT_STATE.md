# État du projet

**Dernière mise à jour : 12 octobre 2026**, après la réorganisation de la documentation (aucun calcul, aucune donnée modifiée).

Ce fichier décrit l'état **actuel**. Il est réécrit à chaque mise à jour, pas empilé. L'historique détaillé est dans [`logs/research_journal.md`](logs/research_journal.md) ; l'ancienne version longue de ce fichier est archivée dans [`docs/archive/PROJECT_STATE_historique_2026-10-12.md`](docs/archive/PROJECT_STATE_historique_2026-10-12.md).

## En une minute

1. **Données en place** : 186 séries communales de nuitées hôtelières (janvier 2013 – mars 2026, 185 territoires après le pont de Moutier), 93 événements Magic Pass officiels, 271 fiches de stations, un registre de provenance complet.
2. **Effet communal du Magic Pass** : une commune est « exposée » quand une station membre devient accessible en voiture en 30 minutes au plus (15 et 45 min en sensibilité). Le DiD cohortes × mois ne détecte **aucun effet moyen** : à 30 min, 54 communes exposées sont calculables et aucune des 101 bandes mensuelles post-entrée n'exclut zéro ([rapport 91](reports/91_DID_ROUTIER_30MIN_SENSIBILITES_FR.md)). Ce n'est pas une preuve d'absence d'effet.
3. **Profils des stations membres** (69 groupes, hiver décembre–avril) : longueur de pistes, relief, neige modélisée et accès routier depuis six grandes villes sont disponibles ; les six variables comparables le sont pour 67 groupes ([rapports 127–128](reports/128_CLUSTERING_DESCRIPTIF_BASE_NATIONALE_FR.md)).
4. **Direction actuelle** : regroupement **descriptif** des stations, membres et non-membres, avant toute prédiction. La base nationale (200 fiches suisses non membres à vérifier) est en préparation.
5. **Aucun clustering de profils n'a encore été lancé** ; le protocole attend validation.

## Travail en cours (interrompu proprement, rien n'est actif)

- **Étape 94 — Flumserberg (accès multiples)** : quatre arrêts d'arrivée vérifiés (Unterterzen, Oberterzen, Tannenboden, Tannenheim) ; le collecteur `src/data_collection/collect_flumserberg_urban_road_stage94.py` est prêt, mais **les 48 durées routières n'ont pas été collectées**. Règle validée : moyenne aller-retour par arrêt, minimum des arrêts pour chaque ville, puis minimum des six villes.
- **Base nationale** : 200 fiches conservées dans `data_processed/national_preparation_work_queue_stage91.csv`. Six dossiers ouverts (Avers, Bivio, Braunwald, Elm, Feldis, Flumserberg) ; ski historique confirmé pour Braunwald (2019/20), Elm (2022/23) et Feldis (2019/20) ; Avers, Bivio et Flumserberg restent à certifier. Aucun nouveau domaine indépendant n'est encore accepté.

## Décisions déjà prises par le chercheur (ne pas redemander)

- Saison d'hiver analysée : **décembre–avril**.
- Accès : voiture « arrêt communal → arrêt de station » (openrouteservice) ; seuil principal **30 min**, sensibilités 15 et 45 min. Exceptions validées : Lauterbrunnen et Saas-Fee (rapport 90), Braunwald → Linthal Braunwaldbahn (rapport 129).
- Témoins : communes jamais exposées et pas encore exposées (option C, rapport 75) ; toutes les cohortes, COVID inclus avec sensibilité (rapport 74).
- Regroupements validés : Eischoll–Unterbäch (rapport 108), Wilerallmi–Schwanden et La Dôle–Tuffes entière, transfrontalière (rapport 125) → 69 groupes.
- Relief swissALTI3D 2 m ; neige SPASS seule (hypothèse « mètres ») ; pas de raccord avec OSHD ; complément français de La Dôle **abandonné**.
- Profils neige : 5 hivers propres à chaque entrée (préentrée) **et** décennie commune 2013/14–2022/23 (descriptive, non préentrée).
- Base nationale : domaines transfrontaliers connectés gardés entiers ; une station est admissible si une activité de ski est documentée pendant au moins un hiver de la décennie commune ; arrêts de station vérifiés pour l'accès aux six villes ; damage seulement descriptif (étape 92).
- Clustering : descriptif d'abord, prédiction plus tard ; l'ancien choix « 54 avec neige / 67 sans neige » est caduc.

## Décisions en attente

1. **Protocole de clustering** : variables (proposition : km de pistes mesurables, altitude pondérée, orientations nord/sud et est/ouest, neige, minimum des six villes), transformations (log + standardisation), algorithme (Ward / k-means), nombre de classes (2 à 5), traitement des couvertures partielles.
2. **Stratégie pour la base nationale** : vérifier les 200 fiches une par une ou réduire et standardiser la préparation des non-membres.
3. **Lien entre profils et effets** : comment rattacher les effets communaux (DiD) aux classes de profils pour l'aide à la décision.
4. **Cadre du mémoire** : échéance, langue, attentes de la direction, plan des chapitres. Les brouillons générés (rapports 43–51) ne reflètent que la phase A et sont dépassés.

## Prochaines étapes

À définir avec le chercheur après la réorganisation (voir la conversation du 12 octobre 2026). Ordre de travail recommandé : cadre du mémoire → stratégie de la base nationale → protocole de clustering → effets par classe → aide à la décision → rédaction.

## Reprise technique

- Dernier état Git : tout le travail est commité sur `main` (sauvegardes du 12 octobre 2026 : `ad25b97`, `a402cf2`, `6675ad6`, puis commits de réorganisation).
- Table consolidée pour le futur clustering : `data_processed/national_similarity_feature_context_stage86.csv`.
- Tables de référence par thème : [`docs/DONNEES_DE_REFERENCE.md`](docs/DONNEES_DE_REFERENCE.md).
- Ne pas relancer les collectes terminées (pistes, relief, neige, routes, Braunwald) : les caches sont réutilisés.
- Aucun job de collecte ou de calcul n'est actif.
