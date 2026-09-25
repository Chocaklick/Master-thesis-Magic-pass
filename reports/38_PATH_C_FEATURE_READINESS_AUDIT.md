# Path C feature-readiness audit

## Decision

The registry covers **19 feature groups**. Only **1** group—the three current structural fields—is approved for the existing exploratory similarity calculation. **0** groups are approved as pre-treatment predictors, **0** as causal covariates, **0** for recommendations and **0** for a composite score.

Complete candidate coverage is available for **13** groups, partial coverage for **2**, and no candidate-level feature exists for **4**. Coverage is not approval: most complete layers are current or post-treatment descriptive context.

## Registry

| Feature group | Complete candidate rows | Temporal status | Approved usage |
|---|---:|---|---|
| Current structural similarity | 104/104 | undated_cross_sectional_snapshot_may_postdate_treatment | exploratory_structural_segmentation_and_analogue_distance |
| Analogue opportunity signal | 104/104 | explicit_post_treatment_reference_outcome | separate_descriptive_opportunity_dimension |
| Snow vulnerability proxy | 104/104 | 2013_2025_window_spans_pre_and_post_treatment | separate_descriptive_vulnerability_dimension |
| Point-container tourism intensity | 39/104 | 2025_current_or_post_treatment | qualified_descriptive_point_container_context |
| Swiss straight-line population context | 104/104 | 2025_population_current_or_post_treatment | qualified_descriptive_swiss_population_context |
| Cross-border population context | 104/104 | 2021_snapshot_postdates_early_entries | qualified_descriptive_cross_border_population_context |
| NPVM road and public-transport context | 104/104 | 2025_model_current_or_post_treatment | qualified_descriptive_transport_context |
| Public-transport stop proximity | 104/104 | 2026_current_or_post_treatment | qualified_descriptive_stop_proximity_context |
| National-road-axis proximity | 104/104 | 2026_current_or_post_treatment | qualified_descriptive_national_road_context |
| Current competing-pass links | 104/104 | current_snapshot_not_historical_pre_treatment | qualified_descriptive_current_competing_pass_context |
| Current cluster and reviewed pass-network density | 104/104 | current_or_undated_snapshot_not_historical | qualified_descriptive_current_network_context |
| Listing-point network-distance sensitivity | 104/104 | current_or_undated_listing_geometry | measurement_sensitivity_only |
| Structural aggregation sensitivity | 104/104 | inherits_undated_structural_snapshot | measurement_sensitivity_only |
| Reviewed treated outcome-scope tourism context | 0/104 | 2025_current_or_post_treatment | treated_destination_descriptive_context_only |
| Candidate destination-scope sensitivity and transfer gate | 104/104 | 2025_context_on_2026_boundaries_current_or_post_treatment | scope_measurement_sensitivity_only_zero_candidate_transfers |
| Current scheduled destination journeys | 0/104 | winter_2026_current_or_post_treatment | treated_destination_descriptive_context_only |
| Historical public-transport stability | 0/104 | required_historical_evidence_missing | not_available |
| Historical competing-pass context | 30/104 | dated_historical_product_roster_partial_market_coverage_not_uniformly_pre_anchor | qualified_partial_historical_competition_context_only |
| Dated resort infrastructure | 0/104 | required_historical_evidence_missing | not_available |

## Guardrail

The current structural fields remain undated and may themselves postdate treatment. Their sole approval is the already declared exploratory segmentation and analogue distance; it is not predictive or causal approval. Opportunity uses post-treatment reference outcomes and remains a separate descriptive dimension. Snow, tourism, population, transport, road, stop, competition and network layers remain outside the similarity calculation. Historical public transport and dated infrastructure remain absent. Historical competing-pass coverage is partial: one eight-season Top4 roster gives positive presence links for two candidates, while all non-links remain unverified market absence.

The registry is executable: every declared decision-support field must exist, candidate coverage is recomputed from the 104-candidate table, exactly one group may enter exploratory similarity, and all pre-treatment, causal, recommendation and composite approvals must remain false.

## Outputs

- `config/path_c_feature_readiness.json`
- `reports/path_c_feature_readiness_audit.csv`
- `reports/path_c_feature_readiness_summary.json`
- `reports/38_PATH_C_FEATURE_READINESS_AUDIT.md`
