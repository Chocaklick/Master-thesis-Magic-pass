"""Run the reproducible Checkpoints 1–5 preparation pipeline."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(script: str, *arguments: str) -> None:
    command = [sys.executable, str(ROOT / script), *arguments]
    print(f"\n>>> {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-collection",
        action="store_true",
        help="Check/download configured official evidence. Cached files are checksum-verified and reused.",
    )
    args = parser.parse_args()

    run("src/data_processing/audit_existing_data.py")
    run("src/data_processing/build_initial_tables.py")
    run("src/geospatial/validate_existing_clusters.py")
    run("src/geospatial/prepare_municipality_queries.py")
    if args.with_collection:
        run("src/data_collection/collect_evidence.py", "--config", "config/evidence_sources.json")
        run(
            "src/data_collection/collect_evidence.py",
            "--config",
            "config/meteoswiss_selected_station_files.json",
        )
        run(
            "src/data_collection/collect_evidence.py",
            "--config",
            "config/meteoswiss_weather_sensitivity_station_files.json",
        )
        run(
            "src/data_collection/collect_evidence.py",
            "--config",
            "config/meteoswiss_gridded_weather_files.json",
        )
        run("src/data_collection/collect_spass_snow_grid.py")
        run("src/data_collection/collect_bfs_hotel_capacity.py")
        run("src/data_collection/collect_bfs_statpop.py")
        run("src/data_collection/collect_eurostat_census_grid.py")
        run("src/data_collection/collect_evidence.py", "--config", "config/municipality_queries.json")
        run("src/data_collection/extract_press_text.py")
    run("src/data_processing/build_hotel_capacity_panel.py")
    run("src/data_processing/build_snow_proxy_panel.py")
    run("src/data_processing/build_snow_station_sensitivity.py")
    run("src/data_processing/build_snow_gridded_sensitivity.py")
    run("src/data_processing/build_weather_proxy_panel.py")
    run("src/data_processing/build_weather_station_sensitivity.py")
    run("src/data_processing/build_weather_gridded_sensitivity.py")
    run("src/data_processing/build_temporal_controls.py")
    run("src/geospatial/build_point_municipality_crosswalk.py")
    run("src/entity_resolution/build_magic_membership_history.py")
    run("src/entity_resolution/extract_current_magic_destinations.py")
    run("src/data_processing/build_treatment_destination_panel.py")
    run("src/entity_resolution/build_membership_continuity_audit.py")
    run("src/entity_resolution/build_unmatched_scope_review.py")
    run("src/causal_inference/build_control_audit.py")
    run("src/causal_inference/build_donor_pretrend_screen.py")
    run("src/causal_inference/build_donor_network_spillover_audit.py")
    run("src/causal_inference/build_donor_external_shock_audit.py")
    run("src/causal_inference/build_distance_gradient_diagnostic.py")
    run("src/data_processing/build_public_transport_journey_context.py")
    run("src/data_processing/build_public_transport_arrival_node_review.py")
    run("src/data_processing/build_public_transport_historical_audit.py")
    run("src/data_processing/build_distance_transport_comparison.py")
    run("src/scoring/build_resort_data_quality.py")
    run("src/scoring/build_path_c_feature_matrix.py")
    run("src/scoring/build_path_c_segments_and_analogues.py")
    run("src/scoring/build_path_c_aggregation_sensitivity.py")
    run("src/data_processing/build_tourism_dependence_context.py")
    run("src/data_processing/build_accessibility_context.py")
    run("src/data_processing/build_cross_border_population_context.py")
    run("src/data_processing/build_transport_accessibility_context.py")
    run("src/data_processing/audit_transport_zone_proxies.py")
    run("src/data_processing/build_public_transport_stop_context.py")
    run("src/data_processing/build_national_road_proximity_context.py")
    run("src/data_processing/build_competing_pass_context.py")
    run("src/data_processing/build_path_c_network_context.py")
    run("src/data_processing/build_path_c_cluster_geography_sensitivity.py")
    run("src/data_processing/build_feasibility_report.py")
    run("src/scoring/plot_path_c_outputs.py")
    run("src/data_processing/update_provenance.py")
    subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
