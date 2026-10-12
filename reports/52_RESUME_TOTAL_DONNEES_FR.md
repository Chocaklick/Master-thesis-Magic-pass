# Résumé des données récoltées

## Vue d'ensemble

Le projet rassemble des données sur les stations de ski suisses, la fréquentation hôtelière, l'adhésion au Magic Pass, la neige et la météo, la population, l'accessibilité et l'environnement concurrentiel. Les données proviennent principalement de l'OFS, de MétéoSuisse, du SLF, de l'ARE, de l'OFT, de l'ASTRA, d'Eurostat, de Magic Pass et d'opérateurs de remontées mécaniques.

L'inventaire comprend **271 fiches de stations**, **242 clusters de remontées**, **186 communes hôtelières**, une série mensuelle allant de **janvier 2013 à mars 2026**, ainsi que **104 clusters considérés comme candidats apparents non membres**. L'extension d'accessibilité ajoute **71 groupes de stations Magic Pass** reliés aux 186 séries communales. Les registres techniques contiennent désormais **5 459 définitions table-variable** et **229 sources documentées**. Le présent résumé regroupe les variables proches afin d'éviter de répéter les identifiants, indicateurs de qualité et champs de provenance présents dans plusieurs tables.

| Grande famille | Contenu principal | Couverture essentielle |
|---|---|---|
| Stations et domaines skiables | Localisation, altitude, kilomètres de pistes, remontées et clusters | 271 fiches, 242 clusters, 1 805 remontées |
| Tourisme hôtelier | Arrivées, nuitées, capacité et occupation | 186 communes, 31 248 mois-communes |
| Magic Pass et autres forfaits | Entrées, sorties, saisons et droits hiver-été | 93 événements Magic Pass et 5 forfaits concurrents historiques |
| Population et dépendance touristique | Population, nuitées par habitant et lits par habitant | Suisse 2025-2026 et grille transfrontalière 2021 |
| Neige et climat | Neige, température, précipitations et anomalies | Séries mensuelles et hivernales, principalement 2013-2026 |
| Transport et accessibilité | Temps de trajet, arrêts, gares, routes et horaires | 268 points suisses; 13 206 couples groupe-commune dans l'extension |
| Réseau et aide à la décision | Voisinage, analogues, segmentation et qualité | 162 clusters, dont 104 candidats apparents |

## 1 Stations, remontées et géographie

| Variable ou groupe de variables | Description rapide |
|---|---|
| `resort_id`, `cluster_id` | Identifiants stables de la fiche station et du cluster de remontées auquel elle est rattachée. |
| Nom, région et URL | Nom original et harmonisé de la station, région et page source de la fiche. |
| Latitude, longitude | Coordonnées du point représentant la station. Trois points se trouvent hors de la couche communale suisse actuelle. |
| `altitude_top_m` | Altitude maximale publiée pour la station, en mètres. |
| `ski_area_km` | Longueur publiée du domaine skiable, en kilomètres de pistes. |
| `number_lifts` | Nombre total de remontées publié dans l'annuaire de stations. |
| Type et géométrie des remontées | Nom, type, identifiant et tracé des 1 805 remontées de la couche hivernale. |
| Taille et forme du cluster | Nombre de stations et de remontées, centroïde, étendue, distance au cluster voisin et diamètre du cluster. |
| Qualité d'assignation | Distance station-cluster, qualité du rapprochement, incertitude et besoin éventuel de contrôle manuel. |
| Commune de rattachement | Code BFS et nom de la commune contenant le point. Cette commune est un repère géographique, pas automatiquement le marché touristique de la station. |

Les 271 fiches sont reliées à 162 clusters; 156 clusters disposent simultanément de l'altitude, des kilomètres de pistes et du nombre de remontées. Le clustering existant a été audité et conservé, sans reclassement.

## 2 Tourisme hôtelier et capacité

| Variable ou groupe de variables | Description rapide |
|---|---|
| Commune, code BFS, date | Unité géographique et mois d'observation. La série couvre janvier 2013 à mars 2026. |
| `hotel_overnights` | Nombre mensuel total de nuitées hôtelières. 28 455 valeurs sont observées; les cellules confidentielles restent manquantes. |
| `hotel_arrivals` | Nombre mensuel d'arrivées dans les hôtels. |
| Nuitées suisses et étrangères | Répartition des nuitées entre clientèle domestique et étrangère. Le fichier brut conserve aussi le détail par pays d'origine. |
| Établissements ouverts | Nombre d'établissements hôteliers ouverts pendant le mois. |
| Chambres et lits disponibles | Capacité hôtelière mensuelle disponible. Les trois mesures de capacité sont complètes dans 29 274 mois-communes. |
| Chambres-nuits | Offre mensuelle totale de chambres multipliée par les jours d'ouverture. |
| Taux d'occupation | Taux officiel d'occupation des chambres et des lits. Ils ne sont pas moyennés entre communes lorsque cela serait incorrect. |
| `log_overnights` | Transformation logarithmique des nuitées, utilisée pour certains diagnostics. |
| Nuitées par lit disponible | Indicateur descriptif de demande rapportée à la capacité du mois. |
| Portée de la destination | Nombre de communes attendues et observées, complétude du périmètre et statut de la définition géographique. |

Le panel agrégé historique contient **1 848 mois-destinations pour 11 destinations**, dont 1 581 avec une valeur complète de nuitées et 1 637 avec une capacité complète. Trois destinations composites en étaient exclues parce que leur périmètre hôtelier était incomplet. La nouvelle branche ne remplace pas ces 11 périmètres : elle utilise plutôt les temps de trajet pour construire une exposition commune–mois à 71 groupes de stations.

## 3 Magic Pass et autres forfaits

| Variable ou groupe de variables | Description rapide |
|---|---|
| `event_id`, destination publiée | Identifiant de l'événement et libellé utilisé dans la source officielle. |
| Type d'événement | Entrée dans le pass de base, sortie, inclusion particulière ou supplément. |
| Saison et date d'entrée | Saison d'adhésion, date exacte lorsqu'elle est connue et précision de cette date. |
| Date de sortie | Fin documentée de l'adhésion; elle empêche de supposer que le traitement reste toujours actif. |
| Statut saisonnier | Destination active ou non pour chaque saison étudiée. |
| Accès hiver et été | Droit documenté en hiver, en été, ou seulement au niveau global du produit. Les droits non nommés ne sont pas imputés. |
| Lien avec station et cluster | Station correspondante, cluster, méthode de rapprochement, confiance et éventuel chevauchement de périmètre. |
| Source et preuve | Document officiel, page, date, type de preuve, notes et niveau de confiance. |
| Forfait concurrent | Nom du produit, saison, domaine couvert, niveau d'accès et éventuelle limite en jours. |

Les données Magic Pass contiennent **93 événements officiels**, dont 88 entrées dans le pass de base. L'ancien panel partait de 18 liens disposant d'une correspondance directe et d'un périmètre hôtelier; la revue élargie exclut 10 entrées entièrement étrangères et répartit les **78 entrées suisses ou à composante suisse dans 71 groupes**. L'historique concurrentiel couvre Top4, Meilenweiss, Schneepass Zentralschweiz, TopCard et SnowPass Graubünden: 155 couples domaine-saison et 184 liens positifs documentés. Une absence de lien ne prouve pas l'absence du marché.

## 4 Population, communes et dépendance touristique

| Variable ou groupe de variables | Description rapide |
|---|---|
| Population résidente 2025 | Population permanente officielle de la commune, alignée sur les limites communales de 2026. |
| Géométrie et point communal | Surface, coordonnées représentatives et date de référence de la commune. |
| Pont 2025-2026 | Correspondance des codes BFS modifiés lors des fusions ou changements territoriaux. |
| Population à 30, 60, 90 et 120 km | Population suisse située dans plusieurs rayons autour du cluster, calculée en ligne droite. |
| Population transfrontalière | Population 2021 de la grille Eurostat à 1 km, séparée entre Suisse, étranger et cellules mixtes. |
| Distance aux centres de population | Distance aux communes dépassant différents seuils de population. |
| Nuitées par habitant | Intensité hôtelière annuelle de la commune ou du périmètre examiné. |
| Lits pour 1 000 habitants | Capacité hôtelière moyenne rapportée à la population. |
| Périmètre touristique | Commune du point, périmètre hôtelier examiné, ou test de rayon à 0, 5 et 10 km. Ces définitions restent distinctes. |

Les données couvrent **2 115 communes STATPOP 2025**, alignées sur **2 110 géométries communales 2026**, et 181 598 cellules de population Eurostat retenues autour des stations. Dans l'ancien panel, une intensité touristique complète est disponible pour les 11 destinations examinées, mais sept reposent encore sur une commune centrale plutôt que sur un bassin touristique complet. L'extension contourne cette limite en observant toutes les communes hôtelières accessibles, sans affirmer qu'elles appartiennent administrativement à la station.

## 5 Neige, température et précipitations

| Variable ou groupe de variables | Description rapide |
|---|---|
| Station neige, distance et écart d'altitude | Station SLF associée, distance à la station et différence entre son altitude et le sommet du domaine. |
| Profondeur de neige | Moyenne, médiane et maximum mensuels de neige au sol, en centimètres. |
| Jours au-dessus de 10, 20 et 30 cm | Nombre et part des jours observés dépassant chaque seuil. |
| Neige fraîche modélisée | Cumul mensuel de neige fraîche estimée par le SLF. |
| Couverture et qualité du proxy | Part des jours observés, nombre d'hivers utilisables et qualité spatiale du rapprochement. |
| Vulnérabilité neige | Profondeur hivernale moyenne, variabilité, tendance, fréquence des hivers peu enneigés et fiabilité au seuil de 30 cm. |
| Température | Température moyenne mensuelle et moyenne des minima et maxima journaliers. |
| Jours de gel | Part des jours observés avec gel. |
| Précipitations | Cumul mensuel, part des jours avec au moins 1 mm et fenêtre officielle d'observation. |
| Anomalies climatiques | Écart de température et de précipitations par rapport aux normales mensuelles calculées sur 2013-2025. |
| Sensibilités alternatives | Comparaison avec une deuxième station, les grilles MétéoSuisse à 1 km et le produit de neige SPASS. |

Parmi 166 stations neige disposant de données, 115 passent le seuil de couverture. Les 271 stations de ski ont un proxy SLF, mais 60 rapprochements sont de faible qualité. Pour la météo, sept stations SwissMetNet couvrent les 15 composantes des destinations examinées; 1 744 mois-destinations ont température et précipitations complètes. Ces mesures décrivent les conditions régionales et ne constituent pas des observations directes des pistes ou de l'enneigement artificiel.

## 6 Transport et accessibilité

| Variable ou groupe de variables | Description rapide |
|---|---|
| Zone NPVM et méthode d'assignation | Zone de trafic contenant le point ou zone la plus proche dans la même commune; distance du proxy conservée. |
| Temps routier vers un grand centre | Temps de trajet modélisé en voiture vers le grand centre le plus rapide. |
| Temps en transports publics vers un grand centre | Temps modélisé par l'ARE vers le grand centre le plus rapide. |
| Temps vers une agglomération | Temps routier et en transports publics vers l'agglomération ou commune-centre la plus rapide. |
| Arrêt de transports publics le plus proche | Nom, identifiant, mode, opérateur et distance en ligne droite. |
| Gare ferroviaire la plus proche | Nom, mode officiel et distance en ligne droite vers un arrêt ferroviaire. |
| Axe routier national le plus proche | Identifiant, numéro de route et distance au réseau principal ou à l'ensemble des axes publiés. |
| Trajet horaire aller et retour | Temps d'attente, temps prévu, durée généralisée, transferts et modes pour les fenêtres du matin et du retour. |
| Couverture des trajets | Nombre de requêtes faisables et part des horaires échantillonnés couverts. |

Le contexte NPVM et les distances aux arrêts sont disponibles pour 268 fiches suisses sur 271. L'ancien panel contient 49 104 trajets échantillonnés et 2 046 couples destination-commune. L'extension produit **316 944 requêtes horaires**, agrégées en **13 206 couples groupe-commune**; 459 sont à 120 minutes ou moins dans la matrice brute. Une archive GTFS officielle de 2018 permet aussi une validation ciblée de 39 relations prioritaires sous trois hypothèses de correspondance, mais pas une reconstruction historique complète du réseau. Ces données restent descriptives: elles ne mesurent ni les perturbations réelles, ni un temps routier porte-à-porte validé.

## 7 Concurrence, réseau et données d'aide à la décision

| Variable ou groupe de variables | Description rapide |
|---|---|
| Distance à la station voisine | Distance au cluster de ski le plus proche, en excluant le cluster lui-même. |
| Voisins à 25 et 50 km | Nombre de clusters, de stations et de domaines Magic Pass ou concurrents dans chaque rayon. |
| Taille skiable voisine | Somme des kilomètres de pistes observés autour du cluster, avec les valeurs manquantes conservées séparément. |
| Densité de réseau de forfaits | Nombre et part des clusters voisins liés au Magic Pass ou à un forfait concurrent examiné. |
| Segment structurel | Groupe obtenu à partir de l'altitude, des kilomètres de pistes et du nombre de remontées. Deux segments ont été retenus. |
| Analogues | Clusters Magic Pass et destinations examinées les plus proches sur le profil structurel. |
| Distance de similarité et OOD | Écart au voisin le plus proche et classe de support: bon, extrapolation modérée ou forte. |
| Sensibilité d'agrégation | Stabilité du segment et des analogues lorsque les caractéristiques du cluster sont résumées par le minimum, la médiane ou le maximum. |
| Qualité des données | Synthèse de la couverture, de la qualité des liens et des principales incertitudes. |
| Variables finales laissées vides | Effet prédit, score composite, confiance de recommandation et recommandation. Elles ne sont pas calculées faute d'identification suffisante. |

Le tableau final couvre **104 candidats apparents**. Parmi eux, 74 ont un bon support structurel, 5 une extrapolation modérée et 25 une forte extrapolation; seuls 11 restent stables sur tous les tests d'agrégation. Ces résultats servent à comparer les profils, pas à mesurer l'effet causal du Magic Pass ni à classer les stations.

## 8 Variables temporelles, qualité et limites

Les tables mensuelles contiennent aussi l'année, le mois, le trimestre, la saison Magic Pass, les indicateurs hiver-été, Noël-Nouvel An, Pâques et une période large de sensibilité COVID. Les champs de contrôle indiquent la source, la couverture, les valeurs manquantes, la qualité du rapprochement, le rôle causal possible et l'autorisation ou non d'utiliser la variable dans un modèle.

Les principales données encore absentes ou insuffisantes sont: les horaires historiques complets, un temps routier validé entre communes et stations, l'enneigement artificiel et les jours d'ouverture, l'accès piéton jusqu'aux remontées, des infrastructures datées de façon homogène, le marché historique complet des forfaits concurrents et des données financières permettant d'estimer la rentabilité. En conséquence, les données permettent aujourd'hui une **analyse descriptive et une aide à la comparaison**, mais pas une estimation causale fiable, un uplift prédit ou une recommandation chiffrée.
