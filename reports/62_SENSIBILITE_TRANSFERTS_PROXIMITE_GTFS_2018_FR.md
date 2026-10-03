# Sensibilité des transferts de proximité dans le GTFS 2018 — étape 15

## Pourquoi une sensibilité est nécessaire

Le flux 2018 ne publie que **184 transferts entre identifiants d'arrêts normalisés**, contre **7 369** dans le flux 2026. Le scénario strict reste conservé, mais il ne permet que 9 / 39 couples complets et 3 / 39 couples à 120 minutes ou moins. Plusieurs gares bus–train proches ne sont donc pas reliées dans l'ancien schéma.

La sensibilité ajoute uniquement des liens de marche bidirectionnels entre arrêts GTFS 2018 actifs situés à **250 m ou moins**. Le temps vaut 120 secondes d'interchange plus la marche à 1,2 m/s, arrondie aux 30 secondes supérieures. Les transferts publiés sont conservés et jamais remplacés.

| Résultat | Strict publié | Sensibilité 250 m |
|---|---:|---:|
| Couples complets sur 24 horaires | 9 / 39 | 39 / 39 |
| Couples complets à 120 minutes ou moins | 3 / 39 | 22 / 39 |
| Communes gardant au moins un groupe fondateur à 120 minutes ou moins | 2 / 19 | 13 / 19 |
| Communes gardant tous leurs groupes fondateurs actuels | 2 / 19 | 6 / 19 |

La variante 250 m est une **sensibilité modélisée**, pas une propriété publiée par le GTFS 2018. Elle sert à mesurer l'effet du changement de codage des correspondances. Le scénario strict et la variante doivent être rapportés ensemble; aucun des deux n'autorise à lui seul une interprétation causale.

## Fichiers

- `data_processed/accessibility_historical_gtfs_2018_proximity_journey_context.csv` : 39 couples;
- `data_processed/accessibility_historical_gtfs_2018_proximity_journey_samples.csv` : 936 horaires;
- `reports/accessibility_historical_gtfs_2018_proximity_municipality_validation.csv` : 19 communes;
- `reports/accessibility_historical_gtfs_2018_proximity_summary.json` : paramètres, liens inférés et comptes.
