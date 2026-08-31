"""Scoring extracted annotations against the human validation gold.

Reads only the extraction cache. Cell-level agreement is scored on the
five-family P/A/N grid. The scorer reports the original five-family metrics
and a coarse two-family view that collapses comprehension/relevance/principles
into ``conceptual`` and wrong_operation/steps into ``procedural``. Within a
pooled turn, P takes precedence over A, which takes precedence over N. Thus a
pooled family is P when any constituent family is P, rather than counting the
same turn several times.

Both views report exact P/A/N accuracy and macro, micro, and
gold-positive-support-weighted F1 for detecting P. The original five-family
view also reports overall nominal Cohen's kappa across all P/A/N cells. F1 for
a family with no gold and no predicted positives in a sample is undefined and
excluded from macro averages (verified: gold scored against itself gives
exactly 1.0), and all bootstrap uncertainty resamples dialogues, never turns.
Each configuration also reports the whitespace-delimited word count of its
fully assembled static system prompt, including the selected codebook and
excluding dialogue-specific user content.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from typing import Dict, List, Optional, Tuple

import pandas as pd

from . import prompt_loader
from .extraction import cache_path
from .schema import FAMILIES


POOLED_FAMILIES = {
    "conceptual": ("comprehension", "relevance", "principles"),
    "procedural": ("wrong_operation", "steps"),
}


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


def accuracy(golds: List, preds: List) -> float:
    """Exact P/A/N agreement across the supplied cells."""
    return (
        sum(g == p for g, p in zip(golds, preds)) / len(golds)
        if golds else float("nan")
    )


def _collapse_labels(labels) -> str:
    """Collapse constituent P/A/N labels using presence-first precedence."""
    values = set(labels)
    for label in ("P", "A", "N"):
        if label in values:
            return label
    raise ValueError(f"cannot pool labels without P/A/N values: {values}")


def pooled_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Collapse the five family cells at each turn into two coarse cells.

    Conceptual comprises comprehension, relevance, and principles;
    procedural comprises wrong_operation and steps. Gold and predictions are
    collapsed independently so the coarser evaluation never uses gold labels
    to transform predictions (or vice versa).
    """
    rows = []
    for pooled_family, members in POOLED_FAMILIES.items():
        subset = frame[frame["family"].isin(members)]
        for (did, unit), group in subset.groupby(["did", "unit"], sort=False):
            rows.append({
                "did": did,
                "unit": unit,
                "family": pooled_family,
                "gold": _collapse_labels(group["gold"]),
                "pred": _collapse_labels(group["pred"]),
            })
    return pd.DataFrame(rows, columns=["did", "unit", "family", "gold", "pred"])


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


def cohen_kappa(pairs: List[Tuple[str, str]]) -> float:
    """Nominal Cohen's kappa for two complete P/A/N label sequences."""
    n = len(pairs)
    if n == 0:
        return float("nan")
    observed = sum(gold == pred for gold, pred in pairs) / n
    gold_counts = Counter(gold for gold, _ in pairs)
    pred_counts = Counter(pred for _, pred in pairs)
    labels = set(gold_counts) | set(pred_counts)
    expected = sum(
        (gold_counts[label] / n) * (pred_counts[label] / n)
        for label in labels
    )
    return (
        (observed - expected) / (1 - expected)
        if expected < 1 else float("nan")
    )


def prompt_word_count(prompt_name: str) -> int:
    """Count words in the assembled static prompt and selected codebook.

    Dialogue text, dialogue ID, and unit names live in the per-request user
    message and are deliberately excluded, so this measures only differences
    between prompt versions. A word is one whitespace-delimited item, matching
    the ordinary word-count convention used for prose documents.
    """
    return len(prompt_loader.system_for(prompt_name).split())


# ---------------------------------------------------------------------------
# Per-configuration scoring
# ---------------------------------------------------------------------------

def config_frames(gold: pd.DataFrame, model_key: str, prompt_name: str, dids: List[int],
                  split: str = "validation"):
    rows = []
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
    frame, valid, costs, latencies = config_frames(
        gold, model_slug, prompt_name, dids, split
    )
    out = {
        "model": model_slug,
        "prompt": prompt_name,
        "prompt_word_count": prompt_word_count(prompt_name),
        "valid_rate": valid / len(dids),
        "usd_per_dialogue": (sum(costs) / len(costs)) if costs else float("nan"),
        "latency_s": (sum(latencies) / len(latencies)) if latencies else float("nan"),
    }
    if frame.empty:
        out.update({
            "macro_f1_P": float("nan"),
            "micro_f1_P": float("nan"),
            "weighted_f1_P": float("nan"),
            "accuracy": float("nan"),
            "alpha": float("nan"),
            "kappa": float("nan"),
            "f1_ci_lo": float("nan"),
            "f1_ci_hi": float("nan"),
            "pooled_macro_f1_P": float("nan"),
            "pooled_micro_f1_P": float("nan"),
            "pooled_weighted_f1_P": float("nan"),
            "pooled_accuracy": float("nan"),
            "pooled_alpha": float("nan"),
            "pooled_f1_ci_lo": float("nan"),
            "pooled_f1_ci_hi": float("nan"),
        })
        out.update({f"f1_{fam}": float("nan") for fam in FAMILIES})
        out.update({f"accuracy_{fam}": float("nan") for fam in FAMILIES})
        out.update({
            f"pooled_f1_{fam}": float("nan") for fam in POOLED_FAMILIES
        })
        out.update({
            f"pooled_accuracy_{fam}": float("nan")
            for fam in POOLED_FAMILIES
        })
        return out

    # Original five-family view.
    f1s, supports = {}, {}
    for fam in FAMILIES:
        sub = frame[frame.family == fam]
        f1s[fam] = prf(sub.gold.tolist(), sub.pred.tolist())[2]
        supports[fam] = int((sub.gold == "P").sum())
        out[f"accuracy_{fam}"] = accuracy(
            sub.gold.tolist(), sub.pred.tolist()
        )
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
    out["accuracy"] = accuracy(frame.gold.tolist(), frame.pred.tolist())
    for fam in FAMILIES:
        out[f"f1_{fam}"] = (
            round(f1s[fam], 3)
            if f1s[fam] is not None else float("nan")
        )
    label_pairs = list(zip(frame.gold, frame.pred))
    out["alpha"] = kripp_alpha(label_pairs)
    out["kappa"] = cohen_kappa(label_pairs)

    # Coarse two-family view. Each dialogue-turn contributes exactly one
    # conceptual cell and one procedural cell.
    pooled = pooled_frame(frame)
    pooled_f1s, pooled_supports = {}, {}
    for fam in POOLED_FAMILIES:
        sub = pooled[pooled.family == fam]
        pooled_f1s[fam] = prf(sub.gold.tolist(), sub.pred.tolist())[2]
        pooled_supports[fam] = int((sub.gold == "P").sum())
        out[f"pooled_f1_{fam}"] = (
            round(pooled_f1s[fam], 3)
            if pooled_f1s[fam] is not None else float("nan")
        )
        out[f"pooled_accuracy_{fam}"] = accuracy(
            sub.gold.tolist(), sub.pred.tolist()
        )
    out["pooled_macro_f1_P"] = macro(pooled_f1s.values())
    pooled_micro_f1 = prf(
        pooled.gold.tolist(), pooled.pred.tolist()
    )[2]
    out["pooled_micro_f1_P"] = (
        pooled_micro_f1 if pooled_micro_f1 is not None else float("nan")
    )
    pooled_total_support = sum(pooled_supports.values())
    out["pooled_weighted_f1_P"] = (
        sum(
            pooled_f1s[fam] * pooled_supports[fam]
            for fam in POOLED_FAMILIES if pooled_supports[fam]
        ) / pooled_total_support
        if pooled_total_support else float("nan")
    )
    out["pooled_accuracy"] = accuracy(
        pooled.gold.tolist(), pooled.pred.tolist()
    )
    out["pooled_alpha"] = kripp_alpha(
        list(zip(pooled.gold, pooled.pred))
    )

    if n_boot == 0:
        out["f1_ci_lo"] = out["f1_ci_hi"] = float("nan")
        out["pooled_f1_ci_lo"] = out["pooled_f1_ci_hi"] = float("nan")
        return out
    by_dialogue = {d: g for d, g in frame.groupby("did")}
    pooled_by_dialogue = {d: g for d, g in pooled.groupby("did")}
    dialogue_ids = list(by_dialogue)
    stats, pooled_stats = [], []
    for _ in range(n_boot):
        sampled_ids = [random.choice(dialogue_ids) for _ in dialogue_ids]
        sample = pd.concat([by_dialogue[d] for d in sampled_ids])
        pooled_sample = pd.concat([pooled_by_dialogue[d] for d in sampled_ids])
        vals = [
            prf(sample[sample.family == fam].gold.tolist(), sample[sample.family == fam].pred.tolist())[2]
            for fam in FAMILIES
        ]
        stats.append(macro(vals))
        pooled_vals = [
            prf(
                pooled_sample[pooled_sample.family == fam].gold.tolist(),
                pooled_sample[pooled_sample.family == fam].pred.tolist(),
            )[2]
            for fam in POOLED_FAMILIES
        ]
        pooled_stats.append(macro(pooled_vals))
    stats.sort()
    pooled_stats.sort()
    out["f1_ci_lo"] = stats[int(0.025 * n_boot)]
    out["f1_ci_hi"] = stats[int(0.975 * n_boot) - 1]
    out["pooled_f1_ci_lo"] = pooled_stats[int(0.025 * n_boot)]
    out["pooled_f1_ci_hi"] = pooled_stats[int(0.975 * n_boot) - 1]
    return out
