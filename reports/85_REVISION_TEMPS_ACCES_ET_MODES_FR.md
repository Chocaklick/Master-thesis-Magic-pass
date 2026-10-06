# Révision des temps d’accès et déplacements réels — 6 octobre 2026

## État : méthode implémentée, recalcul complet en cours

Les règles demandées sont codées dans une version séparée. Le routage national est en cours : **ne pas lire les premiers points terminés comme un résultat pour toutes les communes**. Le manifeste `accessibility_reference_time_v2_summary.json` indique le dernier point enregistré et l’état réel. Les 71 groupes, 75 points d’accès et 186 séries d’origine sont conservés ; ces séries correspondent à 185 territoires après le raccordement de Moutier déjà validé. Aucun nouveau bassin, seuil, témoin ou résultat causal n’est adopté.

Les anciens fichiers de trajets, panels, estimations et graphiques restent protégés par empreintes SHA-256. Le tableau des études et la revue des 75 accès locaux sont déjà disponibles, indépendamment du calcul long.

## Calcul validé

Pour chaque couple commune–groupe et chaque jour :

`temps_jour = (minimum des trajets du matin + minimum des retours du soir) / 2`

Puis `temps_reference = (temps_mercredi + temps_samedi) / 2`, conformément à ta réponse. Jours et requêtes conservés : 4 et 7 février 2026, cinq départs matin et sept retours, soit 24 horaires au total par couple.

- Le temps exclut **seulement l’attente avant le premier véhicule**. Le trajet, les attentes de correspondance et la marche codée sont conservés. Une marche initiale codée est identifiée séparément pour ne pas la retirer avec l’attente.
- **Aucun filtre 24/24**, ni taux minimal de réussite alternatif. Un seul trajet disponible peut fournir le minimum d’un sens pour un jour. Les nombres de départs disponibles et l’étendue max–min restent visibles.
- Si un sens manque, son minimum et le temps du jour restent manquants. Si un jour ne peut être calculé, le fichier conserve l’autre jour séparément et signale la moyenne de deux jours comme incomplète : aucune valeur n’est inventée et aucune commune n’est retirée.
- Chaque point d’accès est interrogé séparément, puis les minima sont pris au niveau du groupe. L’ancien meilleur accès, choisi avec attente incluse, n’est pas recyclé comme s’il était nécessairement le plus court sans attente.

Ces minima portent sur les **itinéraires retournés pour les requêtes disponibles**, pas sur une recherche exhaustive du trajet de durée minimale à toute heure. Le moteur existant retourne une arrivée au plus tôt pour chaque demande. Ses bornes de collecte antérieures — six véhicules et 480 minutes avec attente — restent explicites ; un échec signifie « pas d’itinéraire utilisable dans ces requêtes/bornes », pas « aucune liaison possible ». Les supprimer ou changer l’horizon demande une validation supplémentaire.

Attention : l’origine reste l’arrêt communal choisi antérieurement, **pas nécessairement le centre communal**. L’arrivée reste un arrêt d’accès, **pas toujours le départ réel de la remontée**. Le temps publié reste donc un proxy entre nœuds tant que les derniers mètres ne sont pas vérifiés ; aucun kilomètre à vol d’oiseau n’est converti automatiquement en marche. Les horaires 2026 ne sont pas certifiés valables pour toutes les années historiques.

## Accès locaux : correction et preuves

Le rejet automatique « aucun véhicule » est remplacé par une classification explicite. Un accès local à documenter n’est plus présenté comme une absence de transport. Le code accepte un temps de marche sourcé entre les véritables extrémités, ou zéro **uniquement avec preuve de leur coïncidence réelle** ; l’identité de deux identifiants d’arrêt ne suffit pas.

| Cas | Preuve / limite actuelle | Action restante avant valeur définitive |
|---|---|---|
| Leukerbad / Torrent | My Leukerbad indique **5 min à pied**, terminal de bus → départ Torrent. Fiche estivale, retour non précisé. | Vérifier l’applicabilité hivernale et le retour ; ne pas remplacer par zéro. |
| Hasliberg / Twing | Guide ATE hiver 2010/11 : **0,5 min à pied** depuis Wasserwendi Twing. Source ancienne, retour non précisé. | Vérifier la configuration actuelle et le retour ; pas de transfert automatique à 2026. |
| Beatenberg / Hohwald | L’option sans véhicule à Waldegg était masquée par l’autre accès du groupe. | Conserver cette option dans l’inventaire et documenter le chemin jusqu’au départ Hohwald. |
| Château-d’Œx / La Braye | Connexion sans véhicule entre deux arrêts différents. | Distinguer durée de transfert GTFS et marche réellement vérifiée jusqu’à la remontée. |

Sources directes : [My Leukerbad / Suisse Rando, information de départ](https://www.schweizer-wanderwege.ch/de/wandervorschlaege/3050/Thermi-Erlebnisweg-auf-Torrent) ; [ATE, Ride & Glide 2010/11, p. 12](https://www.mobilservice.ch/admin/data/files/news_section_file/file/2469/lride-glider-sur-les-pistes-en-train-et-en-bus.pdf?lm=1418801183). Le site [Meiringen-Hasliberg](https://en.meiringen-hasliberg.ch/Infos/anreise) donne aussi environ **12 min gare de Meiringen → télécabine** : autre origine/départ, donc pas une valeur pour Twing. Les preuves partielles sont conservées, mais aucun aller-retour local chiffré n’est encore appliqué sans documentation correspondante.

## Études : ce qu’elles montrent réellement

| Étude primaire | Résultat observé | Limites importantes |
|---|---|---|
| [Baumann, Schubert et Del Duce, 2025 : Toggenburg](https://link.springer.com/chapter/10.1007/978-3-031-85578-8_10) | Enquête hiver 2022/23, 572 visiteurs : **92,7 % voiture** ; sous-groupe ski **94,3 %**, calculé comme 100 − 5,7 %. 45,2 % des visiteurs sont à la journée. | Région nécessitant train puis bus ; recrutement volontaire, revenus/formation élevés. Les 7,3 % hors voiture ne sont **pas tous des TP**. Taille du sous-groupe ski non précisée dans la section consultée ; pas de ventilation modale journée/séjour. |
| [Imesch, 2010 : Saint-Bernard, enquête 2008](https://doc.rero.ch/record/18333/files/WP_4.pdf) | Voiture : **Champex 98 %, La Fouly 96 %, Vichères 100 %, Super Saint-Bernard 95 %** ; TP respectivement 2/4/0/5 %. 84 % de réponses excursionnistes. | 100 questionnaires, mais **256 réponses par station pour le mode**, 263 pour le type de visite ; pas autant de personnes indépendantes. Principalement fin de saison/week-end hors vacances. Historique, non représentatif de toutes les stations actuelles. |
| [Blättler, Wallimann et von Arx, 2024 : Appenzell](https://arxiv.org/html/2401.14945v2) | Séjournants ≥3 nuits, mai–octobre 2023 : **44 % TP chez les informés** d’une offre de trajet gratuit, **22 % chez les non-informés** ; échantillon analytique sélectionné de 654 personnes. | Pas une enquête de ski hivernal ni d’excursionnistes. Les deux groupes diffèrent ; l’écart brut ne devient pas automatiquement un effet causal. Arrivée à l’hébergement, pas trajet hôtel–remontée. |
| [Masse / EPFL LaSUR / DGMR, 2025 : loisirs vaudois](https://www.epfl.ch/labs/lasur/wp-content/uploads/2026/02/SeABeMoL_rapport-analytique_19.03.25-2.pdf) | Courts séjours hivernaux ≤4 jours en Suisse : **73,1 % voiture** = 45,5 % conducteurs + 27,6 % passagers ; **22,4 % train**. | Résidents vaudois, séjour le plus marquant ; pas exclusivement ski, ni visiteurs étrangers. Train ≠ tous TP. Les 1 854 répondants concernent l’enquête hivernale entière, pas automatiquement ce tableau. Date de début incohérente en annexe conservée comme telle. |

Conclusion : la voiture domine dans les enquêtes de ski trouvées, mais les stations et clientèles diffèrent. **Ces sources ne donnent pas une comparaison nationale, actuelle, à station égale, entre excursionnistes et séjournants.** Leur contraste ne permet donc pas d’inventer des poids voiture/TP par commune. Pour les nuitées, il faut également distinguer le trajet domicile–hébergement du trajet hébergement–départ de station.

## Proposition, non appliquée

Je propose de construire ensuite **un temps routier comme référence potentielle**, de conserver les TP corrigés comme comparaison, et de traiter séparément la marche locale documentée. C’est une orientation fondée sur la prédominance automobile observée, **pas la preuve qu’un seuil routier définit un bassin hôtelier**. Mode, source de routage, origine exacte, circulation et seuil doivent être validés avant ce nouveau calcul. Aucune moyenne voiture/TP pondérée par des parts modales non observées n’est proposée.

## Fichiers et reprise

- Disponibles : `reports/accessibility_mobility_literature.csv` (13 constats sourcés) et `reports/accessibility_reference_time_v2_local_review.csv` (75 points, preuves partielles et limites).
- Après routage complet : `data_processed/accessibility_reference_time_v2_samples.csv`, `..._daily.csv`, `..._pairs.csv` et `reports/accessibility_reference_time_v2_query_status.csv`. La comparaison aux moyennes anciennes figure dans le fichier des couples. Ne pas annoncer ces quatre résultats comme terminés avant le statut final du manifeste.
- Reprise : `.venv/Scripts/python.exe -u src/run_accessibility_reference_time_revision.py`. Réutilise seulement les caches dont configuration/code/source et SHA sont valides ; n’exécuter **qu’une instance**. `--max-new-caches N` permet un arrêt propre après N nouveaux points/jours ; `--aggregate-only` exige tous les caches. Le wrapper enrichit ensuite les preuves locales et actualise les empreintes.
- Sources/variables : registres centraux `metadata/data_sources_master.csv` et `metadata/data_dictionary.csv`. Trois limites d’archivage enregistrées : Springer a retourné une page de challenge HTTP200, RERO un HTTP410, et Mobilservice refuse l’archivage automatisé via robots.txt. Les contenus primaires ont été consultés via le navigateur de recherche ; aucun original complet local n’est prétendu pour ces cas.

Validation actuelle : **168 tests réussis**, dont 14 nouveaux sur minima/jours, attente versus marche, correspondances, couverture partielle, manque d’un sens, accès locaux, populations des études, dictionnaire/provenance et préservation des empreintes. Les vérifications des sorties complètes restent à exécuter après le routage. Journal et état du projet indiquent ce point de reprise.
