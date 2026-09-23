"""Normalise source provenance, extend the data dictionary, and write DATA_SOURCES.md."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE_FILE = ROOT / "metadata" / "data_sources_master.csv"
DICTIONARY_FILE = ROOT / "metadata" / "data_dictionary.csv"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
SOURCE_COLUMNS = [
    "source_id", "variable_name", "variable_description", "source_organisation",
    "source_dataset_name", "source_page_url", "direct_download_url", "api_endpoint",
    "api_parameters", "wms_layer", "geocat_metadata_url", "retrieval_method",
    "retrieval_date", "original_file_name", "local_raw_file", "processed_file",
    "geographic_level", "temporal_resolution", "temporal_start", "temporal_end",
    "unit", "license", "access_conditions", "transformation_applied", "quality_notes",
    "confidence_level", "manual_verification", "notes",
]
DICTIONARY_COLUMNS = [
    "variable", "table", "description", "unit", "data_type", "geographic_level",
    "temporal_level", "source_id", "raw_or_derived", "formula", "causal_role",
    "missing_share", "notes",
]


def blank_source(source_id: str, **values: object) -> dict:
    row = {column: "" for column in SOURCE_COLUMNS}
    row["source_id"] = source_id
    row.update({key: value for key, value in values.items() if key in row})
    return row


def cached_metadata(source_id: str) -> dict | None:
    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"))
    ]
    records = [record for record in records if record.get("source_id") == source_id]
    return records[-1] if records else None


def raw_name(metadata: dict | None) -> str:
    return Path(metadata["raw_file"]).name if metadata else ""


def upsert(frame: pd.DataFrame, rows: list[dict], key: str, columns: list[str]) -> pd.DataFrame:
    incoming = pd.DataFrame(rows).reindex(columns=columns, fill_value="")
    frame = frame.reindex(columns=columns, fill_value="")
    frame = frame[~frame[key].isin(incoming[key])]
    return pd.concat([frame, incoming], ignore_index=True).fillna("").sort_values(key)


def missing_share(path: Path, variable: str) -> str:
    data = pd.read_csv(path, usecols=[variable])
    return f"{data[variable].isna().mean():.6f}"


def main() -> None:
    existing_sources = pd.read_csv(SOURCE_FILE, dtype=str, keep_default_na=False)
    config = json.loads((ROOT / "config" / "evidence_sources.json").read_text(encoding="utf-8"))
    configured = {row["source_id"]: row for row in config}
    eurostat_config = json.loads(
        (ROOT / "config" / "eurostat_census_grid_2021.json").read_text(encoding="utf-8")
    )
    rows: list[dict] = []

    bfs_metadata = cached_metadata("BFS_HOTEL_METADATA")
    boundary_metadata = cached_metadata("SWISSTOPO_BOUNDARIES_2026")
    bfs_capacity_metadata = cached_metadata("BFS_HOTEL_CAPACITY_METADATA")
    bfs_statpop_metadata = cached_metadata("BFS_STATPOP_METADATA")
    bfs_statpop_data = cached_metadata("BFS_STATPOP_DATA")
    are_transport_data = cached_metadata("ARE_NPVM_TRAVEL_TIME_2025")
    are_transport_stac = cached_metadata("ARE_NPVM_TRAVEL_TIME_2025_STAC")
    are_transport_method = cached_metadata("ARE_TRANSPORT_ACCESSIBILITY_METHOD")
    bav_stop_data = cached_metadata("BAV_PUBLIC_TRANSPORT_STOPS_2026")
    bav_stop_stac = cached_metadata("BAV_PUBLIC_TRANSPORT_STOPS_2026_STAC")
    bav_stop_model = cached_metadata("BAV_PUBLIC_TRANSPORT_STOPS_MODEL")
    astra_road_data = cached_metadata("ASTRA_NATIONAL_ROAD_AXES_2026")
    astra_road_stac = cached_metadata("ASTRA_NATIONAL_ROAD_AXES_2026_STAC")
    astra_road_collection = cached_metadata("ASTRA_NATIONAL_ROAD_AXES_COLLECTION")
    competing_pass_metadata = {
        source_id: cached_metadata(source_id)
        for source_id in [
            "ALPSPASS_2026_27_ROSTER",
            "ALPSPASS_2026_27_GTC",
            "MEILENWEISS_CURRENT_ROSTER",
            "SCHNEEPASS_ZENTRALSCHWEIZ_2026_27_ROSTER",
        ]
    }
    ski_gtfs_data = cached_metadata("SKI_GTFS_TIMETABLE_2026_WINTER_20260207")
    eurostat_grid_data = cached_metadata("EUROSTAT_CENSUS_GRID_2021_V3")
    eurostat_grid_documentation = cached_metadata("EUROSTAT_CENSUS_GRID_2021_V3_README")
    bfs_capacity_records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in EVIDENCE_DIR.glob("BFS_HOTEL_CAPACITY_DATA_*.metadata.json")
    ]
    bfs_capacity_records = [
        record
        for record in bfs_capacity_records
        if record.get("source_id") == "BFS_HOTEL_CAPACITY_DATA"
        and record.get("raw_files")
    ]
    bfs_capacity_data = (
        max(bfs_capacity_records, key=lambda record: record["retrieval_date"])
        if bfs_capacity_records
        else None
    )
    rows.append(blank_source(
        "BFS_HOTEL_DATA",
        variable_name="hotel_arrivals|hotel_overnights|domestic_overnights|foreign_overnights",
        variable_description="Monthly hotel arrivals and overnight stays in open establishments by municipality and visitor origin",
        source_organisation="Swiss Federal Statistical Office (FSO/OFS/BFS)",
        source_dataset_name="px-x-1003020000_101",
        source_page_url="https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_101/",
        api_endpoint=configured["BFS_HOTEL_METADATA"]["url"],
        api_parameters="All available years, months, municipalities, origins and indicators; original extraction was chunked",
        retrieval_method="Existing researcher API extraction; construction script inspected; live metadata independently cached",
        retrieval_date="UNKNOWN_FOR_EXISTING_DATA_FILE",
        original_file_name="nuitée_commune_final.csv",
        local_raw_file="data_raw/nuitée_commune_final.csv",
        processed_file="data_processed/hotel_municipality_month.csv",
        geographic_level="municipality",
        temporal_resolution="monthly plus annual total rows",
        temporal_start="2013-01",
        temporal_end="2026-03 observed; later 2026 grid cells suppressed/unavailable",
        unit="persons (arrivals); overnight stays",
        license="See official FSO terms",
        access_conditions="Public PXWeb table; source suppression applies",
        transformation_applied="Annual rows excluded from monthly panel; literal tokens preserved; nonnegative integer cells parsed; domestic/foreign split and log1p derived",
        quality_notes="2,793 monthly total-night cells contain '...'; no imputation; municipality boundary changes still require review",
        confidence_level="high for official source; medium for legacy extraction provenance",
        manual_verification="API metadata, row structure, suppression tokens, and annual/monthly reconciliation checked",
        notes="Annual totals reconcile exactly wherever all 12 monthly observations are available",
    ))
    rows.append(blank_source(
        "SWISSTOPO_BOUNDARIES_2026",
        variable_name="municipality_geometry|municipality_bfs_id|municipality_area_ha_2026|municipality_representative_point",
        variable_description="Official 2026 municipality polygons used for distance diagnostics and qualified population accessibility context",
        source_organisation="Federal Office of Topography swisstopo",
        source_dataset_name="swissBOUNDARIES3D 2026-01",
        source_page_url="https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d",
        direct_download_url=configured["SWISSTOPO_BOUNDARIES_2026"]["url"],
        retrieval_method="Configured HTTPS download with immutable ZIP, SHA-256 sidecar and collection log",
        retrieval_date=(boundary_metadata or {}).get("retrieval_date", ""),
        original_file_name=raw_name(boundary_metadata),
        local_raw_file=(boundary_metadata or {}).get("raw_file", ""),
        processed_file="data_processed/treatment_municipality_distance_exposure.csv|data_processed/treatment_distance_gradient_diagnostic.csv|data_processed/municipality_population_geometry_2026.csv|data_processed/path_c_cluster_accessibility_context.csv",
        geographic_level="Swiss political municipality polygon",
        temporal_resolution="boundary snapshot",
        temporal_start="2026-01-01",
        temporal_end="2026-01-01",
        unit="EPSG:2056 multipolygon",
        license="Federal geodata terms; public Open Government Data",
        access_conditions="Public swisstopo download",
        transformation_applied="Checksum verification; GeoPackage extraction; representative point, centroid and polygon-to-resort distance in EPSG:2056; official 2025 population aligned through reviewed 2026 mutations",
        quality_notes="Current geometry is not historical harmonisation; representative points are neither population centroids nor transport nodes",
        confidence_level="high for current boundaries; qualified for historical outcome alignment",
        manual_verification="186 hotel series map to 185 current geometries; 2,115 STATPOP rows reconcile to all 2,110 current municipalities with national population preserved",
    ))
    for mutation_id in range(3999, 4004):
        source_id = f"BFS_MUNICIPAL_MUTATION_{mutation_id}"
        item = configured[source_id]
        metadata = cached_metadata(source_id)
        rows.append(blank_source(
            source_id,
            variable_name="source_bfs_id_2025|target_bfs_id_2026|municipality_mutation_relationship",
            variable_description=item["description"],
            source_organisation="Swiss Federal Statistical Office (FSO/OFS/BFS)",
            source_dataset_name=f"Official municipality mutation {mutation_id}",
            source_page_url=item["url"],
            direct_download_url=item["url"],
            retrieval_method="HTTP GET with immutable response and SHA-256 sidecar",
            retrieval_date=(metadata or {}).get("retrieval_date", ""),
            original_file_name=raw_name(metadata),
            local_raw_file=(metadata or {}).get("raw_file", ""),
            processed_file="config/municipality_boundary_bridge_2025_2026.csv|data_processed/municipality_population_geometry_2026.csv|data_processed/path_c_cluster_accessibility_context.csv",
            geographic_level="affected Swiss municipality identifiers",
            temporal_resolution="official municipality mutation",
            temporal_start="2026-01-01",
            temporal_end="2026-01-01",
            unit="identifier relationship",
            license="See official FSO terms",
            access_conditions="Public official municipality register page",
            transformation_applied="Exact old/new BFS identifiers and municipality names transcribed to a versioned seven-row bridge; cached page tokens verified before use",
            quality_notes="Used only to align the complete 2025 STATPOP municipality universe to the 2026 boundary snapshot",
            confidence_level="high",
            manual_verification="Source and target BFS identifiers and names checked in the checksum-protected official page",
        ))
    donor_archive_sources = [
        ("BBGR_ANNUAL_2017_18", "Bergbahnen Graubünden annual report 2017/18", "2017-07", "2018-06"),
        ("BBGR_ANNUAL_2018_19", "Bergbahnen Graubünden annual report 2018/19", "2018-07", "2019-06"),
        ("BBGR_ANNUAL_2019_20", "Bergbahnen Graubünden annual report 2019/20", "2019-07", "2020-06"),
        ("GRAUBUENDENCARD_TRANSIT_2022_23", "graubündenCARD transport benefits 2022/23", "2022-11", "2023-04"),
        ("KRONBERG_ANNUAL_2017", "Kronberg AG annual report 2017", "2017-01", "2017-12"),
        ("KRONBERG_ANNUAL_2023", "Kronberg AG annual report 2023", "2023-01", "2023-12"),
        ("ENGADIN_MOUNTAINS_ANNUAL_2017_18", "Engadin St. Moritz Mountains AG annual report 2017/18", "2017-11", "2018-10"),
        ("ENGADIN_MOUNTAINS_ANNUAL_2019_20", "Engadin St. Moritz Mountains AG annual report 2019/20", "2019-11", "2020-10"),
        ("SPLUEGEN_TAMBO_ANNUAL_2023_24", "Bergbahnen Splügen-Tambo AG annual report 2023/24", "2023-05", "2024-04"),
        ("GR_MINSCHUNS_INVESTMENT_2019", "Graubünden government release on Minschuns investment", "2019-11", "2019-11"),
        ("SAMNAUN_VISNITZBAHN_HISTORY", "Silvrettaseilbahn AG history of the Visnitzbahn replacement", "2019-01", "2019-12"),
    ]
    for source_id, dataset_name, temporal_start, temporal_end in donor_archive_sources:
        item = configured[source_id]
        metadata = cached_metadata(source_id)
        rows.append(blank_source(
            source_id,
            variable_name="competing_pass_environment|operator_investment_and_tourism_shock_evidence",
            variable_description=item["description"],
            source_organisation=item["organisation"],
            source_dataset_name=dataset_name,
            source_page_url=item["url"],
            direct_download_url=item["url"],
            retrieval_method="HTTP GET with immutable response and SHA-256 sidecar",
            retrieval_date=(metadata or {}).get("retrieval_date", ""),
            original_file_name=raw_name(metadata),
            local_raw_file=(metadata or {}).get("raw_file", ""),
            processed_file="reports/donor_external_shock_evidence.csv|data_processed/donor_shortlist_final_audit.csv",
            geographic_level="regional pass market or reviewed donor operator",
            temporal_resolution="annual report or winter-season publication",
            temporal_start=temporal_start,
            temporal_end=temporal_end,
            unit="documentary evidence",
            license="See publisher terms",
            access_conditions="Public official PDF at collection time",
            transformation_applied="Page-referenced manual review; source qualification and unresolved exactness retained",
            quality_notes="Regional pass evidence is not automatically exact operator participation; unavailable anchor-season files remain unresolved",
            confidence_level="high for official document; qualified for donor-level causal interpretation",
            manual_verification="Relevant pages reviewed for pass environment, operator scope and contemporaneous investment",
        ))
    rows.append(blank_source(
        "BFS_HOTEL_METADATA",
        variable_name="hotel_table_schema|municipality_bfs_id",
        variable_description="Live metadata for the official hotel table, including municipality codes and labels",
        source_organisation="Swiss Federal Statistical Office (FSO/OFS/BFS)",
        source_dataset_name="px-x-1003020000_101 metadata",
        source_page_url="https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_101/",
        direct_download_url=configured["BFS_HOTEL_METADATA"]["url"],
        api_endpoint=configured["BFS_HOTEL_METADATA"]["url"],
        api_parameters="GET table metadata",
        retrieval_method="HTTP GET with immutable response and SHA-256 sidecar",
        retrieval_date=bfs_metadata.get("retrieval_date", "") if bfs_metadata else "",
        original_file_name=raw_name(bfs_metadata),
        local_raw_file=bfs_metadata.get("raw_file", "") if bfs_metadata else "",
        processed_file="data_processed/resort_point_municipality.csv",
        geographic_level="municipality",
        temporal_resolution="metadata snapshot",
        temporal_start="2013",
        temporal_end="2026",
        unit="metadata",
        license="See official FSO terms",
        access_conditions="Public PXWeb API",
        transformation_applied="Municipality code-label pairs extracted without fuzzy matching",
        quality_notes="Live table composition can change; cached response is the reproducibility anchor",
        confidence_level="high",
        manual_verification="response schema and Gemeinde dimension checked",
    ))
    rows.append(blank_source(
        "BFS_HOTEL_CAPACITY_METADATA",
        variable_name="capacity_table_schema|municipality_bfs_id",
        variable_description="Live metadata for the HESTA supply, demand, and occupancy table",
        source_organisation="Swiss Federal Statistical Office (FSO/OFS/BFS)",
        source_dataset_name="px-x-1003020000_201 metadata",
        source_page_url="https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_201/",
        direct_download_url=configured["BFS_HOTEL_CAPACITY_METADATA"]["url"],
        api_endpoint=configured["BFS_HOTEL_CAPACITY_METADATA"]["url"],
        api_parameters="GET table metadata",
        retrieval_method="HTTP GET with immutable response and SHA-256 sidecar",
        retrieval_date=(bfs_capacity_metadata or {}).get("retrieval_date", ""),
        original_file_name=raw_name(bfs_capacity_metadata),
        local_raw_file=(bfs_capacity_metadata or {}).get("raw_file", ""),
        processed_file="data_processed/hotel_capacity_municipality_month.csv",
        geographic_level="municipality",
        temporal_resolution="metadata snapshot",
        temporal_start="2013",
        temporal_end="2026",
        unit="metadata",
        license="See official FSO terms",
        access_conditions="Public PXWeb API",
        transformation_applied="Dimension codes and municipality code-label pairs extracted exactly",
        quality_notes="Reference municipality universe is dated 2026-01-01; cached response anchors the schema",
        confidence_level="high",
        manual_verification="response schema and all four dimensions checked",
    ))
    capacity_first_raw = (
        bfs_capacity_data["raw_files"][0]["raw_file"] if bfs_capacity_data else ""
    )
    rows.append(blank_source(
        "BFS_HOTEL_CAPACITY_DATA",
        variable_name="hotel_establishments_open|hotel_rooms_available|hotel_beds_available|hotel_room_occupancy_rate_pct|hotel_bed_occupancy_rate_pct",
        variable_description="Monthly HESTA hotel supply, demand, and occupancy in open establishments by municipality",
        source_organisation="Swiss Federal Statistical Office (FSO/OFS/BFS)",
        source_dataset_name="px-x-1003020000_201",
        source_page_url="https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-1003020000_201/",
        api_endpoint=configured["BFS_HOTEL_CAPACITY_METADATA"]["url"],
        api_parameters="All 2013-2026 years, 12 months, 186 municipalities, and 8 indicators; annual-total month excluded; one POST per year",
        retrieval_method="PXWeb HTTP POST in 14 annual chunks; exact queries, responses, SHA-256 checksums, and logs preserved",
        retrieval_date=(bfs_capacity_data or {}).get("retrieval_date", ""),
        original_file_name=Path(capacity_first_raw).name if capacity_first_raw else "",
        local_raw_file=capacity_first_raw,
        processed_file="data_processed/hotel_capacity_municipality_month.csv|data_processed/hotel_municipality_month_enriched.csv|data_processed/destination_month_panel.csv",
        geographic_level="municipality",
        temporal_resolution="monthly grid",
        temporal_start="2013-01",
        temporal_end="2026-12 grid; later months unavailable at retrieval",
        unit="establishments; rooms; beds; arrivals; overnight stays; percent",
        license="See official FSO terms",
        access_conditions="Public PXWeb API; source missing and protection tokens apply",
        transformation_applied="Annual chunks concatenated; literal '..' and '...' tokens preserved; numeric values parsed without imputation; exact municipality-date join to legacy demand panel",
        quality_notes="1,974 supply rows are unavailable/protected; 59 bed-occupancy percentages exceed 100 as published; 6 demand cells in 3 Davos months differ from the legacy extraction and are reported without overwriting it",
        confidence_level="high for official source; version differences explicitly retained",
        manual_verification="schema, checksums, grain, value bounds, and demand reconciliation checked",
        notes="Fourteen raw annual response files are listed in the master metadata sidecar; local_raw_file points to the first chunk",
    ))
    rows.append(blank_source(
        "BFS_STATPOP_METADATA",
        variable_name="statpop_table_schema|municipality_bfs_id",
        variable_description="Live metadata for the official STATPOP municipality population table",
        source_organisation="Swiss Federal Statistical Office (FSO/OFS/BFS)",
        source_dataset_name="px-x-0102010000_101 metadata",
        source_page_url="https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-0102010000_101/",
        direct_download_url=configured["BFS_STATPOP_METADATA"]["url"],
        api_endpoint=configured["BFS_STATPOP_METADATA"]["url"],
        api_parameters="GET table metadata",
        retrieval_method="HTTP GET with immutable response and SHA-256 sidecar",
        retrieval_date=(bfs_statpop_metadata or {}).get("retrieval_date", ""),
        original_file_name=raw_name(bfs_statpop_metadata),
        local_raw_file=(bfs_statpop_metadata or {}).get("raw_file", ""),
        processed_file="data_processed/municipality_tourism_context_2025.csv",
        geographic_level="municipality",
        temporal_resolution="metadata snapshot",
        temporal_start="2010",
        temporal_end="2025",
        unit="metadata",
        license="See official FSO terms; source attribution required",
        access_conditions="Public PXWeb API",
        transformation_applied="Dimension codes and 2,115 municipality code-label pairs reviewed exactly",
        quality_notes="Cached metadata states 31 December reference date and commune geography state 6 April 2025",
        confidence_level="high",
        manual_verification="response schema and all six dimensions checked",
    ))
    rows.append(blank_source(
        "BFS_STATPOP_DATA",
        variable_name="resident_population|population_reference_year|municipality_bfs_id",
        variable_description="Permanent resident population by municipality at 31 December 2025",
        source_organisation="Swiss Federal Statistical Office (FSO/OFS/BFS)",
        source_dataset_name="STATPOP px-x-0102010000_101",
        source_page_url="https://www.pxweb.bfs.admin.ch/pxweb/fr/px-x-0102010000_101/",
        api_endpoint=configured["BFS_STATPOP_METADATA"]["url"],
        api_parameters="2025; all municipalities; permanent residents; total citizenship, sex and age",
        retrieval_method="PXWeb HTTP POST; exact query, raw response and SHA-256 checksum preserved",
        retrieval_date=(bfs_statpop_data or {}).get("retrieval_date", ""),
        original_file_name=raw_name(bfs_statpop_data),
        local_raw_file=(bfs_statpop_data or {}).get("raw_file", ""),
        processed_file="data_processed/municipality_tourism_context_2025.csv|data_processed/path_c_cluster_tourism_context.csv|data_processed/municipality_population_geometry_2026.csv|data_processed/path_c_cluster_accessibility_context.csv|data_processed/magic_pass_decision_support.csv",
        geographic_level="municipality",
        temporal_resolution="annual reference-day population",
        temporal_start="2025-12-31",
        temporal_end="2025-12-31",
        unit="persons",
        license="See official FSO terms; source attribution required",
        access_conditions="Public PXWeb API",
        transformation_applied="Exact BFS code parsed from official municipality label; no population imputation; exact BFS join to HESTA 2025",
        quality_notes="Population is municipal context; it does not define a ski destination catchment",
        confidence_level="high for official municipality population; qualified for resort interpretation",
        manual_verification="2,115 unique municipality rows; positive population values; exact year and category filters",
    ))
    rows.append(blank_source(
        "DERIVED_TOURISM_DEPENDENCE_CONTEXT",
        variable_name="overnights_per_resident|hotel_beds_per_1000_residents|point-container tourism context",
        variable_description="Qualified tourism-intensity context for municipalities containing supplied resort listing points",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C point-container tourism context",
        retrieval_method="Versioned exact-BFS merge of STATPOP 2025, HESTA 2025 and resort point-container crosswalk",
        local_raw_file="data_processed/resort_point_municipality.csv",
        processed_file="data_processed/municipality_tourism_context_2025.csv|data_processed/path_c_cluster_tourism_context.csv|data_processed/magic_pass_decision_support.csv|reports/20_TOURISM_DEPENDENCE_CONTEXT.md",
        geographic_level="municipality and linked lift cluster point-container set",
        temporal_resolution="2025 annual context",
        temporal_start="2025-01-01",
        temporal_end="2025-12-31",
        unit="persons; hotel nights; beds; per-resident ratios",
        transformation_applied="Require all 12 HESTA months; sum annual hotel nights; average monthly supply; divide by resident population; aggregate unique point containers only when every municipality is complete",
        quality_notes="Point containment is not an approved tourism catchment or exposure mapping; hotel statistics omit non-hotel accommodation",
        confidence_level="high for reproducibility; descriptive context only",
        manual_verification="2,115 population rows; 185 complete HESTA municipalities; every tourism-dependence approval flag false",
    ))
    rows.append(blank_source(
        "DERIVED_ACCESSIBILITY_CONTEXT",
        variable_name="distance_to_population_threshold_municipality|resident_population_within_straight_line_radius|distance_to_swiss_country_boundary|cross_border_truncation_risk|boundary_bridge",
        variable_description="Qualified Swiss straight-line population context for every linked Path C lift cluster",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C straight-line population accessibility context",
        retrieval_method="Versioned deterministic Python transformation of STATPOP 2025 and swissBOUNDARIES3D 2026",
        local_raw_file="config/path_c_analysis.json|config/municipality_boundary_bridge_2025_2026.csv",
        processed_file="data_processed/municipality_population_geometry_2026.csv|data_processed/path_c_cluster_accessibility_context.csv|data_processed/magic_pass_decision_support.csv|reports/21_ACCESSIBILITY_CONTEXT.md",
        geographic_level="current Swiss municipality and linked lift cluster",
        temporal_resolution="2025 population aligned to 2026-01-01 boundaries",
        temporal_start="2025-12-31",
        temporal_end="2026-01-01",
        unit="persons and straight-line kilometres",
        transformation_applied="Aggregate seven superseded STATPOP identifiers through five official mutations; use polygon representative points; calculate EPSG:2056 distances and population sums at versioned thresholds and radii",
        quality_notes="Not travel time, a population raster, a destination catchment or a cross-border market; municipality population is collapsed to one interior point and radius-specific border intersection is flagged without filling foreign population",
        confidence_level="high for reproducibility; qualified geographic context only",
        manual_verification="2,115 STATPOP rows reconcile to 2,110 current polygons; 9,127,125 residents preserved; all 162 clusters covered; two artificial cluster-median points outside the Swiss polygon exposed; every approval flag false",
    ))
    rows.append(blank_source(
        "EUROSTAT_CENSUS_GRID_2021_V3",
        variable_name="grid_cell_id|total_population_2021|reporting_country_codes|land_surface|populated_flag",
        variable_description="Official harmonised 2021 census population on a one-kilometre European grid",
        source_organisation="European Commission, Eurostat GISCO",
        source_dataset_name="Eurostat Census Grid 2021 version 3",
        source_page_url=eurostat_config["source_page_url"],
        direct_download_url=eurostat_config["archive_url"],
        retrieval_method="HTTP byte-range extraction of the full unfiltered CSV member; ZIP size and CRC32 plus SHA-256 verified",
        retrieval_date=(eurostat_grid_data or {}).get("retrieval_date", ""),
        original_file_name=raw_name(eurostat_grid_data),
        local_raw_file=(eurostat_grid_data or {}).get("raw_file", ""),
        processed_file="data_processed/eurostat_population_grid_2021_swiss_region.csv|data_processed/path_c_cluster_cross_border_population_context.csv|data_processed/magic_pass_decision_support.csv|reports/29_CROSS_BORDER_POPULATION_CONTEXT.md",
        geographic_level="one-kilometre census grid cell across the European source universe",
        temporal_resolution="2021 census reference",
        temporal_start="2021-01-01",
        temporal_end="2021-12-31",
        unit="persons; EPSG:3035 grid cell",
        license=eurostat_config["license"],
        access_conditions="Public official Eurostat GISCO download; source acknowledgement required",
        transformation_applied="Parse cell lower-left coordinates from the INSPIRE grid identifier; use cell centroid; retain cells within 120.707 km of a linked cluster; preserve Switzerland-only, foreign-only and mixed reporting-country scopes",
        quality_notes="Thirteen country-level unallocated records have no spatial location; mixed-border-cell population cannot be split by country; census residents are not skier demand",
        confidence_level="high for the official harmonised grid; qualified for resort-market interpretation",
        manual_verification="4,595,932 source rows; 4,595,919 located cells; CSV member ZIP CRC32 and SHA-256 verified; all 162 clusters covered",
    ))
    rows.append(blank_source(
        "EUROSTAT_CENSUS_GRID_2021_V3_README",
        variable_name="grid_variable_definitions|missing_value_codes|unallocated_population_rule|change_log",
        variable_description="Official data dictionary and change log for Eurostat Census Grid 2021 version 3",
        source_organisation="European Commission, Eurostat GISCO",
        source_dataset_name="Eurostat Census Grid 2021 version 3 read.me",
        source_page_url=eurostat_config["source_page_url"],
        direct_download_url=eurostat_config["archive_url"],
        retrieval_method="HTTP byte-range extraction of the ZIP documentation member; CRC32 and SHA-256 verified",
        retrieval_date=(eurostat_grid_documentation or {}).get("retrieval_date", ""),
        original_file_name=raw_name(eurostat_grid_documentation),
        local_raw_file=(eurostat_grid_documentation or {}).get("raw_file", ""),
        processed_file="src/data_processing/build_cross_border_population_context.py|reports/29_CROSS_BORDER_POPULATION_CONTEXT.md",
        geographic_level="dataset documentation",
        temporal_resolution="version 3 release documentation",
        temporal_start="2026-05-30",
        temporal_end="2026-05-30",
        unit="metadata",
        license=eurostat_config["license"],
        access_conditions="Public official Eurostat GISCO download",
        transformation_applied="Definitions of total population, EPSG:3035, missing codes and unallocated records are validated before processing",
        quality_notes="Documentation defines -8888 as confidentiality-related unavailability and -9999 as other unavailability",
        confidence_level="high",
        manual_verification="Required data-dictionary tokens are checked automatically against the checksum-protected read.me",
    ))
    rows.append(blank_source(
        "DERIVED_CROSS_BORDER_POPULATION_CONTEXT",
        variable_name="population_within_straight_line_radius|foreign_only_population|mixed_border_cell_population|country_scope|unavailable_total_cell_count",
        variable_description="Qualified cross-border one-kilometre population context for every linked Path C lift cluster",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C Eurostat cross-border population context",
        retrieval_method="Versioned deterministic Python transformation of the checksum-verified Eurostat 2021 census grid",
        local_raw_file="config/path_c_analysis.json|config/eurostat_census_grid_2021.json",
        processed_file="data_processed/eurostat_population_grid_2021_swiss_region.csv|data_processed/path_c_cluster_cross_border_population_context.csv|reports/cross_border_population_candidate_summary.csv|data_processed/magic_pass_decision_support.csv|reports/29_CROSS_BORDER_POPULATION_CONTEXT.md",
        geographic_level="one-kilometre census grid cell and linked lift cluster",
        temporal_resolution="2021 census population; current/undated cluster coordinate",
        temporal_start="2021-01-01",
        temporal_end="2021-12-31",
        unit="persons, cell counts, shares and straight-line kilometres",
        transformation_applied="Use cell centroids in EPSG:3035; sum observed total population inside 30/60/90/120 km; partition Switzerland-only, foreign-only and mixed-border cells; never allocate country-level unplaced population",
        quality_notes="Not a travel-time market, observed visitor origin or destination catchment; separate from STATPOP 2025 because years and spatial allocation differ",
        confidence_level="high for reproducibility; qualified geographic context only",
        manual_verification="181,598 regional cells retained; no unavailable total-population cells in the regional extract; all 162 clusters and 104 candidates covered; every approval flag false",
    ))
    rows.append(blank_source(
        "ARE_NPVM_TRAVEL_TIME_2025",
        variable_name="road_major_center_travel_time_minutes|public_transport_major_center_travel_time_minutes|road_agglomeration_travel_time_minutes|public_transport_agglomeration_travel_time_minutes|npvm_traffic_zone_geometry",
        variable_description="Modelled traffic-zone travel times to the fastest of six major centres and to the fastest agglomeration/core municipality by road and public transport",
        source_organisation="Swiss Federal Office for Spatial Development (ARE)",
        source_dataset_name="NPVM travel time to centres and agglomerations, reference date 2025-06-30",
        source_page_url="https://www.are.admin.ch/de/verkehrserschliessung",
        direct_download_url=configured["ARE_NPVM_TRAVEL_TIME_2025"]["url"],
        api_endpoint=configured["ARE_NPVM_TRAVEL_TIME_2025_STAC"]["url"],
        geocat_metadata_url="https://www.geocat.ch/geonetwork/srv/eng/catalog.search#/metadata/aee88d88-6fa6-445c-8d4d-5b40f592436b",
        retrieval_method="Configured HTTPS download with immutable GeoPackage, SHA-256 sidecar and independently cached STAC metadata",
        retrieval_date=(are_transport_data or {}).get("retrieval_date", ""),
        original_file_name=raw_name(are_transport_data),
        local_raw_file=(are_transport_data or {}).get("raw_file", ""),
        processed_file="data_processed/resort_transport_accessibility_context.csv|data_processed/path_c_cluster_transport_accessibility_context.csv|data_processed/magic_pass_decision_support.csv",
        geographic_level="NPVM traffic zone",
        temporal_resolution="model reference-date snapshot",
        temporal_start="2025-06-30",
        temporal_end="2025-06-30",
        unit="minutes; EPSG:2056 polygon; traffic-zone identifier",
        license="Open Government Data terms with source attribution",
        access_conditions="Public geo.admin.ch STAC/download service",
        transformation_applied="Checksum and STAC multihash verification; point-in-zone assignment or nearest zone intersecting the independently resolved current point municipality; min/median/max listing-point aggregation by existing lift cluster",
        quality_notes="Traffic-zone model output, not live door-to-door routing; polygons do not continuously cover high-alpine terrain; municipality-constrained proxy distance and exact-only medians are retained",
        confidence_level="high for official zonal values; qualified for resort-origin interpretation",
        manual_verification="7,978 unique zones, 84 named targets, six major centres, complete four-way travel-time fields and blank unused accessibility-index fields checked",
    ))
    rows.append(blank_source(
        "ARE_NPVM_TRAVEL_TIME_2025_STAC",
        variable_name="npvm_model_reference_date|asset_url|asset_crs|asset_multihash",
        variable_description="Official STAC item metadata fixing the ARE travel-time asset reference date, CRS, URL and checksum",
        source_organisation="Swiss Federal Office for Spatial Development (ARE) via geo.admin.ch",
        source_dataset_name="STAC item ch.are.reisezeit-miv/reisezeit-miv",
        source_page_url=configured["ARE_NPVM_TRAVEL_TIME_2025_STAC"]["url"],
        api_endpoint=configured["ARE_NPVM_TRAVEL_TIME_2025_STAC"]["url"],
        retrieval_method="HTTP GET with immutable JSON response and SHA-256 sidecar",
        retrieval_date=(are_transport_stac or {}).get("retrieval_date", ""),
        original_file_name=raw_name(are_transport_stac),
        local_raw_file=(are_transport_stac or {}).get("raw_file", ""),
        processed_file="data_processed/resort_transport_accessibility_context.csv|reports/22_TRANSPORT_ACCESSIBILITY_CONTEXT.md",
        geographic_level="dataset metadata",
        temporal_resolution="asset metadata snapshot",
        temporal_start="2025-06-30",
        temporal_end="2025-06-30",
        unit="metadata",
        license="Open Government Data terms with source attribution",
        access_conditions="Public STAC API",
        transformation_applied="Reference date, EPSG code, asset URL and multihash parsed and checked against the cached GeoPackage",
        quality_notes="Publication/update timestamps are not substituted for the model reference date",
        confidence_level="high",
        manual_verification="STAC datetime 2025-06-30, EPSG:2056 and SHA-256 multihash match checked",
    ))
    rows.append(blank_source(
        "ARE_TRANSPORT_ACCESSIBILITY_METHOD",
        variable_name="travel_time_measure_definition|major_centre_definition|agglomeration_core_municipality_definition",
        variable_description="Official ARE definitions for the road and public-transport travel-time measures",
        source_organisation="Swiss Federal Office for Spatial Development (ARE)",
        source_dataset_name="Transport access in Switzerland methodology page",
        source_page_url=configured["ARE_TRANSPORT_ACCESSIBILITY_METHOD"]["url"],
        direct_download_url=configured["ARE_TRANSPORT_ACCESSIBILITY_METHOD"]["url"],
        retrieval_method="HTTP GET with immutable HTML response and SHA-256 sidecar",
        retrieval_date=(are_transport_method or {}).get("retrieval_date", ""),
        original_file_name=raw_name(are_transport_method),
        local_raw_file=(are_transport_method or {}).get("raw_file", ""),
        processed_file="reports/22_TRANSPORT_ACCESSIBILITY_CONTEXT.md",
        geographic_level="methodology",
        temporal_resolution="retrieval snapshot",
        unit="definition",
        license="See official ARE terms",
        access_conditions="Public official page",
        transformation_applied="Definitions interpreted together with the GeoPackage field schema",
        quality_notes="Methodological definition does not make a resort listing coordinate a validated arrival node",
        confidence_level="high",
        manual_verification="Six major centres and fastest accessible agglomeration/core-municipality definitions reviewed",
    ))
    rows.append(blank_source(
        "DERIVED_TRANSPORT_ACCESSIBILITY_CONTEXT",
        variable_name="listing_npvm_zone_assignment|cluster_road_travel_time|cluster_public_transport_travel_time|assignment_distance|exact_only_sensitivity",
        variable_description="Qualified NPVM road and public-transport accessibility context for supplied resort listings and linked Path C lift clusters",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C NPVM transport accessibility context",
        retrieval_method="Versioned deterministic Python transformation of checksum-verified ARE, geo.admin.ch point-municipality and swissBOUNDARIES3D sources",
        local_raw_file="config/path_c_analysis.json|data_processed/resort_point_municipality.csv",
        processed_file="data_processed/resort_transport_accessibility_context.csv|data_processed/path_c_cluster_transport_accessibility_context.csv|data_processed/magic_pass_decision_support.csv|reports/22_TRANSPORT_ACCESSIBILITY_CONTEXT.md|reports/transport_zone_proxy_audit.csv|reports/27_TRANSPORT_ZONE_PROXY_AUDIT.md",
        geographic_level="supplied resort listing point and linked lift cluster",
        temporal_resolution="NPVM model reference date 2025-06-30; current directory coordinates",
        temporal_start="2025-06-30",
        temporal_end="2025-06-30",
        unit="minutes; kilometres; counts and assignment flags",
        transformation_applied="Use exact zone containment for 170 points; for 98 Swiss high-alpine points use the nearest zone intersecting the same independently resolved current municipality; leave three foreign points missing; aggregate min/median/max across usable listing points and retain exact-only medians",
        quality_notes="Not live routing, rail-only access, a timetable, a valley-station origin or a destination catchment; within-municipality zone links are explicit proxies and remain unapproved",
        confidence_level="high for reproducibility; qualified modelled context only",
        manual_verification="268/271 listing points usable; all 98 municipality-constrained proxies geometrically reconstructed; 50 proxy-only clusters lack an internal exact-zone reference; zero approval flags",
    ))
    rows.append(blank_source(
        "BAV_PUBLIC_TRANSPORT_STOPS_2026",
        variable_name="passenger_stop_id|passenger_stop_name|passenger_stop_type|transport_mode|operator|municipality|stop_geometry",
        variable_description="Official public-transport stops and selected operating points, filtered to actual passenger-stop types for proximity calculations",
        source_organisation="Swiss Federal Office of Transport (BAV/OFT)",
        source_dataset_name="Public transport stops, GeoIV ID 98.2, French EPSG:2056 CSV export",
        source_page_url="https://www.bav.admin.ch/de/haltestellen-des-oeffentlichen-verkehrs-geoiv-id-982",
        direct_download_url=configured["BAV_PUBLIC_TRANSPORT_STOPS_2026"]["url"],
        api_endpoint=configured["BAV_PUBLIC_TRANSPORT_STOPS_2026_STAC"]["url"],
        retrieval_method="Configured HTTPS download with immutable ZIP, SHA-256 sidecar and independently cached STAC metadata",
        retrieval_date=(bav_stop_data or {}).get("retrieval_date", ""),
        original_file_name=raw_name(bav_stop_data),
        local_raw_file=(bav_stop_data or {}).get("raw_file", ""),
        processed_file="data_processed/resort_public_transport_stop_context.csv|data_processed/path_c_cluster_public_transport_stop_context.csv|data_processed/magic_pass_decision_support.csv",
        geographic_level="public-transport operating point",
        temporal_resolution="source-state snapshot",
        temporal_start="2026-09-20",
        temporal_end="2026-09-20",
        unit="EPSG:2056 point and categorical stop attributes",
        license="Free use with source attribution: Public transport stops, Federal Office of Transport",
        access_conditions="Public geo.admin.ch STAC/download service",
        transformation_applied="Checksum and STAC multihash verification; retain official VP/VPG passenger-stop types; calculate straight-line EPSG:2056 nearest neighbours from eligible supplied listing coordinates",
        quality_notes="The source also contains pure operating points, which are excluded; the all-stop subset contains aerial and surface modes; selected foreign points do not constitute complete foreign coverage",
        confidence_level="high for official current points; qualified for resort-access interpretation",
        manual_verification="28,967 operating points, 27,325 VP/VPG passenger stops, 1,717 train-capable stops and uniform 2026-09-20 source-state field checked",
    ))
    rows.append(blank_source(
        "BAV_PUBLIC_TRANSPORT_STOPS_2026_STAC",
        variable_name="public_transport_stop_stac_item_datetime|asset_url|asset_crs|asset_multihash",
        variable_description="Official STAC item metadata for the public-transport-stop CSV archive",
        source_organisation="Swiss Federal Office of Transport (BAV/OFT) via geo.admin.ch",
        source_dataset_name="STAC item ch.bav.haltestellen-oev/haltestellen-oev",
        source_page_url=configured["BAV_PUBLIC_TRANSPORT_STOPS_2026_STAC"]["url"],
        api_endpoint=configured["BAV_PUBLIC_TRANSPORT_STOPS_2026_STAC"]["url"],
        retrieval_method="HTTP GET with immutable JSON response and SHA-256 sidecar",
        retrieval_date=(bav_stop_stac or {}).get("retrieval_date", ""),
        original_file_name=raw_name(bav_stop_stac),
        local_raw_file=(bav_stop_stac or {}).get("raw_file", ""),
        processed_file="data_processed/resort_public_transport_stop_context.csv|reports/23_PUBLIC_TRANSPORT_STOP_CONTEXT.md",
        geographic_level="dataset metadata",
        temporal_resolution="asset metadata snapshot",
        temporal_start="2026-09-13",
        temporal_end="2026-09-13",
        unit="metadata",
        license="Open Government Data terms with source attribution",
        access_conditions="Public STAC API",
        transformation_applied="Item datetime, EPSG code, asset URL and multihash parsed and checked against the cached CSV archive",
        quality_notes="The STAC item datetime is retained separately from the archive's embedded 2026-09-20 data-state release note",
        confidence_level="high",
        manual_verification="STAC datetime 2026-09-13, EPSG:2056 and SHA-256 multihash match checked",
    ))
    rows.append(blank_source(
        "BAV_PUBLIC_TRANSPORT_STOPS_MODEL",
        variable_name="passenger_stop_type_definition|transport_mode_definition|train_mode_element_code",
        variable_description="Official model documentation distinguishing passenger stops from pure operating points and defining the transport-mode catalogue",
        source_organisation="Swiss Federal Office of Transport (BAV/OFT)",
        source_dataset_name="Minimal geodata model documentation, public transport stops GeoIV ID 98.2",
        source_page_url="https://www.bav.admin.ch/de/haltestellen-des-oeffentlichen-verkehrs-geoiv-id-982",
        direct_download_url=configured["BAV_PUBLIC_TRANSPORT_STOPS_MODEL"]["url"],
        retrieval_method="HTTP GET with immutable PDF response and SHA-256 sidecar",
        retrieval_date=(bav_stop_model or {}).get("retrieval_date", ""),
        original_file_name=raw_name(bav_stop_model),
        local_raw_file=(bav_stop_model or {}).get("raw_file", ""),
        processed_file="data_processed/resort_public_transport_stop_context.csv|reports/23_PUBLIC_TRANSPORT_STOP_CONTEXT.md",
        geographic_level="data-model definition",
        temporal_resolution="model version 2.1 dated 2025-02-03",
        temporal_start="2025-02-03",
        temporal_end="2025-02-03",
        unit="definition",
        license="See official BAV/OFT terms",
        access_conditions="Public official PDF",
        transformation_applied="Definitions for VP, VPG and elementary mode code B reviewed and implemented as exact code filters",
        quality_notes="The transport-mode attribute describes infrastructure suitability and is not necessarily proof of operation in the current timetable period",
        confidence_level="high",
        manual_verification="Model sections 2.1, 2.3 and 3.4 reviewed; VP/VPG and code B definitions checked",
    ))
    rows.append(blank_source(
        "DERIVED_PUBLIC_TRANSPORT_STOP_CONTEXT",
        variable_name="distance_to_nearest_public_transport_stop|distance_to_nearest_train_station|nearest_stop_attributes|cluster_distance_summary",
        variable_description="Qualified straight-line public-transport-stop and train-station proximity context for supplied resort listings and linked lift clusters",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C public-transport-stop proximity context",
        retrieval_method="Versioned deterministic Python transformation of checksum-verified BAV/OFT stop data",
        local_raw_file="config/path_c_analysis.json|data_processed/resort_point_municipality.csv",
        processed_file="data_processed/resort_public_transport_stop_context.csv|data_processed/path_c_cluster_public_transport_stop_context.csv|data_processed/magic_pass_decision_support.csv|reports/23_PUBLIC_TRANSPORT_STOP_CONTEXT.md",
        geographic_level="supplied resort listing point and linked lift cluster",
        temporal_resolution="BAV/OFT source state 2026-09-20; current supplied listing coordinates",
        temporal_start="2026-09-20",
        temporal_end="2026-09-20",
        unit="straight-line kilometres; identifiers; categorical stop attributes",
        transformation_applied="Restrict to 268 listing points inside a unique current Swiss municipality; calculate nearest VP/VPG passenger stop and nearest VP/VPG stop whose mode code contains B; aggregate min/median/max across eligible listing points",
        quality_notes="Not route distance, travel time, service frequency, timetable convenience, seasonal operation, a validated valley arrival node or destination catchment; all-mode nearest stops can be resort cableways/chairlifts",
        confidence_level="high for reproducibility; qualified current proximity context only",
        manual_verification="268/271 listings and 161/162 clusters complete; three French listings left missing; all 104 candidates retain usable cluster context; zero approval flags",
    ))
    rows.append(blank_source(
        "ASTRA_NATIONAL_ROAD_AXES_2026",
        variable_name="national_road_axis_geometry|axis_layer|axis_id|national_route_number|segment_name|designation|position_code|published_length",
        variable_description="Official Swiss national-road main, feeder, connection and ramp axes used for current straight-line proximity calculations",
        source_organisation="Swiss Federal Roads Office (FEDRO/ASTRA)",
        source_dataset_name="Axes of national routes, EPSG:2056 File Geodatabase",
        source_page_url=configured["ASTRA_NATIONAL_ROAD_AXES_COLLECTION"]["url"],
        direct_download_url=configured["ASTRA_NATIONAL_ROAD_AXES_2026"]["url"],
        api_endpoint=configured["ASTRA_NATIONAL_ROAD_AXES_2026_STAC"]["url"],
        retrieval_method="Configured HTTPS download with immutable File Geodatabase ZIP, SHA-256 sidecar and independently cached STAC item/collection metadata",
        retrieval_date=(astra_road_data or {}).get("retrieval_date", ""),
        original_file_name=raw_name(astra_road_data),
        local_raw_file=(astra_road_data or {}).get("raw_file", ""),
        processed_file="data_processed/resort_national_road_proximity_context.csv|data_processed/path_c_cluster_national_road_proximity_context.csv|data_processed/magic_pass_decision_support.csv",
        geographic_level="Swiss national-road axis feature",
        temporal_resolution="current source snapshot",
        temporal_start="2026-08-01",
        temporal_end="2026-08-01",
        unit="EPSG:2056 line geometry, metres and categorical segment attributes",
        license="Official STAC collection marks the asset proprietary; federal terms-of-use link retained",
        access_conditions="Public geo.admin.ch STAC/download service",
        transformation_applied="Verify archive SHA-256 against the STAC multihash; read all four line layers; validate feature counts, geometry validity and every published feature length; calculate Euclidean EPSG:2056 point-to-line distances",
        quality_notes="National-road axes are not an explicit motorway classification; current geometry does not establish a usable entrance, route distance, travel time or historical accessibility",
        confidence_level="high for official current national-road geometry; qualified for access interpretation",
        manual_verification="3,084 line features across four layers; 268 Swiss listing points covered; three French listings left missing; zero approval flags",
    ))
    rows.append(blank_source(
        "ASTRA_NATIONAL_ROAD_AXES_2026_STAC",
        variable_name="national_road_source_reference_datetime|asset_updated_datetime|asset_url|asset_crs|asset_multihash",
        variable_description="Official STAC item fixing the national-road-axis asset dates, URL, coordinate reference and checksum",
        source_organisation="Swiss Federal Roads Office (FEDRO/ASTRA) via geo.admin.ch",
        source_dataset_name="STAC item ch.astra.nationalstrassenachsen/nationalstrassenachsen",
        source_page_url=configured["ASTRA_NATIONAL_ROAD_AXES_2026_STAC"]["url"],
        api_endpoint=configured["ASTRA_NATIONAL_ROAD_AXES_2026_STAC"]["url"],
        retrieval_method="HTTP GET with immutable JSON response and SHA-256 sidecar",
        retrieval_date=(astra_road_stac or {}).get("retrieval_date", ""),
        original_file_name=raw_name(astra_road_stac),
        local_raw_file=(astra_road_stac or {}).get("raw_file", ""),
        processed_file="data_processed/resort_national_road_proximity_context.csv|reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md",
        geographic_level="dataset metadata",
        temporal_resolution="asset metadata snapshot",
        temporal_start="2026-08-01",
        temporal_end="2026-08-01",
        unit="metadata",
        license="See official federal terms-of-use link in the STAC collection",
        access_conditions="Public STAC API",
        transformation_applied="Reference datetime, update timestamp, EPSG code, asset URL and SHA-256 multihash parsed and checked against the cached archive",
        quality_notes="The 2026-08-01 STAC reference datetime is retained separately from the 2026-09-01 asset update and embedded data-status date",
        confidence_level="high",
        manual_verification="STAC datetime 2026-08-01, updated timestamp 2026-09-01, EPSG:2056 and SHA-256 multihash match checked",
    ))
    rows.append(blank_source(
        "ASTRA_NATIONAL_ROAD_AXES_COLLECTION",
        variable_name="dataset_definition|provider|maintenance_scope|temporal_extent|licence_link",
        variable_description="Official collection definition stating that FEDRO manages and updates national-route axes after construction or linear-reference changes",
        source_organisation="Swiss Federal Roads Office (FEDRO/ASTRA) via geo.admin.ch",
        source_dataset_name="STAC collection ch.astra.nationalstrassenachsen",
        source_page_url=configured["ASTRA_NATIONAL_ROAD_AXES_COLLECTION"]["url"],
        api_endpoint=configured["ASTRA_NATIONAL_ROAD_AXES_COLLECTION"]["url"],
        retrieval_method="HTTP GET with immutable JSON response and SHA-256 sidecar",
        retrieval_date=(astra_road_collection or {}).get("retrieval_date", ""),
        original_file_name=raw_name(astra_road_collection),
        local_raw_file=(astra_road_collection or {}).get("raw_file", ""),
        processed_file="reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md",
        geographic_level="dataset metadata",
        temporal_resolution="collection metadata snapshot",
        temporal_start="2026-08-01",
        temporal_end="2026-08-01",
        unit="metadata",
        license="Official STAC licence link retained",
        access_conditions="Public STAC API",
        transformation_applied="Provider, scope, temporal extent and EPSG summary checked before processing",
        quality_notes="The collection describes national routes and their axes; it does not define a motorway-only subset in the downloaded line-layer schema",
        confidence_level="high",
        manual_verification="Collection identifier, FEDRO provider, EPSG:2056 summary and exact temporal interval checked",
    ))
    rows.append(blank_source(
        "DERIVED_NATIONAL_ROAD_PROXIMITY_CONTEXT",
        variable_name="distance_to_nearest_national_road_main_axis|distance_to_nearest_national_road_network_axis|nearest_axis_attributes|cluster_distance_summary",
        variable_description="Qualified current straight-line national-road-axis proximity context for supplied resort listings and linked lift clusters",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C national-road-axis proximity context",
        retrieval_method="Versioned deterministic Python transformation of checksum-verified FEDRO/ASTRA line geometry",
        local_raw_file="config/path_c_analysis.json|data_processed/resort_point_municipality.csv",
        processed_file="data_processed/resort_national_road_proximity_context.csv|data_processed/path_c_cluster_national_road_proximity_context.csv|reports/national_road_proximity_candidate_summary.csv|data_processed/magic_pass_decision_support.csv|reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md",
        geographic_level="supplied resort listing point and linked lift cluster",
        temporal_resolution="FEDRO/ASTRA reference 2026-08-01; current supplied listing coordinates",
        temporal_start="2026-08-01",
        temporal_end="2026-08-01",
        unit="straight-line kilometres; identifiers and categorical axis attributes",
        transformation_applied="Restrict to 268 listing points inside a unique current Swiss municipality; calculate nearest official main axis and nearest line across all four axis layers; aggregate min/median/max across eligible listing points",
        quality_notes="Not motorway classification, network route, usable entrance, drive time, congestion, winter reliability or historical infrastructure; cross-border French road coverage intentionally left missing",
        confidence_level="high for reproducibility; qualified current proximity context only",
        manual_verification="268/271 listings and 161/162 clusters complete; 103/104 candidates complete; all-axis distance never exceeds main-axis distance; zero approval flags",
    ))
    competing_source_specs = {
        "ALPSPASS_2026_27_ROSTER": {
            "dataset": "Official AlpsPass regions and tariff page 2026/2027",
            "variables": "official_area_label|roster_version|benefit_tier|partner_free_ski_days",
            "description": "Official roster naming four AlpsPass core regions and seven partner regions with three free ski days in each partner region",
            "temporal": "2026/2027",
            "start": "2026-11-01",
            "end": "2027-10-31",
            "verification": "Four core and seven partner labels plus the three-free-ski-days wording checked in the cached page",
        },
        "ALPSPASS_2026_27_GTC": {
            "dataset": "AlpsPass General Terms and Conditions 2026/2027",
            "variables": "core_region_operator|included_infrastructure|gtc_validity",
            "description": "Official terms identifying operators and included infrastructure within the four AlpsPass core regions",
            "temporal": "terms valid from 2026-09-01",
            "start": "2026-09-01",
            "end": "",
            "verification": "Adelboden-Lenk, Jungfrau, Aletsch and Engelberg-Titlis operator wording checked in extracted PDF text",
        },
        "MEILENWEISS_CURRENT_ROSTER": {
            "dataset": "Official Meilenweiss FAQ current roster",
            "variables": "official_area_label|current_annual_pass_roster",
            "description": "Official retrieval-date list of all 17 regions in the Meilenweiss annual pass",
            "temporal": "current retrieval-date snapshot",
            "start": "2026-09-23",
            "end": "2026-09-23",
            "verification": "All 17 published region labels checked; no unsupported season label assigned",
        },
        "SCHNEEPASS_ZENTRALSCHWEIZ_2026_27_ROSTER": {
            "dataset": "Official Schneepass Zentralschweiz winter roster 2026/2027",
            "variables": "official_area_label|roster_version|winter_pass_inclusion",
            "description": "Official winter-season page listing all 15 included Schneepass Zentralschweiz regions",
            "temporal": "winter season 2026/2027",
            "start": "2026",
            "end": "2027",
            "verification": "Season wording and all 15 published region labels checked in the cached page",
        },
    }
    for source_id, spec in competing_source_specs.items():
        item = configured[source_id]
        metadata = competing_pass_metadata[source_id]
        rows.append(blank_source(
            source_id,
            variable_name=spec["variables"],
            variable_description=spec["description"],
            source_organisation=item["organisation"],
            source_dataset_name=spec["dataset"],
            source_page_url=item["url"],
            direct_download_url=item["url"],
            retrieval_method="Configured HTTPS download with immutable response and SHA-256 metadata sidecar",
            retrieval_date=(metadata or {}).get("retrieval_date", ""),
            original_file_name=raw_name(metadata),
            local_raw_file=(metadata or {}).get("raw_file", ""),
            processed_file="config/competing_pass_roster_2026_27.csv|data_processed/resort_competing_pass_context.csv|data_processed/path_c_cluster_competing_pass_context.csv|data_processed/magic_pass_decision_support.csv|reports/31_COMPETING_PASS_CONTEXT.md",
            geographic_level="official pass area / supplied resort listing link",
            temporal_resolution=spec["temporal"],
            temporal_start=spec["start"],
            temporal_end=spec["end"],
            unit="named pass area and benefit category",
            license="Official public operator material; source terms apply",
            access_conditions="Public official webpage or PDF",
            transformation_applied="Checksum verification; source label and scope-token validation; explicit versioned resort-ID links without runtime fuzzy matching",
            quality_notes="Current roster scope only; area non-link does not prove absence from every competing pass; historical competition is not reconstructed",
            confidence_level="high for the published roster; qualified for directory entity links",
            manual_verification=spec["verification"],
        ))
    rows.append(blank_source(
        "DERIVED_COMPETING_PASS_CONTEXT",
        variable_name="competing_pass_roster_link|benefit_tier|cluster_linked_listing_share|competing_pass_scope_status",
        variable_description="Qualified listing- and cluster-level context from three official current competing-pass rosters",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C competing-pass roster context",
        retrieval_method="Versioned deterministic Python expansion of explicit reviewed resort-ID links",
        local_raw_file="config/competing_pass_roster_2026_27.csv",
        processed_file="data_processed/resort_competing_pass_context.csv|data_processed/path_c_cluster_competing_pass_context.csv|reports/competing_pass_candidate_summary.csv|data_processed/magic_pass_decision_support.csv|reports/31_COMPETING_PASS_CONTEXT.md",
        geographic_level="official pass area, supplied resort listing and linked lift cluster",
        temporal_resolution="AlpsPass and Schneepass 2026/2027; Meilenweiss retrieval-date snapshot 2026-09-23",
        temporal_start="2026",
        temporal_end="2027",
        unit="identifiers, categories, counts, shares and flags",
        transformation_applied="Validate official roster cardinalities and source tokens; expand only explicit stable resort-ID links; aggregate linked and unlinked listings separately within preserved lift clusters",
        quality_notes="A non-link is not verified competing-pass absence; mixed clusters retain partial status; snapshots are not historical pre-treatment competition measures",
        confidence_level="high for reproducibility; qualified current roster context only",
        manual_verification="43 official areas, 55 linked listings, 29 linked clusters and 22 linked apparent candidates; zero absence-verification or causal approval flags",
    ))
    rows.append(blank_source(
        "DERIVED_PATH_C_NETWORK_CONTEXT",
        variable_name="cluster_pair_distance|directory_cluster_density|published_ski_area_context|resolved_magic_network_density|reviewed_competing_pass_network_density",
        variable_description="Current straight-line proximity and radius counts among preserved directory-linked lift clusters and reviewed pass-network links",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C ski-cluster and reviewed pass-network context",
        retrieval_method="Deterministic Python derivation from the existing cluster feature matrix and reviewed competing-pass links",
        local_raw_file="data_processed/path_c_resort_cluster_features.csv|data_processed/path_c_cluster_competing_pass_context.csv",
        processed_file="data_processed/path_c_cluster_network_context.csv|reports/path_c_cluster_network_pairs.csv|reports/network_context_candidate_summary.csv|data_processed/magic_pass_decision_support.csv|reports/32_PATH_C_NETWORK_CONTEXT.md",
        geographic_level="ordered lift-cluster pair and focal linked lift cluster",
        temporal_resolution="current/undated supplied directory plus current reviewed pass-network snapshots",
        temporal_start="",
        temporal_end="2026-09-23",
        unit="great-circle kilometres, counts, shares and summed published directory kilometres",
        transformation_applied="Calculate all 26,082 ordered non-self great-circle cluster pairs from median supplied listing coordinates; count other directory, resolved current Magic and reviewed competing-pass-linked clusters within 25/50 km; retain observed/missing ski-area contributors",
        quality_notes="Clusters are not validated independent commercial domains; median coordinates may be artificial; straight-line distance ignores terrain and transport; directory ski area may overlap; pass networks are current rather than historical",
        confidence_level="high for reproducibility; qualified current directory/network context only",
        manual_verification="162 clusters, 26,082 unique ordered non-self pairs and 104 candidates; focal cluster excluded from every count; zero historical or causal approvals",
    ))
    rows.append(blank_source(
        "DERIVED_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY",
        variable_name="within_cluster_listing_point_spread|cross_cluster_listing_pair_distance_rules|network_count_distance_rule_sensitivity",
        variable_description="Geographic spread audit of preserved lift clusters and minimum/median/representative/maximum listing-point distance sensitivity",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C cluster geography and network-distance sensitivity",
        retrieval_method="Deterministic Python derivation from all supplied listing coordinates without rebuilding the existing clusters",
        local_raw_file="data_processed/resort_master.csv|data_processed/path_c_resort_cluster_features.csv|data_processed/path_c_cluster_competing_pass_context.csv",
        processed_file="data_processed/path_c_cluster_geographic_sensitivity.csv|reports/path_c_cluster_distance_rule_pairs.csv|reports/cluster_geography_candidate_summary.csv|data_processed/magic_pass_decision_support.csv|reports/33_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY.md",
        geographic_level="supplied listing point, preserved linked lift cluster and ordered pair of distinct linked clusters",
        temporal_resolution="current/undated supplied listing coordinates and current reviewed pass-network links",
        temporal_start="",
        temporal_end="2026-09-23",
        unit="great-circle kilometres, counts, categories and flags",
        transformation_applied="Measure within-cluster pairwise listing-point spread; calculate minimum, median and maximum distance across every cross-cluster listing-point pair; reproduce the coordinate-wise-median baseline; compare 25/50 km directory and reviewed-network counts",
        quality_notes="Existing clusters are preserved but not certified as independent commercial domains; no distance rule is uniquely correct; straight-line distance ignores terrain, transport, visitor behaviour and historical changes",
        confidence_level="high for reproducibility; qualified entity-definition and measurement sensitivity only",
        manual_verification="162 clusters, 271 listing points and 26,082 ordered non-self cluster pairs; all distance bounds and baseline reproduction checked; zero geographic-coherence or feature approvals",
    ))
    rows.append(blank_source(
        "SKI_GTFS_TIMETABLE_2026_WINTER_20260207",
        variable_name="scheduled_stop_times|trips|routes|service_calendar|transfers|stop_coordinates",
        variable_description="Official all-Switzerland GTFS Static timetable snapshot used for scheduled municipality-to-ski-destination routing",
        source_organisation="Business office SKI on behalf of the Swiss Federal Office of Transport (BAV/OFT)",
        source_dataset_name="Timetable 2026 (GTFS2020), build 20260207",
        source_page_url="https://data.opentransportdata.swiss/en/dataset/timetable-2026-gtfs2020",
        direct_download_url=configured["SKI_GTFS_TIMETABLE_2026_WINTER_20260207"]["url"],
        retrieval_method="Configured HTTPS download with immutable ZIP, SHA-256 sidecar and collection log",
        retrieval_date=(ski_gtfs_data or {}).get("retrieval_date", ""),
        original_file_name=raw_name(ski_gtfs_data),
        local_raw_file=(ski_gtfs_data or {}).get("raw_file", ""),
        processed_file="data_processed/treatment_municipality_public_transport_journey_samples.csv|data_processed/treatment_municipality_public_transport_journey_context.csv|reports/public_transport_journey_nodes.csv|reports/24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md",
        geographic_level="Swiss public-transport stops, routes and trips",
        temporal_resolution="published static timetable with sampled weekday and Saturday requests",
        temporal_start="2025-12-14",
        temporal_end="2026-12-12",
        unit="scheduled service and time",
        license="Open Data Mobility Switzerland terms of use",
        access_conditions="Public official dataset",
        transformation_applied="Checksum verification; Swiss platform IDs collapsed to base stops; active service calendars applied for 2026-02-04 and 2026-02-07; generic transfers and at most six vehicle legs routed",
        quality_notes="Static schedule only; no delays, cancellations, fares, crowding or unlisted walking; route/trip-specific transfer rules are reported but not separately modelled",
        confidence_level="high for reproducibility; qualified for current scheduled access only",
        manual_verification="Feed version, validity dates, 16,551,962 stop-time rows and selected node coverage checked; zero causal approvals",
    ))
    rows.append(blank_source(
        "SKI_GTFS_TIMETABLE_ARCHIVE_INDEX",
        variable_name="historical_gtfs_snapshot_url|timetable_year|snapshot_build",
        variable_description="Official archive index used to identify a winter GTFS snapshot for each first Magic Pass exposure timetable year",
        source_organisation="Business office SKI on behalf of the Swiss Federal Office of Transport (BAV/OFT)",
        source_dataset_name="GTFS timetable data archive",
        source_page_url="https://archive.opentransportdata.swiss/timetable_gtfs_archive.htm",
        api_endpoint="https://archive.opentransportdata.swiss/timetable_gtfs.php",
        retrieval_method="Manual/read-only archive-index inspection; automated project collector stopped because robots.txt disallows it",
        retrieval_date="2026-09-22",
        local_raw_file="not cached; robots.txt restriction respected",
        processed_file="config/public_transport_historical_audit.json|reports/public_transport_historical_audit_plan.csv|reports/25_PUBLIC_TRANSPORT_HISTORICAL_AUDIT.md",
        geographic_level="Swiss national timetable archive",
        temporal_resolution="timetable-year snapshots",
        temporal_start="2018",
        temporal_end="2026",
        unit="archive URL and build date",
        license="Open Data Mobility Switzerland terms of use",
        access_conditions="Public index; automated cache disallowed by robots.txt at review date",
        transformation_applied="Select the official snapshot closest to 7 February of each represented first-exposure winter",
        quality_notes="URL availability is not service stability; historical ZIP contents have not yet been downloaded or routed",
        confidence_level="high for identified archive URLs; none yet for line stability",
        manual_verification="Seven timetable-year URLs identified; zero historical component-service comparisons completed",
    ))
    rows.append(blank_source(
        "DERIVED_PUBLIC_TRANSPORT_JOURNEY_CONTEXT",
        variable_name="scheduled_journey_minutes|initial_wait_minutes|generalized_elapsed_minutes|vehicle_legs|transfers|transport_modes|sample_coverage",
        variable_description="Qualified scheduled public-transport journey context between each hotel municipality main stop and each reviewed ski destination",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Treatment municipality public-transport journey context",
        retrieval_method="Deterministic routing of checksum-verified official GTFS Static and OFT/BAV stop data",
        local_raw_file="config/path_c_analysis.json",
        processed_file="data_processed/treatment_municipality_public_transport_journey_samples.csv|data_processed/treatment_municipality_public_transport_journey_context.csv|reports/public_transport_journey_nodes.csv|reports/public_transport_journey_context_summary.json|reports/24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md",
        geographic_level="reviewed destination by hotel municipality, with component stop nodes",
        temporal_resolution="winter-2026 weekday/Saturday timetable samples",
        temporal_start="2026-02-04",
        temporal_end="2026-02-07",
        unit="minutes, legs, modes and coverage shares",
        transformation_applied="Choose municipality main stops by reference-day departure count; choose nearby served ground stops inside component municipalities; route five morning and seven return requests on two reference days; retain fastest component",
        quality_notes="Current arrival nodes have a versioned name/mode/municipality/distance review; door-to-lift walking and historical continuity remain unverified; 480-minute and six-vehicle limits apply",
        confidence_level="high for reproducibility; descriptive current context only",
        manual_verification="49,104 unique samples, no negative feasible durations, 2,046 destination-municipality pairs and zero causal approvals checked; see separate arrival-node review",
    ))
    rows.append(blank_source(
        "DERIVED_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW",
        variable_name="review_class|review_basis|user_fallback_rule|reference_day_availability|descriptive_routing_node_approved",
        variable_description="Versioned review of current destination arrival-node names, modes, municipalities, point distances and sampled-service-day presence",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Public-transport arrival-node review",
        retrieval_method="Deterministic validation of the reviewed node registry against the generated OFT/BAV and GTFS destination-node table",
        local_raw_file="config/public_transport_arrival_node_review.csv",
        processed_file="reports/public_transport_arrival_node_review.csv|reports/public_transport_arrival_node_review_summary.json|reports/26_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW.md",
        geographic_level="reviewed destination component arrival node",
        temporal_resolution="current official node plus winter-2026 reference-day availability",
        temporal_start="2026-02-04",
        temporal_end="2026-02-07",
        unit="review class, status and distance",
        transformation_applied="Exact component/stop-key match; require bus/train mode, matching current municipality and at most 2.1 km from the supplied component point; classify explicit village-centre fallbacks",
        quality_notes="Does not establish door-to-lift walking, accessibility for every traveller, historical node continuity or line stability",
        confidence_level="high for versioned current descriptive review; none for historical or causal use",
        manual_verification="15 of 15 nodes accepted for descriptive routing; six village/local-centre proxies explicit; one sampled-weekday availability warning; zero historical or causal approvals",
    ))
    rows.append(blank_source(
        "DERIVED_PUBLIC_TRANSPORT_HISTORICAL_AUDIT",
        variable_name="first_exposure_winter_timetable_year|historical_gtfs_anchor_url|historical_service_comparison_status",
        variable_description="Explicit plan and completion gate for comparing current destination access nodes with official historical winter GTFS feeds",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Historical public-transport timetable audit plan",
        retrieval_method="Deterministic join of reviewed entry seasons, selected destination nodes and reviewed official archive URLs",
        local_raw_file="config/public_transport_historical_audit.json",
        processed_file="reports/public_transport_historical_audit_plan.csv|reports/public_transport_historical_audit_summary.json|reports/25_PUBLIC_TRANSPORT_HISTORICAL_AUDIT.md",
        geographic_level="reviewed destination component arrival node",
        temporal_resolution="first Magic Pass exposure winter",
        temporal_start="2018",
        temporal_end="2026",
        unit="audit status and archive reference",
        transformation_applied="Map first-entry season to exposure-winter timetable year and its selected official archive snapshot",
        quality_notes="Historical service comparison remains unexecuted; archive availability is not evidence of unchanged lines or journey times",
        confidence_level="reproducible audit plan; no historical stability conclusion",
        manual_verification="15 component nodes have an official anchor URL; zero historical service comparisons and zero causal approvals",
    ))
    slf_metadata = {
        source_id: cached_metadata(source_id)
        for source_id in [
            "SLF_DATA_SERVICE",
            "SLF_IMIS_README",
            "SLF_IMIS_STATIONS",
            "SLF_IMIS_DAILY_INDEX",
            "SLF_IMIS_DAILY_SNOW",
        ]
    }
    for source_id, dataset_name, variables, processed, level, temporal, notes in [
        (
            "SLF_DATA_SERVICE",
            "SLF data service terms and access documentation",
            "licence|attribution|data_quality_conditions",
            "reports/06_SNOW_SOURCE_AND_PROXY.md",
            "documentation",
            "retrieval snapshot",
            "CC BY 4.0; SLF attribution and DOI are required; some source data are raw and not regularly corrected",
        ),
        (
            "SLF_IMIS_README",
            "SLF historical measurement-data documentation",
            "HS_definition|HN_1D_definition|units|aggregation_time",
            "data_processed/slf_snow_station_month.csv|data_processed/slf_snow_station_winter.csv",
            "station measurement documentation",
            "archive documentation snapshot",
            "Daily HS is the 24-hour median at 06:00 UTC; HN_1D is modelled by SNOWPACK",
        ),
        (
            "SLF_IMIS_STATIONS",
            "SLF IMIS station catalogue",
            "station_code|label|longitude|latitude|elevation|station_type|active",
            "data_processed/resort_snow_station_crosswalk.csv",
            "point station",
            "station metadata snapshot",
            "Station locations are avalanche-monitoring sites and not ski-slope observations",
        ),
        (
            "SLF_IMIS_DAILY_INDEX",
            "SLF station-level daily snow file directory",
            "station_file_inventory",
            "reports/06_SNOW_SOURCE_AND_PROXY.md",
            "file inventory",
            "retrieval snapshot",
            "Directory snapshot supports file-level audit; consolidated file is used for processing",
        ),
        (
            "SLF_IMIS_DAILY_SNOW",
            "SLF IMIS historical daily snow values",
            "snow_depth_cm|modeled_new_snow_cm",
            "data_processed/slf_snow_station_month.csv|data_processed/slf_snow_station_winter.csv|data_processed/resort_snow_vulnerability.csv|data_processed/destination_snow_month.csv",
            "mountain weather station",
            "daily",
            "Negative snow depths are physically invalid and remain raw but missing in derived values; no imputation; station proxies are not direct piste measurements",
        ),
    ]:
        item = configured[source_id]
        metadata = slf_metadata[source_id]
        rows.append(blank_source(
            source_id,
            variable_name=variables,
            variable_description=item["description"],
            source_organisation=item["organisation"],
            source_dataset_name=dataset_name,
            source_page_url=(
                configured["SLF_DATA_SERVICE"]["url"]
                if source_id != "SLF_DATA_SERVICE"
                else item["url"]
            ),
            direct_download_url=item["url"],
            retrieval_method="HTTP GET with immutable response and SHA-256 sidecar",
            retrieval_date=metadata.get("retrieval_date", "") if metadata else "",
            original_file_name=raw_name(metadata),
            local_raw_file=metadata.get("raw_file", "") if metadata else "",
            processed_file=processed,
            geographic_level=level,
            temporal_resolution=temporal,
            temporal_start=("1992-10-01" if source_id == "SLF_IMIS_DAILY_SNOW" else ""),
            temporal_end=("2026-09-13" if source_id == "SLF_IMIS_DAILY_SNOW" else "2026"),
            unit=("centimetres" if source_id == "SLF_IMIS_DAILY_SNOW" else "metadata"),
            license="CC BY 4.0",
            access_conditions="Public static archive; cite SLF and DOI 10.16904/envidat.406 when IMIS data are used scientifically",
            transformation_applied=(
                "Physical nonnegative validation; monthly and November-April aggregation; 80% coverage gates; nearest eligible-station proxy with distance/elevation diagnostics"
                if source_id == "SLF_IMIS_DAILY_SNOW"
                else "Cached and used for documentation or exact station metadata"
            ),
            quality_notes=notes,
            confidence_level=(
                "high for source authenticity; mixed for resort-slope representativeness"
                if source_id in {"SLF_IMIS_STATIONS", "SLF_IMIS_DAILY_SNOW"}
                else "high for official documentation"
            ),
            manual_verification="schema, terms, units, station types, temporal coverage, missingness, and physical signs checked",
        ))

    weather_metadata_ids = [
        "METEOSWISS_SMN_DOCUMENTATION",
        "METEOSWISS_SMN_COLLECTION",
        "METEOSWISS_SMN_PARAMETERS",
        "METEOSWISS_SMN_STATIONS",
        "METEOSWISS_SMN_INVENTORY",
        "METEOSWISS_SMN_ITEMS",
    ]
    weather_details = {
        "METEOSWISS_SMN_DOCUMENTATION": (
            "SwissMetNet Open Data documentation",
            "data_structure|access|licence|aggregation_guidance",
            "reports/07_WEATHER_PROXY.md",
            "documentation",
        ),
        "METEOSWISS_SMN_COLLECTION": (
            "SwissMetNet FSDI STAC collection metadata",
            "collection_metadata|asset_templates|licence_links",
            "reports/07_WEATHER_PROXY.md",
            "collection metadata",
        ),
        "METEOSWISS_SMN_PARAMETERS": (
            "SwissMetNet parameter catalogue",
            "parameter_shortname|description|granularity|unit",
            "data_processed/meteoswiss_station_month.csv",
            "parameter metadata",
        ),
        "METEOSWISS_SMN_STATIONS": (
            "SwissMetNet station catalogue",
            "station_abbr|station_name|coordinates|elevation|station_type",
            "data_processed/resort_weather_station_crosswalk.csv",
            "point station",
        ),
        "METEOSWISS_SMN_INVENTORY": (
            "SwissMetNet station-parameter inventory",
            "station_abbr|parameter_shortname|data_since|data_till|owner",
            "data_processed/resort_weather_station_crosswalk.csv",
            "station-parameter inventory",
        ),
        "METEOSWISS_SMN_ITEMS": (
            "SwissMetNet STAC station-item response",
            "station_items|daily_asset_links",
            "reports/07_WEATHER_PROXY.md",
            "station asset catalogue snapshot",
        ),
    }
    for source_id in weather_metadata_ids:
        item = configured[source_id]
        metadata = cached_metadata(source_id)
        dataset_name, variables, processed, level = weather_details[source_id]
        rows.append(blank_source(
            source_id,
            variable_name=variables,
            variable_description=item["description"],
            source_organisation=item["organisation"],
            source_dataset_name=dataset_name,
            source_page_url=configured["METEOSWISS_SMN_DOCUMENTATION"]["url"],
            direct_download_url=item["url"],
            retrieval_method="HTTP GET with immutable response and SHA-256 sidecar",
            retrieval_date=metadata.get("retrieval_date", "") if metadata else "",
            original_file_name=raw_name(metadata),
            local_raw_file=metadata.get("raw_file", "") if metadata else "",
            processed_file=processed,
            geographic_level=level,
            temporal_resolution="retrieval snapshot",
            temporal_start="",
            temporal_end="2026",
            unit="metadata",
            license="Swiss Open Government Data terms; source acknowledgement required",
            access_conditions="Public static files and FSDI STAC API",
            transformation_applied="Cached and used for parameter definitions, station eligibility, coordinates, and exact official asset discovery",
            quality_notes=(
                "The cached STAC item response is a discovery snapshot; exact selected asset URLs and checksums are recorded separately"
                if source_id == "METEOSWISS_SMN_ITEMS"
                else "Official metadata snapshot; source catalogue can be updated after retrieval"
            ),
            confidence_level="high for official metadata",
            manual_verification="schema, parameter units, station coordinates/elevation, inventory dates, and asset structure checked",
        ))

    selected_weather_sources = json.loads(
        (ROOT / "config" / "meteoswiss_selected_station_files.json").read_text(
            encoding="utf-8"
        )
    )
    selected_weather_metadata = [
        cached_metadata(item["source_id"]) for item in selected_weather_sources
    ]
    if any(metadata is None for metadata in selected_weather_metadata):
        raise FileNotFoundError("A selected MeteoSwiss daily file is not cached")
    weather_first = selected_weather_metadata[0]
    rows.append(blank_source(
        "METEOSWISS_SMN_DAILY_SELECTED",
        variable_name="tre200d0|tre200dn|tre200dx|rre150d0",
        variable_description="Official daily mean/minimum/maximum air temperature and 06:00-to-06:00 UTC precipitation for seven selected SwissMetNet stations",
        source_organisation="Federal Office of Meteorology and Climatology MeteoSwiss",
        source_dataset_name="SwissMetNet selected daily historical and recent station files",
        source_page_url=configured["METEOSWISS_SMN_DOCUMENTATION"]["url"],
        direct_download_url="https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/",
        retrieval_method="HTTP GET of seven historical and seven recent static CSV files; immutable responses and SHA-256 sidecars",
        retrieval_date=max(
            metadata["retrieval_date"] for metadata in selected_weather_metadata
        ),
        original_file_name=raw_name(weather_first),
        local_raw_file="data_external/source_evidence/METEOSWISS_SMN_DAILY_*.csv",
        processed_file="data_processed/meteoswiss_station_month.csv|data_processed/resort_weather_station_crosswalk.csv|data_processed/destination_weather_month.csv|data_processed/destination_month_panel.csv",
        geographic_level="SwissMetNet point station used as regional resort proxy",
        temporal_resolution="daily source; monthly analytical aggregation",
        temporal_start="2013-01-01 analysis window",
        temporal_end="2026-03-31 analysis window",
        unit="degrees Celsius; millimetres",
        license="Swiss Open Government Data terms; source acknowledgement required",
        access_conditions="Public static station files",
        transformation_applied="Exact historical/recent concatenation; monthly aggregation; 80% coverage gate; station-specific 2013-2025 calendar-month normals; nearest eligible-station crosswalk; no imputation",
        quality_notes="Two station-months fail precipitation coverage and remain missing; precipitation uses 06:00 UTC to 06:00 UTC next day; regional stations do not directly represent pistes",
        confidence_level="high for official observations; mixed for local piste representativeness",
        manual_verification="checksums, schema, duplicate dates, physical signs, temperature ordering, daily/monthly coverage, distance, and elevation gaps checked",
        notes="Fourteen exact raw-file URLs, source IDs and suffixes are enumerated in config/meteoswiss_selected_station_files.json; the local_raw_file glob identifies the immutable cache files",
    ))
    alternative_weather_sources = json.loads(
        (ROOT / "config" / "meteoswiss_weather_sensitivity_station_files.json").read_text(
            encoding="utf-8"
        )
    )
    required_alternative_codes = {
        "CHD", "EVO", "GIH", "INT", "LAG", "MVE", "ORO", "SIO", "THU", "ZER"
    }
    all_weather_file_specs = alternative_weather_sources + selected_weather_sources
    sensitivity_weather_specs = [
        item
        for item in all_weather_file_specs
        if any(f"_{code}_" in item["source_id"] for code in required_alternative_codes)
    ]
    sensitivity_weather_metadata = [
        cached_metadata(item["source_id"]) for item in sensitivity_weather_specs
    ]
    if len(sensitivity_weather_specs) != 20 or any(
        metadata is None for metadata in sensitivity_weather_metadata
    ):
        raise FileNotFoundError(
            "The ten-station MeteoSwiss alternative-sensitivity source set is incomplete"
        )
    rows.append(blank_source(
        "METEOSWISS_SMN_DAILY_ALTERNATIVE_SELECTED",
        variable_name="tre200d0|tre200dn|tre200dx|rre150d0",
        variable_description="Official daily temperature and precipitation for the ten SwissMetNet stations used as next-nearest alternatives across reviewed components",
        source_organisation="Federal Office of Meteorology and Climatology MeteoSwiss",
        source_dataset_name="SwissMetNet next-nearest alternative daily station files",
        source_page_url=configured["METEOSWISS_SMN_DOCUMENTATION"]["url"],
        direct_download_url="https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/",
        retrieval_method="Reuse six cached primary historical/recent files and HTTP GET of seven additional historical plus seven recent static CSV files; immutable responses and SHA-256 sidecars",
        retrieval_date=max(
            metadata["retrieval_date"] for metadata in sensitivity_weather_metadata
        ),
        original_file_name="20 station-period CSV files",
        local_raw_file="data_external/source_evidence/METEOSWISS_SMN_DAILY_*.csv",
        processed_file="data_processed/meteoswiss_alternative_station_month.csv|reports/weather_station_alternative_sensitivity.csv|data_processed/destination_weather_alternative_sensitivity.csv|reports/weather_destination_alternative_summary.csv|reports/34_WEATHER_STATION_SENSITIVITY.md",
        geographic_level="SwissMetNet point station used as a next-nearest regional resort proxy",
        temporal_resolution="daily source; monthly analytical aggregation",
        temporal_start="2013-01-01 analysis window",
        temporal_end="2026-03-31 analysis window",
        unit="degrees Celsius; millimetres",
        license="Swiss Open Government Data terms; source acknowledgement required",
        access_conditions="Public static station files",
        transformation_applied="Next-nearest distinct eligible station assignment; exact historical/recent concatenation; primary 80% monthly coverage gate and station-specific 2013-2025 calendar-month normals; no imputation",
        quality_notes="Same-network assignment sensitivity rather than independent gridded validation; regional stations do not directly represent pistes; next-nearest stations can differ in elevation and terrain",
        confidence_level="high for official observations; qualified for assignment sensitivity only",
        manual_verification="Twenty exact cached files cover all ten required alternatives; checksums, schema, duplicate dates, physical signs, temperature ordering, monthly coverage and station assignment checked",
        notes="Fourteen newly required files are enumerated in config/meteoswiss_weather_sensitivity_station_files.json; EVO, INT and MVE files are reused from the primary configuration",
    ))
    rows.append(blank_source(
        "DERIVED_WEATHER_STATION_SENSITIVITY",
        variable_name="next_nearest_weather_station|temperature_anomaly_agreement|precipitation_anomaly_agreement|alternative_destination_month",
        variable_description="Selected-versus-next-nearest eligible SwissMetNet station sensitivity for reviewed components and destinations",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="SwissMetNet regional weather alternative-station sensitivity",
        retrieval_method="Deterministic Python reassignment and monthly comparison",
        local_raw_file="config/meteoswiss_weather_sensitivity_station_files.json|config/meteoswiss_selected_station_files.json",
        processed_file="data_processed/meteoswiss_alternative_station_month.csv|reports/weather_station_alternative_sensitivity.csv|data_processed/destination_weather_alternative_sensitivity.csv|reports/weather_destination_alternative_summary.csv|reports/34_WEATHER_STATION_SENSITIVITY.md",
        geographic_level="reviewed resort component, SwissMetNet station and reviewed destination",
        temporal_resolution="monthly 2013-01 through 2026-03 plus component/destination summary",
        temporal_start="2013-01-01",
        temporal_end="2026-03-31",
        unit="degrees Celsius, millimetres, correlations, counts and flags",
        transformation_applied="Select next-nearest distinct eligible station; apply the primary daily validation, 80% monthly coverage and station-specific normals; compare component and destination anomaly series on common complete months",
        quality_notes="Not independent gridded validation or piste microclimate; descriptive agreement thresholds are review categories, not causal gates",
        confidence_level="high for reproducibility; qualified regional-station sensitivity only",
        manual_verification="15 component comparisons, 11 destination summaries and 1,749 destination-month rows; zero causal approvals",
    ))

    gridded_weather_sources = json.loads(
        (ROOT / "config" / "meteoswiss_gridded_weather_files.json").read_text(
            encoding="utf-8"
        )
    )
    gridded_weather_metadata = {
        item["source_id"]: cached_metadata(item["source_id"])
        for item in gridded_weather_sources
    }
    if len(gridded_weather_sources) != 39 or any(
        metadata is None for metadata in gridded_weather_metadata.values()
    ):
        raise FileNotFoundError(
            "The MeteoSwiss gridded-weather source set is incomplete"
        )
    gridded_asset_specs = [
        item
        for item in gridded_weather_sources
        if item["source_id"].startswith("METEOSWISS_GRID_")
    ]
    if len(gridded_asset_specs) != 32 or any(
        gridded_weather_metadata[item["source_id"]]["sha256"]
        != item.get("expected_sha256")
        for item in gridded_asset_specs
    ):
        raise RuntimeError(
            "MeteoSwiss gridded-weather assets do not match official STAC hashes"
        )
    gridded_retrieval_date = max(
        metadata["retrieval_date"]
        for metadata in gridded_weather_metadata.values()
    )
    rows.append(blank_source(
        "METEOSWISS_TABSM_RHIRESM_MONTHLY_GRID_2013_202603",
        variable_name="TabsM|RhiresM",
        variable_description="Official 1 km LV95 monthly mean-temperature and precipitation spatial analyses for 2013-01 through 2026-03",
        source_organisation="Federal Office of Meteorology and Climatology MeteoSwiss",
        source_dataset_name="Spatial Climate Analyses — TabsM v1.4 and RhiresM v2.0",
        source_page_url="https://data.geo.admin.ch/browser/index.html#/collections/ch.meteoschweiz.ogd-surface-derived-grid",
        direct_download_url="https://data.geo.admin.ch/ch.meteoschweiz.ogd-surface-derived-grid/",
        api_endpoint="https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-surface-derived-grid",
        api_parameters="archive-ch plus 202601-ch, 202602-ch and 202603-ch items; TabsM/RhiresM ch01r.swiss.lv95 assets",
        retrieval_method="HTTP GET of 26 annual and six current-month NetCDF assets; every SHA-256 matched to the official STAC multihash",
        retrieval_date=gridded_retrieval_date,
        original_file_name="32 TabsM/RhiresM NetCDF assets",
        local_raw_file="data_external/source_evidence/METEOSWISS_GRID_*.nc",
        processed_file="data_processed/meteoswiss_gridded_component_month.csv|reports/weather_gridded_component_comparison.csv|data_processed/destination_weather_gridded_sensitivity.csv|reports/weather_gridded_destination_summary.csv|reports/35_WEATHER_GRIDDED_SENSITIVITY.md",
        geographic_level="regular 1 km cell centres in MeteoSwiss ch01r.swiss.lv95 grid",
        temporal_resolution="direct monthly spatial analysis",
        temporal_start="2013-01-01",
        temporal_end="2026-03-01",
        unit="degrees Celsius; millimetres",
        license="CC BY / Swiss Open Government Data terms; source acknowledgement required",
        access_conditions="Public static NetCDF assets exposed through the federal STAC catalogue",
        transformation_applied="Nearest cell valid for both products at each reviewed component; cell/calendar-month 2013-2025 analytical normals; unique-cell destination mean; no imputation",
        quality_notes="Station-informed grids rather than an independent measurement network; 1 km spacing exceeds effective precipitation resolution; high-elevation winter precipitation undercatch and Alpine interpolation uncertainty remain",
        confidence_level="high for official gridded product integrity; qualified for regional-weather sensitivity only",
        manual_verification="32/32 asset SHA-256 values match STAC; CF-1.8 schema, 1 km LV95 coordinates, product versions, units, time axes, masks and component-cell distances checked",
        notes="Exact asset URLs, official hashes, STAC records and documentation sources are enumerated in config/meteoswiss_gridded_weather_files.json",
    ))
    rows.append(blank_source(
        "METEOSWISS_SPATIAL_CLIMATE_ANALYSIS_DOCUMENTATION",
        variable_name="TabsM_method|RhiresM_method|grid_spacing|accuracy_limits",
        variable_description="Official product documentation and STAC discovery metadata for MeteoSwiss monthly spatial climate analyses",
        source_organisation="Federal Office of Meteorology and Climatology MeteoSwiss",
        source_dataset_name="TabsM and RhiresM product documentation plus surface-derived-grid STAC metadata",
        source_page_url="https://www.meteoswiss.admin.ch/services-and-publications/service/open-data.html",
        direct_download_url="https://www.meteoswiss.admin.ch/dam/",
        api_endpoint="https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-surface-derived-grid",
        retrieval_method="HTTP GET with immutable responses and SHA-256 sidecars",
        retrieval_date=gridded_retrieval_date,
        original_file_name="ProdDoc_TabsM.pdf|ProdDoc_RhiresM.pdf|five STAC JSON records",
        local_raw_file="data_external/source_evidence/METEOSWISS_*GRID*STAC_*.json|data_external/source_evidence/METEOSWISS_*DOCUMENTATION_*.pdf",
        processed_file="reports/35_WEATHER_GRIDDED_SENSITIVITY.md",
        geographic_level="Swiss spatial climate analysis grid",
        temporal_resolution="product-method documentation and retrieval-time catalogue snapshots",
        unit="not applicable",
        license="CC BY / Swiss Open Government Data terms",
        access_conditions="Public documentation and STAC API",
        transformation_applied="Product definitions, methods, versions, grid and limitations transcribed into guarded analytical interpretation",
        quality_notes="RhiresM documentation notes high-elevation/winter undercatch and effective resolution coarser than 1 km; TabsM omits some local land/lake effects",
        confidence_level="high for product definitions and declared limitations",
        manual_verification="Product title, station basis, aggregation, version, grid and accuracy/interpretation sections reviewed",
    ))
    rows.append(blank_source(
        "DERIVED_WEATHER_GRIDDED_SENSITIVITY",
        variable_name="gridded_component_month|station_grid_anomaly_agreement|gridded_destination_month",
        variable_description="SwissMetNet station versus MeteoSwiss TabsM/RhiresM monthly gridded sensitivity for reviewed components and destinations",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Regional-weather gridded-product sensitivity",
        retrieval_method="Deterministic Python NetCDF extraction, monthly anomaly construction and station-grid comparison",
        local_raw_file="config/meteoswiss_gridded_weather_files.json|config/path_c_analysis.json",
        processed_file="data_processed/meteoswiss_gridded_component_month.csv|reports/weather_gridded_component_comparison.csv|data_processed/destination_weather_gridded_sensitivity.csv|reports/weather_gridded_destination_summary.csv|reports/35_WEATHER_GRIDDED_SENSITIVITY.md",
        geographic_level="reviewed resort component grid cell and reviewed destination",
        temporal_resolution="monthly 2013-01 through 2026-03 plus component/destination summary",
        temporal_start="2013-01-01",
        temporal_end="2026-03-01",
        unit="degrees Celsius, millimetres, correlations, counts and flags",
        transformation_applied="Select nearest common valid grid cell; calculate cell/calendar-month 2013-2025 anomalies; aggregate unique cells by destination; compare against station anomalies on common complete months",
        quality_notes="Gridded method sensitivity, not an independent measurement network, piste microclimate, snow-phase measure or causal validation",
        confidence_level="high for reproducibility; qualified gridded-product sensitivity only",
        manual_verification="2,385 component-month rows, 15 component comparisons, 11 destination summaries and 1,749 destination-month rows; zero causal approvals",
    ))

    roster_observations = json.loads(
        (ROOT / "metadata/magic_pass_roster_evidence.json").read_text(encoding="utf-8")
    )["observations"]
    roster_by_source = {}
    for observation in roster_observations:
        roster_by_source.setdefault(observation["source_id"], []).append(observation)
    magic_ids = [key for key in configured if key.startswith("MAGIC_")]
    for source_id in magic_ids:
        item = configured[source_id]
        metadata = cached_metadata(source_id)
        is_archive = source_id == "MAGIC_PRESS_ARCHIVE"
        is_map = source_id == "MAGIC_CURRENT_MAP"
        roster_records = roster_by_source.get(source_id, [])
        is_supplemental = source_id in {
            "MAGIC_2019_APRIL", "MAGIC_2020_MAP", "MAGIC_2024_MAP", "MAGIC_PLEIADES_2020_TARIFF",
            "MAGIC_PLEIADES_2021_TARIFF", "MAGIC_FRIBOURG_2021_WINTER",
        }
        rows.append(blank_source(
            source_id,
            variable_name=("current_magic_destination" if is_map else "membership_event_evidence"),
            variable_description=item["description"],
            source_organisation=item["organisation"],
            source_dataset_name=(item["description"] if is_supplemental else "Official current destination map" if is_map else "Official Magic Pass press material"),
            source_page_url=(item["url"] if is_archive or is_map or is_supplemental else configured["MAGIC_PRESS_ARCHIVE"]["url"]),
            direct_download_url=item["url"] if not is_archive and not is_map else "",
            retrieval_method="HTTP GET with immutable response and SHA-256 sidecar" if metadata else "attempted HTTP GET; see collection log",
            retrieval_date=metadata.get("retrieval_date", "") if metadata else "",
            original_file_name=raw_name(metadata),
            local_raw_file=metadata.get("raw_file", "") if metadata else "",
            processed_file=("data_processed/magic_pass_current_destinations.csv" if is_map else "data_processed/magic_pass_membership_status_by_season.csv|reports/membership_continuity_audit.csv" if is_supplemental else "data_processed/magic_pass_membership_history.csv"),
            geographic_level="official ski destination",
            temporal_resolution=("retrieval-date snapshot" if is_map else "dated announcement / season"),
            temporal_start=(min(r["season"] for r in roster_records) if roster_records else "2017" if is_archive else source_id.removeprefix("MAGIC_") if source_id.removeprefix("MAGIC_").isdigit() else ""),
            temporal_end=(max(r["season"] for r in roster_records) if roster_records else "2026" if is_archive or is_map else ""),
            unit="destination membership event",
            license="UNKNOWN; preserve citation and original URL",
            access_conditions="Public source document; automated retrieval respects robots.txt; distributor retained explicitly where not publisher-hosted",
            transformation_applied="Visual review of pp.3-4; page 3 incremental expansion is used for roster continuity, while aggregate 40-winter/21-summer counts are not used as individual modality evidence" if source_id == "MAGIC_2021" else "Page/image-referenced visual/text review recorded in metadata/magic_pass_roster_evidence.json; positive seasonal evidence only" if is_supplemental else "Page-numbered text extraction and manually reviewed event transcription" if not is_map else "Embedded official destination JSON extracted from cached HTML",
            quality_notes=("Official publisher-hosted dated image; winter, summer-winter, Glacier 3000 and baths symbols reviewed separately; absence not evidence of non-membership" if source_id == "MAGIC_2020_MAP" else "Magic Pass branded dated map distributed by Raiffeisen; not publisher-hosted; visible symbols and printed validity reviewed; absence not evidence of non-membership" if source_id == "MAGIC_2024_MAP" else "Current snapshot is not historical evidence" if is_map else "Destination/operator scope may differ from Bergfex listing scope; seasonal membership does not establish daily operation or identical summer access"),
            confidence_level=("high for source authenticity; event/entity confidence stored per row" if metadata else "official URL verified; local retrieval pending"),
            manual_verification="reviewed; incremental roster-continuation statement on p.3 and aggregate counts on p.4" if source_id == "MAGIC_2021" else "reviewed; locators " + ";".join(sorted({r["source_page"] for r in roster_records})) if roster_records else "reviewed" if source_id in {"MAGIC_2017", "MAGIC_2018", "MAGIC_2019", "MAGIC_2020", "MAGIC_2021_APRIL", "MAGIC_2022", "MAGIC_2022_DOSSIER", "MAGIC_2023", "MAGIC_2024", "MAGIC_2025"} else "pending or page-level",
            notes="Not used as extracted evidence because download did not complete" if not metadata else "",
        ))
    rows.append(blank_source(
        "MAGIC_OFFICIAL_EVIDENCE_SET",
        variable_name="membership_event_history|seasonal_membership_evidence",
        variable_description="Union of dated Magic Pass documents, archive notices, operator tariffs and official tourism confirmation; seasonal map distributor recorded separately",
        source_organisation="Magic Mountains Cooperation; named ski operators and official tourism organisations",
        source_dataset_name="Documented Magic Pass event and seasonal evidence set",
        source_page_url=configured["MAGIC_PRESS_ARCHIVE"]["url"],
        retrieval_method="Event sources in metadata/magic_pass_entry_evidence.json; seasonal source IDs and exact pages in metadata/magic_pass_roster_evidence.json",
        processed_file="data_processed/magic_pass_membership_history.csv|data_processed/magic_pass_membership_status_by_season.csv",
        geographic_level="official ski destination with candidate resort link",
        temporal_resolution="season/event",
        temporal_start="2017/2018",
        temporal_end="2025/2026",
        unit="membership event",
        transformation_applied="Manual event transcription; reviewed aliases and unique normalised labels create candidate links",
        quality_notes="Continuity is complete for the 14 reviewed units only; unresolved destinations outside that reviewed set remain",
        confidence_level="mixed; stored per event",
        manual_verification="partial",
        notes="Treatment-ready is false for every event at the current checkpoint",
    ))

    scope_ids = [
        "ANNIVIERS_SCOPE_OFFICIAL",
        "EVOLENE_SCOPE_OFFICIAL",
        "REICHENBACH_SCOPE_OFFICIAL",
        "VILLARS_GRYON_SCOPE_OFFICIAL",
        "SAINTE_CROIX_SCOPE_OFFICIAL",
        "GSTAAD_SCOPE_OFFICIAL",
        "MEIRINGEN_HASLIBERG_SCOPE_OFFICIAL",
        "MEIRINGEN_HASLIBERG_MAGIC_OFFICIAL",
        "AESCHI_LIFT_SCOPE_OFFICIAL",
        "NIEDERHORN_MAGIC_SCOPE_OFFICIAL",
        "VALLEE_JOUX_SKI_SCOPE_OFFICIAL",
        "CHATEAU_DOEX_LA_BRAYE_2018",
        "MAYENS_CONTHEY_OPERATOR_OFFICIAL",
        "WILERALLMI_ANNUAL_2023_24",
        "GRENCHENBERG_OPERATOR_OFFICIAL",
        "DIABLERETS_SCOPE_OFFICIAL",
    ]
    unmatched_scope_ids = {
        "AESCHI_LIFT_SCOPE_OFFICIAL",
        "VALLEE_JOUX_SKI_SCOPE_OFFICIAL",
        "CHATEAU_DOEX_LA_BRAYE_2018",
        "MAYENS_CONTHEY_OPERATOR_OFFICIAL",
        "WILERALLMI_ANNUAL_2023_24",
        "GRENCHENBERG_OPERATOR_OFFICIAL",
        "DIABLERETS_SCOPE_OFFICIAL",
    }
    for source_id in scope_ids:
        item = configured[source_id]
        metadata = cached_metadata(source_id)
        rows.append(blank_source(
            source_id,
            variable_name="destination_scope_evidence",
            variable_description=item["description"],
            source_organisation=item["organisation"],
            source_dataset_name="Official destination or municipal scope page",
            source_page_url=item["url"],
            direct_download_url=item["url"],
            retrieval_method=(
                "HTTP GET with immutable response and SHA-256 sidecar"
                if metadata else "official URL verified; local retrieval pending"
            ),
            retrieval_date=metadata.get("retrieval_date", "") if metadata else "",
            original_file_name=raw_name(metadata),
            local_raw_file=metadata.get("raw_file", "") if metadata else "",
            processed_file=("reports/unmatched_magic_entry_review.csv|data_processed/magic_pass_scope_relations.csv" if source_id in unmatched_scope_ids else "" if source_id == "NIEDERHORN_MAGIC_SCOPE_OFFICIAL" else "data_processed/treatment_destination_units.csv"),
            geographic_level="official destination or municipality",
            temporal_resolution="retrieval-date scope snapshot",
            temporal_start="",
            temporal_end="2026",
            unit="scope evidence",
            license="UNKNOWN; preserve citation and original URL",
            access_conditions="Public official website; automated retrieval respects robots.txt",
            transformation_applied=("Not used; local retrieval unavailable" if not metadata else "Manually reviewed scope statement encoded in config/unmatched_magic_scope_review.json" if source_id in unmatched_scope_ids else "Manually reviewed scope statement encoded in config/treatment_destination_review.json"),
            quality_notes="Current scope evidence does not by itself establish historical tourism exposure",
            confidence_level="high for stated scope; analytical mapping remains explicitly qualified",
            manual_verification="reviewed" if metadata else "not used; retrieval pending",
        ))
    rows.append(blank_source(
        "DESTINATION_SCOPE_OFFICIAL_SET",
        variable_name="destination_unit_scope|municipality_outcome_scope",
        variable_description="Reviewed union of official municipality and lift-operator scope evidence",
        source_organisation="Municipalities and official lift operators",
        source_dataset_name="Destination scope evidence set",
        retrieval_method="Derived from individually registered official pages and geo.admin.ch point containment",
        processed_file="data_processed/treatment_destination_units.csv|data_processed/treatment_destination_municipality.csv",
        geographic_level="reviewed destination and municipality",
        temporal_resolution="scope snapshot",
        temporal_end="2026",
        unit="review decision",
        transformation_applied="Explicit inclusion/exclusion decisions and additive municipality outcome weights",
        quality_notes="Core-municipality proxies are labelled separately from complete observed municipal scope",
        confidence_level="reviewed analytical decision",
        manual_verification="reviewed",
        notes="Does not approve causal treatment status",
    ))

    geo_metadata = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(EVIDENCE_DIR.glob("GEO_POINT_*.metadata.json"))
    ]
    rows.append(blank_source(
        "GEOADMIN_MUNICIPALITY_IDENTIFY",
        variable_name="point_municipality_bfs_id|point_municipality_name|point_municipality_canton",
        variable_description="Current municipality polygon containing each supplied resort coordinate",
        source_organisation="Federal Office of Topography swisstopo / geo.admin.ch",
        source_dataset_name="Municipal boundaries — current swissBOUNDARIES3D layer",
        source_page_url="https://docs.geo.admin.ch/access-data/identify-features.html",
        api_endpoint="https://api3.geo.admin.ch/rest/services/ech/MapServer/identify",
        api_parameters="geometryType=esriGeometryPoint; sr=4326; layer=ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill; query-specific geometry recorded in config/municipality_queries.json",
        wms_layer="ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill",
        retrieval_method="271 rate-limited HTTP GET requests with immutable responses and SHA-256 sidecars",
        retrieval_date=(min(item["retrieval_date"] for item in geo_metadata) if geo_metadata else ""),
        original_file_name="GEO_POINT_<query_hash>_<timestamp>.json",
        local_raw_file="data_external/source_evidence/GEO_POINT_*.json",
        processed_file="data_processed/resort_point_municipality.csv",
        geographic_level="point-in-current-municipality polygon",
        temporal_resolution="boundary snapshot",
        temporal_start="2026-01-01",
        temporal_end="2026-01-01",
        unit="municipality identifier",
        license="See geo.admin.ch terms of use",
        access_conditions="Public API; raw response preserved for every point",
        transformation_applied="Selected the unique result marked is_current_jahr=true; no distance or fuzzy-name inference",
        quality_notes="Coordinate containment is not a tourism catchment or municipal exposure weight",
        confidence_level="high for point containment; none for causal tourism exposure",
        manual_verification="logic checked; 3 non-Swiss points unresolved",
    ))
    rows.append(blank_source(
        "BERGFEX_RESORT_DIRECTORY",
        variable_name="resort_name|region|url_station|altitude_top_m|ski_area_km|number_lifts",
        variable_description="Existing resort-directory scrape supplied by the researcher",
        source_organisation="bergfex GmbH",
        source_dataset_name="Bergfex Swiss ski-resort directory",
        source_page_url="https://www.bergfex.ch/schweiz/",
        retrieval_method="Legacy region-page HTML scraping; upstream R script inspected",
        retrieval_date="UNKNOWN",
        original_file_name="bergfex_stations_ski_suisse_par_region.csv",
        local_raw_file="data_raw/bergfex_stations_ski_suisse_par_region.csv",
        processed_file="data_processed/resort_master.csv",
        geographic_level="resort listing",
        temporal_resolution="undated snapshot",
        unit="mixed",
        license="UNKNOWN; redistribution and reuse require review",
        access_conditions="Existing research copy; do not recollect without terms/robots review",
        transformation_applied="Unique URL join to normalised listing table; no new scrape",
        quality_notes="Observation date and independent-domain semantics are unknown",
        confidence_level="medium for fields; low for temporal interpretation",
        manual_verification="schema and unique URLs checked",
    ))
    rows.append(blank_source(
        "DERIVED_MULTI_SOURCE",
        variable_name="derived analytical fields",
        variable_description="Project-generated fields combining multiple registered sources",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Reproducible local transformations",
        retrieval_method="versioned Python scripts",
        processed_file="data_processed/",
        geographic_level="mixed",
        temporal_resolution="mixed",
        unit="mixed",
        license="inherits source restrictions",
        transformation_applied="See formula and script references in data dictionary",
        quality_notes="Not an external source; lineage remains in source_ids and formulas",
        confidence_level="derived",
        manual_verification="automated tests plus checkpoint review",
    ))
    rows.append(blank_source(
        "DERIVED_REVIEWED_DESTINATION_PANEL",
        variable_name="reviewed_destination_month_outcomes|hotel_capacity|snow_proxy|weather_proxy|diagnostic_membership_status",
        variable_description="Monthly destination outcomes, hotel capacity, qualified snow/weather proxies, and diagnostic treatment coding aggregated across reviewed scopes",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Reviewed destination-month panel",
        retrieval_method="versioned Python transformation",
        processed_file="data_processed/destination_month_panel.csv",
        geographic_level="reviewed destination unit",
        temporal_resolution="monthly",
        temporal_start="2013-01",
        temporal_end="2026-12 grid; 2026-03 latest observed outcome",
        unit="destination-month",
        license="inherits source restrictions",
        transformation_applied="Additive municipality outcome/capacity totals; complete-case multi-station snow/weather proxy means; official occupancy percentages retained only for single-municipality units; entry carried forward only as a flagged diagnostic assumption",
        quality_notes="No row is causal-ready; SLF and MeteoSwiss proxies are not direct piste observations; treatment intensity, controls, spillovers, and other time-varying confounders remain unresolved",
        confidence_level="high for reproducible aggregation; low for causal treatment status",
        manual_verification="automated tests plus destination review",
    ))
    rows.append(blank_source(
        "DERIVED_MAGIC_SCOPE_REVIEW",
        variable_name="unmatched_entry_classification|non_equivalent_scope_relations|precautionary_donor_exclusions",
        variable_description="Reviewed classification of unmatched historical entry labels and explicitly non-equivalent links to supplied resort listings",
        source_organisation="Thesis research; constituent source IDs retained per row",
        source_dataset_name="Unmatched Magic Pass scope review",
        retrieval_method="Versioned config/unmatched_magic_scope_review.json plus cached official sources and supplied directory",
        local_raw_file="config/unmatched_magic_scope_review.json",
        processed_file="reports/unmatched_magic_entry_review.csv|data_processed/magic_pass_scope_relations.csv|reports/control_contamination_audit.csv",
        geographic_level="official entry label; listing relation; point municipality risk",
        temporal_resolution="historical entry event and current scope review kept separate",
        temporal_start="2017/2018", temporal_end="2025/2026",
        unit="classification; relation; boolean screen",
        transformation_applied="Exact reviewed label lookup; expand many-to-many relation rows; deduplicate linked listing IDs for precautionary donor exclusions",
        quality_notes="Not identity equivalence or causal exposure; foreign destinations can create spillovers; a documented destination absent from the supplied directory is a coverage gap, not a non-member",
        manual_verification="26 labels reviewed; five previously uncertain Swiss/overlapping cases resolved on 2026-09-22",
        confidence_level="qualified per relation; no causal mappings approved",
    ))
    rows.append(blank_source(
        "DERIVED_MAGIC_ANNUAL_OFFERING",
        variable_name="winter_access_status|summer_access_status|published_summer_winter_labels|published_winter_only_labels",
        variable_description="Page-referenced annual winter versus summer-winter access classification for reviewed destination units",
        source_organisation="Thesis research; constituent annual Magic Pass source IDs retained per row",
        source_dataset_name="Annual Magic Pass season-offering review",
        retrieval_method="Visual annual-publication review encoded in versioned metadata/magic_pass_season_offering_evidence.json",
        local_raw_file="metadata/magic_pass_season_offering_evidence.json",
        processed_file="data_processed/magic_pass_membership_status_by_season.csv",
        geographic_level="reviewed destination unit with published component labels retained",
        temporal_resolution="annual pass season",
        temporal_start="2017/2018", temporal_end="2025/2026",
        unit="destination-unit season",
        transformation_applied="Join page-referenced annual offering observations to the membership-status grid without filling seasons lacking individual modality evidence",
        quality_notes="Summer access is not daily operation, equal component coverage, tourism exposure, or a causal treatment; unverified seasons remain unknown",
        manual_verification="Seven annual publications visually reviewed on 2026-09-21",
        confidence_level="high for transcribed symbols; qualified for composite destination scope",
    ))
    rows.append(blank_source(
        "DERIVED_DONOR_PRETREND_SCREEN",
        variable_name="pretrend_comparability|descriptive_comparability_score|comparability_rank",
        variable_description="Treatment-specific descriptive prioritisation of provisional donor municipalities using 36 pre-anchor months",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Donor pre-trend comparability screen",
        retrieval_method="Versioned Python transformation of checksum-traceable hotel, capacity, resort-directory and control-screen inputs",
        processed_file="data_processed/donor_pretrend_comparability.csv|reports/donor_pretrend_shortlist.csv",
        geographic_level="reviewed treatment and provisional donor municipality pair",
        temporal_resolution="36-month pre-anchor window",
        temporal_start="treatment-specific",
        temporal_end="month before treatment-specific analytical anchor",
        unit="pair-level descriptive diagnostics and within-treatment ranks",
        license="inherits source restrictions",
        transformation_applied="Log1p outcome comparisons; calendar-month-adjusted linear trend; seasonal profile and standardized-shape diagnostics; equal-weight within-treatment percentile score",
        quality_notes="Heuristic rank only; current directory structure may differ historically; historical non-membership, spillovers, accessibility, confounding, balance and parallel trends are not approved",
        confidence_level="high for reproducibility; none for causal validity",
        manual_verification="35 top-five pairs retained for manual review; zero causal controls approved",
    ))
    rows.append(blank_source(
        "DERIVED_TEMPORAL_CONTROLS",
        variable_name="calendar_quarter|magic_pass_season|winter_month|summer_month|christmas_new_year_peak_month|easter_month|covid_sensitivity_month",
        variable_description="Deterministic month-level calendar and broad COVID sensitivity controls",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Temporal control calendar",
        retrieval_method="Versioned deterministic Python transformation from Gregorian calendar dates and config/temporal_controls.json",
        local_raw_file="config/temporal_controls.json",
        processed_file="data_processed/temporal_controls_month.csv|data_processed/destination_month_panel.csv",
        geographic_level="all reviewed destinations; no geographic variation",
        temporal_resolution="monthly",
        temporal_start="2013-01",
        temporal_end="2026-12",
        unit="calendar month",
        transformation_applied="May-April pass-season label; November-April winter partition; Gregorian Easter calculation; analyst-defined March 2020-April 2022 sensitivity interval",
        quality_notes="Does not encode canton-specific school holidays or a legal COVID-restriction chronology; the broad COVID flag is for sensitivity analysis only",
        confidence_level="high for calendar derivation; qualified for substantive holiday/COVID interpretation",
        manual_verification="168 unique months; winter/summer partition and one-to-many panel join tested",
    ))
    rows.append(blank_source(
        "DERIVED_SNOW_STATION_SENSITIVITY",
        variable_name="alternative_station_agreement|winter_mean_depth_correlation|relative_mean_absolute_depth_difference|trend_direction_agrees",
        variable_description="Selected-versus-next-nearest eligible SLF station robustness diagnostics for reviewed resort components",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="SLF alternative-station sensitivity",
        retrieval_method="Versioned Python transformation of checksum-traceable SLF station metadata and station-winter aggregates",
        processed_file="data_processed/resort_snow_alternative_station_sensitivity.csv",
        geographic_level="reviewed resort component and two external SLF stations",
        temporal_resolution="November-April winter seasons",
        temporal_start="2013/2014",
        temporal_end="2025/2026",
        unit="component-level robustness diagnostic",
        license="inherits SLF source terms (CC BY 4.0)",
        transformation_applied="Replace nearest eligible station with next-nearest distinct station under the same 80% longitudinal gate; compare common usable winters",
        quality_notes="Neither station is a piste observation; alternative is not elevation/aspect optimised; gridded independent-source sensitivity remains pending",
        confidence_level="high for reproducibility; qualified for proxy representativeness; none for causal validity",
        manual_verification="15 reviewed components, 115 eligible stations and zero causal approvals asserted",
    ))
    rows.append(blank_source(
        "DERIVED_DONOR_NETWORK_SPILLOVER_AUDIT",
        variable_name="minimum_distance_to_resolved_magic_km|network_distance_band|network_spillover_cleared_30km",
        variable_description="Network-wide proximity sensitivity from apparent donor resort points to all resolved Magic Pass resort points",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Donor network-wide spillover audit",
        retrieval_method="Versioned Python transformation of resort points, current/historical resolved Magic links and donor screens",
        processed_file="reports/donor_network_spillover_audit.csv|data_processed/donor_shortlist_network_audit.csv",
        geographic_level="apparent donor municipality and treatment-donor shortlist pair",
        temporal_resolution="historical resolved links plus current snapshot",
        temporal_start="2017/2018",
        temporal_end="2026 current snapshot",
        unit="kilometres and sensitivity flags",
        transformation_applied="Minimum haversine distance from any supplied donor-municipality resort point to any historically/currently resolved Magic resort point",
        quality_notes="Resolved network is a lower bound; resort points are not catchments; distance does not prove spillovers or their absence",
        confidence_level="high for reproducibility; none for causal control validity",
        manual_verification="52 apparent controls and all 35 shortlisted pairs covered; zero causal controls approved",
    ))
    rows.append(blank_source(
        "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT",
        variable_name="magic_roster_source_id|historical_magic_nonmembership_status|competing_pass_at_anchor_status|local_tourism_shock_status|final_manual_review_decision|remaining_deep_audit_candidate",
        variable_description="Complete-roster nonmembership and page-referenced competing-pass/local-tourism-shock review for shortlisted donor pairs beyond 50 km from the resolved Magic network",
        source_organisation="Thesis research; constituent official source IDs retained per row",
        source_dataset_name="Donor competing-pass and local-shock audit",
        retrieval_method="Versioned manual evidence config joined by exact treatment, donor BFS and anchor key",
        local_raw_file="config/donor_external_shock_review.json",
        processed_file="reports/donor_external_shock_evidence.csv|data_processed/donor_shortlist_final_audit.csv",
        geographic_level="shortlisted treatment-donor pair",
        temporal_resolution="treatment-specific anchor and surrounding pass season",
        temporal_start="2017-11",
        temporal_end="2023-05",
        unit="qualified evidence status and review decision",
        license="inherits constituent source restrictions",
        transformation_applied="Exact-key completeness check for seven beyond-50-km pairs; complete annual Magic roster label review; network-distance priorities combined with reviewed external-shock evidence",
        quality_notes="Roster absence is documented for reviewed station/place labels, not corporate-register affiliates; all seven remote pairs have a contemporaneous local shock and are excluded",
        confidence_level="high for reproducibility; none for causal control validity",
        manual_verification="Seven remote pairs reviewed and excluded; zero deep-audit candidates and zero causal controls approved",
    ))
    rows.append(blank_source(
        "DERIVED_TREATMENT_DISTANCE_GRADIENT",
        variable_name="representative_point_distance_to_destination_km|minimum_polygon_distance_to_destination_km|descriptive_near_minus_far_log_change",
        variable_description="Same-treated-destination comparison of hotel municipalities by distance to destination component resort points",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Treatment municipality distance-gradient diagnostic",
        retrieval_method="Versioned Python transformation of swissBOUNDARIES3D, resort coordinates, reviewed treatment units and hotel outcomes",
        processed_file="data_processed/treatment_municipality_distance_exposure.csv|data_processed/treatment_distance_gradient_diagnostic.csv|reports/treatment_distance_ring_summary.csv|reports/treatment_distance_near_far_contrast.csv",
        geographic_level="reviewed treated destination by hotel municipality",
        temporal_resolution="current distance snapshot plus treatment-specific adjacent 24-month windows",
        temporal_start="2013",
        temporal_end="2026",
        unit="kilometres and descriptive log change",
        transformation_applied="EPSG:2056 distances to the same destination's component points; 24-month pre/post municipal outcome summaries; within-destination distance rings and buffered near/far contrast",
        quality_notes="Current boundaries, representative points and adjacent windows do not identify exposure or causal effects; travel time and hotel coordinates unavailable",
        confidence_level="high for reproducibility; exploratory only for treatment gradient",
        manual_verification="11x186 distance rows; seven treatment diagnostics; every causal flag false",
    ))
    rows.append(blank_source(
        "DERIVED_DISTANCE_TRANSPORT_COMPARISON",
        variable_name="distance_rank|scheduled_round_trip_rank|rank_disagreement|destination_rank_correlation|distance_band_transit_summary",
        variable_description="Same-destination comparison of current municipality distance and winter-2026 scheduled public-transport journey time",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Distance versus scheduled public-transport comparison",
        retrieval_method="Deterministic one-to-one merge and within-destination rank comparison of existing derived distance and GTFS journey tables",
        local_raw_file="config/path_c_analysis.json",
        processed_file="data_processed/treatment_municipality_distance_transport_comparison.csv|reports/distance_transport_correlations_by_destination.csv|reports/distance_transport_band_summary.csv|reports/28_DISTANCE_TRANSPORT_COMPARISON.md",
        geographic_level="reviewed destination by hotel municipality",
        temporal_resolution="current 2026 boundary distance and winter-2026 weekday/Saturday schedule",
        temporal_start="2026-02-04",
        temporal_end="2026-02-07",
        unit="kilometres, scheduled minutes, ranks and correlations",
        transformation_applied="Preserve all 2,046 pairs; calculate within-destination percentile ranks and rank correlations only where scheduled means are available; retain coverage status",
        quality_notes="Current distance and two-day static timetable are not historical exposure, visitor catchments or observed trips; coverage differs by destination",
        confidence_level="high for reproducibility; descriptive current comparison only",
        manual_verification="1,700 bidirectional pairs, 1,104 complete pairs, ten destination correlations and zero causal approvals checked",
    ))
    rows.append(blank_source(
        "DERIVED_PATH_C_FEATURE_MATRIX",
        variable_name="cluster-level structural features|Magic evidence status|snow vulnerability|data quality",
        variable_description="Least-duplicated available cross-sectional feature table for lift clusters linked to supplied resort listings",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C resort-cluster feature matrix",
        retrieval_method="Versioned aggregation configured in config/path_c_analysis.json",
        local_raw_file="config/path_c_analysis.json",
        processed_file="data_processed/path_c_resort_cluster_features.csv|reports/path_c_feature_summary.json",
        geographic_level="existing lift cluster with at least one supplied resort listing",
        temporal_resolution="undated cross-sectional directory snapshot",
        unit="cluster-level feature and evidence flag",
        transformation_applied="Median/min/max aggregation across assigned listings; exact current/history/scope evidence flags; no hotel outcome used as a feature",
        quality_notes="Existing clusters are not certified independent destinations; Bergfex observation date is unknown; point municipality is not tourism exposure",
        confidence_level="reproducible descriptive feature engineering; not pre-treatment or causal",
        manual_verification="162 linked clusters; missing values retained; multi-listing disagreements exposed",
    ))
    rows.append(blank_source(
        "DERIVED_PATH_C_SEGMENTATION_ANALOGUES",
        variable_name="segment_id|silhouette|bootstrap_ari|nearest Magic analogues|reviewed-treated analogue signal|OOD flag",
        variable_description="Stability-checked structural segmentation and nearest-neighbour analogue diagnostics for exploratory Path C",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C segmentation and analogue analysis",
        retrieval_method="Deterministic NumPy implementation using versioned config and derived feature tables",
        local_raw_file="config/path_c_analysis.json",
        processed_file="data_processed/path_c_cluster_segments.csv|data_processed/path_c_candidate_analogues.csv|data_processed/path_c_reviewed_treated_reference.csv|reports/path_c_segmentation_diagnostics.csv|figures/path_c_structural_segments.png|figures/path_c_opportunity_snow_matrix.png",
        geographic_level="linked lift cluster or reviewed treated destination",
        temporal_resolution="current structural snapshot plus unadjusted adjacent 24-month diagnostics",
        unit="standardised distance, segment, empirical support and descriptive percent change",
        transformation_applied="Z-score altitude and log1p size features; select k by silhouette after size/stability gates; report three nearest reference entities and empirical leave-one-out OOD support",
        quality_notes="Analogue changes are unadjusted, discrete and not counterfactual predictions; snow is kept outside structural similarity",
        confidence_level="exploratory only; support qualified per candidate",
        manual_verification="k=2 selected; predicted-uplift and causal flags remain empty/false",
    ))
    rows.append(blank_source(
        "DERIVED_PATH_C_DECISION_SUPPORT",
        variable_name="opportunity_signal_percentile|snow_vulnerability_percentile|comparability|network context|qualified tourism, population, NPVM transport and stop-proximity context|unapproved strategic-need fields",
        variable_description="Dashboard-ready exploratory Path C export retaining separate opportunity, vulnerability, support, quality and qualified context dimensions",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Magic Pass exploratory decision-support prototype",
        retrieval_method="Versioned merge of Path C feature, segment and analogue outputs",
        local_raw_file="config/path_c_analysis.json",
        processed_file="data_processed/magic_pass_decision_support.csv|reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md|reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md|reports/19_PATH_C_AGGREGATION_SENSITIVITY.md|reports/20_TOURISM_DEPENDENCE_CONTEXT.md|reports/21_ACCESSIBILITY_CONTEXT.md|reports/22_TRANSPORT_ACCESSIBILITY_CONTEXT.md|reports/23_PUBLIC_TRANSPORT_STOP_CONTEXT.md",
        geographic_level="existing lift cluster with supplied resort listings",
        temporal_resolution="mixed descriptive snapshot; lineage retained by field",
        unit="separate decision-support dimensions",
        transformation_applied="One-to-one merge by stable cluster_id; opportunity and snow percentiles retained separately; min/median/max aggregation sensitivity, qualified point-container tourism, Swiss straight-line population, NPVM transport and official stop-proximity context appended; no composite score",
        quality_notes="Catchment-level tourism dependence and validated arrival-node/live-routing accessibility remain missing; zonal travel times and straight-line stop proximity are not approved destination-access measures; foreign population is omitted; blank uplift fields are intentional",
        confidence_level="exploratory prototype; never a recommendation ranking",
        manual_verification="Checkpoint 4 and 5 failures formalised; no predicted uplift or composite score produced",
    ))
    rows.append(blank_source(
        "DERIVED_PATH_C_AGGREGATION_SENSITIVITY",
        variable_name="aggregation rule|segment stability|analogue stability|OOD stability|opportunity-signal range",
        variable_description="Min/median/max within-cluster aggregation robustness audit for every apparent Path C candidate",
        source_organisation="Master thesis analytical pipeline",
        source_dataset_name="Path C aggregation sensitivity",
        retrieval_method="Deterministic rebuild under three predeclared aggregation rules",
        local_raw_file="config/path_c_analysis.json",
        processed_file="data_processed/path_c_candidate_analogue_sensitivity.csv|reports/path_c_aggregation_sensitivity.csv|reports/path_c_aggregation_sensitivity_k_diagnostics.csv|reports/path_c_aggregation_sensitivity_summary.json|reports/19_PATH_C_AGGREGATION_SENSITIVITY.md",
        geographic_level="existing lift cluster with supplied resort listings",
        temporal_resolution="undated cross-sectional directory snapshot",
        unit="scenario-level segment, analogue, support and descriptive percent change",
        transformation_applied="Repeat segmentation and nearest-analogue construction under within-cluster minimum, median and maximum structural features; compare assignments, neighbours, OOD categories and descriptive signal",
        quality_notes="Aggregation rules probe listing semantics, not causal truth or predictive validity; exact analogue assignments and OOD flags are not invariant",
        confidence_level="reproducible robustness diagnostic; exploratory only",
        manual_verification="All three rules select k=2; only 11 of 104 candidates are stable on every recorded criterion; every causal flag false",
    ))
    sources = upsert(existing_sources, rows, "source_id", SOURCE_COLUMNS)
    sources.to_csv(SOURCE_FILE, index=False)

    existing_dictionary = pd.read_csv(DICTIONARY_FILE, dtype=str, keep_default_na=False)
    definitions = [
        ("hotel_overnights", "hotel_municipality_month", "Hotel overnight stays in open establishments", "overnight stays", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "cleaned source", "Parsed only when source token is a nonnegative integer", "outcome", "Suppressed '...' values remain missing"),
        ("hotel_arrivals", "hotel_municipality_month", "Hotel arrivals in open establishments", "persons", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "cleaned source", "Parsed only when source token is a nonnegative integer", "secondary outcome", "Suppressed values remain missing"),
        ("domestic_overnights", "hotel_municipality_month", "Overnight stays by Swiss residents", "overnight stays", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "cleaned source", "Parsed only when source token is a nonnegative integer", "secondary outcome", "Suppressed values remain missing"),
        ("foreign_overnights", "hotel_municipality_month", "Total minus domestic overnight stays", "overnight stays", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "derived", "hotel_overnights - domestic_overnights", "secondary outcome", "Missing when either component is unavailable"),
        ("log_overnights", "hotel_municipality_month", "Log-transformed hotel overnight stays", "log points", "float", "municipality", "monthly", "BFS_HOTEL_DATA", "derived", "log(1 + hotel_overnights)", "outcome", "No imputation"),
        ("hotel_establishments_open", "hotel_capacity_municipality_month", "Open hotel and health establishments", "establishments", "Int64", "municipality", "monthly", "BFS_HOTEL_CAPACITY_DATA", "cleaned source", "Parsed only when the literal source token is a nonnegative integer", "time-varying supply confounder", "Source '..' and '...' tokens remain missing"),
        ("hotel_rooms_available", "hotel_capacity_municipality_month", "Rooms in open hotel and health establishments", "rooms", "Int64", "municipality", "monthly", "BFS_HOTEL_CAPACITY_DATA", "cleaned source", "Parsed only when the literal source token is a nonnegative integer", "time-varying supply confounder", "No imputation"),
        ("hotel_beds_available", "hotel_capacity_municipality_month", "Beds in open hotel and health establishments", "beds", "Int64", "municipality", "monthly", "BFS_HOTEL_CAPACITY_DATA", "cleaned source", "Parsed only when the literal source token is a nonnegative integer", "time-varying supply confounder", "No imputation"),
        ("hotel_room_occupancy_rate_pct", "hotel_capacity_municipality_month", "Official room occupancy rate", "percent", "Float64", "municipality", "monthly", "BFS_HOTEL_CAPACITY_DATA", "cleaned source", "Official published value parsed without adjustment", "descriptive capacity utilisation", "Not an outcome denominator for multi-municipality aggregation"),
        ("hotel_bed_occupancy_rate_pct", "hotel_capacity_municipality_month", "Official bed occupancy rate", "percent", "Float64", "municipality", "monthly", "BFS_HOTEL_CAPACITY_DATA", "cleaned source", "Official published value parsed without adjustment", "descriptive capacity utilisation", "59 source values exceed 100 and remain unchanged"),
        ("complete_capacity_supply", "hotel_capacity_municipality_month", "Whether establishments, rooms, and beds are all observed", "boolean", "boolean", "municipality", "monthly", "BFS_HOTEL_CAPACITY_DATA", "derived", "all three supply values are numeric source observations", "capacity quality", "False rows remain missing; no imputation"),
        ("hotel_overnights_per_available_bed_month", "hotel_municipality_month_enriched", "Monthly overnight stays per contemporaneous available bed", "overnight stays per bed-month", "float", "municipality", "monthly", "BFS_HOTEL_CAPACITY_DATA", "derived", "live-table hotel_overnights_capacity_table / hotel_beds_available when beds > 0", "descriptive capacity-adjusted demand", "Not the official occupancy rate"),
        ("snow_depth_mean_cm", "slf_snow_station_month", "Mean of valid daily SLF total snowpack depth within the month", "centimetres", "float", "SLF IMIS station", "monthly", "SLF_IMIS_DAILY_SNOW", "derived", "mean daily HS after negative values are marked invalid", "time-varying snow proxy", "No imputation; station is not a piste observation"),
        ("days_snow_depth_ge_30cm", "slf_snow_station_month", "Observed days with total snowpack depth at least 30 cm", "days", "integer", "SLF IMIS station", "monthly", "SLF_IMIS_DAILY_SNOW", "derived", "count(valid HS >= 30 cm)", "snow reliability proxy", "Interpret with observation coverage"),
        ("snow_depth_observation_coverage_share", "slf_snow_station_month", "Share of calendar days with a physically valid snow-depth observation", "share", "float", "SLF IMIS station", "monthly", "SLF_IMIS_DAILY_SNOW", "derived", "valid HS days / calendar days", "snow data quality", "Month is usable at >=0.80"),
        ("winter_mean_snow_depth_cm", "slf_snow_station_winter", "Mean valid daily snowpack depth from November through April", "centimetres", "float", "SLF IMIS station", "winter season", "SLF_IMIS_DAILY_SNOW", "derived", "mean daily HS over November-April", "snow vulnerability feature", "Season is usable at >=0.80 observation coverage"),
        ("snow_station_code", "resort_snow_station_crosswalk", "SLF station selected as an external mountain snow proxy", "identifier", "string", "resort-to-station link", "2013/14-2025/26 coverage gate", "SLF_IMIS_STATIONS", "derived linkage", "geographically nearest snow station among stations with >=80% longitudinal winter coverage", "snow linkage", "Never interpreted as direct slope representation"),
        ("snow_station_distance_km", "resort_snow_station_crosswalk", "Great-circle distance from resort listing point to selected SLF station", "kilometres", "float", "resort-to-station link", "station metadata snapshot", "SLF_IMIS_STATIONS", "derived geospatial distance", "haversine distance between supplied resort coordinate and station coordinate", "snow proxy quality", "Does not capture terrain barriers or aspect"),
        ("snow_station_elevation_gap_to_resort_top_m", "resort_snow_station_crosswalk", "Absolute elevation difference between the SLF station and published resort-top altitude", "metres", "float", "resort-to-station link", "snapshot", "DERIVED_MULTI_SOURCE", "derived", "abs(station elevation - Bergfex resort top altitude)", "snow proxy quality", "Resort base/mid elevations are unavailable"),
        ("snow_proxy_quality", "resort_snow_station_crosswalk", "Rule-based spatial/elevation comparability class", "category", "string", "resort-to-station link", "snapshot", "DERIVED_MULTI_SOURCE", "derived", "high if <=10 km and <=500 m gap; moderate if <=25 km and <=1000 m; otherwise low", "snow data quality", "Comparability class, not measurement accuracy"),
        ("snow_reliability_share_days_ge_30cm", "resort_snow_vulnerability", "Share of valid November-April proxy-station days with snow depth >=30 cm", "share", "float", "resort via SLF proxy station", "2013/14-2025/26", "SLF_IMIS_DAILY_SNOW", "derived", "sum station days HS>=30 / sum valid winter days across usable seasons", "snow reliability proxy", "May be shared by multiple resorts mapped to one station"),
        ("snow_depth_trend_cm_per_year", "resort_snow_vulnerability", "Linear trend in proxy-station winter mean snow depth", "centimetres per year", "float", "resort via SLF proxy station", "2013/14-2025/26", "SLF_IMIS_DAILY_SNOW", "derived", "OLS slope of winter mean HS on winter start year over usable seasons", "snow trend proxy", "Short series; descriptive only; no uncertainty model yet"),
        ("snow_vulnerability_proxy", "resort_snow_vulnerability", "Inverse of the proxy-station winter-day snow reliability share", "0-1 proxy", "float", "resort via SLF proxy station", "2013/14-2025/26", "SLF_IMIS_DAILY_SNOW", "derived", "1 - snow_reliability_share_days_ge_30cm", "strategic-need candidate", "Not a piste-level vulnerability measure and not yet approved for scoring"),
        ("air_temperature_mean_c", "meteoswiss_station_month", "Mean of official daily mean 2 m air temperature within the month", "degrees Celsius", "float", "SwissMetNet station", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "mean daily tre200d0", "time-varying regional weather proxy", "No imputation; station is not a piste observation"),
        ("air_temperature_anomaly_c", "meteoswiss_station_month", "Monthly mean-temperature departure from the station's calendar-month 2013-2025 analytical normal", "degrees Celsius", "float", "SwissMetNet station", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "air_temperature_mean_c - mean usable same-calendar-month temperature in 2013-2025", "time-varying regional weather proxy", "Not an official MeteoSwiss climate normal"),
        ("precipitation_total_mm", "meteoswiss_station_month", "Sum of valid official daily precipitation totals within the month", "millimetres", "float", "SwissMetNet station", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "sum daily rre150d0 with at least one valid value", "time-varying regional weather proxy", "Daily observation window is 06:00 UTC to 06:00 UTC next day"),
        ("precipitation_anomaly_mm", "meteoswiss_station_month", "Monthly precipitation departure from the station's calendar-month 2013-2025 analytical normal", "millimetres", "float", "SwissMetNet station", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "precipitation_total_mm - mean usable same-calendar-month precipitation in 2013-2025", "time-varying regional weather proxy", "Missing when the month fails the 80% coverage gate"),
        ("precipitation_coverage_share", "meteoswiss_station_month", "Share of calendar days with a valid precipitation observation", "share", "float", "SwissMetNet station", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "valid rre150d0 days / calendar days", "weather data quality", "Month is usable at >=0.80 together with all temperature fields"),
        ("month_weather_proxy_usable", "meteoswiss_station_month", "Whether mean/min/max temperature and precipitation each meet the monthly coverage gate", "boolean", "boolean", "SwissMetNet station", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "all four observation coverage shares >= 0.80", "weather data quality", "Two of 1,113 station-months fail at this checkpoint"),
        ("weather_station_code", "resort_weather_station_crosswalk", "SwissMetNet station selected as a regional temperature/precipitation proxy", "identifier", "string", "resort-to-station link", "2013-2026 coverage window", "METEOSWISS_SMN_STATIONS", "derived linkage", "nearest current station among official inventory candidates with all four daily parameters starting by 2013", "weather linkage", "Never interpreted as direct slope representation"),
        ("weather_station_distance_km", "resort_weather_station_crosswalk", "Great-circle distance from resort listing point to selected SwissMetNet station", "kilometres", "float", "resort-to-station link", "station metadata snapshot", "METEOSWISS_SMN_STATIONS", "derived geospatial distance", "haversine distance between supplied resort coordinate and station coordinate", "weather proxy quality", "Does not capture terrain barriers or local gradients"),
        ("weather_station_elevation_gap_to_resort_top_m", "resort_weather_station_crosswalk", "Absolute elevation difference between SwissMetNet station and published resort-top altitude", "metres", "float", "resort-to-station link", "snapshot", "DERIVED_MULTI_SOURCE", "derived", "abs(station elevation - Bergfex resort top altitude)", "weather proxy quality", "Regional anomalies are emphasised because gaps can be large"),
        ("weather_proxy_quality", "resort_weather_station_crosswalk", "Rule-based horizontal-distance comparability class for regional weather anomalies", "category", "string", "resort-to-station link", "snapshot", "DERIVED_MULTI_SOURCE", "derived", "high if <=10 km; moderate if <=20 km; otherwise low", "weather data quality", "Elevation gap is retained separately; class is not measurement accuracy"),
        ("resort_id", "resort_master", "Stable ID retained from existing normalised listing table", "identifier", "string", "resort listing", "snapshot", "DERIVED_MULTI_SOURCE", "existing identifier", "retained without fuzzy merging", "identifier", "Does not yet prove independent resort-domain status"),
        ("cluster_id", "resort_master", "Existing lift-cluster assignment", "identifier", "string", "lift cluster", "snapshot", "DERIVED_MULTI_SOURCE", "existing identifier", "preserved existing assignment", "group identifier", "Clustering was validated, not rebuilt"),
        ("altitude_top_m", "resort_master", "Published maximum resort altitude", "metres", "numeric", "resort listing", "snapshot", "BERGFEX_RESORT_DIRECTORY", "cleaned source", "unique URL join", "candidate pre-treatment feature", "Observation date unknown"),
        ("ski_area_km", "resort_master", "Published skiable piste length", "kilometres", "numeric", "resort listing", "snapshot", "BERGFEX_RESORT_DIRECTORY", "cleaned source", "unique URL join", "candidate pre-treatment feature", "Definition and observation date require review"),
        ("number_lifts", "resort_master", "Published lift count", "count", "numeric", "resort listing", "snapshot", "BERGFEX_RESORT_DIRECTORY", "cleaned source", "unique URL join", "candidate pre-treatment feature", "May differ from preserved geospatial lift count"),
        ("point_municipality_bfs_id", "resort_point_municipality", "BFS ID of current municipality containing listing coordinate", "identifier", "Int64", "point/current municipality", "2026 boundary snapshot", "GEOADMIN_MUNICIPALITY_IDENTIFY", "derived spatial link", "unique is_current_jahr point-identify result", "geographic linkage", "Not a tourism exposure assignment"),
        ("bfs_hotel_universe", "resort_point_municipality", "Whether point municipality occurs in live OFS hotel-table metadata", "boolean", "boolean", "point/current municipality", "metadata snapshot", "BFS_HOTEL_METADATA", "derived", "point_municipality_bfs_id in BFS Gemeinde codes", "coverage flag", "Does not establish resort exposure"),
        ("event_type", "magic_pass_membership_history", "Type of documented Magic Pass membership-related event", "category", "string", "official destination", "event/season", "MAGIC_OFFICIAL_EVIDENCE_SET", "manual evidence extraction", "reviewed official announcement", "treatment evidence", "Base entry is separated from supplements and exits"),
        ("entry_season", "magic_pass_membership_history", "Officially announced first membership season", "season", "string", "official destination", "season", "MAGIC_OFFICIAL_EVIDENCE_SET", "manual evidence extraction", "source season label", "treatment timing candidate", "Exact date remains UNKNOWN"),
        ("candidate_resort_id", "magic_pass_membership_history", "Candidate link from official destination to supplied resort listing", "identifier", "string", "cross-source entity link", "event", "DERIVED_MULTI_SOURCE", "derived", "reviewed alias or unique normalised label", "entity resolution", "Destination scope remains pending"),
        ("treatment_ready", "magic_pass_membership_history", "Whether event passes all current causal-use gates", "boolean", "boolean", "cross-source entity link", "event", "DERIVED_MULTI_SOURCE", "derived", "scope AND continuity AND exposure approved", "quality gate", "Currently false for all events"),
        ("current_member_snapshot", "magic_pass_current_destinations", "Presence in cached official current map", "boolean", "boolean", "official destination", "retrieval snapshot", "MAGIC_CURRENT_MAP", "extracted source", "embedded official JSON", "current status evidence", "Not historical timing evidence"),
        ("data_quality_score", "resort_data_quality", "Evidence-completeness score across eight equally weighted components", "0-100 score", "float", "resort listing", "current checkpoint", "DERIVED_MULTI_SOURCE", "derived", "100 * mean(identity scope, lift assignment, geolocation, tourism exposure, hotel outcome, membership history, infrastructure completeness, snow/climate)", "quality indicator", "Not an opportunity, performance, or causal-effect score"),
        ("data_quality_warnings", "resort_data_quality", "Pipe-delimited unresolved evidence dimensions", "labels", "string", "resort listing", "current checkpoint", "DERIVED_MULTI_SOURCE", "derived", "deterministic component-level warning rules", "quality indicator", "Weak observations remain visible"),
        ("reviewed_destination_unit_id", "resort_municipality_crosswalk", "Reviewed destination unit linked to a supplied resort listing where available", "identifier", "string", "resort listing", "review snapshot", "DESTINATION_SCOPE_OFFICIAL_SET", "derived", "manual destination review keyed by resort_id", "entity resolution", "Blank for listings outside the 18 candidate entry/outcome links"),
        ("causal_exposure_approved", "resort_municipality_crosswalk", "Whether point containment has been approved as a causal tourism exposure", "boolean", "boolean", "resort listing", "review snapshot", "DERIVED_MULTI_SOURCE", "derived", "always false at this checkpoint", "quality gate", "Point containment remains distinct from tourism exposure"),
        ("scope_review_status", "treatment_destination_units", "Reviewed outcome-scope decision for a destination unit", "category", "string", "reviewed destination", "review snapshot", "DESTINATION_SCOPE_OFFICIAL_SET", "manual review", "complete observed municipal scope, core-municipality proxy, or excluded incomplete composite", "quality gate", "An approved outcome proxy is not a causal exposure approval"),
        ("eligible_for_reviewed_outcome_panel", "treatment_destination_units", "Whether the reviewed unit has a usable explicitly defined municipality outcome scope", "boolean", "boolean", "reviewed destination", "review snapshot", "DESTINATION_SCOPE_OFFICIAL_SET", "derived", "scope decision passes and every selected municipality exists in the hotel panel", "sample inclusion", "Three composite destinations are excluded"),
        ("municipality_weight", "treatment_destination_municipality", "Additive weight applied to a municipality total", "multiplier", "float", "destination-to-municipality link", "review snapshot", "DESTINATION_SCOPE_OFFICIAL_SET", "manual review", "1.0 for each included municipality", "outcome aggregation", "Weights are not normalised because hotel nights are counts"),
        ("effective_month", "municipality_treatment_events", "Monthly analytical date assigned to a documented entry or exit event", "date", "date", "reviewed destination", "event month", "MAGIC_OFFICIAL_EVIDENCE_SET", "derived", "exact validity date/month where documented; otherwise explicit May analytical anchor", "treatment timing candidate", "Precision is stored separately and causal-ready remains false"),
        ("component_count_change", "municipality_treatment_events", "Change in the number of local destination components covered by base membership", "count", "integer", "reviewed destination", "event month", "DERIVED_MULTI_SOURCE", "derived", "+1 per documented component entry; reviewed exit removes active components", "treatment intensity candidate", "Not an independent treated-unit count"),
        ("hotel_overnights", "destination_month_panel", "Additive hotel overnight stays across the reviewed municipality outcome scope", "overnight stays", "float", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "sum(municipality hotel_overnights * 1.0), missing unless every scoped municipality is observed", "outcome", "No imputation"),
        ("complete_outcome_scope", "destination_month_panel", "Whether all municipalities in the reviewed scope have an observed hotel-night value", "boolean", "boolean", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "observed municipality count equals expected municipality count", "outcome quality", "False rows retain a missing aggregate"),
        ("hotel_beds_available", "destination_month_panel", "Additive available beds across the reviewed municipality outcome scope", "beds", "float", "reviewed destination", "monthly", "BFS_HOTEL_CAPACITY_DATA", "derived", "sum(municipality beds * 1.0), missing unless every scoped municipality is observed", "time-varying supply confounder", "No imputation"),
        ("hotel_rooms_available", "destination_month_panel", "Additive available rooms across the reviewed municipality outcome scope", "rooms", "float", "reviewed destination", "monthly", "BFS_HOTEL_CAPACITY_DATA", "derived", "sum(municipality rooms * 1.0), missing unless every scoped municipality is observed", "time-varying supply confounder", "No imputation"),
        ("hotel_establishments_open", "destination_month_panel", "Additive open establishments across the reviewed municipality outcome scope", "establishments", "float", "reviewed destination", "monthly", "BFS_HOTEL_CAPACITY_DATA", "derived", "sum(municipality establishments * 1.0), missing unless every scoped municipality is observed", "time-varying supply confounder", "No imputation"),
        ("complete_capacity_scope", "destination_month_panel", "Whether supply is observed for every municipality in the reviewed scope", "boolean", "boolean", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "establishments, rooms, and beds observed for all scoped municipalities", "capacity quality", "False rows retain missing capacity aggregates"),
        ("hotel_overnights_per_available_bed_month", "destination_month_panel", "Monthly live-table overnight stays per summed available bed", "overnight stays per bed-month", "float", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "summed live-table overnight stays / summed beds when beds > 0", "descriptive capacity-adjusted demand", "Not the official occupancy rate"),
        ("hotel_bed_occupancy_rate_pct", "destination_month_panel", "Official bed occupancy rate for single-municipality destination units", "percent", "float", "reviewed destination", "monthly", "BFS_HOTEL_CAPACITY_DATA", "cleaned source", "retained only when destination scope has exactly one municipality", "descriptive capacity utilisation", "Not aggregated for Meiringen-Hasliberg"),
        ("snow_depth_mean_cm", "destination_month_panel", "Unweighted mean monthly snow depth across unique assigned SLF proxy stations", "centimetres", "float", "reviewed destination via station proxy", "monthly", "SLF_IMIS_DAILY_SNOW", "derived", "mean station-month snow_depth_mean_cm only when every assigned station month has >=80% daily coverage", "time-varying snow proxy", "Not direct slope snow; missing months are not imputed"),
        ("complete_snow_proxy", "destination_month_panel", "Whether every assigned SLF station-month passes the daily observation coverage gate", "boolean", "boolean", "reviewed destination via station proxy", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "all assigned station months have >=80% valid daily HS coverage", "snow data quality", "False for future/unavailable months"),
        ("destination_snow_proxy_quality", "destination_month_panel", "Worst resort-to-station comparability class among destination components", "category", "string", "reviewed destination via station proxy", "snapshot", "DERIVED_MULTI_SOURCE", "derived", "worst of high/moderate/low component links", "snow data quality", "Comparability class, not accuracy"),
        ("air_temperature_mean_c", "destination_month_panel", "Unweighted mean monthly temperature across unique assigned SwissMetNet proxy stations", "degrees Celsius", "float", "reviewed destination via station proxy", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "mean station-month air_temperature_mean_c only when every assigned station month passes the 80% gate", "time-varying regional weather proxy", "Not piste microclimate; missing months are not imputed"),
        ("air_temperature_anomaly_c", "destination_month_panel", "Unweighted mean station-specific temperature anomaly across unique assigned stations", "degrees Celsius", "float", "reviewed destination via station proxy", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "mean station-month anomaly relative to each station's 2013-2025 same-month analytical normal", "time-varying regional weather proxy", "Not an official climate-normal anomaly"),
        ("precipitation_total_mm_mean_across_stations", "destination_month_panel", "Unweighted mean monthly precipitation total across unique assigned SwissMetNet stations", "millimetres", "float", "reviewed destination via station proxy", "monthly", "METEOSWISS_SMN_DAILY_SELECTED", "derived", "mean station-month precipitation_total_mm only when every assigned station month passes the 80% gate", "time-varying regional weather proxy", "Not summed across stations; 06:00-to-06:00 UTC daily window"),
        ("complete_weather_proxy", "destination_month_panel", "Whether every assigned SwissMetNet station-month passes the four-parameter coverage gate", "boolean", "boolean", "reviewed destination via station proxy", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "all assigned station months have >=80% coverage for mean/min/max temperature and precipitation", "weather data quality", "False for unavailable future months and five in-window destination-months"),
        ("destination_weather_proxy_quality", "destination_month_panel", "Worst horizontal-distance comparability class among destination components", "category", "string", "reviewed destination via station proxy", "snapshot", "DERIVED_MULTI_SOURCE", "derived", "worst of high/moderate/low component links", "weather data quality", "Comparability class, not accuracy"),
        ("weather_causal_covariate_approved", "destination_month_panel", "Whether the regional weather proxy has passed all causal-use validation gates", "boolean", "boolean", "reviewed destination via station proxy", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "always false at this checkpoint", "quality gate", "Next-nearest station and TabsM/RhiresM gridded-product sensitivities are complete, but the grids share station inputs and no piste or causal validation is established"),
        ("assumed_active_component_count", "destination_month_panel", "Diagnostic count of entered components carried forward until a documented exit", "count", "integer", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "cumulative documented component entries with documented exit override", "treatment intensity candidate", "Continuity is an unverified assumption"),
        ("event_time_months", "destination_month_panel", "Months relative to the first analytical membership anchor", "months", "integer", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "calendar month difference from first_analysis_anchor", "event-time index", "Not sufficient for causal event-study identification"),
        ("causal_ready", "destination_month_panel", "Whether the destination-month row passes all causal evidence gates", "boolean", "boolean", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "always false at this checkpoint", "quality gate", "Treatment intensity, confounding, spillovers, and controls remain unresolved"),
        ("membership_status", "magic_pass_membership_status_by_season", "Evidence status for a reviewed destination in each annual Magic Pass season", "category", "string", "reviewed destination", "annual pass season", "MAGIC_OFFICIAL_EVIDENCE_SET", "manual evidence audit", "documented active, unverified active continuity, not yet entered, or documented inactive after exit", "treatment history", "Missing annual evidence is never silently filled"),
        ("documented_active", "magic_pass_membership_status_by_season", "Whether explicit dated evidence documents active base membership in the season", "boolean", "boolean", "reviewed destination", "annual pass season", "MAGIC_OFFICIAL_EVIDENCE_SET", "derived evidence flag", "true only for entry, roster/map, operator/tourism continuation, or last-active exit evidence", "treatment history quality", "False can mean unverified, not documented non-membership; true does not establish identical summer access or daily operation"),
        ("winter_access_status", "magic_pass_membership_status_by_season", "Evidence status of included winter access for the reviewed destination-season", "category", "string", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "reviewed derivation", "documented from annual symbol/list or base-membership evidence; unknown when membership continuity is unverified", "seasonal treatment description", "Does not document daily operation or lift-level scope"),
        ("summer_access_status", "magic_pass_membership_status_by_season", "Evidence status of included summer access for the reviewed destination-season", "category", "string", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "reviewed derivation", "documented only from named annual summer lists or summer-winter symbols; otherwise explicit unknown/not-included/not-applicable", "seasonal treatment description", "Absence is coded only from a complete annual publication with a summer distinction"),
        ("summer_access_documented", "magic_pass_membership_status_by_season", "Whether the annual publication documents summer access for at least one published label in the reviewed unit", "boolean", "boolean", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "derived evidence flag", "published_summer_winter_labels is non-empty", "seasonal treatment description", "For mixed units this does not apply to every component"),
        ("offering_scope_status", "magic_pass_membership_status_by_season", "Scope qualification for winter/summer offering evidence within a reviewed destination", "category", "string", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "manual evidence classification", "preserve all-component, mixed-component, composite-name and winter-only distinctions", "entity scope", "Never treated as identity equivalence or accommodation-market exposure"),
        ("published_summer_winter_labels", "magic_pass_membership_status_by_season", "Pipe-separated labels carrying the annual summer-winter symbol or appearing in the complete summer list", "label list", "string", "official published destination labels", "annual pass season", "MAGIC_OFFICIAL_EVIDENCE_SET", "manual visual transcription", "transcribed from the cited annual source page", "seasonal treatment evidence", "Labels are retained verbatim enough for audit and are not forced to listing IDs"),
        ("published_winter_only_labels", "magic_pass_membership_status_by_season", "Pipe-separated labels carrying only winter access in the complete annual publication", "label list", "string", "official published destination labels", "annual pass season", "MAGIC_OFFICIAL_EVIDENCE_SET", "manual visual transcription", "transcribed from the cited annual source page", "seasonal treatment evidence", "Includes the founding pass, which had no summer validity"),
        ("offering_source_id", "magic_pass_membership_status_by_season", "Source identifier for the annual winter/summer classification", "identifier", "string", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "lineage", "copied from page-referenced offering metadata", "provenance", "Blank where individual annual modality evidence is unavailable"),
        ("offering_source_page", "magic_pass_membership_status_by_season", "One-based page or single-image locator supporting the annual winter/summer classification", "page or image locator", "string", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "lineage", "copied from page/image-referenced offering metadata", "provenance", "Every nonblank locator is validated against the checksum-cached publication"),
        ("offering_evidence_type", "magic_pass_membership_status_by_season", "Type of annual publication used for winter/summer classification", "category", "string", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "manual evidence classification", "founding winter validity, complete named summer list, symbol map or symbol list", "provenance", "Does not upgrade causal readiness"),
        ("offering_evidence_note", "magic_pass_membership_status_by_season", "Source-level note explaining the annual winter/summer evidence", "text", "string", "reviewed destination", "annual pass season", "DERIVED_MAGIC_ANNUAL_OFFERING", "manual evidence note", "copied from versioned offering metadata", "provenance", "Read with offering_scope_status and published labels"),
        ("continuity_fully_documented", "membership_continuity_audit", "Whether every active season from first entry through exit or 2025/2026 has explicit evidence", "boolean", "boolean", "reviewed destination", "2017/2018-2025/2026", "MAGIC_OFFICIAL_EVIDENCE_SET", "derived audit", "no unverified_active_continuity season in the required active window", "quality gate", "Does not resolve confounding, spillovers, or controls"),
        ("known_magic_exposure_from_resolved_links", "control_contamination_audit", "Whether any resort point in the municipality has a resolved historical or current Magic Pass link", "boolean", "boolean", "municipality reached by resort point", "historical plus current snapshot", "DERIVED_MULTI_SOURCE", "derived screen", "any linked resort_id appears in a base-entry event or current official-map candidate link", "control contamination", "False is only an upper-bound candidate because unresolved official labels remain"),
        ("minimum_resort_point_distance_km", "treatment_control_candidate_matrix", "Minimum great-circle distance between a donor-municipality resort point and a treated destination component point", "kilometres", "float", "treatment-donor pair", "review snapshot", "GEOADMIN_MUNICIPALITY_IDENTIFY", "derived geospatial screen", "minimum haversine distance across supplied resort points", "spillover screen", "Point distance does not prove absence of tourism spillovers"),
        ("provisional_donor_30km_36pre", "treatment_control_candidate_matrix", "Mechanical donor-screen flag using resolved membership, geography, and outcome coverage", "boolean", "boolean", "treatment-donor pair", "monthly coverage snapshot", "DERIVED_MULTI_SOURCE", "derived screen", "no resolved Magic exposure AND not treated scope AND distance > 30 km AND >=36 pre months AND >=24 post months", "donor candidate", "Not an approved causal control; 30 km is a sensitivity threshold, not an identification result"),
        ("provisional_donor_50km_36pre", "treatment_control_candidate_matrix", "More conservative distance-sensitivity donor flag", "boolean", "boolean", "treatment-donor pair", "monthly coverage snapshot", "DERIVED_MULTI_SOURCE", "derived screen", "same as provisional_donor_30km_36pre but distance > 50 km", "donor sensitivity", "Not an approved causal control; geographic distance alone does not clear spillovers"),
        ("causal_control_approved", "treatment_control_candidate_matrix", "Whether the donor passes all causal control audits", "boolean", "boolean", "treatment-donor pair", "review snapshot", "DERIVED_MULTI_SOURCE", "derived", "always false at this checkpoint", "quality gate", "Unresolved membership, spillovers, and time-varying confounders remain"),
        ("paired_pre_outcome_months", "donor_pretrend_comparability", "Months in the 36-month pre-anchor window with observed outcomes for both treatment and donor", "months", "integer", "treatment-donor pair", "36-month pre-anchor window", "DERIVED_DONOR_PRETREND_SCREEN", "derived", "count of dates where both hotel_overnights values are observed", "pretrend data quality", "At least 30 required for the descriptive rank"),
        ("pre_log_outcome_correlation", "donor_pretrend_comparability", "Correlation of paired log1p monthly hotel overnight stays in the pre-window", "correlation", "float", "treatment-donor pair", "36-month pre-anchor window", "DERIVED_DONOR_PRETREND_SCREEN", "derived", "Pearson correlation of paired log1p outcomes", "descriptive pretrend screen", "Seasonality can inflate correlation; not a parallel-trends test"),
        ("pre_monthly_log_trend_gap_abs", "donor_pretrend_comparability", "Absolute gap between treated and donor monthly log trends after calendar-month adjustment", "log points per month", "float", "treatment-donor pair", "36-month pre-anchor window", "DERIVED_DONOR_PRETREND_SCREEN", "derived", "absolute difference between separate OLS time coefficients with calendar-month indicators", "descriptive pretrend screen", "Short-window descriptive slope without causal interpretation"),
        ("descriptive_comparability_score", "donor_pretrend_comparability", "Within-treatment heuristic score used to prioritise manual donor review", "0-100 relative score", "float", "treatment-donor pair", "36-month pre-anchor window plus current structure snapshot", "DERIVED_DONOR_PRETREND_SCREEN", "derived", "100 * (1 - mean within-treatment percentile rank across nine lower-is-better gaps)", "descriptive prioritisation", "Scores are not comparable across treatments and do not approve controls"),
        ("comparability_rank", "donor_pretrend_comparability", "Within-treatment rank of the descriptive comparability score", "rank", "integer", "treatment-donor pair", "review snapshot", "DERIVED_DONOR_PRETREND_SCREEN", "derived", "descending score rank among usable provisional donors", "manual review priority", "Top five are shortlisted; rank is not a causal weight"),
        ("pretrend_screen_usable", "donor_pretrend_comparability", "Whether the pair has enough outcome months and comparability components for descriptive ranking", "boolean", "boolean", "treatment-donor pair", "36-month pre-anchor window", "DERIVED_DONOR_PRETREND_SCREEN", "derived", ">=30 paired outcome months and >=6 available score components", "pretrend data quality", "Does not imply causal usability"),
        ("calendar_quarter", "temporal_controls_month", "Gregorian calendar quarter", "quarter", "integer", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "quarter(date)", "time control", "Deterministic calendar field"),
        ("magic_pass_season", "temporal_controls_month", "May-April season label keyed by the May start year", "season label", "string", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "year/year+1 if month >= May, otherwise year-1/year", "time control", "Does not override product-specific validity dates"),
        ("winter_month", "temporal_controls_month", "Analyst-defined November-April winter month", "boolean", "boolean", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "month in {11,12,1,2,3,4}", "seasonality control", "Broad analytical season; operation dates vary by resort"),
        ("summer_month", "temporal_controls_month", "Analyst-defined May-October summer month", "boolean", "boolean", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "month in {5,6,7,8,9,10}", "seasonality control", "Broad analytical season; operation dates vary by resort"),
        ("christmas_new_year_peak_month", "temporal_controls_month", "Whether the month is December or January", "boolean", "boolean", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "calendar month in {12,1}", "peak-season control", "Monthly flag does not isolate exact holiday weeks"),
        ("easter_month", "temporal_controls_month", "Whether Gregorian Easter Sunday falls in the month", "boolean", "boolean", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "Anonymous Gregorian Easter algorithm", "holiday timing control", "Does not encode canton-specific school holidays"),
        ("covid_sensitivity_month", "temporal_controls_month", "Broad 2020-2022 disruption sensitivity flag", "boolean", "boolean", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "true from 2020-03 through 2022-04 inclusive", "COVID sensitivity", "Not a legal restriction chronology or sufficient causal adjustment"),
        ("covid_sensitivity_phase", "temporal_controls_month", "Pre, broad sensitivity, or post period label", "category", "string", "all destinations", "monthly", "DERIVED_TEMPORAL_CONTROLS", "derived", "pre_2020_03, sensitivity_2020_03_to_2022_04, or post_2022_04", "COVID sensitivity", "Analyst-defined periodisation"),
        ("alternative_station_code", "resort_snow_alternative_station_sensitivity", "Next-nearest distinct eligible SLF station used for the robustness perturbation", "identifier", "string", "reviewed resort component", "2013/14-2025/26", "DERIVED_SNOW_STATION_SENSITIVITY", "derived linkage", "nearest eligible code after excluding the primary selected station", "snow proxy sensitivity", "Not an optimised or piste-level substitute"),
        ("alternative_station_distance_km", "resort_snow_alternative_station_sensitivity", "Great-circle distance from the resort point to the alternative station", "kilometres", "float", "reviewed resort component", "station snapshot", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "haversine distance", "snow proxy quality", "Does not capture terrain barriers or aspect"),
        ("common_usable_winters", "resort_snow_alternative_station_sensitivity", "Winters usable for both primary and alternative stations", "winter seasons", "integer", "reviewed resort component", "2013/14-2025/26", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "count of common winters where both stations meet the 80% within-winter gate", "snow sensitivity data quality", "At least eight required for an agreement grade"),
        ("winter_mean_depth_correlation", "resort_snow_alternative_station_sensitivity", "Correlation of November-April mean snow depth between selected and alternative stations", "correlation", "float", "reviewed resort component", "common usable winters", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "Pearson correlation across common usable winters", "snow proxy sensitivity", "Co-movement does not imply equal absolute depth"),
        ("mean_absolute_winter_depth_difference_cm", "resort_snow_alternative_station_sensitivity", "Mean absolute selected-versus-alternative gap in winter mean snow depth", "centimetres", "float", "reviewed resort component", "common usable winters", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "mean(abs(selected winter mean HS - alternative winter mean HS))", "snow proxy sensitivity", "Absolute levels can remain materially station-dependent"),
        ("relative_mean_absolute_depth_difference", "resort_snow_alternative_station_sensitivity", "Mean absolute winter-depth gap relative to the selected-station mean", "share", "float", "reviewed resort component", "common usable winters", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "mean absolute depth difference / selected mean depth", "snow proxy sensitivity", "Descriptive scale-normalised discrepancy"),
        ("absolute_reliability_share_difference", "resort_snow_alternative_station_sensitivity", "Absolute gap between pooled shares of observed winter days with snow depth at least 30 cm", "share", "float", "reviewed resort component", "common usable winters", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "abs(selected pooled reliability share - alternative pooled reliability share)", "snow proxy sensitivity", "External-station reliability proxy only"),
        ("trend_direction_agrees", "resort_snow_alternative_station_sensitivity", "Whether selected and alternative linear winter-depth slopes have the same sign", "boolean", "boolean", "reviewed resort component", "common usable winters", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "selected slope * alternative slope >= 0", "snow trend sensitivity", "No uncertainty test; short descriptive series"),
        ("alternative_station_agreement", "resort_snow_alternative_station_sensitivity", "Rule-based overall agreement grade for the station perturbation", "category", "string", "reviewed resort component", "common usable winters", "DERIVED_SNOW_STATION_SENSITIVITY", "derived", "high/moderate/low thresholds over correlation, relative depth gap and reliability gap", "snow proxy sensitivity", "Conservative descriptive grade; not measurement accuracy"),
        ("causal_covariate_approved", "resort_snow_alternative_station_sensitivity", "Whether the snow proxy passes the causal covariate gate", "boolean", "boolean", "reviewed resort component", "review checkpoint", "DERIVED_SNOW_STATION_SENSITIVITY", "quality gate", "always false at this checkpoint", "causal readiness", "Independent gridded sensitivity and snowmaking/operation data remain missing"),
        ("minimum_distance_to_resolved_magic_km", "donor_network_spillover_audit", "Minimum great-circle distance from any donor-municipality resort point to any resolved Magic Pass resort point", "kilometres", "float", "apparent donor municipality", "historical plus current snapshot", "DERIVED_DONOR_NETWORK_SPILLOVER_AUDIT", "derived", "minimum haversine distance over donor and resolved-Magic resort-point pairs", "network spillover sensitivity", "Resolved Magic points are a lower bound and not tourism catchments"),
        ("network_distance_band", "donor_network_spillover_audit", "Sensitivity band for network-wide Magic proximity", "category", "string", "apparent donor municipality", "historical plus current snapshot", "DERIVED_DONOR_NETWORK_SPILLOVER_AUDIT", "derived", "within 20 km, 20-30 km, 30-50 km or beyond 50 km", "network spillover sensitivity", "Thresholds are not causal rules"),
        ("network_spillover_cleared_30km", "donor_network_spillover_audit", "Whether every resolved Magic resort point is more than 30 km from donor resort points", "boolean", "boolean", "apparent donor municipality", "historical plus current snapshot", "DERIVED_DONOR_NETWORK_SPILLOVER_AUDIT", "derived screen", "minimum network distance > 30 km", "network spillover sensitivity", "Does not prove absence of spillovers"),
        ("same_lift_cluster_as_resolved_magic", "donor_network_spillover_audit", "Whether a donor listing shares a preserved lift cluster with a resolved Magic listing", "boolean", "boolean", "apparent donor municipality", "current listing/cluster snapshot", "DERIVED_DONOR_NETWORK_SPILLOVER_AUDIT", "derived screen", "intersection of donor and resolved-Magic cluster IDs", "domain overlap risk", "Existing clusters are provisional geographic groupings"),
        ("magic_roster_source_id", "donor_shortlist_final_audit", "Complete official annual Magic Pass roster reviewed for the donor at the treatment anchor", "source identifier", "string", "treatment-donor pair", "treatment-specific season", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "manual evidence linkage", "versioned review config linked to checksum-cached annual publication", "historical control eligibility", "Blank for pairs already deprioritised by network distance"),
        ("donor_roster_labels_checked", "donor_shortlist_final_audit", "Station and place-name variants searched in the complete annual roster", "labels", "pipe-delimited string", "treatment-donor pair", "treatment-specific season", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "manual review field", "reviewer-recorded station/place variants", "historical control eligibility", "Label review is not a corporate-register affiliate audit"),
        ("competing_pass_at_anchor_status", "donor_shortlist_final_audit", "Qualified status of competing multi-resort pass evidence around the treatment anchor", "category", "string", "treatment-donor pair", "treatment-specific anchor", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "manual evidence classification", "exact join to page-referenced review config", "competing-network confounding", "Blank for pairs already deprioritised by network distance"),
        ("local_tourism_shock_status", "donor_shortlist_final_audit", "Qualified result of the donor operator investment and local tourism shock review", "category", "string", "treatment-donor pair", "treatment-specific anchor", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "manual evidence classification", "exact join to page-referenced review config", "time-varying confounding", "Every remote pair has a documented overlapping donor-specific shock"),
        ("historical_magic_nonmembership_status", "donor_shortlist_final_audit", "Whether a complete annual roster documents absence under reviewed donor station/place labels", "category", "string", "treatment-donor pair", "treatment-specific history", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "quality gate", "manual complete-roster review; never inferred from missing resolved links", "control eligibility", "All seven remote pairs have documented label absence; this is not corporate-register affiliate proof"),
        ("historical_magic_roster_absence_documented", "donor_shortlist_final_audit", "Whether complete-roster station/place-label absence is documented", "boolean", "boolean", "treatment-donor pair", "treatment-specific history", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "derived quality flag", "historical status equals the documented complete-roster absence category", "control eligibility", "Necessary but not sufficient for causal-control approval"),
        ("accessibility_review_status", "donor_shortlist_final_audit", "Status of road/rail/accessibility review or reason it is moot after exclusion", "category", "string", "treatment-donor pair", "treatment-specific anchor", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "manual evidence classification", "exact join to reviewed evidence config", "time-varying confounding", "Minschuns has an access-replacement project; other remote pairs are already excluded independently"),
        ("accessibility_review_completed_or_moot", "donor_shortlist_final_audit", "Whether accessibility was reviewed or became unnecessary after an independent exclusion", "boolean", "boolean", "treatment-donor pair", "review snapshot", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "derived review flag", "accessibility status contains no pending marker", "review completeness", "Does not mean historical accessibility is stable"),
        ("final_manual_review_decision", "donor_shortlist_final_audit", "Current evidence-priority decision after network distance and external-shock review", "category", "string", "treatment-donor pair", "review snapshot", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "review decision", "distance-band priority plus exact reviewed external-shock config", "donor triage", "A retain decision means more audit is needed, not approval"),
        ("remaining_deep_audit_candidate", "donor_shortlist_final_audit", "Whether the pair remains prioritised for deeper historical donor audit", "boolean", "boolean", "treatment-donor pair", "review snapshot", "DERIVED_DONOR_EXTERNAL_SHOCK_AUDIT", "derived gate", "final decision equals retain_for_deeper_manual_audit_competing_pass_risk", "donor triage", "No shortlisted pair survives at this checkpoint"),
        ("representative_point_distance_to_destination_km", "treatment_municipality_distance_exposure", "Minimum projected distance from the municipality's interior representative point to a treated destination component point", "kilometres", "float", "treated destination by hotel municipality", "2026 boundary snapshot", "DERIVED_TREATMENT_DISTANCE_GRADIENT", "derived", "minimum EPSG:2056 point distance across destination components", "distance exposure diagnostic", "Representative point is not a population, hotel or transport centroid"),
        ("minimum_polygon_distance_to_destination_km", "treatment_municipality_distance_exposure", "Minimum projected distance from the municipality polygon to a treated destination component point", "kilometres", "float", "treated destination by hotel municipality", "2026 boundary snapshot", "DERIVED_TREATMENT_DISTANCE_GRADIENT", "derived", "minimum EPSG:2056 polygon-to-point distance across components", "distance exposure diagnostic", "Zero when any component point is inside the municipality"),
        ("boundary_bfs_id_2026", "treatment_municipality_distance_exposure", "BFS identifier of the current 2026 polygon used for distance", "identifier", "integer", "hotel municipality series", "2026 boundary snapshot", "SWISSTOPO_BOUNDARIES_2026", "source/bridge", "same as hotel BFS except explicit Moutier 700 to 6831 bridge", "boundary lineage", "Both original hotel-series ID and current boundary ID are retained"),
        ("boundary_bfs_bridge_status", "treatment_municipality_distance_exposure", "Whether the hotel-series BFS identifier required an explicit current-boundary bridge", "category", "string", "hotel municipality series", "2026 boundary snapshot", "DERIVED_TREATMENT_DISTANCE_GRADIENT", "derived lineage", "same_bfs_id or explicit Moutier bridge", "boundary quality", "Not a full historical boundary harmonisation"),
        ("representative_distance_band", "treatment_municipality_distance_exposure", "Common same-destination representative-point distance band", "category", "string", "treated destination by hotel municipality", "2026 boundary snapshot", "DERIVED_TREATMENT_DISTANCE_GRADIENT", "derived", "0-15, 15-30, 30-50, 50-100 or over 100 km", "distance exposure diagnostic", "Band thresholds are sensitivity choices"),
        ("descriptive_log_change_post_minus_pre", "treatment_distance_gradient_diagnostic", "Difference between mean log1p monthly overnight stays in adjacent 24-month post and pre windows", "log points", "float", "treated destination by hotel municipality", "treatment-specific 24-month windows", "DERIVED_TREATMENT_DISTANCE_GRADIENT", "derived", "mean post log1p nights - mean pre log1p nights", "descriptive outcome diagnostic", "No common-shock, trend or treatment-intensity adjustment"),
        ("distance_gradient_usable", "treatment_distance_gradient_diagnostic", "Whether at least 18 outcome months are observed in each adjacent window", "boolean", "boolean", "treated destination by hotel municipality", "treatment-specific 24-month windows", "DERIVED_TREATMENT_DISTANCE_GRADIENT", "derived quality", "pre observed months >=18 and post observed months >=18", "distance diagnostic quality", "Does not imply causal usability"),
        ("descriptive_near_minus_far_log_change", "treatment_distance_near_far_contrast", "Near-municipality median log change minus far-municipality median log change for the same destination", "log points", "float", "reviewed treated destination", "treatment-specific 24-month windows", "DERIVED_TREATMENT_DISTANCE_GRADIENT", "derived", "median change at <=30 km minus median change at >50 km; 30-50 km omitted", "distance-gradient diagnostic", "Exploratory contrast, not an effect estimate"),
    ]
    paths = {
        "hotel_municipality_month": ROOT / "data_processed" / "hotel_municipality_month.csv",
        "hotel_capacity_municipality_month": ROOT / "data_processed" / "hotel_capacity_municipality_month.csv",
        "hotel_municipality_month_enriched": ROOT / "data_processed" / "hotel_municipality_month_enriched.csv",
        "slf_snow_station_month": ROOT / "data_processed" / "slf_snow_station_month.csv",
        "slf_snow_station_winter": ROOT / "data_processed" / "slf_snow_station_winter.csv",
        "resort_snow_station_crosswalk": ROOT / "data_processed" / "resort_snow_station_crosswalk.csv",
        "resort_snow_vulnerability": ROOT / "data_processed" / "resort_snow_vulnerability.csv",
        "meteoswiss_station_month": ROOT / "data_processed" / "meteoswiss_station_month.csv",
        "resort_weather_station_crosswalk": ROOT / "data_processed" / "resort_weather_station_crosswalk.csv",
        "destination_weather_month": ROOT / "data_processed" / "destination_weather_month.csv",
        "resort_master": ROOT / "data_processed" / "resort_master.csv",
        "resort_point_municipality": ROOT / "data_processed" / "resort_point_municipality.csv",
        "magic_pass_membership_history": ROOT / "data_processed" / "magic_pass_membership_history.csv",
        "magic_pass_current_destinations": ROOT / "data_processed" / "magic_pass_current_destinations.csv",
        "resort_data_quality": ROOT / "data_processed" / "resort_data_quality.csv",
        "resort_municipality_crosswalk": ROOT / "data_processed" / "resort_municipality_crosswalk.csv",
        "treatment_destination_units": ROOT / "data_processed" / "treatment_destination_units.csv",
        "treatment_destination_municipality": ROOT / "data_processed" / "treatment_destination_municipality.csv",
        "municipality_treatment_events": ROOT / "data_processed" / "municipality_treatment_events.csv",
        "destination_month_panel": ROOT / "data_processed" / "destination_month_panel.csv",
        "magic_pass_membership_status_by_season": ROOT / "data_processed" / "magic_pass_membership_status_by_season.csv",
        "membership_continuity_audit": ROOT / "reports" / "membership_continuity_audit.csv",
        "control_contamination_audit": ROOT / "reports" / "control_contamination_audit.csv",
        "treatment_control_candidate_matrix": ROOT / "data_processed" / "treatment_control_candidate_matrix.csv",
        "donor_pretrend_comparability": ROOT / "data_processed" / "donor_pretrend_comparability.csv",
        "temporal_controls_month": ROOT / "data_processed" / "temporal_controls_month.csv",
        "resort_snow_alternative_station_sensitivity": ROOT / "data_processed" / "resort_snow_alternative_station_sensitivity.csv",
        "donor_network_spillover_audit": ROOT / "reports" / "donor_network_spillover_audit.csv",
        "donor_shortlist_final_audit": ROOT / "data_processed" / "donor_shortlist_final_audit.csv",
        "treatment_municipality_distance_exposure": ROOT / "data_processed" / "treatment_municipality_distance_exposure.csv",
        "treatment_distance_gradient_diagnostic": ROOT / "data_processed" / "treatment_distance_gradient_diagnostic.csv",
        "treatment_distance_near_far_contrast": ROOT / "reports" / "treatment_distance_near_far_contrast.csv",
    }
    scope_glossary = {
        "event_id": "Stable historical event identifier; preserved without merging events",
        "source_resort_name": "Original official entry label",
        "entry_season": "Original documented entry season, not inferred from current scope",
        "event_source_id": "Source ID of the original historical entry announcement",
        "event_source_page": "Page locator of the original historical entry announcement",
        "review_date": "Date of the analyst scope review",
        "review_class": "Foreign, composite component, overlapping scope, ambiguous scope or absent/unverified Swiss listing",
        "source_ids": "Pipe-separated source IDs supporting the qualified scope decision",
        "source_locators": "Human-readable source page/section locators",
        "review_note": "Scope decision, evidence and remaining limits",
        "identity_equivalence_approved": "Whether the relation is an approved identity equivalence; always false here",
        "causal_mapping_approved": "Whether the relation is approved causal exposure; always false here",
        "related_resort_ids": "Pipe-separated related listing IDs; not equivalent resort matches",
        "related_listing_count": "Number of related or risk-candidate listings, not independent treatments",
        "related_resort_id": "One related listing in a many-to-many scope relation",
        "point_municipality_bfs_id": "Current municipality containing the listing point; not full tourism catchment",
        "point_municipality_name": "Current point-container municipality name",
        "bfs_hotel_universe": "Whether the point municipality is in the supplied hotel outcome universe",
        "exclude_from_clean_donor_pool": "Conservative exclusion of linked point municipality from clean donor candidates",
        "exclusion_basis": "Precautionary scope relation; does not assert measured causal exposure",
        "scope_relation_risk": "At least one linked resort point has a composite, overlapping or ambiguous Magic scope relation",
        "scope_risk_listing_ids": "Deduplicated related listing IDs underlying municipal scope risk",
        "additional_scope_exclusion": "Scope-risk municipality not already excluded by resolved historical/current Magic links",
    }
    scope_paths = {
        "unmatched_magic_entry_review": ROOT / "reports/unmatched_magic_entry_review.csv",
        "magic_pass_scope_relations": ROOT / "data_processed/magic_pass_scope_relations.csv",
    }
    for table, path in scope_paths.items():
        paths[table] = path
        for variable in pd.read_csv(path, nrows=0).columns:
            definitions.append((variable, table, scope_glossary[variable], "count" if variable == "related_listing_count" else "flag" if variable.endswith("approved") or variable in {"bfs_hotel_universe", "exclude_from_clean_donor_pool"} else "identifier/text", "integer" if variable == "related_listing_count" else "boolean" if variable.endswith("approved") or variable in {"bfs_hotel_universe", "exclude_from_clean_donor_pool"} else "string", "entry label or listing relation", "event/review", "DERIVED_MAGIC_SCOPE_REVIEW", "reviewed derivation", "Exact reviewed config lookup and explicit relation expansion", "entity scope / control screening", "Not an approved identity or causal mapping"))
    for table in ["control_contamination_audit", "treatment_control_candidate_matrix"]:
        for variable in ["scope_relation_risk", "additional_scope_exclusion"] + (["scope_risk_listing_ids"] if table == "control_contamination_audit" else []):
            definitions.append((variable, table, scope_glossary[variable], "flag" if variable != "scope_risk_listing_ids" else "identifier list", "boolean" if variable != "scope_risk_listing_ids" else "string", "municipality", "whole-history conservative screen", "DERIVED_MAGIC_SCOPE_REVIEW", "derived", "Any linked listing risk; additional if not already resolved-exposed", "control contamination screening", "Precautionary exclusion; never causal approval"))

    path_c_paths = {
        "municipality_tourism_context_2025": ROOT / "data_processed/municipality_tourism_context_2025.csv",
        "path_c_cluster_tourism_context": ROOT / "data_processed/path_c_cluster_tourism_context.csv",
        "municipality_population_geometry_2026": ROOT / "data_processed/municipality_population_geometry_2026.csv",
        "path_c_cluster_accessibility_context": ROOT / "data_processed/path_c_cluster_accessibility_context.csv",
        "eurostat_population_grid_2021_swiss_region": ROOT / "data_processed/eurostat_population_grid_2021_swiss_region.csv",
        "path_c_cluster_cross_border_population_context": ROOT / "data_processed/path_c_cluster_cross_border_population_context.csv",
        "cross_border_population_candidate_summary": ROOT / "reports/cross_border_population_candidate_summary.csv",
        "resort_transport_accessibility_context": ROOT / "data_processed/resort_transport_accessibility_context.csv",
        "path_c_cluster_transport_accessibility_context": ROOT / "data_processed/path_c_cluster_transport_accessibility_context.csv",
        "transport_zone_proxy_audit": ROOT / "reports/transport_zone_proxy_audit.csv",
        "resort_public_transport_stop_context": ROOT / "data_processed/resort_public_transport_stop_context.csv",
        "path_c_cluster_public_transport_stop_context": ROOT / "data_processed/path_c_cluster_public_transport_stop_context.csv",
        "resort_national_road_proximity_context": ROOT / "data_processed/resort_national_road_proximity_context.csv",
        "path_c_cluster_national_road_proximity_context": ROOT / "data_processed/path_c_cluster_national_road_proximity_context.csv",
        "national_road_proximity_candidate_summary": ROOT / "reports/national_road_proximity_candidate_summary.csv",
        "resort_competing_pass_context": ROOT / "data_processed/resort_competing_pass_context.csv",
        "path_c_cluster_competing_pass_context": ROOT / "data_processed/path_c_cluster_competing_pass_context.csv",
        "competing_pass_candidate_summary": ROOT / "reports/competing_pass_candidate_summary.csv",
        "path_c_cluster_network_context": ROOT / "data_processed/path_c_cluster_network_context.csv",
        "path_c_cluster_network_pairs": ROOT / "reports/path_c_cluster_network_pairs.csv",
        "network_context_candidate_summary": ROOT / "reports/network_context_candidate_summary.csv",
        "path_c_cluster_geographic_sensitivity": ROOT / "data_processed/path_c_cluster_geographic_sensitivity.csv",
        "path_c_cluster_distance_rule_pairs": ROOT / "reports/path_c_cluster_distance_rule_pairs.csv",
        "cluster_geography_candidate_summary": ROOT / "reports/cluster_geography_candidate_summary.csv",
        "meteoswiss_alternative_station_month": ROOT / "data_processed/meteoswiss_alternative_station_month.csv",
        "weather_station_alternative_sensitivity": ROOT / "reports/weather_station_alternative_sensitivity.csv",
        "destination_weather_alternative_sensitivity": ROOT / "data_processed/destination_weather_alternative_sensitivity.csv",
        "weather_destination_alternative_summary": ROOT / "reports/weather_destination_alternative_summary.csv",
        "meteoswiss_gridded_component_month": ROOT / "data_processed/meteoswiss_gridded_component_month.csv",
        "weather_gridded_component_comparison": ROOT / "reports/weather_gridded_component_comparison.csv",
        "destination_weather_gridded_sensitivity": ROOT / "data_processed/destination_weather_gridded_sensitivity.csv",
        "weather_gridded_destination_summary": ROOT / "reports/weather_gridded_destination_summary.csv",
        "public_transport_journey_nodes": ROOT / "reports/public_transport_journey_nodes.csv",
        "treatment_municipality_public_transport_journey_samples": ROOT / "data_processed/treatment_municipality_public_transport_journey_samples.csv",
        "treatment_municipality_public_transport_journey_context": ROOT / "data_processed/treatment_municipality_public_transport_journey_context.csv",
        "public_transport_arrival_node_review": ROOT / "reports/public_transport_arrival_node_review.csv",
        "public_transport_historical_audit_plan": ROOT / "reports/public_transport_historical_audit_plan.csv",
        "treatment_municipality_distance_transport_comparison": ROOT / "data_processed/treatment_municipality_distance_transport_comparison.csv",
        "distance_transport_correlations_by_destination": ROOT / "reports/distance_transport_correlations_by_destination.csv",
        "distance_transport_band_summary": ROOT / "reports/distance_transport_band_summary.csv",
        "path_c_resort_cluster_features": ROOT / "data_processed/path_c_resort_cluster_features.csv",
        "path_c_cluster_segments": ROOT / "data_processed/path_c_cluster_segments.csv",
        "path_c_reviewed_treated_reference": ROOT / "data_processed/path_c_reviewed_treated_reference.csv",
        "path_c_candidate_analogues": ROOT / "data_processed/path_c_candidate_analogues.csv",
        "path_c_candidate_analogue_sensitivity": ROOT / "data_processed/path_c_candidate_analogue_sensitivity.csv",
        "magic_pass_decision_support": ROOT / "data_processed/magic_pass_decision_support.csv",
    }
    path_c_sources = {
        "municipality_tourism_context_2025": "DERIVED_TOURISM_DEPENDENCE_CONTEXT",
        "path_c_cluster_tourism_context": "DERIVED_TOURISM_DEPENDENCE_CONTEXT",
        "municipality_population_geometry_2026": "DERIVED_ACCESSIBILITY_CONTEXT",
        "path_c_cluster_accessibility_context": "DERIVED_ACCESSIBILITY_CONTEXT",
        "eurostat_population_grid_2021_swiss_region": "DERIVED_CROSS_BORDER_POPULATION_CONTEXT",
        "path_c_cluster_cross_border_population_context": "DERIVED_CROSS_BORDER_POPULATION_CONTEXT",
        "cross_border_population_candidate_summary": "DERIVED_CROSS_BORDER_POPULATION_CONTEXT",
        "resort_transport_accessibility_context": "DERIVED_TRANSPORT_ACCESSIBILITY_CONTEXT",
        "path_c_cluster_transport_accessibility_context": "DERIVED_TRANSPORT_ACCESSIBILITY_CONTEXT",
        "transport_zone_proxy_audit": "DERIVED_TRANSPORT_ACCESSIBILITY_CONTEXT",
        "resort_public_transport_stop_context": "DERIVED_PUBLIC_TRANSPORT_STOP_CONTEXT",
        "path_c_cluster_public_transport_stop_context": "DERIVED_PUBLIC_TRANSPORT_STOP_CONTEXT",
        "resort_national_road_proximity_context": "DERIVED_NATIONAL_ROAD_PROXIMITY_CONTEXT",
        "path_c_cluster_national_road_proximity_context": "DERIVED_NATIONAL_ROAD_PROXIMITY_CONTEXT",
        "national_road_proximity_candidate_summary": "DERIVED_NATIONAL_ROAD_PROXIMITY_CONTEXT",
        "resort_competing_pass_context": "DERIVED_COMPETING_PASS_CONTEXT",
        "path_c_cluster_competing_pass_context": "DERIVED_COMPETING_PASS_CONTEXT",
        "competing_pass_candidate_summary": "DERIVED_COMPETING_PASS_CONTEXT",
        "path_c_cluster_network_context": "DERIVED_PATH_C_NETWORK_CONTEXT",
        "path_c_cluster_network_pairs": "DERIVED_PATH_C_NETWORK_CONTEXT",
        "network_context_candidate_summary": "DERIVED_PATH_C_NETWORK_CONTEXT",
        "path_c_cluster_geographic_sensitivity": "DERIVED_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY",
        "path_c_cluster_distance_rule_pairs": "DERIVED_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY",
        "cluster_geography_candidate_summary": "DERIVED_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY",
        "meteoswiss_alternative_station_month": "DERIVED_WEATHER_STATION_SENSITIVITY",
        "weather_station_alternative_sensitivity": "DERIVED_WEATHER_STATION_SENSITIVITY",
        "destination_weather_alternative_sensitivity": "DERIVED_WEATHER_STATION_SENSITIVITY",
        "weather_destination_alternative_summary": "DERIVED_WEATHER_STATION_SENSITIVITY",
        "meteoswiss_gridded_component_month": "DERIVED_WEATHER_GRIDDED_SENSITIVITY",
        "weather_gridded_component_comparison": "DERIVED_WEATHER_GRIDDED_SENSITIVITY",
        "destination_weather_gridded_sensitivity": "DERIVED_WEATHER_GRIDDED_SENSITIVITY",
        "weather_gridded_destination_summary": "DERIVED_WEATHER_GRIDDED_SENSITIVITY",
        "public_transport_journey_nodes": "DERIVED_PUBLIC_TRANSPORT_JOURNEY_CONTEXT",
        "treatment_municipality_public_transport_journey_samples": "DERIVED_PUBLIC_TRANSPORT_JOURNEY_CONTEXT",
        "treatment_municipality_public_transport_journey_context": "DERIVED_PUBLIC_TRANSPORT_JOURNEY_CONTEXT",
        "public_transport_arrival_node_review": "DERIVED_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW",
        "public_transport_historical_audit_plan": "DERIVED_PUBLIC_TRANSPORT_HISTORICAL_AUDIT",
        "treatment_municipality_distance_transport_comparison": "DERIVED_DISTANCE_TRANSPORT_COMPARISON",
        "distance_transport_correlations_by_destination": "DERIVED_DISTANCE_TRANSPORT_COMPARISON",
        "distance_transport_band_summary": "DERIVED_DISTANCE_TRANSPORT_COMPARISON",
        "path_c_resort_cluster_features": "DERIVED_PATH_C_FEATURE_MATRIX",
        "path_c_cluster_segments": "DERIVED_PATH_C_SEGMENTATION_ANALOGUES",
        "path_c_reviewed_treated_reference": "DERIVED_PATH_C_SEGMENTATION_ANALOGUES",
        "path_c_candidate_analogues": "DERIVED_PATH_C_SEGMENTATION_ANALOGUES",
        "path_c_candidate_analogue_sensitivity": "DERIVED_PATH_C_AGGREGATION_SENSITIVITY",
        "magic_pass_decision_support": "DERIVED_PATH_C_DECISION_SUPPORT",
    }
    path_c_glossary = {
        "cluster_id": "Stable identifier of the preserved existing lift cluster used as the Path C analysis entity",
        "analysis_entity_level": "Explicit statement of the cluster-level analysis entity and its limitations",
        "cluster_display_name": "Deterministic display label built from up to three supplied listing names",
        "member_resort_ids": "All supplied resort listing IDs assigned to the existing lift cluster",
        "feature_temporal_status": "Whether structural features can be treated as pre-treatment; currently an undated snapshot",
        "review_class": "Transparent arrival-node class: named lift/ski access, named destination locality, or village/local-centre proxy",
        "review_basis": "Human-readable basis for accepting the current stop as a descriptive routing node",
        "user_fallback_rule": "Whether the researcher-authorised village-centre fallback was used",
        "absent_reference_dates": "Sampled active-service dates on which the selected node is absent from the GTFS network",
        "active_reference_day_count": "Number of the two sampled service dates on which the node occurs in the active GTFS network",
        "descriptive_routing_node_approved": "Whether the current node passes the versioned descriptive routing review",
        "historical_node_continuity_verified": "Whether the same node has been verified in the relevant historical timetable anchors",
        "name_distance_municipality_review_complete": "Whether name, mode, municipality and component-point distance checks are complete",
        "structural_feature_complete": "Whether altitude, ski-area kilometres and lift count are all observed",
        "candidate_for_path_c": "Initial apparent-nonmember candidate flag after resolved current, historical and scope relations are excluded",
        "candidate_interpretation": "Warning that the candidate flag is not verified non-membership",
        "reviewed_competing_pass_roster_count": "Number of official competing-pass products included in the scoped current review",
        "reviewed_competing_pass_area_count": "Number of named official pass-area rows included in the scoped current review",
        "competing_pass_linked": "Whether the supplied resort listing has an explicit reviewed link to at least one official area in the three reviewed rosters",
        "competing_pass_link_count": "Number of reviewed pass-area links for the supplied resort listing",
        "competing_pass_ids": "Pipe-separated identifiers of reviewed competing passes linked to the listing or cluster",
        "competing_pass_names": "Pipe-separated names of reviewed competing passes linked to the listing or cluster",
        "competing_pass_roster_versions": "Pipe-separated source roster versions attached to the listing links",
        "competing_pass_benefit_tiers": "Pipe-separated benefit categories retaining core unlimited, limited partner and included-region distinctions",
        "competing_pass_area_links": "Pipe-separated pass-ID and official-area-label pairs linked through the reviewed register",
        "competing_pass_mapping_bases": "Pipe-separated reviewed bases for linking an official area to supplied resort IDs",
        "competing_pass_limited_partner_benefit_linked": "Whether the listing is linked to an AlpsPass three-free-ski-days partner region",
        "competing_pass_core_or_included_region_linked": "Whether the listing is linked to an AlpsPass core region or an included Meilenweiss/Schneepass region",
        "competing_pass_roster_link_status": "Explicit link status whose no-link value does not verify absence from the competing-pass market",
        "competing_pass_market_absence_verified": "Whether absence from the competing-pass market is verified; always false in this scoped review",
        "competing_pass_context_temporal_scope": "Combined version statement for the three reviewed official roster snapshots",
        "competing_pass_context_interpretation": "Guardrail stating that current roster links are not historical competition intensity, market absence or a causal feature",
        "competing_pass_feature_approved": "Whether current competing-pass context is approved as a causal or pre-treatment model feature; always false",
        "competing_pass_link_source_ids": "Official source identifiers supporting the listing's explicit pass-area links",
        "competing_pass_review_source_ids": "All official source identifiers defining the scoped three-pass review universe",
        "cluster_competing_pass_listing_count": "Number of supplied resort listings assigned to the lift cluster",
        "cluster_listings_linked_to_reviewed_competing_pass": "Number of cluster listings with at least one explicit reviewed competing-pass area link",
        "cluster_competing_pass_linked_listing_share": "Share of cluster listings with at least one explicit reviewed competing-pass area link",
        "cluster_competing_pass_scope_status": "Whether the cluster has no reviewed link, partial listing links or links for every supplied listing",
        "cluster_competing_pass_linked_resort_ids": "Pipe-separated cluster listing IDs with at least one reviewed competing-pass link",
        "cluster_competing_pass_unlinked_resort_ids": "Pipe-separated cluster listing IDs without a link in the three reviewed rosters",
        "cluster_has_reviewed_competing_pass_link": "Whether any supplied listing in the cluster has a reviewed competing-pass link",
        "cluster_competing_pass_count": "Number of distinct reviewed competing passes linked to listings in the cluster",
        "cluster_competing_pass_ids": "Pipe-separated identifiers of reviewed competing passes linked within the cluster",
        "cluster_competing_pass_names": "Pipe-separated names of reviewed competing passes linked within the cluster",
        "cluster_competing_pass_area_links": "Pipe-separated pass-ID and official-area-label pairs linked within the cluster",
        "cluster_competing_pass_benefit_tiers": "Pipe-separated benefit tiers represented by reviewed listing links within the cluster",
        "cluster_limited_partner_benefit_listing_count": "Number of cluster listings linked to an AlpsPass three-free-ski-days partner benefit",
        "cluster_core_or_included_region_listing_count": "Number of cluster listings linked to a core or included competing-pass region",
        "network_context_latitude": "Median supplied listing latitude used as the focal lift-cluster location for current network distances",
        "network_context_longitude": "Median supplied listing longitude used as the focal lift-cluster location for current network distances",
        "network_distance_method": "Declared formula and coordinate representation used for current cluster-pair distances",
        "network_focal_cluster_excluded_from_all_neighbourhood_counts": "Whether every neighbourhood count excludes the focal cluster itself; always true",
        "historical_network_context_verified": "Whether the current directory/pass-network context has been reconstructed for historical pre-treatment dates; always false",
        "network_context_feature_approved": "Whether the network context is approved as a causal or historical pre-treatment feature; always false",
        "network_context_interpretation": "Guardrail stating that current straight-line directory/pass-network context is not historical market structure, travel time or causal competition",
        "network_context_source_ids": "Source identifiers for the cluster feature matrix and competing-pass context used in the network derivation",
        "focal_cluster_id": "Stable identifier of the focal cluster in an ordered non-self cluster pair",
        "focal_cluster_name": "Display name of the focal cluster in an ordered non-self cluster pair",
        "other_cluster_id": "Stable identifier of the other cluster in an ordered non-self cluster pair",
        "other_cluster_name": "Display name of the other cluster in an ordered non-self cluster pair",
        "great_circle_distance_km": "Great-circle distance between the two cluster median supplied-listing coordinates",
        "other_cluster_resolved_current_magic": "Whether the other cluster has a resolved link to the current official Magic Pass map",
        "other_cluster_reviewed_competing_pass_linked": "Whether the other cluster contains a listing linked to a reviewed competing-pass roster",
        "other_cluster_reviewed_competing_limited_partner": "Whether the other cluster contains an AlpsPass limited three-day partner link",
        "other_cluster_reviewed_competing_core_or_included": "Whether the other cluster contains a core or included competing-pass-region link",
        "other_cluster_in_reviewed_pass_network": "Whether the other cluster belongs to the union of resolved current Magic and reviewed competing-pass-linked clusters",
        "cluster_listing_point_count": "Number of supplied resort listing points assigned to the preserved lift cluster",
        "cluster_unique_coordinate_count": "Number of distinct supplied latitude/longitude pairs assigned to the preserved lift cluster",
        "within_cluster_listing_pair_count": "Number of unordered pairs of supplied listing points inside the preserved lift cluster",
        "within_cluster_pairwise_distance_min_km": "Minimum great-circle distance among listing-point pairs inside the preserved lift cluster; zero for a single listing",
        "within_cluster_pairwise_distance_median_km": "Median great-circle distance among listing-point pairs inside the preserved lift cluster; zero for a single listing",
        "within_cluster_pairwise_distance_max_km": "Maximum great-circle distance among listing-point pairs inside the preserved lift cluster; the observed listing-point diameter",
        "maximum_listing_distance_from_representative_median_coordinate_km": "Largest great-circle distance from a cluster listing point to the coordinate-wise median location",
        "cluster_listing_geographic_spread_band": "Descriptive band based on listing count and maximum within-cluster listing-point distance",
        "cluster_geographic_coherence_verified": "Whether the existing cluster has been certified as one geographically and commercially coherent destination; always false",
        "network_distance_sensitivity_feature_approved": "Whether the distance-rule sensitivity is approved as a causal or historical model feature; always false",
        "cluster_geography_sensitivity_interpretation": "Guardrail stating that listing-point spread and distance-rule sensitivity do not redefine clusters or establish historical/causal competition",
        "cluster_geography_sensitivity_source_ids": "Source identifiers for the resort master, Path C feature matrix and competing-pass context used in the sensitivity audit",
        "cross_cluster_listing_pair_count": "Number of cross-product supplied listing-point pairs represented by the ordered cluster pair",
        "minimum_listing_pair_distance_km": "Minimum great-circle distance across every supplied listing-point pair joining the two clusters",
        "median_listing_pair_distance_km": "Median great-circle distance across every supplied listing-point pair joining the two clusters",
        "representative_median_coordinate_distance_km": "Great-circle distance between the two coordinate-wise median cluster locations used in the baseline network context",
        "maximum_listing_pair_distance_km": "Maximum great-circle distance across every supplied listing-point pair joining the two clusters",
        "absolute_representative_vs_listing_pair_median_difference_km": "Absolute difference between coordinate-wise-median distance and median cross-listing-pair distance",
        "primary_weather_station_code": "SwissMetNet station selected as the nearest eligible primary regional weather proxy",
        "alternative_weather_station_code": "Next-nearest distinct eligible SwissMetNet station used in the weather assignment sensitivity",
        "alternative_station_selection_method": "Deterministic rule used to select the alternative SwissMetNet station",
        "common_usable_months": "Months in which both primary and alternative station proxies pass the common four-parameter coverage gate",
        "common_usable_winter_months": "November-April months in which both primary and alternative station proxies pass the coverage gate",
        "temperature_anomaly_correlation": "Pearson correlation between primary and alternative station-specific monthly temperature anomalies on common complete months",
        "winter_temperature_anomaly_correlation": "Pearson correlation between primary and alternative temperature anomalies in common complete November-April months",
        "temperature_anomaly_mean_absolute_difference_c": "Mean absolute difference between primary and alternative station-specific monthly temperature anomalies",
        "precipitation_anomaly_correlation": "Pearson correlation between primary and alternative station-specific monthly precipitation anomalies on common complete months",
        "winter_precipitation_anomaly_correlation": "Pearson correlation between primary and alternative precipitation anomalies in common complete November-April months",
        "precipitation_anomaly_mean_absolute_difference_mm": "Mean absolute difference between primary and alternative station-specific monthly precipitation anomalies",
        "weather_station_sensitivity_agreement": "Descriptive high, moderate or low agreement category from predeclared temperature- and precipitation-anomaly correlation thresholds",
        "both_weather_proxies_complete": "Whether both primary and alternative destination weather proxies are complete for the month",
        "temperature_anomaly_difference_alternative_minus_primary_c": "Alternative minus primary destination monthly temperature anomaly",
        "precipitation_anomaly_difference_alternative_minus_primary_mm": "Alternative minus primary destination monthly precipitation anomaly",
        "weather_station_sensitivity_interpretation": "Guardrail stating that next-nearest station sensitivity is not piste, gridded or causal validation",
        "weather_station_sensitivity_causal_covariate_approved": "Whether the weather proxy passes causal-covariate validation after this sensitivity; always false",
        "grid_cell_id": "Stable identifier constructed from the nearest common valid MeteoSwiss 1 km LV95 cell centre",
        "grid_cell_distance_to_component_m": "Planar LV95 distance from the supplied resort component point to the selected climate-grid cell centre",
        "gridded_weather_month_complete": "Whether both TabsM temperature and RhiresM precipitation are observed for the component-cell month",
        "complete_gridded_weather_proxy": "Whether every unique component grid cell expected for the destination is complete in the month",
        "both_station_and_grid_weather_complete": "Whether both the primary station and gridded destination weather proxies are complete in the month",
        "gridded_weather_sensitivity_agreement": "Descriptive high/moderate/low station-grid anomaly agreement category under predeclared thresholds",
        "gridded_weather_sensitivity_interpretation": "Guardrail stating that the monthly grid sensitivity is not an independent measurement network, piste microclimate or causal validation",
        "gridded_weather_causal_covariate_approved": "Whether the gridded-weather proxy passes causal-covariate validation; always false",
        "segment_id": "Stable label of the selected current structural k-means segment",
        "descriptive_profile": "Relative altitude, ski-area and lift-count description of the segment",
        "distance_to_segment_centroid": "Euclidean distance to the assigned centroid in three standardised structural features",
        "magic_member_comparability_score": "Empirical support percentage relative to leave-one-out nearest-current-member distances",
        "reviewed_treated_comparability_score": "Empirical support percentage relative to leave-one-out nearest-reviewed-treated distances",
        "magic_member_ood_flag": "Good, moderate or strong extrapolation against the resolved-current-member reference pool",
        "reviewed_treated_ood_flag": "Good, moderate or strong extrapolation against eight reviewed treated references",
        "analogue_descriptive_change_signal_pct": "Median unadjusted hotel-overnight change of the three closest reviewed treated destinations",
        "analogue_descriptive_change_range_low_pct": "Minimum of the three analogue change diagnostics; not a confidence bound",
        "analogue_descriptive_change_range_high_pct": "Maximum of the three analogue change diagnostics; not a confidence bound",
        "opportunity_signal_percentile": "Within-candidate percentile of the descriptive analogue change signal",
        "snow_vulnerability_percentile": "Within-candidate percentile of the SLF-station snow-vulnerability proxy",
        "strategic_need_status": "Completeness status of strategic need; qualified NPVM travel time and current stop proximity exist but approved catchment-level tourism dependence and validated destination accessibility remain missing",
        "predicted_uplift_pct": "Intentionally empty field because no causal or predictive uplift is supported",
        "uplift_lower_pct": "Intentionally empty lower bound because no uplift interval is supported",
        "uplift_upper_pct": "Intentionally empty upper bound because no uplift interval is supported",
        "composite_opportunity_need_score": "Intentionally empty because opportunity and strategic-need dimensions are kept separate",
        "causal_interpretation_approved": "Whether a causal interpretation is authorised; always false in Path C",
        "model_used": "Name of the descriptive segmentation and analogue architecture",
        "confidence": "Exploratory support label, not statistical confidence or causal certainty",
        "interpretation": "Plain-language restriction on how the row may be used",
        "aggregation_rule": "Within-cluster structural-feature aggregation rule used in the robustness scenario",
        "aggregation_segment_ids": "Distinct structural segment labels assigned across the minimum, median and maximum aggregation rules",
        "aggregation_segment_stable": "Whether the candidate's segment label is unchanged across all three aggregation rules",
        "aggregation_current_magic_top1_stable": "Whether the closest current-Magic cluster is unchanged across all three aggregation rules",
        "aggregation_reviewed_treated_top1_stable": "Whether the closest reviewed-treated reference is unchanged across all three aggregation rules",
        "aggregation_reviewed_treated_ood_stable": "Whether the reviewed-treated OOD category is unchanged across all three aggregation rules",
        "aggregation_signal_min_pct": "Minimum descriptive analogue-change signal across the three aggregation rules",
        "aggregation_signal_max_pct": "Maximum descriptive analogue-change signal across the three aggregation rules",
        "aggregation_signal_range_pct_points": "Range of the descriptive analogue-change signal across the three aggregation rules",
        "aggregation_sensitivity_status": "Combined flag for stability of segment, top-one analogues and reviewed-treated OOD category",
        "municipality_bfs_id": "Official BFS municipality identifier",
        "municipality_name_statpop": "Official STATPOP municipality label",
        "population_reference_year": "Reference year of the permanent-resident population count",
        "resident_population": "Official permanent resident population at 31 December",
        "complete_hotel_reference_year": "Whether all twelve HESTA months are observed for nights and hotel supply",
        "hotel_overnights_annual": "Annual hotel overnight stays summed only from twelve observed monthly values",
        "overnights_per_resident": "Annual hotel overnight stays divided by permanent resident population",
        "hotel_beds_per_1000_residents": "Mean monthly available hotel beds per 1,000 permanent residents",
        "point_container_municipality_count": "Number of unique municipalities containing listing points assigned to the cluster",
        "point_container_population": "Sum of permanent residents across unique listing-point container municipalities",
        "point_container_overnights_per_resident": "Complete-year hotel nights per resident across the unique listing-point container set",
        "point_container_hotel_beds_per_1000_residents": "Mean hotel beds per 1,000 residents across the unique listing-point container set",
        "tourism_context_status": "Availability status for point-container population and complete-year hotel context",
        "tourism_exposure_interpretation": "Explicit restriction that point-container context is not an approved destination catchment",
        "tourism_dependence_feature_approved": "Whether the context is approved as a destination tourism-dependence feature; always false",
        "boundary_bfs_id_2026": "Official BFS identifier of the municipality polygon at 1 January 2026",
        "boundary_name_2026": "Official municipality name in swissBOUNDARIES3D at 1 January 2026",
        "resident_population_2025_on_2026_boundary": "STATPOP 2025 permanent residents aggregated to the 2026 municipality boundary identifier",
        "population_constituent_count_2025": "Number of STATPOP 2025 municipality rows aggregated to the current municipality",
        "population_constituent_bfs_ids_2025": "Pipe-separated STATPOP 2025 BFS identifiers contributing to the current municipality",
        "population_constituent_names_2025": "Pipe-separated STATPOP 2025 municipality names contributing to the current municipality",
        "boundary_bridge_status": "Whether and how a STATPOP 2025 identifier was aligned through an official 2026 municipality mutation",
        "boundary_bridge_source_ids": "Pipe-separated official OFS municipality-mutation source identifiers used for the alignment",
        "municipality_representative_x_2056": "Easting of an interior representative point for the current municipality polygon",
        "municipality_representative_y_2056": "Northing of an interior representative point for the current municipality polygon",
        "municipality_representative_longitude": "Longitude of the current municipality polygon's interior representative point",
        "municipality_representative_latitude": "Latitude of the current municipality polygon's interior representative point",
        "municipality_location_method": "Method used to represent each municipality in straight-line calculations",
        "cluster_location_longitude": "Median longitude across supplied resort listings assigned to the lift cluster",
        "cluster_location_latitude": "Median latitude across supplied resort listings assigned to the lift cluster",
        "cluster_inside_swiss_country_boundary_2026": "Whether the median cluster coordinate lies inside or on the official Swiss country polygon",
        "distance_to_swiss_country_boundary_km": "EPSG:2056 straight-line distance from the median cluster coordinate to the official Swiss country boundary",
        "accessibility_context_status": "Availability status of the qualified Swiss straight-line population context",
        "accessibility_interpretation": "Explicit restriction that the context is neither travel time nor a destination catchment",
        "accessibility_feature_approved": "Whether the context is approved as a generic accessibility feature; always false",
        "population_boundary_alignment": "Reference-year relationship between STATPOP population and the current boundary snapshot",
        "grid_cell_id": "Official INSPIRE identifier of the Eurostat one-kilometre census grid cell",
        "total_population_2021": "Official 2021 census total population reported for the grid cell",
        "populated_flag": "Official Eurostat flag indicating whether the grid cell is populated",
        "reporting_country_codes": "Hyphen-separated official country codes that reported data for the grid cell",
        "cell_lower_left_x_3035": "Easting of the grid cell lower-left corner in EPSG:3035",
        "cell_lower_left_y_3035": "Northing of the grid cell lower-left corner in EPSG:3035",
        "cell_centroid_x_3035": "Easting of the one-kilometre grid cell centroid in EPSG:3035",
        "cell_centroid_y_3035": "Northing of the one-kilometre grid cell centroid in EPSG:3035",
        "minimum_distance_to_path_c_cluster_km": "Smallest straight-line centroid distance from the grid cell to any linked Path C cluster",
        "country_scope_category": "Whether the grid cell is Switzerland-only, foreign-only, or reported by Switzerland and at least one foreign country",
        "total_population_observation_status": "Whether total grid-cell population is observed or unavailable under an official Eurostat code",
        "grid_crs": "Projected coordinate reference system of the Eurostat census grid",
        "grid_resolution_m": "Nominal side length of the Eurostat census grid cell",
        "cluster_location_x_3035": "Easting of the median cluster coordinate projected to EPSG:3035",
        "cluster_location_y_3035": "Northing of the median cluster coordinate projected to EPSG:3035",
        "cross_border_population_context_status": "Availability status of total population across the retained cross-border grid cells",
        "population_grid_release_date": "Release date of Eurostat Census Grid 2021 version 3",
        "population_grid_crs": "Projected coordinate reference system used for cross-border population distances",
        "population_grid_resolution_m": "Nominal side length of the population grid cells",
        "population_grid_cell_location_method": "Rule used to represent each one-kilometre population cell in radius calculations",
        "grid_cell_centroid_maximum_location_error_km": "Maximum distance from a one-kilometre square centroid to any point in that square",
        "unallocated_population_records_excluded": "Whether country-level population records without a spatial grid identifier remain excluded from radius totals",
        "cross_border_population_interpretation": "Explicit restriction that the harmonised grid context is not travel time or a destination catchment",
        "cross_border_population_feature_approved": "Whether cross-border population context is approved as an accessibility or causal feature; always false",
        "cross_border_population_source_ids": "Official Eurostat data and documentation source identifiers supporting the context",
        "npvm_traffic_zone_id": "Official NPVM traffic-zone identifier assigned to the supplied resort listing point",
        "npvm_zone_assignment_status": "Whether the point is inside a zone, uses the nearest zone intersecting its current municipality, or remains outside scope",
        "distance_to_nearest_npvm_zone_km": "Shortest EPSG:2056 distance from the listing point to any NPVM traffic-zone polygon",
        "npvm_zone_assignment_distance_km": "Distance from the listing point to its assigned zone; zero for exact containment",
        "point_municipality_bfs_id_2026": "Current municipality BFS identifier used only to constrain a nearest-zone proxy",
        "travel_time_values_complete": "Whether all four official travel-time values are available for the assigned listing point",
        "npvm_model_reference_date": "Reference date of the official NPVM travel-time asset",
        "npvm_distance_crs": "Projected coordinate reference system used for zone assignment distances",
        "transport_point_assignment_method": "Versioned exact-or-within-current-municipality zone-assignment rule",
        "transport_cluster_aggregation_method": "Versioned listing-to-cluster aggregation rule for transport context",
        "transport_accessibility_interpretation": "Explicit restriction that NPVM values are modelled zonal context, not live routing or a catchment",
        "transport_accessibility_feature_approved": "Whether transport context is approved as a generic accessibility feature; always false",
        "transport_source_ids": "Pipe-separated official source identifiers supporting the transport context",
        "cluster_transport_context_status": "Exact, proxy-complete, partial, or unavailable cluster coverage status",
        "cluster_listing_transport_assignment_share": "Share of supplied cluster listing points with usable NPVM travel times",
        "cluster_listing_exact_transport_assignment_share": "Share of supplied cluster listing points falling exactly inside an NPVM zone",
        "cluster_maximum_zone_proxy_distance_km": "Largest within-current-municipality NPVM zone-proxy distance among cluster listing points",
        "cluster_npvm_traffic_zone_ids": "Pipe-separated NPVM zone identifiers used in the cluster summary",
        "unassigned_resort_ids": "Pipe-separated cluster listing IDs left without an NPVM assignment",
    }
    transport_measures = {
        "road_major_center_travel_time": "road travel time to the fastest accessible one of six major centres",
        "public_transport_major_center_travel_time": "public-transport travel time to the fastest accessible one of six major centres",
        "road_agglomeration_travel_time": "road travel time to the fastest accessible agglomeration or core municipality",
        "public_transport_agglomeration_travel_time": "public-transport travel time to the fastest accessible agglomeration or core municipality",
    }
    for stem, description in transport_measures.items():
        path_c_glossary[f"{stem}_minutes"] = (
            f"Official modelled {description} for the assigned listing-point traffic zone"
        )
        for statistic in ["minimum", "median", "maximum", "range"]:
            path_c_glossary[f"{stem}_{statistic}_minutes"] = (
                f"Cluster-level {statistic} of {description} across usable supplied listing-point assignments"
            )
        path_c_glossary[f"{stem}_exact_only_median_minutes"] = (
            f"Sensitivity median of {description} using only listing points exactly contained in an NPVM zone"
        )
    for prefix, description in {
        "road_major_center": "road major-centre",
        "public_transport_major_center": "public-transport major-centre",
        "road_agglomeration": "road agglomeration/core-municipality",
        "public_transport_agglomeration": "public-transport agglomeration/core-municipality",
    }.items():
        path_c_glossary[f"{prefix}_target_zone_id"] = (
            f"NPVM zone identifier of the official {description} target"
        )
        path_c_glossary[f"{prefix}_target_name"] = (
            f"Published name of the official {description} target"
        )
        path_c_glossary[f"{prefix}_target_published_size_class"] = (
            f"Published ARE size class of the {description} target"
        )
        path_c_glossary[f"{prefix}_target_six_major_centres_flag"] = (
            f"Whether the {description} target is one of the six major centres"
        )
        path_c_glossary[f"{prefix}_target_names"] = (
            f"Pipe-separated official {description} target names across cluster listing points"
        )
    path_c_glossary.update({
        "point_x_2056": "Easting of the supplied resort listing coordinate projected to EPSG:2056",
        "point_y_2056": "Northing of the supplied resort listing coordinate projected to EPSG:2056",
        "selection_status": "Whether the supplied listing point falls inside one unique current Swiss municipality polygon",
        "public_transport_stop_context_status": "Whether the listing point is inside the complete official Swiss stop-data scope and receives nearest-stop values",
        "public_transport_stop_values_complete": "Whether both nearest passenger-stop and nearest train-station distances are populated",
        "public_transport_stop_source_state_date": "Data-state date embedded in the official OFT/BAV archive release note and point records",
        "public_transport_stop_stac_item_datetime": "Datetime published in the official geo.admin.ch STAC item, retained separately from the archive data-state date",
        "public_transport_stop_distance_crs": "Projected coordinate reference system used for straight-line nearest-stop distances",
        "public_transport_stop_point_eligibility": "Versioned rule restricting calculations to supplied points inside a unique current Swiss municipality",
        "public_transport_stop_scope": "Official operating-point types retained as actual passenger stops across all published modes",
        "train_station_scope": "Exact official mode-code rule used to identify train-capable passenger stops",
        "public_transport_stop_distance_method": "Versioned point-to-point straight-line distance method",
        "public_transport_stop_cluster_aggregation": "Versioned listing-to-cluster aggregation rule for nearest-stop distances",
        "public_transport_stop_proximity_interpretation": "Explicit restriction that stop-point distance is not a route, service-quality measure or validated arrival-node metric",
        "public_transport_stop_proximity_feature_approved": "Whether current straight-line stop proximity is approved as a generic accessibility feature; always false",
        "public_transport_stop_source_ids": "Pipe-separated official OFT/BAV source identifiers supporting the stop-proximity context",
        "cluster_listings_with_public_transport_stop_context": "Number of supplied cluster listing points eligible for official Swiss nearest-stop calculations",
        "cluster_listing_public_transport_stop_context_share": "Share of supplied cluster listing points eligible for official Swiss nearest-stop calculations",
        "cluster_public_transport_stop_context_status": "Complete, partial or unavailable cluster coverage under the Swiss point-eligibility rule",
        "cluster_unassigned_public_transport_stop_resort_ids": "Pipe-separated listing identifiers left without stop context because they are outside complete Swiss coverage",
        "node_role": "Whether the selected node is a hotel-municipality origin or a ski-destination component arrival proxy",
        "selection_method": "Deterministic rule used to select the public-transport node",
        "selection_rule": "Versioned public-transport node-selection rule",
        "selected_stop_reference_departures": "Combined boardable departures at the normalized stop on the selected reference days",
        "direction": "Outbound municipality-to-destination or return destination-to-municipality routing direction",
        "reference_day_type": "Winter weekday or winter Saturday reference-day label",
        "reference_date": "Exact GTFS service date used for the scheduled request",
        "requested_departure_time": "Requested clock time at which the fastest subsequent itinerary is sought",
        "journey_feasible": "Whether a scheduled itinerary meets the declared leg and generalized-time limits",
        "journey_exclusion_reason": "Explicit reason a sampled request has no retained feasible itinerary",
        "scheduled_first_boarding_time": "Scheduled first vehicle departure time for the retained itinerary",
        "scheduled_arrival_time": "Scheduled arrival time at the retained destination node",
        "initial_wait_minutes": "Minutes from requested departure time to first scheduled vehicle boarding",
        "scheduled_journey_minutes": "Minutes from first vehicle boarding to arrival",
        "generalized_elapsed_minutes": "Minutes from requested departure time to arrival, including initial waiting",
        "vehicle_legs": "Number of boarded public-transport vehicle legs in the retained itinerary",
        "transfers": "Number of vehicle changes, calculated as vehicle legs minus one",
        "transport_modes": "Pipe-separated scheduled transport modes used by the retained itinerary",
        "outbound_sample_coverage_share": "Share of declared outbound timetable samples with a feasible itinerary",
        "return_sample_coverage_share": "Share of declared return timetable samples with a feasible itinerary",
        "mean_round_trip_generalized_minutes": "Sum of mean outbound and return generalized scheduled times where both are observed",
        "historical_stability_status": "Whether historical timetable stability has actually been verified",
        "public_transport_journey_feature_approved": "Whether the journey context is approved as a causal accessibility feature; always false",
        "first_exposure_winter_timetable_year": "Timetable year covering the destination's first documented Magic Pass exposure winter",
        "snapshot_build": "Official GTFS archive snapshot build selected for the historical audit",
        "archive_url": "Official archive URL for the selected timetable snapshot",
        "archive_index_availability_status": "Status of archive-index URL verification",
        "historical_feed_downloaded": "Whether the selected historical feed has been checksum-cached by the project",
        "historical_destination_stop_service_compared": "Whether the component stop and scheduled service have actually been compared in the anchor-year feed",
        "historical_line_stability_status": "Explicit historical line-stability conclusion status",
    })
    for prefix, description in {
        "public_transport_stop": "official VP/VPG passenger stop across all published modes",
        "train_station": "official VP/VPG passenger stop whose transport-mode code contains elementary code B (train)",
    }.items():
        for suffix, detail in {
            "id": "official stop number",
            "name": "published stop name",
            "mode_code": "official transport-mode code",
            "mode": "published transport-mode designation",
            "type_code": "official operating-point type code",
            "type": "published operating-point type designation",
            "operator": "published responsible transport-company abbreviation",
            "municipality_bfs_id": "published stop-municipality BFS identifier",
            "municipality_name": "published stop-municipality name",
            "x_2056": "official stop easting in EPSG:2056",
            "y_2056": "official stop northing in EPSG:2056",
        }.items():
            path_c_glossary[f"nearest_{prefix}_{suffix}"] = (
                f"{detail.capitalize()} for the nearest {description}"
            )
        path_c_glossary[f"distance_to_nearest_{prefix}_km"] = (
            f"EPSG:2056 straight-line distance from the supplied listing coordinate to the nearest {description}"
        )
        for statistic in ["minimum", "median", "maximum", "range"]:
            path_c_glossary[f"cluster_distance_to_nearest_{prefix}_{statistic}_km"] = (
                f"Cluster-level {statistic} of listing-point straight-line distance to the nearest {description}"
            )
        for suffix, detail in {
            "ids": "official stop numbers",
            "names": "published stop names",
            "mode_codes": "official transport-mode codes",
            "modes": "published transport-mode designations",
        }.items():
            path_c_glossary[f"cluster_listing_nearest_{prefix}_{suffix}"] = (
                f"Pipe-separated {detail} selected as nearest across eligible cluster listing points"
            )
    for prefix, description in {
        "directory": "other supplied-directory lift cluster",
        "resolved_current_magic": "other cluster with a resolved current Magic Pass link",
        "reviewed_competing_pass": "other cluster with a reviewed competing-pass link",
        "reviewed_pass_network": "other cluster in the union of resolved current Magic and reviewed competing-pass links",
    }.items():
        path_c_glossary[f"nearest_other_{prefix}_cluster_km"] = (
            f"Great-circle distance to the nearest {description}, excluding the focal cluster"
        )
        path_c_glossary[f"nearest_other_{prefix}_cluster_id"] = (
            f"Stable cluster identifier of the nearest {description}"
        )
        path_c_glossary[f"nearest_other_{prefix}_cluster_name"] = (
            f"Display name of the nearest {description}"
        )
    for radius in [25, 50]:
        path_c_glossary[f"other_directory_clusters_within_{radius}km"] = (
            f"Number of other directory-linked lift clusters within {radius} great-circle kilometres"
        )
        path_c_glossary[f"other_directory_listings_within_{radius}km"] = (
            f"Number of supplied listings assigned to other clusters within {radius} great-circle kilometres"
        )
        path_c_glossary[
            f"other_directory_clusters_with_observed_ski_area_within_{radius}km"
        ] = f"Number of other clusters within {radius} kilometres whose cluster-median published ski-area value is observed"
        path_c_glossary[
            f"other_directory_clusters_missing_ski_area_within_{radius}km"
        ] = f"Number of other clusters within {radius} kilometres whose cluster-median published ski-area value is missing"
        path_c_glossary[
            f"other_directory_cluster_median_ski_area_km_sum_within_{radius}km"
        ] = f"Sum of observed cluster-median published ski-area kilometres across other clusters within {radius} kilometres"
        path_c_glossary[f"other_resolved_current_magic_clusters_within_{radius}km"] = (
            f"Number of other clusters within {radius} kilometres with a resolved current Magic Pass link"
        )
        path_c_glossary[
            f"other_reviewed_competing_pass_clusters_within_{radius}km"
        ] = f"Number of other clusters within {radius} kilometres with a reviewed competing-pass link"
        path_c_glossary[
            f"other_reviewed_competing_limited_partner_clusters_within_{radius}km"
        ] = f"Number of other clusters within {radius} kilometres with an AlpsPass limited three-day partner link"
        path_c_glossary[
            f"other_reviewed_competing_core_or_included_clusters_within_{radius}km"
        ] = f"Number of other clusters within {radius} kilometres with a core or included competing-pass-region link"
        path_c_glossary[f"other_reviewed_pass_network_clusters_within_{radius}km"] = (
            f"Number of other clusters within {radius} kilometres in the union of resolved current Magic and reviewed competing-pass links"
        )
        for prefix, description in {
            "resolved_current_magic": "resolved current Magic",
            "reviewed_competing_pass": "reviewed competing-pass-linked",
            "reviewed_pass_network": "reviewed pass-network union",
        }.items():
            path_c_glossary[
                f"{prefix}_share_of_other_directory_clusters_within_{radius}km"
            ] = f"Share of other directory clusters within {radius} kilometres belonging to the {description} set; missing when there is no neighbour"
        for rule, description in {
            "minimum_listing_pair": "minimum cross-listing-point pair",
            "median_listing_pair": "median cross-listing-point pair",
            "representative_median_coordinate": "coordinate-wise median representative",
            "maximum_listing_pair": "maximum cross-listing-point pair",
        }.items():
            path_c_glossary[
                f"other_directory_clusters_within_{radius}km_by_{rule}_distance"
            ] = f"Number of other directory clusters within {radius} kilometres under the {description} distance rule"
            path_c_glossary[
                f"other_reviewed_pass_network_clusters_within_{radius}km_by_{rule}_distance"
            ] = f"Number of other reviewed pass-network clusters within {radius} kilometres under the {description} distance rule"
        path_c_glossary[
            f"directory_cluster_count_distance_rule_span_within_{radius}km"
        ] = f"Maximum minus minimum directory-neighbour count across the four distance rules at {radius} kilometres"
        path_c_glossary[
            f"reviewed_pass_network_count_distance_rule_span_within_{radius}km"
        ] = f"Maximum minus minimum reviewed pass-network count across the four distance rules at {radius} kilometres"
        path_c_glossary[
            f"directory_cluster_count_stable_across_distance_rules_within_{radius}km"
        ] = f"Whether all four distance rules give the same directory-neighbour count at {radius} kilometres"
        path_c_glossary[
            f"reviewed_pass_network_count_stable_across_distance_rules_within_{radius}km"
        ] = f"Whether all four distance rules give the same reviewed pass-network count at {radius} kilometres"
    for threshold in [20_000, 50_000, 100_000]:
        prefix = f"nearest_municipality_population_ge_{threshold}"
        path_c_glossary[f"{prefix}_bfs_id_2026"] = (
            f"BFS identifier of the nearest representative-point municipality with at least {threshold:,} STATPOP 2025 residents"
        )
        path_c_glossary[f"{prefix}_name"] = (
            f"Name of the nearest representative-point municipality with at least {threshold:,} STATPOP 2025 residents"
        )
        path_c_glossary[f"distance_to_{prefix}_km"] = (
            f"EPSG:2056 straight-line distance to the nearest representative-point municipality with at least {threshold:,} residents"
        )
    for radius in [30, 60, 90, 120]:
        path_c_glossary[f"resident_population_within_{radius}km_straight_line"] = (
            f"STATPOP 2025 residents assigned to municipality representative points within {radius} straight-line kilometres"
        )
        path_c_glossary[
            f"swiss_only_population_within_{radius}km_cross_border_truncation_risk"
        ] = (
            f"Whether the {radius}-kilometre circle reaches beyond the official Swiss country polygon, so Swiss-only population is geographically truncated"
        )
        path_c_glossary[f"eurostat_population_2021_within_{radius}km_cell_centroid"] = (
            f"Observed Eurostat 2021 total population in grid cells whose centroids fall within {radius} straight-line kilometres"
        )
        for scope, description in {
            "switzerland_only": "reported only by Switzerland",
            "foreign_only": "reported only by countries other than Switzerland",
            "ch_foreign_mixed": "reported by Switzerland and at least one foreign country",
        }.items():
            path_c_glossary[
                f"eurostat_{scope}_population_2021_within_{radius}km_cell_centroid"
            ] = (
                f"Observed Eurostat 2021 population in cells {description} whose centroids fall within {radius} straight-line kilometres"
            )
        path_c_glossary[
            f"eurostat_foreign_only_share_of_observed_population_within_{radius}km"
        ] = f"Foreign-only cell population divided by all observed cell population within {radius} straight-line kilometres"
        path_c_glossary[f"eurostat_population_grid_cells_within_{radius}km"] = (
            f"Number of Eurostat grid-cell centroids within {radius} straight-line kilometres"
        )
        path_c_glossary[
            f"eurostat_total_population_unavailable_cells_within_{radius}km"
        ] = f"Number of grid cells within {radius} kilometres whose official total population is unavailable"
        path_c_glossary[
            f"eurostat_populated_cells_with_unavailable_total_within_{radius}km"
        ] = f"Number of cells marked populated within {radius} kilometres whose official total population is unavailable"
        path_c_glossary[
            f"eurostat_positive_population_country_codes_within_{radius}km"
        ] = f"Country codes reported by positive-population cells within {radius} straight-line kilometres"

    def path_c_unit(variable: str) -> str:
        if "_share_of_" in variable:
            return "share (0-1)"
        if "clusters_within_" in variable or "listings_within_" in variable:
            return "count"
        if "count_distance_rule_span" in variable:
            return "count"
        if "ski_area_km_sum" in variable:
            return "published ski-area kilometres"
        if "foreign_only_share_of_observed_population" in variable:
            return "share (0-1)"
        if variable.startswith("eurostat_") and "population_2021" in variable:
            return "persons"
        if variable.startswith("eurostat_") and "cells_within_" in variable:
            return "count"
        if variable.startswith("eurostat_") and "unavailable" in variable:
            return "count"
        if variable.endswith("_x_3035") or variable.endswith("_y_3035"):
            return "metres (EPSG:3035)"
        if variable.endswith("_minutes"):
            return "minutes"
        if variable.endswith("_share"):
            return "share (0-1)"
        if variable.endswith("_samples") or variable in {"vehicle_legs", "transfers"}:
            return "count"
        if variable.endswith("_crs"):
            return "coordinate reference system"
        if variable.startswith("cluster_listings_"):
            return "count"
        if variable.endswith("_pct"):
            return "percent"
        if variable.endswith("_percentile") or "comparability_score" in variable:
            return "0-100 empirical score"
        if variable.endswith("_km"):
            return "kilometres"
        if variable.endswith("_mm") or "_mm_" in variable:
            return "millimetres"
        if variable.endswith("_c") or "_c_" in variable:
            return "degrees Celsius"
        if "correlation" in variable:
            return "correlation coefficient"
        if variable.endswith("distance_to_component_m"):
            return "metres"
        if "distance" in variable:
            return "standardised Euclidean distance"
        if variable.endswith("_count") or "_count_" in variable or variable.endswith("_clusters"):
            return "count"
        if variable.endswith("_m") or "altitude" in variable:
            return "metres"
        if "per_1000_residents" in variable:
            return "hotel beds per 1,000 residents"
        if "overnights_per_resident" in variable:
            return "hotel nights per resident"
        if variable == "resident_population" or variable.endswith("_population") or variable.startswith("resident_population_"):
            return "persons"
        if variable.endswith("_x_2056") or variable.endswith("_y_2056"):
            return "metres (EPSG:2056)"
        if variable.endswith("_longitude") or variable.endswith("_latitude"):
            return "decimal degrees"
        return "category/value"

    path_c_geographic_level = {
        "municipality_tourism_context_2025": "municipality",
        "municipality_population_geometry_2026": "current Swiss municipality",
        "eurostat_population_grid_2021_swiss_region": "one-kilometre European census grid cell near a linked cluster",
        "path_c_cluster_cross_border_population_context": "linked lift cluster",
        "cross_border_population_candidate_summary": "apparent Path C candidate lift cluster",
        "resort_transport_accessibility_context": "supplied resort listing point / NPVM traffic zone",
        "transport_zone_proxy_audit": "supplied resort listing point / NPVM traffic zone / current municipality",
        "resort_public_transport_stop_context": "supplied resort listing point / official public-transport stop point",
        "resort_national_road_proximity_context": "supplied resort listing point / official Swiss national-road axis",
        "path_c_cluster_national_road_proximity_context": "linked lift cluster",
        "national_road_proximity_candidate_summary": "apparent Path C candidate lift cluster",
        "resort_competing_pass_context": "supplied resort listing / official competing-pass area",
        "path_c_cluster_competing_pass_context": "linked lift cluster",
        "competing_pass_candidate_summary": "apparent Path C candidate lift cluster",
        "path_c_cluster_network_context": "linked lift cluster",
        "path_c_cluster_network_pairs": "ordered pair of distinct linked lift clusters",
        "network_context_candidate_summary": "apparent Path C candidate lift cluster",
        "path_c_cluster_geographic_sensitivity": "preserved linked lift cluster and its supplied listing points",
        "path_c_cluster_distance_rule_pairs": "ordered pair of distinct preserved linked lift clusters",
        "cluster_geography_candidate_summary": "apparent Path C candidate lift cluster",
        "meteoswiss_alternative_station_month": "SwissMetNet point station",
        "weather_station_alternative_sensitivity": "reviewed resort component and primary/alternative station pair",
        "destination_weather_alternative_sensitivity": "reviewed destination by month",
        "weather_destination_alternative_summary": "reviewed destination",
        "meteoswiss_gridded_component_month": "reviewed resort component / 1 km MeteoSwiss grid cell",
        "weather_gridded_component_comparison": "reviewed resort component, selected station and 1 km grid cell",
        "destination_weather_gridded_sensitivity": "reviewed destination by month",
        "weather_gridded_destination_summary": "reviewed destination",
        "public_transport_journey_nodes": "hotel municipality or reviewed destination component",
        "treatment_municipality_public_transport_journey_samples": "reviewed destination by hotel municipality and scheduled request",
        "treatment_municipality_public_transport_journey_context": "reviewed destination by hotel municipality",
        "public_transport_arrival_node_review": "reviewed destination component arrival node",
        "public_transport_historical_audit_plan": "reviewed destination component arrival node",
        "treatment_municipality_distance_transport_comparison": "reviewed destination by hotel municipality",
        "distance_transport_correlations_by_destination": "reviewed destination",
        "distance_transport_band_summary": "reviewed destination by municipality-distance band",
        "path_c_reviewed_treated_reference": "reviewed treated destination",
    }
    path_c_temporal_level = {
        "municipality_tourism_context_2025": "2025 annual municipality context",
        "path_c_cluster_tourism_context": "2025 annual point-container context",
        "municipality_population_geometry_2026": "2025 population aligned to 2026-01-01 boundaries",
        "path_c_cluster_accessibility_context": "2025 population aligned to 2026-01-01 boundaries; undated cluster location",
        "eurostat_population_grid_2021_swiss_region": "2021 census population; version 3 released 2026-05-30",
        "path_c_cluster_cross_border_population_context": "2021 census population; current/undated cluster location",
        "cross_border_population_candidate_summary": "2021 census population; current/undated candidate cluster location",
        "resort_transport_accessibility_context": "NPVM model reference date 2025-06-30; current supplied listing coordinate",
        "path_c_cluster_transport_accessibility_context": "NPVM model reference date 2025-06-30; current supplied listing coordinates",
        "transport_zone_proxy_audit": "NPVM model reference date 2025-06-30; current 2026 municipality geometry audit",
        "resort_public_transport_stop_context": "OFT/BAV source state 2026-09-20; current supplied listing coordinate",
        "path_c_cluster_public_transport_stop_context": "OFT/BAV source state 2026-09-20; current supplied listing coordinates",
        "resort_national_road_proximity_context": "FEDRO/ASTRA reference 2026-08-01; current supplied listing coordinate",
        "path_c_cluster_national_road_proximity_context": "FEDRO/ASTRA reference 2026-08-01; current supplied listing coordinates",
        "national_road_proximity_candidate_summary": "FEDRO/ASTRA reference 2026-08-01; current candidate listing coordinates",
        "resort_competing_pass_context": "AlpsPass and Schneepass 2026/2027; Meilenweiss current snapshot retrieved 2026-09-23",
        "path_c_cluster_competing_pass_context": "AlpsPass and Schneepass 2026/2027; Meilenweiss current snapshot retrieved 2026-09-23",
        "competing_pass_candidate_summary": "AlpsPass and Schneepass 2026/2027; Meilenweiss current snapshot retrieved 2026-09-23",
        "path_c_cluster_network_context": "current/undated supplied directory plus current reviewed pass-network snapshots",
        "path_c_cluster_network_pairs": "current/undated supplied directory plus current reviewed pass-network snapshots",
        "network_context_candidate_summary": "current/undated supplied directory plus current reviewed pass-network snapshots",
        "path_c_cluster_geographic_sensitivity": "current/undated supplied listing coordinates",
        "path_c_cluster_distance_rule_pairs": "current/undated supplied listing coordinates plus current reviewed pass-network links",
        "cluster_geography_candidate_summary": "current/undated supplied listing coordinates plus current reviewed pass-network links",
        "meteoswiss_alternative_station_month": "monthly 2013-01 through 2026-03",
        "weather_station_alternative_sensitivity": "common complete months from 2013-01 through 2026-03",
        "destination_weather_alternative_sensitivity": "monthly 2013-01 through 2026-03",
        "weather_destination_alternative_summary": "common complete months from 2013-01 through 2026-03",
        "meteoswiss_gridded_component_month": "monthly 2013-01 through 2026-03",
        "weather_gridded_component_comparison": "common complete months from 2013-01 through 2026-03",
        "destination_weather_gridded_sensitivity": "monthly 2013-01 through 2026-03",
        "weather_gridded_destination_summary": "common complete months from 2013-01 through 2026-03",
        "public_transport_journey_nodes": "winter-2026 GTFS node-selection reference",
        "treatment_municipality_public_transport_journey_samples": "2026-02-04 and 2026-02-07 scheduled requests",
        "treatment_municipality_public_transport_journey_context": "winter-2026 weekday/Saturday scheduled summary",
        "public_transport_arrival_node_review": "current official node plus 2026-02-04 and 2026-02-07 availability",
        "public_transport_historical_audit_plan": "first-exposure winters 2018-2026; service comparison pending",
        "treatment_municipality_distance_transport_comparison": "2026 boundary distance plus 2026-02-04 and 2026-02-07 schedules",
        "distance_transport_correlations_by_destination": "2026 boundary distance plus winter-2026 schedule",
        "distance_transport_band_summary": "2026 boundary distance plus winter-2026 schedule",
    }

    for table, path in path_c_paths.items():
        paths[table] = path
        frame = pd.read_csv(path)
        for variable in frame.columns:
            description = path_c_glossary.get(
                variable,
                "Path C output field: " + variable.replace("_", " "),
            )
            accessibility_table = table in {
                "municipality_population_geometry_2026",
                "path_c_cluster_accessibility_context",
            }
            cross_border_population_table = table in {
                "eurostat_population_grid_2021_swiss_region",
                "path_c_cluster_cross_border_population_context",
                "cross_border_population_candidate_summary",
            }
            transport_table = table in {
                "resort_transport_accessibility_context",
                "path_c_cluster_transport_accessibility_context",
                "transport_zone_proxy_audit",
            }
            stop_table = table in {
                "resort_public_transport_stop_context",
                "path_c_cluster_public_transport_stop_context",
            }
            road_table = table in {
                "resort_national_road_proximity_context",
                "path_c_cluster_national_road_proximity_context",
                "national_road_proximity_candidate_summary",
            }
            competing_table = table in {
                "resort_competing_pass_context",
                "path_c_cluster_competing_pass_context",
                "competing_pass_candidate_summary",
            }
            network_table = table in {
                "path_c_cluster_network_context",
                "path_c_cluster_network_pairs",
                "network_context_candidate_summary",
            }
            geography_sensitivity_table = table in {
                "path_c_cluster_geographic_sensitivity",
                "path_c_cluster_distance_rule_pairs",
                "cluster_geography_candidate_summary",
            }
            weather_sensitivity_table = table in {
                "meteoswiss_alternative_station_month",
                "weather_station_alternative_sensitivity",
                "destination_weather_alternative_sensitivity",
                "weather_destination_alternative_summary",
            }
            weather_gridded_table = table in {
                "meteoswiss_gridded_component_month",
                "weather_gridded_component_comparison",
                "destination_weather_gridded_sensitivity",
                "weather_gridded_destination_summary",
            }
            journey_table = table in {
                "public_transport_journey_nodes",
                "treatment_municipality_public_transport_journey_samples",
                "treatment_municipality_public_transport_journey_context",
                "public_transport_arrival_node_review",
                "public_transport_historical_audit_plan",
                "treatment_municipality_distance_transport_comparison",
                "distance_transport_correlations_by_destination",
                "distance_transport_band_summary",
            }
            journey_variable = journey_table
            competing_variable = competing_table or (
                table == "magic_pass_decision_support"
                and (
                    variable.startswith("competing_pass_")
                    or variable.startswith("cluster_competing_pass_")
                    or variable.startswith("cluster_listings_linked_to_reviewed_competing_pass")
                    or variable.startswith("cluster_has_reviewed_competing_pass")
                    or variable.startswith("cluster_limited_partner_benefit_")
                    or variable.startswith("cluster_core_or_included_region_")
                    or variable.startswith("reviewed_competing_pass_")
                )
            )
            geography_sensitivity_variable = geography_sensitivity_table or (
                table == "magic_pass_decision_support"
                and (
                    variable.startswith("cluster_listing_point_")
                    or variable.startswith("cluster_unique_coordinate_")
                    or variable.startswith("within_cluster_")
                    or variable.startswith("maximum_listing_distance_from_representative_")
                    or variable.startswith("cluster_listing_geographic_spread_")
                    or variable.startswith("directory_cluster_count_distance_rule_")
                    or variable.startswith("reviewed_pass_network_count_distance_rule_")
                    or variable.startswith(
                        "directory_cluster_count_stable_across_distance_rules_"
                    )
                    or variable.startswith(
                        "reviewed_pass_network_count_stable_across_distance_rules_"
                    )
                    or "_by_minimum_listing_pair_distance" in variable
                    or "_by_median_listing_pair_distance" in variable
                    or "_by_representative_median_coordinate_distance" in variable
                    or "_by_maximum_listing_pair_distance" in variable
                    or variable
                    in {
                        "cluster_geographic_coherence_verified",
                        "network_distance_sensitivity_feature_approved",
                        "cluster_geography_sensitivity_interpretation",
                        "cluster_geography_sensitivity_source_ids",
                    }
                )
            )
            network_variable = not geography_sensitivity_variable and (network_table or (
                table == "magic_pass_decision_support"
                and (
                    variable.startswith("nearest_other_")
                    or variable.startswith("other_directory_")
                    or variable.startswith("other_resolved_current_magic_")
                    or variable.startswith("other_reviewed_")
                    or variable.startswith("resolved_current_magic_share_")
                    or variable.startswith("reviewed_competing_pass_share_")
                    or variable.startswith("reviewed_pass_network_share_")
                    or variable
                    in {
                        "network_context_latitude",
                        "network_context_longitude",
                        "network_distance_method",
                        "network_focal_cluster_excluded_from_all_neighbourhood_counts",
                        "historical_network_context_verified",
                        "network_context_feature_approved",
                        "network_context_interpretation",
                        "network_context_source_ids",
                    }
                )
            ))
            cross_border_population_variable = cross_border_population_table or (
                table == "magic_pass_decision_support"
                and (
                    variable.startswith("eurostat_")
                    or variable.startswith("cross_border_population_")
                    or variable.startswith("population_grid_")
                    or variable.startswith("grid_cell_centroid_")
                    or variable.startswith("unallocated_population_")
                    or variable in {"cluster_location_x_3035", "cluster_location_y_3035"}
                )
            )
            stop_variable = not journey_variable and not competing_variable and not network_variable and (stop_table or (
                table == "magic_pass_decision_support"
                and (
                    variable.startswith("public_transport_stop_")
                    or variable.startswith("train_station_")
                    or variable.startswith("distance_to_nearest_public_transport_stop_")
                    or variable.startswith("distance_to_nearest_train_station_")
                    or variable.startswith("cluster_distance_to_nearest_public_transport_stop_")
                    or variable.startswith("cluster_distance_to_nearest_train_station_")
                    or variable.startswith("cluster_listing_nearest_public_transport_stop_")
                    or variable.startswith("cluster_listing_nearest_train_station_")
                    or variable.startswith("cluster_listings_with_public_transport_stop_")
                    or variable.startswith("cluster_listing_public_transport_stop_")
                    or variable.startswith("cluster_public_transport_stop_")
                    or variable.startswith("cluster_unassigned_public_transport_stop_")
                )
            ))
            road_variable = not journey_variable and not competing_variable and not network_variable and not stop_variable and (road_table or (
                table == "magic_pass_decision_support"
                and (
                    variable.startswith("national_road_")
                    or variable.startswith("cluster_distance_to_nearest_national_road_")
                    or variable.startswith("cluster_listings_with_national_road_")
                    or variable.startswith("cluster_listing_national_road_")
                    or variable.startswith("cluster_national_road_")
                    or variable.startswith("cluster_unassigned_national_road_")
                    or variable.startswith("cluster_nearest_national_road_")
                )
            ))
            transport_variable = not journey_variable and not competing_variable and not network_variable and not stop_variable and not road_variable and (transport_table or (
                table == "magic_pass_decision_support"
                and (
                    variable.startswith("npvm_")
                    or variable.startswith("transport_")
                    or variable.startswith("road_")
                    or variable.startswith("public_transport_")
                    or variable.startswith("cluster_listing_transport_")
                    or variable.startswith("cluster_listing_exact_transport_")
                    or variable.startswith("cluster_listings_")
                    or variable.startswith("cluster_maximum_zone_proxy_")
                    or variable.startswith("cluster_npvm_")
                    or variable
                    in {"cluster_transport_context_status", "unassigned_resort_ids"}
                )
            ))
            accessibility_variable = not journey_variable and not competing_variable and not network_variable and not stop_variable and not road_variable and not transport_variable and (accessibility_table or (
                table == "magic_pass_decision_support"
                and (
                    "accessibility" in variable
                    or "nearest_municipality_population" in variable
                    or variable.startswith("resident_population_within_")
                    or variable.startswith("swiss_only_population_within_")
                    or variable.startswith("cluster_location_")
                    or variable == "cluster_inside_swiss_country_boundary_2026"
                    or variable == "distance_to_swiss_country_boundary_km"
                    or variable
                    in {
                        "population_reference_year",
                        "boundary_reference_date",
                        "distance_crs",
                        "municipality_location_method",
                        "population_source_id",
                        "boundary_source_id",
                        "boundary_bridge_source_ids",
                    }
                )
            ))
            role = (
                "intentionally unavailable causal prediction"
                if variable in {"predicted_uplift_pct", "uplift_lower_pct", "uplift_upper_pct"}
                else "qualified distance versus scheduled-transit diagnostic"
                if table in {
                    "treatment_municipality_distance_transport_comparison",
                    "distance_transport_correlations_by_destination",
                    "distance_transport_band_summary",
                }
                else "qualified current arrival-node review"
                if table == "public_transport_arrival_node_review"
                else "qualified historical public-transport audit plan"
                if table == "public_transport_historical_audit_plan"
                else "qualified scheduled public-transport journey context"
                if journey_variable
                else "qualified current competing-pass roster context"
                if competing_variable
                else "qualified cluster-geography and network-distance sensitivity"
                if geography_sensitivity_variable
                else "qualified regional-weather gridded-product sensitivity"
                if weather_gridded_table
                else "qualified regional-weather alternative-station sensitivity"
                if weather_sensitivity_table
                else "qualified current ski-cluster and reviewed pass-network context"
                if network_variable
                else "qualified cross-border one-kilometre population context"
                if cross_border_population_variable
                else "qualified current public-transport-stop proximity context"
                if stop_variable
                else "qualified current national-road-axis proximity context"
                if road_variable
                else "qualified NPVM modelled travel-time context"
                if transport_variable
                else "qualified straight-line population context"
                if accessibility_variable
                else "strategic-need proxy"
                if "snow_vulnerability" in variable
                else "qualified point-container tourism context"
                if "tourism" in variable or "resident" in variable or "point_container" in variable
                else "descriptive analogue opportunity"
                if "analogue" in variable or "opportunity" in variable
                else "comparability / support"
                if "distance" in variable or "ood" in variable or "comparability" in variable
                else "descriptive segmentation / decision support"
            )
            formula_note = (
                "See src/data_processing/build_distance_transport_comparison.py"
                if table in {
                    "treatment_municipality_distance_transport_comparison",
                    "distance_transport_correlations_by_destination",
                    "distance_transport_band_summary",
                }
                else
                "See config/public_transport_arrival_node_review.csv and src/data_processing/build_public_transport_arrival_node_review.py"
                if table == "public_transport_arrival_node_review"
                else
                "See config/public_transport_historical_audit.json and src/data_processing/build_public_transport_historical_audit.py"
                if table == "public_transport_historical_audit_plan"
                else
                "See config/path_c_analysis.json and src/data_processing/build_public_transport_journey_context.py"
                if journey_variable
                else
                "See config/competing_pass_roster_2026_27.csv and src/data_processing/build_competing_pass_context.py"
                if competing_variable
                else
                "See config/path_c_analysis.json and src/data_processing/build_path_c_cluster_geography_sensitivity.py"
                if geography_sensitivity_variable
                else
                "See config/path_c_analysis.json, config/meteoswiss_gridded_weather_files.json and src/data_processing/build_weather_gridded_sensitivity.py"
                if weather_gridded_table
                else
                "See config/path_c_analysis.json, config/meteoswiss_weather_sensitivity_station_files.json and src/data_processing/build_weather_station_sensitivity.py"
                if weather_sensitivity_table
                else
                "See src/data_processing/build_path_c_network_context.py"
                if network_variable
                else
                "See config/path_c_analysis.json, config/eurostat_census_grid_2021.json and src/data_processing/build_cross_border_population_context.py"
                if cross_border_population_variable
                else
                "See config/path_c_analysis.json and src/data_processing/build_public_transport_stop_context.py"
                if stop_variable
                else
                "See config/path_c_analysis.json and src/data_processing/build_national_road_proximity_context.py"
                if road_variable
                else
                "See config/path_c_analysis.json and src/data_processing/build_transport_accessibility_context.py"
                if transport_variable
                else
                "See config/path_c_analysis.json and src/data_processing/build_accessibility_context.py"
                if accessibility_variable
                else "See config/path_c_analysis.json and Path C scripts; tourism context is implemented in src/data_processing/build_tourism_dependence_context.py"
            )
            limitation_note = (
                "No causal interpretation; current 2026 distance and two-day static timetable are not historical exposure, observed trips or visitor catchments"
                if table in {
                    "treatment_municipality_distance_transport_comparison",
                    "distance_transport_correlations_by_destination",
                    "distance_transport_band_summary",
                }
                else
                "No causal interpretation; current name/mode/municipality/distance review does not establish door-to-lift walking, historical node continuity or line stability"
                if table == "public_transport_arrival_node_review"
                else
                "No causal interpretation; historical stop/service comparison has not yet been executed and archive availability does not prove line stability"
                if table == "public_transport_historical_audit_plan"
                else
                "No causal interpretation; winter-2026 static schedules and algorithmic stop proxies are not real-time, historical or validated destination catchments"
                if journey_variable
                else
                "No causal interpretation; current links in three official rosters do not reconstruct historical competition, verify market absence or establish equivalent benefit intensity"
                if competing_variable
                else
                "No causal interpretation; listing-point spread and distance-rule sensitivity do not certify commercial-domain coherence, historical market structure, travel impedance or skier substitution"
                if geography_sensitivity_variable
                else
                "No causal interpretation; TabsM/RhiresM are station-informed grids rather than an independent measurement network, piste microclimate, snow-phase observation or causal-confounder validation"
                if weather_gridded_table
                else
                "No causal interpretation; next-nearest SwissMetNet sensitivity is not independent gridded validation, piste microclimate, snowfall phase or causal-confounder approval"
                if weather_sensitivity_table
                else
                "No causal interpretation; current directory-cluster and reviewed pass-network straight-line context is not historical market structure, travel impedance, observed competition or visitor behaviour"
                if network_variable
                else
                "No causal interpretation; 2021 census grid-cell centroids and straight-line radii are not travel-time markets, observed visitors or destination catchments; mixed and unallocated population remain explicit"
                if cross_border_population_variable
                else
                "No causal interpretation; straight-line stop-point distance is not a route, service frequency, timetable quality, validated arrival node or destination catchment"
                if stop_variable
                else
                "No causal interpretation; current national-road-axis proximity is not motorway classification, a usable entrance, a route, travel time, winter reliability or historical infrastructure"
                if road_variable
                else
                "No causal interpretation; zonal model output is not live routing, an observed arrival node or a destination catchment; municipality-constrained zone proxies are explicit"
                if transport_variable
                else
                "No causal interpretation; straight-line municipality representative-point context is not travel time or a destination catchment; foreign population is excluded"
                if accessibility_variable
                else "No causal interpretation; point-container context is not a destination catchment; blank uplift/composite fields are intentional"
            )
            definitions.append((
                variable,
                table,
                description,
                path_c_unit(variable),
                str(frame[variable].dtype),
                path_c_geographic_level.get(table, "existing lift cluster"),
                path_c_temporal_level.get(table, "undated structural snapshot; mixed lineage where stated"),
                path_c_sources[table]
                if journey_variable
                else "DERIVED_COMPETING_PASS_CONTEXT"
                if competing_variable
                else "DERIVED_PATH_C_CLUSTER_GEOGRAPHY_SENSITIVITY"
                if geography_sensitivity_variable
                else "DERIVED_WEATHER_GRIDDED_SENSITIVITY"
                if weather_gridded_table
                else "DERIVED_WEATHER_STATION_SENSITIVITY"
                if weather_sensitivity_table
                else "DERIVED_PATH_C_NETWORK_CONTEXT"
                if network_variable
                else "DERIVED_CROSS_BORDER_POPULATION_CONTEXT"
                if cross_border_population_variable
                else "DERIVED_PUBLIC_TRANSPORT_STOP_CONTEXT"
                if stop_variable
                else "DERIVED_NATIONAL_ROAD_PROXIMITY_CONTEXT"
                if road_variable
                else "DERIVED_TRANSPORT_ACCESSIBILITY_CONTEXT"
                if transport_variable
                else "DERIVED_ACCESSIBILITY_CONTEXT"
                if accessibility_variable
                else path_c_sources[table],
                "derived",
                formula_note,
                role,
                limitation_note,
            ))
    dictionary_rows = []
    for variable, table, description, unit, data_type, geo, temporal, source_id, raw_derived, formula, role, notes in definitions:
        dictionary_rows.append({
            "variable": variable, "table": table, "description": description, "unit": unit,
            "data_type": data_type, "geographic_level": geo, "temporal_level": temporal,
            "source_id": source_id, "raw_or_derived": raw_derived, "formula": formula,
            "causal_role": role, "missing_share": missing_share(paths[table], variable), "notes": notes,
        })
    dictionary = upsert(existing_dictionary, dictionary_rows, "variable", DICTIONARY_COLUMNS)
    # Variable names can repeat across tables; restore all untouched rows and de-duplicate on the proper compound key.
    incoming_dictionary = pd.DataFrame(dictionary_rows).reindex(columns=DICTIONARY_COLUMNS, fill_value="")
    existing_dictionary = existing_dictionary.reindex(columns=DICTIONARY_COLUMNS, fill_value="")
    keys = set(zip(incoming_dictionary["table"], incoming_dictionary["variable"]))
    keep = ~existing_dictionary.apply(lambda row: (row["table"], row["variable"]) in keys, axis=1)
    dictionary = pd.concat([existing_dictionary[keep], incoming_dictionary], ignore_index=True).fillna("")
    dictionary.sort_values(["table", "variable"]).to_csv(DICTIONARY_FILE, index=False)

    report_lines = [
        "# Data sources and provenance", "",
        "This report is generated from `metadata/data_sources_master.csv`. Raw internet responses are immutable and accompanied by collection-log entries and SHA-256 metadata where available.", "",
    ]
    for row in sources.to_dict("records"):
        report_lines.extend([
            f"## {row['source_id']} — {row['source_dataset_name'] or row['original_file_name']}", "",
            f"- **Contents and relevance:** {row['variable_description'] or 'Not yet documented.'}",
            f"- **Producer:** {row['source_organisation'] or 'Unknown.'}",
            f"- **Exact URL:** {row['source_page_url'] or row['direct_download_url'] or row['api_endpoint'] or 'Not documented.'}",
            f"- **Access and retrieval date:** {row['retrieval_method'] or 'Unknown'}; {row['retrieval_date'] or 'unknown date'}.",
            f"- **Variables:** {row['variable_name'] or 'Dataset-level record.'}",
            f"- **Transformations:** {row['transformation_applied'] or 'None documented.'}",
            f"- **Coverage:** {row['geographic_level'] or 'unknown geography'}; {row['temporal_resolution'] or 'unknown time resolution'}; {row['temporal_start'] or '?'} to {row['temporal_end'] or '?'}.",
            f"- **Limitations:** {row['quality_notes'] or row['notes'] or 'Not documented.'}",
            f"- **Local raw file:** `{row['local_raw_file'] or 'not cached / not applicable'}`.", "",
        ])
    report_lines.extend([
        "## Outstanding provenance gaps", "",
        "- The retrieval date of the supplied Bergfex and hotel CSV extracts is unknown.",
        "- The precise upstream download URL/version for `bahnen-winter_2056.gpkg` has not been established; it remains registered as a hashed local source rather than attributed by inference.",
        "- Earlier failed/truncated Magic Pass 2021 collection attempts remain in the append-only log, but a later checksum-verified full response is cached and used.",
        "- Current Magic map and press headline counts do not exactly match the 95 embedded destination records; this discrepancy is retained for review.", "",
    ])
    (ROOT / "reports" / "DATA_SOURCES.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({"source_records": len(sources), "dictionary_records": len(dictionary)}, indent=2))


if __name__ == "__main__":
    main()
