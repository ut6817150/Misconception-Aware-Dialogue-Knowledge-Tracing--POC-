"""Prior-control variants for the retrospective solution-augmented BKT.

This module deliberately sits beside ``bkt.py`` rather than changing the
paper-aligned baseline. It fits the same two-state, no-forgetting BKT model but
allows the initial mastery prior to be:

* constrained by a higher hard floor;
* fixed to a supplied reference prior; or
* shrunk toward a supplied reference prior with Beta pseudo-counts.

The solution remains an ordinary incorrect observation in all three fitted
variants. These controls therefore study parameter stabilization; they do not
change the substantive solution-union assumption made by notebook 04.
"""

from __future__ import annotations

from typing import Dict, List, Mapping

import numpy as np
import pandas as pd

from scripts import bkt


VALID_POLICIES = {"hard_floor", "fixed", "shrinkage"}


def reference_priors(
    skills: List[str],
    per_skill: Mapping[str, Mapping[str, float]],
    fallback: Mapping[str, float],
) -> Dict[str, float]:
    """Return one finite reference prior for every requested KC."""
    default = float(fallback["prior"])
    result = {}
    for skill in skills:
        value = per_skill.get(str(skill), {}).get("prior", default)
        value = float(value)
        result[str(skill)] = value if np.isfinite(value) else default
    return result


def _em_single_kc(
    sequences: List[np.ndarray],
    *,
    policy: str,
    reference_prior: float,
    prior_floor: float,
    shrinkage_strength: float,
    n_restarts: int,
    max_iter: int,
    tol: float,
    seed: int,
) -> Dict[str, float]:
    """Fit one KC under a declared prior-control policy."""
    if policy not in VALID_POLICIES:
        raise ValueError(f"policy must be one of {sorted(VALID_POLICIES)}")
    if not 0 < reference_prior < 1:
        raise ValueError("reference_prior must be strictly between 0 and 1")
    if not 0 < prior_floor < 0.5:
        raise ValueError("prior_floor must be strictly between 0 and 0.5")
    if shrinkage_strength < 0:
        raise ValueError("shrinkage_strength must be non-negative")

    rng = np.random.default_rng(seed)
    best = None
    best_objective = -np.inf

    for _ in range(n_restarts):
        prior = (
            reference_prior
            if policy == "fixed"
            else rng.uniform(max(0.05, prior_floor), 0.5)
        )
        learn = rng.uniform(0.05, 0.4)
        guess = rng.uniform(0.05, 0.4)
        slip = rng.uniform(0.05, 0.4)

        previous_objective = -np.inf
        objective = -np.inf
        for _iteration in range(max_iter):
            init0 = init1 = 0.0
            trans_denom = trans_num = 0.0
            guess_correct = guess_total = 0.0
            slip_incorrect = slip_total = 0.0
            data_log_likelihood = 0.0

            for sequence in sequences:
                gamma, xi, log_likelihood = bkt._forward_backward(
                    sequence, prior, learn, guess, slip
                )
                data_log_likelihood += log_likelihood
                init0 += gamma[0, 0]
                init1 += gamma[0, 1]

                if len(sequence) > 1:
                    trans_denom += gamma[:-1, 0].sum()
                    trans_num += xi[:, 0, 1].sum()

                correct = sequence == 1
                guess_correct += gamma[correct, 0].sum()
                guess_total += gamma[:, 0].sum()
                slip_incorrect += gamma[~correct, 1].sum()
                slip_total += gamma[:, 1].sum()

            empirical_prior = (
                init1 / (init0 + init1)
                if (init0 + init1) > 0
                else prior
            )
            if policy == "fixed":
                new_prior = reference_prior
            elif policy == "shrinkage":
                denominator = init0 + init1 + shrinkage_strength
                new_prior = (
                    init1 + shrinkage_strength * reference_prior
                ) / denominator
            else:
                new_prior = empirical_prior

            new_learn = (
                trans_num / trans_denom if trans_denom > 0 else learn
            )
            new_guess = (
                guess_correct / guess_total if guess_total > 0 else guess
            )
            new_slip = (
                slip_incorrect / slip_total if slip_total > 0 else slip
            )

            new_prior = float(np.clip(new_prior, prior_floor, 1 - 1e-3))
            new_learn = float(np.clip(new_learn, 1e-3, 1 - 1e-3))
            new_guess = float(np.clip(new_guess, 1e-3, 0.49))
            new_slip = float(np.clip(new_slip, 1e-3, 0.49))
            prior, learn, guess, slip = (
                new_prior,
                new_learn,
                new_guess,
                new_slip,
            )

            objective = data_log_likelihood
            if policy == "shrinkage" and shrinkage_strength > 0:
                objective += shrinkage_strength * (
                    reference_prior * np.log(prior)
                    + (1 - reference_prior) * np.log(1 - prior)
                )

            if objective - previous_objective < tol:
                break
            previous_objective = objective

        if objective > best_objective:
            best_objective = objective
            best = {
                "prior": prior,
                "learns": learn,
                "guesses": guess,
                "slips": slip,
            }

    if best is None:
        raise RuntimeError("BKT fit did not produce a parameter vector")
    return best


def fit_bkt_prior_control(
    train_long: pd.DataFrame,
    *,
    policy: str,
    reference_prior_by_skill: Mapping[str, float],
    reference_fallback_prior: float,
    prior_floor: float = 1e-3,
    shrinkage_strength: float = 0.0,
    n_restarts: int = 5,
    max_iter: int = 100,
    tol: float = 1e-4,
    seed: int = 221,
    verbose: bool = True,
) -> bkt.FittedBKT:
    """Fit solution-augmented BKT with an explicit prior-control policy.

    Degenerate KCs keep their reference prior under ``fixed`` and
    ``shrinkage`` while borrowing learning/guess/slip from the weighted
    nondegenerate fallback. Under ``hard_floor`` they receive the complete
    weighted fallback, matching the baseline policy.
    """
    if policy not in VALID_POLICIES:
        raise ValueError(f"policy must be one of {sorted(VALID_POLICIES)}")

    sequences = bkt.kc_sequences(train_long)
    stats = train_long.groupby("kc")["correct"].agg(
        n="count", n_correct="sum"
    )
    stats.index = stats.index.astype(str)
    degenerate_mask = (
        (stats["n_correct"] == 0)
        | (stats["n_correct"] == stats["n"])
    )
    degenerate_kcs = set(stats.index[degenerate_mask])

    rows = {}
    for index, (skill, skill_sequences) in enumerate(sequences.items()):
        if skill in degenerate_kcs:
            continue
        target = float(
            reference_prior_by_skill.get(skill, reference_fallback_prior)
        )
        rows[skill] = _em_single_kc(
            skill_sequences,
            policy=policy,
            reference_prior=target,
            prior_floor=prior_floor,
            shrinkage_strength=shrinkage_strength,
            n_restarts=n_restarts,
            max_iter=max_iter,
            tol=tol,
            seed=seed + index,
        )

    params = pd.DataFrame.from_dict(
        rows, orient="index", columns=list(bkt.PARAM_NAMES)
    )
    nondegenerate_rows = ~train_long["kc"].astype(str).isin(degenerate_kcs)
    observation_counts = (
        train_long[nondegenerate_rows].groupby("kc").size()
    )
    observation_counts.index = observation_counts.index.astype(str)
    fallback = bkt.weighted_average_params(params, observation_counts)

    if policy in {"fixed", "shrinkage"}:
        fallback["prior"] = float(reference_fallback_prior)

    per_skill = {
        skill: row.dropna().to_dict() for skill, row in params.iterrows()
    }
    for skill in degenerate_kcs:
        if policy in {"fixed", "shrinkage"}:
            per_skill[skill] = {
                **fallback,
                "prior": float(
                    reference_prior_by_skill.get(
                        skill, reference_fallback_prior
                    )
                ),
            }
        else:
            per_skill[skill] = dict(fallback)

    if verbose:
        print(
            f"[prior_control] policy={policy}; "
            f"fitted={len(rows)}; degenerate={len(degenerate_kcs)}"
        )
    return bkt.FittedBKT(per_skill=per_skill, fallback=fallback)

