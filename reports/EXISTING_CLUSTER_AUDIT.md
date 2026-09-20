# Existing ski-lift cluster audit

## Reuse decision

The existing clustering is preserved and reusable as a **provisional lift-cluster reference layer**. It was validated rather than rebuilt. It is not yet an approved table of independent ski destinations and does not solve the separate tourism-municipality exposure problem.

## Structural results

| Check | Result |
|---|---:|
| Lift geometries in GPKG | 1,805 |
| Existing clusters | 242 |
| Clusters linked to at least one resort listing | 162 |
| Unnamed clusters | 80 |
| Clusters with multiple listings | 53 |
| Unique lift FIDs across cluster memberships | 1,805 |
| Duplicate lift memberships | 0 |
| Count mismatches among assignment, summary, and GeoJSON | 0 |
| Invalid lift geometries | 0 |

## Geographic validation

The validation script decoded the GPKG geometries directly and compared each resort point with the preserved cluster geometries.

- Recomputed distances agree with stored assignment distances to within 0.26 metres.
- Every one of the 271 resort listings was assigned to the nearest preserved cluster geometry.
- Assignment labels comprise 257 `confident`, 7 `warning`, and 7 `review` cases.
- Cluster labels comprise 197 `confident` and 45 `warning` cases.

These results support internal reproducibility. They do not prove that the cluster thresholds or destination boundaries are substantively ideal. Large multi-station domains and close neighbouring clusters remain domain-review cases.

## Outputs

- `reports/cluster_geometry_validation.csv`: listing-level distance validation.
- `reports/assignment_review_queue.csv`: all non-confident assignments.
- `reports/multiple_resorts_per_cluster.csv`: clusters carrying multiple listings.
- `figures/existing_assignment_flags.png`: spatial distribution of preserved assignment quality.

## Methodological boundary

The validated relationship is:

```text
lift geometry -> existing lift cluster -> provisional resort listing
```

It is not:

```text
ski destination -> accommodation market -> hotel overnight stays
```

No municipality exposure is inferred from cluster validity alone.
