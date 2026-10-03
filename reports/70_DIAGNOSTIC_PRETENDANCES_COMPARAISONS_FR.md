# Diagnostic des pré-tendances - étape 23

**Statut : compatibilité pré-traitement, pas preuve de tendances parallèles.**

## Règle fixée avant le calcul

La règle principale exige 36 mois communs, une corrélation des log-nuitées d'au moins 0,70, un RMSE standardisé au plus égal à 0,80, un RMSE saisonnier au plus égal à 0,25 et une pente différentielle mensuelle désaisonnalisée d'au plus 0,005 en valeur absolue. Une règle secondaire plus souple (0,60; 0,90; 0,30; 0,0075) sert uniquement de sensibilité.

L'incertitude de la pente est calculée avec une covariance Newey-West à 12 retards. L'inclusion de zéro dans l'intervalle à 95% est rapportée, mais ne suffit jamais à accepter une paire.

## Résultat

Sur 21 paires, **11** passent la règle principale et couvrent **6 communes traitées**. 4 paires supplémentaires passent seulement la sensibilité relâchée, pour un total de **15**. **6** échouent même à la règle souple.

| Commune traitée | Témoins règle principale | Témoins sensibilité seulement | Échecs |
|---|---|---|---|
| Bulle | Sarnen, Freienbach, Emmen | aucun | Vitznau |
| Fribourg | Schaffhausen, Pratteln | aucun | aucun |
| Gruyères | Kreuzlingen, Emmen | aucun | Rorschacherberg |
| Haut-Intyamon | aucun | aucun | Emmetten, Amden, Walenstadt, Rorschacherberg |
| Köniz | Lenzburg | aucun | aucun |
| La Chaux-de-Fonds | Liestal | Frauenfeld, Aarau, Emmen, Lenzburg | aucun |
| Saignelégier | Walenstadt, Vitznau | aucun | aucun |

## Interprétation

Ces règles réduisent le noyau sans sélectionner sur les résultats postérieurs. Elles montrent surtout qu'aucune paire de Haut-Intyamon ne présente une pré-tendance assez proche, ce qui empêche de retenir cette commune dans le noyau principal actuel. Les paires retenues restent des candidats de sensibilité : l'accès historique repose sur une topologie de transfert projetée et la substitution touristique large n'est pas éliminée. Les drapeaux `parallel_trends_approved` et `causal_pair_approved` restent donc faux.

## Fichiers produits

- `reports/accessibility_parallel_trend_diagnostics.csv` : 21 diagnostics et motifs d'échec ;
- `data_processed/accessibility_comparison_parallel_trend_screen.csv` : statut étape 23 des 70 paires ;
- `reports/accessibility_estimation_candidate_pairs.csv` : noyau principal et sensibilité relâchée ;
- `reports/accessibility_parallel_trend_summary.json` : règles, compteurs et empreintes.
