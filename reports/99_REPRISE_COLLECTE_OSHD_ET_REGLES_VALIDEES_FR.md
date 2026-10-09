# Neige et profils : règles validées et reprise

9 octobre 2026. Complément court au [bilan pistes et sources](98_SOURCES_PISTES_ET_NEIGE_BILAN_FR.md).

## Décisions enregistrées

- OSHD peut être étudié et collecté comme complément potentiel à SPASS. **Comparer avant de décider du raccordement** ; aucun raccordement ni calibration n’est validé.
- Pondération spatiale par la longueur des tracés uniques vérifiés, pour l’altitude, l’orientation du terrain et la neige. Ce n’est pas l’orientation du trajet des skieurs.
- Neige : moyenne des jours observés par hiver, puis poids égal aux **cinq hivers propres à chaque entrée**. Un hiver entièrement absent laisse la moyenne des cinq hivers manquante ; pas de moyenne de quatre hivers présentée comme cinq, ni exclusion du groupe.
- Couvertures publiées ; aucun seuil automatique de couverture ou filtre de groupe. Résolution du relief, terrain plat, surfaces sans axe et correspondances précises aux pistes restent à définir avant extraction.

Réponses conservées dans `config/winter_profile_aggregation_decisions_stage45.json`. Les 71 groupes et les résultats précédents restent inchangés ; aucune classification ou nouvelle estimation DiD.

## Vérification et collecte réelle

Le HTML public original du [dépôt SLF](https://zenodo.org/records/17313889) contient explicitement `cc-by-4.0`, les liens, tailles et MD5 des fichiers. L’extraction web avait omis cette licence et n’affichait que le copyright. La page méthodologique est également archivée. L’API générale du dépôt est interdite par `robots.txt` et n’a pas été appelée ; les téléchargements publics autorisés sont utilisés.

Premier lot utile : 2024/2025 pour les saisons absentes de SPASS ; 2023 pour le dernier hiver commun déjà présent dans l’ancienne extraction SPASS de 15 composantes. Ce choix de collecte ne constitue pas une sélection de groupes ou une méthode de comparaison spatiale.

| Archive originale | Taille attendue | État à ce point de reprise |
|---|---:|---|
| WY2024 | 645 601 691 octets | 216 006 656 octets conservés en fichier partiel ; erreur temporaire 504 |
| WY2025 | 579 028 796 octets | Pas de fichier complet ; tentative 504 |
| WY2023 | 569 361 906 octets | Pas de fichier complet ; tentative 504 |

**0 archive complète sur 3** : aucun nouveau NetCDF extrait, aucune valeur neige calculée. Un fichier partiel n’est pas une source originale validée. La reprise par blocs de 8 Mo a fonctionné sur six plages exactes HTTP206, ajoutant 50 331 648 octets, puis le serveur a de nouveau renvoyé 504. Aucun octet déjà reçu n’a été supprimé. Pas de boucle de relance après échec ni de contournement d’un refus d’accès.

## Reprendre sans recommencer

Depuis la racine :

```powershell
.venv/Scripts/python.exe src/data_collection/collect_oshd_profile_audit.py --resume-failed --max-seconds 300
```

Le drapeau de reprise autorise une nouvelle tentative après interruption **non liée aux permissions**, pas après HTTP401/403. Sans ce drapeau, les échecs restent signalés et ne sont pas relancés. Un verrou système refuse les collectes concurrentes. Les plages sont vérifiées avant ajout ; une session peut se mettre en pause. Promotion dans `data_external/source_evidence/` seulement après taille exacte, MD5 fournisseur et SHA256. Les fichiers partiels restent dans `data_interim/oshd_profile_downloads/`.

État détaillé : `reports/oshd_profile_audit_collection_summary.json`. Sources et échecs dans les registres et le journal de collecte. Tous les anciens enregistrements de provenance sont conservés : **383 sources uniques, 7 381 champs au dictionnaire**. Validation finale : **236 tests réussis**, un avertissement préexistant. Aucun collecteur encore actif à la fin de cette étape.

Suite : terminer les fichiers utiles ; vérifier leurs variables, unités et calendrier ; rattacher et dédoublonner les pistes des 71 groupes avec audit historique. Puis préciser les détails techniques ouverts et comparer les modèles sur un périmètre cohérent avant de te proposer le raccordement. Pas de remplacement de SPASS, classification ou estimation décidé selon la significativité.
