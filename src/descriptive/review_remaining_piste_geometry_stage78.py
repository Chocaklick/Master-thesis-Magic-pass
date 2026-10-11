"""Offline review aids for the 30 remaining groups; never auto-assign geometries.

The 10 km window is a display/search aid only, not an analytical membership
criterion. All original objects and all 70 analytical groups remain unchanged.
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'data_interim/matplotlib_stage78'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from pyproj import Transformer
from shapely.geometry import LineString, Point
from src.descriptive.review_piste_candidates_stage53 import originals
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv


def main():
    folder = ROOT/'data_interim/piste_remaining_stage78'
    folder.mkdir(parents=True, exist_ok=True)
    assignment = pd.read_csv(ROOT/'data_processed/winter_profile_piste_assignment_stage60.csv', dtype=str, keep_default_na=False)
    points = pd.read_csv(ROOT/'data_processed/accessibility_station_access_points_stage55.csv', keep_default_na=False)
    pending = assignment[assignment.current_site_correspondence_verified.eq('False') | assignment.station_group_id.str.contains('sainte_croix')]
    if len(pending) != 30:
        raise ValueError('Retained 30-group review scope changed')
    index, counts, sites = originals()
    transform = Transformer.from_crs(4326, 2056, always_xy=True)
    shapes = {}
    site_membership = {}
    for site_id, site in sites.items():
        for way_id in site['selected_downhill_way_ids']:
            site_membership.setdefault(way_id, []).append(site_id)
    for (kind, way_id), element in index.items():
        geom = element.get('geometry', [])
        if kind != 'way' or len(geom) < 2 or not all('lon' in p and 'lat' in p for p in geom):
            continue
        if element.get('tags', {}).get('piste:type') != 'downhill' and not element.get('tags', {}).get('aerialway'):
            continue
        x, y = transform.transform([p['lon'] for p in geom], [p['lat'] for p in geom])
        shapes[way_id] = LineString(zip(x, y))
    configs = []
    for name in ['piste_operator_evidence_stage53', 'piste_operator_scope_evidence_stage53', 'piste_operator_alternative_evidence_stage53', 'piste_operator_deep_scope_evidence_stage53']:
        configs.extend(json.loads((ROOT/f'config/{name}.json').read_text(encoding='utf-8')))
    records = []
    details = []
    for row in pending.itertuples():
        references = points[points.station_group_id.eq(row.station_group_id)]
        origins = [Point(*transform.transform(r.reference_longitude, r.reference_latitude)) for r in references.itertuples()]
        selected = []
        for way_id, shape in shapes.items():
            distance = min(p.distance(shape) for p in origins)
            if distance <= 10000:
                element = index[('way', way_id)]
                selected.append(dict(osm_way_id=way_id, original_tags=element.get('tags', {}), review_distance_m=distance,
                    site_relation_ids=site_membership.get(way_id, []), geometry_lv95=list(shape.coords)))
        selected.sort(key=lambda r: (r['review_distance_m'], r['osm_way_id']))
        official = [s for s in configs if s.get('station_group_id') == row.station_group_id or any(p.get('station_group_id') == row.station_group_id for p in s.get('official_group_links', []))]
        figure = f'reports/figures/piste_remaining_stage78_{len(details)+1:02d}.png'
        fig, ax = plt.subplots(figsize=(10, 8))
        nearby = [r for r in selected if r['review_distance_m'] <= 6000]
        for r in nearby:
            coords = r['geometry_lv95']; tags = r['original_tags']
            lift = bool(tags.get('aerialway'))
            ax.plot([c[0]/1000 for c in coords], [c[1]/1000 for c in coords], color='#1760a0' if lift else '#555555', lw=1.6 if lift else .7)
            middle = coords[len(coords)//2]
            label = str(r['osm_way_id']) + ' ' + tags.get('name', tags.get('piste:name', ''))
            ax.text(middle[0]/1000, middle[1]/1000, label[:55], fontsize=5.5, color='#1760a0' if lift else '#333333')
        for r, p in zip(references.itertuples(), origins):
            ax.scatter(p.x/1000, p.y/1000, color='#d84315', marker='x', s=50)
            ax.text(p.x/1000, p.y/1000, r.access_point_name, fontsize=7, color='#d84315')
        ax.set_aspect('equal', adjustable='datalim'); ax.ticklabel_format(useOffset=False, style='plain')
        ax.set_xlabel('Est LV95 (km)'); ax.set_ylabel('Nord LV95 (km)')
        ax.set_title(row.station_group_name+' — candidats, aucune attribution automatique', fontsize=11)
        fig.tight_layout(); fig.savefig(ROOT/figure, dpi=160); plt.close(fig)
        downhill = [r for r in selected if r['original_tags'].get('piste:type') == 'downhill']
        documents = []
        for s in official:
            metas = list((ROOT/'data_external/source_evidence').glob(s['source_id']+'_*.metadata.json'))
            documents.append(dict(source_id=s['source_id'], url=s['url'], archived=bool(metas), metadata_paths=[p.relative_to(ROOT).as_posix() for p in metas]))
        records.append(dict(station_group_id=row.station_group_id, station_group_name=row.station_group_name,
            previous_review_status=row.review_status, previous_review_note=row.review_note,
            candidate_downhill_objects_display_window=len(downhill), candidate_objects_without_site_relation=sum(not r['site_relation_ids'] for r in downhill),
            minimum_downhill_review_distance_m=min((r['review_distance_m'] for r in downhill), default=None),
            archived_official_document_count=sum(s['archived'] for s in documents), geometry_assignment_accepted=False,
            review_status='individual_review_pending', review_note='10 km diagnostic search window only; no assignment or absence claim',
            source_id='DERIVED_REMAINING_PISTE_REVIEW_STAGE78'))
        details.append(dict(station_group_id=row.station_group_id, station_group_name=row.station_group_name,
            original_pending_status=row.review_status, original_note=row.review_note, official_documents=documents,
            reference_points=references.to_dict('records'), candidate_objects=selected, diagnostic_map=figure))
    inputs = {p: sha(p) for p in ['data_processed/winter_profile_piste_assignment_stage60.csv',
        'data_processed/accessibility_station_access_points_stage55.csv', 'src/descriptive/review_remaining_piste_geometry_stage78.py',
        'config/piste_assignment_protocol_decisions_stage51.json']}
    path = folder/'candidate_inventory.json'
    path.write_text(json.dumps(dict(input_sha256=inputs, diagnostic_window_m=10000, automatic_assignment=False,
        all_70_groups_retained=True, cases=details), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    write_csv(pd.DataFrame(records), ROOT/'data_processed/piste_remaining_review_stage78.csv')
    print(pd.DataFrame(records)[['station_group_name','candidate_downhill_objects_display_window','candidate_objects_without_site_relation','minimum_downhill_review_distance_m','archived_official_document_count']].to_string(index=False))


if __name__ == '__main__':
    main()
