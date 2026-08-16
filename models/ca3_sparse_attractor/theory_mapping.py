"""Mappings between training statistics, CA3 state, and behavioral readout."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def learned_context_support(
    p_tone_given_a: float,
    p_tone_given_b: float,
    *,
    tone_present: bool,
    prior_a: float = 0.5,
    absence_rule: str = "full_contingency",
) -> dict:
    """Return normalized A/B support implied by learned contingencies."""
    values = (p_tone_given_a, p_tone_given_b, prior_a)
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("probabilities and priors must be in [0, 1]")
    if prior_a in (0.0, 1.0):
        raise ValueError("prior_a must be strictly between 0 and 1")
    if absence_rule not in ("full_contingency", "presence_only"):
        raise ValueError("invalid absence_rule")

    if tone_present:
        likelihood_a = p_tone_given_a
        likelihood_b = p_tone_given_b
        informative = not np.isclose(likelihood_a, likelihood_b)
    elif absence_rule == "full_contingency":
        likelihood_a = 1.0 - p_tone_given_a
        likelihood_b = 1.0 - p_tone_given_b
        informative = not np.isclose(likelihood_a, likelihood_b)
    else:
        likelihood_a = likelihood_b = 1.0
        informative = False

    support_a = prior_a * likelihood_a
    support_b = (1.0 - prior_a) * likelihood_b
    total = support_a + support_b
    if total <= 0.0:
        raise ValueError("the observation is impossible under both contexts")
    lambda_a = support_a / total
    lambda_b = support_b / total
    if support_a > 0.0 and support_b > 0.0:
        log_bayes_factor = math.log(support_a / support_b)
    else:
        log_bayes_factor = math.inf if support_a > support_b else -math.inf
    return {
        "lambda_a": float(lambda_a),
        "lambda_b": float(lambda_b),
        "log_support_ratio_a_vs_b": float(log_bayes_factor),
        "informative": bool(informative),
        "tone_present": bool(tone_present),
        "absence_rule": absence_rule,
        "interpretation": "learned_context_support_not_physical_tone_intensity",
    }


def neural_competition_index(rate_a: float, rate_b: float) -> float:
    """Return a symmetric neural A/B index in [-1, 1]."""
    if rate_a < 0.0 or rate_b < 0.0:
        raise ValueError("rates cannot be negative")
    denominator = rate_a + rate_b
    return 0.0 if denominator == 0.0 else float((rate_a - rate_b) / denominator)


def expected_choice_discrimination(
    neural_index: float,
    inverse_temperature: float,
    *,
    choice_bias: float = 0.0,
) -> float:
    """Map neural evidence to a bounded expected choice discrimination."""
    if not -1.0 <= neural_index <= 1.0:
        raise ValueError("neural_index must be in [-1, 1]")
    if inverse_temperature < 0.0:
        raise ValueError("inverse_temperature cannot be negative")
    return float(math.tanh(0.5 * (inverse_temperature * neural_index + choice_bias)))


def paired_cohens_dz(
    light_on: Iterable[float], light_off: Iterable[float]
) -> float | None:
    """Return paired Cohen's dz, or None when fewer than two pairs exist."""
    on = np.asarray(list(light_on), dtype=float)
    off = np.asarray(list(light_off), dtype=float)
    if on.shape != off.shape:
        raise ValueError("light_on and light_off must contain matched pairs")
    if on.size < 2:
        return None
    differences = on - off
    sd = float(np.std(differences, ddof=1))
    if sd == 0.0:
        return math.inf if float(np.mean(differences)) != 0.0 else 0.0
    return float(np.mean(differences) / sd)
