"""Audit cluster spread and sensitivity of current network-distance context.

The existing lift clusters are preserved. This module does not rebuild them. It
quantifies within-cluster listing-point spread and compares four transparent
between-cluster distance rules: minimum, median and maximum over every
cross-cluster listing-point pair, plus the existing distance between coordinate-
wise median listing locations. All outputs remain descriptive and unapproved.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
FEATURE_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
COMPETING_PATH = ROOT / "data_processed" / "path_c_cluster_competing_pass_context.csv"
NETWORK_PAIR_PATH = ROOT / "reports" / "path_c_cluster_network_pairs.csv"
DECISION_PATH = ROOT / "data_processed" / "magic_pass_decision_support.csv"

CONTEXT_OUTPUT = ROOT / "data_processed" / "path_c_cluster_geographic_sensitivity.csv"
PAIR_OUTPUT = ROOT / "reports" / "path_c_cluster_distance_rule_pairs.csv"
CANDIDATE_OUTPUT = ROOT / "reports" / "cluster_geography_candidate_summary.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "cluster_geography_sensitivity_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "33_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY.md"

RADII_KM = [25, 50]
INTERPRETATION = (
    "current_supplied_listing_point_cluster_spread_and_distance_rule_sensitivity_"
    "not_cluster_redefinition_historical_market_structure_or_causal_competition"
)
DISTANCE_RULES = {
    "minimum_listing_pair": "minimum",
    "median_listing_pair": "median",
    "representative_median_coordinate": "representative",
    "maximum_listing_pair": "maximum",
}


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def haversine_matrix_between(
    longitude_a: np.ndarray,
    latitude_a: np.ndarray,
    longitude_b: np.ndarray,
    latitude_b: np.ndarray,
) -> np.ndarray:
    lon_a = np.radians(longitude_a.astype(float))[:, None]
    lat_a = np.radians(latitude_a.astype(float))[:, None]
    lon_b = np.radians(longitude_b.astype(float))[None, :]
    lat_b = np.radians(latitude_b.astype(float))[None, :]
    dlon = lon_b - lon_a
    dlat = lat_b - lat_a
    value = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat_a) * np.cos(lat_b) * np.sin(dlon / 2.0) ** 2
    )
    value = np.clip(value, 0.0, 1.0)
    return 6371.0088 * 2.0 * np.arctan2(np.sqrt(value), np.sqrt(1.0 - value))


def within_cluster_distances(points: pd.DataFrame) -> np.ndarray:
    matrix = haversine_matrix_between(
        points["longitude"].to_numpy(float),
        points["latitude"].to_numpy(float),
        points["longitude"].to_numpy(float),
        points["latitude"].to_numpy(float),
    )
    return matrix[np.triu_indices(len(points), 1)]


def spread_band(listing_count: int, diameter_km: float) -> str:
    if listing_count == 1:
        return "single_listing"
    if diameter_km <= 5:
        return "multi_listing_diameter_le_5km"
    if diameter_km <= 25:
        return "multi_listing_diameter_gt_5_to_25km"
    if diameter_km <= 50:
        return "multi_listing_diameter_gt_25_to_50km"
    return "multi_listing_diameter_gt_50km"


def load_inputs() -> tuple[pd.DataFrame, dict[str, pd.DataFrame], np.ndarray]:
    resorts = pd.read_csv(RESORT_PATH)
    features = pd.read_csv(FEATURE_PATH)
    competing = pd.read_csv(COMPETING_PATH)
    required = {"resort_id", "cluster_id", "latitude", "longitude"}
    if not required.issubset(resorts.columns):
        raise ValueError(f"Missing resort fields: {sorted(required - set(resorts.columns))}")
    if len(features) != 162 or not features["cluster_id"].is_unique:
        raise ValueError("Geographic sensitivity requires 162 unique linked clusters")
    cluster_ids = features["cluster_id"].astype(str).tolist()
    resorts = resorts[resorts["cluster_id"].astype(str).isin(cluster_ids)].copy()
    if len(resorts) != 271 or not resorts["resort_id"].is_unique:
        raise ValueError("Expected all 271 unique supplied listing points")
    resorts[["latitude", "longitude"]] = resorts[["latitude", "longitude"]].apply(
        pd.to_numeric, errors="raise"
    )
    if resorts[["latitude", "longitude"]].isna().any().any():
        raise ValueError("Every supplied listing must have coordinates")
    groups = {
        cluster_id: resorts[resorts["cluster_id"].astype(str).eq(cluster_id)]
        .sort_values("resort_id")
        .reset_index(drop=True)
        for cluster_id in cluster_ids
    }
    observed_counts = pd.Series({key: len(value) for key, value in groups.items()})
    declared_counts = features.set_index("cluster_id")["listing_count"].astype(int)
    if not observed_counts.reindex(cluster_ids).equals(declared_counts.reindex(cluster_ids)):
        raise ValueError("Listing counts disagree between resort master and feature matrix")
    membership = features[["cluster_id", "resolved_current_magic_member"]].merge(
        competing[["cluster_id", "cluster_has_reviewed_competing_pass_link"]],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    reviewed_union = (
        as_bool(membership["resolved_current_magic_member"])
        | as_bool(membership["cluster_has_reviewed_competing_pass_link"])
    ).to_numpy()
    return features, groups, reviewed_union


def build_outputs(
    features: pd.DataFrame,
    groups: dict[str, pd.DataFrame],
    reviewed_union: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    n_clusters = len(features)
    cluster_ids = features["cluster_id"].astype(str).tolist()
    display_names = features["cluster_display_name"].astype(str).tolist()
    matrices = {
        "minimum": np.zeros((n_clusters, n_clusters), dtype=float),
        "median": np.zeros((n_clusters, n_clusters), dtype=float),
        "representative": np.zeros((n_clusters, n_clusters), dtype=float),
        "maximum": np.zeros((n_clusters, n_clusters), dtype=float),
    }
    representative = haversine_matrix_between(
        features["longitude_median"].to_numpy(float),
        features["latitude_median"].to_numpy(float),
        features["longitude_median"].to_numpy(float),
        features["latitude_median"].to_numpy(float),
    )
    matrices["representative"] = representative

    spread_rows: list[dict[str, object]] = []
    for index, cluster_id in enumerate(cluster_ids):
        points = groups[cluster_id]
        internal = within_cluster_distances(points)
        diameter = float(internal.max()) if len(internal) else 0.0
        coordinate_pairs = points[["latitude", "longitude"]].drop_duplicates()
        centre_distance = haversine_matrix_between(
            points["longitude"].to_numpy(float),
            points["latitude"].to_numpy(float),
            np.array([float(features.iloc[index]["longitude_median"])]),
            np.array([float(features.iloc[index]["latitude_median"])]),
        )[:, 0]
        spread_rows.append(
            {
                "cluster_id": cluster_id,
                "cluster_display_name": display_names[index],
                "candidate_for_path_c": features.iloc[index]["candidate_for_path_c"],
                "cluster_listing_point_count": len(points),
                "cluster_unique_coordinate_count": len(coordinate_pairs),
                "within_cluster_listing_pair_count": len(internal),
                "within_cluster_pairwise_distance_min_km": (
                    float(internal.min()) if len(internal) else 0.0
                ),
                "within_cluster_pairwise_distance_median_km": (
                    float(np.median(internal)) if len(internal) else 0.0
                ),
                "within_cluster_pairwise_distance_max_km": diameter,
                "maximum_listing_distance_from_representative_median_coordinate_km": float(
                    centre_distance.max()
                ),
                "cluster_listing_geographic_spread_band": spread_band(len(points), diameter),
                "cluster_geographic_coherence_verified": False,
                "network_distance_sensitivity_feature_approved": False,
                "cluster_geography_sensitivity_interpretation": INTERPRETATION,
                "cluster_geography_sensitivity_source_ids": (
                    "DERIVED_RESORT_MASTER|DERIVED_PATH_C_FEATURE_MATRIX|"
                    "DERIVED_COMPETING_PASS_CONTEXT"
                ),
            }
        )

    pair_rows: list[dict[str, object]] = []
    for focal_index in range(n_clusters):
        focal_points = groups[cluster_ids[focal_index]]
        for other_index in range(focal_index + 1, n_clusters):
            other_points = groups[cluster_ids[other_index]]
            cross = haversine_matrix_between(
                focal_points["longitude"].to_numpy(float),
                focal_points["latitude"].to_numpy(float),
                other_points["longitude"].to_numpy(float),
                other_points["latitude"].to_numpy(float),
            )
            minimum = float(cross.min())
            median = float(np.median(cross))
            maximum = float(cross.max())
            matrices["minimum"][focal_index, other_index] = minimum
            matrices["minimum"][other_index, focal_index] = minimum
            matrices["median"][focal_index, other_index] = median
            matrices["median"][other_index, focal_index] = median
            matrices["maximum"][focal_index, other_index] = maximum
            matrices["maximum"][other_index, focal_index] = maximum
            for left, right in ((focal_index, other_index), (other_index, focal_index)):
                pair_rows.append(
                    {
                        "focal_cluster_id": cluster_ids[left],
                        "focal_cluster_name": display_names[left],
                        "other_cluster_id": cluster_ids[right],
                        "other_cluster_name": display_names[right],
                        "cross_cluster_listing_pair_count": int(cross.size),
                        "minimum_listing_pair_distance_km": minimum,
                        "median_listing_pair_distance_km": median,
                        "representative_median_coordinate_distance_km": float(
                            representative[left, right]
                        ),
                        "maximum_listing_pair_distance_km": maximum,
                        "absolute_representative_vs_listing_pair_median_difference_km": abs(
                            float(representative[left, right]) - median
                        ),
                        "other_cluster_in_reviewed_pass_network": bool(reviewed_union[right]),
                        "cluster_geography_sensitivity_interpretation": INTERPRETATION,
                        "network_distance_sensitivity_feature_approved": False,
                    }
                )

    context = pd.DataFrame(spread_rows)
    pair_frame = pd.DataFrame(pair_rows)
    for focal_index in range(n_clusters):
        other = np.ones(n_clusters, dtype=bool)
        other[focal_index] = False
        for radius in RADII_KM:
            directory_counts: list[int] = []
            network_counts: list[int] = []
            for output_rule, matrix_key in DISTANCE_RULES.items():
                within = other & (matrices[matrix_key][focal_index] <= radius)
                directory_count = int(within.sum())
                network_count = int((within & reviewed_union).sum())
                directory_counts.append(directory_count)
                network_counts.append(network_count)
                context.loc[
                    focal_index,
                    f"other_directory_clusters_within_{radius}km_by_{output_rule}_distance",
                ] = directory_count
                context.loc[
                    focal_index,
                    f"other_reviewed_pass_network_clusters_within_{radius}km_by_{output_rule}_distance",
                ] = network_count
            context.loc[
                focal_index, f"directory_cluster_count_distance_rule_span_within_{radius}km"
            ] = max(directory_counts) - min(directory_counts)
            context.loc[
                focal_index,
                f"reviewed_pass_network_count_distance_rule_span_within_{radius}km",
            ] = max(network_counts) - min(network_counts)
            context.loc[
                focal_index, f"directory_cluster_count_stable_across_distance_rules_within_{radius}km"
            ] = len(set(directory_counts)) == 1
            context.loc[
                focal_index,
                f"reviewed_pass_network_count_stable_across_distance_rules_within_{radius}km",
            ] = len(set(network_counts)) == 1

    count_columns = [column for column in context if "clusters_within_" in column or "_span_" in column]
    context[count_columns] = context[count_columns].astype(int)
    if len(pair_frame) != n_clusters * (n_clusters - 1):
        raise ValueError("Distance-rule pair table lost the ordered non-self grain")
    if pair_frame[["focal_cluster_id", "other_cluster_id"]].duplicated().any():
        raise ValueError("Distance-rule pair table contains duplicate ordered pairs")
    if (pair_frame["focal_cluster_id"] == pair_frame["other_cluster_id"]).any():
        raise ValueError("Distance-rule pair table contains a self pair")
    if not (
        pair_frame["minimum_listing_pair_distance_km"]
        <= pair_frame["median_listing_pair_distance_km"] + 1e-12
    ).all() or not (
        pair_frame["median_listing_pair_distance_km"]
        <= pair_frame["maximum_listing_pair_distance_km"] + 1e-12
    ).all():
        raise ValueError("Minimum, median and maximum distance rules are not ordered")

    existing_pairs = pd.read_csv(NETWORK_PAIR_PATH)[
        ["focal_cluster_id", "other_cluster_id", "great_circle_distance_km"]
    ]
    check = pair_frame.merge(
        existing_pairs,
        on=["focal_cluster_id", "other_cluster_id"],
        how="left",
        validate="one_to_one",
    )
    if check["great_circle_distance_km"].isna().any() or not np.allclose(
        check["representative_median_coordinate_distance_km"],
        check["great_circle_distance_km"],
        atol=1e-10,
    ):
        raise ValueError("Representative distances do not reproduce the v0.14 pair table")
    return context, pair_frame


def enrich_decision_support(context: pd.DataFrame, analysis_version: str) -> None:
    decision = pd.read_csv(DECISION_PATH)
    append_columns = [
        column
        for column in context.columns
        if column not in {"cluster_id", "cluster_display_name", "candidate_for_path_c"}
    ]
    decision = decision.drop(
        columns=[column for column in append_columns if column in decision.columns]
    ).merge(
        context[["cluster_id", *append_columns]],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    decision["analysis_version"] = analysis_version
    guarded = [
        "accessibility_score",
        "predicted_uplift_pct",
        "uplift_lower_pct",
        "uplift_upper_pct",
        "composite_opportunity_need_score",
    ]
    populated = [column for column in guarded if decision[column].notna().any()]
    if populated:
        raise ValueError(f"Unapproved decision fields became populated: {populated}")
    if as_bool(decision["network_distance_sensitivity_feature_approved"]).any():
        raise ValueError("Network-distance sensitivity was unexpectedly approved")
    DECISION_PATH.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    features, groups, reviewed_union = load_inputs()
    context, pairs = build_outputs(features, groups, reviewed_union)
    context.to_csv(CONTEXT_OUTPUT, index=False, lineterminator="\n")
    pairs.sort_values(
        ["focal_cluster_id", "median_listing_pair_distance_km", "other_cluster_id"]
    ).to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")
    enrich_decision_support(context, str(config["analysis_version"]))

    candidates = context[as_bool(context["candidate_for_path_c"])].copy()
    candidate_columns = [
        "cluster_id",
        "cluster_display_name",
        "cluster_listing_point_count",
        "within_cluster_pairwise_distance_median_km",
        "within_cluster_pairwise_distance_max_km",
        "cluster_listing_geographic_spread_band",
        "directory_cluster_count_distance_rule_span_within_25km",
        "directory_cluster_count_distance_rule_span_within_50km",
        "reviewed_pass_network_count_distance_rule_span_within_25km",
        "reviewed_pass_network_count_distance_rule_span_within_50km",
        "cluster_geographic_coherence_verified",
        "network_distance_sensitivity_feature_approved",
    ]
    candidates.sort_values(
        [
            "directory_cluster_count_distance_rule_span_within_25km",
            "reviewed_pass_network_count_distance_rule_span_within_50km",
            "within_cluster_pairwise_distance_max_km",
            "cluster_id",
        ],
        ascending=[False, False, False, True],
    )[candidate_columns].to_csv(CANDIDATE_OUTPUT, index=False, lineterminator="\n")

    multi = context[context["cluster_listing_point_count"].gt(1)]
    pair_unique = pairs[
        pairs["focal_cluster_id"].astype(str) < pairs["other_cluster_id"].astype(str)
    ]
    listing_counts = context.set_index("cluster_id")["cluster_listing_point_count"]
    pair_unique_involving_multi_listing_cluster = pair_unique[
        pair_unique["focal_cluster_id"].map(listing_counts).gt(1)
        | pair_unique["other_cluster_id"].map(listing_counts).gt(1)
    ]
    summary: dict[str, object] = {
        "analysis_version": config["analysis_version"],
        "linked_clusters": len(context),
        "ordered_nonself_cluster_pairs": len(pairs),
        "single_listing_clusters": int(context["cluster_listing_point_count"].eq(1).sum()),
        "multi_listing_clusters": len(multi),
        "cluster_spread_band_counts": {
            str(key): int(value)
            for key, value in context["cluster_listing_geographic_spread_band"]
            .value_counts()
            .sort_index()
            .items()
        },
        "median_multi_listing_cluster_diameter_km": float(
            multi["within_cluster_pairwise_distance_max_km"].median()
        ),
        "maximum_cluster_diameter_km": float(
            context["within_cluster_pairwise_distance_max_km"].max()
        ),
        "maximum_cluster_diameter_cluster_id": str(
            context.loc[
                context["within_cluster_pairwise_distance_max_km"].idxmax(), "cluster_id"
            ]
        ),
        "clusters_with_diameter_gt_25km": int(
            context["within_cluster_pairwise_distance_max_km"].gt(25).sum()
        ),
        "median_absolute_representative_vs_listing_pair_median_difference_km": float(
            pair_unique[
                "absolute_representative_vs_listing_pair_median_difference_km"
            ].median()
        ),
        "p95_absolute_representative_vs_listing_pair_median_difference_km": float(
            pair_unique[
                "absolute_representative_vs_listing_pair_median_difference_km"
            ].quantile(0.95)
        ),
        "unique_cluster_pairs_involving_multi_listing_cluster": len(
            pair_unique_involving_multi_listing_cluster
        ),
        "median_absolute_representative_vs_listing_pair_median_difference_for_multi_involved_pairs_km": float(
            pair_unique_involving_multi_listing_cluster[
                "absolute_representative_vs_listing_pair_median_difference_km"
            ].median()
        ),
        "p95_absolute_representative_vs_listing_pair_median_difference_for_multi_involved_pairs_km": float(
            pair_unique_involving_multi_listing_cluster[
                "absolute_representative_vs_listing_pair_median_difference_km"
            ].quantile(0.95)
        ),
        "path_c_candidates": len(candidates),
        "candidates_with_directory_count_sensitivity_within_25km": int(
            candidates["directory_cluster_count_distance_rule_span_within_25km"].gt(0).sum()
        ),
        "candidates_with_directory_count_sensitivity_within_50km": int(
            candidates["directory_cluster_count_distance_rule_span_within_50km"].gt(0).sum()
        ),
        "candidates_with_reviewed_pass_network_count_sensitivity_within_25km": int(
            candidates[
                "reviewed_pass_network_count_distance_rule_span_within_25km"
            ].gt(0).sum()
        ),
        "candidates_with_reviewed_pass_network_count_sensitivity_within_50km": int(
            candidates[
                "reviewed_pass_network_count_distance_rule_span_within_50km"
            ].gt(0).sum()
        ),
        "maximum_candidate_directory_count_span_within_25km": int(
            candidates["directory_cluster_count_distance_rule_span_within_25km"].max()
        ),
        "maximum_candidate_reviewed_pass_network_count_span_within_50km": int(
            candidates[
                "reviewed_pass_network_count_distance_rule_span_within_50km"
            ].max()
        ),
        "cluster_geographic_coherence_verified": 0,
        "approved_features": 0,
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    bands = summary["cluster_spread_band_counts"]
    report = f"""# Path C cluster geography and network-distance sensitivity

## Scope

This audit preserves the existing **{len(context)} lift clusters** and their **271 supplied listing points**. It does not rebuild or certify the clustering. For each cluster it measures the full within-cluster listing-point spread. For every one of the **{len(pairs):,} ordered non-self cluster pairs**, it compares:

- minimum distance across all cross-cluster listing-point pairs (at least one point pair is this close);
- median distance across all cross-cluster listing-point pairs;
- the v0.14 distance between coordinate-wise median listing locations;
- maximum distance across all cross-cluster listing-point pairs (all point pairs are within a radius only when this value is within it).

## Within-cluster spread

- single-listing clusters: **{summary['single_listing_clusters']}**
- multi-listing clusters: **{summary['multi_listing_clusters']}**
- multi-listing diameter at most 5 km: **{bands.get('multi_listing_diameter_le_5km', 0)}**
- multi-listing diameter above 5 and at most 25 km: **{bands.get('multi_listing_diameter_gt_5_to_25km', 0)}**
- clusters with diameter above 25 km: **{summary['clusters_with_diameter_gt_25km']}**
- median multi-listing diameter: **{summary['median_multi_listing_cluster_diameter_km']:.2f} km**
- maximum diameter: **{summary['maximum_cluster_diameter_km']:.2f} km** for `{summary['maximum_cluster_diameter_cluster_id']}`

## Candidate sensitivity

Among **{len(candidates)} apparent Path C candidates**, the directory-neighbour count changes across the four distance rules for **{summary['candidates_with_directory_count_sensitivity_within_25km']}** candidates at 25 km and **{summary['candidates_with_directory_count_sensitivity_within_50km']}** at 50 km. The reviewed pass-network count changes for **{summary['candidates_with_reviewed_pass_network_count_sensitivity_within_25km']}** candidates at 25 km and **{summary['candidates_with_reviewed_pass_network_count_sensitivity_within_50km']}** at 50 km. The largest candidate spans are **{summary['maximum_candidate_directory_count_span_within_25km']}** directory clusters at 25 km and **{summary['maximum_candidate_reviewed_pass_network_count_span_within_50km']}** reviewed-network clusters at 50 km.

Across all unique cluster pairs, the absolute difference between the coordinate-wise-median distance and the median listing-pair distance is **{summary['median_absolute_representative_vs_listing_pair_median_difference_km']:.2f} km** at the median and **{summary['p95_absolute_representative_vs_listing_pair_median_difference_km']:.2f} km** at the 95th percentile. The all-pair median is zero because most clusters contain one listing. Restricting to the **{summary['unique_cluster_pairs_involving_multi_listing_cluster']:,} pairs involving at least one multi-listing cluster**, the median is **{summary['median_absolute_representative_vs_listing_pair_median_difference_for_multi_involved_pairs_km']:.2f} km** and the 95th percentile is **{summary['p95_absolute_representative_vs_listing_pair_median_difference_for_multi_involved_pairs_km']:.2f} km**.

## Interpretation limit

Minimum distance is permissive, maximum distance is conservative, and neither is a uniquely correct destination-market definition. The supplied listings may be components of one product, neighbouring products, or directory labels at a different commercial grain. Coordinate-wise medians can fall between actual places. Straight-line distance still ignores terrain, roads, timetables, skier substitution and historical changes. Therefore `cluster_geographic_coherence_verified` and `network_distance_sensitivity_feature_approved` remain false everywhere. No cluster is reassigned, and no causal, uplift, accessibility or composite score is populated.

## Outputs

- `data_processed/path_c_cluster_geographic_sensitivity.csv`
- `reports/path_c_cluster_distance_rule_pairs.csv`
- `reports/cluster_geography_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified sensitivity fields appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
