import pandas as pd
import pytest
from src.data_collection.collect_piste_operator_evidence_stage53 import local_network_block, local_url_encoding_error, request_url
from src.descriptive.verify_piste_assignments_stage53 import validate_official_links, overlay


def test_local_socket_restriction_is_not_provider_refusal():
    assert local_network_block('URLError: [WinError 10013] socket permission')
    for message in ['HTTP Error 403: Forbidden','certificate verify failed','HTTP Error 404']:
        assert not local_network_block(message)


def test_literal_unicode_url_encoded_without_double_encoding():
    assert local_url_encoding_error("UnicodeEncodeError: 'ascii' codec can't encode")
    assert request_url('https://example.ch/über-uns/a%20b?q=été&x=1')=='https://example.ch/%C3%BCber-uns/a%20b?q=%C3%A9t%C3%A9&x=1'


def test_scope_links_must_be_literal():
    source=dict(source_id='S',parent_source_id='P',station_group_id='G',url='https://a.example/scope')
    validate_official_links([source],{'P':{'observed_links':[{'url':source['url']}]}},{},[])
    with pytest.raises(ValueError):validate_official_links([source],{'P':{'observed_links':[]}},{},[])


def test_official_join_cannot_be_name_only():
    source=dict(source_id='S',parent_source_id='P',station_group_id='G',url='https://a.example/scope')
    pages={'P':{'navigation_links':[{'label':'Site web','url':source['url']}]}}
    with pytest.raises(ValueError):validate_official_links([source],{},pages,[{'station_group_id':'OTHER','source_id':'P'}])


def test_search_discovery_alone_is_not_stable_identity():
    source=dict(source_id='S',parent_source_id='DISCOVERY_PISTE_SOURCE_STAGE53',identity_parent_source_id='P',station_group_id='G',url='https://a.example/new')
    with pytest.raises(ValueError):validate_official_links([source],{}, {'P':{}},[],[source['url']])
    with pytest.raises(ValueError):validate_official_links([source],{}, {'P':{}},[{'station_group_id':'G','source_id':'P'}],[])


def test_no_unrecorded_missing_or_extra_group():
    prior=pd.DataFrame({'station_group_id':['G'],'current_site_correspondence_verified':['False']})
    with pytest.raises(ValueError,match='universe'):overlay(prior,[],{},{},[])
    with pytest.raises(ValueError,match='universe'):overlay(prior,[{'station_group_id':'OTHER'}],{},{},[])


def test_duplicate_curated_cases_rejected():
    prior=pd.DataFrame({'station_group_id':['G'],'current_site_correspondence_verified':['False']})
    with pytest.raises(ValueError,match='Duplicate'):overlay(prior,[{'station_group_id':'G'}]*2,{},{},[])
