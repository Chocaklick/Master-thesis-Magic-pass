"""Build a transparent evidence-completeness score for each resort listing."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def bool_series(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def main() -> None:
    resorts = pd.read_csv(ROOT / "data_processed" / "resort_master.csv", dtype="string")
    points = pd.read_csv(ROOT / "data_processed" / "resort_point_municipality.csv", dtype="string")
    history = pd.read_csv(ROOT / "data_processed" / "magic_pass_membership_history.csv", dtype="string")
    current = pd.read_csv(ROOT / "data_processed" / "magic_pass_current_destinations.csv", dtype="string")
    snow = pd.read_csv(ROOT / "data_processed" / "resort_snow_vulnerability.csv", dtype="string")

    quality = resorts.merge(
        points[
            [
                "resort_id",
                "selection_status",
                "assignment_confidence",
                "bfs_hotel_universe",
                "point_municipality_bfs_id",
            ]
        ],
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    event_counts = history.dropna(subset=["candidate_resort_id"]).groupby("candidate_resort_id").agg(
        documented_membership_events=("event_id", "nunique"),
        membership_source_count=("source_id", "nunique"),
    )
    current_flag = (
        current.dropna(subset=["candidate_resort_id"])
        .groupby("candidate_resort_id")
        .size()
        .rename("current_official_destination_candidates")
    )
    quality = quality.join(event_counts, on="resort_id").join(current_flag, on="resort_id")
    quality = quality.merge(
        snow[
            [
                "resort_id",
                "snow_station_code",
                "snow_station_distance_km",
                "snow_station_elevation_gap_to_resort_top_m",
                "usable_winter_seasons",
                "snow_proxy_quality",
                "snow_climate_feature_ready",
            ]
        ],
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    for column in ["documented_membership_events", "membership_source_count", "current_official_destination_candidates"]:
        quality[column] = quality[column].fillna(0).astype(int)

    quality["identity_scope_score"] = 0.0
    quality["lift_assignment_score"] = quality["assignment_quality"].map(
        {"confident": 1.0, "warning": 0.5, "review": 0.0}
    ).fillna(0.0)
    quality["geolocation_score"] = quality["selection_status"].eq("unique_current_polygon").astype(float)
    quality["tourism_exposure_score"] = 0.0
    quality["hotel_outcome_score"] = bool_series(quality["bfs_hotel_universe"]).astype(float)
    quality["membership_history_score"] = (
        quality["documented_membership_events"].gt(0)
        | quality["current_official_destination_candidates"].gt(0)
    ).astype(float) * 0.5
    feature_columns = ["altitude_top_m", "ski_area_km", "number_lifts"]
    quality["infrastructure_feature_score"] = quality[feature_columns].notna().mean(axis=1)
    quality["snow_climate_score"] = quality["snow_proxy_quality"].map(
        {"high": 1.0, "moderate": 0.75, "low": 0.25}
    ).fillna(0.0)
    quality.loc[~bool_series(quality["snow_climate_feature_ready"]), "snow_climate_score"] = (
        quality.loc[
            ~bool_series(quality["snow_climate_feature_ready"]), "snow_climate_score"
        ].clip(upper=0.25)
    )
    component_columns = [
        "identity_scope_score",
        "lift_assignment_score",
        "geolocation_score",
        "tourism_exposure_score",
        "hotel_outcome_score",
        "membership_history_score",
        "infrastructure_feature_score",
        "snow_climate_score",
    ]
    quality["data_quality_score"] = (100 * quality[component_columns].mean(axis=1)).round(1)
    quality["causal_ready"] = False

    def warnings(row: pd.Series) -> str:
        messages = [
            "independent_destination_scope_unverified",
            "tourism_exposure_unverified",
            "snow_proxy_not_direct_slope_measurement",
        ]
        if row["lift_assignment_score"] < 1:
            messages.append("lift_assignment_review")
        if row["geolocation_score"] == 0:
            messages.append("current_point_municipality_unresolved")
        if row["hotel_outcome_score"] == 0:
            messages.append("no_hotel_outcome_at_point_municipality")
        if row["membership_history_score"] == 0:
            messages.append("membership_history_unverified")
        if row["snow_climate_score"] == 0:
            messages.append("snow_proxy_unavailable")
        elif row["snow_proxy_quality"] == "low":
            messages.append("snow_proxy_low_spatial_elevation_comparability")
        return "|".join(messages)

    quality["data_quality_warnings"] = quality.apply(warnings, axis=1)
    output_columns = [
        "resort_id", "resort_name_canonical", "cluster_id", "point_municipality_bfs_id",
        "documented_membership_events", "current_official_destination_candidates",
        "snow_station_code", "snow_station_distance_km",
        "snow_station_elevation_gap_to_resort_top_m", "usable_winter_seasons",
        "snow_proxy_quality", *component_columns,
        "data_quality_score", "causal_ready", "data_quality_warnings",
    ]
    output = quality[output_columns].sort_values(["data_quality_score", "resort_id"], ascending=[False, True])
    output.to_csv(ROOT / "data_processed" / "resort_data_quality.csv", index=False)
    print(output["data_quality_score"].describe().round(2).to_string())


if __name__ == "__main__":
    main()
