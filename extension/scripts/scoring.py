"""Scoring extracted annotations against the human validation gold.

Reads only the extraction cache. Cell-level agreement is scored on the
five-family P/A/N grid; thread-level agreement on per-family resolution
status, which is where the strict authorship rule lives. The scorer reports
macro, micro, and gold-positive-support-weighted F1 for detecting P. F1 for a
family with no gold and no predicted positives in a sample is undefined and
excluded from macro averages (verified: gold scored against itself gives
exactly 1.0), and all bootstrap uncertainty resamples dialogues, never turns.
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .extraction import FAMILIES, cache_path


# ---------------------------------------------------------------------------
# Gold-side derivations
# ---------------------------------------------------------------------------

def units_by_dialogue(gold: pd.DataFrame) -> Dict[int, List[str]]:
    """Expected unit list per dialogue, in gold order (drives grid alignment)."""
    return {int(d): list(g["turn"]) for d, g in gold.groupby("dialogue_id", sort=True)}


def dialogues_for_prompting(gold: pd.DataFrame) -> Dict[int, str]:
    """Model-visible input derived through a strict allowlist: the conversation
    text only. The gold also holds labels, thread grammars, adjudication
    notes, and MathDial's own confusion fields, none of which may ever reach a
    prompt. Never widen this."""
    return {
        int(d): g.iloc[-1]["conversation"]
        for d, g in gold.groupby("dialogue_id", sort=True)
    }


def gold_resolutions(gold: pd.DataFrame) -> Dict[int, Dict[str, int]]:
    """Per dialogue, per family: does any gold thread of that family resolve."""
    out: Dict[int, Dict[str, int]] = {}
    for did, g in gold.groupby("dialogue_id", sort=True):
        threads = g[g["turn"] == "solution"].iloc[0]["dialogue_threads"]
        flags = {f: 0 for f in FAMILIES}
        for block in [b for b in str(threads).split("||") if b.strip()]:
            fam = re.search(r"family=(\w+)", block)
            if fam and "resolved_at" in block:
                flags[fam.group(1)] = 1
        out[int(did)] = flags
    return out


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def prf(golds: List, preds: List, pos="P") -> Tuple[Optional[float], ...]:
    tp = sum(1 for g, p in zip(golds, preds) if g == pos and p == pos)
    fp = sum(1 for g, p in zip(golds, preds) if g != pos and p == pos)
    fn = sum(1 for g, p in zip(golds, preds) if g == pos and p != pos)
    if tp + fp + fn == 0:  # family absent from gold AND predictions:
        return None, None, None  # undefined, excluded from macro averages
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1


def macro(values) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else float("nan")


def kripp_alpha(pairs: List[Tuple[str, str]]) -> float:
    """Nominal Krippendorff's alpha, two raters, complete data per unit."""
    n = len(pairs)
    if n == 0:
        return float("nan")
    observed = sum(1 for a, b in pairs if a != b) / n
    counts = Counter(v for pair in pairs for v in pair)
    total = 2 * n
    expected = 1 - sum((c / total) ** 2 for c in counts.values())
    return 1 - observed / expected if expected > 0 else float("nan")


# ---------------------------------------------------------------------------
# Per-configuration scoring
# ---------------------------------------------------------------------------

def config_frames(gold: pd.DataFrame, model_key: str, prompt_name: str, dids: List[int],
                  split: str = "validation"):
    gold_res = gold_resolutions(gold)
    rows, res_rows = [], []
    valid = 0
    costs, latencies = [], []
    for did in dids:
        path = cache_path(model_key, prompt_name, did, split)
        if not path.exists():
            continue
        record = json.load(open(path))
        costs.append(record.get("cost_usd", 0))
        latencies.append(record.get("latency_s", 0))
        if not record.get("valid"):
            continue
        valid += 1
        annotation = record["annotation"]
        pred_res = {f: 0 for f in FAMILIES}
        for thread in annotation.get("threads", []):
            if thread.get("resolved_at") and thread.get("family") in pred_res:
                pred_res[thread["family"]] = 1
        for fam in FAMILIES:
            res_rows.append((did, fam, gold_res[did][fam], pred_res[fam]))
        row_map = {r["unit"]: r for r in annotation["grid"]}
        for _, gold_row in gold[gold.dialogue_id == did].iterrows():
            pred_row = row_map[gold_row["turn"]]
            for fam in FAMILIES:
                rows.append(
                    {
                        "did": did,
                        "unit": gold_row["turn"],
                        "family": fam,
                        "gold": gold_row[fam],
                        "pred": pred_row[fam],
                    }
                )
    return (
        pd.DataFrame(rows),
        pd.DataFrame(res_rows, columns=["did", "family", "gold", "pred"]),
        valid,
        costs,
        latencies,
    )


def score_config(
    gold: pd.DataFrame,
    model_slug: str,
    prompt_name: str,
    dids: List[int],
    n_boot: int = 500,
    split: str = "validation",
) -> dict:
    frame, res, valid, costs, latencies = config_frames(gold, model_slug, prompt_name, dids, split)
    out = {
        "model": model_slug,
        "prompt": prompt_name,
        "valid_rate": valid / len(dids),
        "usd_per_dialogue": (sum(costs) / len(costs)) if costs else float("nan"),
        "latency_s": (sum(latencies) / len(latencies)) if latencies else float("nan"),
    }
    if frame.empty:
        out.update({
            "macro_f1_P": float("nan"),
            "micro_f1_P": float("nan"),
            "weighted_f1_P": float("nan"),
            "alpha": float("nan"),
        })
        out.update({f"f1_{fam}": float("nan") for fam in FAMILIES})
        return out
    f1s, supports = {}, {}
    for fam in FAMILIES:
        sub = frame[frame.family == fam]
        f1s[fam] = prf(sub.gold.tolist(), sub.pred.tolist())[2]
        supports[fam] = int((sub.gold == "P").sum())
    out["macro_f1_P"] = macro(f1s.values())
    micro_f1 = prf(frame.gold.tolist(), frame.pred.tolist())[2]
    out["micro_f1_P"] = (
        micro_f1 if micro_f1 is not None else float("nan")
    )
    total_support = sum(supports.values())
    out["weighted_f1_P"] = (
        sum(f1s[fam] * supports[fam] for fam in FAMILIES if supports[fam])
        / total_support
        if total_support else float("nan")
    )
    for fam in FAMILIES:
        out[f"f1_{fam}"] = round(f1s[fam], 3) if f1s[fam] is not None else float("nan")
    out["alpha"] = kripp_alpha(list(zip(frame.gold, frame.pred)))
    rprec, rrec, _ = prf(res.gold.tolist(), res.pred.tolist(), pos=1)
    out["res_prec"] = rprec if rprec is not None else float("nan")
    out["res_rec"] = rrec if rrec is not None else float("nan")
    if n_boot == 0:
        out["f1_ci_lo"] = out["f1_ci_hi"] = float("nan")
        return out
    by_dialogue = {d: g for d, g in frame.groupby("did")}
    dialogue_ids = list(by_dialogue)
    stats = []
    for _ in range(n_boot):
        sample = pd.concat([by_dialogue[random.choice(dialogue_ids)] for _ in dialogue_ids])
        vals = [
            prf(sample[sample.family == fam].gold.tolist(), sample[sample.family == fam].pred.tolist())[2]
            for fam in FAMILIES
        ]
        stats.append(macro(vals))
    stats.sort()
    out["f1_ci_lo"] = stats[int(0.025 * n_boot)]
    out["f1_ci_hi"] = stats[int(0.975 * n_boot) - 1]
    return out
