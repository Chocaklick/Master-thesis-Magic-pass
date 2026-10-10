"""Verify protected originals/results once; reference rather than duplicate manifest."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data_processing.prepare_native_snow_weights_stage69 import digest


def main():
    parent_path = 'reports/preservation_stage73_summary.json'
    prior = json.loads((ROOT/parent_path).read_text(encoding='utf8'))
    checks = list(prior['checks'])
    extra = {}
    for path in ['reports/spass_unit_investigation_stage74.json', 'reports/native_snow_metric_diagnostic_stage75_summary.json']:
        obj = json.loads((ROOT/path).read_text(encoding='utf8'))
        extra[path] = digest(path)
        extra.update(obj['input_sha256'])
        extra.update(obj.get('output_sha256', {}))
    checks.extend(dict(path=p, sha256=h) for p, h in extra.items())
    cache = {}
    for row in checks:
        p = row['path']
        if p not in cache:
            cache[p] = digest(p)
        if cache[p] != row['sha256']:
            raise ValueError('Protected file changed: '+p)
    state = dict(date='2026-10-10', parent_manifest=parent_path, parent_manifest_sha256=digest(parent_path),
                 protected_reference_count=len(checks), protected_unique_file_count=len(cache),
                 additional_checks=extra, old_results_and_originals_unchanged=True,
                 new_metric_outputs_added=True, no_collection_requests=True)
    target = ROOT/'reports/preservation_stage75_summary.json'
    if target.exists():
        if json.loads(target.read_text(encoding='utf8')) != state:
            raise ValueError('Frozen preservation changed; use a new stage')
    else:
        target.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:v for k,v in state.items() if k!='additional_checks'}))


if __name__ == '__main__':
    main()
