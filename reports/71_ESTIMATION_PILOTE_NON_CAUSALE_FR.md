# Estimation pilote non causale - étape 24

**Statut : test quantitatif exploratoire; aucune estimation causale approuvée.**

## Modèle préenregistré

Chaque commune traitée forme un ensemble avec ses témoins retenus. La commune traitée reçoit un poids de 1 et les témoins se partagent ensemble un poids de 1, ce qui évite de favoriser Bulle parce qu'elle possède davantage de témoins. Le modèle retire les effets fixes commune × ensemble et mois × ensemble. L'incertitude est regroupée par commune BFS, y compris lorsqu'un témoin est réutilisé.

La fenêtre principale contient 24 mois avant et 24 mois après novembre 2017. Le coefficient compare le changement moyen des log-nuitées des communes traitées à celui de leurs témoins. Il est converti en pourcentage uniquement pour faciliter la lecture.

## Résultat principal

Avec les 11 paires principales et 6 communes traitées, le pilote donne **-6.8%**. L'intervalle normal regroupé à 95% va de **-11.7% à -1.6%**.

Ce nombre ne doit pas être lu comme l'effet du Magic Pass : le nombre de grappes est faible, l'accès historique dépend encore d'une sensibilité de transferts et une substitution touristique large peut subsister.

Les 6 communes traitées sont également retenues sous la sensibilité historique ajoutant des correspondances à 250 m. En revanche, 0 sont retenues avec la seule table de transferts publiée en 2018, connue pour être fortement sous-connectée. Cette concordance entre les deux scénarios augmentés améliore la plausibilité, sans rendre les transferts historiques certains.

## Sensibilités

| Variante | Paires | Communes traitées | Variation pilote | Intervalle 95% |
|---|---:|---:|---:|---:|
| primary_full_24m_post | 11 | 6 | -6.8% | [-11.7%; -1.6%] |
| primary_post_truncated_at_month_13 | 11 | 6 | -7.2% | [-13.5%; -0.3%] |
| relaxed_full_24m_post | 15 | 6 | -8.7% | [-13.6%; -3.5%] |
| primary_excluding_targeted_sensitivity_controls | 5 | 4 | -2.0% | [-7.8%; 4.3%] |

En retirant une paire à la fois, le point estimé varie de **-8.8% à -5.7%**. En retirant une commune traitée à la fois, il varie de **-8.8% à -4.8%**.

## Décomposition par commune traitée

Cette décomposition est descriptive et explique l'hétérogénéité derrière la moyenne pondérée.

| Commune traitée | Témoins | Variation pilote 24 mois | Variation post tronquée |
|---|---|---:|---:|
| Köniz | Lenzburg | -11.2% | -7.4% |
| Bulle | Emmen, Freienbach, Sarnen | -12.7% | -9.2% |
| Gruyères | Emmen, Kreuzlingen | -0.4% | -6.2% |
| Fribourg | Pratteln, Schaffhausen | -2.0% | -1.8% |
| La Chaux-de-Fonds | Liestal | 3.5% | 6.8% |
| Saignelégier | Vitznau, Walenstadt | -16.4% | -22.6% |

## Profil temporel

Les coefficients semestriels sont exprimés relativement au mois -1. Ils servent à repérer une rupture ou une dérive, pas à dater un mécanisme causal.

| Fenêtre | Variation pilote | Intervalle 95% |
|---|---:|---:|
| pre_24_to_19 | -6.1% | [-20.9%; 11.6%] |
| pre_18_to_13 | -1.3% | [-15.5%; 15.2%] |
| pre_12_to_7 | -4.2% | [-16.1%; 9.4%] |
| pre_6_to_2 | -9.0% | [-18.4%; 1.4%] |
| post_0_to_5 | -8.3% | [-17.2%; 1.5%] |
| post_6_to_11 | -14.0% | [-24.7%; -1.8%] |
| post_12_to_17 | -12.4% | [-19.4%; -4.8%] |
| post_18_to_23 | -10.4% | [-21.7%; 2.7%] |

## Conclusion utilisable

Le pilote indique la direction et l'instabilité possibles des résultats, mais il ne franchit pas le seuil de preuve causale. Il peut être présenté comme analyse exploratoire ou test de robustesse. Pour une affirmation causale, il faudrait notamment une reconstruction historique de l'accessibilité plus forte, davantage de grappes indépendantes et une stratégie crédible contre la substitution entre régions.

## Fichiers produits

- `reports/accessibility_pilot_did_estimates.csv` : estimations principale et sensibilités ;
- `reports/accessibility_pilot_event_study.csv` : profil semestriel ;
- `reports/accessibility_pilot_influence_sensitivity.csv` : retraits successifs ;
- `reports/accessibility_pilot_treated_decomposition.csv` : décomposition descriptive par commune traitée ;
- `data_processed/accessibility_pilot_stacked_panel.csv` : panel empilé reproductible ;
- `reports/accessibility_pilot_estimation_summary.json` : résumé et empreintes.
