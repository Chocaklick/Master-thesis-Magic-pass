# Spécification COVID et baseline de clientèle - étape 27

**Statut : option A, baseline de 24 mois et ratio des sommes approuvés. Le traitement des valeurs manquantes reste à valider avant estimation.**

## Règles déjà validées

- Tous les mois disponibles et toutes les cohortes restent dans l'analyse principale.
- Les effets fixes de mois calendaires absorbent les chocs nationaux communs. Une indicatrice COVID nationale seule n'est donc pas ajoutée séparément.
- La sensibilité principale retirera mars 2020 à mars 2022 inclus. L'ancien intervalle large jusqu'à avril 2022 est conservé seulement pour comparer avec les résultats antérieurs.
- L'interaction COVID utilisera une part de clientèle étrangère calculée avant la pandémie, avant la première exposition propre de la commune et avant la cohorte examinée.
- La caractéristique approuvée couvre 24 mois et correspond au ratio entre la somme des nuitées étrangères et la somme des nuitées domestiques plus étrangères.

## Disponibilité des baselines candidates

L'audit couvre 186 communes × 7 cohortes, soit 1 302 lignes. Il ne sélectionne aucun témoin ni traitement.

| Baseline | Lignes complètes sur 1 302 | Premières expositions complètes sur 80 | Premières expositions avec une part calculable | Principal compromis |
|---:|---:|---:|---:|---|
| 12 mois | 1255 | 76 | 76 | Couverture maximale, mais mesure plus volatile |
| 24 mois | 1242 | 76 | 76 | Deux cycles saisonniers, sans perdre de commune exposée observable |
| 36 mois | 1227 | 75 | 76 | Plus stable, mais une commune exposée complète en moins |

Quatre des 80 communes exposées n'ont aucune part calculable avant leur exposition sous leur identifiant communal actuel : Blonay - Saint-Légier, Val de Bagnes, Laténa, Moutier (JU). Elles ne sont pas exclues par ce rapport.

## Agrégation validée

Le **ratio des sommes** est retenu : somme des nuitées étrangères divisée par la somme des nuitées totales. Les mois de forte fréquentation pèsent donc davantage.

Sur la baseline de 24 mois, les deux mesures sont fortement corrélées. Leur corrélation est 0.991; l'écart absolu médian est 0.8 point de pourcentage et le 95e percentile 5.6 points.

## Décision enregistrée

La **baseline de 24 mois avec ratio des sommes** est maintenant verrouillée. Le fichier sélectionné conserve les 1 302 lignes commune-cohorte; il ne retire ni n'impute les valeurs manquantes.

## Nouvelle décision méthodologique requise : quatre historiques manquants

La part approuvée est disponible pour 76 des 80 premières expositions. Elle manque pour : Blonay - Saint-Légier, Val de Bagnes, Laténa, Moutier (JU).

- **A — reconstruire les historiques (recommandé pour maximiser l'inclusion)** : Moutier peut être relié à sa série BFS 700 grâce au pont officiel déjà documenté. Pour les trois autres cas, il faut collecter les séries HESTA des entités antérieures et leurs mutations officielles, puis agréger seulement sur un périmètre territorial justifié.
- **B — interaction sur cas complets** : garder les 80 communes dans le modèle principal sans interaction, mais estimer l'hétérogénéité selon la clientèle étrangère sur les 76 cas disponibles.
- **C — indicatrice de valeur manquante** : conserver les 80 cas dans l'interaction en centrant conventionnellement la part manquante et en ajoutant un terme spécifique. Cette solution préserve la taille, mais repose sur une convention de modélisation plus forte.

Aucune de ces trois solutions n'est appliquée sans validation. Aucune comparaison de cohorte, aucun échantillon et aucun estimateur n'est choisi ici.

## Sources

- Chronologie officielle des décisions COVID du Conseil fédéral : `SWISS_FEDERAL_COUNCIL_COVID_DECISION_CHRONOLOGY`.
- Effondrement de la demande hôtelière 2020 et exposition particulière de la clientèle étrangère : `BFS_HOTEL_DEMAND_COVID_2020`.
- Nuitées domestiques et étrangères mensuelles : panel HESTA déjà enregistré dans le projet.
