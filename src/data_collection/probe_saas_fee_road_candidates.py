"""Probe sourced parking-stop candidates without changing any analytical endpoint."""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_accessibility_road_matrix import request_matrix, validate_response, ENDPOINT, digest
from src.data_collection.road_reference_credentials import load_credential
from src.data_processing.build_public_transport_stop_context import checked_source, load_stops
from src.data_processing.register_road_did_outputs import register
from src.data_processing.atomic_csv_output import write_csv

SOURCE = 'ORS_SAASFEE_PARKING_CANDIDATE_PROBE_2026'
TABLE = 'saas_fee_road_candidate_probe'
OUTPUT = 'reports/'+TABLE+'.csv'
MANIFEST = 'reports/'+TABLE+'_summary.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if not args.execute:
        raise ValueError('Explicit --execute required; candidates do not change analytical points')
    method = json.loads((ROOT/'config/path_c_analysis.json').read_text(encoding='utf-8'))
    stops, _, _ = load_stops(checked_source(method))
    ids = ['8501782','8557144','8511180']
    expected = ['Saas-Fee, Busterminal','Saas-Fee, Parkhaus','Saas-Fee, Parkplatz Nord']
    points = stops.set_index('Numero').loc[ids].copy()
    if points.Nom.tolist() != expected or not points.Commune_Numero.eq('6290').all():
        raise ValueError('Exact source identity changed')
    lon, lat = Transformer.from_crs(2056,4326,always_xy=True).transform(points.E.astype(float).to_numpy(),points.N.astype(float).to_numpy())
    locations = [[float(x),float(y)] for x,y in zip(lon,lat)]
    payload = dict(locations=locations,sources=['0','1','2'],destinations=['0','1','2'],metrics=['duration','distance'],units='m',resolve_locations=True)
    rid = digest(dict(endpoint=ENDPOINT,payload=payload,official_stop_ids=ids))
    folder = ROOT/'data_external/saas_fee_road_candidate_probe'
    folder.mkdir(parents=True,exist_ok=True)
    checkpoint = folder/(rid+'.metadata.json')
    if checkpoint.exists():
        meta = json.loads(checkpoint.read_text(encoding='utf-8'))
        body = (ROOT/meta['raw_file']).read_bytes()
        if hashlib.sha256(body).hexdigest() != meta['raw_sha256'] or meta['payload'] != payload:
            raise ValueError('Probe checksum/request differs')
        print('Reusing verified candidate probe; no request.',flush=True)
    else:
        routing = json.loads((ROOT/'config/accessibility_road_routing.json').read_text(encoding='utf-8'))
        credential, _ = load_credential(routing)
        if not credential:
            raise ValueError('Credential absent; value never displayed')
        code, headers, body, error = request_matrix(payload,credential,ENDPOINT)
        if credential.encode() in body:
            raise ValueError('Credential echoed; response not saved')
        if code != 200:
            raise ValueError('Probe failed; no endpoint changed; status='+str(code)+' type='+str(error))
        raw = folder/(rid+'.json')
        with raw.open('xb') as stream:
            stream.write(body)
        meta = dict(request_id=rid,payload=payload,http_status=code,safe_response_headers=headers,
            retrieval_date=datetime.now(timezone.utc).isoformat(),raw_file=raw.relative_to(ROOT).as_posix(),
            raw_sha256=hashlib.sha256(body).hexdigest(),source_id=SOURCE)
        with checkpoint.open('x',encoding='utf-8') as stream:
            json.dump(meta,stream,ensure_ascii=False,indent=2)
    response = json.loads(body)
    validate_response(response,payload)
    records = []
    for i,origin in enumerate(ids):
        for j,destination in enumerate(ids):
            records.append(dict(origin_stop_id=origin,origin_stop_name=expected[i],destination_stop_id=destination,
                destination_stop_name=expected[j],model_duration_seconds=response['durations'][i][j],
                model_distance_metres=response['distances'][i][j],origin_snap_distance_metres=response['sources'][i].get('snapped_distance'),
                destination_snap_distance_metres=response['destinations'][j].get('snapped_distance'),
                input_origin_longitude=locations[i][0],input_origin_latitude=locations[i][1],
                input_destination_longitude=locations[j][0],input_destination_latitude=locations[j][1],
                resolved_origin_location=json.dumps(response['sources'][i].get('location')),
                resolved_destination_location=json.dumps(response['destinations'][j].get('location')),
                source_id=SOURCE))
    frame = pd.DataFrame(records)
    write_csv(frame,ROOT/OUTPUT)
    descriptions = {field:(('Original source/probe value, candidate not yet approved for analysis: '+field),
        'metres' if field.endswith('metres') else 'seconds' if field.endswith('seconds') else 'decimal degrees WGS84' if field.endswith(('latitude','longitude')) else 'text/identifier') for field in frame}
    register(SOURCE,dict(variable_name='unapproved_saas_fee_parking_stop_candidates',
        variable_description='Read-only design probe: retained Busterminal and official Parkhaus/ParkplatzNord operating points, no analytical endpoint change',
        source_organisation='BAV/OFT and HeiGIT/OpenStreetMap',source_dataset_name='Saas-Fee local parking-stop candidate matrix',
        api_endpoint=ENDPOINT,local_raw_file=meta['raw_file'],processed_file=OUTPUT+'|'+MANIFEST,
        retrieval_method='One authenticated3x3 Matrix POST; key never archived; SHA checkpoint reusable',
        transformation_applied='Exact official operating-point IDs/E/N transformed2056→4326; original seconds/metres and snaps retained',
        quality_notes='Candidate probe only. No endpoint selected/changed, no zero promoted, no walk duration or private-car legal-access certification.'),
        {TABLE:frame},{TABLE:[]},descriptions)
    summary = dict(meta,official_stop_ids=ids,official_stop_names=expected,
        graph=response.get('metadata',{}).get('engine',{}),coordinate_source_id='BAV_PUBLIC_TRANSPORT_STOPS_2026',
        candidate_approval_received=False,analytical_endpoints_changed=False,
        output_sha256={OUTPUT:hashlib.sha256((ROOT/OUTPUT).read_bytes()).hexdigest()})
    (ROOT/MANIFEST).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(frame[frame.origin_stop_id.eq('8501782')][['destination_stop_name','model_duration_seconds','origin_snap_distance_metres','destination_snap_distance_metres']].to_string(index=False))


if __name__ == '__main__':
    main()
