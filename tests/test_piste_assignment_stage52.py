import pandas as pd
import pytest
from src.descriptive.verify_piste_assignments_stage52 import preserve_previous, available_document


def prior_frame():
    return pd.DataFrame({'station_group_id':[f'G{i}' for i in range(71)],
        'current_site_correspondence_verified':['True']+['False']*70,'note':['Original']*71})


def test_retention_and_prior_accepted_rows_unchanged():
    prior=prior_frame();current=prior.copy()
    current.loc[1,'current_site_correspondence_verified']='True'
    preserve_previous(prior,current)
    current.loc[0,'note']='Rewritten'
    with pytest.raises(ValueError):preserve_previous(prior,current)


def test_group_drop_and_duplicate_rejected():
    prior=prior_frame()
    with pytest.raises(ValueError):preserve_previous(prior,prior.iloc[:-1])
    changed=prior.copy();changed.loc[70,'station_group_id']='G0'
    with pytest.raises(ValueError):preserve_previous(prior,changed)


def test_unknown_original_is_not_fabricated():
    assert available_document({'source_id':'NONEXISTENT_STAGE52_TEST_SOURCE','url':'https://invalid.example/'}) is None
