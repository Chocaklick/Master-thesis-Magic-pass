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
| Hotel capacity | Official monthly HESTA table integrated; 29,274/31,248 supply rows complete; live-table revisions preserved separately |
| Magic Pass event evidence | Official sources, but incomplete continuity/exit coverage and 29 unresolved event links |
| Treatment readiness | Zero approved treatment units at this checkpoint |
| Snow/climate | Daily SLF snow proxy integrated; 211/271 listings have high/moderate proxy comparability and ≥10 usable winters; not direct piste measurement |
| Temperature/precipitation | Seven official SwissMetNet stations cover the 15 reviewed treatment components; 1,744/1,749 destination-months complete; regional proxy only |
| Accessibility | Missing |

## Resort-level assessment

`data_processed/resort_data_quality.csv` scores eight equally weighted evidence dimensions: identity scope, lift assignment, geolocation, tourism exposure, hotel outcome, membership history, infrastructure completeness, and snow/climate. After the qualified SLF proxy was added, scores range from 28.1 to 68.8, with a mean of 52.3. Low-comparability snow links receive only partial credit.

This is an evidence-completeness score, not a resort ranking, opportunity score, or model confidence interval. All rows remain `causal_ready = false`, and each unresolved component is exposed in `data_quality_warnings`.

## Highest-priority corrections

1. Complete membership status for the 25 remaining unverified active unit-seasons, including exits and operator-group scope.
2. Resolve the 26 unmatched official base-entry labels and independently validate destination domains outside the reviewed treatment units.
3. Establish tourism-exposure/accommodation markets and audit spillovers without double-counting.
4. Audit historical BFS municipality changes before panel estimation.
5. Test temperature/precipitation and snow sensitivity to alternative stations or a gridded source.
6. Collect accessibility, investment, local-control and competing-pass variables only where they materially improve the selected design.

The current modelling decision is documented in `reports/model_feasibility_report.md`.
