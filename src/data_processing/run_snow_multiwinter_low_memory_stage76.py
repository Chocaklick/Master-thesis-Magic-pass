"""Run the unchanged scientific worker with bounded runtime caches/threads.

Arguments, including --no-register, are passed through. Performance settings
only: same native values, masks, calendars and frozen numerical producer.
"""
import hashlib
import json
import os
import runpy
from datetime import datetime, timezone
from pathlib import Path

# Set before importing NumPy/Pandas/NetCDF; affect this process only.
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[name]='1'
import netCDF4
netCDF4.set_chunk_cache(1048576,101,0.75)

ROOT=Path(__file__).resolve().parents[2]
WORKER=ROOT/'src/data_processing/compare_snow_multiwinter_stage76.py'
SUMMARY=ROOT/'reports/snow_multiwinter_runtime_stage76_summary.json'


def main():
    import sys
    from src.data_collection.collect_oshd_multiwinter_stage76 import single_collector_lock
    folder=ROOT/'data_interim/snow_multiwinter_stage76/calculation_lock'
    folder.mkdir(parents=True,exist_ok=True)
    with single_collector_lock(folder):
        history=json.loads(SUMMARY.read_text(encoding='utf8')) if SUMMARY.exists() else {'runs':[]}
        row=dict(started_at=datetime.now(timezone.utc).isoformat(),arguments=sys.argv[1:],
                 worker_sha256=hashlib.sha256(WORKER.read_bytes()).hexdigest(),
                 launcher_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 threads=1,netcdf_chunk_cache_bytes=1048576,netcdf_cache_slots=101,
                 netcdf_preemption=0.75,scientific_method_changed=False,status='running')
        history['runs'].append(row)
        SUMMARY.write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        try:
            runpy.run_path(str(WORKER),run_name='__main__')
            row['status']='completed'
        except BaseException as exc:
            row.update(status='failed_or_interrupted',error=f'{type(exc).__name__}: {exc}')
            raise
        finally:
            row['ended_at']=datetime.now(timezone.utc).isoformat()
            SUMMARY.write_text(json.dumps(history,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':
    import sys
    sys.path.insert(0,str(ROOT))
    main()
