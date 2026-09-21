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
| Resolved overlapping directory scope | 1 | Les Diablerets overlaps two directory rows; Glacier 3000 is explicitly kept separate |
| Documented destination missing from directory | 2 | Mayens de Conthey and Grenchenberg are official destinations absent from the supplied directory |
| Documented historical destination missing from directory | 1 | Château-d'Oex/La Braye is historically documented but absent from the supplied directory |
| Documented distinct neighbouring destination missing from directory | 1 | Wilerallmi is distinct from nearby Schwanden despite their shared municipality and proximity |

The review creates 14 explicit relation rows involving nine supplied listings. All `identity_equivalence_approved` and `causal_mapping_approved` flags remain false.

## What the annual publications resolved

The complete 2022/2023 Magic Pass map is more informative than the shorter launch text. The launch release names both Beatenberg and Niederhorn; the full map lists Hohwald and Niederhorn as separate new destinations. The current official map uses Beatenberg-Hohwald and Niederhorn. Both historical labels are therefore related to the supplied composite `beatenberg_niederhorn` listing, but they are not collapsed into one event.

Likewise, the complete 2023/2024 annual map names the new destination Gurnigelbad-Gantrisch. This supports a precautionary relation to the supplied `gantrisch_gurnigel` listing. It does not prove identical infrastructure, accommodation catchment or treatment intensity.

Other conservative decisions include:

- Aeschiallmend is related to the broader Aeschi listing, while an official local page explicitly excludes the Lucky village lift from Magic Pass.
- Leysin, Les Mosses and La Lécherette remain three historical labels related to one composite directory listing.
- L'Abbaye, L'Orient and Le Brassus remain components of the Vallée de Joux listing; the broader regional scope also contains Dent de Vaulion.
- Jura sur Léman remains a transboundary domain relation, not a Swiss-only identity match.
- Les Diablerets is related to the two overlapping `les_diablerets_glacier_3000` and `villars_gryon_villars_gryon_les_diablerets` rows, which share lift cluster `SKI_CLUSTER_008`. The separate `glacier_3000_les_diablerets` row is no longer treated as a relation: the founding publication and current map list Glacier 3000 separately, and the operator describes access from the Diablerets slopes by shuttle. No one-to-one identity is approved.

## Resolution of the four missing Swiss labels

Official follow-up evidence resolves the earlier uncertainty without manufacturing rows in the supplied directory:

- the Commune de Château-d'Oex's 2018 preavis identifies La Braye's lift assets and the Télé-Château-d'Oex operator lineage;
- the Commune de Conthey lists the Société coopérative, Téléskis des Mayens de Conthey;
- the official Wilerallmi annual report identifies Skilift Wilerallmi Sigriswil AG, while the current Magic Pass map lists Wilerallmi and Schwanden separately;
- the official Grenchen tourism page identifies Skilift Grenchenberg AG, its two lifts and Magic Pass integration.

These are therefore directory-coverage gaps rather than unverified destinations. Wilerallmi's official point is 0.862 km from the supplied Schwanden point, so Schwanden remains a precautionary neighbouring relation only. Identity equivalence and causal mapping remain false.

## Effect on the provisional donor screen

Among the 74 hotel municipalities reached by supplied resort points, 17 already have known Magic Pass exposure through resolved historical or current links. The scope review conservatively excludes four additional municipalities from a clean donor pool: Aeschi bei Spiez, Beatenberg, Leysin and Ormont-Dessus.

The historical scope review reduces the apparent control upper bound from 57 to 53 municipalities and the mechanical 30 km / 36-pre / 24-post screen from 438 to 413 provisional pairs. A subsequent exact-label review links current destination Sattel-Hochstuckli to `hochstuckli_sattel_hochstuckli`, exposing Schwyz as a current-member municipality. The current upper bounds are therefore 52 municipalities, 404 pairs at 30 km and 366 pairs at a 50 km sensitivity threshold. Zero controls are approved for causal use.

For the seven treatments with complete continuity and 24/24 outcome coverage, `reports/11_DONOR_PRETREND_SCREEN.md` ranks 315 of these pairs and retains 35 for manual review. This is descriptive prioritisation, not matching or control approval.

## Remaining limitations

The four documented Swiss destinations still have no own row in the supplied resort directory, so their infrastructure features, lift-cluster assignments and point-to-municipality links cannot be silently borrowed from another listing. Les Diablerets remains a many-to-many overlap rather than an identity match. Foreign destinations can also generate cross-border spillovers even though they fall outside the Swiss listing inventory.

The review is therefore a contamination screen only. It does not establish historical non-membership, independent resort domains, municipality exposure weights, absence of spillovers or a valid causal counterfactual.
