# Model feasibility report

Generated reproducibly by `src/data_processing/build_feasibility_report.py`.

## Executive verdict

The project currently follows **Path C (weak treatment sample / exploratory decision support)**. This is a checkpoint decision, not a permanent rejection of causal work. Destination scope, reviewed-unit season-by-season membership, monthly hotel capacity, a qualified SLF snow proxy, and qualified MeteoSwiss temperature/precipitation proxies have now been integrated, but a move to Path B still requires treatment-intensity validation, the remaining confounders, spillover analysis, and an uncontaminated control audit.

No causal model, treatment-effect learner, opportunity score, or neural network should be fitted at this checkpoint.

## Effective sample

- The supplied Bergfex layer contains **271 resort listings**. The preserved lift layer has **242 clusters**, of which **162** are linked to at least one listing. Neither number is yet an approved count of independent ski destinations.
- The official current-map snapshot contains **95 embedded destinations**; **69** have a candidate link to a supplied resort listing. The page headline and press archive refer to more than 100 destinations, so the embedded-list discrepancy must be reviewed rather than silently reconciled.
- Official evidence records **88 base-pass entry events**. **62** have a candidate resort-listing link, but only **18** also point to an OFS hotel municipality.
- Those 18 events reduce to **14 municipalities**. This municipality count, not the 28,455 observed monthly rows, is the more relevant upper bound for treatment heterogeneity.
- The 18 candidate links collapse to **14 reviewed destination units**. **11** enter a diagnostic outcome panel; **3** composite destinations are excluded because the supplied hotel panel does not cover their full reviewed scope.
- The reviewed panel has **1,848 destination-month rows**, of which **1,581** have a complete aggregated hotel-night outcome.
- **Zero** treatment units are approved for causal estimation. The reviewed geography and annual membership are evidence inputs, while treatment intensity, confounding, spillovers, and control status remain unresolved.

## Outcome coverage

- The cleaned OFS-derived panel has **186 municipalities**.
- Observed hotel-night values run from **2013-01-01** through **2026-03-01**; later 2026 grid rows are missing and are not counted as observed.
- Resort points reach **74** hotel municipalities.
- Resolved historical/current Magic links reduce the 74-municipality resort-point universe to an upper bound of **56** apparent controls. This is not a clean donor pool: **26** official base-entry labels remain unresolved, and **zero controls are approved**.

## Provisional pre/post windows

For coverage diagnostics only, the script anchors the founding 2017/18 season at 2017-11-01 and later annual seasons at 1 May of their first year. These are not accepted treatment dates. A documented exit bounds Crans-Montana's active post period. The separate reviewed-unit continuity audit now documents all active seasons for the 14 reviewed units, without converting annual membership into an exact treatment date or intensity.

- Season-only candidate events with at least 24 observed pre months: **16**
- With at least 36 observed pre months: **16**
- With at least 24 potentially post-entry months: **15**
- With at least 36 potentially post-entry months: **12**
- Distinct provisional anchors: **7**
- Treated units with an exact entry date: **0**

The provisional event-level audit is in `reports/provisional_treatment_window_coverage.csv`. The stricter destination-unit review superseding raw event counts is in `reports/destination_unit_review.csv`:

- Reviewed units with at least 24 observed pre months and 24 active post months under the explicit continuity assumption: **7**
- Reviewed units with at least 36 observed pre months and 36 active post months under that assumption: **6**

These are coverage counts, not an identification claim.

## Hotel-capacity diagnostic

The official HESTA supply table contributes **31,248 municipality-month rows**; **29,274** have establishments, rooms, and beds observed. After reviewed destination aggregation, **1,637 of 1,848** destination-month rows have complete capacity scope.

For each destination, `reports/hotel_capacity_treatment_diagnostics.csv` compares the last 24 observed pre-anchor months with the first 24 observed active-post months under the explicit continuity assumption. It reports separate changes in live-table overnight stays, available beds, and overnight stays per bed. **8 units** have both complete 24-month capacity windows.

This is a descriptive diagnostic only. The adjacent windows are not seasonally or trend adjusted, early post-periods can overlap COVID, and annual membership does not establish constant treatment intensity. Capacity integration therefore helps distinguish demand changes from contemporaneous supply changes but does not identify a Magic Pass effect.

## Snow proxy coverage

The official SLF historical archive contains daily observations for **166 snow stations**. The project predeclares an 80% November–April coverage gate over 2013/14–2025/26; **115 stations** pass. Every resort listing is mapped to the geographically nearest passing station, while distance and the elevation gap to the published resort top remain visible. **211 of 271 listings** have high/moderate proxy comparability and at least ten usable winters.

The reviewed panel contains **1,733 complete station-proxy months**; **1,565 rows** also have an observed hotel-night outcome. These fields support descriptive climate adjustment and future robustness checks only. IMIS stations serve avalanche monitoring and can differ materially from pistes in terrain, aspect, wind, elevation, grooming, and snowmaking. No snow field is yet an approved causal covariate.

A next-nearest-station sensitivity covers all **15 reviewed resort components** using the same station coverage gate. **11 components** receive a high or moderate descriptive agreement grade and **4** receive a low grade. The median winter-depth correlation is **0.864**, but the median relative mean absolute depth difference is **47.2%**; absolute snow levels are therefore materially station-dependent even when seasonal variation co-moves. See `reports/13_SNOW_PROXY_SENSITIVITY.md`. This test does not approve the snow covariate, and an independent gridded-source sensitivity remains pending.

## Temperature and precipitation proxy coverage

Official MeteoSwiss inventory metadata identifies **112 current SwissMetNet stations** whose daily mean/minimum/maximum temperature and 06:00-to-06:00 UTC precipitation series start by the analysis date and have no recorded end. Nearest-station assignment for the reviewed resort components requires **7 stations**.

The reviewed panel contains **1,744 complete weather-proxy months**; **1,576 rows** also have an observed hotel-night outcome. Station-specific calendar-month anomalies use 2013–2025 usable observations. Two station-months fail the 80% precipitation coverage gate and remain missing. These are regional station proxies, not piste microclimate or snowfall-phase measures, and no weather field is yet approved as a causal covariate.

## Temporal controls

A deterministic calendar table covers **168 months** from January 2013 through December 2026 and joins to **1,848 of 1,848 reviewed destination-month rows**. It records calendar month/quarter, winter and summer indicators, the December/January holiday peak, and the Gregorian Easter month.

The table also flags March 2020 through April 2022 as a deliberately broad COVID sensitivity interval. This marks **286 reviewed destination-month rows**. It is not a legal chronology of canton-specific restrictions or travel rules. Any later event-study diagnostic must therefore report at least a full-sample specification, exclusion of this broad interval, and documented alternative period definitions; the flag does not by itself remove COVID confounding.

## Same-destination distance gradient

Following the researcher's proposed comparison, the pipeline now measures each of 186 hotel municipality series against the component resort points of each reviewed treated destination while keeping that destination fixed. The resulting **2,046 destination–municipality rows** retain both representative-point and minimum-polygon distance. For the seven continuity-plus-24/24 destinations, **1,246 municipality rows** have at least 18 observed months in both adjacent 24-month windows.

**6 of seven** treatment-specific near-versus-far contrasts are descriptively positive when municipalities at most 30 km away are compared with municipalities beyond 50 km and the 30–50 km band is omitted. Moléson is the exception. This pattern is exploratory only: current 2026 boundaries are applied to historical outcomes, hotel locations and travel time are unavailable, and the adjacent windows do not remove common shocks, COVID, competing passes or investment. See `reports/15_TREATMENT_DISTANCE_GRADIENT.md`; all effect and exposure approval flags remain false.

## Membership-continuity audit

Entry events, full official rosters, named continuation statements, and the documented Crans-Montana exit were checked season by season. Missing annual evidence remains unverified rather than being filled as active or inactive.

- Reviewed units with every active season explicitly documented: **14**
- Such units that also enter the outcome panel: **11**
- Such panel units with both 24 observed pre months and 24 observed active-post months: **7**

The detailed audit is in `reports/membership_continuity_audit.csv`. The final count is an evidence/coverage screen, not a count of identified effects. Seasonal documentation does not establish identical summer access, precise treatment intensity, absence of confounding, or a valid counterfactual. Zero controls and zero treatment units are approved for causal estimation. The additional dated rosters and operator/tourism documents are reviewed in `reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md`.

Annual launch lists and map symbols now classify winter versus summer-winter access for **58 active destination-unit seasons across 7 annual publications**. **36** of those unit-seasons have documented summer access for at least one published component label. Composite destinations retain mixed-component labels rather than being flattened. See `reports/10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md`; summer inclusion is not evidence of daily operation or causal tourism exposure.

## Donor/control contamination screen

The pipeline screened **814** treatment-municipality pairs. A deliberately provisional flag removes known resolved Magic exposure, precautionary composite/overlapping scope risks, the treated municipality scope, donors within 30 km, donors with fewer than 36 observed pre months, and donors with fewer than 24 post months. Resolving the current Sattel-Hochstuckli label exposes one additional Magic-linked municipality. The scope review excludes **4 additional municipalities**, leaving **52** apparent controls and **404** pairs passing the 30 km screen; **366** survive a 50 km sensitivity screen.

For the seven continuity-plus-coverage treatments, the pre-trend screen ranks **315** provisional pairs from the 36 pre-anchor months and retains **35** top-five pairs for manual review. The heuristic combines outcome level, deseasonalized trend, seasonality, standardized shape, bed capacity, distance and current resort-directory structure. **Zero are approved causal controls** because historical donor membership, spillovers beyond simple distance, accessibility, time-varying confounders and formal balance remain unresolved. See `reports/11_DONOR_PRETREND_SCREEN.md`.

The first screen measured distance only to the treatment being evaluated. A network-wide audit now shows that **15 of the 35 shortlisted pairs** use a donor municipality within 30 km of some historically or currently resolved Magic Pass resort point; only **7 pairs** lie beyond 50 km from every resolved point. This is a lower-bound proximity screen because 26 official labels remain unresolved, and distance cannot prove spillovers or their absence. See `reports/14_DONOR_NETWORK_SPILLOVER_AUDIT.md`.

See `reports/control_contamination_audit.csv`, `reports/control_candidates_by_treatment.csv`, and `reports/donor_pretrend_shortlist.csv`.

## Model-family decisions

| Model family | Current decision | Evidence-based reason |
|---|---|---|
| Municipality fixed-effects panel | Diagnostic-ready only | Eleven reviewed outcome units, documented seasonal membership, monthly hotel capacity, deterministic calendar/COVID sensitivity flags, SLF snow proxies, and MeteoSwiss temperature/precipitation proxies can be represented, but treatment intensity, remaining confounding, spillovers, and controls remain unresolved. |
| Staggered Difference-in-Differences | Not credible yet | Reviewed-unit membership continuity is documented, but treatment intensity, pre-trends, spillovers and untreated-control status are not validated. |
| Matching | Descriptive only | A pre-period comparability screen now prioritises 35 donor pairs for manual review, but historical non-membership, spillovers, accessibility and covariate balance remain unapproved. |
| Synthetic control / synthetic DiD | Case-study candidate | Could be assessed for a few clearly mapped municipalities with uncontaminated donors; no donor pool is approved yet. |
| Causal forest | Not supported | At most 14 provisional treated municipalities is far below a defensible heterogeneous-effect sample. |
| X-Learner | Not supported | The effective treated-unit count is too small and treatment labels are not final. |
| DR-Learner | Not supported | The effective treated-unit count is too small and nuisance models would be unstable. |
| Gradient boosting | Deferred | Potentially useful for ordinary prediction after features exist, but not evidence of membership uplift. |
| Random forest | Deferred | Potentially useful as a grouped predictive benchmark; current independent destination sample is unresolved. |
| Neural network | Rejected | Monthly rows do not create independent resorts; the effective cross-sectional sample is far too small. |

## Main identification risks

1. Selection into Magic Pass and pre-existing trends are unmeasured.
2. Resort listings, lift clusters, official pass destinations, and tourism municipalities are different units.
3. Several resorts share the same municipality; some destinations span several municipalities.
4. Crans-Montana proves that treatment is not universally absorbing.
5. COVID overlaps the post-period of early entrants and the entry period of later ones.
6. Spillovers may contaminate nearby nominal controls.
7. Hotel capacity, mountain-station snow, and regional temperature/precipitation proxies are integrated, but snowmaking, accessibility, investment, local economic conditions, and competing-network changes remain unmeasured.

## Next evidence gate

Resolve the four Swiss labels without a supplied-listing relation and the ambiguous Les Diablerets scope, document historical membership and spillovers for the apparent donors, validate treatment intensity and winter-versus-summer definitions, and add the remaining time-varying confounders. Complete regional-weather sensitivity and an independent gridded snow sensitivity; the next-nearest SLF-station test alone is not sufficient. Only then reassess fixed-effects/event-study or case-study synthetic-control feasibility. Complex heterogeneous-effect ML remains unjustified unless the effective treated-destination count increases substantially.
