# Spécification COVID et baseline de clientèle - étape 27

**Statut : option A approuvée. La longueur et l'agrégation de la baseline étrangère restent à valider avant estimation.**

## Règles déjà validées

- Tous les mois disponibles et toutes les cohortes restent dans l'analyse principale.
- Les effets fixes de mois calendaires absorbent les chocs nationaux communs. Une indicatrice COVID nationale seule n'est donc pas ajoutée séparément.
- La sensibilité principale retirera mars 2020 à mars 2022 inclus. L'ancien intervalle large jusqu'à avril 2022 est conservé seulement pour comparer avec les résultats antérieurs.
- L'interaction COVID utilisera une part de clientèle étrangère calculée avant la pandémie, avant la première exposition propre de la commune et avant la cohorte examinée.

## Disponibilité des baselines candidates

L'audit couvre 186 communes × 7 cohortes, soit 1 302 lignes. Il ne sélectionne aucun témoin ni traitement.

| Baseline | Lignes complètes sur 1 302 | Premières expositions complètes sur 80 | Premières expositions avec une part calculable | Principal compromis |
|---:|---:|---:|---:|---|
| 12 mois | 1255 | 76 | 76 | Couverture maximale, mais mesure plus volatile |
| 24 mois | 1242 | 76 | 76 | Deux cycles saisonniers, sans perdre de commune exposée observable |
| 36 mois | 1227 | 75 | 76 | Plus stable, mais une commune exposée complète en moins |

Quatre des 80 communes exposées n'ont aucune part calculable avant leur exposition sous leur identifiant communal actuel : Blonay - Saint-Légier, Val de Bagnes, Laténa, Moutier (JU). Elles ne sont pas exclues par ce rapport.

## Deux agrégations possibles

1. **Ratio des sommes** : somme des nuitées étrangères divisée par la somme des nuitées totales. Les mois de forte fréquentation pèsent davantage.
2. **Moyenne des parts mensuelles** : chaque mois pèse autant. Elle décrit mieux un profil mensuel moyen, mais donne le même poids aux mois creux.

Sur la baseline de 24 mois, les deux mesures sont fortement corrélées. Leur corrélation est 0.991; l'écart absolu médian est 0.8 point de pourcentage et le 95e percentile 5.6 points.

## Proposition soumise au chercheur

La proposition est une **baseline de 24 mois avec ratio des sommes**. Elle conserve les 76 premières expositions disposant de données d'origine et couvre deux cycles saisonniers complets. Les quatre communes sans donnée restent documentées et ne pourront recevoir cette interaction sans une source supplémentaire.

Aucune comparaison de cohorte, aucun échantillon et aucun estimateur n'est choisi ici.

## Sources

- Chronologie officielle des décisions COVID du Conseil fédéral : `SWISS_FEDERAL_COUNCIL_COVID_DECISION_CHRONOLOGY`.
- Effondrement de la demande hôtelière 2020 et exposition particulière de la clientèle étrangère : `BFS_HOTEL_DEMAND_COVID_2020`.
- Nuitées domestiques et étrangères mensuelles : panel HESTA déjà enregistré dans le projet.
