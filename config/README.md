# config/

Fichiers lus par les scripts de `src/`. On y trouve quatre familles :

| Famille | Exemples | Rôle |
|---|---|---|
| **Décisions du chercheur** | `*_decision_stageNN.json`, `*_decisions_stageNN.json`, `winter_profile_researcher_decisions.json` | Choix méthodologiques validés, souvent avec le texte exact de la validation et sa date. Ils font foi pour les étapes suivantes. |
| **Listes de sources à collecter** | `*_sources*.json`, `evidence_sources.json`, `municipality_queries.json`, `meteoswiss_*_files.json` | URL, paramètres et identifiants de source utilisés par les collecteurs (réponses archivées dans `data_external/`). |
| **Paramètres d'analyse** | `accessibility_*.json`, `path_c_*.json`, `temporal_controls.json` | Seuils, fenêtres, estimateurs, règles de comparaison. |
| **Registres saisis à la main** | `competing_pass_*.json`, `competing_pass_roster_2026_27.csv`, `piste_assignment_*`, `piste_operator_*` | Informations relevées dans des documents officiels, avec leurs sources. |

Le suffixe `_stageNN` indique l'étape concernée (correspondance avec les rapports dans [`docs/INDEX_RAPPORTS.md`](../docs/INDEX_RAPPORTS.md)). Pour retrouver une décision, chercher son étape ou sa date dans `logs/research_journal.md`.

Ne pas renommer ces fichiers : les scripts les appellent par leur chemin exact. Aucun secret ne doit être écrit ici : les clés d'API restent dans les variables d'environnement.
