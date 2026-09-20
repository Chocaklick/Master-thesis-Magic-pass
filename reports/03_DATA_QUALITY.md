# 03 — Data quality

## Overall assessment

The supplied files are structurally stronger than their filenames initially suggested: hashes are stable, identifiers reconcile, lift assignments are geographically reproducible, and the hotel panel preserves suppression rather than silently replacing it. The main risks are semantic and causal rather than mechanical.

## Quality dimensions

| Dimension | Current assessment |
|---|---|
| Raw-file integrity | Strong: all 11 inputs hashed and verified before transformation |
| Lift-cluster consistency | Strong internally: no duplicate lift memberships or count mismatches |
| Resort identity | Weak-to-moderate: 271 listings remain provisional, not validated independent domains |
| Current point geolocation | Strong for 268/271 coordinates; three lie outside the Swiss layer |
| Tourism municipality exposure | Not established; point containment cannot substitute for accommodation-market mapping |
| Hotel outcome | Strong source and long panel; suppression is material and municipality boundaries need review |
| Magic Pass event evidence | Official sources, but incomplete continuity/exit coverage and 29 unresolved event links |
| Treatment readiness | Zero approved treatment units at this checkpoint |
| Snow/climate and accessibility | Missing |

## Resort-level assessment

`data_processed/resort_data_quality.csv` scores eight equally weighted evidence dimensions: identity scope, lift assignment, geolocation, tourism exposure, hotel outcome, membership history, infrastructure completeness, and snow/climate. Scores range from 25.0 to 56.2, with a mean of 43.0.

This is an evidence-completeness score, not a resort ranking, opportunity score, or model confidence interval. All rows remain `causal_ready = false`, and each unresolved component is exposed in `data_quality_warnings`.

## Highest-priority corrections

1. Review the 18 provisional base-entry/outcome links and resolve shared-municipality attribution.
2. Define independent destination units and reconcile composite official destinations with Bergfex listings and lift clusters.
3. Complete membership status for every season, including exits and operator-group scope.
4. Establish weighted destination-to-municipality accommodation markets without double-counting.
5. Audit historical BFS municipality changes before panel estimation.
6. Only after these gates, collect snow, capacity, accessibility, investment, and local-control variables.

The current modelling decision is documented in `reports/model_feasibility_report.md`.
