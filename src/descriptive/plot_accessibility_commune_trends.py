"""Fifteen approved descriptive illustrations; source/estimation sample unchanged."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "data_interim/matplotlib_cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT))
from src.causal_inference.estimate_accessibility_cohort_time import month_number

CONFIG = ROOT / "config/accessibility_commune_trend_plots.json"
SOURCE = "DERIVED_ACCESSIBILITY_COMMUNE_TREND_PLOTS"


def fit_line(values: np.ndarray, event_months: np.ndarray) -> dict:
    valid = np.isfinite(values)
    x = np.column_stack([np.ones(valid.sum()), event_months[valid]])
    if valid.sum() < 3 or np.linalg.matrix_rank(x) != 2:
        raise ValueError("At least three observed months with positive residual degrees of freedom required")
    intercept, slope = np.linalg.lstsq(x, values[valid], rcond=None)[0]
    return {"intercept": float(intercept), "slope": float(slope), "n": int(valid.sum())}


def prepare_unit(local: pd.DataFrame, anchor: pd.Timestamp, calibration: pd.Series,
                 pre_months: int) -> tuple[pd.DataFrame, dict]:
    local = local.copy()
    local["date"] = pd.to_datetime(local.date)
    if local.date.duplicated().any():
        raise ValueError("Duplicate territory/month in plotting source")
    last = local.loc[local.hotel_overnights.notna(), "date"].max()
    dates = pd.date_range(anchor-pd.DateOffset(months=pre_months), last, freq="MS")
    local = local.set_index("date").reindex(dates)
    event = (month_number(dates)-(anchor.year*12+anchor.month)).astype(int)
    raw_log = local.log_overnights.to_numpy(float)
    raw_nights = local.hotel_overnights.to_numpy(float)
    if not np.array_equal(np.isfinite(raw_log), np.isfinite(raw_nights)):
        raise ValueError("Night/log missingness mismatch")
    valid = np.isfinite(raw_nights)
    if not np.allclose(raw_log[valid], np.log1p(raw_nights[valid])):
        raise ValueError("Source log1p mismatch")
    seasonal = np.array([calibration[f"seasonal_offset_month_{m:02d}"] for m in range(1, 13)], float)
    if not np.isfinite(seasonal).all():
        raise ValueError("Approved pre36 seasonal calibration unavailable")
    seasonal -= seasonal.mean()  # Average calendar-month profile, never post-weighted.
    z = raw_log-seasonal[np.asarray(dates.month)-1]
    pre_mask = event < 0
    pre = fit_line(z[pre_mask], event[pre_mask])
    post = fit_line(z[~pre_mask], event[~pre_mask])
    pre_curve = np.where(pre_mask, np.expm1(pre["intercept"]+pre["slope"]*event), np.nan)
    post_curve = np.where(~pre_mask, np.expm1(post["intercept"]+post["slope"]*event), np.nan)
    points = pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "event_month": event,
                           "hotel_overnights": raw_nights,
                           "observed_log_overnights": raw_log,
                           "centered_pre_seasonal_offset": seasonal[np.asarray(dates.month)-1],
                           "seasonally_adjusted_log_overnights": z,
                           "pre_trend_nights": pre_curve, "post_trend_nights": post_curve,
                           "source_outcome_observed": valid,
                           "source_id": SOURCE})
    metadata = {"pre_observed_months": pre["n"], "post_observed_months": post["n"],
                "pre_trend_intercept_log1p": pre["intercept"], "post_trend_intercept_log1p": post["intercept"],
                "pre_trend_slope_log1p_per_month": pre["slope"], "post_trend_slope_log1p_per_month": post["slope"],
                "plot_start_month": dates[0].strftime("%Y-%m-%d"), "plot_end_month": dates[-1].strftime("%Y-%m-%d"),
                "missing_source_months_in_plot": int((~valid).sum()), "source_id": SOURCE}
    return points, metadata


def draw_page(records: list[tuple[pd.DataFrame, dict]], number: int,
              covid_start: str, covid_end: str) -> Path:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 14,
                         "axes.titlesize": 15, "axes.labelsize": 13,
                         "xtick.labelsize": 12, "ytick.labelsize": 12})
    fig, axes = plt.subplots(5, 1, figsize=(11.5, 16.0))
    fig.subplots_adjust(left=.13, right=.965, bottom=.11, top=.85, hspace=1.0)
    fig.suptitle(f"Nuitées et tendances avant / après exposition — {number}/3", fontsize=18, y=.975)
    handles = [Line2D([], [], color="#7A8188", marker=".", linewidth=.9, label="Nuitées mensuelles observées"),
               Line2D([], [], color="#0072B2", linewidth=2.5, label="Tendance avant (désaisonnalisée)"),
               Line2D([], [], color="#D55E00", linewidth=2.5, label="Tendance après (désaisonnalisée)"),
               Line2D([], [], color="#292D31", linestyle="--", label="Première exposition au réseau")]
    legend = fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.53, .951),
               ncol=2, frameon=False, fontsize=12, handlelength=2.9, columnspacing=2)
    footer = fig.text(.5, .018, "Source : OFS/HESTA. Zone grise : mars 2020–mars 2022.\n"
             "36 mois avant, suivi disponible après. Échelles verticales propres à chaque commune.\n"
             "Tendances descriptives en unités de nuitées : aucune attribution causale au Magic Pass.",
             ha="center", fontsize=11.5, color="#3F464D")
    for ax, (points, unit) in zip(axes, records):
        dates = pd.to_datetime(points.date)
        anchor = pd.Timestamp(unit["focal_cohort_month"])
        ax.axvspan(pd.Timestamp(covid_start), pd.Timestamp(covid_end)+pd.offsets.MonthBegin(1),
                   color="#B7BCC2", alpha=.20, zorder=0)
        ax.plot(dates, points.hotel_overnights, color="#7A8188", linewidth=.85,
                marker=".", markersize=3.2, alpha=.8, zorder=2)
        ax.plot(dates, points.pre_trend_nights, color="#0072B2", linewidth=2.6, zorder=4)
        ax.plot(dates, points.post_trend_nights, color="#D55E00", linewidth=2.6, zorder=4)
        ax.axvline(anchor, color="#292D31", linestyle="--", linewidth=1.1, zorder=3)
        title = (f"{unit['municipality_name']} (BFS {unit['municipality_bfs_id']}) — exposition {anchor:%m/%Y}"
                 f"\n{unit['pre_observed_months']} mois observés avant / {unit['post_observed_months']} après")
        ax.set_title(title, loc="left", pad=7)
        if unit["post_observed_months"] < 12:
            ax.text(.98, .96, "Suivi après < 12 mois", ha="right", va="top", transform=ax.transAxes,
                    fontsize=10.5, color="#8A3F00")
        ax.set_xlim(dates.iloc[0], dates.iloc[-1])
        low = min(0., float(np.nanmin(points[["hotel_overnights", "pre_trend_nights", "post_trend_nights"]].to_numpy())))
        high = float(np.nanmax(points[["hotel_overnights", "pre_trend_nights", "post_trend_nights"]].to_numpy()))
        ax.set_ylim(low, high*1.08)
        ax.set_ylabel("Nuitées / mois")
        ax.set_xlabel("Date")
        locator = mdates.YearLocator(base=2 if (dates.iloc[-1]-dates.iloc[0]).days > 6*365.25 else 1)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}".replace(",", " ")))
        ax.grid(axis="y", alpha=.22, linewidth=.6)
        ax.spines[["top", "right"]].set_visible(False)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for before, after in zip(axes[:-1], axes[1:]):
        if before.xaxis.label.get_window_extent(renderer).y0 < after._left_title.get_window_extent(renderer).y1+3:
            raise ValueError("Plot x-label overlaps following commune title")
    if legend.get_window_extent(renderer).y0 < axes[0]._left_title.get_window_extent(renderer).y1+3:
        raise ValueError("Legend overlaps first commune title")
    if axes[-1].xaxis.label.get_window_extent(renderer).y0 < footer.get_window_extent(renderer).y1+3:
        raise ValueError("Footer overlaps last x-label")
    path = ROOT / f"figures/accessibility_15_communes_trends_{number}.png"
    fig.savefig(path, dpi=160, facecolor="white", metadata={"Description": "15 approved descriptive municipality plots; not causal effects"})
    plt.close(fig)
    return path


def plain_records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records", force_ascii=False, double_precision=15))


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not config["researcher_approved"] or not config["selection_only_for_illustration"]:
        raise ValueError("Explicit illustration approval required")
    paths = [CONFIG, ROOT / config["support_file"], ROOT / config["calibration_file"],
             ROOT / config["panel_file"], ROOT / config["temporal_config"], Path(__file__)]
    input_sha = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    support = pd.read_csv(ROOT / config["support_file"])
    candidates = support.loc[support.calculable, "municipality_bfs_id"].sort_values().to_numpy(int)
    draw = np.random.default_rng(config["selection_seed"]).choice(candidates, 15, replace=False).tolist()
    if draw != config["selected_bfs_ids_in_draw_order"]:
        raise ValueError("Candidate universe/draw changed; do not silently redraw the illustration sample")
    selected = support.set_index("municipality_bfs_id").loc[draw].reset_index()
    selected = selected.sort_values(["focal_cohort_month", "municipality_bfs_id"])
    calibration = pd.read_csv(ROOT / config["calibration_file"]).set_index(["focal_cohort_month", "municipality_bfs_id"])
    panel = pd.read_csv(ROOT / config["panel_file"], low_memory=False)
    records, metadata, point_frames = [], [], []
    for unit in selected.itertuples():
        key = (unit.focal_cohort_month, unit.municipality_bfs_id)
        local = panel.loc[panel.municipality_bfs_id.eq(unit.municipality_bfs_id)]
        points, details = prepare_unit(local, pd.Timestamp(unit.focal_cohort_month), calibration.loc[key], config["pre_months"])
        details.update({"municipality_bfs_id": int(unit.municipality_bfs_id), "municipality_name": unit.municipality_name,
                        "focal_cohort_month": unit.focal_cohort_month, "illustration_only": True,
                        "plot_page": len(metadata)//5+1, "causal_estimation_approved": False})
        points.insert(0, "municipality_bfs_id", int(unit.municipality_bfs_id))
        metadata.append(details)
        point_frames.append(points)
        records.append((points, details))
    temporal = json.loads((ROOT / config["temporal_config"]).read_text(encoding="utf-8"))
    outputs = [draw_page(records[i:i+5], i//5+1, temporal["covid_exclusion_sensitivity_start_month"],
                         temporal["covid_exclusion_sensitivity_end_month"]) for i in range(0, 15, 5)]
    points_path = ROOT / config["output_points"]
    payload = {"source_id": SOURCE, "illustration_only": True,
               "communes": metadata, "observations": plain_records(pd.concat(point_frames, ignore_index=True))}
    points_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    outputs.append(points_path)
    summary = {"specification_version": config["specification_version"], "researcher_approved": True,
               "selection_only_for_illustration": True, "selection_seed": config["selection_seed"],
               "candidate_territories": len(candidates), "selected_bfs_ids_in_draw_order": draw,
               "illustrated_territories": len(metadata), "plot_pages": 3,
               "observed_months_plotted": int(pd.concat(point_frames).source_outcome_observed.sum()),
               "trend_rule": config["trend_rule"], "seasonality_after_entry": config["seasonality_after_entry"],
               "analysis_sample_changed": False, "causal_estimation_approved": False,
               "input_sha256": input_sha,
               "output_sha256": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},
               "runtime_versions": {"numpy": np.__version__, "pandas": pd.__version__, "matplotlib": matplotlib.__version__},
               "communes": metadata}
    (ROOT / config["output_summary"]).write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = ["# Nuitées et tendances de 15 communes", "",
             "Choix A approuvé le 5 octobre 2026. Quinze communes tirées sans remise parmi les 76 calculables, avec la graine 20261005 et les identifiants BFS triés. Ce choix sert uniquement à illustrer les séries : il ne modifie aucun échantillon ni résultat du rapport 82.", ""]
    for number in range(1, 4):
        lines += [f"## Planche {number}", "", f"![Cinq communes : nuitées et tendances](../figures/accessibility_15_communes_trends_{number}.png)", ""]
    lines += ["## Lecture et méthode", "",
              "Gris : nuitées hôtelières mensuelles HESTA originales. Bleu : tendance avant exposition. Orange : tendance après. Verticale noire : première exposition communale au réseau Magic Pass accessible, pas entrée d'une station ni localisation de la station. Le seuil reste les 120 minutes de la matrice actuelle, tenue fixe historiquement : ces dates ne valident pas l'accessibilité passée. Fond gris : période COVID documentée (mars 2020–mars 2022), conservée dans les ajustements. Les axes verticaux ont leur propre échelle pour rendre chaque série lisible.", "",
              "Fenêtre : 36 mois avant la première exposition, puis tous les mois jusqu'à la dernière nuitée observée. Une valeur manquante crée un trou dans la série brute ; aucun remplissage. Les deux suivis après de moins d'un an sont signalés.", "",
              "La calibration saisonnière reprend exactement les onze coefficients locaux pré36 du rapport 82, estimés sur log(1 + nuitées) avec intercept et temps calendaire. On les centre sur les douze mois, puis soustrait le profil aux observations avant **et** après. Ce même profil prétraitement est conservé, sans le réestimer sur les données postérieures. Deux régressions descriptives intercept + temps calendaire sont ensuite ajustées séparément aux valeurs corrigées observées avant et après. Les courbes affichées sont exp(tendance log1p) − 1, en unités de nuitées. Elles représentent un niveau désaisonnalisé, pas une moyenne arithmétique prédite ou un effet causal. Elles peuvent être courbes même si la pente est linéaire sur l'échelle logarithmique.", "",
              "Un profil saisonnier stable après entrée est une hypothèse de lecture. Changement de saisonnalité, COVID, nouveaux hôtels et autres entrées accessibles peuvent modifier les courbes. La comparaison de deux pentes ne sépare pas ces phénomènes et n'utilise pas de témoins ; aucun intervalle, test ou effet du Magic Pass n'en est déduit.", "",
              "## Sources et reproduction", "",
              "Sources existantes : OFS/HESTA (`BFS_HOTEL_DATA`), panel territorial avec Moutier raccordé, première exposition et calibration du rapport 82. Aucun téléchargement ni changement des valeurs sources. Nouvelle source dérivée : `DERIVED_ACCESSIBILITY_COMMUNE_TREND_PLOTS`. Config, identifiants tirés, formules, coefficients, points, empreintes et versions sont conservés dans `config/accessibility_commune_trend_plots.json`, `data_processed/accessibility_commune_trend_plot_points.json` et `accessibility_commune_trend_plot_summary.json`.", "",
              "Reproduction : `.venv/Scripts/python.exe src/descriptive/plot_accessibility_commune_trends.py`, puis mise à jour de la provenance. Le script vérifie le tirage figé et s'arrête si l'univers a changé, plutôt que choisir d'autres communes automatiquement.", ""]
    (ROOT / "reports/83_GRAPHIQUES_15_COMMUNES_TENDANCES_FR.md").write_text("\n".join(lines), encoding="utf-8")
    if input_sha != {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}:
        raise ValueError("Input changed during plotting")
    print(json.dumps({"illustrated_territories": len(metadata), "pages": 3,
                      "observed_months_plotted": summary["observed_months_plotted"],
                      "figures": [p.relative_to(ROOT).as_posix() for p in outputs[:3]]}, indent=2))


if __name__ == "__main__":
    main()
