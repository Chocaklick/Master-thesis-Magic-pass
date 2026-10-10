# Relief et exposition : extension aux groupes disposant de pistes

10 octobre 2026. Les **70 groupes et 185 territoires communaux restent conservés**. Aucun nouveau clustering, effet DiD ou filtre communal. Les résultats précédents, y compris le pilote St-Luc 2019/2024, restent intacts.

## Résultat

L’altitude, la pente et les deux composantes d’exposition sont maintenant disponibles pour **40 groupes**, contre un auparavant : **39 références de terrain supplémentaires**, pas 39 nouvelles stations ou communes intégrées. Il s’agit de profils de **tracés OSM candidats documentés**, pas d’une certification des domaines exhaustifs ou préentrée.

- 34 groupes : tous les voisinages nécessaires à la pente sont observés et d’une même édition.
- 6 groupes : pente et orientation calculées sur les portions observées après la décision ci-dessous ; couverture publiée.
- 29 groupes : rattachement des pistes encore non résolu ; groupe conservé, profil manquant.
- Sainte-Croix–Les Rasses : correspondance du site vérifiée, mais absence d’axes de descente référencés ; profil manquant, pas zéro.

[Table actuelle — 70 groupes](../data_processed/terrain_reference_profiles_stage67.csv) · [Audit précédent conservé](../data_processed/terrain_native2m_reference_audit_stage66.csv) · [Couverture du catalogue](../data_processed/terrain_group_catalogue_coverage_stage65.csv).

## Méthode et décision sur les jonctions

Catalogue officiel swisstopo : 40 pages nouvelles archivées pour les 39 autres groupes, y compris la pagination de Crans. Le catalogue St-Luc existant est réutilisé. Sélection de l’édition la plus récente **par tuile native**, conformément à ta validation : 499 fichiers de référence vérifiés, dont 42 déjà conservés et **457 nouveaux téléchargements réussis**. Les autres éditions repérées restent inventoriées, mais ne sont pas toutes téléchargées.

Les 331 391 cellules traversées par 523,606 km d’axes uniques portent leur longueur exacte, altitude centrale, sources et dates. Grille native 2 m/LV95, pente et orientation Horn sur neuf cellules observées ; aucune interpolation, déplacement de tracé ou tolérance de rapprochement. Les altitudes centrales et les neuf valeurs voisines sont disponibles sur toute cette longueur.

Six groupes traversent une jonction entre éditions. Un saut du modèle pourrait y produire une pente artificielle ; des altitudes centrales disponibles ne garantissent donc pas un gradient comparable.

| Groupe | Éditions sur les axes | Longueur au voisinage d’une jonction | Part des axes |
|---|---|---:|---:|
| Crans-Montana | 2024/2025 | 4,06 m | 0,006 % |
| Lauchernalp–Lötschental | 2024/2025 | 14,66 m | 0,119 % |
| Bugnenets–Savagnières | 2021/2025 | 35,90 m | 0,229 % |
| Marbachegg | 2022/2025 | 27,96 m | 0,400 % |
| Melchsee-Frutt | 2022/2025 | 42,27 m | 0,133 % |
| Sörenberg | 2022/2025 | 7,48 m | 0,047 % |

**Décision reçue et appliquée en Stage67 :** « Laisser pente et orientation manquantes sur ces seules portions, puis résumer les portions observées du groupe ». Les 132,33 m concernés gardent leur altitude et leur longueur. Aucun groupe n’est supprimé et aucun gradient n’est ajusté. L’audit Stage66 conserve son ancien statut d’attente ; le fichier Stage67 est la référence actualisée.

Pente moyenne : pondération sur la longueur avec gradient observé. Exposition : cosinus nord/sud et sinus est/ouest sur la longueur non plate avec angle observé. Pente exactement nulle : altitude et longueur conservées, orientation indéfinie. Concentration et quatre parts cardinales restent **descriptives uniquement**. Longueurs plates, gradients manquants et couvertures sont distingués.

## Sources, réserves et contrôle

Source du relief : **Office fédéral de topographie swisstopo**, [catalogue officiel swissALTI3D](https://data.geo.admin.ch/api/stac/v1/collections/ch.swisstopo.swissalti3d). Chaque URL de tuile, date d’édition et SHA256 fournisseur est archivé ; les éditions ne sont pas assimilées à des dates d’acquisition. Tracés : instantanés OpenStreetMap antérieurs conservés, attribution/ODbL ; règles et preuves de rattachement inchangées. Conditions OGD et attribution swisstopo déjà vérifiées en Stage61. Ces données actuelles restent des **proxies à validité historique réservée**, pas des mesures prétraitement certifiées.

1 196 sources et 8 084 champs de dictionnaire uniques. Toutes les anciennes lignes de registres sont préservées, ainsi que les 1 072 anciens événements de collecte ; 497 nouveaux événements réussis exactement. Contrôle de préservation : **2 206 références SHA sur 1 694 fichiers**. **349 tests passent**, avec un avertissement préexistant. Reprise sur cache vérifiée sans requête ou ligne de registre supplémentaire. Les CSV cellulaires détaillés restent en cache local `data_interim/`, avec angles et empreintes ; les originaux/cache/environnement ne sont pas ajoutés à Git.

Deux descriptions héritées du pilote dans le nouveau dictionnaire Stage65 ont été corrigées avant sauvegarde : identifiant de groupe et sélection du millésime. Ancien/nouveau libellés documentés ; aucune valeur scientifique ni ancienne ligne modifiée. Les erreurs initiales de syntaxe/appel Python ont été corrigées avant les sorties concernées, sans nouveau téléchargement ni modification de méthode.

## Reprise et suite

Depuis la racine, sans nouvelle requête :

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/summarise_terrain_reference_stage67.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_piste_preservation_stage67.py
```

Les empreintes doivent correspondre ; ne pas modifier les producteurs figés ni relancer un ancien contrôle de registre avec ses comptes historiques. Décision exacte : `config/terrain_seam_decision_stage67.json`. Métadonnées et méthodes : les deux registres, les résumés Stage65/66/67, `PROJECT_STATE.md` et le journal.

Suite autorisée : audit de compatibilité et préparation de la comparaison neige SPASS–OSHD, recherche des rattachements encore manquants. **Aucun raccordement neige automatique**, aucune fenêtre de cinq hivers changée. Standardisation, catégories/clustering et identification des effets restent des choix distincts à valider avant estimation.
