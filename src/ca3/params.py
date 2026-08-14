"""Parameters for the CA3 engram-competition model.

PROVENANCE RULE (README section 6): every number here carries its source.
Sources used in this file:

  KK-T1 / KK-T2 / KK-T3
      Kim G, Kim P (2025) "Selective inhibition in CA3: a mechanism for stable
      pattern completion through heterosynaptic plasticity."
      PLoS Comput Biol 21(7):e1013267.  Tables 1, 2, 3.
  KK-CODE
      github.com/kgt1220/Hippocampus_SNN, module/Neuron/neuron.py and the
      `config` class in module/Simulation/*.ipynb.  Used where the paper's
      tables are ambiguous or where the code contradicts the paper.
  OURS
      Our own choice, not taken from any source.  Every one of these is a free
      parameter to be swept, never silently fixed.

KNOWN PAPER <-> CODE CONTRADICTIONS (do not resolve these silently):
  * CA3 excitatory current bound: KK-T1 lists "4, 0.75, 20"; KK-CODE sets
    BDe=2, BDp=0.75, BDr=20.  The first element disagrees (4 vs 2).
    We follow KK-CODE and expose it as `bd_exc`.
  * STDP kernel: KK-T3 text describes an exponential kernel with A+-=0.2 nS,
    tau+-=62.5 ms; KK-CODE implements a Gaussian, LTP = gra*exp(-dt^2/(2*grc^2))
    with gra=1, grc=40 ms.  Not used in v0.1 (no STDP yet) but recorded here.
  * The published neuron model uses a term `self.W` (neuron.py:310) that is
    never assigned anywhere in the repository and does not appear in the
    paper's Eq. 1.  We omit it.  See notes/01_referans_kod_durumu.md.
"""

from dataclasses import dataclass, field


@dataclass
class IzhikevichParams:
    """Izhikevich neuron parameters. Source: KK-T3, confirmed in KK-CODE."""

    C: float
    k: float
    v_rest: float
    v_th: float
    v_peak: float
    a: float
    b: float
    c: float
    d: float


# KK-T3 row "Exc"; identical in KK-CODE for types 'CA3'
EXC = IzhikevichParams(C=80, k=3, v_rest=-60, v_th=-50, v_peak=50,
                       a=0.01, b=5, c=-60, d=10)

# KK-T3 row "Inh"; identical in KK-CODE for types 'CA3i'
INH = IzhikevichParams(C=20, k=1, v_rest=-55, v_th=-40, v_peak=25,
                       a=0.15, b=8, c=-55, d=200)


@dataclass
class CA3Params:
    # ---- population sizes -------------------------------------------------
    n_exc: int = 2400          # KK-T1 "CA3 (exc)"; KK-CODE pc[3]
    n_inh: int = 120           # KK-T1 "CA3 (inh)"; KK-CODE pc[4]
    n_ec: int = 16             # KK-T1 "Superficial EC"

    # ---- connectivity: number of presynaptic partners ---------------------
    # KK-T2 gives pconn; KK-CODE `config` gives the equivalent counts.
    c_rc: int = 600            # exc->exc,  = n_exc//4   (pconn 0.25, KK-T2)
    c_ei: int = 30             # exc->inh,  = n_inh//4   (pconn 0.25, KK-T2)
    c_ie: int = 600            # inh->exc,  KK-CODE pc[2] (pconn 0.25, KK-T2)
    c_ii: int = 20             # inh->inh,  KK-CODE pc[5] (pconn 0.167, KK-T2)
    c_ec: int = 8              # EC->exc per cell, KK-CODE config.c_ppCA3

    # ---- fixed synaptic weights (w in KK-T2) ------------------------------
    w_rc: float = 1.0          # KK-T2 CA3(exc)->CA3(exc)
    w_ei: float = 1.0          # KK-T2 CA3(exc)->CA3(inh)
    w_ie: float = 2.0          # KK-T2 CA3(inh)->CA3(exc)
    w_ii: float = 0.5          # KK-T2 CA3(inh)->CA3(inh)
    w_ec: float = 1.0          # KK-T2 Superficial EC->CA3(exc)
    w_noise: float = 0.5       # KK-T2 Noise->CA3(exc)

    # ---- peak conductances q (nS) -----------------------------------------
    q_max: float = 3.0         # KK-CODE model.py self.q_max; KK-T3 text
    q_static: float = 3.0      # KK-CODE Synapse.q_s, non-plastic connections
    q_ei_baseline: float = 0.5  # KK-CODE Synapse.q_EI; gives global inhibition
    q_noise: float = 3.0       # KK-CODE, noise treated as a 'strong' synapse

    # ---- synaptic time constants (ms) -------------------------------------
    tau_ampa: float = 5.0      # KK-T1 CA3 rows
    tau_nmda: float = 30.0     # KK-T1 CA3 rows
    tau_gaba_a: float = 8.0    # KK-T1 CA3 rows
    tau_gaba_b: float = 30.0   # KK-T1 CA3 rows

    # ---- receptor mixing coefficients -------------------------------------
    # KK-T3 text states NMDA:AMPA = 5:5 and GABA_A:GABA_B = 9:1.
    # KK-CODE implements this as multiplicative factors 0.5 and 0.1.
    nmda_coeff: float = 0.5    # KK-CODE (e.g. neuron.py:257)
    gaba_b_coeff: float = 0.1  # KK-CODE (e.g. neuron.py:246)

    # ---- reversal potentials (mV) -----------------------------------------
    v_exc_rev: float = 0.0     # KK-T3 Eq. 3
    v_gaba_a_rev: float = -70.0  # KK-T3 Eq. 3
    v_gaba_b_rev: float = -90.0  # KK-T3 Eq. 3

    # ---- saturating current bounds ----------------------------------------
    # KK-CODE neuron.py:42-68. See the paper<->code contradiction noted above.
    alpha: float = 1.3         # KK-CODE self.alpha
    bd_exc: float = 2.0        # KK-CODE BDe for 'CA3'  (KK-T1 says 4)
    bd_inh: float = 10.0       # KK-CODE BDi for 'CA3'
    bd_rc: float = 20.0        # KK-CODE BDr
    bd_ec: float = 0.75        # KK-CODE BDp
    bd_exc_i: float = 5.0      # KK-CODE BDe for 'CA3i'
    bd_inh_i: float = 10.0     # KK-CODE BDi for 'CA3i'

    # ---- drive ------------------------------------------------------------
    ec_rate_hz: float = 50.0   # KK methods: sustained 50 Hz EC spike train
    noise_rate_hz: float = 3.5  # KK methods: Poisson noise onto CA3 exc

    # ---- simulation -------------------------------------------------------
    dt: float = 1.0            # ms; KK-CODE Neuron.dt
    retrieval_ms: int = 120    # KK methods: theta half-cycle

    # ---- readout ----------------------------------------------------------
    active_thresh_hz: float = 25.0  # KK methods, "Similarity analysis"

    # ---- OURS: engram construction, all free parameters -------------------
    engram_size: int = 100     # OURS. KK get ~10 cells emergently, which is too
                               # coarse to resolve a critical silenced fraction.
                               # Swept, never fixed. See notes/02.
    n_inh_per_engram: int = 12  # OURS. Size of the interneuron set recruited
                                # with an engram.
    seed: int = 0              # OURS.

    # ---- OURS: recurrent normalisation ------------------------------------
    # Kim & Kim's peak conductances were tuned for the ~10-cell engrams their
    # encoding phase happens to produce.  Holding q at q_max while enlarging
    # the engram multiplies the recurrent drive each cell receives by the same
    # factor, pushes tanh() into saturation, and excitation then overwhelms
    # inhibition: both engrams ignite and the competition never resolves.
    # We therefore hold the *expected total recurrent conductance per cell*
    # fixed instead of holding the per-synapse conductance fixed.
    #   q = g_target / (p_conn * engram_size * w)
    # The defaults reproduce Kim & Kim's own regime at their engram size:
    #   p_conn = c_rc/n_exc = 0.25, size 10, w 1, q_max 3  ->  7.5
    # The same argument applies to inhibition, and missing it is what made the
    # first scale check fail: holding the connection *probability* at 0.25 does
    # not hold the inhibition each cell receives fixed, because doubling the
    # network also doubles the interneuron population.  A cell then draws 60
    # presynaptic interneurons instead of 30 and the competition sharpens for
    # no reason other than network size.  So hold the expected total inhibitory
    # conductance per cell fixed instead.
    #   q_ie = g_ie_total / (n_inh * (c_ie/n_exc) * w_ie)
    # Defaults reproduce the reference values exactly at n_inh = 120:
    #   30 presynaptic interneurons * w_ie 2 * q_static 3 = 180
    #   c_ii 20 * w_ii 0.5 * q_static 3 = 30
    normalize_inhibition: bool = True  # OURS
    g_ie_total: float = 180.0          # OURS, = reference value at n_inh=120
    g_ii_total: float = 30.0           # OURS, = reference value at n_inh=120

    normalize_recurrent: bool = True   # OURS
    # Calibrated in experiments/02 against a number that has nothing to do with
    # our hypothesis: Kim & Kim's report that a cue overlapping two engrams
    # retrieves one of them on ~80% of trials.  We reach 45-55% at the q_max
    # ceiling, so this is the top of the achievable range, not a fitted value.
    # Still a free parameter: sweep it, do not treat it as measured.
    g_rc_target: float = 75.0          # OURS, calibrated, must still be swept
    g_ei_target: float = 7.5           # OURS, free parameter, must be swept


DEFAULT = CA3Params()
