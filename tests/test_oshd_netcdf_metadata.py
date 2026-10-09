import zipfile
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from src.descriptive.inspect_oshd_netcdf_metadata import metadata, safe_member, serial, source_units


def test_unsafe_member_paths_rejected_and_stable_unique_names():
    for path in ['../file.nc', '/file.nc', 'dir\\file.nc', 'folder/']:
        info = zipfile.ZipInfo(path)
        # ZipInfo creation normalizes separators on Windows; emulate a raw name.
        info.filename = path
        with pytest.raises(ValueError):
            safe_member(info)
    assert safe_member(zipfile.ZipInfo('first/file.nc')) != safe_member(zipfile.ZipInfo('second/file.nc'))
    assert serial(np.float32(np.nan)) == 'nan'
    assert serial(np.array([1, 2])) == [1, 2]


def test_original_singular_units_not_lost():
    assert source_units({'unit':'m'}) == 'm'
    assert source_units({'units':'days since 2023-09-01'}) == 'days since 2023-09-01'
    assert source_units({}) == 'UNKNOWN'


def test_only_original_coordinate_axis_is_read_never_snow_field():
    class Variable:
        def __init__(self, name, shape, dims, attrs, values=None):
            self.name=name; self.shape=shape; self.dimensions=dims; self.ndim=len(shape); self.size=int(np.prod(shape)); self.dtype=np.dtype('float32'); self.attrs=attrs; self.values=values
        def ncattrs(self): return list(self.attrs)
        def getncattr(self, key): return self.attrs[key]
        def __getitem__(self, key):
            if self.values is None: raise AssertionError('Snow field was read')
            return self.values
    class Dimension:
        def __init__(self, length): self.length=length
        def __len__(self): return self.length
        def isunlimited(self): return False
    dataset = SimpleNamespace(variables={
        'time': Variable('time', (2,), ('time',), {'units':'days since 2023-09-01', 'calendar':'standard'}, np.array([0.,1.])),
        'HS': Variable('HS', (2,3), ('time','x'), {'units':'m', '_FillValue': np.float32(-9999)}),
        'x': Variable('x', (3,), ('x',), {'units':'m'}, np.array([200.,450.,700.]))},
        dimensions={'time':Dimension(2), 'x':Dimension(3)}, groups={}, ncattrs=lambda:[])
    result = metadata(dataset)
    assert result['variables']['time']['axis']['decoded_first'].startswith('2023-09-01')
    assert result['variables']['x']['axis']['difference_min'] == 250
    assert 'axis' not in result['variables']['HS']
    assert result['variables']['HS']['attributes']['_FillValue'] == -9999


def test_real_source_schemas_and_no_silent_snow_mapping():
    root = Path(__file__).resolve().parents[1]
    oshd = json.loads((root/'reports/oshd_netcdf_metadata_inventory.json').read_text(encoding='utf-8'))
    archive = oshd['archives']['SLF_OSHD_PF_WY2024_PROFILE_AUDIT']
    assert len(archive['members']) == 12
    variables = archive['members'][0]['netcdf']['variables']
    assert variables['hs']['dimensions'] == ['easting','northing','time']
    assert source_units(variables['hs']['attributes']) == 'm'
    assert variables['northing']['axis']['difference_min'] == -250
    assert sum(m['netcdf']['variables']['time']['axis']['observed_count'] for m in archive['members']) == 366
    assert not any(oshd[key] for key in ['snow_values_read','group_profiles_computed','source_spliced','geographic_assignment_applied'])
    comparison = json.loads((root/'reports/snow_grid_metadata_compatibility_stage47.json').read_text(encoding='utf-8'))
    spass = comparison['spass_original_metadata']['variables']
    assert spass['HSCLQMD']['dimensions'] == ['time','N','E']
    assert source_units(spass['HSCLQMD']['attributes']) == 'UNKNOWN'
    assert spass['N']['axis']['difference_min'] == 1000
    assert not any(comparison[key] for key in ['snow_values_read','spatial_mapping_applied','snow_models_spliced','station_profiles_computed'])


def test_official_navigation_keeps_only_observed_links():
    from src.descriptive.register_piste_operator_evidence_stage47 import navigation
    links = navigation('<a href="../pistes">Les pistes</a><a href="mailto:test@example.com">Contact</a><a href="../pistes">Les pistes</a>', 'https://example.com/web/')
    assert links == [{'url':'https://example.com/pistes','label':'Les pistes','original_href':'../pistes'}]
