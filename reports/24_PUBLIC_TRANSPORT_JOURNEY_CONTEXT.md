# Scheduled public-transport journey context

## Definition

This qualified context uses the checksum-verified official Swiss GTFS Static feed version **20260207**, valid from **20251214** through **20261212**. The reference dates are Wednesday **20260204** and Saturday **20260207**, both inside the winter timetable. Outbound requests are sampled every 30 minutes from 08:00 through 10:00; return requests are sampled every 30 minutes from 15:00 through 18:00. The fastest scheduled itinerary at or after each requested time is retained. `generalized_elapsed_minutes` includes initial waiting; `scheduled_journey_minutes` starts at the first vehicle boarding.

The origin for each of the **186** hotel municipalities is the train stop inside its current municipality with the highest combined reference-day departure count. If no served train stop exists, the most frequently served terrestrial stop is used. The arrival node for each reviewed destination component is the nearest served bus/train stop inside the component point's current municipality. Cableways, chairlifts and funiculars are excluded from node selection. Multi-component destinations use the fastest component for each sampled request.

## Coverage

- reviewed destination units: **11**
- component arrival nodes: **15**
- destination × municipality pairs: **2,046**
- scheduled samples: **49,104**
- feasible samples: **38,504**
- pairs complete on every outbound and return sample: **1,104 / 2,046**
- median pair mean outbound generalized time: **246.3 minutes**
- median pair mean return generalized time: **243.1 minutes**
- median pair mean round-trip generalized time: **482.1 minutes**

Municipality-node methods: `{"highest_departure_count_train_stop_inside_current_municipality": 148, "highest_departure_count_ground_stop_inside_current_municipality": 38}`. Destination-node methods: `{"nearest_served_ground_stop_inside_component_current_municipality": 15}`.

## Limits

GTFS Static represents the published schedule, not delays, cancellations, crowding, fares, snow-road disruptions or guaranteed connections. Platform identifiers are collapsed to their Swiss base stop; generic published transfers are modelled, while route/trip-specific transfer rules are reported but not separately modelled. Walking is limited to transfers present in the feed. The destination nodes are reproducible algorithmic proxies for village/valley access and still require manual face validation.

Most importantly, this is a winter-2026 reference measure. The selected Magic Pass entry seasons range across earlier years, and the historical line-stability comparison has status **`not_yet_verified_against_anchor_year_timetables`**. It is therefore a useful descriptive transport-access variable but not yet an approved pre-treatment or causal covariate. The generic `accessibility_score` and all causal effect fields remain untouched.

## Outputs

- `reports/public_transport_journey_nodes.csv`
- `data_processed/treatment_municipality_public_transport_journey_samples.csv`
- `data_processed/treatment_municipality_public_transport_journey_context.csv`
- `reports/public_transport_journey_context_summary.json`
