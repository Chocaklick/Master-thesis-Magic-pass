"""Register serialized missingness; verify all frozen and historical provenance."""
import json
import hashlib
import subprocess
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import pandas as pd
from src.data_processing.atomic_csv_output import write_csv

REGISTRY = ['metadata/data_sources_master.csv', 'metadata/data_dictionary.csv', 'logs/data_collection_log.csv']


def sha(path):
    # Low-memory launcher: no plotting/geospatial imports, bounded reusable buffer.
    result = hashlib.sha256()
    buffer = bytearray(65536)
    with (ROOT / path).open('rb', buffering=0) as source:
        while length := source.readinto(buffer):
            result.update(memoryview(buffer)[:length])
    return result.hexdigest()


def read(path):
    return pd.read_csv(ROOT / path, dtype=str, keep_default_na=False)


def digest(frame):
    return hashlib.sha256(frame.to_csv(index=False, lineterminator='\n').encode('utf-8')).hexdigest()

MANIFESTS = ['reports/common_snow_profiles_stage84_summary.json',
             'reports/national_similarity_inventory_stage85_summary.json',
             'reports/national_similarity_context_stage86_summary.json']
SUMMARY = 'reports/preservation_national_stage87_summary.json'


def main():
    parent_path = 'reports/preservation_stage83_summary.json'
    parent = json.loads((ROOT / parent_path).read_text(encoding='utf-8'))
    hashes = {r['path']: r['sha256'] for r in parent['checks']}
    outputs = []
    for path in MANIFESTS:
        m = json.loads((ROOT / path).read_text(encoding='utf-8'))
        candidates = m['input_sha256'] | m['output_sha256'] | {path: sha(path)}
        outputs.extend(m['output_sha256'])
        for checkpoint in m.get('daily_checkpoints', {}).values():
            candidates[checkpoint['path']] = checkpoint['sha256']
            candidates[checkpoint['metadata']] = checkpoint['metadata_sha256']
        for p, h in candidates.items():
            if p in hashes and hashes[p] != h:
                raise ValueError('Conflicting frozen input/output ' + p)
            hashes[p] = h
    hashes[parent_path] = sha(parent_path)
    hashes['src/descriptive/check_national_preparation_stage87.py'] = sha('src/descriptive/check_national_preparation_stage87.py')
    # Dictionary repair only, after numerical producers were frozen. Blank fields in
    # a serialized scientific CSV are missing even if their producer used "".
    dictionary_path = ROOT / 'metadata/data_dictionary.csv'
    dictionary = read('metadata/data_dictionary.csv')
    repairs = []
    for p in outputs:
        f = pd.read_csv(ROOT / p, dtype=str, keep_default_na=False)
        table = Path(p).stem
        part = dictionary[dictionary.table.eq(table)]
        if not part.variable.is_unique or set(part.variable) != set(f.columns):
            raise ValueError('Dictionary schema differs ' + table)
        for v in part.itertuples():
            observed = f[v.variable].eq('').mean()
            if abs(float(v.missing_share) - observed) > .00000051:
                mask = dictionary.table.eq(table) & dictionary.variable.eq(v.variable)
                repairs.append(dict(table=table, variable=v.variable, previous=v.missing_share, serialized_share=f'{observed:.6f}'))
                dictionary.loc[mask, 'missing_share'] = f'{observed:.6f}'
        # Retain literal query lineage IDs without inventing hundreds of external sources.
        if 'source_ids' in f:
            mask = dictionary.table.eq(table) & dictionary.variable.eq('source_ids')
            dictionary.loc[mask, 'notes'] = (
                'Registered parent sources plus literal GEO_POINT_* query identifiers from original resort_point_municipality; '
                'queries belong to GEOADMIN_MUNICIPALITY_IDENTIFY, not new external datasets. '
                'Archived MAGIC_CURRENT_MAP remains catalogue-candidate provenance; absence is not verified nonmembership.')
    if repairs or not dictionary.equals(read('metadata/data_dictionary.csv')):
        write_csv(dictionary, dictionary_path)
    for index, (p, h) in enumerate(hashes.items(), 1):
        if sha(p) != h:
            raise ValueError('Historical/frozen result or source changed ' + p)
        if index % 400 == 0:
            print('Verified', index, 'files', flush=True)
    prefixes = {}
    for p in REGISTRY:
        old = pd.read_csv(StringIO(subprocess.check_output(['git', 'show', 'b639eea:' + p], cwd=ROOT).decode('utf-8-sig')),
                          dtype=str, keep_default_na=False)
        actual = read(p)
        if not actual.iloc[:len(old)].reset_index(drop=True).equals(old):
            raise ValueError('Historical registry prefix changed ' + p)
        prefixes[p] = dict(previous_rows_exact=len(old), previous_row_digest=digest(old),
                           current_rows=len(actual), appended_rows=len(actual) - len(old))
    groups = pd.read_csv(ROOT / 'data_processed/accessibility_station_groups_stage79.csv')
    if len(groups) != 69:
        raise ValueError('No new physical group merge allowed in this preparation')
    state = dict(checked_at=datetime.now(timezone.utc).isoformat(), baseline_commit='b639eea',
                 historical_unique_files=len(parent['checks']), checked_unique_files=len(hashes),
                 original_sources_old_preentry_results_caches_and_exposures_unchanged=True,
                 no_new_external_request_ORSpoints_or_French_relief=True,
                 old_lift_clusters_connected_groups_and_municipal_outcomes_unchanged=True,
                 no_prediction_causal_fit_clustering_or_automatic_sample_filter=True,
                 registry_prefixes_exact=prefixes, serialized_missingness_repairs=repairs,
                 checks=[dict(path=p, sha256=h) for p, h in hashes.items()])
    target = ROOT / SUMMARY
    if target.exists():
        existing = json.loads(target.read_text(encoding='utf-8'))
        if existing['checks'] != state['checks'] or existing['registry_prefixes_exact'] != prefixes:
            raise ValueError('Previously completed preservation audit differs')
    else:
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in state.items() if k != 'checks'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
