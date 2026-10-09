"""Inspect completed, checksum-verified OSHD archives; never read snow values.

Member bytes are extracted to interim with CRC/SHA checkpoints. Only original
dimensions/attributes and bounded one-dimensional coordinate axes are read.
No station footprint, interpolation, model splicing or feature aggregation.
"""
import hashlib
import argparse
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from contextlib import contextmanager

import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_collection.collect_oshd_profile_audit import digest
from src.data_processing.atomic_csv_output import write_csv
from src.data_processing.update_accessibility_expansion_provenance import SOURCE_COLUMNS, DICTIONARY_COLUMNS

SUMMARY = 'reports/oshd_netcdf_metadata_inventory.json'
SOURCE = 'DERIVED_OSHD_NETCDF_METADATA_AUDIT_2026_10_09'
SCRIPT = 'src/descriptive/inspect_oshd_netcdf_metadata.py'


def serial(value):
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    if isinstance(value, np.ndarray):
        return [serial(v) for v in value.tolist()] if value.ndim else serial(value.item())
    if isinstance(value, np.generic):
        return serial(value.item())
    if isinstance(value, (float, int)) and not isinstance(value, bool) and not np.isfinite(value):
        return str(value)
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    return value


def source_units(attributes):
    # OSHD snow fields use singular `unit`; preserve either original spelling.
    if 'units' in attributes:
        return str(attributes['units'])
    return str(attributes.get('unit', 'UNKNOWN'))


def safe_member(info):
    path = PurePosixPath(info.filename)
    if path.is_absolute() or '..' in path.parts or chr(92) in info.filename or info.is_dir():
        raise ValueError('Unsafe or directory ZIP member')
    if (info.external_attr >> 16) & 0o170000 == 0o120000:
        raise ValueError('Symlink ZIP member')
    return hashlib.sha256(info.filename.encode()).hexdigest()[:20] + '.nc'


@contextmanager
def ascii_link(source):
    # netCDF-C on Windows requires an ASCII path; link only our owned temp file.
    import os
    temp = Path(tempfile.mkdtemp(prefix='magic_oshd_header_'))
    if temp.resolve().parent != Path(tempfile.gettempdir()).resolve():
        raise ValueError('Unexpected temporary directory')
    link = temp / 'member.nc'
    os.link(source, link)
    try:
        yield link
    finally:
        link.unlink()
        temp.rmdir()


def metadata(dataset):
    def inspect(group):
        variables = {}
        for name, variable in group.variables.items():
            attrs = {key:serial(variable.getncattr(key)) for key in variable.ncattrs()}
            item = dict(dtype=str(variable.dtype), dimensions=list(variable.dimensions), shape=list(variable.shape), attributes=attrs)
            # Read coordinates only, never dependent HS/SWE/SCF fields, even scalar.
            if variable.ndim == 1 and variable.dimensions == (name,) and variable.size <= 100000:
                axis = np.ma.asarray(variable[:])
                observed = axis.compressed()
                item['axis'] = dict(observed_count=int(observed.size), missing_count=int(np.ma.count_masked(axis)))
                if observed.size:
                    item['axis'].update(first=serial(observed[0]), last=serial(observed[-1]))
                    if np.issubdtype(observed.dtype, np.number) and observed.size > 1:
                        differences = np.diff(observed.astype(float))
                        item['axis'].update(strictly_increasing=bool((differences > 0).all()), strictly_decreasing=bool((differences < 0).all()),
                            difference_min=float(differences.min()), difference_max=float(differences.max()))
                    if 'since' in str(attrs.get('units', '')):
                        calendar = attrs.get('calendar', 'standard')
                        decoded = num2date(observed, attrs['units'], calendar=calendar)
                        item['axis'].update(decoded_first=str(decoded[0]), decoded_last=str(decoded[-1]),
                            calendar_used=calendar, calendar_explicit_in_source='calendar' in attrs,
                            decoding_note='netCDF4 num2date output; original units retained; timezone interpretation not independently validated')
            variables[name] = item
        return dict(attributes={key:serial(group.getncattr(key)) for key in group.ncattrs()},
            dimensions={key:dict(size=len(dim), unlimited=dim.isunlimited()) for key, dim in group.dimensions.items()},
            variables=variables, groups={key:inspect(child) for key, child in group.groups.items()})
    return inspect(dataset)


def extract_member(archive, info, folder):
    filename = safe_member(info)
    target = folder / filename
    sidecar = target.with_suffix('.metadata.json')
    if target.exists():
        if not sidecar.exists():
            raise ValueError('Uncheckpointed partial extraction retained; inspect before retry')
        prior = json.loads(sidecar.read_text(encoding='utf-8'))
        if prior['member_name'] != info.filename or target.stat().st_size != info.file_size or digest(target)[1] != prior['sha256']:
            raise ValueError('Extracted member identity or hash changed')
        return target, prior
    with archive.open(info) as origin, target.open('xb') as output:
        shutil.copyfileobj(origin, output, length=1024*1024)
    if target.stat().st_size != info.file_size:
        raise ValueError('Incomplete extraction retained, not inspected')
    record = dict(member_name=info.filename, uncompressed_bytes=info.file_size,
        zip_crc32=f'{info.CRC:08x}', zip_crc_verified_by_zipfile_stream=True,
        extracted_file=target.relative_to(ROOT).as_posix(), sha256=digest(target)[1])
    sidecar.write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return target, record


def register(state):
    master = pd.read_csv(ROOT / 'metadata/data_sources_master.csv', dtype=str, keep_default_na=False)
    record = dict(source_id=SOURCE, variable_name='oshd_netcdf_original_metadata',
        variable_description='Archive members, original dimensions/attributes, coordinate/time axes only; no snow values or group profiles',
        source_organisation='Thesis audit of completed WSL SLF OSHD source archives', retrieval_date='2026-10-09',
        source_page_url='https://zenodo.org/records/17313889',
        retrieval_method='Provider MD5/size/SHA256, member stream CRC/SHA256, NetCDF headers and coordinate axes',
        local_raw_file='', processed_file=SUMMARY,
        geographic_level='Original model grids, no accepted resort footprint', temporal_resolution='Original archive metadata',
        license='Parent OSHD CC-BY4.0', transformation_applied='None to source values; no snow data read or model/source raccordement',
        quality_notes='Calendar and grid metadata do not establish valid piste cells or historical model comparability',
        notes='Parent source_ids='+ '|'.join(state['archives']) + '; original paths/checksums retained in inventory; inspector_sha256='+state['inspector_sha256'])
    write_csv(pd.concat([master[master.source_id.ne(SOURCE)], pd.DataFrame([record]).reindex(columns=SOURCE_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_sources_master.csv')
    # Register original schema once per archive/variable, retaining raw names/units.
    fields = []
    for source_id, entry in state['archives'].items():
        variants = {}
        def visit(group, prefix=''):
            for name, item in group['variables'].items():
                variants.setdefault(prefix+name, []).append(item)
            for name, child in group['groups'].items():
                visit(child, prefix+name+'/')
        for member in entry['members']:
            visit(member['netcdf'])
        for name, items in variants.items():
            attrs = items[0]['attributes']
            units = sorted({source_units(i['attributes']) for i in items})
            fields.append(dict(variable=name, table=f'oshd_original_WY{entry["water_year"]}_schema',
                description=attrs.get('long_name', attrs.get('standard_name', 'Original source variable; meaning not further inferred')),
                unit='|'.join(units), data_type='|'.join(sorted({i['dtype'] for i in items})), geographic_level='original OSHD model grid',
                temporal_level='original member coordinates/dimensions; see metadata inventory', source_id=source_id,
                raw_or_derived='raw schema only, no variable values extracted', formula='Original NetCDF attributes',
                causal_role='source-audit candidate only, not approved station feature', missing_share='',
                notes='Original unit/units attribute spelling retained in inventory. No station means, leakage rule changes or source splicing.'))
    dictionary = pd.read_csv(ROOT / 'metadata/data_dictionary.csv', dtype=str, keep_default_na=False)
    tables = {f['table'] for f in fields}
    write_csv(pd.concat([dictionary[~dictionary.table.isin(tables)], pd.DataFrame(fields).reindex(columns=DICTIONARY_COLUMNS)], ignore_index=True).fillna(''), ROOT / 'metadata/data_dictionary.csv')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-register', action='store_true', help='Inspect/checkpoint only; defer shared CSV registration while a collector is active')
    args = parser.parse_args()
    collection = json.loads((ROOT / 'reports/oshd_profile_audit_collection_summary.json').read_text(encoding='utf-8'))
    completed = [f for f in collection['files'] if f['status'] == 'complete']
    if not completed:
        print('No completed checksum-verified archive: no NetCDF inspected or schema registered.')
        return
    path = ROOT / SUMMARY
    state = json.loads(path.read_text(encoding='utf-8')) if path.exists() else dict(date='2026-10-09', archives={}, snow_values_read=False,
        group_profiles_computed=False, source_spliced=False, geographic_assignment_applied=False)
    inspector_hash = digest(ROOT / SCRIPT)[1]
    refresh_headers = state.get('inspector_sha256') != inspector_hash
    for file in completed:
        raw = ROOT / file['raw_file']
        if not file.get('provider_md5_verified') or raw.stat().st_size != file['expected_bytes'] or digest(raw) != (file['expected_md5'], file['sha256']):
            raise ValueError('Require exact completed provider archive')
        folder = ROOT / 'data_interim/oshd_metadata_members' / f'WY{file["water_year"]}'
        folder.mkdir(parents=True, exist_ok=True)
        entry = state['archives'].setdefault(file['source_id'], dict(water_year=file['water_year'], raw_file=file['raw_file'],
            archive_sha256=file['sha256'], members=[]))
        if entry['archive_sha256'] != file['sha256']:
            raise ValueError('Never replace an already inspected source')
        with zipfile.ZipFile(raw) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError('Duplicate ZIP names')
            for info in archive.infolist():
                if info.is_dir() or not info.filename.lower().endswith('.nc'):
                    continue
                previous = [m for m in entry['members'] if m['member_name'] == info.filename]
                if previous:
                    cached = ROOT / previous[0]['extracted_file']
                    if digest(cached)[1] != previous[0]['sha256']:
                        raise ValueError('Cached extraction changed')
                    if refresh_headers:
                        with ascii_link(cached) as link, Dataset(str(link), 'r') as dataset:
                            previous[0]['netcdf'] = metadata(dataset)
                    continue
                if shutil.disk_usage(folder).free < info.file_size + 512*1024*1024:
                    raise ValueError('Insufficient free disk for one source member')
                target, record = extract_member(archive, info, folder)
                with ascii_link(target) as link, Dataset(str(link), 'r') as dataset:
                    record['netcdf'] = metadata(dataset)
                entry['members'].append(record)
                path.write_text(json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
                print(file['key'], info.filename, 'headers/coordinate axes inspected; no snow values', flush=True)
    state['inspector_sha256'] = inspector_hash
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    if not args.no_register:
        register(state)
    print('OSHD metadata inventory:', sum(len(a['members']) for a in state['archives'].values()), 'members; no profile or splicing.')


if __name__ == '__main__':
    main()
