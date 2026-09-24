"""Collect the large SPASS snow-depth grid with resumable verified downloads.

The EnviDat resource is a single ZIP member rather than year-separated files.
The server supports byte ranges, so the archive is downloaded in bounded chunks
and can be resumed after interruption.  Both the immutable ZIP response and its
original NetCDF member are retained under the ignored evidence cache.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from collect_evidence import append_log


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "spass_snow_grid.json"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
IO_CHUNK = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(IO_CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def cached_record(source_id: str) -> dict | None:
    records = []
    for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if not records:
        return None
    if len(records) != 1:
        raise RuntimeError(f"Expected one cached {source_id} record, found {len(records)}")
    record = records[0]
    archive_path = ROOT / record["raw_file"]
    member_path = ROOT / record["extracted_file"]
    if archive_path.stat().st_size != int(record["size_bytes"]):
        raise RuntimeError("Cached SPASS archive size differs from metadata")
    if member_path.stat().st_size != int(record["extracted_size_bytes"]):
        raise RuntimeError("Cached SPASS NetCDF size differs from metadata")
    return record


def download_archive(config: dict, part_path: Path) -> None:
    total = int(config["archive_size_bytes"])
    chunk_size = int(config["download_chunk_bytes"])
    existing = part_path.stat().st_size if part_path.exists() else 0
    if existing > total:
        raise RuntimeError("Partial SPASS archive exceeds configured size")

    while existing < total:
        end = min(existing + chunk_size, total) - 1
        expected_range = f"bytes {existing}-{end}/{total}"
        chunk_path = part_path.with_suffix(".chunk")
        last_error: Exception | None = None
        for attempt in range(1, 5):
            try:
                chunk_path.unlink(missing_ok=True)
                command = [
                    "curl.exe",
                    "--location",
                    "--fail-with-body",
                    "--retry",
                    "4",
                    "--retry-all-errors",
                    "--connect-timeout",
                    "30",
                    "--max-time",
                    "600",
                    "--range",
                    f"{existing}-{end}",
                    "--output",
                    str(chunk_path),
                    "--silent",
                    "--show-error",
                    "--write-out",
                    "%{http_code}\\n%header{content-range}\\n%header{etag}\\n",
                    config["archive_url"],
                ]
                result = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=720,
                )
                response_lines = result.stdout.splitlines()
                if len(response_lines) < 3 or response_lines[-3] != "206":
                    raise RuntimeError(f"Unexpected curl response: {result.stdout!r}")
                actual_range = response_lines[-2]
                actual_etag = response_lines[-1]
                if actual_range != expected_range:
                    raise RuntimeError(
                        f"Unexpected Content-Range {actual_range!r}; expected {expected_range!r}"
                    )
                if actual_etag != config["archive_etag"]:
                    raise RuntimeError(
                        f"Unexpected ETag {actual_etag!r}; expected {config['archive_etag']!r}"
                    )
                expected_written = end - existing + 1
                if chunk_path.stat().st_size != expected_written:
                    raise RuntimeError(
                        f"Range body size {chunk_path.stat().st_size} differs from {expected_written}"
                    )
                with chunk_path.open("rb") as source, part_path.open("ab") as output:
                    shutil.copyfileobj(source, output, IO_CHUNK)
                chunk_path.unlink()
                last_error = None
                break
            except (OSError, subprocess.SubprocessError, TimeoutError, RuntimeError) as exc:
                last_error = exc
                if attempt == 4:
                    raise
                time.sleep(2**attempt)
        if last_error is not None:
            raise last_error
        existing = part_path.stat().st_size
        print(f"SPASS archive {existing}/{total} bytes ({100 * existing / total:.1f}%)")

    if existing != total:
        raise RuntimeError(f"SPASS archive size {existing} differs from {total}")


def extract_member(config: dict, archive_path: Path, member_part: Path) -> None:
    expected_name = config["archive_member"]
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) != 1 or members[0].filename != expected_name:
            raise RuntimeError(
                f"Unexpected SPASS ZIP members: {[member.filename for member in members]}"
            )
        info = members[0]
        if info.compress_type != zipfile.ZIP_DEFLATED:
            raise RuntimeError(f"Unexpected ZIP method {info.compress_type}")
        if info.compress_size != int(config["member_compressed_size_bytes"]):
            raise RuntimeError("SPASS compressed member size differs from configuration")
        if info.file_size != int(config["member_uncompressed_size_bytes"]):
            raise RuntimeError("SPASS uncompressed member size differs from configuration")
        if f"{info.CRC:08x}" != config["member_crc32"].lower():
            raise RuntimeError("SPASS member CRC32 differs from configuration")
        with archive.open(info) as source, member_part.open("wb") as output:
            copied = 0
            while True:
                block = source.read(IO_CHUNK)
                if not block:
                    break
                output.write(block)
                copied += len(block)
                if copied % (512 * IO_CHUNK) < IO_CHUNK:
                    print(
                        f"SPASS NetCDF {copied}/{info.file_size} bytes "
                        f"({100 * copied / info.file_size:.1f}%)"
                    )
        if copied != info.file_size:
            raise RuntimeError(f"Extracted SPASS size {copied} differs from {info.file_size}")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cached = cached_record(config["source_id"])
    if cached:
        if config.get("archive_sha256") and cached["sha256"] != config["archive_sha256"]:
            raise RuntimeError("Cached SPASS archive hash differs from pinned configuration")
        if config.get("member_sha256") and cached["extracted_sha256"] != config["member_sha256"]:
            raise RuntimeError("Cached SPASS NetCDF hash differs from pinned configuration")
        print(config["source_id"], "cached", cached["extracted_size_bytes"])
        return

    stamp = datetime.now(timezone.utc)
    token = stamp.strftime("%Y%m%dT%H%M%SZ")
    archive_part = EVIDENCE_DIR / f".{config['source_id']}.zip.part"
    member_part = EVIDENCE_DIR / f".{config['source_id']}.nc.part"
    archive_path = EVIDENCE_DIR / f"{config['source_id']}_{token}.zip"
    member_path = EVIDENCE_DIR / f"{config['source_id']}_{token}.nc"

    download_archive(config, archive_part)
    archive_sha256 = sha256_file(archive_part)
    if config.get("archive_sha256") and archive_sha256 != config["archive_sha256"]:
        raise RuntimeError("Downloaded SPASS archive hash differs from pinned configuration")
    archive_part.replace(archive_path)

    extract_member(config, archive_path, member_part)
    member_sha256 = sha256_file(member_part)
    if config.get("member_sha256") and member_sha256 != config["member_sha256"]:
        raise RuntimeError("Extracted SPASS NetCDF hash differs from pinned configuration")
    member_part.replace(member_path)

    metadata = {
        "source_id": config["source_id"],
        "source_page_url": config["source_page_url"],
        "archive_url": config["archive_url"],
        "organisation": config["organisation"],
        "description": config["dataset_title"],
        "dataset_version": config["dataset_version"],
        "doi": config["doi"],
        "license": config["license"],
        "license_url": config["license_url"],
        "retrieval_date": stamp.isoformat(),
        "http_status": 206,
        "retrieval_method": "resumable HTTP byte-range download of complete single-member ZIP",
        "archive_etag": config["archive_etag"],
        "raw_file": archive_path.relative_to(ROOT).as_posix(),
        "sha256": archive_sha256,
        "size_bytes": archive_path.stat().st_size,
        "archive_member": config["archive_member"],
        "member_crc32": config["member_crc32"],
        "extracted_file": member_path.relative_to(ROOT).as_posix(),
        "extracted_sha256": member_sha256,
        "extracted_size_bytes": member_path.stat().st_size,
    }
    metadata_path = EVIDENCE_DIR / f"{config['source_id']}_{token}.metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    append_log(
        {
            "timestamp": stamp.isoformat(),
            "task": "spass_gridded_snow_collection",
            "source_id": config["source_id"],
            "source": config["organisation"],
            "source_url": config["source_page_url"],
            "URL/API": config["archive_url"],
            "request": f"GET Range chunks, complete bytes 0-{config['archive_size_bytes'] - 1}",
            "retrieval_method": metadata["retrieval_method"],
            "HTTP_status": 206,
            "status": "downloaded_and_extracted",
            "raw_file": metadata["raw_file"],
            "output_file": metadata["extracted_file"],
            "checksum": archive_sha256,
            "records": "one original NetCDF member",
            "success": "True",
            "notes": (
                f"archive ETag {config['archive_etag']}; member CRC32 "
                f"{config['member_crc32']}; extracted SHA-256 {member_sha256}"
            ),
        }
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
