import json
from pathlib import Path

from src.descriptive.preview_december_april_support import months, compute


def test_five_month_window_and_recorded_preview():
    assert months(2025) == ['2025-12', '2026-01', '2026-02', '2026-03', '2026-04']
    root = Path(__file__).resolve().parents[1]
    decisions = json.loads((root / 'config/winter_profile_researcher_decisions.json').read_text(encoding='utf-8'))
    assert decisions['validated_winter_months'] == [12, 1, 2, 3, 4]
    assert compute() == decisions['december_april_support_preview']
    assert not decisions['new_effect_estimation_approved']
    assert not decisions['clustering_experiment_approved']
    assert not decisions['additional_entry_estimator_approved']


def test_sources_and_preview_variable_definitions_registered():
    import csv
    root = Path(__file__).resolve().parents[1]
    with (root/'metadata/data_sources_master.csv').open(encoding='utf-8', newline='') as handle:
        sources = list(csv.DictReader(handle))
    assert len({r['source_id'] for r in sources}) == len(sources)
    assert {'CHAIS_HAULT_INTERTEMPORAL_DID_ARXIV_V14', 'CHAIS_HAULT_SEVERAL_TREATMENTS_ARXIV_V8',
            'SKLEARN_CLUSTERING_METHODS_2026_10_08', 'DERIVED_DEC_APR_SUPPORT_PREVIEW_2026_10_08'}.issubset({r['source_id'] for r in sources})
    with (root/'metadata/data_dictionary.csv').open(encoding='utf-8', newline='') as handle:
        definitions = list(csv.DictReader(handle))
    assert len({(r['table'], r['variable']) for r in definitions}) == len(definitions)
    assert set(compute()['30']) == {r['variable'] for r in definitions if r['table'] == 'dec_apr_support_preview'}
