# Checkpoints 4–5 and Path C decision

## Decision

Checkpoint 4 fails under the present design: there are **0 approved causal treatment units** and **0 approved controls**. The 35-pair donor shortlist is exhausted after 28 proximity deprioritisations and seven official-source shock exclusions. No DiD, event-study, matching or synthetic-control estimate is authorised.

Checkpoint 5 also fails for heterogeneous-effect ML: the project has 14 reviewed destination units, 11 in the outcome panel, seven with 24 observed pre and active-post months, and still zero causally approved units. Monthly repetition does not increase the number of independent treated destinations. Causal forest, X-Learner, DR-Learner and a neural network remain rejected; supervised gradient boosting/random forest have no defensible cluster-level target.

The selected architecture is therefore **Path C: exploratory structural segmentation and descriptive analogue decision support**. This is a positive architecture choice, not a causal fallback disguised as prediction.

## Leakage and unit controls

- Analysis entity: the **162 existing lift clusters linked to at least one supplied listing**, rather than 271 repeated directory rows. A cluster is still not a certified independent destination.
- The Bergfex infrastructure snapshot is undated, so it is labelled current/undated and **not pre-treatment**.
- Similarity uses only top altitude, log ski-area kilometres and log lift count.
- Membership, hotel outcomes, post-entry changes and snow vulnerability do not enter the structural clustering.
- Hotel outcomes/capacity are excluded because a resort point's municipality is not an approved tourism catchment.
- Snow vulnerability is retained on a separate strategic-need axis. Qualified point-container tourism, Swiss municipality-point and Eurostat cross-border grid population, NPVM zonal travel-time, official stop-proximity and current FEDRO/ASTRA national-road-axis context are appended downstream. A separate winter-2026 GTFS module measures scheduled municipality-to-destination journeys, and all 15 current component arrival nodes pass a versioned name/mode/municipality/distance review for descriptive routing. A same-pair diagnostic confirms that geographic distance is informative but not interchangeable with scheduled transit time. Six arrivals remain explicit village/local-centre proxies; door-to-lift walking and historical continuity are unverified. The road layer does not classify motorways or measure route access. None is an approved catchment or causal destination-accessibility feature.

## Prohibited interpretations

The analogue signal is not predicted uplift, a counterfactual, a confidence interval or evidence that a resort should join Magic Pass. No composite opportunity/need score is produced. A later causal redesign would require new donor and exposure evidence rather than a more complex algorithm.
