"""Build a conservative current competing-pass roster context for Path C.

The official rosters are validated against checksum-cached source pages. Explicit,
versioned listing links are then expanded without fuzzy matching. A missing link
means only that the supplied listing was not linked in the three reviewed rosters;
it never proves absence from every competing pass or from an unreviewed component.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
ROSTER_PATH = ROOT / "config" / "competing_pass_roster_2026_27.csv"
CONFIG_PATH = ROOT / "config" / "path_c_analysis.json"
RESORT_PATH = ROOT / "data_processed" / "resort_master.csv"
FEATURE_PATH = ROOT / "data_processed" / "path_c_resort_cluster_features.csv"
LISTING_OUTPUT = ROOT / "data_processed" / "resort_competing_pass_context.csv"
CLUSTER_OUTPUT = ROOT / "data_processed" / "path_c_cluster_competing_pass_context.csv"
CANDIDATE_OUTPUT = ROOT / "reports" / "competing_pass_candidate_summary.csv"
DECISION_OUTPUT = ROOT / "data_processed" / "magic_pass_decision_support.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "competing_pass_context_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "31_COMPETING_PASS_CONTEXT.md"

SOURCE_IDS = [
    "ALPSPASS_2026_27_ROSTER",
    "ALPSPASS_2026_27_GTC",
    "MEILENWEISS_CURRENT_ROSTER",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2026_27_ROSTER",
]
EXPECTED_AREA_COUNTS = {
    "alpspass": 11,
    "meilenweiss": 17,
    "schneepass_zentralschweiz": 15,
}
EXPECTED_BENEFIT_COUNTS = {
    "unlimited_core_region": 4,
    "three_free_ski_days_partner_region": 7,
    "included_region_current_annual_pass": 17,
    "included_region_winter_season_pass": 15,
}
INTERPRETATION = (
    "current_official_reviewed_roster_links_not_historical_competition_"
    "intensity_market_absence_or_causal_feature"
)
NO_LINK_STATUS = (
    "not_linked_in_three_reviewed_rosters_not_verified_no_competing_pass"
)
TEMPORAL_SCOPE = (
    "official_2026_27_alpspass_and_schneepass_plus_"
    "current_retrieval_snapshot_meilenweiss"
)


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("false").str.lower().eq("true")


def pipe_unique(values) -> str:
    return "|".join(sorted({str(value) for value in values if pd.notna(value) and str(value)}))


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def exact_metadata(source_id: str) -> dict:
    records = []
    for path in EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("source_id") == source_id:
            records.append(record)
    if len(records) != 1:
        raise ValueError(f"Expected one cached {source_id} record, found {len(records)}")
    record = records[0]
    raw_path = ROOT / record["raw_file"]
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Cached source checksum failure: {source_id}")
    return record


def source_text(record: dict) -> str:
    path = ROOT / record["raw_file"]
    if path.suffix.lower() == ".pdf":
        return " ".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return BeautifulSoup(path.read_bytes(), "html.parser").get_text(" ", strip=True)


def validate_sources(roster: pd.DataFrame) -> dict[str, dict]:
    metadata = {source_id: exact_metadata(source_id) for source_id in SOURCE_IDS}
    texts = {source_id: normalize_text(source_text(record)) for source_id, record in metadata.items()}

    for row in roster.itertuples(index=False):
        roster_source = str(row.source_ids).split("|")[0]
        token = normalize_text(row.official_area_label)
        if token not in texts[roster_source]:
            raise ValueError(
                f"Official area label {row.official_area_label!r} not found in {roster_source}"
            )

    alps = texts["ALPSPASS_2026_27_ROSTER"]
    gtc = texts["ALPSPASS_2026_27_GTC"]
    meilenweiss = texts["MEILENWEISS_CURRENT_ROSTER"]
    schneepass = texts["SCHNEEPASS_ZENTRALSCHWEIZ_2026_27_ROSTER"]
    required_tokens = {
        "ALPSPASS_2026_27_ROSTER": ["202627", "quatre", "sept", "3journeesdeskigratuites"],
        "ALPSPASS_2026_27_GTC": ["202608", "elsigenalpbahnen", "brunnibahnenengelberg"],
        "MEILENWEISS_CURRENT_ROSTER": ["17verschiedene", "amden", "3talerpass"],
        "SCHNEEPASS_ZENTRALSCHWEIZ_2026_27_ROSTER": ["20262027", "15skiregionen", "neusell"],
    }
    for source_id, tokens in required_tokens.items():
        missing = [token for token in tokens if token not in texts[source_id]]
        if missing:
            raise ValueError(f"Expected source tokens missing from {source_id}: {missing}")
    if "3journeesdeskigratuites" not in alps:
        raise ValueError("AlpsPass partner three-day benefit wording was not found")
    if "jahreskarte" not in meilenweiss:
        raise ValueError("Meilenweiss annual-pass wording was not found")
    if "winterabosaison" not in schneepass:
        raise ValueError("Schneepass winter-season wording was not found")
    if "adelbodenlenkskiregion" not in gtc or "jungfrauskiregion" not in gtc:
        raise ValueError("AlpsPass GTC core-region scope wording was not found")
    return metadata


def load_roster() -> tuple[pd.DataFrame, dict[str, dict]]:
    roster = pd.read_csv(ROSTER_PATH, dtype="string", keep_default_na=False)
    required = {
        "competing_pass_id",
        "competing_pass_name",
        "roster_version",
        "benefit_tier",
        "official_area_label",
        "source_ids",
        "linked_resort_ids",
        "mapping_status",
        "mapping_basis",
        "scope_note",
    }
    if set(roster.columns) != required:
        raise ValueError(f"Unexpected competing-pass roster schema: {roster.columns.tolist()}")
    if len(roster) != 43 or roster[["competing_pass_id", "official_area_label"]].duplicated().any():
        raise ValueError("Competing-pass roster must contain 43 unique pass-area rows")
    if roster["competing_pass_id"].value_counts().to_dict() != EXPECTED_AREA_COUNTS:
        raise ValueError("Unexpected official competing-pass area counts")
    if roster["benefit_tier"].value_counts().to_dict() != EXPECTED_BENEFIT_COUNTS:
        raise ValueError("Unexpected competing-pass benefit-tier counts")
    linked = roster["linked_resort_ids"].ne("")
    if not roster.loc[linked, "mapping_status"].eq("reviewed_listing_links").all():
        raise ValueError("Every non-empty mapping must be explicitly reviewed")
    if not roster.loc[~linked, "mapping_status"].eq("no_supplied_directory_link").all():
        raise ValueError("Every empty mapping must retain a no-link status")
    metadata = validate_sources(roster)
    return roster, metadata


def expand_links(roster: pd.DataFrame, resorts: pd.DataFrame) -> pd.DataFrame:
    known = set(resorts["resort_id"])
    records = []
    for row in roster.itertuples(index=False):
        linked_ids = [value for value in str(row.linked_resort_ids).split("|") if value]
        unknown = set(linked_ids) - known
        if unknown:
            raise ValueError(f"Unknown linked resort IDs for {row.official_area_label}: {sorted(unknown)}")
        for resort_id in linked_ids:
            records.append(
                {
                    "resort_id": resort_id,
                    "competing_pass_id": row.competing_pass_id,
                    "competing_pass_name": row.competing_pass_name,
                    "roster_version": row.roster_version,
                    "benefit_tier": row.benefit_tier,
                    "official_area_label": row.official_area_label,
                    "source_ids": row.source_ids,
                    "mapping_basis": row.mapping_basis,
                    "scope_note": row.scope_note,
                }
            )
    links = pd.DataFrame(records)
    if links.duplicated(["resort_id", "competing_pass_id"]).any():
        raise ValueError("A supplied listing was linked to multiple areas within one pass")
    return links


def build_listing_context(roster: pd.DataFrame, resorts: pd.DataFrame) -> pd.DataFrame:
    links = expand_links(roster, resorts)
    grouped = {resort_id: group for resort_id, group in links.groupby("resort_id", sort=False)}
    rows = []
    for resort in resorts.itertuples(index=False):
        group = grouped.get(resort.resort_id)
        linked = group is not None
        if linked:
            pass_ids = pipe_unique(group["competing_pass_id"])
            pass_names = pipe_unique(group["competing_pass_name"])
            versions = pipe_unique(group["roster_version"])
            tiers = pipe_unique(group["benefit_tier"])
            area_links = pipe_unique(
                f"{row.competing_pass_id}:{row.official_area_label}"
                for row in group.itertuples(index=False)
            )
            mapping_bases = pipe_unique(group["mapping_basis"])
            link_sources = pipe_unique(
                source_id
                for value in group["source_ids"]
                for source_id in str(value).split("|")
            )
        else:
            pass_ids = pass_names = versions = tiers = area_links = mapping_bases = ""
            link_sources = ""
        rows.append(
            {
                "resort_id": resort.resort_id,
                "resort_name_canonical": resort.resort_name_canonical,
                "cluster_id": resort.cluster_id,
                "reviewed_competing_pass_roster_count": 3,
                "reviewed_competing_pass_area_count": len(roster),
                "competing_pass_linked": linked,
                "competing_pass_link_count": 0 if group is None else len(group),
                "competing_pass_ids": pass_ids,
                "competing_pass_names": pass_names,
                "competing_pass_roster_versions": versions,
                "competing_pass_benefit_tiers": tiers,
                "competing_pass_area_links": area_links,
                "competing_pass_mapping_bases": mapping_bases,
                "competing_pass_limited_partner_benefit_linked": bool(
                    linked
                    and group["benefit_tier"].eq("three_free_ski_days_partner_region").any()
                ),
                "competing_pass_core_or_included_region_linked": bool(
                    linked
                    and group["benefit_tier"].ne("three_free_ski_days_partner_region").any()
                ),
                "competing_pass_roster_link_status": (
                    "linked_to_one_or_more_reviewed_official_roster_areas"
                    if linked
                    else NO_LINK_STATUS
                ),
                "competing_pass_market_absence_verified": False,
                "competing_pass_context_temporal_scope": TEMPORAL_SCOPE,
                "competing_pass_context_interpretation": INTERPRETATION,
                "competing_pass_feature_approved": False,
                "competing_pass_link_source_ids": link_sources,
                "competing_pass_review_source_ids": pipe_unique(SOURCE_IDS),
            }
        )
    context = pd.DataFrame(rows)
    if len(context) != 271 or not context["resort_id"].is_unique:
        raise ValueError("Listing context must preserve all 271 supplied resort rows")
    if context["competing_pass_market_absence_verified"].any():
        raise ValueError("Roster non-links cannot verify market absence")
    if context["competing_pass_feature_approved"].any():
        raise ValueError("Current competing-pass context cannot be causally approved")
    return context


def build_cluster_context(listings: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    feature_lookup = features.set_index("cluster_id")
    rows = []
    for cluster_id, group in listings.groupby("cluster_id", sort=False):
        linked = group["competing_pass_linked"]
        linked_count = int(linked.sum())
        listing_count = len(group)
        if linked_count == 0:
            status = "no_link_in_reviewed_rosters"
        elif linked_count == listing_count:
            status = "all_listing_points_linked_to_one_or_more_reviewed_rosters"
        else:
            status = "partial_cluster_listing_links"
        pass_ids = pipe_unique(
            token for value in group.loc[linked, "competing_pass_ids"] for token in str(value).split("|")
        )
        pass_names = pipe_unique(
            token for value in group.loc[linked, "competing_pass_names"] for token in str(value).split("|")
        )
        tiers = pipe_unique(
            token for value in group.loc[linked, "competing_pass_benefit_tiers"] for token in str(value).split("|")
        )
        areas = pipe_unique(
            token for value in group.loc[linked, "competing_pass_area_links"] for token in str(value).split("|")
        )
        rows.append(
            {
                "cluster_id": cluster_id,
                "cluster_display_name": feature_lookup.loc[cluster_id, "cluster_display_name"],
                "candidate_for_path_c": feature_lookup.loc[cluster_id, "candidate_for_path_c"],
                "cluster_competing_pass_listing_count": listing_count,
                "cluster_listings_linked_to_reviewed_competing_pass": linked_count,
                "cluster_competing_pass_linked_listing_share": linked_count / listing_count,
                "cluster_competing_pass_scope_status": status,
                "cluster_competing_pass_linked_resort_ids": pipe_unique(group.loc[linked, "resort_id"]),
                "cluster_competing_pass_unlinked_resort_ids": pipe_unique(group.loc[~linked, "resort_id"]),
                "cluster_has_reviewed_competing_pass_link": linked_count > 0,
                "cluster_competing_pass_count": len([value for value in pass_ids.split("|") if value]),
                "cluster_competing_pass_ids": pass_ids,
                "cluster_competing_pass_names": pass_names,
                "cluster_competing_pass_area_links": areas,
                "cluster_competing_pass_benefit_tiers": tiers,
                "cluster_limited_partner_benefit_listing_count": int(
                    group["competing_pass_limited_partner_benefit_linked"].sum()
                ),
                "cluster_core_or_included_region_listing_count": int(
                    group["competing_pass_core_or_included_region_linked"].sum()
                ),
                "reviewed_competing_pass_roster_count": 3,
                "reviewed_competing_pass_area_count": 43,
                "competing_pass_market_absence_verified": False,
                "competing_pass_context_temporal_scope": TEMPORAL_SCOPE,
                "competing_pass_context_interpretation": INTERPRETATION,
                "competing_pass_feature_approved": False,
                "competing_pass_review_source_ids": pipe_unique(SOURCE_IDS),
            }
        )
    context = pd.DataFrame(rows).merge(
        features[["cluster_id"]], on="cluster_id", how="right", validate="one_to_one"
    )
    if len(context) != 162 or not context["cluster_id"].is_unique:
        raise ValueError("Cluster context must preserve all 162 linked lift clusters")
    if int(context["cluster_competing_pass_listing_count"].sum()) != len(listings):
        raise ValueError("Cluster aggregation lost supplied resort listings")
    if not context["cluster_competing_pass_linked_listing_share"].between(0, 1).all():
        raise ValueError("Invalid competing-pass linked listing share")
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
    guarded = [
        "accessibility_score",
        "predicted_uplift_pct",
        "uplift_lower_pct",
        "uplift_upper_pct",
        "composite_opportunity_need_score",
    ]
    populated = [column for column in guarded if decision[column].notna().any()]
    if populated:
        raise ValueError(f"Unapproved decision fields became populated: {populated}")
    if as_bool(decision["competing_pass_feature_approved"]).any():
        raise ValueError("Competing-pass context was unexpectedly approved")
    DECISION_OUTPUT.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    roster, metadata = load_roster()
    resorts = pd.read_csv(RESORT_PATH, dtype="string")
    features = pd.read_csv(FEATURE_PATH, dtype="string")
    if len(resorts) != 271 or resorts["resort_id"].duplicated().any():
        raise ValueError("Unexpected resort master grain")
    if len(features) != 162 or features["cluster_id"].duplicated().any():
        raise ValueError("Unexpected Path C cluster feature grain")

    listings = build_listing_context(roster, resorts)
    listings.to_csv(LISTING_OUTPUT, index=False, lineterminator="\n")
    clusters = build_cluster_context(listings, features)
    clusters.to_csv(CLUSTER_OUTPUT, index=False, lineterminator="\n")
    enrich_decision_support(clusters)

    candidates = clusters[as_bool(clusters["candidate_for_path_c"])].copy()
    candidate_columns = [
        "cluster_id",
        "cluster_display_name",
        "cluster_competing_pass_scope_status",
        "cluster_listings_linked_to_reviewed_competing_pass",
        "cluster_competing_pass_linked_listing_share",
        "cluster_competing_pass_count",
        "cluster_competing_pass_names",
        "cluster_competing_pass_area_links",
        "cluster_competing_pass_benefit_tiers",
        "cluster_competing_pass_linked_resort_ids",
        "cluster_competing_pass_unlinked_resort_ids",
        "competing_pass_market_absence_verified",
        "competing_pass_feature_approved",
    ]
    candidates.sort_values(
        ["cluster_has_reviewed_competing_pass_link", "cluster_competing_pass_count", "cluster_id"],
        ascending=[False, False, True],
    )[candidate_columns].to_csv(CANDIDATE_OUTPUT, index=False, lineterminator="\n")

    linked_listings = int(listings["competing_pass_linked"].sum())
    linked_clusters = int(clusters["cluster_has_reviewed_competing_pass_link"].sum())
    linked_candidates = int(candidates["cluster_has_reviewed_competing_pass_link"].sum())
    summary = {
        "analysis_version": config["analysis_version"],
        "reviewed_passes": 3,
        "official_area_rows": len(roster),
        "official_area_rows_by_pass": EXPECTED_AREA_COUNTS,
        "benefit_tier_rows": EXPECTED_BENEFIT_COUNTS,
        "source_sha256": {
            source_id: record["sha256"] for source_id, record in metadata.items()
        },
        "resort_listings": len(listings),
        "resort_listings_linked": linked_listings,
        "resort_listings_not_linked": len(listings) - linked_listings,
        "path_c_clusters": len(clusters),
        "path_c_clusters_with_link": linked_clusters,
        "path_c_clusters_partial": int(
            clusters["cluster_competing_pass_scope_status"].eq("partial_cluster_listing_links").sum()
        ),
        "path_c_candidates": len(candidates),
        "path_c_candidates_with_link": linked_candidates,
        "path_c_candidates_without_link": len(candidates) - linked_candidates,
        "candidate_scope_status_counts": {
            str(key): int(value)
            for key, value in candidates["cluster_competing_pass_scope_status"].value_counts().items()
        },
        "market_absence_verified_rows": int(
            listings["competing_pass_market_absence_verified"].sum()
        ),
        "approved_features": int(clusters["competing_pass_feature_approved"].sum()),
        "temporal_scope": TEMPORAL_SCOPE,
        "interpretation": INTERPRETATION,
    }
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = f"""# Qualified competing-pass roster context

## Scope

This review uses checksum-cached official material for three products: **AlpsPass 2026/2027**, **Meilenweiss at the retrieval-date snapshot**, and **Schneepass Zentralschweiz 2026/2027**. The versioned register contains **{len(roster)} official pass-area rows**: 11 AlpsPass regions, 17 Meilenweiss regions and 15 Schneepass regions.

AlpsPass is deliberately split into **four unlimited core regions** and **seven partner regions providing three free ski days**. Meilenweiss is recorded as a current annual-pass roster without inventing a season label. Schneepass is recorded as a winter-2026/2027 included-region roster. These benefit tiers are never flattened into a single equivalent treatment intensity.

## Conservative entity linking

The official-area register contains explicit reviewed links to supplied resort IDs. It does not fuzzy-match names at runtime. This preserves mixed clusters: for example, Arosa Lenzerheide can be linked without automatically assigning Chur-Brambrüesch, and Pizol can be linked without automatically assigning Mastrils or Tristeli.

- supplied resort listings linked to at least one reviewed roster: **{linked_listings} / {len(listings)}**
- lift clusters containing at least one linked listing: **{linked_clusters} / {len(clusters)}**
- clusters with only partial listing-level links: **{summary['path_c_clusters_partial']}**
- apparent Path C candidates containing at least one linked listing: **{linked_candidates} / {len(candidates)}**
- listing or cluster rows treated as verified absence from the competing-pass market: **0**
- competing-pass fields approved as causal/pre-treatment model features: **0**

## Interpretation limit

A non-link means only **not linked in these three reviewed official rosters**. It does not prove that a destination has no competing pass, no regional alliance, no reciprocal benefit, or no unenumerated component coverage. Two products are season-specific 2026/2027 snapshots and Meilenweiss is a retrieval-date snapshot; they do not reconstruct historical competition around Magic Pass entry dates. The separate five-product reconstruction in `reports/41_HISTORICAL_COMPETING_PASS_CONTEXT.md` supplies dated positive-presence evidence for Top4, Meilenweiss, Schneepass Zentralschweiz, TopCard and SnowPass Graubünden, but its windows remain partial and it does not change the interpretation of current non-links. The fields are therefore descriptive current business context only. `competing_pass_market_absence_verified` and `competing_pass_feature_approved` remain false for every row, and no uplift or composite score is populated.

## Outputs

- `config/competing_pass_roster_2026_27.csv`
- `data_processed/resort_competing_pass_context.csv`
- `data_processed/path_c_cluster_competing_pass_context.csv`
- `reports/competing_pass_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified roster context appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
