# Neige : concordance des variations quotidiennes

10 octobre 2026 — complément au [diagnostic sur les niveaux](116_DIAGNOSTIC_NEIGE_SPEARMAN_FR.md), conservé intégralement.

## Résultat principal

**Au même jour civil, la corrélation médiane des variations est de 0,214, contre 0,783 pour les niveaux.** Les deux modèles suivent donc mieux une trajectoire d’enneigement commune que les changements quotidiens appariés au même jour. Le diagnostic est sensible au décalage temporel ; il ne permet pas d’attribuer tout l’écart à la saisonnalité.

| Date OSHD par rapport à SPASS | Spearman médian des niveaux (référence conservée) | Spearman médian des variations |
|---|---:|---:|
| Jour précédent (−1) | 0,698 | 0,038 |
| Même jour (0, référence) | 0,783 | 0,214 |
| Jour suivant (+1) | 0,838 | 0,623 |

Ce sont des **médianes de 40 coefficients de groupes**, pas une corrélation obtenue en empilant tous les jours ou cellules. Chaque coefficient utilise **150 paires de variations observées**. Au même jour, les coefficients vont de −0,059 à 0,383 ; un groupe a une valeur négative et reste conservé. Les 40 coefficients augmentent au décalage +1, mais **aucun décalage n’est sélectionné pour maximiser l’accord**. Le zéro demeure la référence validée.

Le CSV garde **les 70 groupes × 3 décalages = 210 lignes** : 120 coefficients calculables ; les 30 groupes sans axes utilisables restent présents avec valeurs manquantes et statuts explicites. Melchsee-Frutt reste calculable sur 86,35 % de sa longueur cartographiée observée ; les 39 autres couvertures sont complètes.

[Détail par groupe et décalage](../data_processed/native_snow_change_rank_diagnostic_stage72.csv).

## Méthode et contrôles

Validation reçue : « Oui, ajouter ce diagnostic, sans remplacer celui sur les niveaux quotidiens (recommandé). » Configuration nouvelle `config/snow_daily_change_decisions_stage72.json`, namespace Stage72 ; aucun ancien résultat remplacé.

Pour chaque modèle séparément, on calcule `moyenne du jour − moyenne de la veille`, dans son unité source. Les deux journées doivent être réellement consécutives et les quatre moyennes finies. Aucun trou n’est comblé ; aucun saut de plusieurs jours n’est transformé en variation journalière. Les variations sont ensuite classées et Spearman est calculé comme Pearson des rangs moyens en cas d’ex æquo. Une variation constante ou moins de deux paires donne un coefficient manquant, jamais zéro. Les comptes de paires, ex æquo et variations nulles sont publiés ; une variation nulle n’est pas une absence de neige.

**Stabilité spatiale vérifiée avant calcul :** les masques d’observation de chaque empreinte native SPASS–OSHD sont identiques aux deux dates de chacune des **18 000 comparaisons groupe–décalage–jours consécutifs**, y compris aux frontières des fichiers mensuels. Aucune portion observée ne change de composition. Ce contrôle porte sur les empreintes elles-mêmes : une fraction de couverture identique ne suffirait pas. Les moyennes quotidiennes figées Stage70 peuvent donc être différenciées sans changement de support. Aucun rééchantillonnage, interpolation ou nouveau découpage de piste.

## Ce que cela permet — et ne permet pas

- La forte corrélation des niveaux ne garantit pas une reproduction comparable des hausses et baisses journalières. La sensibilité à +1 jour est importante et pourrait refléter des conventions temporelles différentes ; elle ne les prouve pas. Horaires originaux 0 h/6 h conservés, sans convention journalière réinventée.
- La différenciation accentue le bruit et les petites erreurs quotidiennes. Une seule saison, décembre 2022–avril 2023, ne vérifie pas la stabilité interannuelle. Les variations restent dépendantes dans le temps : aucun test supposant 150 jours indépendants ni intervalle de confiance non validé.
- SPASS reste en **unité source inconnue**, OSHD en mètres. Les différences sont internes à chaque modèle, pas entre modèles. Une conversion positive uniforme préserverait les rangs mais ne prouverait pas l’unité. Aucun biais en mètres, calibrage ou raccordement.
- Ces groupes sont des domaines de pistes candidates actuelles avec réserve historique, pas des cellules indépendantes ni des communes. Les nuitées communales et les anciens DiD restent inchangés. Le pilote ne remplace pas les **cinq hivers décembre–avril propres à chaque entrée**.

## Suite proposée, à valider

Le pilote ne fournit **pas une justification suffisante pour raccorder automatiquement OSHD à SPASS**. L’unité SPASS manque, la concordance des variations dépend beaucoup du jour d’appariement et la stabilité sur plusieurs hivers n’est pas vérifiée.

**A — recommandation :** avancer sur les profils neige avec SPASS seul, en unité source explicitement non certifiée, selon les cinq hivers et la pondération déjà validés. Publier les couvertures ; un hiver entièrement absent laisse la moyenne des cinq hivers manquante. Conserver OSHD séparément en diagnostic, sans remplir les hivers absents ni retirer de groupe. Limite : les lacunes récentes ne sont pas résolues ; aucun indicateur en mètres certifiés.

**B :** approfondir la compatibilité avant de produire les profils neige définitifs : rechercher une preuve de l’unité distribuée et des conventions temporelles, puis proposer des diagnostics supplémentaires seulement après cette preuve et validation. Limite : retard des profils neige ; aucune garantie de trouver une preuve ou de rendre les modèles raccordables. Aucun message externe, hypothèse d’unité ou décalage optimal imposé.

**Aucune des deux suites n’est choisie à ta place.** Aucun raccordement, catégorie de clustering, seuil d’exclusion ou nouvel effet estimé.

## Sources, traçabilité et reprise

Source dérivée `DERIVED_NATIVE_SNOW_CHANGES_STAGE72` : CSV quotidiens, poids, calendriers et huit caches originaux figés des Stages69–71. Aucun téléchargement ou nouveau service. Droits des parents maintenus : SPASS/WSL Data Policy, OSHD/CC-BY4.0, tracés OSM/ODbL ; pas de licence de redistribution supplémentaire présumée. **1 203 sources et 8 247 champs uniques**, ajout d’une source et 31 champs, anciennes lignes intactes. Le guide CSV scientifique a structuré unités, effectifs, manquants et couverture sans mise en page additionnelle.

La première implémentation émettait un avertissement pandas/NumPy sur le type temporel générique. Correction technique vers des jours explicites, sans règle scientifique modifiée : première version et deux manifestes conservés dans `data_interim/native_snow_changes_stage72_before_calendar_fix/`, empreintes et amendement documentés dans `config/native_snow_calendar_repair_stage72.json`. CSV et tous les coefficients inchangés ; aucun fichier source réécrit.

**Neuf tests spécifiques et 378 tests complets réussis**, un seul avertissement hérité sans lien avec ce diagnostic. Recalcul indépendant des 120 coefficients, trous calendaires et valeurs manquantes, variations constantes/zéros/ex æquo, identité des empreintes malgré les frontières mensuelles, référence Stage71 et anciens registres. Reprise mise en cache réussie, sans nouvel avertissement. Préservation : **2 326 références SHA sur 1 753 fichiers**, tous les 1 202 anciens enregistrements sources et 8 216 anciens champs exacts ; **1 569 événements de collecte inchangés**. Les trois archives de réparation sont contrôlées séparément par leurs SHA et le test d’identité des versions.

Reprise locale sans réseau :

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/diagnose_native_snow_changes_stage72.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_preservation_stage72.py
.venv/Scripts/python.exe -X utf8 -m pytest -q
```

Le calcul vérifie les SHA et réutilise les valeurs extraites ; il ne relit pas les blocs NetCDF ni ne régénère le diagnostic Stage71. Le dernier contrôle est désormais Stage72 : les anciens comptes et contrôles Stages70–71 restent historiques. Point de reprise : enregistrer la réponse A/B avant tout changement de source ou méthode des profils neige.
