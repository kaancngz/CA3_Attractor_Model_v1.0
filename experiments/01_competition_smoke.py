"""First runnable check: does an unbiased cue produce competition at all?

Three things must be true before anything else in this project is worth doing:
  1. A clean cue for engram A retrieves A and not B.
  2. An unbiased cue (equally similar to both) produces a contest.
  3. Silencing part of A shifts the outcome toward B.

Retrieval in this network is noise-triggered and bistable -- Kim & Kim report
~80% success and treat the rest as retrieval failures -- so every condition is
run over many trials and reported as a probability, never as a single run.
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ca3 import (CA3Params, Manipulation, build_connectivity, build_engrams,
                 potentiate, readout, simulate_retrieval)

N_TRIALS = 30


def condition(p, conn, engrams, bias, silence_frac=0.0, n_trials=N_TRIALS):
    """Run one condition n_trials times; return summary statistics."""
    wins = np.zeros(len(engrams) + 1)     # last slot = retrieval failure
    dis, rates_a, rates_b = [], [], []

    n_sil = int(round(silence_frac * len(engrams[0].exc)))
    manip = Manipulation(silenced=engrams[0].exc[:n_sil]) if n_sil else Manipulation()

    for trial in range(n_trials):
        rng = np.random.default_rng(10_000 + trial)
        cue = readout.make_cue(p, engrams[0], engrams[1], bias, rng)
        res = simulate_retrieval(p, conn, cue, rng, manip=manip)
        w = readout.winner(p, res, engrams)
        wins[w if w is not None else -1] += 1
        dis.append(readout.discrimination_index(res, engrams[0], engrams[1]))
        rates_a.append(readout.engram_rate(res, engrams[0]))
        rates_b.append(readout.engram_rate(res, engrams[1]))

    return {
        "p_A": wins[0] / n_trials,
        "p_B": wins[1] / n_trials,
        "p_fail": wins[-1] / n_trials,
        "DI": float(np.mean(dis)),
        "DI_sd": float(np.std(dis)),
        "rate_A": float(np.mean(rates_a)),
        "rate_B": float(np.mean(rates_b)),
    }


def show(label, s):
    print(f"  {label:>6}  {s['rate_A']:7.1f}  {s['rate_B']:7.1f}   "
          f"{s['DI']:+6.3f}+-{s['DI_sd']:.3f}   "
          f"{s['p_A']:5.2f} {s['p_B']:5.2f} {s['p_fail']:5.2f}")


def main():
    p = CA3Params()
    rng = np.random.default_rng(p.seed)

    conn = build_connectivity(p, rng)
    engrams = build_engrams(p, conn, rng, n_engrams=2, overlap=0.0,
                            selective=True)
    potentiate(p, conn, engrams)
    ov = readout.overlap_dice(engrams[0].exc, engrams[1].exc)
    print(f"n_exc={p.n_exc}  engram_size={p.engram_size}  "
          f"incidental overlap (dice)={ov:.3f}  trials/condition={N_TRIALS}")

    t0 = time.time()
    simulate_retrieval(p, conn, engrams[0].ec_pattern, rng)
    dt = time.time() - t0
    print(f"one {p.retrieval_ms} ms retrieval: {dt * 1000:.0f} ms\n")

    hdr = "          rate_A   rate_B         DI           P(A)  P(B)  P(fail)"

    print("--- 1. clean cues ---")
    print(hdr)
    show("cue=A", condition(p, conn, engrams, bias=1.0))
    show("cue=B", condition(p, conn, engrams, bias=0.0))

    print("\n--- 2. cue bias sweep, no manipulation ---")
    print(hdr)
    for bias in (0.0, 0.25, 0.5, 0.75, 1.0):
        show(f"{bias:.2f}", condition(p, conn, engrams, bias=bias))

    print("\n--- 3. silencing fraction f of A, unbiased cue ---")
    print(hdr)
    for f in (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0):
        show(f"f={f:.2f}", condition(p, conn, engrams, bias=0.5, silence_frac=f))


if __name__ == "__main__":
    main()
