"""Focused unit investigation: documentary search plus scale cross-checks.

The likely metre encoding is an inference, not a newly discovered source unit
attribute. Never convert the frozen snow series or silently certify the unit.
"""
import io
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest, SOURCE_COLUMNS
from src.data_processing.atomic_csv_output import write_csv
from src.descriptive.audit_snow_compatibility_stage73 import evidence

CONFIG = 'config/spass_unit_evidence_stage74.json'
OUTPUT = 'reports/spass_unit_investigation_stage74.json'
SOURCE = 'DERIVED_SPASS_UNIT_INVESTIGATION_STAGE74'


def committed_csv(path):
    return pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','1fc3401:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)


def main():
    sources = json.loads((ROOT/CONFIG).read_text(encoding='utf8'))
    docs = {s['source_id']:evidence(s['source_id']) for s in sources}
    package = json.loads((ROOT/docs['ENVIDAT_SPASS_PACKAGE_METADATA_STAGE74']['raw_file']).read_text(encoding='utf8'))
    resource = json.loads((ROOT/docs['ENVIDAT_SPASS_HS_RESOURCE_METADATA_STAGE74']['raw_file']).read_text(encoding='utf8'))
    assert package['success'] and resource['success']
    assert resource['result']['id']=='688d1caf-ed63-4cb8-8579-8c017bb7458c'
    assert package['result']['id']==resource['result']['package_id']=='da0c9ee4-ff02-4848-bc65-cbcaae343636'
    comparison_path = 'reports/snow_gridded_component_comparison.csv'
    producer_path = 'src/data_processing/build_snow_gridded_sensitivity.py'
    daily_path = 'data_processed/native_snow_daily_common_support_stage70.csv'
    comparisons = pd.read_csv(ROOT/comparison_path)
    cols = ['selected_station_code','selected_station_label','station_location_3x3_common_usable_winters',
        'station_location_3x3_station_mean_winter_depth_cm','station_location_3x3_grid_mean_winter_depth_cm']
    # Previously calculated grid-centred local medians, all 11 unique stations;
    # duplicated resort links are not treated as independent evidence.
    c = comparisons[cols].drop_duplicates()
    assert len(c)==11 and c.selected_station_code.is_unique
    assert set(c.station_location_3x3_common_usable_winters)=={10}
    producer = (ROOT/producer_path).read_text(encoding='utf8')
    assert 'local_m * 100' in producer
    rows = []
    for r in c.itertuples(index=False):
        raw = r.station_location_3x3_grid_mean_winter_depth_cm / 100
        rows.append(dict(station_code=r.selected_station_code,station_label=r.selected_station_label,
            observed_station_winter_mean_cm=r.station_location_3x3_station_mean_winter_depth_cm,
            model_raw_mean_recovered_by_reversing_prior_explicit_x100=raw,
            model_cm_if_raw_is_m=r.station_location_3x3_grid_mean_winter_depth_cm,
            model_cm_if_raw_is_cm=raw,common_winters=10))
    daily = pd.read_csv(ROOT/daily_path)
    daily = daily[daily.oshd_date_offset_days==0]
    assert len(daily)==6040 and daily.station_group_id.nunique()==40
    inputs = [CONFIG, comparison_path, producer_path, daily_path,
        'reports/snow_grid_metadata_compatibility_stage47.json',
        'src/descriptive/investigate_spass_unit_stage74.py']
    for m in docs.values():
        inputs += [m['raw_file'], m['sidecar_file']]
    state = dict(date='2026-10-10',resource_id=resource['result']['id'],
        original_hs_sha256='b8d740993a4bfa2b542aa2c2986564073d275b07f2b2fd9c869dfc5daf597c0d',
        likely_encoding_unit='m',unit_evidence_status='strong_scale_inference_not_producer_certified',
        source_units_attribute_present=False,new_direct_unit_declaration_found=False,
        finding='Metres strongly supported by scale cross-checks and configurable SWE2HS default, not proven by a product-specific unit statement.',
        original_unit_field_changed=False,analytical_data_converted=False,profiles_or_effects_estimated=False,
        observed_station_comparisons=rows,
        comparison_limit='Existing November-April 10-winter averages at station-neighbourhood grids; station and model differ spatially and share parts of the observation network. This is a scale plausibility check, not independent validation or a production-code identity test.',
        daily_raw_crosscheck=dict(unique_groups=40,reference_offset=0,rows=len(daily),
            spass_raw_mean=float(daily.spass_mean_common_raw.mean()),spass_raw_max=float(daily.spass_mean_common_raw.max()),
            oshd_documented_m_mean=float(daily.oshd_mean_common_m.mean()),oshd_documented_m_max=float(daily.oshd_mean_common_m.max())),
        public_spass_named_projects=json.loads((ROOT/docs['WSL_PUBLIC_SPASS_PROJECT_SEARCH_STAGE74']['raw_file']).read_text(encoding='utf8')),
        public_snowqm_tree_entries=len(json.loads((ROOT/docs['WSL_SNOWQM_PUBLIC_TREE_STAGE74']['raw_file']).read_text(encoding='utf8'))),
        input_sha256={p:digest(p) for p in inputs})
    target = ROOT/OUTPUT
    if target.exists():
        assert json.loads(target.read_text(encoding='utf8'))==state, 'Frozen investigation differs'
    else:
        target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    path = 'metadata/data_sources_master.csv'
    old = committed_csv(path)
    current = pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
    assert len(old)==1210 and old.equals(current.iloc[:len(old)].reset_index(drop=True))
    additions=[]
    for s in sources:
        m=docs[s['source_id']]
        additions.append(dict(source_id=s['source_id'], variable_name='spass_unit_documentary_search',
            variable_description=s['description'],source_organisation=s['organisation'],source_dataset_name='Public source metadata/code catalogue',
            source_page_url=s['url'],api_endpoint=s['url'],retrieval_method='Read-only public GET through existing robots-respecting collector; HTTP200 JSON',
            retrieval_date=m['retrieval_date'],original_file_name=Path(m['raw_file']).name,local_raw_file=m['raw_file'],processed_file=OUTPUT,
            unit='No product-specific HS unit declaration in these retrieved records',license='Producer catalogue/software terms retained; no new data licence inferred',
            transformation_applied='Source identity, resource description and public repository inventory inspection',
            quality_notes='No public SPASS-named project found; not proof that no private/unindexed production code exists',
            notes='SHA256 '+m['sha256']+'; '+CONFIG))
    additions.append(dict(source_id=SOURCE,variable_name='spass_encoding_unit_investigation',variable_description=state['finding'],
        source_organisation='Thesis reproducible source/scale investigation',source_dataset_name='Exact SPASS resource metadata and preserved source-value comparisons',
        source_page_url='reports/119_UNITE_HAUTEUR_NEIGE_SPASS_FR.md',retrieval_method='Local frozen comparisons plus six archived public JSON responses',
        retrieval_date='2026-10-10',processed_file=OUTPUT,unit='Candidate m: strongly supported inference, not certified original metadata',
        transformation_applied='Undo explicit legacy x100 for comparison only; all 11 unique stations retained; fixed zero-lag daily value summaries',
        quality_notes=state['comparison_limit'],license='Inherited sources; no new redistribution rights',notes='No source unit rewrite or analytical conversion; '+CONFIG))
    missing=[a for a in additions if a['source_id'] not in set(current.source_id)]
    if missing:
        write_csv(pd.concat([current,pd.DataFrame(missing).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/path)
    now=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
    assert len(now)==1217 and not now.source_id.duplicated().any()
    dictionary='metadata/data_dictionary.csv'
    assert committed_csv(dictionary).equals(pd.read_csv(ROOT/dictionary,dtype=str,keep_default_na=False))
    logs='logs/data_collection_log.csv'
    before=committed_csv(logs)
    after=pd.read_csv(ROOT/logs,dtype=str,keep_default_na=False)
    assert before.equals(after.iloc[:len(before)].reset_index(drop=True)) and len(after)==len(before)+6
    assert set(after.iloc[len(before):].source_id)==set(docs)
    assert set(after.iloc[len(before):].success)=={'True'}
    print(json.dumps(dict(likely_encoding_unit='m',direct_product_unit_proof=False,unique_station_checks=11,
        source_rows=len(now),dictionary_unchanged=True,prior_collection_rows_exact=len(before),current_collection_rows=len(after)),ensure_ascii=False))


if __name__=='__main__':
    main()
