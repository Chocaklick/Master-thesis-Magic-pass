"""One literal latest reference asset per native tile, cached originals reused."""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha


def main():
    previous = json.loads((ROOT / 'reports/terrain_catalogue_extension_stage65_summary.json').read_text(encoding='utf8'))
    for p, h in {**previous['input_sha256'], **previous['output_sha256']}.items():
        if sha(p) != h:
            raise ValueError('Frozen catalogue changed: ' + p)
    inventory = pd.read_csv(ROOT / 'data_processed/terrain_group_native2m_asset_inventory_stage65.csv')
    selected = inventory[inventory.latest_reference_for_native_tile].copy()
    queue = []
    for url, part in selected.groupby('asset_url', sort=True):
        if part.asset_sha256.nunique() != 1 or part.native_tile_key.nunique() != 1 or part.item_reference_datetime.nunique() != 1:
            raise ValueError('Conflicting selected asset; no arbitrary first-match choice')
        r = part.iloc[0]
        cache_ids = part.cached_original_tile_source_id.dropna().unique()
        if len(cache_ids) > 1:
            raise ValueError('Ambiguous cached original')
        sid = cache_ids[0] if len(cache_ids) else 'SWISSTOPO_ALTI3D_TILE_STAGE66_' + r.asset_id.removesuffix('.tif').upper()
        queue.append(dict(source_id=sid, url=url, organisation='Office fédéral de topographie swisstopo', suffix='tif',
                          expected_sha256=r.asset_sha256, native_tile_key=r.native_tile_key, asset_id=r.asset_id,
                          item_reference_datetime=r.item_reference_datetime, asset_created_datetime=r.asset_created_datetime if pd.notna(r.asset_created_datetime) else None,
                          asset_updated_datetime=r.asset_updated_datetime if pd.notna(r.asset_updated_datetime) else None,
                          reference_edition=True, station_group_ids=sorted(part.station_group_id.unique()),
                          parent_source_ids=sorted(part.catalogue_page_source_id.unique()),
                          purpose='Approved latest-per-native-tile2m observed reference; not preentry-certified; mixed-edition gradient convention still requires audit'))
    by_native = {}
    for source in queue:
        if source['native_tile_key'] in by_native:
            raise ValueError('Several latest reference assets per native tile; review catalogue coverage')
        by_native[source['native_tile_key']] = source
    target = ROOT / 'config/terrain_reference_tile_sources_stage66.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8')) != queue:
            raise ValueError('Frozen reference queue differs')
    else:
        target.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(dict(reference_assets=len(queue), reused_originals=sum(s['source_id'].startswith('SWISSTOPO_ALTI3D_TILE_STAGE62_') for s in queue),
                         new_asset_requests=sum(s['source_id'].startswith('SWISSTOPO_ALTI3D_TILE_STAGE66_') for s in queue),
                         no_duplicate_literal_asset_download=True)))


if __name__ == '__main__':
    main()
