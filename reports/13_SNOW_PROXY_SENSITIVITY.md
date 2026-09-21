# SLF alternative-station sensitivity

Generated reproducibly by `src/data_processing/build_snow_station_sensitivity.py`.

## Purpose

The primary snow proxy assigns the nearest SLF snow station passing the 80% longitudinal winter-coverage gate. This sensitivity replaces it, for each reviewed resort component, with the next-nearest distinct station passing the same gate. It asks whether broad winter snow patterns are stable to a simple plausible alternative; it does not identify the best station and does not turn either station into a piste observation.

## Results

- Reviewed resort components: **15**.
- Eligible SLF stations considered: **115**.
- Components with at least eight common usable winters: **15**.
- Agreement grades: **{"high": 6, "low": 4, "moderate": 5}**.
- Median correlation of November-April mean snow depth: **0.864**.
- Median mean absolute depth difference relative to the selected-station mean: **47.2%**.
- Components whose selected and alternative linear depth trends have the same sign: **11 of 15**.

`alternative_station_agreement` is a predeclared descriptive grade: high requires correlation at least 0.75, relative mean absolute difference at most 35%, and the ≥30 cm reliability-share gap at most 0.20; moderate requires correlation at least 0.50 and relative difference at most 60%. The grade is deliberately conservative and has no causal interpretation.

## Limitations and decision

The next-nearest station is a transparent perturbation, not an elevation-, aspect-, or climatology-optimised substitute. Both stations may share regional errors or both may poorly represent a resort. Resort-top altitude is not the piste elevation distribution, and no snowmaking, grooming, wind redistribution or operating-day information is observed. The output therefore remains a robustness diagnostic; every `causal_covariate_approved` value is false. A gridded product such as ERA5-Land remains the required independent-source sensitivity.

Detailed output: `data_processed/resort_snow_alternative_station_sensitivity.csv`.
