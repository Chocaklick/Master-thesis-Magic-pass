"""Read-only December-April coverage preview; no estimates or source rewrites."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = 'data_processed/accessibility_municipality_month_exposure_territorial.csv'
SUPPORT = 'reports/winter_profile_municipality_support_audit.csv'


def months(year):
    return [f'{year}-12'] + [f'{year+1}-{m:02}' for m in [1, 2, 3, 4]]


def compute():
    panel = defaultdict(set)
    with (ROOT/PANEL).open(encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle):
            if row['hotel_overnights'] != '':
                panel[row['municipality_bfs_id']].add(row['date'][:7])
    with (ROOT/SUPPORT).open(encoding='utf-8', newline='') as handle:
        rows = [r for r in csv.DictReader(handle) if r['winter_definition'] == 'nov_apr']
    result = {}
    for threshold in ['15', '30', '45']:
        sub = [r for r in rows if r['threshold_minutes'] == threshold and r['first_winter_exposure_month']]
        counts = dict(exposed_territories=len(sub), complete_pre_and_post=0,
                      first_post_complete=0, immediate_pre_and_first_post_complete=0,
                      first_two_post_complete=0)
        for row in sub:
            observed = panel[row['municipality_bfs_id']]
            complete = {y: all(m in observed for m in months(y)) for y in range(2012, 2027)}
            base = row['first_base_exposure_month'][:7]
            first = row['first_winter_exposure_month'][:7]
            year = int(first[:4])
            pre = any(ok and months(y)[-1] < base for y, ok in complete.items())
            post = any(ok and months(y)[0] >= first for y, ok in complete.items())
            counts['complete_pre_and_post'] += int(pre and post)
            counts['first_post_complete'] += int(complete[year])
            counts['immediate_pre_and_first_post_complete'] += int(
                complete[year-1] and months(year-1)[-1] < base and complete[year])
            counts['first_two_post_complete'] += int(complete[year] and complete[year+1])
        result[threshold] = counts
    return result


if __name__ == '__main__':
    print(json.dumps(compute()))
