# Destination-unit and municipality outcome review

Generated reproducibly by `src/data_processing/build_treatment_destination_panel.py` from the versioned review configuration and cached official evidence.

## Decision

The 18 candidate Magic Pass entry/outcome links represent **14 reviewed destination units**, not 18 independent treatments. **11 units** have an explicit municipality outcome scope and enter the diagnostic panel. **3 composite units** are excluded because the supplied OFS hotel panel does not cover their complete reviewed geography.

This review approves an outcome aggregation, not a causal exposure. Every destination and month remains `causal_ready = false` until membership continuity, confounding, spillovers, and untreated controls are audited.

## Unit decisions

| Destination unit | Entry events | Outcome municipalities | Review status | Observed pre months | Active post months under assumption |
|---|---:|---|---|---:|---:|
| Anniviers Magic Pass portfolio | 2 | Anniviers | approved_complete_observed_municipal_scope | 58 | 99 |
| Axalp | 1 | Brienz (BE) | approved_core_municipality_proxy | 112 | 47 |
| Bumbach | 1 | Schangnau | approved_core_municipality_proxy | 122 | 35 |
| Crans-Montana | 1 | Crans-Montana | approved_core_municipality_proxy | 10 | 30 |
| Espace Dent Blanche | 3 | Evolène | approved_complete_observed_municipal_scope | 64 | 93 |
| Bergbahnen Destination Gstaad | 1 | Saanen | excluded_incomplete_composite_outcome_scope | — | — |
| Les Pléiades | 1 | Blonay - Saint-Légier | approved_core_municipality_proxy | 0 | 51 |
| Meiringen-Hasliberg | 1 | Hasliberg<br>Meiringen | approved_complete_observed_municipal_scope | 146 | 11 |
| Moléson | 1 | Gruyères | approved_core_municipality_proxy | 58 | 99 |
| Reichenbach im Kandertal Magic Pass portfolio | 2 | Reichenbach im Kandertal | approved_complete_observed_municipal_scope | 110 | 47 |
| Saas-Fee | 1 | Saas-Fee | approved_core_municipality_proxy | 76 | 83 |
| Sainte-Croix / Les Rasses | 1 | Bullet | excluded_incomplete_composite_outcome_scope | — | — |
| Schwanden | 1 | Sigriswil | approved_core_municipality_proxy | 136 | 23 |
| Villars-Gryon-Les Diablerets | 1 | Ollon<br>Ormont-Dessus | excluded_incomplete_composite_outcome_scope | — | — |

## Aggregation rules

- Resort point containment remains a geographic fact only. It is copied to `data_processed/resort_municipality_crosswalk.csv` with causal exposure set to false.
- Municipality hotel-night counts are additive. Each included municipality has weight 1.0; weights are not normalised into shares.
- A destination-month aggregate is missing unless every municipality in its approved scope has an observed value.
- Establishments, rooms and beds are summed across the reviewed municipal scope only when every municipality is observed. `hotel_overnights_per_available_bed_month` uses the contemporaneous demand and bed capacity from the same live HESTA table.
- Official occupancy percentages are retained for single-municipality destinations only. They are not averaged across multi-municipality destinations because the required open-bed-day denominator is unavailable.
- Snow fields are external mountain-station proxies from the nearest longitudinally complete SLF IMIS station(s), not direct observations on the pistes. Distance, elevation gap, station coverage and proxy quality are retained in separate crosswalks; missing station months are not imputed.
- Anniviers and Espace Dent Blanche collapse multiple same-season resort labels to one municipal outcome. Reichenbach im Kandertal has one municipal outcome with a later treatment-intensity increment when Kiental enters.
- Meiringen-Hasliberg sums Hasliberg and Meiringen. Villars-Gryon-Les Diablerets, Sainte-Croix / Les Rasses, and Bergbahnen Destination Gstaad are excluded because the hotel panel only observes part of their reviewed composite scope.

## Timing and remaining gate

The 2017-11 anchor is the documented first-pass validity date. Later 1 May values are monthly analytical anchors unless the operator documents the exact date. The diagnostic panel carries entry forward until a documented exit; Crans-Montana is switched off after 2020-04. This continuity convention is an assumption, not evidence.

Under that assumption, **7 units** have at least 24 observed pre and active-post months and **6** have at least 36. These are coverage counts only. The causal-treatment count remains **zero**.
