"""Literal provider asset queue; both pilot editions retained for comparison."""
import json,re,sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha


def main():
    parent=json.loads((ROOT/'reports/terrain_catalogue_stage61_summary.json').read_text(encoding='utf8'))
    for p,h in {**parent['input_sha256'],**parent['output_sha256']}.items():
        if sha(p)!=h:raise ValueError('Frozen pilot catalogue changed')
    decision=json.loads((ROOT/'config/terrain_vintage_decisions_stage62.json').read_text(encoding='utf8'))
    if not decision['researcher_reply']:raise ValueError('Require vintage approval')
    frame=pd.read_csv(ROOT/'data_processed/terrain_stluc_native2m_asset_inventory_stage61.csv',dtype=str,keep_default_na=False)
    frame['native_tile_key']=frame.asset_id.str.extract(r'^swissalti3d_\d{4}_(\d+-\d+)_')[0]
    if frame.native_tile_key.isna().any():raise ValueError('Unknown literal tile identifier format')
    latest=frame.groupby('native_tile_key').item_reference_datetime.max().to_dict()
    records=[]
    # Pair editions per tile for immediate matching/header verification.
    for r in frame.sort_values(['native_tile_key','item_reference_datetime'],ascending=[True,False]).itertuples():
        records.append(dict(source_id='SWISSTOPO_ALTI3D_TILE_STAGE62_'+r.asset_id.removesuffix('.tif').upper(),url=r.asset_url,organisation='Office fédéral de topographie swisstopo',suffix='tif',expected_sha256=r.asset_sha256,native_tile_key=r.native_tile_key,item_reference_datetime=r.item_reference_datetime,asset_created_datetime=r.asset_created_datetime,asset_updated_datetime=r.asset_updated_datetime,asset_id=r.asset_id,reference_edition=r.item_reference_datetime==latest[r.native_tile_key],purpose='Approved native2m current terrain diagnostic/reference versus pilotcomparison; not verifiedpreentry',parent_source_id='SWISSTOPO_ALTI3D_STLUC_ITEMS_STAGE61'))
    target=ROOT/'config/terrain_tile_sources_stage62.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8'))!=records:raise ValueError('Frozen tile queue differs')
    else:target.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(len(records),'literal native2m assets; both editions retained; no guessed URLs.')


if __name__=='__main__':main()
