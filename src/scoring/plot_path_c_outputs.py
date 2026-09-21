"""Create static scientific figures for the exploratory Path C outputs."""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MPL_CACHE = ROOT / "data_interim" / "matplotlib"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def as_bool(series: pd.Series) -> pd.Series:
    return series.fillna(False).astype(str).str.lower().eq("true")


def main() -> None:
    segments = pd.read_csv(ROOT / "data_processed/path_c_cluster_segments.csv")
    eligible = segments[segments["segment_id"].notna()].copy()
    colours = {"SEGMENT_01": "#4C78A8", "SEGMENT_02": "#F58518"}

    fig, axis = plt.subplots(figsize=(9.2, 6.2))
    for segment_id, group in eligible.groupby("segment_id", observed=True):
        member = as_bool(group["resolved_current_magic_member"])
        sizes = 24 + 14 * np.log1p(pd.to_numeric(group["number_lifts_median"]))
        axis.scatter(
            np.log1p(pd.to_numeric(group["ski_area_km_median"])),
            pd.to_numeric(group["altitude_top_m_median"]),
            s=sizes,
            c=colours.get(segment_id, "#999999"),
            alpha=0.68,
            edgecolors=np.where(member, "#111111", "none"),
            linewidths=np.where(member, 1.0, 0.0),
            label=f"{segment_id} (n={len(group)})",
        )
    axis.set_xlabel("log(1 + published ski-area kilometres)")
    axis.set_ylabel("Median published top altitude (m)")
    axis.set_title("Current structural lift-cluster segments\nblack outline = resolved current Magic Pass link")
    axis.grid(alpha=0.2)
    axis.legend(frameon=False)
    fig.text(
        0.01,
        0.01,
        "Undated directory snapshot; clusters are not certified independent destinations; no causal interpretation.",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(ROOT / "figures/path_c_structural_segments.png", dpi=180)
    plt.close(fig)

    analogues = pd.read_csv(ROOT / "data_processed/path_c_candidate_analogues.csv")
    ood_colours = {
        "good_support": "#2A9D8F",
        "moderate_extrapolation": "#E9C46A",
        "strong_extrapolation": "#E76F51",
    }
    fig, axis = plt.subplots(figsize=(8.4, 7.0))
    for status, group in analogues.groupby("reviewed_treated_ood_flag", observed=True):
        axis.scatter(
            group["opportunity_signal_percentile"],
            group["snow_vulnerability_percentile"],
            s=42,
            c=ood_colours.get(status, "#999999"),
            alpha=0.76,
            edgecolors="white",
            linewidths=0.4,
            label=f"{status.replace('_', ' ')} (n={len(group)})",
        )
    axis.axvline(50, color="#666666", linewidth=0.8, linestyle="--")
    axis.axhline(50, color="#666666", linewidth=0.8, linestyle="--")
    axis.set_xlim(0, 101)
    axis.set_ylim(0, 101)
    axis.set_xlabel("Descriptive analogue-opportunity percentile")
    axis.set_ylabel("Snow-vulnerability percentile")
    axis.set_title("Exploratory Opportunity × partial Strategic Need view\n(no predicted uplift; strategic need lacks tourism dependence/accessibility)")
    axis.grid(alpha=0.15)
    axis.legend(frameon=False, loc="lower left")
    fig.text(
        0.01,
        0.01,
        "Opportunity uses unadjusted changes from three nearest reviewed treated analogues; colours show structural OOD support.",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.savefig(ROOT / "figures/path_c_opportunity_snow_matrix.png", dpi=180)
    plt.close(fig)

    print(
        {
            "structural_segment_points": len(eligible),
            "opportunity_snow_points": len(analogues),
            "figures": [
                "figures/path_c_structural_segments.png",
                "figures/path_c_opportunity_snow_matrix.png",
            ],
        }
    )


if __name__ == "__main__":
    main()
