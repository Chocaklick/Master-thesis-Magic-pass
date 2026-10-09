# Vérification des tracés et option des données officielles

9 octobre 2026 — Stage50, suite du [bilan précédent](102_AXES_SURFACES_PISTES_ET_REPRISE_NEIGE_FR.md). Les 71 groupes et 185 territoires restent conservés. Aucun rattachement OSM–groupe ni nouveau calcul de profil n’est accepté à ce stade.

## Les sept tracés : contrôle individuel

Les attributs, identifiants, versions, coordonnées et relations disponibles de chaque objet ont été examinés dans l’archive originale. Trois pages de documentation OSM sont archivées, vérifiées par SHA256 et distinctes des données ODbL. Le texte du wiki indique une licence CC-BY-SA2.0.

| Identifiant OSM | Résultat de la vérification | Suite |
|---|---|---|
| 551342308, 560349845, 560499042, 562826738 | Quatre contours fermés avec `landuse=piste`. La convention OSM étaye une interprétation en surfaces, malgré l’absence de `area=yes`. Leur topologie polygonale est valide sans réparation. | Candidats surfaces documentés ; rattachement au domaine et validité historique encore à vérifier |
| 670568310 | `man_made=bridge` décrit le contour du pont. Cela ne prouve pas que toute l’emprise de la structure est une surface de piste. | Étendue de piste encore incertaine ; ne pas fabriquer d’axe |
| 551031993 | Objet fermé d’école de ski ; nature exacte du contour non établie | Chercher une preuve complémentaire |
| 670568333 | Objet fermé marqué comme tunnel ; interprétation ligne/surface non établie | Chercher une preuve complémentaire |

Les sept objets restent présents. **Aucune longueur ou superficie n’est calculée**, et aucun groupe n’est supprimé. Le diagnostic Stage49 reste intact ; cette revue complémentaire ne réécrit pas ses catégories originales. [Revue individuelle CSV](../data_processed/winter_profile_closed_piste_review_stage50.csv), [preuves et empreintes](piste_closed_semantics_stage50_summary.json).

Sources : [conventions des surfaces OSM](https://wiki.openstreetmap.org/wiki/Area), [pistes de descente](https://wiki.openstreetmap.org/wiki/Tag:piste:type=downhill), [contours des ponts](https://wiki.openstreetmap.org/wiki/Tag:man_made=bridge). Ce sont des conventions de représentation, pas une certification de périmètre réel ou préentrée.

## Rattachement des groupes : option 1 validée

Les pages officielles Magic Pass et les sites OSM renvoient au même domaine web pour cinq cas : Mayens de Conthey, Saas-Fee, Belalp, Linden, Meiringen–Hasliberg. Ces liens constituent des indices de revue, pas une acceptation automatique des pistes du site. Aucun rattachement ne repose uniquement sur un nom ou sur une distance.

Après clarification de l’option stricte, le chercheur a répondu « tu peux faire l'option 1 ». La vérification individuelle identité/composantes + opérateur officiel + cohérence géographique est autorisée, sans acceptation automatique par nom ou distance. Décision enregistrée dans `config/piste_assignment_protocol_decisions_stage51.json`. Les cinq cas restent des candidats jusqu’à examen effectif des preuves ; toutes les unités non résolues sont conservées. Suite : rapport104.

## Ce que demanderait l’option stricte

Il s’agirait d’obtenir **une référence officielle géoréférencée pour chaque groupe** afin de contrôler les correspondances avec les pistes OSM. Cela n’oblige pas, à lui seul, à remplacer tous les tracés OSM par de nouvelles géométries officielles. Des fichiers vectoriels officiels seraient l’option la plus directe ; une carte officielle géoréférencée adéquate pourrait aussi servir de référence de contrôle.

1. **Inventorier les données disponibles**, groupe par groupe : fichiers SIG de l’exploitant, couches cantonales, cartes interactives dont les tracés sont accessibles et réutilisables. Formats possibles : GeoPackage, GeoJSON, Shapefile ou GPX pour des axes. Le format seul ne garantit pas la qualité ni l’origine officielle.
2. **Contrôler la source et le contenu** : coordonnées et système de référence, axes de pistes versus surfaces, descente alpine versus ski de fond/randonnée, domaine et composantes effectivement couverts. Une couche de remontées ou un périmètre de planification ne remplace pas les pistes réelles.
3. **Vérifier date, droits et historique** : millésime, changements connus avant/après entrée, conditions de téléchargement et de réutilisation. Un fichier actuel reste un proxy historique s’il n’existe pas d’archive préentrée vérifiée.
4. **Si nécessaire, demander les fichiers aux exploitants**. Aucune demande externe n’a été envoyée. Pour un PDF cartographique à l’échelle, un géoréférencement puis une numérisation pourraient être proposés avec contrôle de précision et validation préalable. Un panorama déformé ne permet pas automatiquement un tracé métrique fiable.
5. **Raccorder et contrôler** : conserver les groupes directement reliés déjà validés, distinguer axes/surfaces, vérifier les recouvrements et publier les lacunes. Sans fichier adéquat, le groupe reste conservé avec variables indisponibles ; ne pas remplacer implicitement l’absence par zéro ou retirer la commune.

Il n’y a pas encore de couverture officielle indépendante complète vérifiée pour les 71 groupes. Les pistes affichées dans l’app swisstopo sont issues d’OSM, donc leur seul affichage n’est pas une confirmation indépendante ([conditions officielles](https://www.swisstopo.admin.ch/fr/conditions-utilisation-app-swisstopo)). Des résultats de catalogue trouvés pour le ski de fond, le VTT ou les domaines planifiés n’ont pas été substitués aux pistes de descente. Leur présence ne prouve pas l’absence d’un fichier adapté ailleurs.

L’option stricte dépend donc de la disponibilité et des autorisations de chaque fournisseur. Une possibilité à discuter serait d’utiliser les géodonnées officielles adéquates lorsqu’elles existent, et des correspondances OSM documentées ailleurs. Ce compromis n’est pas appliqué sans validation.

## Neige et reprise

La collecte WY2023 est désormais **complète : 569 361 906 octets**, taille, MD5 fournisseur et SHA256 vérifiés. Les 84 934 656 octets existants ont été réutilisés et les archives WY2024/WY2025 n’ont pas été téléchargées de nouveau. Les trois ZIP sont disponibles pour l’audit ; cela ne constitue pas encore une comparaison numérique ou un raccordement SPASS–OSHD. Les écritures des registres et du journal commun ont été effectuées après arrêt du collecteur pour éviter les conflits. État des contrôles NetCDF, tests et sauvegarde consignés dans `PROJECT_STATE.md` et `logs/research_journal.md`.
