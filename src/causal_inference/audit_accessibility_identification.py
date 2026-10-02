"""Audit causal identifiability of the expanded municipality exposure design.

This module does not estimate treatment effects.  It checks whether station-group
entries can be separated at municipality level and defines a narrower candidate
design based on a municipality's first accessible Magic Pass exposure.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
GROUPS_PATH = ROOT / "data_processed" / "accessibility_station_groups.csv"
JOURNEYS_PATH = ROOT / "data_processed" / "accessibility_station_group_journey_context.csv"
PAIR_PATH = ROOT / "data_processed" / "accessibility_station_group_pair_diagnostic.csv"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
FEASIBILITY_PATH = ROOT / "reports" / "accessibility_station_group_feasibility.csv"

PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_identification_pair_audit.csv"
GROUP_OUTPUT = ROOT / "reports" / "accessibility_identification_group_audit.csv"
MUNICIPALITY_OUTPUT = ROOT / "reports" / "accessibility_identification_municipality_audit.csv"
COHORT_OUTPUT = ROOT / "reports" / "accessibility_identification_cohort_audit.csv"
OVERLAP_OUTPUT = ROOT / "reports" / "accessibility_identification_overlap_audit.csv"
FIRST_EXPOSURE_OUTPUT = ROOT / "reports" / "accessibility_first_exposure_audit.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_identification_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "58_AUDIT_IDENTIFICATION_EXPOSITION_COMMUNALE_FR.md"

COVID_START = pd.Timestamp("2020-03-01")
COVID_END = pd.Timestamp("2022-04-01")
THRESHOLDS = (30, 60, 90, 120)


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def month_sequence(anchor: pd.Timestamp, start: int, end: int) -> pd.DatetimeIndex:
    return pd.date_range(
        anchor + pd.DateOffset(months=start),
        anchor + pd.DateOffset(months=end),
        freq="MS",
    )


def covid_month_count(anchor: pd.Timestamp) -> tuple[int, int, int]:
    pre = month_sequence(anchor, -24, -1)
    post = month_sequence(anchor, 0, 23)
    in_covid = lambda dates: int(((dates >= COVID_START) & (dates <= COVID_END)).sum())
    return in_covid(pre), in_covid(post), in_covid(pre.append(post))


def outcome_window_status(
    panel: pd.DataFrame, municipality_id: int, anchor: pd.Timestamp
) -> dict[str, int | bool]:
    dates = month_sequence(anchor, -24, 23)
    rows = panel[
        panel.municipality_bfs_id.eq(municipality_id) & panel.date.isin(dates)
    ]
    pre = rows[rows.date.lt(anchor)]
    post = rows[rows.date.ge(anchor)]
    pre_observed = int(pre.hotel_overnights.notna().sum())
    post_observed = int(post.hotel_overnights.notna().sum())
    return {
        "observed_pre_24_months": pre_observed,
        "observed_post_24_months": post_observed,
        "complete_24_pre_24_post": bool(
            len(rows) == 48 and pre_observed == 24 and post_observed == 24
        ),
    }


def build_pair_audit(
    groups: pd.DataFrame, journeys: pd.DataFrame, pairs: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    qualified = journeys[
        as_bool(journeys.descriptive_accessibility_usable)
        & as_bool(journeys.within_120_minutes)
    ].copy()
    qualified = qualified.merge(
        groups[["station_group_id", "first_effective_month"]],
        on="station_group_id",
        how="left",
        validate="many_to_one",
    )
    same_month = (
        qualified.groupby(["municipality_bfs_id", "first_effective_month"])
        .agg(
            accessible_groups_entering_same_month=("station_group_id", "nunique"),
            accessible_group_names_entering_same_month=(
                "station_group_name",
                lambda values: "|".join(sorted(set(values))),
            ),
        )
        .reset_index()
    )
    audit = pairs.merge(
        same_month,
        on=["municipality_bfs_id", "first_effective_month"],
        how="left",
        validate="many_to_one",
    ).merge(
        groups[
            [
                "station_group_id",
                "scope_status",
                "structural_data_status",
            ]
        ],
        on="station_group_id",
        how="left",
        validate="many_to_one",
    )
    audit["complete_24_pre_24_post"] = as_bool(audit.complete_24_pre_24_post)
    audit["other_entry_within_12_months_120min"] = as_bool(
        audit.other_entry_within_12_months_120min
    )
    audit["entry_window_overlaps_covid_sensitivity"] = as_bool(
        audit.entry_window_overlaps_covid_sensitivity
    )
    audit["same_month_entry_collision"] = audit[
        "accessible_groups_entering_same_month"
    ].gt(1)
    audit["mechanically_isolated_non_covid_window"] = (
        audit.complete_24_pre_24_post
        & ~audit.other_entry_within_12_months_120min
        & ~audit.entry_window_overlaps_covid_sensitivity
    )
    audit["manual_identification_review_priority"] = audit[
        "mechanically_isolated_non_covid_window"
    ]
    audit["causal_pair_approved"] = False

    def reasons(row: pd.Series) -> str:
        values = []
        if not row.complete_24_pre_24_post:
            values.append("incomplete_24_pre_or_post")
        if row.entry_window_overlaps_covid_sensitivity:
            values.append("window_overlaps_covid_sensitivity")
        if row.other_entry_within_12_months_120min:
            values.append("another_accessible_entry_within_12_months")
        if row.same_month_entry_collision:
            values.append("multiple_accessible_groups_enter_same_month")
        values.extend(
            ["historical_access_not_validated", "no_validated_comparison_group"]
        )
        return "|".join(values)

    audit["identification_blocking_reasons"] = audit.apply(reasons, axis=1)
    audit = audit.sort_values(
        ["first_effective_month", "station_group_id", "municipality_bfs_id"],
        kind="stable",
    )
    return audit, qualified


def catchment_overlap(
    groups: pd.DataFrame, qualified: pd.DataFrame, ready_ids: set[str]
) -> tuple[pd.DataFrame, dict[str, tuple[int, ...]], dict[str, list[str]]]:
    catchments = {
        group_id: tuple(sorted(frame.municipality_bfs_id.astype(int).unique()))
        for group_id, frame in qualified[
            qualified.station_group_id.isin(ready_ids)
        ].groupby("station_group_id")
    }
    group_lookup = groups.set_index("station_group_id")
    rows = []
    ready = groups[groups.station_group_id.isin(ready_ids)].sort_values(
        ["first_effective_month", "station_group_id"]
    )
    for anchor, cohort in ready.groupby("first_effective_month"):
        identifiers = cohort.station_group_id.tolist()
        for index, left_id in enumerate(identifiers):
            for right_id in identifiers[index + 1 :]:
                left = set(catchments.get(left_id, ()))
                right = set(catchments.get(right_id, ()))
                union = left | right
                intersection = left & right
                rows.append(
                    {
                        "first_effective_month": anchor,
                        "station_group_id_left": left_id,
                        "station_group_name_left": group_lookup.loc[
                            left_id, "station_group_name"
                        ],
                        "station_group_id_right": right_id,
                        "station_group_name_right": group_lookup.loc[
                            right_id, "station_group_name"
                        ],
                        "left_municipality_count": len(left),
                        "right_municipality_count": len(right),
                        "intersection_municipality_count": len(intersection),
                        "union_municipality_count": len(union),
                        "jaccard_similarity": (
                            len(intersection) / len(union) if union else np.nan
                        ),
                        "exact_same_catchment_and_anchor": bool(left == right),
                        "individual_effects_separable_from_exposure": bool(left != right),
                    }
                )
    overlap = pd.DataFrame(rows).sort_values(
        ["first_effective_month", "jaccard_similarity"],
        ascending=[True, False],
        kind="stable",
    )
    duplicates: dict[tuple[str, tuple[int, ...]], list[str]] = {}
    for group_id in ready_ids:
        key = (
            str(group_lookup.loc[group_id, "first_effective_month"]),
            catchments.get(group_id, ()),
        )
        duplicates.setdefault(key, []).append(group_id)
    exact_groups: dict[str, list[str]] = {}
    for identifiers in duplicates.values():
        if len(identifiers) > 1:
            names = [str(group_lookup.loc[x, "station_group_name"]) for x in identifiers]
            for group_id in identifiers:
                exact_groups[group_id] = sorted(name for name in names if name != group_lookup.loc[group_id, "station_group_name"])
    return overlap, catchments, exact_groups


def two_way_fixed_effect_rank(
    panel: pd.DataFrame,
    groups: pd.DataFrame,
    journeys: pd.DataFrame,
    ready_ids: set[str],
    threshold: int,
) -> dict[str, int | float]:
    usable = journeys[
        as_bool(journeys.descriptive_accessibility_usable)
        & as_bool(journeys[f"within_{threshold}_minutes"])
        & journeys.station_group_id.isin(ready_ids)
    ]
    catchments = {
        group_id: set(frame.municipality_bfs_id.astype(int))
        for group_id, frame in usable.groupby("station_group_id")
    }
    active_ids = sorted(group_id for group_id in ready_ids if catchments.get(group_id))
    observed = panel[panel.hotel_overnights.notna()].reset_index(drop=True)
    municipality = observed.municipality_bfs_id.astype(int).to_numpy()
    dates = observed.date.to_numpy(dtype="datetime64[ns]")
    anchors = pd.to_datetime(
        groups.set_index("station_group_id").first_effective_month
    ).to_dict()
    if not active_ids:
        return {
            "threshold_minutes": threshold,
            "usable_group_municipality_pairs": 0,
            "nonzero_group_columns": 0,
            "two_way_fe_design_rank": 0,
            "rank_deficiency": 0,
            "condition_number_nonzero_space": np.nan,
        }
    matrix = np.column_stack(
        [
            (
                np.isin(municipality, list(catchments[group_id]))
                & (dates >= np.datetime64(anchors[group_id]))
            ).astype(float)
            for group_id in active_ids
        ]
    )
    frame = pd.DataFrame(matrix)
    municipality_means = (
        frame.assign(key=municipality).groupby("key").transform("mean").to_numpy()
    )
    time_means = (
        frame.assign(key=observed.date).groupby("key").transform("mean").to_numpy()
    )
    residual = matrix - municipality_means - time_means + matrix.mean(axis=0)
    singular = np.linalg.svd(residual, compute_uv=False)
    rank = int(np.linalg.matrix_rank(residual))
    condition = float(singular[0] / singular[rank - 1]) if rank else np.nan
    return {
        "threshold_minutes": threshold,
        "usable_group_municipality_pairs": int(len(usable)),
        "nonzero_group_columns": len(active_ids),
        "two_way_fe_design_rank": rank,
        "rank_deficiency": len(active_ids) - rank,
        "condition_number_nonzero_space": condition,
    }


def build_municipality_audit(panel: pd.DataFrame, pair_audit: pd.DataFrame) -> pd.DataFrame:
    base = panel[
        ["municipality_bfs_id", "municipality_name_source", "shared_current_territory"]
    ].drop_duplicates()
    rows = []
    for municipality_id, group in pair_audit.groupby("municipality_bfs_id"):
        complete = group[group.complete_24_pre_24_post]
        priority = group[group.mechanically_isolated_non_covid_window]
        collisions = (
            group.groupby("first_effective_month").station_group_id.nunique()
            if len(group)
            else pd.Series(dtype=int)
        )
        rows.append(
            {
                "municipality_bfs_id": int(municipality_id),
                "accessible_groups_120min": int(group.station_group_id.nunique()),
                "distinct_accessible_entry_months": int(
                    group.first_effective_month.nunique()
                ),
                "complete_24_24_group_pairs": int(len(complete)),
                "complete_24_24_distinct_entry_months": int(
                    complete.first_effective_month.nunique()
                ),
                "mechanically_isolated_non_covid_pairs": int(len(priority)),
                "mechanically_isolated_non_covid_entry_months": int(
                    priority.first_effective_month.nunique()
                ),
                "maximum_groups_entering_same_month": int(collisions.max()),
            }
        )
    metrics = pd.DataFrame(rows)
    result = base.merge(metrics, on="municipality_bfs_id", how="left", validate="one_to_one")
    count_columns = [
        column
        for column in result.columns
        if column not in {"municipality_bfs_id", "municipality_name_source", "shared_current_territory"}
    ]
    result[count_columns] = result[count_columns].fillna(0).astype(int)
    result["multiple_accessible_groups"] = result.accessible_groups_120min.ge(2)
    result["multiple_distinct_entry_months"] = result.distinct_accessible_entry_months.ge(2)
    result["sequential_complete_window_candidate"] = result[
        "complete_24_24_distinct_entry_months"
    ].ge(2)
    result["sequential_non_covid_isolated_candidate"] = result[
        "mechanically_isolated_non_covid_entry_months"
    ].ge(2)
    result["causal_sequence_approved"] = False
    return result.sort_values("municipality_bfs_id", kind="stable")


def build_first_exposure_audit(
    panel: pd.DataFrame, groups: pd.DataFrame, qualified: pd.DataFrame
) -> pd.DataFrame:
    names = panel[
        ["municipality_bfs_id", "municipality_name_source", "shared_current_territory"]
    ].drop_duplicates()
    access = qualified.merge(
        groups[["station_group_id", "station_group_name", "first_effective_month"]]
        .drop_duplicates("station_group_id")
        .rename(columns={"station_group_name": "group_name_registry"}),
        on=["station_group_id", "first_effective_month"],
        how="left",
        validate="many_to_one",
    )
    access["first_effective_month"] = pd.to_datetime(access.first_effective_month)
    first_month = access.groupby("municipality_bfs_id").first_effective_month.min()
    rows = []
    for municipality in names.itertuples(index=False):
        municipality_id = int(municipality.municipality_bfs_id)
        reached = access[access.municipality_bfs_id.eq(municipality_id)]
        if reached.empty:
            rows.append(
                {
                    "municipality_bfs_id": municipality_id,
                    "municipality_name": municipality.municipality_name_source,
                    "shared_current_territory": municipality.shared_current_territory,
                    "ever_accessible_120min": False,
                    "first_exposure_month": "",
                    "groups_entering_at_first_exposure": 0,
                    "first_exposure_group_names": "",
                    "later_entry_months_within_post24": 0,
                    "complete_24_pre_24_post": False,
                    "window_overlaps_covid_sensitivity": False,
                    "first_exposure_candidate_for_manual_design_review": False,
                    "first_exposure_causal_treatment_approved": False,
                }
            )
            continue
        anchor = pd.Timestamp(first_month.loc[municipality_id])
        initial = reached[reached.first_effective_month.eq(anchor)]
        later_post = reached[
            reached.first_effective_month.gt(anchor)
            & reached.first_effective_month.le(anchor + pd.DateOffset(months=23))
        ]
        outcome = outcome_window_status(panel, municipality_id, anchor)
        pre_covid, post_covid, total_covid = covid_month_count(anchor)
        candidate = bool(
            outcome["complete_24_pre_24_post"]
            and total_covid == 0
            and later_post.first_effective_month.nunique() == 0
        )
        rows.append(
            {
                "municipality_bfs_id": municipality_id,
                "municipality_name": municipality.municipality_name_source,
                "shared_current_territory": municipality.shared_current_territory,
                "ever_accessible_120min": True,
                "first_exposure_month": anchor.date().isoformat(),
                "groups_entering_at_first_exposure": int(
                    initial.station_group_id.nunique()
                ),
                "first_exposure_group_names": "|".join(
                    sorted(initial.station_group_name.unique())
                ),
                "nearest_first_exposure_group_minutes": float(
                    initial.mean_one_way_generalized_minutes.min()
                ),
                "later_entry_months_within_post24": int(
                    later_post.first_effective_month.nunique()
                ),
                **outcome,
                "pre_24_covid_months": pre_covid,
                "post_24_covid_months": post_covid,
                "window_overlaps_covid_sensitivity": total_covid > 0,
                "first_exposure_candidate_for_manual_design_review": candidate,
                "first_exposure_causal_treatment_approved": False,
            }
        )
    result = pd.DataFrame(rows)
    result["ever_accessible_120min"] = as_bool(result.ever_accessible_120min)
    return result.sort_values("municipality_bfs_id", kind="stable")


def build_cohort_audit(
    groups: pd.DataFrame,
    group_audit: pd.DataFrame,
    panel: pd.DataFrame,
    first_exposure: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for anchor_text, cohort in groups.groupby("first_effective_month"):
        anchor = pd.Timestamp(anchor_text)
        window_dates = month_sequence(anchor, -24, 23)
        window = panel[panel.date.isin(window_dates)].copy()
        support = window.groupby("municipality_bfs_id").agg(
            rows=("date", "size"),
            observed=("hotel_overnights", lambda values: int(values.notna().sum())),
            new_entries=("new_station_group_entry_count_120min", "sum"),
            active_at_window_end=("active_station_group_count_120min", "last"),
        )
        ever = panel.groupby("municipality_bfs_id").active_station_group_count_120min.max().gt(0)
        support["ever_exposed"] = ever
        complete = support.rows.eq(48) & support.observed.eq(48)
        audit_rows = group_audit[group_audit.first_effective_month.eq(anchor_text)]
        first_rows = first_exposure[
            first_exposure.first_exposure_month.eq(anchor.date().isoformat())
        ]
        pre_covid, post_covid, total_covid = covid_month_count(anchor)
        rows.append(
            {
                "first_effective_month": anchor.date().isoformat(),
                "station_groups_in_cohort": int(len(cohort)),
                "station_groups_with_complete_24_24_pair": int(
                    audit_rows.pairs_complete_24_pre_24_post.gt(0).sum()
                ),
                "station_groups_with_timing_priority_pair": int(
                    audit_rows.mechanically_isolated_non_covid_pairs.gt(0).sum()
                ),
                "complete_group_municipality_pairs": int(
                    audit_rows.pairs_complete_24_pre_24_post.sum()
                ),
                "timing_priority_group_municipality_pairs": int(
                    audit_rows.mechanically_isolated_non_covid_pairs.sum()
                ),
                "municipalities_first_exposed_in_cohort": int(len(first_rows)),
                "first_exposure_complete_24_24_municipalities": int(
                    as_bool(first_rows.complete_24_pre_24_post).sum()
                ) if len(first_rows) else 0,
                "first_exposure_manual_design_candidates": int(
                    as_bool(first_rows.first_exposure_candidate_for_manual_design_review).sum()
                ) if len(first_rows) else 0,
                "pre_24_covid_months": pre_covid,
                "post_24_covid_months": post_covid,
                "complete_outcome_municipalities": int(complete.sum()),
                "complete_not_exposed_during_window": int(
                    (complete & support.new_entries.eq(0)).sum()
                ),
                "complete_never_exposed_municipalities": int(
                    (complete & ~support.ever_exposed).sum()
                ),
                "causal_cohort_approved": False,
                "window_overlaps_covid_sensitivity": total_covid > 0,
            }
        )
    return pd.DataFrame(rows).sort_values("first_effective_month", kind="stable")


def build_group_audit(
    groups: pd.DataFrame,
    feasibility: pd.DataFrame,
    pair_audit: pd.DataFrame,
    catchments: dict[str, tuple[int, ...]],
    exact_groups: dict[str, list[str]],
) -> pd.DataFrame:
    result = groups[
        [
            "station_group_id",
            "station_group_name",
            "first_effective_month",
            "scope_status",
            "structural_data_status",
            "current_access_assumption",
        ]
    ].merge(
        feasibility[
            [
                "station_group_id",
                "municipalities_within_120min",
                "pairs_complete_24_pre_24_post",
                "descriptive_event_window_ready",
            ]
        ],
        on="station_group_id",
        validate="one_to_one",
    )
    pair_metrics = (
        pair_audit.groupby("station_group_id")
        .agg(
            complete_pairs_overlapping_covid=(
                "entry_window_overlaps_covid_sensitivity",
                lambda values: int(
                    (values & pair_audit.loc[values.index, "complete_24_pre_24_post"]).sum()
                ),
            ),
            complete_pairs_with_other_entry_within_12m=(
                "other_entry_within_12_months_120min",
                lambda values: int(
                    (values & pair_audit.loc[values.index, "complete_24_pre_24_post"]).sum()
                ),
            ),
            mechanically_isolated_non_covid_pairs=(
                "mechanically_isolated_non_covid_window",
                "sum",
            ),
        )
        .reset_index()
    )
    result = result.merge(pair_metrics, on="station_group_id", how="left", validate="one_to_one")
    metric_columns = [
        "complete_pairs_overlapping_covid",
        "complete_pairs_with_other_entry_within_12m",
        "mechanically_isolated_non_covid_pairs",
    ]
    result[metric_columns] = result[metric_columns].fillna(0).astype(int)
    result["historical_access_validated"] = False
    result["catchment_signature_sha256"] = result.station_group_id.map(
        lambda group_id: hashlib.sha256(
            "|".join(map(str, catchments.get(group_id, ()))).encode("utf-8")
        ).hexdigest()
    )
    result["exact_same_anchor_catchment_group_names"] = result.station_group_id.map(
        lambda group_id: "|".join(exact_groups.get(group_id, []))
    )
    result["exact_same_anchor_catchment_collision"] = result[
        "exact_same_anchor_catchment_group_names"
    ].ne("")
    result["mechanically_distinct_design_column"] = ~result[
        "exact_same_anchor_catchment_collision"
    ]

    def status(row: pd.Series) -> str:
        if not as_bool(pd.Series([row.descriptive_event_window_ready])).iloc[0]:
            return "insufficient_complete_24_24_window"
        if row.mechanically_isolated_non_covid_pairs > 0:
            return "timing_priority_only_controls_and_historical_access_unvalidated"
        if row.complete_pairs_overlapping_covid >= row.pairs_complete_24_pre_24_post:
            return "complete_window_but_all_pairs_overlap_covid"
        return "complete_window_but_entries_not_separable"

    result["identification_status"] = result.apply(status, axis=1)
    result["manual_identification_review_priority"] = result[
        "mechanically_isolated_non_covid_pairs"
    ].gt(0)
    result["causal_treatment_approved"] = False
    return result.sort_values(
        ["first_effective_month", "station_group_name"], kind="stable"
    )


def main() -> None:
    groups = pd.read_csv(GROUPS_PATH)
    journeys = pd.read_csv(JOURNEYS_PATH)
    pairs = pd.read_csv(PAIR_PATH)
    panel = pd.read_csv(PANEL_PATH)
    feasibility = pd.read_csv(FEASIBILITY_PATH)
    groups["first_effective_month"] = groups.first_effective_month.astype(str)
    panel["date"] = pd.to_datetime(panel.date, errors="raise")
    panel["municipality_bfs_id"] = panel.municipality_bfs_id.astype(int)

    if len(groups) != 71 or len(journeys) != 71 * 186 or len(panel) != 31_248:
        raise ValueError("Unexpected expanded accessibility universe")

    pair_audit, qualified = build_pair_audit(groups, journeys, pairs)
    ready_ids = set(
        feasibility.loc[
            as_bool(feasibility.descriptive_event_window_ready), "station_group_id"
        ]
    )
    overlap, catchments, exact_groups = catchment_overlap(groups, qualified, ready_ids)
    group_audit = build_group_audit(
        groups, feasibility, pair_audit, catchments, exact_groups
    )
    municipality_audit = build_municipality_audit(panel, pair_audit)
    first_exposure = build_first_exposure_audit(panel, groups, qualified)
    cohort_audit = build_cohort_audit(groups, group_audit, panel, first_exposure)
    rank_sensitivity = [
        two_way_fixed_effect_rank(panel, groups, journeys, ready_ids, threshold)
        for threshold in THRESHOLDS
    ]

    priority_pairs = pair_audit[pair_audit.mechanically_isolated_non_covid_window]
    first_candidates = first_exposure[
        as_bool(first_exposure.first_exposure_candidate_for_manual_design_review)
    ]
    founding = cohort_audit[cohort_audit.first_effective_month.eq("2017-11-01")].iloc[0]
    exact_pairs = overlap[overlap.exact_same_catchment_and_anchor]

    if len(pair_audit) != 386:
        raise ValueError("Expected 386 descriptively usable group-municipality pairs")
    if len(ready_ids) != 34:
        raise ValueError("Expected 34 station groups with a complete 24/24 pair")
    if pair_audit.causal_pair_approved.any() or group_audit.causal_treatment_approved.any():
        raise ValueError("Identification audit must not approve causal units")
    if municipality_audit.causal_sequence_approved.any():
        raise ValueError("Municipality sequences must remain causally unapproved")
    if first_exposure.first_exposure_causal_treatment_approved.any():
        raise ValueError("First-exposure candidates must remain causally unapproved")

    for output, frame in [
        (PAIR_OUTPUT, pair_audit),
        (GROUP_OUTPUT, group_audit),
        (MUNICIPALITY_OUTPUT, municipality_audit),
        (COHORT_OUTPUT, cohort_audit),
        (OVERLAP_OUTPUT, overlap),
        (FIRST_EXPOSURE_OUTPUT, first_exposure),
    ]:
        output.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(output, index=False, lineterminator="\n")

    exact_labels = [
        f"{row.station_group_name_left} / {row.station_group_name_right}"
        for row in exact_pairs.itertuples(index=False)
    ]
    summary = {
        "analysis_date": "2026-10-02",
        "descriptive_usable_pairs_within_120min": len(pair_audit),
        "groups_with_complete_24_24_pair": len(ready_ids),
        "complete_24_24_group_municipality_pairs": int(
            pair_audit.complete_24_pre_24_post.sum()
        ),
        "complete_pairs_overlapping_covid": int(
            (
                pair_audit.complete_24_pre_24_post
                & pair_audit.entry_window_overlaps_covid_sensitivity
            ).sum()
        ),
        "mechanically_isolated_non_covid_pairs": len(priority_pairs),
        "groups_with_mechanically_isolated_non_covid_pair": int(
            priority_pairs.station_group_id.nunique()
        ),
        "exact_same_anchor_catchment_pairs": len(exact_pairs),
        "exact_same_anchor_catchment_labels": exact_labels,
        "two_way_fe_rank_sensitivity": rank_sensitivity,
        "municipalities_with_descriptive_120min_access": int(
            municipality_audit.accessible_groups_120min.gt(0).sum()
        ),
        "municipalities_with_multiple_distinct_entry_months": int(
            municipality_audit.multiple_distinct_entry_months.sum()
        ),
        "municipalities_with_two_complete_entry_windows": int(
            municipality_audit.sequential_complete_window_candidate.sum()
        ),
        "municipalities_with_two_non_covid_isolated_entry_windows": int(
            municipality_audit.sequential_non_covid_isolated_candidate.sum()
        ),
        "municipalities_ever_exposed_120min": int(
            as_bool(first_exposure.ever_accessible_120min).sum()
        ),
        "municipalities_never_exposed_120min": int(
            (~as_bool(first_exposure.ever_accessible_120min)).sum()
        ),
        "first_exposure_complete_24_24_municipalities": int(
            as_bool(first_exposure.complete_24_pre_24_post).sum()
        ),
        "first_exposure_manual_design_candidates": len(first_candidates),
        "founding_window_complete_comparison_candidates": int(
            founding.complete_not_exposed_during_window
        ),
        "founding_window_complete_never_exposed_candidates": int(
            founding.complete_never_exposed_municipalities
        ),
        "causal_treatments_approved": 0,
        "causal_controls_approved": 0,
        "recommended_next_design": (
            "screen municipality first exposure to the accessible Magic Pass network; "
            "do not estimate separate station effects where dates or catchments coincide"
        ),
        "input_sha256": {
            str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in [
                GROUPS_PATH,
                JOURNEYS_PATH,
                PAIR_PATH,
                PANEL_PATH,
                FEASIBILITY_PATH,
            ]
        },
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    priority_names = ", ".join(
        sorted(priority_pairs.station_group_name.unique())
    )
    report = f"""# Audit d'identification de l'exposition communale — étape 11

## Conclusion

L'élargissement améliore fortement la couverture descriptive, mais les **34 groupes** ayant au moins une fenêtre 24/24 ne fournissent pas 34 effets de station identifiables. Sur **{int(pair_audit.complete_24_pre_24_post.sum())} couples groupe–commune complets**, **{summary['complete_pairs_overlapping_covid']}** chevauchent la période COVID et seuls **{len(priority_pairs)} couples appartenant à {summary['groups_with_mechanically_isolated_non_covid_pair']} groupes** passent le filtre temporel mécanique : issue 24/24 complète, aucune autre entrée accessible à ±12 mois et aucun mois COVID. Les groupes concernés sont {priority_names}. Ils restent non causaux faute d'accès historique validé et de groupe de comparaison audité.

Toutes les fenêtres complètes des cohortes postérieures à 2017 croisent le COVID. Pour les fondateurs de 2017, le lancement simultané du réseau reste un choc commun même lorsqu'une commune n'a qu'un groupe accessible en 120 minutes.

## Pourquoi les effets par station se confondent

Avec effets fixes commune et mois, les 34 colonnes d'exposition au seuil de 120 minutes n'ont qu'un **rang de {rank_sensitivity[-1]['two_way_fe_design_rank']}**. Trois paires partagent exactement la même date et la même empreinte communale : **{'; '.join(exact_labels)}**. Leurs effets individuels ne peuvent pas être séparés avec cette définition; seul un effet conjoint ou une exposition regroupée serait estimable.

| Seuil | Couples utilisables des 34 groupes | Colonnes non nulles | Rang avec effets fixes commune + mois |
|---:|---:|---:|---:|
{chr(10).join(f"| {row['threshold_minutes']} min | {row['usable_group_municipality_pairs']} | {row['nonzero_group_columns']} | {row['two_way_fe_design_rank']} |" for row in rank_sensitivity)}

## Entrées successives dans une même commune

Parmi les 186 séries, **{summary['municipalities_with_descriptive_120min_access']} communes** ont au moins un groupe descriptivement accessible, **{summary['municipalities_with_multiple_distinct_entry_months']}** connaissent plusieurs mois d'entrée distincts et **{summary['municipalities_with_two_complete_entry_windows']}** disposent d'au moins deux fenêtres 24/24 complètes. Cependant, **{summary['municipalities_with_two_non_covid_isolated_entry_windows']} commune** n'a deux entrées à la fois isolées et hors COVID. Les entrées successives peuvent donc être comparées descriptivement, mais elles ne permettent pas encore d'attribuer causalement chaque variation de nuitées à une station précise.

## Piste recommandée : première exposition au réseau

Une unité plus défendable est la **première exposition d'une commune à au moins un groupe Magic Pass accessible**, en conservant comme intensité le nombre de groupes entrant simultanément. Le seuil 120 minutes donne {summary['municipalities_ever_exposed_120min']} communes exposées et {summary['municipalities_never_exposed_120min']} jamais exposées dans la matrice actuelle. Pour la cohorte fondatrice, **{summary['first_exposure_manual_design_candidates']} communes** ont une issue 24/24 complète, aucune entrée supplémentaire pendant les 24 mois postérieurs et aucun chevauchement COVID. En face, {summary['founding_window_complete_comparison_candidates']} communes complètes ne connaissent aucune entrée accessible pendant la même fenêtre, dont {summary['founding_window_complete_never_exposed_candidates']} ne sont jamais exposées.

Ce comptage justifie un **screening de comparabilité pré-traitement**, pas encore une estimation DiD. Avant toute approbation, il faut vérifier les tendances préalables, l'accessibilité historique des 19 communes traitées prioritaires, les chocs touristiques locaux, les effets de débordement et la cohérence du groupe de comparaison.

## Décision méthodologique

- Ne pas estimer 34 coefficients de station comme s'ils étaient indépendants.
- Conserver les diagnostics par station comme résultats descriptifs.
- Tester ensuite un traitement principal au niveau communal : première exposition au réseau, avec intensité initiale et entrées ultérieures explicites.
- Garder **zéro traitement et zéro contrôle causal approuvés** jusqu'aux audits de comparaison et d'accès historique.

## Fichiers

- `data_processed/accessibility_identification_pair_audit.csv` : blocages par couple groupe–commune;
- `reports/accessibility_identification_group_audit.csv` : statut des 71 groupes;
- `reports/accessibility_identification_municipality_audit.csv` : entrées successives des 186 séries;
- `reports/accessibility_first_exposure_audit.csv` : première exposition et candidats du dessin communal;
- `reports/accessibility_identification_cohort_audit.csv` : diagnostic par cohorte;
- `reports/accessibility_identification_overlap_audit.csv` : chevauchement des empreintes;
- `reports/accessibility_identification_summary.json` : comptes et empreintes des entrées.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
