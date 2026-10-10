# Tronçons uniques et contexte des profils

10 octobre 2026 — Application de la décision : « Compter une seule fois les portions exactement superposées, avec comparaison conservée ».

## Résultat

Les **70 groupes** et les **773 objets OSM** restent conservés : 765 axes candidats et 8 surfaces. Les portions exactement superposées sont comptées une seule fois dans chaque groupe. La somme des longueurs par identifiants reste disponible pour comparaison. Aucun rapprochement par distance, déplacement, arrondi des coordonnées, réparation ou exclusion automatique.

**Sept groupes** ont de véritables portions communes : Belalp, Lauchernalp, Crêt-du-Puy, Meiringen–Hasliberg, Nax, Vercorin et Eischoll–Unterbäch. Leur union représente environ **369 m de portions partagées**, correspondant à **380 m de poids répété évité**. Ces chiffres diffèrent lorsqu’un tronçon appartient à plus de deux axes.

La mesure porte sur le **réseau candidat actuellement cartographié**, pas sur des kilomètres exhaustifs ou certifiés avant l’entrée dans Magic Pass. 39 groupes disposent d’axes cartographiés ; Sainte-Croix–Les Rasses a une correspondance vérifiée mais aucun axe référencé dans son site OSM, ce qui ne signifie pas zéro piste réelle. Les 30 correspondances non résolues restent présentes avec longueurs manquantes.

## Méthode et contrôles

Les géométries proviennent des deux originaux OSM déjà archivés ; leurs empreintes, types, identifiants et versions sont contrôlés. Projection EPSG:2056 identique à l’audit précédent, puis union géométrique des axes par groupe, sans grille de précision ni tolérance. Les huit surfaces explicites ont une union d’aire séparée : ni leur périmètre ni un axe inventé n’alimentent les longueurs.

Un contrôle supplémentaire vérifie directement les intersections linéaires : un croisement ponctuel ne constitue pas une superposition. La liste des différences brutes de l’étape 58 comprend aussi des résidus d’arithmétique flottante, au maximum 2,2 × 10⁻¹¹ m sans chevauchement. **L’étape 59 fait foi pour identifier les groupes réellement concernés** ; les différences brutes antérieures sont conservées, sans introduire de tolérance géographique.

Les deux objets de Moosalp portant des tags d’abandon sont conservés et signalés. Leur validité pour un profil préentrée reste à vérifier ; aucune acceptation individuelle ou suppression automatique. Les couvertures lacunaires et la réserve historique demeurent visibles. Pas de nouveau clustering, caractéristique de relief/neige finale, raccordement de modèles ou estimation DiD à cette étape.

## Calendriers de neige et accès urbain

Le contexte a été reporté vers les 70 groupes sans modifier les règles validées : **420 temps urbains détaillés**, minimum parmi les six villes et **350 calendriers hivernaux**, cinq propres à chaque entrée. Les valeurs et dates des 69 groupes non concernés sont identiques aux anciennes. Pour Eischoll–Unterbäch, les hivers commencent en 2018, 2019, 2020, 2021 et 2022.

Les 23 hivers hors couverture temporelle SPASS demeurent signalés. Un calendrier disponible n’est pas une moyenne de neige observée : aucun jour, unité, modèle de remplacement ou raccordement n’est inventé. L’incertitude sur l’unité source SPASS et la comparaison avec OSHD restent à résoudre avant combinaison.

## Fichiers, sources et reprise

- [Longueurs comparées et surfaces](../data_processed/winter_profile_exact_piste_overlap_stage58.csv).
- [Vérification des vrais chevauchements](../data_processed/winter_profile_overlap_geometry_stage59.csv).
- [Temps urbains](../data_processed/winter_profile_urban_city_detail_stage57.csv) et [minimum des six villes](../data_processed/winter_profile_urban_minimum_stage57.csv).
- [Cinq hivers par groupe](../data_processed/winter_profile_approved_snow_windows_stage57.csv).
- Décision : `config/piste_exact_overlap_decisions_stage58.json`. Géométries uniques en WKT EPSG:2056 et tous les membres originaux : `data_interim/winter_profile_exact_network_stage58.json`.

Sources dérivées `DERIVED_CONNECTED_PROFILE_CONTEXT_STAGE57`, `DERIVED_EXACT_PISTE_OVERLAP_STAGE58` et `DERIVED_EXACT_OVERLAP_GEOMETRY_STAGE59` inscrites dans le registre ; toutes les variables CSV sont définies dans le dictionnaire. Pas de nouvelle collecte externe. Filiation aux sources OSM originales et aux résultats routiers conservée dans les manifestes SHA des étapes 57–59.

Rejouer depuis la racine, hors réseau et sans remplacer les anciens résultats :

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/build_connected_profile_context_stage57.py
.venv/Scripts/python.exe -X utf8 src/descriptive/audit_exact_piste_overlap_stage58.py
.venv/Scripts/python.exe -X utf8 src/descriptive/verify_exact_overlap_geometry_stage59.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_piste_preservation_stage59.py
```

Suite : poursuivre les 30 périmètres non résolus et le contrôle historique des objets ; préparer le relief swissALTI3D 2 m. La règle d’extraction le long des axes et le traitement de l’exposition des terrains quasi plats doivent être présentés au chercheur avant calcul. Les modèles neige, catégories de profils et nouvelles estimations gardent leurs validations distinctes.
