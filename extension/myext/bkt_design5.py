"""
myext/bkt_design5.py

Design 5: TEMPERED-emission BKT. A weighted variant of Design 1 in which the
correctness and misconception emission factors are raised to powers set by a
percentage split (a, b) with a + b = 100.

Mapping from split to exponents (sum-to-2 convention):
    w_c = 2 * a / 100        (correctness exponent)
    w_m = 2 * b / 100        (misconception exponent)

So the emission for mastery state k is

    P(obs | k)  =  [P(C_t | k)]^{w_c}  *  [P(M_t | k)]^{w_m}

Anchoring points:
    (100, 0)  -> (w_c, w_m) = (2, 0): correctness only (misc factor = 1).
                 Recovers the correctness-only baseline.
    ( 50,50)  -> (w_c, w_m) = (1, 1): exactly Design 1 (untempered).
    (  0,100) -> (w_c, w_m) = (0, 2): misconception only.

The weights enter BOTH the EM E-step (the model is trained under the tempered
emission) and the prediction, so this is a genuinely tempered model and not
merely tempered scoring.

Note on the M-step. The core BKT parameters (prior, learn, guess, slip) and the
misconception parameters (mu0, mu1) are still re-estimated by the same soft-count
updates as Design 1; the tempering reweights the responsibilities (gamma, xi)
through the tempered emission, which is the standard way a likelihood-tempered
HMM shifts where evidence comes from. The closed-form M-step is an approximation
under tempering (exact tempered EM would reweight the sufficient statistics by
the exponents too), but it keeps Design 5 directly comparable to Design 1 and is
the conventional choice; this is documented as a modelling decision.

Fit:   fit_design5(train_long, granularity, split=(a, b))
Score: bkt_mc_common.evaluate_mc(fitted, test_long)

train_long needs columns: dialogue_idx, turn, correct, kc, misc, family.
(family is accepted but ignored, matching the Design 1 interface.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from . import bkt
from . import bkt_mc_common as mc


# ---------------------------------------------------------------------------
# Tempered emission and forward-backward
# ---------------------------------------------------------------------------

def split_to_weights(split: Tuple[float, float]) -> Tuple[float, float]:
    """Map a percentage split (a, b) with a + b = 100 to exponents (w_c, w_m)
    under the sum-to-2 convention."""
    a, b = float(split[0]), float(split[1])
    s = a + b
    if s <= 0:
        raise ValueError("split must sum to a positive number")
    # normalise to 100 in case caller passes e.g. (2, 8)
    a, b = 100.0 * a / s, 100.0 * b / s
    return 2.0 * a / 100.0, 2.0 * b / 100.0


def _emission_tempered(c_t: int, m_t: int, guess: float, slip: float,
                       mu0: float, mu1: float, w_c: float, w_m: float) -> np.ndarray:
    """[P(C|K=0)^wc * P(M|K=0)^wm,  P(C|K=1)^wc * P(M|K=1)^wm].

    Same channel definitions as bkt_mc_common._emission, with each factor raised
    to its exponent. A no-update misconception (m_t == -1) contributes a factor
    of 1 regardless of w_m, as in Design 1.
    """
    pc = np.array([guess, 1.0 - slip])
    c_factor = pc if c_t == 1 else (1.0 - pc)
    c_factor = np.power(np.clip(c_factor, 1e-12, 1.0), w_c)

    if m_t == -1:
        m_factor = np.array([1.0, 1.0])
    else:
        mu = np.array([mu0, mu1])
        m_raw = mu if m_t == 1 else (1.0 - mu)
        m_factor = np.power(np.clip(m_raw, 1e-12, 1.0), w_m)

    return c_factor * m_factor


def forward_backward_tempered(seq: dict, prior, learn, guess, slip,
                              mu0, mu1, w_c, w_m):
    """Scaled forward-backward over the tempered joint emission.
    Returns (gamma, xi, loglike). Mirrors bkt_mc_common.forward_backward_mc."""
    c, m = seq["c"], seq["m"]
    T = len(c)
    b = np.empty((T, 2))
    for t in range(T):
        b[t] = _emission_tempered(c[t], m[t], guess, slip, mu0, mu1, w_c, w_m)

    A = np.array([[1.0 - learn, learn], [0.0, 1.0]])
    pi = np.array([1.0 - prior, prior])

    alpha = np.zeros((T, 2)); scale = np.zeros(T)
    alpha[0] = pi * b[0]; scale[0] = max(alpha[0].sum(), 1e-300); alpha[0] /= scale[0]
    for t in range(1, T):
        alpha[t] = (alpha[t - 1] @ A) * b[t]
        scale[t] = max(alpha[t].sum(), 1e-300); alpha[t] /= scale[t]

    beta = np.zeros((T, 2)); beta[T - 1] = 1.0
    for t in range(T - 2, -1, -1):
        beta[t] = (A @ (b[t + 1] * beta[t + 1])) / scale[t + 1]

    gamma = alpha * beta
    gs = gamma.sum(axis=1, keepdims=True); gs[gs == 0] = 1e-300; gamma /= gs

    xi = np.zeros((T - 1, 2, 2))
    for t in range(T - 1):
        for i in range(2):
            for j in range(2):
                xi[t, i, j] = (alpha[t, i] * A[i, j] * b[t + 1, j]
                               * beta[t + 1, j] / scale[t + 1])
        s = xi[t].sum()
        if s > 0:
            xi[t] /= s

    loglike = float(np.sum(np.log(scale)))
    return gamma, xi, loglike


def predict_seq_tempered(c, misc, granularity, prior, learn, guess, slip,
                         mu0, mu1, w_c, w_m):
    """One-step-ahead P(correct) per turn under the tempered emission.

    Mirrors bkt_mc_common.predict_seq_mc: belief is updated using the tempered
    joint emission (correctness + misconception), and each turn's prediction is
    the prior-belief probability of a correct response BEFORE seeing that turn.
    """
    def m_code(x):
        if granularity == "binary":
            return 0 if str(x) in ("absent", "not_evidenced") else 1
        # trinary
        s = str(x)
        if s == "present":
            return 1
        if s == "absent":
            return 0
        return -1  # not_evidenced -> no update

    T = len(c)
    preds = np.empty(T)
    p = prior  # P(mastered) before turn 0
    for t in range(T):
        # predict correctness for this turn from current belief
        preds[t] = p * (1.0 - slip) + (1.0 - p) * guess
        # posterior update on the tempered joint emission for this turn
        m_t = m_code(misc[t])
        em = _emission_tempered(int(c[t]), m_t, guess, slip, mu0, mu1, w_c, w_m)
        num0 = (1.0 - p) * em[0]
        num1 = p * em[1]
        denom = num0 + num1
        p_post = num1 / denom if denom > 0 else p
        # transition
        p = p_post + (1.0 - p_post) * learn
    return preds


# ---------------------------------------------------------------------------
# EM for one KC under tempering
# ---------------------------------------------------------------------------

def _em_single_kc(sequences: List[dict], w_c: float, w_m: float,
                  n_restarts: int = 4, max_iter: int = 100,
                  tol: float = 1e-4, seed: int = 221) -> dict:
    rng = np.random.default_rng(seed)
    best, best_ll = None, -np.inf
    fb_core = {"prior": 0.3, "learns": 0.1, "guesses": 0.2, "slips": 0.1}

    for _ in range(n_restarts):
        prior = rng.uniform(0.05, 0.5); learn = rng.uniform(0.05, 0.4)
        guess = rng.uniform(0.05, 0.4); slip = rng.uniform(0.05, 0.4)
        mu0 = rng.uniform(0.4, 0.8); mu1 = rng.uniform(0.1, 0.4)

        prev_ll = -np.inf
        total_ll = -np.inf
        for _it in range(max_iter):
            acc = {k: 0.0 for k in ("init0", "init1", "tnum", "tden",
                                    "g_corr", "g_tot", "s_corr", "s_tot")}
            m_pres = [0.0, 0.0]; m_totl = [0.0, 0.0]
            total_ll = 0.0
            for seq in sequences:
                gamma, xi, ll = forward_backward_tempered(
                    seq, prior, learn, guess, slip, mu0, mu1, w_c, w_m)
                total_ll += ll
                cs = mc.core_softcounts(seq, gamma, xi)
                for k in acc:
                    acc[k] += cs[k]
                m = seq["m"]; obs = m != -1; present = m == 1
                for state in (0, 1):
                    m_totl[state] += gamma[obs, state].sum()
                    m_pres[state] += gamma[present & obs, state].sum()

            core = mc.core_mstep(acc, fb_core)
            prior, learn = core["prior"], core["learns"]
            guess, slip = core["guesses"], core["slips"]
            # when w_m == 0 the misconception channel is off; keep mu defined but inert
            mu0 = mc.safe_mu(m_pres[0], m_totl[0])
            mu1 = mc.safe_mu(m_pres[1], m_totl[1])

            if total_ll - prev_ll < tol:
                break
            prev_ll = total_ll

        if total_ll > best_ll:
            best_ll = total_ll
            best = {"prior": prior, "learns": learn, "guesses": guess,
                    "slips": slip, "mu0": mu0, "mu1": mu1}
    return best


# ---------------------------------------------------------------------------
# Fitted container and public fit
# ---------------------------------------------------------------------------

@dataclass
class FittedDesign5:
    per_skill: Dict[str, dict]
    fallback: dict
    granularity: str
    w_c: float
    w_m: float
    split: Tuple[float, float]

    def _params(self, skill: str) -> dict:
        p = self.per_skill.get(skill, {})
        out = {}
        for name in ("prior", "learns", "guesses", "slips", "mu0", "mu1"):
            v = p.get(name)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                v = self.fallback[name]
            out[name] = v
        return out

    def predict_long(self, long_df: pd.DataFrame) -> pd.DataFrame:
        df = long_df.copy()
        df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
        df = df.sort_values(["dialogue_idx", "kc", "_turn_num"])
        preds = np.empty(len(df))
        for (_did, skill), grp in df.groupby(["dialogue_idx", "kc"], sort=False):
            pos = df.index.get_indexer(grp.index)
            pr = self._params(str(skill))
            preds[pos] = predict_seq_tempered(
                grp["correct"].to_numpy(dtype=int), grp["misc"].astype(str).to_numpy(),
                self.granularity, pr["prior"], pr["learns"], pr["guesses"],
                pr["slips"], pr["mu0"], pr["mu1"], self.w_c, self.w_m)
        out = df.copy(); out["pred"] = preds
        return out.drop(columns="_turn_num").sort_index()


def fit_design5(train_long: pd.DataFrame, granularity: str,
                split: Tuple[float, float], n_restarts: int = 4,
                seed: int = 221, verbose: bool = True) -> FittedDesign5:
    """Fit Design 5 (tempered emission) at a given percentage split.

    split: (a, b) with a + b = 100, a = correctness weight, b = misconception
    weight. granularity in {binary, trinary}.
    """
    w_c, w_m = split_to_weights(split)
    sequences = mc.kc_sequences_mc(train_long, granularity)
    rows = {kc: _em_single_kc(seqs, w_c, w_m, n_restarts=n_restarts, seed=seed + i)
            for i, (kc, seqs) in enumerate(sequences.items())}

    obs_counts = train_long.groupby("kc").size()
    obs_counts.index = obs_counts.index.astype(str)
    core_df = pd.DataFrame({k: {p: v[p] for p in mc.CORE_PARAMS}
                            for k, v in rows.items()}).T
    fallback = bkt.weighted_average_params(core_df, obs_counts)
    fallback["mu0"] = float(np.mean([v["mu0"] for v in rows.values()])) if rows else 0.6
    fallback["mu1"] = float(np.mean([v["mu1"] for v in rows.values()])) if rows else 0.3

    if verbose:
        print(f"[design5] split={split} -> (w_c={w_c:.2f}, w_m={w_m:.2f}), "
              f"granularity={granularity}: {len(rows)} KCs fitted")
    return FittedDesign5(per_skill=rows, fallback=fallback, granularity=granularity,
                         w_c=w_c, w_m=w_m, split=split)


# Default split grid (correctness, misconception), summing to 100.
DEFAULT_SPLITS: List[Tuple[int, int]] = [
    (100, 0), (80, 20), (60, 40), (50, 50), (40, 60), (20, 80), (0, 100),
]
