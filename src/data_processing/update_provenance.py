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
    paths = sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"))
    if not paths:
        return None
    return json.loads(paths[-1].read_text(encoding="utf-8"))


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
            manual_verification="reviewed" if source_id in {"MAGIC_2017", "MAGIC_2018", "MAGIC_2019", "MAGIC_2020", "MAGIC_2022", "MAGIC_2023", "MAGIC_2024", "MAGIC_2025"} else "pending or page-level",
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
    sources = upsert(existing_sources, rows, "source_id", SOURCE_COLUMNS)
    sources.to_csv(SOURCE_FILE, index=False)

    existing_dictionary = pd.read_csv(DICTIONARY_FILE, dtype=str, keep_default_na=False)
    definitions = [
        ("hotel_overnights", "hotel_municipality_month", "Hotel overnight stays in open establishments", "overnight stays", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "cleaned source", "Parsed only when source token is a nonnegative integer", "outcome", "Suppressed '...' values remain missing"),
        ("hotel_arrivals", "hotel_municipality_month", "Hotel arrivals in open establishments", "persons", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "cleaned source", "Parsed only when source token is a nonnegative integer", "secondary outcome", "Suppressed values remain missing"),
        ("domestic_overnights", "hotel_municipality_month", "Overnight stays by Swiss residents", "overnight stays", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "cleaned source", "Parsed only when source token is a nonnegative integer", "secondary outcome", "Suppressed values remain missing"),
        ("foreign_overnights", "hotel_municipality_month", "Total minus domestic overnight stays", "overnight stays", "Int64", "municipality", "monthly", "BFS_HOTEL_DATA", "derived", "hotel_overnights - domestic_overnights", "secondary outcome", "Missing when either component is unavailable"),
        ("log_overnights", "hotel_municipality_month", "Log-transformed hotel overnight stays", "log points", "float", "municipality", "monthly", "BFS_HOTEL_DATA", "derived", "log(1 + hotel_overnights)", "outcome", "No imputation"),
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
    ]
    paths = {
        "hotel_municipality_month": ROOT / "data_processed" / "hotel_municipality_month.csv",
        "resort_master": ROOT / "data_processed" / "resort_master.csv",
        "resort_point_municipality": ROOT / "data_processed" / "resort_point_municipality.csv",
        "magic_pass_membership_history": ROOT / "data_processed" / "magic_pass_membership_history.csv",
        "magic_pass_current_destinations": ROOT / "data_processed" / "magic_pass_current_destinations.csv",
        "resort_data_quality": ROOT / "data_processed" / "resort_data_quality.csv",
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
        "- Magic Pass 2021 and 2026 PDF downloads did not complete in the scripted collector; failures remain in the collection log. The official press archive HTML is cached, and 2026 entry events are outside the current outcome window.",
        "- Current Magic map and press headline counts do not exactly match the 95 embedded destination records; this discrepancy is retained for review.", "",
    ])
    (ROOT / "reports" / "DATA_SOURCES.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({"source_records": len(sources), "dictionary_records": len(dictionary)}, indent=2))


if __name__ == "__main__":
    main()
