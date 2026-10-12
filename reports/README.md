# reports/

Ce dossier contient trois types de fichiers :

- **Rapports numérotés** `NN_TITRE.md` (01 à 129) : une étape de travail chacun, en anglais pour la phase A, en français ensuite (suffixe `_FR`). L'index commenté, avec le statut de chaque rapport (référence, historique ou brouillon), est dans [`docs/INDEX_RAPPORTS.md`](../docs/INDEX_RAPPORTS.md).
- **Sorties chiffrées** `*.csv` et `*_summary.json` : produites par les scripts de `src/` et citées dans les rapports. Les fichiers `preservation_*_summary.json` sont les manifestes de contrôle (empreintes SHA-256) d'une étape.
- **Figures** : `reports/figures/` contient les cartes de revue des rattachements de pistes ; quelques figures de résultats sont à la racine de ce dossier (par exemple `accessibility_road_did_dynamic.png`).

Rapports transversaux non numérotés : `EXECUTIVE_SUMMARY.md` (phase A), `DATA_SOURCES.md`, `INITIAL_DATA_AUDIT.md`, `EXISTING_CLUSTER_AUDIT.md`, `model_feasibility_report.md`.

Ne pas renommer ni déplacer ces fichiers : les scripts les écrivent et les tests les relisent à ces chemins exacts.
