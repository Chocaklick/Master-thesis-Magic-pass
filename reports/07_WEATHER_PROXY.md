# MeteoSwiss regional weather proxy

Generated reproducibly by `src/data_processing/build_weather_proxy_panel.py`.

## Source decision

The project selected official MeteoSwiss SwissMetNet station files for the first temperature and precipitation control. SwissMetNet provides directly observed daily station values, official station coordinates/elevations, a parameter inventory and static historical/current-year CSV files. MeteoSwiss 1 km spatial climate analyses remain a future robustness option; ERA5-Land remains a coarser reanalysis fallback. The targeted seven-station download is materially smaller and fully traceable to the reviewed destination units.

The four daily parameters are:

- `tre200d0`: mean air temperature 2 m above ground, °C;
- `tre200dn`: minimum air temperature 2 m above ground, °C;
- `tre200dx`: maximum air temperature 2 m above ground, °C;
- `rre150d0`: precipitation total from 06:00 UTC to 06:00 UTC the following day, mm.

The precipitation window is therefore not identical to a civil calendar day. This timing difference is preserved in the output rather than silently relabelled.

## Collection and coverage

- Daily analysis rows: **33,866**, from 2013-01-01 through 2026-03-31.
- Stations eligible from official inventory metadata: **112** with all four parameters starting by the analysis date and no recorded end date.
- Selected stations used by the reviewed destinations: **7** (ABO, EVO, GRC, INT, MER, MLS, MVE).
- Station-month rows: **1,113**; **1,111** pass the 80% coverage gate for all four parameters.
- Two station-months fail the precipitation gate: EVO in 2016-07 and INT in 2013-08. They remain missing downstream; no imputation is used.

Calendar-month temperature and precipitation anomalies use station-specific 2013–2025 normals calculated only from usable months. These normals are analytical reference values, not MeteoSwiss climatological normals.

## Resort-to-station assignments

Each of the 15 resort listings in the 11 reviewed destination units is assigned to the geographically nearest current SwissMetNet station with all four daily parameters starting by 2013. Repeated stations within a destination are deduplicated before destination aggregation.

| Destination | Resort listing | Station | Station name | Distance km | Station elevation m | Gap to resort top m | Proxy quality |
|---|---|---|---|---:|---:|---:|---|
| Anniviers Magic Pass portfolio | Grimentz/Zinal Grimentz - Zinal | EVO | Evolène / Villa | 8.5 | 1825 | 1075 | high |
| Anniviers Magic Pass portfolio | St - Luc Chandolin | MVE | Montana | 13.6 | 1423 | 1577 | moderate |
| Axalp | Axalp Brienz | MER | Meiringen | 9.9 | 589 | 1411 | high |
| Bumbach | Bumbach - Schangnau | INT | Interlaken | 15.0 | 578 | 787 | moderate |
| Crans-Montana | Crans - Montana Crans - Montana | MVE | Montana | 4.4 | 1423 | 1577 | high |
| Espace Dent Blanche | Arolla | EVO | Evolène / Villa | 9.9 | 1825 | 1175 | high |
| Espace Dent Blanche | Evolène | EVO | Evolène / Villa | 3.5 | 1825 | 775 | high |
| Espace Dent Blanche | La Forclaz | EVO | Evolène / Villa | 2.7 | 1825 | 379 | high |
| Les Pléiades | Les Pléiades | MLS | Le Moléson | 9.6 | 1974 | 577 | high |
| Meiringen-Hasliberg | Meiringen - Hasliberg | MER | Meiringen | 5.0 | 589 | 1844 | high |
| Moléson | Moléson - La Gruyère | MLS | Le Moléson | 0.5 | 1974 | 28 | high |
| Reichenbach im Kandertal Magic Pass portfolio | Faltschen - Reichenbach im Kandertal | INT | Interlaken | 12.4 | 578 | 782 | moderate |
| Reichenbach im Kandertal Magic Pass portfolio | Kiental | ABO | Adelboden | 15.2 | 1321 | 90 | moderate |
| Saas-Fee | Saas - Fee | GRC | Grächen | 13.4 | 1605 | 1995 | moderate |
| Schwanden | Schwanden - Sigriswil Thunersee | INT | Interlaken | 11.7 | 578 | 862 | moderate |

Quality is based on horizontal distance for a regional anomaly proxy: high at ≤10 km, moderate at ≤20 km, and low beyond 20 km. The elevation gap remains visible and can be large because resort-top altitude is not the station's measurement target.

## Destination aggregation and limits

The destination output contains **1,749 rows**, of which **1,744** have complete weather proxies. Temperature, precipitation and anomalies are unweighted means across unique assigned stations and are withheld unless every expected station-month passes the coverage gate.

These observations describe regional weather near the reviewed resort listings. They do not measure piste microclimate, snowfall phase, snowmaking, grooming, aspect, wind redistribution or conditions across the full tourism catchment. `weather_direct_slope_representation` and `weather_causal_covariate_approved` are false throughout. Adding weather reduces one time-varying confounding gap but does not resolve treatment continuity, selection, spillovers or donor validity.
