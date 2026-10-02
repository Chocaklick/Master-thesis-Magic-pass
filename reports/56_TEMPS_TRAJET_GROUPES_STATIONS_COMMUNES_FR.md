# Temps de trajet entre groupes-stations et communes — étape 6

## Résultat

Le réseau horaire officiel GTFS hiver 2026 relie maintenant les **71 groupes-stations** aux **186 séries communales hôtelières**, soit **13,206 couples** et **316,944 requêtes horaires**. Le meilleur point d'accès du groupe est retenu séparément pour chaque horaire.

| Indicateur | Nombre |
|---|---:|
| Couples complets sur les 24 horaires | 7,571 |
| Couples utilisables descriptivement après contrôle du nœud | 7,116 |
| Temps moyen aller simple ≤ 30 min | 7 |
| ≤ 60 min | 52 |
| ≤ 90 min | 173 |
| ≤ 120 min | 459 |
| Communes avec au moins un groupe à ≤ 120 min | 85 / 186 |
| Groupes avec au moins une commune à ≤ 120 min | 57 / 71 |

Le temps généralisé inclut l'attente jusqu'au premier départ. Cinq départs aller entre 08:00 et 10:00 et sept retours entre 15:00 et 18:00 sont testés le mercredi 4 et le samedi 7 février 2026. Les seuils 30/60/90/120 minutes sont des variantes descriptives, pas une définition imposée du bassin touristique.

## Limites

Il s'agit d'horaires publiés actuels : ni retards, ni voiture, ni marche non codée, ni tarifs. Conformément à la décision du chercheur, l'accès actuel est maintenu fixe pour le premier test; la stabilité historique reste `not_yet_verified_against_anchor_year_timetables`. Les résultats sont donc adaptés à la construction d'expositions descriptives, pas à une interprétation causale.

## Reprise et fichiers

Le cache est enregistré **par groupe et par jour** dans `data_interim/accessibility_station_group_journeys`. Une interruption reprend aux groupes non calculés.

- `data_processed/accessibility_station_group_journey_context.csv` : un couple groupe–commune;
- `data_processed/accessibility_station_group_journey_samples.csv` : les requêtes horaires;
- `reports/accessibility_station_group_journey_summary.json` : comptes et empreintes.
