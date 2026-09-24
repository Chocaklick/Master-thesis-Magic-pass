"""Audit whether component-point municipalities reproduce reviewed outcome scopes.

This is a transferability diagnostic for the existing point-container context.
It does not construct or validate tourism catchments. Core-municipality proxies
are definition-linked to point containment and are therefore reported separately
from the complete observed municipal scopes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "reports" / "destination_scope_concordance_audit.csv"
SUMMARY = ROOT / "reports" / "destination_scope_concordance_audit_summary.json"
REPORT = ROOT / "reports" / "37_DESTINATION_SCOPE_CONCORDANCE_AUDIT.md"
INTERPRETATION = (
    "component_point_municipality_scope_transfer_diagnostic_not_validated_"
    "tourism_catchment_or_candidate_outcome_scope"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def pipe_values(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [item.strip() for item in str(value).split("|") if item.strip()]


def joined(values: set[str]) -> str:
    return "|".join(sorted(values, key=int))


def build_audit() -> pd.DataFrame:
    units = pd.read_csv(
        ROOT / "data_processed" / "treatment_destination_units.csv",
        dtype="string",
    )
    units = units[as_bool(units["eligible_for_reviewed_outcome_panel"])].copy()
    if len(units) != 11 or not units["destination_unit_id"].is_unique:
        raise ValueError("Expected 11 unique reviewed destination outcome units")

    points = pd.read_csv(
        ROOT / "data_processed" / "resort_point_municipality.csv",
        dtype="string",
    )
    if not points["resort_id"].is_unique:
        raise ValueError("Point-municipality resort IDs must be unique")
    point_lookup = points.set_index("resort_id")

    rows: list[dict[str, object]] = []
    for unit in units.itertuples(index=False):
        component_ids = pipe_values(unit.component_resort_ids)
        missing_components = sorted(set(component_ids) - set(point_lookup.index))
        if missing_components:
            raise ValueError(
                f"Missing point-container components for {unit.destination_unit_id}: "
                f"{missing_components}"
            )
        component_points = point_lookup.loc[component_ids]
        if component_points["point_municipality_bfs_id"].isna().any():
            raise ValueError(
                f"Unresolved point municipality for {unit.destination_unit_id}"
            )

        point_ids = set(
            component_points["point_municipality_bfs_id"].astype(str).tolist()
        )
        point_name_by_id = {
            str(row.point_municipality_bfs_id): str(row.point_municipality_name)
            for row in component_points.itertuples(index=False)
        }
        outcome_id_list = pipe_values(unit.municipality_bfs_ids)
        outcome_name_list = pipe_values(unit.municipality_names)
        if (
            len(outcome_id_list) != int(unit.municipality_count)
            or len(outcome_id_list) != len(set(outcome_id_list))
            or len(outcome_name_list) != len(outcome_id_list)
        ):
            raise ValueError(
                f"Invalid reviewed outcome scope for {unit.destination_unit_id}"
            )
        outcome_ids = set(outcome_id_list)
        outcome_name_by_id = dict(zip(outcome_id_list, outcome_name_list, strict=True))

        intersection = point_ids & outcome_ids
        point_only = point_ids - outcome_ids
        outcome_only = outcome_ids - point_ids
        union = point_ids | outcome_ids
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
        exact = point_ids == outcome_ids
        if scope_kind == "core_municipality_proxy":
            if not exact:
                raise ValueError(
                    f"Definition-linked core proxy mismatch for {unit.destination_unit_id}"
                )
            comparison_status = "exact_definition_linked_core_proxy"
            independence_status = "definition_linked_not_independent_validation"
        elif exact:
            comparison_status = "exact_complete_scope_concordance"
            independence_status = "separately_reviewed_complete_scope_comparison"
        else:
            comparison_status = "partial_complete_scope_missing_outcome_municipality"
            independence_status = "separately_reviewed_complete_scope_comparison"

        rows.append(
            {
                "destination_unit_id": unit.destination_unit_id,
                "destination_name": unit.destination_name,
                "reviewed_outcome_scope_kind": scope_kind,
                "reviewed_outcome_scope_status": unit.scope_review_status,
                "component_resort_count": len(component_ids),
                "component_resort_ids": "|".join(component_ids),
                "component_point_municipality_count": len(point_ids),
                "component_point_municipality_bfs_ids": joined(point_ids),
                "component_point_municipality_names": "|".join(
                    point_name_by_id[bfs_id]
                    for bfs_id in sorted(point_ids, key=int)
                ),
                "reviewed_outcome_municipality_count": len(outcome_ids),
                "reviewed_outcome_municipality_bfs_ids": joined(outcome_ids),
                "reviewed_outcome_municipality_names": "|".join(
                    outcome_name_by_id[bfs_id]
                    for bfs_id in sorted(outcome_ids, key=int)
                ),
                "shared_municipality_count": len(intersection),
                "shared_municipality_bfs_ids": joined(intersection),
                "component_point_only_municipality_count": len(point_only),
                "component_point_only_municipality_bfs_ids": joined(point_only),
                "reviewed_outcome_only_municipality_count": len(outcome_only),
                "reviewed_outcome_only_municipality_bfs_ids": joined(outcome_only),
                "component_point_scope_precision": len(intersection) / len(point_ids),
                "component_point_scope_recall": len(intersection) / len(outcome_ids),
                "component_point_scope_jaccard": len(intersection) / len(union),
                "exact_municipality_set_match": exact,
                "scope_concordance_status": comparison_status,
                "comparison_independence_status": independence_status,
                "scope_concordance_interpretation": INTERPRETATION,
                "candidate_scope_transfer_approved": False,
                "tourism_catchment_validated": False,
                "causal_covariate_approved": False,
                "point_scope_source_id": "GEOADMIN_MUNICIPALITY_IDENTIFY",
                "reviewed_scope_source_ids": unit.scope_source_ids,
            }
        )

    audit = pd.DataFrame(rows).sort_values("destination_unit_id").reset_index(drop=True)
    if audit["component_point_only_municipality_count"].sum() != 0:
        raise ValueError("Unexpected component-point-only municipality in reviewed audit")
    return audit


def build_summary(audit: pd.DataFrame) -> dict[str, object]:
    complete = audit[
        audit["reviewed_outcome_scope_kind"].eq(
            "complete_observed_municipal_scope"
        )
    ]
    core = audit[
        audit["reviewed_outcome_scope_kind"].eq("core_municipality_proxy")
    ]
    return {
        "reviewed_destinations": int(len(audit)),
        "destinations_with_exact_municipality_set_match": int(
            audit["exact_municipality_set_match"].sum()
        ),
        "reviewed_outcome_municipality_links": int(
            audit["reviewed_outcome_municipality_count"].sum()
        ),
        "component_point_municipality_links": int(
            audit["component_point_municipality_count"].sum()
        ),
        "shared_municipality_links": int(audit["shared_municipality_count"].sum()),
        "reviewed_outcome_only_municipality_links": int(
            audit["reviewed_outcome_only_municipality_count"].sum()
        ),
        "component_point_only_municipality_links": int(
            audit["component_point_only_municipality_count"].sum()
        ),
        "overall_component_point_scope_precision": float(
            audit["shared_municipality_count"].sum()
            / audit["component_point_municipality_count"].sum()
        ),
        "overall_component_point_scope_recall": float(
            audit["shared_municipality_count"].sum()
            / audit["reviewed_outcome_municipality_count"].sum()
        ),
        "core_proxy_destinations": int(len(core)),
        "core_proxy_exact_matches": int(core["exact_municipality_set_match"].sum()),
        "complete_scope_destinations": int(len(complete)),
        "complete_scope_exact_matches": int(
            complete["exact_municipality_set_match"].sum()
        ),
        "complete_scope_reviewed_municipality_links": int(
            complete["reviewed_outcome_municipality_count"].sum()
        ),
        "complete_scope_shared_municipality_links": int(
            complete["shared_municipality_count"].sum()
        ),
        "complete_scope_component_point_recall": float(
            complete["shared_municipality_count"].sum()
            / complete["reviewed_outcome_municipality_count"].sum()
        ),
        "candidate_scope_transfers_approved": int(
            audit["candidate_scope_transfer_approved"].sum()
        ),
        "validated_tourism_catchments": int(
            audit["tourism_catchment_validated"].sum()
        ),
        "interpretation": INTERPRETATION,
    }


def write_report(summary: dict[str, object], audit: pd.DataFrame) -> None:
    incomplete = audit[~audit["exact_municipality_set_match"]]
    missing_text = ", ".join(
        f"{row.destination_name}: {row.reviewed_outcome_only_municipality_bfs_ids}"
        for row in incomplete.itertuples(index=False)
    )
    report = f"""# Destination scope concordance audit

## Question

Can the municipalities containing the supplied destination component points reproduce the municipality scopes already reviewed for hotel outcomes? This is a transferability diagnostic for the candidate point-container layer, not a construction or validation of tourism catchments.

## Result

- exact municipality-set matches: **{summary['destinations_with_exact_municipality_set_match']} / {summary['reviewed_destinations']}**;
- all reviewed links recovered: **{summary['shared_municipality_links']} / {summary['reviewed_outcome_municipality_links']}** ({100 * summary['overall_component_point_scope_recall']:.1f}% recall);
- point-scope precision: **{100 * summary['overall_component_point_scope_precision']:.1f}%**; no component-point municipality lies outside its reviewed outcome scope;
- definition-linked core proxies: **{summary['core_proxy_exact_matches']} / {summary['core_proxy_destinations']}** exact;
- separately reviewed complete scopes: **{summary['complete_scope_exact_matches']} / {summary['complete_scope_destinations']}** exact, recovering **{summary['complete_scope_shared_municipality_links']} / {summary['complete_scope_reviewed_municipality_links']}** municipality links;
- missing reviewed municipality: **{missing_text}**.

## Interpretation

The seven core-proxy matches are expected because those scopes were explicitly defined from the component's core municipality; they are not independent validation. The informative comparison is the four complete observed municipal scopes: three are reproduced exactly, while the Meiringen-Hasliberg component point falls in Hasliberg and does not recover Meiringen. Point containment is therefore a useful, conservative core-municipality descriptor, but it can omit an outcome municipality even in this small reviewed set.

No candidate-scope transfer is approved. A component-point municipality set is not a visitor catchment, a hotel market, an observed origin market or a pre-treatment causal covariate. The audit supports retaining candidate point-container ratios as qualified descriptive context only; it does not justify filling `tourism_dependence`, changing analogue matching or producing a composite ranking.

The follow-up 0/5/10 km municipality-polygon sensitivity is documented in `reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md`. It recovers the missing reviewed municipality at larger radii only by adding many municipalities outside the reviewed scopes, so it does not reverse this decision.

## Outputs

- `reports/destination_scope_concordance_audit.csv`
- `reports/destination_scope_concordance_audit_summary.json`
- `reports/37_DESTINATION_SCOPE_CONCORDANCE_AUDIT.md`
- `reports/40_CANDIDATE_SCOPE_RADIUS_SENSITIVITY.md` (downstream radius validation)
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    audit = build_audit()
    summary = build_summary(audit)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(OUTPUT, index=False)
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_report(summary, audit)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
