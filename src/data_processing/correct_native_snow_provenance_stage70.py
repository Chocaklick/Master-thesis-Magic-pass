"""Explicit documentary repair only to newly appended Stage70 source records."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.summarise_terrain_reference_stage67 import row_digest


def main():
    config=json.loads((ROOT/'config/native_snow_provenance_corrections_stage70.json').read_text(encoding='utf8'))
    summary=json.loads((ROOT/'reports/native_snow_values_stage70_summary.json').read_text(encoding='utf8'))
    path=ROOT/'metadata/data_sources_master.csv'
    frame=pd.read_csv(path,dtype=str,keep_default_na=False)
    n=config['prior_source_rows_protected']
    expected=summary['prior_registry_rows_and_digest']['metadata/data_sources_master.csv']
    if n!=expected['rows'] or row_digest(frame.iloc[:n])!=expected['sha256']:
        raise ValueError('Prior source rows changed')
    changed=False
    for c in config['corrections']:
        rows=frame.index[frame.source_id.eq(c['source_id'])].tolist()
        if len(rows)!=1 or rows[0]<n or c['field'] not in frame.columns:
            raise ValueError('Only existing new Stage70 row/valid column allowed')
        value=frame.at[rows[0],c['field']]
        if value==c['new']:
            continue
        if value!=c['old']:
            raise ValueError('Unexpected documentary value')
        frame.at[rows[0],c['field']]=c['new'];changed=True
    if changed:
        write_csv(frame,path)
    print(json.dumps(dict(date='2026-10-10',source_rows=len(frame),prior_rows_exact=n,documentary_cells=len(config['corrections']),changed=changed)))


if __name__=='__main__':
    main()
