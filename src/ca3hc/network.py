"""Scaled mouse CA3 network built from the Hippocampome parameters.

Eight neuron types, 51 connection types, Izhikevich neurons, Tsodyks-Markram
synapses -- the structure of Kopsick et al. (2023), reimplemented on CPU with
sparse connectivity so it runs on a workstation instead of a V100 cluster.

Two choices make full scale tractable:

  * Connectivity is stored sparse (CSR).  At p = 0.025 the pyramidal-pyramidal
    matrix is 97.5% zeros, and only the rows of cells that actually spiked are
    touched on any given step.
  * Short-term plasticity state is kept per presynaptic neuron per connection
    type, not per synapse.  Tsodyks-Markram parameters are defined at the level
    of a connection type, so every synapse a neuron makes onto a given target
    type shares one (u, x) pair.  That turns 250 million synaptic state
    variables into about ninety thousand, exactly, with no approximation.

Simplifications, all deliberate and all departures from the reference:

  * One excitatory and one inhibitory conductance per cell, decaying with the
    connection type's tau_d, rather than separate AMPA/NMDA/GABA_A/GABA_B
    channels.  The reference splits them; we do not, yet.
  * Synaptic delay is rounded to whole milliseconds.
  * Hippocampome's `Vmin` is taken to be the Izhikevich reset potential c.
    The table does not label it as such; this is an assumption.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import sparse

from . import hippocampome as hc

E_REV_EXC = 0.0        # mV
E_REV_INH = -70.0      # mV, GABA_A


@dataclass
class Connection:
    pre: str
    post: str
    M: sparse.csr_matrix          # (n_pre, n_post), binary connectivity
    g: float
    tau_d: float
    tau_r: float
    tau_f: float
    U: float
    delay_steps: int
    is_exc: bool
    u: np.ndarray = field(repr=False, default=None)   # (n_pre,)
    x: np.ndarray = field(repr=False, default=None)   # (n_pre,)
    G: np.ndarray = field(repr=False, default=None)   # (n_post,) conductance
    pending: np.ndarray = field(repr=False, default=None)  # ring buffer


@dataclass
class CA3Network:
    scale: int
    sizes: dict
    offset: dict
    n_total: int
    n_pyr: int
    conns: list
    # per-neuron Izhikevich parameters, concatenated in hc.TYPES order
    k: np.ndarray
    a: np.ndarray
    b: np.ndarray
    d: np.ndarray
    C: np.ndarray
    v_rest: np.ndarray
    v_th: np.ndarray
    v_reset: np.ndarray
    v_peak: np.ndarray
    dt: float = 1.0

    def slice_of(self, t: str) -> slice:
        return slice(self.offset[t], self.offset[t] + self.sizes[t])

    def n_synapses(self) -> int:
        return int(sum(c.M.nnz for c in self.conns))


def _random_csr(n_pre: int, n_post: int, p: float, rng) -> sparse.csr_matrix:
    """Bernoulli(p) connectivity, generated without materialising n_pre*n_post."""
    expected = int(round(n_pre * n_post * p))
    if expected <= 0:
        return sparse.csr_matrix((n_pre, n_post), dtype=np.float32)
    # draw with replacement then deduplicate: for p well below 1 the collision
    # rate is small, and the resulting probability is p to within a fraction of
    # a percent, which is finer than the source estimates themselves
    draw = int(expected * 1.02) + 8
    rows = rng.integers(0, n_pre, size=draw, dtype=np.int64)
    cols = rng.integers(0, n_post, size=draw, dtype=np.int64)
    key = rows * n_post + cols
    key = np.unique(key)[:expected]
    rows, cols = np.divmod(key, n_post)
    data = np.ones(rows.size, dtype=np.float32)
    return sparse.csr_matrix((data, (rows, cols)), shape=(n_pre, n_post))


def build(scale: int = 8, seed: int = 0, verbose: bool = True) -> CA3Network:
    """Build the network at 1/`scale` of the biological population sizes.

    Connection probabilities are NOT rescaled -- they are properties of the
    circuit, not of its size.  The consequence is that a scaled-down network
    has proportionally fewer partners per cell, which is the coupling between
    scale and connectivity found in experiments/04.
    """
    rng = np.random.default_rng(seed)

    sizes, offset, cursor = {}, {}, 0
    for t in hc.TYPES:
        n = max(1, int(round(hc.POPULATION[t] / scale)))
        sizes[t] = n
        offset[t] = cursor
        cursor += n
    n_total = cursor

    def per_neuron(attr):
        return np.concatenate([
            np.full(sizes[t], getattr(hc.IZHIKEVICH[t], attr), dtype=np.float64)
            for t in hc.TYPES
        ])

    net = CA3Network(
        scale=scale, sizes=sizes, offset=offset, n_total=n_total,
        n_pyr=sizes["pyramidal"], conns=[],
        k=per_neuron("k"), a=per_neuron("a"), b=per_neuron("b"),
        d=per_neuron("d"), C=per_neuron("C"),
        v_rest=per_neuron("v_rest"), v_th=per_neuron("v_th"),
        v_reset=per_neuron("v_min"), v_peak=per_neuron("v_peak"),
    )

    for pre, targets in hc.P_CONNECT.items():
        for post, p in targets.items():
            stp = hc.STP_PARAMS[(pre, post)]
            M = _random_csr(sizes[pre], sizes[post], p, rng)
            delay = int(round(float(np.mean(stp.delay))))
            net.conns.append(Connection(
                pre=pre, post=post, M=M,
                g=stp.g, tau_d=stp.tau_d, tau_r=stp.tau_r,
                tau_f=stp.tau_f, U=stp.U,
                delay_steps=max(1, delay),
                is_exc=pre in hc.EXCITATORY,
                u=np.full(sizes[pre], stp.U),
                x=np.ones(sizes[pre]),
                G=np.zeros(sizes[post]),
                pending=np.zeros((max(1, delay) + 1, sizes[post])),
            ))

    if verbose:
        print(f"scale 1/{scale}: {n_total:,} neurons "
              f"({sizes['pyramidal']:,} pyramidal), "
              f"{net.n_synapses():,} synapses, "
              f"{len(net.conns)} connection types")
    return net


def simulate(net: CA3Network, duration_ms: int, rng,
             stim_frac: float = 0.01, stim_current: float = 500.0,
             stim_ms: int = 5, record_from: int = 0):
    """Transient stimulation of a random subset of pyramidal cells, then free run.

    Mirrors the reference protocol: each chosen pyramidal cell is driven once at
    the start, and whatever happens afterwards is the network's own doing.

    Returns (total_counts, late_counts) where late_counts only accumulates from
    `record_from` ms onward.  The distinction matters: a network that merely
    echoes the stimulus and one that sustains its own activity look identical
    in a total spike count.
    """
    n = net.n_total
    v = net.v_rest.copy()
    u = np.zeros(n)
    spike_counts = np.zeros(n, dtype=np.int64)
    late_counts = np.zeros(n, dtype=np.int64)

    n_stim = max(1, int(round(stim_frac * net.n_pyr)))
    stim_idx = rng.choice(net.n_pyr, size=n_stim, replace=False)

    decay = {id(c): np.exp(-net.dt / c.tau_d) for c in net.conns}
    rec_r = np.exp(-net.dt / np.array([c.tau_r for c in net.conns]))
    rec_f = np.exp(-net.dt / np.array([c.tau_f for c in net.conns]))

    for step in range(duration_ms):
        # ---- deliver conductances scheduled for this step -----------------
        g_exc = np.zeros(n)
        g_inh = np.zeros(n)
        for c in net.conns:
            slot = step % c.pending.shape[0]
            c.G *= decay[id(c)]
            c.G += c.pending[slot]
            c.pending[slot] = 0.0
            target = slice(net.offset[c.post], net.offset[c.post] + net.sizes[c.post])
            if c.is_exc:
                g_exc[target] += c.G
            else:
                g_inh[target] += c.G

        # ---- membrane update ---------------------------------------------
        I = g_exc * (E_REV_EXC - v) + g_inh * (E_REV_INH - v)
        if step < stim_ms:
            I[stim_idx] += stim_current

        v += net.dt * (net.k * (v - net.v_rest) * (v - net.v_th) - u + I) / net.C
        u += net.dt * net.a * (net.b * (v - net.v_rest) - u)
        np.clip(v, -120.0, net.v_peak, out=v)

        fired = v >= net.v_peak
        v[fired] = net.v_reset[fired]
        u[fired] += net.d[fired]
        spike_counts += fired
        if step >= record_from:
            late_counts += fired

        # ---- propagate ----------------------------------------------------
        for ci, c in enumerate(net.conns):
            lo = net.offset[c.pre]
            pre_fired = np.flatnonzero(fired[lo: lo + net.sizes[c.pre]])
            # short-term plasticity recovers whether or not the cell spiked
            c.x += (1.0 - c.x) * (1.0 - rec_r[ci])
            c.u += (c.U - c.u) * (1.0 - rec_f[ci])
            if pre_fired.size == 0:
                continue
            release = c.u[pre_fired] * c.x[pre_fired]
            c.x[pre_fired] -= release
            c.u[pre_fired] += c.U * (1.0 - c.u[pre_fired])
            inc = release @ c.M[pre_fired]
            slot = (step + c.delay_steps) % c.pending.shape[0]
            c.pending[slot] += c.g * np.asarray(inc).ravel()

    return spike_counts, late_counts
