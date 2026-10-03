# Audit externe des contrôles prioritaires - étape 20

**Statut : screening incrémental, pas validation causale.**

## Résultat

Les 7 communes témoins les plus réutilisées couvrent 15 des 32 paires du noyau strict précédent.

- **2 contrôles exclus** : Sursee et Maienfeld, soit **4 paires retirées** ;
- **5 contrôles conservés avec réserves ciblées**, soit **11 paires revues et conservées** ;
- le noyau candidat passe de **32 à 28 paires** ;
- il reste **17 contrôles / 17 paires** à documenter.

Les 7 communes traitées restent représentées. Aucune paire n'est encore approuvée causalement : les contrôles restants, les bassins touristiques et les tendances parallèles doivent encore être examinés.

## Décisions par contrôle

| Contrôle | Paires strictes | Décision | Motif court | Sources |
|---|---:|---|---|---|
| Emmen | 3 | conserver avec sensibilité | Aucun choc majeur repéré dans le rapport communal; capacité quasi stable. | EMMEN_ANNUAL_REPORT_2019 |
| Vitznau | 2 | conserver avec sensibilité | Programme touristique dès 2019: conserver seulement avec une sensibilité coupant 2019. | VITZNAU_TOURISM_PROJECTS_RETROSPECTIVE_2021 |
| Sursee | 2 | exclure du noyau strict | Ouverture en 2019 du FOCUS Hotel (64 chambres): exclusion du noyau strict. | SURSEE_FOCUS_HOTEL_HISTORY |
| Rorschacherberg | 2 | conserver avec sensibilité | Seulement un petit écart budgétaire touristique lié à l'impression; capacité en baisse graduelle. | RORSCHACHERBERG_ANNUAL_REPORT_2019 |
| Walenstadt | 2 | conserver avec sensibilité | Rénovation en 2018 d'un hôtel de 7 chambres: conserver avec test sans Walenstadt. | WALENSTADT_HOTEL_LOEWEN_RENOVATION_2018 |
| Maienfeld | 2 | exclure du noyau strict | Engagement de 10,1 M CHF pour le Heididorf annoncé le 2 novembre 2017: exclusion stricte. | MAIENFELD_HEIDIDORF_GRANT_2017 |
| Lenzburg | 2 | conserver avec sensibilité | Ouverture pré-ancrage d'un hôtel de 7 chambres: conserver avec test sans Lenzburg. | LENZBURG_BARRACUDA_OPENING_2017\|LENZBURG_BARRACUDA_OPERATOR_CURRENT |

## Pourquoi Sursee et Maienfeld sont retirés

Sursee connaît une modification directe du mécanisme de mesure : un hôtel de 64 chambres ouvre pendant la fenêtre postérieure et la plus forte hausse annuelle des lits survient en juin 2019. Maienfeld reçoit, le 2 novembre 2017, un engagement public pour une extension touristique de 10,1 millions de francs du Heididorf, qualifiée d'infrastructure d'importance systémique. Dans les deux cas, garder la commune comme témoin strict rendrait l'interprétation Magic-Pass-seul trop fragile.

## Contrôles encore à examiner

| Contrôle | Paires | Communes traitées | Alerte interne capacité |
|---|---:|---|---|
| Aarau | 1 | La Chaux-de-Fonds | aucune alerte mécanique |
| Amden | 1 | Haut-Intyamon | aucune alerte mécanique |
| Appenzell | 1 | Saignelégier | aucune alerte mécanique |
| Arbon | 1 | Haut-Intyamon | mean_available_beds_change_at_least_20pct\|maximum_year_on_year_bed_change_at_least_50pct |
| Dübendorf | 1 | Köniz | aucune alerte mécanique |
| Einsiedeln | 1 | Bulle | aucune alerte mécanique |
| Emmetten | 1 | Haut-Intyamon | aucune alerte mécanique |
| Frauenfeld | 1 | La Chaux-de-Fonds | aucune alerte mécanique |
| Freienbach | 1 | Bulle | aucune alerte mécanique |
| Gais | 1 | Saignelégier | aucune alerte mécanique |
| Kreuzlingen | 1 | Gruyères | aucune alerte mécanique |
| Liestal | 1 | La Chaux-de-Fonds | aucune alerte mécanique |
| Pratteln | 1 | Fribourg | aucune alerte mécanique |
| Sarnen | 1 | Bulle | aucune alerte mécanique |
| Schaffhausen | 1 | Fribourg | aucune alerte mécanique |
| Sigriswil | 1 | Fribourg | aucune alerte mécanique |
| Winterthur | 1 | Fribourg | aucune alerte mécanique |

## Méthode et limites

La priorité est purement opérationnelle : revue d'abord des contrôles utilisés dans au moins deux paires. Chaque preuve positive est archivée avec URL, date et SHA-256. Les variations de capacité hôtelière complètent les documents sans être interprétées seules comme causalité. Une recherche sans résultat ne prouve jamais l'absence d'un choc.

Les décisions sont volontairement asymétriques : un grand choc documenté suffit à exclure un contrôle du noyau strict; une petite rénovation ou un programme tardif peut être conservé uniquement avec la sensibilité indiquée. La proximité réseau actuelle ne valide pas un bassin touristique historique.

## Fichiers produits

- `reports/accessibility_high_leverage_control_external_shock_evidence.csv` : preuve et décision pour les 7 contrôles ;
- `data_processed/accessibility_comparison_high_leverage_control_external_risk_screen.csv` : 70 paires avec le statut étape 20 ;
- `reports/accessibility_remaining_control_external_review_worklist.csv` : les 17 contrôles restants ;
- `reports/accessibility_comparison_high_leverage_control_review_summary.json` : compteurs et empreintes.
