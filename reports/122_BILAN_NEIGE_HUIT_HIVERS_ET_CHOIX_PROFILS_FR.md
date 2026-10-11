# Neige : bilan des huit hivers et choix pour les profils

11 octobre 2026 — Étape 76. Collecte et comparaison terminées. Les anciens résultats restent conservés ; le rapport 121 décrit les checkpoints intermédiaires.

## Résultat

Les huit hivers décembre–avril de 2015/16 à 2022/23 sont calculés, pour les trois décalages fixés −1/0/+1 jour. Les **70 groupes sont conservés** : 40 disposent de pistes exploitables et 30 gardent un résultat manquant pour absence de géométrie exploitable. Il n'y a aucune exclusion de commune ni duplication de nuitées.

Le tableau comporte 1 680 lignes : 960 comparaisons calculées et 720 cas sans géométrie (696 avec rattachement non résolu, 24 avec axes référencés manquants). Les effectifs sont des groupes, pas des observations indépendantes par jour.

Résultats au même jour civil, référence validée. Chaque nombre ci-dessous est une médiane entre les 40 groupes, et non une moyenne pondérée de tout le réseau.

| Hiver | Jours appariés par groupe | Écart moyen OSHD − SPASS (cm) | Écart absolu quotidien moyen (cm) |
| --- | ---: | ---: | ---: |
| 2015/16 | 152 | −15,89 | 20,60 |
| 2016/17 | 151 | −6,29 | 9,51 |
| 2017/18 | 151 | −26,51 | 29,76 |
| 2018/19 | 151 | −10,61 | 15,42 |
| 2019/20 | 152 | −12,94 | 17,89 |
| 2020/21 | 151 | −9,90 | 15,10 |
| 2021/22 | 151 | −10,43 | 14,78 |
| 2022/23 | 151 | −7,25 | 9,38 |

OSHD est plus bas en médiane chaque hiver, mais l'écart change nettement selon l'hiver et le groupe. En 2017/18, les différences de moyennes vont de −105,04 à +72,03 cm entre groupes. **Un décalage additif constant commun n'est donc pas justifié par ces seuls résultats.** Les écarts mesurent le désaccord de deux modèles, pas leur erreur par rapport à la neige réelle. Aucun raccordement n'est appliqué.

## Méthode et couverture

SPASS est interprété en mètres conformément à ta décision : facteur 1, unité originale `UNKNOWN` conservée. OSHD déclare `m`. Cette hypothèse d'unité n'est pas rebaptisée certification du fournisseur.

Pour chaque jour, les hauteurs sont pondérées par la longueur exacte des mêmes portions de pistes observées dans les deux grilles natives, sans interpolation. Chaque jour effectivement apparié reçoit ensuite le même poids dans la moyenne hivernale. Les décalages restent tous publiés ; aucun « meilleur » décalage n'est sélectionné. Zéro observé et absence restent distincts.

Les 40 groupes ont tous leurs 151 ou 152 jours appariés à chacun des trois décalages. La couverture spatiale commune atteint 100 % des axes retenus pour 39 groupes et 86,35 % pour Melchsee-Frutt. Cela n'établit pas l'exhaustivité des pistes OSM du domaine. Les géométries actuelles gardent leur réserve historique. Aucune hauteur négative n'est détectée dans les moyennes journalières comparées.

Ces huit hivers sont un diagnostic de compatibilité. Ils **ne remplacent pas les cinq hivers propres à chaque entrée**, dont les règles restent inchangées : décembre–avril, longueurs de pistes, poids égal de chaque hiver et moyenne des cinq manquante si un hiver est entièrement absent.

## Conséquence pour les futurs profils

Le calendrier des cinq hivers préentrée représente 350 fenêtres pour 70 groupes : 327 sont dans l'archive SPASS et 23, concernant 14 groupes, n'y sont pas. Ces nombres décrivent la disponibilité temporelle, pas des profils déjà calculés ni leur couverture spatiale.

Parmi les 40 groupes ayant des axes, 34 ont les cinq fenêtres dans SPASS ; six en ont trois sur cinq. Les 30 autres restent signalés pour leur géométrie. OSHD couvre temporellement les 23 fenêtres absentes de SPASS, mais ne résout pas les axes manquants. À lui seul, son calendrier contient les cinq fenêtres pour 39 des 70 groupes ; les autres en ont deux, trois ou quatre. Remplacer toute la série par OSHD ne règle donc pas le problème historique.

Il reste un choix de méthode à valider, sans regarder la significativité des futurs effets :

- **A — SPASS comme source principale unique**, avec ses cinq hivers préentrée ; laisser les moyennes incomplètes manquantes et conserver tous les groupes. OSHD reste une source séparée de comparaison. C'est l'option la plus simple pour éviter qu'un changement de modèle crée artificiellement un profil différent, mais elle ne comble pas les 23 fenêtres.
- **B — Étudier une harmonisation avant tout complément OSHD.** Il faudrait définir puis faire valider un protocole de calibration et de validation par groupe/hiver, tester sa stabilité et documenter l'incertitude. Les huit hivers offrent une base de comparaison, sans garantir une extrapolation fiable. Aucune substitution brute ni correction choisie pour améliorer les résultats DiD.

Je recommande A pour avancer avec une référence homogène, tout en conservant explicitement les lacunes. Aucune option n'est encore appliquée. Le traitement des profils incomplets dans le clustering et les modèles reste également à valider avant estimation.

## Sources, contrôles et reprise

Sources déjà enregistrées dans `metadata/data_sources_master.csv` : SPASS original conservé, OSHD [jeu de données SLF/Zenodo](https://zenodo.org/records/17313889), DOI `10.5281/zenodo.17313889`, licence CC-BY 4.0 ; poids communs de pistes issus de l'étape 69. Les identifiants sources et les 26 variables du tableau sont documentés dans les registres existants.

Les sept nouvelles archives OSHD WY2016–2022 sont complètes : **4 507 509 648 octets**, tailles et MD5 fournisseur vérifiés, SHA256 conservés. Le pilote 2022/23 est réutilisé sans nouvelle collecte. Les erreurs HTTP504 et mémoire restent au journal. La lecture quotidienne à mémoire bornée assemble exactement les mêmes valeurs mensuelles, sans changer le producteur numérique ni la méthode.

Contrôles finaux : **23 tests réussis**, dont recalcul NumPy indépendant des 960 comparaisons disponibles, années bissextiles, vrais zéros/manquants, cellules natives et contrats de reprise. Trois avertissements de dépréciation proviennent du fichier NetCDF synthétique de test. L'audit final réussit : 2 375 références SHA sur 1 792 fichiers historiques, préfixes des 1 218 sources / 8 291 variables / 1 585 événements anciens inchangés, sept nouvelles archives et **459 égalités quotidiennes→mensuelles à tolérance nulle** vérifiées. Les registres actuels contiennent 1 228 sources, 8 317 variables et 2 056 événements de collecte.

- [Tableau complet](../data_processed/snow_multiwinter_comparison_stage76.csv) et [résumé du calcul](snow_multiwinter_comparison_stage76_summary.json).
- [Collecte complète](oshd_multiwinter_collection_stage76_summary.json), [historique d'exécution](snow_multiwinter_runtime_stage76_summary.json) et [contrôle de préservation](preservation_stage76_summary.json).
- Reprise : lire d'abord `PROJECT_STATE.md` et `logs/research_journal.md`. **Ne pas relancer la collecte ni les calculs terminés.** Prochaine action : obtenir le choix A/B avant les profils neige, puis reprendre les caractéristiques et le clustering selon les validations existantes. Aucun nouveau regroupement, modèle DiD ou choix d'exclusion n'a été appliqué ici.
