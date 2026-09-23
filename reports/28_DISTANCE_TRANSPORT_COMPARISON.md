# Same-destination distance versus scheduled public transport

## Result

The comparison preserves the complete **2,046 pair** universe: 11 reviewed destinations × 186 hotel municipalities. **1,700 pairs** have both outbound and return means, while **1,104** are feasible at every sampled time in both directions.

For the **10 destinations** with at least 20 bidirectional pairs, the median within-destination rank correlation between representative-point distance and mean scheduled round-trip time is **0.743**. It ranges from **0.607** for Saas-Fee to **0.869** for Les Pléiades. Distance is informative, but it is not interchangeable with scheduled public-transport accessibility.

Using a predeclared absolute rank-gap threshold of 0.25, **225 pairs** have materially worse transit rank than their distance rank suggests, while **171** have materially better transit rank. These are diagnostic disagreements, not causal exposure classes.

## Coverage warning

Meiringen-Hasliberg has no pair with both outbound and return means under the declared six-vehicle and 480-minute limits. Four destinations have no pair feasible at every sampled time in both directions, so complete-pair correlations are available for only **7 destinations**. Partial-coverage correlations remain separately labelled and never replace the raw coverage fields.

## Interpretation

Distances use current 2026 municipality geometry; travel times use two winter-2026 GTFS reference days and reviewed current arrival nodes. Neither is a historical visitor catchment, observed traveller route or treatment effect. Historical comparability, causal exposure and causal-effect approvals remain false.

## Outputs

- `data_processed/treatment_municipality_distance_transport_comparison.csv`
- `reports/distance_transport_correlations_by_destination.csv`
- `reports/distance_transport_band_summary.csv`
- `reports/distance_transport_comparison_summary.json`
