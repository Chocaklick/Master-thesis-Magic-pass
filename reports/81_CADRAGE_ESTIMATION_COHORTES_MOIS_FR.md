# Cadrage de l'estimation par cohorte et mois

## Décision validée le 5 octobre 2026

L'orientation A est retenue : comparer les changements de nuitées par cohorte et mois avec les témoins autorisés. La tendance linéaire reste une sensibilité, pas le contrefactuel imposé au modèle principal. Le panel territorial, les groupes existants, le suivi non équilibré, les entrées successives et les sensibilités déjà validées restent inchangés.

Le choix de l'orientation ne valide pas automatiquement les paramètres ci-dessous. Aucun effet n'est encore calculé et aucune commune n'est retirée.

## Proposition à valider ensemble

| Point | Proposition | Conséquence / alternative |
|---|---|---|
| Référence | Dernier mois avant la première exposition, soit mois relatif -1, et diagnostics sur les 36 mois précédents. | Suppose l'absence d'anticipation à la référence. Une référence plus ancienne ou une période moyenne prétraitement reste possible, mais changerait le contraste. |
| Saisonnalité | Estimer les effets des douze mois séparément pour chaque territoire à partir de ses seules observations prétraitement, sur 36 mois. Une pente accompagne la calibration pour ne pas l'assimiler à la saisonnalité ; elle n'est pas soustraite en principal. | Permet de distinguer saisonnalité locale et chocs de calendrier communs. Suppose un profil saisonnier stable ; une comparaison annuelle ou une variante non corrigée est une autre possibilité. |
| Poids | Même poids à chaque commune observable, dans la cohorte et parmi les témoins autorisés ; agrégation dynamique avec effectifs publiés. Aucun appariement ni seuil de qualité. | Cible une commune moyenne, pas une moyenne pondérée par la taille hôtelière. Aucun coefficient global mélangeant silencieusement les durées de suivi n'est choisi. |
| Données manquantes | Conserver les 79 communes dans l'inventaire. Marquer les trois historiques prétraitement incomplets comme non calculables dans cette spécification, sans imputation. Pour chaque contraste, exiger les deux valeurs originales observées. | Alternative : différer l'estimation et rechercher les historiques complets des trois fusions. Les dates et raisons de non-calcul resteraient publiées. |
| Incertitude | Bootstrap par territoire : tous ses mois et ses réutilisations comme témoin restent ensemble. Intervalles/bandes simultanés à 95 % ; signaler les petites cohortes. | Ne pas traiter les mois comme des communes indépendantes. Les quelques communes de certaines cohortes limitent la précision et la fiabilité de l'inférence. |

La nouvelle typologie OFS, la construction et les séries agrégées du rapport 80 restent du contexte. Elles ne deviennent pas automatiquement des variables d'ajustement. Les capacités hôtelières après entrée ne sont pas introduites comme contrôles, car elles peuvent être modifiées par le traitement.

## Disponibilité vérifiée, sans appliquer de sélection

Les 79 communes et 5 580 observations postérieures restent dans le panel. 76 communes disposent à la fois de la référence -1 et d'une calibration saisonnière algébriquement calculable. Elles représentent 5 451 observations postérieures, avant de vérifier pour chaque date les résultats disponibles chez les témoins. Ces comptes sont une conséquence potentielle de la proposition, pas un échantillon adopté.

| Cohorte | Exposées : référence et calibration / inventaire | Témoins : référence et calibration / candidats |
|---|---:|---:|
| 2017-11 | 37/40 | 138/145 |
| 2018-05 | 3/3 | 137/142 |
| 2019-05 | 3/3 | 136/139 |
| 2022-05 | 16/16 | 122/123 |
| 2023-05 | 9/9 | 113/114 |
| 2024-05 | 5/5 | 109/109 |
| 2025-05 | 3/3 | 106/106 |

Les trois cas sont Blonay–Saint-Légier, Val de Bagnes et Laténa. Aucune reconstruction partielle ou exclusion arbitraire n'est appliquée. La disponibilité d'un témoin ici ne garantit pas son observation pour chaque mois postérieur, sa comparabilité, ni l'absence de chocs ou de retombées indirectes.

## Sources et reprise

Les entrées sont les fichiers territoriaux du rapport 78 et les règles approuvées des rapports 74–79. La vérification réutilise le diagnostic de rang du rapport 79 ; elle ne soustrait aucune saisonnalité et n'estime aucun effet. Empreintes SHA-256 et comptes : `accessibility_cohort_time_specification_support.json`.

Cadre méthodologique déjà enregistré : `CALLAWAY_SANTANNA_2021_DID` ([article, version auteur](https://arxiv.org/abs/1803.09015v4)). La correction saisonnière préestimée décrite ici est une proposition spécifique au projet, non une implémentation automatiquement certifiée par cet article. Les hypothèses de tendances parallèles après correction, de non-anticipation et de comparaison valide restent à évaluer.

Décision durable : `config/accessibility_cohort_time_estimator.json`. Seule l'orientation A est approuvée ; `parameter_bundle_approved` reste faux. Avant le calcul, recueillir l'accord explicite pour cette proposition ou ses modifications. L'effet propre d'une entrée additionnelle reste une analyse distincte, et aucun résultat n'est déclaré causal.
