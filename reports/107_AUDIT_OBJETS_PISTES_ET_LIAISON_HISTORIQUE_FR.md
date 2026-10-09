# Pistes : contrôle des objets et liaison historique

10 octobre 2026. Anciennes données conservées ; aucune sélection selon les résultats statistiques.

## Objets contrôlés

L’étape 54 contrôle les 710 objets rattachés aux 39 sites vérifiés, tout en conservant les 71 groupes d’origine. Après le regroupement Eischoll–Unterbäch validé séparément, l’étape 56 couvre **773 objets pour 40 groupes sur 70** : 765 axes candidats et 8 surfaces explicites. Les 30 groupes sans correspondance résolue restent présents, avec des comptes manquants plutôt que des zéros.

Les objets ont été raccordés au précédent inventaire par type, identifiant et version OSM, avec contrôle des empreintes des originaux. La simplicité des lignes, les répétitions exactes de coordonnées, les arêtes partageant deux nœuds consécutifs et les tags d’abandon/désaffectation ont été contrôlés. Aucun rapprochement par tolérance, réparation, suppression ou changement de coordonnées.

Résultats : pas de duplication complète de séquence géométrique ni d’axe auto-intersectant détecté ; 27 objets partagent au moins une arête avec un autre objet. **Cela ne signifie pas 27 pistes dupliquées** : les cas comprennent aussi des frontières communes entre surfaces ou entre un axe et une surface. Deux descentes de Moosalp sont taguées `abandoned=yes`. Quatre objets apparaissent dans une autre relation de site, dont les trois descentes du doublon Rossberg déjà documenté. Tous restent conservés ; ces alertes ne constituent pas une exclusion automatique.

La correspondance actuelle d’un site n’est pas encore une certification de l’usage de chaque piste pour les profils. Les kilomètres de groupe, hectares, altitude, orientation et neige ne sont pas calculés ici. Le traitement des portions superposées a été soumis au chercheur avant toute pondération finale.

[Objets : version actuelle, étape 56](../data_processed/winter_profile_verified_piste_member_qa_stage56.csv) · [Bilan des 70 groupes](../data_processed/winter_profile_verified_piste_group_qa_stage56.csv). Les tables de l’étape 54 restent disponibles pour comparaison.

## Eischoll–Unterbäch avant l’entrée

Sept originaux nouveaux sont archivés : quatre rapports annuels de l’opérateur, sa page d’archives et deux récits de visites. Les trois rapports préentrée examinés (2019/20, 2020/21, 2021/22) ne mentionnent pas Eischoll. Le rapport 2022/23, publié après l’entrée, traite de coopération commerciale : **un forfait commun ne prouve pas une liaison à skis**. Couverture 2021/22 et page 14 du rapport suivant rendues et inspectées.

Le [récit Enviadi de Felix Gross](https://www.enviadi.com/blog/eischoll-unterbaech-augstbordregion) décrit les deux chemins de liaison. L’original indique publication le 10 mars 2022 et modification le 7 juillet 2022, donc avant mai 2023. Le [récit d’une visite en février 2021](https://snow-and-sun.blogspot.com/2021/08/unterbach-februar-2021.html) corrobore un passage, mais indique une modification en 2025 : il n’est pas présenté comme une version figée de 2021. La [source officielle actuelle d’Eischoll](https://www.eischoll.ch/ski-snowboard/) confirme la liaison actuelle.

Conclusion : liaison antérieure **corroborée par un récit daté et la confirmation officielle actuelle**, pas par un plan officiel historique retrouvé. Les dates des récits sont déclarées par leurs éditeurs ; aucune archive indépendante de la version 2022 n’est revendiquée. Cette réserve a été exposée au chercheur, qui a validé le regroupement dans une nouvelle version. Voir le [bilan du regroupement](108_REGROUPEMENT_EISCHOLL_UNTERBAECH_FR.md).

## Reprise et limites

Sources inscrites dans le registre, définitions des diagnostics dans le dictionnaire. Recherche finie de 14 requêtes, URLs et identifiants conservés dans les deux journaux de découverte de l’étape 54 ; aucun extrait de recherche ne remplace l’original. Originaux, dates et empreintes : [audit historique](piste_history_stage54_summary.json). Rejouer `audit_piste_history_stage54.py` et `audit_verified_piste_members_stage56.py` depuis la racine ; pas de téléchargement nécessaire. Les anciens instantanés restent intacts. Résolution terrain de 2 m, cinq hivers préentrée et rôles distincts axes/surfaces restent ceux validés ; les choix supplémentaires ne sont pas imposés.
