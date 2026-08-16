"""Construction and sampling utilities for sparse cellular engrams."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def balanced_cue_order(
    unique: np.ndarray, shared: np.ndarray, rng: np.random.RandomState
) -> np.ndarray:
    """Return a nested cue order with balanced shared-cell prefix counts."""
    unique_order = rng.permutation(unique)
    shared_order = rng.permutation(shared)
    total = unique_order.size + shared_order.size
    if total == 0:
        return np.array([], dtype=np.int64)
    order = np.empty(total, dtype=np.int64)
    unique_used = 0
    shared_used = 0
    for position in range(total):
        target_shared = round((position + 1) * shared_order.size / total)
        if shared_used < target_shared:
            order[position] = shared_order[shared_used]
            shared_used += 1
        else:
            order[position] = unique_order[unique_used]
            unique_used += 1
    return order


@dataclass(frozen=True)
class EngramLayout:
    a: np.ndarray
    b: np.ndarray
    shared: np.ndarray
    a_only: np.ndarray
    b_only: np.ndarray
    outside: np.ndarray

    def as_counts(self) -> dict:
        return {
            "a": int(self.a.size),
            "b": int(self.b.size),
            "shared": int(self.shared.size),
            "a_only": int(self.a_only.size),
            "b_only": int(self.b_only.size),
            "outside": int(self.outside.size),
        }


def make_engram_layout(
    n_e: int,
    engram_fraction: float,
    overlap_fraction: float,
    rng: np.random.RandomState,
) -> EngramLayout:
    """Create exact-size A and B sets with overlap relative to one engram."""
    n_engram = max(2, round(n_e * engram_fraction))
    n_shared = round(n_engram * overlap_fraction)
    n_unique = n_engram - n_shared
    required = n_shared + 2 * n_unique
    if required > n_e:
        raise ValueError("Engram size/overlap combination exceeds the population")

    order = rng.permutation(n_e)
    shared = np.sort(order[:n_shared])
    a_only = np.sort(order[n_shared : n_shared + n_unique])
    b_only = np.sort(order[n_shared + n_unique : required])
    outside = np.sort(order[required:])
    a = np.sort(np.concatenate((shared, a_only)))
    b = np.sort(np.concatenate((shared, b_only)))
    return EngramLayout(
        a=a,
        b=b,
        shared=shared,
        a_only=a_only,
        b_only=b_only,
        outside=outside,
    )


def make_tag_source_representation(
    final_a: np.ndarray,
    n_e: int,
    tag_test_match_fraction: float,
    rng: np.random.RandomState,
) -> np.ndarray:
    """Construct the bare-context A representation present during tagging."""
    if not 0.0 <= tag_test_match_fraction <= 1.0:
        raise ValueError("tag_test_match_fraction must be in [0, 1]")
    final_a = np.asarray(final_a, dtype=np.int64)
    if final_a.size > n_e:
        raise ValueError("final_a cannot contain more cells than n_e")
    n_retained = round(final_a.size * tag_test_match_fraction)
    n_turnover = final_a.size - n_retained
    complement = np.setdiff1d(np.arange(n_e, dtype=np.int64), final_a)
    if n_turnover > complement.size:
        raise ValueError("not enough non-A cells for the tag-source representation")
    retained = rng.permutation(final_a)[:n_retained]
    turnover = rng.permutation(complement)[:n_turnover]
    return np.sort(np.concatenate((retained, turnover)))


def select_tagged_and_accessible(
    a: np.ndarray,
    tagging_efficiency: float,
    fiber_coverage: float,
    rng: np.random.RandomState,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample the tagged A set and then the light-accessible subset."""
    shuffled = rng.permutation(a)
    n_tagged = round(a.size * tagging_efficiency)
    tagged = np.sort(shuffled[:n_tagged])
    n_accessible = round(tagged.size * fiber_coverage)
    accessible = np.sort(rng.permutation(tagged)[:n_accessible])
    return tagged, accessible
