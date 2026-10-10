# Pilote relief 2 m : St-Luc–Chandolin

10 octobre 2026 — Attribution des altitudes : **Office fédéral de topographie swisstopo**. Axes : contributeurs OpenStreetMap, originaux et identifiants conservés.

Le chercheur valide l’édition la plus récente disponible par tuile, dates conservées, avec comparaison pilote des éditions 2019 et 2024. La décision est enregistrée dans `config/terrain_vintage_decisions_stage62.json` ; aucune édition n’est présentée comme un relief préentrée vérifié.

## Collecte et extraction achevées

**84 GeoTIFF 2 m**, environ 95,8 Mo, téléchargés sans échec ni doublon. Toutes les empreintes SHA-256 correspondent au catalogue fournisseur. Les en-têtes confirment EPSG:2056, cellules natives 2 m et altitudes en mètres. Les originaux restent intacts et hors Git. Quarante-deux emprises par édition couvrent la boîte du pilote, dont 25 directement traversées par les axes ; les voisines permettent de lire les véritables cellules adjacentes, sans interpolation.

La nouvelle version du réseau conserve **70 groupes, 854 objets**, dont 846 axes candidats et 8 surfaces séparées. Quarante groupes ont des axes cartographiés ; Sainte-Croix reste sans axes référencés et 29 correspondances restent non résolues, toutes conservées. Les longueurs des 69 groupes autres que St-Luc sont inchangées. Les anciens fichiers, sources, accès, clusters et nuitées ne sont pas remplacés.

Pour St-Luc, l’union exacte des axes représente **50,038 km cartographiés**, répartis dans **31 806 cellules**. Ce n’est ni le kilométrage officiel ni une couverture exhaustive certifiée. Les deux éditions utilisent exactement les mêmes cellules et longueurs. L’altitude centrale et le voisinage complet Horn 3 × 3 sont observés sur toute cette longueur dans les deux éditions : aucune valeur manquante inventée, aucun besoin d’interpolation. L’exposition est l’azimut descendant du terrain, pas la direction du tracé.

## Comparaison des éditions

| Indicateur sur les axes actuels | 2019, comparaison | 2024, référence |
| --- | ---: | ---: |
| Altitude minimale observée | 1 678,02 m | 1 679,79 m |
| Altitude maximale observée | 2 972,89 m | 2 972,54 m |
| Altitude moyenne pondérée par longueur | 2 320,37 m | 2 320,14 m |
| Pente moyenne du terrain pondérée par longueur | 15,60° | 14,26° |
| Longueur avec altitude et gradient observés | 100 % | 100 % |

Les moyennes d’altitude diffèrent d’environ −0,24 m. La différence absolue moyenne cellule par cellule, pondérée par longueur, vaut 0,46 m ; son maximum vaut 6,05 m. Pour la pente, la moyenne diminue de 1,34°, mais la différence absolue moyenne cellule par cellule vaut 3,48° : **la proximité des altitudes moyennes ne suffit pas à garantir la stabilité des orientations et des pentes locales**.

Ces différences décrivent les éditions du modèle, pas un effet du Magic Pass ou une évolution causale du domaine. L’altitude maximale le long des axes n’est pas nécessairement celle du sommet ou des installations. Les dates de référence, de création et de mise à jour restent distinctes d’une date réelle d’acquisition non vérifiée. Aucun raccordement ou correction entre éditions n’est appliqué.

## Fichiers et garde-fous

- [Synthèse des deux éditions](../data_processed/terrain_native2m_pilot_summary_stage63.csv).
- [Cellules, longueurs, altitudes, pentes et expositions détaillées](../data_processed/terrain_native2m_pilot_cells_stage63.csv).
- [Réseau cartographié unique actualisé](../data_processed/winter_profile_exact_piste_overlap_stage63.csv).
- [Manifeste, empreintes et contrôles des 84 en-têtes](native2m_terrain_pilot_stage63_summary.json).

Les 84 sources originales et la source dérivée sont inscrites dans le registre ; toutes les variables CSV sont définies. Les angles restent détaillés : **le résumé de l’exposition d’un groupe a été soumis au chercheur**, indicateurs continus nord/sud–est/ouest–concentration ou quatre parts cardinales. Aucun regroupement ou orientation dominante n’est imposé avant sa réponse. Pas de nouvelle classe de stations, estimation DiD, substitution de neige ou exclusion automatique. Les alertes historiques et objets abandonnés restent suivis.

Contrôles : **320 tests réussis**, dont conservation des anciennes longueurs, identité des cellules/poids entre éditions et comparaison directe avec les valeurs GeoTIFF originales. 963 références SHA sur 552 fichiers vérifiées ; anciennes lignes du registre, du dictionnaire et des 988 événements de collecte conservées exactement. Tous les processus de collecte et calcul sont arrêtés.

## Reprise

```powershell
.venv/Scripts/python.exe -X utf8 src/data_collection/collect_terrain_tiles_stage62.py --limit 84
.venv/Scripts/python.exe -X utf8 src/descriptive/extract_terrain_pilot_stage63.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_piste_preservation_stage63.py
```

La première commande réutilise les 84 fichiers complets contrôlés ; aucune collecte achevée n’est répétée. Les sorties sont figées par leurs empreintes. Suite : résumé d’exposition après validation, extension du relief aux autres périmètres cartographiés avec dates par tuile et contrôle de couverture ; poursuite des 29 périmètres non résolus. Les variables de neige et futurs groupes de profils gardent leurs validations distinctes.
