# Existing Ski-Lift Cluster Audit

## Status

Pending source data. This report intentionally does not reconstruct clusters or invent counts.

## Intended object of the audit

The prior workflow is understood conceptually as:

```text
individual ski lifts -> geographic lift clusters -> assigned ski-resort name -> resort identity
```

The expected files are `clusters_stations_final_clean.csv` and `assignations_stations_final_clean.csv`. The latter reportedly associates lift clusters with ski resorts. Neither file was present during initialization, so their actual schemas and methodology could not be inspected.

## Baseline findings

| Question | Finding |
|---|---|
| Number of clusters | Unknown; source file absent |
| Number assigned to resorts | Unknown; source file absent |
| Unassigned clusters | Unknown |
| Duplicate cluster identifiers | Not testable |
| Conflicting resort assignments | Not testable |
| Ambiguous cases | Not identifiable yet |
| Geographic plausibility | Not testable |
| Preliminary usability | Undetermined pending audit |

## Validation plan once files are supplied

1. Preserve the originals under `data_raw/` and record checksums and provenance.
2. Identify the row grain and all candidate identifiers in both files.
3. Count unique lift, cluster, and resort identifiers; distinguish missing assignments from intentionally unassigned clusters.
4. Test identifier uniqueness, orphaned keys, one-to-many/many-to-many assignments, duplicate rows, and conflicting labels.
5. Compare cluster-level summaries with assignment-level records without altering either source.
6. Flag implausible coordinate ranges, coordinate reference-system ambiguity, disconnected geometries, extreme geographic extents, and naming inconsistencies.
7. Geographically verify a documented, reproducible sample including large clusters, small clusters, border cases, duplicate names, and suspicious assignments.
8. Classify issues into harmless label differences, resolvable corrections, and cases requiring domain review.

## Methodological boundary

Even a valid lift-cluster-to-resort mapping does not establish which municipality or municipalities should receive a resort's hotel overnight stays. The later chain may be resort to tourism destination to one or more municipalities. This separate crosswalk must have its own evidence and uncertainty.

## Reuse decision

No reuse decision is possible before the files and any methodology notes are available. The default is to preserve and audit the existing clustering, not rebuild it. Limited corrections, if eventually justified, must be expressed in a separate versioned correction table so the original assignments remain recoverable.
