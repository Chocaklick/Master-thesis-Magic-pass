"""Inventory original research inputs without modifying them. Run from project root."""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MISSING_TOKENS = {"", "NA", "N/A", "NaN", "nan", "null"}
DICTIONARY_COLUMNS = [
    "variable", "table", "description", "unit", "data_type", "geographic_level",
    "temporal_level", "source_id", "raw_or_derived", "formula", "causal_role",
    "missing_share", "notes",
]
SOURCE_COLUMNS = [
    "source_id", "variable_name", "variable_description", "source_organisation",
    "source_dataset_name", "source_page_url", "direct_download_url", "api_endpoint",
    "api_parameters", "wms_layer", "geocat_metadata_url", "retrieval_method",
    "retrieval_date", "original_file_name", "local_raw_file", "processed_file",
    "geographic_level", "temporal_resolution", "temporal_start", "temporal_end",
    "unit", "license", "access_conditions", "transformation_applied", "quality_notes",
    "confidence_level", "manual_verification", "notes",
]


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_csv(path: Path) -> pd.DataFrame:
    """Retain literal source tokens and identifiers; inference is an audit output."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        delimiter = csv.Sniffer().sniff(stream.read(8192), delimiters=",;\t").delimiter
    return pd.read_csv(path, sep=delimiter, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def json_value(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "" if value is None else str(value)


def read_tables(path: Path) -> dict[str, pd.DataFrame]:
    if path.suffix.lower() == ".csv":
        return {path.stem: read_csv(path)}
    if path.suffix.lower() == ".geojson":
        obj = json.loads(path.read_text(encoding="utf-8-sig"))
        return {path.stem: pd.DataFrame([
            {k: json_value(v) for k, v in feature["properties"].items()}
            for feature in obj["features"]
        ]).fillna("")}
    if path.suffix.lower() == ".gpkg":
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            tables = db.execute("SELECT table_name FROM gpkg_contents").fetchall()
            result = {}
            for (table,) in tables:
                quoted = '"' + table.replace('"', '""') + '"'
                frame = pd.read_sql_query(f"SELECT * FROM {quoted}", db)
                for name in frame:
                    frame[name] = frame[name].map(
                        lambda x: hashlib.sha256(x).hexdigest() if isinstance(x, bytes) else json_value(x)
                    )
                result[table] = frame
            return result
    return {}


def profile(frame: pd.DataFrame) -> dict:
    columns = []
    for name in frame:
        values = frame[name].astype(str)
        missing = values.isin(MISSING_TOKENS)
        available = values[~missing]
        numeric = pd.to_numeric(available, errors="coerce")
        dtype = "unknown" if available.empty else "numeric" if numeric.notna().all() else "string"
        columns.append({
            "variable": name, "inferred_type": dtype, "missing_count": int(missing.sum()),
            "missing_share": float(missing.mean()) if len(frame) else None,
            "n_unique_nonmissing": int(available.nunique()),
            "examples": available.drop_duplicates().head(5).tolist(),
            "nonnumeric_tokens": available[numeric.isna()].value_counts().head(10).to_dict()
            if numeric.notna().any() else {},
        })
    return {"n_rows": len(frame), "n_columns": len(frame.columns),
            "duplicate_rows": int(frame.duplicated().sum()), "columns": columns}


def main():
    raw_paths = sorted(p for p in (ROOT / "data_raw").rglob("*") if p.is_file() and p.name != ".gitkeep")
    manifest, audit, details, dictionary, sources = [], [], {}, [], []
    for path in raw_paths:
        relative = path.relative_to(ROOT).as_posix()
        source_id = "LOCAL_" + hashlib.sha256(relative.encode()).hexdigest()[:12]
        manifest.append({"file_name": relative, "size_bytes": path.stat().st_size,
                         "sha256": sha256(path), "source_id": source_id})
        tables = read_tables(path)
        details[relative] = {}
        for table, frame in tables.items():
            info = profile(frame)
            details[relative][table] = info
            keys = [c for c in frame if c in {"ski_id", "cluster_id", "fid", "Commune", "url_station", "Année", "Mois"}]
            audit.append({
                "file_name": relative, "dataset_description": table,
                "n_rows": len(frame), "n_columns": len(frame.columns),
                "temporal_start": frame["Année"].min() if "Année" in frame else "UNKNOWN",
                "temporal_end": frame["Année"].max() if "Année" in frame else "UNKNOWN",
                "n_resorts": frame["ski_id"].nunique() if "ski_id" in frame else "UNKNOWN",
                "n_municipalities": frame["Commune"].nunique() if "Commune" in frame else "UNKNOWN",
                "geographic_level": "municipality label" if "Commune" in frame else "requires verification",
                "potential_join_keys": "|".join(keys), "important_variables": "|".join(frame.columns),
                "missingness_summary": json.dumps({c["variable"]: c["missing_count"] for c in info["columns"] if c["missing_count"]}, ensure_ascii=False),
                "known_source": source_id, "quality_notes": f"Exact duplicate rows: {info['duplicate_rows']}; literal source tokens retained",
                "recommended_use": "audit before analytical use",
            })
            for c in info["columns"]:
                dictionary.append({"table": table, "variable": c["variable"],
                    "description": "Source field; definition requires verification", "data_type": c["inferred_type"],
                    "unit": "UNKNOWN", "geographic_level": audit[-1]["geographic_level"],
                    "temporal_level": "UNKNOWN", "source_id": source_id,
                    "raw_or_derived": "existing thesis input",
                    "formula": "", "causal_role": "unclassified", "missing_share": c["missing_share"],
                    "notes": ("Byte geometry represented by SHA-256 for audit only" if c["variable"] == "geom"
                              else "Missing/source-token meaning requires verification")})
        if not tables:
            audit.append({"file_name": relative, "dataset_description": "Existing HTML research map" if path.suffix == ".html" else "Unparsed input",
                          "n_rows": "UNKNOWN", "n_columns": "UNKNOWN", "known_source": source_id,
                          "quality_notes": "Non-tabular original retained; embedded evidence requires separate extraction",
                          "recommended_use": "inspect provenance and embedded map data"})
        sources.append({"source_id": source_id, "variable_name": "dataset",
            "variable_description": "Existing thesis input; upstream construction under audit",
            "source_organisation": "UNKNOWN", "source_dataset_name": path.name,
            "retrieval_method": "researcher-supplied local file",
            "retrieval_date": "UNKNOWN", "original_file_name": path.name,
            "local_raw_file": relative, "license": "UNKNOWN", "access_conditions": "Local research copy; redistribution not established",
            "quality_notes": "See reports/data_audit_details.json; upstream provenance requires verification",
            "confidence_level": "unverified", "manual_verification": "pending",
            "notes": "Filesystem timestamp is not treated as a retrieval date"})
    (ROOT / "reports/data_audit_details.json").write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(manifest).to_csv(ROOT / "metadata/raw_file_manifest.csv", index=False)
    pd.DataFrame(audit).to_csv(ROOT / "reports/data_audit.csv", index=False)
    # Merge by stable keys: later manual/source verification must survive reruns.
    merge_registry(ROOT / "metadata/data_dictionary.csv", dictionary, ["table", "variable"], DICTIONARY_COLUMNS)
    merge_registry(ROOT / "metadata/data_sources_master.csv", sources, ["source_id"], SOURCE_COLUMNS)
    print(json.dumps({"source_files": len(raw_paths), "tables": sum(len(t) for t in details.values()),
                      "rows_by_file": {r["file_name"]: r["n_rows"] for r in audit}}, ensure_ascii=False, indent=2))


def merge_registry(path: Path, rows: list[dict], keys: list[str], columns: list[str]):
    existing = pd.read_csv(path, dtype=str, keep_default_na=False) if path.exists() else pd.DataFrame()
    incoming = pd.DataFrame(rows)
    combined = pd.concat([existing, incoming], ignore_index=True).fillna("")
    combined = combined.drop_duplicates(subset=keys, keep="first")
    combined.reindex(columns=columns, fill_value="").to_csv(path, index=False)


if __name__ == "__main__":
    main()
