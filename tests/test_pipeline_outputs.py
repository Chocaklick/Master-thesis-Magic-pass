from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / name, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().eq("true")


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


def test_spass_gridded_snow_sensitivity_separates_method_and_location() -> None:
    component_winter = read("data_processed/spass_snow_component_winter.csv")
    component = read("reports/snow_gridded_component_comparison.csv")
    destination = read("data_processed/destination_snow_gridded_sensitivity.csv")
    destination_summary = read("reports/snow_gridded_destination_summary.csv")

    assert len(component_winter) == 15 * 10
    assert not component_winter.duplicated(["resort_id", "winter_start_year"]).any()
    assert set(component_winter["winter_start_year"]) == set(range(2013, 2023))
    assert as_bool(component_winter["grid_winter_complete"]).all()
    assert component_winter["grid_cell_distance_m"].max() < 1_000
    assert component_winter["station_location_grid_cell_distance_m"].max() < 1_000
    assert not as_bool(component_winter["independent_measurement_network"]).any()
    assert not as_bool(component_winter["causal_covariate_approved"]).any()

    assert len(component) == 15
    assert component["resort_id"].is_unique
    assert component["local_3x3_common_usable_winters"].eq(10).all()
    assert component["local_3x3_agreement"].value_counts().to_dict() == {
        "low": 8,
        "moderate": 6,
        "high": 1,
    }
    assert component["station_location_3x3_agreement"].value_counts().to_dict() == {
        "high": 9,
        "moderate": 6,
    }
    assert (
        component["station_location_3x3_relative_mean_absolute_depth_difference"].median()
        < component["local_3x3_relative_mean_absolute_depth_difference"].median()
    )
    assert not as_bool(component["independent_measurement_network"]).any()
    assert not as_bool(component["causal_covariate_approved"]).any()

    assert len(destination) == 11 * 10
    assert not destination.duplicated(["destination_unit_id", "winter_start_year"]).any()
    assert as_bool(destination["grid_winter_complete"]).all()
    assert as_bool(destination["station_winter_complete"]).all()
    assert len(destination_summary) == 11
    assert destination_summary["agreement"].value_counts().to_dict() == {
        "low": 6,
        "moderate": 4,
        "high": 1,
    }
    assert not as_bool(destination["causal_covariate_approved"]).any()
    assert not as_bool(destination_summary["causal_covariate_approved"]).any()


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


def test_meteoswiss_alternative_station_sensitivity_preserves_monthly_grain() -> None:
    month = read("data_processed/meteoswiss_alternative_station_month.csv")
    component = read("reports/weather_station_alternative_sensitivity.csv")
    destination = read("data_processed/destination_weather_alternative_sensitivity.csv")
    destination_summary = read("reports/weather_destination_alternative_summary.csv")

    assert len(month) == 10 * 159
    assert not month.duplicated(["station_abbr", "month_date"]).any()
    assert set(month["station_abbr"]) == {
        "CHD", "EVO", "GIH", "INT", "LAG", "MVE", "ORO", "SIO", "THU", "ZER"
    }
    assert int(month["month_weather_proxy_usable"].sum()) == 1_583
    assert len(component) == 15
    assert component["resort_id"].is_unique
    assert component["common_usable_months"].ge(156).all()
    assert component["weather_station_sensitivity_agreement"].value_counts().to_dict() == {
        "high": 10,
        "moderate": 5,
    }
    assert component["temperature_anomaly_correlation"].between(-1, 1).all()
    assert component["precipitation_anomaly_correlation"].between(-1, 1).all()
    assert not as_bool(
        component["weather_station_sensitivity_causal_covariate_approved"]
    ).any()

    assert len(destination) == 11 * 159
    assert not destination.duplicated(["destination_unit_id", "date"]).any()
    assert int(as_bool(destination["both_weather_proxies_complete"]).sum()) == 1_737
    assert len(destination_summary) == 11
    assert destination_summary["weather_station_sensitivity_agreement"].value_counts().to_dict() == {
        "high": 8,
        "moderate": 3,
    }
    assert not as_bool(
        destination["weather_station_sensitivity_causal_covariate_approved"]
    ).any()
    assert not as_bool(
        destination_summary["weather_station_sensitivity_causal_covariate_approved"]
    ).any()


def test_meteoswiss_gridded_weather_sensitivity_preserves_monthly_grain() -> None:
    component_month = read("data_processed/meteoswiss_gridded_component_month.csv")
    component = read("reports/weather_gridded_component_comparison.csv")
    destination = read("data_processed/destination_weather_gridded_sensitivity.csv")
    destination_summary = read("reports/weather_gridded_destination_summary.csv")

    assert len(component_month) == 15 * 159
    assert not component_month.duplicated(["resort_id", "date"]).any()
    assert component_month["grid_cell_id"].nunique() == 15
    assert int(as_bool(component_month["gridded_weather_month_complete"]).sum()) == 15 * 159
    assert component_month["grid_cell_distance_to_component_m"].max() < 1_000
    assert component_month["grid_normal_years_temperature"].eq(13).all()
    assert component_month["grid_normal_years_precipitation"].eq(13).all()
    assert not as_bool(
        component_month["gridded_weather_causal_covariate_approved"]
    ).any()

    assert len(component) == 15
    assert component["resort_id"].is_unique
    assert component["common_complete_months"].ge(158).all()
    assert component["gridded_weather_sensitivity_agreement"].value_counts().to_dict() == {
        "high": 12,
        "low": 2,
        "moderate": 1,
    }
    assert set(
        component.loc[
            component["gridded_weather_sensitivity_agreement"].eq("low"),
            "resort_id",
        ]
    ) == {"axalp_brienz", "meiringen_hasliberg"}
    assert component["temperature_anomaly_correlation_station_grid"].between(-1, 1).all()
    assert component["precipitation_anomaly_correlation_station_grid"].between(-1, 1).all()
    assert not as_bool(
        component["gridded_weather_causal_covariate_approved"]
    ).any()

    assert len(destination) == 11 * 159
    assert not destination.duplicated(["destination_unit_id", "date"]).any()
    assert int(as_bool(destination["both_station_and_grid_weather_complete"]).sum()) == 1_744
    assert len(destination_summary) == 11
    assert destination_summary["gridded_weather_sensitivity_agreement"].value_counts().to_dict() == {
        "high": 8,
        "low": 2,
        "moderate": 1,
    }
    assert not as_bool(
        destination["gridded_weather_causal_covariate_approved"]
    ).any()
    assert not as_bool(
        destination_summary["gridded_weather_causal_covariate_approved"]
    ).any()


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
    assert int(metrics["reviewed_units_with_fully_documented_membership_continuity"]) == 14
    assert int(metrics["panel_units_with_fully_documented_membership_continuity"]) == 11
    assert int(metrics["fully_documented_panel_units_with_24_pre_and_post_months"]) == 7
    assert int(metrics["active_unit_seasons_with_individual_winter_summer_evidence"]) == 58
    assert int(metrics["active_unit_seasons_with_documented_summer_access"]) == 36
    assert int(metrics["annual_seasons_with_individual_winter_summer_evidence"]) == 7
    assert int(metrics["control_municipalities_upper_bound_after_resolved_magic_links"]) == 56
    assert int(metrics["control_municipalities_upper_bound_after_scope_screen"]) == 52
    assert int(metrics["additional_scope_risk_municipalities_excluded"]) == 4
    assert int(metrics["treatment_donor_pairs_screened"]) == 814
    assert int(metrics["provisional_donor_pairs_30km_36pre"]) == 404
    assert int(metrics["provisional_donor_pairs_50km_36pre"]) == 366
    assert int(metrics["donor_pretrend_treatments_screened"]) == 7
    assert int(metrics["donor_pretrend_pairs_screened"]) == 315
    assert int(metrics["donor_pretrend_shortlisted_pairs"]) == 35


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
    assert (status["membership_status"] == "unverified_active_continuity").sum() == 0
    complete = audit["continuity_fully_documented"].str.lower().eq("true")
    assert complete.all()
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
    assert anniviers_2020["membership_status"] == "documented_active"
    assert "MAGIC_2020_MAP" in anniviers_2020["source_ids"]


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
        if raw.suffix.lower() == ".pdf":
            assert 1 <= int(observation["source_page"]) <= len(PdfReader(raw).pages)
        else:
            from PIL import Image

            assert observation["source_page"] == "1"
            with Image.open(raw) as image:
                image.verify()
        for unit in observation["active_destination_unit_ids"]:
            row = status.loc[(unit, observation["season"])]
            assert row["membership_status"] == "documented_active"
            assert source_id in row["source_ids"].split("|")


def test_annual_winter_summer_symbols_are_page_referenced() -> None:
    from pypdf import PdfReader

    observations = json.loads(
        (ROOT / "metadata/magic_pass_season_offering_evidence.json").read_text(
            encoding="utf-8"
        )
    )["observations"]
    sources = read("metadata/data_sources_master.csv", dtype=str).set_index("source_id")
    status = read(
        "data_processed/magic_pass_membership_status_by_season.csv", dtype=str
    ).set_index(["destination_unit_id", "season"])
    reviewed = 0
    summer = 0
    for observation in observations:
        source_id = observation["source_id"]
        raw = ROOT / sources.loc[source_id, "local_raw_file"]
        metadata = json.loads(
            raw.with_suffix(".metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["source_id"] == source_id
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == metadata["sha256"]
        if raw.suffix.lower() == ".pdf":
            assert 1 <= int(observation["source_page"]) <= len(PdfReader(raw).pages)
        else:
            from PIL import Image

            assert observation["source_page"] == "1"
            with Image.open(raw) as image:
                image.verify()
        for offering in observation["destination_offerings"]:
            row = status.loc[
                (offering["destination_unit_id"], observation["season"])
            ]
            reviewed += 1
            has_summer = bool(offering["summer_winter_labels"])
            summer += int(has_summer)
            assert row["membership_status"] == "documented_active"
            assert row["offering_source_id"] == source_id
            assert row["offering_source_page"] == observation["source_page"]
            assert row["summer_access_documented"].lower() == str(has_summer).lower()
            actual_summer_labels = row["published_summer_winter_labels"]
            actual_winter_labels = row["published_winter_only_labels"]
            assert (
                "" if pd.isna(actual_summer_labels) else actual_summer_labels
            ) == "|".join(
                offering["summer_winter_labels"]
            )
            assert (
                "" if pd.isna(actual_winter_labels) else actual_winter_labels
            ) == "|".join(
                offering["winter_only_labels"]
            )
    assert reviewed == 58
    assert summer == 36


def test_unmatched_entry_scope_review_is_complete_and_noncausal() -> None:
    review = read("reports/unmatched_magic_entry_review.csv", dtype=str)
    relations = read("data_processed/magic_pass_scope_relations.csv", dtype=str)
    assert len(review) == 26
    assert review["event_id"].is_unique
    assert review["review_class"].value_counts().to_dict() == {
        "foreign_outside_swiss_listing_universe": 10,
        "component_of_composite_listing": 8,
        "partial_or_overlapping_scope": 3,
        "documented_destination_missing_from_directory": 2,
        "documented_historical_destination_missing_from_directory": 1,
        "documented_distinct_neighbouring_destination_missing_from_directory": 1,
        "resolved_overlapping_directory_scope": 1,
    }
    assert len(relations) == 14
    assert relations["related_resort_id"].nunique() == 9
    assert (review["identity_equivalence_approved"].str.lower() == "false").all()
    assert (review["causal_mapping_approved"].str.lower() == "false").all()
    assert (relations["identity_equivalence_approved"].str.lower() == "false").all()
    assert (relations["causal_mapping_approved"].str.lower() == "false").all()
    beatenberg = relations[relations["source_resort_name"].eq("Beatenberg")]
    assert beatenberg["related_resort_id"].tolist() == ["beatenberg_niederhorn"]
    gurnigelbad = relations[relations["source_resort_name"].eq("Gurnigelbad")]
    assert gurnigelbad["related_resort_id"].tolist() == ["gantrisch_gurnigel"]
    diablerets = relations[relations["source_resort_name"].eq("Les Diablerets")]
    assert diablerets["related_resort_id"].tolist() == [
        "les_diablerets_glacier_3000",
        "villars_gryon_villars_gryon_les_diablerets",
    ]
    assert "glacier_3000_les_diablerets" not in set(
        diablerets["related_resort_id"]
    )
    wilerallmi = relations[relations["source_resort_name"].eq("Wilerallmi")]
    assert wilerallmi["related_resort_id"].tolist() == [
        "schwanden_sigriswil_thunersee"
    ]


def test_control_audit_never_promotes_screened_donors() -> None:
    audit = read("reports/control_contamination_audit.csv")
    matrix = read("data_processed/treatment_control_candidate_matrix.csv")
    assert len(audit) == 74
    assert audit["municipality_bfs_id"].is_unique
    assert int(audit["known_magic_exposure_from_resolved_links"].sum()) == 18
    assert int(audit["candidate_control_upper_bound"].sum()) == 52
    assert int(audit["additional_scope_exclusion"].sum()) == 4
    assert not audit["causal_control_approved"].any()
    assert len(matrix) == 11 * 74
    assert not matrix.duplicated(
        ["destination_unit_id", "donor_municipality_bfs_id"]
    ).any()
    assert int(matrix["provisional_donor_30km_36pre"].sum()) == 404
    assert int(matrix["provisional_donor_50km_36pre"].sum()) == 366
    assert not matrix["causal_control_approved"].any()

    current = read("data_processed/magic_pass_current_destinations.csv", dtype=str)
    sattel = current[current["official_destination_name"].eq("Sattel-Hochstuckli")]
    assert sattel["candidate_resort_id"].tolist() == [
        "hochstuckli_sattel_hochstuckli"
    ]


def test_donor_pretrend_screen_is_descriptive_and_complete() -> None:
    pairs = read("data_processed/donor_pretrend_comparability.csv")
    shortlist = read("reports/donor_pretrend_shortlist.csv")
    assert len(pairs) == 315
    assert pairs["destination_unit_id"].nunique() == 7
    assert pairs["paired_pre_outcome_months"].ge(30).all()
    assert pairs["pretrend_screen_usable"].all()
    assert not pairs["causal_control_approved"].any()
    assert len(shortlist) == 35
    assert shortlist.groupby("destination_unit_id").size().eq(5).all()
    assert shortlist["comparability_rank"].between(1, 5).all()
    assert shortlist["descriptive_comparability_score"].notna().all()


def test_temporal_controls_cover_panel_without_claiming_policy_precision() -> None:
    temporal = read("data_processed/temporal_controls_month.csv")
    panel = read("data_processed/destination_month_panel.csv")
    assert len(temporal) == 168
    assert temporal["date"].is_unique
    assert int(as_bool(temporal["covid_sensitivity_month"]).sum()) == 26
    assert int(as_bool(temporal["easter_month"]).sum()) == 14
    assert (
        as_bool(temporal["winter_month"]) ^ as_bool(temporal["summer_month"])
    ).all()
    assert panel["temporal_control_source_id"].eq(
        "DERIVED_TEMPORAL_CONTROLS"
    ).all()
    assert int(as_bool(panel["covid_sensitivity_month"]).sum()) == 286


def test_snow_alternative_station_sensitivity_remains_noncausal() -> None:
    sensitivity = read(
        "data_processed/resort_snow_alternative_station_sensitivity.csv"
    )
    assert len(sensitivity) == 15
    assert sensitivity["resort_id"].is_unique
    assert sensitivity["common_usable_winters"].ge(8).all()
    assert sensitivity["selected_station_code"].ne(
        sensitivity["alternative_station_code"]
    ).all()
    assert sensitivity["alternative_station_agreement"].value_counts().to_dict() == {
        "high": 6,
        "moderate": 5,
        "low": 4,
    }
    assert not as_bool(sensitivity["direct_slope_representation"]).any()
    assert not as_bool(sensitivity["causal_covariate_approved"]).any()


def test_donor_network_spillover_audit_is_network_wide_and_noncausal() -> None:
    audit = read("reports/donor_network_spillover_audit.csv")
    pairs = read("data_processed/donor_shortlist_network_audit.csv")
    assert len(audit) == 52
    assert audit["municipality_bfs_id"].is_unique
    assert int(audit["minimum_distance_to_resolved_magic_km"].le(20).sum()) == 21
    assert int(audit["minimum_distance_to_resolved_magic_km"].le(30).sum()) == 23
    assert int(audit["minimum_distance_to_resolved_magic_km"].le(50).sum()) == 32
    assert int(as_bool(audit["same_lift_cluster_as_resolved_magic"]).sum()) == 6
    assert not as_bool(audit["causal_control_approved"]).any()
    assert len(pairs) == 35
    assert int(pairs["minimum_distance_to_resolved_magic_km"].le(20).sum()) == 14
    assert int(pairs["minimum_distance_to_resolved_magic_km"].le(30).sum()) == 15
    assert int(pairs["minimum_distance_to_resolved_magic_km"].le(50).sum()) == 28
    assert not as_bool(pairs["causal_control_approved"]).any()


def test_donor_external_shock_audit_exhausts_remote_shortlist_without_approving_controls() -> None:
    evidence = read("reports/donor_external_shock_evidence.csv")
    final = read("data_processed/donor_shortlist_final_audit.csv")
    assert len(evidence) == 7
    assert not evidence.duplicated(
        ["destination_unit_id", "donor_municipality_bfs_id", "analysis_anchor"]
    ).any()
    assert evidence["review_source_ids"].notna().all()
    assert int(
        evidence["final_manual_review_decision"]
        .eq("exclude_contemporaneous_local_tourism_shock")
        .sum()
    ) == 7
    assert as_bool(evidence["historical_magic_roster_absence_documented"]).all()
    assert as_bool(evidence["accessibility_review_completed_or_moot"]).all()
    assert evidence["magic_roster_source_id"].isin(
        ["MAGIC_2017", "MAGIC_2018", "MAGIC_2019_APRIL", "MAGIC_2023"]
    ).all()
    assert len(final) == 35
    assert not as_bool(final["remaining_deep_audit_candidate"]).any()
    assert not as_bool(final["causal_control_approved"]).any()


def test_same_destination_distance_gradient_preserves_scope_and_uncertainty() -> None:
    distance = read("data_processed/treatment_municipality_distance_exposure.csv")
    diagnostic = read("data_processed/treatment_distance_gradient_diagnostic.csv")
    rings = read("reports/treatment_distance_ring_summary.csv")
    contrasts = read("reports/treatment_distance_near_far_contrast.csv")
    assert len(distance) == 11 * 186
    assert distance["destination_unit_id"].nunique() == 11
    assert distance["municipality_bfs_id"].nunique() == 186
    assert distance["boundary_bfs_id_2026"].nunique() == 185
    assert not distance.duplicated(
        ["destination_unit_id", "municipality_bfs_id"]
    ).any()
    moutier_bridge = distance[distance["municipality_bfs_id"].eq(700)]
    assert len(moutier_bridge) == 11
    assert moutier_bridge["boundary_bfs_id_2026"].eq(6831).all()
    assert not as_bool(distance["causal_exposure_approved"]).any()
    assert len(diagnostic) == 7 * 186
    assert diagnostic["destination_unit_id"].nunique() == 7
    assert int(as_bool(diagnostic["distance_gradient_usable"]).sum()) == 1246
    assert not as_bool(diagnostic["causal_effect_estimate"]).any()
    assert len(rings) == 35
    assert not as_bool(rings["causal_effect_estimate"]).any()
    assert len(contrasts) == 7
    assert int(contrasts["descriptive_near_minus_far_log_change"].gt(0).sum()) == 6
    assert not as_bool(contrasts["causal_effect_estimate"]).any()


def test_path_c_feature_matrix_uses_clusters_and_conservative_membership_status() -> None:
    features = read("data_processed/path_c_resort_cluster_features.csv")
    assert len(features) == 162
    assert features["cluster_id"].is_unique
    assert int(as_bool(features["structural_feature_complete"]).sum()) == 156
    assert int(as_bool(features["resolved_current_magic_member"]).sum()) == 51
    candidates = features[as_bool(features["candidate_for_path_c"])]
    assert len(candidates) == 104
    assert candidates["magic_status"].eq("no_resolved_magic_link").all()
    assert as_bool(candidates["has_resolved_swiss_point"]).all()
    assert as_bool(candidates["structural_feature_complete"]).all()
    assert not as_bool(candidates["resolved_current_magic_member"]).any()
    assert not as_bool(candidates["historical_magic_link"]).any()
    assert not as_bool(candidates["precautionary_scope_relation"]).any()
    assert features["feature_temporal_status"].eq(
        "undated_cross_sectional_snapshot_not_pre_treatment"
    ).all()


def test_path_c_segmentation_is_stable_and_not_an_effect_model() -> None:
    diagnostics = read("reports/path_c_segmentation_diagnostics.csv")
    segments = read("data_processed/path_c_cluster_segments.csv")
    assert diagnostics["k"].tolist() == list(range(2, 9))
    selected = diagnostics[as_bool(diagnostics["selected"])]
    assert len(selected) == 1
    assert int(selected.iloc[0]["k"]) == 2
    assert float(selected.iloc[0]["silhouette"]) > 0.5
    assert float(selected.iloc[0]["bootstrap_ari_median"]) >= 0.75
    assert int(selected.iloc[0]["minimum_cluster_size"]) >= 5
    assigned = segments[as_bool(segments["segmentation_eligible"])]
    assert len(assigned) == 156
    assert assigned["segment_id"].value_counts().sort_index().to_dict() == {
        "SEGMENT_01": 83,
        "SEGMENT_02": 73,
    }
    assert assigned["segmentation_interpretation"].eq(
        "current_structural_segment_not_treatment_effect_group"
    ).all()


def test_path_c_analogues_preserve_ood_and_blank_uplift_fields() -> None:
    analogues = read("data_processed/path_c_candidate_analogues.csv")
    treated = read("data_processed/path_c_reviewed_treated_reference.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")
    features = read("data_processed/path_c_resort_cluster_features.csv")
    assert len(analogues) == 104
    assert analogues["cluster_id"].is_unique
    assert len(treated) == 8
    assert not as_bool(treated["causal_interpretation_approved"]).any()
    assert analogues["reviewed_treated_ood_flag"].value_counts().to_dict() == {
        "good_support": 74,
        "strong_extrapolation": 25,
        "moderate_extrapolation": 5,
    }
    assert analogues["predicted_uplift_pct"].isna().all()
    assert analogues["uplift_lower_pct"].isna().all()
    assert analogues["uplift_upper_pct"].isna().all()
    assert analogues["composite_opportunity_need_score"].isna().all()
    assert not as_bool(analogues["causal_interpretation_approved"]).any()
    assert as_bool(analogues["two_dimension_coordinates_available"]).all()
    member_clusters = set(
        features.loc[
            as_bool(features["resolved_current_magic_member"]), "cluster_id"
        ]
    )
    for rank in range(1, 4):
        assert set(analogues[f"closest_magic_analogue_{rank}_cluster_id"]).issubset(
            member_clusters
        )
        assert set(
            analogues[f"closest_reviewed_treated_analogue_{rank}_id"]
        ).issubset(set(treated["destination_unit_id"]))
    assert len(decision) == 162
    assert decision["cluster_id"].is_unique
    assert int(as_bool(decision["candidate_for_path_c"]).sum()) == 104
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()


def test_path_c_aggregation_sensitivity_is_explicit_and_noncausal() -> None:
    detail = read("data_processed/path_c_candidate_analogue_sensitivity.csv")
    comparison = read("reports/path_c_aggregation_sensitivity.csv")
    diagnostics = read("reports/path_c_aggregation_sensitivity_k_diagnostics.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(detail) == 104 * 3
    assert not detail.duplicated(["cluster_id", "aggregation_rule"]).any()
    assert set(detail["aggregation_rule"]) == {"median", "min", "max"}
    assert not as_bool(detail["causal_interpretation_approved"]).any()

    assert len(comparison) == 3
    assert comparison["selected_k"].eq(2).all()
    by_rule = comparison.set_index("aggregation_rule")
    assert abs(float(by_rule.loc["min", "segment_assignment_ari_vs_median"]) - 0.8274623639) < 1e-9
    assert abs(float(by_rule.loc["max", "segment_assignment_ari_vs_median"]) - 0.7141397589) < 1e-9
    assert not as_bool(comparison["causal_interpretation_approved"]).any()

    selected = diagnostics[as_bool(diagnostics["selected"])]
    assert selected.groupby("aggregation_rule").size().eq(1).all()
    assert selected.set_index("aggregation_rule")["k"].eq(2).all()

    candidates = decision[as_bool(decision["candidate_for_path_c"])]
    assert len(candidates) == 104
    assert candidates["aggregation_sensitivity_status"].notna().all()
    assert int(
        candidates["aggregation_sensitivity_status"]
        .eq("stable_across_min_median_max")
        .sum()
    ) == 11
    assert int(as_bool(candidates["aggregation_reviewed_treated_top1_stable"]).sum()) == 71
    assert int(as_bool(candidates["aggregation_reviewed_treated_ood_stable"]).sum()) == 60
    assert candidates["aggregation_signal_range_pct_points"].ge(0).all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()


def test_tourism_context_uses_complete_official_year_without_claiming_catchment() -> None:
    municipality = read("data_processed/municipality_tourism_context_2025.csv")
    cluster = read("data_processed/path_c_cluster_tourism_context.csv")
    destination = read(
        "data_processed/reviewed_destination_tourism_context_2025.csv"
    )
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(municipality) == 2_115
    assert municipality["municipality_bfs_id"].is_unique
    assert municipality["population_reference_year"].eq(2025).all()
    assert municipality["resident_population"].gt(0).all()
    complete = as_bool(municipality["complete_hotel_reference_year"])
    assert int(complete.sum()) == 185
    assert municipality.loc[complete, "overnights_per_resident"].notna().all()
    assert municipality.loc[complete, "hotel_beds_per_1000_residents"].notna().all()
    assert municipality.loc[~complete, "overnights_per_resident"].isna().all()
    assert municipality.loc[~complete, "hotel_beds_per_1000_residents"].isna().all()
    moutier_2025 = municipality[municipality["municipality_bfs_id"].eq(700)].iloc[0]
    assert moutier_2025["municipality_name_statpop"] == "Moutier"
    assert bool(moutier_2025["complete_hotel_reference_year"])
    assert 6831 not in set(municipality["municipality_bfs_id"])
    assert not as_bool(municipality["tourism_dependence_feature_approved"]).any()
    assert municipality["tourism_context_interpretation"].eq(
        "point_container_context_not_destination_catchment"
    ).all()

    assert len(cluster) == 162
    assert cluster["cluster_id"].is_unique
    assert int(as_bool(cluster["all_point_containers_have_complete_hotel_year"]).sum()) == 52
    candidates = cluster[as_bool(cluster["candidate_for_path_c"])]
    assert len(candidates) == 104
    assert int(as_bool(candidates["all_point_containers_have_complete_hotel_year"]).sum()) == 39
    assert not as_bool(cluster["tourism_dependence_feature_approved"]).any()
    assert cluster["tourism_exposure_interpretation"].eq(
        "point_container_context_not_destination_catchment"
    ).all()

    assert len(destination) == 11
    assert destination["destination_unit_id"].is_unique
    assert int(destination["outcome_scope_municipality_count"].sum()) == 12
    assert destination["outcome_scope_kind"].value_counts().to_dict() == {
        "core_municipality_proxy": 7,
        "complete_observed_municipal_scope": 4,
    }
    assert as_bool(
        destination["all_outcome_scope_municipalities_have_population"]
    ).all()
    assert as_bool(
        destination["all_outcome_scope_municipalities_have_complete_hotel_year"]
    ).all()
    assert destination["outcome_scope_overnights_per_resident"].notna().all()
    assert destination[
        "outcome_scope_hotel_beds_per_1000_residents"
    ].notna().all()
    meiringen = destination.set_index("destination_unit_id").loc[
        "meiringen_hasliberg"
    ]
    assert int(meiringen["outcome_scope_municipality_count"]) == 2
    assert str(meiringen["outcome_scope_municipality_bfs_ids"]) == "783|785"
    assert not as_bool(destination["tourism_catchment_validated"]).any()
    assert not as_bool(destination["pre_treatment_feature_approved"]).any()
    assert not as_bool(destination["tourism_dependence_feature_approved"]).any()
    assert not as_bool(destination["causal_covariate_approved"]).any()
    assert destination["destination_tourism_context_interpretation"].eq(
        "reviewed_outcome_municipality_scope_current_context_not_validated_"
        "tourism_catchment_or_pre_treatment_feature"
    ).all()

    assert len(decision) == 162
    assert decision["tourism_dependence"].isna().all()
    assert int(
        as_bool(decision["all_point_containers_have_complete_hotel_year"]).sum()
    ) == 52
    assert not as_bool(decision["tourism_dependence_feature_approved"]).any()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()


def test_accessibility_context_preserves_population_and_stays_unapproved() -> None:
    municipality = read("data_processed/municipality_population_geometry_2026.csv")
    cluster = read("data_processed/path_c_cluster_accessibility_context.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(municipality) == 2_110
    assert municipality["boundary_bfs_id_2026"].is_unique
    assert municipality["population_reference_year"].eq(2025).all()
    assert municipality["boundary_reference_date"].eq("2026-01-01").all()
    assert int(municipality["resident_population_2025_on_2026_boundary"].sum()) == 9_127_125
    assert municipality["resident_population_2025_on_2026_boundary"].gt(0).all()
    expected_constituents = {
        6831: (1, "700"),
        2056: (2, "2016|2027"),
        2262: (2, "2262|2278"),
        2525: (3, "2520|2525|2529"),
        4095: (2, "4095|4122"),
    }
    indexed = municipality.set_index("boundary_bfs_id_2026")
    for boundary_id, (count, source_ids) in expected_constituents.items():
        assert int(indexed.loc[boundary_id, "population_constituent_count_2025"]) == count
        assert indexed.loc[boundary_id, "population_constituent_bfs_ids_2025"] == source_ids

    assert len(cluster) == 162
    assert cluster["cluster_id"].is_unique
    assert int(as_bool(cluster["candidate_for_path_c"]).sum()) == 104
    assert cluster["accessibility_context_status"].eq(
        "complete_swiss_straight_line_population_context"
    ).all()
    assert not as_bool(cluster["accessibility_feature_approved"]).any()
    assert cluster["accessibility_interpretation"].eq(
        "swiss_straight_line_population_context_not_travel_time_or_destination_catchment"
    ).all()
    assert int(as_bool(cluster["cluster_inside_swiss_country_boundary_2026"]).sum()) == 160
    assert set(
        cluster.loc[
            ~as_bool(cluster["cluster_inside_swiss_country_boundary_2026"]),
            "cluster_id",
        ]
    ) == {"SKI_CLUSTER_001", "SKI_CLUSTER_200"}
    assert cluster["distance_to_swiss_country_boundary_km"].ge(0).all()
    assert (
        cluster["distance_to_nearest_municipality_population_ge_20000_km"]
        <= cluster["distance_to_nearest_municipality_population_ge_50000_km"] + 1e-9
    ).all()
    assert (
        cluster["distance_to_nearest_municipality_population_ge_50000_km"]
        <= cluster["distance_to_nearest_municipality_population_ge_100000_km"] + 1e-9
    ).all()
    radius_columns = [
        "resident_population_within_30km_straight_line",
        "resident_population_within_60km_straight_line",
        "resident_population_within_90km_straight_line",
        "resident_population_within_120km_straight_line",
    ]
    assert not (cluster[radius_columns].diff(axis=1).iloc[:, 1:] < 0).any().any()
    expected_border_risk = {30: 112, 60: 158, 90: 162, 120: 162}
    for radius, expected_count in expected_border_risk.items():
        risk = as_bool(
            cluster[
                f"swiss_only_population_within_{radius}km_cross_border_truncation_risk"
            ]
        )
        assert int(risk.sum()) == expected_count
        assert risk.equals(
            (~as_bool(cluster["cluster_inside_swiss_country_boundary_2026"]))
            | cluster["distance_to_swiss_country_boundary_km"].lt(radius)
        )

    assert len(decision) == 162
    assert decision["accessibility_score"].isna().all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()
    assert not as_bool(decision["accessibility_feature_approved"]).any()


def test_cross_border_population_context_is_complete_separate_and_unapproved() -> None:
    grid = read("data_processed/eurostat_population_grid_2021_swiss_region.csv")
    cluster = read("data_processed/path_c_cluster_cross_border_population_context.csv")
    candidates = read("reports/cross_border_population_candidate_summary.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")
    summary = json.loads(
        (ROOT / "reports/cross_border_population_context_summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(grid) == 181_598
    assert grid["grid_cell_id"].is_unique
    assert grid["population_reference_year"].eq(2021).all()
    assert grid["grid_crs"].eq("EPSG:3035").all()
    assert grid["total_population_2021"].ge(0).all()
    assert grid["country_scope_category"].value_counts().to_dict() == {
        "foreign_only": 139_217,
        "switzerland_only": 40_171,
        "switzerland_foreign_mixed": 2_210,
    }

    assert len(cluster) == 162
    assert cluster["cluster_id"].is_unique
    assert int(as_bool(cluster["candidate_for_path_c"]).sum()) == 104
    assert cluster["cross_border_population_context_status"].eq(
        "complete_observed_total_population_grid_cells"
    ).all()
    assert cluster["cross_border_population_interpretation"].eq(
        "eurostat_2021_one_km_population_context_not_travel_time_or_destination_catchment"
    ).all()
    assert not as_bool(cluster["cross_border_population_feature_approved"]).any()
    assert as_bool(cluster["unallocated_population_records_excluded"]).all()
    assert cluster.filter(like="total_population_unavailable_cells").eq(0).all().all()

    for radius in [30, 60, 90, 120]:
        total = cluster[f"eurostat_population_2021_within_{radius}km_cell_centroid"]
        components = (
            cluster[
                f"eurostat_switzerland_only_population_2021_within_{radius}km_cell_centroid"
            ]
            + cluster[
                f"eurostat_foreign_only_population_2021_within_{radius}km_cell_centroid"
            ]
            + cluster[
                f"eurostat_ch_foreign_mixed_population_2021_within_{radius}km_cell_centroid"
            ]
        )
        assert total.equals(components)
    total_columns = [
        f"eurostat_population_2021_within_{radius}km_cell_centroid"
        for radius in [30, 60, 90, 120]
    ]
    assert not (cluster[total_columns].diff(axis=1).iloc[:, 1:] < 0).any().any()
    assert int(
        cluster["eurostat_foreign_only_population_2021_within_30km_cell_centroid"]
        .gt(0)
        .sum()
    ) == 99
    assert cluster[
        "eurostat_foreign_only_population_2021_within_120km_cell_centroid"
    ].gt(0).all()

    assert len(candidates) == 104
    shares = candidates[
        "eurostat_foreign_only_share_of_observed_population_within_120km"
    ]
    assert shares.is_monotonic_decreasing
    assert summary["source_rows"] == 4_595_932
    assert summary["unallocated_rows_excluded"] == 13
    assert summary["observed_unallocated_population_excluded"] == 434_787
    assert summary["cross_border_population_features_approved"] == 0

    assert len(decision) == 162
    assert decision["accessibility_score"].isna().all()
    assert not as_bool(decision["cross_border_population_feature_approved"]).any()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()


def test_transport_accessibility_uses_npvm_zones_and_exposes_proxies() -> None:
    listing = read("data_processed/resort_transport_accessibility_context.csv")
    cluster = read("data_processed/path_c_cluster_transport_accessibility_context.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(listing) == 271
    assert listing["resort_id"].is_unique
    assert listing["npvm_model_reference_date"].eq("2025-06-30").all()
    status_counts = listing["npvm_zone_assignment_status"].value_counts().to_dict()
    assert status_counts == {
        "exact_point_in_npvm_traffic_zone": 170,
        "nearest_npvm_zone_intersecting_current_point_municipality": 98,
        "outside_swiss_current_municipality_and_npvm_coverage": 3,
    }
    usable = as_bool(listing["travel_time_values_complete"])
    assert int(usable.sum()) == 268
    assert set(listing.loc[~usable, "resort_id"]) == {
        "avoriaz_1800_portes_du_soleil",
        "chapelle_abondance_la_chapelle_d_abondance_portes_du_soleil",
        "chatel_portes_du_soleil",
    }
    travel_columns = [
        "road_major_center_travel_time_minutes",
        "public_transport_major_center_travel_time_minutes",
        "road_agglomeration_travel_time_minutes",
        "public_transport_agglomeration_travel_time_minutes",
    ]
    assert listing.loc[usable, travel_columns].notna().all().all()
    assert listing.loc[usable, travel_columns].ge(0).all().all()
    assert listing.loc[~usable, travel_columns].isna().all().all()
    exact = listing["npvm_zone_assignment_status"].eq(
        "exact_point_in_npvm_traffic_zone"
    )
    proxied = listing["npvm_zone_assignment_status"].eq(
        "nearest_npvm_zone_intersecting_current_point_municipality"
    )
    assert listing.loc[exact, "npvm_zone_assignment_distance_km"].eq(0).all()
    assert listing.loc[proxied, "npvm_zone_assignment_distance_km"].gt(0).all()
    assert listing.loc[proxied, "npvm_zone_assignment_distance_km"].max() < 4
    assert listing.loc[usable, "road_major_center_target_six_major_centres_flag"].eq(
        True
    ).all()
    assert listing.loc[
        usable, "public_transport_major_center_target_six_major_centres_flag"
    ].eq(True).all()
    assert not as_bool(listing["transport_accessibility_feature_approved"]).any()

    assert len(cluster) == 162
    assert cluster["cluster_id"].is_unique
    assert int(cluster["cluster_listing_count"].sum()) == 271
    assert int(cluster["cluster_listings_assigned_to_npvm_zone"].sum()) == 268
    assert int(
        cluster["cluster_listings_assigned_by_current_municipality_zone_proxy"].sum()
    ) == 98
    assert cluster["cluster_transport_context_status"].value_counts().to_dict() == {
        "complete_all_listing_points_exact": 89,
        "complete_with_nearest_same_municipality_zone_proxy": 72,
        "partial_foreign_or_unresolved_listing_points": 1,
    }
    partial = cluster[
        cluster["cluster_transport_context_status"].eq(
            "partial_foreign_or_unresolved_listing_points"
        )
    ]
    assert partial["cluster_id"].tolist() == ["SKI_CLUSTER_001"]
    candidates = cluster[as_bool(cluster["candidate_for_path_c"])]
    assert len(candidates) == 104
    assert candidates["road_major_center_travel_time_median_minutes"].notna().all()
    assert candidates[
        "public_transport_major_center_travel_time_median_minutes"
    ].notna().all()
    for prefix in [
        "road_major_center_travel_time",
        "public_transport_major_center_travel_time",
        "road_agglomeration_travel_time",
        "public_transport_agglomeration_travel_time",
    ]:
        assert (
            cluster[f"{prefix}_minimum_minutes"]
            <= cluster[f"{prefix}_median_minutes"]
        ).all()
        assert (
            cluster[f"{prefix}_median_minutes"]
            <= cluster[f"{prefix}_maximum_minutes"]
        ).all()
    assert not as_bool(cluster["transport_accessibility_feature_approved"]).any()
    assert cluster["transport_accessibility_interpretation"].eq(
        "npvm_2025_modelled_traffic_zone_context_not_live_routing_or_destination_catchment"
    ).all()

    assert len(decision) == 162
    assert decision["accessibility_score"].isna().all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()
    assert not as_bool(decision["transport_accessibility_feature_approved"]).any()


def test_transport_zone_proxy_audit_reconstructs_geometry_and_exposes_dependence() -> None:
    audit = read("reports/transport_zone_proxy_audit.csv")
    summary = json.loads(
        (ROOT / "reports/transport_zone_proxy_audit_summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(audit) == 98
    assert audit["resort_id"].is_unique
    assert as_bool(audit["proxy_geometry_validation_passed"]).all()
    assert as_bool(
        audit["nearest_positive_area_intersection_with_current_municipality"]
    ).all()
    assert audit["assigned_zone_municipality_overlap_area_km2"].gt(0).all()
    assert audit["stored_recomputed_absolute_difference_km"].le(1e-9).all()
    assert audit["same_municipality_constraint_extra_distance_km"].ge(-1e-9).all()
    assert audit["proxy_distance_band"].value_counts().to_dict() == {
        "gt_0_to_0_5_km": 38,
        "gt_0_5_to_1_km": 35,
        "gt_1_to_2_km": 19,
        "gt_2_km": 6,
    }
    assert not as_bool(audit["historical_npvm_zone_lineage_verified"]).any()
    assert not as_bool(audit["transport_accessibility_feature_approved"]).any()
    assert summary["proxy_clusters"] == 73
    assert summary["proxy_only_clusters"] == 50
    assert summary["mixed_exact_and_proxy_clusters"] == 23
    assert summary["candidate_clusters_using_proxy"] == 40
    assert summary["candidate_clusters_proxy_only"] == 28
    assert summary["transport_accessibility_features_approved"] == 0


def test_public_transport_stop_context_uses_only_official_passenger_stops() -> None:
    listing = read("data_processed/resort_public_transport_stop_context.csv")
    cluster = read("data_processed/path_c_cluster_public_transport_stop_context.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(listing) == 271
    assert listing["resort_id"].is_unique
    assert listing["public_transport_stop_source_state_date"].eq("2026-09-20").all()
    assert listing["public_transport_stop_stac_item_datetime"].eq(
        "2026-09-13T00:00:00Z"
    ).all()
    status_counts = listing["public_transport_stop_context_status"].value_counts().to_dict()
    assert status_counts == {
        "assigned_official_swiss_passenger_stop_scope": 268,
        "outside_official_swiss_passenger_stop_scope": 3,
    }
    usable = as_bool(listing["public_transport_stop_values_complete"])
    assert int(usable.sum()) == 268
    assert set(listing.loc[~usable, "resort_id"]) == {
        "avoriaz_1800_portes_du_soleil",
        "chapelle_abondance_la_chapelle_d_abondance_portes_du_soleil",
        "chatel_portes_du_soleil",
    }
    distance_columns = [
        "distance_to_nearest_public_transport_stop_km",
        "distance_to_nearest_train_station_km",
    ]
    assert listing.loc[usable, distance_columns].notna().all().all()
    assert listing.loc[usable, distance_columns].ge(0).all().all()
    assert listing.loc[~usable, distance_columns].isna().all().all()
    assert set(listing.loc[usable, "nearest_public_transport_stop_type_code"]) <= {
        "VP",
        "VPG",
    }
    assert set(listing.loc[usable, "nearest_train_station_type_code"]) <= {
        "VP",
        "VPG",
    }
    assert listing.loc[usable, "nearest_train_station_mode_code"].str.contains(
        "B", regex=False
    ).all()
    assert listing.loc[usable, "distance_to_nearest_public_transport_stop_km"].max() < 3.1
    assert listing.loc[usable, "distance_to_nearest_train_station_km"].max() < 24.2
    assert not as_bool(
        listing["public_transport_stop_proximity_feature_approved"]
    ).any()

    assert len(cluster) == 162
    assert cluster["cluster_id"].is_unique
    assert int(cluster["cluster_listing_count"].sum()) == 271
    assert int(cluster["cluster_listings_with_public_transport_stop_context"].sum()) == 268
    assert cluster["cluster_public_transport_stop_context_status"].value_counts().to_dict() == {
        "complete_all_listing_points_inside_swiss_scope": 161,
        "partial_listing_points_outside_swiss_scope": 1,
    }
    partial = cluster[
        cluster["cluster_public_transport_stop_context_status"].eq(
            "partial_listing_points_outside_swiss_scope"
        )
    ]
    assert partial["cluster_id"].tolist() == ["SKI_CLUSTER_001"]
    candidates = cluster[as_bool(cluster["candidate_for_path_c"])]
    assert len(candidates) == 104
    assert candidates[
        "cluster_distance_to_nearest_public_transport_stop_median_km"
    ].notna().all()
    assert candidates[
        "cluster_distance_to_nearest_train_station_median_km"
    ].notna().all()
    for prefix in ["public_transport_stop", "train_station"]:
        stem = f"cluster_distance_to_nearest_{prefix}"
        assert (cluster[f"{stem}_minimum_km"] <= cluster[f"{stem}_median_km"]).all()
        assert (cluster[f"{stem}_median_km"] <= cluster[f"{stem}_maximum_km"]).all()
    assert not as_bool(
        cluster["public_transport_stop_proximity_feature_approved"]
    ).any()
    assert cluster["public_transport_stop_proximity_interpretation"].eq(
        "official_current_stop_point_straight_line_context_not_route_service_frequency_or_validated_resort_arrival_node"
    ).all()

    assert len(decision) == 162
    assert decision["accessibility_score"].isna().all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()
    assert not as_bool(
        decision["public_transport_stop_proximity_feature_approved"]
    ).any()


def test_national_road_proximity_context_preserves_scope_and_definitions() -> None:
    listing = read("data_processed/resort_national_road_proximity_context.csv")
    cluster = read("data_processed/path_c_cluster_national_road_proximity_context.csv")
    candidates = read("reports/national_road_proximity_candidate_summary.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(listing) == 271
    assert listing["resort_id"].is_unique
    assert listing["national_road_source_reference_datetime"].eq(
        "2026-08-01T00:00:00Z"
    ).all()
    assert listing["national_road_asset_updated_datetime"].eq(
        "2026-09-01T03:32:13.046159Z"
    ).all()
    assert listing["national_road_proximity_context_status"].value_counts().to_dict() == {
        "assigned_official_swiss_national_road_scope": 268,
        "outside_official_swiss_national_road_scope": 3,
    }
    usable = as_bool(listing["national_road_proximity_values_complete"])
    assert int(usable.sum()) == 268
    assert set(listing.loc[~usable, "resort_id"]) == {
        "avoriaz_1800_portes_du_soleil",
        "chapelle_abondance_la_chapelle_d_abondance_portes_du_soleil",
        "chatel_portes_du_soleil",
    }
    distances = [
        "distance_to_nearest_national_road_main_km",
        "distance_to_nearest_national_road_network_km",
    ]
    assert listing.loc[usable, distances].notna().all().all()
    assert listing.loc[usable, distances].ge(0).all().all()
    assert listing.loc[~usable, distances].isna().all().all()
    assert (
        listing.loc[usable, "distance_to_nearest_national_road_network_km"]
        <= listing.loc[usable, "distance_to_nearest_national_road_main_km"] + 1e-12
    ).all()
    assert listing.loc[usable, "nearest_national_road_main_axis_layer"].eq(
        "Stammachsen"
    ).all()
    assert listing.loc[
        usable, "nearest_national_road_network_axis_layer"
    ].value_counts().to_dict() == {
        "Stammachsen": 172,
        "Anschlussachse": 57,
        "Rampenachsen": 35,
        "Zubringerachsen": 4,
    }
    assert not as_bool(
        listing["national_road_motorway_classification_available"]
    ).any()
    assert not as_bool(listing["national_road_proximity_feature_approved"]).any()

    assert len(cluster) == 162
    assert cluster["cluster_id"].is_unique
    assert int(cluster["cluster_listing_count"].sum()) == 271
    assert int(cluster["cluster_listings_with_national_road_context"].sum()) == 268
    assert cluster["cluster_national_road_proximity_context_status"].value_counts().to_dict() == {
        "complete_all_listing_points_inside_swiss_scope": 161,
        "partial_listing_points_outside_swiss_scope": 1,
    }
    partial = cluster[
        cluster["cluster_national_road_proximity_context_status"].eq(
            "partial_listing_points_outside_swiss_scope"
        )
    ]
    assert partial["cluster_id"].tolist() == ["SKI_CLUSTER_001"]
    candidate_rows = cluster[as_bool(cluster["candidate_for_path_c"])]
    assert len(candidate_rows) == 104
    assert int(
        candidate_rows["cluster_national_road_proximity_context_status"]
        .eq("complete_all_listing_points_inside_swiss_scope")
        .sum()
    ) == 103
    for prefix in ["national_road_main", "national_road_network"]:
        stem = f"cluster_distance_to_nearest_{prefix}"
        assert (cluster[f"{stem}_minimum_km"] <= cluster[f"{stem}_median_km"]).all()
        assert (cluster[f"{stem}_median_km"] <= cluster[f"{stem}_maximum_km"]).all()
    assert cluster["national_road_proximity_interpretation"].eq(
        "official_current_swiss_national_road_axis_straight_line_context_not_motorway_classification_route_or_historical_accessibility"
    ).all()
    assert not as_bool(cluster["national_road_proximity_feature_approved"]).any()

    assert len(candidates) == 104
    assert candidates["cluster_id"].is_unique
    assert len(decision) == 162
    assert decision["accessibility_score"].isna().all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()
    assert not as_bool(decision["national_road_proximity_feature_approved"]).any()


def test_competing_pass_context_preserves_roster_scope_and_mixed_clusters() -> None:
    roster = read("config/competing_pass_roster_2026_27.csv")
    listing = read("data_processed/resort_competing_pass_context.csv")
    cluster = read("data_processed/path_c_cluster_competing_pass_context.csv")
    candidates = read("reports/competing_pass_candidate_summary.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(roster) == 43
    assert not roster[["competing_pass_id", "official_area_label"]].duplicated().any()
    assert roster["competing_pass_id"].value_counts().to_dict() == {
        "meilenweiss": 17,
        "schneepass_zentralschweiz": 15,
        "alpspass": 11,
    }
    assert roster["benefit_tier"].value_counts().to_dict() == {
        "included_region_current_annual_pass": 17,
        "included_region_winter_season_pass": 15,
        "three_free_ski_days_partner_region": 7,
        "unlimited_core_region": 4,
    }

    assert len(listing) == 271
    assert listing["resort_id"].is_unique
    assert int(as_bool(listing["competing_pass_linked"]).sum()) == 55
    assert int(listing["competing_pass_link_count"].sum()) > 55
    assert not as_bool(listing["competing_pass_market_absence_verified"]).any()
    assert not as_bool(listing["competing_pass_feature_approved"]).any()
    unlinked = listing[~as_bool(listing["competing_pass_linked"])]
    assert unlinked["competing_pass_roster_link_status"].eq(
        "not_linked_in_three_reviewed_rosters_not_verified_no_competing_pass"
    ).all()
    assert not as_bool(
        listing.loc[
            listing["resort_id"].eq("toggenburg_chaserrugg_alt_st_johann_unterwasser"),
            "competing_pass_linked",
        ]
    ).any()
    assert as_bool(
        listing.loc[
            listing["resort_id"].eq("toggenburg_wildhaus"),
            "competing_pass_linked",
        ]
    ).all()

    assert len(cluster) == 162
    assert cluster["cluster_id"].is_unique
    assert int(cluster["cluster_competing_pass_listing_count"].sum()) == 271
    assert int(cluster["cluster_listings_linked_to_reviewed_competing_pass"].sum()) == 55
    assert int(as_bool(cluster["cluster_has_reviewed_competing_pass_link"]).sum()) == 29
    assert cluster["cluster_competing_pass_scope_status"].value_counts().to_dict() == {
        "no_link_in_reviewed_rosters": 133,
        "partial_cluster_listing_links": 10,
        "all_listing_points_linked_to_one_or_more_reviewed_rosters": 19,
    }
    assert not as_bool(cluster["competing_pass_market_absence_verified"]).any()
    assert not as_bool(cluster["competing_pass_feature_approved"]).any()

    assert len(candidates) == 104
    assert candidates["cluster_id"].is_unique
    assert candidates["cluster_competing_pass_scope_status"].value_counts().to_dict() == {
        "no_link_in_reviewed_rosters": 82,
        "all_listing_points_linked_to_one_or_more_reviewed_rosters": 16,
        "partial_cluster_listing_links": 6,
    }
    assert len(decision) == 162
    assert decision["analysis_version"].eq("path_c_v0_19").all()
    assert decision["accessibility_score"].isna().all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()
    assert not as_bool(decision["competing_pass_feature_approved"]).any()


def test_path_c_network_context_excludes_focal_cluster_and_preserves_pair_grain() -> None:
    context = read("data_processed/path_c_cluster_network_context.csv")
    pairs = read("reports/path_c_cluster_network_pairs.csv")
    candidates = read("reports/network_context_candidate_summary.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(context) == 162
    assert context["cluster_id"].is_unique
    assert len(pairs) == 162 * 161
    assert not pairs[["focal_cluster_id", "other_cluster_id"]].duplicated().any()
    assert not pairs["focal_cluster_id"].eq(pairs["other_cluster_id"]).any()
    assert pairs["great_circle_distance_km"].ge(0).all()
    assert pairs.groupby("focal_cluster_id").size().eq(161).all()

    reversed_pairs = pairs[[
        "focal_cluster_id", "other_cluster_id", "great_circle_distance_km"
    ]].rename(
        columns={
            "focal_cluster_id": "other_cluster_id",
            "other_cluster_id": "focal_cluster_id",
            "great_circle_distance_km": "reverse_distance_km",
        }
    )
    symmetric = pairs.merge(
        reversed_pairs,
        on=["focal_cluster_id", "other_cluster_id"],
        how="left",
        validate="one_to_one",
    )
    assert np.allclose(
        symmetric["great_circle_distance_km"], symmetric["reverse_distance_km"]
    )

    for radius in [25, 50]:
        expected_directory = (
            pairs[pairs["great_circle_distance_km"].le(radius)]
            .groupby("focal_cluster_id")
            .size()
            .reindex(context["cluster_id"], fill_value=0)
            .to_numpy()
        )
        assert np.array_equal(
            expected_directory,
            context[f"other_directory_clusters_within_{radius}km"].to_numpy(),
        )
        assert (
            context[f"other_directory_clusters_within_{radius}km"]
            <= context[f"other_directory_clusters_within_{50}km"]
        ).all()
        assert (
            context[f"other_reviewed_pass_network_clusters_within_{radius}km"]
            <= context[f"other_directory_clusters_within_{radius}km"]
        ).all()
        assert (
            context[f"other_directory_clusters_with_observed_ski_area_within_{radius}km"]
            + context[f"other_directory_clusters_missing_ski_area_within_{radius}km"]
            == context[f"other_directory_clusters_within_{radius}km"]
        ).all()

    assert len(candidates) == 104
    assert candidates["cluster_id"].is_unique
    assert int(candidates["other_directory_clusters_within_25km"].eq(0).sum()) == 1
    assert int(
        candidates["other_reviewed_pass_network_clusters_within_50km"].eq(0).sum()
    ) == 2
    assert candidates["other_directory_clusters_within_25km"].median() == 8
    assert candidates["other_directory_clusters_within_50km"].median() == 26
    assert candidates["other_reviewed_pass_network_clusters_within_50km"].median() == 9

    assert as_bool(context["network_focal_cluster_excluded_from_all_neighbourhood_counts"]).all()
    assert not as_bool(context["historical_network_context_verified"]).any()
    assert not as_bool(context["network_context_feature_approved"]).any()
    assert not as_bool(pairs["network_context_feature_approved"]).any()
    assert len(decision) == 162
    assert decision["analysis_version"].eq("path_c_v0_19").all()
    assert decision["accessibility_score"].isna().all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()
    assert not as_bool(decision["network_context_feature_approved"]).any()


def test_path_c_cluster_geography_sensitivity_preserves_clusters_and_bounds_rules() -> None:
    context = read("data_processed/path_c_cluster_geographic_sensitivity.csv")
    pairs = read("reports/path_c_cluster_distance_rule_pairs.csv")
    candidates = read("reports/cluster_geography_candidate_summary.csv")
    baseline_pairs = read("reports/path_c_cluster_network_pairs.csv")
    decision = read("data_processed/magic_pass_decision_support.csv")

    assert len(context) == 162
    assert context["cluster_id"].is_unique
    assert int(context["cluster_listing_point_count"].sum()) == 271
    assert int(context["cluster_listing_point_count"].eq(1).sum()) == 109
    assert int(context["cluster_listing_point_count"].gt(1).sum()) == 53
    assert context["cluster_listing_geographic_spread_band"].value_counts().to_dict() == {
        "single_listing": 109,
        "multi_listing_diameter_gt_5_to_25km": 28,
        "multi_listing_diameter_le_5km": 24,
        "multi_listing_diameter_gt_25_to_50km": 1,
    }
    widest = context.loc[context["within_cluster_pairwise_distance_max_km"].idxmax()]
    assert widest["cluster_id"] == "SKI_CLUSTER_200"
    assert np.isclose(widest["within_cluster_pairwise_distance_max_km"], 46.35442691735824)

    assert len(pairs) == 162 * 161
    assert not pairs[["focal_cluster_id", "other_cluster_id"]].duplicated().any()
    assert not pairs["focal_cluster_id"].eq(pairs["other_cluster_id"]).any()
    assert (
        pairs["minimum_listing_pair_distance_km"]
        <= pairs["median_listing_pair_distance_km"] + 1e-12
    ).all()
    assert (
        pairs["median_listing_pair_distance_km"]
        <= pairs["maximum_listing_pair_distance_km"] + 1e-12
    ).all()
    reproduced = pairs.merge(
        baseline_pairs[["focal_cluster_id", "other_cluster_id", "great_circle_distance_km"]],
        on=["focal_cluster_id", "other_cluster_id"],
        how="left",
        validate="one_to_one",
    )
    assert np.allclose(
        reproduced["representative_median_coordinate_distance_km"],
        reproduced["great_circle_distance_km"],
    )

    for radius in [25, 50]:
        for scope in ["directory", "reviewed_pass_network"]:
            minimum = context[
                f"other_{scope}_clusters_within_{radius}km_by_minimum_listing_pair_distance"
            ]
            median = context[
                f"other_{scope}_clusters_within_{radius}km_by_median_listing_pair_distance"
            ]
            maximum = context[
                f"other_{scope}_clusters_within_{radius}km_by_maximum_listing_pair_distance"
            ]
            assert (minimum >= median).all()
            assert (median >= maximum).all()
        assert np.array_equal(
            context[
                f"other_directory_clusters_within_{radius}km_by_representative_median_coordinate_distance"
            ].to_numpy(),
            read("data_processed/path_c_cluster_network_context.csv")[
                f"other_directory_clusters_within_{radius}km"
            ].to_numpy(),
        )

    assert len(candidates) == 104
    assert int(candidates["directory_cluster_count_distance_rule_span_within_25km"].gt(0).sum()) == 71
    assert int(candidates["reviewed_pass_network_count_distance_rule_span_within_50km"].gt(0).sum()) == 72
    assert not as_bool(context["cluster_geographic_coherence_verified"]).any()
    assert not as_bool(context["network_distance_sensitivity_feature_approved"]).any()
    assert not as_bool(pairs["network_distance_sensitivity_feature_approved"]).any()
    assert decision["analysis_version"].eq("path_c_v0_19").all()
    assert decision["accessibility_score"].isna().all()
    assert decision["predicted_uplift_pct"].isna().all()
    assert decision["composite_opportunity_need_score"].isna().all()
    assert not as_bool(decision["network_distance_sensitivity_feature_approved"]).any()


def test_public_transport_journey_context_preserves_grain_and_limits() -> None:
    samples = read(
        "data_processed/treatment_municipality_public_transport_journey_samples.csv"
    )
    context = read(
        "data_processed/treatment_municipality_public_transport_journey_context.csv"
    )
    nodes = read("reports/public_transport_journey_nodes.csv")
    arrival_review = read("reports/public_transport_arrival_node_review.csv")
    historical = read("reports/public_transport_historical_audit_plan.csv")

    assert len(samples) == 49_104
    assert samples[
        [
            "destination_unit_id",
            "municipality_bfs_id",
            "reference_date",
            "direction",
            "requested_departure_time",
        ]
    ].duplicated().sum() == 0
    assert samples["destination_unit_id"].nunique() == 11
    assert samples["municipality_bfs_id"].nunique() == 186
    assert samples["direction"].value_counts().to_dict() == {
        "return_destination_to_municipality": 28_644,
        "outbound_municipality_to_destination": 20_460,
    }
    assert set(samples["reference_date"].astype(str)) == {"20260204", "20260207"}

    feasible = samples[as_bool(samples["journey_feasible"])]
    assert len(feasible) == 38_504
    for column in [
        "initial_wait_minutes",
        "scheduled_journey_minutes",
        "generalized_elapsed_minutes",
    ]:
        assert feasible[column].notna().all()
        assert feasible[column].ge(0).all()
    assert feasible["generalized_elapsed_minutes"].le(480).all()
    assert feasible["vehicle_legs"].between(1, 6).all()
    assert feasible["transfers"].eq(feasible["vehicle_legs"] - 1).all()
    assert not as_bool(samples["causal_accessibility_feature_approved"]).any()

    assert len(context) == 2_046
    assert not context[["destination_unit_id", "municipality_bfs_id"]].duplicated().any()
    complete = context["outbound_sample_coverage_share"].eq(1) & context[
        "return_sample_coverage_share"
    ].eq(1)
    assert int(complete.sum()) == 1_104
    assert context["historical_stability_status"].eq(
        "not_yet_verified_against_anchor_year_timetables"
    ).all()
    assert not as_bool(context["public_transport_journey_feature_approved"]).any()

    assert len(nodes) == 201
    assert nodes["node_role"].value_counts().to_dict() == {
        "municipality_origin": 186,
        "destination_component_arrival": 15,
    }
    destination_nodes = nodes[nodes["node_role"].eq("destination_component_arrival")]
    assert destination_nodes["selected_stop_mode_code"].str.contains(
        "A|B", regex=True
    ).all()

    assert len(arrival_review) == 15
    assert not arrival_review["component_resort_id"].duplicated().any()
    assert arrival_review["review_class"].value_counts().to_dict() == {
        "named_lift_or_ski_access_stop": 8,
        "village_or_local_centre_proxy": 6,
        "named_destination_locality_stop": 1,
    }
    assert arrival_review[
        "selected_stop_distance_from_reference_point_km"
    ].le(2.1).all()
    assert as_bool(arrival_review["descriptive_routing_node_approved"]).all()
    assert not as_bool(arrival_review["historical_node_continuity_verified"]).any()
    assert not as_bool(arrival_review["causal_accessibility_feature_approved"]).any()
    assert int(arrival_review["active_reference_day_count"].eq(2).sum()) == 14
    warned = arrival_review[arrival_review["active_reference_day_count"].lt(2)]
    assert warned["component_resort_id"].tolist() == [
        "grimentz_zinal_grimentz_zinal"
    ]
    assert warned["absent_reference_dates"].astype(str).tolist() == ["20260204"]
    village_proxies = arrival_review[
        arrival_review["review_class"].eq("village_or_local_centre_proxy")
    ]
    assert village_proxies["user_fallback_rule"].eq(
        "village_centre_stop_authorised_when_lift_stop_is_not_practical"
    ).all()

    assert len(historical) == 15
    assert historical["destination_unit_id"].nunique() == 11
    assert set(historical["first_exposure_winter_timetable_year"]) == {
        2018,
        2019,
        2020,
        2023,
        2024,
        2025,
        2026,
    }
    assert historical["archive_url"].str.startswith("https://").all()
    assert not as_bool(
        historical["historical_destination_stop_service_compared"]
    ).any()
    assert historical["historical_line_stability_status"].eq(
        "not_yet_verified_against_anchor_year_timetables"
    ).all()
    assert not as_bool(historical["causal_accessibility_feature_approved"]).any()


def test_distance_transport_comparison_preserves_pairs_and_exposes_disagreement() -> None:
    comparison = read(
        "data_processed/treatment_municipality_distance_transport_comparison.csv"
    )
    correlations = read("reports/distance_transport_correlations_by_destination.csv")
    bands = read("reports/distance_transport_band_summary.csv")

    assert len(comparison) == 2_046
    assert not comparison[["destination_unit_id", "municipality_bfs_id"]].duplicated().any()
    assert comparison["journey_comparison_status"].value_counts().to_dict() == {
        "complete_all_sampled_times": 1_104,
        "bidirectional_means_partial_sample_coverage": 596,
        "no_bidirectional_mean": 246,
        "outbound_mean_only": 84,
        "return_mean_only": 16,
    }
    ranked = comparison[
        comparison["round_trip_time_rank_percentile_within_destination"].notna()
    ]
    assert len(ranked) == 1_700
    assert ranked["distance_rank_percentile_within_destination"].between(0, 1).all()
    assert ranked["round_trip_time_rank_percentile_within_destination"].between(0, 1).all()
    assert int(comparison["transit_materially_worse_than_distance_rank"].sum()) == 225
    assert int(comparison["transit_materially_better_than_distance_rank"].sum()) == 171
    assert not as_bool(comparison["causal_exposure_approved"]).any()
    assert not as_bool(comparison["causal_effect_approved"]).any()

    assert len(correlations) == 11
    assert correlations[
        "distance_round_trip_rank_correlation_available_pairs"
    ].notna().sum() == 10
    assert correlations[
        "distance_round_trip_rank_correlation_complete_pairs"
    ].notna().sum() == 7
    assert correlations.loc[
        correlations["bidirectional_mean_pairs"].eq(0), "destination_unit_id"
    ].tolist() == ["meiringen_hasliberg"]
    assert correlations[
        "distance_round_trip_rank_correlation_available_pairs"
    ].dropna().between(0.60, 0.88).all()
    assert len(bands) == 55
    assert not as_bool(bands["causal_exposure_approved"]).any()
