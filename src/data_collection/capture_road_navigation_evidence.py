"""Archive an operator-linked navigation redirect, without visiting Google Maps.

The URL is read from the already archived operator arrival page, not invented.
"""
import base64
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_accessibility_road_reference import archived_metadata


def main():
    sid = "HASLIBERG_TWING_OFFICIAL_NAVIGATION_REDIRECT_2026"
    folder = ROOT / "data_external/source_evidence"
    if list(folder.glob(sid + "_*.metadata.json")):
        archived_metadata(sid)
        print(sid, "cached")
        return
    parent = archived_metadata("MEIRINGEN_HASLIBERG_OFFICIAL_ARRIVAL_2026")
    soup = BeautifulSoup((ROOT / parent["raw_file"]).read_bytes(), "html.parser")
    links = [a for a in soup.find_all("a", href=True)
             if a["href"] == "https://maps.app.goo.gl/ix54i6g3jhi21jSr5"]
    if not links or not any("Twing" in a.parent.get_text(" ", strip=True) for a in links):
        raise ValueError("Operator parking link or Twing identity is no longer evidenced")
    url = links[0]["href"]
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    try:
        response = build_opener(NoRedirect).open(Request(url), timeout=30)
    except HTTPError as exc:
        response = exc
    if response.code not in (301, 302, 303, 307, 308):
        raise ValueError(f"Expected navigation redirect, received HTTP {response.code}")
    stamp = datetime.now(timezone.utc)
    raw = folder / f"{sid}_{stamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    envelope = {"url": url, "status": response.code,
                "location": response.headers.get("Location"),
                "body_base64": base64.b64encode(response.read()).decode("ascii")}
    content = (json.dumps(envelope, ensure_ascii=False, indent=2) + "\n").encode()
    with raw.open("xb") as stream:
        stream.write(content)
    metadata = dict(source_id=sid, source_url=url, final_url=url,
                    retrieval_date=stamp.isoformat(), raw_file=raw.relative_to(ROOT).as_posix(),
                    sha256=hashlib.sha256(content).hexdigest(),
                    retrieval_method="Single GET without following redirect; response Location and original body archived in JSON envelope",
                    parent_source_id="MEIRINGEN_HASLIBERG_OFFICIAL_ARRIVAL_2026")
    with raw.with_suffix(".metadata.json").open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"source_id": sid, "navigation_target": envelope["location"]}))


if __name__ == "__main__":
    main()
