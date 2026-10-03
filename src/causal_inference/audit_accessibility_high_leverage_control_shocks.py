"""Review external shocks for the seven most reused strict-control candidates.

The stage is deliberately incremental.  It removes only controls with positive,
source-backed major competing shocks, keeps qualified small or late changes as
sensitivity cases, and leaves all other controls pending.  No pair is causally
approved by this document review.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_high_leverage_control_external_shock_review.json"
EVIDENCE_CONFIG_PATH = ROOT / "config" / "evidence_sources.json"
PAIR_INPUT = ROOT / "data_processed" / "accessibility_comparison_treated_external_risk_screen.csv"
CAPACITY_INPUT = ROOT / "data_processed" / "hotel_capacity_municipality_month.csv"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"

AUDIT_OUTPUT = ROOT / "reports" / "accessibility_high_leverage_control_external_shock_evidence.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_comparison_high_leverage_control_external_risk_screen.csv"
WORKLIST_OUTPUT = ROOT / "reports" / "accessibility_remaining_control_external_review_worklist.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_comparison_high_leverage_control_review_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "67_AUDIT_EXTERNE_CONTROLES_PRIORITAIRES_FR.md"

ANCHOR = pd.Timestamp("2017-11-01")
WINDOW_START = pd.Timestamp("2015-11-01")
WINDOW_END = pd.Timestamp("2019-10-01")
EXPECTED_ALL_PAIRS = 70
EXPECTED_STRICT_PAIRS = 32
EXPECTED_HIGH_LEVERAGE_CONTROLS = 7
EXPECTED_REVIEWED_STRICT_PAIRS = 15


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


def strict_pairs(pairs: pd.DataFrame) -> pd.DataFrame:
    return pairs[as_bool(pairs.eligible_strict_magic_only_candidate_set)].copy()


def build_audit(pairs: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    strict = strict_pairs(pairs)
    counts = (
        strict.groupby(["control_municipality_bfs_id", "control_municipality_name"], as_index=False)
        .agg(
            strict_pair_count=("treated_municipality_bfs_id", "size"),
            strict_treated_municipality_count=("treated_municipality_bfs_id", "nunique"),
            strict_treated_municipality_names=(
                "treated_municipality_name", lambda values: pipe(sorted(set(values)))
            ),
        )
    )
    high_leverage = counts[counts.strict_pair_count.ge(2)].copy()
    if len(high_leverage) != EXPECTED_HIGH_LEVERAGE_CONTROLS:
        raise ValueError("Expected seven controls reused in at least two strict pairs")

    review_rows = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    audit = pd.DataFrame(review_rows)
    if len(audit) != EXPECTED_HIGH_LEVERAGE_CONTROLS or not audit.municipality_bfs_id.is_unique:
        raise ValueError("Control-review config must contain seven unique municipalities")

    expected = high_leverage[["control_municipality_bfs_id", "control_municipality_name"]].rename(
        columns={
            "control_municipality_bfs_id": "municipality_bfs_id",
            "control_municipality_name": "municipality_name",
        }
    ).sort_values("municipality_bfs_id", kind="stable")
    observed = audit[["municipality_bfs_id", "municipality_name"]].sort_values(
        "municipality_bfs_id", kind="stable"
    )
    if expected.reset_index(drop=True).to_dict("records") != observed.reset_index(drop=True).to_dict("records"):
        raise ValueError("Configured controls do not match the seven high-leverage strict controls")

    count_fields = high_leverage.rename(columns={
        "control_municipality_bfs_id": "municipality_bfs_id",
        "control_municipality_name": "municipality_name",
    })
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
    diagnostics = strict[diagnostic_columns].drop_duplicates("control_municipality_bfs_id").rename(
        columns={column: column.removeprefix("control_") for column in diagnostic_columns}
    )
    audit = audit.merge(count_fields, on=["municipality_bfs_id", "municipality_name"], validate="one_to_one")
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
    audit["high_leverage_control_review_completed"] = True
    audit["retained_in_strict_candidate_after_review"] = audit.design_decision.str.startswith("retain_")
    audit["excluded_from_strict_candidate_by_review"] = ~audit.retained_in_strict_candidate_after_review
    audit["spillover_review_completed"] = False
    audit["causal_control_approved"] = False
    audit["external_review_source_id"] = "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW"
    return audit.sort_values("municipality_bfs_id", kind="stable")


def build_pair_screen(pairs: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "municipality_bfs_id", "review_status", "shock_severity", "shock_timing",
        "design_decision", "recommended_sensitivity", "review_source_ids",
        "high_leverage_control_review_completed", "retained_in_strict_candidate_after_review",
        "excluded_from_strict_candidate_by_review",
    ]
    selected = audit[fields].rename(columns={
        "municipality_bfs_id": "control_municipality_bfs_id",
        "review_status": "control_high_leverage_external_review_status",
        "shock_severity": "control_high_leverage_external_shock_severity",
        "shock_timing": "control_high_leverage_external_shock_timing",
        "design_decision": "control_high_leverage_external_design_decision",
        "recommended_sensitivity": "control_high_leverage_external_recommended_sensitivity",
        "review_source_ids": "control_high_leverage_external_review_source_ids",
        "retained_in_strict_candidate_after_review": "control_retained_in_strict_candidate_after_review",
        "excluded_from_strict_candidate_by_review": "control_excluded_from_strict_candidate_by_review",
    })
    out = pairs.merge(selected, on="control_municipality_bfs_id", how="left", validate="many_to_one")
    out["high_leverage_control_review_completed"] = as_bool(
        out.high_leverage_control_review_completed
    )
    out["control_retained_in_strict_candidate_after_review"] = as_bool(
        out.control_retained_in_strict_candidate_after_review
    )
    out["control_excluded_from_strict_candidate_by_review"] = as_bool(
        out.control_excluded_from_strict_candidate_by_review
    )
    out["strict_candidate_before_high_leverage_control_review"] = as_bool(
        out.eligible_strict_magic_only_candidate_set
    )
    out["strict_candidate_excluded_by_high_leverage_control_review"] = (
        out.strict_candidate_before_high_leverage_control_review
        & out.high_leverage_control_review_completed
        & out.control_excluded_from_strict_candidate_by_review
    )
    out["retained_in_strict_candidate_after_high_leverage_control_review"] = (
        out.strict_candidate_before_high_leverage_control_review
        & ~out.strict_candidate_excluded_by_high_leverage_control_review
    )
    out["strict_candidate_control_external_reviewed_and_retained"] = (
        out.retained_in_strict_candidate_after_high_leverage_control_review
        & out.high_leverage_control_review_completed
    )
    out["strict_candidate_control_external_review_pending"] = (
        out.retained_in_strict_candidate_after_high_leverage_control_review
        & ~out.high_leverage_control_review_completed
    )
    out["control_external_review_completed_after_stage20"] = (
        as_bool(out.control_external_review_completed)
        | out.high_leverage_control_review_completed
    )
    out["causal_control_approved_after_stage20"] = False
    out["causal_pair_approved_after_stage20"] = False
    out["stage20_pair_decision"] = np.select(
        [
            ~out.strict_candidate_before_high_leverage_control_review,
            out.strict_candidate_excluded_by_high_leverage_control_review,
            out.strict_candidate_control_external_reviewed_and_retained,
            out.strict_candidate_control_external_review_pending,
        ],
        [
            "outside_stage19_strict_candidate_set",
            "exclude_strict_pair_due_reviewed_control_shock",
            "retain_strict_candidate_reviewed_control_spillover_still_pending",
            "retain_strict_candidate_control_external_review_pending",
        ],
        default="not_applicable",
    )
    out["control_high_leverage_external_screen_source_id"] = (
        "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW"
    )
    if out.causal_pair_approved_after_stage20.any() or out.causal_control_approved_after_stage20.any():
        raise ValueError("Control document review must not grant causal approval")
    return out


def build_remaining_worklist(pair_screen: pd.DataFrame) -> pd.DataFrame:
    pending = pair_screen[as_bool(pair_screen.strict_candidate_control_external_review_pending)].copy()
    worklist = (
        pending.groupby(["control_municipality_bfs_id", "control_municipality_name"], as_index=False)
        .agg(
            strict_candidate_pair_count=("treated_municipality_bfs_id", "size"),
            treated_municipality_count=("treated_municipality_bfs_id", "nunique"),
            treated_municipality_names=(
                "treated_municipality_name", lambda values: pipe(sorted(set(values)))
            ),
            internal_capacity_warning=("control_large_hotel_capacity_shift_warning", "max"),
            internal_capacity_warning_reasons=(
                "control_hotel_capacity_warning_reasons",
                lambda values: pipe(sorted({str(value) for value in values if pd.notna(value)})),
            ),
            minimum_comparability_rank=("comparability_rank", "min"),
        )
    )
    worklist["external_local_shock_review_status"] = "pending"
    worklist["visitor_market_spillover_review_status"] = "pending"
    worklist["causal_control_approved"] = False
    worklist["source_id"] = "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW"
    return worklist.sort_values(
        ["strict_candidate_pair_count", "control_municipality_name"],
        ascending=[False, True], kind="stable",
    )


def make_summary(audit: pd.DataFrame, pair_screen: pd.DataFrame, worklist: pd.DataFrame) -> dict[str, object]:
    strict_before = as_bool(pair_screen.strict_candidate_before_high_leverage_control_review)
    reviewed = strict_before & as_bool(pair_screen.high_leverage_control_review_completed)
    excluded = as_bool(pair_screen.strict_candidate_excluded_by_high_leverage_control_review)
    retained = as_bool(pair_screen.retained_in_strict_candidate_after_high_leverage_control_review)
    pending = as_bool(pair_screen.strict_candidate_control_external_review_pending)
    reviewed_retained = as_bool(pair_screen.strict_candidate_control_external_reviewed_and_retained)
    return {
        "analysis_anchor": ANCHOR.date().isoformat(),
        "review_window_start": WINDOW_START.date().isoformat(),
        "review_window_end": WINDOW_END.date().isoformat(),
        "all_input_pairs": int(len(pair_screen)),
        "stage19_strict_candidate_pairs": int(strict_before.sum()),
        "stage19_strict_candidate_controls": int(pair_screen.loc[strict_before, "control_municipality_bfs_id"].nunique()),
        "high_leverage_controls_reviewed": int(len(audit)),
        "strict_pairs_covered_by_high_leverage_review": int(reviewed.sum()),
        "reviewed_controls_excluded_from_strict_candidate": int(audit.excluded_from_strict_candidate_by_review.sum()),
        "strict_pairs_excluded_by_high_leverage_control_review": int(excluded.sum()),
        "reviewed_controls_retained_with_qualified_sensitivity": int(audit.retained_in_strict_candidate_after_review.sum()),
        "strict_pairs_with_reviewed_retained_high_leverage_control": int(reviewed_retained.sum()),
        "strict_candidate_pairs_after_high_leverage_control_review": int(retained.sum()),
        "strict_candidate_treated_municipalities_after_high_leverage_control_review": int(
            pair_screen.loc[retained, "treated_municipality_bfs_id"].nunique()
        ),
        "strict_candidate_controls_after_high_leverage_control_review": int(
            pair_screen.loc[retained, "control_municipality_bfs_id"].nunique()
        ),
        "remaining_control_reviews": int(len(worklist)),
        "strict_candidate_pairs_with_control_review_pending": int(pending.sum()),
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
        "source_id": "DERIVED_ACCESSIBILITY_HIGH_LEVERAGE_CONTROL_EXTERNAL_SHOCK_REVIEW",
        "interpretation": (
            "Incremental external-shock triage only. Surviving pairs remain candidates; "
            "unreviewed controls, visitor-market spillovers and parallel-trend diagnostics are pending."
        ),
    }


def write_report(audit: pd.DataFrame, worklist: pd.DataFrame, summary: dict[str, object]) -> None:
    labels = {
        1024: "Aucun choc majeur repéré dans le rapport communal; capacité quasi stable.",
        1068: "Programme touristique dès 2019: conserver seulement avec une sensibilité coupant 2019.",
        1103: "Ouverture en 2019 du FOCUS Hotel (64 chambres): exclusion du noyau strict.",
        3216: "Seulement un petit écart budgétaire touristique lié à l'impression; capacité en baisse graduelle.",
        3298: "Rénovation en 2018 d'un hôtel de 7 chambres: conserver avec test sans Walenstadt.",
        3953: "Engagement de 10,1 M CHF pour le Heididorf annoncé le 2 novembre 2017: exclusion stricte.",
        4201: "Ouverture pré-ancrage d'un hôtel de 7 chambres: conserver avec test sans Lenzburg.",
    }
    lines = [
        "# Audit externe des contrôles prioritaires - étape 20",
        "",
        "**Statut : screening incrémental, pas validation causale.**",
        "",
        "## Résultat",
        "",
        f"Les 7 communes témoins les plus réutilisées couvrent {summary['strict_pairs_covered_by_high_leverage_review']} "
        f"des {summary['stage19_strict_candidate_pairs']} paires du noyau strict précédent.",
        "",
        f"- **2 contrôles exclus** : Sursee et Maienfeld, soit "
        f"**{summary['strict_pairs_excluded_by_high_leverage_control_review']} paires retirées** ;",
        f"- **5 contrôles conservés avec réserves ciblées**, soit "
        f"**{summary['strict_pairs_with_reviewed_retained_high_leverage_control']} paires revues et conservées** ;",
        f"- le noyau candidat passe de **32 à {summary['strict_candidate_pairs_after_high_leverage_control_review']} paires** ;",
        f"- il reste **{summary['remaining_control_reviews']} contrôles / "
        f"{summary['strict_candidate_pairs_with_control_review_pending']} paires** à documenter.",
        "",
        "Les 7 communes traitées restent représentées. Aucune paire n'est encore approuvée causalement : "
        "les contrôles restants, les bassins touristiques et les tendances parallèles doivent encore être examinés.",
        "",
        "## Décisions par contrôle",
        "",
        "| Contrôle | Paires strictes | Décision | Motif court | Sources |",
        "|---|---:|---|---|---|",
    ]
    for row in audit.itertuples(index=False):
        decision = "conserver avec sensibilité" if row.retained_in_strict_candidate_after_review else "exclure du noyau strict"
        lines.append(
            f"| {markdown_cell(row.municipality_name)} | {row.strict_pair_count} | {decision} | "
            f"{markdown_cell(labels[int(row.municipality_bfs_id)])} | {markdown_cell(row.review_source_ids)} |"
        )
    lines += [
        "",
        "## Pourquoi Sursee et Maienfeld sont retirés",
        "",
        "Sursee connaît une modification directe du mécanisme de mesure : un hôtel de 64 chambres ouvre pendant "
        "la fenêtre postérieure et la plus forte hausse annuelle des lits survient en juin 2019. Maienfeld reçoit, "
        "le 2 novembre 2017, un engagement public pour une extension touristique de 10,1 millions de francs du "
        "Heididorf, qualifiée d'infrastructure d'importance systémique. Dans les deux cas, garder la commune comme "
        "témoin strict rendrait l'interprétation Magic-Pass-seul trop fragile.",
        "",
        "## Contrôles encore à examiner",
        "",
        "| Contrôle | Paires | Communes traitées | Alerte interne capacité |",
        "|---|---:|---|---|",
    ]
    for row in worklist.itertuples(index=False):
        warning = row.internal_capacity_warning_reasons or "aucune alerte mécanique"
        lines.append(
            f"| {markdown_cell(row.control_municipality_name)} | {row.strict_candidate_pair_count} | "
            f"{markdown_cell(row.treated_municipality_names)} | {markdown_cell(warning)} |"
        )
    lines += [
        "",
        "## Méthode et limites",
        "",
        "La priorité est purement opérationnelle : revue d'abord des contrôles utilisés dans au moins deux paires. "
        "Chaque preuve positive est archivée avec URL, date et SHA-256. Les variations de capacité hôtelière "
        "complètent les documents sans être interprétées seules comme causalité. Une recherche sans résultat ne "
        "prouve jamais l'absence d'un choc.",
        "",
        "Les décisions sont volontairement asymétriques : un grand choc documenté suffit à exclure un contrôle "
        "du noyau strict; une petite rénovation ou un programme tardif peut être conservé uniquement avec la "
        "sensibilité indiquée. La proximité réseau actuelle ne valide pas un bassin touristique historique.",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_high_leverage_control_external_shock_evidence.csv` : preuve et décision pour les 7 contrôles ;",
        "- `data_processed/accessibility_comparison_high_leverage_control_external_risk_screen.csv` : 70 paires avec le statut étape 20 ;",
        "- `reports/accessibility_remaining_control_external_review_worklist.csv` : les 17 contrôles restants ;",
        "- `reports/accessibility_comparison_high_leverage_control_review_summary.json` : compteurs et empreintes.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    pairs = pd.read_csv(PAIR_INPUT)
    capacity = pd.read_csv(CAPACITY_INPUT)
    capacity["date"] = pd.to_datetime(capacity.date, errors="raise")
    if len(pairs) != EXPECTED_ALL_PAIRS:
        raise ValueError(f"Expected {EXPECTED_ALL_PAIRS} input pairs")
    if len(strict_pairs(pairs)) != EXPECTED_STRICT_PAIRS:
        raise ValueError(f"Expected {EXPECTED_STRICT_PAIRS} stage-19 strict pairs")

    audit = build_audit(pairs, capacity)
    if int(audit.strict_pair_count.sum()) != EXPECTED_REVIEWED_STRICT_PAIRS:
        raise ValueError(f"Expected {EXPECTED_REVIEWED_STRICT_PAIRS} reviewed strict pairs")
    pair_screen = build_pair_screen(pairs, audit)
    worklist = build_remaining_worklist(pair_screen)
    summary = make_summary(audit, pair_screen, worklist)
    expected = {
        "strict_pairs_excluded_by_high_leverage_control_review": 4,
        "strict_pairs_with_reviewed_retained_high_leverage_control": 11,
        "strict_candidate_pairs_after_high_leverage_control_review": 28,
        "remaining_control_reviews": 17,
        "strict_candidate_pairs_with_control_review_pending": 17,
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
    write_report(audit, worklist, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
