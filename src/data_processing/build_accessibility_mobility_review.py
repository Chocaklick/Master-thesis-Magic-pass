"""Publish the completed evidence review independently of long-running routing."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/data_processing"))
import build_accessibility_reference_time_v2 as v2


def main():
    local = pd.read_csv(ROOT / "reports/accessibility_local_node_audit.csv")
    local["actual_local_duration_minutes"] = np.nan
    local["endpoint_evidence_status"] = "actual_origin_departure_and_walking_duration_to_document"
    local["documented_outbound_walk_minutes"] = np.nan
    local["documented_return_walk_minutes"] = np.nan
    local["walking_evidence_source_id"] = ""
    local["walking_evidence_locator"] = ""
    local["walking_evidence_applicability"] = ""
    review = json.loads((ROOT / "config/accessibility_local_walking_evidence_review.json").read_text(encoding="utf-8"))
    for evidence in review:
        chosen = local.municipality_bfs_id.eq(evidence["municipality_bfs_id"]) & local.same_stop_local_candidate
        if chosen.sum() != 1:
            raise ValueError("Reviewed local case must resolve to one existing local candidate")
        for direction in ["outbound", "return"]:
            local.loc[chosen, f"documented_{direction}_walk_minutes"] = evidence[direction + "_walk_minutes"]
        local.loc[chosen, "walking_evidence_source_id"] = evidence["source_id"]
        local.loc[chosen, "walking_evidence_locator"] = evidence["locator"]
        local.loc[chosen, "walking_evidence_applicability"] = evidence["applicability"]
        local.loc[chosen, "endpoint_evidence_status"] = "positive_source_evidence_not_yet_validated_for_two_direction_winter_metric"
    literature = pd.DataFrame(json.loads((ROOT / "config/accessibility_mobility_literature_review.json").read_text(encoding="utf-8")))
    v2.OUTPUTS = {k: p for k, p in v2.OUTPUTS.items() if k.endswith("local_review") or k == "accessibility_mobility_literature"}
    # New columns have explicit definitions. v2.register inherits definitions
    # already in the central dictionary, so seed these own fields without
    # overwriting unrelated variables, then register only these actual outputs.
    from src.data_processing.update_accessibility_expansion_provenance import DICTIONARY_COLUMNS
    dictionary_path = ROOT / "metadata/data_dictionary.csv"
    dictionary = pd.read_csv(dictionary_path, dtype=str, keep_default_na=False)
    descriptions = {
        "documented_outbound_walk_minutes": ("Published outward actual local walking duration; source period/applicability explicit, not automatically applied", "minutes"),
        "documented_return_walk_minutes": ("Published reverse local walking duration if independently documented; missing is not assumed symmetric", "minutes"),
        "walking_evidence_source_id": ("Primary identifier for local walking/endpoint evidence", "identifier"),
        "walking_evidence_locator": ("Specific source section/page supporting actual local endpoint or duration", "text"),
        "walking_evidence_applicability": ("Exact endpoint, season, direction and historical applicability limits", "text"),
    }
    seeded = []
    for field, (description, unit) in descriptions.items():
        seeded.append(dict(variable=field, table="accessibility_reference_time_v2_local_review", description=description,
            unit=unit, data_type=str(local[field].dtype), source_id=v2.SOURCE,
            geographic_level="existing local access-point candidate", temporal_level="source-specific current/historical evidence",
            raw_or_derived="documented source evidence", formula="No inferred reverse time or seasonal equivalence",
            causal_role="local access review only", missing_share=f"{local[field].isna().mean():.6f}",
            notes="Not applied to the winter reference pending explicit applicability.") )
    dictionary = dictionary[~(dictionary.table.eq("accessibility_reference_time_v2_local_review") & dictionary.variable.isin(descriptions))]
    pd.concat([dictionary, pd.DataFrame(seeded).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna("").to_csv(dictionary_path, index=False, lineterminator="\n")
    frames = dict(zip(v2.OUTPUTS, [local, literature]))
    for table, frame in frames.items():
        frame.to_csv(ROOT / v2.OUTPUTS[table], index=False, lineterminator="\n")
    v2.register(frames)
    # Preserve immutable responses, but distinguish an HTTP-200 challenge page
    # from an archived study. RERO's HTTP410 is recorded, not called success.
    path = ROOT / "metadata/data_sources_master.csv"
    sources = pd.read_csv(path, dtype=str, keep_default_na=False)
    sources.loc[sources.source_id.eq("TOGGENBURG_VISITOR_MOBILITY_SURVEY_2025"), "quality_notes"] += " Archived HTTP200 body is a 3038-byte Client Challenge, not study content. Findings inspected via web primary page; no local full-study snapshot claimed."
    sources.loc[sources.source_id.eq("SAINT_BERNARD_SKI_MOBILITY_SURVEY_2008_WP2010"), "quality_notes"] += " Direct local collector received HTTP410; web primary PDF remains readable. No downloaded original or local SHA claimed."
    sources.loc[sources.source_id.eq("ATE_RIDE_GLIDE_LAST_MILE_2010_2011"), "quality_notes"] += " Local archiving blocked by robots.txt and not bypassed; primary guide inspected through web. Historical measured walking time, not a 2026 measurement."
    sources.to_csv(path, index=False, lineterminator="\n")
    manifest_path = ROOT / v2.MANIFEST
    completed = manifest_path.exists() and json.loads(manifest_path.read_text(encoding="utf-8"))["status"].startswith("completed_")
    print(json.dumps({"completed_review_rows": {k: len(f) for k, f in frames.items()}, "routing_complete": completed}))


if __name__ == "__main__":
    main()
