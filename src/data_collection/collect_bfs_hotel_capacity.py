"""Download the official BFS HESTA municipality-month capacity table.

The PXWeb response and the exact POST query are preserved as immutable raw
evidence.  A checksum-verified cached response is reused on later runs.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from collect_evidence import AGENT, append_log


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
METADATA_SOURCE_ID = "BFS_HOTEL_CAPACITY_METADATA"
DATA_SOURCE_ID = "BFS_HOTEL_CAPACITY_DATA"
ENDPOINT = "https://www.pxweb.bfs.admin.ch/api/v1/fr/px-x-1003020000_201/px-x-1003020000_201.px"


def latest_exact_metadata(source_id: str) -> dict:
    matches = []
    for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            matches.append(record)
    if not matches:
        raise FileNotFoundError(
            f"No cached {source_id} metadata. Run collect_evidence.py first."
        )
    return matches[-1]


def checked_raw(record: dict) -> Path:
    path = ROOT / record["raw_file"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != record["sha256"]:
        raise RuntimeError(f"Cached evidence integrity failure: {path}")
    return path


def table_query(table_metadata: dict, selected_years: list[str]) -> dict:
    query = []
    for variable in table_metadata["variables"]:
        values = variable["values"]
        if variable["code"] == "Jahr":
            values = selected_years
        elif variable["code"] == "Monat":
            values = [value for value in values if value != "YYYY"]
        query.append(
            {
                "code": variable["code"],
                "selection": {"filter": "item", "values": values},
            }
        )
    return {"query": query, "response": {"format": "csv"}}


def cached_data() -> dict | None:
    matches = []
    for path in sorted(EVIDENCE_DIR.glob(f"{DATA_SOURCE_ID}_*.metadata.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == DATA_SOURCE_ID and record.get("raw_files"):
            matches.append(record)
    if not matches:
        return None
    record = max(matches, key=lambda item: item["retrieval_date"])
    for item in record["raw_files"]:
        path = ROOT / item["raw_file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError(f"Cached evidence integrity failure: {path}")
    return record


def cached_years() -> dict[str, dict]:
    records: dict[str, dict] = {}
    for path in sorted(EVIDENCE_DIR.glob(f"{DATA_SOURCE_ID}_????_*.metadata.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") != DATA_SOURCE_ID or not record.get("year"):
            continue
        checked_raw(record)
        records[str(record["year"])] = record
    return records


def download_year(table_metadata: dict, year: str) -> dict:
    payload = table_query(table_metadata, [year])
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stamp = datetime.now(timezone.utc)
    token = stamp.strftime("%Y%m%dT%H%M%SZ")
    request = Request(
        ENDPOINT,
        data=body,
        headers={
            "User-Agent": AGENT,
            "Content-Type": "application/json",
            "Accept": "text/csv",
        },
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        content = response.read()
        status = response.status
        final_url = response.geturl()

    stem = f"{DATA_SOURCE_ID}_{year}_{token}"
    raw_path = EVIDENCE_DIR / f"{stem}.csv"
    request_path = EVIDENCE_DIR / f"{stem}.request.json"
    raw_path.write_bytes(content)
    request_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    checksum = hashlib.sha256(content).hexdigest()
    record = {
        "source_id": DATA_SOURCE_ID,
        "year": year,
        "organisation": "Swiss Federal Statistical Office",
        "description": "Official HESTA municipality-month hotel supply, demand and occupancy data",
        "retrieval_date": stamp.isoformat(),
        "url": ENDPOINT,
        "final_url": final_url,
        "request_file": request_path.relative_to(ROOT).as_posix(),
        "request_sha256": hashlib.sha256(body).hexdigest(),
        "raw_file": raw_path.relative_to(ROOT).as_posix(),
        "sha256": checksum,
        "size_bytes": len(content),
        "http_status": status,
        "selected_years": 1,
        "selected_months": 12,
        "selected_municipalities": len(table_metadata["variables"][2]["values"]),
        "selected_indicators": len(table_metadata["variables"][3]["values"]),
    }
    (EVIDENCE_DIR / f"{stem}.metadata.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    rows = max(0, content.count(b"\n") - 1)
    append_log(
        {
            "timestamp": stamp.isoformat(),
            "task": "hotel_capacity_collection",
            "source_id": DATA_SOURCE_ID,
            "source": "Swiss Federal Statistical Office",
            "source_url": ENDPOINT,
            "URL/API": ENDPOINT,
            "request": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            "retrieval_method": "PXWeb HTTP POST; annual chunk",
            "HTTP_status": status,
            "status": "downloaded",
            "raw_file": record["raw_file"],
            "output_file": record["raw_file"],
            "checksum": checksum,
            "records": rows,
            "rows_collected": rows,
            "success": "True",
            "notes": f"Annual-total month excluded; calendar year {year}.",
        }
    )
    print(year, status, len(content), "bytes", rows, "CSV rows")
    return record


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cached = cached_data()
    if cached:
        total_bytes = sum(item["size_bytes"] for item in cached["raw_files"])
        print(DATA_SOURCE_ID, "cached", len(cached["raw_files"]), "chunks", total_bytes, "bytes")
        return

    metadata_record = latest_exact_metadata(METADATA_SOURCE_ID)
    metadata_path = checked_raw(metadata_record)
    table_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    years = table_metadata["variables"][0]["values"]
    records = cached_years()
    for year in years:
        if year in records:
            print(year, "cached")
            continue
        records[year] = download_year(table_metadata, year)

    completed = [records[year] for year in years]
    stamp = datetime.now(timezone.utc)
    master = {
        "source_id": DATA_SOURCE_ID,
        "organisation": "Swiss Federal Statistical Office",
        "description": "Official HESTA municipality-month hotel supply, demand and occupancy data",
        "retrieval_date": stamp.isoformat(),
        "url": ENDPOINT,
        "retrieval_method": "PXWeb HTTP POST in annual chunks",
        "raw_files": [
            {
                "year": record["year"],
                "raw_file": record["raw_file"],
                "request_file": record["request_file"],
                "sha256": record["sha256"],
                "size_bytes": record["size_bytes"],
            }
            for record in completed
        ],
        "years": years,
        "months": 12,
        "municipalities": len(table_metadata["variables"][2]["values"]),
        "indicators": len(table_metadata["variables"][3]["values"]),
    }
    token = stamp.strftime("%Y%m%dT%H%M%SZ")
    (EVIDENCE_DIR / f"{DATA_SOURCE_ID}_{token}.metadata.json").write_text(
        json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(DATA_SOURCE_ID, "complete", len(completed), "annual chunks")


if __name__ == "__main__":
    main()
