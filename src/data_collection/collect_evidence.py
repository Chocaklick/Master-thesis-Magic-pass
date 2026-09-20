"""Fetch a small configured evidence set, preserving originals and every outcome."""
from __future__ import annotations

import csv
import argparse
import hashlib
from http.client import IncompleteRead
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[2]
AGENT = "ThesisSkiResearch/0.1 (academic source verification)"
LOG_COLUMNS = ["timestamp", "task", "source_id", "source", "source_url", "URL/API", "request",
    "retrieval_method", "HTTP_status", "status", "raw_file", "output_file", "checksum", "records",
    "rows_collected", "success", "error", "notes"]


def append_log(row):
    path = ROOT / "logs/data_collection_log.csv"
    old = list(csv.DictReader(path.open(encoding="utf-8", newline=""))) if path.exists() else []
    fields = list(dict.fromkeys(LOG_COLUMNS + [k for r in old for k in r]))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(old + [row])


def fetch(url):
    content = b""
    last_error = None
    for _ in range(4):
        headers = {"User-Agent": AGENT}
        if content:
            headers["Range"] = f"bytes={len(content)}-"
        with urlopen(Request(url, headers=headers), timeout=45) as response:
            status = response.status
            final_url = response.geturl()
            try:
                block = response.read()
            except IncompleteRead as exc:
                block = exc.partial
                last_error = exc
                if content and status == 206:
                    content += block
                else:
                    content = block
                continue
            if content and status == 206:
                content += block
            else:
                content = block
            return content, status, final_url
    if last_error:
        raise last_error
    raise RuntimeError(f"Download did not complete: {url}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/evidence_sources.json")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    sources = json.loads((ROOT / args.config).read_text(encoding="utf-8"))
    if args.limit is not None:
        sources = sources[:args.limit]
    folder = ROOT / "data_external/source_evidence"
    folder.mkdir(parents=True, exist_ok=True)
    policies = {}
    for source in sources:
        sid, url = source["source_id"], source["url"]
        cached = [
            path
            for path in sorted(folder.glob(sid + "_*.metadata.json"))
            if json.loads(path.read_text(encoding="utf-8")).get("source_id") == sid
        ]
        if cached:
            metadata = json.loads(cached[-1].read_text(encoding="utf-8"))
            raw = ROOT / metadata["raw_file"]
            if raw.exists() and hashlib.sha256(raw.read_bytes()).hexdigest() == metadata["sha256"]:
                print(sid, "cached")
                continue
            raise RuntimeError(f"Cached evidence integrity failure: {sid}")
        stamp = datetime.now(timezone.utc)
        row = {"timestamp": stamp.isoformat(), "task": "initial_source_verification", "source_id": sid,
               "source": source["organisation"], "source_url": url, "URL/API": url,
               "request": "GET", "retrieval_method": "urllib GET", "success": "False"}
        try:
            host = urlsplit(url)
            origin = f"{host.scheme}://{host.netloc}"
            if origin not in policies:
                robots_url = origin + "/robots.txt"
                try:
                    content, _, _ = fetch(robots_url)
                    parser = RobotFileParser()
                    parser.parse(content.decode("utf-8", errors="replace").splitlines())
                    policies[origin] = parser
                    robots_path = folder / (host.netloc + "_robots_" + stamp.strftime("%Y%m%dT%H%M%SZ") + ".txt")
                    with robots_path.open("xb") as stream:
                        stream.write(content)
                except HTTPError as exc:
                    if exc.code != 404:
                        raise
                    policies[origin] = None
            policy = policies[origin]
            if policy and not policy.can_fetch(AGENT, url):
                raise PermissionError("robots.txt disallows this request")
            delay = policy.crawl_delay(AGENT) if policy else None
            time.sleep(max(1, delay or 0))
            content, status, final_url = fetch(url)
            token = stamp.strftime("%Y%m%dT%H%M%SZ")
            raw = folder / f"{sid}_{token}.{source['suffix']}"
            with raw.open("xb") as stream:
                stream.write(content)
            metadata = {**source, "retrieval_date": stamp.isoformat(), "final_url": final_url,
                "raw_file": raw.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content), "http_status": status}
            with (folder / f"{sid}_{token}.metadata.json").open("x", encoding="utf-8") as stream:
                json.dump(metadata, stream, ensure_ascii=False, indent=2)
            row.update(HTTP_status=status, status="downloaded", raw_file=metadata["raw_file"],
                       output_file=metadata["raw_file"], checksum=metadata["sha256"], success="True")
            print(sid, status, len(content))
        except Exception as exc:
            row.update(status="failed", error=f"{type(exc).__name__}: {exc}", HTTP_status=getattr(exc, "code", ""))
            print(sid, row["error"])
        append_log(row)


if __name__ == "__main__":
    main()
