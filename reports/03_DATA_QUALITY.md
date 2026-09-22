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
| Tourism municipality exposure | Same-destination distances cover 11×186 destination–municipality rows. STATPOP/HESTA ratios add complete 2025 point-container context for 52 linked clusters, but neither current containment nor representative-point distance establishes an accommodation market or destination catchment |
| Hotel outcome | Strong source and long panel; suppression is material and municipality boundaries need review |
| Hotel capacity | Official monthly HESTA table integrated; 29,274/31,248 supply rows complete; live-table revisions preserved separately |
| Magic Pass event evidence | Reviewed-unit continuity complete; 29 broader event links remain unresolved and individual annual modality is incomplete |
| Treatment readiness | Zero approved treatment units at this checkpoint |
| Snow/climate | Daily SLF snow proxy integrated; 211/271 listings have high/moderate proxy comparability and ≥10 usable winters; next-nearest-station sensitivity has high/moderate agreement for 11/15 reviewed components and low agreement for four; not direct piste measurement |
| Temporal controls | All 1,848 reviewed rows receive deterministic calendar fields; 286 rows fall in a broad COVID sensitivity interval that is not a legal restriction chronology |
| Temperature/precipitation | Seven official SwissMetNet stations cover the 15 reviewed treatment components; 1,744/1,749 destination-months complete; regional proxy only |
| Donor external shocks | Seven beyond-50-km pairs checked against complete annual Magic rosters and official operator/government sources; all seven are excluded for overlapping local tourism or infrastructure shocks |
| Tourism dependence | Official population and hotel-intensity ratios available for 2,115 municipalities / 185 complete HESTA joins; 39 Path C candidates have complete point-container context, but zero destination-level tourism-dependence features are approved |
| Accessibility | Qualified Swiss straight-line population context covers all 162 linked clusters / 104 candidates. Official NPVM 2025 context is usable for 268/271 listing points; current OFT/BAV stop proximity covers the same 268 Swiss points. Winter-2026 GTFS adds 49,104 scheduled journey requests across 2,046 reviewed destination–hotel-municipality pairs, with 38,504 feasible under declared limits and 1,104 pairs complete at every sampled time. Three French listing points remain outside the cluster-level stop sources. Zonal context, straight-line stop distance and the current two-day timetable sample are not validated historical arrival-node accessibility or destination catchments; historical service comparison is pending and zero accessibility features are approved |

## Resort-level assessment

`data_processed/resort_data_quality.csv` scores eight equally weighted evidence dimensions: identity scope, lift assignment, geolocation, tourism exposure, hotel outcome, membership history, infrastructure completeness, and snow/climate. After the qualified SLF proxy was added, scores range from 28.1 to 68.8, with a mean of 52.3. Low-comparability snow links receive only partial credit.

This is an evidence-completeness score, not a resort ranking, opportunity score, or model confidence interval. All rows remain `causal_ready = false`, and each unresolved component is exposed in `data_quality_warnings`.

## Highest-priority corrections

1. Validate treatment intensity and exact winter-versus-summer scope. All active seasons are documented for the 14 reviewed units and seven panel units pass the 24/24 coverage screen, but no causal treatment or control is approved (see `08_MEMBERSHIP_EVIDENCE_REVIEW.md`).
2. Rebuild the donor search if causal identification remains a goal. The current top-five-per-treatment shortlist is exhausted: 28 pairs are proximity-deprioritised and all seven remote pairs are excluded for overlapping local shocks. Complete-roster station-label absence is documented for the remote pairs, although corporate-affiliate and exact competing-pass tariff details remain qualified.
3. Convert the completed conservative 26-label scope review into independently validated destination domains. Four documented Swiss destinations have no own supplied-directory row, and Les Diablerets remains an explicit many-to-many overlap rather than an identity match.
4. Establish tourism-exposure/accommodation markets and audit spillovers without double-counting. The STATPOP/HESTA ratios describe point containers only, population-radius fields omit cross-border markets, and NPVM values can use municipality-constrained zone proxies. Winter-2026 GTFS now supplies scheduled journey time from municipality main stops to algorithmic component arrival nodes, but the 15 nodes need manual face validation and the 2018–2025 archive feeds need identical stop/service comparison before historical or causal use. The same-destination distance gradient remains exploratory: six of seven near/far contrasts are positive, but no exposure or effect is approved.
5. Audit historical BFS municipality changes before panel estimation. The seven STATPOP 2025 identifiers affected by the five official 2026 mutations are now reconciled to current geometry with the population total preserved, but the earlier outcome panel is not fully boundary-harmonised.
6. Add an independent gridded snow sensitivity and test temperature/precipitation sensitivity to alternative stations or a gridded source. The first next-nearest SLF-station test is complete, but its 47.2% median relative absolute depth gap confirms station dependence.

The current modelling decision is documented in `reports/model_feasibility_report.md`.
