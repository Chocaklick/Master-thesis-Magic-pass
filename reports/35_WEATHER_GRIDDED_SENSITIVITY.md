# MeteoSwiss monthly gridded-weather sensitivity

## Design

This check compares the selected SwissMetNet station proxy with the official MeteoSwiss **TabsM v1.4** monthly mean-temperature and **RhiresM v2.0** monthly precipitation spatial analyses. The archive supplies one annual NetCDF per product for 2013–2025; three current monthly files extend both products through March 2026. All **32 assets** are cached and matched to their official STAC SHA-256 multihashes.

For each of the **15 reviewed resort components**, the extraction uses the nearest cell that is valid for both products on the regular `ch01r.swiss.lv95` grid. Grid spacing is 1 km; the largest point-to-cell-centre distance is **519 m**. Anomalies use a component-cell and calendar-month 2013–2025 mean, matching the station proxy's analytical reference years. Destination values are unweighted means across unique component grid cells and are complete only when every expected cell is observed.

## Component results

- component-month rows: **2,385**; complete temperature and precipitation rows: **2,385**
- component agreement counts: **{'high': 12, 'low': 2, 'moderate': 1}**
- median temperature-anomaly correlation: **0.983**
- median temperature-anomaly mean absolute difference: **0.24 °C**
- median precipitation-anomaly correlation: **0.942**
- median precipitation-anomaly mean absolute difference: **14.9 mm/month**

The predeclared review categories are unchanged from the station sensitivity: high requires temperature/precipitation anomaly correlations of at least 0.90/0.70, moderate at least 0.80/0.50, and otherwise low. They are descriptive review bands, not causal gates.

## Destination results

The comparison contains **1,749 destination-months** for **11 units**. Both station and grid proxies are complete in **1,744 rows**. Destination agreement counts are **{'high': 8, 'low': 2, 'moderate': 1}**; median temperature- and precipitation-anomaly correlations are **0.980** and **0.942**.

## Interpretation limit

TabsM is based on homogenised monthly climate-station series and RhiresM on monthly rain-gauge totals. The gridding and monthly analysis method differ from the direct daily SwissMetNet extraction, but these are not independent measurement networks. A 1 km cell spacing does not imply 1 km effective precipitation resolution; official documentation warns of larger Alpine/high-elevation uncertainty and winter precipitation undercatch. Neither product measures piste microclimate, snow phase, wind redistribution, grooming or snowmaking. Every gridded-weather causal-approval flag therefore remains false.

## Outputs

- `data_processed/meteoswiss_gridded_component_month.csv`
- `reports/weather_gridded_component_comparison.csv`
- `data_processed/destination_weather_gridded_sensitivity.csv`
- `reports/weather_gridded_destination_summary.csv`
