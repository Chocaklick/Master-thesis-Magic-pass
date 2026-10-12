"""Build a detailed, comment-friendly thesis review draft from validated outputs."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_VERSION = "path_c_v0_31"


REVIEW_PROMPTS = {
    1: "Is the distinction between listings, lift clusters and independent commercial destinations sufficiently clear?",
    2: "Which membership denominator should be emphasised in the final introduction and results chapter?",
    3: "Does the treatment-history explanation make the difference between documented entry and causal exposure clear?",
    4: "Is the pre-treatment coverage threshold sufficiently justified for a feasibility screen?",
    5: "Is the post-treatment coverage discussion clear about observed data versus validated treatment?",
    6: "Does the text explain convincingly why descriptive pre-trends cannot rescue the donor design?",
    7: "Is the rejection of causal interpretation stated strongly enough without overstating data failure?",
    8: "Is the effective treated-sample limitation understandable to a non-specialist reader?",
    9: "Should the final thesis retain a short causal-forest explanation or move it to an appendix?",
    10: "Is the distinction between useful descriptive ML and unsupported supervised prediction sufficiently explicit?",
    11: "Is the neural-network rejection concise and persuasive?",
    12: "Does the structural clustering section clearly delimit what similarity can and cannot establish?",
    13: "Is the seven-dimension Path C architecture presented as a useful final contribution rather than a fallback failure?",
    14: "Which evidence dimensions deserve the most space in the final results narrative?",
    15: "Are the missing variables prioritised appropriately?",
    16: "Which uncertainty source should be highlighted most strongly in the abstract and conclusion?",
    17: "Is the proposed future-data priority realistic for a follow-up study?",
    18: "Does the final classification accurately describe the thesis contribution?",
}


def relative_report_link(raw_path: str) -> str:
    """Return a link target relative to the reports directory."""
    path = raw_path.strip().replace("\\", "/")
    if path.startswith("reports/"):
        return path.removeprefix("reports/")
    return f"../{path}"


def main() -> None:
    reading_path = ROOT / "reports" / "50_THESIS_READING_DRAFT.md"
    answers_path = ROOT / "reports" / "final_methodological_question_answers.csv"
    final_summary_path = ROOT / "reports" / "final_methodological_report_summary.json"
    reading_summary_path = ROOT / "reports" / "thesis_reading_draft_summary.json"

    reading = reading_path.read_text(encoding="utf-8")
    answers = pd.read_csv(answers_path).sort_values("question_number")
    final_summary = json.loads(final_summary_path.read_text(encoding="utf-8"))
    reading_summary = json.loads(reading_summary_path.read_text(encoding="utf-8"))

    if final_summary.get("analysis_version") != ANALYSIS_VERSION:
        raise ValueError("Final methodological report is not Path C v0.31")
    if reading_summary.get("analysis_version") != ANALYSIS_VERSION:
        raise ValueError("Reading draft is not Path C v0.31")
    if answers["question_number"].tolist() != list(range(1, 19)):
        raise ValueError("Detailed review requires all 18 mission questions")
    if len(REVIEW_PROMPTS) != 18:
        raise ValueError("Each mission question requires a review prompt")

    protected = [
        final_summary["causal_treatments_approved"],
        final_summary["causal_controls_approved"],
        final_summary["recommendations_issued"],
        final_summary["composite_scores"],
        final_summary["causal_interpretation_approvals"],
    ]
    if any(int(value) != 0 for value in protected):
        raise ValueError("Detailed review cannot contain an approved causal claim")

    abstract_start = reading.index("## Abstract")
    short_answers_start = reading.index(
        "## 5. Direct answers to the 18 mission questions"
    )
    cases_start = reading.index(
        "## 6. Illustrative candidate uncertainty cases", short_answers_start
    )
    chapters = reading[abstract_start:short_answers_start].strip()
    chapters = chapters.replace(
        "3. The 18-question table provides a fast audit against the original "
        "project mission; the complete answers are in "
        "`reports/49_FINAL_METHODOLOGICAL_REPORT.md`.",
        "3. Section 5 provides the full answers to all 18 questions from the "
        "original project mission, with an evidence trail and a review prompt.",
    )
    closing_sections = reading[cases_start:].strip()

    expanded_answers = []
    for row in answers.itertuples(index=False):
        evidence_items = []
        for evidence_path in str(row.evidence).split("|"):
            evidence_path = evidence_path.strip()
            target = relative_report_link(evidence_path)
            evidence_items.append(f"[`{evidence_path}`]({target})")
        evidence = ", ".join(evidence_items)
        expanded_answers.append(
            f"""### 5.{int(row.question_number)}. {row.question}

**Short answer.** {row.short_answer}

{row.answer}

**Evidence trail.** {evidence}

**Point for review.** {REVIEW_PROMPTS[int(row.question_number)]}

**Your comment:**
""".rstrip()
        )

    review_topics = [
        (
            "Research positioning",
            "Does the thesis make a convincing contribution even though the causal and predictive gates failed?",
        ),
        (
            "Entity definitions",
            "Are listing, cluster, destination unit and municipality distinctions understandable throughout?",
        ),
        (
            "Causal feasibility",
            "Is the zero-treatment/zero-control conclusion sufficiently documented and proportionate?",
        ),
        (
            "Path C contribution",
            "Is the seven-dimension evidence dashboard useful and clearly separated from a ranking system?",
        ),
        (
            "Accessibility",
            "Should the distance-versus-public-transport result receive more emphasis in the final thesis?",
        ),
        (
            "Climate and snow",
            "Is the station-to-resort representativeness limitation explained at the right level of detail?",
        ),
        (
            "Candidate examples",
            "Do the four cases illustrate uncertainty without appearing to recommend specific stations?",
        ),
        (
            "Final writing",
            "Which sections are too technical, repetitive or insufficiently developed?",
        ),
    ]
    review_rows = "\n".join(
        f"| {topic} | {question} |  |" for topic, question in review_topics
    )

    draft = f"""# Detailed thesis review draft

> **Status:** Path C v0.31 detailed content-review document. It assembles validated results and full methodological answers for substantive feedback. It is not final UNIL typesetting and it does not authorise causal, predictive-uplift, profitability or ranking claims.

## Review guide

This document is deliberately more detailed than `reports/50_THESIS_READING_DRAFT.md`. The shorter manuscript remains the compact reading version; this version expands all 18 mission questions, links each answer to its evidence and provides explicit places for comments. Comments can be typed directly after any **Your comment:** label or collected in the final review sheet.

The most important judgments for the reviewer are:

1. whether the entity and denominator distinctions are understandable;
2. whether the rejection of causal and predictive modelling is convincing;
3. whether Path C is framed as a defensible analytical contribution;
4. whether the balance between technical detail and readability is appropriate;
5. which results and figures should receive more emphasis in the final manuscript.

{chapters}

## 5. Detailed answers to the 18 mission questions

The following answers reproduce the validated methodological conclusions in full. The evidence trail identifies the internal report or processed artifact supporting each answer. These links document project lineage; they are not substitutes for the final academic bibliography.

{chr(10).join(chr(10) + item for item in expanded_answers)}

{closing_sections}

## 9. Supporting audit figure

### Existing cluster-assignment flags

This early audit figure belongs to the data-validation stage rather than the final Path C results. It is included here so that all four existing project figures can be reviewed from one document. It does not certify the preserved lift clusters as independent commercial destinations.

![Existing assignment flags](../figures/existing_assignment_flags.png)

## 10. Reviewer comment sheet

| Topic | Question for the reviewer | Comment |
|---|---|---|
{review_rows}

### Overall decision

- **Sections that are already clear:**
- **Sections requiring rewriting:**
- **Results or figures to add:**
- **Claims that appear too strong:**
- **Material that could move to an appendix:**
- **Other comments:**
"""

    unresolved_markers = ["TODO", "TBD", "[INSERT", "lorem ipsum"]
    if any(marker.lower() in draft.lower() for marker in unresolved_markers):
        raise ValueError("Detailed review draft contains an unresolved placeholder")
    question_comment_fields = draft.count("\n**Your comment:**\n")
    if question_comment_fields != 18:
        raise ValueError("Detailed review draft must expose 18 question comment fields")
    if draft.count("![") != 4:
        raise ValueError("Detailed review draft must include all four existing figures")

    output_path = ROOT / "reports" / "51_THESIS_DETAILED_REVIEW_DRAFT.md"
    output_path.write_text(draft.rstrip() + "\n", encoding="utf-8")

    summary = {
        "analysis_version": ANALYSIS_VERSION,
        "output": "reports/51_THESIS_DETAILED_REVIEW_DRAFT.md",
        "mission_questions_expanded": len(answers),
        "question_comment_fields": question_comment_fields,
        "review_sheet_topics": len(review_topics),
        "figures_included": draft.count("!["),
        "approximate_word_count": len(re.findall(r"\b\w+\b", draft)),
        "predicted_uplift_values": 0,
        "recommendations_issued": 0,
        "composite_scores": 0,
        "causal_interpretation_approvals": 0,
        "interpretation": "detailed_comment_friendly_review_draft_not_final_typesetting",
    }
    (ROOT / "reports" / "thesis_detailed_review_draft_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
