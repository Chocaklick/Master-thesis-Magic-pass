"""Validate and render the thesis methodological-literature register."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_VERSION = "path_c_v0_31"
CONFIG_PATH = ROOT / "config" / "methodological_literature.json"
EXPECTED_GROUPS = {
    "METHOD_CAUSAL_IDENTIFICATION",
    "METHOD_CLUSTERING_VALIDATION",
    "METHOD_CAUSAL_ML_FEASIBILITY",
}
REQUIRED_FIELDS = {
    "source_id",
    "claim_group",
    "authors",
    "publication_year",
    "title",
    "journal",
    "volume",
    "issue",
    "pages",
    "doi",
    "source_page_url",
    "publisher",
    "relevance",
    "interpretive_boundary",
}


def main() -> None:
    records = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("Methodological literature config must be a non-empty list")
    for index, record in enumerate(records):
        missing = REQUIRED_FIELDS - set(record)
        if missing:
            raise ValueError(f"Literature record {index} lacks fields: {sorted(missing)}")

    frame = pd.DataFrame(records).fillna("")
    if frame["source_id"].duplicated().any():
        raise ValueError("Methodological source IDs must be unique")
    if frame["doi"].str.lower().duplicated().any():
        raise ValueError("Methodological DOI values must be unique")
    if set(frame["claim_group"]) != EXPECTED_GROUPS:
        raise ValueError("Methodological literature must cover the three declared claim groups")
    if not frame["source_page_url"].str.startswith("https://").all():
        raise ValueError("Every methodological reference must have an HTTPS publisher URL")
    if not frame["doi"].str.match(r"^10\.").all():
        raise ValueError("Every methodological reference must have a DOI")

    frame = frame.sort_values(["claim_group", "publication_year", "source_id"])
    frame.to_csv(ROOT / "reports" / "thesis_methodological_references.csv", index=False)

    group_titles = {
        "METHOD_CAUSAL_IDENTIFICATION": "Causal identification, staggered adoption and interference",
        "METHOD_CLUSTERING_VALIDATION": "Clustering validation and partition stability",
        "METHOD_CAUSAL_ML_FEASIBILITY": "Causal machine-learning feasibility",
    }
    sections = []
    for group in sorted(EXPECTED_GROUPS):
        sections.extend([f"## {group_titles[group]}", ""])
        for row in frame[frame["claim_group"].eq(group)].itertuples():
            issue = f"({row.issue})" if str(row.issue) else ""
            reference = (
                f"{row.authors} ({row.publication_year}). “{row.title}.” "
                f"*{row.journal}*, {row.volume}{issue}, {row.pages}. "
                f"https://doi.org/{row.doi}"
            )
            sections.extend(
                [
                    f"### `{row.source_id}`",
                    "",
                    f"- Reference: {reference}",
                    f"- Verified publisher page: {row.source_page_url}",
                    f"- Use in this thesis: {row.relevance}",
                    f"- Interpretive boundary: {row.interpretive_boundary}",
                    "",
                ]
            )

    report = [
        "# Methodological literature register",
        "",
        "This register closes the three methodological citation gaps identified in the thesis claim map. Metadata were checked against original publisher pages and DOI records on 2026-09-25. The references support method definitions and limitations; they do not override the project-specific identification gates or turn the descriptive Path C analysis into causal evidence.",
        "",
        f"- Peer-reviewed references: **{len(frame)}**",
        f"- Methodological claim groups covered: **{frame['claim_group'].nunique()} / 3**",
        f"- Unique DOI values: **{frame['doi'].nunique()}**",
        "",
        *sections,
        "## Editorial rule",
        "",
        "Retain the `source_id` values as auditable temporary citation keys. Convert the displayed references to the university's required citation style only at final typesetting, without changing titles, years, journals, pages or DOI values.",
    ]
    (ROOT / "reports" / "47_METHODOLOGICAL_LITERATURE.md").write_text(
        "\n".join(report).rstrip() + "\n", encoding="utf-8"
    )

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "peer_reviewed_references": len(frame),
        "claim_groups_covered": frame["claim_group"].nunique(),
        "expected_claim_groups": len(EXPECTED_GROUPS),
        "unique_dois": frame["doi"].nunique(),
        "missing_required_fields": 0,
        "interpretation": "verified_methodological_bibliography_not_project_specific_identification_evidence",
    }
    (ROOT / "reports" / "thesis_methodological_literature_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
