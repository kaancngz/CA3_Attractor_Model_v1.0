"""Mechanism-ablation controls for the frozen sparse CA3 attractor."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.ca3_sparse_attractor.config import SparseAttractorConfig
from models.ca3_sparse_attractor.model import AttractorCondition, SparseCA3Attractor
from models.ca3_sparse_attractor.run_hypothesis_phase_map import run_paired
from models.ca3_sparse_attractor.run_validation import evaluate
from models.ca3_sparse_attractor.cli import parse_int_list


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("smoke", "pilot", "full"), default="pilot")
    parser.add_argument(
        "--seeds",
        type=parse_int_list,
        default=parse_int_list(
            ",".join(str(seed) for seed in range(20260815, 20260840))
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def state_fractions(rows: list[dict], state_key: str) -> dict:
    states = ("A", "B", "mixed", "silent", "undecided")
    return {
        state: statistics.mean(row[state_key] == state for row in rows)
        for state in states
    }


def main() -> None:
    args = parse_args()
    started = time.time()
    regimes = {
        "intact": {},
        "no_recurrence": {"recurrent_gain": 0.0},
        "no_sparse_inhibition": {"max_active_fraction": 1.0},
        "zero_overlap": {"overlap_fraction": 0.0},
    }
    results = []
    for regime, overrides in regimes.items():
        seed_rows = []
        for seed in args.seeds:
            config_kwargs = {
                "seed": seed,
                "engram_fraction": 0.08,
                "overlap_fraction": 0.20,
                "activation_threshold": 0.12,
                "max_active_fraction": 0.08,
                "tagging_efficiency": 1.0,
                "fiber_coverage": 1.0,
                "tag_test_match_fraction": 1.0,
                **overrides,
            }
            model = SparseCA3Attractor(
                SparseAttractorConfig.for_profile(args.profile, **config_kwargs)
            )
            validation = evaluate(model)
            h1 = run_paired(
                model,
                AttractorCondition("H1_off", 1.0, 0.0),
                AttractorCondition(
                    "H1_on", 1.0, 0.0,
                    manipulation="suppress",
                    manipulation_strength=1.0,
                    manipulation_fraction=0.25,
                ),
                [1.0, 2.0, 4.0, 8.0],
            )
            h2 = run_paired(
                model,
                AttractorCondition("H2_off", 0.0, 1.0),
                AttractorCondition(
                    "H2_on", 0.0, 1.0,
                    manipulation="activate",
                    manipulation_strength=1.0,
                    manipulation_fraction=0.25,
                ),
                [1.0, 2.0, 4.0, 8.0],
            )
            leading = run_paired(
                model,
                AttractorCondition("H3_leading_off", 0.325, 0.175),
                AttractorCondition(
                    "H3_leading_on", 0.325, 0.175,
                    manipulation="suppress",
                    manipulation_strength=1.0,
                    manipulation_fraction=0.25,
                ),
                [1.0, 2.0, 4.0, 8.0],
            )
            trailing = run_paired(
                model,
                AttractorCondition("H3_trailing_off", 0.175, 0.325),
                AttractorCondition(
                    "H3_trailing_on", 0.175, 0.325,
                    manipulation="suppress",
                    manipulation_strength=1.0,
                    manipulation_fraction=0.25,
                ),
                [1.0, 2.0, 4.0, 8.0],
            )
            seed_rows.append(
                {
                    "seed": seed,
                    "validation": validation,
                    "H1": h1,
                    "H2": h2,
                    "H3_A_leading": leading,
                    "H3_A_trailing": trailing,
                }
            )

        h1_rows = [row["H1"] for row in seed_rows]
        h2_rows = [row["H2"] for row in seed_rows]
        leading_rows = [row["H3_A_leading"] for row in seed_rows]
        trailing_rows = [row["H3_A_trailing"] for row in seed_rows]
        qualified = [
            index
            for index, (leading, trailing) in enumerate(zip(leading_rows, trailing_rows))
            if leading["off_state"] == "A" and trailing["off_state"] == "B"
        ]
        results.append(
            {
                "regime": regime,
                "overrides": overrides,
                "validation_all_gates_fraction": statistics.mean(
                    row["validation"]["passed_all_gates"] for row in seed_rows
                ),
                "mean_validation_gate_fraction": statistics.mean(
                    row["validation"]["passed_gate_count"]
                    / row["validation"]["total_gate_count"]
                    for row in seed_rows
                ),
                "validation_gate_pass_fraction": {
                    gate: statistics.mean(
                        row["validation"]["gates"][gate] for row in seed_rows
                    )
                    for gate in seed_rows[0]["validation"]["gates"]
                },
                "H1": {
                    "mean_delta_evidence": statistics.mean(
                        row["delta_evidence"] for row in h1_rows
                    ),
                    "on_state_fractions": state_fractions(h1_rows, "on_state"),
                },
                "H2": {
                    "mean_delta_evidence": statistics.mean(
                        row["delta_evidence"] for row in h2_rows
                    ),
                    "on_state_fractions": state_fractions(h2_rows, "on_state"),
                },
                "H3": {
                    "baseline_qualified_fraction": len(qualified) / len(seed_rows),
                    "mean_signed_interaction": (
                        statistics.mean(
                            leading_rows[index]["delta_evidence"]
                            - trailing_rows[index]["delta_evidence"]
                            for index in qualified
                        )
                        if qualified
                        else None
                    ),
                    "leading_on_state_fractions": state_fractions(
                        leading_rows, "on_state"
                    ),
                    "trailing_on_state_fractions": state_fractions(
                        trailing_rows, "on_state"
                    ),
                },
            }
        )
        print("%s complete" % regime, flush=True)

    payload = {
        "status": "frozen_ca3_mechanism_ablations_v1",
        "architecture_retained": True,
        "design": {
            "profile": args.profile,
            "seeds": args.seeds,
            "primary_point": {
                "engram_fraction": 0.08,
                "overlap_fraction": 0.20,
                "activation_threshold": 0.12,
                "effective_access_fraction": 0.25,
                "manipulation_strength": 1.0,
                "tone_scale": 0.50,
            },
        },
        "interpretation_contract": {
            "no_recurrence": "must abolish autonomous pattern completion/basin recovery",
            "no_sparse_inhibition": (
                "must degrade selective competition under ambiguous cue if normalization is causal"
            ),
            "zero_overlap": (
                "tests whether the selected 65/35 tone regime can establish the H3 competition"
            ),
        },
        "regimes": results,
        "runtime_seconds": time.time() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("saved %s" % args.output, flush=True)


if __name__ == "__main__":
    main()
