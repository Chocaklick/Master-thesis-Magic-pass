# 66 — Audit externe des 14 communes traitées

**Ancrage étudié :** 2017-11-01 — **fenêtre :** 2015-11-01 à 2019-10-01.

## Résultat directement utilisable

Les 50 paires conservées après le screening interne deviennent deux ensembles emboîtés :

- **ensemble élargi revu : 38 paires, 9 communes traitées** ;
- **noyau strict « Magic Pass seul » : 32 paires, 7 communes traitées**.

Les 14 communes restent utilisables pour une description ou une analyse d'intervention combinée. Aucune commune, aucun contrôle et aucune paire n'est validé causalement à ce stade : la revue externe des contrôles et des bassins touristiques reste à terminer.

## Chocs directs forts — hors des deux ensembles Magic-only

| Commune | Paires | Motif principal | Sources |
|---|---:|---|---|
| Saanen | 1 | Gstaad/Saanen est aussi exposée au pass Top4 dès l'automne 2017, exactement au moment de l'entrée dans Magic Pass. | JUNGFRAU_TOP4_2018_19_CONTINUITY |
| Leysin | 2 | Leysin finance une nouvelle remontée Fer-Brion-Tête d'Aï puis des travaux d'enneigement mécanique pendant la fenêtre étudiée. | LEYSIN_CHAIRLIFT_PREAVIS_2017\|LEYSIN_SNOWMAKING_PREAVIS_2018 |
| Ollon | 3 | Les Bains de Villars rénovés et leur espace wellness ouvrent en août 2017, juste avant l'ancrage; le projet représente environ CHF 18,5 millions. | OLLON_VILLARS_BATHS_PREAVIS_2017 |
| Ormont-Dessus | 2 | La commune garantit la télécabine Vioz-Mazots et les travaux de la Jorasse; le Meilleret est aussi adapté pour Lausanne 2020. | ORMONT_DESSUS_TVGD_LOAN_PREAVIS_2017\|ORMONT_DESSUS_MEILLERET_PREAVIS_2018 |
| Château-d'Oex | 4 | Après les difficultés de l'exploitant et la fin d'une subvention annuelle de CHF 350'000, la vente des actifs de La Braye pour CHF 1 est proposée en 2018. | CHATEAU_DOEX_LA_BRAYE_2018 |

## Interventions directes modérées — ensemble élargi seulement

| Commune | Paires | Motif principal | Sensibilité recommandée |
|---|---:|---|---|
| Plaffeien | 5 | La commune approuve en avril 2019 une nouvelle société touristique intégrant les offres existantes et de nouveaux produits; le choc est direct mais tardif. | Tronquer la période postérieure à décembre 2018 et comparer à la fenêtre complète. |
| Anniviers | 1 | Des outils numériques, du marketing et de nouveaux produits outdoor sont financés en 2017-2019, en même temps que l'exposition Magic Pass. | Traiter comme intervention combinée ou retirer du noyau Magic Pass seul. |

## Communes conservées dans le noyau strict, avec réserves ciblées

| Commune | Paires | Réserve | Sensibilité recommandée |
|---|---:|---|---|
| Köniz | 4 | Aucun choc touristique communal majeur n'a été identifié dans la revue officielle limitée. L'alerte de capacité hôtelière culmine avant novembre 2017. | Conserver les contrôles de capacité et signaler le pic pré-ancrage. |
| Haut-Intyamon | 5 | Le contexte stratégique des Préalpes fribourgeoises est documenté, sans rupture opérationnelle propre à Haut-Intyamon dans les sources examinées. | Tester des erreurs ou effets fixes au niveau régional si l'échantillon le permet. |
| Bulle | 5 | Bulle mène dès 2018-2019 un travail d'identité et de statut touristique, mais les documents décrivent surtout une démarche de politique et de marque. | Comparer les résultats avec et sans les mois de 2019. |
| Gruyères | 4 | La stratégie régionale couvre directement l'opérateur de Moléson et peut toucher le bassin de Gruyères, sans rupture communale unique clairement datée. | Tester une robustesse au regroupement régional et aux capacités hôtelières. |
| Fribourg | 4 | L'auberge de jeunesse ferme en novembre 2016 et n'est pas remplacée en 2019; ce changement précède l'ancrage mais affecte la structure d'hébergement. | Recommencer la pré-tendance après novembre 2016 ou retirer les mois antérieurs. |
| La Chaux-de-Fonds | 5 | Un consortium est retenu pour un futur hôtel à l'automne 2019, mais le rapport ne montre pas une mise en exploitation dans la fenêtre étudiée. | Vérifier la date d'ouverture avant de prolonger la fenêtre après octobre 2019. |
| Saignelégier | 5 | La célébration Jura 40 attire ponctuellement des milliers de visiteurs en juin 2019; il s'agit d'un événement concentré sur un mois. | Réestimer après exclusion de juin 2019. |

## Méthode et limites

La revue utilise des préavis, rapports et bulletins officiels archivés localement avec URL, date de récupération et SHA-256. Les documents ont été lus au niveau des pages/sections indiquées. Le classement distingue un choc direct fort, une intervention directe modérée et une réserve indirecte ou ponctuelle. Une recherche sans résultat n'est jamais interprétée comme preuve d'absence.

Les alertes de capacité hôtelière sont complétées par la date de leur plus forte variation annuelle : cela évite de confondre automatiquement saisonnalité, volatilité pré-traitement et rupture postérieure. Les fichiers CSV gardent le détail des sources, fichiers locaux, empreintes, dates et limites de chaque cas.

## Fichiers produits

- `reports/accessibility_treated_external_shock_evidence.csv` : revue des 14 communes ;
- `data_processed/accessibility_comparison_treated_external_risk_screen.csv` : 70 paires avec les deux niveaux ;
- `reports/accessibility_comparison_treated_external_review_summary.json` : compteurs et empreintes d'entrée.
