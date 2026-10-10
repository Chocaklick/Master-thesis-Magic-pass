# Exposition du terrain : composantes continues et description

10 octobre 2026. Source des altitudes : **Office fédéral de topographie swisstopo**. Tracés : contributeurs OpenStreetMap. Les décisions exactes sont conservées dans `config/terrain_orientation_decisions_stage64.json`.

## Décision appliquée

Les deux composantes continues nord/sud et est/ouest sont autorisées comme variables candidates pour l’analyse et le clustering. La concentration et les quatre parts cardinales restent **descriptives**, sans intégration automatique aux modèles. Aucun clustering ni nouvel effet DiD n’est estimé ici. Aucun groupe, commune ou ancien résultat n’est supprimé.

Les angles détaillés du pilote restent dans le fichier Stage63 intact. L’exposition mesure la direction descendante du **relief**, pas la direction du tracé de piste. Une ligne de piste ne décrit pas toute sa largeur ni nécessairement le domaine exhaustif. Les tracés actuels et éditions du relief ne sont pas présentés comme des mesures préentrée vérifiées.

## Calcul et valeurs manquantes

Pour chaque cellule traversée, le poids est la longueur du réseau de pistes unique, selon les règles déjà validées. L’angle `a` est en radians dans les formules, avec nord = 0°, est = 90°, sud = 180° et ouest = 270°.

- Nord/sud = somme(longueur × cos(a)) / longueur avec orientation observée. +1 correspond au nord et −1 au sud.
- Est/ouest = somme(longueur × sin(a)) / même dénominateur. +1 correspond à l’est et −1 à l’ouest.
- Concentration descriptive = racine(nord/sud² + est/ouest²). C’est la longueur du vecteur moyen, pas une troisième caractéristique indépendante.
- Parts cardinales : nord [315°, 360°[ et [0°, 45°[ ; est [45°, 135°[ ; sud [135°, 225°[ ; ouest [225°, 315°[. Ces limites ont été validées séparément. Chaque angle appartient à un seul secteur.

Les moyennes et parts portent seulement sur les longueurs dont l’orientation est observée. Leur couverture est publiée par rapport à toute la longueur cartographiée. Les terrains exactement plats et les gradients manquants restent distingués, sans direction inventée. Sans orientation observée, les indicateurs restent manquants, jamais artificiellement nuls. Les quatre parts somment à 100 % de la longueur **orientable observée**, pas nécessairement de toute la longueur du groupe.

## Pilote St-Luc–Chandolin

Les deux éditions utilisent les mêmes 50,038 km d’axes cartographiés uniques. Toute cette longueur dispose d’une orientation observée ; aucun terrain plat ou gradient manquant n’apparaît dans ce pilote.

| Indicateur | 2019, comparaison | 2024, référence |
| --- | ---: | ---: |
| Composante nord/sud | −0,339 | −0,315 |
| Composante est/ouest | −0,530 | −0,512 |
| Concentration descriptive | 0,629 | 0,601 |
| Part nord | 8,34 % | 8,38 % |
| Part est | 3,56 % | 4,77 % |
| Part sud | 37,38 % | 36,22 % |
| Part ouest | 50,72 % | 50,63 % |

Ces différences sont des diagnostics entre éditions du relief, pas des effets du Magic Pass. Une composante proche de zéro peut résulter d’orientations opposées qui se compensent. La concentration ne distingue pas non plus une répartition uniforme de deux versants opposés : les parts descriptives et les angles détaillés doivent accompagner l’interprétation. Aucune orientation dominante n’est imposée.

## Fichiers, couverture et reprise

- [Référence : 70 groupes conservés, une ligne par groupe](../data_processed/terrain_orientation_reference_stage64.csv). Un pilote calculé, 39 autres groupes avec axes dont le relief reste à extraire, 29 périmètres non résolus et Sainte-Croix sans axes référencés. Ces manques ne sont pas des exclusions.
- [Comparaison séparée des deux éditions du pilote](../data_processed/terrain_orientation_edition_comparison_stage64.csv). Les deux lignes ne constituent pas deux stations indépendantes ; seule la référence 2024 rejoint le tableau de référence.
- [Formules, décisions, résultats et empreintes](terrain_orientation_stage64_summary.json). Source dérivée `DERIVED_TERRAIN_ORIENTATION_STAGE64` et toutes les variables inscrites dans les registres habituels.

Contrôles : 11 nouveaux tests réussis (poids inégaux, directions opposées, limites des secteurs, plats/manquants, calcul indépendant et conservation des 70 groupes) ; **331 tests réussis au total**, avec un avertissement NumPy/pandas déjà présent auparavant. Conservation de 970 références SHA sur 557 fichiers et de toutes les anciennes lignes des registres ; 696 sources et 7 968 variables uniques. Le journal de collecte n’a aucune nouvelle ligne. Un premier contrôle binaire a signalé les fins de ligne CRLF de Windows face au LF de Git ; les textes normalisés et toutes les valeurs CSV ont ensuite été vérifiés identiques, sans changer le journal.

Reprise sans nouvelle requête ni modification des sources :

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/summarise_terrain_orientation_stage64.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_piste_preservation_stage64.py
.venv/Scripts/python.exe -X utf8 -m pytest -q tests/test_terrain_orientation_stage64.py
```

Suite : étendre le relief aux autres périmètres cartographiés avec millésimes figés par tuile et couverture explicite, poursuivre les correspondances non résolues et les cinq hivers de neige propres à chaque entrée. La validation des composantes ne vaut pas validation de l’ensemble des variables historiques, du choix de groupes, de la standardisation, de l’imputation ou d’un modèle causal.
