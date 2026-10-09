import json
from pathlib import Path


def test_researcher_approves_only_two_metre_terrain_resolution():
    root = Path(__file__).resolve().parents[1]
    decision = json.loads((root / 'config/winter_profile_terrain_decisions_stage48.json').read_text(encoding='utf-8'))
    assert decision['researcher_reply'] == '2m de relief'
    assert decision['dem_dataset'] == 'swissALTI3D'
    assert decision['dem_grid_resolution_m'] == 2
    assert decision['dem_resolution_approved']
    assert decision['dem_tile_vintage_must_be_retained']
    assert decision['historical_uncertainty_must_be_explicit']
    assert decision['surface_only_piste_rule'] is None
    assert decision['terrain_flat_aspect_threshold_degrees'] is None
    assert not decision['snow_model_splicing_or_calibration_approved']
    assert not decision['automatic_exclusion_approved']
    assert all((root / path).is_file() for path in decision['parent_decisions'])
