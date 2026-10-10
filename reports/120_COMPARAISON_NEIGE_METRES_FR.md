# Neige SPASS–OSHD : comparaison en mètres

10 octobre 2026 — Étape 75. Résultats descriptifs, pas estimation du Magic Pass.

## Hypothèse et périmètre

Conformément à ta réponse, **les nombres SPASS sont interprétés comme des mètres** (facteur 1). Cette hypothèse analytique est validée ; la déclaration d'unité du fichier original reste absente. On ne modifie ni les originaux ni leurs métadonnées. OSHD déclare effectivement `m`.

Comparaison de décembre 2022 à avril 2023 : 151 jours par groupe calculable, sur les mêmes portions de pistes observées dans les deux grilles natives, sans interpolation. Les 70 groupes restent présents : 40 calculables et 30 sans géométrie utilisable. La couverture commune reste complète pour 39 groupes et de 86,35 % pour Melchsee-Frutt. Les pistes actuelles ne sont pas présentées comme préentrée vérifiées.

## Résultat principal

Au même jour civil, la moyenne OSHD est inférieure à SPASS pour **33 groupes sur 40**, supérieure pour 7. La différence moyenne médiane entre groupes vaut **−7,25 cm** ; l'écart absolu moyen médian est **9,38 cm**. Ce ne sont pas des erreurs par rapport à une vérité observée : on compare deux modèles.

| Date OSHD par rapport à SPASS | Différence moyenne médiane | Écart absolu moyen médian | Écart quadratique moyen, racine, médian |
|---|---:|---:|---:|
| −1 jour | −7,25 cm | 9,39 cm | 12,99 cm |
| Même jour — référence | −7,25 cm | 9,38 cm | 11,95 cm |
| +1 jour | −7,25 cm | 9,38 cm | 10,76 cm |

Chaque métrique est d'abord calculée sur les jours appariés d'un groupe ; le tableau donne ensuite la médiane des 40 métriques de groupe. Ce n'est ni une moyenne nationale des visiteurs ni un échantillon de 6 040 jours indépendants. Le CSV conserve les valeurs en mètres ; les centimètres servent seulement à la lecture du tableau. Le signe est toujours **OSHD moins SPASS**.

Les écarts ne sont pas uniformes : au même jour, la différence moyenne va de **−35,92 cm à Nax** à **+33,28 cm à Belalp**. Ces extrema décrivent l'ensemble conservé, sans sélectionner de « bonnes » stations. Un décalage d'un jour réduit l'écart quadratique médian, mais change à peine la différence moyenne : aucun décalage optimal n'est choisi.

## Ce que cela permet — et ne permet pas

L'hypothèse en mètres permet désormais les comparaisons physiques. Elle ne suffit pas à autoriser un raccordement : modèles, résolutions et assimilation diffèrent, les écarts changent de signe selon les groupes et un seul hiver est comparé. OSHD représente un état à 06 h CET fixes ; l'instant représenté par SPASS reste non certifié. La publication SPASS déconseille l'interprétation à haute résolution temporelle. Les corrélations quotidiennes et de variations des étapes 71–72 restent conservées, pas remplacées par ces écarts.

Aucune calibration, substitution de source, exclusion, modification des cinq hivers propres à chaque entrée, classification ou nouvelle estimation DiD n'a été effectuée.

## Prochaine décision : extension saisonnière proposée, non appliquée

Pour vérifier la compatibilité au niveau pertinent pour les profils, je propose de comparer les **moyennes décembre–avril des huit hivers communs 2015/16 à 2022/23**, par groupe et hiver : mêmes longueurs communes observées, moyenne des jours réellement appariés, nombres de jours et couvertures publiés, absence laissée manquante. Les trois décalages fixes seraient conservés, avec zéro comme référence. Les résultats resteraient séparés par hiver ; aucune année ne serait sélectionnée selon l'accord des modèles, aucune correction ou fusion ne serait automatique. Ces hivers de diagnostic ne remplaceraient pas les cinq hivers préentrée de chaque groupe.

L'inventaire public déjà archivé contient sept archives manquantes `OSHD_DATA_WY2016.zip` à `OSHD_DATA_WY2022.zip`, **4 507 509 648 octets (4,51 Go)**, avec tailles et MD5 fournis. L'archive WY2023 est déjà récoltée. Les fichiers couvrent des années hydrologiques septembre–août : WY2016 contient donc l'hiver 2015/16. Les en-têtes et jours disponibles devront être vérifiés après téléchargement. La collecte serait reprenable et ne referait pas les archives présentes.

**Validation demandée avant cette nouvelle agrégation saisonnière.** L'alternative est de limiter la comparaison au pilote disponible, mais celui-ci ne suffit pas à justifier le remplacement des hivers SPASS absents par OSHD. Il faudrait alors décider séparément de conserver les profils SPASS incomplets, sans les combler.

## Fichiers, sources et reprise

- [Détail par groupe et décalage](../data_processed/native_snow_metric_diagnostic_stage75.csv) : 210 lignes, unités, hypothèse, effectifs, couverture, écarts et corrélations antérieures.
- [Décision en mètres](../config/snow_metric_decisions_stage75.json), [résumé et empreintes](native_snow_metric_diagnostic_stage75_summary.json), [préservation](preservation_stage75_summary.json).
- Sources et preuves préexistantes : [unité SPASS](119_UNITE_HAUTEUR_NEIGE_SPASS_FR.md), [documentation temporelle et modèles](118_COMPATIBILITE_NEIGE_UNITES_TEMPS_FR.md), [données quotidiennes figées](native_snow_values_stage70_summary.json). Inventaire public OSHD : source `SLF_OSHD_RECORD_PUBLIC_HTML_2026_10_09`, original archivé sous `data_external/source_evidence/`, DOI `10.5281/zenodo.17313889` ; publication OSHD, §6. Aucun nouvel accès réseau pour cette étape.
- Registres : **1 218 sources et 8 291 champs**, ajouts seuls (+1/+30) ; toutes les anciennes lignes conservées. Journal de collecte inchangé : 1 585 événements. Le guide CSV scientifique a orienté la séparation explicite entre unité source, unité supposée, valeurs manquantes et vrais zéros.
- Vérification indépendante de toutes les 120 lignes calculées et des cas limites : **4 tests réussis** ; reprise du producteur identique. Préservation vérifiée : **2 375 références SHA / 1 792 fichiers distincts**. Le premier contrôle du journal comparait les octets Git/LF au fichier Windows/CRLF ; corrigé en comparaison exacte des cellules, sans modification du journal.

Reprise depuis la racine : `.venv/Scripts/python.exe -X utf8 src/descriptive/diagnose_native_snow_metrics_stage75.py`. Le producteur vérifie les empreintes et ne réécrit pas ses résultats figés. Tous les travaux lancés sont terminés ; aucune collecte active. À la reprise, traiter la réponse à l'extension saisonnière proposée, sans redemander l'hypothèse en mètres ni reprendre les anciennes questions d'unité.
