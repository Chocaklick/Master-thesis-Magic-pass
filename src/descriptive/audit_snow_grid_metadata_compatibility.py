"""Compare source schemas only, with no snow-field reading or spatial mapping."""
import json
import sys
from pathlib import Path

import pandas as pd
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.descriptive.inspect_oshd_netcdf_metadata import ascii_link, metadata, source_units
from src.data_collection.collect_oshd_profile_audit import digest
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

OUTPUT = 'reports/snow_grid_metadata_compatibility_stage47.json'
SCRIPT = 'src/descriptive/audit_snow_grid_metadata_compatibility.py'
SOURCE = 'DERIVED_SNOW_GRID_METADATA_COMPATIBILITY_STAGE47'


def main():
    config_path = ROOT / 'config/spass_snow_grid.json'
    config = json.loads(config_path.read_text(encoding='utf-8'))
    matches = list((ROOT / 'data_external/source_evidence').glob(config['source_id']+'_*.metadata.json'))
    if len(matches) != 1:
        raise ValueError('Require one original SPASS provenance record')
    record = json.loads(matches[0].read_text(encoding='utf-8'))
    raw = ROOT / record['extracted_file']
    if record['extracted_sha256'] != config['member_sha256'] or raw.stat().st_size != config['member_uncompressed_size_bytes']:
        raise ValueError('SPASS source identity changed')
    manifest_path = ROOT / 'reports/oshd_netcdf_metadata_inventory.json'
    oshd = json.loads(manifest_path.read_text(encoding='utf-8'))
    if not oshd['archives'] or oshd['inspector_sha256'] != digest(ROOT / 'src/descriptive/inspect_oshd_netcdf_metadata.py')[1]:
        raise ValueError('Require current completed OSHD metadata audit')
    pins = {p.relative_to(ROOT).as_posix():digest(p)[1] for p in [config_path, matches[0], manifest_path, ROOT / SCRIPT]}
    output = ROOT / OUTPUT
    if output.exists():
        previous = json.loads(output.read_text(encoding='utf-8'))
        if previous['input_sha256'] == pins:
            if digest(raw)[1] != config['member_sha256']:
                raise ValueError('SPASS NetCDF bytes changed')
            print('Exact snow schema checkpoint reused; no values, requests or registration writes.')
            return
    if digest(raw)[1] != config['member_sha256']:
        raise ValueError('SPASS NetCDF hash changed')
    with ascii_link(raw) as link, Dataset(str(link), 'r') as dataset:
        spass = metadata(dataset)
    snow = spass['variables']['HSCLQMD']
    state = dict(date='2026-10-09', input_sha256=pins, spass_source_id=config['source_id'],
        spass_raw_file=record['extracted_file'], spass_netcdf_sha256=config['member_sha256'],
        spass_original_metadata=spass, oshd_inventory='reports/oshd_netcdf_metadata_inventory.json',
        oshd_source_ids=list(oshd['archives']), snow_values_read=False, spatial_mapping_applied=False,
        snow_models_spliced=False, station_profiles_computed=False,
        comparison_notes=[
            'SPASS HSCLQMD and OSHD hs represent modelled snow depth, not piste measurements.',
            'Different resolution and axis order: never compare array indices as shared cells.',
            'Use each source coordinate axes and raw dimension order; northing orientation may differ.',
            'No matching/interpolation, validation threshold, calibration or snow substitution approved by this audit.',
            'Original unit/units metadata retained. The prior SPASS metre interpretation is not an original unit attribute.',
            'The current OSHD WY2024 archive follows the end of SPASS; it alone cannot support a temporal overlap comparison.',
            'Decoded timestamps retain original time units; timezone interpretation needs separate verification if hours matter.'
        ])
    output.write_text(json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    source = dict(source_id=SOURCE, variable_name='snow_grid_original_schema_comparison',
        variable_description='Original SPASS and completed OSHD metadata comparison; no snow fields read',
        source_organisation='Thesis source compatibility audit', retrieval_date='2026-10-09',
        source_page_url=config['source_page_url']+'|https://zenodo.org/records/17313889',
        retrieval_method='Full cached SPASS SHA256/size check, NetCDF headers and coordinate axes; completed OSHD inventory',
        local_raw_file='', processed_file=OUTPUT, geographic_level='original model grids',
        temporal_resolution='source coordinate axes only', license='Parent SPASS WSL Data Policy; OSHD CC-BY4.0',
        transformation_applied='No spatial support matching, snow means or model splicing',
        quality_notes='Different model definitions/resolution, omitted SPASS unit; no independent ground truth or causal approval',
        notes='Parent source_ids='+config['source_id']+'|'+'|'.join(oshd['archives'])+'; original paths/hashes retained in comparison inventory, not owned by this derived source')
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([source]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    table = 'spass_original_schema_metadata_stage47'
    fields = [dict(variable=name, table=table, description=item['attributes'].get('long_name', item['attributes'].get('standard_name', 'Original SPASS source variable; meaning not inferred')),
        unit=source_units(item['attributes']), data_type=item['dtype'], geographic_level='original SPASS model grid',
        temporal_level='original coordinate axes/dimensions', source_id=config['source_id'], raw_or_derived='raw schema only',
        formula='Original NetCDF attributes retained in metadata inventory', causal_role='source-audit candidate only',
        missing_share='', notes='No dependent snow field read; omitted unit remains UNKNOWN, prior metre interpretation separate')
        for name, item in spass['variables'].items()]
    write_csv(pd.concat([dictionary[dictionary.table.ne(table)], pd.DataFrame(fields).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')
    print('SPASS/OSHD schema audit complete; SPASS original snow unit:', source_units(snow['attributes']))


if __name__ == '__main__':
    main()
