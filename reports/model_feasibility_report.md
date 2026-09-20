# Model feasibility report

Generated reproducibly by `src/data_processing/build_feasibility_report.py`.

## Executive verdict

The project currently follows **Path C (weak treatment sample / exploratory decision support)**. This is a checkpoint decision, not a permanent rejection of causal work. A move to Path B would require a reviewed destination-level resort definition, complete season-by-season membership and exit histories, an explicit resort-to-tourism-municipality exposure crosswalk, and an uncontaminated control audit.

No causal model, treatment-effect learner, opportunity score, or neural network should be fitted at this checkpoint.

## Effective sample

- The supplied Bergfex layer contains **271 resort listings**. The preserved lift layer has **242 clusters**, of which **162** are linked to at least one listing. Neither number is yet an approved count of independent ski destinations.
- The official current-map snapshot contains **95 embedded destinations**; **68** have a candidate link to a supplied resort listing. The page headline and press archive refer to more than 100 destinations, so the embedded-list discrepancy must be reviewed rather than silently reconciled.
- Official evidence records **88 base-pass entry events**. **62** have a candidate resort-listing link, but only **18** also point to an OFS hotel municipality.
- Those 18 events reduce to **14 municipalities**. This municipality count, not the 28,455 observed monthly rows, is the more relevant upper bound for treatment heterogeneity.
- **Zero** treatment units are approved for causal estimation because point containment is not tourism exposure and membership continuity is incomplete.

## Outcome coverage

- The cleaned OFS-derived panel has **186 municipalities**.
- Observed hotel-night values run from **2013-01-01** through **2026-03-01**; later 2026 grid rows are missing and are not counted as observed.
- Resort points reach **74** hotel municipalities.
- A naive subtraction leaves at most **60** apparent control municipalities, but **zero controls are approved** because historical non-membership and spillover contamination have not been verified.

## Provisional pre/post windows

For coverage diagnostics only, the script anchors the founding 2017/18 season at 2017-11-01 and later annual seasons at 1 May of their first year. These are not accepted treatment dates. A documented exit bounds Crans-Montana's active post period; continuity for all other events remains unverified.

- Season-only candidate events with at least 24 observed pre months: **16**
- With at least 36 observed pre months: **16**
- With at least 24 potentially post-entry months: **15**
- With at least 36 potentially post-entry months: **12**
- Distinct provisional anchors: **7**
- Treated units with an exact entry date: **0**

The event-level audit is in `reports/provisional_treatment_window_coverage.csv`.

## Model-family decisions

| Model family | Current decision | Evidence-based reason |
|---|---|---|
| Municipality fixed-effects panel | Not ready | Outcome panel is large enough, but exposure and treatment coding are not validated. |
| Staggered Difference-in-Differences | Not credible yet | Only season-level entry timing is available; exits, scope, spillovers, and controls remain incomplete. |
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
7. Hotel capacity, snow, accessibility, investment, and local economic controls have not yet been integrated.

## Next evidence gate

Prioritise manual review of the 18 candidate entry/outcome links, starting with shared municipalities (Anniviers, Evolène, and Reichenbach im Kandertal), complete annual membership/exit status, and define explicit destination-to-municipality weights. Only then reassess fixed-effects/event-study feasibility and donor contamination. Complex heterogeneous-effect ML remains unjustified unless the effective treated-destination count increases substantially.
