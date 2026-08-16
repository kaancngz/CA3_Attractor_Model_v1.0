"""Robustness surfaces for the frozen sparse-attractor architecture."""

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
from models.ca3_sparse_attractor.run_validation import evaluate
from models.ca3_sparse_attractor.cli import parse_float_list, parse_int_list


def final_summary(result: dict) -> dict:
    return result["convergence"]["trajectory"][-1]


def run_pair(
    model: SparseCA3Attractor,
    base: AttractorCondition,
    manipulated: AttractorCondition,
) -> dict:
    off = final_summary(model.run_condition(base, cue_remains_on=True))
    on = final_summary(model.run_condition(manipulated, cue_remains_on=True))
    return {
        "baseline_state": off["state_class"],
        "manipulated_state": on["state_class"],
        "neural_competition_delta": (
            on["neural_competition_index"] - off["neural_competition_index"]
        ),
        "signed_retrieval_evidence_delta": (
            on["signed_retrieval_evidence"] - off["signed_retrieval_evidence"]
        ),
        "a_engram_activity_delta": (
            on["a_engram_activity"] - off["a_engram_activity"]
        ),
        "tagged_reactivation_delta": (
            on["tagged_reactivation"] - off["tagged_reactivation"]
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("smoke", "pilot", "full"), default="pilot")
    parser.add_argument(
        "--seeds",
        type=parse_int_list,
        default=parse_int_list("20260815,20260816,20260817,20260818,20260819"),
    )
    parser.add_argument(
        "--engram-fractions",
        type=parse_float_list,
        default=parse_float_list("0.04,0.06,0.08,0.10,0.12"),
    )
    parser.add_argument(
        "--overlaps",
        type=parse_float_list,
        default=parse_float_list("0,0.10,0.20,0.30,0.40,0.50,0.60"),
    )
    parser.add_argument("--threshold", type=float, default=0.12)
    parser.add_argument("--tone-scale", type=float, default=0.50)
    parser.add_argument("--manipulation-fraction", type=float, default=0.25)
    parser.add_argument("--manipulation-strength", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.time()
    cells = []
    for engram_fraction in args.engram_fractions:
        for overlap_fraction in args.overlaps:
            seed_rows = []
            for seed in args.seeds:
                model = SparseCA3Attractor(
                    SparseAttractorConfig.for_profile(
                        args.profile,
                        seed=seed,
                        engram_fraction=engram_fraction,
                        overlap_fraction=overlap_fraction,
                        activation_threshold=args.threshold,
                        max_active_fraction=engram_fraction,
                        tag_test_match_fraction=1.0,
                    )
                )
                validation = evaluate(model)
                strength = args.manipulation_strength
                fraction = args.manipulation_fraction
                h1 = run_pair(
                    model,
                    AttractorCondition("H1_off", 1.0, 0.0),
                    AttractorCondition(
                        "H1_on", 1.0, 0.0,
                        manipulation="suppress",
                        manipulation_strength=strength,
                        manipulation_fraction=fraction,
                    ),
                )
                h2 = run_pair(
                    model,
                    AttractorCondition("H2_off", 0.0, 1.0),
                    AttractorCondition(
                        "H2_on", 0.0, 1.0,
                        manipulation="activate",
                        manipulation_strength=strength,
                        manipulation_fraction=fraction,
                    ),
                )
                h3_leading = run_pair(
                    model,
                    AttractorCondition(
                        "H3_leading_off", args.tone_scale * 0.65, args.tone_scale * 0.35
                    ),
                    AttractorCondition(
                        "H3_leading_on",
                        args.tone_scale * 0.65,
                        args.tone_scale * 0.35,
                        manipulation="suppress",
                        manipulation_strength=strength,
                        manipulation_fraction=fraction,
                    ),
                )
                h3_trailing = run_pair(
                    model,
                    AttractorCondition(
                        "H3_trailing_off", args.tone_scale * 0.35, args.tone_scale * 0.65
                    ),
                    AttractorCondition(
                        "H3_trailing_on",
                        args.tone_scale * 0.35,
                        args.tone_scale * 0.65,
                        manipulation="suppress",
                        manipulation_strength=strength,
                        manipulation_fraction=fraction,
                    ),
                )
                seed_rows.append(
                    {
                        "seed": seed,
                        "passed_all_validation_gates": validation["passed_all_gates"],
                        "passed_validation_gate_count": validation["passed_gate_count"],
                        "H1": h1,
                        "H2": h2,
                        "H3_A_leading": h3_leading,
                        "H3_A_trailing": h3_trailing,
                    }
                )

            h3_qualified = [
                row
                for row in seed_rows
                if row["H3_A_leading"]["baseline_state"] == "A"
                and row["H3_A_trailing"]["baseline_state"] == "B"
            ]
            cells.append(
                {
                    "engram_fraction": engram_fraction,
                    "overlap_fraction": overlap_fraction,
                    "n_structural_seeds": len(seed_rows),
                    "validation_pass_fraction": statistics.mean(
                        row["passed_all_validation_gates"] for row in seed_rows
                    ),
                    "mean_validation_gate_fraction": statistics.mean(
                        row["passed_validation_gate_count"] / 10.0 for row in seed_rows
                    ),
                    "H1_A_state_fraction": statistics.mean(
                        row["H1"]["manipulated_state"] == "A" for row in seed_rows
                    ),
                    "H1_mean_signed_retrieval_evidence_delta": statistics.mean(
                        row["H1"]["signed_retrieval_evidence_delta"] for row in seed_rows
                    ),
                    "H1_mean_tagged_reactivation_delta": statistics.mean(
                        row["H1"]["tagged_reactivation_delta"] for row in seed_rows
                    ),
                    "H2_A_state_fraction": statistics.mean(
                        row["H2"]["manipulated_state"] == "A" for row in seed_rows
                    ),
                    "H2_mean_signed_retrieval_evidence_delta": statistics.mean(
                        row["H2"]["signed_retrieval_evidence_delta"] for row in seed_rows
                    ),
                    "H3_baseline_qualification_fraction": len(h3_qualified) / len(seed_rows),
                    "H3_mean_abs_signed_evidence_effect_asymmetry": (
                        statistics.mean(
                            abs(row["H3_A_leading"]["signed_retrieval_evidence_delta"])
                            - abs(row["H3_A_trailing"]["signed_retrieval_evidence_delta"])
                            for row in h3_qualified
                        )
                        if h3_qualified
                        else None
                    ),
                    "seed_results": seed_rows,
                }
            )
            print(
                "engram %.2f overlap %.2f complete" % (engram_fraction, overlap_fraction),
                flush=True,
            )

    payload = {
        "status": "frozen_architecture_overlap_sparsity_robustness_v1",
        "architecture_changed_for_sweep": False,
        "hypothesis_outputs_used_for_parameter_selection": False,
        "fixed": {
            "profile": args.profile,
            "seeds": args.seeds,
            "activation_threshold": args.threshold,
            "tone_scale": args.tone_scale,
            "manipulation_fraction": args.manipulation_fraction,
            "manipulation_strength": args.manipulation_strength,
            "tag_test_match_fraction": 1.0,
        },
        "swept": {
            "engram_fractions": args.engram_fractions,
            "overlap_fractions": args.overlaps,
        },
        "cells": cells,
        "runtime_seconds": time.time() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("saved %s" % args.output, flush=True)


if __name__ == "__main__":
    main()
