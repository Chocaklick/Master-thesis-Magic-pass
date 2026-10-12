# Profils de stations : relief, neige et prochaine validation

12 octobre 2026. Suite du [bilan126](126_GEOMETRIES_REVUES_ET_COUVERTURES_FR.md). Aucun nouveau DiD ou clustering estimé.

## Résultat de l'extension

| Élément | Avant | Maintenant |
|---|---:|---:|
| Groupes avec profil de relief observé | 40 | **67** |
| Groupes avec moyenne neige disponible sur leurs cinq hivers | 34 | **54** |

Les **69 groupes reliés, 71 identités originales et 185 territoires communaux restent conservés**. Les anciens résultats ne sont pas remplacés. Les nuitées restent communales ; les cellules de relief et journées neige ne deviennent pas des stations indépendantes.

Deux groupes restent sans tracés mesurables : La Braye et Riffenmatt. Treize autres ont des fenêtres neige incomplètes : leur moyenne des cinq hivers reste manquante. Les 54 moyennes disponibles comprennent 53 couvertures spatiales complètes et une partielle, Vallée de Joux (94,3 % de longueur observée). Ce sont des disponibilités, pas des exclusions décidées selon des résultats.

## Relief et neige : méthode conservée

Le plan exact des cellules et des neuf voisins de Horn nécessite 635 tuiles suisses natives à 2 m : **326 originaux réutilisés, 309 nouveaux téléchargements**, avec sommes de contrôle officielles et en-têtes vérifiés. Aucun relief français récolté. Les cinq clés absentes du catalogue concernent La Dôle–Tuffes et restent manquantes.

Les cellules sources sont réutilisées pour 39 réseaux géométriquement identiques. Les 28 extractions nouvelles comprennent Moosalp après retrait des seules portions ambiguës de la mesure : il y a donc 27 profils supplémentaires, pas 28 nouveaux groupes.

La Dôle conserve une couverture d'altitude de **65,8 % du réseau mesurable** : pas un profil complet du domaine. Sept groupes ont de petites jonctions entre éditions différentes, dont Gstaad nouvellement calculé ; altitude conservée, pente/orientation manquantes sur ces seules portions selon la règle validée. Les résumés portent sur les longueurs observées, couvertures séparées, sans interpolation ni exclusion.

Les cinq réseaux avec pistes ambiguës restent signalés comme au bilan126. Les kilomètres sont ceux des axes OSM uniques mesurables, pas une longueur officielle exhaustive. Les surfaces ne sont jamais transformées en axes.

Pour la neige, cinq hivers propres à chaque entrée, décembre–avril, sont conservés. Les deux calendriers identiques des parents Wilerallmi–Schwanden sont représentés une seule fois : **345 lignes groupe–hiver**, sans toucher à l'ancien fichier de 350 lignes.

Les 55 mois nécessaires réutilisent 324 cellules déjà en cache et lisent 315 cellules supplémentaires dans l'original SPASS, sans collecte météo. **313 moyennes hivernales** sont observées. Pour les 39 réseaux inchangés, la différence maximale des moyennes des cinq hivers avec l'ancien calcul est de 6,7 × 10⁻¹⁶ m, uniquement de précision numérique.

Méthode : moyenne quotidienne pondérée par les longueurs observées, moyenne des jours observés par hiver, puis poids égal des cinq hivers. Un hiver entièrement absent empêche la moyenne des cinq. Zéros conservés, trous non comblés, négatifs signalés. SPASS seul, aucun complément OSHD. L'hypothèse mètres validée reste distincte de la déclaration originale UNKNOWN.

## Choix du clustering à valider

**Aucune catégorie n'est encore ajustée.** Le clustering de profils serait une segmentation distincte des anciens clusters de remontées et des regroupements de stations reliées, qui restent intacts.

Les six villes validées — Bâle, Berne, Genève, Lausanne, Lugano et Zurich — ont chacune une référence routière existante pour les 69 groupes : 414 lignes. Aucun nouveau routage ni changement des seuils DiD de 15/30/45 minutes. Ces références actuelles arrêt→arrêt ne sont pas les origines réelles des visiteurs.

- **A proposée : 54 avec neige en principal, 67 sans neige en sensibilité.** La dimension climatique est conservée, mais les entrées récentes aux calendriers incomplets ne sont pas classées automatiquement par le premier modèle.
- **B : 67 sans neige en principal, 54 avec neige en sensibilité.** Couverture plus large, mais l'enneigement n'intervient pas dans la segmentation principale.

Les 69 groupes restent dans les données dans les deux cas ; les deux sans géométrie restent non classés, sans imputation.

Six variables proposées : kilomètres mesurables, altitude moyenne pondérée, composantes nord/sud et est/ouest, moyenne neige préentrée, minimum des six temps urbains. La variante sans neige utilise les cinq autres. Concentration des orientations et parts cardinales restent descriptives. Aucune capacité hôtelière communale n'est attribuée arbitrairement à une station.

**Protocole proposé, non appliqué :** logarithme des kilomètres et temps positifs, puis standardisation ; comparaison Ward/k-means pour deux à cinq catégories ; stabilité, silhouette et interprétabilité. Les nuitées et effets DiD ne servent pas à former ou sélectionner les catégories. Les catégories et leur interprétation seront présentées avant l'analyse des différences d'effet.

Limites : domaines OSM incomplets, proxies géographiques/routiers actuels non certifiés préentrée, neige sur des fenêtres différentes selon la cohorte, corrélation altitude–neige pouvant donner davantage de poids au climat. Standardiser ne corrige pas ces problèmes. Les couvertures partielles restent visibles, sans filtre automatique.

## Fichiers, sources et reprise

- [Profils de relief](../data_processed/terrain_reviewed_profiles_stage82.csv) : 69 groupes, altitudes/pentes/orientations et couvertures.
- [Profils neige des cinq hivers](../data_processed/spass_reviewed_profiles_stage83.csv) : 69 groupes, 54 moyennes et raisons des lacunes.
- [Détail hivernal](../data_processed/spass_reviewed_winter_stage83.csv) et [calendriers dérivés](../data_processed/spass_reviewed_windows_stage83.csv) : 345 lignes chacun, identifiants parents et fenêtres originales.

Sources : swisstopo swissALTI3D (attribution Office fédéral de topographie swisstopo), original SLF SPASS et politique WSL, géométries OSM versionnées sous ODbL, anciens trajets ORS archivés. Nouveaux originaux immuables dans data_external/source_evidence ; sources et variables enregistrées au registre et au dictionnaire. Stage81 conserve queue/événements, Stage82 relief/cellules, Stage83 neige/calendriers/caches. Les producteurs et manifestes figent leurs sources et sorties.

Ne pas refaire la collecte terminée, modifier les anciens caches ou rechercher du relief français. Ne pas présenter les 54 profils disponibles comme 54 effets identifiés. **Reprise : recevoir les validations du périmètre et du protocole**, puis segmentation versionnée, jamais choix des groupes selon une significativité.

Vérifications terminées : **60 tests combinés réussis** (61,46 s), dont neuf nouveaux ; audit de 3 087 fichiers, avec les 2 189 historiques et préfixes des registres exacts. Sources/dictionnaire/log : 1 634 / 8 924 / 2 470 lignes. Aucun job actif.
