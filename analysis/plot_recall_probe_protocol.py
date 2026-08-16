"""Plot the experiment-matched CA3 recall/probe protocol results."""

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


PRIMARY_ARMS = [
    "H1_ARCHT_TAGGED_CONTEXT",
    "H2_CHR2_UNTAGGED_CONTEXT",
    "H3_ARCHT_C_TAGGED_LEADING",
    "H3_ARCHT_C_TAGGED_TRAILING",
]
CONTROL_ARMS = [
    "EGFP_TAGGED_CONTEXT_CONTROL",
    "EGFP_UNTAGGED_CONTEXT_CONTROL",
    "EGFP_C_TAGGED_LEADING_CONTROL",
    "EGFP_C_TAGGED_TRAILING_CONTROL",
]
SHORT_LABELS = {
    "H1_ARCHT_TAGGED_CONTEXT": "H1\nArchT / tagged",
    "H2_CHR2_UNTAGGED_CONTEXT": "H2\nChR2 / untagged",
    "H3_ARCHT_C_TAGGED_LEADING": "H3\nA leading",
    "H3_ARCHT_C_TAGGED_TRAILING": "H3\nA trailing",
    "EGFP_TAGGED_CONTEXT_CONTROL": "EGFP\nA context",
    "EGFP_UNTAGGED_CONTEXT_CONTROL": "EGFP\nB context",
    "EGFP_C_TAGGED_LEADING_CONTROL": "EGFP\nC / A leading",
    "EGFP_C_TAGGED_TRAILING_CONTROL": "EGFP\nC / A trailing",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def paired_values(payload: dict, arm_id: str, key: str) -> tuple[np.ndarray, np.ndarray]:
    rows = [row for row in payload["probe_rows"] if row["arm_id"] == arm_id]
    by_network: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_network.setdefault(row["network_id"], {})[row["light_state"]] = row
    off = np.asarray([by_network[name]["off"][key] for name in sorted(by_network)])
    on = np.asarray([by_network[name]["on"][key] for name in sorted(by_network)])
    return off, on


def delta_values(payload: dict, arm_id: str, key: str) -> np.ndarray:
    rows = [row for row in payload["paired_effects"] if row["arm_id"] == arm_id]
    return np.asarray([row[key] for row in rows], dtype=float)


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    n_structures = payload["design"]["n_structural_realizations"]
    colors = ["#B23A48", "#2878B5", "#7A5195", "#D98E04"]
    fig, axes = plt.subplots(2, 2, figsize=(12.2, 8.7), constrained_layout=True)

    ax = axes[0, 0]
    for index, (arm_id, color) in enumerate(zip(PRIMARY_ARMS, colors)):
        off, on = paired_values(payload, arm_id, "signed_retrieval_evidence")
        x0, x1 = index * 1.35, index * 1.35 + 0.42
        for off_value, on_value in zip(off, on):
            ax.plot([x0, x1], [off_value, on_value], color=color, alpha=0.12, lw=0.8)
        ax.plot(
            [x0, x1],
            [off.mean(), on.mean()],
            color=color,
            marker="o",
            markersize=5,
            lw=2.6,
        )
    centers = np.arange(len(PRIMARY_ARMS)) * 1.35 + 0.21
    ax.set_xticks(centers, [SHORT_LABELS[arm] for arm in PRIMARY_ARMS])
    ax.set_ylabel("Signed retrieval evidence E (A−B)")
    ax.set_ylim(-1.12, 1.12)
    ax.axhline(0.0, color="#666666", lw=0.8, ls="--")
    ax.set_title("A  Paired light OFF → ON probe outcome", loc="left", fontweight="bold")
    ax.text(0.02, 0.04, "thin lines: structural networks · thick: mean", transform=ax.transAxes, fontsize=8)

    ax = axes[0, 1]
    all_arms = PRIMARY_ARMS + CONTROL_ARMS
    evidence_deltas = [delta_values(payload, arm, "delta_evidence") for arm in all_arms]
    positions = np.arange(len(all_arms))
    bar_colors = colors + ["#8A8F98"] * len(CONTROL_ARMS)
    ax.bar(
        positions,
        [values.mean() for values in evidence_deltas],
        color=bar_colors,
        alpha=0.88,
        width=0.72,
    )
    for position, values in zip(positions, evidence_deltas):
        jitter = np.linspace(-0.18, 0.18, len(values))
        ax.scatter(
            position + jitter,
            values,
            s=9,
            color="#222222",
            alpha=0.28,
            linewidths=0,
        )
    ax.axhline(0.0, color="#444444", lw=0.9)
    ax.set_xticks(positions, [SHORT_LABELS[arm] for arm in all_arms], rotation=35, ha="right")
    ax.set_ylabel("Light effect ΔE")
    ax.set_title("B  Neural light effect and EGFP invariance", loc="left", fontweight="bold")

    ax = axes[1, 0]
    reactivation_deltas = [
        delta_values(payload, arm, "delta_tagged_reactivation") for arm in all_arms
    ]
    ax.bar(
        positions,
        [values.mean() for values in reactivation_deltas],
        color=bar_colors,
        alpha=0.88,
        width=0.72,
    )
    for position, values in zip(positions, reactivation_deltas):
        jitter = np.linspace(-0.18, 0.18, len(values))
        ax.scatter(
            position + jitter,
            values,
            s=9,
            color="#222222",
            alpha=0.28,
            linewidths=0,
        )
    ax.axhline(0.0, color="#444444", lw=0.9)
    ax.set_xticks(positions, [SHORT_LABELS[arm] for arm in all_arms], rotation=35, ha="right")
    ax.set_ylabel("Light effect Δ tagged reactivation")
    ax.set_title("C  Histology-facing reactivation prediction", loc="left", fontweight="bold")

    ax = axes[1, 1]
    h3_rows = [
        row
        for row in payload["H3_positional_interaction"]["rows"]
        if row["baseline_qualified"]
    ]
    leading = np.asarray([row["leading_delta_evidence"] for row in h3_rows])
    trailing = np.asarray([row["trailing_delta_evidence"] for row in h3_rows])
    bounds = (-0.75, 0.20)
    ax.plot(bounds, bounds, color="#666666", ls="--", lw=1.0, label="equal effect")
    ax.scatter(leading, trailing, color="#7A5195", s=30, alpha=0.75)
    ax.scatter(
        [leading.mean()],
        [trailing.mean()],
        color="#111111",
        marker="*",
        s=125,
        label="mean",
        zorder=3,
    )
    ax.set_xlim(bounds)
    ax.set_ylim(bounds)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("H3 ΔE when tagged memory is leading")
    ax.set_ylabel("H3 ΔE when tagged memory is trailing")
    interaction = payload["H3_positional_interaction"]["mean_signed_interaction"]
    ax.set_title(
        "D  H3 positional interaction (mean I = %.3f)" % interaction,
        loc="left",
        fontweight="bold",
    )
    ax.legend(frameon=False, fontsize=8, loc="lower right")

    fig.suptitle(
        "Experiment-matched CA3 recall–probe protocol · %d structural networks"
        % n_structures,
        fontsize=14,
        fontweight="bold",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=220)
    print("saved %s" % args.output)


if __name__ == "__main__":
    main()
