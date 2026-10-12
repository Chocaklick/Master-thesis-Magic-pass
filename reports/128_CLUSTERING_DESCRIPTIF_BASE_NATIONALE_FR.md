# Clustering descriptif : neige commune et préparation nationale

12 octobre 2026 — étapes 84–87. Objectif : décrire les similarités entre domaines, membres **et** non-membres du Magic Pass. Ni prédiction d’adhésion ou d’effet, ni nouveau DiD, ni classement de recommandations. Les anciennes versions restent conservées.

## 1. Les 13 groupes retrouvent une moyenne de neige

La fenêtre commune demandée est appliquée à tous les groupes : **dix hivers 2013/14–2022/23, décembre–avril**. Elle ne dépend ni de l’adhésion ni des résultats touristiques.

| Vérification | Résultat |
|---|---:|
| Groupes existants conservés | 69 |
| Groupes avec une moyenne sur les dix hivers | 67 |
| Parmi eux : couverture spatiale complète / partielle | 64 / 3 |
| Anciens groupes incomplets réexaminés / désormais avec dix hivers | 13 / 13 |
| Groupes encore sans géométrie utilisable | 2 : La Braye et Riffenmatt |

Les 13 lacunes précédentes venaient des fenêtres préentrée des cohortes récentes, qui dépassaient la fin de SPASS en 2023. **Aucun de ces 13 groupes ne reste sans moyenne décennale pour cette raison.** Ce n’est pas une imputation : les jours sources existent dans la nouvelle fenêtre.

| Groupe réexaminé | Hivers préentrée observés sur 5 | Hivers communs observés sur 10 | Couverture minimale des longueurs |
|---|---:|---:|---:|
| Grenchenberg | 3 | 10 | 100 % |
| Wilerallmi–Schwanden | 4 | 10 | 100 % |
| Balmberg | 3 | 10 | 100 % |
| Belalp | 3 | 10 | 100 % |
| Bergbahnen Gstaad | 3 | 10 | 100 % |
| Homberg | 4 | 10 | 100 % |
| La Dôle–Tuffes | 4 | 10 | 65,8 % |
| Linden | 3 | 10 | 100 % |
| Meiringen–Hasliberg | 3 | 10 | 100 % |
| Melchsee-Frutt | 3 | 10 | 86,4 % |
| Mörlialp | 3 | 10 | 100 % |
| Sörenberg | 3 | 10 | 100 % |
| Saint-Cergue | 4 | 10 | 100 % |

Le troisième profil spatialement partiel est Vallée de Joux : **94,3 %**. La couverture porte sur les axes cartographiés admissibles, pas sur la totalité certifiée des pistes réelles. Les portions ambiguës déjà laissées non mesurées restent distinguées. Aucun groupe n’est exclu automatiquement.

Fichiers : [profils décennaux](../data_processed/common_snow_profiles_stage84.csv), [détail des 13 cas](../data_processed/common_snow_reassessment_stage84.csv), [690 lignes groupe–hiver](../data_processed/common_snow_winter_stage84.csv).

## 2. Méthode neige : ce qui change et ce qui reste

Seule la fenêtre temporelle change. Les longueurs uniques de pistes admissibles et leurs intersections exactes avec les cellules SPASS natives restent celles de l’étape 80, sans interpolation, nouvelle tolérance ou déplacement des tracés.

Chaque jour, la hauteur modélisée est pondérée par les longueurs réellement couvertes. Chaque hiver est ensuite la moyenne de ses jours observés ; la moyenne décennale donne **1/10 à chacun des dix hivers**, même lors des années bissextiles. Un hiver entièrement absent laisserait cette moyenne manquante. Les vrais zéros sont conservés ; aucune valeur n’est inventée.

Calcul vérifiable : **1 512 dates par groupe mesurable, 101 304 lignes groupe–jour, 670 moyennes hivernales observées**. Les 20 autres lignes groupe–hiver restent manquantes faute de géométrie. Les caches sources déjà disponibles sont réutilisés ; aucune nouvelle collecte neige et aucun raccordement OSHD.

SPASS est une **hauteur de neige modélisée**, pas une mesure sur chaque piste. L’hypothèse de mètres précédemment validée est conservée ; l’attribut d’unité original absent n’est pas réécrit. La période commune peut contenir des années postérieures à l’adhésion : elle est descriptive et **ne remplace jamais les profils préentrée** pour un usage causal ou prédictif. Les tracés et le relief restent des proxies actuels avec leurs réserves historiques.

## 3. Extension nationale : préparation, pas encore 269 domaines vérifiés

Le catalogue existant contient **271 fiches**, dont **268 points dans les communes suisses**. Trois fiches étrangères autonomes sont conservées dans l’audit mais hors périmètre de préparation suisse. Cela ne justifie pas de couper les groupes transfrontaliers déjà validés.

La nouvelle version réunit les **69 groupes existants** et **200 fiches suisses supplémentaires à vérifier**. Il ne faut pas additionner ces lignes comme des domaines indépendants : plusieurs fiches peuvent décrire le même domaine, un secteur ou un ancien réseau.

Une correction de doublon est documentée : la fiche **Rougemont–La Videmanette** est raccordée au périmètre de Gstaad qui incluait déjà Eggli–Videmanette dans l’étape 79. La page officielle archivée confirme cette identité. Ce n’est ni une nouvelle fusion physique ni un changement des 132 objets de pistes retenus. L’identifiant original est gardé ; anciennes mesures, expositions et nuitées ne changent pas.

Parmi les 200 fiches suisses restantes, 119 ont un indice de regroupement dans les anciens clusters de remontées, dont 13 partagent un cluster avec un groupe existant. **Ce sont des indices de recherche, pas des preuves de liaison.** Les 162 anciens clusters ne sont ni reconstruits ni transformés automatiquement en domaines. Les 238 relations de sites OSM déjà archivées sont inventoriées pour vérification documentaire.

L’absence de correspondance avec le catalogue Magic Pass n’est pas une non-adhésion certifiée : **192 fiches sans lien résolu**, 8 avec un lien candidat dont le périmètre reste à vérifier. Elles sont toutes conservées pour la préparation nationale ; l’adhésion ne sert pas à calculer les similarités.

Fichiers : [inventaire national courant](../data_processed/national_similarity_inventory_stage86.csv), [271 identifiants et caractéristiques sources](../data_processed/national_similarity_listing_lineage_stage86.csv), [variables comparables et couvertures](../data_processed/national_similarity_feature_context_stage86.csv), [sites OSM à examiner](../data_processed/national_similarity_piste_site_inventory_stage85.csv). L’inventaire initial de l’étape 85 reste disponible pour comparaison.

## 4. Variables : réutilisation sans mélange de définitions

| Bloc | Déjà comparable dans les groupes existants | Prudence pour les nouvelles fiches |
|---|---|---|
| Taille et relief | Longueur d’axes uniques, altitude pondérée, composantes nord/sud et est/ouest | Altitude sommitale, kilomètres et nombre de remontées du catalogue restent des champs distincts, non datés ; pas de sommes entre fiches qui se chevauchent |
| Neige | Dix hivers communs ; couvertures temporelles et spatiales publiées | Étendre les mêmes poids après vérification des pistes, pas une extraction arbitraire au point de station |
| Accès urbain | Minimum des six villes et six trajets détaillés déjà validés | Les temps zonaux ARE et le plus proche arrêt BAV ne remplacent pas automatiquement les mêmes trajets ORS vers des départs vérifiés |

Les six champs précédemment envisagés sont disponibles pour **67 groupes existants**. C’est un constat de disponibilité, **pas un échantillon national accepté ni un clustering réalisé**. Pour les nouvelles fiches, les mesures physiques comparables restent manquantes jusqu’à validation de leur identité et de leur périmètre. Les chiffres de catalogue sont conservés séparément ; 11 fiches suisses ont au moins un des trois chiffres structurels absent. Les nuitées et la capacité hôtelière communales ne sont pas attribuées arbitrairement aux stations.

## 5. Sources, contrôles et reprise

Sources originales inchangées : SPASS ([EnviDat, DOI 10.16904/envidat.580](https://doi.org/10.16904/envidat.580)), OSM archivé et sites complétés, swissALTI3D 2 m, ancien catalogue Bergfex, conteneurs communaux geo.admin, catalogue Magic Pass archivé, ARE/BAV et trajets ORS déjà récoltés. Preuve du raccordement Videmanette : [opérateur officiel](https://bergbahnen-gstaad.ch/fr/hiver/activites/activites/nos-montagnes/la-videmanette-eggli), archive `GSTAAD_EGGLI_STAGE79` du 11 octobre et périmètre explicite de l’étape 79. Pas de nouvelle affirmation d’état courant à partir de ces snapshots.

Premier contrôle des étapes 84–87 : trois sources dérivées et 171 champs ajoutés ; audit **3 127 fichiers vérifiés, dont 3 087 historiques inchangés**, et **73 tests réussis**. Huit taux de champs vides ont été corrigés dans les nouvelles métadonnées seulement, sans changer les valeurs ou producteurs figés. Les tests et le journal consignent aussi les tentatives échouées.

L’extension documentaire suivante ouvre six dossiers : Avers, Bivio, Braunwald, Elm, Feldis et Flumserberg. **Huit originaux archivés**, un communiqué détaillé refusé (403), aucun contournement. La [file de préparation des 200 fiches](../data_processed/national_preparation_work_queue_stage88.csv) indique les sources, les 35 fiches avec indices de sites OSM déjà disponibles et le travail restant. Ce lot n’est pas un échantillon d’analyse et ne produit pas encore six nouveaux profils. Registres courants après cette collecte et la vérification d’accès : **1 648 sources, 9 113 champs, 2 488 événements**.

Contrôle final : audit étape 89 **3 162 fichiers vérifiés / 3 127 du contrôle précédent inchangés**, anciens registres préservés. **79 tests distincts réussis en lots**, dont 19 tests des nouvelles étapes dans le dernier lot ; aucune tâche de collecte ou de calcul active.

Reprise : vérifier les identités, les opérateurs et les liaisons des 200 fiches ; rattacher explicitement leurs pistes, puis étendre les mêmes mesures terrain/neige et les accès vérifiés. Ni rapprochement automatique par nom/distance, ni exclusion selon une significativité. Les sorties et caches terminés des étapes 84–86 ne sont pas à refaire.

**Trois validations supplémentaires reçues :** domaine transfrontalier connecté entier avec couvertures partielles ; activité de ski documentée pendant au moins un hiver de 2013/14–2022/23 avec statut actuel séparé ; maintien des arrêts de station vérifiés pour l’accès aux six villes. Décisions enregistrées dans les configurations des étapes 88–89. Cette règle d’activité sera vérifiée pour les nouveaux domaines et les anciens groupes, en réutilisant leurs preuves historiques ; un historique non encore audité reste en attente, pas exclu.

Braunwald illustre la distinction : son [rapport officiel 2019/20, page 4](https://sportbahnen-braunwald.ch/files/sportbahnen-braunwald.ch/media/PDFs/Gesch%C3%A4ftsbericht_2019-20%20%281%29.pdf) documente le ski pendant la décennie ; la [page hivernale de l’opérateur](https://sportbahnen-braunwald.ch/de/informationen/winter.html) annonce désormais son arrêt. L’activité passée le rend admissible à la préparation, sans certifier ses géométries historiques.

**Arrivée de Braunwald désormais validée et utilisée (étape 90) :** le chercheur a approuvé **Linthal Braunwaldbahn (Talst.), BAV 8503260**, arrêt inférieur du funiculaire. Le plus proche arrêt BAV du point de catalogue était un télésiège, pas une arrivée routière ; l’[opérateur limite les voitures à Linthal](https://sportbahnen-braunwald.ch/de/informationen/anreise.html). Les six temps routiers sont maintenant disponibles : minimum **83,5 min depuis Zurich**, voiture seule jusqu’à Linthal. Funiculaire et accès aux pistes restent non mesurés, jamais zéro. [Bilan et tableau étape 90](129_BRAUNWALD_ACCES_ROUTIER_VALIDE_FR.md). Le [dossier de proposition](braunwald_road_arrival_proposal_stage89.json) demeure figé dans son état historique ; la validation et la collecte sont conservées dans une nouvelle version. Aucune station n’est retirée et l’arrivée n’est plus en attente. Les nombres de registres cités plus haut décrivent le jalon précédent ; bilan 129 et journal donnent les nouveaux totaux.

Le complément français de La Dôle reste annulé ; aucun nouveau relief étranger n’est autorisé implicitement. Variables finales, transformations, algorithme, nombre de classes et traitement des couvertures seront présentés après la vérification de la base nationale ; le précédent choix 54/67 est devenu caduc. Aucune prédiction, estimation causale ou partition descriptive n’a été lancée.
