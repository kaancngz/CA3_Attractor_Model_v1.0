"""Turning network state into the quantities the experiment actually measures.

The definitions here are taken from two papers, deliberately:

  * active cell / engram cell threshold, and the overlap metric
        Kim & Kim (2025), PLoS Comput Biol 21(7):e1013267, "Similarity analysis"
  * normalised discrimination index, and the distinction between the set
    labelled at encoding and the set active at recall
        Feitosa Tome et al. (2022), Nat Neurosci, "Dynamic and selective
        engrams emerge with memory consolidation"

The second is what lets the model speak to a RAM/DOX labelling experiment at
all: the labelled ensemble is not the ensemble that is active at test.
"""

from __future__ import annotations

import numpy as np

from .engrams import Engram
from .network import Result
from .params import CA3Params


def active_cells(p: CA3Params, res: Result) -> np.ndarray:
    """Indices of excitatory cells firing above the analysis threshold."""
    return np.flatnonzero(res.exc_rates_hz >= p.active_thresh_hz)


def engram_rate(res: Result, eg: Engram) -> float:
    """Mean firing rate (Hz) over an engram's excitatory cells."""
    return float(res.exc_rates_hz[eg.exc].mean())


def discrimination_index(res: Result, target: Engram, rival: Engram) -> float:
    """(target - rival) / (target + rival), in [-1, +1].

    Same normalised form as the experiment's digging discrimination ratio and
    as Feitosa Tome et al.'s recall discrimination index.  0 means no
    preference; negative means the rival won.
    """
    a, b = engram_rate(res, target), engram_rate(res, rival)
    if a + b <= 0.0:
        return 0.0
    return (a - b) / (a + b)


def winner(p: CA3Params, res: Result, engrams: list[Engram]) -> int | None:
    """Index of the dominant engram, or None if none reached threshold.

    Kim & Kim count a trial as a retrieval failure when no assembly achieves
    dominance; we keep that, since 'nothing was retrieved' and 'the rival was
    retrieved' are different outcomes behaviourally.
    """
    rates = [engram_rate(res, eg) for eg in engrams]
    best = int(np.argmax(rates))
    return best if rates[best] >= p.active_thresh_hz else None


def reactivation_rate(p: CA3Params, res: Result, labelled: np.ndarray) -> float:
    """Fraction of the labelled ensemble that is active at recall.

    This is the model's version of the histological measure: double-positive
    cells / total labelled cells.
    """
    if labelled.size == 0:
        return 0.0
    act = np.zeros(p.n_exc, dtype=bool)
    act[active_cells(p, res)] = True
    return float(act[labelled].mean())


def chance_reactivation(p: CA3Params, res: Result, labelled: np.ndarray) -> float:
    """Chance-level double-labelling: labelled fraction x active fraction.

    The experiment compares observed co-labelling against exactly this
    product (README section 1.7).  If the model cannot reproduce the chance
    level, the model's and the experiment's definitions disagree.
    """
    frac_labelled = labelled.size / p.n_exc
    frac_active = active_cells(p, res).size / p.n_exc
    return float(frac_labelled * frac_active)


def overlap_dice(a: np.ndarray, b: np.ndarray) -> float:
    """2|A n B| / (|A| + |B|). 1.0 for identical sets, 0.0 for disjoint."""
    inter = np.intersect1d(a, b).size
    total = a.size + b.size
    return 0.0 if total == 0 else 2.0 * inter / total


def overlap_kk(a: np.ndarray, b: np.ndarray) -> float:
    """|A n B| / (|A| + |B|), the metric exactly as printed in Kim & Kim Eq. 6.

    Note this maxes out at 0.5 for identical sets, although the paper's text
    describes 1.0 as identical.  Kept so their overlap axis can be reproduced,
    but `overlap_dice` is what we report.
    """
    inter = np.intersect1d(a, b).size
    total = a.size + b.size
    return 0.0 if total == 0 else inter / total


def make_cue(p: CA3Params, a: Engram, b: Engram, bias: float,
             rng: np.random.Generator) -> np.ndarray:
    """A cue that is `bias` similar to engram a and (1 - bias) similar to b.

    bias = 0.5 gives the unbiased cue that forces the competition; bias = 1.0
    is a clean cue for a.  Same construction as Kim & Kim's graded cue task.
    """
    size = int(p.n_ec // 2)
    pat_a = np.flatnonzero(a.ec_pattern)
    pat_b = np.flatnonzero(b.ec_pattern)

    n_from_a = int(round(bias * size))
    take_a = rng.choice(pat_a, size=min(n_from_a, pat_a.size), replace=False)
    remaining = size - take_a.size
    pool_b = np.setdiff1d(pat_b, take_a)
    take_b = rng.choice(pool_b, size=min(remaining, pool_b.size), replace=False)

    cue = np.zeros(p.n_ec, dtype=np.float32)
    cue[np.concatenate([take_a, take_b]).astype(int)] = 1.0
    return cue
