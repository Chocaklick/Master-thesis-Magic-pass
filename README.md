# Mémoire de Master — Magic Pass, stations de ski et nuitées communales

Espace de travail reproductible (Python) d'un mémoire de Master en Business Analytics à l'Université de Lausanne.

## La question

L'entrée d'une station dans le **Magic Pass** a-t-elle un effet observable sur les **nuitées hôtelières des communes** qui ont accès à cette station ? Et peut-on s'appuyer sur les stations membres au **profil similaire** pour repérer les stations non membres pour lesquelles une entrée aurait le plus de potentiel ?

La mission complète (questions de recherche, garde-fous méthodologiques, livrables attendus) se trouve dans [`prompts/main_research_prompt.md`](prompts/main_research_prompt.md). Principe constant : ne jamais confondre corrélation, effet causal, prédiction et recommandation.

## Par où commencer

| Je veux… | Lire |
|---|---|
| savoir où en est le projet et ce qui reste à décider | [`PROJECT_STATE.md`](PROJECT_STATE.md) |
| comprendre la logique, les phases et le vocabulaire | [`docs/GUIDE_DU_PROJET.md`](docs/GUIDE_DU_PROJET.md) |
| retrouver un rapport (01 à 129) et savoir s'il est encore d'actualité | [`docs/INDEX_RAPPORTS.md`](docs/INDEX_RAPPORTS.md) |
| savoir quelle table de données utiliser | [`docs/DONNEES_DE_REFERENCE.md`](docs/DONNEES_DE_REFERENCE.md) |
| retracer une décision ou une étape passée | [`logs/research_journal.md`](logs/research_journal.md) (journal chronologique) |
| connaître la source exacte d'une donnée | `metadata/data_sources_master.csv`, `metadata/data_dictionary.csv` et [`reports/DATA_SOURCES.md`](reports/DATA_SOURCES.md) |

Les anciennes versions longues du README et de l'état du projet (jusqu'au 12 octobre 2026) sont conservées telles quelles dans [`docs/archive/`](docs/archive/).

## Organisation du dépôt

```text
prompts/          Mission de recherche (document de référence)
docs/             Guide, index des rapports, tables de référence, archives de documentation
config/           Paramètres, listes de sources et décisions du chercheur (JSON/CSV)
data_raw/         Fichiers fournis au départ — immuables, non versionnés
data_external/    Téléchargements originaux (réponses API, PDF, rasters) — immuables, non versionnés
data_interim/     Caches et transformations intermédiaires — non versionnés
data_processed/   Tables analytiques produites par les scripts — versionnées
metadata/         Registre des sources, dictionnaire des variables, rôles causaux
src/              Code Python par domaine (collecte, traitement, causal, descriptif, scoring)
tests/            Tests automatisés (pytest)
reports/          Rapports numérotés 01–129 + sorties CSV/JSON + figures de revue
figures/          Figures de recherche versionnées
logs/             Journal de recherche et journal des collectes
notebooks/        Explorations (vide pour l'instant)
models/, outputs/ Artefacts et exports locaux — non versionnés
```

Chaque dossier principal (`reports/`, `data_processed/`, `config/`, `src/`) contient un court `README.md` qui explique son contenu.

**Important :** ne pas renommer ni déplacer les fichiers de `src/`, `tests/`, `config/`, `data_processed/`, `reports/` ou `metadata/`. Les scripts et les tests utilisent des chemins écrits en dur, et certains contrôles comparent les fichiers à l'historique Git. Pour s'orienter, utiliser les documents de `docs/` plutôt que de déplacer des fichiers.

## Règles de travail (résumé)

- Les données brutes (`data_raw/`, originaux de `data_external/`) ne sont jamais modifiées ; tout ce qui est dérivé va dans `data_interim/` ou `data_processed/`.
- Rien n'est inventé : une valeur introuvable reste `NA`, avec une explication.
- Toute source externe est enregistrée dans `metadata/data_sources_master.csv`, toute variable dans `metadata/data_dictionary.csv`.
- Identifiants stables (`resort_id`, `cluster_id`, `station_group_id`, `municipality_bfs_id`) plutôt que des noms.
- Règles complètes pour les assistants IA (Codex, Claude) : [`AGENTS.md`](AGENTS.md).

## Installation Python

Python 3.12. Depuis PowerShell, à la racine du projet :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev,audit]"
```

## Reproduire les calculs

- **Phase A** (rapports 01–51) : `.\.venv\Scripts\python.exe src\run_checkpoint_pipeline.py` (ajouter `--with-collection` pour revérifier les sources en ligne ; sans cette option, aucun accès réseau).
- **Phase B, début** (rapports 53–75) : `.\.venv\Scripts\python.exe src\run_accessibility_expansion.py`.
- **Étapes suivantes** : chaque étape a son propre script, indiqué dans la section « Reprise » du rapport correspondant et dans le journal. Les étapes terminées réutilisent leurs caches et ne relancent pas les collectes.
- **Tests** : `.\.venv\Scripts\python.exe -m pytest`. Plusieurs tests lisent des fichiers non versionnés de `data_external/` ou `data_interim/` ; ils ne passent donc que sur la machine qui possède ces fichiers.

Les clés d'API (openrouteservice) sont lues dans les variables d'environnement de l'utilisateur Windows et ne sont jamais écrites dans le dépôt.

## Git

Branche `main`, synchronisée avec `https://github.com/Chocaklick/Master-thesis-Magic-pass` (dépôt **public** : ne jamais y commiter de secret ni de donnée brute ou propriétaire). Faire des commits cohérents par étape ; ne jamais réécrire l'historique.
