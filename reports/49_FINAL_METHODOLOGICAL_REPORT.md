# Final methodological report

This report answers the 18 questions required by the authoritative project mission. It is generated from validated Path C v0.31 outputs. Counts use their stated entity level; listings, lift clusters, official destinations, reviewed destination units and municipalities are not silently treated as equivalent.

## Final decision

The available data support a reproducible **exploratory decision-support framework**, not a causal, predictive-uplift or profitability model. Checkpoints 4 and 5 fail because zero treatments and zero controls are causally approved. Checkpoint 6 therefore retains a transparent seven-dimension dashboard with no recommendation ranking or composite score.

## 1. How many ski resorts are available?

**Answer:** 271 directory listings; not 271 independent resorts.

The supplied directory contains 271 listings. The preserved lift layer contains 242 clusters, of which 162 link to at least one listing. Because 53 linked clusters contain multiple listings and commercial-domain boundaries are not certified, no single independent-resort count is claimed.

**Internal evidence:** `reports/01_DATA_AUDIT.md`, `reports/EXISTING_CLUSTER_AUDIT.md`

## 2. How many are Magic Pass members?

**Answer:** 95 official current destinations; 69 conservatively linked directory listings.

The official current-map snapshot contains 95 destinations. Conservative entity resolution links 69 of those labels to supplied directory listings and leaves 26 unresolved. At the preserved cluster level, the Path C feature table contains 51 resolved current Magic clusters; 50 have complete structural fields and form the analogue reference pool. The counts are not interchangeable because destination labels, listings and clusters have different scope.

**Internal evidence:** `data_processed/magic_pass_current_destinations.csv`, `reports/current_magic_pass_summary.json`, `reports/path_c_summary.json`

## 3. How many treated resorts have reliable entry dates?

**Answer:** 14 reviewed destination units have documented entry seasons; none has an exact causal activation date.

The review consolidates 18 component entry events into 14 destination units. All 14 have explicit positive evidence for their active seasons, but entry timing is mainly seasonal rather than an exact activation date and treatment intensity is not homogeneous. Eleven units have an explicit hotel-outcome scope. Zero units are approved as causal treatments.

**Internal evidence:** `reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md`, `reports/membership_continuity_audit.csv`, `reports/treatment_panel_summary.json`

## 4. How many have sufficient pre-treatment observations?

**Answer:** 7 support the 24-month adjacent-window diagnostic; 6 support 36 months.

Under the explicit season carry-forward diagnostic, 7 units have 24 observed pre and 24 active-post months, and 6 have 36 on each side. These are coverage counts, not causal-readiness approvals.

**Internal evidence:** `reports/treatment_panel_summary.json`, `reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md`

## 5. How many have sufficient post-treatment observations?

**Answer:** The same 7 units have 24 active-post months; 6 have 36.

The adjacent-window gate is joint: seven reviewed panel units have both 24 pre and 24 active-post months, while six have both 36 pre and 36 active-post months. Post-period coverage does not resolve treatment intensity, donors, spillovers or contemporaneous shocks.

**Internal evidence:** `reports/treatment_panel_summary.json`, `reports/model_feasibility_report.md`

## 6. Are parallel trends plausible?

**Answer:** Eleven pairs are pre-period compatible, but none is approved as a parallel-trend counterfactual.

A descriptive pre-period screen ranked 315 pairs and shortlisted 35. The later accessibility redesign completed treated/control shock and direct-local-spillover screens, then applied a predeclared 36-month magnitude rule. It retained 11 primary-compatible pairs across 6 treated municipalities, plus 4 relaxed-only pairs. Compatibility under correlation, standardized-RMSE, seasonality and differential-trend thresholds does not prove the unobserved parallel-trends counterfactual; broad visitor substitution and historical transport topology remain unresolved, so zero pairs receive parallel-trend or causal approval.

**Internal evidence:** `reports/11_DONOR_PRETREND_SCREEN.md`, `reports/16_DONOR_EXTERNAL_SHOCK_AUDIT.md`, `reports/69_SCREENING_BASSINS_TOURISTIQUES_SPILLOVERS_FR.md`, `reports/70_DIAGNOSTIC_PRETENDANCES_COMPARAISONS_FR.md`

## 7. Is causal inference credible?

**Answer:** No under the current design.

Zero treatments, controls or pairs pass all causal identification gates. A predeclared matched-comparison pilot over 6 treated municipalities gives -6.8%, but this is explicitly non-causal. Its normal municipality-clustered interval excludes zero, whereas the reference based on only six treated-stack estimates has p=0.099 and an interval from -14.8% to 1.9%. The exact five-component sign sensitivity gives p=0.188. Removing controls with targeted caveats reduces the estimate to -2.0% with an interval spanning zero. Small effective sample size, selected comparisons, residual spillovers and uncertain historical access therefore prevent a causal Magic Pass interpretation.

**Internal evidence:** `reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md`, `reports/71_ESTIMATION_PILOTE_NON_CAUSALE_FR.md`, `reports/72_INFERENCE_PETIT_NOMBRE_COMMUNES_FR.md`

## 8. Is heterogeneous treatment-effect modelling statistically feasible?

**Answer:** No.

The effective treatment sample is at most 14 reviewed destinations, only 7 with the original joint 24/24 coverage gate and only 6 treated municipality stacks in the redesigned pilot. Their descriptive estimates range from -16.4% to 3.5%, but none is causally approved. Repeated municipality-month rows do not create independent treatments, so stable heterogeneity or causal-ML estimation is unsupported.

**Internal evidence:** `reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md`, `reports/accessibility_pilot_treated_decomposition.csv`, `reports/72_INFERENCE_PETIT_NOMBRE_COMMUNES_FR.md`

## 9. Is Causal Forest feasible?

**Answer:** No.

Causal Forest is rejected because the causal target is unidentified, no control is approved, overlap cannot be defended and the number of independent treated units is too small. A software implementation would not repair those design failures.

**Internal evidence:** `reports/model_experiment_log.csv`, `reports/47_METHODOLOGICAL_LITERATURE.md`

## 10. Is standard ML useful?

**Answer:** Only for qualified descriptive structure, not outcome prediction or uplift.

Supervised ML has no defensible cluster-level causal or recommendation target and would face leakage from current/post-treatment features. Unsupervised structural segmentation and nearest-analogue distances are useful as transparent exploratory tools with grouped entities, explicit support checks and aggregation sensitivity.

**Internal evidence:** `reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md`, `reports/38_PATH_C_FEATURE_READINESS_AUDIT.md`

## 11. Is a neural network justified?

**Answer:** No.

The sample of independent destinations is far too small, the target is not causally approved, and a neural network would reduce interpretability while increasing leakage and overfitting risk.

**Internal evidence:** `reports/model_experiment_log.csv`, `reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md`

## 12. Is clustering/similarity more appropriate?

**Answer:** Yes, as an exploratory fallback with explicit sensitivity checks.

Among 156 structurally complete clusters, k=2 has silhouette 0.514 and median subsample ARI 0.987. However, only 11 of 104 candidates retain every recorded segment, analogue and support criterion across min/median/max aggregation. Clustering is therefore more appropriate only as a qualified descriptive device.

**Internal evidence:** `reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md`, `reports/19_PATH_C_AGGREGATION_SENSITIVITY.md`

## 13. What is the most defensible final Business Analytics methodology?

**Answer:** A separated seven-dimension exploratory evidence dashboard.

Checkpoint 6 selects a 7-dimension dashboard covering 104 apparent candidates and assigning all 19 evidence groups exactly once. Structural similarity, analogue opportunity, snow vulnerability, tourism context, accessibility, competition/network context and evidence gaps remain separate. No weighted composite, ranking or treatment-effect prediction is authorised.

**Internal evidence:** `reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md`, `reports/42_THESIS_RESULTS_SYNTHESIS.md`

## 14. Which variables appear most informative?

**Answer:** Current structural fields are the only approved similarity inputs; other layers are informative context.

Published top altitude, ski-area kilometres and lift count provide the clearest reproducible cross-sectional structural separation and are the only fields approved for exploratory similarity. Snow vulnerability, point-container tourism intensity, population/accessibility, competing-pass links and network density help diagnose context and uncertainty, but none is approved as a pre-treatment predictor, causal covariate, recommendation input or composite-score component.

**Internal evidence:** `reports/path_c_feature_readiness_audit.csv`, `reports/38_PATH_C_FEATURE_READINESS_AUDIT.md`

## 15. Which variables are missing?

**Answer:** Validated candidate catchments, historical access/infrastructure and treatment-intensity data remain missing.

Material gaps include externally validated destination catchments and exposure weights, historical public-transport/service measures, dated lift capacity and infrastructure, systematic snowmaking, complete historical competing-pass coverage, area-specific summer rights, hotel-location/final-mile access and a broader uncontaminated donor universe. Four readiness groups have no candidate feature and two have only partial candidate coverage.

**Internal evidence:** `reports/38_PATH_C_FEATURE_READINESS_AUDIT.md`, `PROJECT_STATE.md`

## 16. What are the main sources of uncertainty?

**Answer:** Entity scope, treatment, counterfactuals, timing and spatial proxy mismatch.

The principal uncertainties are multi-listing cluster semantics, resort-to-municipality exposure, season-level and heterogeneous treatment, donor shocks and spillovers, current/post-treatment feature timing, station-to-resort snow mismatch, timetable currentness and incomplete historical pass-market coverage. The snow-station sensitivity classifies 4 of 15 component comparisons as low, and the four-case appendix demonstrates how aggregation and empirical support can change at row level.

**Internal evidence:** `reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md`, `reports/48_CANDIDATE_UNCERTAINTY_EXAMPLES.md`

## 17. Which additional data would most improve the model?

**Answer:** Destination exposure definitions and a much larger credible treatment/control design.

The highest-value additions are externally validated destination boundaries and municipality weights, treatment intensity and exact timing, a larger set of credibly untreated comparison destinations with shock/interference audits, and pre-treatment histories for hotel capacity, infrastructure, access and snowmaking. Stakeholder-defined decision weights are also required before any composite business score.

**Internal evidence:** `reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md`, `reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md`

## 18. Can the final system reasonably be described as predictive, causal, exploratory or decision-support?

**Answer:** Exploratory and decision-support oriented; not predictive or causal.

The final system is an exploratory decision-support evidence architecture. It has 1 feature group approved for similarity, 0 approved pre-treatment predictors, 0 causal covariates, 0 recommendations and 0 causal interpretations. It must not be described as an uplift model, profitability estimate or admission ranking.

**Internal evidence:** `reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md`, `reports/path_c_feature_readiness_audit.csv`

## Reproducibility and claim boundary

All numerical answers are regenerated from repository summaries and linked to internal evidence artifacts. External-source claims are mapped separately in `reports/46_THESIS_CITATION_MAP.md`; methodological references are in `reports/47_METHODOLOGICAL_LITERATURE.md`. The four candidate rows in `reports/48_CANDIDATE_UNCERTAINTY_EXAMPLES.md` illustrate uncertainty categories only. No answer in this report authorises a candidate recommendation or a treatment-effect interpretation.
