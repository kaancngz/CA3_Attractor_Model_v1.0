"""Joint phase map for the frozen CA3 attractor and the preregistered H1-H3 tests."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.ca3_sparse_attractor.config import SparseAttractorConfig
from models.ca3_sparse_attractor.model import AttractorCondition, SparseCA3Attractor
from models.ca3_sparse_attractor.cli import parse_float_list, parse_int_list
from models.ca3_sparse_attractor.theory_mapping import expected_choice_discrimination


STATE_CLASSES = ("A", "B", "mixed", "silent", "undecided")


def final_summary(result: dict) -> dict:
    return result["convergence"]["trajectory"][-1]


def run_paired(
    model: SparseCA3Attractor,
    baseline: AttractorCondition,
    manipulated: AttractorCondition,
    inverse_temperatures: list[float],
) -> dict:
    off = final_summary(model.run_condition(baseline, cue_remains_on=True))
    on = final_summary(model.run_condition(manipulated, cue_remains_on=True))
    off_evidence = off["signed_retrieval_evidence"]
    on_evidence = on["signed_retrieval_evidence"]
    return {
        "off_state": off["state_class"],
        "on_state": on["state_class"],
        "off_evidence": off_evidence,
        "on_evidence": on_evidence,
        "delta_evidence": on_evidence - off_evidence,
        "off_nci": off["neural_competition_index"],
        "on_nci": on["neural_competition_index"],
        "delta_nci": on["neural_competition_index"] - off["neural_competition_index"],
        "off_tagged_reactivation": off["tagged_reactivation"],
        "on_tagged_reactivation": on["tagged_reactivation"],
        "delta_tagged_reactivation": (
            on["tagged_reactivation"] - off["tagged_reactivation"]
        ),
        "behavior": {
            str(beta): {
                "off_expected_discrimination": expected_choice_discrimination(
                    off_evidence, beta
                ),
                "on_expected_discrimination": expected_choice_discrimination(
                    on_evidence, beta
                ),
                "delta_expected_discrimination": (
                    expected_choice_discrimination(on_evidence, beta)
                    - expected_choice_discrimination(off_evidence, beta)
                ),
            }
            for beta in inverse_temperatures
        },
    }


def mean(items, key: str) -> float:
    return statistics.mean(item[key] for item in items)


def sd(items, key: str) -> float:
    values = [item[key] for item in items]
    return statistics.stdev(values) if len(values) >= 2 else 0.0


def state_fractions(items: list[dict], key: str) -> dict:
    return {
        state: statistics.mean(item[key] == state for item in items)
        for state in STATE_CLASSES
    }


def summarize_protocol(items: list[dict], inverse_temperatures: list[float]) -> dict:
    return {
        "n_structural_realizations": len(items),
        "off_state_fractions": state_fractions(items, "off_state"),
        "on_state_fractions": state_fractions(items, "on_state"),
        "mean_off_evidence": mean(items, "off_evidence"),
        "mean_on_evidence": mean(items, "on_evidence"),
        "mean_delta_evidence": mean(items, "delta_evidence"),
        "sd_delta_evidence_across_structures": sd(items, "delta_evidence"),
        "mean_delta_nci": mean(items, "delta_nci"),
        "mean_delta_tagged_reactivation": mean(items, "delta_tagged_reactivation"),
        "directional_negative_fraction": statistics.mean(
            item["delta_evidence"] < -1e-12 for item in items
        ),
        "directional_positive_fraction": statistics.mean(
            item["delta_evidence"] > 1e-12 for item in items
        ),
        "near_chance_on_fraction": statistics.mean(
            abs(item["on_evidence"]) <= 0.10 for item in items
        ),
        "behavioral_envelope": {
            str(beta): {
                "mean_off_expected_discrimination": statistics.mean(
                    item["behavior"][str(beta)]["off_expected_discrimination"]
                    for item in items
                ),
                "mean_on_expected_discrimination": statistics.mean(
                    item["behavior"][str(beta)]["on_expected_discrimination"]
                    for item in items
                ),
                "mean_delta_expected_discrimination": statistics.mean(
                    item["behavior"][str(beta)]["delta_expected_discrimination"]
                    for item in items
                ),
            }
            for beta in inverse_temperatures
        },
    }


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
    parser.add_argument(
        "--overlaps",
        type=parse_float_list,
        default=parse_float_list("0,0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50,0.60"),
    )
    parser.add_argument(
        "--effective-access",
        type=parse_float_list,
        default=parse_float_list(
            "0,0.025,0.05,0.075,0.10,0.125,0.15,0.175,0.20,0.225,0.25,0.30,0.35,0.40,0.50"
        ),
    )
    parser.add_argument(
        "--strengths",
        type=parse_float_list,
        default=parse_float_list("0.25,0.50,1.00,2.00,4.00"),
    )
    parser.add_argument(
        "--inverse-temperatures",
        type=parse_float_list,
        default=parse_float_list("1,2,4,8"),
    )
    parser.add_argument("--engram-fraction", type=float, default=0.08)
    parser.add_argument("--threshold", type=float, default=0.12)
    parser.add_argument("--tone-scale", type=float, default=0.50)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.time()
    phase_cells = []
    primary_pairs = []

    for overlap in args.overlaps:
        networks = []
        for seed in args.seeds:
            model = SparseCA3Attractor(
                SparseAttractorConfig.for_profile(
                    args.profile,
                    seed=seed,
                    engram_fraction=args.engram_fraction,
                    overlap_fraction=overlap,
                    activation_threshold=args.threshold,
                    max_active_fraction=args.engram_fraction,
                    # The phase map isolates effective access itself. RAM
                    # efficiency, fiber coverage and tag-test match map onto
                    # this axis upstream and are not multiplied twice here.
                    tagging_efficiency=1.0,
                    fiber_coverage=1.0,
                    tag_test_match_fraction=1.0,
                )
            )
            baselines = {
                "H1": AttractorCondition("H1_A_context_off", 1.0, 0.0),
                "H2": AttractorCondition("H2_B_context_off", 0.0, 1.0),
                "H3_leading": AttractorCondition(
                    "H3_A_leading_off", args.tone_scale * 0.65, args.tone_scale * 0.35
                ),
                "H3_trailing": AttractorCondition(
                    "H3_A_trailing_off", args.tone_scale * 0.35, args.tone_scale * 0.65
                ),
            }
            networks.append((seed, model, baselines))

        for strength in args.strengths:
            for access in args.effective_access:
                h1_rows = []
                h2_rows = []
                h3_leading_rows = []
                h3_trailing_rows = []
                for seed, model, baselines in networks:
                    h1 = run_paired(
                        model,
                        baselines["H1"],
                        AttractorCondition(
                            "H1_A_context_on",
                            1.0,
                            0.0,
                            manipulation="suppress",
                            manipulation_strength=strength,
                            manipulation_fraction=access,
                        ),
                        args.inverse_temperatures,
                    )
                    h2 = run_paired(
                        model,
                        baselines["H2"],
                        AttractorCondition(
                            "H2_B_context_on",
                            0.0,
                            1.0,
                            manipulation="activate",
                            manipulation_strength=strength,
                            manipulation_fraction=access,
                        ),
                        args.inverse_temperatures,
                    )
                    h3_leading = run_paired(
                        model,
                        baselines["H3_leading"],
                        AttractorCondition(
                            "H3_A_leading_on",
                            args.tone_scale * 0.65,
                            args.tone_scale * 0.35,
                            manipulation="suppress",
                            manipulation_strength=strength,
                            manipulation_fraction=access,
                        ),
                        args.inverse_temperatures,
                    )
                    h3_trailing = run_paired(
                        model,
                        baselines["H3_trailing"],
                        AttractorCondition(
                            "H3_A_trailing_on",
                            args.tone_scale * 0.35,
                            args.tone_scale * 0.65,
                            manipulation="suppress",
                            manipulation_strength=strength,
                            manipulation_fraction=access,
                        ),
                        args.inverse_temperatures,
                    )
                    h1_rows.append(h1)
                    h2_rows.append(h2)
                    h3_leading_rows.append(h3_leading)
                    h3_trailing_rows.append(h3_trailing)

                    if (
                        math.isclose(overlap, 0.20)
                        and math.isclose(access, 0.25)
                        and math.isclose(strength, 1.0)
                    ):
                        primary_pairs.append(
                            {
                                "seed": seed,
                                "H1": h1,
                                "H2": h2,
                                "H3_A_leading": h3_leading,
                                "H3_A_trailing": h3_trailing,
                            }
                        )

                h3_qualified_indices = [
                    index
                    for index, (leading, trailing) in enumerate(
                        zip(h3_leading_rows, h3_trailing_rows)
                    )
                    if leading["off_state"] == "A" and trailing["off_state"] == "B"
                ]
                h3_interactions = [
                    h3_leading_rows[index]["delta_evidence"]
                    - h3_trailing_rows[index]["delta_evidence"]
                    for index in h3_qualified_indices
                ]
                h3_asymmetries = [
                    abs(h3_leading_rows[index]["delta_evidence"])
                    - abs(h3_trailing_rows[index]["delta_evidence"])
                    for index in h3_qualified_indices
                ]
                phase_cells.append(
                    {
                        "overlap_fraction": overlap,
                        "effective_access_fraction": access,
                        "manipulation_strength": strength,
                        "H1": {
                            **summarize_protocol(h1_rows, args.inverse_temperatures),
                            "non_A_on_fraction": statistics.mean(
                                item["on_state"] != "A" for item in h1_rows
                            ),
                        },
                        "H2": {
                            **summarize_protocol(h2_rows, args.inverse_temperatures),
                            "A_on_fraction": statistics.mean(
                                item["on_state"] == "A" for item in h2_rows
                            ),
                        },
                        "H3": {
                            "baseline_qualified_fraction": (
                                len(h3_qualified_indices) / len(args.seeds)
                            ),
                            "n_baseline_qualified": len(h3_qualified_indices),
                            "A_leading": summarize_protocol(
                                h3_leading_rows, args.inverse_temperatures
                            ),
                            "A_trailing": summarize_protocol(
                                h3_trailing_rows, args.inverse_temperatures
                            ),
                            "mean_signed_interaction": (
                                statistics.mean(h3_interactions)
                                if h3_interactions
                                else None
                            ),
                            "mean_abs_effect_asymmetry": (
                                statistics.mean(h3_asymmetries)
                                if h3_asymmetries
                                else None
                            ),
                            "positional_asymmetry_support_fraction": (
                                statistics.mean(value > 1e-12 for value in h3_asymmetries)
                                if h3_asymmetries
                                else None
                            ),
                            "leading_rival_B_on_fraction": statistics.mean(
                                item["on_state"] == "B" for item in h3_leading_rows
                            ),
                        },
                    }
                )
        print("overlap %.2f complete" % overlap, flush=True)

    primary_cell = next(
        cell
        for cell in phase_cells
        if math.isclose(cell["overlap_fraction"], 0.20)
        and math.isclose(cell["effective_access_fraction"], 0.25)
        and math.isclose(cell["manipulation_strength"], 1.0)
    )
    payload = {
        "status": "frozen_ca3_hypothesis_phase_map_v1",
        "architecture_changed_for_hypothesis_map": False,
        "inference_boundary": (
            "Structural realizations quantify model robustness, not animal sampling variance. "
            "Behavioral beta and biological parameter distributions require pilot calibration."
        ),
        "design": {
            "profile": args.profile,
            "n_cells": SparseAttractorConfig.for_profile(args.profile).n_cells,
            "seeds": args.seeds,
            "engram_fraction": args.engram_fraction,
            "activation_threshold": args.threshold,
            "tone_scale": args.tone_scale,
            "overlap_fractions": args.overlaps,
            "effective_access_fractions": args.effective_access,
            "manipulation_strengths": args.strengths,
            "inverse_temperatures": args.inverse_temperatures,
            "effective_access_isolated": True,
            "upstream_access_mapping": (
                "RAM tagging efficiency x fiber coverage x bare-A/test-A match, "
                "with exact cellular intersection used by the model"
            ),
        },
        "hypothesis_contract": {
            "H1_original_strong": (
                "A-context suppression should drive signed retrieval evidence toward zero "
                "or disrupt the A attractor"
            ),
            "H1_minimal_neural": "suppression lowers A-minus-B evidence and tagged reactivation",
            "H2": "A activation in B shifts evidence toward A and may cross into the A basin",
            "H3_original_strong": (
                "when A is cue-leading, A suppression should reverse retrieval to B"
            ),
            "H3_positional": (
                "the suppression effect is larger when A is leading than when A is trailing; "
                "signed interaction deltaE_leading-deltaE_trailing is negative"
            ),
        },
        "primary_predata_point": {
            "overlap_fraction": 0.20,
            "effective_access_fraction": 0.25,
            "manipulation_strength": 1.0,
            "aggregate": primary_cell,
            "paired_structural_realizations": primary_pairs,
        },
        "phase_cells": phase_cells,
        "runtime_seconds": time.time() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("saved %s" % args.output, flush=True)


if __name__ == "__main__":
    main()
