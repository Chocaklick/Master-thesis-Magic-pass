"""Complete the local external-shock review of stage-20 strict controls.

The stage reviews the 17 controls still pending after the high-leverage audit.
It excludes a control only when positive source-backed evidence documents a
major competing shock. Surviving pairs remain candidates: basin spillovers and
parallel trends are still pending, and no causal flag is approved here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_remaining_control_external_shock_review.json"
EVIDENCE_CONFIG_PATH = ROOT / "config" / "evidence_sources.json"
PAIR_INPUT = ROOT / "data_processed" / "accessibility_comparison_high_leverage_control_external_risk_screen.csv"
CAPACITY_INPUT = ROOT / "data_processed" / "hotel_capacity_municipality_month.csv"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"

AUDIT_OUTPUT = ROOT / "reports" / "accessibility_remaining_control_external_shock_evidence.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_comparison_full_control_external_risk_screen.csv"
WORKLIST_OUTPUT = ROOT / "reports" / "accessibility_spillover_review_worklist.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_comparison_full_control_review_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "68_AUDIT_EXTERNE_CONTROLES_RESTANTS_FR.md"

ANCHOR = pd.Timestamp("2017-11-01")
WINDOW_START = pd.Timestamp("2015-11-01")
WINDOW_END = pd.Timestamp("2019-10-01")
EXPECTED_ALL_PAIRS = 70
EXPECTED_STAGE20_CANDIDATE_PAIRS = 28
EXPECTED_PENDING_CONTROLS = 17
EXPECTED_EXCLUDED_CONTROLS = 7
EXPECTED_RETAINED_CONTROLS = 10
EXPECTED_FINAL_CANDIDATE_PAIRS = 21


def as_bool(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower().eq("true").fillna(False)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pipe(values: list[str]) -> str:
    return "|".join(value for value in values if value)


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def latest_source_metadata(source_id: str) -> tuple[dict, Path]:
    candidates = []
    for path in sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json")):
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata.get("source_id") == source_id and metadata.get("http_status") == 200:
            candidates.append((metadata.get("retrieval_date", ""), metadata, path))
    if not candidates:
        raise FileNotFoundError(f"No successful immutable retrieval for {source_id}")
    _, metadata, path = max(candidates, key=lambda item: item[0])
    return metadata, path


def verify_sources(source_ids: list[str], catalog: dict[str, dict]) -> dict[str, object]:
    urls: list[str] = []
    raw_files: list[str] = []
    metadata_files: list[str] = []
    hashes: list[str] = []
    for source_id in source_ids:
        if source_id not in catalog:
            raise KeyError(f"Evidence source missing from catalog: {source_id}")
        metadata, metadata_path = latest_source_metadata(source_id)
        raw_relative = metadata.get("raw_file", "")
        raw_path = ROOT / raw_relative
        if not raw_relative or not raw_path.exists():
            raise FileNotFoundError(f"Cached source missing for {source_id}: {raw_relative}")
        actual_hash = sha256(raw_path)
        if actual_hash != metadata.get("sha256"):
            raise ValueError(f"SHA-256 mismatch for {source_id}")
        urls.append(catalog[source_id]["url"])
        raw_files.append(raw_relative.replace("\\", "/"))
        metadata_files.append(metadata_path.relative_to(ROOT).as_posix())
        hashes.append(f"{source_id}:{actual_hash}")
    return {
        "review_source_urls": pipe(urls),
        "review_local_files": pipe(raw_files),
        "review_source_metadata_files": pipe(metadata_files),
        "review_source_sha256": pipe(hashes),
        "review_source_integrity_status": "all_cited_sources_cached_and_sha256_verified",
        "all_cited_sources_integrity_verified": True,
    }


def capacity_peak(capacity: pd.DataFrame, municipality_id: int) -> dict[str, object]:
    subset = capacity[
        capacity.municipality_bfs_id.eq(municipality_id)
        & capacity.date.between(WINDOW_START, WINDOW_END)
    ].sort_values("date")
    values = subset.set_index("date").hotel_beds_available.astype(float)
    previous = values.shift(12, freq="MS")
    aligned = pd.concat([values.rename("current"), previous.rename("previous")], axis=1)
    aligned = aligned.loc[aligned.index.intersection(values.index)].dropna()
    aligned = aligned[aligned.previous.gt(0)]
    if aligned.empty:
        return {
            "largest_absolute_yoy_bed_change_date": "",
            "largest_absolute_yoy_bed_change_phase": "unavailable",
            "largest_yoy_bed_change_pct": np.nan,
            "largest_yoy_bed_change_current_beds": np.nan,
            "largest_yoy_bed_change_prior_year_beds": np.nan,
        }
    aligned["pct_change"] = aligned.current / aligned.previous - 1
    peak_date = aligned["pct_change"].abs().idxmax()
    peak = aligned.loc[peak_date]
    return {
        "largest_absolute_yoy_bed_change_date": peak_date.strftime("%Y-%m-%d"),
        "largest_absolute_yoy_bed_change_phase": "pre_anchor" if peak_date < ANCHOR else "post_anchor",
        "largest_yoy_bed_change_pct": float(peak["pct_change"]),
        "largest_yoy_bed_change_current_beds": float(peak.current),
        "largest_yoy_bed_change_prior_year_beds": float(peak.previous),
    }


def stage20_candidates(pairs: pd.DataFrame) -> pd.DataFrame:
    return pairs[as_bool(pairs.retained_in_strict_candidate_after_high_leverage_control_review)].copy()


def build_audit(pairs: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    candidates = stage20_candidates(pairs)
    pending = candidates[as_bool(candidates.strict_candidate_control_external_review_pending)].copy()
    counts = (
        pending.groupby(["control_municipality_bfs_id", "control_municipality_name"], as_index=False)
        .agg(
            strict_pair_count=("treated_municipality_bfs_id", "size"),
            strict_treated_municipality_count=("treated_municipality_bfs_id", "nunique"),
            strict_treated_municipality_names=(
                "treated_municipality_name", lambda values: pipe(sorted(set(values)))
            ),
        )
        .rename(columns={
            "control_municipality_bfs_id": "municipality_bfs_id",
            "control_municipality_name": "municipality_name",
        })
    )
    if len(counts) != EXPECTED_PENDING_CONTROLS or int(counts.strict_pair_count.sum()) != 17:
        raise ValueError("Expected 17 pending one-use strict controls")

    audit = pd.DataFrame(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    if len(audit) != EXPECTED_PENDING_CONTROLS or not audit.municipality_bfs_id.is_unique:
        raise ValueError("Remaining-control review must contain 17 unique municipalities")
    expected = counts[["municipality_bfs_id", "municipality_name"]].sort_values(
        "municipality_bfs_id", kind="stable"
    ).reset_index(drop=True)
    observed = audit[["municipality_bfs_id", "municipality_name"]].sort_values(
        "municipality_bfs_id", kind="stable"
    ).reset_index(drop=True)
    if expected.to_dict("records") != observed.to_dict("records"):
        raise ValueError("Configured controls do not match the stage-20 pending worklist")

    diagnostic_columns = [
        "control_municipality_bfs_id",
        "control_large_hotel_capacity_shift_warning",
        "control_hotel_capacity_warning_reasons",
        "control_pre_mean_hotel_beds_available",
        "control_post_mean_hotel_beds_available",
        "control_hotel_beds_mean_change_post_vs_pre_pct",
        "control_pre_mean_hotel_establishments_open",
        "control_post_mean_hotel_establishments_open",
        "control_hotel_establishments_mean_change_post_vs_pre_pct",
    ]
    diagnostics = pending[diagnostic_columns].drop_duplicates(
        "control_municipality_bfs_id"
    ).rename(columns={column: column.removeprefix("control_") for column in diagnostic_columns})
    audit = audit.merge(counts, on=["municipality_bfs_id", "municipality_name"], validate="one_to_one")
    audit = audit.merge(diagnostics, on="municipality_bfs_id", validate="one_to_one")

    catalog_rows = json.loads(EVIDENCE_CONFIG_PATH.read_text(encoding="utf-8"))
    catalog = {row["source_id"]: row for row in catalog_rows}
    source_fields = []
    capacity_fields = []
    for row in audit.itertuples(index=False):
        source_fields.append(verify_sources(list(row.source_ids), catalog))
        capacity_fields.append(capacity_peak(capacity, int(row.municipality_bfs_id)))
    audit = pd.concat(
        [audit.reset_index(drop=True), pd.DataFrame(source_fields), pd.DataFrame(capacity_fields)],
        axis=1,
    )
    audit["review_source_ids"] = audit.source_ids.apply(pipe)
    audit = audit.drop(columns="source_ids")
    audit["remaining_control_review_completed"] = True
    audit["retained_in_strict_candidate_after_review"] = audit.design_decision.str.startswith("retain_")
    audit["excluded_from_strict_candidate_by_review"] = ~audit.retained_in_strict_candidate_after_review
    audit["spillover_review_completed"] = False
    audit["causal_control_approved"] = False
    audit["external_review_source_id"] = "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW"
    return audit.sort_values("municipality_bfs_id", kind="stable")


def build_pair_screen(pairs: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "municipality_bfs_id", "review_status", "shock_severity", "shock_timing",
        "design_decision", "recommended_sensitivity", "review_source_ids",
        "remaining_control_review_completed", "retained_in_strict_candidate_after_review",
        "excluded_from_strict_candidate_by_review",
    ]
    selected = audit[fields].rename(columns={
        "municipality_bfs_id": "control_municipality_bfs_id",
        "review_status": "control_remaining_external_review_status",
        "shock_severity": "control_remaining_external_shock_severity",
        "shock_timing": "control_remaining_external_shock_timing",
        "design_decision": "control_remaining_external_design_decision",
        "recommended_sensitivity": "control_remaining_external_recommended_sensitivity",
        "review_source_ids": "control_remaining_external_review_source_ids",
        "retained_in_strict_candidate_after_review": "control_retained_after_remaining_review",
        "excluded_from_strict_candidate_by_review": "control_excluded_by_remaining_review",
    })
    out = pairs.merge(selected, on="control_municipality_bfs_id", how="left", validate="many_to_one")
    for column in [
        "remaining_control_review_completed", "control_retained_after_remaining_review",
        "control_excluded_by_remaining_review",
    ]:
        out[column] = as_bool(out[column])
    out["strict_candidate_before_remaining_control_review"] = as_bool(
        out.retained_in_strict_candidate_after_high_leverage_control_review
    )
    out["strict_candidate_excluded_by_remaining_control_review"] = (
        out.strict_candidate_before_remaining_control_review
        & out.remaining_control_review_completed
        & out.control_excluded_by_remaining_review
    )
    out["retained_in_strict_candidate_after_full_control_review"] = (
        out.strict_candidate_before_remaining_control_review
        & ~out.strict_candidate_excluded_by_remaining_control_review
    )
    out["control_external_review_completed_after_stage21"] = (
        as_bool(out.control_external_review_completed_after_stage20)
        | out.remaining_control_review_completed
    )
    out["strict_candidate_all_local_control_reviews_complete"] = (
        out.retained_in_strict_candidate_after_full_control_review
        & out.control_external_review_completed_after_stage21
    )
    out["visitor_market_spillover_review_completed_after_stage21"] = False
    out["causal_control_approved_after_stage21"] = False
    out["causal_pair_approved_after_stage21"] = False
    out["stage21_pair_decision"] = np.select(
        [
            ~out.strict_candidate_before_remaining_control_review,
            out.strict_candidate_excluded_by_remaining_control_review,
            out.strict_candidate_all_local_control_reviews_complete,
        ],
        [
            "outside_stage20_strict_candidate_set",
            "exclude_strict_pair_due_reviewed_control_shock",
            "retain_strict_candidate_local_control_review_complete_spillover_pending",
        ],
        default="unexpected_pending_local_control_review",
    )
    out["control_remaining_external_screen_source_id"] = (
        "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW"
    )
    if out.causal_pair_approved_after_stage21.any() or out.causal_control_approved_after_stage21.any():
        raise ValueError("Local control review must not grant causal approval")
    return out


def coalesced_review_sources(row: pd.Series) -> str:
    values = []
    for column in [
        "control_high_leverage_external_review_source_ids",
        "control_remaining_external_review_source_ids",
    ]:
        value = row.get(column)
        if pd.notna(value) and str(value):
            values.extend(str(value).split("|"))
    return pipe(list(dict.fromkeys(values)))


def build_spillover_worklist(pair_screen: pd.DataFrame) -> pd.DataFrame:
    retained = pair_screen[
        as_bool(pair_screen.retained_in_strict_candidate_after_full_control_review)
    ].copy()
    columns = [
        "treated_municipality_bfs_id", "treated_municipality_name", "first_exposure_month",
        "first_exposure_group_names", "control_municipality_bfs_id", "control_municipality_name",
        "comparability_rank", "treated_control_representative_distance_km",
        "treated_network_proximity_band", "control_network_proximity_band",
        "treated_current_scheduled_nearest_window_magic_group_minutes",
        "control_current_scheduled_nearest_window_magic_group_minutes",
        "strict_candidate_all_local_control_reviews_complete",
    ]
    worklist = retained[columns].copy()
    worklist["control_local_review_source_ids"] = retained.apply(coalesced_review_sources, axis=1)
    worklist["visitor_market_spillover_review_status"] = "pending"
    worklist["spillover_review_questions"] = (
        "shared_destination_or_marketing_area|shared_transport_catchment|"
        "same_day_trip_or_overnight_substitution|control_exposure_to_treated_station_groups"
    )
    worklist["parallel_trends_review_status"] = "pending"
    worklist["causal_pair_approved"] = False
    worklist["source_id"] = "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW"
    return worklist.sort_values(
        ["treated_municipality_name", "comparability_rank", "control_municipality_name"],
        kind="stable",
    )


def make_summary(audit: pd.DataFrame, pair_screen: pd.DataFrame, worklist: pd.DataFrame) -> dict[str, object]:
    before = as_bool(pair_screen.strict_candidate_before_remaining_control_review)
    excluded = as_bool(pair_screen.strict_candidate_excluded_by_remaining_control_review)
    retained = as_bool(pair_screen.retained_in_strict_candidate_after_full_control_review)
    completed = as_bool(pair_screen.strict_candidate_all_local_control_reviews_complete)
    return {
        "analysis_anchor": ANCHOR.date().isoformat(),
        "review_window_start": WINDOW_START.date().isoformat(),
        "review_window_end": WINDOW_END.date().isoformat(),
        "all_input_pairs": int(len(pair_screen)),
        "stage20_strict_candidate_pairs": int(before.sum()),
        "remaining_controls_reviewed": int(len(audit)),
        "remaining_controls_excluded": int(audit.excluded_from_strict_candidate_by_review.sum()),
        "remaining_controls_retained_with_qualified_sensitivity": int(
            audit.retained_in_strict_candidate_after_review.sum()
        ),
        "strict_pairs_excluded_by_remaining_control_review": int(excluded.sum()),
        "strict_candidate_pairs_after_full_local_control_review": int(retained.sum()),
        "strict_candidate_treated_municipalities_after_full_local_control_review": int(
            pair_screen.loc[retained, "treated_municipality_bfs_id"].nunique()
        ),
        "strict_candidate_controls_after_full_local_control_review": int(
            pair_screen.loc[retained, "control_municipality_bfs_id"].nunique()
        ),
        "surviving_pairs_with_all_local_control_reviews_complete": int(completed.sum()),
        "spillover_pairs_pending": int(len(worklist)),
        "reviewed_controls_with_verified_source_integrity": int(
            audit.all_cited_sources_integrity_verified.sum()
        ),
        "causal_controls_approved": 0,
        "causal_pairs_approved": 0,
        "input_sha256": {
            PAIR_INPUT.relative_to(ROOT).as_posix(): sha256(PAIR_INPUT),
            CAPACITY_INPUT.relative_to(ROOT).as_posix(): sha256(CAPACITY_INPUT),
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            EVIDENCE_CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(EVIDENCE_CONFIG_PATH),
        },
        "source_id": "DERIVED_ACCESSIBILITY_REMAINING_CONTROL_EXTERNAL_SHOCK_REVIEW",
        "interpretation": (
            "All surviving strict pairs now have a completed local control review. "
            "They remain candidates because basin spillovers and parallel trends are pending."
        ),
    }


def write_report(audit: pd.DataFrame, summary: dict[str, object]) -> None:
    short_reasons = {
        191: "ouverture d'une très grande salle événementielle dans la pré-période",
        230: "fusion tourisme-développement régional et financement dès 2018",
        938: "taxe de séjour passée de 2,50 à 3,50 CHF en 2019",
        1301: "programme de destination et financement public autour de l'ancrage",
        1322: "faibles dépenses touristiques communales; capacité stable",
        1407: "petite rénovation d'un hôtel début 2019",
        1504: "contribution touristique stable; capacité stable",
        2829: "revue officielle limitée; baisse graduelle de capacité",
        2831: "revue officielle limitée; capacité exactement stable",
        2939: "réouverture tardive d'un hôtel de neuf studios",
        3022: "nouvelle loi touristique cantonale et mandat marketing",
        3101: "offensive qualité et gestion de produits touristiques dès 2017",
        3311: "réorganisation touristique principale prévue pour 2020",
        4001: "nuitées 2018-2019 et capacité globalement stables",
        4401: "fermeture de l'Hotel Metropol en novembre 2016",
        4566: "programme d'attractivité surtout actif en fin de fenêtre",
        4671: "activation ciblée du centre culturel Kult-X",
    }
    sensitivities = {
        191: "garder seulement dans un ensemble large avec contrôle du calendrier de la salle",
        230: "ne pas utiliser comme témoin strict Magic-seul",
        938: "ne pas utiliser comme témoin strict sur toute la fenêtre postérieure",
        1301: "ne pas utiliser comme témoin strict Magic-seul",
        1322: "conserver les contrôles de capacité; la revue limitée ne prouve pas l'absence",
        1407: "couper la période postérieure à décembre 2018 ou retirer Sarnen",
        1504: "conserver les contrôles de capacité; la revue limitée ne prouve pas l'absence",
        2829: "conserver les contrôles de capacité; la revue limitée ne prouve pas l'absence",
        2831: "conserver les contrôles de capacité; la revue limitée ne prouve pas l'absence",
        2939: "couper la période postérieure à décembre 2018 ou retirer Schaffhausen",
        3022: "ne pas utiliser comme témoin strict Magic-seul",
        3101: "ne pas utiliser comme témoin strict Magic-seul",
        3311: "terminer la fenêtre en octobre 2019 et exclure toute extension en 2020",
        4001: "conserver les contrôles de capacité; la stabilité ne prouve pas l'absence",
        4401: "ne pas utiliser comme témoin strict autour de novembre 2017",
        4566: "terminer la fenêtre postérieure en août 2019 ou retirer Frauenfeld",
        4671: "présenter les résultats avec et sans Kreuzlingen",
    }
    lines = [
        "# Audit externe des contrôles restants - étape 21",
        "",
        "**Statut : revue locale terminée; validation causale non accordée.**",
        "",
        "## Résultat",
        "",
        f"Les {summary['remaining_controls_reviewed']} communes témoins encore en attente ont été examinées. "
        f"Sept sont exclues sur preuve positive d'un choc concurrent important et dix sont conservées avec une réserve ciblée.",
        "",
        f"Le noyau strict passe de **{summary['stage20_strict_candidate_pairs']} à "
        f"{summary['strict_candidate_pairs_after_full_local_control_review']} paires**, représentant "
        f"**{summary['strict_candidate_treated_municipalities_after_full_local_control_review']} communes traitées** "
        f"et **{summary['strict_candidate_controls_after_full_local_control_review']} témoins distincts**.",
        "",
        "Toutes les paires survivantes ont désormais une revue locale du témoin. Il reste cependant à examiner "
        "le bassin touristique partagé, les débordements possibles et les tendances parallèles. Aucune paire "
        "n'est donc encore approuvée causalement.",
        "",
        "## Décisions",
        "",
        "| Commune témoin | Décision | Motif court | Sensibilité / suite |",
        "|---|---|---|---|",
    ]
    for row in audit.itertuples(index=False):
        decision = "conserver avec réserve" if row.retained_in_strict_candidate_after_review else "exclure du noyau strict"
        lines.append(
            f"| {markdown_cell(row.municipality_name)} | {decision} | "
            f"{markdown_cell(short_reasons[int(row.municipality_bfs_id)])} | "
            f"{markdown_cell(sensitivities[int(row.municipality_bfs_id)])} |"
        )
    lines += [
        "",
        "## Règle appliquée",
        "",
        "Une commune n'est retirée que lorsqu'une source archivée documente un changement directement lié "
        "au tourisme, à l'hébergement ou à l'économie des visiteurs et suffisamment important ou proche de "
        "l'ancrage de novembre 2017. Les changements petits, indirects, tardifs ou hors fenêtre sont conservés "
        "avec un test de sensibilité explicite. Une recherche sans résultat ne vaut jamais preuve d'absence.",
        "",
        "Chaque source citée est conservée avec son URL, sa date de collecte, son fichier brut et son empreinte "
        "SHA-256. Les variations de lits et d'établissements complètent la revue documentaire sans être "
        "interprétées seules comme un effet causal.",
        "",
        "## Prochaine étape",
        "",
        f"Le fichier de travail contient les **{summary['spillover_pairs_pending']} paires survivantes**. Pour "
        "chacune, il faut vérifier si le témoin partage avec la commune traitée une destination touristique, "
        "un bassin de transport, des campagnes de promotion ou des substitutions de séjours. Ensuite seulement "
        "viendra le diagnostic formel des tendances parallèles.",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_remaining_control_external_shock_evidence.csv` : preuves, décisions et sensibilités des 17 témoins ;",
        "- `data_processed/accessibility_comparison_full_control_external_risk_screen.csv` : 70 paires avec le statut étape 21 ;",
        "- `reports/accessibility_spillover_review_worklist.csv` : 21 paires à examiner par bassin touristique ;",
        "- `reports/accessibility_comparison_full_control_review_summary.json` : compteurs et empreintes des entrées.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    pairs = pd.read_csv(PAIR_INPUT)
    capacity = pd.read_csv(CAPACITY_INPUT)
    capacity["date"] = pd.to_datetime(capacity.date, errors="raise")
    if len(pairs) != EXPECTED_ALL_PAIRS:
        raise ValueError(f"Expected {EXPECTED_ALL_PAIRS} input pairs")
    if len(stage20_candidates(pairs)) != EXPECTED_STAGE20_CANDIDATE_PAIRS:
        raise ValueError(f"Expected {EXPECTED_STAGE20_CANDIDATE_PAIRS} stage-20 candidates")

    audit = build_audit(pairs, capacity)
    pair_screen = build_pair_screen(pairs, audit)
    worklist = build_spillover_worklist(pair_screen)
    summary = make_summary(audit, pair_screen, worklist)
    expected = {
        "remaining_controls_excluded": EXPECTED_EXCLUDED_CONTROLS,
        "remaining_controls_retained_with_qualified_sensitivity": EXPECTED_RETAINED_CONTROLS,
        "strict_pairs_excluded_by_remaining_control_review": EXPECTED_EXCLUDED_CONTROLS,
        "strict_candidate_pairs_after_full_local_control_review": EXPECTED_FINAL_CANDIDATE_PAIRS,
        "surviving_pairs_with_all_local_control_reviews_complete": EXPECTED_FINAL_CANDIDATE_PAIRS,
        "spillover_pairs_pending": EXPECTED_FINAL_CANDIDATE_PAIRS,
    }
    for key, value in expected.items():
        if summary[key] != value:
            raise ValueError(f"Expected {key}={value}, got {summary[key]}")

    AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PAIR_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT_OUTPUT, index=False, lineterminator="\n")
    pair_screen.to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")
    worklist.to_csv(WORKLIST_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(audit, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
