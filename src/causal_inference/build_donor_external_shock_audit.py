"""Review the beyond-50-km donor shortlist for competing passes and local shocks."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "donor_external_shock_review.json"
INPUT = ROOT / "data_processed" / "donor_shortlist_network_audit.csv"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
EVIDENCE_OUTPUT = ROOT / "reports" / "donor_external_shock_evidence.csv"
FINAL_OUTPUT = ROOT / "data_processed" / "donor_shortlist_final_audit.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "donor_external_shock_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "16_DONOR_EXTERNAL_SHOCK_AUDIT.md"

KEY = ["destination_unit_id", "donor_municipality_bfs_id", "analysis_anchor"]


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().eq("true")


def assert_cached_source(source_id: str) -> None:
    metadata_files = sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"))
    if not metadata_files:
        raise ValueError(f"No checksum-cached evidence for {source_id}")
    metadata = json.loads(metadata_files[-1].read_text(encoding="utf-8"))
    raw_file = ROOT / metadata["raw_file"]
    if not raw_file.exists():
        raise ValueError(f"Missing cached raw evidence for {source_id}: {raw_file}")


def main() -> None:
    pairs = pd.read_csv(INPUT)
    review = pd.DataFrame(json.loads(CONFIG.read_text(encoding="utf-8")))
    if review.duplicated(KEY).any():
        raise ValueError("External-shock review keys must be unique")

    beyond = pairs[pairs["minimum_distance_to_resolved_magic_km"].gt(50)].copy()
    expected = set(map(tuple, beyond[KEY].itertuples(index=False, name=None)))
    reviewed = set(map(tuple, review[KEY].itertuples(index=False, name=None)))
    if expected != reviewed:
        raise ValueError(
            "External-shock review must cover exactly the beyond-50-km pairs; "
            f"missing={sorted(expected - reviewed)}, extra={sorted(reviewed - expected)}"
        )
    for source_ids in review["review_source_ids"]:
        for source_id in str(source_ids).split("|"):
            assert_cached_source(source_id)

    review["historical_magic_nonmembership_status"] = (
        "not_proven_complete_label_and_operator_audit_still_required"
    )
    review["accessibility_review_status"] = "historical_road_rail_change_review_pending"
    review["external_shock_reviewed"] = True
    review["causal_control_approved"] = False
    review.to_csv(EVIDENCE_OUTPUT, index=False)

    merge_columns = [column for column in review.columns if column not in {"donor_resort_name"}]
    final = pairs.drop(columns=["causal_control_approved"], errors="ignore").merge(
        review[merge_columns], on=KEY, how="left", validate="one_to_one"
    )
    within_30 = final["minimum_distance_to_resolved_magic_km"].le(30)
    within_50 = final["minimum_distance_to_resolved_magic_km"].le(50) & ~within_30
    final.loc[within_30, "final_manual_review_decision"] = (
        "deprioritise_network_proximity_within_30km"
    )
    final.loc[within_50, "final_manual_review_decision"] = (
        "deprioritise_network_proximity_30_to_50km"
    )
    final.loc[within_30 | within_50, "external_shock_reviewed"] = False
    final.loc[within_30 | within_50, "historical_magic_nonmembership_status"] = (
        "not_reviewed_after_network_proximity_deprioritisation"
    )
    final.loc[within_30 | within_50, "accessibility_review_status"] = (
        "not_reviewed_after_network_proximity_deprioritisation"
    )
    final["remaining_deep_audit_candidate"] = final[
        "final_manual_review_decision"
    ].eq("retain_for_deeper_manual_audit_competing_pass_risk")
    final["causal_control_approved"] = False
    final.to_csv(FINAL_OUTPUT, index=False)

    decision_counts = final["final_manual_review_decision"].value_counts().to_dict()
    summary = {
        "shortlisted_pairs": int(len(final)),
        "deprioritised_within_30km": int(within_30.sum()),
        "deprioritised_30_to_50km": int(within_50.sum()),
        "beyond_50km_pairs_reviewed": int(len(review)),
        "excluded_contemporaneous_local_tourism_shock": int(
            (review["final_manual_review_decision"] == "exclude_contemporaneous_local_tourism_shock").sum()
        ),
        "remaining_deep_audit_pairs": int(final["remaining_deep_audit_candidate"].sum()),
        "remaining_deep_audit_unique_donors": int(
            final.loc[
                final["remaining_deep_audit_candidate"], "donor_municipality_bfs_id"
            ].nunique()
        ),
        "causal_controls_approved": int(as_bool(final["causal_control_approved"]).sum()),
        "decision_counts": {key: int(value) for key, value in decision_counts.items()},
        "interpretation": (
            "The review narrows manual-audit priorities but does not prove historical "
            "Magic nonmembership, clear competing-pass confounding, or approve controls."
        ),
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    table_rows = []
    for row in review.sort_values(KEY).itertuples(index=False):
        table_rows.append(
            f"| {row.destination_unit_id} | {row.donor_municipality_bfs_id} "
            f"{row.donor_resort_name} | {row.competing_pass_names or '—'} | "
            f"{row.local_tourism_shock_status} | {row.final_manual_review_decision} |"
        )
    report = f"""# Donor competing-pass and local-shock audit

Generated reproducibly by `src/causal_inference/build_donor_external_shock_audit.py` from a versioned manual review whose cited official publications are checksum-cached.

## Result

The network screen left seven pairs beyond 50 km from every resolved Magic Pass point. Official-source review now excludes the two Gonten/Kronberg pairs from priority consideration because independent local tourism investments overlap their treatment anchors. The remaining **{summary['remaining_deep_audit_pairs']} pairs ({summary['remaining_deep_audit_unique_donors']} unique donor municipalities)** remain only deep-audit candidates: all have a documented or strongly indicated competing Grisons pass environment, and none has complete proof of historical Magic nonmembership, accessibility stability, and absence of operator-specific investment.

| Treatment | Donor | Competing pass evidence | Local-shock review | Decision |
|---|---|---|---|---|
{chr(10).join(table_rows)}

## Evidence qualifications

- `regional_pass_environment_documented_operator_participation_not_exactly_proven` is deliberately weaker than exact operator membership. Regional SnowPass activity cannot by itself establish a specific operator's tariff validity.
- The 2022/23 graubündenCARD list names Splügen-Tambo immediately before the May 2023 anchor. The original 2023/24 publication was found in the official search index but returned HTTP 404 during reproducible collection, so anchor-season continuity remains unresolved.
- TopCard access in Upper Engadine around the Saas-Fee anchor is explicitly documented, but the original operator tariff still needs checking.
- Samnaun is a cross-border domain. Austrian demand, access, policy, snow and investment shocks remain outside the current Swiss covariate panel.
- Kronberg's reports show a diversified family/leisure destination with its own capital projects; it is not treated as a clean ski-only comparison municipality.

## Identification decision

This stage prioritises evidence collection; it does not turn any donor into a causal control. Of 35 shortlisted pairs, {summary['deprioritised_within_30km']} are deprioritised within 30 km of the resolved network, {summary['deprioritised_30_to_50km']} are deprioritised at 30–50 km, two are excluded for contemporaneous local tourism shocks, and five await deeper audit. **Approved causal controls: 0.**

Detailed outputs are `{EVIDENCE_OUTPUT.relative_to(ROOT).as_posix()}` and `{FINAL_OUTPUT.relative_to(ROOT).as_posix()}`.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
