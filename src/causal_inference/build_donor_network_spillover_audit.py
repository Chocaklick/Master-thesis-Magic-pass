"""Audit apparent donor municipalities against the full resolved Magic Pass point network."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MUNICIPAL_OUTPUT = ROOT / "reports" / "donor_network_spillover_audit.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "donor_shortlist_network_audit.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "donor_network_spillover_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "14_DONOR_NETWORK_SPILLOVER_AUDIT.md"


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().eq("true")


def haversine_matrix(
    origin_lat: np.ndarray,
    origin_lon: np.ndarray,
    target_lat: np.ndarray,
    target_lon: np.ndarray,
) -> np.ndarray:
    lat1 = np.radians(origin_lat)[:, None]
    lon1 = np.radians(origin_lon)[:, None]
    lat2 = np.radians(target_lat)[None, :]
    lon2 = np.radians(target_lon)[None, :]
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2
    )
    return 6371.0088 * 2 * np.arcsin(np.sqrt(value))


def main() -> None:
    municipal = pd.read_csv(ROOT / "reports" / "control_contamination_audit.csv")
    shortlist = pd.read_csv(ROOT / "reports" / "donor_pretrend_shortlist.csv")
    resorts = pd.read_csv(ROOT / "data_processed" / "resort_master.csv")
    points = pd.read_csv(ROOT / "data_processed" / "resort_point_municipality.csv")
    history = pd.read_csv(ROOT / "data_processed" / "magic_pass_membership_history.csv")
    current = pd.read_csv(ROOT / "data_processed" / "magic_pass_current_destinations.csv")

    historical_ids = set(
        history.loc[
            history["event_type"].eq("base_pass_entry")
            & history["candidate_resort_id"].notna(),
            "candidate_resort_id",
        ]
    )
    current_ids = set(current.loc[current["candidate_resort_id"].notna(), "candidate_resort_id"])
    resolved_magic_ids = historical_ids | current_ids
    point_resorts = points.merge(
        resorts[
            [
                "resort_id",
                "resort_name_canonical",
                "cluster_id",
                "latitude",
                "longitude",
            ]
        ],
        on="resort_id",
        how="left",
        validate="one_to_one",
    )
    magic_points = (
        point_resorts[point_resorts["resort_id"].isin(resolved_magic_ids)]
        .drop_duplicates("resort_id")
        .reset_index(drop=True)
    )
    if magic_points.empty:
        raise ValueError("No resolved Magic Pass resort points available")

    rows: list[dict] = []
    candidates = municipal[as_bool(municipal["candidate_control_upper_bound"])].copy()
    for candidate in candidates.itertuples(index=False):
        donor_points = point_resorts[
            point_resorts["point_municipality_bfs_id"].eq(
                candidate.municipality_bfs_id
            )
        ].copy()
        if donor_points.empty:
            raise ValueError(
                f"Candidate municipality has no resort point: {candidate.municipality_bfs_id}"
            )
        distances = haversine_matrix(
            donor_points["latitude"].to_numpy(float),
            donor_points["longitude"].to_numpy(float),
            magic_points["latitude"].to_numpy(float),
            magic_points["longitude"].to_numpy(float),
        )
        origin_index, magic_index = np.unravel_index(
            np.argmin(distances), distances.shape
        )
        nearest_distance = float(distances[origin_index, magic_index])
        nearest_donor = donor_points.iloc[origin_index]
        nearest_magic = magic_points.iloc[magic_index]
        nearest_id = nearest_magic["resort_id"]
        source_scope = (
            "historical_and_current"
            if nearest_id in historical_ids and nearest_id in current_ids
            else "historical_resolved"
            if nearest_id in historical_ids
            else "current_resolved"
        )
        minimum_by_magic = distances.min(axis=0)
        donor_clusters = set(donor_points["cluster_id"].dropna())
        magic_cluster_ids = set(magic_points["cluster_id"].dropna())
        shared_clusters = sorted(donor_clusters & magic_cluster_ids)
        if nearest_distance <= 20:
            distance_band = "within_20km"
        elif nearest_distance <= 30:
            distance_band = "20_to_30km"
        elif nearest_distance <= 50:
            distance_band = "30_to_50km"
        else:
            distance_band = "beyond_50km"
        rows.append(
            {
                "municipality_bfs_id": int(candidate.municipality_bfs_id),
                "municipality_name": candidate.municipality_name,
                "donor_resort_listing_count": int(len(donor_points)),
                "minimum_distance_to_resolved_magic_km": nearest_distance,
                "closest_donor_resort_id": nearest_donor["resort_id"],
                "closest_donor_resort_name": nearest_donor["resort_name_canonical"],
                "nearest_resolved_magic_resort_id": nearest_id,
                "nearest_resolved_magic_resort_name": nearest_magic[
                    "resort_name_canonical"
                ],
                "nearest_magic_evidence_scope": source_scope,
                "resolved_magic_resorts_within_20km": int(
                    (minimum_by_magic <= 20).sum()
                ),
                "resolved_magic_resorts_within_30km": int(
                    (minimum_by_magic <= 30).sum()
                ),
                "resolved_magic_resorts_within_50km": int(
                    (minimum_by_magic <= 50).sum()
                ),
                "network_distance_band": distance_band,
                "same_lift_cluster_as_resolved_magic": bool(shared_clusters),
                "shared_magic_cluster_ids": "|".join(shared_clusters),
                "network_spillover_cleared_20km": nearest_distance > 20,
                "network_spillover_cleared_30km": nearest_distance > 30,
                "network_spillover_cleared_50km": nearest_distance > 50,
                "historical_membership_review_status": "pending_complete_label_and_operator_audit",
                "competing_pass_review_status": "pending",
                "accessibility_investment_review_status": "pending",
                "causal_control_approved": False,
                "audit_note": (
                    "Distance is from any supplied resort point in the candidate "
                    "municipality to any historically or currently resolved Magic Pass "
                    "resort point. The resolved network is a lower bound because 26 "
                    "official labels remain without approved identity equivalence."
                ),
            }
        )

    audit = pd.DataFrame(rows).sort_values(
        ["minimum_distance_to_resolved_magic_km", "municipality_bfs_id"]
    )
    audit.to_csv(MUNICIPAL_OUTPUT, index=False)
    pair_audit = shortlist.merge(
        audit.drop(columns=["causal_control_approved"]),
        left_on=["donor_municipality_bfs_id", "donor_municipality_name"],
        right_on=["municipality_bfs_id", "municipality_name"],
        how="left",
        validate="many_to_one",
    )
    if pair_audit["minimum_distance_to_resolved_magic_km"].isna().any():
        raise ValueError("Shortlisted pair is missing the network spillover audit")
    pair_audit["manual_donor_review_status"] = "network_distance_audited_other_domains_pending"
    pair_audit["causal_control_approved"] = False
    pair_audit.to_csv(PAIR_OUTPUT, index=False)

    shortlist_municipalities = audit[
        audit["municipality_bfs_id"].isin(shortlist["donor_municipality_bfs_id"])
    ]
    summary = {
        "candidate_control_municipalities_audited": int(len(audit)),
        "candidate_municipalities_within_20km_resolved_magic": int(
            audit["minimum_distance_to_resolved_magic_km"].le(20).sum()
        ),
        "candidate_municipalities_within_30km_resolved_magic": int(
            audit["minimum_distance_to_resolved_magic_km"].le(30).sum()
        ),
        "candidate_municipalities_within_50km_resolved_magic": int(
            audit["minimum_distance_to_resolved_magic_km"].le(50).sum()
        ),
        "shortlisted_unique_donor_municipalities": int(len(shortlist_municipalities)),
        "shortlisted_municipalities_within_20km_resolved_magic": int(
            shortlist_municipalities["minimum_distance_to_resolved_magic_km"].le(20).sum()
        ),
        "shortlisted_municipalities_within_30km_resolved_magic": int(
            shortlist_municipalities["minimum_distance_to_resolved_magic_km"].le(30).sum()
        ),
        "shortlisted_municipalities_within_50km_resolved_magic": int(
            shortlist_municipalities["minimum_distance_to_resolved_magic_km"].le(50).sum()
        ),
        "shortlisted_pairs": int(len(pair_audit)),
        "shortlisted_pairs_within_20km_resolved_magic": int(
            pair_audit["minimum_distance_to_resolved_magic_km"].le(20).sum()
        ),
        "shortlisted_pairs_within_30km_resolved_magic": int(
            pair_audit["minimum_distance_to_resolved_magic_km"].le(30).sum()
        ),
        "shortlisted_pairs_within_50km_resolved_magic": int(
            pair_audit["minimum_distance_to_resolved_magic_km"].le(50).sum()
        ),
        "same_cluster_candidate_municipalities": int(
            audit["same_lift_cluster_as_resolved_magic"].sum()
        ),
        "causal_controls_approved": 0,
        "interpretation": (
            "This is a network-wide proximity sensitivity against resolved Magic Pass "
            "points, not proof of actual tourism spillovers or their absence."
        ),
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report = f"""# Donor network-wide spillover audit

Generated reproducibly by `src/causal_inference/build_donor_network_spillover_audit.py`.

## Why this changes the donor screen

The earlier mechanical screen kept a donor when it was more than 30 km from the treatment under review. That is necessary but incomplete: a nominal donor can still sit next to another Magic Pass destination and receive network-related tourism spillovers. This audit therefore measures the minimum great-circle distance from every resort point in each of the {summary['candidate_control_municipalities_audited']} apparent-control municipalities to every historically or currently resolved Magic Pass resort point.

## Results

| Scope | Within 20 km | Within 30 km | Within 50 km |
|---|---:|---:|---:|
| All {summary['candidate_control_municipalities_audited']} apparent-control municipalities | {summary['candidate_municipalities_within_20km_resolved_magic']} | {summary['candidate_municipalities_within_30km_resolved_magic']} | {summary['candidate_municipalities_within_50km_resolved_magic']} |
| {summary['shortlisted_unique_donor_municipalities']} unique municipalities in the 35-pair shortlist | {summary['shortlisted_municipalities_within_20km_resolved_magic']} | {summary['shortlisted_municipalities_within_30km_resolved_magic']} | {summary['shortlisted_municipalities_within_50km_resolved_magic']} |
| 35 shortlisted treatment-donor pairs | {summary['shortlisted_pairs_within_20km_resolved_magic']} | {summary['shortlisted_pairs_within_30km_resolved_magic']} | {summary['shortlisted_pairs_within_50km_resolved_magic']} |

The distance thresholds are sensitivity bands, not causal rules. `network_spillover_cleared_30km`, for example, means only that the supplied donor resort points are more than 30 km from every resolved Magic point. It does not establish a separate visitor market, exclude shared transport corridors, or clear pass-network and investment confounding.

## Interpretation limits

- Resolved historical/current Magic resort points are a lower bound: 26 official labels still lack approved identity equivalence.
- Resort points are not full ski-domain polygons or tourism catchments.
- Great-circle distance omits road/rail travel time, shared valleys, accommodation substitution and marketing spillovers.
- Absence from a resolved link is not proof of historical non-membership.
- Competing-pass, accessibility and simultaneous-investment reviews remain pending for every donor.

No causal control is approved. Detailed outputs are `{MUNICIPAL_OUTPUT.relative_to(ROOT).as_posix()}` and `{PAIR_OUTPUT.relative_to(ROOT).as_posix()}`.
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
