# Path C aggregation sensitivity

## Purpose

Fifty-three lift clusters contain multiple supplied listings that disagree on at least one structural feature. The baseline uses the within-cluster median. This robustness check rebuilds the structural segmentation and analogues with the within-cluster minimum and maximum instead.

## Results

All three aggregation rules select k=2. Relative to the median baseline:

- minimum aggregation: segment ARI 0.827; current-Magic top-1 analogue agreement 29.8%; reviewed-treated top-1 agreement 83.7%; treated OOD-category agreement 74.0%; opportunity-signal rank correlation 0.935;
- maximum aggregation: segment ARI 0.714; current-Magic top-1 analogue agreement 60.6%; reviewed-treated top-1 agreement 77.9%; treated OOD-category agreement 76.0%; opportunity-signal rank correlation 0.779.

The selected number of broad segments is robust, but individual nearest analogues and OOD classifications are not invariant. Only **11 of 104** candidates retain the same segment, closest current-Magic analogue, closest reviewed-treated analogue and treated-reference OOD category under all three rules. The enriched decision-support export exposes those row-level flags and lowers confidence for aggregation-sensitive or strong-OOD cases.

`data_processed/path_c_candidate_analogue_sensitivity.csv` preserves every candidate-scenario result, and `reports/path_c_aggregation_sensitivity.csv` contains the full comparison.

## Interpretation

This is a measurement/aggregation sensitivity, not model validation against a causal truth. The median remains the primary rule because it is less dominated by the broadest or narrowest duplicated listing, while min/max results expose how much the decision-support view depends on listing semantics. No causal interpretation or composite ranking is approved.
