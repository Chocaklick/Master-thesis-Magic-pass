"""Build a conservative treatment-specific donor/control contamination audit.

This is a screening table, not a donor-pool approval.  It excludes known
resolved Magic Pass links, checks outcome history, and quantifies proximity to
the reviewed treated destination.  Because unresolved membership labels and
time-varying confounders remain, every control stays unapproved.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
POINTS = ROOT / "data_processed" / "resort_point_municipality.csv"
HISTORY = ROOT / "data_processed" / "magic_pass_membership_history.csv"
CURRENT = ROOT / "data_processed" / "magic_pass_current_destinations.csv"
HOTEL = ROOT / "data_processed" / "hotel_municipality_month.csv"
UNITS = ROOT / "data_processed" / "treatment_destination_units.csv"
UNIT_MUNICIPALITIES = ROOT / "data_processed" / "treatment_destination_municipality.csv"

MATRIX_OUT = ROOT / "data_processed" / "treatment_control_candidate_matrix.csv"
AUDIT_OUT = ROOT / "reports" / "control_contamination_audit.csv"
SUMMARY_OUT = ROOT / "reports" / "control_audit_summary.json"


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def haversine_km(
    lon_a: np.ndarray, lat_a: np.ndarray, lon_b: np.ndarray, lat_b: np.ndarray
) -> np.ndarray:
    lon_a = np.radians(lon_a)
    lat_a = np.radians(lat_a)
    lon_b = np.radians(lon_b)
    lat_b = np.radians(lat_b)
    dlon = lon_b - lon_a
    dlat = lat_b - lat_a
    value = np.sin(dlat / 2) ** 2 + np.cos(lat_a) * np.cos(lat_b) * np.sin(dlon / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(value))


def main() -> None:
    points = pd.read_csv(POINTS)
    history = pd.read_csv(HISTORY, dtype="string")
    current = pd.read_csv(CURRENT, dtype="string")
    hotel = pd.read_csv(HOTEL)
    units = pd.read_csv(UNITS, dtype="string")
    unit_municipalities = pd.read_csv(UNIT_MUNICIPALITIES)
    hotel["date"] = pd.to_datetime(hotel["date"], errors="raise")

    reached = points[as_bool(points["bfs_hotel_universe"])].copy()
    reached["point_municipality_bfs_id"] = reached["point_municipality_bfs_id"].astype(int)
    known_member_resort_ids = set(
        history.loc[
            history["event_type"].eq("base_pass_entry")
            & history["candidate_resort_id"].notna(),
            "candidate_resort_id",
        ]
    ) | set(current["candidate_resort_id"].dropna())
    reached["known_magic_resort_listing"] = reached["resort_id"].isin(
        known_member_resort_ids
    )

    municipality_rows: list[dict] = []
    for bfs_id, group in reached.groupby("point_municipality_bfs_id", observed=True):
        names = group["bfs_hotel_municipality_name"].dropna().unique()
        if len(names) != 1:
            raise ValueError(f"Ambiguous hotel municipality name for BFS {bfs_id}")
        municipality_rows.append(
            {
                "municipality_bfs_id": int(bfs_id),
                "municipality_name": names[0],
                "resort_listing_count": len(group),
                "known_magic_resort_listing_count": int(
                    group["known_magic_resort_listing"].sum()
                ),
                "known_magic_exposure_from_resolved_links": bool(
                    group["known_magic_resort_listing"].any()
                ),
                "candidate_control_upper_bound": not bool(
                    group["known_magic_resort_listing"].any()
                ),
                "unresolved_membership_contamination_cleared": False,
                "spillover_contamination_cleared": False,
                "time_varying_confounders_available": False,
                "causal_control_approved": False,
                "control_blocker": (
                    "Unresolved official destination labels, historical membership, "
                    "spillovers, and time-varying confounders are not fully audited."
                ),
            }
        )
    municipality_audit = pd.DataFrame(municipality_rows).sort_values(
        "municipality_bfs_id"
    )
    municipality_audit.to_csv(AUDIT_OUT, index=False)

    eligible_units = units[as_bool(units["eligible_for_reviewed_outcome_panel"])].copy()
    observed_hotel = hotel[hotel["hotel_overnights"].notna()].copy()
    observed_months = {
        name: set(group["date"])
        for name, group in observed_hotel.groupby("municipality_name_source", observed=True)
    }

    matrix_rows: list[dict] = []
    for unit in eligible_units.itertuples(index=False):
        component_ids = str(unit.component_resort_ids).split("|")
        treated_points = points[points["resort_id"].isin(component_ids)]
        if treated_points.empty:
            raise ValueError(f"No component point for {unit.destination_unit_id}")
        treated_bfs_ids = set(
            unit_municipalities.loc[
                unit_municipalities["destination_unit_id"].eq(unit.destination_unit_id),
                "municipality_bfs_id",
            ].astype(int)
        )
        anchor = pd.Timestamp(unit.first_analysis_anchor)
        for municipality in municipality_audit.itertuples(index=False):
            donor_points = reached[
                reached["point_municipality_bfs_id"].eq(
                    municipality.municipality_bfs_id
                )
            ]
            distances = []
            for donor in donor_points.itertuples(index=False):
                values = haversine_km(
                    np.full(len(treated_points), donor.point_longitude),
                    np.full(len(treated_points), donor.point_latitude),
                    treated_points["point_longitude"].to_numpy(),
                    treated_points["point_latitude"].to_numpy(),
                )
                distances.extend(values.tolist())
            minimum_distance = min(distances)
            months = observed_months.get(municipality.municipality_name, set())
            pre = sum(date < anchor for date in months)
            post = sum(date >= anchor for date in months)
            self_scope = municipality.municipality_bfs_id in treated_bfs_ids
            known_exposure = municipality.known_magic_exposure_from_resolved_links
            matrix_rows.append(
                {
                    "destination_unit_id": unit.destination_unit_id,
                    "destination_name": unit.destination_name,
                    "analysis_anchor": anchor.date().isoformat(),
                    "donor_municipality_bfs_id": municipality.municipality_bfs_id,
                    "donor_municipality_name": municipality.municipality_name,
                    "donor_resort_listing_count": municipality.resort_listing_count,
                    "known_magic_exposure_from_resolved_links": known_exposure,
                    "same_as_treated_outcome_scope": self_scope,
                    "minimum_resort_point_distance_km": round(minimum_distance, 3),
                    "within_15km": minimum_distance <= 15,
                    "within_30km": minimum_distance <= 30,
                    "within_50km": minimum_distance <= 50,
                    "observed_pre_months": pre,
                    "observed_post_months": post,
                    "has_36_observed_pre_months": pre >= 36,
                    "has_24_observed_post_months": post >= 24,
                    "provisional_donor_30km_36pre": bool(
                        not known_exposure
                        and not self_scope
                        and minimum_distance > 30
                        and pre >= 36
                        and post >= 24
                    ),
                    "unresolved_membership_contamination_cleared": False,
                    "time_varying_confounders_available": False,
                    "causal_control_approved": False,
                    "screening_note": (
                        "A provisional donor flag is only an upper-bound screen; "
                        "unresolved membership, spillovers, and confounders remain."
                    ),
                }
            )
    matrix = pd.DataFrame(matrix_rows).sort_values(
        ["destination_unit_id", "donor_municipality_bfs_id"]
    )
    matrix.to_csv(MATRIX_OUT, index=False)

    by_treatment = (
        matrix.groupby("destination_unit_id", observed=True)
        .agg(
            municipalities_screened=("donor_municipality_bfs_id", "size"),
            known_exposed=("known_magic_exposure_from_resolved_links", "sum"),
            within_30km=("within_30km", "sum"),
            provisional_donors_30km_36pre=("provisional_donor_30km_36pre", "sum"),
            causal_controls_approved=("causal_control_approved", "sum"),
        )
        .reset_index()
    )
    by_treatment.to_csv(ROOT / "reports" / "control_candidates_by_treatment.csv", index=False)

    unresolved_base_entries = history[
        history["event_type"].eq("base_pass_entry")
        & history["candidate_resort_id"].isna()
    ]
    summary = {
        "hotel_municipalities_reached_by_resort_points": int(len(municipality_audit)),
        "municipalities_with_known_magic_exposure_from_resolved_links": int(
            municipality_audit["known_magic_exposure_from_resolved_links"].sum()
        ),
        "candidate_control_municipalities_upper_bound": int(
            municipality_audit["candidate_control_upper_bound"].sum()
        ),
        "unresolved_official_base_entry_labels": int(len(unresolved_base_entries)),
        "reviewed_treatments_screened": int(len(eligible_units)),
        "treatment_donor_pairs_screened": int(len(matrix)),
        "provisional_donor_pairs_30km_36pre": int(
            matrix["provisional_donor_30km_36pre"].sum()
        ),
        "approved_causal_controls": 0,
        "interpretation": (
            "The provisional donor flag excludes resolved Magic links, the treated "
            "scope, donors within 30 km, and donors without 36 pre/24 post months. "
            "It is not an approval because membership and confounder audits are incomplete."
        ),
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
