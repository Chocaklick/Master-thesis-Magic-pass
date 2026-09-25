# Executive summary

## Research decision

This thesis evaluates whether the available Swiss ski-resort, hotel-demand, Magic Pass, snow/climate and accessibility evidence can support causal effect estimation and strategic decision support. The central conclusion is deliberately narrower than the initial ambition: the evidence does **not** support a credible causal estimate of Magic Pass membership, heterogeneous treatment-effect modelling or a ranked admission recommendation. It does support a reproducible exploratory framework that makes structural comparability, contextual evidence and uncertainty visible without combining them into a misleading score.

## Evidence base

The supplied universe contains **271 directory listings**, **242 preserved lift clusters** and **162 clusters linked to at least one listing**. These are not certified independent commercial resorts. The hotel panel contains 31,248 municipality-month rows for 186 municipalities from January 2013 through March 2026. Fourteen Magic Pass destination units were manually reviewed, 11 have an explicit hotel-outcome scope and seven have the joint 24-month pre/post coverage required for the adjacent-window diagnostic.

## Why causal and predictive modelling were rejected

The donor process screened 315 descriptive treatment-donor pairs and shortlisted 35. Twenty-eight shortlisted pairs were at or within 50 km of another resolved Magic Pass point; every one of the seven remote pairs had an independently documented contemporaneous local shock. Zero causal treatments and zero controls were approved. With at most 14 reviewed treated destinations, only seven passing the 24/24 coverage screen and no identified causal target, causal forests, meta-learners, standard uplift models and neural networks are not statistically defensible.

## Final analytical architecture

Checkpoint 6 selects a **seven-dimension separated evidence dashboard** for 104 apparent candidates. The 19 evidence groups cover structural similarity, analogue opportunity, snow vulnerability, tourism context, accessibility, competition/network context and evidence gaps. Thirteen groups have complete candidate coverage, two are partial and four lack a candidate feature. Coverage is not permission: only structural similarity is approved for exploratory matching, while zero groups are approved as pre-treatment predictors, causal covariates, recommendation inputs or composite-score components.

The structural solution uses top altitude, ski-area kilometres and lift count. Among 156 complete clusters, k=2 achieves silhouette 0.514 and median subsample ARI 0.987. Yet only 11 of 104 candidates preserve every recorded segment, analogue and support criterion across minimum, median and maximum within-cluster aggregation. Twenty-five candidates are strong extrapolations from the eight reviewed treated references. These diagnostics prevent structural resemblance from being mistaken for predicted benefit.

## Business interpretation

The framework is useful for organising due diligence, not deciding admission. It can show whether a candidate lies inside the observed structural support, where snow or access context may be relevant and which evidence is incomplete. It cannot estimate expected overnight-stay gains, financial profitability or the causal effect of joining Magic Pass. The four fixed examples in the uncertainty appendix demonstrate how the same evidence system communicates stability, aggregation sensitivity and extrapolation without ranking candidates.

## Priority next evidence

The most valuable future inputs are externally validated destination catchments and municipality exposure weights, exact treatment timing and intensity, a larger uncontaminated donor/treatment universe, and pre-treatment histories for hotel capacity, access, lift/infrastructure investment and snowmaking. Historical timetable and pass details are secondary unless required for a specific claim. Stakeholder-defined decision weights would be required before any composite business score could be considered.

## Final classification

The completed system is **exploratory and decision-support oriented**. It is not causal, not an uplift predictor, not a profitability model and not a candidate ranking. This boundary is the principal methodological result of the thesis.
