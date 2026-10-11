"""Reuse unchanged serial STAC collector in a separate checkpoint namespace."""
import sys
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_collection import collect_terrain_extension_stage65 as worker
import pandas as pd
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha


def atomic_log(row):
    """Same event cells, atomic destination replacement instead of truncate/write."""
    target=ROOT/'logs/data_collection_log.csv'
    old=pd.read_csv(target,dtype=str,keep_default_na=False)
    columns=list(dict.fromkeys([*old.columns,*row]))
    added=pd.DataFrame([row]).reindex(columns=columns).fillna('')
    write_csv(pd.concat([old.reindex(columns=columns).fillna(''),added],ignore_index=True),target)


def restore_unlogged_events():
    path=ROOT/'data_interim/terrain_catalogue_events_stage80.json'
    if not path.exists():return
    log=pd.read_csv(ROOT/'logs/data_collection_log.csv',dtype=str,keep_default_na=False)
    keys=set(zip(log.timestamp,log.source_id))
    for event in json.loads(path.read_text(encoding='utf-8')):
        key=(event['timestamp'],event['source_id'])
        if key in keys:continue
        if event['status']=='downloaded' and sha(event['raw_file'])!=event['checksum']:
            raise ValueError('Actual downloaded event proof differs')
        atomic_log(event);keys.add(key)
        print('Restored actual unlogged event without new request:',event['source_id'],flush=True)


if __name__=='__main__':
    restore_unlogged_events()
    worker.collect_evidence.append_log=atomic_log
    worker.CONFIG='config/terrain_group_catalogue_sources_stage80.json'
    worker.QUEUE='data_interim/terrain_catalogue_queue_stage80.json'
    worker.EVENTS='data_interim/terrain_catalogue_events_stage80.json'
    worker.main()
