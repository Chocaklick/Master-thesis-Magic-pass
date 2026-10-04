# Couverture de toutes les cohortes - étape 26

**Statut : inventaire exhaustif; aucune commune ni cohorte sélectionnée ou exclue.**

## Résultat principal

Le seuil de 120 minutes déjà utilisé relie **80 communes** à au moins une entrée Magic Pass. Le tableau ci-dessous ne déclare pas ces communes causalement utilisables : il indique seulement combien disposent mécaniquement de nuitées observées avant et après leur première exposition.

| Horizon symétrique | Communes avec fenêtre complète | Communes en plus des 6 du pilote | Groupes représentés | Groupes en plus des 6 du pilote | Chevauchement COVID | Entrée ultérieure | Post trop court |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 6+6 mois | 76 | 70 | 32 | 26 | 16 | 0 | 0 |
| 12+12 mois | 73 | 67 | 31 | 25 | 19 | 12 | 3 |
| 24+24 mois | 65 | 59 | 27 | 21 | 31 | 27 | 8 |

## Couverture par seuil d'accès

| Seuil | Communes exposées au moins une fois | Cohortes de première exposition | Entrées multiples dès le premier mois | Au moins une entrée ultérieure |
|---:|---:|---:|---:|---:|
| 30 min | 5 | 3 | 0 | 0 |
| 60 min | 30 | 6 | 9 | 2 |
| 90 min | 55 | 7 | 27 | 18 |
| 120 min | 80 | 7 | 40 | 46 |

## Cohortes au seuil de 120 minutes

| Première exposition | Groupes entrant dans le réseau | Groupes causant une première exposition communale | Communes | Complètes 6+6 | Complètes 12+12 | Complètes 24+24 |
|---|---:|---:|---:|---:|---:|---:|
| 2017-11-01 | 22 | 12 | 41 | 37 | 37 | 37 |
| 2018-05-01 | 6 | 4 | 3 | 3 | 3 | 1 |
| 2019-05-01 | 3 | 2 | 3 | 3 | 3 | 3 |
| 2022-05-01 | 10 | 6 | 16 | 16 | 16 | 15 |
| 2023-05-01 | 15 | 6 | 9 | 9 | 9 | 9 |
| 2024-05-01 | 5 | 1 | 5 | 5 | 5 | 0 |
| 2025-05-01 | 9 | 1 | 3 | 3 | 0 | 0 |

## Comment lire ces nombres

- Une fenêtre complète signifie uniquement que les nuitées sont observées pendant tous les mois avant et après considérés.
- Le COVID n'exclut aucune ligne ici : son chevauchement est compté pour préparer l'étape 27.
- Les entrées multiples sont conservées. Les groupes simultanés et les ajouts ultérieurs sont signalés afin de ne pas attribuer arbitrairement leur effet à une seule station.
- L'accessibilité reste fondée sur le réseau actuel. La sensibilité GTFS 2018 n'est réutilisée que pour les communes déjà auditées et n'est jamais extrapolée aux cohortes ultérieures.

## Décision méthodologique suivante

L'étape 27 doit définir le traitement analytique du COVID avant toute nouvelle estimation. Ce rapport ne choisit pas cette règle : les options doivent être soumises au chercheur.

## Fichiers produits

- `reports/accessibility_all_cohort_municipality_coverage.csv` : une ligne par seuil et commune exposée ;
- `reports/accessibility_all_cohort_coverage_by_cohort.csv` : synthèse par mois de première exposition ;
- `reports/accessibility_all_cohort_station_group_coverage.csv` : couverture des 71 groupes à chaque seuil ;
- `reports/accessibility_all_cohort_coverage_summary.json` : compteurs et empreintes ;
- `config/accessibility_all_cohort_coverage.json` : règles d'inventaire sans sélection.
