# Historical public-transport timetable audit

## What has been verified

The official SKI/Open Data Mobility Switzerland archive index was inspected on **2026-09-22**. A winter GTFS snapshot was found for every first-exposure timetable year represented by the 11 destination units and 15 component arrival nodes in the scheduled-journey context. The deterministic selection rule is: **official_snapshot_closest_to_7_february_of_first_magic_pass_exposure_winter**.

- **2018**: `2018-02-07` — https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2018-gtfs/GTFS_FP2018_2018-02-07.zip
- **2019**: `2019-02-06` — https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2019-gtfs/GTFS_FP2019_2019-02-06.zip
- **2020**: `2020-02-05` — https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2020-gtfs/GTFS_FP2020_2020-02-05.zip
- **2023**: `2023-02-08_04-15` — https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2023-gtfs2020/GTFS_FP2023_2023-02-08_04-15.zip
- **2024**: `2024-02-07_04-15` — https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2024-gtfs2020/GTFS_FP2024_2024-02-07_04-15.zip
- **2025**: `2025-02-06` — https://archive.opentransportdata.swiss/timetable_gtfs/timetable-2025-gtfs2020/GTFS_FP2025_2025-02-06.zip
- **2026**: `2026-02-07` — https://data.opentransportdata.swiss/dataset/3d2c18f9-9ef1-463f-a249-5c67604efd74/resource/a18f0b30-fc68-4478-af5b-a90f1fc7c65d/download/gtfs_fp2026_20260207.zip

Automated caching of the dynamic archive index was attempted but stopped because its `robots.txt` policy disallows the project collector. The reviewed URLs and the failed collection attempt are retained transparently; the restriction was not bypassed.

## What has not been verified

The historical ZIP files for 2018–2025 have not yet been downloaded and routed. Consequently, stop continuity, departure frequency, mode sequence and journey-time changes around each destination's first Magic Pass winter have **not** been measured. Identifying an official archive file is not evidence that a line remained stable.

The winter-2026 scheduled journey measures therefore remain descriptive current context. They are not approved as pre-treatment or causal covariates until the anchor-year feeds are checksum-cached and compared with the same node and routing rules.

## Reproducible audit table

See `reports/public_transport_historical_audit_plan.csv`. It links each selected current component node to its first-exposure winter archive URL and keeps `historical_destination_stop_service_compared` and `causal_accessibility_feature_approved` false.
