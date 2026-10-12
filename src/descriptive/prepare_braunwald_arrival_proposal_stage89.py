"""Human-validation proposal, not an approved route endpoint or analytical row."""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from bs4 import BeautifulSoup
from pyproj import Transformer
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.prepare_native_snow_weights_stage69 import digest as sha
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS
from src.data_processing.build_public_transport_stop_context import checked_source, load_stops, exact_metadata

SOURCE = 'NATIONAL_BRAUNWALD_ARRIVAL_STAGE89'
OUTPUT = 'reports/braunwald_road_arrival_proposal_stage89.json'


def main():
    files = []
    for p in (ROOT / 'data_external/source_evidence').glob(SOURCE + '_*.metadata.json'):
        m = json.loads(p.read_text(encoding='utf-8'))
        if m['source_id'] == SOURCE:
            files.append((p, m))
    if len(files) != 1:
        raise ValueError('One original operator access page required')
    path, metadata = files[0]
    if sha(metadata['raw_file']) != metadata['sha256'] or metadata['http_status'] != 200:
        raise ValueError('Operator evidence differs')
    html = BeautifulSoup((ROOT / metadata['raw_file']).read_text(encoding='utf-8'), 'html.parser').get_text(' ', strip=True)
    if not all(t in html for t in ['Braunwald ist autofrei', 'Zufahrt für den Privatverkehr ist nur bis Linthal möglich', 'Talstation der Braunwald-Standseilbahn']):
        raise ValueError('No certified public-car valley-access statement')
    cfg = json.loads((ROOT / 'config/path_c_analysis.json').read_text(encoding='utf-8'))
    archive = checked_source(cfg)
    stops, _, _ = load_stops(archive)
    selected = stops[stops.Numero.eq('8503260')]
    if len(selected) != 1:
        raise ValueError('Unique published funicular base station required')
    p = selected.iloc[0]
    if p.Nom != 'Linthal Braunwaldbahn (Talst.)' or p.MoyenTransport_Code != 'F':
        raise ValueError('Published BAV point identity differs')
    longitude, latitude = Transformer.from_crs(2056, 4326, always_xy=True).transform(float(p.E), float(p.N))
    bav = exact_metadata('BAV_PUBLIC_TRANSPORT_STOPS_2026')
    inputs = {s: sha(s) for s in ['src/descriptive/prepare_braunwald_arrival_proposal_stage89.py',
              'config/national_arrival_sources_stage89.json', 'config/national_urban_reference_decision_stage89.json',
              'config/path_c_analysis.json', path.relative_to(ROOT).as_posix(), metadata['raw_file'], bav['raw_file']]}
    proposal = dict(prepared_at=datetime.now(timezone.utc).isoformat(), input_sha256=inputs,
                    status='exact_arrival_point_validation_pending_no_route_requested', resort_id='braunwald',
                    source_id=SOURCE, operator_url=metadata['url'], coordinate_source_id='BAV_PUBLIC_TRANSPORT_STOPS_2026',
                    coordinate_state_date='2026-09-20', proposed_stop_id='8503260', proposed_stop_name=p.Nom,
                    proposed_stop_mode_source=p.MoyenTransport_Code,
                    bav_easting_2056=float(p.E), bav_northing_2056=float(p.N),
                    proposed_longitude_wgs84=longitude, proposed_latitude_wgs84=latitude,
                    coordinate_conversion='Published LV95 EPSG2056 toEPSG4326, no invented coordinate or interpolation',
                    rationale='Operator explicitly permits public-car access only to Linthal; original BAV point is the funicular valley departure next to the documented parking/access area',
                    nearest_listing_stop_not_selected=dict(stop_id='8530956', name='Grotzenbüel (Seblengrat)',
                                                          mode='H chairlift', reason='Nearest geographic stop is not a validated public-car arrival'),
                    proposed_measure='Six approved city stops to Linthal funicular base stop, same static directional car reference; source snap distances and limitations published',
                    onward_access='Funicular to Braunwald and internal transfer to pistes remain separate, duration not measured/not added/not zero-filled',
                    proposed_measure_not_complete_city_to_piste_travel_time=True,
                    no_new_ORS_call_domain_exclusion_or_old_endpoint_overwrite=True)
    output = ROOT / OUTPUT
    if output.exists():
        previous = json.loads(output.read_text(encoding='utf-8'))
        if previous['input_sha256'] != inputs:
            raise ValueError('Frozen proposal differs; create a new version')
    else:
        output.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sources = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    if SOURCE not in set(sources.source_id):
        record = dict(source_id=SOURCE, variable_name='documented_Braunwald_public_car_access_arrival_review',
                      variable_description='Official public-car access to Linthal only, adjacent published funicular valley stop proposed for validation; no route measurement',
                      source_organisation=metadata['organisation'], source_page_url=metadata['url'],
                      retrieval_method='Checkpointed GET of literal link from existing official operator page; source robots respected',
                      retrieval_date=metadata['retrieval_date'], local_raw_file=metadata['raw_file'], processed_file=OUTPUT,
                      geographic_level='Literal documented operator access point, not inferred municipal tourism catchment',
                      temporal_resolution='Current operator/BAV2026access proposal, not historically verified travel time',
                      license='Publisher rights; BAV coordinate OGD attribution retained',
                      quality_notes='Car reference ends at valley departure, not actual alpine pistes; onward transfer missing, not invented or silently added',
                      manual_verification='Original SHA/operator vehicle restriction, BAV stop8503260modeF/source archive/provider multihash/CRS verified',
                      confidence_level='Sourced point proposal awaiting researcher validation, not a used endpoint',
                      notes='Parent NATIONAL_BRAUNWALD_WINTER_STAGE88; BAV_PUBLIC_TRANSPORT_STOPS_2026; ' + OUTPUT)
        write_csv(pd.concat([sources, pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    print(json.dumps({k: v for k, v in proposal.items() if k != 'input_sha256'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
