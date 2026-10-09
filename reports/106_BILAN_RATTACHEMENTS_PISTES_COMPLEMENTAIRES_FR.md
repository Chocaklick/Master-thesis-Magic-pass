# Rattachement des pistes : bilan complémentaire

10 octobre 2026. Option 1 validée : identité de la station, sources officielles et contrôle géographique individuel. Les nuitées restent communales ; aucun panel ou résultat DiD n’est modifié.

## Résultat

**24 correspondances actuelles supplémentaires, soit 39 sur 71. Les 32 groupes non résolus restent conservés.** Les 15 lignes déjà validées sont inchangées. Il s’agit de correspondances entre groupes et sites OSM actuels, pas d’une certification de chaque piste, de l’exhaustivité du domaine ou de son périmètre avant l’entrée.

Les nouveaux cas sont : Heimenschwand, Jaun, Les Paccots, Les Pléiades, Marbachegg, Melchsee-Frutt, Moléson, Nax, Moosalp, Ottenleue, Prés-d’Orvin, Rathvel, Rossberg, Rosswald, Rüschegg, Sainte-Croix/Les Rasses, Selital, Schwarzsee, Sörenberg, Gspon, Vercorin, Visperterminen, Crans-Montana et Lauchernalp.

423 objets OSM de descente supplémentaires sont rattachés à ces sites, pour 710 au total. **Ce ne sont pas 710 pistes distinctes ni des kilomètres mesurés.** Sainte-Croix est reconnue grâce aux remontées mais sa relation ne contient aucune géométrie de descente : cela ne signifie pas qu’il n’y a pas de ski alpin.

[Table complète des 71 groupes](../data_processed/winter_profile_piste_assignment_stage53.csv). [Preuves, identifiants, limites et empreintes](piste_assignment_stage53_summary.json). Sept planches de contrôle, 38 vues candidates, sont référencées dans ce fichier.

## Méthode et sources

1. Parcourir les 56 groupes non résolus et réutiliser les liens exacts déjà archivés, sans nouvel appariement automatique par nom ou distance.
2. Archiver les pages publiques autorisées et les liens de périmètre réellement présents dans leurs contenus. Réutiliser le cache avec contrôle SHA-256 ; vérifier TLS et robots ; conserver les échecs.
3. Pour les liens périmés ou insuffisants, rechercher des sources officielles alternatives. Les six recherches sont archivées avec leurs URLs et identifiants de requête dans le [journal de découverte](piste_source_discovery_stage53.json). Les résultats de recherche ne remplacent jamais le contenu primaire.
4. Vérifier individuellement les réseaux de descentes/remontées et les références existantes sur cartes LV95, avec notes par cas et contrôles d’identifiants originaux. Aucun rayon de sélection, découpage, remplacement de coordonnées ou retrait de groupe.

77 nouvelles pages HTML originales ont été archivées ; trois pages existantes réutilisées. Les sources et les 19 champs de la nouvelle table sont inscrits dans les registres du projet. Les originaux OSM et les deux étapes précédentes restent intacts.

Les restrictions locales sur les sockets et deux erreurs d’encodage d’URL ont été distinguées des réponses des fournisseurs ; les essais restent dans le journal. Les accents sont encodés conformément aux URI sans modifier les URLs sources. Un ancien 404 ne rend pas tout son domaine interdit : une nouvelle URL officielle effectivement découverte peut être vérifiée, sans retenter l’ancien chemin. Les refus 403, robots, TLS et la réponse 502 ne sont pas contournés.

## Points importants

| Cas | Constat et traitement |
| --- | --- |
| Eischoll / Unterbäch | L’opérateur d’Eischoll décrit une liaison skiable. Entrée commune en 2023/24, mais deux groupes existants. Vérification historique/regroupement soumis au chercheur ; aucune fusion appliquée. |
| Schwanden / Wilerallmi | Une relation OSM contient la remontée de Wilerallmi, conservée comme groupe distinct. Pas d’attribution intégrale à Schwanden. |
| Rossberg | Deux relations contiennent exactement les mêmes trois descentes et remontée. Identifiants conservés ; relation portant le lien de l’opérateur retenue une fois. |
| Moosalp | L’opérateur annonce l’arrêt du Blattlift décidé le 22 avril 2025, dernière exploitation en 2021/22. Sa présence OSM n’établit pas son exploitation actuelle. |
| Sörenberg | Source : Rischli/Brunnenboden non exploités en 2025/26 ; Ochsenweid utilisé comme accès. Ne pas convertir tous les membres OSM en installations actives. |
| Ottenleue | Site reconnu indépendamment ; référence d’accès éloignée dans la carte, anomalie conservée. Aucun déplacement du point ni recalcul routier. |
| Crans-Montana | Interdiction robots du site touristique respectée. Source originale indépendante de l’exploitant CMA utilisée pour l’identité actuelle ; sortie du Magic Pass inchangée. |
| Lauchernalp | Le contenu primaire actuel indique 2026/27 alors que l’index de recherche mentionnait 2025/26 : l’original archivé fait référence. |

Les réserves concernent aussi des domaines partiels (Niederhorn/Hohwald, Gurnigel/Gurnigelbad, Vallée de Joux…), un domaine transfrontalier (La Dôle), de mauvaises correspondances proposées par proximité (Torrent/Gemmipass, Gstaad/Wasserngrat), des sources indisponibles (Marécottes, Mörlialp), un site contenant du texte de démonstration (Riffenmatt), et des pistes sans relation de site vérifiée. Chaque groupe possède sa propre note de reprise ; aucun cas n’est exclu.

## Reprise

277 tests réussis en 92,31 secondes (un avertissement pandas hérité). Audit de préservation : 537 références SHA-256 sur 272 fichiers antérieurs, plus 171 empreintes de cette étape, conformes. Les 500 anciennes sources et 7 518 anciens champs sont strictement identiques ; registres actuels : 586 sources et 7 537 champs uniques. Le contrôle distingue les anciens formats à empreinte unique des dictionnaires d’empreintes, en utilisant les chemins définis dans leurs scripts originaux.

Le chercheur a ensuite validé la recherche de preuve de liaison Eischoll–Unterbäch **antérieure à leur entrée**, puis une proposition de regroupement si elle est confirmée. Cela n’autorise pas encore une fusion.

Rejouer hors réseau `src/descriptive/verify_piste_assignments_stage53.py`, puis `src/descriptive/check_piste_preservation_stage53.py`. Ne pas modifier les configurations, scripts et sorties déjà figés. Continuer dans un nouvel espace d’étape : contrôle des objets axes/surfaces, doublons et historique, puis compléments des 32 groupes. Pas encore de nouvelles variables de terrain/neige, clustering ou effets par profil. Toute nouvelle règle méthodologique reste soumise à validation.
