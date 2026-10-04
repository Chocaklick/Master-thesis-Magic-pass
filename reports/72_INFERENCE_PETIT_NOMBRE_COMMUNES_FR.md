# Inférence avec peu de communes - étape 25

**Statut : sensibilité du pilote non causal; aucune estimation causale approuvée.**

## Pourquoi ce contrôle

L'intervalle initial regroupe 16 communes, mais l'effet moyen repose en réalité sur seulement **6 communes traitées**. Avec si peu d'unités effectivement traitées, les approximations normales peuvent donner une impression de précision excessive. La littérature recommande donc d'exposer explicitement cette fragilité.

## Deux sensibilités préenregistrées

1. La référence *t* traite les six variations propres aux communes traitées comme les six observations effectives. Elle est facile à lire, mais reste approximative car Emmen sert de témoin à Bulle et à Gruyères.
2. Le test de changement de signe relie d'abord les ensembles partageant une commune, puis énumère exactement tous les signes possibles des composantes disjointes du graphe. Sa lecture suppose l'indépendance de ces composantes et une symétrie sous l'hypothèse nulle; **ce n'est pas un test fondé sur une assignation aléatoire du Magic Pass**.

## Résultat

| Référence | Unités effectives | Valeur p bilatérale | Intervalle 95% |
|---|---:|---:|---:|
| Normale, regroupée par commune | 16 | 0.010 | [-11.7%; -1.6%] |
| *t* sur variations des communes traitées | 6 | 0.099 | [-14.8%; 1.9%] |
| Signes exacts sur composantes connectées | 5 | 0.188 | non construit |

La moyenne reste **-6.8%**, mais elle n'est plus distinguable de zéro avec les deux références adaptées au faible nombre d'unités effectives. Le test exact ne dispose que de 32 configurations et sa valeur p minimale possible est 0.0625.

## Structure de dépendance

| Composante | Communes traitées | Lien partagé | Contribution au coefficient |
|---|---|---|---:|
| component_01 | Köniz | aucun | -0.0199 |
| component_02 | Bulle, Gruyères | 1024 | -0.0233 |
| component_03 | Fribourg | aucun | -0.0033 |
| component_04 | La Chaux-de-Fonds | aucun | 0.0058 |
| component_05 | Saignelégier | aucun | -0.0299 |

## Conclusion pour le mémoire

Le signe négatif constitue un **résultat exploratoire**, pas une preuve statistique robuste et encore moins un effet causal. La formulation défendable est : les comparaisons retenues suggèrent une baisse moyenne, mais cette conclusion dépend fortement de l'approximation d'inférence et de la composition des témoins. La sensibilité conservatrice de l'étape 24 (-2,0%, intervalle incluant zéro) reste l'autre résultat central à présenter.

## Sources méthodologiques

- Canay, Romano et Shaikh (2017), [tests par changements de signe sous symétrie approximative](https://doi.org/10.3982/ECTA13081).
- MacKinnon et Webb (2018), [limites de l'inférence avec peu de grappes traitées](https://doi.org/10.1111/ectj.12107).

## Fichiers produits

- `reports/accessibility_pilot_small_cluster_inference.csv` : résultat comparé ;
- `reports/accessibility_pilot_inference_components.csv` : composantes et dépendances ;
- `reports/accessibility_pilot_small_cluster_inference_summary.json` : résumé et empreintes ;
- `config/accessibility_small_cluster_inference.json` : règles préenregistrées.
