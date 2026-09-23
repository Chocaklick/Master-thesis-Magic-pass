# Path C cluster geography and network-distance sensitivity

## Scope

This audit preserves the existing **162 lift clusters** and their **271 supplied listing points**. It does not rebuild or certify the clustering. For each cluster it measures the full within-cluster listing-point spread. For every one of the **26,082 ordered non-self cluster pairs**, it compares:

- minimum distance across all cross-cluster listing-point pairs (at least one point pair is this close);
- median distance across all cross-cluster listing-point pairs;
- the v0.14 distance between coordinate-wise median listing locations;
- maximum distance across all cross-cluster listing-point pairs (all point pairs are within a radius only when this value is within it).

## Within-cluster spread

- single-listing clusters: **109**
- multi-listing clusters: **53**
- multi-listing diameter at most 5 km: **24**
- multi-listing diameter above 5 and at most 25 km: **28**
- clusters with diameter above 25 km: **1**
- median multi-listing diameter: **6.54 km**
- maximum diameter: **46.35 km** for `SKI_CLUSTER_200`

## Candidate sensitivity

Among **104 apparent Path C candidates**, the directory-neighbour count changes across the four distance rules for **71** candidates at 25 km and **86** at 50 km. The reviewed pass-network count changes for **56** candidates at 25 km and **72** at 50 km. The largest candidate spans are **13** directory clusters at 25 km and **11** reviewed-network clusters at 50 km.

Across all unique cluster pairs, the absolute difference between the coordinate-wise-median distance and the median listing-pair distance is **0.00 km** at the median and **1.28 km** at the 95th percentile. The all-pair median is zero because most clusters contain one listing. Restricting to the **7,155 pairs involving at least one multi-listing cluster**, the median is **0.03 km** and the 95th percentile is **1.72 km**.

## Interpretation limit

Minimum distance is permissive, maximum distance is conservative, and neither is a uniquely correct destination-market definition. The supplied listings may be components of one product, neighbouring products, or directory labels at a different commercial grain. Coordinate-wise medians can fall between actual places. Straight-line distance still ignores terrain, roads, timetables, skier substitution and historical changes. Therefore `cluster_geographic_coherence_verified` and `network_distance_sensitivity_feature_approved` remain false everywhere. No cluster is reassigned, and no causal, uplift, accessibility or composite score is populated.

## Outputs

- `data_processed/path_c_cluster_geographic_sensitivity.csv`
- `reports/path_c_cluster_distance_rule_pairs.csv`
- `reports/cluster_geography_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified sensitivity fields appended)
