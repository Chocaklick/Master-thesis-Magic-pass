# Illustrative Path C candidate uncertainty cases

These four rows are selected by predeclared, deterministic uncertainty rules and then by ascending stable `cluster_id`. They are **not** the best, worst or most representative candidates. The ordering below is the rule order, not a ranking. No candidate is assigned an expected treatment effect, recommendation, confidence interval or composite score.

## Selection overview

| Rule order | Case | Stable cluster ID | Directory label | Median-rule treated support | Aggregation status |
|---:|---|---|---|---|---|
| 1 | `stable_complete_context` | `SKI_CLUSTER_010` | Wengen Jungfrau Ski Region Grindelwald - Wengen / Schilthorn Jungfrau Ski Region Mürren - Schilthorn | good_support | stable_across_min_median_max |
| 2 | `segment_assignment_sensitive` | `SKI_CLUSTER_017` | Disentis / Andermatt - Oberalp - Sedrun / Gemsstock Andermatt - Gemsstock / +1 listings | good_support | sensitive_to_within_cluster_aggregation |
| 3 | `support_category_sensitive` | `SKI_CLUSTER_007` | Arosa Lenzerheide / Pradaschier - Churwalden / Brambrüesch Chur - Brambrüesch | good_support | sensitive_to_within_cluster_aggregation |
| 4 | `strong_treated_reference_extrapolation` | `SKI_CLUSTER_001` | Châtel Portes du Soleil / Torgon Portes du Soleil / Avoriaz 1800 Portes du Soleil / +2 listings | strong_extrapolation | sensitive_to_within_cluster_aggregation |

The first rule illustrates stability with available point-container context. The next two isolate distinct aggregation problems: segment movement and support-category movement. The final rule illustrates extrapolation beyond the empirical treated-reference support. The exact selection fields are preserved in `reports/thesis_candidate_uncertainty_examples.csv`.

## 1. Stable structural comparison with point-container context: `SKI_CLUSTER_010`

**Directory label:** Wengen Jungfrau Ski Region Grindelwald - Wengen / Schilthorn Jungfrau Ski Region Mürren - Schilthorn

**Selection rule:** First cluster_id with stable min/median/max segment, analogue and support criteria; good treated-reference support; and complete point-container population/hotel context.

**Structural reading.** The median directory profile is 2750 m top altitude, 108.0 km of published ski area and 21.0 lifts. The median-rule segment is `SEGMENT_02` and the treated-reference support flag is `good_support`. The aggregation rules record segment set `SEGMENT_02` and an analogue-signal range of 12.9 percentage points.

**Analogue reading.** The closest current Magic cluster is `SKI_CLUSTER_020` (Anzère / Crans - Montana Crans - Montana), while the closest reviewed treated reference is `anniviers_magic_portfolio` (Anniviers Magic Pass portfolio). These are geometric neighbours in the three-field structural feature space, not counterfactual controls.

**Evidence limits.** Tourism context is `complete_point_container_population_and_hotel_context` and no tourism catchment is validated. NPVM assignment is `complete_with_nearest_same_municipality_zone_proxy`; current stop context is `complete_all_listing_points_inside_swiss_scope` and road-axis context is `complete_all_listing_points_inside_swiss_scope`. Current pass scope is `all_listing_points_linked_to_one_or_more_reviewed_rosters` and historical positive-presence scope is `partial_cluster_listing_links_documented`; historical market absence is not verified.

**Permitted conclusion.** This row illustrates how evidence strength and uncertainty can be narrated for one stable identifier. It is not an admission recommendation, a causal estimate, an expected-uplift value or a statement of relative merit.

## 2. Segment assignment changes under aggregation: `SKI_CLUSTER_017`

**Directory label:** Disentis / Andermatt - Oberalp - Sedrun / Gemsstock Andermatt - Gemsstock / +1 listings

**Selection rule:** First cluster_id with good treated-reference support whose recorded min/median/max solutions span more than one segment.

**Structural reading.** The median directory profile is 2725 m top altitude, 45.5 km of published ski area and 7.0 lifts. The median-rule segment is `SEGMENT_02` and the treated-reference support flag is `good_support`. The aggregation rules record segment set `SEGMENT_01|SEGMENT_02` and an analogue-signal range of 15.5 percentage points.

**Analogue reading.** The closest current Magic cluster is `SKI_CLUSTER_071` (Mont - Noble Nax), while the closest reviewed treated reference is `espace_dent_blanche` (Espace Dent Blanche). These are geometric neighbours in the three-field structural feature space, not counterfactual controls.

**Evidence limits.** Tourism context is `population_only_no_complete_hotel_context` and no tourism catchment is validated. NPVM assignment is `complete_with_nearest_same_municipality_zone_proxy`; current stop context is `complete_all_listing_points_inside_swiss_scope` and road-axis context is `complete_all_listing_points_inside_swiss_scope`. Current pass scope is `all_listing_points_linked_to_one_or_more_reviewed_rosters` and historical positive-presence scope is `all_cluster_listings_have_documented_link`; historical market absence is not verified.

**Permitted conclusion.** This row illustrates how evidence strength and uncertainty can be narrated for one stable identifier. It is not an admission recommendation, a causal estimate, an expected-uplift value or a statement of relative merit.

## 3. Treated-reference support changes under aggregation: `SKI_CLUSTER_007`

**Directory label:** Arosa Lenzerheide / Pradaschier - Churwalden / Brambrüesch Chur - Brambrüesch

**Selection rule:** First cluster_id with good median-rule support, stable segment assignment and a non-stable treated-reference support category across aggregation rules.

**Structural reading.** The median directory profile is 2235 m top altitude, 122.5 km of published ski area and 4.0 lifts. The median-rule segment is `SEGMENT_02` and the treated-reference support flag is `good_support`. The aggregation rules record segment set `SEGMENT_02` and an analogue-signal range of 0.0 percentage points.

**Analogue reading.** The closest current Magic cluster is `SKI_CLUSTER_106` (Evolène), while the closest reviewed treated reference is `espace_dent_blanche` (Espace Dent Blanche). These are geometric neighbours in the three-field structural feature space, not counterfactual controls.

**Evidence limits.** Tourism context is `population_only_no_complete_hotel_context` and no tourism catchment is validated. NPVM assignment is `complete_with_nearest_same_municipality_zone_proxy`; current stop context is `complete_all_listing_points_inside_swiss_scope` and road-axis context is `complete_all_listing_points_inside_swiss_scope`. Current pass scope is `partial_cluster_listing_links` and historical positive-presence scope is `partial_cluster_listing_links_documented`; historical market absence is not verified.

**Permitted conclusion.** This row illustrates how evidence strength and uncertainty can be narrated for one stable identifier. It is not an admission recommendation, a causal estimate, an expected-uplift value or a statement of relative merit.

## 4. Strong treated-reference extrapolation: `SKI_CLUSTER_001`

**Directory label:** Châtel Portes du Soleil / Torgon Portes du Soleil / Avoriaz 1800 Portes du Soleil / +2 listings

**Selection rule:** First cluster_id classified as a strong extrapolation from the eight reviewed treated reference units under the median rule.

**Structural reading.** The median directory profile is 2276 m top altitude, 79.0 km of published ski area and 34.0 lifts. The median-rule segment is `SEGMENT_02` and the treated-reference support flag is `strong_extrapolation`. The aggregation rules record segment set `SEGMENT_02` and an analogue-signal range of 9.4 percentage points.

**Analogue reading.** The closest current Magic cluster is `SKI_CLUSTER_016` (Gstaad / Rougemont Rougemont - La Videmanette), while the closest reviewed treated reference is `anniviers_magic_portfolio` (Anniviers Magic Pass portfolio). These are geometric neighbours in the three-field structural feature space, not counterfactual controls.

**Evidence limits.** Tourism context is `population_only_no_complete_hotel_context` and no tourism catchment is validated. NPVM assignment is `partial_foreign_or_unresolved_listing_points`; current stop context is `partial_listing_points_outside_swiss_scope` and road-axis context is `partial_listing_points_outside_swiss_scope`. Current pass scope is `all_listing_points_linked_to_one_or_more_reviewed_rosters` and historical positive-presence scope is `no_documented_link_in_reviewed_products`; historical market absence is not verified.

**Permitted conclusion.** This row illustrates how evidence strength and uncertainty can be narrated for one stable identifier. It is not an admission recommendation, a causal estimate, an expected-uplift value or a statement of relative merit.

## Use in the thesis

Use at most these examples as a short boxed illustration or appendix. Keep the stable IDs, selection rules and limitation paragraphs together. Do not reorder them by an opportunity signal, add a recommendation label, or interpret the closest analogue as a causal control. Any managerial assessment would still require validated destination scope, stakeholder-defined decision weights and decision-specific evidence that the present project does not contain.
