"""Generate the treatment, panel, causal, and model feasibility gate report."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESORTS = ROOT / "data_processed" / "resort_master.csv"
POINTS = ROOT / "data_processed" / "resort_point_municipality.csv"
HOTEL = ROOT / "data_processed" / "hotel_municipality_month.csv"
HISTORY = ROOT / "data_processed" / "magic_pass_membership_history.csv"
CURRENT = ROOT / "data_processed" / "magic_pass_current_destinations.csv"
CLUSTERS = ROOT / "data_raw" / "stations_ski_clusters_resume_gps_bergfex.csv"
WINDOW_OUTPUT = ROOT / "reports" / "provisional_treatment_window_coverage.csv"
COUNT_OUTPUT = ROOT / "reports" / "feasibility_counts.csv"
REPORT_OUTPUT = ROOT / "reports" / "model_feasibility_report.md"


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def diagnostic_anchor(season: str) -> pd.Timestamp:
    first_year = int(str(season).split("/")[0])
    # The first official pass was winter-only from November 2017.  Later press
    # packs describe annual summer/winter passes; 1 May is used only to count
    # potentially available outcome months, never as an accepted treatment date.
    month = 11 if first_year == 2017 else 5
    return pd.Timestamp(year=first_year, month=month, day=1)


def main() -> None:
    resorts = pd.read_csv(RESORTS, dtype="string")
    points = pd.read_csv(POINTS, dtype="string")
    hotel = pd.read_csv(HOTEL)
    history = pd.read_csv(HISTORY, dtype="string")
    current = pd.read_csv(CURRENT, dtype="string")
    clusters = pd.read_csv(CLUSTERS, sep=";", dtype="string")
    hotel["date"] = pd.to_datetime(hotel["date"], errors="raise")

    observed = hotel[hotel["hotel_overnights"].notna()].copy()
    observed_start = observed["date"].min()
    observed_end = observed["date"].max()
    municipality_months = {
        name: set(group["date"])
        for name, group in observed.groupby("municipality_name_source", observed=True)
    }

    base = history[
        history["event_type"].eq("base_pass_entry")
        & history["candidate_resort_id"].notna()
        & as_bool(history["bfs_hotel_universe"])
    ].copy()
    window_rows: list[dict] = []
    for row in base.itertuples(index=False):
        anchor = diagnostic_anchor(row.entry_season)
        months = municipality_months.get(row.bfs_hotel_municipality_name, set())
        pre = sum(month < anchor for month in months)
        potential_post = sum(month >= anchor for month in months)
        if pd.notna(row.exit_date) and str(row.exit_date).strip():
            exit_month = pd.Timestamp(row.exit_date).to_period("M").to_timestamp()
            active_post = sum(anchor <= month <= exit_month for month in months)
            active_post_status = "bounded_by_documented_exit"
        else:
            active_post = potential_post
            active_post_status = "continuity_not_verified"
        window_rows.append(
            {
                "event_id": row.event_id,
                "candidate_resort_id": row.candidate_resort_id,
                "source_resort_name": row.source_resort_name,
                "cluster_id": row.cluster_id,
                "municipality_bfs_id": row.point_municipality_bfs_id,
                "municipality_name": row.bfs_hotel_municipality_name,
                "entry_season": row.entry_season,
                "diagnostic_anchor": anchor.date().isoformat(),
                "anchor_status": "provisional_for_coverage_count_only",
                "observed_pre_months": pre,
                "observed_post_months_potential": potential_post,
                "observed_post_months_with_known_exit_bound": active_post,
                "post_continuity_status": active_post_status,
                "has_24_months_pre": pre >= 24,
                "has_36_months_pre": pre >= 36,
                "has_24_months_post_potential": active_post >= 24,
                "has_36_months_post_potential": active_post >= 36,
                "treatment_ready": False,
            }
        )
    windows = pd.DataFrame(window_rows)
    WINDOW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    windows.to_csv(WINDOW_OUTPUT, index=False)

    reached_hotel_municipalities = set(
        points.loc[as_bool(points["bfs_hotel_universe"]), "point_municipality_bfs_id"].dropna()
    )
    provisional_treated_municipalities = set(base["point_municipality_bfs_id"].dropna())
    naive_control_upper_bound = len(reached_hotel_municipalities - provisional_treated_municipalities)

    metrics = {
        "resort_listings_total": len(resorts),
        "lift_clusters_total": clusters["cluster_id"].nunique(),
        "lift_clusters_linked_to_resort_listings": resorts["cluster_id"].nunique(),
        "independent_resort_domains_validated": 0,
        "official_current_magic_destinations_snapshot": current["official_destination_id"].nunique(),
        "official_current_destinations_candidate_linked": current["candidate_resort_id"].nunique(),
        "documented_base_entry_events": int(history["event_type"].eq("base_pass_entry").sum()),
        "candidate_linked_base_entry_events": int(
            (history["event_type"].eq("base_pass_entry") & history["candidate_resort_id"].notna()).sum()
        ),
        "candidate_linked_base_entries_with_hotel_outcome": len(base),
        "provisional_treated_clusters_with_hotel_outcome": base["cluster_id"].nunique(),
        "provisional_treated_municipalities_with_hotel_outcome": base[
            "point_municipality_bfs_id"
        ].nunique(),
        "treated_with_exact_entry_date": 0,
        "treated_with_season_only_and_24_months_pre": int(windows["has_24_months_pre"].sum()),
        "treated_with_season_only_and_36_months_pre": int(windows["has_36_months_pre"].sum()),
        "treated_with_season_only_and_24_months_post_potential": int(
            windows["has_24_months_post_potential"].sum()
        ),
        "treated_with_season_only_and_36_months_post_potential": int(
            windows["has_36_months_post_potential"].sum()
        ),
        "unique_provisional_treatment_anchors": windows["diagnostic_anchor"].nunique(),
        "hotel_municipalities_total": hotel["municipality_name_source"].nunique(),
        "hotel_municipalities_reached_by_resort_point": len(reached_hotel_municipalities),
        "naive_non_treated_control_municipalities_upper_bound": naive_control_upper_bound,
        "approved_usable_controls": 0,
        "hotel_observed_start": observed_start.date().isoformat(),
        "hotel_observed_end": observed_end.date().isoformat(),
        "hotel_observed_month_rows": int(observed["hotel_overnights"].notna().sum()),
        "causal_treatment_units_approved": 0,
    }
    pd.DataFrame([{"metric": key, "value": value} for key, value in metrics.items()]).to_csv(
        COUNT_OUTPUT, index=False
    )

    model_rows = [
        ("Municipality fixed-effects panel", "Not ready", "Outcome panel is large enough, but exposure and treatment coding are not validated."),
        ("Staggered Difference-in-Differences", "Not credible yet", "Only season-level entry timing is available; exits, scope, spillovers, and controls remain incomplete."),
        ("Matching", "Descriptive only", "May help select analogues after pre-treatment covariates and membership status are completed; it is not yet causal."),
        ("Synthetic control / synthetic DiD", "Case-study candidate", "Could be assessed for a few clearly mapped municipalities with uncontaminated donors; no donor pool is approved yet."),
        ("Causal forest", "Not supported", "At most 14 provisional treated municipalities is far below a defensible heterogeneous-effect sample."),
        ("X-Learner", "Not supported", "The effective treated-unit count is too small and treatment labels are not final."),
        ("DR-Learner", "Not supported", "The effective treated-unit count is too small and nuisance models would be unstable."),
        ("Gradient boosting", "Deferred", "Potentially useful for ordinary prediction after features exist, but not evidence of membership uplift."),
        ("Random forest", "Deferred", "Potentially useful as a grouped predictive benchmark; current independent destination sample is unresolved."),
        ("Neural network", "Rejected", "Monthly rows do not create independent resorts; the effective cross-sectional sample is far too small."),
    ]
    model_table = "\n".join(
        f"| {name} | {verdict} | {reason} |" for name, verdict, reason in model_rows
    )
    report = f"""# Model feasibility report

Generated reproducibly by `src/data_processing/build_feasibility_report.py`.

## Executive verdict

The project currently follows **Path C (weak treatment sample / exploratory decision support)**. This is a checkpoint decision, not a permanent rejection of causal work. A move to Path B would require a reviewed destination-level resort definition, complete season-by-season membership and exit histories, an explicit resort-to-tourism-municipality exposure crosswalk, and an uncontaminated control audit.

No causal model, treatment-effect learner, opportunity score, or neural network should be fitted at this checkpoint.

## Effective sample

- The supplied Bergfex layer contains **{metrics['resort_listings_total']} resort listings**. The preserved lift layer has **{metrics['lift_clusters_total']} clusters**, of which **{metrics['lift_clusters_linked_to_resort_listings']}** are linked to at least one listing. Neither number is yet an approved count of independent ski destinations.
- The official current-map snapshot contains **{metrics['official_current_magic_destinations_snapshot']} embedded destinations**; **{metrics['official_current_destinations_candidate_linked']}** have a candidate link to a supplied resort listing. The page headline and press archive refer to more than 100 destinations, so the embedded-list discrepancy must be reviewed rather than silently reconciled.
- Official evidence records **{metrics['documented_base_entry_events']} base-pass entry events**. **{metrics['candidate_linked_base_entry_events']}** have a candidate resort-listing link, but only **{metrics['candidate_linked_base_entries_with_hotel_outcome']}** also point to an OFS hotel municipality.
- Those {metrics['candidate_linked_base_entries_with_hotel_outcome']} events reduce to **{metrics['provisional_treated_municipalities_with_hotel_outcome']} municipalities**. This municipality count, not the {metrics['hotel_observed_month_rows']:,} observed monthly rows, is the more relevant upper bound for treatment heterogeneity.
- **Zero** treatment units are approved for causal estimation because point containment is not tourism exposure and membership continuity is incomplete.

## Outcome coverage

- The cleaned OFS-derived panel has **{metrics['hotel_municipalities_total']} municipalities**.
- Observed hotel-night values run from **{metrics['hotel_observed_start']}** through **{metrics['hotel_observed_end']}**; later 2026 grid rows are missing and are not counted as observed.
- Resort points reach **{metrics['hotel_municipalities_reached_by_resort_point']}** hotel municipalities.
- A naive subtraction leaves at most **{metrics['naive_non_treated_control_municipalities_upper_bound']}** apparent control municipalities, but **zero controls are approved** because historical non-membership and spillover contamination have not been verified.

## Provisional pre/post windows

For coverage diagnostics only, the script anchors the founding 2017/18 season at 2017-11-01 and later annual seasons at 1 May of their first year. These are not accepted treatment dates. A documented exit bounds Crans-Montana's active post period; continuity for all other events remains unverified.

- Season-only candidate events with at least 24 observed pre months: **{metrics['treated_with_season_only_and_24_months_pre']}**
- With at least 36 observed pre months: **{metrics['treated_with_season_only_and_36_months_pre']}**
- With at least 24 potentially post-entry months: **{metrics['treated_with_season_only_and_24_months_post_potential']}**
- With at least 36 potentially post-entry months: **{metrics['treated_with_season_only_and_36_months_post_potential']}**
- Distinct provisional anchors: **{metrics['unique_provisional_treatment_anchors']}**
- Treated units with an exact entry date: **0**

The event-level audit is in `reports/provisional_treatment_window_coverage.csv`.

## Model-family decisions

| Model family | Current decision | Evidence-based reason |
|---|---|---|
{model_table}

## Main identification risks

1. Selection into Magic Pass and pre-existing trends are unmeasured.
2. Resort listings, lift clusters, official pass destinations, and tourism municipalities are different units.
3. Several resorts share the same municipality; some destinations span several municipalities.
4. Crans-Montana proves that treatment is not universally absorbing.
5. COVID overlaps the post-period of early entrants and the entry period of later ones.
6. Spillovers may contaminate nearby nominal controls.
7. Hotel capacity, snow, accessibility, investment, and local economic controls have not yet been integrated.

## Next evidence gate

Prioritise manual review of the 18 candidate entry/outcome links, starting with shared municipalities (Anniviers, Evolène, and Reichenbach im Kandertal), complete annual membership/exit status, and define explicit destination-to-municipality weights. Only then reassess fixed-effects/event-study feasibility and donor contamination. Complex heterogeneous-effect ML remains unjustified unless the effective treated-destination count increases substantially.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
