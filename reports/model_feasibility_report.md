# Model feasibility report

Generated reproducibly by `src/data_processing/build_feasibility_report.py`.

## Executive verdict

The project currently follows **Path C (weak treatment sample / exploratory decision support)**. This is a checkpoint decision, not a permanent rejection of causal work. Destination scope and monthly hotel capacity have now been integrated, but a move to Path B still requires complete season-by-season membership and exit histories, the remaining confounders, and an uncontaminated control audit.

No causal model, treatment-effect learner, opportunity score, or neural network should be fitted at this checkpoint.

## Effective sample

- The supplied Bergfex layer contains **271 resort listings**. The preserved lift layer has **242 clusters**, of which **162** are linked to at least one listing. Neither number is yet an approved count of independent ski destinations.
- The official current-map snapshot contains **95 embedded destinations**; **68** have a candidate link to a supplied resort listing. The page headline and press archive refer to more than 100 destinations, so the embedded-list discrepancy must be reviewed rather than silently reconciled.
- Official evidence records **88 base-pass entry events**. **62** have a candidate resort-listing link, but only **18** also point to an OFS hotel municipality.
- Those 18 events reduce to **14 municipalities**. This municipality count, not the 28,455 observed monthly rows, is the more relevant upper bound for treatment heterogeneity.
- The 18 candidate links collapse to **14 reviewed destination units**. **11** enter a diagnostic outcome panel; **3** composite destinations are excluded because the supplied hotel panel does not cover their full reviewed scope.
- The reviewed panel has **1,848 destination-month rows**, of which **1,581** have a complete aggregated hotel-night outcome.
- **Zero** treatment units are approved for causal estimation. The reviewed geography is an outcome-scope decision, while membership continuity, confounding, spillovers, and control status remain unresolved.

## Outcome coverage

- The cleaned OFS-derived panel has **186 municipalities**.
- Observed hotel-night values run from **2013-01-01** through **2026-03-01**; later 2026 grid rows are missing and are not counted as observed.
- Resort points reach **74** hotel municipalities.
- Resolved historical/current Magic links reduce the 74-municipality resort-point universe to an upper bound of **57** apparent controls. This is not a clean donor pool: **26** official base-entry labels remain unresolved, and **zero controls are approved**.

## Provisional pre/post windows

For coverage diagnostics only, the script anchors the founding 2017/18 season at 2017-11-01 and later annual seasons at 1 May of their first year. These are not accepted treatment dates. A documented exit bounds Crans-Montana's active post period; continuity for all other events remains unverified.

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

This is a descriptive diagnostic only. The adjacent windows are not seasonally or trend adjusted, early post-periods can overlap COVID, and membership continuity remains assumed. Capacity integration therefore helps distinguish demand changes from contemporaneous supply changes but does not identify a Magic Pass effect.

## Membership-continuity audit

Entry events, full official rosters, named continuation statements, and the documented Crans-Montana exit were checked season by season. Missing annual evidence remains unverified rather than being filled as active or inactive.

- Reviewed units with every active season explicitly documented: **4**
- Such units that also enter the outcome panel: **3**
- Such panel units with both 24 observed pre months and 24 observed active-post months: **0**

The detailed audit is in `reports/membership_continuity_audit.csv`. Its zero in the final line is the decisive reason not to estimate a multi-unit causal effect yet.

## Donor/control contamination screen

The pipeline screened **814** treatment-municipality pairs. A deliberately provisional flag removes known resolved Magic exposure, the treated municipality scope, donors within 30 km, donors with fewer than 36 observed pre months, and donors with fewer than 24 post months. **438** pairs pass that mechanical screen, but **zero are approved causal controls** because unresolved membership, spillovers beyond an arbitrary distance threshold, and time-varying confounders remain.

See `reports/control_contamination_audit.csv` and `reports/control_candidates_by_treatment.csv`.

## Model-family decisions

| Model family | Current decision | Evidence-based reason |
|---|---|---|
| Municipality fixed-effects panel | Diagnostic-ready only | Eleven reviewed outcome units and monthly hotel capacity can be represented, but membership continuity, remaining confounding, spillovers, and controls remain unresolved. |
| Staggered Difference-in-Differences | Not credible yet | Destination scope is improved, but continuity assumptions and untreated-control status are not validated. |
| Matching | Descriptive only | May help select analogues after pre-treatment covariates and membership status are completed; it is not yet causal. |
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
7. Hotel capacity is integrated, but snow, weather, accessibility, investment, local economic conditions, and competing-network changes remain unmeasured.

## Next evidence gate

Fill the remaining unverified unit-seasons, resolve the unmatched official entry labels, add snow/weather and the remaining time-varying confounders, and replace the mechanical donor screen with a documented membership/spillover audit. Only then reassess fixed-effects/event-study or case-study synthetic-control feasibility. Complex heterogeneous-effect ML remains unjustified unless the effective treated-destination count increases substantially.
