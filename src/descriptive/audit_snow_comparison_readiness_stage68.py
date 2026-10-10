"""Actual snow-calendar and grid readiness, never a selected comparison method.

Read archived metadata and preserved axis bounds only. No dependent snow-field
values, nearest-cell matching, interpolation, aggregation or model splice.
"""
import json
import sys
from pathlib import Path

import pandas as pd
from shapely import wkt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.verify_piste_assignments_stage51 import sha
from src.descriptive.summarise_terrain_reference_stage67 import row_digest
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SOURCE = 'DERIVED_SNOW_COMPARISON_READINESS_STAGE68'
TABLE = 'snow_comparison_readiness_stage68'
OUTPUT = 'data_processed/' + TABLE + '.csv'
SUMMARY = 'reports/snow_comparison_readiness_stage68_summary.json'
CONFIG = 'config/snow_comparison_readiness_stage68.json'
TERRAIN = 'data_processed/terrain_reference_profiles_stage67.csv'
WINDOWS = 'data_processed/winter_profile_approved_snow_windows_stage57.csv'
NETWORK = 'data_interim/winter_profile_exact_network_stage63.json'
SPASS = 'reports/snow_grid_metadata_compatibility_stage47.json'
OSHD = 'reports/oshd_netcdf_metadata_inventory.json'
DEFS = {
    'source_id': ('Registered metadata/calendar readiness audit', 'identifier'),
    'station_group_id': ('Preserved group, one row each; never municipality', 'identifier'),
    'station_group_name': ('Preserved group name', 'text'),
    'group_retained': ('True for all70groups; no metadata-driven exclusion', 'boolean'),
    'mapped_axis_geometry_available': ('Preserved exact candidate-axis geometry available, not exhaustive/preentry-certified', 'boolean'),
    'unique_mapped_axis_length_m': ('Unchanged candidate unique-axis length; missing is not zero', 'metres'),
    'requested_own_preentry_winters': ('Five previously approved December-April calendars per group', 'count'),
    'spass_calendar_available_winters': ('Requested full winter date calendars inside SPASS archive; no observed snow-field coverage', 'count'),
    'spass_calendar_missing_winters': ('Requested winters outside SPASS original calendar, not replaced', 'count'),
    'downloaded_oshd_calendar_available_winters': ('Requested full winters within already verified WY2023/2024/2025 monthly date calendars, not all advertised years', 'count'),
    'both_downloaded_calendar_available_winters': ('Requested full winters whose dates occur in both archived model calendars; no paired values', 'count'),
    'missing_spass_with_downloaded_oshd_calendar_winters': ('Requested SPASS-absent winters covered by downloaded OSHD dates, not substituted', 'count'),
    'comparison_2022_winter_is_own_preentry_window': ('Proposed model diagnostic winter2022/23 is in this group approved preentry window; not a sample filter', 'boolean'),
    'axis_min_east_2056': ('Minimum preserved axiscoordinate, no raster matching', 'metres'),
    'axis_min_north_2056': ('Minimum preserved axiscoordinate, no raster matching', 'metres'),
    'axis_max_east_2056': ('Maximum preserved axiscoordinate, no raster matching', 'metres'),
    'axis_max_north_2056': ('Maximum preserved axiscoordinate, no raster matching', 'metres'),
    'within_spass_centre_envelope': ('Axisbbox lies within first/lastcoordinate centre envelope; not valid-cell or full-domain coverage', 'boolean'),
    'within_oshd_centre_envelope': ('Axisbbox lies within first/lastcoordinate centre envelope; not valid-cell or full-domain coverage', 'boolean'),
    'snow_feature_computed': ('False; values and matching/aggregation/conversion still pending', 'boolean'),
}


def metadata_dates(variable):
    a = variable['axis']
    if a['missing_count'] or not a['strictly_increasing'] or a['difference_min'] != 1 or a['difference_max'] != 1:
        raise ValueError('Only previously verified complete daily coordinate calendars')
    dates = pd.date_range(pd.Timestamp(a['decoded_first']).normalize(), pd.Timestamp(a['decoded_last']).normalize())
    if len(dates) != a['observed_count']:
        raise ValueError('Daily metadata date count differs')
    return set(dates)


def centre_envelope(variables, x, y):
    xa, ya = variables[x]['axis'], variables[y]['axis']
    return (min(xa['first'], xa['last']), min(ya['first'], ya['last']),
            max(xa['first'], xa['last']), max(ya['first'], ya['last']))


def main():
    paths = [CONFIG, TERRAIN, WINDOWS, NETWORK, SPASS, OSHD, 'src/descriptive/audit_snow_comparison_readiness_stage68.py',
             'reports/terrain_reference_profiles_stage67_summary.json', 'config/winter_profile_aggregation_decisions_stage45.json']
    inputs = {p: sha(p) for p in paths}
    config = json.loads((ROOT / CONFIG).read_text(encoding='utf8'))
    if any(config[k] for k in ('spatial_comparison_method_selected', 'daily_timestamp_alignment_selected', 'unit_conversion_selected', 'model_splicing_or_calibration_selected', 'automatic_group_exclusion')):
        raise ValueError('This is a readiness audit, not a new analytical method')
    groups = pd.read_csv(ROOT / TERRAIN, float_precision='round_trip')
    windows = pd.read_csv(ROOT / WINDOWS)
    network_rows = json.loads((ROOT / NETWORK).read_text(encoding='utf8'))
    networks = {row['station_group_id']: row for row in network_rows}
    if len(networks) != len(network_rows):
        raise ValueError('Duplicate original network keys')
    sp = json.loads((ROOT / SPASS).read_text(encoding='utf8'))['spass_original_metadata']['variables']
    inventory = json.loads((ROOT / OSHD).read_text(encoding='utf8'))
    spdates = metadata_dates(sp['time'])
    osdates, first, months = set(), None, []
    for source_id in config['oshd_source_ids']:
        members = inventory['archives'][source_id]['members']
        if len(members) != 12:
            raise ValueError('Require all twelve actual archived members')
        for m in members:
            v = m['netcdf']['variables']
            if first is None:
                first = v
            for name in ('easting', 'northing'):
                if v[name] != first[name]:
                    raise ValueError('Grid metadata differs across downloaded months')
            if v['hs']['attributes'].get('unit') != 'm':
                raise ValueError('OSHD literal snowdepth unit differs')
            dates = metadata_dates(v['time'])
            if osdates.intersection(dates):
                raise ValueError('Duplicated monthly date coordinates')
            osdates.update(dates)
            months.append(dict(source_id=source_id, member_name=m['member_name'], sha256=m['sha256'],
                               first_date=str(min(dates).date()), last_date=str(max(dates).date()), days=len(dates)))
    envelopes = [centre_envelope(sp, 'E', 'N'), centre_envelope(first, 'easting', 'northing')]
    if len(groups) != 70 or groups.station_group_id.duplicated().any() or set(windows.station_group_id) != set(groups.station_group_id):
        raise ValueError('Preserved group/calendar universe changed')
    rows = []
    for g in groups.itertuples():
        w = windows[windows.station_group_id.eq(g.station_group_id)]
        if len(w) != 5 or not pd.to_datetime(w.winter_end_date).lt(pd.to_datetime(w.first_base_entry_month)).all():
            raise ValueError('Exactly five own preentry winters required')
        calendars = [set(pd.date_range(r.winter_start_date, r.winter_end_date)) for r in w.itertuples()]
        sa, oa = [d.issubset(spdates) for d in calendars], [d.issubset(osdates) for d in calendars]
        if sa != w.spass_calendar_within_archive.tolist():
            raise ValueError('Old SPASS calendar availability changed')
        geom_text = networks[g.station_group_id]['exact_unique_axis_wkt']
        available = bool(geom_text)
        row = dict(source_id=SOURCE, station_group_id=g.station_group_id, station_group_name=g.station_group_name,
                   group_retained=True, mapped_axis_geometry_available=available, unique_mapped_axis_length_m=g.unique_mapped_axis_length_m,
                   requested_own_preentry_winters=5, spass_calendar_available_winters=sum(sa), spass_calendar_missing_winters=5-sum(sa),
                   downloaded_oshd_calendar_available_winters=sum(oa), both_downloaded_calendar_available_winters=sum(a and b for a,b in zip(sa,oa)),
                   missing_spass_with_downloaded_oshd_calendar_winters=sum(not a and b for a,b in zip(sa,oa)),
                   comparison_2022_winter_is_own_preentry_window=bool(w.winter_start_year.eq(2022).any()), snow_feature_computed=False)
        if available:
            xmin, ymin, xmax, ymax = wkt.loads(geom_text).bounds
            row.update(axis_min_east_2056=xmin, axis_min_north_2056=ymin, axis_max_east_2056=xmax, axis_max_north_2056=ymax)
            for label, (left, bottom, right, top) in zip(('spass', 'oshd'), envelopes):
                row['within_' + label + '_centre_envelope'] = xmin >= left and ymin >= bottom and xmax <= right and ymax <= top
        rows.append(row)
    frame = pd.DataFrame(rows).reindex(columns=DEFS)
    target = ROOT / SUMMARY
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    if target.exists():
        state = json.loads(target.read_text(encoding='utf8'))
        if state['input_sha256'] != inputs or sha(OUTPUT) != state['output_sha256'][OUTPUT]:
            raise ValueError('Frozen readiness audit changed; use a new stage')
    else:
        if len(master) != 1196 or len(dictionary) != 8084:
            raise ValueError('Reconcile unexpected registry baseline before writing')
        write_csv(frame, ROOT / OUTPUT)
        start, end = config['comparison_pilot_calendar_candidate']['start'], config['comparison_pilot_calendar_candidate']['end']
        candidate = set(pd.date_range(start, end))
        state = dict(date='2026-10-10', input_sha256=inputs, output_sha256={OUTPUT: sha(OUTPUT)},
                     prior_registry_rows_and_digest={p:dict(rows=len(f), sha256=row_digest(f)) for p,f in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]},
                     retained_groups=70, requested_group_winters=350, total_spass_calendar_missing_group_winters=int(frame.spass_calendar_missing_winters.sum()),
                     missing_spass_covered_by_downloaded_oshd_group_winters=int(frame.missing_spass_with_downloaded_oshd_calendar_winters.sum()),
                     groups_with_geometry=int(frame.mapped_axis_geometry_available.sum()),
                     geometries_inside_both_centre_envelopes=int((frame.within_spass_centre_envelope.eq(True) & frame.within_oshd_centre_envelope.eq(True)).sum()),
                     complete_downloaded_month_count=len(months), downloaded_oshd_days=len(osdates),
                     downloaded_model_common_days=len(spdates & osdates), candidate_winter_days=len(candidate), candidate_winter_calendar_complete=candidate.issubset(spdates & osdates),
                     centre_envelopes=dict(spass=envelopes[0],oshd=envelopes[1]), original_spass_time_units=sp['time']['attributes']['units'],
                     original_oshd_time_units=first['time']['attributes']['units'], oshd_months=months,
                     snow_values_read=False, snow_features_computed=False, spatial_mapping_applied=False, model_splicing_or_unit_conversion_applied=False,
                     unit_review=config['primary_unit_review'])
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    for path,f in [('metadata/data_sources_master.csv',master),('metadata/data_dictionary.csv',dictionary)]:
        baseline=state['prior_registry_rows_and_digest'][path]
        if row_digest(f.iloc[:baseline['rows']]) != baseline['sha256']:
            raise ValueError('Prior registry changed')
    source_records = [dict(source_id=config['primary_unit_review']['source_id'], variable_name='spass_numeric_unit_documentation_review',
                           variable_description='Publication HS analyticalunitcm does not certify the distributed raw numeric scale; missing raw unit retained',
                           source_organisation='WSL SLF/MeteoSwiss; The Cryosphere/EnviDat', source_page_url=config['primary_unit_review']['paper_url'],
                           retrieval_date='2026-10-10', retrieval_method='Primary webpage consultation, sections2.4/dataavailability and same dataset catalogue; no invented local archive/checksum',
                           license='Paper CC-BY4.0; distributed dataset retains its own terms', quality_notes='Original HSCLQMD unit UNKNOWN; previous metres inference retained separately, no conversion/source rewrite', notes=CONFIG),
                      dict(source_id=SOURCE, variable_name='snow_comparison_calendar_grid_readiness', variable_description='70retainedgroups/350ownwindows and36actual downloaded monthly calendars, coordinate envelopes only',
                           source_organisation='Thesis audit of retained SLF/OSM metadata', retrieval_date='2026-10-10', processed_file=OUTPUT,
                           geographic_level='Retained station groups, not municipality effects', temporal_resolution='OwnpreentryDecemberAprilcalendars and archivedmodel coordinate dates',
                           license='Parent model terms retained; OSM ODbL', retrieval_method='Frozen local metadata/calendar/geometry only; snow fields not read',
                           transformation_applied='Exact calendar containment and coordinate-envelope diagnostics; no cell matching, interpolation or conversion', quality_notes='Calendar/bbox is not observed snow coverage; no splice or selected comparison method', notes=SUMMARY)]
    pending = [r for r in source_records if r['source_id'] not in set(master.source_id)]
    if pending:
        write_csv(pd.concat([master,pd.DataFrame(pending).reindex(columns=SOURCE_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_sources_master.csv')
    records=[]
    for col,(description,unit) in DEFS.items():
        if ((dictionary.table == TABLE) & (dictionary.variable == col)).any():
            continue
        records.append(dict(variable=col,table=TABLE,description=description,unit=unit,data_type=str(frame[col].dtype),geographic_level='Station group, no duplicated municipalities',
                            temporal_level='Retained ownwintercalendars/currentgeometry envelopes',source_id=SOURCE,raw_or_derived='derived',formula=description,
                            causal_role='Metadata/provenance readiness only, not analytical snowfeature or selection filter',missing_share=f'{frame[col].isna().mean():.6f}',
                            notes='No model values read or source conversion; no automatic exclusion; current geometry not preentry certified'))
    if records:
        write_csv(pd.concat([dictionary,pd.DataFrame(records).reindex(columns=DICTIONARY_COLUMNS).fillna('')],ignore_index=True),ROOT/'metadata/data_dictionary.csv')
    print(json.dumps({k:v for k,v in state.items() if k not in ('input_sha256','output_sha256','prior_registry_rows_and_digest','oshd_months')},ensure_ascii=False))


if __name__ == '__main__':
    main()
