# Plan d'élargissement des stations et communes

Décisions du chercheur des 1 et 2 octobre 2026. Ce plan prolonge la mission de `prompts/main_research_prompt.md` et ouvre une nouvelle branche de travail, centrée sur les communes et leur accessibilité aux stations. Les résultats Path C v0.31 restent ceux du périmètre antérieur.

## Principe

Une station peut être étudiée à travers les communes hôtelières accessibles depuis ses départs, même si sa propre commune n'a pas de série hôtelière. L'unité du futur panel sera la commune × mois, avec une exposition évoluant selon les entrées et sorties Magic Pass des stations accessibles. Les dix événements concernant des destinations entièrement étrangères sont hors périmètre. Pour un domaine transfrontalier, seule sa composante suisse pourra être retenue après clarification.

## Étapes convenues

| Étape | Travail et méthode | État |
|---|---|---|
| 1. Compter les ajouts possibles | Reprendre les 44 entrées liées à une station sans commune hôtelière, les trois domaines exclus pour périmètre incomplet et les 16 événements suisses ou à composante suisse sans identité directe. Compter séparément événements, fiches, groupes et séries communales. | Inventaire effectué, voir rapport 54 |
| 2. Résoudre et regrouper les stations | Documenter les identités manquantes et les domaines connectés par pistes ou remontées. Créer des groupes analytiques distincts des clusters existants. Additionner pistes et remontées sans doublons, garder les altitudes extrêmes et les dates d'adhésion par composante. Une commune ou un opérateur partagé ne suffit pas à prouver une connexion. | Terminé : 78 événements répartis dans 71 groupes, voir rapport 55 |
| 3. Réutiliser et compléter les accès | Auditer les points existants, localiser les départs utiles et conserver plusieurs accès par domaine lorsque nécessaire. Les approximations restent explicites. | Terminé pour le test initial : 75 accès, dont 3 proxys distants signalés |
| 4. Harmoniser les origines communales | Réutiliser les gares/arrêts déjà sélectionnés. Préciser la règle finale entre centre communal et gare principale et, si nécessaire, inclure le trajet jusqu'à l'arrêt. | Terminé : 186 origines existantes réutilisées avec leur règle documentée |
| 5. Vérifier la couverture hôtelière | Mobiliser d'abord les 186 séries déjà présentes. Rechercher ensuite les séries officielles supplémentaires disponibles, en distinguant absence de collecte, confidentialité et changements de communes. | Terminé localement ; extension externe différée |
| 6. Étendre les temps de trajet | Relier les origines communales aux accès des stations supplémentaires. Séparer voiture et transports publics et conserver les trajets non trouvés comme tels. | Transports publics terminés : 13 206 couples ; voiture différée faute de source routière validée, voir rapport 56 |
| 7. Construire l'exposition mensuelle | Croiser temps de trajet et historique Magic Pass. Conserver des seuils de sensibilité, le nombre de groupes accessibles et les entrées successives. | Terminé : seuils 30/60/90/120 min et deux ancrages temporels |
| 8. Vérifier l'histoire des accès | Pour les premiers tests, utiliser une accessibilité fixe explicitement supposée. Reporter l'audit historique détaillé après la collecte et les premiers essais, puis tester les changements importants et les cas influents. Les dates d'adhésion restent historiques. | Différé, conformément au choix du chercheur |
| 9. Construire le panel communal | Une ligne par commune × mois. Plusieurs entrées peuvent expliquer une même série de nuitées. Distinguer leurs contributions lorsque les dates et accès le permettent ; examiner un effet conjoint lorsque les entrées sont indissociables. | Terminé : 31 248 lignes et expositions multiples conservées |
| 10. Réexaminer la faisabilité | Recompter les unités utilisables et les fenêtres avant/après, examiner tendances, événements concomitants, expositions multiples et sensibilités. Une plus grande couverture ne suffit pas à valider un effet causal. | Terminé descriptivement : 34 groupes avec au moins un couple 24/24 ; 0 traitement causal approuvé, voir rapport 57 |

## Point d'arrêt levé

Le compte rendu de l'étape 1 a été remis avant la suite, puis le chercheur a autorisé les étapes restantes. Les rapports 55 à 57 documentent les groupes, les accès, les trajets, le panel et la faisabilité. L'audit historique détaillé et le temps routier restent des finitions séparées. Aucun effet causal n'est approuvé.

## Prolongement d'identification

Les rapports 58 et 59 prolongent l'étape 10. Ils montrent que les entrées par station ne sont pas toutes séparables et proposent comme unité principale la première exposition d'une commune au réseau accessible. Dix-neuf communes fondatrices passent le filtre temporel initial; 132 comparaisons communales sont disponibles mécaniquement et 95 couples ont été retenus pour revue. Le rapport 60 réduit ensuite l'audit historique à 39 trajets prioritaires et documente le téléchargement manuel requis du GTFS 2018. Ce screening n'approuve toujours aucun traitement, contrôle ou effet causal.
