"""Audit season-by-season Magic Pass continuity for reviewed destination units.

Positive evidence is recorded from entry events, full official rosters, named
continuation statements, and documented exits.  Missing seasons stay
unverified; they are never filled by an absorbing-treatment assumption.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
UNIT_CONFIG = ROOT / "config" / "treatment_destination_review.json"
ROSTER_CONFIG = ROOT / "metadata" / "magic_pass_roster_evidence.json"
HISTORY = ROOT / "data_processed" / "magic_pass_membership_history.csv"
UNIT_TABLE = ROOT / "data_processed" / "treatment_destination_units.csv"
STATUS_OUT = ROOT / "data_processed" / "magic_pass_membership_status_by_season.csv"
AUDIT_OUT = ROOT / "reports" / "membership_continuity_audit.csv"
SUMMARY_OUT = ROOT / "reports" / "membership_continuity_summary.json"

SEASONS = [f"{year}/{year + 1}" for year in range(2017, 2026)]


def main() -> None:
    units = json.loads(UNIT_CONFIG.read_text(encoding="utf-8"))["units"]
    roster = json.loads(ROSTER_CONFIG.read_text(encoding="utf-8"))["observations"]
    history = pd.read_csv(HISTORY, dtype="string", keep_default_na=False)
    unit_table = pd.read_csv(UNIT_TABLE)
    unit_ids = {unit["destination_unit_id"] for unit in units}

    evidence: dict[tuple[str, str], list[dict]] = {}
    entries = history[history["event_type"].eq("base_pass_entry")]
    for unit in units:
        for resort_id, label in zip(
            unit["component_resort_ids"], unit["entry_labels"], strict=True
        ):
            matches = entries[
                entries["candidate_resort_id"].eq(resort_id)
                & entries["source_resort_name"].eq(label)
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one entry event for {unit['destination_unit_id']} / {label}"
                )
            row = matches.iloc[0]
            evidence.setdefault(
                (unit["destination_unit_id"], row["entry_season"]), []
            ).append(
                {
                    "source_id": row["source_id"],
                    "source_page": row["source_page"],
                    "evidence_type": "documented_entry",
                    "note": f"Entry evidence for {label}",
                }
            )

    for observation in roster:
        unknown = set(observation["active_destination_unit_ids"]) - unit_ids
        if unknown:
            raise ValueError(f"Unknown roster destination units: {sorted(unknown)}")
        for destination_unit_id in observation["active_destination_unit_ids"]:
            evidence.setdefault((destination_unit_id, observation["season"]), []).append(
                {
                    "source_id": observation["source_id"],
                    "source_page": observation["source_page"],
                    "evidence_type": observation["evidence_type"],
                    "note": observation["note"],
                }
            )

    exits = history[history["event_type"].eq("base_pass_exit")]
    for unit in units:
        if not unit["exit_date"]:
            continue
        matches = exits[
            exits["candidate_resort_id"].isin(unit["component_resort_ids"])
            & exits["exit_date"].eq(unit["exit_date"])
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one exit event for {unit['destination_unit_id']}")
        row = matches.iloc[0]
        exit_year = pd.Timestamp(unit["exit_date"]).year
        last_active_season = f"{exit_year - 1}/{exit_year}"
        evidence.setdefault((unit["destination_unit_id"], last_active_season), []).append(
            {
                "source_id": row["source_id"],
                "source_page": row["source_page"],
                "evidence_type": "documented_exit_last_active_season",
                "note": f"Documented last active day {unit['exit_date']}",
            }
        )

    rows: list[dict] = []
    for unit in units:
        first_year = int(unit["entry_season"].split("/")[0])
        exit_year = (
            pd.Timestamp(unit["exit_date"]).year - 1 if unit["exit_date"] else None
        )
        for season in SEASONS:
            season_year = int(season.split("/")[0])
            records = evidence.get((unit["destination_unit_id"], season), [])
            if season_year < first_year:
                status = "not_yet_entered"
            elif exit_year is not None and season_year > exit_year:
                status = "documented_inactive_after_exit"
            elif records:
                status = "documented_active"
            else:
                status = "unverified_active_continuity"
            rows.append(
                {
                    "destination_unit_id": unit["destination_unit_id"],
                    "destination_name": unit["destination_name"],
                    "season": season,
                    "membership_status": status,
                    "documented_active": status == "documented_active",
                    "evidence_types": "|".join(
                        sorted({record["evidence_type"] for record in records})
                    ),
                    "source_ids": "|".join(
                        sorted({record["source_id"] for record in records})
                    ),
                    "source_pages": "|".join(
                        sorted({record["source_page"] for record in records})
                    ),
                    "evidence_notes": " | ".join(record["note"] for record in records),
                    "outcome_panel_eligible": unit[
                        "eligible_for_reviewed_outcome_panel"
                    ],
                    "causal_treatment_status_approved": False,
                }
            )
    status = pd.DataFrame(rows).sort_values(["destination_unit_id", "season"])
    status.to_csv(STATUS_OUT, index=False)

    audit_rows: list[dict] = []
    for unit in units:
        group = status[status["destination_unit_id"].eq(unit["destination_unit_id"])]
        active_window = group[
            ~group["membership_status"].isin(
                ["not_yet_entered", "documented_inactive_after_exit"]
            )
        ]
        documented = active_window["documented_active"]
        missing = active_window.loc[
            ~documented, "season"
        ].tolist()
        audit_rows.append(
            {
                "destination_unit_id": unit["destination_unit_id"],
                "destination_name": unit["destination_name"],
                "first_entry_season": unit["entry_season"],
                "documented_exit_date": unit["exit_date"] or "",
                "active_seasons_requiring_evidence": len(active_window),
                "active_seasons_documented": int(documented.sum()),
                "active_seasons_unverified": int((~documented).sum()),
                "unverified_seasons": "|".join(missing),
                "continuity_fully_documented": not missing,
                "outcome_panel_eligible": unit[
                    "eligible_for_reviewed_outcome_panel"
                ],
                "causal_treatment_status_approved": False,
            }
        )
    audit = pd.DataFrame(audit_rows).sort_values("destination_unit_id")
    audit.to_csv(AUDIT_OUT, index=False)

    eligible = audit["outcome_panel_eligible"].astype(bool)
    complete = audit["continuity_fully_documented"].astype(bool)
    summary = {
        "reviewed_destination_units": int(len(audit)),
        "destination_units_with_fully_documented_active_seasons": int(complete.sum()),
        "outcome_panel_units_with_fully_documented_active_seasons": int(
            (eligible & complete).sum()
        ),
        "outcome_panel_units_with_continuity_gaps": int((eligible & ~complete).sum()),
        "unverified_active_unit_seasons": int(
            status["membership_status"].eq("unverified_active_continuity").sum()
        ),
        "fully_documented_panel_units_with_24_pre_and_post_months": int(
            audit[["destination_unit_id", "continuity_fully_documented"]]
            .merge(
                unit_table[
                    [
                        "destination_unit_id",
                        "eligible_for_reviewed_outcome_panel",
                        "has_24_observed_pre_months",
                        "has_24_active_post_months_assumption",
                    ]
                ],
                on="destination_unit_id",
                validate="one_to_one",
            )
            .eval(
                "continuity_fully_documented and eligible_for_reviewed_outcome_panel "
                "and has_24_observed_pre_months and has_24_active_post_months_assumption"
            )
            .sum()
        ),
        "causal_treatment_units_approved": 0,
        "interpretation": (
            "Only explicit positive evidence is coded active. Missing annual evidence "
            "remains unverified and is not converted to non-membership."
        ),
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
