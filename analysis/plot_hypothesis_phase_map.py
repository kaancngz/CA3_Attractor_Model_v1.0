"""Plot the joint H1-H3 phase surface at a selected manipulation strength."""

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
    parser.add_argument("--strength", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    overlaps = payload["design"]["overlap_fractions"]
    accesses = payload["design"]["effective_access_fractions"]
    cells = [
        cell
        for cell in payload["phase_cells"]
        if np.isclose(cell["manipulation_strength"], args.strength)
    ]
    lookup = {
        (cell["overlap_fraction"], cell["effective_access_fraction"]): cell
        for cell in cells
    }

    def matrix(extractor) -> np.ndarray:
        rows = []
        for overlap in overlaps:
            row = []
            for access in accesses:
                value = extractor(lookup[(overlap, access)])
                row.append(np.nan if value is None else value)
            rows.append(row)
        return np.asarray(rows, dtype=float)

    panels = (
        (
            matrix(lambda cell: cell["H1"]["mean_delta_evidence"]),
            "A  H1 neural weakening",
            "Δ signed retrieval evidence",
            "coolwarm",
            -1.0,
            1.0,
        ),
        (
            matrix(lambda cell: cell["H1"]["non_A_on_fraction"]),
            "B  H1 attractor disruption",
            "Fraction no longer in A",
            "viridis",
            0.0,
            1.0,
        ),
        (
            matrix(lambda cell: cell["H2"]["A_on_fraction"]),
            "C  H2 sufficiency",
            "Fraction ending in A",
            "viridis",
            0.0,
            1.0,
        ),
        (
            matrix(
                lambda cell: (
                    cell["H3"]["mean_signed_interaction"]
                    if cell["H3"]["baseline_qualified_fraction"] >= 0.80
                    else None
                )
            ),
            "D  H3 position × suppression",
            "Interaction ΔE_leading − ΔE_trailing",
            "coolwarm",
            -2.0,
            2.0,
        ),
    )
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "figure.dpi": 150,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 8.2), constrained_layout=True)
    x_tick_indices = list(range(0, len(accesses), 2))
    if x_tick_indices[-1] != len(accesses) - 1:
        x_tick_indices.append(len(accesses) - 1)
    for ax, (values, title, color_label, cmap_name, vmin, vmax) in zip(
        axes.flat, panels
    ):
        cmap = plt.get_cmap(cmap_name).copy()
        cmap.set_bad("#D9D9D9")
        image = ax.imshow(values, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_xticks(
            x_tick_indices,
            ["%.1f" % (100 * accesses[index]) for index in x_tick_indices],
        )
        ax.set_yticks(
            range(len(overlaps)), ["%.0f" % (100 * overlap) for overlap in overlaps]
        )
        ax.set_xlabel("Effective final-A access (%)")
        ax.set_ylabel("A/B cellular overlap (%)")
        ax.set_title(title, loc="left", fontweight="bold")
        if 0.20 in overlaps and 0.25 in accesses:
            ax.plot(
                accesses.index(0.25),
                overlaps.index(0.20),
                marker="*",
                markersize=11,
                markerfacecolor="none",
                markeredgecolor="black",
                markeredgewidth=1.2,
            )
        colorbar = fig.colorbar(image, ax=ax, shrink=0.82)
        colorbar.set_label(color_label)
    fig.suptitle(
        "Frozen CA3 hypothesis phase map — manipulation strength %.2g (25 structures)"
        % args.strength,
        fontsize=13,
        fontweight="bold",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=220)
    print("saved %s" % args.output)


if __name__ == "__main__":
    main()
