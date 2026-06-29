"""
myext/bkt_design4.py

Design 4: misconception-augmented BKT where the misconception modulates the
TRANSITION (learning dynamics), not the emission.

Motivation. Designs 1-3 put the misconception in the emission, as an observation
of the current mastery state. The diagnostics show that fails because the
misconception is redundant with correctness: as a state observation it adds
nothing BKT didn't already infer from the correctness sequence, and on the
disagree turns it actively misleads. Design 4 takes the one structural route the
diagnostics leave open: the misconception is not an observation of the current
state at all, but a covariate on whether the student LEARNS between turns. A
present misconception predicts the student is still confused and less likely to
have mastered the skill by the next turn; an absent one predicts the opposite.

Because the misconception enters only the transition, it never appears in the
correctness emission likelihood, so it cannot double-count with the turn's
correctness. It can only help by better predicting the trajectory of mastery,
which is information correctness alone does not directly give.

Parameterisation. Standard correctness emission (guess, slip). Standard prior.
The learn rate is split by the misconception at the SOURCE turn:
  trinary: learn_present, learn_absent, learn_notev (3 rates)
  binary:  learn_present, learn_absent (2 rates; not_evidenced folded to absent)
The transition from turn t to t+1 uses the learn rate keyed by the misconception
code at turn t. This is a time-inhomogeneous HMM (transition varies by step).

Fit:   fit_design4(train_long, granularity)
Score: bkt_mc_common.evaluate_mc(fitted, test_long)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from . import bkt
from . import bkt_mc_common as mc


def _forward_backward_trans(seq, prior, guess, slip, learn_by_code):
    """Forward-backward with a standard correctness emission and a TIME-VARYING
    transition whose learn rate at step t is learn_by_code[m[t]].
    """
    c, m = seq["c"], seq["m"]
    T = len(c)
    pc = np.array([guess, 1.0 - slip])
    b = np.empty((T, 2))
    for t in range(T):
        b[t] = pc if c[t] == 1 else (1.0 - pc)

    pi = np.array([1.0 - prior, prior])

    def A_at(t):
        lr = learn_by_code[m[t]]
        return np.array([[1.0 - lr, lr], [0.0, 1.0]])

    alpha = np.zeros((T, 2)); scale = np.zeros(T)
    alpha[0] = pi * b[0]; scale[0] = max(alpha[0].sum(), 1e-300); alpha[0] /= scale[0]
    for t in range(1, T):
        alpha[t] = (alpha[t - 1] @ A_at(t - 1)) * b[t]   # transition t-1 -> t uses m[t-1]
        scale[t] = max(alpha[t].sum(), 1e-300); alpha[t] /= scale[t]

    beta = np.zeros((T, 2)); beta[T - 1] = 1.0
    for t in range(T - 2, -1, -1):
        beta[t] = (A_at(t) @ (b[t + 1] * beta[t + 1])) / scale[t + 1]

    gamma = alpha * beta
    gs = gamma.sum(axis=1, keepdims=True); gs[gs == 0] = 1e-300; gamma /= gs

    xi = np.zeros((T - 1, 2, 2))
    for t in range(T - 1):
        A = A_at(t)
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
    # which misconception codes actually appear (binary: {0,1}; trinary: {-1,0,1})
    codes = sorted({int(x) for s in sequences for x in s["m"]})
    best, best_ll = None, -np.inf

    for _ in range(n_restarts):
        prior = rng.uniform(0.05, 0.5)
        guess = rng.uniform(0.05, 0.4); slip = rng.uniform(0.05, 0.4)
        learn = {code: rng.uniform(0.05, 0.4) for code in codes}

        prev_ll = -np.inf
        for _it in range(max_iter):
            init0 = init1 = 0.0
            g_corr = g_tot = s_corr = s_tot = 0.0
            tnum = {code: 0.0 for code in codes}   # 0->1 transitions by source-turn code
            tden = {code: 0.0 for code in codes}   # time in state0 by source-turn code
            total_ll = 0.0
            for seq in sequences:
                gamma, xi, ll = _forward_backward_trans(seq, prior, guess, slip, learn)
                total_ll += ll
                c, m = seq["c"], seq["m"]
                init0 += gamma[0, 0]; init1 += gamma[0, 1]
                correct = c == 1
                g_corr += gamma[correct, 0].sum(); g_tot += gamma[:, 0].sum()
                s_corr += gamma[~correct, 1].sum(); s_tot += gamma[:, 1].sum()
                for t in range(len(c) - 1):
                    code = int(m[t])           # transition t->t+1 keyed by m[t]
                    tnum[code] += xi[t, 0, 1]
                    tden[code] += gamma[t, 0]

            prior = float(np.clip(init1 / (init0 + init1) if (init0 + init1) > 0 else prior, 1e-3, 1 - 1e-3))
            guess = float(np.clip(g_corr / g_tot if g_tot > 0 else guess, 1e-3, 0.49))
            slip = float(np.clip(s_corr / s_tot if s_tot > 0 else slip, 1e-3, 0.49))
            for code in codes:
                if tden[code] > 0:
                    learn[code] = float(np.clip(tnum[code] / tden[code], 1e-3, 1 - 1e-3))

            if total_ll - prev_ll < tol:
                break
            prev_ll = total_ll

        if total_ll > best_ll:
            best_ll = total_ll
            best = {"prior": prior, "guesses": guess, "slips": slip,
                    "learn_by_code": dict(learn)}
    return best


@dataclass
class FittedDesign4:
    per_skill: Dict[str, dict]
    fallback: dict
    granularity: str

    def _get(self, skill):
        p = self.per_skill.get(skill)
        if p is None:
            return (self.fallback["prior"], self.fallback["guesses"],
                    self.fallback["slips"], self.fallback["learn_by_code"])
        return p["prior"], p["guesses"], p["slips"], p["learn_by_code"]

    def predict_long(self, long_df: pd.DataFrame) -> pd.DataFrame:
        df = long_df.copy()
        df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
        df = df.sort_values(["dialogue_idx", "kc", "_turn_num"])
        preds = np.empty(len(df))
        gran = self.granularity
        for (_did, skill), grp in df.groupby(["dialogue_idx", "kc"], sort=False):
            pos = df.index.get_indexer(grp.index)
            prior, guess, slip, learn = self._get(str(skill))
            preds[pos] = _predict_seq_trans(
                grp["correct"].to_numpy(dtype=int),
                grp["misc"].astype(str).to_numpy(), gran, prior, guess, slip, learn,
                self.fallback["learn_by_code"])
        out = df.copy(); out["pred"] = preds
        return out.drop(columns="_turn_num").sort_index()


def _predict_seq_trans(c, misc, granularity, prior, guess, slip, learn, learn_fb):
    def m_code(x):
        if x == "present":
            return 1
        if x == "absent":
            return 0
        return -1 if granularity == "trinary" else 0

    def lr(code):
        if code in learn:
            return learn[code]
        # unseen code for this KC -> fallback (or average of this KC's rates)
        if learn:
            return float(np.mean(list(learn.values())))
        return learn_fb.get(code, 0.1)

    p_known = prior
    preds = np.empty(len(c))
    for t in range(len(c)):
        p_correct = p_known * (1 - slip) + (1 - p_known) * guess
        preds[t] = p_correct
        # update belief on correctness (standard emission; misconception NOT here)
        if c[t] == 1:
            num = p_known * (1 - slip); den = p_correct
        else:
            num = p_known * slip; den = 1 - p_correct
        p_post = num / den if den > 0 else p_known
        # transition modulated by THIS turn's misconception
        code = m_code(misc[t])
        p_known = p_post + (1 - p_post) * lr(code)
    return preds


def fit_design4(train_long: pd.DataFrame, granularity: str,
                n_restarts: int = 4, seed: int = 221,
                verbose: bool = True) -> FittedDesign4:
    """Fit Design 4 (misconception as transition modulator). granularity in
    {binary, trinary}."""
    sequences = mc.kc_sequences_mc(train_long, granularity)
    rows = {kc: _em_single_kc(seqs, n_restarts=n_restarts, seed=seed + i)
            for i, (kc, seqs) in enumerate(sequences.items())}

    obs_counts = train_long.groupby("kc").size(); obs_counts.index = obs_counts.index.astype(str)
    core_df = pd.DataFrame({k: {"prior": v["prior"], "guesses": v["guesses"],
                                "slips": v["slips"]} for k, v in rows.items()}).T
    # reuse weighted-average for prior/guess/slip; learns handled separately
    core_df["learns"] = 0.1  # placeholder so weighted_average_params has the column
    fb = bkt.weighted_average_params(core_df, obs_counts)
    # learn-by-code fallback: average each code's rate across KCs that have it
    all_codes = sorted({code for v in rows.values() for code in v["learn_by_code"]})
    lbc = {}
    for code in all_codes:
        vals = [v["learn_by_code"][code] for v in rows.values() if code in v["learn_by_code"]]
        lbc[code] = float(np.mean(vals)) if vals else 0.1
    fb["learn_by_code"] = lbc

    if verbose:
        print(f"[design4] transition-modulated, granularity={granularity}: "
              f"{len(rows)} KCs fitted")
    return FittedDesign4(per_skill=rows, fallback=fb, granularity=granularity)
