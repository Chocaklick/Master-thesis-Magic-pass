# src/

Code Python du projet, à lancer depuis la racine du dépôt (`.\.venv\Scripts\python.exe src\...`).

| Dossier | Contenu |
|---|---|
| `data_collection/` | Collecteurs : téléchargent et archivent les sources (API, pages, rasters) dans `data_external/`, avec reprise et journal de collecte. |
| `data_processing/` | Construction des tables de `data_processed/` (panels, accessibilité, neige, relief, pistes) et mise à jour des registres de provenance. |
| `causal_inference/` | Témoins, pré-tendances, chocs externes et estimations (pilote, cohortes × mois, DiD routier). |
| `descriptive/` | Audits, vérifications de pistes, diagnostics, contrôles de préservation (`check_*preservation_stageNN.py`) et génération des rapports et brouillons de mémoire. |
| `scoring/` | Voie C de la phase A : variables structurelles, segments, analogues, tableau de bord. |
| `entity_resolution/` | Historique Magic Pass et correspondances entre libellés et fiches de stations. |
| `geospatial/` | Rattachement des points aux communes et validation des clusters fournis. |
| `ml/`, `utils/` | Vides pour l'instant. |

Points d'entrée :

- `run_checkpoint_pipeline.py` : toute la phase A (rapports 01–51), suivie des tests ;
- `run_accessibility_expansion.py` : début de la phase B (rapports 53–75) ;
- `run_accessibility_reference_time_revision.py` : révision des temps en transports publics (rapport 85).

Les étapes suivantes ont chacune leur script, souvent suffixé `_stageNN` ; la commande de reprise est indiquée dans le rapport correspondant et dans le journal.

Modules partagés utiles : `data_processing/atomic_csv_output.py` (écriture sûre des CSV), `data_processing/update_accessibility_expansion_provenance.py` (colonnes des registres), `data_collection/collect_evidence.py` (collecte générique avec cache), `data_processing/gtfs_static_router.py` (calcul d'itinéraires sur les horaires GTFS).

Il n'existe pas de module central de chemins : chaque script définit `ROOT` et écrit ses chemins en dur. **Ne pas renommer ni déplacer les scripts** : beaucoup s'importent entre eux (`from src.… import …`) et les tests importent les constantes des producteurs.
