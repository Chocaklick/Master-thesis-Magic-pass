# Sensibilité : topologie actuelle des transferts sur le GTFS 2018 — étape 16

## Principe

Cette variante ajoute au réseau 2018 uniquement les transferts entre arrêts publiés dans le GTFS officiel 2026 lorsque **les deux identifiants normalisés sont déjà actifs en 2018**. Elle ne crée aucun lien par simple distance et conserve tous les transferts 2018. Elle teste donc l'effet d'un changement de codage de la topologie des correspondances, mais ne prouve pas que chaque lien existait en 2018.

| Variante | Couples complets | Couples à 120 min ou moins |
|---|---:|---:|
| Transferts strictement publiés en 2018 | 9 / 39 | 3 / 39 |
| Marche inférée à 250 m | 39 / 39 | 22 / 39 |
| Topologie officielle 2026 projetée sur les arrêts 2018 | 39 / 39 | 24 / 39 |

Avec la topologie actuelle projetée, **14 / 19 communes** gardent au moins un groupe fondateur à 120 minutes ou moins et **6 / 19** gardent tous les groupes actuellement attribués. La différence médiane signée, calculée comme temps 2026 moins temps 2018, vaut -20.8 minutes.

## Décision méthodologique

Le scénario strict est une borne basse sous-connectée; la marche à 250 m est une borne plus permissive; la projection de la topologie officielle actuelle est la sensibilité structurelle la plus directement documentée. Les trois doivent rester visibles. Aucun drapeau causal n'est activé tant que le choix du scénario principal et les autres hypothèses d'identification ne sont pas validés.
