# Entrées successives et trajectoire du réseau - étape 29

Cet audit conserve les identifiants administratifs sources. Le raccordement territorial de Moutier, validé ensuite, est appliqué dans un panel séparé au [rapport 78](78_RACCORDEMENT_TERRITORIAL_MOUTIER_FR.md) : ses comptes territoriaux et son diagnostic recalculé sont à utiliser avant estimation.

## Décision appliquée

L'analyse principale conserve tous les mois observés après la première exposition, y compris après une nouvelle entrée accessible. Elle cible la trajectoire d'exposition au réseau depuis cette première entrée. L'effet propre de chaque ajout fait l'objet d'un diagnostic séparé avant de choisir une estimation.

## Ce que les données permettent d'examiner

Les 80 séries communales exposées représentent 79 territoires actuels : les identifiants Moutier BE (700) et Moutier JU (6831) correspondent au même territoire. Les séries recensent 177 événements commune-mois : 80 premières expositions et 97 ajouts dans 46 séries, soit 45 territoires. En dédupliquant uniquement pour compter les territoires, on obtient 175 dates territoire-mois, dont 96 ajouts. Aucun raccordement analytique n'est encore appliqué.

Parmi les 97 ajouts recensés par identifiant, 43 font entrer plusieurs groupes simultanément. 94 disposent d'au moins une nuitée observée entre l'entrée précédente et cet ajout, puis entre cet ajout et l'entrée suivante. Cette disponibilité ne garantit pas la comparabilité.

Le tableau des événements conserve les groupes entrant ensemble, les délais entre entrées et les données cumulées déjà présentes : nombre de groupes actifs, kilomètres de pistes et remontées connus. Les structures manquantes restent signalées. Les sommes connues peuvent être partielles.

## Peut-on séparer les groupes ?

Les 71 groupes restent recensés. 45 ont au moins une commune accessible à 120 minutes ; 26 n'en ont aucune dans cette matrice. Sur les 28455 lignes où les nuitées sont observées, les 45 colonnes d'exposition ont un rang de 41 après retrait des effets fixes commune et mois. Le déficit est de 4 dimensions.

Colonnes d'exposition exactement identiques sur les observations disponibles : Mayens de Conthey / Anzère; Wilerallmi / Schwanden; Aeschiallmend / Faltschen; Grimentz-Zinal / St-Luc / Chandolin. Ces contributions ne peuvent pas être estimées séparément dans cette définition. Les identifiants originaux restent distincts et aucun regroupement supplémentaire n'est appliqué.

Une colonne distincte ou un rang suffisant indique seulement une variation algébrique. Cela ne valide ni les tendances avant entrée, ni l'absence de choc concomitant, ni l'interprétation causale d'un effet additionnel. La projection du calendrier de transport actuel sur le passé et les changements de territoire restent des limites.

Le rang de cet audit décrit le panel par identifiants sources. Moutier ne constitue pas deux communes indépendantes : l'ancien identifiant contient 154 mois observés jusqu'en décembre 2025 et le nouveau trois mois de janvier à mars 2026. Le raccordement exact validé et le diagnostic territorial recalculé figurent au rapport 78 ; les données sources de cet audit restent intactes.

## Méthode et reprise

Le calendrier de groupe réutilise la première entrée et la sortie documentée de Crans-Montana. L'hypothèse de continuité des autres adhésions reste celle du projet. Les changements internes de composantes d'un groupe ne deviennent pas automatiquement de nouvelles entrées de groupe.

Le rang est calculé sur toutes les lignes de nuitées observées disponibles, sans seuil de durée avant/après et sans exclusion COVID. Une projection alternée retire exactement, à la tolérance numérique de 1e-12, les moyennes par commune et mois dans le panel non équilibré. Le seuil de rang est celui de NumPy : valeur singulière maximale × plus grande dimension × précision machine. Ce calcul est un diagnostic de dépendance, pas une régression estimant un effet.

Prochaine décision : choisir les diagnostics de comparabilité et l'estimateur pour la trajectoire principale ; définir ensuite la spécification des effets additionnels en tenant compte des groupes indissociables. Après le raccordement de Moutier au rapport 78, trois historiques préexposition restent incomplets. Aucun échantillon final ou effet causal n'est validé à ce stade.

## Sources et fichiers

- `data_processed/accessibility_station_groups.csv`, `accessibility_station_group_events.csv` et `magic_pass_membership_history.csv` : identifiants, entrées, regroupements existants et sortie documentée.
- `data_processed/accessibility_station_group_journey_context.csv` : accès actuel et règle descriptive de qualité déjà appliquée.
- `data_processed/accessibility_municipality_month_exposure.csv` : nuitées HESTA, expositions et structures cumulées ; reconciliation intégrale des comptes de groupes.
- `reports/accessibility_successive_entry_events.csv` : un événement commune-mois par ligne.
- `reports/accessibility_successive_entry_group_separability.csv` : les 71 groupes et les dépendances exactes observées.
- `reports/accessibility_successive_entry_summary.json` : effectifs, paramètres numériques, sortie documentée et empreintes SHA-256 des entrées. Aucun téléchargement supplémentaire.
