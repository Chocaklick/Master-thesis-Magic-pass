# Eischoll–Unterbäch : regroupement validé

10 octobre 2026. Le chercheur valide un groupe commun avec réserve historique explicite, conservation des identifiants et des anciens résultats, minimum des accès existants et aucune duplication des nuitées.

## Ce qui change

La nouvelle version contient **70 groupes, contre 71 auparavant**. Les 71 identifiants originaux sont conservés dans une table de filiation ; il ne s’agit pas d’une station ou commune exclue. Le nouveau groupe dérivé `MP_GROUP_CONNECTED__eischoll_unterbaech` contient Eischoll et Unterbäch, entrées toutes deux en mai 2023. Les deux événements et deux départs restent identifiés. Les 69 autres groupes conservent exactement leurs attributs antérieurs ; les 242 clusters de remontées ne sont pas reconstruits.

Les 75 points d’accès et 13 875 couples routiers existants sont réutilisés. Aucun appel routier, déplacement de point ni modification des temps sources. Le temps du groupe est le minimum des moyennes aller/retour utilisables des deux accès, conformément à la règle déjà validée. Les origines et raccordements au réseau restent ceux de la collecte précédente.

La relation OSM actuelle 9142700 couvre le domaine commun : 63 objets de descente et 6 remontées identifiées dans les originaux. Elle est comptée une fois. Bilan : **40 correspondances vérifiées sur 70, 30 non résolues conservées**, 773 objets de descente rattachés, et non 773 pistes ou kilomètres. Ni l’exhaustivité réelle, ni chaque objet, ni les géométries préentrée ne sont certifiés.

## Vérification communale

| Seuil automobile | Communes où deux groupes deviennent un | Première exposition, nuitées, accès le plus proche |
| --- | ---: | --- |
| 15 min | 1 | Inchangés |
| 30 min, référence principale | 2 | Inchangés |
| 45 min | 3 | Inchangés |

Les 185 territoires restent présents. Dans chaque spécification, il existe toujours une seule ligne par commune et mois : 31 080 lignes de calendrier, **pas nécessairement autant de nuitées observées**. Le fichier réunit les trois seuils uniquement pour comparaison, pas comme observations indépendantes d’une même estimation. La première exposition et son statut sont inchangés ; les nombres de groupes actifs et d’entrées simultanées diminuent d’un là où les deux composantes étaient accessibles. Aucun effet DiD n’est réestimé à cette étape.

## Réserves conservées

- Liaison préentrée corroborée par un récit publié et modifié en 2022, plus confirmation officielle actuelle ; aucun plan officiel préentrée retrouvé ni version indépendante figée du récit. Les [preuves et limites](107_AUDIT_OBJETS_PISTES_ET_LIAISON_HISTORIQUE_FR.md) restent explicites.
- Les sommes de catalogue donnent 35 km et 10 remontées à partir des deux fiches distinctes. **Le nombre 10 n’est pas un compte physique validé** : la source officielle actuelle parle de 7 installations et OSM en référence 6. Différences de périmètre, types et dates à vérifier ; aucune valeur n’est remplacée arbitrairement et ces comptes ne sont pas validés pour le clustering.
- La connexion hivernale ne prouve pas une offre estivale commune. Les historiques d’offre par composante restent séparés pour la future analyse d’été.
- L’hiver principal reste décembre–avril ; aucune nouvelle catégorie de profil, estimation, imputation ou exclusion.

## Fichiers et reprise

[Filiation des 71 identifiants](../data_processed/station_group_lineage_stage55.csv) · [70 groupes dérivés](../data_processed/accessibility_station_groups_stage55.csv) · [Expositions routières, trois seuils](../data_processed/accessibility_road_monthly_exposure_stage55.csv) · [Correspondances pistes](../data_processed/winter_profile_piste_assignment_stage55.csv).

La décision et la méthode figurent dans `config/eischoll_unterbaech_regrouping_stage55.json`, avec preuves/empreintes dans [le manifeste](eischoll_unterbaech_regrouping_stage55_summary.json). Rejouer `src/data_processing/regroup_eischoll_unterbaech_stage55.py` hors réseau, puis l’audit des membres étape 56. Les anciens fichiers et scripts restent figés ; les prochains consommateurs doivent explicitement utiliser cette nouvelle version et sa filiation, sans mélanger les univers 71/70.
