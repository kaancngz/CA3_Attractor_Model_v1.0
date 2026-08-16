from __future__ import annotations

import unittest

import numpy as np

from models.ca3_sparse_attractor.config import SparseAttractorConfig
from models.ca3_sparse_attractor.model import AttractorCondition, SparseCA3Attractor
from models.ca3_sparse_attractor.parameter_audit import build_audit
from models.ca3_sparse_attractor.run_recall_probe_protocol import (
    asymptotic_summary,
    build_probe_arms,
    counterbalance_assignment,
    pair_probe_rows,
    run_probe,
    run_recall_qualification,
)


class SparseAttractorTests(unittest.TestCase):
    def test_recall_probe_arms_cover_all_experimental_groups(self):
        arms = build_probe_arms()
        self.assertEqual({arm.experimental_group for arm in arms}, {"G1", "G2", "G3", "G4"})
        self.assertEqual(sum(arm.hypothesis == "H3" for arm in arms), 2)
        self.assertEqual(sum(arm.vector == "EGFP" for arm in arms), 4)

    def test_pre_cue_light_order_is_explicit(self):
        model = SparseCA3Attractor(
            SparseAttractorConfig.for_profile(
                "smoke", tagging_efficiency=1.0, fiber_coverage=1.0
            )
        )
        result = model.run_condition(
            AttractorCondition(
                "preactivate_A",
                0.0,
                1.0,
                manipulation="activate",
                manipulation_strength=1.0,
            ),
            pre_cue_steps=1,
            cue_remains_on=True,
        )
        self.assertEqual(result["pre_cue_steps"], 1)
        self.assertGreater(
            result["pre_cue_trajectory"][-1]["active_fraction"], 0.0
        )
        summary, meta = asymptotic_summary(result)
        self.assertEqual(summary["state_class"], "A")
        self.assertTrue(meta["macrostate_stable_across_cycle"])

    def test_recall_probe_qualification_and_egfp_invariance(self):
        model = SparseCA3Attractor(SparseAttractorConfig.for_profile("smoke"))
        self.assertTrue(run_recall_qualification(model)["passed"])
        control = next(
            arm
            for arm in build_probe_arms()
            if arm.arm_id == "EGFP_TAGGED_CONTEXT_CONTROL"
        )
        assignment = counterbalance_assignment(0)
        common = {
            "model": model,
            "arm": control,
            "manipulation_strength": 1.0,
            "pre_light_steps": 1,
            "inverse_temperatures": [2.0],
            "network_id": "test_network",
            "seed": model.config.seed,
            "assignment": assignment,
            "recall_qualified": True,
        }
        off = run_probe(light_state="off", **common)
        on = run_probe(light_state="on", **common)
        pair = pair_probe_rows(off, on, [2.0])
        self.assertEqual(pair["delta_evidence"], 0.0)
        self.assertEqual(pair["delta_tagged_reactivation"], 0.0)

    def test_every_model_parameter_has_an_explicit_role(self):
        audit = build_audit()
        self.assertTrue(audit["all_config_fields_classified"])
        self.assertEqual(audit["n_fitted_to_H1_H2_H3"], 0)

    def test_primary_hypothesis_directions_at_frozen_point(self):
        model = SparseCA3Attractor(
            SparseAttractorConfig.for_profile(
                "smoke",
                tagging_efficiency=1.0,
                fiber_coverage=1.0,
                tag_test_match_fraction=1.0,
            )
        )

        def evidence(condition):
            result = model.run_condition(condition, cue_remains_on=True)
            return result["convergence"]["trajectory"][-1]

        h1_off = evidence(AttractorCondition("H1_off", 1.0, 0.0))
        h1_on = evidence(
            AttractorCondition(
                "H1_on", 1.0, 0.0,
                manipulation="suppress",
                manipulation_strength=1.0,
                manipulation_fraction=0.25,
            )
        )
        self.assertLess(
            h1_on["signed_retrieval_evidence"],
            h1_off["signed_retrieval_evidence"],
        )

        h2_on = evidence(
            AttractorCondition(
                "H2_on", 0.0, 1.0,
                manipulation="activate",
                manipulation_strength=1.0,
                manipulation_fraction=0.25,
            )
        )
        self.assertEqual(h2_on["state_class"], "A")

        leading_off = evidence(AttractorCondition("lead_off", 0.325, 0.175))
        leading_on = evidence(
            AttractorCondition(
                "lead_on", 0.325, 0.175,
                manipulation="suppress",
                manipulation_strength=1.0,
                manipulation_fraction=0.25,
            )
        )
        trailing_off = evidence(AttractorCondition("trail_off", 0.175, 0.325))
        trailing_on = evidence(
            AttractorCondition(
                "trail_on", 0.175, 0.325,
                manipulation="suppress",
                manipulation_strength=1.0,
                manipulation_fraction=0.25,
            )
        )
        leading_delta = (
            leading_on["signed_retrieval_evidence"]
            - leading_off["signed_retrieval_evidence"]
        )
        trailing_delta = (
            trailing_on["signed_retrieval_evidence"]
            - trailing_off["signed_retrieval_evidence"]
        )
        self.assertLess(leading_delta, trailing_delta)

    def test_ablation_values_are_explicitly_allowed(self):
        SparseAttractorConfig(recurrent_gain=0.0).validate()
        SparseAttractorConfig(max_active_fraction=1.0).validate()

    def test_factorized_field_matches_dense_zero_diagonal_covariance(self):
        config = SparseAttractorConfig(n_cells=200, seed=7)
        model = SparseCA3Attractor(config)
        state = model.pattern_state("A")
        dense_weights = (
            model.centered_patterns.T @ model.centered_patterns
        ) / model.normalization
        np.fill_diagonal(dense_weights, 0.0)
        expected = config.recurrent_gain * (dense_weights @ state.astype(float))
        np.testing.assert_allclose(model.recurrent_field(state), expected, atol=1e-12)

    def setUp(self):
        self.model = SparseCA3Attractor(
            SparseAttractorConfig.for_profile("smoke", activation_threshold=0.14)
        )

    def test_stored_patterns_are_fixed_points(self):
        for memory in ("A", "B"):
            state = self.model.pattern_state(memory)
            result = self.model.converge(state)
            self.assertEqual(result["status"], "fixed_point")
            self.assertTrue((result["final_state"] == state).all())

    def test_fixed_total_mixture_cue_field(self):
        totals = []
        for lambda_a in (0.0, 0.35, 0.50, 0.65, 1.0):
            condition = AttractorCondition(
                "mixture", lambda_a, 1.0 - lambda_a, cue_target_fraction=0.20
            )
            _, meta = self.model._cue_field(condition)
            totals.append(meta["nominal_total_cue_field"])
        for total in totals[1:]:
            self.assertAlmostEqual(total, totals[0])

    def test_tag_source_match_is_separate_from_efficiency(self):
        model = SparseCA3Attractor(
            SparseAttractorConfig.for_profile(
                "smoke",
                tag_test_match_fraction=0.50,
                tagging_efficiency=0.50,
            )
        )
        self.assertEqual(model.tag_source.size, model.layout.a.size)
        self.assertEqual(
            len(set(model.tag_source).intersection(model.layout.a)),
            round(model.layout.a.size * 0.50),
        )


if __name__ == "__main__":
    unittest.main()
