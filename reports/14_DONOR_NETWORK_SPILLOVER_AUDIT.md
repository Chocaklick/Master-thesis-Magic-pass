# Donor network-wide spillover audit

Generated reproducibly by `src/causal_inference/build_donor_network_spillover_audit.py`.

## Why this changes the donor screen

The earlier mechanical screen kept a donor when it was more than 30 km from the treatment under review. That is necessary but incomplete: a nominal donor can still sit next to another Magic Pass destination and receive network-related tourism spillovers. This audit therefore measures the minimum great-circle distance from every resort point in each of the 52 apparent-control municipalities to every historically or currently resolved Magic Pass resort point.

## Results

| Scope | Within 20 km | Within 30 km | Within 50 km |
|---|---:|---:|---:|
| All 52 apparent-control municipalities | 21 | 23 | 32 |
| 22 unique municipalities in the 35-pair shortlist | 10 | 11 | 17 |
| 35 shortlisted treatment-donor pairs | 14 | 15 | 28 |

The distance thresholds are sensitivity bands, not causal rules. `network_spillover_cleared_30km`, for example, means only that the supplied donor resort points are more than 30 km from every resolved Magic point. It does not establish a separate visitor market, exclude shared transport corridors, or clear pass-network and investment confounding.

## Interpretation limits

- Resolved historical/current Magic resort points are a lower bound: 26 official labels still lack approved identity equivalence.
- Resort points are not full ski-domain polygons or tourism catchments.
- Great-circle distance does not use the current NPVM zonal context and omits validated historical arrival-node travel time, shared valleys, accommodation substitution and marketing spillovers.
- Absence from a resolved link is not proof of historical non-membership.
- Competing-pass, accessibility and simultaneous-investment reviews remain pending for every donor.

No causal control is approved. Detailed outputs are `reports/donor_network_spillover_audit.csv` and `data_processed/donor_shortlist_network_audit.csv`.
