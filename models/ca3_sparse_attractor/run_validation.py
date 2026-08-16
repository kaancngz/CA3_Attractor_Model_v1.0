"""Hypothesis-independent validation of the primary sparse attractor core."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.ca3_sparse_attractor.config import SparseAttractorConfig
from models.ca3_sparse_attractor.model import AttractorCondition, SparseCA3Attractor
from models.ca3_sparse_attractor.cli import parse_float_list, parse_int_list


def exact_pattern_match(model: SparseCA3Attractor, state, memory: str) -> bool:
    return bool((state == model.pattern_state(memory)).all())


def perturb_state(model: SparseCA3Attractor, memory: str, fraction: float):
    """Replace a nested fraction of the current memory with opponent-unique cells."""
    state = model.pattern_state(memory)
    own = model.layout.a_only if memory == "A" else model.layout.b_only
    opponent = model.layout.b_only if memory == "A" else model.layout.a_only
    count = min(round(model.layout.a.size * fraction), own.size, opponent.size)
    rng = model.rng
    state[rng.permutation(own)[:count]] = 0
    state[rng.permutation(opponent)[:count]] = 1
    return state


def evaluate(model: SparseCA3Attractor) -> dict:
    zero = model.empty_state()
    zero_result = model.converge(zero)
    fixed = {}
    recall = {}
    weak = {}
    perturb = {}
    for memory in ("A", "B"):
        cue = AttractorCondition(
            "partial_%s" % memory,
            1.0 if memory == "A" else 0.0,
            1.0 if memory == "B" else 0.0,
            cue_target_fraction=model.config.cue_target_fraction,
        )
        weak_cue = AttractorCondition(
            "weak_%s" % memory,
            1.0 if memory == "A" else 0.0,
            1.0 if memory == "B" else 0.0,
            cue_target_fraction=model.config.weak_cue_target_fraction,
        )
        fixed_result = model.converge(model.pattern_state(memory))
        recall_result = model.run_condition(cue)
        weak_result = model.run_condition(weak_cue)
        perturbed = perturb_state(model, memory, model.config.weak_cue_target_fraction)
        perturb_result = model.converge(perturbed)
        fixed[memory] = {
            "status": fixed_result["status"],
            "steps": fixed_result["steps"],
            "summary": fixed_result["trajectory"][-1],
            "exact_match": exact_pattern_match(model, fixed_result["final_state"], memory),
        }
        recall[memory] = {
            "status": recall_result["convergence"]["status"],
            "steps": recall_result["convergence"]["steps"],
            "summary": recall_result["convergence"]["trajectory"][-1],
            "exact_match": exact_pattern_match(
                model, recall_result["convergence"]["final_state"], memory
            ),
        }
        weak[memory] = {
            "status": weak_result["convergence"]["status"],
            "steps": weak_result["convergence"]["steps"],
            "summary": weak_result["convergence"]["trajectory"][-1],
            "silent": weak_result["convergence"]["trajectory"][-1]["state_class"] == "silent",
        }
        perturb[memory] = {
            "status": perturb_result["status"],
            "steps": perturb_result["steps"],
            "summary": perturb_result["trajectory"][-1],
            "exact_match": exact_pattern_match(model, perturb_result["final_state"], memory),
        }

    gates = {
        "silent_rest_fixed": (
            zero_result["status"] == "fixed_point"
            and zero_result["trajectory"][-1]["state_class"] == "silent"
        ),
        "A_is_fixed_point": fixed["A"]["exact_match"],
        "B_is_fixed_point": fixed["B"]["exact_match"],
        "A_partial_pattern_completion": recall["A"]["exact_match"],
        "B_partial_pattern_completion": recall["B"]["exact_match"],
        "A_weak_cue_no_false_recall": weak["A"]["silent"],
        "B_weak_cue_no_false_recall": weak["B"]["silent"],
        "A_local_basin_recovery": perturb["A"]["exact_match"],
        "B_local_basin_recovery": perturb["B"]["exact_match"],
        "A_B_recall_symmetry": abs(
            recall["A"]["summary"]["neural_competition_index"]
            + recall["B"]["summary"]["neural_competition_index"]
        )
        <= 1e-12,
    }
    return {
        "gates": gates,
        "passed_gate_count": sum(gates.values()),
        "total_gate_count": len(gates),
        "passed_all_gates": all(gates.values()),
        "rest": {
            "status": zero_result["status"],
            "summary": zero_result["trajectory"][-1],
        },
        "fixed_points": fixed,
        "partial_recall": recall,
        "weak_cues": weak,
        "local_perturbations": perturb,
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
        "--thresholds",
        type=parse_float_list,
        default=parse_float_list("0.08,0.10,0.12,0.14,0.16,0.18"),
    )
    parser.add_argument("--overlap", type=float, default=0.20)
    parser.add_argument("--engram-fraction", type=float, default=0.08)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.time()
    candidates = []
    for threshold in args.thresholds:
        seed_results = []
        for seed in args.seeds:
            config = SparseAttractorConfig.for_profile(
                args.profile,
                seed=seed,
                engram_fraction=args.engram_fraction,
                overlap_fraction=args.overlap,
                activation_threshold=threshold,
                max_active_fraction=args.engram_fraction,
            )
            model = SparseCA3Attractor(config)
            seed_results.append({"seed": seed, **evaluate(model)})
        passed_gates = sum(item["passed_gate_count"] for item in seed_results)
        total_gates = sum(item["total_gate_count"] for item in seed_results)
        candidate = {
            "activation_threshold": threshold,
            "passed_gate_count": passed_gates,
            "total_gate_count": total_gates,
            "passed_seed_count": sum(item["passed_all_gates"] for item in seed_results),
            "total_seed_count": len(seed_results),
            "passed_all_seeds": all(item["passed_all_gates"] for item in seed_results),
            "seed_results": seed_results,
        }
        candidates.append(candidate)
        print(
            "threshold %.3f: %d/%d gates; %d/%d seeds%s"
            % (
                threshold,
                passed_gates,
                total_gates,
                candidate["passed_seed_count"],
                candidate["total_seed_count"],
                " PASS" if candidate["passed_all_seeds"] else "",
            ),
            flush=True,
        )

    payload = {
        "status": "primary_sparse_attractor_independent_validation",
        "hypothesis_outputs_used_for_selection": False,
        "theoretical_core": {
            "learning_rule": "centered_covariance_hebbian",
            "weight_evaluation": (
                "factorized_exact_equivalent_of_dense_two_pattern_matrix_with_zero_diagonal"
            ),
            "inhibition": "hard_sparse_activity_cap",
            "patterns": "two_exact_size_partially_overlapping_binary_engrams",
        },
        "design": {
            "profile": args.profile,
            "seeds": args.seeds,
            "thresholds": args.thresholds,
            "engram_fraction": args.engram_fraction,
            "overlap_fraction": args.overlap,
            "strong_partial_cue_fraction": 0.20,
            "weak_partial_cue_fraction": 0.05,
        },
        "candidates": candidates,
        "runtime_seconds": time.time() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("saved %s" % args.output, flush=True)


if __name__ == "__main__":
    main()
