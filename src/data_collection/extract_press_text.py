"""Extract page-numbered text from cached official PDFs; never infer entry dates."""
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]


def main():
    target = ROOT / "data_interim/press_text"
    target.mkdir(parents=True, exist_ok=True)
    for metadata_path in sorted((ROOT / "data_external/source_evidence").glob("MAGIC_*.metadata.json")):
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata.get("suffix") != "pdf":
            continue
        reader = PdfReader(ROOT / metadata["raw_file"])
        pages = [{"page": i + 1, "text": page.extract_text() or ""} for i, page in enumerate(reader.pages)]
        (target / (metadata["source_id"] + ".json")).write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
        print(metadata["source_id"], len(pages), "pages")


if __name__ == "__main__":
    main()
