"""Basin and H1-H3 sweeps on the independently qualified sparse core."""

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
from models.ca3_sparse_attractor.cli import parse_float_list, parse_int_list
from models.ca3_sparse_attractor.theory_mapping import (
    expected_choice_discrimination,
    learned_context_support,
    paired_cohens_dz,
)


def final_summary(result: dict) -> dict:
    return result["convergence"]["trajectory"][-1]


def with_behavioral_envelope(summary: dict, inverse_temperatures: list[float]) -> dict:
    # The normalized competition index identifies the winning attractor but
    # discards absolute retrieval strength (any A>0, B=0 gives NCI=1).  Choice
    # therefore uses the signed unnormalized A-minus-B evidence so that a weak
    # but correctly oriented retrieval can approach chance.
    neural = summary["signed_retrieval_evidence"]
    return {
        **summary,
        "expected_choice_discrimination_by_inverse_temperature": {
            str(value): expected_choice_discrimination(neural, value)
            for value in inverse_temperatures
        },
    }


def run_basin_map(
    model: SparseCA3Attractor,
    lambdas: list[float],
    cue_scales: list[float],
    inverse_temperatures: list[float],
) -> list[dict]:
    rows = []
    initial_states = {
        "A": model.pattern_state("A"),
        "neutral": model.empty_state(),
        "B": model.pattern_state("B"),
    }
    for cue_scale in cue_scales:
        for lambda_a in lambdas:
            condition = AttractorCondition(
                "lambda_%.2f_scale_%.2f" % (lambda_a, cue_scale),
                cue_scale * lambda_a,
                cue_scale * (1.0 - lambda_a),
                cue_target_fraction=0.20,
            )
            for initial_name, initial_state in initial_states.items():
                for cue_remains_on in (False, True):
                    result = model.run_condition(
                        condition,
                        initial_state=initial_state,
                        cue_steps=1,
                        cue_remains_on=cue_remains_on,
                    )
                    rows.append(
                        {
                            "lambda_a": lambda_a,
                            "lambda_b": 1.0 - lambda_a,
                            "cue_scale": cue_scale,
                            "initial_state": initial_name,
                            "cue_mode": "sustained" if cue_remains_on else "cue_off",
                            "status": result["convergence"]["status"],
                            "steps": result["convergence"]["steps"],
                            "nominal_total_cue_field": result["nominal_total_cue_field"],
                            "summary": with_behavioral_envelope(
                                final_summary(result), inverse_temperatures
                            ),
                        }
                    )
    return rows


def hypothesis_conditions(tone_scale: float) -> dict:
    return {
        "H1_A_context": AttractorCondition("H1_A_context", 1.0, 0.0),
        "H2_B_context": AttractorCondition("H2_B_context", 0.0, 1.0),
        "H3_A_leading": AttractorCondition(
            "H3_A_leading", tone_scale * 0.65, tone_scale * 0.35
        ),
        "H3_A_trailing": AttractorCondition(
            "H3_A_trailing", tone_scale * 0.35, tone_scale * 0.65
        ),
        "P4_tone_absent_full_contingency": AttractorCondition(
            "P4_tone_absent_full_contingency", tone_scale * 0.35, tone_scale * 0.65
        ),
        "P4_tone_absent_presence_only": AttractorCondition(
            "P4_tone_absent_presence_only", tone_scale * 0.50, tone_scale * 0.50
        ),
    }


def run_hypothesis_sweep(
    model: SparseCA3Attractor,
    manipulation_fractions: list[float],
    manipulation_strengths: list[float],
    tone_scale: float,
    inverse_temperatures: list[float],
) -> dict:
    base_conditions = hypothesis_conditions(tone_scale)
    baselines = {}
    for label, condition in base_conditions.items():
        result = model.run_condition(condition, cue_remains_on=True)
        baselines[label] = {
            "status": result["convergence"]["status"],
            "steps": result["convergence"]["steps"],
            "summary": with_behavioral_envelope(
                final_summary(result), inverse_temperatures
            ),
        }

    rows = []
    protocols = {
        "H1_A_context": "suppress",
        "H2_B_context": "activate",
        "H3_A_leading": "suppress",
        "H3_A_trailing": "suppress",
    }
    for strength in manipulation_strengths:
        for fraction in manipulation_fractions:
            for label, manipulation in protocols.items():
                base = base_conditions[label]
                condition = AttractorCondition(
                    name="%s_%s" % (label, manipulation),
                    cue_a=base.cue_a,
                    cue_b=base.cue_b,
                    cue_target_fraction=base.cue_target_fraction,
                    manipulation=manipulation,
                    manipulation_strength=strength,
                    manipulation_fraction=fraction,
                )
                result = model.run_condition(condition, cue_remains_on=True)
                summary = with_behavioral_envelope(
                    final_summary(result), inverse_temperatures
                )
                baseline = baselines[label]["summary"]
                rows.append(
                    {
                        "protocol": label,
                        "manipulation": manipulation,
                        "requested_manipulation_fraction": fraction,
                        "manipulation_strength": strength,
                        "manipulated_count": result["manipulated_count"],
                        "effective_manipulated_final_a_fraction": result[
                            "effective_manipulated_final_a_fraction"
                        ],
                        "baseline_summary": baseline,
                        "manipulated_summary": summary,
                        "neural_competition_delta": (
                            summary["neural_competition_index"]
                            - baseline["neural_competition_index"]
                        ),
                        "reactivation_delta": (
                            summary["tagged_reactivation"]
                            - baseline["tagged_reactivation"]
                        ),
                        "a_engram_activity_delta": (
                            summary["a_engram_activity"]
                            - baseline["a_engram_activity"]
                        ),
                        "signed_retrieval_evidence_delta": (
                            summary["signed_retrieval_evidence"]
                            - baseline["signed_retrieval_evidence"]
                        ),
                        "active_fraction_delta": (
                            summary["active_fraction"] - baseline["active_fraction"]
                        ),
                    }
                )
    return {"baselines": baselines, "rows": rows}


def summarize_cohort(seed_results: list[dict]) -> list[dict]:
    keys = sorted(
        {
            (
                row["protocol"],
                row["requested_manipulation_fraction"],
                row["manipulation_strength"],
            )
            for seed in seed_results
            for row in seed["hypothesis_sweep"]["rows"]
        }
    )
    summaries = []
    for protocol, fraction, strength in keys:
        matched = [
            row
            for seed in seed_results
            for row in seed["hypothesis_sweep"]["rows"]
            if row["protocol"] == protocol
            and row["requested_manipulation_fraction"] == fraction
            and row["manipulation_strength"] == strength
        ]
        deltas = [row["neural_competition_delta"] for row in matched]
        off = [row["baseline_summary"]["neural_competition_index"] for row in matched]
        on = [row["manipulated_summary"]["neural_competition_index"] for row in matched]
        summaries.append(
            {
                "protocol": protocol,
                "requested_manipulation_fraction": fraction,
                "manipulation_strength": strength,
                "n_virtual_animals": len(matched),
                "mean_effective_manipulated_final_a_fraction": statistics.mean(
                    row["effective_manipulated_final_a_fraction"] for row in matched
                ),
                "mean_neural_competition_delta": statistics.mean(deltas),
                "mean_signed_retrieval_evidence_delta": statistics.mean(
                    row["signed_retrieval_evidence_delta"] for row in matched
                ),
                "mean_a_engram_activity_delta": statistics.mean(
                    row["a_engram_activity_delta"] for row in matched
                ),
                "mean_tagged_reactivation_delta": statistics.mean(
                    row["reactivation_delta"] for row in matched
                ),
                "mean_active_fraction_delta": statistics.mean(
                    row["active_fraction_delta"] for row in matched
                ),
                "min_neural_competition_delta": min(deltas),
                "max_neural_competition_delta": max(deltas),
                "paired_cohens_dz_neural": paired_cohens_dz(on, off),
                "manipulated_state_counts": {
                    state_class: sum(
                        row["manipulated_summary"]["state_class"] == state_class
                        for row in matched
                    )
                    for state_class in ("A", "B", "mixed", "silent", "undecided")
                },
            }
        )
    return summaries


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("smoke", "pilot", "full"), default="pilot")
    parser.add_argument(
        "--seeds",
        type=parse_int_list,
        default=parse_int_list("20260815,20260816,20260817,20260818,20260819"),
    )
    parser.add_argument("--threshold", type=float, default=0.12)
    parser.add_argument("--engram-fraction", type=float, default=0.08)
    parser.add_argument("--overlap", type=float, default=0.20)
    parser.add_argument("--tagging-efficiency", type=float, default=0.50)
    parser.add_argument("--fiber-coverage", type=float, default=0.50)
    parser.add_argument("--tag-test-match", type=float, default=1.0)
    parser.add_argument(
        "--lambdas",
        type=parse_float_list,
        default=parse_float_list("0,0.2,0.35,0.4,0.5,0.6,0.65,0.8,1.0"),
    )
    parser.add_argument(
        "--cue-scales", type=parse_float_list, default=parse_float_list("0.25,0.5,1.0")
    )
    parser.add_argument("--tone-scale", type=float, default=0.50)
    parser.add_argument(
        "--manipulation-fractions",
        type=parse_float_list,
        default=parse_float_list("0,0.05,0.10,0.15,0.20,0.25"),
    )
    parser.add_argument(
        "--manipulation-strengths",
        type=parse_float_list,
        default=parse_float_list("0.25,0.50,1.00,2.00,4.00"),
    )
    parser.add_argument(
        "--inverse-temperatures",
        type=parse_float_list,
        default=parse_float_list("1,2,4,8"),
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started = time.time()
    seed_results = []
    for seed in args.seeds:
        config = SparseAttractorConfig.for_profile(
            args.profile,
            seed=seed,
            activation_threshold=args.threshold,
            engram_fraction=args.engram_fraction,
            overlap_fraction=args.overlap,
            max_active_fraction=args.engram_fraction,
            tagging_efficiency=args.tagging_efficiency,
            fiber_coverage=args.fiber_coverage,
            tag_test_match_fraction=args.tag_test_match,
        )
        model = SparseCA3Attractor(config)
        basin = run_basin_map(
            model, args.lambdas, args.cue_scales, args.inverse_temperatures
        )
        hypothesis = run_hypothesis_sweep(
            model,
            args.manipulation_fractions,
            args.manipulation_strengths,
            args.tone_scale,
            args.inverse_temperatures,
        )
        seed_results.append(
            {
                "seed": seed,
                "engram_counts": model.layout.as_counts(),
                "tag_source_count": int(model.tag_source.size),
                "tagged_count": int(model.tagged.size),
                "accessible_count": int(model.accessible.size),
                "tagged_final_a_count": int(
                    len(set(model.tagged).intersection(model.layout.a))
                ),
                "basin_map": basin,
                "hypothesis_sweep": hypothesis,
            }
        )
        print("seed %d complete" % seed, flush=True)

    tone_mappings = {
        "tone_present_A_high": learned_context_support(0.65, 0.35, tone_present=True),
        "tone_absent_full_contingency": learned_context_support(
            0.65, 0.35, tone_present=False, absence_rule="full_contingency"
        ),
        "tone_absent_presence_only": learned_context_support(
            0.65, 0.35, tone_present=False, absence_rule="presence_only"
        ),
    }
    payload = {
        "status": "primary_sparse_attractor_theory_experiments_v1",
        "architecture_selected_without_H1_H2_H3": True,
        "candidate": {
            "profile": args.profile,
            "activation_threshold": args.threshold,
            "engram_fraction": args.engram_fraction,
            "overlap_fraction": args.overlap,
            "tagging_efficiency": args.tagging_efficiency,
            "fiber_coverage": args.fiber_coverage,
            "tag_test_match_fraction": args.tag_test_match,
        },
        "epistemic_contract": {
            "lambda": "normalized learned context support, not physical tone intensity",
            "neural_readouts": (
                "normalized A/B unique-cell competition identifies attractor identity; "
                "signed A-minus-B evidence retains absolute retrieval strength"
            ),
            "behavioral_readout": (
                "logistic envelope of signed retrieval evidence; inverse temperature is "
                "free/pilot, so neural evidence and digging discrimination are not identified"
            ),
            "effect_size_warning": (
                "structural-seed Cohen dz is descriptive only and is not a sampling distribution "
                "or a power-analysis input"
            ),
            "novel_context_C": (
                "no A/B-specific context field; only learned tone support acts in the A/B subspace"
            ),
            "RAM": (
                "bare-A tag source, tagging efficiency, tag-test match, and light accessibility "
                "are separate operations"
            ),
        },
        "design": {
            "seeds": args.seeds,
            "lambdas": args.lambdas,
            "cue_scales": args.cue_scales,
            "tone_scale": args.tone_scale,
            "manipulation_fractions": args.manipulation_fractions,
            "manipulation_strengths": args.manipulation_strengths,
            "inverse_temperatures": args.inverse_temperatures,
        },
        "training_probability_mappings": tone_mappings,
        "seed_results": seed_results,
        "cohort_summary": summarize_cohort(seed_results),
        "runtime_seconds": time.time() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("saved %s" % args.output, flush=True)


if __name__ == "__main__":
    main()
