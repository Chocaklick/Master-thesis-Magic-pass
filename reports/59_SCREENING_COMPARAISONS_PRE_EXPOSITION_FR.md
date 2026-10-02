# Screening des comparaisons avant première exposition — étape 12

## Résultat

Le dessin communal proposé dans le rapport 58 retient **19 communes** dont la première exposition accessible se situe au lancement de novembre 2017, avec 24 mois observés avant et après, aucun COVID dans la fenêtre et aucune nouvelle entrée accessible pendant les 24 mois postérieurs. **132 communes** ont une issue complète et aucune entrée accessible dans la même fenêtre : 99 ne sont jamais exposées dans la matrice actuelle et 33 ne le deviennent que plus tard.

Les **2,508 couples** sont comparés uniquement sur les 36 mois antérieurs : niveau et forme des nuitées, saisonnalité, tendance désaisonnalisée, lits disponibles et part domestique. Les cinq meilleures comparaisons relatives par commune produisent **95 couples**, impliquant 50 communes de comparaison distinctes. Le score sert uniquement à prioriser une revue manuelle.

## Meilleure comparaison mécanique par commune traitée

| Commune exposée | Groupes à la première exposition | Comparaison provisoire | Statut | Score relatif | Corrélation pré | Écart de tendance mensuelle |
|---|---:|---|---|---:|---:|---:|
| Anniviers | 2 | Andermatt | never exposed in current 120min matrix | 84.4 | 0.832 | 0.0029 |
| Bulle | 5 | Sarnen | not yet exposed during 2015 11 to 2019 10 | 83.8 | 0.855 | 0.0011 |
| Burgdorf | 1 | Lenzburg | never exposed in current 120min matrix | 89.2 | 0.839 | 0.0041 |
| Champéry | 1 | Andermatt | never exposed in current 120min matrix | 83.1 | 0.747 | 0.0029 |
| Château-d'Oex | 2 | Bullet | not yet exposed during 2015 11 to 2019 10 | 80.6 | 0.683 | 0.0025 |
| Fribourg | 4 | Schaffhausen | never exposed in current 120min matrix | 91.0 | 0.896 | 0.0017 |
| Gruyères | 3 | Maienfeld | never exposed in current 120min matrix | 88.2 | 0.845 | 0.0013 |
| Haut-Intyamon | 4 | Emmetten | never exposed in current 120min matrix | 85.2 | 0.751 | 0.0149 |
| Köniz | 1 | Lenzburg | never exposed in current 120min matrix | 88.4 | 0.764 | 0.0021 |
| La Chaux-de-Fonds | 1 | Liestal | never exposed in current 120min matrix | 85.9 | 0.776 | 0.0019 |
| Leysin | 3 | Meiringen | not yet exposed during 2015 11 to 2019 10 | 83.8 | 0.507 | 0.0009 |
| Murten | 1 | Appenzell | never exposed in current 120min matrix | 84.6 | 0.946 | 0.0007 |
| Ollon | 1 | Klosters | never exposed in current 120min matrix | 86.9 | 0.933 | 0.0060 |
| Ormont-Dessus | 3 | Andermatt | never exposed in current 120min matrix | 87.3 | 0.827 | 0.0024 |
| Orsières | 1 | Beatenberg | not yet exposed during 2015 11 to 2019 10 | 81.6 | 0.735 | 0.0006 |
| Plaffeien | 1 | Bullet | not yet exposed during 2015 11 to 2019 10 | 87.7 | 0.776 | 0.0033 |
| Saanen | 3 | Pontresina | never exposed in current 120min matrix | 89.6 | 0.934 | 0.0025 |
| Saignelégier | 1 | Gais | never exposed in current 120min matrix | 83.1 | 0.866 | 0.0002 |
| Thun | 1 | Schaffhausen | never exposed in current 120min matrix | 87.3 | 0.944 | 0.0011 |

## Ce que ce screening permet — et ne permet pas

Le résultat montre qu'un groupe de comparaison communal plus large existe mécaniquement; il ne valide pas les tendances parallèles. Le score est relatif à chaque commune traitée et ne doit pas être comparé entre lignes. Il ne vérifie encore ni les chocs touristiques locaux, ni les autres forfaits, ni les investissements hôteliers ou de remontées, ni les débordements au-delà du seuil de 120 minutes.

L'accès de 2026 est toujours projeté sur 2017. Il faut donc d'abord auditer l'existence et la plausibilité des liaisons historiques pour les 19 communes traitées, puis examiner les 95 couples présélectionnés. **Zéro contrôle, zéro traitement et aucune hypothèse de tendances parallèles ne sont approuvés.**

## Fichiers

- `data_processed/accessibility_first_exposure_pretrend_pairs.csv` : les 2 508 couples et leurs mesures pré-traitement;
- `reports/accessibility_first_exposure_pretrend_shortlist.csv` : cinq comparaisons provisoires par commune exposée;
- `reports/accessibility_first_exposure_pretrend_summary.json` : comptes, décisions et empreintes.
