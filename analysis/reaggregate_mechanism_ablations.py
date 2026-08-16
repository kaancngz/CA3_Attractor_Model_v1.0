"""Rebuild paired completion summaries in an existing ablation JSON output."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


FIELDS = (
    "correct_template_margin",
    "correct_cued_rate_hz",
    "correct_uncued_rate_hz",
    "wrong_memory_rate_hz",
    "completion_ratio",
    "pyramidal_rate_hz",
    "inhibitory_rate_hz",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.loads(args.path.read_text(encoding="utf-8"))
    paired = {}
    for row in payload["completion_rows"]:
        paired.setdefault((row["variant"], row["seed"]), []).append(row)
    seed_rows = []
    for (variant, seed), group in sorted(paired.items()):
        seed_rows.append(
            {
                "variant": variant,
                "seed": seed,
                **{field: statistics.mean(row[field] for row in group) for field in FIELDS},
            }
        )
    grouped = {}
    for row in seed_rows:
        grouped.setdefault(row["variant"], []).append(row)
    summary = []
    for variant, group in sorted(grouped.items()):
        item = {"variant": variant}
        for field in FIELDS:
            values = [row[field] for row in group]
            mean = statistics.mean(values)
            sd = statistics.stdev(values) if len(values) > 1 else 0.0
            item[field] = {
                "mean": mean,
                "sd": sd,
                "sem": sd / len(values) ** 0.5,
                "n": len(values),
            }
        summary.append(item)
    payload["completion_seed_rows"] = seed_rows
    payload["completion_summary"] = summary
    args.path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("reaggregated %s" % args.path)


if __name__ == "__main__":
    main()
