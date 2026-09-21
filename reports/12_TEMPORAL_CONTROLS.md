# Temporal controls

The deterministic month table covers **168 months** from 2013-01-01 through 2026-12-01 and joins one-to-many to every reviewed destination-month row.

It records calendar year, month, quarter, month length, a May–April Magic Pass season label, an analyst-defined November–April winter flag, a May–October summer flag, December/January peak-season flags, and the Gregorian Easter month. The Easter calculation is deterministic and does not claim canton-specific school-holiday coverage.

The `covid_sensitivity_month` flag covers **26 months**, March 2020 through April 2022 inclusive. This is a broad robustness interval required by the project mission, not a legal-restriction chronology and not evidence that destinations faced equal disruption. Models must compare full-sample, exclusion and alternative-period specifications rather than treating the flag as sufficient COVID adjustment.

The source assumptions are versioned in `config/temporal_controls.json`, the reusable table is `data_processed/temporal_controls_month.csv`, and all 168 dates are present in `data_processed/destination_month_panel.csv` for each eligible destination.
