# HESTA hotel-capacity integration

Generated reproducibly by `src/data_processing/build_hotel_capacity_panel.py`.

## Source and collection

The source is the official Swiss Federal Statistical Office PXWeb table `px-x-1003020000_201`, “Hôtellerie: offre et demande des établissements ouverts selon année, mois, communes et indicateur”. The collector selects all 14 years (2013–2026), all 12 calendar months, all 186 published reference municipalities, and all eight indicators. Annual totals are excluded. Because the API rejected the 248,000-cell request, the exact same selection is submitted in 14 annual chunks. Every query, response, retrieval timestamp, and SHA-256 checksum is preserved.

## Processed coverage

- Municipality-month grid rows: **31,248**
- Municipality labels with exact BFS identifiers: **186**
- Rows with establishments, rooms, and beds all observed: **29,274**
- Rows with an official bed-occupancy rate: **29,194**
- Source bed-occupancy rates above 100 retained unchanged: **59**

The literal source tokens `..` and `...` remain in companion token columns and produce missing numeric values. They are never converted to zero or imputed.

## Reconciliation with the legacy demand extraction

The live capacity table and the supplied legacy demand extraction overlap on 28,455 observed municipality-months. They match exactly except for **6 cells in 3 Davos months in 2014**. These revisions are listed in `reports/hotel_capacity_reconciliation_mismatches.csv`.

The project retains the legacy table as its primary hotel-demand outcome so historical results are not silently rewritten. Capacity-adjusted ratios use demand and capacity from the same live table version.

## Analytical use

- Establishments, rooms, and beds are time-varying supply covariates, not outcomes attributed to Magic Pass.
- `hotel_overnights_per_available_bed_month` is a descriptive intensity ratio: monthly live-table overnight stays divided by contemporaneous available beds. It is not the official occupancy rate.
- Destination capacity totals are additive only when every municipality in the reviewed scope is observed.
- Official occupancy percentages are not averaged across multi-municipality destinations because the open-room-day/open-bed-day denominators required for a correct aggregation are unavailable.
- Capacity integration reduces one confounding gap but does not resolve membership continuity, selection, COVID, weather/snow, investment, accessibility, spillovers, or donor contamination. No causal-readiness flag changes.
