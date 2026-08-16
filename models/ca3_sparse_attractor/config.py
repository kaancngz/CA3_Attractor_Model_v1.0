"""Configuration for the sparse cellular CA3 attractor core."""

from __future__ import annotations

from dataclasses import dataclass, replace


PROFILES = {"smoke": 1_200, "pilot": 2_400, "full": 10_000}


@dataclass(frozen=True)
class SparseAttractorConfig:
    profile: str = "pilot"
    n_cells: int = 2_400
    engram_fraction: float = 0.08
    overlap_fraction: float = 0.20

    # Standard centered Hebbian/covariance autoassociation.  The activity cap
    # is the reduced representation of fast global inhibition.
    recurrent_gain: float = 1.0
    activation_threshold: float = 0.12
    max_active_fraction: float = 0.08

    cue_gain: float = 1.0
    cue_target_fraction: float = 0.20
    weak_cue_target_fraction: float = 0.05

    tagging_efficiency: float = 0.50
    fiber_coverage: float = 0.50
    tag_test_match_fraction: float = 1.0

    max_steps: int = 100
    seed: int = 20260815

    @classmethod
    def for_profile(cls, profile: str, **overrides: object) -> "SparseAttractorConfig":
        if profile not in PROFILES:
            raise ValueError("unknown profile %r" % profile)
        return replace(cls(profile=profile, n_cells=PROFILES[profile]), **overrides)

    def validate(self) -> None:
        if self.profile not in PROFILES:
            raise ValueError("unknown profile %r" % self.profile)
        if self.n_cells < 100:
            raise ValueError("n_cells must be at least 100")
        if not 0.0 < self.engram_fraction < 0.5:
            raise ValueError("engram_fraction must be in (0, 0.5)")
        if not 0.0 <= self.overlap_fraction <= 1.0:
            raise ValueError("overlap_fraction must be in [0, 1]")
        if self.recurrent_gain < 0.0 or self.activation_threshold < 0.0:
            raise ValueError("recurrent_gain and threshold must be nonnegative")
        if not self.engram_fraction <= self.max_active_fraction <= 1.0:
            raise ValueError("max_active_fraction must cover an engram and be at most one")
        if self.cue_gain <= 0.0:
            raise ValueError("cue_gain must be positive")
        if not 0.0 < self.weak_cue_target_fraction < self.cue_target_fraction <= 1.0:
            raise ValueError("cue fractions must satisfy 0 < weak < strong <= 1")
        for name, value in (
            ("tagging_efficiency", self.tagging_efficiency),
            ("fiber_coverage", self.fiber_coverage),
            ("tag_test_match_fraction", self.tag_test_match_fraction),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("%s must be in [0, 1]" % name)
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")
