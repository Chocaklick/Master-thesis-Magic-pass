"""Compare same-destination geographic distance with scheduled transit time."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "path_c_analysis.json"
DISTANCE = ROOT / "data_processed" / "treatment_municipality_distance_exposure.csv"
JOURNEY = ROOT / "data_processed" / "treatment_municipality_public_transport_journey_context.csv"
OUTPUT = ROOT / "data_processed" / "treatment_municipality_distance_transport_comparison.csv"
CORRELATIONS = ROOT / "reports" / "distance_transport_correlations_by_destination.csv"
BANDS = ROOT / "reports" / "distance_transport_band_summary.csv"
SUMMARY = ROOT / "reports" / "distance_transport_comparison_summary.json"
REPORT = ROOT / "reports" / "28_DISTANCE_TRANSPORT_COMPARISON.md"


def rank_correlation(left: pd.Series, right: pd.Series) -> float:
    return float(left.rank(method="average").corr(right.rank(method="average")))


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    distance = pd.read_csv(DISTANCE)
    journey = pd.read_csv(JOURNEY)
    if len(distance) != 2_046 or len(journey) != 2_046:
        raise ValueError("Expected the complete 11 x 186 comparison universe")
    keys = ["destination_unit_id", "municipality_bfs_id"]
    if distance[keys].duplicated().any() or journey[keys].duplicated().any():
        raise ValueError("Distance and journey keys must be unique")

    keep_distance = keys + [
        "destination_name",
        "municipality_name",
        "boundary_bfs_id_2026",
        "boundary_bfs_bridge_status",
        "representative_point_distance_to_destination_km",
        "minimum_polygon_distance_to_destination_km",
        "representative_distance_band",
        "destination_component_inside_municipality",
        "distance_method",
        "boundary_reference_date",
    ]
    keep_journey = keys + [
        "municipality_main_stop_id",
        "municipality_main_stop_name",
        "municipality_main_stop_mode",
        "municipality_main_stop_distance_from_representative_point_km",
        "outbound_sample_coverage_share",
        "outbound_mean_generalized_elapsed_minutes",
        "return_sample_coverage_share",
        "return_mean_generalized_elapsed_minutes",
        "mean_round_trip_generalized_minutes",
        "gtfs_feed_version",
        "reference_dates",
        "historical_stability_status",
    ]
    result = distance[keep_distance].merge(
        journey[keep_journey], on=keys, how="outer", validate="one_to_one"
    )
    if len(result) != 2_046 or result[keys].isna().any().any():
        raise ValueError("Distance-transport merge lost or added pairs")

    outbound = result["outbound_mean_generalized_elapsed_minutes"].notna()
    returning = result["return_mean_generalized_elapsed_minutes"].notna()
    bidirectional = outbound & returning
    complete = (
        result["outbound_sample_coverage_share"].eq(1)
        & result["return_sample_coverage_share"].eq(1)
    )
    result["journey_comparison_status"] = "no_bidirectional_mean"
    result.loc[outbound & ~returning, "journey_comparison_status"] = "outbound_mean_only"
    result.loc[~outbound & returning, "journey_comparison_status"] = "return_mean_only"
    result.loc[bidirectional, "journey_comparison_status"] = (
        "bidirectional_means_partial_sample_coverage"
    )
    result.loc[complete, "journey_comparison_status"] = "complete_all_sampled_times"

    result["distance_rank_percentile_within_destination"] = pd.NA
    result["round_trip_time_rank_percentile_within_destination"] = pd.NA
    for _, group in result[bidirectional].groupby("destination_unit_id", observed=True):
        index = group.index
        result.loc[index, "distance_rank_percentile_within_destination"] = group[
            "representative_point_distance_to_destination_km"
        ].rank(method="average", pct=True)
        result.loc[index, "round_trip_time_rank_percentile_within_destination"] = group[
            "mean_round_trip_generalized_minutes"
        ].rank(method="average", pct=True)
    for column in [
        "distance_rank_percentile_within_destination",
        "round_trip_time_rank_percentile_within_destination",
    ]:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    result["transit_minus_distance_rank_percentile"] = (
        result["round_trip_time_rank_percentile_within_destination"]
        - result["distance_rank_percentile_within_destination"]
    )
    result["absolute_distance_transport_rank_disagreement"] = result[
        "transit_minus_distance_rank_percentile"
    ].abs()
    result["transit_materially_worse_than_distance_rank"] = result[
        "transit_minus_distance_rank_percentile"
    ].ge(0.25)
    result["transit_materially_better_than_distance_rank"] = result[
        "transit_minus_distance_rank_percentile"
    ].le(-0.25)
    result["comparison_interpretation"] = (
        "current_same_destination_distance_vs_winter_2026_scheduled_transit_"
        "diagnostic_not_historical_catchment_exposure_or_causal_effect"
    )
    result["causal_exposure_approved"] = False
    result["causal_effect_approved"] = False
    result = result.sort_values(keys, kind="stable")
    result.to_csv(OUTPUT, index=False, lineterminator="\n")

    correlation_rows = []
    for destination_id, group in result.groupby("destination_unit_id", observed=True):
        both = group[group["mean_round_trip_generalized_minutes"].notna()]
        full = group[group["journey_comparison_status"].eq("complete_all_sampled_times")]
        outbound_group = group[group["outbound_mean_generalized_elapsed_minutes"].notna()]
        return_group = group[group["return_mean_generalized_elapsed_minutes"].notna()]
        correlation_rows.append(
            {
                "destination_unit_id": destination_id,
                "destination_name": group["destination_name"].iloc[0],
                "municipality_pairs": len(group),
                "bidirectional_mean_pairs": len(both),
                "complete_all_sampled_time_pairs": len(full),
                "distance_round_trip_rank_correlation_available_pairs": (
                    rank_correlation(
                        both["representative_point_distance_to_destination_km"],
                        both["mean_round_trip_generalized_minutes"],
                    )
                    if len(both) >= 20
                    else pd.NA
                ),
                "minimum_polygon_distance_round_trip_rank_correlation_available_pairs": (
                    rank_correlation(
                        both["minimum_polygon_distance_to_destination_km"],
                        both["mean_round_trip_generalized_minutes"],
                    )
                    if len(both) >= 20
                    else pd.NA
                ),
                "distance_round_trip_rank_correlation_complete_pairs": (
                    rank_correlation(
                        full["representative_point_distance_to_destination_km"],
                        full["mean_round_trip_generalized_minutes"],
                    )
                    if len(full) >= 20
                    else pd.NA
                ),
                "distance_outbound_rank_correlation": (
                    rank_correlation(
                        outbound_group["representative_point_distance_to_destination_km"],
                        outbound_group["outbound_mean_generalized_elapsed_minutes"],
                    )
                    if len(outbound_group) >= 20
                    else pd.NA
                ),
                "distance_return_rank_correlation": (
                    rank_correlation(
                        return_group["representative_point_distance_to_destination_km"],
                        return_group["return_mean_generalized_elapsed_minutes"],
                    )
                    if len(return_group) >= 20
                    else pd.NA
                ),
                "historical_comparability_verified": False,
                "causal_exposure_approved": False,
            }
        )
    correlations = pd.DataFrame(correlation_rows).sort_values("destination_unit_id")
    correlations.to_csv(CORRELATIONS, index=False, lineterminator="\n")

    band_rows = []
    for (destination_id, band), group in result.groupby(
        ["destination_unit_id", "representative_distance_band"], observed=True
    ):
        available = group[group["mean_round_trip_generalized_minutes"].notna()]
        band_rows.append(
            {
                "destination_unit_id": destination_id,
                "destination_name": group["destination_name"].iloc[0],
                "representative_distance_band": band,
                "municipality_pairs": len(group),
                "bidirectional_mean_pairs": len(available),
                "complete_all_sampled_time_pairs": int(
                    group["journey_comparison_status"].eq("complete_all_sampled_times").sum()
                ),
                "median_representative_distance_km": float(
                    group["representative_point_distance_to_destination_km"].median()
                ),
                "median_round_trip_generalized_minutes": (
                    float(available["mean_round_trip_generalized_minutes"].median())
                    if len(available)
                    else pd.NA
                ),
                "median_outbound_generalized_minutes": (
                    float(available["outbound_mean_generalized_elapsed_minutes"].median())
                    if len(available)
                    else pd.NA
                ),
                "median_return_generalized_minutes": (
                    float(available["return_mean_generalized_elapsed_minutes"].median())
                    if len(available)
                    else pd.NA
                ),
                "causal_exposure_approved": False,
            }
        )
    pd.DataFrame(band_rows).to_csv(BANDS, index=False, lineterminator="\n")

    available_correlations = pd.to_numeric(
        correlations["distance_round_trip_rank_correlation_available_pairs"],
        errors="coerce",
    ).dropna()
    complete_correlations = pd.to_numeric(
        correlations["distance_round_trip_rank_correlation_complete_pairs"],
        errors="coerce",
    ).dropna()
    summary = {
        "analysis_version": config["analysis_version"],
        "destination_municipality_pairs": int(len(result)),
        "bidirectional_mean_pairs": int(bidirectional.sum()),
        "complete_all_sampled_time_pairs": int(complete.sum()),
        "destinations_with_bidirectional_rank_correlation": int(len(available_correlations)),
        "median_destination_distance_round_trip_rank_correlation_available_pairs": float(available_correlations.median()),
        "minimum_destination_distance_round_trip_rank_correlation_available_pairs": float(available_correlations.min()),
        "maximum_destination_distance_round_trip_rank_correlation_available_pairs": float(available_correlations.max()),
        "destinations_with_complete_pair_rank_correlation": int(len(complete_correlations)),
        "median_destination_distance_round_trip_rank_correlation_complete_pairs": float(complete_correlations.median()),
        "materially_worse_transit_than_distance_rank_pairs": int(result["transit_materially_worse_than_distance_rank"].sum()),
        "materially_better_transit_than_distance_rank_pairs": int(result["transit_materially_better_than_distance_rank"].sum()),
        "destinations_without_bidirectional_mean_pairs": correlations.loc[
            correlations["bidirectional_mean_pairs"].eq(0), "destination_unit_id"
        ].tolist(),
        "historical_comparability_verified": 0,
        "causal_exposure_or_effect_approvals": 0,
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    weakest = correlations.loc[
        correlations["distance_round_trip_rank_correlation_available_pairs"].idxmin()
    ]
    strongest = correlations.loc[
        correlations["distance_round_trip_rank_correlation_available_pairs"].idxmax()
    ]
    REPORT.write_text(
        f"""# Same-destination distance versus scheduled public transport

## Result

The comparison preserves the complete **{len(result):,} pair** universe: 11 reviewed destinations × 186 hotel municipalities. **{int(bidirectional.sum()):,} pairs** have both outbound and return means, while **{int(complete.sum()):,}** are feasible at every sampled time in both directions.

For the **{len(available_correlations)} destinations** with at least 20 bidirectional pairs, the median within-destination rank correlation between representative-point distance and mean scheduled round-trip time is **{available_correlations.median():.3f}**. It ranges from **{available_correlations.min():.3f}** for {weakest['destination_name']} to **{available_correlations.max():.3f}** for {strongest['destination_name']}. Distance is informative, but it is not interchangeable with scheduled public-transport accessibility.

Using a predeclared absolute rank-gap threshold of 0.25, **{summary['materially_worse_transit_than_distance_rank_pairs']} pairs** have materially worse transit rank than their distance rank suggests, while **{summary['materially_better_transit_than_distance_rank_pairs']}** have materially better transit rank. These are diagnostic disagreements, not causal exposure classes.

## Coverage warning

Meiringen-Hasliberg has no pair with both outbound and return means under the declared six-vehicle and 480-minute limits. Four destinations have no pair feasible at every sampled time in both directions, so complete-pair correlations are available for only **{len(complete_correlations)} destinations**. Partial-coverage correlations remain separately labelled and never replace the raw coverage fields.

## Interpretation

Distances use current 2026 municipality geometry; travel times use two winter-2026 GTFS reference days and reviewed current arrival nodes. Neither is a historical visitor catchment, observed traveller route or treatment effect. Historical comparability, causal exposure and causal-effect approvals remain false.

## Outputs

- `data_processed/treatment_municipality_distance_transport_comparison.csv`
- `reports/distance_transport_correlations_by_destination.csv`
- `reports/distance_transport_band_summary.csv`
- `reports/distance_transport_comparison_summary.json`
""",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
