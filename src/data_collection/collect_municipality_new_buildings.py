"""Collect the requested BFS construction cube for the existing territorial universe.

Run from the project root. Preserve the query, immutable response and checksum;
reuse the cached response on subsequent runs. No municipality name matching.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

from collect_evidence import AGENT, append_log

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / "data_external/source_evidence"
SOURCE_ID = "BFS_NEW_RESIDENTIAL_BUILDINGS_DATA"
METADATA_ID = "BFS_NEW_RESIDENTIAL_BUILDINGS_METADATA"


def cached(source_id: str) -> dict | None:
    records = [json.loads(p.read_text(encoding="utf-8"))
               for p in FOLDER.glob(f"{source_id}_*.metadata.json")]
    if not records:
        return None
    record = max(records, key=lambda r: r["retrieval_date"])
    for field, checksum in [("raw_file", "sha256"), ("request_file", "request_sha256")]:
        if field in record and hashlib.sha256((ROOT / record[field]).read_bytes()).hexdigest() != record[checksum]:
            raise RuntimeError(f"Cached evidence integrity failure: {record[field]}")
    return record


def build_query(metadata: dict, municipality_ids: set[int]) -> tuple[dict, list[int]]:
    # This source retains the predecessor BFS 700. The approved official bridge
    # verifies that it is the same territory as analytical BFS 6831.
    requested = {700 if int(x) == 6831 else int(x) for x in municipality_ids}
    query = []
    unmatched = []
    for variable in metadata["variables"]:
        if "Gemeinde" in variable["code"]:
            available = {int(v): v for v, label in zip(variable["values"], variable["valueTexts"])
                         if v.isdigit() and label.startswith("......")}
            unmatched = sorted(requested - available.keys())
            values = [available[x] for x in sorted(requested & available.keys())]
        else:
            values = variable["values"]
        query.append({"code": variable["code"], "selection": {"filter": "item", "values": values}})
    return {"query": query, "response": {"format": "csv"}}, unmatched


def main() -> None:
    bridge = json.loads((ROOT / "config/accessibility_outcome_territorial_harmonisation.json").read_text(encoding="utf-8"))
    ids = set(pd.read_csv(ROOT / bridge["comparison_universe"]).municipality_bfs_id.unique())
    meta = cached(METADATA_ID)
    if meta is None:
        raise FileNotFoundError("Collect the configured PXWeb metadata first")
    query, unmatched = build_query(json.loads((ROOT / meta["raw_file"]).read_text(encoding="utf-8")), ids)
    old = cached(SOURCE_ID)
    if old:
        if json.loads((ROOT / old["request_file"]).read_text(encoding="utf-8")) != query:
            raise RuntimeError("Cached query differs from current universe; version a new extract explicitly")
        print(SOURCE_ID, "cached", "unmatched IDs:", unmatched)
        return
    stamp = datetime.now(timezone.utc)
    token = stamp.strftime("%Y%m%dT%H%M%SZ")
    body = json.dumps(query, ensure_ascii=False).encode("utf-8")
    endpoint = meta["url"]
    row = dict(timestamp=stamp.isoformat(), task="municipality_additional_context_collection",
               source_id=SOURCE_ID, source="Swiss Federal Statistical Office", source_url=endpoint,
               **{"URL/API": endpoint}, request=json.dumps(query, ensure_ascii=False),
               retrieval_method="PXWeb POST CSV; municipality IDs selected from approved territorial universe",
               success="False")
    try:
        req = Request(endpoint, data=body, method="POST", headers={"User-Agent": AGENT, "Content-Type": "application/json"})
        with urlopen(req, timeout=120) as response:
            content, status, final_url = response.read(), response.status, response.geturl()
        raw = FOLDER / f"{SOURCE_ID}_{token}.csv"
        request_path = FOLDER / f"{SOURCE_ID}_{token}.request.json"
        raw.write_bytes(content)
        request_path.write_text(json.dumps(query, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        record = dict(source_id=SOURCE_ID, url=endpoint, final_url=final_url, retrieval_date=stamp.isoformat(),
                      raw_file=raw.relative_to(ROOT).as_posix(), request_file=request_path.relative_to(ROOT).as_posix(),
                      sha256=hashlib.sha256(content).hexdigest(), request_sha256=hashlib.sha256(request_path.read_bytes()).hexdigest(),
                      http_status=status, size_bytes=len(content), metadata_source_id=METADATA_ID,
                      unmatched_source_ids=unmatched, analytical_territories=len(ids),
                      moutier_bridge_source_id="BFS_MUNICIPAL_MUTATION_3999")
        (FOLDER / f"{SOURCE_ID}_{token}.metadata.json").write_text(json.dumps(record, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        row.update(HTTP_status=status, status="downloaded", raw_file=record["raw_file"], output_file=record["raw_file"],
                   checksum=record["sha256"], success="True", notes=f"Unmatched source IDs: {unmatched}; no imputation")
        print(SOURCE_ID, status, len(content), "bytes", "unmatched IDs:", unmatched)
    except Exception as exc:
        row.update(status="failed", error=f"{type(exc).__name__}: {exc}", HTTP_status=getattr(exc, "code", ""))
        raise
    finally:
        append_log(row)


if __name__ == "__main__":
    main()
