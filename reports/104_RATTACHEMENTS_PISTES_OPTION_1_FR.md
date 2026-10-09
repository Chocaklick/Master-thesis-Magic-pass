# Pistes : premiers rattachements vérifiés — option 1

9 octobre 2026. La réponse « tu peux faire l'option 1 » valide la vérification individuelle : identité/composantes, preuves officielles de l’opérateur et cohérence géographique des pistes/remontées. Aucun rapprochement automatique par nom ou distance.

## Résultat du premier lot

**5 correspondances actuelles site OSM → groupe vérifiées**, sur les **71 groupes conservés**. Les 66 autres restent à vérifier, pas exclus. Les 185 territoires communaux et les anciens groupes de remontées sont inchangés. Ce travail ne modifie aucune exposition communale ni estimation DiD.

| Groupe | Relation OSM | Objets de descente membres | Remontées membres connues | Preuves et réserves |
|---|---:|---:|---:|---|
| Mayens de Conthey | 19914387 | 2 | 1 | Téléconthey nomme les Ombrins ; géométrie des deux descentes cohérente avec cette remontée |
| Saas-Fee | 3609152 | 49 | 19 | Page hivernale propre à Saas-Fee et installations Alpin Express/Felskinn/Spielboden ; ne pas étendre à toute la vallée |
| Belalp | 15310559 | 95 | 10 | Liaison Blatten–Belalp et Sparrhorn confirmés par l’opérateur, cohérents avec le réseau cartographié |
| Linden | 9210387 | 3 | 2 | Identité Schindelberg AG confirmée ; l’opérateur annonce trois remontées : couverture OSM incomplète ou incertaine |
| Meiringen–Hasliberg | 3578623 | 57 | 10 | Branches Meiringen–Reuti, Twing–Lischen–Käserstatt et Mägisalp corroborées ; groupe relié conservé |

Les **206 objets de descente** sont des membres OSM uniques dans ce lot, pas 206 pistes distinctes ni des kilomètres. Le rattachement du site est vérifié ; **la validité de chaque axe/surface pour les mesures reste à contrôler**. Les nœuds non demandés restent signalés (24 Meiringen, 14 Saas-Fee). Aucune couverture exhaustive du domaine réel n’est certifiée.

Saas-Fee contient aussi 18 objets nordiques, conservés séparément, sans les ajouter aux pistes alpines. Le signalement OSM de reconstruction de Hannig en 2024 et de coordonnées à actualiser est conservé comme **alerte source**, pas une vérification indépendante du changement. La page complémentaire « Anlagen » de Linden a renvoyé HTTP500 : erreur enregistrée, pas de nouvelle tentative ; sa page d’accueil reste disponible.

## Méthode et traçabilité

1. Joindre les groupes aux pages Magic Pass par identifiants stables, puis reprendre leur lien exact « Site web ». Archiver les pages et sous-pages réellement liées, avec date, robots et SHA256.
2. Comparer les composantes et installations nommées à la relation OSM et à ses membres récursifs. Conserver noms, versions, dates d’édition et deux instantanés originaux ; ne pas écraser les objets ou confondre une date d’édition avec une date de construction.
3. Examiner individuellement la carte LV95 des membres de descente, remontées et points de référence existants. Consigner le constat par cas ; aucun rayon, découpage communal ou point de référence remplacé.
4. Publier une ligne pour chaque groupe, y compris ceux non résolus. Pour ceux-ci, les comptes inconnus restent vides, jamais zéro. Les anciens audits restent inchangés.

[Table complète — 71 groupes](../data_processed/winter_profile_piste_assignment_stage51.csv) · [Contrôle géographique](figures/piste_assignment_geographic_review_stage51.png) · [Preuves, identifiants et empreintes](piste_assignment_stage51_summary.json). Décision : `config/piste_assignment_protocol_decisions_stage51.json` ; constats individuels : `config/piste_assignment_cases_stage51.json`. Sources et champs sont enregistrés dans les deux registres de métadonnées.

Sources principales : [Téléconthey](https://www.teleconthey.ch/www/1-accueil), [horaires hivernaux de Saas-Fee](https://www.saas-fee.ch/fr/services-informationen/tarifs-et-horaires-des-remontees-mecaniques/horaires-des-remontees-mecaniques/horaires-des-remontees-mecaniques/hiver/saas-fee), [Belalp](https://www.belalp.ch/fr/horaires), [Linden](https://www.skilift-linden.ch/home), [Meiringen–Hasliberg](https://meiringen-hasliberg.ch/Infos/betriebszeiten). Les descriptions actuelles ne certifient pas les tracés préentrée ; leurs droits sont distincts de la licence ODbL des données OSM.

## Suite et reprise

Poursuivre la même revue pour les 66 groupes restants, puis contrôler axes/surfaces, chevauchements et changements historiques avant les profils. Les choix supplémentaires de réparation, seuil de terrain plat ou comparaison spatiale de neige restent à valider. Aucune classe, moyenne neige, fusion de modèles ou nouvelle estimation n’a été calculée.

En parallèle, les trois archives neige WY2023/2024/2025 sont complètes et les **36 fichiers mensuels** ont été contrôlés au niveau métadonnées/coordonnées/empreintes. Pas encore de comparaison numérique SPASS–OSHD ; l’unité originale SPASS reste non renseignée.

Reprise locale de la vérification : `.venv/Scripts/python.exe src/descriptive/verify_piste_assignments_stage51.py` ; elle exige les mêmes empreintes et ne fait aucun appel réseau. Le collecteur refuse de réinterroger une source ayant échoué ; les pages déjà obtenues sont mises en cache. Tests et sauvegarde finale : `PROJECT_STATE.md` et `logs/research_journal.md`.
