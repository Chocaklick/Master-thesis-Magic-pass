# Décembre–avril, clustering et nouveaux arrivants

8 octobre 2026. Décisions reçues : **décembre–avril**, variables continues, essai du portefeuille initial. Aucune nouvelle estimation ou classification lancée. Les groupes reliés et les anciens résultats restent intacts. Les questions sur clustering et effets additionnels sont traitées comme des demandes d’explication, pas comme une validation d’un nouvel algorithme.

## Hiver

Décembre, janvier, février, mars et avril deviennent la fenêtre retenue. Le motif avancé sur les ouvertures est enregistré comme justification du choix, pas comme un pourcentage vérifié. Le format total commune–hiver, la référence et l’inférence restent à préciser dans le protocole d’estimation.

Vérification locale des cinq mois, sans imputation :

| Seuil | Exposées | ≥1 hiver complet avant et après | Hiver précédent et premier hiver post complets |
|---|---:|---:|---:|
| 15 min | 30 | 26 | 26 |
| 30 min | 58 | 49 | 48 |
| 45 min | 88 | 71 | 69 |

Ces comptes décrivent le support, pas un échantillon excluant les autres communes ni une garantie de témoins/tendances comparables. Avril 2026 manque toujours. Le calcul est reproduisible par `src/descriptive/preview_december_april_support.py`, qui ne réécrit aucun fichier.

## Le clustering serait-il judicieux ?

**Oui, en complément des variables continues.** Les variables continues montrent des gradients ; le clustering permet de résumer des combinaisons de caractéristiques et de présenter des profils lisibles. Une classe similaire structurellement n’implique pas un effet Magic Pass homogène ou causal.

Je propose de comparer **k-means et classification hiérarchique de Ward**, avec un petit nombre de classes candidates (2 à 4), avant de consulter les effets. K-means produit des centres utilisables pour rattacher ensuite de nouvelles stations ; Ward montre les rapprochements successifs, mais le rattachement de nouvelles stations demande une règle distincte. Les deux approches dépendent des distances et de la préparation des variables. [Documentation officielle](https://scikit-learn.org/stable/modules/clustering.html).

Le protocole à valider devra préciser : variables historiquement vérifiées, transformations/mise à l’échelle, traitement de la corrélation pistes–remontées, effectifs et données manquantes. Le nombre de classes serait discuté sur séparation, stabilité et interprétation, jamais sur la significativité des effets. On classerait les **groupes-stations existants**, sans refaire les clusters de remontées ou séparer les domaines reliés. Les anciennes classes actuelles restent conservées comme comparaison descriptive.

L’hébergement observé au niveau communal ne sera pas attribué arbitrairement à un groupe. Le portefeuille initial de plusieurs groupes peut conserver plusieurs profils ; une moyenne ou une pondération d’indicateurs continus nécessite une règle validée. La priorité reste de vérifier les caractéristiques d’avant entrée : le clustering ne répare pas leurs dates inconnues.

## Peut-on trouver l’effet de chaque nouvel arrivant ?

**On peut chercher un effet additionnel, sans pouvoir garantir un effet individuel pour chaque groupe.** Des DiD existent pour des expositions qui augmentent/changent plusieurs fois et des effets retardés. Elles demandent notamment des hypothèses de tendances parallèles et une définition de la dose. [de Chaisemartin et D’Haultfœuille, version 14](https://arxiv.org/abs/2007.04267v14).

Application proposée, à auditer avant de choisir l’estimateur : pour l’entrée d’un groupe B, comparer l’évolution hivernale des communes nouvellement exposées à B à celles de communes avec une exposition antérieure comparable, mais sans cet ajout à cette date. Tenir compte de l’ancienneté, de la composition du réseau déjà accessible, des autres ajouts et des chocs simultanés. Conserver une seule série de nuitées par commune ; l’éventuel réemploi d’une commune dans plusieurs contrastes ne crée pas plusieurs unités indépendantes.

Le contre-factuel recherché est **« le réseau antérieur continue, sans l’ajout de B »**, pas « la commune n’a jamais eu de Magic Pass ». On pourrait ensuite comparer les ajouts selon le profil du groupe entrant et le nombre de groupes déjà présents, notamment pour examiner des rendements décroissants.

Attention : une dose « nombre de groupes accessibles » permettrait d’étudier une augmentation d’exposition, mais ne distingue pas automatiquement l’identité de chaque nouvel arrivant. Une simple régression avec un indicateur pour chaque groupe n’est pas une solution générale : sous hétérogénéité, ses coefficients peuvent mélanger les effets des autres traitements. [Référence sur les traitements multiples](https://arxiv.org/abs/2012.10077v8).

Si B et C entrent le même hiver et touchent exactement les mêmes communes, seule leur contribution conjointe est identifiable avec ce panel ; ni clustering ni estimateur moderne ne crée la variation manquante. Une colonne distincte ne suffit pas non plus : témoins, préhistorique, suivi, chevauchements et incertitude doivent être vérifiés. Les 24 communes ayant des ajouts ultérieurs à 30 minutes dans l’audit ne représentent pas 24 expériences indépendantes garanties.

**Prochaine proposition :** portefeuille initial au principal, variables continues ; clustering complémentaire à préparer si validé ; audit d’identification des ajouts groupe par groupe, sans exclusion automatique, avant de présenter les effets individuellement estimables ou uniquement conjoints. Choix exacts d’agrégation, de catégories et d’inférence encore soumis au chercheur.

## Sources et reprise

Décisions dans `config/winter_profile_researcher_decisions.json`. Le rapport 92 et son checkpoint restent historiques et intacts. Données locales : panel territorial HESTA, audit communal/groupe, route finale ; sources originales et valeurs manquantes conservées. Deux articles originaux et documentation officielle consultés le 8 octobre et enregistrés dans metadata ; consultation des résumés/présentation, pas revendication d’un audit intégral des preuves ou d’une implémentation. Pages NBER bloquées403 à l’ouverture, versions auteur arXiv utilisées. Aucune clé utilisée pour la recherche, aucun routage ou téléchargement national répété.
