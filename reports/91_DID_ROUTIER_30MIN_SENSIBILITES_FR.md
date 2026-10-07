# DiD avec référence automobile

7 octobre 2026. **30 minutes au principal ;15 et45 minutes en sensibilité**, seuils validés. Même estimateur et paramètres que les tests précédents, nouvelles dates d’exposition et nouveaux témoins. Les résultats TP et la première matrice automobile restent intacts.

## Couverture et corrections

Le point communal de Lauterbrunnen est désormais l’arrêt officiel **Lauterbrunnen8507384**, et non Grütschalp8507378. Six matrices mesurent150 directions/75 couples ; les autres184 communes réutilisent leurs observations. **Saas-Fee : arrivée automobile Parkplatz Nord8511180 validée**, origine Busterminal inchangée. Les185 communes ont un trajet recalculé vers ce seul accès ; les deux directions locales du probe exact sont réutilisées. Les autres74 accès et les71 groupes restent inchangés. Les trois zéros locaux déjà approuvés restent utilisables, aucun nouveau zéro n’est inventé.

| Seuil | Exposées dans l’inventaire | Calibration/référence disponibles | Mois postérieurs effectivement utilisés |
|---:|---:|---:|---:|
| 15 min | 30 | 28 | 1886 |
| 30 min | 58 | 54 | 3625 |
| 45 min | 88 | 81 | 5337 |

Lauterbrunnen : 15min : aucune exposition calculée au seuil; 30min : première exposition 2022-05; 45min : première exposition 2022-05.

Les185 territoires restent dans l’inventaire. Une exposition au seuil ne garantit pas un historique hôtelier utilisable : les communes sans calibration/référence restent listées dans les tables de support, sans imputation. Les mois après une nouvelle entrée de station restent présents.

## Contrastes principaux

Unités : points logarithmiques sur log(1+nuitées), **pas des nuitées supplémentaires ni directement des pourcentages**. Référence : mois−1. Les compositions peuvent changer avec le mois relatif.

| Seuil | Mois relatif | Communes traitées observées | Contraste | IC ponctuel95 % | Bande simultanée95 % |
|---:|---:|---:|---:|---:|---:|
| 15 | 0 | 28 | 0.048 | [-0.082 ; 0.178] | [-0.164 ; 0.259] |
| 15 | 11 | 26 | -0.355 | [-0.827 ; 0.114] | [-1.104 ; 0.393] |
| 15 | 23 | 23 | 0.116 | [-0.050 ; 0.286] | [-0.154 ; 0.387] |
| 30 | 0 | 54 | 0.002 | [-0.093 ; 0.099] | [-0.158 ; 0.161] |
| 30 | 11 | 48 | -0.215 | [-0.478 ; 0.050] | [-0.652 ; 0.222] |
| 30 | 23 | 46 | 0.081 | [-0.031 ; 0.189] | [-0.102 ; 0.264] |
| 45 | 0 | 81 | -0.061 | [-0.147 ; 0.023] | [-0.203 ; 0.081] |
| 45 | 11 | 69 | -0.044 | [-0.220 ; 0.132] | [-0.338 ; 0.251] |
| 45 | 23 | 64 | 0.018 | [-0.071 ; 0.109] | [-0.134 ; 0.171] |

## Diagnostics et sensibilités

- 15min : 0/35 mois prétraitement et 0/101 mois postérieurs ont une bande simultanée excluant zéro. Ce décompte n’est pas un test global de tendances parallèles.
- 30min : 0/35 mois prétraitement et 0/101 mois postérieurs ont une bande simultanée excluant zéro. Ce décompte n’est pas un test global de tendances parallèles.
- 45min : 0/35 mois prétraitement et 0/101 mois postérieurs ont une bande simultanée excluant zéro. Ce décompte n’est pas un test global de tendances parallèles.

Toutes les variantes précédentes sont recalculées à chaque seuil : témoins jamais exposés seulement, soustraction de pente prétraitement, omission des contrastes COVID de mars2020 à mars2022, horizons communs6/12/24 mois et mêmes territoires à ces trois horizons. Aucun coefficient post global ni effet propre d’une entrée additionnelle n’est ajouté. Les tables publient tous les mois, pas seulement ceux du tableau.

## Méthode, sources et limites

Accessibilité : moyenne aller/retour automobile statique, puis accès le plus rapide disponible de chaque groupe et seuil inclusif. Exposition : première entrée historique d’un groupe accessible ; réseau complet conservé avec les sorties documentées selon la convention existante. Chaque seuil reconstruit ses cohortes et ses témoins, sans zone tampon ou filtre géographique nouveau.

Calcul : changements depuis−1 chez les exposées moins ceux des témoins jamais/pas encore exposés ; ces derniers cessent de contribuer à leur première entrée. Correction saisonnière estimée sur les36 mois précédents, pente soustraite uniquement en sensibilité. Pondérations égales par territoire, pondération dynamique par effectifs traités observés. Bootstrap multiplicateur territorial4 999 tirages, graine20261005, mêmes paramètres qu’avant. Bandes simultanées par courbe/variante, pas conjointement entre seuils.

Sources déjà enregistrées : HESTA OFS, historique officiel Magic Pass, BAV/OFT et matrices HeiGIT/OpenStreetMap archivées. Décision et fichiers : `config/accessibility_road_did_final_execution.json`, `accessibility_road_final_collection_summary.json`, sources/dictionnaire metadata. La comparaison avec les TP d’origine n’est plus à extrémités identiques pour les deux exceptions validées Lauterbrunnen/Saas-Fee. Raccordement au réseau dans les tables `accessibility_road_final_snapping_*` ; grand raccordement, lieux sans voitures et restrictions hivernales restent signalés sans exclusion. Busterminal de Saas-Fee : raccordement300,78m ; Parkplatz Nord :62,29m ; parcours final vers les remontées distinct et non chiffré.

Le réseau routier2026 est tenu fixe historiquement. Temps modélisés sans congestion, marche finale ou supplément neige/parking. Les communes au-delà du seuil ne sont pas certifiées sans retombées ; déplacer le seuil change à la fois les communes traitées, les dates et les témoins. Tendances préalables, chocs hôteliers/COVID et changements de composition limitent l’interprétation. Ce pipeline est un contraste Python spécifique au projet, pas l’exécution du package R did ni une certification causale.

Reprise : `.venv/Scripts/python.exe src/causal_inference/estimate_accessibility_road_did.py --config config/accessibility_road_did_final_execution.json`. Résultats séparés par seuil (`accessibility_road_did_15min/30min/45min_*`), exposition mensuelle, inventaire, univers de témoins, figure et empreintes dans `accessibility_road_did_summary.json`. Les étapes achevées sont réutilisées si leurs entrées et sorties sont inchangées ; aucune collecte routière n’est relancée.
