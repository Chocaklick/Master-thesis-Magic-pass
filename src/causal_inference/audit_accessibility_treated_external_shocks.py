"""Audit external shocks for the 14 retained accessibility treatments.

This stage reviews documented municipality/destination interventions around the
November 2017 first-exposure anchor.  It creates nested analysis sets rather
than converting document review into a causal approval:

* broad reviewed set: excludes high direct concurrent shocks;
* strict Magic-only candidate set: also excludes moderate direct interventions.

All comparisons still require the pending control and visitor-market review.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "accessibility_treated_external_shock_review.json"
EVIDENCE_CONFIG_PATH = ROOT / "config" / "evidence_sources.json"
PAIR_INPUT = ROOT / "data_processed" / "accessibility_comparison_internal_risk_screen.csv"
CAPACITY_INPUT = ROOT / "data_processed" / "hotel_capacity_municipality_month.csv"
EVIDENCE_DIR = ROOT / "data_external" / "source_evidence"

AUDIT_OUTPUT = ROOT / "reports" / "accessibility_treated_external_shock_evidence.csv"
PAIR_OUTPUT = ROOT / "data_processed" / "accessibility_comparison_treated_external_risk_screen.csv"
SUMMARY_OUTPUT = ROOT / "reports" / "accessibility_comparison_treated_external_review_summary.json"
REPORT_OUTPUT = ROOT / "reports" / "66_AUDIT_EXTERNE_COMMUNES_TRAITEES_FR.md"

ANCHOR = pd.Timestamp("2017-11-01")
WINDOW_START = pd.Timestamp("2015-11-01")
WINDOW_END = pd.Timestamp("2019-10-01")
EXPECTED_TREATMENTS = 14
EXPECTED_PAIRS = 70
EXPECTED_STAGE18_RETAINED_PAIRS = 50


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.strip().str.lower().eq("true")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pipe(values: list[str]) -> str:
    return "|".join(value for value in values if value)


def markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def latest_source_metadata(source_id: str) -> tuple[dict, Path]:
    candidates = sorted(EVIDENCE_DIR.glob(f"{source_id}_*.metadata.json"))
    if not candidates:
        raise FileNotFoundError(f"No immutable metadata sidecar for {source_id}")
    records = []
    for path in candidates:
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata.get("source_id") == source_id and metadata.get("http_status") == 200:
            records.append((metadata.get("retrieval_date", ""), metadata, path))
    if not records:
        raise ValueError(f"No successful immutable retrieval for {source_id}")
    _, metadata, path = max(records, key=lambda item: item[0])
    return metadata, path


def verify_sources(source_ids: list[str], catalog: dict[str, dict]) -> dict[str, str | bool]:
    if not source_ids:
        return {
            "review_source_urls": "",
            "review_local_files": "",
            "review_source_metadata_files": "",
            "review_source_sha256": "",
            "review_source_integrity_status": "not_applicable_no_negative_proof_source",
            "all_cited_sources_integrity_verified": True,
        }
    urls: list[str] = []
    raw_files: list[str] = []
    metadata_files: list[str] = []
    hashes: list[str] = []
    for source_id in source_ids:
        if source_id not in catalog:
            raise KeyError(f"Evidence source missing from config/evidence_sources.json: {source_id}")
        metadata, metadata_path = latest_source_metadata(source_id)
        raw_relative = metadata.get("raw_file", "")
        raw_path = ROOT / raw_relative
        if not raw_relative or not raw_path.exists():
            raise FileNotFoundError(f"Cached source missing for {source_id}: {raw_relative}")
        actual_hash = sha256(raw_path)
        expected_hash = metadata.get("sha256", "")
        if actual_hash != expected_hash:
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
    ].sort_values("date").copy()
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
        "largest_absolute_yoy_bed_change_phase": (
            "pre_anchor" if peak_date < ANCHOR else "post_anchor"
        ),
        "largest_yoy_bed_change_pct": float(peak["pct_change"]),
        "largest_yoy_bed_change_current_beds": float(peak.current),
        "largest_yoy_bed_change_prior_year_beds": float(peak.previous),
    }


def build_audit(pairs: pd.DataFrame, capacity: pd.DataFrame) -> pd.DataFrame:
    review_rows = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    catalog_rows = json.loads(EVIDENCE_CONFIG_PATH.read_text(encoding="utf-8"))
    catalog = {row["source_id"]: row for row in catalog_rows}
    audit = pd.DataFrame(review_rows)
    if len(audit) != EXPECTED_TREATMENTS or not audit.municipality_bfs_id.is_unique:
        raise ValueError("The treated external-shock config must contain 14 unique municipalities")

    expected = pairs[["treated_municipality_bfs_id", "treated_municipality_name"]].drop_duplicates()
    expected = expected.rename(columns={
        "treated_municipality_bfs_id": "municipality_bfs_id",
        "treated_municipality_name": "municipality_name",
    }).sort_values("municipality_bfs_id", kind="stable")
    observed = audit[["municipality_bfs_id", "municipality_name"]].sort_values(
        "municipality_bfs_id", kind="stable"
    )
    if expected.reset_index(drop=True).to_dict("records") != observed.reset_index(drop=True).to_dict("records"):
        raise ValueError("Configured municipalities do not exactly match the 14 treated municipalities")

    treated_internal = pairs[[
        "treated_municipality_bfs_id",
        "treated_large_hotel_capacity_shift_warning",
        "treated_hotel_capacity_warning_reasons",
        "treated_pre_mean_hotel_beds_available",
        "treated_post_mean_hotel_beds_available",
        "treated_hotel_beds_mean_change_post_vs_pre_pct",
    ]].drop_duplicates("treated_municipality_bfs_id").rename(columns={
        "treated_municipality_bfs_id": "municipality_bfs_id",
        "treated_large_hotel_capacity_shift_warning": "internal_large_hotel_capacity_shift_warning",
        "treated_hotel_capacity_warning_reasons": "internal_hotel_capacity_warning_reasons",
        "treated_pre_mean_hotel_beds_available": "pre_mean_hotel_beds_available",
        "treated_post_mean_hotel_beds_available": "post_mean_hotel_beds_available",
        "treated_hotel_beds_mean_change_post_vs_pre_pct": "hotel_beds_mean_change_post_vs_pre_pct",
    })
    audit = audit.merge(treated_internal, on="municipality_bfs_id", validate="one_to_one")

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
    audit["external_treatment_review_completed"] = True
    audit["eligible_broad_reviewed_set"] = ~audit.design_decision.eq(
        "exclude_broad_and_strict_magic_only_sets"
    )
    audit["eligible_strict_magic_only_candidate_set"] = audit.design_decision.str.startswith(
        "retain_broad_and_strict"
    )
    audit["descriptive_combined_intervention_usable"] = True
    audit["causal_treatment_approved"] = False
    audit["external_review_source_id"] = (
        "DERIVED_ACCESSIBILITY_TREATED_EXTERNAL_SHOCK_REVIEW"
    )
    audit = audit.sort_values("municipality_bfs_id", kind="stable")
    if audit.causal_treatment_approved.any():
        raise ValueError("Document review must not approve causal treatments")
    return audit


def build_pair_screen(pairs: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    selected = audit[[
        "municipality_bfs_id", "review_status", "shock_severity", "shock_timing",
        "design_decision", "recommended_sensitivity", "review_source_ids",
        "external_treatment_review_completed", "eligible_broad_reviewed_set",
        "eligible_strict_magic_only_candidate_set",
    ]].rename(columns={
        "municipality_bfs_id": "treated_municipality_bfs_id",
        "review_status": "treated_external_review_status",
        "shock_severity": "treated_external_shock_severity",
        "shock_timing": "treated_external_shock_timing",
        "design_decision": "treated_external_design_decision",
        "recommended_sensitivity": "treated_external_recommended_sensitivity",
        "review_source_ids": "treated_external_review_source_ids",
        "external_treatment_review_completed": "treated_external_review_completed",
        "eligible_broad_reviewed_set": "treated_eligible_broad_reviewed_set",
        "eligible_strict_magic_only_candidate_set": "treated_eligible_strict_magic_only_candidate_set",
    })
    result = pairs.merge(selected, on="treated_municipality_bfs_id", validate="many_to_one")
    stage18_retained = as_bool(result.retained_for_external_review)
    result["eligible_broad_reviewed_comparison_set"] = (
        stage18_retained & as_bool(result.treated_eligible_broad_reviewed_set)
    )
    result["eligible_strict_magic_only_candidate_set"] = (
        stage18_retained & as_bool(result.treated_eligible_strict_magic_only_candidate_set)
    )
    result["eligible_descriptive_after_internal_control_screen"] = stage18_retained
    result["stage19_pair_decision"] = np.select(
        [
            ~stage18_retained,
            ~as_bool(result.treated_eligible_broad_reviewed_set),
            ~as_bool(result.treated_eligible_strict_magic_only_candidate_set),
        ],
        [
            "deferred_by_stage18_control_or_proximity_screen",
            "descriptive_only_high_treated_concurrent_shock",
            "broad_sensitivity_only_moderate_treated_concurrent_shock",
        ],
        default="strict_magic_only_candidate_pending_control_external_review",
    )
    result["control_external_review_completed"] = result[
        "control_existing_external_shock_exact_anchor"
    ].fillna(False).astype(bool)
    result["parallel_trends_approved"] = False
    result["causal_treatment_approved"] = False
    result["causal_control_approved"] = False
    result["causal_pair_approved"] = False
    result["treated_external_screen_source_id"] = (
        "DERIVED_ACCESSIBILITY_TREATED_EXTERNAL_SHOCK_REVIEW"
    )
    if result[[
        "parallel_trends_approved", "causal_treatment_approved",
        "causal_control_approved", "causal_pair_approved",
    ]].any().any():
        raise ValueError("Stage 19 must not approve causal comparisons")
    return result.sort_values(
        ["treated_municipality_bfs_id", "comparability_rank"], kind="stable"
    )


def make_summary(audit: pd.DataFrame, pairs: pd.DataFrame) -> dict:
    broad = as_bool(pairs.eligible_broad_reviewed_comparison_set)
    strict = as_bool(pairs.eligible_strict_magic_only_candidate_set)
    stage18 = as_bool(pairs.retained_for_external_review)
    return {
        "analysis_date": date.today().isoformat(),
        "analysis_anchor": ANCHOR.date().isoformat(),
        "review_window": {
            "start": WINDOW_START.date().isoformat(),
            "end": WINDOW_END.date().isoformat(),
        },
        "treated_municipalities_reviewed": int(len(audit)),
        "treated_reviews_with_cached_cited_sources": int(audit.review_source_ids.ne("").sum()),
        "treated_reviews_without_negative_proof_source": int(audit.review_source_ids.eq("").sum()),
        "stage18_pairs_retained_for_external_review": int(stage18.sum()),
        "broad_reviewed_set_pairs": int(broad.sum()),
        "broad_reviewed_set_treated_municipalities": int(
            pairs.loc[broad, "treated_municipality_bfs_id"].nunique()
        ),
        "strict_magic_only_candidate_pairs": int(strict.sum()),
        "strict_magic_only_candidate_treated_municipalities": int(
            pairs.loc[strict, "treated_municipality_bfs_id"].nunique()
        ),
        "high_direct_concurrent_treatments_excluded_from_broad_set": int(
            (~as_bool(audit.eligible_broad_reviewed_set)).sum()
        ),
        "moderate_direct_treatments_retained_only_in_broad_set": int((
            as_bool(audit.eligible_broad_reviewed_set)
            & ~as_bool(audit.eligible_strict_magic_only_candidate_set)
        ).sum()),
        "all_treatments_descriptively_usable": bool(
            as_bool(audit.descriptive_combined_intervention_usable).all()
        ),
        "control_external_reviews_completed_for_retained_pairs": int(
            as_bool(pairs.loc[stage18, "control_external_review_completed"]).sum()
        ),
        "control_external_reviews_still_pending_for_retained_pairs": int(
            (~as_bool(pairs.loc[stage18, "control_external_review_completed"])).sum()
        ),
        "parallel_trends_approved": False,
        "causal_pairs_approved": 0,
        "decision_counts": audit.design_decision.value_counts().sort_index().to_dict(),
        "input_sha256": {
            CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(CONFIG_PATH),
            EVIDENCE_CONFIG_PATH.relative_to(ROOT).as_posix(): sha256(EVIDENCE_CONFIG_PATH),
            PAIR_INPUT.relative_to(ROOT).as_posix(): sha256(PAIR_INPUT),
            CAPACITY_INPUT.relative_to(ROOT).as_posix(): sha256(CAPACITY_INPUT),
        },
    }


def write_report(audit: pd.DataFrame, summary: dict) -> None:
    note_fr = {
        355: "Aucun choc touristique communal majeur n'a été identifié dans la revue officielle limitée. L'alerte de capacité hôtelière culmine avant novembre 2017.",
        843: "Gstaad/Saanen est aussi exposée au pass Top4 dès l'automne 2017, exactement au moment de l'entrée dans Magic Pass.",
        2121: "Le contexte stratégique des Préalpes fribourgeoises est documenté, sans rupture opérationnelle propre à Haut-Intyamon dans les sources examinées.",
        2125: "Bulle mène dès 2018-2019 un travail d'identité et de statut touristique, mais les documents décrivent surtout une démarche de politique et de marque.",
        2135: "La stratégie régionale couvre directement l'opérateur de Moléson et peut toucher le bassin de Gruyères, sans rupture communale unique clairement datée.",
        2196: "L'auberge de jeunesse ferme en novembre 2016 et n'est pas remplacée en 2019; ce changement précède l'ancrage mais affecte la structure d'hébergement.",
        2299: "La commune approuve en avril 2019 une nouvelle société touristique intégrant les offres existantes et de nouveaux produits; le choc est direct mais tardif.",
        5407: "Leysin finance une nouvelle remontée Fer-Brion-Tête d'Aï puis des travaux d'enneigement mécanique pendant la fenêtre étudiée.",
        5409: "Les Bains de Villars rénovés et leur espace wellness ouvrent en août 2017, juste avant l'ancrage; le projet représente environ CHF 18,5 millions.",
        5411: "La commune garantit la télécabine Vioz-Mazots et les travaux de la Jorasse; le Meilleret est aussi adapté pour Lausanne 2020.",
        5841: "Après les difficultés de l'exploitant et la fin d'une subvention annuelle de CHF 350'000, la vente des actifs de La Braye pour CHF 1 est proposée en 2018.",
        6252: "Des outils numériques, du marketing et de nouveaux produits outdoor sont financés en 2017-2019, en même temps que l'exposition Magic Pass.",
        6421: "Un consortium est retenu pour un futur hôtel à l'automne 2019, mais le rapport ne montre pas une mise en exploitation dans la fenêtre étudiée.",
        6757: "La célébration Jura 40 attire ponctuellement des milliers de visiteurs en juin 2019; il s'agit d'un événement concentré sur un mois.",
    }
    sensitivity_fr = {
        355: "Conserver les contrôles de capacité et signaler le pic pré-ancrage.",
        843: "Usage descriptif ou exposition combinée Magic Pass–Top4 seulement.",
        2121: "Tester des erreurs ou effets fixes au niveau régional si l'échantillon le permet.",
        2125: "Comparer les résultats avec et sans les mois de 2019.",
        2135: "Tester une robustesse au regroupement régional et aux capacités hôtelières.",
        2196: "Recommencer la pré-tendance après novembre 2016 ou retirer les mois antérieurs.",
        2299: "Tronquer la période postérieure à décembre 2018 et comparer à la fenêtre complète.",
        5407: "Usage descriptif ou analyse d'intervention combinée seulement.",
        5409: "Usage descriptif ou analyse d'intervention combinée seulement.",
        5411: "Usage descriptif ou analyse d'intervention combinée seulement.",
        5841: "Usage descriptif ou analyse combinée avec restructuration de l'exploitant.",
        6252: "Traiter comme intervention combinée ou retirer du noyau Magic Pass seul.",
        6421: "Vérifier la date d'ouverture avant de prolonger la fenêtre après octobre 2019.",
        6757: "Réestimer après exclusion de juin 2019.",
    }
    pair_counts = {
        int(row.municipality_bfs_id): int(row.retained_pair_count)
        for row in pd.read_csv(ROOT / "reports" / "accessibility_comparison_external_review_worklist.csv")
        .query("entity_role == 'historically_retained_treated_municipality'")
        .itertuples(index=False)
    }
    audit = audit.copy()
    audit["retained_pair_count"] = audit.municipality_bfs_id.map(pair_counts)
    strong = audit[~as_bool(audit.eligible_broad_reviewed_set)]
    moderate = audit[
        as_bool(audit.eligible_broad_reviewed_set)
        & ~as_bool(audit.eligible_strict_magic_only_candidate_set)
    ]
    retained = audit[as_bool(audit.eligible_strict_magic_only_candidate_set)]

    lines = [
        "# 66 — Audit externe des 14 communes traitées",
        "",
        f"**Ancrage étudié :** {ANCHOR.date().isoformat()} — **fenêtre :** "
        f"{WINDOW_START.date().isoformat()} à {WINDOW_END.date().isoformat()}.",
        "",
        "## Résultat directement utilisable",
        "",
        f"Les 50 paires conservées après le screening interne deviennent deux ensembles emboîtés :",
        "",
        f"- **ensemble élargi revu : {summary['broad_reviewed_set_pairs']} paires, "
        f"{summary['broad_reviewed_set_treated_municipalities']} communes traitées** ;",
        f"- **noyau strict « Magic Pass seul » : {summary['strict_magic_only_candidate_pairs']} paires, "
        f"{summary['strict_magic_only_candidate_treated_municipalities']} communes traitées**.",
        "",
        "Les 14 communes restent utilisables pour une description ou une analyse d'intervention combinée. "
        "Aucune commune, aucun contrôle et aucune paire n'est validé causalement à ce stade : la revue "
        "externe des contrôles et des bassins touristiques reste à terminer.",
        "",
        "## Chocs directs forts — hors des deux ensembles Magic-only",
        "",
        "| Commune | Paires | Motif principal | Sources |",
        "|---|---:|---|---|",
    ]
    for row in strong.itertuples(index=False):
        lines.append(
            f"| {markdown_cell(row.municipality_name)} | {row.retained_pair_count} | "
            f"{markdown_cell(note_fr[int(row.municipality_bfs_id)])} | {markdown_cell(row.review_source_ids)} |"
        )
    lines += [
        "",
        "## Interventions directes modérées — ensemble élargi seulement",
        "",
        "| Commune | Paires | Motif principal | Sensibilité recommandée |",
        "|---|---:|---|---|",
    ]
    for row in moderate.itertuples(index=False):
        lines.append(
            f"| {markdown_cell(row.municipality_name)} | {row.retained_pair_count} | "
            f"{markdown_cell(note_fr[int(row.municipality_bfs_id)])} | "
            f"{markdown_cell(sensitivity_fr[int(row.municipality_bfs_id)])} |"
        )
    lines += [
        "",
        "## Communes conservées dans le noyau strict, avec réserves ciblées",
        "",
        "| Commune | Paires | Réserve | Sensibilité recommandée |",
        "|---|---:|---|---|",
    ]
    for row in retained.itertuples(index=False):
        lines.append(
            f"| {markdown_cell(row.municipality_name)} | {row.retained_pair_count} | "
            f"{markdown_cell(note_fr[int(row.municipality_bfs_id)])} | "
            f"{markdown_cell(sensitivity_fr[int(row.municipality_bfs_id)])} |"
        )
    lines += [
        "",
        "## Méthode et limites",
        "",
        "La revue utilise des préavis, rapports et bulletins officiels archivés localement avec URL, "
        "date de récupération et SHA-256. Les documents ont été lus au niveau des pages/sections indiquées. "
        "Le classement distingue un choc direct fort, une intervention directe modérée et une réserve "
        "indirecte ou ponctuelle. Une recherche sans résultat n'est jamais interprétée comme preuve d'absence.",
        "",
        "Les alertes de capacité hôtelière sont complétées par la date de leur plus forte variation annuelle : "
        "cela évite de confondre automatiquement saisonnalité, volatilité pré-traitement et rupture postérieure. "
        "Les fichiers CSV gardent le détail des sources, fichiers locaux, empreintes, dates et limites de chaque cas.",
        "",
        "## Fichiers produits",
        "",
        "- `reports/accessibility_treated_external_shock_evidence.csv` : revue des 14 communes ;",
        "- `data_processed/accessibility_comparison_treated_external_risk_screen.csv` : 70 paires avec les deux niveaux ;",
        "- `reports/accessibility_comparison_treated_external_review_summary.json` : compteurs et empreintes d'entrée.",
        "",
    ]
    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    pairs = pd.read_csv(PAIR_INPUT)
    capacity = pd.read_csv(CAPACITY_INPUT)
    capacity["date"] = pd.to_datetime(capacity.date, errors="raise")
    if len(pairs) != EXPECTED_PAIRS:
        raise ValueError(f"Expected {EXPECTED_PAIRS} stage-18 pairs")
    if as_bool(pairs.retained_for_external_review).sum() != EXPECTED_STAGE18_RETAINED_PAIRS:
        raise ValueError("Expected 50 stage-18 retained pairs")

    audit = build_audit(pairs, capacity)
    pair_screen = build_pair_screen(pairs, audit)
    summary = make_summary(audit, pair_screen)
    if summary["broad_reviewed_set_pairs"] != 38:
        raise ValueError("Expected 38 pairs in the broad reviewed set")
    if summary["strict_magic_only_candidate_pairs"] != 32:
        raise ValueError("Expected 32 pairs in the strict Magic-only candidate set")

    AUDIT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PAIR_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT_OUTPUT, index=False, lineterminator="\n")
    pair_screen.to_csv(PAIR_OUTPUT, index=False, lineterminator="\n")
    SUMMARY_OUTPUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(audit, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
