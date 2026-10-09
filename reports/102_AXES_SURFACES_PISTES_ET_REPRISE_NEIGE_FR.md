# Pistes : axes, surfaces et sources vérifiées

9 octobre 2026 — Stage49. Suite du [bilan neige précédent](101_NEIGE_GRILLES_ET_SOURCES_PISTES_FR.md). Les **71 groupes de stations et 185 territoires communaux restent conservés**. Aucun ancien résultat, seuil routier ou regroupement de remontées n’est remplacé.

## Règles validées

| Géométrie | Mesures prévues après vérification des correspondances |
|---|---|
| Axes de pistes | Longueur unique ; altitude minimale, maximale et moyenne pondérée par longueur ; pente et exposition du relief swissALTI3D à 2 m |
| Surfaces de pistes | Superficie **cartographiée** en hectares/km², après union des recouvrements |
| Sept tracés fermés sans type explicite | Conservés mais **non mesurés avant vérification individuelle** |

Pas de pourtour de polygone compté comme piste, pas d’axe inventé au centre d’une surface, pas de mélange des pondérations lignes/surfaces. Les surfaces ne remplacent pas les axes pour les indicateurs altitude, orientation ou neige. Leur couverture OSM ne représente pas nécessairement la surface réelle complète du domaine.

Les décisions sont enregistrées dans [le protocole axes/surfaces](../config/winter_profile_geometry_roles_decisions_stage49.json) et [la validation des sept cas](../config/piste_ambiguous_geometry_decisions_stage49.json). Les règles antérieures restent : exposition du **terrain**, pas direction du tracé ; cinq hivers décembre–avril entièrement préentrée propres à chaque groupe, de poids égal ; aucune imputation ni suppression automatique d’un groupe.

## Ce qui a été fait

L’inventaire des deux extractions OSM conserve les identifiants, versions, dates et sources originales. Il distingue **9 948 objets**, et non autant de pistes complètes :

- 8 793 objets candidats axes ;
- 838 objets explicitement cartographiés comme surfaces, dont trois attendent la vérification de leur relation multipolygone ;
- sept tracés fermés ambigus ;
- 228 relations de parcours et 82 multipolygones, non ajoutés comme axes indépendants.

Les sept identifiants sont `551031993`, `551342308`, `560349845`, `560499042`, `562826738`, `670568310`, `670568333`. Ils n’ont pas de nom dans l’extraction. Leur longueur et superficie restent manquantes, pas nulles. Leur interprétation individuelle reste à établir avec une preuve adaptée.

[L’inventaire CSV](../data_processed/winter_profile_piste_geometry_roles.csv) contient les diagnostics **par objet**. Il ne contient encore aucune caractéristique GIS validée par groupe. La fonction d’union des surfaces est testée sur recouvrements et trous, mais aucune superficie de groupe n’est encore calculée.

Les **72 pages officielles prévues sont archivées et vérifiées par SHA256**. Elles couvrent 68 groupes via les identifiants existants de carte et d’accès, sans rapprochement automatique par nom ou distance. Les trois références de repli restent conservées : Château-d’Œx–La Braye, Crans-Montana et Lauchernalp–Lötschental. Les pages actuelles ne certifient pas le périmètre historique d’avant entrée et ne suffisent pas seules à affecter les objets OSM.

[Le suivi des 71 groupes](../data_processed/winter_profile_official_page_coverage_stage49.csv) publie la disponibilité des documents, pas une couverture complète des pistes. Les titres et liens réellement présents sont conservés dans [l’audit des pages](piste_official_page_audit_stage49_summary.json). Les 70 nouvelles pages sont enregistrées ; les deux pages déjà archivées sont réutilisées sans modifier leurs anciennes fiches sources. Les événements de collecte ont été raccordés au journal commun.

Deux sources complémentaires sont vérifiées : [les installations des Rasses](https://www.ski-vaud.ch/web/ski/les-pistes) et [le plan régional de la Vallée de Joux](https://static.mycity.travel/manage/uploads/6/26/452439/1/plan-des-pistes-de-ski-alpin.pdf). Le PDF a été rendu et examiné visuellement. Il confirme les trois composantes retenues, mais inclut aussi un panneau Dent de Vaulion sans le même marquage Magic Pass : **aucune composante ajoutée**. Ce plan schématique n’est pas converti en axes géographiques. Les noms d’installations des Rasses ne sont pas assimilés à un nombre de pistes ou à des kilomètres.

## Neige et limites

| Archive SLF OSHD | État réellement atteint |
|---|---|
| WY2024 | Complète : 645 601 691 octets |
| WY2025 | Complète : 579 028 796 octets |
| WY2023 | Partielle : 84 934 656 / 569 361 906 octets, conservée pour reprise |

Les deux archives complètes ont passé taille, MD5 fournisseur et SHA256. Leurs **24 fichiers mensuels** sont vérifiés et leurs métadonnées/coordonnées inspectées. Aucun champ neige n’est encore agrégé par station, et aucun raccordement SPASS–OSHD n’est appliqué. Source et licence : [dépôt officiel SLF OSHD](https://zenodo.org/records/17313889), CC-BY4.0.

La mise à jour du contrôle des grilles conserve leur différence : OSHD 250 m, SPASS 1 000 m, orientations et ordre des axes différents. L’unité neige absente des métadonnées originales SPASS reste `UNKNOWN`, distincte de l’interprétation physique antérieure. WY2023 est nécessaire pour une comparaison temporelle avec SPASS ; les deux années récentes seules ne la permettent pas. Pas de substitution automatique ni de moyenne inventée.

## Reprise

Les collecteurs sont arrêtés. Les originaux et téléchargements partiels restent conservés. Ne pas refaire les 72 pages ni les deux ZIP complets. Les scripts de contrôle sont relançables sur cache ; les sources et champs nouveaux sont consignés dans les registres du projet.

Suite : vérifier individuellement les sept objets et les correspondances domaine–pistes, traiter les relations/topologies sans inventer de géométrie, compléter WY2023 puis proposer le protocole spatial de comparaison des modèles. Le seuil définissant un terrain « plat », une éventuelle réparation géométrique et tout raccordement/calibration neige exigent encore validation. **Aucun clustering ni nouvel effet DiD lancé.**

Validation : **260 tests passent**, avec un avertissement pandas déjà présent. Les 373 contrôles SHA des fichiers antérieurs passent. Les registres contiennent 467 sources et 7 458 champs uniques ; les 7 422 anciennes définitions sont inchangées. État final et sauvegarde Git consignés dans `PROJECT_STATE.md` et `logs/research_journal.md`.
