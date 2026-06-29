"""
myext/diagnostics.py

Diagnostics for understanding WHY the misconception channel behaves as it does,
given the finding that the labels are highly informative (large P(correct|misc)
separation) yet adding them to BKT does not improve, and mildly degrades,
prediction.

Two analyses:

  1. overconfidence_report: compares the predicted-probability distribution and
     calibration of a baseline model against an augmented model. The redundancy
     hypothesis predicts the augmented model pushes predictions closer to 0/1
     (more extreme) and is worse calibrated (the double-counting of a
     correctness-redundant channel makes the mastery belief overconfident).

  2. offdiagonal_report: evaluates where the channel could carry information
     correctness does not, namely the turns where the misconception label and
     the correctness label DISAGREE (present-but-correct, absent-but-incorrect).
     If the channel helps anywhere, it should be on these off-diagonal turns;
     reporting AUC/accuracy on the agree vs disagree subsets shows whether the
     channel's value is concentrated there.

Both take prediction dataframes (with a 'pred' column) from bkt.evaluate /
bkt_mc_common.evaluate_mc, aligned on the same rows.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss


def _safe_auc(y, p):
    return roc_auc_score(y, p) if len(np.unique(y)) > 1 else float("nan")


def overconfidence_report(base_pred: pd.DataFrame, aug_pred: pd.DataFrame
                          ) -> Dict[str, float]:
    """Compare confidence and calibration of baseline vs augmented predictions.

    Both frames must have 'pred' and 'correct' over the same rows (same order).
    Returns summary stats; the augmented model being more extreme (higher mean
    |pred-0.5|) and worse calibrated (higher ECE, worse Brier) supports the
    double-counting / overconfidence explanation.
    """
    pb = base_pred["pred"].to_numpy()
    pa = aug_pred["pred"].to_numpy()
    y = base_pred["correct"].to_numpy()

    def extremity(p):
        return float(np.mean(np.abs(p - 0.5)))

    def ece(p, y, bins=10):
        # expected calibration error
        edges = np.linspace(0, 1, bins + 1)
        e = 0.0
        for i in range(bins):
            m = (p >= edges[i]) & (p < edges[i + 1] if i < bins - 1 else p <= edges[i + 1])
            if m.sum() == 0:
                continue
            conf = p[m].mean(); acc = y[m].mean()
            e += (m.sum() / len(p)) * abs(conf - acc)
        return float(e)

    return {
        "base_extremity": extremity(pb),
        "aug_extremity": extremity(pa),
        "base_ece": ece(pb, y),
        "aug_ece": ece(pa, y),
        "base_brier": brier_score_loss(y, np.clip(pb, 1e-6, 1 - 1e-6)),
        "aug_brier": brier_score_loss(y, np.clip(pa, 1e-6, 1 - 1e-6)),
        "frac_aug_more_extreme": float(np.mean(np.abs(pa - 0.5) > np.abs(pb - 0.5))),
    }


def offdiagonal_report(aug_pred: pd.DataFrame, base_pred: pd.DataFrame,
                       test_mc: pd.DataFrame) -> pd.DataFrame:
    """Split test turns into agree vs disagree (misconception vs correctness)
    and report baseline and augmented performance on each subset.

    'agree' turns: present & incorrect, or absent & correct (misconception
       tracks correctness; channel is redundant here).
    'disagree' turns: present & correct, or absent & incorrect (misconception
       carries info correctness does not; channel's best chance to help).
    not_evidenced turns are reported as their own group.
    """
    # align misc onto the predictions by (dialogue, turn, kc). The augmented
    # prediction frame may already carry 'misc'; only merge it in if missing.
    def with_misc(frame):
        if "misc" in frame.columns:
            return frame
        return frame.merge(test_mc[["dialogue_idx", "turn", "kc", "misc"]],
                           on=["dialogue_idx", "turn", "kc"], how="left")

    a = with_misc(aug_pred)
    b = with_misc(base_pred)

    def group(row):
        m, c = row["misc"], row["correct"]
        if m == "not_evidenced":
            return "not_evidenced"
        if (m == "present" and c == 0) or (m == "absent" and c == 1):
            return "agree"
        return "disagree"

    a["grp"] = a.apply(group, axis=1)
    b["grp"] = b.apply(group, axis=1)

    rows = []
    for g in ["agree", "disagree", "not_evidenced"]:
        ag = a[a["grp"] == g]; bg = b[b["grp"] == g]
        if len(ag) == 0:
            continue
        y = ag["correct"].to_numpy()
        rows.append({
            "subset": g,
            "n": len(ag),
            "frac_correct": round(y.mean(), 3),
            "base_AUC": round(_safe_auc(bg["correct"].to_numpy(), bg["pred"].to_numpy()), 4),
            "aug_AUC": round(_safe_auc(y, ag["pred"].to_numpy()), 4),
            "base_acc": round(((bg["pred"] >= 0.5).astype(int) == bg["correct"]).mean(), 4),
            "aug_acc": round(((ag["pred"] >= 0.5).astype(int) == ag["correct"]).mean(), 4),
        })
    out = pd.DataFrame(rows)
    if len(out):
        out["dAUC"] = (out["aug_AUC"] - out["base_AUC"]).round(4)
    return out
