# data_processed/

Tables analytiques produites par les scripts de `src/` à partir de `data_raw/`, `data_external/` et `data_interim/`. Elles sont versionnées dans Git, sauf deux très gros fichiers d'échantillons de trajets (voir `.gitignore`), qui se reconstruisent depuis les caches.

**Quelle table utiliser ?** Voir [`docs/DONNEES_DE_REFERENCE.md`](../docs/DONNEES_DE_REFERENCE.md), qui donne pour chaque thème la version actuelle et les versions antérieures.

Conventions :

- un suffixe `_stageNN` indique l'étape qui a produit cette version ; une table n'est jamais écrasée, une correction crée une nouvelle version ;
- le sens de chaque colonne est décrit dans `metadata/data_dictionary.csv` (colonne `table` = nom du fichier sans extension) ;
- les valeurs manquantes restent vides (`NA`) : elles ne sont jamais remplacées par zéro ni imputées.

Ne pas renommer, déplacer ni modifier ces fichiers à la main : les scripts, les tests et les manifestes de contrôle utilisent ces chemins et leurs empreintes.
