# Thesis chapter draft — Results

> Draft generated from the validated Path C v0.31 outputs. This chapter reports feasibility and descriptive evidence; it does not report a Magic Pass treatment effect.

## 1. Data foundation and treatment panel

The audit retained **271 directory listings**, **242 preserved lift clusters** and **186 hotel municipalities**. Of the lift clusters, 162 were linked to at least one directory listing and 156 had complete structural fields for segmentation. The hotel panel covered January 2013 to March 2026 and contained 28455 observed monthly overnight-stay values.

Official Magic Pass material yielded **88 documented base-entry events**. After conservative entity resolution and destination-scope review, 14 destination units were retained and 11 entered the hotel panel. All reviewed units had documented active-season continuity, but only 7 panel units combined that evidence with at least 24 observed pre and 24 active-post months. No destination was approved as a causal treatment unit.

## 2. Causal and machine-learning feasibility

The donor screen initially considered 814 treatment–municipality combinations. Mechanical distance and coverage rules retained 404 pairs under the 30 km screen and 366 under the 50 km sensitivity. The descriptive pre-trend stage ranked 315 pairs and retained 35 for manual review.

The network audit showed that 28 of the 35 shortlisted pairs lay within 50 km of another resolved Magic Pass point. Of the seven remote pairs, every donor had an independently documented contemporaneous local shock. No shortlisted donor survived the combined proximity and external-shock review, leaving **0 deep-audit pairs, 0 approved controls and 0 approved causal treatments**.

Checkpoint 4 therefore rejected causal estimation. Checkpoint 5 also rejected causal forests, meta-learners and neural networks because there was no defensible causal target and the effective treated sample was at most 14 reviewed units, only seven with the required 24/24 continuity and outcome coverage. No CATE, uplift or treatment-effect prediction was produced.

## 3. Structural segmentation and support

The selected two-segment structural solution achieved silhouette **0.514** and high subsample stability (median ARI **0.987**, 10th percentile **0.924**). Among **104 apparent candidates**, 74 had good support relative to the reviewed treated references, 5 were moderate extrapolations and 25 were strong extrapolations.

Sensitivity to within-cluster aggregation was substantial. Although minimum, median and maximum rules all selected k=2, segment ARI relative to the median solution fell to **0.827** under minimum aggregation and **0.714** under maximum aggregation. Only **11 of 104 candidates** preserved every recorded segment, nearest-analogue and treated-support criterion. Seventy-one retained the same closest reviewed treated analogue and 60 retained the same treated-reference support category. These results justify reporting candidate-specific stability rather than a single league table.

## 4. Tourism-scope evidence

Component-point municipalities exactly reproduced 10 of 11 reviewed outcome municipality sets, but seven of those matches were core-municipality proxies defined from the same component logic. Among the four independently reviewed complete municipal scopes, only three matched exactly and component points recovered four of five municipalities. Meiringen-Hasliberg supplied the principal mismatch because the resort point lies in Hasliberg while the reviewed outcome scope also includes Meiringen.

The radius sensitivity confirmed a precision–recall trade-off. Point containment recovered four of five links with no extras. A 5 km rule recovered all five but added **25 municipalities**, and a 10 km rule added **60**. Although 99 candidates obtained an observed HESTA ratio under at least one rule, only 39 had complete hotel context under any rule and zero catchments were validated.

## 5. Climate and snow robustness

The alternative SLF-station test classified 11 of 15 component comparisons as high or moderate and four as low. Median winter-depth correlation was **0.864**, while the median relative absolute depth difference was **47.2%**. SPASS comparison at station locations was uniformly high or moderate, but resort-centred comparison was low for 8 of 15 components. This pattern identifies station-to-resort location and elevation mismatch as the principal limitation of the snow proxy.

Weather anomalies were more robust to station choice. All 15 alternative-station comparisons were high or moderate; median temperature- and precipitation-anomaly correlations were **0.967** and **0.815**. The official 1 km grids produced median correlations of **0.983** and **0.942**, although two component comparisons were low. None of these sensitivities converted a climate field into an approved causal covariate.

## 6. Accessibility and transport

The scheduled GTFS analysis produced **49104 samples**, of which 38504 were feasible under the six-vehicle and eight-hour limits. Across 2046 destination–municipality pairs, 1104 were feasible at every sampled time. Median outbound and return generalized times were **246.3** and **243.1 minutes**.

Ten destinations supported a bidirectional distance/time rank correlation. The median correlation was **0.743**, ranging from 0.607 to 0.869. At the 0.25 rank-gap threshold, 225 pairs had worse transit access than straight-line distance suggested and 171 had better access. Distance is therefore informative but not interchangeable with scheduled travel time.

## 7. Competition and network context

The historical multi-area-pass register covered five products over 21 product-seasons. It contained **155 area-season rows** and **184 positive listing-season links**, reaching 52 listings and 37 lift clusters. Thirty candidates had at least one documented historical link; 19 had every cluster listing linked in at least one reviewed product-season and 11 were partial mixed-listing clusters. SnowPass remained winter-only, and product-level summer statements were not widened to individual areas.

This reconstruction improved positive-presence coverage but did not produce a full historical market panel. Zero non-links were verified as market absence, so historical competition remained descriptive context rather than a treatment, predictor or ranking feature.

## 8. Final decision framework

Checkpoint 6 assigned 19 evidence groups to seven dimensions. Thirteen groups had complete candidate coverage, two were partial and four had no candidate feature. Only structural similarity was approved for exploratory use. **Zero groups** were approved as pre-treatment predictors, causal covariates, recommendation inputs or composite-score inputs.

The final dashboard contains 104 candidate clusters. It produces **0 predicted-uplift values, 0 recommendations, 0 composite scores and 0 causal approvals**. No candidate meets the complete Opportunity × Strategic Need gate. The empirical result is therefore a qualified multidimensional evidence system, not a ranked expansion recommendation.
