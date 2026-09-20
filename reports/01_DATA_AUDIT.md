# 01 — Data audit

## Checkpoint status

Checkpoint 1 is complete. Eleven supplied raw files were hashed and audited without modification. The audit identified usable hotel, resort-listing, lift, assignment, cluster, and legacy-map inputs, together with important semantic gaps.

## Core findings

- 271 Bergfex-derived resort listings are available, but they collapse to 162 assigned lift clusters within a universe of 242 clusters. No count is yet accepted as the number of independent ski destinations.
- The lift-cluster artifacts are internally consistent: 1,805 unique lift features, no duplicated membership, no count mismatches, valid geometries, and nearest-cluster assignment for all 271 listings.
- The hotel source has 186 municipalities and 28,455 observed municipality-month total-night outcomes from 2013-01 to 2026-03.
- Suppression is material and explicit. The monthly total-night measure has 2,793 `...` cells, retained as missing.
- Annual/monthly reconciliation has zero discrepancies where all twelve months are observed.
- No supplied resort row contains a municipality assignment. A legacy name-overlap map is insufficient for exposure modelling.

## Reproducible evidence

| Output | Purpose |
|---|---|
| `metadata/raw_file_manifest.csv` | Immutable file hashes and local source IDs |
| `reports/data_audit.csv` | Dataset-level inventory and recommended use |
| `reports/data_audit_details.json` | Full column profiling and suspicious tokens |
| `metadata/data_dictionary.csv` | Variable definitions, lineage, formulas, and causal roles |
| `reports/EXISTING_CLUSTER_AUDIT.md` | Dedicated cluster reuse decision |
| `reports/initial_findings.json` | Machine-readable checkpoint metrics |

## Audit decision

The outcome and cluster inputs are suitable for continued data engineering. Treatment and exposure are not ready for causal analysis. The next work must prioritize entity scope and membership/municipality validation rather than additional high-dimensional features.
