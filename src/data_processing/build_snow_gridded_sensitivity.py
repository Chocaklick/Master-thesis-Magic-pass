"""Compare selected SLF station snow proxies with the SPASS 1 km snow grid."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "spass_snow_grid.json"
COMPONENT_WINTER_OUTPUT = ROOT / "data_processed" / "spass_snow_component_winter.csv"
COMPONENT_COMPARISON_OUTPUT = ROOT / "reports" / "snow_gridded_component_comparison.csv"
DESTINATION_WINTER_OUTPUT = ROOT / "data_processed" / "destination_snow_gridded_sensitivity.csv"
DESTINATION_SUMMARY_OUTPUT = ROOT / "reports" / "snow_gridded_destination_summary.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "snow_gridded_sensitivity_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "36_SNOW_GRIDDED_SENSITIVITY.md"
IO_CHUNK = 1024 * 1024
SOURCE_ID = "SLF_SPASS_HSCLQMD_GRID_1962_2023"
DERIVED_SOURCE_ID = "DERIVED_SNOW_GRIDDED_SENSITIVITY"
INTERPRETATION = (
    "slf_imis_station_vs_spass_oshd_clqm_1km_modelled_snow_sensitivity_"
    "shared_slf_assimilation_target_not_independent_measurement_network_"
    "piste_observation_or_causal_approval"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().eq("true")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(IO_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def source_metadata(config: dict) -> tuple[dict, Path]:
    matches = []
    for path in sorted(
        (ROOT / "data_external" / "source_evidence").glob(
            f"{config['source_id']}_*.metadata.json"
        )
    ):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == config["source_id"]:
            matches.append(record)
    if len(matches) != 1:
        raise RuntimeError(f"Expected one SPASS metadata record, found {len(matches)}")
    record = matches[0]
    if record["sha256"] != config["archive_sha256"]:
        raise RuntimeError("SPASS archive hash metadata differs from pinned configuration")
    if record["extracted_sha256"] != config["member_sha256"]:
        raise RuntimeError("SPASS NetCDF hash metadata differs from pinned configuration")
    path = ROOT / record["extracted_file"]
    if path.stat().st_size != int(config["member_uncompressed_size_bytes"]):
        raise RuntimeError("SPASS NetCDF size differs from configuration")
    actual_hash = sha256_file(path)
    if actual_hash != config["member_sha256"]:
        raise RuntimeError("SPASS NetCDF content differs from pinned SHA-256")
    return record, path


@contextmanager
def ascii_netcdf_path(source: Path):
    """Expose the large NetCDF through an ASCII hard link for netCDF-C on Windows."""

    link = Path(tempfile.gettempdir()) / f"spass_snow_{os.getpid()}.nc"
    link.unlink(missing_ok=True)
    os.link(source, link)
    try:
        yield link
    finally:
        link.unlink(missing_ok=True)


def reviewed_components() -> tuple[pd.DataFrame, dict[str, list[str]], dict[str, str]]:
    review = json.loads(
        (ROOT / "config" / "treatment_destination_review.json").read_text(
            encoding="utf-8"
        )
    )
    unit_by_resort: dict[str, list[str]] = {}
    destination_names: dict[str, str] = {}
    for unit in review["units"]:
        if not unit["eligible_for_reviewed_outcome_panel"]:
            continue
        destination_names[unit["destination_unit_id"]] = unit["destination_name"]
        for resort_id in unit["component_resort_ids"]:
            unit_by_resort.setdefault(resort_id, []).append(unit["destination_unit_id"])
    crosswalk = pd.read_csv(
        ROOT / "data_processed" / "resort_snow_station_crosswalk.csv"
    )
    components = crosswalk[crosswalk["resort_id"].isin(unit_by_resort)].copy()
    if len(components) != 15 or set(components["resort_id"]) != set(unit_by_resort):
        raise RuntimeError("Reviewed snow components do not reproduce the expected 15 rows")
    components["destination_unit_ids"] = components["resort_id"].map(
        lambda value: "|".join(sorted(unit_by_resort[value]))
    )
    return components.sort_values("resort_id"), unit_by_resort, destination_names


def cell_index_table(
    components: pd.DataFrame,
    east: np.ndarray,
    north: np.ndarray,
    target_kind: str,
) -> pd.DataFrame:
    if target_kind == "resort_component":
        longitude_column, latitude_column = "longitude", "latitude"
    elif target_kind == "selected_station":
        longitude_column, latitude_column = "snow_station_longitude", "snow_station_latitude"
    else:
        raise ValueError(f"Unknown grid target kind: {target_kind}")
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    x, y = transformer.transform(
        components[longitude_column].to_numpy(float),
        components[latitude_column].to_numpy(float),
    )
    rows = []
    for resort, point_e, point_n in zip(
        components.itertuples(index=False), x, y, strict=True
    ):
        e_index = int(np.abs(east - point_e).argmin())
        n_index = int(np.abs(north - point_n).argmin())
        e_start, e_end = max(0, e_index - 1), min(len(east), e_index + 2)
        n_start, n_end = max(0, n_index - 1), min(len(north), n_index + 2)
        rows.append(
            {
                "destination_unit_ids": resort.destination_unit_ids,
                "resort_id": resort.resort_id,
                "resort_name_canonical": resort.resort_name_canonical,
                "grid_target_kind": target_kind,
                "grid_target_latitude": float(getattr(resort, latitude_column)),
                "grid_target_longitude": float(getattr(resort, longitude_column)),
                "altitude_top_m": float(resort.altitude_top_m),
                "selected_station_code": resort.snow_station_code,
                "selected_station_label": resort.snow_station_label,
                "selected_station_distance_km": float(resort.snow_station_distance_km),
                "selected_station_elevation_m": float(resort.snow_station_elevation_m),
                "grid_e_index": e_index,
                "grid_n_index": n_index,
                "grid_easting_m": float(east[e_index]),
                "grid_northing_m": float(north[n_index]),
                "grid_cell_distance_m": float(
                    np.hypot(east[e_index] - point_e, north[n_index] - point_n)
                ),
                "grid_local_e_start": e_start,
                "grid_local_e_end_exclusive": e_end,
                "grid_local_n_start": n_start,
                "grid_local_n_end_exclusive": n_end,
                "grid_local_cell_count": int((e_end - e_start) * (n_end - n_start)),
            }
        )
    return pd.DataFrame(rows).sort_values("resort_id").reset_index(drop=True)


def extract_daily_grid(
    variable,
    dates: pd.DatetimeIndex,
    cells: pd.DataFrame,
    first_winter_start: int,
    last_winter_start: int,
) -> pd.DataFrame:
    mask = (
        dates.year.isin(range(first_winter_start, last_winter_start + 2))
        & dates.month.isin([11, 12, 1, 2, 3, 4])
    )
    wanted = np.flatnonzero(mask)
    groups: dict[tuple[int, int], list[int]] = {}
    for index in wanted:
        date = dates[index]
        winter_start = date.year if date.month >= 11 else date.year - 1
        if first_winter_start <= winter_start <= last_winter_start:
            groups.setdefault((date.year, date.month), []).append(int(index))

    rows: list[dict] = []
    for (year, month), indices in sorted(groups.items()):
        if indices != list(range(indices[0], indices[-1] + 1)):
            raise RuntimeError(f"Non-contiguous SPASS month {year}-{month:02d}")
        cube = np.asarray(variable[indices[0] : indices[-1] + 1, :, :], dtype=float)
        cube[~np.isfinite(cube)] = np.nan
        if np.nanmin(cube) < 0 or np.nanmax(cube) > 20:
            raise RuntimeError("SPASS values are outside plausible raw-metre snow depth bounds")
        month_dates = dates[indices]
        for cell in cells.itertuples(index=False):
            nearest = cube[:, cell.grid_n_index, cell.grid_e_index]
            local = cube[
                :,
                cell.grid_local_n_start : cell.grid_local_n_end_exclusive,
                cell.grid_local_e_start : cell.grid_local_e_end_exclusive,
            ]
            local_median = np.nanmedian(local, axis=(1, 2))
            for date, nearest_m, local_m in zip(
                month_dates, nearest, local_median, strict=True
            ):
                rows.append(
                    {
                        "resort_id": cell.resort_id,
                        "grid_target_kind": cell.grid_target_kind,
                        "date": date,
                        "winter_start_year": int(
                            date.year if date.month >= 11 else date.year - 1
                        ),
                        "grid_nearest_snow_depth_cm": nearest_m * 100,
                        "grid_local_3x3_median_snow_depth_cm": local_m * 100,
                    }
                )
    return pd.DataFrame(rows)


def build_component_winter(
    daily: pd.DataFrame, cells: pd.DataFrame, station_winter: pd.DataFrame
) -> pd.DataFrame:
    grid = daily.groupby(["resort_id", "winter_start_year"], as_index=False).agg(
        grid_expected_days=("date", "size"),
        grid_nearest_valid_days=("grid_nearest_snow_depth_cm", "count"),
        grid_local_3x3_valid_days=("grid_local_3x3_median_snow_depth_cm", "count"),
        grid_nearest_mean_snow_depth_cm=("grid_nearest_snow_depth_cm", "mean"),
        grid_local_3x3_mean_snow_depth_cm=(
            "grid_local_3x3_median_snow_depth_cm",
            "mean",
        ),
        grid_nearest_days_ge_30cm=(
            "grid_nearest_snow_depth_cm",
            lambda values: int(values.ge(30).sum()),
        ),
        grid_local_3x3_days_ge_30cm=(
            "grid_local_3x3_median_snow_depth_cm",
            lambda values: int(values.ge(30).sum()),
        ),
        grid_at_station_nearest_valid_days=("grid_at_station_nearest_snow_depth_cm", "count"),
        grid_at_station_local_3x3_valid_days=(
            "grid_at_station_local_3x3_median_snow_depth_cm",
            "count",
        ),
        grid_at_station_nearest_mean_snow_depth_cm=(
            "grid_at_station_nearest_snow_depth_cm",
            "mean",
        ),
        grid_at_station_local_3x3_mean_snow_depth_cm=(
            "grid_at_station_local_3x3_median_snow_depth_cm",
            "mean",
        ),
        grid_at_station_nearest_days_ge_30cm=(
            "grid_at_station_nearest_snow_depth_cm",
            lambda values: int(values.ge(30).sum()),
        ),
        grid_at_station_local_3x3_days_ge_30cm=(
            "grid_at_station_local_3x3_median_snow_depth_cm",
            lambda values: int(values.ge(30).sum()),
        ),
    )
    grid["grid_nearest_share_days_ge_30cm"] = (
        grid["grid_nearest_days_ge_30cm"] / grid["grid_nearest_valid_days"]
    )
    grid["grid_local_3x3_share_days_ge_30cm"] = (
        grid["grid_local_3x3_days_ge_30cm"] / grid["grid_local_3x3_valid_days"]
    )
    grid["grid_at_station_nearest_share_days_ge_30cm"] = (
        grid["grid_at_station_nearest_days_ge_30cm"]
        / grid["grid_at_station_nearest_valid_days"]
    )
    grid["grid_at_station_local_3x3_share_days_ge_30cm"] = (
        grid["grid_at_station_local_3x3_days_ge_30cm"]
        / grid["grid_at_station_local_3x3_valid_days"]
    )
    base = cells.merge(grid, on="resort_id", validate="one_to_many")
    station = station_winter[
        [
            "station_code",
            "winter_start_year",
            "winter_mean_snow_depth_cm",
            "share_observed_days_snow_depth_ge_30cm",
            "snow_depth_observation_coverage_share",
            "winter_snow_proxy_usable",
        ]
    ].rename(
        columns={
            "station_code": "selected_station_code",
            "winter_mean_snow_depth_cm": "station_mean_snow_depth_cm",
            "share_observed_days_snow_depth_ge_30cm": "station_share_days_ge_30cm",
            "snow_depth_observation_coverage_share": "station_observation_coverage_share",
            "winter_snow_proxy_usable": "station_winter_usable",
        }
    )
    result = base.merge(
        station,
        on=["selected_station_code", "winter_start_year"],
        how="left",
        validate="many_to_one",
    )
    result["grid_winter_complete"] = (
        result["grid_nearest_valid_days"].eq(result["grid_expected_days"])
        & result["grid_local_3x3_valid_days"].eq(result["grid_expected_days"])
        & result["grid_at_station_nearest_valid_days"].eq(result["grid_expected_days"])
        & result["grid_at_station_local_3x3_valid_days"].eq(
            result["grid_expected_days"]
        )
    )
    result["station_winter_usable"] = as_bool(result["station_winter_usable"])
    result["source_ids"] = f"SLF_IMIS_DAILY_SNOW|{SOURCE_ID}|{DERIVED_SOURCE_ID}"
    result["direct_slope_representation"] = False
    result["independent_measurement_network"] = False
    result["causal_covariate_approved"] = False
    return result.sort_values(["resort_id", "winter_start_year"]).reset_index(drop=True)


def grade(correlation: float, relative_difference: float, reliability_gap: float, n: int) -> str:
    if n < 8 or pd.isna(correlation):
        return "insufficient_common_winters"
    if correlation >= 0.75 and relative_difference <= 0.35 and reliability_gap <= 0.20:
        return "high"
    if correlation >= 0.50 and relative_difference <= 0.60:
        return "moderate"
    return "low"


def compare_group(frame: pd.DataFrame, prefix: str) -> dict:
    usable = frame[
        frame["grid_winter_complete"]
        & frame["station_winter_usable"]
        & frame["station_mean_snow_depth_cm"].notna()
        & frame[f"{prefix}_mean_snow_depth_cm"].notna()
    ].copy()
    station = usable["station_mean_snow_depth_cm"]
    grid = usable[f"{prefix}_mean_snow_depth_cm"]
    correlation = (
        float(station.corr(grid))
        if len(usable) >= 5 and station.nunique() > 1 and grid.nunique() > 1
        else np.nan
    )
    station_mean = float(station.mean()) if len(usable) else np.nan
    grid_mean = float(grid.mean()) if len(usable) else np.nan
    mad = float((station - grid).abs().mean()) if len(usable) else np.nan
    relative = mad / station_mean if pd.notna(station_mean) and station_mean > 0 else np.nan
    station_reliability = float(usable["station_share_days_ge_30cm"].mean())
    grid_reliability = float(usable[f"{prefix}_share_days_ge_30cm"].mean())
    gap = abs(station_reliability - grid_reliability)
    return {
        "common_usable_winters": int(len(usable)),
        "winter_mean_depth_correlation": correlation,
        "station_mean_winter_depth_cm": station_mean,
        "grid_mean_winter_depth_cm": grid_mean,
        "mean_absolute_winter_depth_difference_cm": mad,
        "relative_mean_absolute_depth_difference": relative,
        "station_snow_reliability_share_ge_30cm": station_reliability,
        "grid_snow_reliability_share_ge_30cm": grid_reliability,
        "absolute_reliability_share_difference": gap,
        "agreement": grade(correlation, relative, gap, len(usable)),
    }


def component_comparisons(component_winter: pd.DataFrame) -> pd.DataFrame:
    rows = []
    identity = [
        "destination_unit_ids",
        "resort_id",
        "resort_name_canonical",
        "altitude_top_m",
        "selected_station_code",
        "selected_station_label",
        "selected_station_distance_km",
        "selected_station_elevation_m",
        "grid_easting_m",
        "grid_northing_m",
        "grid_cell_distance_m",
        "grid_local_cell_count",
        "station_location_grid_easting_m",
        "station_location_grid_northing_m",
        "station_location_grid_cell_distance_m",
        "station_location_grid_local_cell_count",
    ]
    for _, frame in component_winter.groupby("resort_id", observed=True):
        row = frame.iloc[0][identity].to_dict()
        nearest = compare_group(frame, "grid_nearest")
        local = compare_group(frame, "grid_local_3x3")
        station_local = compare_group(frame, "grid_at_station_local_3x3")
        row.update({f"nearest_{key}": value for key, value in nearest.items()})
        row.update({f"local_3x3_{key}": value for key, value in local.items()})
        row.update(
            {f"station_location_3x3_{key}": value for key, value in station_local.items()}
        )
        row.update(
            {
                "primary_grid_rule": "daily_median_of_nearest_3x3_grid_cells_then_november_april_mean",
                "grid_elevation_match_available": False,
                "direct_slope_representation": False,
                "independent_measurement_network": False,
                "causal_covariate_approved": False,
                "source_ids": f"SLF_IMIS_DAILY_SNOW|{SOURCE_ID}|{DERIVED_SOURCE_ID}",
            }
        )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["destination_unit_ids", "resort_id"])


def destination_outputs(
    component_winter: pd.DataFrame,
    unit_by_resort: dict[str, list[str]],
    destination_names: dict[str, str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    expanded = []
    for row in component_winter.to_dict("records"):
        for destination_id in unit_by_resort[row["resort_id"]]:
            expanded.append({**row, "destination_unit_id": destination_id})
    frame = pd.DataFrame(expanded)
    rows = []
    for (destination_id, winter), group in frame.groupby(
        ["destination_unit_id", "winter_start_year"], observed=True
    ):
        unique_stations = group.drop_duplicates("selected_station_code")
        rows.append(
            {
                "destination_unit_id": destination_id,
                "destination_name": destination_names[destination_id],
                "winter_start_year": int(winter),
                "winter_season": f"{winter}/{winter + 1}",
                "component_count": int(group["resort_id"].nunique()),
                "grid_component_count_complete": int(group["grid_winter_complete"].sum()),
                "station_count_expected": int(unique_stations["selected_station_code"].nunique()),
                "station_count_usable": int(unique_stations["station_winter_usable"].sum()),
                "grid_winter_complete": bool(group["grid_winter_complete"].all()),
                "station_winter_complete": bool(unique_stations["station_winter_usable"].all()),
                "station_mean_snow_depth_cm": unique_stations[
                    "station_mean_snow_depth_cm"
                ].mean(),
                "grid_local_3x3_mean_snow_depth_cm": group[
                    "grid_local_3x3_mean_snow_depth_cm"
                ].mean(),
                "station_share_days_ge_30cm": unique_stations[
                    "station_share_days_ge_30cm"
                ].mean(),
                "grid_local_3x3_share_days_ge_30cm": group[
                    "grid_local_3x3_share_days_ge_30cm"
                ].mean(),
                "independent_measurement_network": False,
                "causal_covariate_approved": False,
                "source_ids": f"SLF_IMIS_DAILY_SNOW|{SOURCE_ID}|{DERIVED_SOURCE_ID}",
            }
        )
    winter = pd.DataFrame(rows).sort_values(
        ["destination_unit_id", "winter_start_year"]
    )
    winter["station_winter_usable"] = winter["station_winter_complete"]
    summaries = []
    for destination_id, group in winter.groupby("destination_unit_id", observed=True):
        compared = compare_group(group, "grid_local_3x3")
        summaries.append(
            {
                "destination_unit_id": destination_id,
                "destination_name": destination_names[destination_id],
                **compared,
                "primary_grid_rule": "mean_of_component_daily_3x3_median_winter_means",
                "independent_measurement_network": False,
                "causal_covariate_approved": False,
            }
        )
    return winter, pd.DataFrame(summaries).sort_values("destination_unit_id")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["analysis_version"] != "path_c_v0_28":
        raise RuntimeError("Unexpected SPASS analysis version")
    metadata, netcdf_path = source_metadata(config)
    components, unit_by_resort, destination_names = reviewed_components()
    station_winter = pd.read_csv(ROOT / "data_processed" / "slf_snow_station_winter.csv")

    with ascii_netcdf_path(netcdf_path) as ascii_path, Dataset(str(ascii_path)) as dataset:
        if dataset.getncattr("convention") != "CF-1.8":
            raise RuntimeError("Unexpected SPASS CF convention")
        expected_dimensions = {"E": 370, "N": 265, "time": 22645}
        actual_dimensions = {name: len(value) for name, value in dataset.dimensions.items()}
        if actual_dimensions != expected_dimensions:
            raise RuntimeError(f"Unexpected SPASS dimensions: {actual_dimensions}")
        variable = dataset.variables["HSCLQMD"]
        if variable.dimensions != ("time", "N", "E") or variable.shape != (22645, 265, 370):
            raise RuntimeError("Unexpected SPASS snow variable grain")
        if variable.getncattr("version") != "v1.0":
            raise RuntimeError("Unexpected SPASS snow variable version")
        if "units" in variable.ncattrs():
            raise RuntimeError("SPASS unit-metadata assumption must be reviewed")
        east = np.asarray(dataset.variables["E"][:], dtype=float)
        north = np.asarray(dataset.variables["N"][:], dtype=float)
        if not np.allclose(np.diff(east), 1000) or not np.allclose(np.diff(north), 1000):
            raise RuntimeError("SPASS grid is not the expected regular 1 km grid")
        time = dataset.variables["time"]
        raw_dates = num2date(time[:], units=time.units, calendar=time.calendar)
        dates = pd.DatetimeIndex([pd.Timestamp(value.isoformat()) for value in raw_dates])
        if dates[0] != pd.Timestamp("1961-09-01") or dates[-1] != pd.Timestamp("2023-08-31"):
            raise RuntimeError("Unexpected SPASS temporal coverage")
        resort_cells = cell_index_table(
            components, east, north, target_kind="resort_component"
        )
        station_cells = cell_index_table(
            components, east, north, target_kind="selected_station"
        )
        target_daily = extract_daily_grid(
            variable,
            dates,
            pd.concat([resort_cells, station_cells], ignore_index=True),
            2013,
            2022,
        )
        daily = target_daily[
            target_daily["grid_target_kind"].eq("resort_component")
        ].drop(columns="grid_target_kind")
        station_daily = target_daily[
            target_daily["grid_target_kind"].eq("selected_station")
        ].drop(columns="grid_target_kind")
        station_daily = station_daily.rename(
            columns={
                "grid_nearest_snow_depth_cm": "grid_at_station_nearest_snow_depth_cm",
                "grid_local_3x3_median_snow_depth_cm": (
                    "grid_at_station_local_3x3_median_snow_depth_cm"
                ),
            }
        )
        daily = daily.merge(
            station_daily,
            on=["resort_id", "date", "winter_start_year"],
            validate="one_to_one",
        )
        station_cell_fields = [
            "resort_id",
            "grid_e_index",
            "grid_n_index",
            "grid_easting_m",
            "grid_northing_m",
            "grid_cell_distance_m",
            "grid_local_cell_count",
        ]
        station_cell_names = {
            name: f"station_location_{name}"
            for name in station_cell_fields
            if name != "resort_id"
        }
        cells = resort_cells.merge(
            station_cells[station_cell_fields].rename(columns=station_cell_names),
            on="resort_id",
            validate="one_to_one",
        )

    component_winter = build_component_winter(daily, cells, station_winter)
    if len(component_winter) != 150 or not component_winter["grid_winter_complete"].all():
        raise RuntimeError("SPASS component-winter panel is not 15 × 10 complete")
    comparisons = component_comparisons(component_winter)
    destination_winter, destination_summary = destination_outputs(
        component_winter, unit_by_resort, destination_names
    )

    component_winter.to_csv(COMPONENT_WINTER_OUTPUT, index=False, na_rep="NA")
    comparisons.to_csv(COMPONENT_COMPARISON_OUTPUT, index=False, na_rep="NA")
    destination_winter.to_csv(DESTINATION_WINTER_OUTPUT, index=False, na_rep="NA")
    destination_summary.to_csv(DESTINATION_SUMMARY_OUTPUT, index=False, na_rep="NA")

    component_counts = comparisons["local_3x3_agreement"].value_counts().to_dict()
    station_location_counts = comparisons[
        "station_location_3x3_agreement"
    ].value_counts().to_dict()
    destination_counts = destination_summary["agreement"].value_counts().to_dict()
    summary = {
        "analysis_version": config["analysis_version"],
        "source_id": SOURCE_ID,
        "source_doi": config["doi"],
        "source_archive_sha256": metadata["sha256"],
        "source_netcdf_sha256": metadata["extracted_sha256"],
        "source_grid": config["grid"],
        "source_hydrological_years": [1962, 2023],
        "comparison_winter_start_years": [2013, 2022],
        "source_netcdf_unit_attribute_present": False,
        "raw_value_unit_interpretation": (
            "metres converted to centimetres; inferred from physically plausible raw magnitude "
            "and the peer-reviewed definition of HS analyses in centimetres"
        ),
        "reviewed_components": int(len(comparisons)),
        "unique_nearest_grid_cells": int(
            cells[["grid_e_index", "grid_n_index"]].drop_duplicates().shape[0]
        ),
        "unique_station_location_grid_cells": int(
            cells[
                ["station_location_grid_e_index", "station_location_grid_n_index"]
            ].drop_duplicates().shape[0]
        ),
        "maximum_grid_cell_distance_to_component_m": float(
            cells["grid_cell_distance_m"].max()
        ),
        "maximum_grid_cell_distance_to_station_m": float(
            cells["station_location_grid_cell_distance_m"].max()
        ),
        "component_winter_rows": int(len(component_winter)),
        "component_winters_grid_complete": int(
            component_winter["grid_winter_complete"].sum()
        ),
        "component_local_3x3_agreement_counts": component_counts,
        "component_station_location_3x3_agreement_counts": station_location_counts,
        "median_component_local_3x3_winter_depth_correlation": float(
            comparisons["local_3x3_winter_mean_depth_correlation"].median()
        ),
        "median_component_local_3x3_relative_depth_difference": float(
            comparisons["local_3x3_relative_mean_absolute_depth_difference"].median()
        ),
        "median_component_station_location_3x3_winter_depth_correlation": float(
            comparisons[
                "station_location_3x3_winter_mean_depth_correlation"
            ].median()
        ),
        "median_component_station_location_3x3_relative_depth_difference": float(
            comparisons[
                "station_location_3x3_relative_mean_absolute_depth_difference"
            ].median()
        ),
        "destination_units": int(len(destination_summary)),
        "destination_winter_rows": int(len(destination_winter)),
        "destination_winters_both_complete": int(
            (destination_winter["grid_winter_complete"] & destination_winter["station_winter_complete"]).sum()
        ),
        "destination_agreement_counts": destination_counts,
        "median_destination_winter_depth_correlation": float(
            destination_summary["winter_mean_depth_correlation"].median()
        ),
        "median_destination_relative_depth_difference": float(
            destination_summary["relative_mean_absolute_depth_difference"].median()
        ),
        "independent_measurement_network": False,
        "gridded_snow_causal_covariates_approved": 0,
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# SPASS gridded-snow sensitivity

Generated reproducibly by `src/data_processing/build_snow_gridded_sensitivity.py`.

## Purpose and source

This audit compares the selected SLF IMIS station proxy with the peer-reviewed SPASS OSHD-CLQM daily snow-depth grid (DOI `{config['doi']}`). SPASS supplies a 1 km grid for hydrological years 1962–2023. The common project window contains ten complete November–April winters, 2013/14 through 2022/23.

SPASS is a modelled product, not a second measurement network. It is driven by gridded MeteoSwiss temperature/precipitation, quantile-mapped to mimic OSHD-EKF, whose target assimilates snow observations from 350 stations, and converted from SWE to snow depth with SWE2HS. It therefore changes spatial representation and method, but is not independent of the broader SLF snow-observation system.

## Method

For every reviewed resort component, the script retains both the nearest 1 km cell and the daily median of its surrounding 3×3 cells before forming November–April winter means and ≥30 cm day shares. The same extraction is repeated around the selected station itself. This separates disagreement caused by the model/measurement method from disagreement caused by using a station located away from the resort point. The resort-centred local 3×3 statistic is primary because the source publication recommends some spatial aggregation and cautions against single-cell interpretation. The comparison deliberately does not reproduce the publication's elevation-matched 3×3 selection because the distributed NetCDF contains no grid elevation and resort-top altitude is not a piste elevation distribution.

The `HSCLQMD` variable has no `units` attribute. Raw values (country maximum about 3 m on the inspected winter day) are interpreted as metres and converted to centimetres; the publication defines its HS analyses in centimetres. This upstream metadata omission remains explicit in the output and is a limitation rather than silently invented metadata.

## Results

- Reviewed components / unique resort-centred nearest cells / unique station-centred nearest cells: **{summary['reviewed_components']} / {summary['unique_nearest_grid_cells']} / {summary['unique_station_location_grid_cells']}**.
- Maximum component-to-cell-centre / station-to-cell-centre distance: **{summary['maximum_grid_cell_distance_to_component_m']:.1f} m / {summary['maximum_grid_cell_distance_to_station_m']:.1f} m**.
- Complete component-winters: **{summary['component_winters_grid_complete']} / {summary['component_winter_rows']}**.
- Component agreement using the resort-centred local 3×3 rule: **{json.dumps(component_counts, ensure_ascii=False, sort_keys=True)}**.
- Component agreement using the station-centred local 3×3 diagnostic: **{json.dumps(station_location_counts, ensure_ascii=False, sort_keys=True)}**.
- Median resort-centred / station-centred winter-depth correlation: **{summary['median_component_local_3x3_winter_depth_correlation']:.3f} / {summary['median_component_station_location_3x3_winter_depth_correlation']:.3f}**.
- Median resort-centred / station-centred relative mean absolute depth difference: **{summary['median_component_local_3x3_relative_depth_difference']:.1%} / {summary['median_component_station_location_3x3_relative_depth_difference']:.1%}**.
- Destination winters with both grid and station proxies complete: **{summary['destination_winters_both_complete']} / {summary['destination_winter_rows']}**.
- Destination agreement: **{json.dumps(destination_counts, ensure_ascii=False, sort_keys=True)}**.
- Median destination winter-depth correlation: **{summary['median_destination_winter_depth_correlation']:.3f}**.
- Median destination relative mean absolute depth difference: **{summary['median_destination_relative_depth_difference']:.1%}**.

The agreement thresholds are the same conservative rules used by the next-nearest-station sensitivity: high requires at least eight common winters, correlation ≥0.75, relative mean absolute difference ≤35%, and an absolute ≥30 cm reliability-share gap ≤0.20; moderate requires correlation ≥0.50 and relative difference ≤60%.

## Decision and limitations

Station measurements represent flat local observation sites and can overrepresent snow relative to a 1 km areal cell. Conversely, SPASS smooths unresolved terrain and land-cover effects, inherits limitations from the daily temperature and precipitation fields, does not fully correct monthly or single-winter bias, and converts SWE to depth. The grid ends in August 2023, so it cannot evaluate the two latest project winters. It is neither direct piste snow nor snowmaking, grooming, wind redistribution or operating-day evidence.

Interpretation: `{INTERPRETATION}`. Every causal approval remains false. A genuinely independent measurement or reanalysis product is still required if snow is proposed as a causal covariate.

Detailed outputs: `{COMPONENT_WINTER_OUTPUT.relative_to(ROOT).as_posix()}`, `{COMPONENT_COMPARISON_OUTPUT.relative_to(ROOT).as_posix()}`, `{DESTINATION_WINTER_OUTPUT.relative_to(ROOT).as_posix()}`, and `{DESTINATION_SUMMARY_OUTPUT.relative_to(ROOT).as_posix()}`.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
