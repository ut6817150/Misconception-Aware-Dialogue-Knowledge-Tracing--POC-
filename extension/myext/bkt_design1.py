"""
myext/bkt_design1.py

Design 1: misconception-augmented BKT with a POOLED misconception emission.

The misconception emission parameters mu0 = P(present | not-mastered) and
mu1 = P(present | mastered) are shared across all families, estimated per KC
from all of that KC's observations regardless of family. This is the simplest
augmentation: one extra pair of parameters per KC on top of the four core BKT
parameters.

Assumes correctness and misconception status are conditionally independent
given mastery, so the joint emission factorises (see bkt_mc_common._emission).

Fit:   fit_design1(train_long, granularity)
Score: bkt_mc_common.evaluate_mc(fitted, test_long)

train_long needs columns: dialogue_idx, turn, correct, kc, misc, family.
(family is ignored by this design but accepted for a common interface.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from . import bkt
from . import bkt_mc_common as mc


def _em_single_kc(sequences: List[dict], n_restarts: int = 4,
                  max_iter: int = 100, tol: float = 1e-4, seed: int = 221) -> dict:
    """EM for one KC: core BKT params plus pooled mu0, mu1."""
    rng = np.random.default_rng(seed)
    best, best_ll = None, -np.inf
    fb_core = {"prior": 0.3, "learns": 0.1, "guesses": 0.2, "slips": 0.1}

    for _ in range(n_restarts):
        prior = rng.uniform(0.05, 0.5); learn = rng.uniform(0.05, 0.4)
        guess = rng.uniform(0.05, 0.4); slip = rng.uniform(0.05, 0.4)
        mu0 = rng.uniform(0.4, 0.8); mu1 = rng.uniform(0.1, 0.4)

        prev_ll = -np.inf
        for _it in range(max_iter):
            acc = {k: 0.0 for k in ("init0", "init1", "tnum", "tden",
                                    "g_corr", "g_tot", "s_corr", "s_tot")}
            m_pres = [0.0, 0.0]; m_totl = [0.0, 0.0]
            total_ll = 0.0
            for seq in sequences:
                gamma, xi, ll = mc.forward_backward_mc(
                    seq, prior, learn, guess, slip, mu0, mu1)
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


@dataclass
class FittedDesign1:
    per_skill: Dict[str, dict]
    fallback: dict
    granularity: str

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
            preds[pos] = mc.predict_seq_mc(
                grp["correct"].to_numpy(dtype=int), grp["misc"].astype(str).to_numpy(),
                self.granularity, pr["prior"], pr["learns"], pr["guesses"],
                pr["slips"], pr["mu0"], pr["mu1"])
        out = df.copy(); out["pred"] = preds
        return out.drop(columns="_turn_num").sort_index()


def fit_design1(train_long: pd.DataFrame, granularity: str,
                n_restarts: int = 4, seed: int = 221,
                verbose: bool = True) -> FittedDesign1:
    """Fit Design 1 (pooled misconception emission). granularity in
    {binary, trinary}."""
    sequences = mc.kc_sequences_mc(train_long, granularity)
    rows = {kc: _em_single_kc(seqs, n_restarts=n_restarts, seed=seed + i)
            for i, (kc, seqs) in enumerate(sequences.items())}

    obs_counts = train_long.groupby("kc").size(); obs_counts.index = obs_counts.index.astype(str)
    core_df = pd.DataFrame({k: {p: v[p] for p in mc.CORE_PARAMS}
                            for k, v in rows.items()}).T
    fallback = bkt.weighted_average_params(core_df, obs_counts)
    fallback["mu0"] = float(np.mean([v["mu0"] for v in rows.values()])) if rows else 0.6
    fallback["mu1"] = float(np.mean([v["mu1"] for v in rows.values()])) if rows else 0.3

    if verbose:
        print(f"[design1] pooled, granularity={granularity}: {len(rows)} KCs fitted")
    return FittedDesign1(per_skill=rows, fallback=fallback, granularity=granularity)
