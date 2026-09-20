# PROJECT STATE

## Project objective

Build a reproducible and scientifically defensible Business Analytics framework for Swiss ski destinations, integrating resort structure, hotel overnight stays, Magic Pass adoption, and climate/snow information. The authoritative mission is `prompts/main_research_prompt.md`.

## Current phase

Checkpoints 1–3, the first treatment-unit review, and initial capacity/climate integrations are complete: existing data have been audited, official treatment evidence collected, candidate destination/municipality scopes reviewed, membership continuity audited season by season, donor contamination mechanically screened, official monthly hotel capacity added, and qualified SLF snow plus MeteoSwiss temperature/precipitation proxies built. Checkpoints 4–5 still fail for causal and heterogeneous-effect modelling. The evidence supports Path C (exploratory segmentation/analogue decision support) unless membership continuity, remaining confounders, spillovers, and controls are materially improved.

## Last update

2026-09-20 11:35 CEST

## Completed work

- Preserved and SHA-256 hashed all 11 supplied raw files.
- Audited nine tabular/geospatial datasets plus two legacy HTML maps.
- Retained and validated the existing clustering without rebuilding it: 1,805 valid lift geometries, 242 clusters, 162 assigned clusters, no duplicate lift membership, no count mismatch, and all 271 listing assignments nearest their stored cluster.
- Built `data_processed/resort_master.csv` with 271 provisional resort listings and stable IDs.
- Built a 31,248-row municipality-month hotel table for 186 municipalities. It contains 28,455 observed total-night values from 2013-01 through 2026-03; 2,793 suppressed monthly total-night cells remain missing.
- Collected the official HESTA supply/demand table in 14 checksum-verified annual PXWeb chunks and built a 31,248-row capacity panel. Establishments, rooms, and beds are jointly observed in 29,274 municipality-months; source `..`/`...` tokens remain missing with no imputation.
- Reconciled the new live table to the legacy demand extraction: 28,452 arrival cells and 28,452 overnight-stay cells match exactly; six cells across three Davos months in 2014 reflect live-table revisions and are reported without overwriting the legacy outcome.
- Cached official OFS table metadata, the official Magic Pass press archive/current map, nine main seasonal Magic Pass PDFs except the repeatedly truncated 2021 dossier, two supplemental 2021/2022 releases, eight official destination-scope pages, and 271 geo.admin.ch point-identify responses with checksums and retrieval logs.
- Built a point-container crosswalk: 268 coordinates resolve to a current Swiss municipality, 103 listings fall in 74 municipalities present in the OFS hotel universe, and three coordinates lie outside the Swiss current-municipality layer.
- Built 93 official Magic Pass evidence events: 88 base-pass entries plus separately coded exit/supplement/inclusion events. Sixty-four events have candidate listing links; 29 remain unresolved.
- Extracted 95 destinations from the cached current official map, with 68 candidate listing links. The embedded count conflicts with the official page's “more than 100” headline and is retained as a discrepancy.
- Collapsed the 18 candidate entry/outcome links into 14 reviewed destination units. Eleven units have an explicit municipality outcome scope; Villars-Gryon-Les Diablerets, Sainte-Croix / Les Rasses, and Bergbahnen Destination Gstaad are excluded because their composite geography is only partly covered by the hotel panel.
- Built a 1,848-row reviewed destination-month panel with 1,581 complete aggregated hotel-night outcomes and 1,637 complete aggregated capacity rows. Counts are summed with weight 1 and are missing unless every municipality in scope is observed; official occupancy rates are not averaged across multi-municipality units.
- Produced a non-causal 24-month capacity diagnostic separating changes in overnight stays, available beds, and overnight stays per bed. Eight panel units have complete adjacent 24-month capacity windows, but continuity, seasonality, trends, COVID, weather, and donor adjustment remain unresolved.
- Compared official/scientific snow sources and selected the SLF historical IMIS archive for the first proxy. The cached file contains 1,212,878 daily rows from 1992-10 through 2026-09; 166 snow stations have data and 115 pass the predeclared 80% winter-coverage gate for 2013/14–2025/26.
- Built a 271-row resort-to-SLF-station crosswalk retaining distance, station elevation, gap to resort-top altitude, coverage and proxy quality. 112 links are high, 99 moderate and 60 low quality; every row states that the external station is not a direct piste observation.
- Built station-month, station-winter, resort vulnerability and reviewed destination-month snow tables. The 1,848-row destination panel contains 1,733 complete snow-proxy months and 1,565 rows with both an observed hotel outcome and complete snow proxy; no snow field is approved for causal use.
- Cached six official SwissMetNet metadata/catalogue responses and 14 checksum-verified historical/current-year files for the seven nearest required stations. The raw selected files contain 265,838 daily rows across their full histories; the aligned 2013-01 to 2026-03 window contains 33,866 rows with complete temperatures and only 27 missing precipitation values.
- Screened the official inventory for current stations with daily mean/minimum/maximum temperature and precipitation starting by 2013. Of 112 eligible candidates, nearest assignment for the 15 reviewed resort components requires seven stations; nine links are high and six moderate on horizontal-distance comparability, with distance and elevation gaps retained.
- Built a 1,113-row SwissMetNet station-month panel with station-specific 2013–2025 calendar-month anomalies. Two station-months fail the 80% precipitation gate. The reviewed destination weather panel contains 1,744 complete rows out of 1,749 through 2026-03; the 1,848-row outcome panel contains 1,576 rows with both observed hotel nights and complete weather, and 1,560 with observed hotel nights plus complete snow and weather.
- Audited annual membership evidence without filling gaps: 4 of 14 reviewed units have every active season documented, only 3 of those enter the outcome panel, and none of the 3 has both 24 observed pre and 24 observed active-post months.
- Screened 814 treatment-donor pairs across 74 resort-linked hotel municipalities. Fifty-seven municipalities remain an upper-bound control pool after resolved Magic links; 438 pairs pass a mechanical 30 km / 36-pre / 24-post screen, but zero controls are approved.
- Generated normalized provenance (55 source records), a 375-row data dictionary, source report, destination/capacity/snow/weather reviews, continuity/control audits, a resort-level evidence-quality table, and an updated model-feasibility report.
- Added a reproducible checkpoint runner and 15 passing automated tests.

## Main empirical counts

| Quantity | Current value | Interpretation |
|---|---:|---|
| Resort listings | 271 | Not independent destinations |
| Existing lift clusters | 242 | Preserved geographic clusters |
| Clusters linked to listings | 162 | Listing-to-cluster assignments |
| Hotel municipalities | 186 | OFS outcome universe |
| Observed hotel municipality-months | 28,455 | Repeated outcomes, not independent resorts |
| Complete hotel-capacity municipality-months | 29,274 | Establishments, rooms, and beds all observed |
| Official base-entry events | 88 | Destination labels from official evidence |
| Candidate-linked base entries | 62 | Scope still provisional |
| Candidate-linked base entries with hotel outcome | 18 | Upper-bound event count |
| Distinct provisional treated municipalities | 14 | Upper bound for treatment heterogeneity |
| Reviewed destination units | 14 | 18 events collapsed across shared/composite units |
| Units in reviewed destination-month panel | 11 | 3 incomplete composite scopes excluded |
| Reviewed destination-month rows | 1,848 | 1,581 complete hotel-night outcomes |
| Reviewed destination-months with complete capacity | 1,637 | Capacity covariate coverage, not causal identification |
| Units with complete 24-month pre/post capacity windows | 8 | Descriptive adjacent-window diagnostic only |
| SLF snow stations passing longitudinal gate | 115 | External mountain-station proxies, not pistes |
| Resort listings with feature-ready snow proxy | 211 | High/moderate comparability and ≥10 usable winters |
| Destination-months with complete snow proxy | 1,733 | 1,565 also have observed hotel nights |
| SwissMetNet stations eligible from inventory | 112 | All four daily parameters start by 2013 and have no recorded end date |
| SwissMetNet stations selected | 7 | Nearest stations for 15 reviewed resort components |
| Destination-months with complete weather proxy | 1,744 | 1,576 also have observed hotel nights |
| Units with 24 pre and 24 post months under continuity assumption | 7 | Coverage only; not identification |
| Panel units with fully documented active-season continuity | 3 | Crans-Montana, Schwanden, Meiringen-Hasliberg |
| Fully documented panel units with 24 pre and 24 post months | 0 | Decisive causal feasibility failure |
| Provisional donor pairs passing mechanical screen | 438 | None approved as causal controls |
| Approved causal treatment units | 0 | Exposure/continuity gates not passed |
| Approved controls | 0 | Historical status and spillovers not audited |

## Current model decision

- Municipality fixed effects: diagnostic panel exists, but causal treatment/control status is not ready.
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
- Resort listings, lift clusters, official Magic Pass destinations, reviewed destination units, and municipalities remain distinct units.
- A point's containing municipality is recorded only as `coordinate_container_only`; it is never promoted to tourism exposure.
- Membership events and destination-month rows remain causal-not-ready until continuity/exits, confounding, spillovers, and controls are approved.
- Crans-Montana's documented 2020-04-30 base-pass exit proves treatment cannot be assumed absorbing.
- Suppressed hotel values are missing, not zero, and are not imputed.
- Physically negative SLF snow-depth values are retained in raw evidence but set missing in derived metrics. Station proxies preserve distance/elevation diagnostics and never claim direct slope representation.
- SwissMetNet precipitation retains its official 06:00-to-06:00 UTC daily window. Weather anomalies use project-calculated 2013–2025 station/month references, not official climatological normals. Regional station proxies remain non-piste and causal-not-approved.
- Validation must remain grouped by destination/municipality and time.

## Known blockers and data gaps

1. Independent destination/domain definitions remain unresolved outside the 14 reviewed candidate units.
2. Twenty-five active destination-seasons remain unverified; the main 2021 dossier still fails to download completely, although a smaller official 2021 follow-up is cached.
3. Twenty-six official base-entry labels remain unresolved to supplied listings.
4. Core-municipality proxies do not establish full tourism catchments, and spillovers remain unresolved.
5. No historical municipality-boundary harmonization has been implemented.
6. Hotel capacity and qualified snow/temperature/precipitation proxies are integrated, but snowmaking, accessibility, population, tourism dependence, simultaneous investment, and competition/network controls are missing.
7. Sixty resort-to-snow-station links have low spatial/elevation comparability; alternative-station and gridded-data sensitivity tests remain pending for both snow and regional weather.
8. The 57-municipality apparent control pool and 438 provisional donor pairs remain upper bounds, not approved controls.
9. The exact upstream source/version of the lift GPKG and retrieval dates of legacy extracts remain unknown.

## Immediate next action

Fill the remaining 25 unverified active unit-seasons and resolve the 26 unmatched base-entry labels. Test alternative-station or gridded sensitivity for snow and weather, then replace the mechanical donor screen with a documented membership/spillover review before reassessing Checkpoints 4–5. Do not fit causal or complex ML models before the gate changes.

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
- Reviewed destination panel: `data_processed/destination_month_panel.csv`
- Destination review: `reports/04_DESTINATION_UNIT_REVIEW.md`
- Hotel capacity: `reports/05_HOTEL_CAPACITY.md` and `reports/hotel_capacity_treatment_diagnostics.csv`
- Snow proxy: `reports/06_SNOW_SOURCE_AND_PROXY.md`, `data_processed/resort_snow_station_crosswalk.csv`, and `data_processed/resort_snow_vulnerability.csv`
- Weather proxy: `reports/07_WEATHER_PROXY.md`, `data_processed/resort_weather_station_crosswalk.csv`, and `data_processed/destination_weather_month.csv`
- Membership continuity: `reports/membership_continuity_audit.csv`
- Control screen: `reports/control_candidates_by_treatment.csv`
- Research log: `logs/research_journal.md`
