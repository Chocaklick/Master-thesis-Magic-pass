"""Build qualified straight-line context to official public-transport stops.

The BAV/OFT source contains both passenger stops and pure operating points.
Only the official passenger-stop types VP and VPG are eligible. A train
station is defined only from the official elementary transport-mode code B,
including multi-mode combinations containing B. Distances are Euclidean in
EPSG:2056 from supplied resort-listing coordinates and are not routes,
service-frequency measures, or validated destination-arrival access.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
POINT_MUNICIPALITY_PATH = ROOT / "data_processed" / "resort_point_municipality.csv"
FEATURE_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
LISTING_OUTPUT = ROOT / "data_processed" / "resort_public_transport_stop_context.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_public_transport_stop_context.csv"
DECISION_OUTPUT = ROOT / "data_processed" / "magic_pass_decision_support.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "public_transport_stop_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "23_PUBLIC_TRANSPORT_STOP_CONTEXT.md"

SOURCE_ID = "BAV_PUBLIC_TRANSPORT_STOPS_2026"
STAC_SOURCE_ID = "BAV_PUBLIC_TRANSPORT_STOPS_2026_STAC"
MODEL_SOURCE_ID = "BAV_PUBLIC_TRANSPORT_STOPS_MODEL"
SOURCE_STATE_DATE = "2026-09-20"
STAC_DATETIME = "2026-09-13T00:00:00Z"
PASSENGER_STOP_TYPES = ["VP", "VPG"]
TRAIN_MODE_CODE = "B"
INTERPRETATION = (
    "official_current_stop_point_straight_line_context_not_route_service_frequency_"
    "or_validated_resort_arrival_node"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def exact_metadata(source_id: str) -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if len(records) != 1:
        raise ValueError(f"Expected one cached {source_id} record, found {len(records)}")
    record = records[0]
    raw_path = ROOT / record["raw_file"]
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Cached source checksum failure: {source_id}")
    return record


def checked_source(config: dict) -> Path:
    settings = config["public_transport_stop_context"]
    expected = {
        "source_id": SOURCE_ID,
        "source_state_date": SOURCE_STATE_DATE,
        "stac_item_datetime": STAC_DATETIME,
        "distance_crs": "EPSG:2056",
        "passenger_stop_type_codes": PASSENGER_STOP_TYPES,
        "train_mode_element_code": TRAIN_MODE_CODE,
        "train_station_rule": "passenger_stop_with_transport_mode_element_code_B_train",
        "point_eligibility": "supplied_listing_coordinate_inside_unique_current_swiss_municipality",
        "cluster_aggregation": "minimum_median_maximum_across_eligible_supplied_listing_points",
        "interpretation": INTERPRETATION,
    }
    if settings != expected:
        raise ValueError("Unexpected public-transport-stop configuration")

    data_metadata = exact_metadata(SOURCE_ID)
    stac_metadata = exact_metadata(STAC_SOURCE_ID)
    exact_metadata(MODEL_SOURCE_ID)
    stac = json.loads((ROOT / stac_metadata["raw_file"]).read_text(encoding="utf-8"))
    if stac.get("properties", {}).get("datetime") != STAC_DATETIME:
        raise ValueError("Unexpected BAV STAC item datetime")
    asset = stac.get("assets", {}).get("haltestellen-oev_2056_fr.csv.zip", {})
    if asset.get("href") != data_metadata["url"] or asset.get("proj:epsg") != 2056:
        raise ValueError("BAV STAC asset URL or CRS does not match the cached source")
    if asset.get("file:checksum") != "1220" + data_metadata["sha256"]:
        raise ValueError("BAV STAC multihash does not match the cached archive")
    return ROOT / data_metadata["raw_file"]


def load_stops(archive_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("BAV public-transport-stop archive integrity failure")
        required_members = {"PointExploitation.csv", "BordureArret.csv"}
        if not required_members.issubset(archive.namelist()):
            raise ValueError("BAV archive does not contain the required tables")
        release_names = [
            name for name in archive.namelist() if name.startswith("ReleaseNotes_")
        ]
        if len(release_names) != 1:
            raise ValueError("Expected exactly one BAV release-note file")
        release = archive.read(release_names[0]).decode("utf-8-sig")
        points = pd.read_csv(
            io.BytesIO(archive.read("PointExploitation.csv")), dtype="string"
        )

    required_columns = {
        "xtf_id",
        "Numero",
        "Nom",
        "EntrepriseTransport_Abreviation",
        "TypePointExploitation_Code",
        "TypePointExploitation_Designation",
        "MoyenTransport_Code",
        "MoyenTransport_Designation",
        "Commune_Numero",
        "Commune_Nom",
        "Validite_DebutValidite",
        "Validite_FinValidite",
        "Validite_Etat",
        "E",
        "N",
        "H",
    }
    if not required_columns.issubset(points.columns):
        raise ValueError("BAV point table schema changed")
    if len(points) != 28_967 or not points["Numero"].is_unique:
        raise ValueError("Unexpected BAV operating-point grain")
    if points["Validite_Etat"].nunique() != 1 or points["Validite_Etat"].iloc[0] != "20260920":
        raise ValueError("Unexpected BAV source-state date")
    if "Etat: 20.09.2026" not in release:
        raise ValueError("BAV release note does not confirm the configured source-state date")
    source_day = int(SOURCE_STATE_DATE.replace("-", ""))
    starts = pd.to_numeric(points["Validite_DebutValidite"], errors="raise")
    ends = pd.to_numeric(points["Validite_FinValidite"], errors="coerce")
    if (starts > source_day).any() or (ends.dropna() <= source_day).any():
        raise ValueError("BAV archive contains a point outside its source-state validity")

    for column in ["E", "N", "H"]:
        points[column] = pd.to_numeric(points[column], errors="raise")
    passenger = points[
        points["TypePointExploitation_Code"].isin(PASSENGER_STOP_TYPES)
    ].copy()
    if len(passenger) != 27_325 or passenger["MoyenTransport_Code"].isna().any():
        raise ValueError("Unexpected BAV passenger-stop subset")
    passenger["_number_sort"] = pd.to_numeric(passenger["Numero"], errors="raise")
    passenger = passenger.sort_values("_number_sort").drop(columns="_number_sort")
    train = passenger[
        passenger["MoyenTransport_Code"].str.contains(TRAIN_MODE_CODE, regex=False)
    ].copy()
    if len(train) != 1_717:
        raise ValueError("Unexpected BAV train-capable passenger-stop subset")
    summary = {
        "operating_points": int(len(points)),
        "passenger_stops": int(len(passenger)),
        "train_capable_passenger_stops": int(len(train)),
        "passenger_stop_type_counts": {
            str(key): int(value)
            for key, value in passenger["TypePointExploitation_Code"]
            .value_counts()
            .sort_index()
            .items()
        },
        "passenger_stop_mode_counts": {
            str(key): int(value)
            for key, value in passenger["MoyenTransport_Designation"]
            .value_counts()
            .sort_index()
            .items()
        },
    }
    return passenger, train, summary


def nearest_rows(
    queries: pd.DataFrame, pool: pd.DataFrame, prefix: str
) -> pd.DataFrame:
    pool_x = pool["E"].to_numpy(dtype=float)
    pool_y = pool["N"].to_numpy(dtype=float)
    rows = []
    for query in queries.itertuples(index=False):
        squared = (pool_x - query.point_x_2056) ** 2 + (pool_y - query.point_y_2056) ** 2
        chosen = int(np.argmin(squared))
        stop = pool.iloc[chosen]
        rows.append(
            {
                "resort_id": query.resort_id,
                f"nearest_{prefix}_id": str(stop["Numero"]),
                f"nearest_{prefix}_name": str(stop["Nom"]),
                f"nearest_{prefix}_mode_code": str(stop["MoyenTransport_Code"]),
                f"nearest_{prefix}_mode": str(stop["MoyenTransport_Designation"]),
                f"nearest_{prefix}_type_code": str(stop["TypePointExploitation_Code"]),
                f"nearest_{prefix}_type": str(stop["TypePointExploitation_Designation"]),
                f"nearest_{prefix}_operator": (
                    str(stop["EntrepriseTransport_Abreviation"])
                    if pd.notna(stop["EntrepriseTransport_Abreviation"])
                    else ""
                ),
                f"nearest_{prefix}_municipality_bfs_id": (
                    int(stop["Commune_Numero"])
                    if pd.notna(stop["Commune_Numero"])
                    else pd.NA
                ),
                f"nearest_{prefix}_municipality_name": str(stop["Commune_Nom"]),
                f"nearest_{prefix}_x_2056": float(stop["E"]),
                f"nearest_{prefix}_y_2056": float(stop["N"]),
                f"distance_to_nearest_{prefix}_km": float(np.sqrt(squared[chosen]) / 1000),
            }
        )
    return pd.DataFrame(rows)


def build_listing_context(
    passenger: pd.DataFrame, train: pd.DataFrame, config: dict
) -> pd.DataFrame:
    resorts = pd.read_csv(RESORT_PATH)
    crosswalk = pd.read_csv(POINT_MUNICIPALITY_PATH)
    if len(resorts) != 271 or not resorts["resort_id"].is_unique:
        raise ValueError("Unexpected resort listing grain")
    if len(crosswalk) != len(resorts) or not crosswalk["resort_id"].is_unique:
        raise ValueError("Unexpected resort point-municipality crosswalk grain")
    context = resorts[
        [
            "resort_id",
            "resort_name_canonical",
            "cluster_id",
            "latitude",
            "longitude",
        ]
    ].merge(
        crosswalk[
            [
                "resort_id",
                "point_municipality_bfs_id",
                "point_municipality_name",
                "selection_status",
            ]
        ],
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    x, y = transformer.transform(
        context["longitude"].to_numpy(), context["latitude"].to_numpy()
    )
    context["point_x_2056"] = x
    context["point_y_2056"] = y
    eligible = context["selection_status"].eq("unique_current_polygon")
    if int(eligible.sum()) != 268:
        raise ValueError("Unexpected Swiss point-eligibility count")
    query_columns = ["resort_id", "point_x_2056", "point_y_2056"]
    assigned = context.loc[eligible, query_columns]
    context = context.merge(
        nearest_rows(assigned, passenger, "public_transport_stop"),
        on="resort_id",
        how="left",
        validate="one_to_one",
    ).merge(
        nearest_rows(assigned, train, "train_station"),
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    context["public_transport_stop_context_status"] = np.where(
        eligible,
        "assigned_official_swiss_passenger_stop_scope",
        "outside_official_swiss_passenger_stop_scope",
    )
    context["public_transport_stop_values_complete"] = eligible
    settings = config["public_transport_stop_context"]
    context["public_transport_stop_source_state_date"] = settings[
        "source_state_date"
    ]
    context["public_transport_stop_stac_item_datetime"] = settings[
        "stac_item_datetime"
    ]
    context["public_transport_stop_distance_crs"] = settings["distance_crs"]
    context["public_transport_stop_point_eligibility"] = settings[
        "point_eligibility"
    ]
    context["public_transport_stop_scope"] = (
        "official_passenger_stop_types_VP_or_VPG_all_published_modes"
    )
    context["train_station_scope"] = settings["train_station_rule"]
    context["public_transport_stop_distance_method"] = (
        "euclidean_straight_line_from_supplied_listing_coordinate_to_official_stop_point"
    )
    context["public_transport_stop_proximity_interpretation"] = INTERPRETATION
    context["public_transport_stop_proximity_feature_approved"] = False
    context["public_transport_stop_source_ids"] = (
        f"{SOURCE_ID}|{STAC_SOURCE_ID}|{MODEL_SOURCE_ID}"
    )
    distance_columns = [
        "distance_to_nearest_public_transport_stop_km",
        "distance_to_nearest_train_station_km",
    ]
    if context.loc[eligible, distance_columns].isna().any().any():
        raise ValueError("Eligible listing lacks a nearest-stop distance")
    if context.loc[~eligible, distance_columns].notna().any().any():
        raise ValueError("Outside-scope listing received a nearest-stop distance")
    if (context.loc[eligible, distance_columns] < 0).any().any():
        raise ValueError("Negative nearest-stop distance")
    return context


def pipe_unique(series: pd.Series) -> str:
    return "|".join(sorted({str(value) for value in series.dropna() if str(value)}))


def build_cluster_context(listings: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = pd.read_csv(FEATURE_PATH)
    if len(features) != 162 or not features["cluster_id"].is_unique:
        raise ValueError("Unexpected Path C feature grain")
    if set(features["cluster_id"]) != set(listings["cluster_id"]):
        raise ValueError("Listing and Path C cluster universes differ")
    rows = []
    for feature in features.itertuples(index=False):
        group = listings[listings["cluster_id"].eq(feature.cluster_id)].copy()
        usable = group[as_bool(group["public_transport_stop_values_complete"])]
        if len(usable) == len(group):
            status = "complete_all_listing_points_inside_swiss_scope"
        elif len(usable):
            status = "partial_listing_points_outside_swiss_scope"
        else:
            status = "unavailable_no_listing_point_inside_swiss_scope"
        row = {
            "cluster_id": feature.cluster_id,
            "cluster_display_name": feature.cluster_display_name,
            "candidate_for_path_c": str(feature.candidate_for_path_c).lower() == "true",
            "cluster_listing_count": int(len(group)),
            "cluster_listings_with_public_transport_stop_context": int(len(usable)),
            "cluster_listing_public_transport_stop_context_share": len(usable) / len(group),
            "cluster_public_transport_stop_context_status": status,
            "cluster_unassigned_public_transport_stop_resort_ids": pipe_unique(
                group.loc[
                    ~as_bool(group["public_transport_stop_values_complete"]), "resort_id"
                ]
            ),
        }
        for prefix in ["public_transport_stop", "train_station"]:
            distance = f"distance_to_nearest_{prefix}_km"
            values = usable[distance].astype(float)
            for statistic, calculation in {
                "minimum": values.min,
                "median": values.median,
                "maximum": values.max,
            }.items():
                row[f"cluster_{distance.removesuffix('_km')}_{statistic}_km"] = (
                    float(calculation()) if len(values) else np.nan
                )
            row[f"cluster_{distance.removesuffix('_km')}_range_km"] = (
                float(values.max() - values.min()) if len(values) else np.nan
            )
            row[f"cluster_listing_nearest_{prefix}_ids"] = pipe_unique(
                usable[f"nearest_{prefix}_id"]
            )
            row[f"cluster_listing_nearest_{prefix}_names"] = pipe_unique(
                usable[f"nearest_{prefix}_name"]
            )
            row[f"cluster_listing_nearest_{prefix}_mode_codes"] = pipe_unique(
                usable[f"nearest_{prefix}_mode_code"]
            )
            row[f"cluster_listing_nearest_{prefix}_modes"] = pipe_unique(
                usable[f"nearest_{prefix}_mode"]
            )
        settings = config["public_transport_stop_context"]
        row.update(
            {
                "public_transport_stop_source_state_date": settings[
                    "source_state_date"
                ],
                "public_transport_stop_stac_item_datetime": settings[
                    "stac_item_datetime"
                ],
                "public_transport_stop_distance_crs": settings["distance_crs"],
                "public_transport_stop_point_eligibility": settings[
                    "point_eligibility"
                ],
                "public_transport_stop_scope": (
                    "official_passenger_stop_types_VP_or_VPG_all_published_modes"
                ),
                "train_station_scope": settings["train_station_rule"],
                "public_transport_stop_cluster_aggregation": settings[
                    "cluster_aggregation"
                ],
                "public_transport_stop_proximity_interpretation": INTERPRETATION,
                "public_transport_stop_proximity_feature_approved": False,
                "public_transport_stop_source_ids": (
                    f"{SOURCE_ID}|{STAC_SOURCE_ID}|{MODEL_SOURCE_ID}"
                ),
            }
        )
        rows.append(row)
    context = pd.DataFrame(rows)
    if len(context) != 162 or not context["cluster_id"].is_unique:
        raise ValueError("Cluster stop context must preserve one row per lift cluster")
    if int(context["cluster_listing_count"].sum()) != len(listings):
        raise ValueError("Cluster stop aggregation lost resort listings")
    for prefix in ["public_transport_stop", "train_station"]:
        stem = f"cluster_distance_to_nearest_{prefix}"
        complete = context[f"{stem}_median_km"].notna()
        if not (
            context.loc[complete, f"{stem}_minimum_km"]
            <= context.loc[complete, f"{stem}_median_km"]
        ).all() or not (
            context.loc[complete, f"{stem}_median_km"]
            <= context.loc[complete, f"{stem}_maximum_km"]
        ).all():
            raise ValueError(f"Invalid cluster distance summary for {prefix}")
    return context


def enrich_decision_support(context: pd.DataFrame) -> None:
    decision = pd.read_csv(DECISION_OUTPUT)
    context_columns = [
        column
        for column in context.columns
        if column not in {"cluster_id", "cluster_display_name", "candidate_for_path_c"}
    ]
    decision = decision.drop(
        columns=[column for column in context_columns if column in decision.columns]
    ).merge(
        context[["cluster_id", *context_columns]],
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
    nonblank = [
        column for column in guarded if column in decision and decision[column].notna().any()
    ]
    if nonblank:
        raise ValueError(f"Unapproved decision fields became populated: {nonblank}")
    if as_bool(decision["public_transport_stop_proximity_feature_approved"]).any():
        raise ValueError("Public-transport stop proximity was unexpectedly approved")
    DECISION_OUTPUT.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    passenger, train, source_summary = load_stops(checked_source(config))
    listings = build_listing_context(passenger, train, config)
    listings.to_csv(LISTING_OUTPUT, index=False, lineterminator="\n")
    clusters = build_cluster_context(listings, config)
    clusters.to_csv(CLUSTER_OUTPUT, index=False, lineterminator="\n")
    enrich_decision_support(clusters)

    usable = as_bool(listings["public_transport_stop_values_complete"])
    candidates = clusters[as_bool(clusters["candidate_for_path_c"])]
    summary = {
        "analysis_version": config["analysis_version"],
        "source_state_date": SOURCE_STATE_DATE,
        "stac_item_datetime": STAC_DATETIME,
        **source_summary,
        "resort_listings": int(len(listings)),
        "resort_listings_inside_official_swiss_scope": int(usable.sum()),
        "resort_listings_outside_official_swiss_scope": int((~usable).sum()),
        "outside_scope_resort_ids": listings.loc[~usable, "resort_id"].tolist(),
        "path_c_clusters": int(len(clusters)),
        "path_c_clusters_complete": int(
            clusters["cluster_public_transport_stop_context_status"]
            .eq("complete_all_listing_points_inside_swiss_scope")
            .sum()
        ),
        "path_c_clusters_partial": int(
            clusters["cluster_public_transport_stop_context_status"]
            .eq("partial_listing_points_outside_swiss_scope")
            .sum()
        ),
        "path_c_candidates": int(len(candidates)),
        "path_c_candidates_with_complete_context": int(
            candidates["cluster_public_transport_stop_context_status"]
            .eq("complete_all_listing_points_inside_swiss_scope")
            .sum()
        ),
        "median_cluster_median_distance_to_public_transport_stop_km": float(
            clusters[
                "cluster_distance_to_nearest_public_transport_stop_median_km"
            ].median()
        ),
        "median_cluster_median_distance_to_train_station_km": float(
            clusters["cluster_distance_to_nearest_train_station_median_km"].median()
        ),
        "maximum_listing_distance_to_public_transport_stop_km": float(
            listings.loc[usable, "distance_to_nearest_public_transport_stop_km"].max()
        ),
        "maximum_listing_distance_to_train_station_km": float(
            listings.loc[usable, "distance_to_nearest_train_station_km"].max()
        ),
        "nearest_public_transport_stop_mode_counts_for_eligible_listings": {
            str(key): int(value)
            for key, value in listings.loc[usable, "nearest_public_transport_stop_mode"]
            .value_counts()
            .sort_index()
            .items()
        },
        "approved_features": int(
            as_bool(clusters["public_transport_stop_proximity_feature_approved"]).sum()
        ),
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    outside = ", ".join(
        f"{row.resort_name_canonical} (`{row.resort_id}`)"
        for row in listings.loc[~usable].itertuples(index=False)
    )
    mode_counts = ", ".join(
        f"{mode}: {count}"
        for mode, count in summary[
            "nearest_public_transport_stop_mode_counts_for_eligible_listings"
        ].items()
    )
    report = f"""# Qualified proximity to official public-transport stops

## Scope and definitions

The checksum-verified OFT/BAV archive has a published data state of **{SOURCE_STATE_DATE}** and contains **{summary['operating_points']:,}** operating points. The official data model distinguishes passenger stops from pure operating points. This analysis therefore retains only the **{summary['passenger_stops']:,}** records with type `VP` (stop) or `VPG` (stop and loading point).

The nearest train station is selected from the **{summary['train_capable_passenger_stops']:,}** passenger stops whose official transport-mode code contains elementary code `B` (train), including multi-mode combinations. Rack railway (`E`) is a separate published mode and is not silently reclassified as train. All-stop proximity includes every mode in the official passenger-stop subset, including bus, train, tram, ship, funicular, gondola and chairlift.

Distances are EPSG:2056 Euclidean straight-line distances from each supplied resort-listing coordinate. Cluster summaries use the minimum, median and maximum across eligible supplied listing points rather than an artificial median-cluster point. Ties are resolved deterministically after sorting by official stop number.

## Coverage and descriptive reference

- eligible Swiss resort listings with both distances: **{summary['resort_listings_inside_official_swiss_scope']:,} / {summary['resort_listings']:,}**
- listings outside the complete Swiss scope and left missing: **{summary['resort_listings_outside_official_swiss_scope']:,}**
- clusters complete for every supplied listing point: **{summary['path_c_clusters_complete']:,} / {summary['path_c_clusters']:,}**
- partially covered clusters: **{summary['path_c_clusters_partial']:,}**
- apparent Path C candidates with complete context: **{summary['path_c_candidates_with_complete_context']:,} / {summary['path_c_candidates']:,}**
- median of cluster-median distance to any official passenger stop: **{summary['median_cluster_median_distance_to_public_transport_stop_km']:.2f} km**
- median of cluster-median distance to a train station: **{summary['median_cluster_median_distance_to_train_station_km']:.2f} km**
- maximum eligible listing distance to any official passenger stop: **{summary['maximum_listing_distance_to_public_transport_stop_km']:.2f} km**
- maximum eligible listing distance to a train station: **{summary['maximum_listing_distance_to_train_station_km']:.2f} km**
- nearest all-stop modes across eligible listings: {mode_counts}
- approved generic accessibility features or scores: **0**

The outside-scope listings are {outside}. The OFT source can include selected foreign operating points but is not a complete French stop universe, so these rows are not assigned to a potentially incomplete nearest point. Their shared cross-border cluster is explicitly partial.

## Interpretation limit

This is current straight-line point proximity, not a walking, driving or public-transport route. It does not measure service frequency, timetable convenience, transfers, waiting time, seasonal operation, winter closures, fare integration or accessibility from a validated valley/base arrival node. The official mode attribute describes the infrastructure for which a stop is designed and is not by itself proof of a particular service in every timetable period. A supplied resort coordinate may be on-mountain; accordingly, the nearest all-mode stop can be the resort's own cableway or chairlift and must not be interpreted automatically as external access quality. `public_transport_stop_proximity_feature_approved` therefore remains false, `accessibility_score` remains blank, and no composite ranking or causal estimate is produced.

## Outputs

- `data_processed/resort_public_transport_stop_context.csv`
- `data_processed/path_c_cluster_public_transport_stop_context.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified stop-proximity columns appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
