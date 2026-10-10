# Unité de la hauteur de neige SPASS

10 octobre 2026. Fichier examiné : `HSCLQMD_ch01h.swiss.lv95_WY_1962_2023.nc`, ressource EnviDat `688d1caf-ed63-4cb8-8579-8c017bb7458c`.

**Le mètre (m) est l’encodage nettement le mieux étayé.** Les vérifications numériques et le logiciel convergent vers cette interprétation. La réserve exacte reste l’absence de déclaration d’unité propre au fichier distribué : je n’ai pas trouvé de nouvelle preuve documentaire permettant de présenter cette conclusion comme certifiée par le producteur.

Une valeur brute `0,75` correspondrait donc à **0,75 m = 75 cm**. Le facteur pour afficher des centimètres est 100.

## Les éléments concrets

L’[API officielle SWE2HS](https://git-pages.wsl.ch/aschauer/swe2hs/_autosummary/swe2hs.two_dimensional.convert_2d.html) donne `hs_output_unit='m'` par défaut. Le [code](https://git-pages.wsl.ch/aschauer/swe2hs/_modules/swe2hs/two_dimensional.html) permet néanmoins d’autres unités : ce défaut seul ne prouve pas le paramètre de production SPASS.

Le contrôle porte aussi sur **les 11 stations distinctes déjà comparées sur dix hivers**, toutes conservées. Exemples de moyennes novembre–avril :

| Station | Moyenne SPASS brute* | Si l’unité est m : SPASS en cm | Mesure station en cm |
|---|---:|---:|---:|
| Homad | 0,8203 | 82,03 | 76,91 |
| Bréona | 0,7253 | 72,53 | 83,55 |
| Schmidigen-Bidmeren | 0,9102 | 91,02 | 112,99 |
| Donin du Jour | 1,3111 | 131,11 | 171,91 |

*Moyennes brutes retrouvées en annulant exactement le ×100 explicite de l’ancien calcul ; il ne s’agit pas d’une nouvelle extraction. Le détail des 11 stations est conservé dans [le résultat reproductible](spass_unit_investigation_stage74.json). Les observations de stations et les grilles voisines ne sont pas identiques, et le modèle utilise en partie le réseau SLF. Ce contrôle établit la plausibilité de l’échelle, pas une validation indépendante des modèles. Lire ces valeurs brutes comme des centimètres donnerait ici seulement 0,73 à 1,31 cm pour des moyennes mesurées de 77 à 172 cm.

Les valeurs quotidiennes brutes Stage70, vérifiées séparément au décalage de référence zéro, sont également de l’ordre de celles du produit OSHD documenté en mètres. Aucun décalage n’a été choisi pour améliorer cette concordance.

## Recherche documentaire complémentaire

Les [métadonnées complètes EnviDat de la ressource HS](https://www.envidat.ch/api/3/action/resource_show?id=688d1caf-ed63-4cb8-8579-8c017bb7458c) et [du jeu SPASS](https://www.envidat.ch/api/3/action/package_show?id=spass---new-gridded-snow-datasets-for-switzerland) ont été récupérées et archivées : elles identifient le fichier exact mais omettent l’unité. Le catalogue n’a que deux ressources, SWE et HS, sans notice supplémentaire. La recherche publique WSL ne retourne aucun projet nommé SPASS ; le dépôt SnowQM accessible a 96 entrées et concerne le SWE, sans script de génération HS identifié. Cela ne dit rien des dépôts privés ou non indexés.

Les centimètres de la [publication SPASS, section 2.4](https://tc.copernicus.org/articles/19/4391/2025/) sont ceux de ses analyses et graphiques ; ils ne suffisent pas à établir l’encodage numérique du NetCDF. L’attribut d’unité y reste absent. Le précédent bilan était donc trop peu utile en ne donnant que « UNKNOWN » : il devait aussi expliciter l’hypothèse **mètres fortement étayée**, sans la confondre avec une preuve directe.

Six réponses publiques JSON archivées, HTTP200/SHA-256 et sources enregistrés ; aucune nouvelle grille téléchargée. Les anciens résultats, valeurs, unités sources et profils restent inchangés. Reprise : `.venv/Scripts/python.exe -X utf8 src/descriptive/investigate_spass_unit_stage74.py`. Aucun nouveau choix d’estimation ou raccordement n’est effectué par cette recherche d’unité.

Correction factuelle au brouillon précédent : l’auteur correspondant s’appelle **Christoph Marty**, pas Christian.
