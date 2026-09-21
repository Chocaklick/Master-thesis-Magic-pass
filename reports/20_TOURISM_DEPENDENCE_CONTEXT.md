# Point-container tourism context

## Scope

Official STATPOP 2025 permanent-resident population is joined by exact BFS municipality ID to the internally consistent HESTA 2025 extract. Annual hotel nights are summed only when all 12 monthly values are observed; monthly-mean hotel beds, rooms and establishments follow the same complete-year rule. No missing values are imputed.

The source is OFS table `px-x-0102010000_101`, filtered to permanent residents and total citizenship, sex and age. Its 31 December 2025 population and 2025 municipality reference are deliberately aligned to the observed Moutier (BE), BFS 700, HESTA history; the protected future Moutier (JU), BFS 6831, HESTA cells are not backfilled.

## Coverage

- STATPOP municipalities: **2,115**
- HESTA municipalities in the project universe: **186**; complete year: **185**
- linked Path C clusters with complete point-container population and hotel context: **52 / 162**
- apparent Path C candidates with complete context: **39 / 104**

## Interpretation limit

`overnights_per_resident` and `hotel_beds_per_1000_residents` describe the municipality or unique set of municipalities containing the supplied resort listing points. Point containment does **not** establish the destination's tourism catchment, visitor origin market or causal exposure. For this reason `tourism_dependence_feature_approved` remains false everywhere and the generic `tourism_dependence` decision field remains blank. These variables are qualified descriptive context, not inputs to a composite ranking.

## Outputs

- `data_processed/municipality_tourism_context_2025.csv`
- `data_processed/path_c_cluster_tourism_context.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified context columns appended)
