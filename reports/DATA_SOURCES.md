# Data sources and provenance

This report is generated from `metadata/data_sources_master.csv`. Raw internet responses are immutable and accompanied by collection-log entries and SHA-256 metadata where available.

## AESCHI_LIFT_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official ski-area scope: Aeschiallmend and Allmispitz, with Lucky village lift explicitly outside Magic Pass
- **Producer:** Aeschi Tourismus
- **Exact URL:** https://www.aeschi-tourismus.ch/en/experiences/winter-sport/ski-lifts
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T19:28:15.013061+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/AESCHI_LIFT_SCOPE_OFFICIAL_20260920T192815Z.html`.

## ANNIVIERS_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official municipal evidence that Grimentz, Zinal, Saint-Luc and Chandolin belong to Anniviers
- **Producer:** Commune d'Anniviers
- **Exact URL:** https://www.anniviers.org/fr/villages-hameaux-6.html
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:33.490971+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/ANNIVIERS_SCOPE_OFFICIAL_20260920T005533Z.html`.

## BBGR_ANNUAL_2017_18 — Bergbahnen Graubünden annual report 2017/18

- **Contents and relevance:** Official 2017/2018 annual report documenting the SnowPass Graubünden market, regional first entries and the then-current TopCard change
- **Producer:** Bergbahnen Graubünden
- **Exact URL:** https://www.bbgr.ch/wp-content/uploads/2016/10/BBGR_WEB-JB_2017-18.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:18:44.601748+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2017-07 to 2018-06.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/BBGR_ANNUAL_2017_18_20260921T151844Z.pdf`.

## BBGR_ANNUAL_2018_19 — Bergbahnen Graubünden annual report 2018/19

- **Contents and relevance:** Official 2018/2019 annual report documenting SnowPass Graubünden and three TopCard days in Upper Engadine
- **Producer:** Bergbahnen Graubünden
- **Exact URL:** https://www.bbgr.ch/wp-content/uploads/2016/10/WEB_BBGR_JB_18_19.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:18:47.270687+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2018-07 to 2019-06.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/BBGR_ANNUAL_2018_19_20260921T151847Z.pdf`.

## BBGR_ANNUAL_2019_20 — Bergbahnen Graubünden annual report 2019/20

- **Contents and relevance:** Official 2019/2020 annual report documenting the last SnowPass winter and transition to the year-round graubündenCARD
- **Producer:** Bergbahnen Graubünden
- **Exact URL:** https://www.bbgr.ch/wp-content/uploads/2020/11/WEB_BBGR_JB_19_20.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:18:49.252750+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2019-07 to 2020-06.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/BBGR_ANNUAL_2019_20_20260921T151849Z.pdf`.

## BERGFEX_RESORT_DIRECTORY — Bergfex Swiss ski-resort directory

- **Contents and relevance:** Existing resort-directory scrape supplied by the researcher
- **Producer:** bergfex GmbH
- **Exact URL:** https://www.bergfex.ch/schweiz/
- **Access and retrieval date:** Legacy region-page HTML scraping; upstream R script inspected; UNKNOWN.
- **Variables:** resort_name|region|url_station|altitude_top_m|ski_area_km|number_lifts
- **Transformations:** Unique URL join to normalised listing table; no new scrape
- **Coverage:** resort listing; undated snapshot; ? to ?.
- **Limitations:** Observation date and independent-domain semantics are unknown
- **Local raw file:** `data_raw/bergfex_stations_ski_suisse_par_region.csv`.

## BFS_HOTEL_CAPACITY_DATA — px-x-1003020000_201

- **Contents and relevance:** Monthly HESTA hotel supply, demand, and occupancy in open establishments by municipality
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_201/
- **Access and retrieval date:** PXWeb HTTP POST in 14 annual chunks; exact queries, responses, SHA-256 checksums, and logs preserved; 2026-09-20T08:39:13.504956+00:00.
- **Variables:** hotel_establishments_open|hotel_rooms_available|hotel_beds_available|hotel_room_occupancy_rate_pct|hotel_bed_occupancy_rate_pct
- **Transformations:** Annual chunks concatenated; literal '..' and '...' tokens preserved; numeric values parsed without imputation; exact municipality-date join to legacy demand panel
- **Coverage:** municipality; monthly grid; 2013-01 to 2026-12 grid; later months unavailable at retrieval.
- **Limitations:** 1,974 supply rows are unavailable/protected; 59 bed-occupancy percentages exceed 100 as published; 6 demand cells in 3 Davos months differ from the legacy extraction and are reported without overwriting it
- **Local raw file:** `data_external/source_evidence/BFS_HOTEL_CAPACITY_DATA_2013_20260920T083901Z.csv`.

## BFS_HOTEL_CAPACITY_METADATA — px-x-1003020000_201 metadata

- **Contents and relevance:** Live metadata for the HESTA supply, demand, and occupancy table
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_201/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T08:36:08.846339+00:00.
- **Variables:** capacity_table_schema|municipality_bfs_id
- **Transformations:** Dimension codes and municipality code-label pairs extracted exactly
- **Coverage:** municipality; metadata snapshot; 2013 to 2026.
- **Limitations:** Reference municipality universe is dated 2026-01-01; cached response anchors the schema
- **Local raw file:** `data_external/source_evidence/BFS_HOTEL_CAPACITY_METADATA_20260920T083608Z.json`.

## BFS_HOTEL_DATA — px-x-1003020000_101

- **Contents and relevance:** Monthly hotel arrivals and overnight stays in open establishments by municipality and visitor origin
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_101/
- **Access and retrieval date:** Existing researcher API extraction; construction script inspected; live metadata independently cached; UNKNOWN_FOR_EXISTING_DATA_FILE.
- **Variables:** hotel_arrivals|hotel_overnights|domestic_overnights|foreign_overnights
- **Transformations:** Annual rows excluded from monthly panel; literal tokens preserved; nonnegative integer cells parsed; domestic/foreign split and log1p derived
- **Coverage:** municipality; monthly plus annual total rows; 2013-01 to 2026-03 observed; later 2026 grid cells suppressed/unavailable.
- **Limitations:** 2,793 monthly total-night cells contain '...'; no imputation; municipality boundary changes still require review
- **Local raw file:** `data_raw/nuitée_commune_final.csv`.

## BFS_HOTEL_METADATA — px-x-1003020000_101 metadata

- **Contents and relevance:** Live metadata for the official hotel table, including municipality codes and labels
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_101/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:17:13.867148+00:00.
- **Variables:** hotel_table_schema|municipality_bfs_id
- **Transformations:** Municipality code-label pairs extracted without fuzzy matching
- **Coverage:** municipality; metadata snapshot; 2013 to 2026.
- **Limitations:** Live table composition can change; cached response is the reproducibility anchor
- **Local raw file:** `data_external/source_evidence/BFS_HOTEL_METADATA_20260919T231713Z.json`.

## BFS_MUNICIPAL_MUTATION_3999 — Official municipality mutation 3999

- **Contents and relevance:** Official 2026 Moutier canton-transfer mutation from BFS 700 to 6831
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.agvchapp.bfs.admin.ch/fr/mutations/3999
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T23:50:09.429030+00:00.
- **Variables:** source_bfs_id_2025|target_bfs_id_2026|municipality_mutation_relationship
- **Transformations:** Exact old/new BFS identifiers and municipality names transcribed to a versioned seven-row bridge; cached page tokens verified before use
- **Coverage:** affected Swiss municipality identifiers; official municipality mutation; 2026-01-01 to 2026-01-01.
- **Limitations:** Used only to align the complete 2025 STATPOP municipality universe to the 2026 boundary snapshot
- **Local raw file:** `data_external/source_evidence/BFS_MUNICIPAL_MUTATION_3999_20260921T235009Z.html`.

## BFS_MUNICIPAL_MUTATION_4000 — Official municipality mutation 4000

- **Contents and relevance:** Official 2026 Fétigny and Ménières fusion into Fétigny-Ménières
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.agvchapp.bfs.admin.ch/fr/mutations/4000
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T23:50:19.871716+00:00.
- **Variables:** source_bfs_id_2025|target_bfs_id_2026|municipality_mutation_relationship
- **Transformations:** Exact old/new BFS identifiers and municipality names transcribed to a versioned seven-row bridge; cached page tokens verified before use
- **Coverage:** affected Swiss municipality identifiers; official municipality mutation; 2026-01-01 to 2026-01-01.
- **Limitations:** Used only to align the complete 2025 STATPOP municipality universe to the 2026 boundary snapshot
- **Local raw file:** `data_external/source_evidence/BFS_MUNICIPAL_MUTATION_4000_20260921T235019Z.html`.

## BFS_MUNICIPAL_MUTATION_4001 — Official municipality mutation 4001

- **Contents and relevance:** Official 2026 Ulmiz inclusion into Gurmels
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.agvchapp.bfs.admin.ch/fr/mutations/4001
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T23:50:30.141502+00:00.
- **Variables:** source_bfs_id_2025|target_bfs_id_2026|municipality_mutation_relationship
- **Transformations:** Exact old/new BFS identifiers and municipality names transcribed to a versioned seven-row bridge; cached page tokens verified before use
- **Coverage:** affected Swiss municipality identifiers; official municipality mutation; 2026-01-01 to 2026-01-01.
- **Limitations:** Used only to align the complete 2025 STATPOP municipality universe to the 2026 boundary snapshot
- **Local raw file:** `data_external/source_evidence/BFS_MUNICIPAL_MUTATION_4001_20260921T235030Z.html`.

## BFS_MUNICIPAL_MUTATION_4002 — Official municipality mutation 4002

- **Contents and relevance:** Official 2026 Halten and Oekingen inclusion into Kriegstetten
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.agvchapp.bfs.admin.ch/fr/mutations/4002
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T23:50:40.444267+00:00.
- **Variables:** source_bfs_id_2025|target_bfs_id_2026|municipality_mutation_relationship
- **Transformations:** Exact old/new BFS identifiers and municipality names transcribed to a versioned seven-row bridge; cached page tokens verified before use
- **Coverage:** affected Swiss municipality identifiers; official municipality mutation; 2026-01-01 to 2026-01-01.
- **Limitations:** Used only to align the complete 2025 STATPOP municipality universe to the 2026 boundary snapshot
- **Local raw file:** `data_external/source_evidence/BFS_MUNICIPAL_MUTATION_4002_20260921T235040Z.html`.

## BFS_MUNICIPAL_MUTATION_4003 — Official municipality mutation 4003

- **Contents and relevance:** Official 2026 Villnachern inclusion into Brugg
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.agvchapp.bfs.admin.ch/fr/mutations/4003
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T23:50:50.728087+00:00.
- **Variables:** source_bfs_id_2025|target_bfs_id_2026|municipality_mutation_relationship
- **Transformations:** Exact old/new BFS identifiers and municipality names transcribed to a versioned seven-row bridge; cached page tokens verified before use
- **Coverage:** affected Swiss municipality identifiers; official municipality mutation; 2026-01-01 to 2026-01-01.
- **Limitations:** Used only to align the complete 2025 STATPOP municipality universe to the 2026 boundary snapshot
- **Local raw file:** `data_external/source_evidence/BFS_MUNICIPAL_MUTATION_4003_20260921T235050Z.html`.

## BFS_STATPOP_DATA — STATPOP px-x-0102010000_101

- **Contents and relevance:** Permanent resident population by municipality at 31 December 2025
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-0102010000_101/
- **Access and retrieval date:** PXWeb HTTP POST; exact query, raw response and SHA-256 checksum preserved; 2026-09-21T23:16:05.143142+00:00.
- **Variables:** resident_population|population_reference_year|municipality_bfs_id
- **Transformations:** Exact BFS code parsed from official municipality label; no population imputation; exact BFS join to HESTA 2025
- **Coverage:** municipality; annual reference-day population; 2025-12-31 to 2025-12-31.
- **Limitations:** Population is municipal context; it does not define a ski destination catchment
- **Local raw file:** `data_external/source_evidence/BFS_STATPOP_DATA_2025_20260921T231605Z.csv`.

## BFS_STATPOP_METADATA — px-x-0102010000_101 metadata

- **Contents and relevance:** Live metadata for the official STATPOP municipality population table
- **Producer:** Swiss Federal Statistical Office (FSO/OFS/BFS)
- **Exact URL:** https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-0102010000_101/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T23:13:51.846350+00:00.
- **Variables:** statpop_table_schema|municipality_bfs_id
- **Transformations:** Dimension codes and 2,115 municipality code-label pairs reviewed exactly
- **Coverage:** municipality; metadata snapshot; 2010 to 2025.
- **Limitations:** Cached metadata states 31 December reference date and commune geography state 6 April 2025
- **Local raw file:** `data_external/source_evidence/BFS_STATPOP_METADATA_20260921T231351Z.json`.

## CHATEAU_DOEX_LA_BRAYE_2018 — Official destination or municipal scope page

- **Contents and relevance:** Official municipal preavis 17/2018 documenting the La Braye lift assets and the Télé-Château-d'Oex operator lineage
- **Producer:** Commune de Château-d'Oex
- **Exact URL:** https://www.chateaudoex-admin.ch/_doc/1790818
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T22:04:14.866711+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/CHATEAU_DOEX_LA_BRAYE_2018_20260921T220414Z.pdf`.

## DERIVED_ACCESSIBILITY_CONTEXT — Path C straight-line population accessibility context

- **Contents and relevance:** Qualified Swiss straight-line population context for every linked Path C lift cluster
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned deterministic Python transformation of STATPOP 2025 and swissBOUNDARIES3D 2026; unknown date.
- **Variables:** distance_to_population_threshold_municipality|resident_population_within_straight_line_radius|boundary_bridge
- **Transformations:** Aggregate seven superseded STATPOP identifiers through five official mutations; use polygon representative points; calculate EPSG:2056 distances and population sums at versioned thresholds and radii
- **Coverage:** current Swiss municipality and linked lift cluster; 2025 population aligned to 2026-01-01 boundaries; 2025-12-31 to 2026-01-01.
- **Limitations:** Not travel time, a population raster, a destination catchment or a cross-border market; municipality population is collapsed to one interior point
- **Local raw file:** `config/path_c_analysis.json|config/municipality_boundary_bridge_2025_2026.csv`.

## DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT — Donor competing-pass and local-shock audit

- **Contents and relevance:** Complete-roster nonmembership and page-referenced competing-pass/local-tourism-shock review for shortlisted donor pairs beyond 50 km from the resolved Magic network
- **Producer:** Thesis research; constituent official source IDs retained per row
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned manual evidence config joined by exact treatment, donor BFS and anchor key; unknown date.
- **Variables:** magic_roster_source_id|historical_magic_nonmembership_status|competing_pass_at_anchor_status|local_tourism_shock_status|final_manual_review_decision|remaining_deep_audit_candidate
- **Transformations:** Exact-key completeness check for seven beyond-50-km pairs; complete annual Magic roster label review; network-distance priorities combined with reviewed external-shock evidence
- **Coverage:** shortlisted treatment-donor pair; treatment-specific anchor and surrounding pass season; 2017-11 to 2023-05.
- **Limitations:** Roster absence is documented for reviewed station/place labels, not corporate-register affiliates; all seven remote pairs have a contemporaneous local shock and are excluded
- **Local raw file:** `config/donor_external_shock_review.json`.

## DERIVED_DONOR_NETWORK_SPILLOVER_AUDIT — Donor network-wide spillover audit

- **Contents and relevance:** Network-wide proximity sensitivity from apparent donor resort points to all resolved Magic Pass resort points
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned Python transformation of resort points, current/historical resolved Magic links and donor screens; unknown date.
- **Variables:** minimum_distance_to_resolved_magic_km|network_distance_band|network_spillover_cleared_30km
- **Transformations:** Minimum haversine distance from any supplied donor-municipality resort point to any historically/currently resolved Magic resort point
- **Coverage:** apparent donor municipality and treatment-donor shortlist pair; historical resolved links plus current snapshot; 2017/2018 to 2026 current snapshot.
- **Limitations:** Resolved network is a lower bound; resort points are not catchments; distance does not prove spillovers or their absence
- **Local raw file:** `not cached / not applicable`.

## DERIVED_DONOR_PRETREND_SCREEN — Donor pre-trend comparability screen

- **Contents and relevance:** Treatment-specific descriptive prioritisation of provisional donor municipalities using 36 pre-anchor months
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned Python transformation of checksum-traceable hotel, capacity, resort-directory and control-screen inputs; unknown date.
- **Variables:** pretrend_comparability|descriptive_comparability_score|comparability_rank
- **Transformations:** Log1p outcome comparisons; calendar-month-adjusted linear trend; seasonal profile and standardized-shape diagnostics; equal-weight within-treatment percentile score
- **Coverage:** reviewed treatment and provisional donor municipality pair; 36-month pre-anchor window; treatment-specific to month before treatment-specific analytical anchor.
- **Limitations:** Heuristic rank only; current directory structure may differ historically; historical non-membership, spillovers, accessibility, confounding, balance and parallel trends are not approved
- **Local raw file:** `not cached / not applicable`.

## DERIVED_MAGIC_ANNUAL_OFFERING — Annual Magic Pass season-offering review

- **Contents and relevance:** Page-referenced annual winter versus summer-winter access classification for reviewed destination units
- **Producer:** Thesis research; constituent annual Magic Pass source IDs retained per row
- **Exact URL:** Not documented.
- **Access and retrieval date:** Visual annual-publication review encoded in versioned metadata/magic_pass_season_offering_evidence.json; unknown date.
- **Variables:** winter_access_status|summer_access_status|published_summer_winter_labels|published_winter_only_labels
- **Transformations:** Join page-referenced annual offering observations to the membership-status grid without filling seasons lacking individual modality evidence
- **Coverage:** reviewed destination unit with published component labels retained; annual pass season; 2017/2018 to 2025/2026.
- **Limitations:** Summer access is not daily operation, equal component coverage, tourism exposure, or a causal treatment; unverified seasons remain unknown
- **Local raw file:** `metadata/magic_pass_season_offering_evidence.json`.

## DERIVED_MAGIC_SCOPE_REVIEW — Unmatched Magic Pass scope review

- **Contents and relevance:** Reviewed classification of unmatched historical entry labels and explicitly non-equivalent links to supplied resort listings
- **Producer:** Thesis research; constituent source IDs retained per row
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned config/unmatched_magic_scope_review.json plus cached official sources and supplied directory; unknown date.
- **Variables:** unmatched_entry_classification|non_equivalent_scope_relations|precautionary_donor_exclusions
- **Transformations:** Exact reviewed label lookup; expand many-to-many relation rows; deduplicate linked listing IDs for precautionary donor exclusions
- **Coverage:** official entry label; listing relation; point municipality risk; historical entry event and current scope review kept separate; 2017/2018 to 2025/2026.
- **Limitations:** Not identity equivalence or causal exposure; foreign destinations can create spillovers; a documented destination absent from the supplied directory is a coverage gap, not a non-member
- **Local raw file:** `config/unmatched_magic_scope_review.json`.

## DERIVED_MULTI_SOURCE — Reproducible local transformations

- **Contents and relevance:** Project-generated fields combining multiple registered sources
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** versioned Python scripts; unknown date.
- **Variables:** derived analytical fields
- **Transformations:** See formula and script references in data dictionary
- **Coverage:** mixed; mixed; ? to ?.
- **Limitations:** Not an external source; lineage remains in source_ids and formulas
- **Local raw file:** `not cached / not applicable`.

## DERIVED_PATH_C_AGGREGATION_SENSITIVITY — Path C aggregation sensitivity

- **Contents and relevance:** Min/median/max within-cluster aggregation robustness audit for every apparent Path C candidate
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Deterministic rebuild under three predeclared aggregation rules; unknown date.
- **Variables:** aggregation rule|segment stability|analogue stability|OOD stability|opportunity-signal range
- **Transformations:** Repeat segmentation and nearest-analogue construction under within-cluster minimum, median and maximum structural features; compare assignments, neighbours, OOD categories and descriptive signal
- **Coverage:** existing lift cluster with supplied resort listings; undated cross-sectional directory snapshot; ? to ?.
- **Limitations:** Aggregation rules probe listing semantics, not causal truth or predictive validity; exact analogue assignments and OOD flags are not invariant
- **Local raw file:** `config/path_c_analysis.json`.

## DERIVED_PATH_C_DECISION_SUPPORT — Magic Pass exploratory decision-support prototype

- **Contents and relevance:** Dashboard-ready exploratory Path C export retaining separate opportunity, vulnerability, support, quality and qualified context dimensions
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned merge of Path C feature, segment and analogue outputs; unknown date.
- **Variables:** opportunity_signal_percentile|snow_vulnerability_percentile|comparability|network context|qualified tourism and population context|unapproved strategic-need fields
- **Transformations:** One-to-one merge by stable cluster_id; opportunity and snow percentiles retained separately; min/median/max aggregation sensitivity, qualified point-container tourism context and Swiss straight-line population context appended; no composite score
- **Coverage:** existing lift cluster with supplied resort listings; mixed descriptive snapshot; lineage retained by field; ? to ?.
- **Limitations:** Catchment-level tourism dependence and network travel-time accessibility remain missing; qualified context is not an approved destination scope; foreign population is omitted; blank uplift fields are intentional
- **Local raw file:** `config/path_c_analysis.json`.

## DERIVED_PATH_C_FEATURE_MATRIX — Path C resort-cluster feature matrix

- **Contents and relevance:** Least-duplicated available cross-sectional feature table for lift clusters linked to supplied resort listings
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned aggregation configured in config/path_c_analysis.json; unknown date.
- **Variables:** cluster-level structural features|Magic evidence status|snow vulnerability|data quality
- **Transformations:** Median/min/max aggregation across assigned listings; exact current/history/scope evidence flags; no hotel outcome used as a feature
- **Coverage:** existing lift cluster with at least one supplied resort listing; undated cross-sectional directory snapshot; ? to ?.
- **Limitations:** Existing clusters are not certified independent destinations; Bergfex observation date is unknown; point municipality is not tourism exposure
- **Local raw file:** `config/path_c_analysis.json`.

## DERIVED_PATH_C_SEGMENTATION_ANALOGUES — Path C segmentation and analogue analysis

- **Contents and relevance:** Stability-checked structural segmentation and nearest-neighbour analogue diagnostics for exploratory Path C
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Deterministic NumPy implementation using versioned config and derived feature tables; unknown date.
- **Variables:** segment_id|silhouette|bootstrap_ari|nearest Magic analogues|reviewed-treated analogue signal|OOD flag
- **Transformations:** Z-score altitude and log1p size features; select k by silhouette after size/stability gates; report three nearest reference entities and empirical leave-one-out OOD support
- **Coverage:** linked lift cluster or reviewed treated destination; current structural snapshot plus unadjusted adjacent 24-month diagnostics; ? to ?.
- **Limitations:** Analogue changes are unadjusted, discrete and not counterfactual predictions; snow is kept outside structural similarity
- **Local raw file:** `config/path_c_analysis.json`.

## DERIVED_REVIEWED_DESTINATION_PANEL — Reviewed destination-month panel

- **Contents and relevance:** Monthly destination outcomes, hotel capacity, qualified snow/weather proxies, and diagnostic treatment coding aggregated across reviewed scopes
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** versioned Python transformation; unknown date.
- **Variables:** reviewed_destination_month_outcomes|hotel_capacity|snow_proxy|weather_proxy|diagnostic_membership_status
- **Transformations:** Additive municipality outcome/capacity totals; complete-case multi-station snow/weather proxy means; official occupancy percentages retained only for single-municipality units; entry carried forward only as a flagged diagnostic assumption
- **Coverage:** reviewed destination unit; monthly; 2013-01 to 2026-12 grid; 2026-03 latest observed outcome.
- **Limitations:** No row is causal-ready; SLF and MeteoSwiss proxies are not direct piste observations; treatment intensity, controls, spillovers, and other time-varying confounders remain unresolved
- **Local raw file:** `not cached / not applicable`.

## DERIVED_SNOW_STATION_SENSITIVITY — SLF alternative-station sensitivity

- **Contents and relevance:** Selected-versus-next-nearest eligible SLF station robustness diagnostics for reviewed resort components
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned Python transformation of checksum-traceable SLF station metadata and station-winter aggregates; unknown date.
- **Variables:** alternative_station_agreement|winter_mean_depth_correlation|relative_mean_absolute_depth_difference|trend_direction_agrees
- **Transformations:** Replace nearest eligible station with next-nearest distinct station under the same 80% longitudinal gate; compare common usable winters
- **Coverage:** reviewed resort component and two external SLF stations; November-April winter seasons; 2013/2014 to 2025/2026.
- **Limitations:** Neither station is a piste observation; alternative is not elevation/aspect optimised; gridded independent-source sensitivity remains pending
- **Local raw file:** `not cached / not applicable`.

## DERIVED_TEMPORAL_CONTROLS — Temporal control calendar

- **Contents and relevance:** Deterministic month-level calendar and broad COVID sensitivity controls
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned deterministic Python transformation from Gregorian calendar dates and config/temporal_controls.json; unknown date.
- **Variables:** calendar_quarter|magic_pass_season|winter_month|summer_month|christmas_new_year_peak_month|easter_month|covid_sensitivity_month
- **Transformations:** May-April pass-season label; November-April winter partition; Gregorian Easter calculation; analyst-defined March 2020-April 2022 sensitivity interval
- **Coverage:** all reviewed destinations; no geographic variation; monthly; 2013-01 to 2026-12.
- **Limitations:** Does not encode canton-specific school holidays or a legal COVID-restriction chronology; the broad COVID flag is for sensitivity analysis only
- **Local raw file:** `config/temporal_controls.json`.

## DERIVED_TOURISM_DEPENDENCE_CONTEXT — Path C point-container tourism context

- **Contents and relevance:** Qualified tourism-intensity context for municipalities containing supplied resort listing points
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned exact-BFS merge of STATPOP 2025, HESTA 2025 and resort point-container crosswalk; unknown date.
- **Variables:** overnights_per_resident|hotel_beds_per_1000_residents|point-container tourism context
- **Transformations:** Require all 12 HESTA months; sum annual hotel nights; average monthly supply; divide by resident population; aggregate unique point containers only when every municipality is complete
- **Coverage:** municipality and linked lift cluster point-container set; 2025 annual context; 2025-01-01 to 2025-12-31.
- **Limitations:** Point containment is not an approved tourism catchment or exposure mapping; hotel statistics omit non-hotel accommodation
- **Local raw file:** `data_processed/resort_point_municipality.csv`.

## DERIVED_TREATMENT_DISTANCE_GRADIENT — Treatment municipality distance-gradient diagnostic

- **Contents and relevance:** Same-treated-destination comparison of hotel municipalities by distance to destination component resort points
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** Versioned Python transformation of swissBOUNDARIES3D, resort coordinates, reviewed treatment units and hotel outcomes; unknown date.
- **Variables:** representative_point_distance_to_destination_km|minimum_polygon_distance_to_destination_km|descriptive_near_minus_far_log_change
- **Transformations:** EPSG:2056 distances to the same destination's component points; 24-month pre/post municipal outcome summaries; within-destination distance rings and buffered near/far contrast
- **Coverage:** reviewed treated destination by hotel municipality; current distance snapshot plus treatment-specific adjacent 24-month windows; 2013 to 2026.
- **Limitations:** Current boundaries, representative points and adjacent windows do not identify exposure or causal effects; travel time and hotel coordinates unavailable
- **Local raw file:** `not cached / not applicable`.

## DESTINATION_SCOPE_OFFICIAL_SET — Destination scope evidence set

- **Contents and relevance:** Reviewed union of official municipality and lift-operator scope evidence
- **Producer:** Municipalities and official lift operators
- **Exact URL:** Not documented.
- **Access and retrieval date:** Derived from individually registered official pages and geo.admin.ch point containment; unknown date.
- **Variables:** destination_unit_scope|municipality_outcome_scope
- **Transformations:** Explicit inclusion/exclusion decisions and additive municipality outcome weights
- **Coverage:** reviewed destination and municipality; scope snapshot; ? to 2026.
- **Limitations:** Core-municipality proxies are labelled separately from complete observed municipal scope
- **Local raw file:** `not cached / not applicable`.

## DIABLERETS_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official operator page distinguishing the Les Diablerets/Meilleret sector from Glacier 3000, reached by shuttle from the bottom of the slopes
- **Producer:** Télé-Villars-Gryon-Diablerets SA
- **Exact URL:** https://www.tvgd.ch/en-US/diablerets/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T22:04:28.367940+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/DIABLERETS_SCOPE_OFFICIAL_20260921T220428Z.html`.

## ENGADIN_MOUNTAINS_ANNUAL_2017_18 — Engadin St. Moritz Mountains AG annual report 2017/18

- **Contents and relevance:** Official 2017/2018 annual report documenting Corviglia-Marguns restaurant changes, dynamic-pricing preparation and lift modernisation around the Anniviers anchor
- **Producer:** Engadin St. Moritz Mountains AG
- **Exact URL:** https://www.mountains.ch/fileadmin/user_upload/Bilddatenbank_HP/Organisation/Dokumente/Geschaeftsbericht_GV/Geschaeftsbericht_2017-2018_Engadin_St._Moritz_Mountains_AG.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:44:54.620851+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2017-11 to 2018-10.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/ENGADIN_MOUNTAINS_ANNUAL_2017_18_20260921T154454Z.pdf`.

## ENGADIN_MOUNTAINS_ANNUAL_2019_20 — Engadin St. Moritz Mountains AG annual report 2019/20

- **Contents and relevance:** Official 2019/2020 annual report documenting Celerina and Corviglia lift, piste and other investments around the Saas-Fee anchor
- **Producer:** Engadin St. Moritz Mountains AG
- **Exact URL:** https://mountains.ch/fileadmin/user_upload/Bilddatenbank_HP/Organisation/Dokumente/Geschaeftsbericht_GV/Geschaeftsbericht_2019_20_.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:44:55.961147+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2019-11 to 2020-10.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/ENGADIN_MOUNTAINS_ANNUAL_2019_20_20260921T154455Z.pdf`.

## EVOLENE_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official municipal evidence that Evolène, La Forclaz and Arolla belong to the same municipality
- **Producer:** Commune d'Evolène
- **Exact URL:** https://www.commune-evolene.ch/fr/villages-35.html
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:34.825822+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/EVOLENE_SCOPE_OFFICIAL_20260920T005534Z.html`.

## GEOADMIN_MUNICIPALITY_IDENTIFY — Municipal boundaries — current swissBOUNDARIES3D layer

- **Contents and relevance:** Current municipality polygon containing each supplied resort coordinate
- **Producer:** Federal Office of Topography swisstopo / geo.admin.ch
- **Exact URL:** https://docs.geo.admin.ch/access-data/identify-features.html
- **Access and retrieval date:** 271 rate-limited HTTP GET requests with immutable responses and SHA-256 sidecars; 2026-09-19T23:27:16.405897+00:00.
- **Variables:** point_municipality_bfs_id|point_municipality_name|point_municipality_canton
- **Transformations:** Selected the unique result marked is_current_jahr=true; no distance or fuzzy-name inference
- **Coverage:** point-in-current-municipality polygon; boundary snapshot; 2026-01-01 to 2026-01-01.
- **Limitations:** Coordinate containment is not a tourism catchment or municipal exposure weight
- **Local raw file:** `data_external/source_evidence/GEO_POINT_*.json`.

## GRAUBUENDENCARD_TRANSIT_2022_23 — graubündenCARD transport benefits 2022/23

- **Contents and relevance:** Official 2022/2023 graubündenCARD public-transport benefits list naming participating mountain-railway companies and locations
- **Producer:** Graubünden Ferien
- **Exact URL:** https://www.graubuenden.ch/sites/graubuenden/files/2022-05/grCARD_%C3%B6V_Leistungen.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:19:55.927551+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2022-11 to 2023-04.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/GRAUBUENDENCARD_TRANSIT_2022_23_20260921T151955Z.pdf`.

## GRENCHENBERG_OPERATOR_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official regional tourism page identifying Skilift Grenchenberg AG, its two lifts and Magic Pass integration
- **Producer:** Jurasonnenseite / Grenchen tourism
- **Exact URL:** https://jurasonnenseite.ch/erleben/auf-dem-berg/skilift
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T22:04:23.333867+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/GRENCHENBERG_OPERATOR_OFFICIAL_20260921T220423Z.html`.

## GR_MINSCHUNS_INVESTMENT_2019 — Graubünden government release on Minschuns investment

- **Contents and relevance:** Official 2019 government release documenting federal and cantonal funding for a new Minschuns gondola and snowmaking system, intended to replace difficult road access and support the planned La Sassa resort
- **Producer:** Kanton Graubuenden
- **Exact URL:** https://www.gr.ch/DE/Medien/Mitteilungen/MMStaka/2019/Seiten/2019112101.aspx
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:47:22.986147+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2019-11 to 2019-11.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/GR_MINSCHUNS_INVESTMENT_2019_20260921T154722Z.html`.

## GSTAAD_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official operator evidence for access points spanning Saanen, Rougemont, Zweisimmen and St. Stephan
- **Producer:** Bergbahnen Destination Gstaad AG
- **Exact URL:** https://bergbahnen-gstaad.ch/en/arrival-parking
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:49.309926+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/GSTAAD_SCOPE_OFFICIAL_20260920T005549Z.html`.

## KRONBERG_ANNUAL_2017 — Kronberg AG annual report 2017

- **Contents and relevance:** Official 2017 annual report for the tourism and cableway operator at Jakobsbad-Kronberg
- **Producer:** Kronberg AG
- **Exact URL:** https://kronberg.ch/unternehmen/aktionaere.html?_hash=XU5TA%2FffZUYVBDBMWIN%2FWDNF5O1dfE9i44s8GwhIZHk%3D&ctx=a%3A1%3A%7Bs%3A2%3A%22id%22%3Bi%3A8053%3B%7D&d=attachment&f=Gesch%C3%A4ftsbericht+2017.pdf&p=kronberg.ch%2Fmedia%2Faktionaere%2Fgeschaeftsberichte%2FGesch%C3%A4ftsbericht+2017.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:18:52.650090+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2017-01 to 2017-12.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/KRONBERG_ANNUAL_2017_20260921T151852Z.pdf`.

## KRONBERG_ANNUAL_2023 — Kronberg AG annual report 2023

- **Contents and relevance:** Official 2023 annual report documenting the independent year-round tourism business and winter investment decision at Jakobsbad-Kronberg
- **Producer:** Kronberg AG
- **Exact URL:** https://kronberg.ch/unternehmen/aktionaere.html?_hash=V%2F26lNWygBi2ya3rwmMKRRFnxKwshl7U9e8jWKlZjuY%3D&ctx=a%3A1%3A%7Bs%3A2%3A%22id%22%3Bi%3A8053%3B%7D&d=attachment&f=Gesch%C3%A4ftsbericht+2023.pdf&p=kronberg.ch%2Fmedia%2Faktionaere%2Fgeschaeftsberichte%2FGesch%C3%A4ftsbericht+2023.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:18:54.653153+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2023-01 to 2023-12.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/KRONBERG_ANNUAL_2023_20260921T151854Z.pdf`.

## LOCAL_03b4345dbe87 — stations_ski_assignations_clusters_gps_bergfex.csv

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/stations_ski_assignations_clusters_gps_bergfex.csv`.

## LOCAL_0f53d91bbb86 — bahnen-winter_2056.gpkg

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/bahnen-winter_2056.gpkg`.

## LOCAL_14a174ea6a94 — stations_ski_clusters_calibration_seuils_gps_bergfex.csv

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/stations_ski_clusters_calibration_seuils_gps_bergfex.csv`.

## LOCAL_430fe06a9598 — carte_communes_nuitees_croisees_provisoir_avec_stations_gps_bergfex.html

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/carte_communes_nuitees_croisees_provisoir_avec_stations_gps_bergfex.html`.

## LOCAL_4431c47c859d — bergfex_stations_ski_suisse_par_region.csv

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/bergfex_stations_ski_suisse_par_region.csv`.

## LOCAL_5c587073db3b — nuitée_commune_final.csv

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/nuitée_commune_final.csv`.

## LOCAL_5f838870add4 — stations_ski_clusters_gps_bergfex.geojson

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/stations_ski_clusters_gps_bergfex.geojson`.

## LOCAL_8b04208d016e — stations_ski_gps_bergfex_normalise.csv

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/stations_ski_gps_bergfex_normalise.csv`.

## LOCAL_9960a7d400b5 — carte_stations_ski_clusters_assignations_gps_bergfex.html

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/carte_stations_ski_clusters_assignations_gps_bergfex.html`.

## LOCAL_afb2b0d65a48 — position_gps_stations_ski.csv

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/position_gps_stations_ski.csv`.

## LOCAL_f3dccaa5c1ef — stations_ski_clusters_resume_gps_bergfex.csv

- **Contents and relevance:** Existing thesis input; upstream construction under audit
- **Producer:** UNKNOWN
- **Exact URL:** Not documented.
- **Access and retrieval date:** researcher-supplied local file; UNKNOWN.
- **Variables:** dataset
- **Transformations:** None documented.
- **Coverage:** unknown geography; unknown time resolution; ? to ?.
- **Limitations:** See reports/data_audit_details.json; upstream provenance requires verification
- **Local raw file:** `data_raw/stations_ski_clusters_resume_gps_bergfex.csv`.

## MAGIC_2017 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:21:36.251174+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2017 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2017_20260919T232136Z.pdf`.

## MAGIC_2018 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:21:46.699377+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2018/2019 to 2018/2019.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2018_20260919T232146Z.pdf`.

## MAGIC_2019 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:21:56.936424+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2019 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2019_20260919T232156Z.pdf`.

## MAGIC_2019_APRIL — Official April 2019 release with explicit 2019/2020 partner roster

- **Contents and relevance:** Official April 2019 release with explicit 2019/2020 partner roster
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/media/document/0/mp-cp-24avril-2019-fr-25.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T17:32:53.161428+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page/image-referenced visual/text review recorded in metadata/magic_pass_roster_evidence.json; positive seasonal evidence only
- **Coverage:** official ski destination; dated announcement / season; 2019/2020 to 2019/2020.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2019_APRIL_20260920T173253Z.pdf`.

## MAGIC_2020 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:23:50.233825+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2020/2021 to 2020/2021.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2020_20260919T232350Z.pdf`.

## MAGIC_2020_MAP — Official 2020/2021 Magic Pass network map distinguishing winter-only from summer-winter destinations

- **Contents and relevance:** Official 2020/2021 Magic Pass network map distinguishing winter-only from summer-winter destinations
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/media/image/0/stations_magic_pass_3.png
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T09:33:53.525860+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page/image-referenced visual/text review recorded in metadata/magic_pass_roster_evidence.json; positive seasonal evidence only
- **Coverage:** official ski destination; dated announcement / season; 2020/2021 to 2020/2021.
- **Limitations:** Official publisher-hosted dated image; winter, summer-winter, Glacier 3000 and baths symbols reviewed separately; absence not evidence of non-membership
- **Local raw file:** `data_external/source_evidence/MAGIC_2020_MAP_20260921T093353Z.png`.

## MAGIC_2021 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T09:09:47.167358+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Visual review of pp.3-4; page 3 incremental expansion is used for roster continuity, while aggregate 40-winter/21-summer counts are not used as individual modality evidence
- **Coverage:** official ski destination; dated announcement / season; 2021/2022 to 2021/2022.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2021_20260921T090947Z.pdf`.

## MAGIC_2021_APRIL — Official Magic Pass press material

- **Contents and relevance:** Official April 2021 follow-up release for the 2021/2022 pass
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T01:15:19.337900+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2021/2022 to 2021/2022.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2021_APRIL_20260920T011519Z.pdf`.

## MAGIC_2022 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:22:27.695130+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2022 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2022_20260919T232227Z.pdf`.

## MAGIC_2022_DOSSIER — Official Magic Pass press material

- **Contents and relevance:** Official full press dossier for the 2022/2023 pass
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T01:16:51.624040+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2022/2023 to 2022/2023.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2022_DOSSIER_20260920T011651Z.pdf`.

## MAGIC_2023 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:22:38.145606+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2023/2024 to 2023/2024.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2023_20260919T232238Z.pdf`.

## MAGIC_2024 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:24:11.201676+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2024 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2024_20260919T232411Z.pdf`.

## MAGIC_2024_MAP — Magic Pass branded seasonal map explicitly valid 2024-05-01 to 2025-04-30; partner-hosted original document

- **Contents and relevance:** Magic Pass branded seasonal map explicitly valid 2024-05-01 to 2025-04-30; partner-hosted original document
- **Producer:** Magic Mountains Cooperation; map distributed by Raiffeisen
- **Exact URL:** https://www.raiffeisen.ch/content/dam/www/rch/pdf/produkte/mitglieder/de/magic-pass-de.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T17:33:03.755072+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page/image-referenced visual/text review recorded in metadata/magic_pass_roster_evidence.json; positive seasonal evidence only
- **Coverage:** official ski destination; dated announcement / season; 2024/2025 to 2024/2025.
- **Limitations:** Magic Pass branded dated map distributed by Raiffeisen; not publisher-hosted; visible symbols and printed validity reviewed; absence not evidence of non-membership
- **Local raw file:** `data_external/source_evidence/MAGIC_2024_MAP_20260920T173303Z.pdf`.

## MAGIC_2025 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:22:58.692358+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2025/2026 to 2025/2026.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2025_20260919T232258Z.pdf`.

## MAGIC_2026 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:56:13.071390+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2026 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_2026_20260920T005613Z.pdf`.

## MAGIC_CURRENT_MAP — Official current destination map

- **Contents and relevance:** Current destination list; not historical entry evidence
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/stations/map
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:17:26.501601+00:00.
- **Variables:** current_magic_destination
- **Transformations:** Embedded official destination JSON extracted from cached HTML
- **Coverage:** official ski destination; retrieval-date snapshot; ? to 2026.
- **Limitations:** Current snapshot is not historical evidence
- **Local raw file:** `data_external/source_evidence/MAGIC_CURRENT_MAP_20260919T231726Z.html`.

## MAGIC_FRIBOURG_2021_WINTER — Official tourism release dated 2021-12-01 confirming the seven named Fribourg ski stations participate in Magic Pass for winter 2021/2022

- **Contents and relevance:** Official tourism release dated 2021-12-01 confirming the seven named Fribourg ski stations participate in Magic Pass for winter 2021/2022
- **Producer:** Fribourg Region
- **Exact URL:** https://fribourg.ch/wp-content/uploads/2021/12/20211201_Fribourg-Region_hiver-2021-22_CP.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T17:34:44.091464+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page/image-referenced visual/text review recorded in metadata/magic_pass_roster_evidence.json; positive seasonal evidence only
- **Coverage:** official ski destination; dated announcement / season; 2021/2022 to 2021/2022.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_FRIBOURG_2021_WINTER_20260920T173444Z.pdf`.

## MAGIC_OFFICIAL_EVIDENCE_SET — Documented Magic Pass event and seasonal evidence set

- **Contents and relevance:** Union of dated Magic Pass documents, archive notices, operator tariffs and official tourism confirmation; seasonal map distributor recorded separately
- **Producer:** Magic Mountains Cooperation; named ski operators and official tourism organisations
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** Event sources in metadata/magic_pass_entry_evidence.json; seasonal source IDs and exact pages in metadata/magic_pass_roster_evidence.json; unknown date.
- **Variables:** membership_event_history|seasonal_membership_evidence
- **Transformations:** Manual event transcription; reviewed aliases and unique normalised labels create candidate links
- **Coverage:** official ski destination with candidate resort link; season/event; 2017/2018 to 2025/2026.
- **Limitations:** Continuity is complete for the 14 reviewed units only; unresolved destinations outside that reviewed set remain
- **Local raw file:** `not cached / not applicable`.

## MAGIC_PLEIADES_2020_TARIFF — Official operator winter 2020/2021 tariff explicitly confirming Magic Pass validity at Les Pleiades

- **Contents and relevance:** Official operator winter 2020/2021 tariff explicitly confirming Magic Pass validity at Les Pleiades
- **Producer:** Cooperative des Pleiades
- **Exact URL:** https://lespleiades.ch/documents/CP21_tarifs_MP_20-21.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T17:33:05.072337+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page/image-referenced visual/text review recorded in metadata/magic_pass_roster_evidence.json; positive seasonal evidence only
- **Coverage:** official ski destination; dated announcement / season; 2020/2021 to 2020/2021.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_PLEIADES_2020_TARIFF_20260920T173305Z.pdf`.

## MAGIC_PLEIADES_2021_TARIFF — Official operator winter 2021/2022 tariff explicitly confirming Magic Pass validity at Les Pleiades

- **Contents and relevance:** Official operator winter 2021/2022 tariff explicitly confirming Magic Pass validity at Les Pleiades
- **Producer:** Cooperative des Pleiades
- **Exact URL:** https://lespleiades.ch/documents/CP22_tarifs_MP_21-22.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T17:34:33.826817+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page/image-referenced visual/text review recorded in metadata/magic_pass_roster_evidence.json; positive seasonal evidence only
- **Coverage:** official ski destination; dated announcement / season; 2021/2022 to 2021/2022.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_PLEIADES_2021_TARIFF_20260920T173433Z.pdf`.

## MAGIC_PRESS_ARCHIVE — Official Magic Pass press material

- **Contents and relevance:** Official dated membership announcements and exit notices
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:17:15.917509+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2017 to 2026.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access
- **Local raw file:** `data_external/source_evidence/MAGIC_PRESS_ARCHIVE_20260919T231715Z.html`.

## MAYENS_CONTHEY_OPERATOR_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official municipal directory entry for the Société coopérative, Téléskis des Mayens de Conthey
- **Producer:** Commune de Conthey
- **Exact URL:** https://www.conthey.ch/fr/annuaire/societe-cooperative-teleskis-des-mayens-764/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T22:04:16.998727+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/MAYENS_CONTHEY_OPERATOR_OFFICIAL_20260921T220416Z.html`.

## MEIRINGEN_HASLIBERG_MAGIC_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official operator evidence for Magic Pass membership from 1 May 2025
- **Producer:** Bergbahnen Meiringen-Hasliberg AG
- **Exact URL:** https://en.meiringen-hasliberg.ch/Infos/magic-pass
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:52.206162+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/MEIRINGEN_HASLIBERG_MAGIC_OFFICIAL_20260920T005552Z.html`.

## MEIRINGEN_HASLIBERG_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official operator evidence for lift access in both Hasliberg and Meiringen
- **Producer:** Bergbahnen Meiringen-Hasliberg AG
- **Exact URL:** https://en.meiringen-hasliberg.ch/Infos/anreise
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:50.713606+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/MEIRINGEN_HASLIBERG_SCOPE_OFFICIAL_20260920T005550Z.html`.

## METEOSWISS_SMN_COLLECTION — SwissMetNet FSDI STAC collection metadata

- **Contents and relevance:** Official FSDI STAC collection metadata and asset links for SwissMetNet
- **Producer:** Federal Office of Meteorology and Climatology MeteoSwiss
- **Exact URL:** https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T09:14:30.310962+00:00.
- **Variables:** collection_metadata|asset_templates|licence_links
- **Transformations:** Cached and used for parameter definitions, station eligibility, coordinates, and exact official asset discovery
- **Coverage:** collection metadata; retrieval snapshot; ? to 2026.
- **Limitations:** Official metadata snapshot; source catalogue can be updated after retrieval
- **Local raw file:** `data_external/source_evidence/METEOSWISS_SMN_COLLECTION_20260920T091430Z.json`.

## METEOSWISS_SMN_DAILY_SELECTED — SwissMetNet selected daily historical and recent station files

- **Contents and relevance:** Official daily mean/minimum/maximum air temperature and 06:00-to-06:00 UTC precipitation for seven selected SwissMetNet stations
- **Producer:** Federal Office of Meteorology and Climatology MeteoSwiss
- **Exact URL:** https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- **Access and retrieval date:** HTTP GET of seven historical and seven recent static CSV files; immutable responses and SHA-256 sidecars; 2026-09-20T09:19:30.969388+00:00.
- **Variables:** tre200d0|tre200dn|tre200dx|rre150d0
- **Transformations:** Exact historical/recent concatenation; monthly aggregation; 80% coverage gate; station-specific 2013-2025 calendar-month normals; nearest eligible-station crosswalk; no imputation
- **Coverage:** SwissMetNet point station used as regional resort proxy; daily source; monthly analytical aggregation; 2013-01-01 analysis window to 2026-03-31 analysis window.
- **Limitations:** Two station-months fail precipitation coverage and remain missing; precipitation uses 06:00 UTC to 06:00 UTC next day; regional stations do not directly represent pistes
- **Local raw file:** `data_external/source_evidence/METEOSWISS_SMN_DAILY_*.csv`.

## METEOSWISS_SMN_DOCUMENTATION — SwissMetNet Open Data documentation

- **Contents and relevance:** Official SwissMetNet data structure, access, parameter, station and licence documentation
- **Producer:** Federal Office of Meteorology and Climatology MeteoSwiss
- **Exact URL:** https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T09:14:28.151525+00:00.
- **Variables:** data_structure|access|licence|aggregation_guidance
- **Transformations:** Cached and used for parameter definitions, station eligibility, coordinates, and exact official asset discovery
- **Coverage:** documentation; retrieval snapshot; ? to 2026.
- **Limitations:** Official metadata snapshot; source catalogue can be updated after retrieval
- **Local raw file:** `data_external/source_evidence/METEOSWISS_SMN_DOCUMENTATION_20260920T091428Z.html`.

## METEOSWISS_SMN_INVENTORY — SwissMetNet station-parameter inventory

- **Contents and relevance:** Official SwissMetNet station-parameter measurement start and end inventory
- **Producer:** Federal Office of Meteorology and Climatology MeteoSwiss
- **Exact URL:** https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T09:14:34.206029+00:00.
- **Variables:** station_abbr|parameter_shortname|data_since|data_till|owner
- **Transformations:** Cached and used for parameter definitions, station eligibility, coordinates, and exact official asset discovery
- **Coverage:** station-parameter inventory; retrieval snapshot; ? to 2026.
- **Limitations:** Official metadata snapshot; source catalogue can be updated after retrieval
- **Local raw file:** `data_external/source_evidence/METEOSWISS_SMN_INVENTORY_20260920T091434Z.csv`.

## METEOSWISS_SMN_ITEMS — SwissMetNet STAC station-item response

- **Contents and relevance:** Official SwissMetNet STAC station items and downloadable data assets
- **Producer:** Federal Office of Meteorology and Climatology MeteoSwiss
- **Exact URL:** https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T09:15:57.136217+00:00.
- **Variables:** station_items|daily_asset_links
- **Transformations:** Cached and used for parameter definitions, station eligibility, coordinates, and exact official asset discovery
- **Coverage:** station asset catalogue snapshot; retrieval snapshot; ? to 2026.
- **Limitations:** The cached STAC item response is a discovery snapshot; exact selected asset URLs and checksums are recorded separately
- **Local raw file:** `data_external/source_evidence/METEOSWISS_SMN_ITEMS_20260920T091557Z.json`.

## METEOSWISS_SMN_PARAMETERS — SwissMetNet parameter catalogue

- **Contents and relevance:** Official SwissMetNet parameter identifiers, definitions, aggregation intervals and units
- **Producer:** Federal Office of Meteorology and Climatology MeteoSwiss
- **Exact URL:** https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T09:14:31.705550+00:00.
- **Variables:** parameter_shortname|description|granularity|unit
- **Transformations:** Cached and used for parameter definitions, station eligibility, coordinates, and exact official asset discovery
- **Coverage:** parameter metadata; retrieval snapshot; ? to 2026.
- **Limitations:** Official metadata snapshot; source catalogue can be updated after retrieval
- **Local raw file:** `data_external/source_evidence/METEOSWISS_SMN_PARAMETERS_20260920T091431Z.csv`.

## METEOSWISS_SMN_STATIONS — SwissMetNet station catalogue

- **Contents and relevance:** Official SwissMetNet station identifiers, coordinates, elevations and metadata
- **Producer:** Federal Office of Meteorology and Climatology MeteoSwiss
- **Exact URL:** https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T09:14:32.959152+00:00.
- **Variables:** station_abbr|station_name|coordinates|elevation|station_type
- **Transformations:** Cached and used for parameter definitions, station eligibility, coordinates, and exact official asset discovery
- **Coverage:** point station; retrieval snapshot; ? to 2026.
- **Limitations:** Official metadata snapshot; source catalogue can be updated after retrieval
- **Local raw file:** `data_external/source_evidence/METEOSWISS_SMN_STATIONS_20260920T091432Z.csv`.

## NIEDERHORN_MAGIC_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official Niederhorn Magic Pass participation and conditional Beatenbucht-Beatenberg route validity; current scope, not entry-date proof
- **Producer:** Niederhornbahn AG
- **Exact URL:** https://www.niederhorn.ch/en/special-tickets/magic-pass
- **Access and retrieval date:** official URL verified; local retrieval pending; unknown date.
- **Variables:** destination_scope_evidence
- **Transformations:** Not used; local retrieval unavailable
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `not cached / not applicable`.

## REICHENBACH_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official municipal evidence that Faltschen and Kiental are localities in Reichenbach im Kandertal
- **Producer:** Gemeinde Reichenbach im Kandertal
- **Exact URL:** https://www.reichenbach.ch/de/gemeinde/reichenbach/zahlen-und-fakten/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:36.148672+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/REICHENBACH_SCOPE_OFFICIAL_20260920T005536Z.html`.

## SAINTE_CROIX_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official operator page for the Sainte-Croix / Les Rasses ski domain
- **Producer:** Ski Lift Les Rasses SA
- **Exact URL:** https://www.ski-vaud.ch/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:39.094372+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/SAINTE_CROIX_SCOPE_OFFICIAL_20260920T005539Z.html`.

## SAMNAUN_VISNITZBAHN_HISTORY — Silvrettaseilbahn AG history of the Visnitzbahn replacement

- **Contents and relevance:** Official operator history documenting replacement of Samnaun's Visnitz chairlift in 2019 and the new lift's capacity increase
- **Producer:** Silvrettaseilbahn AG
- **Exact URL:** https://www.ischgl.com/de/silvrettaseilbahnag/winter/bergbahnen-ueberblick/visnitzbahn
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:44:59.056951+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2019-01 to 2019-12.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/SAMNAUN_VISNITZBAHN_HISTORY_20260921T154459Z.html`.

## SLF_DATA_SERVICE — SLF data service terms and access documentation

- **Contents and relevance:** Official scope, access, licence, attribution, and quality conditions for SLF snow data
- **Producer:** WSL Institute for Snow and Avalanche Research SLF
- **Exact URL:** https://www.slf.ch/en/services-and-products/slf-data-service/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T08:55:53.205098+00:00.
- **Variables:** licence|attribution|data_quality_conditions
- **Transformations:** Cached and used for documentation or exact station metadata
- **Coverage:** documentation; retrieval snapshot; ? to 2026.
- **Limitations:** CC BY 4.0; SLF attribution and DOI are required; some source data are raw and not regularly corrected
- **Local raw file:** `data_external/source_evidence/SLF_DATA_SERVICE_20260920T085553Z.html`.

## SLF_IMIS_DAILY_INDEX — SLF station-level daily snow file directory

- **Contents and relevance:** Official directory of station-level daily snow CSV files
- **Producer:** WSL Institute for Snow and Avalanche Research SLF
- **Exact URL:** https://www.slf.ch/en/services-and-products/slf-data-service/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T08:55:57.098632+00:00.
- **Variables:** station_file_inventory
- **Transformations:** Cached and used for documentation or exact station metadata
- **Coverage:** file inventory; retrieval snapshot; ? to 2026.
- **Limitations:** Directory snapshot supports file-level audit; consolidated file is used for processing
- **Local raw file:** `data_external/source_evidence/SLF_IMIS_DAILY_INDEX_20260920T085557Z.html`.

## SLF_IMIS_DAILY_SNOW — SLF IMIS historical daily snow values

- **Contents and relevance:** Official historical daily IMIS snow-depth and modelled new-snow observations
- **Producer:** WSL Institute for Snow and Avalanche Research SLF
- **Exact URL:** https://www.slf.ch/en/services-and-products/slf-data-service/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T08:57:32.484947+00:00.
- **Variables:** snow_depth_cm|modeled_new_snow_cm
- **Transformations:** Physical nonnegative validation; monthly and November-April aggregation; 80% coverage gates; nearest eligible-station proxy with distance/elevation diagnostics
- **Coverage:** mountain weather station; daily; 1992-10-01 to 2026-09-13.
- **Limitations:** Negative snow depths are physically invalid and remain raw but missing in derived values; no imputation; station proxies are not direct piste measurements
- **Local raw file:** `data_external/source_evidence/SLF_IMIS_DAILY_SNOW_20260920T085732Z.csv`.

## SLF_IMIS_README — SLF historical measurement-data documentation

- **Contents and relevance:** Official documentation for the historical SLF measurement-data archive
- **Producer:** WSL Institute for Snow and Avalanche Research SLF
- **Exact URL:** https://www.slf.ch/en/services-and-products/slf-data-service/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T08:55:54.645354+00:00.
- **Variables:** HS_definition|HN_1D_definition|units|aggregation_time
- **Transformations:** Cached and used for documentation or exact station metadata
- **Coverage:** station measurement documentation; archive documentation snapshot; ? to 2026.
- **Limitations:** Daily HS is the 24-hour median at 06:00 UTC; HN_1D is modelled by SNOWPACK
- **Local raw file:** `data_external/source_evidence/SLF_IMIS_README_20260920T085554Z.md`.

## SLF_IMIS_STATIONS — SLF IMIS station catalogue

- **Contents and relevance:** Official IMIS station catalogue with location and elevation metadata
- **Producer:** WSL Institute for Snow and Avalanche Research SLF
- **Exact URL:** https://www.slf.ch/en/services-and-products/slf-data-service/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T08:55:55.917544+00:00.
- **Variables:** station_code|label|longitude|latitude|elevation|station_type|active
- **Transformations:** Cached and used for documentation or exact station metadata
- **Coverage:** point station; station metadata snapshot; ? to 2026.
- **Limitations:** Station locations are avalanche-monitoring sites and not ski-slope observations
- **Local raw file:** `data_external/source_evidence/SLF_IMIS_STATIONS_20260920T085555Z.csv`.

## SPLUEGEN_TAMBO_ANNUAL_2023_24 — Bergbahnen Splügen-Tambo AG annual report 2023/24

- **Contents and relevance:** Official 2023/2024 annual report documenting the new children lift, snowmaking changes, management changes and large visitor/revenue increase after the Bumbach anchor
- **Producer:** Bergbahnen Spluegen-Tambo AG
- **Exact URL:** https://storage.tramino.net/spluegen/1615535/gb-bbst-2024-deu-5-es-v1.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T15:46:22.543832+00:00.
- **Variables:** competing_pass_environment|operator_investment_and_tourism_shock_evidence
- **Transformations:** Page-referenced manual review; source qualification and unresolved exactness retained
- **Coverage:** regional pass market or reviewed donor operator; annual report or winter-season publication; 2023-05 to 2024-04.
- **Limitations:** Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved
- **Local raw file:** `data_external/source_evidence/SPLUEGEN_TAMBO_ANNUAL_2023_24_20260921T154622Z.pdf`.

## SWISSTOPO_BOUNDARIES_2026 — swissBOUNDARIES3D 2026-01

- **Contents and relevance:** Official 2026 municipality polygons used for distance diagnostics and qualified population accessibility context
- **Producer:** Federal Office of Topography swisstopo
- **Exact URL:** https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d
- **Access and retrieval date:** Configured HTTPS download with immutable ZIP, SHA-256 sidecar and collection log; 2026-09-21T14:53:10.749354+00:00.
- **Variables:** municipality_geometry|municipality_bfs_id|municipality_area_ha_2026|municipality_representative_point
- **Transformations:** Checksum verification; GeoPackage extraction; representative point, centroid and polygon-to-resort distance in EPSG:2056; official 2025 population aligned through reviewed 2026 mutations
- **Coverage:** Swiss political municipality polygon; boundary snapshot; 2026-01-01 to 2026-01-01.
- **Limitations:** Current geometry is not historical harmonisation; representative points are neither population centroids nor transport nodes
- **Local raw file:** `data_external/source_evidence/SWISSTOPO_BOUNDARIES_2026_20260921T145310Z.zip`.

## VALLEE_JOUX_SKI_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Tourism article distinguishing the ski areas of Le Brassus, L Orient, L Abbaye and Dent de Vaulion; regional scope is broader than the three historical entry labels
- **Producer:** Vallee de Joux tourism
- **Exact URL:** https://www.valleedejoux.ch/2022/01/04/le-ski-alpin-a-la-vallee/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T19:28:18.078623+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/VALLEE_JOUX_SKI_SCOPE_OFFICIAL_20260920T192818Z.html`.

## VILLARS_GRYON_SCOPE_OFFICIAL — Official destination or municipal scope page

- **Contents and relevance:** Official operator evidence that Villars, Gryon and Les Diablerets form one connected ski domain
- **Producer:** Télé-Villars-Gryon-Diablerets SA
- **Exact URL:** https://www.tvgd.ch/ski/
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:55:37.624544+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/treatment_destination_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/VILLARS_GRYON_SCOPE_OFFICIAL_20260920T005537Z.html`.

## WILERALLMI_ANNUAL_2023_24 — Official destination or municipal scope page

- **Contents and relevance:** Official 2023/2024 annual report establishing Wilerallmi as a separately operated Sigriswil ski destination
- **Producer:** Skilift Wilerallmi Sigriswil AG
- **Exact URL:** https://www.wilerallmi.ch/images/Skilift_Wilerallmi_Jahresbericht_2023-2024.pdf
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-21T22:04:21.185154+00:00.
- **Variables:** destination_scope_evidence
- **Transformations:** Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json
- **Coverage:** official destination or municipality; retrieval-date scope snapshot; ? to 2026.
- **Limitations:** Current scope evidence does not by itself establish historical tourism exposure
- **Local raw file:** `data_external/source_evidence/WILERALLMI_ANNUAL_2023_24_20260921T220421Z.pdf`.

## Outstanding provenance gaps

- The retrieval date of the supplied Bergfex and hotel CSV extracts is unknown.
- The precise upstream download URL/version for `bahnen-winter_2056.gpkg` has not been established; it remains registered as a hashed local source rather than attributed by inference.
- Earlier failed/truncated Magic Pass 2021 collection attempts remain in the append-only log, but a later checksum-verified full response is cached and used.
- Current Magic map and press headline counts do not exactly match the 95 embedded destination records; this discrepancy is retained for review.
