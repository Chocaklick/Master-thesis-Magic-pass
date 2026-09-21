"""Download official STATPOP permanent-resident population by municipality.

The exact PXWeb POST query, raw CSV response, metadata and SHA-256 checksum
are preserved. A checksum-verified cached response is reused on later runs.
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
METADATA_SOURCE_ID = "BFS_STATPOP_METADATA"
DATA_SOURCE_ID = "BFS_STATPOP_DATA"
ENDPOINT = (
    "https://www.pxweb.bfs.admin.ch/api/v1/fr/"
    "px-x-0102010000_101/px-x-0102010000_101.px"
)
REFERENCE_YEAR = "2025"


def checked_raw(record: dict) -> Path:
    path = ROOT / record["raw_file"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != record["sha256"]:
        raise RuntimeError(f"Cached evidence integrity failure: {path}")
    return path


def latest_metadata() -> dict:
    records = []
    for path in sorted(EVIDENCE_DIR.glob(f"{METADATA_SOURCE_ID}_*.metadata.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == METADATA_SOURCE_ID:
            records.append(record)
    if not records:
        raise FileNotFoundError(
            f"No cached {METADATA_SOURCE_ID}; run collect_evidence.py first"
        )
    record = max(records, key=lambda item: item["retrieval_date"])
    checked_raw(record)
    return record


def cached_data() -> dict | None:
    records = []
    for path in sorted(EVIDENCE_DIR.glob(f"{DATA_SOURCE_ID}_*.metadata.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            record.get("source_id") == DATA_SOURCE_ID
            and str(record.get("reference_year")) == REFERENCE_YEAR
        ):
            records.append(record)
    if not records:
        return None
    record = max(records, key=lambda item: item["retrieval_date"])
    checked_raw(record)
    request_path = ROOT / record["request_file"]
    if hashlib.sha256(request_path.read_bytes()).hexdigest() != record["request_sha256"]:
        raise RuntimeError(f"Cached request integrity failure: {request_path}")
    return record


def selection(variable: dict, values: list[str]) -> dict:
    missing = set(values) - set(variable["values"])
    if missing:
        raise ValueError(f"Missing {variable['code']} values: {sorted(missing)}")
    return {
        "code": variable["code"],
        "selection": {"filter": "item", "values": values},
    }


def build_query(table: dict) -> tuple[dict, int]:
    variables = {variable["code"]: variable for variable in table["variables"]}
    geography_code = "Kanton (-) / Bezirk (>>) / Gemeinde (......)"
    geography = variables[geography_code]
    municipalities = [
        value
        for value, label in zip(geography["values"], geography["valueTexts"])
        if str(label).startswith("......")
    ]
    query = [
        selection(variables["Jahr"], [REFERENCE_YEAR]),
        selection(geography, municipalities),
        selection(variables["Bevölkerungstyp"], ["1"]),
        selection(variables["Staatsangehörigkeit (Kategorie)"], ["-99999"]),
        selection(variables["Geschlecht"], ["-99999"]),
        selection(variables["Alter"], ["-99999"]),
    ]
    return {"query": query, "response": {"format": "csv"}}, len(municipalities)


def main() -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cached = cached_data()
    if cached:
        print(
            DATA_SOURCE_ID,
            "cached",
            cached["reference_year"],
            cached["municipalities"],
            "municipalities",
        )
        return

    metadata_record = latest_metadata()
    table = json.loads(checked_raw(metadata_record).read_text(encoding="utf-8"))
    payload, municipality_count = build_query(table)
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

    raw_path = EVIDENCE_DIR / f"{DATA_SOURCE_ID}_{REFERENCE_YEAR}_{token}.csv"
    request_path = EVIDENCE_DIR / f"{DATA_SOURCE_ID}_{REFERENCE_YEAR}_{token}.request.json"
    raw_path.write_bytes(content)
    request_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    record = {
        "source_id": DATA_SOURCE_ID,
        "organisation": "Swiss Federal Statistical Office",
        "description": "Official STATPOP permanent resident population by municipality",
        "retrieval_date": stamp.isoformat(),
        "url": ENDPOINT,
        "final_url": final_url,
        "reference_year": REFERENCE_YEAR,
        "population_type": "Population résidante permanente",
        "municipalities": municipality_count,
        "raw_file": raw_path.relative_to(ROOT).as_posix(),
        "request_file": request_path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "request_sha256": hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "size_bytes": len(content),
        "http_status": status,
    }
    metadata_path = EVIDENCE_DIR / f"{DATA_SOURCE_ID}_{REFERENCE_YEAR}_{token}.metadata.json"
    metadata_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    rows = max(0, content.count(b"\n") - 1)
    append_log(
        {
            "timestamp": stamp.isoformat(),
            "task": "statpop_collection",
            "source_id": DATA_SOURCE_ID,
            "source": "Swiss Federal Statistical Office",
            "source_url": ENDPOINT,
            "URL/API": ENDPOINT,
            "request": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            "retrieval_method": "PXWeb HTTP POST; one current-year municipality extract",
            "HTTP_status": status,
            "status": "downloaded",
            "raw_file": record["raw_file"],
            "output_file": record["raw_file"],
            "checksum": record["sha256"],
            "records": rows,
            "rows_collected": rows,
            "success": "True",
            "notes": (
                "2025 permanent residents; total citizenship, sex and age; "
                "current municipality reference from cached table metadata."
            ),
        }
    )
    print(DATA_SOURCE_ID, status, len(content), "bytes", rows, "CSV rows")


if __name__ == "__main__":
    main()
