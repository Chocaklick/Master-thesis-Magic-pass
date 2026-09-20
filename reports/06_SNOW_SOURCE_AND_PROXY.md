# Snow-source review and SLF proxy construction

Generated reproducibly by `src/data_processing/build_snow_proxy_panel.py`.

## Source decision

Three authoritative options were compared before collection:

| Source | Strength | Limitation | Decision |
|---|---|---|---|
| WSL Institute for Snow and Avalanche Research SLF, IMIS historical measurements | Direct daily mountain snow-depth observations; station coordinates/elevation; static CSV; CC BY 4.0; DOI 10.16904/envidat.406 | Avalanche-monitoring sites, often above treeline; some raw values are not regularly corrected; not direct piste observations | **Selected for the first snow proxy** |
| MeteoSwiss Open Government Data, SwissMetNet | Official station observations for temperature, precipitation and snow at several resolutions with historical chunks | Lower-elevation/general meteorological network; a separate spatial/elevation match is required | Retain for a later temperature/precipitation block |
| Copernicus ERA5-Land | Spatially complete 0.1° hourly reanalysis from 1950, CC-BY, DOI 10.24381/cds.e2161bac | Modelled grid, coarse for Alpine topography; CDS workflow and larger extraction | Retain as a gridded sensitivity/fallback source |

## Collected SLF data

- Raw daily rows: **1,212,878**, from 1992-10-01 to 2026-09-13.
- Snow-station codes with daily data: **166**.
- Stations passing the predeclared 80% winter-day coverage gate for 2013/14–2025/26: **115**.
- Negative physical snow-depth values retained in raw data but treated as invalid in derived measures: **2,295**.

Daily `HS` is the median total snowpack depth over the preceding 24 hours at 06:00 UTC. `HN_1D` is modelled by SNOWPACK, so every derived new-snow field is labelled `modeled_`; it is not presented as a direct gauge observation. No missing or physically negative snow depth is imputed.

## Resort proxy assignment

Each of the **271 resort listings** is assigned to the geographically nearest SLF snow station among those passing the longitudinal coverage gate. The crosswalk preserves distance, station elevation, gap to the published resort-top altitude, station activity/type, coverage, and the assignment rule.

- High proxy quality (≤10 km and ≤500 m elevation gap): **112** resorts.
- Moderate proxy quality (≤25 km and ≤1,000 m elevation gap): **99** resorts.
- Low proxy quality: **60** resorts.

This classification measures proxy comparability, not measurement accuracy. IMIS stations can differ from a resort in aspect, terrain, wind exposure, grooming and snowmaking. `direct_slope_representation` is therefore false for every row.

## Derived outputs

- `data_processed/slf_snow_station_month.csv`: station-month snow depth, observation coverage, threshold-day shares and modelled new snow.
- `data_processed/slf_snow_station_winter.csv`: November–April station-winter summaries.
- `data_processed/resort_snow_station_crosswalk.csv`: auditable resort-to-station proxy assignments.
- `data_processed/resort_snow_vulnerability.csv`: long-run reliability, variability, trend and low-snow indicators for exploratory use.
- `data_processed/destination_snow_month.csv`: snow proxies for the 11 reviewed destination units; multi-station destinations use an unweighted mean only when all assigned station-months pass 80% daily coverage.

The destination panel contains **1,733 complete snow-proxy months** out of 1,749. No snow variable is approved as a causal covariate yet; source representativeness and remaining weather controls must be evaluated in robustness analyses.
