# Audit d'identification de l'exposition communale — étape 11

## Conclusion

L'élargissement améliore fortement la couverture descriptive, mais les **34 groupes** ayant au moins une fenêtre 24/24 ne fournissent pas 34 effets de station identifiables. Sur **277 couples groupe–commune complets**, **185** chevauchent la période COVID et seuls **15 couples appartenant à 3 groupes** passent le filtre temporel mécanique : issue 24/24 complète, aucune autre entrée accessible à ±12 mois et aucun mois COVID. Les groupes concernés sont Schwarzsee, Tramelan, Villars-Gryon-Les Diablerets. Ils restent non causaux faute d'accès historique validé et de groupe de comparaison audité.

Toutes les fenêtres complètes des cohortes postérieures à 2017 croisent le COVID. Pour les fondateurs de 2017, le lancement simultané du réseau reste un choc commun même lorsqu'une commune n'a qu'un groupe accessible en 120 minutes.

## Pourquoi les effets par station se confondent

Avec effets fixes commune et mois, les 34 colonnes d'exposition au seuil de 120 minutes n'ont qu'un **rang de 31**. Trois paires partagent exactement la même date et la même empreinte communale : **Mayens de Conthey / Anzère; Grimentz-Zinal / St-Luc / Chandolin; Aeschiallmend / Faltschen**. Leurs effets individuels ne peuvent pas être séparés avec cette définition; seul un effet conjoint ou une exposition regroupée serait estimable.

| Seuil | Couples utilisables des 34 groupes | Colonnes non nulles | Rang avec effets fixes commune + mois |
|---:|---:|---:|---:|
| 30 min | 5 | 5 | 5 |
| 60 min | 39 | 23 | 20 |
| 90 min | 116 | 32 | 28 |
| 120 min | 309 | 34 | 31 |

## Entrées successives dans une même commune

Parmi les 186 séries, **80 communes** ont au moins un groupe descriptivement accessible, **46** connaissent plusieurs mois d'entrée distincts et **27** disposent d'au moins deux fenêtres 24/24 complètes. Cependant, **0 commune** n'a deux entrées à la fois isolées et hors COVID. Les entrées successives peuvent donc être comparées descriptivement, mais elles ne permettent pas encore d'attribuer causalement chaque variation de nuitées à une station précise.

## Piste recommandée : première exposition au réseau

Une unité plus défendable est la **première exposition d'une commune à au moins un groupe Magic Pass accessible**, en conservant comme intensité le nombre de groupes entrant simultanément. Le seuil 120 minutes donne 80 communes exposées et 106 jamais exposées dans la matrice actuelle. Pour la cohorte fondatrice, **19 communes** ont une issue 24/24 complète, aucune entrée supplémentaire pendant les 24 mois postérieurs et aucun chevauchement COVID. En face, 132 communes complètes ne connaissent aucune entrée accessible pendant la même fenêtre, dont 99 ne sont jamais exposées.

Ce comptage justifie un **screening de comparabilité pré-traitement**, pas encore une estimation DiD. Avant toute approbation, il faut vérifier les tendances préalables, l'accessibilité historique des 19 communes traitées prioritaires, les chocs touristiques locaux, les effets de débordement et la cohérence du groupe de comparaison.

## Décision méthodologique

- Ne pas estimer 34 coefficients de station comme s'ils étaient indépendants.
- Conserver les diagnostics par station comme résultats descriptifs.
- Tester ensuite un traitement principal au niveau communal : première exposition au réseau, avec intensité initiale et entrées ultérieures explicites.
- Garder **zéro traitement et zéro contrôle causal approuvés** jusqu'aux audits de comparaison et d'accès historique.

## Fichiers

- `data_processed/accessibility_identification_pair_audit.csv` : blocages par couple groupe–commune;
- `reports/accessibility_identification_group_audit.csv` : statut des 71 groupes;
- `reports/accessibility_identification_municipality_audit.csv` : entrées successives des 186 séries;
- `reports/accessibility_first_exposure_audit.csv` : première exposition et candidats du dessin communal;
- `reports/accessibility_identification_cohort_audit.csv` : diagnostic par cohorte;
- `reports/accessibility_identification_overlap_audit.csv` : chevauchement des empreintes;
- `reports/accessibility_identification_summary.json` : comptes et empreintes des entrées.
