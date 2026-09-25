# Thesis chapter draft — Methods

> Draft generated from the validated Path C v0.31 outputs. Adapt numbering and citation style to the final thesis template. Counts are pipeline-derived and must remain linked to the cited repository outputs.

## 1. Research design

The study followed a sequential, feasibility-gated Business Analytics design. The initial objective was to estimate whether Magic Pass participation affected hotel overnight stays and, if identification proved credible, to study heterogeneous effects and transfer the resulting evidence to non-member ski destinations. The design did not assume that a particular causal or machine-learning method would be suitable. Instead, six checkpoints progressively assessed the existing data, treatment definition, panel coverage, causal identification, machine-learning feasibility and final decision-support architecture.

Checkpoints 1–3 constructed and audited the empirical foundation. Checkpoints 4–5 treated causal inference and heterogeneous-effect modelling as hypotheses to be accepted only if treatment, outcome, donor and temporal-support conditions were met. Because those gates failed, Checkpoint 6 selected Path C: an exploratory structural-analogue dashboard in which descriptive opportunity, vulnerability, tourism context, accessibility, competition and uncertainty remain separate. This fallback was precluded from producing treatment-effect predictions, a composite score or a candidate ranking.

## 2. Units of analysis and entity resolution

The supplied directory contained **271 resort listings**. These listings were not assumed to represent independent ski destinations because several names can refer to components of one domain and one preserved lift cluster can contain multiple directory rows. The existing geographic clustering was therefore audited rather than rebuilt. It contains **242 lift clusters**, of which **162** link to at least one supplied listing. Stable `resort_id`, `cluster_id`, `destination_unit_id` and BFS municipality identifiers were retained throughout.

Magic Pass evidence was resolved from official dated publications. Candidate links were reviewed conservatively and ambiguous labels were not forced into one-to-one matches. Eighteen candidate-linked entry components were collapsed into **14 reviewed destination units**. **11** had an explicit hotel-outcome scope; three composite destinations were excluded because the available municipality panel covered only part of their geography. Membership continuity and winter/summer modality were stored separately. All 14 reviewed units have documented active seasons, while modality evidence exists for 58 active unit-seasons.

## 3. Hotel outcome and capacity panel

The main outcome was monthly hotel overnight stays at municipality level. The processed panel contains **31248 municipality-month rows** for **186 municipalities**, with **28455 observed overnight-stay cells** between January 2013 and March 2026. Suppressed source values remained missing and were not imputed. Establishments, rooms and beds were retained as supply-side context. For multi-municipality destination units, count variables were summed only when every municipality in the reviewed scope was observed; published occupancy rates were not averaged across municipalities.

The reviewed destination panel contains **1848 destination-month rows**, including **1581 observed outcomes** and **1637 complete capacity rows**. Entry seasons provided diagnostic anchors rather than exact treatment dates. The carry-forward membership rule was explicitly treated as a diagnostic coding assumption, not causal exposure validation.

## 4. Climate, snow and temporal context

Snow conditions were represented first through the nearest eligible long-running SLF station, retaining distance, elevation difference, winter coverage and proxy quality. A next-nearest-station sensitivity test was run for all **15 reviewed components**. It yielded 6 high, 5 moderate and 4 low comparisons, with a median winter-depth correlation of **0.864**. A second sensitivity used the SPASS 1 km modelled snow product at resort and station locations. All **150 component-winter rows** were complete, but resort-centred disagreement remained material.

Regional temperature and precipitation context used eligible SwissMetNet stations and calendar-month anomalies. The next-nearest-station comparison produced median component correlations of **0.967** for temperature and **0.815** for precipitation. Official 1 km TabsM/RhiresM grids supplied an additional spatial sensitivity. These products were treated as regional proxies, not direct piste measurements or automatically valid causal covariates. Deterministic month, winter/summer, peak-season, Easter and broad COVID-sensitivity indicators were generated for the full panel.

## 5. Accessibility, tourism and competitive context

Accessibility was deliberately measured in several non-equivalent ways: straight-line population context, cross-border population grids, modelled NPVM travel time, distance to official passenger stops and national-road axes, and scheduled public-transport journeys. The GTFS calculation sampled five outbound departure times from 08:00–10:00 and seven return times from 15:00–18:00 on one winter weekday and one Saturday. It produced **49104 journey samples** for **2046 destination–municipality pairs**. The measure is a winter-2026 timetable snapshot; historical stability was not assumed.

Tourism dependence was reported for the reviewed outcome scopes and, separately, for municipalities containing candidate component points. Candidate rules based on 0, 5 and 10 km municipality buffers were evaluated against the independently reviewed complete destination scopes. These rules were sensitivity analyses rather than definitions of a visitor catchment.

Competitive context combined three current multi-area-pass rosters with dated positive-presence evidence for Top4, Meilenweiss, Schneepass Zentralschweiz, TopCard and SnowPass Graubünden. The historical table contains **155 area-season rows** and **184 positive listing-season links**. A missing link means only that no reviewed positive evidence was found; it does not establish historical absence.

## 6. Causal feasibility assessment

The causal screen required an explicit destination scope, documented membership continuity, sufficient pre/post outcomes, historically credible non-treated donors, limited spillover risk and no major contemporaneous donor-specific shock. This is stricter than selecting an available estimator: staggered Difference-in-Differences still requires a credible parallel-trends comparison and careful treatment of heterogeneous timing and effects (Callaway and Sant'Anna, 2021; Sun and Abraham, 2021), while connected ski markets make interference a substantive threat rather than a technical footnote (Hudgens and Halloran, 2008). Seven treatments supported a 36-month descriptive pre-period screen. Among **315 provisional pairs**, 35 top-five pairs were shortlisted for manual review. Network proximity deprioritised **15 pairs within 30 km** and **13 pairs between 30 and 50 km**. The seven pairs beyond 50 km were all excluded because official evidence documented a contemporaneous donor-specific tourism, pricing, access or infrastructure shock. Consequently, zero treatments and zero controls were approved for causal estimation.

## 7. Path C structural segmentation and analogues

Path C used only three structural directory fields: median published top altitude, median published ski-area kilometres and median published lift count. Ski area and lift count were log-transformed before standardisation. Geography, membership, hotel outcomes, tourism dependence and snow vulnerability were excluded from the similarity model so that labels, outcomes and strategic dimensions did not define structural resemblance.

Deterministic k-means solutions from k=2 to k=8 were compared using average silhouette width (Rousseeuw, 1987), minimum segment size and 80% subsample adjusted Rand stability, whose chance-corrected partition-comparison foundation follows Hubert and Arabie (1985). The selected **k=2** solution had silhouette **0.514**, median bootstrap ARI **0.987** and 10th-percentile ARI **0.924**. Apparent non-member candidates were compared with structurally complete current Magic Pass clusters and with eight reviewed treated reference units. The resulting analogue signal is the median unadjusted post-versus-pre diagnostic of the three nearest reviewed treated references; it is not predicted uplift.

Within-cluster minimum, median and maximum aggregation rules were then compared. All selected k=2, but assignment and nearest-analogue stability varied. Candidate-level stability flags were retained rather than selecting the most favourable aggregation.

## 8. Decision framework and reproducibility

The final dashboard assigns **19 feature groups** exactly once across seven decision dimensions. Candidate coverage and permitted use are separate fields. Only structural similarity is authorised for exploratory matching. Zero groups are approved as pre-treatment predictors, causal covariates, recommendation inputs or composite-score inputs. Candidate rows remain sorted by stable cluster ID.

All source files are checksum-audited, external evidence is registered in the provenance table, and analytical variables are described in the data dictionary. The offline pipeline regenerates processed tables, diagnostics, reports, figures and automated tests from the project root. Raw inputs are never overwritten.
