"""Build same-destination municipality distance exposure and descriptive pre/post gradients."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely import from_wkb, make_valid
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
INTERIM_DIR = ROOT / "data_interim" / "swissboundaries3d_2026"
DISTANCE_OUTPUT = ROOT / "data_processed" / "treatment_municipality_distance_exposure.csv"
DIAGNOSTIC_OUTPUT = ROOT / "data_processed" / "treatment_distance_gradient_diagnostic.csv"
RING_OUTPUT = ROOT / "reports" / "treatment_distance_ring_summary.csv"
NEAR_FAR_OUTPUT = ROOT / "reports" / "treatment_distance_near_far_contrast.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "treatment_distance_gradient_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "15_TREATMENT_DISTANCE_GRADIENT.md"
SOURCE_ID = "SWISSTOPO_BOUNDARIES_2026"


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().eq("true")


def normalise_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def gpkg_geometry(blob: bytes):
    if blob[:2] != b"GP":
        raise ValueError("Unexpected GeoPackage geometry header")
    envelope_code = (blob[3] >> 1) & 7
    envelope_bytes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[envelope_code]
    geometry = from_wkb(blob[8 + envelope_bytes :])
    return make_valid(geometry) if not geometry.is_valid else geometry


def exact_metadata() -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{SOURCE_ID}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == SOURCE_ID:
            records.append(record)
    if len(records) != 1:
        raise ValueError(f"Expected one cached {SOURCE_ID} record, found {len(records)}")
    return records[0]


def checked_gpkg() -> Path:
    metadata = exact_metadata()
    archive = ROOT / metadata["raw_file"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != metadata["sha256"]:
        raise RuntimeError("swissBOUNDARIES3D archive checksum mismatch")
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        members = [item for item in bundle.infolist() if item.filename.lower().endswith(".gpkg")]
        if len(members) != 1:
            raise ValueError(f"Expected one GeoPackage in archive, found {len(members)}")
        output = INTERIM_DIR / Path(members[0].filename).name
        if not output.exists() or output.stat().st_size != members[0].file_size:
            bundle.extract(members[0], INTERIM_DIR)
        bundle.testzip()
    return output


def hotel_bfs_mapping() -> pd.DataFrame:
    candidates = sorted(
        path
        for path in EVIDENCE_DIR.glob("BFS_HOTEL_METADATA_*.json")
        if not path.name.endswith(".metadata.json")
    )
    if not candidates:
        raise FileNotFoundError("No cached BFS hotel metadata")
    payload = json.loads(candidates[-1].read_text(encoding="utf-8"))
    dimension = next(item for item in payload["variables"] if item["code"] == "Gemeinde")
    mapping = pd.DataFrame(
        {
            "municipality_bfs_id": pd.Series(dimension["values"], dtype="int64"),
            "bfs_municipality_name": dimension["valueTexts"],
        }
    )
    mapping["normalised_name"] = mapping["bfs_municipality_name"].map(normalise_name)
    if mapping["normalised_name"].duplicated().any():
        raise ValueError("Normalised BFS hotel municipality names are not unique")
    return mapping


def load_hotel_municipalities(gpkg: Path) -> pd.DataFrame:
    hotel = pd.read_csv(
        ROOT / "data_processed" / "hotel_municipality_month.csv",
        usecols=["municipality_name_source"],
    ).drop_duplicates()
    hotel["normalised_name"] = hotel["municipality_name_source"].map(normalise_name)
    hotel = hotel.merge(hotel_bfs_mapping(), on="normalised_name", validate="one_to_one")
    # Moutier changed canton on 2026-01-01. The cached HESTA dimension still
    # labels the series Moutier (BE), BFS 700, while the 2026 boundary product
    # assigns the current polygon BFS 6831. Keep both IDs and expose the bridge.
    hotel["boundary_bfs_id_2026"] = hotel["municipality_bfs_id"].replace({700: 6831})
    hotel["boundary_bfs_bridge_status"] = np.where(
        hotel["municipality_bfs_id"].eq(hotel["boundary_bfs_id_2026"]),
        "same_bfs_id",
        "explicit_Moutier_700_to_6831_canton_transfer_bridge",
    )
    query = (
        "SELECT bfs_nummer,name,gem_flaeche,einwohnerzahl,geom "
        "FROM tlm_hoheitsgebiet WHERE objektart='Gemeindegebiet' AND icc='CH'"
    )
    with sqlite3.connect(gpkg.resolve().as_uri() + "?mode=ro", uri=True) as database:
        rows = database.execute(query).fetchall()
    geometry = pd.DataFrame(
        rows,
        columns=[
            "boundary_bfs_id_2026",
            "boundary_name",
            "municipality_area_ha_2026",
            "municipality_population_snapshot",
            "geometry_blob",
        ],
    )
    geometry["geometry"] = geometry.pop("geometry_blob").map(gpkg_geometry)
    hotel = hotel.merge(geometry, on="boundary_bfs_id_2026", validate="many_to_one")
    if len(hotel) != 186:
        raise ValueError(f"Expected 186 hotel municipalities with geometry, found {len(hotel)}")
    return hotel


def distance_band(distance_km: float) -> str:
    if distance_km <= 15:
        return "00_15km"
    if distance_km <= 30:
        return "15_30km"
    if distance_km <= 50:
        return "30_50km"
    if distance_km <= 100:
        return "50_100km"
    return "over_100km"


def main() -> None:
    gpkg = checked_gpkg()
    municipalities = load_hotel_municipalities(gpkg)
    resorts = pd.read_csv(ROOT / "data_processed" / "resort_master.csv")
    units = pd.read_csv(ROOT / "data_processed" / "treatment_destination_units.csv")
    scopes = pd.read_csv(ROOT / "data_processed" / "treatment_destination_municipality.csv")
    continuity = pd.read_csv(ROOT / "reports" / "membership_continuity_audit.csv")
    hotel = pd.read_csv(ROOT / "data_processed" / "hotel_municipality_month.csv")
    hotel["date"] = pd.to_datetime(hotel["date"], errors="raise")
    hotel["normalised_name"] = hotel["municipality_name_source"].map(normalise_name)
    hotel = hotel.merge(
        hotel_bfs_mapping()[["normalised_name", "municipality_bfs_id"]],
        on="normalised_name",
        validate="many_to_one",
    )

    coordinate_transform = Transformer.from_crs(4326, 2056, always_xy=True)
    inverse_transform = Transformer.from_crs(2056, 4326, always_xy=True)
    reviewed = units[as_bool(units["eligible_for_reviewed_outcome_panel"])].copy()
    distance_rows: list[dict] = []
    for unit in reviewed.itertuples(index=False):
        component_ids = str(unit.component_resort_ids).split("|")
        components = resorts[resorts["resort_id"].isin(component_ids)].copy()
        if len(components) != len(component_ids):
            raise ValueError(f"Missing component resort for {unit.destination_unit_id}")
        component_points = []
        for component in components.itertuples(index=False):
            x, y = coordinate_transform.transform(component.longitude, component.latitude)
            component_points.append((component.resort_id, component.resort_name_canonical, Point(x, y)))
        outcome_ids = set(
            scopes.loc[
                scopes["destination_unit_id"].eq(unit.destination_unit_id),
                "municipality_bfs_id",
            ].astype(int)
        )
        for municipality in municipalities.itertuples(index=False):
            representative = municipality.geometry.representative_point()
            centroid = municipality.geometry.centroid
            representative_distances = np.array(
                [representative.distance(point) / 1000 for _, _, point in component_points]
            )
            polygon_distances = np.array(
                [municipality.geometry.distance(point) / 1000 for _, _, point in component_points]
            )
            centroid_distances = np.array(
                [centroid.distance(point) / 1000 for _, _, point in component_points]
            )
            nearest_index = int(representative_distances.argmin())
            nearest_id, nearest_name, _ = component_points[nearest_index]
            representative_lon, representative_lat = inverse_transform.transform(
                representative.x, representative.y
            )
            distance_rows.append(
                {
                    "destination_unit_id": unit.destination_unit_id,
                    "destination_name": unit.destination_name,
                    "analysis_anchor": unit.first_analysis_anchor,
                    "component_resort_count": len(component_points),
                    "nearest_component_resort_id": nearest_id,
                    "nearest_component_resort_name": nearest_name,
                    "municipality_bfs_id": int(municipality.municipality_bfs_id),
                    "boundary_bfs_id_2026": int(municipality.boundary_bfs_id_2026),
                    "boundary_bfs_bridge_status": municipality.boundary_bfs_bridge_status,
                    "municipality_name": municipality.municipality_name_source,
                    "municipality_boundary_name_2026": municipality.boundary_name,
                    "municipality_area_ha_2026": municipality.municipality_area_ha_2026,
                    "municipality_representative_longitude": representative_lon,
                    "municipality_representative_latitude": representative_lat,
                    "representative_point_distance_to_destination_km": float(
                        representative_distances[nearest_index]
                    ),
                    "centroid_distance_to_destination_km": float(
                        centroid_distances.min()
                    ),
                    "minimum_polygon_distance_to_destination_km": float(
                        polygon_distances.min()
                    ),
                    "representative_distance_band": distance_band(
                        float(representative_distances[nearest_index])
                    ),
                    "destination_component_inside_municipality": bool(
                        np.isclose(polygon_distances.min(), 0.0, atol=1e-9)
                    ),
                    "reviewed_outcome_scope_municipality": int(
                        municipality.municipality_bfs_id
                    )
                    in outcome_ids,
                    "boundary_reference_date": "2026-01-01",
                    "distance_method": "minimum_EPSG2056_distance_to_component_resort_point",
                    "exposure_interpretation": "descriptive_same_destination_distance_only",
                    "causal_exposure_approved": False,
                    "source_id": SOURCE_ID,
                }
            )
    distance = pd.DataFrame(distance_rows).sort_values(
        ["destination_unit_id", "municipality_bfs_id"]
    )
    distance.to_csv(DISTANCE_OUTPUT, index=False)

    eligible = reviewed.merge(
        continuity[
            ["destination_unit_id", "continuity_fully_documented"]
        ],
        on="destination_unit_id",
        validate="one_to_one",
    )
    eligible = eligible[
        as_bool(eligible["continuity_fully_documented"])
        & as_bool(eligible["has_24_observed_pre_months"])
        & as_bool(eligible["has_24_active_post_months_assumption"])
    ]
    diagnostics: list[dict] = []
    for unit in eligible.itertuples(index=False):
        anchor = pd.Timestamp(unit.first_analysis_anchor)
        pre_start = anchor - pd.DateOffset(months=24)
        post_end = anchor + pd.DateOffset(months=24)
        scoped_distance = distance[distance["destination_unit_id"].eq(unit.destination_unit_id)]
        for municipality in scoped_distance.itertuples(index=False):
            series = hotel[hotel["municipality_bfs_id"].eq(municipality.municipality_bfs_id)]
            pre = series[series["date"].between(pre_start, anchor, inclusive="left")]
            post = series[series["date"].between(anchor, post_end, inclusive="left")]
            pre_observed = pre[pre["hotel_overnights"].notna()]
            post_observed = post[post["hotel_overnights"].notna()]
            pre_mean = pre_observed["hotel_overnights"].mean()
            post_mean = post_observed["hotel_overnights"].mean()
            pre_log_mean = np.log1p(pre_observed["hotel_overnights"]).mean()
            post_log_mean = np.log1p(post_observed["hotel_overnights"]).mean()
            diagnostics.append(
                {
                    "destination_unit_id": unit.destination_unit_id,
                    "destination_name": unit.destination_name,
                    "analysis_anchor": anchor.date().isoformat(),
                    "municipality_bfs_id": municipality.municipality_bfs_id,
                    "municipality_name": municipality.municipality_name,
                    "representative_point_distance_to_destination_km": municipality.representative_point_distance_to_destination_km,
                    "minimum_polygon_distance_to_destination_km": municipality.minimum_polygon_distance_to_destination_km,
                    "representative_distance_band": municipality.representative_distance_band,
                    "reviewed_outcome_scope_municipality": municipality.reviewed_outcome_scope_municipality,
                    "pre_window_start": pre_start.date().isoformat(),
                    "pre_window_end": (anchor - pd.DateOffset(months=1)).date().isoformat(),
                    "post_window_start": anchor.date().isoformat(),
                    "post_window_end": (post_end - pd.DateOffset(months=1)).date().isoformat(),
                    "pre_observed_months": int(len(pre_observed)),
                    "post_observed_months": int(len(post_observed)),
                    "pre_covid_sensitivity_months": int(
                        pre["date"].between("2020-03-01", "2022-04-01").sum()
                    ),
                    "post_covid_sensitivity_months": int(
                        post["date"].between("2020-03-01", "2022-04-01").sum()
                    ),
                    "pre_mean_monthly_hotel_overnights": pre_mean,
                    "post_mean_monthly_hotel_overnights": post_mean,
                    "descriptive_log_change_post_minus_pre": post_log_mean - pre_log_mean,
                    "descriptive_percent_change_mean_overnights": (
                        100 * (post_mean / pre_mean - 1)
                        if pd.notna(pre_mean) and pre_mean > 0 and pd.notna(post_mean)
                        else np.nan
                    ),
                    "distance_gradient_usable": len(pre_observed) >= 18
                    and len(post_observed) >= 18,
                    "causal_effect_estimate": False,
                    "diagnostic_note": (
                        "Same-destination descriptive 24-month comparison. No common-shock, "
                        "trend, spillover, boundary-history or treatment-intensity adjustment."
                    ),
                }
            )
    diagnostic = pd.DataFrame(diagnostics).sort_values(
        ["destination_unit_id", "municipality_bfs_id"]
    )
    diagnostic.to_csv(DIAGNOSTIC_OUTPUT, index=False, na_rep="NA")

    usable = diagnostic[as_bool(diagnostic["distance_gradient_usable"])].copy()
    ring = (
        usable.groupby(
            ["destination_unit_id", "destination_name", "representative_distance_band"],
            observed=True,
        )
        .agg(
            municipalities=("municipality_bfs_id", "nunique"),
            median_distance_km=("representative_point_distance_to_destination_km", "median"),
            median_log_change_post_minus_pre=("descriptive_log_change_post_minus_pre", "median"),
            median_percent_change_mean_overnights=("descriptive_percent_change_mean_overnights", "median"),
            mean_log_change_post_minus_pre=("descriptive_log_change_post_minus_pre", "mean"),
            municipalities_with_pre_covid_overlap=("pre_covid_sensitivity_months", lambda values: int((values > 0).sum())),
            municipalities_with_post_covid_overlap=("post_covid_sensitivity_months", lambda values: int((values > 0).sum())),
        )
        .reset_index()
        .sort_values(["destination_unit_id", "representative_distance_band"])
    )
    ring["causal_effect_estimate"] = False
    ring.to_csv(RING_OUTPUT, index=False, na_rep="NA")

    near_far_rows: list[dict] = []
    for (destination_unit_id, destination_name), group in usable.groupby(
        ["destination_unit_id", "destination_name"], observed=True
    ):
        near = group[
            group["representative_point_distance_to_destination_km"].le(30)
        ]
        far = group[
            group["representative_point_distance_to_destination_km"].gt(50)
        ]
        near_median = near["descriptive_log_change_post_minus_pre"].median()
        far_median = far["descriptive_log_change_post_minus_pre"].median()
        near_far_rows.append(
            {
                "destination_unit_id": destination_unit_id,
                "destination_name": destination_name,
                "near_definition": "representative_point_distance_le_30km",
                "far_definition": "representative_point_distance_gt_50km",
                "buffer_excluded": "30_to_50km",
                "near_municipalities": int(near["municipality_bfs_id"].nunique()),
                "far_municipalities": int(far["municipality_bfs_id"].nunique()),
                "near_median_log_change": near_median,
                "far_median_log_change": far_median,
                "descriptive_near_minus_far_log_change": near_median - far_median,
                "causal_effect_estimate": False,
                "interpretation": "same-destination descriptive contrast only",
            }
        )
    near_far = pd.DataFrame(near_far_rows).sort_values("destination_unit_id")
    near_far.to_csv(NEAR_FAR_OUTPUT, index=False, na_rep="NA")

    summary = {
        "hotel_municipalities_with_2026_geometry": int(
            distance["municipality_bfs_id"].nunique()
        ),
        "distinct_2026_municipality_geometries": int(
            distance["boundary_bfs_id_2026"].nunique()
        ),
        "reviewed_destinations_with_distance_crosswalk": int(
            distance["destination_unit_id"].nunique()
        ),
        "distance_crosswalk_rows": int(len(distance)),
        "continuity_24_24_destinations_in_gradient_diagnostic": int(
            diagnostic["destination_unit_id"].nunique()
        ),
        "distance_gradient_municipality_rows": int(len(diagnostic)),
        "distance_gradient_usable_rows": int(as_bool(diagnostic["distance_gradient_usable"]).sum()),
        "ring_summary_rows": int(len(ring)),
        "near_far_contrast_rows": int(len(near_far)),
        "destinations_with_positive_descriptive_near_far_contrast": int(
            near_far["descriptive_near_minus_far_log_change"].gt(0).sum()
        ),
        "diagnostic_rows_with_pre_covid_overlap": int(
            diagnostic["pre_covid_sensitivity_months"].gt(0).sum()
        ),
        "diagnostic_rows_with_post_covid_overlap": int(
            diagnostic["post_covid_sensitivity_months"].gt(0).sum()
        ),
        "causal_effect_estimates": 0,
        "interpretation": (
            "Distance bands compare municipalities around the same treated destination. "
            "They are descriptive exposure diagnostics, not causal treatment effects."
        ),
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Same-destination municipality distance gradient

Generated reproducibly by `src/causal_inference/build_distance_gradient_diagnostic.py` following the researcher's proposed distance comparison.

## Design

For each of the **{summary['reviewed_destinations_with_distance_crosswalk']} reviewed treated destinations**, the crosswalk compares all **{summary['hotel_municipalities_with_2026_geometry']} hotel municipality series** to the same destination's component resort points. These series map to **{summary['distinct_2026_municipality_geometries']} distinct 2026 geometries** because the source retains both Moutier (BE), BFS 700, and Moutier (JU), BFS 6831; the former is explicitly bridged to the current BFS 6831 polygon. This yields **{summary['distance_crosswalk_rows']:,} destination–municipality rows**. Keeping the destination fixed avoids interpreting cross-resort differences as a distance effect.

Two EPSG:2056 distances are retained:

- representative-point distance, used for common 0–15, 15–30, 30–50, 50–100 and over-100 km bands;
- minimum municipality-polygon distance, which is zero when a component point lies inside the municipality and reduces centroid distortion for large Alpine municipalities.

The seven destinations with documented continuity and 24 observed pre/post months contribute **{summary['distance_gradient_municipality_rows']:,} municipality rows** to a descriptive adjacent-window diagnostic; **{summary['distance_gradient_usable_rows']:,}** have at least 18 observed months in both windows. Ring summaries are in `{RING_OUTPUT.relative_to(ROOT).as_posix()}`.

A direct near-versus-far diagnostic compares the median log change for municipalities at most 30 km away with municipalities beyond 50 km, leaving a 30–50 km buffer. **{summary['destinations_with_positive_descriptive_near_far_contrast']} of {summary['near_far_contrast_rows']} destinations** have a positive descriptive near-minus-far contrast; Moléson is the exception. These signs are exploratory and must not be called effects. The treatment-specific contrasts are in `{NEAR_FAR_OUTPUT.relative_to(ROOT).as_posix()}`.

## What this can and cannot show

The output can reveal whether nearby municipalities around the same treated destination display a different descriptive post-versus-pre pattern than remote municipalities. It is a useful exposure-gradient falsification and scope diagnostic.

It is **not** a treatment-effect estimate. Current 2026 municipal geometry is applied to a 2013–2026 outcome panel; hotel coordinates, validated historical arrival-node travel times, tourism catchments and cross-destination contamination are unavailable for this diagnostic. The current NPVM zonal context is not substituted for those historical exposure measures. The adjacent windows do not remove national trends, COVID, competing passes or simultaneous investments. Every `causal_effect_estimate` and `causal_exposure_approved` flag is therefore false.

Detailed outputs: `{DISTANCE_OUTPUT.relative_to(ROOT).as_posix()}` and `{DIAGNOSTIC_OUTPUT.relative_to(ROOT).as_posix()}`.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
