# Bassins touristiques et spillovers - étape 22

**Statut : screening spatial et de transport terminé; absence globale de spillover non démontrée.**

## Définition opérationnelle du bassin

Le bassin n'est pas défini par la commune administrative où se trouve la station. Il est défini, comme proposé pour cette extension, par le temps de trajet entre l'origine de référence du centre communal et les points d'accès des groupes de stations. Le seuil principal reste 120 minutes dans un sens. Les frontières officielles de destination ne sont pas utilisées comme frontière dure, car elles ne suffisent pas à décrire les visiteurs réels.

## Résultat

Les 21 paires ont été contrôlées. Toutes sont à plus de 50 km entre centres communaux, tous les témoins sont à plus de 50 km d'un point Magic actif dans la fenêtre, et aucun témoin n'est exposé à moins de 120 minutes pendant novembre 2015-octobre 2019.

Pour 20 paires, une route actuelle complète vers au moins un groupe entrant est disponible; le minimum observé est **138.2 minutes**, donc au-dessus du seuil. Une paire n'a pas de route complète vers son groupe précis, mais son témoin reste classé hors du bassin de 120 minutes dans la matrice complète.

Les **21 paires** avancent donc au diagnostic des pré-tendances avec un risque direct local faible selon ces règles.

## Limite importante

Cette étape ne prouve pas que les marchés touristiques suisses sont indépendants. Un visiteur peut substituer un séjour entre régions éloignées, et l'horaire actuel n'est pas une reconstitution parfaite de 2017. Le statut obtenu autorise seulement le test statistique suivant; il n'accorde ni contrôle causal ni effet causal. Les sensibilités finales devront retirer tour à tour les témoins et les cas touristiques les plus exposés à une substitution large.

## Fichiers produits

- `reports/accessibility_pair_spillover_evidence.csv` : diagnostic des 21 paires ;
- `data_processed/accessibility_comparison_spillover_screen.csv` : statut étape 22 des 70 paires ;
- `reports/accessibility_parallel_trend_worklist.csv` : 21 paires prêtes pour la règle de pré-tendances ;
- `reports/accessibility_pair_spillover_summary.json` : seuils, compteurs et empreintes.
