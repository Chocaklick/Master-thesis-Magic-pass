# Premiers contrastes par cohorte et mois — option A

## Résultat et couverture

Calcul exploratoire approuvé le 5 octobre 2026. **76/79 communes** contribuent au calcul principal, soit **5451 observations postérieures**. Les 79 communes et 5 580 observations restent dans le panel source. Aucun filtrage de qualité, appariement, imputation ou contrôle OFS nouveau.

Blonay–Saint-Légier, Val de Bagnes et Laténa gardent leurs 51, 63 et 15 mois postérieurs, mais n'ont pas la référence/calibration requise. Moutier constitue une seule commune, avec ses deux identifiants sources préservés.

Les chiffres ci-dessous sont des différences de changements de **log(1 + nuitées)**, en points logarithmiques. Ce ne sont ni des nuitées supplémentaires, ni directement des pourcentages de nuitées, ni des effets causaux établis. Chaque ligne peut représenter une composition différente de communes/cohortes.

| Mois relatif | Communes | Cohortes | Contraste principal | IC ponctuel 95 % | Bande simultanée 95 % |
|---:|---:|---:|---:|---:|---:|
| -24 | 75 | 7 | -0.044 | [-0.177 ; 0.094] | [-0.267 ; 0.180] |
| -12 | 76 | 7 | -0.028 | [-0.124 ; 0.065] | [-0.186 ; 0.129] |
| 0 | 76 | 7 | -0.060 | [-0.144 ; 0.021] | [-0.198 ; 0.079] |
| 5 | 76 | 7 | 0.006 | [-0.098 ; 0.114] | [-0.171 ; 0.184] |
| 11 | 73 | 6 | -0.009 | [-0.097 ; 0.079] | [-0.158 ; 0.139] |
| 23 | 66 | 5 | 0.078 | [-0.013 ; 0.169] | [-0.072 ; 0.228] |
| 35 | 59 | 4 | 0.074 | [-0.070 ; 0.213] | [-0.162 ; 0.310] |
| 59 | 43 | 3 | 0.104 | [-0.050 ; 0.257] | [-0.151 ; 0.358] |
| 100 | 37 | 1 | 0.058 | [-0.085 ; 0.198] | [-0.175 ; 0.292] |

Sur les 101 mois relatifs postérieurs, 0 bandes simultanées excluent zéro. Cela ne prouve pas un effet nul : l'incertitude et les limites d'identification restent importantes.

## Méthode et vérifications

Pour chaque cohorte g, une régression locale sur les seuls 36 mois avant g estime intercept, pente calendaire et onze indicatrices de mois. Un rang complet et des degrés de liberté positifs rendent le calcul possible, sans seuil de qualité. On soustrait seulement les effets saisonniers à l'issue. La pente n'est soustraite que dans la sensibilité linéaire. Les trous restent des trous et le temps reste calendaire.

Le contraste à la date t est : changement moyen depuis g−1 chez les exposées, moins le même changement chez les témoins observés. Les témoins sont ceux approuvés à g, jamais ou pas encore exposés, et sortent strictement avant leur propre entrée. Chaque commune a le même poids dans sa cohorte ou chez les témoins. À mois relatif égal, les cohortes sont pondérées par leur nombre de communes effectivement observées : chaque commune traitée garde le même poids.

Bootstrap multiplicateur gaussien, 4 999 tirages, graine 20261005 : un même multiplicateur par territoire dans tous les mois, cohortes et rôles. Les contributions centrées des moyennes et des poids de cohortes donnent les erreurs simulées. IC ponctuels dans la table cohorte/mois ; bandes simultanées sur tous les mois calculables de chaque courbe dynamique, hors référence normalisée −1. Les bandes ne couvrent pas conjointement toutes les variantes. La calibration est une fonction du dossier prétraitement de chaque territoire, conservé entier. Cette approximation asymptotique reste fragile pour les cohortes de trois communes et ne corrige pas une dépendance géographique entre communes.

La saisonnalité étant ajustée dans la fenêtre diagnostique elle-même, les écarts prétraitement sont des diagnostics **en échantillon**, pas une validation indépendante des tendances parallèles. La référence −1 suppose l'absence d'anticipation. L'audit 79 relevait déjà des écarts de tendance, surtout pour les cohortes récentes. Un intervalle étroit ne corrige pas ces problèmes d'identification.

## Sensibilités disponibles

| Variante | Ce qui change |
|---|---|
| Témoins jamais exposés | Retire les futurs exposés du groupe de comparaison, sans changer les communes traitées. |
| Tendance linéaire prétraitement | Soustrait également la pente pré36 propre à chaque territoire, extrapolée après entrée. Hypothèse forte, pas modèle principal. |
| Mois de contraste COVID omis | Omet mars 2020–mars 2022 des comparaisons. La calibration pré36 reste identique : ce n'est pas une estimation entièrement sans COVID. |
| Horizons communs 6/12/24 mois | Respectivement 76/73/65 communes avec toutes les issues pré/post observées. Variante complémentaire avec les mêmes 65 communes aux trois horizons. |

Comparaison compacte à mois relatif 23, qui représente 66 communes en principal :

| Variante | Communes | Contraste | IC ponctuel 95 % |
|---|---:|---:|---:|
| Principal | 66 | 0.078 | [-0.013 ; 0.169] |
| Jamais exposés | 66 | 0.082 | [-0.007 ; 0.173] |
| Pente prétraitement | 66 | 0.108 | [-0.026 ; 0.242] |
| Mois COVID omis | 62 | 0.048 | [-0.040 ; 0.139] |
| Même support 65 communes | 65 | 0.082 | [-0.011 ; 0.174] |

Les CSV donnent tous les mois et variantes, sans sélectionner les résultats favorables. Aucun coefficient post global/saut permanent n'est calculé : son agrégation n'était pas choisie dans le cadrage approuvé. Les plages 0–5, 6–11, 12–23 et 24+ restent examinables mois par mois ; une baisse entre plages ne démontrerait pas un rendement décroissant, car composition et contexte changent. L'effet propre des entrées additionnelles n'est pas identifié par ce modèle, qui conserve toute la trajectoire du réseau.

## Limites, sources et reprise

L'accessibilité actuelle est tenue fixe historiquement, les retombées indirectes restent possibles et seuls 18/79 territoires disposent d'une revue de chocs antérieure. La pandémie touche certaines calibrations et suivis. Ces contrastes ne débloquent donc pas une interprétation causale, une prédiction d'effet individuel de station ou un score d'opportunité.

Entrées : panel HESTA territorial et univers de comparaison du rapport 78, décisions des rapports 74–79, proposition historique 81. Approbation d'exécution : `config/accessibility_cohort_time_execution.json`. Le rapport 81 et sa configuration sont conservés comme instantané de la proposition avant accord, pas comme état courant.

Cadre : `CALLAWAY_SANTANNA_2021_DID` et documentation officielle [`att_gt`](https://bcallaway11.github.io/did/reference/att_gt.html), consultée le 5 octobre 2026 (`DID_ATT_GT_OFFICIAL_DOCUMENTATION`). Cette dernière documente le principe de comparaisons par cohorte, la référence universelle et le bootstrap multiplicateur. Le script Python applique un contraste et une saisonnalité propres au projet : ce n'est pas l'exécution du package R ni une certification automatique de sa théorie pour ce panel.

Résultats : `accessibility_cohort_time_estimation_cohort_month.csv`, `_dynamic.csv`, `_calibration.csv`, `_territory_support.csv`. Empreintes des entrées/sorties, versions et comptes : `accessibility_cohort_time_estimation_summary.json`. Les variables et sources sont enregistrées dans les deux catalogues metadata.

Reprise : `.venv/Scripts/python.exe src/causal_inference/estimate_accessibility_cohort_time.py`, puis mise à jour de la provenance et tests. Le calcul est déterministe, local et ne relance aucune collecte. Prochaine discussion : confronter les sensibilités et diagnostics, puis valider tout changement de référence, calibration, témoins ou agrégation avant de le mettre en œuvre.
