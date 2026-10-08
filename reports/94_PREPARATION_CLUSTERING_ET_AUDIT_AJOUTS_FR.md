# Profils de stations et effet des nouveaux arrivants

8 octobre 2026. Préparation et audit autorisés par « vas y ». **Aucun nouvel effet estimé, aucun clustering ajusté, aucune commune exclue.** Décembre–avril, route principale à 30 minutes, sensibilités 15/45 minutes. Les 71 groupes existants restent distincts des 185 territoires communaux ; les anciens résultats sont conservés.

## 1. Ce que l’audit permet de distinguer

L’audit reconstruit l’exposition à chaque groupe sur les mois hivernaux où les nuitées communales sont réellement observées. Il vérifie les colonnes identiques et leurs dépendances après retrait des composantes commune et mois calendaire. **C’est un diagnostic de variation, pas une estimation ou une preuve causale.**

| À 30 minutes | Groupes | Interprétation |
|---|---:|---|
| Variation algébrique distincte | 39 | Effet individuel envisageable, mais témoins et hypothèses encore à vérifier |
| Exposition exactement identique à d’autres groupes | 22 | Contribution individuelle non séparable dans ce design ; variation conjointe seulement |
| Autres dépendances linéaires | 5 | Des colonnes différentes ne suffisent pas pour identifier tous les coefficients |
| Aucune exposition hivernale observée dans ce panel | 5 | Pas de support ici ; groupes conservés dans l’inventaire |

Les 66 colonnes exposées ont un rang de 51, soit 15 dépendances. Les 22 groupes à colonne identique forment neuf ensembles, notamment **Grimentz-Zinal / St-Luc-Chandolin**, **Charmey / La Berra**, **Arolla / Evolène / La Forclaz**. Il ne s’agit pas de fusionner ces groupes physiques : seulement de reconnaître une variation commune dans le panel à ce seuil. Les autres dépendances concernent Crêt-du-Puy, Les Bugnenets-Savagnières, Nax, Ovronnaz et Vercorin. L’absence d’exposition observée concerne Eriz, Jaunpass, Lauchernalp-Lötschental, Rüschegg-Eywald et Sörenberg ; elle ne signifie pas que ces stations n’influencent aucune commune suisse.

| Seuil routier | Communes exposées | Groupes exposés | Rang / colonnes | Communes avec ajout ultérieur |
|---|---:|---:|---:|---:|
| 15 min | 30 | 38 | 26 / 38 | 3 |
| **30 min** | **58** | **66** | **51 / 66** | **24** |
| 45 min | 88 | 70 | 63 / 70 | 60 |

Ces sensibilités ne serviront pas à retenir le seuil qui donne un effet significatif. Les catégories ci-dessus concernent toute l’exposition observée, pas uniquement les ajouts successifs.

## 2. Effet additionnel : support beaucoup plus limité

À 30 minutes, on compte **30 dates d’ajout commune–hiver dans 24 communes**, concernant **24 groupes entrants**. Ce ne sont pas 30 expériences indépendantes.

- 19 groupes ont au moins un ajout avec l’hiver précédent et le premier hiver suivant entièrement observés.
- 7 ont au moins un tel ajout où ils sont le seul nouveau groupe accessible.
- **2 seulement** ont un candidat de comparaison conservant exactement le même portefeuille antérieur : **Gspon et Homberg**.

Concrètement : Gspon rejoint l’exposition de **Saas-Grund en hiver 2023/24**, avec un candidat ; Homberg celle de **Spiez en 2024/25**, avec deux candidats. Ces candidats partagent aussi la date de première exposition au réseau. Les identifiants BFS sont fournis dans le tableau des événements. Les effectifs sont trop faibles pour annoncer dès maintenant des estimations individuelles fiables.

Le diagnostic exige : mêmes groupes actifs en octobre précédent, aucun ajout ou retrait pendant l’hiver étudié, cinq mois observés dans les deux hivers adjacents. Une seconde variante vérifie aussi la date initiale d’exposition. **Aucune de ces exigences n’est appliquée comme filtre définitif.** Elles servent à mesurer ce qu’exigerait une comparaison très stricte. Composition antérieure complète, ancienneté de chaque groupe, tendances, chocs, changements de capacité et voisinage restent à examiner ; le même portefeuille ne suffit pas.

Options à discuter avant estimation : comparaison individuelle stricte, potentiellement très peu précise ; comparaison plus souple de portefeuilles/histoires explicitement définie ; ou effet d’un ajout par profil/dose, plus mutualisé mais sans prétendre isoler chaque station. Un simple compteur de groupes n’identifie pas leur contribution individuelle. Références déjà enregistrées : [traitements changeants](https://arxiv.org/abs/2007.04267v14), [traitements multiples](https://arxiv.org/abs/2012.10077v8).

## 3. Clustering complémentaire : protocole préparé, dates à établir

La structure actuelle est complète pour 66 groupes, incomplète pour un et absente pour quatre. Mais ses dates d’observation restent inconnues : **aucun profil structurel complet n’est encore vérifié avant l’entrée**. Les anciennes classes sont conservées comme comparaison descriptive ; elles ne deviennent pas des catégories historiques.

Triage ciblé de trois archives déjà récoltées : Leysin (24 février 2017, page 1) et TVGD/Ormont-Dessus (29 mai 2017, page 1) documentent des projets de composantes, pas toute la capacité du groupe. La Braye (31 juillet 2018, texte des pages 1–4, tableau page 3 vérifié visuellement) décrit une vente après l’entrée de novembre 2017 ; ses lignes de biens ne sont pas un décompte vérifié des remontées avant entrée. Aucun chiffre structurel n’a été inventé/transféré. Les autres groupes sont **non encore examinés historiquement**, pas réputés sans archive.

Proposition à valider :

| Élément | Proposition et limite |
|---|---|
| Variables centrales | Kilomètres de pistes et altitude supérieure du **groupe**, historiquement vérifiés ; deux dimensions lisibles |
| Remontées | Variante avec leur nombre : informative, mais peut surpondérer la taille déjà représentée par les pistes |
| Hébergement | Contexte communal pré-entrée séparé ; ne pas attribuer les lits d’une commune à une station sans règle validée |
| Préparation | `log1p` des variables de taille puis standardisation ; comparer à la standardisation sans logarithme |
| Classification | Comparer k-means et Ward, 2–4 classes candidates ; séparation, stabilité et interprétation avant les effets |
| Manquants | Pas d’imputation approuvée. Présenter la couverture historique avant de décider du périmètre ajustable |

Les caractéristiques doivent précéder l’entrée **au pass de base**, pas seulement le premier hiver ; les mois mai–octobre déjà exposés ne sont pas un prétraitement. Les périodes et périmètres des inventaires doivent être comparables. Plusieurs profils peuvent coexister dans le portefeuille initial d’une commune : aucune moyenne, pondération ou affectation au seul groupe le plus proche n’est décidée ici.

## Fichiers, sources et reprise

- [Audit par groupe et seuil](winter_entrant_group_audit.csv).
- [Événements, support et candidats BFS](winter_entrant_event_support.csv).
- [Disponibilité des caractéristiques, 71 groupes](winter_clustering_feature_readiness.csv).

Source dérivée `DERIVED_WINTER_ENTRANT_PREPARATION_2026_10_08` et toutes les colonnes enregistrées dans les deux registres metadata. Archives déjà enregistrées sous `LEYSIN_CHAIRLIFT_PREAVIS_2017`, `ORMONT_DESSUS_TVGD_LOAN_PREAVIS_2017`, `CHATEAU_DOEX_LA_BRAYE_2018` ; inspection limitée décrite dans `config/winter_profile_historical_source_review.json`. Aucune nouvelle collecte routière ou externe. Projection numérique reprise de l’ancien audit des entrées successives, mais recalculée avec la route actuelle et décembre–avril. Avril 2026 manquant reste manquant ; retrait de Crans-Montana conservé avec avril 2020 inclus. Réseau routier actuel fixé historiquement et limites d’accès légal/hivernal inchangés.

Reprise : `.venv/Scripts/python.exe src/descriptive/audit_winter_entrant_preparation.py`. Le manifeste `winter_entrant_preparation_summary.json` vérifie les empreintes des sources, résultats et anciens fichiers ; reprise identique sans réécriture, clustering ou estimation. Prochaine décision : variables/préparation du clustering et degré de comparabilité pour les ajouts. Les catégories finales, agrégation du portefeuille et protocole d’estimation restent à valider.
