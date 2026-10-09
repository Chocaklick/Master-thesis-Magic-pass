# Pistes : dix correspondances supplémentaires

9 octobre 2026 — suite de l’option 1 validée et du [premier lot](104_RATTACHEMENTS_PISTES_OPTION_1_FR.md).

**10 nouveaux rattachements actuels site OSM → groupe vérifiés : 15 sur 71 au total. Les 56 autres restent conservés, sans exclusion.** Les cinq premiers rattachements, les groupes reliés, les 185 territoires communaux, les anciens clusters et les résultats DiD sont inchangés. Il s’agit de l’avancement des données de pistes, pas de dix nouvelles communes analysables.

| Groupe et preuve officielle | Relation OSM | Objets descente / remontées membres connues | Réserve principale |
|---|---:|---:|---|
| [Axalp](https://www.axalp.ch/besucherinfo/pisten-pistenbericht/) | 5634250 | 12 / 4 | Les 7 pistes annoncées et les 12 objets OSM sont des unités différentes |
| [Balmberg](https://www.balmberg.ch/pisten-nachtskifahren) | 9244613 | 5 / 3 | Kähle/Bödeli corroborés ; type et identité de la petite installation encore à clarifier |
| [Bumbach](https://bumbach.ch/) | 9206149 | 5 / 2 | Deux sections principales corroborées ; installations pour enfants pas toutes présentes dans les membres |
| [Charmey](https://www.charmey.ch/activites/ski-snowboard/) | 9363438 | 8 / 4 | TéléCharmey/Banderettes et domaine corroborés ; pas de couverture exhaustive certifiée |
| [Eriz](https://www.snowparkeriz.ch/) | 9205188 | 6 / 2 | Obersohl et Schwändli corroborés ; autres activités séparées des descentes alpines |
| [Habkern](https://www.skilifthabkern.ch/) | 9199977 | 5 / 1 | Sattelegg corroboré ; petites installations officielles non toutes représentées |
| [Jaunpass](https://www.sportbahnen-jaunpass.ch/?lang=fr) | 9356119 | 9 / 2 | Winteregg/Zügwegen corroborés ; signalement OSM de pistes nordiques manquantes conservé |
| [La Berra](https://www.laberra.ch/fr/ouverture-des-installations) | 9363437 | 7 / 2 | Le Brand–La Berra corroboré ; le bulletin automnal ne décrit pas toute l’offre hivernale |
| [Crêt-du-Puy](https://www.cretdupuy.com/) | 9387990 | 6 / 2 | Deux téléskis corroborés ; tapis roulant officiel non supposé présent dans OSM |
| [Bugnenets–Savagnières](http://www.chasseral-snow.ch) | 9387991 | 18 / 4 | Quatre membres corroborés ; l’exploitant liste huit installations, couverture encore incomplète/incertaine |

Ce lot contient **81 objets de descente**, soit **287** avec le premier lot. Ce ne sont ni des pistes distinctes, ni des kilomètres. **Aucune mesure finale de longueur, altitude, orientation ou neige n’est encore calculée.** Le rattachement du site ne valide pas automatiquement chacun de ses objets, son périmètre exhaustif ou son état préentrée.

## Deux cas non résolus dans ce lot

Le lien officiel d’**Heimenschwand** renvoie HTTP404. Celui de **Jaun** présente un certificat TLS incompatible avec son nom d’hôte. Les erreurs sont enregistrées, sans nouvelle tentative ni désactivation de la vérification TLS. Les deux groupes restent présents avec compte de pistes indisponible dans le tableau des rattachements, et leurs identifiants candidats restent dans les preuves. Leur cohérence géographique seule ne suffit pas à les accepter.

## Vérification et traçabilité

Les douze candidats ont été examinés par identité, composantes et carte des géométries originales en LV95. Dix pages d’accueil et quatre sous-pages liées ont été archivées avec date, robots, adresse finale et SHA256. Le lien relatif de La Berra a été résolu avec la balise HTML `base` effectivement présente. Aucun lien ou coordonnée n’a été inventé. Les variations de noms sont documentées par cas, jamais rapprochées automatiquement.

Les remontées et descentes proviennent des deux instantanés OSM déjà récoltés. Identifiants, versions, dates d’édition, composantes et points de référence sont conservés. Aucun rayon, découpage communal, remplacement des points ou regroupement nouveau n’a été appliqué. Les sources actuelles restent des proxies à auditer historiquement, pas des données préentrée certifiées ; les kilomètres publiés sur les sites ne sont pas importés comme profils GIS ou historiques.

[Table cumulée des 71 groupes](../data_processed/winter_profile_piste_assignment_stage52.csv) ; [preuves et empreintes](piste_assignment_stage52_summary.json) ; cartes [lot 1](figures/piste_assignment_geographic_review_stage52_1.png) et [lot 2](figures/piste_assignment_geographic_review_stage52_2.png). Les 16 sources tentées, leurs échecs compris, figurent au registre. Les 19 champs du tableau ont leur définition et leur filiation dans le dictionnaire.

**Contrôles : 270 tests réussis**, un avertissement hérité ; 367 références de fichiers protégés contrôlées, soit 223 fichiers uniques, plus 44 empreintes du nouveau lot. Les 483 anciens enregistrements sources et les 7 499 anciens champs sont inchangés. Registres actuels : 500 sources, 7 518 champs. Aucun collecteur ou test n’est encore actif.

## Reprise

Continuer les 56 groupes non résolus dans un nouveau lot, sans modifier ces deux premiers checkpoints. Chercher des adresses officielles indépendamment étayées pour les liens défaillants, sans contourner les restrictions. Pour les groupes dont la relation OSM ne couvre qu’une composante, conserver le manque plutôt que l’assimiler au groupe entier. Puis vérifier individuellement axes/surfaces, topologie, recouvrements et changements historiques avant les profils. Les nouveaux choix de méthode restent à faire valider.

Reprise sans réseau : `.venv/Scripts/python.exe src/descriptive/verify_piste_assignments_stage52.py`. Les archives neige précédemment complétées restent disponibles ; aucune nouvelle extraction ou fusion de modèles n’a été faite pendant ce lot. État détaillé et journal actualisés.
