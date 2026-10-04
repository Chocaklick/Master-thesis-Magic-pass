# Données complémentaires OFS pour les communes — 5 octobre 2026

Les quatre liens proposés apportent des informations nouvelles au projet. La recherche initiale dans les registres, scripts et configurations ne trouvait ni cette typologie, ni l'IMPI, ni les nouvelles constructions résidentielles, ni ces séries économiques touristiques. La population et les capacités hôtelières étaient déjà présentes, mais ne mesurent pas les mêmes choses. Le chercheur a explicitement demandé de conserver également les séries agrégées comme contexte.

## Sources et intérêt

| Lien proposé | Données identifiées et intégrées | Utilité et limites |
|---|---|---|
| [1 — Typologie des communes](https://www.agvchapp.bfs.admin.ch/fr/typologies/results?SnapshotDate=01.01.2026&SelectedTypologies%5B0%5D=HR_GDETYP2020) | Typologie 2020 en 3, 9 et 25 catégories ; état administratif du 1er janvier 2026 ; 2 110 communes. | Décrire la structure territoriale, distinguer communes urbaines, intermédiaires, rurales et catégories touristiques. Catégories nominales : les nombres ne constituent pas une échelle de distance. |
| [2 — Prix de l'immobilier](https://www.bfs.admin.ch/bfs/fr/home/statistiques/prix/prix-immobilier.html) | Indice résidentiel IMPI, 2017 T1–2026 T2 : logements en propriété, maisons individuelles et appartements, au total et pour cinq types de communes. | Contexte trimestriel d'évolution des prix, base 2019 T4 = 100. Aucun prix communal en CHF/m², prix de location ou prix hôtelier. |
| [3 — Nouveaux bâtiments avec logements](https://www.bfs.admin.ch/asset/fr/px-x-0904030000_106) | Nombre de bâtiments terminés contenant des logements, total et quatre types ; années 2013–2024 ; géographie fixée au 31 décembre 2024. | Activité de construction résidentielle pour la comparaison descriptive et de futurs diagnostics. Ce sont des bâtiments, pas des logements, des lits hôteliers, une part de résidences secondaires ou des dépenses d'investissement. |
| [4 — Investissements et compte satellite du tourisme](https://www.bfs.admin.ch/bfs/fr/home/statistiques/catalogues-banques-donnees.gnpdetail.2025-0367.html) | Publication du 17 novembre 2025 : investissements 1995–2023 et indicateurs économiques du tourisme 2001–2024. | Contexte des communes touristiques agrégées, des cantons GR/UR/VS et de l'économie touristique suisse. Aucun investissement individualisé pour chacune des communes du projet. |

## Couverture des territoires étudiés

Le fichier `municipality_comparison_context_2026.csv` contient exactement les **185 territoires analytiques** de l'univers territorial approuvé, avec une jointure univoque par identifiant OFS. La typologie les couvre tous : 93 urbains, 46 intermédiaires et 46 ruraux. 56 relèvent des catégories touristiques officielles 134, 314 ou 334. Cette distribution décrit l'univers existant ; elle n'en sélectionne pas un sous-ensemble.

La construction couvre **184 territoires**, avec 11 040 lignes = 184 × 12 années × 5 types de bâtiments. Laténa (6513), créée en 2025, est absente du référentiel de 2024. Son absence reste explicite ; aucun de ses prédécesseurs n'est agrégé automatiquement. Pour Moutier, le numéro source 700 reste conservé et correspond au territoire analytique 6831 selon le raccordement officiel déjà autorisé (`BFS_MUNICIPAL_MUTATION_3999`).

Un audit supplémentaire conserve les **1 295 lignes territoire × cohorte** existantes. Il extrait le total des bâtiments pour l'année civile complète immédiatement antérieure à l'année d'entrée : par exemple 2016 pour novembre 2017, 2021 pour mai 2022. 1 288 valeurs sont disponibles ; les sept autres correspondent à Laténa. Les totaux de l'année d'entrée ne sont jamais utilisés comme caractéristique antérieure. Cette règle temporelle ne valide pas à elle seule la comparabilité des périmètres historiques, l'exogénéité ou l'usage causal.

## Précautions temporelles et géographiques

- La [méthode OFS de la typologie 2020](https://www.swissstats.bfs.admin.ch/data/webviewer/appId/ch.admin.bfs.swissstat/article/issue242122982000-05/package) utilise notamment population et emploi de 2019–2021 et nuitées de 2018, 2019 et 2022. Cette typologie peut donc incorporer des résultats observés après certaines entrées au Magic Pass. Elle est intégrée comme contexte descriptif actuel, sans autorisation automatique de matching avant traitement.
- L'IMPI est un indice d'évolution, pas une comparaison des niveaux de prix entre communes. Ses cinq types ne sont pas assimilés automatiquement aux codes de la typologie 2020. Aucune série immobilière agrégée n'est attribuée aux communes.
- La géographie de construction au 31 décembre 2024 s'applique à toutes les années du cube. Un identifiant identique n'établit pas que les frontières d'une commune ont toujours été identiques. Aucun nouveau raccordement historique n'est décidé ici.
- Les séries d'investissement sont à prix courants, en **milliers de CHF**, et couvrent uniquement les maîtres d'ouvrage résidents. Elles distinguent total, nouvelles constructions et transformations. Les parts cantonales et nationales sont conservées en **pourcentage**. Six cellules « X » restent confidentielles/manquantes, jamais nulles.
- Les indicateurs du compte satellite portent sur la Suisse : VAB et dépenses en **millions de CHF**, emploi en **équivalents plein temps**, taux de croissance et parts en **pourcentage**. Les totaux, sous-totaux et lignes « dont » ne doivent pas être additionnés ensemble. Les résultats 2024 sont provisoires dans cette publication ; la révision 2025 des comptes nationaux n'y est pas encore incorporée. La version de novembre 2025 est volontairement conservée et datée.
- Avec des effets fixes pour chaque mois calendaire, une série nationale commune à toutes les communes peut être absorbée par ces effets. Sa présence dans le dépôt ne justifie pas automatiquement son inclusion dans une régression. Les constructions après entrée peuvent aussi être un résultat ou un médiateur.

## Fichiers intégrés

| Table dans `data_processed/` | Lignes | Grain |
|---|---:|---|
| `municipality_typology_2020_snapshot_2026.csv` | 2 110 | Commune OFS au 1er janvier 2026 |
| `municipality_comparison_context_2026.csv` | 185 | Territoire analytique actuel |
| `municipality_new_residential_buildings_year.csv` | 11 040 | Commune source × année × type de bâtiment |
| `municipality_new_buildings_cohort_baseline_audit.csv` | 1 295 | Territoire × cohorte ; disponibilité de l'année précédente |
| `bfs_residential_property_price_index_quarter.csv` | 684 | Trimestre × logement × type communal agrégé/total |
| `bfs_tourism_investments_tourist_municipalities_year.csv` | 783 | Année × genre de travaux × catégorie d'ouvrage |
| `bfs_tourism_investments_alpine_context_year.csv` | 1 044 | Année × agrégat/canton × ouvrage × montant/part |
| `bfs_tourism_satellite_national_context_year.csv` | 2 304 | Année × produit/indicateur économique suisse |

Les classeurs proviennent des assets OFS [IMPI 36754186](https://dam-api.bfs.admin.ch/hub/api/dam/assets/36754186/master), [investissements à huit catégories 36217219](https://dam-api.bfs.admin.ch/hub/api/dam/assets/36217219/master), [cantons alpins 36217222](https://dam-api.bfs.admin.ch/hub/api/dam/assets/36217222/master), [valeurs économiques 36217227](https://dam-api.bfs.admin.ch/hub/api/dam/assets/36217227/master) et [parts nationales 36217232](https://dam-api.bfs.admin.ch/hub/api/dam/assets/36217232/master). Le chemin de découverte depuis les pages proposées est archivé, avec requêtes, réponses, dates et SHA-256. Chaque valeur Excel exportée conserve son classeur/source, son onglet et sa cellule.

## Anomalies et contrôles

L'onglet **2024** du fichier CST porte un titre mentionnant **2023**. L'année de l'onglet est utilisée et le titre original est conservé dans l'export ; la publication décrit explicitement une série allant jusqu'en 2024. Les fichiers CST de valeurs et de parts contiennent également une très petite différence dans leur total de VAB 2002, d'environ 0,000494 million de CHF. Les deux valeurs officielles restent distinctes, avec leur provenance ; aucune correction arbitraire n'est appliquée.

Le téléchargement des constructions a enregistré sa réponse et sa requête avant une erreur de sérialisation d'un identifiant NumPy dans la métadonnée. Les fichiers locaux ont été récupérés et vérifiés sans nouveau téléchargement. L'échec et la récupération sont tous deux conservés dans le journal de collecte ; le statut HTTP non persisté n'est pas reconstitué par supposition.

Les contrôles portent sur l'unicité et la couverture des identifiants, la distinction des zéros et des valeurs manquantes, la restitution de toutes les cellules numériques originales, la confidentialité, les unités et l'antériorité des années de baseline. Le panel territorial de nuitées/exposition reste identique à son empreinte initiale. Aucun filtre, appariement, estimateur ou nouveau résultat causal n'est produit.

## Reproduction et reprise

Depuis la racine du projet :

1. `python src/data_collection/collect_evidence.py --config config/municipality_additional_evidence_sources.json` et `python src/data_collection/collect_municipality_new_buildings.py` collectent les réponses ou réutilisent les caches vérifiés.
2. Exécuter `src/data_processing/extract_optional_bfs_workbooks.py` avec le runtime Python fourni par la compétence Spreadsheets (openpyxl en lecture seule). L'intermédiaire est écrit dans `data_interim/municipality_additional_context/workbooks.json`. Aucun chemin utilisateur n'est codé dans les scripts.
3. `.venv/Scripts/python.exe src/data_processing/build_municipality_additional_context.py` reconstruit les huit tables, le bilan JSON et les ajouts aux deux registres de métadonnées.
4. `.venv/Scripts/python.exe -m pytest -q` vérifie le projet.

La provenance passe de 233 à **250 sources**, et le dictionnaire de 5 768 à **5 910 définitions**. Le [bilan JSON](municipality_additional_context_summary.json) conserve les empreintes et les tailles. Ces ajouts précèdent la reprise de l'étape 30 : l'estimateur, la saisonnalité, la référence, les pondérations, l'incertitude et le traitement des trois préhistoires de fusion manquantes restent à préciser avec le chercheur.
