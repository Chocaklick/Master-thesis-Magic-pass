# Dynamique temporelle non équilibrée - étape 28b

**Statut : règle temporelle validée et support audité. Aucun effet n'est encore estimé.**

## Règle appliquée

- L'analyse principale pourra utiliser tous les mois postérieurs observés pour chaque commune, même si leur nombre diffère entre cohortes.
- Les effets seront distingués par mois relatif à l'entrée. La composition des cohortes et des témoins est donc publiée pour chaque mois relatif.
- Les périodes 0-5, 6-11, 12-23 et 24 mois ou plus serviront à vérifier une éventuelle atténuation, sans imposer une forme décroissante.
- Un saut postérieur permanent et les fenêtres communes 6/12/24 mois restent des sensibilités.
- Les mois prétraitement sont inventoriés. La période utilisée pour tester les tendances avant entrée et le mois de référence restent à définir avec l'estimateur.

## Support obtenu

Les nuitées observées couvrent 159 mois, de 2013-01-01 à 2026-03-01. Les 80 séries administratives exposées sur 80 ont au moins un mois postérieur observé. Elles représentent 79 territoires actuels, car Moutier BE (700) et JU (6831) sont deux identifiants du même territoire. Le raccordement du panel reste à valider avant estimation. Avec au moins une cohorte traitée et ses témoins principaux, le support va du mois relatif 0 au mois 100.

| Cohorte | Séries administratives exposées | Dernier mois relatif observé | Mois postérieurs avec au moins une issue observée |
|---|---:|---:|---:|
| 2017-11-01 | 41 | 100 | 101 |
| 2018-05-01 | 3 | 94 | 95 |
| 2019-05-01 | 3 | 82 | 83 |
| 2022-05-01 | 16 | 46 | 47 |
| 2023-05-01 | 9 | 34 | 35 |
| 2024-05-01 | 5 | 22 | 23 |
| 2025-05-01 | 3 | 10 | 11 |

## Composition des quatre périodes postérieures

| Période relative | Cohortes contributrices | Communes contributrices | Observations commune-mois traitées | Part après une entrée accessible supplémentaire |
|---|---:|---:|---:|---:|
| 0-5 mois | 7 | 76 | 456 | 0.0 % |
| 6-11 mois | 7 | 76 | 453 | 14.6 % |
| 12-23 mois | 6 | 73 | 869 | 28.2 % |
| 24 mois ou plus | 5 | 72 | 3802 | 56.6 % |

## Couverture des fenêtres de sensibilité

| Fenêtre avant + après | Communes traitées complètes | Cohortes représentées | Dont entrée supplémentaire dans la fenêtre postérieure |
|---|---:|---:|---:|
| 6+6 mois | 76 | 7 | 0 |
| 12+12 mois | 73 | 6 | 11 |
| 24+24 mois | 65 | 5 | 22 |

Les trois fenêtres peuvent être comparées sur les mêmes 65 communes disposant de toutes les observations requises à 24+24 mois. Les effectifs 76/73/65 ci-dessus décrivent leur couverture respective, pas une composition identique. Aucune estimation ni sélection définitive n'est effectuée ici.

## Limites avant estimation

76 séries disposent d'au moins une nuitée observée avant et après. Les quatre autres restent dans l'inventaire mais leur historique de résultat avant exposition manque sous l'identifiant courant : Blonay - Saint-Légier, Val de Bagnes, Laténa et Moutier (JU). L'historique antérieur de Moutier est déjà présent sous BFS 700 ; la reconstruction de sa part étrangère n'a pas encore été appliquée au panel de résultats. Les 80 séries ne constituent donc pas 80 unités indépendantes estimables.

46 communes traitées connaissent au moins une entrée accessible supplémentaire. Le choix validé conserve toute la trajectoire du réseau dans l'analyse principale ; les effets additionnels sont examinés séparément au rapport 77. Aucune attribution à une station ni censure du suivi n'est appliquée.

Une tendance contrefactuelle linéaire reste une hypothèse à diagnostiquer. Le présent audit ne valide ni tendances parallèles, ni forme linéaire, ni saut permanent. Aucun filtre de comparabilité, échantillon final ou estimateur n'est choisi.

## Décision sur les entrées successives

Le chercheur a choisi de garder la trajectoire du réseau après la première exposition : les 5580 observations postérieures restent disponibles. L'alternative non appliquée consistant à arrêter le suivi dès la prochaine entrée laisserait 3118 observations et 77 communes avec une observation postérieure. Le diagnostic des dates, bassins et variations permettant d'examiner séparément les ajouts figure au rapport 77 ; leur estimateur reste à définir.

## Fichiers de contrôle

- Support par cohorte et mois relatif : `reports/accessibility_dynamic_event_time_support_by_cohort_month.csv`.
- Support agrégé par mois relatif : `reports/accessibility_dynamic_event_time_support_by_event_month.csv`.
- Spécification approuvée : `config/accessibility_dynamic_event_time.json`.
- Sources internes : `reports/accessibility_cohort_comparison_universe.csv` pour les rôles et dates d'exposition ; `data_processed/accessibility_municipality_month_exposure.csv` pour les nuitées HESTA et entrées accessibles. Leurs empreintes SHA-256 figurent dans le résumé JSON. Aucun téléchargement supplémentaire.

Les témoins agrégés sont comptés seulement pour les cohortes-mois ayant au moins une issue traitée observée. Une commune témoin réutilisée dans plusieurs cohortes produit plusieurs observations commune-cohorte, sans devenir plusieurs communes indépendantes. Les tableaux décrivent la disponibilité mensuelle ; ils ne fixent aucune pondération d'estimation.
