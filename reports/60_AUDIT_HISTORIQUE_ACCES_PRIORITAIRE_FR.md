# Audit historique ciblé des accès — étape 13

## Périmètre utile

Le screening du rapport 59 réduit l'audit historique à **19 communes** et **39 couples commune–groupe fondateur**, couvrant 10 groupes et 19 arrêts d'origine. Il n'est donc pas nécessaire de recalculer immédiatement les 13 206 couples de la matrice complète.

## Source 2018 identifiée

- source officielle : `SKI_GTFS_TIMETABLE_2018_WINTER_20180207`;
- construction GTFS : `2018-02-07`;
- URL : https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2018-gtfs/GTFS_FP2018_2018-02-07.zip;
- taille annoncée par le serveur : **50,151,599 octets**;
- réponse HEAD vérifiée : HTTP 200 le 2026-10-02.

Le fichier n'a pas été téléchargé automatiquement. Le `robots.txt` du serveur d'archive indique `Disallow: /`; cette restriction est respectée. Le téléchargement doit donc être effectué manuellement depuis l'URL officielle, puis le ZIP doit être placé sans modification à l'emplacement suivant :

`data_external/source_evidence/SKI_GTFS_TIMETABLE_2018_WINTER_20180207.zip`

Après dépôt, le projet devra calculer SHA-256, vérifier l'intégrité du ZIP, retrouver les arrêts historiques et exécuter exactement les mêmes horaires-types que pour 2026. Les champs de résultat restent actuellement faux ou manquants; **aucun accès historique ni usage causal n'est approuvé**.

## Fichier de travail

`reports/accessibility_historical_gtfs_2018_manual_worklist.csv` contient chaque origine communale, chaque groupe fondateur accessible, les identifiants d'arrêts actuels, les références d'accès utilisées en 2026 et les champs qui seront complétés après validation du flux 2018.
