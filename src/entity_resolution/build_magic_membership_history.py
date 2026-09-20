"""Resolve documented Magic Pass events to candidate resort listings.

The output is an evidence table, not yet a causal treatment panel.  A label
match does not prove destination scope, continuous membership, or municipal
tourism exposure; those limitations are encoded explicitly.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_FILE = ROOT / "metadata" / "magic_pass_entry_evidence.json"
ALIASES_FILE = ROOT / "metadata" / "magic_pass_entity_aliases.json"
RESORT_FILE = ROOT / "data_processed" / "resort_master.csv"
POINT_FILE = ROOT / "data_processed" / "resort_point_municipality.csv"
OUTPUT = ROOT / "data_processed" / "magic_pass_membership_history.csv"
RESOLUTION_OUTPUT = ROOT / "reports" / "magic_pass_entity_resolution.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "magic_pass_evidence_summary.json"


def normalise(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.casefold().replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def stable_event_id(event: dict) -> str:
    identity = "|".join(
        str(event.get(key, ""))
        for key in ("source_id", "source_resort_name", "event_type", "entry_season", "exit_date")
    )
    return "MAGIC_EVENT_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]


def main() -> None:
    events = json.loads(EVIDENCE_FILE.read_text(encoding="utf-8"))
    alias_payload = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
    aliases: dict[str, str] = alias_payload["aliases"]
    resorts = pd.read_csv(RESORT_FILE, dtype="string")
    points = pd.read_csv(POINT_FILE, dtype="string")
    resort_ids = set(resorts["resort_id"].dropna())

    invalid_alias_ids = sorted(set(aliases.values()) - resort_ids)
    if invalid_alias_ids:
        raise ValueError(f"Alias file references unknown resort IDs: {invalid_alias_ids}")

    name_index: defaultdict[str, set[str]] = defaultdict(set)
    for row in resorts.itertuples(index=False):
        for label in (row.resort_name_canonical, row.resort_name_original):
            if pd.notna(label):
                name_index[normalise(label)].add(row.resort_id)

    resolved_rows: list[dict] = []
    for event in events:
        source_label = event["source_resort_name"]
        exact_candidates = sorted(name_index.get(normalise(source_label), set()))
        if source_label in aliases:
            candidate_id = aliases[source_label]
            method = "reviewed_alias"
            status = "candidate_match_scope_pending"
            confidence = "medium"
        elif len(exact_candidates) == 1:
            candidate_id = exact_candidates[0]
            method = "unique_normalised_label"
            status = "candidate_match_scope_pending"
            confidence = "medium"
        elif len(exact_candidates) > 1:
            candidate_id = None
            method = "ambiguous_normalised_label"
            status = "unresolved"
            confidence = "low"
        else:
            candidate_id = None
            method = "no_candidate"
            status = "unresolved"
            confidence = "low"
        resolved_rows.append(
            {
                "event_id": stable_event_id(event),
                **event,
                "candidate_resort_id": candidate_id,
                "entity_resolution_method": method,
                "entity_resolution_status": status,
                "entity_resolution_confidence": confidence,
                "exact_label_candidate_ids": "|".join(exact_candidates),
                "treatment_ready": False,
                "treatment_blocker": (
                    "Destination scope, continuity/exit audit, and municipality exposure are not all approved"
                ),
            }
        )

    history = pd.DataFrame(resolved_rows)
    if history["event_id"].duplicated().any():
        duplicates = history.loc[history["event_id"].duplicated(False), "event_id"].tolist()
        raise ValueError(f"Duplicate stable event IDs: {duplicates}")

    resort_context = resorts[
        ["resort_id", "resort_name_canonical", "cluster_id", "assignment_quality", "identity_status"]
    ].rename(columns={"resort_id": "candidate_resort_id"})
    point_context = points[
        [
            "resort_id",
            "point_municipality_bfs_id",
            "point_municipality_name",
            "bfs_hotel_municipality_name",
            "bfs_hotel_universe",
            "relationship_type",
        ]
    ].rename(columns={"resort_id": "candidate_resort_id"})
    history = history.merge(resort_context, on="candidate_resort_id", how="left", validate="many_to_one")
    history = history.merge(point_context, on="candidate_resort_id", how="left", validate="many_to_one")
    history = history.sort_values(["source_date", "source_resort_name", "event_type"]).reset_index(drop=True)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RESOLUTION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    history.to_csv(OUTPUT, index=False)
    history[
        [
            "event_id",
            "source_id",
            "source_resort_name",
            "event_type",
            "entry_season",
            "candidate_resort_id",
            "resort_name_canonical",
            "cluster_id",
            "entity_resolution_method",
            "entity_resolution_status",
            "entity_resolution_confidence",
            "point_municipality_bfs_id",
            "point_municipality_name",
            "bfs_hotel_municipality_name",
            "bfs_hotel_universe",
            "treatment_ready",
            "treatment_blocker",
        ]
    ].to_csv(RESOLUTION_OUTPUT, index=False)

    candidate = history["candidate_resort_id"].notna()
    hotel_covered = history["bfs_hotel_universe"].fillna("False").astype(str).str.lower().eq("true")
    base_entries = history["event_type"].eq("base_pass_entry")
    summary = {
        "documented_events": int(len(history)),
        "documented_source_labels": int(history["source_resort_name"].nunique()),
        "candidate_resolved_events": int(candidate.sum()),
        "unresolved_events": int((~candidate).sum()),
        "base_pass_entry_events": int(base_entries.sum()),
        "candidate_resolved_base_entry_events": int((candidate & base_entries).sum()),
        "candidate_resolved_events_in_bfs_hotel_universe": int((candidate & hotel_covered).sum()),
        "candidate_resolved_base_entries_in_bfs_hotel_universe": int(
            (candidate & base_entries & hotel_covered).sum()
        ),
        "candidate_resort_listings_with_any_event": int(
            history.loc[candidate, "candidate_resort_id"].nunique()
        ),
        "candidate_clusters_with_any_event": int(history.loc[candidate, "cluster_id"].nunique()),
        "events_by_type": {
            str(key): int(value) for key, value in history["event_type"].value_counts().items()
        },
        "events_by_source": {
            str(key): int(value) for key, value in history["source_id"].value_counts().sort_index().items()
        },
        "treatment_ready_events": 0,
        "causal_readiness": "blocked_pending_scope_continuity_and_exposure_review",
        "known_non_absorbing_case": "Crans-Montana base membership ends 2020-04-30",
        "coverage_gap": (
            "The evidence inventory contains announced entry events, but not a complete season-by-season "
            "membership and exit audit for every destination."
        ),
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
