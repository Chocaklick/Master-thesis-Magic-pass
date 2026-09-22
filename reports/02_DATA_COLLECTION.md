# 02 — Data collection

## Collection scope

Collection was initially limited to high-priority evidence needed for the treatment/outcome feasibility gates. After those gates were assessed, the project added the official HESTA hotel-capacity table, SLF snow history, targeted MeteoSwiss temperature/precipitation, STATPOP 2025 municipal population, ARE NPVM 2025 transport travel times, current OFT/BAV public-transport stops, and an official SKI/OFT winter-2026 GTFS Static timetable. Employment and commercial datasets remain deferred.

## Completed official collections

| Source | Result | Reproducible use |
|---|---|---|
| OFS/BFS PXWeb hotel metadata | Cached successfully | Official table definition and 186 municipality code-label pairs |
| OFS/BFS HESTA supply/demand table | 14 annual API chunks cached successfully | Monthly establishments, rooms, beds and occupancy with exact query/checksum provenance |
| OFS/BFS STATPOP population | 2025 municipality extract and metadata cached successfully | Permanent residents for 2,115 municipalities; exact BFS join to complete-year HESTA context |
| geo.admin.ch current municipality identify | 271/271 requests succeeded | Current polygon containing each supplied resort coordinate |
| swisstopo swissBOUNDARIES3D 2026-01 | Checksum-cached official GeoPackage ZIP | Current municipality polygons for same-destination distance diagnostics; not historical boundary harmonisation |
| Magic Pass press archive | Cached successfully | Dated official announcements and known exit/supplement evidence |
| Magic Pass current map | Cached successfully | Current-state destination snapshot, not historical timing |
| Magic Pass seasonal publications | 2017–2025 annual PDFs plus the official 2020/2021 PNG map cached | Page/image-reviewed entry, roster and modality evidence |
| Magic Pass 2021 main PDF | Download recovered on 2026-09-21 after earlier incomplete responses | Page 3 documents an expansion by five named additions; page 4 gives aggregate 40-winter/21-summer counts but no named modality list |
| Grisons competing-pass archives | Three BBGR annual reports (2017/18–2019/20) and the 2022/23 graubündenCARD operator/transport list cached | Page-referenced SnowPass, TopCard and graubündenCARD environment review for remote donor candidates |
| Kronberg operator archives | Official 2017 and 2023 annual reports cached | Contemporaneous investment, product mix, winter sensitivity and local tourism-shock review for Gonten |
| SLF IMIS documentation, stations and daily snow | Cached successfully | Daily mountain-station snow-depth history and auditable station-proxy construction |
| MeteoSwiss SwissMetNet metadata and selected daily station files | Six metadata snapshots plus 14 historical/recent station files cached successfully | Daily temperature and precipitation, coverage-qualified monthly anomalies, and auditable regional station proxies |
| ARE NPVM transport travel times | Checksum-verified 32.8 MB GeoPackage, STAC item and methodology page cached | 7,978 traffic-zone values for road/public transport to major centres and agglomerations, reference date 2025-06-30 |
| OFT/BAV public-transport stops | Checksum-verified 2.8 MB French EPSG:2056 CSV archive, STAC item and official model documentation cached | 27,325 official passenger stops after excluding pure operating points; 1,717 stops carry train mode code `B` |
| SKI/OFT GTFS Static timetable | Checksum-verified 195.9 MB build `20260207`, valid 2025-12-14 through 2026-12-12 | Scheduled weekday/Saturday routing from 186 municipality origin stops to 15 reviewed destination component nodes |

Every successful response has a SHA-256 metadata sidecar under the ignored immutable evidence cache. Requests, statuses, files, and failures are recorded in `logs/data_collection_log.csv`. Configuration is versioned in `config/evidence_sources.json`, `config/meteoswiss_selected_station_files.json`, and `config/municipality_queries.json`.

## Derived evidence tables

The supplemental membership review first cached five dated documents: the official April 2019 roster, the Magic Pass 2024/2025 map distributed by Raiffeisen, operator tariffs for Les Pleiades in 2020/2021 and 2021/2022, and Fribourg Region's December 2021 winter release. The later recovery of Magic Pass's own 2020/2021 network map and the 2021/2022 dossier's explicit incremental expansion statement close the seven remaining gaps for the 14 reviewed units. Exact locators and interpretation limits are recorded in `08_MEMBERSHIP_EVIDENCE_REVIEW.md`. Selective collection supports repeated `--source-id` arguments so completed/failed unrelated requests need not be repeated.

The annual-offering review rendered seven dated launch lists/maps and transcribed only explicit `HIVER` versus `ÉTÉ-HIVER` symbols or complete named summer lists. It classifies 58 active reviewed unit-seasons, including 36 with summer access for at least one published component. The versioned transcription and limitations are documented in `10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md`.

- `data_processed/resort_point_municipality.csv`: 268 Swiss current point containers and three points outside the current Swiss municipality layer. This is explicitly not a tourism-exposure crosswalk.
- `data_processed/magic_pass_membership_history.csv`: 93 official events, including 88 base-pass entries, one exit, and separately coded supplement/inclusion cases.
- `data_processed/magic_pass_current_destinations.csv`: 95 destinations embedded in the cached current map; 69 have a candidate link to a supplied listing.
- `data_processed/hotel_capacity_municipality_month.csv`: 31,248 official municipality-month supply rows; 29,274 have establishments, rooms and beds observed.
- `data_processed/resort_snow_station_crosswalk.csv`: 271 resort listings linked to a coverage-qualified external SLF snow-station proxy with distance, elevation gap and representativeness flags.
- `data_processed/destination_snow_month.csv`: 1,749 reviewed destination-month snow-proxy rows through 2026-03; 1,733 pass the complete station-month coverage gate.
- `data_processed/meteoswiss_station_month.csv`: 1,113 station-month rows for seven selected stations; 1,111 pass the joint temperature/precipitation coverage gate.
- `data_processed/resort_weather_station_crosswalk.csv`: 15 reviewed component resorts linked to the nearest of 112 current inventory-eligible SwissMetNet stations, with distance, elevation gap and non-piste representation flags.
- `data_processed/destination_weather_month.csv`: 1,749 reviewed destination-month weather rows through 2026-03; 1,744 pass the complete station-month coverage gate.
- `data_processed/treatment_municipality_distance_exposure.csv`: 2,046 same-destination distance rows for 11 reviewed destinations and 186 hotel municipality series, using 185 current polygons and an explicit Moutier boundary-version bridge.
- `data_processed/donor_shortlist_final_audit.csv`: all 35 shortlisted pairs with network-distance priority and the seven beyond-50-km pairs joined to page-referenced competing-pass/local-shock evidence.
- `data_processed/municipality_tourism_context_2025.csv`: STATPOP population plus complete-year HESTA hotel nights/supply and per-resident ratios, with no imputation.
- `data_processed/path_c_cluster_tourism_context.csv`: qualified context for the unique municipalities containing each cluster's listing points; explicitly not a destination catchment.
- `data_processed/resort_transport_accessibility_context.csv`: official NPVM travel-time values for 170 exact point-in-zone assignments plus 98 explicit nearest-zone-within-current-municipality proxies; three foreign listing points remain missing.
- `data_processed/path_c_cluster_transport_accessibility_context.csv`: min/median/max travel-time context across usable listing points for all 162 clusters, with exact-only medians, proxy distances and one partial cross-border cluster exposed.
- `data_processed/resort_public_transport_stop_context.csv`: nearest official passenger stop and nearest train-capable passenger stop for 268 Swiss listing points; three French points remain missing.
- `data_processed/path_c_cluster_public_transport_stop_context.csv`: min/median/max straight-line stop distances across eligible listing points for all 162 clusters, with one partial cross-border cluster exposed.
- `data_processed/treatment_municipality_public_transport_journey_samples.csv`: 49,104 weekday/Saturday timetable requests, retaining waiting time, scheduled vehicle time, generalized elapsed time, legs, transfers, modes and explicit exclusion reasons.
- `data_processed/treatment_municipality_public_transport_journey_context.csv`: 2,046 destination–municipality summaries for 11 reviewed destinations and 186 hotel municipalities; 1,104 pairs are feasible at every sampled time.
- `reports/public_transport_arrival_node_review.csv`: versioned current review of all 15 component arrival nodes; eight name a lift/ski access, one names the destination locality and six are explicit village/local-centre proxies.
- `reports/public_transport_historical_audit_plan.csv`: all 15 destination component nodes linked to an official archive snapshot for their first-exposure winter; historical service comparison remains false.

## Collection discrepancies and gaps

- The official current page headline refers to more than 100 destinations, while the cached embedded map list contains 95. The mismatch is retained for investigation.
- Twenty-nine membership events have no candidate link to the supplied Swiss listing table; several are foreign destinations, others are composite or differently scoped domains.
- Continuity is complete for the 14 reviewed units, but the broader 88-event historical inventory still contains unresolved destination identities and is not a complete audit of every network destination.
- The exact upstream version and download URL of `bahnen-winter_2056.gpkg` remain unknown.
- SLF IMIS stations support avalanche monitoring and are not direct observations of resort pistes; the 60 low-comparability resort links remain visible and are not feature-ready.
- SwissMetNet stations are regional weather proxies rather than piste measurements. EVO 2016-07 and INT 2013-08 fail the 80% precipitation coverage gate and remain missing; the daily precipitation window is 06:00 UTC to 06:00 UTC the following day.
- The official 2023/24 graubündenCARD operator/transport PDF remains visible in the publisher's search index but returned HTTP 404 during reproducible collection. The audit therefore records exact Splügen-Tambo participation in 2022/23 and leaves anchor-season continuity unresolved.
- NPVM zone polygons do not continuously cover high-alpine terrain. Ninety-eight Swiss listing points therefore use the nearest zone that intersects their independently resolved current municipality; assignment distance is retained (maximum 3.64 km), and the values remain qualified model context rather than live routing.
- The OFT/BAV source includes selected foreign operating points but is not a complete French stop universe, so the three French listing points are left missing. All-mode passenger stops include cableways and chairlifts, and straight-line point distance does not measure routes, timetables, frequency, seasonal operation or validated resort arrival access.
- GTFS Static describes published schedules, not real-time disruption, fares, crowding or guaranteed transfers. All 15 current arrival nodes pass the versioned name/mode/municipality/distance review for descriptive routing, but six are explicitly village/local-centre proxies and door-to-lift walking remains unverified. Official historical archive URLs were identified for all represented exposure winters, but the dynamic archive index disallows the automated collector via `robots.txt`; the 2018–2025 ZIP contents have not yet been checksum-cached or compared.

Full field-level provenance and plain-language source descriptions are in `metadata/data_sources_master.csv` and `reports/DATA_SOURCES.md`.
