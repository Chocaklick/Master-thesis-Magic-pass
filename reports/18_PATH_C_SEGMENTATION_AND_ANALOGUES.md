# Path C segmentation and analogue review

## Segmentation result

Of 162 linked lift clusters, **156** have all three structural features. The predeclared rule selects **k = 2**: silhouette **0.514**, median 80% subsample ARI **0.987**, and 10th-percentile ARI **0.924**. The full k=2–8 comparison is in `reports/path_c_segmentation_diagnostics.csv`.

| segment_id | entities | altitude_top_m_median | ski_area_km_median | number_lifts_median | resolved_current_magic_clusters | apparent_candidate_clusters | descriptive_profile |
|---|---|---|---|---|---|---|---|
| SEGMENT_01 | 83 | 1250.000 | 3.000 | 2.000 | 22 | 61 | lower altitude, lower ski area, lower lift count |
| SEGMENT_02 | 73 | 2364.000 | 32.300 | 7.000 | 28 | 43 | higher altitude, higher ski area, higher lift count |

These are broad current structural segments, not treatment-effect groups. **53** lift clusters contain supplied listings that disagree on at least one structural feature; the cluster table retains every min/median/max range rather than hiding that ambiguity.

## Analogue system

- **50** structurally complete clusters have a resolved link to the current official Magic Pass map and form the current-member reference pool.
- **8** reviewed destinations have complete unadjusted 24-month pre/post capacity diagnostics and form the historical-pattern reference pool.
- **104** structurally complete clusters with no resolved current, historical or precautionary Magic relation are scored as *apparent* non-member candidates. This is not verified non-membership.
- Against the eight reviewed treated references, 74 candidates have good support, 5 moderate extrapolation and 25 strong extrapolation under empirical leave-one-out distance thresholds.

For each candidate, `data_processed/path_c_candidate_analogues.csv` retains three closest current Magic clusters, three closest reviewed treated destinations, their standardised distances, the three unadjusted hotel-change diagnostics, an empirical support flag, network-distance context and snow vulnerability. The analogue signal is the median of those three changes; its low/high fields are an observed range, **not a confidence interval**.

## Two dimensions kept separate

The decision-support export contains an analogue-opportunity percentile and a snow-vulnerability percentile for **104** candidates. The downstream pipeline appends qualified point-container tourism context, Swiss straight-line population context, official NPVM 2025 zonal road/public-transport context and official OFT/BAV straight-line proximity to passenger stops and train stations. A separate treatment-municipality module supplies winter-2026 scheduled journey time for the 11 reviewed destinations; it is not merged into candidate scores because arrival-node face validation and historical timetable comparison remain pending. Neither tourism dependence nor destination-level accessibility is approved. Strategic need is therefore incomplete. Predicted-uplift fields are blank (0 populated), and no composite score is produced (0 populated).

## Outputs and next evidence needs

- `data_processed/path_c_resort_cluster_features.csv`
- `data_processed/path_c_cluster_segments.csv`
- `data_processed/path_c_reviewed_treated_reference.csv`
- `data_processed/path_c_candidate_analogues.csv`
- `data_processed/path_c_cluster_tourism_context.csv`
- `data_processed/path_c_cluster_accessibility_context.csv`
- `data_processed/path_c_cluster_transport_accessibility_context.csv`
- `data_processed/path_c_cluster_public_transport_stop_context.csv`
- `data_processed/magic_pass_decision_support.csv`

The min/median/max audit and the qualified contexts are documented in reports 19–25. Next, face-validate the selected arrival nodes, compare the historical GTFS anchor feeds, validate the within-municipality NPVM zone proxies, add motorway and cross-border population context where relevant, define defensible destination catchments, and audit competing-pass status for apparent candidates. Until then the export is an exploratory dashboard-ready prototype, not a recommendation ranking.
