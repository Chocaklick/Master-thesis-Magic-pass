# Same-destination municipality distance gradient

Generated reproducibly by `src/causal_inference/build_distance_gradient_diagnostic.py` following the researcher's proposed distance comparison.

## Design

For each of the **11 reviewed treated destinations**, the crosswalk compares all **186 hotel municipality series** to the same destination's component resort points. These series map to **185 distinct 2026 geometries** because the source retains both Moutier (BE), BFS 700, and Moutier (JU), BFS 6831; the former is explicitly bridged to the current BFS 6831 polygon. This yields **2,046 destination–municipality rows**. Keeping the destination fixed avoids interpreting cross-resort differences as a distance effect.

Two EPSG:2056 distances are retained:

- representative-point distance, used for common 0–15, 15–30, 30–50, 50–100 and over-100 km bands;
- minimum municipality-polygon distance, which is zero when a component point lies inside the municipality and reduces centroid distortion for large Alpine municipalities.

The seven destinations with documented continuity and 24 observed pre/post months contribute **1,302 municipality rows** to a descriptive adjacent-window diagnostic; **1,246** have at least 18 observed months in both windows. Ring summaries are in `reports/treatment_distance_ring_summary.csv`.

A direct near-versus-far diagnostic compares the median log change for municipalities at most 30 km away with municipalities beyond 50 km, leaving a 30–50 km buffer. **6 of 7 destinations** have a positive descriptive near-minus-far contrast; Moléson is the exception. These signs are exploratory and must not be called effects. The treatment-specific contrasts are in `reports/treatment_distance_near_far_contrast.csv`.

## What this can and cannot show

The output can reveal whether nearby municipalities around the same treated destination display a different descriptive post-versus-pre pattern than remote municipalities. It is a useful exposure-gradient falsification and scope diagnostic.

It is **not** a treatment-effect estimate. Current 2026 municipal geometry is applied to a 2013–2026 outcome panel; hotel coordinates, validated historical arrival-node travel times, tourism catchments and cross-destination contamination are unavailable for this diagnostic. The current NPVM zonal context is not substituted for those historical exposure measures. The adjacent windows do not remove national trends, COVID, competing passes or simultaneous investments. Every `causal_effect_estimate` and `causal_exposure_approved` flag is therefore false.

Detailed outputs: `data_processed/treatment_municipality_distance_exposure.csv` and `data_processed/treatment_distance_gradient_diagnostic.csv`.
