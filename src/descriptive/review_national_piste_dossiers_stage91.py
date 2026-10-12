"""Visual source review aid only; no nearest-name or automatic domain acceptance."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'data_interim/matplotlib_stage91'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from pyproj import Transformer
from src.descriptive.audit_completed_piste_membership import audit
from src.descriptive.prepare_national_documentary_queue_stage88 import CASES
from src.descriptive.check_national_preparation_stage87 import sha


def main():
    original = json.loads((ROOT / 'data_interim/current_piste_geometry_collection_checkpoint.json').read_text(encoding='utf-8'))
    extra = json.loads((ROOT / 'reports/piste_missing_member_collection_summary.json').read_text(encoding='utf-8'))
    for m in [original, extra]:
        if sha(m['raw_file']) != m['sha256']:
            raise ValueError('OSM source changed')
    first = json.loads((ROOT / original['raw_file']).read_text(encoding='utf-8'))
    second = json.loads((ROOT / extra['raw_file']).read_text(encoding='utf-8'))
    _, sites = audit(first, second)
    sites = {s['osm_relation_id']: s for s in sites}
    index = {(e['type'], e['id']): e for e in first['elements'] + second['elements']}
    listings = pd.read_csv(ROOT / 'data_processed/resort_master.csv').set_index('resort_id')
    convert = Transformer.from_crs(4326, 2056, always_xy=True)
    details = []
    folder = ROOT / 'data_interim/national_scope_stage91'
    folder.mkdir(parents=True, exist_ok=True)
    for rid, (site_id, _) in CASES.items():
        s = sites[site_id]
        lifts = [index[(m['type'], m['id'])] for m in s['member_references_outside_query']
                 if (m['type'], m['id']) in index and index[(m['type'], m['id'])].get('tags', {}).get('aerialway')]
        fig, ax = plt.subplots(figsize=(8, 6))
        for e, color in [(index[('way', i)], '#8c8c8c') for i in s['selected_downhill_way_ids']] + [(e, '#1764a0') for e in lifts]:
            geometry = e.get('geometry', [])
            if len(geometry) < 2:
                continue
            x, y = convert.transform([p['lon'] for p in geometry], [p['lat'] for p in geometry])
            ax.plot([v / 1000 for v in x], [v / 1000 for v in y], color=color, lw=1)
            if color == '#1764a0':
                ax.text(x[0] / 1000, y[0] / 1000, f"{e['id']} {e.get('tags', {}).get('name', '')}", fontsize=6)
        row = listings.loc[rid]
        x, y = convert.transform(row.longitude, row.latitude)
        ax.scatter(x / 1000, y / 1000, marker='x', color='#d45125')
        ax.set_title(rid + ': objets de descente gris / remontées bleues\nPoint catalogue orange, ni origine routière ni filtre')
        ax.set_aspect('equal', adjustable='datalim')
        ax.set_xlabel('Est LV95 (km)'); ax.set_ylabel('Nord LV95 (km)')
        fig.tight_layout()
        path = folder / (rid + '_scope_review.png')
        fig.savefig(path, dpi=130); plt.close(fig)
        details.append(dict(resort_id=rid, osm_site_relation_id=site_id, map_path=path.relative_to(ROOT).as_posix(),
                            downhill_way_ids=s['selected_downhill_way_ids'],
                            lift_member_tags=[dict(osm_way_id=e['id'], tags=e.get('tags', {})) for e in lifts],
                            ambiguous_flags=[dict(osm_way_id=i, tags=index[('way', i)].get('tags', {})) for i in s['selected_downhill_way_ids']
                                             if any(k in index[('way', i)].get('tags', {}) for k in ['disused', 'abandoned', 'fixme', 'note'])],
                            site_assignment_accepted=False, metric_profile_computed=False))
    path = folder / 'visual_review_aids.json'
    path.write_text(json.dumps(details, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Six source maps produced for manual review, no domain assignment or analytical measurements')


if __name__ == '__main__':
    main()
