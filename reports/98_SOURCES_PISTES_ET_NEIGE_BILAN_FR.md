# Pistes et neige : bilan des sources et prochaine décision

9 octobre 2026. Les **71 groupes de stations** restent inchangés. Aucun nouveau cluster, effet DiD, changement de commune ou remplacement de valeur de neige.

## 1. Tracés actuels : collecte réussie, rattachement à vérifier

Une requête publique OpenStreetMap a été archivée avec les géométries, identifiants `type + id`, versions, dates de modification et empreinte SHA256. Instantané : 9 octobre 2026 à 16:21:05 UTC.

| Inventaire national collecté | Nombre |
|---|---:|
| Objets au total | 9 744 |
| Tracés `way` de descente | 9 196 |
| Relations de descente | 310 |
| Relations de sites de pistes, éventuellement mixtes | 238 |

Ce n’est **pas un nombre de pistes distinctes**, ni une preuve de couverture des 71 groupes. Les relations peuvent contenir des tracés déjà comptés ; 690 tracés sont fermés et peuvent représenter des surfaces. Tous les tracés ont au moins deux points géométriques, mais leur qualité et exhaustivité restent à examiner. La sélection suisse peut conserver des géométries transfrontalières : aucune découpe ou affectation automatique n’a été faite.

Le rattachement devra utiliser les identifiants et relations OSM, les accès et composantes existants, puis les plans et documents des exploitants. Les cas ambigus resteront signalés. On ne remplace ni les groupes connectés validés ni le clustering des remontées par les groupes d’un fournisseur externe. Une date d’édition OSM n’est pas une date de construction ; les tracés actuels restent des **proxys à validité historique incertaine**, conformément à ta décision.

Les trois documents historiques déjà examinés — Leysin 2017, TVGD/Ormont-Dessus 2017 et La Braye 2018 — ne prouvent pas une géométrie complète et inchangée des pistes. Leur revue reste dans `config/winter_profile_historical_source_review.json`. Ce nouveau CSV ne lie que les références déjà présentes dans les parents exacts des groupes : un groupe a ce lien, ce qui ne signifie pas que les autres n'ont aucun document. L’audit historique exhaustif reste à faire.

Sources : [définition OSM des pistes de descente](https://wiki.openstreetmap.org/wiki/Tag:piste:type=downhill) et [politique du service Overpass](https://dev.overpass-api.de/overpass-doc/en/preface/commons.html). Attribution des données : © contributeurs OpenStreetMap, licence ODbL. Les pistes de l’application swisstopo viennent aussi d’OSM : ce n’est pas une validation indépendante ([conditions officielles](https://www.swisstopo.admin.ch/fr/conditions-utilisation-app-swisstopo)). OpenSkiData a été consulté, mais ses accès directs testés ont renvoyé HTTP403 ; aucun contournement ni téléchargement de ses fichiers.

## 2. Neige : complément possible, pas extension identique

Le catalogue [SPASS](https://www.envidat.ch/metadata/spass---new-gridded-snow-datasets-for-switzerland) consulté ne fournit pas d’extension identique vérifiée après le 31 août 2023. Une autre série SLF existe : [OSHD 250 m, années hydrologiques 2016–2025](https://zenodo.org/records/17313889), soit septembre 2015–août 2025. Elle utilise un modèle physique FSM2OSHD avec assimilation d’observations ; SPASS utilise une autre chaîne. La neige modélisée n’est pas une mesure d’enneigement artificiel sur pistes. Les comparaisons avec IMIS ne sont pas entièrement indépendantes puisque des observations alimentent les modèles ([article méthodologique](https://tc.copernicus.org/articles/20/3387/2026/)).

| Compatibilité avec les cinq hivers propres à chaque entrée | Bilan |
|---|---:|
| Hivers demandés, 71 groupes × 5 | 355 |
| Hivers absents du calendrier SPASS | 23, dans 14 groupes |
| Parmi ces 23, calendriers couverts par OSHD | 23 |
| Groupes ayant leurs cinq calendriers dans OSHD | 40 sur 71 |
| Autres groupes : 4 / 3 / 2 calendriers dans OSHD | 3 / 6 / 22 groupes |
| Calendriers groupe–hiver présents dans les deux séries | 251 |

Ce sont des **disponibilités calendaires**, pas encore des cellules valides ou des moyennes de neige. OSHD seul ne résout donc pas les cinq hivers de tous les groupes. Raccorder les modèles sans vérifier leurs écarts pourrait créer de fausses différences entre profils et cohortes. Les saisons plus anciennes ne remplacent pas les saisons demandées.

Au terme de l’inventaire initial, aucun nouveau fichier neige n’avait été téléchargé : les archives 2024 et 2025 représentent environ 1,22 Go ensemble. **Vérification suivante après ton accord :** le HTML public archivé contient explicitement `cc-by-4.0`, en plus du copyright. L’apparente ambiguïté venait de l’extraction web incomplète, pas d’une incompatibilité des termes. La collecte utile a ensuite été lancée ; son état est dans `reports/oshd_profile_audit_collection_summary.json`.

## 3. Protocole proposé, en attente de validation

1. **Neige récente** : étudier OSHD comme complément, vérifier les termes et comparer les modèles sur des lieux et dates communs ; présenter ensuite les possibilités de raccordement. Aucun mélange automatiquement accepté, aucune modification des cinq hivers ni exclusion.
2. **Périmètre des profils** : dédoublonner les tracés de pistes vérifiés et pondérer les segments par leur longueur. Calculer altitude et exposition depuis le relief, pas depuis le sens de circulation de la piste. Les surfaces sans axe utilisable et les ambiguïtés seront identifiées avant application.
3. **Moyenne de neige** : moyenne des jours observés par hiver, puis poids égal aux cinq hivers. Publier la couverture ; ne pas remplacer un hiver entièrement absent par zéro ou par une moyenne de quatre hivers. Ce principe n’introduit aucun seuil de couverture ni filtre de groupe. Les détails de résolution, gestion des surfaces et exposition du terrain plat restent à préciser avant extraction.

**Validé pendant cette étape :** audit et collecte utile d’OSHD avant décision de raccordement ; pondération par longueur et cinq hivers de poids égal. Réponses enregistrées dans `config/winter_profile_aggregation_decisions_stage45.json`. Aucun raccordement de modèles n’est validé. Le rattachement des pistes, l’audit des changements et les détails techniques encore ouverts restent nécessaires avant d’utiliser les variables dans une classification. Les nuitées restent communales et leur exposition à plusieurs groupes reste distincte des caractéristiques des stations.

## Fichiers et reprise

- [Bilan par groupe — 71 lignes](../data_processed/winter_profile_terrain_snow_source_feasibility.csv).
- Manifeste : `reports/terrain_snow_source_feasibility_summary.json` ; décisions et sources candidates : `config/winter_profile_terrain_snow_source_review_stage44.json`.
- Collecteur : `.venv/Scripts/python.exe src/data_collection/collect_current_piste_geometry.py` — réutilise l’archive vérifiée, sans nouvelle requête. Un échec ne déclenche pas de relance automatique.
- Audit : `.venv/Scripts/python.exe src/descriptive/audit_terrain_snow_source_feasibility.py` — réutilise les empreintes, sans réécrire ni calculer de profil ou d’effet.

Sources consultées et collection enregistrées dans `metadata/data_sources_master.csv`, 18 champs du bilan dans `metadata/data_dictionary.csv`. Tous les résultats précédents sont conservés et contrôlés par empreintes. Le journal et `PROJECT_STATE.md` indiquent ce qui est terminé et les validations encore attendues.
