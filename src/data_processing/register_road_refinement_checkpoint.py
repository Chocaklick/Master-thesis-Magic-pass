"""Register all collected/discovery outcomes and deferred endpoint audit.

No download or routing, no claim that discoveries are verified endpoints.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_accessibility_road_reference import archived_metadata
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = "DERIVED_ACCESSIBILITY_ROAD_ORIGIN_GEOCODING_AUDIT_2026"
TABLE = "accessibility_road_origin_geocoding_audit"
OUTPUT = "reports/accessibility_road_origin_geocoding_audit.csv"


def main():
    path = ROOT / "metadata/data_sources_master.csv"
    master = pd.read_csv(path, dtype=str, keep_default_na=False)
    log = pd.read_csv(ROOT / "logs/data_collection_log.csv", dtype=str, keep_default_na=False)
    rows = []
    discovery = json.loads((ROOT / "config/accessibility_road_bulk_discovery_sources.json").read_text(encoding="utf-8"))
    for spec in discovery:
        if spec["source_id"] in set(master.source_id):
            continue  # Already registered used endpoint sources keep richer exact lineage.
        evidence = dict(source_id=spec["source_id"], variable_name="road_endpoint_refinement_discovery",
            variable_description=spec["description"], source_organisation=spec["organisation"],
            source_dataset_name="Deferred administrative/parking refinement discovery; not completed road endpoints",
            source_page_url=spec["url"], processed_file="reports/88_REFERENCE_ROUTIERE_ARRETS_TP_FR.md",
            geographic_level="directory or operator page", temporal_resolution="retrieval snapshot2026-10-07", unit="documentation",
            license="Original source terms, do not redistribute unreviewed originals", access_conditions="Public source; robots respected, blocked sources not bypassed",
            confidence_level="source discovery only, no endpoint inference", transformation_applied="Archived/reviewed as discovery; user deferred precise endpoints on2026-10-07",
            quality_notes="No point/time inferred; official street contacts distinguish postal versus physical addresses",
            notes="Retained for later refinement, not an analytical filter")
        try:
            metadata = archived_metadata(spec["source_id"])
        except ValueError:
            failed = log[log.source_id.eq(spec["source_id"])]
            if failed.empty:
                raise ValueError("Unrecorded attempted discovery: " + spec["source_id"])
            record = failed.iloc[-1]
            evidence.update(retrieval_date=record.timestamp, retrieval_method="Attempted robots-respecting collection, no usable original",
                quality_notes="Collection outcome " + record.status + "; " + record.error + "; not bypassed")
        else:
            evidence.update(retrieval_date=metadata["retrieval_date"], retrieval_method=metadata.get("retrieval_method", "Robots-respecting GET, immutable original and SHA"),
                local_raw_file=metadata["raw_file"], original_file_name=Path(metadata["raw_file"]).name,
                direct_download_url=metadata.get("final_url", spec["url"]), notes="SHA256=" + metadata["sha256"] + "; refinement deferred by user")
            if "PUBLIC_JS" in spec["source_id"]:
                evidence["quality_notes"] = "HTTP200 returned HTML, not requested JavaScript; unusable asset response, no API inferred or bypassed"
            if "PARQUET" in spec["source_id"]:
                evidence["quality_notes"] = "Valid archive retained but parquet engine absent locally; official GPKG equivalent used without package installation; polygon coordinates never used"
        rows.append(evidence)
    for spec in json.loads((ROOT / "config/accessibility_road_stop_warning_sources.json").read_text(encoding="utf-8")):
        rows.append(dict(source_id=spec["source_id"], variable_name="road_stop_proxy_documentation",
            variable_description=spec["description"], source_organisation=spec["organisation"], source_dataset_name="Primary proxy/routing-limit documentation",
            source_page_url=spec["url"], retrieval_date=spec["consultation_date"], retrieval_method="Primary page consulted with web tool, no original downloaded",
            processed_file="reports/88_REFERENCE_ROUTIERE_ARRETS_TP_FR.md", geographic_level="documented access restriction or API methodology",
            temporal_resolution="consultation date, not historical certification", unit="documentation", license="See original source terms",
            access_conditions="Public primary page", transformation_applied="Warning only; no replacement coordinate/time, no exclusion",
            quality_notes="No universal car-free screening certified; model duration is not a legal door-to-door driving time", confidence_level="primary published statement"))
    rows.append(dict(source_id=SOURCE, variable_name="exact_official_origin_geocoding_audit",
        variable_description="All36 exact Bern/Grisons address candidates retained, including7 pending; deferred precise endpoint refinement",
        source_organisation="Thesis project /official Bern and Grisons contacts /swisstopo",
        source_dataset_name="Exact address candidate audit", retrieval_date="2026-10-07", retrieval_method="Deterministic Python exact comparison, not fuzzy-first-result choice",
        processed_file=OUTPUT, geographic_level="Official BFS-keyed administrative addresses", temporal_resolution="current source snapshot", unit="matches and explicit statuses",
        license="Inherited source terms", access_conditions="Local derived audit", transformation_applied="Normalized exact street/number/postcode/BFS, unique result required; all candidates retained",
        quality_notes="Postal/physical postcode mismatch and duplicate physical points remain pending, not exclusions. Source originals unchanged.",
        confidence_level="exact factual candidate audit", notes="Parent IDs in every row; Fribourg6 points separate official main-building layer, not this geocoding audit. User deferred further refinement."))
    ids = {r["source_id"] for r in rows}
    write_csv(pd.concat([master[~master.source_id.isin(ids)], pd.DataFrame(rows).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(""), path)
    path = ROOT / "metadata/data_dictionary.csv"
    dictionary = pd.read_csv(path, dtype=str, keep_default_na=False)
    frame = pd.read_csv(ROOT / OUTPUT)
    descriptions = {
        "municipality_bfs_id": "Stable existing municipal territory BFS ID, no name-only assignment",
        "address_source_id": "Official primary administrative street contact source ID",
        "coordinate_source_id": "Archived official SearchServer query source ID",
        "source_address": "Unaltered reviewed official address, potentially postal postcode not physical postcode",
        "exact_candidate_count": "Number of exact normalized street/number/postcode/BFS candidates; not accepted unless unique",
        "status": "Unique exact coordinate verified or address coordinate awaiting review; no commune excluded",
        "all_candidate_details": "All original candidate address details retained as JSON, not only first result",
    }
    rows = [dict(variable=f, table=TABLE, description=descriptions[f], unit="count" if f == "exact_candidate_count" else "text/identifier/status",
        data_type=str(frame[f].dtype), geographic_level="municipality BFS", temporal_level="2026 endpoint refinement snapshot", source_id=SOURCE,
        raw_or_derived="derived candidate audit", formula="Exact official street/number/postcode/BFS comparison; German ae/oe/ue transliteration, no approximate selection",
        causal_role="deferred endpoint refinement, not sample filter", missing_share=f"{frame[f].isna().mean():.6f}",
        notes="No polygon centroid, fuzzy first match or missing-time imputation") for f in frame]
    write_csv(pd.concat([dictionary[dictionary.table.ne(TABLE)], pd.DataFrame(rows).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(""), path)
    print(json.dumps({"registered_discovery_documentation_and_audit_sources": len(ids), "geocoding_audit_variables": len(rows), "network_requests": 0}))


if __name__ == "__main__":
    main()
