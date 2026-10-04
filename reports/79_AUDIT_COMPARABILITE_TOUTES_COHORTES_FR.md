# Comparabilité descriptive de toutes les cohortes — étape 29c

Audit approuvé, sans filtre automatique ni choix d'estimateur. Les 79 territoires exposés restent recensés ; Moutier est une seule unité. Aucune commune n'est déclarée comparable ou exclue par un seuil.

## Disponibilité avant entrée

| Fenêtre diagnostique | Nuitées complètes | Tendance estimable algébriquement | Capacité disponible au moins un mois |
|---|---:|---:|---:|
| 6 mois | 76/79 | 0/79 | 76/79 |
| 12 mois | 76/79 | 0/79 | 76/79 |
| 24 mois | 75/79 | 76/79 | 76/79 |
| 36 mois | 70/79 | 76/79 | 76/79 |

Les historiques préexposition de Blonay–Saint-Légier, Val de Bagnes et Laténa restent manquants. Les fenêtres servent à diagnostiquer la couverture, pas à fixer la fenêtre d'estimation. Une seule année ou moins ne permet pas de séparer une tendance linéaire des effets propres aux douze mois.

## Comparaison avec tous les témoins autorisés

Les 10 500 couples candidats sont audités  sans classement ni top-5. Les témoins suivent l'option C : jamais ou pas encore exposés à l'entrée de la cohorte ; leur date de sortie est conservée. Les statistiques ci-dessous portent sur les 36 mois avant entrée et ne sont pas des estimations de l'effet du Magic Pass.

| Cohorte | Communes | Couples complets sur 36 mois | Corrélation médiane | Écart de tendance absolu médian (log/mois) | Mois COVID dans le prétraitement |
|---|---:|---:|---:|---:|---:|
| 2017-11 | 40 | 5069/5800 | 0.501 | 0.0055 | 0 |
| 2018-05 | 3 | 402/426 | 0.527 | 0.0092 | 0 |
| 2019-05 | 3 | 266/417 | 0.571 | 0.0083 | 0 |
| 2022-05 | 16 | 1372/1968 | 0.676 | 0.0129 | 25 |
| 2023-05 | 9 | 570/1026 | 0.423 | 0.0246 | 23 |
| 2024-05 | 5 | 540/545 | 0.227 | 0.0304 | 11 |
| 2025-05 | 3 | 315/318 | 0.661 | 0.0040 | 0 |

Une forte corrélation peut simplement refléter une saisonnalité commune. Le CSV conserve aussi l'écart entre profils saisonniers centrés, l'erreur standardisée, le nombre réel de mois appariés, le rang de la tendance et le ratio de capacités sur les mêmes mois observés. Des tailles hôtelières différentes ou une pente différente sont des diagnostics, pas des motifs automatiques d'exclusion. Les médianes portent sur les couples calculables et peuvent masquer des cas individuels.

## Chocs déjà documentés

18/79 communes exposées disposent d'une revue externe déjà réalisée. Les autres restent non revues : cela ne signifie pas absence de choc. Les preuves et limites des anciennes revues sont reprises, mais leur période se rattache au pilote autour de 2017. Leur validité pour chaque nouvelle fenêtre n'est pas automatiquement acquise, et les anciennes décisions d'exclusion ne sont pas réappliquées.

Les fenêtres prétraitement récentes peuvent traverser la pandémie : cette présence est comptée, sans exclusion. Une tendance prétraitement linéaire ajustée de la saisonnalité ne prouve pas que le contrefactuel restera linéaire après l'entrée.

La capacité varie fortement entre candidats : parmi 9852 couples calculables, le ratio des lits exposé/témoin a une médiane de 1.04, avec un intervalle interquartile de 0.38 à 2.78. Ce constat ne définit aucun filtre.

## Méthode, sources et reprise

Issue : champ existant `log_overnights = log(1 + nuitées)`, sans imputation. Corrélation et erreur standardisée utilisent les mois où les deux issues sont observées. Le profil saisonnier exige les douze mois calendaires représentés ; les années manquantes ne sont pas remplacées. La pente est une régression descriptive avec intercept, temps calendaire réel et onze indicatrices de mois, calculée seulement si le rang est complet et s'il reste des degrés de liberté. Les mois manquants ne compriment pas le temps. Aucun test de significativité ou seuil de succès n'est employé.

La capacité provient des séries HESTA déjà intégrées : médianes prétraitement, ratio des médianes sur mois communs, variation annuelle maximale absolue des lits observés. Les changements après entrée ne sont pas utilisés pour décider de la comparabilité prétraitement. Les sommes de groupes ou pistes ne sont pas assimilées à une capacité hôtelière.

- [Audit des communes](accessibility_all_cohort_comparability_municipalities.csv) : quatre fenêtres par commune, disponibilité, pente, capacité et preuves de chocs.
- [Audit de tous les couples](accessibility_all_cohort_comparability_pairs.csv) : métriques prétraitement, identifiants, rôles et sortie des témoins.
- `accessibility_all_cohort_comparability_summary.json` et `config/accessibility_all_cohort_comparability_audit.json` : résumé, règles, garde-fous et empreintes des entrées.
- Sources : panel territorial HESTA et univers de comparaison approuvés au rapport 78 ; revues de chocs traités et témoins des étapes 19–21 avec leurs sources originales. Aucun téléchargement supplémentaire.

Reproduction : `.venv/Scripts/python.exe src/causal_inference/audit_accessibility_all_cohort_comparability.py` depuis la racine. Prochaine décision : définir avec le chercheur l'estimateur par cohorte et mois, son mois de référence et les hypothèses de tendance ; un éventuel appariement ou filtre exige également un accord séparé. Aucun effet ou échantillon final n'est produit par cet audit.

Deux orientations à discuter : comparaison des changements par cohorte et mois avec les témoins autorisés, en gardant une variante de tendance linéaire comme sensibilité ; ou tendance linéaire préestimée et saut/dynamique comme modèle principal, sous une hypothèse d'extrapolation plus forte. Dans les deux cas, il reste à valider l'ajustement de saisonnalité, la référence, la pondération, l'incertitude et le traitement des trois historiques manquants avant calcul des effets.

Référence méthodologique déjà enregistrée : [Callaway et Sant'Anna, Difference-in-Differences with Multiple Time Periods](https://arxiv.org/abs/1803.09015v4), `CALLAWAY_SANTANNA_2021_DID`. Ce cadre traite des dates d'entrée échelonnées et d'effets hétérogènes, mais requiert toujours des hypothèses de tendances parallèles, éventuellement conditionnelles. Il ne résout pas automatiquement les écarts diagnostiqués ici. L'abstract de la version auteur a été consulté ; aucune implémentation spécifique n'est validée par cet audit.
