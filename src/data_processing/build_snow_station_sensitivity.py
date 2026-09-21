"""Compare each reviewed resort component's selected SLF proxy with the next-nearest eligible station."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data_processed" / "resort_snow_alternative_station_sensitivity.csv"
SUMMARY = ROOT / "reports" / "snow_station_sensitivity_summary.json"
REPORT = ROOT / "reports" / "13_SNOW_PROXY_SENSITIVITY.md"
MIN_LONGITUDINAL_COVERAGE = 0.80


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().eq("true")


def haversine_km(latitude: float, longitude: float, stations: pd.DataFrame) -> np.ndarray:
    lat1 = np.radians(latitude)
    lon1 = np.radians(longitude)
    lat2 = np.radians(stations["lat"].to_numpy(float))
    lon2 = np.radians(stations["lon"].to_numpy(float))
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2
    )
    return 6371.0088 * 2 * np.arcsin(np.sqrt(value))


def proxy_quality(distance_km: float, elevation_gap_m: float) -> str:
    if distance_km <= 10 and elevation_gap_m <= 500:
        return "high"
    if distance_km <= 25 and elevation_gap_m <= 1000:
        return "moderate"
    return "low"


def linear_slope(frame: pd.DataFrame, column: str) -> float:
    values = frame[["winter_start_year", column]].dropna()
    if len(values) < 5 or values[column].nunique() < 2:
        return np.nan
    return float(np.polyfit(values["winter_start_year"], values[column], 1)[0])


def main() -> None:
    winter = pd.read_csv(ROOT / "data_processed" / "slf_snow_station_winter.csv")
    crosswalk = pd.read_csv(ROOT / "data_processed" / "resort_snow_station_crosswalk.csv")
    config = json.loads(
        (ROOT / "config" / "treatment_destination_review.json").read_text(
            encoding="utf-8"
        )
    )

    unit_by_resort: dict[str, list[str]] = {}
    for unit in config["units"]:
        if unit["eligible_for_reviewed_outcome_panel"]:
            for resort_id in unit["component_resort_ids"]:
                unit_by_resort.setdefault(resort_id, []).append(
                    unit["destination_unit_id"]
                )

    coverage = winter.groupby("station_code", observed=True).agg(
        valid_winter_days=("snow_depth_observed_days", "sum"),
        expected_winter_days=("winter_expected_days", "sum"),
    )
    coverage["longitudinal_coverage"] = (
        coverage["valid_winter_days"] / coverage["expected_winter_days"]
    )
    eligible_codes = coverage.index[
        coverage["longitudinal_coverage"].ge(MIN_LONGITUDINAL_COVERAGE)
    ]
    station_fields = ["station_code", "label", "lat", "lon", "elevation"]
    stations = (
        winter.loc[winter["station_code"].isin(eligible_codes), station_fields]
        .drop_duplicates("station_code")
        .sort_values("station_code")
        .reset_index(drop=True)
    )
    components = crosswalk[crosswalk["resort_id"].isin(unit_by_resort)].copy()
    if len(components) != len(unit_by_resort):
        missing = sorted(set(unit_by_resort) - set(components["resort_id"]))
        raise ValueError(f"Reviewed components missing from snow crosswalk: {missing}")

    rows: list[dict] = []
    for resort in components.itertuples(index=False):
        candidate_stations = stations.copy()
        candidate_stations["distance_km"] = haversine_km(
            float(resort.latitude), float(resort.longitude), candidate_stations
        )
        alternative = (
            candidate_stations[
                candidate_stations["station_code"].ne(resort.snow_station_code)
            ]
            .sort_values(["distance_km", "station_code"])
            .iloc[0]
        )
        selected_winter = winter[
            winter["station_code"].eq(resort.snow_station_code)
            & as_bool(winter["winter_snow_proxy_usable"])
        ][
            [
                "winter_start_year",
                "winter_mean_snow_depth_cm",
                "days_snow_depth_ge_30cm",
                "snow_depth_observed_days",
            ]
        ].rename(
            columns={
                "winter_mean_snow_depth_cm": "selected_mean_depth",
                "days_snow_depth_ge_30cm": "selected_days_ge_30",
                "snow_depth_observed_days": "selected_observed_days",
            }
        )
        alternative_winter = winter[
            winter["station_code"].eq(alternative.station_code)
            & as_bool(winter["winter_snow_proxy_usable"])
        ][
            [
                "winter_start_year",
                "winter_mean_snow_depth_cm",
                "days_snow_depth_ge_30cm",
                "snow_depth_observed_days",
            ]
        ].rename(
            columns={
                "winter_mean_snow_depth_cm": "alternative_mean_depth",
                "days_snow_depth_ge_30cm": "alternative_days_ge_30",
                "snow_depth_observed_days": "alternative_observed_days",
            }
        )
        common = selected_winter.merge(
            alternative_winter, on="winter_start_year", validate="one_to_one"
        ).dropna(subset=["selected_mean_depth", "alternative_mean_depth"])
        correlation = (
            common["selected_mean_depth"].corr(common["alternative_mean_depth"])
            if len(common) >= 5
            and common["selected_mean_depth"].nunique() > 1
            and common["alternative_mean_depth"].nunique() > 1
            else np.nan
        )
        selected_mean = common["selected_mean_depth"].mean()
        alternative_mean = common["alternative_mean_depth"].mean()
        mean_absolute_difference = (
            common["selected_mean_depth"] - common["alternative_mean_depth"]
        ).abs().mean()
        relative_difference = (
            mean_absolute_difference / selected_mean
            if pd.notna(selected_mean) and selected_mean > 0
            else np.nan
        )
        selected_reliability = (
            common["selected_days_ge_30"].sum()
            / common["selected_observed_days"].sum()
            if common["selected_observed_days"].sum() > 0
            else np.nan
        )
        alternative_reliability = (
            common["alternative_days_ge_30"].sum()
            / common["alternative_observed_days"].sum()
            if common["alternative_observed_days"].sum() > 0
            else np.nan
        )
        reliability_gap = abs(selected_reliability - alternative_reliability)
        if len(common) < 8 or pd.isna(correlation):
            agreement = "insufficient_common_winters"
        elif correlation >= 0.75 and relative_difference <= 0.35 and reliability_gap <= 0.20:
            agreement = "high"
        elif correlation >= 0.50 and relative_difference <= 0.60:
            agreement = "moderate"
        else:
            agreement = "low"
        selected_slope = linear_slope(common, "selected_mean_depth")
        alternative_slope = linear_slope(common, "alternative_mean_depth")
        rows.append(
            {
                "destination_unit_ids": "|".join(sorted(unit_by_resort[resort.resort_id])),
                "resort_id": resort.resort_id,
                "resort_name_canonical": resort.resort_name_canonical,
                "selected_station_code": resort.snow_station_code,
                "selected_station_label": resort.snow_station_label,
                "selected_station_distance_km": resort.snow_station_distance_km,
                "selected_station_elevation_gap_m": resort.snow_station_elevation_gap_to_resort_top_m,
                "selected_station_quality": resort.snow_proxy_quality,
                "alternative_station_code": alternative.station_code,
                "alternative_station_label": alternative.label,
                "alternative_station_distance_km": alternative.distance_km,
                "alternative_station_elevation_gap_m": abs(
                    float(alternative.elevation) - float(resort.altitude_top_m)
                ),
                "alternative_station_quality": proxy_quality(
                    float(alternative.distance_km),
                    abs(float(alternative.elevation) - float(resort.altitude_top_m)),
                ),
                "common_usable_winters": len(common),
                "winter_mean_depth_correlation": correlation,
                "selected_mean_winter_depth_cm": selected_mean,
                "alternative_mean_winter_depth_cm": alternative_mean,
                "mean_absolute_winter_depth_difference_cm": mean_absolute_difference,
                "relative_mean_absolute_depth_difference": relative_difference,
                "selected_snow_reliability_share_ge_30cm": selected_reliability,
                "alternative_snow_reliability_share_ge_30cm": alternative_reliability,
                "absolute_reliability_share_difference": reliability_gap,
                "selected_depth_trend_cm_per_year": selected_slope,
                "alternative_depth_trend_cm_per_year": alternative_slope,
                "trend_direction_agrees": (
                    bool(selected_slope * alternative_slope >= 0)
                    if pd.notna(selected_slope) and pd.notna(alternative_slope)
                    else False
                ),
                "alternative_station_agreement": agreement,
                "selection_rule": "next_nearest_distinct_station_passing_same_80pct_longitudinal_gate",
                "direct_slope_representation": False,
                "causal_covariate_approved": False,
                "source_ids": "SLF_IMIS_STATIONS|SLF_IMIS_DAILY_SNOW|DERIVED_SNOW_STATION_SENSITIVITY",
            }
        )

    result = pd.DataFrame(rows).sort_values(["destination_unit_ids", "resort_id"])
    result.to_csv(OUTPUT, index=False, na_rep="NA")
    counts = result["alternative_station_agreement"].value_counts().to_dict()
    summary = {
        "reviewed_resort_components": int(len(result)),
        "eligible_slf_stations": int(len(stations)),
        "components_with_at_least_8_common_usable_winters": int(
            result["common_usable_winters"].ge(8).sum()
        ),
        "agreement_counts": counts,
        "median_winter_mean_depth_correlation": float(
            result["winter_mean_depth_correlation"].median()
        ),
        "median_relative_mean_absolute_depth_difference": float(
            result["relative_mean_absolute_depth_difference"].median()
        ),
        "trend_direction_agreement_count": int(result["trend_direction_agrees"].sum()),
        "causal_covariates_approved": 0,
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# SLF alternative-station sensitivity

Generated reproducibly by `src/data_processing/build_snow_station_sensitivity.py`.

## Purpose

The primary snow proxy assigns the nearest SLF snow station passing the 80% longitudinal winter-coverage gate. This sensitivity replaces it, for each reviewed resort component, with the next-nearest distinct station passing the same gate. It asks whether broad winter snow patterns are stable to a simple plausible alternative; it does not identify the best station and does not turn either station into a piste observation.

## Results

- Reviewed resort components: **{summary['reviewed_resort_components']}**.
- Eligible SLF stations considered: **{summary['eligible_slf_stations']}**.
- Components with at least eight common usable winters: **{summary['components_with_at_least_8_common_usable_winters']}**.
- Agreement grades: **{json.dumps(counts, ensure_ascii=False, sort_keys=True)}**.
- Median correlation of November-April mean snow depth: **{summary['median_winter_mean_depth_correlation']:.3f}**.
- Median mean absolute depth difference relative to the selected-station mean: **{summary['median_relative_mean_absolute_depth_difference']:.1%}**.
- Components whose selected and alternative linear depth trends have the same sign: **{summary['trend_direction_agreement_count']} of {summary['reviewed_resort_components']}**.

`alternative_station_agreement` is a predeclared descriptive grade: high requires correlation at least 0.75, relative mean absolute difference at most 35%, and the ≥30 cm reliability-share gap at most 0.20; moderate requires correlation at least 0.50 and relative difference at most 60%. The grade is deliberately conservative and has no causal interpretation.

## Limitations and decision

The next-nearest station is a transparent perturbation, not an elevation-, aspect-, or climatology-optimised substitute. Both stations may share regional errors or both may poorly represent a resort. Resort-top altitude is not the piste elevation distribution, and no snowmaking, grooming, wind redistribution or operating-day information is observed. The output therefore remains a robustness diagnostic; every `causal_covariate_approved` value is false. A gridded product such as ERA5-Land remains the required independent-source sensitivity.

Detailed output: `{OUTPUT.relative_to(ROOT).as_posix()}`.
"""
    REPORT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
