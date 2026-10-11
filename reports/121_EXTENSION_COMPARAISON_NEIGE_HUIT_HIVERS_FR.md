# Extension neige : huit hivers communs

Actualisation du 11 octobre 2026 : **les huit hivers et les sept archives supplémentaires sont terminés**. Le [bilan final 122](122_BILAN_NEIGE_HUIT_HIVERS_ET_CHOIX_PROFILS_FR.md) remplace les indications d'avancement ci-dessous. Ce document conserve les checkpoints et incidents de collecte ; aucun travail achevé ne doit être recommencé.

10 octobre 2026 — Étape 76, **extension validée, collecte en cours**.

Point de reprise à 17 h 40 UTC : **cinq hivers calculés sur huit**, 2017/18, 2018/19, 2019/20, 2020/21 et 2022/23. Quatre nouvelles archives sont intégralement récoltées, tailles et MD5 fournisseur vérifiés : WY2018/2019/2020/2021. WY2016/2017/2022 restent incomplètes. Le collecteur 26316 reprend leurs préfixes, sans téléchargement depuis zéro. Le JSON de collecte reste la référence pour l'avancement ultérieur.

Le calcul 2017/18 a rencontré un manque de mémoire (allocation52,6MiB, puis1MiB), résolu en limitant les threads à un et le cache NetCDF à1MiB. **Calcul désormais terminé**, cinq caches existants réutilisés et avril/mai ajoutés ; aucune méthode ou valeur changée. Le lanceur `run_snow_multiwinter_low_memory_stage76.py` conserve le producteur numérique figé, reprend ses arguments et archive ses réglages/empreintes dans `snow_multiwinter_runtime_stage76_summary.json`. Aucun processus tiers ou service de sécurité n'est modifié ; fermer des applications n'est plus nécessaire à ce stade.

| Hiver calculé | Groupes calculables | Jours appariés par groupe | Médiane des écarts moyens OSHD − SPASS |
| --- | ---: | ---: | ---: |
| 2017/18 | 40 | 151 | −26,51 cm |
| 2018/19 | 40 | 151 | −10,61 cm |
| 2019/20 | 40 | 152 | −12,94 cm |
| 2020/21 | 40 | 151 | −9,90 cm |
| 2022/23 | 40 | 151 | −7,25 cm |

Ces médianes décrivent les différences entre modèles, pas leur erreur par rapport à la neige réelle. Les 30 autres groupes restent dans le tableau, avec leur absence de géométrie signalée. Cinq hivers ne suffisent pas à conclure sur les huit ni à autoriser un raccordement.

## Périmètre et calcul

Ta réponse « je valide » approuve le protocole proposé au [bilan précédent](120_COMPARAISON_NEIGE_METRES_FR.md) : les huit hivers décembre–avril 2015/16 à 2022/23. Les cinq hivers préentrée propres à chaque groupe restent inchangés : ces huit hivers servent uniquement à comparer les modèles.

Les nombres SPASS sont interprétés comme des mètres selon ta décision ; leur métadonnée originale d'unité reste `UNKNOWN`. OSHD déclare `m`. Pour chaque groupe, jour et décalage fixé −1/0/+1, les deux modèles sont pondérés par les longueurs des **mêmes portions de pistes observées dans leurs grilles natives**, sans interpolation. Les moyennes hivernales donnent ensuite le même poids aux jours réellement appariés. Les résultats sont séparés par hiver ; aucun décalage ou hiver n'est choisi selon l'accord des modèles.

Les 70 groupes sont conservés. L'absence de géométrie, une archive encore non récoltée, un jour manquant et une vraie hauteur nulle restent distincts. Les comptes de jours et couvertures spatiales sont publiés. Les hivers 2015/16 et 2019/20 ont 152 jours, les six autres 151. Les pistes actuelles gardent leur réserve historique.

## Collecte et reprise

Sept archives originales OSHD WY2016–WY2022, total **4 507 509 648 octets**, sont ajoutées dans une nouvelle version. La première collecte WY2023–2025 reste inchangée. Les liens, tailles, MD5 et droits CC-BY4.0 proviennent de la page publique Zenodo déjà archivée (source `SLF_OSHD_RECORD_PUBLIC_HTML_2026_10_09`, DOI `10.5281/zenodo.17313889`). Aucun appel à l'API interdite, compte ni frais.

Le nouveau collecteur vérifie les réponses HTTP206 et leurs intervalles exacts, respecte le délai robots de dix secondes, conserve les préfixes reçus et ne promeut un original qu'après vérification de sa taille et du MD5 fournisseur. Le SHA256 et les membres ZIP sont enregistrés. Les refus HTTP401/403 arrêtent la reprise ; les échecs restent dans le journal. Une erreur transitoire 504 a interrompu la première tentative après **301 989 888 octets** : reprise explicite à cet endroit avec des portions de 8 Mo, sans effacer l'échec ni recommencer depuis zéro.

Les trois voies publiées pour WY2016 (ancre `?download=1`, lien canonique, lien `files/.../content`) ont rencontré au total quatre erreurs HTTP504, avec **369 098 752 octets** conservés. L'URL de contenu est littéralement présente dans les métadonnées publiques archivées. La règle robots `Allow: /api/records/*/files` la permet, contrairement à l'API générale : priorité du chemin le plus spécifique et caractères génériques vérifiés dans la [RFC9309, §2.2.2–2.2.3](https://www.rfc-editor.org/rfc/rfc9309.html#section-2.2.2), puis testés. Le parseur Python initial utilisait la première correspondance et ne traitait pas ces caractères : son refus local n'était pas un refus du fournisseur. Ce défaut est corrigé uniquement dans le nouveau collecteur ; l'ancien reste figé. Aucun contournement HTTP401/403, authentification ou endpoint général interdit. La RFC est archivée HTTP200/SHA dans le registre des sources.

Les autres archives sont testées indépendamment avec `--continue-pending --published-file-content` : les fichiers échoués ne sont pas réessayés et leurs préfixes restent conservés. Un refus d'accès arrêterait tout le lot. Deux premières versions du nouveau collecteur sont conservées dans son répertoire intermédiaire ; les versions ultérieures et arguments figurent dans `collector_runs`. Tavily et son guide d'installation lié sont absents : vérification par le lecteur web de la source IETF, sans installation ni connexion.

- Décision : `config/snow_multiwinter_decisions_stage76.json`.
- État dynamique de collecte : `reports/oshd_multiwinter_collection_stage76_summary.json`.
- Préfixes : `data_interim/oshd_multiwinter_stage76_downloads/`.
- Commande de reprise : `.venv/Scripts/python.exe -X utf8 src/data_collection/collect_oshd_multiwinter_stage76.py --chunk-bytes 8388608 --max-seconds 3600`. Ajouter `--resume-failed` uniquement après examen d'une interruption non liée à un refus d'accès. Les archives complètes ne sont pas téléchargées à nouveau.

## Calcul préparé, résultats encore partiels

Le producteur `src/data_processing/compare_snow_multiwinter_stage76.py` traite uniquement les archives complètes. Il extrait les membres mensuels nécessaires dans un nouvel espace intermédiaire, contrôle le CRC/SHA, les axes natifs, les unités, les dates et les masques, puis conserve des caches par mois et hiver avec empreintes. Le pilote 2022/23 est repris directement, sans relire ses champs originaux. Les fenêtres −1/+1 utilisent aussi le 30 novembre et le 1er mai lorsqu'ils sont présents.

[Tableau de suivi](../data_processed/snow_multiwinter_comparison_stage76.csv) : 1 680 lignes (70 groupes × 8 hivers × 3 décalages), avec statuts explicites. **2017/18, 2018/19, 2019/20, 2020/21 et 2022/23 sont calculés à ce point de reprise** ; les trois autres hivers ne sont pas présentés comme des résultats. [Résumé du calcul](snow_multiwinter_comparison_stage76_summary.json) conserve les hivers réellement terminés et leurs caches.

Pendant l'interruption OSHD, `prepare_spass_multiwinter_caches_stage76.py` a terminé les **35 mois SPASS des sept hivers restants : 1 059 jours observés, zéro date manquante, 325 cellules natives sélectionnées**. Le futur calcul réutilisera ces caches de valeurs/masques ; aucune moyenne de groupe, substitution ou conversion n'est faite par ce préparateur. Bilan : `reports/spass_multiwinter_cache_preparation_stage76_summary.json`, unité source `UNKNOWN` conservée.

Commande pendant la collecte : `.venv/Scripts/python.exe -X utf8 src/data_processing/run_snow_multiwinter_low_memory_stage76.py --no-register`. Ce drapeau évite les écritures concurrentes dans le registre partagé. Après l'arrêt du collecteur, relancer sans ce drapeau pour enregistrer le tableau et ses variables. À la fin, vérifier toutes les lignes historiques des registres et du journal, ainsi que les empreintes des résultats précédents.

Après ce calcul, `src/data_processing/sync_snow_multiwinter_dictionary_stage76.py` actualise uniquement les taux de valeurs manquantes/types enregistrés de cette nouvelle table, protégés par le verrou du collecteur. Les définitions et autres tables restent inchangées. Cela évite de laisser dans le dictionnaire le taux observé au tout premier checkpoint ; le producteur numérique reste figé pour protéger les caches existants.

Les tests ciblés valident les calendriers bissextiles, les vrais zéros et absences, le poids égal des jours appariés, les doublons, la reprise exacte du pilote, les cellules natives appariées (pas un produit cartésien), les masques et contrats de cache, les 35 caches SPASS, le contrôle robots et son renouvellement, ainsi que les garanties du collecteur et la continuité de l'étape précédente : **23 tests réussis**, avec recalcul NumPy indépendant de toutes les lignes hivernales effectivement disponibles et contrôle du synchroniseur limité aux nouveaux champs. Trois avertissements NumPy/netCDF4 viennent de la création du petit fichier synthétique de test, pas d'un changement du calcul.

Aucun raccordement, calibration, profil final, regroupement ou modèle DiD supplémentaire. La décision de compléter SPASS par OSHD restera à présenter après la comparaison effective des huit hivers. Le guide CSV scientifique impose des colonnes explicites pour unités, statuts et couvertures ; aucun indicateur visuel ne remplace ces informations.

À la reprise, la copie des règles robots dépassait 24 heures : nouvelle version publique récoltée et archivée à 16 h 54 UTC, sans remplacer l'original ni ses empreintes. Une première tentative a échoué localement faute d'accès réseau du sandbox (WinError10013, aucun statut HTTP fournisseur) ; la reprise autorisée a reçu HTTP200. Les requêtes d'archives suivent désormais cette version fraîche. Une indisponibilité de la politique arrête la collecte, sans utiliser silencieusement une ancienne permission. Sources et échecs figurent dans les registres habituels. Les avertissements NumPy/Pandas du calcul 2020/21 concernent une unité temporelle générique dépréciée ; les dates effectivement produites sont contrôlées, aucun changement de calendrier n'est appliqué.
