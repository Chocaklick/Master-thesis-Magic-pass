"""Compare primary and next-nearest eligible SwissMetNet weather proxies.

This robustness module uses the same official station universe, parameters,
coverage gate and analytical normals as the primary weather proxy. It replaces
each reviewed resort component's nearest eligible station with the next-nearest
distinct station and rebuilds destination-month context. It does not validate
piste microclimate or approve a causal covariate.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_weather_proxy_panel import (
    ANALYSIS_END,
    ANALYSIS_START,
    CORE_PARAMETERS,
    DAILY_COLUMNS,
    MIN_MONTH_COVERAGE,
    aggregate_station_months,
    build_destination_month,
    checked_path,
    eligible_station_metadata,
    haversine_matrix,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
ALTERNATIVE_SOURCE_CONFIG = (
    ROOT / "config" / "meteoswiss_weather_sensitivity_station_files.json"
)
PRIMARY_SOURCE_CONFIG = ROOT / "config" / "meteoswiss_selected_station_files.json"
PRIMARY_CROSSWALK = ROOT / "data_processed" / "resort_weather_station_crosswalk.csv"
PRIMARY_STATION_MONTH = ROOT / "data_processed" / "meteoswiss_station_month.csv"
PRIMARY_DESTINATION_MONTH = ROOT / "data_processed" / "destination_weather_month.csv"

ALTERNATIVE_STATION_MONTH_OUT = (
    ROOT / "data_processed" / "meteoswiss_alternative_station_month.csv"
)
COMPONENT_SENSITIVITY_OUT = (
    ROOT / "reports" / "weather_station_alternative_sensitivity.csv"
)
DESTINATION_MONTH_SENSITIVITY_OUT = (
    ROOT / "data_processed" / "destination_weather_alternative_sensitivity.csv"
)
DESTINATION_SUMMARY_OUT = (
    ROOT / "reports" / "weather_destination_alternative_summary.csv"
)
SUMMARY_OUT = ROOT / "reports" / "weather_station_sensitivity_summary.json"
REPORT_OUT = ROOT / "reports" / "34_WEATHER_STATION_SENSITIVITY.md"

INTERPRETATION = (
    "selected_vs_next_nearest_eligible_swissmetnet_regional_weather_proxy_"
    "sensitivity_not_piste_microclimate_gridded_validation_or_causal_approval"
)


def load_alternative_daily(
    required_station_codes: set[str],
) -> tuple[pd.DataFrame, int, list[str]]:
    new_sources = json.loads(ALTERNATIVE_SOURCE_CONFIG.read_text(encoding="utf-8"))
    primary_sources = json.loads(PRIMARY_SOURCE_CONFIG.read_text(encoding="utf-8"))
    if len(new_sources) != 14 or len(primary_sources) != 14:
        raise ValueError("Expected historical and recent files for seven alternative stations")
    sources = new_sources + primary_sources
    frames: list[pd.DataFrame] = []
    for source in sources:
        frame = pd.read_csv(
            checked_path(source["source_id"]),
            sep=";",
            encoding="cp1252",
            usecols=DAILY_COLUMNS,
            dtype="string",
            keep_default_na=False,
        )
        if set(frame.columns) != set(DAILY_COLUMNS):
            raise ValueError(f"Unexpected daily schema for {source['source_id']}")
        frame["source_id"] = source["source_id"]
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    raw = raw[raw["station_abbr"].isin(required_station_codes)].copy()
    raw_rows_all_dates = len(raw)
    raw["date"] = pd.to_datetime(
        raw["reference_timestamp"], format="%d.%m.%Y %H:%M", errors="raise"
    )
    raw = raw[raw["date"].between(ANALYSIS_START, ANALYSIS_END)].copy()
    if raw.duplicated(["station_abbr", "date"]).any():
        raise ValueError("Duplicate station-date rows across alternative files")
    station_codes = sorted(raw["station_abbr"].unique())
    if set(station_codes) != required_station_codes:
        raise ValueError(
            f"Configured files do not cover required alternative stations: {station_codes}"
        )
    for parameter in CORE_PARAMETERS:
        raw[parameter] = pd.to_numeric(raw[parameter], errors="coerce")
    raw["invalid_negative_precipitation"] = raw["rre150d0"].lt(0)
    raw["rre150d0"] = raw["rre150d0"].where(~raw["invalid_negative_precipitation"])
    impossible_temperature = (
        raw["tre200dn"].gt(raw["tre200d0"])
        | raw["tre200d0"].gt(raw["tre200dx"])
    )
    if impossible_temperature.any():
        raise ValueError("Alternative daily minimum/mean/maximum ordering violated")
    return raw, raw_rows_all_dates, station_codes


def build_alternative_crosswalk() -> pd.DataFrame:
    primary = pd.read_csv(PRIMARY_CROSSWALK)
    eligible, candidate_count = eligible_station_metadata()
    distances = haversine_matrix(
        primary["latitude"].to_numpy(float),
        primary["longitude"].to_numpy(float),
        eligible["station_coordinates_wgs84_lat"].to_numpy(float),
        eligible["station_coordinates_wgs84_lon"].to_numpy(float),
    )
    station_codes = eligible["station_abbr"].astype(str).to_numpy()
    rows: list[dict[str, object]] = []
    for position, resort in primary.reset_index(drop=True).iterrows():
        ordered = np.argsort(distances[position])
        selected_primary = str(resort["weather_station_code"])
        if station_codes[ordered[0]] != selected_primary:
            raise ValueError(
                f"Primary station no longer nearest for {resort['resort_id']}: "
                f"{station_codes[ordered[0]]} != {selected_primary}"
            )
        alternative_position = next(
            int(index) for index in ordered if station_codes[index] != selected_primary
        )
        alternative = eligible.iloc[alternative_position]
        distance = float(distances[position, alternative_position])
        rows.append(
            {
                "destination_unit_id": resort["destination_unit_id"],
                "destination_name": resort["destination_name"],
                "resort_id": resort["resort_id"],
                "resort_name_canonical": resort["resort_name_canonical"],
                "latitude": float(resort["latitude"]),
                "longitude": float(resort["longitude"]),
                "altitude_top_m": float(resort["altitude_top_m"]),
                "primary_weather_station_code": selected_primary,
                "primary_weather_station_name": resort["weather_station_name"],
                "primary_weather_station_distance_km": float(
                    resort["weather_station_distance_km"]
                ),
                "primary_weather_station_elevation_m": float(
                    resort["weather_station_elevation_m"]
                ),
                "alternative_weather_station_code": str(alternative["station_abbr"]),
                "alternative_weather_station_name": alternative["station_name"],
                "alternative_weather_station_latitude": float(
                    alternative["station_coordinates_wgs84_lat"]
                ),
                "alternative_weather_station_longitude": float(
                    alternative["station_coordinates_wgs84_lon"]
                ),
                "alternative_weather_station_elevation_m": float(
                    alternative["station_height_masl"]
                ),
                "alternative_weather_station_distance_km": distance,
                "alternative_weather_station_elevation_gap_to_resort_top_m": abs(
                    float(alternative["station_height_masl"])
                    - float(resort["altitude_top_m"])
                ),
                "eligible_weather_station_count": candidate_count,
                "alternative_station_selection_method": (
                    "next_nearest_distinct_current_swissmetnet_station_with_all_four_"
                    "daily_parameters_since_2013"
                ),
                "weather_station_sensitivity_interpretation": INTERPRETATION,
                "weather_station_sensitivity_causal_covariate_approved": False,
            }
        )
    crosswalk = pd.DataFrame(rows)
    return crosswalk


def correlation(left: pd.Series, right: pd.Series) -> float:
    if len(left) < 3 or left.nunique(dropna=True) < 2 or right.nunique(dropna=True) < 2:
        return np.nan
    return float(left.corr(right))


def agreement_grade(temperature_correlation: float, precipitation_correlation: float) -> str:
    if temperature_correlation >= 0.90 and precipitation_correlation >= 0.70:
        return "high"
    if temperature_correlation >= 0.80 and precipitation_correlation >= 0.50:
        return "moderate"
    return "low"


def component_diagnostics(
    crosswalk: pd.DataFrame,
    primary_month: pd.DataFrame,
    alternative_month: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for link in crosswalk.itertuples(index=False):
        primary = primary_month[
            primary_month["station_abbr"].eq(link.primary_weather_station_code)
        ].copy()
        alternative = alternative_month[
            alternative_month["station_abbr"].eq(link.alternative_weather_station_code)
        ].copy()
        paired = primary.merge(
            alternative,
            on="month_date",
            how="inner",
            suffixes=("_primary", "_alternative"),
            validate="one_to_one",
        )
        common = paired[
            paired["month_weather_proxy_usable_primary"].astype(bool)
            & paired["month_weather_proxy_usable_alternative"].astype(bool)
        ].copy()
        winter = common[common["month_date"].dt.month.isin([11, 12, 1, 2, 3, 4])]
        temperature_correlation = correlation(
            common["air_temperature_anomaly_c_primary"],
            common["air_temperature_anomaly_c_alternative"],
        )
        precipitation_correlation = correlation(
            common["precipitation_anomaly_mm_primary"],
            common["precipitation_anomaly_mm_alternative"],
        )
        row = dict(link._asdict())
        row.update(
            {
                "common_usable_months": len(common),
                "common_usable_winter_months": len(winter),
                "temperature_anomaly_correlation": temperature_correlation,
                "winter_temperature_anomaly_correlation": correlation(
                    winter["air_temperature_anomaly_c_primary"],
                    winter["air_temperature_anomaly_c_alternative"],
                ),
                "temperature_anomaly_mean_absolute_difference_c": float(
                    (
                        common["air_temperature_anomaly_c_primary"]
                        - common["air_temperature_anomaly_c_alternative"]
                    ).abs().mean()
                ),
                "precipitation_anomaly_correlation": precipitation_correlation,
                "winter_precipitation_anomaly_correlation": correlation(
                    winter["precipitation_anomaly_mm_primary"],
                    winter["precipitation_anomaly_mm_alternative"],
                ),
                "precipitation_anomaly_mean_absolute_difference_mm": float(
                    (
                        common["precipitation_anomaly_mm_primary"]
                        - common["precipitation_anomaly_mm_alternative"]
                    ).abs().mean()
                ),
                "weather_station_sensitivity_agreement": agreement_grade(
                    temperature_correlation, precipitation_correlation
                ),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["destination_unit_id", "resort_id"])


def build_destination_sensitivity(
    crosswalk: pd.DataFrame,
    alternative_month: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    alternative_links = crosswalk.rename(
        columns={
            "alternative_weather_station_code": "weather_station_code",
            "alternative_weather_station_name": "weather_station_name",
            "alternative_weather_station_latitude": "weather_station_latitude",
            "alternative_weather_station_longitude": "weather_station_longitude",
            "alternative_weather_station_elevation_m": "weather_station_elevation_m",
            "alternative_weather_station_distance_km": "weather_station_distance_km",
            "alternative_weather_station_elevation_gap_to_resort_top_m": (
                "weather_station_elevation_gap_to_resort_top_m"
            ),
        }
    ).copy()
    alternative_links["weather_proxy_quality"] = np.select(
        [
            alternative_links["weather_station_distance_km"].le(10),
            alternative_links["weather_station_distance_km"].le(20),
        ],
        ["high", "moderate"],
        default="low",
    )
    alternative_destination = build_destination_month(
        alternative_month, alternative_links
    )
    primary = pd.read_csv(PRIMARY_DESTINATION_MONTH)
    primary["date"] = pd.to_datetime(primary["date"], errors="raise")
    alternative_destination["date"] = pd.to_datetime(
        alternative_destination["date"], errors="raise"
    )
    keep = [
        "destination_unit_id",
        "destination_name",
        "date",
        "complete_weather_proxy",
        "air_temperature_anomaly_c",
        "precipitation_anomaly_mm",
    ]
    comparison = primary[keep].merge(
        alternative_destination[keep],
        on=["destination_unit_id", "destination_name", "date"],
        how="outer",
        suffixes=("_primary", "_alternative"),
        validate="one_to_one",
    )
    if len(comparison) != 1_749:
        raise ValueError("Alternative destination sensitivity lost the 11-unit monthly grain")
    comparison["both_weather_proxies_complete"] = (
        comparison["complete_weather_proxy_primary"].fillna(False).astype(bool)
        & comparison["complete_weather_proxy_alternative"].fillna(False).astype(bool)
    )
    comparison["temperature_anomaly_difference_alternative_minus_primary_c"] = (
        comparison["air_temperature_anomaly_c_alternative"]
        - comparison["air_temperature_anomaly_c_primary"]
    ).where(comparison["both_weather_proxies_complete"])
    comparison["precipitation_anomaly_difference_alternative_minus_primary_mm"] = (
        comparison["precipitation_anomaly_mm_alternative"]
        - comparison["precipitation_anomaly_mm_primary"]
    ).where(comparison["both_weather_proxies_complete"])
    comparison["weather_station_sensitivity_interpretation"] = INTERPRETATION
    comparison["weather_station_sensitivity_causal_covariate_approved"] = False

    summary_rows: list[dict[str, object]] = []
    for destination_unit_id, group in comparison.groupby(
        "destination_unit_id", observed=True
    ):
        common = group[group["both_weather_proxies_complete"]]
        temperature_correlation = correlation(
            common["air_temperature_anomaly_c_primary"],
            common["air_temperature_anomaly_c_alternative"],
        )
        precipitation_correlation = correlation(
            common["precipitation_anomaly_mm_primary"],
            common["precipitation_anomaly_mm_alternative"],
        )
        summary_rows.append(
            {
                "destination_unit_id": destination_unit_id,
                "destination_name": group["destination_name"].iloc[0],
                "common_complete_months": len(common),
                "temperature_anomaly_correlation": temperature_correlation,
                "temperature_anomaly_mean_absolute_difference_c": float(
                    common[
                        "temperature_anomaly_difference_alternative_minus_primary_c"
                    ].abs().mean()
                ),
                "precipitation_anomaly_correlation": precipitation_correlation,
                "precipitation_anomaly_mean_absolute_difference_mm": float(
                    common[
                        "precipitation_anomaly_difference_alternative_minus_primary_mm"
                    ].abs().mean()
                ),
                "weather_station_sensitivity_agreement": agreement_grade(
                    temperature_correlation, precipitation_correlation
                ),
                "weather_station_sensitivity_causal_covariate_approved": False,
            }
        )
    comparison["date"] = comparison["date"].dt.date.astype(str)
    return comparison.sort_values(["destination_unit_id", "date"]), pd.DataFrame(
        summary_rows
    ).sort_values("destination_unit_id")


def main() -> None:
    analysis_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    crosswalk = build_alternative_crosswalk()
    required_alternative_codes = set(crosswalk["alternative_weather_station_code"])
    daily, raw_rows_all_dates, alternative_codes = load_alternative_daily(
        required_alternative_codes
    )
    alternative_month = aggregate_station_months(daily, alternative_codes)
    eligible, _ = eligible_station_metadata()
    station_details = eligible[
        [
            "station_abbr",
            "station_name",
            "station_height_masl",
            "station_coordinates_wgs84_lat",
            "station_coordinates_wgs84_lon",
        ]
    ].rename(
        columns={
            "station_name": "weather_station_name",
            "station_height_masl": "weather_station_elevation_m",
            "station_coordinates_wgs84_lat": "weather_station_latitude",
            "station_coordinates_wgs84_lon": "weather_station_longitude",
        }
    )
    alternative_month = alternative_month.merge(
        station_details, on="station_abbr", how="left", validate="many_to_one"
    ).sort_values(["station_abbr", "month_date"])

    primary_month = pd.read_csv(PRIMARY_STATION_MONTH)
    primary_month["month_date"] = pd.to_datetime(
        primary_month["month_date"], errors="raise"
    )
    component = component_diagnostics(crosswalk, primary_month, alternative_month)
    destination_month, destination_summary = build_destination_sensitivity(
        crosswalk, alternative_month
    )

    month_output = alternative_month.copy()
    month_output["month_date"] = month_output["month_date"].dt.date.astype(str)
    month_output["weather_source_id"] = "METEOSWISS_SMN_DAILY_ALTERNATIVE_SELECTED"
    month_output.to_csv(ALTERNATIVE_STATION_MONTH_OUT, index=False, na_rep="NA")
    component.to_csv(COMPONENT_SENSITIVITY_OUT, index=False, na_rep="NA")
    destination_month.to_csv(
        DESTINATION_MONTH_SENSITIVITY_OUT, index=False, na_rep="NA"
    )
    destination_summary.to_csv(DESTINATION_SUMMARY_OUT, index=False, na_rep="NA")

    summary = {
        "analysis_version": analysis_config["analysis_version"],
        "alternative_raw_daily_rows_all_dates": raw_rows_all_dates,
        "alternative_analysis_daily_rows": len(daily),
        "alternative_station_count": len(alternative_codes),
        "alternative_station_codes": alternative_codes,
        "alternative_station_month_rows": len(alternative_month),
        "alternative_station_month_usable_rows": int(
            alternative_month["month_weather_proxy_usable"].sum()
        ),
        "reviewed_component_comparisons": len(component),
        "component_agreement_counts": {
            str(key): int(value)
            for key, value in component["weather_station_sensitivity_agreement"]
            .value_counts()
            .items()
        },
        "median_component_temperature_anomaly_correlation": float(
            component["temperature_anomaly_correlation"].median()
        ),
        "median_component_temperature_anomaly_mean_absolute_difference_c": float(
            component["temperature_anomaly_mean_absolute_difference_c"].median()
        ),
        "median_component_precipitation_anomaly_correlation": float(
            component["precipitation_anomaly_correlation"].median()
        ),
        "median_component_precipitation_anomaly_mean_absolute_difference_mm": float(
            component["precipitation_anomaly_mean_absolute_difference_mm"].median()
        ),
        "destination_units": destination_summary["destination_unit_id"].nunique(),
        "destination_month_rows": len(destination_month),
        "destination_months_with_both_complete_proxies": int(
            destination_month["both_weather_proxies_complete"].sum()
        ),
        "destination_agreement_counts": {
            str(key): int(value)
            for key, value in destination_summary[
                "weather_station_sensitivity_agreement"
            ].value_counts().items()
        },
        "median_destination_temperature_anomaly_correlation": float(
            destination_summary["temperature_anomaly_correlation"].median()
        ),
        "median_destination_precipitation_anomaly_correlation": float(
            destination_summary["precipitation_anomaly_correlation"].median()
        ),
        "causal_covariates_approved": 0,
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# SwissMetNet alternative-station sensitivity

## Design

This robustness check retains the official SwissMetNet universe and the primary module's four daily parameters, 2013 start gate, 80% monthly coverage rule and station-specific 2013–2025 calendar-month analytical normals. For each of the **{len(component)} reviewed resort components**, it replaces the nearest eligible station with the next-nearest distinct eligible station. The required alternatives are **{', '.join(alternative_codes)}**. Their historical and current-year files are checksum-cached through the standard collector.

The resulting destination panel repeats the primary unweighted unique-station aggregation under the alternative assignments. Temperature and precipitation anomalies are compared only where both primary and alternative proxies are complete.

## Component results

- alternative station-month rows: **{len(alternative_month):,}**; usable under the common four-parameter gate: **{int(alternative_month['month_weather_proxy_usable'].sum()):,}**
- component agreement counts: **{summary['component_agreement_counts']}**
- median temperature-anomaly correlation: **{summary['median_component_temperature_anomaly_correlation']:.3f}**
- median temperature-anomaly mean absolute difference: **{summary['median_component_temperature_anomaly_mean_absolute_difference_c']:.2f} °C**
- median precipitation-anomaly correlation: **{summary['median_component_precipitation_anomaly_correlation']:.3f}**
- median precipitation-anomaly mean absolute difference: **{summary['median_component_precipitation_anomaly_mean_absolute_difference_mm']:.1f} mm/month**

The descriptive agreement grade is high when temperature-anomaly correlation is at least 0.90 and precipitation-anomaly correlation at least 0.70; moderate at 0.80 and 0.50; otherwise low. These thresholds organise review and are not causal validation criteria.

## Destination results

The alternative panel contains **{len(destination_month):,} destination-month rows** for **{summary['destination_units']} units**. Both primary and alternative proxies are complete in **{summary['destination_months_with_both_complete_proxies']:,} rows**. Destination agreement counts are **{summary['destination_agreement_counts']}**; the median temperature- and precipitation-anomaly correlations are **{summary['median_destination_temperature_anomaly_correlation']:.3f}** and **{summary['median_destination_precipitation_anomaly_correlation']:.3f}**, respectively.

## Interpretation limit

This test measures assignment sensitivity inside one point-station network. It is not independent gridded validation and does not observe piste conditions, snowfall phase, snowmaking, terrain, aspect or a tourism catchment. The next-nearest station can be farther away or at a very different elevation. `weather_station_sensitivity_causal_covariate_approved` remains false everywhere, and the primary causal weather gate remains closed.

## Outputs

- `data_processed/meteoswiss_alternative_station_month.csv`
- `reports/weather_station_alternative_sensitivity.csv`
- `data_processed/destination_weather_alternative_sensitivity.csv`
- `reports/weather_destination_alternative_summary.csv`
"""
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
