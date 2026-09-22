# NPVM municipality-constrained zone-proxy audit

## Geometric reconstruction

All **98** proxy assignments are reproduced from the checksum-verified NPVM and current municipality geometries. In every case, the stored zone is the nearest NPVM zone with a positive-area intersection with the point's independently resolved current municipality, the stored distance matches the recomputed distance, and the overlap area is positive.

Proxy distance is at most **3.64 km** and has a median of **0.64 km**. Distance-band counts are `{"gt_0_to_0_5_km": 38, "gt_0_5_to_1_km": 35, "gt_1_to_2_km": 19, "gt_2_km": 6}`. These bands are diagnostics, not quality or causal approval classes.

## Dependence and sensitivity

**73** clusters use at least one proxy. **50** have no exactly contained listing point, so the NPVM context for those clusters cannot be checked against an internal exact-only value. This includes **28** apparent Path C candidates. The remaining **23** mixed clusters permit a limited aggregation sensitivity comparison.

For public-transport time to a major centre, the absolute difference between the all-usable median and exact-only median is **2.0 minutes** at the median, **11.3 minutes** at p90 and **20.0 minutes** at maximum. This does not validate proxy-only clusters; it only exposes observed sensitivity where exact and proxy listings coexist.

## Decision

The geometry and deterministic selection logic are validated, but the proxy is still not an observed trip origin, live route, winter-service guarantee or historical zone-lineage match. Historical lineage and transport-accessibility approval therefore remain false. No generic accessibility or composite score is populated.

## Outputs

- `reports/transport_zone_proxy_audit.csv`
- `reports/transport_zone_proxy_audit_summary.json`
