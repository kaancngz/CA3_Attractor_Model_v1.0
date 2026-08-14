"""Can the Hippocampome CA3 network sustain its own activity?

The reference network settles into a stable rhythm at a grand-average firing
rate of about 3 Hz after a transient stimulus, and reports that this is robust
"relative to a wide range of transient activation".  The paper does not state
the fraction of pyramidal cells stimulated, so it is scanned here rather than
guessed.

The quantity that decides whether recurrent activity can sustain itself is the
number of recurrent partners a pyramidal cell has, which at a fixed connection
probability is set by the network size:

    partners = 0.025 * n_pyramidal

At 1/16 scale that is 116; at full scale it is 1859.  If self-sustained
activity needs a minimum number of partners, the scan will show the network
waking up as the scale increases -- which would mean the model has a lower
size limit and cannot be shrunk freely.
"""

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ca3hc import build, simulate
from ca3hc import hippocampome as hc

DURATION = 1000          # ms
SETTLE = 500             # ms; rate is measured over the second half only


def main():
    print("grand-average firing rate over the LAST 500 ms, i.e. after the")
    print(f"stimulus is long gone.  Target from the reference: "
          f"{hc.GRAND_AVERAGE_FIRING_HZ} Hz\n")
    print("scale   n_pyr   partners |  stim 1%   stim 5%  stim 20%  stim 50% | build  sim")
    print("-" * 86)

    for scale in (32, 16, 8, 4):
        net = build(scale=scale, seed=0, verbose=False)
        partners = 0.025 * net.n_pyr
        rates, t_sim = [], 0.0
        for frac in (0.01, 0.05, 0.20, 0.50):
            rng = np.random.default_rng(7)
            t0 = time.time()
            _, late = simulate(net, DURATION, rng, stim_frac=frac,
                               record_from=SETTLE)
            t_sim += time.time() - t0
            rates.append(late.sum() / net.n_total / (DURATION - SETTLE) * 1000.0)
        print(f"1/{scale:<4d} {net.n_pyr:7,d} {partners:9.0f} |"
              + "".join(f" {r:8.2f}" for r in rates)
              + f" | {t_sim:5.0f}s")


if __name__ == "__main__":
    main()
