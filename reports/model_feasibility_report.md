# Model feasibility report

Generated reproducibly by `src/data_processing/build_feasibility_report.py`.

## Executive verdict

**Checkpoints 4 and 5 fail under the present design.** The project therefore follows **Path C (weak treatment sample / exploratory decision support)**. Destination scope, reviewed-unit season-by-season membership, monthly hotel capacity, and qualified snow/weather proxies are integrated, but the current donor shortlist is exhausted and the effective treated sample is too small for heterogeneous-effect ML.

No causal model, treatment-effect learner, predicted uplift, composite opportunity score, or neural network is authorised. A separate Path C module now builds current structural segments and descriptive analogues, with out-of-distribution flags and no causal interpretation.

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
- Resolved historical/current Magic links reduce the 74-municipality resort-point universe to an upper bound of **56** apparent controls. The **26** base-entry labels without one-to-one supplied-directory links have all received conservative scope classifications; the remaining problem is not an unreviewed label backlog but the absence of identity-equivalent mappings and a valid donor pool. **Zero controls are approved.**

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

A next-nearest-station sensitivity covers all **15 reviewed resort components** using the same station coverage gate. **11 components** receive a high or moderate descriptive agreement grade and **4** receive a low grade. The median winter-depth correlation is **0.864**, but the median relative mean absolute depth difference is **47.2%**; absolute snow levels are therefore materially station-dependent even when seasonal variation co-moves. See `reports/13_SNOW_PROXY_SENSITIVITY.md`.

The peer-reviewed SPASS OSHD-CLQM grid adds **150 component-winter comparisons**, all complete for the ten common winters 2013/14–2022/23. Around the selected stations, all **15 components** have high/moderate agreement with median correlation **0.897** and median relative depth difference **25.9%**. Repeating the same 3×3 rule around the resort points leaves only **7 high/moderate and 8 low**, while the median relative difference rises to **61.9%**. This decomposition identifies station-to-resort placement/elevation as the dominant representativeness problem. The 1 km model is quantile-mapped against a snow-assimilating SLF model and is therefore not an independent measurement network, piste observation or causal approval. See `reports/36_SNOW_GRIDDED_SENSITIVITY.md`.

## Temperature and precipitation proxy coverage

Official MeteoSwiss inventory metadata identifies **112 current SwissMetNet stations** whose daily mean/minimum/maximum temperature and 06:00-to-06:00 UTC precipitation series start by the analysis date and have no recorded end. Nearest-station assignment for the reviewed resort components requires **7 stations**.

The reviewed panel contains **1,744 complete weather-proxy months**; **1,576 rows** also have an observed hotel-night outcome. Station-specific calendar-month anomalies use 2013–2025 usable observations. Two station-months fail the 80% precipitation coverage gate and remain missing. These are regional station proxies, not piste microclimate or snowfall-phase measures, and no weather field is yet approved as a causal covariate.

A next-nearest-eligible-station sensitivity now covers all **15 reviewed components** using **10 distinct alternative stations** and the same parameters, monthly coverage gate and station-specific normals. All **15 components** receive high or moderate descriptive agreement and **0** receive low agreement. Median component anomaly correlation is **0.967 for temperature** and **0.815 for precipitation**. Both destination-level proxies are complete for **1,737 months**; median destination correlations are **0.959** and **0.885**. This supports regional anomaly robustness but remains a same-network station sensitivity, not independent gridded or piste validation. See `reports/34_WEATHER_STATION_SENSITIVITY.md`; causal approval remains false.

The official 1 km TabsM/RhiresM check adds **32 checksum-matched NetCDF assets** and **2,385 component-month rows**, all complete. Station-grid agreement is high or moderate for **13 components** and low for **2** (Axalp and Meiringen-Hasliberg). Median component correlations are **0.983 for temperature** and **0.942 for precipitation**. At destination level, both sources are complete for **1,744 rows**, with median correlations of **0.980** and **0.942**. This closes the gridded-product sensitivity gate for regional weather, but TabsM/RhiresM remain station-informed analyses rather than an independent measurement network or piste observation. See `reports/35_WEATHER_GRIDDED_SENSITIVITY.md`; causal approval remains false.

## Temporal controls

A deterministic calendar table covers **168 months** from January 2013 through December 2026 and joins to **1,848 of 1,848 reviewed destination-month rows**. It records calendar month/quarter, winter and summer indicators, the December/January holiday peak, and the Gregorian Easter month.

The table also flags March 2020 through April 2022 as a deliberately broad COVID sensitivity interval. This marks **286 reviewed destination-month rows**. It is not a legal chronology of canton-specific restrictions or travel rules. Any later event-study diagnostic must therefore report at least a full-sample specification, exclusion of this broad interval, and documented alternative period definitions; the flag does not by itself remove COVID confounding.

## Same-destination distance gradient

Following the researcher's proposed comparison, the pipeline now measures each of 186 hotel municipality series against the component resort points of each reviewed treated destination while keeping that destination fixed. The resulting **2,046 destination–municipality rows** retain both representative-point and minimum-polygon distance. For the seven continuity-plus-24/24 destinations, **1,246 municipality rows** have at least 18 observed months in both adjacent 24-month windows.

**6 of seven** treatment-specific near-versus-far contrasts are descriptively positive when municipalities at most 30 km away are compared with municipalities beyond 50 km and the 30–50 km band is omitted. Moléson is the exception. This pattern is exploratory only: current 2026 boundaries are applied to historical outcomes, hotel locations and validated historical origin-to-destination travel times are unavailable, and the adjacent windows do not remove common shocks, COVID, competing passes or investment. See `reports/15_TREATMENT_DISTANCE_GRADIENT.md`; all effect and exposure approval flags remain false.

## Cross-border population context

The official Eurostat 2021 census grid supplies a harmonised one-kilometre population reference on both sides of the Swiss border. The checksum-verified source contains **4,595,932 rows**; the regional extract retains **181,598 cells** and covers all **162 linked clusters** and **104 apparent candidates**. Foreign-only population occurs within 30 km for **73 candidates** and within 120 km for **104 candidates**. Across all linked clusters, the median foreign-only share of observed population is **20.6% at 60 km** and **36.7% at 120 km**.

This resolves the known geographic truncation of the earlier Swiss-only radius totals, but it is still straight-line residential context rather than a skier or visitor catchment. Mixed Swiss/foreign border cells remain separate, unallocated national records are excluded, and the 2021 grid is not merged numerically with STATPOP 2025. No accessibility or causal feature is approved. See `reports/29_CROSS_BORDER_POPULATION_CONTEXT.md`.

## National-road-axis proximity

The current FEDRO/ASTRA source supplies **3,084 line features** across the official main, feeder, connection and ramp axis layers. Straight-line EPSG:2056 distances are available for **268 Swiss listing points**. Across linked clusters, the median of cluster-median distances is **6.81 km** to a main national-road axis and **6.79 km** to any published national-road axis. Context is complete for **103 of 104 apparent candidates**; the cross-border Portes du Soleil cluster remains partial because the source does not provide a complete French road universe.

The published attributes do not classify axes as motorway versus non-motorway. The measure is therefore labelled national-road-axis proximity, not motorway access. It is current point-to-line geometry rather than a route, a usable entrance, driving time, congestion, winter reliability or historical pre-treatment infrastructure; its approval flag and the generic accessibility score remain blank. See `reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md`.

## Competing-pass roster context

Official current material was checksum-cached for **3 competing products** and **43 named pass areas**: AlpsPass 2026/2027, the Meilenweiss retrieval-date roster, and Schneepass Zentralschweiz 2026/2027. Explicit reviewed resort-ID links cover **55 supplied listings in 29 lift clusters**. **10 clusters** are only partially linked because neighbouring listings are not automatically assigned the same pass status. Among the **104 apparent Path C candidates**, **22** contain at least one listing linked to a reviewed roster.

AlpsPass unlimited core access remains distinct from its three-free-ski-days partner benefit. A non-link means only that no explicit link was established in these three rosters; it does not prove absence from every competing product. The snapshots do not reconstruct competition at historical Magic Pass entry dates, so all absence-verification and causal-feature approval flags remain false. See `reports/31_COMPETING_PASS_CONTEXT.md`.

## Current ski-cluster and reviewed pass-network context

The complete **26,082-row ordered non-self pair table** measures great-circle distance among all 162 preserved directory-linked lift clusters. Across the 104 apparent candidates, the median number of other directory clusters is **8 within 25 km** and **26 within 50 km**. The resolved-current-Magic/reviewed-competing-pass union contains **73 clusters**; a candidate has a median **9 other reviewed-network clusters within 50 km**. **1 candidate** has no other directory cluster within 25 km and **2** have no other reviewed pass-network cluster within 50 km.

Every count excludes the focal cluster. The supplied clusters are not validated independent commercial domains, multi-listing median coordinates can be artificial, straight-line distance ignores terrain and transport, published ski-area values are undated and can overlap, and the pass links are current rather than historical. These are therefore directory/network diagnostics rather than true competitor counts, market penetration, visitor flows or causal exposure. Historical and feature-approval flags remain false. See `reports/32_PATH_C_NETWORK_CONTEXT.md`.

## Cluster geography and network-distance sensitivity

The preserved clustering contains **53 multi-listing clusters**. Their median point-to-point diameter is **6.54 km**; the maximum is **46.35 km**, and **1 cluster** exceeds 25 km. Comparing minimum, median and maximum cross-listing-point distances with the existing coordinate-wise-median distance changes the 25 km directory-neighbour count for **71 of 104 candidates** and the 50 km reviewed-network count for **72 candidates**. The largest candidate spans are **13 directory clusters at 25 km** and **11 reviewed-network clusters at 50 km**.

No rule is promoted as the uniquely correct commercial-market distance. Minimum distance is permissive, maximum distance is conservative, and coordinate-wise medians can fall between actual places. The audit preserves all existing cluster assignments and keeps geographic-coherence and feature-approval flags false. See `reports/33_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY.md`.

## NPVM zone-proxy audit

All **98** municipality-constrained NPVM listing-point assignments are exactly reconstructed against the checksum-verified zone and current municipality geometries. They affect **73 clusters**; **50** have no exact listing-point assignment for an internal comparison, including **28** apparent Path C candidates. The geometry and deterministic choice are validated, but proxy-only travel times are not independently validated observed routes. Historical zone lineage and causal approval remain false. See `reports/27_TRANSPORT_ZONE_PROXY_AUDIT.md`.

## Scheduled public-transport journey context

The official winter-2026 Swiss GTFS timetable now supplies **49,104 scheduled routing requests** across **2,046 destination–municipality pairs**. Morning departures are sampled from 08:00 to 10:00 and return departures from 15:00 to 18:00 on one winter weekday and one winter Saturday. **38,504 samples** meet the six-vehicle and eight-hour limits; **1,104 pairs** are feasible at every sampled time. Municipality origins use the most frequently served train stop inside the municipality where possible, with a terrestrial-stop fallback. All **15** component arrival nodes have passed the versioned current name/mode/municipality/distance review for descriptive routing; **6** are transparently retained as village/local-centre proxies under the researcher's fallback rule, and **1** has a reference-day availability warning. This is not historical or causal approval. See `reports/24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md` and `reports/26_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW.md`.

The official archive index exposes snapshots for **7 relevant timetable years**, but **0 historical component nodes** have yet undergone actual stop/service comparison. The 2026 journey measure is therefore useful descriptive context, not a historically stable pre-treatment or causal covariate. See `reports/25_PUBLIC_TRANSPORT_HISTORICAL_AUDIT.md`.

Comparing the same municipality–destination pairs shows why distance and transit time must remain separate. **1,700 pairs** have both outbound and return means. Across **10 destinations**, the median within-destination distance–round-trip rank correlation is **0.743**, while **225 pairs** have transit rank at least 0.25 worse than distance rank suggests. This is a current descriptive disagreement diagnostic, not historical exposure or an effect. See `reports/28_DISTANCE_TRANSPORT_COMPARISON.md`.

## Membership-continuity audit

Entry events, full official rosters, named continuation statements, and the documented Crans-Montana exit were checked season by season. Missing annual evidence remains unverified rather than being filled as active or inactive.

- Reviewed units with every active season explicitly documented: **14**
- Such units that also enter the outcome panel: **11**
- Such panel units with both 24 observed pre months and 24 observed active-post months: **7**

The detailed audit is in `reports/membership_continuity_audit.csv`. The final count is an evidence/coverage screen, not a count of identified effects. Seasonal documentation does not establish identical summer access, precise treatment intensity, absence of confounding, or a valid counterfactual. Zero controls and zero treatment units are approved for causal estimation. The additional dated rosters and operator/tourism documents are reviewed in `reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md`.

Annual launch lists and map symbols now classify winter versus summer-winter access for **58 active destination-unit seasons across 7 annual publications**. **36** of those unit-seasons have documented summer access for at least one published component label. Composite destinations retain mixed-component labels rather than being flattened. See `reports/10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md`; summer inclusion is not evidence of daily operation or causal tourism exposure.

## Donor/control contamination screen

The pipeline screened **814** treatment-municipality pairs. A deliberately provisional flag removes known resolved Magic exposure, precautionary composite/overlapping scope risks, the treated municipality scope, donors within 30 km, donors with fewer than 36 observed pre months, and donors with fewer than 24 post months. Resolving the current Sattel-Hochstuckli label exposes one additional Magic-linked municipality. The scope review excludes **4 additional municipalities**, leaving **52** apparent controls and **404** pairs passing the 30 km screen; **366** survive a 50 km sensitivity screen.

For the seven continuity-plus-coverage treatments, the pre-trend screen ranks **315** provisional pairs from the 36 pre-anchor months and retains **35** top-five pairs for manual review. The heuristic combines outcome level, deseasonalized trend, seasonality, standardized shape, bed capacity, distance and current resort-directory structure. **Zero are approved causal controls** because network spillovers, accessibility, time-varying confounders and formal balance are not jointly cleared. See `reports/11_DONOR_PRETREND_SCREEN.md`.

The first screen measured distance only to the treatment being evaluated. A network-wide audit now shows that **15 of the 35 shortlisted pairs** use a donor municipality within 30 km of some historically or currently resolved Magic Pass resort point; only **7 pairs** lie beyond 50 km from every resolved point. This remains a lower-bound proximity screen because scope-classified labels without one-to-one directory links cannot all be represented as points, and distance cannot prove spillovers or their absence. See `reports/14_DONOR_NETWORK_SPILLOVER_AUDIT.md`.

The official-source review uses complete annual Magic Pass rosters to document station-label absence for all **7** geographically remote pairs. Operator and government evidence then excludes **all 7 pairs** because a donor-specific tourism, pricing, access or infrastructure shock overlaps the relevant post window. **0 pairs remain for deep manual audit.** Exact regional-pass operator terms are still qualified, but no exclusion depends on resolving them. See `reports/16_DONOR_EXTERNAL_SHOCK_AUDIT.md`; approved controls remain zero.

See `reports/control_contamination_audit.csv`, `reports/control_candidates_by_treatment.csv`, and `reports/donor_pretrend_shortlist.csv`.

## Model-family decisions

| Model family | Current decision | Evidence-based reason |
|---|---|---|
| Municipality fixed-effects panel | Diagnostic-ready only | Eleven reviewed outcome units, documented seasonal membership, monthly hotel capacity, deterministic calendar/COVID sensitivity flags, SLF snow proxies, and MeteoSwiss temperature/precipitation proxies can be represented, but treatment intensity, remaining confounding, spillovers, and controls remain unresolved. |
| Staggered Difference-in-Differences | Not credible yet | Reviewed-unit membership continuity is documented, but treatment intensity, pre-trends, spillovers and untreated-control status are not validated. |
| Matching | Causal use rejected | The 35-pair donor shortlist is exhausted by network proximity or overlapping donor-specific shocks; zero controls are approved. |
| Synthetic control / synthetic DiD | Not credible under present donor design | Every shortlisted pair is deprioritised or excluded; a future attempt requires a redesigned and broader donor search. |
| Causal forest | Not supported | At most 14 provisional treated municipalities is far below a defensible heterogeneous-effect sample. |
| X-Learner | Not supported | The effective treated-unit count is too small and treatment labels are not final. |
| DR-Learner | Not supported | The effective treated-unit count is too small and nuisance models would be unstable. |
| Gradient boosting | Not run | No defensible cluster-level supervised target exists; an unadjusted post-entry change is not a membership-uplift label. |
| Random forest | Not run | No defensible cluster-level supervised target exists and current lift clusters are not certified independent destinations. |
| Neural network | Rejected | Monthly rows do not create independent resorts; the effective cross-sectional sample is far too small. |
| K-means plus nearest analogues | Selected for exploratory Path C | Uses current undated structural features only, keeps snow vulnerability separate, reports stability/OOD support, and never labels analogue changes as causal uplift. |

## Main identification risks

1. Selection into Magic Pass and pre-existing trends are unmeasured.
2. Resort listings, lift clusters, official pass destinations, and tourism municipalities are different units.
3. Several resorts share the same municipality; some destinations span several municipalities.
4. Crans-Montana proves that treatment is not universally absorbing.
5. COVID overlaps the post-period of early entrants and the entry period of later ones.
6. Spillovers may contaminate nearby nominal controls.
7. Hotel capacity, mountain-station snow, regional temperature/precipitation, qualified Swiss and cross-border straight-line population, NPVM 2025 context, current OFT/BAV stop proximity, current FEDRO/ASTRA national-road-axis proximity, winter-2026 scheduled journeys and three current competing-pass rosters are integrated. Historical timetable stability, historical competing-network changes, snowmaking, true motorway-entrance access, investment and local economic conditions remain unmeasured.

## Next evidence gate

For Path C, obtain the historical GTFS anchor feeds manually or through an authorised channel before applying the same routing rules; validate destination catchments for tourism dependence; reconstruct historical competing-pass rosters if competition is to become a pre-treatment feature; and obtain dated infrastructure features. Current competing-pass links, national-road-axis proximity, listing-point distance-rule sensitivity, next-nearest SwissMetNet weather sensitivity, TabsM/RhiresM gridded weather and SPASS gridded snow sensitivities are complete within their declared source scopes, while a true motorway-access measure would require explicit road-class and entrance data. The cross-border population context and NPVM proxy geometry audit are complete, but 50 proxy-only clusters still lack an internal exact-zone sensitivity reference. If door-to-lift precision becomes necessary, supplement the completed current arrival-node review with walking/access evidence. Keep the completed structural aggregation, network-distance and climate sensitivities and preserve separate opportunity, vulnerability, comparability and data-quality dimensions. Add an independent measurement/reanalysis sensitivity only if climate fields are proposed for causal use. Any return to Path B requires a redesigned broader donor search, validated treatment intensity/exposure and stronger time-varying confounders. Complex heterogeneous-effect ML remains unjustified unless the effective treated-destination count increases substantially.
