"""Build deterministic month-level calendar and COVID sensitivity controls."""

from __future__ import annotations

import calendar
import json
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "temporal_controls.json"
OUTPUT = ROOT / "data_processed" / "temporal_controls_month.csv"
SUMMARY = ROOT / "reports" / "temporal_controls_summary.json"
REPORT = ROOT / "reports" / "12_TEMPORAL_CONTROLS.md"


def gregorian_easter(year: int) -> date:
    """Anonymous Gregorian algorithm, returning Easter Sunday."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    ell = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * ell) // 451
    month = (h + ell - 7 * m + 114) // 31
    day = ((h + ell - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    dates = pd.date_range(config["panel_start"], config["panel_end"], freq="MS")
    covid_start = pd.Timestamp(config["covid_sensitivity_start"])
    covid_end = pd.Timestamp(config["covid_sensitivity_end"])
    winter = set(config["winter_months"])
    summer = set(config["summer_months"])
    if winter & summer or winter | summer != set(range(1, 13)):
        raise ValueError("Winter and summer month definitions must partition the year")

    rows = []
    for index, timestamp in enumerate(dates):
        pass_start_year = timestamp.year if timestamp.month >= 5 else timestamp.year - 1
        easter = gregorian_easter(timestamp.year)
        covid = covid_start <= timestamp <= covid_end
        rows.append(
            {
                "date": timestamp.date().isoformat(),
                "calendar_year": timestamp.year,
                "calendar_month": timestamp.month,
                "calendar_quarter": timestamp.quarter,
                "calendar_month_index": index,
                "days_in_month": calendar.monthrange(timestamp.year, timestamp.month)[1],
                "magic_pass_season": f"{pass_start_year}/{pass_start_year + 1}",
                "winter_month": timestamp.month in winter,
                "summer_month": timestamp.month in summer,
                "christmas_new_year_peak_month": timestamp.month
                in set(config["christmas_new_year_peak_months"]),
                "easter_month": timestamp.month == easter.month,
                "easter_sunday": easter.isoformat(),
                "covid_sensitivity_month": covid,
                "covid_sensitivity_phase": (
                    "pre_2020_03"
                    if timestamp < covid_start
                    else "sensitivity_2020_03_to_2022_04"
                    if covid
                    else "post_2022_04"
                ),
                "source_id": "DERIVED_TEMPORAL_CONTROLS",
            }
        )
    controls = pd.DataFrame(rows)
    if controls["date"].duplicated().any() or len(controls) != len(dates):
        raise ValueError("Temporal control month grid is not one-to-one")
    if (controls["winter_month"] == controls["summer_month"]).any():
        raise ValueError("Every month must have exactly one winter/summer label")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    controls.to_csv(OUTPUT, index=False)
    summary = {
        "month_rows": int(len(controls)),
        "date_min": controls["date"].min(),
        "date_max": controls["date"].max(),
        "covid_sensitivity_months": int(controls["covid_sensitivity_month"].sum()),
        "easter_month_rows": int(controls["easter_month"].sum()),
        "interpretation": config["covid_interpretation"],
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    REPORT.write_text(
        f"""# Temporal controls

The deterministic month table covers **{summary['month_rows']} months** from {summary['date_min']} through {summary['date_max']} and joins one-to-many to every reviewed destination-month row.

It records calendar year, month, quarter, month length, a May–April Magic Pass season label, an analyst-defined November–April winter flag, a May–October summer flag, December/January peak-season flags, and the Gregorian Easter month. The Easter calculation is deterministic and does not claim canton-specific school-holiday coverage.

The `covid_sensitivity_month` flag covers **{summary['covid_sensitivity_months']} months**, March 2020 through April 2022 inclusive. This is a broad robustness interval required by the project mission, not a legal-restriction chronology and not evidence that destinations faced equal disruption. Models must compare full-sample, exclusion and alternative-period specifications rather than treating the flag as sufficient COVID adjustment.

The source assumptions are versioned in `config/temporal_controls.json`, the reusable table is `data_processed/temporal_controls_month.csv`, and all {summary['month_rows']} dates are present in `data_processed/destination_month_panel.csv` for each eligible destination.
""",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
