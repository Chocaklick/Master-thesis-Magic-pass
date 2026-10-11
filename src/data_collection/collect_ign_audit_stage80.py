"""Archive small official IGN evidence; no raster download or source combination."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data_collection import collect_evidence
from src.data_collection.collect_reviewed_terrain_catalogue_stage80 import atomic_log

if __name__=='__main__':
    collect_evidence.append_log=atomic_log
    collect_evidence.main()
