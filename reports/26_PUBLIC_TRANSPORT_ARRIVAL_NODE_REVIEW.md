# Public-transport arrival-node review

## Decision

All **15** component arrival nodes pass the current descriptive review: the official stop identifier and published name still match the versioned review, the stop is bus/train-capable, it lies in the component point's current municipality, and it is no more than **2.1 km** from the supplied component coordinate. The observed maximum is **2.04 km**.

The review classes are `{"named_lift_or_ski_access_stop": 8, "village_or_local_centre_proxy": 6, "named_destination_locality_stop": 1}`. The **6** village/local-centre proxies implement the researcher's explicit fallback permission when a lift-base stop is not practical. They are not silently relabelled as lift-base access.

## Service-day warning

**14 of 15** nodes occur in both active reference-day networks. `Grimentz, Le Boccard` is absent from the Wednesday network but present on Saturday. Anniviers remains routable through its separate Chandolin component in the destination-level fastest-component calculation, but the Grimentz weekday absence stays visible in the review table.

## Limits

This is a controlled name, mode, municipality, distance and reference-day-availability review against official current OFT/BAV and GTFS data. It does not establish door-to-lift walking time, accessibility for every traveller, historical stop continuity, unchanged lines, real-time reliability or a tourism catchment. Every node is approved only for the current descriptive routing context; historical and causal approval remain false.

## Output

- `reports/public_transport_arrival_node_review.csv`
- `reports/public_transport_arrival_node_review_summary.json`
