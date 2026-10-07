"""Approved Saas-Fee arrival correction; reuse exact local probe and all other accesses."""
import json
import sys
from pathlib import Path
import pandas as pd
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection import collect_accessibility_road_matrix as engine
from src.data_processing.build_public_transport_stop_context import checked_source, load_stops
from src.data_processing.prepare_accessibility_road_reference import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.register_road_did_outputs import register

CONFIG = 'config/accessibility_road_did_final_execution.json'
PROPOSAL = 'config/accessibility_saas_fee_road_endpoint_proposal.json'
PROBE = 'reports/saas_fee_road_candidate_probe_summary.json'
ORIGINS = 'reports/accessibility_road_stop_corrected_origins.csv'
ARRIVAL = 'reports/accessibility_road_saasfee_arrival.csv'
FINAL_ARRIVALS = 'reports/accessibility_road_final_arrivals.csv'
PREP = 'reports/accessibility_road_saasfee_preparation_summary.json'
DELTA = 'reports/accessibility_road_saasfee_collection_summary.json'
SUMMARY = 'reports/accessibility_road_final_collection_summary.json'
BASE = ['data_processed/accessibility_road_stop_corrected_directional.csv',
    'data_processed/accessibility_road_stop_corrected_pairs.csv',
    'reports/accessibility_road_stop_corrected_collection_summary.json', ORIGINS,
    'reports/accessibility_road_stop_arrivals.csv', PROPOSAL, PROBE,
    'config/accessibility_road_did_execution.json']
TABLES = {f'accessibility_road_saasfee_{k}': f'data_processed/accessibility_road_saasfee_{k}.csv' for k in ['directional','pairs']}
FINAL = {f'accessibility_road_final_{k}': f'data_processed/accessibility_road_final_{k}.csv' for k in ['directional','pairs']}
ACCESS = 'ACCESS_MAGIC_CURRENT__600'
SOURCE = 'DERIVED_ACCESSIBILITY_ROAD_SAASFEE_ENDPOINT'


def check_manifest(path):
    manifest = json.loads((ROOT/path).read_text(encoding='utf-8'))
    for p,value in {**manifest.get('input_sha256',{}), **manifest.get('output_sha256',{}), **manifest.get('protected_legacy_sha256',{})}.items():
        if sha(p) != value:
            raise ValueError('Changed input/output/protected file: '+p)
    return manifest


def prepare():
    config = json.loads((ROOT/CONFIG).read_text(encoding='utf-8'))
    if config['approval_user_text'] != 'oui tout bon':
        raise ValueError('Explicit endpoint approval absent')
    check_manifest(BASE[2])
    proposal = json.loads((ROOT/PROPOSAL).read_text(encoding='utf-8'))
    points,_,_ = load_stops(checked_source(json.loads((ROOT/'config/path_c_analysis.json').read_text(encoding='utf-8'))))
    point = points[points.Numero.eq(proposal['proposed_stop_id'])]
    if len(point)!=1 or point.iloc[0].Nom!=proposal['proposed_stop_name'] or point.iloc[0].Commune_Numero!='6290':
        raise ValueError('Exact proposed source identity changed')
    arrivals = pd.read_csv(ROOT/BASE[4],dtype={'selected_stop_id':str})
    row = arrivals[arrivals.access_point_id.eq(ACCESS)].copy()
    if len(row)!=1 or row.iloc[0].selected_stop_id != proposal['old_station_stop_id']:
        raise ValueError('Unexpected previous arrival')
    point = point.iloc[0]
    lon,lat = Transformer.from_crs(2056,4326,always_xy=True).transform(float(point.E),float(point.N))
    fields = dict(selected_stop_id=point.Numero, selected_stop_name=point.Nom, bav_xtf_id=point.xtf_id,
        bav_easting_2056=float(point.E),bav_northing_2056=float(point.N),road_arrival_longitude=lon,
        road_arrival_latitude=lat,source_id=SOURCE)
    for field,value in fields.items():
        row[field]=value
        arrivals.loc[arrivals.access_point_id.eq(ACCESS),field]=value
    if (ROOT/PREP).exists():
        check_manifest(PREP)
        print('Approved Saas-Fee arrival preparation reused; original proposal untouched.')
        return
    write_csv(row,ROOT/ARRIVAL); write_csv(arrivals,ROOT/FINAL_ARRIVALS)
    frames={'accessibility_road_saasfee_arrival':row,'accessibility_road_final_arrivals':arrivals}
    register(SOURCE,dict(variable_name='approved_saasfee_automobile_arrival',
        variable_description='Validated AlpinExpress8594574 to ParkplatzNord8511180 arrival exception; unchanged Busterminal origin',
        source_organisation='BAV/OFT; researcher-approved arrival correction',source_dataset_name='Official parking-area stop reference',
        retrieval_method='SHA-checked existing BAV point archive, exact ID/name/commune, no download',
        local_raw_file=PROPOSAL+'|'+PROBE,processed_file=ARRIVAL+'|'+FINAL_ARRIVALS,
        transformation_applied='Official E/N2056 to WGS84, only ACCESS_MAGIC_CURRENT__600 arrival changed',
        quality_notes='Point associated with parking north, not surveyed gate; communal snap300.78m persists, last leg to lifts missing/separate; old proposal remains historical snapshot.'),
        frames,{t:['accessibility_road_stop_arrivals'] for t in frames})
    baseline = json.loads((ROOT/BASE[2]).read_text(encoding='utf-8'))
    protected = dict(baseline['protected_legacy_sha256'], **{p:sha(p) for p in BASE})
    manifest=dict(input_sha256={p:sha(p) for p in [CONFIG,*BASE]},output_sha256={p:sha(p) for p in [ARRIVAL,FINAL_ARRIVALS]},protected_legacy_sha256=protected)
    (ROOT/PREP).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Approved ParkplatzNord8511180 arrival prepared, original endpoints preserved.')


def probe_records(origins, arrivals):
    meta=json.loads((ROOT/PROBE).read_text(encoding='utf-8'))
    raw=ROOT/meta['raw_file']
    if sha(meta['raw_file'])!=meta['raw_sha256']:
        raise ValueError('Original probe checksum differs')
    response=json.loads(raw.read_bytes()); engine.validate_response(response,meta['payload'])
    m=origins.set_index('municipality_bfs_id').loc[6290]
    a=arrivals.set_index('access_point_id').loc[ACCESS]
    if [m.road_origin_longitude,m.road_origin_latitude]!=meta['payload']['locations'][0] or [a.road_arrival_longitude,a.road_arrival_latitude]!=meta['payload']['locations'][2]:
        raise ValueError('Probe endpoints not exactly compatible')
    records,references=[],[]
    for direction,si,di in [('outbound',0,2),('return',2,0)]:
        batch=dict(batch_id='exact_probe_subset_'+direction,direction=direction,municipality_bfs_ids=[6290],access_point_ids=[ACCESS],requested_cells=1)
        payload=engine.make_payload(batch,origins,arrivals,{'metrics':['duration','distance'],'units':'m','resolve_locations':True})
        subset=dict(durations=[[response['durations'][si][di]]],distances=[[response['distances'][si][di]]],
            sources=[response['sources'][si]],destinations=[response['destinations'][di]],metadata=response.get('metadata',{}))
        reference=dict(meta,batch=batch,endpoint=engine.ENDPOINT,status='success',
            reuse_method='Exact cell subset of archived3x3 probe, not a new HTTP request',source_index=si,destination_index=di)
        records.extend(engine.cell_records(batch,payload,subset,reference)); references.append(reference)
    return records,references


def configure():
    engine.OUTPUTS={'accessibility_road_stop_corrected_origins':ORIGINS,'accessibility_road_saasfee_arrival':ARRIVAL}
    engine.TABLES=TABLES; engine.SOURCE='ORS_DRIVING_CAR_SAASFEE_ARRIVAL_CORRECTION_2026'
    engine.INVENTORY_SOURCE=SOURCE
    engine.ORIGIN_READY=engine.ARRIVAL_READY='verified_existing_tp_stop_coordinate'
    engine.SUMMARY=DELTA
    engine.PROTECTED=list(check_manifest(PREP)['protected_legacy_sha256'])
    engine.CACHE_DIRECTORY='data_interim/accessibility_road_saasfee_ors'
    engine.RAW_DIRECTORY='data_external/accessibility_road_saasfee_ors'
    engine.EXTRA_INPUTS=[CONFIG,PREP,PROBE]
    engine.ENTRY_POINT='src/data_collection/collect_accessibility_road_saasfee.py'
    engine.RESUME_COMMAND='.venv/Scripts/python.exe '+engine.ENTRY_POINT+' --execute --max-new-batches 16'
    engine.MEASUREMENT_LABEL='arrêt communal → Parkplatz Nord Saas-Fee8511180, arrivée validée'
    engine.APPROVED_ZERO_PAIRS=set()
    recover=engine.recover_completed
    def with_probe(folder,origins,arrivals,config):
        records,successes=recover(folder,origins,arrivals,config)
        seeded,references=probe_records(origins,arrivals)
        records.extend(seeded); successes.extend(references)
        return records,successes
    engine.recover_completed=with_probe


def publish():
    delta=check_manifest(DELTA); check_manifest(PREP)
    if delta['actual_directional_cells_returned']!=370:
        print('Saas-Fee correction pending; resume collector before estimation.'); return
    if (ROOT/SUMMARY).exists(): check_manifest(SUMMARY)
    frames={}
    for kind,oldpath in zip(['directional','pairs'],BASE[:2]):
        old=pd.read_csv(ROOT/oldpath); new=pd.read_csv(ROOT/TABLES['accessibility_road_saasfee_'+kind])
        frame=pd.concat([old[old.access_point_id.ne(ACCESS)],new],ignore_index=True)
        keys=['municipality_bfs_id','access_point_id']+(['direction'] if kind=='directional' else [])
        if len(frame)!=len(old) or frame.duplicated(keys).any(): raise ValueError('Full reference key/universe changed')
        table='accessibility_road_final_'+kind
        frames[table]=frame.sort_values(keys).reset_index(drop=True); write_csv(frames[table],ROOT/FINAL[table])
    register('DERIVED_ACCESSIBILITY_ROAD_FINAL_REFERENCE',dict(variable_name='road_reference_with_two_approved_exceptions',
        variable_description='Full matrix retaining approved Lauterbrunnen communal correction and adding approved Saas-Fee arrival correction',
        source_organisation='Thesis pipeline from BAV and archived HeiGIT/OpenStreetMap results',source_dataset_name='Final approved static road reference for exploratory DiD',
        local_raw_file=BASE[0]+'|'+BASE[1]+'|'+DELTA,processed_file='|'.join(FINAL.values()),
        retrieval_method='Replace only one station access, reuse exact archived local probe and every other access observation',
        transformation_applied='Independent outward/return mean; no imputation or new zero rule',
        quality_notes='Static graph, winter/legal access not certified, snapping and missing final walk retained; unchanged hotel territory/group inventory.'),
        frames,{t:['accessibility_road_stop_corrected_'+t.rsplit('_',1)[1]] for t in frames})
    d,p=frames.values()
    manifest=dict(status='completed_approved_road_reference',input_sha256={v:sha(v) for v in [CONFIG,PREP,DELTA,*BASE]},
        output_sha256={v:sha(v) for v in FINAL.values()},protected_legacy_sha256=delta['protected_legacy_sha256'],
        directional_rows=len(d),pairs=len(p),usable_pairs=int(p.road_reference_minutes.notna().sum()),
        graph_versions=d[['graph_date','engine_version']].drop_duplicates().to_dict('records'),
        route_status_counts=d.route_status.value_counts().to_dict(),new_http_requests=delta['new_requests'],
        exact_probe_cells_reused=2,original_tp_outputs_changed=False)
    (ROOT/SUMMARY).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    from src.data_processing import audit_accessibility_road_stop_snapping as audit
    audit.INPUT=FINAL['accessibility_road_final_directional']; audit.COLLECTION=SUMMARY
    audit.ENDPOINTS={'accessibility_road_stop_corrected_origins':ORIGINS,'accessibility_road_final_arrivals':FINAL_ARRIVALS}
    audit.SOURCE='DERIVED_ACCESSIBILITY_ROAD_FINAL_SNAPPING'
    audit.OUTPUTS={t.replace('_stop_','_final_'):v.replace('_stop_','_final_') for t,v in audit.OUTPUTS.items()}
    audit.SUMMARY='reports/accessibility_road_final_snapping_summary.json'
    audit.main()
    print(json.dumps({k:manifest[k] for k in ['status','usable_pairs','new_http_requests','exact_probe_cells_reused']}))


if __name__=='__main__':
    if sys.argv[1:]==['--prepare']: prepare()
    else:
        check_manifest(PREP); configure(); engine.main(); publish()
