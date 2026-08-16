"""Publication-style summary figure for sparse attractor validation and predictions."""

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


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cohort_rows(payload: dict, protocol: str, strength: float) -> list[dict]:
    rows = [
        row
        for row in payload["cohort_summary"]
        if row["protocol"] == protocol
        and np.isclose(row["manipulation_strength"], strength)
    ]
    return sorted(rows, key=lambda row: row["mean_effective_manipulated_final_a_fraction"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--match-050", type=Path, required=True)
    parser.add_argument("--match-075", type=Path, required=True)
    parser.add_argument("--match-100", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validation = load(args.validation)
    payloads = {
        0.50: load(args.match_050),
        0.75: load(args.match_075),
        1.00: load(args.match_100),
    }
    primary = payloads[1.00]

    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "figure.dpi": 150,
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.8), constrained_layout=True)

    ax = axes[0, 0]
    thresholds = [row["activation_threshold"] for row in validation["candidates"]]
    seed_fraction = [
        row["passed_seed_count"] / row["total_seed_count"]
        for row in validation["candidates"]
    ]
    ax.plot(thresholds, seed_fraction, marker="o", color="#2A6F97", linewidth=2)
    ax.axvline(0.12, color="#D1495B", linestyle="--", linewidth=1.5, label="Frozen: 0.12")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Activation threshold (model units)")
    ax.set_ylabel("Fraction passing all 10 gates")
    ax.set_title("A  Independent attractor qualification (5 seeds)", loc="left", fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)

    ax = axes[0, 1]
    lambdas = primary["design"]["lambdas"]
    scales = primary["design"]["cue_scales"]
    heat = np.zeros((len(scales), len(lambdas)))
    for row_index, scale in enumerate(scales):
        for col_index, lambda_a in enumerate(lambdas):
            values = []
            for seed in primary["seed_results"]:
                match = next(
                    item
                    for item in seed["basin_map"]
                    if np.isclose(item["cue_scale"], scale)
                    and np.isclose(item["lambda_a"], lambda_a)
                    and item["initial_state"] == "neutral"
                    and item["cue_mode"] == "sustained"
                )
                values.append(match["summary"]["neural_competition_index"])
            heat[row_index, col_index] = np.mean(values)
    image = ax.imshow(heat, vmin=-1, vmax=1, cmap="coolwarm", aspect="auto")
    ax.set_xticks(range(len(lambdas)), ["%.2g" % value for value in lambdas])
    ax.set_yticks(range(len(scales)), ["%.2g" % value for value in scales])
    ax.set_xlabel("Learned A support, λ")
    ax.set_ylabel("Total cue scale")
    ax.set_title("B  Fixed-total learned-cue basin map", loc="left", fontweight="bold")
    cbar = fig.colorbar(image, ax=ax, shrink=0.85)
    cbar.set_label("Mean neural competition index (B ← 0 → A)")

    match_styles = {
        0.50: ("#8D99AE", ":"),
        0.75: ("#5B8E7D", "--"),
        1.00: ("#1D3557", "-"),
    }
    ax = axes[1, 0]
    for match_fraction, payload in payloads.items():
        color, linestyle = match_styles[match_fraction]
        for protocol, marker, prefix in (
            ("H1_A_context", "o", "H1 suppress"),
            ("H2_B_context", "s", "H2 activate"),
        ):
            rows = cohort_rows(payload, protocol, 1.0)
            ax.plot(
                [row["mean_effective_manipulated_final_a_fraction"] for row in rows],
                [row["mean_signed_retrieval_evidence_delta"] for row in rows],
                color=color,
                linestyle=linestyle,
                marker=marker,
                markersize=4,
                label="%s; tag match %.0f%%" % (prefix, 100 * match_fraction),
            )
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Effective fraction of final A engram manipulated")
    ax.set_ylabel("Δ signed retrieval evidence (A−B)")
    ax.set_title(
        "C  H1 weakening and H2 switching track effective access",
        loc="left",
        fontweight="bold",
    )
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, ncol=2, fontsize=7)

    ax = axes[1, 1]
    for match_fraction, payload in payloads.items():
        color, linestyle = match_styles[match_fraction]
        for protocol, marker, label in (
            ("H3_A_leading", "o", "A leading"),
            ("H3_A_trailing", "^", "A trailing"),
        ):
            rows = cohort_rows(payload, protocol, 1.0)
            ax.plot(
                [row["mean_effective_manipulated_final_a_fraction"] for row in rows],
                [row["mean_signed_retrieval_evidence_delta"] for row in rows],
                color=color,
                linestyle=linestyle,
                marker=marker,
                markersize=4,
                label="%s; tag match %.0f%%" % (label, 100 * match_fraction),
            )
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set_xlabel("Effective fraction of final A engram suppressed")
    ax.set_ylabel("Δ signed retrieval evidence (A−B)")
    ax.set_title("D  H3 positional asymmetry is the main prediction", loc="left", fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, ncol=2, fontsize=7)

    fig.suptitle(
        "Primary sparse CA3 attractor: qualification, cue competition, and manipulation predictions",
        fontsize=13,
        fontweight="bold",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=220)
    print("saved %s" % args.output)


if __name__ == "__main__":
    main()
