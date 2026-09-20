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


def test_hotel_capacity_panel_is_complete_at_grid_level_and_not_imputed() -> None:
    capacity = read("data_processed/hotel_capacity_municipality_month.csv")
    enriched = read("data_processed/hotel_municipality_month_enriched.csv")
    reconciliation = read("reports/hotel_capacity_reconciliation.csv")
    assert len(capacity) == len(enriched) == 31_248
    assert not capacity.duplicated(["municipality_bfs_id", "date"]).any()
    assert capacity["municipality_bfs_id"].nunique() == 186
    for variable in [
        "hotel_establishments_open",
        "hotel_rooms_available",
        "hotel_beds_available",
    ]:
        assert (capacity[variable].dropna() >= 0).all()
    assert int(capacity["complete_capacity_supply"].sum()) == 29_274
    missing = capacity["hotel_beds_available"].isna()
    assert set(capacity.loc[missing, "hotel_beds_available_source_token"]) == {"..", "..."}
    assert int(reconciliation["mismatches"].sum()) == 6


def test_slf_snow_proxy_preserves_coverage_and_representation_limits() -> None:
    month = read("data_processed/slf_snow_station_month.csv")
    winter = read("data_processed/slf_snow_station_winter.csv")
    crosswalk = read("data_processed/resort_snow_station_crosswalk.csv")
    vulnerability = read("data_processed/resort_snow_vulnerability.csv")
    destination = read("data_processed/destination_snow_month.csv")
    assert len(month) == 166 * 159
    assert len(winter) == 166 * 13
    assert not month.duplicated(["station_code", "date"]).any()
    assert not winter.duplicated(["station_code", "winter_season"]).any()
    assert len(crosswalk) == len(vulnerability) == 271
    assert crosswalk["resort_id"].is_unique
    assert crosswalk["snow_station_winter_coverage_share_2013_2025"].ge(0.80).all()
    assert set(crosswalk["snow_proxy_quality"]) == {"high", "moderate", "low"}
    assert not crosswalk["direct_slope_representation"].any()
    assert int(vulnerability["snow_climate_feature_ready"].sum()) == 211
    assert not vulnerability["causal_covariate_approved"].any()
    assert len(destination) == 11 * 159
    assert int(destination["complete_snow_proxy"].sum()) == 1_733
    assert not destination["snow_direct_slope_representation"].any()


def test_meteoswiss_weather_proxy_preserves_coverage_and_representation_limits() -> None:
    month = read("data_processed/meteoswiss_station_month.csv")
    crosswalk = read("data_processed/resort_weather_station_crosswalk.csv")
    destination = read("data_processed/destination_weather_month.csv")
    assert len(month) == 7 * 159
    assert not month.duplicated(["station_abbr", "month_date"]).any()
    assert set(month["station_abbr"]) == {"ABO", "EVO", "GRC", "INT", "MER", "MLS", "MVE"}
    assert int(month["month_weather_proxy_usable"].sum()) == 1_111
    assert int(month["precipitation_coverage_share"].lt(0.80).sum()) == 2
    assert month["temperature_mean_coverage_share"].ge(0.80).all()
    assert (month["precipitation_total_mm"].dropna() >= 0).all()
    assert len(crosswalk) == 15
    assert crosswalk["resort_id"].is_unique
    assert set(crosswalk["weather_proxy_quality"]) == {"high", "moderate"}
    assert not crosswalk["direct_slope_representation"].any()
    assert not crosswalk["weather_causal_covariate_approved"].any()
    assert len(destination) == 11 * 159
    assert int(destination["complete_weather_proxy"].sum()) == 1_744
    assert not destination["weather_direct_slope_representation"].any()
    assert not destination["weather_causal_covariate_approved"].any()


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
    for row in sources.itertuples(index=False):
        if pd.isna(row.local_raw_file) or not row.local_raw_file.startswith(
            "data_external/source_evidence/"
        ):
            continue
        raw = ROOT / row.local_raw_file
        metadata_path = raw.with_name(raw.stem + ".metadata.json")
        if metadata_path.exists():
            cached = json.loads(metadata_path.read_text(encoding="utf-8"))
            assert cached["source_id"] == row.source_id


def test_checkpoint_metrics_remain_conservative() -> None:
    metrics = read("reports/feasibility_counts.csv").set_index("metric")["value"]
    assert int(metrics["candidate_linked_base_entries_with_hotel_outcome"]) == 18
    assert int(metrics["provisional_treated_municipalities_with_hotel_outcome"]) == 14
    assert int(metrics["causal_treatment_units_approved"]) == 0
    assert int(metrics["approved_usable_controls"]) == 0
    assert int(metrics["reviewed_destination_units"]) == 14
    assert int(metrics["reviewed_destination_units_in_outcome_panel"]) == 11
    assert int(metrics["reviewed_units_with_24_pre_and_post_months_assumption"]) == 7
    assert int(metrics["reviewed_units_with_36_pre_and_post_months_assumption"]) == 6
    assert int(metrics["reviewed_units_with_fully_documented_membership_continuity"]) == 10
    assert int(metrics["panel_units_with_fully_documented_membership_continuity"]) == 8
    assert int(metrics["fully_documented_panel_units_with_24_pre_and_post_months"]) == 4
    assert int(metrics["control_municipalities_upper_bound_after_resolved_magic_links"]) == 57
    assert int(metrics["treatment_donor_pairs_screened"]) == 814
    assert int(metrics["provisional_donor_pairs_30km_36pre"]) == 438


def test_reviewed_destination_scope_is_explicit_and_conservative() -> None:
    units = read("data_processed/treatment_destination_units.csv", dtype=str)
    mappings = read("data_processed/treatment_destination_municipality.csv", dtype=str)
    crosswalk = read("data_processed/resort_municipality_crosswalk.csv", dtype=str)
    assert len(units) == 14
    assert units["destination_unit_id"].is_unique
    eligible = units["eligible_for_reviewed_outcome_panel"].str.lower().eq("true")
    assert eligible.sum() == 11
    excluded = set(units.loc[~eligible, "destination_unit_id"])
    assert excluded == {
        "gstaad_operator_domain",
        "sainte_croix_les_rasses",
        "villars_gryon_les_diablerets",
    }
    assert (units["causal_treatment_unit_approved"].str.lower() == "false").all()
    assert (mappings["municipality_weight"].astype(float) == 1.0).all()
    assert (mappings["causal_exposure_approved"].str.lower() == "false").all()
    assert len(crosswalk) == 271
    assert crosswalk["resort_id"].is_unique
    assert (crosswalk["causal_exposure_approved"].str.lower() == "false").all()


def test_reviewed_destination_panel_aggregation_and_timing() -> None:
    panel = read("data_processed/destination_month_panel.csv")
    hotel = read("data_processed/hotel_municipality_month.csv")
    capacity = read("data_processed/hotel_capacity_municipality_month.csv")
    events = read("data_processed/municipality_treatment_events.csv", dtype=str)
    assert len(panel) == 1_848
    assert panel["destination_unit_id"].nunique() == 11
    assert not panel.duplicated(["destination_unit_id", "date"]).any()
    assert not panel["causal_ready"].any()
    assert int(panel["complete_snow_proxy"].sum()) == 1_733
    assert int((panel["complete_snow_proxy"] & panel["hotel_overnights"].notna()).sum()) == 1_565
    assert not panel["snow_direct_slope_representation"].any()
    assert int(panel["complete_weather_proxy"].sum()) == 1_744
    assert int((panel["complete_weather_proxy"] & panel["hotel_overnights"].notna()).sum()) == 1_576
    assert not panel["weather_direct_slope_representation"].any()
    assert not panel["weather_causal_covariate_approved"].any()
    assert len(events) == 19
    assert (events["treatment_ready"].str.lower() == "false").all()

    date = "2019-01-01"
    source_total = hotel.loc[
        hotel["municipality_name_source"].isin(["Hasliberg", "Meiringen"])
        & hotel["date"].eq(date),
        "hotel_overnights",
    ].sum(min_count=2)
    panel_total = panel.loc[
        panel["destination_unit_id"].eq("meiringen_hasliberg")
        & panel["date"].eq(date),
        "hotel_overnights",
    ].iloc[0]
    assert panel_total == source_total

    source_beds = capacity.loc[
        capacity["municipality_name_source"].isin(["Hasliberg", "Meiringen"])
        & capacity["date"].eq(date),
        "hotel_beds_available",
    ].sum(min_count=2)
    panel_row = panel.loc[
        panel["destination_unit_id"].eq("meiringen_hasliberg")
        & panel["date"].eq(date)
    ].iloc[0]
    assert panel_row["hotel_beds_available"] == source_beds
    assert pd.isna(panel_row["hotel_bed_occupancy_rate_pct"])
    assert panel_row["occupancy_rate_aggregation_status"] == (
        "not_aggregated_across_multiple_municipalities"
    )

    crans = panel[
        panel["destination_unit_id"].eq("crans_montana")
        & panel["date"].isin(["2020-04-01", "2020-05-01"])
    ].set_index("date")
    assert bool(crans.loc["2020-04-01", "assumed_base_member"])
    assert not bool(crans.loc["2020-05-01", "assumed_base_member"])

    reichenbach = panel[
        panel["destination_unit_id"].eq("reichenbach_magic_portfolio")
        & panel["date"].isin(["2023-04-01", "2023-05-01"])
    ].set_index("date")
    assert int(reichenbach.loc["2023-04-01", "assumed_active_component_count"]) == 1
    assert int(reichenbach.loc["2023-05-01", "assumed_active_component_count"]) == 2


def test_membership_continuity_gaps_are_not_silently_filled() -> None:
    status = read("data_processed/magic_pass_membership_status_by_season.csv", dtype=str)
    audit = read("reports/membership_continuity_audit.csv", dtype=str)
    assert len(status) == 14 * 9
    assert not status.duplicated(["destination_unit_id", "season"]).any()
    assert (status["causal_treatment_status_approved"].str.lower() == "false").all()
    assert (status["membership_status"] == "unverified_active_continuity").sum() == 7
    complete = audit["continuity_fully_documented"].str.lower().eq("true")
    assert set(audit.loc[complete, "destination_unit_id"]) == {
        "crans_montana",
        "gstaad_operator_domain",
        "meiringen_hasliberg",
        "schwanden",
        "axalp", "bumbach", "les_pleiades", "reichenbach_magic_portfolio",
        "saas_fee", "sainte_croix_les_rasses",
    }
    anniviers_2019 = status[
        status["destination_unit_id"].eq("anniviers_magic_portfolio")
        & status["season"].eq("2019/2020")
    ].iloc[0]
    assert anniviers_2019["membership_status"] == "documented_active"
    assert "MAGIC_2019_APRIL" in anniviers_2019["source_ids"]
    anniviers_2020 = status[
        status["destination_unit_id"].eq("anniviers_magic_portfolio")
        & status["season"].eq("2020/2021")
    ].iloc[0]
    assert anniviers_2020["membership_status"] == "unverified_active_continuity"


def test_seasonal_roster_sources_are_cached_and_page_referenced() -> None:
    from pypdf import PdfReader

    observations = json.loads((ROOT / "metadata/magic_pass_roster_evidence.json").read_text(encoding="utf-8"))["observations"]
    sources = read("metadata/data_sources_master.csv", dtype=str).set_index("source_id")
    status = read("data_processed/magic_pass_membership_status_by_season.csv", dtype=str).set_index(["destination_unit_id", "season"])
    for observation in observations:
        source_id = observation["source_id"]
        raw = ROOT / sources.loc[source_id, "local_raw_file"]
        metadata = json.loads(raw.with_suffix(".metadata.json").read_text(encoding="utf-8"))
        assert metadata["source_id"] == source_id
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == metadata["sha256"]
        assert 1 <= int(observation["source_page"]) <= len(PdfReader(raw).pages)
        for unit in observation["active_destination_unit_ids"]:
            row = status.loc[(unit, observation["season"])]
            assert row["membership_status"] == "documented_active"
            assert source_id in row["source_ids"].split("|")


def test_control_audit_never_promotes_screened_donors() -> None:
    audit = read("reports/control_contamination_audit.csv")
    matrix = read("data_processed/treatment_control_candidate_matrix.csv")
    assert len(audit) == 74
    assert audit["municipality_bfs_id"].is_unique
    assert int(audit["known_magic_exposure_from_resolved_links"].sum()) == 17
    assert int(audit["candidate_control_upper_bound"].sum()) == 57
    assert not audit["causal_control_approved"].any()
    assert len(matrix) == 11 * 74
    assert not matrix.duplicated(
        ["destination_unit_id", "donor_municipality_bfs_id"]
    ).any()
    assert int(matrix["provisional_donor_30km_36pre"].sum()) == 438
    assert not matrix["causal_control_approved"].any()
