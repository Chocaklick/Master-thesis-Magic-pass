# Checkpoint 6 — Business decision framework

## Decision

Checkpoint 6 selects a **separated exploratory evidence dashboard** for the **104 Path C candidates**. It does not select an uplift model, causal ranking, recommendation engine or composite score. The architecture keeps structural comparability, descriptive analogue opportunity, snow vulnerability, tourism dependence, accessibility, competition/network context and evidence gaps separate across **7 dimensions**.

The dashboard is deliberately incomplete as a business recommendation. Only **39** candidates have complete point-container hotel context. The 0/5/10 km scope sensitivity reaches an observed HESTA ratio for **99** candidates, but still leaves only **39** with complete municipal hotel coverage under any rule; more importantly, the radius validation rejects every rule as a comparable destination catchment. Historical public transport, competition and dated infrastructure remain missing. A full Opportunity × Strategic Need matrix is therefore ready for **0 candidates**.

## Dimension register

| Dimension | Feature groups | Coverage pattern | Status | Permitted use |
|---|---:|---|---|---|
| Structural comparability and support | 3 | 3 complete / 0 partial / 0 absent | qualified_available | exploratory_segmentation_analogue_distance_and_measurement_sensitivity |
| Descriptive analogue opportunity | 1 | 1 complete / 0 partial / 0 absent | qualified_descriptive_signal_not_effect | separate_descriptive_dimension_only |
| Snow vulnerability | 1 | 1 complete / 0 partial / 0 absent | qualified_proxy | separate_descriptive_vulnerability_dimension_only |
| Tourism dependence and destination scope | 3 | 1 complete / 1 partial / 1 absent | incomplete_noncomparable_candidate_scope | qualified_context_and_scope_audit_only |
| Population and accessibility context | 7 | 5 complete / 0 partial / 2 absent | qualified_current_context_historical_gap | separate_descriptive_context_only |
| Competition and network context | 3 | 2 complete / 0 partial / 1 absent | qualified_current_context_historical_gap | separate_descriptive_context_only |
| Dated infrastructure and recommendation gate | 1 | 0 complete / 0 partial / 1 absent | blocked_missing_historical_evidence | no_recommendation_or_composite_score |

## Candidate uncertainty

Among the 104 candidates, **74** have good structural support against the reviewed treated references, **5** are moderate extrapolations and **25** are strong extrapolations. Only **11** remain stable on every recorded min/median/max aggregation criterion. These diagnostics qualify interpretation; they do not produce recommendation confidence or treatment-effect uncertainty.

## Protected outputs

Predicted-uplift values: **0**. Recommendations issued: **0**. Composite scores: **0**. Causal approvals: **0**. Candidate rows are sorted by stable `cluster_id`, never by opportunity signal.

## Outputs

- `config/path_c_decision_framework.json`
- `data_processed/path_c_candidate_evidence_dashboard.csv`
- `reports/path_c_decision_framework_dimensions.csv`
- `reports/path_c_decision_framework_summary.json`
- `reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md`
- `reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md` (scope diagnostic feeding the tourism-dimension gate)
