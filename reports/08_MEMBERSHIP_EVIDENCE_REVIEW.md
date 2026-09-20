# Historical membership evidence review

Review date: 2026-09-20. This is a seasonal evidence audit, not a causal estimate.

## Result

Five additional dated documents resolve **18 of 25** previously unverified destination-seasons. **Seven** remain unverified. Ten of fourteen reviewed units now have evidence for every active season through 2025/2026; eight enter the municipality outcome panel. Four units also satisfy the existing 24 observed pre-month / 24 observed active-post-month screen: Axalp, Bumbach, Reichenbach im Kandertal's Magic portfolio, and Saas-Fee.

The four units are not four approved treatments. No control has been approved; timing/intensity, confounding, spatial spillovers and accommodation catchments remain open. Path C remains the current supported research architecture. The old claim that zero units pass the continuity-plus-coverage screen is superseded by this review.

## Additional evidence

| Source ID | Document and exact locator | Seasonal contribution |
|---|---|---|
| MAGIC_2019_APRIL | [Magic Pass release, 24 April 2019](https://www.magicpass.ch/media/document/0/mp-cp-24avril-2019-fr-25.pdf), PDF p. 2, boxed roster | Resolves five 2019/2020 gaps: Anniviers portfolio, Espace Dent Blanche, Moleson, Les Pleiades, Villars-Gryon-Les Diablerets. Also corroborates Crans-Montana and Saas-Fee. |
| MAGIC_2024_MAP | [Magic Pass branded map distributed by Raiffeisen](https://www.raiffeisen.ch/content/dam/www/rch/pdf/produkte/mitglieder/de/magic-pass-de.pdf), PDF p. 1 | Printed validity 2024-05-01 to 2025-04-30. Resolves ten 2024/2025 gaps; also corroborates Schwanden. Visual winter/summer-winter symbols distinguish ski destinations from baths. Publisher and distributor are retained separately. |
| MAGIC_PLEIADES_2020_TARIFF | [Operator tariff 2020/2021](https://lespleiades.ch/documents/CP21_tarifs_MP_20-21.pdf), PDF p. 1, dated 2020-11-01 | Confirms Les Pleiades winter 2020/2021 lift validity. |
| MAGIC_PLEIADES_2021_TARIFF | [Operator tariff 2021/2022](https://lespleiades.ch/documents/CP22_tarifs_MP_21-22.pdf), PDF p. 1, dated 2021-11-04 | Confirms Les Pleiades winter 2021/2022 lift validity. |
| MAGIC_FRIBOURG_2021_WINTER | [Fribourg Region winter release](https://fribourg.ch/wp-content/uploads/2021/12/20211201_Fribourg-Region_hiver-2021-22_CP.pdf), PDF p. 1, final paragraph, dated 2021-12-01 | Names Moleson-sur-Gruyeres among participating ski stations for the forthcoming winter 2021/2022. |

Original responses are immutable in `data_external/source_evidence/`; exact local files, source URLs, retrieval times and SHA-256 hashes are recorded in metadata sidecars and `logs/data_collection_log.csv`. The reviewed positive observations and their page references are versioned in `metadata/magic_pass_roster_evidence.json`. Poppler-rendered pages were visually checked, including validity dates, legends and named components. The two operator tariffs restrict the associated train benefit to skiers/snowboarders; this is not unrestricted rail access.

## Remaining gaps

| Reviewed unit | Missing seasons |
|---|---|
| Anniviers Magic Pass portfolio | 2020/2021; 2021/2022 |
| Espace Dent Blanche | 2020/2021; 2021/2022 |
| Moleson | 2020/2021 |
| Villars-Gryon-Les Diablerets (excluded outcome scope) | 2020/2021; 2021/2022 |

Composite portfolios require evidence for their relevant components, not just one similarly named domain. Missing evidence remains unverified, never inactive. Later rosters are not backfilled into earlier years.

## Search decisions and negative findings

- The cached main 2019 and 2020 dossiers were rendered and inspected; charts and press prose do not supply the missing full rosters. The April 2019 follow-up supplies an explicit dated list and is therefore used instead.
- The 2024 main dossier has no extracted full roster. The one-page branded map was selected because it explicitly prints the applicable dates and shows the named destinations with a legend. A distributor-hosted original document has weaker hosting provenance than a publisher-hosted original, which remains explicit in the source register.
- Live historical press pages include current destination navigation. Search snippets can therefore attach destinations that joined in 2025/2026 to a 2020 article. That navigation is rejected as historical membership evidence.
- The main French 2021 dossier's repeated incomplete download remains unresolved. The [German 2021 dossier](https://www.magicpass.ch/media/document/0/210316_magicpass-pressemappe-final.pdf) was inspected through the web text service as an alternative; its retrieved prose does not supply the remaining named roster. It is not an input to the coded evidence.
- A local newspaper's April 2020 roster and operator annual reports were discovered as further leads, but have not been accepted into the reviewed evidence. Source prioritisation favours exact seasonal primary documentation before relying on the newspaper transcription.

## Interpretation boundary

`documented_active` means that dated evidence establishes base-pass participation in the named season. It does not prove twelve months of operation, identical summer inclusion, unchanged portfolio intensity, full municipality exposure, or a causal effect. The 24/24 screen counts observed months in the existing analytical windows; it does not establish parallel trends or remove COVID overlap. Annual continuity now supports a more focused design review of four cases, while causal modelling remains gated.

The 26 unmatched official base-entry labels are unchanged in this milestone. The 2019 roster's explicit grouped labels are useful evidence for a subsequent entity-scope review, but no new listing link is silently assigned here.
