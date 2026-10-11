# Géométries manquantes : bilan du premier lot vérifié

11 octobre 2026 — étape 78. Priorité : compléter les dossiers avant le clustering.

## Résultat

**20 des 30 dossiers ont une nouvelle correspondance documentée avec des tracés OSM originaux.** Le nombre de groupes disposant d'au moins un objet associé passe de **40 à 60 sur 70**. Les **10 autres groupes restent présents**, avec leur problème précis signalé. Il ne s'agit pas de 20 nouvelles stations, de nouvelles communes ou de 20 nouveaux profils neige calculés.

La principale lacune était le rattachement : beaucoup de pistes existaient déjà dans l'extraction nationale, mais hors d'une relation OSM de domaine skiable, ou dans une relation ne couvrant qu'une composante du groupe. Une relation vide/incomplète n'établit donc pas l'absence de pistes.

| Groupe nouvellement rattaché | Objets OSM associés |
|---|---:|
| Grenchenberg | 2 |
| Aeschiallmend | 14 |
| Anzère | 168 |
| Arolla | 32 |
| Beatenberg-Hohwald / Niederhorn | 17, dont 2 surfaces |
| Evolène | 41 |
| Faltschen | 7 |
| Gantrisch-Gurnigel / Gurnigelbad | 10 |
| Homberg | 5 |
| Kiental | 10 |
| La Forclaz | 21 |
| La Robella | 10 |
| Les Marécottes | 19 |
| Mörlialp | 6 |
| Ovronnaz | 45 |
| Rochers-de-Naye / Haut-de-Caux / Dent-de-Jaman | 9 |
| Sainte-Croix–Les Rasses | 16 |
| Saint-Cergue, secteur du Vallon documenté | 4 |
| Tramelan | 9 |
| Vallée de Joux, trois composantes | 24 |

**Un objet OSM n'est pas une piste indépendante** : il peut s'agir d'un fragment, d'une variante ou d'une surface. Les 469 nouveaux objets sont conservés séparément des 854 anciennes lignes, soit 1 323 lignes dans la nouvelle table de membres. Ce tableau n'est ni un classement de taille ni une mesure de couverture réelle du domaine.

## Méthode et preuves

Le protocole déjà validé est appliqué : identité de la station/composantes, preuve officielle de l'opérateur ou de l'office touristique, cohérence géographique des pistes et remontées. Les identifiants précis sont inscrits dans `config/piste_remaining_assignments_stage78.json`, avec les sources et une justification individuelle. Aucune attribution automatique par nom, proximité ou ancien cluster.

L'inventaire à 10 km et les cartes à 6 km sont uniquement des aides de recherche/affichage. Ces distances ne définissent pas le domaine et ne servent pas de règle d'exclusion. Les remontées du GPKG original sont un contexte visuel séparé, avec leurs fids/UUID et une date/provenance amont inconnues ; elles ne deviennent pas des objets OSM ni un nouveau clustering.

Les originaux OSM du 9 octobre sont réutilisés, sans nouvelle extraction ou modification. Les plans officiels de [Grenchenberg](https://jurasonnenseite.ch/assets/Skilift/pistenplan/Skilift_Pistenplan-Grenchenberge_Tafel_3_2025.pdf), [Homberg](https://skilift-homberg.ch/ueber-den-skilift/), [Tramelan](https://www.teleski-tramelan.ch/images/plan-pistes.png) et [La Robella](https://www.robella.ch/pdf/robella-plan-station-hiver.pdf) sont archivés et examinés visuellement. Des preuves officielles complémentaires documentent notamment [Anzère](https://www.anzere.ch/fr/remontees-mecaniques/domaine-skiable/), [Mörlialp](https://www.obwalden-tourismus.ch/de/bergbahnen/skilifte-moerlialp/), [Les Marécottes](https://www.valais.ch/fr/explorer/activites/ski-snowboard/domaines-skiables/les-marecottes) et [l'accès ski MOB](https://support.mob.ch/hc/fr-ch/articles/15547210908061-Validit%C3%A9-du-Magic-Pass-sur-la-ligne-Montreux-Les-Rochers-de-Naye).

Collecte : **12 nouvelles archives réussies, 2 refus robots et 1 échec TLS**, tous documentés ; les refus ne sont pas contournés. Six erreurs initiales locales de socket ont précédé les vrais essais et restent enregistrées, sans être prises pour des absences chez le fournisseur. Le moteur Tavily était indisponible : recherche web de remplacement documentée, aucun extrait de moteur utilisé seul comme preuve d'acceptation. Les 15 tentatives de sources, 3 sources dérivées/de découverte et les 90 champs sont enregistrés dans les registres du projet ; URL, date, original et SHA sont conservés lorsqu'ils existent réellement.

Les guides de travail sur tableaux et plans ont conduit à garder des CSV simples, à vérifier les plans rendus et à séparer clairement correspondance, diagnostic et variable analytique.

## Limites et dossiers encore ouverts

**La correspondance actuelle ne certifie ni l'inventaire exhaustif, ni l'exploitation de chaque piste, ni sa géométrie avant l'entrée.** Les nouveaux objets ne sont pas encore autorisés comme mesures finales. Les deux surfaces de Hohwald ne deviennent pas des axes. Arolla et Evolène comportent **19 objets marqués `abandoned=yes`** ; Arolla comporte aussi un objet nommé « ancienne piste ». Ils restent associés à leur station et signalés, sans suppression automatique. Il faudra vérifier leur statut et les changements avant les profils.

Le plan de Robella distingue l'itinéraire vers le Chasseron des pistes balisées : l'objet candidat correspondant n'est pas assimilé aux pistes de ski. À Sainte-Croix, le rattachement des axes du réseau Ski Vaud résout la relation OSM vide ; les pistes du club de Mont-des-Cerfs restent à clarifier séparément. À Saint-Cergue, le Vallon est explicitement documenté pour Magic ; Basse-Ruche/Trélasse ne sont pas ajoutées sur la seule mention d'une offre touristique voisine. Ces réserves sont conservées, pas cachées derrière une affirmation de couverture complète.

| Dossiers sans correspondance finalisée | Suite précise |
|---|---|
| Grimentz–Zinal, Bergbahnen Gstaad, Leysin–Les Mosses–La Lécherette, Villars–Gryon–Les Diablerets | Les tracés existent. Établir les listes de membres de chaque composante à partir des plans opérateurs ; ne pas confondre les domaines voisins, notamment Glacier 3000 et Wasserngrat. |
| Leukerbad | Distinguer Torrent/Gemmi/Erli et leur inclusion exacte dans l'offre, puis rattacher les axes ; la relation Gemmi seule ne décrit pas le domaine. |
| Wilerallmi et Schwanden | Le plan officiel montre une liaison directe, le rapport annuel une entrée commune en 2024/25. Le PDF porte création 25/10/2019 et modification 14/11/2019 : corroboration antérieure, pas preuve de publication à cette date. Un groupe commun avec cette réserve a été soumis à validation ; aucune fusion appliquée. |
| La Dôle | Choix franco-suisse soumis au chercheur : portions suisses seulement ou tracés entiers du secteur. Ne pas appliquer de découpage avant validation. |
| Château-d'Œx–La Braye | Des tracés existent mais sont marqués abandonnés. Vérifier histoire d'exploitation et périmètre historique ; ne pas remplacer par une station voisine. |
| Riffenmatt | Pas de piste proche retrouvée dans l'archive actuelle, site opérateur ancien devenu une page générique. Rechercher un vrai plan/une autre source géoréférencée ; ne pas fabriquer un axe à partir de la remontée. |

## Conservation et reprise

Les **70 groupes, communes, dates d'entrée et résultats DiD restent inchangés**. Les 19 anciennes colonnes de correspondance et les 854 lignes membres sont recopiées à l'identique dans de nouveaux fichiers. Le drapeau ancien `current_site_correspondence_verified` concerne la relation OSM : lorsqu'il reste faux, la nouvelle colonne `stage78_geometry_correspondence_verified` peut être vraie grâce aux identifiants revus hors relation. Ce n'est pas une contradiction.

Les anciens résultats terrain/neige restent **40 groupes terrain et 34 moyennes SPASS complètes** : ils n'ont pas été relancés. Aucun clustering, nouvelle classe, imputation, exclusion, raccordement neige ou DiD n'est effectué.

Sorties : `piste_remaining_review_stage78.csv` (30 dossiers), `winter_profile_piste_assignment_stage78.csv` (70 groupes), `winter_profile_piste_members_stage78.csv` (objets et drapeaux), `winter_profile_piste_groups_stage78.csv` (couverture/QA). Producteur et manifeste : `build_remaining_piste_assignments_stage78.py` / `remaining_piste_assignments_stage78_summary.json`. Reprise sûre : compléter les 10 dossiers et la QA des nouvelles géométries dans une **nouvelle version**, puis étendre les portions uniques, le relief 2 m et les cellules SPASS selon les méthodes déjà validées. Ne pas modifier les producteurs/caches ou profils Stage67/77 et ne pas commencer le clustering sur un sous-échantillon non validé.

Contrôles terminés : **35 tests combinés réussis**, dont 28 du nouveau rattachement. L'audit SHA par blocs confirme **2 000 fichiers vérifiés, dont 1 939 historiques inchangés**, et les anciens préfixes exacts des registres. Registres actuels : 1 247 sources, 8 456 champs et 2 077 événements. Tous les collecteurs/calculs/tests sont terminés ; aucun job actif. Le manifeste `preservation_stage78_summary.json`, le journal et l'état du projet donnent la reprise précise.
