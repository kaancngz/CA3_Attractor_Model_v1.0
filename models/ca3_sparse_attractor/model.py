"""Sparse two-memory covariance attractor with explicit cellular overlap."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from .engrams import (
    balanced_cue_order,
    make_engram_layout,
    make_tag_source_representation,
    select_tagged_and_accessible,
)
from .theory_mapping import neural_competition_index

from .config import SparseAttractorConfig


@dataclass(frozen=True)
class AttractorCondition:
    name: str
    cue_a: float
    cue_b: float
    cue_target_fraction: float | None = None
    manipulation: str = "none"
    manipulation_strength: float = 0.0
    manipulation_fraction: float | None = None


class SparseCA3Attractor:
    """Factorized sparse autoassociative network storing A and B.

    The recurrent field is mathematically equivalent to a dense centered
    Hebbian weight matrix for the two stored patterns, but is evaluated in
    O(NP) memory/time.  A dynamic activity cap implements fast global
    inhibitory normalization without introducing another neural population.
    """

    def __init__(self, config: SparseAttractorConfig):
        config.validate()
        self.config = config
        self.rng = np.random.RandomState(config.seed)
        self.layout = make_engram_layout(
            config.n_cells,
            config.engram_fraction,
            config.overlap_fraction,
            self.rng,
        )
        self.tag_source = make_tag_source_representation(
            self.layout.a,
            config.n_cells,
            config.tag_test_match_fraction,
            self.rng,
        )
        self.tagged, self.accessible = select_tagged_and_accessible(
            self.tag_source,
            config.tagging_efficiency,
            config.fiber_coverage,
            self.rng,
        )
        self.intervention_order = self.rng.permutation(self.accessible)

        cue_rng = np.random.RandomState(config.seed + 10_000_019)
        self.cue_order_a = balanced_cue_order(
            self.layout.a_only, self.layout.shared, cue_rng
        )
        self.cue_order_b = balanced_cue_order(
            self.layout.b_only, self.layout.shared, cue_rng
        )

        patterns = np.zeros((2, config.n_cells), dtype=float)
        patterns[0, self.layout.a] = 1.0
        patterns[1, self.layout.b] = 1.0
        self.activity_fraction = self.layout.a.size / config.n_cells
        self.centered_patterns = patterns - self.activity_fraction
        self.normalization = (
            config.n_cells * self.activity_fraction * (1.0 - self.activity_fraction)
        )
        # Standard autoassociative networks omit autapses (W_ii = 0).  The
        # factorized field first evaluates the full covariance matrix, then
        # removes each active cell's exact diagonal contribution.
        self.diagonal_coupling = (
            np.sum(self.centered_patterns**2, axis=0) / self.normalization
        )
        self.max_active_count = round(config.n_cells * config.max_active_fraction)
        # Fixed infinitesimal ordering resolves exact field ties without
        # injecting trial noise or changing any non-tied decision.
        self.tie_break = self.rng.uniform(0.0, 1.0, config.n_cells) * 1e-12

    def empty_state(self) -> np.ndarray:
        return np.zeros(self.config.n_cells, dtype=np.int8)

    def pattern_state(self, memory: str) -> np.ndarray:
        state = self.empty_state()
        indices = self.layout.a if memory == "A" else self.layout.b
        state[indices] = 1
        return state

    def overlaps(self, state: np.ndarray) -> np.ndarray:
        return self.centered_patterns @ state.astype(float) / self.normalization

    def recurrent_field(self, state: np.ndarray) -> np.ndarray:
        state_float = state.astype(float)
        full_field = self.overlaps(state) @ self.centered_patterns
        zero_diagonal_field = full_field - self.diagonal_coupling * state_float
        return self.config.recurrent_gain * zero_diagonal_field

    def step(self, state: np.ndarray, external_field: np.ndarray | None = None) -> np.ndarray:
        field = self.recurrent_field(state)
        if external_field is not None:
            field = field + external_field
        candidates = np.flatnonzero(field >= self.config.activation_threshold)
        next_state = self.empty_state()
        if candidates.size <= self.max_active_count:
            next_state[candidates] = 1
            return next_state
        scores = field[candidates] + self.tie_break[candidates]
        winners = candidates[np.argpartition(scores, -self.max_active_count)[-self.max_active_count:]]
        next_state[winners] = 1
        return next_state

    def converge(
        self,
        initial_state: np.ndarray,
        external_field: np.ndarray | None = None,
    ) -> dict:
        state = initial_state.astype(np.int8, copy=True)
        trajectory = [self.summarize_state(state)]
        seen = {state.tobytes(): 0}
        status = "max_steps"
        cycle_length = None
        for step_index in range(1, self.config.max_steps + 1):
            next_state = self.step(state, external_field)
            trajectory.append(self.summarize_state(next_state))
            if np.array_equal(next_state, state):
                status = "fixed_point"
                state = next_state
                break
            key = next_state.tobytes()
            if key in seen:
                status = "cycle"
                cycle_length = step_index - seen[key]
                state = next_state
                break
            seen[key] = step_index
            state = next_state
        return {
            "status": status,
            "cycle_length": cycle_length,
            "steps": len(trajectory) - 1,
            "final_state": state,
            "trajectory": trajectory,
        }

    def _cue_field(self, condition: AttractorCondition) -> tuple[np.ndarray, dict]:
        fraction = (
            self.config.cue_target_fraction
            if condition.cue_target_fraction is None
            else condition.cue_target_fraction
        )
        if not 0.0 < fraction <= 1.0:
            raise ValueError("cue_target_fraction must be in (0, 1]")
        total_support = condition.cue_a + condition.cue_b
        if condition.cue_a < 0.0 or condition.cue_b < 0.0:
            raise ValueError("cue supports cannot be negative")
        n_cue_total = max(1, round(self.layout.a.size * fraction))
        if total_support > 0.0:
            lambda_a = condition.cue_a / total_support
            n_cue_a = round(n_cue_total * lambda_a)
        else:
            lambda_a = 0.5
            n_cue_a = 0
        n_cue_b = n_cue_total - n_cue_a if total_support > 0.0 else 0
        targets_a = self.cue_order_a[:n_cue_a]
        targets_b = self.cue_order_b[:n_cue_b]
        field = np.zeros(self.config.n_cells, dtype=float)
        field[targets_a] += self.config.cue_gain * total_support
        field[targets_b] += self.config.cue_gain * total_support
        return field, {
            "cue_target_fraction": fraction,
            "cue_target_count_a": int(targets_a.size),
            "cue_target_count_b": int(targets_b.size),
            "nominal_total_cue_field": float(field.sum()),
            "learned_support_lambda_a": float(lambda_a),
            "cue_target_budget": int(n_cue_total),
            "cue_support_encoding": "fixed_total_target_slots",
        }

    def _manipulation_field(self, condition: AttractorCondition) -> tuple[np.ndarray, dict]:
        field = np.zeros(self.config.n_cells, dtype=float)
        if condition.manipulation == "none":
            return field, {
                "manipulated_count": 0,
                "effective_manipulated_final_a_fraction": 0.0,
            }
        if condition.manipulation not in ("suppress", "activate"):
            raise ValueError("manipulation must be none, suppress or activate")
        if condition.manipulation_strength < 0.0:
            raise ValueError("manipulation_strength cannot be negative")
        if condition.manipulation_fraction is None:
            targets = self.accessible
        else:
            if not 0.0 <= condition.manipulation_fraction <= 1.0:
                raise ValueError("manipulation_fraction must be in [0, 1]")
            requested = round(self.layout.a.size * condition.manipulation_fraction)
            targets = self.intervention_order[:min(requested, self.intervention_order.size)]
        sign = -1.0 if condition.manipulation == "suppress" else 1.0
        field[targets] = sign * condition.manipulation_strength
        matched = np.intersect1d(targets, self.layout.a).size
        return field, {
            "manipulated_count": int(targets.size),
            "effective_manipulated_final_a_fraction": matched / self.layout.a.size,
        }

    def run_condition(
        self,
        condition: AttractorCondition,
        *,
        initial_state: np.ndarray | None = None,
        pre_cue_steps: int = 0,
        cue_steps: int = 1,
        cue_remains_on: bool = False,
    ) -> dict:
        if pre_cue_steps < 0:
            raise ValueError("pre_cue_steps cannot be negative")
        if cue_steps < 1:
            raise ValueError("cue_steps must be positive")
        state = self.empty_state() if initial_state is None else initial_state.copy()
        cue_field, cue_meta = self._cue_field(condition)
        manipulation_field, manipulation_meta = self._manipulation_field(condition)
        pre_cue_trajectory = [self.summarize_state(state)]
        for _ in range(pre_cue_steps):
            state = self.step(state, manipulation_field)
            pre_cue_trajectory.append(self.summarize_state(state))
        combined_field = cue_field + manipulation_field
        cue_trajectory = [self.summarize_state(state)]
        for _ in range(cue_steps):
            state = self.step(state, combined_field)
            cue_trajectory.append(self.summarize_state(state))
        post_field = combined_field if cue_remains_on else manipulation_field
        convergence = self.converge(state, post_field)
        return {
            "condition": asdict(condition),
            **cue_meta,
            **manipulation_meta,
            "pre_cue_steps": pre_cue_steps,
            "pre_cue_trajectory": pre_cue_trajectory,
            "cue_steps": cue_steps,
            "cue_remains_on": cue_remains_on,
            "cue_trajectory": cue_trajectory,
            "convergence": convergence,
        }

    def summarize_state(self, state: np.ndarray) -> dict:
        overlap_a, overlap_b = self.overlaps(state)
        a_unique_activity = float(np.mean(state[self.layout.a_only]))
        b_unique_activity = float(np.mean(state[self.layout.b_only]))
        shared_activity = float(np.mean(state[self.layout.shared])) if self.layout.shared.size else 0.0
        a_engram_activity = float(np.mean(state[self.layout.a]))
        b_engram_activity = float(np.mean(state[self.layout.b]))
        outside_activity = float(np.mean(state[self.layout.outside]))
        competition = neural_competition_index(a_unique_activity, b_unique_activity)
        signed_retrieval_evidence = a_unique_activity - b_unique_activity
        active_fraction = float(np.mean(state))
        if active_fraction < 0.01:
            state_class = "silent"
        elif competition >= 0.25 and a_unique_activity >= 0.50:
            state_class = "A"
        elif competition <= -0.25 and b_unique_activity >= 0.50:
            state_class = "B"
        elif a_unique_activity >= 0.25 and b_unique_activity >= 0.25:
            state_class = "mixed"
        else:
            state_class = "undecided"
        tagged_active = int(np.count_nonzero(state[self.tagged])) if self.tagged.size else 0
        reactivation = tagged_active / self.tagged.size if self.tagged.size else 0.0
        chance = active_fraction
        return {
            "overlap_a": float(overlap_a),
            "overlap_b": float(overlap_b),
            "overlap_margin_a_minus_b": float(overlap_a - overlap_b),
            "a_unique_activity": a_unique_activity,
            "b_unique_activity": b_unique_activity,
            "shared_activity": shared_activity,
            "a_engram_activity": a_engram_activity,
            "b_engram_activity": b_engram_activity,
            "outside_activity": outside_activity,
            "active_fraction": active_fraction,
            "neural_competition_index": competition,
            "signed_retrieval_evidence": signed_retrieval_evidence,
            "state_class": state_class,
            "tagged_reactivation": reactivation,
            "chance_reactivation": chance,
            "reactivation_enrichment": reactivation / chance if chance > 0.0 else None,
        }
