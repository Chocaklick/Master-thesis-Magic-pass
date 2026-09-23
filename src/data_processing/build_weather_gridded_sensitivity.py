"""Compare station weather proxies with official 1 km monthly climate grids.

TabsM and RhiresM are direct monthly spatial analyses from MeteoSwiss. This
module extracts the nearest valid LV95 grid cell for each reviewed resort
component, constructs like-for-like 2013-2025 calendar-month anomalies and
compares them with the existing SwissMetNet station proxy. The grids remain
station-informed analyses, not an independent measurement network or piste
microclimate observations.
"""

from __future__ import annotations

import json
from pathlib import Path

import netCDF4
import numpy as np
import pandas as pd
from pyproj import Transformer

from build_weather_proxy_panel import checked_path, exact_metadata
from build_weather_station_sensitivity import agreement_grade, correlation


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
SOURCE_CONFIG = ROOT / "config" / "meteoswiss_gridded_weather_files.json"
PRIMARY_CROSSWALK = ROOT / "data_processed" / "resort_weather_station_crosswalk.csv"
PRIMARY_STATION_MONTH = ROOT / "data_processed" / "meteoswiss_station_month.csv"
PRIMARY_DESTINATION_MONTH = ROOT / "data_processed" / "destination_weather_month.csv"

COMPONENT_MONTH_OUT = ROOT / "data_processed" / "meteoswiss_gridded_component_month.csv"
COMPONENT_COMPARISON_OUT = ROOT / "reports" / "weather_gridded_component_comparison.csv"
DESTINATION_MONTH_OUT = ROOT / "data_processed" / "destination_weather_gridded_sensitivity.csv"
DESTINATION_SUMMARY_OUT = ROOT / "reports" / "weather_gridded_destination_summary.csv"
SUMMARY_OUT = ROOT / "reports" / "weather_gridded_sensitivity_summary.json"
REPORT_OUT = ROOT / "reports" / "35_WEATHER_GRIDDED_SENSITIVITY.md"

ANALYSIS_START = pd.Timestamp("2013-01-01")
ANALYSIS_END = pd.Timestamp("2026-03-01")
NORMAL_END = pd.Timestamp("2025-12-01")
GRID_SOURCE_ID = "METEOSWISS_TABSM_RHIRESM_MONTHLY_GRID_2013_202603"
INTERPRETATION = (
    "swissmetnet_station_vs_meteoswiss_tabsm_rhiresm_1km_gridded_monthly_"
    "sensitivity_not_independent_measurement_network_piste_microclimate_or_"
    "causal_approval"
)


def configured_sources() -> dict[str, dict[str, object]]:
    sources = json.loads(SOURCE_CONFIG.read_text(encoding="utf-8"))
    by_id = {str(source["source_id"]): source for source in sources}
    if len(sources) != len(by_id):
        raise ValueError("Duplicate source IDs in gridded-weather configuration")
    return by_id


def grid_source_id(product: str, period: str) -> str:
    return f"METEOSWISS_GRID_{product}_{period}"


def periods() -> list[str]:
    return [str(year) for year in range(2013, 2026)] + ["202601", "202602", "202603"]


def checked_grid_path(
    sources: dict[str, dict[str, object]], product: str, period: str
) -> Path:
    source_id = grid_source_id(product, period)
    source = sources.get(source_id)
    if source is None:
        raise ValueError(f"Missing configured gridded source {source_id}")
    path = checked_path(source_id)
    metadata = exact_metadata(source_id)
    expected = source.get("expected_sha256")
    if expected is None or metadata["sha256"] != expected:
        raise RuntimeError(f"Official STAC checksum mismatch for {source_id}")
    return path


def validate_dataset(
    dataset: netCDF4.Dataset,
    variable_name: str,
    expected_period: str,
) -> tuple[np.ndarray, np.ndarray]:
    expected_title = f"Spatial Climate Analyses Dataset of MeteoSwiss ({variable_name})"
    if dataset.title != expected_title or dataset.Conventions != "CF-1.8":
        raise ValueError(f"Unexpected {variable_name} NetCDF metadata")
    if set(["time", "N", "E", variable_name, "lon", "lat"]) - set(dataset.variables):
        raise ValueError(f"Incomplete {variable_name} NetCDF schema")
    variable = dataset.variables[variable_name]
    if variable.dimensions != ("time", "N", "E"):
        raise ValueError(f"Unexpected {variable_name} dimension order")
    expected_units = "degree" if variable_name == "TabsM" else "millimeter"
    if variable.units != expected_units or variable.grid_name != "ch01r.swiss.lv95":
        raise ValueError(f"Unexpected {variable_name} units or grid")
    easting = np.asarray(dataset.variables["E"][:], dtype=float)
    northing = np.asarray(dataset.variables["N"][:], dtype=float)
    if (
        len(easting) != 370
        or len(northing) != 240
        or not np.allclose(np.diff(easting), 1000.0)
        or not np.allclose(np.diff(northing), 1000.0)
    ):
        raise ValueError("Expected regular 1 km LV95 grid")
    expected_months = 12 if len(expected_period) == 4 else 1
    if len(dataset.dimensions["time"]) != expected_months:
        raise ValueError(f"Unexpected time dimension for {expected_period}")
    units = str(dataset.variables["time"].units)
    expected_start = (
        f"{expected_period}-01-01" if len(expected_period) == 4 else
        f"{expected_period[:4]}-{expected_period[4:]}-01"
    )
    if units != f"months since {expected_start} 00:00:00":
        raise ValueError(f"Unexpected time units for {expected_period}: {units}")
    if not np.array_equal(
        np.asarray(dataset.variables["time"][:], dtype=float),
        np.arange(expected_months, dtype=float),
    ):
        raise ValueError(f"Unexpected time coordinate for {expected_period}")
    return easting, northing


def open_pair(
    sources: dict[str, dict[str, object]], period: str
) -> tuple[netCDF4.Dataset, netCDF4.Dataset]:
    # The netCDF C library cannot reliably open the repository's Unicode Windows
    # path. Reading the small monthly files in memory preserves native-path
    # portability without making an untracked ASCII-path copy.
    tabs_path = checked_grid_path(sources, "TABSM", period)
    rain_path = checked_grid_path(sources, "RHIRESM", period)
    tabs = netCDF4.Dataset("tabs_inmemory.nc", memory=tabs_path.read_bytes())
    rain = netCDF4.Dataset("rain_inmemory.nc", memory=rain_path.read_bytes())
    try:
        tabs_e, tabs_n = validate_dataset(tabs, "TabsM", period)
        rain_e, rain_n = validate_dataset(rain, "RhiresM", period)
        if not np.array_equal(tabs_e, rain_e) or not np.array_equal(tabs_n, rain_n):
            raise ValueError(f"TabsM/RhiresM grid mismatch for {period}")
        if not np.allclose(tabs.variables["lon"][:], rain.variables["lon"][:]):
            raise ValueError(f"TabsM/RhiresM longitude grid mismatch for {period}")
        if not np.allclose(tabs.variables["lat"][:], rain.variables["lat"][:]):
            raise ValueError(f"TabsM/RhiresM latitude grid mismatch for {period}")
    except Exception:
        tabs.close()
        rain.close()
        raise
    return tabs, rain


def first_common_valid_grid(
    sources: dict[str, dict[str, object]],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    tabs, rain = open_pair(sources, "2013")
    try:
        easting = np.asarray(tabs.variables["E"][:], dtype=float)
        northing = np.asarray(tabs.variables["N"][:], dtype=float)
        lon = np.asarray(tabs.variables["lon"][:], dtype=float)
        lat = np.asarray(tabs.variables["lat"][:], dtype=float)
        tabs_values = np.ma.asarray(tabs.variables["TabsM"][:])
        rain_values = np.ma.asarray(rain.variables["RhiresM"][:])
        common_valid = (
            ~np.ma.getmaskarray(tabs_values).any(axis=0)
            & ~np.ma.getmaskarray(rain_values).any(axis=0)
        )
    finally:
        tabs.close()
        rain.close()
    return easting, northing, lon, lat, common_valid


def build_component_cells(
    sources: dict[str, dict[str, object]],
) -> pd.DataFrame:
    links = pd.read_csv(PRIMARY_CROSSWALK)
    if len(links) != 15 or links["resort_id"].duplicated().any():
        raise ValueError("Expected exactly 15 unique reviewed weather components")
    easting, northing, lon_grid, lat_grid, valid = first_common_valid_grid(sources)
    e_grid, n_grid = np.meshgrid(easting, northing)
    valid_rows, valid_cols = np.where(valid)
    valid_e = e_grid[valid]
    valid_n = n_grid[valid]
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    point_e, point_n = transformer.transform(
        links["longitude"].to_numpy(float), links["latitude"].to_numpy(float)
    )
    rows: list[dict[str, object]] = []
    for position, link in enumerate(links.itertuples(index=False)):
        squared = (valid_e - point_e[position]) ** 2 + (valid_n - point_n[position]) ** 2
        nearest = int(np.argmin(squared))
        row_index = int(valid_rows[nearest])
        column_index = int(valid_cols[nearest])
        row = link._asdict()
        row.update(
            {
                "resort_point_e_lv95_m": float(point_e[position]),
                "resort_point_n_lv95_m": float(point_n[position]),
                "grid_row_index": row_index,
                "grid_column_index": column_index,
                "grid_cell_e_lv95_m": float(easting[column_index]),
                "grid_cell_n_lv95_m": float(northing[row_index]),
                "grid_cell_longitude": float(lon_grid[row_index, column_index]),
                "grid_cell_latitude": float(lat_grid[row_index, column_index]),
                "grid_cell_distance_to_component_m": float(np.sqrt(squared[nearest])),
                "grid_cell_id": (
                    f"LV95_E{int(easting[column_index])}_N{int(northing[row_index])}"
                ),
                "gridded_weather_source_id": GRID_SOURCE_ID,
                "grid_cell_selection_method": (
                    "nearest_common_valid_1km_lv95_tabsm_rhiresm_cell"
                ),
                "gridded_weather_sensitivity_interpretation": INTERPRETATION,
                "gridded_weather_causal_covariate_approved": False,
            }
        )
        rows.append(row)
    result = pd.DataFrame(rows)
    if result["grid_cell_distance_to_component_m"].max() > np.sqrt(2) * 1000:
        raise ValueError("Reviewed component unexpectedly far from a valid climate-grid cell")
    return result.sort_values(["destination_unit_id", "resort_id"])


def period_dates(period: str) -> list[pd.Timestamp]:
    if len(period) == 4:
        return list(pd.date_range(f"{period}-01-01", periods=12, freq="MS"))
    return [pd.Timestamp(f"{period[:4]}-{period[4:]}-01")]


def extract_component_months(
    sources: dict[str, dict[str, object]], cells: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    reference_e: np.ndarray | None = None
    reference_n: np.ndarray | None = None
    for period in periods():
        tabs, rain = open_pair(sources, period)
        try:
            easting = np.asarray(tabs.variables["E"][:], dtype=float)
            northing = np.asarray(tabs.variables["N"][:], dtype=float)
            if reference_e is None:
                reference_e, reference_n = easting, northing
            elif not np.array_equal(reference_e, easting) or not np.array_equal(
                reference_n, northing
            ):
                raise ValueError(f"Grid coordinates changed in {period}")
            tabs_values = np.ma.asarray(tabs.variables["TabsM"][:])
            rain_values = np.ma.asarray(rain.variables["RhiresM"][:])
            for month_index, date in enumerate(period_dates(period)):
                for cell in cells.itertuples(index=False):
                    temperature = tabs_values[
                        month_index, cell.grid_row_index, cell.grid_column_index
                    ]
                    precipitation = rain_values[
                        month_index, cell.grid_row_index, cell.grid_column_index
                    ]
                    rows.append(
                        {
                            "destination_unit_id": cell.destination_unit_id,
                            "destination_name": cell.destination_name,
                            "resort_id": cell.resort_id,
                            "resort_name_canonical": cell.resort_name_canonical,
                            "date": date,
                            "calendar_month": date.month,
                            "grid_cell_id": cell.grid_cell_id,
                            "grid_row_index": cell.grid_row_index,
                            "grid_column_index": cell.grid_column_index,
                            "grid_cell_e_lv95_m": cell.grid_cell_e_lv95_m,
                            "grid_cell_n_lv95_m": cell.grid_cell_n_lv95_m,
                            "grid_cell_longitude": cell.grid_cell_longitude,
                            "grid_cell_latitude": cell.grid_cell_latitude,
                            "grid_cell_distance_to_component_m": (
                                cell.grid_cell_distance_to_component_m
                            ),
                            "air_temperature_mean_c_grid": (
                                np.nan if np.ma.is_masked(temperature) else float(temperature)
                            ),
                            "precipitation_total_mm_grid": (
                                np.nan if np.ma.is_masked(precipitation) else float(precipitation)
                            ),
                        }
                    )
        finally:
            tabs.close()
            rain.close()
    frame = pd.DataFrame(rows)
    if len(frame) != 15 * 159 or frame.duplicated(["resort_id", "date"]).any():
        raise ValueError("Gridded component-month output lost its expected grain")
    normal_sample = frame[frame["date"].between(ANALYSIS_START, NORMAL_END)]
    normals = normal_sample.groupby(
        ["resort_id", "calendar_month"], as_index=False, observed=True
    ).agg(
        air_temperature_2013_2025_normal_c_grid=("air_temperature_mean_c_grid", "mean"),
        precipitation_2013_2025_normal_mm_grid=("precipitation_total_mm_grid", "mean"),
        grid_normal_years_temperature=("air_temperature_mean_c_grid", "count"),
        grid_normal_years_precipitation=("precipitation_total_mm_grid", "count"),
    )
    frame = frame.merge(
        normals,
        on=["resort_id", "calendar_month"],
        how="left",
        validate="many_to_one",
    )
    frame["air_temperature_anomaly_c_grid"] = (
        frame["air_temperature_mean_c_grid"]
        - frame["air_temperature_2013_2025_normal_c_grid"]
    )
    frame["precipitation_anomaly_mm_grid"] = (
        frame["precipitation_total_mm_grid"]
        - frame["precipitation_2013_2025_normal_mm_grid"]
    )
    frame["precipitation_ratio_to_2013_2025_normal_grid"] = (
        frame["precipitation_total_mm_grid"]
        / frame["precipitation_2013_2025_normal_mm_grid"]
    )
    frame["gridded_weather_month_complete"] = frame[
        ["air_temperature_mean_c_grid", "precipitation_total_mm_grid"]
    ].notna().all(axis=1)
    frame["gridded_weather_source_id"] = GRID_SOURCE_ID
    frame["gridded_weather_sensitivity_interpretation"] = INTERPRETATION
    frame["gridded_weather_causal_covariate_approved"] = False
    return frame.sort_values(["destination_unit_id", "resort_id", "date"])


def component_comparison(cells: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    primary = pd.read_csv(PRIMARY_STATION_MONTH)
    primary["month_date"] = pd.to_datetime(primary["month_date"], errors="raise")
    rows: list[dict[str, object]] = []
    for cell in cells.itertuples(index=False):
        station = primary[
            primary["station_abbr"].eq(cell.weather_station_code)
        ].copy()
        component_grid = grid[grid["resort_id"].eq(cell.resort_id)].copy()
        paired = station.merge(
            component_grid,
            left_on="month_date",
            right_on="date",
            how="inner",
            validate="one_to_one",
        )
        common = paired[
            paired["month_weather_proxy_usable"].astype(bool)
            & paired["gridded_weather_month_complete"].astype(bool)
        ]
        winter = common[common["date"].dt.month.isin([11, 12, 1, 2, 3, 4])]
        temperature_correlation = correlation(
            common["air_temperature_anomaly_c"],
            common["air_temperature_anomaly_c_grid"],
        )
        precipitation_correlation = correlation(
            common["precipitation_anomaly_mm"],
            common["precipitation_anomaly_mm_grid"],
        )
        rows.append(
            {
                "destination_unit_id": cell.destination_unit_id,
                "destination_name": cell.destination_name,
                "resort_id": cell.resort_id,
                "resort_name_canonical": cell.resort_name_canonical,
                "component_latitude": cell.latitude,
                "component_longitude": cell.longitude,
                "primary_weather_station_code": cell.weather_station_code,
                "primary_weather_station_name": cell.weather_station_name,
                "primary_weather_station_distance_km": cell.weather_station_distance_km,
                "grid_cell_id": cell.grid_cell_id,
                "grid_cell_e_lv95_m": cell.grid_cell_e_lv95_m,
                "grid_cell_n_lv95_m": cell.grid_cell_n_lv95_m,
                "grid_cell_latitude": cell.grid_cell_latitude,
                "grid_cell_longitude": cell.grid_cell_longitude,
                "grid_cell_distance_to_component_m": (
                    cell.grid_cell_distance_to_component_m
                ),
                "common_complete_months": len(common),
                "common_complete_winter_months": len(winter),
                "temperature_anomaly_correlation_station_grid": temperature_correlation,
                "winter_temperature_anomaly_correlation_station_grid": correlation(
                    winter["air_temperature_anomaly_c"],
                    winter["air_temperature_anomaly_c_grid"],
                ),
                "temperature_anomaly_mean_absolute_difference_c_station_grid": float(
                    (
                        common["air_temperature_anomaly_c_grid"]
                        - common["air_temperature_anomaly_c"]
                    ).abs().mean()
                ),
                "precipitation_anomaly_correlation_station_grid": precipitation_correlation,
                "winter_precipitation_anomaly_correlation_station_grid": correlation(
                    winter["precipitation_anomaly_mm"],
                    winter["precipitation_anomaly_mm_grid"],
                ),
                "precipitation_anomaly_mean_absolute_difference_mm_station_grid": float(
                    (
                        common["precipitation_anomaly_mm_grid"]
                        - common["precipitation_anomaly_mm"]
                    ).abs().mean()
                ),
                "gridded_weather_sensitivity_agreement": agreement_grade(
                    temperature_correlation, precipitation_correlation
                ),
                "gridded_weather_sensitivity_interpretation": INTERPRETATION,
                "gridded_weather_causal_covariate_approved": False,
            }
        )
    return pd.DataFrame(rows).sort_values(["destination_unit_id", "resort_id"])


def destination_grid_month(
    cells: pd.DataFrame, component_month: pd.DataFrame
) -> pd.DataFrame:
    expected = (
        cells[["destination_unit_id", "grid_cell_id"]]
        .drop_duplicates()
        .groupby("destination_unit_id", observed=True)["grid_cell_id"]
        .nunique()
    )
    unique_cells = component_month.drop_duplicates(
        ["destination_unit_id", "grid_cell_id", "date"]
    )
    grouped = unique_cells.groupby(
        ["destination_unit_id", "destination_name", "date"],
        observed=True,
    )
    destination = grouped.agg(
        grid_cells_observed=("grid_cell_id", "nunique"),
        grid_cells_complete=("gridded_weather_month_complete", "sum"),
        air_temperature_mean_c_grid=("air_temperature_mean_c_grid", "mean"),
        air_temperature_anomaly_c_grid=("air_temperature_anomaly_c_grid", "mean"),
        precipitation_total_mm_grid=("precipitation_total_mm_grid", "mean"),
        precipitation_anomaly_mm_grid=("precipitation_anomaly_mm_grid", "mean"),
    ).reset_index()
    destination["grid_cells_expected"] = destination["destination_unit_id"].map(expected)
    destination["complete_gridded_weather_proxy"] = (
        destination["grid_cells_observed"].eq(destination["grid_cells_expected"])
        & destination["grid_cells_complete"].eq(destination["grid_cells_expected"])
    )
    value_columns = [
        "air_temperature_mean_c_grid",
        "air_temperature_anomaly_c_grid",
        "precipitation_total_mm_grid",
        "precipitation_anomaly_mm_grid",
    ]
    destination[value_columns] = destination[value_columns].where(
        destination["complete_gridded_weather_proxy"], np.nan
    )
    destination["gridded_weather_source_id"] = GRID_SOURCE_ID
    destination["gridded_weather_sensitivity_interpretation"] = INTERPRETATION
    destination["gridded_weather_causal_covariate_approved"] = False
    if len(destination) != 11 * 159:
        raise ValueError("Destination gridded proxy lost the 11-unit monthly grain")
    return destination.sort_values(["destination_unit_id", "date"])


def compare_destinations(
    destination_grid: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    primary = pd.read_csv(PRIMARY_DESTINATION_MONTH)
    primary["date"] = pd.to_datetime(primary["date"], errors="raise")
    keep = [
        "destination_unit_id",
        "destination_name",
        "date",
        "complete_weather_proxy",
        "air_temperature_anomaly_c",
        "precipitation_anomaly_mm",
    ]
    comparison = primary[keep].merge(
        destination_grid,
        on=["destination_unit_id", "destination_name", "date"],
        how="outer",
        validate="one_to_one",
    )
    if len(comparison) != 11 * 159:
        raise ValueError("Station-grid destination comparison lost expected grain")
    comparison["both_station_and_grid_weather_complete"] = (
        comparison["complete_weather_proxy"].fillna(False).astype(bool)
        & comparison["complete_gridded_weather_proxy"].fillna(False).astype(bool)
    )
    comparison["temperature_anomaly_difference_grid_minus_station_c"] = (
        comparison["air_temperature_anomaly_c_grid"]
        - comparison["air_temperature_anomaly_c"]
    ).where(comparison["both_station_and_grid_weather_complete"])
    comparison["precipitation_anomaly_difference_grid_minus_station_mm"] = (
        comparison["precipitation_anomaly_mm_grid"]
        - comparison["precipitation_anomaly_mm"]
    ).where(comparison["both_station_and_grid_weather_complete"])
    summary_rows: list[dict[str, object]] = []
    for destination_id, group in comparison.groupby("destination_unit_id", observed=True):
        common = group[group["both_station_and_grid_weather_complete"]]
        temperature_correlation = correlation(
            common["air_temperature_anomaly_c"],
            common["air_temperature_anomaly_c_grid"],
        )
        precipitation_correlation = correlation(
            common["precipitation_anomaly_mm"],
            common["precipitation_anomaly_mm_grid"],
        )
        summary_rows.append(
            {
                "destination_unit_id": destination_id,
                "destination_name": group["destination_name"].iloc[0],
                "common_complete_months": len(common),
                "temperature_anomaly_correlation_station_grid": temperature_correlation,
                "temperature_anomaly_mean_absolute_difference_c_station_grid": float(
                    common["temperature_anomaly_difference_grid_minus_station_c"]
                    .abs()
                    .mean()
                ),
                "precipitation_anomaly_correlation_station_grid": precipitation_correlation,
                "precipitation_anomaly_mean_absolute_difference_mm_station_grid": float(
                    common["precipitation_anomaly_difference_grid_minus_station_mm"]
                    .abs()
                    .mean()
                ),
                "gridded_weather_sensitivity_agreement": agreement_grade(
                    temperature_correlation, precipitation_correlation
                ),
                "gridded_weather_causal_covariate_approved": False,
            }
        )
    return comparison, pd.DataFrame(summary_rows).sort_values("destination_unit_id")


def main() -> None:
    analysis = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    sources = configured_sources()
    required_grid_sources = {
        grid_source_id(product, period)
        for product in ["TABSM", "RHIRESM"]
        for period in periods()
    }
    if len(required_grid_sources) != 32 or not required_grid_sources.issubset(sources):
        raise ValueError("Expected exactly 32 configured grid assets")

    cells = build_component_cells(sources)
    component_month = extract_component_months(sources, cells)
    component = component_comparison(cells, component_month)
    destination_grid = destination_grid_month(cells, component_month)
    destination_comparison, destination_summary = compare_destinations(destination_grid)

    component_output = component_month.copy()
    component_output["date"] = component_output["date"].dt.date.astype(str)
    destination_output = destination_comparison.copy()
    destination_output["date"] = destination_output["date"].dt.date.astype(str)
    component_output.to_csv(COMPONENT_MONTH_OUT, index=False, na_rep="NA")
    component.to_csv(COMPONENT_COMPARISON_OUT, index=False, na_rep="NA")
    destination_output.to_csv(DESTINATION_MONTH_OUT, index=False, na_rep="NA")
    destination_summary.to_csv(DESTINATION_SUMMARY_OUT, index=False, na_rep="NA")

    summary = {
        "analysis_version": analysis["analysis_version"],
        "source_grid": "MeteoSwiss ch01r.swiss.lv95 1 km",
        "source_products": ["TabsM v1.4", "RhiresM v2.0"],
        "configured_grid_assets": len(required_grid_sources),
        "analysis_months": 159,
        "reviewed_components": len(cells),
        "unique_grid_cells": int(cells["grid_cell_id"].nunique()),
        "maximum_grid_cell_distance_to_component_m": float(
            cells["grid_cell_distance_to_component_m"].max()
        ),
        "component_month_rows": len(component_month),
        "component_months_complete": int(
            component_month["gridded_weather_month_complete"].sum()
        ),
        "component_agreement_counts": {
            str(key): int(value)
            for key, value in component["gridded_weather_sensitivity_agreement"]
            .value_counts()
            .items()
        },
        "median_component_temperature_anomaly_correlation": float(
            component["temperature_anomaly_correlation_station_grid"].median()
        ),
        "median_component_temperature_anomaly_mean_absolute_difference_c": float(
            component[
                "temperature_anomaly_mean_absolute_difference_c_station_grid"
            ].median()
        ),
        "median_component_precipitation_anomaly_correlation": float(
            component["precipitation_anomaly_correlation_station_grid"].median()
        ),
        "median_component_precipitation_anomaly_mean_absolute_difference_mm": float(
            component[
                "precipitation_anomaly_mean_absolute_difference_mm_station_grid"
            ].median()
        ),
        "destination_units": int(destination_summary["destination_unit_id"].nunique()),
        "destination_month_rows": len(destination_comparison),
        "destination_months_both_station_and_grid_complete": int(
            destination_comparison["both_station_and_grid_weather_complete"].sum()
        ),
        "destination_agreement_counts": {
            str(key): int(value)
            for key, value in destination_summary[
                "gridded_weather_sensitivity_agreement"
            ].value_counts().items()
        },
        "median_destination_temperature_anomaly_correlation": float(
            destination_summary[
                "temperature_anomaly_correlation_station_grid"
            ].median()
        ),
        "median_destination_precipitation_anomaly_correlation": float(
            destination_summary[
                "precipitation_anomaly_correlation_station_grid"
            ].median()
        ),
        "gridded_weather_causal_covariates_approved": 0,
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# MeteoSwiss monthly gridded-weather sensitivity

## Design

This check compares the selected SwissMetNet station proxy with the official MeteoSwiss **TabsM v1.4** monthly mean-temperature and **RhiresM v2.0** monthly precipitation spatial analyses. The archive supplies one annual NetCDF per product for 2013–2025; three current monthly files extend both products through March 2026. All **{len(required_grid_sources)} assets** are cached and matched to their official STAC SHA-256 multihashes.

For each of the **{len(cells)} reviewed resort components**, the extraction uses the nearest cell that is valid for both products on the regular `ch01r.swiss.lv95` grid. Grid spacing is 1 km; the largest point-to-cell-centre distance is **{summary['maximum_grid_cell_distance_to_component_m']:.0f} m**. Anomalies use a component-cell and calendar-month 2013–2025 mean, matching the station proxy's analytical reference years. Destination values are unweighted means across unique component grid cells and are complete only when every expected cell is observed.

## Component results

- component-month rows: **{len(component_month):,}**; complete temperature and precipitation rows: **{summary['component_months_complete']:,}**
- component agreement counts: **{summary['component_agreement_counts']}**
- median temperature-anomaly correlation: **{summary['median_component_temperature_anomaly_correlation']:.3f}**
- median temperature-anomaly mean absolute difference: **{summary['median_component_temperature_anomaly_mean_absolute_difference_c']:.2f} °C**
- median precipitation-anomaly correlation: **{summary['median_component_precipitation_anomaly_correlation']:.3f}**
- median precipitation-anomaly mean absolute difference: **{summary['median_component_precipitation_anomaly_mean_absolute_difference_mm']:.1f} mm/month**

The predeclared review categories are unchanged from the station sensitivity: high requires temperature/precipitation anomaly correlations of at least 0.90/0.70, moderate at least 0.80/0.50, and otherwise low. They are descriptive review bands, not causal gates.

## Destination results

The comparison contains **{len(destination_comparison):,} destination-months** for **{summary['destination_units']} units**. Both station and grid proxies are complete in **{summary['destination_months_both_station_and_grid_complete']:,} rows**. Destination agreement counts are **{summary['destination_agreement_counts']}**; median temperature- and precipitation-anomaly correlations are **{summary['median_destination_temperature_anomaly_correlation']:.3f}** and **{summary['median_destination_precipitation_anomaly_correlation']:.3f}**.

## Interpretation limit

TabsM is based on homogenised monthly climate-station series and RhiresM on monthly rain-gauge totals. The gridding and monthly analysis method differ from the direct daily SwissMetNet extraction, but these are not independent measurement networks. A 1 km cell spacing does not imply 1 km effective precipitation resolution; official documentation warns of larger Alpine/high-elevation uncertainty and winter precipitation undercatch. Neither product measures piste microclimate, snow phase, wind redistribution, grooming or snowmaking. Every gridded-weather causal-approval flag therefore remains false.

## Outputs

- `data_processed/meteoswiss_gridded_component_month.csv`
- `reports/weather_gridded_component_comparison.csv`
- `data_processed/destination_weather_gridded_sensitivity.csv`
- `reports/weather_gridded_destination_summary.csv`
"""
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
