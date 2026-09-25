"""Build a claim-to-provenance citation map for the generated thesis drafts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_VERSION = "path_c_v0_31"


HISTORICAL_PASS_SOURCE_IDS = [
    "JUNGFRAU_TOP4_2018_19_CONTINUITY",
    "JUNGFRAU_TOP4_2024_25_EIGHTH_SEASON",
    "ATZMAENNIG_MEILENWEISS_2019_20_ORDER_FORM",
    "ATZMAENNIG_WINTER_BROCHURE_2020_21",
    "MALBUN_MEILENWEISS_2021_22_WINTER_BROCHURE",
    "PIZOL_ANNUAL_REPORT_2018_19",
    "BRUNNI_SCHNEEPASS_ZENTRALSCHWEIZ_2021_22_BROCHURE",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2022_23_ARCHIVED_ROSTER",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2022_23_ARCHIVED_SUMMER_ROSTER",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2023_24_MEDIA_KIT",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2024_25_MEDIA_KIT",
    "SAMNAUN_TOPCARD_SNOWPASS_TARIFFS_2017_18",
    "BBGR_ANNUAL_2017_18",
    "BBGR_ANNUAL_2018_19",
    "BBGR_ANNUAL_2019_20",
    "CORVATSCH_DIAVOLEZZA_ANNUAL_2018_19",
    "SBS_PRICING_STUDY_2020_TOPCARD",
    "GRAUBUENDEN_SNOWPASS_2018_19_ARCHIVED_PAGE",
    "GRAUBUENDEN_SNOWPASS_2019_20_ARCHIVED_PAGE",
]


def claim(
    claim_id: str,
    chapter: str,
    section: str,
    claim_scope: str,
    source_ids: list[str] | None,
    validation: str,
    status: str = "external_source_ready",
    note: str = "Use source_id as a temporary citation key; format in the final bibliography style.",
    citation_kind: str | None = None,
) -> dict[str, str]:
    return {
        "claim_id": claim_id,
        "chapter_file": chapter,
        "chapter_section": section,
        "claim_scope": claim_scope,
        "citation_kind": citation_kind or (
            "external_primary_or_scientific_source"
            if source_ids
            else "methodological_literature"
        ),
        "source_ids": "|".join(source_ids or []),
        "internal_validation_artifacts": validation,
        "citation_status": status,
        "editorial_note": note,
    }


def main() -> None:
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv").fillna("")
    if sources["source_id"].duplicated().any():
        raise ValueError("Source IDs must be unique before building the citation map")
    by_id = sources.set_index("source_id")
    methodological_literature = json.loads(
        (ROOT / "config" / "methodological_literature.json").read_text(
            encoding="utf-8"
        )
    )
    methodology_by_claim: dict[str, list[str]] = {}
    for reference in methodological_literature:
        methodology_by_claim.setdefault(reference["claim_group"], []).append(
            reference["source_id"]
        )
    expected_methodology_groups = {
        "METHOD_CAUSAL_IDENTIFICATION",
        "METHOD_CLUSTERING_VALIDATION",
        "METHOD_CAUSAL_ML_FEASIBILITY",
    }
    if set(methodology_by_claim) != expected_methodology_groups:
        raise ValueError("Methodological literature does not cover the declared claim groups")

    claims = [
        claim(
            "DATA_RESORT_DIRECTORY",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "2. Units of analysis and entity resolution",
            "The supplied resort attributes and names originate from the Bergfex Swiss directory snapshot.",
            ["BERGFEX_RESORT_DIRECTORY"],
            "reports/01_DATA_AUDIT.md|data_processed/resort_master.csv",
        ),
        claim(
            "DATA_LIFT_GEOMETRY",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "2. Units of analysis and entity resolution",
            "Lift geometry and the preserved listing-to-cluster assignments come from the supplied thesis files.",
            ["LOCAL_0f53d91bbb86", "LOCAL_03b4345dbe87"],
            "reports/03_CLUSTER_VALIDATION.md|reports/cluster_validation_summary.json",
        ),
        claim(
            "DATA_HOTEL_OUTCOMES",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "3. Hotel outcome and capacity panel",
            "Monthly hotel overnight stays and capacity measures are official BFS/FSO HESTA series.",
            ["BFS_HOTEL_DATA", "BFS_HOTEL_CAPACITY_DATA"],
            "reports/05_HOTEL_CAPACITY_AND_DEMAND_RECONCILIATION.md|reports/hotel_capacity_summary.json",
        ),
        claim(
            "DATA_MAGIC_HISTORY",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "2. Units of analysis and entity resolution",
            "Magic Pass entry, continuity and winter/summer status are reconstructed from official annual evidence.",
            ["MAGIC_OFFICIAL_EVIDENCE_SET", "MAGIC_PRESS_ARCHIVE"],
            "reports/08_MEMBERSHIP_EVIDENCE_REVIEW.md|reports/10_ANNUAL_WINTER_SUMMER_OFFERING_REVIEW.md|reports/membership_continuity_audit.csv",
        ),
        claim(
            "DATA_CURRENT_MAGIC_MAP",
            "reports/44_THESIS_RESULTS_DRAFT.md",
            "1. Data foundation and treatment panel",
            "Current Magic Pass destinations are a retrieval-date official map snapshot rather than historical entry evidence.",
            ["MAGIC_CURRENT_MAP"],
            "data_processed/magic_pass_current_destinations.csv|reports/current_magic_pass_summary.json",
        ),
        claim(
            "DATA_POPULATION_BOUNDARIES",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "5. Accessibility, tourism and competitive context",
            "Swiss population and municipal geometry use official BFS STATPOP and swisstopo boundary products.",
            ["BFS_STATPOP_DATA", "SWISSTOPO_BOUNDARIES_2026"],
            "reports/21_ACCESSIBILITY_CONTEXT.md|data_processed/municipality_population_geometry_2026.csv",
        ),
        claim(
            "DATA_CROSS_BORDER_POPULATION",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "5. Accessibility, tourism and competitive context",
            "Cross-border population context uses Eurostat Census Grid 2021 version 3.",
            ["EUROSTAT_CENSUS_GRID_2021_V3", "EUROSTAT_CENSUS_GRID_2021_V3_README"],
            "reports/29_CROSS_BORDER_POPULATION_CONTEXT.md|reports/cross_border_population_context_summary.json",
        ),
        claim(
            "DATA_SLF_SNOW",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "4. Climate, snow and temporal context",
            "Daily snow-depth proxies and stations use the official SLF historical IMIS archive and documentation.",
            [
                "SLF_IMIS_DAILY_SNOW",
                "SLF_IMIS_STATIONS",
                "SLF_IMIS_README",
                "SLF_DATA_SERVICE",
            ],
            "reports/06_SNOW_PROXY_REVIEW.md|reports/13_SNOW_PROXY_SENSITIVITY.md",
        ),
        claim(
            "DATA_SPASS_SNOW_GRID",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "4. Climate, snow and temporal context",
            "The gridded snow sensitivity uses the scientific SPASS HSCLQMD archive.",
            ["SLF_SPASS_HSCLQMD_GRID_1962_2023"],
            "reports/36_SNOW_GRIDDED_SENSITIVITY.md|reports/snow_gridded_sensitivity_summary.json",
        ),
        claim(
            "DATA_METEOSWISS_STATIONS",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "4. Climate, snow and temporal context",
            "Regional weather anomalies use official SwissMetNet station data and documentation.",
            [
                "METEOSWISS_SMN_DAILY_SELECTED",
                "METEOSWISS_SMN_DAILY_ALTERNATIVE_SELECTED",
                "METEOSWISS_SMN_INVENTORY",
                "METEOSWISS_SMN_DOCUMENTATION",
            ],
            "reports/07_WEATHER_PROXY_REVIEW.md|reports/34_WEATHER_STATION_SENSITIVITY.md",
        ),
        claim(
            "DATA_METEOSWISS_GRIDS",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "4. Climate, snow and temporal context",
            "The spatial weather sensitivity uses official TabsM and RhiresM monthly grids and product documentation.",
            [
                "METEOSWISS_TABSM_RHIRESM_MONTHLY_GRID_2013_202603",
                "METEOSWISS_SPATIAL_CLIMATE_ANALYSIS_DOCUMENTATION",
            ],
            "reports/35_WEATHER_GRIDDED_SENSITIVITY.md|reports/weather_gridded_sensitivity_summary.json",
        ),
        claim(
            "DATA_NPVM_ACCESSIBILITY",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "5. Accessibility, tourism and competitive context",
            "Modelled road and public-transport access to centres uses the official ARE NPVM product and methodology.",
            [
                "ARE_NPVM_TRAVEL_TIME_2025",
                "ARE_NPVM_TRAVEL_TIME_2025_STAC",
                "ARE_TRANSPORT_ACCESSIBILITY_METHOD",
            ],
            "reports/22_TRANSPORT_ACCESSIBILITY_CONTEXT.md|reports/27_TRANSPORT_ZONE_PROXY_AUDIT.md",
        ),
        claim(
            "DATA_PUBLIC_TRANSPORT_STOPS",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "5. Accessibility, tourism and competitive context",
            "Passenger-stop proximity uses the official BAV/OFT public-transport-stop geodata model.",
            ["BAV_PUBLIC_TRANSPORT_STOPS_2026", "BAV_PUBLIC_TRANSPORT_STOPS_MODEL"],
            "reports/23_PUBLIC_TRANSPORT_STOP_CONTEXT.md",
        ),
        claim(
            "DATA_GTFS_JOURNEYS",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "5. Accessibility, tourism and competitive context",
            "Scheduled journeys use the official Swiss timetable 2026 GTFS build.",
            ["SKI_GTFS_TIMETABLE_2026_WINTER_20260207"],
            "reports/24_PUBLIC_TRANSPORT_JOURNEY_CONTEXT.md|reports/26_PUBLIC_TRANSPORT_ARRIVAL_NODE_REVIEW.md|reports/28_DISTANCE_TRANSPORT_COMPARISON.md",
        ),
        claim(
            "DATA_NATIONAL_ROADS",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "5. Accessibility, tourism and competitive context",
            "Road-axis proximity uses official FEDRO/ASTRA national-route geometries.",
            ["ASTRA_NATIONAL_ROAD_AXES_2026", "ASTRA_NATIONAL_ROAD_AXES_2026_STAC"],
            "reports/30_NATIONAL_ROAD_PROXIMITY_CONTEXT.md",
        ),
        claim(
            "DATA_CURRENT_COMPETING_PASSES",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "5. Accessibility, tourism and competitive context",
            "Current competing-pass context uses official AlpsPass, Meilenweiss and Schneepass Zentralschweiz rosters.",
            [
                "ALPSPASS_2026_27_ROSTER",
                "ALPSPASS_2026_27_GTC",
                "MEILENWEISS_CURRENT_ROSTER",
                "SCHNEEPASS_ZENTRALSCHWEIZ_2026_27_ROSTER",
            ],
            "reports/31_COMPETING_PASS_CONTEXT.md",
        ),
        claim(
            "DATA_HISTORICAL_COMPETING_PASSES",
            "reports/44_THESIS_RESULTS_DRAFT.md",
            "7. Competition and network context",
            "Historical positive-presence evidence covers five partially reconstructed products and distinct benefit tiers.",
            HISTORICAL_PASS_SOURCE_IDS,
            "reports/41_HISTORICAL_COMPETING_PASS_CONTEXT.md|reports/historical_competing_pass_context_summary.json",
        ),
        claim(
            "METHOD_CAUSAL_IDENTIFICATION",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "6. Causal feasibility assessment",
            "Parallel trends, stable treatment, no interference and credible donor conditions require methodological literature citations.",
            methodology_by_claim["METHOD_CAUSAL_IDENTIFICATION"],
            "reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md",
            status="peer_reviewed_literature_ready",
            note="Use the verified DiD/event-study and interference articles; retain the project-specific rejection as an internal empirical result.",
            citation_kind="peer_reviewed_methodological_literature",
        ),
        claim(
            "METHOD_CLUSTERING_VALIDATION",
            "reports/43_THESIS_METHODS_DRAFT.md",
            "7. Path C structural segmentation and analogues",
            "K-means, silhouette and adjusted Rand stability require standard methodological references.",
            methodology_by_claim["METHOD_CLUSTERING_VALIDATION"],
            "reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md|reports/19_PATH_C_AGGREGATION_SENSITIVITY.md",
            status="peer_reviewed_literature_ready",
            note="Use the verified silhouette and chance-corrected partition-comparison references; retain repository reports for implementation details.",
            citation_kind="peer_reviewed_methodological_literature",
        ),
        claim(
            "METHOD_CAUSAL_ML_FEASIBILITY",
            "reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md",
            "2. Implications for causal inference and machine learning",
            "Causal ML cannot repair an unidentified treatment/control design and requires adequate effective sample size.",
            methodology_by_claim["METHOD_CAUSAL_ML_FEASIBILITY"],
            "reports/17_CHECKPOINT_4_5_PATH_C_DECISION.md|reports/model_feasibility_report.md",
            status="peer_reviewed_literature_ready",
            note="Use the verified causal-forest and meta-learner articles while preserving identification, overlap and sample-support requirements and the project-specific rejection.",
            citation_kind="peer_reviewed_methodological_literature",
        ),
        claim(
            "RESULT_PATH_C_COUNTS",
            "reports/44_THESIS_RESULTS_DRAFT.md",
            "3–8. Path C results",
            "Segmentation, stability, scope, transport and dashboard counts are derived analytical results.",
            ["DERIVED_PATH_C_DECISION_SUPPORT"],
            "reports/18_PATH_C_SEGMENTATION_AND_ANALOGUES.md|reports/19_PATH_C_AGGREGATION_SENSITIVITY.md|reports/39_CHECKPOINT_6_BUSINESS_DECISION_FRAMEWORK.md|reports/42_THESIS_RESULTS_SYNTHESIS.md",
            status="internal_result_with_lineage",
            note="Cite the thesis tables/figures in the prose; use the derived source record only for lineage, not as an external bibliographic authority.",
        ),
    ]

    claims_frame = pd.DataFrame(claims)
    referenced_ids = sorted(
        {
            source_id
            for packed in claims_frame["source_ids"]
            for source_id in packed.split("|")
            if source_id
        }
    )
    missing = [source_id for source_id in referenced_ids if source_id not in by_id.index]
    if missing:
        raise ValueError(f"Citation map contains unknown source IDs: {missing}")

    claims_frame.to_csv(ROOT / "reports/thesis_claim_source_matrix.csv", index=False)

    source_rows = []
    for source_id in referenced_ids:
        row = by_id.loc[source_id]
        bibliographic_role = (
            "internal_lineage"
            if source_id.startswith(("DERIVED_", "LOCAL_"))
            else "external_source"
        )
        source_rows.append(
            {
                "source_id": source_id,
                "bibliographic_role": bibliographic_role,
                "source_organisation": row["source_organisation"],
                "source_dataset_name": row["source_dataset_name"],
                "source_page_url": row["source_page_url"],
                "temporal_start": row["temporal_start"],
                "temporal_end": row["temporal_end"],
                "confidence_level": row["confidence_level"],
                "quality_notes": row["quality_notes"],
            }
        )
    bibliography_frame = pd.DataFrame(source_rows)
    external_bibliography = bibliography_frame[
        bibliography_frame["bibliographic_role"].eq("external_source")
    ]
    external_sources_missing_url = int(
        external_bibliography["source_page_url"].astype(str).str.strip().eq("").sum()
    )
    if external_sources_missing_url:
        raise ValueError("A registered external citation source has no source-page URL")
    bibliography_frame.to_csv(
        ROOT / "reports/thesis_source_bibliography_worklist.csv", index=False
    )

    claim_table = "\n".join(
        f"| `{row.claim_id}` | {Path(row.chapter_file).name}: {row.chapter_section} | {row.citation_status} | "
        f"{row.source_ids.replace('|', '<br>') if row.source_ids else '—'} |"
        for row in claims_frame.itertuples()
    )
    source_sections = []
    for row in bibliography_frame.itertuples():
        dates = "–".join(
            value for value in [str(row.temporal_start), str(row.temporal_end)] if value
        ) or "not stated"
        source_sections.append(
            f"### `{row.source_id}`\n\n"
            f"- Organisation: {row.source_organisation}\n"
            f"- Dataset/document: {row.source_dataset_name}\n"
            f"- URL: {row.source_page_url or 'not available'}\n"
            f"- Temporal scope: {dates}\n"
            f"- Confidence: {row.confidence_level or 'not stated'}\n"
            f"- Citation note: use the official organisation and document title; verify the final access-date format required by the thesis style.\n\n"
        )

    report = f"""# Thesis claim-to-source citation map

This editorial map links the main externally sourced claims in the generated thesis chapters to the master provenance register. It does not invent author names, publication years, DOI values or bibliography entries that are absent from the recorded source. `source_id` values are temporary, auditable citation keys; the final thesis must format them in the required university style.

## Status summary

- Mapped claims: **{len(claims_frame)}**
- Unique registered sources referenced: **{len(referenced_ids)}**
- External bibliography sources: **{len(external_bibliography)}**
- Internal lineage entries not requiring an external URL: **{int(bibliography_frame['bibliographic_role'].eq('internal_lineage').sum())}**
- Claims ready for external-source bibliography formatting: **{int(claims_frame['citation_status'].eq('external_source_ready').sum())}**
- Derived result claims with lineage: **{int(claims_frame['citation_status'].eq('internal_result_with_lineage').sum())}**
- Methodological claims with verified peer-reviewed literature: **{int(claims_frame['citation_status'].eq('peer_reviewed_literature_ready').sum())}**
- Methodological claims still requiring peer-reviewed literature: **{int(claims_frame['citation_status'].eq('literature_citation_required').sum())}**

## Claim map

| Claim ID | Draft location | Status | Registered source IDs |
|---|---|---|---|
{claim_table}

The detailed insertion notes and internal validation artifacts are in `reports/thesis_claim_source_matrix.csv`. The bibliography worklist is in `reports/thesis_source_bibliography_worklist.csv`.

## Editorial rules

1. Cite external official/scientific sources for data definitions, published rosters and product scope.
2. Cite thesis tables, figures or repository reports for derived counts and diagnostics; do not present the pipeline as an external authority.
3. Use the verified peer-reviewed methodological literature for causal identification, interference, clustering validation and causal-ML feasibility; do not treat method availability as project-specific identification.
4. Keep retrieval dates for mutable web pages and archived captures.
5. Do not replace missing bibliographic metadata with guesses. Mark it for manual completion.

## Registered-source worklist

{''.join(source_sections)}
"""
    (ROOT / "reports/46_THESIS_CITATION_MAP.md").write_text(
        report.rstrip() + "\n", encoding="utf-8"
    )

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "mapped_claims": len(claims_frame),
        "unique_registered_sources": len(referenced_ids),
        "registered_external_sources": len(external_bibliography),
        "internal_lineage_sources": int(
            bibliography_frame["bibliographic_role"].eq("internal_lineage").sum()
        ),
        "external_sources_missing_url": external_sources_missing_url,
        "external_source_ready_claims": int(
            claims_frame["citation_status"].eq("external_source_ready").sum()
        ),
        "internal_result_with_lineage_claims": int(
            claims_frame["citation_status"].eq("internal_result_with_lineage").sum()
        ),
        "peer_reviewed_literature_ready_claims": int(
            claims_frame["citation_status"].eq("peer_reviewed_literature_ready").sum()
        ),
        "literature_citation_required_claims": int(
            claims_frame["citation_status"].eq("literature_citation_required").sum()
        ),
        "unknown_source_ids": missing,
        "interpretation": "editorial_claim_to_registered_provenance_map_not_final_formatted_bibliography",
    }
    (ROOT / "reports/thesis_citation_map_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
