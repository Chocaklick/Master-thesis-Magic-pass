"""Extend official-address evidence using exact matches only, without centroids.

--prepare builds requests from archived, BFS-keyed official Bern contacts.
--review admits one exact street/number/postcode/BFS result; others stay pending.
No first-result/fuzzy selection, no change to analytical inclusion or thresholds.
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.inspect_official_road_directory import bern_contacts
from src.data_processing.prepare_accessibility_road_reference import archived_metadata

SOURCES = "config/accessibility_road_endpoint_sources.json"
REVIEW = "config/accessibility_road_endpoint_evidence_review.json"
CANDIDATES = "data_interim/accessibility_road_directory/origin_candidates.json"
PENDING = "reports/accessibility_road_origin_geocoding_audit.csv"


def normalize(value):
    value = str(value).lower().replace("’", "'")
    # SearchServer's German spelling is ae/oe/ue, not a/o/u. This is
    # transliteration only; never approximate a different street or number.
    value = value.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(value.split())


def exact_candidates(response, candidate):
    street = normalize(candidate["street"])
    prefix = street + " " + str(candidate["postcode"]) + " "
    bfs = str(candidate["municipality_bfs_id"])
    found = []
    for entry in response.get("results", []):
        attrs = entry.get("attrs", {})
        detail = normalize(attrs.get("detail", ""))
        if (attrs.get("origin") == "address" and detail.startswith(prefix)
                and re.search(r"\s" + bfs + r"\s[^\d]+\sch\s[a-z]{2}$", detail)):
            found.append(attrs)
    return found


def prepare():
    sources = json.loads((ROOT / SOURCES).read_text(encoding="utf-8"))
    review = json.loads((ROOT / REVIEW).read_text(encoding="utf-8"))
    known = {r["municipality_bfs_id"] for r in review["origins"]}
    origins = pd.read_csv(ROOT / "reports/accessibility_road_origin_review.csv")
    contacts = bern_contacts()
    if contacts.bfsnr.duplicated().any():
        raise ValueError("Official source contains duplicate municipal IDs")
    primary_sid = "BERN_OFFICIAL_MUNICIPAL_CONTACTS_GPKG_2026"
    discovery = json.loads((ROOT / "config/accessibility_road_bulk_discovery_sources.json").read_text())
    primary_spec = next(s for s in discovery if s["source_id"] == primary_sid)
    by_id = {s["source_id"]: s for s in sources}
    by_id[primary_sid] = primary_spec
    candidate_path = ROOT / CANDIDATES
    candidates = json.loads(candidate_path.read_text(encoding="utf-8")) if candidate_path.exists() else []
    candidate_ids = {c["municipality_bfs_id"] for c in candidates}
    for r in contacts[contacts.bfsnr.isin(origins.municipality_bfs_id)].itertuples(index=False):
        bfs = int(r.bfsnr)
        if bfs in known or bfs in candidate_ids:
            continue
        street = str(r.strname)
        if "/" in street:
            # Bilingual street spelling, not two buildings: retain both source
            # spellings, query first exact spelling; identity still BFS keyed.
            street = street.split("/")[0].strip()
        postcode = int(r.plz)
        sid = f"ROAD_ORIGIN_BFS_{bfs}_GEOADMIN_2026"
        params = dict(searchText=f"{street} {postcode} {r.ort}", type="locations", origins="address", sr=4326)
        url = "https://api3.geo.admin.ch/rest/services/api/SearchServer?" + urlencode(params)
        by_id[sid] = dict(source_id=sid, url=url, suffix="json", organisation="swisstopo / geo.admin.ch",
            description=f"Official administrative address geocoding for BFS {bfs}; all candidates retained; exact street/number/postcode/BFS required")
        candidates.append(dict(municipality_bfs_id=bfs, municipality_name=str(r.gemname),
            street=street, source_street=str(r.strname), postcode=postcode, locality=str(r.ort),
            address=f"{r.strname}, {postcode} {r.ort}", address_source_id=primary_sid,
            address_locator=f"GPKG GDEDAT row bfsnr={bfs}; verwalt={r.verwalt}; strname/plz/ort; polygon geometry excluded",
            coordinate_source_id=sid))
    supplemental = json.loads((ROOT / "config/accessibility_road_origin_address_review.json").read_text(encoding="utf-8"))
    for candidate in supplemental:
        if candidate["municipality_bfs_id"] in known or candidate["municipality_bfs_id"] in candidate_ids:
            continue
        metadata = archived_metadata(candidate["address_source_id"])
        text = BeautifulSoup((ROOT / metadata["raw_file"]).read_bytes(), "html.parser", from_encoding="utf-8").get_text(" ", strip=True).replace("\u200b", "")
        if normalize(candidate["street"]) not in normalize(text):
            raise ValueError("Reviewed street missing from archived official contact source")
        sid = f"ROAD_ORIGIN_BFS_{candidate['municipality_bfs_id']}_GEOADMIN_2026"
        params = dict(searchText=f"{candidate['street']} {candidate['postcode']} {candidate['locality']}", type="locations", origins="address", sr=4326)
        by_id[sid] = dict(source_id=sid, url="https://api3.geo.admin.ch/rest/services/api/SearchServer?" + urlencode(params),
            suffix="json", organisation="swisstopo / geo.admin.ch", description=f"Exact official administrative address candidates, BFS {candidate['municipality_bfs_id']}; no fuzzy or first-result assignment")
        by_id[candidate["address_source_id"]] = next(s for s in discovery if s["source_id"] == candidate["address_source_id"])
        candidates.append(dict(candidate, source_street=candidate["street"], address=f"{candidate['street']}, {candidate['postcode']} {candidate['locality']}", coordinate_source_id=sid))
    (ROOT / CANDIDATES).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / CANDIDATES).write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / SOURCES).write_text(json.dumps(list(by_id.values()), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"new_official_address_queries": len(candidates)}))


def review_candidates():
    review = json.loads((ROOT / REVIEW).read_text(encoding="utf-8"))
    candidates = json.loads((ROOT / CANDIDATES).read_text(encoding="utf-8"))
    by_id = {r["municipality_bfs_id"]: r for r in review["origins"]}
    rows = []
    for candidate in candidates:
        archived_metadata(candidate["address_source_id"])
        metadata = archived_metadata(candidate["coordinate_source_id"])
        response = json.loads((ROOT / metadata["raw_file"]).read_text(encoding="utf-8"))
        exact = exact_candidates(response, candidate)
        verified = len(exact) == 1
        evidence = dict(municipality_bfs_id=candidate["municipality_bfs_id"], address=candidate["address"],
            address_source_id=candidate["address_source_id"], address_locator=candidate["address_locator"],
            coordinate_source_id=candidate["coordinate_source_id"], coordinates_verified=verified)
        if verified:
            evidence.update(reviewed_feature_id=exact[0]["featureId"], expected_detail=exact[0]["detail"],
                coordinate_locator="Unique exact normalized official street/number/postcode and explicit BFS match, no fuzzy or first-result selection; complete candidates and SHA retained")
        if candidate["municipality_bfs_id"] not in by_id or not by_id[candidate["municipality_bfs_id"]]["coordinates_verified"]:
            by_id[candidate["municipality_bfs_id"]] = evidence
        rows.append(dict(municipality_bfs_id=candidate["municipality_bfs_id"],
            address_source_id=candidate["address_source_id"], coordinate_source_id=candidate["coordinate_source_id"],
            source_address=candidate["address"], exact_candidate_count=len(exact),
            status="exact_address_coordinate_verified" if verified else "address_verified_coordinate_match_needs_review",
            all_candidate_details=json.dumps([r.get("attrs", {}).get("detail") for r in response.get("results", [])], ensure_ascii=False)))
    review["origins"] = sorted(by_id.values(), key=lambda r: r["municipality_bfs_id"])
    review["review_date"] = "2026-10-07"
    (ROOT / REVIEW).write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows).to_csv(ROOT / PENDING, index=False, lineterminator="\n")
    print(json.dumps({"official_addresses": len(rows), "unique_exact_coordinates": sum(r["exact_candidate_count"] == 1 for r in rows), "pending_exact_match": sum(r["exact_candidate_count"] != 1 for r in rows)}))


def fribourg_points():
    sid = "FR_OFFICIAL_MAIN_MUNICIPAL_BUILDINGS_POINTS_2026"
    metadata = archived_metadata(sid)
    response = json.loads((ROOT / metadata["raw_file"]).read_text(encoding="utf-8"))
    if response.get("geometryType") != "esriGeometryPoint" or response.get("spatialReference", {}).get("wkid") != 4326:
        raise ValueError("Expected official main-administration WGS84 points")
    origins = pd.read_csv(ROOT / "reports/accessibility_road_origin_review.csv")
    review = json.loads((ROOT / REVIEW).read_text(encoding="utf-8"))
    by_id = {r["municipality_bfs_id"]: r for r in review["origins"]}
    ids = [r["attributes"]["FOSNR"] for r in response["features"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Multiple main-building points for a municipality require review")
    for feature in response["features"]:
        attrs = feature["attributes"]
        bfs = attrs["FOSNR"]
        if bfs not in set(origins.municipality_bfs_id):
            raise ValueError("Point outside unchanged study universe")
        address = attrs["ADRESSE"]
        try:
            repaired = address.encode("latin1").decode("utf-8")
            if repaired.encode("utf-8").decode("latin1") == address:
                address = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        by_id[bfs] = dict(municipality_bfs_id=bfs, address=address, source_address_original=attrs["ADRESSE"],
            address_encoding_note="Original preserved; reversible Latin1/UTF8 display repair where applicable, coordinates untouched",
            address_source_id=sid, address_locator=f"Official main administration building layer: FOSNR={bfs}, OBJECTID={attrs['OBJECTID']}, EGAID={attrs['EGAID']}; CASE_POSTALE separate",
            coordinate_source_id=sid, coordinates_verified=True, coordinate_kind="official_main_building_arcgis_point",
            reviewed_object_id=attrs["OBJECTID"], reviewed_egaid=attrs["EGAID"],
            coordinate_locator="Official SGéo main-administration point, WGS84 requested and checked; exact BFS/object/entrance/address identity, not polygon centroid")
    review["origins"] = sorted(by_id.values(), key=lambda r: r["municipality_bfs_id"])
    (ROOT / REVIEW).write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sources = json.loads((ROOT / SOURCES).read_text(encoding="utf-8"))
    discovery = json.loads((ROOT / "config/accessibility_road_bulk_discovery_sources.json").read_text())
    if sid not in {s["source_id"] for s in sources}:
        sources.append(next(s for s in discovery if s["source_id"] == sid))
    (ROOT / SOURCES).write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"official_fribourg_main_building_points": len(ids)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--fribourg-points", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    if args.review:
        review_candidates()
    if args.fribourg_points:
        fribourg_points()
