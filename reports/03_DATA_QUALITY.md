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
| Tourism municipality exposure | Same-destination distances now cover 11×186 destination–municipality rows, but current polygon/representative-point distance cannot substitute for accommodation-market mapping or travel time |
| Hotel outcome | Strong source and long panel; suppression is material and municipality boundaries need review |
| Hotel capacity | Official monthly HESTA table integrated; 29,274/31,248 supply rows complete; live-table revisions preserved separately |
| Magic Pass event evidence | Reviewed-unit continuity complete; 29 broader event links remain unresolved and individual annual modality is incomplete |
| Treatment readiness | Zero approved treatment units at this checkpoint |
| Snow/climate | Daily SLF snow proxy integrated; 211/271 listings have high/moderate proxy comparability and ≥10 usable winters; next-nearest-station sensitivity has high/moderate agreement for 11/15 reviewed components and low agreement for four; not direct piste measurement |
| Temporal controls | All 1,848 reviewed rows receive deterministic calendar fields; 286 rows fall in a broad COVID sensitivity interval that is not a legal restriction chronology |
| Temperature/precipitation | Seven official SwissMetNet stations cover the 15 reviewed treatment components; 1,744/1,749 destination-months complete; regional proxy only |
| Accessibility | Missing |

## Resort-level assessment

`data_processed/resort_data_quality.csv` scores eight equally weighted evidence dimensions: identity scope, lift assignment, geolocation, tourism exposure, hotel outcome, membership history, infrastructure completeness, and snow/climate. After the qualified SLF proxy was added, scores range from 28.1 to 68.8, with a mean of 52.3. Low-comparability snow links receive only partial credit.

This is an evidence-completeness score, not a resort ranking, opportunity score, or model confidence interval. All rows remain `causal_ready = false`, and each unresolved component is exposed in `data_quality_warnings`.

## Highest-priority corrections

1. Validate treatment intensity and exact winter-versus-summer scope. All active seasons are documented for the 14 reviewed units and seven panel units pass the 24/24 coverage screen, but no causal treatment or control is approved (see `08_MEMBERSHIP_EVIDENCE_REVIEW.md`).
2. Manually audit historical non-membership, competing passes, accessibility and investment for the 35 treatment-donor pairs prioritised in `11_DONOR_PRETREND_SCREEN.md`. The network-wide point-distance audit now flags 15 pairs within 30 km of another resolved Magic destination, but cannot by itself prove spillovers.
3. Convert the completed 26-label scope-risk review into independently validated destination domains: four Swiss labels still lack a supplied-listing relation and Les Diablerets remains ambiguous.
4. Establish tourism-exposure/accommodation markets and audit spillovers without double-counting. The same-destination distance gradient is exploratory: six of seven near/far contrasts are positive, but no exposure or effect is approved.
5. Audit historical BFS municipality changes before panel estimation. The distance pipeline exposes Moutier's BFS 700-to-6831 transition explicitly but does not harmonise all historical boundaries.
6. Add an independent gridded snow sensitivity and test temperature/precipitation sensitivity to alternative stations or a gridded source. The first next-nearest SLF-station test is complete, but its 47.2% median relative absolute depth gap confirms station dependence.

The current modelling decision is documented in `reports/model_feasibility_report.md`.
