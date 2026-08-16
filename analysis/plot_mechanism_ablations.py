"""Plot recurrence, inhibitory-feedback and overlap mechanism ablations."""

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


ORDER = (
    "baseline",
    "no_engram_recurrence",
    "half_inhibitory_feedback",
    "no_inhibitory_feedback",
    "no_overlap",
)
LABELS = {
    "baseline": "Temel",
    "no_engram_recurrence": "Engram\nrekürrensi yok",
    "half_inhibitory_feedback": "İnhibisyon\nyarım",
    "no_inhibitory_feedback": "İnhibitör geri\nbildirim yok",
    "no_overlap": "Örtüşme\nyok",
}
COLORS = {
    "baseline": "#4f6d7a",
    "no_engram_recurrence": "#8f8f8f",
    "half_inhibitory_feedback": "#e69f00",
    "no_inhibitory_feedback": "#c43c39",
    "no_overlap": "#2b6cb0",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    completion = {row["variant"]: row for row in payload["completion_summary"]}
    competition = {
        (row["variant"], row["lambda_a"]): row for row in payload["competition_summary"]
    }
    lambdas = payload["design"]["lambda_a_values"]

    fig, axes = plt.subplots(2, 2, figsize=(12.0, 8.6), constrained_layout=True)
    x = np.arange(len(ORDER))
    uncued = [completion[name]["correct_uncued_rate_hz"]["mean"] for name in ORDER]
    uncued_sem = [completion[name]["correct_uncued_rate_hz"]["sem"] for name in ORDER]
    cued = [completion[name]["correct_cued_rate_hz"]["mean"] for name in ORDER]
    width = 0.36
    axes[0, 0].bar(x - width / 2, cued, width, color="#b8c4c9", label="cue alan")
    axes[0, 0].bar(
        x + width / 2,
        uncued,
        width,
        yerr=uncued_sem,
        color=[COLORS[name] for name in ORDER],
        capsize=3,
        label="cue almayan",
    )
    axes[0, 0].set_xticks(x, [LABELS[name] for name in ORDER], fontsize=8)
    axes[0, 0].set_ylabel("engram hızı (Hz)")
    axes[0, 0].set_title("%20 partial cue altında örüntü tamamlama")
    axes[0, 0].legend(frameon=False)
    axes[0, 0].grid(axis="y", alpha=0.2)

    margins = [completion[name]["correct_template_margin"]["mean"] for name in ORDER]
    margin_sem = [completion[name]["correct_template_margin"]["sem"] for name in ORDER]
    axes[0, 1].bar(
        x,
        margins,
        yerr=margin_sem,
        color=[COLORS[name] for name in ORDER],
        capsize=3,
    )
    axes[0, 1].axhline(0, color="#333333", linewidth=0.8)
    axes[0, 1].set_xticks(x, [LABELS[name] for name in ORDER], fontsize=8)
    axes[0, 1].set_ylabel("doğru şablon marjı")
    axes[0, 1].set_title("A/B engram seçiciliği")
    axes[0, 1].grid(axis="y", alpha=0.2)

    for name in ORDER:
        means = [competition[(name, value)]["m_a_minus_m_b"]["mean"] for value in lambdas]
        sems = [competition[(name, value)]["m_a_minus_m_b"]["sem"] for value in lambdas]
        means_array = np.asarray(means)
        sems_array = np.asarray(sems)
        axes[1, 0].plot(
            lambdas,
            means_array,
            color=COLORS[name],
            marker="o",
            linewidth=1.8,
            label=LABELS[name].replace("\n", " "),
        )
        axes[1, 0].fill_between(
            lambdas,
            means_array - sems_array,
            means_array + sems_array,
            color=COLORS[name],
            alpha=0.12,
        )
    axes[1, 0].axhline(0, color="#333333", linewidth=0.8)
    axes[1, 0].axvline(0.5, color="#777777", linestyle="--", linewidth=0.8)
    axes[1, 0].set_xlabel("A cue bileşeni λ")
    axes[1, 0].set_ylabel("mA − mB")
    axes[1, 0].set_title("A/B rekabet eğrisi")
    axes[1, 0].legend(frameon=False, fontsize=8, ncol=2)
    axes[1, 0].grid(alpha=0.2)

    for name in ORDER:
        rates = [competition[(name, value)]["pyramidal_rate_hz"]["mean"] for value in lambdas]
        axes[1, 1].plot(
            lambdas,
            rates,
            color=COLORS[name],
            marker="o",
            linewidth=1.8,
            label=LABELS[name].replace("\n", " "),
        )
    axes[1, 1].axhline(40.0, color="#9b2226", linestyle=":", linewidth=1.0, label="40 Hz referansı")
    axes[1, 1].set_xlabel("A cue bileşeni λ")
    axes[1, 1].set_ylabel("toplam piramidal hız (Hz)")
    axes[1, 1].set_title("Ablasyon sonrası ağ kararlılığı")
    axes[1, 1].grid(alpha=0.2)
    axes[1, 1].legend(frameon=False, fontsize=8)

    fig.suptitle("CA3 rekabet modelinde mekanizma ablasyonları", fontsize=15)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=180)
    plt.close(fig)
    print("saved %s" % args.output)


if __name__ == "__main__":
    main()
