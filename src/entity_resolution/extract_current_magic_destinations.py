"""Extract the official current Magic Pass destination list from cached HTML."""

from __future__ import annotations

import hashlib
import html
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
ALIASES_FILE = ROOT / "metadata" / "magic_pass_entity_aliases.json"
RESORT_FILE = ROOT / "data_processed" / "resort_master.csv"
OUTPUT = ROOT / "data_processed" / "magic_pass_current_destinations.csv"
REVIEW_OUTPUT = ROOT / "reports" / "current_magic_pass_entity_resolution.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "current_magic_pass_summary.json"


def normalise(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = html.unescape(text).casefold().replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def main() -> None:
    metadata_files = sorted(EVIDENCE_DIR.glob("MAGIC_CURRENT_MAP_*.metadata.json"))
    if len(metadata_files) != 1:
        raise ValueError(f"Expected one cached current-map snapshot, found {len(metadata_files)}")
    metadata = json.loads(metadata_files[0].read_text(encoding="utf-8"))
    raw_path = ROOT / metadata["raw_file"]
    raw_bytes = raw_path.read_bytes()
    if hashlib.sha256(raw_bytes).hexdigest() != metadata["sha256"]:
        raise ValueError("Current Magic Pass map checksum does not match its metadata")
    page = raw_bytes.decode("utf-8")
    match = re.search(r'<bd-map-all\b[^>]*:resorts="([^"]+)"', page, flags=re.DOTALL)
    if not match:
        raise ValueError("Could not locate the embedded resort list in the official map HTML")
    official = json.loads(html.unescape(match.group(1)))

    resorts = pd.read_csv(RESORT_FILE, dtype="string")
    aliases = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))["aliases"]
    resort_ids = set(resorts["resort_id"].dropna())
    name_index: defaultdict[str, set[str]] = defaultdict(set)
    for row in resorts.itertuples(index=False):
        for label in (row.resort_name_canonical, row.resort_name_original):
            if pd.notna(label):
                name_index[normalise(label)].add(row.resort_id)

    rows: list[dict] = []
    for destination in official:
        title = html.unescape(destination["title"])
        exact = sorted(name_index.get(normalise(title), set()))
        if title in aliases:
            candidate = aliases[title]
            method = "reviewed_alias"
        elif len(exact) == 1:
            candidate = exact[0]
            method = "unique_normalised_label"
        elif len(exact) > 1:
            candidate = None
            method = "ambiguous_normalised_label"
        else:
            candidate = None
            method = "no_candidate"
        if candidate is not None and candidate not in resort_ids:
            raise ValueError(f"Unknown candidate resort ID {candidate!r} for {title!r}")
        coordinates = destination.get("realCoords") or []
        rows.append(
            {
                "official_destination_id": destination["idContent"],
                "official_destination_name": title,
                "official_destination_path": destination.get("href_url"),
                "official_regions": "|".join(
                    str(region.get("name", "")) for region in destination.get("states", [])
                ),
                "official_region_codes": "|".join(
                    str(region.get("shortname", "")) for region in destination.get("states", [])
                ),
                "official_coordinate_count": len(coordinates),
                "official_latitude_first": coordinates[0][0] if coordinates else None,
                "official_longitude_first": coordinates[0][1] if coordinates else None,
                "candidate_resort_id": candidate,
                "entity_resolution_method": method,
                "entity_resolution_status": (
                    "candidate_match_scope_pending" if candidate else "unresolved"
                ),
                "current_member_snapshot": True,
                "snapshot_retrieval_date": metadata["retrieval_date"],
                "source_id": "MAGIC_CURRENT_MAP",
                "source_url": metadata["url"],
                "source_sha256": metadata["sha256"],
            }
        )
    current = pd.DataFrame(rows).sort_values("official_destination_name").reset_index(drop=True)
    if current["official_destination_id"].duplicated().any():
        raise ValueError("Official destination IDs are not unique in the cached page")
    if current["official_destination_name"].duplicated().any():
        raise ValueError("Official destination names are not unique in the cached page")

    context = resorts[["resort_id", "resort_name_canonical", "cluster_id"]].rename(
        columns={"resort_id": "candidate_resort_id"}
    )
    review = current.merge(context, on="candidate_resort_id", how="left", validate="many_to_one")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    current.to_csv(OUTPUT, index=False)
    review.to_csv(REVIEW_OUTPUT, index=False)

    candidate = current["candidate_resort_id"].notna()
    summary = {
        "snapshot_retrieval_date": metadata["retrieval_date"],
        "official_current_destinations": int(len(current)),
        "candidate_resolved_destinations": int(candidate.sum()),
        "unresolved_destinations": int((~candidate).sum()),
        "candidate_resort_listings": int(current.loc[candidate, "candidate_resort_id"].nunique()),
        "scope_note": (
            "The official map is a current-state snapshot, not evidence of historical entry dates. "
            "Candidate matches remain subject to destination-scope review."
        ),
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
