"""Real pilot source lineage, native values, cell weights and observed coverage."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from src.descriptive.verify_piste_assignments_stage51 import sha
ROOT=Path(__file__).resolve().parents[1]


def test_all84tiles_have_official_checksums_and_native_units():
    s=json.loads((ROOT/'reports/native2m_terrain_pilot_stage63_summary.json').read_text(encoding='utf8'))
    assert s['original_tile_count']==84 and len(s['header_checks'])==84
    assert all(x['units']==['metre'] and x['crs']=='EPSG:2056' for x in s['header_checks'])
    assert all(sha(p)==h for p,h in {**s['input_sha256'],**s['output_sha256']}.items())


def test_identical_native_cells_weights_between_editions_and_full_coverage():
    f=pd.read_csv(ROOT/'data_processed/terrain_native2m_pilot_cells_stage63.csv')
    parts=[p.sort_values(['cell_row','cell_col']).reset_index(drop=True) for _,p in f.groupby('edition_reference_datetime')]
    assert len(parts)==2 and all(len(p)==31806 for p in parts)
    cols=['cell_row','cell_col','cell_centre_east_2056','cell_centre_north_2056','unique_axis_length_m']
    pd.testing.assert_frame_equal(parts[0][cols],parts[1][cols],check_exact=True)
    assert f.altitude_observed.all() and f.gradient_observed.all() and f.centre_tile_source_id.notna().all()
    assert not f.duplicated(['edition_reference_datetime','cell_row','cell_col']).any()


def test_native_altitude_values_are_direct_source_cells_not_interpolated():
    f=pd.read_csv(ROOT/'data_processed/terrain_native2m_pilot_cells_stage63.csv').iloc[::997]
    for sid,p in f.groupby('centre_tile_source_id'):
        metadata=list((ROOT/'data_external/source_evidence').glob(sid+'_*.metadata.json'))
        m=json.loads(metadata[0].read_text(encoding='utf8'))
        with rasterio.open(ROOT/m['raw_file']) as d:
            values=[float(v[0]) for v in d.sample(zip(p.cell_centre_east_2056,p.cell_centre_north_2056))]
        np.testing.assert_allclose(values,p.altitude_m,rtol=1e-12,atol=1e-10)


def test_all_old_group_lengths_and_original_objects_preserved():
    old=pd.read_csv(ROOT/'data_processed/winter_profile_exact_piste_overlap_stage58.csv')
    new=pd.read_csv(ROOT/'data_processed/winter_profile_exact_piste_overlap_stage63.csv')
    mask=old.station_group_id.ne('MP_GROUP_RESORT__st_luc_chandolin')
    cols=[c for c in old if c not in ['source_id','parent_source_ids']]
    pd.testing.assert_frame_equal(old.loc[mask,cols],new.loc[mask,cols],check_dtype=False,rtol=1e-12,atol=1e-10)
    assert len(new)==70 and new.group_retained.all() and new.candidate_axis_count.sum()==846
    assert new.individual_metric_use_verified.eq(False).all()


def test_weighted_statistics_recompute_without_missing_to_zero():
    f=pd.read_csv(ROOT/'data_processed/terrain_native2m_pilot_cells_stage63.csv')
    stats=pd.read_csv(ROOT/'data_processed/terrain_native2m_pilot_summary_stage63.csv')
    for r in stats.itertuples():
        p=f[f.edition_reference_datetime.eq(r.edition_reference_datetime)]
        np.testing.assert_allclose(np.average(p.altitude_m,weights=p.unique_axis_length_m),r.length_weighted_observed_altitude_m,rtol=1e-12)
        np.testing.assert_allclose(p.unique_axis_length_m.sum(),r.unique_mapped_axis_length_m,rtol=1e-12)
        assert r.missing_altitude_length_m==0 and r.missing_gradient_length_m==0
        assert r.current_candidate_proxy_not_verified_preentry
