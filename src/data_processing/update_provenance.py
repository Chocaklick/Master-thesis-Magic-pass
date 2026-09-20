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
    rows: list[dict] = []

    bfs_metadata = cached_metadata("BFS_HOTEL_METADATA")
    bfs_capacity_metadata = cached_metadata("BFS_HOTEL_CAPACITY_METADATA")
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

    magic_ids = [key for key in configured if key.startswith("MAGIC_")]
    for source_id in magic_ids:
        item = configured[source_id]
        metadata = cached_metadata(source_id)
        is_archive = source_id == "MAGIC_PRESS_ARCHIVE"
        is_map = source_id == "MAGIC_CURRENT_MAP"
        rows.append(blank_source(
            source_id,
            variable_name=("current_magic_destination" if is_map else "membership_event_evidence"),
            variable_description=item["description"],
            source_organisation=item["organisation"],
            source_dataset_name=("Official current destination map" if is_map else "Official Magic Pass press material"),
            source_page_url=(item["url"] if is_archive or is_map else configured["MAGIC_PRESS_ARCHIVE"]["url"]),
            direct_download_url=item["url"] if not is_archive and not is_map else "",
            retrieval_method="HTTP GET with immutable response and SHA-256 sidecar" if metadata else "attempted HTTP GET; see collection log",
            retrieval_date=metadata.get("retrieval_date", "") if metadata else "",
            original_file_name=raw_name(metadata),
            local_raw_file=metadata.get("raw_file", "") if metadata else "",
            processed_file=("data_processed/magic_pass_current_destinations.csv" if is_map else "data_processed/magic_pass_membership_history.csv"),
            geographic_level="official ski destination",
            temporal_resolution=("retrieval-date snapshot" if is_map else "dated announcement / season"),
            temporal_start=("2017" if is_archive else source_id.removeprefix("MAGIC_") if source_id.removeprefix("MAGIC_").isdigit() else ""),
            temporal_end=("2026" if is_archive or is_map else ""),
            unit="destination membership event",
            license="UNKNOWN; preserve citation and original URL",
            access_conditions="Public official website; automated retrieval respects robots.txt",
            transformation_applied="Page-numbered text extraction and manually reviewed event transcription" if not is_map else "Embedded official destination JSON extracted from cached HTML",
            quality_notes=("Current snapshot is not historical evidence" if is_map else "Destination/operator scope may differ from Bergfex listing scope"),
            confidence_level=("high for source authenticity; event/entity confidence stored per row" if metadata else "official URL verified; local retrieval pending"),
            manual_verification="reviewed" if source_id in {"MAGIC_2017", "MAGIC_2018", "MAGIC_2019", "MAGIC_2020", "MAGIC_2021_APRIL", "MAGIC_2022", "MAGIC_2022_DOSSIER", "MAGIC_2023", "MAGIC_2024", "MAGIC_2025"} else "pending or page-level",
            notes="Not used as extracted evidence because download did not complete" if not metadata else "",
        ))
    rows.append(blank_source(
        "MAGIC_OFFICIAL_EVIDENCE_SET",
        variable_name="membership_event_history",
        variable_description="Union of official Magic Pass seasonal press evidence and dated archive notices",
        source_organisation="Magic Mountains Cooperation",
        source_dataset_name="Official Magic Pass evidence set",
        source_page_url=configured["MAGIC_PRESS_ARCHIVE"]["url"],
        retrieval_method="Derived only from source rows MAGIC_2017 through MAGIC_2025 and MAGIC_PRESS_ARCHIVE",
        processed_file="data_processed/magic_pass_membership_history.csv",
        geographic_level="official ski destination with candidate resort link",
        temporal_resolution="season/event",
        temporal_start="2017/2018",
        temporal_end="2025/2026",
        unit="membership event",
        transformation_applied="Manual event transcription; reviewed aliases and unique normalised labels create candidate links",
        quality_notes="Incomplete continuity/exit audit; unresolved destinations retained",
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
    ]
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
            processed_file="data_processed/treatment_destination_units.csv",
            geographic_level="official destination or municipality",
            temporal_resolution="retrieval-date scope snapshot",
            temporal_start="",
            temporal_end="2026",
            unit="scope evidence",
            license="UNKNOWN; preserve citation and original URL",
            access_conditions="Public official website; automated retrieval respects robots.txt",
            transformation_applied="Manually reviewed scope statement encoded in config/treatment_destination_review.json",
            quality_notes="Current scope evidence does not by itself establish historical tourism exposure",
            confidence_level="high for stated scope; analytical mapping remains explicitly qualified",
            manual_verification="reviewed",
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
        quality_notes="No row is causal-ready; SLF and MeteoSwiss proxies are not direct piste observations; treatment continuity, controls, and other time-varying confounders remain unresolved",
        confidence_level="high for reproducible aggregation; low for causal treatment status",
        manual_verification="automated tests plus destination review",
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
        ("weather_causal_covariate_approved", "destination_month_panel", "Whether the regional weather proxy has passed all causal-use validation gates", "boolean", "boolean", "reviewed destination via station proxy", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "always false at this checkpoint", "quality gate", "Station choice and gridded-data sensitivity remain pending"),
        ("assumed_active_component_count", "destination_month_panel", "Diagnostic count of entered components carried forward until a documented exit", "count", "integer", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "cumulative documented component entries with documented exit override", "treatment intensity candidate", "Continuity is an unverified assumption"),
        ("event_time_months", "destination_month_panel", "Months relative to the first analytical membership anchor", "months", "integer", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "calendar month difference from first_analysis_anchor", "event-time index", "Not sufficient for causal event-study identification"),
        ("causal_ready", "destination_month_panel", "Whether the destination-month row passes all causal evidence gates", "boolean", "boolean", "reviewed destination", "monthly", "DERIVED_REVIEWED_DESTINATION_PANEL", "derived", "always false at this checkpoint", "quality gate", "Continuity, confounding, spillovers, and controls remain unresolved"),
        ("membership_status", "magic_pass_membership_status_by_season", "Evidence status for a reviewed destination in each annual Magic Pass season", "category", "string", "reviewed destination", "annual pass season", "MAGIC_OFFICIAL_EVIDENCE_SET", "manual evidence audit", "documented active, unverified active continuity, not yet entered, or documented inactive after exit", "treatment history", "Missing annual evidence is never silently filled"),
        ("documented_active", "magic_pass_membership_status_by_season", "Whether explicit official evidence documents active base membership in the season", "boolean", "boolean", "reviewed destination", "annual pass season", "MAGIC_OFFICIAL_EVIDENCE_SET", "derived evidence flag", "true only for entry, full-roster, named-continuation, or last-active exit evidence", "treatment history quality", "False can mean unverified and must not be read as documented non-membership"),
        ("continuity_fully_documented", "membership_continuity_audit", "Whether every active season from first entry through exit or 2025/2026 has explicit evidence", "boolean", "boolean", "reviewed destination", "2017/2018-2025/2026", "MAGIC_OFFICIAL_EVIDENCE_SET", "derived audit", "no unverified_active_continuity season in the required active window", "quality gate", "Does not resolve confounding, spillovers, or controls"),
        ("known_magic_exposure_from_resolved_links", "control_contamination_audit", "Whether any resort point in the municipality has a resolved historical or current Magic Pass link", "boolean", "boolean", "municipality reached by resort point", "historical plus current snapshot", "DERIVED_MULTI_SOURCE", "derived screen", "any linked resort_id appears in a base-entry event or current official-map candidate link", "control contamination", "False is only an upper-bound candidate because unresolved official labels remain"),
        ("minimum_resort_point_distance_km", "treatment_control_candidate_matrix", "Minimum great-circle distance between a donor-municipality resort point and a treated destination component point", "kilometres", "float", "treatment-donor pair", "review snapshot", "GEOADMIN_MUNICIPALITY_IDENTIFY", "derived geospatial screen", "minimum haversine distance across supplied resort points", "spillover screen", "Point distance does not prove absence of tourism spillovers"),
        ("provisional_donor_30km_36pre", "treatment_control_candidate_matrix", "Mechanical donor-screen flag using resolved membership, geography, and outcome coverage", "boolean", "boolean", "treatment-donor pair", "monthly coverage snapshot", "DERIVED_MULTI_SOURCE", "derived screen", "no resolved Magic exposure AND not treated scope AND distance > 30 km AND >=36 pre months AND >=24 post months", "donor candidate", "Not an approved causal control; 30 km is a sensitivity threshold, not an identification result"),
        ("causal_control_approved", "treatment_control_candidate_matrix", "Whether the donor passes all causal control audits", "boolean", "boolean", "treatment-donor pair", "review snapshot", "DERIVED_MULTI_SOURCE", "derived", "always false at this checkpoint", "quality gate", "Unresolved membership, spillovers, and time-varying confounders remain"),
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
    }
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
        "- The Magic Pass 2021 PDF download did not complete in the scripted collector; failures remain in the collection log. The 2026 PDF and official press archive HTML are cached, and 2026 entry events are outside the current outcome window.",
        "- Current Magic map and press headline counts do not exactly match the 95 embedded destination records; this discrepancy is retained for review.", "",
    ])
    (ROOT / "reports" / "DATA_SOURCES.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({"source_records": len(sources), "dictionary_records": len(dictionary)}, indent=2))


if __name__ == "__main__":
    main()
