"""Exhaustive role audit for every parameter of the primary CA3 model."""

from __future__ import annotations

import argparse
import json
from dataclasses import fields
from pathlib import Path

from .config import SparseAttractorConfig


CONFIG_PARAMETER_ROLES = {
    "profile": ("computational", "runtime scale profile"),
    "n_cells": ("computational", "network resolution, not mouse CA3 cell count"),
    "engram_fraction": ("free_pilot", "replace with cellular activity estimate"),
    "overlap_fraction": ("free_pilot", "replace with measured A/B cellular overlap"),
    "recurrent_gain": ("theory_normalization", "defines normalized recurrent field unit"),
    "activation_threshold": (
        "independently_qualified",
        "midpoint of H1-H3-blind attractor-validity plateau",
    ),
    "max_active_fraction": (
        "theory_linked",
        "fast inhibition reduction, tied to engram fraction",
    ),
    "cue_gain": ("theory_normalization", "defines external-field unit"),
    "cue_target_fraction": (
        "free_design",
        "strong partial-cue fraction used in independent qualification",
    ),
    "weak_cue_target_fraction": (
        "free_design",
        "subthreshold cue control used in independent qualification",
    ),
    "tagging_efficiency": ("free_pilot", "replace with RAM histology"),
    "fiber_coverage": ("free_pilot", "replace with expression/light-volume estimate"),
    "tag_test_match_fraction": (
        "free_pilot",
        "replace with bare-A versus final-A cellular match",
    ),
    "max_steps": ("computational", "convergence safety ceiling"),
    "seed": ("computational", "reproducible structural realization"),
}


EXTERNAL_PARAMETER_ROLES = {
    "learned_support_lambda": (
        "free_pilot",
        "replace probability-to-retrieval mapping with tone pilot",
    ),
    "tone_cue_scale": ("free_pilot", "calibrate cue efficacy, separate from lambda"),
    "manipulation_strength": (
        "free_pilot",
        "calibrate ArchT/ChR2 efficacy; phase map sweeps it",
    ),
    "behavior_inverse_temperature_beta": (
        "free_pilot",
        "calibrate signed neural evidence to digging discrimination",
    ),
    "pre_cue_light_steps": (
        "computational_protocol",
        "represents light-before-cue ordering, not elapsed biological seconds",
    ),
    "effective_access_fraction": (
        "derived",
        "exact accessible-tag intersection with final A; phase-map axis",
    ),
}


def build_audit() -> dict:
    config_fields = {item.name for item in fields(SparseAttractorConfig)}
    classified_fields = set(CONFIG_PARAMETER_ROLES)
    missing = sorted(config_fields - classified_fields)
    stale = sorted(classified_fields - config_fields)
    if missing or stale:
        raise RuntimeError(
            "parameter audit mismatch; missing=%r stale=%r" % (missing, stale)
        )
    config_rows = [
        {
            "name": name,
            "default": getattr(SparseAttractorConfig(), name),
            "role": role,
            "justification": justification,
        }
        for name, (role, justification) in CONFIG_PARAMETER_ROLES.items()
    ]
    external_rows = [
        {"name": name, "role": role, "justification": justification}
        for name, (role, justification) in EXTERNAL_PARAMETER_ROLES.items()
    ]
    all_rows = config_rows + external_rows
    return {
        "status": "complete_parameter_role_audit_v1",
        "all_config_fields_classified": True,
        "n_config_parameters": len(config_rows),
        "n_external_mapping_parameters": len(external_rows),
        "n_free_pilot_primitives": sum(
            row["role"] == "free_pilot" for row in all_rows
        ),
        "n_fitted_to_H1_H2_H3": 0,
        "phase_map_axes": [
            "overlap_fraction",
            "effective_access_fraction",
            "manipulation_strength",
        ],
        "note": (
            "Effective access is derived from tagging, coverage and tag-test match; "
            "it is counted as an axis but not as an additional fitted primitive."
        ),
        "config_parameters": config_rows,
        "external_parameters": external_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = build_audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("saved %s" % args.output)


if __name__ == "__main__":
    main()
