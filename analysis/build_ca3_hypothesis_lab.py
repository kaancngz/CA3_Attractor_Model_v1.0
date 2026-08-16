"""Build the no-server interactive hypothesis lab from exact phase-map outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase-map", type=Path, required=True)
    parser.add_argument("--ablations", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--standalone-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    phase = json.loads(args.phase_map.read_text(encoding="utf-8"))
    ablations = json.loads(args.ablations.read_text(encoding="utf-8"))
    beta_values = phase["design"]["inverse_temperatures"]
    beta_key = lambda value: "%g" % value
    reduced_cells = []
    for cell in phase["phase_cells"]:
        h1 = cell["H1"]
        h2 = cell["H2"]
        h3 = cell["H3"]
        reduced_cells.append(
            {
                "o": cell["overlap_fraction"],
                "a": cell["effective_access_fraction"],
                "s": cell["manipulation_strength"],
                "h1de": round(h1["mean_delta_evidence"], 6),
                "h1non": round(h1["non_A_on_fraction"], 6),
                "h1chance": round(h1["near_chance_on_fraction"], 6),
                "h1react": round(h1["mean_delta_tagged_reactivation"], 6),
                "h1dr": {
                    beta_key(beta): round(
                        h1["behavioral_envelope"][str(beta)][
                            "mean_delta_expected_discrimination"
                        ],
                        6,
                    )
                    for beta in beta_values
                },
                "h2de": round(h2["mean_delta_evidence"], 6),
                "h2a": round(h2["A_on_fraction"], 6),
                "h2dr": {
                    beta_key(beta): round(
                        h2["behavioral_envelope"][str(beta)][
                            "mean_delta_expected_discrimination"
                        ],
                        6,
                    )
                    for beta in beta_values
                },
                "h3q": round(h3["baseline_qualified_fraction"], 6),
                "h3i": (
                    None
                    if h3["mean_signed_interaction"] is None
                    else round(h3["mean_signed_interaction"], 6)
                ),
                "h3as": (
                    None
                    if h3["positional_asymmetry_support_fraction"] is None
                    else round(h3["positional_asymmetry_support_fraction"], 6)
                ),
                "h3b": round(h3["leading_rival_B_on_fraction"], 6),
                "h3lead": round(h3["A_leading"]["mean_delta_evidence"], 6),
                "h3trail": round(h3["A_trailing"]["mean_delta_evidence"], 6),
                "h3dr": {
                    beta_key(beta): round(
                        h3["A_leading"]["behavioral_envelope"][str(beta)][
                            "mean_delta_expected_discrimination"
                        ]
                        - h3["A_trailing"]["behavioral_envelope"][str(beta)][
                            "mean_delta_expected_discrimination"
                        ],
                        6,
                    )
                    for beta in beta_values
                },
            }
        )
    reduced_ablations = [
        {
            "name": regime["regime"],
            "gates": regime["validation_all_gates_fraction"],
            "h2A": regime["H2"]["on_state_fractions"]["A"],
            "h2Mixed": regime["H2"]["on_state_fractions"]["mixed"],
            "h3Qualified": regime["H3"]["baseline_qualified_fraction"],
            "h3Interaction": regime["H3"]["mean_signed_interaction"],
        }
        for regime in ablations["regimes"]
    ]
    data = {
        "overlaps": phase["design"]["overlap_fractions"],
        "accesses": phase["design"]["effective_access_fractions"],
        "strengths": phase["design"]["manipulation_strengths"],
        "betas": beta_values,
        "cells": reduced_cells,
        "ablations": reduced_ablations,
        "nStructures": len(phase["design"]["seeds"]),
    }
    template = args.template.read_text(encoding="utf-8")
    if template.count("__CA3_DATA__") != 1:
        raise RuntimeError("template must contain exactly one __CA3_DATA__ placeholder")
    fragment = template.replace(
        "__CA3_DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(fragment, encoding="utf-8")
    print("saved %s (%d bytes)" % (args.output, len(fragment.encode("utf-8"))))
    if args.standalone_output is not None:
        standalone = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CA3 Hipotez Laboratuvarı</title>
</head>
<body>
%s
</body>
</html>
""" % fragment
        args.standalone_output.parent.mkdir(parents=True, exist_ok=True)
        args.standalone_output.write_text(standalone, encoding="utf-8")
        print(
            "saved %s (%d bytes)"
            % (args.standalone_output, len(standalone.encode("utf-8")))
        )


if __name__ == "__main__":
    main()
