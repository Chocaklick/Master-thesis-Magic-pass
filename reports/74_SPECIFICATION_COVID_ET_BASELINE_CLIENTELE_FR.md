# Spécification COVID et baseline de clientèle - étape 27

**Statut : option A appliquée. Moutier est reconstruit exactement; trois historiques restent indisponibles sans approximation.**

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

## Reconstruction officielle des historiques

L'option A a été appliquée en exigeant l'identifiant BFS, la mutation officielle et toutes les composantes territoriales d'une fusion. Une composante absente de la publication contrôlée n'est jamais remplacée par zéro.

| Commune actuelle | Couverture des composantes historiques | Résultat |
|---|---:|---|
| Moutier (JU) | 1/1 | Série BFS 700 reliée au BFS 6831 par la mutation officielle 3999; part reconstruite |
| Val de Bagnes | 1/2 | Bagnes est dans l'archive HESTA contrôlée, Vollèges ne l'est pas; aucune agrégation partielle |
| Blonay - Saint-Légier | 0/2 | Les deux anciennes communes sont absentes de l'archive HESTA contrôlée |
| Laténa | 0/4 | Les quatre anciennes communes sont absentes de l'archive HESTA contrôlée |

Après reconstruction, la part est disponible pour 77 des 80 premières expositions. Elle reste manquante pour : Blonay - Saint-Légier, Val de Bagnes, Laténa. Les 1 302 lignes sont conservées et aucune valeur n'est imputée.

Aucune comparaison de cohorte, aucun échantillon et aucun estimateur n'est choisi ici. Le traitement analytique des trois valeurs toujours manquantes devra rester explicite dans la prochaine spécification.

## Sources

- Chronologie officielle des décisions COVID du Conseil fédéral : `SWISS_FEDERAL_COUNCIL_COVID_DECISION_CHRONOLOGY`.
- Effondrement de la demande hôtelière 2020 et exposition particulière de la clientèle étrangère : `BFS_HOTEL_DEMAND_COVID_2020`.
- Nuitées domestiques et étrangères mensuelles : panel HESTA déjà enregistré dans le projet.
- Mutations communales officielles : `BFS_MUNICIPAL_MUTATION_3944`, `BFS_MUNICIPAL_MUTATION_3961`, `BFS_MUNICIPAL_MUTATION_3994` et `BFS_MUNICIPAL_MUTATION_3999`.
- Univers communal de l'ancienne publication HESTA contrôlée : `BFS_HESTA_ARCHIVE_2020_METADATA`.
