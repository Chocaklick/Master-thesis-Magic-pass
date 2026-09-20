# Initial data audit — completed Checkpoint 1

The original initialization found no datasets. The researcher subsequently supplied 11 immutable files in `data_raw/`; this report now reflects the reproducible content audit. Exact schemas, column profiles, missing counts, examples, suspicious tokens, and SHA-256 hashes are in `reports/data_audit_details.json`, `reports/data_audit.csv`, and `metadata/raw_file_manifest.csv`.

## Inventory summary

| Data family | Files / rows | Main grain | Main finding |
|---|---:|---|---|
| Winter lift geometry | 1 GPKG / 1,805 lifts | lift geometry | All geometries valid; stable `fid` and `tlm_uuid` fields present |
| Resort directory and normalised listings | 3 CSVs / 271 listings each where applicable | resort listing | Stable `ski_id` retained as `resort_id`; listings are not yet validated independent domains |
| Existing cluster products | 3 tabular/GeoJSON files / 242 clusters | lift cluster | 1,805 lift memberships are unique; 162 clusters receive a listing assignment |
| Hotel statistics | 1 CSV / 33,852 rows / 149 columns | municipality × year × annual/month × origin × measure (wide) | 186 municipality labels, 2013–2026 grid, monthly and annual totals |
| Legacy HTML maps | 2 files | embedded research outputs | Useful as legacy evidence only; not authoritative source data |

## Hotel outcome audit

- The official table definition is hotel arrivals and overnight stays in open establishments, by municipality, month, origin, and indicator.
- The source contains 31,248 monthly grid rows and 2,604 annual rows. Annual rows are excluded from the analytical monthly table.
- There are 28,455 observed monthly total-night values. Observations run from January 2013 through March 2026; later 2026 grid months are unavailable rather than observed zeros.
- The total-night field contains 2,793 literal `...` cells. They remain missing; no zero fill or imputation is applied.
- Across all 146 measure columns, the non-numeric tokens are `...` (624,654 cells), `a` (one cell), and `-3` (two cells). These are preserved in raw source-token columns or the immutable source.
- Annual totals agree with the sum of the twelve monthly values in every complete municipality-year.
- The source has municipality labels but the existing extract does not retain BFS IDs. Current code-label pairs are taken from separately cached official OFS metadata.

## Resort and join-key audit

- `resort_id`/`ski_id`, `cluster_id`, source URLs, coordinates, and lift `fid` are the strongest current keys.
- Resort-directory URLs are unique, and the 271 normalised listings join one-to-one to the assignment table.
- Fifty-three clusters contain more than one resort listing; 80 clusters are unnamed. A listing therefore cannot be treated automatically as an independent destination.
- All original resort `commune` fields are empty. The legacy overnight-stay map contains 69 name overlaps but no defensible resort-to-municipality exposure weights.

## Missing information after Checkpoint 1

1. A reviewed independent destination/domain definition.
2. A complete historical Magic Pass membership and exit audit.
3. A tourism-exposure crosswalk from destinations to one or more municipalities, including weights and shared-market rules.
4. Historical municipality-boundary handling for the hotel panel.
5. Hotel capacity, snow/climate, accessibility, population, tourism-dependence, investment, and network variables.
6. Upstream retrieval dates for the supplied Bergfex and hotel extracts and the precise original source/version of the lift GPKG.

Checkpoint 1 is complete as an audit. It does not authorize causal modelling.
