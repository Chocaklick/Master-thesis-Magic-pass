# Guide du projet

Ce guide explique la logique du mémoire, les quatre phases de travail déjà réalisées et le vocabulaire utilisé dans les rapports, les tables et le code. Pour l'état courant, voir [`PROJECT_STATE.md`](../PROJECT_STATE.md) ; pour trouver un rapport précis, voir [`INDEX_RAPPORTS.md`](INDEX_RAPPORTS.md).

## 1. La logique d'ensemble

Le mémoire relie trois mondes qui n'ont pas la même unité d'observation :

```text
remontées mécaniques (1 805)
   └─> clusters de remontées (242, dont 162 reliés à une fiche)        [géographie, données fournies]
fiches de stations (271, catalogue Bergfex)                            [caractéristiques publiées]
   └─> groupes de stations Magic Pass (71 → 70 → 69 après regroupements) [unité de traitement]
         └─> communes ayant accès au groupe en ≤ 30 min de voiture      [exposition]
               └─> nuitées hôtelières communales mensuelles (HESTA, OFS) [résultat]
```

Deux règles traversent tout le projet :

- **Une station n'est pas une commune.** Les nuitées sont observées par commune ; une station peut desservir plusieurs communes et une commune peut avoir accès à plusieurs stations. Le lien se fait par l'**exposition** (accessibilité), jamais en attribuant arbitrairement les nuitées d'une commune à une station.
- **Corrélation ≠ effet causal ≠ prédiction ≠ recommandation.** Chaque résultat indique explicitement ce qu'il permet de dire.

La question finale (aide à la décision) : pour une station non membre, quelles stations membres lui ressemblent, qu'a-t-on observé autour de ces stations après leur entrée, et avec quelle incertitude ?

## 2. Les quatre phases

### Phase A — Mission initiale, faisabilité et « voie C » (20–26 septembre 2026, rapports 01–51)

- Audit des 11 fichiers fournis, registre de provenance, historique Magic Pass (93 événements officiels dont 88 entrées), panel de 11 destinations examinées.
- **Échec de l'identification causale** : la recherche de témoins (35 paires présélectionnées) s'épuise ; chaque témoin éloigné subit un choc local documenté. Les checkpoints 4–5 (causal et ML) échouent formellement ([rapport 17](../reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md)).
- **Voie C (« Path C »)** : segmentation k-means (k = 2) de 156 clusters sur trois variables structurelles (altitude, km de pistes, remontées), analogues pour 104 candidats non membres, tableau de bord à 7 dimensions sans score ni classement ([rapports 18–41](INDEX_RAPPORTS.md)).
- Brouillons de mémoire générés automatiquement (rapports 42–51) : ils ne reflètent **que** cette phase.

### Phase B — Exposition des communes et différences-en-différences (2–7 octobre 2026, rapports 52–91)

- Refonte demandée par le chercheur ([rapport 53](../reports/53_PLAN_ELARGISSEMENT_COMMUNES_STATIONS_FR.md)) : les 78 entrées suisses deviennent 71 groupes de stations ; chaque commune hôtelière est reliée à chaque groupe par un temps de trajet.
- Première version en transports publics (horaires GTFS, 120 min), pilote apparié non causal (−6,8 %, non robuste) puis estimation cohortes × mois sur toutes les cohortes : aucun effet distinct de zéro ([rapport 82](../reports/82_ESTIMATION_COHORTES_MOIS_OPTION_A_FR.md)).
- Critique de la fenêtre de 120 min et d'un défaut de codage des accès locaux ([rapport 84](../reports/84_AUDIT_ACCES_LOCAUX_SEUILS_FR.md)) → passage à la **voiture** (openrouteservice, arrêt communal → arrêt de station).
- **Résultat de référence** ([rapport 91](../reports/91_DID_ROUTIER_30MIN_SENSIBILITES_FR.md)) : à 30 min, 58 communes exposées dont 54 calculables ; aucune bande simultanée à 95 % n'exclut zéro, ni avant ni après l'entrée ; mêmes conclusions à 15 et 45 min.

### Phase C — Profils des stations (8–12 octobre 2026, rapports 92–127)

Objectif : décrire les stations membres pour étudier si l'effet dépend du profil (hétérogénéité), puis comparer avec les non-membres.

- Saison retenue : décembre–avril.
- **Pistes** : rattachement manuel, groupe par groupe, des tracés OpenStreetMap actuels (67 groupes sur 69 cartographiés ; La Braye et Riffenmatt sans géométrie).
- **Relief** : modèle swissALTI3D à 2 m → altitude, pente, orientation pondérées par la longueur des pistes (67 profils).
- **Neige** : produit modélisé SPASS (SLF, grille de 1 km, jusqu'en 2023), comparé à OSHD sans raccord. Deux versions : 5 hivers avant l'entrée de chaque groupe (54 profils) et décennie commune 2013/14–2022/23 (67 profils).
- **Accès urbain** : temps routier minimal depuis Bâle, Berne, Genève, Lausanne, Lugano ou Zurich (69 groupes).

### Phase D — Base nationale membres + non-membres (12 octobre 2026, rapports 128–129, étapes 84–94)

- Nouvelle direction : **clustering descriptif** des stations membres et non membres avant toute prédiction.
- Inventaire de 272 unités : 69 groupes existants, 200 fiches suisses à vérifier, 3 fiches étrangères autonomes (hors périmètre).
- Vérification documentaire au cas par cas (identité, périmètre, activité pendant la décennie commune, pistes) : six dossiers ouverts ; Braunwald entièrement traité (accès routier validé).

## 3. Ce qu'il faut retenir pour le mémoire

1. La base de données et sa traçabilité sont solides (registre de sources, dictionnaire, journal de collecte, tests).
2. Deux stratégies causales ont été tentées : les témoins de destinations (phase A) et l'exposition communale par accessibilité (phase B). Aucune ne montre d'effet moyen détectable du Magic Pass sur les nuitées ; ce résultat négatif est documenté et défendable.
3. Les profils de stations (phase C) permettent une segmentation descriptive plus riche que les trois variables de la voie C.
4. L'aide à la décision doit rester descriptive et fondée sur des analogues, avec une incertitude explicite, sans score de recommandation non justifié.

## 4. Vocabulaire

| Terme | Sens dans ce projet |
|---|---|
| Fiche (listing) | Une ligne du catalogue de stations fourni (271 fiches, `resort_id`). Plusieurs fiches peuvent décrire le même domaine. |
| Cluster de remontées | Regroupement géographique des remontées fourni au départ (`cluster_id`). Conservé tel quel, jamais recalculé. |
| Groupe de stations | Unité Magic Pass de la phase B et suivantes (`station_group_id`) : une ou plusieurs composantes entrées ensemble dans le pass. 69 groupes actuellement. |
| Territoire | Commune hôtelière harmonisée ; Moutier (BFS 700 puis 6831) compte pour un seul territoire → 185 territoires. |
| Exposition | Une commune est exposée à partir du mois où un groupe accessible dans le seuil (30 min) entre dans le Magic Pass. |
| Cohorte | Ensemble des communes exposées pour la première fois le même mois. |
| Témoins | Communes jamais exposées ou pas encore exposées au mois considéré (option C). |
| Voie C (Path C) | Stratégie de repli de la phase A : segmentation + analogues + tableau de bord, sans effet causal. |
| Préentrée | Mesuré avant l'entrée du groupe dans le Magic Pass (seul usage admissible pour expliquer un effet). |
| SPASS / OSHD | Deux produits de neige modélisée du SLF ; SPASS est utilisé, OSHD sert de comparaison. |
| swissALTI3D | Modèle altimétrique de swisstopo (2 m) utilisé pour le relief. |
| ORS | openrouteservice (HeiGIT), service de calcul des temps routiers. |
| HESTA | Statistique de l'hébergement touristique de l'OFS (nuitées, arrivées, capacité). |
| Étape (« stage ») | Unité de travail de Codex, numérotée de 1 à 94. Un fichier suffixé `_stageNN` a été produit à l'étape NN. Les numéros d'étapes ne sont pas ceux des rapports (correspondance dans [`INDEX_RAPPORTS.md`](INDEX_RAPPORTS.md)). |
| Version figée | Les anciennes versions d'une table ne sont jamais écrasées ; une nouvelle version porte un nouveau suffixe d'étape. Les versions à utiliser sont listées dans [`DONNEES_DE_REFERENCE.md`](DONNEES_DE_REFERENCE.md). |

## 5. Reprendre le travail

1. Lire [`PROJECT_STATE.md`](../PROJECT_STATE.md) : état actuel, décisions prises, décisions en attente.
2. Lire les rapports « référence » du thème concerné ([`INDEX_RAPPORTS.md`](INDEX_RAPPORTS.md)).
3. Utiliser les tables listées dans [`DONNEES_DE_REFERENCE.md`](DONNEES_DE_REFERENCE.md).
4. Pour le détail d'une décision passée : chercher la date ou l'étape dans [`logs/research_journal.md`](../logs/research_journal.md) ou dans l'archive [`docs/archive/`](archive/).
