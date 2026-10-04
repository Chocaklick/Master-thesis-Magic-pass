"""Inventory every accessibility-exposure cohort without selecting an analysis sample."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_all_cohort_coverage.json"
PANEL_PATH = ROOT / "data_processed" / "accessibility_municipality_month_exposure.csv"
EVENT_PATH = ROOT / "data_processed" / "accessibility_station_group_events.csv"
GROUP_PATH = ROOT / "data_processed" / "accessibility_station_groups.csv"
JOURNEY_PATH = ROOT / "data_processed" / "accessibility_station_group_journey_context.csv"
TEMPORAL_PATH = ROOT / "data_processed" / "temporal_controls_month.csv"
HISTORICAL_2018_PATH = (
    ROOT / "reports" / "accessibility_historical_gtfs_2018_current_transfer_municipality_validation.csv"
)
STAGE24_CANDIDATE_PATH = ROOT / "reports" / "accessibility_estimation_candidate_pairs.csv"

MUNICIPALITY_OUTPUT = ROOT / "reports" / "accessibility_all_cohort_municipality_coverage.csv"
COHORT_OUTPUT = ROOT / "reports" / "accessibility_all_cohort_coverage_by_cohort.csv"
GROUP_OUTPUT = ROOT / "reports" / "accessibility_all_cohort_station_group_coverage.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_all_cohort_coverage_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "73_COUVERTURE_TOUTES_COHORTES_FR.md"

SOURCE_ID = "DERIVED_ACCESSIBILITY_ALL_COHORT_COVERAGE"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def pipe(values) -> str:
    return "|".join(str(value) for value in values)


def build_group_anchors(events: pd.DataFrame, groups: pd.DataFrame) -> pd.DataFrame:
    anchors = events.groupby("station_group_id", as_index=False).agg(
        first_effective_month=("effective_month", "min"),
        first_entry_season=("entry_season", "min"),
        source_event_count=("event_id", "nunique"),
    )
    anchors = anchors.merge(
        groups[["station_group_id", "station_group_name"]],
        on="station_group_id",
        validate="one_to_one",
    )
    anchors["first_effective_month"] = pd.to_datetime(anchors.first_effective_month)
    anchors["group_entry_calendar_year"] = anchors.first_effective_month.dt.year
    return anchors.sort_values(["first_effective_month", "station_group_id"], kind="stable")


def historical_status(
    threshold: int,
    first_exposure: pd.Timestamp,
    municipality_id: int,
    historical_lookup: pd.DataFrame,
) -> tuple[str, bool]:
    if threshold != 120:
        return "targeted_2018_validation_defined_only_for_120min", False
    if first_exposure != pd.Timestamp("2017-11-01"):
        return "no_anchor_year_historical_timetable_validation_for_later_cohort", False
    if municipality_id not in historical_lookup.index:
        return "2017_cohort_not_in_targeted_2018_priority_worklist", False
    retained = bool(historical_lookup.loc[municipality_id, "historical_first_exposure_retained"])
    status = str(
        historical_lookup.loc[
            municipality_id, "historical_first_exposure_design_review_status"
        ]
    )
    return f"targeted_2018_current_transfer_sensitivity__{status}", retained


def horizon_metrics(
    local_panel: pd.DataFrame,
    first_exposure: pd.Timestamp,
    horizon: int,
    global_outcome_start: pd.Timestamp,
    global_outcome_end: pd.Timestamp,
    covid_months: set[pd.Timestamp],
    accessible_links: pd.DataFrame,
) -> dict:
    pre_dates = pd.date_range(
        first_exposure - pd.DateOffset(months=horizon), periods=horizon, freq="MS"
    )
    post_dates = pd.date_range(first_exposure, periods=horizon, freq="MS")
    outcome = local_panel.set_index("date").hotel_overnights

    def metrics_for_dates(dates: pd.DatetimeIndex, phase: str) -> dict:
        within_source = (dates >= global_outcome_start) & (dates <= global_outcome_end)
        values = outcome.reindex(dates)
        observed = values.notna()
        return {
            f"observed_{phase}_{horizon}_months": int(observed.sum()),
            f"calendar_available_{phase}_{horizon}_months": int(within_source.sum()),
            f"missing_outcome_{phase}_{horizon}_months_within_source_coverage": int(
                (within_source & ~observed.to_numpy()).sum()
            ),
            f"short_{phase}_{horizon}_window_due_panel_bounds": bool(
                within_source.sum() < horizon
            ),
            f"covid_sensitivity_{phase}_{horizon}_months": int(
                sum(date in covid_months for date in dates)
            ),
        }

    result = {
        **metrics_for_dates(pre_dates, "pre"),
        **metrics_for_dates(post_dates, "post"),
    }
    result[f"complete_observed_{horizon}_pre_{horizon}_post"] = bool(
        result[f"observed_pre_{horizon}_months"] == horizon
        and result[f"observed_post_{horizon}_months"] == horizon
    )
    result[f"window_{horizon}_overlaps_existing_covid_sensitivity"] = bool(
        result[f"covid_sensitivity_pre_{horizon}_months"]
        + result[f"covid_sensitivity_post_{horizon}_months"]
        > 0
    )
    post_end = post_dates[-1]
    later = accessible_links[
        accessible_links.first_effective_month.gt(first_exposure)
        & accessible_links.first_effective_month.le(post_end)
    ]
    result[f"later_entry_group_count_within_post_{horizon}"] = int(
        later.station_group_id.nunique()
    )
    result[f"later_entry_month_count_within_post_{horizon}"] = int(
        later.first_effective_month.nunique()
    )
    return result


def build_municipality_inventory(
    panel: pd.DataFrame,
    journeys: pd.DataFrame,
    anchors: pd.DataFrame,
    temporal: pd.DataFrame,
    historical: pd.DataFrame,
    thresholds: list[int],
    horizons: list[int],
) -> pd.DataFrame:
    observed_dates = panel.loc[panel.hotel_overnights.notna(), "date"]
    global_outcome_start = pd.Timestamp(observed_dates.min())
    global_outcome_end = pd.Timestamp(observed_dates.max())
    covid_months = set(
        temporal.loc[as_bool(temporal.covid_sensitivity_month), "date"].tolist()
    )
    historical = historical.copy()
    historical["historical_first_exposure_retained"] = as_bool(
        historical.historical_first_exposure_retained
    )
    historical_lookup = historical.set_index("municipality_bfs_id")

    pairs = journeys.merge(
        anchors,
        on=["station_group_id", "station_group_name"],
        validate="many_to_one",
    )
    pairs["descriptive_accessibility_usable"] = as_bool(
        pairs.descriptive_accessibility_usable
    )
    panel_names = (
        panel[["municipality_bfs_id", "municipality_name_source"]]
        .drop_duplicates("municipality_bfs_id")
        .set_index("municipality_bfs_id")
        .municipality_name_source
    )
    rows: list[dict] = []
    for threshold in thresholds:
        within_column = f"within_{threshold}_minutes"
        pairs[within_column] = as_bool(pairs[within_column])
        eligible = pairs[
            pairs.descriptive_accessibility_usable & pairs[within_column]
        ].copy()
        for municipality_id, links in eligible.groupby("municipality_bfs_id", sort=True):
            municipality_id = int(municipality_id)
            links = links.sort_values(
                ["first_effective_month", "station_group_id"], kind="stable"
            )
            first_exposure = pd.Timestamp(links.first_effective_month.min())
            first_links = links[links.first_effective_month.eq(first_exposure)]
            later_links = links[links.first_effective_month.gt(first_exposure)]
            local_panel = panel[panel.municipality_bfs_id.eq(municipality_id)].copy()
            expected_panel_first = local_panel.loc[
                local_panel[f"active_station_group_count_{threshold}min"].gt(0), "date"
            ].min()
            if pd.Timestamp(expected_panel_first) != first_exposure:
                raise ValueError(
                    f"First-exposure mismatch for threshold {threshold}, BFS {municipality_id}"
                )
            access_status, targeted_retained = historical_status(
                threshold, first_exposure, municipality_id, historical_lookup
            )
            temporal_match = temporal[temporal.date.eq(first_exposure)]
            if len(temporal_match) != 1:
                raise ValueError(f"Missing temporal control for {first_exposure}")
            row = {
                "accessibility_threshold_minutes": threshold,
                "municipality_bfs_id": municipality_id,
                "municipality_name": str(panel_names.loc[municipality_id]),
                "first_exposure_month": first_exposure.date().isoformat(),
                "first_exposure_calendar_year": int(first_exposure.year),
                "first_exposure_magic_pass_season": str(
                    temporal_match.magic_pass_season.iloc[0]
                ),
                "first_exposure_group_count": int(first_links.station_group_id.nunique()),
                "first_exposure_group_ids": pipe(first_links.station_group_id.tolist()),
                "first_exposure_group_names": pipe(first_links.station_group_name.tolist()),
                "accessible_group_count_all_cohorts": int(links.station_group_id.nunique()),
                "later_accessible_group_count": int(later_links.station_group_id.nunique()),
                "later_entry_month_count": int(later_links.first_effective_month.nunique()),
                "later_entry_months": pipe(
                    sorted(date.date().isoformat() for date in later_links.first_effective_month.unique())
                ),
                "multiple_groups_at_first_exposure": bool(
                    first_links.station_group_id.nunique() > 1
                ),
                "any_later_accessible_group_entry": bool(len(later_links)),
                "nearest_first_exposure_group_minutes": float(
                    first_links.mean_one_way_generalized_minutes.min()
                ),
                "shared_current_territory": bool(
                    as_bool(local_panel.shared_current_territory).iloc[0]
                ),
                "historical_access_validation_status": access_status,
                "targeted_2018_sensitivity_retained_first_exposure": targeted_retained,
                "current_access_fixed": True,
                "analysis_sample_selected": False,
                "causal_treatment_approved": False,
                "source_id": SOURCE_ID,
            }
            for horizon in horizons:
                row.update(
                    horizon_metrics(
                        local_panel,
                        first_exposure,
                        horizon,
                        global_outcome_start,
                        global_outcome_end,
                        covid_months,
                        links,
                    )
                )
            rows.append(row)
    result = pd.DataFrame(rows).sort_values(
        ["accessibility_threshold_minutes", "first_exposure_month", "municipality_bfs_id"],
        kind="stable",
    )
    return result


def build_cohort_summary(
    municipalities: pd.DataFrame,
    anchors: pd.DataFrame,
    horizons: list[int],
) -> pd.DataFrame:
    rows = []
    for (threshold, month), cohort in municipalities.groupby(
        ["accessibility_threshold_minutes", "first_exposure_month"], sort=True
    ):
        month_timestamp = pd.Timestamp(month)
        row = {
            "accessibility_threshold_minutes": int(threshold),
            "first_exposure_month": month,
            "first_exposure_calendar_year": int(month_timestamp.year),
            "first_exposure_magic_pass_season": cohort.first_exposure_magic_pass_season.iloc[0],
            "station_groups_entering_network_this_month": int(
                anchors.first_effective_month.eq(month_timestamp).sum()
            ),
            "station_groups_causing_first_municipal_exposure": len({
                value
                for text in cohort.first_exposure_group_ids
                for value in str(text).split("|")
                if value
            }),
            "municipalities_first_exposed": int(len(cohort)),
            "municipalities_with_multiple_groups_at_first_exposure": int(
                cohort.multiple_groups_at_first_exposure.sum()
            ),
            "municipalities_with_any_later_entry": int(
                cohort.any_later_accessible_group_entry.sum()
            ),
            "municipalities_in_shared_current_territory": int(
                cohort.shared_current_territory.sum()
            ),
            "municipalities_with_targeted_2018_retention": int(
                cohort.targeted_2018_sensitivity_retained_first_exposure.sum()
            ),
            "analysis_sample_selected": False,
            "causal_treatment_approved": False,
            "source_id": SOURCE_ID,
        }
        for horizon in horizons:
            row[f"municipalities_complete_{horizon}_pre_{horizon}_post"] = int(
                cohort[f"complete_observed_{horizon}_pre_{horizon}_post"].sum()
            )
            row[f"municipalities_short_post_{horizon}_due_panel_end"] = int(
                cohort[f"short_post_{horizon}_window_due_panel_bounds"].sum()
            )
            row[f"municipalities_with_missing_outcome_in_{horizon}_window"] = int((
                cohort[f"missing_outcome_pre_{horizon}_months_within_source_coverage"]
                + cohort[f"missing_outcome_post_{horizon}_months_within_source_coverage"]
            ).gt(0).sum())
            row[f"municipalities_overlapping_existing_covid_sensitivity_{horizon}"] = int(
                cohort[f"window_{horizon}_overlaps_existing_covid_sensitivity"].sum()
            )
            row[f"municipalities_with_later_entry_in_post_{horizon}"] = int(
                cohort[f"later_entry_group_count_within_post_{horizon}"].gt(0).sum()
            )
        rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["accessibility_threshold_minutes", "first_exposure_month"], kind="stable"
    )


def build_group_summary(
    municipalities: pd.DataFrame,
    anchors: pd.DataFrame,
    thresholds: list[int],
    horizons: list[int],
) -> pd.DataFrame:
    rows = []
    for threshold in thresholds:
        local = municipalities[
            municipalities.accessibility_threshold_minutes.eq(threshold)
        ]
        for group in anchors.itertuples(index=False):
            first_mask = local.first_exposure_group_ids.map(
                lambda text: group.station_group_id in str(text).split("|")
            )
            first_municipalities = local[first_mask]
            row = {
                "accessibility_threshold_minutes": threshold,
                "station_group_id": group.station_group_id,
                "station_group_name": group.station_group_name,
                "group_first_effective_month": group.first_effective_month.date().isoformat(),
                "group_entry_calendar_year": int(group.group_entry_calendar_year),
                "group_first_entry_season": group.first_entry_season,
                "source_event_count": int(group.source_event_count),
                "municipalities_for_which_group_causes_first_exposure": int(
                    len(first_municipalities)
                ),
                "analysis_sample_selected": False,
                "causal_treatment_approved": False,
                "source_id": SOURCE_ID,
            }
            for horizon in horizons:
                complete = first_municipalities[
                    f"complete_observed_{horizon}_pre_{horizon}_post"
                ]
                row[f"first_exposure_municipalities_complete_{horizon}_pre_{horizon}_post"] = int(
                    complete.sum()
                )
                row[f"has_complete_first_exposure_municipality_{horizon}_pre_{horizon}_post"] = bool(
                    complete.any()
                )
            rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["accessibility_threshold_minutes", "group_first_effective_month", "station_group_id"],
        kind="stable",
    )


def build_summary(
    config: dict,
    panel: pd.DataFrame,
    municipalities: pd.DataFrame,
    cohorts: pd.DataFrame,
    groups: pd.DataFrame,
    stage24_primary_treated_ids: set[int],
) -> dict:
    overview = {}
    for threshold in config["accessibility_thresholds_minutes"]:
        local = municipalities[
            municipalities.accessibility_threshold_minutes.eq(threshold)
        ]
        group_local = groups[groups.accessibility_threshold_minutes.eq(threshold)]
        stage24_local = local[
            local.municipality_bfs_id.astype(int).isin(stage24_primary_treated_ids)
        ]
        stage24_first_groups = {
            value
            for text in stage24_local.first_exposure_group_ids
            for value in str(text).split("|")
            if value
        }
        overview[str(threshold)] = {
            "municipalities_ever_exposed": int(len(local)),
            "first_exposure_cohorts": int(local.first_exposure_month.nunique()),
            "first_exposure_calendar_years": sorted(
                local.first_exposure_calendar_year.astype(int).unique().tolist()
            ),
            "municipalities_with_multiple_groups_at_first_exposure": int(
                local.multiple_groups_at_first_exposure.sum()
            ),
            "municipalities_with_any_later_entry": int(
                local.any_later_accessible_group_entry.sum()
            ),
            "mechanical_coverage_by_horizon": {
                str(horizon): {
                    "municipalities_complete_pre_and_post": int(
                        local[f"complete_observed_{horizon}_pre_{horizon}_post"].sum()
                    ),
                    "first_exposure_groups_with_at_least_one_complete_municipality": int(
                        group_local[
                            f"has_complete_first_exposure_municipality_{horizon}_pre_{horizon}_post"
                        ].sum()
                    ),
                    "mechanically_additional_complete_municipalities_vs_stage24_primary": int(
                        local[
                            local[f"complete_observed_{horizon}_pre_{horizon}_post"]
                            & ~local.municipality_bfs_id.astype(int).isin(
                                stage24_primary_treated_ids
                            )
                        ].municipality_bfs_id.nunique()
                    ),
                    "mechanically_additional_first_exposure_groups_vs_stage24_primary": int(
                        len({
                            value
                            for text in local.loc[
                                local[f"complete_observed_{horizon}_pre_{horizon}_post"],
                                "first_exposure_group_ids",
                            ]
                            for value in str(text).split("|")
                            if value
                        } - stage24_first_groups)
                    ),
                    "municipalities_overlapping_existing_covid_sensitivity": int(
                        local[
                            f"window_{horizon}_overlaps_existing_covid_sensitivity"
                        ].sum()
                    ),
                    "municipalities_with_later_entry_in_post_window": int(
                        local[
                            f"later_entry_group_count_within_post_{horizon}"
                        ].gt(0).sum()
                    ),
                    "municipalities_with_short_post_window_due_panel_end": int(
                        local[f"short_post_{horizon}_window_due_panel_bounds"].sum()
                    ),
                }
                for horizon in config["symmetric_pre_post_horizons_months"]
            },
        }
    return {
        "specification_version": config["specification_version"],
        "panel_municipalities": int(panel.municipality_bfs_id.nunique()),
        "panel_months": int(panel.date.nunique()),
        "panel_rows": int(len(panel)),
        "station_groups": 71,
        "stage24_primary_treated_municipalities": len(stage24_primary_treated_ids),
        "stage24_primary_first_exposure_groups_at_120min": int(len({
            value
            for text in municipalities.loc[
                municipalities.accessibility_threshold_minutes.eq(120)
                & municipalities.municipality_bfs_id.astype(int).isin(
                    stage24_primary_treated_ids
                ),
                "first_exposure_group_ids",
            ]
            for value in str(text).split("|")
            if value
        })),
        "accessibility_thresholds_minutes": config["accessibility_thresholds_minutes"],
        "horizons_months": config["symmetric_pre_post_horizons_months"],
        "threshold_overview": overview,
        "cohort_summary_rows": int(len(cohorts)),
        "municipality_coverage_rows": int(len(municipalities)),
        "station_group_coverage_rows": int(len(groups)),
        "analysis_sample_selected": False,
        "causal_treatment_approved": False,
        "causal_estimation_approved": False,
        "input_sha256": {
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            PANEL_PATH.relative_to(ROOT).as_posix(): sha256(PANEL_PATH),
            EVENT_PATH.relative_to(ROOT).as_posix(): sha256(EVENT_PATH),
            GROUP_PATH.relative_to(ROOT).as_posix(): sha256(GROUP_PATH),
            JOURNEY_PATH.relative_to(ROOT).as_posix(): sha256(JOURNEY_PATH),
            TEMPORAL_PATH.relative_to(ROOT).as_posix(): sha256(TEMPORAL_PATH),
            HISTORICAL_2018_PATH.relative_to(ROOT).as_posix(): sha256(HISTORICAL_2018_PATH),
            STAGE24_CANDIDATE_PATH.relative_to(ROOT).as_posix(): sha256(STAGE24_CANDIDATE_PATH),
        },
        "source_id": SOURCE_ID,
        "interpretation": (
            "Mechanical coverage inventory only. Complete outcome windows, COVID overlap and "
            "accessible entry timing are reported without selecting an estimation sample."
        ),
    }


def write_report(summary: dict, cohorts: pd.DataFrame) -> None:
    main = summary["threshold_overview"]["120"]
    lines = [
        "# Couverture de toutes les cohortes - étape 26",
        "",
        "**Statut : inventaire exhaustif; aucune commune ni cohorte sélectionnée ou exclue.**",
        "",
        "## Résultat principal",
        "",
        "Le seuil de 120 minutes déjà utilisé relie **80 communes** à au moins une entrée Magic Pass. "
        "Le tableau ci-dessous ne déclare pas ces communes causalement utilisables : il indique seulement "
        "combien disposent mécaniquement de nuitées observées avant et après leur première exposition.",
        "",
        "| Horizon symétrique | Communes avec fenêtre complète | Communes en plus des 6 du pilote | Groupes représentés | Groupes en plus des 6 du pilote | Chevauchement COVID | Entrée ultérieure | Post trop court |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for horizon in summary["horizons_months"]:
        item = main["mechanical_coverage_by_horizon"][str(horizon)]
        lines.append(
            f"| {horizon}+{horizon} mois | {item['municipalities_complete_pre_and_post']} | "
            f"{item['mechanically_additional_complete_municipalities_vs_stage24_primary']} | "
            f"{item['first_exposure_groups_with_at_least_one_complete_municipality']} | "
            f"{item['mechanically_additional_first_exposure_groups_vs_stage24_primary']} | "
            f"{item['municipalities_overlapping_existing_covid_sensitivity']} | "
            f"{item['municipalities_with_later_entry_in_post_window']} | "
            f"{item['municipalities_with_short_post_window_due_panel_end']} |"
        )
    lines += [
        "",
        "## Couverture par seuil d'accès",
        "",
        "| Seuil | Communes exposées au moins une fois | Cohortes de première exposition | Entrées multiples dès le premier mois | Au moins une entrée ultérieure |",
        "|---:|---:|---:|---:|---:|",
    ]
    for threshold in summary["accessibility_thresholds_minutes"]:
        item = summary["threshold_overview"][str(threshold)]
        lines.append(
            f"| {threshold} min | {item['municipalities_ever_exposed']} | "
            f"{item['first_exposure_cohorts']} | "
            f"{item['municipalities_with_multiple_groups_at_first_exposure']} | "
            f"{item['municipalities_with_any_later_entry']} |"
        )
    lines += [
        "",
        "## Cohortes au seuil de 120 minutes",
        "",
        "| Première exposition | Groupes entrant dans le réseau | Groupes causant une première exposition communale | Communes | Complètes 6+6 | Complètes 12+12 | Complètes 24+24 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    selected = cohorts[cohorts.accessibility_threshold_minutes.eq(120)]
    for row in selected.itertuples(index=False):
        lines.append(
            f"| {row.first_exposure_month} | {row.station_groups_entering_network_this_month} | "
            f"{row.station_groups_causing_first_municipal_exposure} | "
            f"{row.municipalities_first_exposed} | "
            f"{row.municipalities_complete_6_pre_6_post} | "
            f"{row.municipalities_complete_12_pre_12_post} | "
            f"{row.municipalities_complete_24_pre_24_post} |"
        )
    lines += [
        "",
        "## Comment lire ces nombres",
        "",
        "- Une fenêtre complète signifie uniquement que les nuitées sont observées pendant tous les mois "
        "avant et après considérés.",
        "- Le COVID n'exclut aucune ligne ici : son chevauchement est compté pour préparer l'étape 27.",
        "- Les entrées multiples sont conservées. Les groupes simultanés et les ajouts ultérieurs sont "
        "signalés afin de ne pas attribuer arbitrairement leur effet à une seule station.",
        "- L'accessibilité reste fondée sur le réseau actuel. La sensibilité GTFS 2018 n'est réutilisée "
        "que pour les communes déjà auditées et n'est jamais extrapolée aux cohortes ultérieures.",
        "",
        "## Décision méthodologique suivante",
        "",
        "L'étape 27 doit définir le traitement analytique du COVID avant toute nouvelle estimation. "
        "Ce rapport ne choisit pas cette règle : les options doivent être soumises au chercheur.",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_all_cohort_municipality_coverage.csv` : une ligne par seuil et commune exposée ;",
        "- `reports/accessibility_all_cohort_coverage_by_cohort.csv` : synthèse par mois de première exposition ;",
        "- `reports/accessibility_all_cohort_station_group_coverage.csv` : couverture des 71 groupes à chaque seuil ;",
        "- `reports/accessibility_all_cohort_coverage_summary.json` : compteurs et empreintes ;",
        "- `config/accessibility_all_cohort_coverage.json` : règles d'inventaire sans sélection.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    panel = pd.read_csv(PANEL_PATH)
    events = pd.read_csv(EVENT_PATH)
    groups = pd.read_csv(GROUP_PATH)
    journeys = pd.read_csv(JOURNEY_PATH)
    temporal = pd.read_csv(TEMPORAL_PATH)
    historical = pd.read_csv(HISTORICAL_2018_PATH)
    stage24_candidates = pd.read_csv(STAGE24_CANDIDATE_PATH)
    panel["date"] = pd.to_datetime(panel.date)
    temporal["date"] = pd.to_datetime(temporal.date)
    anchors = build_group_anchors(events, groups)
    thresholds = [int(value) for value in config["accessibility_thresholds_minutes"]]
    horizons = [int(value) for value in config["symmetric_pre_post_horizons_months"]]
    municipalities = build_municipality_inventory(
        panel, journeys, anchors, temporal, historical, thresholds, horizons
    )
    cohorts = build_cohort_summary(municipalities, anchors, horizons)
    group_coverage = build_group_summary(municipalities, anchors, thresholds, horizons)
    stage24_primary_treated_ids = set(
        stage24_candidates.loc[
            stage24_candidates.estimation_candidate_tier.eq("primary"),
            "treated_municipality_bfs_id",
        ].astype(int)
    )
    if len(stage24_primary_treated_ids) != 6:
        raise ValueError("Expected six stage-24 primary treated municipalities")
    summary = build_summary(
        config,
        panel,
        municipalities,
        cohorts,
        group_coverage,
        stage24_primary_treated_ids,
    )

    expected_exposed = {30: 5, 60: 30, 90: 55, 120: 80}
    actual_exposed = {
        threshold: summary["threshold_overview"][str(threshold)][
            "municipalities_ever_exposed"
        ]
        for threshold in thresholds
    }
    if actual_exposed != expected_exposed:
        raise ValueError(f"Unexpected exposed-municipality counts: {actual_exposed}")
    if summary["analysis_sample_selected"] or summary["causal_treatment_approved"]:
        raise ValueError("Stage 26 must remain a non-selective inventory")

    municipalities.to_csv(MUNICIPALITY_OUTPUT, index=False, lineterminator="\n")
    cohorts.to_csv(COHORT_OUTPUT, index=False, lineterminator="\n")
    group_coverage.to_csv(GROUP_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary, cohorts)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
