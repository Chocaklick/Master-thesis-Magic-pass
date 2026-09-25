# Thesis results synthesis — Path C v0.31

## Research conclusion

The validated data support an **exploratory Business Analytics decision-support architecture**, not a causal Magic Pass effect model and not a candidate ranking. Checkpoints 1–3 establish a reproducible data foundation. Checkpoint 4 rejects causal estimation under the present design because there are **0 approved treatment units** and **0 approved controls**. Checkpoint 5 rejects heterogeneous-effect machine learning because the effective treated-destination sample is too small and no defensible causal target exists. Checkpoint 6 therefore retains a seven-dimension evidence dashboard with protected blank uplift, composite-score and recommendation fields.

This negative feasibility result is substantive: the project prevents a technically elaborate model from being presented as causal when treatment exposure, donor validity, spillovers and pre-treatment comparability are not identified.

## Analytical foundation

| Empirical layer | Validated scope | Thesis interpretation |
|---|---:|---|
| Supplied resort listings | 271 | Directory listings, not independent destinations |
| Existing lift clusters | 242 | Preserved; 162 link to at least one listing |
| Hotel municipalities | 186 | 28455 observed monthly overnight-stay cells, 2013-01 to 2026-03 |
| Reviewed destination units | 14 | 11 enter the outcome panel; three composite scopes are excluded |
| Apparent Path C candidates | 104 | Screening universe, not verified non-membership or recommended resorts |
| Historical competing-pass context | 155 area-season rows | 184 conservative positive listing-season links; non-links are not absence |
| Scheduled public-transport comparison | 2046 destination–municipality pairs | Current winter-2026 context, not historical accessibility |

## Feasibility gates

| Gate | Result | Consequence |
|---|---:|---|
| Approved causal treatment units | 0 | No defensible event-study/DiD treatment sample |
| Approved controls | 0 | No promoted donor comparison |
| Candidate catchments validated | 0 | Municipal tourism intensity remains qualified context |
| Pre-treatment feature groups approved | 0 / 19 | No supervised candidate-uplift model |
| Causal covariate groups approved | 0 / 19 | No causal adjustment using current/post-treatment context |
| Candidates ready for full Opportunity × Strategic Need matrix | 0 / 104 | No complete matrix or rank |
| Recommendations issued | 0 | Recommendation fields remain intentionally blank |

## Selected Path C architecture

The final architecture separates evidence that would otherwise be easy to conflate. The coverage pattern below is reported at feature-group level; **coverage does not imply analytical permission**.

| Dimension | Groups | Complete / partial / unavailable | Status |
|---|---:|---:|---|
| Structural comparability and support | 3 | 3 / 0 / 0 | qualified_available |
| Descriptive analogue opportunity | 1 | 1 / 0 / 0 | qualified_descriptive_signal_not_effect |
| Snow vulnerability | 1 | 1 / 0 / 0 | qualified_proxy |
| Tourism dependence and destination scope | 3 | 1 / 1 / 1 | incomplete_noncomparable_candidate_scope |
| Population and accessibility context | 7 | 5 / 0 / 2 | qualified_current_context_historical_gap |
| Competition and network context | 3 | 2 / 1 / 0 | qualified_current_context_partial_top4_and_meilenweiss_history_full_historical_market_gap |
| Dated infrastructure and recommendation gate | 1 | 0 / 0 / 1 | blocked_missing_historical_evidence |

Across the 19 groups, **13** have complete candidate coverage, **2** are partial and **4** are unavailable at candidate level. Only the undated structural-similarity group is approved for exploratory similarity; zero groups are approved for prediction, causal adjustment, recommendation or composite scoring.

![Checkpoint 6 evidence coverage](../figures/path_c_evidence_coverage.png)

## Candidate-side descriptive findings

- **74 of 104 candidates (71.2%)** have good structural support relative to the reviewed treated references, while **25 (24.0%)** are strong extrapolations.
- Only **11 candidates (10.6%)** preserve every recorded segment, nearest-analogue and support classification under minimum/median/maximum within-cluster aggregation. This is the strongest reason not to turn analogue results into a league table.
- Point-container tourism context is complete for **39 candidates (37.5%)**. Radius rules reach more candidates but fail destination-catchment validation, so they do not repair the strategic-need dimension.
- A documented positive link to at least one of five partially reconstructed historical competing passes exists for **30 candidates (28.8%)**. The remaining candidates cannot be labelled historically absent from competing passes.

## Accessibility result

Straight-line distance is informative but not interchangeable with scheduled public-transport time. Across the reviewed destinations, **2046** destination–municipality pairs are compared; **1700** have both outbound and return means and **1104** are feasible at every sampled time. The median destination-specific distance/time rank correlation is **0.743**. At the declared rank-gap threshold, **225** pairs have worse transit access than distance suggests. These are current scheduled-access diagnostics, not historical exposure measures.

## Defensible contribution

The contribution is the reproducible integration of hotel demand and capacity, reviewed Magic Pass history, preserved lift clusters, snow and weather sensitivities, population, road and public-transport context, competing-pass history and explicit evidence gates. The dashboard makes useful descriptive heterogeneity visible while preserving the distinction between:

1. data availability and permission to model;
2. structural similarity and treatment-effect similarity;
3. current accessibility and historical pre-treatment accessibility;
4. positive competing-pass evidence and verified market absence;
5. a municipality containing a resort point and a validated tourism catchment.

## Claims the thesis must not make

- It must not report the analogue signal as predicted uplift or a Magic Pass treatment effect.
- It must not rank the 104 candidates as recommendations.
- It must not interpret current competing-pass non-links as historical absence.
- It must not present winter-2026 transport time, current infrastructure or current tourism intensity as pre-treatment covariates.
- It must not describe the preserved lift clusters as certified independent ski destinations.

## Writing implication

The results chapter should lead with the causal/ML feasibility decision, then present Path C as the empirically supported fallback architecture. Candidate-level examples may illustrate how the seven dimensions expose evidence and uncertainty, but stable IDs rather than an opportunity score must determine display order. Missing detailed SnowPass small-lift schedules, historical GTFS feeds, candidate catchments, dated infrastructure, walking access and independent climate measurements belong in limitations and future research unless a specific thesis claim makes one indispensable.
