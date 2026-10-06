# Référence routière — préparation et décisions restantes

6 octobre 2026. La voiture devient la référence approuvée ; les TP corrigés restent une comparaison. Aucun nouveau seuil ni remplacement des expositions/estimations n'est décidé.

## Ce qui est prêt

L'inventaire conserve **185 territoires communaux**, issus de **186 historiques sources** (les deux identifiants de Moutier restent raccordés selon la décision déjà validée), et **75 points d'accès dans 71 groupes de stations inchangés**. Cela représente **13 875 couples commune–point d'accès**, soit 27 750 sens de trajet potentiels. Ce sont des besoins de calcul, **pas des trajets obtenus** : aucun temps routier n'est encore calculé.

- [Origines communales à documenter](accessibility_road_origin_review.csv) : identifiants territoriaux et sources, noms originaux, anciens arrêts TP et champs de preuve/coordonnées routières.
- [Arrivées aux stations à documenter](accessibility_road_station_arrival_review.csv) : identifiants d'accès conservés, coordonnées de référence anciennes, preuves du parking/dépose, marche finale et accès hivernal à compléter.

Les coordonnées anciennes sont conservées pour contrôle, sans être renommées « départ des remontées ». Un point de village, de sommet ou un arrêt TP ne prouve pas un accès automobile. Un champ vide signifie **non documenté**, pas zéro minute ni commune exclue.

Premières preuves, choisies pour contrôler deux problèmes déjà identifiés et non pour limiter l'analyse :

- **Moutier** : [adresse municipale officielle](https://moutier.ch/nous-contacter/) rue de l'Hôtel-de-Ville 1, 2740 Moutier ; réponse geo.admin.ch archivée avec 11 candidats. Un seul correspond exactement au numéro, au NPA et au BFS 6831 (`featureId=1376503_0`) : latitude 47.27961349487305, longitude 7.370380401611328. Les variantes 10, 10a, 11, etc. ne sont pas sélectionnées. **1 origine documentée sur 185** ; pas encore de temps routier.
- **Leukerbad/Torrent** : [source officielle d'accessibilité](https://leukerbad.ch/en/barrier-free-travelling) : dépose au guichet autorisée, stationnement à cet endroit interdit, garage distinct et escaliers vers la télécabine. L'entrée routière exacte, la disponibilité hivernale et les minutes de marche restent à vérifier. **0 arrivée entièrement géocodée sur 75** ; preuve partielle conservée, pas de valeur inventée.

Les trois réponses originales de ces contrôles sont archivées avec empreintes SHA-256. Les 184 autres origines et les 74 autres points d'accès restent dans l'inventaire, à documenter ; le contrôle de Leukerbad reste lui aussi incomplet.

## Définition géographique validée

Le chercheur a validé **centre administratif principal de la commune (mairie, coordonnées sourcées) → parking ou point de dépose desservant le départ réel des remontées**. La marche finale sera documentée séparément. Les coordonnées doivent être recueillies et prouvées pour chaque point, sans généraliser le premier contrôle de Moutier.

Les anciens arrêts TP restent conservés. Leurs temps ne seront pas comparés comme du porte-à-porte aux temps routiers si les extrémités diffèrent : une comparaison directe des modes exige les mêmes points géographiques et des liaisons piétonnes documentées. Les groupes existants ne sont pas reconstruits.

## Circulation : référence statique validée

La référence validée est un itinéraire automobile rapide **modélisé sans embouteillages**, avec calcul indépendant des deux sens puis moyenne. Les restrictions hivernales doivent être examinées ; un cas non vérifié reste signalé. Aucun forfait neige, recherche de parking, marche ou effet horaire ne sera inventé.

La première réponse affirmative a été retirée explicitement, car envoyée par erreur. La question a été reposée et **la nouvelle réponse valide la référence statique, avec limites hivernales explicites**. L'alternative horaire/avec trafic n'est pas retenue pour cette première référence. Avec un graphe statique, matin/soir et mercredi/samedi ne créent pas artificiellement quatre temps distincts.

## Source de routage choisie après délégation

Le chercheur a demandé « fait celui qui est le plus simple ». **openrouteservice est retenu**, car il évite l'installation d'un environnement Linux/Docker et d'un moteur local. La présence d'une clé a été contrôlée sans afficher de secret : ni `ORS_API_KEY` ni `OPENROUTESERVICE_API_KEY` n'est définie dans l'environnement inspecté. Aucun compte créé, aucun frais engagé, aucune requête de matrice routière lancée.

| Possibilité | Intérêt | Limite et situation actuelle |
|---|---|---|
| OSRM local, réseau OSM daté et profil automobile archivés | Réseau/version fixes, calcul reproductible dans les deux sens. | Moteur local non disponible dans le PATH inspecté ; Docker non détecté et WSL ne fournit pas de distribution utilisable lors du contrôle. Installation et ressources à examiner, aucune installation lancée. |
| openrouteservice hébergé | Matrices automobile, calcul par lots et archivage des réponses. | API authentifiée ; disponibilité d'une clé et quota réel du compte à établir, sans créer de compte ni engager de frais. Le réseau du fournisseur n'est pas figé par nous. |
| Démonstration publique OSRM/FOSSGIS | Contrôle ponctuel possible sous les conditions du service. | L'opérateur interdit le scraping/usage intensif : aucune collecte nationale lancée sur ce service. Le graphe évolue ; sa version n'est pas celle de toutes les pages de documentation OSRM. |

La [documentation OSRM Route/Table](https://project-osrm.org/docs/v26.6.1/http) définit les durées directionnelles, les valeurs `null` lorsqu'aucun trajet n'est trouvé et l'option `fallback_speed`, qui inventerait un temps à partir d'une distance : cette option ne devra pas servir à remplir les manques. Les durées sont des résultats du modèle/profil, pas des déplacements observés.

Les limites [openrouteservice Matrix](https://openrouteservice.org/restrictions/) sont de 3 500 cellules par requête standard, avec des limites réduites pour certains arguments ; elles ne sont pas un quota journalier garanti. Sa [documentation Matrix](https://openrouteservice.org/dev/) indique une authentification et un résultat nul en cas de valeur indéterminable. La [politique OSRM](https://github.com/Project-OSRM/osrm-backend/wiki/Api-usage-policy) renvoie aux conditions actuelles de l'opérateur ; son [extrait public FOSSGIS](https://routing.openstreetmap.de/about.html) fixe notamment au plus une requête/seconde et interdit les usages intensifs. La page allemande complète a renvoyé un refus Anubis, non contourné.

Pour un calcul local, un [extrait OSM daté de Geofabrik](https://download.geofabrik.de/europe/switzerland.html) est une source possible, pas encore téléchargée. Un réseau découpé aux seules frontières suisses pourrait manquer des trajets passant à l'étranger entre deux points suisses : il faudra contrôler cette couverture, sans supprimer ces communes.

Les données routières ARE/NPVM déjà présentes fournissent des temps vers des centres/agglomérations, **pas** ces couples commune–remontée ([rapport 22](22_TRANSPORT_ACCESSIBILITY_CONTEXT.md)). Les distances aux axes ASTRA sont des distances géométriques, pas des durées automobiles ([rapport 30](30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md)). Elles ne sont pas converties artificiellement en minutes.

## Reprise et garanties

Préparation reproductible : `.venv/Scripts/python.exe src/data_processing/prepare_accessibility_road_reference.py`. Configuration : `config/accessibility_road_reference_method.json` ; inventaire des sources techniques : `config/accessibility_road_documentation_sources.json` ; manifeste des entrées/sorties et empreintes protégées : `reports/accessibility_road_reference_preparation_summary.json`. Sources et champs sont enregistrés dans les deux tables de métadonnées. Documentation technique consultée en ligne, sans prétendre à un original local archivé ni à un moteur déjà déployé.

Plan opérationnel : `.venv/Scripts/python.exe src/data_processing/plan_accessibility_road_matrix.py`, paramètres dans `config/accessibility_road_routing.json`, résultat dans `reports/accessibility_road_matrix_plan.json`. Pour l'univers complet, les blocs de 25 × 25 prévoient **48 requêtes directionnelles**, au plus 625 cellules chacune, sans imposer un nouveau filtre analytique. **0 lot prêt** : une seule origine documentée et aucune arrivée géocodée à ce stade. Le plan n'appelle aucune API ; le collecteur routier reste à implémenter. Les requêtes futures devront conserver réponses originales, dates, paramètres, version/graphe, distances de raccordement au réseau et contrôles d'intégrité, sans journaliser la clé. Les limites réelles du compte doivent être vérifiées avant exécution.

Le recalcul TP stage 33 continue dans son processus existant et ses checkpoints ; aucune modification de son code/configuration ne les invalide. Vérifier son état avant toute reprise, sans lancer un doublon. Prochaine collecte : compléter les preuves des extrémités dans `config/accessibility_road_endpoint_evidence_review.json`, en archivant les sources avec `src/data_collection/collect_evidence.py --config config/accessibility_road_endpoint_sources.json`. Avant le routage, configurer localement la clé ORS et implémenter le collecteur reprenable ; ne pas envoyer la clé dans le chat. Ensuite seulement, calculer les trajets, comparer aux TP avec leurs limites géographiques, présenter la couverture et soumettre les choix de seuil/exposition avant toute nouvelle estimation.

Les nouvelles preuves sont stockées dans la configuration de revue distincte avant intégration, pas simplement saisies dans un CSV de sortie. Le script refuse de régénérer si un inventaire a été modifié depuis son empreinte enregistrée. Les consignes scientifiques du skill tableaux ont guidé la séparation entre anciennes coordonnées/proxys, coordonnées réellement documentées et valeurs manquantes ; aucun classeur ni mise en page supplémentaire n'est créé.
