"""Refresh only Stage76 registration statistics after a completed calculation.

Run after collection stops; preserve earlier definitions and historical rows.
The numerical worker is frozen because its SHA protects existing value caches.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.compare_snow_multiwinter_stage76 import DEFS, OUTPUT, SUMMARY, SOURCE, CONFIG
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest
from src.data_collection.collect_oshd_multiwinter_stage76 import single_collector_lock, FOLDER


def refresh(dictionary, result):
    """Preserve all rows outside the exact new table/source namespace."""
    updated = dictionary.copy()
    for col in DEFS:
        mask = updated.table.eq('snow_multiwinter_comparison_stage76') & updated.variable.eq(col) & updated.source_id.eq(SOURCE)
        if mask.sum() != 1:
            raise ValueError('Require one registered Stage76 field: '+col)
        updated.loc[mask, 'missing_share'] = f'{result[col].isna().mean():.6f}'
        updated.loc[mask, 'data_type'] = str(result[col].dtype)
    return updated


def sync():
    collection = json.loads((ROOT/'reports/oshd_multiwinter_collection_stage76_summary.json').read_text(encoding='utf8'))
    if any(f['status']=='collecting' for f in collection['files']):
        raise ValueError('Wait for collector to stop before shared registry updates')
    state = json.loads((ROOT/SUMMARY).read_text(encoding='utf8'))
    if state['output_sha256'][OUTPUT] != digest(OUTPUT):
        raise ValueError('Calculation checkpoint changed')
    result = pd.read_csv(ROOT/OUTPUT)
    path = ROOT/'metadata/data_dictionary.csv'
    original = pd.read_csv(path, dtype=str, keep_default_na=False)
    updated = refresh(original, result)
    if not original.equals(updated):
        write_csv(updated, path)
    print(json.dumps(dict(updated_table='snow_multiwinter_comparison_stage76', fields=len(DEFS),
                         completed_water_years=state['completed_water_years'],
                         other_tables_unchanged=True, config=CONFIG)))


def main():
    with single_collector_lock(FOLDER):
        sync()


if __name__=='__main__':
    main()
