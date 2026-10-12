# Braunwald : arrêt inférieur validé et six références routières

12 octobre 2026 — étape 90. Le chercheur a validé **Linthal Braunwaldbahn (Talst.), BAV 8503260**, à l’entrée inférieure du funiculaire. Le point de proposition de l’étape 89 est conservé dans son état historique ; la nouvelle décision est enregistrée séparément.

## Résultats

Mesure : **arrêt urbain → arrêt inférieur de Linthal**, en voiture seulement. Les six origines sont exactement celles déjà utilisées dans le projet, pas de nouveaux centres ou points du catalogue.

| Ville | Aller (min) | Retour (min) | Moyenne (min) |
|---|---:|---:|---:|
| Zurich | 82,1 | 84,8 | 83,5 |
| Berne | 158,3 | 160,2 | 159,3 |
| Bâle | 135,1 | 137,0 | 136,1 |
| Lugano | 160,3 | 160,5 | 160,4 |
| Lausanne | 219,3 | 222,0 | 220,7 |
| Genève | 249,1 | 251,6 | 250,3 |

Le minimum des six moyennes est **83,4558 minutes depuis Zurich**. L’arrondi à une décimale sert uniquement à la lecture ; les valeurs sources et calculées restent conservées dans les CSV.

[Six trajets détaillés](../data_processed/braunwald_urban_road_city_reference_stage90.csv) · [12 observations directionnelles](../data_processed/braunwald_urban_road_directional_stage90.csv) · [Raccordements au réseau](../data_processed/braunwald_urban_road_snapping_stage90.csv).

## Méthode et limites

Deux vraies requêtes Matrix ORS, une dans chaque sens, ont retourné les **12 durées**. Pour chaque ville : `(aller + retour) / 2`, puis minimum parmi les six villes. Aucun temps n’est remplacé par son sens opposé. Le trajet rapide statique ne représente ni des embouteillages ni un trajet historique ou observé de visiteurs.

Réseau retourné : **21 septembre 2026 à 10:31:27 UTC**, moteur **9.10.0** — même version que la référence routière corrigée antérieure. Collecte le 12 octobre 2026 à 15:41:57 et 15:41:59 UTC. Endpoint : `https://api.heigit.org/openrouteservice/v2/matrix/driving-car`. Réponses originales, paramètres, horodatages, versions, contrôles SHA et en-têtes de quota non sensibles sont archivés ; la clé n’est ni affichée ni enregistrée.

À Linthal, ORS rapporte un raccordement de **22,93 m** dans les deux sens ; le déplacement géodésique indépendant est **22,96 m**. Aux six origines, les raccordements rapportés vont de **22,34 à 91,99 m**. Coordonnées demandées et coordonnées raccordées restent distinctes. Ce ne sont pas des distances de marche et aucune durée de raccordement n’est inventée. Pas de route nulle, de point distinct confondu avec l’arrivée ou de durée manquante dans ce lot.

**Le funiculaire vers Braunwald et l’accès aux pistes ne sont pas mesurés : valeurs manquantes, jamais zéro.** La voiture s’arrête à Linthal ; ce n’est donc pas un temps complet ville–pistes. La matrice ne fournit pas de géométrie permettant de certifier toutes les restrictions hivernales ou légales du parcours : elles restent non vérifiées, sans supplément neige, parking ou marche ajouté.

Sources : coordonnées originales **BAV_PUBLIC_TRANSPORT_STOPS_2026**, état du 20 septembre 2026 ; accès automobile documenté par [Sportbahnen Braunwald](https://sportbahnen-braunwald.ch/de/informationen/anreise.html), archive **NATIONAL_BRAUNWALD_ARRIVAL_STAGE89**. Sources nouvelles : **DERIVED_BRAUNWALD_URBAN_ENDPOINTS_STAGE90**, **ORS_BRAUNWALD_URBAN_MATRIX_STAGE90**, **DERIVED_BRAUNWALD_URBAN_REFERENCE_STAGE90**, avec champs et manquants enregistrés dans les registres du projet.

## Conservation et reprise

La validation de l’arrivée ne valide pas à elle seule Braunwald comme un nouveau domaine indépendant : son identité nationale provisoire et la vérification de ses pistes restent distinctes. Anciens 69 groupes, 185 territoires, nuitées, profils préentrée et DiD restent inchangés. Aucun clustering ou filtre de communes n’est appliqué.

La collecte est **terminée**, ses sorties sont figées et réutilisables sans nouvelle requête. [Manifeste](braunwald_urban_road_reference_stage90_summary.json) · [Conservation](preservation_braunwald_urban_stage90_summary.json) : **327 fichiers contrôlés**, dont les 300 sorties, configurations et producteurs numériques historiques protégés, plus les sources directement utilisées et les nouveaux résultats. Les gros rasters non concernés n’ont pas été recontrôlés dans ce lot ; leur audit complet précédent reste conservé. Les préfixes des trois registres sont inchangés : 3 sources, 116 champs et 2 vraies requêtes ajoutés, soit **1 651 sources / 9 229 champs / 2 490 événements**. La republication depuis les caches ne crée ni requête ni doublon.

**14 tests ciblés réussis** (huit nouveaux et six de conservation des étapes 88–89) vérifient l’arrivée approuvée, les origines identiques, les cellules originales, les calculs, les raccordements, les manquants et la traçabilité. Le guide CSV scientifique a servi aux contrôles de champs et de valeurs manquantes, sans mise en page supplémentaire.

La suite nationale reste la vérification des périmètres, liaisons et activités documentées des fiches supplémentaires, puis les mêmes mesures physiques. Ne pas relancer les données déjà collectées ou remettre l’arrêt inférieur en attente.
