# Qualified NPVM transport accessibility context

## Scope

The official ARE GeoPackage contains **7,978** National Passenger Traffic Model (NPVM) traffic zones and **84** named centre/agglomeration targets. Its STAC item dates the model output to **2025-06-30**. For every zone, the source provides modelled travel time by road and public transport to the fastest of the six major centres (Basel, Bern, Geneva, Lausanne, Lugano and Zurich) and to the fastest agglomeration or core municipality.

Each of the 271 supplied resort-listing coordinates is projected to EPSG:2056. Exact point-in-zone containment is used where available. Because NPVM zone polygons do not continuously cover high-alpine terrain, a Swiss point outside every zone is linked to the nearest zone that spatially intersects its independently resolved current municipality; the assignment distance remains explicit. No global nearest-zone assignment is used. Cluster values are minimum, median and maximum across usable listing-point assignments; this preserves multi-listing dispersion instead of assigning the artificial cluster-median coordinate to one zone. Exact-only medians are retained as a sensitivity reference where available.

## Coverage

- resort listings exactly assigned to one NPVM zone: **170 / 271**
- Swiss resort listings assigned to the nearest zone intersecting their current municipality: **98**
- resort listings with a usable travel-time value: **268 / 271**
- listings outside the Swiss municipality/NPVM scope: **3**
- ambiguous multi-zone listing assignments: **0**
- linked Path C clusters with every listing point assigned exactly: **89 / 162**
- linked clusters complete after the within-municipality zone proxy: **72**
- partially covered clusters: **1**
- apparent Path C candidates with usable travel-time context: **104 / 104**
- maximum reported within-municipality proxy distance: **3.64 km**
- approved generic transport-accessibility features or scores: **0**

The uncovered directory listings are Avoriaz 1800 Portes du Soleil (`avoriaz_1800_portes_du_soleil`), Chapelle Abondance La Chapelle d'Abondance / Portes du Soleil (`chapelle_abondance_la_chapelle_d_abondance_portes_du_soleil`), Châtel Portes du Soleil (`chatel_portes_du_soleil`). They are retained without imputation. Their shared cluster can still have Swiss listing points with valid values, so its coverage status remains partial rather than silently complete.

## Descriptive reference values

Across the 162 cluster summaries, the median of the cluster-level median travel times is **72.2 minutes by road** and **108.2 minutes by public transport** to a major centre. The analogous values to the fastest agglomeration/core municipality are **26.0** and **42.0 minutes**.

## Interpretation limit

These are NPVM traffic-zone model outputs, not live door-to-door routes, rail-only times, timetables, waiting-time guarantees, access from a particular valley station, or winter road-closure measures. For 98 Swiss high-alpine points, the nearest zone intersecting the same current municipality is a transparent spatial proxy; it is not an observed route origin, and municipality boundary changes can differ from the NPVM zone lineage. A supplied resort coordinate may represent a listing or ski area rather than the actual visitor arrival node. Cluster aggregation describes the supplied directory points and does not establish a destination catchment. Therefore `transport_accessibility_feature_approved` remains false, the generic `accessibility_score` remains blank, and no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/resort_transport_accessibility_context.csv`
- `data_processed/path_c_cluster_transport_accessibility_context.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified transport columns appended)
