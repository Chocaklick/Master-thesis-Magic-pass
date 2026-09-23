"""Collect one checksum-verified CSV member from the official Eurostat grid ZIP.

The full archive contains several redundant encodings and census themes.  The
collector uses the archive's advertised byte-range support to retrieve only the
compressed CSV member, then validates its length and ZIP CRC before preserving
the original CSV.  Interrupted range downloads are resumed from a local part
file; no statistical rows are filtered at collection time.
"""

from __future__ import annotations

import binascii
import hashlib
import json
import os
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from collect_evidence import AGENT, append_log


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "eurostat_census_grid_2021.json"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_cached(source_id: str) -> dict | None:
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
    raw = ROOT / record["raw_file"]
    if not raw.exists() or sha256_file(raw) != record["sha256"]:
        raise RuntimeError(f"Cached evidence integrity failure: {source_id}")
    return record


def check_robots(url: str, stamp: datetime) -> None:
    parsed = urlsplit(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        with urlopen(Request(robots_url, headers={"User-Agent": AGENT}), timeout=45) as response:
            content = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            return
        raise
    parser = RobotFileParser()
    parser.parse(content.decode("utf-8", errors="replace").splitlines())
    robots_path = EVIDENCE_DIR / (
        f"{parsed.netloc}_robots_{stamp.strftime('%Y%m%dT%H%M%SZ')}.txt"
    )
    robots_path.write_bytes(content)
    if not parser.can_fetch(AGENT, url):
        raise PermissionError("robots.txt disallows this request")


def download_member(config: dict, compressed_path: Path) -> None:
    range_start = int(config["member_data_range_start"])
    range_end = int(config["member_data_range_end"])
    expected_size = int(config["member_compressed_size_bytes"])
    existing = compressed_path.stat().st_size if compressed_path.exists() else 0
    if existing > expected_size:
        raise RuntimeError("Partial compressed member is larger than the configured member")
    while existing < expected_size:
        request_start = range_start + existing
        request = Request(
            config["archive_url"],
            headers={
                "User-Agent": AGENT,
                "Range": f"bytes={request_start}-{range_end}",
                "If-Range": config["archive_etag"],
            },
        )
        with urlopen(request, timeout=90) as response:
            if response.status != 206:
                raise RuntimeError(
                    f"Expected HTTP 206 for range request, received {response.status}"
                )
            expected_content_range = f"bytes {request_start}-{range_end}/{config['archive_size_bytes']}"
            if response.headers.get("Content-Range") != expected_content_range:
                raise RuntimeError(
                    "Unexpected Content-Range: "
                    f"{response.headers.get('Content-Range')} != {expected_content_range}"
                )
            with compressed_path.open("ab") as output:
                while True:
                    block = response.read(CHUNK_SIZE)
                    if not block:
                        break
                    output.write(block)
        new_size = compressed_path.stat().st_size
        if new_size <= existing:
            raise RuntimeError("Range download made no progress")
        existing = new_size
    if existing != expected_size:
        raise RuntimeError(f"Compressed size mismatch: {existing} != {expected_size}")


def collect_documentation(config: dict, stamp: datetime) -> None:
    source_id = config["documentation_source_id"]
    if checked_cached(source_id):
        return
    start = int(config["documentation_member_data_range_start"])
    end = int(config["documentation_member_data_range_end"])
    request = Request(
        config["archive_url"],
        headers={
            "User-Agent": AGENT,
            "Range": f"bytes={start}-{end}",
            "If-Range": config["archive_etag"],
        },
    )
    with urlopen(request, timeout=90) as response:
        if response.status != 206:
            raise RuntimeError(
                f"Expected HTTP 206 for documentation range, received {response.status}"
            )
        expected_content_range = f"bytes {start}-{end}/{config['archive_size_bytes']}"
        if response.headers.get("Content-Range") != expected_content_range:
            raise RuntimeError(
                "Unexpected documentation Content-Range: "
                f"{response.headers.get('Content-Range')} != {expected_content_range}"
            )
        compressed = response.read()
    if len(compressed) != int(config["documentation_member_compressed_size_bytes"]):
        raise RuntimeError("Documentation compressed size mismatch")
    content = zlib.decompress(compressed, -zlib.MAX_WBITS)
    if len(content) != int(config["documentation_member_uncompressed_size_bytes"]):
        raise RuntimeError("Documentation uncompressed size mismatch")
    crc = f"{binascii.crc32(content) & 0xFFFFFFFF:08x}"
    if crc != config["documentation_member_crc32"].lower():
        raise RuntimeError("Documentation CRC32 mismatch")
    token = stamp.strftime("%Y%m%dT%H%M%SZ")
    raw_path = EVIDENCE_DIR / f"{source_id}_{token}.txt"
    raw_path.write_bytes(content)
    sha256 = hashlib.sha256(content).hexdigest()
    if sha256 != config["documentation_member_sha256"]:
        raw_path.unlink()
        raise RuntimeError(
            f"Documentation SHA-256 mismatch: {sha256} != {config['documentation_member_sha256']}"
        )
    metadata = {
        "source_id": source_id,
        "source_page_url": config["source_page_url"],
        "archive_url": config["archive_url"],
        "organisation": config["organisation"],
        "description": "Official read.me data dictionary and change log for the Eurostat Census Grid 2021 version 3",
        "license": config["license"],
        "member": config["documentation_member"],
        "member_crc32": config["documentation_member_crc32"],
        "retrieval_date": stamp.isoformat(),
        "http_status": 206,
        "retrieval_method": "HTTP byte-range extraction of one ZIP documentation member",
        "raw_file": raw_path.relative_to(ROOT).as_posix(),
        "sha256": sha256,
        "size_bytes": len(content),
    }
    metadata_path = EVIDENCE_DIR / f"{source_id}_{token}.metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    append_log(
        {
            "timestamp": stamp.isoformat(),
            "task": "cross_border_population_grid_documentation_collection",
            "source_id": source_id,
            "source": config["organisation"],
            "source_url": config["source_page_url"],
            "URL/API": config["archive_url"],
            "request": f"GET Range bytes={start}-{end}",
            "retrieval_method": "HTTP byte-range extraction of one ZIP documentation member",
            "HTTP_status": 206,
            "status": "downloaded_member_range",
            "raw_file": metadata["raw_file"],
            "output_file": metadata["raw_file"],
            "checksum": sha256,
            "records": "official read.me",
            "success": "True",
            "notes": f"ZIP member CRC32 {crc} and size {len(content)} verified",
        }
    )


def inflate_and_verify(config: dict, compressed_path: Path, output_path: Path) -> tuple[int, str]:
    decompressor = zlib.decompressobj(-zlib.MAX_WBITS)
    crc = 0
    size = 0
    digest = hashlib.sha256()
    with compressed_path.open("rb") as source, output_path.open("wb") as output:
        for block in iter(lambda: source.read(CHUNK_SIZE), b""):
            decoded = decompressor.decompress(block)
            if decoded:
                output.write(decoded)
                crc = binascii.crc32(decoded, crc)
                size += len(decoded)
                digest.update(decoded)
        decoded = decompressor.flush()
        if decoded:
            output.write(decoded)
            crc = binascii.crc32(decoded, crc)
            size += len(decoded)
            digest.update(decoded)
    if not decompressor.eof or decompressor.unused_data:
        raise RuntimeError("The ZIP member deflate stream did not end cleanly")
    if size != int(config["member_uncompressed_size_bytes"]):
        raise RuntimeError(
            f"Uncompressed size mismatch: {size} != {config['member_uncompressed_size_bytes']}"
        )
    actual_crc = f"{crc & 0xFFFFFFFF:08x}"
    if actual_crc != config["member_crc32"].lower():
        raise RuntimeError(f"CRC32 mismatch: {actual_crc} != {config['member_crc32']}")
    return size, digest.hexdigest()


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    cached = checked_cached(config["source_id"])
    cached_documentation = checked_cached(config["documentation_source_id"])
    if cached and cached["sha256"] != config["member_sha256"]:
        raise RuntimeError("Cached census-grid SHA-256 differs from the configured checksum")
    if (
        cached_documentation
        and cached_documentation["sha256"] != config["documentation_member_sha256"]
    ):
        raise RuntimeError("Cached census-grid documentation SHA-256 differs from configuration")
    if cached and cached_documentation:
        print(config["source_id"], "cached", cached["size_bytes"])
        return

    stamp = datetime.now(timezone.utc)
    token = stamp.strftime("%Y%m%dT%H%M%SZ")
    compressed_path = EVIDENCE_DIR / f".{config['source_id']}.deflate.part"
    raw_path = EVIDENCE_DIR / f"{config['source_id']}_{token}.csv"
    raw_part = raw_path.with_suffix(".csv.part")
    check_robots(config["archive_url"], stamp)
    if not cached_documentation:
        collect_documentation(config, stamp)
    if cached:
        print(config["source_id"], "cached", cached["size_bytes"])
        return
    row = {
        "timestamp": stamp.isoformat(),
        "task": "cross_border_population_grid_collection",
        "source_id": config["source_id"],
        "source": config["organisation"],
        "source_url": config["source_page_url"],
        "URL/API": config["archive_url"],
        "request": (
            f"GET Range bytes={config['member_data_range_start']}-"
            f"{config['member_data_range_end']}"
        ),
        "retrieval_method": "HTTP byte-range extraction of one ZIP CSV member",
        "success": "False",
    }
    try:
        download_member(config, compressed_path)
        size, sha256 = inflate_and_verify(config, compressed_path, raw_part)
        if sha256 != config["member_sha256"]:
            raise RuntimeError(
                f"CSV SHA-256 mismatch: {sha256} != {config['member_sha256']}"
            )
        os.replace(raw_part, raw_path)
        compressed_path.unlink()
        metadata = {
            **config,
            "retrieval_date": stamp.isoformat(),
            "http_status": 206,
            "retrieval_method": "HTTP byte-range extraction of one ZIP CSV member",
            "raw_file": raw_path.relative_to(ROOT).as_posix(),
            "sha256": sha256,
            "size_bytes": size,
        }
        metadata_path = EVIDENCE_DIR / f"{config['source_id']}_{token}.metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        row.update(
            HTTP_status=206,
            status="downloaded_member_range",
            raw_file=metadata["raw_file"],
            output_file=metadata["raw_file"],
            checksum=sha256,
            records="full unfiltered CSV member",
            success="True",
            notes=(
                f"ZIP member CRC32 {config['member_crc32']} and uncompressed size "
                f"{config['member_uncompressed_size_bytes']} verified"
            ),
        )
        print(config["source_id"], 206, size, sha256)
    except Exception as exc:
        if raw_part.exists():
            raw_part.unlink()
        row.update(
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            HTTP_status=getattr(exc, "code", ""),
        )
        raise
    finally:
        append_log(row)


if __name__ == "__main__":
    main()
