from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def read(path: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / path, **kwargs)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().eq("true")


def test_station_groups_cover_every_in_scope_entry_without_using_clusters_as_groups() -> None:
    groups = read("data_processed/accessibility_station_groups.csv", dtype=str)
    events = read("data_processed/accessibility_station_group_events.csv", dtype=str)
    points = read("data_processed/accessibility_station_access_points.csv", dtype=str)
    nodes = read("reports/accessibility_station_access_nodes.csv", dtype=str)
    assert len(groups) == 71
    assert groups.station_group_id.is_unique
    assert len(events) == 78
    assert events.event_id.is_unique
    assert set(events.station_group_id) == set(groups.station_group_id)
    assert len(points) == len(nodes) == 75
    assert points.access_point_id.is_unique
    assert nodes.access_point_id.is_unique
    assert set(points.station_group_id) == set(groups.station_group_id)
    assert (pd.to_numeric(groups.component_listing_count).sum() == 67)
    assert groups.structural_data_status.eq("missing_directory_listing").sum() == 4
    assert groups.structural_data_status.eq("incomplete_unique_listing_aggregation").sum() == 1
    assert not as_bool(groups.causal_treatment_approved).any()
    assert not as_bool(events.causal_treatment_approved).any()
    # The preserved clusters demonstrably span independent station groups.
    cluster_023 = groups.cluster_ids_lineage_only.str.contains("SKI_CLUSTER_023", na=False)
    assert groups.loc[cluster_023, "station_group_id"].nunique() >= 4
    assert groups.loc[cluster_023, "station_group_id"].str.contains(
        "les_paccots|les_pleiades|moleson|rathvel", regex=True).all()


def test_expanded_journeys_preserve_pair_and_sample_grain() -> None:
    pairs = read("data_processed/accessibility_station_group_journey_context.csv")
    summary = json.loads((ROOT / "reports" /
        "accessibility_station_group_journey_summary.json").read_text(encoding="utf-8"))
    assert len(pairs) == 71 * 186
    assert not pairs.duplicated(["station_group_id", "municipality_bfs_id"]).any()
    assert summary["journey_samples"] == 71 * 186 * 24
    assert summary["reference_dates"] == {
        "winter_weekday": "20260204", "winter_saturday": "20260207"}
    for lower, upper in [(30, 60), (60, 90), (90, 120)]:
        assert not (as_bool(pairs[f"within_{lower}_minutes"]) &
                    ~as_bool(pairs[f"within_{upper}_minutes"])).any()
    assert not as_bool(pairs.causal_accessibility_feature_approved).any()


def test_municipality_exposure_keeps_multiple_groups_and_zero_causal_approvals() -> None:
    panel = read("data_processed/accessibility_municipality_month_exposure.csv")
    window = read("data_processed/accessibility_station_group_event_window.csv")
    feasibility = read("reports/accessibility_station_group_feasibility.csv")
    assert len(panel) == 31_248
    assert panel.municipality_bfs_id.nunique() == 186
    assert not panel.duplicated(["municipality_bfs_id", "date"]).any()
    for lower, upper in [(30, 60), (60, 90), (90, 120)]:
        assert (panel[f"active_station_group_count_{lower}min"] <=
                panel[f"active_station_group_count_{upper}min"]).all()
    assert panel.multiple_active_groups_120min.astype(str).str.lower().eq("true").any()
    assert not as_bool(panel.causal_exposure_approved).any()
    assert len(feasibility) == 71
    assert feasibility.station_group_id.is_unique
    assert not as_bool(feasibility.causal_treatment_approved).any()
    assert not as_bool(window.causal_interpretation_approved).any()
    crans = window.station_group_id.eq(
        "MP_GROUP_RESORT__crans_montana_crans_montana")
    after_exit = pd.to_datetime(window.date).ge("2020-05-01")
    assert not as_bool(window.loc[crans & after_exit, "group_assumed_active"]).any()


def test_accessibility_expansion_summaries_and_provenance_are_registered() -> None:
    group_summary = json.loads((ROOT / "reports" /
        "accessibility_station_group_summary.json").read_text(encoding="utf-8"))
    journey_summary = json.loads((ROOT / "reports" /
        "accessibility_station_group_journey_summary.json").read_text(encoding="utf-8"))
    feasibility_summary = json.loads((ROOT / "reports" /
        "accessibility_expansion_feasibility_summary.json").read_text(encoding="utf-8"))
    assert group_summary["station_groups"] == journey_summary["station_groups"] == 71
    assert journey_summary["station_group_municipality_pairs"] == 71 * 186
    assert feasibility_summary["municipality_month_rows"] == 31_248
    assert feasibility_summary["panel_grid_end_month"] == "2026-12-01"
    assert feasibility_summary["hotel_overnights_last_observed_month"] == "2026-03-01"
    assert feasibility_summary["raw_pairs_within_120min"] == 459
    assert feasibility_summary["descriptive_usable_pairs_within_120min"] == 386
    assert feasibility_summary["groups_with_at_least_one_complete_24_pre_24_post_pair"] == 34
    assert feasibility_summary["causal_treatments_approved"] == 0
    sources = read("metadata/data_sources_master.csv", dtype=str)
    dictionary = read("metadata/data_dictionary.csv", dtype=str)
    required_sources = {
        "DERIVED_ACCESSIBILITY_STATION_GROUPS",
        "DERIVED_ACCESSIBILITY_STATION_GROUP_EVENTS",
        "DERIVED_ACCESSIBILITY_STATION_GROUP_JOURNEYS",
        "DERIVED_ACCESSIBILITY_MUNICIPALITY_EXPOSURE",
    }
    assert required_sources <= set(sources.source_id)
    assert set(dictionary.source_id) <= set(sources.source_id)
    for table in [
        "accessibility_station_groups",
        "accessibility_station_group_journey_context",
        "accessibility_municipality_month_exposure",
        "accessibility_station_group_event_window",
        "accessibility_station_group_feasibility",
    ]:
        assert table in set(dictionary.table)
