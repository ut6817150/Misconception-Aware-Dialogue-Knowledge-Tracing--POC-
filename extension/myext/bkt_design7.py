"""
myext/bkt_design7.py

Design 7: PARTIAL-POOLING sweep on the misconception emission. Blends the pooled
misconception emission (Design 1) with the family-specific emission (Design 2a)
by a weight lambda, WITHOUT changing the correctness-vs-misconception balance.

The correctness and misconception channels combine exactly as in ordinary
Design 2a (untempered product, both at full strength). The only thing lambda
controls is how far each family's misconception emission is pulled toward the
pooled value:

    mu_k^{(F)}(lambda) = (1 - lambda) * mu_k^{pooled} + lambda * mu_k^{(F)}

Anchoring:
    lambda = 0  -> every family uses the pooled mu, on Design 2a's shared core
                   == the Design 1 emission on a shared core.
    lambda = 1  -> every family uses its own mu^{(F)} == Design 2a exactly.
    0 < lambda < 1 -> each family's emission shrunk toward the pool.

The core BKT parameters are held FIXED across the sweep (one Design 2a fit), so
lambda changes only the misconception emission and the endpoints are exact. The
pooled mu for each KC is the observation-weighted average of that KC's
family-specific mu, so lambda = 0 genuinely pools the same estimates lambda = 1
keeps separate, rather than being a second independent fit. This deliberately
keeps lambda = 0 from drifting away from the family-specific end through a
core-parameter difference between two EM runs.

This sweep answers a different question from Design 5/6: holding the
misconception channel at full strength, is an INTERMEDIATE amount of
family-specificity better than either the pooled or the fully-split extreme?
An interior peak in lambda would indicate the per-family signal is real but
noisy (the thin (KC, family) cells in Design 2a), and that shrinkage helps.

Implementation note (fixed-blend vs hierarchical). This module uses a
FIXED-BLEND implementation: it fits the pooled mu and the family-specific mu by
EM once each (reusing Design 1 and Design 2a), then forms the convex blend at
prediction time and sweeps lambda. This is simple, interpretable, and cheap (no
refit per lambda). The fully principled alternative is a hierarchical prior on
mu^{(F)} centred on the pooled mu with a strength parameter, letting EM shrink
each family by an amount that depends on its data; that changes the M-step and
is more code. The fixed blend captures the same intuition and is the natural
first experiment. The blend uses each KC's own pooled and family-specific
estimates, so shrinkage is per-KC-per-family.

Fit:   fit_design7(train_long, granularity)            # fits both ends once
Score: fitted.evaluate_sweep(test_long, lambdas=...)   # sweeps lambda
   or: fitted.predict_long(test_long, lam=L)           # single lambda
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from . import bkt
from . import bkt_mc_common as mc
from . import bkt_design1 as d1
from . import bkt_design2 as d2


@dataclass
class FittedDesign7:
    """Holds a single Design 2a fit and blends its family-specific misconception
    emission toward a pooled emission by lambda. Crucially, the CORE BKT
    parameters (prior, learn, guess, slip) are held fixed across the whole sweep
    (taken from the one Design 2a fit), so lambda changes ONLY the misconception
    emission. This makes the endpoints exact and the sweep clean:

        lambda = 0  -> Design 2a's core with the POOLED misconception emission
                       (the Design 1 emission, on shared core).
        lambda = 1  -> Design 2a exactly.

    The pooled mu for each KC is the observation-weighted average of that KC's
    family-specific mu, so lambda = 0 is a genuine pooling of the same estimates
    that lambda = 1 keeps separate, not a different fit. This avoids confounding
    the pooling weight with a core-parameter difference between two separate EM
    runs."""
    fitted_family: "d2.FittedDesign2"
    granularity: str
    pooled_mu: Dict[str, Tuple[float, float]]   # per-KC observation-weighted pooled mu
    fam_counts: Dict[str, Dict[str, int]]       # per-KC per-family obs counts (for reference)

    def _blended_mu(self, skill: str, family: str, lam: float) -> Tuple[float, float]:
        mu0_f, mu1_f = self.fitted_family._mu(str(skill), str(family))
        mu0_p, mu1_p = self.pooled_mu.get(
            str(skill), (self.fitted_family.fallback["mu0"],
                         self.fitted_family.fallback["mu1"]))
        mu0 = (1.0 - lam) * mu0_p + lam * mu0_f
        mu1 = (1.0 - lam) * mu1_p + lam * mu1_f
        return mu0, mu1

    def predict_long(self, long_df: pd.DataFrame, lam: float) -> pd.DataFrame:
        df = long_df.copy()
        df["_turn_num"] = df["turn"].astype(str).str.extract(r"(\d+)").astype(float)
        df = df.sort_values(["dialogue_idx", "kc", "_turn_num"])
        preds = np.empty(len(df))
        for (_did, skill), grp in df.groupby(["dialogue_idx", "kc"], sort=False):
            pos = df.index.get_indexer(grp.index)
            core = self.fitted_family._core(str(skill))   # shared pooled core
            fam = str(grp["family"].iloc[0]) if "family" in grp else "ALL"
            mu0, mu1 = self._blended_mu(str(skill), fam, lam)
            preds[pos] = mc.predict_seq_mc(
                grp["correct"].to_numpy(dtype=int), grp["misc"].astype(str).to_numpy(),
                self.granularity, core["prior"], core["learns"], core["guesses"],
                core["slips"], mu0, mu1)
        out = df.copy(); out["pred"] = preds
        return out.drop(columns="_turn_num").sort_index()

    def evaluate_sweep(self, test_long: pd.DataFrame,
                       lambdas: List[float] = None) -> pd.DataFrame:
        """Return a tidy frame of AUC/Acc/Brier per lambda. Requires sklearn."""
        from sklearn.metrics import roc_auc_score
        lambdas = lambdas if lambdas is not None else DEFAULT_LAMBDAS
        recs = []
        for lam in lambdas:
            pred = self.predict_long(test_long, lam=lam)
            y = pred["correct"].to_numpy(dtype=int)
            p = pred["pred"].to_numpy(dtype=float)
            auc = float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 else float("nan")
            acc = float(((p >= 0.5).astype(int) == y).mean())
            brier = float(np.mean((p - y) ** 2))
            recs.append({"lambda": lam, "AUC": round(auc, 4),
                         "Acc": round(acc, 4), "Brier": round(brier, 4)})
        out = pd.DataFrame(recs)
        base = out[out["lambda"] == 0.0]["AUC"]
        if len(base):
            out["dAUC_vs_pooled"] = (out["AUC"] - base.iloc[0]).round(4)
        return out


def fit_design7(train_long: pd.DataFrame, granularity: str,
                n_restarts: int = 4, seed: int = 221,
                verbose: bool = True) -> FittedDesign7:
    """Fit Design 2a once; derive each KC's pooled mu as the observation-weighted
    average of its family-specific mu. Lambda is swept at prediction time on a
    shared core, so the endpoints are exact (lambda=0 pooled emission, lambda=1
    Design 2a) and only the misconception emission varies."""
    ff = d2.fit_design2(train_long, granularity, n_restarts=n_restarts,
                        seed=seed, verbose=False)

    # per-(KC, family) observation counts, to weight the pooled mu by data mass
    counts = (train_long.groupby(["kc", "family"]).size()
              .rename("n").reset_index())
    fam_counts: Dict[str, Dict[str, int]] = {}
    for _, r in counts.iterrows():
        fam_counts.setdefault(str(r["kc"]), {})[str(r["family"])] = int(r["n"])

    pooled_mu: Dict[str, Tuple[float, float]] = {}
    for kc, p in ff.per_skill.items():
        mu0_d, mu1_d = p["mu0"], p["mu1"]
        w = fam_counts.get(str(kc), {})
        fams = list(mu0_d.keys())
        if not fams:
            continue
        weights = np.array([max(w.get(f, 1), 1) for f in fams], dtype=float)
        weights = weights / weights.sum()
        mu0_p = float(np.sum([weights[i] * mu0_d[f] for i, f in enumerate(fams)]))
        mu1_p = float(np.sum([weights[i] * mu1_d[f] for i, f in enumerate(fams)]))
        pooled_mu[str(kc)] = (mu0_p, mu1_p)

    if verbose:
        print(f"[design7] partial-pooling, granularity={granularity}: "
              f"fitted Design 2a + per-KC pooled mu ({len(ff.per_skill)} KCs); "
              f"core held fixed across lambda")
    return FittedDesign7(fitted_family=ff, granularity=granularity,
                         pooled_mu=pooled_mu, fam_counts=fam_counts)


# default lambda grid: 0 (pooled / D1) .. 1 (family-specific / D2a)
DEFAULT_LAMBDAS: List[float] = [0.0, 0.2, 0.4, 0.5, 0.6, 0.8, 1.0]
