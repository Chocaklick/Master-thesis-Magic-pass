# Comparaison des cohortes - étape 28

**Statut : option C appliquée aux univers candidats. Aucun estimateur n'est encore choisi.**

## Règle validée

- Analyse principale : communes jamais exposées ou pas encore exposées à la date de la cohorte.
- Une commune pas encore exposée cesse d'être témoin au mois de sa propre première exposition; seuls les mois strictement antérieurs peuvent être utilisés.
- Sensibilité : communes jamais exposées dans la matrice actuelle à 120 minutes uniquement.
- Les communes déjà exposées avant la cohorte ne servent jamais de témoins; les communes de la cohorte sont marquées comme traitées.

## Effectifs mécaniques par cohorte

| Cohorte | Traitées | Témoins principaux | Dont pas encore exposées | Dont jamais exposées | Témoins de sensibilité | Déjà exposées exclues des témoins |
|---|---:|---:|---:|---:|---:|---:|
| 2017-11-01 | 41 | 145 | 39 | 106 | 106 | 0 |
| 2018-05-01 | 3 | 142 | 36 | 106 | 106 | 41 |
| 2019-05-01 | 3 | 139 | 33 | 106 | 106 | 44 |
| 2022-05-01 | 16 | 123 | 17 | 106 | 106 | 47 |
| 2023-05-01 | 9 | 114 | 8 | 106 | 106 | 63 |
| 2024-05-01 | 5 | 109 | 3 | 106 | 106 | 72 |
| 2025-05-01 | 3 | 106 | 0 | 106 | 106 | 77 |

L'audit conserve 1302 lignes commune-cohorte, 80 communes exposées une première fois et 106 communes jamais exposées dans la matrice actuelle.

## Limites et prochaine décision

Ces effectifs décrivent une disponibilité mécanique. Ils ne valident ni comparabilité, ni tendances parallèles, ni absence de choc local. La matrice d'accessibilité actuelle reste projetée sur les cohortes historiques.

Aucune fenêtre de résultat, aucun filtre de comparabilité, aucun échantillon final et aucun estimateur n'est choisi ici. La prochaine décision doit fixer l'horizon principal avant d'appliquer les diagnostics aux témoins candidats.

## Sources internes

- Première exposition communale et statut par cohorte : `reports/accessibility_covid_foreign_share_selected.csv`.
- Règle approuvée : `config/accessibility_cohort_comparison.json`.
