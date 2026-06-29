"""
myext/bkt_mc_common.py

Shared machinery for the misconception-augmented BKT designs. Both Design 1
(pooled, bkt_design1.py) and Design 2a (family-conditioned, bkt_design2.py)
import from here, so the forward-backward recursion, the joint emission, the
sequence builder, the prediction loop, and the evaluation are defined once.

What is shared:
  - kc_sequences_mc:    build per-KC, per-dialogue sequences carrying
                        correctness, the misconception emission code, and family.
  - _emission:          the joint (correctness, misconception) emission in a
                        mastery state.
  - forward_backward_mc:scaled forward-backward over the joint emission.
  - predict_seq_mc:     forward next-step prediction of P(correct).
  - evaluate_mc:        predict + score (overall and final-turn).

What is design-specific (and therefore NOT here):
  - how the misconception emission mu0/mu1 are parameterised (a scalar for the
    pooled design, a per-family dict for the family design),
  - the EM that estimates them,
  - the fitted-model wrapper that stores and serves them.

Granularity handling (binary vs trinary) is shared and lives in the emission
code via the misconception code m_t:
  trinary: 1=present, 0=absent, -1=not_evidenced (no-update; factor = 1)
  binary:  1=present, 0=absent OR not_evidenced (folded; emits 1 - mu)
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from . import bkt  # metrics


# Core (correctness) parameters plus the misconception emission.
CORE_PARAMS = ("prior", "learns", "guesses", "slips")


# ---------------------------------------------------------------------------
# Sequence building
# ---------------------------------------------------------------------------

def kc_sequences_mc(long_df: pd.DataFrame, granularity: str
                    ) -> Dict[str, List[dict]]:
    """Per-KC list of per-dialogue sequences. Each sequence is a dict with
    'c' (0/1 correctness), 'm' (misconception emission code), and 'family'.

    Misconception code per granularity:
      trinary: 1=present, 0=absent, -1=not_evidenced (no-update)
      binary:  1=present, 0=absent OR not_evidenced (folded into absent)
    """
    assert granularity in ("binary", "trinary")
    df = long_df.copy()
    df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
    df = df.sort_values(["dialogue_idx", "_turn_num"])

    def emit_code(misc: str) -> int:
        if misc == "present":
            return 1
        if misc == "absent":
            return 0
        return -1 if granularity == "trinary" else 0

    sequences: Dict[str, List[dict]] = {}
    for (kc, _did), grp in df.groupby(["kc", "dialogue_idx"], sort=False):
        c = grp["correct"].to_numpy(dtype=int)
        m = np.array([emit_code(x) for x in grp["misc"].astype(str)], dtype=int)
        fam = str(grp["family"].iloc[0]) if "family" in grp else "ALL"
        sequences.setdefault(str(kc), []).append({"c": c, "m": m, "family": fam})
    return sequences


# ---------------------------------------------------------------------------
# Joint emission and forward-backward
# ---------------------------------------------------------------------------

def _emission(c_t: int, m_t: int, guess: float, slip: float,
              mu0: float, mu1: float) -> np.ndarray:
    """P(obs_t | K=0), P(obs_t | K=1).

    Correctness: P(C=1|K=0)=guess, P(C=1|K=1)=1-slip.
    Misconception m_t: 1 present -> mu_k; 0 absent -> 1-mu_k; -1 no-update -> 1.
    """
    pc = np.array([guess, 1.0 - slip])
    c_factor = pc if c_t == 1 else (1.0 - pc)
    if m_t == -1:
        m_factor = np.array([1.0, 1.0])
    else:
        mu = np.array([mu0, mu1])
        m_factor = mu if m_t == 1 else (1.0 - mu)
    return c_factor * m_factor


def forward_backward_mc(seq: dict, prior, learn, guess, slip, mu0, mu1):
    """Scaled forward-backward over the joint emission. Returns
    (gamma, xi, loglike). mu0/mu1 are the scalars for THIS sequence (the caller
    selects pooled or family-specific values before calling).
    """
    c, m = seq["c"], seq["m"]
    T = len(c)
    b = np.empty((T, 2))
    for t in range(T):
        b[t] = _emission(c[t], m[t], guess, slip, mu0, mu1)

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


# ---------------------------------------------------------------------------
# E-step soft-count accumulation for the CORE parameters (shared)
# ---------------------------------------------------------------------------

def core_softcounts(seq, gamma, xi):
    """Accumulate the correctness-side soft counts from one sequence's
    posteriors. Returns a dict of partial sums the M-step combines. The
    misconception soft counts are design-specific and handled by each design.
    """
    c = seq["c"]
    correct = c == 1
    out = {
        "init0": gamma[0, 0], "init1": gamma[0, 1],
        "tnum": xi[:, 0, 1].sum() if len(c) > 1 else 0.0,
        "tden": gamma[:-1, 0].sum() if len(c) > 1 else 0.0,
        "g_corr": gamma[correct, 0].sum(), "g_tot": gamma[:, 0].sum(),
        "s_corr": gamma[~correct, 1].sum(), "s_tot": gamma[:, 1].sum(),
    }
    return out


def core_mstep(acc, fallback_core):
    """Turn accumulated core soft counts into clipped core parameters."""
    init0, init1 = acc["init0"], acc["init1"]
    prior = init1 / (init0 + init1) if (init0 + init1) > 0 else fallback_core["prior"]
    learn = acc["tnum"] / acc["tden"] if acc["tden"] > 0 else fallback_core["learns"]
    guess = acc["g_corr"] / acc["g_tot"] if acc["g_tot"] > 0 else fallback_core["guesses"]
    slip = acc["s_corr"] / acc["s_tot"] if acc["s_tot"] > 0 else fallback_core["slips"]
    return {
        "prior": float(np.clip(prior, 1e-3, 1 - 1e-3)),
        "learns": float(np.clip(learn, 1e-3, 1 - 1e-3)),
        "guesses": float(np.clip(guess, 1e-3, 0.49)),
        "slips": float(np.clip(slip, 1e-3, 0.49)),
    }


def safe_mu(pres_mass, tot_mass):
    """Misconception emission probability from present-mass over total-mass,
    clipped for stability. Used by both designs."""
    return float(np.clip(pres_mass / tot_mass, 1e-3, 1 - 1e-3)) if tot_mass > 0 else 0.5


# ---------------------------------------------------------------------------
# Prediction (shared); caller supplies mu0/mu1 per (KC, family)
# ---------------------------------------------------------------------------

def predict_seq_mc(c, misc, granularity, prior, learn, guess, slip, mu0, mu1):
    """Forward next-step prediction of P(correct) per turn, updating the belief
    on the joint (correctness, misconception) emission. Prediction at t uses
    information before the response at t.
    """
    def m_code(x):
        if x == "present":
            return 1
        if x == "absent":
            return 0
        return -1 if granularity == "trinary" else 0

    p_known = prior
    preds = np.empty(len(c))
    for t in range(len(c)):
        p_correct = p_known * (1 - slip) + (1 - p_known) * guess
        preds[t] = p_correct
        if c[t] == 1:
            num = p_known * (1 - slip); den = p_correct
        else:
            num = p_known * slip; den = 1 - p_correct
        p_post = num / den if den > 0 else p_known
        mc = m_code(misc[t])
        if mc != -1:
            mpres = np.array([mu0, mu1])
            mfac = mpres if mc == 1 else (1 - mpres)
            j0 = (1 - p_post) * mfac[0]; j1 = p_post * mfac[1]
            p_post = j1 / (j0 + j1) if (j0 + j1) > 0 else p_post
        p_known = p_post + (1 - p_post) * learn
    return preds


# ---------------------------------------------------------------------------
# Shared evaluation
# ---------------------------------------------------------------------------

def evaluate_mc(fitted, test_long: pd.DataFrame):
    """Predict and score, overall and final-turn. Works with any fitted model
    exposing predict_long (both designs do)."""
    pred_df = fitted.predict_long(test_long)
    overall = bkt.compute_metrics(pred_df["correct"].to_numpy(),
                                  pred_df["pred"].to_numpy())
    pred_df = pred_df.copy()
    pred_df["_tn"] = pred_df["turn"].astype(str).str.extract(r"(\d+)").astype(int)
    final_idx = pred_df.groupby("dialogue_idx")["_tn"].idxmax()
    final = pred_df.loc[final_idx]
    final_m = bkt.compute_metrics(final["correct"].to_numpy(), final["pred"].to_numpy())
    return overall, final_m, pred_df.drop(columns="_tn")
