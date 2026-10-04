"""Integrate the four researcher-supplied BFS sources as separate context layers.

Offline rebuild from immutable evidence and checksum-linked workbook extraction.
No outcome, exposure, comparison role, estimator or sample is altered.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "data_external/source_evidence"
DERIVED = "DERIVED_MUNICIPALITY_ADDITIONAL_BFS_CONTEXT"
TYPOLOGY = "BFS_MUNICIPAL_TYPOLOGY_2020_SNAPSHOT_2026"
BUILDINGS = "BFS_NEW_RESIDENTIAL_BUILDINGS_DATA"
IMPI = "BFS_IMPI_INDEX_VALUES_2017_2026Q2"
INV8 = "BFS_TOURISM_INVESTMENTS_8_CATEGORIES_2023"
INV3 = "BFS_TOURISM_INVESTMENTS_ALPINE_2023"
CST_VALUES = "BFS_TOURISM_SATELLITE_VALUES_2024"
CST_SHARES = "BFS_TOURISM_SATELLITE_SHARES_2024"
OUTPUTS: dict[str, tuple[pd.DataFrame, str, str, str]] = {}


def evidence(sid: str) -> tuple[dict, Path]:
    records = [json.loads(p.read_text(encoding="utf-8")) for p in EVIDENCE.glob(sid + "_*.metadata.json")]
    if not records:
        raise FileNotFoundError(f"Uncollected evidence: {sid}")
    record = max(records, key=lambda r: r["retrieval_date"])
    path = ROOT / record["raw_file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
        raise RuntimeError(f"Checksum failure: {sid}")
    return record, path


def save(name: str, frame: pd.DataFrame, sid: str, geo: str, temporal: str) -> pd.DataFrame:
    frame.to_csv(ROOT / "data_processed" / f"{name}.csv", index=False, lineterminator="\n")
    OUTPUTS[name] = (frame, sid, geo, temporal)
    return frame


def numeric(token: object) -> float:
    if token is None or str(token).strip() in {"", "X", "...", "..", "*"}:
        return np.nan
    return float(token)


def typology() -> pd.DataFrame:
    _, path = evidence(TYPOLOGY)
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    rows = [[c.get_text(" ", strip=True) for c in tr.find_all("td")] for tr in soup.select("table tbody tr")]
    rows = [r for r in rows if r]
    if any(len(r) != 9 for r in rows):
        raise ValueError("Unexpected typology schema")
    frame = pd.DataFrame(rows, columns=["municipality_history_id", "municipality_bfs_id", "municipality_name_source",
                                       "canton_source", "district_name_source", "district_id_source",
                                       "urban_rural_code", "municipality_type_9_code", "municipality_type_25_code"])
    codecols = [c for c in frame if c.endswith("_code") or c.endswith("_id") or c.endswith("_id_source")]
    for c in codecols:
        frame[c] = pd.to_numeric(frame[c], errors="raise").astype(int)
    _, method = evidence("BFS_MUNICIPAL_TYPOLOGY_2020_METHOD")
    text = BeautifulSoup(method.read_text(encoding="utf-8"), "html.parser")
    labels = {}
    for cell in text.select("td"):
        match = re.fullmatch(r"(\d{1,3})\s+–\s+(.+)", cell.get_text(" ", strip=True))
        if match:
            labels.setdefault(int(match[1]), match[2])
    for code in ["urban_rural", "municipality_type_9", "municipality_type_25"]:
        frame[code + "_label_fr"] = frame[code + "_code"].map(labels)
        if frame[code + "_label_fr"].isna().any():
            raise ValueError(f"Unlabelled official category: {code}")
    frame["tourist_category_2020"] = frame.municipality_type_25_code.isin([134, 314, 334])
    frame["municipality_snapshot_date"] = "2026-01-01"
    frame["typology_reference_version"] = "2020"
    frame["typology_input_period_note"] = "STATPOP/STATENT 2019-2021; HESTA 2018,2019,2022; current municipality snapshot"
    frame["pre_treatment_matching_approved"] = False
    frame["source_id"] = TYPOLOGY
    frame["category_label_source_id"] = "BFS_MUNICIPAL_TYPOLOGY_2020_METHOD"
    assert len(frame) == 2110 and frame.municipality_bfs_id.is_unique
    return save("municipality_typology_2020_snapshot_2026", frame, TYPOLOGY, "municipality", "2020 typology; 2026-01-01 administrative snapshot")


def buildings() -> pd.DataFrame:
    _, raw = evidence(BUILDINGS)
    source = pd.read_csv(raw, encoding="cp1252", dtype=str, keep_default_na=False)
    geography, kind = source.columns[:2]
    _, meta = evidence("BFS_NEW_RESIDENTIAL_BUILDINGS_METADATA")
    variable = next(v for v in json.loads(meta.read_text(encoding="utf-8"))["variables"] if v["code"] == "Gebäudetyp")
    kinds = dict(zip(variable["valueTexts"], variable["values"]))
    long = source.melt(id_vars=[geography, kind], var_name="year", value_name="new_residential_buildings_source_token")
    parsed = long[geography].str.extract(r"^\.{6}(\d+) (.+)$")
    if parsed.isna().any().any():
        raise ValueError("Unexpected official municipality label")
    long["source_municipality_bfs_id"] = parsed[0].astype(int)
    long["municipality_bfs_id"] = long.source_municipality_bfs_id.replace({700: 6831})
    long["municipality_name_source"] = parsed[1]
    long["building_type_code"] = long[kind].map(kinds)
    if long.building_type_code.isna().any():
        raise ValueError("Unknown building category")
    long["building_type_label_source"] = long[kind]
    long["year"] = long.year.astype(int)
    long["new_residential_buildings"] = long.new_residential_buildings_source_token.map(numeric)
    long["source_spatial_reference_date"] = "2024-12-31"
    long["territorial_harmonisation_applied"] = long.source_municipality_bfs_id.eq(700)
    long["territorial_mutation_source_id"] = np.where(long.territorial_harmonisation_applied, "BFS_MUNICIPAL_MUTATION_3999", "")
    long["source_id"] = BUILDINGS
    long["causal_covariate_approved"] = False
    long = long.drop(columns=[geography, kind]).sort_values(["municipality_bfs_id", "year", "building_type_code"])
    assert not long.duplicated(["municipality_bfs_id", "year", "building_type_code"]).any()
    observed = long.new_residential_buildings.dropna()
    assert observed.ge(0).all() and observed.mod(1).eq(0).all()
    return save("municipality_new_residential_buildings_year", long, BUILDINGS, "municipality on fixed 2024 spatial reference", "calendar year 2013-2024")


def context(types: pd.DataFrame, construction: pd.DataFrame, universe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    units = universe[["municipality_bfs_id", "municipality_name", "municipality_first_exposure_month_120min"]].drop_duplicates()
    assert len(units) == 185 and units.municipality_bfs_id.is_unique
    result = units.merge(types.drop(columns="source_id"), on="municipality_bfs_id", how="left", validate="one_to_one")
    last = construction.loc[construction.year.eq(2024) & construction.building_type_code.eq("0"),
                            ["municipality_bfs_id", "source_municipality_bfs_id", "new_residential_buildings", "new_residential_buildings_source_token"]]
    result = result.merge(last, on="municipality_bfs_id", how="left", validate="one_to_one")
    result["new_buildings_context_year"] = 2024
    result["new_buildings_missing_reason"] = np.where(result.municipality_bfs_id.eq(6513), "Latena_not_in_2024_spatial_reference_no_predecessor_aggregation", np.where(result.new_residential_buildings.isna(), "source_value_unavailable", ""))
    result["typology_source_id"] = TYPOLOGY
    result["construction_source_id"] = BUILDINGS
    result["source_id"] = DERIVED
    result["context_use"] = "descriptive_current_context_only_no_automatic_matching"
    result = save("municipality_comparison_context_2026", result, DERIVED, "185 existing analytical territories", "current context; source dates retained")
    audit = universe[["focal_cohort_month", "municipality_bfs_id", "municipality_name", "treated_in_focal_cohort", "primary_donor_candidate_at_anchor"]].copy()
    # A full calendar year ending before the focal entry. Never use entry-year
    # annual totals, carry a later value backwards or impute missing predecessors.
    audit["baseline_calendar_year"] = pd.to_datetime(audit.focal_cohort_month).dt.year - 1
    total = construction.loc[construction.building_type_code.eq("0"), ["municipality_bfs_id", "year", "source_municipality_bfs_id", "new_residential_buildings", "new_residential_buildings_source_token"]]
    audit = audit.merge(total, left_on=["municipality_bfs_id", "baseline_calendar_year"], right_on=["municipality_bfs_id", "year"], how="left", validate="many_to_one").drop(columns="year")
    audit["baseline_value_available"] = audit.new_residential_buildings.notna()
    audit["baseline_missing_reason"] = np.where(audit.municipality_bfs_id.eq(6513), "Latena_not_in_2024_spatial_reference_no_predecessor_aggregation", np.where(audit.baseline_value_available, "", "source_value_unavailable"))
    audit["source_spatial_reference_date"] = "2024-12-31"
    audit["baseline_rule"] = "full_calendar_year_immediately_before_focal_entry_year"
    audit["causal_covariate_approved"] = False
    audit["pre_treatment_matching_approved"] = False
    audit["construction_source_id"] = BUILDINGS
    audit["source_id"] = DERIVED
    save("municipality_new_buildings_cohort_baseline_audit", audit, DERIVED, "analytical territory by existing focal cohort", "previous complete calendar year; fixed 2024 source geography")
    return result, audit


def workbooks() -> dict:
    data = json.loads((ROOT / "data_interim/municipality_additional_context/workbooks.json").read_text(encoding="utf-8"))
    for sid, book in data.items():
        record, _ = evidence(sid)
        if book["sha256"] != record["sha256"]:
            raise RuntimeError(f"Stale workbook extraction: {sid}")
    return data


def cell_record(sid: str, sheet: str, row: int, col: int, token: object) -> dict:
    return dict(source_id=sid, source_sheet=sheet, source_cell=f"{chr(64+col)}{row}",
                source_token="" if token is None else str(token), value=numeric(token),
                causal_covariate_approved=False)


def aggregate_context(books: dict) -> dict:
    rows = []
    sheets = books[IMPI]["sheets"]
    translated = {str(r[2]).strip(): str(r[3]).strip() for r in sheets["Uebersetzungen"] if r[2] and r[3]}
    table = sheets["T2"]
    scope_labels = {0: "Suisse — tous types de communes"}
    for n in range(1, 6):
        label = translated[str(table[52+n][0]).strip()]
        scope_labels[n] = label.split(" - ", 1)[1].strip()
    for rnum, row in enumerate(table, 1):
        match = re.fullmatch(r"Q([1-4]) (\d{4})", str(row[0]))
        if not match:
            continue
        quarter, year = map(int, match.groups())
        for col in range(2, 20):
            group, typecode = divmod(col-2, 6)
            rec = cell_record(IMPI, "T2", rnum, col, row[col-1])
            rec.update(year=year, quarter=quarter, quarter_start=f"{year}-{3*quarter-2:02d}-01",
                       property_type_code=["TOTAL", "MI", "PPE"][group],
                       property_type_label_fr=["Logements en propriété", "Maisons individuelles", "Appartements en propriété"][group],
                       municipality_type_code=typecode, scope_id="CH_ALL" if typecode == 0 else f"IMPI_TYPE_{typecode}",
                       geographic_scope=scope_labels[typecode], unit="index; 2019 Q4 = 100", publication_date="2026-07-30",
                       municipality_mapping_approved=False)
            rows.append(rec)
    prices = save("bfs_residential_property_price_index_quarter", pd.DataFrame(rows), IMPI, "Switzerland and five aggregated municipality types", "2017 Q1-2026 Q2")
    assert len(prices) == 38*18 and prices.value.notna().all()

    rows = []
    for sheet, table in books[INV8]["sheets"].items():
        headers = next(r for r in table if r[1] == "Installations de transport")
        for rnum, row in enumerate(table, 1):
            if not re.fullmatch(r"\d{4}", str(row[0])) or not 1995 <= int(row[0]) <= 2023:
                continue
            for col in range(2, 11):
                rec = cell_record(INV8, sheet, rnum, col, row[col-1])
                rec.update(year=int(row[0]), scope_id="CH_TOURIST_MUNICIPALITIES_2020", geographic_scope="Ensemble des communes touristiques; typologie 2020",
                           construction_work_type=sheet, structure_category_code=f"INV8_{col-1}", structure_category_label_source=headers[col-1],
                           unit="thousand CHF; current prices", publication_date="2025-11-17", resident_project_owners_only=True)
                rows.append(rec)
    inv8 = save("bfs_tourism_investments_tourist_municipalities_year", pd.DataFrame(rows), INV8, "aggregate of tourist municipalities defined by 2020 typology", "1995-2023 annual; November 2025 vintage")
    assert len(inv8) == 29*9*3

    rows = []
    for sheet, table in books[INV3]["sheets"].items():
        labels = {"Communes_touristiques": ("CH_TOURIST_MUNICIPALITIES_2020", "Ensemble des communes touristiques; typologie 2020"),
                  "Grisons": ("CH_CANTON_GR", "Grisons"), "Uri": ("CH_CANTON_UR", "Uri"), "Valais": ("CH_CANTON_VS", "Valais")}
        scope, label = labels[sheet]
        for rnum, row in enumerate(table, 1):
            if not re.fullmatch(r"\d{4}", str(row[0])) or not 1995 <= int(row[0]) <= 2023:
                continue
            for col in range(2, 11):
                group, metric = divmod(col-2, 3)
                rec = cell_record(INV3, sheet, rnum, col, row[col-1])
                rec.update(year=int(row[0]), scope_id=scope, geographic_scope=label,
                           structure_category_code=f"INV3_{group+1}", structure_category_label_source=table[2][1+3*group],
                           metric_label_source=table[3][col-1], unit="thousand CHF; current prices" if metric == 0 else "percent",
                           publication_date="2025-11-17", resident_project_owners_only=True)
                rows.append(rec)
    inv3 = save("bfs_tourism_investments_alpine_context_year", pd.DataFrame(rows), INV3, "tourist municipality aggregate plus cantons GR/UR/VS", "1995-2023 annual; November 2025 vintage")
    assert len(inv3) == 29*9*4

    rows = []
    heading_mismatches = []
    for sheet, table in books[CST_VALUES]["sheets"].items():
        year = int(sheet)
        if str(year) not in str(table[0][0]):
            heading_mismatches.append({"sheet": sheet, "original_heading": table[0][0]})
        for rnum in range(5, 20):
            row = table[rnum-1]
            for col in range(2, 8):
                metric_index = (col-2)//2
                rec = cell_record(CST_VALUES, sheet, rnum, col, row[col-1])
                rec.update(year=year, product_label_source=row[0], metric_label_source=str(table[2][1+2*metric_index]).strip()+"; "+str(table[3][col-1]).strip(),
                           unit="percent" if col % 2 else ("FTE" if col == 6 else "million CHF; current prices"),
                           scope_id="CH", geographic_scope="Suisse", publication_date="2025-11-17", provisional=year == 2024,
                           year_basis="official_sheet_name", original_sheet_heading=table[0][0],
                           vintage_note="CST 2017 revised base; does not incorporate national accounts revision 2025")
                rows.append(rec)
    for sheet, table in books[CST_SHARES]["sheets"].items():
        for col, yearlabel in enumerate(table[2][1:], 2):
            if yearlabel is None:
                continue
            year = int(str(yearlabel)[:4])
            for rnum in range(4, 10):
                token = table[rnum-1][col-1]
                rec = cell_record(CST_SHARES, sheet, rnum, col, token)
                label = table[rnum-1][0]
                rec.update(year=year, product_label_source="National total", metric_label_source=label,
                           unit="percent" if rnum in [8, 9] else "FTE" if rnum in [5, 7] else "million CHF; current prices",
                           scope_id="CH", geographic_scope="Suisse", publication_date="2025-11-17", provisional=year == 2024,
                           year_basis="official_column_label", original_sheet_heading=table[0][0],
                           vintage_note="CST 2017 revised base; does not incorporate national accounts revision 2025")
                rows.append(rec)
    cst = save("bfs_tourism_satellite_national_context_year", pd.DataFrame(rows), CST_VALUES+"|"+CST_SHARES, "Switzerland; products and national shares", "2001-2024 annual; November 2025 vintage")
    assert len(cst) == 24*15*6 + 24*6
    return dict(property_price_rows=len(prices), investments_8_category_rows=len(inv8), investments_3_category_rows=len(inv3),
                tourism_satellite_rows=len(cst), tourism_satellite_sheet_heading_mismatches=heading_mismatches)


def register_provenance() -> None:
    source_path = ROOT / "metadata/data_sources_master.csv"
    dictionary_path = ROOT / "metadata/data_dictionary.csv"
    old_sources = pd.read_csv(source_path, dtype=str).fillna("")
    old_dictionary = pd.read_csv(dictionary_path, dtype=str).fillna("")
    specs = json.loads((ROOT / "config/municipality_additional_evidence_sources.json").read_text(encoding="utf-8"))
    specs.append(dict(source_id=BUILDINGS, description="New completed buildings with dwellings; all five types for the existing territorial universe", organisation="Swiss Federal Statistical Office"))
    incoming = []
    for spec in specs:
        sid = spec["source_id"]
        record, _ = evidence(sid)
        linked = [name for name, (_, sources, _, _) in OUTPUTS.items() if sid in sources.split("|")]
        row = {c: "" for c in old_sources.columns}
        row.update(source_id=sid, variable_name="|".join(sorted(set(v for name in linked for v in OUTPUTS[name][0].columns))),
                   variable_description=spec["description"], source_organisation="Swiss Federal Statistical Office",
                   source_dataset_name=spec["description"], source_page_url=spec.get("url", record["url"]), direct_download_url=record["url"],
                   retrieval_method="Public HTTP GET or PXWeb POST; immutable local response with SHA-256; source-linked offline extraction",
                   retrieval_date=record["retrieval_date"], original_file_name=Path(record["raw_file"]).name, local_raw_file=record["raw_file"],
                   processed_file="|".join(f"data_processed/{name}.csv" for name in linked),
                   geographic_level=" | ".join(dict.fromkeys(OUTPUTS[name][2] for name in linked)) or "source discovery / documentation",
                   temporal_resolution=" | ".join(dict.fromkeys(OUTPUTS[name][3] for name in linked)) or "retrieved source snapshot",
                   license="Official terms govern; source attribution retained. IMPI table: OPEN-BY from package metadata; other exact license not verified",
                   access_conditions="Public; robots checked by existing collector; no restriction bypass",
                   transformation_applied="Original labels, codes and tokens retained; long reshaping. See report 80 and reproducible builder",
                   quality_notes="Context only; no causal covariate or matching approval. Source vintages and geographic scope are retained",
                   confidence_level="official source; analytical suitability qualified", manual_verification="Cached source content, method notes, workbook cells and scopes inspected",
                   notes=record.get("recovery_note", "No outcome/exposure/sample change; archived original source remains immutable"))
        if sid == BUILDINGS:
            row.update(api_endpoint=record["url"], api_parameters=record["request_file"], temporal_start="2013", temporal_end="2024", unit="completed building with dwellings")
        elif sid == TYPOLOGY:
            row.update(temporal_start="2020", temporal_end="2026-01-01", unit="categorical classification")
        elif sid == IMPI:
            row.update(temporal_start="2017 Q1", temporal_end="2026 Q2", unit="index; 2019 Q4 = 100")
        elif sid in [INV8, INV3]:
            row.update(temporal_start="1995", temporal_end="2023", unit="thousand CHF at current prices; percent where labelled")
        elif sid in [CST_VALUES, CST_SHARES]:
            row.update(temporal_start="2001", temporal_end="2024", unit="million CHF at current prices; FTE; percent")
        incoming.append(row)
    derived = {c: "" for c in old_sources.columns}
    derived.update(source_id=DERIVED, variable_description="Separate current municipal context and pre-entry construction availability audit; no automatic selection",
                   source_organisation="Thesis reproducible pipeline", source_dataset_name="Additional BFS municipality context",
                   retrieval_method="Deterministic offline Python", processed_file="data_processed/municipality_comparison_context_2026.csv|data_processed/municipality_new_buildings_cohort_baseline_audit.csv",
                   geographic_level="185 approved analytical territories; 1295 territory-cohort rows", temporal_resolution="current descriptive snapshot and previous complete year",
                   transformation_applied="Exact BFS ID joins; approved Moutier 700/6831 bridge; no other fusion; no imputation",
                   quality_notes="Latena missing for 2024 construction geography; typology uses post-entry HESTA for early cohorts; no matching approval",
                   confidence_level="high for transformation; contextual interpretation only")
    incoming.append(derived)
    new = pd.DataFrame(incoming).reindex(columns=old_sources.columns).fillna("")
    sources = pd.concat([old_sources[~old_sources.source_id.isin(new.source_id)], new], ignore_index=True)
    assert sources.source_id.is_unique
    sources.sort_values("source_id").to_csv(source_path, index=False, lineterminator="\n")
    definitions = []
    special = {
        "new_residential_buildings": ("Number of completed new buildings containing dwellings; NOT number of dwellings, hotel beds or investment expenditure", "building"),
        "new_residential_buildings_source_token": ("Original source token; preserve numeric zero versus unavailable/suppressed value", "source token"),
        "tourist_category_2020": ("Membership of official tourist categories 134,314,334; partly uses HESTA 2018/2019/2022", "boolean"),
        "municipality_bfs_id": ("Stable analytical territory BFS ID; only Moutier 700 is bridged to 6831 under prior official approval", "BFS identifier"),
        "value": ("Original source numeric value with unit carried by the row; no conversion, imputation or allocation to municipalities", "see unit field"),
        "baseline_calendar_year": ("Full calendar year immediately before focal entry year; annual entry-year values excluded", "calendar year"),
        "source_cell": ("Exact Excel cell in immutable source workbook and named sheet", "Excel coordinate"),
        "scope_id": ("Stable context scope identifier distinguishing national, canton and aggregated municipality types; no municipal allocation", "scope identifier"),
        "provisional": ("Official provisional 2024 tourism satellite result in November 2025 publication vintage", "boolean"),
        "source_spatial_reference_date": ("Fixed official construction-cube municipal perimeter reference: 2024-12-31", "ISO date"),
        "municipality_snapshot_date": ("Official administrative municipality state used for current typology: 2026-01-01", "ISO date"),
    }
    for name, (frame, sid, geo, time) in OUTPUTS.items():
        for variable in frame:
            default_unit = ("boolean" if pd.api.types.is_bool_dtype(frame[variable]) else
                            "calendar year" if variable in ["year", "new_buildings_context_year"] else
                            "quarter number" if variable == "quarter" else
                            "ISO date" if variable.endswith("_date") or variable.endswith("_month") or variable == "quarter_start" else
                            "BFS identifier" if variable.endswith("bfs_id") else "label/code")
            desc, unit = special.get(variable, (variable.replace("_", " ").capitalize()+"; original official label/code, explicit context restriction or transformation lineage", default_unit))
            definitions.append(dict(variable=variable, table=name, description=desc, unit=unit, data_type=str(frame[variable].dtype),
                                    geographic_level=geo, temporal_level=time, source_id=DERIVED if "|" in sid else sid,
                                    raw_or_derived="retained source field or explicitly documented derived context", formula="See report 80 and build_municipality_additional_context.py; original cells and tokens retained",
                                    causal_role="descriptive context; potential mediator after entry; causal/matching use unapproved", missing_share=f"{frame[variable].isna().mean():.6f}",
                                    notes="No interpolation, predecessor aggregation or municipality allocation of national/type/canton totals; dates and units are explicit"))
    new_dict = pd.DataFrame(definitions).reindex(columns=old_dictionary.columns).fillna("")
    keys = set(zip(new_dict.table, new_dict.variable))
    keep = ~old_dictionary.apply(lambda r: (r.table, r.variable) in keys, axis=1)
    dictionary = pd.concat([old_dictionary[keep], new_dict], ignore_index=True)
    dictionary.sort_values(["table", "variable"]).to_csv(dictionary_path, index=False, lineterminator="\n")
    # Add/update only our source sections; preserve unrelated source explanations.
    sections = []
    for r in new.sort_values("source_id").to_dict("records"):
        lines = [f"## {r['source_id']} — {r['source_dataset_name'] or r['original_file_name']}", "",
                      f"- **Contents and relevance:** {r['variable_description']}", f"- **Producer:** {r['source_organisation']}",
                      f"- **Exact URL:** {r['source_page_url'] or r['direct_download_url'] or r['api_endpoint'] or 'Not documented.'}",
                      f"- **Access and retrieval date:** {r['retrieval_method']}; {r['retrieval_date'] or 'unknown date'}.",
                      f"- **Variables:** {r['variable_name'] or 'Dataset-level record.'}", f"- **Transformations:** {r['transformation_applied']}",
                      f"- **Coverage:** {r['geographic_level']}; {r['temporal_resolution']}; {r['temporal_start'] or '?'} to {r['temporal_end'] or '?'}.",
                      f"- **Limitations:** {r['quality_notes'] or r['notes']}", f"- **Local raw file:** `{r['local_raw_file'] or 'not cached / not applicable'}`.", ""]
        sections.append((r["source_id"], "\n".join(lines)+"\n"))
    report = ROOT / "reports/DATA_SOURCES.md"
    text = report.read_text(encoding="utf-8")
    for sid, section in sections:
        pattern = rf"(?ms)^## {re.escape(sid)} — .*?(?=^## |\Z)"
        if re.search(pattern, text):
            text = re.sub(pattern, lambda _: section, text)
        else:
            anchor = text.find("## Outstanding provenance gaps")
            anchor = len(text) if anchor < 0 else anchor
            text = text[:anchor]+section+text[anchor:]
    report.write_text(text, encoding="utf-8")


def main() -> None:
    bridge = json.loads((ROOT / "config/accessibility_outcome_territorial_harmonisation.json").read_text(encoding="utf-8"))
    universe = pd.read_csv(ROOT / bridge["comparison_universe"])
    panel = ROOT / bridge["analytical_panel"]
    before = hashlib.sha256(panel.read_bytes()).hexdigest()
    types = typology()
    construction = buildings()
    current, baseline = context(types, construction, universe)
    summary = aggregate_context(workbooks())
    summary.update(researcher_request_date="2026-10-05", aggregated_series_authorised=True,
                   sources_already_integrated_at_initial_audit=False, municipality_typology_rows=len(types), analytical_territories=len(current),
                   typology_territory_coverage=int(current.municipality_type_25_code.notna().sum()), construction_rows=len(construction),
                   construction_territories=construction.municipality_bfs_id.nunique(), baseline_rows=len(baseline),
                   construction_baseline_available=int(baseline.baseline_value_available.sum()),
                   construction_missing_territories=current.loc[current.new_residential_buildings.isna(), "municipality_bfs_id"].tolist(),
                   causal_covariate_approved=False, pre_treatment_matching_approved=False, imputation_applied=False,
                   source_panel_sha256=before, input_files={sid: evidence(sid)[0]["sha256"] for sid in [TYPOLOGY, BUILDINGS, IMPI, INV8, INV3, CST_VALUES, CST_SHARES]},
                   outputs={name: len(frame) for name, (frame, _, _, _) in OUTPUTS.items()})
    assert before == hashlib.sha256(panel.read_bytes()).hexdigest()
    register_provenance()
    summary["total_sources"] = len(pd.read_csv(ROOT / "metadata/data_sources_master.csv"))
    summary["total_dictionary_rows"] = len(pd.read_csv(ROOT / "metadata/data_dictionary.csv"))
    (ROOT / "reports/municipality_additional_context_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
