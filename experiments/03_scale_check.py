"""Does the answer depend on the ratios, or on the number 2400 itself?

n_exc = 2400 came from Kim & Kim, who hand-tuned it; real dorsal CA3 is far
larger.  If the silencing curve is set by ratios (engram / network, overlap,
inhibition vs recurrence) then that arbitrary number is harmless and the result
transfers.  If the curve moves when the network doubles, the threshold we
measure is an artefact of network size and says nothing about an animal.

Everything that scales with the network is doubled together, so every ratio is
held fixed -- including the connection counts, since 600 partners out of 2400
is a connection probability of 0.25 but 600 out of 4800 is 0.125.

Prediction, written before running (see notes/03):
  * the discrimination-index curves should overlap;
  * P(fail) should DROP in the larger network, because ignition is noise-driven
    and doubling the cells doubles the noise events per unit time.
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ca3 import (CA3Params, Manipulation, build_connectivity, build_engrams,
                 potentiate, readout, simulate_retrieval)

N_TRIALS = 30
F_GRID = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]


def scaled_params(k: int, scale_inh_per_engram: bool = True) -> CA3Params:
    """The base network multiplied by k, with every ratio preserved.

    `scale_inh_per_engram` controls the one quantity that may not want to be a
    ratio.  Selective inhibition works because an engram's cells are the ones
    that escaped its own interneurons, and the chance of escaping m
    interneurons that each contact a quarter of the network is 0.75**m -- a
    function of the absolute count, not of the fraction.  Doubling m from 12 to
    24 takes that from ~3% of cells to ~0.1%, so the engram has to be built
    from cells that did not really escape, and selectivity degrades.
    """
    return CA3Params(
        n_exc=2400 * k,
        n_inh=120 * k,
        c_rc=600 * k,
        c_ei=30 * k,
        c_ie=600 * k,
        c_ii=20 * k,
        engram_size=100 * k,
        n_inh_per_engram=12 * k if scale_inh_per_engram else 12,
        # n_ec / c_ec are the input layer, not part of CA3: left alone so the
        # cue statistics are identical in both networks.
    )


def build(p, overlap):
    rng = np.random.default_rng(p.seed)
    conn = build_connectivity(p, rng)
    engrams = build_engrams(p, conn, rng, n_engrams=2, overlap=overlap,
                            selective=True)
    potentiate(p, conn, engrams)
    return conn, engrams


def condition(p, conn, engrams, bias, f):
    n_sil = int(round(f * len(engrams[0].exc)))
    manip = Manipulation(silenced=engrams[0].exc[:n_sil]) if n_sil else Manipulation()
    wins = np.zeros(3)
    dis = []
    for trial in range(N_TRIALS):
        rng = np.random.default_rng(30_000 + trial)
        cue = readout.make_cue(p, engrams[0], engrams[1], bias, rng)
        res = simulate_retrieval(p, conn, cue, rng, manip=manip)
        w = readout.winner(p, res, engrams)
        wins[w if w is not None else 2] += 1
        dis.append(readout.discrimination_index(res, engrams[0], engrams[1]))
    return wins / N_TRIALS, float(np.mean(dis))


def run_block(title, overlap, note, scale_inh=True):
    print(f"\n=== {title} ===")
    print(note)
    nets = {}
    for k, tag in ((1, "2400"), (2, "4800")):
        p = scaled_params(k, scale_inh)
        conn, engrams = build(p, overlap)
        ov = readout.overlap_dice(engrams[0].exc, engrams[1].exc)
        print(f"  n_exc={p.n_exc:5d} engram={p.engram_size:3d}  "
              f"realised overlap={ov:.3f}  inh/engram={p.n_inh_per_engram}")
        nets[tag] = (p, conn, engrams)

    print("\n        |-------- n_exc = 2400 --------|-------- n_exc = 4800 --------|")
    print("   f    |   DI     P(A)  P(B)  P(fail) |   DI     P(A)  P(B)  P(fail) |")
    print("  " + "-" * 74)

    rows = []
    for f in F_GRID:
        out = []
        for tag in ("2400", "4800"):
            p, conn, engrams = nets[tag]
            w, di = condition(p, conn, engrams, bias=0.5, f=f)
            out.append((di, w))
        (d1, w1), (d2, w2) = out
        rows.append((f, d1, w1, d2, w2))
        print(f"  {f:4.2f}  | {d1:+6.3f}  {w1[0]:4.2f}  {w1[1]:4.2f}   {w1[2]:4.2f}  "
              f"| {d2:+6.3f}  {w2[0]:4.2f}  {w2[1]:4.2f}   {w2[2]:4.2f}  |")

    gap = max(abs(r[1] - r[3]) for r in rows)
    print(f"\n  largest DI difference between the two networks: {gap:.3f}")
    print(f"  mean P(fail)   2400: {np.mean([r[2][2] for r in rows]):.2f}"
          f"    4800: {np.mean([r[4][2] for r in rows]):.2f}")
    return gap


def main():
    t0 = time.time()
    g1 = run_block(
        "A. overlap left to emerge (overlap=0.0 requested)", 0.0,
        "  Engram membership is chosen by the selective-inhibition criterion, so\n"
        "  some sharing happens on its own.  Whether that incidental overlap is\n"
        "  itself scale-invariant is exactly what is in question.")
    g2 = run_block(
        "B. overlap pinned to 0.10 in both networks", 0.10,
        "  Same test with the one ratio that block A failed to hold fixed now\n"
        "  imposed explicitly.")
    g3 = run_block(
        "C. overlap pinned AND interneurons-per-engram held at 12", 0.10,
        "  Selectivity depends on how many interneurons an engram had to escape,\n"
        "  which is an absolute count (0.75**m), not a fraction. So do not scale it.",
        scale_inh=False)
    print(f"\nDI gap   A: {g1:.3f}   B (overlap pinned): {g2:.3f}   "
          f"C (+ inh/engram fixed): {g3:.3f}")
    print(f"total {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
