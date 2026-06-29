"""
myext/bkt_design3.py

Design 3: misconception-augmented BKT with a JOINT (correctness, misconception)
emission, modelling the dependence between the two rather than assuming
conditional independence given mastery.

Motivation. Designs 1 and 2a factor the emission as P(C|K) * P(M|K), assuming
C _|_ M | K. The diagnostics show this assumption is badly violated: the
misconception is nearly a copy of correctness, so the product double-counts the
shared evidence and the belief becomes overconfident, hurting the off-diagonal
(disagree) turns most. Design 3 removes the assumption by modelling the full
joint P(C, M | K) as a single emission, so the present-but-correct and
absent-but-incorrect cells get their own learned probabilities instead of being
forced through a product of marginals.

Parameterisation. Per KC, for each mastery state k in {0,1}, a distribution
theta_k over the four cells (C in {0,1}) x (M in {absent, present}), summing to
1. That is 3 free parameters per state, 6 per KC, replacing the 2 correctness
(guess, slip) + 2 misconception (mu0, mu1) parameters of Design 1.

not_evidenced handling:
  trinary: a not_evidenced turn observes C but not M; its emission is the
    correctness marginal theta_k[c, absent] + theta_k[c, present]. In the
    M-step its soft mass is split across the two M cells in proportion to the
    current theta (proper EM for the latent M).
  binary: not_evidenced folded into absent, so every turn is fully observed.

Prediction marginal: P(C=1 | K=k) = theta_k[1, absent] + theta_k[1, present].

Fit:   fit_design3(train_long, granularity)
Score: bkt_mc_common.evaluate_mc(fitted, test_long)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from . import bkt
from . import bkt_mc_common as mc


# theta indexing: theta[k, c, mi] with k in {0,1}, c in {0,1}, mi: 0=absent,1=present
ABSENT, PRESENT = 0, 1


def _emission_joint(c_t, m_code, theta):
    """P(obs_t | K=0), P(obs_t | K=1) under the joint emission.

    m_code: 1=present, 0=absent, -1=not_evidenced (correctness marginal).
    theta: array [2,2,2] = theta[k,c,mi].
    """
    if m_code == -1:
        # correctness marginal: sum over M
        return np.array([theta[0, c_t, ABSENT] + theta[0, c_t, PRESENT],
                         theta[1, c_t, ABSENT] + theta[1, c_t, PRESENT]])
    mi = PRESENT if m_code == 1 else ABSENT
    return np.array([theta[0, c_t, mi], theta[1, c_t, mi]])


def _forward_backward_joint(seq, prior, learn, theta):
    c, m = seq["c"], seq["m"]
    T = len(c)
    b = np.empty((T, 2))
    for t in range(T):
        b[t] = _emission_joint(c[t], m[t], theta)
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
    return gamma, xi, float(np.sum(np.log(scale)))


def _em_single_kc(sequences: List[dict], n_restarts=4, max_iter=100,
                  tol=1e-4, seed=221) -> dict:
    rng = np.random.default_rng(seed)
    best, best_ll = None, -np.inf
    for _ in range(n_restarts):
        prior = rng.uniform(0.05, 0.5); learn = rng.uniform(0.05, 0.4)
        # init theta: random, normalised per state
        theta = rng.uniform(0.1, 1.0, size=(2, 2, 2))
        theta /= theta.sum(axis=(1, 2), keepdims=True)
        prev_ll = -np.inf
        for _it in range(max_iter):
            init0 = init1 = tnum = tden = 0.0
            cnt = np.zeros((2, 2, 2))   # soft counts theta[k,c,mi]
            total_ll = 0.0
            for seq in sequences:
                gamma, xi, ll = _forward_backward_joint(seq, prior, learn, theta)
                total_ll += ll
                c, m = seq["c"], seq["m"]
                init0 += gamma[0, 0]; init1 += gamma[0, 1]
                if len(c) > 1:
                    tden += gamma[:-1, 0].sum(); tnum += xi[:, 0, 1].sum()
                for t in range(len(c)):
                    ct = c[t]
                    for k in (0, 1):
                        g = gamma[t, k]
                        if m[t] == -1:
                            # split across M in proportion to current theta
                            a = theta[k, ct, ABSENT]; p = theta[k, ct, PRESENT]
                            s = a + p
                            if s > 0:
                                cnt[k, ct, ABSENT] += g * a / s
                                cnt[k, ct, PRESENT] += g * p / s
                            else:
                                cnt[k, ct, ABSENT] += g * 0.5
                                cnt[k, ct, PRESENT] += g * 0.5
                        else:
                            mi = PRESENT if m[t] == 1 else ABSENT
                            cnt[k, ct, mi] += g
            # M-step
            prior = float(np.clip(init1 / (init0 + init1) if (init0 + init1) > 0 else prior, 1e-3, 1 - 1e-3))
            learn = float(np.clip(tnum / tden if tden > 0 else learn, 1e-3, 1 - 1e-3))
            for k in (0, 1):
                s = cnt[k].sum()
                if s > 0:
                    theta[k] = cnt[k] / s
                theta[k] = np.clip(theta[k], 1e-4, None)
                theta[k] /= theta[k].sum()
            if total_ll - prev_ll < tol:
                break
            prev_ll = total_ll
        if total_ll > best_ll:
            best_ll = total_ll
            best = {"prior": prior, "learns": learn, "theta": theta.copy()}
    return best


@dataclass
class FittedDesign3:
    per_skill: Dict[str, dict]
    fallback: dict
    granularity: str

    def _get(self, skill):
        p = self.per_skill.get(skill)
        if p is None or "theta" not in p:
            return self.fallback["prior"], self.fallback["learns"], self.fallback["theta"]
        return p["prior"], p["learns"], p["theta"]

    def predict_long(self, long_df: pd.DataFrame) -> pd.DataFrame:
        df = long_df.copy()
        df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
        df = df.sort_values(["dialogue_idx", "kc", "_turn_num"])
        preds = np.empty(len(df))
        gran = self.granularity
        for (_did, skill), grp in df.groupby(["dialogue_idx", "kc"], sort=False):
            pos = df.index.get_indexer(grp.index)
            prior, learn, theta = self._get(str(skill))
            preds[pos] = _predict_seq_joint(
                grp["correct"].to_numpy(dtype=int),
                grp["misc"].astype(str).to_numpy(), gran, prior, learn, theta)
        out = df.copy(); out["pred"] = preds
        return out.drop(columns="_turn_num").sort_index()


def _predict_seq_joint(c, misc, granularity, prior, learn, theta):
    def m_code(x):
        if x == "present":
            return 1
        if x == "absent":
            return 0
        return -1 if granularity == "trinary" else 0

    def corr_marginal(k):
        # P(C=1 | K=k)
        return theta[k, 1, ABSENT] + theta[k, 1, PRESENT]

    p_known = prior
    preds = np.empty(len(c))
    pc1 = np.array([corr_marginal(0), corr_marginal(1)])
    for t in range(len(c)):
        preds[t] = p_known * pc1[1] + (1 - p_known) * pc1[0]
        # update on the full joint observation (or marginal if not_evidenced)
        em = _emission_joint(c[t], m_code(misc[t]), theta)
        j0 = (1 - p_known) * em[0]; j1 = p_known * em[1]
        p_post = j1 / (j0 + j1) if (j0 + j1) > 0 else p_known
        p_known = p_post + (1 - p_post) * learn
    return preds


def fit_design3(train_long: pd.DataFrame, granularity: str,
                n_restarts: int = 4, seed: int = 221,
                verbose: bool = True) -> FittedDesign3:
    """Fit Design 3 (joint emission). granularity in {binary, trinary}."""
    sequences = mc.kc_sequences_mc(train_long, granularity)
    rows = {kc: _em_single_kc(seqs, n_restarts=n_restarts, seed=seed + i)
            for i, (kc, seqs) in enumerate(sequences.items())}
    # fallback: average theta and core params across KCs, obs-weighted on core
    obs_counts = train_long.groupby("kc").size(); obs_counts.index = obs_counts.index.astype(str)
    thetas = np.array([v["theta"] for v in rows.values()])
    fallback = {
        "prior": float(np.average([v["prior"] for v in rows.values()])) if rows else 0.3,
        "learns": float(np.average([v["learns"] for v in rows.values()])) if rows else 0.1,
        "theta": thetas.mean(axis=0) if len(thetas) else np.full((2, 2, 2), 0.25),
    }
    if verbose:
        print(f"[design3] joint emission, granularity={granularity}: {len(rows)} KCs fitted")
    return FittedDesign3(per_skill=rows, fallback=fallback, granularity=granularity)
