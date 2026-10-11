# Géométries revues et couvertures des sources — 12 octobre 2026

## Résultat et dernière décision

Les **69 groupes et 185 territoires communaux restent conservés**. Les 71 identités originales, les regroupements validés et les anciens résultats ne sont pas modifiés. Sur les 67 groupes avec tracés rattachés, les réseaux mesurables sont préparés ; cela ne signifie pas que 67 nouveaux profils de neige et de relief sont déjà calculés.

**La recherche IGN est arrêtée à la demande du chercheur. Aucun relief français ne sera ajouté.** La Dôle–Tuffes reste un seul groupe, ses géométries originales transfrontalières restent archivées. Le futur profil de relief reposera uniquement sur les données suisses disponibles et sera explicitement partiel. Pas de découpage automatique des pistes à la frontière, pas de valeur inventée pour la partie non couverte. Cette décision concerne le complément de relief, pas une exclusion de communes ou un nouveau regroupement.

## 1. Contrôle individuel des portions ambiguës

37 objets ont une revue individuelle : 28 axes restent non mesurés faute de preuve suffisante, six anciens noms de La Dôle ne sont **pas** assimilés à des pistes abandonnées, deux notes ne concernent pas la précision géométrique et une surface TVGD est résolue avec son trou d'origine. Les 2 001 objets originaux restent conservés. Les surfaces servent à mesurer une superficie cartographiée, jamais à inventer des axes.

La disponibilité pour mesurer les axes est partielle pour cinq groupes :

| Groupe | Part mesurable des axes cartographiés uniques |
|---|---:|
| Arolla | 83,4 % |
| Evolène | 69,4 % |
| Gstaad | 96,1 % |
| La Dôle–Tuffes | 97,3 % |
| Moosalp | 93,9 % |

Ces parts ont pour dénominateur les **tracés OSM rattachés**, pas une longueur officielle certifiée du domaine. Leur complétude réelle et leur validité avant entrée restent incertaines. La Braye et Riffenmatt restent sans géométrie mesurable : manque explicite, pas zéro et pas exclusion.

Méthode inchangée : union des axes exactement superposés, sans rapprochement ni déplacement ; portions ambiguës conservées séparément. Une difficulté numérique de superposition a été résolue en vérifiant les axes originaux identiques et en soustrayant les longueurs des deux unions, sans introduire de tolérance géographique.

Fichiers : [revues individuelles](../data_processed/piste_individual_review_stage80.csv), [réseaux et couvertures](../data_processed/winter_profile_metric_network_stage80.csv). Configuration des décisions : `config/piste_individual_review_stage80.json` ; règles : `config/piste_metric_decisions_stage80.json`.

## 2. Relief suisse à 2 m : disponibilité, pas encore nouvelles altitudes

Les 40 catalogues terminés sont réutilisés et les 27 nouveaux domaines ont été interrogés : 35 pages officielles archivées. Les éditions, dates et sommes de contrôle sont conservées ; la sélection demeure le millésime le plus récent par tuile native, conformément à la validation antérieure.

Pour La Dôle–Tuffes, les empreintes des tuiles suisses couvrent **65,8 % du réseau mesurable**. Ce chiffre n'est pas une certification des valeurs finies ni des voisinages de neuf cellules nécessaires à Horn : ces contrôles auront lieu à la lecture du relief. La part mesurable des pistes (97,3 %) et la couverture du catalogue (65,8 %) répondent donc à deux questions différentes.

L'inventaire contient 1 274 URL distinctes de dernières éditions sur toutes les emprises interrogées, dont 499 originaux déjà archivés et vérifiés. Parmi les 635 tuiles intersectant les axes, 326 sont déjà présentes et 309 non récoltées. Le besoin final devra aussi tenir compte des cellules voisines pour Horn. Le champ ancien indiquant 45 caches est une photographie antérieure, **pas** l'état actuel : ne pas télécharger de nouveau les 499 originaux vérifiés.

Fichiers : [couverture du catalogue](../data_processed/terrain_reviewed_catalogue_coverage_stage80.csv), [éditions et liens originaux](../data_processed/terrain_reviewed_asset_inventory_stage80.csv). Attribution : Office fédéral de topographie swisstopo. Aucun raster français ni nouveau relief final n'a été incorporé.

## 3. Neige : poids natifs prêts, diagnostic de masque séparé

Les longueurs exactes du réseau mesurable ont été allouées aux cellules natives SPASS à 1 km pour les 67 groupes documentés ; les deux groupes sans tracés restent dans la table. Les 639 cellules sources sélectionnées et leurs valeurs originales du **1er avril 2023** sont conservées pour un contrôle de couverture. Ce jour de l'ancien hiver pilote n'est jamais utilisé comme caractéristique préentrée ni comme moyenne hivernale.

Ce jour-là, des valeurs sources manquent sur une partie des réseaux de La Dôle–Tuffes (couverture 65,8 %), Melchsee-Frutt (86,4 %) et Vallée de Joux (94,3 %). Ces constats ne certifient pas les autres dates. Les vrais zéros restent observés ; les valeurs masquées restent manquantes. Aucun complément OSHD, interpolation, conversion ou raccordement n'est appliqué. L'hypothèse « mètres » validée reste distincte de la déclaration originale `UNKNOWN`.

Les futurs profils garderont les **cinq hivers propres à chaque entrée**, décembre–avril, pondération par longueur puis poids égal des hivers. Un hiver entièrement absent laissera la moyenne des cinq manquante. Les anciens 40 profils de relief et 34 moyennes SPASS complètes restent inchangés.

Fichiers : [poids SPASS](../data_processed/spass_native_weights_stage80.csv), [couverture du jour diagnostic](../data_processed/spass_coverage_check_stage80.csv), [cellules originales sélectionnées](../data_processed/spass_coverage_source_cells_stage80.csv).

## Sources, contrôles et reprise exacte

Les preuves opérateurs et géométries OSM des étapes précédentes sont réutilisées, avec versions et identifiants. Les définitions OSM distinguent [ancien nom](https://wiki.openstreetmap.org/wiki/Key%3Aname%3Awas) et [mention d'abandon](https://wiki.openstreetmap.org/wiki/Tag%3Aabandoned%3Dyes) ; elles ne prouvent pas une date de fermeture.

Les tentatives IGN déjà effectuées sont conservées au registre et au journal, y compris les échecs et les deux réponses HTTP 200 qui sont des redirections HTML, **pas** des PDF consultés. Les [métadonnées officielles IGN](https://www.data.gouv.fr/datasets/mnt-lidar-hd) et la licence ont été archivées, mais l'audit n'est pas achevé et aucun jeu français n'est intégré. **Ne pas reprendre cette recherche sans nouvelle demande.**

**76 tests combinés réussis** (51,11 s), dont 17 ciblés de cette étape. Audit de préservation terminé : 2 189 fichiers contrôlés, dont les 2 065 protégés à l'étape précédente, tous inchangés ; préfixes des registres exacts. Les manifestes `reviewed_*stage80_summary.json` figent les configurations, producteurs, sources et sorties. Le complément `reviewed_geometry_followup_stage80_summary.json` donne l'état vérifié des caches ; `preservation_stage80_summary.json` contrôle les originaux, anciens résultats et préfixes des registres.

Reprise : récolter seulement les tuiles suisses nécessaires encore absentes avec les voisinages Horn, puis calculer les nouveaux profils versionnés de relief et les cinq hivers SPASS sur les réseaux revus. Réutiliser les caches existants sans modifier leurs dimensions ni leurs sources. Garder toutes les couvertures ; ne pas assimiler les 67 réseaux préparés à 67 profils complets. Aucun nouveau DiD ou clustering n'est lancé ici.
