# Raccordement territorial de Moutier — étape 29b

## Décision et méthode

Raccordement explicitement validé par le chercheur : BFS 700 avant janvier 2026, BFS 6831 à partir de janvier 2026, pour le même territoire. La mutation officielle déjà archivée est `BFS_MUNICIPAL_MUTATION_3999`. Il ne s'agit ni d'une fusion à reconstituer ni d'une imputation.

Le panel dérivé utilise 6831 comme identifiant analytique. `source_municipality_bfs_id` conserve l'identifiant réellement fourni chaque mois ; `municipality_name_source`, les valeurs, jetons et identifiants de sources HESTA restent ceux de la ligne originale. Les lignes parallèles retirées ne contenaient aucune valeur numérique d'issue ou de capacité. Toutes les autres communes restent inchangées.

Les calendriers d'exposition et l'accessibilité des deux identifiants sont vérifiés identiques. Les rôles de comparaison et valeurs de clientèle étrangère sont également réconciliés : une seule ligne territoriale est conservée par cohorte. Les sorties administratives antérieures ne sont pas écrasées ; elles documentent la provenance, mais ne constituent plus le grain prévu pour l'estimation élargie.

## Bilan après raccordement

| Indicateur | Résultat |
|---|---:|
| Territoires dans le panel | 185 (au lieu de 186 identifiants) |
| Communes exposées | 79 (au lieu de 80 séries) |
| Lignes commune-mois | 31 080 |
| Nuitées mensuelles observées | 28 455 — aucune perte |
| Mois observés pour Moutier | 157 |
| Observations postérieures exposées conservées | 5 580 |
| Communes avec observations avant et après | 76/79 |
| Communes avec ajouts successifs | 45 |
| Entrées territoire-mois | 175 : 79 premières + 96 ajouts |
| Part étrangère disponible pour l'interaction | 76/79 |

Les fenêtres complètes de 6+6, 12+12 et 24+24 mois restent disponibles pour 76, 73 et 65 communes. Le raccordement ne crée aucune nouvelle nuitée et ne modifie pas les contrôles jamais exposés ou pas encore exposés. Il corrige uniquement le double identifiant et rend l'historique de Moutier exploitable dans une seule unité.

Les trois historiques préexposition encore incomplets sont : Blonay - Saint-Légier, Val de Bagnes, Laténa. Ces communes restent recensées ; aucune exclusion ou approximation supplémentaire n'est décidée.

Le diagnostic territorial est recalculé : 45 colonnes d'exposition accessibles, rang 41, quatre paires identiques. Les 71 groupes et la sortie documentée de Crans-Montana sont préservés. Le rang reste un diagnostic algébrique, pas une preuve causale.

## Fichiers et reprise

- [Panel territorial](../data_processed/accessibility_municipality_month_exposure_territorial.csv).
- [Rôles de comparaison territoriaux](accessibility_cohort_comparison_universe_territorial.csv).
- [Baseline de clientèle étrangère territoriale](accessibility_covid_foreign_share_selected_territorial.csv).
- `accessibility_territorial_harmonisation_summary.json` : support temporel, diagnostic des ajouts, rang et empreintes des entrées.
- `config/accessibility_outcome_territorial_harmonisation.json` : décision, dates, sources et chemins canoniques.

Reproduction : `.venv/Scripts/python.exe src/data_processing/build_accessibility_territorial_panel.py` depuis la racine. Les rapports 76–77 restent des audits par identifiant source ; ce rapport précise le bilan territorial à utiliser ensuite. Aucun nouvel accès externe n'a été nécessaire.

Prochain point à valider avant estimation : diagnostics de comparabilité et spécification de l'estimateur. Aucun filtre de communes, effet additionnel ou effet causal n'est choisi ici.
