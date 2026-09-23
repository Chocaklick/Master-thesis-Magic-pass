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

The decision-support export contains an analogue-opportunity percentile and a snow-vulnerability percentile for **104** candidates. The downstream pipeline appends qualified point-container tourism context, Swiss municipality-point population, harmonised Eurostat 2021 cross-border grid population, official NPVM 2025 zonal road/public-transport context, official OFT/BAV straight-line proximity to passenger stops and train stations, current FEDRO/ASTRA national-road-axis proximity, explicit links to three current official competing-pass rosters, focal-excluded 25/50 km density for directory clusters and the reviewed pass-network union, and a four-rule listing-point distance sensitivity. The cross-border grid closes the known geographic truncation of the Swiss-only radii but remains residential straight-line context, not a visitor catchment. The NPVM layer covers every candidate but uses a transparent nearest-zone-within-current-municipality proxy for high-alpine listing points outside the zone polygons. Stop and national-road-axis proximity have usable cluster context for every candidate, while the mixed Swiss/French Portes du Soleil cluster is explicitly partial. The road-axis schema does not support a motorway-only label. Competing-pass non-links do not verify market absence; current network density does not reconstruct historical competition or true commercial domains; and the distance sensitivity does not certify cluster coherence. Neither tourism dependence nor destination-level accessibility is approved. Strategic need is therefore incomplete. Predicted-uplift fields are blank (0 populated), and no composite score is produced (0 populated).

## Outputs and next evidence needs

- `data_processed/path_c_resort_cluster_features.csv`
- `data_processed/path_c_cluster_segments.csv`
- `data_processed/path_c_reviewed_treated_reference.csv`
- `data_processed/path_c_candidate_analogues.csv`
- `data_processed/path_c_cluster_tourism_context.csv`
- `data_processed/path_c_cluster_accessibility_context.csv`
- `data_processed/path_c_cluster_cross_border_population_context.csv`
- `data_processed/path_c_cluster_transport_accessibility_context.csv`
- `data_processed/path_c_cluster_public_transport_stop_context.csv`
- `data_processed/path_c_cluster_national_road_proximity_context.csv`
- `data_processed/path_c_cluster_competing_pass_context.csv`
- `data_processed/path_c_cluster_network_context.csv`
- `data_processed/path_c_cluster_geographic_sensitivity.csv`
- `data_processed/magic_pass_decision_support.csv`

The structural min/median/max audit and qualified contexts are documented in reports 19–33. Cross-border population, current national-road-axis proximity, the scoped current competing-pass review, current directory/network density and listing-point distance-rule sensitivity are complete within their declared scopes. Next, obtain the historical GTFS anchors through a manual or authorised channel, define defensible destination catchments, and reconstruct historical competing-pass rosters if competition is to enter a pre-treatment model. A true motorway-access variable would require a source that explicitly classifies road type and usable entrances; the present ASTRA layer does neither. The NPVM proxy geometry and same-pair distance/transit audits are complete, but 50 proxy-only clusters still lack an internal exact-zone sensitivity reference. If door-to-lift precision is needed, add explicit walking/access evidence for the six village/local-centre proxies. Until then the export is an exploratory dashboard-ready prototype, not a recommendation ranking.
