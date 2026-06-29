"""
myext/param_audit.py

Inspect the fitted parameters of the baseline and augmented models, to check
they are sensible and to explain fit-speed differences (fast EM convergence
often means parameters piling at boundaries, i.e. degenerate fits).

Functions:
  core_param_table:   distribution stats of prior/learn/guess/slip across KCs,
                      with boundary-piling flags, for a baseline FittedBKT.
  mc_param_table:     same plus mu0/mu1 (Design 1) or per-family mu (Design 2a).
  joint_param_table:  for Design 3, summarises the joint emission cells and the
                      implied correctness marginal + misconception separation.
  family_mu_report:   for Design 2a, per-family mu spread and observation counts
                      (checks whether family-conditioning actually varies).
  compare_core:       baseline vs augmented core params side by side, to see if
                      the channel shifted guess/slip (a sign of variance being
                      absorbed by the misconception channel).
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def _boundary_flags(df: pd.DataFrame) -> Dict[str, float]:
    """Fraction of KCs piling at parameter boundaries (degeneracy signals)."""
    flags = {}
    if "guesses" in df:
        flags["guess_at_ceiling(>=0.48)"] = float((df["guesses"] >= 0.48).mean())
    if "slips" in df:
        flags["slip_at_ceiling(>=0.48)"] = float((df["slips"] >= 0.48).mean())
    if "learns" in df:
        flags["learn_at_floor(<=0.01)"] = float((df["learns"] <= 0.01).mean())
        flags["learn_at_ceiling(>=0.99)"] = float((df["learns"] >= 0.99).mean())
    if "prior" in df:
        flags["prior_extreme(<=0.01 or >=0.99)"] = float(
            ((df["prior"] <= 0.01) | (df["prior"] >= 0.99)).mean())
    return flags


def core_param_table(fitted) -> pd.DataFrame:
    """prior/learn/guess/slip distribution for a baseline FittedBKT."""
    rows = {k: v for k, v in fitted.per_skill.items()}
    df = pd.DataFrame(rows).T[["prior", "learns", "guesses", "slips"]]
    return df


def mc_param_table(fitted, design: str) -> pd.DataFrame:
    """Core params + misconception emission for Design 1 or 2a.

    For Design 2a (family), mu0/mu1 are per-family dicts; this reports the
    mean across families per KC (use family_mu_report for the per-family view).
    """
    recs = {}
    for kc, p in fitted.per_skill.items():
        rec = {k: p.get(k) for k in ("prior", "learns", "guesses", "slips")}
        mu0, mu1 = p.get("mu0"), p.get("mu1")
        if isinstance(mu0, dict):
            rec["mu0"] = float(np.mean(list(mu0.values()))) if mu0 else np.nan
            rec["mu1"] = float(np.mean(list(mu1.values()))) if mu1 else np.nan
        else:
            rec["mu0"], rec["mu1"] = mu0, mu1
        recs[kc] = rec
    df = pd.DataFrame(recs).T
    df["mu_sep(mu0-mu1)"] = df["mu0"] - df["mu1"]
    return df


def summarise(df: pd.DataFrame, label: str) -> str:
    """Pretty summary: describe() plus boundary flags."""
    lines = [f"=== {label} ({len(df)} KCs) ==="]
    lines.append(df.describe().round(3).to_string())
    flags = _boundary_flags(df)
    if flags:
        lines.append("boundary piling: " + ", ".join(f"{k}={v:.2f}" for k, v in flags.items()))
    if "mu_sep(mu0-mu1)" in df:
        sep = df["mu_sep(mu0-mu1)"]
        lines.append(f"misconception separation mu0-mu1: mean={sep.mean():.3f} "
                     f"median={sep.median():.3f} frac>0.1={float((sep>0.1).mean()):.2f}")
    return "\n".join(lines)


def family_mu_report(fitted) -> pd.DataFrame:
    """For Design 2a: per-family mu0/mu1 averaged across KCs, with how many KCs
    actually observed each family. If mu barely varies across families, the
    family-conditioning is doing little (explains D2a ~ D1)."""
    fam_mu0, fam_mu1, fam_n = {}, {}, {}
    for kc, p in fitted.per_skill.items():
        mu0, mu1 = p.get("mu0"), p.get("mu1")
        if not isinstance(mu0, dict):
            continue
        for f in mu0:
            fam_mu0.setdefault(f, []).append(mu0[f])
            fam_mu1.setdefault(f, []).append(mu1[f])
            fam_n[f] = fam_n.get(f, 0) + 1
    rows = []
    for f in sorted(fam_mu0):
        rows.append({"family": f, "n_kcs": fam_n[f],
                     "mean_mu0": round(np.mean(fam_mu0[f]), 3),
                     "mean_mu1": round(np.mean(fam_mu1[f]), 3),
                     "mean_sep": round(np.mean(fam_mu0[f]) - np.mean(fam_mu1[f]), 3)})
    return pd.DataFrame(rows)


def joint_param_table(fitted) -> pd.DataFrame:
    """For Design 3: per-KC summary of the joint emission. Reports the implied
    correctness marginals and a dependence measure showing how far the joint is
    from the independence factorisation (large => the joint design is capturing
    dependence the product models could not)."""
    ABSENT, PRESENT = 0, 1
    recs = {}
    for kc, p in fitted.per_skill.items():
        th = p.get("theta")
        if th is None:
            continue
        rec = {"prior": p["prior"], "learns": p["learns"]}
        # correctness marginal per state
        rec["P(C=1|K=0)"] = th[0, 1, ABSENT] + th[0, 1, PRESENT]
        rec["P(C=1|K=1)"] = th[1, 1, ABSENT] + th[1, 1, PRESENT]
        # misconception marginal per state
        rec["P(M=pres|K=0)"] = th[0, 0, PRESENT] + th[0, 1, PRESENT]
        rec["P(M=pres|K=1)"] = th[1, 0, PRESENT] + th[1, 1, PRESENT]
        # dependence: how much P(C,M|K) departs from P(C|K)P(M|K), summed
        dep = 0.0
        for k in (0, 1):
            pc = np.array([1 - rec[f"P(C=1|K={k})"], rec[f"P(C=1|K={k})"]])
            pm_pres = th[k, 0, PRESENT] + th[k, 1, PRESENT]
            pm = np.array([1 - pm_pres, pm_pres])
            indep = np.outer(pc, pm)  # [c, mi]
            joint = th[k]
            dep += float(np.abs(joint - indep).sum())
        rec["dependence(|joint-indep|)"] = dep
        recs[kc] = rec
    return pd.DataFrame(recs).T


def compare_core(baseline_fitted, aug_fitted) -> pd.DataFrame:
    """Baseline vs augmented core params (mean across KCs). A shift in guess/
    slip when the channel is added indicates the misconception channel is
    absorbing variance the correctness emission used to explain."""
    def means(f, names):
        rows = {}
        for kc, p in f.per_skill.items():
            for n in names:
                rows.setdefault(n, []).append(p.get(n))
        return {n: float(np.nanmean([x for x in v if x is not None])) for n, v in rows.items()}

    base = means(baseline_fitted, ["prior", "learns", "guesses", "slips"])
    # aug may store theta (design3) instead of guess/slip
    aug_names = ["prior", "learns", "guesses", "slips"]
    if any("theta" in p for p in aug_fitted.per_skill.values()):
        aug = means(aug_fitted, ["prior", "learns"])
    else:
        aug = means(aug_fitted, aug_names)
    rows = []
    for n in ["prior", "learns", "guesses", "slips"]:
        rows.append({"param": n, "baseline": round(base.get(n, np.nan), 3),
                     "augmented": round(aug.get(n, np.nan), 3) if n in aug else "n/a (joint)"})
    return pd.DataFrame(rows)


def transition_rate_report(fitted) -> pd.DataFrame:
    """For Design 4: average learn rate by misconception code across KCs.

    The informative direction is learn_present < learn_absent: a present
    misconception predicts LESS learning to the next turn. If learn_present >=
    learn_absent, the transition channel has not found a useful signal.
    Codes: 1=present, 0=absent, -1=not_evidenced.
    """
    names = {1: "present", 0: "absent", -1: "not_evidenced"}
    buckets = {1: [], 0: [], -1: []}
    for p in fitted.per_skill.values():
        for code, lr in p.get("learn_by_code", {}).items():
            buckets[int(code)].append(lr)
    rows = []
    for code in (1, 0, -1):
        if buckets[code]:
            rows.append({"misc_code": names[code], "n_kcs": len(buckets[code]),
                         "mean_learn": round(float(np.mean(buckets[code])), 3),
                         "median_learn": round(float(np.median(buckets[code])), 3)})
    return pd.DataFrame(rows)