"""Connectivity and engram construction for the CA3 competition model.

The mechanism we take from Kim & Kim (2025) is *selective inhibition*, and the
important thing about it is that it is not a plasticity rule on inhibitory
synapses.  It is a selection effect:

    During encoding, mossy fibres drive a set of interneurons I_k.  Those
    interneurons silence most excitatory cells.  The excitatory cells that
    survive are, by construction, the ones that happen to receive few
    inhibitory connections from I_k.  Those survivors become engram E_k.
    Hence I_k inhibits every other engram but barely touches its own.

Kim & Kim obtain E_k by simulating that encoding phase, which leaves them with
engrams of ~10 cells and no control over overlap.  We construct E_k directly
from the same criterion -- lowest inhibitory input from I_k -- which reproduces
the mechanism while making engram size and pairwise overlap explicit
parameters.  The `selective=False` path draws E_k at random instead, which is
the global-inhibition control: interneurons then inhibit their own engram as
much as any other.  That switch is the ablation the whole project turns on.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .params import CA3Params


@dataclass
class Connectivity:
    """Static wiring. Weights w are fixed; peak conductances q carry learning."""

    w_rc: np.ndarray      # (n_exc, n_exc) exc -> exc
    w_ei: np.ndarray      # (n_exc, n_inh) exc -> inh
    w_ie: np.ndarray      # (n_inh, n_exc) inh -> exc
    w_ii: np.ndarray      # (n_inh, n_inh) inh -> inh
    w_ec: np.ndarray      # (n_ec,  n_exc) EC  -> exc
    q_rc: np.ndarray
    q_ei: np.ndarray
    q_ie: np.ndarray
    q_ii: np.ndarray
    q_ec: np.ndarray


@dataclass
class Engram:
    """One stored memory."""

    exc: np.ndarray       # indices of excitatory cells
    inh: np.ndarray       # indices of the interneurons recruited with it
    ec_pattern: np.ndarray  # (n_ec,) binary input pattern that encodes it


def _mask_pre_view(rng, n_pre: int, n_post: int, n_targets: int) -> np.ndarray:
    """Each PREsynaptic cell projects to `n_targets` postsynaptic cells.

    This is KK-CODE's 'Pre_view' and it is the direction used for every
    connection inside CA3.  Getting it backwards makes inh->exc fully
    connected (120 partners requested out of 120 sources), which destroys the
    selection effect that selective inhibition depends on.
    """
    mask = np.zeros((n_pre, n_post), dtype=np.float32)
    for i in range(n_pre):
        idx = rng.choice(n_post, size=min(n_targets, n_post), replace=False)
        mask[i, idx] = 1.0
    return mask


def _mask_post_view(rng, n_pre: int, n_post: int, n_sources: int) -> np.ndarray:
    """Each POSTsynaptic cell draws `n_sources` presynaptic partners.

    KK-CODE's 'Post_view', used for the EC -> CA3 direct path.
    """
    mask = np.zeros((n_pre, n_post), dtype=np.float32)
    for j in range(n_post):
        idx = rng.choice(n_pre, size=min(n_sources, n_pre), replace=False)
        mask[idx, j] = 1.0
    return mask


def build_connectivity(p: CA3Params, rng: np.random.Generator) -> Connectivity:
    w_rc = _mask_pre_view(rng, p.n_exc, p.n_exc, p.c_rc) * p.w_rc
    np.fill_diagonal(w_rc, 0.0)
    w_ei = _mask_pre_view(rng, p.n_exc, p.n_inh, p.c_ei) * p.w_ei
    w_ie = _mask_pre_view(rng, p.n_inh, p.n_exc, p.c_ie) * p.w_ie
    w_ii = _mask_pre_view(rng, p.n_inh, p.n_inh, p.c_ii) * p.w_ii
    np.fill_diagonal(w_ii, 0.0)          # KK-CODE zeroes inh self-connections
    w_ec = _mask_post_view(rng, p.n_ec, p.n_exc, p.c_ec) * p.w_ec

    # Inhibitory conductances are held per postsynaptic cell, not per synapse,
    # so that network size does not silently change how hard the competition
    # is fought.  See params.CA3Params.normalize_inhibition.
    if p.normalize_inhibition:
        n_pre_ie = p.n_inh * (p.c_ie / p.n_exc)      # interneurons onto one exc cell
        n_pre_ii = p.n_inh * (p.c_ii / p.n_inh)      # interneurons onto one inh cell
        q_ie = p.g_ie_total / max(1e-9, n_pre_ie * p.w_ie)
        q_ii = p.g_ii_total / max(1e-9, n_pre_ii * p.w_ii)
    else:
        q_ie = q_ii = p.q_static

    return Connectivity(
        w_rc=w_rc, w_ei=w_ei, w_ie=w_ie, w_ii=w_ii, w_ec=w_ec,
        # plastic connections start silent (KK-CODE Synapse.q_w = 0)
        q_rc=np.zeros_like(w_rc),
        # except E->I, which starts at a non-zero baseline so that ordinary
        # global inhibition exists before any learning (KK-CODE Synapse.q_EI)
        q_ei=np.full_like(w_ei, p.q_ei_baseline),
        # inhibitory connections are not plastic in KK-T2
        q_ie=np.full_like(w_ie, q_ie),
        q_ii=np.full_like(w_ii, q_ii),
        q_ec=np.zeros_like(w_ec),
    )


def build_engrams(
    p: CA3Params,
    conn: Connectivity,
    rng: np.random.Generator,
    n_engrams: int = 2,
    overlap: float = 0.0,
    selective: bool = True,
    ec_overlap: float = 0.0,
) -> list[Engram]:
    """Construct `n_engrams` engrams with a prescribed pairwise overlap.

    `overlap` is the fraction of each engram's cells shared with engram 0,
    i.e. shared_cells / engram_size.  (Kim & Kim print the overlap metric as
    O = n_ij/(n_i+n_j), which maxes out at 0.5 for identical sets even though
    they describe 1.0 as identical; we therefore do not reuse their number
    directly.  See readout.overlap_dice.)
    """
    engrams: list[Engram] = []
    taken_inh: list[np.ndarray] = []
    ec_patterns = _make_ec_patterns(p, rng, n_engrams, ec_overlap)

    for k in range(n_engrams):
        inh_set = rng.choice(p.n_inh, size=p.n_inh_per_engram, replace=False)
        taken_inh.append(inh_set)

        if selective:
            # inhibitory drive each excitatory cell would receive from I_k
            drive = (conn.w_ie[inh_set, :] * conn.q_ie[inh_set, :]).sum(axis=0)
            # cells least inhibited by I_k are the ones that survive encoding
            order = np.argsort(drive, kind="stable")
        else:
            order = rng.permutation(p.n_exc)

        if k == 0:
            exc_set = order[: p.engram_size]
        else:
            # The exclusive part must avoid *all* of engram 0, not just the
            # cells deliberately shared with it.  Excluding only the shared
            # cells lets the ranking pull in further engram-0 members by
            # accident, so the realised overlap exceeds the requested one --
            # and by a different amount at every network size, which is what
            # broke the first two scale checks.
            n_shared = int(round(overlap * p.engram_size))
            taken = set(engrams[0].exc.tolist())
            shared = engrams[0].exc[:n_shared]
            pool = np.array([i for i in order if i not in taken], dtype=int)
            need = p.engram_size - n_shared
            if pool.size < need:
                raise ValueError("not enough non-overlapping cells for engram %d" % k)
            exc_set = np.concatenate([shared, pool[:need]])

        engrams.append(Engram(exc=np.sort(exc_set), inh=np.sort(inh_set),
                              ec_pattern=ec_patterns[k]))

    return engrams


def _make_ec_patterns(p: CA3Params, rng: np.random.Generator,
                      n_engrams: int, ec_overlap: float) -> list[np.ndarray]:
    """Input patterns with a controlled number of shared EC units.

    Drawing each pattern independently at random lets two memories share most
    of their input by chance, which confounds input similarity with the CA3
    competition we are trying to isolate.  Here the sharing is a parameter.
    """
    size = int(p.n_ec // 2)
    units = rng.permutation(p.n_ec)
    n_shared = int(round(ec_overlap * size))
    shared, rest = units[:n_shared], units[n_shared:]

    patterns = []
    for k in range(n_engrams):
        lo = k * (size - n_shared)
        exclusive = rest[lo: lo + (size - n_shared)]
        pat = np.zeros(p.n_ec, dtype=np.float32)
        pat[np.concatenate([shared, exclusive]).astype(int)] = 1.0
        patterns.append(pat)
    return patterns


def potentiate(p: CA3Params, conn: Connectivity, engrams: list[Engram]) -> None:
    """Apply the end state of encoding to the plastic peak conductances.

    v0.1 sets the learned values directly instead of running STDP.  What STDP
    would produce, per Kim & Kim's Fig. 5A, is: recurrent excitation clustered
    within each engram, E->I potentiated from an engram onto its own
    interneurons, and the direct EC path potentiated onto the engram's cells.
    Running the actual STDP is deferred; see notes/02.
    """
    if p.normalize_recurrent:
        p_rc = p.c_rc / p.n_exc
        p_ei = p.c_ei / p.n_inh
        q_rc = min(p.q_max, p.g_rc_target / max(1e-9, p_rc * p.engram_size * p.w_rc))
        q_ei = min(p.q_max, p.g_ei_target / max(1e-9, p_ei * p.engram_size * p.w_ei))
    else:
        q_rc = q_ei = p.q_max

    for eg in engrams:
        ex = eg.exc
        conn.q_rc[np.ix_(ex, ex)] = q_rc             # recurrent excitation
        conn.q_ei[np.ix_(ex, eg.inh)] = q_ei         # engram -> its interneurons
        active_ec = np.flatnonzero(eg.ec_pattern)
        conn.q_ec[np.ix_(active_ec, ex)] = p.q_max   # cue path onto the engram
