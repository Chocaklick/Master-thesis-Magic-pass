# SPASS–OSHD : concordance des évolutions quotidiennes

10 octobre 2026 — ta décision est appliquée : **Spearman par groupe aux trois décalages fixés**, sans convertir SPASS, comparer les écarts en mètres ou raccorder les modèles. Les anciens résultats et les cinq hivers propres à chaque entrée restent inchangés.

## Résultat

Pour décembre 2022–avril 2023, **40 groupes ont chacun 151 paires quotidiennes calculables**. Les 30 autres restent dans le fichier avec un motif d’indisponibilité, jamais avec une corrélation artificiellement nulle. Aucun groupe n’est exclu.

| Date OSHD par rapport à SPASS | Médiane des 40 corrélations | Quartiles 25–75 % | Minimum–maximum |
|---|---:|---:|---:|
| Jour précédent | 0,698 | 0,593–0,790 | 0,085–0,896 |
| Même jour civil : référence | 0,783 | 0,678–0,852 | 0,166–0,924 |
| Jour suivant | 0,838 | 0,742–0,902 | 0,244–0,954 |

Ce sont des résumés descriptifs **entre groupes**, pas une corrélation regroupant tous les jours/stations. La référence demeure le même jour civil. Le jour suivant concorde davantage pour 39 groupes sur 40 ; ce constat ne choisit pas automatiquement un décalage et ne prouve pas qu’une date source est erronée. Les horaires et unités temporelles originaux restent conservés.

La concordance varie nettement : au même jour, Mayens de Conthey vaut 0,166, Axalp 0,306 et Gspon 0,385. Ces cas restent présents. **Aucun seuil de « bon accord », filtre de stations ou choix selon la significativité** n’est introduit. Melchsee-Frutt conserve ses 151 paires mais seulement 86,35 % de longueur commune observée ; la couverture des 39 autres groupes est complète.

[Détail de tous les groupes et décalages](../data_processed/native_snow_rank_diagnostic_stage71.csv) · [Graphique en ordre alphabétique](native_snow_rank_diagnostic_stage71.png). La figure montre les 40 groupes calculables ; le CSV conserve les 70 groupes, soit 210 lignes.

## Calcul et interprétation

Pour chaque groupe/décalage, on classe les **moyennes quotidiennes déjà calculées sur exactement les mêmes portions de pistes observées** dans les deux grilles natives. Les ex æquo reçoivent leur rang moyen. Spearman est la corrélation de Pearson de ces deux suites de rangs. Les valeurs sources, masques, vrais zéros et poids de pistes ne sont pas modifiés. Aucune nouvelle interpolation, conversion, sélection de dates ou transformation des séries.

Le coefficient ne dépend pas d’une conversion positive uniforme telle que mètres vers centimètres. Cela permet ce diagnostic **sans certifier l’unité inconnue de SPASS**. Une série constante, moins de deux paires finies ou des axes absents donnent une corrélation manquante et un statut explicite, pas zéro. Ici les 120 coefficients groupe–décalage sont calculables ; les effectifs, valeurs distinctes et jours ex æquo/zéro sont publiés.

**Limites importantes :**

- Une forte corrélation de rang ne garantit pas les mêmes hauteurs de neige. Elle ne donne ni biais, erreur en mètres, équivalence des résolutions, preuve d’unité ou autorisation de raccordement.
- Les deux modèles peuvent suivre le même cycle saisonnier, notamment la fonte. Ce calcul sur les niveaux quotidiens ne démontre pas qu’ils reproduisent les mêmes chutes de neige ou variations rapides. Aucun détrendage ni différenciation n’est présumé.
- Les jours sont dépendants dans le temps. Aucun test standard supposant 151 jours indépendants ni intervalle de confiance non validé n’est présenté. 151 jours ne signifient pas 151 stations indépendantes.
- Une seule saison commune ne certifie pas la stabilité interannuelle. Les tracés actuels restent des proxies historiquement qualifiés, pas un domaine exhaustif vérifié avant chaque entrée. Ce diagnostic n’est pas un effet Magic Pass ni un profil préentrée définitif.

## Suite méthodologique proposée, désormais validée

Pour vérifier que la concordance ne reflète pas surtout le cycle saisonnier, on peut **compléter**, sans remplacer cette référence, par Spearman sur les variations entre deux jours consécutifs. Les trois décalages et les mêmes groupes restent fixes. Chaque variation utilise uniquement deux journées consécutives réellement observées, sans combler de trou, soit au plus 150 paires par groupe/décalage dans ce pilote. Une variation constante reste non calculable.

Ce diagnostic répond à une autre question : les modèles reproduisent-ils les mêmes hausses et baisses quotidiennes ? Il est plus sensible au bruit journalier et ne résout toujours ni les unités, ni les écarts absolus, ni le raccordement. **Validé le 10 octobre 2026 : « Oui, ajouter ce diagnostic, sans remplacer celui sur les niveaux quotidiens (recommandé). »** Il sera produit séparément en Stage72, en conservant intégralement cette référence Stage71. Aucun de ces choix ne remplace tes cinq hivers ou ne fusionne automatiquement SPASS et OSHD.

## Sources et reprise

Source dérivée `DERIVED_NATIVE_SNOW_RANK_DIAGNOSTIC_STAGE71`, configuration `config/snow_rank_diagnostic_decisions_stage71.json`. Sources parentes SLF/OSHD/EnviDat et droits déjà documentés dans le [bilan précédent](115_NEIGE_GRILLES_NATIVES_ET_COUVERTURE_FR.md), sans nouvelle collecte. **1 202 sources et 8 216 champs uniques** après ajout d’une source dérivée et 28 variables, anciens registres intacts.

Six tests spécifiques réussis : rangs ex æquo/zéros/manquants, séries constantes, invariance à une conversion positive uniforme, tous les coefficients recalculés par une définition indépendante des rangs, calendrier/doublons, couverture et anciens registres. Suite complète : **369 tests réussis**, un avertissement pandas/NumPy hérité sans échec. Préservation : **2 298 références SHA / 1 748 fichiers**, tous les 1 201 anciens enregistrements sources et 8 188 anciens champs exacts ; 1 569 événements de collecte inchangés. Figure contrôlée visuellement. Le guide CSV scientifique a servi à conserver des champs typés et les statuts/couvertures explicites.

Reprise sans réseau ni répétition des lectures de neige :

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/diagnose_native_snow_ranks_stage71.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_preservation_stage71.py
```

Le calcul réutilise les CSV quotidiens figés et contrôle leurs empreintes. La figure déjà produite est conservée, pas à régénérer lors d’une reprise inchangée. Utiliser le dernier contrôle Stage71 : les anciens comptes Stage70 sont historiques. État et journal actualisés, aucun nouveau clustering ou effet DiD.
