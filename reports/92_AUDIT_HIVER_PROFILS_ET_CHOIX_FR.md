# Recentrage : hiver, profils de stations et expositions multiples

8 octobre 2026. **Audit uniquement : aucune nouvelle estimation, classification ou exclusion.** Les DiD toutes saisons du rapport 91 restent la référence conservée. Les seuils routiers validés restent 30 minutes au principal, 15/45 en sensibilité. Les propositions ci-dessous attendent validation.

## 1. Ce qui existe et ce qui manque

Les 71 groupes-stations validés, leurs 75 points d’accès et les 185 territoires communaux sont conservés. Les groupes reliés ne sont pas redécoupés. Les composites non prouvés reliés — notamment Beatenberg/Niederhorn et Vallée de Joux — gardent leurs réserves documentées. Un cluster de remontées n’est pas automatiquement un groupe-station. Les nuitées HESTA sont **hôtelières et communales**, pas des nuitées propres à une station ou toutes formes d’hébergement.

| Information disponible | Couverture et limite pour les profils préentrée |
|---|---|
| Pistes, remontées, altitude du sommet | 66/71 groupes complets, 1 incomplet (La Forclaz), 4 sans fiche. Fiches actuelles/non datées : **0 profil structurel vérifié comme préentrée dans les tables auditées**. Cela ne signifie pas que les archives ne contiennent aucune preuve historique. |
| Deux classes existantes | Clusters plutôt petits/bas et plutôt grands/hauts, rapport 18. Raccordement exact par `resort_id` : 31 groupes liés à la première classe, 35 à la seconde, 5 sans classe. Classes actuelles descriptives, pas catégories préentrée déjà validées. |
| Hébergement historique | Chambres/lits/établissements disponibles mensuellement dans le panel territorial. À 30 min, 55/58 communes ont les 24 mois de lits précédant leur première exposition au pass. **Contexte communal**, pas capacité propre du groupe ni total d’un bassin approuvé. |
| Clientèle et demande préalables | À 30 min, 51/58 communes ont 24 mois de nuitées et de clientèle étrangère avant exposition. Les données non observées restent manquantes. |
| Neige, climat, accessibilité | Des sources historiques existent pour neige/climat, mais les indicateurs actuels couvrant avant et après l’entrée ne peuvent pas être repris tels quels. Recalcul préentrée et représentativité géographique à vérifier. Route : réseau actuel tenu fixe, restrictions hivernales non certifiées. |
| Offre estivale historique | Registre de 14 destinations anciennes, avec 36 destination-saisons à accès estival documenté et 13 statuts estivaux individuels inconnus. Ce n’est pas une couverture des 71 groupes. Les archives annuelles existantes sont à retranscrire/étendre avant une analyse estivale générale. |

Les kilomètres de pistes et remontées restent cumulés **une fois par fiche unique** dans les groupes existants. L’altitude n’est pas additionnée. Une altitude de sommet de fiche n’est pas une altitude moyenne skiée ni l’altitude du départ. L’absence de date ne sera pas remplacée par une hypothèse implicite de stabilité.

## 2. Hiver : choix proposé avant estimation

**Proposition : novembre–avril**, déjà défini comme hiver analytique dans `config/temporal_controls.json`, avec décembre–mars en sensibilité. Ce périmètre large comprend les débuts/fins de saison sans prétendre mesurer les jours d’ouverture. Alternative : décembre–mars au principal, plus ciblé mais omettant une part du tourisme hivernal.

Je propose une observation **commune × hiver** : somme des six nuitées mensuelles, hiver identifié par ses deux années, puis `log(1 + total hivernal)` pour les contrastes. Une saison incomplète reste indisponible, jamais annualisée ou mise à zéro. La commune demeure dans l’inventaire. Les mois disponibles restent conservés pour les diagnostics. Alternative : modèle mensuel limité aux mois d’hiver, plus détaillé mais nécessitant une nouvelle définition du mois de référence et de la correction saisonnière.

| Seuil routier | Communes exposées | ≥1 hiver complet avant et après, nov.–avr. | Même diagnostic, déc.–mars |
|---|---:|---:|---:|
| 15 min | 30 | 26 | 28 |
| 30 min | 58 | 49 | 55 |
| 45 min | 88 | 71 | 83 |

À 30 min, 50 communes ont leur premier hiver postentrée complet, 48 leurs deux premiers. Les historiques et l’hiver 2025/2026 incomplet expliquent la couverture. Avril 2026 n’est pas encore observé : aucune comparaison d’un total novembre–mars à un total novembre–avril. Ces comptes **ne garantissent ni témoins adéquats, ni tendances comparables, ni estimation fiable**.

Le premier hiver exposé utilise l’ancre hivernale de groupe déjà enregistrée en novembre, qui est une convention analytique sauf validité fondatrice exactement documentée. Les caractéristiques seraient figées **avant la première exposition au pass en mai/novembre**, pas juste avant le premier hiver : les mois d’été déjà exposés ne doivent pas entrer dans la baseline. Les contrastes resteraient par cohorte d’entrée et hiver, avec témoins jamais/pas encore exposés. La référence proposée est l’hiver immédiatement précédent, complet et préexposition ; s’il manque, ne pas choisir silencieusement un hiver plus ancien. Les comptes de couverture ci-dessus ne vérifient pas encore ce support précis ni celui des témoins. L’effet annuel antérieur est conservé, non renommé « effet hivernal ».

## 3. Profils : options à valider, sans examiner leur significativité

**A — Catégories simples, proposées pour une présentation lisible.** Après vérification historique, examiner séparément taille (≤20 km / >20 km de pistes) et altitude du sommet (<2 000 m / ≥2 000 m). Ce sont des coupures descriptives proposées, pas des seuils physiques ou causaux établis. Pas de croisement automatique en quatre/huit cellules. Hébergement communal pré24 mois présenté séparément, de préférence en variable continue. Les coupures et les horizons seront fixés avant estimation et ne seront pas ajustés pour obtenir un résultat significatif.

**B — Variables continues.** Examiner les différences associées à la taille, l’altitude et la capacité préentrée sans seuils, avec interactions simples. Évite les coupures, mais impose une forme fonctionnelle et ne crée pas des catégories naturelles. Même besoin de sources historiques et de diagnostic de support.

**C — Nouvelle typologie multivariée préentrée.** Réutiliser la logique/interprétation des deux classes existantes, mais les reconstruire sur les groupes et des caractéristiques historiques vérifiées. Plus synthétique, plus coûteux et potentiellement instable avec peu d’unités indépendantes. Ce n’est ni un reclustering des remontées ni un transfert des anciens centroïdes actuels dans un modèle historique.

Les deux anciennes classes seront conservées comme repère descriptif, pas promues automatiquement au principal. Les groupes sans caractéristique restent « non classables » sur cette dimension, sans disparition du résultat global. Les nuitées hôtelières ne permettent pas de classer directement un groupe en « station de séjour » versus « station d’excursion » : hébergement communal et déplacements réels ne sont pas interchangeables.

## 4. Communes exposées à plusieurs groupes

À 30 min, **33/58 communes ont plusieurs groupes au premier hiver**, 45 ont plusieurs groupes actifs au cours de l’historique, et 24 connaissent une entrée ultérieure. Il faut conserver **une seule ligne commune–hiver dans chaque scénario**, sans copier ses nuitées pour chaque groupe.

**Méthode principale proposée : profil du portefeuille déclencheur.** À la première exposition, conserver tous les groupes entrant ensemble. Pour chaque dimension validée : classe commune aux groupes si elle est homogène, sinon « mixte », ou « information insuffisante ». Ce profil initial reste fixe. Les entrées ultérieures restent dans la trajectoire, conformément à la décision antérieure. Aucun groupe n’est choisi parce qu’il est le plus proche, le plus grand ou associé au meilleur résultat.

L’effet vise alors la **réponse des nuitées communales après l’entrée d’un portefeuille de ce profil**, pas l’effet isolé de chaque station. Les groupes reliés constituent toujours une unité conjointe. Une commune « mixte » n’est pas répartie avec des poids inventés. Une distribution ou moyenne pondérée des profils demanderait une règle supplémentaire validée.

Alternatives : un modèle conjoint des expositions par profil et des ajouts successifs, plus proche d’effets additionnels mais exigeant variation indépendante et hypothèses d’additivité ; ou une analyse secondaire des expositions uniques, plus lisible mais moins représentative. **Aucun de ces filtres/modèles n’est appliqué maintenant.**

## 5. Incertitude et portée des résultats

Pour chaque profil : communes, groupes déclencheurs distincts, cohortes, hivers observés, témoins et intervalles. Comparer aussi les profils aux mêmes cohortes/horizons lorsque le support le permet, plutôt que confondre profil et durée de suivi. Taille et altitude peuvent être corrélées ; régions, cohortes et clientèle peuvent aussi expliquer des différences entre profils. Un contraste par catégorie n’isole donc pas automatiquement l’effet propre de sa caractéristique. Le contraste moyen hivernal sera la référence, mais les profils seront au premier plan.

Le graphe commune–groupes accessibles compte 13 composantes de chevauchement à 30 min, dont deux de 24 et 14 communes ; à 45 min seulement deux composantes. Ce diagnostic conservateur ne définit pas automatiquement des groupes indépendants ou un nouveau bootstrap. Il indique que 58 communes ne sont pas nécessairement 58 réponses indépendantes de stations. L’inférence territoriale antérieure et une sensibilité au partage des groupes devront être discutées avant estimation. Peu de groupes/cohortes, absence de témoins, colinéarité ou suivi court seront signalés comme limites de fiabilité, **pas filtrés selon les p-values**.

Pour l’été, proposition mai–octobre, séparé de l’hiver, mais uniquement après vérification groupe/composante × année de l’inclusion réelle et de la validité du produit. Une preuve estivale pour une composante n’est pas transférée à tout le groupe ou à son accès le plus rapide. Inconnu ≠ exclu du pass ≠ témoin non exposé. Les anciens trous 2019/2020 et 2021/2022, les composites mixtes et les témoins potentiellement exposés doivent rester explicites. Pas d’estimation estivale générale lancée avec le registre actuel.

## Sources et reprise

Audit local, sans téléchargement : HESTA et capacité OFS déjà archivés, entrées Magic Pass, registre annuel et preuves d’offre, groupes validés, fiches structurelles, classes Path C et route finale. Sources/variables d’audit ajoutées aux deux registres metadata. Voir rapports [10](10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md), [18](18_PATH_C_SEGMENTATION_AND_ANALOGUES.md), [38](38_PATH_C_FEATURE_READINESS_AUDIT.md), [55](55_GROUPES_STATIONS_ET_POINTS_ACCES_FR.md) et [91](91_DID_ROUTIER_30MIN_SENSIBILITES_FR.md).

Reprise : `.venv/Scripts/python.exe src/descriptive/audit_winter_profile_design.py`. Deux tables : `winter_profile_group_audit.csv` (71 groupes) et `winter_profile_municipality_support_audit.csv` (185 territoires × 3 seuils × 2 fenêtres). Ce sont des scénarios de couverture, pas 1 110 communes indépendantes. Entrées/sorties et anciens résultats protégés par SHA dans `winter_profile_design_audit_summary.json`. Le checkpoint identique est réutilisé sans réécriture. **Prochaine étape : valider fenêtre/agrégation, approche des profils et portefeuille initial ; puis établir les caractéristiques historiques, étendre le registre été et soumettre la spécification d’estimation/inférence encore nécessaire.**
