"""Audit municipality-radius tourism scopes without validating a catchment.

For each preserved lift cluster, this module selects current Swiss municipality
polygons whose minimum straight-line distance to any supplied component point
is at most 0, 5 or 10 kilometres. It then reports how much of each artificial
scope has complete 2025 HESTA data. The same rules are evaluated against the
reviewed destination outcome scopes. The diagnostic is deliberately unable to
approve a destination catchment, candidate transfer or causal feature.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point

from build_accessibility_context import checked_gpkg, load_boundaries


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "candidate_scope_radius_sensitivity.json"
MUNICIPALITY_CONTEXT = ROOT / "data_processed" / "municipality_tourism_context_2025.csv"
MUNICIPALITY_GEOMETRY = ROOT / "data_processed" / "municipality_population_geometry_2026.csv"
RESORT_MASTER = ROOT / "data_processed" / "resort_master.csv"
CLUSTER_FEATURES = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
DESTINATION_UNITS = ROOT / "data_processed" / "treatment_destination_units.csv"
RULE_OUTPUT = ROOT / "data_processed" / "path_c_candidate_scope_radius_sensitivity.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_scope_sensitivity_summary.csv"
VALIDATION_OUTPUT = ROOT / "reports" / "candidate_scope_radius_validation.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "candidate_scope_radius_sensitivity_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md"
INTERPRETATION = (
    "municipality_polygon_radius_scope_sensitivity_not_validated_destination_"
    "catchment_or_tourism_dependence_feature"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def pipe_ints(value: object) -> list[int]:
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [int(token) for token in str(value).split("|")]


def load_municipality_evidence(boundaries: pd.DataFrame) -> pd.DataFrame:
    geometry_export = pd.read_csv(MUNICIPALITY_GEOMETRY)
    context = pd.read_csv(MUNICIPALITY_CONTEXT)
    if len(geometry_export) != 2110 or len(context) != 2115:
        raise ValueError("Unexpected municipality geometry or tourism-context grain")

    mapping_rows: list[dict[str, int]] = []
    for row in geometry_export.itertuples(index=False):
        for source_id in pipe_ints(row.population_constituent_bfs_ids_2025):
            mapping_rows.append(
                {
                    "municipality_bfs_id": source_id,
                    "boundary_bfs_id_2026": int(row.boundary_bfs_id_2026),
                }
            )
    mapping = pd.DataFrame(mapping_rows)
    if len(mapping) != 2115 or not mapping["municipality_bfs_id"].is_unique:
        raise ValueError("The 2025-to-2026 municipality mapping is incomplete")
    context = context.merge(
        mapping,
        on="municipality_bfs_id",
        how="left",
        validate="one_to_one",
    )
    if context["boundary_bfs_id_2026"].isna().any():
        raise ValueError("A 2025 tourism-context municipality has no 2026 boundary")

    rows: list[dict[str, object]] = []
    for boundary_id, group in context.groupby("boundary_bfs_id_2026", sort=True):
        complete = as_bool(group["complete_hotel_reference_year"])
        hotel_complete = bool(complete.all())
        observed = group[complete]
        rows.append(
            {
                "boundary_bfs_id_2026": int(boundary_id),
                "resident_population_2025": int(group["resident_population"].sum()),
                "hesta_complete": hotel_complete,
                "hesta_observed_population_2025": int(
                    observed["resident_population"].sum()
                ),
                "hotel_overnights_annual_2025": (
                    float(observed["hotel_overnights_annual"].sum())
                    if len(observed)
                    else np.nan
                ),
                "hotel_beds_monthly_mean_2025": (
                    float(observed["hotel_beds_available_monthly_mean"].sum())
                    if len(observed)
                    else np.nan
                ),
                "population_constituent_bfs_ids_2025": "|".join(
                    group["municipality_bfs_id"].astype(str)
                ),
            }
        )
    evidence = pd.DataFrame(rows)
    evidence = boundaries.merge(
        evidence,
        on="boundary_bfs_id_2026",
        how="left",
        validate="one_to_one",
    )
    if evidence[
        ["resident_population_2025", "hesta_complete"]
    ].isna().any().any():
        raise ValueError("A current municipality boundary lacks aligned evidence")
    return evidence


def component_points(resort: pd.DataFrame, resort_ids: list[str]) -> list[Point]:
    group = resort[resort["resort_id"].isin(resort_ids)]
    if set(group["resort_id"]) != set(resort_ids):
        missing = sorted(set(resort_ids) - set(group["resort_id"]))
        raise ValueError(f"Missing component resort coordinates: {missing}")
    if group[["longitude", "latitude"]].isna().any().any():
        raise ValueError("Component resort coordinates cannot be missing")
    transform = Transformer.from_crs(4326, 2056, always_xy=True)
    return [
        Point(*transform.transform(row.longitude, row.latitude))
        for row in group.itertuples(index=False)
    ]


def distances_to_components(
    municipalities: pd.DataFrame, points: list[Point]
) -> np.ndarray:
    if not points:
        return np.full(len(municipalities), np.inf)
    return np.array(
        [
            min(geometry.distance(point) for point in points) / 1000
            for geometry in municipalities["geometry"]
        ],
        dtype=float,
    )


def scope_row(
    *,
    analysis_version: str,
    cluster_id: str,
    cluster_display_name: str,
    candidate: bool,
    radius: int,
    selected: pd.DataFrame,
    config: dict[str, object],
) -> dict[str, object]:
    population = int(selected["resident_population_2025"].sum()) if len(selected) else 0
    observed = selected[as_bool(selected["hesta_complete"])]
    observed_population = (
        int(observed["hesta_observed_population_2025"].sum()) if len(observed) else 0
    )
    observed_nights = (
        float(observed["hotel_overnights_annual_2025"].sum()) if len(observed) else np.nan
    )
    observed_beds = (
        float(observed["hotel_beds_monthly_mean_2025"].sum()) if len(observed) else np.nan
    )
    complete = len(selected) > 0 and len(observed) == len(selected)
    row = {
        "analysis_version": analysis_version,
        "cluster_id": cluster_id,
        "cluster_display_name": cluster_display_name,
        "candidate_for_path_c": candidate,
        "scope_rule_id": f"municipality_polygon_within_{radius}km_of_any_component",
        "radius_km": radius,
        "selected_municipality_count": int(len(selected)),
        "selected_bfs_ids_2026": "|".join(
            selected["boundary_bfs_id_2026"].astype(str)
        ),
        "selected_municipality_names_2026": "|".join(
            selected["boundary_name_2026"].astype(str)
        ),
        "scope_resident_population_2025": population,
        "hesta_complete_municipality_count": int(len(observed)),
        "hesta_observed_population_2025": observed_population,
        "hesta_population_coverage_share": (
            observed_population / population if population > 0 else np.nan
        ),
        "observed_hesta_hotel_overnights_annual_2025": observed_nights,
        "observed_hesta_hotel_beds_monthly_mean_2025": observed_beds,
        "observed_hesta_overnights_per_resident": (
            observed_nights / observed_population
            if observed_population > 0 and pd.notna(observed_nights)
            else np.nan
        ),
        "observed_hesta_beds_per_1000_residents": (
            1000 * observed_beds / observed_population
            if observed_population > 0 and pd.notna(observed_beds)
            else np.nan
        ),
        "complete_scope_hotel_context": complete,
        "complete_scope_overnights_per_resident": (
            observed_nights / population
            if complete and population > 0 and pd.notna(observed_nights)
            else np.nan
        ),
        "complete_scope_beds_per_1000_residents": (
            1000 * observed_beds / population
            if complete and population > 0 and pd.notna(observed_beds)
            else np.nan
        ),
        "boundary_reference_date": config["boundary_reference_date"],
        "population_reference_year": config["population_reference_year"],
        "hotel_reference_year": config["hotel_reference_year"],
        "distance_crs": config["distance_crs"],
        "scope_interpretation": INTERPRETATION,
    }
    row.update({key: bool(value) for key, value in config["protected_outputs"].items()})
    return row


def build_cluster_rules(
    config: dict[str, object], municipalities: pd.DataFrame, resort: pd.DataFrame
) -> pd.DataFrame:
    features = pd.read_csv(CLUSTER_FEATURES, dtype={"cluster_id": "string"})
    rows: list[dict[str, object]] = []
    for cluster in features.itertuples(index=False):
        resort_ids = resort.loc[
            resort["cluster_id"].eq(cluster.cluster_id), "resort_id"
        ].astype(str).tolist()
        distances = distances_to_components(
            municipalities, component_points(resort, resort_ids)
        )
        for radius in config["radius_rules_km"]:
            selected = municipalities.loc[distances <= float(radius) + 1e-9].sort_values(
                "boundary_bfs_id_2026"
            )
            rows.append(
                scope_row(
                    analysis_version=config["analysis_version"],
                    cluster_id=cluster.cluster_id,
                    cluster_display_name=cluster.cluster_display_name,
                    candidate=str(cluster.candidate_for_path_c).lower() == "true",
                    radius=int(radius),
                    selected=selected,
                    config=config,
                )
            )
    rules = pd.DataFrame(rows)
    expected = len(features) * len(config["radius_rules_km"])
    if len(rules) != expected or rules.duplicated(["cluster_id", "radius_km"]).any():
        raise ValueError("Scope-radius output does not preserve cluster-rule grain")
    protected = list(config["protected_outputs"])
    if rules[protected].any().any():
        raise ValueError("A protected scope-radius output became true")
    return rules


def summarise_clusters(config: dict[str, object], rules: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for cluster_id, group in rules.groupby("cluster_id", sort=True):
        group = group.sort_values("radius_km")
        candidate = bool(group["candidate_for_path_c"].iloc[0])
        row: dict[str, object] = {
            "analysis_version": config["analysis_version"],
            "cluster_id": cluster_id,
            "candidate_for_path_c": candidate,
            "candidate_scope_radius_sensitivity_status": (
                "complete_radius_diagnostic_not_validated"
                if int(group.loc[group["radius_km"].eq(0), "selected_municipality_count"].iloc[0]) > 0
                else "no_swiss_zero_radius_scope_diagnostic_not_validated"
            ),
            "candidate_scope_radius_rules_evaluated": int(len(group)),
            "candidate_scope_municipality_count_min": int(
                group["selected_municipality_count"].min()
            ),
            "candidate_scope_municipality_count_max": int(
                group["selected_municipality_count"].max()
            ),
            "candidate_scope_complete_hotel_context_rule_count": int(
                as_bool(group["complete_scope_hotel_context"]).sum()
            ),
            "candidate_scope_hesta_population_coverage_share_min": float(
                group["hesta_population_coverage_share"].min()
            ) if group["hesta_population_coverage_share"].notna().any() else np.nan,
            "candidate_scope_hesta_population_coverage_share_max": float(
                group["hesta_population_coverage_share"].max()
            ) if group["hesta_population_coverage_share"].notna().any() else np.nan,
            "candidate_scope_observed_overnights_per_resident_min": float(
                group["observed_hesta_overnights_per_resident"].min()
            ) if group["observed_hesta_overnights_per_resident"].notna().any() else np.nan,
            "candidate_scope_observed_overnights_per_resident_max": float(
                group["observed_hesta_overnights_per_resident"].max()
            ) if group["observed_hesta_overnights_per_resident"].notna().any() else np.nan,
            "tourism_catchment_validated": False,
            "candidate_scope_transfer_approved": False,
            "pre_treatment_feature_approved": False,
            "causal_covariate_approved": False,
            "scope_interpretation": INTERPRETATION,
        }
        for radius in config["radius_rules_km"]:
            record = group[group["radius_km"].eq(radius)].iloc[0]
            row[f"scope_{radius}km_municipality_count"] = int(
                record["selected_municipality_count"]
            )
            row[f"scope_{radius}km_hesta_population_coverage_share"] = record[
                "hesta_population_coverage_share"
            ]
            row[f"scope_{radius}km_observed_overnights_per_resident"] = record[
                "observed_hesta_overnights_per_resident"
            ]
        rows.append(row)
    summary = pd.DataFrame(rows)
    if len(summary) * len(config["radius_rules_km"]) != len(rules):
        raise ValueError("Cluster sensitivity summary has an unexpected grain")
    return summary


def map_2025_to_2026(municipalities: pd.DataFrame) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for row in municipalities.itertuples(index=False):
        for source_id in pipe_ints(row.population_constituent_bfs_ids_2025):
            if source_id in mapping:
                raise ValueError(f"Duplicate 2025 municipality mapping: {source_id}")
            mapping[source_id] = int(row.boundary_bfs_id_2026)
    if len(mapping) != 2115:
        raise ValueError("Unexpected 2025-to-2026 mapping size")
    return mapping


def validate_against_reviewed_scopes(
    config: dict[str, object],
    municipalities: pd.DataFrame,
    resort: pd.DataFrame,
) -> pd.DataFrame:
    units = pd.read_csv(DESTINATION_UNITS)
    units = units[as_bool(units["eligible_for_reviewed_outcome_panel"])].copy()
    if len(units) != 11:
        raise ValueError("Expected 11 reviewed destination units")
    mapping = map_2025_to_2026(municipalities)
    rows: list[dict[str, object]] = []
    for unit in units.itertuples(index=False):
        resort_ids = str(unit.component_resort_ids).split("|")
        distances = distances_to_components(
            municipalities, component_points(resort, resort_ids)
        )
        expected = {mapping[value] for value in pipe_ints(unit.municipality_bfs_ids)}
        scope_kind = (
            "complete_observed_municipal_scope"
            if unit.scope_review_status == "approved_complete_observed_municipal_scope"
            else "core_municipality_proxy"
        )
        for radius in config["radius_rules_km"]:
            selected = set(
                municipalities.loc[
                    distances <= float(radius) + 1e-9, "boundary_bfs_id_2026"
                ].astype(int)
            )
            intersection = selected & expected
            union = selected | expected
            rows.append(
                {
                    "analysis_version": config["analysis_version"],
                    "destination_unit_id": unit.destination_unit_id,
                    "destination_name": unit.destination_name,
                    "reviewed_scope_kind": scope_kind,
                    "radius_km": int(radius),
                    "reviewed_scope_bfs_ids_2026": "|".join(map(str, sorted(expected))),
                    "radius_scope_bfs_ids_2026": "|".join(map(str, sorted(selected))),
                    "reviewed_scope_municipality_count": len(expected),
                    "radius_scope_municipality_count": len(selected),
                    "intersection_municipality_count": len(intersection),
                    "extra_radius_municipality_count": len(selected - expected),
                    "missed_reviewed_municipality_count": len(expected - selected),
                    "exact_scope_match": selected == expected,
                    "precision": len(intersection) / len(selected) if selected else 0.0,
                    "recall": len(intersection) / len(expected),
                    "jaccard": len(intersection) / len(union) if union else 1.0,
                    "candidate_scope_transfer_approved": False,
                    "tourism_catchment_validated": False,
                    "scope_interpretation": INTERPRETATION,
                }
            )
    validation = pd.DataFrame(rows)
    expected_rows = len(units) * len(config["radius_rules_km"])
    if len(validation) != expected_rows:
        raise ValueError("Reviewed-scope radius validation has an unexpected grain")
    if validation[["candidate_scope_transfer_approved", "tourism_catchment_validated"]].any().any():
        raise ValueError("A reviewed-scope protection gate became true")
    return validation


def enrich_decision_support(summary: pd.DataFrame) -> None:
    path = ROOT / "data_processed" / "magic_pass_decision_support.csv"
    decision = pd.read_csv(path)
    context_columns = [
        column
        for column in summary.columns
        if column not in {"analysis_version", "cluster_id", "candidate_for_path_c"}
    ]
    decision = decision.drop(
        columns=[column for column in context_columns if column in decision.columns]
    ).merge(
        summary[["cluster_id", *context_columns]],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    guarded = [
        "predicted_uplift_pct",
        "composite_opportunity_need_score",
        "recommendation_confidence",
    ]
    if any(column in decision and decision[column].notna().any() for column in guarded):
        raise ValueError("A protected decision-support value became populated")
    decision.to_csv(path, index=False)


def build_summary(
    config: dict[str, object],
    rules: pd.DataFrame,
    cluster_summary: pd.DataFrame,
    validation: pd.DataFrame,
) -> dict[str, object]:
    candidates = cluster_summary[as_bool(cluster_summary["candidate_for_path_c"])]
    complete_scope = validation[
        validation["reviewed_scope_kind"].eq("complete_observed_municipal_scope")
    ]
    radius_validation: dict[str, dict[str, object]] = {}
    for radius, group in complete_scope.groupby("radius_km", sort=True):
        radius_validation[str(int(radius))] = {
            "exact_matches": int(as_bool(group["exact_scope_match"]).sum()),
            "destinations": int(len(group)),
            "reviewed_links_recovered": int(group["intersection_municipality_count"].sum()),
            "reviewed_links": int(group["reviewed_scope_municipality_count"].sum()),
            "extra_municipality_links": int(group["extra_radius_municipality_count"].sum()),
            "mean_precision": float(group["precision"].mean()),
            "mean_recall": float(group["recall"].mean()),
        }
    return {
        "analysis_version": config["analysis_version"],
        "radius_rules_km": config["radius_rules_km"],
        "path_c_clusters": int(cluster_summary["cluster_id"].nunique()),
        "path_c_candidates": int(len(candidates)),
        "candidate_rule_rows": int(
            len(rules[as_bool(rules["candidate_for_path_c"])])
        ),
        "candidates_with_swiss_zero_radius_scope": int(
            candidates["scope_0km_municipality_count"].gt(0).sum()
        ),
        "candidates_with_any_observed_hesta_ratio": int(
            candidates["candidate_scope_observed_overnights_per_resident_max"]
            .notna()
            .sum()
        ),
        "candidates_with_complete_hotel_context_for_any_rule": int(
            candidates["candidate_scope_complete_hotel_context_rule_count"].gt(0).sum()
        ),
        "reviewed_destination_rule_rows": int(len(validation)),
        "complete_observed_scope_validation_by_radius_km": radius_validation,
        "validated_tourism_catchments": int(
            as_bool(cluster_summary["tourism_catchment_validated"]).sum()
        ),
        "candidate_scope_transfers_approved": int(
            as_bool(cluster_summary["candidate_scope_transfer_approved"]).sum()
        ),
        "interpretation": INTERPRETATION,
    }


def write_report(summary: dict[str, object]) -> None:
    rows = [
        "| Radius | Exact complete scopes | Reviewed links recovered | Extra municipality links | Mean precision | Mean recall |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for radius, values in summary["complete_observed_scope_validation_by_radius_km"].items():
        rows.append(
            f"| {radius} km | {values['exact_matches']} / {values['destinations']} | "
            f"{values['reviewed_links_recovered']} / {values['reviewed_links']} | "
            f"{values['extra_municipality_links']} | {values['mean_precision']:.3f} | "
            f"{values['mean_recall']:.3f} |"
        )
    REPORT_OUTPUT.write_text(
        f"""# Candidate destination-scope radius sensitivity

## Purpose

This audit tests three transparent geometric rules—municipality polygons within 0, 5 or 10 km of any supplied cluster component point—without calling any of them a destination catchment. It uses official swissBOUNDARIES3D 2026 polygons, STATPOP 2025 population and complete-year HESTA 2025 observations. Every scope is current and straight-line; none is a visitor-origin market, travel-time basin or pre-treatment feature.

## Candidate coverage

- Path C candidates: **{summary['path_c_candidates']}**; rule rows: **{summary['candidate_rule_rows']}**
- candidates with a Swiss municipality at 0 km: **{summary['candidates_with_swiss_zero_radius_scope']}**
- candidates with at least one observed HESTA ratio under any rule: **{summary['candidates_with_any_observed_hesta_ratio']}**
- candidates with complete HESTA coverage for every municipality under at least one rule: **{summary['candidates_with_complete_hotel_context_for_any_rule']}**
- validated tourism catchments: **{summary['validated_tourism_catchments']}**
- approved candidate scope transfers: **{summary['candidate_scope_transfers_approved']}**

An observed HESTA ratio uses only municipalities with a complete published hotel year. The accompanying population-coverage share makes the partial denominator explicit. A complete-scope ratio is emitted only when every municipality selected by the rule has complete HESTA data.

## Validation against independently reviewed complete outcome scopes

{chr(10).join(rows)}

The zero-kilometre rule is component-point containment. Larger radii may recover a municipality omitted by point containment, but they also add municipalities not present in the reviewed outcome scope. This precision–recall trade-off is evidence that a universal radius is a sensitivity device, not validation of a commercial or accommodation catchment. The seven core-municipality proxies are retained in the validation file as a separate definition-linked stratum and are not used to claim independent validation.

## Interpretation limit

The outputs can diagnose how strongly current tourism context changes under simple municipal scope rules. They cannot identify where guests stay, prove a candidate's destination boundary, establish historical tourism dependence or support a recommendation. `tourism_catchment_validated`, `candidate_scope_transfer_approved`, `pre_treatment_feature_approved` and `causal_covariate_approved` therefore remain false throughout.

## Outputs

- `config/candidate_scope_radius_sensitivity.json`
- `data_processed/path_c_candidate_scope_radius_sensitivity.csv`
- `data_processed/path_c_cluster_scope_sensitivity_summary.csv`
- `reports/candidate_scope_radius_validation.csv`
- `reports/candidate_scope_radius_sensitivity_summary.json`
- `reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md`
""",
        encoding="utf-8",
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["interpretation"] != INTERPRETATION:
        raise ValueError("Scope-radius interpretation differs from the approved label")
    radii = [int(value) for value in config["radius_rules_km"]]
    if radii != [0, 5, 10]:
        raise ValueError("The predeclared scope-radius rules must be 0, 5 and 10 km")

    boundaries = load_boundaries(checked_gpkg())
    municipalities = load_municipality_evidence(boundaries)
    resort = pd.read_csv(RESORT_MASTER, dtype={"cluster_id": "string"})
    if not resort["resort_id"].is_unique:
        raise ValueError("Resort master IDs must be unique")

    rules = build_cluster_rules(config, municipalities, resort)
    cluster_summary = summarise_clusters(config, rules)
    validation = validate_against_reviewed_scopes(config, municipalities, resort)
    enrich_decision_support(cluster_summary)
    summary = build_summary(config, rules, cluster_summary, validation)

    rules.to_csv(RULE_OUTPUT, index=False)
    cluster_summary.to_csv(CLUSTER_OUTPUT, index=False)
    validation.to_csv(VALIDATION_OUTPUT, index=False)
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
