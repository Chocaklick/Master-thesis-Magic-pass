"""Build qualified municipal tourism-intensity context for Path C.

The output combines official 2025 STATPOP permanent-resident population with
the internally consistent 2025 HESTA capacity-table extract. Resort coordinates
identify only their containing municipalities; reviewed destination units use
their separately approved outcome-municipality scope. Neither layer is promoted
to a validated tourism catchment or causal exposure measure.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
REFERENCE_YEAR = 2025
SOURCE_ID = "BFS_STATPOP_DATA"
CONTEXT_INTERPRETATION = "point_container_context_not_destination_catchment"
DESTINATION_CONTEXT_INTERPRETATION = (
    "reviewed_outcome_municipality_scope_current_context_not_validated_"
    "tourism_catchment_or_pre_treatment_feature"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def latest_source_record() -> dict:
    records: list[dict] = []
    for path in EVIDENCE_DIR.glob(f"{SOURCE_ID}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if (
            record.get("source_id") == SOURCE_ID
            and int(record.get("reference_year", -1)) == REFERENCE_YEAR
        ):
            records.append(record)
    if not records:
        raise FileNotFoundError(
            f"No cached {SOURCE_ID} for {REFERENCE_YEAR}; run collect_bfs_statpop.py"
        )
    record = max(records, key=lambda item: item["retrieval_date"])
    raw_path = ROOT / record["raw_file"]
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Cached STATPOP checksum failure: {raw_path}")
    return record


def load_population(record: dict) -> pd.DataFrame:
    raw = pd.read_csv(ROOT / record["raw_file"], encoding="latin-1")
    if len(raw.columns) != 6:
        raise ValueError(f"Unexpected STATPOP column count: {len(raw.columns)}")
    raw.columns = [
        "reference_year",
        "geography_label",
        "population_type",
        "citizenship_category",
        "sex_category",
        "resident_population",
    ]
    parsed = raw["geography_label"].str.extract(r"^\.{6}(\d{4})\s+(.+)$")
    if parsed.isna().any().any():
        raise ValueError("A STATPOP municipality label does not contain an exact BFS code")
    population = pd.DataFrame(
        {
            "municipality_bfs_id": parsed[0].astype(int),
            "municipality_name_statpop": parsed[1],
            "population_reference_year": pd.to_numeric(
                raw["reference_year"], errors="raise"
            ).astype(int),
            "resident_population": pd.to_numeric(
                raw["resident_population"], errors="raise"
            ).astype(int),
        }
    )
    if not population["population_reference_year"].eq(REFERENCE_YEAR).all():
        raise ValueError("STATPOP response includes an unexpected year")
    if not population["resident_population"].gt(0).all():
        raise ValueError("STATPOP municipality population must be positive")
    if not population["municipality_bfs_id"].is_unique:
        raise ValueError("STATPOP municipality BFS IDs are not unique")
    population["population_source_id"] = SOURCE_ID
    return population


def annual_hotel_context() -> pd.DataFrame:
    monthly = pd.read_csv(ROOT / "data_processed/hotel_capacity_municipality_month.csv")
    monthly = monthly[pd.to_numeric(monthly["year"], errors="raise").eq(REFERENCE_YEAR)].copy()
    if monthly.empty or monthly.groupby("municipality_bfs_id").size().ne(12).any():
        raise ValueError("HESTA 2025 must contain exactly 12 rows per municipality")

    observations = [
        "hotel_overnights_capacity_table",
        "hotel_beds_available",
        "hotel_rooms_available",
        "hotel_establishments_open",
    ]
    grouped = monthly.groupby("municipality_bfs_id", observed=True)
    annual = grouped.agg(
        municipality_name_hesta=("municipality_name_source", "first"),
        hotel_months_expected=("date", "size"),
        hotel_overnight_months_observed=(
            "hotel_overnights_capacity_table",
            "count",
        ),
        hotel_capacity_months_observed=("hotel_beds_available", "count"),
        hotel_overnights_annual=("hotel_overnights_capacity_table", "sum"),
        hotel_beds_available_monthly_mean=("hotel_beds_available", "mean"),
        hotel_rooms_available_monthly_mean=("hotel_rooms_available", "mean"),
        hotel_establishments_open_monthly_mean=("hotel_establishments_open", "mean"),
    ).reset_index()
    complete = grouped[observations].count().eq(12).all(axis=1)
    annual["complete_hotel_reference_year"] = annual["municipality_bfs_id"].map(complete)
    incomplete = ~annual["complete_hotel_reference_year"]
    annual.loc[
        incomplete,
        [
            "hotel_overnights_annual",
            "hotel_beds_available_monthly_mean",
            "hotel_rooms_available_monthly_mean",
            "hotel_establishments_open_monthly_mean",
        ],
    ] = np.nan
    annual["hotel_reference_year"] = REFERENCE_YEAR
    annual["hotel_source_id"] = "BFS_HOTEL_CAPACITY_DATA"
    return annual


def build_cluster_context(municipality: pd.DataFrame) -> pd.DataFrame:
    features = pd.read_csv(ROOT / "data_processed/path_c_resort_cluster_features.csv")
    resort = pd.read_csv(ROOT / "data_processed/resort_master.csv", dtype={"cluster_id": "string"})
    points = pd.read_csv(ROOT / "data_processed/resort_point_municipality.csv")
    links = resort[["resort_id", "cluster_id"]].dropna().merge(
        points[["resort_id", "point_municipality_bfs_id"]],
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    links["point_municipality_bfs_id"] = pd.to_numeric(
        links["point_municipality_bfs_id"], errors="coerce"
    ).astype("Int64")
    links = links.dropna(subset=["point_municipality_bfs_id"]).drop_duplicates(
        ["cluster_id", "point_municipality_bfs_id"]
    )
    links = links.merge(
        municipality,
        left_on="point_municipality_bfs_id",
        right_on="municipality_bfs_id",
        how="left",
        validate="many_to_one",
    )

    rows: list[dict[str, object]] = []
    for cluster in features[["cluster_id", "cluster_display_name", "candidate_for_path_c"]].itertuples(index=False):
        group = links[links["cluster_id"].eq(cluster.cluster_id)].copy()
        count = len(group)
        population_complete = count > 0 and group["resident_population"].notna().all()
        hotel_complete = (
            population_complete
            and as_bool(group["complete_hotel_reference_year"]).all()
        )
        population_total = (
            float(group["resident_population"].sum()) if population_complete else np.nan
        )
        nights_total = (
            float(group["hotel_overnights_annual"].sum()) if hotel_complete else np.nan
        )
        beds_total = (
            float(group["hotel_beds_available_monthly_mean"].sum())
            if hotel_complete
            else np.nan
        )
        rooms_total = (
            float(group["hotel_rooms_available_monthly_mean"].sum())
            if hotel_complete
            else np.nan
        )
        establishments_total = (
            float(group["hotel_establishments_open_monthly_mean"].sum())
            if hotel_complete
            else np.nan
        )
        if count == 0:
            status = "no_resolved_swiss_point_container"
        elif hotel_complete:
            status = "complete_point_container_population_and_hotel_context"
        elif population_complete:
            status = "population_only_no_complete_hotel_context"
        else:
            status = "incomplete_population_context"
        rows.append(
            {
                "cluster_id": cluster.cluster_id,
                "cluster_display_name": cluster.cluster_display_name,
                "candidate_for_path_c": str(cluster.candidate_for_path_c).lower() == "true",
                "point_container_municipality_count": count,
                "point_container_bfs_ids": "|".join(
                    group["point_municipality_bfs_id"].astype(str).tolist()
                ),
                "point_container_names": "|".join(
                    group["municipality_name_statpop"].dropna().astype(str).tolist()
                ),
                "all_point_containers_have_population": population_complete,
                "all_point_containers_have_complete_hotel_year": hotel_complete,
                "point_container_population": population_total,
                "point_container_hotel_overnights_annual": nights_total,
                "point_container_hotel_beds_monthly_mean": beds_total,
                "point_container_hotel_rooms_monthly_mean": rooms_total,
                "point_container_hotel_establishments_monthly_mean": establishments_total,
                "point_container_overnights_per_resident": (
                    nights_total / population_total
                    if hotel_complete and population_total > 0
                    else np.nan
                ),
                "point_container_hotel_beds_per_1000_residents": (
                    1000 * beds_total / population_total
                    if hotel_complete and population_total > 0
                    else np.nan
                ),
                "tourism_context_status": status,
                "tourism_exposure_interpretation": CONTEXT_INTERPRETATION,
                "tourism_dependence_feature_approved": False,
                "population_source_id": SOURCE_ID,
                "hotel_source_id": "BFS_HOTEL_CAPACITY_DATA",
            }
        )
    return pd.DataFrame(rows)


def build_reviewed_destination_context(municipality: pd.DataFrame) -> pd.DataFrame:
    units = pd.read_csv(ROOT / "data_processed/treatment_destination_units.csv")
    units = units[as_bool(units["eligible_for_reviewed_outcome_panel"])].copy()
    if len(units) != 11 or not units["destination_unit_id"].is_unique:
        raise ValueError("Expected 11 unique reviewed destination outcome units")

    rows: list[dict[str, object]] = []
    for unit in units.itertuples(index=False):
        bfs_ids = [int(value) for value in str(unit.municipality_bfs_ids).split("|")]
        if len(bfs_ids) != int(unit.municipality_count) or len(bfs_ids) != len(set(bfs_ids)):
            raise ValueError(f"Invalid reviewed municipality scope for {unit.destination_unit_id}")
        group = municipality[municipality["municipality_bfs_id"].isin(bfs_ids)].copy()
        if set(group["municipality_bfs_id"]) != set(bfs_ids):
            missing = sorted(set(bfs_ids) - set(group["municipality_bfs_id"]))
            raise ValueError(
                f"Missing STATPOP municipality rows for {unit.destination_unit_id}: {missing}"
            )
        population_complete = group["resident_population"].notna().all()
        hotel_complete = (
            population_complete
            and as_bool(group["complete_hotel_reference_year"]).all()
        )
        population_total = (
            float(group["resident_population"].sum()) if population_complete else np.nan
        )
        nights_total = (
            float(group["hotel_overnights_annual"].sum()) if hotel_complete else np.nan
        )
        beds_total = (
            float(group["hotel_beds_available_monthly_mean"].sum())
            if hotel_complete
            else np.nan
        )
        rooms_total = (
            float(group["hotel_rooms_available_monthly_mean"].sum())
            if hotel_complete
            else np.nan
        )
        establishments_total = (
            float(group["hotel_establishments_open_monthly_mean"].sum())
            if hotel_complete
            else np.nan
        )
        scope_kind = (
            "complete_observed_municipal_scope"
            if unit.scope_review_status
            == "approved_complete_observed_municipal_scope"
            else "core_municipality_proxy"
        )
        if unit.scope_review_status not in {
            "approved_complete_observed_municipal_scope",
            "approved_core_municipality_proxy",
        }:
            raise ValueError(
                f"Unexpected eligible scope status for {unit.destination_unit_id}: "
                f"{unit.scope_review_status}"
            )
        context_status = (
            f"complete_2025_population_and_hotel_context_{scope_kind}"
            if hotel_complete
            else f"incomplete_2025_context_{scope_kind}"
        )
        rows.append(
            {
                "destination_unit_id": unit.destination_unit_id,
                "destination_name": unit.destination_name,
                "outcome_scope_kind": scope_kind,
                "outcome_scope_review_status": unit.scope_review_status,
                "outcome_scope_municipality_count": len(bfs_ids),
                "outcome_scope_municipality_bfs_ids": "|".join(map(str, bfs_ids)),
                "outcome_scope_municipality_names": "|".join(
                    group.set_index("municipality_bfs_id")
                    .loc[bfs_ids, "municipality_name_statpop"]
                    .astype(str)
                    .tolist()
                ),
                "outcome_scope_source_ids": unit.scope_source_ids,
                "population_reference_year": REFERENCE_YEAR,
                "hotel_reference_year": REFERENCE_YEAR,
                "all_outcome_scope_municipalities_have_population": population_complete,
                "all_outcome_scope_municipalities_have_complete_hotel_year": hotel_complete,
                "outcome_scope_resident_population": population_total,
                "outcome_scope_hotel_overnights_annual": nights_total,
                "outcome_scope_hotel_beds_monthly_mean": beds_total,
                "outcome_scope_hotel_rooms_monthly_mean": rooms_total,
                "outcome_scope_hotel_establishments_monthly_mean": establishments_total,
                "outcome_scope_overnights_per_resident": (
                    nights_total / population_total
                    if hotel_complete and population_total > 0
                    else np.nan
                ),
                "outcome_scope_hotel_beds_per_1000_residents": (
                    1000 * beds_total / population_total
                    if hotel_complete and population_total > 0
                    else np.nan
                ),
                "destination_tourism_context_status": context_status,
                "destination_tourism_context_interpretation": (
                    DESTINATION_CONTEXT_INTERPRETATION
                ),
                "tourism_catchment_validated": False,
                "pre_treatment_feature_approved": False,
                "tourism_dependence_feature_approved": False,
                "causal_covariate_approved": False,
                "population_source_id": SOURCE_ID,
                "hotel_source_id": "BFS_HOTEL_CAPACITY_DATA",
            }
        )
    return pd.DataFrame(rows).sort_values("destination_unit_id")


def enrich_decision_support(cluster_context: pd.DataFrame) -> None:
    path = ROOT / "data_processed/magic_pass_decision_support.csv"
    decision = pd.read_csv(path)
    context_columns = [
        column
        for column in cluster_context.columns
        if column not in {"cluster_id", "cluster_display_name", "candidate_for_path_c"}
    ]
    decision = decision.drop(
        columns=[column for column in context_columns if column in decision.columns]
    ).merge(
        cluster_context[["cluster_id", *context_columns]],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    decision.to_csv(path, index=False)


def main() -> None:
    record = latest_source_record()
    population = load_population(record)
    hotel = annual_hotel_context()
    municipality = population.merge(
        hotel,
        on="municipality_bfs_id",
        how="left",
        validate="one_to_one",
    )
    complete_hotel = as_bool(municipality["complete_hotel_reference_year"])
    municipality["overnights_per_resident"] = np.where(
        complete_hotel,
        municipality["hotel_overnights_annual"] / municipality["resident_population"],
        np.nan,
    )
    municipality["hotel_beds_per_1000_residents"] = np.where(
        complete_hotel,
        1000
        * municipality["hotel_beds_available_monthly_mean"]
        / municipality["resident_population"],
        np.nan,
    )
    municipality["tourism_context_interpretation"] = CONTEXT_INTERPRETATION
    municipality["tourism_dependence_feature_approved"] = False
    municipality.to_csv(
        ROOT / "data_processed/municipality_tourism_context_2025.csv", index=False
    )

    cluster = build_cluster_context(municipality)
    cluster.to_csv(
        ROOT / "data_processed/path_c_cluster_tourism_context.csv", index=False
    )
    enrich_decision_support(cluster)

    destination = build_reviewed_destination_context(municipality)
    destination.to_csv(
        ROOT / "data_processed/reviewed_destination_tourism_context_2025.csv",
        index=False,
    )

    candidates = cluster[as_bool(cluster["candidate_for_path_c"])]
    complete_candidates = candidates[
        as_bool(candidates["all_point_containers_have_complete_hotel_year"])
    ]
    summary = {
        "statpop_reference_year": REFERENCE_YEAR,
        "statpop_municipalities": int(len(population)),
        "hesta_municipalities_in_reference_year": int(len(hotel)),
        "hesta_municipalities_with_complete_reference_year": int(
            as_bool(hotel["complete_hotel_reference_year"]).sum()
        ),
        "path_c_clusters": int(len(cluster)),
        "clusters_with_complete_point_container_context": int(
            as_bool(cluster["all_point_containers_have_complete_hotel_year"]).sum()
        ),
        "path_c_candidates": int(len(candidates)),
        "candidates_with_complete_point_container_context": int(
            len(complete_candidates)
        ),
        "reviewed_destination_outcome_scopes": int(len(destination)),
        "reviewed_destination_outcome_scope_municipality_links": int(
            destination["outcome_scope_municipality_count"].sum()
        ),
        "reviewed_complete_observed_municipal_scopes": int(
            destination["outcome_scope_kind"].eq(
                "complete_observed_municipal_scope"
            ).sum()
        ),
        "reviewed_core_municipality_proxies": int(
            destination["outcome_scope_kind"].eq("core_municipality_proxy").sum()
        ),
        "reviewed_destination_scopes_with_complete_2025_context": int(
            as_bool(
                destination[
                    "all_outcome_scope_municipalities_have_complete_hotel_year"
                ]
            ).sum()
        ),
        "median_reviewed_destination_outcome_scope_overnights_per_resident": float(
            destination["outcome_scope_overnights_per_resident"].median()
        ),
        "median_reviewed_destination_outcome_scope_hotel_beds_per_1000_residents": float(
            destination["outcome_scope_hotel_beds_per_1000_residents"].median()
        ),
        "validated_tourism_catchments": int(
            as_bool(destination["tourism_catchment_validated"]).sum()
        ),
        "tourism_dependence_features_approved": 0,
        "interpretation": (
            "separate_point_container_and_reviewed_outcome_municipality_scope_"
            "contexts_neither_validated_destination_catchment_or_causal_feature"
        ),
    }
    (ROOT / "reports/tourism_dependence_context_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Municipal tourism context

## Source and common rules

Official STATPOP {REFERENCE_YEAR} permanent-resident population is joined by exact BFS municipality ID to the internally consistent HESTA {REFERENCE_YEAR} extract. Annual hotel nights are summed only when all 12 monthly values are observed; monthly-mean hotel beds, rooms and establishments follow the same complete-year rule. No missing values are imputed.

The source is OFS table `px-x-0102010000_101`, filtered to permanent residents and total citizenship, sex and age. Its 31 December {REFERENCE_YEAR} population and {REFERENCE_YEAR} municipality reference are deliberately aligned to the observed Moutier (BE), BFS 700, HESTA history; the protected future Moutier (JU), BFS 6831, HESTA cells are not backfilled.

## Point-container layer

- STATPOP municipalities: **{summary['statpop_municipalities']:,}**
- HESTA municipalities in the project universe: **{summary['hesta_municipalities_in_reference_year']:,}**; complete year: **{summary['hesta_municipalities_with_complete_reference_year']:,}**
- linked Path C clusters with complete point-container population and hotel context: **{summary['clusters_with_complete_point_container_context']:,} / {summary['path_c_clusters']:,}**
- apparent Path C candidates with complete context: **{summary['candidates_with_complete_point_container_context']:,} / {summary['path_c_candidates']:,}**

`point_container_*` fields describe the unique municipalities containing the supplied listing points. They remain available for all linked clusters but do not define commercial destinations or accommodation markets.

## Reviewed destination outcome-scope layer

The 11 destination units already admitted to the hotel outcome panel are aggregated separately from their versioned outcome-municipality scope. This is not derived from listing-point containment. The layer contains **{summary['reviewed_destination_outcome_scope_municipality_links']} municipality links** and all **{summary['reviewed_destination_scopes_with_complete_2025_context']} / {summary['reviewed_destination_outcome_scopes']}** scopes have complete 2025 population and hotel context. Four are complete observed municipal scopes and seven remain explicitly labelled core-municipality proxies. Their median outcome-scope ratios are **{summary['median_reviewed_destination_outcome_scope_overnights_per_resident']:.2f} hotel nights per resident** and **{summary['median_reviewed_destination_outcome_scope_hotel_beds_per_1000_residents']:.1f} beds per 1,000 residents**.

These ratios are current 2025 descriptions, not pre-treatment features. A reviewed outcome scope is the geography used to construct an outcome, not proof of the full destination catchment. In particular, the seven core proxies deliberately remain weaker than the four complete observed municipal scopes.

## Interpretation limit

`overnights_per_resident` and `hotel_beds_per_1000_residents` describe the municipality or unique set of municipalities containing the supplied resort listing points. Point containment does **not** establish the destination's tourism catchment, visitor origin market or causal exposure. For this reason `tourism_dependence_feature_approved` remains false everywhere and the generic `tourism_dependence` decision field remains blank. These variables are qualified descriptive context, not inputs to a composite ranking.

The same non-approval applies to the reviewed outcome-scope layer: `tourism_catchment_validated`, `pre_treatment_feature_approved`, `tourism_dependence_feature_approved` and `causal_covariate_approved` are false in all 11 rows.

The separate 0/5/10 km municipality-polygon sensitivity in `reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md` tests whether transparent radius rules can extend this context. It does not change the catchment or feature approvals.

## Outputs

- `data_processed/municipality_tourism_context_2025.csv`
- `data_processed/path_c_cluster_tourism_context.csv`
- `data_processed/reviewed_destination_tourism_context_2025.csv`
- `data_processed/path_c_candidate_scope_radius_sensitivity.csv` (separate downstream scope sensitivity)
- `data_processed/magic_pass_decision_support.csv` (qualified context columns appended)
"""
    (ROOT / "reports/20_TOURISM_DEPENDENCE_CONTEXT.md").write_text(
        report, encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
