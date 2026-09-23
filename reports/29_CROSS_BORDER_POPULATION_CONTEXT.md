# Qualified cross-border population context

## Scope

The official Eurostat GISCO Census Grid 2021 version 3 supplies total population on a harmonised **1 km grid** in **EPSG:3035**. The checksum-verified raw CSV member contains **4,595,932 rows**. Of these, **4,595,919** have a grid location; **13** country-level `CC_unallocated` records cannot be placed spatially and are excluded rather than assigned arbitrarily. Their observed population totals **434,787** people across the full source universe.

For every linked Path C lift cluster, a cell contributes when its centroid falls inside the predeclared 30, 60, 90 or 120 km straight-line radius. A 1 km square's centroid can differ from a point elsewhere in the cell by at most **0.707 km**. Cells are partitioned into Switzerland-only, foreign-only, and mixed Swiss/foreign border cells using the official reporting-country list. Mixed cells remain separate because the CSV does not allocate their population by country.

## Coverage

| Radius | Clusters with foreign-only population | Candidates with foreign-only population | Clusters with mixed-cell population | Median foreign-only share | Clusters with unavailable-total cells |
|---:|---:|---:|---:|---:|---:|
| 30 | 99 | 73 | 89 | 1.6% | 0 |
| 60 | 154 | 101 | 143 | 20.6% | 0 |
| 90 | 162 | 104 | 162 | 29.0% | 0 |
| 120 | 162 | 104 | 162 | 36.7% | 0 |

- linked clusters with context: **162**
- apparent Path C candidates with context: **104**
- regional source cells retained: **181,598**
- regional cells whose total population is unavailable: **0**
- approved generic accessibility or causal population features: **0**

## Interpretation limit

This module closes the known *geographic truncation* of the Swiss-only population-radius diagnostic, but it does not create a visitor catchment. Census population is not skier demand; straight-line distance ignores mountains, roads, borders and travel behaviour. The 2021 grid is not merged numerically with STATPOP 2025 municipality totals because the reference year and allocation method differ. Confidential or otherwise unavailable totals (`-8888` and `-9999`) remain missing, while national unallocated records cannot be assigned to a radius. Population in mixed Swiss/foreign cells is reported separately rather than guessed. `cross_border_population_feature_approved` therefore remains false, `accessibility_score` remains blank, and no causal or composite ranking is produced.

## Outputs

- `data_processed/eurostat_population_grid_2021_swiss_region.csv`
- `data_processed/path_c_cluster_cross_border_population_context.csv`
- `reports/cross_border_population_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified context appended)
