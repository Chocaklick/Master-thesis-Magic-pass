# Compatibilité neige : unités, dates et modèles

10 octobre 2026 — option **B** validée : approfondir les preuves avant les profils. Les diagnostics [116](116_DIAGNOSTIC_NEIGE_SPEARMAN_FR.md) et [117](117_DIAGNOSTIC_VARIATIONS_QUOTIDIENNES_NEIGE_FR.md) restent inchangés.

## Ce que l’audit établit

| Point | Conclusion | Conséquence |
|---|---|---|
| Unité OSHD récolté | `hs.unit=m` dans les 36 fichiers mensuels ; publication concordante. | OSHD est documenté en mètres. |
| Horaire OSHD | État à 6 h CET, offset fixe UTC+01, donc 5 h UTC ; pas une moyenne quotidienne. | Interprétation désormais sourcée, anciens timestamps conservés. |
| Unité SPASS | Aucun attribut `unit`/`units` dans `HSCLQMD`. SWE2HS accepte plusieurs unités. | Toujours **UNKNOWN** ; aucun facteur de conversion appliqué. |
| Date SPASS | Étiquette décodée à minuit ; instant physique et fuseau de la sortie non certifiés. | Ne pas la présenter comme un état à minuit UTC. |
| Identité des modèles | La référence EKF de SPASS n’est pas notre produit PF/FSM2 à 250 m. | Le raccordement publié avec EKF ne valide pas un raccordement avec PF. |

OSHD distingue l’état de neige du cumul de ruissellement sur les 24 heures précédentes. Le décalage fixe des fichiers est corroboré par la [publication OSHD, section 6](https://tc.copernicus.org/articles/20/3387/2026/). Aucun passage implicite à l’heure d’été ; aucune réécriture des dates déjà appariées.

La [publication SPASS, sections 2.3 et 3.3](https://tc.copernicus.org/articles/19/4391/2025/) déconseille l’interprétation quotidienne et privilégie des agrégations plus longues. Ses températures couvrent le jour UTC, mais ses précipitations couvrent 6 h UTC de D à D+1. Ce sont des **fenêtres d’entrée**, pas une preuve de l’instant représenté par la neige produite. Elles rendent une sensibilité au décalage plausible, sans justifier de choisir +1 jour.

**Point critique :** le faible accord des variations quotidiennes ne suffit pas à rejeter la compatibilité des moyennes hivernales. Inversement, l’accord des rangs ne prouve ni unité ni interchangeabilité. Le pilote porte sur un seul hiver ; les réserves sur les proxies de pistes actuelles restent valables. Aucune nouvelle restriction d’altitude, sélection de groupe ou agrégation estimée.

## Vérification du logiciel : ce qu’elle ne résout pas

L’[API `convert_2d`](https://git-pages.wsl.ch/aschauer/swe2hs/_autosummary/swe2hs.two_dimensional.convert_2d.html) propose mètres, millimètres et centimètres, avec mètres par défaut. Son [code publié](https://git-pages.wsl.ch/aschauer/swe2hs/_modules/swe2hs/two_dimensional.html) convertit vers l’unité choisie et écrit `unit`. Le [code journalier](https://git-pages.wsl.ch/aschauer/swe2hs/_modules/swe2hs/stepwise.html) reprend l’étiquette temporelle SWE pour nommer sa sortie ; son [interface](https://git-pages.wsl.ch/aschauer/swe2hs/_autosummary/swe2hs.stepwise.process_timestep_from_nc_files.html) a aussi été examinée.

Cela **ne relie pas** ces versions/fonctions au fichier SPASS distribué : ses métadonnées diffèrent et le script de production exact n’a pas été identifié dans les pièces examinées. Le ZIP original ne contient qu’un fichier NetCDF, sans notice jointe. La [publication SnowQM](https://gmd.copernicus.org/articles/17/8969/2024/) concerne la correction du SWE, pas la convention du HS distribué. Ni un défaut logiciel, ni l’exemple en centimètres déjà examiné, ni l’ordre de grandeur des valeurs ne certifie l’unité réelle.

## Information nécessaire auprès du producteur

L’inconnue est factuelle : **il ne faut pas te demander de choisir arbitrairement une unité ou une date**. Il faut une notice officielle, le script/configuration de production exact, ou une confirmation écrite identifiant le fichier récolté. Brouillon prêt ci-dessous ; **aucun message envoyé**. Contact de correspondance publié : Christoph Marty, `marty@slf.ch`, dans l’article SPASS (prénom corrigé lors de la recherche Stage74).

> Objet : unité et convention temporelle du fichier SPASS HSCLQMD
>
> Bonjour, pour mon mémoire à l’UNIL, j’utilise la ressource HS de SPASS (DOI 10.16904/envidat.580), fichier `HSCLQMD_ch01h.swiss.lv95_WY_1962_2023.nc`, variable `HSCLQMD`, version v1.0, `prod_date=2024-10-13 13:57:52`. Son SHA-256 est `b8d740993a4bfa2b542aa2c2986564073d275b07f2b2fd9c869dfc5daf597c0d`.
>
> Pourriez-vous confirmer : (1) l’unité des valeurs numériques stockées, sans conversion ; (2) l’instant ou intervalle physique représenté par l’étiquette D et son fuseau, notamment par rapport aux précipitations de 6 h UTC D à D+1 ; (3) la version/fonction SWE2HS et les paramètres d’unité employés ? Une notice ou le script de génération serait particulièrement utile. L’objectif est de comparer des moyennes décembre–avril avec le produit OSHD-PF/FSM2 à 250 m, sans présumer leur raccordabilité. Merci.

Après réception : archiver la preuve, la relier à cette empreinte/version, puis proposer les éventuelles conversions et diagnostics agrégés pour validation. **Aucun raccordement automatique**, même avec l’unité connue. Les cinq hivers propres à chaque entrée, leurs poids égaux et les groupes/communes conservés restent inchangés. Les profils définitifs attendent cette preuve conformément à B.

## Traçabilité et reprise

[CSV des 15 constats et limites](../data_processed/snow_compatibility_evidence_stage73.csv). Chaque ligne donne source, section/fonction, fichier local, SHA-256, statut de preuve et limite ; aucune ligne n’est une observation communale ou un profil de station.

Six petites pièces publiques archivées avec HTTP200/SHA ; l’article OSHD déjà archivé est réutilisé. Quatre échecs initiaux de sockets dans le bac à sable sont conservés, puis accès réseau autorisé pour le même collecteur respectant robots.txt : dix événements ajoutés, aucune réécriture d’événement antérieur. Les erreurs du lecteur web ne sont pas assimilées à des HTTP d’archive. Aucune nouvelle grille, installation, connexion de compte ou donnée neige relue.

Registres append-only : **1 210 sources / 8 261 champs**, soit +7 sources et +14 champs ; droits des sources conservés, aucune licence de redistribution inventée. Les guides de recherche primaire et CSV scientifique ont structuré la séparation preuves/inférences/manquants ; recherche web en remplacement du CLI Tavily absent, sans mise en page supplémentaire.

Contrôles terminés : **7 tests spécifiques et 385 tests complets réussis** ; un avertissement hérité du DiD routier, sans lien avec cet audit. Reprise en cache identique. Préservation : **2 346 références SHA sur 1 770 fichiers**, anciens registres et 1 569 événements de collecte exacts. Tous les travaux sont arrêtés ; aucun collecteur ou calcul en arrière-plan.

Configuration : `config/snow_compatibility_decisions_stage73.json` (réponse B exacte). Producteur et reprise locale :

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/audit_snow_compatibility_stage73.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_preservation_stage73.py
.venv/Scripts/python.exe -X utf8 -m pytest -q
```

Le producteur réutilise les documents contrôlés et refuse une modification de son résultat figé. Pas de conversion, sélection de décalage, imputation, exclusion, profil neige final, clustering ou DiD supplémentaire. Le contrôle Stage73 devient la référence de reprise ; les contrôles à comptes fixes des étapes précédentes restent historiques. B résout l’ancienne question A/B ; seule la preuve producteur reste à obtenir.
