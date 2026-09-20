from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / name, **kwargs)


def test_raw_files_match_manifest() -> None:
    manifest = read("metadata/raw_file_manifest.csv", dtype=str)
    assert len(manifest) == 11
    for row in manifest.itertuples(index=False):
        digest = hashlib.sha256((ROOT / row.file_name).read_bytes()).hexdigest()
        assert digest == row.sha256


def test_resort_and_crosswalk_keys_are_unique() -> None:
    resorts = read("data_processed/resort_master.csv", dtype=str)
    points = read("data_processed/resort_point_municipality.csv", dtype=str)
    assert len(resorts) == 271
    assert resorts["resort_id"].is_unique
    assert points["resort_id"].is_unique
    assert set(resorts["resort_id"]) == set(points["resort_id"])
    assert set(points["relationship_type"]) == {"coordinate_container_only"}
    assert set(points["tourism_exposure_interpretation"]) == {"not_established"}


def test_existing_cluster_memberships_are_complete_and_unique() -> None:
    geojson = json.loads(
        (ROOT / "data_raw" / "stations_ski_clusters_gps_bergfex.geojson").read_text(encoding="utf-8")
    )
    lift_ids = [
        lift_id
        for feature in geojson["features"]
        for lift_id in feature["properties"]["lift_fids"]
    ]
    assert len(geojson["features"]) == 242
    assert len(lift_ids) == 1805
    assert len(set(lift_ids)) == 1805
    validation = read("reports/cluster_geometry_validation.csv")
    assert len(validation) == 271
    assert validation["assigned_is_nearest"].all()
    assert validation["distance_difference_m"].abs().max() <= 0.3


def test_hotel_panel_grain_and_values() -> None:
    hotel = read("data_processed/hotel_municipality_month.csv")
    assert len(hotel) == 31_248
    assert not hotel.duplicated(["municipality_name_source", "date"]).any()
    for variable in ["hotel_overnights", "hotel_arrivals", "domestic_overnights", "foreign_overnights"]:
        assert (hotel[variable].dropna() >= 0).all()
    observed = hotel[hotel["hotel_overnights"].notna()]
    assert observed["date"].min() == "2013-01-01"
    assert observed["date"].max() == "2026-03-01"
    assert observed["municipality_name_source"].nunique() == 186


def test_magic_evidence_is_not_silently_promoted_to_treatment() -> None:
    history = read("data_processed/magic_pass_membership_history.csv", dtype=str)
    assert len(history) == 93
    assert history["event_id"].is_unique
    assert (history["treatment_ready"].str.lower() == "false").all()
    exits = history[history["event_type"] == "base_pass_exit"]
    assert len(exits) == 1
    assert exits.iloc[0]["source_resort_name"] == "Crans-Montana"
    assert exits.iloc[0]["exit_date"] == "2020-04-30"


def test_current_map_snapshot_and_quality_outputs() -> None:
    current = read("data_processed/magic_pass_current_destinations.csv", dtype=str)
    quality = read("data_processed/resort_data_quality.csv")
    assert len(current) == 95
    assert current["official_destination_id"].is_unique
    assert len(quality) == 271
    assert quality["resort_id"].is_unique
    assert quality["data_quality_score"].between(0, 100).all()
    assert not quality["causal_ready"].any()


def test_provenance_and_dictionary_referential_integrity() -> None:
    expected_source_columns = [
        "source_id", "variable_name", "variable_description", "source_organisation",
        "source_dataset_name", "source_page_url", "direct_download_url", "api_endpoint",
        "api_parameters", "wms_layer", "geocat_metadata_url", "retrieval_method",
        "retrieval_date", "original_file_name", "local_raw_file", "processed_file",
        "geographic_level", "temporal_resolution", "temporal_start", "temporal_end",
        "unit", "license", "access_conditions", "transformation_applied", "quality_notes",
        "confidence_level", "manual_verification", "notes",
    ]
    expected_dictionary_columns = [
        "variable", "table", "description", "unit", "data_type", "geographic_level",
        "temporal_level", "source_id", "raw_or_derived", "formula", "causal_role",
        "missing_share", "notes",
    ]
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    assert list(sources.columns) == expected_source_columns
    assert list(dictionary.columns) == expected_dictionary_columns
    assert sources["source_id"].is_unique
    assert not dictionary.duplicated(["table", "variable"]).any()
    assert set(dictionary["source_id"].dropna()) <= set(sources["source_id"])


def test_checkpoint_metrics_remain_conservative() -> None:
    metrics = read("reports/feasibility_counts.csv").set_index("metric")["value"]
    assert int(metrics["candidate_linked_base_entries_with_hotel_outcome"]) == 18
    assert int(metrics["provisional_treated_municipalities_with_hotel_outcome"]) == 14
    assert int(metrics["causal_treatment_units_approved"]) == 0
    assert int(metrics["approved_usable_controls"]) == 0
