# AGENTS.md — règles pour les assistants IA (Codex, Claude…)

## Démarrage de session

Lire, dans cet ordre : `PROJECT_STATE.md` (état actuel, décisions prises et en attente), `docs/GUIDE_DU_PROJET.md` (logique et vocabulaire), ce fichier, puis les dernières entrées de `logs/research_journal.md`. Consulter `docs/INDEX_RAPPORTS.md` et `docs/DONNEES_DE_REFERENCE.md` pour trouver les rapports et les tables à jour, et inspecter les sorties existantes avant de refaire un travail.

Lire ensuite `prompts/main_research_prompt.md`, la mission de référence. Suivre sa séquence de recherche, ses garde-fous de faisabilité et ses checkpoints, en tenant compte des dernières directives du chercheur. Préserver le clustering de remontées existant et la distinction entre l'affectation des remontées aux stations et l'exposition des communes.

## Règles de fond

- Python est le langage principal ; lancer les scripts importants depuis la racine du projet.
- Chemins relatifs au projet ou configuration centralisée ; ne jamais commiter de chemin absolu propre à un utilisateur.
- `data_raw/` et les originaux de `data_external/` sont immuables. Les données dérivées vont dans `data_interim/` ou `data_processed/` et n'écrasent jamais une source.
- Ne jamais inventer de données, définitions, sources, valeurs manquantes, identifiants ou provenance. Signaler explicitement l'incertitude (`NA`, `UNKNOWN`).
- Enregistrer toute source externe dans `metadata/data_sources_master.csv` et toute variable analytique comprise dans `metadata/data_dictionary.csv`.
- Ne pas reconstruire le clustering de remontées existant sans justification documentée et approbation.
- Garder distinctes l'affectation remontée/cluster → station et l'affectation station/destination → commune pour les nuitées.
- Conserver les identifiants stables (`resort_id`, `cluster_id`, `station_group_id`, `municipality_id`, `bfs_id` / `municipality_bfs_id`) et les noms d'origine ; ne jamais utiliser un nom comme seule clé.
- Les variables de traitement doivent être historiquement exactes. Utiliser des informations préentrée pour les variables de recommandation prédictive, sauf justification explicite.
- Éviter les fuites d'information : les observations mensuelles d'une même station ne sont pas des stations indépendantes ; préférer une validation groupée et temporelle à un découpage aléatoire des lignes.
- Un package causal ne rend pas une estimation causale : énoncer hypothèses, stratégie d'identification, diagnostics et limites.
- Préférer des méthodes interprétables et défendables à une complexité inutile. Documenter les échecs et les résultats négatifs.
- Rendre les collectes longues reprenables avec des points de contrôle ; ne pas répéter des téléchargements ou des vérifications manuelles terminés sans raison documentée.
- Ne pas supprimer de résultats de recherche existants ni réécrire l'historique Git sans justification et approbation explicites.

## Documentation

- `README.md` est une **page d'entrée stable** : objectif, organisation, installation. N'y ajouter aucun compte rendu d'étape.
- `PROJECT_STATE.md` décrit **l'état actuel** : le **réécrire** (remplacer, ne pas empiler de nouvelles sections) à la fin de chaque travail important, en restant court. Y garder les décisions prises, les décisions en attente, le travail en cours et la reprise technique.
- `logs/research_journal.md` est le **seul historique chronologique** : y ajouter une entrée datée à la fin de chaque travail important (tâche, raison, méthode, résultat, problèmes, décision, suite).
- Chaque nouveau rapport `reports/NN_*.md` doit être ajouté à `docs/INDEX_RAPPORTS.md` (avec son étape et son statut), et le statut des rapports qu'il remplace doit être mis à jour.
- Chaque nouvelle version de table de référence doit être reportée dans `docs/DONNEES_DE_REFERENCE.md`.
- Rédiger la documentation et les rapports en français clair, avec une ponctuation et des espaces normaux.

## Organisation des fichiers

- Ne pas renommer ni déplacer les fichiers de `src/`, `tests/`, `config/`, `data_processed/`, `reports/` et `metadata/` : les scripts et les tests utilisent des chemins écrits en dur, et les contrôles de préservation comparent les fichiers à l'historique Git (`git show`).
- Les nouveaux fichiers suivent les conventions existantes (suffixe `_stageNN` pour une nouvelle version d'une table).

## Git et sécurité

- Vérifier `git status` avant tout changement important et commiter des étapes cohérentes.
- Ne jamais commiter `.venv/`, des caches, des secrets, des identifiants ni des données volumineuses ou propriétaires non revues. Le dépôt GitHub est **public**.
- Ne jamais forcer un push ni supprimer de branche distante sans autorisation explicite.
