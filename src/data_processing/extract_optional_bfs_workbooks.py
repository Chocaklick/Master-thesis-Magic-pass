"""Read immutable BFS workbooks with the bundled spreadsheet Python runtime.

No workbook is edited. Output is a checksum-linked cell-value intermediate for
the project's Python environment, which does not require Excel libraries.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    specs = json.loads((ROOT / "config/municipality_additional_evidence_sources.json").read_text(encoding="utf-8"))
    result = {}
    for spec in specs:
        if spec["suffix"] != "xlsx":
            continue
        records = [json.loads(p.read_text(encoding="utf-8")) for p in
                   (ROOT / "data_external/source_evidence").glob(spec["source_id"] + "_*.metadata.json")]
        record = max(records, key=lambda r: r["retrieval_date"])
        raw = ROOT / record["raw_file"]
        if hashlib.sha256(raw.read_bytes()).hexdigest() != record["sha256"]:
            raise RuntimeError(f"Source checksum mismatch: {raw}")
        workbook = openpyxl.load_workbook(raw, read_only=True, data_only=True)
        result[spec["source_id"]] = dict(raw_file=record["raw_file"], sha256=record["sha256"], sheets={
            sheet.title: [list(row) for row in sheet.iter_rows(values_only=True)] for sheet in workbook})
        workbook.close()
    folder = ROOT / "data_interim/municipality_additional_context"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "workbooks.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Checksum-linked workbook extraction:", len(result), "original workbooks")


if __name__ == "__main__":
    main()
