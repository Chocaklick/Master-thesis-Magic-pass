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
    for source_id in review["magic_roster_source_id"]:
        assert_cached_source(str(source_id))

    required_review_fields = [
        "magic_roster_source_page",
        "donor_roster_labels_checked",
        "historical_magic_nonmembership_status",
        "accessibility_review_status",
    ]
    for column in required_review_fields:
        if review[column].fillna("").astype(str).str.strip().eq("").any():
            raise ValueError(f"External-shock review field must be populated: {column}")
    review["historical_magic_roster_absence_documented"] = review[
        "historical_magic_nonmembership_status"
    ].eq(
        "documented_absent_from_complete_anchor_season_official_roster_under_reviewed_station_labels"
    )
    if not review["historical_magic_roster_absence_documented"].all():
        raise ValueError("Every remote donor must have documented complete-roster label absence")
    review["accessibility_review_completed_or_moot"] = ~review[
        "accessibility_review_status"
    ].str.contains("pending", case=False, na=True)
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
    final.loc[within_30 | within_50, "historical_magic_roster_absence_documented"] = False
    final.loc[within_30 | within_50, "accessibility_review_status"] = (
        "not_reviewed_after_network_proximity_deprioritisation"
    )
    final.loc[within_30 | within_50, "accessibility_review_completed_or_moot"] = False
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
        "historical_magic_roster_absence_documented": int(
            review["historical_magic_roster_absence_documented"].sum()
        ),
        "accessibility_review_completed_or_moot": int(
            review["accessibility_review_completed_or_moot"].sum()
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
            "Complete annual Magic Pass rosters document station-label absence for all "
            "seven remote pairs, but official operator evidence also documents a "
            "contemporaneous donor-specific shock for every pair. No control is approved."
        ),
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    table_rows = []
    for row in review.sort_values(KEY).itertuples(index=False):
        competing_passes = str(row.competing_pass_names).replace("|", " / ")
        table_rows.append(
            f"| {row.destination_unit_id} | {row.donor_municipality_bfs_id} "
            f"{row.donor_resort_name} | {row.magic_roster_source_id} "
            f"p. {row.magic_roster_source_page} | {competing_passes or '—'} | "
            f"{row.local_tourism_shock_status} | {row.final_manual_review_decision} |"
        )
    report = f"""# Donor competing-pass and local-shock audit

Generated reproducibly by `src/causal_inference/build_donor_external_shock_audit.py` from a versioned manual review whose cited official publications are checksum-cached.

## Result

The network screen left seven pairs beyond 50 km from every resolved Magic Pass point. The complete official annual rosters document that each donor station label (including the reviewed spelling and place variants) was absent from Magic Pass at the relevant anchor season. That resolves the principal historical-membership question raised for these candidates.

The same official-source review finds a donor-specific tourism or infrastructure shock overlapping every treatment post window. Consequently **all seven remote pairs are excluded from priority consideration and zero deep-audit candidates remain**. Historical Magic nonmembership is necessary for a donor, but it is not sufficient when the donor itself changes materially.

| Treatment | Donor | Complete Magic roster checked | Competing pass evidence | Local-shock review | Decision |
|---|---|---|---|---|---|
{chr(10).join(table_rows)}

## Evidence qualifications

- Roster absence is a direct statement about the checked station/place labels in a complete annual publication. It is not reinterpreted as corporate-register proof that no hidden affiliate arrangement existed.
- Exact operator participation in SnowPass or TopCard remains weaker than the roster evidence where only a regional publication was available. The exclusion decisions do not depend on resolving that remaining tariff detail because the local-shock evidence is independently sufficient.
- Corviglia/Celerina has contemporaneous restaurant, pricing, lift, piste and investment changes; Splügen has snowmaking, children-lift, management and demand changes; Minschuns has a publicly financed access/snowmaking project trajectory; Samnaun replaced the Visnitz chairlift in 2019; and Kronberg has its own capital projects.
- The Minschuns source documents approval and intended access replacement, not completed construction. The exclusion is therefore based on the financing/anticipation trajectory within the post window, not on an invented commissioning date.
- Samnaun remains a cross-border domain. Austrian demand, access, policy and tourism shocks lie outside the current Swiss covariate panel and reinforce, but are not required for, its exclusion.

## Identification decision

Of 35 shortlisted pairs, {summary['deprioritised_within_30km']} are deprioritised within 30 km of the resolved network, {summary['deprioritised_30_to_50km']} are deprioritised at 30–50 km, and all seven remote pairs are excluded for contemporaneous donor-specific tourism or infrastructure shocks. The pre-trend shortlist therefore contains **no surviving control candidate and no approved causal control**.

Detailed outputs are `{EVIDENCE_OUTPUT.relative_to(ROOT).as_posix()}` and `{FINAL_OUTPUT.relative_to(ROOT).as_posix()}`.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
