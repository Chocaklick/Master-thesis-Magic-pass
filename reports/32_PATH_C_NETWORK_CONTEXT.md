# Current ski-cluster and reviewed pass-network context

## Scope

This module quantifies the current spatial surroundings of all **162 preserved lift clusters** represented in the supplied resort directory. Great-circle distances use each cluster's median supplied listing coordinate, and all neighbourhood statistics exclude the focal cluster itself. The full **26,082 ordered non-self pair** table makes every count reproducible.

The context distinguishes:

- all other directory-linked lift clusters;
- clusters with a resolved current Magic Pass link;
- clusters with at least one listing linked to the three reviewed competing-pass rosters;
- the union of those two reviewed pass networks.

Counts are reported within 25 and 50 km. The surrounding published ski-area total is the sum of cluster-median directory values with observed ski-area kilometres; observed and missing contributor counts remain separate.

## Candidate diagnostics

- apparent Path C candidates: **104**
- median nearest other directory cluster: **9.16 km**
- median other directory clusters within 25 / 50 km: **8 / 26**
- median other resolved current Magic clusters within 50 km: **1**
- median other reviewed competing-pass-linked clusters within 50 km: **6**
- median other clusters in the reviewed pass-network union within 50 km: **9**
- candidates with no other directory cluster within 25 km: **1**
- candidates with no other reviewed pass-network cluster within 50 km: **2**

## Interpretation limit

The preserved clusters are not validated independent commercial destinations, median coordinates can be artificial for multi-listing clusters, straight-line distance ignores terrain and transport, directory ski-area values are undated and can represent overlapping products, and the reviewed pass rosters are current rather than historical. Counts therefore describe the supplied directory and reviewed network links—not true competitor counts, skier substitution, market penetration, visitor flows or pre-treatment network exposure. `historical_network_context_verified` and `network_context_feature_approved` remain false everywhere. No accessibility, uplift or composite score is populated.

## Outputs

- `data_processed/path_c_cluster_network_context.csv`
- `reports/path_c_cluster_network_pairs.csv`
- `reports/network_context_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified network context appended)
