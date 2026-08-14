"""Vectorised CA3 spiking network.

Same dynamics as Kim & Kim (2025) -- Izhikevich neurons, conductance-based
AMPA/NMDA/GABA_A/GABA_B synapses, saturating per-pathway currents -- but
evaluated as whole-population array operations instead of a Python loop over
neuron objects.  The reference implementation costs ~0.66 s per 1 ms step at
n_exc=2400; this one runs the same network in milliseconds, which is what makes
a sweep over (silenced fraction x overlap x cue bias) possible at all.

Deviations from the reference implementation, all deliberate:
  * Conductances are accumulated per postsynaptic cell rather than per synapse.
    Decay is linear and uniform, so this is exact -- except that the reference
    skips the decay step for a synapse whose presynaptic cell spiked that step.
    We always decay.
  * `self.W`, an unassigned term in the reference neuron equation and absent
    from the paper's Eq. 1, is omitted.
  * Membrane potential is clipped before spike detection; a 1 ms forward Euler
    step on a quadratic model can otherwise overflow.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .engrams import Connectivity
from .params import EXC, INH, CA3Params


@dataclass
class Manipulation:
    """An optogenetic-style intervention, expressed as a set of cells.

    Deliberately abstract: which cells, and what is done to them.  How many
    cells a real fibre could reach is an experimental question, not a model
    parameter (see notes/02_kendi_modelimiz.md).
    """

    silenced: np.ndarray | None = None   # excitatory indices held at rest
    driven: np.ndarray | None = None     # excitatory indices forced to spike
    drive_hz: float = 20.0               # KK-independent; matches the 20 Hz
                                         # pulse train used experimentally


@dataclass
class Result:
    exc_spike_counts: np.ndarray   # (n_exc,)
    inh_spike_counts: np.ndarray   # (n_inh,)
    duration_ms: int

    @property
    def exc_rates_hz(self) -> np.ndarray:
        return self.exc_spike_counts * 1000.0 / self.duration_ms


def _nmda_gate(v: np.ndarray) -> np.ndarray:
    """Mg2+ block, KK-T3 Eq. 3."""
    t = ((v + 80.0) / 60.0) ** 2
    return t / (1.0 + t)


def _saturate(g: np.ndarray, bound: float, alpha: float) -> np.ndarray:
    """alpha * BD * tanh(g / BD): the reference model's soft current ceiling."""
    return alpha * bound * np.tanh(g / bound)


def simulate_retrieval(
    p: CA3Params,
    conn: Connectivity,
    cue: np.ndarray,
    rng: np.random.Generator,
    manip: Manipulation | None = None,
    duration_ms: int | None = None,
) -> Result:
    """Present `cue` (binary, length n_ec) to the network and let it settle."""
    T = duration_ms if duration_ms is not None else p.retrieval_ms
    manip = manip or Manipulation()

    v_e = np.full(p.n_exc, EXC.v_rest, dtype=np.float64)
    u_e = np.zeros(p.n_exc)
    v_i = np.full(p.n_inh, INH.v_rest, dtype=np.float64)
    u_i = np.zeros(p.n_inh)

    # conductance accumulators, one per (pathway, receptor)
    g_ec_a = np.zeros(p.n_exc); g_ec_n = np.zeros(p.n_exc)
    g_rc_a = np.zeros(p.n_exc); g_rc_n = np.zeros(p.n_exc)
    g_ie_a = np.zeros(p.n_exc); g_ie_b = np.zeros(p.n_exc)
    g_no_a = np.zeros(p.n_exc); g_no_n = np.zeros(p.n_exc)
    g_ei_a = np.zeros(p.n_inh); g_ei_n = np.zeros(p.n_inh)
    g_ii_a = np.zeros(p.n_inh); g_ii_b = np.zeros(p.n_inh)

    # effective per-synapse increments (weight x peak conductance)
    m_ec = conn.w_ec * conn.q_ec
    m_rc = conn.w_rc * conn.q_rc
    m_ie = conn.w_ie * conn.q_ie
    m_ei = conn.w_ei * conn.q_ei
    m_ii = conn.w_ii * conn.q_ii

    silenced = np.zeros(p.n_exc, dtype=bool)
    if manip.silenced is not None and len(manip.silenced):
        silenced[manip.silenced] = True
    drive_period = max(1, int(round(1000.0 / manip.drive_hz / p.dt)))

    d_a = 1.0 - p.dt / p.tau_ampa
    d_n = 1.0 - p.dt / p.tau_nmda
    d_ga = 1.0 - p.dt / p.tau_gaba_a
    d_gb = 1.0 - p.dt / p.tau_gaba_b

    ec_period = max(1, int(round(1000.0 / p.ec_rate_hz / p.dt)))
    p_noise = p.noise_rate_hz * p.dt / 1000.0
    noise_inc = p.w_noise * p.q_noise

    exc_counts = np.zeros(p.n_exc, dtype=np.int32)
    inh_counts = np.zeros(p.n_inh, dtype=np.int32)

    for t in range(T):
        # ---- decay -------------------------------------------------------
        g_ec_a *= d_a; g_ec_n *= d_n
        g_rc_a *= d_a; g_rc_n *= d_n
        g_ie_a *= d_ga; g_ie_b *= d_gb
        g_no_a *= d_a; g_no_n *= d_n
        g_ei_a *= d_a; g_ei_n *= d_n
        g_ii_a *= d_ga; g_ii_b *= d_gb

        # ---- external drive ---------------------------------------------
        if t % ec_period == 0:
            active_ec = np.flatnonzero(cue)
            if active_ec.size:
                inc = m_ec[active_ec].sum(axis=0)
                g_ec_a += inc; g_ec_n += inc

        fired_noise = rng.random(p.n_exc) < p_noise
        g_no_a[fired_noise] += noise_inc
        g_no_n[fired_noise] += noise_inc

        # ---- synaptic currents ------------------------------------------
        b_e = _nmda_gate(v_e)
        drive_e = p.v_exc_rev - v_e
        i_e = (
            (_saturate(g_ec_a, p.bd_ec, p.alpha)
             + _saturate(p.nmda_coeff * g_ec_n, p.bd_ec, p.alpha) * b_e) * drive_e
            + (_saturate(g_rc_a, p.bd_rc, p.alpha)
               + _saturate(p.nmda_coeff * g_rc_n, p.bd_rc, p.alpha) * b_e) * drive_e
            + (g_no_a + p.nmda_coeff * g_no_n * b_e) * drive_e   # noise unbounded
            + _saturate(g_ie_a, p.bd_inh, p.alpha) * (p.v_gaba_a_rev - v_e)
            + _saturate(p.gaba_b_coeff * g_ie_b, p.bd_inh, p.alpha)
            * (p.v_gaba_b_rev - v_e)
        )

        b_i = _nmda_gate(v_i)
        i_i = (
            (_saturate(g_ei_a, p.bd_exc_i, p.alpha)
             + _saturate(p.nmda_coeff * g_ei_n, p.bd_exc_i, p.alpha) * b_i)
            * (p.v_exc_rev - v_i)
            + _saturate(g_ii_a, p.bd_inh_i, p.alpha) * (p.v_gaba_a_rev - v_i)
            + _saturate(p.gaba_b_coeff * g_ii_b, p.bd_inh_i, p.alpha)
            * (p.v_gaba_b_rev - v_i)
        )

        # ---- membrane update --------------------------------------------
        v_e += p.dt * (EXC.k * (v_e - EXC.v_rest) * (v_e - EXC.v_th) - u_e + i_e) / EXC.C
        u_e += p.dt * EXC.a * (EXC.b * (v_e - EXC.v_rest) - u_e)
        v_i += p.dt * (INH.k * (v_i - INH.v_rest) * (v_i - INH.v_th) - u_i + i_i) / INH.C
        u_i += p.dt * INH.a * (INH.b * (v_i - INH.v_rest) - u_i)

        np.clip(v_e, -100.0, EXC.v_peak, out=v_e)
        np.clip(v_i, -100.0, INH.v_peak, out=v_i)

        s_e = v_e >= EXC.v_peak
        s_i = v_i >= INH.v_peak

        # ---- manipulation ------------------------------------------------
        if silenced.any():
            s_e &= ~silenced
            v_e[silenced] = EXC.v_rest
            u_e[silenced] = 0.0
        if manip.driven is not None and len(manip.driven) and t % drive_period == 0:
            s_e[manip.driven] = True

        v_e[s_e] = EXC.c; u_e[s_e] += EXC.d
        v_i[s_i] = INH.c; u_i[s_i] += INH.d
        exc_counts += s_e
        inh_counts += s_i

        # ---- propagate ---------------------------------------------------
        idx_e = np.flatnonzero(s_e)
        if idx_e.size:
            inc_rc = m_rc[idx_e].sum(axis=0)
            g_rc_a += inc_rc; g_rc_n += inc_rc
            inc_ei = m_ei[idx_e].sum(axis=0)
            g_ei_a += inc_ei; g_ei_n += inc_ei
        idx_i = np.flatnonzero(s_i)
        if idx_i.size:
            inc_ie = m_ie[idx_i].sum(axis=0)
            g_ie_a += inc_ie; g_ie_b += inc_ie
            inc_ii = m_ii[idx_i].sum(axis=0)
            g_ii_a += inc_ii; g_ii_b += inc_ii

    return Result(exc_spike_counts=exc_counts, inh_spike_counts=inh_counts,
                  duration_ms=T)
