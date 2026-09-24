# Municipal tourism context

## Source and common rules

Official STATPOP 2025 permanent-resident population is joined by exact BFS municipality ID to the internally consistent HESTA 2025 extract. Annual hotel nights are summed only when all 12 monthly values are observed; monthly-mean hotel beds, rooms and establishments follow the same complete-year rule. No missing values are imputed.

The source is OFS table `px-x-0102010000_101`, filtered to permanent residents and total citizenship, sex and age. Its 31 December 2025 population and 2025 municipality reference are deliberately aligned to the observed Moutier (BE), BFS 700, HESTA history; the protected future Moutier (JU), BFS 6831, HESTA cells are not backfilled.

## Point-container layer

- STATPOP municipalities: **2,115**
- HESTA municipalities in the project universe: **186**; complete year: **185**
- linked Path C clusters with complete point-container population and hotel context: **52 / 162**
- apparent Path C candidates with complete context: **39 / 104**

`point_container_*` fields describe the unique municipalities containing the supplied listing points. They remain available for all linked clusters but do not define commercial destinations or accommodation markets.

## Reviewed destination outcome-scope layer

The 11 destination units already admitted to the hotel outcome panel are aggregated separately from their versioned outcome-municipality scope. This is not derived from listing-point containment. The layer contains **12 municipality links** and all **11 / 11** scopes have complete 2025 population and hotel context. Four are complete observed municipal scopes and seven remain explicitly labelled core-municipality proxies. Their median outcome-scope ratios are **20.86 hotel nights per resident** and **160.1 beds per 1,000 residents**.

These ratios are current 2025 descriptions, not pre-treatment features. A reviewed outcome scope is the geography used to construct an outcome, not proof of the full destination catchment. In particular, the seven core proxies deliberately remain weaker than the four complete observed municipal scopes.

## Interpretation limit

`overnights_per_resident` and `hotel_beds_per_1000_residents` describe the municipality or unique set of municipalities containing the supplied resort listing points. Point containment does **not** establish the destination's tourism catchment, visitor origin market or causal exposure. For this reason `tourism_dependence_feature_approved` remains false everywhere and the generic `tourism_dependence` decision field remains blank. These variables are qualified descriptive context, not inputs to a composite ranking.

The same non-approval applies to the reviewed outcome-scope layer: `tourism_catchment_validated`, `pre_treatment_feature_approved`, `tourism_dependence_feature_approved` and `causal_covariate_approved` are false in all 11 rows.

The separate 0/5/10 km municipality-polygon sensitivity in `reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md` tests whether transparent radius rules can extend this context. It does not change the catchment or feature approvals.

## Outputs

- `data_processed/municipality_tourism_context_2025.csv`
- `data_processed/path_c_cluster_tourism_context.csv`
- `data_processed/reviewed_destination_tourism_context_2025.csv`
- `data_processed/path_c_candidate_scope_radius_sensitivity.csv` (separate downstream scope sensitivity)
- `data_processed/magic_pass_decision_support.csv` (qualified context columns appended)
