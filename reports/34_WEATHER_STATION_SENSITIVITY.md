# SwissMetNet alternative-station sensitivity

## Design

This robustness check retains the official SwissMetNet universe and the primary module's four daily parameters, 2013 start gate, 80% monthly coverage rule and station-specific 2013–2025 calendar-month analytical normals. For each of the **15 reviewed resort components**, it replaces the nearest eligible station with the next-nearest distinct eligible station. The required alternatives are **CHD, EVO, GIH, INT, LAG, MVE, ORO, SIO, THU, ZER**. Their historical and current-year files are checksum-cached through the standard collector.

The resulting destination panel repeats the primary unweighted unique-station aggregation under the alternative assignments. Temperature and precipitation anomalies are compared only where both primary and alternative proxies are complete.

## Component results

- alternative station-month rows: **1,590**; usable under the common four-parameter gate: **1,583**
- component agreement counts: **{'high': 10, 'moderate': 5}**
- median temperature-anomaly correlation: **0.967**
- median temperature-anomaly mean absolute difference: **0.29 °C**
- median precipitation-anomaly correlation: **0.815**
- median precipitation-anomaly mean absolute difference: **18.7 mm/month**

The descriptive agreement grade is high when temperature-anomaly correlation is at least 0.90 and precipitation-anomaly correlation at least 0.70; moderate at 0.80 and 0.50; otherwise low. These thresholds organise review and are not causal validation criteria.

## Destination results

The alternative panel contains **1,749 destination-month rows** for **11 units**. Both primary and alternative proxies are complete in **1,737 rows**. Destination agreement counts are **{'high': 8, 'moderate': 3}**; the median temperature- and precipitation-anomaly correlations are **0.959** and **0.885**, respectively.

## Interpretation limit

This test measures assignment sensitivity inside one point-station network. It is not independent gridded validation and does not observe piste conditions, snowfall phase, snowmaking, terrain, aspect or a tourism catchment. The next-nearest station can be farther away or at a very different elevation. `weather_station_sensitivity_causal_covariate_approved` remains false everywhere, and the primary causal weather gate remains closed.

## Outputs

- `data_processed/meteoswiss_alternative_station_month.csv`
- `reports/weather_station_alternative_sensitivity.csv`
- `data_processed/destination_weather_alternative_sensitivity.csv`
- `reports/weather_destination_alternative_summary.csv`
