# 02 — Data collection

## Collection scope

Collection was initially limited to high-priority evidence needed for the treatment/outcome feasibility gates. After those gates were assessed, the project added the official HESTA hotel-capacity table, SLF snow history, and targeted MeteoSwiss temperature/precipitation. Mobility, demographic and commercial datasets remain deferred.

## Completed official collections

| Source | Result | Reproducible use |
|---|---|---|
| OFS/BFS PXWeb hotel metadata | Cached successfully | Official table definition and 186 municipality code-label pairs |
| OFS/BFS HESTA supply/demand table | 14 annual API chunks cached successfully | Monthly establishments, rooms, beds and occupancy with exact query/checksum provenance |
| geo.admin.ch current municipality identify | 271/271 requests succeeded | Current polygon containing each supplied resort coordinate |
| Magic Pass press archive | Cached successfully | Dated official announcements and known exit/supplement evidence |
| Magic Pass current map | Cached successfully | Current-state destination snapshot, not historical timing |
| Magic Pass seasonal PDFs | 2017–2020 and 2022–2025 cached | Page-reviewed entry-event evidence |
| Magic Pass 2021 main PDF | Repeated incomplete downloads | Failure retained in the collection log; smaller official follow-up used where applicable |
| SLF IMIS documentation, stations and daily snow | Cached successfully | Daily mountain-station snow-depth history and auditable station-proxy construction |
| MeteoSwiss SwissMetNet metadata and selected daily station files | Six metadata snapshots plus 14 historical/recent station files cached successfully | Daily temperature and precipitation, coverage-qualified monthly anomalies, and auditable regional station proxies |

Every successful response has a SHA-256 metadata sidecar under the ignored immutable evidence cache. Requests, statuses, files, and failures are recorded in `logs/data_collection_log.csv`. Configuration is versioned in `config/evidence_sources.json`, `config/meteoswiss_selected_station_files.json`, and `config/municipality_queries.json`.

## Derived evidence tables

The additional membership review cached five dated documents: the official April 2019 roster, the Magic Pass 2024/2025 map distributed by Raiffeisen, operator tariffs for Les Pleiades in 2020/2021 and 2021/2022, and Fribourg Region's December 2021 winter release. These resolve 18 of 25 previously missing unit-seasons. Seven remain; exact pages and selection limits are recorded in `08_MEMBERSHIP_EVIDENCE_REVIEW.md`. Selective collection now supports repeated `--source-id` arguments so completed/failed unrelated requests need not be repeated.

- `data_processed/resort_point_municipality.csv`: 268 Swiss current point containers and three points outside the current Swiss municipality layer. This is explicitly not a tourism-exposure crosswalk.
- `data_processed/magic_pass_membership_history.csv`: 93 official events, including 88 base-pass entries, one exit, and separately coded supplement/inclusion cases.
- `data_processed/magic_pass_current_destinations.csv`: 95 destinations embedded in the cached current map; 68 have a candidate link to a supplied listing.
- `data_processed/hotel_capacity_municipality_month.csv`: 31,248 official municipality-month supply rows; 29,274 have establishments, rooms and beds observed.
- `data_processed/resort_snow_station_crosswalk.csv`: 271 resort listings linked to a coverage-qualified external SLF snow-station proxy with distance, elevation gap and representativeness flags.
- `data_processed/destination_snow_month.csv`: 1,749 reviewed destination-month snow-proxy rows through 2026-03; 1,733 pass the complete station-month coverage gate.
- `data_processed/meteoswiss_station_month.csv`: 1,113 station-month rows for seven selected stations; 1,111 pass the joint temperature/precipitation coverage gate.
- `data_processed/resort_weather_station_crosswalk.csv`: 15 reviewed component resorts linked to the nearest of 112 current inventory-eligible SwissMetNet stations, with distance, elevation gap and non-piste representation flags.
- `data_processed/destination_weather_month.csv`: 1,749 reviewed destination-month weather rows through 2026-03; 1,744 pass the complete station-month coverage gate.

## Collection discrepancies and gaps

- The official current page headline refers to more than 100 destinations, while the cached embedded map list contains 95. The mismatch is retained for investigation.
- Twenty-nine membership events have no candidate link to the supplied Swiss listing table; several are foreign destinations, others are composite or differently scoped domains.
- The historical evidence is not yet a complete season-by-season continuity and exit audit.
- The exact upstream version and download URL of `bahnen-winter_2056.gpkg` remain unknown.
- SLF IMIS stations support avalanche monitoring and are not direct observations of resort pistes; the 60 low-comparability resort links remain visible and are not feature-ready.
- SwissMetNet stations are regional weather proxies rather than piste measurements. EVO 2016-07 and INT 2013-08 fail the 80% precipitation coverage gate and remain missing; the daily precipitation window is 06:00 UTC to 06:00 UTC the following day.

Full field-level provenance and plain-language source descriptions are in `metadata/data_sources_master.csv` and `reports/DATA_SOURCES.md`.
