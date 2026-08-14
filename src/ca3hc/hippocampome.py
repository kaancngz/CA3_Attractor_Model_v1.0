"""Mouse CA3 parameters from Hippocampome.org, as published by Kopsick et al.

Single source for every number in this package:

    Kopsick JD, Tecuatl C, Moradi K, Attili SM, Kashyap HJ, Xing J, Chen K,
    Krichmar JL, Ascoli GA (2023) "Robust Resting-State Dynamics in a
    Large-Scale Spiking Neural Network Model of Area CA3 in the Mouse
    Hippocampus." Cognit Comput 15(4):1190-1210.
    doi:10.1007/s12559-021-09954-2

    Table 1  population sizes          -> POPULATION
    Table 2  Izhikevich parameters     -> IZHIKEVICH
    Table 3  connection probabilities  -> P_CONNECT
    Table 4  short-term plasticity     -> STP
    Table 5  firing rates in vivo      -> validation target

Every value was read off the tables in the PDF, not from an abstract or a
search result.  Hippocampome.org's own counts.php and connprob.php are
password protected, so these tables are our accessible copy of them.

A note on how the ambiguous rows were resolved.  The connection-probability
table has rows with fewer entries than columns, because absent connection
types are simply left blank -- and a blank cell in extracted text carries no
position.  Three rows were affected: basket and basket CCK+ (7 values for 8
columns) and QuadD-LM (4 values for 8).  Table 4 lists every connection type
that exists by name, so it says exactly which targets are missing:

    basket      -> no Ivy target        (7 named targets in Table 4)
    basket CCK+ -> no Ivy target        (7 named targets)
    QuadD-LM    -> only pyramidal, axo-axonic, basket, basket CCK+  (4 named)
    axo-axonic  -> only pyramidal       (1 named)

So the two tables cross-check each other and no cell had to be guessed.
"""

from __future__ import annotations

from dataclasses import dataclass

# Order used consistently for every matrix and vector in this module.
TYPES = [
    "pyramidal",
    "axo_axonic",
    "basket",
    "basket_cck",
    "bistratified",
    "ivy",
    "mfa_orden",
    "quadd_lm",
]

EXCITATORY = {"pyramidal"}
INHIBITORY = set(TYPES) - EXCITATORY

# Interneurons grouped by what part of the pyramidal cell they target. The
# distinction matters for competition: perisomatic-targeting cells contact
# pyramidal cells an order of magnitude more densely than dendritic-targeting
# ones (0.150 vs 0.028), so they dominate the winner-take-all interaction.
PERISOMATIC = {"axo_axonic", "basket", "basket_cck"}
DENDRITIC = {"bistratified", "ivy", "mfa_orden", "quadd_lm"}

# ---------------------------------------------------------------- Table 1

POPULATION = {
    "pyramidal": 74366,
    "axo_axonic": 1909,
    "basket": 515,
    "basket_cck": 665,
    "bistratified": 4631,
    "ivy": 2334,
    "mfa_orden": 1526,
    "quadd_lm": 3280,
}
LOCAL_CIRCUIT_TOTAL = 89226          # paper's stated total; equals sum above
DG_GRANULE_POPULATION = 394502       # external afferent, not modelled here


# ---------------------------------------------------------------- Table 2

@dataclass(frozen=True)
class Izhikevich:
    k: float
    a: float
    b: float
    d: float
    C: float
    v_rest: float
    v_th: float
    v_min: float
    v_peak: float


IZHIKEVICH = {
    "pyramidal":    Izhikevich(0.792, 0.008, -42.552, 588, 366, -63.204, -33.604, -38.868, 35.861),
    "axo_axonic":   Izhikevich(3.961, 0.005,   8.684,  15, 165, -57.100, -51.719, -73.969, 27.799),
    "basket":       Izhikevich(0.995, 0.004,   9.264,  -6,  45, -57.506, -23.379, -47.556, 18.455),
    "basket_cck":   Izhikevich(0.583, 0.006,  -1.245,  54, 135, -58.997, -39.398, -42.771, 18.275),
    "bistratified": Izhikevich(3.935, 0.002,  16.580,  19, 107, -64.673, -58.744, -59.703,  -9.929),
    "ivy":          Izhikevich(1.916, 0.009,   1.908,  45, 364, -70.435, -40.859, -53.400,  -6.920),
    "mfa_orden":    Izhikevich(1.380, 0.008,  12.933,   0, 209, -57.076, -39.102, -40.681, 16.313),
    "quadd_lm":     Izhikevich(1.776, 0.006,  -3.449,  52, 186, -73.482, -54.937, -64.404,  7.066),
}


# ---------------------------------------------------------------- Table 3

# P_CONNECT[pre][post]; a missing key means the connection type does not exist.
P_CONNECT: dict[str, dict[str, float]] = {
    "pyramidal": {
        "pyramidal": 0.025, "axo_axonic": 0.015, "basket": 0.020,
        "basket_cck": 0.017, "bistratified": 0.016, "ivy": 0.025,
        "mfa_orden": 0.021, "quadd_lm": 0.013,
    },
    "axo_axonic": {
        "pyramidal": 0.150,
    },
    "basket": {                       # no Ivy target
        "pyramidal": 0.150, "axo_axonic": 0.025, "basket": 0.005,
        "basket_cck": 0.005, "bistratified": 0.025,
        "mfa_orden": 0.005, "quadd_lm": 0.005,
    },
    "basket_cck": {                   # no Ivy target
        "pyramidal": 0.150, "axo_axonic": 0.025, "basket": 0.005,
        "basket_cck": 0.005, "bistratified": 0.025,
        "mfa_orden": 0.005, "quadd_lm": 0.025,
    },
    "bistratified": {
        "pyramidal": 0.028, "axo_axonic": 0.007, "basket": 0.009,
        "basket_cck": 0.004, "bistratified": 0.033, "ivy": 0.004,
        "mfa_orden": 0.009, "quadd_lm": 0.008,
    },
    "ivy": {
        "pyramidal": 0.072, "axo_axonic": 0.004, "basket": 0.016,
        "basket_cck": 0.011, "bistratified": 0.017, "ivy": 0.004,
        "mfa_orden": 0.017, "quadd_lm": 0.002,
    },
    "mfa_orden": {
        "pyramidal": 0.042, "axo_axonic": 0.004, "basket": 0.007,
        "basket_cck": 0.005, "bistratified": 0.005, "ivy": 0.003,
        "mfa_orden": 0.002, "quadd_lm": 0.004,
    },
    "quadd_lm": {                     # only four targets exist
        "pyramidal": 0.119, "axo_axonic": 0.005, "basket": 0.067,
        "basket_cck": 0.050,
    },
}

# DG granule cells onto CA3, kept for when mossy fibre input is added.
P_CONNECT_DG = {t: (0.002 if t == "pyramidal" else 0.001) for t in TYPES}


# ---------------------------------------------------------------- Table 4

@dataclass(frozen=True)
class STP:
    """Tsodyks-Markram parameters. tau in ms, delay in ms."""

    g: float
    tau_d: float
    tau_r: float
    tau_f: float
    U: float
    delay: tuple[float, float]


_D2 = (1.0, 2.0)
_D1 = (1.0, 1.0)

STP_PARAMS: dict[tuple[str, str], STP] = {
    ("pyramidal", "pyramidal"):      STP(0.30, 10.22, 318.51, 21.45, 0.28, _D2),
    ("pyramidal", "axo_axonic"):     STP(0.65,  4.92, 630.73, 26.26, 0.26, _D2),
    ("pyramidal", "basket"):         STP(1.70,  3.97, 691.42, 21.16, 0.12, _D2),
    ("pyramidal", "basket_cck"):     STP(0.85,  4.29, 530.40, 22.45, 0.20, _D2),
    ("pyramidal", "bistratified"):   STP(0.62,  5.37, 569.15, 23.85, 0.26, _D2),
    ("pyramidal", "ivy"):            STP(1.77,  5.67, 552.27, 26.73, 0.12, _D2),
    ("pyramidal", "mfa_orden"):      STP(1.10,  5.95, 444.99, 29.01, 0.15, _D2),
    ("pyramidal", "quadd_lm"):       STP(1.09,  5.82, 453.29, 27.16, 0.15, _D2),

    ("axo_axonic", "pyramidal"):     STP(2.71,  7.62, 361.03, 12.93, 0.13, _D1),

    ("basket", "pyramidal"):         STP(2.28,  7.64, 384.34, 16.74, 0.13, _D1),
    ("basket", "axo_axonic"):        STP(2.63,  3.80, 725.03, 23.21, 0.19, _D1),
    ("basket", "basket"):            STP(1.80,  3.01, 689.51, 11.19, 0.39, _D1),
    ("basket", "basket_cck"):        STP(1.69,  4.21, 636.76, 16.72, 0.24, _D1),
    ("basket", "bistratified"):      STP(2.30,  4.72, 680.33, 16.72, 0.18, _D1),
    ("basket", "mfa_orden"):         STP(1.36,  5.23, 581.94, 19.60, 0.30, _D1),
    ("basket", "quadd_lm"):          STP(1.31,  5.16, 589.20, 19.31, 0.31, _D1),

    ("basket_cck", "pyramidal"):     STP(1.89,  9.10, 376.87, 13.76, 0.08, _D1),
    ("basket_cck", "axo_axonic"):    STP(1.94,  5.44, 477.43, 18.50, 0.12, _D1),
    ("basket_cck", "basket"):        STP(0.96,  4.69, 505.12, 14.86, 0.28, _D1),
    ("basket_cck", "basket_cck"):    STP(0.97,  4.89, 283.28, 23.38, 0.12, _D1),
    ("basket_cck", "bistratified"):  STP(1.78,  5.97, 478.31, 15.25, 0.13, _D1),
    ("basket_cck", "mfa_orden"):     STP(1.02,  6.54, 421.42, 17.84, 0.21, _D1),
    ("basket_cck", "quadd_lm"):      STP(1.00,  6.48, 398.15, 17.34, 0.22, _D1),

    ("bistratified", "pyramidal"):   STP(2.08,  7.49, 481.85, 16.61, 0.12, _D1),
    ("bistratified", "axo_axonic"):  STP(2.15,  4.57, 686.28, 19.16, 0.17, _D1),
    ("bistratified", "basket"):      STP(1.10,  3.86, 695.21, 14.60, 0.37, _D1),
    ("bistratified", "basket_cck"):  STP(1.44,  4.58, 592.19, 17.69, 0.22, _D1),
    ("bistratified", "bistratified"): STP(2.01, 4.58, 775.04, 13.60, 0.17, _D1),
    ("bistratified", "ivy"):         STP(1.34,  5.33, 649.83, 18.17, 0.30, _D1),
    ("bistratified", "mfa_orden"):   STP(1.57,  5.54, 605.25, 18.30, 0.29, _D1),
    ("bistratified", "quadd_lm"):    STP(1.12,  5.53, 594.33, 17.89, 0.30, _D1),

    ("ivy", "pyramidal"):            STP(2.23,  9.01, 439.50, 23.01, 0.12, _D1),
    ("ivy", "axo_axonic"):           STP(2.29,  5.67, 651.64, 25.51, 0.17, _D1),
    ("ivy", "basket"):               STP(1.16,  4.75, 665.16, 19.12, 0.37, _D1),
    ("ivy", "basket_cck"):           STP(1.54,  5.40, 614.01, 20.98, 0.23, _D1),
    ("ivy", "bistratified"):         STP(2.16,  6.24, 660.48, 22.69, 0.17, _D1),
    ("ivy", "ivy"):                  STP(1.34,  5.51, 675.54, 17.72, 0.31, _D1),
    ("ivy", "mfa_orden"):            STP(1.27,  6.96, 578.90, 28.45, 0.30, _D1),
    ("ivy", "quadd_lm"):             STP(1.18,  6.89, 563.47, 26.15, 0.30, _D1),

    ("mfa_orden", "pyramidal"):      STP(1.97,  7.15, 496.05, 20.62, 0.12, _D1),
    ("mfa_orden", "axo_axonic"):     STP(2.12,  4.55, 762.60, 21.45, 0.16, _D1),
    ("mfa_orden", "basket"):         STP(1.08,  3.90, 759.12, 15.70, 0.36, _D1),
    ("mfa_orden", "basket_cck"):     STP(1.42,  4.32, 693.92, 17.08, 0.22, _D1),
    ("mfa_orden", "bistratified"):   STP(2.00,  4.96, 776.57, 17.27, 0.17, _D1),
    ("mfa_orden", "ivy"):            STP(1.35,  5.39, 712.27, 21.22, 0.30, _D1),
    ("mfa_orden", "mfa_orden"):      STP(1.16,  5.53, 642.10, 22.52, 0.29, _D1),
    ("mfa_orden", "quadd_lm"):       STP(1.10,  5.52, 637.95, 21.01, 0.29, _D1),

    ("quadd_lm", "pyramidal"):       STP(1.72,  9.11, 382.14, 24.79, 0.11, _D1),
    ("quadd_lm", "axo_axonic"):      STP(1.91,  5.17, 635.01, 22.34, 0.15, _D1),
    ("quadd_lm", "basket"):          STP(1.00,  4.29, 663.25, 16.42, 0.34, _D1),
    ("quadd_lm", "basket_cck"):      STP(1.31,  4.83, 596.50, 17.78, 0.21, _D1),
}


# ------------------------------------------------------- validation target

# The paper's headline network observable: a stable grand-average firing rate
# of about 3 Hz after transient stimulation, with low variability. This is a
# biological observable rather than a model output, which makes it a far
# better calibration target than a retrieval-success percentage.
GRAND_AVERAGE_FIRING_HZ = 3.0


def consistency_report() -> list[str]:
    """Cross-checks that must hold if the tables were transcribed correctly."""
    problems = []

    total = sum(POPULATION.values())
    if total != LOCAL_CIRCUIT_TOTAL:
        problems.append(f"population sum {total} != stated total {LOCAL_CIRCUIT_TOTAL}")

    for pre, targets in P_CONNECT.items():
        for post in targets:
            if (pre, post) not in STP_PARAMS:
                problems.append(f"connection {pre}->{post} has a probability but no STP")
    for (pre, post) in STP_PARAMS:
        if post not in P_CONNECT.get(pre, {}):
            problems.append(f"connection {pre}->{post} has STP but no probability")

    for t in TYPES:
        if t not in IZHIKEVICH:
            problems.append(f"no Izhikevich parameters for {t}")
        if t not in POPULATION:
            problems.append(f"no population size for {t}")

    return problems


def ei_ratio() -> float:
    exc = sum(POPULATION[t] for t in EXCITATORY)
    inh = sum(POPULATION[t] for t in INHIBITORY)
    return exc / inh
