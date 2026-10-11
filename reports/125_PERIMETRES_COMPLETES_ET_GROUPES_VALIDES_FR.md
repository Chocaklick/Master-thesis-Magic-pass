# Périmètres des pistes et regroupement validés — étape79

Mise à jour : 12 octobre 2026. Deux validations appliquées dans une nouvelle version : **La Dôle–Tuffes entière, sans découpage à la frontière**, et **Wilerallmi–Schwanden en un seul groupe**. Originaux et versions antérieures conservés.

## Résultat

**67 groupes sur 69 ont maintenant des objets de piste associés**, contre60/70 auparavant. Sept nouveaux rattachements ; la diminution de70 à69 vient uniquement du regroupement validé, pas d'une exclusion. LaBraye etRiffenmatt restent non résolus. Cela ne signifie pas67profils physiques calculés : les anciennes sorties restent à40profils de terrain et34moyennes SPASS complètes.

| Nouveau rattachement | Objets OSM | Périmètre et réserve |
|---|---:|---|
| Wilerallmi–Schwanden | 16 | Réseau commun du plan officiel ; réserve sur sa publication historique. |
| La Dôle–Tuffes | 104 | Parties françaises comprises ;99axes et5surfaces séparées. Serra/Noirmont ne sont pas absorbés par leur seule appartenance aux Rousses. |
| Grimentz–Zinal | 115 | Bendolla/Becs-de-Bosson etSorebois ; Vercorin et l'itinéraire inter-domaines non vérifié distincts. |
| Bergbahnen Gstaad | 132 | Rinderberg/Saanersloch/Horneggli, Eggli/Videmanette, Wispile. Wasserngrat et candidats de l'ancien Rellerli non attribués automatiquement. |
| Leysin–Les Mosses–La Lécherette | 110 | Groupe déjà validé conservé ; ski-bus non présenté comme piste. |
| Villars–Gryon–Les Diablerets | 153 | TVGD, hors Glacier3000 et ancien Isenau non vérifié ;21surfaces ne deviennent pas des axes. |
| Leukerbad | 48 | Torrent ; Gemmi non transformée en domaine alpin. Inclusion des trois tracés Erli non prouvée. |

**678objets ajoutés aux1 323lignes anciennes exactes :2 001objets originaux uniques.** Ces comptes ne sont pas des nombres de pistes officielles.

## Méthode et préservation

Rattachement individuel par identité de l'exploitant/composantes, preuves primaires archivées, contexte des remontées et contrôle visuel des identifiants. Listes figées dans `config/piste_remaining_assignments_stage79.json`. Ni distance seule, ni nom seul, ni résultat DiD pour sélectionner les objets. Relations OSM partielles non déclarées intégralement vérifiées ; couverture exhaustive/préentrée non certifiée. Tous groupes conservés.

Fusion : **71identités originales,75points d'accès et185territoires communaux conservés**. Temps du groupe = minimum des références routières disponibles vers les deux départs, selon règle existante. Aux15/30/45minutes : nuitées, première exposition et temps au groupe actif le plus proche inchangés ; aucune observation dupliquée. Nombre de groupes actifs réduit de un seulement là où les deux unités étaient comptées. Aucun itinéraire/effet recalculé ; catalogue incomplet du groupe fusionné laissé manquant.

Plan Wilerallmi–Schwanden : dates internes octobre/novembre2019, antérieures à l'entrée commune2024/25, mais **pas preuve de publication publique en2019**. Rapport annuel : confirmation de l'entrée commune, pas de publication du plan. Réserve conservée dans configuration, registre et filiation.

Nom source LaDôle « composante suisse » conservé comme nom historique : **il ne définit plus le périmètre de cette nouvelle version**. Données suisses absentes côté français laissées manquantes ; aucune substitution/interpolation/source française ajoutée automatiquement.

## Sources et cas ouverts

22nouvelles sources tentées :17archives réussies et5refus/échecs distants conservés, sans contournement. Neuf échecs locaux initiaux puis les vraies réponses figurent dans31événements. Registres actualisés avec URL, original, date réelle et empreinte.

Principales preuves : [Dôle–Tuffes](https://www.jurasurleman.com/domaine-skiable/doles-tuffes/), [secteurs Gstaad](https://bergbahnen-gstaad.ch/fr/hiver/informations/plan-des-pistes), [Grimentz–Zinal](https://booking.valdanniviers.ch/documentation-anniviers-fr.html), [TLML](https://www.tlml.ch/plan-du-domaine/), [TVGD](https://www.tvgd.ch/ski/), [Leukerbad](https://www.leukerbad.ch/ski), [plan Wilerallmi–Schwanden](https://www.wilerallmi.ch/images/Pistenplan_Schwanden_Wilerallmi.pdf). Originaux/refus de plans détaillés dans les manifestes, pas remplacés par des copies non autorisées.

**LaBraye :** [Capdenho2018, p.7](https://www.capdenho.ch/_Resources/Persistent/b14d25aec9c00485d1a623dbbc2ab0d748f959ff/20190318_rapport_activit%C3%A9.pdf) confirme du ski en2017/18, sans géométrie précise. Les309journées regroupent plusieurs stations, pas LaBraye seule. Le [rapport communal2018, pp.28–29](https://www.chateaudoex-admin.ch/_doc/2135771) distingue retrait de subvention, démontage d'un autre télésiège et convention d'exploitation : aucun ne fixe à lui seul le dernier jour de ski. Tracés abandonnés candidats et calendrier de traitement inchangé.

**Riffenmatt :** [tourisme local](https://www.guggisberg-tourismus.ch/angebote/) confirme le Winterpark, mais le lien d'exploitant essayé renvoie404, sans prouver sa fermeture. Aucune piste voisine ou longueur de remontée substituée à un axe.

## Contrôles et reprise

59tests combinésStage79/78/55 réussis. Audit terminé à22:10UTC le11octobre : **2 065fichiers vérifiés, dont2 000historiques inchangés**, préfixes exacts des1 247sources/8 456champs/2 077événements. Registres finaux :1 272sources/8 690champs/2 108événements. Manifeste : `reports/preservation_stage79_summary.json`. FileQA :144objets/25groupes, dont33alertes statut/anciennom. Arêtes communes incluant frontières de surfaces ≠ pistes dupliquées. Rattachements distincts de l'acceptation des métriques.

Le chercheur a validé **vérification individuelle, portions encore ambiguës non mesurées, couverture publiée et groupes conservés**. À appliquer dans une nouvelle version, sans modifier les producteurs figés ni les anciens40/34profils. Ancien nom ≠ ancienne piste ; nom, difficulté, approximation et abandon seront distingués.

Consultation : `data_processed/piste_remaining_review_stage79.csv` (neuf dossiers), `piste_flagged_objects_stage79.csv` (QA), `piste_historical_claims_stage79.csv` (cinq constatations primaires bornées). Manifestes figés : rattachements/fusion/suivi historique Stage79. Reprise : QA individuelle, réseaux uniques puis extension des profils ; ne refaire ni les27correspondances des étapes78/79, ni leurs collectes réussies/refusées, ni les anciens calculs neige.
