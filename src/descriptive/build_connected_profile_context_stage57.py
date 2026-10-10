"""Carry approved city minima and own five-winter calendars to70 groups.

Reuse the original approved calendar/endpoint functions, preserving the old
71-group context. No grid values, seasonal-offer inference or profile fit.
"""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.descriptive.build_approved_profile_context import build_context,DEFS
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS,DICTIONARY_COLUMNS
SOURCE='DERIVED_CONNECTED_PROFILE_CONTEXT_STAGE57'
SUMMARY='reports/connected_profile_context_stage57_summary.json'
OUTPUTS={name:f'data_processed/{name}_stage57.csv' for name in ['winter_profile_urban_city_detail','winter_profile_urban_minimum','winter_profile_approved_snow_windows']}


def main():
    inputs_list=['src/descriptive/build_connected_profile_context_stage57.py','src/descriptive/build_approved_profile_context.py','src/descriptive/audit_five_dimension_profile_availability.py',
        'config/winter_profile_operational_decisions_stage43.json','config/eischoll_unterbaech_regrouping_stage55.json','data_processed/accessibility_station_groups_stage55.csv',
        'data_processed/winter_profile_five_dimension_groups.csv','data_processed/accessibility_road_group_reference_stage55.csv','reports/accessibility_road_stop_origins.csv',
        'reports/accessibility_road_final_snapping_endpoints.csv','reports/eischoll_unterbaech_regrouping_stage55_summary.json','reports/approved_profile_context_summary.json']
    for summary in ['reports/eischoll_unterbaech_regrouping_stage55_summary.json','reports/approved_profile_context_summary.json']:
        previous=json.loads((ROOT/summary).read_text(encoding='utf-8'))
        for p,h in {**previous['input_sha256'],**previous['output_sha256']}.items():
            if sha(p)!=h:raise ValueError('Prior context/group checkpoint changed: '+p)
    inputs={p:sha(p) for p in inputs_list}
    config=json.loads((ROOT/inputs_list[3]).read_text(encoding='utf-8'));decision=json.loads((ROOT/inputs_list[4]).read_text(encoding='utf-8'))
    if not config['urban_six_city_summary_choice_received'] or not config['snow_source_and_baseline_choice_received']:raise ValueError('Require prior approvals')
    parents=decision['parent_group_ids'];new_id=decision['new_derived_group_id']
    universe=pd.read_csv(ROOT/inputs_list[5],dtype=str,keep_default_na=False)
    old_groups=pd.read_csv(ROOT/inputs_list[6],dtype=str,keep_default_na=False)
    groupcols=['station_group_id','station_group_name','first_base_entry_month']
    joint=universe[universe.station_group_id.eq(new_id)].rename(columns={'first_effective_month':'first_base_entry_month'})[groupcols]
    old_parents=old_groups[old_groups.station_group_id.isin(parents)]
    if len(old_parents)!=2 or not old_parents.first_base_entry_month.eq(joint.first_base_entry_month.iloc[0]).all():raise ValueError('No harmonisation of different entry calendars without approval')
    groups=pd.concat([old_groups[~old_groups.station_group_id.isin(parents)][groupcols],joint],ignore_index=True)
    if len(groups)!=70 or set(groups.station_group_id)!=set(universe.station_group_id):raise ValueError('Wrong derived profile universe')
    road=pd.read_csv(ROOT/inputs_list[7]);origins=pd.read_csv(ROOT/inputs_list[8]);snaps=pd.read_csv(ROOT/inputs_list[9])
    frames=build_context(groups,road,origins,snaps,config['urban_city_bfs_ids'],pd.Timestamp('1961-09-01'),pd.Timestamp('2023-08-31'))
    lineage=universe.set_index('station_group_id').parent_station_group_ids.to_dict()
    for key,frame in frames.items():
        frame['source_id']=SOURCE
        frame['parent_station_group_ids']=frame.station_group_id.map(lineage)
        if key!='winter_profile_approved_snow_windows':frame['parent_source_ids']=frame.parent_source_ids+'|DERIVED_CONNECTED_GROUP_OVERLAY_STAGE55'
    # All69 unrelated profiles must retain their actual computed values/dates.
    for key,frame in frames.items():
        original_path=f'data_processed/{key}.csv';inputs[original_path]=sha(original_path)
        old=pd.read_csv(ROOT/original_path,dtype={'minimum_city_bfs_ids':str})
        keys=['station_group_id']+(['municipality_bfs_id'] if key.endswith('detail') else ['winter_start_year'] if 'windows' in key else [])
        cols=[c for c in old if c not in ['source_id','parent_source_ids']]
        a=old[~old.station_group_id.isin(parents)][cols].sort_values(keys).reset_index(drop=True)
        b=frame[frame.station_group_id.ne(new_id)][cols].sort_values(keys).reset_index(drop=True)
        pd.testing.assert_frame_equal(a,b,check_dtype=False,check_exact=False,rtol=1e-12,atol=0)
    winters=frames['winter_profile_approved_snow_windows'];minima=frames['winter_profile_urban_minimum']
    common=winters[winters.station_group_id.eq(new_id)]
    if len(common)!=5 or not pd.to_datetime(common.winter_end_date).lt(pd.Timestamp('2023-05-01')).all():raise ValueError('Five own strictly preentry winters required')
    state=dict(date='2026-10-10',input_sha256=inputs,derived_group_count=70,original_group_id_count=71,city_detail_count=len(frames['winter_profile_urban_city_detail']),all_six_city_group_count=int(minima.all_six_cities_available.sum()),snow_window_count=len(winters),snow_winters_outside_spass=int((~winters.spass_calendar_within_archive).sum()),groups_with_snow_winters_outside_spass=sorted(winters.loc[~winters.spass_calendar_within_archive,'station_group_id'].unique()),common_group_snow_winters=common.winter_start_year.tolist(),common_group_urban_minimum_minutes=float(minima.loc[minima.station_group_id.eq(new_id),'urban_min_road_minutes'].iloc[0]),unrelated_69_profiles_preserved=True,prior_outputs_preserved=True,no_routing_calls=True,no_snow_values_or_splice=True,no_clustering_or_effects=True,no_automatic_exclusions=True)
    target=ROOT/SUMMARY
    if target.exists():
        prior=json.loads(target.read_text(encoding='utf-8'))
        if prior['input_sha256']!=inputs or any(sha(p)!=h for p,h in prior['output_sha256'].items()):raise ValueError('Own frozen context changed')
    else:
        for key,frame in frames.items():write_csv(frame,ROOT/OUTPUTS[key])
        state['output_sha256']={p:sha(p) for p in OUTPUTS.values()};target.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    master=pd.read_csv(ROOT/'metadata/data_sources_master.csv',dtype=str,keep_default_na=False)
    if SOURCE not in set(master.source_id):
        record=dict(source_id=SOURCE,variable_name='connected_group_approved_urban_context_snow_calendars',variable_description='Existing six-city minima and own fivepreentrywinters carried to70-group approved overlay',source_organisation='Thesis deterministic context using ORS/OFT/SLF parent sources',retrieval_date='2026-10-10',retrieval_method='Original approved build_context function/newlineage/cachedroadreferences, no requests',processed_file='|'.join(OUTPUTS.values()),geographic_level='70derivedgroups with71originalIDs preserved',temporal_resolution='Current static road graph; fiveownfullypreentryDecember-Aprilcalendars',transformation_applied='Minima among unchanged sixcities/ties; samecalendaralgorithm;69oldprofiles identical',quality_notes='Roadgraph notpreentryverified; calendars not observed snow means; no source substitution/imputation/exclusions',notes='FullSHA and originallineage in '+SUMMARY)
        write_csv(pd.concat([master,pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_sources_master.csv')
    dictionary=pd.read_csv(ROOT/'metadata/data_dictionary.csv',dtype=str,keep_default_na=False);records=[]
    for key,frame in frames.items():
        table=Path(OUTPUTS[key]).stem
        for col in frame:
            if ((dictionary.table==table)&(dictionary.variable==col)).any():continue
            description,unit=('Retained original group IDs behind the approved derived group','identifiers') if col=='parent_station_group_ids' else ('Current derived station group ID; original group IDs separately retained','identifier') if col=='station_group_id' else DEFS[col]
            records.append(dict(variable=col,table=table,description=description,unit=unit,data_type=str(frame[col].dtype),source_id=SOURCE,geographic_level='derivedgroup, cityaccess or requestedwintercalendar',temporal_level='current road graph/own preentry winter dates',raw_or_derived='retained or approved context derivation',formula='Original build_context function with approved70-group lineage; no new estimator',causal_role='candidateprofilecontext, not verified finalcausalfeature',missing_share=f'{frame[col].isna().mean():.6f}',notes='No missing-to-zero/snowvalues/splice/imputation/exclusion; all69unrelatedprofiles preserved'))
    if records:write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS)],ignore_index=True).fillna(''),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if not k.endswith('sha256')},ensure_ascii=False))


if __name__=='__main__':main()
