"""Build reproducible MeteoSwiss temperature and precipitation proxies.

The selected SwissMetNet stations represent regional weather near the reviewed
resort listings. They are not direct piste measurements. Distance, station
elevation, coverage and the absence of direct-slope representation remain
explicit in every crosswalk and destination-month output.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
SELECTED_CONFIG = ROOT / "config" / "meteoswiss_selected_station_files.json"
DESTINATION_CONFIG = ROOT / "config" / "treatment_destination_review.json"

STATION_MONTH_OUT = ROOT / "data_processed" / "meteoswiss_station_month.csv"
CROSSWALK_OUT = ROOT / "data_processed" / "resort_weather_station_crosswalk.csv"
DESTINATION_MONTH_OUT = ROOT / "data_processed" / "destination_weather_month.csv"
SUMMARY_OUT = ROOT / "reports" / "weather_proxy_summary.json"
REPORT_OUT = ROOT / "reports" / "07_WEATHER_PROXY.md"

ANALYSIS_START = pd.Timestamp("2013-01-01")
ANALYSIS_END = pd.Timestamp("2026-03-31")
CLIMATOLOGY_END = pd.Timestamp("2025-12-31")
MIN_MONTH_COVERAGE = 0.80
CORE_PARAMETERS = ["tre200d0", "tre200dn", "tre200dx", "rre150d0"]
DAILY_COLUMNS = ["station_abbr", "reference_timestamp", *CORE_PARAMETERS]


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


def load_selected_daily() -> tuple[pd.DataFrame, int, list[str]]:
    sources = json.loads(SELECTED_CONFIG.read_text(encoding="utf-8"))
    if len(sources) != 14:
        raise ValueError("Expected historical and recent files for seven stations")
    frames = []
    for source in sources:
        source_id = source["source_id"]
        frame = pd.read_csv(
            checked_path(source_id),
            sep=";",
            encoding="cp1252",
            usecols=DAILY_COLUMNS,
            dtype="string",
            keep_default_na=False,
        )
        if set(frame.columns) != set(DAILY_COLUMNS):
            raise ValueError(f"Unexpected daily schema for {source_id}")
        frame["source_id"] = source_id
        frames.append(frame)

    raw = pd.concat(frames, ignore_index=True)
    raw_rows_all_dates = len(raw)
    raw["date"] = pd.to_datetime(
        raw["reference_timestamp"], format="%d.%m.%Y %H:%M", errors="raise"
    )
    raw = raw[raw["date"].between(ANALYSIS_START, ANALYSIS_END)].copy()
    if raw.duplicated(["station_abbr", "date"]).any():
        raise ValueError("Duplicate station-date rows across historical/recent files")
    station_codes = sorted(raw["station_abbr"].unique())
    if len(station_codes) != 7:
        raise ValueError(f"Expected seven selected stations, found {station_codes}")
    for parameter in CORE_PARAMETERS:
        raw[parameter] = pd.to_numeric(raw[parameter], errors="coerce")

    raw["invalid_negative_precipitation"] = raw["rre150d0"].lt(0)
    raw["rre150d0"] = raw["rre150d0"].where(
        ~raw["invalid_negative_precipitation"]
    )
    impossible_temperature = (
        raw["tre200dn"].gt(raw["tre200d0"])
        | raw["tre200d0"].gt(raw["tre200dx"])
    )
    if impossible_temperature.any():
        raise ValueError("Daily minimum/mean/maximum temperature ordering violated")
    return raw, raw_rows_all_dates, station_codes


def aggregate_station_months(
    daily: pd.DataFrame, station_codes: list[str]
) -> pd.DataFrame:
    daily = daily.copy()
    daily["month_date"] = daily["date"].dt.to_period("M").dt.to_timestamp()
    daily["temperature_mean_valid"] = daily["tre200d0"].notna()
    daily["temperature_min_valid"] = daily["tre200dn"].notna()
    daily["temperature_max_valid"] = daily["tre200dx"].notna()
    daily["precipitation_valid"] = daily["rre150d0"].notna()
    daily["freezing_day"] = daily["temperature_min_valid"] & daily["tre200dn"].le(0)
    daily["precipitation_day_ge_1mm"] = (
        daily["precipitation_valid"] & daily["rre150d0"].ge(1)
    )

    grouped = daily.groupby(["station_abbr", "month_date"], observed=True)
    observed = grouped.agg(
        daily_rows_present=("date", "size"),
        temperature_mean_observed_days=("temperature_mean_valid", "sum"),
        temperature_min_observed_days=("temperature_min_valid", "sum"),
        temperature_max_observed_days=("temperature_max_valid", "sum"),
        precipitation_observed_days=("precipitation_valid", "sum"),
        invalid_negative_precipitation_days=("invalid_negative_precipitation", "sum"),
        air_temperature_mean_c=("tre200d0", "mean"),
        air_temperature_daily_min_mean_c=("tre200dn", "mean"),
        air_temperature_daily_max_mean_c=("tre200dx", "mean"),
        freezing_days=("freezing_day", "sum"),
        precipitation_total_mm=("rre150d0", lambda values: values.sum(min_count=1)),
        precipitation_days_ge_1mm=("precipitation_day_ge_1mm", "sum"),
    ).reset_index()

    grid = pd.MultiIndex.from_product(
        [
            station_codes,
            pd.date_range(ANALYSIS_START, ANALYSIS_END, freq="MS"),
        ],
        names=["station_abbr", "month_date"],
    ).to_frame(index=False)
    month = grid.merge(
        observed, on=["station_abbr", "month_date"], how="left", validate="one_to_one"
    )
    month["calendar_days"] = month["month_date"].dt.days_in_month
    count_columns = [
        "daily_rows_present",
        "temperature_mean_observed_days",
        "temperature_min_observed_days",
        "temperature_max_observed_days",
        "precipitation_observed_days",
        "invalid_negative_precipitation_days",
        "freezing_days",
        "precipitation_days_ge_1mm",
    ]
    month[count_columns] = month[count_columns].fillna(0).astype(int)
    for prefix in ["temperature_mean", "temperature_min", "temperature_max", "precipitation"]:
        month[f"{prefix}_coverage_share"] = (
            month[f"{prefix}_observed_days"] / month["calendar_days"]
        )
    month["freezing_day_share_observed"] = (
        month["freezing_days"]
        / month["temperature_min_observed_days"].replace(0, np.nan)
    )
    month["precipitation_day_ge_1mm_share_observed"] = (
        month["precipitation_days_ge_1mm"]
        / month["precipitation_observed_days"].replace(0, np.nan)
    )
    coverage_columns = [
        "temperature_mean_coverage_share",
        "temperature_min_coverage_share",
        "temperature_max_coverage_share",
        "precipitation_coverage_share",
    ]
    month["month_weather_proxy_usable"] = month[coverage_columns].ge(
        MIN_MONTH_COVERAGE
    ).all(axis=1)

    baseline = month[
        month["month_weather_proxy_usable"]
        & month["month_date"].le(CLIMATOLOGY_END)
    ].copy()
    baseline["calendar_month"] = baseline["month_date"].dt.month
    climatology = baseline.groupby(
        ["station_abbr", "calendar_month"], observed=True
    ).agg(
        climatology_years=("month_date", "size"),
        air_temperature_2013_2025_normal_c=("air_temperature_mean_c", "mean"),
        precipitation_2013_2025_normal_mm=("precipitation_total_mm", "mean"),
    ).reset_index()
    month["calendar_month"] = month["month_date"].dt.month
    month = month.merge(
        climatology,
        on=["station_abbr", "calendar_month"],
        how="left",
        validate="many_to_one",
    )
    month["air_temperature_anomaly_c"] = (
        month["air_temperature_mean_c"]
        - month["air_temperature_2013_2025_normal_c"]
    ).where(month["month_weather_proxy_usable"])
    month["precipitation_anomaly_mm"] = (
        month["precipitation_total_mm"]
        - month["precipitation_2013_2025_normal_mm"]
    ).where(month["month_weather_proxy_usable"])
    month["precipitation_ratio_to_2013_2025_normal"] = (
        month["precipitation_total_mm"]
        / month["precipitation_2013_2025_normal_mm"].replace(0, np.nan)
    ).where(month["month_weather_proxy_usable"])
    month["weather_source_id"] = "METEOSWISS_SMN_DAILY_SELECTED"
    month["precipitation_observation_window"] = "06:00_UTC_to_06:00_UTC_next_day"
    return month


def eligible_station_metadata() -> tuple[pd.DataFrame, int]:
    stations = pd.read_csv(
        checked_path("METEOSWISS_SMN_STATIONS"),
        sep=";",
        encoding="cp1252",
        dtype="string",
        keep_default_na=False,
    )
    inventory = pd.read_csv(
        checked_path("METEOSWISS_SMN_INVENTORY"),
        sep=";",
        encoding="cp1252",
        dtype="string",
        keep_default_na=False,
    )
    inventory = inventory[inventory["parameter_shortname"].isin(CORE_PARAMETERS)].copy()
    inventory["data_since_parsed"] = pd.to_datetime(
        inventory["data_since"], format="%d.%m.%Y %H:%M", errors="raise"
    )
    eligible_codes = []
    for station_code, group in inventory.groupby("station_abbr", observed=True):
        parameter_coverage = group.groupby("parameter_shortname", observed=True).agg(
            earliest=("data_since_parsed", "min"),
            current=("data_till", lambda values: values.eq("").any()),
        )
        if (
            set(CORE_PARAMETERS).issubset(parameter_coverage.index)
            and parameter_coverage.loc[CORE_PARAMETERS, "earliest"].le(ANALYSIS_START).all()
            and parameter_coverage.loc[CORE_PARAMETERS, "current"].all()
        ):
            eligible_codes.append(station_code)
    eligible = stations[stations["station_abbr"].isin(eligible_codes)].copy()
    numeric_columns = [
        "station_height_masl",
        "station_coordinates_wgs84_lat",
        "station_coordinates_wgs84_lon",
    ]
    for column in numeric_columns:
        eligible[column] = pd.to_numeric(eligible[column], errors="coerce")
    eligible = eligible.dropna(subset=numeric_columns).sort_values("station_abbr")
    return eligible, len(eligible)


def build_crosswalk(
    available_station_codes: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    config = json.loads(DESTINATION_CONFIG.read_text(encoding="utf-8"))
    units = [unit for unit in config["units"] if unit["eligible_for_reviewed_outcome_panel"]]
    resort_to_unit = {
        resort_id: (unit["destination_unit_id"], unit["destination_name"])
        for unit in units
        for resort_id in unit["component_resort_ids"]
    }
    resorts = pd.read_csv(ROOT / "data_processed" / "resort_master.csv")
    components = resorts[resorts["resort_id"].isin(resort_to_unit)].copy()
    if len(components) != len(resort_to_unit):
        raise ValueError("A reviewed component resort is missing from resort_master.csv")

    eligible, candidate_count = eligible_station_metadata()
    distances = haversine_matrix(
        components["latitude"].to_numpy(float),
        components["longitude"].to_numpy(float),
        eligible["station_coordinates_wgs84_lat"].to_numpy(float),
        eligible["station_coordinates_wgs84_lon"].to_numpy(float),
    )
    selected_indexes = distances.argmin(axis=1)
    selected = eligible.iloc[selected_indexes].reset_index(drop=True)
    selected_distances = distances[np.arange(len(components)), selected_indexes]
    expected_selected = set(selected["station_abbr"])
    if expected_selected != set(available_station_codes):
        raise ValueError(
            "Downloaded station set differs from nearest eligible assignments: "
            f"downloaded={available_station_codes}, expected={sorted(expected_selected)}"
        )

    crosswalk = components[
        ["resort_id", "resort_name_canonical", "latitude", "longitude", "altitude_top_m"]
    ].reset_index(drop=True)
    crosswalk["destination_unit_id"] = crosswalk["resort_id"].map(
        lambda value: resort_to_unit[value][0]
    )
    crosswalk["destination_name"] = crosswalk["resort_id"].map(
        lambda value: resort_to_unit[value][1]
    )
    crosswalk["weather_station_code"] = selected["station_abbr"]
    crosswalk["weather_station_name"] = selected["station_name"]
    crosswalk["weather_station_latitude"] = selected[
        "station_coordinates_wgs84_lat"
    ]
    crosswalk["weather_station_longitude"] = selected[
        "station_coordinates_wgs84_lon"
    ]
    crosswalk["weather_station_elevation_m"] = selected["station_height_masl"]
    crosswalk["weather_station_distance_km"] = selected_distances
    crosswalk["weather_station_elevation_gap_to_resort_top_m"] = (
        crosswalk["weather_station_elevation_m"] - crosswalk["altitude_top_m"]
    ).abs()
    crosswalk["candidate_station_count"] = candidate_count
    crosswalk["weather_proxy_quality"] = np.select(
        [
            crosswalk["weather_station_distance_km"].le(10),
            crosswalk["weather_station_distance_km"].le(20),
        ],
        ["high", "moderate"],
        default="low",
    )
    crosswalk["assignment_method"] = (
        "nearest_current_SwissMetNet_station_with_all_four_daily_parameters_since_2013"
    )
    crosswalk["relationship_type"] = "regional_weather_station_proxy_only"
    crosswalk["direct_slope_representation"] = False
    crosswalk["weather_causal_covariate_approved"] = False
    crosswalk["source_ids"] = (
        "METEOSWISS_SMN_STATIONS|METEOSWISS_SMN_INVENTORY|"
        "METEOSWISS_SMN_DAILY_SELECTED"
    )
    crosswalk["limitations"] = (
        "Station weather can differ from the ski area because of elevation, terrain, "
        "aspect and local precipitation gradients; use primarily as a regional anomaly proxy."
    )
    return crosswalk.sort_values(["destination_unit_id", "resort_id"]), eligible


def build_destination_month(
    station_month: pd.DataFrame, crosswalk: pd.DataFrame
) -> pd.DataFrame:
    quality_order = {"high": 0, "moderate": 1, "low": 2}
    links = crosswalk.drop_duplicates(
        ["destination_unit_id", "weather_station_code"]
    ).copy()
    rows = []
    metric_columns = [
        "air_temperature_mean_c",
        "air_temperature_daily_min_mean_c",
        "air_temperature_daily_max_mean_c",
        "air_temperature_anomaly_c",
        "freezing_day_share_observed",
        "precipitation_total_mm",
        "precipitation_anomaly_mm",
        "precipitation_ratio_to_2013_2025_normal",
        "precipitation_day_ge_1mm_share_observed",
    ]
    for destination_unit_id, destination_links in links.groupby(
        "destination_unit_id", observed=True
    ):
        expected_count = destination_links["weather_station_code"].nunique()
        worst_quality = max(
            destination_links["weather_proxy_quality"],
            key=lambda value: quality_order[value],
        )
        scoped = station_month[
            station_month["station_abbr"].isin(
                destination_links["weather_station_code"]
            )
        ]
        for date, group in scoped.groupby("month_date", observed=True):
            usable_count = int(group["month_weather_proxy_usable"].sum())
            complete = usable_count == expected_count and len(group) == expected_count
            row = {
                "destination_unit_id": destination_unit_id,
                "destination_name": destination_links["destination_name"].iloc[0],
                "date": date.date().isoformat(),
                "weather_station_count_expected": expected_count,
                "weather_station_months_usable": usable_count,
                "complete_weather_proxy": complete,
                "temperature_coverage_share_mean": group[
                    "temperature_mean_coverage_share"
                ].mean(),
                "precipitation_coverage_share_mean": group[
                    "precipitation_coverage_share"
                ].mean(),
                "destination_weather_proxy_quality": worst_quality,
                "weather_source_id": "METEOSWISS_SMN_DAILY_SELECTED",
                "weather_direct_slope_representation": False,
                "weather_causal_covariate_approved": False,
                "precipitation_observation_window": "06:00_UTC_to_06:00_UTC_next_day",
            }
            for column in metric_columns:
                output_name = (
                    "precipitation_total_mm_mean_across_stations"
                    if column == "precipitation_total_mm"
                    else column
                )
                row[output_name] = group[column].mean() if complete else np.nan
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["destination_unit_id", "date"])


def main() -> None:
    daily, raw_rows_all_dates, station_codes = load_selected_daily()
    station_month = aggregate_station_months(daily, station_codes)
    crosswalk, eligible_stations = build_crosswalk(station_codes)

    station_details = eligible_stations[
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
    station_month = station_month.merge(
        station_details, on="station_abbr", how="left", validate="many_to_one"
    )
    station_month = station_month.sort_values(["station_abbr", "month_date"])
    station_month["month_date"] = station_month["month_date"].dt.date.astype(str)
    station_month.to_csv(STATION_MONTH_OUT, index=False, na_rep="NA")
    crosswalk.to_csv(CROSSWALK_OUT, index=False, na_rep="NA")

    destination_month = build_destination_month(
        station_month.assign(month_date=pd.to_datetime(station_month["month_date"])),
        crosswalk,
    )
    destination_month.to_csv(DESTINATION_MONTH_OUT, index=False, na_rep="NA")

    quality_counts = crosswalk["weather_proxy_quality"].value_counts().to_dict()
    summary = {
        "selected_raw_daily_rows_all_dates": raw_rows_all_dates,
        "analysis_daily_rows": int(len(daily)),
        "analysis_start": daily["date"].min().date().isoformat(),
        "analysis_end": daily["date"].max().date().isoformat(),
        "eligible_candidate_stations_with_core_parameters_since_2013": int(
            crosswalk["candidate_station_count"].iloc[0]
        ),
        "selected_station_count": len(station_codes),
        "selected_station_codes": station_codes,
        "invalid_negative_precipitation_values": int(
            daily["invalid_negative_precipitation"].sum()
        ),
        "temperature_ordering_violations": 0,
        "station_month_rows": int(len(station_month)),
        "station_month_usable_rows": int(station_month["month_weather_proxy_usable"].sum()),
        "station_month_incomplete_precipitation_rows": int(
            station_month["precipitation_coverage_share"].lt(MIN_MONTH_COVERAGE).sum()
        ),
        "reviewed_component_resort_crosswalk_rows": int(len(crosswalk)),
        "weather_proxy_quality_counts": quality_counts,
        "destination_units": int(destination_month["destination_unit_id"].nunique()),
        "destination_month_rows": int(len(destination_month)),
        "destination_month_complete_weather_proxy_rows": int(
            destination_month["complete_weather_proxy"].sum()
        ),
        "causal_covariates_approved": 0,
        "no_imputation": True,
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    assignment_rows = []
    for row in crosswalk.itertuples(index=False):
        assignment_rows.append(
            "| "
            + " | ".join(
                [
                    row.destination_name,
                    row.resort_name_canonical,
                    row.weather_station_code,
                    row.weather_station_name,
                    f"{row.weather_station_distance_km:.1f}",
                    f"{row.weather_station_elevation_m:.0f}",
                    f"{row.weather_station_elevation_gap_to_resort_top_m:.0f}",
                    row.weather_proxy_quality,
                ]
            )
            + " |"
        )
    report = f"""# MeteoSwiss regional weather proxy

Generated reproducibly by `src/data_processing/build_weather_proxy_panel.py`.

## Source decision

The project selected official MeteoSwiss SwissMetNet station files for the first temperature and precipitation control. SwissMetNet provides directly observed daily station values, official station coordinates/elevations, a parameter inventory and static historical/current-year CSV files. MeteoSwiss 1 km spatial climate analyses remain a future robustness option; ERA5-Land remains a coarser reanalysis fallback. The targeted seven-station download is materially smaller and fully traceable to the reviewed destination units.

The four daily parameters are:

- `tre200d0`: mean air temperature 2 m above ground, °C;
- `tre200dn`: minimum air temperature 2 m above ground, °C;
- `tre200dx`: maximum air temperature 2 m above ground, °C;
- `rre150d0`: precipitation total from 06:00 UTC to 06:00 UTC the following day, mm.

The precipitation window is therefore not identical to a civil calendar day. This timing difference is preserved in the output rather than silently relabelled.

## Collection and coverage

- Daily analysis rows: **{summary['analysis_daily_rows']:,}**, from {summary['analysis_start']} through {summary['analysis_end']}.
- Stations eligible from official inventory metadata: **{summary['eligible_candidate_stations_with_core_parameters_since_2013']}** with all four parameters starting by the analysis date and no recorded end date.
- Selected stations used by the reviewed destinations: **{summary['selected_station_count']}** ({', '.join(station_codes)}).
- Station-month rows: **{summary['station_month_rows']:,}**; **{summary['station_month_usable_rows']:,}** pass the 80% coverage gate for all four parameters.
- Two station-months fail the precipitation gate: EVO in 2016-07 and INT in 2013-08. They remain missing downstream; no imputation is used.

Calendar-month temperature and precipitation anomalies use station-specific 2013–2025 normals calculated only from usable months. These normals are analytical reference values, not MeteoSwiss climatological normals.

## Resort-to-station assignments

Each of the 15 resort listings in the 11 reviewed destination units is assigned to the geographically nearest current SwissMetNet station with all four daily parameters starting by 2013. Repeated stations within a destination are deduplicated before destination aggregation.

| Destination | Resort listing | Station | Station name | Distance km | Station elevation m | Gap to resort top m | Proxy quality |
|---|---|---|---|---:|---:|---:|---|
{chr(10).join(assignment_rows)}

Quality is based on horizontal distance for a regional anomaly proxy: high at ≤10 km, moderate at ≤20 km, and low beyond 20 km. The elevation gap remains visible and can be large because resort-top altitude is not the station's measurement target.

## Destination aggregation and limits

The destination output contains **{summary['destination_month_rows']:,} rows**, of which **{summary['destination_month_complete_weather_proxy_rows']:,}** have complete weather proxies. Temperature, precipitation and anomalies are unweighted means across unique assigned stations and are withheld unless every expected station-month passes the coverage gate.

These observations describe regional weather near the reviewed resort listings. They do not measure piste microclimate, snowfall phase, snowmaking, grooming, aspect, wind redistribution or conditions across the full tourism catchment. `weather_direct_slope_representation` and `weather_causal_covariate_approved` are false throughout. Adding weather reduces one time-varying confounding gap but does not resolve treatment continuity, selection, spillovers or donor validity.
"""
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
