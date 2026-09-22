from __future__ import annotations

import hashlib
import json
from pathlib import Path

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
