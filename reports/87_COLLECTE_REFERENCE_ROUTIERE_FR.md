# Référence routière — premier lot vérifié (7 octobre 2026)

La clé `ORS_API_KEY` est présente dans la variable **utilisateur Windows**, vérifiée sans affichage. Le collecteur fonctionne sur la nouvelle API : deux réponses HTTP 200, **6 trajets directionnels / 3 couples commune–parking**. Une seconde exécution les a repris sans nouvelle requête.

## Coordonnées et couverture

| Élément | Avancement | Preuve et limite |
|---|---:|---|
| Origines administratives | 3 / 185 communes | Moutier, Hasliberg et Leukerbad : adresse officielle et candidat geo.admin.ch vérifié par rue, numéro, code postal et BFS. |
| Arrivées routières | 1 / 75 accès | Parking **Twing 2**, Meiringen-Hasliberg : destination du lien de navigation fourni par l'exploitant, pas le centre d'affichage de la carte. Ce n'est pas un relevé de l'entrée de voirie. |
| Trajets calculés | 6 / 27 750 directions possibles | Chaque mairie vérifiée vers Twing, et retour indépendant. Les autres cellules restent en attente de preuves, pas exclues. |
| Hiver / marche finale | Non vérifiés | Pas de temps de marche nul inventé ; pas de certification d'accessibilité hivernale. |

Les **185 territoires, 186 historiques sources, 75 accès et 71 groupes** sont conservés, ainsi que le raccordement Moutier 700/6831. Aucun nouveau seuil, filtre de communes, bassin touristique, groupe de stations ou résultat causal n'est créé.

## Calcul et reprise

- API : `https://api.heigit.org/openrouteservice/v2/matrix/driving-car`. Durée et distance, coordonnées `[longitude, latitude]`, sans trafic réel ni heure de départ.
- Temps routier = moyenne des minutes aller et retour, seulement si les deux sens sont utilisables. La marche finale est **séparée**, manquante si non documentée.
- Une absence de trajet reste manquante. Un zéro du modèle reste visible, mais n'est pas considéré comme un véritable accès nul : le raccordement au réseau peut confondre deux points distincts. Vérification locale nécessaire.
- Réponses originales et métadonnées sous `data_external/accessibility_road_ors/`, avec requête, horodatage, graphe, coordonnées raccordées et SHA-256. Jamais de clé ni d'en-tête Authorization dans les fichiers. Redirections authentifiées désactivées.
- Checkpoints sous `data_interim/accessibility_road_ors/` : cellules achevées réutilisées même lorsque d'autres coordonnées sont ajoutées. Un point modifié ne réutilise pas une mesure à l'ancienne coordonnée. Erreurs et quotas arrêtent la collecte sans répétition aveugle.

Les réponses indiquent une limite de **500**, un restant de **498** après les deux requêtes : constat ponctuel, pas promesse de quota futur. Graphe : **21 septembre 2026**, moteur **9.10.0**. Aucun compte créé, paiement engagé ou serveur public de démonstration utilisé.

Le raccordement au réseau déplace les mairies de 6,51 à 46 mètres et Twing de 0,09 mètre. Distances conservées pour contrôle, sans décider de seuil d'acceptation. Les trajets longs ne sont pas certifiés praticables en hiver : une matrice seule ne fournit pas leur tracé pour vérifier les cols et restrictions.

## Fichiers et sources

- [Coordonnées des communes](accessibility_road_origin_review.csv) et [des accès](accessibility_road_station_arrival_review.csv).
- [Trajets directionnels](../data_processed/accessibility_road_reference_directional.csv), [moyennes aller–retour](../data_processed/accessibility_road_reference_pairs.csv), [manifest de collecte](accessibility_road_reference_collection_summary.json). Ces tableaux conservent les cellules en attente : matrice complète en identifiants, pas en mesures.
- Adresses : [Moutier](https://moutier.ch/nous-contacter/), [Hasliberg, pied de page officiel](https://www.hasliberg.ch/), [Leukerbad](https://www.leukerbad.org/). Ancienne page administrative Hasliberg : erreur404 conservée dans le journal, adresse confirmée sur la page actuelle.
- Géocodage : [documentation geo.admin.ch](https://docs.geo.admin.ch/access-data/search.html), réponses originales et caractéristiques exactes dans `config/accessibility_road_endpoint_evidence_review.json`.
- Twing : [arrivée officielle de l'exploitant](https://en.meiringen-hasliberg.ch/Infos/anreise), original déjà archivé, et redirection du lien de navigation capturée sans visiter Google Maps. Coordonnées du **lieu** `!3d46.7450222!4d8.1952418`, pas les coordonnées de viewport `@…`.
- API : [annonce officielle de migration](https://ask.openrouteservice.org/t/deprecating-api-openrouteservice-org-in-favour-of-api-heigit-org/7912), [réduction des quotas de l'ancien hôte](https://ask.openrouteservice.org/t/reducing-the-quota-of-deprecated-api-api-openrouteservice-org/8013), [restrictions Matrix](https://openrouteservice.org/restrictions/). Ancien hôte déprécié, pas le service Matrix lui-même. Sources et variables enregistrées dans les métadonnées.

## Suite exacte

Restent **182 origines et 74 arrivées** à documenter. Compléter les configurations de sources/preuves, archiver les originaux, vérifier les correspondances exactes, régénérer les inventaires, reprendre le collecteur. Ne pas compléter directement les CSV générés. Contrôler les restrictions hivernales et documenter la marche finale. Tout choix supplémentaire de seuil, point ambigu, regroupement des accès ou remplacement des expositions sera soumis au chercheur.

Commandes depuis la racine :

```text
.venv/Scripts/python.exe src/data_processing/prepare_accessibility_road_reference.py
.venv/Scripts/python.exe src/data_processing/plan_accessibility_road_matrix.py
.venv/Scripts/python.exe src/data_collection/collect_accessibility_road_matrix.py --execute --max-new-batches 2
```

La variable utilisateur doit être lue sous le compte du chercheur : le compte isolé de la sandbox ne la voit pas nécessairement. Ne jamais copier la clé dans le code ou la ligne de commande.

Les anciens résultats restent conservés. Le recalcul TP révisé est terminé (**334800 requêtes, 26412 lignes quotidiennes, 13206 couples groupe–historique**) ; les six sorties et treize résultats protégés concordent avec leurs SHA-256. Il reste un proxy entre anciens arrêts, non une comparaison aux mêmes extrémités que la référence automobile, sans remplacement des expositions ou estimations historiques.

Les150 checkpoints TP ont aussi été vérifiés. L'audit a repéré des colonnes de marche documentée perdues lors de l'agrégation finale : restaurées depuis les preuves existantes via `src/run_accessibility_reference_time_revision.py --review-only`, sans recalculer les trajets, inventer un retour ou appliquer ces marches à l'hiver.
