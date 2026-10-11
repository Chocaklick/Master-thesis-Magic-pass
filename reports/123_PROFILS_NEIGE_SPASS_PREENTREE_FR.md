# Profils neige SPASS avant l'entrée dans le Magic Pass

11 octobre 2026 — Étape 77, option A validée par ta réponse « A ».

## Résultat

Les **70 groupes sont conservés**, avec une ligne de profil par groupe et les 350 fenêtres hivernales originales. Les résultats SPASS sont désormais calculés indépendamment des valeurs OSHD.

| Situation | Groupes | Moyenne des cinq hivers |
| --- | ---: | --- |
| Cinq hivers et pistes observés | 34 | Calculée |
| Seulement trois hivers dans SPASS | 6 | Manquante, pas de moyenne réduite à trois hivers |
| Rattachement des pistes non résolu | 29 | Manquante |
| Axes référencés absents | 1 | Manquante |

Les six profils incomplets sont **Balmberg, Belalp, Linden, Meiringen-Hasliberg, Melchsee-Frutt et Sörenberg**, entrés en mai 2025. Leurs fenêtres 2023/24 et 2024/25 ne sont pas dans SPASS. Leurs trois autres moyennes hivernales sont conservées dans le détail, mais ne deviennent pas une moyenne « sur cinq hivers ».

La moyenne des cinq hivers des 34 groupes calculables varie de **0,093 à 1,173 m**, avec une médiane de **0,327 m** entre groupes. Ces mesures décrivent la hauteur de neige modélisée sur les pistes cartographiées, pas la neige réellement damée, l'enneigement artificiel ou les jours d'ouverture. Les fenêtres diffèrent selon l'entrée : leur comparaison mélange donc aussi des périodes climatiques différentes, conformément à la règle choisie.

## Méthode appliquée

- **Période :** les cinq hivers décembre–avril finissant strictement avant l'entrée de chaque groupe, sans changer leurs dates ni leur nombre.
- **Espace :** longueurs des axes uniques vérifiés dans les cellules natives SPASS à 1 km. Les subdivisions géométriques déjà établies sont regroupées par cellule SPASS, en conservant leur somme de longueurs. Aucun poids ne dépend d'une valeur ou d'un masque OSHD.
- **Jour :** moyenne des hauteurs SPASS pondérée par les seules longueurs effectivement observées ce jour. Un zéro est une observation ; une cellule masquée n'est pas remplacée par zéro. Pas d'interpolation ni de seuil de couverture ajouté.
- **Hiver :** moyenne donnant le même poids à chaque jour observé. Les jours attendus, observés et manquants et la couverture spatiale sont publiés.
- **Cinq hivers :** moyenne donnant exactement un cinquième du poids à chacun des cinq hivers. Si un hiver n'a aucune moyenne, le profil reste manquant. Aucun complément OSHD, aucune calibration ou imputation.

L'hypothèse SPASS en **mètres**, facteur 1, reste celle validée par toi ; la déclaration originale `UNKNOWN` n'est pas réécrite. Les géométries actuelles et leur réserve historique restent explicites. Une couverture de 100 % concerne les axes retenus, pas l'exhaustivité du domaine skiable.

Le détail contient **188 moyennes hivernales observées** : 185 à couverture spatiale complète et trois à couverture partielle pour Melchsee-Frutt (86,35 %). Tous leurs jours attendus sont observés ; aucun jour n'est imputé et aucune hauteur négative n'est détectée sur les portions utilisées. Les autres 162 lignes restent manquantes : 150 sans géométrie et 12 hors calendrier SPASS avec géométrie disponible. Le calendrier seul compte toujours 23 fenêtres hors SPASS pour 14 groupes, dont 11 cumulent aussi le manque de géométrie.

Dans la colonne `missing_winter_start_years`, une liste vide signifie « aucun hiver manquant », pas « liste inconnue ». Les autres absences numériques restent des cellules manquantes, jamais des zéros inventés.

## Sources, reprise et contrôles

Source originale déjà enregistrée : `SLF_SPASS_HSCLQMD_GRID_1962_2023`, fichier NetCDF conservé avec son SHA256. Calendriers : étape 57 ; longueurs uniques et indices natifs : étape 69 ; unité analytique : décision de l'étape 75. La nouvelle source dérivée `DERIVED_SPASS_PREENTRY_PROFILES_STAGE77` et les 49 champs des deux tables sont ajoutés aux registres, sans changer leurs lignes historiques.

**Aucune nouvelle collecte externe.** Les 35 caches mensuels SPASS de l'étape 76 et les cellules originales du pilote 2022/23 sont réutilisés. Seuls les 15 mois des trois hivers plus anciens, 2012/13–2014/15, sont lus dans l'original déjà présent, par le même lecteur figé. Les 11 checkpoints journaliers contiennent 28 422 lignes groupe–jour ; une reprise les vérifie sans refaire leur calcul. Le producteur et les contrats de cache gardent leurs empreintes.

**30 tests réussis**, dont contrôle indépendant des 28 422 moyennes journalières contre les cellules sources et longueurs originales, des 188 moyennes hivernales et des profils finaux. Zéros, cellules manquantes, poids égal des hivers, fenêtres strictement préentrée, identifiants, dictionnaire et résultats précédents sont vérifiés. Trois avertissements de dépréciation concernent le petit fichier NetCDF synthétique de test. **Audit de préservation réussi le 11 octobre à 06:42 UTC : 1 939 fichiers vérifiés**, incluant les 1 792 fichiers historiques correspondant aux 2 375 références antérieures. Les anciennes 1 228 sources, 8 317 variables et 2 056 entrées de collecte sont préservées exactement ; seuls les ajouts documentés de cette étape sont enregistrés. Le manifeste de l'étape 77 conserve les empreintes et contrôles des 11 checkpoints journaliers et des 51 références de caches mensuels ou du pilote. Aucun calcul ni collecteur ne reste actif.

- [Profils par groupe](../data_processed/spass_preentry_profiles_stage77.csv).
- [Détail des cinq hivers](../data_processed/spass_preentry_winter_stage77.csv).
- [Méthode et empreintes](spass_preentry_profiles_stage77_summary.json) ; [préservation](preservation_stage77_summary.json).

Commande reproductible depuis la racine : `.venv/Scripts/python.exe -X utf8 src/data_processing/build_spass_preentry_profiles_stage77.py`. Les sorties terminées sont figées : ne pas modifier le producteur puis réutiliser ses checkpoints sous la même version. Les originals, diagnostics OSHD, groupes reliés et panel communal de nuitées restent inchangés.

## Choix suivant : périmètre du clustering exploratoire

Le rapprochement exact par identifiant des tables existantes donne : longueur de pistes cartographiées, altitude pondérée, composantes nord/sud et est/ouest pour **40 groupes**, neige préentrée pour **34**, accès routier minimal aux six villes pour **70**. Les six dimensions réunies sont disponibles pour 34 groupes ; sans la neige, pour 40. Ce sont des comptes de disponibilité, pas des exclusions approuvées.

Trois possibilités, à valider avant ajustement :

1. **Pilote avec neige sur les 34 profils complets.** Garde toutes les dimensions, mais laisse 36 groupes non classés. Les groupes et communes restent dans le panel ; ce sous-ensemble n'est pas représentatif de tout le réseau par défaut.
2. **Pilote sans neige sur les 40 profils de terrain et d'accès.** La neige reste descriptive pour les 34 où elle existe ; 30 groupes restent non classés. Cette option augmente la couverture, mais les classes ne sont plus construites selon la neige.
3. **Compléter d'abord la géométrie des 30 groupes.** Cela retarde le clustering, sans résoudre à lui seul les hivers absents de SPASS.

Je propose de comparer les deux premiers pilotes comme diagnostic exploratoire, sans imposer une classe aux groupes incomplets ni choisir selon les effets DiD. Ce serait un nouveau choix : **aucun pilote n'est encore ajusté**. Les variables finales, la mise à l'échelle et les classes restent à valider selon le protocole de préparation existant (k-means/Ward, deux à quatre classes candidates). La longueur cartographiée n'est pas assimilée aux kilomètres officiels exhaustifs. Hébergement communal et effets moyens ne sont pas attribués arbitrairement aux stations ; concentration et parts cardinales restent descriptives, hors modèles automatiques.
