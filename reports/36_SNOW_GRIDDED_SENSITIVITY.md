# SPASS gridded-snow sensitivity

Generated reproducibly by `src/data_processing/build_snow_gridded_sensitivity.py`.

## Purpose and source

This audit compares the selected SLF IMIS station proxy with the peer-reviewed SPASS OSHD-CLQM daily snow-depth grid (DOI `10.16904/envidat.580`). SPASS supplies a 1 km grid for hydrological years 1962–2023. The common project window contains ten complete November–April winters, 2013/14 through 2022/23.

SPASS is a modelled product, not a second measurement network. It is driven by gridded MeteoSwiss temperature/precipitation, quantile-mapped to mimic OSHD-EKF, whose target assimilates snow observations from 350 stations, and converted from SWE to snow depth with SWE2HS. It therefore changes spatial representation and method, but is not independent of the broader SLF snow-observation system.

## Method

For every reviewed resort component, the script retains both the nearest 1 km cell and the daily median of its surrounding 3×3 cells before forming November–April winter means and ≥30 cm day shares. The same extraction is repeated around the selected station itself. This separates disagreement caused by the model/measurement method from disagreement caused by using a station located away from the resort point. The resort-centred local 3×3 statistic is primary because the source publication recommends some spatial aggregation and cautions against single-cell interpretation. The comparison deliberately does not reproduce the publication's elevation-matched 3×3 selection because the distributed NetCDF contains no grid elevation and resort-top altitude is not a piste elevation distribution.

The `HSCLQMD` variable has no `units` attribute. Raw values (country maximum about 3 m on the inspected winter day) are interpreted as metres and converted to centimetres; the publication defines its HS analyses in centimetres. This upstream metadata omission remains explicit in the output and is a limitation rather than silently invented metadata.

## Results

- Reviewed components / unique resort-centred nearest cells / unique station-centred nearest cells: **15 / 15 / 11**.
- Maximum component-to-cell-centre / station-to-cell-centre distance: **519.1 m / 527.8 m**.
- Complete component-winters: **150 / 150**.
- Component agreement using the resort-centred local 3×3 rule: **{"high": 1, "low": 8, "moderate": 6}**.
- Component agreement using the station-centred local 3×3 diagnostic: **{"high": 9, "moderate": 6}**.
- Median resort-centred / station-centred winter-depth correlation: **0.887 / 0.897**.
- Median resort-centred / station-centred relative mean absolute depth difference: **61.9% / 25.9%**.
- Destination winters with both grid and station proxies complete: **110 / 110**.
- Destination agreement: **{"high": 1, "low": 6, "moderate": 4}**.
- Median destination winter-depth correlation: **0.906**.
- Median destination relative mean absolute depth difference: **60.8%**.

The agreement thresholds are the same conservative rules used by the next-nearest-station sensitivity: high requires at least eight common winters, correlation ≥0.75, relative mean absolute difference ≤35%, and an absolute ≥30 cm reliability-share gap ≤0.20; moderate requires correlation ≥0.50 and relative difference ≤60%.

## Decision and limitations

Station measurements represent flat local observation sites and can overrepresent snow relative to a 1 km areal cell. Conversely, SPASS smooths unresolved terrain and land-cover effects, inherits limitations from the daily temperature and precipitation fields, does not fully correct monthly or single-winter bias, and converts SWE to depth. The grid ends in August 2023, so it cannot evaluate the two latest project winters. It is neither direct piste snow nor snowmaking, grooming, wind redistribution or operating-day evidence.

Interpretation: `slf_imis_station_vs_spass_oshd_clqm_1km_modelled_snow_sensitivity_shared_slf_assimilation_target_not_independent_measurement_network_piste_observation_or_causal_approval`. Every causal approval remains false. A genuinely independent measurement or reanalysis product is still required if snow is proposed as a causal covariate.

Detailed outputs: `data_processed/spass_snow_component_winter.csv`, `reports/snow_gridded_component_comparison.csv`, `data_processed/destination_snow_gridded_sensitivity.csv`, and `reports/snow_gridded_destination_summary.csv`.
