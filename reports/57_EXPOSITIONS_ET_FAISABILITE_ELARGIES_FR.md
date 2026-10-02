# Expositions communales et faisabilité élargie — étapes 7 à 10

## Panel obtenu

Le panel final garde **une ligne par série communale et par mois** : **31,248 lignes**, 186 séries et une grille de 2013-01 à 2026-12. Les nuitées sont observées jusqu'en 2026-03; les mois ultérieurs restent dans la grille avec une issue manquante et ne sont pas traités comme des zéros. Une commune n'est plus assignée à une station unique. Elle peut être exposée simultanément à plusieurs groupes Magic Pass accessibles.

Les origines communales existantes sont réutilisées : gare ferroviaire desservie ayant le plus de départs dans la commune actuelle; à défaut, arrêt terrestre le plus desservi, puis arrêt desservi le plus proche. Il s'agit d'un point de référence de transport du centre communal, et non d'une affirmation que tous les hôtels se situent à cet arrêt. Moutier BE et Moutier JU gardent leurs deux séries sources mais partagent explicitement le même territoire communal actuel.

Pour chaque mois, quatre variantes sont conservées : temps moyen aller simple ≤ 30, 60, 90 et 120 minutes. Chacune contient le nombre de groupes actifs, les nouvelles entrées, les pistes/remontées connues cumulées sans doublon et le temps du groupe actif le plus proche. Le seuil n'est donc pas choisi à l'avance; il pourra être testé en sensibilité.

La matrice brute compte **459 couples** et **57 groupes** avec au moins une commune à 120 minutes. Après la règle de qualité des nœuds et des trajets, **386 couples** et **45 groupes** alimentent les fenêtres descriptives. Cette différence est conservée plutôt que masquée.

Deux temporalités sont distinguées. L'ancrage principal reprend la convention du projet : novembre 2017 pour le pass fondateur, puis mai de la saison d'entrée comme début commercial analytique. Une variante hivernale commence en novembre de chaque première saison et ne compte que novembre–avril. Elle évite d'interpréter automatiquement une adhésion au réseau comme une ouverture estivale de toutes les remontées.

## Entrées multiples

- couples groupe–commune à ≤ 120 minutes utilisables dans une fenêtre d'événement : **386**;
- lignes de fenêtre -36 à +36 mois : **28,178**;
- communes connaissant au moins une fois plusieurs groupes actifs à ≤ 120 minutes : **58**;
- maximum simultané : **20 groupes**.

La table événementielle contient, pour chaque entrée de groupe et chaque commune accessible, le nombre d'autres groupes déjà actifs, les autres entrées le même mois et l'écart à l'entrée voisine. On peut donc estimer séparément une entrée seulement lorsque son calendrier apporte de la variation; les entrées simultanées restent un effet conjoint.

Un premier diagnostic adjacent compare aussi, pour chaque couple complet, la moyenne des 24 mois après à celle des 24 mois avant. **34 groupes** ont au moins un tel couple à 120 minutes. Cette variation brute équilibre les saisons sur deux années mais ne corrige ni les tendances, ni le COVID, ni les entrées concurrentes : elle n'est pas un effet Magic Pass.

## Faisabilité

| Contrôle | Groupes |
|---|---:|
| Au moins une commune hôtelière à ≤ 120 min avec accès descriptivement utilisable | 45 / 71 |
| Au moins un couple avec 24 mois observés avant et 24 après | 34 / 71 |
| Au moins une commune sans autre entrée à ±12 mois | 16 / 71 |
| Fiche structurelle absente | 4 / 71 |
| Fiche structurelle incomplète | 1 / 71 |
| Traitements causaux approuvés | 0 |

Les groupes sans fenêtre 24/24 sont principalement les entrées récentes : Grenchenberg, Wilerallmi, Arolla, Axalp, Balmberg, Belalp, Charmey, Crans-Montana, Gantrisch-Gurnigel / Gurnigelbad, Bergbahnen Gstaad, Heimenschwand, Homberg.... Le fichier de faisabilité donne le diagnostic complet groupe par groupe.

Cette extension augmente fortement la couverture descriptive, mais ne crée pas automatiquement un contrefactuel. Les adhésions fondatrices simultanées, le COVID, les autres changements touristiques et les expositions croisées restent à traiter avant toute estimation causale.

## Hypothèses et travail différé

L'accessibilité de 2026 est tenue fixe pour ces premiers tests, comme convenu. Une seule sortie documentée, Crans-Montana après avril 2020, interrompt le report de l'exposition. Pour les autres groupes, la continuité depuis la première entrée est une hypothèse explicite, pas un fait annuel complètement audité. L'audit historique détaillé reste dans la liste de finition.

Le temps routier automobile n'est pas fabriqué à partir de distance à vol d'oiseau : le projet ne contient pas encore de moteur routier ou de matrice station–commune validée. Le panel actuel repose donc sur le transport public horaire; l'ajout routier est un chantier séparé documenté.

## Fichiers

- `data_processed/accessibility_municipality_month_exposure.csv` : panel commune–mois;
- `data_processed/accessibility_station_group_event_window.csv` : fenêtres groupe–commune -36/+36 mois;
- `data_processed/accessibility_station_group_pair_diagnostic.csv` : premier avant/après descriptif par couple;
- `reports/accessibility_station_group_feasibility.csv` : faisabilité par groupe;
- `reports/accessibility_expansion_feasibility_summary.json` : comptes et empreintes.
