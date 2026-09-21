# Historical membership evidence review

Review date: 2026-09-21. This is a seasonal evidence audit, not a causal estimate.

## Result

Seven additional dated publications resolve all **25 of 25** previously unverified destination-seasons. All fourteen reviewed units now have evidence for every active season through 2025/2026; eleven enter the municipality outcome panel. Seven units also satisfy the existing 24 observed pre-month / 24 observed active-post-month screen: Anniviers, Axalp, Bumbach, Espace Dent Blanche, Moleson, Reichenbach im Kandertal's Magic portfolio, and Saas-Fee.

The seven units are not seven approved treatments. No control has been approved; timing/intensity, confounding, spatial spillovers and accommodation catchments remain open. Path C remains the current supported research architecture. Completion of the annual membership audit removes one evidence blocker but does not establish causal identification.

## Additional evidence

| Source ID | Document and exact locator | Seasonal contribution |
|---|---|---|
| MAGIC_2019_APRIL | [Magic Pass release, 24 April 2019](https://www.magicpass.ch/media/document/0/mp-cp-24avril-2019-fr-25.pdf), PDF p. 2, boxed roster | Resolves five 2019/2020 gaps: Anniviers portfolio, Espace Dent Blanche, Moleson, Les Pleiades, Villars-Gryon-Les Diablerets. Also corroborates Crans-Montana and Saas-Fee. |
| MAGIC_2024_MAP | [Magic Pass branded map distributed by Raiffeisen](https://www.raiffeisen.ch/content/dam/www/rch/pdf/produkte/mitglieder/de/magic-pass-de.pdf), PDF p. 1 | Printed validity 2024-05-01 to 2025-04-30. Resolves ten 2024/2025 gaps; also corroborates Schwanden. Visual winter/summer-winter symbols distinguish ski destinations from baths. Publisher and distributor are retained separately. |
| MAGIC_PLEIADES_2020_TARIFF | [Operator tariff 2020/2021](https://lespleiades.ch/documents/CP21_tarifs_MP_20-21.pdf), PDF p. 1, dated 2020-11-01 | Confirms Les Pleiades winter 2020/2021 lift validity. |
| MAGIC_PLEIADES_2021_TARIFF | [Operator tariff 2021/2022](https://lespleiades.ch/documents/CP22_tarifs_MP_21-22.pdf), PDF p. 1, dated 2021-11-04 | Confirms Les Pleiades winter 2021/2022 lift validity. |
| MAGIC_FRIBOURG_2021_WINTER | [Fribourg Region winter release](https://fribourg.ch/wp-content/uploads/2021/12/20211201_Fribourg-Region_hiver-2021-22_CP.pdf), PDF p. 1, final paragraph, dated 2021-12-01 | Names Moleson-sur-Gruyeres among participating ski stations for the forthcoming winter 2021/2022. |
| MAGIC_2020_MAP | [Official Magic Pass 2020/2021 network map](https://www.magicpass.ch/media/image/0/stations_magic_pass_3.png), single image | Complete publisher-hosted annual network map. Resolves Anniviers, Espace Dent Blanche, Moleson and Villars-Gryon-Les Diablerets for 2020/2021 and corroborates Les Pleiades and Saas-Fee. The legend distinguishes winter, summer-winter, Glacier 3000 and baths. |
| MAGIC_2021 | [Official 2021/2022 launch dossier](https://www.magicpass.ch/media/document/0/210316_magicpass-dossier-de-presse-final.pdf), PDF pp. 3–4 | Page 3 explicitly says the territory expands by five new stations and names the additions. Combined with the complete prior-year official map, this documents continuation of its reviewed base units; page 4 gives 40 winter stations and 21 summer destinations but no individual modality list. |

Original responses are immutable in `data_external/source_evidence/`; exact local files, source URLs, retrieval times and SHA-256 hashes are recorded in metadata sidecars and `logs/data_collection_log.csv`. The reviewed positive observations and their page references are versioned in `metadata/magic_pass_roster_evidence.json`. Poppler-rendered pages were visually checked, including validity dates, legends and named components. The two operator tariffs restrict the associated train benefit to skiers/snowboarders; this is not unrestricted rail access.

## Resolved gap accounting

| Reviewed unit | Seasons newly resolved by the final annual-publication step |
|---|---|
| Anniviers Magic Pass portfolio | 2020/2021 map; 2021/2022 incremental continuation |
| Espace Dent Blanche | 2020/2021 map; 2021/2022 incremental continuation |
| Moleson | 2020/2021 map |
| Villars-Gryon-Les Diablerets (excluded outcome scope) | 2020/2021 map; 2021/2022 incremental continuation |

Composite portfolios require evidence for their relevant components, not just one similarly named domain. The 2021/2022 rows are not a silent forward fill: they are tagged `official_incremental_roster_continuation` because the dated launch dossier explicitly describes the network as expanding by five identified additions. Individual summer/winter modality remains unknown for that season.

## Search decisions and negative findings

- The cached main 2019 and 2020 dossiers were rendered and inspected; charts and press prose do not supply full rosters. The April 2019 follow-up supplies an explicit dated list. For 2020/2021, the later-discovered publisher-hosted map supplies the complete dated network and legend.
- The 2024 main dossier has no extracted full roster. The one-page branded map was selected because it explicitly prints the applicable dates and shows the named destinations with a legend. A distributor-hosted original document has weaker hosting provenance than a publisher-hosted original, which remains explicit in the source register.
- Live historical press pages include current destination navigation. Search snippets can therefore attach destinations that joined in 2025/2026 to a 2020 article. That navigation is rejected as historical membership evidence.
- The main French 2021 dossier was subsequently recovered and checksum-cached. Visual review of page 3 establishes an incremental expansion by five named additions, so the complete 2020/2021 base map can be carried into 2021/2022 as explicit continuation evidence. Page 4's aggregate totals of 40 winter stations and 21 summer destinations do not identify individual summer status; those modality cells remain unknown. The [German 2021 dossier](https://www.magicpass.ch/media/document/0/210316_magicpass-pressemappe-final.pdf) is corroborating only.
- A local newspaper's April 2020 roster and operator annual reports were discovered as further leads, but have not been accepted into the reviewed evidence. Source prioritisation favours exact seasonal primary documentation before relying on the newspaper transcription.

## Interpretation boundary

`documented_active` means that dated evidence establishes base-pass participation in the named season. It does not prove twelve months of operation, identical summer inclusion, unchanged portfolio intensity, full municipality exposure, or a causal effect. The 24/24 screen counts observed months in the existing analytical windows; it does not establish parallel trends or remove COVID overlap. Annual continuity now supports a more focused design review of four cases, while causal modelling remains gated.

The 26 unmatched official base-entry labels are classified conservatively in `reports/09_ENTITY_SCOPE_AND_DONOR_REVIEW.md`; no relation is an approved identity or causal mapping.
