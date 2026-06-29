"""
myext/endpoint.py

Automatic endpoint validation. Cross-checks each dialogue's extracted
misconception trajectory against the dialogue-level resolution field
(self-correctness), without any human labelling.

The endpoint is the last SUBSTANTIVE label (present or absent), found by
walking back from the end past trailing not_evidenced turns, since
not_evidenced is the no-update case and makes no claim about the misconception.

Expected endpoint by resolution:
  - resolved ("Yes")            -> expect absent  (misconception gone by end)
  - unresolved ("No")           -> expect present (misconception persisted)
  - reveal-assisted ("Yes, ...")-> ambiguous; reported as its own stratum,
                                   not folded into the pass/fail rate.

Dialogues with no substantive label at all cannot be assessed and are excluded
and counted (a large excluded fraction is itself a warning about the prompt).

This is a screen, not ground truth: it validates only the endpoint, not the
per-turn trajectory, and the resolution field is itself an imperfect
annotation. Interpreted accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np


def _turn_order(turn_key: str) -> int:
    return int("".join(ch for ch in turn_key if ch.isdigit()) or 0)


def last_substantive_label(labels: Dict[str, dict]) -> Optional[str]:
    """The last present/absent label, skipping trailing not_evidenced turns.
    Returns None if the dialogue has no substantive label at all.
    """
    if "_error" in labels:
        return None
    items = sorted(((_turn_order(k), v["label"]) for k, v in labels.items()
                    if isinstance(v, dict) and "label" in v),
                   key=lambda x: x[0])
    for _, label in reversed(items):
        if label in ("present", "absent"):
            return label
    return None


def _resolution_class(resolution: str) -> str:
    """Map the self-correctness field to one of resolved / unresolved / reveal."""
    r = str(resolution).strip().lower()
    if r.startswith("no"):
        return "unresolved"
    if "reveal" in r or "help" in r or "but" in r or "," in r:
        return "reveal"
    if r.startswith("yes"):
        return "resolved"
    return "other"


@dataclass
class EndpointResult:
    n_total: int
    n_assessable: int
    n_excluded_no_substantive: int
    n_agree: int
    agreement: float
    # per-stratum breakdown
    resolved_agree: Tuple[int, int]    # (agree, total)
    unresolved_agree: Tuple[int, int]
    reveal_endpoint_absent: Tuple[int, int]  # (absent-ending, total) for info
    label_distribution: Dict[str, float]

    def summary(self) -> str:
        ra, rt = self.resolved_agree
        ua, ut = self.unresolved_agree
        lines = [
            f"endpoint agreement: {self.agreement:.3f} "
            f"({self.n_agree}/{self.n_assessable} assessable)",
            f"  excluded (no substantive label): {self.n_excluded_no_substantive}"
            f" of {self.n_total}",
            f"  resolved   -> expect absent : {ra}/{rt} agree"
            + (f" ({ra/rt:.3f})" if rt else ""),
            f"  unresolved -> expect present: {ua}/{ut} agree"
            + (f" ({ua/ut:.3f})" if ut else ""),
            f"  label distribution: " + ", ".join(
                f"{k}={v:.2f}" for k, v in self.label_distribution.items()),
        ]
        return "\n".join(lines)


def label_distribution(results: Dict[int, dict]) -> Dict[str, float]:
    """Fraction of all per-turn labels that are present / absent / not_evidenced.
    A degenerate distribution (e.g. almost all one class) is a red flag even if
    endpoint agreement looks fine.
    """
    counts = {"present": 0, "absent": 0, "not_evidenced": 0}
    for labels in results.values():
        if "_error" in labels:
            continue
        for v in labels.values():
            if isinstance(v, dict) and v.get("label") in counts:
                counts[v["label"]] += 1
    total = sum(counts.values()) or 1
    return {k: c / total for k, c in counts.items()}


def endpoint_check(results: Dict[int, dict], df) -> EndpointResult:
    """Run the endpoint check over a set of extracted dialogues.

    results: {dialogue_id: {turn_key: {label, reason}}}
    df:      the dialogue dataframe (indexed by dialogue id) with a
             'self-correctness' column.
    """
    n_total = len(results)
    n_excluded = 0
    n_agree = 0
    n_assessable = 0
    r_agree = r_tot = 0
    u_agree = u_tot = 0
    rev_absent = rev_tot = 0

    for did, labels in results.items():
        endpoint = last_substantive_label(labels)
        if endpoint is None:
            n_excluded += 1
            continue
        rclass = _resolution_class(df.loc[did, "self-correctness"])
        if rclass == "resolved":
            n_assessable += 1
            r_tot += 1
            if endpoint == "absent":
                n_agree += 1
                r_agree += 1
        elif rclass == "unresolved":
            n_assessable += 1
            u_tot += 1
            if endpoint == "present":
                n_agree += 1
                u_agree += 1
        elif rclass == "reveal":
            # ambiguous: not counted in pass/fail, reported separately
            rev_tot += 1
            if endpoint == "absent":
                rev_absent += 1
        # 'other' resolutions are skipped silently (rare)

    agreement = n_agree / n_assessable if n_assessable else float("nan")
    return EndpointResult(
        n_total=n_total,
        n_assessable=n_assessable,
        n_excluded_no_substantive=n_excluded,
        n_agree=n_agree,
        agreement=agreement,
        resolved_agree=(r_agree, r_tot),
        unresolved_agree=(u_agree, u_tot),
        reveal_endpoint_absent=(rev_absent, rev_tot),
        label_distribution=label_distribution(results),
    )
