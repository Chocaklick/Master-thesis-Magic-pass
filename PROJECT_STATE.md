# PROJECT STATE

## Project objective

Build a reproducible and scientifically defensible Business Analytics framework for Swiss ski destinations, integrating resort structure, hotel overnight stays, Magic Pass adoption, and later climate/snow information. The authoritative mission is `prompts/main_research_prompt.md`.

## Current phase

Checkpoints 1–3 have been investigated: the existing data audit is complete, initial official treatment evidence has been collected, and panel coverage has been quantified. Checkpoints 4–5 currently fail for causal and heterogeneous-effect modelling. The evidence supports Path C (exploratory segmentation/analogue decision support) unless destination scope, membership continuity, exposure mapping, and controls are materially improved.

## Last update

2026-09-20 01:58 CEST

## Completed work

- Preserved and SHA-256 hashed all 11 supplied raw files.
- Audited nine tabular/geospatial datasets plus two legacy HTML maps.
- Retained and validated the existing clustering without rebuilding it: 1,805 valid lift geometries, 242 clusters, 162 assigned clusters, no duplicate lift membership, no count mismatch, and all 271 listing assignments nearest their stored cluster.
- Built `data_processed/resort_master.csv` with 271 provisional resort listings and stable IDs.
- Built a 31,248-row municipality-month hotel table for 186 municipalities. It contains 28,455 observed total-night values from 2013-01 through 2026-03; 2,793 suppressed monthly total-night cells remain missing.
- Cached official OFS table metadata, the official Magic Pass press archive/current map, eight seasonal Magic Pass PDFs, and 271 geo.admin.ch point-identify responses with checksums and retrieval logs.
- Built a point-container crosswalk: 268 coordinates resolve to a current Swiss municipality, 103 listings fall in 74 municipalities present in the OFS hotel universe, and three coordinates lie outside the Swiss current-municipality layer.
- Built 93 official Magic Pass evidence events: 88 base-pass entries plus separately coded exit/supplement/inclusion events. Sixty-four events have candidate listing links; 29 remain unresolved.
- Extracted 95 destinations from the cached current official map, with 68 candidate listing links. The embedded count conflicts with the official page's “more than 100” headline and is retained as a discrepancy.
- Generated normalized provenance (29 source records), a 313-row data dictionary, source report, initial checkpoint reports, a resort-level evidence-quality table, and a model-feasibility report.
- Added a reproducible checkpoint runner and 8 passing automated tests.

## Main empirical counts

| Quantity | Current value | Interpretation |
|---|---:|---|
| Resort listings | 271 | Not independent destinations |
| Existing lift clusters | 242 | Preserved geographic clusters |
| Clusters linked to listings | 162 | Listing-to-cluster assignments |
| Hotel municipalities | 186 | OFS outcome universe |
| Observed hotel municipality-months | 28,455 | Repeated outcomes, not independent resorts |
| Official base-entry events | 88 | Destination labels from official evidence |
| Candidate-linked base entries | 62 | Scope still provisional |
| Candidate-linked base entries with hotel outcome | 18 | Upper-bound event count |
| Distinct provisional treated municipalities | 14 | Upper bound for treatment heterogeneity |
| Approved causal treatment units | 0 | Exposure/continuity gates not passed |
| Approved controls | 0 | Historical status and spillovers not audited |

## Current model decision

- Municipality fixed effects: data dimension exists, but treatment/exposure not ready.
- Staggered DiD/event study: not credible yet.
- Matching: descriptive analogue selection only at present.
- Synthetic control: possible future case-study design after donor audit.
- Causal forest, X-Learner, DR-Learner: unsupported by the effective treated sample.
- Gradient boosting/random forest: deferred as grouped predictive benchmarks until features and independent units are ready.
- Neural network: rejected; monthly repetition does not create independent resorts.

No causal estimate, CATE, uplift prediction, opportunity score, or business recommendation has been produced.

## Important methodological decisions

- Python remains the primary language; raw and external source responses are immutable.
- The existing lift clustering is a provisional reference layer and was not reconstructed.
- Resort listings, lift clusters, official Magic Pass destinations, tourism destinations, and municipalities remain distinct units.
- A point's containing municipality is recorded only as `coordinate_container_only`; it is never promoted to tourism exposure.
- Membership events are `treatment_ready = false` until scope, continuity/exits, exact timing, exposure, and controls are reviewed.
- Crans-Montana's documented 2020-04-30 base-pass exit proves treatment cannot be assumed absorbing.
- Suppressed hotel values are missing, not zero, and are not imputed.
- Validation must remain grouped by destination/municipality and time.

## Known blockers and data gaps

1. Independent destination/domain definitions are not approved.
2. Season-by-season membership continuity and exit history are incomplete.
3. Twenty-nine official membership events remain unresolved to supplied listings.
4. Destination-to-accommodation-market weights do not exist; shared municipalities and spillovers are unresolved.
5. No historical municipality-boundary harmonization has been implemented.
6. Hotel capacity, snow/climate, accessibility, population, tourism dependence, simultaneous investment, and competition/network controls are missing.
7. The exact upstream source/version of the lift GPKG and retrieval dates of legacy extracts remain unknown.

## Immediate next action

Manually review the 18 candidate entry/outcome links, beginning with shared municipalities (Anniviers, Evolène, and Reichenbach im Kandertal); define independent destination units; complete membership continuity/exits; and construct explicit municipality exposure weights. Reassess Checkpoints 4–5 only after those decisions. Do not fit causal or complex ML models before the gate changes.

## Key files

- Mission: `prompts/main_research_prompt.md`
- Reproducible runner: `src/run_checkpoint_pipeline.py`
- Audit: `reports/01_DATA_AUDIT.md`
- Collection: `reports/02_DATA_COLLECTION.md`
- Quality: `reports/03_DATA_QUALITY.md`
- Feasibility: `reports/model_feasibility_report.md`
- Provenance: `metadata/data_sources_master.csv` and `reports/DATA_SOURCES.md`
- Data dictionary: `metadata/data_dictionary.csv`
- Treatment evidence: `data_processed/magic_pass_membership_history.csv`
- Point municipality mapping: `data_processed/resort_point_municipality.csv`
- Research log: `logs/research_journal.md`
