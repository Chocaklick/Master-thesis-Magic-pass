"""Build reproducible SLF IMIS snow proxies for resorts and destinations.

The selected station is a transparent proxy, never a claim that the station is
located on or directly represents the ski slopes.  Distance, elevation gap,
coverage, and a qualitative proxy-quality flag remain in every crosswalk row.
"""
from __future__ import annotations

import calendar
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
MONTH_OUT = ROOT / "data_processed" / "slf_snow_station_month.csv"
WINTER_OUT = ROOT / "data_processed" / "slf_snow_station_winter.csv"
CROSSWALK_OUT = ROOT / "data_processed" / "resort_snow_station_crosswalk.csv"
VULNERABILITY_OUT = ROOT / "data_processed" / "resort_snow_vulnerability.csv"
DESTINATION_MONTH_OUT = ROOT / "data_processed" / "destination_snow_month.csv"
SUMMARY_OUT = ROOT / "reports" / "snow_proxy_summary.json"
REPORT_OUT = ROOT / "reports" / "06_SNOW_SOURCE_AND_PROXY.md"

ANALYSIS_START = pd.Timestamp("2013-01-01")
MONTHLY_END = pd.Timestamp("2026-03-31")
WINTER_END = pd.Timestamp("2026-04-30")
WINTER_MONTHS = {11, 12, 1, 2, 3, 4}
MIN_STATION_WINTER_COVERAGE = 0.80
MIN_MONTH_COVERAGE = 0.80


def exact_metadata(source_id: str) -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if not records:
        raise FileNotFoundError(f"No cached metadata record for {source_id}")
    return max(records, key=lambda record: record["retrieval_date"])


def checked_path(source_id: str) -> Path:
    record = exact_metadata(source_id)
    path = ROOT / record["raw_file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Cached evidence integrity failure: {source_id}")
    return path


def haversine_matrix(
    resort_lat: np.ndarray,
    resort_lon: np.ndarray,
    station_lat: np.ndarray,
    station_lon: np.ndarray,
) -> np.ndarray:
    lat1 = np.radians(resort_lat)[:, None]
    lon1 = np.radians(resort_lon)[:, None]
    lat2 = np.radians(station_lat)[None, :]
    lon2 = np.radians(station_lon)[None, :]
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2
    )
    return 6371.0088 * 2 * np.arcsin(np.sqrt(value))


def winter_start_year(dates: pd.Series) -> pd.Series:
    return dates.dt.year.where(dates.dt.month.ge(11), dates.dt.year - 1)


def winter_expected_days(start_year: int) -> int:
    return 30 + 31 + 31 + calendar.monthrange(start_year + 1, 2)[1] + 31 + 30


def aggregate_months(daily: pd.DataFrame, station_codes: list[str]) -> pd.DataFrame:
    monthly_daily = daily[daily["date"].le(MONTHLY_END)].copy()
    monthly_daily["date"] = monthly_daily["date"].dt.to_period("M").dt.to_timestamp()
    grouped = monthly_daily.groupby(["station_code", "date"], observed=True)
    observed = grouped.agg(
        snow_depth_observed_days=("snow_depth_valid", "sum"),
        snow_depth_invalid_negative_days=("snow_depth_invalid_negative", "sum"),
        snow_depth_mean_cm=("snow_depth_cm", "mean"),
        snow_depth_median_cm=("snow_depth_cm", "median"),
        snow_depth_max_cm=("snow_depth_cm", "max"),
        days_snow_depth_ge_10cm=("snow_depth_ge_10cm", "sum"),
        days_snow_depth_ge_20cm=("snow_depth_ge_20cm", "sum"),
        days_snow_depth_ge_30cm=("snow_depth_ge_30cm", "sum"),
        modeled_new_snow_observed_days=("modeled_new_snow_valid", "sum"),
        modeled_new_snow_total_cm=("modeled_new_snow_cm", lambda values: values.sum(min_count=1)),
    ).reset_index()
    grid = pd.MultiIndex.from_product(
        [
            station_codes,
            pd.date_range(ANALYSIS_START, MONTHLY_END, freq="MS"),
        ],
        names=["station_code", "date"],
    ).to_frame(index=False)
    month = grid.merge(observed, how="left", on=["station_code", "date"], validate="one_to_one")
    for column in [
        "snow_depth_observed_days",
        "snow_depth_invalid_negative_days",
        "days_snow_depth_ge_10cm",
        "days_snow_depth_ge_20cm",
        "days_snow_depth_ge_30cm",
        "modeled_new_snow_observed_days",
    ]:
        month[column] = month[column].fillna(0).astype("int64")
    month["calendar_days"] = month["date"].dt.days_in_month
    month["snow_depth_observation_coverage_share"] = (
        month["snow_depth_observed_days"] / month["calendar_days"]
    )
    denominator = month["snow_depth_observed_days"].replace(0, np.nan)
    for threshold in [10, 20, 30]:
        month[f"share_observed_days_snow_depth_ge_{threshold}cm"] = (
            month[f"days_snow_depth_ge_{threshold}cm"] / denominator
        )
    month["month_snow_proxy_usable"] = month[
        "snow_depth_observation_coverage_share"
    ].ge(MIN_MONTH_COVERAGE)
    month["source_id"] = "SLF_IMIS_DAILY_SNOW"
    return month


def aggregate_winters(daily: pd.DataFrame, station_codes: list[str]) -> pd.DataFrame:
    winter_daily = daily[
        daily["date"].between(ANALYSIS_START, WINTER_END)
        & daily["date"].dt.month.isin(WINTER_MONTHS)
    ].copy()
    winter_daily["winter_start_year"] = winter_start_year(winter_daily["date"])
    winter_daily = winter_daily[winter_daily["winter_start_year"].between(2013, 2025)]
    observed = winter_daily.groupby(
        ["station_code", "winter_start_year"], observed=True
    ).agg(
        snow_depth_observed_days=("snow_depth_valid", "sum"),
        snow_depth_invalid_negative_days=("snow_depth_invalid_negative", "sum"),
        winter_mean_snow_depth_cm=("snow_depth_cm", "mean"),
        winter_median_snow_depth_cm=("snow_depth_cm", "median"),
        winter_max_snow_depth_cm=("snow_depth_cm", "max"),
        days_snow_depth_ge_10cm=("snow_depth_ge_10cm", "sum"),
        days_snow_depth_ge_20cm=("snow_depth_ge_20cm", "sum"),
        days_snow_depth_ge_30cm=("snow_depth_ge_30cm", "sum"),
        modeled_new_snow_observed_days=("modeled_new_snow_valid", "sum"),
        modeled_new_snow_total_cm=("modeled_new_snow_cm", lambda values: values.sum(min_count=1)),
    ).reset_index()
    grid = pd.MultiIndex.from_product(
        [station_codes, list(range(2013, 2026))],
        names=["station_code", "winter_start_year"],
    ).to_frame(index=False)
    winter = grid.merge(
        observed,
        how="left",
        on=["station_code", "winter_start_year"],
        validate="one_to_one",
    )
    for column in [
        "snow_depth_observed_days",
        "snow_depth_invalid_negative_days",
        "days_snow_depth_ge_10cm",
        "days_snow_depth_ge_20cm",
        "days_snow_depth_ge_30cm",
        "modeled_new_snow_observed_days",
    ]:
        winter[column] = winter[column].fillna(0).astype("int64")
    winter["winter_expected_days"] = winter["winter_start_year"].map(winter_expected_days)
    winter["snow_depth_observation_coverage_share"] = (
        winter["snow_depth_observed_days"] / winter["winter_expected_days"]
    )
    denominator = winter["snow_depth_observed_days"].replace(0, np.nan)
    for threshold in [10, 20, 30]:
        winter[f"share_observed_days_snow_depth_ge_{threshold}cm"] = (
            winter[f"days_snow_depth_ge_{threshold}cm"] / denominator
        )
    winter["winter_snow_proxy_usable"] = winter[
        "snow_depth_observation_coverage_share"
    ].ge(MIN_MONTH_COVERAGE)
    winter["winter_season"] = winter["winter_start_year"].astype(str) + "/" + (
        winter["winter_start_year"] + 1
    ).astype(str)
    winter["source_id"] = "SLF_IMIS_DAILY_SNOW"
    return winter


def station_long_term_features(winter: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for station_code, group in winter.groupby("station_code", observed=True):
        usable = group[group["winter_snow_proxy_usable"]].copy()
        mean_depth = usable["winter_mean_snow_depth_cm"].mean()
        standard_deviation = usable["winter_mean_snow_depth_cm"].std(ddof=1)
        trend = np.nan
        if len(usable) >= 5:
            trend = float(
                np.polyfit(
                    usable["winter_start_year"].astype(float),
                    usable["winter_mean_snow_depth_cm"].astype(float),
                    1,
                )[0]
            )
        rows.append(
            {
                "station_code": station_code,
                "usable_winter_seasons": len(usable),
                "mean_winter_snow_depth_cm": mean_depth,
                "snow_variability_cv": (
                    standard_deviation / mean_depth
                    if pd.notna(mean_depth) and mean_depth > 0
                    else np.nan
                ),
                "snow_depth_trend_cm_per_year": trend,
                "snow_reliability_share_days_ge_30cm": (
                    usable["days_snow_depth_ge_30cm"].sum()
                    / usable["snow_depth_observed_days"].sum()
                    if usable["snow_depth_observed_days"].sum() > 0
                    else np.nan
                ),
                "low_snow_winter_frequency": (
                    usable["share_observed_days_snow_depth_ge_30cm"].lt(0.5).mean()
                    if len(usable)
                    else np.nan
                ),
                "extreme_low_snow_winter_count": (
                    int(
                        usable["winter_mean_snow_depth_cm"]
                        .lt(mean_depth - standard_deviation)
                        .sum()
                    )
                    if len(usable) >= 2 and pd.notna(standard_deviation)
                    else 0
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    raw_path = checked_path("SLF_IMIS_DAILY_SNOW")
    station_path = checked_path("SLF_IMIS_STATIONS")
    raw = pd.read_csv(raw_path, dtype=str, keep_default_na=False)
    required = {"station_code", "measure_date", "hyear", "HS", "HN_1D"}
    if set(raw.columns) != required:
        raise ValueError(f"Unexpected SLF daily schema: {raw.columns.tolist()}")
    if raw.duplicated(["station_code", "measure_date"]).any():
        raise ValueError("Duplicate station-date rows in SLF daily data")
    stations = pd.read_csv(station_path)
    snow_stations = stations[
        stations["station_type"].astype(str).str.startswith("SNOW")
        & stations["station_code"].isin(raw["station_code"])
    ].copy()
    station_codes = sorted(snow_stations["station_code"].unique())

    daily = raw[raw["station_code"].isin(station_codes)].copy()
    daily["date"] = pd.to_datetime(daily["measure_date"], utc=True, errors="raise").dt.tz_localize(None)
    daily["snow_depth_source_token"] = daily["HS"]
    daily["modeled_new_snow_source_token"] = daily["HN_1D"]
    daily["snow_depth_cm_raw_numeric"] = pd.to_numeric(daily["HS"], errors="coerce")
    daily["snow_depth_valid"] = daily["snow_depth_cm_raw_numeric"].ge(0)
    daily["snow_depth_invalid_negative"] = daily["snow_depth_cm_raw_numeric"].lt(0)
    daily["snow_depth_cm"] = daily["snow_depth_cm_raw_numeric"].where(
        daily["snow_depth_valid"]
    )
    daily["modeled_new_snow_cm"] = pd.to_numeric(daily["HN_1D"], errors="coerce")
    daily["modeled_new_snow_valid"] = daily["modeled_new_snow_cm"].ge(0)
    daily["modeled_new_snow_cm"] = daily["modeled_new_snow_cm"].where(
        daily["modeled_new_snow_valid"]
    )
    for threshold in [10, 20, 30]:
        daily[f"snow_depth_ge_{threshold}cm"] = (
            daily["snow_depth_valid"] & daily["snow_depth_cm"].ge(threshold)
        )

    month = aggregate_months(daily, station_codes)
    winter = aggregate_winters(daily, station_codes)
    month = month.merge(
        snow_stations[
            ["station_code", "label", "active", "lon", "lat", "elevation", "station_type"]
        ],
        on="station_code",
        validate="many_to_one",
    )
    winter = winter.merge(
        snow_stations[
            ["station_code", "label", "active", "lon", "lat", "elevation", "station_type"]
        ],
        on="station_code",
        validate="many_to_one",
    )
    month.to_csv(MONTH_OUT, index=False, na_rep="NA")
    winter.to_csv(WINTER_OUT, index=False, na_rep="NA")

    station_coverage = winter.groupby("station_code", observed=True).agg(
        valid_winter_days=("snow_depth_observed_days", "sum"),
        expected_winter_days=("winter_expected_days", "sum"),
        usable_winter_seasons=("winter_snow_proxy_usable", "sum"),
    )
    station_coverage["winter_coverage_share_2013_2025"] = (
        station_coverage["valid_winter_days"] / station_coverage["expected_winter_days"]
    )
    eligible_codes = station_coverage.index[
        station_coverage["winter_coverage_share_2013_2025"].ge(
            MIN_STATION_WINTER_COVERAGE
        )
    ]
    eligible = snow_stations[snow_stations["station_code"].isin(eligible_codes)].copy()
    eligible = eligible.merge(
        station_coverage.reset_index(), on="station_code", validate="one_to_one"
    ).sort_values("station_code")
    if eligible.empty:
        raise ValueError("No SLF station passes the longitudinal coverage gate")

    resorts = pd.read_csv(ROOT / "data_processed" / "resort_master.csv")
    distances = haversine_matrix(
        resorts["latitude"].to_numpy(float),
        resorts["longitude"].to_numpy(float),
        eligible["lat"].to_numpy(float),
        eligible["lon"].to_numpy(float),
    )
    selected_indexes = distances.argmin(axis=1)
    selected = eligible.iloc[selected_indexes].reset_index(drop=True)
    selected_distances = distances[np.arange(len(resorts)), selected_indexes]
    crosswalk = resorts[
        [
            "resort_id",
            "resort_name_canonical",
            "latitude",
            "longitude",
            "altitude_top_m",
        ]
    ].reset_index(drop=True)
    crosswalk["snow_station_code"] = selected["station_code"]
    crosswalk["snow_station_label"] = selected["label"]
    crosswalk["snow_station_latitude"] = selected["lat"]
    crosswalk["snow_station_longitude"] = selected["lon"]
    crosswalk["snow_station_elevation_m"] = selected["elevation"]
    crosswalk["snow_station_active_snapshot"] = selected["active"]
    crosswalk["snow_station_type"] = selected["station_type"]
    crosswalk["snow_station_distance_km"] = selected_distances
    crosswalk["snow_station_elevation_gap_to_resort_top_m"] = (
        crosswalk["snow_station_elevation_m"] - crosswalk["altitude_top_m"]
    ).abs()
    crosswalk["snow_station_winter_coverage_share_2013_2025"] = selected[
        "winter_coverage_share_2013_2025"
    ]
    crosswalk["snow_station_usable_winter_seasons"] = selected[
        "usable_winter_seasons"
    ].astype(int)
    high = crosswalk["snow_station_distance_km"].le(10) & crosswalk[
        "snow_station_elevation_gap_to_resort_top_m"
    ].le(500)
    moderate = crosswalk["snow_station_distance_km"].le(25) & crosswalk[
        "snow_station_elevation_gap_to_resort_top_m"
    ].le(1000)
    crosswalk["snow_proxy_quality"] = np.select(
        [high, moderate], ["high", "moderate"], default="low"
    )
    crosswalk["assignment_method"] = (
        "nearest_geographic_SLF_snow_station_with_at_least_80pct_winter_coverage_2013_2025"
    )
    crosswalk["relationship_type"] = "external_mountain_station_proxy_only"
    crosswalk["direct_slope_representation"] = False
    crosswalk["source_ids"] = "SLF_IMIS_STATIONS|SLF_IMIS_DAILY_SNOW"
    crosswalk["limitations"] = (
        "IMIS stations support avalanche monitoring and can differ from the resort in "
        "terrain, aspect, exposure, elevation, grooming, and snowmaking."
    )
    crosswalk.to_csv(CROSSWALK_OUT, index=False)

    station_features = station_long_term_features(winter)
    vulnerability = crosswalk.merge(
        station_features,
        left_on="snow_station_code",
        right_on="station_code",
        how="left",
        validate="many_to_one",
    ).drop(columns="station_code")
    vulnerability["snow_vulnerability_proxy"] = (
        1 - vulnerability["snow_reliability_share_days_ge_30cm"]
    )
    vulnerability["snow_climate_feature_ready"] = (
        vulnerability["snow_proxy_quality"].isin(["high", "moderate"])
        & vulnerability["usable_winter_seasons"].ge(10)
    )
    vulnerability["causal_covariate_approved"] = False
    vulnerability.to_csv(VULNERABILITY_OUT, index=False, na_rep="NA")

    config = json.loads(
        (ROOT / "config" / "treatment_destination_review.json").read_text(
            encoding="utf-8"
        )
    )
    destination_station_rows = []
    quality_order = {"high": 0, "moderate": 1, "low": 2}
    for unit in config["units"]:
        if not unit["eligible_for_reviewed_outcome_panel"]:
            continue
        links = crosswalk[
            crosswalk["resort_id"].isin(unit["component_resort_ids"])
        ].drop_duplicates("snow_station_code")
        worst_quality = max(
            links["snow_proxy_quality"], key=lambda value: quality_order[value]
        )
        for row in links.itertuples(index=False):
            destination_station_rows.append(
                {
                    "destination_unit_id": unit["destination_unit_id"],
                    "destination_name": unit["destination_name"],
                    "snow_station_code": row.snow_station_code,
                    "snow_station_distance_km": row.snow_station_distance_km,
                    "snow_station_elevation_gap_to_resort_top_m": row.snow_station_elevation_gap_to_resort_top_m,
                    "destination_snow_proxy_quality": worst_quality,
                }
            )
    destination_station = pd.DataFrame(destination_station_rows)
    destination_month_rows = []
    for destination_unit_id, links in destination_station.groupby(
        "destination_unit_id", observed=True
    ):
        scoped = month[month["station_code"].isin(links["snow_station_code"])].copy()
        expected_station_count = links["snow_station_code"].nunique()
        for date, group in scoped.groupby("date", observed=True):
            usable = group["month_snow_proxy_usable"]
            complete = int(usable.sum()) == expected_station_count
            destination_month_rows.append(
                {
                    "destination_unit_id": destination_unit_id,
                    "destination_name": links["destination_name"].iloc[0],
                    "date": date.date().isoformat(),
                    "snow_station_count_expected": expected_station_count,
                    "snow_station_months_usable": int(usable.sum()),
                    "complete_snow_proxy": complete,
                    "snow_depth_mean_cm": (
                        group["snow_depth_mean_cm"].mean() if complete else np.nan
                    ),
                    "snow_depth_median_cm": (
                        group["snow_depth_median_cm"].mean() if complete else np.nan
                    ),
                    "share_observed_days_snow_depth_ge_10cm": (
                        group["share_observed_days_snow_depth_ge_10cm"].mean()
                        if complete
                        else np.nan
                    ),
                    "share_observed_days_snow_depth_ge_20cm": (
                        group["share_observed_days_snow_depth_ge_20cm"].mean()
                        if complete
                        else np.nan
                    ),
                    "share_observed_days_snow_depth_ge_30cm": (
                        group["share_observed_days_snow_depth_ge_30cm"].mean()
                        if complete
                        else np.nan
                    ),
                    "modeled_new_snow_total_cm_mean_across_stations": (
                        group["modeled_new_snow_total_cm"].mean()
                        if complete
                        else np.nan
                    ),
                    "snow_depth_observation_coverage_share_mean": group[
                        "snow_depth_observation_coverage_share"
                    ].mean(),
                    "destination_snow_proxy_quality": links[
                        "destination_snow_proxy_quality"
                    ].iloc[0],
                    "snow_source_id": "SLF_IMIS_DAILY_SNOW",
                    "snow_direct_slope_representation": False,
                }
            )
    destination_month = pd.DataFrame(destination_month_rows).sort_values(
        ["destination_unit_id", "date"]
    )
    destination_month.to_csv(DESTINATION_MONTH_OUT, index=False, na_rep="NA")

    quality_counts = crosswalk["snow_proxy_quality"].value_counts().to_dict()
    summary = {
        "raw_daily_rows": int(len(raw)),
        "raw_daily_start": raw["measure_date"].min(),
        "raw_daily_end": raw["measure_date"].max(),
        "snow_stations_with_daily_data": len(station_codes),
        "stations_passing_80pct_winter_coverage_gate": int(len(eligible)),
        "negative_snow_depth_values_treated_as_invalid": int(
            daily["snow_depth_invalid_negative"].sum()
        ),
        "station_month_rows": int(len(month)),
        "station_winter_rows": int(len(winter)),
        "resort_crosswalk_rows": int(len(crosswalk)),
        "resort_proxy_quality_counts": quality_counts,
        "resorts_with_snow_climate_feature_ready": int(
            vulnerability["snow_climate_feature_ready"].sum()
        ),
        "destination_month_rows": int(len(destination_month)),
        "destination_month_complete_snow_proxy_rows": int(
            destination_month["complete_snow_proxy"].sum()
        ),
        "destination_units": int(destination_month["destination_unit_id"].nunique()),
        "causal_covariates_approved": 0,
        "no_imputation": True,
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Snow-source review and SLF proxy construction

Generated reproducibly by `src/data_processing/build_snow_proxy_panel.py`.

## Source decision

Three authoritative options were compared before collection:

| Source | Strength | Limitation | Decision |
|---|---|---|---|
| WSL Institute for Snow and Avalanche Research SLF, IMIS historical measurements | Direct daily mountain snow-depth observations; station coordinates/elevation; static CSV; CC BY 4.0; DOI 10.16904/envidat.406 | Avalanche-monitoring sites, often above treeline; some raw values are not regularly corrected; not direct piste observations | **Selected for the first snow proxy** |
| MeteoSwiss Open Government Data, SwissMetNet | Official station observations for temperature, precipitation and snow at several resolutions with historical chunks | Lower-elevation/general meteorological network; a separate spatial/elevation match is required | Retain for a later temperature/precipitation block |
| Copernicus ERA5-Land | Spatially complete 0.1° hourly reanalysis from 1950, CC-BY, DOI 10.24381/cds.e2161bac | Modelled grid, coarse for Alpine topography; CDS workflow and larger extraction | Retain as a gridded sensitivity/fallback source |

## Collected SLF data

- Raw daily rows: **{summary['raw_daily_rows']:,}**, from {summary['raw_daily_start'][:10]} to {summary['raw_daily_end'][:10]}.
- Snow-station codes with daily data: **{summary['snow_stations_with_daily_data']}**.
- Stations passing the predeclared 80% winter-day coverage gate for 2013/14–2025/26: **{summary['stations_passing_80pct_winter_coverage_gate']}**.
- Negative physical snow-depth values retained in raw data but treated as invalid in derived measures: **{summary['negative_snow_depth_values_treated_as_invalid']:,}**.

Daily `HS` is the median total snowpack depth over the preceding 24 hours at 06:00 UTC. `HN_1D` is modelled by SNOWPACK, so every derived new-snow field is labelled `modeled_`; it is not presented as a direct gauge observation. No missing or physically negative snow depth is imputed.

## Resort proxy assignment

Each of the **{summary['resort_crosswalk_rows']} resort listings** is assigned to the geographically nearest SLF snow station among those passing the longitudinal coverage gate. The crosswalk preserves distance, station elevation, gap to the published resort-top altitude, station activity/type, coverage, and the assignment rule.

- High proxy quality (≤10 km and ≤500 m elevation gap): **{quality_counts.get('high', 0)}** resorts.
- Moderate proxy quality (≤25 km and ≤1,000 m elevation gap): **{quality_counts.get('moderate', 0)}** resorts.
- Low proxy quality: **{quality_counts.get('low', 0)}** resorts.

This classification measures proxy comparability, not measurement accuracy. IMIS stations can differ from a resort in aspect, terrain, wind exposure, grooming and snowmaking. `direct_slope_representation` is therefore false for every row.

## Derived outputs

- `{MONTH_OUT.relative_to(ROOT).as_posix()}`: station-month snow depth, observation coverage, threshold-day shares and modelled new snow.
- `{WINTER_OUT.relative_to(ROOT).as_posix()}`: November–April station-winter summaries.
- `{CROSSWALK_OUT.relative_to(ROOT).as_posix()}`: auditable resort-to-station proxy assignments.
- `{VULNERABILITY_OUT.relative_to(ROOT).as_posix()}`: long-run reliability, variability, trend and low-snow indicators for exploratory use.
- `{DESTINATION_MONTH_OUT.relative_to(ROOT).as_posix()}`: snow proxies for the 11 reviewed destination units; multi-station destinations use an unweighted mean only when all assigned station-months pass 80% daily coverage.

The destination panel contains **{summary['destination_month_complete_snow_proxy_rows']:,} complete snow-proxy months** out of {summary['destination_month_rows']:,}. No snow variable is approved as a causal covariate yet; source representativeness and remaining weather controls must be evaluated in robustness analyses.
"""
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
