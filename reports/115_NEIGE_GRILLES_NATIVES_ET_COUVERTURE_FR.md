# Neige : poids natifs et valeurs quotidiennes préparés

10 octobre 2026 — suite du [bilan précédent](114_PREPARATION_COMPARAISON_NEIGE_FR.md). Tes deux réponses sont appliquées dans de **nouvelles versions** ; les anciens résultats restent intacts. **70 groupes de stations et 185 territoires communaux sont conservés.** Aucun nouveau clustering, effet DiD ou raccordement entre modèles.

## Résultat

Les valeurs SPASS et OSHD sont extraites pour les **40 groupes disposant de tracés**. Sur décembre 2022–avril 2023 :

| Point contrôlé | Résultat |
|---|---|
| Groupes avec couverture commune complète | 39 sur 40, pour les 151 jours et chacun des trois décalages |
| Couverture de Melchsee-Frutt | 86,35 % de la longueur, pour chaque jour/décalage ; groupe conservé |
| Groupes sans axes utilisables | 30 conservés avec valeurs manquantes, pas zéro |
| Longueur unique de pistes candidates | 523,606 km, inchangée |
| Portions hors des deux grilles | Aucune ; cela ne garantit pas des valeurs de neige disponibles |
| Cellules natives utilisées | 325 SPASS et 1 852 OSHD ; pas autant de stations indépendantes |
| Séries quotidiennes | 18 120 lignes groupe–date–décalage ; 210 lignes de couverture pour tous les groupes |

Les trois décalages ont ici la même couverture. Les vrais zéros sont conservés ; aucune valeur négative n’est rencontrée sur le support commun. Cette absence ne justifie pas un filtre futur. Les valeurs manquantes restent manquantes.

[Couverture par groupe et décalage](../data_processed/native_snow_value_coverage_stage70.csv) · [Valeurs quotidiennes, unités sources distinctes](../data_processed/native_snow_daily_common_support_stage70.csv). **Ne pas soustraire les deux colonnes de neige : l’unité SPASS n’est pas certifiée.**

## Méthode appliquée

**Géographie.** Les axes uniques antérieurement validés sont inchangés. Les frontières effectivement lues dans les fichiers SPASS à 1 km et OSHD à 250 m sont emboîtées. Un découpage exact des axes selon leurs empreintes communes suffit donc ; aucune valeur de neige n’est interpolée ou rééchantillonnée. Les identifiants et indices natifs sont conservés, y compris l’ordre nord croissant de SPASS et décroissant d’OSHD. Les poids réagrégés à 1 km concordent avec un découpage indépendant directement à 1 km.

**Valeurs.** Pour chaque groupe, date et décalage, on retient exactement les mêmes portions dont les deux valeurs sont finies et non masquées par leur fichier source. Chaque moyenne vaut `somme(longueur × valeur) / longueur commune observée`. La couverture publiée distingue : observations dans les deux modèles, seulement SPASS, seulement OSHD, et dans aucun. Sans support commun, la moyenne reste manquante. Zéro n’est pas une donnée manquante ; aucune valeur négative n’est automatiquement retirée.

**Temps.** Les 151 dates SPASS de décembre–avril sont fixes. OSHD est apparié au même jour civil en référence, puis au jour précédent et suivant en sensibilité. Les jours limites 30 novembre/1er mai proviennent des fichiers effectivement disponibles. Aucun décalage n’est choisi pour améliorer les résultats. Horaires originaux 0 h/6 h et unités temporelles littérales sont conservés : ce n’est pas une simultanéité garantie ni une conversion de fuseau présumée.

Ce pilote est un diagnostic de compatibilité **sur une seule saison**, pas une nouvelle fenêtre préentrée. Tes **cinq hivers propres à chaque entrée** restent inchangés. Les tracés actuels restent des proxies avec réserve historique ; leur couverture ne certifie pas tout le domaine skiable. Les nuitées restent communales, sans duplication ni attribution d’effet à ces cellules.

## Unité SPASS : point non résolu

Le champ OSHD `hs` déclare **m**. Le champ SPASS `HSCLQMD` ne déclare aucune unité. L’[exemple officiel SWE2HS](https://git-pages.wsl.ch/aschauer/swe2hs/examples/transfer_two_dimensional_dataarray.html) choisit explicitement une sortie en centimètres : le logiciel permet de définir l’unité. Cela **ne prouve pas le paramètre utilisé pour le fichier SPASS distribué**. Le [catalogue EnviDat du produit](https://www.envidat.ch/metadata/spass---new-gridded-snow-datasets-for-switzerland) indique l’algorithme mais pas l’unité stockée dans les passages inspectés.

L’ancienne interprétation en mètres reste conservée comme inférence, séparée de l’unité fournisseur. Les moyennes SPASS sont ici en **unité source inconnue**, OSHD en mètres. Aucun biais, MAE/RMSE, ratio physique ou conversion nouvelle n’est calculé. Même un bon accord apparent ne certifierait ni l’unité ni un raccordement.

**Choix soumis pour la suite :** comparer d’abord les évolutions par corrélation de rang Spearman, séparément par groupe et aux trois décalages fixés, sans comparaison physique ; ou autoriser en plus un diagnostic de niveaux sous l’hypothèse provisoire « SPASS en mètres », clairement non certifiée. Aucun raccordement/calibrage automatique dans les deux cas. Une confirmation de l’échelle du fichier auprès du producteur serait la preuve directe ; aucun message externe n’a été envoyé.

## Sources, contrôles et reprise

Sources/méthodes : configurations `snow_comparison_decisions_stage69.json` et `snow_value_audit_stage70.json`. **1 201 sources et 8 188 champs uniques**, anciennes lignes préservées. Consultations documentaires enregistrées avec leurs limites : pas d’archive HTML, statut HTTP ou checksum inventés. Fichiers neige originaux et 12 mois WY2023 contrôlés par SHA ; valeurs extraites avec les masques natifs. Politique SPASS « WSL Data Policy », attribution OSHD Oberrauch et al., [dépôt CC-BY4.0](https://zenodo.org/records/17313889), et OSM/ODbL conservées ; aucune nouvelle licence n’est présumée. CSV quotidien de 7,24 Mo gardé localement, sans redistribution Git de ces valeurs dans ce jalon.

Revue finale du registre : correction documentaire du nom de colonne URL et explicitation des unités/conditions héritées sur les deux nouvelles sources Stage70 uniquement. Les cinq cellules avant/après sont conservées dans `config/native_snow_provenance_corrections_stage70.json` ; producteurs figés et résultats inchangés.

**Dix contrôles spécifiques et 363 tests complets réussis** ; un avertissement préexistant. Contrôles : indices/axes réels, découpage indépendant, dates/horaires, vrais zéros, absence de support, valeurs directement relues dans les sources, recalcul des moyennes, URL/conditions des nouvelles sources et préservation des anciennes lignes. **2 287 références SHA sur 1 740 fichiers vérifiées**, anciennes lignes de registres intactes, **1 569 événements de collecte inchangés**, aucun téléchargement nouveau. Le guide CSV scientifique a structuré les unités, dénominateurs et couvertures explicites, sans mise en page supplémentaire. Bilan complet consigné au journal.

Reprise, sans téléchargement :

```powershell
.venv/Scripts/python.exe -X utf8 src/data_processing/prepare_native_snow_weights_stage69.py
.venv/Scripts/python.exe -X utf8 src/data_processing/extract_native_snow_values_stage70.py
.venv/Scripts/python.exe -X utf8 src/data_processing/correct_native_snow_provenance_stage70.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_preservation_stage70.py
```

Les valeurs source extraites sont mises en cache par fichier avec indices, dates, masques et SHA ; aucune lecture de bloc complétée n’est répétée. Les contrôles d’intégrité des originaux restent effectués. Utiliser le dernier contrôle Stage70, les comptes des anciens contrôles restant historiques. Première préparation interrompue sur une sérialisation technique NumPy, corrigée sans changer le calcul ; incident enregistré dans le journal. Prochain travail : appliquer la réponse méthodologique sur les diagnostics, puis présenter leurs limites avant toute proposition de raccordement ou profils neige définitifs.
