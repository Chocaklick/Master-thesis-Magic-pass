"""Plan all directional ORS batches; never call an API or invent coordinates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_accessibility_road_reference import sha, OUTPUTS
from src.data_collection.road_reference_credentials import load_credential

CONFIG = "config/accessibility_road_routing.json"
PLAN = "reports/accessibility_road_matrix_plan.json"


def plan_batches(municipality_ids, access_ids, size):
    if size < 1 or size > 25:
        raise ValueError("Operational block size must be 1..25")
    if len(set(municipality_ids)) != len(municipality_ids) or len(set(access_ids)) != len(access_ids):
        raise ValueError("Duplicate endpoint identifiers")
    batches = []
    for i in range(0, len(municipality_ids), size):
        for j in range(0, len(access_ids), size):
            for direction in ["outbound", "return"]:
                origin_ids = municipality_ids[i:i + size]
                arrival_ids = access_ids[j:j + size]
                batches.append(dict(batch_id=f"{direction}_{i:04}_{j:04}", direction=direction,
                    municipality_bfs_ids=origin_ids, access_point_ids=arrival_ids,
                    requested_cells=len(origin_ids) * len(arrival_ids)))
    return batches


def main():
    config = json.loads((ROOT / CONFIG).read_text(encoding="utf-8"))
    origin_path, arrival_path = OUTPUTS.values()
    origins = pd.read_csv(ROOT / origin_path, keep_default_na=False)
    arrivals = pd.read_csv(ROOT / arrival_path, keep_default_na=False)
    ids = sorted(int(v) for v in origins.municipality_bfs_id)
    access_ids = sorted(arrivals.access_point_id.tolist())
    batches = plan_batches(ids, access_ids, config["block_size"])
    ready_origins = set(origins.loc[origins.road_origin_status.eq("verified_documented_administrative_centre"), "municipality_bfs_id"])
    ready_arrivals = set(arrivals.loc[arrivals.road_arrival_status.eq("verified_documented_road_arrival"), "access_point_id"])
    for batch in batches:
        batch["ready_for_execution"] = (set(batch["municipality_bfs_ids"]).issubset(ready_origins)
            and set(batch["access_point_ids"]).issubset(ready_arrivals))
    credential, credential_location = load_credential(config)
    credential_present = credential is not None
    plan = dict(status="planning_only_no_api_request", provider=config["provider"],
        endpoint=config["api_endpoint"], profile=config["profile"],
        all_endpoints_planned_batches=len(batches), all_endpoints_planned_directional_cells=sum(b["requested_cells"] for b in batches),
        ready_origin_count=len(ready_origins), ready_arrival_count=len(ready_arrivals),
        ready_batches=sum(b["ready_for_execution"] for b in batches),
        local_credential_environment_present=credential_present,
        credential_location=credential_location,
        note="Pending endpoints remain represented. In later collection, verified subsets may be requested without dropping unresolved endpoints; current batch readiness is a collection status, not a municipality filter.",
        input_sha256={p: sha(p) for p in [CONFIG, origin_path, arrival_path]},
        batches=batches)
    (ROOT / PLAN).write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in plan.items() if k not in ["batches", "input_sha256", "note"]}))


if __name__ == "__main__":
    main()
