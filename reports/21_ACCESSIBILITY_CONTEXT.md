# Qualified straight-line population accessibility context

## Scope

Official STATPOP 2025 permanent-resident population is aligned to the official swissBOUNDARIES3D municipality state of 1 January 2026. The seven 2025 identifiers affected by the five official 2026 OFS mutations are explicitly mapped and aggregated. This preserves all **9,127,125 residents** while reconciling **2,115** STATPOP rows to **2,110** current polygons.

Each municipality is represented by a point guaranteed to lie within its polygon. Distances from each cluster's median supplied coordinate are Euclidean distances in EPSG:2056. Three transparent population thresholds are reported instead of selecting one untested definition: at least 20,000: **55**, at least 50,000: **10**, at least 100,000: **6**. Population totals are also reported inside 30 km, 60 km, 90 km, 120 km straight-line radii. The thresholds and radii are versioned in `config/path_c_analysis.json`.

## Coverage

- linked Path C clusters with complete geographic context: **162**
- apparent Path C candidates with complete geographic context: **104**
- municipality mutation records verified against checksum-protected OFS pages: **5**
- clusters outside the official Swiss country polygon: **2**
- clusters whose Swiss-only radius intersects the national boundary (30/60/90/120 km): **112 / 158 / 162 / 162**
- approved generic accessibility features or scores: **0**

## Interpretation limit

These fields are Swiss straight-line population context, not road or public-transport travel time, not a labour or visitor market, and not a destination catchment. Municipality population is collapsed to one representative point, so totals within a radius are discretised approximations. Foreign population is excluded. The output therefore reports the distance to the official Swiss country boundary and a radius-specific truncation-risk flag whenever the Swiss-only circle reaches that boundary; the flag diagnoses incompleteness but does not fill it. Terrain, network impedance, seasonal closures and travel behaviour are not represented. Consequently `accessibility_feature_approved` remains false and the generic `accessibility_score` remains blank; no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/municipality_population_geometry_2026.csv`
- `data_processed/path_c_cluster_accessibility_context.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified context columns appended)
