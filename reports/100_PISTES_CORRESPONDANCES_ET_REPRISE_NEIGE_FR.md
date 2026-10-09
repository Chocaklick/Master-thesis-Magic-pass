# Pistes : correspondances et reprise de la neige

9 octobre 2026. Suite des [règles validées](99_REPRISE_COLLECTE_OSHD_ET_REGLES_VALIDEES_FR.md). Les **71 groupes et 185 territoires communaux restent conservés**, ainsi que les anciens résultats ; aucune nouvelle classification ou estimation.

## Travail réalisé

| Travail | Résultat | Limite |
|---|---|---|
| Correspondances groupes ↔ relations OSM | 71 × 238, soit 16 898 couples conservés sans filtre de distance | Une relation OSM n’est pas un groupe du mémoire |
| Noms originaux et géométrie | 33 groupes ont une correspondance exacte de nom ; 32 ont aussi cette relation parmi les plus proches dans l’extraction initiale | Nom et proximité ne valident pas seuls un périmètre |
| Complément des membres référencés | 2 751 ways et 75 relations demandés, tous retournés ; original de 5,9 Mo archivé | Collecte complète des identifiants demandés ≠ carte complète des stations |
| Membership des relations | 5 173 ways alpins uniques référencés, contre 4 729 initialement ; six relations enrichies | Un way n’est pas nécessairement une piste entière ; domaines transfrontaliers non automatiquement assignés |
| Vérifications officielles ciblées | Deux pages Magic Pass archivées pour Sainte-Croix et la Vallée de Joux | Descriptions actuelles, pas périmètres préentrée certifiés |

**Aucun rattachement géographique final accepté**, aucun groupe écarté. Fichiers simples : [correspondances des 71 groupes](../data_processed/winter_profile_piste_group_review.csv) et [audit des 238 relations](../data_processed/winter_profile_piste_site_membership_audit.csv).

## Deux problèmes de périmètre documentés

**Sainte-Croix–Les Rasses.** La relation OSM 2899124 référence 22 ways nordiques et sept remontées, mais aucun way alpin. La [page officielle](https://www.magicpass.ch/fr/stations/ste-croix-les-rasses-2772) distingue pourtant un domaine alpin sur les versants du Chasseron et un réseau nordique. Il s’agit d’un membership incomplet pour notre besoin, **pas d’une absence de ski alpin**. La relation proche avec descentes référencées est Mauborget : elle ne doit pas remplacer Sainte-Croix par proximité.

**Vallée de Joux.** La relation 9374152 correspond à L’Abbaye, avec neuf ways alpins et quatre remontées. La [description officielle](https://www.magicpass.ch/fr/stations/vallee-de-joux-87) comprend aussi L’Orient et Le Brassus. L’Abbaye seule ne peut représenter le groupe déjà retenu. Le point de référence existant est à environ 7,10 km des géométries alpines référencées de L’Abbaye ; cette distance sert au contrôle, pas à une exclusion ou à un nouveau seuil d’exposition.

Dans tout l’inventaire, 32 relations n’ont aucun way alpin référencé ; 15 gardent des membres way/relation non résolus après exploration récursive. Ce ne sont **ni 32 stations sans ski, ni 15 groupes à retirer**. Certaines relations sont nordiques ou partielles. Les pistes nouvellement identifiées concernent notamment des domaines transfrontaliers : aucune fusion avec nos groupes n’en découle.

## Méthode et sources

- Identifiants des groupes, composantes et accès conservés. Noms complets normalisés uniquement ; aucun alias inventé ou rapprochement flou automatiquement accepté.
- Relations parcourues récursivement ; ways dédoublonnés par identifiant OSM ; références partagées, cycles et membres non résolus signalés. Une référence hors de la première requête n’est pas une donnée nécessairement absente d’OSM.
- Distance minimale en ligne droite dans EPSG:2056, depuis les **points de référence de station existants** vers les géométries référencées. Ni temps routier, ni nouveau point mairie/parking ; aucun rayon de sélection.
- Complément fini pour tous les ways/relations référencés hors de la sélection initiale. Réponses originales séparées : instantanés OSM à 16:21:05 et 17:24:05 UTC. Aucun identifiant/version commun écrasé ou original modifié. Les nodes ne sont pas demandés pour cet audit des tracés.
- Tracés actuels = proxies autorisés avec réserve historique. Date d’édition OSM ≠ construction. Les surfaces fermées ne deviennent pas arbitrairement des axes. Pas encore de calcul d’altitude, orientation ou neige.

Sources : contributeurs [OpenStreetMap](https://wiki.openstreetmap.org/wiki/Tag:site=piste), réponses Overpass originales, descriptions officielles ci-dessus. Attribution ODbL conservée pour OSM ; aucune licence ouverte supposée pour les pages commerciales. Les consignes scientifiques des tableaux ont servi à séparer données originales, candidates et validations.

## Neige : progression réelle, archive encore partielle

WY2024 passe de **216 006 656 à 484 411 044 octets sur 645 601 691**, soit environ **75 %**. WY2025 et WY2023 restent sans archive complète. **0 ZIP complet sur 3**, aucune valeur de neige extraite ou moyenne calculée.

Le lien canonique Zenodo a encore retourné 504 après trois blocs supplémentaires. Le collecteur peut désormais utiliser **l’ancre réelle `?download=1` du HTML public archivé**, sans URL API interdite ou paramètre inventé. Même archive, mêmes taille et MD5, contrôles HTTP206 exacts, délai robots et verrou conservés. Ce lien a permis de progresser, puis une réponse s’est terminée avant la fin de sa plage : erreur `Incomplete range`, préfixe reçu conservé. Pas de boucle de relance après échec. Aucun collecteur encore actif à la clôture.

Le fichier partiel n’est pas une source originale validée. La [source SLF](https://zenodo.org/records/17313889) demeure un complément à auditer, pas un remplacement validé. État détaillé : `reports/oshd_profile_audit_collection_summary.json`. Les anciennes tentatives restent dans le journal ; aucun octet déjà reçu n’est téléchargé de nouveau.

## Reprise et suite

Depuis la racine, étapes terminées avec checkpoints sans requête ni réécriture :

```powershell
.venv/Scripts/python.exe src/descriptive/prepare_piste_group_review.py
.venv/Scripts/python.exe src/data_collection/collect_piste_member_tags.py
.venv/Scripts/python.exe src/descriptive/audit_completed_piste_membership.py
```

Pour poursuivre la neige après examen d’une interruption non liée aux permissions :

```powershell
.venv/Scripts/python.exe src/data_collection/collect_oshd_profile_audit.py --resume-failed --official-download-anchor --max-seconds 300
```

Un seul collecteur ; une erreur 401/403 n’autorise pas une relance. ZIP promu seulement après taille, MD5 et SHA256 exacts. Originaux et anciens résultats préservés.

**Suite concrète :** compléter les pistes/composantes avec les opérateurs et plans, vérifier les changements historiques documentés ; terminer les archives utiles et inspecter variables, unités et grille. Avant les profils, te présenter les choix ouverts : résolution du relief, terrain plat, pistes uniquement en surface, protocole de comparaison des modèles. Aucun de ces choix n’est tranché ici.

Validation : **244 tests réussis**, un avertissement préexistant. **388 sources uniques et 7 408 champs de dictionnaire**, dont 27 nouveaux champs de diagnostic. Anciennes lignes de provenance conservées hors statuts des six enregistrements de collecte OSHD ; SHA des anciens résultats contrôlés. Sources, méthodes et reprise consignées dans les registres, `PROJECT_STATE.md` et le journal.
