"""Locate the recurrent-drive regime in which retrieval works at all.

Enlarging the engram from Kim & Kim's emergent ~10 cells to a size that can
resolve a silenced fraction changes how much recurrent conductance each cell
receives.  `g_rc_target` (total recurrent conductance per cell from its own
engram) therefore has to be set, and it cannot be read off their paper.

It is calibrated here against a published number that has nothing to do with
our hypothesis: Kim & Kim report that a cue overlapping two engrams retrieves
one of them on about 80% of trials, the rest being retrieval failures.  That
is the target.  Calibrating to their success rate is legitimate; calibrating
to a discrimination shift we expect to see would not be.
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ca3 import (CA3Params, build_connectivity, build_engrams, potentiate,
                 readout, simulate_retrieval)

N_TRIALS = 20
TARGET_SUCCESS = 0.80          # Kim & Kim (2025), Results, retrieval section


def trials(p, conn, engrams, bias, n=N_TRIALS):
    wins = np.zeros(3)
    dis, n_active, pop_rate, eg_rate = [], [], [], []
    for t in range(n):
        rng = np.random.default_rng(20_000 + t)
        cue = readout.make_cue(p, engrams[0], engrams[1], bias, rng)
        res = simulate_retrieval(p, conn, cue, rng)
        w = readout.winner(p, res, engrams)
        wins[w if w is not None else 2] += 1
        dis.append(readout.discrimination_index(res, engrams[0], engrams[1]))
        n_active.append(readout.active_cells(p, res).size)
        pop_rate.append(float(res.exc_rates_hz.mean()))
        eg_rate.append(readout.engram_rate(res, engrams[0]))
    return (wins / n, float(np.mean(dis)), float(np.mean(n_active)),
            float(np.mean(pop_rate)), float(np.mean(eg_rate)))


def main():
    print(f"engram_size=100, sweeping g_rc_target; {N_TRIALS} trials/cell")
    print("target: clean-cue success ~0.80, and the active population should be")
    print("about one engram (100), not two (200) and not the whole network\n")
    print(" g_target   q_rc | clean cue: P(A) P(fail)  rate_A  active  pop | "
          "unbiased: P(A) P(B) P(fail)   DI   active")
    print("-" * 112)

    best = None
    for g in (20.0, 30.0, 40.0, 50.0, 60.0, 75.0, 90.0, 120.0, 200.0):
        p = CA3Params(g_rc_target=g)
        rng = np.random.default_rng(p.seed)
        conn = build_connectivity(p, rng)
        engrams = build_engrams(p, conn, rng, n_engrams=2, overlap=0.0,
                                selective=True)
        potentiate(p, conn, engrams)
        q_rc = min(p.q_max, g / ((p.c_rc / p.n_exc) * p.engram_size * p.w_rc))

        w_clean, di_clean, act_clean, pop_clean, rate_clean = trials(
            p, conn, engrams, bias=1.0)
        w_unb, di_unb, act_unb, pop_unb, _ = trials(p, conn, engrams, bias=0.5)

        print(f"{g:9.1f} {q_rc:6.2f} |           {w_clean[0]:4.2f} "
              f"{w_clean[2]:5.2f} {rate_clean:7.1f} {act_clean:7.0f} "
              f"{pop_clean:5.1f} |"
              f"          {w_unb[0]:4.2f} {w_unb[1]:4.2f} {w_unb[2]:5.2f} "
              f"{di_unb:+5.2f} {act_unb:7.0f}")

        success = w_clean[0]
        one_engram = abs(act_clean - p.engram_size) / p.engram_size
        score = abs(success - TARGET_SUCCESS) + one_engram
        if best is None or score < best[0]:
            best = (score, g, success, act_clean)

    print(f"\nclosest to target: g_rc_target={best[1]:.1f} "
          f"(clean-cue success {best[2]:.2f}, {best[3]:.0f} active cells)")


if __name__ == "__main__":
    main()
