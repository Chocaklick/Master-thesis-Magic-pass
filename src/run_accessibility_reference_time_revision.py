"""Resume v2 routing, then enrich final provenance with independent walk review.

This wrapper does not change the routing fingerprint, so checkpoints remain
reusable when only the independently collected literature review is updated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/data_processing"))
import build_accessibility_reference_time_v2 as routing
import build_accessibility_mobility_review as review


def main():
    routing.main()
    path = ROOT / routing.MANIFEST
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not manifest["status"].startswith("completed_"):
        return
    output_paths = dict(routing.OUTPUTS)
    review.main()
    manifest["output_sha256"] = {p: routing.sha(p) for p in output_paths.values()}
    manifest["output_row_counts"]["accessibility_reference_time_v2_local_review"] = len(pd.read_csv(ROOT / output_paths["accessibility_reference_time_v2_local_review"]))
    manifest["independent_walking_review_enriched"] = True
    manifest["local_walking_review_sha256"] = routing.sha("config/accessibility_local_walking_evidence_review.json")
    manifest["literature_review_sha256"] = routing.sha("config/accessibility_mobility_literature_review.json")
    if manifest["protected_legacy_sha256"] != {p: routing.sha(p) for p in routing.PROTECTED}:
        raise RuntimeError("Legacy outputs changed during revision")
    source_path = ROOT / "metadata/data_sources_master.csv"
    sources = pd.read_csv(source_path, dtype=str, keep_default_na=False)
    sources.loc[sources.source_id.eq(routing.SOURCE), "processed_file"] = "|".join(output_paths.values())
    sources.to_csv(source_path, index=False, lineterminator="\n")
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Completed routing, enriched walk evidence, source/variable registration and legacy SHA checks", flush=True)


if __name__ == "__main__":
    main()
