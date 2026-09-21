"""Classify unmatched entry labels and preserve non-equivalent scope relations.

This table supplies conservative donor exclusions, never a treatment mapping.
The original historical event table and one-to-one aliases are unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    config = json.loads((ROOT / "config/unmatched_magic_scope_review.json").read_text(encoding="utf-8"))
    history = pd.read_csv(ROOT / "data_processed/magic_pass_membership_history.csv", dtype="string")
    points = pd.read_csv(ROOT / "data_processed/resort_point_municipality.csv", dtype="string").set_index("resort_id")
    unmatched = history[history.event_type.eq("base_pass_entry") & history.candidate_resort_id.isna()]
    reviews = {}
    for group in config["groups"]:
        for label in group["labels"]:
            if label in reviews:
                raise ValueError(f"Duplicate review label: {label}")
            reviews[label] = group
        unknown = set(group["related_resort_ids"]) - set(points.index)
        if unknown:
            raise ValueError(f"Unknown scope candidates: {unknown}")
    if set(unmatched.source_resort_name) != set(reviews):
        raise ValueError("Unmatched event set changed; explicitly review added/removed labels")

    review_rows, relation_rows = [], []
    for event in unmatched.itertuples(index=False):
        group = reviews[event.source_resort_name]
        common = {
            "event_id": event.event_id,
            "source_resort_name": event.source_resort_name,
            "entry_season": event.entry_season,
            "event_source_id": event.source_id,
            "event_source_page": event.source_page,
            "review_date": config["review_date"],
            "review_class": group["review_class"],
            "source_ids": "|".join(group["source_ids"]),
            "source_locators": group["source_locators"],
            "review_note": group["note"],
            "identity_equivalence_approved": False,
            "causal_mapping_approved": False,
        }
        review_rows.append({**common, "related_resort_ids": "|".join(group["related_resort_ids"]),
                            "related_listing_count": len(group["related_resort_ids"])})
        for resort_id in group["related_resort_ids"]:
            point = points.loc[resort_id]
            relation_rows.append({**common, "related_resort_id": resort_id,
                "point_municipality_bfs_id": point.point_municipality_bfs_id,
                "point_municipality_name": point.point_municipality_name,
                "bfs_hotel_universe": point.bfs_hotel_universe,
                "exclude_from_clean_donor_pool": True,
                "exclusion_basis": "precautionary_scope_relation_not_causal_exposure"})
    review = pd.DataFrame(review_rows).sort_values("source_resort_name")
    relations = pd.DataFrame(relation_rows).sort_values(["event_id", "related_resort_id"])
    review.to_csv(ROOT / "reports/unmatched_magic_entry_review.csv", index=False)
    relations.to_csv(ROOT / "data_processed/magic_pass_scope_relations.csv", index=False)
    summary = {"reviewed_unmatched_base_entries": len(review),
        "review_class_counts": review.review_class.value_counts().to_dict(),
        "scope_relation_rows": len(relations),
        "related_resort_listings": int(relations.related_resort_id.nunique()),
        "identity_equivalences_approved": 0, "causal_mappings_approved": 0}
    (ROOT / "reports/unmatched_magic_scope_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
