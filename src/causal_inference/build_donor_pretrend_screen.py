"""Rank provisional donors for manual review without approving causal controls.

The screen uses only information observed in the 36 months before each reviewed
treatment anchor.  It compares hotel-demand level, trend and seasonality,
available-bed scale, current directory structure, and geographic distance.  The
result is a descriptive prioritisation for evidence review, not matching or a
causal design.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "data_processed" / "treatment_control_candidate_matrix.csv"
DESTINATIONS = ROOT / "data_processed" / "destination_month_panel.csv"
HOTEL = ROOT / "data_processed" / "hotel_municipality_month.csv"
CAPACITY = ROOT / "data_processed" / "hotel_capacity_municipality_month.csv"
UNITS = ROOT / "data_processed" / "treatment_destination_units.csv"
CONTINUITY = ROOT / "reports" / "membership_continuity_audit.csv"
POINTS = ROOT / "data_processed" / "resort_point_municipality.csv"
RESORTS = ROOT / "data_processed" / "resort_master.csv"

PAIR_OUT = ROOT / "data_processed" / "donor_pretrend_comparability.csv"
SHORTLIST_OUT = ROOT / "reports" / "donor_pretrend_shortlist.csv"
SUMMARY_OUT = ROOT / "reports" / "donor_pretrend_summary.json"
REPORT_OUT = ROOT / "reports" / "11_DONOR_PRETREND_SCREEN.md"

PRE_MONTHS = 36
MIN_PAIRED_MONTHS = 30
SHORTLIST_SIZE = 5
COVID_SENSITIVITY_START = pd.Timestamp("2020-03-01")
COVID_SENSITIVITY_END = pd.Timestamp("2022-04-01")


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def deseasonalized_trend(log_values: pd.Series, dates: pd.Series) -> float:
    """Return the monthly log trend after calendar-month fixed effects."""
    valid = log_values.notna() & dates.notna()
    if int(valid.sum()) < 24:
        return np.nan
    y = log_values.loc[valid].to_numpy(dtype=float)
    d = pd.to_datetime(dates.loc[valid])
    time = ((d.dt.year - d.dt.year.min()) * 12 + d.dt.month - d.dt.month.min()).to_numpy(
        dtype=float
    )
    month_dummies = pd.get_dummies(d.dt.month, drop_first=True, dtype=float)
    x = np.column_stack([np.ones(len(y)), time, month_dummies.to_numpy()])
    coefficients, *_ = np.linalg.lstsq(x, y, rcond=None)
    return float(coefficients[1])


def seasonal_profile_rmse(
    treated_log: pd.Series, donor_log: pd.Series, months: pd.Series
) -> float:
    frame = pd.DataFrame(
        {"treated": treated_log, "donor": donor_log, "month": months}
    ).dropna()
    profiles = frame.groupby("month", observed=True)[["treated", "donor"]].mean()
    if len(profiles) != 12:
        return np.nan
    profiles = profiles - profiles.mean(axis=0)
    return float(np.sqrt(np.mean((profiles["treated"] - profiles["donor"]) ** 2)))


def standardised_rmse(treated_log: pd.Series, donor_log: pd.Series) -> float:
    valid = treated_log.notna() & donor_log.notna()
    treated = treated_log.loc[valid].to_numpy(dtype=float)
    donor = donor_log.loc[valid].to_numpy(dtype=float)
    if len(treated) < 24 or np.std(treated) == 0 or np.std(donor) == 0:
        return np.nan
    treated = (treated - np.mean(treated)) / np.std(treated)
    donor = (donor - np.mean(donor)) / np.std(donor)
    return float(np.sqrt(np.mean((treated - donor) ** 2)))


def feature_summary(resort_ids: set[str], resorts: pd.DataFrame) -> dict[str, float]:
    rows = resorts[resorts["resort_id"].isin(resort_ids)]
    return {
        "altitude_top_m": float(rows["altitude_top_m"].max()) if rows["altitude_top_m"].notna().any() else np.nan,
        "ski_area_km": float(rows["ski_area_km"].max()) if rows["ski_area_km"].notna().any() else np.nan,
        "number_lifts": float(rows["number_lifts"].max()) if rows["number_lifts"].notna().any() else np.nan,
    }


def main() -> None:
    matrix = pd.read_csv(MATRIX)
    destinations = pd.read_csv(DESTINATIONS)
    hotel = pd.read_csv(HOTEL)
    capacity = pd.read_csv(CAPACITY)
    units = pd.read_csv(UNITS, dtype="string")
    continuity = pd.read_csv(CONTINUITY)
    points = pd.read_csv(POINTS)
    resorts = pd.read_csv(RESORTS)

    for frame in (destinations, hotel, capacity):
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    for column in ("altitude_top_m", "ski_area_km", "number_lifts"):
        resorts[column] = pd.to_numeric(resorts[column], errors="coerce")

    donor_month = hotel.merge(
        capacity[
            [
                "municipality_name_source",
                "date",
                "hotel_beds_available",
                "complete_capacity_supply",
            ]
        ],
        on=["municipality_name_source", "date"],
        how="left",
        validate="one_to_one",
    )

    eligible = units[
        as_bool(units["eligible_for_reviewed_outcome_panel"])
        & as_bool(units["has_24_observed_pre_months"])
        & as_bool(units["has_24_active_post_months_assumption"])
    ].merge(
        continuity.loc[
            as_bool(continuity["continuity_fully_documented"]),
            ["destination_unit_id"],
        ],
        on="destination_unit_id",
        how="inner",
        validate="one_to_one",
    )
    eligible_ids = set(eligible["destination_unit_id"])
    candidates = matrix[
        matrix["destination_unit_id"].isin(eligible_ids)
        & as_bool(matrix["provisional_donor_30km_36pre"])
    ].copy()

    unit_by_id = eligible.set_index("destination_unit_id")
    points["point_municipality_bfs_id"] = pd.to_numeric(
        points["point_municipality_bfs_id"], errors="coerce"
    )
    donor_resorts = {
        int(bfs_id): set(group["resort_id"])
        for bfs_id, group in points.dropna(subset=["point_municipality_bfs_id"]).groupby(
            "point_municipality_bfs_id", observed=True
        )
    }

    rows: list[dict] = []
    for pair in candidates.itertuples(index=False):
        unit = unit_by_id.loc[pair.destination_unit_id]
        anchor = pd.Timestamp(pair.analysis_anchor)
        start = anchor - pd.DateOffset(months=PRE_MONTHS)
        treated = destinations[
            destinations["destination_unit_id"].eq(pair.destination_unit_id)
            & destinations["date"].ge(start)
            & destinations["date"].lt(anchor)
        ][["date", "hotel_overnights", "hotel_beds_available"]]
        donor = donor_month[
            donor_month["municipality_name_source"].eq(pair.donor_municipality_name)
            & donor_month["date"].ge(start)
            & donor_month["date"].lt(anchor)
        ][["date", "hotel_overnights", "hotel_beds_available"]]
        paired = treated.merge(
            donor,
            on="date",
            how="outer",
            suffixes=("_treated", "_donor"),
            validate="one_to_one",
        ).sort_values("date")
        paired_outcome = paired[
            paired["hotel_overnights_treated"].notna()
            & paired["hotel_overnights_donor"].notna()
        ].copy()
        paired_beds = paired[
            paired["hotel_beds_available_treated"].notna()
            & paired["hotel_beds_available_donor"].notna()
        ].copy()

        treated_log = np.log1p(paired_outcome["hotel_overnights_treated"])
        donor_log = np.log1p(paired_outcome["hotel_overnights_donor"])
        correlation = (
            float(treated_log.corr(donor_log))
            if len(paired_outcome) >= 24
            else np.nan
        )
        treated_trend = deseasonalized_trend(treated_log, paired_outcome["date"])
        donor_trend = deseasonalized_trend(donor_log, paired_outcome["date"])

        treated_features = feature_summary(
            set(str(unit["component_resort_ids"]).split("|")), resorts
        )
        donor_features = feature_summary(
            donor_resorts.get(int(pair.donor_municipality_bfs_id), set()), resorts
        )
        covid_months = int(
            (
                paired["date"].ge(COVID_SENSITIVITY_START)
                & paired["date"].le(COVID_SENSITIVITY_END)
            ).sum()
        )
        rows.append(
            {
                "destination_unit_id": pair.destination_unit_id,
                "destination_name": pair.destination_name,
                "analysis_anchor": pair.analysis_anchor,
                "pre_window_start": start.date().isoformat(),
                "pre_window_end": (anchor - pd.DateOffset(months=1)).date().isoformat(),
                "donor_municipality_bfs_id": int(pair.donor_municipality_bfs_id),
                "donor_municipality_name": pair.donor_municipality_name,
                "minimum_resort_point_distance_km": pair.minimum_resort_point_distance_km,
                "paired_pre_outcome_months": len(paired_outcome),
                "paired_pre_capacity_months": len(paired_beds),
                "pre_window_covid_sensitivity_months": covid_months,
                "pre_log_outcome_correlation": correlation,
                "pre_log_outcome_level_gap_abs": (
                    float(abs(treated_log.mean() - donor_log.mean()))
                    if len(paired_outcome)
                    else np.nan
                ),
                "pre_standardised_outcome_rmse": standardised_rmse(
                    treated_log, donor_log
                ),
                "pre_seasonal_profile_rmse": seasonal_profile_rmse(
                    treated_log, donor_log, paired_outcome["date"].dt.month
                ),
                "treated_monthly_log_trend": treated_trend,
                "donor_monthly_log_trend": donor_trend,
                "pre_monthly_log_trend_gap_abs": (
                    abs(treated_trend - donor_trend)
                    if np.isfinite(treated_trend) and np.isfinite(donor_trend)
                    else np.nan
                ),
                "pre_log_bed_capacity_gap_abs": (
                    float(
                        abs(
                            np.log1p(paired_beds["hotel_beds_available_treated"]).mean()
                            - np.log1p(paired_beds["hotel_beds_available_donor"]).mean()
                        )
                    )
                    if len(paired_beds) >= 24
                    else np.nan
                ),
                "top_altitude_gap_m_abs": (
                    abs(treated_features["altitude_top_m"] - donor_features["altitude_top_m"])
                    if np.isfinite(treated_features["altitude_top_m"])
                    and np.isfinite(donor_features["altitude_top_m"])
                    else np.nan
                ),
                "ski_area_log_gap_abs": (
                    abs(
                        np.log1p(treated_features["ski_area_km"])
                        - np.log1p(donor_features["ski_area_km"])
                    )
                    if np.isfinite(treated_features["ski_area_km"])
                    and np.isfinite(donor_features["ski_area_km"])
                    else np.nan
                ),
                "lift_count_log_gap_abs": (
                    abs(
                        np.log1p(treated_features["number_lifts"])
                        - np.log1p(donor_features["number_lifts"])
                    )
                    if np.isfinite(treated_features["number_lifts"])
                    and np.isfinite(donor_features["number_lifts"])
                    else np.nan
                ),
                "historical_membership_screen_status": "provisional_no_resolved_magic_link",
                "spillover_screen_status": "outside_30km_only",
                "manual_donor_review_status": "pending",
                "causal_control_approved": False,
            }
        )

    result = pd.DataFrame(rows)
    ranking_features = [
        "pre_log_outcome_level_gap_abs",
        "pre_standardised_outcome_rmse",
        "pre_seasonal_profile_rmse",
        "pre_monthly_log_trend_gap_abs",
        "pre_log_bed_capacity_gap_abs",
        "minimum_resort_point_distance_km",
        "top_altitude_gap_m_abs",
        "ski_area_log_gap_abs",
        "lift_count_log_gap_abs",
    ]
    ranked_parts: list[pd.DataFrame] = []
    for _, group in result.groupby("destination_unit_id", observed=True):
        group = group.copy()
        percentile_ranks = group[ranking_features].rank(
            method="average", pct=True, ascending=True
        )
        group["comparability_components_available"] = percentile_ranks.notna().sum(axis=1)
        group["descriptive_comparability_score"] = (
            100 * (1 - percentile_ranks.mean(axis=1, skipna=True))
        ).round(2)
        valid = (
            group["paired_pre_outcome_months"].ge(MIN_PAIRED_MONTHS)
            & group["comparability_components_available"].ge(6)
        )
        group["pretrend_screen_usable"] = valid
        group["comparability_rank"] = pd.NA
        group.loc[valid, "comparability_rank"] = (
            group.loc[valid, "descriptive_comparability_score"]
            .rank(method="first", ascending=False)
            .astype(int)
        )
        ranked_parts.append(group)
    result = pd.concat(ranked_parts, ignore_index=True).sort_values(
        ["destination_unit_id", "comparability_rank", "donor_municipality_bfs_id"],
        na_position="last",
    )
    shortlist = result[
        result["pretrend_screen_usable"]
        & pd.to_numeric(result["comparability_rank"], errors="coerce").le(SHORTLIST_SIZE)
    ].copy()

    if len(result) != int(candidates.shape[0]):
        raise ValueError("Donor pretrend output does not preserve every provisional pair")
    if shortlist.groupby("destination_unit_id").size().ne(SHORTLIST_SIZE).any():
        raise ValueError("Expected five shortlisted donors for every screened treatment")
    if result["causal_control_approved"].any():
        raise ValueError("Descriptive donor screen must not approve causal controls")

    PAIR_OUT.parent.mkdir(parents=True, exist_ok=True)
    SHORTLIST_OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(PAIR_OUT, index=False)
    shortlist.to_csv(SHORTLIST_OUT, index=False)

    summary = {
        "treatments_screened": int(result["destination_unit_id"].nunique()),
        "provisional_pairs_screened": int(len(result)),
        "pairs_with_30_of_36_paired_outcome_months": int(
            result["paired_pre_outcome_months"].ge(MIN_PAIRED_MONTHS).sum()
        ),
        "pairs_usable_for_descriptive_ranking": int(result["pretrend_screen_usable"].sum()),
        "shortlisted_pairs_for_manual_review": int(len(shortlist)),
        "treatments_with_pre_window_overlapping_2020_03_to_2022_04": int(
            result.loc[result["pre_window_covid_sensitivity_months"].gt(0), "destination_unit_id"].nunique()
        ),
        "causal_controls_approved": 0,
        "interpretation": (
            "Ranks prioritise manual donor review using pre-anchor outcomes, capacity, current directory "
            "structure and distance. They do not establish historical non-membership, parallel trends, "
            "absence of spillovers, covariate balance or causal validity."
        ),
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    table_rows = []
    for row in shortlist.sort_values(
        ["destination_unit_id", "comparability_rank"]
    ).itertuples(index=False):
        table_rows.append(
            f"| {row.destination_name} | {int(row.comparability_rank)} | "
            f"{row.donor_municipality_name} | {row.descriptive_comparability_score:.2f} | "
            f"{row.minimum_resort_point_distance_km:.1f} | {int(row.paired_pre_outcome_months)} | "
            f"{row.pre_log_outcome_correlation:.3f} | {int(row.pre_window_covid_sensitivity_months)} |"
        )
    report = f"""# Donor pre-trend comparability screen

## Result

The screen ranks {summary['provisional_pairs_screened']} provisional treatment-donor pairs for the seven reviewed units that combine complete annual membership evidence with 24 observed pre and post months. It retains {summary['shortlisted_pairs_for_manual_review']} top-five pairs for manual evidence review. **Zero controls are causally approved.**

The score is an equal-weight average of within-treatment percentile ranks for pre-period hotel-demand level, deseasonalized trend, seasonal profile, standardized outcome shape, available-bed scale, geographic distance, resort-top altitude, ski-area size and lift count. Missing structural fields are skipped, and at least six components plus 30 of the 36 pre-window outcome months are required. Current directory features are descriptive and may not represent historical capacity.

## Shortlist

| Treatment | Rank | Provisional donor municipality | Score | Distance km | Paired pre months | Log-outcome correlation | COVID-sensitivity months in pre-window |
|---|---:|---|---:|---:|---:|---:|---:|
{chr(10).join(table_rows)}

## Interpretation limits

- The input already excludes resolved Magic Pass links, conservative scope relations, the treated outcome scope and resort points within 30 km. The newly resolved Sattel-Hochstuckli link is therefore excluded before ranking.
- A high score is a prioritisation signal, not evidence of parallel trends or a valid untreated counterfactual. The score is relative within each treatment and must not be compared across treatments.
- The 36-month pre-window overlaps the analyst-defined March 2020–April 2022 COVID sensitivity interval for {summary['treatments_with_pre_window_overlapping_2020_03_to_2022_04']} of seven treatments. These cases need full-sample and COVID-exclusion sensitivity specifications.
- Spatial spillovers can extend beyond 30 km; road travel time, shared valleys, marketing networks and accommodation catchments are not yet measured.
- Historical membership for apparent donors, simultaneous investment, accessibility, snowmaking, local economic conditions and competing passes still require explicit review.

The complete pair-level output is `data_processed/donor_pretrend_comparability.csv`; the compact shortlist is `reports/donor_pretrend_shortlist.csv`.
"""
    REPORT_OUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
