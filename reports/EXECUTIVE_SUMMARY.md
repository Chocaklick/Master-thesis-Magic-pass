# Executive summary

## Research decision

This thesis evaluates whether the available Swiss ski-resort, hotel-demand, Magic Pass, snow/climate and accessibility evidence can support causal effect estimation and strategic decision support. The central conclusion is deliberately narrower than the initial ambition: the evidence does **not** support a credible causal estimate of Magic Pass membership, heterogeneous treatment-effect modelling or a ranked admission recommendation. It does support a reproducible exploratory framework that makes structural comparability, contextual evidence and uncertainty visible without combining them into a misleading score.

## Evidence base

The supplied universe contains **271 directory listings**, **242 preserved lift clusters** and **162 clusters linked to at least one listing**. These are not certified independent commercial resorts. The hotel panel contains 31,248 municipality-month rows for 186 municipalities from January 2013 through March 2026. Fourteen Magic Pass destination units were manually reviewed, 11 have an explicit hotel-outcome scope and seven have the joint 24-month pre/post coverage required for the adjacent-window diagnostic.

## Why causal and predictive modelling were rejected

The original donor process screened 315 descriptive treatment-donor pairs and shortlisted 35, but every geographically remote case had a documented contemporaneous local shock. The later municipality-accessibility redesign retained 11 primary pre-period-compatible pairs across 6 treated municipalities. Its explicitly non-causal pilot averages -6.8%, yet the treated-stack t reference gives p=0.099, the five-component sign sensitivity gives p=0.188, and the conservative control exclusion is -2.0% with an interval spanning zero. Zero causal treatments, controls or pairs are approved. The sample and identification therefore remain insufficient for causal forests, meta-learners, uplift models or neural networks.

## Final analytical architecture

Checkpoint 6 selects a **seven-dimension separated evidence dashboard** for 104 apparent candidates. The 19 evidence groups cover structural similarity, analogue opportunity, snow vulnerability, tourism context, accessibility, competition/network context and evidence gaps. Thirteen groups have complete candidate coverage, two are partial and four lack a candidate feature. Coverage is not permission: only structural similarity is approved for exploratory matching, while zero groups are approved as pre-treatment predictors, causal covariates, recommendation inputs or composite-score components.

The structural solution uses top altitude, ski-area kilometres and lift count. Among 156 complete clusters, k=2 achieves silhouette 0.514 and median subsample ARI 0.987. Yet only 11 of 104 candidates preserve every recorded segment, analogue and support criterion across minimum, median and maximum within-cluster aggregation. Twenty-five candidates are strong extrapolations from the eight reviewed treated references. These diagnostics prevent structural resemblance from being mistaken for predicted benefit.

## Business interpretation

The framework is useful for organising due diligence, not deciding admission. It can show whether a candidate lies inside the observed structural support, where snow or access context may be relevant and which evidence is incomplete. It cannot estimate expected overnight-stay gains, financial profitability or the causal effect of joining Magic Pass. The four fixed examples in the uncertainty appendix demonstrate how the same evidence system communicates stability, aggregation sensitivity and extrapolation without ranking candidates.

## Priority next evidence

The most valuable future inputs are externally validated destination catchments and municipality exposure weights, exact treatment timing and intensity, a larger uncontaminated donor/treatment universe, and pre-treatment histories for hotel capacity, access, lift/infrastructure investment and snowmaking. Historical timetable and pass details are secondary unless required for a specific claim. Stakeholder-defined decision weights would be required before any composite business score could be considered.

## Final classification

The completed system is **exploratory and decision-support oriented**. It is not causal, not an uplift predictor, not a profitability model and not a candidate ranking. This boundary is the principal methodological result of the thesis.
