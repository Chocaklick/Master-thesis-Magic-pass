"""Reproduce the initial resort/outcome/cluster checks. No inferred treatment."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from audit_existing_data import ROOT, read_csv, sha256

MONTHS = {name: i + 1 for i, name in enumerate([
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août",
    "Septembre", "Octobre", "Novembre", "Décembre"])}


def extract_constant(path: Path, name: str):
    text = path.read_text(encoding="utf-8")
    start = text.index("=", text.index("const " + name)) + 1
    return json.JSONDecoder().raw_decode(text[start:].lstrip())[0]


def numeric_outcome(values: pd.Series) -> pd.Series:
    """Only nonnegative whole-number observations qualify; never impute tokens."""
    valid = values.str.fullmatch(r"\d+")
    return pd.to_numeric(values.where(valid), errors="coerce").astype("Int64")


def main():
    out = ROOT / "data_processed"
    manifest = pd.read_csv(ROOT / "metadata/raw_file_manifest.csv", dtype=str)
    source = dict(zip(manifest.file_name, manifest.source_id))
    for record in manifest.to_dict("records"):
        assert sha256(ROOT / record["file_name"]) == record["sha256"], record["file_name"]
    stations = read_csv(ROOT / "data_raw/stations_ski_gps_bergfex_normalise.csv")
    bergfex = read_csv(ROOT / "data_raw/bergfex_stations_ski_suisse_par_region.csv")
    assignments = read_csv(ROOT / "data_raw/stations_ski_assignations_clusters_gps_bergfex.csv")
    clusters = read_csv(ROOT / "data_raw/stations_ski_clusters_resume_gps_bergfex.csv")
    features = json.loads((ROOT / "data_raw/stations_ski_clusters_gps_bergfex.geojson").read_text(encoding="utf-8"))["features"]
    assert stations.ski_id.is_unique and assignments.ski_id.is_unique and clusters.cluster_id.is_unique
    assert bergfex.url_station.is_unique, "Resolve duplicated URLs before joining"
    assert set(stations.ski_id) == set(assignments.ski_id)
    assert set(assignments.cluster_id) <= set(clusters.cluster_id)
    master = stations.rename(columns={"ski_id": "resort_id", "ski_name": "resort_name_canonical",
        "original_station_name": "resort_name_original", "lat": "latitude", "lon": "longitude"})[
        ["resort_id", "resort_name_canonical", "resort_name_original", "latitude", "longitude", "region", "url_station"]]
    master = master.merge(bergfex[["url_station", "altitude_max_m", "pistes_km", "lifts_total"]],
                          on="url_station", how="left", validate="one_to_one")
    master = master.merge(assignments[["ski_id", "cluster_id", "assignment_quality", "distance_m"]],
                          left_on="resort_id", right_on="ski_id", how="left", validate="one_to_one").drop(columns="ski_id")
    master = master.rename(columns={"altitude_max_m": "altitude_top_m", "pistes_km": "ski_area_km",
                                    "lifts_total": "number_lifts"})
    master["identity_status"] = "provisional_existing_listing_not_independent_domain"
    master["feature_observation_date"] = "UNKNOWN"
    for column in ["municipality_bfs_id", "country", "magic_pass_member", "magic_pass_entry_date"]:
        master[column] = "UNKNOWN"
    master["source_ids"] = "|".join(source["data_raw/" + p] for p in [
        "stations_ski_gps_bergfex_normalise.csv", "bergfex_stations_ski_suisse_par_region.csv",
        "stations_ski_assignations_clusters_gps_bergfex.csv"])
    master.to_csv(out / "resort_master.csv", index=False)
    assignments[assignments.assignment_quality != "confident"].to_csv(ROOT / "reports/assignment_review_queue.csv", index=False)
    clusters[pd.to_numeric(clusters.station_count) > 1].to_csv(ROOT / "reports/multiple_resorts_per_cluster.csv", index=False)
    entity = master[["resort_id", "resort_name_original", "resort_name_canonical", "url_station"]].copy()
    entity["match_method"] = "existing ski_id retained; exact unique URL joins; no fuzzy merges"
    entity["manual_review"] = "pending_domain_and_country_verification"
    entity["decision"] = "retain_provisional_listing"
    entity.to_csv(ROOT / "metadata/entity_resolution_log.csv", index=False)

    hotel = read_csv(ROOT / "data_raw/nuitée_commune_final.csv")
    unknown_months = set(hotel.Mois) - set(MONTHS) - {"Total de l'année"}
    assert not unknown_months, unknown_months
    assert not hotel.duplicated(["Commune", "Année", "Mois"]).any()
    monthly = hotel[hotel.Mois.isin(MONTHS)].copy()
    clean = pd.DataFrame({"municipality_name_source": monthly.Commune,
        "year": pd.to_numeric(monthly["Année"]), "month": monthly.Mois.map(MONTHS)})
    clean["date"] = pd.to_datetime(clean[["year", "month"]].assign(day=1)).dt.strftime("%Y-%m-%d")
    for original, target in [("Pays de provenance - total Nuitées", "hotel_overnights"),
        ("Pays de provenance - total Arrivées", "hotel_arrivals"), ("Suisse Nuitées", "domestic_overnights")]:
        clean[target + "_source_token"] = monthly[original]
        clean[target] = numeric_outcome(monthly[original])
    clean["foreign_overnights"] = clean.hotel_overnights - clean.domestic_overnights
    clean["log_overnights"] = np.log1p(clean.hotel_overnights.astype(float))
    clean["source_id"] = "BFS_HOTEL_DATA"
    clean.to_csv(out / "hotel_municipality_month.csv", index=False, na_rep="NA")
    coverage = clean.groupby("municipality_name_source").agg(n_monthly_rows=("date", "size"),
        n_observed_overnights=("hotel_overnights", "count"), first_grid_month=("date", "min"), last_grid_month=("date", "max"))
    observed = clean[clean.hotel_overnights.notna()]
    observed_limits = observed.groupby("municipality_name_source").agg(
        first_observed_month=("date", "min"), last_observed_month=("date", "max"))
    coverage = coverage.join(observed_limits)
    coverage.to_csv(ROOT / "reports/hotel_coverage_by_municipality.csv", na_rep="NA")
    annual = hotel[hotel.Mois == "Total de l'année"].copy()
    annual["annual_nights"] = numeric_outcome(annual["Pays de provenance - total Nuitées"])
    sums = clean.groupby(["municipality_name_source", "year"]).hotel_overnights.agg(["sum", "count"]).reset_index()
    annual["year"] = pd.to_numeric(annual["Année"])
    checks = annual[["Commune", "year", "annual_nights"]].merge(sums, left_on=["Commune", "year"],
        right_on=["municipality_name_source", "year"], validate="one_to_one")
    checks["difference_when_complete"] = (checks.annual_nights - checks["sum"]).where(checks["count"] == 12)
    checks.to_csv(ROOT / "reports/annual_monthly_reconciliation.csv", index=False, na_rep="NA")
    cell_tokens = Counter(v for name in hotel.columns[3:] for v in hotel[name] if not str(v).isdigit())

    cluster_counts = assignments.groupby("cluster_id").size()
    properties = {f["properties"]["cluster_id"]: f["properties"] for f in features}
    assert set(properties) == set(clusters.cluster_id)
    all_fids = [fid for p in properties.values() for fid in p["lift_fids"]]
    mismatches = []
    for row in clusters.to_dict("records"):
        cid = row["cluster_id"]
        p = properties[cid]
        if int(row["station_count"]) != cluster_counts.get(cid, 0) or int(row["lift_count"]) != len(p["lift_fids"]):
            mismatches.append(cid)
    map_path = ROOT / "data_raw/carte_communes_nuitees_croisees_provisoir_avec_stations_gps_bergfex.html"
    lookup = extract_constant(map_path, "matchLookup")
    legacy = pd.DataFrame([{"municipality_name_source": name, **values} for name, values in lookup.items()])
    legacy["evidence_status"] = "legacy_name_overlap_only_no_resort_id_or_exposure_weights"
    legacy["source_id"] = source[map_path.relative_to(ROOT).as_posix()]
    legacy.to_csv(out / "legacy_municipality_name_matches.csv", index=False)
    snapshot = {
        "resort_listings": len(master), "clusters": len(clusters), "assigned_clusters": assignments.cluster_id.nunique(),
        "unnamed_clusters": int((pd.to_numeric(clusters.station_count) == 0).sum()),
        "multi_listing_clusters": int((pd.to_numeric(clusters.station_count) > 1).sum()),
        "assignment_quality": assignments.assignment_quality.value_counts().to_dict(),
        "cluster_quality": clusters.cluster_quality.value_counts().to_dict(),
        "count_mismatches": mismatches, "lift_fid_memberships": len(all_fids), "unique_lift_fids": len(set(all_fids)),
        "duplicate_lift_memberships": [fid for fid, count in Counter(all_fids).items() if count > 1],
        "hotel_raw_rows": len(hotel), "hotel_columns": len(hotel.columns), "municipality_labels": hotel.Commune.nunique(),
        "monthly_grid_rows": len(clean), "annual_rows_excluded": len(annual),
        "observed_monthly_outcomes": len(observed), "observed_municipalities": observed.municipality_name_source.nunique(),
        "observed_date_min": observed.date.min(), "observed_date_max": observed.date.max(),
        "nonnumeric_tokens_all_hotel_measures": dict(cell_tokens),
        "nonnumeric_tokens_monthly_total_nights": monthly.loc[clean.hotel_overnights.isna(), "Pays de provenance - total Nuitées"].value_counts().to_dict(),
        "annual_reconciliation_discrepancies": int((checks.difference_when_complete.notna() & (checks.difference_when_complete != 0)).sum()),
        "legacy_municipality_overlap_count": int((legacy.color == "vert").sum()),
        "all_resort_municipality_fields_empty": bool((stations.commune == "").all()),
        "source_hashes_verified": True,
    }
    (ROOT / "reports/initial_findings.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
