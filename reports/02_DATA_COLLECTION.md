# 02 — Data collection

## Collection scope

Collection was deliberately limited to high-priority evidence needed for the initial feasibility gates. No large climate, mobility, demographic, or commercial dataset was downloaded before treatment/outcome viability was assessed.

## Completed official collections

| Source | Result | Reproducible use |
|---|---|---|
| OFS/BFS PXWeb hotel metadata | Cached successfully | Official table definition and 186 municipality code-label pairs |
| geo.admin.ch current municipality identify | 271/271 requests succeeded | Current polygon containing each supplied resort coordinate |
| Magic Pass press archive | Cached successfully | Dated official announcements and known exit/supplement evidence |
| Magic Pass current map | Cached successfully | Current-state destination snapshot, not historical timing |
| Magic Pass seasonal PDFs | 2017–2020 and 2022–2025 cached | Page-reviewed entry-event evidence |
| Magic Pass PDFs 2021 and 2026 | Repeated incomplete downloads | Failure retained in the collection log; archive evidence used where applicable |

Every successful response has a SHA-256 metadata sidecar under the ignored immutable evidence cache. Requests, statuses, files, and failures are recorded in `logs/data_collection_log.csv`. Configuration is versioned in `config/evidence_sources.json` and `config/municipality_queries.json`.

## Derived evidence tables

- `data_processed/resort_point_municipality.csv`: 268 Swiss current point containers and three points outside the current Swiss municipality layer. This is explicitly not a tourism-exposure crosswalk.
- `data_processed/magic_pass_membership_history.csv`: 93 official events, including 88 base-pass entries, one exit, and separately coded supplement/inclusion cases.
- `data_processed/magic_pass_current_destinations.csv`: 95 destinations embedded in the cached current map; 68 have a candidate link to a supplied listing.

## Collection discrepancies and gaps

- The official current page headline refers to more than 100 destinations, while the cached embedded map list contains 95. The mismatch is retained for investigation.
- Twenty-nine membership events have no candidate link to the supplied Swiss listing table; several are foreign destinations, others are composite or differently scoped domains.
- The historical evidence is not yet a complete season-by-season continuity and exit audit.
- The exact upstream version and download URL of `bahnen-winter_2056.gpkg` remain unknown.

Full field-level provenance and plain-language source descriptions are in `metadata/data_sources_master.csv` and `reports/DATA_SOURCES.md`.
