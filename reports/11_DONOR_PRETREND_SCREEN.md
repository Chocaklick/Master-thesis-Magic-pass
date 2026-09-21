# Donor pre-trend comparability screen

## Result

The screen ranks 315 provisional treatment-donor pairs for the seven reviewed units that combine complete annual membership evidence with 24 observed pre and post months. It retains 35 top-five pairs for manual evidence review. **Zero controls are causally approved.**

The score is an equal-weight average of within-treatment percentile ranks for pre-period hotel-demand level, deseasonalized trend, seasonal profile, standardized outcome shape, available-bed scale, geographic distance, resort-top altitude, ski-area size and lift count. Missing structural fields are skipped, and at least six components plus 30 of the 36 pre-window outcome months are required. Current directory features are descriptive and may not represent historical capacity.

## Shortlist

| Treatment | Rank | Provisional donor municipality | Score | Distance km | Paired pre months | Log-outcome correlation | COVID-sensitivity months in pre-window |
|---|---:|---|---:|---:|---:|---:|---:|
| Anniviers Magic Pass portfolio | 1 | Celerina/Schlarigna | 80.42 | 171.8 | 36 | 0.847 | 0 |
| Anniviers Magic Pass portfolio | 2 | Andermatt | 78.04 | 86.6 | 36 | 0.832 | 0 |
| Anniviers Magic Pass portfolio | 3 | Laax | 75.93 | 140.1 | 36 | 0.794 | 0 |
| Anniviers Magic Pass portfolio | 4 | Tujetsch | 74.87 | 96.7 | 36 | 0.661 | 0 |
| Anniviers Magic Pass portfolio | 5 | Lauterbrunnen | 71.03 | 40.5 | 36 | 0.603 | 0 |
| Axalp | 1 | Glarus Süd | 73.67 | 76.8 | 36 | 0.608 | 26 |
| Axalp | 2 | Orsières | 72.46 | 104.8 | 36 | 0.648 | 26 |
| Axalp | 3 | Morschach | 68.24 | 55.3 | 36 | 0.626 | 26 |
| Axalp | 4 | Breil/Brigels | 67.39 | 79.2 | 36 | 0.454 | 26 |
| Axalp | 5 | Glarus Nord | 66.79 | 89.6 | 36 | 0.762 | 26 |
| Bumbach | 1 | Gonten | 77.07 | 122.7 | 35 | 0.332 | 24 |
| Bumbach | 2 | Küssnacht (SZ) | 74.35 | 52.8 | 35 | 0.067 | 24 |
| Bumbach | 3 | Amden | 74.00 | 103.2 | 35 | 0.293 | 24 |
| Bumbach | 4 | La Chaux-de-Fonds | 73.52 | 84.5 | 35 | 0.088 | 24 |
| Bumbach | 5 | Rheinwald | 73.29 | 113.1 | 34 | 0.335 | 24 |
| Espace Dent Blanche | 1 | Saas-Grund | 76.39 | 34.2 | 36 | 0.849 | 0 |
| Espace Dent Blanche | 2 | Val Müstair | 66.16 | 224.0 | 36 | 0.696 | 0 |
| Espace Dent Blanche | 3 | Breil/Brigels | 65.40 | 142.2 | 36 | 0.660 | 0 |
| Espace Dent Blanche | 4 | Tujetsch | 65.40 | 111.2 | 36 | 0.743 | 0 |
| Espace Dent Blanche | 5 | Andermatt | 62.75 | 101.1 | 36 | 0.694 | 0 |
| Moléson | 1 | Orsières | 72.10 | 58.5 | 36 | 0.548 | 0 |
| Moléson | 2 | Amden | 69.95 | 175.2 | 36 | 0.651 | 0 |
| Moléson | 3 | Gonten | 63.51 | 194.6 | 36 | 0.711 | 0 |
| Moléson | 4 | Morschach | 62.12 | 133.5 | 36 | 0.385 | 0 |
| Moléson | 5 | Breil/Brigels | 61.62 | 159.1 | 36 | 0.138 | 0 |
| Reichenbach im Kandertal Magic Pass portfolio | 1 | Bulle | 84.54 | 50.3 | 34 | 0.732 | 26 |
| Reichenbach im Kandertal Magic Pass portfolio | 2 | La Chaux-de-Fonds | 80.92 | 82.6 | 34 | 0.707 | 26 |
| Reichenbach im Kandertal Magic Pass portfolio | 3 | Glarus Nord | 78.86 | 115.8 | 34 | 0.820 | 26 |
| Reichenbach im Kandertal Magic Pass portfolio | 4 | Küssnacht (SZ) | 78.38 | 74.9 | 34 | 0.848 | 26 |
| Reichenbach im Kandertal Magic Pass portfolio | 5 | Einsiedeln | 76.81 | 95.8 | 34 | 0.830 | 26 |
| Saas-Fee | 1 | Celerina/Schlarigna | 77.29 | 153.3 | 36 | 0.798 | 0 |
| Saas-Fee | 2 | Adelboden | 76.93 | 47.1 | 36 | 0.833 | 0 |
| Saas-Fee | 3 | Laax | 75.85 | 130.4 | 36 | 0.717 | 0 |
| Saas-Fee | 4 | Lenk | 74.03 | 54.6 | 36 | 0.655 | 0 |
| Saas-Fee | 5 | Samnaun | 73.91 | 212.4 | 36 | 0.841 | 0 |

## Interpretation limits

- The input already excludes resolved Magic Pass links, conservative scope relations, the treated outcome scope and resort points within 30 km. The newly resolved Sattel-Hochstuckli link is therefore excluded before ranking.
- A high score is a prioritisation signal, not evidence of parallel trends or a valid untreated counterfactual. The score is relative within each treatment and must not be compared across treatments.
- The 36-month pre-window overlaps the analyst-defined March 2020–April 2022 COVID sensitivity interval for 3 of seven treatments. These cases need full-sample and COVID-exclusion sensitivity specifications.
- Spatial spillovers can extend beyond 30 km; road travel time, shared valleys, marketing networks and accommodation catchments are not yet measured.
- Historical membership for apparent donors, simultaneous investment, accessibility, snowmaking, local economic conditions and competing passes still require explicit review.

The complete pair-level output is `data_processed/donor_pretrend_comparability.csv`; the compact shortlist is `reports/donor_pretrend_shortlist.csv`.
