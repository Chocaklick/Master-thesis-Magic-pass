"""Build the cluster-level, leakage-conscious feature table for exploratory Path C.

The supplied resort directory contains duplicated and composite listings.  The
preserved lift cluster is therefore used as the least duplicated available
analysis entity.  This does not certify independent ski domains.  Bergfex
features are an undated current snapshot and are never labelled pre-treatment.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def joined(values: pd.Series) -> str:
    clean = sorted({str(value) for value in values.dropna() if str(value).strip()})
    return "|".join(clean)


def display_name(values: pd.Series) -> str:
    names = sorted(
        {str(value) for value in values.dropna() if str(value).strip()},
        key=lambda value: (len(value), value.casefold()),
    )
    if len(names) <= 3:
        return " / ".join(names)
    return " / ".join(names[:3]) + f" / +{len(names) - 3} listings"


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_stat(series: pd.Series, statistic: str) -> float:
    values = series.dropna()
    if values.empty:
        return np.nan
    return float(getattr(values, statistic)())


def main() -> None:
    config = json.loads((ROOT / "config/path_c_analysis.json").read_text(encoding="utf-8"))
    resorts = pd.read_csv(ROOT / "data_processed/resort_master.csv", dtype="string")
    points = pd.read_csv(ROOT / "data_processed/resort_point_municipality.csv", dtype="string")
    snow = pd.read_csv(ROOT / "data_processed/resort_snow_vulnerability.csv", dtype="string")
    quality = pd.read_csv(ROOT / "data_processed/resort_data_quality.csv", dtype="string")
    current = pd.read_csv(ROOT / "data_processed/magic_pass_current_destinations.csv", dtype="string")
    history = pd.read_csv(ROOT / "data_processed/magic_pass_membership_history.csv", dtype="string")
    scope = pd.read_csv(ROOT / "data_processed/magic_pass_scope_relations.csv", dtype="string")

    current_names = (
        current.dropna(subset=["candidate_resort_id"])
        .groupby("candidate_resort_id", observed=True)["official_destination_name"]
        .agg(joined)
    )
    current_counts = (
        current.dropna(subset=["candidate_resort_id"])
        .groupby("candidate_resort_id", observed=True)
        .size()
    )
    historical = history[
        history["event_type"].eq("base_pass_entry")
        & history["candidate_resort_id"].notna()
    ]
    history_counts = historical.groupby("candidate_resort_id", observed=True).size()
    scope_counts = scope.groupby("related_resort_id", observed=True).size()

    listing = resorts.merge(
        points[
            [
                "resort_id",
                "selection_status",
                "point_municipality_bfs_id",
                "point_municipality_name",
                "point_municipality_canton",
                "bfs_hotel_universe",
                "bfs_hotel_municipality_name",
            ]
        ],
        on="resort_id",
        how="left",
        validate="one_to_one",
    ).merge(
        snow[
            [
                "resort_id",
                "mean_winter_snow_depth_cm",
                "snow_reliability_share_days_ge_30cm",
                "low_snow_winter_frequency",
                "snow_vulnerability_proxy",
                "snow_proxy_quality",
                "snow_climate_feature_ready",
            ]
        ],
        on="resort_id",
        how="left",
        validate="one_to_one",
    ).merge(
        quality[["resort_id", "data_quality_score"]],
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    listing["resolved_current_magic_destination_count"] = (
        listing["resort_id"].map(current_counts).fillna(0).astype(int)
    )
    listing["resolved_current_magic_destination_names"] = (
        listing["resort_id"].map(current_names).fillna("")
    )
    listing["historical_base_entry_count"] = (
        listing["resort_id"].map(history_counts).fillna(0).astype(int)
    )
    listing["scope_relation_event_count"] = (
        listing["resort_id"].map(scope_counts).fillna(0).astype(int)
    )
    for column in [
        "latitude",
        "longitude",
        "altitude_top_m",
        "ski_area_km",
        "number_lifts",
        "mean_winter_snow_depth_cm",
        "snow_reliability_share_days_ge_30cm",
        "low_snow_winter_frequency",
        "snow_vulnerability_proxy",
        "data_quality_score",
    ]:
        listing[column] = numeric(listing[column])

    rows: list[dict] = []
    quality_order = {"high": 3, "moderate": 2, "low": 1}
    assignment_order = {"confident": 3, "review": 2, "warning": 1}
    for cluster_id, group in listing.groupby("cluster_id", observed=True, sort=True):
        structural = {
            "altitude_top_m": group["altitude_top_m"],
            "ski_area_km": group["ski_area_km"],
            "number_lifts": group["number_lifts"],
        }
        row: dict[str, object] = {
            "cluster_id": cluster_id,
            "analysis_entity_level": config["analysis_entity"],
            "cluster_display_name": display_name(group["resort_name_canonical"]),
            "member_resort_ids": joined(group["resort_id"]),
            "member_resort_names": joined(group["resort_name_canonical"]),
            "listing_count": len(group),
            "latitude_median": safe_stat(group["latitude"], "median"),
            "longitude_median": safe_stat(group["longitude"], "median"),
            "feature_temporal_status": config["feature_temporal_status"],
            "assignment_quality_worst": min(
                group["assignment_quality"].dropna(),
                key=lambda value: assignment_order.get(str(value), 0),
                default="unknown",
            ),
            "all_listing_assignments_confident": bool(group["assignment_quality"].eq("confident").all()),
            "point_municipality_bfs_ids": joined(group["point_municipality_bfs_id"]),
            "point_municipality_names": joined(group["point_municipality_name"]),
            "point_municipality_cantons": joined(group["point_municipality_canton"]),
            "has_resolved_swiss_point": bool(group["selection_status"].eq("unique_current_polygon").any()),
            "has_hotel_point_context": bool(as_bool(group["bfs_hotel_universe"]).any()),
            "hotel_point_context_names": joined(group["bfs_hotel_municipality_name"]),
            "hotel_context_interpretation": "coordinate_container_only_not_approved_tourism_catchment",
            "resolved_current_magic_destination_count": int(group["resolved_current_magic_destination_count"].sum()),
            "resolved_current_magic_destination_names": joined(group["resolved_current_magic_destination_names"]),
            "historical_base_entry_count": int(group["historical_base_entry_count"].sum()),
            "scope_relation_event_count": int(group["scope_relation_event_count"].sum()),
            "mean_winter_snow_depth_cm_median": safe_stat(group["mean_winter_snow_depth_cm"], "median"),
            "snow_reliability_share_days_ge_30cm_median": safe_stat(group["snow_reliability_share_days_ge_30cm"], "median"),
            "low_snow_winter_frequency_median": safe_stat(group["low_snow_winter_frequency"], "median"),
            "snow_vulnerability_proxy_median": safe_stat(group["snow_vulnerability_proxy"], "median"),
            "snow_feature_ready_share": float(as_bool(group["snow_climate_feature_ready"]).mean()),
            "snow_proxy_quality_worst": min(
                group["snow_proxy_quality"].dropna(),
                key=lambda value: quality_order.get(str(value), 0),
                default="unknown",
            ),
            "data_quality_score_median": safe_stat(group["data_quality_score"], "median"),
            "data_quality_score_min": safe_stat(group["data_quality_score"], "min"),
            "source_ids": "BERGFEX_RESORT_DIRECTORY|DERIVED_EXISTING_CLUSTER_REFERENCE|DERIVED_RESORT_DATA_QUALITY|DERIVED_SLF_RESORT_PROXY|MAGIC_CURRENT_MAP|MAGIC_OFFICIAL_EVIDENCE_SET|DERIVED_MAGIC_SCOPE_REVIEW",
        }
        disagreements = []
        for name, values in structural.items():
            row[f"{name}_median"] = safe_stat(values, "median")
            row[f"{name}_min"] = safe_stat(values, "min")
            row[f"{name}_max"] = safe_stat(values, "max")
            if values.notna().any() and values.max() > values.min():
                disagreements.append(name)
        row["multi_listing_feature_disagreement"] = bool(disagreements)
        row["disagreeing_structural_features"] = "|".join(disagreements)
        rows.append(row)

    output = pd.DataFrame(rows).sort_values("cluster_id").reset_index(drop=True)
    output["structural_feature_complete"] = output[
        ["altitude_top_m_median", "ski_area_km_median", "number_lifts_median"]
    ].notna().all(axis=1)
    output["resolved_current_magic_member"] = output[
        "resolved_current_magic_destination_count"
    ].gt(0)
    output["historical_magic_link"] = output["historical_base_entry_count"].gt(0)
    output["precautionary_scope_relation"] = output["scope_relation_event_count"].gt(0)

    def status(row: pd.Series) -> str:
        if row["resolved_current_magic_member"]:
            return "resolved_current_member"
        if row["historical_magic_link"]:
            return "historical_link_not_resolved_current"
        if row["precautionary_scope_relation"]:
            return "precautionary_scope_relation"
        return "no_resolved_magic_link"

    output["magic_status"] = output.apply(status, axis=1)
    output["candidate_for_path_c"] = (
        output["magic_status"].eq("no_resolved_magic_link")
        & output["structural_feature_complete"]
        & output["has_resolved_swiss_point"]
    )
    output["candidate_interpretation"] = np.where(
        output["candidate_for_path_c"],
        "apparent_nonmember_candidate_not_verified_nonmember",
        "not_in_initial_candidate_pool",
    )
    output.to_csv(ROOT / "data_processed/path_c_resort_cluster_features.csv", index=False)

    summary = {
        "analysis_version": config["analysis_version"],
        "resort_listings": int(len(resorts)),
        "linked_lift_clusters": int(len(output)),
        "clusters_with_complete_structural_features": int(output["structural_feature_complete"].sum()),
        "resolved_current_magic_clusters": int(output["resolved_current_magic_member"].sum()),
        "historical_not_current_clusters": int(
            output["magic_status"].eq("historical_link_not_resolved_current").sum()
        ),
        "precautionary_scope_relation_clusters": int(
            output["magic_status"].eq("precautionary_scope_relation").sum()
        ),
        "apparent_nonmember_candidates": int(output["candidate_for_path_c"].sum()),
        "clusters_with_multi_listing_feature_disagreement": int(
            output["multi_listing_feature_disagreement"].sum()
        ),
        "feature_temporal_status": config["feature_temporal_status"],
        "causal_interpretation_approved": False,
    }
    (ROOT / "reports/path_c_feature_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
