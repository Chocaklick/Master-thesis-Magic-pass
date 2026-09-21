# PROJECT STATE

## Project objective

Build a reproducible and scientifically defensible Business Analytics framework for Swiss ski destinations, integrating resort structure, hotel overnight stays, Magic Pass adoption, and climate/snow information. The authoritative mission is `prompts/main_research_prompt.md`.

## Current phase

Checkpoints 1–3, the first treatment-unit review, and initial capacity/climate integrations are complete: existing data have been audited, official treatment evidence collected, candidate destination/municipality scopes reviewed, membership continuity documented for all 14 reviewed units, donor contamination mechanically screened, official monthly hotel capacity added, and qualified SLF snow plus MeteoSwiss temperature/precipitation proxies built. Checkpoints 4–5 still fail for causal and heterogeneous-effect modelling. The evidence supports Path C (exploratory segmentation/analogue decision support) unless treatment intensity, remaining confounders, spillovers, and controls are materially improved.

## Last update

2026-09-21 23:49 CEST

## Completed work

- Preserved and SHA-256 hashed all 11 supplied raw files.
- Audited nine tabular/geospatial datasets plus two legacy HTML maps.
- Retained and validated the existing clustering without rebuilding it: 1,805 valid lift geometries, 242 clusters, 162 assigned clusters, no duplicate lift membership, no count mismatch, and all 271 listing assignments nearest their stored cluster.
- Built `data_processed/resort_master.csv` with 271 provisional resort listings and stable IDs.
- Built a 31,248-row municipality-month hotel table for 186 municipalities. It contains 28,455 observed total-night values from 2013-01 through 2026-03; 2,793 suppressed monthly total-night cells remain missing.
- Collected the official HESTA supply/demand table in 14 checksum-verified annual PXWeb chunks and built a 31,248-row capacity panel. Establishments, rooms, and beds are jointly observed in 29,274 municipality-months; source `..`/`...` tokens remain missing with no imputation.
- Reconciled the new live table to the legacy demand extraction: 28,452 arrival cells and 28,452 overnight-stay cells match exactly; six cells across three Davos months in 2014 reflect live-table revisions and are reported without overwriting the legacy outcome.
- Cached official OFS table metadata, the official Magic Pass press archive/current map, all main seasonal Magic Pass PDFs including the recovered 2021/2022 dossier, two supplemental 2021/2022 releases, official destination-scope pages, and 271 geo.admin.ch point-identify responses with checksums and retrieval logs.
- Built a point-container crosswalk: 268 coordinates resolve to a current Swiss municipality, 103 listings fall in 74 municipalities present in the OFS hotel universe, and three coordinates lie outside the Swiss current-municipality layer.
- Built 93 official Magic Pass evidence events: 88 base-pass entries plus separately coded exit/supplement/inclusion events. Sixty-four events have candidate listing links; 29 remain unresolved.
- Extracted 95 destinations from the cached current official map, with 69 candidate listing links after resolving Sattel-Hochstuckli to the supplied exact-name listing. The embedded count conflicts with the official page's “more than 100” headline and is retained as a discrepancy.
- Collapsed the 18 candidate entry/outcome links into 14 reviewed destination units. Eleven units have an explicit municipality outcome scope; Villars-Gryon-Les Diablerets, Sainte-Croix / Les Rasses, and Bergbahnen Destination Gstaad are excluded because their composite geography is only partly covered by the hotel panel.
- Built a 1,848-row reviewed destination-month panel with 1,581 complete aggregated hotel-night outcomes and 1,637 complete aggregated capacity rows. Counts are summed with weight 1 and are missing unless every municipality in scope is observed; official occupancy rates are not averaged across multi-municipality units.
- Produced a non-causal 24-month capacity diagnostic separating changes in overnight stays, available beds, and overnight stays per bed. Eight panel units have complete adjacent 24-month capacity windows, but treatment intensity, seasonality, trends, COVID, weather, and donor adjustment remain unresolved.
- Compared official/scientific snow sources and selected the SLF historical IMIS archive for the first proxy. The cached file contains 1,212,878 daily rows from 1992-10 through 2026-09; 166 snow stations have data and 115 pass the predeclared 80% winter-coverage gate for 2013/14–2025/26.
- Built a 271-row resort-to-SLF-station crosswalk retaining distance, station elevation, gap to resort-top altitude, coverage and proxy quality. 112 links are high, 99 moderate and 60 low quality; every row states that the external station is not a direct piste observation.
- Built station-month, station-winter, resort vulnerability and reviewed destination-month snow tables. The 1,848-row destination panel contains 1,733 complete snow-proxy months and 1,565 rows with both an observed hotel outcome and complete snow proxy; no snow field is approved for causal use.
- Cached six official SwissMetNet metadata/catalogue responses and 14 checksum-verified historical/current-year files for the seven nearest required stations. The raw selected files contain 265,838 daily rows across their full histories; the aligned 2013-01 to 2026-03 window contains 33,866 rows with complete temperatures and only 27 missing precipitation values.
- Screened the official inventory for current stations with daily mean/minimum/maximum temperature and precipitation starting by 2013. Of 112 eligible candidates, nearest assignment for the 15 reviewed resort components requires seven stations; nine links are high and six moderate on horizontal-distance comparability, with distance and elevation gaps retained.
- Built a 1,113-row SwissMetNet station-month panel with station-specific 2013–2025 calendar-month anomalies. Two station-months fail the 80% precipitation gate. The reviewed destination weather panel contains 1,744 complete rows out of 1,749 through 2026-03; the 1,848-row outcome panel contains 1,576 rows with both observed hotel nights and complete weather, and 1,560 with observed hotel nights plus complete snow and weather.
- Added five dated supplemental membership documents, then recovered the official publisher-hosted 2020/2021 symbol map and used the 2021/2022 launch dossier's explicit five-station expansion statement. All 14 reviewed units now have every active season documented, 11 enter the outcome panel, and seven have both 24 observed pre and 24 observed active-post months. No causal treatment/control approval follows from this coverage screen.
- Reviewed all 26 unmatched base-entry labels without forcing identity matches: 10 are foreign to the Swiss listing universe, eight are components of composite listings, three have partial/overlapping scope, one remains ambiguous and four Swiss listings remain missing or unverified. Four additional point municipalities are conservatively excluded from the donor pool.
- Visually reviewed seven dated annual launch lists/maps and encoded winter versus summer-winter access for 58 active reviewed unit-seasons. Thirty-six have documented summer access for at least one published component label; mixed-component destinations retain their component labels and 22 unit-seasons are winter-only or part of the founding winter-only pass.
- Screened 814 treatment-donor pairs across 74 resort-linked hotel municipalities. Fifty-six municipalities remain after resolved Magic links and 52 after the additional scope-risk screen; 404 pairs pass a mechanical 30 km / 36-pre / 24-post screen and 366 survive a 50 km sensitivity screen, but zero controls are approved.
- Ranked the 315 provisional pairs belonging to the seven continuity-plus-coverage treatments using only their 36 pre-anchor months, capacity, distance and current resort-directory structure. Thirty-five top-five pairs are retained for manual review; three treatments have pre-windows overlapping the March 2020–April 2022 COVID sensitivity interval.
- Built a 168-month deterministic calendar table and joined it to all 1,848 reviewed destination-month rows. It supplies winter/summer, December/January peak, Easter-month and broad March 2020–April 2022 COVID-sensitivity flags; 286 panel rows fall in that broad interval, which is explicitly not treated as a canton-specific restriction chronology.
- Compared the selected SLF snow station with the next-nearest station passing the same longitudinal gate for all 15 reviewed resort components. Six comparisons have high, five moderate and four low descriptive agreement; median winter-depth correlation is 0.864, but median relative mean absolute depth difference is 47.2%, so snow remains causally unapproved and a gridded independent-source sensitivity is still required.
- Extended spillover screening from treatment-specific distance to the full resolved Magic Pass point network. Of 52 apparent-control municipalities, 23 lie within 30 km of a resolved Magic point; among the 35 shortlisted pairs, 15 are within 30 km and only seven are beyond 50 km. The distances are lower-bound sensitivity flags, not proof of spillovers.
- Checked all seven beyond-50-km donor pairs against complete official Magic Pass rosters for their anchor seasons and documented absence under reviewed station/place labels. Checksum-cached operator evidence from Engadin St. Moritz Mountains, Splügen-Tambo, Samnaun and the canton of Graubünden in addition to the existing regional/Kronberg archives. Every remote pair has an overlapping donor-specific tourism, pricing, access or infrastructure shock, so all seven are excluded, zero deep-audit candidates remain and zero causal controls are approved.
- Implemented the researcher's same-station distance comparison using checksum-cached swissBOUNDARIES3D 2026 geometry. The 11 reviewed destinations × 186 hotel municipality series produce 2,046 distance rows; seven 24/24 destinations produce 1,302 adjacent-window diagnostic rows, 1,246 usable. Six of seven descriptive ≤30 km versus >50 km contrasts are positive; Moléson is the exception. All causal effect/exposure flags remain false.
- Exposed the Moutier boundary-version issue: HESTA retains Moutier (BE), BFS 700, alongside Moutier (JU), BFS 6831, while the current boundary product has one BFS 6831 polygon. Both series are preserved and the geometry bridge is explicit rather than silently harmonised.
- Generated normalized provenance (84 source records), a 469-row data dictionary, source report, destination/capacity/snow/weather/membership/scope/donor/temporal/distance reviews, continuity/control audits, a resort-level evidence-quality table, and an updated model-feasibility report.
- Reran the complete offline checkpoint pipeline and final test suite successfully; all 24 automated tests pass, including network-wide spillover, external-shock triage, same-destination distance, Moutier boundary-lineage and zero-causal-approval validation.

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
| Panel units with fully documented active-season continuity | 11 | All eligible panel units; seasonal evidence is not daily operation |
| Fully documented panel units with 24 pre and 24 post months | 7 | Coverage screen only; no approved controls |
| Active reviewed unit-seasons with individual winter/summer evidence | 58 | 36 include summer access for at least one published component |
| Apparent control municipalities after scope-risk screen | 52 | Upper bound; Sattel-Hochstuckli is now a resolved current member |
| Provisional donor pairs passing 30 km mechanical screen | 404 | 366 survive the 50 km sensitivity; none approved |
| Donor pairs ranked on 36-month pre-period | 315 | 35 shortlisted for manual review across seven treatments |
| Shortlisted pairs within 30 km of any resolved Magic point | 15 | Network-wide lower-bound spillover sensitivity; not proof of contamination |
| Beyond-50-km donor pairs with complete-roster and external-shock review | 7 | All seven have documented Magic roster-label absence but are excluded for overlapping donor-specific shocks |
| Same-destination municipality distance rows | 2,046 | 11 reviewed destinations × 186 hotel municipality series |
| Usable municipality rows in 24/24 distance diagnostic | 1,246 | Six of seven near/far contrasts positive; descriptive only |
| Temporal-control months | 168 | Deterministic calendar plus broad COVID sensitivity flags; not a legal restriction chronology |
| Reviewed components in alternative SLF-station sensitivity | 15 | 11 high/moderate and 4 low agreement; zero snow covariates approved |
| Approved causal treatment units | 0 | Intensity/exposure, confounder, spillover and control gates not passed |
| Approved controls | 0 | The top-35 shortlist is exhausted: 28 proximity-deprioritised pairs plus seven remote pairs excluded for donor-specific shocks |

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
- Membership events and destination-month rows remain causal-not-ready until treatment intensity/exposure, confounding, spillovers, and controls are approved.
- Crans-Montana's documented 2020-04-30 base-pass exit proves treatment cannot be assumed absorbing.
- Suppressed hotel values are missing, not zero, and are not imputed.
- Physically negative SLF snow-depth values are retained in raw evidence but set missing in derived metrics. Station proxies preserve distance/elevation diagnostics and never claim direct slope representation.
- SwissMetNet precipitation retains its official 06:00-to-06:00 UTC daily window. Weather anomalies use project-calculated 2013–2025 station/month references, not official climatological normals. Regional station proxies remain non-piste and causal-not-approved.
- Validation must remain grouped by destination/municipality and time.

## Known blockers and data gaps

1. Independent destination/domain definitions remain unresolved outside the 14 reviewed candidate units.
2. Active-season membership continuity is complete for the 14 reviewed units. Individual winter/summer modality is still unavailable for 2019/2020 and 2021/2022 because those publications do not provide a named modality list; this is a treatment-intensity gap, not a membership gap.
3. All 26 unmatched base-entry labels are classified for scope risk, but none has been promoted to an identity-equivalent causal mapping. Four Swiss labels still lack a supplied-listing relation and Les Diablerets remains ambiguous across overlapping listings.
4. Core-municipality proxies do not establish full tourism catchments. Network-wide point distance and same-destination distance bands now expose proximity risk, but road/rail travel time, hotel locations and actual visitor spillovers remain unresolved.
5. No full historical municipality-boundary harmonization has been implemented. Moutier's BFS 700-to-6831 transition is explicitly bridged only for the current-geometry distance diagnostic.
6. Hotel capacity and qualified snow/temperature/precipitation proxies are integrated, but systematic snowmaking, accessibility, population and tourism dependence remain missing. The seven remote donor pairs now have complete-roster label checks and contemporaneous-shock review; exact competing-pass operator tariffs remain qualified but are no longer decision-critical because every pair is independently excluded.
7. Sixty resort-to-snow-station links have low spatial/elevation comparability. The alternative-SLF-station test is complete for the 15 reviewed components, but four have low agreement; an independent gridded sensitivity remains pending for snow, and alternative-station/gridded sensitivity remains pending for regional weather.
8. The 52-municipality post-scope apparent control pool and 404 provisional treatment-distance pairs remain screening outputs. The top-35 pre-trend shortlist is exhausted: distance deprioritises 28 pairs at or within 50 km and official-source review excludes all seven remote pairs for donor-specific shocks. Any future causal attempt requires a redesigned/broader donor strategy rather than promoting a current shortlist row.
9. The exact upstream source/version of the lift GPKG and retrieval dates of legacy extracts remain unknown.

## Immediate next action

Resolve the four missing/unverified Swiss listing relations and ambiguous Les Diablerets scope, then lock Checkpoint 4 as failed under the present donor design and advance to the explicitly exploratory Path C architecture (segmentation, analogue matching and uncertainty-aware decision support). A future causal redesign would need a broader donor search plus authoritative travel-time/accommodation exposure and stronger accessibility/confounder data. Add gridded snow/regional-weather sensitivities before treating climate fields as causal covariates. Do not fit causal or complex heterogeneous-effect models before approval gates change. See reports 08–16.

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
- Additional historical evidence: `reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md`
- Unmatched entity scope: `reports/09_ENTITY_SCOPE_AND_DONOR_REVIEW.md` and `data_processed/magic_pass_scope_relations.csv`
- Annual winter/summer register: `reports/10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md` and `data_processed/magic_pass_membership_status_by_season.csv`
- Donor pre-trend screen: `reports/11_DONOR_PRETREND_SCREEN.md` and `data_processed/donor_pretrend_comparability.csv`
- Temporal controls: `reports/12_TEMPORAL_CONTROLS.md` and `data_processed/temporal_controls_month.csv`
- Snow-station sensitivity: `reports/13_SNOW_PROXY_SENSITIVITY.md` and `data_processed/resort_snow_alternative_station_sensitivity.csv`
- Donor network spillover: `reports/14_DONOR_NETWORK_SPILLOVER_AUDIT.md` and `data_processed/donor_shortlist_network_audit.csv`
- Same-destination distance gradient: `reports/15_TREATMENT_DISTANCE_GRADIENT.md`, `data_processed/treatment_municipality_distance_exposure.csv`, and `reports/treatment_distance_near_far_contrast.csv`
- Donor external shocks: `reports/16_DONOR_EXTERNAL_SHOCK_AUDIT.md`, `reports/donor_external_shock_evidence.csv`, and `data_processed/donor_shortlist_final_audit.csv`
- Control screen: `reports/control_candidates_by_treatment.csv`
- Research log: `logs/research_journal.md`
