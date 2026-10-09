# Neige : première archive complète et contrôle des grilles

9 octobre 2026 — suite du [bilan précédent](100_PISTES_CORRESPONDANCES_ET_REPRISE_NEIGE_FR.md). Les **71 groupes de stations et 185 territoires communaux restent inchangés**. Anciens résultats, regroupements et seuils routiers conservés ; aucun nouveau profil, clustering ou DiD estimé.

## 1. Collecte : ce qui est réellement disponible

| Archive OSHD | État à la clôture | Utilisable pour le contrôle du contenu ? |
|---|---|---|
| WY2024 : septembre 2023–août 2024 | **Complète : 645 601 691 octets**, taille et MD5 fournisseur validés, SHA256 archivé | Oui : les 12 fichiers mensuels sont vérifiés |
| WY2025 : année hydrologique suivante | **198 180 864 / 579 028 796 octets**, environ 34 % ; pause de durée prévue | Non : fichier partiel conservé pour reprise |
| WY2023 : année hydrologique précédente | Aucun octet conservé ; ancien échec HTTP504 | Non : prochaine reprise explicitement autorisée, pas de relance en boucle |

La reprise n’a pas téléchargé de nouveau les 484 Mo déjà reçus de WY2024. Un seul collecteur a fonctionné, avec plages HTTP206 vérifiées et délai robots. **Aucun collecteur encore actif.** Le compteur de fichiers complets a été corrigé : une pause anticipée le laissait auparavant à zéro malgré la réussite de WY2024. Il affiche maintenant **1 sur 3**. Les anciens messages d’erreur restent historiques ; ils ne remplacent pas les statuts actuels `complete` et `paused`.

Original : [jeu OSHD du SLF](https://zenodo.org/records/17313889), licence CC-BY4.0. ZIP original immuable ; membres NetCDF décompressés séparément dans `data_interim/oshd_metadata_members/`, avec contrôle CRC et SHA256. **Les champs d’enneigement n’ont pas été lus ni agrégés** : seules les métadonnées et les coordonnées sont examinées.

## 2. Pourquoi le contrôle des grilles était nécessaire

| Point | SPASS déjà conservé | OSHD WY2024 vérifié |
|---|---|---|
| Résolution des axes | 1 000 m | 250 m |
| Ordre du champ de neige | `time, N, E` | `easting, northing, time` |
| Axe nord–sud | Croissant | Décroissant |
| Hauteur de neige | `HSCLQMD`, unité absente des attributs | `hs`, attribut **`unit = m`** |
| Période contrôlée | 1 septembre 1961–31 août 2023 | 1 septembre 2023–31 août 2024, **366 dates quotidiennes** |

Comparer directement les indices des tableaux donnerait donc de faux rapprochements spatiaux. Les coordonnées originales LV95 sont conservées, ainsi que les dimensions, attributs, valeurs de remplissage et calendriers. Les heures décodées restent accompagnées des unités temporelles originales ; leur interprétation de fuseau n’est pas indépendamment validée.

OSHD fournit aussi `swe` (équivalent en eau, kg/m²), `scf` (fraction de couverture neigeuse, sans unité) et `smro` (flux journalier de fonte, kg/m²/jour). Ces variables sont **inventoriées, pas sélectionnées comme caractéristiques**. Le lecteur tient compte de l’attribut singulier `unit`, faute de quoi leurs unités seraient perdues.

Le NetCDF SPASS de 8,88 Go a été contrôlé à nouveau par SHA256. Son unité manquante reste `UNKNOWN` dans le dictionnaire du schéma original ; l’interprétation antérieure en mètres reste séparément documentée, sans être transformée en attribut fournisseur. **WY2024 ne chevauche pas SPASS** : sa complétude ne suffit pas à comparer les modèles. WY2023 est nécessaire pour une première période commune. Ni raccordement, ni calibration, ni substitution de modèle n’a été appliqué.

Fichiers de contrôle : [métadonnées OSHD](oshd_netcdf_metadata_inventory.json) et [compatibilité des schémas](snow_grid_metadata_compatibility_stage47.json). Les données climatiques rétrospectives ne certifient pas à elles seules un profil observable historiquement au moment de l’entrée.

## 3. Pistes : vérifications officielles poursuivies

Trois pages publiques ont été archivées, vérifiées et enregistrées, avec leurs liens réellement présents — pas d’URL de plan inventée.

- **Sainte-Croix–Les Rasses** : [site de l’opérateur](https://www.ski-vaud.ch/web/), relié par la page Magic Pass déjà archivée. Le lien vers [Les Pistes](https://www.ski-vaud.ch/web/ski/les-pistes) est conservé pour la suite. Cela ne fournit pas encore des axes géographiques vérifiés et ne résout pas automatiquement le membership OSM alpin incomplet.
- **Vallée de Joux** : la [page touristique officielle](https://www.myvalleedejoux.ch/fr/Z10411/ski-alpin) confirme les trois composantes L’Abbaye, Le Brassus et L’Orient et donne un lien vers leur [plan des pistes](https://static.mycity.travel/manage/uploads/6/26/452439/1/plan-des-pistes-de-ski-alpin.pdf). Ce PDF est **repéré, mais pas encore collecté ni interprété**. Une offre régionale plus large dans l’ancienne source de 2022 mentionne aussi Vaulion : cela ne justifie pas de l’ajouter au groupe Magic Pass retenu.
- **Relief** : [documentation swissALTI3D](https://www.swisstopo.admin.ch/en/height-model-swissalti3d) archivée. Elle distingue 0,5 m et 2 m ; 0,5 m peut être suréchantillonné et représente environ 26 Mo par tuile, contre 1 Mo à 2 m. La résolution n’est pas encore choisie et aucune tuile n’a été collectée.

Les descriptions et chiffres actuels ne deviennent pas des caractéristiques préentrée. Navigation complète, sources, empreintes et réserves sont conservées dans [l’inventaire des preuves opérateurs](piste_operator_evidence_stage47_summary.json). **Aucune affectation GIS validée, aucune fusion ni exclusion.** Les consignes scientifiques des tableaux ont servi à distinguer les schémas originaux, leur provenance et les transformations dérivées.

## 4. Choix en attente et prochaine reprise

Deux questions ont été soumises, sans présumer ta réponse : **relief à 2 m**, ou comparaison préalable avec 0,5 m ; **pistes seulement en surface laissées en attente**, ou recherche d’un axe documenté avant leur utilisation. Terrain plat, extraction spatiale commune et éventuel raccordement neige restent à définir ensuite. Aucun seuil de couverture ni suppression de groupe n’a été décidé.

Reprise depuis la racine :

```powershell
# État seul, aucune requête
.venv/Scripts/python.exe src/data_collection/collect_oshd_profile_audit.py --checkpoint-only
# Poursuivre les archives incomplètes ; anciens HTTP504 réexaminés, jamais 401/403
.venv/Scripts/python.exe src/data_collection/collect_oshd_profile_audit.py --resume-failed --official-download-anchor --max-seconds 300
```

**Après arrêt du collecteur**, pour éviter des écritures concurrentes dans les registres :

```powershell
.venv/Scripts/python.exe src/descriptive/inspect_oshd_netcdf_metadata.py
.venv/Scripts/python.exe src/descriptive/audit_snow_grid_metadata_compatibility.py
.venv/Scripts/python.exe src/descriptive/register_piste_operator_evidence_stage47.py
```

L’inspection peut aussi utiliser `--no-register` pendant une collecte : elle n’inspecte que les ZIP complets et n’écrit aucun CSV partagé. La prochaine étape concrète reste **terminer WY2025/WY2023 et vérifier les plans et composantes**, puis soumettre le protocole de comparaison neige avant de calculer les profils pondérés par longueur et cinq hivers propres à chaque entrée.

Registres : **393 sources uniques, 7 422 champs de dictionnaire**, dont 14 champs de schémas originaux ajoutés. Anciennes lignes conservées hors état des sources OSHD en cours ; **373 contrôles SHA sur 126 fichiers protégés** réussis. **250 tests réussis**, un avertissement préexistant. Commit de clôture consigné dans le journal de recherche ; sources originales et modifications éditoriales héritées exclues du commit technique.
