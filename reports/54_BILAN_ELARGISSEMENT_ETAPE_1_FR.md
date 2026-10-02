# Bilan de la première étape d'élargissement

Inventaire local du 2 octobre 2026, conformément au [plan](53_PLAN_ELARGISSEMENT_COMMUNES_STATIONS_FR.md). Aucun nouveau trajet, regroupement de stations ou modèle n'a été calculé.

## Comptage comparable

| Unité comptée | Ancien périmètre | Inventaire élargi | Ajout |
|---|---:|---:|---:|
| Fiches de stations ayant une entrée Magic Pass directement identifiée | 15 composantes des 11 destinations du panel | 62 | +47 |
| Séries communales hôtelières, comparées au périmètre des résultats des 11 destinations | 12 | 186 | +174 |
| Territoires communaux distincts selon les limites 2026 | 12 | 185 | +173 |
| Communes supplémentaires par rapport aux calculs de trajets déjà existants | 186 origines déjà présentes | 186 | 0 |

Les **47 fiches ajoutées au registre de préparation** se décomposent en 44 dont la commune du point n'appartient pas au panel hôtelier, et trois domaines précédemment exclus pour périmètre composite incomplet : Gstaad, Sainte-Croix / Les Rasses et Villars-Gryon-Les Diablerets. Leurs 62 points de fiches sont résolus dans une commune suisse. La réduction par futurs regroupements n'est pas encore connue : 62 fiches ne signifient pas 62 domaines indépendants.

Les **174 séries communales supplémentaires** sont déjà stockées dans le projet ; aucun nouveau téléchargement n'a eu lieu. Elles deviennent disponibles pour examiner l'exposition aux nouvelles stations. Toutes les 186 séries ont au moins une valeur mensuelle de nuitées observée et une origine de transport existante. Moutier BE (BFS 700) et Moutier JU (BFS 6831) représentent deux séries administratives pour un seul territoire actuel ; elles ne doivent pas devenir deux communes indépendantes. Séries de moins de 24 mois observés : Laténa (6513) : 15 mois; Moutier (JU) (6831) : 3 mois. Le nombre avec des fenêtres avant/après suffisantes dépendra des adhésions examinées.

## Cas restant à résoudre

Sur 88 entrées de base, 10 destinations entièrement étrangères sont écartées du périmètre. Restent **78 événements**, soit 62 correspondances directes et **16 événements suisses ou à composante suisse en attente**. Parmi ces 16, quatre concernent une destination sans fiche propre : Château-d'Oex / La Braye, Grenchenberg, Mayens de Conthey et Wilerallmi. Les douze autres concernent des composantes ou périmètres chevauchants. Six fiches supplémentaires apparaissent dans les relations documentées, mais ces relations ne sont pas des identités validées et ne sont pas ajoutées aux 62. Le cas Jura sur Léman est limité à sa composante suisse à clarifier.

## Ce qui est effectivement intégré

Les cas figurent désormais dans les trois registres ci-dessous. **L'intégration porte sur le périmètre de préparation**, pas sur un panel final d'effets. Zéro nouveau couple station–commune a encore été validé par temps de trajet, et zéro nouvelle unité causale est approuvée. Le nombre finalement analysable ne peut être annoncé avant les contrôles d'identité, d'accès et de couverture temporelle. Arrêt à cette étape pour présentation au chercheur.

## Registres et reproduction

- [Stations identifiées](accessibility_expansion_station_inventory.csv) : une ligne par entrée liée à une fiche, avec identifiants d'origine, saison, méthode de lien, commune du point et motif d'ajout.
- [Événements en attente](accessibility_expansion_pending_events.csv) : les 16 cas, leurs preuves existantes et relations possibles. `integrated_as_station` reste faux.
- [Séries communales](accessibility_expansion_municipality_inventory.csv) : code BFS, observations disponibles, première/dernière observation, origine existante et doublons territoriaux.
- [Comptes et empreintes des entrées](accessibility_expansion_inventory_summary.json).

Reproduction depuis la racine : `python src/descriptive/audit_accessibility_expansion.py`. Les fichiers CSV sont des registres d'audit ; aucun nouvel indicateur analytique ou source externe n'est introduit. Les sources et variables d'origine restent référencées dans `metadata/data_sources_master.csv` et `metadata/data_dictionary.csv`.
