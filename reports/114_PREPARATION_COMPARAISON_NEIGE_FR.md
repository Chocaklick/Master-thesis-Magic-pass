# Neige : ce qui est prêt et les choix restant à valider

10 octobre 2026 — suite du [relief étendu à 40 groupes](113_RELIEF_ET_JONCTIONS_DE_MILLESIMES_FR.md), sauvegardé dans `ad80e4c`. **70 groupes et 185 territoires restent conservés.** Aucun raccordement SPASS–OSHD, conversion nouvelle, clustering ou effet DiD.

## Vérifications effectuées

- Tes **350 fenêtres groupe–hiver**, soit cinq hivers décembre–avril propres à chaque entrée, sont inchangées et entièrement antérieures à l’entrée correspondante.
- 327 fenêtres sont dans le calendrier SPASS ; les **23 absentes** sont couvertes par les dates des archives OSHD déjà téléchargées. Ce n’est pas encore une couverture de valeurs valides sur les pistes.
- Les trois ZIP OSHD complets contiennent **36 mois**, soit 1 096 dates quotidiennes. L’intersection avec SPASS comprend septembre 2022–août 2023 ; **décembre 2022–avril 2023 offre 151 dates communes** pour un premier diagnostic.
- Les axes des 40 groupes disponibles sont à l’intérieur des enveloppes de coordonnées des deux grilles. Cela ne valide ni chaque cellule de neige, ni l’exhaustivité des pistes. Les 30 groupes sans axes utilisables restent présents avec des champs manquants.

[Audit — une ligne par groupe](../data_processed/snow_comparison_readiness_stage68.csv) · [Calendriers et grilles vérifiés](snow_comparison_readiness_stage68_summary.json). Aucune valeur du champ neige n’a été lue dans cet audit ; seuls les métadonnées, dates et tracés préservés sont utilisés.

## Une unité qui ne doit pas être inventée

OSHD déclare `unit = m`. SPASS n’a pas d’attribut d’unité pour `HSCLQMD`. L’[article des producteurs, section 2.4](https://tc.copernicus.org/articles/19/4391/2025/) présente ses analyses de hauteur de neige en centimètres et renvoie au [même jeu EnviDat](https://www.envidat.ch/metadata/spass---new-gridded-snow-datasets-for-switzerland), mais les passages consultés ne certifient pas l’échelle numérique stockée dans le fichier.

L’ancienne interprétation en mètres, basée notamment sur les ordres de grandeur, reste donc **une inférence distincte de l’unité fournisseur**. Aucun ancien résultat n’est modifié et aucune nouvelle conversion n’est appliquée. Les poids géométriques peuvent être préparés indépendamment de cette unité ; une comparaison en mètres/centimètres doit attendre une justification explicite de l’échelle. Une bonne corrélation ne suffirait pas à certifier cette échelle ou à autoriser un raccordement.

## Deux décisions demandées, non appliquées

**1. Comparaison spatiale.** Proposition : traverser les mêmes axes uniques dans chaque grille native — SPASS 1 km, OSHD 250 m — avec des longueurs exactes, sans interpolation. Comparer les moyennes sur les seules portions où les deux modèles ont des valeurs observées, publier la couverture et garder tous les groupes. Cela correspond au profil de pistes recherché ; une partie des différences restera liée aux résolutions. Alternative : agréger OSHD par surface à 1 km avant comparaison, pour harmoniser l’échelle mais perdre le détail local. Il faudra alors définir explicitement les cellules fines manquantes ; aucune règle de remplissage n’est présumée.

**2. Dates.** Proposition : apparier les dates civiles et conserver les horaires sources (SPASS 0 h, OSHD 6 h), avec diagnostic de sensibilité à un décalage d’un jour. Ce n’est pas une observation simultanée garantie. Alternative : ne comparer que les moyennes de l’hiver commun, sans diagnostic quotidien, moins informatif sur les écarts temporels.

Le diagnostic 2022/23 concerne la **compatibilité des modèles**, pas un nouveau profil préentrée identique pour toutes les stations. Tes cinq hivers restent propres à l’entrée. Une seule saison commune ne certifiera pas la stabilité des différences entre modèles ; aucun seuil de « bon accord », raccordement, calibration ou filtre de groupes ne sera choisi selon les résultats.

## Sources, contrôle et reprise

Les sources du modèle OSHD et leur licence CC-BY4.0 restent celles du [dépôt SLF](https://zenodo.org/records/17313889), déjà archivées et vérifiées. La consultation primaire supplémentaire, ses limites et les 20 champs de diagnostic sont enregistrés dans les registres : **1 198 sources et 8 104 champs uniques**, anciennes lignes intactes. **353 tests réussis**, un avertissement préexistant ; 2 216 références SHA sur 1 700 fichiers préservés et 1 569 événements de collecte inchangés. Méthode/configuration : `config/snow_comparison_readiness_stage68.json`. L’état et la sauvegarde sont consignés dans `PROJECT_STATE.md` et le journal.

Reprise locale, sans téléchargement :

```powershell
.venv/Scripts/python.exe -X utf8 src/descriptive/audit_snow_comparison_readiness_stage68.py
.venv/Scripts/python.exe -X utf8 src/descriptive/check_preservation_stage68.py
```

Utiliser le dernier contrôle de préservation : les comptes des anciens contrôles Stage66/67 restent historiques. Après tes réponses, enregistrer la décision dans **une nouvelle version**, préparer les poids et le diagnostic selon le protocole validé, poursuivre la vérification d’unité ; ne pas modifier les fichiers figés ou relancer les téléchargements complets.
