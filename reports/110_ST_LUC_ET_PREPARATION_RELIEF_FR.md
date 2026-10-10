# St-Luc–Chandolin et préparation du relief

10 octobre 2026. Suite de la règle des tronçons uniques et des deux décisions supplémentaires validées par le chercheur.

## Un périmètre supplémentaire raccordé

**41 correspondances vérifiées sur 70 groupes**, contre 40 auparavant. Les 29 périmètres encore non résolus restent présents. St-Luc–Chandolin apporte 81 objets OSM de descente : **854 objets conservés**, dont 846 axes candidats et 8 surfaces. Ce ne sont pas des nombres de pistes réelles ou des périmètres exhaustifs.

Le [tarif hivernal officiel](https://www.valdanniviers.ch/fr/Z33284/tarifs-luge-pieton-ski-de-randonnee), archivé avec empreinte, nomme les chaînes d’accès Tsapé–Rotzé–Pas-de-bœuf–Bella-Tola et Forêt–Pas-de-bœuf–Bella-Tola. Elles corroborent les installations originales, avec la fiche d’opérateur officielle déjà conservée et le contrôle visuel de la carte OSM. Pas de rapprochement automatique par nom ou rayon. Le plan estival précédent n’est pas transformé en preuve hivernale ; les tarifs du moteur de recherche, différents de l’original actuel, ne sont pas repris comme données.

Les 69 autres lignes de correspondance et leurs diagnostics restent identiques. Les remontées, événements, accès routiers et nuitées communales ne sont ni modifiés ni dupliqués. Le funiculaire mentionné officiellement n’est pas inventé dans les membres OSM de type remontée aérienne. Trois références de nœuds non complétées restent signalées. La preuve actuelle ne certifie pas les tracés préentrée ou chaque objet individuellement.

[Correspondances actualisées](../data_processed/winter_profile_piste_assignment_stage60.csv) · [854 objets et leurs alertes](../data_processed/winter_profile_verified_piste_member_qa_stage60.csv).

## Calcul du relief : décisions enregistrées

Les réponses exactes figurent dans `config/terrain_extraction_decisions_stage61.json` :

- Relief **swissALTI3D 2 m** ; axes uniques découpés selon les cellules, poids égal à la longueur réellement présente dans chaque cellule, sans pas d’échantillonnage arbitraire.
- Pente et exposition du terrain par **Horn, voisinage 3 × 3**, sans interpolation des cellules manquantes. L’azimut décrit la pente descendante du terrain, pas le sens du tracé.
- Orientation indéfinie seulement à **pente exactement nulle**. Les portions plates restent dans les longueurs et l’altitude ; pas de seuil supplémentaire à 1°.
- Couverture et longueurs manquantes publiées ; pas d’exclusion automatique d’un groupe.

Le module de calcul est préparé et testé sur des cas artificiels explicitement identifiés comme tests, pas comme données recueillies : quatre orientations cardinales, terrain plat, voisin manquant, petite pente non nulle, longueur par cellule, frontières et inversion d’un tracé. Une portion exactement sur une frontière reçoit un seul propriétaire selon l’indexation native ligne/colonne du raster, sans déplacer ses coordonnées. Les premiers tests d’égalité bit à bit des longueurs ont échoué sur des résidus flottants ; comparaisons numériques corrigées à précision machine, sans ajouter de tolérance géographique.

La documentation [gdaldem](https://gdal.org/en/stable/programs/gdaldem.html) et [gdal raster aspect](https://gdal.org/en/stable/programs/gdal_raster_aspect.html) est archivée. Point technique important : la nouvelle commande peut interpoler par défaut aux bords ; le futur lecteur utilisera explicitement le comportement sans interpolation validé. Des cellules voisines observées dans les tuiles adjacentes ne constituent pas une interpolation.

## Catalogue et conditions d’utilisation

Un pilote borné autour de St-Luc–Chandolin conserve **84 entrées GeoTIFF 2 m** : éditions de référence 2019 et 2024. Cinquante entrées, soit **25 emprises de tuiles dans chacune des deux éditions**, intersectent directement les axes. Les autres entrées de la boîte englobante restent dans l’inventaire. Pagination complète, adresses d’actifs littérales, résolution/CRS et empreintes SHA-256 fournisseur contrôlés. Aucun raster téléchargé ou millésime choisi à cette étape.

Le catalogue contient littéralement `license=proprietary` : cette mention est conservée. Les [conditions OGD de swisstopo](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata-and-geoservices), liées depuis la documentation du produit et archivées séparément, autorisent usage et transformation avec attribution obligatoire. L’attribution prévue est « Office fédéral de topographie swisstopo ». Pas de licence ouverte spécifique inventée, de contournement ou de collecte excessive.

Les dates de référence d’édition, de création et de mise à jour des actifs restent distinctes ; aucune ne devient automatiquement une date réelle d’acquisition du relief. Même l’édition 2019 n’est pas préentrée pour St-Luc, entré en 2017. **Le choix du millésime de référence a été soumis au chercheur** : plus récent disponible avec réserve historique et comparaison pilote, ou comparaison des deux avant choix. Aucun choix supplémentaire n’est appliqué en son absence.

[Inventaire complet des actifs du pilote](../data_processed/terrain_stluc_native2m_asset_inventory_stage61.csv).

## Sources, contrôles et reprise

Six nouvelles pages/JSON originaux archivés en deux collectes bornées, tous HTTP 200 : tarif de St-Luc, deux documentations GDAL, collection swissALTI3D, requête du pilote et conditions d’utilisation. Les quatre recherches de découverte et identifiants de requête restent séparés des preuves primaires. Chaque source et chaque variable CSV sont inscrites dans les registres ; les anciens résultats et originaux restent intacts.

Lecteur GeoTIFF installé seulement dans `.venv` ; versions figées dans `config/terrain_runtime_requirements_stage61.txt` et le manifeste. La méthode ne dépend pas d’un Python système modifié.

Contrôle final : **315 tests réussis**, un avertissement antérieur conservé ; 863 références SHA sur 459 fichiers vérifiées. Toutes les anciennes lignes des sources, du dictionnaire et des 982 événements de collecte sont identiques. Six événements ajoutés, sans doublon. Reprise des deux consommateurs sur cache vérifiée sans nouvelle requête.

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/verify_piste_terrain_sources_stage60.py
.venv/Scripts/python.exe -X utf8 src/descriptive/audit_terrain_catalogue_stage61.py
.venv/Scripts/python.exe -X utf8 -m pytest tests/test_terrain_cells_stage61.py tests/test_terrain_catalogue_stage61.py -q
```

Ces commandes réutilisent les caches, sans requête réseau ni changement des anciens fichiers. Les manifestes `piste_terrain_sources_stage60_summary.json` et `terrain_catalogue_stage61_summary.json` fixent les entrées/sorties. Suite : décision sur les millésimes, collecte bornée et reprenable des tuiles avec contrôle fournisseur, extraction diagnostique puis extension aux autres périmètres vérifiés ; les 29 cas non résolus et réserves historiques restent suivis. Aucun nouveau clustering, raccordement des modèles neige ou effet DiD estimé.
