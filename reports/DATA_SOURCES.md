# Data sources and provenance

This report is generated from `metadata/data_sources_master.csv`. Raw internet responses are immutable and accompanied by collection-log entries and SHA-256 metadata where available.

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

## DERIVED_REVIEWED_DESTINATION_PANEL — Reviewed destination-month panel

- **Contents and relevance:** Monthly destination outcomes and hotel capacity aggregated across reviewed municipality scopes with diagnostic treatment coding
- **Producer:** Master thesis analytical pipeline
- **Exact URL:** Not documented.
- **Access and retrieval date:** versioned Python transformation; unknown date.
- **Variables:** reviewed_destination_month_outcomes|hotel_capacity|diagnostic_membership_status
- **Transformations:** Additive municipality outcome and capacity totals; missing unless every municipality is observed; official occupancy percentages retained only for single-municipality units; entry carried forward only as a flagged diagnostic assumption
- **Coverage:** reviewed destination unit; monthly; 2013-01 to 2026-12 grid; 2026-03 latest observed outcome.
- **Limitations:** No row is causal-ready; treatment continuity and controls remain unresolved and other time-varying confounders are pending
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
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2017_20260919T232136Z.pdf`.

## MAGIC_2018 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:21:46.699377+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2018 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2018_20260919T232146Z.pdf`.

## MAGIC_2019 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:21:56.936424+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2019 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2019_20260919T232156Z.pdf`.

## MAGIC_2020 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:23:50.233825+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2020 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2020_20260919T232350Z.pdf`.

## MAGIC_2021 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** attempted HTTP GET; see collection log; unknown date.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2021 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `not cached / not applicable`.

## MAGIC_2021_APRIL — Official Magic Pass press material

- **Contents and relevance:** Official April 2021 follow-up release for the 2021/2022 pass
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T01:15:19.337900+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; ? to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2021_APRIL_20260920T011519Z.pdf`.

## MAGIC_2022 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:22:27.695130+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2022 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2022_20260919T232227Z.pdf`.

## MAGIC_2022_DOSSIER — Official Magic Pass press material

- **Contents and relevance:** Official full press dossier for the 2022/2023 pass
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T01:16:51.624040+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; ? to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2022_DOSSIER_20260920T011651Z.pdf`.

## MAGIC_2023 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:22:38.145606+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2023 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2023_20260919T232238Z.pdf`.

## MAGIC_2024 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:24:11.201676+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2024 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2024_20260919T232411Z.pdf`.

## MAGIC_2025 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:22:58.692358+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2025 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_2025_20260919T232258Z.pdf`.

## MAGIC_2026 — Official Magic Pass press material

- **Contents and relevance:** Official seasonal press evidence; membership extraction requires page verification
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-20T00:56:13.071390+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2026 to ?.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
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

## MAGIC_OFFICIAL_EVIDENCE_SET — Official Magic Pass evidence set

- **Contents and relevance:** Union of official Magic Pass seasonal press evidence and dated archive notices
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** Derived only from source rows MAGIC_2017 through MAGIC_2025 and MAGIC_PRESS_ARCHIVE; unknown date.
- **Variables:** membership_event_history
- **Transformations:** Manual event transcription; reviewed aliases and unique normalised labels create candidate links
- **Coverage:** official ski destination with candidate resort link; season/event; 2017/2018 to 2025/2026.
- **Limitations:** Incomplete continuity/exit audit; unresolved destinations retained
- **Local raw file:** `not cached / not applicable`.

## MAGIC_PRESS_ARCHIVE — Official Magic Pass press material

- **Contents and relevance:** Official dated membership announcements and exit notices
- **Producer:** Magic Mountains Cooperation
- **Exact URL:** https://www.magicpass.ch/fr/presse
- **Access and retrieval date:** HTTP GET with immutable response and SHA-256 sidecar; 2026-09-19T23:17:15.917509+00:00.
- **Variables:** membership_event_evidence
- **Transformations:** Page-numbered text extraction and manually reviewed event transcription
- **Coverage:** official ski destination; dated announcement / season; 2017 to 2026.
- **Limitations:** Destination/operator scope may differ from Bergfex listing scope
- **Local raw file:** `data_external/source_evidence/MAGIC_PRESS_ARCHIVE_20260919T231715Z.html`.

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

## Outstanding provenance gaps

- The retrieval date of the supplied Bergfex and hotel CSV extracts is unknown.
- The precise upstream download URL/version for `bahnen-winter_2056.gpkg` has not been established; it remains registered as a hashed local source rather than attributed by inference.
- The Magic Pass 2021 PDF download did not complete in the scripted collector; failures remain in the collection log. The 2026 PDF and official press archive HTML are cached, and 2026 entry events are outside the current outcome window.
- Current Magic map and press headline counts do not exactly match the 95 embedded destination records; this discrepancy is retained for review.
