"""Build a reproducible point-to-municipality crosswalk.

This module deliberately makes a narrow claim: the municipality is the current
Swiss administrative polygon containing a resort listing's coordinate.  It is
not a catchment area, a tourism-exposure weight, or evidence that the listing is
an independent ski domain.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
QUERY_CONFIG = ROOT / "config" / "municipality_queries.json"
RESORT_MASTER = ROOT / "data_processed" / "resort_master.csv"
HOTEL_PANEL = ROOT / "data_processed" / "hotel_municipality_month.csv"
OUTPUT = ROOT / "data_processed" / "resort_point_municipality.csv"
COVERAGE_OUTPUT = ROOT / "reports" / "resort_point_hotel_coverage.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "municipality_mapping_summary.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalise_name(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = text.casefold().replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def load_bfs_hotel_universe() -> dict[int, str]:
    candidates = sorted(EVIDENCE_DIR.glob("BFS_HOTEL_METADATA_*.json"))
    candidates = [path for path in candidates if not path.name.endswith(".metadata.json")]
    if not candidates:
        raise FileNotFoundError("No cached BFS hotel metadata response was found")
    payload = json.loads(candidates[-1].read_text(encoding="utf-8"))
    dimension = next(item for item in payload["variables"] if item["code"] == "Gemeinde")
    if len(dimension["values"]) != len(dimension["valueTexts"]):
        raise ValueError("BFS municipality codes and labels have different lengths")
    return {int(code): label for code, label in zip(dimension["values"], dimension["valueTexts"])}


def metadata_for(source_id: str) -> tuple[Path, dict]:
    matches = [
        path
        for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"))
        if json.loads(path.read_text(encoding="utf-8")).get("source_id") == source_id
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one metadata file for {source_id}, found {len(matches)}")
    path = matches[0]
    return path, json.loads(path.read_text(encoding="utf-8"))


def select_current_result(payload: dict) -> tuple[dict | None, str, int]:
    current = [
        result.get("attributes", {})
        for result in payload.get("results", [])
        if result.get("attributes", {}).get("is_current_jahr") is True
    ]
    candidates = len(current)
    if not current:
        return None, "outside_swiss_current_municipality_layer", candidates
    if len(current) == 1:
        return current[0], "unique_current_polygon", candidates
    municipal_areas = [row for row in current if row.get("objektart_lookup") == "gemeindegebiet"]
    if len(municipal_areas) == 1:
        return municipal_areas[0], "unique_current_municipal_area_among_multiple", candidates
    return None, "ambiguous_multiple_current_polygons", candidates


def main() -> None:
    queries = json.loads(QUERY_CONFIG.read_text(encoding="utf-8"))
    resorts = pd.read_csv(RESORT_MASTER, dtype={"resort_id": "string"})
    hotel = pd.read_csv(HOTEL_PANEL, usecols=["municipality_name_source"], dtype="string")
    hotel_names = set(hotel["municipality_name_source"].dropna().map(normalise_name))
    bfs_hotels = load_bfs_hotel_universe()

    resort_ids = set(resorts["resort_id"].dropna())
    query_ids = {query["resort_id"] for query in queries}
    if resort_ids != query_ids:
        missing_queries = sorted(resort_ids - query_ids)
        unknown_queries = sorted(query_ids - resort_ids)
        raise ValueError(
            f"Query/resort mismatch; missing_queries={missing_queries}, unknown_queries={unknown_queries}"
        )

    rows: list[dict] = []
    for query in queries:
        source_id = query["source_id"]
        _, metadata = metadata_for(source_id)
        raw_path = ROOT / metadata["raw_file"]
        actual_hash = sha256(raw_path)
        if actual_hash != metadata["sha256"]:
            raise ValueError(f"Checksum mismatch for {raw_path}")
        payload = json.loads(raw_path.read_text(encoding="utf-8"))
        selected, selection_status, candidates = select_current_result(payload)
        attrs = selected or {}
        bfs_id = attrs.get("gde_nr")
        bfs_hotel_name = bfs_hotels.get(int(bfs_id)) if bfs_id is not None else None
        official_name = attrs.get("gemname")
        in_hotel_metadata = bfs_hotel_name is not None
        hotel_name_present = normalise_name(bfs_hotel_name) in hotel_names if bfs_hotel_name else False
        rows.append(
            {
                "resort_id": query["resort_id"],
                "point_longitude": float(query["api_parameters"]["geometry"].split(",")[0]),
                "point_latitude": float(query["api_parameters"]["geometry"].split(",")[1]),
                "point_municipality_bfs_id": bfs_id,
                "point_municipality_name": official_name,
                "point_municipality_canton": attrs.get("kanton"),
                "boundary_reference_year": attrs.get("jahr"),
                "selection_status": selection_status,
                "current_polygon_candidates": candidates,
                "relationship_type": "coordinate_container_only",
                "assignment_method": "geo.admin.ch point identify",
                "assignment_confidence": (
                    "high_for_coordinate_container_only" if selected else "unresolved"
                ),
                "tourism_exposure_interpretation": "not_established",
                "bfs_hotel_universe": in_hotel_metadata,
                "bfs_hotel_municipality_name": bfs_hotel_name,
                "hotel_panel_name_present": hotel_name_present,
                "source_id": "GEOADMIN_MUNICIPALITY_IDENTIFY",
                "query_source_id": source_id,
                "source_sha256": metadata["sha256"],
            }
        )

    crosswalk = pd.DataFrame(rows).sort_values("resort_id").reset_index(drop=True)
    crosswalk["point_municipality_bfs_id"] = crosswalk["point_municipality_bfs_id"].astype("Int64")
    crosswalk["boundary_reference_year"] = crosswalk["boundary_reference_year"].astype("Int64")
    if crosswalk["resort_id"].duplicated().any():
        raise ValueError("A resort_id occurs more than once in the point crosswalk")
    if not (crosswalk["bfs_hotel_universe"] == crosswalk["hotel_panel_name_present"]).all():
        mismatches = crosswalk.loc[
            crosswalk["bfs_hotel_universe"] != crosswalk["hotel_panel_name_present"],
            ["resort_id", "point_municipality_bfs_id", "bfs_hotel_municipality_name"],
        ]
        raise ValueError(f"BFS metadata and processed hotel-name coverage disagree:\n{mismatches}")

    enriched = resorts[
        ["resort_id", "resort_name_canonical", "cluster_id", "assignment_quality", "identity_status"]
    ].merge(crosswalk, on="resort_id", validate="one_to_one")
    coverage = enriched[
        [
            "resort_id",
            "resort_name_canonical",
            "cluster_id",
            "point_municipality_bfs_id",
            "point_municipality_name",
            "point_municipality_canton",
            "selection_status",
            "bfs_hotel_universe",
            "bfs_hotel_municipality_name",
            "assignment_quality",
            "identity_status",
            "relationship_type",
            "tourism_exposure_interpretation",
            "source_id",
        ]
    ].copy()
    coverage["usable_for_descriptive_point_merge"] = (
        coverage["selection_status"].str.startswith("unique_current")
        & coverage["bfs_hotel_universe"]
    )
    coverage["usable_as_causal_exposure_without_review"] = False

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    crosswalk.to_csv(OUTPUT, index=False)
    coverage.to_csv(COVERAGE_OUTPUT, index=False)

    resolved = crosswalk["point_municipality_bfs_id"].notna()
    summary = {
        "resort_listings": int(len(crosswalk)),
        "point_municipality_resolved": int(resolved.sum()),
        "point_municipality_unresolved": int((~resolved).sum()),
        "unique_resolved_municipalities": int(
            crosswalk.loc[resolved, "point_municipality_bfs_id"].nunique()
        ),
        "resort_listings_in_bfs_hotel_universe": int(crosswalk["bfs_hotel_universe"].sum()),
        "unique_bfs_hotel_municipalities_reached": int(
            crosswalk.loc[crosswalk["bfs_hotel_universe"], "point_municipality_bfs_id"].nunique()
        ),
        "descriptive_point_merges_available": int(
            coverage["usable_for_descriptive_point_merge"].sum()
        ),
        "causal_exposure_units_approved": 0,
        "causal_exposure_blocker": (
            "Point containment does not establish which municipality or municipalities receive "
            "tourism exposure from a ski domain; destination-level entity resolution and explicit "
            "weights remain required."
        ),
        "selection_status_counts": {
            str(key): int(value)
            for key, value in crosswalk["selection_status"].value_counts(dropna=False).items()
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
