"""Build current directory-cluster and reviewed pass-network proximity context.

Distances use the median coordinates already retained for the 162 preserved lift
clusters. All neighbourhood statistics exclude the focal cluster itself. They are
current descriptive diagnostics, not historical market structure, visitor flows,
travel impedance, independent-domain counts or causal competition features.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
FEATURE_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
COMPETING_PATH = ROOT / "data_processed" / "path_c_cluster_competing_pass_context.csv"
DECISION_PATH = ROOT / "data_processed" / "magic_pass_decision_support.csv"
CONTEXT_OUTPUT = ROOT / "data_processed" / "path_c_cluster_network_context.csv"
PAIR_OUTPUT = ROOT / "reports" / "path_c_cluster_network_pairs.csv"
CANDIDATE_OUTPUT = ROOT / "reports" / "network_context_candidate_summary.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "network_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "32_PATH_C_NETWORK_CONTEXT.md"

RADII_KM = [25, 50]
INTERPRETATION = (
    "current_supplied_directory_cluster_and_reviewed_pass_network_straight_line_"
    "context_not_historical_market_structure_travel_time_or_causal_competition"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def haversine_matrix(longitude: np.ndarray, latitude: np.ndarray) -> np.ndarray:
    longitude_radians = np.radians(longitude.astype(float))
    latitude_radians = np.radians(latitude.astype(float))
    longitude_difference = longitude_radians[None, :] - longitude_radians[:, None]
    latitude_difference = latitude_radians[None, :] - latitude_radians[:, None]
    value = (
        np.sin(latitude_difference / 2.0) ** 2
        + np.cos(latitude_radians[:, None])
        * np.cos(latitude_radians[None, :])
        * np.sin(longitude_difference / 2.0) ** 2
    )
    value = np.clip(value, 0.0, 1.0)
    return 6371.0088 * 2.0 * np.arctan2(np.sqrt(value), np.sqrt(1.0 - value))


def nearest_other(
    distances: np.ndarray,
    mask: np.ndarray,
    focal_index: int,
    clusters: pd.DataFrame,
) -> tuple[float, str, str]:
    eligible = mask.copy()
    eligible[focal_index] = False
    positions = np.flatnonzero(eligible)
    if not len(positions):
        return np.nan, "", ""
    local_position = int(np.argmin(distances[focal_index, positions]))
    nearest_position = int(positions[local_position])
    return (
        float(distances[focal_index, nearest_position]),
        str(clusters.iloc[nearest_position]["cluster_id"]),
        str(clusters.iloc[nearest_position]["cluster_display_name"]),
    )


def safe_share(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else np.nan


def build_context(features: pd.DataFrame, competing: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    columns = [
        "cluster_id",
        "cluster_display_name",
        "candidate_for_path_c",
        "latitude_median",
        "longitude_median",
        "listing_count",
        "ski_area_km_median",
        "resolved_current_magic_member",
    ]
    clusters = features[columns].merge(
        competing[
            [
                "cluster_id",
                "cluster_has_reviewed_competing_pass_link",
                "cluster_limited_partner_benefit_listing_count",
                "cluster_core_or_included_region_listing_count",
            ]
        ],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    if len(clusters) != 162 or clusters["cluster_id"].duplicated().any():
        raise ValueError("Network context requires exactly 162 unique linked clusters")
    numeric_coordinates = clusters[["longitude_median", "latitude_median"]].apply(
        pd.to_numeric, errors="raise"
    )
    if numeric_coordinates.isna().any().any():
        raise ValueError("Every linked cluster must have a median coordinate")
    distances = haversine_matrix(
        numeric_coordinates["longitude_median"].to_numpy(),
        numeric_coordinates["latitude_median"].to_numpy(),
    )
    if not np.allclose(distances, distances.T, atol=1e-10) or not np.allclose(
        np.diag(distances), 0.0, atol=1e-10
    ):
        raise ValueError("Invalid symmetric cluster distance matrix")

    all_clusters = np.ones(len(clusters), dtype=bool)
    magic_clusters = as_bool(clusters["resolved_current_magic_member"]).to_numpy()
    competing_clusters = as_bool(
        clusters["cluster_has_reviewed_competing_pass_link"]
    ).to_numpy()
    limited_partner_clusters = (
        pd.to_numeric(clusters["cluster_limited_partner_benefit_listing_count"], errors="raise")
        .gt(0)
        .to_numpy()
    )
    core_or_included_clusters = (
        pd.to_numeric(clusters["cluster_core_or_included_region_listing_count"], errors="raise")
        .gt(0)
        .to_numpy()
    )
    reviewed_pass_network_clusters = magic_clusters | competing_clusters
    ski_area = pd.to_numeric(clusters["ski_area_km_median"], errors="coerce").to_numpy()

    rows: list[dict[str, object]] = []
    pair_rows: list[dict[str, object]] = []
    for focal_index, focal in clusters.iterrows():
        other = np.ones(len(clusters), dtype=bool)
        other[focal_index] = False
        nearest_directory = nearest_other(distances, all_clusters, focal_index, clusters)
        nearest_magic = nearest_other(distances, magic_clusters, focal_index, clusters)
        nearest_competing = nearest_other(distances, competing_clusters, focal_index, clusters)
        nearest_reviewed_network = nearest_other(
            distances, reviewed_pass_network_clusters, focal_index, clusters
        )
        row: dict[str, object] = {
            "cluster_id": focal["cluster_id"],
            "cluster_display_name": focal["cluster_display_name"],
            "candidate_for_path_c": focal["candidate_for_path_c"],
            "network_context_latitude": float(focal["latitude_median"]),
            "network_context_longitude": float(focal["longitude_median"]),
            "nearest_other_directory_cluster_km": nearest_directory[0],
            "nearest_other_directory_cluster_id": nearest_directory[1],
            "nearest_other_directory_cluster_name": nearest_directory[2],
            "nearest_other_resolved_current_magic_cluster_km": nearest_magic[0],
            "nearest_other_resolved_current_magic_cluster_id": nearest_magic[1],
            "nearest_other_resolved_current_magic_cluster_name": nearest_magic[2],
            "nearest_other_reviewed_competing_pass_cluster_km": nearest_competing[0],
            "nearest_other_reviewed_competing_pass_cluster_id": nearest_competing[1],
            "nearest_other_reviewed_competing_pass_cluster_name": nearest_competing[2],
            "nearest_other_reviewed_pass_network_cluster_km": nearest_reviewed_network[0],
            "nearest_other_reviewed_pass_network_cluster_id": nearest_reviewed_network[1],
            "nearest_other_reviewed_pass_network_cluster_name": nearest_reviewed_network[2],
            "network_distance_method": "great_circle_distance_between_median_supplied_listing_coordinates",
            "network_focal_cluster_excluded_from_all_neighbourhood_counts": True,
            "historical_network_context_verified": False,
            "network_context_feature_approved": False,
            "network_context_interpretation": INTERPRETATION,
            "network_context_source_ids": "DERIVED_PATH_C_FEATURE_MATRIX|DERIVED_COMPETING_PASS_CONTEXT",
        }
        for radius in RADII_KM:
            within = other & (distances[focal_index] <= radius)
            directory_count = int(within.sum())
            magic_count = int((within & magic_clusters).sum())
            competing_count = int((within & competing_clusters).sum())
            reviewed_network_count = int((within & reviewed_pass_network_clusters).sum())
            observed_ski_area = within & np.isfinite(ski_area)
            row.update(
                {
                    f"other_directory_clusters_within_{radius}km": directory_count,
                    f"other_directory_listings_within_{radius}km": int(
                        pd.to_numeric(clusters.loc[within, "listing_count"], errors="raise").sum()
                    ),
                    f"other_directory_clusters_with_observed_ski_area_within_{radius}km": int(
                        observed_ski_area.sum()
                    ),
                    f"other_directory_clusters_missing_ski_area_within_{radius}km": int(
                        directory_count - observed_ski_area.sum()
                    ),
                    f"other_directory_cluster_median_ski_area_km_sum_within_{radius}km": float(
                        np.nansum(ski_area[within])
                    ),
                    f"other_resolved_current_magic_clusters_within_{radius}km": magic_count,
                    f"other_reviewed_competing_pass_clusters_within_{radius}km": competing_count,
                    f"other_reviewed_competing_limited_partner_clusters_within_{radius}km": int(
                        (within & limited_partner_clusters).sum()
                    ),
                    f"other_reviewed_competing_core_or_included_clusters_within_{radius}km": int(
                        (within & core_or_included_clusters).sum()
                    ),
                    f"other_reviewed_pass_network_clusters_within_{radius}km": reviewed_network_count,
                    f"resolved_current_magic_share_of_other_directory_clusters_within_{radius}km": safe_share(
                        magic_count, directory_count
                    ),
                    f"reviewed_competing_pass_share_of_other_directory_clusters_within_{radius}km": safe_share(
                        competing_count, directory_count
                    ),
                    f"reviewed_pass_network_share_of_other_directory_clusters_within_{radius}km": safe_share(
                        reviewed_network_count, directory_count
                    ),
                }
            )
        rows.append(row)
        for source_index, source in clusters.iterrows():
            if source_index == focal_index:
                continue
            pair_rows.append(
                {
                    "focal_cluster_id": focal["cluster_id"],
                    "focal_cluster_name": focal["cluster_display_name"],
                    "other_cluster_id": source["cluster_id"],
                    "other_cluster_name": source["cluster_display_name"],
                    "great_circle_distance_km": float(distances[focal_index, source_index]),
                    "other_cluster_resolved_current_magic": bool(magic_clusters[source_index]),
                    "other_cluster_reviewed_competing_pass_linked": bool(
                        competing_clusters[source_index]
                    ),
                    "other_cluster_reviewed_competing_limited_partner": bool(
                        limited_partner_clusters[source_index]
                    ),
                    "other_cluster_reviewed_competing_core_or_included": bool(
                        core_or_included_clusters[source_index]
                    ),
                    "other_cluster_in_reviewed_pass_network": bool(
                        reviewed_pass_network_clusters[source_index]
                    ),
                    "network_context_interpretation": INTERPRETATION,
                    "network_context_feature_approved": False,
                }
            )
    context = pd.DataFrame(rows)
    pairs = pd.DataFrame(pair_rows)
    if len(context) != 162 or not context["cluster_id"].is_unique:
        raise ValueError("Network context lost the cluster grain")
    if len(pairs) != 162 * 161 or pairs[["focal_cluster_id", "other_cluster_id"]].duplicated().any():
        raise ValueError("Network pair table lost the ordered pair grain")
    if (pairs["focal_cluster_id"] == pairs["other_cluster_id"]).any():
        raise ValueError("Focal clusters must be excluded from pair context")
    for radius in RADII_KM:
        if not (
            context[f"other_reviewed_pass_network_clusters_within_{radius}km"]
            <= context[f"other_directory_clusters_within_{radius}km"]
        ).all():
            raise ValueError("Reviewed pass-network count exceeds directory count")
        if not (
            context[f"other_directory_clusters_within_{radius}km"]
            == context[f"other_directory_clusters_with_observed_ski_area_within_{radius}km"]
            + context[f"other_directory_clusters_missing_ski_area_within_{radius}km"]
        ).all():
            raise ValueError("Ski-area observation counts do not partition neighbours")
    nearest_columns = [
        "nearest_other_directory_cluster_km",
        "nearest_other_resolved_current_magic_cluster_km",
        "nearest_other_reviewed_competing_pass_cluster_km",
        "nearest_other_reviewed_pass_network_cluster_km",
    ]
    for column in nearest_columns:
        if context[column].isna().any():
            raise ValueError(f"Missing nearest-cluster distance in {column}")
    return context, pairs


def enrich_decision_support(context: pd.DataFrame) -> None:
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
    if as_bool(decision["network_context_feature_approved"]).any():
        raise ValueError("Network context was unexpectedly approved")
    DECISION_PATH.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    features = pd.read_csv(FEATURE_PATH)
    competing = pd.read_csv(COMPETING_PATH)
    context, pairs = build_context(features, competing)
    context.to_csv(CONTEXT_OUTPUT, index=False, lineterminator="\n")
    pairs.sort_values(["focal_cluster_id", "great_circle_distance_km", "other_cluster_id"]).to_csv(
        PAIR_OUTPUT, index=False, lineterminator="\n"
    )
    enrich_decision_support(context)

    candidates = context[as_bool(context["candidate_for_path_c"])].copy()
    candidate_columns = [
        "cluster_id",
        "cluster_display_name",
        "nearest_other_directory_cluster_km",
        "other_directory_clusters_within_25km",
        "other_directory_clusters_within_50km",
        "other_directory_cluster_median_ski_area_km_sum_within_50km",
        "nearest_other_resolved_current_magic_cluster_km",
        "other_resolved_current_magic_clusters_within_25km",
        "other_resolved_current_magic_clusters_within_50km",
        "nearest_other_reviewed_competing_pass_cluster_km",
        "other_reviewed_competing_pass_clusters_within_25km",
        "other_reviewed_competing_pass_clusters_within_50km",
        "other_reviewed_pass_network_clusters_within_25km",
        "other_reviewed_pass_network_clusters_within_50km",
        "reviewed_pass_network_share_of_other_directory_clusters_within_50km",
        "historical_network_context_verified",
        "network_context_feature_approved",
    ]
    candidates.sort_values(
        ["other_reviewed_pass_network_clusters_within_50km", "other_directory_clusters_within_50km", "cluster_id"],
        ascending=[False, False, True],
    )[candidate_columns].to_csv(CANDIDATE_OUTPUT, index=False, lineterminator="\n")

    membership = features[["cluster_id", "resolved_current_magic_member"]].merge(
        competing[["cluster_id", "cluster_has_reviewed_competing_pass_link"]],
        on="cluster_id",
        how="inner",
        validate="one_to_one",
    )
    summary: dict[str, object] = {
        "analysis_version": config["analysis_version"],
        "linked_clusters": len(context),
        "ordered_nonself_cluster_pairs": len(pairs),
        "resolved_current_magic_clusters": int(
            as_bool(features["resolved_current_magic_member"]).sum()
        ),
        "reviewed_competing_pass_linked_clusters": int(
            as_bool(competing["cluster_has_reviewed_competing_pass_link"]).sum()
        ),
        "reviewed_pass_network_union_clusters": int(
            (
                as_bool(membership["resolved_current_magic_member"])
                | as_bool(membership["cluster_has_reviewed_competing_pass_link"])
            ).sum()
        ),
        "path_c_candidates": len(candidates),
        "median_candidate_nearest_other_directory_cluster_km": float(
            candidates["nearest_other_directory_cluster_km"].median()
        ),
        "median_candidate_other_directory_clusters_within_25km": float(
            candidates["other_directory_clusters_within_25km"].median()
        ),
        "median_candidate_other_directory_clusters_within_50km": float(
            candidates["other_directory_clusters_within_50km"].median()
        ),
        "median_candidate_other_resolved_current_magic_clusters_within_50km": float(
            candidates["other_resolved_current_magic_clusters_within_50km"].median()
        ),
        "median_candidate_other_reviewed_competing_pass_clusters_within_50km": float(
            candidates["other_reviewed_competing_pass_clusters_within_50km"].median()
        ),
        "median_candidate_other_reviewed_pass_network_clusters_within_50km": float(
            candidates["other_reviewed_pass_network_clusters_within_50km"].median()
        ),
        "candidates_with_no_other_directory_cluster_within_25km": int(
            candidates["other_directory_clusters_within_25km"].eq(0).sum()
        ),
        "candidates_with_no_other_reviewed_pass_network_cluster_within_50km": int(
            candidates["other_reviewed_pass_network_clusters_within_50km"].eq(0).sum()
        ),
        "historical_network_context_verified": 0,
        "approved_features": 0,
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# Current ski-cluster and reviewed pass-network context

## Scope

This module quantifies the current spatial surroundings of all **{len(context)} preserved lift clusters** represented in the supplied resort directory. Great-circle distances use each cluster's median supplied listing coordinate, and all neighbourhood statistics exclude the focal cluster itself. The full **{len(pairs):,} ordered non-self pair** table makes every count reproducible.

The context distinguishes:

- all other directory-linked lift clusters;
- clusters with a resolved current Magic Pass link;
- clusters with at least one listing linked to the three reviewed competing-pass rosters;
- the union of those two reviewed pass networks.

Counts are reported within 25 and 50 km. The surrounding published ski-area total is the sum of cluster-median directory values with observed ski-area kilometres; observed and missing contributor counts remain separate.

## Candidate diagnostics

- apparent Path C candidates: **{len(candidates)}**
- median nearest other directory cluster: **{summary['median_candidate_nearest_other_directory_cluster_km']:.2f} km**
- median other directory clusters within 25 / 50 km: **{summary['median_candidate_other_directory_clusters_within_25km']:.0f} / {summary['median_candidate_other_directory_clusters_within_50km']:.0f}**
- median other resolved current Magic clusters within 50 km: **{summary['median_candidate_other_resolved_current_magic_clusters_within_50km']:.0f}**
- median other reviewed competing-pass-linked clusters within 50 km: **{summary['median_candidate_other_reviewed_competing_pass_clusters_within_50km']:.0f}**
- median other clusters in the reviewed pass-network union within 50 km: **{summary['median_candidate_other_reviewed_pass_network_clusters_within_50km']:.0f}**
- candidates with no other directory cluster within 25 km: **{summary['candidates_with_no_other_directory_cluster_within_25km']}**
- candidates with no other reviewed pass-network cluster within 50 km: **{summary['candidates_with_no_other_reviewed_pass_network_cluster_within_50km']}**

## Interpretation limit

The preserved clusters are not validated independent commercial destinations, median coordinates can be artificial for multi-listing clusters, straight-line distance ignores terrain and transport, directory ski-area values are undated and can represent overlapping products, and the reviewed pass rosters are current rather than historical. Counts therefore describe the supplied directory and reviewed network links—not true competitor counts, skier substitution, market penetration, visitor flows or pre-treatment network exposure. `historical_network_context_verified` and `network_context_feature_approved` remain false everywhere. No accessibility, uplift or composite score is populated.

## Outputs

- `data_processed/path_c_cluster_network_context.csv`
- `reports/path_c_cluster_network_pairs.csv`
- `reports/network_context_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified network context appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
