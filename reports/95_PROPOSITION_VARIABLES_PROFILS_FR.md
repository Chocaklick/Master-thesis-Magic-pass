# Variables proposées pour les profils de stations

8 octobre 2026. Extension demandée : orientation, neige et accès automobile aux grandes villes. **Propositions seulement** : aucune nouvelle variable calculée, classification ou pondération choisie. Conserver les 71 groupes ; caractéristiques avant entrée au pass de base, hiver décembre–avril.

## Base proposée : cinq dimensions

| Dimension | Indicateurs candidats | Construction et limite |
|---|---|---|
| Taille | Kilomètres de pistes ; remontées en variante | Périmètre historique du groupe, pas somme de fiches recouvrantes. Ne pas donner deux fois le même poids à la taille. |
| Altitude | Altitude basse et altitude dominante des pistes ; sommet comme proxy disponible | Le sommet seul ne décrit pas où l’on skie. Géométrie historique et règle d’agrégation à valider ; pas de moyenne arbitraire des stations. |
| Orientation | Répartition nord/est/sud/ouest et caractère multidirectionnel | Calcul sur le terrain des pistes, pas au point de départ d’une remontée. Pour le clustering, codage circulaire ou parts directionnelles à discuter, sans codage ordinal N=1/E=2/etc. Une étiquette dominante peut masquer un domaine mixte. |
| Neige | Hauteur moyenne décembre–avril ; jours suffisamment enneigés et variabilité annuelle en variantes | Recalculer sur plusieurs hivers entièrement avant entrée. Période commune ou fenêtres propres à chaque entrée, seuil de neige et couverture minimale restent à valider. Neige locale observée/modélisée ≠ neige sur piste ou jours d’ouverture. |
| Accès urbain | Minutes en voiture vers un grand centre ; éventuellement plusieurs pôles | Définir la liste des villes et le point urbain avant collecte. Distinguer le NPVM zonal déjà disponible et de vrais trajets depuis les points d’accès conservés. Proxy routier actuel ≠ accès historique certifié. |

Le nombre exact de colonnes sera limité après examen des corrélations et de la couverture. Ne pas multiplier les métriques d’un même bloc au point de dominer les autres. Ces dimensions sont candidates, pas un protocole final approuvé ; elles peuvent aussi rester continues sans entrer toutes dans le clustering.

## Autres paramètres pertinents à tester

- **Population accessible en voiture** : complément à la proximité d’une seule ville, pour distinguer petit pôle proche et vaste marché. Population et réseau routier doivent être datés ; inclure ou non les marchés frontaliers reste à discuter. Les rayons de clientèle urbaine ne sont pas le seuil communal d’exposition de 30 minutes.
- **Enneigement artificiel** : part des pistes équipées avant entrée, si archives comparables ; ni canons actuels ni projet de travaux ne prouvent la couverture historique.
- **Profil du domaine** : part de pistes faciles/difficiles, variété et dénivelé ; utiles pour différencier offre familiale et sportive, mais pas assimiler cette offre aux visiteurs effectivement observés.
- **Concurrence antérieure** : offre skiable accessible autour du groupe, avec appartenance historique aux pass concurrents ; choisir le rayon/temps et prévenir les doubles comptes avant calcul.
- **Hébergement et dépendance touristique** : lits préentrée, poids hivernal et clientèle étrangère restent au niveau communal. Une attribution au groupe ou pondération de bassin exige une règle validée.

Les tarifs, investissements et jours d’ouverture peuvent être intéressants mais demandent souvent plus d’archives ; ne pas bloquer le premier protocole sur leur disponibilité. Les effets DiD, nuitées postentrée et succès supposé du Magic Pass ne serviront pas à construire les classes.

## Réutiliser les données déjà récoltées

Le projet possède des historiques IMIS, une grille SPASS/OSHD et des indicateurs de neige, mais les agrégats existants mélangent avant/après et l’audit de grille ne couvre que l’ancien périmètre. Ils ne seront pas transférés automatiquement aux 71 groupes. Sources déjà enregistrées : `SLF_SNOW_HISTORY`, `SLF_SPASS_HSCLQMD_GRID_1962_2023` ; rapports de neige et audit du rapport92.

L’accessibilité NPVM2025 est déjà disponible pour les fiches/anciens clusters : centre le plus rapidement atteint parmi Bâle, Berne, Genève, Lausanne, Lugano et Zurich, et accès à une agglomération. Elle utilise des zones et parfois un raccordement de proximité, pas les nouveaux départs routiers. Cette définition des six centres est celle du produit, **pas un nouveau choix validé du mémoire**. Voir [rapport22](22_TRANSPORT_ACCESSIBILITY_CONTEXT.md), sources `ARE_NPVM_TRAVEL_TIME_2025` et son STAC ; audit historique dans `config/path_c_feature_readiness.json`. Les populations BFS/Eurostat et contextes frontaliers existent aussi, mais plusieurs instantanés postdatent les premières entrées.

Pour l’orientation, [swissALTI3D](https://www.swisstopo.admin.ch/en/height-model-swissalti3d) fournit un modèle du terrain sans végétation/bâtiments ; le choix d’une géométrie de pistes et l’hypothèse de stabilité temporelle restent séparés. Pour la neige, les [cartes SLF](https://www.slf.ch/en/services-and-products/snow-maps/) mêlent observations et modèles OSHD : documentation du service, pas une archive préentrée nouvellement acquise. Deux consultations officielles enregistrées dans le registre de sources ; aucun raster ou trajet supplémentaire collecté. Tavily CLI et sa ressource de setup étaient absents ; recherche intégrée utilisée sans installation ni authentification.

## Validation et reprise

Proposer d’abord ces cinq dimensions ; après bilan de disponibilité, valider indicateurs, codage de l’orientation, fenêtre neige, villes, méthode routière et mise à l’échelle. Hébergement communal et concurrence peuvent rester des dimensions d’hétérogénéité séparées. Le protocole précédent pistes+sommet seul n’est pas figé : cette extension est proposée sans modifier ses snapshots ni checkpoints. Les nouvelles variables seront enregistrées au dictionnaire lors de leur définition opérationnelle, avec statut/provenance/manquants, jamais comme données déjà observées. Aucune exclusion liée à la disponibilité ou significativité n’est décidée.
