# Candidate destination-scope radius sensitivity

## Purpose

This audit tests three transparent geometric rules—municipality polygons within 0, 5 or 10 km of any supplied cluster component point—without calling any of them a destination catchment. It uses official swissBOUNDARIES3D 2026 polygons, STATPOP 2025 population and complete-year HESTA 2025 observations. Every scope is current and straight-line; none is a visitor-origin market, travel-time basin or pre-treatment feature.

## Candidate coverage

- Path C candidates: **104**; rule rows: **312**
- candidates with a Swiss municipality at 0 km: **104**
- candidates with at least one observed HESTA ratio under any rule: **99**
- candidates with complete HESTA coverage for every municipality under at least one rule: **39**
- validated tourism catchments: **0**
- approved candidate scope transfers: **0**

An observed HESTA ratio uses only municipalities with a complete published hotel year. The accompanying population-coverage share makes the partial denominator explicit. A complete-scope ratio is emitted only when every municipality selected by the rule has complete HESTA data.

## Validation against independently reviewed complete outcome scopes

| Radius | Exact complete scopes | Reviewed links recovered | Extra municipality links | Mean precision | Mean recall |
|---:|---:|---:|---:|---:|---:|
| 0 km | 3 / 4 | 4 / 5 | 0 | 1.000 | 0.875 |
| 5 km | 0 / 4 | 5 / 5 | 25 | 0.178 | 1.000 |
| 10 km | 0 / 4 | 5 / 5 | 60 | 0.095 | 1.000 |

The zero-kilometre rule is component-point containment. Larger radii may recover a municipality omitted by point containment, but they also add municipalities not present in the reviewed outcome scope. This precision–recall trade-off is evidence that a universal radius is a sensitivity device, not validation of a commercial or accommodation catchment. The seven core-municipality proxies are retained in the validation file as a separate definition-linked stratum and are not used to claim independent validation.

## Interpretation limit

The outputs can diagnose how strongly current tourism context changes under simple municipal scope rules. They cannot identify where guests stay, prove a candidate's destination boundary, establish historical tourism dependence or support a recommendation. `tourism_catchment_validated`, `candidate_scope_transfer_approved`, `pre_treatment_feature_approved` and `causal_covariate_approved` therefore remain false throughout.

## Outputs

- `config/candidate_scope_radius_sensitivity.json`
- `data_processed/path_c_candidate_scope_radius_sensitivity.csv`
- `data_processed/path_c_cluster_scope_sensitivity_summary.csv`
- `reports/candidate_scope_radius_validation.csv`
- `reports/candidate_scope_radius_sensitivity_summary.json`
- `reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md`
