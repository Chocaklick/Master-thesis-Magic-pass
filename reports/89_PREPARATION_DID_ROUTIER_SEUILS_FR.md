# DiD routier : seuil à valider

7 octobre 2026. La reprise des tests avec les temps automobiles est demandée. Le maximum de 120 minutes doit être réduit ; aucun nouveau maximum précis n'est encore validé. Aucun test DiD routier n'a été exécuté à ce stade.

## Couverture selon le seuil

Les 185 territoires du panel sont conservés. Une commune est candidate à l'exposition lorsqu'au moins un accès à un groupe déjà entré dans le Magic Pass satisfait le seuil. Les effectifs ci-dessous portent sur la période disposant de nuitées, jusqu'à mars 2026.

| Maximum routier | Communes exposées candidates | Référence et calibration préalables calculables | Mois postérieurs avec nuitées observées |
|---:|---:|---:|---:|
| 15 min | 29 | 27 | 1 955 |
| 30 min | 56 | 52 | 3 732 |
| 45 min | 87 | 80 | 5 675 |
| 60 min | 102 | 97 | 6 998 |
| 120 min, comparaison seulement | 136 | 128 | 11 985 |

« Calculables » vérifie seulement l'existence de la référence à −1 mois et le rang/degrés de liberté de la calibration saisonnière pré36 déjà approuvée. Ce n'est ni une validation des tendances parallèles, ni une garantie de témoins disponibles à chaque date. Les historiques incomplets restent dans le panel et seront signalés, pas imputés.

## Méthode du diagnostic et sources locales

- Temps issus de `data_processed/accessibility_road_stop_pairs.csv` : moyenne des durées automobiles aller/retour utilisables, aux mêmes arrêts que les TP. Les trois véritables trajets au même arrêt sont à zéro conformément à la validation ; les valeurs manquantes et le zéro Saas-Fee non validé ne sont pas remplacés.
- Pour ce diagnostic uniquement : accès le plus rapide disponible parmi les accès de chaque groupe, puis seuil inclusif. Les 75 accès et 71 groupes existants restent inchangés. Cette règle signifie « au moins un accès du groupe dans le rayon temporel » ; elle sera explicitée avant estimation.
- Dates de première entrée et sorties documentées reprises de `data_processed/accessibility_station_groups.csv` et `data_processed/magic_pass_membership_history.csv`, selon la logique existante de `threshold_inventory` dans `src/data_processing/audit_accessibility_local_thresholds.py`.
- Nuitées originales et raccordement exact de Moutier repris de `data_processed/accessibility_municipality_month_exposure_territorial.csv`. Les contrôles de calculabilité réutilisent `seasonal_fit` dans `src/causal_inference/estimate_accessibility_cohort_time.py`, sans ajuster les paramètres aux résultats.
- Provenance du réseau, coordonnées, restrictions et raccordements : rapport `88_REFERENCE_ROUTIERE_ARRETS_TP_FR.md` et registres existants. Calculs locaux en mémoire, sans nouvelle requête API, nouvelle source externe, écriture de données ou remplacement d'un résultat ancien.

Lauterbrunnen (BFS 584) n'a aucun temps routier utilisable depuis l'arrêt communal retenu, Grütschalp. Dans le décompte brut, elle figure parmi les territoires sans exposition calculée : **cela ne signifie pas « non exposée »** et ne justifie pas son emploi comme témoin. Les restrictions des lieux sans voitures et les grands raccordements restent signalés ; aucun filtre géographique supplémentaire n'a été appliqué.

## Décisions avant relance

1. Valider le maximum principal et les seuils de sensibilité. Possibilité proposée : 30 minutes au principal, 15 et 45 minutes en sensibilité. C'est un choix de périmètre à valider, pas un rayon d'effet causal démontré ; ne pas le sélectionner selon la significativité des DiD.
2. Valider le traitement de l'accès inconnu : conserver Lauterbrunnen dans l'inventaire, avec rôle d'exposition/témoin indéterminé tant que l'accès n'est pas résolu. Aucun changement d'arrêt automatique.

À validation, recalculer les dates d'exposition et les témoins à chaque seuil, puis reprendre les contrastes cohorte/mois et leurs diagnostics approuvés : log(1+nuitées), référence −1, saisonnalité pré36, témoins jamais/pas encore exposés avec censure à leur entrée, trajectoire complète malgré les entrées successives, bootstrap territorial 4 999 tirages, sensibilités de tendance linéaire, COVID et horizons communs. Publier dans un nouvel espace de fichiers, conserver les résultats TP et comparer les compositions.

Réduire le seuil peut faire devenir témoins des communes anciennement exposées : leur absence d'exposition selon le seuil ne prouve pas leur absence de retombées. Une éventuelle zone tampon serait un choix supplémentaire à discuter, pas un filtre automatique. Aucun estimateur additionnel, seuil de raccordement, choix de communes ou certification causale n'est validé par ce diagnostic.
