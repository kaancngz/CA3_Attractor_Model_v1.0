"""What happens when the connectivity ratios are replaced by measured ones?

Three of our structural parameters turned out to be wrong by large factors
(notes/04): the excitatory/inhibitory ratio (20:1 vs a measured 5:1), the
recurrent connection probability (0.25 vs a measured 0.025), and the network
size.  This runs the model across that grid.

The quantity that ties connection probability to network size is the number of
recurrent partners a cell has *inside its own engram*:

    partners = p_recurrent * engram_size

Kim & Kim get 0.25 * 100 = 25.  At the measured 0.025 the same 25 partners
require a 1000-cell engram, which in turn needs a network large enough to hold
two of them sparsely.  So the two parameters cannot be varied independently,
and a small network with measured connectivity has engrams that are barely
connected to themselves.

Interneurons recruited per engram is held at the count that keeps the escape
probability -- the chance a pyramidal cell receives nothing from that
interneuron set, which is what makes inhibition selective at all -- near the
value it has in the Kim & Kim configuration (0.75**12 = 0.032).  Scaling that
count with the population instead was one of the errors found in notes/03.

Population-weighted connection probabilities, from Kopsick et al. 2023 Table 3
weighted by the Table 1 population of each interneuron type:
    interneuron -> pyramidal : 0.082
    pyramidal -> interneuron : 0.017
(The single lumped interneuron pool is itself an approximation: the seven real
types range from 0.028 to 0.150 onto pyramidal cells.)
"""

import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ca3 import (CA3Params, Manipulation, build_connectivity, build_engrams,
                 potentiate, readout, simulate_retrieval)

N_TRIALS = 20
ESCAPE_TARGET = 0.032          # 0.75**12, the Kim & Kim configuration
P_IE_BIO = 0.082               # weighted mean, interneuron -> pyramidal
P_EI_BIO = 0.017               # weighted mean, pyramidal -> interneuron
P_II_BIO = 0.010               # approximate; the table is sparse for I->I


def make(n_exc, p_rc, ei_ratio, engram_frac, p_ie, p_ei, p_ii):
    n_inh = max(2, int(round(n_exc / ei_ratio)))
    engram = max(4, int(round(engram_frac * n_exc)))
    # keep the chance of escaping the engram's own interneurons constant
    m = max(1, int(round(math.log(ESCAPE_TARGET) / math.log(1.0 - p_ie))))
    m = min(m, n_inh)
    return CA3Params(
        n_exc=n_exc,
        n_inh=n_inh,
        c_rc=max(1, int(round(p_rc * n_exc))),
        c_ei=max(1, int(round(p_ei * n_inh))),
        c_ie=max(1, int(round(p_ie * n_exc))),
        c_ii=max(1, int(round(p_ii * n_inh))),
        engram_size=engram,
        n_inh_per_engram=m,
    )


def sweep(p, conn, engrams, f_values=(0.0, 0.2, 0.5)):
    out = {}
    for f in f_values:
        n_sil = int(round(f * len(engrams[0].exc)))
        manip = Manipulation(silenced=engrams[0].exc[:n_sil]) if n_sil else Manipulation()
        wins = np.zeros(3)
        dis = []
        for trial in range(N_TRIALS):
            rng = np.random.default_rng(40_000 + trial)
            cue = readout.make_cue(p, engrams[0], engrams[1], 0.5, rng)
            res = simulate_retrieval(p, conn, cue, rng, manip=manip)
            w = readout.winner(p, res, engrams)
            wins[w if w is not None else 2] += 1
            dis.append(readout.discrimination_index(res, engrams[0], engrams[1]))
        out[f] = (float(np.mean(dis)), wins / N_TRIALS)
    return out


def main():
    configs = [
        # label,                     n_exc, p_rc,  E/I, engram frac, p_ie,     p_ei,     p_ii
        ("Kim&Kim 2400",              2400, 0.25,  20.0, 0.0417,     0.25,     0.25,     0.167),
        ("bio ratios, 2400",          2400, 0.025,  5.0, 0.0417,     P_IE_BIO, P_EI_BIO, P_II_BIO),
        ("bio ratios, 9600",          9600, 0.025,  5.0, 0.0417,     P_IE_BIO, P_EI_BIO, P_II_BIO),
        ("bio ratios, 9600, big eng", 9600, 0.025,  5.0, 0.1042,     P_IE_BIO, P_EI_BIO, P_II_BIO),
    ]

    print(f"unbiased cue, {N_TRIALS} trials per point\n")
    print("config                     n_exc n_inh engram  partners  inh/eng | "
          "     f=0.0            f=0.2            f=0.5")
    print("                                                                 | "
          "  DI   P(A) P(fail)   DI   P(A) P(fail)   DI   P(A) P(fail)")
    print("-" * 128)

    for label, n_exc, p_rc, ei, frac, p_ie, p_ei, p_ii in configs:
        p = make(n_exc, p_rc, ei, frac, p_ie, p_ei, p_ii)
        partners = p_rc * p.engram_size          # recurrent partners inside own engram
        t0 = time.time()
        rng = np.random.default_rng(p.seed)
        conn = build_connectivity(p, rng)
        engrams = build_engrams(p, conn, rng, n_engrams=2, overlap=0.10,
                                selective=True)
        potentiate(p, conn, engrams)
        r = sweep(p, conn, engrams)

        cells = "  ".join(
            f"{r[f][0]:+5.2f} {r[f][1][0]:5.2f}  {r[f][1][2]:5.2f}"
            for f in (0.0, 0.2, 0.5))
        print(f"{label:26s} {p.n_exc:5d} {p.n_inh:5d} {p.engram_size:6d} "
              f"{partners:8.1f} {p.n_inh_per_engram:8d} | {cells}"
              f"   [{time.time() - t0:.0f}s]")


if __name__ == "__main__":
    main()
