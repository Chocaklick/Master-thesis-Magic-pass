# Qualified proximity to official public-transport stops

## Scope and definitions

The checksum-verified OFT/BAV archive has a published data state of **2026-09-20** and contains **28,967** operating points. The official data model distinguishes passenger stops from pure operating points. This analysis therefore retains only the **27,325** records with type `VP` (stop) or `VPG` (stop and loading point).

The nearest train station is selected from the **1,717** passenger stops whose official transport-mode code contains elementary code `B` (train), including multi-mode combinations. Rack railway (`E`) is a separate published mode and is not silently reclassified as train. All-stop proximity includes every mode in the official passenger-stop subset, including bus, train, tram, ship, funicular, gondola and chairlift.

Distances are EPSG:2056 Euclidean straight-line distances from each supplied resort-listing coordinate. Cluster summaries use the minimum, median and maximum across eligible supplied listing points rather than an artificial median-cluster point. Ties are resolved deterministically after sorting by official stop number.

## Coverage and descriptive reference

- eligible Swiss resort listings with both distances: **268 / 271**
- listings outside the complete Swiss scope and left missing: **3**
- clusters complete for every supplied listing point: **161 / 162**
- partially covered clusters: **1**
- apparent Path C candidates with complete context: **103 / 104**
- median of cluster-median distance to any official passenger stop: **0.33 km**
- median of cluster-median distance to a train station: **4.39 km**
- maximum eligible listing distance to any official passenger stop: **3.09 km**
- maximum eligible listing distance to a train station: **24.18 km**
- nearest all-stop modes across eligible listings: Bus: 135, Chemin de fer à crémaillère: 2, Funiculaire: 3, Funiculaire / Télécabine: 1, Train: 4, Télécabine: 51, Télésiège: 72
- approved generic accessibility features or scores: **0**

The outside-scope listings are Avoriaz 1800 Portes du Soleil (`avoriaz_1800_portes_du_soleil`), Chapelle Abondance La Chapelle d'Abondance / Portes du Soleil (`chapelle_abondance_la_chapelle_d_abondance_portes_du_soleil`), Châtel Portes du Soleil (`chatel_portes_du_soleil`). The OFT source can include selected foreign operating points but is not a complete French stop universe, so these rows are not assigned to a potentially incomplete nearest point. Their shared cross-border cluster is explicitly partial.

## Interpretation limit

This is current straight-line point proximity, not a walking, driving or public-transport route. It does not measure service frequency, timetable convenience, transfers, waiting time, seasonal operation, winter closures, fare integration or accessibility from a validated valley/base arrival node. The official mode attribute describes the infrastructure for which a stop is designed and is not by itself proof of a particular service in every timetable period. A supplied resort coordinate may be on-mountain; accordingly, the nearest all-mode stop can be the resort's own cableway or chairlift and must not be interpreted automatically as external access quality. `public_transport_stop_proximity_feature_approved` therefore remains false, `accessibility_score` remains blank, and no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/resort_public_transport_stop_context.csv`
- `data_processed/path_c_cluster_public_transport_stop_context.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified stop-proximity columns appended)
