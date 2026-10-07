# Correction routière et point restant à valider

7 octobre 2026. **Seuils validés :30 minutes au principal ;15 et45 minutes en sensibilité.** Lauterbrunnen est corrigée. Les DiD attendent la validation du point de Saas-Fee ; aucune commune n'est retirée arbitrairement, aucun zéro n'est inventé.

## Lauterbrunnen : correction terminée

L'arrêt communal devient **Lauterbrunnen8507384**, à la place de Grütschalp8507378. Identité, commune BFS584 et coordonnées E/N vérifiées dans l'archive officielle BAV/OFT déjà utilisée. La correction porte sur le point communal dans les deux directions, pas sur un départ de station.

Six nouvelles matrices ont fourni150 directions/75 couples utilisables. Les184 autres communes réutilisent exactement leurs valeurs et leur provenance. La nouvelle matrice complète conserve185 territoires,75 accès et71 groupes : **13 874/13 875 moyennes utilisables**, contre13 799 avant correction. La seule moyenne encore indéterminée est le trajet local Saas-Fee. Anciennes coordonnées, matrices, sources et réponses originales conservées.

À30 et45 minutes, Lauterbrunnen a une première exposition calculée en **mai2022** ; aucune exposition calculée à15 minutes. Ce résultat d'accessibilité n'est pas une estimation d'effet sur les nuitées.

Fichiers : `accessibility_road_stop_corrected_origins.csv`, matrices `accessibility_road_stop_corrected_directional.csv`/`_pairs.csv`, préparation et collecte `accessibility_road_lauterbrunnen_*`, audit `accessibility_road_stop_corrected_snapping_*`. Raccordements et restrictions restent signalés, sans seuil de rejet.

## Saas-Fee : proposition à valider

Le chercheur a choisi de résoudre l'accès local avant les tests, plutôt que laisser Saas-Fee sans contribution aux contrastes. L'ancien zéro Busterminal→AlpinExpress venait de deux points différents raccordés au même point routier. Le groupe Saas-Fee entre en mai2019 : ignorer cet accès pourrait faire utiliser cette commune comme témoin, ou attribuer à tort sa première exposition à Gspon en2023 au seuil45.

L'[office du tourisme](https://www.saas-fee.ch/fr/arrivee/parking-saas-fee) indique que la voiture doit rester au parking couvert ou extérieur à l'entrée du village. Deux points candidats ont été identifiés exactement dans les données officielles OFT, puis testés dans **une seule matrice locale3×3**, sans changer les coordonnées analytiques :

| Point candidat | Identifiant OFT | Moyenne locale aller/retour depuis Busterminal | Raccordement du point au réseau |
|---|---|---:|---:|
| Saas-Fee, Parkhaus | 8557144 | Zéro modèle, toujours non validé | 132,45m |
| **Saas-Fee, Parkplatz Nord** | **8511180** | **1,569min** | **62,29m** |

**Proposition : remplacer uniquement l'arrivée automobile du groupe Saas-Fee par le point officiel « Parkplatz Nord »**, pour les trajets venant de toutes les communes. Conserver l'origine communale Busterminal. Coordonnées exactes : E2638184/N1106816 EPSG2056 ; longitude7.932519089243055/latitude46.11176706686821 WGS84.

Il s'agit du point d'arrêt officiel associé au parking nord, **pas d'une entrée de parking relevée sur le terrain**. Le raccordement du Busterminal reste300,78m : la durée modélisée concerne les points raccordés au réseau, sans marche locale incluse. Le parcours parking→remontées reste distinct et son temps de marche reste manquant. Le probe positif ne certifie pas à lui seul les restrictions privées/hivernales.

Décision en attente dans `config/accessibility_saas_fee_road_endpoint_proposal.json`. Observations et réponse originale : `saas_fee_road_candidate_probe.csv` et son manifeste avec identifiants, coordonnées, réseau et SHA. Toutes les sources/variables de correction et du probe sont enregistrées dans metadata. Aucun temps de ce probe n'est encore intégré à la référence analytique.

## Reprise

La préparation Python des expositions/témoins et la relance du même estimateur sont prêtes dans `src/causal_inference/estimate_accessibility_road_did.py`. Le garde-fou interrompt avant toute estimation si un accès manquant peut rendre l'exposition indéterminée ou antérieure à la date connue. **Aucun nouveau résultat DiD n'a été publié.**

Après validation du point Saas-Fee : calculer les deux directions entre les185 origines et ce seul accès, dans un nouvel espace de collecte ; réutiliser les observations exactes déjà compatibles, ne pas relancer la correction de Lauterbrunnen ni les autres accès. Mettre à jour explicitement la référence d'entrée du nouveau DiD, sans modifier le manifeste de préparation historique de Lauterbrunnen. Puis recalculer expositions, témoins et tests aux trois seuils, avec résultats séparés des TP.
