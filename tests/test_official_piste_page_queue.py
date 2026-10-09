import pandas as pd
import pytest

from src.data_collection.collect_group_piste_pages import make_queue


def test_queue_joins_ids_not_names_and_retains_unresolved_fallback():
    points=pd.DataFrame([dict(station_group_id='group1',access_point_id='ACCESS_MAGIC_CURRENT__4'),
        dict(station_group_id='group2',access_point_id='ACCESS_BAV__1')])
    destinations=pd.DataFrame([dict(official_destination_id='4',official_destination_path='/fr/stations/anzere-4',official_destination_name='Anzere')])
    sources,links=make_queue(points,destinations,{'https://www.magicpass.ch/fr/stations/anzere-4':'ALREADY_ARCHIVED'})
    assert sources[0]['source_id']=='ALREADY_ARCHIVED'
    assert links[1]['source_id'] is None and links[1]['station_group_id']=='group2'
    points.loc[0,'access_point_id']='ACCESS_MAGIC_CURRENT__999'
    with pytest.raises(ValueError):
        make_queue(points,destinations,{})
