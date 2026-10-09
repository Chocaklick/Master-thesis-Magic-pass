# Profils : décisions appliquées et limites restantes

9 octobre 2026. Les 71 groupes existants restent inchangés. Ce document complète, sans modifier, le [bilan de disponibilité](96_AUDIT_DISPONIBILITE_CINQ_DIMENSIONS_FR.md).

## Décisions validées

| Dimension | Règle retenue | État |
|---|---|---|
| Neige | Cinq hivers décembre–avril entièrement terminés avant l’entrée de chaque groupe ; SPASS en référence, IMIS en comparaison | 355 calendriers préparés ; moyennes non calculées |
| Pistes | Tracés actuels autorisés comme proxys, avec audit des changements documentés et réserve historique | Recherche et correspondance aux groupes à réaliser ; pas de tracé actuel présenté comme préentrée vérifié |
| Villes | Minimum du temps routier parmi Bâle, Berne, Genève, Lausanne, Lugano et Zurich ; six temps détaillés conservés | Calcul terminé pour les 71 groupes, 426 références conservées |

« Hivers communs » signifiait les mêmes cinq saisons pour toutes les stations. Ce n’est **pas** le choix retenu. Par exemple, pour une entrée en mai 2025, la fenêtre retenue va de décembre 2020–avril 2021 à décembre 2024–avril 2025. Les conditions décrivent ainsi le passé récent de chaque entrant ; les différences de neige peuvent aussi refléter des différences de période entre cohortes, pas seulement de station.

## Accès urbain calculé

Le calcul prend le minimum parmi six références existantes. Chaque référence est déjà la moyenne des directions aller et retour calculées indépendamment ; le choix d’accès au groupe reste celui de la matrice validée. Il ne s’agit donc pas de prendre séparément l’aller d’une ville et le retour d’une autre. Les ex æquo sont tous conservés, sans attribution arbitraire à une seule ville.

Mesure : **arrêt communal de la ville → arrêt de station**, trajet automobile statique modélisé. Pas de nouvelle requête, recherche de mairie ou parking, changement d’extrémités, supplément de circulation, neige ou marche. Le réseau actuel n’est pas un réseau préentrée vérifié ; les limites hivernales et d’accès légal restent celles du collecteur. Ce ne sont pas des origines observées de visiteurs.

Les minima vont de 32,07 à 129,44 minutes. Ces temps vers les grandes villes ne sont **pas** le seuil de traitement commune–station de 30 minutes, qui reste inchangé. Aucun groupe n’est éliminé sur cette base. Le détail conserve le raccordement maximal observé de chaque extrémité au réseau, repris de l’audit final : ces mètres ne sont pas des temps de marche ni une preuve de légalité de l’accès.

- [Minimum par groupe — 71 lignes](../data_processed/winter_profile_urban_minimum.csv).
- [Six références et raccordements — 426 lignes](../data_processed/winter_profile_urban_city_detail.csv).

## Neige : une limite temporelle à résoudre

L’archive SPASS locale, déjà contrôlée lors de sa récolte, couvre les années hydrologiques 1962–2023 : dernier jour le **31 août 2023**. Le calendrier demandé comprend **23 hivers au-delà de cette archive, concernant 14 groupes**. Ces dates restent dans le fichier, explicitement signalées, et ne sont ni remplacées par des saisons plus anciennes ni imputées. Aucun groupe n’est exclu. Les 332 autres calendriers sont dans la période de l’archive ; cela ne certifie pas encore la présence de cellules valides sur les pistes.

[Fenêtres approuvées et disponibilité calendaire — 355 lignes](../data_processed/winter_profile_approved_snow_windows.csv). Le champ `snow_mean_computed` reste faux : ce fichier ne contient pas de moyenne d’enneigement.

Suite : rechercher si une extension temporelle documentée peut couvrir les saisons récentes ; conserver les manques si elle n’existe pas. Toute substitution de source ou modification de fenêtre sera soumise à validation. En parallèle, vérifier les tracés et leur rattachement aux groupes avant de proposer le périmètre, les pondérations spatiales et la moyenne entre hivers. Pas de neige évaluée au parking ou de moyenne de stations-proxys éloignées présentée comme neige sur pistes.

## Sources, méthode et reprise

Parents déjà archivés : `DERIVED_ACCESSIBILITY_ROAD_DID_2026`, `DERIVED_ACCESSIBILITY_ROAD_FINAL_SNAPPING`, coordonnées BAV, `SLF_SPASS_HSCLQMD_GRID_1962_2023`. Transformation enregistrée sous `DERIVED_APPROVED_PROFILE_CONTEXT_2026_10_09` ; les champs des trois tables sont inscrits au dictionnaire. Aucune nouvelle source externe ou donnée neige extraite lors de cette étape.

Décisions : `config/winter_profile_operational_decisions_stage43.json`. Script : `src/descriptive/build_approved_profile_context.py`. Reprise depuis la racine : `.venv/Scripts/python.exe src/descriptive/build_approved_profile_context.py`. Le manifeste `reports/approved_profile_context_summary.json` vérifie les empreintes des entrées, sorties et résultats protégés ; une reprise exacte ne réécrit ni ne recollecte. Un rafraîchissement contrôlé du seul nouveau contexte refuse les sorties éditées.

Pas de nouveaux clusters, estimation d’effet, changement d’affectation ou filtre selon la significativité. La normalisation, les variables finales et la méthode de classification restent à valider après préparation des caractéristiques.
