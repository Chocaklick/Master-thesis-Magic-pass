"""Rebuild the researcher-requested municipality/accessibility expansion.

Run from the project root. The expensive GTFS step resumes from per-group,
per-day caches in data_interim/accessibility_station_group_journeys/.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "src/descriptive/audit_accessibility_expansion.py",
    "src/data_processing/build_accessibility_station_groups.py",
    "src/data_processing/build_accessibility_station_group_journeys.py",
    "src/data_processing/build_accessibility_municipality_exposure.py",
    "src/causal_inference/audit_accessibility_identification.py",
    "src/causal_inference/build_accessibility_first_exposure_pretrend.py",
    "src/data_processing/build_accessibility_historical_access_worklist.py",
    "src/data_processing/build_accessibility_historical_gtfs_2018_routes.py",
    "src/data_processing/build_accessibility_historical_gtfs_2018_proximity_sensitivity.py",
    "src/data_processing/build_accessibility_historical_gtfs_2018_current_transfer_sensitivity.py",
    "src/causal_inference/build_accessibility_historically_screened_comparisons.py",
    "src/causal_inference/screen_accessibility_comparison_internal_risks.py",
    "src/data_processing/update_accessibility_expansion_provenance.py",
    "src/data_processing/update_provenance.py",
]


def main() -> None:
    for relative in SCRIPTS:
        path = ROOT / relative
        if not path.exists():
            raise FileNotFoundError(path)
        print(f"\n=== {relative} ===", flush=True)
        subprocess.run([sys.executable, str(path)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
