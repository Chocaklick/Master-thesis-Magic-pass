"""Documentary evidence must not silently become a snow unit/time correction."""
import io
import json
import subprocess
from pathlib import Path

import pandas as pd
import pytest

from src.descriptive.audit_snow_compatibility_stage73 import fixed_reference_utc_hour, evidence, plain, DEFS, SPASS_PAPER, OSHD_PAPER
from src.data_processing.prepare_native_snow_weights_stage69 import digest
from src.descriptive.summarise_terrain_reference_stage67 import row_digest

ROOT=Path(__file__).resolve().parents[1]


def claims():
    return pd.read_csv(ROOT/'data_processed/snow_compatibility_evidence_stage73.csv').set_index('claim_id')


def test_fixed_cet_not_dst_or_six_utc():
    for date in ['2023-01-01','2023-07-01','2024-03-01']:
        assert fixed_reference_utc_hour('days since '+date+'T06:00:00 UTC+01:00')==5
    for text in ['days since 2023-01-01','days since 2023-01-01T06:00:00 UTC','days since 2023-01-01T06:00:00 UTC+02:00']:
        with pytest.raises(ValueError):
            fixed_reference_utc_hour(text)


def test_unknown_output_not_inferred_from_forcing_or_default():
    f=claims()
    assert len(f)==15 and len(DEFS)==14 and not f.analytical_change_applied.any()
    assert f.loc['spass_unit','source_unit']=='UNKNOWN'
    assert f.loc['spass_unit','evidence_status']=='unresolved'
    assert pd.isna(f.loc['spass_time_label','documented_utc_hour'])
    assert f.loc['spass_precipitation_window','target']=='forcing_time_window'
    assert f.loc['swe2hs_configurable_default','evidence_status']=='scoped_software_only'
    assert f.loc['oshd_snapshot','documented_utc_hour']==5


def test_publication_proves_snapshot_and_daily_use_warning():
    t=plain(evidence(OSHD_PAPER))
    assert 'representing states at that time' in t and '06:00 Central European Time' in t
    s=plain(evidence(SPASS_PAPER))
    assert 'Daily aggregations were by purpose not assessed' in s
    assert 'high temporal resolution is not recommended' in s
    assert 'midnight to midnight UTC' in s and '06:00 UTC of day D' in s
    assert 'OSHD-EKF' in s and 'OSHD-Comb' in s
    assert 'particle filter' in t and '444' in t


def test_all_original_headers_agree_without_reading_snow():
    x=json.loads((ROOT/'reports/oshd_netcdf_metadata_inventory.json').read_text(encoding='utf8'))
    rows=[m for a in x['archives'].values() for m in a['members']]
    assert len(rows)==36
    for r in rows:
        v=r['netcdf']['variables']
        assert v['hs']['attributes']['unit']=='m'
        assert fixed_reference_utc_hour(v['time']['attributes']['units'])==5
    s=json.loads((ROOT/'reports/snow_grid_metadata_compatibility_stage47.json').read_text(encoding='utf8'))
    v=s['spass_original_metadata']['variables']
    assert 'unit' not in v['HSCLQMD']['attributes'] and 'units' not in v['HSCLQMD']['attributes']
    assert v['time']['attributes']['units']=='days since 1900-01-01'


def test_researcher_b_and_guards_are_explicit():
    x=json.loads((ROOT/'reports/snow_compatibility_stage73_summary.json').read_text(encoding='utf8'))
    assert x['decisions']['researcher_reply']=='B — Approfondir la compatibilité avant les profils'
    assert x['reference_date_offset_days']==0 and x['producer_confirmation_needed']
    for k in ['source_spliced','unit_converted','final_profiles_computed','additional_aggregation_computed','groups_or_municipalities_excluded','analytical_outputs_changed']:
        assert x[k] is False
    assert x['spass_output_instant']==x['spass_output_timezone']==x['spass_snow_unit']=='UNKNOWN'


def test_every_claim_has_real_evidence_and_registered_source():
    f=claims()
    sources=pd.read_csv(ROOT/'metadata/data_sources_master.csv').source_id
    for r in f.itertuples():
        assert r.source_id in set(sources)
        assert digest(r.evidence_file)==r.evidence_sha256
        assert str(r.locator) and str(r.proof_limit_fr)


def test_registry_and_collection_prefixes_preserved():
    x=json.loads((ROOT/'reports/snow_compatibility_stage73_summary.json').read_text(encoding='utf8'))
    for path, extra in [('metadata/data_sources_master.csv',7),('metadata/data_dictionary.csv',14)]:
        new=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
        b=x['prior_registry_rows_and_digest'][path]
        assert len(new)>=b['rows']+extra and row_digest(new.iloc[:b['rows']])==b['sha256']
        old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','86b6e37:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
        assert old.equals(new.iloc[:len(old)].reset_index(drop=True))
    path='logs/data_collection_log.csv'
    new=pd.read_csv(ROOT/path,dtype=str,keep_default_na=False)
    old=pd.read_csv(io.BytesIO(subprocess.check_output(['git','show','86b6e37:'+path],cwd=ROOT)),dtype=str,keep_default_na=False)
    assert old.equals(new.iloc[:len(old)].reset_index(drop=True))
    # Later documentary stages append their own events; audit the frozen
    # Stage73 block without prohibiting subsequent authorised collection.
    events=new.iloc[len(old):len(old)+10]
    assert len(events)==10 and (events.success=='True').sum()==6 and (events.success=='False').sum()==4
