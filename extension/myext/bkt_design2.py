"""
myext/bkt_design2.py

Design 2a: misconception-augmented BKT with a FAMILY-CONDITIONED misconception
emission.

Only the misconception emission carries the family F: mu0^(f) =
P(present | not-mastered, F=f) and mu1^(f) = P(present | mastered, F=f). The
prior, learn rate, and correctness emission (guess, slip) stay POOLED across
families, estimated from all of a KC's observations.

This rests on the assumption that correctness is conditionally independent of
family given mastery, C _|_ F | K (see report). It is the partial-pooling
middle ground: more expressive than Design 1 on the misconception channel,
without the data-sparsity blow-up of conditioning every parameter on family
(the scrapped Design 2b).

Fit:   fit_design2(train_long, granularity)
Score: bkt_mc_common.evaluate_mc(fitted, test_long)

train_long needs columns: dialogue_idx, turn, correct, kc, misc, family.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from . import bkt
from . import bkt_mc_common as mc


def _em_single_kc(sequences: List[dict], n_restarts: int = 4,
                  max_iter: int = 100, tol: float = 1e-4, seed: int = 221) -> dict:
    """EM for one KC: pooled core params, per-family mu0/mu1 dicts."""
    rng = np.random.default_rng(seed)
    families = sorted({s["family"] for s in sequences})
    best, best_ll = None, -np.inf
    fb_core = {"prior": 0.3, "learns": 0.1, "guesses": 0.2, "slips": 0.1}

    for _ in range(n_restarts):
        prior = rng.uniform(0.05, 0.5); learn = rng.uniform(0.05, 0.4)
        guess = rng.uniform(0.05, 0.4); slip = rng.uniform(0.05, 0.4)
        mu0 = {f: rng.uniform(0.4, 0.8) for f in families}
        mu1 = {f: rng.uniform(0.1, 0.4) for f in families}

        prev_ll = -np.inf
        for _it in range(max_iter):
            acc = {k: 0.0 for k in ("init0", "init1", "tnum", "tden",
                                    "g_corr", "g_tot", "s_corr", "s_tot")}
            m_pres = {f: [0.0, 0.0] for f in families}
            m_totl = {f: [0.0, 0.0] for f in families}
            total_ll = 0.0
            for seq in sequences:
                fam = seq["family"]
                gamma, xi, ll = mc.forward_backward_mc(
                    seq, prior, learn, guess, slip, mu0[fam], mu1[fam])
                total_ll += ll
                cs = mc.core_softcounts(seq, gamma, xi)
                for k in acc:
                    acc[k] += cs[k]
                m = seq["m"]; obs = m != -1; present = m == 1
                for state in (0, 1):
                    m_totl[fam][state] += gamma[obs, state].sum()
                    m_pres[fam][state] += gamma[present & obs, state].sum()

            core = mc.core_mstep(acc, fb_core)
            prior, learn = core["prior"], core["learns"]
            guess, slip = core["guesses"], core["slips"]
            mu0 = {f: mc.safe_mu(m_pres[f][0], m_totl[f][0]) for f in families}
            mu1 = {f: mc.safe_mu(m_pres[f][1], m_totl[f][1]) for f in families}

            if total_ll - prev_ll < tol:
                break
            prev_ll = total_ll

        if total_ll > best_ll:
            best_ll = total_ll
            best = {"prior": prior, "learns": learn, "guesses": guess,
                    "slips": slip, "mu0": mu0, "mu1": mu1, "families": families}
    return best


@dataclass
class FittedDesign2:
    per_skill: Dict[str, dict]
    fallback: dict
    granularity: str

    def _core(self, skill: str) -> dict:
        p = self.per_skill.get(skill, {})
        out = {}
        for name in mc.CORE_PARAMS:
            v = p.get(name)
            if v is None or (isinstance(v, float) and np.isnan(v)):
                v = self.fallback[name]
            out[name] = v
        return out

    def _mu(self, skill: str, family: str) -> Tuple[float, float]:
        p = self.per_skill.get(skill)
        if p is None:
            return self.fallback["mu0"], self.fallback["mu1"]
        mu0, mu1 = p["mu0"], p["mu1"]
        d0, d1 = mu0.get(family), mu1.get(family)
        if d0 is None:  # family unseen for this KC -> average over seen families
            d0 = float(np.mean(list(mu0.values()))) if mu0 else self.fallback["mu0"]
            d1 = float(np.mean(list(mu1.values()))) if mu1 else self.fallback["mu1"]
        return d0, d1

    def predict_long(self, long_df: pd.DataFrame) -> pd.DataFrame:
        df = long_df.copy()
        df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
        df = df.sort_values(["dialogue_idx", "kc", "_turn_num"])
        preds = np.empty(len(df))
        for (_did, skill), grp in df.groupby(["dialogue_idx", "kc"], sort=False):
            pos = df.index.get_indexer(grp.index)
            core = self._core(str(skill))
            fam = str(grp["family"].iloc[0]) if "family" in grp else "ALL"
            mu0, mu1 = self._mu(str(skill), fam)
            preds[pos] = mc.predict_seq_mc(
                grp["correct"].to_numpy(dtype=int), grp["misc"].astype(str).to_numpy(),
                self.granularity, core["prior"], core["learns"], core["guesses"],
                core["slips"], mu0, mu1)
        out = df.copy(); out["pred"] = preds
        return out.drop(columns="_turn_num").sort_index()


def fit_design2(train_long: pd.DataFrame, granularity: str,
                n_restarts: int = 4, seed: int = 221,
                verbose: bool = True) -> FittedDesign2:
    """Fit Design 2a (family-conditioned misconception emission). granularity
    in {binary, trinary}."""
    sequences = mc.kc_sequences_mc(train_long, granularity)
    rows = {kc: _em_single_kc(seqs, n_restarts=n_restarts, seed=seed + i)
            for i, (kc, seqs) in enumerate(sequences.items())}

    obs_counts = train_long.groupby("kc").size(); obs_counts.index = obs_counts.index.astype(str)
    core_df = pd.DataFrame({k: {p: v[p] for p in mc.CORE_PARAMS}
                            for k, v in rows.items()}).T
    fallback = bkt.weighted_average_params(core_df, obs_counts)
    # pooled mu fallback: flatten per-family dicts across KCs
    all_mu0, all_mu1 = [], []
    for v in rows.values():
        all_mu0 += list(v["mu0"].values()); all_mu1 += list(v["mu1"].values())
    fallback["mu0"] = float(np.mean(all_mu0)) if all_mu0 else 0.6
    fallback["mu1"] = float(np.mean(all_mu1)) if all_mu1 else 0.3

    if verbose:
        print(f"[design2a] family-conditioned, granularity={granularity}: "
              f"{len(rows)} KCs fitted")
    return FittedDesign2(per_skill=rows, fallback=fallback, granularity=granularity)
