"""Critical source-value, territorial-grain and leakage checks for BFS additions."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def read(name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(ROOT / "data_processed" / (name + ".csv"), float_precision="round_trip", **kwargs)


def test_context_joins_preserve_territorial_universe_and_missingness():
    frame = read("municipality_comparison_context_2026")
    bridge = json.loads((ROOT / "config/accessibility_outcome_territorial_harmonisation.json").read_text(encoding="utf8"))
    roles = pd.read_csv(ROOT / bridge["comparison_universe"])
    assert len(frame) == 185 and frame.municipality_bfs_id.is_unique
    assert set(frame.municipality_bfs_id) == set(roles.municipality_bfs_id)
    assert frame.municipality_type_25_code.notna().all()
    assert frame.loc[frame.new_residential_buildings.isna(), "municipality_bfs_id"].tolist() == [6513]
    assert frame.loc[frame.municipality_bfs_id.eq(6831), "source_municipality_bfs_id"].tolist() == [700]
    assert not frame.pre_treatment_matching_approved.any()
    summary = json.loads((ROOT / "reports/municipality_additional_context_summary.json").read_text(encoding="utf8"))
    assert hashlib.sha256((ROOT / bridge["analytical_panel"]).read_bytes()).hexdigest() == summary["source_panel_sha256"]


def test_buildings_roundtrip_source_tokens_and_exact_moutier_identity():
    frame = read("municipality_new_residential_buildings_year", dtype={"building_type_code": str, "new_residential_buildings_source_token": str}, keep_default_na=False)
    record = max((json.loads(p.read_text(encoding="utf8")) for p in (ROOT / "data_external/source_evidence").glob("BFS_NEW_RESIDENTIAL_BUILDINGS_DATA_*.metadata.json")), key=lambda r:r["retrieval_date"])
    source = pd.read_csv(ROOT / record["raw_file"], encoding="cp1252", dtype=str, keep_default_na=False)
    geo, kind = source.columns[:2]
    long = source.melt(id_vars=[geo,kind], var_name="year", value_name="token")
    long["source_municipality_bfs_id"] = long[geo].str.extract(r"^\.{6}(\d+)")[0].astype(int)
    long["year"] = long.year.astype(int)
    merged = frame.merge(long, left_on=["source_municipality_bfs_id","building_type_label_source","year"], right_on=["source_municipality_bfs_id",kind,"year"], validate="one_to_one")
    assert len(merged) == len(frame) == 11040
    assert merged.token.equals(merged.new_residential_buildings_source_token)
    assert len(frame[frame.new_residential_buildings_source_token.eq("0")]) > 0
    assert frame.loc[frame.new_residential_buildings_source_token.eq("0"), "new_residential_buildings"].astype(float).eq(0).all()
    assert set(frame.source_spatial_reference_date) == {"2024-12-31"}
    assert set(frame.loc[frame.territorial_harmonisation_applied.eq(True), "municipality_bfs_id"]) == {6831}


def test_pre_entry_annual_availability_does_not_use_entry_year_or_impute_latena():
    audit = read("municipality_new_buildings_cohort_baseline_audit")
    assert len(audit) == 1295 and not audit.duplicated(["focal_cohort_month","municipality_bfs_id"]).any()
    entry = pd.to_datetime(audit.focal_cohort_month)
    end = pd.to_datetime(audit.baseline_calendar_year.astype(str)+"-12-31")
    assert end.lt(entry).all()
    assert audit.baseline_value_available.sum() == 1288
    assert set(audit.loc[~audit.baseline_value_available,"municipality_bfs_id"]) == {6513}
    assert not audit.causal_covariate_approved.any()
    assert not audit.pre_treatment_matching_approved.any()


def test_aggregated_context_roundtrips_every_official_excel_cell():
    books = json.loads((ROOT / "data_interim/municipality_additional_context/workbooks.json").read_text(encoding="utf8"))
    names = ["bfs_residential_property_price_index_quarter", "bfs_tourism_investments_tourist_municipalities_year",
             "bfs_tourism_investments_alpine_context_year", "bfs_tourism_satellite_national_context_year"]
    for name in names:
        frame = read(name)
        assert not frame.duplicated(["source_id","source_sheet","source_cell"]).any()
        assert "municipality_bfs_id" not in frame
        assert not frame.causal_covariate_approved.any()
        expected = []
        for row in frame.itertuples():
            col, line = re.fullmatch(r"([A-Z])(\d+)", row.source_cell).groups()
            token = books[row.source_id]["sheets"][row.source_sheet][int(line)-1][ord(col)-65]
            expected.append(float(token) if isinstance(token,(int,float)) else np.nan)
        np.testing.assert_allclose(frame.value.to_numpy(), expected, rtol=1e-14, equal_nan=True)
    price = read(names[0])
    assert len(price) == 684
    assert price.loc[price.year.eq(2019)&price.quarter.eq(4), "value"].eq(100).all()
    assert not price.municipality_mapping_approved.any()
    alpine = read(names[2])
    assert set(alpine.scope_id) == {"CH_TOURIST_MUNICIPALITIES_2020","CH_CANTON_GR","CH_CANTON_UR","CH_CANTON_VS"}
    assert alpine.source_token.eq("X").sum() == alpine.value.isna().sum()


def test_new_variable_provenance_is_registered():
    sources = pd.read_csv(ROOT / "metadata/data_sources_master.csv")
    dictionary = pd.read_csv(ROOT / "metadata/data_dictionary.csv")
    for name in ["municipality_typology_2020_snapshot_2026", "municipality_new_residential_buildings_year", "municipality_comparison_context_2026",
                 "municipality_new_buildings_cohort_baseline_audit", "bfs_residential_property_price_index_quarter",
                 "bfs_tourism_investments_tourist_municipalities_year", "bfs_tourism_investments_alpine_context_year", "bfs_tourism_satellite_national_context_year"]:
        definitions = dictionary[dictionary.table.eq(name)]
        assert set(definitions.variable) == set(read(name).columns)
        assert set(definitions.source_id) <= set(sources.source_id)
