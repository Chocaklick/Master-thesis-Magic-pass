"""Assemble a clear, style-neutral reading draft from validated thesis outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_VERSION = "path_c_v0_31"


def read_report(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8").strip()


def without_title_and_shift(text: str, levels: int = 1) -> str:
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines.pop(0)
    shifted = []
    for line in lines:
        match = re.match(r"^(#{2,5})(\s+.*)$", line)
        if match:
            hashes = "#" * min(len(match.group(1)) + levels, 6)
            shifted.append(hashes + match.group(2))
        else:
            shifted.append(line)
    return "\n".join(shifted).strip()


def main() -> None:
    final_summary = json.loads(
        (ROOT / "reports" / "final_methodological_report_summary.json").read_text(
            encoding="utf-8"
        )
    )
    chapter_summary = json.loads(
        (ROOT / "reports" / "thesis_chapter_drafts_summary.json").read_text(
            encoding="utf-8"
        )
    )
    citation_summary = json.loads(
        (ROOT / "reports" / "thesis_citation_map_summary.json").read_text(
            encoding="utf-8"
        )
    )
    example_summary = json.loads(
        (
            ROOT
            / "reports"
            / "thesis_candidate_uncertainty_examples_summary.json"
        ).read_text(encoding="utf-8")
    )
    for payload in [final_summary, chapter_summary, citation_summary, example_summary]:
        if payload.get("analysis_version") != ANALYSIS_VERSION:
            raise ValueError("Reading-draft inputs do not share Path C v0.31")
    protected = [
        final_summary["causal_treatments_approved"],
        final_summary["causal_controls_approved"],
        final_summary["recommendations_issued"],
        final_summary["composite_scores"],
        final_summary["causal_interpretation_approvals"],
    ]
    if any(int(value) != 0 for value in protected):
        raise ValueError("Reading draft cannot be built with an approved causal claim")
    if citation_summary["literature_citation_required_claims"] != 0:
        raise ValueError("Reading draft requires closed methodological citation groups")

    executive = without_title_and_shift(read_report("reports/EXECUTIVE_SUMMARY.md"))
    methods = without_title_and_shift(read_report("reports/43_THESIS_METHODS_DRAFT.md"))
    results = without_title_and_shift(read_report("reports/44_THESIS_RESULTS_DRAFT.md"))
    discussion = without_title_and_shift(
        read_report("reports/45_THESIS_DISCUSSION_LIMITATIONS_DRAFT.md")
    )
    examples = without_title_and_shift(
        read_report("reports/48_CANDIDATE_UNCERTAINTY_EXAMPLES.md")
    )
    answers = pd.read_csv(ROOT / "reports" / "final_methodological_question_answers.csv")
    if answers["question_number"].tolist() != list(range(1, 19)):
        raise ValueError("Reading draft requires all 18 final methodological answers")
    answer_rows = "\n".join(
        f"| {int(row.question_number)} | {row.question} | {row.short_answer} |"
        for row in answers.itertuples()
    )

    abstract = (
        "This thesis examines whether Swiss ski-resort, hotel-demand, Magic Pass, snow/climate "
        "and accessibility data can support causal evaluation and strategic decision support for "
        "potential pass expansion. A reproducible pipeline audits 271 directory listings, 242 "
        "preserved lift clusters, 186 hotel municipalities and 14 manually reviewed Magic Pass "
        "destination units. Although seven units have the joint 24-month pre/post coverage used "
        "for diagnostic screening, no treatment or control passes the combined identification "
        "gates. Causal Difference-in-Differences, heterogeneous-effect learners and neural networks "
        "are therefore rejected. The supported fallback is a seven-dimension exploratory dashboard "
        "for 104 apparent candidates. It separates structural similarity, analogue context, snow "
        "vulnerability, tourism context, accessibility, competition/network context and evidence "
        "gaps. The system produces no predicted uplift, composite score or admission ranking. Its "
        "contribution is a transparent Business Analytics architecture that shows what the evidence "
        "can support, where it is fragile and what additional data would be required for stronger "
        "causal or managerial claims."
    )

    draft = f"""# Master thesis working reading draft

> **Status:** Path C v0.31 working manuscript assembled from validated repository outputs. This file is designed for clear review and revision, not final university typesetting. Counts, claim boundaries and source keys are generated; chapter wording may still change.

## Abstract

{abstract}

## How to read this draft

1. The executive summary states the research decision in plain language.
2. Methods, results and discussion are generated from the same validated summaries used by the tests.
3. The 18-question table provides a fast audit against the original project mission; the complete answers are in `reports/49_FINAL_METHODOLOGICAL_REPORT.md`.
4. The candidate examples illustrate uncertainty categories only. Their order is not a ranking.
5. Temporary `source_id` keys and the bibliography worklist remain separate until the final citation style is chosen.

## 1. Executive summary

{executive}

## 2. Methods

{methods}

## 3. Results

{results}

### Visual summary of evidence coverage

![Path C evidence coverage](../figures/path_c_evidence_coverage.png)

### Structural segments

![Path C structural segments](../figures/path_c_structural_segments.png)

### Opportunity and snow dimensions kept separate

![Path C opportunity and snow matrix](../figures/path_c_opportunity_snow_matrix.png)

## 4. Discussion and limitations

{discussion}

## 5. Direct answers to the 18 mission questions

| No. | Question | Short answer |
|---:|---|---|
{answer_rows}

The full evidence-backed answers and internal artifact links are in `reports/49_FINAL_METHODOLOGICAL_REPORT.md` and `reports/final_methodological_question_answers.csv`.

## 6. Illustrative candidate uncertainty cases

{examples}

## 7. Source and citation guide

- `reports/46_THESIS_CITATION_MAP.md` maps 21 central claims to {citation_summary['unique_registered_sources']} registered sources.
- `reports/thesis_source_bibliography_worklist.csv` contains {citation_summary['registered_external_sources']} external official/scientific entries and {citation_summary['internal_lineage_sources']} internal lineage entries.
- `reports/47_METHODOLOGICAL_LITERATURE.md` contains the seven verified peer-reviewed methodological references.
- `metadata/data_sources_master.csv` is the authoritative provenance register; `reports/DATA_SOURCES.md` is its readable rendering.
- Final author-date formatting should wait until the university style is known. Missing author/year metadata must remain missing rather than being guessed.

## 8. Current interpretation and next revision points

The manuscript is sufficiently complete to review the research logic, main empirical counts, methodological rejection and supported Path C contribution. The next revisions should focus on wording, literature positioning and thesis narrative—not additional marginal data collection. Final typesetting later requires the university template and citation style. Any future empirical extension should be added only if it is necessary for a concrete claim and should preserve the current distinctions between listings, clusters, destination units, municipalities and exposure scopes.

### Claims that must remain prohibited

- No causal effect of Magic Pass membership is estimated.
- No candidate receives predicted uplift, recommendation confidence or a composite opportunity score.
- A missing historical pass link does not prove market absence.
- Point-container or radius-based municipalities are not validated tourism catchments.
- Current structural or accessibility fields are not silently relabelled as pre-treatment predictors.
- The four example candidates are not a shortlist, rank or recommendation.
"""
    unresolved_markers = ["TODO", "TBD", "[INSERT", "lorem ipsum"]
    if any(marker.lower() in draft.lower() for marker in unresolved_markers):
        raise ValueError("Reading draft contains an unresolved placeholder")
    output_path = ROOT / "reports" / "50_THESIS_READING_DRAFT.md"
    output_path.write_text(draft.rstrip() + "\n", encoding="utf-8")

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "output": "reports/50_THESIS_READING_DRAFT.md",
        "assembled_sections": 8,
        "mission_questions_included": len(answers),
        "candidate_examples_included": int(example_summary["selected_examples"]),
        "registered_sources_linked": int(citation_summary["unique_registered_sources"]),
        "approximate_word_count": len(re.findall(r"\b\w+\b", draft)),
        "predicted_uplift_values": 0,
        "recommendations_issued": 0,
        "composite_scores": 0,
        "causal_interpretation_approvals": 0,
        "interpretation": "style_neutral_reading_draft_for_review_not_final_typesetting",
    }
    (ROOT / "reports" / "thesis_reading_draft_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
