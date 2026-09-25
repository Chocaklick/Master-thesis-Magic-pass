"""Build conservative dated multi-resort-pass context for Path C.

Only positive, checksum-pinned evidence is linked to supplied resort IDs. The
output never interprets a non-link as historical market absence. Product-level
summer inclusion is kept separate from area-specific summer access, and
unlimited core access is kept separate from limited partner benefits.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
from bs4 import BeautifulSoup
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"
TOP4_CONFIG_PATH = ROOT / "config" / "competing_pass_historical_top4.json"
MEILENWEISS_CONFIG_PATH = (
    ROOT / "config" / "competing_pass_historical_meilenweiss.json"
)
SCHNEEPASS_CONFIG_PATH = (
    ROOT / "config" / "competing_pass_historical_schneepass_zentralschweiz.json"
)
TOPCARD_CONFIG_PATH = ROOT / "config" / "competing_pass_historical_topcard.json"
SNOWPASS_GRAUBUENDEN_CONFIG_PATH = (
    ROOT / "config" / "competing_pass_historical_snowpass_graubuenden.json"
)
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

EXPECTED_TOP4_SEASONS = [
    "2017/2018",
    "2018/2019",
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
]
EXPECTED_TOP4_AREAS = {
    "Adelboden-Lenk",
    "Gstaad",
    "Jungfrau Ski Region",
    "Meiringen-Hasliberg",
}
EXPECTED_MEILENWEISS_SEASONS = ["2019/2020", "2020/2021", "2021/2022"]
EXPECTED_MEILENWEISS_AREA_COUNTS = {
    "2019/2020": 12,
    "2020/2021": 1,
    "2021/2022": 16,
}
EXPECTED_SCHNEEPASS_SEASONS = [
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
]
EXPECTED_SCHNEEPASS_AREA_COUNTS = {
    "2021/2022": 1,
    "2022/2023": 15,
    "2023/2024": 15,
    "2024/2025": 15,
}
EXPECTED_TOPCARD_SEASONS = ["2017/2018", "2018/2019", "2019/2020"]
EXPECTED_TOPCARD_AREA_COUNTS = {
    "2017/2018": 3,
    "2018/2019": 4,
    "2019/2020": 4,
}
EXPECTED_SNOWPASS_GRAUBUENDEN_SEASONS = [
    "2017/2018",
    "2018/2019",
    "2019/2020",
]
EXPECTED_SNOWPASS_GRAUBUENDEN_AREA_COUNTS = {
    "2017/2018": 1,
    "2018/2019": 19,
    "2019/2020": 17,
}
EXPECTED_SOURCE_HOSTS = {
    "JUNGFRAU_TOP4_2018_19_CONTINUITY": "jungfrau.ch",
    "JUNGFRAU_TOP4_2024_25_EIGHTH_SEASON": "jungfrau.ch",
    "ATZMAENNIG_MEILENWEISS_2019_20_ORDER_FORM": "atzmaennig.ch",
    "ATZMAENNIG_WINTER_BROCHURE_2020_21": "atzmaennig.ch",
    "MALBUN_MEILENWEISS_2021_22_WINTER_BROCHURE": "bergbahnen.li",
    "PIZOL_ANNUAL_REPORT_2018_19": "pizol.com",
    "BRUNNI_SCHNEEPASS_ZENTRALSCHWEIZ_2021_22_BROCHURE": "brunni.ch",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2022_23_ARCHIVED_ROSTER": "web.archive.org",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2022_23_ARCHIVED_SUMMER_ROSTER": "web.archive.org",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2023_24_MEDIA_KIT": "schneepasszentralschweiz.ch",
    "SCHNEEPASS_ZENTRALSCHWEIZ_2024_25_MEDIA_KIT": "schneepasszentralschweiz.ch",
    "SAMNAUN_TOPCARD_SNOWPASS_TARIFFS_2017_18": "samnaun-engadin.ch",
    "BBGR_ANNUAL_2017_18": "bbgr.ch",
    "BBGR_ANNUAL_2018_19": "bbgr.ch",
    "BBGR_ANNUAL_2019_20": "bbgr.ch",
    "SBS_PRICING_STUDY_2020_TOPCARD": "bbgr.ch",
    "GRAUBUENDEN_SNOWPASS_2018_19_ARCHIVED_PAGE": "web.archive.org",
    "GRAUBUENDEN_SNOWPASS_2019_20_ARCHIVED_PAGE": "web.archive.org",
    "CORVATSCH_DIAVOLEZZA_ANNUAL_2018_19": "corvatsch-diavolezza.ch",
}
INTERPRETATION = (
    "dated_top4_2017_18_to_2024_25_meilenweiss_2019_20_to_2021_22_and_"
    "schneepass_zentralschweiz_2021_22_to_2024_25_plus_topcard_"
    "2017_18_to_2019_20_tiered_plus_snowpass_graubuenden_2017_18_to_"
    "2019_20_conservative_"
    "positive_presence_evidence_not_complete_historical_pass_market_absence_"
    "pre_treatment_or_causal_feature"
)
NO_LINK_STATUS = (
    "not_linked_in_reviewed_product_season_positive_evidence_not_verified_"
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


def exact_metadata(source_id: str, expected_sha256: str) -> dict[str, object]:
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
    observed_sha256 = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    if observed_sha256 != record["sha256"] or observed_sha256 != expected_sha256:
        raise RuntimeError(f"Cached source checksum failure: {source_id}")
    host = urlsplit(str(record.get("final_url", ""))).hostname or ""
    if not host.endswith(EXPECTED_SOURCE_HOSTS[source_id]):
        raise ValueError(f"Unexpected final source host for {source_id}: {host}")
    return record


def source_text(record: dict[str, object]) -> str:
    path = ROOT / str(record["raw_file"])
    if path.suffix.lower() == ".pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
    return BeautifulSoup(path.read_bytes(), "html.parser").get_text(" ", strip=True)


def validate_sources(
    top4_config: dict[str, object],
    meilenweiss_config: dict[str, object],
    schneepass_config: dict[str, object],
    topcard_config: dict[str, object],
    snowpass_graubuenden_config: dict[str, object],
) -> dict[str, dict[str, object]]:
    expected_ids = set(EXPECTED_SOURCE_HOSTS)
    sha_by_id = {
        **top4_config["source_sha256_by_id"],
        **meilenweiss_config["source_sha256_by_id"],
        **schneepass_config["source_sha256_by_id"],
        **topcard_config["source_sha256_by_id"],
        **snowpass_graubuenden_config["source_sha256_by_id"],
    }
    if set(sha_by_id) != expected_ids:
        raise ValueError("Historical competing-pass source registry changed unexpectedly")
    metadata = {
        source_id: exact_metadata(source_id, str(sha_by_id[source_id]))
        for source_id in sorted(expected_ids)
    }
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
        "ATZMAENNIG_MEILENWEISS_2019_20_ORDER_FORM": [
            "winter201920",
            "jahreskarte201920inklsommersaison2020",
            "saisonkarte201920",
            "atzmannig",
            "braunwald",
            "flumserberg",
            "malbun",
            "mythenregion",
            "pizol",
            "stoos",
            "wildhaus",
            "krummenauwolzenalp",
            "sattelhochstuckli",
            "gruschdanusa",
        ],
        "ATZMAENNIG_WINTER_BROCHURE_2020_21": [
            "meilenweissabo",
            "freiefahrtin19revieren",
            "jahreskarteinklusivesommersaison2021",
        ],
        "MALBUN_MEILENWEISS_2021_22_WINTER_BROCHURE": [
            "flumserberg",
            "wildhaus",
            "pizol",
            "elm",
            "mythenregion",
            "braunwald",
            "stoos",
            "ebenalphorn",
            "sattelhochstuckli",
            "amden",
            "atzmannig",
            "wolzenalp",
            "gruschdanusa",
            "ebnatkappeltanzboden",
            "hoherkasten",
            "malbun",
        ],
        "BRUNNI_SCHNEEPASS_ZENTRALSCHWEIZ_2021_22_BROCHURE": [
            "winter20212022",
            "schneepasszentralschweiz",
            "14skigebieten",
            "schneepasspluszentralschweiz",
            "unlimitierteswinterundsommersportvergnugen",
        ],
        "SCHNEEPASS_ZENTRALSCHWEIZ_2022_23_ARCHIVED_ROSTER": [
            "15schneesportgebieteuber600pistenkilometer1abo",
            "sattelhochstuckliag",
            "mythenregion",
            "stoosbahnenag",
            "klewenalpstockhutte",
            "andermattsedrundisentis",
            "engelbergtitlis",
            "brunnibahnenengelberg",
            "sportbahnenmelchseefrutt",
            "rigibahnenag",
            "bergbahnenmeiringenhaslibergag",
            "morlialp",
            "bergbahnensorenbergag",
            "sportbahnenmarbacheggag",
            "seilbahnenairolopescium",
            "skigebietrothenthurmneusell",
            "0312202212032023",
        ],
        "SCHNEEPASS_ZENTRALSCHWEIZ_2022_23_ARCHIVED_SUMMER_ROSTER": [
            "schneepassplusdasabofurdenwinterunddensommer",
            "15wintersportgebiete13sommersportgebiete1abo",
            "13sommergebietewartendaraufentdecktzuwerden",
            "aboschneepassplus22231102022bis3092023",
        ],
        "SCHNEEPASS_ZENTRALSCHWEIZ_2023_24_MEDIA_KIT": [
            "schneesportregionzentralschweiz20232024",
            "zugangszu15skigebieten",
            "13zentralschweizersommergebieten",
            "airolopescium",
            "andermattsedrundisentis",
            "engelbergbrunni",
            "engelbergtitlis",
            "klewenalpstockhutte",
            "marbachegg",
            "meringenhasliberg",
            "melchseefrutt",
            "morlialp",
            "mythenregion",
            "rothenturmneusell",
            "rigi",
            "sattelhochstuckli",
            "sorenberg",
            "stoos",
        ],
        "SCHNEEPASS_ZENTRALSCHWEIZ_2024_25_MEDIA_KIT": [
            "schneesportregion20242025",
            "15schneesportgebieten",
            "zugangzu13sommergebieten",
            "airolopescium",
            "andermattsedrundisentis",
            "engelbergbrunni",
            "engelbergtitlis",
            "klewenalpstockhutte",
            "marbachegg",
            "meringenhasliberg",
            "melchseefrutt",
            "morlialp",
            "mythenregion",
            "rothenturmneusell",
            "rigi",
            "sattelhochstuckli",
            "sorenberg",
            "stoos",
        ],
        "SAMNAUN_TOPCARD_SNOWPASS_TARIFFS_2017_18": [
            "tarifewinter201718",
            "snowpassgr",
            "samnaunischglgraubunden",
            "topcard",
            "1jahrsommer2017winter201718",
            "samnaunischgldavosklostersflimslaax",
        ],
        "BBGR_ANNUAL_2017_18": [
            "snowpassgraubunden",
            "wintersaison201718",
            "weiterentwicklungdessnowpasses",
        ],
        "BBGR_ANNUAL_2018_19": [
            "topcard",
            "aufdiewintersaison201819hin",
            "arosalenzerheideanstellesamnaunischgl",
            "3freiwahlbaretageimoberengadin",
            "snowpassgraubunden",
            "wintersaison201819",
            "8grossenunternehmen",
            "11mittlerenunternehmen",
            "31kleinenunternehmen",
        ],
        "BBGR_ANNUAL_2019_20": [
            "snowpassgraubunden",
            "letztesaisondesproduktssnowpass",
            "erweiterungdessnowpasseszueinemganzjahresabonnement",
        ],
        "SBS_PRICING_STUDY_2020_TOPCARD": [
            "topcardberechtigtzumskifahrenindendreigebieten",
            "arosalenzerheidedavosklostersundflimslaaxfalera",
            "bisundmit201718warsamnaunischglmitglied",
            "arosalenzerheideersetztsamnaunischglseit201819",
            "imsommerberechtigt",
            "dietopcardzurfreienfahrtinallendreigebieten",
            "ab201920istdietopcardandreitagenimgebietengelbergtitlisgultig",
            "engelbergtitlisersetztdieregionstmoritzoberengadin",
            "dersnowpassgraubundenkostetfurerwachsene",
            "imgegensatzzumsurselvaskipassistdersommernichtinkludiert",
            "inallengebietenunlimitiertgultig",
            "abbildung39saisonkartenpreisvonuberregionalengraubundnersaisonkarten",
        ],
        "GRAUBUENDEN_SNOWPASS_2019_20_ARCHIVED_PAGE": [
            "snowpassderskipassfurganzgraubunden",
            "wintersaisonabonnement",
            "beisamtlichenbergbahneningraubunden",
            "sedrunandermatt",
            "samnaunischgl",
            "ausgenommensindzudemeinzelnekleinskilifte",
            "tarifewintersaison20192020",
        ],
        "GRAUBUENDEN_SNOWPASS_2018_19_ARCHIVED_PAGE": [
            "snowpassderskipassfurganzgraubunden",
            "wintersaisonabonnement",
            "beisamtlichenbergbahneningraubunden",
            "sedrunandermatt",
            "samnaunischgl",
            "ausgenommensindeinzelnekleinskilifte",
            "gultigkeitsbereichdessnowpassingraubunden",
        ],
        "CORVATSCH_DIAVOLEZZA_ANNUAL_2018_19": [
            "berichtdesverwaltungsratesdercorvatschagunddiavolezzalagalbag",
            "geschaftsjahr201819",
            "dieserberichtdesverwaltungsratesbeziehtsichsomitaufbeidegesellschaften",
            "dasengadinwerdekeinpartnervonsnowpasscardwerden",
            "furvielskifahreramsnowpassgraubundenfesthalten",
        ],
    }
    for source_id, tokens in required.items():
        missing = [token for token in tokens if token not in texts[source_id]]
        if missing:
            raise ValueError(
                f"Expected historical pass evidence tokens missing from {source_id}: {missing}"
            )
    if "meilenweiss" in texts["PIZOL_ANNUAL_REPORT_2018_19"]:
        raise ValueError("Pizol annual report negative review changed; inspect before use")
    return metadata


def validate_configs(
    top4_config: dict[str, object],
    meilenweiss_config: dict[str, object],
    schneepass_config: dict[str, object],
    topcard_config: dict[str, object],
    snowpass_graubuenden_config: dict[str, object],
    analysis_config: dict[str, object],
    resorts: pd.DataFrame,
) -> dict[str, dict[str, object]]:
    versions = {
        top4_config["analysis_version"],
        meilenweiss_config["analysis_version"],
        schneepass_config["analysis_version"],
        topcard_config["analysis_version"],
        snowpass_graubuenden_config["analysis_version"],
        analysis_config["analysis_version"],
    }
    if len(versions) != 1:
        raise ValueError("Historical pass and Path C versions differ")
    if top4_config["seasons"] != EXPECTED_TOP4_SEASONS:
        raise ValueError("Historical Top4 must preserve the eight declared seasons")
    top4_areas = list(top4_config["areas"])
    if len(top4_areas) != 4 or {
        area["official_area_label"] for area in top4_areas
    } != EXPECTED_TOP4_AREAS:
        raise ValueError("Historical Top4 must contain the four official regional areas")
    meilenweiss_seasons = list(meilenweiss_config["seasons"])
    if [item["season"] for item in meilenweiss_seasons] != EXPECTED_MEILENWEISS_SEASONS:
        raise ValueError("Historical Meilenweiss seasons changed unexpectedly")
    known_resort_ids = set(resorts["resort_id"])
    for season in meilenweiss_seasons:
        areas = list(season["areas"])
        if len(areas) != EXPECTED_MEILENWEISS_AREA_COUNTS[season["season"]]:
            raise ValueError(f"Unexpected Meilenweiss area count for {season['season']}")
        if len({area["official_area_label"] for area in areas}) != len(areas):
            raise ValueError(f"Duplicate Meilenweiss area in {season['season']}")
        linked_ids = [item for area in areas for item in area["linked_resort_ids"]]
        if len(linked_ids) != len(set(linked_ids)):
            raise ValueError(f"Duplicate supplied listing link in {season['season']}")
        unknown = set(linked_ids) - known_resort_ids
        if unknown:
            raise ValueError(f"Unknown Meilenweiss listing IDs: {sorted(unknown)}")
    schneepass_seasons = list(schneepass_config["seasons"])
    if [item["season"] for item in schneepass_seasons] != EXPECTED_SCHNEEPASS_SEASONS:
        raise ValueError("Historical Schneepass seasons changed unexpectedly")
    for season in schneepass_seasons:
        areas = list(season["areas"])
        if len(areas) != EXPECTED_SCHNEEPASS_AREA_COUNTS[season["season"]]:
            raise ValueError(f"Unexpected Schneepass area count for {season['season']}")
        if len({area["official_area_label"] for area in areas}) != len(areas):
            raise ValueError(f"Duplicate Schneepass area in {season['season']}")
        linked_ids = [item for area in areas for item in area["linked_resort_ids"]]
        if len(linked_ids) != len(set(linked_ids)):
            raise ValueError(f"Duplicate supplied Schneepass listing link in {season['season']}")
        unknown = set(linked_ids) - known_resort_ids
        if unknown:
            raise ValueError(f"Unknown Schneepass listing IDs: {sorted(unknown)}")
    topcard_seasons = list(topcard_config["seasons"])
    if [item["season"] for item in topcard_seasons] != EXPECTED_TOPCARD_SEASONS:
        raise ValueError("Historical TopCard seasons changed unexpectedly")
    for season in topcard_seasons:
        areas = list(season["areas"])
        if len(areas) != EXPECTED_TOPCARD_AREA_COUNTS[season["season"]]:
            raise ValueError(f"Unexpected TopCard area count for {season['season']}")
        if len({area["official_area_label"] for area in areas}) != len(areas):
            raise ValueError(f"Duplicate TopCard area in {season['season']}")
        linked_ids = [item for area in areas for item in area["linked_resort_ids"]]
        if len(linked_ids) != len(set(linked_ids)):
            raise ValueError(f"Duplicate supplied TopCard listing link in {season['season']}")
        unknown = set(linked_ids) - known_resort_ids
        if unknown:
            raise ValueError(f"Unknown TopCard listing IDs: {sorted(unknown)}")
        for area in areas:
            tier = area["winter_access_tier"]
            day_limit = area["winter_access_days_limit"]
            if tier == "limited_partner_three_days" and day_limit != 3:
                raise ValueError("TopCard limited partner must retain a three-day limit")
            if tier == "unlimited_core_area" and day_limit is not None:
                raise ValueError("TopCard core areas cannot carry a winter day limit")
    snowpass_graubuenden_seasons = list(snowpass_graubuenden_config["seasons"])
    if [item["season"] for item in snowpass_graubuenden_seasons] != (
        EXPECTED_SNOWPASS_GRAUBUENDEN_SEASONS
    ):
        raise ValueError("Historical SnowPass Graubünden seasons changed unexpectedly")
    for season in snowpass_graubuenden_seasons:
        areas = list(season["areas"])
        expected_count = EXPECTED_SNOWPASS_GRAUBUENDEN_AREA_COUNTS[season["season"]]
        if len(areas) != expected_count:
            raise ValueError(
                f"Unexpected SnowPass Graubünden area count for {season['season']}"
            )
        if len({area["official_area_label"] for area in areas}) != len(areas):
            raise ValueError(
                f"Duplicate SnowPass Graubünden area in {season['season']}"
            )
        linked_ids = [item for area in areas for item in area["linked_resort_ids"]]
        if len(linked_ids) != len(set(linked_ids)):
            raise ValueError(
                f"Duplicate supplied SnowPass Graubünden listing link in {season['season']}"
            )
        unknown = set(linked_ids) - known_resort_ids
        if unknown:
            raise ValueError(
                f"Unknown SnowPass Graubünden listing IDs: {sorted(unknown)}"
            )
        if any(area["winter_access_tier"] != "unlimited_winter_area" for area in areas):
            raise ValueError("SnowPass Graubünden areas must retain unlimited winter access")
        if any(area["winter_access_days_limit"] is not None for area in areas):
            raise ValueError("SnowPass Graubünden areas cannot carry a winter day limit")
        if any(bool(area["area_specific_summer_access_documented"]) for area in areas):
            raise ValueError("Winter-only SnowPass Graubünden cannot gain summer area links")
    top4_linked_ids = [
        item for area in top4_areas for item in area["linked_resort_ids"]
    ]
    if len(top4_linked_ids) != 5 or len(top4_linked_ids) != len(set(top4_linked_ids)):
        raise ValueError("Historical Top4 mapping must retain five unique listing links")
    protected = [
        "historical_market_absence_verified",
        "pre_treatment_feature_approved",
        "causal_covariate_approved",
        "recommendation_feature_approved",
        "composite_score_approved",
    ]
    for config in [
        top4_config,
        meilenweiss_config,
        schneepass_config,
        topcard_config,
        snowpass_graubuenden_config,
    ]:
        if any(bool(config[field]) for field in protected):
            raise ValueError("A protected historical competing-pass approval became true")
    reviews = list(meilenweiss_config["nonconfirming_source_reviews"])
    if len(reviews) != 1 or reviews[0]["membership_use"] != "not_used_as_membership_evidence":
        raise ValueError("Non-confirming Pizol source must remain excluded from membership")
    return validate_sources(
        top4_config,
        meilenweiss_config,
        schneepass_config,
        topcard_config,
        snowpass_graubuenden_config,
    )


def product_seasons(
    top4_config: dict[str, object],
    meilenweiss_config: dict[str, object],
    schneepass_config: dict[str, object],
    topcard_config: dict[str, object],
    snowpass_graubuenden_config: dict[str, object],
) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for season in top4_config["seasons"]:
        items.append(
            {
                "competing_pass_id": top4_config["competing_pass_id"],
                "competing_pass_name": top4_config["competing_pass_name"],
                "season": season,
                "areas": top4_config["areas"],
                "source_ids": top4_config["source_ids"],
                "evidence_scope": "continuous_official_four_area_product_roster",
                "product_winter_destination_count": 4,
                "product_summer_destination_count": None,
                "annual_pass_following_summer_season": None,
                "annual_pass_following_summer_included": None,
                "season_only_pass_following_summer_included": None,
                "continuity_basis": top4_config["continuity_basis"],
            }
        )
    for season in meilenweiss_config["seasons"]:
        items.append(
            {
                "competing_pass_id": meilenweiss_config["competing_pass_id"],
                "competing_pass_name": meilenweiss_config["competing_pass_name"],
                **season,
                "continuity_basis": (
                    "season_specific_official_operator_material_no_cross_season_"
                    "continuity_inference"
                ),
            }
        )
    for season in schneepass_config["seasons"]:
        items.append(
            {
                "competing_pass_id": schneepass_config["competing_pass_id"],
                "competing_pass_name": schneepass_config["competing_pass_name"],
                **season,
                "continuity_basis": (
                    "season_specific_official_operator_or_product_material_no_"
                    "cross_season_continuity_inference"
                ),
            }
        )
    for season in topcard_config["seasons"]:
        items.append(
            {
                "competing_pass_id": topcard_config["competing_pass_id"],
                "competing_pass_name": topcard_config["competing_pass_name"],
                **season,
                "continuity_basis": (
                    "season_specific_official_tariff_and_industry_study_with_"
                    "explicit_2018_2019_core_area_replacement"
                ),
            }
        )
    for season in snowpass_graubuenden_config["seasons"]:
        items.append(
            {
                "competing_pass_id": snowpass_graubuenden_config[
                    "competing_pass_id"
                ],
                "competing_pass_name": snowpass_graubuenden_config[
                    "competing_pass_name"
                ],
                **season,
                "continuity_basis": (
                    "season_specific_official_evidence_no_unnamed_area_or_"
                    "cross_season_membership_inference"
                ),
            }
        )
    return items


def build_area_seasons(
    analysis_version: str, specs: list[dict[str, object]]
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for spec in specs:
        for area in spec["areas"]:
            product_summer_season = spec.get(
                "product_summer_season",
                spec["annual_pass_following_summer_season"],
            )
            product_summer_included = spec.get(
                "product_summer_included",
                spec["annual_pass_following_summer_included"],
            )
            product_summer_timing = spec.get(
                "product_summer_timing",
                "following_summer_after_winter_season"
                if product_summer_season is not None
                else "not_documented",
            )
            has_product_summer_statement = product_summer_included is True
            area_summer = bool(
                area.get("area_specific_summer_access_documented", False)
            )
            records.append(
                {
                    "analysis_version": analysis_version,
                    "competing_pass_id": spec["competing_pass_id"],
                    "competing_pass_name": spec["competing_pass_name"],
                    "season": spec["season"],
                    "official_area_label": area["official_area_label"],
                    "winter_access_documented": True,
                    "evidence_scope": spec["evidence_scope"],
                    "product_winter_destination_count": spec["product_winter_destination_count"],
                    "product_summer_destination_count": spec["product_summer_destination_count"],
                    "annual_pass_following_summer_season": spec["annual_pass_following_summer_season"],
                    "annual_pass_following_summer_included": spec["annual_pass_following_summer_included"],
                    "season_only_pass_following_summer_included": spec["season_only_pass_following_summer_included"],
                    "product_summer_season": product_summer_season,
                    "product_summer_included": product_summer_included,
                    "product_summer_timing": product_summer_timing,
                    "winter_access_tier": area.get(
                        "winter_access_tier", "documented_area_access_tier_unspecified"
                    ),
                    "winter_access_days_limit": area.get("winter_access_days_limit"),
                    "area_specific_summer_access_documented": area_summer,
                    "area_specific_summer_access_status": (
                        "documented_for_official_pass_area"
                        if area_summer
                        else
                        "unknown_not_inferable_from_product_wide_annual_pass_statement"
                        if has_product_summer_statement
                        else "not_documented_in_reviewed_sources"
                    ),
                    "area_specific_summer_access_tier": area.get(
                        "area_specific_summer_access_tier", "not_documented"
                    ),
                    "area_specific_summer_access_days_limit": area.get(
                        "area_specific_summer_access_days_limit"
                    ),
                    "linked_resort_ids": "|".join(area["linked_resort_ids"]),
                    "mapping_basis": area["mapping_basis"],
                    "scope_note": area["scope_note"],
                    "continuity_basis": spec["continuity_basis"],
                    "source_ids": "|".join(area.get("source_ids", spec["source_ids"])),
                    "historical_market_absence_verified": False,
                    "pre_treatment_feature_approved": False,
                    "causal_covariate_approved": False,
                    "recommendation_feature_approved": False,
                    "composite_score_approved": False,
                    "interpretation": INTERPRETATION,
                }
            )
    area_seasons = pd.DataFrame(records)
    if len(area_seasons) != 155:
        raise ValueError("Expected 155 historical pass area-season rows")
    if area_seasons.duplicated(
        ["competing_pass_id", "season", "official_area_label"]
    ).any():
        raise ValueError("Duplicate historical pass area-season row")
    documented_summer = area_seasons[
        area_seasons["area_specific_summer_access_documented"]
    ]
    if len(documented_summer) != 10 or not documented_summer[
        "competing_pass_id"
    ].eq("topcard").all():
        raise ValueError("Area-specific summer evidence must remain limited to TopCard")
    return area_seasons


def build_resort_seasons(
    analysis_version: str,
    specs: list[dict[str, object]],
    resorts: pd.DataFrame,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for spec in specs:
        area_by_resort: dict[str, dict[str, object]] = {}
        for area in spec["areas"]:
            for resort_id in area["linked_resort_ids"]:
                area_by_resort[resort_id] = area
        for resort in resorts.itertuples(index=False):
            area = area_by_resort.get(resort.resort_id)
            linked = area is not None
            product_summer = spec.get(
                "product_summer_included",
                spec["annual_pass_following_summer_included"],
            )
            product_summer_season = spec.get(
                "product_summer_season",
                spec["annual_pass_following_summer_season"],
            )
            product_summer_timing = spec.get(
                "product_summer_timing",
                "following_summer_after_winter_season"
                if product_summer_season is not None
                else "not_documented",
            )
            area_summer = bool(
                linked and area.get("area_specific_summer_access_documented", False)
            )
            records.append(
                {
                    "analysis_version": analysis_version,
                    "resort_id": resort.resort_id,
                    "resort_name_canonical": resort.resort_name_canonical,
                    "cluster_id": resort.cluster_id,
                    "season": spec["season"],
                    "competing_pass_id": spec["competing_pass_id"],
                    "competing_pass_name": spec["competing_pass_name"],
                    "official_area_label": area["official_area_label"] if linked else "",
                    "historical_competing_pass_link_documented": linked,
                    "winter_access_documented": linked,
                    "historical_competing_pass_link_status": (
                        f"documented_{spec['competing_pass_id']}_positive_area_link"
                        if linked
                        else NO_LINK_STATUS
                    ),
                    "evidence_scope": spec["evidence_scope"],
                    "product_winter_destination_count": spec["product_winter_destination_count"],
                    "product_summer_destination_count": spec["product_summer_destination_count"],
                    "annual_pass_following_summer_season": spec["annual_pass_following_summer_season"],
                    "annual_pass_following_summer_included": spec[
                        "annual_pass_following_summer_included"
                    ],
                    "product_summer_season": product_summer_season,
                    "product_summer_included": product_summer,
                    "product_summer_timing": product_summer_timing,
                    "winter_access_tier": (
                        area.get(
                            "winter_access_tier",
                            "documented_area_access_tier_unspecified",
                        )
                        if linked
                        else "not_evaluated_without_documented_area_link"
                    ),
                    "winter_access_days_limit": (
                        area.get("winter_access_days_limit") if linked else None
                    ),
                    "area_specific_summer_access_documented": area_summer,
                    "area_specific_summer_access_status": (
                        "documented_for_official_pass_area"
                        if area_summer
                        else
                        "unknown_not_inferable_from_product_wide_annual_pass_statement"
                        if linked and product_summer is True
                        else "not_documented_in_reviewed_sources"
                        if linked
                        else "not_evaluated_without_documented_area_link"
                    ),
                    "area_specific_summer_access_tier": (
                        area.get("area_specific_summer_access_tier", "not_documented")
                        if linked
                        else "not_evaluated_without_documented_area_link"
                    ),
                    "area_specific_summer_access_days_limit": (
                        area.get("area_specific_summer_access_days_limit")
                        if linked
                        else None
                    ),
                    "mapping_basis": area["mapping_basis"] if linked else "",
                    "historical_competing_pass_market_absence_verified": False,
                    "historical_competing_pass_feature_approved": False,
                    "pre_treatment_feature_approved": False,
                    "causal_covariate_approved": False,
                    "recommendation_feature_approved": False,
                    "composite_score_approved": False,
                    "source_ids": "|".join(spec["source_ids"]),
                    "interpretation": INTERPRETATION,
                }
            )
    history = pd.DataFrame(records)
    if len(history) != len(resorts) * 21:
        raise ValueError("Historical product-listing-season grain changed")
    if history.duplicated(["competing_pass_id", "resort_id", "season"]).any():
        raise ValueError("Duplicate historical product-listing-season row")
    links_by_product = history.groupby("competing_pass_id")[
        "historical_competing_pass_link_documented"
    ].sum()
    if links_by_product.to_dict() != {
        "meilenweiss": 26,
        "schneepass_zentralschweiz": 55,
        "snowpass_graubuenden": 43,
        "top4": 40,
        "topcard": 20,
    }:
        raise ValueError(f"Unexpected documented product links: {links_by_product.to_dict()}")
    if history["historical_competing_pass_market_absence_verified"].any():
        raise ValueError("Reviewed product non-links cannot verify historical market absence")
    documented_summer = history[
        history["area_specific_summer_access_documented"]
    ]
    if len(documented_summer) != 19 or not documented_summer[
        "competing_pass_id"
    ].eq("topcard").all():
        raise ValueError("Listing-level summer access must remain limited to TopCard")
    return history


def build_cluster_context(
    analysis_version: str,
    history: pd.DataFrame,
    resorts: pd.DataFrame,
    features: pd.DataFrame,
    positive_source_ids: list[str],
    nonconfirming_source_ids: list[str],
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
        documented_seasons = sorted(set(linked_rows["season"]), key=season_sort_key)
        if linked_listing_count == 0:
            scope_status = "no_documented_link_in_reviewed_products"
        elif linked_listing_count == listing_count:
            scope_status = "all_cluster_listings_have_documented_link"
        else:
            scope_status = "partial_cluster_listing_links_documented"
        has_product_summer_statement = linked_rows["product_summer_included"].eq(True).any()
        has_area_summer = linked_rows[
            "area_specific_summer_access_documented"
        ].eq(True).any()
        limited_partner_link = linked_rows["winter_access_tier"].astype("string").str.startswith(
            "limited_partner"
        ).any()
        summer_tiers = linked_rows.loc[
            linked_rows["area_specific_summer_access_documented"].eq(True),
            "area_specific_summer_access_tier",
        ]
        rows.append(
            {
                "analysis_version": analysis_version,
                "cluster_id": cluster_id,
                "cluster_display_name": feature_lookup.loc[cluster_id, "cluster_display_name"],
                "candidate_for_path_c": feature_lookup.loc[cluster_id, "candidate_for_path_c"],
                "historical_competing_pass_products_reviewed": 5,
                "historical_competing_pass_unique_seasons_reviewed": 8,
                "historical_competing_pass_product_seasons_reviewed": 21,
                "historical_competing_pass_area_seasons_reviewed": 155,
                "historical_competing_pass_cluster_listing_count": listing_count,
                "historical_competing_pass_linked_listing_count": linked_listing_count,
                "historical_competing_pass_linked_listing_share": linked_listing_count / listing_count,
                "historical_competing_pass_scope_status": scope_status,
                "historical_competing_pass_linked_resort_ids": pipe_unique(linked_ids),
                "historical_competing_pass_unlinked_resort_ids": pipe_unique(listing_ids - linked_ids),
                "historical_competing_pass_documented_season_count": len(documented_seasons),
                "historical_competing_pass_documented_product_season_count": len(
                    linked_rows[["competing_pass_id", "season"]].drop_duplicates()
                ),
                "historical_competing_pass_documented_seasons": "|".join(documented_seasons),
                "historical_competing_pass_first_documented_season": (
                    documented_seasons[0] if documented_seasons else pd.NA
                ),
                "historical_competing_pass_last_documented_season": (
                    documented_seasons[-1] if documented_seasons else pd.NA
                ),
                "historical_competing_pass_ids": pipe_unique(linked_rows["competing_pass_id"]),
                "historical_competing_pass_names": pipe_unique(linked_rows["competing_pass_name"]),
                "historical_competing_pass_area_labels": pipe_unique(linked_rows["official_area_label"]),
                "historical_competing_pass_access_tiers": pipe_unique(
                    linked_rows["winter_access_tier"]
                ),
                "historical_competing_pass_limited_partner_link_documented": bool(
                    limited_partner_link
                ),
                "historical_competing_pass_product_level_summer_inclusion_documented": bool(
                    has_product_summer_statement
                ),
                "historical_competing_pass_area_specific_summer_access_documented": bool(
                    has_area_summer
                ),
                "historical_competing_pass_area_specific_summer_access_tiers": pipe_unique(
                    summer_tiers
                ),
                "historical_competing_pass_summer_scope_status": (
                    "area_specific_summer_access_documented_for_one_or_more_linked_areas"
                    if has_area_summer
                    else "product_level_summer_inclusion_only_area_specific_status_unknown"
                    if has_product_summer_statement
                    else "no_reviewed_area_specific_summer_evidence"
                    if documented_seasons
                    else "no_documented_historical_link"
                ),
                "historical_competing_pass_market_absence_verified": False,
                "historical_competing_pass_context_available": bool(documented_seasons),
                "historical_competing_pass_temporal_scope": (
                    "top4_2017_2018_to_2024_2025_and_meilenweiss_positive_"
                    "evidence_2019_2020_to_2021_2022_plus_schneepass_"
                    "zentralschweiz_2021_2022_to_2024_2025_plus_"
                    "tiered_topcard_2017_2018_to_2019_2020_plus_snowpass_"
                    "graubuenden_2017_2018_to_2019_2020_conservative"
                ),
                "historical_competing_pass_context_interpretation": INTERPRETATION,
                "historical_competing_pass_feature_approved": False,
                "historical_competing_pass_pre_treatment_approved": False,
                "historical_competing_pass_causal_covariate_approved": False,
                "historical_competing_pass_recommendation_feature_approved": False,
                "historical_competing_pass_composite_score_approved": False,
                "historical_competing_pass_source_ids": "|".join(sorted(positive_source_ids)),
                "historical_competing_pass_nonconfirming_source_ids": "|".join(
                    sorted(nonconfirming_source_ids)
                ),
            }
        )
    context = pd.DataFrame(rows)
    if len(context) != 162 or not context["cluster_id"].is_unique:
        raise ValueError("Historical competing-pass context must preserve 162 clusters")
    if int(context["historical_competing_pass_context_available"].sum()) != 37:
        raise ValueError("Expected 37 lift clusters with documented historical links")
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
        if column not in {"analysis_version", "cluster_id", "cluster_display_name", "candidate_for_path_c"}
    ]
    stale_historical_columns = [
        column
        for column in decision.columns
        if column.startswith("historical_competing_pass_")
    ]
    decision = decision.drop(columns=stale_historical_columns).merge(
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
        raise ValueError("Historical pass evidence became an approved or inferred feature")
    DECISION_OUTPUT.write_text(
        decision.to_csv(index=False, lineterminator="\n"), encoding="utf-8"
    )


def write_report(summary: dict[str, object]) -> None:
    report = f"""# Historical competing-pass context: Top4, Meilenweiss, Schneepass Zentralschweiz, TopCard and SnowPass Graubünden

## Evidence recovered

The checksum-pinned Top4 reconstruction remains unchanged: four official regions over eight consecutive seasons from 2017/2018 through 2024/2025. Three official operator PDFs retain the bounded Meilenweiss evidence for 2019/2020, 2020/2021 and 2021/2022. Schneepass Zentralschweiz now covers four consecutive seasons from 2021/2022 through 2024/2025: the previously missing 2022/2023 season is recovered from checksum-pinned official winter and summer pages captured on 30 November 2022. The archived winter page supplies the complete 15-area roster and the separate SchneepassPlus page documents a 13-area summer product valid through 30 September 2023; the product-wide summer statement is not widened into area-specific rights.

Three official TopCard sources add 2017/2018 through 2019/2020. Samnaun/Ischgl, Davos-Klosters and Flims-Laax form the 2017/2018 core. Arosa Lenzerheide replaces Samnaun/Ischgl in 2018/2019. The three core areas remain unlimited, while the additional partner benefit is kept in a separate tier: three freely selectable days in Engadin St. Moritz/Oberengadin in 2018/2019, replaced by three visits at Engelberg-Titlis from 2019/2020. The supplied Schatzalp listing is not inferred from the broader Davos-Klosters label.

SnowPass Graubünden is now separated from both TopCard and Schneepass Zentralschweiz. The official Samnaun tariff supports one exact 2017/2018 host-area link. For 2018/2019, an immutable capture of the official Graubünden Ferien page states validity at all Graubünden mountain railways, explicitly including Samnaun-Ischgl and Sedrun-Andermatt, while excluding unresolved individual small lifts. The industry study supplies a stable 17-major-area terminology, and the joint Corvatsch AG / Diavolezza Lagalb AG report supports two additional exact host links. The reconstruction therefore retains 19 conservative areas for 2018/2019 rather than inferring the unavailable detailed small-lift roster. The corresponding official 2019/2020 page and industry study support the same 17-major-area frame for the final SnowPass season. Together these sources support **{summary['snowpass_graubuenden_area_season_rows']} conservative area-season rows** and **{summary['documented_snowpass_graubuenden_listing_season_links']} positive listing-season links**. Neither season is called a complete small-lift roster because both detailed validity PDFs remain unavailable and the stated individual exclusions are unresolved.

The combined output contains **{summary['area_season_rows']} area-season rows**, **{summary['resort_product_season_rows']} product-listing-season rows** and **{summary['documented_listing_season_links']} positive listing-season links**. These reach **{summary['clusters_with_documented_link']} lift clusters**, including **{summary['path_c_candidates_with_documented_link']} of {summary['path_c_candidates']}** apparent Path C candidates.

## Winter and summer are not conflated

Each linked area is positive winter evidence. TopCard contributes **{summary['documented_topcard_unlimited_core_listing_season_links']} unlimited-core** and **{summary['documented_topcard_limited_partner_listing_season_links']} limited-partner** listing-season links; those tiers are never pooled as equivalent access. Its three core areas have documented summer access, and the 2019/2020 Engelberg-Titlis benefit is limited to three visits shared between summer and winter. This yields **{summary['area_specific_summer_access_documented_rows']} area-season** and **{summary['listing_specific_summer_access_documented_rows']} listing-season** summer links, all from TopCard.

Meilenweiss and Schneepass Zentralschweiz retain product-level summer statements where their official material supports them. Their aggregate statements do not identify every area-level summer entitlement, so no area-specific summer right is inferred for those products. SnowPass Graubünden is explicitly retained as winter-only. Product-level and area-specific evidence remain separate.

## Conservative scope and negative evidence

Malbun in Liechtenstein is not linked to the supplied Buchserberg-Malbun listing, which is a different Swiss area. Hoher Kasten has no equivalent supplied ski listing. The historical Airolo-Pesciüm label is not widened to Airolo-Lüina, and broad cluster neighbours never inherit a documented listing link. The official Pizol 2018/2019 annual report was checksum-verified, text-searched and visually reviewed but contains no explicit Meilenweiss reference; it is recorded as a non-confirming source and creates neither membership nor absence evidence.

## Decision limit

Five products and twenty-one product-seasons still do not reconstruct the full historical multi-resort-pass market. The recovered 2022/2023 Schneepass Zentralschweiz roster is season-specific official evidence rather than an adjacent-season interpolation; the official SnowPass 2018/2019 and 2019/2020 all-canton statements support major-area links but not the excluded-small-lift boundary encoded in their unavailable detailed PDFs; non-links do not verify absence; evidence scopes differ by season; several observations postdate Magic Pass treatment anchors; and benefit intensity and prices are not harmonised. Historical-market-absence, pre-treatment, causal, recommendation and composite-score approvals remain false. The result is qualified context, not a ranking input.

## Outputs

- `config/competing_pass_historical_top4.json`
- `config/competing_pass_historical_meilenweiss.json`
- `config/competing_pass_historical_schneepass_zentralschweiz.json`
- `config/competing_pass_historical_topcard.json`
- `config/competing_pass_historical_snowpass_graubuenden.json`
- `data_processed/competing_pass_historical_area_seasons.csv`
- `data_processed/resort_competing_pass_history.csv`
- `data_processed/path_c_cluster_historical_competing_pass_context.csv`
- `reports/historical_competing_pass_candidate_summary.csv`
- `data_processed/magic_pass_decision_support.csv` (qualified historical fields appended)
"""
    REPORT_OUTPUT.write_text(report, encoding="utf-8")


def main() -> None:
    top4_config = json.loads(TOP4_CONFIG_PATH.read_text(encoding="utf-8"))
    meilenweiss_config = json.loads(MEILENWEISS_CONFIG_PATH.read_text(encoding="utf-8"))
    schneepass_config = json.loads(SCHNEEPASS_CONFIG_PATH.read_text(encoding="utf-8"))
    topcard_config = json.loads(TOPCARD_CONFIG_PATH.read_text(encoding="utf-8"))
    snowpass_graubuenden_config = json.loads(
        SNOWPASS_GRAUBUENDEN_CONFIG_PATH.read_text(encoding="utf-8")
    )
    analysis_config = json.loads(ANALYSIS_CONFIG_PATH.read_text(encoding="utf-8"))
    resorts = pd.read_csv(RESORT_PATH, dtype="string")
    features = pd.read_csv(FEATURE_PATH, dtype="string")
    if len(resorts) != 271 or resorts["resort_id"].duplicated().any():
        raise ValueError("Unexpected resort master grain")
    if len(features) != 162 or features["cluster_id"].duplicated().any():
        raise ValueError("Unexpected Path C cluster feature grain")

    metadata = validate_configs(
        top4_config,
        meilenweiss_config,
        schneepass_config,
        topcard_config,
        snowpass_graubuenden_config,
        analysis_config,
        resorts,
    )
    specs = product_seasons(
        top4_config,
        meilenweiss_config,
        schneepass_config,
        topcard_config,
        snowpass_graubuenden_config,
    )
    analysis_version = str(analysis_config["analysis_version"])
    area_seasons = build_area_seasons(analysis_version, specs)
    area_seasons.to_csv(AREA_SEASON_OUTPUT, index=False, lineterminator="\n")
    history = build_resort_seasons(analysis_version, specs, resorts)
    history.to_csv(RESORT_SEASON_OUTPUT, index=False, lineterminator="\n")
    positive_source_ids = list(top4_config["source_ids"]) + [
        source_id
        for season in meilenweiss_config["seasons"]
        for source_id in season["source_ids"]
    ] + [
        source_id
        for season in schneepass_config["seasons"]
        for source_id in season["source_ids"]
    ] + [
        source_id
        for season in topcard_config["seasons"]
        for source_id in season["source_ids"]
    ] + [
        source_id
        for season in snowpass_graubuenden_config["seasons"]
        for source_id in season["source_ids"]
    ]
    positive_source_ids = sorted(set(positive_source_ids))
    nonconfirming_source_ids = [
        item["source_id"] for item in meilenweiss_config["nonconfirming_source_reviews"]
    ]
    context = build_cluster_context(
        analysis_version,
        history,
        resorts,
        features,
        positive_source_ids,
        nonconfirming_source_ids,
    )
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
        "historical_competing_pass_documented_product_season_count",
        "historical_competing_pass_first_documented_season",
        "historical_competing_pass_last_documented_season",
        "historical_competing_pass_ids",
        "historical_competing_pass_names",
        "historical_competing_pass_area_labels",
        "historical_competing_pass_access_tiers",
        "historical_competing_pass_limited_partner_link_documented",
        "historical_competing_pass_product_level_summer_inclusion_documented",
        "historical_competing_pass_area_specific_summer_access_documented",
        "historical_competing_pass_area_specific_summer_access_tiers",
        "historical_competing_pass_summer_scope_status",
        "historical_competing_pass_market_absence_verified",
        "historical_competing_pass_feature_approved",
    ]
    candidates.sort_values(
        ["historical_competing_pass_context_available", "cluster_id"],
        ascending=[False, True],
    )[candidate_columns].to_csv(CANDIDATE_OUTPUT, index=False, lineterminator="\n")

    linked_candidates = int(candidates["historical_competing_pass_context_available"].sum())
    summary = {
        "analysis_version": analysis_version,
        "reviewed_historical_products": 5,
        "reviewed_product_seasons": 21,
        "reviewed_unique_winter_seasons": 8,
        "season_start": EXPECTED_TOP4_SEASONS[0],
        "season_end": EXPECTED_TOP4_SEASONS[-1],
        "top4_area_season_rows": int(area_seasons["competing_pass_id"].eq("top4").sum()),
        "meilenweiss_area_season_rows": int(
            area_seasons["competing_pass_id"].eq("meilenweiss").sum()
        ),
        "schneepass_zentralschweiz_area_season_rows": int(
            area_seasons["competing_pass_id"].eq("schneepass_zentralschweiz").sum()
        ),
        "topcard_area_season_rows": int(
            area_seasons["competing_pass_id"].eq("topcard").sum()
        ),
        "snowpass_graubuenden_area_season_rows": int(
            area_seasons["competing_pass_id"].eq("snowpass_graubuenden").sum()
        ),
        "area_season_rows": len(area_seasons),
        "resort_product_season_rows": len(history),
        "resort_season_rows": len(history),
        "documented_listing_season_links": int(
            history["historical_competing_pass_link_documented"].sum()
        ),
        "documented_top4_listing_season_links": int(
            history.loc[
                history["competing_pass_id"].eq("top4"),
                "historical_competing_pass_link_documented",
            ].sum()
        ),
        "documented_meilenweiss_listing_season_links": int(
            history.loc[
                history["competing_pass_id"].eq("meilenweiss"),
                "historical_competing_pass_link_documented",
            ].sum()
        ),
        "documented_schneepass_zentralschweiz_listing_season_links": int(
            history.loc[
                history["competing_pass_id"].eq("schneepass_zentralschweiz"),
                "historical_competing_pass_link_documented",
            ].sum()
        ),
        "documented_topcard_listing_season_links": int(
            history.loc[
                history["competing_pass_id"].eq("topcard"),
                "historical_competing_pass_link_documented",
            ].sum()
        ),
        "documented_snowpass_graubuenden_listing_season_links": int(
            history.loc[
                history["competing_pass_id"].eq("snowpass_graubuenden"),
                "historical_competing_pass_link_documented",
            ].sum()
        ),
        "documented_topcard_unlimited_core_listing_season_links": int(
            history.loc[
                history["competing_pass_id"].eq("topcard")
                & history["historical_competing_pass_link_documented"]
                & history["winter_access_tier"].eq("unlimited_core_area")
            ].shape[0]
        ),
        "documented_topcard_limited_partner_listing_season_links": int(
            history.loc[
                history["competing_pass_id"].eq("topcard")
                & history["historical_competing_pass_link_documented"]
                & history["winter_access_tier"].eq("limited_partner_three_days")
            ].shape[0]
        ),
        "unique_supplied_listings_with_documented_link": int(
            history.loc[history["historical_competing_pass_link_documented"], "resort_id"].nunique()
        ),
        "clusters_with_documented_link": int(
            context["historical_competing_pass_context_available"].sum()
        ),
        "path_c_candidates": len(candidates),
        "path_c_candidates_with_documented_link": linked_candidates,
        "path_c_candidates_without_documented_link": len(candidates) - linked_candidates,
        "path_c_candidate_partial_cluster_links": int(
            candidates["historical_competing_pass_scope_status"].eq(
                "partial_cluster_listing_links_documented"
            ).sum()
        ),
        "path_c_candidate_all_cluster_listing_links": int(
            candidates["historical_competing_pass_scope_status"].eq(
                "all_cluster_listings_have_documented_link"
            ).sum()
        ),
        "path_c_candidates_with_product_level_summer_inclusion": int(
            candidates[
                "historical_competing_pass_product_level_summer_inclusion_documented"
            ].sum()
        ),
        "area_specific_summer_access_documented_rows": int(
            area_seasons["area_specific_summer_access_documented"].sum()
        ),
        "listing_specific_summer_access_documented_rows": int(
            history["area_specific_summer_access_documented"].sum()
        ),
        "path_c_candidates_with_area_specific_summer_access": int(
            candidates[
                "historical_competing_pass_area_specific_summer_access_documented"
            ].sum()
        ),
        "nonconfirming_sources_reviewed": len(nonconfirming_source_ids),
        "market_absence_verified_rows": int(
            context["historical_competing_pass_market_absence_verified"].sum()
        ),
        "approved_features": int(context["historical_competing_pass_feature_approved"].sum()),
        "source_sha256": {
            source_id: record["sha256"] for source_id, record in metadata.items()
        },
        "interpretation": INTERPRETATION,
    }
    expected_summary = {
        "top4_area_season_rows": 32,
        "meilenweiss_area_season_rows": 29,
        "schneepass_zentralschweiz_area_season_rows": 46,
        "topcard_area_season_rows": 11,
        "snowpass_graubuenden_area_season_rows": 37,
        "area_season_rows": 155,
        "resort_product_season_rows": 5691,
        "documented_listing_season_links": 184,
        "documented_topcard_listing_season_links": 20,
        "documented_topcard_unlimited_core_listing_season_links": 18,
        "documented_topcard_limited_partner_listing_season_links": 2,
        "documented_snowpass_graubuenden_listing_season_links": 43,
        "unique_supplied_listings_with_documented_link": 52,
        "clusters_with_documented_link": 37,
        "path_c_candidates_with_documented_link": 30,
        "path_c_candidate_partial_cluster_links": 11,
        "path_c_candidate_all_cluster_listing_links": 19,
        "path_c_candidates_with_product_level_summer_inclusion": 19,
        "area_specific_summer_access_documented_rows": 10,
        "listing_specific_summer_access_documented_rows": 19,
        "path_c_candidates_with_area_specific_summer_access": 4,
        "market_absence_verified_rows": 0,
        "approved_features": 0,
    }
    mismatches = {
        key: (summary[key], value)
        for key, value in expected_summary.items()
        if summary[key] != value
    }
    if mismatches:
        raise ValueError(f"Historical competing-pass invariants changed: {mismatches}")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
