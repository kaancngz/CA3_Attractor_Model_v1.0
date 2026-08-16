"""Plot overlap-by-sparsity robustness of the frozen sparse attractor."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "MPLCONFIGDIR",
    str(PROJECT_ROOT / ".mplconfig"),
)
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    engrams = payload["swept"]["engram_fractions"]
    overlaps = payload["swept"]["overlap_fractions"]
    lookup = {
        (row["engram_fraction"], row["overlap_fraction"]): row
        for row in payload["cells"]
    }

    def matrix(key: str) -> np.ndarray:
        return np.asarray(
            [
                [
                    np.nan if lookup[(engram, overlap)][key] is None
                    else lookup[(engram, overlap)][key]
                    for overlap in overlaps
                ]
                for engram in engrams
            ],
            dtype=float,
        )

    panels = (
        ("validation_pass_fraction", "A  Independent validation", "viridis", 0.0, 1.0),
        (
            "H1_mean_signed_retrieval_evidence_delta",
            "B  H1: Δ signed retrieval evidence",
            "coolwarm",
            -0.8,
            0.0,
        ),
        ("H2_A_state_fraction", "C  H2: fraction ending in A", "viridis", 0.0, 1.0),
        (
            "H3_mean_abs_signed_evidence_effect_asymmetry",
            "D  H3 evidence: |leading effect| − |trailing effect|",
            "coolwarm",
            -0.2,
            1.0,
        ),
    )
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.8), constrained_layout=True)
    for ax, (key, title, cmap, vmin, vmax) in zip(axes.flat, panels):
        values = matrix(key)
        color_map = plt.get_cmap(cmap).copy()
        color_map.set_bad("#D9D9D9")
        image = ax.imshow(values, cmap=color_map, vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_xticks(range(len(overlaps)), ["%.2g" % value for value in overlaps])
        ax.set_yticks(range(len(engrams)), ["%.2g" % value for value in engrams])
        ax.set_xlabel("A/B cellular overlap fraction")
        ax.set_ylabel("Engram fraction of CA3 cells")
        ax.set_title(title, loc="left", fontweight="bold")
        for row_index in range(values.shape[0]):
            for col_index in range(values.shape[1]):
                value = values[row_index, col_index]
                if np.isnan(value):
                    ax.text(
                        col_index,
                        row_index,
                        "NA",
                        ha="center",
                        va="center",
                        fontsize=7,
                        color="black",
                    )
                    continue
                color = "white" if abs(value) > 0.55 * max(abs(vmin), abs(vmax)) else "black"
                ax.text(
                    col_index,
                    row_index,
                    "%.2f" % value,
                    ha="center",
                    va="center",
                    fontsize=7,
                    color=color,
                )
        fig.colorbar(image, ax=ax, shrink=0.82)
    fig.suptitle(
        "Frozen CA3 attractor robustness: sparsity × cellular overlap (5 structural seeds)",
        fontsize=13,
        fontweight="bold",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=220)
    print("saved %s" % args.output)


if __name__ == "__main__":
    main()
