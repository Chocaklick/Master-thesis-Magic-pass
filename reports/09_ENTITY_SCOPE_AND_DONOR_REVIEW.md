# Entity scope and donor review

## Purpose

This review classifies every historical base-entry label that could not be linked one-to-one to the supplied 271 Swiss resort listings. It protects the donor pool from likely Magic Pass exposure without inventing identity equivalences or complete tourism catchments.

The versioned decisions are in `config/unmatched_magic_scope_review.json`. The row-level outputs are `reports/unmatched_magic_entry_review.csv` and `data_processed/magic_pass_scope_relations.csv`.

## Results

All 26 previously unmatched base-entry labels have been reviewed:

| Review class | Labels | Interpretation |
|---|---:|---|
| Foreign, outside the Swiss listing universe | 10 | French or Italian destinations; absence from the supplied Swiss directory is expected |
| Component of a composite listing | 8 | Named components are related to a broader supplied listing but remain distinct historical events |
| Partial or overlapping scope | 3 | A supplied listing overlaps the official Magic Pass scope without proving equality |
| Ambiguous scope | 1 | Multiple supplied listings overlap the historical label |
| Swiss listing missing or unverified | 4 | No defensible supplied-listing relation has yet been established |

The review creates 14 explicit relation rows involving nine supplied listings. All `identity_equivalence_approved` and `causal_mapping_approved` flags remain false.

## What the annual publications resolved

The complete 2022/2023 Magic Pass map is more informative than the shorter launch text. The launch release names both Beatenberg and Niederhorn; the full map lists Hohwald and Niederhorn as separate new destinations. The current official map uses Beatenberg-Hohwald and Niederhorn. Both historical labels are therefore related to the supplied composite `beatenberg_niederhorn` listing, but they are not collapsed into one event.

Likewise, the complete 2023/2024 annual map names the new destination Gurnigelbad-Gantrisch. This supports a precautionary relation to the supplied `gantrisch_gurnigel` listing. It does not prove identical infrastructure, accommodation catchment or treatment intensity.

Other conservative decisions include:

- Aeschiallmend is related to the broader Aeschi listing, while an official local page explicitly excludes the Lucky village lift from Magic Pass.
- Leysin, Les Mosses and La Lécherette remain three historical labels related to one composite directory listing.
- L'Abbaye, L'Orient and Le Brassus remain components of the Vallée de Joux listing; the broader regional scope also contains Dent de Vaulion.
- Jura sur Léman remains a transboundary domain relation, not a Swiss-only identity match.
- Les Diablerets remains ambiguous across overlapping supplied Villars-Gryon and Glacier 3000 listings.

## Effect on the provisional donor screen

Among the 74 hotel municipalities reached by supplied resort points, 17 already have known Magic Pass exposure through resolved historical or current links. The scope review conservatively excludes four additional municipalities from a clean donor pool: Aeschi bei Spiez, Beatenberg, Leysin and Ormont-Dessus.

The historical scope review reduces the apparent control upper bound from 57 to 53 municipalities and the mechanical 30 km / 36-pre / 24-post screen from 438 to 413 provisional pairs. A subsequent exact-label review links current destination Sattel-Hochstuckli to `hochstuckli_sattel_hochstuckli`, exposing Schwyz as a current-member municipality. The current upper bounds are therefore 52 municipalities, 404 pairs at 30 km and 366 pairs at a 50 km sensitivity threshold. Zero controls are approved for causal use.

For the seven treatments with complete continuity and 24/24 outcome coverage, `reports/11_DONOR_PRETREND_SCREEN.md` ranks 315 of these pairs and retains 35 for manual review. This is descriptive prioritisation, not matching or control approval.

## Remaining limitations

Four Swiss labels still lack a defensible supplied-listing relation: Château-d'Oex, Mayens de Conthey, Wilerallmi and Grenchenberg. One label, Les Diablerets, remains ambiguous across overlapping listings. Foreign destinations can also generate cross-border spillovers even though they fall outside the Swiss listing inventory.

The review is therefore a contamination screen only. It does not establish historical non-membership, independent resort domains, municipality exposure weights, absence of spillovers or a valid causal counterfactual.
