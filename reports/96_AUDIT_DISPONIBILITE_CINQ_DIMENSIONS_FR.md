# Disponibilité des cinq dimensions de profils

9 octobre 2026. Audit des cinq dimensions validé par « très bien applique ta proposition ». **71 groupes conservés**, anciens fichiers et classes intacts. Aucun clustering ajusté, aucune exclusion ou nouvelle estimation. Ce bilan applique l’audit de disponibilité demandé ; il ne prétend pas avoir déjà calculé une orientation ou un enneigement représentatif du domaine.

## Résultat

| Dimension | Ce qui existe | Ce qui reste à résoudre |
|---|---|---|
| Taille | 66 groupes avec pistes + remontées complètes | Dates historiques inconnues ; un groupe incomplet et quatre sans fiche |
| Altitude | Sommet disponible pour 67 groupes | Ni altitude basse ni distribution altitudinale vérifiée des pistes ; le sommet n’est pas la moyenne skiée |
| Orientation | Pas de géométrie de pistes validée dans les entrées auditées | Obtenir les tracés ; ne pas assimiler direction d’une remontée et exposition de la pente |
| Neige | 67 groupes ont un proxy IMIS et cinq hivers préentrée avec ≥80 % de jours valides | Localisation, sélection historique et agrégation restent non validées ; 11 proxys de faible qualité |
| Accès aux villes | **426 couples déjà disponibles : 6 villes × 71 groupes** | Valider les villes et le résumé d’accès ; mesure actuelle arrêt communal → arrêt de station |

Les 67 fiches uniques se rattachent exactement aux groupes existants. Château-d’Oex–La Braye, Mayens de Conthey, Grenchenberg et Wilerallmi restent sans fiche de structure/neige jointe ; ils ne sont pas exclus. Leurs références routières existent bien. **Aucun groupe n’est encore certifié prêt pour les cinq dimensions historiques complètes.** Cela décrit les preuves disponibles, pas l’impossibilité de récolter les manques.

## Neige : vérification réellement préentrée

Relecture du fichier quotidien original IMIS, empreinte vérifiée : 1 212 878 lignes, du 1 octobre 1992 au 13 septembre 2026. Recompter uniquement décembre–avril, avant l’entrée au pass de base, et non avant son seul hiver d’entrée. Une neige nulle observée est valide ; valeurs négatives/non numériques et jours absents ne deviennent pas des observations. Aucun enneigement moyen n’est encore publié ou imputé.

Deux fenêtres candidates de cinq hivers ont été comparées **pour la couverture seulement** :

| Fenêtre | Groupes avec les 5 hivers à ≥80 % | Groupes avec tous les jours observés |
|---|---:|---:|
| Commune à tous : 2012/13–2016/17 | 67 | 47 |
| Cinq hivers propres à chaque entrée | 67 | 60 |

Le seuil de 80 % reprend l’ancien diagnostic de couverture ; il n’est pas un nouveau filtre de sélection. La fenêtre commune facilite la comparaison climatique entre profils ; les fenêtres propres à l’entrée sont plus contemporaines, mais mélangent période et cohorte. Ni l’une ni l’autre n’est choisie ici. Une moyenne par hiver puis entre hivers, le traitement de couverture et les pondérations géographiques seront explicités avant calcul.

Qualité géographique existante : 38 proxys de qualité haute, 18 modérée, 11 faible. Distance médiane 8,23 km, maximum 65,69 km ; certains écarts d’altitude dépassent 1 000 m. Les faibles comprennent Balmberg, Gstaad, La Dôle, La Robella, Crêt-du-Puy, Bugnenets-Savagnières, Prés-d’Orvin, Les Rasses, Saint-Cergue, Tramelan et Vallée de Joux. Leur présence de données ne démontre pas une neige représentative des pistes. Le choix IMIS existant utilisait la couverture 2013–2025, parfois postérieure à l’entrée : pas de certification historique automatique du raccordement.

La grille SPASS/OSHD de 1 km est déjà récoltée ; l’ancienne extraction porte sur 15 composantes exactement retrouvées ici, pas les 71 groupes. Je propose de l’étendre après validation du périmètre et de la référence neige, en gardant IMIS comme comparaison. La grille partage des données/références SLF avec les mesures : ce n’est pas une validation indépendante, ni de la neige préparée sur piste ou des jours d’ouverture.

## Voiture : réutilisation plutôt que nouvelle collecte

Les six villes du produit NPVM sont déjà dans le panel et la matrice routière finale : **Zurich HB, Berne, Bâle SBB, Lugano, Lausanne et Genève**, identifiants communaux et d’arrêts dans le manifeste. Chacune dispose d’un temps vers les 71 groupes, y compris ceux sans fiche : **0 nouvelle requête nécessaire** pour ce périmètre.

Cette alternative reprend la référence déjà validée : directions calculées séparément puis moyennées, accès du groupe selon la référence existante, réseau statique actuel, limites hivernales/légales et raccordements conservés. Pas de centre administratif, stationnement réel ou circulation inventés. Le minimum parmi les six villes, leur présentation séparée ou une pondération par population restent des choix non appliqués. Aucun nouveau seuil ; le marché urbain n’est pas le seuil communal d’exposition de 30 minutes.

Le contexte NPVM2025 est conservé comme comparaison : 67 groupes avec données, dont 34 exactement rattachés à une zone et 33 avec proxy zonal. Toutes ses dates modèles postdatent l’entrée : il ne devient pas une mesure historique sans hypothèse explicite. La matrice routière actuelle reste elle aussi un proxy actuel fixé historiquement, pas un réseau reconstruit pour chaque année.

## Décisions à valider ensuite

1. **Neige** : grille SPASS comme référence candidate, IMIS en comparaison ; fenêtre commune 2012/13–2016/17 ou cinq hivers propres à l’entrée ? Pas de moyenne de points urbains ou de parkings pour représenter une piste.
2. **Altitude/orientation** : rechercher les tracés de pistes et préciser si une géométrie actuelle peut servir de proxy, avec changements documentés et réserve historique, ou si l’on exige un périmètre historique. Le relief et le tracé du domaine sont deux informations distinctes.
3. **Accès urbain** : retenir les six villes déjà couvertes et, éventuellement, le temps minimal parmi elles comme indicateur principal, sans en faire une observation des origines réelles des visiteurs ?

Les variables continues restent au principal ; les paramètres numériques et classes finales seront proposés après ces choix. Pas d’affectation arbitraire de lits communaux à une station, de profil moyen du portefeuille ou de regroupement selon les résultats.

## Fichiers, sources et reprise

- [Bilan par groupe](../data_processed/winter_profile_five_dimension_groups.csv) : les 71 groupes et leurs manques.
- [Composantes et proxys conservés](../data_processed/winter_profile_five_dimension_components.csv) : 67 fiches et leurs valeurs originales qualifiées.
- [Couverture neige préentrée](../data_processed/winter_profile_preentry_snow_coverage.csv) : 1 922 lignes groupe–fiche–hiver, pas des unités statistiques indépendantes.

Source dérivée `DERIVED_FIVE_DIMENSION_AVAILABILITY_2026_10_09` et 70 champs de tables enregistrés. Parents : répertoire existant, `SLF_IMIS_DAILY_SNOW`, `SLF_IMIS_STATIONS`, `ARE_NPVM_TRAVEL_TIME_2025`, grille SPASS et référence routière finale. Aucun téléchargement, raster ou trajet ajouté. Le GeoPackage local contient une couche de transport, non un périmètre de pistes certifié ; pas de nouvel usage des clusters de remontées.

Reprise : `.venv/Scripts/python.exe src/descriptive/audit_five_dimension_profile_availability.py`. Empreintes dans `five_dimension_profile_availability_summary.json`, décisions dans `config/winter_profile_five_dimension_audit.json`. Reprise identique sans réécriture, requête, clustering ou estimation. La révision explicite de cette seule étape a ajouté l’inventaire des trajets urbains déjà récoltés ; les anciennes étapes restent protégées. Vérification finale et commit consignés au journal.
