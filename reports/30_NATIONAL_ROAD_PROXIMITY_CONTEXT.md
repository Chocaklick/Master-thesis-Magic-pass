# Qualified proximity to official Swiss national-road axes

## Scope and definitions

The checksum-verified FEDRO/ASTRA File Geodatabase has STAC reference datetime **2026-08-01T00:00:00Z**, asset update timestamp **2026-09-01T03:32:13.046159Z**, embedded data-status date **2026-09-01**, and official coordinate reference **EPSG:2056**. It publishes **166 main-axis features**, **596 connection-axis features**, **2,292 ramp-axis features**, and **30 feeder-axis features**. Geometry lengths reproduce every published `SHAPE_Length` value within numerical tolerance.

Two straight-line measures are retained from each eligible supplied listing coordinate:

- distance to the nearest official `Stammachsen` main axis;
- distance to the nearest line in any of the four official national-road axis layers.

The source fields identify a national-route number, segment and axis family, but do **not** provide a motorway-versus-non-motorway classification. The analysis therefore never renames these measures as motorway distance. Cluster summaries preserve the minimum, median and maximum across eligible supplied listing points.

## Coverage and descriptive reference

- eligible Swiss resort listings with both distances: **268 / 271**
- listings outside the complete Swiss source scope and left missing: **3**
- clusters complete for every supplied listing point: **161 / 162**
- partially covered clusters: **1**
- apparent Path C candidates with complete context: **103 / 104**
- median of cluster-median distance to a national-road main axis: **6.81 km**
- median of cluster-median distance to any national-road axis: **6.79 km**
- maximum eligible listing distance to a main axis: **41.41 km**
- maximum eligible listing distance to any published axis: **41.41 km**
- nearest any-axis layer across eligible listings: Anschlussachse: 57, Rampenachsen: 35, Stammachsen: 172, Zubringerachsen: 4
- approved generic accessibility features or scores: **0**

The outside-scope listings are Avoriaz 1800 Portes du Soleil (`avoriaz_1800_portes_du_soleil`), Chapelle Abondance La Chapelle d'Abondance / Portes du Soleil (`chapelle_abondance_la_chapelle_d_abondance_portes_du_soleil`), Châtel Portes du Soleil (`chatel_portes_du_soleil`). They are French points in the shared Portes du Soleil cluster. A distance from those points to the nearest Swiss axis would be computable geometrically but would compare against a truncated road universe, so it remains missing and the cluster is marked partial.

## Interpretation limit

These are current Euclidean point-to-line distances, not road-network routes, distance to a usable motorway entrance, travel times, winter-reliable access, congestion, parking capacity or historical pre-treatment infrastructure. The closest line may be a main axis, ramp, connection or feeder, and physical proximity does not establish legal access. The official source is current rather than season-specific. `national_road_proximity_feature_approved` therefore remains false, `accessibility_score` remains blank, and no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/resort_national_road_proximity_context.csv`
- `data_processed/path_c_cluster_national_road_proximity_context.csv`
- `reports/national_road_proximity_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified road-axis context appended)
