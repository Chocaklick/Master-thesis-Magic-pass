# Index des rapports

Les rapports se trouvent dans [`reports/`](../reports/). Ils sont numérotés dans l'ordre de production (01 à 129). Les rapports produits par Codex parlent aussi d'« étapes » (stages 1 à 94) : la colonne **Étape** donne la correspondance quand elle existe.

**Statut :**
- **référence** : encore valable sur son sujet ;
- **historique** : point d'étape dépassé par un travail ultérieur (→ rapport qui le remplace) ; conservé pour la traçabilité ;
- **brouillon A** : brouillon de mémoire généré automatiquement à la fin de la phase A ; il ne reflète pas les phases B à D.

À côté des rapports `.md`, `reports/` contient les sorties chiffrées (CSV/JSON) des scripts et, dans `reports/figures/`, des cartes de revue des pistes. Ces fichiers sont cités dans les rapports.

## Phase A — Mission initiale, audit, faisabilité et « voie C » (rapports 01–51)

### A1 — Audit et données de base

| N° | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|
| — | [INITIAL_DATA_AUDIT](../reports/INITIAL_DATA_AUDIT.md) | Audit du contenu des 11 fichiers fournis au départ (checkpoint 1). | référence |
| — | [EXISTING_CLUSTER_AUDIT](../reports/EXISTING_CLUSTER_AUDIT.md) | Les clusters de remontées fournis sont validés et conservés comme couche de référence, sans être recalculés. | référence |
| 01 | [Data audit](../reports/01_DATA_AUDIT.md) | Synthèse du checkpoint 1 : fichiers hachés, entrées utilisables et limites de sens des données fournies. | référence |
| 02 | [Data collection](../reports/02_DATA_COLLECTION.md) | Sources ajoutées (capacité HESTA, neige SLF, météo, preuves Magic Pass…) et méthode de collecte. | référence |
| 03 | [Data quality](../reports/03_DATA_QUALITY.md) | Qualité des données : identifiants cohérents, affectations reproductibles, valeurs confidentielles laissées manquantes. | référence |
| 04 | [Destination unit review](../reports/04_DESTINATION_UNIT_REVIEW.md) | 18 liens entrée–nuitées regroupés en 14 unités de destination, dont 11 avec un périmètre communal explicite. | référence (phase A) |
| 05 | [Hotel capacity](../reports/05_HOTEL_CAPACITY.md) | Intégration de la capacité hôtelière HESTA (établissements, chambres, lits) par commune et par mois. | référence |
| 06 | [Snow source and proxy](../reports/06_SNOW_SOURCE_AND_PROXY.md) | Choix de la source SLF et indicateurs de neige à la station de mesure la plus proche. | historique (neige des profils → 123, 128) |
| 07 | [Weather proxy](../reports/07_WEATHER_PROXY.md) | Températures et précipitations régionales MétéoSuisse par destination. | référence (contexte) |
| — | [model_feasibility_report](../reports/model_feasibility_report.md) | Taille d'échantillon par famille de modèles : le ML causal et les réseaux de neurones ne sont pas justifiés. | référence |
| — | [DATA_SOURCES](../reports/DATA_SOURCES.md) | Description de toutes les sources, générée depuis le registre. En cas d'écart, `metadata/data_sources_master.csv` fait foi. | référence |

### A2 — Adhésions Magic Pass et témoins

| N° | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|
| 08 | [Membership evidence review](../reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md) | Preuves d'adhésion saison par saison pour les unités examinées. | référence |
| 09 | [Entity scope and donor review](../reports/09_ENTITY_SCOPE_AND_DONOR_REVIEW.md) | Classement des 26 libellés d'entrée sans fiche correspondante, pour protéger le réservoir de témoins. | référence |
| 10 | [Annual winter/summer offering](../reports/10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md) | Droits d'hiver et d'été du Magic Pass par saison, d'après les publications annuelles. | référence |
| 11 | [Donor pretrend screen](../reports/11_DONOR_PRETREND_SCREEN.md) | 315 paires traitement–témoin examinées, 35 présélectionnées sur les tendances avant entrée. | historique → 17 |
| 12 | [Temporal controls](../reports/12_TEMPORAL_CONTROLS.md) | Calendrier de 168 mois : saisons, fêtes, Pâques, période COVID. | référence |
| 13 | [Snow proxy sensitivity](../reports/13_SNOW_PROXY_SENSITIVITY.md) | Sensibilité du proxy neige à une deuxième station SLF (4 accords faibles sur 15). | historique |
| 14 | [Donor network spillover](../reports/14_DONOR_NETWORK_SPILLOVER_AUDIT.md) | Proximité des témoins avec tout le réseau Magic Pass : risque de contamination. | historique → 17 |
| 15 | [Treatment distance gradient](../reports/15_TREATMENT_DISTANCE_GRADIENT.md) | Nuitées des communes proches (≤ 30 km) et éloignées (> 50 km) d'une même destination, descriptif. | historique |
| 16 | [Donor external shocks](../reports/16_DONOR_EXTERNAL_SHOCK_AUDIT.md) | Chocs locaux et forfaits concurrents chez les témoins éloignés : les 7 dernières paires sont exclues. | historique → 17 |
| 17 | [Checkpoints 4–5 et voie C](../reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md) | Aucun traitement ni témoin causalement admissible ; passage à la voie C exploratoire. | référence |

### A3 — Voie C et couches de contexte

| N° | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|
| 18 | [Segmentation and analogues](../reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md) | k-means (k = 2) sur 156 clusters et analogues membres pour 104 candidats non membres. | référence (phase A) |
| 19 | [Aggregation sensitivity](../reports/19_PATH_C_AGGREGATION_SENSITIVITY.md) | Agrégation min/médiane/max : seuls 11 candidats restent stables sur tous les critères. | référence (phase A) |
| 20 | [Tourism dependence context](../reports/20_TOURISM_DEPENDENCE_CONTEXT.md) | Intensité touristique communale (nuitées par habitant, lits) d'après STATPOP et HESTA 2025. | référence (contexte) |
| 21 | [Accessibility context](../reports/21_ACCESSIBILITY_CONTEXT.md) | Population suisse dans des rayons en ligne droite autour des clusters. | référence (contexte) |
| 22 | [Transport accessibility (NPVM)](../reports/22_TRANSPORT_ACCESSIBILITY_CONTEXT.md) | Temps d'accès modélisés par l'ARE (NPVM 2025) vers les centres. | référence (contexte) |
| 23 | [Public transport stops](../reports/23_PUBLIC_TRANSPORT_STOP_CONTEXT.md) | Distance aux arrêts et gares officiels (OFT/BAV). | référence (contexte) |
| 24 | [Public transport journeys](../reports/24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md) | Trajets planifiés (GTFS hiver 2026) entre 11 destinations et 186 communes. | historique → 56 |
| 25 | [Historical timetable audit](../reports/25_PUBLIC_TRANSPORT_HISTORICAL_AUDIT.md) | Horaires historiques disponibles et interdiction de collecte automatique des archives. | référence |
| 26 | [Arrival node review](../reports/26_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW.md) | Revue des 15 points d'arrivée en transports publics des destinations. | historique |
| 27 | [NPVM zone proxy audit](../reports/27_TRANSPORT_ZONE_PROXY_AUDIT.md) | Zones NPVM attribuées aux points de haute montagne. | référence (contexte) |
| 28 | [Distance vs transport](../reports/28_DISTANCE_TRANSPORT_COMPARISON.md) | Distance et temps en transports publics sont corrélés mais pas interchangeables. | référence |
| 29 | [Cross-border population](../reports/29_CROSS_BORDER_POPULATION_CONTEXT.md) | Population transfrontalière (grille Eurostat 2021) autour des clusters. | référence (contexte) |
| 30 | [National road proximity](../reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md) | Distance aux axes routiers nationaux (OFROU). | référence (contexte) |
| 31 | [Competing passes (actuels)](../reports/31_COMPETING_PASS_CONTEXT.md) | Forfaits concurrents actuels (AlpsPass, Meilenweiss, Schneepass) reliés aux stations. | référence |
| 32 | [Network context](../reports/32_PATH_C_NETWORK_CONTEXT.md) | Nombre de stations et de stations de forfaits dans un rayon de 25 et 50 km. | référence (contexte) |
| 33 | [Cluster geography sensitivity](../reports/33_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY.md) | Sensibilité de la géographie des clusters aux règles de distance. | référence (contexte) |
| 34 | [Weather station sensitivity](../reports/34_WEATHER_STATION_SENSITIVITY.md) | Sensibilité météo à une deuxième station SwissMetNet. | historique |
| 35 | [Weather gridded sensitivity](../reports/35_WEATHER_GRIDDED_SENSITIVITY.md) | Sensibilité météo aux grilles MétéoSuisse à 1 km. | historique |
| 36 | [Snow gridded sensitivity](../reports/36_SNOW_GRIDDED_SENSITIVITY.md) | Grille SPASS : forte différence entre la station de mesure et la station de ski. | référence (justifie SPASS) |
| 37 | [Destination scope concordance](../reports/37_DESTINATION_SCOPE_CONCORDANCE_AUDIT.md) | La commune du point de station ne reproduit pas toujours le périmètre de nuitées examiné. | référence |
| 38 | [Feature readiness](../reports/38_PATH_C_FEATURE_READINESS_AUDIT.md) | Seules 3 variables structurelles sont autorisées pour la similarité de la voie C. | historique |
| 39 | [Checkpoint 6](../reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md) | Tableau de bord à 7 dimensions pour 104 candidats, sans score ni recommandation. | référence (phase A) |
| 40 | [Scope radius sensitivity](../reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md) | Périmètres touristiques par rayon (0/5/10 km) : aucun n'est un bassin valide. | référence |
| 41 | [Historical competing passes](../reports/41_HISTORICAL_COMPETING_PASS_CONTEXT.md) | Historique partiel de Top4, Meilenweiss, Schneepass, TopCard et SnowPass. | référence |

### A4 — Synthèses et brouillons de mémoire

| N° | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|
| 42 | [Thesis results synthesis](../reports/42_THESIS_RESULTS_SYNTHESIS.md) | Synthèse des résultats de la voie C v0.31. | brouillon A |
| 43 | [Methods draft](../reports/43_THESIS_METHODS_DRAFT.md) | Brouillon du chapitre Méthodes. | brouillon A |
| 44 | [Results draft](../reports/44_THESIS_RESULTS_DRAFT.md) | Brouillon du chapitre Résultats. | brouillon A |
| 45 | [Discussion draft](../reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md) | Brouillon Discussion et limites. | brouillon A |
| 46 | [Citation map](../reports/46_THESIS_CITATION_MAP.md) | Lien entre les affirmations du mémoire et 62 sources ; base pour la bibliographie. | brouillon A (utile) |
| 47 | [Methodological literature](../reports/47_METHODOLOGICAL_LITERATURE.md) | Sept articles méthodologiques vérifiés (DOI). | référence (bibliographie) |
| 48 | [Candidate uncertainty examples](../reports/48_CANDIDATE_UNCERTAINTY_EXAMPLES.md) | Quatre cas illustrant les types d'incertitude des candidats. | brouillon A |
| 49 | [Final methodological report](../reports/49_FINAL_METHODOLOGICAL_REPORT.md) | Réponses aux 18 questions de la mission, état de la phase A. | brouillon A |
| 50 | [Reading draft](../reports/50_THESIS_READING_DRAFT.md) | Brouillon de lecture intégré du mémoire. | brouillon A |
| 51 | [Detailed review draft](../reports/51_THESIS_DETAILED_REVIEW_DRAFT.md) | Version détaillée pour relecture (exports Word EN et FR dans `reports/`). | brouillon A |
| — | [EXECUTIVE_SUMMARY](../reports/EXECUTIVE_SUMMARY.md) | Résumé exécutif de la phase A. | brouillon A |

## Phase B — Exposition des communes et différences-en-différences (rapports 52–91)

### B1 — Élargissement aux communes et accès en transports publics

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 52 | — | [Résumé des données](../reports/52_RESUME_TOTAL_DONNEES_FR.md) | Inventaire en français de toutes les données récoltées au 4 octobre. | référence (inventaire) |
| 53 | — | [Plan d'élargissement](../reports/53_PLAN_ELARGISSEMENT_COMMUNES_STATIONS_FR.md) | Décisions des 1–2 octobre : passer aux communes et à l'accessibilité des stations. | référence |
| 54 | 1 | [Bilan étape 1](../reports/54_BILAN_ELARGISSEMENT_ETAPE_1_FR.md) | Premier inventaire de l'élargissement. | historique → 55 |
| 55 | 2–4 | [Groupes et points d'accès](../reports/55_GROUPES_STATIONS_ET_POINTS_ACCES_FR.md) | 78 entrées suisses reliées à 71 groupes de stations et 75 points d'accès. | référence (origine des groupes) |
| 56 | 6 | [Temps de trajet TP](../reports/56_TEMPS_TRAJET_GROUPES_STATIONS_COMMUNES_FR.md) | Temps en transports publics entre 71 groupes et 186 communes (13 206 couples). | historique → 88 |
| 57 | 7–10 | [Expositions communales](../reports/57_EXPOSITIONS_ET_FAISABILITE_ELARGIES_FR.md) | Panel commune × mois de 31 248 lignes avec expositions (TP 120 min). | historique → 78, 91 |
| 58 | 11 | [Identification](../reports/58_AUDIT_IDENTIFICATION_EXPOSITION_COMMUNALE_FR.md) | Les effets propres à chaque station ne sont pas identifiables : leurs aires d'accès se recouvrent. | référence |
| 59 | 12 | [Screening pré-exposition](../reports/59_SCREENING_COMPARAISONS_PRE_EXPOSITION_FR.md) | 19 communes de la cohorte de lancement 2017 et leurs paires de comparaison. | historique |
| 60 | 13 | [Audit historique des accès](../reports/60_AUDIT_HISTORIQUE_ACCES_PRIORITAIRE_FR.md) | Accès historiques à vérifier pour 39 couples prioritaires. | historique |
| 61 | 14 | [Accès 2018–2026](../reports/61_COMPARAISON_ACCES_HISTORIQUE_2018_2026_FR.md) | Horaire officiel 2018 : trop peu de correspondances publiées pour reconstruire les trajets. | historique |
| 62 | 15 | [Correspondances à pied](../reports/62_SENSIBILITE_TRANSFERTS_PROXIMITE_GTFS_2018_FR.md) | Sensibilité avec correspondances à pied de 250 m. | historique |
| 63 | 16 | [Topologie 2026 sur 2018](../reports/63_SENSIBILITE_TOPOLOGIE_TRANSFERTS_ACTUELS_GTFS_2018_FR.md) | Sensibilité avec les correspondances 2026 projetées sur le réseau 2018. | historique |
| 64 | 17 | [Comparaisons après filtre historique](../reports/64_REVUE_COMPARAISONS_APRES_ACCES_HISTORIQUE_FR.md) | 70 paires restantes après le filtre d'accès historique. | historique |
| 65 | 18 | [Risques internes](../reports/65_SCREENING_INTERNE_RISQUES_COMPARAISONS_FR.md) | Screening des forfaits concurrents, de la capacité et de la proximité des témoins. | historique |

### B2 — Revues des chocs, témoins et pilote

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 66 | 19 | [Communes traitées](../reports/66_AUDIT_EXTERNE_COMMUNES_TRAITEES_FR.md) | Revue des chocs locaux des 14 communes traitées : 32 paires strictes restent candidates. | historique |
| 67 | 20 | [Témoins prioritaires](../reports/67_AUDIT_EXTERNE_CONTROLES_PRIORITAIRES_FR.md) | Revue des 7 témoins les plus réutilisés. | historique |
| 68 | 21 | [Témoins restants](../reports/68_AUDIT_EXTERNE_CONTROLES_RESTANTS_FR.md) | Revue des 17 autres témoins. | historique |
| 69 | 22 | [Bassins et débordements](../reports/69_SCREENING_BASSINS_TOURISTIQUES_SPILLOVERS_FR.md) | Bassins touristiques et risque d'effets de débordement entre communes. | historique |
| 70 | 23 | [Pré-tendances](../reports/70_DIAGNOSTIC_PRETENDANCES_COMPARAISONS_FR.md) | Tendances avant entrée : 11 paires principales et 4 en sensibilité. | historique |
| 71 | 24 | [Pilote non causal](../reports/71_ESTIMATION_PILOTE_NON_CAUSALE_FR.md) | Pilote apparié : −6,8 %, mais −2,0 % non significatif dans la version prudente. | référence (pilote) |
| 72 | 25 | [Inférence avec peu de communes](../reports/72_INFERENCE_PETIT_NOMBRE_COMMUNES_FR.md) | Le −6,8 % n'est pas robuste (p = 0,10 à 0,19). | référence |

### B3 — Toutes les cohortes et estimation cohortes × mois

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 73 | 26 | [Couverture de toutes les cohortes](../reports/73_COUVERTURE_TOUTES_COHORTES_FR.md) | Inventaire de toutes les cohortes à 120 min, sans exclusion. | historique → 91 |
| 74 | 27 | [COVID et clientèle](../reports/74_SPECIFICATION_COVID_ET_BASELINE_CLIENTELE_FR.md) | Tous les mois gardés (COVID en sensibilité) ; part de clientèle étrangère avant entrée. | référence (décision) |
| 75 | 28 | [Option C](../reports/75_COMPARAISON_COHORTES_OPTION_C_FR.md) | Témoins = communes jamais ou pas encore exposées. | référence (décision) |
| 76 | 28b | [Dynamique non équilibrée](../reports/76_DYNAMIQUE_TEMPORELLE_NON_EQUILIBREE_FR.md) | Tous les mois observés après l'entrée sont conservés. | référence (décision) |
| 77 | 29 | [Entrées successives](../reports/77_ENTREES_SUCCESSIVES_TRAJECTOIRE_RESEAU_FR.md) | Trajectoire complète du réseau après la première exposition. | référence |
| 78 | 29b | [Pont de Moutier](../reports/78_RACCORDEMENT_TERRITORIAL_MOUTIER_FR.md) | Moutier (BFS 700 → 6831) = un territoire : 185 territoires. | référence |
| 79 | 29c | [Comparabilité des cohortes](../reports/79_AUDIT_COMPARABILITE_TOUTES_COHORTES_FR.md) | Comparabilité descriptive de toutes les cohortes, sans filtre. | référence |
| 80 | — | [Données OFS complémentaires](../reports/80_DONNEES_COMPLEMENTAIRES_COMMUNES_OFS_FR.md) | Typologie, constructions, prix immobiliers et investissements touristiques. | référence |
| 81 | 29d | [Cadrage cohortes × mois](../reports/81_CADRAGE_ESTIMATION_COHORTES_MOIS_FR.md) | Choix de l'estimateur cohortes × mois (orientation A). | historique → 82 |
| 82 | 30 | [Estimation cohortes × mois](../reports/82_ESTIMATION_COHORTES_MOIS_OPTION_A_FR.md) | Transports publics, 120 min : aucune bande mensuelle n'exclut zéro. | historique → 91 |
| 83 | 31 | [15 communes](../reports/83_GRAPHIQUES_15_COMMUNES_TENDANCES_FR.md) | Nuitées avant/après pour 15 communes tirées au hasard. | référence (illustration) |

### B4 — Révision des temps d'accès et DiD routier

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 84 | 32 | [Accès locaux et seuils](../reports/84_AUDIT_ACCES_LOCAUX_SEUILS_FR.md) | 120 min trop large et accès locaux mal codés : la mesure d'exposition doit être revue. | référence |
| 85 | 33 | [Révision des temps d'accès](../reports/85_REVISION_TEMPS_ACCES_ET_MODES_FR.md) | Temps TP révisés et études de mobilité suisses. | historique → 88 |
| 86 | 34 | [Préparation routière](../reports/86_PREPARATION_REFERENCE_ROUTIERE_FR.md) | La voiture devient la référence ; préparation des points d'arrivée. | historique → 88 |
| 87 | 35 | [Premier lot routier](../reports/87_COLLECTE_REFERENCE_ROUTIERE_FR.md) | Premiers trajets routiers (mairies et parkings). | historique → 88 |
| 88 | 36 | [Arrêt communal → arrêt de station](../reports/88_REFERENCE_ROUTIERE_ARRETS_TP_FR.md) | Collecte nationale terminée : 13 799 couples utilisables sur 13 875. | référence |
| 89 | — | [Préparation DiD routier](../reports/89_PREPARATION_DID_ROUTIER_SEUILS_FR.md) | Seuil maximal à réduire, à valider. | historique → 90 |
| 90 | 37 | [Lauterbrunnen et Saas-Fee](../reports/90_CORRECTION_LAUTERBRUNNEN_ET_SAASFEE_FR.md) | Seuils 30/15/45 min validés, Lauterbrunnen corrigé, Saas-Fee proposé. | historique → 91 |
| 91 | 38 | [DiD routier](../reports/91_DID_ROUTIER_30MIN_SENSIBILITES_FR.md) | **Résultat de référence** : aucun effet distinct de zéro à 15, 30 ou 45 min. | référence |

## Phase C — Profils des stations (rapports 92–127)

### C1 — Conception des profils d'hiver

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 92 | 39 | [Recentrage hiver](../reports/92_AUDIT_HIVER_PROFILS_ET_CHOIX_FR.md) | Audit : hiver, profils de stations, expositions multiples. | historique → 93 |
| 93 | 40 | [Décisions hiver](../reports/93_DECISIONS_HIVER_CLUSTERING_ET_AJOUTS_FR.md) | Décembre–avril, variables continues, portefeuille initial. | référence (décisions) |
| 94 | 41 | [Préparation du clustering](../reports/94_PREPARATION_CLUSTERING_ET_AUDIT_AJOUTS_FR.md) | Peu de comparaisons strictes possibles pour les stations entrées plus tard. | historique |
| 95 | — | [Variables proposées](../reports/95_PROPOSITION_VARIABLES_PROFILS_FR.md) | Orientation, neige et accès aux grandes villes proposés comme dimensions. | historique → 96, 127 |
| 96 | 42 | [Cinq dimensions](../reports/96_AUDIT_DISPONIBILITE_CINQ_DIMENSIONS_FR.md) | Disponibilité des cinq dimensions pour les 71 groupes. | historique → 127 |
| 97 | 43 | [Décisions neige et accès](../reports/97_DECISIONS_PROFILS_NEIGE_ACCES_URBAIN_FR.md) | Minimum des six villes, calendriers propres à chaque entrée, pistes actuelles comme proxy. | référence (décisions) |

### C2 — Pistes : sources et rattachements

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 98 | 44 | [Sources pistes et neige](../reports/98_SOURCES_PISTES_ET_NEIGE_BILAN_FR.md) | Pistes OpenStreetMap archivées ; choix des sources de neige. | historique |
| 99 | 45 | [Règles validées](../reports/99_REPRISE_COLLECTE_OSHD_ET_REGLES_VALIDEES_FR.md) | Règles de profils validées ; reprise de la collecte OSHD. | historique |
| 100 | 46 | [Correspondances pistes](../reports/100_PISTES_CORRESPONDANCES_ET_REPRISE_NEIGE_FR.md) | Correspondances pistes–groupes à vérifier ; reprise de la neige. | historique |
| 101 | 47–48 | [Grilles neige](../reports/101_NEIGE_GRILLES_ET_SOURCES_PISTES_FR.md) | Première archive OSHD complète ; relief à 2 m validé (addendum). | historique |
| 102 | 49 | [Axes et surfaces](../reports/102_AXES_SURFACES_PISTES_ET_REPRISE_NEIGE_FR.md) | Rôles distincts des axes et des surfaces de pistes. | historique (règle valable) |
| 103 | 50 | [Vérification des tracés](../reports/103_VERIFICATION_TRACES_ET_OPTION_GIS_OFFICIEL_FR.md) | Vérification des tracés ; option des données officielles. | historique |
| 104 | 51 | [Premiers rattachements](../reports/104_RATTACHEMENTS_PISTES_OPTION_1_FR.md) | Vérification individuelle des pistes (option 1) : premier lot. | historique → 106 |
| 105 | 52 | [Deuxième lot](../reports/105_DEUXIEME_LOT_RATTACHEMENTS_PISTES_FR.md) | Dix correspondances supplémentaires. | historique → 106 |
| 106 | 53 | [Bilan complémentaire](../reports/106_BILAN_RATTACHEMENTS_PISTES_COMPLEMENTAIRES_FR.md) | 39 groupes sur 71 vérifiés. | historique → 125 |
| 107 | 54 | [Objets et liaison historique](../reports/107_AUDIT_OBJETS_PISTES_ET_LIAISON_HISTORIQUE_FR.md) | Contrôle des objets de pistes ; preuve de liaison Eischoll–Unterbäch. | historique |
| 108 | 55–56 | [Eischoll–Unterbäch](../reports/108_REGROUPEMENT_EISCHOLL_UNTERBAECH_FR.md) | Regroupement validé : 70 groupes. | référence (décision) |
| 109 | 57–59 | [Tronçons uniques](../reports/109_TRONCONS_UNIQUES_ET_CONTEXTE_PROFILS_FR.md) | Les tronçons superposés ne sont comptés qu'une fois. | référence (règle) |
| 124 | 78 | [Géométries manquantes](../reports/124_RATTACHEMENT_GEOMETRIES_MANQUANTES_FR.md) | 20 correspondances supplémentaires. | historique → 125 |
| 125 | 79 | [Périmètres complétés](../reports/125_PERIMETRES_COMPLETES_ET_GROUPES_VALIDES_FR.md) | La Dôle–Tuffes entière, Wilerallmi–Schwanden regroupé : 69 groupes, 67 cartographiés. | référence |
| 126 | 80 | [Géométries revues](../reports/126_GEOMETRIES_REVUES_ET_COUVERTURES_FR.md) | Revue individuelle, couvertures publiées ; complément français abandonné. | référence |

### C3 — Relief

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 110 | 60–61 | [St-Luc et préparation](../reports/110_ST_LUC_ET_PREPARATION_RELIEF_FR.md) | St-Luc–Chandolin ajouté ; méthode de relief préparée. | historique |
| 111 | 62–63 | [Pilote 2 m](../reports/111_PILOTE_RELIEF_2M_ET_COMPARAISON_MILLESIMES_FR.md) | Pilote swissALTI3D 2 m et comparaison des millésimes. | historique |
| 112 | 64 | [Orientation](../reports/112_EXPOSITION_CONTINUE_ET_DESCRIPTION_CARDINALE_FR.md) | Orientation mesurée par des composantes continues nord/sud et est/ouest. | référence (méthode) |
| 113 | 65–67 | [Relief étendu](../reports/113_RELIEF_ET_JONCTIONS_DE_MILLESIMES_FR.md) | Relief étendu à 40 groupes ; jonctions entre millésimes. | historique → 127 |

### C4 — Neige : comparaison des sources et profils

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 114 | 68 | [Préparation](../reports/114_PREPARATION_COMPARAISON_NEIGE_FR.md) | Ce qui est prêt pour comparer les sources de neige. | historique |
| 115 | 69–70 | [Poids natifs](../reports/115_NEIGE_GRILLES_NATIVES_ET_COUVERTURE_FR.md) | Pondération des cellules de grille par les pistes ; valeurs quotidiennes. | historique |
| 116 | 71 | [Spearman niveaux](../reports/116_DIAGNOSTIC_NEIGE_SPEARMAN_FR.md) | Concordance SPASS–OSHD des niveaux quotidiens. | historique |
| 117 | 72 | [Variations quotidiennes](../reports/117_DIAGNOSTIC_VARIATIONS_QUOTIDIENNES_NEIGE_FR.md) | Concordance des variations quotidiennes. | historique |
| 118 | 73 | [Unités et dates](../reports/118_COMPATIBILITE_NEIGE_UNITES_TEMPS_FR.md) | Compatibilité des unités, dates et modèles. | historique |
| 119 | 74 | [Unité SPASS](../reports/119_UNITE_HAUTEUR_NEIGE_SPASS_FR.md) | L'unité est très probablement le mètre, sans déclaration officielle. | référence (hypothèse) |
| 120 | 75 | [Comparaison en mètres](../reports/120_COMPARAISON_NEIGE_METRES_FR.md) | Les deux modèles diffèrent : en médiane, OSHD est environ 7 cm sous SPASS. | historique → 122 |
| 121 | 76 | [Huit hivers (en cours)](../reports/121_EXTENSION_COMPARAISON_NEIGE_HUIT_HIVERS_FR.md) | Points d'étape de l'extension à huit hivers. | historique → 122 |
| 122 | 76 | [Bilan huit hivers](../reports/122_BILAN_NEIGE_HUIT_HIVERS_ET_CHOIX_PROFILS_FR.md) | Les deux modèles ne sont pas raccordés ; choix de source pour les profils. | référence |
| 123 | 77 | [Profils SPASS préentrée](../reports/123_PROFILS_NEIGE_SPASS_PREENTREE_FR.md) | Profils neige des cinq hivers avant l'entrée (34 complets). | historique → 127 |

### C5 — Profils étendus et choix du clustering

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 127 | 81–83 | [Profils étendus](../reports/127_PROFILS_RELIEF_NEIGE_ET_CHOIX_CLUSTERING_FR.md) | Relief pour 67 groupes, neige préentrée pour 54 ; protocole de clustering proposé. | référence |

## Phase D — Base nationale membres + non-membres (rapports 128–129)

| N° | Étape | Rapport | Ce qu'il établit | Statut |
|---|---|---|---|---|
| 128 | 84–89 | [Clustering descriptif et base nationale](../reports/128_CLUSTERING_DESCRIPTIF_BASE_NATIONALE_FR.md) | Neige sur la décennie commune (67 groupes) ; inventaire de 69 groupes et 200 fiches suisses à vérifier. | référence |
| 129 | 90 | [Braunwald](../reports/129_BRAUNWALD_ACCES_ROUTIER_VALIDE_FR.md) | Arrivée Linthal validée et six temps routiers depuis les grandes villes. | référence |
| — | 91–94 | *(pas encore de rapport)* | Dossiers nationaux, neige des réseaux provisoires, préparation de Flumserberg : voir `PROJECT_STATE.md` et le journal. | en cours |
