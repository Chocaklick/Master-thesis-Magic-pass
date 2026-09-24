"""Build a conservative dated Top4 history for the Path C competition gate.

Two checksum-cached official Jungfraubahnen releases jointly document the
autumn-2017 launch and the eighth Top4 season in 2024/2025. The four named
regional areas are expanded to explicit supplied listing IDs without fuzzy
matching. A non-link is never interpreted as absence from the historical pass
market, because this stage reconstructs only one product.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
CONFIG_PATH = ROOT / "config" / "competing_pass_historical_top4.json"
ANALYSIS_CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
FEATURE_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
AREA_SEASON_OUTPUT = ROOT / "data_processed" / "competing_pass_historical_area_seasons.csv"
RESORT_SEASON_OUTPUT = ROOT / "data_processed" / "resort_competing_pass_history.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_historical_competing_pass_context.csv"
CANDIDATE_OUTPUT = ROOT / "reports" / "historical_competing_pass_candidate_summary.csv"
DECISION_OUTPUT = ROOT / "data_processed" / "magic_pass_decision_support.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "historical_competing_pass_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "41_HISTORICAL_COMPETING_PASS_CONTEXT.md"

EXPECTED_SEASONS = [
    "2017/2018",
    "2018/2019",
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
]
EXPECTED_AREAS = {
    "Adelboden-Lenk",
    "Gstaad",
    "Jungfrau Ski Region",
    "Meiringen-Hasliberg",
}
INTERPRETATION = (
    "dated_top4_2017_18_to_2024_25_presence_links_for_one_product_"
    "not_complete_historical_pass_market_absence_pre_treatment_or_causal_feature"
)
NO_LINK_STATUS = (
    "not_linked_in_one_reconstructed_top4_roster_not_verified_"
    "absence_from_historical_competing_passes"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def pipe_unique(values) -> str:
    return "|".join(
        sorted({str(value) for value in values if pd.notna(value) and str(value)})
    )


def season_sort_key(season: str) -> int:
    return int(str(season).split("/")[0])


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def exact_metadata(source_id: str) -> dict[str, object]:
    records: list[dict[str, object]] = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if len(records) != 1:
        raise ValueError(f"Expected one cached {source_id} record, found {len(records)}")
    record = records[0]
    raw_path = ROOT / str(record["raw_file"])
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Cached source checksum failure: {source_id}")
    if "jungfrau.ch" not in str(record.get("final_url", "")):
        raise ValueError(f"Unexpected final source host for {source_id}")
    return record


def source_text(record: dict[str, object]) -> str:
    path = ROOT / str(record["raw_file"])
    return BeautifulSoup(path.read_bytes(), "html.parser").get_text(" ", strip=True)


def validate_sources(source_ids: list[str]) -> dict[str, dict[str, object]]:
    expected_ids = {
        "JUNGFRAU_TOP4_2018_19_CONTINUITY",
        "JUNGFRAU_TOP4_2024_25_EIGHTH_SEASON",
    }
    if set(source_ids) != expected_ids:
        raise ValueError("Historical Top4 source registry changed unexpectedly")
    metadata = {source_id: exact_metadata(source_id) for source_id in source_ids}
    texts = {
        source_id: normalize_text(source_text(record))
        for source_id, record in metadata.items()
    }
    required = {
        "JUNGFRAU_TOP4_2018_19_CONTINUITY": [
            "winter20172018",
            "zweitesaison",
            "adelbodenlenk",
            "gstaad",
            "jungfrauskiregion",
            "meiringenhasliberg",
            "unveranderterform",
        ],
        "JUNGFRAU_TOP4_2024_25_EIGHTH_SEASON": [
            "eighthseasonin20242025",
            "adelbodenlenk",
            "gstaad",
            "jungfrauskiregion",
            "meiringenhasliberg",
            "gstaadswithdrawal",
        ],
    }
    for source_id, tokens in required.items():
        missing = [token for token in tokens if token not in texts[source_id]]
        if missing:
            raise ValueError(f"Expected Top4 evidence tokens missing from {source_id}: {missing}")
    return metadata


def validate_config(
    config: dict[str, object], analysis_config: dict[str, object], resorts: pd.DataFrame
) -> dict[str, dict[str, object]]:
    if config["analysis_version"] != analysis_config["analysis_version"]:
        raise ValueError("Historical Top4 and Path C versions differ")
    if config["seasons"] != EXPECTED_SEASONS:
        raise ValueError("Historical Top4 must preserve the eight declared seasons")
    areas = list(config["areas"])
    if len(areas) != 4 or {area["official_area_label"] for area in areas} != EXPECTED_AREAS:
        raise ValueError("Historical Top4 must contain the four official regional areas")
    known_resort_ids = set(resorts["resort_id"])
    linked_ids: list[str] = []
    for area in areas:
        area_ids = list(area["linked_resort_ids"])
        if not area_ids:
            raise ValueError(f"Empty reviewed mapping for {area['official_area_label']}")
        unknown = set(area_ids) - known_resort_ids
        if unknown:
            raise ValueError(f"Unknown historical Top4 listing IDs: {sorted(unknown)}")
        linked_ids.extend(area_ids)
    if len(linked_ids) != len(set(linked_ids)) or len(linked_ids) != 5:
        raise ValueError("Historical Top4 mapping must contain five unique conservative listing links")
    protected = [
        "historical_market_absence_verified",
        "pre_treatment_feature_approved",
        "causal_covariate_approved",
        "recommendation_feature_approved",
        "composite_score_approved",
    ]
    if any(bool(config[field]) for field in protected):
        raise ValueError("A protected historical competing-pass approval became true")
    return validate_sources(list(config["source_ids"]))


def build_area_seasons(config: dict[str, object]) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    source_ids = "|".join(config["source_ids"])
    for season in config["seasons"]:
        for area in config["areas"]:
            records.append(
                {
                    "analysis_version": config["analysis_version"],
                    "competing_pass_id": config["competing_pass_id"],
                    "competing_pass_name": config["competing_pass_name"],
                    "season": season,
                    "official_area_label": area["official_area_label"],
                    "linked_resort_ids": "|".join(area["linked_resort_ids"]),
                    "mapping_basis": area["mapping_basis"],
                    "scope_note": area["scope_note"],
                    "continuity_basis": config["continuity_basis"],
                    "source_ids": source_ids,
                    "historical_market_absence_verified": False,
                    "pre_treatment_feature_approved": False,
                    "causal_covariate_approved": False,
                    "recommendation_feature_approved": False,
                    "composite_score_approved": False,
                    "interpretation": INTERPRETATION,
                }
            )
    area_seasons = pd.DataFrame(records)
    if len(area_seasons) != 32:
        raise ValueError("Expected 32 Top4 area-season rows")
    if area_seasons.duplicated(["competing_pass_id", "season", "official_area_label"]).any():
        raise ValueError("Duplicate historical Top4 area-season row")
    if area_seasons.groupby("season")["official_area_label"].nunique().ne(4).any():
        raise ValueError("Every historical Top4 season must retain four official areas")
    return area_seasons


def build_resort_seasons(
    config: dict[str, object], resorts: pd.DataFrame
) -> pd.DataFrame:
    area_by_resort: dict[str, dict[str, object]] = {}
    for area in config["areas"]:
        for resort_id in area["linked_resort_ids"]:
            area_by_resort[resort_id] = area
    records: list[dict[str, object]] = []
    source_ids = "|".join(config["source_ids"])
    for season in config["seasons"]:
        for resort in resorts.itertuples(index=False):
            area = area_by_resort.get(resort.resort_id)
            linked = area is not None
            records.append(
                {
                    "analysis_version": config["analysis_version"],
                    "resort_id": resort.resort_id,
                    "resort_name_canonical": resort.resort_name_canonical,
                    "cluster_id": resort.cluster_id,
                    "season": season,
                    "competing_pass_id": config["competing_pass_id"] if linked else "",
                    "competing_pass_name": config["competing_pass_name"] if linked else "",
                    "official_area_label": area["official_area_label"] if linked else "",
                    "historical_competing_pass_link_documented": linked,
                    "historical_competing_pass_link_status": (
                        "documented_top4_roster_link" if linked else NO_LINK_STATUS
                    ),
                    "mapping_basis": area["mapping_basis"] if linked else "",
                    "historical_competing_pass_market_absence_verified": False,
                    "historical_competing_pass_feature_approved": False,
                    "pre_treatment_feature_approved": False,
                    "causal_covariate_approved": False,
                    "recommendation_feature_approved": False,
                    "composite_score_approved": False,
                    "source_ids": source_ids,
                    "interpretation": INTERPRETATION,
                }
            )
    history = pd.DataFrame(records)
    if len(history) != len(resorts) * len(EXPECTED_SEASONS):
        raise ValueError("Historical competing-pass listing-season grain changed")
    if history.duplicated(["resort_id", "season"]).any():
        raise ValueError("Duplicate historical competing-pass listing-season row")
    if int(history["historical_competing_pass_link_documented"].sum()) != 40:
        raise ValueError("Expected five conservative listing links in each of eight seasons")
    if history["historical_competing_pass_market_absence_verified"].any():
        raise ValueError("One-product non-links cannot verify historical market absence")
    return history


def build_cluster_context(
    config: dict[str, object], history: pd.DataFrame, resorts: pd.DataFrame, features: pd.DataFrame
) -> pd.DataFrame:
    feature_lookup = features.set_index("cluster_id")
    resort_groups = {cluster_id: group for cluster_id, group in resorts.groupby("cluster_id")}
    rows: list[dict[str, object]] = []
    for cluster_id in features["cluster_id"]:
        listing_group = resort_groups[cluster_id]
        listing_ids = set(listing_group["resort_id"])
        group = history[history["cluster_id"].eq(cluster_id)]
        linked_rows = group[group["historical_competing_pass_link_documented"]]
        linked_ids = set(linked_rows["resort_id"])
        linked_listing_count = len(linked_ids)
        listing_count = len(listing_ids)
        documented_seasons = sorted(
            set(linked_rows["season"]), key=season_sort_key
        )
        if linked_listing_count == 0:
            scope_status = "no_documented_link_in_one_reconstructed_product"
        elif linked_listing_count == listing_count:
            scope_status = "all_listing_points_documented_in_top4"
        else:
            scope_status = "partial_cluster_listing_links_documented_in_top4"
        rows.append(
            {
                "cluster_id": cluster_id,
                "cluster_display_name": feature_lookup.loc[cluster_id, "cluster_display_name"],
                "candidate_for_path_c": feature_lookup.loc[cluster_id, "candidate_for_path_c"],
                "historical_competing_pass_products_reviewed": 1,
                "historical_competing_pass_seasons_reviewed": len(EXPECTED_SEASONS),
                "historical_competing_pass_area_seasons_reviewed": 32,
                "historical_competing_pass_cluster_listing_count": listing_count,
                "historical_competing_pass_linked_listing_count": linked_listing_count,
                "historical_competing_pass_linked_listing_share": (
                    linked_listing_count / listing_count
                ),
                "historical_competing_pass_scope_status": scope_status,
                "historical_competing_pass_linked_resort_ids": pipe_unique(linked_ids),
                "historical_competing_pass_unlinked_resort_ids": pipe_unique(
                    listing_ids - linked_ids
                ),
                "historical_competing_pass_documented_season_count": len(documented_seasons),
                "historical_competing_pass_documented_seasons": "|".join(documented_seasons),
                "historical_competing_pass_first_documented_season": (
                    documented_seasons[0] if documented_seasons else pd.NA
                ),
                "historical_competing_pass_last_documented_season": (
                    documented_seasons[-1] if documented_seasons else pd.NA
                ),
                "historical_competing_pass_ids": (
                    config["competing_pass_id"] if documented_seasons else ""
                ),
                "historical_competing_pass_names": (
                    config["competing_pass_name"] if documented_seasons else ""
                ),
                "historical_competing_pass_area_labels": pipe_unique(
                    linked_rows["official_area_label"]
                ),
                "historical_competing_pass_market_absence_verified": False,
                "historical_competing_pass_context_available": bool(documented_seasons),
                "historical_competing_pass_temporal_scope": (
                    "top4_2017_2018_through_2024_2025"
                ),
                "historical_competing_pass_context_interpretation": INTERPRETATION,
                "historical_competing_pass_feature_approved": False,
                "historical_competing_pass_pre_treatment_approved": False,
                "historical_competing_pass_causal_covariate_approved": False,
                "historical_competing_pass_recommendation_feature_approved": False,
                "historical_competing_pass_composite_score_approved": False,
                "historical_competing_pass_source_ids": "|".join(config["source_ids"]),
            }
        )
    context = pd.DataFrame(rows)
    if len(context) != 162 or not context["cluster_id"].is_unique:
        raise ValueError("Historical competing-pass context must preserve 162 clusters")
    linked_clusters = context["historical_competing_pass_context_available"]
    if int(linked_clusters.sum()) != 4:
        raise ValueError("Expected four lift clusters with documented Top4 links")
    if not context["historical_competing_pass_linked_listing_share"].between(0, 1).all():
        raise ValueError("Invalid historical competing-pass listing share")
    protected = [
        "historical_competing_pass_market_absence_verified",
        "historical_competing_pass_feature_approved",
        "historical_competing_pass_pre_treatment_approved",
        "historical_competing_pass_causal_covariate_approved",
        "historical_competing_pass_recommendation_feature_approved",
        "historical_competing_pass_composite_score_approved",
    ]
    if context[protected].any().any():
        raise ValueError("A protected historical competing-pass cluster flag became true")
    return context


def enrich_decision_support(context: pd.DataFrame) -> None:
    decision = pd.read_csv(DECISION_OUTPUT)
    context_columns = [
        column
        for column in context.columns
        if column not in {"cluster_id", "cluster_display_name", "candidate_for_path_c"}
    ]
    decision = decision.drop(
        columns=[column for column in context_columns if column in decision.columns]
    ).merge(
        context[["cluster_id", *context_columns]],
        on="cluster_id",
        how="left",
        validate="one_to_one",
    )
    guarded_values = [
        "accessibility_score",
        "predicted_uplift_pct",
        "uplift_lower_pct",
        "uplift_upper_pct",
        "composite_opportunity_need_score",
    ]
    populated = [column for column in guarded_values if decision[column].notna().any()]
    if populated:
        raise ValueError(f"Unapproved decision fields became populated: {populated}")
    protected_flags = [
        "historical_competing_pass_market_absence_verified",
        "historical_competing_pass_feature_approved",
        "historical_competing_pass_pre_treatment_approved",
        "historical_competing_pass_causal_covariate_approved",
        "historical_competing_pass_recommendation_feature_approved",
        "historical_competing_pass_composite_score_approved",
    ]
    if any(as_bool(decision[column]).any() for column in protected_flags):
        raise ValueError("Historical competing-pass evidence became an approved decision feature")
    DECISION_OUTPUT.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def write_report(summary: dict[str, object]) -> None:
    report = f"""# Historical competing-pass context: Top4

## Evidence recovered

Two checksum-cached official Jungfraubahnen releases provide a bounded historical reconstruction. The September 2018 release states that Top4 was launched in autumn 2017, names Adelboden-Lenk, Gstaad, Jungfrau Ski Region and Meiringen-Hasliberg, and describes 2018/2019 as the unchanged second season. The December 2024 release names the same four regions, describes 2024/2025 as the eighth season and records Gstaad's announced withdrawal after that winter. Together these statements support **eight consecutive seasons from 2017/2018 through 2024/2025** for the four-area Top4 product.

The output contains **{summary['area_season_rows']} area-season rows** and **{summary['resort_season_rows']} supplied-listing-season rows**. Five conservative supplied listing links are recorded in every season, producing **{summary['documented_listing_season_links']} documented listing-season links** across **{summary['clusters_with_documented_link']} lift clusters**.

## Conservative entity scope

Only exact or conservative supplied-directory links are used. Adelboden and Lenk are linked, but Engstligenalp and Elsigenalp-Metschalp are not inferred from the broad historical regional label. Grindelwald-Wengen is linked to Jungfrau Ski Region, while Schilthorn is deliberately left unlinked because component eligibility changed during the Top4 period and the two continuity releases do not establish its season-specific scope. Gstaad and Meiringen-Hasliberg use exact supplied listing links.

Among the **{summary['path_c_candidates']}** apparent Path C candidates, **{summary['path_c_candidates_with_documented_link']}** clusters have a documented Top4 link and both are partial mixed-listing clusters. The remaining {summary['path_c_candidates_without_documented_link']} candidate non-links mean only that no link was found in this one reconstructed product.

## Decision limit

This milestone reconstructs **one competing pass**, not the full Swiss multi-resort-pass market. The evidence is dated, but it is not uniformly pre-treatment for the Magic Pass anchors, does not measure pass intensity or prices, and does not verify absence from Meilenweiss, Schneepass, SnowPass, TopCard, regional alliances or reciprocal offers. Historical market-absence, pre-treatment, causal, recommendation and composite-score approvals therefore remain false. The result is qualified partial historical context, not a ranking input.

## Outputs

- `config/competing_pass_historical_top4.json`
- `data_processed/competing_pass_historical_area_seasons.csv`
- `data_processed/resort_competing_pass_history.csv`
- `data_processed/path_c_cluster_historical_competing_pass_context.csv`
- `reports/historical_competing_pass_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified historical fields appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    analysis_config = json.loads(ANALYSIS_CONFIG_PATH.read_text(encoding="utf-8"))
    resorts = pd.read_csv(RESORT_PATH, dtype="string")
    features = pd.read_csv(FEATURE_PATH, dtype="string")
    if len(resorts) != 271 or resorts["resort_id"].duplicated().any():
        raise ValueError("Unexpected resort master grain")
    if len(features) != 162 or features["cluster_id"].duplicated().any():
        raise ValueError("Unexpected Path C cluster feature grain")

    metadata = validate_config(config, analysis_config, resorts)
    area_seasons = build_area_seasons(config)
    area_seasons.to_csv(AREA_SEASON_OUTPUT, index=False, lineterminator="\n")
    history = build_resort_seasons(config, resorts)
    history.to_csv(RESORT_SEASON_OUTPUT, index=False, lineterminator="\n")
    context = build_cluster_context(config, history, resorts, features)
    context.to_csv(CLUSTER_OUTPUT, index=False, lineterminator="\n")
    enrich_decision_support(context)

    candidates = context[as_bool(context["candidate_for_path_c"])].copy()
    if len(candidates) != 104:
        raise ValueError("Expected 104 Path C candidate clusters")
    candidate_columns = [
        "cluster_id",
        "cluster_display_name",
        "historical_competing_pass_scope_status",
        "historical_competing_pass_linked_listing_count",
        "historical_competing_pass_linked_listing_share",
        "historical_competing_pass_linked_resort_ids",
        "historical_competing_pass_unlinked_resort_ids",
        "historical_competing_pass_documented_season_count",
        "historical_competing_pass_first_documented_season",
        "historical_competing_pass_last_documented_season",
        "historical_competing_pass_names",
        "historical_competing_pass_area_labels",
        "historical_competing_pass_market_absence_verified",
        "historical_competing_pass_feature_approved",
    ]
    candidates.sort_values(
        ["historical_competing_pass_context_available", "cluster_id"],
        ascending=[False, True],
    )[candidate_columns].to_csv(CANDIDATE_OUTPUT, index=False, lineterminator="\n")

    linked_candidates = int(candidates["historical_competing_pass_context_available"].sum())
    summary = {
        "analysis_version": config["analysis_version"],
        "reviewed_historical_products": 1,
        "reviewed_seasons": len(EXPECTED_SEASONS),
        "season_start": EXPECTED_SEASONS[0],
        "season_end": EXPECTED_SEASONS[-1],
        "official_areas_per_season": 4,
        "area_season_rows": len(area_seasons),
        "resort_season_rows": len(history),
        "documented_listing_season_links": int(
            history["historical_competing_pass_link_documented"].sum()
        ),
        "unique_supplied_listings_with_documented_link": int(
            history.loc[
                history["historical_competing_pass_link_documented"], "resort_id"
            ].nunique()
        ),
        "clusters_with_documented_link": int(
            context["historical_competing_pass_context_available"].sum()
        ),
        "path_c_candidates": len(candidates),
        "path_c_candidates_with_documented_link": linked_candidates,
        "path_c_candidates_without_documented_link": len(candidates) - linked_candidates,
        "path_c_candidate_partial_cluster_links": int(
            candidates["historical_competing_pass_scope_status"].eq(
                "partial_cluster_listing_links_documented_in_top4"
            ).sum()
        ),
        "market_absence_verified_rows": int(
            context["historical_competing_pass_market_absence_verified"].sum()
        ),
        "approved_features": int(
            context["historical_competing_pass_feature_approved"].sum()
        ),
        "source_sha256": {
            source_id: record["sha256"] for source_id, record in metadata.items()
        },
        "interpretation": INTERPRETATION,
    }
    if summary["path_c_candidates_with_documented_link"] != 2:
        raise ValueError("Expected two Path C candidates with conservative Top4 links")
    if summary["path_c_candidate_partial_cluster_links"] != 2:
        raise ValueError("Expected both candidate Top4 links to be partial clusters")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
