# Thesis chapter draft — Discussion and limitations

> Draft generated from the validated Path C v0.31 outputs. It interprets the research design and findings without converting descriptive evidence into causal or managerial certainty.

## 1. Main interpretation

The project demonstrates that the available Swiss ski-destination data are rich enough to support a reproducible, multidimensional descriptive decision system, but not a credible estimate of the causal effect of Magic Pass participation. This distinction is the central finding. The absence of a causal estimate is not a computational failure: it follows from explicit evidence gates that exposed unresolved treatment intensity, destination scope, donor contamination, local shocks, spillovers and insufficient effective sample size.

Path C preserves analytical usefulness after that rejection. Structural segmentation, analogue distance, snow vulnerability, tourism context, accessibility and competition can inform structured investigation when kept separate. The architecture is particularly useful for identifying where evidence is strong, where a candidate is an extrapolation and which additional information would be required before a strategic decision. It is not suitable for estimating expected overnight-stay gains or ranking destinations for admission.

## 2. Implications for causal inference and machine learning

The donor audit illustrates why a superficially adequate panel can still be unsuitable for causal inference. Seven treatments had sufficient continuity and 24/24 outcome coverage, and 315 pairs passed the descriptive pre-trend data screen. Yet 28 of the 35 shortlisted pairs were within 50 km of another resolved Magic Pass point, and all seven remote pairs had contemporaneous donor-specific shocks. Promoting one of these pairs would have replaced an explicit identification failure with an untestable assumption.

The same logic applies to causal machine learning. Causal forests are developed under explicit causal assumptions including unconfoundedness (Wager and Athey, 2018), while meta-learners organise flexible supervised models around a conditional treatment-effect target rather than identifying that target automatically (Künzel et al., 2019). Neither can compensate for an invalid treatment/control design, and 14 reviewed destinations are not an adequate effective sample for stable heterogeneous-effect estimation. Rejecting complex models therefore improves scientific credibility. The contribution shifts from algorithmic novelty to disciplined integration, scope control and uncertainty communication.

## 3. Managerial usefulness of Path C

The dashboard can support a staged managerial conversation. Structural comparability identifies whether a candidate resembles existing Magic Pass clusters. The treated-reference support flag shows whether analogue interpretation is interpolation or extrapolation. Snow, access, tourism and competition layers identify distinct strategic considerations. The evidence-gap dimension prevents an attractive structural profile from being mistaken for a complete business case.

However, candidate rows must remain examples for due diligence rather than recommendations. Only 11 of 104 candidates were stable across every aggregation check, 25 were strong extrapolations and only 39 had complete hotel context under any tested scope rule. A single weighted score would conceal these non-equivalent uncertainties and imply value judgements not established by the data.

## 4. Measurement and scope limitations

### 4.1 Resort and destination entities

The supplied directory is a listing system rather than a certified inventory of independent commercial ski domains. The preserved lift clusters reduce duplication but do not solve ownership, joint-ticketing or destination-boundary questions. Fifty-three linked clusters contain multiple listings, and within-cluster structural aggregation changes many analogue results. Destination-level conclusions should therefore be phrased in terms of the reviewed units or preserved clusters used by the analysis.

### 4.2 Hotel-outcome geography

Municipality hotel data do not automatically represent a ski destination's visitor catchment. Seven reviewed outcome scopes are core-municipality proxies, and the radius experiment shows that improving recall rapidly adds unrelated municipalities. Five kilometres recovered the one omitted reviewed link but added 25 others. Candidate tourism dependence must remain qualified point-container or radius-sensitivity context until external destination scopes are available.

### 4.3 Treatment definition and intensity

Official publications support membership timing and continuity for the reviewed units, but treatment is not homogeneous. Winter-only and winter-plus-summer access differ, as do prices, supplements, product rules, local marketing and capacity responses. Entry is known mainly by season rather than exact activation date. The design therefore cannot assume a single binary treatment with constant intensity.

### 4.4 Donors, interference and common shocks

Ski destinations operate in connected regional markets. Nearby resorts may experience diversion, complementarity or shared marketing effects, violating no-interference assumptions. Remote destinations are not automatically credible controls: every remote shortlisted donor had a documented concurrent shock. The COVID sensitivity interval, weather, capacity changes, infrastructure investment and flexible pricing further complicate parallel-trend claims.

### 4.5 Climate and snow proxies

SLF stations are external point measurements and can differ materially from resort elevations. The resort-centred SPASS comparison was low for 8 of 15 components, even though station-location agreement was much stronger. SPASS and SLF are also not independent because the gridded product is modelled and quantile-mapped to an SLF snow target. SwissMetNet and official weather grids describe regional conditions rather than piste microclimates, snowmaking or operational decisions. Climate fields are appropriate for qualified vulnerability context, not causal adjustment without further design work.

### 4.6 Accessibility

The GTFS analysis improves on straight-line distance by using departure-time-specific scheduled journeys, but it represents one weekday and one Saturday in winter 2026. It does not measure historical service at treatment entry, real-time reliability, fares, crowding, car access, hotel location or final walking time. Six destination nodes are village/local-centre proxies. The median distance/time rank correlation of 0.743 confirms that distance is informative, while the 225 materially worse-transit pairs show why it is insufficient.

### 4.7 Competing passes

The historical register records positive presence, not a complete market census. Evidence scope varies by product and season, benefit tiers are not equivalent, and detailed small-lift boundaries remain incomplete. A candidate without a documented link cannot be called historically unserved by multi-area passes. Competition variables therefore remain contextual and cannot establish treatment contrast or market whitespace.

### 4.8 Temporal leakage and transportability

Most candidate-side structural, accessibility, tourism and network layers are current or undated snapshots. They may encode post-treatment investment or market evolution and are not approved as pre-treatment predictors. The eight reviewed treated analogue references are too few to establish that structural proximity transports hotel-demand responses. The analogue signal must remain an unadjusted descriptive comparison.

## 5. Strengths

The study nevertheless has several strengths. It preserves raw sources and stable identifiers, separates resort assignment from municipality exposure mapping, uses explicit positive-evidence rules, records source checksums and provenance, and encodes analytical permissions as executable flags. Sensitivity tests expose dependence on station choice, grid location, within-cluster aggregation, geographic distance rule and candidate municipality scope. Negative results and failed collection attempts remain documented rather than silently removed.

The seven-dimension architecture is also a substantive Business Analytics contribution. It prevents structural attractiveness, vulnerability, accessibility and data quality from collapsing into one opaque score. The resulting system is auditable and communicates why a candidate cannot yet receive a defensible recommendation.

## 6. Prioritised future research

Future work should follow the identification bottlenecks rather than add marginal variables indiscriminately:

1. define destination exposure using externally validated tourism scopes and treatment intensity;
2. redesign the donor strategy, potentially expanding beyond the supplied ski-resort municipality universe while retaining interference and shock audits;
3. obtain historical transport and infrastructure measures only if they are needed as pre-treatment variables;
4. collect operational snowmaking, investment and lift-capacity histories if climate adaptation is part of the causal question;
5. expand the number of credibly treated destination units before reconsidering heterogeneous-effect models;
6. validate decision weights with Magic Pass stakeholders before any composite business score is introduced.

Detailed historical SnowPass schedules, additional regional-pass rosters and walking-access refinements are secondary unless a specific claim depends on them. They should not displace the higher-priority treatment, scope and donor problems.

## 7. Conclusion

Under the available design, the project should be described as **exploratory and decision-support oriented**, not causal or predictive. The evidence supports structured comparison of 104 apparent candidates and transparent reporting of opportunity, vulnerability and uncertainty. It does not support expected-uplift estimates, a causal interpretation, or a ranked recommendation list. That boundary is a core result of the thesis rather than a caveat appended after modelling.
